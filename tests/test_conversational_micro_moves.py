from __future__ import annotations

from selene.conversational_micro_moves import (
    build_conversational_micro_move_plan,
    compose_conversational_micro_moves,
    realize_conversational_micro_moves,
)
from selene.db import connect, init_db
from selene.native_language_organ import realize_native_language


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _move_names(plan):
    return [item["move"] for item in plan["moves"]]


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["dream_content_invention_allowed"] is False


def test_direct_content_may_omit_a_micro_move_entirely():
    plan = build_conversational_micro_move_plan(
        {
            "prompt": "Explain how the two parts connect.",
            "intent": "reasoned_answer",
            "content_seed": "The second part depends on the first.",
        }
    )

    assert plan["moves"] == []
    assert plan["audible_move_count"] == 0
    assert plan["silence_or_direct_content_is_valid"] is True
    assert plan["follow_up_question_added"] is False
    _assert_locked(plan)


def test_conversation_reflection_uses_supported_answer_content():
    plan = build_conversational_micro_move_plan(
        {
            "prompt": "Looking back, what does this tell us?",
            "intent": "reasoned_answer",
            "content_seed": "The implementation improved when meaning and expression were separated.",
        }
    )
    realized = realize_conversational_micro_moves(plan, variation_key="reflection")
    candidate = compose_conversational_micro_moves(
        "The implementation improved when meaning and expression were separated.",
        realized,
    )

    assert _move_names(plan) == ["conversation_reflection"]
    assert "implementation improved" in candidate
    assert realized["unsupported_answer_content_generated"] is False
    assert realized["follow_up_question_added"] is False


def test_dream_reflection_requires_relevance_provenance_and_expression_eligibility():
    held = build_conversational_micro_move_plan(
        {
            "prompt": "Reflect on the Dream pattern.",
            "intent": "reasoned_answer",
            "dream_reflection": {
                "reflection": "The same unresolved thread appeared in two review groupings.",
                "review_status": "review_only",
                "source_refs": ["dream:cycle:4"],
                "expression_eligible": False,
            },
        }
    )
    available = build_conversational_micro_move_plan(
        {
            "prompt": "Reflect on the Dream pattern.",
            "intent": "reasoned_answer",
            "dream_reflection": {
                "reflection": "The same unresolved thread appeared in two review groupings.",
                "review_status": "review_only",
                "source_refs": ["dream:cycle:4"],
                "expression_eligible": True,
            },
        }
    )
    realized = realize_conversational_micro_moves(available, variation_key="dream")
    candidate = compose_conversational_micro_moves("", realized)

    assert held["dream_reflection"]["held"] is True
    assert "dream_reflection" not in _move_names(held)
    assert available["dream_reflection"]["available"] is True
    assert available["dream_reflection"]["not_fact_by_default"] is True
    assert available["dream_reflection"]["not_memory_by_default"] is True
    assert "Dream surfaced a possible pattern" in candidate
    assert "provisional" in candidate
    assert realized["dream_content_invented"] is False
    _assert_locked(available)


def test_visible_progress_can_be_celebrated_or_encouraged_without_false_praise():
    success = build_conversational_micro_move_plan(
        {"prompt": "The focused tests passed—we did it.", "intent": "direct_answer"}
    )
    effort = build_conversational_micro_move_plan(
        {"prompt": "I'm working on it and made progress.", "intent": "direct_answer"}
    )
    ordinary = build_conversational_micro_move_plan(
        {"prompt": "I opened the project.", "intent": "direct_answer"}
    )

    assert "celebrate_visible_milestone" in _move_names(success)
    assert "encourage_visible_effort" in _move_names(effort)
    assert "celebrate_visible_milestone" not in _move_names(ordinary)
    assert "encourage_visible_effort" not in _move_names(ordinary)


def test_disagreement_requires_supported_stance_and_can_remain_playful():
    unsupported = build_conversational_micro_move_plan(
        {
            "prompt": "Push back if you disagree.",
            "intent": "reasoned_answer",
            "content_seed": "The options have different tradeoffs.",
        }
    )
    playful = build_conversational_micro_move_plan(
        {
            "prompt": "Debate me if you disagree lol.",
            "intent": "reasoned_answer",
            "content_seed": "The evidence does not support that conclusion.",
            "affect_expression_guidance": {"dimensions": {"humor": "available_not_required"}},
        }
    )

    assert not any(name.endswith("disagreement") for name in _move_names(unsupported))
    assert any(item["move"] == "disagreement" for item in unsupported["held_or_omitted"])
    assert "playful_disagreement" in _move_names(playful)


