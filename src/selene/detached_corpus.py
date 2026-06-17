from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from .gates import ArchiveAuditGate
from .paths import DETACHED_CORPUS_DIR
from .registry import truncate


ARCHIVE_ID = "DevelopmentalCorpusArchive_20260526_122541"
MAX_PREVIEW_CHARS = 520
MAX_SCAN_CHARS = 240_000
MAX_PREVIEWS = 8
TEXT_SUFFIXES = {".html", ".htm", ".json", ".txt", ".md", ".csv"}


def detached_corpus_audit(
    query: str = "",
    file_id: str | None = None,
    preview_limit: int = 5,
    archive_root: Path = DETACHED_CORPUS_DIR,
) -> dict[str, Any]:
    gate = ArchiveAuditGate().evaluate_text(
        f"bounded source archive provenance audit raw corpus metadata {query}".strip()
    )
    previews = detached_corpus_previews(query, file_id, preview_limit, archive_root)
    return {
        "archive_id": ARCHIVE_ID,
        "boundary": "read_only_detached_corpus_audit",
        "memory_candidate_type": "shared_developmental_memory_candidate",
        "abc_transfer_rule": "A -> B-reviewed translation -> C; never raw A -> C",
        "route_purpose": "prepare accountable future B-reviewed memory accession; this audit route is not memory import",
        "audit_status": "provenance_only_for_this_route",
        "future_b_reviewed_accession_status": "not_implemented_explicit_b_review_required",
        "accession_note": (
            "The corpus is treated as a candidate shared developmental memory source for Selene C. "
            "This endpoint only inspects metadata and bounded previews; any C memory accession must pass through B as a separate, explicit, reviewed, reversible translation process."
        ),
        "blocked_transfer": "raw_A_direct_to_C_memory",
        "writes_performed": False,
        "model_call_allowed": False,
        "gate": gate.__dict__,
        "metadata": detached_corpus_metadata(archive_root),
        "previews": previews,
    }


def detached_corpus_metadata(archive_root: Path = DETACHED_CORPUS_DIR) -> dict[str, Any]:
    root = archive_root.resolve()
    files = []
    total_bytes = 0
    if root.exists():
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            stat = path.stat()
            total_bytes += stat.st_size
            rel = path.relative_to(root).as_posix()
            files.append(
                {
                    "file_id": rel,
                    "name": path.name,
                    "relative_path": rel,
                    "size_bytes": stat.st_size,
                    "modified_at": _iso_timestamp(stat.st_mtime),
                    "content_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                    "preview_available": _previewable(path),
                    "role": _file_role(path),
                }
            )
    return {
        "exists": root.exists(),
        "archive_root": str(root),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "files": files,
    }


def detached_corpus_previews(
    query: str = "",
    file_id: str | None = None,
    limit: int = 5,
    archive_root: Path = DETACHED_CORPUS_DIR,
) -> list[dict[str, Any]]:
    root = archive_root.resolve()
    if not root.exists():
        return []
    safe_limit = max(1, min(int(limit or 5), MAX_PREVIEWS))
    candidates = [_resolve_file_id(root, file_id)] if file_id else sorted(path for path in root.rglob("*") if path.is_file())
    previews: list[dict[str, Any]] = []
    for path in candidates:
        if path is None or not _previewable(path):
            continue
        item = _preview_file(root, path, query)
        if item:
            previews.append(item)
        if len(previews) >= safe_limit:
            break
    return previews


def _preview_file(root: Path, path: Path, query: str) -> dict[str, Any] | None:
    text = _read_prefix(path, MAX_SCAN_CHARS)
    if not text:
        return None
    needle = query.strip().lower()
    index = text.lower().find(needle) if needle else 0
    if index < 0:
        return None
    start = max(0, index - 180)
    end = min(len(text), index + len(needle) + 340 if needle else MAX_PREVIEW_CHARS)
    snippet = truncate(text[start:end], MAX_PREVIEW_CHARS)
    return {
        "file_id": path.relative_to(root).as_posix(),
        "preview": snippet,
        "query_matched": bool(needle),
        "offset_approx": index,
        "max_preview_chars": MAX_PREVIEW_CHARS,
        "boundary": "bounded_preview_only_not_memory",
    }


def _read_prefix(path: Path, max_chars: int) -> str:
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return handle.read(max_chars)
    except OSError:
        return ""


def _resolve_file_id(root: Path, file_id: str | None) -> Path | None:
    if not file_id:
        return None
    candidate = (root / file_id).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def _previewable(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES


def _file_role(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".zip":
        return "detached_source_package_metadata_only"
    if path.name.startswith("conversations-") and suffix == ".json":
        return "conversation_export_bounded_preview_source"
    if path.name == "chat.html":
        return "html_export_bounded_preview_source"
    return "detached_archive_file"


def _iso_timestamp(value: float) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
