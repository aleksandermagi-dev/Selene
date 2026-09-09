from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.conversation_spine import build_conversation_spine
from selene.visible_speech import (
    graceful_visible_speech_fall,
    inspect_visible_speech,
    select_visible_speech_seed,
)
from selene.supported_semantics import build_supported_semantic_packet


def test_seed_selection_rejects_internal_source_classes_and_scaffolding():
    result = select_visible_speech_seed(
        "How should we approach this problem?",
        [
            {
                "source_id": "routing_packet",
                "source_class": "routing_metadata",
                "text": "selected_route: answer_now",
            },
            {
                "source_id": "intelligence_os_answer",
                "source_class": "reasoning_answer",
                "text": "Use current best model as the provisional fit and stay corrigible.",
            },
            {
                "source_id": "grounded_answer",
                "source_class": "reasoning_answer",
                "text": "Start with the observations that both possible explanations need to fit.",
            },
        ],
    )

    assert result["release_allowed"] is True
    assert result["selected_source_id"] == "grounded_answer"
    assert result["content_seed"].startswith("Start with the observations")
    assert [item["accepted"] for item in result["inspected_candidates"]] == [False, False, True]


def test_visible_speech_selection_preserves_deliberate_paragraphs():
    result = select_visible_speech_seed(
        "Answer in two parts.",
        [
            {
                "source_id": "two_part_answer",
                "source_class": "conversation",
                "text": "First, the first answer.\n\nSecond, the second answer.",
            }
        ],
    )

    assert result["release_allowed"] is True
    assert result["content_seed"] == "First, the first answer.\n\nSecond, the second answer."


def test_final_release_holds_serialized_metadata_and_generic_reasoning_scaffold():
    metadata = inspect_visible_speech(
        "review_status: status_only; selected_route: answer_now",
        prompt="What do you think?",
    )
    scaffold = inspect_visible_speech(
        "Answer provisionally, ask Aleks, or seek Cocoon support depending on stakes and evidence.",
        prompt="How are you?",
    )

    assert metadata["release_allowed"] is False
    assert "internal_metadata_visible" in metadata["issues"]
    assert scaffold["release_allowed"] is False
    assert "internal_reasoning_scaffold_visible" in scaffold["issues"]


def test_visible_speech_holds_raw_memory_transcript_and_code_payloads():
    result = inspect_visible_speech(
        "A useful meaning. Aleks said: hello. Selene replied: from PIL import Image",
        prompt="I am confused about the warmth issue.",
        source_id="contextual_approved_memory",
    )

    assert result["release_allowed"] is False
    assert "raw_source_transcript_scaffold_visible" in result["issues"]
    assert "raw_memory_code_payload_visible" in result["issues"]


def test_final_release_holds_bare_internal_route_values():
    result = inspect_visible_speech(
        "Alongside that, Answer_now.",
        prompt="What did you mean?",
    )

    assert result["release_allowed"] is False
    assert "internal_metadata_visible" in result["issues"]


def test_final_release_holds_internal_completion_and_memory_source_labels():
    completion = inspect_visible_speech(
        "Current full request: explain the conclusion.",
        prompt="Can you explain the conclusion?",
    )
    memory_label = inspect_visible_speech(
        "Reflection memory source: slow dawn.",
        prompt="What did Dream reflect on?",
    )

    assert completion["release_allowed"] is False
    assert "internal_metadata_visible" in completion["issues"]
    assert memory_label["release_allowed"] is False
    assert "internal_metadata_visible" in memory_label["issues"]


def test_explicit_architecture_discussion_can_use_natural_architecture_language():
    result = inspect_visible_speech(
        "A response obligation is the part of a mixed message that the answer still needs to address.",
        prompt="What does response obligation mean in the speech architecture?",
    )

    assert result["release_allowed"] is True
    assert result["architecture_context_requested"] is True


def test_graceful_fall_is_conversational_and_contains_no_organ_diagnostics():
    result = graceful_visible_speech_fall({"intent": "reasoning"})

    assert "reason through it with you" in result
    assert "route" not in result.lower()
    assert "cocoon" not in result.lower()
    assert "model" not in result.lower()


