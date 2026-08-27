from selene.answer_completion import build_bounded_answer_completion
from selene.epistemic_composition import compose_epistemic_answer
from selene.metacognition import evaluate_metacognition
from selene.owner_specific_retry import attempt_owner_specific_retry
from selene.pragmatic_planner import evaluate_response_coverage
from selene.selene_chat import _metacognitive_owner_outputs
from selene.semantic_fulfillment import (
    build_semantic_fulfillment_packet,
    evaluate_operation_fulfillment,
    semantic_fulfillment_status,
)


def _obligation(
    operation: str,
    *,
    obligation_id: str = "operation-1",
    kind: str | None = None,
    requested_count: int = 0,
) -> dict:
    aliases = {
        "causal_explanation": "reason",
        "choice": "choice",
        "summary": "session_summary",
    }
    return {
        "id": obligation_id,
        "kind": kind or aliases.get(operation, operation),
        "required": True,
        "responsible_owner": "intelligence_os",
        "requested_response_functions": [aliases.get(operation, operation)],
        "requested_count": requested_count,
        "source_text": f"Please perform the {operation} operation.",
        "coverage_terms": [operation],
    }


def _result(
    obligation: dict,
    operation: str,
    fields: dict,
    *,
    status: str = "completed",
    expression_seed: str = "",
    missing_input: str = "",
) -> dict:
    return {
        "obligation_id": obligation["id"],
        "operation": operation,
        "responsible_owner": obligation["responsible_owner"],
        "status": status,
        "fields": fields,
        "expression_seed": expression_seed,
        "missing_input": missing_input,
        "generic_prose_used_as_completion": False,
    }


def _packet(result: dict) -> dict:
    return {"status": "answer_operations_complete", "results": [result]}


def test_status_declares_ids_and_missing_statements_are_not_answers() -> None:
    status = semantic_fulfillment_status()

    assert status["obligation_ids_are_proof"] is False
    assert status["generic_missing_statement_is_answer"] is False
    assert status["visible_realization_required"] is True
    assert status["memory_write_active"] is False
    assert status["identity_change"] is False
    assert status["expression_authority"] is False


def test_declared_id_and_generic_comparison_prose_do_not_prove_performance() -> None:
    obligation = _obligation("comparison")
    result = _result(
        obligation,
        "comparison",
        {
            "candidates": ["the porch", "the walk"],
            "findings": {
                "shared": ["both are available this afternoon"],
                "only_left": ["the porch stays near home"],
                "only_right": ["the walk provides movement"],
            },
            "comparison_basis": "the same visible options",
        },
    )

    receipt = evaluate_operation_fulfillment(
        obligation,
        "I can compare those options.",
        result,
    )

    assert receipt["fulfilled"] is False
    assert receipt["declared_obligation_id_accepted_as_proof"] is False
    assert receipt["generic_prose_accepted_as_performance"] is False


def test_visible_comparison_must_realize_candidates_and_findings() -> None:
    obligation = _obligation("comparison")
    result = _result(
        obligation,
        "comparison",
        {
            "candidates": ["the porch", "the walk"],
            "findings": {
                "shared": ["both are available this afternoon"],
                "only_left": ["the porch stays near home"],
                "only_right": ["the walk provides movement"],
            },
            "comparison_basis": "the same visible options",
        },
    )
    candidate = (
        "The porch and the walk are both available this afternoon. "
        "The porch stays near home, while the walk provides movement."
    )

    receipt = evaluate_operation_fulfillment(obligation, candidate, result)

    assert receipt["fulfilled"] is True
    assert receipt["visible_semantics_performed"] is True
    assert receipt["owner_fit"] is True


def test_requested_method_count_is_part_of_fulfillment_truth() -> None:
    obligation = _obligation("method", requested_count=2)
    result = _result(
        obligation,
        "method",
        {
            "steps": ["inspect the current state", "compare the result with the goal"],
            "basis": "the current task",
            "limitations": ["the method stays within the supplied workspace"],
        },
    )

    short = evaluate_operation_fulfillment(
        obligation,
        "First, inspect the current state.",
        result,
    )
    complete = evaluate_operation_fulfillment(
        obligation,
        "First, inspect the current state. Second, compare the result with the goal.",
        result,
    )

    assert short["fulfilled"] is False
    assert short["performed_count"] == 1
    assert short["count_fit"] is False
    assert complete["fulfilled"] is True
    assert complete["performed_count"] == 2


