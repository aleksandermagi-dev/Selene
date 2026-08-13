from __future__ import annotations

import re
from typing import Any

from .registry import truncate


CONTEXTUAL_COMPOSITION_BOUNDARY = (
    "supported_expression_structure_only_no_fact_certainty_source_memory_identity_"
    "personality_authority_or_voice_ownership_change"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "automatic_speech_allowed": False,
}

_SOCIAL_INTENTS = {
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

_EXACT_DOMAINS = {"verified_math", "source_backed_research"}


def build_contextual_composition_plan(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or ""), 2400)
    intent = str(payload.get("intent") or "direct_answer")
    depth = _depth(payload.get("response_depth"))
    profile = str(payload.get("expression_profile") or "direct")
    domain = str(payload.get("answer_domain") or "ordinary_conversation")
    discourse = (
        payload.get("supported_discourse")
        if isinstance(payload.get("supported_discourse"), dict)
        else {}
    )
    continuity = (
        payload.get("pragmatic_continuity")
        if isinstance(payload.get("pragmatic_continuity"), dict)
        else {}
    )
    contextual = (
        payload.get("contextual_follow_up")
        if isinstance(payload.get("contextual_follow_up"), dict)
        else {}
    )
    conversation = (
        payload.get("conversation_context")
        if isinstance(payload.get("conversation_context"), dict)
        else {}
    )
    affect = (
        payload.get("affect_expression_guidance")
        if isinstance(payload.get("affect_expression_guidance"), dict)
        else {}
    )
    dimensions = affect.get("dimensions") if isinstance(affect.get("dimensions"), dict) else {}
    micro = (
        payload.get("conversational_micro_move_plan")
        if isinstance(payload.get("conversational_micro_move_plan"), dict)
        else {}
    )
    expression_range = (
        payload.get("relational_expression_range")
        if isinstance(payload.get("relational_expression_range"), dict)
        else {}
    )
    units = [item for item in discourse.get("content_units") or [] if isinstance(item, dict)]
    roles = [str(item.get("role") or "") for item in units]
    register = _register(prompt, profile, domain)
    audience = _audience(prompt)
    exact_structure = domain in _EXACT_DOMAINS
    social_structure = intent in _SOCIAL_INTENTS
    supported_unit_count = len(units)
    developed_limited = depth == "developed" and supported_unit_count < 2
    named_callback = str(contextual.get("kind") or "") in {
        "named_callback",
        "reason_follow_up",
        "priority_follow_up",
        "analogy_transfer_request",
    }
    prior_visible = bool(
        (conversation.get("previous_turn") or {}).get("preview")
        or contextual.get("previous_assistant_preview")
    )
    transition = (
        continuity.get("topic_transition")
        if isinstance(continuity.get("topic_transition"), dict)
        else {}
    )
    transition_kind = str(transition.get("kind") or "")
    ending = (
        continuity.get("ending_decision")
        if isinstance(continuity.get("ending_decision"), dict)
        else {}
    )
    audible_micro_moves = int(micro.get("audible_move_count") or 0)

    opening = (
        "exact_domain_answer"
        if exact_structure
        else "social_act"
        if social_structure
        else "micro_move_then_thesis"
        if audible_micro_moves
        else "answer_first"
        if depth == "brief"
        else "callback_into_thesis"
        if named_callback and prior_visible
        else "thesis_first"
    )
    support_mode = (
        "all_required_only"
        if depth == "brief"
        else "thesis_plus_bounded_support"
        if depth == "standard"
        else "thesis_support_example_and_qualification"
    )
    example_mode = (
        "include_if_explicitly_requested_and_supported"
        if depth == "brief"
        else "include_if_supported"
    )
    qualification_mode = (
        "preserve_concisely"
        if depth == "brief"
        else "separate_when_material"
        if any(role in {"limitation", "reopening", "assumption"} for role in roles)
        else "not_needed"
    )
    callback_mode = (
        "carry_attributed_visible_callback"
        if named_callback and prior_visible
        else "omit_callback"
    )
    pivot_mode = (
        "resume_named_thread"
        if transition_kind == "explicit_return"
        else "silent_soft_pivot"
        if transition_kind in {"side_topic", "continuation_or_soft_pivot"}
        else "no_pivot_marker"
    )
    conclusion_mode = str((discourse.get("closure_plan") or {}).get("mode") or "stop_after_supported_content")
    stopping_mode = str(ending.get("mode") or "answer_and_stop_when_complete")
    rhythm = str(dimensions.get("sentence_rhythm") or _default_rhythm(depth))
    pacing = str(dimensions.get("pacing") or _default_pacing(depth))
    enthusiasm = str(dimensions.get("enthusiasm") or _enthusiasm(prompt, dimensions))
    emotional_intensity = str(
        dimensions.get("emotional_intensity") or _emotional_intensity(prompt, dimensions)
    )
    sentence_distribution = {
        "brief": {"target_words_per_sentence": [6, 20], "paragraph_shape": "one_compact_block"},
        "standard": {"target_words_per_sentence": [8, 26], "paragraph_shape": "one_or_two_balanced_blocks"},
        "developed": {"target_words_per_sentence": [7, 30], "paragraph_shape": "thesis_development_qualification"},
    }[depth]

    return {
        "status": "contextual_composition_plan_ready",
        "version": "v1_supported_contextual_composition",
        "response_depth": depth,
        "expression_profile": profile,
        "answer_domain": domain,
        "task_kind": _task_kind(profile, prompt),
        "audience": audience,
        "register": register,
        "task_bound_register": register != "ordinary_conversation",
        "pacing": pacing,
        "sentence_rhythm": rhythm,
        "enthusiasm": enthusiasm,
        "emotional_intensity": emotional_intensity,
        "relational_expression_range": {
            "status": str(expression_range.get("status") or "not_available"),
            "selected_channel_names": expression_range.get("selected_channel_names") or [],
            "selected_optional_visible_count": int(
                expression_range.get("selected_optional_visible_count") or 0
            ),
            "none_selected_is_valid": expression_range.get("none_selected_is_valid") is True,
            "expression_is_available_not_compulsory_or_suppressed": (
                expression_range.get(
                    "expression_is_available_not_compulsory_or_suppressed"
                )
                is True
            ),
        },
        "directness": str(dimensions.get("directness") or "ordinary"),
        "restraint": str(dimensions.get("restraint") or "ordinary"),
        "sentence_distribution": sentence_distribution,
        "decisions": {
            "opening": opening,
            "thesis": "preserve_supported_thesis_first",
            "support": support_mode,
            "example": example_mode,
            "qualification": qualification_mode,
            "callback": callback_mode,
            "pivot": pivot_mode,
            "conclusion": conclusion_mode,
            "stopping": stopping_mode,
        },
        "supported_content_unit_ids": [
            str(item.get("id") or "") for item in units if str(item.get("id") or "")
        ],
        "supported_content_roles": roles,
        "supported_content_unit_count": supported_unit_count,
        "developed_depth_limited_by_supported_content": developed_limited,
        "content_recomposition_allowed": not exact_structure and not social_structure,
        "exact_domain_structure_locked": exact_structure,
        "social_act_structure_owned_elsewhere": social_structure,
        "callback_requires_visible_attribution": True,
        "enthusiasm_is_optional_expression_not_emotion_claim": True,
        "emotional_intensity_may_change_facts": False,
        "register_may_change_identity_or_personality": False,
        "meaning_change_allowed": False,
        "certainty_change_allowed": False,
        "source_change_allowed": False,
        "filler_generation_allowed": False,
        "unsupported_example_generation_allowed": False,
        "follow_up_question_added": False,
        "coordinated_expression_contract_active": True,
        "session_scoped_only": True,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": CONTEXTUAL_COMPOSITION_BOUNDARY,
        **GUARDS,
    }


