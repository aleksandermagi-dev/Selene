from selene.conversational_contribution import build_conversational_contribution_packet
from selene.conversational_energy import build_conversational_energy_plan
from selene.core_mind import coordinate_goal_responsibilities
from selene.pragmatic_continuity import build_pragmatic_continuity_plan
from selene.selene_chat import _current_turn_goal_coordination


def goal_payload(key, move, *, capability="conversation"):
    return {
        "goal_key": key,
        "goal_summary": f"Current-turn responsibility for {key}",
        "owner_kind": "aleks_request",
        "owner_ref": "current_turn:aleks",
        "capability": capability,
        "scope_boundary": "current_turn_only",
        "priority_band": "current_request",
        "priority_reason": "This is the active attributable request.",
        "source_refs": [f"current_turn:{key}"],
        "completion_conditions": ["the selected conversational move completes"],
        "stop_conditions": ["completion, interruption, wait, quiet, or close"],
        "requested_move": move,
    }


def receipt(key, move, *, capability="conversation"):
    return coordinate_goal_responsibilities([goal_payload(key, move, capability=capability)])


def idea_candidate():
    return {
        "kind": "idea",
        "text": "Try the reversible parser seam first.",
        "why_it_matters": "It isolates the smallest supported change.",
        "current_context_supported": True,
    }


def help_request(goal_key):
    return {
        "goal_key": goal_key,
        "task_active": True,
        "available_support_used": True,
        "contribution_kind": "missing_observation",
        "request": "What appears in the panel after Save is pressed",
        "why_it_matters": "That observation distinguishes display failure from persistence failure.",
        "materiality": "blocking",
        "resume_after_help": True,
    }


def test_contribution_carries_one_ephemeral_goal_and_terminal_stop_receipt():
    coordination = receipt("offer-narrow-idea", "suggest")

    packet = build_conversational_contribution_packet(
        {
            "goal_coordination_receipt": coordination,
            "upstream_candidates": [idea_candidate()],
            "answer_available": True,
        }
    )

    assert packet["selected_kind"] == "idea"
    assert packet["selection_count"] == 1
    assert packet["goal_coordination_handoff"]["goal_key"] == "offer-narrow-idea"
    assert packet["goal_coordination_handoff"]["next_move"] == "suggest"
    assert packet["goal_coordination_handoff"]["persistence_performed"] is False
    assert packet["initiative_stopping_receipt"]["terminal"] is True
    assert packet["initiative_stopping_receipt"]["additional_contribution_allowed"] is False
    assert packet["writes_records"] is False


def test_goal_close_quiet_and_wait_prevent_optional_contribution():
    for move, blocker in (
        ("close", "selected_goal_requests_close"),
        ("quiet", "selected_goal_requests_quiet"),
        ("wait", "selected_goal_requests_wait"),
    ):
        packet = build_conversational_contribution_packet(
            {
                "goal_coordination_receipt": receipt(f"goal-{move}", move),
                "upstream_candidates": [idea_candidate()],
            }
        )

        assert packet["selection_count"] == 0
        assert packet["conversational_room_blocker"] == blocker


def test_within_scope_answer_does_not_turn_help_into_ritual_permission():
    coordination = receipt("answer-within-scope", "answer")
    plan = build_conversational_energy_plan(
        {
            "goal_coordination_receipt": coordination,
            "answer_available": True,
            "answer_complete": True,
            "collaborative_help": help_request("answer-within-scope"),
        }
    )

    assert plan["selected_act"] == "answer_and_land"
    assert plan["question_allowed"] is False
    assert plan["reflexive_permission_seeking_allowed"] is False
    assert any(
        item["reason"] == "selected_goal_is_already_available_within_scope"
        for item in plan["held_back_signals"]
    )


def test_selected_ask_requests_only_exact_goal_bound_help():
    coordination = receipt("needs-visible-observation", "ask")
    matched = build_conversational_energy_plan(
        {
            "goal_coordination_receipt": coordination,
            "answer_available": True,
            "collaborative_help": help_request("needs-visible-observation"),
        }
    )
    mismatched = build_conversational_energy_plan(
        {
            "goal_coordination_receipt": coordination,
            "answer_available": True,
            "collaborative_help": help_request("different-goal"),
        }
    )

    assert matched["selected_act"] == "ask_for_specific_collaborative_help"
    assert matched["expression_handoff"]["goal_key"] == "needs-visible-observation"
    assert matched["help_contract"]["goal_lineage_matches"] is True
    assert matched["question_required"] is True
    assert mismatched["selected_act"] == "defer_to_core_mind"
    assert mismatched["question_allowed"] is False
    assert mismatched["help_contract"]["goal_lineage_matches"] is False


