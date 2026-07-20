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


def _complete_and_approve(conn, lesson_key: str):
    item = next(item for item in list_language_teaching_items(conn)["items"] if item["lesson_key"] == lesson_key)
    concept_id = int(item["comprehension_concept_id"])
    blueprint = item["teaching_blueprint"]
    acquire = blueprint["acquire"]
    integrate = blueprint["integrate"]
    express = blueprint["express"]
    route_request(conn, "teaching.lifecycle.acquire", {"concept_id": concept_id, **acquire})
    route_request(conn, "teaching.lifecycle.integrate", {"concept_id": concept_id, **integrate})
    route_request(
        conn,
        "teaching.lifecycle.express",
        {
            "concept_id": concept_id,
            "explanation": express["teach_back"],
            "distinct_examples": express["application"],
            "limits": express["limits"],
            "counterexamples": express["counterexamples"],
            "correction_response": express["correction_response"],
            "analogies": express["analogies"],
            "questions": express["questions"],
            "comparisons": express["comparisons"],
            "conversational_participation": express["conversational_participation"],
            "source_alignment": True,
        },
    )
    return route_request(
        conn,
        "teaching.lifecycle.approve",
        {"concept_id": concept_id, "aleks_approved": True, "approval_actor": "Aleks"},
    )["result"]


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
    assert after["status"] == "language_teaching_candidates_awaiting_review"
    assert after["candidate_lesson_count"] == len(LANGUAGE_QOL_LESSONS)
    assert after["available_lesson_count"] == 0
    assert conn.execute("SELECT COUNT(*) FROM selene_language_teaching_shelf").fetchone()[0] == len(LANGUAGE_QOL_LESSONS)
    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts WHERE concept_key LIKE 'language_lesson:%'").fetchone()[0] == len(LANGUAGE_QOL_LESSONS)
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == memory_candidates_before
    assert first["memory_write_active"] is False
    assert first["training_allowed"] is False
    assert first["voice_personality_changed"] is False


