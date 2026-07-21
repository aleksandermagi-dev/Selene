from __future__ import annotations

import pytest

from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.language_teaching_shelf import (
    LANGUAGE_QOL_LESSONS,
    _language_range_eligibility,
    build_language_capability_answer,
    language_teaching_status,
    list_language_teaching_items,
    prepare_language_teaching_shelf,
    select_language_guidance,
)
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.teaching_lifecycle import approve_teaching_lifecycle_under_authorization


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _prepare_review_only(conn):
    return prepare_language_teaching_shelf(conn, {"defer_standing_authorization": True})


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


def test_language_shelf_applies_bounded_standing_authorization_and_is_idempotent(tmp_path):
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
    assert first["status"] == "language_teaching_shelf_prepared_under_standing_authorization"
    assert first["graduated_count"] == len(LANGUAGE_QOL_LESSONS)
    assert first["held_count"] == 0
    assert second["graduated_count"] == 0
    assert after["status"] == "language_teaching_guidance_ready"
    assert after["candidate_lesson_count"] == 0
    assert after["available_lesson_count"] == len(LANGUAGE_QOL_LESSONS)
    assert conn.execute("SELECT COUNT(*) FROM selene_language_teaching_shelf").fetchone()[0] == len(LANGUAGE_QOL_LESSONS)
    assert conn.execute("SELECT COUNT(*) FROM selene_comprehension_concepts WHERE concept_key LIKE 'language_lesson:%'").fetchone()[0] == len(LANGUAGE_QOL_LESSONS)
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == memory_candidates_before
    assert first["memory_write_active"] is False
    assert first["training_allowed"] is False
    assert first["voice_personality_changed"] is False
    assert first["language_capability_item_approval_required"] is False
    assert first["standing_authorization"]["authorized_by"] == "Aleks"
    assert first["standing_authorization"]["scope"]["guidance_only"] is True
    assert first["standing_authorization"]["scope"]["authorization_class"] == "language_capability_range"
    lifecycle_modes = conn.execute(
        """
        SELECT DISTINCT lifecycle.approval_status, lifecycle.approval_mode
        FROM selene_teaching_lifecycles AS lifecycle
        JOIN selene_comprehension_concepts AS concept ON concept.id = lifecycle.concept_id
        WHERE concept.concept_key LIKE 'language_lesson:%'
        """
    ).fetchall()
    assert [tuple(row) for row in lifecycle_modes] == [
        ("approved_under_language_capability_authorization", "language_capability_authorization")
    ]
    assert conn.execute(
        "SELECT COUNT(*) FROM selene_curriculum_authorization_events WHERE action = 'language_capability_graduated_under_standing_authorization'"
    ).fetchone()[0] == len(LANGUAGE_QOL_LESSONS)


def test_uncertainty_guidance_uses_middle_ground_without_cocoon_pressure(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)
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


def test_language_lessons_are_guidance_not_answer_bearing_knowledge(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)
    _complete_and_approve(conn, "answer_then_expand")

    packet = route_request(
        conn,
        "comprehension.turn.packet",
        {
            "prompt": "What changed in the conversation lessons?",
            "intent_decision": {
                "intent": "reasoning",
                "reasoning_requested": True,
                "dialogue_acts": ["question"],
            },
        },
    )["result"]
    capability = build_language_capability_answer(
        conn,
        {"prompt": "What changed in the conversation lessons?"},
    )

    assert packet["knowledge_response_seed"] == ""
    assert packet["knowledge_context"]["answer_eligible"] is False
    assert all(not item["concept_key"].startswith("language_lesson:") for item in packet["knowledge_context"]["items"])
    assert capability["used"] is True
    assert capability["lesson_central_claim_used_as_answer"] is False
    assert "What changed is" in capability["content_seed"]
    assert capability["identity_changed"] is False


def test_unavailable_or_held_lessons_are_not_selected(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)
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
    _prepare_review_only(conn)
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
    assert result["version"] == "v18_compositional_special_expression"
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

    assert prepared["status"] == "language_teaching_shelf_prepared_under_standing_authorization"
    assert status["nlo_guidance_available"] is True
    assert len(items["items"]) == len(LANGUAGE_QOL_LESSONS)
    assert preview["lesson_keys"]
    assert all(item["available_to_nlo"] for item in items["items"])
    assert preview["activation_change"] == "none"
    assert preview["autonomous_action_allowed"] is False


def test_lesson_content_and_safety_boundaries_are_separate(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)

    item = next(item for item in list_language_teaching_items(conn)["items"] if item["lesson_key"] == "uncertainty_middle_ground")

    assert item["available_to_nlo"] is False
    assert item["lesson_content"]["concept"]
    assert item["lesson_content"]["review_blueprint"]["acquire"]["uncertainties"]
    assert all(not line.lower().startswith("do not") for line in item["lesson_content"]["review_blueprint"]["acquire"]["uncertainties"])
    assert item["boundaries"]["constraints"]
    assert item["boundaries"]["personality_change_allowed"] is False
    assert item["boundaries"]["provider_used"] is False


