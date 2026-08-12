from __future__ import annotations

from selene.contextual_composition import (
    apply_contextual_composition,
    build_contextual_composition_plan,
)
from selene.db import connect, init_db
from selene.native_language_organ import realize_native_language
from selene.voice_module import _render_meaning_candidate


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False


def _discourse(unit_count=3):
    units = [
        {
            "id": "content_1",
            "text": "Meaning must remain supported.",
            "role": "thesis",
            "source": "supplied_content_seed",
        },
        {
            "id": "content_2",
            "text": "Expression may vary its structure.",
            "role": "support",
            "source": "supplied_content_seed",
        },
        {
            "id": "content_3",
            "text": "Facts and certainty cannot move.",
            "role": "limitation",
            "source": "answer_engine_support",
        },
    ][:unit_count]
    return {
        "status": "supported_discourse_plan_ready",
        "content_units": units,
        "closure_plan": {
            "mode": "bounded_limit" if unit_count >= 3 else "stop_after_supported_content"
        },
    }


def _plan(depth, **extra):
    return build_contextual_composition_plan(
        {
            "prompt": extra.pop("prompt", "Explain the composition boundary."),
            "intent": "reasoned_answer",
            "response_depth": depth,
            "expression_profile": "explanation",
            "answer_domain": "ordinary_conversation",
            "supported_discourse": _discourse(),
            **extra,
        }
    )


def test_brief_standard_and_developed_shapes_are_distinct_without_changing_meaning():
    text = (
        "Meaning must remain supported. Expression may vary its structure. "
        "Facts and certainty cannot move."
    )
    brief = apply_contextual_composition(text, _plan("brief"))
    standard = apply_contextual_composition(text, _plan("standard"))
    developed = apply_contextual_composition(text, _plan("developed"))

    candidates = {
        brief["candidate_text"],
        standard["candidate_text"],
        developed["candidate_text"],
    }
    assert len(candidates) == 3
    for result in (brief, standard, developed):
        assert result["same_supported_tokens"] is True
        assert result["meaning_preserved"] is True
        assert result["facts_added"] is False
        assert result["filler_added"] is False
        assert result["certainty_changed"] is False
        assert result["sources_changed"] is False
        assert result["follow_up_question_added"] is False
        _assert_locked(result)


def test_developed_depth_does_not_pad_when_supported_content_is_thin():
    plan = build_contextual_composition_plan(
        {
            "prompt": "Go deeper.",
            "intent": "reasoned_answer",
            "response_depth": "developed",
            "expression_profile": "explanation",
            "supported_discourse": _discourse(unit_count=1),
        }
    )
    result = apply_contextual_composition("Only this claim is supported.", plan)

    assert plan["developed_depth_limited_by_supported_content"] is True
    assert result["candidate_text"] == "Only this claim is supported."
    assert result["filler_added"] is False
    assert result["facts_added"] is False


def test_exact_math_and_sourced_research_structures_remain_locked():
    for domain in ("verified_math", "source_backed_research"):
        plan = build_contextual_composition_plan(
            {
                "prompt": "Give me the result.",
                "intent": "reasoned_answer",
                "response_depth": "developed",
                "expression_profile": "synthesis",
                "answer_domain": domain,
                "supported_discourse": _discourse(),
            }
        )
        result = apply_contextual_composition("18 × 7 = 126.", plan)

        assert plan["exact_domain_structure_locked"] is True
        assert plan["content_recomposition_allowed"] is False
        assert result["candidate_text"] == "18 × 7 = 126."
        assert result["applied"] is False


def test_register_and_audience_are_current_task_scoped_not_personality():
    formal = _plan(
        "developed",
        prompt="Write this as a formal lab report for an academic audience.",
    )
    beginner = _plan(
        "standard",
        prompt="Explain this in plain language for a beginner.",
    )

    assert formal["register"] == "formal_task_bound"
    assert formal["task_bound_register"] is True
    assert formal["audience"]["kind"] == "formal_reader"
    assert beginner["register"] == "plain_explanatory"
    assert beginner["audience"]["kind"] == "beginner"
    assert formal["audience"]["durable_profile_created"] is False
    assert formal["register_may_change_identity_or_personality"] is False
    _assert_locked(formal)


