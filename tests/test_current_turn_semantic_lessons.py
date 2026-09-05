from __future__ import annotations

from selene.current_turn_semantic_lessons import EVIDENCE, LESSONS, SOURCE_FINGERPRINT, TEACHING_GROUP
from selene.db import connect, init_db
from selene.language_teaching_shelf import (
    LANGUAGE_QOL_LESSONS,
    language_teaching_status,
    list_language_teaching_items,
    prepare_language_teaching_shelf,
    select_language_guidance,
)
from selene.relational_context import interpret_relational_context
from selene.social_language_realizer import build_content_light_plan


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_current_turn_group_has_eight_source_free_mechanism_lessons():
    assert len(LESSONS) == 8
    assert len(EVIDENCE) == 8
    assert [lesson["lesson_order"] for lesson in LESSONS] == list(range(1, 9))
    assert all(lesson["teaching_group"] == TEACHING_GROUP for lesson in LESSONS)
    assert all(lesson["group_order"] == 13 for lesson in LESSONS)
    assert all(lesson["key"] in EVIDENCE for lesson in LESSONS)
    assert all(f"source_fingerprint:{SOURCE_FINGERPRINT}" in lesson["source_refs"] for lesson in LESSONS)
    assert not any("#" in ref for lesson in LESSONS for ref in lesson["source_refs"])
    assert all(
        lesson["teaching_source_type"]
        == "project_authored_private_corpus_current_turn_semantic_mechanism"
        for lesson in LESSONS
    )
    for evidence in EVIDENCE.values():
        assert evidence["vocabulary"]
        assert evidence["near_concept_distinctions"]
        assert evidence["scope_of_application"]
        assert evidence["explanation"]
        assert evidence["distinct_examples"]
        assert evidence["uncertainties"]
        assert evidence["counterexamples"]
        assert evidence["correction_response"]


def test_current_turn_group_completes_existing_teaching_lifecycle_without_boundary_writes(tmp_path):
    conn = _conn(tmp_path)
    memory_before = conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0]

    first = prepare_language_teaching_shelf(conn)
    second = prepare_language_teaching_shelf(
        conn,
        {"lesson_keys": [str(lesson["key"]) for lesson in LESSONS]},
    )
    status = language_teaching_status(conn)
    group = next(item for item in status["teaching_groups"] if item["group_order"] == 13)
    stored = {
        item["lesson_key"]: item
        for item in list_language_teaching_items(conn)["items"]
        if item["group_order"] == 13
    }

    assert first["created_count"] == len(LANGUAGE_QOL_LESSONS) == 81
    assert first["graduated_count"] == 81
    assert second["created_count"] == 0
    assert second["refreshed_count"] == 8
    assert group["teaching_group"] == TEACHING_GROUP
    assert group["defined_lesson_count"] == 8
    assert group["stored_lesson_count"] == 8
    assert group["available_lesson_count"] == 8
    assert all(item["available_to_nlo"] is True for item in stored.values())
    assert all(item["lifecycle"]["all_stages_complete"] is True for item in stored.values())
    assert all(
        item["lifecycle"]["standing_language_capability_authorization"] is True
        for item in stored.values()
    )
    assert stored["current_turn_meaning_bearing_response"]["source_refs"][0] == (
        "speech_phase_14:current_turn_semantic_conversation"
    )
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == memory_before
    assert first["memory_write_active"] is False
    assert first["runtime_memory_recall"] is False
    assert first["training_allowed"] is False
    assert first["identity_change"] is False
    assert first["personality_change"] is False
    assert first["governance_change"] is False
    assert first["authority_change"] is False


def test_shared_feeling_and_playful_address_select_current_turn_guidance(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)

    feeling_text = "It makes me happy that we are this close <3"
    feeling_relational = interpret_relational_context(
        feeling_text,
        speaker_context={
            "claimed_speaker": "Aleks",
            "purpose": "conversation",
            "authentication_strength": "local_desktop_session",
        },
    )
    feeling = select_language_guidance(
        conn,
        {
            "prompt": feeling_text,
            "intent_decision": {
                "intent": "warm_connection",
                "relational_context": feeling_relational,
            },
            "dialogue_workspace": {},
        },
    )
    playful_text = "Selene beannnn"
    playful_relational = interpret_relational_context(
        playful_text,
        speaker_context={
            "claimed_speaker": "Aleks",
            "purpose": "conversation",
            "authentication_strength": "local_desktop_session",
        },
    )
    playful = select_language_guidance(
        conn,
        {
            "prompt": playful_text,
            "intent_decision": {
                "intent": "playful_connection",
                "relational_context": playful_relational,
            },
            "dialogue_workspace": {},
        },
    )
    plan = build_content_light_plan(
        {
            "prompt": feeling_text,
            "relational_context": feeling_relational,
            "language_teaching_guidance": feeling,
        }
    )

    assert "current_turn_shared_affect_reciprocity" in feeling["lesson_keys"]
    assert "current_turn_meaning_bearing_response" in feeling["lesson_keys"]
    assert "current_turn_playful_vocative_presence" in playful["lesson_keys"]
    assert plan["language_guidance_used"] is True
    assert "current_turn_shared_affect_reciprocity" in plan["language_lesson_keys"]
    assert "choose_fitting_relational_stance" in plan["approved_response_moves"]
    assert plan["current_turn_response_semantics"]["teaching_guidance_supplies_wording"] is False
    assert plan["factual_content_generation_allowed"] is False
    assert plan["response_stance_is_durable_emotion_record"] is False


def test_unfamiliar_expressive_name_elongation_reaches_playful_vocative_guidance(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    prompt = "Seleneeeee!"
    relational = interpret_relational_context(
        prompt,
        speaker_context={
            "claimed_speaker": "Aleks",
            "purpose": "conversation",
            "authentication_strength": "local_desktop_session",
        },
    )

    guidance = select_language_guidance(
        conn,
        {
            "prompt": prompt,
            "intent_decision": {
                "intent": "direct_conversation",
                "social_turn": False,
                "relational_context": relational,
            },
            "dialogue_workspace": {},
        },
    )

    assert "affectionate_vocative" in relational["cue_types"]
    assert "current_turn_playful_vocative_presence" in guidance["lesson_keys"]
    assert guidance["automatic_content_generation"] is False