def test_standing_authorization_holds_personality_or_meaning_exceptions(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)
    item = next(item for item in list_language_teaching_items(conn)["items"] if item["lesson_key"] == "natural_register")
    lesson = next(lesson for lesson in LANGUAGE_QOL_LESSONS if lesson["key"] == "natural_register")
    unsafe = {**item, "boundaries": {**item["boundaries"], "personality_change_allowed": True}}

    result = _language_range_eligibility(unsafe, lesson)

    assert result["eligible"] is False
    assert "personality_change_allowed" in result["exceptions"]
    assert result["guidance_only"] is True
    assert result["meaning_change_allowed"] is False


def test_language_authorization_cannot_be_reused_without_guidance_only_eligibility(tmp_path):
    conn = _conn(tmp_path)
    prepared = _prepare_review_only(conn)
    item = next(item for item in list_language_teaching_items(conn)["items"] if item["lesson_key"] == "answer_then_expand")
    concept_id = int(item["comprehension_concept_id"])
    blueprint = item["teaching_blueprint"]
    route_request(conn, "teaching.lifecycle.acquire", {"concept_id": concept_id, **blueprint["acquire"]})
    route_request(conn, "teaching.lifecycle.integrate", {"concept_id": concept_id, **blueprint["integrate"]})
    express = blueprint["express"]
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

    with pytest.raises(ValueError, match="out-of-scope material"):
        approve_teaching_lifecycle_under_authorization(
            conn,
            {"concept_id": concept_id},
            {
                "decision": "covered_by_active_authorization",
                "authorization_id": prepared["standing_authorization"]["id"],
                "guidance_only": False,
                "eligibility": {"eligible": True},
            },
        )


def test_prepared_but_unapproved_lesson_cannot_reach_nlo(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)

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

    result = _prepare_review_only(conn)
    item = next(item for item in list_language_teaching_items(conn)["items"] if item["lesson_key"] == "uncertainty_middle_ground")

    assert result["legacy_auto_approved_rows_returned_to_review"] == ["uncertainty_middle_ground"]
    assert item["review_status"] == "pending_comprehension_review"
    assert item["available_to_nlo"] is False
    assert item["boundaries"]["constraints"]
    assert item["lesson_content"]["review_blueprint"]["acquire"]["uncertainties"]


def test_refresh_preserves_explicit_aleks_approval(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)
    _complete_and_approve(conn, "uncertainty_middle_ground")

    refreshed = _prepare_review_only(conn)
    item = next(item for item in list_language_teaching_items(conn)["items"] if item["lesson_key"] == "uncertainty_middle_ground")

    assert refreshed["legacy_auto_approved_rows_returned_to_review"] == []
    assert item["available_to_nlo"] is True
    assert item["lifecycle"]["explicit_aleks_approval"] is True
    assert item["stored_review_status"] == "pending_comprehension_review"
    assert item["review_status"] == "approved_for_language_guidance"
    assert item["status"] == "language_guidance_available"


def test_language_shelf_rejects_authority_expansion_payload(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError, match="cannot change memory"):
        prepare_language_teaching_shelf(conn, {"request": "activate runtime recall"})

    assert list_language_teaching_items(conn)["items"] == []


def test_language_shelf_exposes_ordered_review_groups_and_prerequisites(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)

    status = language_teaching_status(conn)
    items = list_language_teaching_items(conn)["items"]
    groups = status["teaching_groups"]

    assert status["defined_lesson_count"] == 31
    assert status["defined_group_count"] == 6
    assert [group["group_order"] for group in groups] == [1, 2, 3, 4, 5, 6]
    assert [group["defined_lesson_count"] for group in groups] == [10, 4, 4, 4, 4, 5]
    assert [group["available_lesson_count"] for group in groups] == [0, 0, 0, 0, 0, 0]
    assert [(item["group_order"], item["lesson_order"]) for item in items] == sorted(
        (item["group_order"], item["lesson_order"]) for item in items
    )

    explanation = next(item for item in items if item["lesson_key"] == "explain_from_foundation")
    assert explanation["teaching_group"] == "G2 · Explaining and Connecting Ideas"
    assert explanation["prerequisites"] == ["answer_then_expand", "natural_register"]
    assert explanation["source_refs"][0] == "speech_phase_6:reviewed_expressive_breadth"
    assert explanation["available_to_nlo"] is False

    composition = next(item for item in items if item["lesson_key"] == "paraphrase_without_drift")
    assert composition["teaching_group"] == "G5 · Compositional Expression"
    assert composition["prerequisites"] == ["lexical_variation", "information_focus_and_order"]
    assert composition["source_refs"][0] == "speech_phase_7:compositional_expression"
    assert composition["available_to_nlo"] is False

    judgment = next(item for item in items if item["lesson_key"] == "grounded_self_state_expression")
    assert judgment["teaching_group"] == "G6 · Grounded Conversational Judgment"
    assert judgment["prerequisites"] == ["tender_without_overreach", "contextual_word_choice"]
    assert judgment["source_refs"][0] == "speech_phase_8:grounded_conversational_judgment"
    assert judgment["available_to_nlo"] is False