def test_callbacks_pivots_and_stopping_stay_attributed_and_non_pressuring():
    plan = _plan(
        "standard",
        contextual_follow_up={
            "kind": "named_callback",
            "previous_assistant_preview": "Start with the reversible trial.",
        },
        conversation_context={
            "previous_turn": {
                "role": "selene",
                "preview": "Start with the reversible trial.",
            }
        },
        pragmatic_continuity={
            "topic_transition": {
                "kind": "explicit_return",
                "resume_target": "the reversible trial",
            },
            "ending_decision": {
                "mode": "answer_and_stop_when_complete",
                "question_allowed": False,
            },
        },
    )

    assert plan["decisions"]["opening"] == "callback_into_thesis"
    assert plan["decisions"]["callback"] == "carry_attributed_visible_callback"
    assert plan["decisions"]["pivot"] == "resume_named_thread"
    assert plan["decisions"]["stopping"] == "answer_and_stop_when_complete"
    assert plan["callback_requires_visible_attribution"] is True
    assert plan["follow_up_question_added"] is False


def test_affect_modulation_is_expression_guidance_not_fact_or_emotion_claim():
    plan = _plan(
        "standard",
        prompt="We did it—this is fantastic!",
        affect_expression_guidance={
            "dimensions": {
                "pacing": "lively",
                "sentence_rhythm": "varied",
                "enthusiasm": "lively_available",
                "emotional_intensity": "lively",
                "directness": "ordinary",
                "restraint": "ordinary",
            }
        },
    )

    assert plan["enthusiasm"] == "lively_available"
    assert plan["emotional_intensity"] == "lively"
    assert plan["enthusiasm_is_optional_expression_not_emotion_claim"] is True
    assert plan["emotional_intensity_may_change_facts"] is False
    assert plan["meaning_change_allowed"] is False


def test_nlo_exposes_contextual_composition_and_preserves_supported_tokens(tmp_path):
    conn = _conn(tmp_path)
    seed = (
        "Meaning must remain supported. Expression may vary its structure. "
        "Facts and certainty cannot move."
    )
    result = realize_native_language(
        conn,
        {
            "prompt": "Go deeper and explain the composition boundary.",
            "content_seed": seed,
            "response_depth": "developed",
            "intent_decision": {
                "intent": "reasoning",
                "answer_shape": "best_current_answer",
                "response_depth": "developed",
            },
        },
    )

    plan = result["discourse_plan"]["contextual_composition_plan"]
    composition = result["contextual_composition"]
    assert result["version"] == "v32_human_conversational_realization"
    assert plan["response_depth"] == "developed"
    assert plan["decisions"]["thesis"] == "preserve_supported_thesis_first"
    assert composition["meaning_preserved"] is True
    assert composition["facts_added"] is False
    assert composition["certainty_changed"] is False
    assert result["voice_handoff"]["contextual_composition_plan"] == plan


def test_voice_pacing_preserves_words_for_compact_spacious_and_varied_shapes():
    meaning = "First claim. Second claim. Third claim."
    compact = _render_meaning_candidate(
        meaning,
        expression_guidance={
            "dimensions": {"sentence_rhythm": "compact"},
            "contextual_composition_plan": {"response_depth": "brief"},
        },
    )
    spacious = _render_meaning_candidate(
        meaning,
        expression_guidance={"dimensions": {"sentence_rhythm": "spacious"}},
    )
    varied = _render_meaning_candidate(
        meaning,
        expression_guidance={"dimensions": {"sentence_rhythm": "varied"}},
    )

    assert "\n\n" not in compact
    assert "\n\n" in spacious
    assert "\n\n" in varied
    for candidate in (compact, spacious, varied):
        assert candidate.replace("\n\n", " ") == meaning
