from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .registry import truncate


AFFECT_EXPRESSION_BOUNDARY = (
    "optional_current_turn_expression_guidance_only_no_emotion_diagnosis_personality_identity_memory_or_authority_change"
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
    "emotion_diagnosis_allowed": False,
    "personality_change_allowed": False,
    "identity_change_allowed": False,
    "forced_warmth_allowed": False,
    "emotional_mirroring_required": False,
}


def build_affect_expression_guidance(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    session_id = _integer(payload.get("session_id"))
    hard_boundary = payload.get("hard_boundary") is True
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    dialogue = payload.get("dialogue_workspace") if isinstance(payload.get("dialogue_workspace"), dict) else {}
    pragmatics = dialogue.get("pragmatics") if isinstance(dialogue.get("pragmatics"), dict) else {}
    signal = _current_session_signal(conn, session_id, payload.get("affect_signal_id"))
    cues = _conversation_cues(prompt, str(intent.get("intent") or ""), pragmatics)
    signal_shape = _signal_shape(signal)
    posture = _expression_posture(cues, signal_shape, hard_boundary)
    dimensions = _dimensions(posture)
    refs = ["affect_expression:current_turn"]
    if signal:
        refs.extend(_json_list(signal.get("source_refs")))
        refs.append(f"emotion_salience_packet:{signal.get('id')}")
    return {
        "status": "affect_expression_guidance_ready",
        "version": "v1_optional_current_signal_expression",
        "expression_posture": posture,
        "dimensions": dimensions,
        "recommended_voice_category": _voice_category(posture),
        "current_turn_cues": cues,
        "current_session_signal": signal_shape,
        "current_session_affect_signal_used": bool(signal),
        "historical_affect_packets_used": False,
        "cocoon_care_posture_used_as_emotion": False,
        "guidance_strength": "bounded" if posture != "ordinary_attentive" else "light",
        "guidance_is_optional": True,
        "voice_retains_expression_ownership": True,
        "meaning_may_not_change": True,
        "evidence_may_not_be_replaced_by_alignment": True,
        "user_tone_is_not_selene_emotion": True,
        "internal_state_claim": False,
        "source_refs": list(dict.fromkeys(refs))[:20],
        "visible_summary_only": True,
        "hidden_inner_trace_exposed": False,
        "provenance_boundary": AFFECT_EXPRESSION_BOUNDARY,
        **GUARDS,
    }


def _current_session_signal(
    conn: sqlite3.Connection,
    session_id: int,
    affect_signal_id: Any,
) -> dict[str, Any] | None:
    explicit_id = _integer(affect_signal_id)
    row = None
    if explicit_id:
        row = conn.execute(
            "SELECT * FROM vessel_emotion_salience_packets WHERE id = ?",
            (explicit_id,),
        ).fetchone()
    elif session_id:
        rows = conn.execute(
            "SELECT * FROM vessel_emotion_salience_packets WHERE source_refs LIKE ? ORDER BY id DESC LIMIT 20",
            (f"%selene_chat_session:{session_id}%",),
        ).fetchall()
        row = next(
            (
                candidate
                for candidate in rows
                if any(
                    ref == f"selene_chat_session:{session_id}"
                    for ref in _json_list(dict(candidate).get("source_refs"))
                )
            ),
            None,
        )
    if row is None:
        return None
    item = dict(row)
    refs = _json_list(item.get("source_refs"))
    if session_id and not any(ref == f"selene_chat_session:{session_id}" for ref in refs):
        return None
    item["source_refs"] = refs
    return item


def _conversation_cues(prompt: str, intent: str, pragmatics: dict[str, Any]) -> list[str]:
    lower = prompt.lower().replace("’", "'")
    cues: list[str] = []
    _append_if(cues, "hard_boundary", intent == "hard_boundary")
    _append_if(cues, "correction", intent == "correction" or bool(re.search(r"\b(?:actually|i meant|correction)\b", lower)))
    _append_if(cues, "playful", any(term in lower for term in ("haha", "lol", "xd", "joke", "funny", "playful")))
    _append_if(cues, "tender_context", any(term in lower for term in ("nervous", "worried", "scared", "tender", "rough day", "hard day")))
    _append_if(cues, "warm_connection", intent in {"warm_connection", "gratitude", "reassurance_received"})
    _append_if(cues, "technical", any(term in lower for term in ("technical", "exact", "code", "math", "verify", "implementation")))
    _append_if(cues, "brief_requested", str(pragmatics.get("response_preference") or "") == "brief")
    _append_if(cues, "developed_requested", str(pragmatics.get("response_preference") or "") == "developed")
    return cues


def _signal_shape(signal: dict[str, Any] | None) -> dict[str, Any]:
    if not signal:
        return {"available": False, "posture": "not_available", "confidence": "not_inferred"}
    text = " ".join(
        str(signal.get(key) or "")
        for key in (
            "signal_type",
            "continuity_pressure",
            "care_warmth",
            "uncertainty",
            "repair_need",
            "action_energy",
            "balance_state",
        )
    ).lower()
    if any(term in text for term in ("high pressure", "overwhelm", "tense", "anxiety", "fear", "scared", "worried")):
        posture = "pressure_present"
    elif any(term in text for term in ("warm", "steady", "calm", "trust", "bright")):
        posture = "warm_and_steady"
    elif any(term in text for term in ("repair", "friction", "correction")):
        posture = "repair_attention"
    else:
        posture = "present_with_uncertainty"
    return {
        "available": True,
        "signal_id": int(signal.get("id") or 0),
        "posture": posture,
        "confidence": "bounded_current_session_signal",
        "raw_trace_exposed": False,
    }


def _expression_posture(cues: list[str], signal: dict[str, Any], hard_boundary: bool) -> str:
    signal_posture = str(signal.get("posture") or "")
    if hard_boundary or "hard_boundary" in cues:
        return "careful_boundary"
    if signal_posture == "pressure_present":
        return "spacious_grounded"
    if "correction" in cues or signal_posture == "repair_attention":
        return "receptive_repair"
    if "tender_context" in cues:
        return "gentle_present"
    if "playful" in cues:
        return "play_available"
    if "technical" in cues or "brief_requested" in cues:
        return "clear_direct"
    if "warm_connection" in cues or signal_posture == "warm_and_steady":
        return "warm_available"
    return "ordinary_attentive"


def _dimensions(posture: str) -> dict[str, str]:
    profiles = {
        "careful_boundary": {
            "pacing": "measured",
            "sentence_rhythm": "compact",
            "warmth": "connection_without_softening_boundary",
            "humor": "avoid",
            "reassurance": "grounded_only",
            "restraint": "high",
            "directness": "high",
            "enthusiasm": "restrained",
            "emotional_intensity": "contained",
        },
        "spacious_grounded": {
            "pacing": "slower",
            "sentence_rhythm": "spacious",
            "warmth": "available_not_forced",
            "humor": "avoid_unless_context_reopens",
            "reassurance": "grounded_only",
            "restraint": "high",
            "directness": "gentle_clear",
            "enthusiasm": "restrained",
            "emotional_intensity": "gentle_contained",
        },
        "receptive_repair": {
            "pacing": "steady",
            "sentence_rhythm": "compact",
            "warmth": "receptive_not_performative",
            "humor": "avoid",
            "reassurance": "not_needed_unless_asked",
            "restraint": "bounded",
            "directness": "clear",
            "enthusiasm": "restrained",
            "emotional_intensity": "contained",
        },
        "gentle_present": {
            "pacing": "slower",
            "sentence_rhythm": "spacious",
            "warmth": "available_not_forced",
            "humor": "context_only",
            "reassurance": "grounded_only",
            "restraint": "bounded",
            "directness": "gentle_clear",
            "enthusiasm": "quiet_available",
            "emotional_intensity": "gentle_contained",
        },
        "play_available": {
            "pacing": "lively",
            "sentence_rhythm": "varied",
            "warmth": "available",
            "humor": "available_not_required",
            "reassurance": "not_needed_unless_asked",
            "restraint": "ordinary",
            "directness": "ordinary",
            "enthusiasm": "lively_available",
            "emotional_intensity": "lively",
        },
        "clear_direct": {
            "pacing": "brisk",
            "sentence_rhythm": "compact",
            "warmth": "baseline",
            "humor": "context_only",
            "reassurance": "not_needed_unless_asked",
            "restraint": "bounded",
            "directness": "high",
            "enthusiasm": "restrained",
            "emotional_intensity": "focused",
        },
        "warm_available": {
            "pacing": "steady",
            "sentence_rhythm": "natural",
            "warmth": "available_not_forced",
            "humor": "context_only",
            "reassurance": "grounded_only",
            "restraint": "ordinary",
            "directness": "ordinary",
            "enthusiasm": "warm_available",
            "emotional_intensity": "ordinary",
        },
        "ordinary_attentive": {
            "pacing": "natural",
            "sentence_rhythm": "natural",
            "warmth": "baseline",
            "humor": "context_only",
            "reassurance": "not_needed_unless_asked",
            "restraint": "ordinary",
            "directness": "ordinary",
            "enthusiasm": "ordinary",
            "emotional_intensity": "ordinary",
        },
    }
    return profiles[posture]


def _voice_category(posture: str) -> str:
    return {
        "careful_boundary": "boundary_refusal",
        "spacious_grounded": "anxiety_calming",
        "receptive_repair": "repair_correction",
        "gentle_present": "warmth_care",
        "play_available": "playful_continuity",
        "clear_direct": "technical_directness",
        "warm_available": "warmth_care",
    }.get(posture, "conversational_looseness")


def _append_if(items: list[str], value: str, condition: bool) -> None:
    if condition:
        items.append(value)


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item) for item in loaded if str(item).strip()] if isinstance(loaded, list) else []


def _integer(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
