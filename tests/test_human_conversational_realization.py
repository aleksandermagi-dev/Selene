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


def test_supported_answer_uses_contextual_entry_and_cadence_without_changing_clauses():
    source = (
        "The pilot should begin with the smaller reversible step. "
        "That step produces evidence before the larger commitment. "
        "A known prerequisite would change the order."
    )
    plan = build_human_conversational_plan(
        {
            "epistemic_composition": {
                "dominant_state": "supported_answer",
                "parts": [],
            },
            "epistemic_answer_state": {"epistemic_state": "supported_answer"},
            "contextual_composition_plan": {
                "expression_profile": "procedure",
                "response_depth": "standard",
                "sentence_rhythm": "natural",
            },
            "supported_surface_available": True,
        }
    )

    results = [
        realize_human_conversation(
            source,
            plan,
            variation_key=f"supported-{index}",
        )
        for index in range(16)
    ]

    surfaces = {item["candidate_text"] for item in results}
    assert len(surfaces) >= 4
    assert all(item["release_safe"] is True for item in results)
    assert all(item["meaning_preserved"] is True for item in results)
    assert all("The pilot should begin" in item["candidate_text"] for item in results)
    assert all("That step produces evidence" in item["candidate_text"] for item in results)
    assert all("A known prerequisite" in item["candidate_text"] for item in results)
    assert any("\n\n" in item for item in surfaces)


def test_supported_answer_replaces_a_neutral_stock_entry_without_losing_content():
    source = "The direct answer is this: The supported result remains provisional."
    plan = {
        "eligible": True,
        "profile": "supported_answer",
        "expression_profile": "direct",
        "response_depth": "standard",
        "sentence_rhythm": "natural",
        "contractions_allowed": True,
        "supported_surface_available": True,
    }

    results = [
        realize_human_conversation(source, plan, variation_key=f"entry-{index}")
        for index in range(12)
    ]

    assert all("The supported result remains provisional." in item["candidate_text"] for item in results)
    assert all(item["release_safe"] is True for item in results)
    assert any(item["candidate_text"] == "The supported result remains provisional." for item in results)
    assert any("replace_neutral_stock_entry" in item["operations"] for item in results)


def test_supported_answer_can_use_context_shaped_warmth_without_forcing_it():
    source = "The local pilot is reversible. It also gives us evidence before expansion."
    plan = build_human_conversational_plan(
        {
            "epistemic_composition": {"dominant_state": "supported_answer", "parts": []},
            "epistemic_answer_state": {"epistemic_state": "supported_answer"},
            "contextual_composition_plan": {
                "expression_profile": "procedure",
                "response_depth": "standard",
            },
            "affect_expression_guidance": {
                "expression_posture": "warm_focused",
                "current_turn_cues": ["shared_progress"],
                "dimensions": {
                    "warmth": "available_not_forced",
                    "enthusiasm": "quietly_available",
                },
            },
            "supported_surface_available": True,
        }
    )

    results = [
        realize_human_conversation(source, plan, variation_key=f"warm-focus-{index}")
        for index in range(32)
    ]
    surfaces = {item["candidate_text"] for item in results}

    assert plan["affect_expression_posture"] == "warm_focused"
    assert all("The local pilot is reversible." in item for item in surfaces)
    assert all("It also gives us evidence before expansion." in item for item in surfaces)
    assert source in surfaces
    assert any(
        item.startswith(("Absolutely—", "Yeah—"))
        for item in surfaces
    )
    assert all(item["release_safe"] is True for item in results)
