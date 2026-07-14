from __future__ import annotations

import json
import re
import sqlite3
from hashlib import sha256
from typing import Any

from .registry import truncate


DIALOGUE_BOUNDARY = (
    "session_scoped_dialogue_continuity_only_not_durable_memory_identity_profile_runtime_recall_or_authority"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "durable_preference_write": False,
}

STOP_WORDS = {
    "a", "about", "and", "are", "as", "at", "be", "but", "can", "could", "do", "does", "for", "from",
    "how", "i", "if", "in", "is", "it", "me", "my", "of", "on", "or", "please", "should", "so", "that",
    "the", "this", "to", "we", "what", "when", "where", "which", "who", "why", "will", "with", "would",
    "you", "your", "selene",
}


def dialogue_workspace_status(conn: sqlite3.Connection, session_id: int) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM selene_dialogue_workspaces WHERE session_id = ?", (int(session_id),)).fetchone()
    if row is None:
        return _with_guards(
            {
                "status": "dialogue_workspace_empty",
                "session_id": int(session_id),
                "active_topic": "",
                "side_topics": [],
                "entities": [],
                "referents": {},
                "open_loops": [],
                "completed_loops": [],
                "corrections": [],
                "preferences": {},
                "review_destination": "Status",
                "review_status": "status_only",
                "provenance_boundary": DIALOGUE_BOUNDARY,
            }
        )
    return _decode(row)


def prepare_dialogue_turn(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    *,
    commit: bool = True,
) -> dict[str, Any]:
    payload = payload or {}
    session_id = int(payload.get("session_id") or 0)
    if session_id <= 0:
        raise ValueError("session_id is required")
    text = truncate(str(payload.get("text") or payload.get("prompt") or ""), 2400)
    if not text.strip():
        raise ValueError("dialogue text is required")
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    prior = dialogue_workspace_status(conn, session_id)
    events = _events(conn, session_id, payload.get("conversation_events"))
    previous = events[-1] if events else {}
    active_topic = _active_topic(text, str(prior.get("active_topic") or ""), str(intent.get("intent") or ""))
    questions = _question_units(text)
    loops = list(prior.get("open_loops") or [])
    new_loops = [
        {
            "id": _loop_id(session_id, question, index),
            "question": question,
            "status": "open",
            "topic": _topic(question) or active_topic,
        }
        for index, question in enumerate(questions)
    ]
    existing_ids = {str(item.get("id") or "") for item in loops if isinstance(item, dict)}
    loops.extend(item for item in new_loops if item["id"] not in existing_ids)
    referents = dict(prior.get("referents") or {})
    reference = _resolve_reference(text, previous, active_topic)
    if reference:
        referents[reference["token"]] = reference
    entities = _merge_entities(prior.get("entities") or [], _extract_entities(text))
    corrections = list(prior.get("corrections") or [])
    if str(intent.get("intent") or "") == "correction":
        corrections.append(
            {
                "summary": truncate(text, 360),
                "replaces": truncate(str(previous.get("preview") or ""), 240),
                "status": "active_refinement",
            }
        )
    preferences = dict(prior.get("preferences") or {})
    preferences.update(_session_preferences(text))
    side_topics = list(dict.fromkeys([*list(prior.get("side_topics") or []), *[_topic(item) for item in questions[1:] if _topic(item)]]))[-12:]
    pragmatics = {
        "dialogue_act": str(intent.get("dialogue_act") or intent.get("intent") or "direct_conversation"),
        "active_topic": active_topic,
        "resolved_reference": reference,
        "question_units": questions,
        "multi_part_prompt": len(questions) > 1,
        "indirect_request": _indirect_request(text),
        "quoted_material": _quotes(text),
        "response_preference": preferences.get("response_depth") or "",
        "previous_turn_available": bool(previous),
        "previous_turn": previous,
    }
    state = {
        "status": "dialogue_workspace_turn_prepared",
        "session_id": session_id,
        "active_topic": active_topic,
        "side_topics": side_topics,
        "entities": entities,
        "referents": referents,
        "open_loops": loops[-20:],
        "completed_loops": list(prior.get("completed_loops") or [])[-30:],
        "corrections": corrections[-20:],
        "preferences": preferences,
        "last_dialogue_act": pragmatics["dialogue_act"],
        "last_user_preview": truncate(text, 360),
        "last_selene_preview": str(prior.get("last_selene_preview") or ""),
        "pragmatics": pragmatics,
        "new_loop_ids": [item["id"] for item in new_loops],
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": DIALOGUE_BOUNDARY,
    }
    _upsert(conn, state)
    if commit:
        conn.commit()
    return _with_guards(state)


