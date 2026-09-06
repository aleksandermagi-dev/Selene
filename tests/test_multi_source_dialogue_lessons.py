from __future__ import annotations

from selene.db import connect, init_db
from selene.language_teaching_shelf import (
    LANGUAGE_QOL_LESSONS,
    language_teaching_status,
    list_language_teaching_items,
    prepare_language_teaching_shelf,
    select_language_guidance,
)
from selene.multi_source_dialogue_lessons import EVIDENCE, LESSONS, SOURCE_REFS, TEACHING_GROUP
from selene.native_language_organ import realize_native_language


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_multi_source_group_contains_only_source_free_dialogue_mechanisms():
    serialized = repr((LESSONS, EVIDENCE)).lower()

    assert len(LESSONS) == len(EVIDENCE) == 10
    assert [lesson["lesson_order"] for lesson in LESSONS] == list(range(1, 11))
    assert all(lesson["group_order"] == 15 for lesson in LESSONS)
    assert all(lesson["teaching_group"] == TEACHING_GROUP for lesson in LESSONS)
    assert all(lesson["key"] in EVIDENCE for lesson in LESSONS)
    assert all(
        lesson["teaching_source_type"] == "project_authored_multi_source_dialogue_function_mechanism"
        for lesson in LESSONS
    )
    assert any(ref == "license:CC-BY-4.0" for ref in SOURCE_REFS)
    assert any(ref == "license:CDLA-Sharing-1.0" for ref in SOURCE_REFS)
    assert any(ref == "license:Apache-2.0" for ref in SOURCE_REFS)
    assert "earth, wind & fire" not in serialized
    assert "blade runner" not in serialized
    assert "hamilton" not in serialized
    assert "monopsony" not in serialized

    for evidence in EVIDENCE.values():
        assert evidence["vocabulary"]
        assert evidence["near_concept_distinctions"]
        assert evidence["scope_of_application"]
        assert evidence["explanation"]
        assert evidence["distinct_examples"]
        assert evidence["uncertainties"]
        assert evidence["counterexamples"]
        assert evidence["correction_response"]


def test_multi_source_group_graduates_through_existing_lifecycle_without_memory_write(tmp_path):
    conn = _conn(tmp_path)
    memory_before = conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0]

    prepared = prepare_language_teaching_shelf(conn)
    status = language_teaching_status(conn)
    group = next(item for item in status["teaching_groups"] if item["group_order"] == 15)
    items = [item for item in list_language_teaching_items(conn)["items"] if item["group_order"] == 15]

    assert prepared["created_count"] == prepared["graduated_count"] == len(LANGUAGE_QOL_LESSONS) == 96
    assert prepared["held_count"] == 0
    assert group["teaching_group"] == TEACHING_GROUP
    assert group["defined_lesson_count"] == group["stored_lesson_count"] == group["available_lesson_count"] == 10
    assert all(item["available_to_nlo"] is True for item in items)
    assert all(item["source_refs"][0] == "speech_phase_16:multi_source_dialogue_function_transfer" for item in items)
    assert all(item["boundaries"]["answer_bearing_knowledge"] is False for item in items)
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == memory_before
    assert prepared["memory_write_active"] is False
    assert prepared["runtime_memory_recall"] is False
    assert prepared["identity_change"] is False
    assert prepared["personality_change"] is False
    assert prepared["governance_change"] is False
    assert prepared["authority_change"] is False
    assert prepared["training_allowed"] is False


def test_contextual_answer_rejection_and_changed_constraint_select_on_unfamiliar_wording(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)

    yes_answer = select_language_guidance(
        conn,
        {
            "prompt": "Yeah, after dinner works.",
            "intent_decision": {"intent": "direct_conversation"},
            "dialogue_workspace": {"recent_assistant_texts": ["Would you like to continue after dinner?"]},
        },
    )
    changed = select_language_guidance(
        conn,
        {
            "prompt": "No thanks, that route will not work. Actually, keep the budget but use the local option instead.",
            "intent_decision": {"intent": "correction"},
            "dialogue_workspace": {
                "pragmatics": {
                    "response_obligations": [{"id": "reject"}, {"id": "replace"}],
                    "utterance_units": [{"kind": "boundary"}, {"kind": "correction"}],
                }
            },
        },
    )

    assert "contextual_yes_no_completion" in yes_answer["lesson_keys"]
    assert "reattach_answer_to_pending_question" in yes_answer["response_moves"]
    assert "rejection_acceptance_and_redirection" in changed["lesson_keys"]
    assert "changed_constraint_state_rebuild" in changed["lesson_keys"]
    assert "constraint_summary_and_confirmation" in changed["lesson_keys"]
    assert changed["memory_write_active"] is False
    assert changed["automatic_content_generation"] is False


def test_disfluency_topic_development_and_branching_reach_nlo_as_guidance_only(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    prompt = "I mean... I think the first idea almost works. What is another way to approach it?"

    guidance = select_language_guidance(
        conn,
        {
            "prompt": prompt,
            "intent_decision": {"intent": "direct_conversation", "social_turn": True},
            "dialogue_workspace": {"recent_assistant_texts": ["The first approach depends on the remote service."]},
        },
    )
    realized = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "intent_decision": {"intent": "direct_conversation", "social_turn": True},
            "dialogue_workspace": {"recent_assistant_texts": ["The first approach depends on the remote service."]},
            "language_teaching_guidance": guidance,
            "content_seed": "A local-only route avoids that dependency.",
        },
    )
    policy = realized["meaning_packet"]["language_realization_policy"]

    assert "informal_disfluency_meaning_reconstruction" in guidance["lesson_keys"]
    assert "branching_alternatives_and_revision" in guidance["lesson_keys"]
    assert policy["disfluency_reconstruction"] is True
    assert policy["branching_revision"] is True
    assert policy["content_generation_allowed"] is False
    assert policy["meaning_change_allowed"] is False
    assert realized["memory_write_active"] is False
    assert realized["training_allowed"] is False
