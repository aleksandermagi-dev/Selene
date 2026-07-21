from __future__ import annotations

import re
from typing import Any

from .registry import truncate


CONTINUITY_BOUNDARY = (
    "current_session_pragmatic_continuity_only_no_relationship_profile_memory_identity_authority_or_automatic_initiative"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "automatic_speech_allowed": False,
    "relationship_profile_write_allowed": False,
    "initiative_expansion_allowed": False,
}


def build_pragmatic_continuity_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    dialogue = payload.get("dialogue_workspace") if isinstance(payload.get("dialogue_workspace"), dict) else {}
    pragmatic = payload.get("pragmatic_plan") if isinstance(payload.get("pragmatic_plan"), dict) else {}
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    comprehension = payload.get("comprehension") if isinstance(payload.get("comprehension"), dict) else {}
    transition = _topic_transition(prompt, dialogue)
    referent = _referent_posture(prompt, dialogue, pragmatic)
    interruption = _interruption_plan(prompt, transition, dialogue)
    ending = _ending_decision(prompt, intent, pragmatic, comprehension, referent)
    initiative = _initiative_decision(prompt, ending)
    speaker = _speaker_scope(prompt, payload.get("speaker_context"))
    return {
        "status": "pragmatic_continuity_plan_ready",
        "version": "v1_session_continuity_and_restraint",
        "topic_transition": transition,
        "referent_posture": referent,
        "interruption_plan": interruption,
        "ending_decision": ending,
        "initiative_decision": initiative,
        "speaker_scope": speaker,
        "active_correction": _active_correction(dialogue),
        "response_preference": dict(dialogue.get("preferences") or {}),
        "open_loop_ids": [
            str(item.get("id") or "")
            for item in dialogue.get("open_loops") or []
            if isinstance(item, dict) and str(item.get("id") or "")
        ],
        "session_scoped_only": True,
        "durable_relationship_inference": False,
        "unmarked_topic_change_is_certain": False,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": CONTINUITY_BOUNDARY,
        **GUARDS,
    }


def _topic_transition(prompt: str, dialogue: dict[str, Any]) -> dict[str, Any]:
    lower = " ".join(prompt.lower().split())
    active = str(dialogue.get("active_topic") or "")
    side_topics = [str(item) for item in dialogue.get("side_topics") or [] if str(item).strip()]
    return_match = re.search(r"\b(?:back|return|going back) to\s+(.+?)(?:[,.!?]|$)", lower)
    if return_match:
        target = truncate(return_match.group(1).strip(" ,"), 240)
        matched = next((item for item in [active, *reversed(side_topics)] if target in item.lower() or item.lower() in target), "")
        return {
            "kind": "explicit_return",
            "from_topic": active,
            "to_topic": matched or target,
            "resume_target": matched or target,
            "preserve_prior_topic": True,
            "confidence": "explicit",
        }
    if any(marker in lower for marker in ("by the way", "quick aside", "separately", "another thing")):
        return {
            "kind": "side_topic",
            "from_topic": active,
            "to_topic": _bounded_topic(prompt),
            "resume_target": active,
            "preserve_prior_topic": True,
            "confidence": "explicit",
        }
    if any(re.match(rf"^\s*{re.escape(marker)}\b", lower) for marker in ("wait", "hold on", "one second")):
        return {
            "kind": "interruption",
            "from_topic": active,
            "to_topic": active,
            "resume_target": active,
            "preserve_prior_topic": True,
            "confidence": "explicit",
        }
    if any(marker in lower for marker in ("never mind", "drop that", "leave that")):
        return {
            "kind": "explicit_abandon",
            "from_topic": active,
            "to_topic": "",
            "resume_target": "",
            "preserve_prior_topic": False,
            "confidence": "explicit",
        }
    if any(marker in lower for marker in ("anyway", "so,", "continuing", "from there")):
        return {
            "kind": "continuation_or_soft_pivot",
            "from_topic": active,
            "to_topic": _bounded_topic(prompt) or active,
            "resume_target": active,
            "preserve_prior_topic": True,
            "confidence": "bounded",
        }
    return {
        "kind": "unmarked_continuation_or_shift",
        "from_topic": active,
        "to_topic": _bounded_topic(prompt) or active,
        "resume_target": "",
        "preserve_prior_topic": bool(active),
        "confidence": "not_assumed",
    }


def _referent_posture(prompt: str, dialogue: dict[str, Any], pragmatic: dict[str, Any]) -> dict[str, Any]:
    reference = pragmatic.get("resolved_reference") if isinstance(pragmatic.get("resolved_reference"), dict) else None
    if reference:
        ambiguous = str(reference.get("resolution_status") or "") == "materially_ambiguous"
        return {
            "detected": True,
            "token": str(reference.get("token") or ""),
            "resolved_to": str(reference.get("resolved_to") or ""),
            "source": str(reference.get("source") or "immediate_session_context"),
            "confidence": "unresolved" if ambiguous else str(reference.get("confidence") or "bounded"),
            "materially_ambiguous": ambiguous,
            "ask_if_materially_ambiguous": ambiguous,
        }
    lower = prompt.lower()
    token_match = re.search(r"\b(it|this|that|they|them|those|he|she)\b", lower)
    if not token_match:
        return {"detected": False, "confidence": "not_needed", "materially_ambiguous": False}
    candidates = [str(item) for item in (dialogue.get("reference_candidates") or []) if str(item).strip()]
    if not candidates:
        candidates = [str(item.get("name") or "") for item in dialogue.get("entities") or [] if isinstance(item, dict) and str(item.get("name") or "")]
    token = token_match.group(1)
    if token in {"they", "them", "those"} and len(candidates) == 2:
        return {
            "detected": True,
            "token": token,
            "resolved_to": " and ".join(candidates),
            "source": "bounded_session_candidates",
            "confidence": "bounded",
            "materially_ambiguous": False,
            "ask_if_materially_ambiguous": False,
        }
    if len(candidates) == 1:
        return {
            "detected": True,
            "token": token,
            "resolved_to": candidates[0],
            "source": "single_bounded_session_candidate",
            "confidence": "bounded",
            "materially_ambiguous": False,
            "ask_if_materially_ambiguous": False,
        }
    return {
        "detected": True,
        "token": token,
        "resolved_to": "",
        "source": "",
        "confidence": "unresolved",
        "materially_ambiguous": len(candidates) > 1,
        "ask_if_materially_ambiguous": len(candidates) > 1,
        "candidate_count": len(candidates),
    }