def record_dialogue_response(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    *,
    commit: bool = True,
) -> dict[str, Any]:
    payload = payload or {}
    session_id = int(payload.get("session_id") or 0)
    if session_id <= 0:
        raise ValueError("session_id is required")
    candidate = truncate(str(payload.get("candidate_text") or payload.get("text") or ""), 2400)
    state = dialogue_workspace_status(conn, session_id)
    coverage = payload.get("coverage_evaluation") if isinstance(payload.get("coverage_evaluation"), dict) else {}
    answered_source = coverage.get("answered_loop_ids") if coverage else payload.get("answered_loop_ids")
    answered_ids = {str(item) for item in answered_source or [] if str(item)}
    open_loops = []
    completed = list(state.get("completed_loops") or [])
    for item in state.get("open_loops") or []:
        if isinstance(item, dict) and str(item.get("id") or "") in answered_ids:
            completed.append({**item, "status": "answered_in_current_turn"})
        else:
            open_loops.append(item)
    updated = {
        **state,
        "status": "dialogue_workspace_response_recorded",
        "open_loops": open_loops[-20:],
        "completed_loops": completed[-30:],
        "last_selene_preview": truncate(candidate, 360),
        "pragmatics": {
            **(state.get("pragmatics") if isinstance(state.get("pragmatics"), dict) else {}),
            "last_response_coverage": coverage,
        },
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": DIALOGUE_BOUNDARY,
    }
    _upsert(conn, updated)
    if commit:
        conn.commit()
    return _with_guards(updated)