def test_uncertainty_guidance_uses_middle_ground_without_cocoon_pressure(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    _complete_and_approve(conn, "uncertainty_middle_ground")

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
    _complete_and_approve(conn, "uncertainty_middle_ground")
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
    assert language_teaching_status(conn)["available_lesson_count"] == 0


def test_nlo_consults_prepared_shelf_without_changing_voice_or_identity(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    _complete_and_approve(conn, "answer_then_expand")
    _complete_and_approve(conn, "list_or_prose_fit")
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
    assert result["version"] == "v12_pragmatic_continuity"
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

    assert prepared["status"] == "language_teaching_review_candidates_prepared"
    assert status["nlo_guidance_available"] is False
    assert len(items["items"]) == len(LANGUAGE_QOL_LESSONS)
    assert preview["lesson_keys"] == []
    assert preview["activation_change"] == "none"
    assert preview["autonomous_action_allowed"] is False


def test_lesson_content_and_safety_boundaries_are_separate(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)

    item = next(item for item in list_language_teaching_items(conn)["items"] if item["lesson_key"] == "uncertainty_middle_ground")

    assert item["available_to_nlo"] is False
    assert item["lesson_content"]["concept"]
    assert item["lesson_content"]["review_blueprint"]["acquire"]["uncertainties"]
    assert all(not line.lower().startswith("do not") for line in item["lesson_content"]["review_blueprint"]["acquire"]["uncertainties"])
    assert item["boundaries"]["constraints"]
    assert item["boundaries"]["personality_change_allowed"] is False
    assert item["boundaries"]["provider_used"] is False


def test_prepared_but_unapproved_lesson_cannot_reach_nlo(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)

    result = select_language_guidance(
        conn,
        {"prompt": "Maybe my memory is fuzzy?", "intent_decision": {"intent": "recall_uncertain", "memory_recall_requested": True}},
    )

    assert result["used"] is False
    assert result["lesson_keys"] == []
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False


def test_legacy_auto_approved_rows_return_to_review_once(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        """
        INSERT INTO selene_language_teaching_shelf
        (lesson_key, title, category, purpose, guidance_json, source_refs,
         provenance_boundary, review_status, status)
        VALUES ('uncertainty_middle_ground', 'Legacy uncertainty', 'uncertainty',
                'Legacy mixed field', '{}', '[]', 'legacy_boundary',
                'approved_for_language_guidance', 'language_guidance_available')
        """
    )
    conn.commit()

    result = prepare_language_teaching_shelf(conn)
    item = next(item for item in list_language_teaching_items(conn)["items"] if item["lesson_key"] == "uncertainty_middle_ground")

    assert result["legacy_auto_approved_rows_returned_to_review"] == ["uncertainty_middle_ground"]
    assert item["review_status"] == "pending_comprehension_review"
    assert item["available_to_nlo"] is False
    assert item["boundaries"]["constraints"]
    assert item["lesson_content"]["review_blueprint"]["acquire"]["uncertainties"]


def test_refresh_preserves_explicit_aleks_approval(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    _complete_and_approve(conn, "uncertainty_middle_ground")

    refreshed = prepare_language_teaching_shelf(conn)
    item = next(item for item in list_language_teaching_items(conn)["items"] if item["lesson_key"] == "uncertainty_middle_ground")

    assert refreshed["legacy_auto_approved_rows_returned_to_review"] == []
    assert item["available_to_nlo"] is True
    assert item["lifecycle"]["explicit_aleks_approval"] is True


def test_language_shelf_rejects_authority_expansion_payload(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError, match="cannot change memory"):
        prepare_language_teaching_shelf(conn, {"request": "activate runtime recall"})

    assert list_language_teaching_items(conn)["items"] == []


def test_language_shelf_exposes_ordered_review_groups_and_prerequisites(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)

    status = language_teaching_status(conn)
    items = list_language_teaching_items(conn)["items"]
    groups = status["teaching_groups"]

    assert status["defined_lesson_count"] == 22
    assert status["defined_group_count"] == 4
    assert [group["group_order"] for group in groups] == [1, 2, 3, 4]
    assert [group["defined_lesson_count"] for group in groups] == [10, 4, 4, 4]
    assert [group["available_lesson_count"] for group in groups] == [0, 0, 0, 0]
    assert [(item["group_order"], item["lesson_order"]) for item in items] == sorted(
        (item["group_order"], item["lesson_order"]) for item in items
    )

    explanation = next(item for item in items if item["lesson_key"] == "explain_from_foundation")
    assert explanation["teaching_group"] == "G2 · Explaining and Connecting Ideas"
    assert explanation["prerequisites"] == ["answer_then_expand", "natural_register"]
    assert explanation["source_refs"][0] == "speech_phase_6:reviewed_expressive_breadth"
    assert explanation["available_to_nlo"] is False


def test_every_expressive_breadth_lesson_has_complete_review_evidence(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)

    phase_six_items = [
        item for item in list_language_teaching_items(conn)["items"] if item["group_order"] > 1
    ]

    assert len(phase_six_items) == 12
    for item in phase_six_items:
        blueprint = item["teaching_blueprint"]
        assert blueprint["acquire"]["vocabulary"]
        assert blueprint["acquire"]["near_concept_distinctions"]
        assert blueprint["integrate"]["scope_of_application"]
        assert blueprint["express"]["teach_back"]
        assert blueprint["express"]["application"]
        assert blueprint["express"]["limits"]
        assert blueprint["express"]["counterexamples"]
        assert blueprint["express"]["correction_response"]
        assert blueprint["express"]["source_alignment"] is False
        assert item["available_to_nlo"] is False


def test_new_lesson_reaches_guidance_only_after_full_review_and_aleks_approval(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    prompt = "I disagree with that conclusion. Can we compare the assumption and evidence?"

    before = select_language_guidance(
        conn,
        {"prompt": prompt, "intent_decision": {"intent": "reasoned_answer"}},
    )
    _complete_and_approve(conn, "respectful_disagreement")
    blocked = next(
        item for item in list_language_teaching_items(conn)["items"] if item["lesson_key"] == "respectful_disagreement"
    )
    blocked_guidance = select_language_guidance(
        conn,
        {"prompt": prompt, "intent_decision": {"intent": "reasoned_answer"}},
    )
    _complete_and_approve(conn, "uncertainty_middle_ground")
    _complete_and_approve(conn, "natural_register")
    after = select_language_guidance(
        conn,
        {"prompt": prompt, "intent_decision": {"intent": "reasoned_answer"}},
    )

    assert "respectful_disagreement" not in before["lesson_keys"]
    assert blocked["own_review_complete"] is True
    assert blocked["available_to_nlo"] is False
    assert blocked["unmet_prerequisites"] == ["uncertainty_middle_ground", "natural_register"]
    assert "respectful_disagreement" not in blocked_guidance["lesson_keys"]
    assert "respectful_disagreement" in after["lesson_keys"]
    assert "state_disagreement_clearly" in after["response_moves"]
    assert language_teaching_status(conn)["available_lesson_count"] == 3
    assert after["memory_write_active"] is False
    assert after["training_allowed"] is False
