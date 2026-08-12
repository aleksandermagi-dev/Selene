from __future__ import annotations

import re
from typing import Any

from .registry import truncate


EPISTEMIC_ANSWER_STATE_BOUNDARY = (
    "typed_epistemic_and_missing_ground_coordination_only_no_fact_invention_"
    "memory_identity_personality_governance_training_authority_or_action_change"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "raw_a_import_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "hidden_chain_of_thought_exposed": False,
}

_PREDICTION_CUES = (
    "predict",
    "prediction",
    "likely",
    "expect",
    "best read",
    "best estimate",
    "what might happen",
    "what could happen",
)

_SPECULATION_CUES = ("speculate", "speculation", "wild possibility")

_CURRENT_INFORMATION_CUES = (
    "current",
    "right now",
    "today",
    "tomorrow",
    "latest",
    "live",
    "exact sunrise",
    "exact rainfall",
    "forecast",
)

_SOURCE_CUES = (
    "cite",
    "citation",
    "page number",
    "direct quotation",
    "exact quote",
    "research paper",
    "source",
)

_UNKNOWABLE_CUES = (
    "nobody copied",
    "nobody preserved",
    "not preserved",
    "lost final page",
    "cannot be recovered",
)

_FALLBACK_MARKERS = (
    "do not have enough grounded detail",
    "do not have a grounded factual answer",
    "cannot answer that part reliably",
    "cannot answer that with a reliable yes or no",
    "would need an attributed fact",
    "without guessing",
)


def epistemic_answer_state_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "epistemic_answer_state_contract_ready",
            "version": "v1_typed_epistemic_and_missing_ground_states",
            "epistemic_states": [
                "supported_answer",
                "supported_inference",
                "bounded_prediction",
                "open_hypothesis",
                "labeled_speculation",
                "reviewed_experience_recall",
                "partial_answer",
                "missing_ground",
                "conversational_response",
                "hard_boundary",
            ],
            "missing_ground_states": [
                "missing_taught_knowledge",
                "missing_visible_context",
                "missing_current_information",
                "missing_attributed_source",
                "missing_mechanism",
                "missing_decision_criteria",
                "missing_comparison_dimension",
                "missing_discriminating_evidence",
                "conflicting_evidence",
                "genuinely_unknowable",
                "missing_supported_basis",
            ],
            "confidence_dimensions": [
                "route_confidence",
                "evidence_confidence",
                "inference_confidence",
                "prediction_confidence",
                "answer_confidence",
                "memory_confidence",
                "expression_confidence",
            ],
            "fact_certainty_required_for_prediction": False,
            "fact_certainty_required_for_hypothesis": False,
            "reviewed_lived_experience_is_scoped_evidence": True,
            "epistemic_label_prescribes_tone": False,
            "human_conversational_presence_allowed": True,
            "review_status": "status_only",
            "provenance_boundary": EPISTEMIC_ANSWER_STATE_BOUNDARY,
        }
    )


