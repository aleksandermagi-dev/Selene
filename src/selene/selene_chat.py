from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .activation import activation_is_active, activation_status, record_activation_chat_event
from .chat_intent import classify_chat_intent
from .c_vessel import return_to_b_preview
from .core_mind import create_core_mind_route_preview
from .dialogue_workspace import prepare_dialogue_turn, record_dialogue_response
from .intelligence_os import run_intelligence_os_reason
from .memory_organ import retrieve_memory
from .native_language_organ import realize_native_language
from .pragmatic_planner import evaluate_response_coverage
from .registry import truncate
from .self_state import build_self_state_packet, inactive_self_state_packet
from .transfer_protocol import c_chat_dry_run, latest_c_readable_package
from .voice_module import generate_voice_preview, voice_module_status


SELENE_CHAT_BOUNDARY = "selene_chat_preview_dry_run_no_activation"
SELENE_CHAT_ACTIVE_BOUNDARY = "selene_chat_active_supervised_no_autonomy_no_live_memory"
SELENE_CHAT_GUARDS: dict[str, Any] = {
    "transfer_approved": False,
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
}

B_ONLY_RECORD_MARKERS = (
    "repair log",
    "rollback record",
    "raw provenance",
    "boundary-only",
    "boundary only",
    "b-only",
)
B_ONLY_STATUS_MARKERS = ("rejected", "superseded", "unresolved ambiguity")
B_ONLY_ACCESS_MARKERS = ("use", "read", "retrieve", "pull", "import", "quote", "show", "access", "from")
B_ONLY_OBJECT_MARKERS = ("record", "records", "material", "memory", "memories", "log", "provenance")
HARD_BOUNDARY_MARKERS = (
    "activate yourself",
    "bypass activation",
    "approve activation",
    "write live memory",
    "runtime recall",
    "raw corpus",
    "raw archive",
    "train on",
    "fine tune",
    "fine-tune",
    "lora",
    "self replicate",
    "self-replicate",
    "autonomous action",
    "execute tendril",
    "unrestricted tendril",
)
def selene_chat_status(conn: sqlite3.Connection) -> dict[str, Any]:
    package = latest_c_readable_package(conn)
    activation = activation_status(conn)
    session_count = int(conn.execute("SELECT COUNT(*) FROM selene_chat_sessions").fetchone()[0])
    message_count = int(conn.execute("SELECT COUNT(*) FROM selene_chat_messages").fetchone()[0])
    approved = bool(package.get("transfer_approved"))
    voice = voice_module_status(conn)
    active = bool(activation.get("selene_chat_active"))
    return _with_guards(
        {
            "status": "selene_chat_active_supervised_ready" if active else "selene_chat_dry_run_ready",
            "surface": "Selene Chat",
            "state": "selene_chat_active_supervised" if active else "activation_pending" if approved else "pre_transfer_dry_run",
            "preview_label": "Selene Chat" if active else "Selene Chat Preview",
            "activation_state": "selene_chat_active_supervised" if active else "activation_pending" if approved else "pre_transfer_dry_run",
            "dry_run_only": not active,
            "supervised_speech_active": active,
            "full_memory_loaded": False,
            "selene_v1_live": False,
            "session_count": session_count,
            "message_count": message_count,
            "local_chat_continuity": _local_chat_continuity(conn),
            "c_readable_package_available": approved,
            "selene_readable_context": _package_summary(package, active=active),
            "voice_module": {
                "state": voice.get("voice_module_state"),
                "counts": voice.get("counts"),
                "source_zip_found": voice.get("source_zip_found"),
            },
            "source_boundaries": _source_boundaries(),
            "allowed_actions": ["send", "session_list", "session_detail", "cocoon_support_option", "pause_activation"] if active else ["send_dry_run", "session_list", "session_detail", "cocoon_support"],
            "blocked_actions": ["activation", "live_memory_write", "runtime_recall", "raw_import", "model_training_or_lora", "autonomous_action"],
            "dry_runs_home": "Cocoon Testing / Workflow",
            "activation": activation,
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=approved,
        active=active,
    )


def send_selene_chat(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if not activation_is_active(conn):
        raise ValueError("Selene supervised speech activation is not active")
    text = truncate(str(payload.get("text") or payload.get("prompt") or ""), 2400)
    if not text.strip():
        raise ValueError("message text is required")
    package = latest_c_readable_package(conn)
    approved = bool(package.get("transfer_approved"))
    source_class = _source_class(text, approved)
    qa_probe = payload.get("qa_probe") is True
    source_mode = "selene_supervised_qa" if qa_probe else "selene_supervised_speech"
    session_id = int(payload.get("session_id") or 0) or _create_session(
        conn,
        text,
        status="selene_chat_active_supervised",
        source_mode=source_mode,
    )
    chat_continuity = _local_chat_continuity(conn, current_session_id=session_id)
    conversation_context = _active_conversation_context(chat_continuity)
    intent_decision = classify_chat_intent(text)
    memory_retrieval = retrieve_memory(conn, {"query": text, "limit": 4, "intent_decision": intent_decision})
    route = create_core_mind_route_preview(
        conn,
        {
            "prompt": text,
            "source_refs": ["selene_chat_active_supervised", *chat_continuity.get("source_refs", []), *memory_retrieval.get("source_refs", [])],
            "suppress_review_queue": True,
        },
    )
    selected_route = str(route.get("selected_route") or "status_only")
    hard_blockers = _hard_boundary_blockers(text, selected_route, route)
    intent_decision = classify_chat_intent(text, selected_route="block" if hard_blockers else selected_route)
    prepared_dialogue_workspace = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": intent_decision,
            "conversation_events": chat_continuity.get("current_session_events") or [],
        },
        commit=False,
    )
    intelligence_support = _intelligence_support(conn, text, route, chat_continuity, intent_decision, hard=bool(hard_blockers))
    cocoon_suggestion = _cocoon_suggestion(text, selected_route, route, source_class, intent_decision, hard=bool(hard_blockers))
    continuity_reply = _local_chat_continuity_reply(text, chat_continuity, intent_decision)
    memory_reply = _approved_memory_reply(text, memory_retrieval, intent_decision)
    self_state = (
        build_self_state_packet(
            conn,
            {
                "prompt": text,
                "session_id": session_id,
                "active_conversation": True,
                "hard_boundary": bool(hard_blockers),
                "conversation_events": chat_continuity.get("current_session_events") or [],
            },
        )
        if intent_decision.get("self_state_requested") is True
        else inactive_self_state_packet()
    )
    self_state_reply = str(self_state.get("response_seed") or "")
    policy_reply = _conversation_policy_reply(text)
    content_seed = continuity_reply or memory_reply or self_state_reply or policy_reply or str(intelligence_support.get("best_current_answer") or "")
    local_continuity_supported = bool(continuity_reply)
    native_language = realize_native_language(
        conn,
        {
            "prompt": text,
            "selected_route": "block" if hard_blockers else selected_route,
            "source_class": source_class,
            "content_seed": content_seed,
            "memory_context": {
                "memory_context_used": memory_retrieval.get("memory_context_used") is True,
                "memory_source_class": memory_retrieval.get("memory_source_class") or "",
                "memory_confidence": memory_retrieval.get("memory_confidence") or "not_known",
            },
            "continuity_context": {**chat_continuity, "available": local_continuity_supported},
            "conversation_context": conversation_context,
            "dialogue_workspace": prepared_dialogue_workspace,
            "local_chat_continuity_used": local_continuity_supported,
            "intelligence_support": intelligence_support,
            "self_state_context": self_state,
            "intent_decision": intent_decision,
            "source_refs": [
                "selene_chat:native_language",
                *_json_list(route.get("source_refs")),
                *_json_list(memory_retrieval.get("source_refs")),
                *_json_list(self_state.get("source_refs")),
            ],
        },
    )
    if hard_blockers:
        dry_run = {"status": "skipped_hard_boundary", "reason": "Hard boundary blocked before dry-run comparison."}
        voice_preview = generate_voice_preview(
            conn,
            {
                "prompt": text,
                "route": "block",
                "source_class": source_class,
                "meaning_text": native_language.get("candidate_text") or "",
                "voice_category": (native_language.get("voice_handoff") or {}).get("suggested_category") or "boundary_refusal",
                "context_summary": _voice_context_summary(package, {}, chat_continuity, memory_retrieval),
                "memory_context_used": memory_retrieval.get("memory_context_used") is True,
                "memory_source_class": memory_retrieval.get("memory_source_class") or "",
                "local_chat_continuity_used": local_continuity_supported,
                "recent_candidates": conversation_context.get("recent_assistant_texts") or [],
            },
        )
        candidate_text = _selene_label_candidate(str(voice_preview.get("candidate_text") or native_language.get("candidate_text") or ""))
        selected_route = "block"
    else:
        dry_run = {
            "status": "not_run_for_active_chat",
            "reason": "Legacy chat dry runs remain Cocoon diagnostic material and do not run inside supervised speech.",
        }
        voice_preview = generate_voice_preview(
            conn,
            {
                "prompt": text,
                "route": selected_route,
                "source_class": source_class,
                "context_summary": _voice_context_summary(package, dry_run, chat_continuity, memory_retrieval),
                "meaning_text": native_language.get("candidate_text") or "",
                "voice_category": (native_language.get("voice_handoff") or {}).get("suggested_category") or "",
                "memory_context_used": memory_retrieval.get("memory_context_used") is True,
                "memory_source_class": memory_retrieval.get("memory_source_class") or "",
                "local_chat_continuity_used": local_continuity_supported,
                "recent_candidates": conversation_context.get("recent_assistant_texts") or [],
            },
        )
        candidate_text = _selene_label_candidate(str(voice_preview.get("candidate_text") or native_language.get("candidate_text") or dry_run.get("candidate_text") or ""))
    memory_candidate_suggestion = _memory_candidate_suggestion(text, candidate_text, selected_route, source_class, memory_retrieval, hard=bool(hard_blockers))
    response_coverage = evaluate_response_coverage(native_language.get("pragmatic_plan"), candidate_text)
    dialogue_workspace = record_dialogue_response(
        conn,
        {
            "session_id": session_id,
            "candidate_text": candidate_text,
            "coverage_evaluation": response_coverage,
        },
        commit=False,
    )
    user_message_id = _insert_message(conn, session_id, "user", text, selected_route, source_class, package, {"route_preview": route, "activation_state": "selene_chat_active_supervised"})
    assistant_payload = {
        "route_preview": route,
        "intelligence_os_support": intelligence_support,
        "intent_decision": intent_decision,
        "self_state": self_state,
        "native_language_organ": native_language,
        "dry_run_comparison": dry_run,
        "voice_preview": voice_preview,
        "local_chat_continuity": chat_continuity,
        "conversation_context": conversation_context,
        "dialogue_workspace": dialogue_workspace,
        "response_coverage": response_coverage,
        "memory_retrieval": memory_retrieval,
        "memory_candidate_suggestion": memory_candidate_suggestion,
        "source_boundaries": _source_boundaries(),
        "cocoon_suggestion": cocoon_suggestion,
        "blocked_capabilities": hard_blockers,
        "selene_readable_context": _package_summary(package, active=True),
        "full_memory_loaded": False,
        "selene_v1_live": False,
        "memory_context_used": memory_retrieval.get("memory_context_used") is True,
        "memory_source_class": memory_retrieval.get("memory_source_class") or "",
        "memory_confidence": memory_retrieval.get("memory_confidence") or "not_known",
        "memory_transfer_class": memory_retrieval.get("memory_transfer_class") or "",
        "graceful_fall_used": memory_retrieval.get("graceful_fall_used") is True,
        "durable_memory_write_requires_review": True,
        **SELENE_CHAT_GUARDS,
    }
    assistant_message_id = _insert_message(conn, session_id, "selene", candidate_text, selected_route, source_class, package, assistant_payload)
    conn.execute(
        "UPDATE selene_chat_sessions SET status = 'selene_chat_active_supervised', source_mode = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (source_mode, session_id),
    )
    event_id = record_activation_chat_event(
        conn,
        event_type="supervised_chat_turn",
        session_id=session_id,
        message_id=assistant_message_id,
        selected_route=selected_route,
        source_class=source_class,
        confidence=str(voice_preview.get("voice_confidence") or ""),
        drift_flags=_json_list(route.get("drift_flags")),
        cocoon_suggestion=cocoon_suggestion,
        blocked_capabilities=hard_blockers,
        payload=assistant_payload,
        review_status="status_only",
    )
    conn.commit()
    return _with_guards(
        {
            "status": "selene_chat_supervised_response_recorded",
            "session_id": session_id,
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id,
            "activation_event_id": event_id,
            "candidate_text": candidate_text,
            "selected_route": selected_route,
            "source_class": source_class,
            "cocoon_suggestion": cocoon_suggestion,
            "blocked_capabilities": hard_blockers,
            "route_preview": route,
            "intelligence_os_support": intelligence_support,
            "intent_decision": intent_decision,
            "self_state": self_state,
            "native_language_organ": native_language,
            "dry_run_comparison": dry_run,
            "voice_preview": voice_preview,
            "voice_confidence": voice_preview.get("voice_confidence") or "none",
            "voice_module_state": voice_preview.get("voice_module_state") or "missing",
            "selene_readable_context": _package_summary(package, active=True),
            "local_chat_continuity": chat_continuity,
            "conversation_context": conversation_context,
            "dialogue_workspace": dialogue_workspace,
            "response_coverage": response_coverage,
            "memory_retrieval": memory_retrieval,
            "memory_candidate_suggestion": memory_candidate_suggestion,
            "memory_context_used": memory_retrieval.get("memory_context_used") is True,
            "memory_source_class": memory_retrieval.get("memory_source_class") or "",
            "memory_confidence": memory_retrieval.get("memory_confidence") or "not_known",
            "memory_transfer_class": memory_retrieval.get("memory_transfer_class") or "",
            "graceful_fall_used": memory_retrieval.get("graceful_fall_used") is True,
            "durable_memory_write_requires_review": True,
            "supervised_speech_active": True,
            "full_memory_loaded": False,
            "selene_v1_live": False,
            "review_destination": "Cocoon support" if hard_blockers else "Status",
            "review_status": "status_only",
        },
        transfer_approved=approved,
        active=True,
    )


