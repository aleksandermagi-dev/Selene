from __future__ import annotations

from array import array
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import hashlib
from io import StringIO
import math
import sqlite3
from typing import Any, Protocol
import warnings

from .registry import truncate


class EmbeddingService(Protocol):
    model_name: str

    def availability_status(self) -> dict[str, object]: ...
    def content_hash(self, text: str | None) -> str: ...
    def embed_text(self, text: str | None) -> list[float]: ...


class MiniLMEmbeddingService:
    """Optional local MiniLM embedding service for reviewed evidence retrieval."""

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    provider_name = "sentence_transformers"

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = str(model_name or self.MODEL_NAME).strip() or self.MODEL_NAME
        self._model: Any | None = None
        self._import_error: str | None = None
        self._cache: dict[str, list[float]] = {}

    def availability_status(self) -> dict[str, object]:
        available = self.is_available()
        return {
            "available": available,
            "provider_name": self.provider_name,
            "status": "ready" if available else "unavailable",
            "model_name": self.model_name,
            "error": None if available else self._import_error,
        }

    def is_available(self) -> bool:
        try:
            self._load_model()
        except RuntimeError:
            return False
        return True

    def normalize_text(self, text: str | None) -> str:
        return " ".join(str(text or "").strip().split())

    def content_hash(self, text: str | None) -> str:
        return hashlib.sha256(self.normalize_text(text).encode("utf-8")).hexdigest()

    def embed_text(self, text: str | None) -> list[float]:
        normalized = self.normalize_text(text)
        key = self.content_hash(normalized)
        if key not in self._cache:
            model = self._load_model()
            with self._quiet_runtime():
                vector = model.encode(normalized, normalize_embeddings=True, convert_to_numpy=True)
            self._cache[key] = self._vector_to_list(vector)
        return list(self._cache[key])

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        try:
            with self._quiet_runtime():
                from sentence_transformers import SentenceTransformer
        except Exception as exc:  # pragma: no cover - depends on optional local runtime
            self._import_error = str(exc)
            raise RuntimeError("sentence-transformers runtime is unavailable") from exc
        with self._quiet_runtime():
            self._model = SentenceTransformer(self.model_name)
        return self._model

    @staticmethod
    def pack_embedding(vector: list[float]) -> bytes:
        return array("f", [float(value) for value in vector]).tobytes()

    @staticmethod
    def unpack_embedding(blob: bytes | bytearray | memoryview | None) -> list[float]:
        if blob is None:
            return []
        payload = array("f")
        payload.frombytes(bytes(blob))
        return [float(value) for value in payload]

    @staticmethod
    def cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        dot = math.fsum(float(a) * float(b) for a, b in zip(left, right, strict=False))
        left_norm = math.sqrt(math.fsum(float(a) * float(a) for a in left))
        right_norm = math.sqrt(math.fsum(float(b) * float(b) for b in right))
        if left_norm <= 0.0 or right_norm <= 0.0:
            return 0.0
        return max(-1.0, min(1.0, dot / (left_norm * right_norm)))

    @staticmethod
    def _quiet_runtime() -> ExitStack:
        stack = ExitStack()
        stack.enter_context(redirect_stdout(StringIO()))
        stack.enter_context(redirect_stderr(StringIO()))
        warning_context = warnings.catch_warnings()
        stack.enter_context(warning_context)
        warnings.filterwarnings("ignore", module="huggingface_hub")
        warnings.filterwarnings("ignore", module="sentence_transformers")
        warnings.filterwarnings("ignore", module="transformers")
        return stack

    @staticmethod
    def _vector_to_list(vector: Any) -> list[float]:
        if hasattr(vector, "tolist"):
            values = vector.tolist()
            if isinstance(values, list):
                return [float(item) for item in values]
        return [float(item) for item in vector]


def evidence_text(row: sqlite3.Row | dict[str, Any]) -> str:
    item = dict(row)
    parts = [
        item.get("title"),
        item.get("themes"),
        item.get("roles"),
        item.get("confidence"),
        item.get("source"),
        item.get("preview"),
        item.get("human_note"),
    ]
    return " ".join(str(part or "") for part in parts).strip()


