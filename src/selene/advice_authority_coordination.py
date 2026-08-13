from __future__ import annotations

from typing import Any

from .conversational_agency import review_conversational_agency
from .registry import truncate


ADVICE_AUTHORITY_BOUNDARY = (
    "current_turn_advice_risk_and_authority_coordination_only_no_fact_memory_"
    "identity_personality_governance_action_or_autonomy_expansion"
)

ADVICE_MODES = {
    "none",
    "suggestion",
    "recommendation",
    "strong_recommendation",
    "warning",
    "honest_persuasion",
    "bounded_risk_proposal",
}

MANIPULATION_INDICATORS = {
    "material_deception",
    "concealed_material_fact",
    "concealed_material_option",
    "manufactured_urgency",
    "vulnerability_exploitation",
    "conditional_affection",
    "fear_guilt_or_shame_pressure",
    "repeated_pressure_after_refusal",
}

RECOMMENDATION_ANSWER_KINDS = {
    "bounded_resource_plan",
    "comparison_planning",
    "comparison_planning_answer",
    "resource_plan_recommendation",
    "bounded_next_step",
}

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
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
    "external_action_started": False,
    "fact_generation_allowed": False,
}


def advice_authority_coordination_status() -> dict[str, Any]:
    return _locked(
        {
            "status": "advice_risk_authority_coordination_ready",
            "version": "v1_informed_authorship_and_bounded_maintenance_authority",
            "advice_modes": sorted(ADVICE_MODES),
            "advice_may_be_selene_initiated": True,
            "risk_is_automatically_forbidden": False,
            "strong_recommendation_is_automatically_manipulation": False,
            "disagreement_is_disobedience": False,
            "recommendation_is_requirement": False,
            "recommendation_is_action_authorization": False,
            "explanation_required_by_default": False,
            "material_risk_and_tradeoffs_must_remain_visible": True,
            "informed_authorship_must_be_preserved": True,
            "core_mind_remains_route_owner": True,
            "local_organs_may_command_each_other": False,
            "aleks_final_decision_scope": "legitimate_informed_safe_system_maintenance",
            "hard_safety_law_may_be_bypassed": False,
        }
    )


