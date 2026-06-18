from __future__ import annotations

from typing import Any

import sqlite3

from .chatgpt_export import parse_chatgpt_export
from .registry import truncate


BOUNDARY = "b_review_context_bounded_source_preview_not_memory"
MAX_CONTEXT_CHARS = 1400


def review_context_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    refs = [str(item) for item in (payload.get("source_refs") or [])]
    conversation_id = _ref_value(refs, "conversation")
    source_file = _ref_value(refs, "file")
    target_ids = {
        _ref_value(refs, "user_message"),
        _ref_value(refs, "assistant_message"),
        _ref_value(refs, "followup_message"),
        _ref_value(refs, "message"),
    }
    target_ids = {item for item in target_ids if item}
    before = _bounded_int(payload.get("before"), default=4, minimum=1, maximum=8)
    after = _bounded_int(payload.get("after"), default=3, minimum=1, maximum=8)

    if not conversation_id:
        return _base(
            {
                "status": "review_context_unavailable",
                "reason": "source refs did not include a conversation id",
                "items": [],
                "source_refs": refs,
            }
        )

    _ensure_index(conn)
    db_rows = _db_context_rows(conn, conversation_id, source_file)
    raw_rows = _raw_context_rows(conversation_id, source_file)
    rows = raw_rows or db_rows
    if not rows:
        return _base(
            {
                "status": "review_context_unavailable",
                "reason": "conversation was not found in parsed index or local export",
                "items": [],
                "source_refs": refs,
            }
        )

    target_index = _target_index(rows, target_ids)
    start = max(0, target_index - before)
    end = min(len(rows), target_index + after + 1)
    items = []
    for index, row in enumerate(rows[start:end], start=start):
        items.append(
            {
                "index": index,
                "is_target": row["message_id"] in target_ids,
                "role": row["role"],
                "message_id": row["message_id"],
                "create_time": row.get("create_time"),
                "model_slug": row.get("model_slug") or "",
                "bounded_preview": truncate(str(row.get("content") or ""), MAX_CONTEXT_CHARS),
            }
        )

    return _base(
        {
            "status": "review_context_preview_ready",
            "decision": "bounded_context_preview_only",
            "conversation_id": conversation_id,
            "source_file": source_file,
            "target_message_ids": sorted(target_ids),
            "window": {"before": before, "after": after, "start_index": start, "end_index": end - 1},
            "items": items,
            "source_refs": refs,
            "note": "Use this only to understand the review card context. It is not active memory, transfer, runtime recall, or raw corpus import.",
        }
    )


def _ensure_index(conn: sqlite3.Connection) -> None:
    exists = conn.execute("SELECT COUNT(*) AS n FROM b_corpus_messages").fetchone()
    if exists and int(exists["n"] or 0) > 0:
        return
    # The parser stores bounded previews only. This indexes source material as review provenance, not memory.
    from .chatgpt_export import index_chatgpt_export

    index_chatgpt_export(conn)
    conn.commit()


def _db_context_rows(conn: sqlite3.Connection, conversation_id: str, source_file: str) -> list[dict[str, Any]]:
    params: list[Any] = [conversation_id]
    source_clause = ""
    if source_file:
        source_clause = "AND source_file = ?"
        params.append(source_file)
    rows = conn.execute(
        f"""
        SELECT source_file, conversation_id, message_id, role, content_preview AS content, create_time, model_slug
        FROM b_corpus_messages
        WHERE conversation_id = ? {source_clause}
        ORDER BY COALESCE(create_time, 0), message_id
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def _raw_context_rows(conversation_id: str, source_file: str) -> list[dict[str, Any]]:
    try:
        _conversations, messages = parse_chatgpt_export()
    except Exception:
        return []
    rows = []
    for message in messages:
        if message.conversation_id != conversation_id:
            continue
        if source_file and message.source_file != source_file:
            continue
        rows.append(
            {
                "source_file": message.source_file,
                "conversation_id": message.conversation_id,
                "message_id": message.message_id,
                "role": message.role,
                "content": message.content,
                "create_time": message.create_time,
                "model_slug": message.model_slug,
            }
        )
    return sorted(rows, key=lambda item: (float(item.get("create_time") or 0), str(item.get("message_id") or "")))


def _target_index(rows: list[dict[str, Any]], target_ids: set[str]) -> int:
    if target_ids:
        for index, row in enumerate(rows):
            if str(row.get("message_id") or "") in target_ids:
                return index
    return 0


def _ref_value(refs: list[str], prefix: str) -> str:
    needle = f"{prefix}:"
    for ref in refs:
        if ref.startswith(needle):
            return ref[len(needle) :]
    return ""


def _bounded_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def _base(extra: dict[str, Any]) -> dict[str, Any]:
    return {
        **extra,
        "boundary": BOUNDARY,
        "activation_change": "none",
        "raw_a_import_allowed": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "training_allowed": False,
        "provider_dependency": False,
    }
