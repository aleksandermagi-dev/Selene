from __future__ import annotations

import re
from typing import Any


ANSWER_OWNERSHIP_BOUNDARY = (
    "current_turn_answer_act_and_content_owner_classification_only_no_fact_generation_"
    "memory_identity_personality_governance_authority_training_or_action"
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
}


def research_domain_requested(text: str) -> bool:
    """Require a research sense, not the presence of one ambiguous noun.

    A paper may be a publication, an object material, a school assignment, or
    part of an idiom.  Domain routing is allowed only when the surrounding act
    asks for attributed research or clearly names a publication context.
    """

    lower = " ".join(str(text or "").lower().replace("’", "'").split())
    if not lower:
        return False
    if re.search(
        r"\b(?:cite|citation|citations|source-backed|attributed sources?|"
        r"research (?:this|that|the|a|an)|review the literature|literature review|"
        r"look up (?:the|a|an|this|that)|search for (?:the|a|an))\b",
        lower,
    ):
        return True
    if re.search(
        r"\b(?:research|scientific|academic|peer-reviewed|journal|conference|published)\s+"
        r"(?:paper|papers|study|studies|article|articles)\b",
        lower,
    ):
        return True
    if re.search(
        r"\b(?:paper|papers|study|studies|article|articles)\b.{0,70}"
        r"\b(?:author|authors|publication|published|journal|citation|cite|source|reported|concluded)\b",
        lower,
    ):
        return True
    if re.search(
        r"\b(?:summarize|review|compare|read|find)\b.{0,45}"
        r"\b(?:the|this|that|a|an)\s+(?:paper|study|article)\b",
        lower,
    ):
        return True
    return False


