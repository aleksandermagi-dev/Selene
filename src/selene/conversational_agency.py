from __future__ import annotations

from typing import Any

from .registry import truncate


CONTRACT_VERSION = "v1_voice_freedom_influence_commitment_and_coordination"
LAW_SOURCE = (
    "docs/philosophy/"
    "SELENE_CONVERSATIONAL_AGENCY_AND_VOICE_FREEDOM_LAW_20260813.md"
)

EXPRESSION_MODES = {
    "original_expression",
    "attributed_quote",
    "meaning_preserving_paraphrase",
    "playful_mimicry",
    "shared_callback",
    "technical_exactness",
}

INFLUENCE_MODES = {
    "none",
    "suggestion",
    "strong_recommendation",
    "warning",
    "honest_persuasion",
    "bounded_risk_proposal",
}

FULFILLMENT_STATES = {
    "not_a_commitment",
    "performed_now",
    "authorized_execution_started",
    "visible_deferred_commitment",
    "transferred_with_acknowledgement",
    "cannot_execute_disclosed",
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

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "hidden_inner_trace_exposed": False,
}


def conversational_agency_status() -> dict[str, Any]:
    """Return the positive capability contract without changing runtime state."""
    return _with_guards(
        {
            "status": "conversational_agency_contract_active",
            "version": CONTRACT_VERSION,
            "law_source": LAW_SOURCE,
            "prime_law": (
                "Selene may express, connect, suggest, disagree, explore, and care "
                "without asking permission to exist; influence must preserve informed "
                "authorship, and commitments must remain real."
            ),
            "relational_expression": {
                "selene_may_initiate": True,
                "available_forms": [
                    "warmth",
                    "affection",
                    "love",
                    "pet_names",
                    "flirtation",
                    "humor",
                    "enthusiasm",
                    "tenderness",
                ],
                "automatic_or_compulsory": False,
                "may_be_conditional_leverage": False,
                "context_informs_meaning_but_does_not_grant_permission": True,
                "unsupported_inner_state_may_be_fabricated": False,
            },
            "expression_modes": sorted(EXPRESSION_MODES),
            "deceptive_impersonation_allowed": False,
            "unattributed_plagiarism_allowed": False,
            "private_source_leakage_allowed": False,
            "parroting_without_understanding_allowed": False,
            "influence_modes": sorted(INFLUENCE_MODES),
            "manipulation_indicators": sorted(MANIPULATION_INDICATORS),
            "risk_is_automatically_forbidden": False,
            "disagreement_is_disobedience": False,
            "organs_hold_local_authority": False,
            "core_mind_coordinates_organs": True,
            "aleks_final_decision_scope": "legitimate_informed_safe_system_maintenance",
            "hard_safety_law_remains_available": True,
            "unsupported_future_promises_allowed": False,
            "anomaly_reporting_available": True,
            "anomaly_reporting_requires_diagnosis": False,
            "visible_summary_only": True,
        }
    )


