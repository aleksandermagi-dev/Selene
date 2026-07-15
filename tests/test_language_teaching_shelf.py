from __future__ import annotations

import pytest

from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.language_teaching_shelf import (
    LANGUAGE_QOL_LESSONS,
    language_teaching_status,
    list_language_teaching_items,
    prepare_language_teaching_shelf,
    select_language_guidance,
)
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_language_shelf_is_explicit_and_idempotent(tmp_path):
    conn = _conn(tmp_path)
    memory_candidates_before = conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0]

    before = language_teaching_status(conn)
    first = prepare_language_teaching_shelf(conn)
    second = prepare_language_teaching_shelf(conn)
    after = language_teaching_status(conn)

    assert before["status"] == "language_teaching_shelf_not_prepared"
    assert first["created_count"] == len(LANGUAGE_QOL_LESSONS)
    assert first["refreshed_count"] == 0
    assert second["created_count"] == 0
    assert second["refreshed_count"] == len(LANGUAGE_QOL_LESSONS)
    assert after["status"] == "language_teaching_shelf_ready"
    assert after["available_lesson_count"] == len(LANGUAGE_QOL_LESSONS)
    assert conn.execute("SELECT COUNT(*) FROM selene_language_teaching_shelf").fetchone()[0] == len(LANGUAGE_QOL_LESSONS)
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == memory_candidates_before
    assert first["memory_write_active"] is False
    assert first["training_allowed"] is False
    assert first["voice_personality_changed"] is False


def test_uncertainty_guidance_uses_middle_ground_without_cocoon_pressure(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)

    result = select_language_guidance(
        conn,
        {
            "prompt": "I think I remember it, but the detail is fuzzy. What is your best current read?",
            "intent_decision": {"intent": "recall_uncertain", "memory_recall_requested": True},
        },
    )

    assert result["used"] is True
    assert "uncertainty_middle_ground" in result["lesson_keys"]
    assert "state_best_current_read" in result["response_moves"]
    assert all("cocoon" not in move.lower() for move in result["response_moves"])
    assert result["automatic_content_generation"] is False
    assert result["runtime_memory_recall"] is False


def test_unavailable_or_held_lessons_are_not_selected(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    conn.execute(
        "UPDATE selene_language_teaching_shelf SET status = 'hold_for_tending' WHERE lesson_key = 'uncertainty_middle_ground'"
    )
    conn.commit()

    result = select_language_guidance(
        conn,
        {
            "prompt": "Maybe my memory is fuzzy?",
            "intent_decision": {"intent": "recall_uncertain", "memory_recall_requested": True},
        },
    )

    assert "uncertainty_middle_ground" not in result["lesson_keys"]
    assert language_teaching_status(conn)["available_lesson_count"] == len(LANGUAGE_QOL_LESSONS) - 1


def test_nlo_consults_prepared_shelf_without_changing_voice_or_identity(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    prompt = "How should we compare these two options without turning the answer into a report?"

    result = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "intent_decision": classify_chat_intent(prompt),
            "content_seed": "Compare the decision criteria first, then explain the meaningful tradeoff.",
        },
    )

    guidance = result["language_teaching_guidance"]
    assert result["version"] == "v7_comprehension_integration"
    assert guidance["used"] is True
    assert "answer_then_expand" in guidance["lesson_keys"]
    assert "list_or_prose_fit" in guidance["lesson_keys"]
    assert result["discourse_plan"]["language_guidance_used"] is True
    assert result["revision"]["language_guidance_checked"] is True
    assert result["voice_handoff"]["voice_owns_expression_style"] is True
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False


def test_language_shelf_routes_preserve_boundaries(tmp_path):
    conn = _conn(tmp_path)

    prepared = route_request(conn, "language_teaching.prepare", {})["result"]
    status = route_request(conn, "language_teaching.status", {})["result"]
    items = route_request(conn, "language_teaching.items", {})["result"]
    preview = route_request(
        conn,
        "language_teaching.guidance.preview",
        {"prompt": "Anyway, back to the other question. How should we answer it?", "intent_decision": {"intent": "reasoned_answer"}},
    )["result"]

    assert prepared["status"] == "language_teaching_shelf_prepared"
    assert status["nlo_guidance_available"] is True
    assert len(items["items"]) == len(LANGUAGE_QOL_LESSONS)
    assert "topic_transition_continuity" in preview["lesson_keys"]
    assert preview["activation_change"] == "none"
    assert preview["autonomous_action_allowed"] is False


def test_language_shelf_rejects_authority_expansion_payload(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError, match="cannot change memory"):
        prepare_language_teaching_shelf(conn, {"request": "activate runtime recall"})

    assert list_language_teaching_items(conn)["items"] == []
