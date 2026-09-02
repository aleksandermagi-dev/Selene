from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime
from typing import Any

from .conversational_agency import build_anomaly_report, review_conversational_agency
from .registry import truncate


COMMITMENT_ANOMALY_BOUNDARY = (
    "current_turn_commitment_integrity_and_observation_first_anomaly_voice_only_"
    "no_action_memory_identity_personality_governance_authority_or_test_execution"
)
COMMITMENT_LIFECYCLE_VERSION = "v2_phase8c_explicit_goal_capability_lineage"
COMMITMENT_LIFECYCLE_BOUNDARY = (
    "explicit_commitment_goal_and_capability_lineage_only_no_implicit_promise_"
    "capability_grant_background_work_or_silent_completion"
)
COMMITMENT_LIFECYCLE_STATES = {
    "accepted",
    "in_progress",
    "fulfilled",
    "blocked",
    "released",
    "closed",
}
COMMITMENT_TERMINAL_STATES = {"fulfilled", "released", "closed"}
COMMITMENT_TRANSITIONS = {
    "accepted": {"in_progress", "fulfilled", "blocked", "released", "closed"},
    "in_progress": {"fulfilled", "blocked", "released", "closed"},
    "blocked": {"in_progress", "released", "closed"},
}
GRADUATED_CAPABILITIES = (
    "conversation",
    "study",
    "memory_proposal",
    "tools",
    "tendril",
    "future_embodiment",
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
            "version": COMMITMENT_LIFECYCLE_VERSION,
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


def record_commitment_acceptance(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    if payload.get("accept_commitment") is not True:
        raise ValueError("accept_commitment must be explicitly true")
    if str(payload.get("speech_act") or "").strip().lower() != "commitment":
        raise ValueError("speech_act must be an explicit commitment")
    event = _base_commitment_event(payload, lifecycle_state="accepted")
    existing = _event_by_idempotency(conn, event["idempotency_key"])
    if existing:
        _assert_idempotent_event_matches(existing, event)
        return _event_result(existing, idempotent_replay=True)
    if _latest_commitment_event(conn, event["commitment_key"]):
        raise ValueError("commitment_key already exists; use an explicit lifecycle transition")
    goal = _typed_goal(conn, event["goal_key"])
    if not goal:
        raise ValueError("goal_key must identify an existing typed goal")
    if str(goal["scope_kind"] or "") != event["capability"]:
        raise ValueError("commitment capability must match its typed goal lineage")
    if str(goal["lifecycle_state"] or "") in {"completed", "closed", "superseded"}:
        raise ValueError("a terminal typed goal cannot accept a new commitment")
    event["goal_id"] = int(goal["id"])
    event_id = _insert_commitment_event(conn, event)
    event["root_event_id"] = event_id
    event["event_id"] = event_id
    event["recorded_in_lifecycle_shelf"] = True
    conn.execute(
        "UPDATE selene_commitment_lifecycles SET root_event_id = ?, payload_json = ? WHERE id = ?",
        (event_id, json.dumps(event), event_id),
    )
    conn.commit()
    return _locked(
        {
            "status": "commitment_lifecycle_event_recorded",
            "event_id": event_id,
            "idempotent_replay": False,
            "event": event,
            "resident_content_exposed": False,
        }
    )


def transition_commitment_lifecycle(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    if payload.get("transition_commitment") is not True:
        raise ValueError("transition_commitment must be explicitly true")
    idempotency_key = _required_text(payload, "idempotency_key", 240)
    commitment_key = _required_text(payload, "commitment_key", 180)
    goal_key = _required_text(payload, "goal_key", 180)
    capability = _required_text(payload, "capability", 80).lower()
    next_state = str(payload.get("lifecycle_state") or "").strip().lower()
    source_refs = _required_list(payload, "source_refs")
    existing = _event_by_idempotency(conn, idempotency_key)
    if existing:
        _assert_idempotent_event_matches(
            existing,
            {
                "commitment_key": commitment_key,
                "goal_key": goal_key,
                "capability": capability,
                "lifecycle_state": next_state,
                "source_refs": source_refs,
                "mechanism_ref": _text(payload.get("mechanism_ref"), 240),
                "result_refs": _text_list(payload.get("result_refs"), 360, 30),
                "blocker": _text(payload.get("blocker"), 1000),
                "stop_reason": _text(payload.get("stop_reason"), 1000),
            },
            compare_optional_only=True,
        )
        return _event_result(existing, idempotent_replay=True)
    latest = _latest_commitment_event(conn, commitment_key)
    if not latest:
        raise ValueError("commitment_key has no accepted lifecycle")
    current_state = str(latest["lifecycle_state"] or "")
    if current_state in COMMITMENT_TERMINAL_STATES:
        raise ValueError("terminal commitment cannot reopen; accept a new explicit commitment")
    if next_state not in COMMITMENT_TRANSITIONS.get(current_state, set()):
        raise ValueError(f"unsupported commitment transition: {current_state} -> {next_state}")
    if goal_key != str(latest["goal_key"] or "") or capability != str(latest["capability"] or ""):
        raise ValueError("commitment transition must preserve exact goal and capability lineage")
    mechanism_ref = _text(payload.get("mechanism_ref") or latest["mechanism_ref"], 240)
    result_refs = _text_list(payload.get("result_refs"), 360, 30)
    blocker = _text(payload.get("blocker"), 1000)
    stop_reason = _text(payload.get("stop_reason"), 1000)
    if next_state == "in_progress" and not mechanism_ref:
        raise ValueError("mechanism_ref is required before a commitment is in progress")
    if next_state == "fulfilled" and not result_refs:
        raise ValueError("result_refs are required before a commitment is fulfilled")
    if next_state == "blocked" and not blocker:
        raise ValueError("blocker is required for a blocked commitment")
    if next_state in COMMITMENT_TERMINAL_STATES | {"blocked"} and not stop_reason:
        raise ValueError("stop_reason is required for a stopped commitment state")
    event = {
        "status": "commitment_lifecycle_event_ready",
        "version": COMMITMENT_LIFECYCLE_VERSION,
        "commitment_key": commitment_key,
        "commitment_claim": str(latest["commitment_claim"] or ""),
        "speech_act": "commitment",
        "goal_id": int(latest["goal_id"]),
        "goal_key": goal_key,
        "capability": capability,
        "lifecycle_state": next_state,
        "mechanism_ref": mechanism_ref,
        "result_refs": result_refs,
        "blocker": blocker,
        "stop_reason": stop_reason,
        "parent_event_id": int(latest["id"]),
        "root_event_id": int(latest["root_event_id"] or latest["id"]),
        "idempotency_key": idempotency_key,
        "source_refs": source_refs,
        "commitment_is_capability_grant": False,
        "execution_started_by_lifecycle": False,
        "stopping_receipt": _commitment_stop(next_state, stop_reason),
        "created_at": datetime.now(UTC).isoformat(),
    }
    event_id = _insert_commitment_event(conn, event)
    event["event_id"] = event_id
    event["recorded_in_lifecycle_shelf"] = True
    conn.execute(
        "UPDATE selene_commitment_lifecycles SET payload_json = ? WHERE id = ?",
        (json.dumps(event), event_id),
    )
    conn.commit()
    return _locked(
        {
            "status": "commitment_lifecycle_event_recorded",
            "event_id": event_id,
            "idempotent_replay": False,
            "event": event,
            "resident_content_exposed": False,
        }
    )


def commitment_lifecycle_status(conn: sqlite3.Connection) -> dict[str, Any]:
    latest = _latest_commitment_rows(conn)
    states = [str(row["lifecycle_state"] or "") for row in latest]
    return _locked(
        {
            "status": "commitment_lifecycle_status_ready",
            "version": COMMITMENT_LIFECYCLE_VERSION,
            "commitment_count": len(latest),
            "active_commitment_count": sum(state in {"accepted", "in_progress"} for state in states),
            "blocked_commitment_count": sum(state == "blocked" for state in states),
            "terminal_commitment_count": sum(state in COMMITMENT_TERMINAL_STATES for state in states),
            "state_counts": {state: states.count(state) for state in sorted(COMMITMENT_LIFECYCLE_STATES)},
            "explicit_acceptance_required": True,
            "result_evidence_required_for_fulfillment": True,
            "resident_content_exposed": False,
        }
    )


def list_commitment_lifecycles(
    conn: sqlite3.Connection,
    limit: int = 50,
) -> dict[str, Any]:
    rows = _latest_commitment_rows(conn)[: max(1, min(int(limit), 100))]
    return _locked(
        {
            "status": "commitment_lifecycles_ready",
            "items": [_decode_commitment_row(row) for row in rows],
            "maximum_items": 100,
            "visible_summary_only": True,
        }
    )


def build_capability_graduation_receipts(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    tool_grants = _reported_grants(payload.get("reported_tool_grants"))
    tendril_grants = _reported_grants(payload.get("reported_tendril_grants"))
    receipts = [
        _graduation(
            "conversation",
            "mature_responsive_current_turn",
            downstream_owner_required=False,
            permitted_move="answer_ask_suggest_explore_wait_quiet_or_close",
        ),
        _graduation(
            "study",
            "available_via_explicit_study_lifecycle",
            downstream_owner_required=True,
            permitted_move="select_study_lifecycle_only",
        ),
        {
            **_graduation(
                "memory_proposal",
                "proposal_only_via_privacy_and_review_gate",
                downstream_owner_required=True,
                permitted_move="propose_for_review_only",
            ),
            "automatic_durable_memory": False,
        },
        {
            **_graduation(
                "tools",
                "reported_named_grant_requires_verification" if tool_grants else "named_grant_required",
                downstream_owner_required=True,
                permitted_move="named_tool_only_after_downstream_verification",
            ),
            "reported_grants": tool_grants,
        },
        {
            **_graduation(
                "tendril",
                "reported_named_grant_requires_verification" if tendril_grants else "specific_tendril_grant_required",
                downstream_owner_required=True,
                permitted_move="specific_tendril_only_after_downstream_verification",
            ),
            "reported_grants": tendril_grants,
        },
        _graduation(
            "future_embodiment",
            "deferred_unavailable",
            downstream_owner_required=True,
            permitted_move="none_until_real_substrate_and_later_phase",
        ),
    ]
    return _locked(
        {
            "status": "capability_specific_graduation_receipts_ready",
            "version": COMMITMENT_LIFECYCLE_VERSION,
            "receipts": receipts,
            "capability_order": list(GRADUATED_CAPABILITIES),
            "aggregate_autonomy_state_created": False,
            "reported_grant_is_verified_authority": False,
            "external_action_started": False,
            "writes_records": False,
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
    lifecycle = _normalize_lifecycle_event(payload.get("commitment_lifecycle_event"))

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
            "version": COMMITMENT_LIFECYCLE_VERSION,
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
            "commitment_lifecycle": lifecycle,
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
    lifecycle = _dict(coordination.get("commitment_lifecycle"))
    future_claim = bool(_UNSUPPORTED_FUTURE_ACTION.search(text))
    completion_claim = bool(_UNSUPPORTED_COMPLETION_CLAIM.search(text))
    state_claim_present = future_claim or completion_claim
    lifecycle_state = str(lifecycle.get("lifecycle_state") or "")
    lifecycle_result_refs = _text_list(lifecycle.get("result_refs"), 360, 30)
    lifecycle_support = bool(
        lifecycle.get("status") == "commitment_lifecycle_event_ready"
        and lifecycle.get("recorded_in_lifecycle_shelf") is True
        and isinstance(lifecycle.get("event_id"), int)
        and lifecycle.get("event_id", 0) > 0
        and lifecycle.get("goal_key")
        and lifecycle.get("capability")
    )
    supported = commitment.get("release_supported") is True or lifecycle_support
    effective = str(commitment.get("effective_fulfillment_state") or "not_a_commitment")
    if completion_claim:
        supported = (
            lifecycle_support
            and lifecycle_state == "fulfilled"
            and bool(lifecycle_result_refs)
        ) or (
            commitment.get("release_supported") is True
            and effective in {
                "performed_now",
                "authorized_execution_started",
                "transferred_with_acknowledgement",
            }
        )
    elif future_claim:
        supported = (
            lifecycle_support
            and lifecycle_state in {"accepted", "in_progress"}
            and bool(lifecycle.get("mechanism_ref"))
        ) or (
            commitment.get("release_supported") is True
            and effective in {
                "authorized_execution_started",
                "visible_deferred_commitment",
            }
        )
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
            "lifecycle_support_used": lifecycle_support,
            "effective_fulfillment_state": lifecycle_state if lifecycle_support else effective,
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


def _base_commitment_event(payload: dict[str, Any], *, lifecycle_state: str) -> dict[str, Any]:
    source_refs = _required_list(payload, "source_refs")
    stop_conditions = _required_list(payload, "stop_conditions")
    mechanism_ref = _required_text(payload, "mechanism_ref", 240)
    return {
        "status": "commitment_lifecycle_event_ready",
        "version": COMMITMENT_LIFECYCLE_VERSION,
        "commitment_key": _required_text(payload, "commitment_key", 180),
        "commitment_claim": _required_text(payload, "commitment_claim", 1200),
        "speech_act": "commitment",
        "goal_id": 0,
        "goal_key": _required_text(payload, "goal_key", 180),
        "capability": _required_text(payload, "capability", 80).lower(),
        "lifecycle_state": lifecycle_state,
        "mechanism_ref": mechanism_ref,
        "result_refs": [],
        "blocker": "",
        "stop_reason": "",
        "stop_conditions": stop_conditions,
        "parent_event_id": None,
        "root_event_id": None,
        "idempotency_key": _required_text(payload, "idempotency_key", 240),
        "source_refs": source_refs,
        "commitment_is_capability_grant": False,
        "execution_started_by_lifecycle": False,
        "stopping_receipt": _commitment_stop(lifecycle_state, ""),
        "created_at": datetime.now(UTC).isoformat(),
    }


def _typed_goal(conn: sqlite3.Connection, goal_key: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT id, goal_key, scope_kind, lifecycle_state FROM c_runtime_goal_drive_records "
        "WHERE goal_key = ? AND goal_key != ''",
        (goal_key,),
    ).fetchone()


def _event_by_idempotency(conn: sqlite3.Connection, key: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM selene_commitment_lifecycles WHERE idempotency_key = ?",
        (key,),
    ).fetchone()


def _latest_commitment_event(conn: sqlite3.Connection, key: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM selene_commitment_lifecycles WHERE commitment_key = ? "
        "ORDER BY id DESC LIMIT 1",
        (key,),
    ).fetchone()


def _latest_commitment_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT events.* FROM selene_commitment_lifecycles AS events "
        "JOIN (SELECT commitment_key, MAX(id) AS latest_id "
        "      FROM selene_commitment_lifecycles GROUP BY commitment_key) AS latest "
        "ON latest.latest_id = events.id ORDER BY events.id DESC"
    ).fetchall()


def _insert_commitment_event(conn: sqlite3.Connection, event: dict[str, Any]) -> int:
    cursor = conn.execute(
        """
        INSERT INTO selene_commitment_lifecycles(
          commitment_key, commitment_claim, speech_act, goal_id, goal_key,
          capability, lifecycle_state, mechanism_ref, result_refs, blocker,
          stop_reason, parent_event_id, root_event_id, idempotency_key,
          source_refs, provenance_boundary, review_status, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["commitment_key"],
            event["commitment_claim"],
            event["speech_act"],
            event["goal_id"],
            event["goal_key"],
            event["capability"],
            event["lifecycle_state"],
            event["mechanism_ref"],
            json.dumps(event["result_refs"]),
            event["blocker"],
            event["stop_reason"],
            event["parent_event_id"],
            event["root_event_id"],
            event["idempotency_key"],
            json.dumps(event["source_refs"]),
            COMMITMENT_LIFECYCLE_BOUNDARY,
            "explicit_commitment_lifecycle",
            json.dumps(event),
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def _decode_commitment_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "event_id": int(row["id"]),
        "commitment_key": str(row["commitment_key"] or ""),
        "commitment_claim": str(row["commitment_claim"] or ""),
        "goal_key": str(row["goal_key"] or ""),
        "capability": str(row["capability"] or ""),
        "lifecycle_state": str(row["lifecycle_state"] or ""),
        "mechanism_ref": str(row["mechanism_ref"] or ""),
        "result_refs": _text_list(row["result_refs"], 360, 30),
        "blocker": str(row["blocker"] or ""),
        "stop_reason": str(row["stop_reason"] or ""),
        "parent_event_id": int(row["parent_event_id"]) if row["parent_event_id"] is not None else None,
        "root_event_id": int(row["root_event_id"]) if row["root_event_id"] is not None else None,
        "source_refs": _text_list(row["source_refs"], 360, 30),
        "stopping_receipt": _commitment_stop(str(row["lifecycle_state"] or ""), str(row["stop_reason"] or "")),
        "commitment_is_capability_grant": False,
        "execution_started_by_lifecycle": False,
    }


def _event_result(row: sqlite3.Row, *, idempotent_replay: bool) -> dict[str, Any]:
    event = _decode_commitment_row(row)
    event["status"] = "commitment_lifecycle_event_ready"
    event["version"] = COMMITMENT_LIFECYCLE_VERSION
    event["recorded_in_lifecycle_shelf"] = True
    return _locked(
        {
            "status": "commitment_lifecycle_event_recorded",
            "event_id": int(row["id"]),
            "idempotent_replay": idempotent_replay,
            "event": event,
            "resident_content_exposed": False,
        }
    )


def _commitment_stop(state: str, reason: str) -> dict[str, Any]:
    terminal = state in COMMITMENT_TERMINAL_STATES
    return {
        "terminal": terminal,
        "reason": reason or ("commitment_remains_visible" if not terminal else "terminal_state_recorded"),
        "silent_disappearance_allowed": False,
        "reopen_same_lineage_allowed": False if terminal else True,
    }


def _graduation(
    capability: str,
    state: str,
    *,
    downstream_owner_required: bool,
    permitted_move: str,
) -> dict[str, Any]:
    return {
        "capability": capability,
        "state": state,
        "permitted_move": permitted_move,
        "downstream_owner_required": downstream_owner_required,
        "downstream_authority_recheck_required": downstream_owner_required,
        "receipt_is_action_authority": False,
        "whole_system_authority_inherited": False,
    }


def _reported_grants(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, str]] = []
    for raw in value[:8]:
        item = _dict(raw)
        capability = _text(item.get("capability"), 120)
        grant_ref = _text(item.get("grant_ref"), 240)
        scope = _text(item.get("scope"), 600)
        if capability and grant_ref and scope:
            result.append({"capability": capability, "grant_ref": grant_ref, "scope": scope})
    return result


def _normalize_lifecycle_event(value: Any) -> dict[str, Any]:
    item = _dict(value)
    state = str(item.get("lifecycle_state") or "")
    if (
        item.get("status") != "commitment_lifecycle_event_ready"
        or state not in COMMITMENT_LIFECYCLE_STATES
        or not item.get("commitment_key")
        or not item.get("goal_key")
        or not item.get("capability")
        or item.get("recorded_in_lifecycle_shelf") is not True
        or not isinstance(item.get("event_id"), int)
        or item.get("event_id", 0) <= 0
    ):
        return {}
    return {
        "status": "commitment_lifecycle_event_ready",
        "event_id": int(item["event_id"]),
        "recorded_in_lifecycle_shelf": True,
        "commitment_key": str(item["commitment_key"]),
        "goal_key": str(item["goal_key"]),
        "capability": str(item["capability"]),
        "lifecycle_state": state,
        "mechanism_ref": _text(item.get("mechanism_ref"), 240),
        "result_refs": _text_list(item.get("result_refs"), 360, 30),
        "blocker": _text(item.get("blocker"), 1000),
        "stop_reason": _text(item.get("stop_reason"), 1000),
        "commitment_is_capability_grant": False,
    }


def _assert_idempotent_event_matches(
    row: sqlite3.Row,
    expected: dict[str, Any],
    *,
    compare_optional_only: bool = False,
) -> None:
    recorded = _decode_commitment_row(row)
    required_fields = ("commitment_key", "goal_key", "capability", "lifecycle_state")
    for field in required_fields:
        if str(recorded.get(field) or "") != str(expected.get(field) or ""):
            raise ValueError("idempotency_key already belongs to a different commitment event")
    comparable_fields = (
        "commitment_claim",
        "mechanism_ref",
        "result_refs",
        "blocker",
        "stop_reason",
        "source_refs",
    )
    for field in comparable_fields:
        wanted = expected.get(field)
        if compare_optional_only and wanted in (None, "", []):
            continue
        if recorded.get(field) != wanted:
            raise ValueError("idempotency_key replay payload does not match the recorded event")


def _required_text(payload: dict[str, Any], key: str, limit: int) -> str:
    value = _text(payload.get(key), limit)
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _required_list(payload: dict[str, Any], key: str) -> list[str]:
    values = _text_list(payload.get(key), 360, 30)
    if not values:
        raise ValueError(f"{key} must contain at least one value")
    return values


def _text_list(value: Any, item_limit: int, count_limit: int) -> list[str]:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            decoded = [value]
        value = decoded
    if not isinstance(value, (list, tuple, set)):
        return []
    return [
        _text(item, item_limit)
        for item in value
        if _text(item, item_limit)
    ][:count_limit]


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