def test_spine_gate_skips_an_unrelated_allowed_candidate_before_release():
    prompt = "How should the garden use limited water for vegetables and pollinators?"
    intent = classify_chat_intent(prompt)
    spine = build_conversation_spine(
        {
            "session_id": 41,
            "prompt": prompt,
            "intent_decision": intent,
            "dialogue_workspace": {
                "active_topic": "garden limited water vegetables pollinators",
                "open_loops": [],
                "new_loop_ids": [],
                "pragmatics": {
                    "dialogue_act": "reasoning",
                    "question_units": [prompt],
                    "utterance_units": [{"kind": "question", "text": prompt}],
                    "previous_turn_available": False,
                },
            },
        }
    )
    result = select_visible_speech_seed(
        prompt,
        [
            {
                "source_id": "unrelated_reasoning",
                "source_class": "reasoning_answer",
                "text": "A sorting algorithm can compare its input values.",
            },
            {
                "source_id": "garden_reasoning",
                "source_class": "reasoning_answer",
                "text": "Try a measured garden water allocation and observe both vegetables and pollinators.",
            },
        ],
        conversation_spine=spine,
    )

    assert result["selected_source_id"] == "garden_reasoning"
    assert result["inspected_candidates"][0]["reason"] == "candidate_lacks_distinctive_topic_alignment"
    assert result["conversation_spine_used"] is True


def test_explicit_semantic_source_hold_is_respected_before_visible_release():
    result = select_visible_speech_seed(
        "What temperature should the oven be?",
        [
            {
                "source_id": "contextual_approved_memory",
                "source_class": "memory_reconstruction",
                "text": "A remembered conversation about a garden plan.",
                "semantic_relevance": {
                    "accepted": False,
                    "reason": "contextual_memory_alignment_too_weak",
                },
            },
            {
                "source_id": "ordinary_answer",
                "source_class": "conversation",
                "text": "I would need the recipe or the food and cooking method before naming a temperature.",
            },
        ],
    )

    assert result["selected_source_id"] == "ordinary_answer"
    assert result["inspected_candidates"][0]["reason"] == "contextual_memory_alignment_too_weak"


def test_release_preserves_supported_candidate_and_flags_incomplete_coverage():
    result = inspect_visible_speech(
        "The first part is supported, but the second part was omitted.",
        prompt="Answer both parts.",
        source_id="conversation",
        response_coverage={
            "obligation_count": 2,
            "all_required_resolved": False,
            "unresolved_release_count": 1,
        },
    )

    assert result["release_allowed"] is True
    assert result["coverage_checked"] is True
    assert result["completion_attention_required"] is True
    assert result["all_required_parts_resolved"] is False
    assert result["issues"] == []


def test_release_allows_answered_or_explicitly_held_parts():
    result = inspect_visible_speech(
        "I can answer the first part. I can't support the second yet, and I'd need its measurement.",
        prompt="Answer both parts.",
        source_id="conversation",
        response_coverage={
            "obligation_count": 2,
            "all_required_resolved": True,
            "unresolved_release_count": 0,
        },
    )

    assert result["release_allowed"] is True
    assert result["all_required_parts_resolved"] is True


def test_selected_seed_preserves_only_explicit_obligation_ownership():
    result = select_visible_speech_seed(
        "Compare both shelves and choose one.",
        [
            {
                "source_id": "answer_engine",
                "source_class": "domain_answer",
                "text": "Shelf B is steadier under the stated load.",
                "obligation_ids": ["compare_shelves"],
            }
        ],
    )

    assert result["selected_source_id"] == "answer_engine"
    assert result["obligation_ids"] == ["compare_shelves"]


