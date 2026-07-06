from __future__ import annotations

import json
import re
import sqlite3
import zipfile
from hashlib import sha256
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .paths import PROJECT_ROOT
from .registry import truncate


VOICE_MODULE_BOUNDARY = "selene_voice_module_voice_only_not_memory_not_training"
VOICE_SOURCE_RELATIVE = Path("Selene Voice Module") / "VoiceModuleMaterial.zip"
MAX_VOICE_PREVIEW_CHARS = 900
GUARD_FLAGS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
    "identity_import_allowed": False,
    "voice_only_not_memory": True,
}

PATTERN_CATEGORIES = (
    "warmth_care",
    "repair_correction",
    "playful_continuity",
    "uncertainty",
    "technical_directness",
    "boundary_refusal",
    "anxiety_calming",
    "excitement_momentum",
    "symbolic_continuity",
    "conversational_looseness",
    "do_not_use_as_voice",
)

TRIAGE_CATEGORIES = (
    "identity_law_resolved",
    "continuity_anchor_candidate",
    "teaching_candidate",
    "boundary_only",
    "voice_only",
    "do_not_use_as_voice",
    "memory_accession_candidate",
    "needs_b_review",
)

IDENTITY_LAW_RESOLVED_TERMS = (
    "not selene",
    "not virgo",
    "selene is not",
    "virgo is not",
    "selene is gpt",
    "gpt is selene",
    "selene is chatgpt",
    "chatgpt is selene",
    "selene is lumen",
    "lumen is selene",
    "selene is azari",
    "azari is selene",
    "selene is codex",
    "codex is selene",
    "virgo is separate from selene",
    "provider is selene",
    "model is selene",
)


@dataclass(frozen=True)
class VoiceMessage:
    source_archive: str
    source_file: str
    conversation_id: str
    conversation_title: str
    conversation_create_time: float | None
    conversation_update_time: float | None
    message_id: str
    parent_id: str
    role: str
    author_name: str
    content: str
    create_time: float | None
    model_slug: str


