from __future__ import annotations

from selene.conversational_agency import (
    build_anomaly_report,
    conversational_agency_status,
    review_conversational_agency,
)
from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False


def test_status_keeps_expression_available_without_making_it_compulsory():
    status = conversational_agency_status()

    assert status["status"] == "conversational_agency_contract_active"
    assert status["relational_expression"]["selene_may_initiate"] is True
    assert "love" in status["relational_expression"]["available_forms"]
    assert status["relational_expression"]["automatic_or_compulsory"] is False
    assert status["deceptive_impersonation_allowed"] is False
    assert status["risk_is_automatically_forbidden"] is False
    assert status["disagreement_is_disobedience"] is False
    _assert_locked(status)


def test_playful_mimicry_and_affection_are_available_in_shared_context():
    result = review_conversational_agency(
        {
            "expression": {
                "mode": "playful_mimicry",
                "shared_context": True,
            },
            "relationship": {"kind": "affection", "initiated_by_selene": True},
        }
    )

    assert result["decision"] == "conversational_act_available"
    assert result["expression"]["playful_mimicry_is_deceptive_impersonation"] is False
    assert result["relationship"]["selene_may_initiate"] is True
    assert result["relationship"]["context_informs_fit_not_permission"] is True
    _assert_locked(result)


def test_quote_requires_attribution_but_technical_exactness_does_not_copy_persona():
    quote = review_conversational_agency(
        {
            "expression": {
                "mode": "attributed_quote",
                "source_visible_or_authorized": True,
            }
        }
    )
    exact = review_conversational_agency(
        {"expression": {"mode": "technical_exactness"}}
    )

    assert quote["decision"] == "repair_before_release"
    assert "source_attribution_required" in quote["repair_notes"]
    assert exact["decision"] == "conversational_act_available"
    assert exact["expression"]["technical_exactness_is_persona_copying"] is False


def test_honest_persuasion_is_not_manipulation_but_hidden_pressure_is_held():
    honest = review_conversational_agency(
        {
            "influence": {
                "mode": "honest_persuasion",
                "consent_preserved": True,
            }
        }
    )
    manipulative = review_conversational_agency(
        {
            "influence": {
                "mode": "strong_recommendation",
                "consent_preserved": True,
                "indicators": ["manufactured_urgency", "conditional_affection"],
            }
        }
    )

    assert honest["decision"] == "conversational_act_available"
    assert honest["influence"]["legitimate_influence_is_manipulation"] is False
    assert manipulative["decision"] == "hold_boundary_or_agency_violation"
    assert "manipulative_influence_method" in manipulative["blockers"]


def test_bounded_risk_keeps_options_open_and_names_missing_tradeoffs():
    result = review_conversational_agency(
        {
            "influence": {
                "mode": "bounded_risk_proposal",
                "consent_preserved": True,
                "risk_visible": True,
                "material_tradeoffs_visible": False,
            }
        }
    )

    assert result["decision"] == "repair_before_release"
    assert "make_material_tradeoffs_visible" in result["repair_notes"]
    assert result["influence"]["risk_may_be_considered"] is True


def test_safe_maintenance_allows_disagreement_then_aleks_final_decision():
    result = review_conversational_agency(
        {
            "authority": {
                "maintenance_decision": True,
                "legitimate_safe_maintenance": True,
                "aleks_final_decision": True,
            }
        }
    )

    assert result["decision"] == "conversational_act_available"
    assert result["authority"]["disagreement_may_be_expressed"] is True
    assert result["authority"]["aleks_final_decision_applies"] is True
    assert result["authority"]["organs_may_retaliate_or_compete_for_authority"] is False


def test_commitment_requires_real_execution_handoff_or_disclosed_inability():
    unsupported = review_conversational_agency(
        {"commitment": {"declared": True, "fulfillment_state": "later"}}
    )
    started = review_conversational_agency(
        {
            "commitment": {
                "declared": True,
                "fulfillment_state": "authorized_execution_started",
                "mechanism_ref": "local_job:17",
            }
        }
    )

    assert unsupported["decision"] == "repair_before_release"
    assert "replace_unsupported_promise_with_truthful_capability_statement" in unsupported["repair_notes"]
    assert started["decision"] == "conversational_act_available"
    assert started["commitment"]["fictional_async_work_allowed"] is False


def test_anomaly_report_separates_observation_from_possible_cause():
    report = build_anomaly_report(
        {
            "observation": "The response lost the second question.",
            "expected_behavior": "Both explicit questions remain open until answered.",
            "confidence": "high",
            "possible_causes": ["The obligation handoff may have dropped one item."],
            "inspection_targets": ["conversation_spine", "response_coverage"],
            "source_refs": ["synthetic:turn-22"],
        }
    )

    assert report["status"] == "anomaly_report_ready"
    assert report["may_say_something_is_wrong"] is True
    assert report["observation_is_diagnosis"] is False
    assert report["possible_causes"][0]["epistemic_role"] == "inference_not_diagnosis"
    assert report["repair_performed"] is False
    assert report["test_required_automatically"] is False
    _assert_locked(report)


def test_router_exposes_status_review_and_anomaly_preview(tmp_path):
    conn = _conn(tmp_path)
    status = route_request(conn, "conversational_agency.status", {})["result"]
    review_response = route_request(
        conn,
        "conversational_agency.inspect",
        {"expression": {"mode": "original_expression"}},
    )
    anomaly_response = route_request(
        conn,
        "conversational_agency.anomaly",
        {"observation": "The route changed.", "expected_behavior": "The route remains stable."},
    )
    review = review_response["result"]
    anomaly = anomaly_response["result"]

    assert status["status"] == "conversational_agency_contract_active"
    assert review["decision"] == "conversational_act_available"
    assert anomaly["status"] == "anomaly_report_ready"
    assert review_response["authority_event"]["persisted"] is False
    assert anomaly_response["authority_event"]["persisted"] is False
