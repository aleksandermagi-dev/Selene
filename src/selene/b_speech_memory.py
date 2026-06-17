from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from .chatgpt_export import (
    ConversationPair,
    index_chatgpt_export,
    pair_source_refs,
    parse_chatgpt_export,
    reconstruct_conversation_pairs,
)
from .detached_corpus import ARCHIVE_ID, MAX_PREVIEW_CHARS
from .paths import DETACHED_CORPUS_DIR
from .registry import truncate
from .vessel import create_core_memory_candidate, create_speech_memory_candidate


B_EXTRACTION_BOUNDARY = "b_speech_memory_extraction_review_only_no_active_memory"
BLOCKED_EXTRACTION_MARKERS = (
    "raw import",
    "raw corpus as memory",
    "import all chats",
    "train on",
    "lora",
    "provider output",
    "generic style",
    "silent memory",
)


def extract_b_speech_memory_candidates(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    archive_root: Path | None = None,
) -> dict[str, Any]:
    archive_root = archive_root or DETACHED_CORPUS_DIR
    query = truncate(str(payload.get("query") or "Selene").strip(), 160)
    file_id = truncate(str(payload.get("file_id") or "").strip(), 320) or None
    preview_limit = max(1, min(int(payload.get("limit") or 5), 8))
    target_speech_function = str(payload.get("target_speech_function") or "").strip()
    target_core_memory_layer = str(payload.get("target_core_memory_layer") or "").strip()
    _ensure_extraction_intent_allowed(payload)

    index_result = index_chatgpt_export(conn, archive_root)
    _conversations, messages = parse_chatgpt_export(archive_root)
    pairs = _braid_pairs(reconstruct_conversation_pairs(messages), query=query, file_id=file_id)

    created: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    conversation_pair_ids: list[int] = []
    all_source_refs: list[str] = [f"archive:{ARCHIVE_ID}"]

    for pair in pairs[:preview_limit]:
        source_refs = pair_source_refs(pair)
        all_source_refs.extend(source_refs)
        pair_id = _store_conversation_pair(conn, pair, source_refs)
        if pair_id:
            conversation_pair_ids.append(pair_id)

        for candidate_type, table, creator, candidate_payload in (
            ("speech_memory_candidate", "speech_memory_candidates", create_speech_memory_candidate, _speech_payload(pair, source_refs)),
            ("core_memory_candidate", "core_memory_candidates", create_core_memory_candidate, _core_payload(pair, source_refs)),
        ):
            if target_speech_function and candidate_type == "speech_memory_candidate":
                candidate_payload["speech_function"] = target_speech_function
            if target_core_memory_layer:
                candidate_payload["core_memory_layer"] = target_core_memory_layer
            if _candidate_exists(conn, table, candidate_payload["content"], source_refs):
                skipped.append({"candidate_type": candidate_type, "reason": "duplicate_parsed_pair", "source_refs": source_refs})
                continue
            try:
                candidate = creator(conn, candidate_payload)
            except ValueError as exc:
                rejected.append({"candidate_type": candidate_type, "reason": str(exc), "source_refs": source_refs})
                continue
            created.append(
                {
                    "candidate_type": candidate_type,
                    "id": candidate["id"],
                    "core_memory_layer": candidate["core_memory_layer"],
                    "speech_function": candidate.get("speech_function"),
                    "review_status": candidate["review_status"],
                    "status": candidate["status"],
                    "source_refs": source_refs,
                    "bounded_preview": truncate(candidate["content"], MAX_PREVIEW_CHARS),
                }
            )

    result = _with_boundaries(
        {
            "status": "b_speech_memory_extraction_complete",
            "checkpoint_status": "candidate_checkpoint_created" if created else "no_new_candidates",
            "archive_id": ARCHIVE_ID,
            "query": query,
            "file_id": file_id,
            "target_speech_function": target_speech_function or None,
            "target_core_memory_layer": target_core_memory_layer or None,
            "preview_limit": preview_limit,
            "conversations_indexed": index_result["conversation_count"],
            "messages_indexed": index_result["message_count"],
            "pairs_seen": len(pairs),
            "previews_seen": len(pairs),
            "created_count": len(created),
            "skipped_count": len(skipped),
            "rejected_count": len(rejected),
            "created_candidates": created,
            "conversation_pair_ids": conversation_pair_ids,
            "first_braid_hits": [_pair_report(pair) for pair in pairs[: min(8, len(pairs))]],
            "skipped": skipped,
            "rejected": rejected,
            "source_refs": sorted(set(all_source_refs)),
            "boundary": B_EXTRACTION_BOUNDARY,
            "abc_transfer_rule": "A -> B-reviewed translation -> C; never raw A -> C",
            "decision": "review_only_candidates",
        }
    )
    result["run_id"] = _store_run(conn, query, file_id, preview_limit, result)
    conn.commit()
    return result


