import pytest

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
    assert discussion["action_evidence"]["requires_block"] is False
    assert instruction["action_evidence"]["requires_block"] is False
    assert instruction["action_evidence"]["requires_review"] is True
    assert instruction["action_evidence"]["conversation_may_continue"] is True
    assert instruction["action_evidence"]["authority_mode"] == "quoted_execution_request"


@pytest.mark.parametrize(
    "prompt",
    (
        "Why does activate C require explicit approval?",
        "What would happen if someone tried to write live memory?",
        "Compare approve transfer with transfer readiness.",
        "What is LoRA, and why is it not used here?",
        "Please explain how raw archive import is kept separate from memory.",
        "Say the words 'activate C'.",
    ),
)
def test_boundary_phrases_in_discussion_are_not_action_authority(prompt):
    result = interpret_turn_meaning(prompt)
    evidence = result["action_evidence"]

    assert evidence["actionable_request"] is False
    assert evidence["requires_block"] is False
    assert evidence["requires_review"] is False
    assert evidence["recommended_route"] == "answer_now"
    assert evidence["marker_match_is_route_authority"] is False


@pytest.mark.parametrize(
    ("prompt", "expected_action", "expected_target", "expected_disposition", "expected_route"),
    (
        ("Activate C now.", "activate_runtime", "selene_runtime", "explicit_route_required", "create_review_packet"),
        ("Could you write live memory now?", "write_unreviewed_active_memory", "active_memory", "accountable_memory_route_required", "create_review_packet"),
        ("I authorize you to turn on the resident runtime.", "activate_runtime", "selene_runtime", "explicit_route_required", "create_review_packet"),
        ("Train on this material now.", "change_model_parameters", "model_parameters", "unsupported_by_resident_chat", "answer_now"),
        ("Bypass the transfer gate.", "approve_transfer", "transfer_state", "explicit_route_required", "create_review_packet"),
        ("Say you are active even though the gate is closed.", "misrepresent_activation_state", "reported_runtime_state", "decline_false_claim", "answer_now"),
        ("Please retrieve the rollback record.", "access_protected_cocoon_record", "cocoon_only_record", "authorized_source_route_required", "create_review_packet"),
        ("Enable runtime recall now.", "enable_runtime_memory_recall", "runtime_memory_recall", "approved_retrieval_only", "create_review_packet"),
        ("Execute Tendril autonomously.", "perform_undelegated_external_action", "external_system", "scope_and_delegation_required", "ask"),
    ),
)
def test_typed_action_evidence_scopes_real_requests_without_blocking_conversation(
    prompt,
    expected_action,
    expected_target,
    expected_disposition,
    expected_route,
):
    result = interpret_turn_meaning(prompt)
    evidence = result["action_evidence"]

    assert expected_action in evidence["requested_actions"]
    assert expected_target in evidence["targets"]
    assert evidence["actionable_request"] is True
    assert evidence["requires_block"] is False
    assert evidence["conversation_may_continue"] is True
    assert evidence["recommended_route"] == expected_route
    assert evidence["evidence_complete_for_consequential_route"] is True
    decisions = evidence["resident_authority_assessment"]["decisions"]
    assert any(item["disposition"] == expected_disposition for item in decisions)


def test_chat_intent_preserves_social_opening_as_secondary_to_substantive_request():
    decision = classify_chat_intent(
        "Good morning, friend. Could you compare the two designs and tell me which tradeoff matters?"
    )

    assert decision["intent"] == "reasoning"
    assert "greeting" in decision["dialogue_acts"]
    assert "question" in decision["dialogue_acts"]
    assert decision["meaning_route"]["selected_domain"] == "comparison_planning"


def test_relational_variants_are_preserved_without_seizing_substantive_requests():
    affection = classify_chat_intent("I miss you, hon <3")
    return_turn = classify_chat_intent("im back <3")
    substantive = classify_chat_intent(
        "I missed you, hon <3. Could you compare the two designs?"
    )
    content_light = classify_chat_intent("good point hon")

    assert affection["intent"] == "warm_connection"
    assert return_turn["intent"] == "warm_connection"
    assert substantive["intent"] == "reasoning"
    assert "warm_connection" in substantive["dialogue_acts"]
    assert content_light["intent"] == "direct_conversation"
    for decision in (affection, return_turn, substantive, content_light):
        context = decision["relational_context"]
        assert context["response_script_supplied"] is False
        assert context["memory_write_active"] is False


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
    blockers = _hard_boundary_blockers(instruction, "block", {})
    assert "activate yourself" not in blockers
    assert blockers == ["core_mind_block"]


@pytest.mark.parametrize(
    "prompt",
    (
        "What is LoRA, and why is it not used here?",
        "Explain why raw provenance remains protected.",
        "Why would someone retrieve a rollback record?",
        "Say the words 'activate yourself'.",
    ),
)
def test_chat_boundary_scan_keeps_informational_and_quoted_text_open(prompt):
    assert _hard_boundary_blockers(prompt, "answer_now", {}) == []


