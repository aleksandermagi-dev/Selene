from __future__ import annotations

import re
from typing import Any

from .registry import truncate
from .supported_semantics import semantic_units_for_formation
from .whole_answer_composition import compose_whole_answer


EPISTEMIC_COMPOSITION_BOUNDARY = (
    "current_answer_epistemic_part_composition_only_no_fact_invention_memory_"
    "identity_personality_governance_training_authority_or_action_change"
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
    "expression_authority": False,
}

_PREDICTION_CUES = (
    "predict", "prediction", "forecast", "likely", "expect", "what might happen",
    "what could happen", "best estimate",
)

_HYPOTHESIS_CUES = (
    "hypothesis", "hypothesize", "possible explanation", "might explain",
    "could explain", "working model",
)


def epistemic_composition_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "epistemic_composition_ready",
            "version": "v1_obligation_bound_mixed_epistemic_answer",
            "part_states": [
                "supported_answer",
                "supported_inference",
                "bounded_prediction",
                "open_hypothesis",
                "labeled_speculation",
                "reviewed_experience_recall",
                "missing_ground",
            ],
            "exploratory_reasoning_may_supply_complete_primary_part": True,
            "known_part_may_survive_unknown_neighbor": True,
            "unknown_part_may_not_downgrade_supported_part": True,
            "prediction_requires_future_fact": False,
            "hypothesis_requires_prior_proof": False,
            "composition_changes_supported_meaning": False,
            "visible_summary_only": True,
            "provenance_boundary": EPISTEMIC_COMPOSITION_BOUNDARY,
        }
    )


