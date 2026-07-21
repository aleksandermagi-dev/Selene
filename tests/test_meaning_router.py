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


def test_ordinary_self_check_in_outranks_generic_how_reasoning():
    check_in = interpret_turn_meaning("How are you?")
    procedural = interpret_turn_meaning("How are you calculating that result?")

    assert check_in["primary_intent"] == "self_state"
    assert "self_state_question" in check_in["dialogue_acts"]
    assert procedural["primary_intent"] == "reasoning"


def test_colloquial_and_embedded_check_ins_route_to_self_state():
    prompts = (
        "whats up?",
        "What's up?",
        "I'm glad I did too, how are you?",
    )

    for prompt in prompts:
        result = interpret_turn_meaning(prompt)
        assert result["primary_intent"] == "self_state"
        assert "self_state_question" in result["dialogue_acts"]

    procedural = interpret_turn_meaning("How are you calculating that result?")
    assert procedural["primary_intent"] == "reasoning"


def test_natural_quoted_correction_and_mixed_check_in_summary_keep_distinct_acts():
    correction = interpret_turn_meaning(
        'When I say "what\'s up," I mean "how are you." Does that distinction make sense?'
    )
    mixed = classify_chat_intent(
        "In two short parts, how are you doing, and what has this conversation been about?"
    )

    assert correction["primary_intent"] == "correction"
    assert correction["dialogue_acts"] == ["correction", "question"]
    assert mixed["intent"] == "self_state"
    assert mixed["self_state_requested"] is True
    assert mixed["memory_recall_requested"] is True
    assert mixed["mixed_intent"] is True


def test_greeting_and_demo_context_do_not_displace_an_explicit_self_state_question():
    result = interpret_turn_meaning(
        "Good morning, Selene. Aleks and I are preparing a short demo today, "
        "and we wanted to have a real conversation with you first. "
        "How are you feeling about talking with us for a few minutes?"
    )

    assert result["primary_intent"] == "self_state"
    assert "self_state_question" in result["dialogue_acts"]
    assert "greeting" in result["dialogue_acts"]


def test_ordinary_speech_and_technical_lookalikes_route_by_meaning():
    contrast_pairs = (
        ("How are you?", "self_state", "How are you calculating that result?", "reasoning"),
        ("Can you remember where we left off?", "memory_recall", "How should memory handle fuzzy recall?", "reasoning"),
        ("Let's stop here for today.", "farewell", "How do I stop the local service without losing state?", "reasoning"),
        ("I feel like this is working.", "direct_conversation", "How does affect expression work?", "reasoning"),
        ("Are you okay?", "self_state", "Are you okay with using SQLite for this?", "direct_conversation"),
        ("Do you remember what I said yesterday?", "memory_recall", "Do you remember how binary search works?", "reasoning"),
        ("That's enough for now.", "farewell", "Should the service pause before writing?", "reasoning"),
        ("Thank you; we can leave it there for now.", "farewell", "Should we leave the value there?", "reasoning"),
        ("Talk to you later.", "farewell", "Can the phone bridge talk to you later?", "direct_conversation"),
        ("Remember this: close file handles after use.", "memory_candidate", "Remember to close the file handle.", "direct_conversation"),
    )

    for ordinary, ordinary_intent, technical, technical_intent in contrast_pairs:
        assert interpret_turn_meaning(ordinary)["primary_intent"] == ordinary_intent
        assert interpret_turn_meaning(technical)["primary_intent"] == technical_intent


def test_partial_agreement_preserves_the_qualification_as_a_secondary_dialogue_act():
    result = interpret_turn_meaning("Okay, but what changes if voice comes first?")

    assert result["primary_intent"] == "reasoning"
    assert "partial_agreement" in result["dialogue_acts"]
    assert "question" in result["dialogue_acts"]


def test_definition_question_reaches_knowledge_reasoning_without_consuming_personal_questions():
    definition = interpret_turn_meaning("What is photosynthesis?")
    personal = interpret_turn_meaning("What is your current state?")

    assert definition["primary_intent"] == "reasoning"
    assert personal["primary_intent"] != "reasoning"


def test_ordinary_resource_division_is_not_mistaken_for_arithmetic():
    ordinary = interpret_turn_meaning(
        "How should a garden divide limited water between vegetables and pollinators?"
    )
    arithmetic = interpret_turn_meaning("Divide 18 by 3.")

    assert ordinary["selected_domain"] == "ordinary_conversation"
    assert arithmetic["selected_domain"] == "verified_math"


def test_social_opening_cannot_displace_a_later_multi_part_direct_request():
    prompt = (
        "Good afternoon, Selene. Let's think through a practical idea together. "
        "A neighborhood learning festival has limited rooms and volunteers, but it wants to offer both "
        "hands-on science activities and quiet reading discussions for children and adults. "
        "Walk me through two workable designs, compare their tradeoffs, and recommend one small pilot we could try first."
    )
    result = interpret_turn_meaning(prompt)

    assert result["primary_intent"] == "reasoning"
    assert result["sentence_shape"]["explicit_request"] is True
    assert result["sentence_shape"]["mixed_intent_possible"] is True
    assert "greeting" in result["dialogue_acts"]
    assert "request" in result["dialogue_acts"]
    assert result["selected_domain"] == "comparison_planning"