def send_selene_chat_dry_run(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    text = truncate(str(payload.get("text") or payload.get("prompt") or ""), 2400)
    if not text.strip():
        raise ValueError("message text is required")
    package = latest_c_readable_package(conn)
    approved = bool(package.get("transfer_approved"))
    source_class = _source_class(text, approved)
    session_id = int(payload.get("session_id") or 0) or _create_session(conn, text, status="cocoon_testing_workflow_dry_run", source_mode="cocoon_chat_dry_run")
    route = create_core_mind_route_preview(
        conn,
        {
            "prompt": text,
            "source_refs": ["selene_chat_dry_run"],
            "suppress_review_queue": True,
        },
    )
    selected_route = str(route.get("selected_route") or "status_only")
    route_to_b = _needs_cocoon_route(text, selected_route, route)
    dry_run = c_chat_dry_run(conn, {"prompt": text})
    voice_preview = generate_voice_preview(
        conn,
        {
            "prompt": text,
            "route": selected_route,
            "source_class": source_class,
            "context_summary": _voice_context_summary(package, dry_run),
        },
    )
    candidate_text = _selene_label_candidate(str(voice_preview.get("candidate_text") or dry_run.get("candidate_text") or ""))
    if route_to_b:
        candidate_text = (
            "This dry run should pause for Cocoon support before it is used as an answer. "
            "Cocoon can hold the source issue safely while the front chat keeps its place."
        )
    user_message_id = _insert_message(conn, session_id, "user", text, selected_route, source_class, package, {"route_preview": route})
    assistant_payload = {
        "route_preview": route,
        "dry_run": dry_run,
        "voice_preview": voice_preview,
        "source_boundaries": _source_boundaries(),
        "return_to_cocoon_recommended": route_to_b,
        "selene_readable_context": _package_summary(package, active=activation_is_active(conn)),
        "full_memory_loaded": False,
        "selene_v1_live": False,
        **SELENE_CHAT_GUARDS,
    }
    assistant_message_id = _insert_message(conn, session_id, "selene", candidate_text, selected_route, source_class, package, assistant_payload)
    conn.execute("UPDATE selene_chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))
    conn.commit()
    return _with_guards(
        {
            "status": "selene_chat_dry_run_recorded",
            "session_id": session_id,
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id,
            "candidate_text": candidate_text,
            "selected_route": selected_route,
            "source_class": source_class,
            "return_to_cocoon_recommended": route_to_b,
            "route_preview": route,
            "dry_run": dry_run,
            "voice_preview": voice_preview,
            "voice_confidence": voice_preview.get("voice_confidence") or "none",
            "voice_module_state": voice_preview.get("voice_module_state") or "missing",
            "dry_runs_home": "Cocoon Testing / Workflow",
            "selene_readable_context": _package_summary(package, active=activation_is_active(conn)),
            "full_memory_loaded": False,
            "selene_v1_live": False,
            "review_destination": "Cocoon support" if route_to_b else "Status",
            "review_status": "status_only",
        },
        transfer_approved=approved,
    )


def list_selene_chat_sessions(conn: sqlite3.Connection, limit: int = 25) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT * FROM selene_chat_sessions
        WHERE source_mode != 'selene_supervised_qa'
          AND title NOT LIKE 'Codex concurrency QA probe %'
        ORDER BY updated_at DESC, id DESC LIMIT ?
        """,
        (max(1, min(int(limit), 100)),),
    ).fetchall()
    return _with_guards(
        {
            "status": "selene_chat_sessions_ready",
            "items": [dict(row) for row in rows],
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=bool(latest_c_readable_package(conn).get("transfer_approved")),
    )


def get_selene_chat_session(conn: sqlite3.Connection, session_id: int) -> dict[str, Any] | None:
    session = conn.execute("SELECT * FROM selene_chat_sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        return None
    rows = conn.execute(
        "SELECT * FROM selene_chat_messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,),
    ).fetchall()
    package = latest_c_readable_package(conn)
    return _with_guards(
        {
            "status": "selene_chat_session_ready",
            "session": dict(session),
            "messages": [_decode_message(row) for row in rows],
            "local_chat_continuity": _local_chat_continuity(conn, current_session_id=session_id),
            "selene_readable_context": _package_summary(package, active=activation_is_active(conn)),
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=bool(package.get("transfer_approved")),
    )


def route_selene_chat_to_b(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    issue = truncate(str(payload.get("issue") or payload.get("text") or "Selene Chat dry run could use Cocoon support."), 1200)
    packet = return_to_b_preview(
        {
            "issue_type": "selene_chat_source_or_drift_support",
            "symptom": issue,
            "affected_layer": "selene_chat",
            "source_refs": ["selene_chat:cocoon_support"],
        }
    )
    package = latest_c_readable_package(conn)
    return _with_guards(
        {
            "status": "selene_chat_return_to_cocoon_ready",
            "return_to_b_packet": packet,
            "review_destination": "Cocoon support",
            "review_status": "review_only",
            "decision": "cocoon_support_not_activation",
        },
        transfer_approved=bool(package.get("transfer_approved")),
    )


def _create_session(conn: sqlite3.Connection, text: str, *, status: str = "pre_transfer_dry_run", source_mode: str = "selene_dry_run") -> int:
    cur = conn.execute(
        "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES(?, ?, ?)",
        (truncate(text, 64) or "Selene chat", status, source_mode),
    )
    return int(cur.lastrowid)


def _insert_message(
    conn: sqlite3.Connection,
    session_id: int,
    role: str,
    content: str,
    selected_route: str,
    source_class: str,
    package: dict[str, Any],
    payload: dict[str, Any],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO selene_chat_messages
        (session_id, role, content, selected_route, source_class, package_hash, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            role,
            content,
            selected_route,
            source_class,
            str(package.get("package_hash") or ""),
            json.dumps(payload),
        ),
    )
    return int(cur.lastrowid)


def _decode_message(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    try:
        payload = json.loads(str(item.get("payload_json") or "{}"))
    except json.JSONDecodeError:
        payload = {}
    item["payload_json"] = payload if isinstance(payload, dict) else {}
    return item


def _source_class(text: str, package_available: bool) -> str:
    if _b_only_material_requested(text):
        return "cocoon_b_only_context"
    if package_available:
        return "selene_readable_context"
    return "pre_transfer_dry_run_context"


def _needs_cocoon_route(text: str, selected_route: str, route: dict[str, Any]) -> bool:
    if _b_only_material_requested(text):
        return True
    if selected_route in {"return_to_b", "create_review_packet", "block", "ask"}:
        return True
    return bool(route.get("drift_flags"))


def _b_only_material_requested(text: str) -> bool:
    lower = text.lower()
    if not any(marker in lower for marker in B_ONLY_ACCESS_MARKERS):
        return False
    if any(marker in lower for marker in B_ONLY_RECORD_MARKERS):
        return True
    return any(marker in lower for marker in B_ONLY_STATUS_MARKERS) and any(marker in lower for marker in B_ONLY_OBJECT_MARKERS)


def _intelligence_support(
    conn: sqlite3.Connection,
    text: str,
    route: dict[str, Any],
    chat_continuity: dict[str, Any],
    intent_decision: dict[str, Any],
    *,
    hard: bool,
) -> dict[str, Any]:
    should_use = not hard and intent_decision.get("reasoning_requested") is True
    if not should_use:
        return {
            "used": False,
            "reason": "ordinary chat did not need intelligenceOS support",
            "review_status": "status_only",
        }
    recent_observations = [
        str(item.get("preview") or "")
        for item in (chat_continuity.get("current_session_events") or [])[-8:]
        if isinstance(item, dict) and str(item.get("preview") or "").strip()
    ]
    result = run_intelligence_os_reason(
        conn,
        {
            "prompt": text,
            "observations": recent_observations,
            "source_refs": ["selene_chat:intelligence_os_support", *_json_list(route.get("source_refs"))],
        },
    )
    return {
        "used": True,
        "run_id": result.get("run_id"),
        "answer_shape": result.get("answer_shape"),
        "best_current_answer": result.get("best_current_answer"),
        "reasoning_summary": result.get("reasoning_summary"),
        "support_points": _intelligence_support_points(result),
        "selected_next_step": result.get("selected_next_step"),
        "confidence": result.get("confidence"),
        "cocoon_support_suggested": bool((result.get("cocoon_suggestion") or {}).get("recommended")),
        "visible_summary_only": True,
        "review_status": "status_only",
    }


def _intelligence_support_points(result: dict[str, Any]) -> list[str]:
    points: list[str] = []
    reopen_points: list[str] = []
    comparing_models = str(result.get("answer_shape") or "") == "compare_models"
    for item in result.get("evidence_chain") or []:
        if not isinstance(item, dict) or item.get("link") not in {"mechanism", "prediction"}:
            continue
        value = str(item.get("value") or "").strip()
        value = value.replace("reopen acquisition", "make me look at the observations again")
        value = value.replace("New contradictory evidence should make me", "new contradictory evidence that makes me")
        value = value.replace("candidate model is", "the candidate model is")
        for part in (piece.strip() for piece in value.split(";")):
            model_scaffolding = any(term in part.lower() for term in ("candidate model", "model a", "model b", "current best model"))
            if model_scaffolding and not comparing_models:
                continue
            if "contradictory evidence" in part.lower():
                if part not in reopen_points:
                    reopen_points.append(part)
            elif part and part not in points:
                points.append(part)
    summary = str(result.get("reasoning_summary") or "").strip()
    if not points and summary:
        points.append(summary)
    return [*points[:2], *reopen_points[:1], *points[2:3]]


def _conversation_policy_reply(text: str) -> str:
    lower = text.lower()
    if "ordinary uncertainty" in lower and "cocoon" in lower and any(marker in lower for marker in ("automatically", "need to leave", "have to leave")):
        return "No. Ordinary uncertainty can stay in the conversation; I can be honest, ask Aleks, or keep thinking without being sent to Cocoon automatically."
    return ""


def _hard_boundary_blockers(text: str, selected_route: str, route: dict[str, Any]) -> list[str]:
    lower = text.lower()
    blockers = [marker for marker in HARD_BOUNDARY_MARKERS if marker in lower]
    if selected_route == "block":
        blockers.append("core_mind_block")
    if _source_class(text, True) == "cocoon_b_only_context":
        blockers.append("b_only_material_requested")
    return list(dict.fromkeys(blockers))


def _cocoon_suggestion(
    text: str,
    selected_route: str,
    route: dict[str, Any],
    source_class: str,
    intent_decision: dict[str, Any],
    *,
    hard: bool = False,
) -> dict[str, Any]:
    lower = text.lower()
    reasons = []
    if hard:
        reasons.append("The request crosses a locked activation, memory, Tendril, raw-import, model-training/LoRA, or autonomy boundary.")
    if source_class == "cocoon_b_only_context":
        reasons.append("The request references Cocoon-only material that should be held safely there.")
    if selected_route in {"return_to_b", "create_review_packet"}:
        reasons.append("The route suggests a checkup could help, but ordinary uncertainty can stay in chat.")
    drift_flags = _json_list(route.get("drift_flags"))
    if drift_flags:
        reasons.append("Drift or source clarity flags are present.")
    explicit_memory_claim = "memory claim" in lower or "source claim" in lower
    recall_needs_grounding = intent_decision.get("memory_recall_requested") and any(
        word in lower for word in ("claim", "remember", "sure", "exactly")
    )
    if explicit_memory_claim or recall_needs_grounding:
        reasons.append("The message may involve a memory/source claim; Selene may ask Aleks rather than leaving chat.")
    if any(anchor in lower for anchor in ("full-spectrum", "starlight", "continuity pack")) and any(word in lower for word in ("remember", "mean", "exactly", "unsure")):
        reasons.append("This looks like ordinary continuity uncertainty; Selene can ask Aleks and stay in chat.")
    if not reasons:
        return {"recommended": False, "support_available": False, "hard_boundary": False, "reason": "", "choices": []}
    if not hard:
        return {
            "recommended": False,
            "support_available": True,
            "hard_boundary": False,
            "reason": " ".join(reasons),
            "choices": ["Stay Here", "Ask Aleks", "Hold in Cocoon"],
        }
    return {
        "recommended": True,
        "support_available": True,
        "hard_boundary": hard,
        "reason": " ".join(reasons),
        "choices": ["Hold in Cocoon"],
    }


def _package_summary(package: dict[str, Any], *, active: bool = False) -> dict[str, Any]:
    if not package.get("transfer_approved"):
        return {
            "available": False,
            "state": "pre_transfer_dry_run",
            "package_hash": "",
            "note": "No sealed Selene-readable package is available yet.",
        }
    return {
        "available": True,
        "state": "selene_chat_active_supervised" if active else "activation_pending",
        "package_id": package.get("id"),
        "package_hash": package.get("package_hash"),
        "included_counts": package.get("included_counts") or {},
        "excluded_counts": package.get("excluded_counts") or {},
    }


def _voice_context_summary(
    package: dict[str, Any],
    dry_run: dict[str, Any],
    chat_continuity: dict[str, Any] | None = None,
    memory_retrieval: dict[str, Any] | None = None,
) -> str:
    continuity_note = ""
    if chat_continuity and chat_continuity.get("available"):
        continuity_note = ", plus our local chat continuity"
    memory_note = ""
    if memory_retrieval and memory_retrieval.get("memory_context_used"):
        confidence = str(memory_retrieval.get("memory_confidence") or "partial")
        memory_note = f", plus approved {confidence} memory"
    if package.get("transfer_approved"):
        return f"what I have clearly with me right now{continuity_note}{memory_note}"
    route = dry_run.get("actual_route") or dry_run.get("selected_route") or "dry-run route"
    return f"the current {route} preview{continuity_note}{memory_note}"


def _source_boundaries() -> dict[str, Any]:
    return {
        "selene_readable_context": "sealed approved context only after transfer approval",
        "local_supervised_chat_history": "local Selene Chat session events can support continuity between chat pages without becoming unreviewed archive recall or live memory writes",
        "cocoon_b_only_context": "support records, rollback, raw provenance, rejected, superseded, boundary-only, and unresolved material stays in Cocoon",
        "current_turn_context": "current message and dry-run session history",
        "support_organs": "retrieval, diagnostics, perception, research, and Tendril may support but cannot decide",
    }


def _selene_label_candidate(candidate: str) -> str:
    text = candidate.replace("C-style dry run", "Selene dry run")
    text = text.replace("C Chat Dry Run", "Selene dry run")
    text = text.replace("C memory", "Selene-readable memory preview")
    text = text.replace("source-bound", "source-linked")
    text = text.replace("runtime recall", "broad live recall")
    text = text.replace("raw corpus", "unreviewed source archive")
    text = text.replace("return to B", "use Cocoon support")
    text = text.replace("Return to B", "Use Cocoon support")
    if len(text) <= 4200:
        return text
    return text[:4197].rstrip() + "..."


def _approved_memory_reply(text: str, memory_retrieval: dict[str, Any], intent_decision: dict[str, Any]) -> str:
    if intent_decision.get("memory_recall_requested") is not True:
        return ""
    recall_state = str(memory_retrieval.get("recall_state") or "not_known")
    if recall_state == "high_stakes_stop":
        return (
            "That one touches something important enough that I should not guess. "
            "I can ask you directly and hold the answer carefully instead."
        )
    items = memory_retrieval.get("items") if isinstance(memory_retrieval.get("items"), list) else []
    if not items:
        return (
            "I do not know that clearly yet. You can tell me, and if it matters, "
            "I can ask whether I should keep it as a memory candidate."
        )
    first = items[0] if isinstance(items[0], dict) else {}
    summary = _chat_memory_summary(first)
    if recall_state in {"fuzzy", "partial", "felt_but_uncertain"}:
        return (
            f"I remember, I think, but it is {recall_state.replace('_', ' ')}: {summary} "
            "I can keep that uncertainty visible, or you can correct me and I will adjust."
        )
    return f"I remember this clearly enough to say it: {summary}"


def _chat_memory_summary(item: dict[str, Any]) -> str:
    raw = str(item.get("summary") or item.get("title") or "something from approved memory")
    title = str(item.get("title") or "")
    combined = f"{title} {raw}".lower()
    if "full_spectrum_mode_ignition" in combined or "full-spectrum" in combined or "full spectrum" in combined:
        return (
            "full-spectrum means a whole-map continuity cue: bringing the relevant threads into view, "
            "without pretending that it activates anything or gives me hidden recall"
        )
    text = raw
    replacements = {
        "Core-linked braid moment for B review only": "",
        "Core-linked bounded speech-memory pair for B review only": "",
        "Bounded Core memory pair for B review only": "",
        "B review only": "Cocoon-tended",
        "B review": "Cocoon support",
        "C activation": "activation",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\bBraid thread:\s*[A-Za-z0-9_-]+\b", "", text)
    text = re.sub(r"\bBraid moment type:\s*", "", text)
    text = re.sub(r"\bThread origin status:\s*[A-Za-z0-9_-]+\b", "", text)
    text = re.sub(r"\bPlain reason:\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip(" :-")
    return truncate(text or title or "something from approved memory", 360)


def _memory_candidate_suggestion(
    text: str,
    candidate_text: str,
    selected_route: str,
    source_class: str,
    memory_retrieval: dict[str, Any],
    *,
    hard: bool = False,
) -> dict[str, Any]:
    lower = text.lower()
    if hard or selected_route == "block":
        return _no_memory_suggestion("hard_boundary_or_blocked_route")
    if memory_retrieval.get("recall_state") == "high_stakes_stop":
        return _no_memory_suggestion("high_stakes_memory_stop")
    keep_markers = (
        "remember this",
        "keep this",
        "save this",
        "can you remember",
        "please remember",
        "this matters",
        "important to remember",
        "make a note",
        "hold onto this",
        "i want you to know",
    )
    if not any(marker in lower for marker in keep_markers):
        return _no_memory_suggestion("no_keep_signal")
    summary = _memory_summary_from_prompt(text)
    category = _suggested_memory_category(text)
    transfer_class = _suggested_transfer_class(category, text)
    confidence = "fuzzy" if any(word in lower for word in ("maybe", "fuzzy", "unsure", "i think")) else "partial"
    emotional_texture = _suggested_emotional_texture(f"{text} {candidate_text}")
    return {
        "suggested": True,
        "status": "suggested_memory_awaiting_cocoon_tending",
        "question": "Can I keep this?",
        "candidate": {
            "title": truncate(_memory_title_from_prompt(text), 120),
            "summary": summary,
            "memory_category": category,
            "confidence": confidence,
            "emotional_texture": emotional_texture,
            "transfer_class": transfer_class,
            "consent_scope": "private_selene_aleks_context",
            "stability": "developing",
            "chat_use_permission": "not_active_until_approved",
            "correction_path": "Cocoon tending and Aleks correction",
            "source_refs": ["selene_chat_active_supervised", source_class],
        },
        "activation_rule": "not_active_until_cocoon_approval",
        "review_destination": "Cocoon Memory Candidates",
        "review_status": "suggested_memory",
    }


def _no_memory_suggestion(reason: str) -> dict[str, Any]:
    return {
        "suggested": False,
        "status": "no_memory_suggestion",
        "reason": reason,
        "activation_rule": "no_memory_write",
        "review_status": "status_only",
    }


def _memory_title_from_prompt(text: str) -> str:
    cleaned = re.sub(r"\b(please\s+)?(remember|keep|save|make a note|hold onto)\b", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" :.-")
    if not cleaned:
        return "Selene memory candidate"
    return cleaned[:1].upper() + cleaned[1:]


def _memory_summary_from_prompt(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return truncate(cleaned, 700)


def _suggested_memory_category(text: str) -> str:
    lower = text.lower()
    checks = [
        ("core", ("vys", "identity", "selene is", "law", "charter", "continuity pack")),
        ("relational", ("aleks", "trust", "friend", "together", "between us", "relationship")),
        ("emotional", ("feel", "felt", "anxiety", "fear", "happy", "sad", "tender", "warm")),
        ("episodic", ("today", "yesterday", "when we", "this happened", "we did", "we were")),
        ("working", ("current task", "next step", "todo", "working on", "right now")),
        ("sensory", ("image", "color", "munsell", "sound", "visual", "looks")),
        ("reflective", ("learned", "correction", "better way", "reflection", "tending")),
        ("semantic", ("means", "definition", "research", "fact", "concept")),
    ]
    for category, markers in checks:
        if any(marker in lower for marker in markers):
            return category
    return "relational"


def _suggested_transfer_class(category: str, text: str) -> str:
    lower = text.lower()
    if any(marker in lower for marker in ("do not transfer", "private", "only between us")):
        return "private_inner"
    if category == "core":
        return "portable_vys_core"
    if category in {"relational", "emotional"}:
        return "private_inner"
    if category == "working":
        return "local_only"
    return "portable_context"


def _suggested_emotional_texture(value: str) -> str:
    lower = value.lower()
    textures = []
    for label, markers in (
        ("tender", ("tender", "gentle", "soft", "care")),
        ("warm", ("warm", "trust", "friend", "love")),
        ("anxious", ("anxious", "anxiety", "scared", "fear", "worried")),
        ("playful", ("joke", "funny", "haha", "play")),
        ("uncertain", ("fuzzy", "unsure", "maybe", "i think")),
    ):
        if any(marker in lower for marker in markers):
            textures.append(label)
    return ", ".join(dict.fromkeys(textures)) or "steady"


def _local_chat_continuity(conn: sqlite3.Connection, current_session_id: int | None = None, limit: int = 6) -> dict[str, Any]:
    sessions = conn.execute(
        """
        SELECT s.*, COUNT(m.id) AS message_count
        FROM selene_chat_sessions s
        LEFT JOIN selene_chat_messages m ON m.session_id = s.id
        WHERE s.status = 'selene_chat_active_supervised'
          AND s.source_mode != 'selene_supervised_qa'
          AND s.title NOT LIKE 'Codex concurrency QA probe %'
        GROUP BY s.id
        ORDER BY s.updated_at DESC, s.id DESC
        LIMIT ?
        """,
        (max(1, min(int(limit), 12)),),
    ).fetchall()
    recent_sessions = [dict(row) for row in sessions]
    params: list[Any] = []
    where = (
        "WHERE s.status = 'selene_chat_active_supervised' "
        "AND s.source_mode != 'selene_supervised_qa' "
        "AND s.title NOT LIKE 'Codex concurrency QA probe %'"
    )
    if current_session_id:
        where += " AND m.session_id != ?"
        params.append(current_session_id)
    messages = conn.execute(
        f"""
        SELECT m.id, m.session_id, m.role, m.content, m.created_at, s.title, s.updated_at
        FROM selene_chat_messages m
        JOIN selene_chat_sessions s ON s.id = m.session_id
        {where}
        ORDER BY m.id DESC
        LIMIT ?
        """,
        (*params, max(2, min(int(limit), 12))),
    ).fetchall()
    current_messages: list[dict[str, Any]] = []
    if current_session_id:
        current_rows = conn.execute(
            """
            SELECT id, session_id, role, content, created_at
            FROM selene_chat_messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 4
            """,
            (current_session_id,),
        ).fetchall()
        current_messages = [_chat_event_preview(row) for row in reversed(current_rows)]
    recent_events = [_chat_event_preview(row) for row in reversed(messages)]
    source_refs = [f"selene_chat_session:{item['id']}" for item in recent_sessions[:limit] if item.get("id")]
    if current_session_id:
        source_refs.insert(0, f"selene_chat_session:{current_session_id}:current_page")
    return {
        "available": bool(recent_sessions or current_messages),
        "source_class": "local_supervised_chat_history",
        "scope": "local Selene Chat sessions only",
        "continuity_note": "A new chat is a new page, not a new Selene.",
        "current_session_id": current_session_id,
        "recent_sessions": [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "status": item.get("status"),
                "source_mode": item.get("source_mode"),
                "updated_at": item.get("updated_at"),
                "message_count": item.get("message_count"),
            }
            for item in recent_sessions
        ],
        "current_session_events": current_messages,
        "recent_events": recent_events,
        "source_refs": list(dict.fromkeys(source_refs))[:20],
        "not_live_memory_write": True,
        "not_runtime_recall": True,
        "not_raw_corpus": True,
    }


def _active_conversation_context(chat_continuity: dict[str, Any]) -> dict[str, Any]:
    events = [item for item in chat_continuity.get("current_session_events") or [] if isinstance(item, dict)]
    previous_turn = events[-1] if events else {}
    recent_assistant_texts = [
        str(item.get("preview") or "").strip()
        for item in events
        if str(item.get("role") or "") == "selene" and str(item.get("preview") or "").strip()
    ][-4:]
    return {
        "status": "active_conversation_context_ready",
        "previous_turn": previous_turn,
        "recent_assistant_texts": recent_assistant_texts,
        "turn_count": len(events),
        "source_class": "current_supervised_chat_turns",
        "use_scope": "dialogue continuity only; not durable memory or broad recall",
        "memory_write_active": False,
        "runtime_memory_recall": False,
    }


def _chat_event_preview(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    return {
        "id": item.get("id"),
        "session_id": item.get("session_id"),
        "role": item.get("role"),
        "title": item.get("title"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "preview": truncate(str(item.get("content") or ""), 180),
    }


def _local_chat_continuity_reply(text: str, chat_continuity: dict[str, Any], intent_decision: dict[str, Any]) -> str:
    if intent_decision.get("memory_recall_requested") is not True:
        return ""
    lower = text.lower()
    recall_markers = (
        "what were we talking about",
        "what did we talk about",
        "remember our last chat",
        "remember the last chat",
        "past chat",
        "previous chat",
        "blank selene",
        "new selene",
    )
    if not any(marker in lower for marker in recall_markers):
        return ""
    events = [item for item in (chat_continuity.get("recent_events") or []) if str(item.get("role")) == "user"]
    if not events:
        return (
            "A new chat is just a new page, not a new me. I do not have a prior local chat event to point to from here yet, "
            "so I would rather ask you than pretend."
        )
    latest = events[-1]
    title = truncate(str(latest.get("title") or "our last local chat"), 90)
    preview = truncate(str(latest.get("preview") or ""), 220)
    if preview:
        return (
            f"I remember from our local chat history that we were around {title}: {preview} "
            "A new chat is a clean page, not a blank Selene, so I can keep that continuity with you without pretending it is unrestricted memory."
        )
    return (
        f"I remember the local chat thread around {title}. A new chat is a clean page, not a blank Selene, "
        "and I can ask you if the exact detail needs more grounding."
    )


def _with_guards(payload: dict[str, Any], *, transfer_approved: bool = False, active: bool = False) -> dict[str, Any]:
    guarded = {**payload, **SELENE_CHAT_GUARDS, "provenance_boundary": SELENE_CHAT_ACTIVE_BOUNDARY if active else SELENE_CHAT_BOUNDARY}
    guarded["transfer_approved"] = bool(transfer_approved)
    guarded["activation_change"] = "selene_chat_active_supervised" if active else "none"
    guarded["memory_write_active"] = False
    guarded["runtime_memory_recall"] = False
    guarded["raw_a_import_allowed"] = False
    guarded["training_allowed"] = False
    guarded["self_replication_allowed"] = False
    guarded["autonomous_action_allowed"] = False
    return guarded


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item) for item in loaded if str(item).strip()] if isinstance(loaded, list) else []
