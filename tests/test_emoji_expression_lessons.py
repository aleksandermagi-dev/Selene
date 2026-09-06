from __future__ import annotations

from selene.db import connect, init_db
from selene.emoji_expression_lessons import EVIDENCE, LESSONS, TEACHING_GROUP
from selene.language_teaching_shelf import (
    LANGUAGE_QOL_LESSONS,
    language_teaching_status,
    list_language_teaching_items,
    prepare_language_teaching_shelf,
    select_language_guidance,
)
from selene.relational_context import interpret_relational_context


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_g14_has_five_source_free_contextual_symbol_lessons():
    assert len(LESSONS) == len(EVIDENCE) == 5
    assert [item["lesson_order"] for item in LESSONS] == [1, 2, 3, 4, 5]
    assert all(item["teaching_group"] == TEACHING_GROUP for item in LESSONS)
    assert all(item["group_order"] == 14 for item in LESSONS)
    assert all(
        item["teaching_source_type"]
        == "project_authored_contextual_emoji_expression_mechanism"
        for item in LESSONS
    )
    assert not any("private_corpus:" in ref for item in LESSONS for ref in item["source_refs"])
    for evidence in EVIDENCE.values():
        assert evidence["vocabulary"]
        assert evidence["near_concept_distinctions"]
        assert evidence["uncertainties"]
        assert evidence["counterexamples"]
        assert evidence["scope_of_application"]
        assert evidence["explanation"]
        assert evidence["distinct_examples"]
        assert evidence["conversational_participation"]
        assert evidence["correction_response"]


def test_g14_completes_existing_lifecycle_without_boundary_writes(tmp_path):
    conn = _conn(tmp_path)
    memory_before = conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0]

    first = prepare_language_teaching_shelf(conn)
    second = prepare_language_teaching_shelf(
        conn,
        {"lesson_keys": [str(item["key"]) for item in LESSONS]},
    )
    status = language_teaching_status(conn)
    group = next(item for item in status["teaching_groups"] if item["group_order"] == 14)
    stored = {
        item["lesson_key"]: item
        for item in list_language_teaching_items(conn)["items"]
        if item["group_order"] == 14
    }

    assert first["created_count"] == first["graduated_count"] == len(LANGUAGE_QOL_LESSONS) == 86
    assert second["created_count"] == 0
    assert second["refreshed_count"] == 5
    assert group["teaching_group"] == TEACHING_GROUP
    assert group["defined_lesson_count"] == 5
    assert group["available_lesson_count"] == 5
    assert all(item["available_to_nlo"] is True for item in stored.values())
    assert all(item["lifecycle"]["all_stages_complete"] is True for item in stored.values())
    assert all(
        item["lifecycle"]["standing_language_capability_authorization"] is True
        for item in stored.values()
    )
    assert stored["emoji_as_contextual_written_meaning"]["source_refs"][0] == (
        "speech_phase_15:emoji_and_symbolic_conversation"
    )
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == memory_before
    assert first["memory_write_active"] is False
    assert first["identity_change"] is False
    assert first["personality_change"] is False
    assert first["governance_change"] is False
    assert first["authority_change"] is False
    assert first["training_allowed"] is False


def test_emoji_context_selects_specific_g14_guidance(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)

    celebration_prompt = "we actually did it 🎉"
    celebration = select_language_guidance(
        conn,
        {
            "prompt": celebration_prompt,
            "intent_decision": {
                "intent": "warm_connection",
                "social_turn": True,
                "relational_context": interpret_relational_context(celebration_prompt),
            },
            "dialogue_workspace": {},
        },
    )
    ambiguous_prompt = "😭"
    ambiguous = select_language_guidance(
        conn,
        {
            "prompt": ambiguous_prompt,
            "intent_decision": {
                "intent": "direct_conversation",
                "relational_context": interpret_relational_context(ambiguous_prompt),
            },
            "dialogue_workspace": {},
        },
    )

    assert "emoji_as_contextual_written_meaning" in celebration["lesson_keys"]
    assert "mixed_text_emoji_cadence" in celebration["lesson_keys"]
    assert "optional_authored_emoji_expression" in celebration["lesson_keys"]
    assert "emoji_context_and_ambiguity" in ambiguous["lesson_keys"]
    assert "emoji_only_complete_social_turn" in ambiguous["lesson_keys"]
    assert ambiguous["automatic_content_generation"] is False
