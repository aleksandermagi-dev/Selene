from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.native_language_organ import realize_native_language
from selene.social_language_realizer import (
    build_content_light_plan,
    build_social_act_plan,
    realize_acknowledgement,
    realize_social_act_plan,
)


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_social_plan_exposes_semantic_acts_without_claiming_voice_or_internal_state():
    plan = build_social_act_plan(
        {
            "intent": "greet_presently",
            "prompt": "Good morning Selene!",
            "turn_count": 3,
            "affect_expression_guidance": {
                "dimensions": {"warmth": "available_not_forced", "sentence_rhythm": "spacious"}
            },
        }
    )

    assert plan["status"] == "social_act_plan_ready"
    assert [item["act"] for item in plan["acts"]] == ["return_greeting", "signal_presence"]
    assert plan["affect_guidance_may_change_meaning"] is False
    assert plan["relationship_term_invention_allowed"] is False
    assert plan["internal_state_invention_allowed"] is False
    assert plan["content_generation_allowed"] is False
    assert plan["voice_owns_expression_style"] is True
    realized = realize_social_act_plan(plan, prompt="Good morning Selene!", variation_key="spacious-greeting")
    assert "\n\n" in realized["candidate_text"]
    assert realized["meaning_preserved"] is True


def test_social_realizer_composes_contextual_clauses_instead_of_selecting_whole_responses():
    plan = build_social_act_plan({"intent": "greet_presently", "prompt": "Greetings!", "turn_count": 4})
    results = [
        realize_social_act_plan(plan, prompt="Greetings!", variation_key=f"greeting-turn-{index}")
        for index in range(18)
    ]
    outputs = {result["candidate_text"] for result in results}

    assert len(outputs) >= 6
    assert all(result["act_count"] == 2 for result in results)
    assert all(result["whole_response_template_selected"] is False for result in results)
    assert all(result["unsupported_content_generated"] is False for result in results)
    assert all(result["relationship_term_invented"] is False for result in results)


def test_social_realizer_uses_recent_wording_to_avoid_repeating_act_fragments():
    plan = build_social_act_plan({"intent": "receive_gratitude", "prompt": "Thank you for the work.", "turn_count": 8})
    first = realize_social_act_plan(plan, prompt="Thank you for the work.", variation_key="first")
    second = realize_social_act_plan(
        plan,
        prompt="Thank you for the work.",
        variation_key="second",
        recent_texts=[first["candidate_text"]],
    )
    first_fragments = {item["text"] for item in first["selected_realizations"]}
    second_fragments = {item["text"] for item in second["selected_realizations"]}

    assert first["candidate_text"] != second["candidate_text"]
    assert first_fragments.isdisjoint(second_fragments)
    assert second["recent_wording_consulted"] is True


def test_correction_realization_preserves_supplied_changed_meaning_and_valid_context():
    plan = build_social_act_plan(
        {
            "intent": "receive_correction",
            "prompt": "Small correction: use the semantic layer first.",
            "corrected_meaning": "the semantic layer should come first",
            "turn_count": 6,
        }
    )
    result = realize_social_act_plan(plan, prompt="Small correction", variation_key="correction")

    assert [item["act"] for item in plan["acts"]] == [
        "acknowledge_correction",
        "state_corrected_meaning",
        "preserve_valid_context",
    ]
    assert "semantic layer should come first" in result["candidate_text"]
    assert "changed point is that" not in result["candidate_text"].lower()
    assert any(item["source"] == "supplied_corrected_meaning" for item in result["selected_realizations"])
    assert result["meaning_preserved"] is True


def test_repair_acknowledgements_use_the_compositional_social_layer():
    results = [
        realize_acknowledgement("partial_agreement", variation_key=f"turn-{index}")
        for index in range(12)
    ]

    assert len({item["candidate_text"] for item in results}) >= 3
    assert all(item["repair_acknowledgement_kind"] == "partial_agreement" for item in results)
    assert all(item["whole_response_template_selected"] is False for item in results)
    assert all(item["answer_content_generated"] is False for item in results)


def test_content_light_conversation_is_composed_without_paraphrasing_or_inventing_content():
    plan = build_content_light_plan({"prompt": "I think this finally has the right shape."})
    results = [
        realize_social_act_plan(
            plan,
            prompt="I think this finally has the right shape.",
            variation_key=f"content-light-{index}",
        )
        for index in range(18)
    ]

    assert len({item["candidate_text"] for item in results}) >= 6
    assert plan["content_generation_allowed"] is False
    assert plan["prompt_paraphrase_allowed"] is False
    assert all(item["whole_response_template_selected"] is False for item in results)
    assert all(item["unsupported_content_generated"] is False for item in results)


def test_nlo_routes_social_intent_through_compositional_act_realization(tmp_path):
    conn = _conn(tmp_path)
    prompt = "Greetings hon!"
    result = realize_native_language(
        conn,
        {
            "prompt": prompt,
            "intent_decision": classify_chat_intent(prompt),
            "conversation_context": {"turn_count": 5, "recent_assistant_texts": []},
        },
    )

    social_plan = result["discourse_plan"]["social_act_plan"]
    social_realization = result["discourse_plan"]["social_act_realization"]
    assert result["version"] == "v20_conversation_maturity_composition"
    assert social_plan["intent"] == "greet_presently"
    assert social_realization["status"] == "social_act_realized"
    assert social_realization["whole_response_template_selected"] is False
    assert result["candidate_text"] == social_realization["candidate_text"]
    assert "?" not in result["candidate_text"]
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