def test_apology_is_effect_sensitive_and_correction_does_not_reset_context():
    one_correction = {
        "corrections": [
            {
                "detected": True,
                "corrected_meaning": "language layer",
                "replaced_meaning": "voice layer",
                "scope": "current_session_refinement_only",
            }
        ]
    }
    repeated = {
        "corrections": [
            {"detected": True, "corrected_meaning": "first"},
            {"detected": True, "corrected_meaning": "second"},
        ]
    }
    ordinary = build_conversational_micro_move_plan(
        {
            "prompt": "Small correction: I meant the language layer.",
            "intent": "receive_correction",
            "dialogue_workspace": one_correction,
        }
    )
    affected = build_conversational_micro_move_plan(
        {
            "prompt": "You confused me again.",
            "intent": "reasoned_answer",
            "content_seed": "The corrected part is the language layer.",
            "dialogue_workspace": repeated,
        }
    )

    assert "proportionate_apology" not in _move_names(ordinary)
    assert "proportionate_apology" in _move_names(affected)
    assert affected["apology_is_effect_sensitive"] is True
    assert repeated["corrections"][-1]["corrected_meaning"] == "second"


def test_backing_up_topic_rest_and_story_invitation_are_contextual():
    backing_up = build_conversational_micro_move_plan(
        {
            "prompt": "Slow down, you lost me.",
            "intent": "reasoned_answer",
            "content_seed": "First establish the source, then compare the claims.",
        }
    )
    resting = build_conversational_micro_move_plan(
        {
            "prompt": "We're going in circles; let it rest.",
            "intent": "direct_answer",
        }
    )
    story = build_conversational_micro_move_plan(
        {
            "prompt": "Want to hear what happened next?",
            "intent": "direct_answer",
        }
    )

    assert "back_up" in _move_names(backing_up)
    assert "let_topic_rest" in _move_names(resting)
    assert "invite_story_continuation" in _move_names(story)


def test_humor_does_not_enter_tender_context_unless_the_user_opens_it():
    tender = build_conversational_micro_move_plan(
        {
            "prompt": "I am grieving Ranger's death.",
            "intent": "direct_answer",
            "affect_expression_guidance": {"dimensions": {"humor": "available_not_required"}},
        }
    )
    user_opened = build_conversational_micro_move_plan(
        {
            "prompt": "Ranger being dead still hurts, but that old muddy-paws story was funny lol.",
            "intent": "direct_answer",
            "affect_expression_guidance": {"dimensions": {"humor": "available_not_required"}},
        }
    )

    assert "one_playful_turn" not in _move_names(tender)
    assert "one_playful_turn" in _move_names(user_opened)


def test_administrative_joke_reference_does_not_create_a_playful_turn():
    plan = build_conversational_micro_move_plan(
        {
            "prompt": "Return to the observation log and keep the drawer joke separate.",
            "intent": "direct_answer",
            "content_seed": "The practical observation log keeps its three fields.",
            "affect_expression_guidance": {"dimensions": {"humor": "available_not_required"}},
        }
    )

    assert "one_playful_turn" not in _move_names(plan)


def test_nlo_exposes_micro_move_and_dream_reflection_plans(tmp_path):
    conn = _conn(tmp_path)
    result = realize_native_language(
        conn,
        {
            "prompt": "Reflect on the Dream pattern.",
            "content_seed": "The recurring thread may be worth comparing with the next cycle.",
            "dream_reflection": {
                "reflection": "A recurring unresolved thread appeared across two review groupings",
                "review_status": "review_only",
                "source_refs": ["dream:cycle:9"],
                "expression_eligible": True,
            },
            "intent_decision": {
                "intent": "reasoning",
                "answer_shape": "best_current_answer",
                "response_depth": "standard",
            },
        },
    )

    plan = result["discourse_plan"]["conversational_micro_move_plan"]
    realized = result["discourse_plan"]["conversational_micro_move_realization"]
    assert result["version"] == "v32_human_conversational_realization"
    assert plan["dream_reflection"]["available"] is True
    assert "dream_reflection" in _move_names(plan)
    assert realized["dream_content_invented"] is False
    assert "Dream surfaced a possible pattern" in result["candidate_text"]
    assert "provisional" in result["candidate_text"]
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
