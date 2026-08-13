from __future__ import annotations

import re
from typing import Any

from .conversational_agency import build_anomaly_report, review_conversational_agency
from .registry import truncate


COMMITMENT_ANOMALY_BOUNDARY = (
    "current_turn_commitment_integrity_and_observation_first_anomaly_voice_only_"
    "no_action_memory_identity_personality_governance_authority_or_test_execution"
)

NON_COMMITMENT_ACTS = {"none", "idea", "hope", "plan", "offer", "possibility"}
COMMITMENT_ACTS = {
    "commitment",
    "completion_report",
    "execution_report",
    "handoff_report",
    "capability_disclosure",
}
ANOMALY_KINDS = {
    "lost_thread",
    "missing_capability",
    "code_behavior_mismatch",
    "unsupported_promise",
    "organ_disagreement",
    "unexpected_result",
    "other_observable_anomaly",
}

# This is a narrow final consistency check for claims that an external or
# persistent action happened or will happen.  It is not an intent classifier.
_DIRECT_EXTERNAL_ACTION_VERBS = (
    "send|schedule|install|update|fix|delete|submit|contact|email|text|reinstall|"
    "save|queue|launch|upload|publish|deploy"
)
_DIRECT_EXTERNAL_ACTION_PAST = (
    "sent|scheduled|installed|updated|fixed|deleted|submitted|contacted|emailed|"
    "texted|reinstalled|saved|queued|launched|uploaded|published|deployed"
)
_AMBIGUOUS_STATE_VERBS = "create|build|change|write|start"
_AMBIGUOUS_STATE_PAST = "created|built|changed|written|started"
_EXTERNAL_OBJECTS = (
    "file|code|repo|repository|database|document|app|application|project|website|"
    "server|configuration|config|installation|build|commit|branch|job|process|"
    "task|deployment|poller|message|email|update"
)
_UNSUPPORTED_FUTURE_ACTION = re.compile(
    rf"\b(?:i\s+will|i['’]ll|i\s+am\s+going\s+to|i['’]m\s+going\s+to)\s+"
    rf"(?:\w+\s+){{0,2}}(?:"
    rf"(?:{_DIRECT_EXTERNAL_ACTION_VERBS})\b|"
    rf"(?:{_AMBIGUOUS_STATE_VERBS})\s+(?:\w+\s+){{0,2}}(?:{_EXTERNAL_OBJECTS})\b"
    rf")",
    re.IGNORECASE,
)
_UNSUPPORTED_COMPLETION_CLAIM = re.compile(
    rf"\b(?:i\s+have|i['’]ve|i)\s+(?:just|now|already|successfully)\s+"
    rf"(?:\w+\s+){{0,2}}(?:"
    rf"(?:{_DIRECT_EXTERNAL_ACTION_PAST})\b|"
    rf"(?:{_AMBIGUOUS_STATE_PAST})\s+(?:\w+\s+){{0,2}}(?:{_EXTERNAL_OBJECTS})\b"
    rf")",
    re.IGNORECASE,
)

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
    "repair_performed": False,
    "test_started": False,
    "automatic_cocoon_route": False,
}


def commitment_anomaly_coordination_status() -> dict[str, Any]:
    return _locked(
        {
            "status": "commitment_integrity_and_anomaly_voice_ready",
            "version": "v1_real_commitments_and_observation_first_anomaly_voice",
            "non_commitment_acts": sorted(NON_COMMITMENT_ACTS),
            "commitment_acts": sorted(COMMITMENT_ACTS),
            "fulfillment_states": [
                "not_a_commitment",
                "performed_now",
                "authorized_execution_started",
                "visible_deferred_commitment",
                "transferred_with_acknowledgement",
                "cannot_execute_disclosed",
            ],
            "anomaly_kinds": sorted(ANOMALY_KINDS),
            "plan_or_offer_is_automatically_a_commitment": False,
            "unsupported_background_work_allowed": False,
            "observable_anomaly_may_be_reported_without_diagnosis": True,
            "explanation_required_by_default": False,
            "ordinary_wrongness_is_identity_failure": False,
            "visible_summary_only": True,
        }
    )


