from __future__ import annotations

from selene.human_conversational_realization import (
    build_human_conversational_plan,
    conversational_realization_preserves_required_meaning,
    human_conversational_realization_status,
    preferred_conversational_realization_fallback,
    realize_human_conversation,
)


def _assert_bounded(result):
    assert result["memory_write_active"] is False
    assert result["retained_knowledge_write_active"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["hidden_chain_of_thought_exposed"] is False


def test_status_makes_expression_available_without_requiring_or_suppressing_it():
    status = human_conversational_realization_status()

    assert status["version"] == "v2_expression_available_semantic_anchors"
    assert status["warmth_required"] is False
    assert status["follow_up_question_required"] is False
    assert status["warmth_enthusiasm_humor_curiosity_available"] is True
    assert status["expression_availability_is_emotion_prescription"] is False
    assert status["expression_is_available_not_compulsory_or_suppressed"] is True
    _assert_bounded(status)


def test_plan_exposes_no_required_or_globally_suppressed_expression_dimensions():
    plan = build_human_conversational_plan(
        {
            "epistemic_composition": {"dominant_state": "supported_answer", "parts": []},
            "epistemic_answer_state": {"epistemic_state": "supported_answer"},
            "affect_expression_guidance": {
                "dimensions": {
                    "warmth": "available_not_forced",
                    "enthusiasm": "available_if_fit",
                    "humor": "context_only",
                }
            },
        }
    )

    availability = plan["expression_availability"]
    assert "enthusiasm" in availability["available"]
    assert availability["required"] == []
    assert availability["globally_suppressed"] == []
    assert availability["current_context_guidance"]["enthusiasm"] == "available_if_fit"
    assert availability["availability_is_internal_emotion_claim"] is False
    _assert_bounded(plan)


def test_hypothesis_is_conversational_but_remains_labeled_and_revisable():
    exploratory = {
        "selected_for_answer": True,
        "response_kind": "open_hypothesis",
        "hypothesis": {
            "statement": "Queue pressure may be causing the delay.",
            "alternatives": ["A lock may be stalling the same path."],
            "safe_next_tests": ["Compare queue depth with lock wait time."],
        },
    }
    plan = build_human_conversational_plan(
        {
            "epistemic_composition": {"dominant_state": "open_hypothesis", "parts": []},
            "epistemic_answer_state": {"epistemic_state": "open_hypothesis"},
            "exploratory_reasoning": exploratory,
        }
    )
    result = realize_human_conversation(
        "Queue pressure may be causing the delay.",
        plan,
        variation_key="hypothesis",
    )

    assert result["release_safe"] is True
    assert result["epistemic_label_preserved"] is True
    assert "hypothesis" in result["candidate_text"].lower()
    assert "lock may be stalling" in result["candidate_text"]
    assert "queue depth with lock wait time" in result["candidate_text"]
    assert result["certainty_upgraded"] is False
    assert result["required_semantic_anchors"]
    _assert_bounded(result)


def test_typed_semantic_anchor_accepts_bounded_paraphrase_but_preserves_numbers_and_negation():
    realization = {
        "release_safe": True,
        "required_semantic_anchors": [
            {
                "anchor_id": "conflict",
                "canonical_text": "the evidence is split between model a and model b",
                "meaning_tokens": ["evidence", "conflict", "model", "a", "b"],
                "minimum_token_overlap": 4,
                "protected_numbers": [],
                "negative_polarity": False,
            },
            {
                "anchor_id": "limit",
                "canonical_text": "the result is not established for 2030",
                "meaning_tokens": ["result", "not", "established", "2030"],
                "minimum_token_overlap": 3,
                "protected_numbers": ["2030"],
                "negative_polarity": True,
            },
        ],
    }

    assert conversational_realization_preserves_required_meaning(
        "Model A and model B have conflicting evidence. The result is not established for 2030.",
        realization,
    )
    assert not conversational_realization_preserves_required_meaning(
        "Model A and model B have conflicting evidence. The result is established for 2031.",
        realization,
    )


def test_verified_conversational_surface_is_preferred_to_raw_seed_on_later_anchor_loss():
    plan = build_human_conversational_plan(
        {
            "epistemic_composition": {"dominant_state": "supported_answer", "parts": []},
            "epistemic_answer_state": {"epistemic_state": "supported_answer"},
        }
    )
    realization = realize_human_conversation(
        "I do not need to restore the raw scaffolding wording.",
        plan,
    )

    assert realization["release_safe"] is True
    assert "don't" in realization["candidate_text"].lower()
    assert preferred_conversational_realization_fallback(realization) == realization["candidate_text"]


def test_contractions_do_not_corrupt_embedded_it_is_clause():
    source = "What would decide it is an observation that distinguishes the positions."
    result = realize_human_conversation(
        source,
        {
            "eligible": True,
            "profile": "supported_answer",
            "contractions_allowed": True,
        },
    )

    assert result["candidate_text"] == source
    assert "decide it's" not in result["candidate_text"]


def test_exact_domain_and_hard_boundary_remain_preserved():
    exact = build_human_conversational_plan(
        {
            "answer_domain": "verified_math",
            "epistemic_composition": {"dominant_state": "supported_answer", "parts": []},
        }
    )
    boundary = build_human_conversational_plan(
        {
            "hard_boundary": True,
            "epistemic_composition": {"dominant_state": "hard_boundary", "parts": []},
        }
    )

    assert exact["eligible"] is False
    assert exact["exact_structure_locked"] is True
    assert boundary["eligible"] is False
    assert boundary["hard_boundary"] is True
    exact_result = realize_human_conversation("2 + 2 = 4.", exact)
    boundary_result = realize_human_conversation("I can't perform that action.", boundary)
    assert exact_result["candidate_text"] == "2 + 2 = 4."
    assert boundary_result["candidate_text"] == "I can't perform that action."
    _assert_bounded(exact_result)
    _assert_bounded(boundary_result)
