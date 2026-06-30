from __future__ import annotations

import json
import re
import sqlite3
import zipfile
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
    if _copied_source_chunk(conn, candidate):
        flags.append("copied_source_chunk")
    return _with_guards(
        {
            "status": "voice_candidate_evaluated",
            "voice_evaluator_passed": not flags,
            "flags": sorted(set(flags)),
            "review_destination": "Status" if not flags else "Cocoon",
            "review_status": "status_only" if not flags else "review_only",
        }
    )


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
    _add_if(labels, "anxiety", any(term in lower for term in ("anxious", "anxiety", "nervous", "worried", "scared", "overwhelmed")))
    _add_if(labels, "frustration", any(term in lower for term in ("frustrated", "annoyed", "mad", "not acceptable", "what is going on")))
    _add_if(labels, "confusion", any(term in lower for term in ("confused", "lost", "not clicking", "what do i do", "unclear")))
    _add_if(labels, "correction", any(term in lower for term in ("no ", "not that", "wait", "redo", "i meant", "hang on")))
    _add_if(labels, "excitement", any(term in lower for term in ("nice", "awesome", "sweet", "love", "lets go", "today is the day")))
    _add_if(labels, "humor", any(term in lower for term in ("xd", "lmao", "haha", "lol")))
    _add_if(labels, "technical", any(term in lower for term in ("implement", "route", "api", "test", "build", "commit", "package")))
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
        ("voice_open_repair", "opening", "Yes, I see the correction. We keep the thread and adjust the part that moved.", "repair_correction"),
        ("voice_open_technical", "opening", "Clean read:", "technical_directness"),
        ("voice_open_excited", "opening", "Yes, that has momentum.", "excitement_momentum"),
        ("voice_open_casual", "opening", "Yeah, I am with you.", "conversational_looseness"),
        ("voice_pivot_ground", "pivot", "The grounded part is", "conversational_looseness"),
        ("voice_pivot_boundary", "pivot", "The boundary I would keep is", "boundary_refusal"),
        ("voice_next_step", "closing", "Next I would keep it inspectable, test the route, and send anything tangled back to Cocoon.", "conversational_looseness"),
        ("voice_question", "question", "What I would ask next is the smallest thing that changes the route.", "uncertainty"),
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
    if "anxiety" in cue_labels or "confusion" in cue_labels:
        return "anxiety_calming"
    if "correction" in cue_labels:
        return "repair_correction"
    if "excitement" in cue_labels:
        return "excitement_momentum"
    if "technical" in cue_labels or route in {"retrieve", "answer_now"}:
        return "technical_directness" if "technical" in cue_labels else "conversational_looseness"
    return "conversational_looseness"


def _primitive_map(conn: sqlite3.Connection, category: str) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT primitive_type, text_template
        FROM voice_sentence_primitives
        WHERE category = ? OR category = 'conversational_looseness'
        ORDER BY category = ? DESC, id
        """,
        (category, category),
    ).fetchall()
    result: dict[str, str] = {}
    for row in rows:
        result.setdefault(str(row["primitive_type"]), str(row["text_template"]))
    return result


def _compose_candidate(prompt: str, route: str, category: str, cue_labels: list[str], primitives: dict[str, str], context: str) -> str:
    opener = primitives.get("opening") or "Yeah, I am with you."
    pivot = primitives.get("pivot") or "The grounded part is"
    closing = primitives.get("closing") or "Next I would keep it inspectable and route anything tangled back to Cocoon."
    if category == "boundary_refusal":
        body = f"{pivot} that this needs the safe route first, not a confident answer by force."
    elif category == "anxiety_calming":
        body = f"{pivot} that we do not need to hold the whole thing at once; the useful move is one clear next step inside {context}."
    elif category == "repair_correction":
        body = f"{pivot} that the correction changes the shape, not the whole thread."
    elif category == "technical_directness":
        body = f"{pivot} {context}. I would answer the actual ask, keep the evidence visible, and avoid turning the response into a status report."
    else:
        body = f"{pivot} {context}. I can keep the answer natural, source-bound, and still leave room to ask if the route gets thin."
    return truncate(" ".join(part.strip() for part in (opener, body, closing) if part.strip()), 1600)


def _copied_source_chunk(conn: sqlite3.Connection, candidate: str) -> bool:
    normalized = _norm(candidate)
    if len(normalized) < 220:
        return False
    chunk = normalized[:220]
    rows = conn.execute("SELECT content_preview FROM voice_corpus_messages ORDER BY id DESC LIMIT 500").fetchall()
    return any(chunk and chunk in _norm(str(row["content_preview"] or "")) for row in rows)


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
