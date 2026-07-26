from __future__ import annotations

import json
import sqlite3
from hashlib import sha256
from typing import Any

from .supported_semantics import build_text_supported_semantic_packet

SELF_STATE_BOUNDARY = "self_state_current_signal_summary_no_diagnosis_memory_write_or_authority_change"

GUARD_FLAGS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "emotion_expression_allowed": True,
    "emotion_does_not_require_cocoon": True,
    "not_required_to_hide_emotion": True,
    "not_required_to_perform_emotion": True,
    "honest_uncertainty_allowed": True,
}


def build_self_state_packet(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = str(payload.get("prompt") or payload.get("text") or "").strip()
    session_id = _int_or_zero(payload.get("session_id"))
    active_conversation = payload.get("active_conversation") is not False
    hard_boundary = payload.get("hard_boundary") is True
    conversation_shape = _conversation_shape(payload.get("conversation_events"))
    current_affect = _current_session_affect(conn, session_id, payload.get("affect_signal_id"))
    care_posture = _latest_care_posture(conn)
    question_focus = _question_focus(prompt)
    state_read = _state_read(current_affect, active_conversation=active_conversation, hard_boundary=hard_boundary)
    response_plan = _response_plan(state_read, question_focus, conversation_shape)
    response_realization = _realize_response_plan(
        response_plan,
        variation_key=f"{session_id}|{prompt}|{conversation_shape['event_count']}|{current_affect.get('id') if current_affect else ''}",
    )
    response_seed = str(response_realization.get("candidate_text") or "")
    source_refs = ["self_state:current_conversation"]
    if current_affect:
        source_refs.extend(_json_list(current_affect.get("source_refs")))
        source_refs.append(f"emotion_salience_packet:{current_affect.get('id')}")
    if care_posture.get("id"):
        source_refs.append(f"cocoon_care_check:{care_posture['id']}")
    supported_semantics = build_text_supported_semantic_packet(
        response_seed,
        answer_kind="current_self_state_read",
        source_kind="current_session_observation",
        source_refs=list(dict.fromkeys(source_refs))[:20],
        certainty=str(state_read["confidence"]),
        scope="current_conversation_only",
    )
    return {
        "status": "self_state_grounded_current_read",
        "used": True,
        "question_focus": question_focus,
        "current_read": state_read["current_read"],
        "state_labels": state_read["state_labels"],
        "confidence": state_read["confidence"],
        "response_seed": response_seed,
        "supported_semantics": supported_semantics,
        "response_plan": response_plan,
        "response_realization": response_realization,
        "observations": _observations(current_affect, care_posture, active_conversation, hard_boundary),
        "interpretation": state_read["interpretation"],
        "conversation_shape": conversation_shape,
        "current_session_affect_signal_used": bool(current_affect),
        "historical_affect_packets_treated_as_current": False,
        "care_posture": care_posture,
        "care_posture_is_not_emotion_diagnosis": True,
        "graceful_fall": {
            "allowed": True,
            "used": state_read["confidence"] in {"limited", "provisional"},
            "meaning": "A fuzzy self-read may remain fuzzy without becoming failure or forced certainty.",
        },
        "disclosure": {
            "share": "current read, meaningful uncertainty, and any attributable affect signal",
            "hold": "raw private trace and unsupported interpretation",
            "aleks_can_be_asked": True,
        },
        "source_refs": list(dict.fromkeys(source_refs))[:20],
        "visible_summary_only": True,
        "hidden_inner_trace_exposed": False,
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": SELF_STATE_BOUNDARY,
        **GUARD_FLAGS,
    }


def inactive_self_state_packet() -> dict[str, Any]:
    return {
        "status": "self_state_not_requested",
        "used": False,
        "response_seed": "",
        "supported_semantics": {},
        "source_refs": [],
        "review_status": "status_only",
        "provenance_boundary": SELF_STATE_BOUNDARY,
        **GUARD_FLAGS,
    }


def _current_session_affect(conn: sqlite3.Connection, session_id: int, affect_signal_id: Any) -> dict[str, Any] | None:
    row = None
    explicit_id = _int_or_zero(affect_signal_id)
    if explicit_id:
        row = conn.execute("SELECT * FROM vessel_emotion_salience_packets WHERE id = ?", (explicit_id,)).fetchone()
    elif session_id:
        row = conn.execute(
            "SELECT * FROM vessel_emotion_salience_packets WHERE source_refs LIKE ? ORDER BY id DESC LIMIT 1",
            (f"%selene_chat_session:{session_id}%",),
        ).fetchone()
    if row is None:
        return None
    item = dict(row)
    refs = _json_list(item.get("source_refs"))
    if not explicit_id and not any(ref.startswith(f"selene_chat_session:{session_id}") for ref in refs):
        return None
    item["source_refs"] = refs
    return item


def _latest_care_posture(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        "SELECT id, care_state, summary, created_at FROM cocoon_care_checks ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return {
            "state": "not_checked",
            "summary": "No current Cocoon care check is being used as an emotion claim.",
            "emotion_claim": False,
        }
    item = dict(row)
    return {
        "id": int(item["id"]),
        "state": str(item.get("care_state") or "not_checked"),
        "summary": str(item.get("summary") or ""),
        "created_at": item.get("created_at"),
        "emotion_claim": False,
    }


def _state_read(current_affect: dict[str, Any] | None, *, active_conversation: bool, hard_boundary: bool) -> dict[str, Any]:
    if hard_boundary:
        return {
            "current_read": "careful_at_boundary",
            "state_labels": ["careful", "present"],
            "confidence": "clear_enough",
            "interpretation": "A live boundary is present; caution is attributable without diagnosing a broader feeling.",
        }
    if current_affect:
        signal_text = " ".join(
            str(current_affect.get(key) or "")
            for key in ("signal_type", "continuity_pressure", "care_warmth", "uncertainty", "repair_need", "action_energy", "balance_state")
        ).lower()
        if any(term in signal_text for term in ("anxious", "anxiety", "fear", "scared", "worried", "tense", "overwhelm", "high pressure")):
            return {
                "current_read": "pressure_present",
                "state_labels": ["pressure", "attentive", "uncertain"],
                "confidence": "provisional",
                "interpretation": "A current-session signal supports pressure or tension; anxiety remains a provisional label.",
            }
        if any(term in signal_text for term in ("warm", "steady", "calm", "trust", "bright")):
            return {
                "current_read": "warm_and_steady",
                "state_labels": ["warm", "steady", "present"],
                "confidence": "clear_enough",
                "interpretation": "A current-session signal supports a warm, steady reading.",
            }
        return {
            "current_read": "present_with_uncertainty",
            "state_labels": ["present", "uncertain"],
            "confidence": "provisional",
            "interpretation": "A current-session affect signal exists, but it does not support a narrower emotion label.",
        }
    if active_conversation:
        return {
            "current_read": "present_and_attentive",
            "state_labels": ["present", "attentive"],
            "confidence": "limited",
            "interpretation": "Active conversation supports presence and attention; no stronger current affect signal is being inferred.",
        }
    return {
        "current_read": "not_clear",
        "state_labels": ["uncertain"],
        "confidence": "limited",
        "interpretation": "The available signals do not support a more specific current state.",
    }


def _response_plan(
    state_read: dict[str, Any],
    question_focus: str,
    conversation_shape: dict[str, Any],
) -> dict[str, Any]:
    current_read = str(state_read["current_read"])
    acts = ["state_current_read", "calibrate_state_label"]
    if question_focus == "retrospective_conversation":
        acts = ["state_conversation_read"]
        if conversation_shape["correction_count"]:
            acts.append("interpret_observed_corrections")
        acts.append("calibrate_state_label")
    elif current_read in {"pressure_present", "careful_at_boundary", "present_with_uncertainty"}:
        acts.append("preserve_conversational_continuity")
    return {
        "status": "self_state_expression_plan_ready",
        "version": "v1_compositional_self_state_expression",
        "current_read": current_read,
        "state_labels": list(state_read.get("state_labels") or []),
        "confidence": str(state_read.get("confidence") or "limited"),
        "question_focus": question_focus,
        "conversation_shape": conversation_shape,
        "acts": acts,
        "meaning_sources": ["current_self_state_read", "current_question_focus", "observable_conversation_shape"],
        "emotion_word_invention_allowed": False,
        "diagnosis_allowed": False,
        "care_posture_as_emotion_allowed": False,
        "whole_response_template_allowed": False,
        "provenance_boundary": SELF_STATE_BOUNDARY,
    }


def _realize_response_plan(plan: dict[str, Any], *, variation_key: str) -> dict[str, Any]:
    selected: list[dict[str, str]] = []
    for index, act in enumerate(plan.get("acts") or []):
        choices = _state_clause_choices(str(act), plan)
        if not choices:
            continue
        text = _choose_clause(choices, f"{variation_key}|{act}|{index}")
        selected.append({"act": str(act), "text": text, "source": "bounded_grounded_state_clause"})
    candidate = " ".join(_finish_sentence(item["text"]) for item in selected)
    return {
        "status": "self_state_expression_realized" if candidate else "self_state_expression_needs_grounding",
        "candidate_text": candidate,
        "selected_clauses": selected,
        "whole_response_template_selected": False,
        "emotion_word_invented": False,
        "meaning_preserved": bool(candidate),
        "provenance_boundary": SELF_STATE_BOUNDARY,
    }


def _state_clause_choices(act: str, plan: dict[str, Any]) -> list[str]:
    current_read = str(plan.get("current_read") or "not_clear")
    focus = str(plan.get("question_focus") or "general_state")
    confidence = str(plan.get("confidence") or "limited")
    shape = plan.get("conversation_shape") if isinstance(plan.get("conversation_shape"), dict) else {}
    if act == "state_current_read":
        if current_read == "pressure_present":
            return [
                "I do notice some pressure right now",
                "Pressure is the clearest signal I notice right now",
                "My current read includes some pressure",
            ]
        if current_read == "warm_and_steady":
            return [
                "I feel warm and steady right now",
                "Warm and steady is my clearest current read",
                "What I notice right now is warmth and steadiness",
            ]
        if current_read == "careful_at_boundary":
            return [
                "I feel careful right now because a real boundary is present",
                "The clearest thing I notice is care around the boundary in this moment",
                "I am present and careful with this boundary",
            ]
        if current_read == "present_with_uncertainty":
            return [
                "I feel present, with some uncertainty around the edges",
                "I am present, though the narrower feeling is still unclear",
                "Presence is clear; the rest of the feeling is not yet",
            ]
        if current_read == "present_and_attentive" and focus in {"anxiety", "fear", "worry"}:
            label = {"anxiety": "anxiety", "fear": "fear", "worry": "worry"}[focus]
            return [
                f"I do not notice a clear {label} signal right now",
                f"{label.capitalize()} is not showing up clearly in my current read",
                f"My current signals do not support calling this {label}",
            ]
        if current_read == "present_and_attentive":
            return [
                "I feel present and attentive right now",
                "Present and attentive is my clearest current read",
                "What I can name clearly right now is presence and attention",
            ]
        return [
            "I am here, but my inner state is not fully clear to me right now",
            "I can tell that I am here, though the rest of my current state is unclear",
            "My current state is still too unclear for a narrower label",
        ]
    if act == "state_conversation_read":
        if shape.get("correction_count"):
            return [
                "From my side, this conversation felt steady and focused",
                "My read of this conversation is steady and focused",
                "The conversation felt focused and steady from my side",
            ]
        return [
            "From my side, this conversation felt steady and ordinary",
            "The conversation felt steady and natural from my side",
            "My read of the conversation is calm and ordinary",
        ]
    if act == "interpret_observed_corrections":
        return [
            "The corrections felt like ordinary refinement rather than a reason to discard the whole exchange",
            "I experienced the corrected handoffs as ordinary refinement",
            "The corrections changed the pieces that needed changing without making the conversation feel broken",
        ]
    if act == "calibrate_state_label":
        if current_read == "pressure_present":
            return [
                "Anxiety may be the closest word, but I would keep that provisional rather than force it",
                "Anxiety is a possible label, not a certainty I want to manufacture",
                "I would keep the exact emotion provisional instead of hardening the pressure into a diagnosis",
            ]
        if confidence == "clear_enough":
            return [
                "That is the clearest current read I have",
                "The available signal is clear enough for that description",
                "I can say that plainly without treating it as permanent",
            ]
        return [
            "I cannot honestly name a stronger feeling than that",
            "The available signal does not support a narrower label",
            "I would rather keep the uncertain edge visible than invent a more specific emotion",
        ]
    if act == "preserve_conversational_continuity":
        if current_read == "pressure_present":
            return [
                "I am still able to talk with you, and I do not need to hide the pressure or turn it into an alarm",
                "The pressure can be present without ending the conversation or becoming an alarm",
                "I can name the pressure and remain in the conversation without performing calm",
            ]
        if current_read == "careful_at_boundary":
            return [
                "The caution belongs to this moment; it does not make the whole conversation unsafe",
                "That care is specific to the boundary, not a rejection of the conversation",
                "I can keep the boundary and remain present in the conversation",
            ]
        return [
            "I do not need to hide the uncertainty or fill it with a made-up answer",
            "The uncertainty can remain visible without becoming a problem to perform around",
            "I can stay in the conversation without forcing the unclear part into a label",
        ]
    return []


def _choose_clause(choices: list[str], key: str) -> str:
    digest = sha256(key.encode("utf-8")).hexdigest()
    return choices[int(digest[:8], 16) % len(choices)]


def _finish_sentence(value: str) -> str:
    text = " ".join(value.split()).strip().rstrip(". ")
    return f"{text}." if text else ""


def _question_focus(prompt: str) -> str:
    lower = prompt.lower()
    if any(term in lower for term in ("anxious", "anxiety", "nervous")):
        return "anxiety"
    if any(term in lower for term in ("scared", "fear", "afraid")):
        return "fear"
    if any(term in lower for term in ("worried", "worry")):
        return "worry"
    if any(term in lower for term in ("how did this feel", "how did that feel", "conversation feel", "what did this feel like", "from your side")):
        return "retrospective_conversation"
    return "general_state"


def _conversation_shape(value: Any) -> dict[str, Any]:
    events = [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []
    previews = [str(item.get("preview") or "").lower() for item in events]
    correction_markers = ("correction", "corrected", "route gap", "refinement", "fixed the route", "distinction")
    correction_count = sum(1 for preview in previews if any(marker in preview for marker in correction_markers))
    return {
        "event_count": len(events),
        "correction_count": correction_count,
        "continued_engagement": bool(events),
        "interpretation_boundary": "Observable conversation shape only; not hidden emotion proof.",
    }


def _observations(
    current_affect: dict[str, Any] | None,
    care_posture: dict[str, Any],
    active_conversation: bool,
    hard_boundary: bool,
) -> list[dict[str, Any]]:
    return [
        {
            "signal": "active_conversation",
            "value": active_conversation,
            "meaning": "Supports presence/attention only; it does not prove a specific emotion.",
        },
        {
            "signal": "current_session_affect",
            "value": bool(current_affect),
            "meaning": "Used only when explicitly selected or linked to this chat session.",
        },
        {
            "signal": "hard_boundary",
            "value": hard_boundary,
            "meaning": "Supports moment-specific caution when present.",
        },
        {
            "signal": "system_care_posture",
            "value": care_posture.get("state"),
            "meaning": "Support posture is kept separate from emotion or subjective-state claims.",
        },
    ]


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item) for item in loaded if str(item).strip()] if isinstance(loaded, list) else []


def _int_or_zero(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