def apply_contextual_composition(
    text: str,
    plan: dict[str, Any] | None,
) -> dict[str, Any]:
    source = _normalize_paragraphs(str(text or ""))
    plan = plan if isinstance(plan, dict) else {}
    if not source:
        return _result(source, source, plan, applied=False, reason="no_supported_text")
    if plan.get("content_recomposition_allowed") is not True:
        return _result(
            source,
            source,
            plan,
            applied=False,
            reason=(
                "exact_domain_structure_locked"
                if plan.get("exact_domain_structure_locked") is True
                else "structure_owned_by_specialized_expression_layer"
            ),
        )

    depth = _depth(plan.get("response_depth"))
    rhythm = str(plan.get("sentence_rhythm") or _default_rhythm(depth))
    candidate = source
    operations: list[str] = []

    if depth == "brief":
        compact = _compact(source)
        if compact != candidate:
            candidate = compact
            operations.append("compact_brief_structure")
    elif depth == "developed":
        developed = _develop(candidate, plan)
        if developed != candidate:
            candidate = developed
            operations.append("develop_supported_paragraph_structure")
    else:
        standard = _standard(candidate, plan)
        if standard != candidate:
            candidate = standard
            operations.append("balance_standard_structure")

    paced = _pace(candidate, rhythm, depth)
    if paced != candidate:
        candidate = paced
        operations.append(f"apply_{rhythm}_rhythm")

    return _result(
        source,
        candidate,
        plan,
        applied=bool(operations),
        reason="supported_structure_modulated" if operations else "source_already_fit_profile",
        operations=operations,
    )


