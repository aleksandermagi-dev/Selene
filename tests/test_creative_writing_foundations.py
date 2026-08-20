from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.creative_writing_foundations import EVIDENCE, LESSONS, SOURCE_REFS, TEACHING_GROUP
from selene.db import connect, init_db
from selene.language_teaching_shelf import (
    LANGUAGE_QOL_LESSONS,
    language_teaching_status,
    list_language_teaching_items,
    prepare_language_teaching_shelf,
    select_language_guidance,
)
from selene.native_language_organ import realize_native_language


CREATIVE_KEYS = {str(lesson["key"]) for lesson in LESSONS}


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False


def test_creative_writing_group_is_complete_original_and_ordered():
    assert len(LESSONS) == 6
    assert len(LANGUAGE_QOL_LESSONS) == 73
    assert [lesson["lesson_order"] for lesson in LESSONS] == list(range(1, 7))
    assert all(lesson["teaching_group"] == TEACHING_GROUP for lesson in LESSONS)
    assert all(lesson["group_order"] == 10 for lesson in LESSONS)
    assert all(lesson["teaching_source_type"] == "project_authored_provider_free_language_lesson" for lesson in LESSONS)
    assert set(EVIDENCE) == CREATIVE_KEYS
    assert "style_boundary:no_living_author_or_source_persona_imitation" in SOURCE_REFS
    assert "copyright_boundary:no_whole_modern_book_import_no_raw_corpus_recall" in SOURCE_REFS
    for lesson in LESSONS:
        evidence = EVIDENCE[lesson["key"]]
        assert lesson["purpose"] and lesson["response_moves"] and lesson["constraints"]
        assert evidence["vocabulary"] and evidence["near_concept_distinctions"]
        assert evidence["explanation"] and "works" in evidence["explanation"].lower()
        assert evidence["distinct_examples"] and evidence["counterexamples"]
        assert evidence["questions"] and evidence["correction_response"]


def test_creative_group_completes_acquire_integrate_express_under_standing_authorization(tmp_path):
    conn = _conn(tmp_path)
    memory_before = conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0]

    prepared = prepare_language_teaching_shelf(conn)
    status = language_teaching_status(conn)
    items = [item for item in list_language_teaching_items(conn)["items"] if item["group_order"] == 10]

    assert prepared["graduated_count"] == len(LANGUAGE_QOL_LESSONS)
    assert prepared["held_count"] == 0
    assert status["defined_group_count"] == 12
    creative_group = next(group for group in status["teaching_groups"] if group["group_order"] == 10)
    assert creative_group["teaching_group"] == TEACHING_GROUP
    assert creative_group["available_lesson_count"] == 6
    assert len(items) == 6
    assert all(item["available_to_nlo"] is True for item in items)
    assert all(item["lifecycle"]["all_stages_complete"] is True for item in items)
    assert all(item["lifecycle"]["standing_language_capability_authorization"] is True for item in items)
    assert all(item["boundaries"]["answer_bearing_knowledge"] is False for item in items)
    assert all(item["boundaries"]["source_persona_imitation_allowed"] is False for item in items)
    assert all(item["source_refs"][0] == "speech_phase_11:creative_writing_and_voice_foundations" for item in items)
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == memory_before
    _assert_locked(prepared)


def test_creative_guidance_selects_by_requested_technique_not_ordinary_chat(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)

    creative = select_language_guidance(
        conn,
        {
            "prompt": "Rewrite this scene's dialogue and metaphor, then explain why the revision works.",
            "intent_decision": {"intent": "creative_request", "response_depth": "developed"},
        },
    )
    ordinary = select_language_guidance(
        conn,
        {"prompt": "Good morning :) How are you?", "intent_decision": {"intent": "greeting"}},
    )

    assert "creative_revision_for_effect_without_imitation" in creative["lesson_keys"]
    assert "dialogue_subtext_and_turn_motion" in creative["lesson_keys"]
    assert "figurative_mapping_with_limits" in creative["lesson_keys"]
    assert not (CREATIVE_KEYS & set(ordinary["lesson_keys"]))
    assert creative["automatic_content_generation"] is False
    _assert_locked(creative)


def test_nlo_receives_creative_technique_policy_without_content_or_personality_authority(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    prompt = "Rewrite this scene's dialogue and metaphor, then explain why the revision works."
    seed = "The character closes the workshop door and decides to return tomorrow."

    result = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "intent_decision": classify_chat_intent(prompt),
            "content_seed": seed,
        },
    )
    policy = result["meaning_packet"]["language_realization_policy"]

    assert policy["purpose_led_revision"] is True
    assert policy["dialogue_subtext"] is True
    assert policy["figurative_mapping"] is True
    assert policy["content_generation_allowed"] is False
    assert policy["meaning_change_allowed"] is False
    assert policy["personality_change_allowed"] is False
    assert result["voice_handoff"]["expression_contract"]["expression_is_coordinated"] is True
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
