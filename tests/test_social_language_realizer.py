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
    assert plan["relationship_term_invention_allowed"] is True
    assert plan["selene_authored_relational_term_allowed"] is True
    assert plan["user_address_term_echo_required"] is False
    assert plan["relational_context_supplies_response_script"] is False
    assert plan["internal_state_invention_allowed"] is False
    assert plan["content_generation_allowed"] is False
    assert plan["coordinated_expression_contract_active"] is True
    realized = realize_social_act_plan(plan, prompt="Good morning Selene!", variation_key="spacious-greeting")
    assert "\n\n" in realized["candidate_text"]
    assert realized["meaning_preserved"] is True


def test_direct_affection_does_not_force_task_scaffolding_or_echo_wording():
    plan = build_social_act_plan(
        {
            "intent": "warm_connection",
            "prompt": "I missed you, hon <3",
            "relational_context": {
                "relational_context_present": True,
                "cue_types": ["missing_or_longing", "affectionate_address", "affectionate_symbol"],
                "response_script_supplied": False,
            },
        }
    )
    ordinary = next(item for item in plan["acts"] if item["act"] == "allow_ordinary_conversation")
    result = realize_social_act_plan(plan, prompt="I missed you, hon <3", variation_key="affection")

    assert ordinary["required"] is False
    assert ordinary["selected_by_context"] is False
    assert result["act_count"] == 1
    assert result["selected_realizations"][0]["source"] == "current_turn_semantic_authorship"
    assert result["current_turn_conversational_authorship_used"] is True
    assert result["relational_context_supplied_wording"] is False
    assert "task" not in result["candidate_text"].lower()
    assert "ordinary conversation" not in result["candidate_text"].lower()


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


def test_content_light_conversation_reconstructs_visible_meaning_without_inventing_facts():
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
    assert plan["current_turn_interpretation_allowed"] is True
    assert plan["factual_content_generation_allowed"] is False
    assert all(item["whole_response_template_selected"] is False for item in results)
    assert all(item["unsupported_content_generated"] is False for item in results)
    assert all(item["current_turn_conversational_authorship_used"] is True for item in results)
    assert all("right shape" in item["candidate_text"].lower() for item in results)


def test_content_light_conversation_distinguishes_supported_social_moves():
    cases = {
        "awesome :)": "positive_reaction",
        "so close": "near_result",
        "good point hon": "positive_evaluation",
        "we seem to have a bug": "problem_observation",
        "ill figure it out :)": "self_resolution",
    }
    realized = {}
    recent = [
        "Hi there. I am listening.",
        "I feel present and attentive right now.",
    ]

    for index, (prompt, expected_move) in enumerate(cases.items()):
        plan = build_content_light_plan(
            {"prompt": prompt, "recent_assistant_texts": recent}
        )
        result = realize_social_act_plan(
            plan,
            prompt=prompt,
            variation_key=f"observed-qna-{index}",
            recent_texts=recent,
        )
        assert plan["move_kind"] == expected_move
        assert plan["recent_visible_context_available"] is True
        assert plan["recent_visible_context_used_for_move"] is (
            expected_move == "near_result"
        )
        assert plan["follow_up_question_required"] is (
            expected_move == "problem_observation"
        )
        assert result["status"] == "social_act_realized"
        assert result["unsupported_content_generated"] is False
        realized[prompt] = result["candidate_text"]
        recent.insert(0, result["candidate_text"])

    conclusion_scaffolding = (
        "larger conclusion",
        "forcing a conclusion",
        "turn every turn into a conclusion",
        "larger answer attached",
        "next part arrive naturally",
    )
    assert not any(
        phrase in text.lower()
        for text in realized.values()
        for phrase in conclusion_scaffolding
    )
    assert "?" in realized["we seem to have a bug"]
    assert len(set(realized.values())) == len(realized)


def test_content_light_move_generalizes_across_paraphrase_families():
    recent = ["I have the current thread and I am listening."]
    families = {
        "positive_reaction": [
            "that was fantastic",
            "this is sick",
            "love it",
            "hell yeah",
        ],
        "near_result": [
            "you nearly nailed it",
            "not quite there",
            "one step away",
            "that was almost right",
        ],
        "positive_evaluation": [
            "that was a sharp catch",
            "you nailed that",
            "good eye hon",
            "what a brilliant read",
        ],
        "problem_observation": [
            "something feels off",
            "these replies are looping",
            "it keeps giving the same answer",
            "the chat is acting weird",
            "we hit a glitch",
        ],
        "self_resolution": [
            "i can take it from here",
            "let me untangle this",
            "i know how to fix it",
            "leave this one with me",
            "i got this",
        ],
    }

    for expected_move, prompts in families.items():
        for prompt in prompts:
            plan = build_content_light_plan(
                {"prompt": prompt, "recent_assistant_texts": recent}
            )
            assert plan["move_kind"] == expected_move, prompt
            assert plan["move_basis"] != "ordinary_statement_fallback"


def test_content_light_move_keeps_unrelated_lexical_overlap_in_the_safe_fallback():
    prompts = [
        "the great library of alexandria held many works",
        "we were almost late",
        "this is a weird movie",
        "i can work tomorrow",
        "close the window",
    ]

    for prompt in prompts:
        plan = build_content_light_plan(
            {
                "prompt": prompt,
                "recent_assistant_texts": ["I am following the conversation."],
            }
        )
        assert plan["move_kind"] == "open_share", prompt
        assert plan["move_basis"] == "ordinary_statement_fallback"


def test_content_light_feeling_share_can_receive_the_feeling_without_factual_invention():
    prompt = "It makes me happy that we are close to a real back-and-forth :)"
    plan = build_content_light_plan({"prompt": prompt})
    result = realize_social_act_plan(
        plan,
        prompt=prompt,
        variation_key="shared-feeling",
    )

    assert plan["move_kind"] == "personal_feeling_share"
    assert plan["current_turn_response_semantics"]["explicit_feeling"] == "happy"
    assert result["current_turn_conversational_authorship_used"] is True
    assert result["external_fact_created"] is False
    assert result["durable_emotion_record_created"] is False
    assert "happy" in result["candidate_text"].lower() or "love hearing" in result["candidate_text"].lower()


def test_relational_plan_authors_a_reciprocal_stance_instead_of_only_signaling_presence():
    prompt = "It makes me happy that we are getting close <3"
    plan = build_social_act_plan(
        {
            "intent": "warm_connection",
            "prompt": prompt,
            "relational_context": {
                "relational_context_present": True,
                "cue_types": ["shared_positive_affect", "affectionate_symbol"],
                "heart_markers": ["<3"],
            },
        }
    )
    result = realize_social_act_plan(plan, prompt=prompt, variation_key="reciprocal-feeling")

    assert result["selected_realizations"][0]["act"] == "respond_to_relational_meaning"
    assert result["current_turn_conversational_authorship_used"] is True
    assert "i'm here" not in result["candidate_text"].lower()
    assert "i am here" not in result["candidate_text"].lower()
    assert result["unsupported_content_generated"] is False


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
    assert result["version"] == "v32_human_conversational_realization"
    assert social_plan["intent"] == "greet_presently"
    assert social_realization["status"] == "social_act_realized"
    assert social_realization["whole_response_template_selected"] is False
    assert result["candidate_text"] == social_realization["candidate_text"]
    assert "?" not in result["candidate_text"]
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