def build_epistemic_answer_state(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 3000).strip()
    lower = _normalize(prompt)
    source_id = str(payload.get("source_id") or "none")
    source_class = str(payload.get("source_class") or "conversation")
    content_seed = truncate(str(payload.get("content_seed") or ""), 5000).strip()
    completion = _dict(payload.get("answer_completion"))
    composition = _dict(
        payload.get("epistemic_composition")
        or completion.get("epistemic_composition")
    )
    hypothesis = _dict(payload.get("bounded_hypothesis") or payload.get("hypothesis_attempt"))
    answer_engine = _dict(payload.get("answer_engine_support"))
    comprehension = _dict(payload.get("comprehension_context") or payload.get("comprehension"))
    memory = _dict(payload.get("memory_context") or payload.get("memory_retrieval"))
    hard_boundary = bool(payload.get("hard_boundary"))
    resolutions = [
        item for item in completion.get("resolutions") or [] if isinstance(item, dict)
    ]
    missing_parts = _composition_missing_parts(composition, prompt) or _missing_parts(
        prompt, resolutions, payload
    )
    supported_parts = _composition_supported_parts(composition) or _supported_parts(
        resolutions, payload
    )
    fallback_only = _fallback_only(content_seed)
    explicit_prediction = any(cue in lower for cue in _PREDICTION_CUES)
    explicit_speculation = any(cue in lower for cue in _SPECULATION_CUES)
    selected_hypothesis = (
        hypothesis.get("offered") is True
        and hypothesis.get("selected_for_answer") is True
    )
    reviewed_experience = source_id in {
        "reviewed_memory",
        "contextual_approved_memory",
        "local_chat_continuity",
    } or source_class == "memory_reconstruction"

    composition_state = str(composition.get("dominant_state") or "")
    if hard_boundary:
        epistemic_state = "hard_boundary"
    elif composition_state == "partial_answer":
        epistemic_state = "partial_answer"
    elif composition_state in {
        "supported_answer",
        "supported_inference",
        "bounded_prediction",
        "open_hypothesis",
        "labeled_speculation",
        "reviewed_experience_recall",
        "missing_ground",
    }:
        epistemic_state = composition_state
    elif selected_hypothesis:
        epistemic_state = "open_hypothesis"
    elif explicit_speculation and content_seed and not fallback_only:
        epistemic_state = "labeled_speculation"
    elif explicit_prediction and content_seed and not fallback_only:
        epistemic_state = "bounded_prediction"
    elif missing_parts and content_seed and not fallback_only:
        epistemic_state = "partial_answer"
    elif missing_parts or fallback_only:
        epistemic_state = "missing_ground"
    elif reviewed_experience:
        epistemic_state = "reviewed_experience_recall"
    elif source_class in {"approved_knowledge", "domain_answer"} or source_id in {
        "approved_comprehension",
        "answer_engine",
    }:
        epistemic_state = "supported_answer"
    elif source_class == "reasoning_answer" or source_id == "intelligence_os_answer":
        epistemic_state = "supported_inference"
    else:
        epistemic_state = "conversational_response"

    confidence = _confidence_vector(
        payload,
        epistemic_state=epistemic_state,
        answer_engine=answer_engine,
        comprehension=comprehension,
        memory=memory,
    )
    grounding_requirement = _grounding_requirement(epistemic_state)
    next_routes = list(
        dict.fromkeys(
            route
            for part in missing_parts
            for route in _next_routes(str(part.get("state") or ""))
        )
    )
    if epistemic_state in {"bounded_prediction", "open_hypothesis"}:
        next_routes.extend(
            route for route in ("state_assumptions", "name_reopening_condition")
            if route not in next_routes
        )

    result = {
        "status": "epistemic_answer_state_ready",
        "version": "v1_typed_epistemic_and_missing_ground_states",
        "prompt": prompt,
        "epistemic_state": epistemic_state,
        "grounding_requirement": grounding_requirement,
        "supported_parts": supported_parts,
        "missing_parts": missing_parts,
        "epistemic_parts": composition.get("parts") or [],
        "epistemic_composition": composition,
        "known_part_present": bool(supported_parts or (content_seed and not fallback_only)),
        "missing_part_present": bool(missing_parts),
        "partial_answer_allowed": True,
        "prediction_allowed_without_future_fact": True,
        "hypothesis_allowed_without_prior_proof": True,
        "speculation_requires_visible_label": True,
        "reviewed_lived_experience": {
            "available": reviewed_experience,
            "scope": "personal_experience_not_universal_fact" if reviewed_experience else "not_used",
            "may_support_prediction_or_hypothesis": reviewed_experience,
            "may_be_invented": False,
        },
        "confidence_vector": confidence,
        "next_route_candidates": next_routes,
        "source_id": source_id,
        "source_class": source_class,
        "content_seed_present": bool(content_seed),
        "fallback_only": fallback_only,
        "epistemic_label_prescribes_tone": False,
        "human_conversational_presence_allowed": True,
        "warmth_curiosity_humor_may_remain_natural": True,
        "voice_may_change_epistemic_state": False,
        "voice_may_upgrade_confidence": False,
        "unknown_part_downgraded_supported_part": False,
        "review_status": "status_only",
        "provenance_boundary": EPISTEMIC_ANSWER_STATE_BOUNDARY,
    }
    return _with_guards(result)


def _composition_missing_parts(
    composition: dict[str, Any], prompt: str
) -> list[dict[str, Any]]:
    lower = _normalize(prompt)
    result: list[dict[str, Any]] = []
    for item in composition.get("parts") or []:
        if not isinstance(item, dict) or item.get("epistemic_state") != "missing_ground":
            continue
        missing_ground = str(item.get("missing_ground") or "support for this requested part")
        state = _missing_state(missing_ground, lower, source_required=False)
        result.append(
            {
                "obligation_id": str(item.get("obligation_id") or ""),
                "requested_kind": str(item.get("requested_kind") or "direct_question"),
                "state": state,
                "missing_ground": missing_ground,
                "why_it_matters": _why_it_matters(state),
                "resolution": "epistemic_composition_missing_part",
            }
        )
    return result


