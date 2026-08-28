from selene.semantic_relevance import (
    evaluate_semantic_relevance,
    semantic_relevance_status,
)
from selene.chat_intent import classify_chat_intent


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False


def test_status_describes_a_bounded_non_writing_gate():
    result = semantic_relevance_status()

    assert result["status"] == "semantic_relevance_gate_ready"
    assert result["single_keyword_is_authority"] is False
    assert result["open_ended_reasoning_preserved"] is True
    assert result["bounded_prediction_and_hypothesis_preserved"] is True
    _assert_locked(result)


def test_generic_information_overlap_cannot_redirect_an_oven_question_to_health():
    result = evaluate_semantic_relevance(
        {
            "prompt": "What information would you need to predict the oven temperature?",
            "source_class": "approved_knowledge",
            "candidate": {
                "title": "Reliable health information",
                "domain": "health",
                "concept_key": "reliable_health_information",
                "central_claim": "Health information should be checked against reliable evidence.",
                "principles": ["Use evidence before making a health claim."],
            },
            "intent_decision": {"intent": "reasoning", "reasoning_requested": True},
        }
    )

    assert result["accepted"] is False
    assert result["reason"] == "approved_knowledge_has_only_peripheral_overlap"
    assert "information" not in result["query_terms"]
    _assert_locked(result)


def test_named_subject_accepts_relevant_approved_knowledge_and_preserves_comparison_role():
    result = evaluate_semantic_relevance(
        {
            "prompt": "Which lever arrangement should feel easier, and why?",
            "source_class": "approved_knowledge",
            "candidate": {
                "title": "Levers and fulcrums",
                "domain": "physical science",
                "concept_key": "lever_fulcrum_distance",
                "central_claim": "A lever can reduce the effort needed to move a load.",
                "relationships": [
                    "Increasing the effort arm relative to the load arm changes mechanical advantage."
                ],
                "examples": ["Move the fulcrum closer to the load and compare the effort."],
            },
            "intent_decision": {"intent": "reasoning", "reasoning_requested": True},
        }
    )

    assert result["accepted"] is True
    assert result["reason"] == "approved_knowledge_subject_aligned"
    assert "lever" in result["strong_subject_overlap"]
    assert {"comparison", "reason"}.issubset(set(result["requested_roles"]))
    _assert_locked(result)


def test_explicit_memory_recall_and_contextual_memory_have_different_thresholds():
    candidate = {
        "title": "Butterfly Cocoon button",
        "summary": "The butterfly button opens Cocoon support from Selene's desktop.",
    }
    explicit = evaluate_semantic_relevance(
        {
            "prompt": "Do you remember the butterfly button?",
            "source_class": "memory_reconstruction",
            "candidate": candidate,
            "intent_decision": {"intent": "memory_recall", "memory_recall_requested": True},
        }
    )
    contextual = evaluate_semantic_relevance(
        {
            "prompt": "What should we do next?",
            "source_class": "memory_reconstruction",
            "candidate": candidate,
            "intent_decision": {"intent": "reasoning", "reasoning_requested": True},
        }
    )

    assert explicit["accepted"] is True
    assert contextual["accepted"] is False
    assert contextual["reason"] == "contextual_memory_alignment_too_weak"


def test_private_memory_is_held_for_a_different_claimed_speaker():
    result = evaluate_semantic_relevance(
        {
            "prompt": "Do you remember the butterfly button?",
            "source_class": "memory_reconstruction",
            "candidate": {
                "title": "Butterfly Cocoon button",
                "summary": "The butterfly button opens Cocoon support.",
                "consent_scope": "private_selene_aleks_context",
            },
            "intent_decision": {
                "intent": "memory_recall",
                "memory_recall_requested": True,
            },
            "speaker_envelope": {"claimed_speaker": "Demo guest"},
        }
    )

    assert result["accepted"] is False
    assert result["reason"] == "memory_privacy_scope_does_not_include_current_speaker"
    assert result["speaker_privacy_gate_applied"] is True
    _assert_locked(result)


