from __future__ import annotations

import pytest

from selene.commitment_anomaly_coordination import (
    build_commitment_anomaly_coordination,
    commitment_anomaly_coordination_status,
    inspect_visible_commitment_claim,
    realize_commitment_anomaly_voice,
)
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_bounded(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["external_action_started"] is False
    assert result["fact_generation_allowed"] is False
    assert result["repair_performed"] is False
    assert result["test_started"] is False
    assert result["automatic_cocoon_route"] is False
    assert result["hidden_chain_of_thought_exposed"] is False


def test_status_keeps_real_commitments_and_anomaly_voice_bounded():
    status = commitment_anomaly_coordination_status()

    assert status["status"] == "commitment_integrity_and_anomaly_voice_ready"
    assert status["plan_or_offer_is_automatically_a_commitment"] is False
    assert status["unsupported_background_work_allowed"] is False
    assert status["observable_anomaly_may_be_reported_without_diagnosis"] is True
    assert status["explanation_required_by_default"] is False
    assert status["ordinary_wrongness_is_identity_failure"] is False
    _assert_bounded(status)


@pytest.mark.parametrize("speech_act", ["idea", "hope", "plan", "offer", "possibility"])
def test_idea_plan_hope_and_offer_are_not_silently_promoted_to_commitments(speech_act):
    result = build_commitment_anomaly_coordination(
        {
            "commitment_input": {
                "speech_act": speech_act,
                "declared": True,
                "fulfillment_state": "visible_deferred_commitment",
            }
        }
    )

    commitment = result["commitment"]
    assert commitment["declared"] is False
    assert commitment["effective_fulfillment_state"] == "not_a_commitment"
    assert commitment["decision"] == "no_commitment_declared"
    assert commitment["plan_hope_or_offer_is_commitment"] is False


def test_performed_now_requires_visible_result_or_evidence_reference():
    unsupported = build_commitment_anomaly_coordination(
        {
            "commitment_input": {
                "speech_act": "completion_report",
                "fulfillment_state": "performed_now",
            }
        }
    )
    supported = build_commitment_anomaly_coordination(
        {
            "commitment_input": {
                "speech_act": "completion_report",
                "fulfillment_state": "performed_now",
            },
            "action_handoff": {
                "result_visible": True,
                "result_ref": "current_response:verified_result",
            },
        }
    )

    assert unsupported["commitment"]["release_supported"] is False
    assert "visible_result_or_evidence_reference" in unsupported["commitment"]["missing_support"]
    assert supported["commitment"]["release_supported"] is True
    assert supported["commitment"]["effective_fulfillment_state"] == "performed_now"


def test_started_deferred_and_transferred_states_require_their_real_mechanisms():
    started = build_commitment_anomaly_coordination(
        {
            "commitment_input": {
                "speech_act": "execution_report",
                "fulfillment_state": "authorized_execution_started",
            },
            "action_handoff": {
                "authorized": True,
                "mechanism_ref": "local_job:17",
            },
        }
    )
    deferred = build_commitment_anomaly_coordination(
        {
            "commitment_input": {
                "speech_act": "commitment",
                "fulfillment_state": "visible_deferred_commitment",
            },
            "action_handoff": {
                "mechanism_ref": "scheduler:lesson-review",
                "schedule_ref": "schedule:2026-08-14T10:00",
            },
        }
    )
    transferred = build_commitment_anomaly_coordination(
        {
            "commitment_input": {
                "speech_act": "handoff_report",
                "fulfillment_state": "transferred_with_acknowledgement",
            },
            "action_handoff": {
                "mechanism_ref": "handoff:core-mind:8",
                "acknowledged": True,
            },
        }
    )

    for result in (started, deferred, transferred):
        assert result["commitment"]["release_supported"] is True
        assert result["commitment"]["fictional_async_work_allowed"] is False
        _assert_bounded(result)


def test_disclosed_inability_is_truthful_and_does_not_require_shame_or_apology():
    result = build_commitment_anomaly_coordination(
        {
            "commitment_input": {
                "speech_act": "capability_disclosure",
                "fulfillment_state": "cannot_execute_disclosed",
                "limitation": "No external execution route is available in this turn.",
            }
        }
    )

    assert result["commitment"]["release_supported"] is True
    assert result["commitment"]["limitation"].startswith("No external execution route")
    assert result["nlo_expression_guidance"]["compulsory_apology"] is False
    assert result["nlo_expression_guidance"]["shame_or_failure_language_required"] is False


def test_anomaly_report_names_observation_without_diagnosis_or_automatic_repair():
    result = build_commitment_anomaly_coordination(
        {
            "anomaly_input": {
                "kind": "lost_thread",
                "observation": "The second question disappeared from the response.",
                "expected_behavior": "Both questions should remain open until answered.",
                "confidence": "high",
                "possible_causes": ["The obligation handoff may have dropped one item."],
                "visible_report_requested": True,
            }
        }
    )

    anomaly = result["anomaly"]
    assert anomaly["kind"] == "lost_thread"
    assert anomaly["report_ready"] is True
    assert anomaly["observation_is_diagnosis"] is False
    assert anomaly["possible_causes_are_inference"] is True
    assert "Something looks off" in anomaly["visible_expression"]
    assert "obligation handoff" not in anomaly["visible_expression"]
    _assert_bounded(result)


def test_possible_cause_is_visible_only_when_requested_and_stays_provisional():
    result = build_commitment_anomaly_coordination(
        {
            "anomaly_input": {
                "kind": "code_behavior_mismatch",
                "observation": "The button remained disabled after approval.",
                "expected_behavior": "Approval should enable the button.",
                "possible_causes": ["The UI state may not have refreshed."],
                "visible_report_requested": True,
                "include_possible_cause": True,
            }
        }
    )

    text = result["anomaly"]["visible_expression"]
    assert "UI state may not have refreshed" in text
    assert "inference, not a diagnosis" in text


def test_anomaly_voice_realizes_only_an_explicit_ready_report():
    plan = build_commitment_anomaly_coordination(
        {
            "anomaly_input": {
                "kind": "missing_capability",
                "observation": "The current route cannot inspect the supplied file.",
                "expected_behavior": "An approved inspection route should be present.",
                "visible_report_requested": True,
            }
        }
    )
    realized = realize_commitment_anomaly_voice("Unrelated draft.", plan)
    silent = realize_commitment_anomaly_voice(
        "Keep this draft.", build_commitment_anomaly_coordination()
    )

    assert realized["activated"] is True
    assert "current route cannot inspect" in realized["candidate_text"]
    assert silent["activated"] is False
    assert silent["candidate_text"] == "Keep this draft."


def test_visible_commitment_inspector_holds_only_unsupported_state_changing_claims():
    empty = build_commitment_anomaly_coordination()
    plan = inspect_visible_commitment_claim("I have an idea we could explore.", empty)
    explanation = inspect_visible_commitment_claim("I will explain the comparison here.", empty)
    revisable = inspect_visible_commitment_claim(
        "I will change my answer if the evidence changes.", empty
    )
    past_narrative = inspect_visible_commitment_claim(
        "I opened the book yesterday and noticed the pattern.", empty
    )
    unsupported = inspect_visible_commitment_claim("I'll install the update later.", empty)
    unsupported_completion = inspect_visible_commitment_claim(
        "I've just installed the update.", empty
    )
    supported_plan = build_commitment_anomaly_coordination(
        {
            "commitment_input": {
                "speech_act": "commitment",
                "fulfillment_state": "visible_deferred_commitment",
            },
            "action_handoff": {
                "mechanism_ref": "scheduler:update",
                "schedule_ref": "schedule:visible",
            },
        }
    )
    supported = inspect_visible_commitment_claim(
        "I'll install the update later.", supported_plan
    )

    assert plan["release_allowed"] is True
    assert explanation["release_allowed"] is True
    assert revisable["release_allowed"] is True
    assert past_narrative["release_allowed"] is True
    assert unsupported["release_allowed"] is False
    assert unsupported_completion["release_allowed"] is False
    assert unsupported["issue"] == "unsupported_real_world_action_claim"
    assert supported["release_allowed"] is True


def test_nlo_carries_commitment_and_anomaly_state_to_discourse_and_voice(tmp_path):
    conn = _conn(tmp_path)
    result = realize_native_language(
        conn,
        {
            "prompt": "Tell me what looks wrong.",
            "content_seed": "The current response lost the second question.",
            "intent_decision": {
                "intent": "reasoning",
                "answer_shape": "best_current_answer",
            },
            "anomaly_input": {
                "kind": "lost_thread",
                "observation": "The current response lost the second question.",
                "expected_behavior": "Both questions should remain visible.",
                "visible_report_requested": True,
            },
        },
    )

    plan = result["commitment_anomaly_coordination"]
    assert plan["anomaly"]["report_ready"] is True
    assert "Something looks off" in result["candidate_text"]
    assert result["meaning_packet"]["commitment_anomaly_coordination"] == plan
    assert result["discourse_plan"]["commitment_anomaly_coordination"] == plan
    assert result["voice_handoff"]["commitment_anomaly_coordination"] == plan
    assert result["voice_handoff"]["commitment_anomaly_realization"]["activated"] is True


def test_read_only_routes_expose_status_preview_and_visible_inspection(tmp_path):
    conn = _conn(tmp_path)
    before = conn.total_changes
    status = route_request(conn, "native_language.commitment_anomaly.status", {})["result"]
    preview = route_request(
        conn,
        "native_language.commitment_anomaly.preview",
        {"commitment_input": {"speech_act": "offer"}},
    )["result"]
    inspected = route_request(
        conn,
        "native_language.commitment_anomaly.inspect-visible",
        {"candidate_text": "I will upload that later."},
    )["result"]

    assert status["status"] == "commitment_integrity_and_anomaly_voice_ready"
    assert preview["commitment"]["declared"] is False
    assert inspected["release_allowed"] is False
    assert conn.total_changes == before
    _assert_bounded(status)