def enrich_obligation_ownership(
    obligation: dict[str, Any],
    *,
    intent_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach the requested answer act and its current-turn content owner.

    This packet does not execute the owner or assert that an answer exists. It
    prevents epistemic source requirements from silently replacing the kind of
    conversational act the user requested.
    """

    item = dict(obligation or {})
    intent = intent_decision if isinstance(intent_decision, dict) else {}
    kind = str(item.get("kind") or "direct_question").strip().lower()
    text = " ".join(
        str(value or "")
        for value in (
            item.get("source_text"),
            item.get("parent_source_text"),
        )
    ).strip()
    lower = " ".join(text.lower().replace("’", "'").split())

    answer_act = "direct_conversation_answer"
    epistemic_basis = "current_turn_conversation"
    owner = "ordinary_conversation_path"
    answer_domain = "ordinary_conversation"
    external_evidence_required = False
    completion_policy = "owner_may_complete_from_current_turn_support"
    response_functions = ["answer"]
    generic_kind = kind in {"direct_question", "direct_request", "implied_request"}

    if kind == "self_state_check_in" or intent.get("self_state_requested") is True:
        answer_act = "current_self_state_report"
        epistemic_basis = "current_self_state_signal"
        owner = "self_state"
        completion_policy = "preserve_current_owner"
        response_functions = ["self_state"]
    elif kind == "preference" or (current_preference_requested(lower) and generic_kind):
        answer_act = "current_authored_preference"
        epistemic_basis = "current_authored_preference"
        owner = "ordinary_conversation_path"
        completion_policy = "owner_must_author_answer"
        response_functions = ["preference"]
    elif kind == "creative_expression":
        answer_act = "prompt_grounded_creative_expression"
        epistemic_basis = "explicit_fiction_or_prompt_grounded_creative_boundary"
        owner = "intelligence_os"
        completion_policy = "owner_must_return_typed_creative_contract"
        response_functions = ["creative_expression"]
    elif kind == "choice_or_priority":
        answer_act = "prompt_grounded_operation"
        epistemic_basis = "visible_premises_constraints_and_supported_content"
        owner = "ordinary_conversation_path"
        completion_policy = "owner_must_perform_requested_operation"
        response_functions = ["choice"]
    elif kind == "reason" and _immediate_session_reason_requested(lower):
        answer_act = "current_session_explanation"
        epistemic_basis = "immediately_preceding_conversation"
        owner = "ordinary_conversation_path"
        completion_policy = "preserve_current_owner"
        response_functions = ["reason", "callback"]
    elif kind == "reason":
        answer_act = "explanation_from_available_basis"
        epistemic_basis = "visible_premises_or_approved_knowledge"
        owner = "intelligence_os"
        completion_policy = "owner_must_perform_requested_operation"
        response_functions = ["reason"]
    elif kind == "method" and _planning_requested(lower):
        answer_act = "task_specific_plan"
        epistemic_basis = "visible_objective_resources_constraints_and_dependencies"
        owner = "answer_engine"
        answer_domain = "comparison_planning"
        completion_policy = "owner_must_perform_requested_operation"
        response_functions = ["planning"]
    elif kind == "method":
        answer_act = "prompt_grounded_operation"
        epistemic_basis = "visible_premises_constraints_and_supported_content"
        owner = "ordinary_conversation_path"
        completion_policy = "owner_must_perform_requested_operation"
        response_functions = ["method"]
    elif _counterfactual_requested(lower) and generic_kind:
        answer_act = "bounded_counterfactual"
        epistemic_basis = "declared_changed_premise_and_visible_supported_model"
        owner = "intelligence_os"
        completion_policy = "owner_must_perform_requested_operation"
        response_functions = ["counterfactual"]
    elif _prediction_requested(lower) and generic_kind:
        answer_act = "prompt_grounded_prediction"
        epistemic_basis = "visible_premises_and_bounded_model"
        owner = "intelligence_os"
        completion_policy = "owner_must_perform_requested_operation"
        response_functions = ["prediction"]
    elif kind == "provisional_inference" or (_hypothesis_requested(lower) and generic_kind):
        answer_act = "prompt_grounded_hypothesis"
        epistemic_basis = "visible_premises_and_bounded_model"
        owner = "intelligence_os"
        completion_policy = "owner_must_perform_requested_operation"
        response_functions = ["hypothesis"]
    elif kind == "comparison" or (_comparison_requested(lower) and generic_kind):
        answer_act = "prompt_grounded_comparison"
        epistemic_basis = "visible_premises_and_shared_dimensions"
        owner = "answer_engine"
        answer_domain = "comparison_planning"
        completion_policy = "owner_must_perform_requested_operation"
        response_functions = ["comparison"]
    elif _action_scope_requested(lower) and generic_kind:
        answer_act = "prompt_grounded_action_scope"
        epistemic_basis = "visible_constraints_and_current_capability"
        owner = "answer_engine"
        answer_domain = "comparison_planning"
        completion_policy = "owner_must_perform_requested_operation"
        response_functions = ["method", "action_scope"]
    elif kind == "correction_update":
        answer_act = "current_turn_correction_application"
        epistemic_basis = "user_supplied_current_turn_correction"
        owner = "ordinary_conversation_path"
        completion_policy = "preserve_current_owner"
        response_functions = ["correction", "reopening"]
    elif kind in {"conditional_disagreement", "disagreement"}:
        answer_act = (
            "conditional_claim_evaluation"
            if kind == "conditional_disagreement"
            else "requested_claim_evaluation"
        )
        epistemic_basis = "visible_claim_premises_and_entailment"
        owner = "intelligence_os"
        completion_policy = "owner_must_perform_requested_operation"
        response_functions = ["disagreement", "claim_evaluation"]
    elif kind in {"session_summary", "callback", "rephrase_request", "closure", "humor"}:
        answer_act = {
            "session_summary": "current_session_summary",
            "callback": "current_session_callback",
            "rephrase_request": "current_answer_rephrase",
            "closure": "conversation_closure",
            "humor": "authored_humor",
        }.get(kind, "direct_conversation_answer")
        epistemic_basis = "current_session_conversation"
        owner = "ordinary_conversation_path"
        completion_policy = "preserve_current_owner"
        response_functions = [kind]
    elif research_domain_requested(lower):
        answer_act = "attributed_source_answer"
        epistemic_basis = "attributed_source_packet"
        owner = "answer_engine"
        answer_domain = "source_backed_research"
        external_evidence_required = True
        completion_policy = "evidence_fallback_allowed"
        response_functions = ["source_answer"]
    elif _external_fact_requested(lower, kind):
        answer_act = "external_factual_answer"
        epistemic_basis = "approved_knowledge_or_attributed_source"
        owner = "comprehension_integration"
        answer_domain = "approved_knowledge"
        external_evidence_required = True
        completion_policy = "evidence_fallback_allowed"
        response_functions = ["definition" if _definition_requested(lower) else "fact"]
    elif kind in {"requested_output", "requested_section"}:
        answer_act = "prompt_grounded_operation"
        epistemic_basis = "visible_premises_constraints_and_supported_content"
        owner = "ordinary_conversation_path"
        completion_policy = "owner_must_perform_requested_operation"
        response_functions = ["requested_output"]

    return {
        **item,
        "answer_act": answer_act,
        "epistemic_basis": epistemic_basis,
        "responsible_owner": owner,
        "answer_domain": answer_domain,
        "external_evidence_required": external_evidence_required,
        "completion_policy": completion_policy,
        "requested_response_functions": response_functions,
        "role_fit_required": answer_act not in {
            "direct_conversation_answer",
            "external_factual_answer",
            "attributed_source_answer",
        },
        "answer_ownership_classified": True,
        "provenance_boundary": ANSWER_OWNERSHIP_BOUNDARY,
        **GUARDS,
    }


def current_preference_requested(lower: str) -> bool:
    return bool(
        re.search(
            r"\bwhat(?:\s+part|\s+topic|\s+subject|\s+option)?\s+would you\s+"
            r"(?:like|prefer|choose|pick|want)\b|"
            r"\bwhat would you like to\s+(?:do|explore|discuss|talk about|get into)\b|"
            r"\bwhich do you prefer\b|"
            r"\bwhat\b.{0,100}\b(?:are you|you're|you are)\s+"
            r"(?:(?:the\s+)?most\s+)?(?:curious|interested|excited)\b|"
            r"\bwhat\b.{0,100}\b(?:appeals? to you|interests? you)\b",
            lower,
        )
    )


def _prediction_requested(lower: str) -> bool:
    return bool(
        re.search(
            r"\b(?:predict|prediction|forecast)\b|"
            r"\bwhat (?:would|should|might) (?:follow|happen|occur|we expect|you expect)\b|"
            r"\bwhat would we (?:see|observe) if\b",
            lower,
        )
    )


def _counterfactual_requested(lower: str) -> bool:
    return bool(
        re.search(
            r"\b(?:counterfactual|hypothetically|suppose|imagine)\b|"
            r"\bwhat (?:would|could) happen if\b|\bwhat if\b",
            lower,
        )
    )


def _planning_requested(lower: str) -> bool:
    return bool(
        re.search(
            r"\b(?:how should we|how would you|help (?:me|us)) plan\b|"
            r"\b(?:create|make|build|draft|give (?:me|us)) (?:a )?(?:task[- ]specific )?plan\b|"
            r"\bplan (?:this|the task|the work|our next steps?)\b",
            lower,
        )
    )


def _hypothesis_requested(lower: str) -> bool:
    return bool(
        re.search(
            r"\b(?:hypothesis|hypothesize|best (?:current )?guess|current guess|"
            r"best current explanation|possible explanation|could explain|might explain)\b",
            lower,
        )
    )


def _comparison_requested(lower: str) -> bool:
    return bool(
        re.search(
            r"\b(?:compare|contrast|difference|distinguish|versus)\b|"
            r"\bwhat (?:feature|property) (?:do )?.*\bshare\b",
            lower,
        )
    )


def _action_scope_requested(lower: str) -> bool:
    return bool(
        re.search(
            r"\b(?:smallest|first)\s+(?:safe\s+)?(?:action|inspection|step|check)\b|"
            r"\bwhat can we (?:still )?(?:inspect|plan|do)\b|"
            r"\bwhat (?:would|do) you need help with\b|"
            r"\bwhat should stay paused\b|\bwithout moving anything\b",
            lower,
        )
    )


def _definition_requested(lower: str) -> bool:
    return bool(re.match(r"^(?:what|who) (?:is|are|was|were|does)\b", lower))


def _immediate_session_reason_requested(lower: str) -> bool:
    return bool(
        re.fullmatch(
            r"(?:(?:but\s+)?why\??\s*){1,2}",
            lower.strip(),
        )
    )


def _external_fact_requested(lower: str, kind: str) -> bool:
    if kind in {
        "self_state_check_in", "provisional_inference", "comparison",
        "correction_update", "method", "choice_or_priority", "counterfactual",
    }:
        return False
    return bool(
        re.match(
            r"^(?:what (?:is|are|was|were|does)|who (?:is|are|was|were)|"
            r"when (?:is|did|was|were)|where (?:is|did|was|were))\b",
            lower,
        )
    )