def test_explicit_order_and_brevity_constraints_are_verified_separately() -> None:
    obligation = _obligation("method", requested_count=2)
    obligation["response_shape"] = {
        "explicit": True,
        "requested_count": 2,
        "counted_unit": "step",
        "ordered": True,
        "brevity": "short",
    }
    result = _result(
        obligation,
        "method",
        {
            "steps": ["inspect the current state", "compare the result with the goal"],
            "basis": "the current task",
            "limitations": ["the method stays within the supplied workspace"],
        },
    )

    unordered = evaluate_operation_fulfillment(
        obligation,
        "Inspect the current state. Compare the result with the goal.",
        result,
    )
    ordered = evaluate_operation_fulfillment(
        obligation,
        "First, inspect the current state. Second, compare the result with the goal.",
        result,
    )

    assert unordered["visible_semantics_performed"] is True
    assert unordered["constraint_fit"] is False
    assert unordered["fulfilled"] is False
    assert ordered["response_shape_receipt"]["ordered_present"] is True
    assert ordered["response_shape_receipt"]["brevity_fit"] is True
    assert ordered["fulfilled"] is True


def test_precise_missing_input_can_resolve_release_without_becoming_answer() -> None:
    obligation = _obligation("comparison")
    result = _result(
        obligation,
        "comparison",
        {},
        status="missing_input",
        missing_input="two supported candidates and one shared comparison basis",
    )
    candidate = (
        "I don't have enough information to compare them yet. "
        "I would need the two candidates and a shared comparison basis."
    )
    coverage = evaluate_response_coverage(
        {"response_obligations": [obligation]},
        candidate,
        answer_operations=_packet(result),
    )

    item = coverage["items"][0]
    assert item["addressed"] is False
    assert item["resolved_for_release"] is True
    assert item["resolution_state"] == "supported_route"
    assert coverage["all_required_addressed"] is False
    assert coverage["all_required_resolved"] is True
    assert coverage["missing_ground_statements_are_answers"] is False


def test_heuristic_coverage_cannot_override_typed_fulfillment_failure() -> None:
    obligation = _obligation("causal_explanation", kind="reason")
    obligation["coverage_terms"] = ["fractions", "calculus", "reason"]
    result = _result(
        obligation,
        "causal_explanation",
        {
            "conclusion": "fractions should come before calculus",
            "mechanism_or_reason": "calculus depends on fractional relationships",
            "basis": "current prompt",
        },
    )
    coverage = evaluate_response_coverage(
        {"response_obligations": [obligation]},
        "The reason concerns fractions and calculus.",
        answer_operations=_packet(result),
    )

    item = coverage["items"][0]
    assert item["heuristic_addressed_before_typed_fulfillment"] is True
    assert item["addressed"] is False
    assert coverage["all_required_addressed"] is False


def test_bounded_completion_does_not_replace_typed_owner_with_generic_prose() -> None:
    obligation = _obligation("method")
    result = _result(
        obligation,
        "method",
        {},
        status="missing_input",
        missing_input="the intended outcome and controlling constraints",
    )

    completion = build_bounded_answer_completion(
        {
            "prompt": "How should we do this?",
            "content_seed": "",
            "response_obligations": [obligation],
            "answer_operations": _packet(result),
        }
    )

    assert completion["accepted"] is False
    assert completion["content_seed"] == ""
    assert completion["resolutions"][0]["resolution"] == (
        "held_for_typed_operation_visible_fulfillment"
    )
    assert completion["resolutions"][0]["generic_fallback_generated"] is False


def test_metacognition_receives_exact_unfulfilled_operation_and_alternate_path() -> None:
    fulfillment = {
        "operation": "comparison",
        "operation_result_state": "completed",
        "unresolved_reason": "the visible answer does not realize the comparison findings",
        "productive_alternate_path": {
            "responsible_owner": "intelligence_os",
            "operation": "comparison",
            "required_visible_fields": ["findings"],
            "use_existing_current_turn_owner_output_only": True,
        },
    }
    result = evaluate_metacognition(
        {
            "prompt": "Compare the porch and the walk.",
            "candidate_text": "I can compare them.",
            "answer_operations": {"results": [{"operation": "comparison"}]},
            "response_coverage": {
                "addressed_count": 0,
                "unresolved_count": 1,
                "items": [
                    {
                        "obligation_id": "operation-1",
                        "kind": "comparison",
                        "responsible_owner": "intelligence_os",
                        "addressed": False,
                        "semantic_fulfillment": fulfillment,
                    }
                ],
            },
        }
    )

    handoff = result["feedback_handoff"]
    assert result["recommended_action"] == "complete_missing_obligation"
    assert handoff["target_obligation_id"] == "operation-1"
    assert handoff["target_operation"] == "comparison"
    assert handoff["target_missing_state"] == "typed_operation_not_visibly_fulfilled"
    assert handoff["target_required_visible_fields"] == ["findings"]
    assert handoff["single_cycle_requested"] is True


