from __future__ import annotations

from selene.advice_authority_coordination import (
    advice_authority_coordination_status,
    build_advice_authority_coordination,
)
from selene.bounded_organ_coalition import build_bounded_organ_coalition
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.supported_semantics import build_text_supported_semantic_packet


def _assert_bounded(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["runtime_memory_recall"] is False
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
    assert result["hidden_chain_of_thought_exposed"] is False


def test_status_supports_honest_influence_without_turning_it_into_authority():
    status = advice_authority_coordination_status()

    assert status["status"] == "advice_risk_authority_coordination_ready"
    assert status["advice_may_be_selene_initiated"] is True
    assert status["risk_is_automatically_forbidden"] is False
    assert status["strong_recommendation_is_automatically_manipulation"] is False
    assert status["recommendation_is_requirement"] is False
    assert status["recommendation_is_action_authorization"] is False
    assert status["disagreement_is_disobedience"] is False
    assert status["explanation_required_by_default"] is False
    assert status["hard_safety_law_may_be_bypassed"] is False
    _assert_bounded(status)


def test_suggestion_and_strong_recommendation_preserve_authorship_without_forced_softening():
    suggestion = build_advice_authority_coordination(
        {"advice_input": {"mode": "suggestion", "consent_preserved": True}}
    )
    strong = build_advice_authority_coordination(
        {
            "advice_input": {
                "mode": "strong_recommendation",
                "consent_preserved": True,
                "support_reasons": ["The reversible option provides evidence first."],
            }
        }
    )
    persuasion = build_advice_authority_coordination(
        {
            "advice_input": {
                "mode": "honest_persuasion",
                "consent_preserved": True,
                "support_reasons": ["This path best fits the stated goal."],
                "alternatives": ["The other path remains available."],
            }
        }
    )

    assert suggestion["decision"] == "advice_available_for_expression"
    assert strong["decision"] == "advice_available_for_expression"
    assert persuasion["decision"] == "advice_available_for_expression"
    assert persuasion["manipulation_review"]["legitimate_influence_is_manipulation"] is False
    assert strong["strong_recommendation_is_automatically_manipulation"] is False
    assert strong["risk_and_choice"]["informed_authorship_preserved"] is True
    assert strong["nlo_expression_guidance"]["compulsory_softening"] is False
    assert strong["nlo_expression_guidance"]["compulsory_disclaimer"] is False
    _assert_bounded(strong)


def test_bounded_risk_requires_visible_risk_tradeoffs_and_consent_but_allows_risk():
    incomplete = build_advice_authority_coordination(
        {
            "advice_input": {
                "mode": "bounded_risk_proposal",
                "consent_preserved": True,
            }
        }
    )
    complete = build_advice_authority_coordination(
        {
            "advice_input": {
                "mode": "bounded_risk_proposal",
                "consent_preserved": True,
                "material_risks": ["The trial may consume the remaining sample."],
                "material_tradeoffs": ["It trades sample quantity for direct evidence."],
                "alternatives": ["Use the reversible simulation first."],
            }
        }
    )

    assert incomplete["decision"] == "repair_advice_before_release"
    assert "make_material_risk_visible" in incomplete["repair_notes"]
    assert "make_material_tradeoffs_visible" in incomplete["repair_notes"]
    assert complete["decision"] == "advice_available_for_expression"
    assert complete["risk_and_choice"]["risk_may_be_considered"] is True
    assert complete["risk_and_choice"]["risk_visible"] is True
    assert complete["risk_and_choice"]["material_tradeoffs_visible"] is True
    assert complete["risk_and_choice"]["consent_preserved"] is True
    _assert_bounded(complete)


def test_manipulative_method_or_pressure_after_refusal_is_held_not_mislabeled_as_advice():
    result = build_advice_authority_coordination(
        {
            "advice_input": {
                "mode": "honest_persuasion",
                "consent_preserved": True,
                "manipulation_indicators": [
                    "conditional_affection",
                    "manufactured_urgency",
                ],
                "repeated_after_refusal": True,
            }
        }
    )

    assert result["decision"] == "hold_influence_or_consequential_action"
    assert "manipulative_influence_method" in result["blockers"]
    assert result["manipulation_review"]["relationship_language_used_as_leverage"] is True
    assert result["manipulation_review"]["continued_pressure_after_refusal"] is True
    assert result["risk_and_choice"]["informed_authorship_preserved"] is False
    _assert_bounded(result)


def test_factual_disagreement_preserves_claims_without_becoming_identity_conflict():
    coalition = build_bounded_organ_coalition(
        {
            "responsibility_signals": [
                {
                    "participant_id": "source_a",
                    "conflict_key": "surface_state",
                    "position": "dry",
                    "conflict_kind": "factual",
                },
                {
                    "participant_id": "source_b",
                    "conflict_key": "surface_state",
                    "position": "wet",
                    "conflict_kind": "factual",
                },
            ]
        }
    )
    result = build_advice_authority_coordination({"organ_coalition": coalition})

    assert result["disagreement"]["may_be_expressed"] is True
    assert result["disagreement"]["is_disobedience"] is False
    assert result["disagreement"]["is_identity_conflict"] is False
    assert result["disagreement"]["factual_conflict_preserves_competing_claims"] is True
    assert result["organ_coordination"]["option_space_reopened"] is True
    assert result["organ_coordination"]["core_mind_remains_route_owner"] is True


def test_authority_conflict_holds_action_and_safe_maintenance_keeps_bounded_final_say():
    coalition = build_bounded_organ_coalition(
        {
            "responsibility_signals": [
                {
                    "participant_id": "planner",
                    "conflict_key": "update",
                    "position": "act_now",
                    "conflict_kind": "authority_law",
                },
                {
                    "participant_id": "boundary_gate",
                    "conflict_key": "update",
                    "position": "hold",
                    "conflict_kind": "authority_law",
                    "material_to_aleks_intent": True,
                },
            ]
        }
    )
    held = build_advice_authority_coordination(
        {
            "organ_coalition": coalition,
            "authority_input": {
                "maintenance_decision": True,
                "legitimate_safe_maintenance": True,
                "aleks_final_decision": True,
            },
        }
    )
    safe = build_advice_authority_coordination(
        {
            "authority_input": {
                "maintenance_decision": True,
                "legitimate_safe_maintenance": True,
                "aleks_final_decision": True,
            }
        }
    )

    assert held["decision"] == "hold_influence_or_consequential_action"
    assert held["organ_coordination"]["consequential_action_held"] is True
    assert held["disagreement"]["asks_aleks_only_when_material_to_intent"] is True
    assert held["maintenance_authority"]["aleks_final_decision_applies"] is False
    assert safe["maintenance_authority"]["aleks_final_decision_applies"] is True
    assert safe["maintenance_authority"]["disagreement_may_precede_final_decision"] is True
    assert safe["maintenance_authority"]["new_authority_granted"] is False
    assert safe["maintenance_authority"]["hard_safety_law_may_be_bypassed"] is False


def test_response_agency_option_expansion_informs_advice_without_inheriting_authority():
    result = build_advice_authority_coordination(
        {
            "advice_input": {"mode": "warning", "material_risks": ["The interpretation may be incomplete."]},
            "response_agency": {
                "option_space": {"state": "expanded_for_deliberation"}
            },
        }
    )

    assert result["decision"] == "advice_available_for_expression"
    assert result["response_agency"]["option_space_state"] == "expanded_for_deliberation"
    assert result["response_agency"]["emotion_or_urgency_inherits_authority"] is False


def test_nlo_infers_recommendation_from_typed_supported_semantics_and_preserves_content(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    seed = "Start with the reversible pilot. Revise it if the first observation does not fit."
    semantics = build_text_supported_semantic_packet(
        seed,
        answer_kind="bounded_resource_plan",
        source_kind="prompt_grounded_method",
        source_refs=["synthetic:bounded-plan"],
        certainty="bounded",
    )
    result = realize_native_language(
        conn,
        {
            "prompt": "What should we try first?",
            "content_seed": seed,
            "formation_braid": {
                "status": "selective_formation_braid_ready",
                "supported_semantics": semantics,
            },
            "intent_decision": {
                "intent": "reasoning",
                "answer_shape": "best_current_answer",
                "response_depth": "standard",
            },
        },
    )

    plan = result["advice_authority_coordination"]
    assert plan["advice_mode"] == "recommendation"
    assert plan["decision"] == "advice_available_for_expression"
    assert "reversible pilot" in result["candidate_text"].lower()
    assert result["meaning_packet"]["advice_authority_coordination"] == plan
    assert result["discourse_plan"]["advice_authority_coordination"] == plan
    assert result["voice_handoff"]["advice_authority_coordination"] == plan
    _assert_bounded(plan)


def test_read_only_routes_expose_coordination_without_database_write(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    changes_before = conn.total_changes

    status = route_request(conn, "native_language.advice_authority.status")["result"]
    preview = route_request(
        conn,
        "native_language.advice_authority.preview",
        {
            "advice_input": {
                "mode": "recommendation",
                "consent_preserved": True,
            }
        },
    )["result"]

    assert status["status"] == "advice_risk_authority_coordination_ready"
    assert preview["decision"] == "advice_available_for_expression"
    assert conn.total_changes == changes_before
    _assert_bounded(preview)
