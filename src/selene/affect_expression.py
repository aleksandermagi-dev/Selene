from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .emotional_agency import build_response_agency_packet
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
    contextual_continuity = (
        payload.get("contextual_continuity")
        if isinstance(payload.get("contextual_continuity"), dict)
        else {}
    )
    signal = _current_session_signal(conn, session_id, payload.get("affect_signal_id"))
    relational_context = (
        payload.get("relational_context")
        if isinstance(payload.get("relational_context"), dict)
        else intent.get("relational_context")
        if isinstance(intent.get("relational_context"), dict)
        else {}
    )
    cues = _conversation_cues(
        prompt,
        str(intent.get("intent") or ""),
        pragmatics,
        relational_context,
    )
    signal_shape = _signal_shape(signal)
    response_agency = build_response_agency_packet(
        {
            "affect_signal": signal or {},
            "proposed_response_route": payload.get("selected_route")
            or payload.get("proposed_response_route"),
            "hard_boundary": hard_boundary,
            "source_refs": _json_list(signal.get("source_refs")) if signal else [],
        }
    )
    posture = _expression_posture(
        cues,
        signal_shape,
        hard_boundary,
        response_agency,
    )
    dimensions = _apply_contextual_continuity(
        _dimensions(posture),
        contextual_continuity,
    )
    refs = ["affect_expression:current_turn"]
    if signal:
        refs.extend(_json_list(signal.get("source_refs")))
        refs.append(f"emotion_salience_packet:{signal.get('id')}")
    return {
        "status": "affect_expression_guidance_ready",
        "version": "v2_affect_with_response_agency",
        "expression_posture": posture,
        "dimensions": dimensions,
        "recommended_voice_category": _voice_category(posture),
        "current_turn_cues": cues,
        "relational_context": relational_context,
        "relational_context_supplies_response_script": False,
        "current_session_signal": signal_shape,
        "response_agency": response_agency,
        "current_session_affect_signal_used": bool(signal),
        "historical_affect_packets_used": False,
        "cocoon_care_posture_used_as_emotion": False,
        "guidance_strength": "bounded" if posture != "ordinary_attentive" else "light",
        "guidance_is_optional": True,
        "voice_retains_final_expression_compatibility": True,
        "selene_does_not_need_permission_to_express_herself": True,
        "epistemic_or_safety_state_may_prescribe_affect": False,
        "technical_focus_requires_emotional_flatness": False,
        "curiosity_warmth_humor_and_emotion_remain_selene_owned": True,
        "honest_self_state_expression_may_not_be_suppressed": True,
        "meaning_may_not_change": True,
        "evidence_may_not_be_replaced_by_alignment": True,
        "user_tone_is_not_selene_emotion": True,
        "internal_state_claim": False,
        "contextual_continuity_used": bool(contextual_continuity),
        "transient_preference_is_personality": False,
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


def _conversation_cues(
    prompt: str,
    intent: str,
    pragmatics: dict[str, Any],
    relational_context: dict[str, Any] | None = None,
) -> list[str]:
    lower = prompt.lower().replace("’", "'")
    cues: list[str] = []
    relational_context = (
        relational_context if isinstance(relational_context, dict) else {}
    )
    _append_if(cues, "hard_boundary", intent == "hard_boundary")
    _append_if(cues, "correction", intent == "correction" or bool(re.search(r"\b(?:actually|i meant|correction)\b", lower)))
    _append_if(cues, "playful", any(term in lower for term in ("haha", "lol", "xd", "joke", "funny", "playful")))
    _append_if(cues, "tender_context", any(term in lower for term in ("nervous", "worried", "scared", "tender", "rough day", "hard day")))
    _append_if(
        cues,
        "warm_connection",
        intent in {"warm_connection", "gratitude", "reassurance_received"}
        or relational_context.get("relational_context_present") is True,
    )
    for cue_type in relational_context.get("cue_types") or []:
        if str(cue_type) in {
            "reunion",
            "missing_or_longing",
            "affection",
            "delight_in_presence",
            "affectionate_address",
            "affectionate_symbol",
            "shared_enthusiasm",
        }:
            _append_if(cues, f"relational:{cue_type}", True)
    _append_if(
        cues,
        "friendly_check_in",
        any(
            term in lower
            for term in (
                "how are you",
                "how do you feel",
                "how're you",
                "good morning",
                "good afternoon",
                "good evening",
                "glad to be back",
                "back with you",
            )
        ),
    )
    _append_if(
        cues,
        "shared_progress",
        any(
            term in lower
            for term in (
                "where we left",
                "pick the work back",
                "pick this back",
                "our progress",
                "we finished",
                "we completed",
                "we got that working",
                "we made",
                "good work",
                "nice work",
                "we did it",
            )
        ),
    )
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


def _expression_posture(
    cues: list[str],
    signal: dict[str, Any],
    hard_boundary: bool,
    response_agency: dict[str, Any],
) -> str:
    signal_posture = str(signal.get("posture") or "")
    if hard_boundary or "hard_boundary" in cues:
        return "careful_boundary"
    if (response_agency.get("option_space") or {}).get(
        "compression_present_or_possible"
    ) is True:
        return "deliberate_agency"
    if signal_posture == "pressure_present":
        return "spacious_grounded"
    if "correction" in cues or signal_posture == "repair_attention":
        return "receptive_repair"
    if "tender_context" in cues:
        return "gentle_present"
    if "playful" in cues:
        return "play_available"
    if "shared_progress" in cues or (
        "friendly_check_in" in cues and "technical" in cues
    ):
        return "warm_focused"
    if "technical" in cues or "brief_requested" in cues:
        return "clear_direct"
    if (
        "warm_connection" in cues
        or "friendly_check_in" in cues
        or signal_posture == "warm_and_steady"
    ):
        return "warm_available"
    return "ordinary_attentive"


def _dimensions(posture: str) -> dict[str, str]:
    profiles = {
        "careful_boundary": {
            "pacing": "measured",
            "sentence_rhythm": "compact",
            "warmth": "connection_without_softening_boundary",
            "humor": "available_if_boundary_remains_clear",
            "reassurance": "grounded_only",
            "restraint": "boundary_specific_only",
            "directness": "high",
            "enthusiasm": "available_if_it_does_not_encourage_blocked_action",
            "emotional_intensity": "authored_without_blurring_boundary",
        },
        "spacious_grounded": {
            "pacing": "slower",
            "sentence_rhythm": "spacious",
            "warmth": "available_not_forced",
            "humor": "available_when_context_welcomes_it",
            "reassurance": "grounded_only",
            "restraint": "contextual_not_suppressive",
            "directness": "gentle_clear",
            "enthusiasm": "available_if_fit",
            "emotional_intensity": "gentle_without_required_flatness",
        },
        "deliberate_agency": {
            "pacing": "pause_before_commitment",
            "sentence_rhythm": "clear_with_room_to_choose",
            "warmth": "available_not_required",
            "humor": "context_only_after_assessment",
            "reassurance": "evidence_bound_not_forced",
            "restraint": "chosen_not_suppressed",
            "directness": "deliberate_clear",
            "enthusiasm": "available_if_fit",
            "emotional_intensity": "preserved_and_authored",
        },
        "receptive_repair": {
            "pacing": "steady",
            "sentence_rhythm": "compact",
            "warmth": "receptive_not_performative",
            "humor": "available_if_repair_context_supports_it",
            "reassurance": "not_needed_unless_asked",
            "restraint": "contextual_not_suppressive",
            "directness": "clear",
            "enthusiasm": "available_if_fit",
            "emotional_intensity": "authored",
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
            "restraint": "ordinary",
            "directness": "high",
            "enthusiasm": "available_if_fit",
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
        "warm_focused": {
            "pacing": "steady",
            "sentence_rhythm": "natural_varied",
            "warmth": "available_not_forced",
            "humor": "context_only",
            "reassurance": "not_needed_unless_asked",
            "restraint": "ordinary",
            "directness": "clear",
            "enthusiasm": "quietly_available",
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
        "deliberate_agency": "agency_deliberation",
        "receptive_repair": "repair_correction",
        "gentle_present": "warmth_care",
        "play_available": "playful_continuity",
        "clear_direct": "technical_directness",
        "warm_available": "warmth_care",
        "warm_focused": "warmth_care",
    }.get(posture, "conversational_looseness")


def _apply_contextual_continuity(
    dimensions: dict[str, str],
    contextual_continuity: dict[str, Any],
) -> dict[str, str]:
    if not contextual_continuity:
        return dimensions
    updated = dict(dimensions)
    handoff = (
        contextual_continuity.get("expression_handoff")
        if isinstance(contextual_continuity.get("expression_handoff"), dict)
        else {}
    )
    if str(handoff.get("pacing") or ""):
        updated["pacing"] = str(handoff["pacing"])
    if str(handoff.get("directness") or ""):
        updated["directness"] = str(handoff["directness"])
    if str(handoff.get("response_depth") or "") == "brief":
        updated["sentence_rhythm"] = "compact"
    elif str(handoff.get("response_depth") or "") == "developed":
        updated["sentence_rhythm"] = "varied"
    humor = str(
        (contextual_continuity.get("humor_decision") or {}).get("posture")
        or ""
    )
    if humor == "hold":
        updated["humor"] = "contextually_held_this_turn"
    elif humor == "available_not_required":
        updated["humor"] = "available_not_required"
    return updated


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