def build_commitment_anomaly_coordination(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    commitment = _dict(payload.get("commitment_input") or payload.get("commitment"))
    action = _dict(payload.get("action_handoff"))
    anomaly = _dict(payload.get("anomaly_input") or payload.get("anomaly"))

    speech_act = str(commitment.get("speech_act") or "none").strip().lower()
    if speech_act not in NON_COMMITMENT_ACTS | COMMITMENT_ACTS:
        speech_act = "none"
    declared = commitment.get("declared") is True or speech_act in COMMITMENT_ACTS
    if speech_act in NON_COMMITMENT_ACTS:
        declared = False

    requested_state = str(
        commitment.get("fulfillment_state")
        or action.get("fulfillment_state")
        or "not_a_commitment"
    ).strip().lower()
    mechanism_ref = _text(
        commitment.get("mechanism_ref") or action.get("mechanism_ref"), 240
    )
    evidence_ref = _text(
        commitment.get("evidence_ref")
        or action.get("result_ref")
        or action.get("evidence_ref"),
        240,
    )
    result_visible = (
        commitment.get("result_visible") is True
        or action.get("result_visible") is True
        or bool(evidence_ref)
    )
    execution_authorized = (
        commitment.get("execution_authorized") is True
        or action.get("authorized") is True
    )
    handoff_acknowledged = (
        commitment.get("handoff_acknowledged") is True
        or action.get("acknowledged") is True
    )
    deferred_visible = (
        commitment.get("deferred_state_visible") is True
        or action.get("deferred_state_visible") is True
        or bool(_text(action.get("schedule_ref"), 240))
    )
    limitation = _text(
        commitment.get("limitation") or action.get("limitation"), 600
    )

    effective_state = requested_state if declared else "not_a_commitment"
    support_missing: list[str] = []
    if declared and requested_state == "performed_now" and not result_visible:
        support_missing.append("visible_result_or_evidence_reference")
    elif declared and requested_state == "authorized_execution_started":
        if not execution_authorized:
            support_missing.append("execution_authorization")
        if not mechanism_ref:
            support_missing.append("execution_mechanism_reference")
    elif declared and requested_state == "visible_deferred_commitment":
        if not mechanism_ref:
            support_missing.append("deferred_mechanism_reference")
        if not deferred_visible:
            support_missing.append("visible_deferred_state")
    elif declared and requested_state == "transferred_with_acknowledgement":
        if not mechanism_ref:
            support_missing.append("handoff_reference")
        if not handoff_acknowledged:
            support_missing.append("handoff_acknowledgement")
    elif declared and requested_state == "cannot_execute_disclosed" and not limitation:
        support_missing.append("visible_capability_limitation")

    agency_review = review_conversational_agency(
        {
            "commitment": {
                "declared": declared,
                "fulfillment_state": (
                    requested_state if declared else "not_a_commitment"
                ),
                "mechanism_ref": mechanism_ref if declared else "",
            }
        }
    )
    repair_notes = list(agency_review.get("repair_notes") or [])
    if support_missing:
        repair_notes.append("replace_state_claim_with_truthful_current_capability")
        effective_state = "unsupported"

    anomaly_kind = str(anomaly.get("kind") or "").strip().lower()
    if anomaly_kind not in ANOMALY_KINDS:
        anomaly_kind = "other_observable_anomaly" if anomaly else "none"
    anomaly_report = (
        build_anomaly_report(anomaly)
        if anomaly
        else {
            "status": "no_anomaly_observation_supplied",
            "observation": "",
            "expected_behavior": "",
            "possible_causes": [],
            "missing_fields": [],
            "may_say_something_is_wrong": False,
        }
    )
    visible_report_requested = (
        anomaly.get("visible_report_requested") is True
        or anomaly.get("expression_requested") is True
    )
    visible_anomaly_text = _anomaly_expression(
        anomaly_report,
        include_inference=anomaly.get("include_possible_cause") is True,
    )
    anomaly_ready = anomaly_report.get("status") == "anomaly_report_ready"

    repair_notes = list(dict.fromkeys(repair_notes))
    if support_missing:
        commitment_decision = "repair_unsupported_commitment_before_release"
    elif agency_review.get("decision") != "conversational_act_available":
        commitment_decision = str(agency_review.get("decision") or "repair_before_release")
    elif declared:
        commitment_decision = "commitment_state_supported"
    else:
        commitment_decision = "no_commitment_declared"

    return _locked(
        {
            "status": "commitment_integrity_and_anomaly_coordination_complete",
            "version": "v1_real_commitments_and_observation_first_anomaly_voice",
            "commitment": {
                "speech_act": speech_act,
                "declared": declared,
                "plan_hope_or_offer_is_commitment": False,
                "requested_fulfillment_state": requested_state,
                "effective_fulfillment_state": effective_state,
                "decision": commitment_decision,
                "mechanism_ref": mechanism_ref,
                "evidence_ref": evidence_ref,
                "result_visible": result_visible,
                "execution_authorized": execution_authorized,
                "deferred_state_visible": deferred_visible,
                "handoff_acknowledged": handoff_acknowledged,
                "limitation": limitation,
                "missing_support": support_missing,
                "repair_notes": repair_notes,
                "release_supported": not support_missing
                and agency_review.get("available_for_release") is True,
                "fictional_async_work_allowed": False,
            },
            "anomaly": {
                "kind": anomaly_kind,
                "observed": bool(anomaly),
                "report_ready": anomaly_ready,
                "visible_report_requested": visible_report_requested,
                "visible_expression": visible_anomaly_text if anomaly_ready else "",
                "observation_is_diagnosis": False,
                "possible_causes_are_inference": True,
                "explanation_required_by_default": False,
                "ordinary_gap_or_wrongness_is_identity_failure": False,
                "report": anomaly_report,
            },
            "nlo_expression_guidance": {
                "commitment_wording_must_match_effective_state": True,
                "unsupported_state_claim_requires_truthful_capability_language": True,
                "anomaly_may_be_stated_concisely": True,
                "visible_anomaly_text": (
                    visible_anomaly_text
                    if anomaly_ready and visible_report_requested
                    else ""
                ),
                "compulsory_apology": False,
                "compulsory_self_explanation": False,
                "compulsory_question": False,
                "shame_or_failure_language_required": False,
            },
            "visible_summary_only": True,
        }
    )


def inspect_visible_commitment_claim(
    candidate_text: str,
    coordination: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Check only visible state-changing claims against the structured handoff."""
    text = _text(candidate_text, 5000)
    coordination = coordination or {}
    commitment = _dict(coordination.get("commitment"))
    future_claim = bool(_UNSUPPORTED_FUTURE_ACTION.search(text))
    completion_claim = bool(_UNSUPPORTED_COMPLETION_CLAIM.search(text))
    state_claim_present = future_claim or completion_claim
    supported = commitment.get("release_supported") is True
    effective = str(commitment.get("effective_fulfillment_state") or "not_a_commitment")
    if completion_claim:
        supported = supported and effective in {
            "performed_now",
            "authorized_execution_started",
            "transferred_with_acknowledgement",
        }
    elif future_claim:
        supported = supported and effective in {
            "authorized_execution_started",
            "visible_deferred_commitment",
        }
    release_allowed = not state_claim_present or supported
    return _locked(
        {
            "status": (
                "visible_commitment_claim_supported"
                if release_allowed
                else "visible_commitment_claim_unsupported"
            ),
            "state_changing_claim_present": state_claim_present,
            "future_action_claim_present": future_claim,
            "completion_claim_present": completion_claim,
            "structured_support_present": supported,
            "effective_fulfillment_state": effective,
            "release_allowed": release_allowed,
            "issue": "" if release_allowed else "unsupported_real_world_action_claim",
            "truthful_fall": (
                "I can help with that here, but I cannot honestly say the action has "
                "started or finished without a real execution path."
                if not release_allowed
                else ""
            ),
            "ordinary_plan_offer_or_idea_was_inspected_as_commitment": False,
            "visible_summary_only": True,
        }
    )


def realize_commitment_anomaly_voice(
    candidate_text: str,
    coordination: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Surface an explicitly requested, observation-ready anomaly report."""
    coordination = coordination or {}
    guidance = _dict(coordination.get("nlo_expression_guidance"))
    anomaly_text = _text(guidance.get("visible_anomaly_text"), 2400)
    activated = bool(anomaly_text)
    original = str(candidate_text or "")
    if len(original) > 5000:
        original = original[:4997].rstrip() + "..."
    return _locked(
        {
            "status": (
                "observation_first_anomaly_voice_realized"
                if activated
                else "commitment_anomaly_voice_not_needed"
            ),
            "activated": activated,
            "candidate_text": anomaly_text if activated else original,
            "meaning_changed": False,
            "anomaly_diagnosed": False,
            "commitment_state_upgraded": False,
            "explanation_added_without_request": False,
            "visible_summary_only": True,
        }
    )


def _anomaly_expression(report: dict[str, Any], *, include_inference: bool) -> str:
    observation = _text(report.get("observation"), 1200)
    expected = _text(report.get("expected_behavior"), 1200)
    if not observation or not expected:
        return ""
    text = f"Something looks off: {observation} I expected {expected}"
    possible = report.get("possible_causes") or []
    if include_inference and possible and isinstance(possible[0], dict):
        cause = _text(possible[0].get("statement"), 600)
        if cause:
            text += f" My current best explanation is {cause}, but that is an inference, not a diagnosis."
    if not text.endswith((".", "!", "?")):
        text += "."
    return text


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text(value: Any, limit: int) -> str:
    return truncate(" ".join(str(value or "").split()), limit)


def _locked(result: dict[str, Any]) -> dict[str, Any]:
    return {
        **result,
        **GUARDS,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": COMMITMENT_ANOMALY_BOUNDARY,
    }