def test_one_bounded_retry_can_use_exact_current_turn_operation_output() -> None:
    obligation = _obligation("preference")
    result = _result(
        obligation,
        "preference",
        {
            "authored_preference": "I would like to hear what has your attention lately",
            "basis": "current_authored_preference",
            "current_only": True,
        },
        expression_seed="I'd like to hear what has your attention lately.",
    )
    feedback = {
        "responsible_owner": "intelligence_os",
        "target_obligation_id": obligation["id"],
        "target_missing_state": "typed_operation_not_visibly_fulfilled",
    }
    outputs = _metacognitive_owner_outputs(
        organ_coalition={},
        answer_operations=_packet(result),
        answer_engine_support={},
        comprehension={},
        intelligence_support={},
        memory_response_seed="",
        conversation_content_seed="",
        feedback_handoff=feedback,
    )
    retry = attempt_owner_specific_retry(
        "I don't have enough support to answer that.",
        {"unresolved_count": 1},
        requested=True,
        hard_boundary=False,
        feedback_handoff=feedback,
        owner_outputs=outputs,
    )

    assert retry["attempted"] is True
    assert retry["count"] == 1
    assert retry["source"] == "existing_exact_owner_current_turn_output"
    assert "what has your attention lately" in retry["selected_fragment"].lower()
    assert retry["content_generation_allowed"] is False


def test_packet_summarizes_visible_fulfillment_without_new_authority() -> None:
    obligation = _obligation("preference")
    result = _result(
        obligation,
        "preference",
        {
            "authored_preference": "I would like to keep working on the conversation spine",
            "basis": "current_authored_preference",
            "current_only": True,
        },
    )
    packet = build_semantic_fulfillment_packet(
        {
            "response_obligations": [obligation],
            "candidate_text": "I would like to keep working on the conversation spine.",
            "answer_operations": _packet(result),
        }
    )

    assert packet["status"] == "semantic_fulfillment_complete"
    assert packet["all_operations_visibly_fulfilled"] is True
    assert packet["authority_change"] is False
    assert packet["expression_authority"] is False


def test_single_typed_operation_seed_reaches_epistemic_composition() -> None:
    obligation = _obligation("preference")
    result = _result(
        obligation,
        "preference",
        {
            "authored_preference": "I would like to hear what has your attention lately",
            "basis": "current_authored_preference",
            "current_only": True,
        },
        expression_seed="I'd like to hear what has your attention lately.",
    )
    composition = compose_epistemic_answer(
        {
            "prompt": obligation["source_text"],
            "content_seed": "",
            "response_obligations": [obligation],
            "answer_operations": _packet(result),
            "answer_completion": {
                "resolutions": [
                    {
                        "obligation_id": obligation["id"],
                        "resolution": "held_for_typed_operation_visible_fulfillment",
                        "source_class": "typed_answer_owner",
                    }
                ]
            },
        }
    )

    assert composition["content_seed"] == "I'd like to hear what has your attention lately."
    assert composition["parts"][0]["addressed"] is True
    assert composition["parts"][0]["typed_operation_result_used"] is True
    assert composition["missing_part_count"] == 0
    assert composition["single_typed_operation_expression_used"] is True


def test_multi_operation_results_reach_whole_answer_composition() -> None:
    first = _obligation("comparison", obligation_id="compare")
    second = _obligation("choice", obligation_id="choose")
    compare_result = _result(
        first,
        "comparison",
        {
            "candidates": ["porch", "walk"],
            "findings": ["the porch stays near home", "the walk provides movement"],
            "comparison_basis": "current options",
        },
        expression_seed="The porch stays near home, while the walk provides movement.",
    )
    choice_result = _result(
        second,
        "choice",
        {
            "selected_option": "the walk",
            "criteria": ["provides movement"],
            "revision_conditions": ["the weather changes"],
        },
        expression_seed="I would choose the walk because it provides movement.",
    )
    composition = compose_epistemic_answer(
        {
            "prompt": "Compare the porch and walk, then choose one.",
            "content_seed": "",
            "response_obligations": [first, second],
            "answer_operations": {"results": [compare_result, choice_result]},
        }
    )

    assert composition["single_typed_operation_expression_used"] is False
    assert composition["whole_answer_composition_applied"] is True
    assert composition["multi_operation_composition_deferred"] is False
    assert composition["content_seed"] == (
        "The porch stays near home, while the walk provides movement.\n\n"
        "I would choose the walk because it provides movement."
    )
    assert composition["composition_order"] == ["compare", "choose"]
