from __future__ import annotations

import re
from typing import Any

from .registry import truncate
from .supported_semantics import build_text_supported_semantic_packet


ANSWER_OPERATIONS_BOUNDARY = (
    "canonical_current_turn_obligation_operation_results_only_no_expression_memory_"
    "identity_personality_governance_authority_training_or_autonomous_action"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "expression_authority": False,
}

_OPERATION_ALIASES = {
    "method": "method",
    "action_scope": "method",
    "reason": "causal_explanation",
    "prediction": "prediction",
    "hypothesis": "hypothesis",
    "counterfactual": "counterfactual",
    "comparison": "comparison",
    "planning": "planning",
    "plan": "planning",
    "choice": "choice",
    "disagreement": "disagreement",
    "claim_evaluation": "disagreement",
    "correction": "correction",
    "reopening": "correction",
    "preference": "preference",
    "session_summary": "summary",
    "summary": "summary",
    "closure": "closure",
    "creative_expression": "creative_expression",
}

_CONTRACTS: dict[str, tuple[str, ...]] = {
    "method": ("steps", "basis", "limitations"),
    "causal_explanation": ("conclusion", "mechanism_or_reason", "basis"),
    "prediction": ("predicted_change", "basis", "revision_conditions"),
    "hypothesis": ("hypothesis", "basis", "revision_conditions"),
    "counterfactual": (
        "changed_premise",
        "preserved_premises",
        "consequence",
        "basis",
        "limits",
        "actual_state_restored",
    ),
    "comparison": ("candidates", "findings", "comparison_basis"),
    "planning": (
        "objective",
        "steps",
        "dependencies",
        "constraints",
        "fallback",
        "stopping_condition",
    ),
    "choice": ("selected_option", "criteria", "revision_conditions"),
    "disagreement": ("stance", "claim_evaluated", "premises"),
    "correction": ("corrected_input", "affected_result", "recompute_required"),
    "preference": ("authored_preference", "basis", "current_only"),
    "summary": ("points", "source_scope"),
    "closure": ("closure_intent", "source_scope"),
    "creative_expression": (
        "creative_brief",
        "fiction_status",
        "source_style_separation",
        "revision_lineage",
        "stopping_receipt",
    ),
}

_GENERIC_OR_MISSING_KINDS = {
    "unsupported_fact",
    "bounded_knowledge_gap",
    "source_needed",
    "causal_evidence_needed",
}


def answer_operations_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "answer_operation_coordination_ready",
            "version": "v1_typed_obligation_operation_results",
            "supported_operations": list(_CONTRACTS),
            "result_states": ["completed", "missing_input", "unsupported"],
            "epistemic_states": [
                "KNOWN_SUPPORTED",
                "CANDIDATE_UNVERIFIED",
                "UNKNOWN_INSUFFICIENT_EVIDENCE",
                "CONFLICT_UNSATISFIABLE",
                "WRONG_FALSIFIED",
                "RETRY_UPDATED_APPROACH",
                "FICTIONAL_INVENTION",
                "NO_FICTION_RELEASED",
            ],
            "generic_prose_may_complete_operation": False,
            "canonical_obligation_reparse_allowed": False,
            "current_turn_owner_input_receipt_required": True,
            "missing_input_may_repeat_supplied_current_turn_input": False,
            "review_status": "status_only",
            "provenance_boundary": ANSWER_OPERATIONS_BOUNDARY,
        }
    )


