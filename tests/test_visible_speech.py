from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.conversation_spine import build_conversation_spine
from selene.visible_speech import (
    graceful_visible_speech_fall,
    inspect_visible_speech,
    select_visible_speech_seed,
)


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


def test_final_release_holds_bare_internal_route_values():
    result = inspect_visible_speech(
        "Alongside that, Answer_now.",
        prompt="What did you mean?",
    )

    assert result["release_allowed"] is False
    assert "internal_metadata_visible" in result["issues"]


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