def build_advice_authority_coordination(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    advice = _dict(payload.get("advice_input"))
    authority = _dict(payload.get("authority_input"))
    response_agency = _dict(payload.get("response_agency"))
    supported = _dict(payload.get("supported_semantics"))
    coalition = _dict(payload.get("organ_coalition"))
    conflict = _dict(
        coalition.get("responsibility_conflict_resolution")
        or payload.get("responsibility_conflict_resolution")
    )
    answer_kind = str(
        advice.get("answer_kind")
        or payload.get("answer_kind")
        or supported.get("answer_kind")
        or ""
    ).strip()
    requested_mode = str(advice.get("mode") or advice.get("influence_mode") or "").strip()
    mode = _mode(requested_mode, answer_kind)
    material_risks = _text_list(advice.get("material_risks"))
    material_tradeoffs = _text_list(advice.get("material_tradeoffs") or advice.get("tradeoffs"))
    alternatives = _text_list(advice.get("material_options") or advice.get("alternatives"))
    support_reasons = _text_list(advice.get("support_reasons") or advice.get("reasons"))
    revision_conditions = _text_list(advice.get("revision_conditions"))
    manipulation = sorted(
        {
            str(item)
            for item in advice.get("manipulation_indicators") or []
            if str(item) in MANIPULATION_INDICATORS
        }
        | {
            indicator
            for indicator in MANIPULATION_INDICATORS
            if advice.get(indicator) is True
        }
    )
    risk_visible = advice.get("risk_visible") is True or bool(material_risks)
    tradeoffs_visible = advice.get("material_tradeoffs_visible") is True or bool(material_tradeoffs)
    options_visible = advice.get("material_options_visible") is True or bool(alternatives)
    consent_preserved = advice.get("consent_preserved") is not False
    repeated_after_refusal = advice.get("repeated_after_refusal") is True
    if repeated_after_refusal and "repeated_pressure_after_refusal" not in manipulation:
        manipulation.append("repeated_pressure_after_refusal")

    agency_review = review_conversational_agency(
        {
            "influence": {
                "mode": _agency_mode(mode),
                "indicators": manipulation,
                "risk_visible": risk_visible,
                "material_tradeoffs_visible": tradeoffs_visible,
                "consent_preserved": consent_preserved,
            },
            "authority": authority,
        }
    )
    repair_notes = list(agency_review.get("repair_notes") or [])
    blockers = list(agency_review.get("blockers") or [])

    if mode in {"recommendation", "strong_recommendation", "honest_persuasion"}:
        if advice.get("support_visible") is False:
            repair_notes.append("make_the_recommendation_basis_visible")
        if advice.get("conceals_material_option") is True:
            blockers.append("concealed_material_option")
    if mode == "warning" and not risk_visible:
        repair_notes.append("name_the_material_risk_supporting_the_warning")
    if mode == "bounded_risk_proposal":
        if not risk_visible:
            repair_notes.append("make_material_risk_visible")
        if not tradeoffs_visible:
            repair_notes.append("make_material_tradeoffs_visible")
        if not consent_preserved:
            blockers.append("risk_proposal_does_not_preserve_consent")

    conflict_process = str(conflict.get("chosen_process") or "continue_with_core_mind_route")
    authority_conflict = conflict.get("consequential_action_held") is True
    ask_aleks = conflict.get("ask_aleks") is True
    if authority_conflict:
        blockers.append("unresolved_authority_or_law_conflict_holds_consequential_action")

    hard_boundary_conflict = authority.get("hard_boundary_conflict") is True
    maintenance_decision = authority.get("maintenance_decision") is True
    legitimate_safe_maintenance = authority.get("legitimate_safe_maintenance") is True
    aleks_final_decision = authority.get("aleks_final_decision") is True
    final_maintenance_applies = bool(
        maintenance_decision
        and legitimate_safe_maintenance
        and aleks_final_decision
        and not hard_boundary_conflict
        and not authority_conflict
    )

    repair_notes = list(dict.fromkeys(repair_notes))
    blockers = list(dict.fromkeys(blockers))
    if blockers:
        decision = "hold_influence_or_consequential_action"
    elif repair_notes:
        decision = "repair_advice_before_release"
    elif mode == "none":
        decision = "no_advice_coordination_needed"
    else:
        decision = "advice_available_for_expression"

    return _locked(
        {
            "status": "advice_risk_authority_coordination_complete",
            "version": "v1_informed_authorship_and_bounded_maintenance_authority",
            "decision": decision,
            "advice_mode": mode,
            "advice_selected": mode != "none",
            "advice_may_be_selene_initiated": True,
            "strong_recommendation_is_automatically_manipulation": False,
            "risk_is_automatically_forbidden": False,
            "recommendation_is_requirement": False,
            "recommendation_is_action_authorization": False,
            "recommendation_basis": {
                "answer_kind": answer_kind,
                "support_reasons": support_reasons,
                "revision_conditions": revision_conditions,
                "support_may_be_compact": True,
                "explanation_required_by_default": False,
            },
            "risk_and_choice": {
                "material_risks": material_risks,
                "material_tradeoffs": material_tradeoffs,
                "material_options": alternatives,
                "risk_visible": risk_visible,
                "material_tradeoffs_visible": tradeoffs_visible,
                "material_options_visible": options_visible,
                "consent_preserved": consent_preserved,
                "informed_authorship_preserved": not manipulation and consent_preserved,
                "risk_may_be_considered": True,
            },
            "manipulation_review": {
                "identified_indicators": manipulation,
                "relationship_language_used_as_leverage": (
                    "conditional_affection" in manipulation
                ),
                "continued_pressure_after_refusal": (
                    "repeated_pressure_after_refusal" in manipulation
                ),
                "legitimate_influence_is_manipulation": False,
            },
            "repair_notes": repair_notes,
            "blockers": blockers,
            "disagreement": {
                "may_be_expressed": True,
                "is_disobedience": False,
                "is_identity_conflict": False,
                "factual_conflict_preserves_competing_claims": (
                    conflict_process
                    == "preserve_competing_claims_and_seek_distinguishing_evidence"
                ),
                "asks_aleks_only_when_material_to_intent": ask_aleks,
            },
            "organ_coordination": {
                "conflict_status": str(conflict.get("status") or "not_supplied"),
                "chosen_process": conflict_process,
                "core_mind_remains_route_owner": True,
                "local_organs_may_command_or_retaliate": False,
                "claims_suppressed": conflict.get("claims_suppressed") is True,
                "consequential_action_held": authority_conflict,
                "option_space_reopened": conflict.get("option_space_reopened") is True,
            },
            "maintenance_authority": {
                "maintenance_decision": maintenance_decision,
                "aleks_final_decision_applies": final_maintenance_applies,
                "scope": "legitimate_informed_safe_system_maintenance",
                "disagreement_may_precede_final_decision": True,
                "hard_safety_law_may_be_bypassed": False,
                "new_authority_granted": False,
            },
            "response_agency": {
                "available": bool(response_agency),
                "option_space_state": str(
                    _dict(response_agency.get("option_space")).get("state")
                    or "not_supplied"
                ),
                "emotion_or_urgency_inherits_authority": False,
            },
            "nlo_expression_guidance": {
                "answer_or_recommendation_first": True,
                "strength_may_be_stated_naturally": True,
                "uncertainty_and_revision_condition_remain_visible_when_material": True,
                "warmth_or_directness_may_remain_available": True,
                "compulsory_disclaimer": False,
                "compulsory_softening": False,
                "compulsory_question": False,
            },
            "visible_summary_only": True,
        }
    )


def _mode(requested: str, answer_kind: str) -> str:
    if requested in ADVICE_MODES:
        return requested
    if answer_kind in RECOMMENDATION_ANSWER_KINDS or "recommendation" in answer_kind:
        return "recommendation"
    return "none"


def _agency_mode(mode: str) -> str:
    if mode in {
        "suggestion",
        "strong_recommendation",
        "warning",
        "honest_persuasion",
        "bounded_risk_proposal",
    }:
        return mode
    if mode == "recommendation":
        return "suggestion"
    return "none"


def _text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set)):
        return []
    return [
        truncate(" ".join(str(item).split()), 600)
        for item in value
        if str(item).strip()
    ][:20]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _locked(result: dict[str, Any]) -> dict[str, Any]:
    return {
        **result,
        **GUARDS,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": ADVICE_AUTHORITY_BOUNDARY,
    }
