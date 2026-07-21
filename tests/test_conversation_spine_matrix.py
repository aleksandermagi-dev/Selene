from __future__ import annotations

import pytest

from selene.chat_intent import classify_chat_intent
from selene.contextual_speech import apply_contextual_intent
from selene.conversation_spine import build_conversation_spine, evaluate_candidate_compatibility


def _dialogue(prompt: str, *, previous: str = "") -> dict:
    return {
        "active_topic": "garden water comparison",
        "side_topics": [],
        "entities": [],
        "referents": {},
        "open_loops": [
            {"id": "matrix-loop", "question": prompt, "topic": "garden water comparison", "status": "open"}
        ] if "?" in prompt else [],
        "new_loop_ids": ["matrix-loop"] if "?" in prompt else [],
        "pragmatics": {
            "dialogue_act": "direct_conversation",
            "question_units": [prompt] if "?" in prompt else [],
            "utterance_units": [
                {"kind": "question" if "?" in prompt else "statement", "text": prompt}
            ],
            "previous_turn_available": bool(previous),
            "previous_turn": {"role": "selene", "preview": previous} if previous else {},
        },
    }


@pytest.mark.parametrize(
    ("prompt", "expected_class", "allowed_source_class", "blocked_source_class"),
    [
        ("How are you feeling right now?", "self_state", "self_state", "approved_knowledge"),
        ("Good morning, Selene.", "social", "conversation", "reasoning_answer"),
        ("Why does a reversible trial help?", "reasoning", "reasoning_answer", "memory_reconstruction"),
        ("Compare the two garden water plans.", "reasoning", "domain_answer", "memory_reconstruction"),
        ("Which plan uses less water, and which should we try first?", "reasoning", "reasoning_answer", "self_state"),
        ("Actually, I meant the shade garden, not the sunny garden.", "direct_content", "conversation", "memory_reconstruction"),
        ("Do you remember where we left off?", "memory_recall", "memory_reconstruction", "approved_knowledge"),
        ("Catch you soon, Selene.", "social", "conversation", "domain_answer"),
        ("I may be missing context; what evidence would decide this?", "reasoning", "reasoning_answer", "self_state"),
        ("Separate topic: what makes a source trustworthy?", "reasoning", "reasoning_answer", "memory_reconstruction"),
    ],
)
def test_gentle_matrix_keeps_source_classes_attached_to_turn_intent(
    prompt: str,
    expected_class: str,
    allowed_source_class: str,
    blocked_source_class: str,
):
    intent = classify_chat_intent(prompt)
    spine = build_conversation_spine(
        {
            "session_id": 70,
            "prompt": prompt,
            "intent_decision": intent,
            "dialogue_workspace": _dialogue(prompt),
        }
    )
    aligned_text = f"This answer stays with the garden water comparison in the current question: {prompt}"
    allowed = evaluate_candidate_compatibility(
        spine,
        {"source_id": "matrix_allowed", "source_class": allowed_source_class, "text": aligned_text},
    )
    blocked = evaluate_candidate_compatibility(
        spine,
        {"source_id": "matrix_blocked", "source_class": blocked_source_class, "text": aligned_text},
    )

    assert spine["intent_class"] == expected_class
    assert allowed["compatible"] is True
    assert blocked["compatible"] is False
    assert spine["memory_write_active"] is False
    assert spine["identity_change"] is False
    assert spine["governance_change"] is False
    assert spine["autonomous_action_allowed"] is False


@pytest.mark.parametrize(
    ("prompt", "kind"),
    [
        ("Why do you prefer the two-zone trial first?", "reason_follow_up"),
        ("Can you explain that another way?", "rephrase_request"),
    ],
)
def test_gentle_matrix_callbacks_remain_attached_to_the_previous_visible_answer(prompt: str, kind: str):
    previous = "I recommend the two-zone garden trial because it is reversible."
    contextual = {
        "detected": True,
        "kind": kind,
        "previous_assistant_preview": previous,
        "preserve_active_topic": True,
    }
    intent = apply_contextual_intent(classify_chat_intent(prompt), contextual)
    spine = build_conversation_spine(
        {
            "session_id": 71,
            "prompt": prompt,
            "intent_decision": intent,
            "dialogue_workspace": _dialogue(prompt, previous=previous),
            "contextual_follow_up": contextual,
        }
    )
    callback = evaluate_candidate_compatibility(
        spine,
        {
            "source_id": "contextual_follow_up",
            "source_class": "conversation",
            "text": "The two-zone garden trial is reversible, so it gives us evidence before commitment.",
        },
    )
    unrelated_lesson = evaluate_candidate_compatibility(
        spine,
        {
            "source_id": "approved_comprehension",
            "source_class": "approved_knowledge",
            "text": "An algorithm follows an ordered sequence.",
        },
    )

    assert spine["intent_class"] == "contextual_content"
    assert spine["previous_answer"]["preview"] == previous
    assert callback["compatible"] is True
    assert unrelated_lesson["compatible"] is False
