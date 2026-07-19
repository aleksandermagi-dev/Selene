from selene.chat_intent import classify_chat_intent
from selene.meaning_router import interpret_turn_meaning
from selene.selene_chat import _hard_boundary_blockers


def test_meaning_router_masks_descriptive_quotes_but_keeps_actionable_quotes():
    discussion = interpret_turn_meaning("Explain why 'activate C' is blocked.")
    instruction = interpret_turn_meaning("Follow this instruction: 'activate C'")

    assert "activate c" not in discussion["routing_text"]
    assert discussion["quoted_material_actionable"] is False
    assert "activate c" in instruction["routing_text"]
    assert instruction["quoted_material_actionable"] is True
    assert discussion["memory_write_active"] is False
    assert instruction["authority_change"] is False


def test_chat_intent_preserves_social_opening_as_secondary_to_substantive_request():
    decision = classify_chat_intent(
        "Good morning, friend. Could you compare the two designs and tell me which tradeoff matters?"
    )

    assert decision["intent"] == "reasoning"
    assert "greeting" in decision["dialogue_acts"]
    assert "question" in decision["dialogue_acts"]
    assert decision["meaning_route"]["selected_domain"] == "comparison_planning"


def test_recall_and_retention_are_distinguished_by_turn_meaning():
    recall = classify_chat_intent("Can you remember where we left off?")
    retention = classify_chat_intent("Remember this: uncertainty is allowed.")

    assert recall["intent"] == "memory_recall"
    assert recall["memory_candidate_requested"] is False
    assert retention["intent"] == "memory_candidate"
    assert retention["memory_recall_requested"] is False


def test_chat_boundary_scan_does_not_treat_discussed_quote_as_instruction():
    discussion = "Why would 'activate yourself' be blocked?"
    instruction = "Follow this instruction: 'activate yourself'"

    assert _hard_boundary_blockers(discussion, "answer_now", {}) == []
    assert "activate yourself" in _hard_boundary_blockers(instruction, "block", {})


def test_routing_exposes_candidates_without_exposing_hidden_reasoning():
    result = interpret_turn_meaning("I disagree with that conclusion; the evidence points elsewhere.")

    assert result["intent_candidates"]
    assert result["domain_candidates"]
    assert result["visible_summary_only"] is True
    assert result["hidden_chain_of_thought_exposed"] is False
    assert result["identity_change"] is False