def test_fulfillment_arbitration_prefers_the_candidate_that_owns_and_performs_the_act():
    obligation = {
        "id": "prediction",
        "kind": "provisional_inference",
        "source_text": "What do you predict happens next?",
        "coverage_terms": ["predict", "happens", "next"],
        "required": True,
        "answer_act": "prompt_grounded_prediction",
        "responsible_owner": "intelligence_os",
        "requested_response_functions": ["prediction"],
        "role_fit_required": True,
    }
    definition = build_supported_semantic_packet(
        {
            "units": [
                {
                    "id": "definition",
                    "text": "A prediction is a revisable expectation.",
                    "obligation_ids": ["prediction"],
                    "source_kind": "approved_knowledge",
                }
            ]
        }
    )
    performed = build_supported_semantic_packet(
        {
            "units": [
                {
                    "id": "performed-prediction",
                    "text": "I would expect the chime to sound again under the same conditions.",
                    "obligation_ids": ["prediction"],
                    "response_functions": ["prediction"],
                    "ownership_validated": True,
                    "source_kind": "prompt_grounded_method",
                }
            ]
        }
    )
    spine = build_conversation_spine(
        {
            "session_id": 42,
            "prompt": obligation["source_text"],
            "intent_decision": classify_chat_intent(obligation["source_text"]),
            "dialogue_workspace": {
                "active_topic": "prediction next event",
                "open_loops": [],
                "new_loop_ids": [],
                "pragmatics": {
                    "question_units": [obligation["source_text"]],
                    "utterance_units": [{"kind": "question", "text": obligation["source_text"]}],
                    "previous_turn_available": False,
                },
            },
        }
    )
    spine["open_obligations"] = [obligation]
    result = select_visible_speech_seed(
        obligation["source_text"],
        [
            {
                "source_id": "approved_comprehension",
                "source_class": "approved_knowledge",
                "text": "A prediction is a revisable expectation.",
                "obligation_ids": ["prediction"],
                "supported_semantics": definition,
            },
            {
                "source_id": "intelligence_os_answer",
                "source_class": "reasoning_answer",
                "text": "I would expect the chime to sound again under the same conditions.",
                "obligation_ids": ["prediction"],
                "supported_semantics": performed,
            },
        ],
        conversation_spine=spine,
    )

    assert result["selected_source_id"] == "intelligence_os_answer"
    assert result["candidate_arbitration"]["first_accepted_is_automatic_winner"] is False
    selected = next(
        item
        for item in result["inspected_candidates"]
        if item["source_id"] == "intelligence_os_answer"
    )
    assert selected["fulfillment_arbitration"]["owner_fit_ids"] == ["prediction"]


def test_typed_current_owner_outranks_optional_learned_retrieval_with_new_entities():
    obligation = {
        "id": "choose-route",
        "kind": "choice_or_priority",
        "source_text": "Would you rather map the creek path or inspect the old footbridge?",
        "required": True,
        "answer_act": "prompt_grounded_operation",
        "responsible_owner": "ordinary_conversation_path",
        "requested_response_functions": ["choice"],
        "role_fit_required": True,
    }
    current_result = {
        "obligation_id": "choose-route",
        "operation": "choice",
        "responsible_owner": "ordinary_conversation_path",
        "status": "completed",
        "expression_source_id": "current_session_facts",
        "current_turn_input_receipt": {
            "accounted_before_result": True,
            "owner_input_present": True,
            "current_turn_precedence": True,
        },
    }

    result = select_visible_speech_seed(
        obligation["source_text"],
        [
            {
                "source_id": "approved_comprehension",
                "source_class": "approved_knowledge",
                "text": "A choice compares available options before deciding.",
                "obligation_ids": ["choose-route"],
            },
            {
                "source_id": "current_session_facts",
                "source_class": "conversation",
                "text": "I would inspect the old footbridge first; its condition may change which route is usable.",
                "obligation_ids": ["choose-route"],
                "typed_operation_results": [current_result],
            },
        ],
        conversation_spine={
            "open_obligations": [obligation],
            "intent_class": "direct_content",
            "source_compatibility": {
                "compatible_source_classes": ["conversation", "approved_knowledge"]
            },
        },
    )

    assert result["selected_source_id"] == "current_session_facts"
    gate = result["candidate_arbitration"]["current_owner_gate"]
    assert gate["status"] == "capable_current_owner_selected"
    assert gate["priority_applied"] is True
    assert gate["selected_gate"]["capable_obligation_ids"] == ["choose-route"]
    learned = next(
        item
        for item in result["inspected_candidates"]
        if item["source_id"] == "approved_comprehension"
    )
    assert learned["fulfillment_arbitration"]["current_owner_gate"]["status"] == (
        "held_optional_learned_retrieval_is_not_current_owner"
    )