def _interruption_plan(prompt: str, transition: dict[str, Any], dialogue: dict[str, Any]) -> dict[str, Any]:
    kind = str(transition.get("kind") or "")
    if kind == "interruption":
        action = "pause_and_listen_without_closing_prior_topic"
    elif kind == "explicit_return":
        action = "resume_named_topic_from_last_clear_session_point"
    elif kind == "explicit_abandon":
        action = "release_current_topic_without_erasing_session_history"
    else:
        action = "continue_without_forced_transition_narration"
    return {
        "detected": kind in {"interruption", "explicit_return", "explicit_abandon"},
        "action": action,
        "prior_open_loops_preserved": kind != "explicit_abandon",
        "open_loop_count": len([item for item in dialogue.get("open_loops") or [] if isinstance(item, dict)]),
        "automatic_loop_deletion": False,
    }


def _ending_decision(
    prompt: str,
    intent: dict[str, Any],
    pragmatic: dict[str, Any],
    comprehension: dict[str, Any],
    referent: dict[str, Any],
) -> dict[str, Any]:
    handshake = comprehension.get("handshake") if isinstance(comprehension.get("handshake"), dict) else {}
    ambiguity = pragmatic.get("ambiguity") if isinstance(pragmatic.get("ambiguity"), dict) else {}
    uncovered = [str(item) for item in pragmatic.get("uncovered_obligation_ids") or [] if str(item)]
    material_question = (
        referent.get("ask_if_materially_ambiguous") is True
        or str(ambiguity.get("level") or "") in {"material", "material_input_ambiguity"}
        or handshake.get("required") is True
    )
    intent_name = str(intent.get("intent") or "")
    if intent_name == "farewell":
        mode = "natural_close"
        question_allowed = False
        reason = "the user is closing the conversation"
    elif intent_name in {"greeting", "gratitude", "affirmation", "warm_connection", "reassurance_received"}:
        mode = "leave_room_without_pressuring"
        question_allowed = False
        reason = "a social turn does not require a habitual follow-up"
    elif material_question:
        mode = "ask_one_material_question"
        question_allowed = True
        reason = "a consequential ambiguity cannot be resolved from bounded session context"
    elif uncovered:
        mode = "leave_missing_content_visible_without_padding"
        question_allowed = False
        reason = "content is incomplete, but no user detail is known to resolve the domain gap"
    else:
        mode = "answer_and_stop_when_complete"
        question_allowed = False
        reason = "no material missing detail requires a question"
    return {
        "mode": mode,
        "question_allowed": question_allowed,
        "question_required": material_question and question_allowed,
        "reason": reason,
        "habitual_follow_up_allowed": False,
        "silence_or_completion_is_valid": True,
    }


def _initiative_decision(prompt: str, ending: dict[str, Any]) -> dict[str, Any]:
    lower = prompt.lower()
    invited = any(
        phrase in lower
        for phrase in (
            "what do you think",
            "any ideas",
            "anything else",
            "what would you add",
            "your take",
            "do you have a thought",
        )
    )
    return {
        "explicitly_invited": invited,
        "mode": "offer_one_relevant_thought" if invited else "no_unsolicited_initiative",
        "automatic_delivery": False,
        "question_pressure_allowed": False,
        "respect_ending": str(ending.get("mode") or "") == "natural_close",
    }


def _speaker_scope(prompt: str, supplied: Any) -> dict[str, Any]:
    if isinstance(supplied, dict) and str(supplied.get("speaker") or ""):
        return {
            "speaker": truncate(str(supplied.get("speaker") or ""), 80),
            "source": "explicit_payload",
            "inferred_relationship_profile": False,
        }
    lower = prompt.lower()
    if "this is codex" in lower:
        speaker, source = "Codex", "explicit_current_turn"
    elif any(phrase in lower for phrase in ("this is aleks", "it is aleks", "it's aleks")):
        speaker, source = "Aleks", "explicit_current_turn"
    else:
        speaker, source = "session_user", "not_individually_inferred"
    return {"speaker": speaker, "source": source, "inferred_relationship_profile": False}


def _active_correction(dialogue: dict[str, Any]) -> dict[str, Any]:
    corrections = [item for item in dialogue.get("corrections") or [] if isinstance(item, dict)]
    latest = corrections[-1] if corrections else {}
    return {
        "available": bool(latest),
        "corrected_meaning": str(latest.get("corrected_meaning") or ""),
        "replaced_meaning": str(latest.get("replaced_meaning") or ""),
        "scope": "current_session_refinement_only" if latest else "not_available",
        "durable_memory_write": False,
    }


def _bounded_topic(prompt: str) -> str:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", prompt.lower())
    stop = {
        "about", "again", "and", "anyway", "back", "can", "could", "from", "going", "how", "into", "let",
        "please", "return", "that", "the", "this", "what", "with", "would", "you", "your",
    }
    return " ".join(word for word in words if word not in stop)[:240]
