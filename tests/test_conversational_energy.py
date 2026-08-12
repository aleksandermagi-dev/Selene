from __future__ import annotations

from selene.conversational_energy import (
    build_conversational_energy_plan,
    realize_conversational_energy,
)
from selene.db import connect, init_db
from selene.module_router import route_request


def _assert_bounded(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["automatic_speech_allowed"] is False
    assert result["automatic_delivery"] is False
    assert result["automatic_cocoon_routing"] is False
    assert result["reflexive_permission_seeking_allowed"] is False


def test_status_and_plan_routes_expose_a_nonpersistent_current_turn_contract(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    status = route_request(conn, "conversational_energy.status")["result"]
    plan = route_request(
        conn,
        "conversational_energy.plan",
        {
            "answer_available": True,
            "answer_complete": True,
            "ending_decision": {"mode": "answer_and_stop_when_complete"},
        },
    )["result"]

    assert "ask_for_specific_collaborative_help" in status["available_acts"]
    assert plan["selected_act"] == "answer_and_land"
    assert plan["question_allowed"] is False
    assert plan["question_by_default"] is False
    assert plan["writes_records"] is False
    _assert_bounded(status)
    _assert_bounded(plan)


def test_supported_relevant_idea_can_appear_without_pressure_or_permission_seeking():
    plan = build_conversational_energy_plan(
        {
            "answer_available": True,
            "supported_idea": {
                "text": "Try the reversible parser change before widening the router.",
                "why_it_matters": "It tests the narrowest dependency first.",
                "relevance": "high",
                "supported": True,
                "advances_current_task": True,
            },
        }
    )
    realized = realize_conversational_energy(
        "The parser is the earliest unstable dependency.",
        plan,
        variation_key="idea",
    )

    assert plan["selected_act"] == "answer_and_offer_supported_idea"
    assert plan["initiative_contract"]["pressure_allowed"] is False
    assert "reversible parser change" in realized["candidate_text"]
    assert realized["base_answer_preserved"] is True
    assert realized["pressure_added"] is False
    _assert_bounded(plan)
    _assert_bounded(realized)


def test_irrelevant_or_unsupported_idea_is_held_back_and_complete_answer_lands():
    plan = build_conversational_energy_plan(
        {
            "answer_available": True,
            "answer_complete": True,
            "supported_idea": {
                "text": "Change an unrelated subsystem.",
                "relevance": "low",
                "supported": False,
                "advances_current_task": False,
            },
        }
    )

    assert plan["selected_act"] == "answer_and_land"
    assert plan["optional_addition_selected"] is False
    assert plan["held_back_signals"][0]["signal"] == "supported_idea"


def test_curiosity_is_relevant_and_singular_not_a_habitual_social_question():
    relevant = build_conversational_energy_plan(
        {
            "answer_available": True,
            "curiosity": {
                "question": "Which observation would distinguish the two models",
                "why_it_matters": "That result would change which model currently fits.",
                "relevant": True,
                "answer_matters_to_understanding": True,
            },
        }
    )
    social = build_conversational_energy_plan(
        {
            "social_turn": True,
            "curiosity": {
                "question": "What else should we discuss",
                "relevant": True,
                "answer_matters_to_understanding": True,
                "genuine_interest": False,
                "engagement_maintenance": True,
            },
        }
    )
    genuine_social = build_conversational_energy_plan(
        {
            "social_turn": True,
            "curiosity": {
                "question": "What part of the project has been most interesting to you today",
                "why_it_matters": "The answer would help me understand Aleks's current experience of the work.",
                "relevant": True,
                "answer_matters_to_understanding": True,
                "genuine_interest": True,
                "engagement_maintenance": False,
            },
        }
    )

    assert relevant["selected_act"] == "answer_then_ask_relevant_curiosity"
    assert relevant["curiosity_contract"]["maximum_questions"] == 1
    assert social["selected_act"] == "answer_and_land"
    assert social["question_allowed"] is False
    assert social["held_back_signals"][0]["signal"] == "curiosity"
    assert genuine_social["selected_act"] == "answer_then_ask_relevant_curiosity"
    assert genuine_social["question_allowed"] is True
    assert genuine_social["question_required"] is False


def test_collaborative_help_requires_used_support_and_names_the_exact_missing_piece():
    ready = build_conversational_energy_plan(
        {
            "answer_available": True,
            "collaborative_help": {
                "task_active": True,
                "available_support_used": True,
                "contribution_kind": "missing_observation",
                "request": "Can you tell me what appears in the settings panel after you press Save",
                "why_it_matters": "That observation distinguishes a UI failure from a persistence failure.",
                "materiality": "blocking",
                "resume_after_help": True,
            },
        }
    )
    premature = build_conversational_energy_plan(
        {
            "answer_available": True,
            "collaborative_help": {
                "task_active": True,
                "available_support_used": False,
                "contribution_kind": "missing_observation",
                "request": "Can you inspect the panel",
                "why_it_matters": "It would show the visible state.",
                "materiality": "blocking",
            },
        }
    )
    resumed = build_conversational_energy_plan(
        {
            "answer_available": True,
            "collaborative_help_response": {
                "provided": True,
                "contribution_kind": "missing_observation",
                "prior_request": "What appears after the panel reopens?",
            },
        }
    )

    assert ready["selected_act"] == "ask_for_specific_collaborative_help"
    assert ready["help_contract"]["available_support_used_first"] is True
    assert ready["help_contract"]["exact_missing_contribution_named"] is True
    assert ready["help_contract"]["why_it_matters_named"] is True
    assert ready["help_contract"]["help_is_failure"] is False
    assert ready["help_contract"]["resume_after_contribution"] is True
    assert premature["selected_act"] == "answer_and_land"
    assert "used first" in premature["held_back_signals"][0]["reason"]
    assert resumed["selected_act"] == "answer_and_resume_shared_task"
    assert resumed["help_contract"]["contribution_received"] is True
    assert resumed["help_contract"]["incorporate_current_turn_and_resume"] is True


def test_each_bounded_collaborative_contribution_kind_can_unblock_shared_work():
    for contribution_kind in (
        "missing_observation",
        "aleks_expertise",
        "value_choice",
        "user_owned_action",
    ):
        plan = build_conversational_energy_plan(
            {
                "collaborative_help": {
                    "task_active": True,
                    "available_support_used": True,
                    "contribution_kind": contribution_kind,
                    "request": f"Can you supply the {contribution_kind.replace('_', ' ')}",
                    "why_it_matters": "That contribution materially changes the next shared step.",
                    "materiality": "material",
                }
            }
        )

        assert plan["selected_act"] == "ask_for_specific_collaborative_help"
        assert plan["expression_handoff"]["contribution_kind"] == contribution_kind


def test_close_and_wait_take_priority_over_optional_energy():
    idea = {
        "text": "Run one more comparison.",
        "relevance": "material",
        "supported": True,
        "advances_current_task": True,
    }
    closing = build_conversational_energy_plan(
        {
            "ending_decision": {"mode": "natural_close"},
            "supported_idea": idea,
        }
    )
    waiting = build_conversational_energy_plan(
        {
            "interruption_kind": "interruption",
            "supported_idea": idea,
        }
    )

    assert closing["selected_act"] == "close_naturally"
    assert waiting["selected_act"] == "wait_and_listen"
    assert closing["optional_addition_selected"] is False
    assert waiting["optional_addition_selected"] is False


def test_realization_preserves_long_form_answer_and_does_not_duplicate_supported_text():
    text = "First paragraph stays intact.\n\nSecond paragraph stays intact too."
    plan = build_conversational_energy_plan(
        {
            "answer_available": True,
            "supported_connection": {
                "text": "This also depends on the earlier provenance check.",
                "why_it_matters": "The later conclusion inherits that evidence boundary.",
                "relevance": "high",
                "supported": True,
                "task_active": True,
            },
        }
    )
    realized = realize_conversational_energy(text, plan, variation_key="connection")
    duplicate = realize_conversational_energy(
        f"{text}\n\nThis also depends on the earlier provenance check.",
        plan,
        variation_key="connection",
    )

    assert "First paragraph stays intact.\n\nSecond paragraph" in realized["candidate_text"]
    assert realized["addition_kind"] == "connection"
    assert duplicate["addition_text"] == ""