def _composition_supported_parts(composition: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in composition.get("parts") or []:
        if not isinstance(item, dict) or item.get("epistemic_state") == "missing_ground":
            continue
        result.append(
            {
                "obligation_id": str(item.get("obligation_id") or ""),
                "requested_kind": str(item.get("requested_kind") or "direct_question"),
                "source_class": str(item.get("source_class") or ""),
                "concept_id": None,
                "resolution": str(item.get("epistemic_state") or "supported"),
                "epistemic_state": str(item.get("epistemic_state") or "supported_inference"),
                "certainty": str(item.get("certainty") or "not_assessed"),
            }
        )
    return result


def finalize_epistemic_answer_state(
    state: dict[str, Any] | None,
    *,
    response_coverage: dict[str, Any] | None = None,
    expression_confidence: str = "not_assessed",
) -> dict[str, Any]:
    result = dict(state or {})
    confidence = dict(result.get("confidence_vector") or {})
    coverage = response_coverage or {}
    confidence["answer_confidence"] = (
        "complete_for_requested_parts"
        if coverage.get("all_required_addressed") is True
        else "incomplete_for_requested_parts"
    )
    confidence["expression_confidence"] = expression_confidence or "not_assessed"
    confidence["dimensions_are_independent"] = True
    result.update(
        {
            "status": "epistemic_answer_state_finalized",
            "confidence_vector": confidence,
            "coverage_complete": coverage.get("all_required_addressed") is True,
            "coverage_unresolved_count": int(coverage.get("unresolved_count") or 0),
            "expression_confidence_is_truth_confidence": False,
        }
    )
    return _with_guards(result)


def _missing_parts(
    prompt: str,
    resolutions: list[dict[str, Any]],
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    parts: list[dict[str, Any]] = []
    lower = _normalize(prompt)
    for item in resolutions:
        unsupported = item.get("unsupported") is True or bool(item.get("missing_ground"))
        if not unsupported:
            continue
        missing_ground = str(item.get("missing_ground") or "").strip()
        state = _missing_state(
            missing_ground,
            lower,
            source_required=payload.get("source_required") is True,
        )
        parts.append(
            {
                "obligation_id": str(item.get("obligation_id") or ""),
                "requested_kind": str(item.get("kind") or "direct_question"),
                "state": state,
                "missing_ground": missing_ground or _state_description(state),
                "why_it_matters": _why_it_matters(state),
                "resolution": str(item.get("resolution") or "explicit_unsupported_part"),
            }
        )
    if parts:
        return parts
    coverage = _dict(payload.get("response_coverage"))
    if coverage.get("all_required_addressed") is False:
        for item in coverage.get("items") or []:
            if not isinstance(item, dict) or item.get("addressed") is True:
                continue
            state = _missing_state("", lower, source_required=False)
            parts.append(
                {
                    "obligation_id": str(item.get("obligation_id") or ""),
                    "requested_kind": str(item.get("kind") or "direct_question"),
                    "state": state,
                    "missing_ground": _state_description(state),
                    "why_it_matters": _why_it_matters(state),
                    "resolution": "coverage_still_open",
                }
            )
    return parts


def _supported_parts(
    resolutions: list[dict[str, Any]], payload: dict[str, Any]
) -> list[dict[str, Any]]:
    parts = []
    for item in resolutions:
        if item.get("unsupported") is True or item.get("added_to_answer") is False:
            continue
        parts.append(
            {
                "obligation_id": str(item.get("obligation_id") or ""),
                "requested_kind": str(item.get("kind") or "direct_question"),
                "source_class": str(item.get("source_class") or ""),
                "concept_id": item.get("concept_id"),
                "resolution": str(item.get("resolution") or "supported"),
            }
        )
    if parts:
        return parts
    semantics = _dict(payload.get("supported_semantics"))
    for unit in semantics.get("units") or []:
        if not isinstance(unit, dict) or unit.get("supported") is False:
            continue
        parts.append(
            {
                "obligation_id": str((unit.get("obligation_ids") or [""])[0]),
                "requested_kind": str(unit.get("role") or "answer"),
                "source_class": str(unit.get("source_kind") or ""),
                "concept_id": None,
                "resolution": "supported_semantic_unit",
            }
        )
    return parts


def _missing_state(
    missing_ground: str,
    lower_prompt: str,
    *,
    source_required: bool,
) -> str:
    ground = _normalize(missing_ground)
    if any(cue in lower_prompt for cue in _UNKNOWABLE_CUES):
        return "genuinely_unknowable"
    if source_required or any(cue in lower_prompt for cue in _SOURCE_CUES):
        return "missing_attributed_source"
    if any(cue in lower_prompt for cue in _CURRENT_INFORMATION_CUES):
        return "missing_current_information"
    if "mechanism" in ground or "explanatory relationship" in ground:
        return "missing_mechanism"
    if "deciding outcome" in ground or "constraints" in ground:
        return "missing_decision_criteria"
    if "comparison" in ground or "dimension" in ground:
        return "missing_comparison_dimension"
    if "distinguishes yes from no" in ground:
        return "missing_discriminating_evidence"
    if "relationship the analogy" in ground:
        return "missing_comparison_dimension"
    if "visible" in ground or "observation" in ground:
        return "missing_supported_basis"
    return "missing_supported_basis"


def _confidence_vector(
    payload: dict[str, Any],
    *,
    epistemic_state: str,
    answer_engine: dict[str, Any],
    comprehension: dict[str, Any],
    memory: dict[str, Any],
) -> dict[str, Any]:
    answer_packet = _dict(answer_engine.get("answer_packet"))
    approved_knowledge_source = (
        str(payload.get("source_class") or "") == "approved_knowledge"
        or str(payload.get("source_id") or "") == "approved_comprehension"
    )
    evidence_confidence = str(
        answer_packet.get("evidence_confidence")
        or comprehension.get("confidence")
        or (
            "reviewed"
            if epistemic_state == "supported_answer" or approved_knowledge_source
            else "not_assessed"
        )
    )
    prediction_confidence = (
        str(payload.get("prediction_confidence") or "bounded_basis_not_outcome_certainty")
        if epistemic_state == "bounded_prediction"
        else "not_applicable"
    )
    inference_confidence = (
        "provisional"
        if epistemic_state in {"supported_inference", "open_hypothesis", "labeled_speculation"}
        else "not_applicable"
    )
    return {
        "route_confidence": str(payload.get("route_confidence") or "not_assessed"),
        "evidence_confidence": evidence_confidence,
        "inference_confidence": inference_confidence,
        "prediction_confidence": prediction_confidence,
        "answer_confidence": "pre_expression_not_assessed",
        "memory_confidence": str(memory.get("memory_confidence") or "not_used"),
        "expression_confidence": "not_assessed",
        "dimensions_are_independent": True,
    }


def _grounding_requirement(epistemic_state: str) -> str:
    return {
        "supported_answer": "attributed_evidence_or_reviewed_knowledge",
        "supported_inference": "connected_visible_or_reviewed_premises",
        "bounded_prediction": "pattern_model_or_relevant_experience_with_conditions",
        "open_hypothesis": "basis_assumptions_and_reopening_condition",
        "labeled_speculation": "visible_low_certainty_label_and_no_fact_presentation",
        "reviewed_experience_recall": "reviewed_personal_scope_and_relevance",
        "partial_answer": "supported_known_parts_plus_typed_missing_parts",
        "missing_ground": "name_missing_ground_without_invention",
        "hard_boundary": "core_mind_boundary",
    }.get(epistemic_state, "current_conversation_fit")


def _next_routes(state: str) -> list[str]:
    return {
        "missing_taught_knowledge": ["seek_teaching_or_approved_knowledge"],
        "missing_visible_context": ["ask_one_material_question"],
        "missing_current_information": ["request_current_data_or_lookup"],
        "missing_attributed_source": ["seek_attributed_source"],
        "missing_mechanism": ["request_reasoning_or_hypothesis_owner"],
        "missing_decision_criteria": ["ask_for_goal_and_constraints"],
        "missing_comparison_dimension": ["ask_which_relationship_or_dimension_matters"],
        "missing_discriminating_evidence": ["seek_distinguishing_observation"],
        "conflicting_evidence": ["compare_sources_conditions_and_scope"],
        "genuinely_unknowable": ["state_unrecoverable_limit"],
        "missing_supported_basis": ["seek_relevant_knowledge_context_or_observation"],
    }.get(state, ["hold_for_relevant_ground"])


def _state_description(state: str) -> str:
    return state.replace("_", " ")


def _why_it_matters(state: str) -> str:
    return {
        "missing_current_information": "the answer changes with current time, place, or measurements",
        "missing_attributed_source": "the requested claim or quotation must remain traceable",
        "missing_mechanism": "a causal answer needs a relationship that connects cause and outcome",
        "missing_decision_criteria": "a choice depends on the goal and constraints",
        "missing_comparison_dimension": "a comparison needs a shared relation or dimension",
        "missing_discriminating_evidence": "the alternatives cannot yet be separated",
        "genuinely_unknowable": "the information is not available to recover",
        "missing_supported_basis": "the requested part lacks relevant support",
    }.get(state, "the open part needs support before it can be stated as known")


def _fallback_only(text: str) -> bool:
    lower = _normalize(text)
    if not lower:
        return False
    return any(marker in lower for marker in _FALLBACK_MARKERS)


def _normalize(value: str) -> str:
    return " ".join(value.lower().replace("’", "'").split())


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
