from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.language_teaching_shelf import (
    LANGUAGE_QOL_LESSONS,
    language_teaching_status,
    list_language_teaching_items,
    prepare_language_teaching_shelf,
    select_language_guidance,
)
from selene.native_language_organ import realize_native_language
from selene.public_domain_creative_reading import EVIDENCE, LESSONS, SOURCE_WORKS, TEACHING_GROUP


READING_KEYS = {str(lesson["key"]) for lesson in LESSONS}


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


def test_public_domain_reading_set_is_bounded_attributed_and_ordered():
    assert len(LESSONS) == 3
    assert len(LANGUAGE_QOL_LESSONS) == 61
    assert [lesson["lesson_order"] for lesson in LESSONS] == [1, 2, 3]
    assert [source["form"] for source in SOURCE_WORKS] == ["poetry", "drama", "prose"]
    assert all(lesson["teaching_group"] == TEACHING_GROUP for lesson in LESSONS)
    assert all(lesson["group_order"] == 11 for lesson in LESSONS)
    assert all(lesson["teaching_source_type"] == "attributed_public_domain_reading_application_lesson" for lesson in LESSONS)
    assert set(EVIDENCE) == READING_KEYS
    for lesson, source in zip(LESSONS, SOURCE_WORKS, strict=True):
        assert source["public_domain_status"] == "public_domain_in_the_USA"
        assert source["source_url"].startswith("https://www.gutenberg.org/")
        assert 0 < len(source["bounded_excerpt"].split()) <= 16
        assert any(ref.startswith("attribution:") for ref in lesson["source_refs"])
        assert any(ref.startswith("license_status:public_domain") for ref in lesson["source_refs"])
        assert "reading_boundary:bounded_excerpt_and_project_authored_analysis_not_whole_work_import" in lesson["source_refs"]
        assert "recall_boundary:technique_transfer_not_quotation_recall" in lesson["source_refs"]
        assert "style_boundary:no_author_persona_or_signature_style_imitation" in lesson["source_refs"]


def test_public_domain_reading_set_has_revisable_understanding_and_original_transfer():
    for lesson in LESSONS:
        evidence = EVIDENCE[lesson["key"]]
        assert evidence["vocabulary"]
        assert evidence["uncertainties"]
        assert evidence["near_concept_distinctions"]
        assert evidence["examples"]
        assert evidence["counterexamples"]
        assert evidence["explanation"]
        assert evidence["distinct_examples"]
        assert evidence["questions"]
        assert evidence["comparisons"]
        assert evidence["correction_response"]
        joined = " ".join(evidence["distinct_examples"]).lower()
        assert "alice" not in joined
        assert "hermia" not in joined
        assert "lysander" not in joined
        assert "tiger" not in joined


def test_reading_group_completes_acquire_integrate_express_without_memory_or_authority(tmp_path):
    conn = _conn(tmp_path)
    memory_before = conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0]

    prepared = prepare_language_teaching_shelf(conn)
    status = language_teaching_status(conn)
    items = [item for item in list_language_teaching_items(conn)["items"] if item["group_order"] == 11]

    assert prepared["graduated_count"] == 61
    assert prepared["held_count"] == 0
    assert status["defined_group_count"] == 11
    assert status["teaching_groups"][-1]["teaching_group"] == TEACHING_GROUP
    assert status["teaching_groups"][-1]["available_lesson_count"] == 3
    assert len(items) == 3
    assert all(item["available_to_nlo"] is True for item in items)
    assert all(item["lifecycle"]["all_stages_complete"] is True for item in items)
    assert all(item["boundaries"]["answer_bearing_knowledge"] is False for item in items)
    assert all(item["boundaries"]["source_persona_imitation_allowed"] is False for item in items)
    assert all(item["source_refs"][0] == "speech_phase_12:public_domain_reading_and_creative_transfer" for item in items)
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == memory_before
    _assert_locked(prepared)


def test_reading_guidance_is_context_selected_and_not_an_ordinary_chat_default(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)

    poetry = select_language_guidance(
        conn,
        {
            "prompt": "Analyze The Tyger as a poem, separate observation from interpretation, and show a creative transfer.",
            "intent_decision": {"intent": "reasoned_answer", "response_depth": "developed"},
        },
    )
    ordinary = select_language_guidance(
        conn,
        {"prompt": "Good morning :) How are you?", "intent_decision": {"intent": "greeting"}},
    )

    assert "public_domain_poetry_mechanism_and_transfer" in poetry["lesson_keys"]
    assert not (READING_KEYS & set(ordinary["lesson_keys"]))
    assert poetry["automatic_content_generation"] is False
    _assert_locked(poetry)


def test_nlo_receives_reading_transfer_policy_without_source_recall_or_personality_authority(tmp_path):
    conn = _conn(tmp_path)
    prepare_language_teaching_shelf(conn)
    prompt = "Read this prose passage for viewpoint and escalation, then create an unrelated original transfer."
    seed = "The passage begins in a stable place, redirects attention twice, and ends with a deliberate choice to investigate."

    result = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "intent_decision": classify_chat_intent(prompt),
            "content_seed": seed,
        },
    )
    policy = result["meaning_packet"]["language_realization_policy"]

    assert policy["source_observation_interpretation"] is True
    assert policy["literary_mechanism_analysis"] is True
    assert policy["original_creative_transfer"] is True
    assert policy["content_generation_allowed"] is False
    assert policy["meaning_change_allowed"] is False
    assert policy["personality_change_allowed"] is False
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