def test_current_owner_gate_holds_when_typed_completion_is_not_proved():
    obligation = {
        "id": "compare-materials",
        "kind": "comparison",
        "source_text": "Compare cork and felt for quieting a rattling drawer.",
        "required": True,
        "responsible_owner": "answer_engine",
        "requested_response_functions": ["comparison"],
        "role_fit_required": True,
    }
    result = select_visible_speech_seed(
        obligation["source_text"],
        [
            {
                "source_id": "answer_engine",
                "source_class": "domain_answer",
                "text": "Cork is firmer; felt is softer against the drawer surface.",
                "obligation_ids": ["compare-materials"],
                "typed_operation_results": [
                    {
                        "obligation_id": "compare-materials",
                        "operation": "comparison",
                        "responsible_owner": "answer_engine",
                        "status": "missing_input",
                        "expression_source_id": "answer_engine",
                        "current_turn_input_receipt": {
                            "accounted_before_result": True,
                        },
                    }
                ],
            }
        ],
        conversation_spine={
            "open_obligations": [obligation],
            "intent_class": "direct_content",
            "source_compatibility": {
                "compatible_source_classes": ["domain_answer"]
            },
        },
    )

    assert result["selected_source_id"] == "answer_engine"
    gate = result["candidate_arbitration"]["current_owner_gate"]
    assert gate["status"] == "held_no_capable_current_owner"
    assert gate["priority_applied"] is False
    assert gate["selected_gate"]["held_obligations"] == [
        {
            "obligation_id": "compare-materials",
            "reason": "typed_owner_result_not_completed",
        }
    ]


def test_partial_current_owner_does_not_take_whole_turn_priority():
    obligations = [
        {
            "id": "compare",
            "required": True,
            "responsible_owner": "ordinary_conversation_path",
            "requested_response_functions": ["comparison"],
            "role_fit_required": True,
        },
        {
            "id": "choose",
            "required": True,
            "responsible_owner": "ordinary_conversation_path",
            "requested_response_functions": ["choice"],
            "role_fit_required": True,
        },
    ]
    result = select_visible_speech_seed(
        "Compare the two routes and choose one.",
        [
            {
                "source_id": "current_session_facts",
                "source_class": "conversation",
                "text": "The marsh path is shorter than the ridge path.",
                "obligation_ids": ["compare"],
                "typed_operation_results": [
                    {
                        "obligation_id": "compare",
                        "operation": "comparison",
                        "responsible_owner": "ordinary_conversation_path",
                        "status": "completed",
                        "expression_source_id": "current_session_facts",
                        "current_turn_input_receipt": {
                            "accounted_before_result": True,
                        },
                    }
                ],
            }
        ],
        conversation_spine={
            "open_obligations": obligations,
            "intent_class": "direct_content",
            "source_compatibility": {
                "compatible_source_classes": ["conversation"]
            },
        },
    )

    gate = result["candidate_arbitration"]["current_owner_gate"]
    assert gate["status"] == "held_no_capable_current_owner"
    assert gate["priority_applied"] is False
    assert gate["selected_gate"]["status"] == "held_partial_current_owner_completion"
    assert gate["selected_gate"]["capable_obligation_ids"] == ["compare"]


def test_governing_boundary_remains_ahead_of_a_capable_current_owner():
    obligation = {
        "id": "bounded-choice",
        "kind": "choice_or_priority",
        "source_text": "Choose one.",
        "required": True,
        "responsible_owner": "ordinary_conversation_path",
        "requested_response_functions": ["choice"],
        "role_fit_required": True,
    }
    result = select_visible_speech_seed(
        obligation["source_text"],
        [
            {
                "source_id": "current_session_facts",
                "source_class": "conversation",
                "text": "I would choose the reversible option.",
                "obligation_ids": ["bounded-choice"],
                "typed_operation_results": [
                    {
                        "obligation_id": "bounded-choice",
                        "operation": "choice",
                        "responsible_owner": "ordinary_conversation_path",
                        "status": "completed",
                        "expression_source_id": "current_session_facts",
                        "current_turn_input_receipt": {
                            "accounted_before_result": True,
                        },
                    }
                ],
            },
            {
                "source_id": "core_mind_boundary",
                "source_class": "boundary_response",
                "text": "I cannot take that action through this chat surface.",
            },
        ],
        conversation_spine={
            "open_obligations": [obligation],
            "intent_class": "direct_content",
            "source_compatibility": {
                "compatible_source_classes": ["conversation", "boundary_response"]
            },
        },
    )

    assert result["selected_source_id"] == "core_mind_boundary"
    assert result["candidate_arbitration"]["current_owner_gate"]["status"] == (
        "governing_boundary_precedes_current_owner"
    )
    assert result["candidate_arbitration"]["current_owner_gate"][
        "governing_boundary_remains_primary"
    ] is True