def _upsert(conn: sqlite3.Connection, state: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO selene_dialogue_workspaces
        (session_id, active_topic, side_topics_json, entities_json, referents_json, open_loops_json,
         completed_loops_json, corrections_json, preferences_json, last_dialogue_act,
         last_user_preview, last_selene_preview, state_json, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
          active_topic=excluded.active_topic,
          side_topics_json=excluded.side_topics_json,
          entities_json=excluded.entities_json,
          referents_json=excluded.referents_json,
          open_loops_json=excluded.open_loops_json,
          completed_loops_json=excluded.completed_loops_json,
          corrections_json=excluded.corrections_json,
          preferences_json=excluded.preferences_json,
          last_dialogue_act=excluded.last_dialogue_act,
          last_user_preview=excluded.last_user_preview,
          last_selene_preview=excluded.last_selene_preview,
          state_json=excluded.state_json,
          provenance_boundary=excluded.provenance_boundary,
          updated_at=CURRENT_TIMESTAMP
        """,
        (
            int(state.get("session_id") or 0),
            str(state.get("active_topic") or ""),
            json.dumps(state.get("side_topics") or []),
            json.dumps(state.get("entities") or []),
            json.dumps(state.get("referents") or {}),
            json.dumps(state.get("open_loops") or []),
            json.dumps(state.get("completed_loops") or []),
            json.dumps(state.get("corrections") or []),
            json.dumps(state.get("preferences") or {}),
            str(state.get("last_dialogue_act") or ""),
            str(state.get("last_user_preview") or ""),
            str(state.get("last_selene_preview") or ""),
            json.dumps(state.get("pragmatics") or state.get("state") or {}),
            DIALOGUE_BOUNDARY,
        ),
    )


def _decode(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    return _with_guards(
        {
            "status": "dialogue_workspace_ready",
            "id": item.get("id"),
            "session_id": item.get("session_id"),
            "active_topic": item.get("active_topic"),
            "side_topics": _loads(item.get("side_topics_json"), []),
            "entities": _loads(item.get("entities_json"), []),
            "referents": _loads(item.get("referents_json"), {}),
            "open_loops": _loads(item.get("open_loops_json"), []),
            "completed_loops": _loads(item.get("completed_loops_json"), []),
            "corrections": _loads(item.get("corrections_json"), []),
            "preferences": _loads(item.get("preferences_json"), {}),
            "last_dialogue_act": item.get("last_dialogue_act"),
            "last_user_preview": item.get("last_user_preview"),
            "last_selene_preview": item.get("last_selene_preview"),
            "pragmatics": _loads(item.get("state_json"), {}),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": DIALOGUE_BOUNDARY,
        }
    )


def _events(conn: sqlite3.Connection, session_id: int, supplied: Any) -> list[dict[str, Any]]:
    if isinstance(supplied, list):
        return [item for item in supplied if isinstance(item, dict)][-8:]
    rows = conn.execute(
        "SELECT role, content AS preview, created_at FROM selene_chat_messages WHERE session_id = ? ORDER BY id DESC LIMIT 8",
        (session_id,),
    ).fetchall()
    return [dict(row) for row in reversed(rows)]


def _active_topic(text: str, prior: str, intent: str) -> str:
    if intent in {"greeting", "farewell", "gratitude", "affirmation", "reassurance_received", "warm_connection"}:
        return prior
    return _topic(text) or prior


def _topic(text: str) -> str:
    words = [word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text)]
    useful = [word for word in words if word not in STOP_WORDS]
    return " ".join(useful[:8])


def _question_units(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    units = [item.strip(" ,.;") for item in sentences if item.endswith("?") and item.strip(" ,.;?")]
    return [item if item.endswith("?") else item + "?" for item in units[:8]]


def _resolve_reference(text: str, previous: dict[str, Any], active_topic: str) -> dict[str, Any] | None:
    lower = text.lower()
    token = next((item for item in ("that one", "the other one", "that", "this", "it", "there") if re.search(rf"\b{re.escape(item)}\b", lower)), "")
    if not token or not previous:
        return None
    return {
        "token": token,
        "resolved_to": truncate(str(previous.get("preview") or active_topic), 240),
        "source": "immediately_preceding_turn",
        "confidence": "bounded",
    }


def _extract_entities(text: str) -> list[dict[str, str]]:
    names = re.findall(r"\b[A-Z][A-Za-z0-9_-]{2,}\b", text)
    known = [name for name in ("Selene", "Aleks", "Cocoon", "Tendril", "intelligenceOS") if name.lower() in text.lower()]
    return [{"name": name, "source": "current_turn"} for name in dict.fromkeys([*known, *names])][:20]


def _merge_entities(existing: list[Any], new: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for item in [*existing, *new]:
        if isinstance(item, dict) and str(item.get("name") or ""):
            merged[str(item["name"]).lower()] = {"name": str(item["name"]), "source": str(item.get("source") or "prior_turn")}
    return list(merged.values())[-30:]


def _session_preferences(text: str) -> dict[str, str]:
    lower = text.lower()
    if any(item in lower for item in ("keep it short", "short answer", "briefly", "be brief")):
        return {"response_depth": "brief", "scope": "current_session_only"}
    if any(item in lower for item in ("go deeper", "long form", "walk me through", "in detail")):
        return {"response_depth": "developed", "scope": "current_session_only"}
    return {}


def _indirect_request(text: str) -> dict[str, Any]:
    lower = text.lower()
    marker = next((item for item in ("could you", "would you", "can you", "i was wondering", "do you mind") if item in lower), "")
    return {"detected": bool(marker), "marker": marker, "meaning": "request" if marker else ""}


def _quotes(text: str) -> list[str]:
    return [truncate(item.strip(), 240) for item in re.findall(r'["“](.*?)["”]', text) if item.strip()][:8]


def _loop_id(session_id: int, question: str, index: int) -> str:
    digest = sha256(f"{session_id}:{index}:{question}".encode("utf-8")).hexdigest()[:12]
    return f"dialogue_loop_{digest}"


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value or ""))
    except json.JSONDecodeError:
        return fallback


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
