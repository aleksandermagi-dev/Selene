from __future__ import annotations

from selene.current_context_inference import build_current_context_inference


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def test_pragmatic_evaluation_uses_the_visible_comparative_premise():
    result = build_current_context_inference("How does a quieter workspace sound?")

    assert result["eligible"] is True
    assert result["request_kind"] == "evaluation"
    assert result["answer_kind"] == "grounded_current_context_inference"
    assert result["answer"].startswith("It sounds like a useful improvement")
    assert "less competing noise" in result["answer"].lower()
    assert result["inference_claim"]["basis_claim_ids"] == ["current-context-prompt"]
    assert result["inference_is_source_statement"] is False
    _assert_locked(result)


def test_practical_consequence_combines_only_visible_session_premises():
    result = build_current_context_inference(
        "What is one practical benefit of that?",
        [
            {
                "observation": "The important records are safe, and the workspace is less cluttered.",
                "source_role": "user",
                "premise_eligible": True,
            }
        ],
    )

    assert result["eligible"] is True
    assert result["request_kind"] == "practical_consequence"
    assert "easier to find and work with" in result["answer"].lower()
    assert "without sacrificing access" in result["answer"].lower()
    assert result["support_basis"] == "current_prompt_and_recent_conversation"
    assert result["external_fact_claimed"] is False
    _assert_locked(result)


def test_unverified_assistant_gap_text_cannot_become_a_premise():
    result = build_current_context_inference(
        "What practical benefit does that provide?",
        [
            {
                "observation": "I do not have enough grounded detail. The missing piece is context.",
                "source_role": "selene",
                "premise_eligible": False,
            }
        ],
    )

    assert result["eligible"] is False
    assert result["premise_claims"] == [
        {
            "claim_id": "current-context-prompt",
            "claim_type": "current_turn_statement",
            "text": "What practical benefit does that provide?",
            "source_role": "user",
            "source_category": "current_prompt",
            "reported_not_independently_verified": True,
        }
    ]
    _assert_locked(result)


def test_literal_domain_and_external_fact_questions_remain_with_their_owners():
    literal = build_current_context_inference("How does a bell produce sound?")
    external = build_current_context_inference("What is the current price of gold?")

    assert literal["eligible"] is False
    assert literal["reason"] == "literal_domain_question_requires_domain_support"
    assert external["eligible"] is False
    assert external["reason"] == "external_fact_request_requires_attributed_support"
    _assert_locked(literal)
    _assert_locked(external)
