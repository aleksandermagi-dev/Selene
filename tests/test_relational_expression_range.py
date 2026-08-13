from __future__ import annotations

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.relational_expression_range import (
    build_relational_expression_range,
    relational_expression_range_status,
)


def _assert_bounded(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_corpus_access_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["fact_generation_allowed"] is False
    assert result["emotion_claim_created"] is False
    assert result["hidden_chain_of_thought_exposed"] is False


def _selected(result):
    return set(result["selected_channel_names"])


def test_status_keeps_expression_available_without_making_any_move_required():
    status = relational_expression_range_status()

    assert status["status"] == "relational_expression_range_ready"
    assert status["none_selected_is_valid"] is True
    assert status["warmth_may_be_selene_initiated"] is True
    assert status["humor_may_be_selene_initiated"] is True
    assert status["enthusiasm_may_be_selene_initiated"] is True
    assert status["follow_up_question_required"] is False
    assert status["random_decoration_allowed"] is False
    assert set(status["available_channels"]) >= {
        "warmth",
        "humor",
        "callback",
        "topic_pivot",
        "interpretation",
        "question",
        "closure",
    }
    _assert_bounded(status)


def test_ordinary_direct_answer_may_remain_plain_without_suppressing_warmth():
    result = build_relational_expression_range(
        {
            "prompt": "Explain the next step.",
            "intent": "direct_answer",
            "content_seed": "Run the bounded check next.",
            "affect_expression_guidance": {
                "expression_posture": "ordinary_attentive",
                "dimensions": {
                    "pacing": "natural",
                    "sentence_rhythm": "natural",
                    "warmth": "baseline",
                    "humor": "context_only",
                    "enthusiasm": "ordinary",
                    "emotional_intensity": "ordinary",
                },
            },
            "pragmatic_continuity": {
                "ending_decision": {
                    "mode": "answer_and_stop_when_complete",
                    "question_allowed": False,
                }
            },
        }
    )

    assert result["selected_optional_visible_count"] == 0
    assert "warmth" not in _selected(result)
    assert "humor" not in _selected(result)
    assert "question" not in _selected(result)
    assert {"pacing", "sentence_rhythm", "emotional_intensity", "closure"} <= _selected(result)
    assert result["expression_is_available_not_compulsory_or_suppressed"] is True
    _assert_bounded(result)


def test_visible_progress_and_play_can_select_enthusiasm_warmth_and_humor():
    result = build_relational_expression_range(
        {
            "prompt": "We did it, that worked! xD",
            "intent": "warm_connection",
            "affect_expression_guidance": {
                "expression_posture": "play_available",
                "dimensions": {
                    "pacing": "lively",
                    "sentence_rhythm": "varied",
                    "warmth": "available",
                    "humor": "available_not_required",
                    "enthusiasm": "lively_available",
                    "emotional_intensity": "lively",
                },
            },
            "conversational_micro_move_plan": {
                "moves": [
                    {"move": "celebrate_visible_milestone", "placement": "before_answer"},
                    {"move": "one_playful_turn", "placement": "after_answer"},
                ]
            },
        }
    )

    assert {"warmth", "enthusiasm", "humor", "acknowledgement"} <= _selected(result)
    assert result["selected_optional_visible_count"] == 4
    _assert_bounded(result)


def test_tender_context_holds_humor_unless_the_user_visibly_opens_play():
    held = build_relational_expression_range(
        {
            "prompt": "Today has been a hard day and I am grieving.",
            "affect_expression_guidance": {
                "dimensions": {"humor": "available_when_context_welcomes_it"}
            },
        }
    )
    opened = build_relational_expression_range(
        {
            "prompt": "Grief is strange, but that part made me laugh lol.",
            "affect_expression_guidance": {
                "dimensions": {"humor": "available_when_context_welcomes_it"}
            },
        }
    )

    assert "humor" not in _selected(held)
    assert "humor" in _selected(opened)
    _assert_bounded(held)
    _assert_bounded(opened)


def test_visible_context_selects_callback_and_pivot_without_inventing_history():
    with_history = build_relational_expression_range(
        {
            "contextual_follow_up": {
                "kind": "named_callback",
                "previous_assistant_preview": "Start with the reversible trial.",
            },
            "conversation_context": {
                "previous_turn": {
                    "role": "selene",
                    "preview": "Start with the reversible trial.",
                }
            },
            "pragmatic_continuity": {
                "topic_transition": {"kind": "explicit_return"},
            },
        }
    )
    without_history = build_relational_expression_range(
        {"contextual_follow_up": {"kind": "named_callback"}}
    )

    assert {"callback", "topic_pivot"} <= _selected(with_history)
    assert "callback" not in _selected(without_history)


def test_question_requires_a_supplied_material_question_and_ending_permission():
    allowed = build_relational_expression_range(
        {
            "pragmatic_continuity": {
                "ending_decision": {"question_allowed": True}
            },
            "generative_thought_expression": {
                "selected_kind": "collaborative_question",
                "expression_text": "Would comparing the two traces separate those explanations?",
            },
        }
    )
    blocked = build_relational_expression_range(
        {
            "pragmatic_continuity": {
                "ending_decision": {"question_allowed": False}
            },
            "generative_thought_expression": {
                "selected_kind": "collaborative_question",
                "expression_text": "Would comparing the two traces separate those explanations?",
            },
        }
    )

    assert "question" in _selected(allowed)
    assert "question" not in _selected(blocked)
    assert allowed["follow_up_question_added_by_range"] is False


def test_interpretation_is_selected_only_from_an_upstream_revisable_packet():
    selected = build_relational_expression_range(
        {
            "exploratory_reasoning": {
                "selected_for_answer": True,
                "response_kind": "open_hypothesis",
            },
            "epistemic_composition": {"dominant_state": "open_hypothesis"},
        }
    )
    ordinary = build_relational_expression_range(
        {"epistemic_composition": {"dominant_state": "supported_answer"}}
    )

    assert "interpretation" in _selected(selected)
    assert "interpretation" not in _selected(ordinary)
    assert selected["meaning_change_allowed"] is False
    _assert_bounded(selected)


def test_exact_answers_and_boundaries_keep_their_meaning_locks():
    result = build_relational_expression_range(
        {
            "prompt": "Give the exact result, and I am excited we solved it!",
            "exact_structure_locked": True,
            "hard_boundary": True,
            "affect_expression_guidance": {
                "dimensions": {
                    "warmth": "connection_without_softening_boundary",
                    "enthusiasm": "available_if_it_does_not_encourage_blocked_action",
                }
            },
        }
    )

    assert result["exact_structure_locked"] is True
    assert result["hard_boundary"] is True
    assert result["meaning_change_allowed"] is False
    assert result["certainty_change_allowed"] is False
    assert result["source_change_allowed"] is False
    assert any(
        item["channel"] == "surface_recomposition"
        for item in result["held_or_unused_channels"]
    )
    assert any(
        item["channel"] == "meaning_softening"
        for item in result["held_or_unused_channels"]
    )
    _assert_bounded(result)


def test_nlo_and_read_only_routes_expose_the_same_inspectable_coordinator(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    nlo = realize_native_language(
        conn,
        {
            "prompt": "We did it—this is fantastic!",
            "content_seed": "The bounded check passed.",
            "intent_decision": {
                "intent": "direct_answer",
                "answer_shape": "best_current_answer",
                "response_depth": "standard",
            },
        },
    )
    changes_before_routes = conn.total_changes
    status = route_request(conn, "native_language.relational_expression.status")["result"]
    preview = route_request(
        conn,
        "native_language.relational_expression.preview",
        {"prompt": "We did it, that worked! xD", "intent": "warm_connection"},
    )["result"]

    plan = nlo["discourse_plan"]["relational_expression_range"]
    assert plan["status"] == "relational_expression_range_selected"
    assert nlo["relational_expression_range"] == plan
    assert nlo["voice_handoff"]["relational_expression_range"] == plan
    assert nlo["discourse_plan"]["contextual_composition_plan"][
        "relational_expression_range"
    ]["status"] == "relational_expression_range_selected"
    assert nlo["discourse_plan"]["human_conversational_plan"][
        "relational_expression_range"
    ]["status"] == "relational_expression_range_selected"
    assert status["status"] == "relational_expression_range_ready"
    assert preview["status"] == "relational_expression_range_selected"
    assert conn.total_changes == changes_before_routes
    _assert_bounded(plan)