def _result(
    source: str,
    candidate: str,
    plan: dict[str, Any],
    *,
    applied: bool,
    reason: str,
    operations: list[str] | None = None,
) -> dict[str, Any]:
    before = _tokens(source)
    after = _tokens(candidate)
    return {
        "status": "contextual_composition_applied" if applied else "contextual_composition_preserved",
        "candidate_text": candidate,
        "applied": applied,
        "reason": reason,
        "operations": operations or [],
        "response_depth": str(plan.get("response_depth") or "standard"),
        "register": str(plan.get("register") or "ordinary_conversation"),
        "pacing": str(plan.get("pacing") or "natural"),
        "sentence_rhythm": str(plan.get("sentence_rhythm") or "natural"),
        "source_token_count": len(before),
        "candidate_token_count": len(after),
        "same_supported_tokens": before == after,
        "meaning_preserved": before == after,
        "certainty_changed": False,
        "sources_changed": False,
        "facts_added": False,
        "filler_added": False,
        "follow_up_question_added": False,
        "coordinated_expression_contract_active": True,
        "provenance_boundary": CONTEXTUAL_COMPOSITION_BOUNDARY,
        **GUARDS,
    }


def _compact(value: str) -> str:
    paragraphs = [item.strip() for item in value.split("\n\n") if item.strip()]
    joined = " ".join(paragraphs)
    sentences = _sentences(joined)
    if 2 <= len(sentences) <= 3 and sum(len(item.split()) for item in sentences) <= 50:
        if not any(item.endswith(("?", "!")) for item in sentences[:-1]):
            parts = [sentences[0].rstrip(". ")]
            for sentence in sentences[1:-1]:
                lowered = sentence[0].lower() + sentence[1:] if sentence else sentence
                parts.append(lowered.rstrip(". "))
            last = sentences[-1].strip()
            lowered_last = last[0].lower() + last[1:] if last else last
            parts.append(lowered_last)
            return "; ".join(parts)
    return joined


def _standard(value: str, plan: dict[str, Any]) -> str:
    if "\n\n" in value:
        return value
    sentences = _sentences(value)
    material_qualification = str((plan.get("decisions") or {}).get("qualification") or "") == "separate_when_material"
    if material_qualification and len(sentences) >= 3:
        return f"{' '.join(sentences[:-1])}\n\n{sentences[-1]}"
    return value


