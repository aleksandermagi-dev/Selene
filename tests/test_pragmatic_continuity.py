from __future__ import annotations

from selene.pragmatic_continuity import build_pragmatic_continuity_plan


def test_explicit_topic_return_resumes_bounded_session_topic():
    result = build_pragmatic_continuity_plan(
        {
            "prompt": "Anyway, back to the memory plan: what comes first?",
            "dialogue_workspace": {
                "active_topic": "voice pacing",
                "side_topics": ["memory plan", "source review"],
                "open_loops": [{"id": "memory-order", "status": "open"}],
            },
            "pragmatic_plan": {"ambiguity": {"level": "low"}},
            "intent_decision": {"intent": "reasoned_answer"},
        }
    )

    transition = result["topic_transition"]
    assert transition["kind"] == "explicit_return"
    assert transition["to_topic"] == "memory plan"
    assert result["interruption_plan"]["action"] == "resume_named_topic_from_last_clear_session_point"
    assert result["open_loop_ids"] == ["memory-order"]
    assert result["session_scoped_only"] is True


def test_interruption_pauses_without_deleting_prior_open_work():
    result = build_pragmatic_continuity_plan(
        {
            "prompt": "Wait, hold on a second.",
            "dialogue_workspace": {
                "active_topic": "teaching review",
                "open_loops": [{"id": "review", "status": "open"}],
            },
            "intent_decision": {"intent": "direct_conversation"},
        }
    )

    assert result["topic_transition"]["kind"] == "interruption"
    assert result["interruption_plan"]["prior_open_loops_preserved"] is True
    assert result["interruption_plan"]["automatic_loop_deletion"] is False
    assert result["automatic_speech_allowed"] is False


def test_braided_turn_reports_the_whole_sequence_instead_of_only_its_return_marker():
    braid = {
        "braided": True,
        "active_thread_id": "z",
        "turn_traversal": [
            {"thread_id": "x", "action": "start"},
            {"thread_id": "y", "action": "branch"},
            {"thread_id": "x", "action": "revise_with_dependency"},
            {"thread_id": "z", "action": "land"},
        ],
    }
    result = build_pragmatic_continuity_plan(
        {
            "prompt": "Start with X. Move to Y. Back to X using Y. Finish with Z.",
            "dialogue_workspace": {"active_topic": "x", "thread_braid": braid},
            "pragmatic_plan": {"thread_braid": braid},
        }
    )

    transition = result["topic_transition"]
    assert transition["kind"] == "braided_sequence"
    assert transition["thread_actions"] == ["start", "branch", "revise_with_dependency", "land"]
    assert result["active_thread_id"] == "z"


def test_plural_pronoun_can_use_two_candidates_but_singular_pronoun_cannot_guess_between_them():
    dialogue = {"reference_candidates": ["memory", "voice"]}
    plural = build_pragmatic_continuity_plan(
        {"prompt": "How do they differ?", "dialogue_workspace": dialogue}
    )
    singular = build_pragmatic_continuity_plan(
        {"prompt": "How does it differ?", "dialogue_workspace": dialogue}
    )

    assert plural["referent_posture"]["resolved_to"] == "memory and voice"
    assert plural["referent_posture"]["materially_ambiguous"] is False
    assert singular["referent_posture"]["resolved_to"] == ""
    assert singular["referent_posture"]["materially_ambiguous"] is True
    assert singular["ending_decision"]["mode"] == "ask_one_material_question"


def test_complete_answer_and_social_turn_do_not_create_habitual_follow_up_questions():
    answer = build_pragmatic_continuity_plan(
        {
            "prompt": "Explain the current plan.",
            "intent_decision": {"intent": "reasoned_answer"},
            "pragmatic_plan": {"ambiguity": {"level": "low"}},
        }
    )
    social = build_pragmatic_continuity_plan(
        {
            "prompt": "Thank you, friend.",
            "intent_decision": {"intent": "gratitude"},
            "pragmatic_plan": {"ambiguity": {"level": "low"}},
        }
    )

    assert answer["ending_decision"]["mode"] == "answer_and_stop_when_complete"
    assert social["ending_decision"]["mode"] == "leave_room_without_pressuring"
    assert answer["ending_decision"]["question_allowed"] is False
    assert social["ending_decision"]["habitual_follow_up_allowed"] is False


def test_initiative_requires_current_turn_invitation_and_never_auto_delivers():
    invited = build_pragmatic_continuity_plan({"prompt": "What do you think—any ideas?"})
    not_invited = build_pragmatic_continuity_plan({"prompt": "That completes the checkpoint."})

    assert invited["initiative_decision"]["mode"] == "offer_one_relevant_thought"
    assert invited["initiative_decision"]["automatic_delivery"] is False
    assert not_invited["initiative_decision"]["mode"] == "no_unsolicited_initiative"
    assert not_invited["initiative_expansion_allowed"] is False


def test_correction_and_response_preference_remain_session_refinements_not_profile():
    result = build_pragmatic_continuity_plan(
        {
            "prompt": "Continue from there.",
            "dialogue_workspace": {
                "corrections": [
                    {
                        "corrected_meaning": "semantic layer",
                        "replaced_meaning": "voice layer",
                        "status": "active_refinement",
                    }
                ],
                "preferences": {"response_depth": "brief", "scope": "current_session_only"},
            },
        }
    )

    assert result["active_correction"]["corrected_meaning"] == "semantic layer"
    assert result["active_correction"]["scope"] == "current_session_refinement_only"
    assert result["response_preference"]["response_depth"] == "brief"
    assert result["relationship_profile_write_allowed"] is False
    assert result["memory_write_active"] is False