def test_current_turn_operation_and_facts_outrank_contextual_memory():
    result = evaluate_semantic_relevance(
        {
            "prompt": "Compare paper and thin card using the costs I just gave you.",
            "source_class": "memory_reconstruction",
            "candidate": {
                "title": "Paper craft memory",
                "summary": "Paper was used in an older craft conversation.",
                "consent_scope": "private_selene_aleks_context",
            },
            "intent_decision": {"intent": "reasoning", "reasoning_requested": True},
            "conversation_spine": {
                "current_turn_fact_ledger": {"fact_count": 4},
                "open_obligations": [
                    {
                        "id": "comparison",
                        "requested_response_functions": ["comparison"],
                    }
                ],
            },
            "speaker_envelope": {"claimed_speaker": "Aleks"},
        }
    )

    assert result["accepted"] is False
    assert result["reason"] == "memory_describes_context_but_does_not_perform_requested_operation"
    assert result["current_turn_fact_count"] == 4
    assert result["current_turn_facts_precede_optional_retrieval"] is True
    _assert_locked(result)


def test_prediction_lesson_can_supply_ground_but_cannot_substitute_for_the_prediction():
    result = evaluate_semantic_relevance(
        {
            "prompt": "Based on the cloud and wind pattern, what would you predict next?",
            "source_class": "approved_knowledge",
            "candidate": {
                "title": "Clouds wind and weather change",
                "domain": "earth science",
                "central_claim": "Observed cloud and wind changes can support a bounded weather prediction.",
                "principles": ["A prediction remains revisable when conditions change."],
            },
            "intent_decision": {"intent": "reasoning", "reasoning_requested": True},
            "conversation_spine": {
                "open_obligations": [
                    {
                        "id": "prediction",
                        "requested_response_functions": ["prediction"],
                    }
                ]
            },
        }
    )

    assert result["accepted"] is False
    assert result["reason"] == "approved_knowledge_describes_but_does_not_perform_requested_operation"
    assert "prediction" in result["requested_roles"]
    assert "prediction" in result["candidate_roles"]
    assert result["requested_operation_performed"] is False
    _assert_locked(result)


def test_a_candidate_that_performed_the_requested_prediction_can_be_admitted():
    result = evaluate_semantic_relevance(
        {
            "prompt": "Based on the cloud and wind pattern, what would you predict next?",
            "source_class": "approved_knowledge",
            "candidate": {
                "title": "Clouds wind and weather change",
                "domain": "earth science",
                "central_claim": "Given these visible clouds and winds, rain is the bounded prediction.",
                "performed_response_functions": ["prediction"],
            },
            "intent_decision": {"intent": "reasoning", "reasoning_requested": True},
            "conversation_spine": {
                "open_obligations": [
                    {
                        "id": "prediction",
                        "requested_response_functions": ["prediction"],
                    }
                ]
            },
        }
    )

    assert result["accepted"] is True
    assert result["requested_operation_performed"] is True
    _assert_locked(result)


def test_self_state_source_requires_an_actual_self_state_question():
    comparison = evaluate_semantic_relevance(
        {
            "prompt": "Which lever would feel easier for you to move?",
            "source_class": "self_state",
            "candidate": {"text": "I feel calm and present."},
            "intent_decision": {"intent": "reasoning", "self_state_requested": False},
        }
    )
    check_in = evaluate_semantic_relevance(
        {
            "prompt": "How are you feeling today?",
            "source_class": "self_state",
            "candidate": {"text": "I feel calm and present."},
            "intent_decision": {"intent": "self_state", "self_state_requested": True},
        }
    )

    assert comparison["accepted"] is False
    assert check_in["accepted"] is True


def test_canonical_pragmatic_sense_cannot_be_laundered_into_academic_relevance():
    prompt = "How does a quieter workspace sound?"
    result = evaluate_semantic_relevance(
        {
            "prompt": prompt,
            "source_class": "approved_knowledge",
            "candidate": {
                "title": "Vibrating matter can make sound",
                "domain": "physical science acoustics",
                "concept_key": "sound_vibration",
                "central_claim": "Vibrating matter can produce sound.",
            },
            "intent_decision": classify_chat_intent(prompt),
        }
    )

    assert result["accepted"] is False
    assert "sound" in result["protected_query_terms"]
    assert "sound" not in result["query_terms"]
    assert result["canonical_meaning_frame_applied"] is True


def test_canonical_literal_control_still_admits_the_named_academic_subject():
    prompt = "How does a bell produce sound?"
    result = evaluate_semantic_relevance(
        {
            "prompt": prompt,
            "source_class": "approved_knowledge",
            "candidate": {
                "title": "Vibrating matter can make sound",
                "domain": "physical science acoustics",
                "concept_key": "sound_vibration",
                "central_claim": "A vibrating bell can produce sound.",
            },
            "intent_decision": classify_chat_intent(prompt),
        }
    )

    assert result["accepted"] is True
    assert result["reason"] == "approved_knowledge_subject_aligned"
    assert result["protected_query_terms"] == []