def _develop(value: str, plan: dict[str, Any]) -> str:
    if "\n\n" in value:
        return value
    sentences = _sentences(value)
    if len(sentences) < 2:
        return value
    if plan.get("developed_depth_limited_by_supported_content") is True:
        return value
    if len(sentences) == 2:
        return "\n\n".join(sentences)
    qualification = str((plan.get("decisions") or {}).get("qualification") or "")
    if qualification == "separate_when_material":
        return f"{sentences[0]}\n\n{' '.join(sentences[1:-1])}\n\n{sentences[-1]}"
    midpoint = max(1, len(sentences) // 2)
    return f"{' '.join(sentences[:midpoint])}\n\n{' '.join(sentences[midpoint:])}"


def _pace(value: str, rhythm: str, depth: str) -> str:
    if rhythm == "compact" and depth == "brief":
        return " ".join(item.strip() for item in value.split("\n\n") if item.strip())
    if rhythm not in {"spacious", "short_spacious", "varied"} or "\n\n" in value:
        return value
    sentences = _sentences(value)
    if len(sentences) < 2:
        return value
    if rhythm in {"spacious", "short_spacious"}:
        return f"{sentences[0]}\n\n{' '.join(sentences[1:])}"
    if rhythm == "varied" and len(sentences) >= 3:
        return f"{sentences[0]}\n\n{' '.join(sentences[1:3])}" + (
            f"\n\n{' '.join(sentences[3:])}" if len(sentences) > 3 else ""
        )
    return value


def _register(prompt: str, profile: str, domain: str) -> str:
    lower = prompt.lower()
    if any(cue in lower for cue in ("lab report", "formal report", "academic essay", "formal email")):
        return "formal_task_bound"
    if any(cue in lower for cue in ("for a child", "for a beginner", "plain language", "simply")):
        return "plain_explanatory"
    if domain in _EXACT_DOMAINS or profile in {"procedure", "comparison", "synthesis"} or any(
        cue in lower for cue in ("technical", "implementation", "architecture", "calculate", "evidence")
    ):
        return "technical_precise"
    if any(cue in lower for cue in ("story", "narrative", "scene")):
        return "narrative"
    if any(cue in lower for cue in ("reflect", "tender", "gently")):
        return "reflective_conversational"
    return "ordinary_conversation"


def _audience(prompt: str) -> dict[str, Any]:
    lower = prompt.lower()
    candidates = (
        ("child", ("for a child", "for a kid")),
        ("beginner", ("for a beginner", "new to this")),
        ("technical_peer", ("for an engineer", "technical audience", "for a developer")),
        ("formal_reader", ("for a judge", "formal report", "academic audience")),
    )
    for audience, cues in candidates:
        if any(cue in lower for cue in cues):
            return {
                "kind": audience,
                "source": "explicit_current_task",
                "durable_profile_created": False,
            }
    return {
        "kind": "current_conversation",
        "source": "no_special_audience_assumed",
        "durable_profile_created": False,
    }


def _task_kind(profile: str, prompt: str) -> str:
    lower = prompt.lower()
    if any(cue in lower for cue in ("summarize", "recap", "sum up")):
        return "summary"
    if any(cue in lower for cue in ("story", "narrative", "scene")):
        return "story"
    return {
        "comparison": "comparison",
        "procedure": "walkthrough",
        "reflection": "reflection",
        "synthesis": "synthesis",
        "explanation": "explanation",
    }.get(profile, "direct_conversation")


def _enthusiasm(prompt: str, dimensions: dict[str, Any]) -> str:
    lower = prompt.lower()
    humor = str(dimensions.get("humor") or "")
    if any(cue in lower for cue in ("we did it", "amazing", "awesome", "fantastic", "excited")):
        return "bright_available"
    if humor == "available_not_required":
        return "lively_available"
    return "ordinary"


def _emotional_intensity(prompt: str, dimensions: dict[str, Any]) -> str:
    lower = prompt.lower()
    if any(cue in lower for cue in ("grief", "died", "death", "scared", "crisis")):
        return "gentle_contained"
    if str(dimensions.get("pacing") or "") == "lively":
        return "lively"
    return "ordinary"


def _default_rhythm(depth: str) -> str:
    return {"brief": "compact", "developed": "varied"}.get(depth, "natural")


def _default_pacing(depth: str) -> str:
    return {"brief": "brisk", "developed": "measured"}.get(depth, "natural")


def _depth(value: Any) -> str:
    normalized = str(value or "standard").lower()
    return normalized if normalized in {"brief", "standard", "developed"} else "standard"


def _sentences(value: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+", " ".join(value.split()))
        if item.strip()
    ]


def _normalize_paragraphs(value: str) -> str:
    return "\n\n".join(
        " ".join(item.split())
        for item in re.split(r"\n\s*\n", value.strip())
        if item.strip()
    )


def _tokens(value: str) -> list[str]:
    return re.findall(r"[^\W_]+(?:['’][^\W_]+)?", value.lower(), flags=re.UNICODE)