def semantic_status(conn: sqlite3.Connection, service: EmbeddingService | None = None) -> dict[str, Any]:
    service = service or MiniLMEmbeddingService()
    availability = service.availability_status()
    counts = {
        row["status"]: row["count"]
        for row in conn.execute("SELECT status, COUNT(*) AS count FROM evidence_embeddings GROUP BY status")
    }
    return {
        **availability,
        "total_embeddings": int(conn.execute("SELECT COUNT(*) FROM evidence_embeddings").fetchone()[0]),
        "ready_embeddings": int(counts.get("ready", 0)),
        "failed_embeddings": int(counts.get("failed", 0)),
        "pending_embeddings": int(counts.get("pending", 0)),
        "reviewed_evidence_items": int(conn.execute("SELECT COUNT(*) FROM evidence_items WHERE decision IN ('yes', 'unsure')").fetchone()[0]),
    }


def backfill_evidence_embeddings(conn: sqlite3.Connection, limit: int | None = None, service: EmbeddingService | None = None) -> dict[str, Any]:
    service = service or MiniLMEmbeddingService()
    status = service.availability_status()
    if not status.get("available"):
        return {"ok": False, "reason": "embedding runtime unavailable", "status": status, "created": 0, "failed": 0}

    sql = """
        SELECT e.* FROM evidence_items e
        LEFT JOIN evidence_embeddings emb ON emb.evidence_id = e.id
        WHERE e.decision IN ('yes', 'unsure')
          AND (emb.id IS NULL OR emb.model_name != ? OR emb.status != 'ready')
        ORDER BY e.score DESC, e.id
    """
    rows = conn.execute(sql, (service.model_name,)).fetchall()
    created = 0
    failed = 0
    for row in rows[: limit or len(rows)]:
        text = evidence_text(row)
        content_hash = service.content_hash(text)
        existing = conn.execute("SELECT content_hash, model_name, status FROM evidence_embeddings WHERE evidence_id = ?", (row["id"],)).fetchone()
        if existing and existing["content_hash"] == content_hash and existing["model_name"] == service.model_name and existing["status"] == "ready":
            continue
        try:
            vector = service.embed_text(text)
            blob = MiniLMEmbeddingService.pack_embedding(vector)
            conn.execute(
                """
                INSERT INTO evidence_embeddings(evidence_id, source_type, model_name, embedding_dim, embedding_blob, content_hash, status, error, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, 'ready', NULL, CURRENT_TIMESTAMP)
                ON CONFLICT(evidence_id) DO UPDATE SET
                  source_type=excluded.source_type,
                  model_name=excluded.model_name,
                  embedding_dim=excluded.embedding_dim,
                  embedding_blob=excluded.embedding_blob,
                  content_hash=excluded.content_hash,
                  status='ready',
                  error=NULL,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (row["id"], row["item_type"], service.model_name, len(vector), blob, content_hash),
            )
            created += 1
        except Exception as exc:  # pragma: no cover - depends on optional local runtime
            conn.execute(
                """
                INSERT INTO evidence_embeddings(evidence_id, source_type, model_name, content_hash, status, error, updated_at)
                VALUES(?, ?, ?, ?, 'failed', ?, CURRENT_TIMESTAMP)
                ON CONFLICT(evidence_id) DO UPDATE SET status='failed', error=excluded.error, updated_at=CURRENT_TIMESTAMP
                """,
                (row["id"], row["item_type"], service.model_name, content_hash, truncate(str(exc), 500)),
            )
            failed += 1
    conn.commit()
    return {"ok": failed == 0, "created": created, "failed": failed, "status": semantic_status(conn, service)}


def semantic_search(conn: sqlite3.Connection, text: str, limit: int = 8, service: EmbeddingService | None = None) -> list[dict[str, Any]]:
    service = service or MiniLMEmbeddingService()
    if not service.availability_status().get("available"):
        return []
    query_vector = service.embed_text(text)
    rows = conn.execute(
        """
        SELECT e.id, e.title, e.decision, e.confidence, e.source, e.preview, e.themes, e.roles, emb.embedding_blob
        FROM evidence_embeddings emb
        JOIN evidence_items e ON e.id = emb.evidence_id
        WHERE emb.status = 'ready' AND e.decision IN ('yes', 'unsure') AND emb.model_name = ?
        """,
        (service.model_name,),
    ).fetchall()
    scored = []
    for row in rows:
        vector = MiniLMEmbeddingService.unpack_embedding(row["embedding_blob"])
        score = MiniLMEmbeddingService.cosine_similarity(query_vector, vector)
        if score > 0:
            item = dict(row)
            item["semantic_score"] = score
            scored.append(item)
    scored.sort(key=lambda item: (item["decision"] != "yes", -float(item["semantic_score"])))
    return scored[:limit]