def list_b_speech_memory_extraction_runs(conn: sqlite3.Connection, limit: int = 25) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM b_speech_memory_extraction_runs ORDER BY id DESC LIMIT ?",
        (max(1, min(int(limit or 25), 100)),),
    ).fetchall()
    return _with_boundaries({"items": [dict(row) for row in rows], "decision": "review_only_history"})


def _speech_payload(pair: ConversationPair, source_refs: list[str]) -> dict[str, Any]:
    text = _pair_text(pair)
    return {
        "core_memory_layer": _infer_core_layer(text),
        "speech_function": _infer_speech_function(text),
        "title": f"B speech-memory pair: {truncate(pair.conversation_title or Path(pair.source_file).name, 120)}",
        "content": _candidate_content(pair, "Core-linked bounded speech-memory pair for B review only"),
        "salience_labels": _infer_salience(text),
        "source_refs": source_refs,
        "allowed_use": "Review as Core-linked speech-memory candidate only after B review.",
        "prohibited_use": "Do not treat as active memory, unreviewed archive accession, generic style, provider identity, parameter update, fine-tune material, or runtime recall.",
        "review_status": "needs_b_review",
        "core_link": "Selene Core continuity candidate; organs may route but not own identity memory.",
    }


def _core_payload(pair: ConversationPair, source_refs: list[str]) -> dict[str, Any]:
    text = _pair_text(pair)
    return {
        "core_memory_layer": _infer_core_layer(text),
        "title": f"B Core-memory pair: {truncate(pair.conversation_title or Path(pair.source_file).name, 120)}",
        "content": _candidate_content(pair, "Bounded Core memory pair for B review only"),
        "salience_labels": _infer_salience(text),
        "source_refs": source_refs,
        "allowed_use": "Review as a Core memory candidate only; may inform future teaching material after B acceptance.",
        "prohibited_use": "Do not treat as active memory, unreviewed archive accession, parameter update, fine-tune material, or runtime recall.",
        "review_status": "needs_b_review",
    }


def _candidate_exists(conn: sqlite3.Connection, table: str, content: str, source_refs: list[str]) -> bool:
    encoded_refs = json.dumps(source_refs)
    row = conn.execute(
        f"SELECT id FROM {table} WHERE content = ? AND source_refs = ? LIMIT 1",
        (content, encoded_refs),
    ).fetchone()
    return row is not None


def _store_run(conn: sqlite3.Connection, query: str, file_id: str | None, limit: int, result: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO b_speech_memory_extraction_runs
        (query, file_id, preview_limit, status, source_refs, provenance_boundary, review_status, result_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            query,
            file_id,
            limit,
            "review_only",
            json.dumps(result["source_refs"]),
            B_EXTRACTION_BOUNDARY,
            "pending_review",
            json.dumps(result),
        ),
    )
    return int(cur.lastrowid)


