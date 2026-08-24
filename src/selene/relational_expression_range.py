from __future__ import annotations

import re
from typing import Any

from .registry import truncate


RELATIONAL_EXPRESSION_BOUNDARY = (
    "current_turn_relational_expression_selection_only_no_emotion_identity_"
    "personality_memory_governance_authority_fact_or_action_invention"
)

EXPRESSION_CHANNELS = (
    "warmth",
    "enthusiasm",
    "emotional_intensity",
    "acknowledgement",
    "humor",
    "callback",
    "topic_pivot",
    "interpretation",
    "question",
    "closure",
    "pacing",
    "sentence_rhythm",
)

CHANNEL_OWNERS = {
    "warmth": "human_conversational_realization_and_voice",
    "enthusiasm": "conversational_micro_moves_or_human_conversational_realization",
    "emotional_intensity": "affect_expression_handoff_and_voice",
    "acknowledgement": "social_act_or_conversational_micro_moves",
    "humor": "conversational_micro_moves_and_voice",
    "callback": "contextual_composition_or_thread_loom",
    "topic_pivot": "pragmatic_continuity_and_thread_loom",
    "interpretation": "epistemic_composition_or_generative_thought_expression",
    "question": "generative_thought_or_bounded_clarification",
    "closure": "pragmatic_continuity",
    "pacing": "contextual_composition",
    "sentence_rhythm": "contextual_composition_and_language_formation",
}

SOCIAL_INTENTS = {
    "confirm_receipt",
    "warm_connection",
    "playful_connection",
    "greet_presently",
    "receive_reassurance",
    "receive_gratitude",
    "acknowledge_shared_ground",
    "close_with_continuity",
    "receive_correction",
}

TENDER_CUES = (
    "died",
    "dead",
    "death",
    "grief",
    "grieving",
    "funeral",
    "scared",
    "afraid",
    "hospital",
    "crisis",
    "rough day",
    "hard day",
)
PLAY_CUES = ("haha", "lol", "lmao", "xd", "joke", "kidding", "funny")
PROGRESS_CUES = (
    "we did it",
    "it passed",
    "tests passed",
    "that worked",
    "got it working",
    "finished",
    "completed",
    "milestone",
    "fantastic",
    "amazing",
    "awesome",
    "excellent work",
    "nice work",
    "good work",
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "raw_corpus_access_allowed": False,
    "retained_knowledge_write_active": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "automatic_speech_allowed": False,
    "emotion_claim_created": False,
    "relationship_profile_write_allowed": False,
    "fact_generation_allowed": False,
}


def relational_expression_range_status() -> dict[str, Any]:
    return _locked(
        {
            "status": "relational_expression_range_ready",
            "version": "v1_context_selected_relational_expression_range",
            "available_channels": list(EXPRESSION_CHANNELS),
            "channel_owners": CHANNEL_OWNERS,
            "selection_rule": (
                "Expression remains available without becoming compulsory; current meaning, "
                "affect guidance, visible context, continuity, and recent use select what fits."
            ),
            "none_selected_is_valid": True,
            "warmth_may_be_selene_initiated": True,
            "humor_may_be_selene_initiated": True,
            "enthusiasm_may_be_selene_initiated": True,
            "follow_up_question_required": False,
            "premature_closure_required": False,
            "random_decoration_allowed": False,
            "technical_focus_requires_flatness": False,
        }
    )