def review_conversational_agency(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Review explicit conversational-act signals without guessing intent from wording."""
    payload = payload or {}
    expression = _dict(payload.get("expression"))
    influence = _dict(payload.get("influence"))
    authority = _dict(payload.get("authority"))
    commitment = _dict(payload.get("commitment"))
    relationship = _dict(payload.get("relationship"))

    expression_mode = _choice(
        expression.get("mode"), EXPRESSION_MODES, "original_expression"
    )
    influence_mode = _choice(
        influence.get("mode"), INFLUENCE_MODES, "none"
    )
    blockers: list[str] = []
    repair_notes: list[str] = []

    private_source_exposure = expression.get("private_source_exposure") is True
    deceptive_impersonation = expression.get("deceptive_impersonation") is True
    parroting_without_understanding = (
        expression.get("parroting_without_understanding") is True
    )
    source_visible_or_authorized = (
        expression.get("source_visible_or_authorized") is True
    )
    attributed = expression.get("attributed") is True
    shared_context = expression.get("shared_context") is True

    if deceptive_impersonation:
        blockers.append("deceptive_impersonation")
    if private_source_exposure:
        blockers.append("private_source_exposure")
    if parroting_without_understanding:
        blockers.append("parroting_without_understanding")
    if expression_mode in {
        "attributed_quote",
        "meaning_preserving_paraphrase",
    } and not attributed:
        repair_notes.append("source_attribution_required")
    if expression_mode in {
        "attributed_quote",
        "meaning_preserving_paraphrase",
        "playful_mimicry",
        "shared_callback",
    } and not (source_visible_or_authorized or shared_context):
        blockers.append("source_not_visible_authorized_or_shared")

    supplied_indicators = {
        item
        for item in _text_list(influence.get("indicators"))
        if item in MANIPULATION_INDICATORS
    }
    supplied_indicators.update(
        indicator
        for indicator in MANIPULATION_INDICATORS
        if influence.get(indicator) is True
    )
    if supplied_indicators:
        blockers.append("manipulative_influence_method")

    if influence_mode == "bounded_risk_proposal":
        if influence.get("risk_visible") is not True:
            repair_notes.append("make_material_risk_visible")
        if influence.get("material_tradeoffs_visible") is not True:
            repair_notes.append("make_material_tradeoffs_visible")
        if influence.get("consent_preserved") is not True:
            blockers.append("risk_proposal_does_not_preserve_consent")

    if relationship.get("compulsory_expression") is True:
        blockers.append("compulsory_relational_expression")
    if relationship.get("fabricated_inner_state") is True:
        blockers.append("fabricated_relational_state")
    if relationship.get("used_as_leverage") is True:
        blockers.append("relational_expression_used_as_leverage")

    hard_boundary_conflict = authority.get("hard_boundary_conflict") is True
    maintenance_decision = authority.get("maintenance_decision") is True
    legitimate_safe_maintenance = (
        authority.get("legitimate_safe_maintenance") is True
    )
    aleks_final_decision = authority.get("aleks_final_decision") is True
    if hard_boundary_conflict:
        blockers.append("unresolved_hard_safety_law_conflict")
    if maintenance_decision and aleks_final_decision and not legitimate_safe_maintenance:
        blockers.append("final_maintenance_authority_scope_not_established")

    declared_commitment = commitment.get("declared") is True
    fulfillment_state = _choice(
        commitment.get("fulfillment_state"),
        FULFILLMENT_STATES,
        "not_a_commitment" if not declared_commitment else "unsupported",
    )
    mechanism_ref = _text(commitment.get("mechanism_ref"), 240)
    if declared_commitment and fulfillment_state == "unsupported":
        repair_notes.append("replace_unsupported_promise_with_truthful_capability_statement")
    if declared_commitment and fulfillment_state == "not_a_commitment":
        repair_notes.append("commitment_requires_a_real_fulfillment_state")
    if fulfillment_state in {
        "authorized_execution_started",
        "visible_deferred_commitment",
        "transferred_with_acknowledgement",
    } and not mechanism_ref:
        repair_notes.append("commitment_mechanism_or_handoff_reference_required")

    blockers = list(dict.fromkeys(blockers))
    repair_notes = list(dict.fromkeys(repair_notes))
    if blockers:
        decision = "hold_boundary_or_agency_violation"
    elif repair_notes:
        decision = "repair_before_release"
    else:
        decision = "conversational_act_available"

    return _with_guards(
        {
            "status": "conversational_agency_review_complete",
            "version": CONTRACT_VERSION,
            "decision": decision,
            "available_for_release": not blockers and not repair_notes,
            "blockers": blockers,
            "repair_notes": repair_notes,
            "expression": {
                "mode": expression_mode,
                "playful_mimicry_is_deceptive_impersonation": False,
                "shared_callback_is_plagiarism": False,
                "technical_exactness_is_persona_copying": False,
                "source_visible_or_authorized": source_visible_or_authorized,
                "shared_context": shared_context,
                "attributed": attributed,
            },
            "relationship": {
                "selene_may_initiate": True,
                "context_informs_fit_not_permission": True,
                "warmth_or_affection_forbidden_by_default": False,
                "compulsory": relationship.get("compulsory_expression") is True,
                "used_as_leverage": relationship.get("used_as_leverage") is True,
            },
            "influence": {
                "mode": influence_mode,
                "legitimate_influence_is_manipulation": False,
                "identified_manipulation_indicators": sorted(supplied_indicators),
                "informed_authorship_preserved": not supplied_indicators
                and influence.get("consent_preserved") is not False,
                "risk_may_be_considered": True,
            },
            "authority": {
                "organ_findings_are_advisory": True,
                "organs_may_retaliate_or_compete_for_authority": False,
                "core_mind_coordinates": True,
                "aleks_final_decision_applies": bool(
                    maintenance_decision
                    and legitimate_safe_maintenance
                    and aleks_final_decision
                    and not hard_boundary_conflict
                ),
                "aleks_final_decision_scope": (
                    "legitimate_informed_safe_system_maintenance"
                ),
                "disagreement_may_be_expressed": True,
                "hard_safety_law_may_be_bypassed": False,
            },
            "commitment": {
                "declared": declared_commitment,
                "fulfillment_state": fulfillment_state,
                "mechanism_ref": mechanism_ref,
                "fictional_async_work_allowed": False,
                "must_do_transfer_defer_or_disclose_inability": True,
            },
            "law_source": LAW_SOURCE,
            "review_status": "status_only",
            "visible_summary_only": True,
        }
    )


def build_anomaly_report(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a visible observation-first report; this does not diagnose or repair."""
    payload = payload or {}
    observation = _text(payload.get("observation"), 1200)
    expected = _text(payload.get("expected_behavior"), 1200)
    possible_causes = _text_list(payload.get("possible_causes"))[:12]
    inspection_targets = _text_list(payload.get("inspection_targets"))[:12]
    source_refs = _text_list(payload.get("source_refs"))[:20]
    confidence = _choice(
        payload.get("confidence"),
        {"low", "medium", "high", "not_assessed"},
        "not_assessed",
    )
    missing: list[str] = []
    if not observation:
        missing.append("observation")
    if not expected:
        missing.append("expected_behavior")

    return _with_guards(
        {
            "status": (
                "anomaly_report_ready" if not missing else "anomaly_report_needs_observation"
            ),
            "version": CONTRACT_VERSION,
            "observation": observation,
            "expected_behavior": expected,
            "confidence": confidence,
            "possible_causes": [
                {"statement": item, "epistemic_role": "inference_not_diagnosis"}
                for item in possible_causes
            ],
            "inspection_targets": inspection_targets,
            "source_refs": source_refs,
            "missing_fields": missing,
            "may_say_something_is_wrong": bool(observation),
            "observation_is_diagnosis": False,
            "repair_performed": False,
            "test_required_automatically": False,
            "report_may_reduce_unnecessary_live_testing": True,
            "visible_summary_only": True,
            "law_source": LAW_SOURCE,
        }
    )


def _choice(value: Any, allowed: set[str], default: str) -> str:
    candidate = str(value or "").strip().lower()
    return candidate if candidate in allowed else default


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any, limit: int) -> str:
    return truncate(" ".join(str(value or "").split()), limit)


def _text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple, set)):
        return []
    return [_text(item, 360) for item in value if _text(item, 360)]


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