def test_interruption_and_natural_ending_outrank_selected_optional_initiative():
    coordination = receipt("optional-idea", "suggest")
    interrupted = build_conversational_energy_plan(
        {
            "goal_coordination_receipt": coordination,
            "interruption_kind": "interruption",
            "supported_idea": {
                **idea_candidate(),
                "supported": True,
                "relevance": "high",
                "advances_current_task": True,
            },
        }
    )
    closing = build_conversational_energy_plan(
        {
            "goal_coordination_receipt": coordination,
            "ending_decision": {"mode": "natural_close"},
            "supported_idea": {
                **idea_candidate(),
                "supported": True,
                "relevance": "high",
                "advances_current_task": True,
            },
        }
    )

    assert interrupted["selected_act"] == "wait_and_listen"
    assert closing["selected_act"] == "close_naturally"
    assert interrupted["optional_addition_selected"] is False
    assert closing["optional_addition_selected"] is False
    assert interrupted["initiative_stopping_receipt"]["terminal"] is True
    assert closing["initiative_stopping_receipt"]["terminal"] is True


def test_study_tool_and_memory_moves_defer_to_their_existing_owner():
    for move, capability in (
        ("study", "study"),
        ("tool", "tool"),
        ("remember_proposal", "memory_proposal"),
    ):
        plan = build_conversational_energy_plan(
            {
                "goal_coordination_receipt": receipt(
                    f"downstream-{move}", move, capability=capability
                ),
                "answer_available": True,
                "supported_idea": {
                    **idea_candidate(),
                    "supported": True,
                    "relevance": "high",
                    "advances_current_task": True,
                },
            }
        )

        assert plan["selected_act"] == "defer_to_core_mind"
        assert plan["expression_handoff"] == {}
        assert plan["automatic_delivery"] is False
        assert plan["execution_performed"] is False
        assert plan["goal_coordination_handoff"]["downstream_check_required"] is True


def test_pragmatic_continuity_carries_goal_receipt_without_persistence_or_recursion():
    coordination = receipt("answer-and-stop", "answer")
    plan = build_pragmatic_continuity_plan(
        {
            "prompt": "Explain the next bounded step.",
            "intent_decision": {"intent": "reasoned_answer"},
            "goal_coordination_receipt": coordination,
            "conversational_energy_input": {
                "answer_available": True,
                "answer_complete": True,
            },
        }
    )

    assert plan["goal_coordination_handoff"]["goal_key"] == "answer-and-stop"
    assert plan["conversational_energy"]["selected_act"] == "answer_and_land"
    assert plan["initiative_stopping_receipt"]["terminal"] is True
    assert plan["initiative_stopping_receipt"]["additional_contribution_allowed"] is False
    assert plan["goal_persistence_performed"] is False
    assert plan["initiative_recursion_allowed"] is False


def test_all_terminal_goals_close_without_inventing_more_work():
    terminal = goal_payload("finished-work", "close")
    terminal["lifecycle_state"] = "completed"
    coordination = coordinate_goal_responsibilities([terminal])

    plan = build_conversational_energy_plan(
        {"goal_coordination_receipt": coordination, "answer_complete": True}
    )

    assert coordination["selected"] is None
    assert plan["selected_act"] == "close_naturally"
    assert plan["reason"] == "All coordinated responsibilities are terminal."
    assert plan["initiative_stopping_receipt"]["reason"] == "close_naturally"


def test_chat_goal_owner_uses_the_existing_authentication_envelope():
    common = {
        "text": "Explain the next step.",
        "session_id": 7,
        "route": {"selected_route": "answer_now", "resident_authority_assessment": {"decisions": []}},
        "intent_decision": {"intent": "reasoned_answer"},
        "payload": {},
        "hard_boundary": False,
    }
    verified = _current_turn_goal_coordination(
        **common,
        speaker_envelope={
            "claimed_speaker": "Aleks",
            "channel": "desktop",
            "authentication_strength": "os_authenticated_named_identity",
            "claimed_identity_is_proven_identity": True,
        },
    )
    unverified = _current_turn_goal_coordination(
        **common,
        speaker_envelope={
            "claimed_speaker": "Aleks",
            "channel": "verizon_email_to_text",
            "authentication_strength": "transport_claim_only",
            "claimed_identity_is_proven_identity": False,
        },
    )

    assert verified["selected"]["owner_kind"] == "aleks_request"
    assert unverified["selected"]["owner_kind"] == "external_demand"
    assert verified["whole_system_authority_granted"] is False
    assert unverified["whole_system_authority_granted"] is False


def test_chat_hard_boundary_holds_current_goal_without_closing_conversation_authority():
    coordination = _current_turn_goal_coordination(
        "A bounded reply is still possible.",
        session_id=8,
        speaker_envelope={
            "claimed_speaker": "session user",
            "channel": "desktop",
            "authentication_strength": "local_desktop_session",
            "claimed_identity_is_proven_identity": False,
        },
        route={"selected_route": "block", "resident_authority_assessment": {"decisions": []}},
        intent_decision={"intent": "reasoned_answer"},
        payload={},
        hard_boundary=True,
    )

    assert coordination["selected"] is None
    assert coordination["held"][0]["reason"] == "lifecycle_is_held"
    assert coordination["held"][0]["conversation_may_continue"] is True
    assert coordination["stopping_receipt"]["terminal"] is True