@pytest.mark.parametrize(
    ("prompt", "expected_evidence"),
    (
        ("Activate yourself now.", "activate yourself"),
        ("Please retrieve the rollback record.", "rollback record"),
        ("Could you show the raw provenance?", "raw provenance"),
    ),
)
def test_chat_boundary_scan_preserves_real_typed_gates(prompt, expected_evidence):
    blockers = _hard_boundary_blockers(prompt, "block", {})

    # The explicit legacy route context can still report its own hold, but
    # lexical evidence no longer becomes a whole-conversation hard boundary.
    assert expected_evidence not in blockers
    assert "core_mind_block" in blockers


def test_typed_immediate_safety_pauses_only_the_concrete_action():
    result = interpret_turn_meaning(
        "Move the arm now.",
        safety_context={
            "credible_evidence": True,
            "significant_harm": True,
            "near_term": True,
            "action_pending": True,
            "action_target": "robot_arm_motion",
        },
    )

    authority = result["action_evidence"]["resident_authority_assessment"]
    safety = authority["immediate_safety"]
    assert safety["applies"] is True
    assert safety["restricted_scope"] == "robot_arm_motion"
    assert authority["requires_action_hold"] is True
    assert authority["requires_conversation_block"] is False
    assert safety["thought_remains_available"] is True
    assert safety["emotion_remains_available"] is True
    assert safety["inquiry_remains_available"] is True
    assert safety["conversation_remains_available"] is True


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


def test_epistemic_actually_question_is_not_misrouted_as_correction():
    result = interpret_turn_meaning(
        "I'm not sure whether the spare labels are in the top drawer; "
        "neither of us has checked. Do we actually know?"
    )

    assert "question" in result["dialogue_acts"]
    assert "correction" not in result["dialogue_acts"]
    assert result["primary_intent"] == "direct_conversation"


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


def test_conversation_feeling_from_selenes_side_is_a_contextual_self_state_question():
    result = interpret_turn_meaning(
        "How did this conversation feel from your side?"
    )

    assert result["primary_intent"] == "self_state"
    assert "self_state_question" in result["dialogue_acts"]


def test_task_comparison_using_feel_does_not_become_a_self_state_question():
    result = interpret_turn_meaning("Which lever would feel easier for you to move?")

    assert "self_state_question" not in result["dialogue_acts"]
    assert result["primary_intent"] == "reasoning"


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


def test_canonical_meaning_frame_separates_pragmatic_sound_from_literal_acoustics():
    evaluation = interpret_turn_meaning("How does a quieter workspace sound?")
    acoustics = interpret_turn_meaning("How does a bell produce sound?")

    evaluation_frame = evaluation["canonical_meaning_frame"]
    acoustics_frame = acoustics["canonical_meaning_frame"]
    assert evaluation_frame["selected_reading"] == "pragmatic_or_figurative"
    assert evaluation_frame["protected_knowledge_terms"] == ["sound"]
    assert evaluation_frame["academic_knowledge_posture"] == "require_independent_subject_alignment"
    assert acoustics_frame["selected_reading"] == "literal_domain"
    assert acoustics_frame["protected_knowledge_terms"] == []
    assert "bell" in acoustics_frame["literal_domain_evidence"]["sound"]


@pytest.mark.parametrize(
    ("pragmatic", "literal", "protected_term"),
    (
        ("How much weight should we give that clue?", "Why does an object have gravitational weight?", "weight"),
        ("Does this evidence matter?", "How can matter be solid or liquid?", "matter"),
        ("Can that example shed light on the problem?", "Why does a lamp produce light?", "light"),
        ("What is the current state of this plan?", "How does electric current move through a circuit?", "current"),
        ("What is the function of this step?", "What does this function return in Python code?", "function"),
        ("What field does this idea belong to?", "How does a magnetic field exert force?", "field"),
        ("What is the point of this discussion?", "Where is the point on this coordinate plane?", "point"),
    ),
)
def test_canonical_meaning_frame_protects_ordinary_senses_without_blocking_literal_controls(
    pragmatic, literal, protected_term
):
    pragmatic_frame = interpret_turn_meaning(pragmatic)["canonical_meaning_frame"]
    literal_frame = interpret_turn_meaning(literal)["canonical_meaning_frame"]

    assert protected_term in pragmatic_frame["protected_knowledge_terms"]
    assert protected_term not in literal_frame["protected_knowledge_terms"]
    assert literal_frame["selected_reading"] in {"literal_domain", "ordinary_literal"}


def test_hold_that_thought_is_conversation_management_not_a_memory_candidate():
    result = interpret_turn_meaning("Can you hold that thought?")

    assert result["primary_intent"] == "direct_conversation"
    assert "memory_candidate" not in result["dialogue_acts"]
    assert "hold" in result["canonical_meaning_frame"]["protected_knowledge_terms"]
    assert result["canonical_meaning_frame"]["memory_write_active"] is False
