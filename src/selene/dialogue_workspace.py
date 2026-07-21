from __future__ import annotations

import json
import re
import sqlite3
from hashlib import sha256
from typing import Any

from .input_detangler import detangle_user_input
from .conversation_thread_loom import build_thread_braid
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
                "session_landmarks": [],
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
    input_interpretation = (
        payload.get("input_interpretation")
        if isinstance(payload.get("input_interpretation"), dict)
        else detangle_user_input(text)
    )
    interpreted_text = truncate(str(input_interpretation.get("interpreted_text") or text), 2400)
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    contextual_follow_up = (
        payload.get("contextual_follow_up")
        if isinstance(payload.get("contextual_follow_up"), dict)
        else {}
    )
    prior = dialogue_workspace_status(conn, session_id)
    events = _events(conn, session_id, payload.get("conversation_events"))
    previous = events[-1] if events else {}
    active_topic = _active_topic(
        interpreted_text,
        str(prior.get("active_topic") or ""),
        str(intent.get("intent") or ""),
        preserve_prior=contextual_follow_up.get("preserve_active_topic") is True,
    )
    questions = _question_units(interpreted_text)
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
    reference = _resolve_reference(
        interpreted_text,
        previous,
        active_topic,
        prior_referents=referents,
        recent_events=events,
    )
    if reference:
        referents[reference["token"]] = reference
    entities = _merge_entities(prior.get("entities") or [], _extract_entities(interpreted_text))
    corrections = list(prior.get("corrections") or [])
    correction = _correction_refinement(interpreted_text, previous)
    if str(intent.get("intent") or "") == "correction" or correction.get("detected") is True:
        corrections.append({**correction, "status": "active_refinement"})
    preferences = dict(prior.get("preferences") or {})
    preferences.update(_session_preferences(interpreted_text))
    utterance_units = _utterance_units(interpreted_text)
    prior_pragmatics = prior.get("pragmatics") if isinstance(prior.get("pragmatics"), dict) else {}
    thread_braid = build_thread_braid(
        {
            "session_id": session_id,
            "prompt": interpreted_text,
            "utterance_units": utterance_units,
            "prior_braid": prior_pragmatics.get("thread_braid") or {},
            "active_topic": active_topic,
            "thread_hints": payload.get("thread_hints") or [],
        }
    )
    braided_side_topics = [
        str(item.get("topic") or "")
        for item in thread_braid.get("threads") or []
        if isinstance(item, dict)
        and str(item.get("id") or "") != str(thread_braid.get("active_thread_id") or "")
        and str(item.get("topic") or "")
    ]
    side_topics = list(
        dict.fromkeys(
            [
                *list(prior.get("side_topics") or []),
                *[_topic(item) for item in questions[1:] if _topic(item)],
                *braided_side_topics,
            ]
        )
    )[-12:]
    pragmatics = {
        "dialogue_act": str(intent.get("dialogue_act") or intent.get("intent") or "direct_conversation"),
        "active_topic": active_topic,
        "resolved_reference": reference,
        "reference_candidates": (reference or {}).get("candidates") or [],
        "correction_refinement": correction,
        "utterance_units": utterance_units,
        "question_units": questions,
        "multi_part_prompt": len(questions) > 1,
        "indirect_request": _indirect_request(interpreted_text),
        "quoted_material": _quotes(interpreted_text),
        "input_interpretation": input_interpretation,
        "response_preference": preferences.get("response_depth") or "",
        "previous_turn_available": bool(previous),
        "previous_turn": previous,
        "contextual_follow_up": contextual_follow_up,
        "thread_braid": thread_braid,
        "session_landmarks": [
            item for item in prior_pragmatics.get("session_landmarks") or [] if isinstance(item, dict)
        ][-24:],
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
    pragmatics = state.get("pragmatics") if isinstance(state.get("pragmatics"), dict) else {}
    prior_landmarks = [
        item for item in pragmatics.get("session_landmarks") or [] if isinstance(item, dict)
    ]
    new_landmarks = _response_landmarks(
        candidate,
        active_topic=str(state.get("active_topic") or ""),
        thread_braid=pragmatics.get("thread_braid") if isinstance(pragmatics.get("thread_braid"), dict) else {},
        coverage=coverage,
    )
    session_landmarks = _merge_landmarks(prior_landmarks, new_landmarks)
    updated = {
        **state,
        "status": "dialogue_workspace_response_recorded",
        "open_loops": open_loops[-20:],
        "completed_loops": completed[-30:],
        "last_selene_preview": truncate(candidate, 360),
        "pragmatics": {
            **pragmatics,
            "last_response_coverage": coverage,
            "session_landmarks": session_landmarks,
        },
        "session_landmarks": session_landmarks,
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
    pragmatics = _loads(item.get("state_json"), {})
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
            "pragmatics": pragmatics,
            "session_landmarks": [
                value for value in pragmatics.get("session_landmarks") or [] if isinstance(value, dict)
            ][-24:],
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


def _active_topic(text: str, prior: str, intent: str, *, preserve_prior: bool = False) -> str:
    if preserve_prior and prior:
        return prior
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


def _resolve_reference(
    text: str,
    previous: dict[str, Any],
    active_topic: str,
    *,
    prior_referents: dict[str, Any] | None = None,
    recent_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    lower = text.lower()
    tokens = (
        "the first one", "the second one", "the third one", "the other one",
        "first one", "second one", "third one", "that one", "this one",
        "the former", "the latter", "former", "latter", "that", "this", "it", "there",
        "they", "them", "those", "he", "she",
    )
    token = next((item for item in tokens if re.search(rf"\b{re.escape(item)}\b", lower)), "")
    if not token or not previous:
        return None
    previous_preview = truncate(str(previous.get("preview") or ""), 480)
    candidates: list[str] = []
    for event in reversed(recent_events or []):
        event_preview = truncate(str(event.get("preview") or ""), 480)
        event_candidates = _reference_candidates(event_preview, "")
        if len(event_candidates) >= 2:
            candidates = event_candidates
            break
    if not candidates:
        candidates = _reference_candidates(previous_preview, active_topic)
    selected = _select_reference_candidate(token, candidates, prior_referents or {})
    if selected:
        status = "resolved"
        confidence = "bounded"
        resolved_to = selected
    elif token in {"the other one", "that one", "this one", "that", "this", "it", "there", "he", "she"} and len(candidates) > 1:
        status = "materially_ambiguous"
        confidence = "unresolved"
        resolved_to = ""
    else:
        status = "resolved_to_previous_turn"
        confidence = "bounded"
        resolved_to = previous_preview or active_topic
    return {
        "token": token,
        "resolved_to": truncate(resolved_to, 240),
        "source": "immediately_preceding_turn",
        "confidence": confidence,
        "resolution_status": status,
        "candidates": candidates,
        "ask_if_materially_ambiguous": status == "materially_ambiguous",
    }


def _reference_candidates(previous_preview: str, active_topic: str) -> list[str]:
    text = " ".join(previous_preview.split())
    candidates: list[str] = []
    numbered = re.findall(r"(?:^|[;.]\s*|\b)(?:option|route|plan|lesson)?\s*(?:one|two|three|1|2|3)\s*[:.)-]\s*([^;.!?]+)", text, flags=re.IGNORECASE)
    candidates.extend(item.strip(" ,") for item in numbered if item.strip(" ,"))
    if len(candidates) < 2:
        pair = re.search(
            r"\b(?:between|compare|options? (?:are|include)|either)\s+(.{2,90}?)\s+(?:and|or|versus|vs\.?)\s+(.{2,90}?)(?:[.!?]|$)",
            text,
            flags=re.IGNORECASE,
        )
        if pair:
            candidates.extend([pair.group(1).strip(" ,"), pair.group(2).strip(" ,")])
    if not candidates and text:
        candidates.append(text)
    elif not candidates and active_topic:
        candidates.append(active_topic)
    return list(dict.fromkeys(truncate(item, 160) for item in candidates if item))[:6]


def _select_reference_candidate(token: str, candidates: list[str], prior_referents: dict[str, Any]) -> str:
    index_map = {
        "the first one": 0, "first one": 0, "the former": 0, "former": 0,
        "the second one": 1, "second one": 1, "the latter": 1, "latter": 1,
        "the third one": 2, "third one": 2,
    }
    if token in index_map and len(candidates) > index_map[token]:
        return candidates[index_map[token]]
    if token == "the other one" and len(candidates) == 2:
        recent_resolutions = [
            str(item.get("resolved_to") or "")
            for item in prior_referents.values()
            if isinstance(item, dict) and str(item.get("resolved_to") or "")
        ]
        if recent_resolutions:
            return next((item for item in candidates if item not in recent_resolutions[-2:]), "")
    if token in {"that one", "this one"} and len(candidates) == 1:
        return candidates[0]
    if token in {"that", "this", "it", "there", "he", "she"} and len(candidates) == 1:
        return candidates[0]
    if token in {"they", "them", "those"} and len(candidates) == 2:
        return " and ".join(candidates)
    return ""


def _correction_refinement(text: str, previous: dict[str, Any]) -> dict[str, Any]:
    normalized = " ".join(text.split())
    if any(
        marker in normalized.lower()
        for marker in ("separate question", "different question", "new question", "separate topic", "different topic", "on another topic")
    ):
        return {
            "detected": False,
            "summary": "",
            "corrected_meaning": "",
            "replaced_meaning": "",
            "replaces_turn": "",
            "scope": "current_session_refinement_only",
            "durable_memory_write": False,
        }
    patterns = (
        r"\b(?:i meant|what i meant was)\s+(.+?)\s*,?\s+not\s+(.+?)(?:[.!?]|$)",
        r"\bnot\s+(.+?)\s*[,;]\s*(?:i meant\s+)?(.+?)(?:[.!?]|$)",
    )
    corrected = ""
    replaced = ""
    first = re.search(patterns[0], normalized, flags=re.IGNORECASE)
    if first:
        corrected, replaced = first.group(1), first.group(2)
    else:
        second = re.search(patterns[1], normalized, flags=re.IGNORECASE)
        if second:
            replaced, corrected = second.group(1), second.group(2)
    detected = bool(corrected or re.search(r"\b(?:actually|i meant|not what i meant|correction)\b", normalized, flags=re.IGNORECASE))
    return {
        "detected": detected,
        "summary": truncate(normalized, 360) if detected else "",
        "corrected_meaning": truncate(corrected.strip(" ,"), 240),
        "replaced_meaning": truncate(replaced.strip(" ,"), 240),
        "replaces_turn": truncate(str(previous.get("preview") or ""), 240) if detected else "",
        "scope": "current_session_refinement_only",
        "durable_memory_write": False,
    }


def _utterance_units(text: str) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for index, raw in enumerate(re.split(r"(?<=[.!?])\s+|\n+", text.strip())):
        value = raw.strip()
        if not value:
            continue
        lower = value.lower()
        if value.endswith("?"):
            kind = "question"
        elif re.search(r"\b(?:actually|i meant|not what i meant|correction)\b", lower):
            kind = "correction"
        elif re.match(r"^(?:please\s+)?(?:compare|explain|show|tell|help|give|list|summarize|check|walk)\b", lower):
            kind = "direct_request"
        elif re.search(r"\b(?:could you|would you|can you|i need you to|let's|lets)\b", lower):
            kind = "indirect_request"
        elif re.search(r"\b(?:i prefer|keep it|make it|be brief|go deeper)\b", lower):
            kind = "session_preference"
        else:
            kind = "statement"
        units.append({"id": f"utterance_{index + 1}", "text": truncate(value, 480), "kind": kind, "position": index})
    return units[:12]


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


def _response_landmarks(
    candidate: str,
    *,
    active_topic: str,
    thread_braid: dict[str, Any],
    coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    if not candidate.strip():
        return []
    active_thread = str(thread_braid.get("active_thread_id") or "")
    sentences = [
        truncate(item.strip(), 480)
        for item in re.split(r"(?<=[.!?])\s+|\n+", candidate)
        if item.strip()
    ]
    landmarks: list[dict[str, Any]] = []
    for index, sentence in enumerate(sentences[:10]):
        lower = sentence.lower()
        kind = (
            "condition"
            if re.search(r"\b(?:if|unless|when|would change|reopen)\b", lower)
            else "recommendation"
            if re.search(r"\b(?:recommend|should|start with|first|next step|prefer|choose|use)\b", lower)
            else "limit"
            if re.search(r"\b(?:limit|cannot|can't|does not|doesn't|however|but)\b", lower)
            else "conclusion"
        )
        digest = sha256(f"{active_thread}|{sentence.lower()}".encode("utf-8")).hexdigest()[:12]
        landmarks.append(
            {
                "id": f"session_landmark_{digest}",
                "kind": kind,
                "summary": sentence,
                "topic": truncate(active_topic, 240),
                "thread_id": active_thread,
                "response_position": index,
                "coverage_complete_at_recording": coverage.get("all_required_addressed") is True,
                "source": "visible_selene_response",
                "scope": "current_session_only",
            }
        )
    return landmarks


def _merge_landmarks(existing: list[dict[str, Any]], new: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in [*existing, *new]:
        key = str(item.get("id") or "") or " ".join(str(item.get("summary") or "").lower().split())
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged[-24:]


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
