from __future__ import annotations

from selene.chat import retrieve_citations
from selene.db import connect, init_db
from selene.semantic import MiniLMEmbeddingService, backfill_evidence_embeddings, semantic_search, semantic_status


class FakeEmbeddingService:
    model_name = "fake-minilm"

    def availability_status(self):
        return {"available": True, "provider_name": "fake", "status": "ready", "model_name": self.model_name, "error": None}

    def content_hash(self, text):
        return str(abs(hash(" ".join(str(text or "").lower().split()))))

    def embed_text(self, text):
        lower = str(text or "").lower()
        if "moonlight" in lower or "starlight" in lower:
            return [1.0, 0.0, 0.0]
        if "tool" in lower or "architecture" in lower:
            return [0.0, 1.0, 0.0]
        return [0.0, 0.0, 1.0]


def insert_evidence(conn):
    rows = [
        ("semantic-a", "human_reviewed_artifact", "artifact", "Moonlight anchor", "", "symbolic", "", "strong", "yes", "", 10, "src-a", "", "", "Starlight and moonlight continuity anchor", "", "", "test"),
        ("semantic-b", "human_reviewed_artifact", "artifact", "Architecture route", "", "tools", "", "strong", "yes", "", 9, "src-b", "", "", "Tool architecture and module route", "", "", "test"),
        ("semantic-no", "human_reviewed_artifact", "artifact", "Rejected moonlight", "", "symbolic", "", "weak", "no", "", 99, "src-c", "", "", "Moonlight rejected", "", "", "test"),
    ]
    conn.executemany(
        """
        INSERT INTO evidence_items
        (id, layer, item_type, title, phase, themes, tier, confidence, decision, roles, score, source,
         month, formation_period, preview, human_note, sensitivity_labels, source_file)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def test_minilm_pack_unpack_and_cosine_similarity():
    blob = MiniLMEmbeddingService.pack_embedding([1.0, 0.0])
    unpacked = MiniLMEmbeddingService.unpack_embedding(blob)
    assert unpacked[0] == 1.0
    assert MiniLMEmbeddingService.cosine_similarity([1.0, 0.0], [0.9, 0.1]) > 0.9
    assert MiniLMEmbeddingService.cosine_similarity([1.0, 0.0], [0.0, 1.0]) < 0.1


def test_semantic_backfill_and_search_use_reviewed_evidence_only(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    insert_evidence(conn)
    result = backfill_evidence_embeddings(conn, service=FakeEmbeddingService())
    assert result["created"] == 2
    status = semantic_status(conn, FakeEmbeddingService())
    assert status["ready_embeddings"] == 2
    matches = semantic_search(conn, "the starlight anchor", service=FakeEmbeddingService())
    ids = [item["id"] for item in matches]
    assert ids[0] == "semantic-a"
    assert "semantic-no" not in ids


def test_chat_citations_prefer_semantic_then_keyword_fallback(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    insert_evidence(conn)
    backfill_evidence_embeddings(conn, service=FakeEmbeddingService())
    citations = retrieve_citations(conn, "what does moonlight mean", semantic_service=FakeEmbeddingService())
    assert citations[0]["evidence_id"] == "semantic-a"
    assert citations[0]["reason_matched"].startswith("semantic_similarity")