def test_every_expressive_breadth_lesson_has_complete_review_evidence(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)

    expressive_items = [
        item for item in list_language_teaching_items(conn)["items"] if item["group_order"] > 1
    ]

    assert len(expressive_items) == 21
    for item in expressive_items:
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


def test_all_six_groups_can_complete_in_order_without_bypassing_prerequisites_or_writing_memory(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)
    memory_before = conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0]

    for lesson in LANGUAGE_QOL_LESSONS:
        result = _complete_and_approve(conn, str(lesson["key"]))
        assert result["stage_complete"] is True
        assert result["snapshot"]["approval_actor"] == "Aleks"
        assert result["snapshot"]["memory_created"] is False
        assert result["snapshot"]["identity_changed"] is False
        assert result["snapshot"]["personality_changed"] is False

    status = language_teaching_status(conn)
    items = list_language_teaching_items(conn)["items"]

    assert status["available_lesson_count"] == 31
    assert status["candidate_lesson_count"] == 0
    assert [group["available_lesson_count"] for group in status["teaching_groups"]] == [10, 4, 4, 4, 4, 5]
    assert all(item["own_review_complete"] is True for item in items)
    assert all(item["prerequisites_complete"] is True for item in items)
    assert all(item["unmet_prerequisites"] == [] for item in items)
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == memory_before


def test_grounded_judgment_group_graduates_under_standing_language_authorization(tmp_path):
    conn = _conn(tmp_path)
    prepared = prepare_language_teaching_shelf(conn)
    self_state = select_language_guidance(
        conn,
        {"prompt": "How are you feeling right now?", "intent_decision": {"intent": "self_state"}},
    )
    recall = select_language_guidance(
        conn,
        {
            "prompt": "Do you remember that clearly?",
            "intent_decision": {"intent": "memory_recall", "memory_recall_requested": True},
        },
    )

    assert prepared["held_count"] == 0
    assert prepared["graduated_count"] == len(LANGUAGE_QOL_LESSONS)
    assert "grounded_self_state_expression" in self_state["lesson_keys"]
    assert "recall_confidence_expression" in recall["lesson_keys"]
    assert self_state["memory_write_active"] is False
    assert recall["training_allowed"] is False


def test_new_lesson_reaches_guidance_only_after_full_review_and_aleks_approval(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)
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


def test_reviewed_compositional_lesson_drives_nlo_realization_without_adding_content(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)
    for lesson_key in (
        "answer_then_expand",
        "purposeful_follow_up",
        "mixed_intent_balance",
        "information_focus_and_order",
        "lexical_variation",
        "paraphrase_without_drift",
    ):
        _complete_and_approve(conn, lesson_key)

    prompt = "Can you explain in your own words why the reviewed bridge stays bounded?"
    seed = "The bridge uses reviewed language guidance while leaving meaning, memory, identity, and authority unchanged."
    result = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "intent_decision": classify_chat_intent(prompt),
            "content_seed": seed,
        },
    )

    policy = result["meaning_packet"]["language_realization_policy"]
    assert "paraphrase_without_drift" in policy["approved_lesson_keys"]
    assert policy["compositional_surface"] is True
    assert policy["information_focus"] is True
    assert policy["meaning_drift_check"] is True
    assert policy["content_generation_allowed"] is False
    assert result["revision"]["approved_language_realization_applied"] is True
    assert result["candidate_text"] != seed
    assert "reviewed language guidance" in result["candidate_text"]
    assert "memory, identity, and authority unchanged" in result["candidate_text"]
    assert result["revision"]["unsupported_content_generated"] is False
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False


def test_reviewed_rhythm_lesson_changes_developed_clause_composition(tmp_path):
    conn = _conn(tmp_path)
    _prepare_review_only(conn)
    for lesson_key in ("lexical_variation", "natural_register", "syntactic_rhythm_and_emphasis"):
        _complete_and_approve(conn, lesson_key)

    prompt = "Go deeper and explain why the bounded route is useful."
    result = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "intent_decision": classify_chat_intent(prompt),
            "response_depth": "developed",
            "content_seed": "The bounded route lets the supported answer proceed without expanding authority.",
            "intelligence_support": {
                "used": True,
                "confidence": "clear_enough_to_continue",
                "support_points": ["The content source remains visible.", "The authority boundary remains unchanged."],
            },
        },
    )

    policy = result["meaning_packet"]["language_realization_policy"]
    assert "syntactic_rhythm_and_emphasis" in policy["approved_lesson_keys"]
    assert policy["clause_composition"] is True
    assert "clause_composition" in result["revision"]["language_realization_features"]
    assert " is that " in result["candidate_text"]
    assert result["revision"]["paragraph_count"] >= 2
    assert result["revision"]["unsupported_content_generated"] is False