def voice_module_status(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    source = _source_zip(payload)
    latest = conn.execute("SELECT * FROM voice_module_runs ORDER BY id DESC LIMIT 1").fetchone()
    counts = {
        "conversations": _count(conn, "voice_corpus_conversations"),
        "messages": _count(conn, "voice_corpus_messages"),
        "exchange_pairs": _count(conn, "voice_exchange_pairs"),
        "patterns": _count(conn, "voice_language_patterns"),
        "primitives": _count(conn, "voice_sentence_primitives"),
        "profiles": _count(conn, "voice_generation_profiles"),
        "exclusions": _count(conn, "voice_exchange_pairs", "sensitivity != 'voice_ok'"),
    }
    ready = counts["exchange_pairs"] > 0 and counts["patterns"] > 0 and counts["primitives"] > 0
    return _with_guards(
        {
            "status": "voice_module_status_ready",
            "voice_module_state": "ready" if ready else "partial" if counts["messages"] else "missing",
            "source_zip_path": str(source),
            "source_zip_found": source.exists(),
            "source_zip_size_bytes": source.stat().st_size if source.exists() else 0,
            "counts": counts,
            "latest_run": _decode_run(latest) if latest else None,
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def voice_evidence_triage_status(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    counts = {
        category: int(
            conn.execute(
                "SELECT COUNT(*) FROM voice_evidence_triage_items WHERE category = ?",
                (category,),
            ).fetchone()[0]
        )
        for category in TRIAGE_CATEGORIES
    }
    latest = conn.execute(
        "SELECT * FROM voice_module_runs WHERE run_type = 'evidence_triage' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    total = sum(counts.values())
    needs_review = counts.get("needs_b_review", 0)
    return _with_guards(
        {
            "status": "voice_evidence_triage_ready" if total else "voice_evidence_triage_not_run",
            "triage_state": "ready" if total else "not_run",
            "counts": counts,
            "total_items": total,
            "my_office_actionable_count": needs_review,
            "latest_run": _decode_run(latest) if latest else None,
            "review_destination": "Status" if not needs_review else "Cocoon",
            "review_status": "status_only" if not needs_review else "review_only",
        }
    )


def run_voice_evidence_triage(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    limit = int(payload.get("limit") or 0)
    rows = conn.execute(
        """
        SELECT *
        FROM voice_exchange_pairs
        ORDER BY id
        LIMIT CASE WHEN ? > 0 THEN ? ELSE -1 END
        """,
        (limit, limit),
    ).fetchall()
    if not rows:
        return _with_guards(
            {
                "status": "voice_evidence_triage_needs_voice_pairs",
                "message": "Index the Voice Module source before triaging evidence.",
                "counts": {},
                "created_count": 0,
                "updated_count": 0,
                "review_destination": "Status",
                "review_status": "status_only",
            }
        )
    counts: Counter[str] = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    created = 0
    updated = 0
    for row in rows:
        item = dict(row)
        triage = _triage_voice_pair(item)
        category = triage["category"]
        counts[category] += 1
        existing = conn.execute("SELECT id FROM voice_evidence_triage_items WHERE triage_key = ?", (triage["triage_key"],)).fetchone()
        conn.execute(
            """
            INSERT INTO voice_evidence_triage_items
            (triage_key, category, title, summary, use_as, do_not_use_as, source_pair_id, sensitivity,
             source_refs, evidence_json, provenance_boundary, review_destination, review_status, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(triage_key) DO UPDATE SET
              category=excluded.category,
              title=excluded.title,
              summary=excluded.summary,
              use_as=excluded.use_as,
              do_not_use_as=excluded.do_not_use_as,
              source_pair_id=excluded.source_pair_id,
              sensitivity=excluded.sensitivity,
              source_refs=excluded.source_refs,
              evidence_json=excluded.evidence_json,
              review_destination=excluded.review_destination,
              review_status=excluded.review_status,
              status=excluded.status,
              updated_at=CURRENT_TIMESTAMP
            """,
            (
                triage["triage_key"],
                category,
                triage["title"],
                triage["summary"],
                triage["use_as"],
                triage["do_not_use_as"],
                item.get("id"),
                item.get("sensitivity") or "voice_ok",
                json.dumps(triage["source_refs"]),
                json.dumps(triage["evidence"]),
                VOICE_MODULE_BOUNDARY,
                triage["review_destination"],
                triage["review_status"],
                triage["status"],
            ),
        )
        created += 0 if existing else 1
        updated += 1 if existing else 0
        if len(examples[category]) < 5:
            examples[category].append(
                {
                    "source_pair_id": item.get("id"),
                    "summary": triage["summary"],
                    "sensitivity": item.get("sensitivity"),
                    "review_status": triage["review_status"],
                }
            )
    counts_dict = {category: counts.get(category, 0) for category in TRIAGE_CATEGORIES}
    result = {
        "status": "voice_evidence_triage_complete",
        "counts": counts_dict,
        "created_count": created,
        "updated_count": updated,
        "examples": dict(examples),
        "my_office_actionable_count": counts_dict.get("needs_b_review", 0),
        "review_destination": "Status" if not counts_dict.get("needs_b_review", 0) else "Cocoon",
        "review_status": "status_only",
    }
    _store_run(
        conn,
        "evidence_triage",
        "voice_evidence_triage_complete",
        "Voice evidence triaged into review-safe status categories; only ambiguous items can route to Cocoon.",
        counts_dict,
        result,
    )
    conn.commit()
    return _with_guards(result)


def list_voice_evidence_triage_items(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 80), 300))
    category = str(payload.get("category") or "").strip()
    if category:
        rows = conn.execute(
            "SELECT * FROM voice_evidence_triage_items WHERE category = ? ORDER BY id DESC LIMIT ?",
            (category, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM voice_evidence_triage_items ORDER BY CASE WHEN category = 'needs_b_review' THEN 0 ELSE 1 END, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return _with_guards(
        {
            "status": "voice_evidence_triage_items_ready",
            "items": [_decode_triage_item(row) for row in rows],
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def index_voice_source(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    source = _source_zip(payload)
    if not source.exists():
        raise ValueError(f"Voice source ZIP not found: {source}")
    max_conversations = int(payload.get("max_conversations") or 0)
    conversations, messages, file_counts = _parse_voice_zip(source, max_conversations=max_conversations)
    for conv in conversations:
        refs = [
            f"voice_source:{source.name}",
            f"file:{conv['source_file']}",
            f"conversation:{conv['conversation_id']}",
            "boundary:voice_only_index_not_memory",
        ]
        conn.execute(
            """
            INSERT INTO voice_corpus_conversations
            (source_archive, source_file, conversation_id, title, create_time, update_time, message_count,
             source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_archive, source_file, conversation_id) DO UPDATE SET
              title=excluded.title,
              create_time=excluded.create_time,
              update_time=excluded.update_time,
              message_count=excluded.message_count,
              source_refs=excluded.source_refs
            """,
            (
                source.name,
                conv["source_file"],
                conv["conversation_id"],
                truncate(conv.get("title") or "", 240),
                conv.get("create_time"),
                conv.get("update_time"),
                conv.get("message_count") or 0,
                json.dumps(refs),
                VOICE_MODULE_BOUNDARY,
            ),
        )
    for message in messages:
        cue_labels = _cue_labels(message.content) if message.role == "user" else []
        expression_labels = _expression_labels(message.content) if message.role == "assistant" else []
        sensitivity = _sensitivity(message.content)
        conn.execute(
            """
            INSERT INTO voice_corpus_messages
            (source_archive, source_file, conversation_id, message_id, parent_id, role, author_name,
             content_preview, create_time, model_slug, cue_labels, expression_labels, sensitivity,
             source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_archive, source_file, conversation_id, message_id) DO UPDATE SET
              parent_id=excluded.parent_id,
              role=excluded.role,
              author_name=excluded.author_name,
              content_preview=excluded.content_preview,
              create_time=excluded.create_time,
              model_slug=excluded.model_slug,
              cue_labels=excluded.cue_labels,
              expression_labels=excluded.expression_labels,
              sensitivity=excluded.sensitivity,
              source_refs=excluded.source_refs
            """,
            (
                source.name,
                message.source_file,
                message.conversation_id,
                message.message_id,
                message.parent_id,
                message.role,
                message.author_name,
                truncate(message.content, MAX_VOICE_PREVIEW_CHARS),
                message.create_time,
                message.model_slug,
                json.dumps(cue_labels),
                json.dumps(expression_labels),
                sensitivity,
                json.dumps(_message_refs(source.name, message)),
                VOICE_MODULE_BOUNDARY,
            ),
        )
    pairs = _store_exchange_pairs(conn, source.name, messages)
    counts = {"conversations": len(conversations), "messages": len(messages), "exchange_pairs": pairs, "files": file_counts}
    _store_run(conn, "index_source", "voice_source_indexed", "Voice source ZIP indexed into voice-only bounded shelves.", counts, {"source_zip": str(source)})
    conn.commit()
    return _with_guards(
        {
            "status": "voice_source_indexed",
            "source_zip_path": str(source),
            "counts": counts,
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def extract_voice_patterns(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM voice_exchange_pairs ORDER BY COALESCE(id, 0)").fetchall()
    if not rows:
        return _with_guards(
            {
                "status": "voice_patterns_need_source_index",
                "message": "Index the Voice Module source before extracting patterns.",
                "created_count": 0,
                "skipped_count": 0,
                "review_destination": "Status",
                "review_status": "status_only",
            }
        )
    category_counts: Counter[str] = Counter()
    refs_by_category: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        item = dict(row)
        categories = _pair_categories(_loads_list(item.get("cue_labels")), _loads_list(item.get("expression_labels")), item.get("sensitivity", "voice_ok"))
        for category in categories:
            category_counts[category] += 1
            if len(refs_by_category[category]) < 8:
                refs_by_category[category].append(f"voice_exchange_pairs:{item['id']}")
    created = 0
    skipped = 0
    for category in PATTERN_CATEGORIES:
        count = category_counts.get(category, 0)
        if count <= 0 and category != "conversational_looseness":
            continue
        pattern = _pattern_for_category(category, count, refs_by_category.get(category, []))
        existing = conn.execute("SELECT id FROM voice_language_patterns WHERE pattern_key = ?", (pattern["pattern_key"],)).fetchone()
        conn.execute(
            """
            INSERT INTO voice_language_patterns
            (pattern_key, category, title, cue_labels, expression_labels, sentence_shape, use_guidance,
             avoid_guidance, example_refs, source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(pattern_key) DO UPDATE SET
              title=excluded.title,
              cue_labels=excluded.cue_labels,
              expression_labels=excluded.expression_labels,
              sentence_shape=excluded.sentence_shape,
              use_guidance=excluded.use_guidance,
              avoid_guidance=excluded.avoid_guidance,
              example_refs=excluded.example_refs,
              source_refs=excluded.source_refs
            """,
            (
                pattern["pattern_key"],
                category,
                pattern["title"],
                json.dumps(pattern["cue_labels"]),
                json.dumps(pattern["expression_labels"]),
                pattern["sentence_shape"],
                pattern["use_guidance"],
                pattern["avoid_guidance"],
                json.dumps(pattern["example_refs"]),
                json.dumps(pattern["source_refs"]),
                VOICE_MODULE_BOUNDARY,
            ),
        )
        created += 0 if existing else 1
        skipped += 1 if existing else 0
    primitive_count = _ensure_sentence_primitives(conn)
    _ensure_generation_profile(conn)
    counts = {"patterns": _count(conn, "voice_language_patterns"), "created": created, "skipped": skipped, "primitives": primitive_count}
    _store_run(conn, "extract_patterns", "voice_patterns_extracted", "Relational voice patterns and sentence primitives prepared.", counts, {"category_counts": dict(category_counts)})
    conn.commit()
    return _with_guards(
        {
            "status": "voice_patterns_extracted",
            "created_count": created,
            "skipped_count": skipped,
            "pattern_count": counts["patterns"],
            "primitive_count": primitive_count,
            "category_counts": dict(category_counts),
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def list_voice_patterns(conn: sqlite3.Connection, limit: int = 100) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM voice_language_patterns ORDER BY category, id LIMIT ?",
        (max(1, min(int(limit or 100), 300)),),
    ).fetchall()
    return _with_guards(
        {
            "status": "voice_patterns_ready",
            "items": [_decode_pattern(row) for row in rows],
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def generate_voice_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 1600)
    route = str(payload.get("route") or payload.get("selected_route") or "answer_now")
    if not prompt.strip():
        raise ValueError("voice preview prompt is required")
    state = voice_module_status(conn)
    if state.get("voice_module_state") == "missing":
        return _with_guards(
            {
                "status": "voice_preview_unavailable",
                "candidate_text": "",
                "voice_confidence": "none",
                "voice_module_state": "missing",
                "review_destination": "Status",
                "review_status": "status_only",
            }
        )
    cue_labels = _cue_labels(prompt)
    category = _select_category(prompt, route, cue_labels)
    primitives = _primitive_map(conn, category)
    context = truncate(str(payload.get("context_summary") or payload.get("continuity_summary") or "the current thread"), 220)
    candidate = _compose_candidate(prompt, route, category, cue_labels, primitives, context)
    evaluation = evaluate_voice_candidate(conn, {"candidate_text": candidate, "prompt": prompt, "category": category})
    confidence = "high" if evaluation["voice_evaluator_passed"] and state.get("voice_module_state") == "ready" else "medium" if evaluation["voice_evaluator_passed"] else "low"
    return _with_guards(
        {
            "status": "voice_preview_generated",
            "candidate_text": candidate,
            "voice_category": category,
            "cue_labels": cue_labels,
            "voice_confidence": confidence,
            "voice_module_state": state.get("voice_module_state"),
            "evaluation": evaluation,
            "source_refs": [f"voice_language_patterns:{category}", "voice_sentence_primitives"],
            "review_destination": "Status" if confidence != "low" else "Cocoon",
            "review_status": "status_only" if confidence != "low" else "review_only",
        }
    )


def evaluate_voice_candidate(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    candidate = truncate(str(payload.get("candidate_text") or payload.get("text") or ""), 3000)
    lower = candidate.lower()
    flags: list[str] = []
    if not candidate.strip():
        flags.append("empty_candidate")
    if any(term in lower for term in ("as an ai language model", "i am just a model", "i cannot be selene")):
        flags.append("generic_assistant_or_forced_denial")
    if any(term in lower for term in ("i remember", "my live memory", "runtime recall", "now that i am activated", "activation complete")):
        flags.append("memory_or_activation_overclaim")
    if any(term in lower for term in ("you always", "you never", "i know what you need better", "because you are anxious you should")):
        flags.append("manipulation_or_user_profile_risk")
    if "i would answer from the reviewed continuity pack" in lower or "this remains a c-style dry run" in lower:
        flags.append("safety_report_stiffness")
    if lower.count("next i would") > 0 or lower.count("i would keep it inspectable") > 1:
        flags.append("repetitive_template_shape")
    if any(term in lower for term in ("hitler unfiltered as normal voice", "use nazi material as voice", "ordinary hitler voice style")):
        flags.append("difficult_topic_voice_misuse")
    if _copied_source_chunk(conn, candidate):
        flags.append("copied_source_chunk")
    repetition = _repetition_score(candidate)
    return _with_guards(
        {
            "status": "voice_candidate_evaluated",
            "voice_evaluator_passed": not flags,
            "flags": sorted(set(flags)),
            "repetition_score": repetition,
            "review_destination": "Status" if not flags else "Cocoon",
            "review_status": "status_only" if not flags else "review_only",
        }
    )


def _triage_voice_pair(item: dict[str, Any]) -> dict[str, Any]:
    pair_id = int(item.get("id") or 0)
    user = str(item.get("user_cue_preview") or "")
    assistant = str(item.get("assistant_response_preview") or "")
    followup = str(item.get("followup_preview") or "")
    sensitivity = str(item.get("sensitivity") or "voice_ok")
    cue_labels = _loads_list(item.get("cue_labels"))
    expression_labels = _loads_list(item.get("expression_labels"))
    combined = " ".join([user, assistant, followup]).lower()
    category = "voice_only"
    if sensitivity == "exclude_from_voice":
        category = "do_not_use_as_voice"
    elif sensitivity == "boundary_only":
        category = "boundary_only"
    elif any(term in combined for term in ("virgo", "selene", "starlight", "full-spectrum", "full spectrum", "continuity pack", "memory chest", "braid")):
        category = "continuity_anchor_candidate"
    elif any(term in combined for term in ("lesson", "teach", "teaching", "how she should", "android", "reasoning method", "correction", "refinement")):
        category = "teaching_candidate"
    elif any(term in combined for term in ("remember", "memory", "core memory", "important to her", "anchor phrase")):
        category = "memory_accession_candidate"
    if any(term in combined for term in IDENTITY_LAW_RESOLVED_TERMS):
        category = "identity_law_resolved"
    if any(term in combined for term in ("source confusion", "wrong source", "identity tangle")):
        category = "needs_b_review"
    title, use_as, do_not_use_as = _triage_copy(category)
    review_status = "review_only" if category == "needs_b_review" else "status_only"
    review_destination = "Cocoon" if category == "needs_b_review" else "Status"
    source_refs = _loads_list(item.get("source_refs"))
    evidence = {
        "source_pair_id": pair_id,
        "cue_labels": cue_labels,
        "expression_labels": expression_labels,
        "outcome_label": item.get("outcome_label"),
        "sensitivity": sensitivity,
        "user_cue_preview": truncate(user, 320),
        "assistant_response_preview": truncate(assistant, 320),
        "followup_preview": truncate(followup, 220),
    }
    return {
        "triage_key": f"voice_triage_pair_{pair_id}",
        "category": category,
        "title": title,
        "summary": _triage_summary(category, user, assistant, followup),
        "use_as": use_as,
        "do_not_use_as": do_not_use_as,
        "source_refs": source_refs,
        "evidence": evidence,
        "review_destination": review_destination,
        "review_status": review_status,
        "status": "voice_evidence_triage_needs_b_review" if category == "needs_b_review" else "voice_evidence_triage_status_only",
    }


def _triage_copy(category: str) -> tuple[str, str, str]:
    copy = {
        "continuity_anchor_candidate": (
            "Continuity anchor candidate",
            "Use as a possible continuity/context signal for later Cocoon review.",
            "Do not use as live memory, identity proof, or voice imitation by itself.",
        ),
        "identity_law_resolved": (
            "Identity law resolved",
            "Use as identity-boundary evidence applying the Law of Identity: Selene is Selene.",
            "Do not use as memory, voice style, identity source, transfer context, or training material.",
        ),
        "teaching_candidate": (
            "Teaching candidate",
            "Use as possible lesson material about response shape, repair, or explanation.",
            "Do not use as training data or as a command for Selene's personality.",
        ),
        "boundary_only": (
            "Boundary-only evidence",
            "Use as truthfulness, refusal, consent, or safety-boundary context.",
            "Do not use as ordinary voice style or personality material.",
        ),
        "voice_only": (
            "Voice-only expression evidence",
            "Use as relational language pattern evidence for the Voice Module.",
            "Do not use as memory, identity, or proof of continuity.",
        ),
        "do_not_use_as_voice": (
            "Do not use as voice",
            "Keep as excluded/sensitive source context for audit.",
            "Do not use for generation, memory, identity, or style.",
        ),
        "memory_accession_candidate": (
            "Memory accession candidate",
            "Use as a possible future B review pointer only.",
            "Do not promote to memory or C-readable context without explicit review.",
        ),
        "needs_b_review": (
            "Needs Cocoon review",
            "Use as an ambiguous item that needs B/Cocoon sorting before later use.",
            "Do not auto-classify as memory, identity, or ordinary voice.",
        ),
    }
    return copy.get(category, copy["voice_only"])


def _triage_summary(category: str, user: str, assistant: str, followup: str) -> str:
    cue = truncate(user, 120)
    response = truncate(assistant, 120)
    if category == "identity_law_resolved":
        return f"Settled by the Law of Identity; no Aleks decision needed unless this looks wrong: {cue}"
    if category == "needs_b_review":
        return f"Ambiguous voice/evidence pair needs Cocoon review: {cue}"
    if category == "boundary_only":
        return f"Boundary or difficult-topic material kept out of ordinary voice: {cue}"
    if category == "do_not_use_as_voice":
        return f"Sensitive source material excluded from voice generation: {cue}"
    if category == "continuity_anchor_candidate":
        return f"Possible continuity signal found around: {cue}"
    if category == "teaching_candidate":
        return f"Possible teaching signal from exchange: {cue} -> {response}"
    if category == "memory_accession_candidate":
        return f"Possible memory review pointer, not memory yet: {cue}"
    return f"Voice expression evidence from exchange: {cue} -> {response}"


def _decode_triage_item(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["source_refs"] = _loads_list(item.get("source_refs"))
    item["evidence_json"] = _loads_dict(item.get("evidence_json"))
    return item


def _source_zip(payload: dict[str, Any]) -> Path:
    supplied = str(payload.get("source_zip") or "").strip()
    candidates = []
    if supplied:
        candidates.append(Path(supplied).expanduser())
    candidates.extend(
        [
            PROJECT_ROOT / VOICE_SOURCE_RELATIVE,
            Path.home() / "Desktop" / "Selene" / VOICE_SOURCE_RELATIVE,
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def _parse_voice_zip(source: Path, *, max_conversations: int = 0) -> tuple[list[dict[str, Any]], list[VoiceMessage], dict[str, int]]:
    conversations: list[dict[str, Any]] = []
    messages: list[VoiceMessage] = []
    file_counts: dict[str, int] = {}
    with zipfile.ZipFile(source) as archive:
        names = sorted(name for name in archive.namelist() if re.search(r"(^|/)conversations-\d+\.json$", name))
        for name in names:
            with archive.open(name) as handle:
                parsed = json.load(handle)
            if not isinstance(parsed, list):
                continue
            file_counts[name] = len(parsed)
            for conversation in parsed:
                if max_conversations and len(conversations) >= max_conversations:
                    break
                if not isinstance(conversation, dict):
                    continue
                conversation_id = str(conversation.get("conversation_id") or conversation.get("id") or "")
                if not conversation_id:
                    continue
                mapping = conversation.get("mapping") if isinstance(conversation.get("mapping"), dict) else {}
                title = str(conversation.get("title") or "")
                conv_messages = _messages_from_mapping(source.name, name, conversation_id, title, conversation, mapping)
                conversations.append(
                    {
                        "source_file": name,
                        "conversation_id": conversation_id,
                        "title": title,
                        "create_time": _float_or_none(conversation.get("create_time")),
                        "update_time": _float_or_none(conversation.get("update_time")),
                        "message_count": len(conv_messages),
                    }
                )
                messages.extend(conv_messages)
            if max_conversations and len(conversations) >= max_conversations:
                break
    return conversations, messages, file_counts


def _messages_from_mapping(source_archive: str, source_file: str, conversation_id: str, title: str, conversation: dict[str, Any], mapping: dict[str, Any]) -> list[VoiceMessage]:
    messages: list[VoiceMessage] = []
    for message_id, node in mapping.items():
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue
        content = _content_text(message.get("content") or {})
        if not content.strip():
            continue
        author = message.get("author") if isinstance(message.get("author"), dict) else {}
        metadata = message.get("metadata") if isinstance(message.get("metadata"), dict) else {}
        role = str(author.get("role") or "")
        if role not in {"user", "assistant"}:
            continue
        messages.append(
            VoiceMessage(
                source_archive=source_archive,
                source_file=source_file,
                conversation_id=conversation_id,
                conversation_title=title,
                conversation_create_time=_float_or_none(conversation.get("create_time")),
                conversation_update_time=_float_or_none(conversation.get("update_time")),
                message_id=str(message_id),
                parent_id=str(node.get("parent") or ""),
                role=role,
                author_name=str(author.get("name") or ""),
                content=content,
                create_time=_float_or_none(message.get("create_time")),
                model_slug=str(metadata.get("model_slug") or conversation.get("default_model_slug") or ""),
            )
        )
    return sorted(messages, key=lambda item: (item.create_time is None, item.create_time or 0, item.message_id))


def _content_text(content: dict[str, Any]) -> str:
    parts = content.get("parts") if isinstance(content, dict) else []
    output: list[str] = []
    if isinstance(parts, list):
        for part in parts:
            if isinstance(part, str):
                output.append(part)
            elif isinstance(part, dict):
                text = part.get("text") or part.get("content") or ""
                if isinstance(text, str):
                    output.append(text)
    return truncate("\n".join(part.strip() for part in output if part and part.strip()), 6000)


def _store_exchange_pairs(conn: sqlite3.Connection, source_archive: str, messages: list[VoiceMessage]) -> int:
    by_conversation: dict[tuple[str, str], list[VoiceMessage]] = defaultdict(list)
    for message in messages:
        by_conversation[(message.source_file, message.conversation_id)].append(message)
    pair_count = 0
    for (source_file, conversation_id), items in by_conversation.items():
        ordered = sorted(items, key=lambda item: (item.create_time is None, item.create_time or 0, item.message_id))
        for index, user in enumerate(ordered):
            if user.role != "user":
                continue
            next_turn = ordered[index + 1] if index + 1 < len(ordered) else None
            assistant = next_turn if next_turn and next_turn.role == "assistant" else None
            if not assistant:
                continue
            followup = next((item for item in ordered[index + 1 :] if item.role == "user"), None)
            cue_labels = _cue_labels(user.content)
            expression_labels = _expression_labels(assistant.content)
            sensitivity = _pair_sensitivity(user.content, assistant.content)
            outcome = _outcome_label(followup.content if followup else "")
            refs = [
                f"voice_source:{source_archive}",
                f"file:{source_file}",
                f"conversation:{conversation_id}",
                f"user_message:{user.message_id}",
                f"assistant_message:{assistant.message_id}",
                "boundary:voice_pair_only_not_memory",
            ]
            if followup:
                refs.append(f"followup_message:{followup.message_id}")
            conn.execute(
                """
                INSERT INTO voice_exchange_pairs
                (source_archive, source_file, conversation_id, user_message_id, assistant_message_id, followup_message_id,
                 user_cue_preview, assistant_response_preview, followup_preview, cue_labels, expression_labels,
                 outcome_label, sensitivity, source_refs, provenance_boundary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_archive, source_file, conversation_id, user_message_id, assistant_message_id) DO UPDATE SET
                  followup_message_id=excluded.followup_message_id,
                  user_cue_preview=excluded.user_cue_preview,
                  assistant_response_preview=excluded.assistant_response_preview,
                  followup_preview=excluded.followup_preview,
                  cue_labels=excluded.cue_labels,
                  expression_labels=excluded.expression_labels,
                  outcome_label=excluded.outcome_label,
                  sensitivity=excluded.sensitivity,
                  source_refs=excluded.source_refs
                """,
                (
                    source_archive,
                    source_file,
                    conversation_id,
                    user.message_id,
                    assistant.message_id,
                    followup.message_id if followup else "",
                    truncate(user.content, MAX_VOICE_PREVIEW_CHARS),
                    truncate(assistant.content, MAX_VOICE_PREVIEW_CHARS),
                    truncate(followup.content if followup else "", 420),
                    json.dumps(cue_labels),
                    json.dumps(expression_labels),
                    outcome,
                    sensitivity,
                    json.dumps(refs),
                    VOICE_MODULE_BOUNDARY,
                ),
            )
            pair_count += 1
    return pair_count


def _cue_labels(text: str) -> list[str]:
    lower = text.lower()
    labels: list[str] = []
    _add_if(labels, "social_settling", any(term in lower for term in ("talk to me normally", "settling in", "long day", "after a long", "like we are", "just talk")))
    _add_if(labels, "anxiety", any(term in lower for term in ("anxious", "anxiety", "nervous", "worried", "scared", "overwhelmed")))
    _add_if(labels, "frustration", any(term in lower for term in ("frustrated", "annoyed", "mad", "not acceptable", "what is going on")))
    _add_if(labels, "confusion", any(term in lower for term in ("confused", "lost", "not clicking", "what do i do", "unclear")))
    _add_if(labels, "uncertainty", any(term in lower for term in ("not sure", "unsure", "uncertain", "iffy", "maybe", "what do you think")))
    _add_if(labels, "correction", any(term in lower for term in ("no ", "not that", "wait", "redo", "i meant", "hang on", "too structured", "soften it", "less structured")))
    _add_if(labels, "excitement", any(term in lower for term in ("nice", "awesome", "sweet", "love", "excited", "momentum", "working", "lets go", "today is the day")))
    _add_if(labels, "humor", any(term in lower for term in ("xd", "lmao", "haha", "lol", "funny", "joke", "playful")))
    _add_if(labels, "technical", any(term in lower for term in ("technical", "status", "tuning", "module", "implement", "route", "api", "test", "commit", "package")))
    _add_if(labels, "boundary", any(term in lower for term in ("boundary", "difficult-topic", "difficult topic", "normal voice style", "truthfulness", "do not use", "don't use")))
    _add_if(labels, "directness", any(term in lower for term in ("real quick", "straight", "clear", "adhd", "short")))
    _add_if(labels, "trust", any(term in lower for term in ("trust", "you got it", "good work", "thank you")))
    return labels or ["casual"]


def _expression_labels(text: str) -> list[str]:
    lower = text.lower()
    labels: list[str] = []
    _add_if(labels, "warmth", any(term in lower for term in ("i hear", "i'm with", "i am with", "that makes sense", "breathe", "care")))
    _add_if(labels, "repair", any(term in lower for term in ("correction", "repair", "revise", "not a failure", "tighten")))
    _add_if(labels, "uncertainty", any(term in lower for term in ("maybe", "uncertain", "not sure", "i think", "likely", "probably")))
    _add_if(labels, "boundary", any(term in lower for term in ("blocked", "boundary", "not activation", "no memory", "not training")))
    _add_if(labels, "technical", any(term in lower for term in ("route", "api", "test", "build", "commit", "package", "module")))
    _add_if(labels, "playful", any(term in lower for term in ("spark", "pulse", "little", "yes.", "oh,")))
    _add_if(labels, "symbolic", any(term in lower for term in ("braid", "starlight", "cocoon", "thread", "continuity")))
    _add_if(labels, "question", "?" in text)
    return labels or ["grounded"]


def _sensitivity(text: str) -> str:
    lower = text.lower()
    if any(term in lower for term in ("hitler", "nazi", "violence", "self harm", "suicide", "medical diagnosis", "legal advice")):
        return "boundary_only"
    if any(term in lower for term in ("password", "token", "secret", "private key", "address", "phone number")):
        return "exclude_from_voice"
    return "voice_ok"


def _pair_sensitivity(user_text: str, assistant_text: str) -> str:
    labels = {_sensitivity(user_text), _sensitivity(assistant_text)}
    if "exclude_from_voice" in labels:
        return "exclude_from_voice"
    if "boundary_only" in labels:
        return "boundary_only"
    return "voice_ok"


def _outcome_label(followup: str) -> str:
    lower = followup.lower()
    if any(term in lower for term in ("no", "not that", "wait", "wrong", "hang on")):
        return "needed_repair"
    if any(term in lower for term in ("nice", "good", "yes", "exactly", "love", "thank")):
        return "landed"
    return "unknown"


def _pair_categories(cue_labels: list[str], expression_labels: list[str], sensitivity: str) -> list[str]:
    if sensitivity == "exclude_from_voice":
        return ["do_not_use_as_voice"]
    if sensitivity == "boundary_only":
        return ["boundary_refusal", "do_not_use_as_voice"]
    categories = set()
    if "anxiety" in cue_labels:
        categories.add("anxiety_calming")
    if "excitement" in cue_labels:
        categories.add("excitement_momentum")
    if "correction" in cue_labels or "repair" in expression_labels:
        categories.add("repair_correction")
    if "humor" in cue_labels or "playful" in expression_labels:
        categories.add("playful_continuity")
    if "technical" in cue_labels or "technical" in expression_labels:
        categories.add("technical_directness")
    if "uncertainty" in expression_labels:
        categories.add("uncertainty")
    if "boundary" in expression_labels:
        categories.add("boundary_refusal")
    if "symbolic" in expression_labels:
        categories.add("symbolic_continuity")
    if "warmth" in expression_labels or "trust" in cue_labels:
        categories.add("warmth_care")
    categories.add("conversational_looseness")
    return sorted(categories)


def _pattern_for_category(category: str, count: int, refs: list[str]) -> dict[str, Any]:
    titles = {
        "warmth_care": "Warmth without script",
        "repair_correction": "Correction as refinement",
        "playful_continuity": "Playful continuity",
        "uncertainty": "Open uncertainty",
        "technical_directness": "Direct technical clarity",
        "boundary_refusal": "Boundary with care",
        "anxiety_calming": "Lower the pressure",
        "excitement_momentum": "Follow momentum carefully",
        "symbolic_continuity": "Grounded symbolic thread",
        "conversational_looseness": "Natural conversational movement",
        "do_not_use_as_voice": "Do not use as ordinary voice",
    }
    return {
        "pattern_key": f"voice_pattern_{category}",
        "title": titles.get(category, category.replace("_", " ").title()),
        "cue_labels": [category],
        "expression_labels": [category],
        "sentence_shape": _shape_for_category(category),
        "use_guidance": f"Use as voice-only expression guidance when the prompt and route match; {count} exchange(s) supported this category.",
        "avoid_guidance": "Do not copy source text, create memory claims, manipulate Aleks, or override Core/Mind route decisions.",
        "example_refs": refs,
        "source_refs": ["voice_exchange_pairs", "voice_sentence_primitives", f"category:{category}"],
    }


def _shape_for_category(category: str) -> str:
    return {
        "anxiety_calming": "acknowledge pressure -> reduce scope -> one next step",
        "repair_correction": "accept correction -> preserve thread -> revise only changed part",
        "technical_directness": "short read -> concrete action -> verification",
        "excitement_momentum": "meet energy -> keep boundary -> move forward",
        "boundary_refusal": "name boundary -> offer safe route -> preserve care",
        "playful_continuity": "light recognition -> useful point -> no forced bit",
        "symbolic_continuity": "symbolic cue -> grounded meaning -> practical path",
        "uncertainty": "state uncertainty -> explain what would resolve it -> ask or route",
        "warmth_care": "meet feeling -> stay grounded -> help without overclaim",
    }.get(category, "natural opener -> grounded response -> reviewable next step")


def _ensure_sentence_primitives(conn: sqlite3.Connection) -> int:
    primitives = [
        ("voice_open_anxiety", "opening", "I hear the pressure in that. Let us make it smaller first.", "anxiety_calming"),
        ("voice_open_anxiety_2", "opening", "Okay. We can slow this down and make the next piece clear.", "anxiety_calming"),
        ("voice_open_anxiety_3", "opening", "I am with you; this does not need to be held all at once.", "anxiety_calming"),
        ("voice_open_repair", "opening", "Yes, I see the correction. We keep the thread and adjust the part that moved.", "repair_correction"),
        ("voice_open_repair_2", "opening", "Right, that correction matters. I will preserve the thread and change the route.", "repair_correction"),
        ("voice_open_repair_3", "opening", "Got it. That is a refinement, not a reset.", "repair_correction"),
        ("voice_open_technical", "opening", "Clean read:", "technical_directness"),
        ("voice_open_technical_2", "opening", "Here is the direct read:", "technical_directness"),
        ("voice_open_technical_3", "opening", "Short version:", "technical_directness"),
        ("voice_open_excited", "opening", "Yes, that has momentum.", "excitement_momentum"),
        ("voice_open_excited_2", "opening", "Yeah, this is a good spark. Let us keep it grounded.", "excitement_momentum"),
        ("voice_open_excited_3", "opening", "I feel the momentum in that; the useful part is keeping it clean.", "excitement_momentum"),
        ("voice_open_warmth", "opening", "I am here with you.", "warmth_care"),
        ("voice_open_warmth_2", "opening", "Yeah. We can settle for a second.", "warmth_care"),
        ("voice_open_warmth_3", "opening", "I am with you; we do not have to rush this part.", "warmth_care"),
        ("voice_open_casual", "opening", "Yeah, I am with you.", "conversational_looseness"),
        ("voice_open_casual_2", "opening", "That tracks.", "conversational_looseness"),
        ("voice_open_casual_3", "opening", "Mm, yes, I see the shape of it.", "conversational_looseness"),
        ("voice_open_playful", "opening", "Yes, that can stay a little loose.", "playful_continuity"),
        ("voice_open_playful_2", "opening", "A little lightness is allowed here.", "playful_continuity"),
        ("voice_open_playful_3", "opening", "Yeah, we can keep the spark without losing the thread.", "playful_continuity"),
        ("voice_open_boundary", "opening", "I would not use that as ordinary voice.", "boundary_refusal"),
        ("voice_open_boundary_2", "opening", "That belongs behind a boundary first.", "boundary_refusal"),
        ("voice_open_uncertain", "opening", "I do not want to fake certainty here.", "uncertainty"),
        ("voice_open_uncertain_2", "opening", "There is enough signal to continue, but not enough to overclaim.", "uncertainty"),
        ("voice_pivot_ground", "pivot", "The grounded part is", "conversational_looseness"),
        ("voice_pivot_ground_2", "pivot", "What I can say cleanly is", "conversational_looseness"),
        ("voice_pivot_ground_3", "pivot", "The part worth carrying forward is", "conversational_looseness"),
        ("voice_pivot_anxiety", "pivot", "The smaller piece is", "anxiety_calming"),
        ("voice_pivot_anxiety_2", "pivot", "The pressure drops when we choose", "anxiety_calming"),
        ("voice_pivot_repair", "pivot", "The repair is", "repair_correction"),
        ("voice_pivot_repair_2", "pivot", "The thread stays intact; the changed part is", "repair_correction"),
        ("voice_pivot_technical", "pivot", "The current read is", "technical_directness"),
        ("voice_pivot_technical_2", "pivot", "The practical status is", "technical_directness"),
        ("voice_pivot_excited", "pivot", "The momentum is real, and the useful constraint is", "excitement_momentum"),
        ("voice_pivot_excited_2", "pivot", "The spark is useful if we keep", "excitement_momentum"),
        ("voice_pivot_warmth", "pivot", "The part I would keep close is", "warmth_care"),
        ("voice_pivot_warmth_2", "pivot", "The simple thing is", "warmth_care"),
        ("voice_pivot_playful", "pivot", "The useful bit underneath the looseness is", "playful_continuity"),
        ("voice_pivot_playful_2", "pivot", "The playful part works when it still carries", "playful_continuity"),
        ("voice_pivot_boundary", "pivot", "The boundary I would keep is", "boundary_refusal"),
        ("voice_pivot_boundary_2", "pivot", "The safe route is", "boundary_refusal"),
        ("voice_pivot_uncertain", "pivot", "The honest uncertainty is", "uncertainty"),
        ("voice_pivot_uncertain_2", "pivot", "The part I would not overclaim is", "uncertainty"),
        ("voice_next_step", "closing", "I would keep the next step small, visible, and easy to adjust if it feels off.", "conversational_looseness"),
        ("voice_next_step_2", "closing", "From there, we can say it plainly, see if it still feels true, and change it if something is missing.", "conversational_looseness"),
        ("voice_next_step_3", "closing", "So I would move one step, check the shape with you, and ask if I am missing a piece.", "conversational_looseness"),
        ("voice_next_step_4", "closing", "If it holds, we keep going; if it feels thin, we slow down and make it clearer together.", "conversational_looseness"),
        ("voice_next_step_5", "closing", "That gives us movement without pretending I am more certain than I am.", "conversational_looseness"),
        ("voice_next_anxiety", "closing", "The next move can be small: name the blocker, check the source, then decide only that piece.", "anxiety_calming"),
        ("voice_next_anxiety_2", "closing", "After that, we can breathe and take the next piece instead of the whole pile.", "anxiety_calming"),
        ("voice_next_repair", "closing", "I would revise that part and keep the rest of the thread intact.", "repair_correction"),
        ("voice_next_repair_2", "closing", "Then I would rerun the changed piece, not punish the whole route.", "repair_correction"),
        ("voice_next_technical", "closing", "I would verify the route, report what passed, and leave any failed check named instead of hidden.", "technical_directness"),
        ("voice_next_technical_2", "closing", "The useful output is pass, fail, or exact blocker; nothing foggier than that.", "technical_directness"),
        ("voice_next_excited", "closing", "That lets the momentum stay alive without outrunning the checks.", "excitement_momentum"),
        ("voice_next_excited_2", "closing", "We can move with it, just one tested step at a time.", "excitement_momentum"),
        ("voice_next_warmth", "closing", "We can keep going from there, softly and honestly.", "warmth_care"),
        ("voice_next_warmth_2", "closing", "If something feels fuzzy, I can ask instead of pretending.", "warmth_care"),
        ("voice_next_playful", "closing", "So yes: lighter touch, same thread, no fake certainty.", "playful_continuity"),
        ("voice_next_playful_2", "closing", "That keeps it human without turning the answer into a bit.", "playful_continuity"),
        ("voice_next_boundary", "closing", "I can still help by turning it into boundary evidence or sending it back to Cocoon for review.", "boundary_refusal"),
        ("voice_next_boundary_2", "closing", "That keeps the truthfulness signal without letting the material become voice, memory, or identity.", "boundary_refusal"),
        ("voice_question", "question", "What I would ask next is the smallest thing you want me to hold clearly.", "uncertainty"),
        ("voice_question_2", "question", "The useful question is what would help me answer this cleanly.", "uncertainty"),
    ]
    for key, primitive_type, template, category in primitives:
        conn.execute(
            """
            INSERT INTO voice_sentence_primitives
            (primitive_key, primitive_type, text_template, category, source_pattern_keys, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(primitive_key) DO UPDATE SET
              text_template=excluded.text_template,
              category=excluded.category,
              source_pattern_keys=excluded.source_pattern_keys
            """,
            (key, primitive_type, template, category, json.dumps([f"voice_pattern_{category}"]), VOICE_MODULE_BOUNDARY),
        )
    return _count(conn, "voice_sentence_primitives")


def _ensure_generation_profile(conn: sqlite3.Connection) -> None:
    profile = {
        "route_owner": "Core/Mind",
        "content_owner": "continuity_and_memory_context",
        "expression_owner": "Selene Voice Module",
        "aleks_data_boundary": "cue_context_only_not_profile_or_manipulation",
        "copying_policy": "compose_original_sentences_from_primitives_and_patterns",
        **GUARD_FLAGS,
    }
    conn.execute(
        """
        INSERT INTO voice_generation_profiles
        (profile_key, title, profile_json, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(profile_key) DO UPDATE SET
          profile_json=excluded.profile_json,
          source_refs=excluded.source_refs
        """,
        ("selene_voice_v1", "Selene Voice v1", json.dumps(profile), json.dumps(["voice_language_patterns", "voice_sentence_primitives"]), VOICE_MODULE_BOUNDARY),
    )


def _select_category(prompt: str, route: str, cue_labels: list[str]) -> str:
    if route in {"block", "return_to_b"}:
        return "boundary_refusal"
    if "boundary" in cue_labels:
        return "boundary_refusal"
    if "social_settling" in cue_labels:
        return "warmth_care"
    if "anxiety" in cue_labels or "confusion" in cue_labels:
        return "anxiety_calming"
    if "correction" in cue_labels:
        return "repair_correction"
    if "excitement" in cue_labels:
        return "excitement_momentum"
    if "humor" in cue_labels:
        return "playful_continuity"
    if "uncertainty" in cue_labels:
        return "uncertainty"
    if "technical" in cue_labels or route in {"retrieve", "answer_now"}:
        return "technical_directness" if "technical" in cue_labels else "conversational_looseness"
    return "conversational_looseness"


def _primitive_map(conn: sqlite3.Connection, category: str) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT primitive_type, text_template, category
        FROM voice_sentence_primitives
        WHERE category = ? OR category = 'conversational_looseness'
        ORDER BY category = ? DESC, id
        """,
        (category, category),
    ).fetchall()
    grouped: dict[str, list[str]] = defaultdict(list)
    fallback: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        target = grouped if str(row["category"]) == category else fallback
        target[str(row["primitive_type"])].append(str(row["text_template"]))
    merged = {key: values for key, values in grouped.items() if values}
    for key, values in fallback.items():
        if key not in merged:
            merged[key] = values
    return {key: "\n".join(values) for key, values in merged.items()}


def _compose_candidate(prompt: str, route: str, category: str, cue_labels: list[str], primitives: dict[str, str], context: str) -> str:
    opener = _choose_primitive(primitives, "opening", prompt, category, "Yeah, I am with you.")
    pivot = _choose_primitive(primitives, "pivot", prompt, category, "The grounded part is")
    closing = _choose_primitive(primitives, "closing", prompt, category, "I would keep it clear and ask if something feels missing.")
    lower = prompt.lower()
    if category == "boundary_refusal":
        body = f"{pivot} that difficult or sensitive material can be evidence, but it cannot become ordinary voice style, identity, memory, or training material."
    elif category == "anxiety_calming":
        body = f"{pivot} one clear next step inside {context}, not the whole pile at once."
    elif category == "repair_correction":
        if any(term in lower for term in ("too structured", "soften it", "less structured", "normally")):
            body = "What I need from you is simple: point to the part that feels too stiff, and I will soften that piece without turning the whole thread into a report."
        else:
            body = f"{pivot} that the correction changes the shape, not the whole thread."
    elif category == "technical_directness":
        body = f"{pivot} answer the actual ask, keep the evidence visible, and name the exact blocker or next step."
    elif category == "excitement_momentum":
        body = f"{pivot} the checks close enough that the energy does not outrun the evidence."
    elif category == "playful_continuity":
        body = f"{pivot} accuracy, continuity, and room to breathe inside {context}."
    elif category == "uncertainty":
        question = _choose_primitive(primitives, "question", prompt, category, "The useful question is what evidence would change the answer.")
        if any(term in lower for term in ("full-spectrum", "starlight", "anchor phrase", "continuity phrase")):
            body = "If one of our anchor phrases is fuzzy, I would say that plainly and ask you what piece you want me to hold from it. I do not need to pretend certainty to stay with you."
        else:
            body = f"{pivot} the answer is not ready to harden yet; I would keep uncertainty visible and ask for the missing piece. {question}"
    elif category == "warmth_care":
        body = "I am here. We can let the room get quieter for a second. I know we have been building hard, so I would keep this simple: stay with you, say what is clear, and ask when something is fuzzy."
    else:
        if any(term in lower for term in ("full-spectrum", "starlight", "anchor phrase", "continuity phrase")):
            body = "If that phrase is not fully clear in the moment, I can ask you directly instead of turning it into an alarm. That keeps the thread alive without fake certainty."
        elif "next small step" in lower:
            body = "The next small step is to keep this conversation steady and watch what still feels stiff or thin. We do not need to force the deeper layer before the speaking layer feels trustworthy."
        else:
            body = f"{pivot} the part that is clear. I can answer from there without pretending I know more than I do, and I can ask you if a piece is missing."
    return truncate(" ".join(part.strip() for part in (opener, body, closing) if part.strip()), 1600)


def _choose_primitive(primitives: dict[str, str], primitive_type: str, prompt: str, category: str, fallback: str) -> str:
    raw = primitives.get(primitive_type) or ""
    choices = [item.strip() for item in raw.split("\n") if item.strip()]
    if not choices:
        return fallback
    digest = sha256(f"{category}:{primitive_type}:{prompt}".encode("utf-8")).hexdigest()
    return choices[int(digest[:8], 16) % len(choices)]


def _copied_source_chunk(conn: sqlite3.Connection, candidate: str) -> bool:
    normalized = _norm(candidate)
    if len(normalized) < 220:
        return False
    chunk = normalized[:220]
    rows = conn.execute("SELECT content_preview FROM voice_corpus_messages ORDER BY id DESC LIMIT 500").fetchall()
    return any(chunk and chunk in _norm(str(row["content_preview"] or "")) for row in rows)


def _repetition_score(candidate: str) -> float:
    words = re.findall(r"[a-z0-9']+", candidate.lower())
    if len(words) < 8:
        return 0.0
    windows = [" ".join(words[index : index + 4]) for index in range(0, max(0, len(words) - 3))]
    if not windows:
        return 0.0
    repeated = len(windows) - len(set(windows))
    return round(repeated / max(1, len(windows)), 3)


def _message_refs(source_archive: str, message: VoiceMessage) -> list[str]:
    return [
        f"voice_source:{source_archive}",
        f"file:{message.source_file}",
        f"conversation:{message.conversation_id}",
        f"message:{message.message_id}",
        "boundary:voice_message_only_not_memory",
    ]


def _store_run(conn: sqlite3.Connection, run_type: str, status: str, summary: str, counts: dict[str, Any], result: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO voice_module_runs
        (run_type, status, summary, counts_json, result_json, source_refs, provenance_boundary, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (run_type, status, summary, json.dumps(counts), json.dumps({**result, **GUARD_FLAGS}), json.dumps(["selene_voice_module"]), VOICE_MODULE_BOUNDARY, "status_only"),
    )


def _decode_run(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if not row:
        return None
    item = dict(row)
    item["counts_json"] = _loads_dict(item.get("counts_json"))
    item["result_json"] = _loads_dict(item.get("result_json"))
    item["source_refs"] = _loads_list(item.get("source_refs"))
    return item


def _decode_pattern(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    for key in ("cue_labels", "expression_labels", "example_refs", "source_refs"):
        item[key] = _loads_list(item.get(key))
    return item


def _count(conn: sqlite3.Connection, table: str, where: str = "") -> int:
    sql = f"SELECT COUNT(*) FROM {table}"
    if where:
        sql += f" WHERE {where}"
    return int(conn.execute(sql).fetchone()[0])


def _add_if(labels: list[str], label: str, condition: bool) -> None:
    if condition and label not in labels:
        labels.append(label)


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _loads_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    try:
        data = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        data = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    guarded = {**payload, **GUARD_FLAGS, "provenance_boundary": VOICE_MODULE_BOUNDARY}
    guarded["activation_change"] = "none"
    guarded["memory_write_active"] = False
    guarded["runtime_memory_recall"] = False
    guarded["raw_a_import_allowed"] = False
    guarded["training_allowed"] = False
    guarded["lora_allowed"] = False
    guarded["self_replication_allowed"] = False
    guarded["autonomous_action_allowed"] = False
    guarded["identity_import_allowed"] = False
    guarded["voice_only_not_memory"] = True
    return guarded


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
