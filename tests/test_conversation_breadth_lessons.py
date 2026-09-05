from __future__ import annotations

import pytest

from selene.conversation_breadth_lessons import EVIDENCE, LESSONS, SOURCE_FINGERPRINT, TEACHING_GROUP
from selene.db import connect, init_db
from selene.language_teaching_shelf import (
    LANGUAGE_QOL_LESSONS,
    language_teaching_status,
    list_language_teaching_items,
    prepare_language_teaching_shelf,
    select_language_guidance,
)


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_conversation_breadth_set_contains_twelve_source_wording_free_review_blueprints():
    assert len(LESSONS) == 12
    assert len(EVIDENCE) == 12
    assert [lesson["lesson_order"] for lesson in LESSONS] == list(range(1, 13))
    assert all(lesson["teaching_group"] == TEACHING_GROUP for lesson in LESSONS)
    assert all(lesson["group_order"] == 12 for lesson in LESSONS)
    assert all(lesson["key"] in EVIDENCE for lesson in LESSONS)
    assert all(f"source_fingerprint:{SOURCE_FINGERPRINT}" in lesson["source_refs"] for lesson in LESSONS)
    assert not any("#" in ref for lesson in LESSONS for ref in lesson["source_refs"])
    for evidence in EVIDENCE.values():
        assert evidence["vocabulary"]
        assert evidence["near_concept_distinctions"]
        assert evidence["scope_of_application"]
        assert evidence["explanation"]
        assert evidence["distinct_examples"]
        assert evidence["uncertainties"]
        assert evidence["counterexamples"]
        assert evidence["correction_response"]


def test_one_breadth_lesson_can_be_taught_live_idempotently_without_boundary_writes(tmp_path):
    conn = _conn(tmp_path)
    prerequisites = [
        str(lesson["key"])
        for lesson in LANGUAGE_QOL_LESSONS
        if int(lesson.get("group_order") or 1) < 12
    ]
    target = "evidence_grounded_reference_and_callback"
    memory_before = conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0]

    prepared_prerequisites = prepare_language_teaching_shelf(conn, {"lesson_keys": prerequisites})
    first = prepare_language_teaching_shelf(conn, {"lesson_keys": [target]})
    second = prepare_language_teaching_shelf(conn, {"lesson_keys": [target]})
    items = list_language_teaching_items(conn)["items"]
    item = next(entry for entry in items if entry["lesson_key"] == target)
    guidance = select_language_guidance(
        conn,
        {
            "prompt": "Back to the second repair option we discussed earlier.",
            "intent_decision": {"intent": "direct_conversation"},
            "dialogue_workspace": {
                "pragmatics": {
                    "resolved_reference": {"text": "the second repair option"},
                    "session_landmarks": [{"label": "two repair options"}],
                }
            },
        },
    )

    assert prepared_prerequisites["created_count"] == 61
    assert first["requested_lesson_keys"] == [target]
    assert first["created_count"] == 1
    assert first["graduated_count"] == 1
    assert first["held_count"] == 0
    assert second["created_count"] == 0
    assert second["refreshed_count"] == 1
    assert second["graduated_count"] == 0
    assert item["available_to_nlo"] is True
    assert item["lifecycle"]["all_stages_complete"] is True
    assert item["lifecycle"]["standing_language_capability_authorization"] is True
    assert item["source_refs"][0] == "speech_phase_13:evidence_grounded_conversation_breadth"
    assert not any("#" in ref for ref in item["source_refs"])
    assert target in guidance["lesson_keys"]
    assert "restore_relevant_visible_context" in guidance["response_moves"]
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == memory_before
    assert first["memory_write_active"] is False
    assert first["runtime_memory_recall"] is False
    assert first["training_allowed"] is False
    assert first["identity_change"] is False
    assert first["personality_change"] is False
    assert first["governance_change"] is False
    assert first["authority_change"] is False


def test_bounded_language_selector_rejects_unknown_empty_and_duplicate_keys(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError, match="non-empty list"):
        prepare_language_teaching_shelf(conn, {"lesson_keys": []})
    with pytest.raises(ValueError, match="duplicates"):
        prepare_language_teaching_shelf(conn, {"lesson_keys": ["natural_register", "natural_register"]})
    with pytest.raises(ValueError, match="unknown language lesson keys"):
        prepare_language_teaching_shelf(conn, {"lesson_keys": ["not_a_real_lesson"]})


def test_status_exposes_breadth_group_without_requiring_it_to_be_taught(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn, {"lesson_keys": ["natural_register"]})

    status = language_teaching_status(conn)
    group = next(entry for entry in status["teaching_groups"] if entry["group_order"] == 12)

    assert status["defined_lesson_count"] == 81
    assert status["defined_group_count"] == 13
    assert group["teaching_group"] == TEACHING_GROUP
    assert group["defined_lesson_count"] == 12
    assert group["stored_lesson_count"] == 0
    assert group["available_lesson_count"] == 0


def test_callback_lesson_requires_current_turn_callback_evidence(tmp_path):
    conn = _conn(tmp_path)
    target = "evidence_grounded_reference_and_callback"
    prerequisites = [
        str(lesson["key"])
        for lesson in LANGUAGE_QOL_LESSONS
        if int(lesson.get("group_order") or 1) < 12
    ]
    prepare_language_teaching_shelf(conn, {"lesson_keys": prerequisites})
    prepare_language_teaching_shelf(conn, {"lesson_keys": [target]})

    unrelated = select_language_guidance(
        conn,
        {
            "prompt": "Give me your best provisional hypothesis about the vibration.",
            "intent_decision": {"intent": "reasoning"},
            "dialogue_workspace": {
                "pragmatics": {
                    "session_landmarks": [{"summary": "We earlier discussed two shelves."}],
                }
            },
        },
    )
    callback = select_language_guidance(
        conn,
        {
            "prompt": "What part of that result am I celebrating?",
            "intent_decision": {
                "intent": "reasoning",
                "contextual_follow_up": {"kind": "immediate_user_callback"},
            },
            "dialogue_workspace": {
                "pragmatics": {
                    "session_landmarks": [{"summary": "The first live lesson completed."}],
                }
            },
        },
    )

    assert target not in unrelated["lesson_keys"]
    assert target in callback["lesson_keys"]