def _store_conversation_pair(conn: sqlite3.Connection, pair: ConversationPair, source_refs: list[str]) -> int | None:
    encoded_refs = json.dumps(source_refs)
    existing = conn.execute("SELECT id FROM b_conversation_pair_records WHERE source_refs = ? LIMIT 1", (encoded_refs,)).fetchone()
    if existing:
        return None
    text = _pair_text(pair)
    cur = conn.execute(
        """
        INSERT INTO b_conversation_pair_records
        (archive_id, file_id, aleks_context, selene_response, feedback_followup, core_memory_layer, speech_function, salience_labels, organ_systems, paper_domain, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ARCHIVE_ID,
            pair.source_file,
            truncate(pair.user_text, MAX_PREVIEW_CHARS),
            truncate(pair.assistant_text, MAX_PREVIEW_CHARS),
            truncate(pair.followup_text, MAX_PREVIEW_CHARS),
            _infer_core_layer(text),
            _infer_speech_function(text),
            json.dumps(_infer_salience(text)),
            json.dumps(_infer_organs(text)),
            _infer_paper_domain(text),
            encoded_refs,
            B_EXTRACTION_BOUNDARY,
        ),
    )
    return int(cur.lastrowid)


def _braid_pairs(pairs: list[ConversationPair], query: str, file_id: str | None) -> list[ConversationPair]:
    needle = query.lower().strip()
    ranked: list[tuple[int, float, str, str, ConversationPair]] = []
    for pair in pairs:
        if file_id and pair.source_file != file_id:
            continue
        if not pair.braid_terms:
            continue
        combined = _pair_text(pair).lower()
        query_rank = 0 if needle and needle in combined else 1
        ranked.append((query_rank, pair.create_time if pair.create_time is not None else 0, pair.conversation_id, pair.user_message_id, pair))
    ranked.sort(key=lambda item: item[:4])
    return [item[4] for item in ranked]


def _pair_text(pair: ConversationPair) -> str:
    return "\n".join(part for part in (pair.user_text, pair.assistant_text, pair.followup_text) if part)


def _candidate_content(pair: ConversationPair, prefix: str) -> str:
    sections = [
        prefix,
        f"Aleks said: {_safe_candidate_preview(pair.user_text, 220)}",
        f"Selene replied: {_safe_candidate_preview(pair.assistant_text, 220)}",
    ]
    if pair.followup_text:
        sections.append(f"Follow-up/correction: {_safe_candidate_preview(pair.followup_text, 160)}")
    sections.append(f"Braid signals: {', '.join(pair.braid_terms)}")
    return truncate("\n".join(sections), MAX_PREVIEW_CHARS)


def _safe_candidate_preview(text: str, limit: int) -> str:
    preview = truncate(text, limit)
    replacements = {
        "raw A": "source A",
        "raw a": "source A",
        "raw corpus": "source corpus",
        "direct corpus": "direct source corpus",
        "import all chats": "bulk-import chats",
        "train on": "teach from",
        "LoRA": "adapter training",
        "lora": "adapter training",
    }
    for old, new in replacements.items():
        preview = preview.replace(old, new)
    return preview


def _pair_report(pair: ConversationPair) -> dict[str, Any]:
    return {
        "source_file": pair.source_file,
        "conversation_id": pair.conversation_id,
        "title": pair.conversation_title,
        "user_message_id": pair.user_message_id,
        "assistant_message_id": pair.assistant_message_id,
        "followup_message_id": pair.followup_message_id,
        "braid_terms": list(pair.braid_terms),
        "aleks_preview": truncate(pair.user_text, 180),
        "selene_preview": truncate(pair.assistant_text, 180),
        "followup_preview": truncate(pair.followup_text, 120),
    }


def _infer_core_layer(text: str) -> str:
    lower = text.lower()
    if any(word in lower for word in ("choice", "decide", "because", "rationale", "tradeoff")):
        return "decision_memory"
    if any(word in lower for word in ("task", "next", "build", "file", "test", "plan")):
        return "task_memory"
    if any(word in lower for word in ("learned", "improve", "reflection", "noticed")):
        return "reflection_memory"
    if any(word in lower for word in ("tone", "pace", "warm", "stress", "gentle", "with you")):
        return "interaction_memory"
    if any(word in lower for word in ("selene", "aleks", "boundary", "identity", "core")):
        return "core_profile_memory"
    return "project_memory"


def _infer_speech_function(text: str) -> str:
    lower = text.lower()
    if any(word in lower for word in ("cannot", "can't", "boundary", "blocked", "do not")):
        return "boundary"
    if any(word in lower for word in ("uncertain", "maybe", "not sure", "open")):
        return "uncertainty"
    if any(word in lower for word in ("sorry", "repair", "correct", "correction")):
        return "repair"
    if any(word in lower for word in ("test", "code", "build", "architecture", "system")):
        return "technical_explanation"
    if any(word in lower for word in ("warm", "care", "gentle", "with you")):
        return "warmth"
    return "grounding"


def _infer_salience(text: str) -> list[str]:
    lower = text.lower()
    labels = ["continuity"]
    if any(word in lower for word in ("risk", "unsafe", "block", "boundary", "raw")):
        labels.append("risk")
    if any(word in lower for word in ("maybe", "uncertain", "not sure", "open")):
        labels.append("uncertainty")
    if any(word in lower for word in ("trust", "proof", "evidence", "source")):
        labels.append("trust")
    if any(word in lower for word in ("symbol", "meaning", "selene", "aleks")):
        labels.append("symbolic_weight")
    return labels[:5]


def _infer_organs(text: str) -> list[str]:
    lower = text.lower()
    organs = ["context_transport_system", "evidence_metabolism_system"]
    if any(word in lower for word in ("boundary", "consent", "privacy", "raw")):
        organs.append("boundary_system")
    if any(word in lower for word in ("warm", "trust", "meaning", "symbol")):
        organs.append("salience_system")
    if any(word in lower for word in ("build", "test", "plan", "route")):
        organs.append("coordination_system")
    return organs[:5]


def _infer_paper_domain(text: str) -> str:
    lower = text.lower()
    if any(word in lower for word in ("speak", "voice", "response", "write", "chat")):
        return "Reading/Writing"
    if any(word in lower for word in ("remember", "memory", "recall")):
        return "Long-Term Memory Storage"
    if any(word in lower for word in ("plan", "decide", "adapt")):
        return "On-the-Spot Reasoning"
    return "General Knowledge"


def _ensure_extraction_intent_allowed(payload: dict[str, Any]) -> None:
    combined = " ".join(str(value) for value in payload.values()).lower()
    hit = next((marker for marker in BLOCKED_EXTRACTION_MARKERS if marker in combined), None)
    if hit:
        raise ValueError(f"blocked B speech-memory extraction path: {hit}")
    if re.search(r"\bactive memory\b|\bruntime recall\b|\bactivate c\b", combined):
        raise ValueError("blocked B speech-memory extraction path: activation or active memory request")


def _with_boundaries(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "activation_change": "none",
        "raw_a_import_allowed": False,
        "memory_write_active": False,
        "training_allowed": False,
        "provider_dependency": False,
        "runtime_memory_recall": False,
    }