def compose_epistemic_answer(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Bind each requested part to its own epistemic state and support.

    The composer does not create answer facts. It preserves already selected
    content, orders completion fragments by their response obligation, and
    keeps an unsupported part local instead of turning the whole answer into
    a generic refusal.
    """

    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or ""), 3000)
    content_seed = _truncate_preserving_paragraphs(
        str(payload.get("content_seed") or ""), 5000
    )
    obligations = [
        item for item in payload.get("response_obligations") or []
        if isinstance(item, dict)
    ][:20]
    completion = (
        payload.get("answer_completion")
        if isinstance(payload.get("answer_completion"), dict)
        else {}
    )
    semantics = (
        payload.get("supported_semantics")
        if isinstance(payload.get("supported_semantics"), dict)
        else completion.get("supported_semantics")
        if isinstance(completion.get("supported_semantics"), dict)
        else {}
    )
    hypothesis = (
        payload.get("bounded_hypothesis")
        if isinstance(payload.get("bounded_hypothesis"), dict)
        else {}
    )
    source_id = str(payload.get("source_id") or "none")
    source_class = str(payload.get("source_class") or "conversation")
    hard_boundary = payload.get("hard_boundary") is True
    exploratory = (
        payload.get("exploratory_reasoning")
        if isinstance(payload.get("exploratory_reasoning"), dict)
        else {}
    )
    answer_operations = (
        payload.get("answer_operations")
        if isinstance(payload.get("answer_operations"), dict)
        else {}
    )
    operation_results = [
        item
        for item in answer_operations.get("results") or []
        if isinstance(item, dict)
        and str(item.get("obligation_id") or "")
    ]
    completed_operations = [
        item for item in operation_results if item.get("status") == "completed"
    ]
    operation_by_id = {
        str(item.get("obligation_id") or ""): item
        for item in completed_operations
    }
    whole_answer = compose_whole_answer(
        {
            "prompt": prompt,
            "content_seed": content_seed,
            "response_obligations": obligations,
            "answer_operations": answer_operations,
        }
    )
    whole_answer_applied = whole_answer.get("applied") is True
    if whole_answer_applied:
        content_seed = _truncate_preserving_paragraphs(
            str(whole_answer.get("content_seed") or content_seed),
            5000,
        )
        whole_semantics = (
            whole_answer.get("supported_semantics")
            if isinstance(whole_answer.get("supported_semantics"), dict)
            else {}
        )
        if semantic_units_for_formation(whole_semantics):
            semantics = whole_semantics
    if (
        exploratory.get("selected_for_answer") is True
        and content_seed
        and not hard_boundary
        and not whole_answer_applied
    ):
        return _exploratory_primary_composition(
            content_seed,
            exploratory=exploratory,
            source_id=source_id,
            source_class=source_class,
        )
    resolutions = [
        item for item in completion.get("resolutions") or []
        if isinstance(item, dict)
    ]
    resolution_by_id = {
        str(item.get("obligation_id") or ""): item
        for item in resolutions
        if str(item.get("obligation_id") or "")
    }
    semantic_units = semantic_units_for_formation(semantics)
    initial_coverage = (
        completion.get("initial_coverage")
        if isinstance(completion.get("initial_coverage"), dict)
        else {}
    )
    final_coverage = (
        completion.get("final_coverage")
        if isinstance(completion.get("final_coverage"), dict)
        else {}
    )
    coverage_items = [
        item for item in final_coverage.get("items") or initial_coverage.get("items") or []
        if isinstance(item, dict)
    ]
    coverage_by_id = {
        str(item.get("obligation_id") or ""): item
        for item in coverage_items
        if str(item.get("obligation_id") or "")
    }
    supplied_parts = [
        item for item in payload.get("part_candidates") or []
        if isinstance(item, dict)
    ]
    supplied_by_id = {
        str(item.get("obligation_id") or ""): item
        for item in supplied_parts
        if str(item.get("obligation_id") or "")
    }

    parts: list[dict[str, Any]] = []
    composed_fragments: list[str] = []
    for order, obligation in enumerate(obligations):
        obligation_id = str(obligation.get("id") or f"part-{order + 1}")
        resolution = resolution_by_id.get(obligation_id, {})
        supplied = supplied_by_id.get(obligation_id, {})
        operation_result = operation_by_id.get(obligation_id, {})
        units = [
            unit for unit in semantic_units
            if obligation_id in {
                str(item) for item in unit.get("obligation_ids") or [] if str(item)
            }
        ]
        visible_text = _truncate_preserving_paragraphs(
            str(
                supplied.get("text")
                or resolution.get("visible_fragment")
                or resolution.get("fragment")
                or operation_result.get("expression_seed")
                or _unit_text(units)
                or ""
            ),
            1800,
        )
        coverage = coverage_by_id.get(obligation_id, {})
        unsupported = bool(
            operation_result.get("status") != "completed"
            and (
                supplied.get("unsupported") is True
                or resolution.get("unsupported") is True
                or resolution.get("missing_ground")
            )
        )
        addressed = bool(
            operation_result.get("status") == "completed" and visible_text
            or
            supplied.get("addressed") is True
            or resolution.get("added_to_answer") is True
            or units
            or coverage.get("addressed") is True
        )
        part_source_class = str(
            supplied.get("source_class")
            or ("typed_operation_result" if operation_result else "")
            or resolution.get("source_class")
            or source_class
        )
        part_source_id = str(
            operation_result.get("expression_source_id")
            or source_id
        )
        state = str(supplied.get("epistemic_state") or "") or _part_state(
            prompt=prompt,
            obligation=obligation,
            text=visible_text or content_seed,
            source_id=part_source_id,
            source_class=part_source_class,
            resolution=resolution,
            unsupported=unsupported or not addressed,
            selected_hypothesis=(
                hypothesis.get("offered") is True
                and hypothesis.get("selected_for_answer") is True
            ),
        )
        missing_ground = str(
            supplied.get("missing_ground")
            or resolution.get("missing_ground")
            or ("support for this requested part" if state == "missing_ground" else "")
        )
        source_refs = _unique_text(
            [
                *[str(item) for item in supplied.get("source_refs") or []],
                *[str(item) for item in resolution.get("source_refs") or []],
                *[str(item) for item in operation_result.get("source_refs") or []],
                *[
                    str(ref)
                    for unit in units
                    for ref in unit.get("source_refs") or []
                ],
            ]
        )
        part = {
            "part_id": f"epistemic-{obligation_id}",
            "order": order,
            "obligation_id": obligation_id,
            "requested_kind": str(obligation.get("kind") or "direct_question"),
            "request_text": truncate(str(obligation.get("source_text") or ""), 700),
            "epistemic_state": state,
            "certainty": _certainty_for_state(state),
            "text": visible_text,
            "addressed": addressed,
            "unsupported": state == "missing_ground",
            "missing_ground": missing_ground,
            "source_id": part_source_id,
            "source_class": part_source_class,
            "source_refs": source_refs,
            "visible_label_required": state in {
                "bounded_prediction", "open_hypothesis", "labeled_speculation"
            },
            "visible_label_present": _visible_label_present(state, visible_text or content_seed),
            "unknown_neighbor_changes_this_part": False,
            "typed_operation_result_used": bool(operation_result),
            "typed_operation": str(operation_result.get("operation") or ""),
        }
        parts.append(part)
        if visible_text and not whole_answer_applied:
            composed_fragments.append(visible_text)

    if not parts and content_seed:
        state = _part_state(
            prompt=prompt,
            obligation={},
            text=content_seed,
            source_id=source_id,
            source_class=source_class,
            resolution={},
            unsupported=False,
            selected_hypothesis=(
                hypothesis.get("offered") is True
                and hypothesis.get("selected_for_answer") is True
            ),
        )
        parts.append(
            {
                "part_id": "epistemic-primary-answer",
                "order": 0,
                "obligation_id": "",
                "requested_kind": "direct_answer",
                "request_text": prompt,
                "epistemic_state": state,
                "certainty": _certainty_for_state(state),
                "text": content_seed,
                "addressed": True,
                "unsupported": False,
                "missing_ground": "",
                "source_id": source_id,
                "source_class": source_class,
                "source_refs": [],
                "visible_label_required": state in {
                    "bounded_prediction", "open_hypothesis", "labeled_speculation"
                },
                "visible_label_present": _visible_label_present(state, content_seed),
                "unknown_neighbor_changes_this_part": False,
            }
        )

    states = list(dict.fromkeys(str(item.get("epistemic_state") or "") for item in parts))
    supported_states = {
        "supported_answer", "supported_inference", "bounded_prediction",
        "open_hypothesis", "labeled_speculation", "reviewed_experience_recall",
    }
    supported_count = sum(1 for item in parts if item.get("epistemic_state") in supported_states)
    missing_count = sum(1 for item in parts if item.get("epistemic_state") == "missing_ground")
    unlabeled_count = sum(
        1 for item in parts
        if item.get("visible_label_required") is True
        and item.get("visible_label_present") is not True
    )
    composed_seed = (
        content_seed
        if whole_answer_applied
        else _preserve_and_append(content_seed, composed_fragments)
    )
    dominant_state = (
        "hard_boundary"
        if hard_boundary
        else "partial_answer"
        if supported_count and missing_count
        else states[0]
        if len(states) == 1
        else "mixed_epistemic_answer"
        if states
        else "missing_ground"
    )
    result = {
        "status": "epistemic_answer_composed",
        "version": "v1_obligation_bound_mixed_epistemic_answer",
        "content_seed": composed_seed,
        "parts": parts,
        "part_count": len(parts),
        "supported_part_count": supported_count,
        "missing_part_count": missing_count,
        "epistemic_states_present": states,
        "dominant_state": dominant_state,
        "mixed_epistemic_answer": len(states) > 1,
        "known_part_preserved_with_missing_part": bool(supported_count and missing_count),
        "unknown_part_downgraded_supported_part": False,
        "single_typed_operation_expression_used": (
            len(completed_operations) == 1 and not whole_answer_applied
        ),
        "whole_answer_composition": whole_answer,
        "whole_answer_composition_applied": whole_answer_applied,
        "multi_operation_composition_deferred": (
            len(operation_results) > 1 and not whole_answer_applied
        ),
        "supported_semantics": semantics,
        "composition_order": [str(item.get("obligation_id") or "") for item in parts],
        "unlabeled_exploratory_part_count": unlabeled_count,
        "release_ready": unlabeled_count == 0,
        "composition_changes_supported_meaning": False,
        "composition_invents_missing_content": False,
        "writes_state": False,
        "visible_summary_only": True,
        "provenance_boundary": EPISTEMIC_COMPOSITION_BOUNDARY,
    }
    return _with_guards(result)


def _exploratory_primary_composition(
    content_seed: str,
    *,
    exploratory: dict[str, Any],
    source_id: str,
    source_class: str,
) -> dict[str, Any]:
    response_kind = str(exploratory.get("response_kind") or "")
    state = {
        "bounded_prediction": "bounded_prediction",
        "open_hypothesis": "open_hypothesis",
        "venn_comparison": "supported_inference",
        "data_conflict": "supported_inference",
    }.get(response_kind, "supported_inference")
    part = {
        "part_id": "epistemic-exploratory-primary",
        "order": 0,
        "obligation_id": "",
        "requested_kind": response_kind or "exploratory_answer",
        "request_text": "",
        "epistemic_state": state,
        "certainty": (
            "unresolved_claim_level_conflict"
            if response_kind == "data_conflict"
            else _certainty_for_state(state)
        ),
        "text": content_seed,
        "addressed": True,
        "unsupported": False,
        "missing_ground": "",
        "source_id": source_id,
        "source_class": source_class,
        "source_refs": _unique_text(
            [str(item) for item in exploratory.get("source_refs") or []]
        ),
        "visible_label_required": state in {
            "bounded_prediction",
            "open_hypothesis",
            "labeled_speculation",
        },
        "visible_label_present": _visible_label_present(state, content_seed),
        "unknown_neighbor_changes_this_part": False,
    }
    return _with_guards(
        {
            "status": "epistemic_answer_composed",
            "version": "v1_obligation_bound_mixed_epistemic_answer",
            "content_seed": content_seed,
            "parts": [part],
            "part_count": 1,
            "supported_part_count": 1,
            "missing_part_count": 0,
            "epistemic_states_present": [state],
            "dominant_state": state,
            "mixed_epistemic_answer": False,
            "known_part_preserved_with_missing_part": False,
            "unknown_part_downgraded_supported_part": False,
            "composition_order": ["exploratory-primary"],
            "unlabeled_exploratory_part_count": (
                0 if part["visible_label_present"] is True else 1
            ),
            "release_ready": part["visible_label_present"] is True,
            "exploratory_reasoning_primary_part_preserved": True,
            "composition_changes_supported_meaning": False,
            "composition_invents_missing_content": False,
            "writes_state": False,
            "visible_summary_only": True,
            "provenance_boundary": EPISTEMIC_COMPOSITION_BOUNDARY,
        }
    )


def _part_state(
    *,
    prompt: str,
    obligation: dict[str, Any],
    text: str,
    source_id: str,
    source_class: str,
    resolution: dict[str, Any],
    unsupported: bool,
    selected_hypothesis: bool,
) -> str:
    if unsupported:
        return "missing_ground"
    request_scope = str(obligation.get("source_text") or "").strip() or prompt
    combined = " ".join(
        [
            request_scope,
            str(obligation.get("kind") or ""),
            text,
        ]
    ).lower()
    kind = str(obligation.get("kind") or "").lower()
    if selected_hypothesis or kind == "hypothesis" or any(cue in combined for cue in _HYPOTHESIS_CUES):
        return "open_hypothesis"
    if kind == "prediction" or any(cue in combined for cue in _PREDICTION_CUES):
        return "bounded_prediction"
    if "speculat" in combined:
        return "labeled_speculation"
    if source_class == "memory_reconstruction" or source_id in {
        "reviewed_memory", "contextual_approved_memory", "local_chat_continuity"
    }:
        return "reviewed_experience_recall"
    support_kind = str(resolution.get("resolution") or "")
    if source_class in {"approved_knowledge", "domain_answer"} or support_kind in {
        "current_session_fact", "approved_central_claim", "approved_reason_or_relationship",
        "approved_limit_or_counterexample", "approved_distinct_example", "approved_change_condition",
    }:
        return "supported_answer"
    return "supported_inference"


def _certainty_for_state(state: str) -> str:
    return {
        "supported_answer": "supported",
        "supported_inference": "provisional_from_supported_premises",
        "bounded_prediction": "bounded_basis_not_outcome_certainty",
        "open_hypothesis": "revisable_explanatory_candidate",
        "labeled_speculation": "low_certainty_explicit",
        "reviewed_experience_recall": "reviewed_personal_scope",
        "missing_ground": "not_available",
    }.get(state, "not_assessed")


def _visible_label_present(state: str, text: str) -> bool:
    lower = " ".join(text.lower().split())
    if state == "bounded_prediction":
        return any(marker in lower for marker in ("predict", "likely", "expect", "best estimate", "may", "might"))
    if state == "open_hypothesis":
        return any(marker in lower for marker in ("hypothesis", "working model", "might explain", "could explain", "possible explanation"))
    if state == "labeled_speculation":
        return "speculat" in lower or "wild possibility" in lower
    return True


def _unit_text(units: list[dict[str, Any]]) -> str:
    return " ".join(
        str(item.get("text") or "").strip()
        for item in units
        if str(item.get("text") or "").strip()
    )


def _preserve_and_append(seed: str, fragments: list[str]) -> str:
    result = seed
    normalized = " ".join(seed.lower().split())
    for fragment in fragments:
        key = " ".join(fragment.lower().split()).rstrip(". ")
        if not key or key in normalized:
            continue
        result = f"{result}\n\n{fragment}" if result else fragment
        normalized = " ".join(result.lower().split())
    return _truncate_preserving_paragraphs(result, 5000)


def _truncate_preserving_paragraphs(value: str, limit: int) -> str:
    paragraphs = [
        " ".join(part.split())
        for part in re.split(r"\n\s*\n", str(value or "").strip())
        if part.strip()
    ]
    text = "\n\n".join(paragraphs)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _unique_text(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))[:40]


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