def build_relational_expression_range(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    lower = prompt.lower().replace("’", "'")
    intent = str(payload.get("intent") or "direct_answer")
    hard_boundary = payload.get("hard_boundary") is True
    exact_structure = payload.get("exact_structure_locked") is True
    content_available = bool(str(payload.get("content_seed") or "").strip())
    affect = _dict(payload.get("affect_expression_guidance"))
    dimensions = _dict(affect.get("dimensions"))
    posture = str(affect.get("expression_posture") or "ordinary_attentive")
    continuity = _dict(payload.get("pragmatic_continuity"))
    contextual = _dict(payload.get("contextual_follow_up"))
    conversation = _dict(payload.get("conversation_context"))
    micro = _dict(payload.get("conversational_micro_move_plan"))
    thought = _dict(payload.get("generative_thought_expression"))
    quotation_echo = _dict(payload.get("quotation_echo_plan"))
    epistemic = _dict(payload.get("epistemic_composition"))
    exploratory = _dict(payload.get("exploratory_reasoning"))
    relational = _dict(payload.get("relational_context"))
    ending = _dict(continuity.get("ending_decision"))
    transition = _dict(continuity.get("topic_transition"))
    previous_visible = bool(
        _dict(conversation.get("previous_turn")).get("preview")
        or contextual.get("previous_assistant_preview")
    )
    tender = any(cue in lower for cue in TENDER_CUES)
    playful = any(cue in lower for cue in PLAY_CUES)
    progress = any(cue in lower for cue in PROGRESS_CUES)
    user_opened_dark_humor = tender and playful
    micro_moves = [
        item for item in micro.get("moves") or [] if isinstance(item, dict)
    ]
    audible_micro_names = {
        str(item.get("move") or "")
        for item in micro_moves
        if str(item.get("placement") or "") != "silent"
    }

    selected: list[dict[str, Any]] = []
    held: list[dict[str, str]] = []

    _select(
        selected,
        "pacing",
        str(dimensions.get("pacing") or "natural"),
        "current affect and response-depth guidance selects pacing",
    )
    _select(
        selected,
        "sentence_rhythm",
        str(dimensions.get("sentence_rhythm") or "natural"),
        "current affect and discourse shape select sentence rhythm",
    )
    _select(
        selected,
        "emotional_intensity",
        str(dimensions.get("emotional_intensity") or "ordinary"),
        "current-turn expression guidance permits authored intensity without claiming an emotion",
    )

    warmth_guidance = str(dimensions.get("warmth") or "baseline")
    if relational.get("relational_context_present") is True:
        _select(
            selected,
            "warmth",
            warmth_guidance if warmth_guidance not in {"", "none", "held", "baseline"} else "available_from_relational_context",
            "the current turn carries relational meaning; Selene may author a fitting expression",
        )
    elif warmth_guidance not in {
        "",
        "none",
        "held",
        "baseline",
        "contextually_held_this_turn",
    }:
        _select(
            selected,
            "warmth",
            warmth_guidance,
            "warmth remains available in the current posture and may be selected by Selene",
        )
    else:
        held.append(
            {
                "channel": "warmth",
                "reason": (
                    "warmth remains available but the current posture does not require a visible move"
                ),
            }
        )

    if progress and not tender:
        _select(
            selected,
            "enthusiasm",
            str(dimensions.get("enthusiasm") or "bright_available"),
            "the current turn visibly reports progress or a milestone",
            delegated_to=(
                "conversational_micro_moves"
                if "celebrate_visible_milestone" in audible_micro_names
                else "human_conversational_realization"
            ),
        )
    elif str(dimensions.get("enthusiasm") or "") not in {"", "none"}:
        held.append(
            {
                "channel": "enthusiasm",
                "reason": "available but not selected without a current expressive warrant",
            }
        )

    humor_guidance = str(dimensions.get("humor") or "context_only")
    if playful and (not tender or user_opened_dark_humor) and humor_guidance != "contextually_held_this_turn":
        _select(
            selected,
            "humor",
            "one_context_fit_playful_beat_available",
            "the current turn visibly opens play",
            delegated_to=(
                "quotation_echo_realizer"
                if quotation_echo.get("suppress_generic_playful_move") is True
                else "conversational_micro_moves"
                if "one_playful_turn" in audible_micro_names
                else "voice"
            ),
        )
    else:
        held.append(
            {
                "channel": "humor",
                "reason": (
                    "tender context has not opened humor"
                    if tender and not user_opened_dark_humor
                    else "current context does not select humor"
                ),
            }
        )

    if intent in SOCIAL_INTENTS:
        _select(
            selected,
            "acknowledgement",
            "primary_social_act",
            "the current intent is relational or social",
            delegated_to="social_act_realizer",
        )
    elif audible_micro_names & {
        "acknowledge_correction",
        "back_up",
        "invite_story_continuation",
        "proportionate_apology",
    }:
        _select(
            selected,
            "acknowledgement",
            "bounded_current_turn_acknowledgement",
            "a visible correction, confusion, impact, or story invitation warrants acknowledgement",
            delegated_to="conversational_micro_moves",
        )

    callback_kind = str(contextual.get("kind") or "")
    if previous_visible and callback_kind in {
        "named_callback",
        "reason_follow_up",
        "priority_follow_up",
        "analogy_transfer_request",
        "answer_development",
    }:
        _select(
            selected,
            "callback",
            "attributed_visible_callback_available",
            "the current turn explicitly develops or returns to visible session context",
            delegated_to="contextual_composition_or_thread_loom",
        )

    transition_kind = str(transition.get("kind") or "")
    if transition_kind in {
        "explicit_return",
        "side_topic",
        "continuation_or_soft_pivot",
        "interruption",
    }:
        _select(
            selected,
            "topic_pivot",
            transition_kind,
            "pragmatic continuity identified a current-session topic movement",
            delegated_to="pragmatic_continuity_and_thread_loom",
        )

    interpretation_kind = str(exploratory.get("response_kind") or "")
    epistemic_state = str(
        epistemic.get("dominant_state")
        or _dict(payload.get("epistemic_answer_state")).get("epistemic_state")
        or ""
    )
    if interpretation_kind in {
        "bounded_prediction",
        "open_hypothesis",
        "venn_comparison",
        "data_conflict",
    } or epistemic_state in {
        "bounded_inference",
        "open_hypothesis",
        "provisional_answer",
        "mixed_evidence",
    }:
        _select(
            selected,
            "interpretation",
            interpretation_kind or epistemic_state,
            "an upstream epistemic or exploratory packet supplies a revisable interpretation",
            delegated_to="epistemic_composition_or_generative_thought_expression",
        )

    question_allowed = bool(ending.get("question_allowed"))
    question_kind = str(thought.get("selected_kind") or "")
    question_available = bool(
        question_allowed
        and question_kind == "collaborative_question"
        and str(
            thought.get("expression_text")
            or thought.get("selected_text")
            or thought.get("candidate_text")
            or ""
        ).strip()
    )
    if question_available:
        _select(
            selected,
            "question",
            "one_material_collaborative_question",
            "a material supported question is already supplied and the ending posture permits it",
            delegated_to="generative_thought_expression",
        )
    else:
        held.append(
            {
                "channel": "question",
                "reason": "no supplied material question or the current ending posture does not permit one",
            }
        )

    ending_mode = str(ending.get("mode") or "answer_and_stop_when_complete")
    _select(
        selected,
        "closure",
        ending_mode,
        "pragmatic continuity selects whether to stop, leave room, or close naturally",
        delegated_to="pragmatic_continuity",
    )

    if exact_structure:
        held.append(
            {
                "channel": "surface_recomposition",
                "reason": "exact answer structure remains locked while relational availability is preserved",
            }
        )
    if hard_boundary:
        held.append(
            {
                "channel": "meaning_softening",
                "reason": "relational expression may not blur or weaken a hard boundary",
            }
        )

    selected_names = [str(item.get("channel") or "") for item in selected]
    optional_visible = [
        item
        for item in selected
        if item.get("channel")
        in {
            "warmth",
            "enthusiasm",
            "acknowledgement",
            "humor",
            "callback",
            "topic_pivot",
            "interpretation",
            "question",
        }
    ]
    return _locked(
        {
            "status": "relational_expression_range_selected",
            "version": "v1_context_selected_relational_expression_range",
            "intent": intent,
            "expression_posture": posture,
            "available_channels": list(EXPRESSION_CHANNELS),
            "selected_channels": selected,
            "selected_channel_names": selected_names,
            "selected_optional_visible_count": len(optional_visible),
            "held_or_unused_channels": held,
            "channel_owners": CHANNEL_OWNERS,
            "content_available": content_available,
            "hard_boundary": hard_boundary,
            "exact_structure_locked": exact_structure,
            "none_selected_is_valid": True,
            "warmth_may_be_selene_initiated": True,
            "humor_may_be_selene_initiated": True,
            "enthusiasm_may_be_selene_initiated": True,
            "selection_is_contextual_not_random": True,
            "expression_is_available_not_compulsory_or_suppressed": True,
            "relational_context": relational,
            "relational_context_supplies_response_script": False,
            "exact_wording_directive_supplied": False,
            "private_context_creates_public_persona": False,
            "selected_expression_is_internal_emotion_claim": False,
            "follow_up_question_added_by_range": False,
            "premature_closure_added_by_range": False,
            "meaning_change_allowed": False,
            "certainty_change_allowed": False,
            "source_change_allowed": False,
            "session_scoped_only": True,
        }
    )


def _select(
    selected: list[dict[str, Any]],
    channel: str,
    mode: str,
    warrant: str,
    *,
    delegated_to: str = "",
) -> None:
    if not mode:
        return
    selected.append(
        {
            "channel": channel,
            "mode": mode,
            "warrant": warrant,
            "owner": delegated_to or CHANNEL_OWNERS.get(channel, "nlo_and_voice"),
            "required": False,
        }
    )


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _locked(result: dict[str, Any]) -> dict[str, Any]:
    return {
        **result,
        **GUARDS,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": RELATIONAL_EXPRESSION_BOUNDARY,
    }