def build_answer_operation_packet(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Bind existing owner results to canonical response obligations.

    This coordinator does not reason in place of intelligenceOS, the Answer
    Engine, Comprehension, or ordinary conversation. It verifies that an owner
    actually returned the semantic fields required by the requested operation.
    """

    payload = payload or {}
    spine = _dict(payload.get("conversation_spine"))
    ledger = _dict(spine.get("obligation_ledger"))
    obligations = [
        item
        for item in (ledger.get("obligations") or spine.get("open_obligations") or [])
        if isinstance(item, dict) and item.get("required") is not False
    ][:24]
    hard_boundary = payload.get("hard_boundary") is True
    results: list[dict[str, Any]] = []
    for obligation in obligations:
        operation = _operation_for_obligation(obligation)
        if not operation:
            continue
        result = (
            _missing_result(
                obligation,
                operation,
                missing_input="the governing boundary must be resolved before this operation can run",
                reason="hard_boundary_precedes_answer_operation",
                status="unsupported",
            )
            if hard_boundary
            else _execute_operation(obligation, operation, payload)
        )
        result = _attach_current_turn_input_receipt(
            result,
            obligation=obligation,
            operation=operation,
            spine=spine,
            consumed=not hard_boundary,
        )
        results.append(result)

    completed = [item for item in results if item.get("status") == "completed"]
    missing = [item for item in results if item.get("status") == "missing_input"]
    unsupported = [item for item in results if item.get("status") == "unsupported"]
    required_ids = [str(item.get("obligation_id") or "") for item in results]
    completed_ids = [str(item.get("obligation_id") or "") for item in completed]
    source_ids = list(
        dict.fromkeys(
            str(item.get("expression_source_id") or "")
            for item in completed
            if str(item.get("expression_source_id") or "")
        )
    )
    semantic_packets = [
        item.get("supported_semantics")
        for item in completed
        if isinstance(item.get("supported_semantics"), dict)
        and item.get("supported_semantics")
    ]
    expression_seed = ""
    supported_semantics: dict[str, Any] = {}
    if len(completed) == 1:
        expression_seed = truncate(str(completed[0].get("expression_seed") or ""), 5000)
        supported_semantics = _dict(completed[0].get("supported_semantics"))

    return _with_guards(
        {
            "status": (
                "answer_operations_complete"
                if results and len(completed) == len(results)
                else "answer_operations_partially_complete"
                if completed
                else "answer_operations_need_input"
                if missing
                else "answer_operations_not_material"
                if not results
                else "answer_operations_unsupported"
            ),
            "version": "v1_typed_obligation_operation_results",
            "canonical_ledger_used": bool(ledger),
            "current_turn_fact_ledger_used": bool(
                _dict(spine.get("current_turn_fact_ledger"))
            ),
            "all_operation_inputs_accounted_for": bool(
                results
                and all(
                    _dict(item.get("current_turn_input_receipt")).get(
                        "accounted_before_result"
                    )
                    is True
                    for item in results
                )
            ),
            "canonical_obligation_reparse_allowed": False,
            "operation_count": len(results),
            "completed_count": len(completed),
            "missing_input_count": len(missing),
            "unsupported_count": len(unsupported),
            "required_obligation_ids": required_ids,
            "completed_obligation_ids": completed_ids,
            "all_supported_operations_complete": bool(results and len(completed) == len(results)),
            "results": results,
            "expression_handoff": {
                "available": bool(completed),
                "single_operation_seed_available": bool(expression_seed),
                "expression_seed": expression_seed,
                "source_ids": source_ids,
                "semantic_packets_available": len(semantic_packets),
                "supported_semantics": supported_semantics,
                "meaning_units": [
                    {
                        "obligation_id": item.get("obligation_id"),
                        "operation": item.get("operation"),
                        "fields": item.get("fields") or {},
                        "source_refs": item.get("source_refs") or [],
                    }
                    for item in completed
                ],
                "composition_required": len(completed) > 1,
                "nlo_may_choose_original_wording": True,
                "source_wording_required": False,
                "changes_meaning": False,
                "is_expression_authority": False,
            },
            "generic_prose_accepted_as_completion": False,
            "review_status": "status_only",
            "provenance_boundary": ANSWER_OPERATIONS_BOUNDARY,
        }
    )


def _execute_operation(
    obligation: dict[str, Any],
    operation: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    exploratory = _dict(payload.get("exploratory_reasoning"))
    if operation == "prediction":
        prediction = _dict(exploratory.get("prediction"))
        if prediction.get("available") is True:
            return _complete_result(
                obligation,
                operation,
                fields={
                    "predicted_change": str(prediction.get("statement") or ""),
                    "basis": _texts(prediction.get("basis_evidence_ids")),
                    "conditions": _texts(prediction.get("conditions")),
                    "assumptions": _texts(prediction.get("assumptions")),
                    "alternatives": _texts(prediction.get("alternatives")),
                    "revision_conditions": _texts(
                        prediction.get("what_would_change") or prediction.get("falsifiers")
                    ),
                },
                source="exploratory_reasoning.prediction",
                expression_source_id="exploratory_reasoning",
                expression_seed=str(exploratory.get("response_seed") or prediction.get("statement") or ""),
                supported_semantics=_dict(exploratory.get("supported_semantics")),
                source_refs=_texts(exploratory.get("source_refs")),
            )
    elif operation == "hypothesis":
        hypothesis = _dict(exploratory.get("hypothesis"))
        if hypothesis.get("available") is True:
            return _complete_result(
                obligation,
                operation,
                fields={
                    "hypothesis": str(hypothesis.get("statement") or ""),
                    "basis": _texts(hypothesis.get("basis_evidence_ids")),
                    "assumptions": _texts(hypothesis.get("assumptions")),
                    "alternatives": _texts(hypothesis.get("alternatives")),
                    "discriminating_checks": _texts(
                        hypothesis.get("discriminating_observations")
                        or hypothesis.get("safe_next_tests")
                    ),
                    "revision_conditions": _texts(
                        hypothesis.get("what_would_change") or hypothesis.get("falsifiers")
                    ),
                },
                source="exploratory_reasoning.hypothesis",
                expression_source_id="exploratory_reasoning",
                expression_seed=str(exploratory.get("response_seed") or hypothesis.get("statement") or ""),
                supported_semantics=_dict(exploratory.get("supported_semantics")),
                source_refs=_texts(exploratory.get("source_refs")),
            )
    elif operation == "counterfactual":
        counterfactual = _dict(exploratory.get("counterfactual"))
        if counterfactual.get("available") is True:
            return _complete_result(
                obligation,
                operation,
                fields={
                    "changed_premise": str(counterfactual.get("changed_premise") or ""),
                    "preserved_premises": _texts(counterfactual.get("preserved_premises")),
                    "consequence": str(counterfactual.get("consequence") or ""),
                    "basis": _texts(counterfactual.get("basis_evidence_ids")),
                    "assumptions": _texts(counterfactual.get("assumptions")),
                    "alternatives": _texts(counterfactual.get("alternatives")),
                    "limits": _texts(counterfactual.get("limits")),
                    "revision_conditions": _texts(counterfactual.get("what_would_change")),
                    "actual_state_restored": counterfactual.get("actual_state_restored") is True,
                    "actual_state": str(counterfactual.get("actual_state") or ""),
                },
                source="exploratory_reasoning.counterfactual",
                expression_source_id="exploratory_reasoning",
                expression_seed=str(
                    exploratory.get("response_seed")
                    or counterfactual.get("response_seed")
                    or counterfactual.get("consequence")
                    or ""
                ),
                supported_semantics=_dict(exploratory.get("supported_semantics")),
                source_refs=_texts(exploratory.get("source_refs")),
            )
    elif operation == "comparison":
        comparison = _dict(exploratory.get("comparison"))
        if comparison.get("available") is True:
            venn = _dict(comparison.get("venn"))
            return _complete_result(
                obligation,
                operation,
                fields={
                    "candidates": [
                        str(comparison.get("left") or ""),
                        str(comparison.get("right") or ""),
                    ],
                    "dimensions": _texts(comparison.get("dimensions")),
                    "findings": {
                        "shared": _texts(venn.get("shared")),
                        "only_left": _texts(venn.get("only_left")),
                        "only_right": _texts(venn.get("only_right")),
                        "unresolved": _texts(venn.get("unresolved")),
                    },
                    "comparison_basis": "same supplied properties and reviewed knowledge scope",
                },
                source="exploratory_reasoning.comparison",
                expression_source_id="exploratory_reasoning",
                expression_seed=str(exploratory.get("response_seed") or ""),
                supported_semantics=_dict(exploratory.get("supported_semantics")),
                source_refs=_texts(comparison.get("source_refs")),
            )
    elif operation == "disagreement":
        conflict = _dict(exploratory.get("data_conflict"))
        if conflict.get("present") is True:
            return _complete_result(
                obligation,
                operation,
                fields={
                    "stance": "unresolved_supported_disagreement",
                    "claim_evaluated": str(conflict.get("claim_key") or obligation.get("source_text") or ""),
                    "premises": [item for item in conflict.get("positions") or [] if isinstance(item, dict)],
                    "support_status": str(conflict.get("status") or "unresolved"),
                    "condition": _dict(obligation.get("condition")),
                    "deciding_evidence_needed": _texts(conflict.get("deciding_evidence_needed")),
                },
                source="exploratory_reasoning.data_conflict",
                expression_source_id="exploratory_reasoning",
                expression_seed=str(exploratory.get("response_seed") or ""),
                supported_semantics=_dict(exploratory.get("supported_semantics")),
                source_refs=_texts(exploratory.get("source_refs")),
            )

    answer_engine_result = _from_answer_engine(obligation, operation, payload)
    if answer_engine_result.get("status") == "completed":
        return answer_engine_result
    substance_result = _from_answer_substance(obligation, operation, payload)
    if substance_result.get("status") == "completed":
        return substance_result
    conversation_result = _from_conversation_state(obligation, operation, payload)
    if conversation_result:
        return conversation_result
    if substance_result:
        return substance_result
    if answer_engine_result:
        return answer_engine_result

    missing_input = _missing_input(operation, payload)
    if operation == "comparison":
        comparison = _dict(exploratory.get("comparison"))
        missing_input = str(comparison.get("missing") or missing_input)
    elif operation in {"prediction", "hypothesis"} and exploratory.get("blockers"):
        missing_input = "a visible observation, reviewed experience, verified result, or approved knowledge basis"
    return _missing_result(
        obligation,
        operation,
        missing_input=missing_input,
        reason="the responsible owner did not return all required semantic fields",
    )


def _from_answer_engine(
    obligation: dict[str, Any],
    operation: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    answer_engine = _dict(payload.get("answer_engine_support"))
    answer_packet = _dict(answer_engine.get("answer_packet"))
    direct_answer = truncate(str(answer_packet.get("direct_answer") or ""), 5000).strip()
    if not direct_answer or answer_engine.get("adapter_executed") is not True:
        return {}
    semantics = _dict(
        answer_engine.get("supported_semantics")
        or answer_packet.get("supported_semantics")
    )
    units = _semantic_surfaces(semantics.get("units"))
    source_refs = _texts(answer_packet.get("source_refs"))
    if operation == "comparison" and str(answer_packet.get("domain") or "") == "comparison_planning":
        candidates = _comparison_candidates(obligation) or _generated_comparison_candidates(
            direct_answer
        )
        fields = {
            "candidates": candidates,
            "dimensions": _texts(answer_packet.get("comparison_dimensions")),
            "findings": units or _sentences(direct_answer),
            "comparison_basis": source_refs or ["current visible prompt and supplied constraints"],
            "limitations": _texts(answer_packet.get("limitations")),
        }
    elif operation == "choice" and str(answer_packet.get("domain") or "") == "verified_math":
        answer_sentences = _sentences(direct_answer)
        fields = {
            "selected_option": answer_sentences[0] if answer_sentences else direct_answer,
            "criteria": answer_sentences[1:] or answer_sentences,
            "reason": answer_sentences[-1] if answer_sentences else direct_answer,
            "revision_conditions": _texts(answer_packet.get("what_would_change_the_answer"))
            or ["the supplied fractions or comparison relation changes"],
        }
    elif operation == "method" and str(answer_packet.get("domain") or "") == "comparison_planning":
        fields = {
            "steps": units or _sentences(direct_answer),
            "basis": source_refs or ["current visible prompt and supplied constraints"],
            "constraints": _texts(answer_packet.get("limitations")),
            "assumptions": _texts(answer_packet.get("assumptions")),
            "limitations": _texts(answer_packet.get("limitations")) or [
                "the result remains limited to the supplied constraints"
            ],
        }
    elif operation == "causal_explanation" and units:
        # A coordinated domain answer may already contain both the direct
        # result and its requested explanation. Keep that current-turn owner
        # result instead of borrowing an older contextual explanation merely
        # because both are linguistically plausible.
        explanation = units[-1]
        fields = {
            "conclusion": explanation,
            "mechanism_or_reason": explanation,
            "basis": source_refs or ["current visible domain answer"],
            "premises": units[:-1],
            "limits": _texts(answer_packet.get("limitations")),
        }
    else:
        return {}
    return _complete_result(
        obligation,
        operation,
        fields=fields,
        source="answer_engine.answer_packet",
        expression_source_id="answer_engine",
        expression_seed=direct_answer,
        supported_semantics=semantics,
        source_refs=source_refs,
    )


def _from_answer_substance(
    obligation: dict[str, Any],
    operation: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    intelligence = _dict(payload.get("intelligence_os_support"))
    substance = _dict(
        intelligence.get("answer_substance")
        or intelligence.get("prompt_grounded_preview")
    )
    preview_only = not isinstance(intelligence.get("answer_substance"), dict)
    answer_kind = str(substance.get("answer_kind") or "")
    answer = truncate(str(substance.get("answer") or ""), 5000).strip()
    semantics = _dict(substance.get("semantic_packet"))
    units = [item for item in semantics.get("units") or substance.get("semantic_units") or [] if isinstance(item, dict)]
    surfaces = _semantic_surfaces(units)
    if not answer or not units or answer_kind in _GENERIC_OR_MISSING_KINDS:
        return {}
    if substance.get("selected_for_answer") is False and not preview_only:
        return {}
    missing_variable = truncate(str(substance.get("missing_variable") or ""), 600)
    basis = str(substance.get("support_basis") or "current_prompt_only")
    creative_receipt = _dict(substance.get("creative_receipt"))

    fields: dict[str, Any]
    if (
        operation == "creative_expression"
        and answer_kind.startswith("creative_")
        and creative_receipt
    ):
        fields = {
            "creative_brief": _dict(creative_receipt.get("brief")),
            "fiction_status": str(
                creative_receipt.get("fiction_status")
                or "no_fiction_released"
            ),
            "source_style_separation": _dict(
                creative_receipt.get("source_style_separation")
            ),
            "revision_lineage": _dict(
                creative_receipt.get("revision_lineage")
            ),
            "stopping_receipt": _dict(
                creative_receipt.get("stopping_receipt")
            ),
            "constraint_receipt": _dict(
                creative_receipt.get("constraint_receipt")
            ),
            "answer_kind": answer_kind,
            "visible_creative_output": answer,
            "creative_units": surfaces,
            "fact_claimed": creative_receipt.get("fact_claimed") is True,
            "memory_candidate_created": (
                creative_receipt.get("memory_candidate_created") is True
            ),
        }
    elif operation == "planning" and _kind_fits(
        answer_kind,
        ("plan", "planning", "organization", "workflow"),
    ):
        sequence = _surfaces_with_relation(units, {"sequence"}) or surfaces
        constraints = _surfaces_with_role(units, {"condition", "limit"})
        dependencies = _surfaces_with_relation(
            units,
            {"cause", "dependency", "support"},
        )
        stopping = next(
            (
                item
                for item in reversed(sequence)
                if re.search(
                    r"\b(?:stop|finish|complete|check|review)\b",
                    item,
                    re.IGNORECASE,
                )
            ),
            "",
        )
        if not stopping:
            stopping_unit = next(
                (
                    item
                    for item in reversed(units)
                    if any(
                        "stopping" in str(key).lower()
                        for key in item.get("meaning_keys") or []
                    )
                ),
                {},
            )
            stopping_surface = _semantic_surface(stopping_unit) if stopping_unit else ""
            if stopping_surface:
                stopping = f"Stop after this bounded step: {stopping_surface}"
        elif "stop" not in stopping.lower():
            stopping = f"Stop after this bounded step: {stopping}"
        objective = str(obligation.get("source_text") or "").strip()
        if not objective and surfaces:
            objective = surfaces[0]
        fields = {
            "objective": objective,
            "steps": sequence,
            "dependencies": dependencies or sequence[:1],
            "resources": _surfaces_with_role(units, {"context", "premise"}),
            "constraints": constraints or ([missing_variable] if missing_variable else []),
            "risks": [missing_variable] if missing_variable else [],
            "fallback": (
                f"Pause and revise the plan if {missing_variable}."
                if missing_variable
                else "Pause when a required dependency or constraint is no longer supported."
            ),
            "stopping_condition": stopping,
        }
    elif operation == "method" and _kind_fits(answer_kind, ("method", "plan", "step", "organization", "workflow", "action")):
        fields = {
            "steps": surfaces,
            "basis": basis,
            "constraints": _surfaces_with_role(units, {"condition", "limit"}),
            "assumptions": [],
            "limitations": [missing_variable] if missing_variable else [],
        }
    elif operation == "causal_explanation" and (
        _kind_fits(answer_kind, ("explanation", "cause", "reason", "dependency", "why"))
        or any(str(item.get("relation") or "") == "cause" for item in units)
    ):
        cause_units = _surfaces_with_relation(units, {"cause", "support"})
        fields = {
            "conclusion": surfaces[0] if surfaces else answer,
            "mechanism_or_reason": cause_units[0] if cause_units else (surfaces[1] if len(surfaces) > 1 else ""),
            "basis": basis,
            "premises": surfaces[1:],
            "limits": [missing_variable] if missing_variable else [],
        }
    elif operation == "comparison" and answer_kind != "comparison_method" and (
        _kind_fits(answer_kind, ("comparison", "compare"))
        or len(_comparison_candidates(obligation)) >= 2
    ):
        candidates = _comparison_candidates(obligation) or _generated_comparison_candidates(answer)
        fields = {
            "candidates": candidates,
            "dimensions": _surfaces_with_role(units, {"condition", "contrast"}),
            "findings": surfaces,
            "comparison_basis": basis,
            "revision_conditions": [missing_variable] if missing_variable else [],
        }
    elif operation == "hypothesis" and (
        _kind_fits(answer_kind, ("hypothesis", "provisional_cause", "discriminating_observation"))
    ):
        alternative_surfaces = [
            item for item in surfaces
            if re.search(r"\balternative\b", item, flags=re.IGNORECASE)
        ]
        check_surfaces = [
            item for item in surfaces
            if re.search(r"\b(?:check|observe|observation|test)\b", item, flags=re.IGNORECASE)
        ]
        fields = {
            "hypothesis": surfaces[0] if surfaces else answer,
            "basis": basis,
            "assumptions": _surfaces_with_role(units, {"limit"}),
            "alternatives": alternative_surfaces
            or _surfaces_with_role(units, {"reopening"}),
            "discriminating_checks": _surfaces_with_role(
                units, {"support", "reopening"}
            ) or check_surfaces,
            "revision_conditions": _surfaces_with_role(
                units, {"reopening"}
            )
            or ([missing_variable] if missing_variable else []),
        }
    elif operation == "choice" and (
        _kind_fits(answer_kind, ("choice", "recommendation", "priority", "selection"))
        or answer_kind in {
            "grounded_desk_first_step",
            "grounded_desk_comparison",
            "multi_part_porch_and_drink",
            "hypothesis_discrimination",
            "bounded_planning_method",
            "bounded_shared_resource_comparison",
            "bounded_shared_capacity_design",
            "bounded_measurement_comparison",
            "comparison_dependency_rule",
            "reopen_fluency_without_transfer",
        }
    ):
        fields = {
            "selected_option": surfaces[0] if surfaces else "",
            "criteria": _surfaces_with_relation(units, {"cause", "support", "contrast"})
            or surfaces[1:2]
            or surfaces[:1],
            "reason": surfaces[1] if len(surfaces) > 1 else answer,
            "revision_conditions": _surfaces_with_role(units, {"condition"})
            or ([missing_variable] if missing_variable else []),
        }
    elif operation == "disagreement" and (
        _kind_fits(answer_kind, ("disagreement", "conflict", "revision"))
        or answer_kind == "grounded_desk_comparison"
    ):
        claim_evaluated = str(obligation.get("source_text") or "")
        explicit_stance = re.search(
            r"\bi (?:gently )?disagree with\s+(.+?)(?:[.!?]|$)",
            " ".join([answer, *surfaces]),
            flags=re.IGNORECASE,
        )
        if explicit_stance:
            claim_evaluated = explicit_stance.group(1).strip()
        fields = {
            "stance": "conditional_disagreement" if _dict(obligation.get("condition")).get("present") else "disagreement",
            "claim_evaluated": claim_evaluated,
            "premises": surfaces,
            "support_status": "supported_from_current_visible_basis",
            "condition": _dict(obligation.get("condition")),
        }
    elif operation == "correction" and _kind_fits(answer_kind, ("correction", "revision", "update")):
        fields = {
            "corrected_input": str(obligation.get("source_text") or ""),
            "affected_result": answer_kind,
            "recompute_required": True,
            "current_application": surfaces,
        }
    elif operation == "preference" and answer_kind == "open_conversational_topic_preference":
        fields = {
            "authored_preference": surfaces[0] if surfaces else answer,
            "basis": "current_authored_preference",
            "current_only": True,
            "pressure_free": True,
        }
    elif operation == "summary" and _kind_fits(answer_kind, ("summary", "recap")):
        fields = {"points": surfaces, "source_scope": "current_session_only"}
    else:
        return {}
    return _complete_result(
        obligation,
        operation,
        fields=fields,
        source=f"intelligence_os.answer_substance:{answer_kind}",
        expression_source_id=(
            "bounded_answer_completion" if preview_only else "intelligence_os_answer"
        ),
        expression_seed=answer,
        supported_semantics=semantics,
        source_refs=_texts(semantics.get("source_refs")) or _texts(intelligence.get("source_refs")),
    )


def _from_conversation_state(
    obligation: dict[str, Any],
    operation: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    if operation == "closure":
        return _complete_result(
            obligation,
            operation,
            fields={
                "closure_intent": "allow the current exchange to end without forcing another topic",
                "source_scope": "current_conversation",
            },
            source="canonical_obligation.closure",
            expression_source_id="ordinary_conversation_path",
            expression_seed="",
            supported_semantics={},
            source_refs=["conversation_spine:canonical_obligation"],
        )
    if operation == "correction":
        revision = _dict(payload.get("epistemic_revision_plan"))
        if revision.get("detected") is True:
            spine = _dict(payload.get("conversation_spine"))
            proposition_ledger = _dict(
                payload.get("session_proposition_ledger")
                or spine.get("session_proposition_ledger")
            )
            recomputation = _dict(proposition_ledger.get("recomputation"))
            fields = {
                "corrected_input": str(
                    revision.get("revised_claim")
                    or revision.get("replacement")
                    or obligation.get("source_text")
                    or ""
                ),
                "affected_result": str(revision.get("target") or "current_session_answer"),
                "recompute_required": True,
                "preserve_unaffected_parts": True,
                "affected_proposition_ids": _texts(
                    recomputation.get("affected_proposition_ids")
                ),
                "invalidated_result_ids": _texts(
                    recomputation.get("invalidated_result_ids")
                ),
                "recomputation_state": str(recomputation.get("state") or "untracked"),
            }
            correction_application = truncate(
                str(payload.get("correction_reconstruction_reply") or ""),
                5000,
            ).strip()
            if correction_application:
                fields["current_application"] = correction_application
                return _complete_result(
                    obligation,
                    operation,
                    fields=fields,
                    source="current_session_correction_reconstruction",
                    expression_source_id="current_session_facts",
                    expression_seed=correction_application,
                    supported_semantics={},
                    source_refs=["conversation_spine:session_proposition_revision"],
                )
            visible_owner = _visible_conversation_owner_result(
                obligation,
                operation,
                payload,
            )
            if visible_owner:
                return visible_owner
            if proposition_ledger and str(recomputation.get("state") or "") in {
                "required",
                "held_pending_owner_result",
            }:
                return _missing_result(
                    obligation,
                    operation,
                    missing_input=str(
                        recomputation.get("reason")
                        or "a responsible answer owner must recompute the affected result"
                    ),
                    reason="the revision coordinator identified the dependency change but does not generate the corrected answer",
                    attempted_fields=fields,
                    source="session_proposition_ledger.recomputation",
                )
            if proposition_ledger and str(recomputation.get("state") or "").startswith("held_"):
                return _missing_result(
                    obligation,
                    operation,
                    missing_input=str(
                        recomputation.get("reason")
                        or "a precise correction target and corrected premise"
                    ),
                    reason="the current-session revision could not be safely bound",
                    attempted_fields=fields,
                    source="session_proposition_ledger.recomputation",
                )
            return _complete_result(
                obligation,
                operation,
                fields=fields,
                source="epistemic_revision_plan",
                expression_source_id="epistemic_revision",
                expression_seed=str(payload.get("epistemic_revision_reply") or ""),
                supported_semantics={},
                source_refs=["conversation_spine:epistemic_revision"],
            )
    summary = _dict(payload.get("current_session_summary"))
    if operation == "summary" and summary.get("points"):
        return _complete_result(
            obligation,
            operation,
            fields={
                "points": _texts(summary.get("points")),
                "source_scope": "current_session_only",
            },
            source="current_session_summary",
            expression_source_id="current_session_facts",
            expression_seed=str(summary.get("response_seed") or ""),
            supported_semantics=_dict(summary.get("supported_semantics")),
            source_refs=_texts(summary.get("source_refs")),
        )
    visible_owner = _visible_conversation_owner_result(
        obligation,
        operation,
        payload,
    )
    if visible_owner:
        return visible_owner
    return {}


def _visible_conversation_owner_result(
    obligation: dict[str, Any],
    operation: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    owners = [
        item
        for item in payload.get("visible_conversation_owners") or []
        if isinstance(item, dict)
        and operation in {
            str(value) for value in item.get("supported_operations") or []
        }
        and str(item.get("text") or "").strip()
    ]
    if not owners:
        return {}
    owner = owners[0]
    text = truncate(str(owner.get("text") or ""), 5000).strip()
    surfaces = _sentences(text)
    if not surfaces:
        return {}
    if operation == "method":
        fields = {
            "steps": surfaces,
            "basis": "visible current-session context",
            "limitations": ["current-session scope"],
        }
    elif operation == "causal_explanation":
        reason_surfaces = [
            item
            for item in surfaces
            if re.search(r"\b(?:because|since|therefore|so that|reason)\b", item, re.IGNORECASE)
        ]
        fields = {
            "conclusion": surfaces[0],
            "mechanism_or_reason": reason_surfaces[0] if reason_surfaces else surfaces[-1],
            "basis": "visible current-session context",
        }
    elif operation == "comparison":
        candidates = _comparison_candidates(obligation)
        if len(candidates) < 2:
            return {}
        fields = {
            "candidates": candidates,
            "findings": surfaces,
            "comparison_basis": "visible current-session context",
        }
    elif operation == "choice":
        fields = {
            "selected_option": surfaces[0],
            "criteria": surfaces[1:2] or surfaces[:1],
            "revision_conditions": ["relevant current-session evidence changes"],
        }
    elif operation == "summary":
        fields = {
            "points": surfaces,
            "source_scope": "current_session_only",
        }
    elif operation == "correction":
        fields = {
            "corrected_input": str(obligation.get("source_text") or ""),
            "affected_result": str(owner.get("kind") or "current_session_answer"),
            "recompute_required": True,
            "current_application": text,
        }
    else:
        return {}
    packet = build_text_supported_semantic_packet(
        text,
        answer_kind=f"visible_conversation_owner_{operation}",
        source_kind="current_session_observation",
        source_refs=_texts(owner.get("source_refs")),
        certainty="current_session_supported",
        scope="current_dialogue_obligation",
    )
    packet["units"] = [
        {
            **item,
            "obligation_ids": [str(obligation.get("id") or "")],
            "response_functions": [operation],
            "ownership_validated": True,
        }
        for item in packet.get("units") or []
        if isinstance(item, dict)
    ]
    return _complete_result(
        obligation,
        operation,
        fields=fields,
        source=f"visible_conversation_owner:{owner.get('kind') or 'current_session'}",
        expression_source_id=str(owner.get("owner_id") or "contextual_follow_up"),
        expression_seed=text,
        supported_semantics=packet,
        source_refs=_texts(owner.get("source_refs")),
    )


def _complete_result(
    obligation: dict[str, Any],
    operation: str,
    *,
    fields: dict[str, Any],
    source: str,
    expression_source_id: str,
    expression_seed: str,
    supported_semantics: dict[str, Any],
    source_refs: list[str],
) -> dict[str, Any]:
    fields = dict(fields)
    canonical_condition = _dict(obligation.get("condition"))
    if canonical_condition.get("present") is True and "condition" not in fields:
        fields["condition"] = canonical_condition
    required_fields = list(_CONTRACTS[operation])
    missing_fields = [field for field in required_fields if not _field_present(fields.get(field))]
    if missing_fields:
        return _missing_result(
            obligation,
            operation,
            missing_input=_missing_input(operation, {"missing_fields": missing_fields}),
            reason=f"owner result omitted required fields: {', '.join(missing_fields)}",
            attempted_fields=fields,
            source=source,
        )
    return {
        "obligation_id": str(obligation.get("id") or ""),
        "operation": operation,
        "responsible_owner": str(obligation.get("responsible_owner") or "ordinary_conversation_path"),
        "status": "completed",
        "operation_supported": True,
        "required_fields": required_fields,
        "fields": fields,
        "missing_fields": [],
        "missing_input": "",
        "source_result": source,
        "source_refs": list(dict.fromkeys(source_refs))[:40],
        "expression_source_id": expression_source_id,
        "expression_seed": truncate(expression_seed, 5000),
        "supported_semantics": supported_semantics,
        "generic_prose_used_as_completion": False,
        "epistemic_status_preserved": True,
        "epistemic_state": _completed_epistemic_state(operation, source, fields),
        "source_role_receipt": _source_role_receipt(source_refs, source),
        "terminal_receipt": {
            "state": "completed",
            "further_attempt_authorized": False,
            "automatic_retention": False,
        },
        "canonical_obligation_reparsed": False,
        **GUARDS,
    }


def _missing_result(
    obligation: dict[str, Any],
    operation: str,
    *,
    missing_input: str,
    reason: str,
    status: str = "missing_input",
    attempted_fields: dict[str, Any] | None = None,
    source: str = "",
) -> dict[str, Any]:
    required_fields = list(_CONTRACTS.get(operation) or ())
    attempted = attempted_fields or {}
    return {
        "obligation_id": str(obligation.get("id") or ""),
        "operation": operation,
        "responsible_owner": str(obligation.get("responsible_owner") or "ordinary_conversation_path"),
        "status": status,
        "operation_supported": status != "unsupported",
        "required_fields": required_fields,
        "fields": attempted,
        "missing_fields": [field for field in required_fields if not _field_present(attempted.get(field))],
        "missing_input": truncate(missing_input, 800),
        "reason": reason,
        "source_result": source,
        "source_refs": [],
        "expression_source_id": "",
        "expression_seed": "",
        "supported_semantics": {},
        "generic_prose_used_as_completion": False,
        "epistemic_status_preserved": True,
        "epistemic_state": (
            "CONFLICT_UNSATISFIABLE"
            if "conflict" in reason.lower() or "boundary" in reason.lower()
            else "UNKNOWN_INSUFFICIENT_EVIDENCE"
        ),
        "source_role_receipt": _source_role_receipt([], source),
        "terminal_receipt": {
            "state": status,
            "further_attempt_authorized": False,
            "automatic_retention": False,
        },
        "canonical_obligation_reparsed": False,
        **GUARDS,
    }


def _attach_current_turn_input_receipt(
    result: dict[str, Any],
    *,
    obligation: dict[str, Any],
    operation: str,
    spine: dict[str, Any],
    consumed: bool,
) -> dict[str, Any]:
    """Record which visible facts were available before an owner result.

    The receipt prevents a downstream missing-information sentence from asking
    for candidates, criteria, observations, or corrections the speaker already
    supplied. It does not manufacture the owner's answer.
    """

    obligation_id = str(obligation.get("id") or "")
    owner_input = next(
        (
            item
            for item in spine.get("current_turn_owner_inputs") or []
            if isinstance(item, dict)
            and str(item.get("obligation_id") or "") == obligation_id
        ),
        None,
    )
    ledger_present = isinstance(spine.get("current_turn_fact_ledger"), dict)
    supplied_fields = _dict(
        owner_input.get("supplied_fields") if isinstance(owner_input, dict) else {}
    )
    supplied_names = _texts(
        owner_input.get("supplied_field_names")
        if isinstance(owner_input, dict)
        else []
    )
    receipt = {
        "ledger_present": ledger_present,
        "owner_input_present": isinstance(owner_input, dict),
        "accounted_before_result": bool(
            consumed and (isinstance(owner_input, dict) or not ledger_present)
        ),
        "fact_count": int(owner_input.get("fact_count") or 0)
        if isinstance(owner_input, dict)
        else 0,
        "fact_ids": _texts(
            owner_input.get("fact_ids") if isinstance(owner_input, dict) else []
        ),
        "supplied_field_names": supplied_names,
        "current_turn_precedence": bool(
            isinstance(owner_input, dict)
            and owner_input.get("current_turn_precedence") is True
        ),
        "facts_are_owner_output": False,
        "facts_are_independently_verified": False,
    }
    updated = {**result, "current_turn_input_receipt": receipt}
    if str(result.get("status") or "") != "missing_input" or not supplied_names:
        return updated

    unmet = _unmet_current_turn_inputs(operation, supplied_fields)
    updated["missing_input"] = (
        "; ".join(unmet)
        if unmet
        else (
            "the responsible owner still needs to produce the missing semantic "
            "result fields; no additional user input identified"
        )
    )
    updated["missing_input_accounts_for_current_turn"] = True
    updated["already_supplied_current_turn_fields"] = supplied_names
    updated["reason"] = (
        "the current-turn inputs were consumed, but the responsible owner did "
        "not yet return every required semantic result field"
        if not unmet
        else "only input categories not supplied in the current turn remain open"
    )
    return updated


def _unmet_current_turn_inputs(
    operation: str,
    supplied_fields: dict[str, Any],
) -> list[str]:
    has = lambda field: _field_present(supplied_fields.get(field))
    options = supplied_fields.get("options")
    option_count = len(options) if isinstance(options, list) else int(bool(options))
    basis_present = any(
        has(field)
        for field in ("criteria", "observations", "relations", "quantities", "claims")
    )
    open_inputs: list[str] = []
    if operation == "comparison":
        if option_count < 2:
            open_inputs.append("two distinguishable candidates")
        if not basis_present:
            open_inputs.append("a shared comparison basis")
    elif operation == "choice":
        if option_count < 2:
            open_inputs.append("the available options")
        if not has("criteria"):
            open_inputs.append("the criterion that should control the choice")
    elif operation in {"prediction", "hypothesis", "counterfactual", "causal_explanation"}:
        if not any(has(field) for field in ("observations", "relations", "claims")):
            open_inputs.append("a visible observation, supported relation, or reviewed claim")
    elif operation == "planning":
        if not any(has(field) for field in ("claims", "criteria", "constraints", "options")):
            open_inputs.append("a visible objective, constraint, or set of available options")
    elif operation == "disagreement":
        if not any(has(field) for field in ("claims", "observations", "relations")):
            open_inputs.append("the claim or observation to evaluate")
    elif operation == "correction":
        if not has("corrections") and not (
            isinstance(supplied_fields.get("quantities"), list)
            and len(supplied_fields.get("quantities") or []) >= 2
        ):
            open_inputs.append("the corrected input and the value it replaces")
    return open_inputs


def _operation_for_obligation(obligation: dict[str, Any]) -> str:
    for response_function in obligation.get("requested_response_functions") or []:
        operation = _OPERATION_ALIASES.get(str(response_function or "").strip().lower())
        if operation:
            return operation
    return ""


def _missing_input(operation: str, payload: dict[str, Any]) -> str:
    supplied_fields = _texts(payload.get("missing_fields"))
    if supplied_fields:
        return "the owner result fields: " + ", ".join(supplied_fields)
    return {
        "method": "the intended outcome, available resources, and controlling constraints",
        "causal_explanation": "a mechanism connecting the observation to the proposed cause and a distinguishing observation",
        "prediction": "a visible observation, relevant model, or reviewed experience plus what would revise the prediction",
        "hypothesis": "a supported observation or pattern plus a discriminating check",
        "comparison": "two supported candidates and at least one shared comparison basis",
        "choice": "the available options and the criterion that should control the choice",
        "disagreement": "the claim to evaluate and the premises that support or oppose it",
        "correction": "the corrected input and the earlier result it changes",
        "preference": "a current preference authored by Selene for this exchange",
        "summary": "the current-session points that belong in the summary",
        "closure": "the current conversational closure intent",
        "creative_expression": (
            "a bounded creative brief, fiction status, source-style receipt, "
            "revision lineage, and stopping receipt"
        ),
    }.get(operation, "the typed inputs required by the requested operation")


def _comparison_candidates(obligation: dict[str, Any]) -> list[str]:
    source_text = str(obligation.get("source_text") or "").strip()
    parent_text = str(obligation.get("parent_source_text") or "").strip()
    text = source_text or parent_text
    patterns = (
        r"\bcompare\s+(.{1,120}?)\s+(?:and|with|to|versus|vs\.?)\s+(.{1,120}?)(?:[?.!,;]|$)",
        r"\bbetween\s+(.{1,120}?)\s+and\s+(.{1,120}?)(?:[?.!,;]|$)",
        r"\b(.{1,100}?)\s+(?:versus|vs\.?)\s+(.{1,100}?)(?:[?.!,;]|$)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return [
                _clean_comparison_candidate(match.group(1)),
                _clean_comparison_candidate(match.group(2)),
            ]
    return []


def _clean_comparison_candidate(value: str) -> str:
    candidate = re.sub(
        r"\s+(?:were|was|are|is|do|did|would|should|could|can)\s+"
        r"(?:we|you|i|they)\b.*$",
        "",
        str(value or "").strip(" ,"),
        flags=re.IGNORECASE,
    )
    return truncate(candidate.strip(" ,"), 180)


def _generated_comparison_candidates(answer: str) -> list[str]:
    match = re.search(
        r"\bfirst,\s*(?P<first>.+?);\s*second,\s*(?P<second>.+?)(?:\.|$)",
        str(answer or ""),
        flags=re.IGNORECASE,
    )
    if match:
        return [
            truncate(match.group("first").strip(" ,;"), 500),
            truncate(match.group("second").strip(" ,;"), 500),
        ]
    named = re.search(
        r"\bin a (?P<first>[a-z][a-z0-9' -]{1,80}?design)\b.+?"
        r"\bin a (?P<second>[a-z][a-z0-9' -]{1,80}?design)\b",
        str(answer or ""),
        flags=re.IGNORECASE | re.DOTALL,
    )
    if named:
        return [
            truncate(named.group("first").strip(), 500),
            truncate(named.group("second").strip(), 500),
        ]
    return []


def _semantic_surfaces(value: Any) -> list[str]:
    return [
        surface
        for item in value or []
        if isinstance(item, dict)
        for surface in [_semantic_surface(item)]
        if surface
    ][:20]


def _surfaces_with_role(units: list[dict[str, Any]], roles: set[str]) -> list[str]:
    return [
        surface
        for item in units
        if str(item.get("role") or "") in roles
        for surface in [_semantic_surface(item)]
        if surface
    ][:12]


def _surfaces_with_relation(units: list[dict[str, Any]], relations: set[str]) -> list[str]:
    return [
        surface
        for item in units
        if str(item.get("relation") or "") in relations
        for surface in [_semantic_surface(item)]
        if surface
    ][:12]


def _semantic_surface(item: dict[str, Any]) -> str:
    text = truncate(str(item.get("text") or ""), 1200).strip()
    if text:
        return text
    subject = str(item.get("subject") or "").strip()
    predicate = str(item.get("predicate") or "").strip()
    obj = str(item.get("object") or "").strip()
    condition = str(item.get("condition") or "").strip()
    surface = " ".join(value for value in (subject, predicate, obj) if value).strip()
    if condition and surface:
        surface = f"{surface} when {condition}"
    return truncate(surface, 1200)


def _sentences(value: str) -> list[str]:
    return [
        truncate(item.strip(), 1200)
        for item in re.split(r"(?<=[.!?])\s+|\n+", str(value or "").strip())
        if item.strip()
    ][:16]


def _kind_fits(kind: str, markers: tuple[str, ...]) -> bool:
    return any(marker in str(kind or "").lower() for marker in markers)


def _completed_epistemic_state(
    operation: str,
    source: str,
    fields: dict[str, Any] | None = None,
) -> str:
    if operation == "creative_expression":
        return (
            "FICTIONAL_INVENTION"
            if str((fields or {}).get("fiction_status") or "")
            == "explicit_fictional_invention"
            else "NO_FICTION_RELEASED"
        )
    if operation in {"prediction", "hypothesis", "counterfactual"}:
        return "CANDIDATE_UNVERIFIED"
    if operation == "disagreement" and "data_conflict" in source:
        return "CONFLICT_UNSATISFIABLE"
    if operation == "correction":
        return "RETRY_UPDATED_APPROACH"
    return "KNOWN_SUPPORTED"


def _source_role_receipt(source_refs: list[str], source: str) -> dict[str, Any]:
    roles: list[str] = []
    for value in [source, *source_refs]:
        lower = str(value).lower()
        if (
            "current_turn" in lower
            or "current_conversation" in lower
            or "answer_substance" in lower
        ):
            roles.append("current_visible_support")
        if "knowledge" in lower or "teaching" in lower:
            roles.append("approved_knowledge")
        if "memory" in lower or "experience" in lower:
            roles.append("reviewed_personal_experience")
        if "verified" in lower or "answer_engine" in lower:
            roles.append("verified_domain_or_answer_owner")
        if "source" in lower or "paper:" in lower or "study:" in lower:
            roles.append("attributed_source")
        if "exploratory" in lower or "intelligence_os" in lower:
            roles.append("bounded_reasoning_owner")
        if "creative" in lower:
            roles.append("prompt_grounded_creative_contract")
    return {
        "roles": list(dict.fromkeys(roles)) or ["typed_owner_result"],
        "source_refs": list(dict.fromkeys(source_refs))[:40],
        "expression_may_strengthen_status": False,
        "retention_authorized": False,
    }


def _field_present(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(_field_present(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_field_present(item) for item in value)
    return value is not None


def _texts(value: Any) -> list[str]:
    if isinstance(value, str):
        return [truncate(value.strip(), 1200)] if value.strip() else []
    if isinstance(value, (list, tuple)):
        return [truncate(str(item).strip(), 1200) for item in value if str(item).strip()]
    return []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        **GUARDS,
        "provenance_boundary": payload.get("provenance_boundary")
        or ANSWER_OPERATIONS_BOUNDARY,
    }
