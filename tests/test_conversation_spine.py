from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.conversation_spine import (
    build_conversation_spine,
    evaluate_candidate_compatibility,
    finalize_conversation_spine,
    spine_response_alignment,
)
from selene.pragmatic_planner import build_pragmatic_plan


def _dialogue(prompt: str, *, topic: str = "community garden limited water vegetables pollinators"):
    return {
        "active_topic": topic,
        "side_topics": [],
        "entities": [],
        "referents": {},
        "open_loops": [
            {
                "id": "loop-1",
                "question": prompt,
                "topic": topic,
                "status": "open",
            }
        ],
        "new_loop_ids": ["loop-1"],
        "pragmatics": {
            "dialogue_act": "reasoning",
            "question_units": [prompt],
            "utterance_units": [{"kind": "question", "text": prompt}],
            "resolved_reference": None,
            "previous_turn_available": False,
        },
    }


def test_conversation_spine_collects_one_shared_grounding_packet():
    prompt = "What two approaches would you compare, and what small next step would you recommend?"
    spine = build_conversation_spine(
        {
            "session_id": 12,
            "prompt": prompt,
            "intent_decision": classify_chat_intent(prompt),
            "dialogue_workspace": _dialogue(prompt),
        }
    )

    assert spine["status"] == "conversation_spine_ready"
    assert spine["session_scoped_only"] is True
    assert spine["active_topic"].startswith("community garden")
    assert spine["open_obligations"][0]["loop_id"] == "loop-1"
    assert "garden" in spine["distinctive_terms"]
    assert spine["memory_write_active"] is False
    assert spine["identity_change"] is False
    assert spine["governance_change"] is False
    assert spine["authority_change"] is False


def test_conversation_spine_exposes_the_dialogue_workspaces_shared_thread_braid():
    prompt = "Plan the garden. Then move to irrigation. Back to the garden: use that to revise it."
    dialogue = _dialogue(prompt, topic="garden")
    braid = {
        "status": "conversation_thread_braid_ready",
        "braided": True,
        "active_thread_id": "garden",
        "turn_traversal": [
            {"index": 1, "thread_id": "garden", "action": "start"},
            {"index": 2, "thread_id": "water", "action": "branch"},
            {
                "index": 3,
                "thread_id": "garden",
                "action": "revise_with_dependency",
                "dependency_thread_id": "water",
            },
        ],
    }
    dialogue["pragmatics"]["thread_braid"] = braid
    spine = build_conversation_spine(
        {
            "session_id": 15,
            "prompt": prompt,
            "intent_decision": classify_chat_intent(prompt),
            "dialogue_workspace": dialogue,
        }
    )

    assert spine["version"] == "v2_braided_turn_grounding"
    assert spine["thread_braid"] == braid
    assert spine["thread_traversal"] == braid["turn_traversal"]
    assert spine["session_scoped_only"] is True


def test_conversation_spine_carries_the_previous_recommendation_into_a_callback():
    prompt = "Why do you prefer the two-zone trial first, and what would make you change it?"
    contextual = {
        "detected": True,
        "kind": "reason_follow_up",
        "previous_assistant_preview": (
            "My recommendation for the next small step is a reversible two-zone trial. "
            "Use the same observation period for both options."
        ),
        "preserve_active_topic": True,
    }
    intent = {
        **classify_chat_intent(prompt),
        "intent": "reasoning",
        "reasoning_requested": True,
        "contextual_follow_up": contextual,
    }
    dialogue = _dialogue(prompt)
    dialogue["pragmatics"]["previous_turn_available"] = True
    spine = build_conversation_spine(
        {
            "session_id": 13,
            "prompt": prompt,
            "intent_decision": intent,
            "dialogue_workspace": dialogue,
            "contextual_follow_up": contextual,
        }
    )

    assert spine["intent_class"] == "contextual_content"
    assert spine["previous_answer"]["available"] is True
    assert "two-zone trial" in spine["previous_answer"]["recommendations"][0]
    assert "Immediate prior answer:" in spine["grounded_prompt"]
    assert spine["source_compatibility"]["immediate_callback_prefers_previous_answer"] is True


def test_spine_rejects_content_sources_for_a_self_state_check_in():
    prompt = "How are you feeling about talking with us for a few minutes?"
    intent = {
        **classify_chat_intent(prompt),
        "intent": "self_state",
        "self_state_requested": True,
    }
    spine = build_conversation_spine(
        {
            "session_id": 14,
            "prompt": prompt,
            "intent_decision": intent,
            "dialogue_workspace": _dialogue(prompt, topic=""),
        }
    )

    knowledge = evaluate_candidate_compatibility(
        spine,
        {
            "source_id": "approved_comprehension",
            "source_class": "approved_knowledge",
            "text": "Understanding requires reconstruction and application.",
        },
    )
    self_state = evaluate_candidate_compatibility(
        spine,
        {
            "source_id": "grounded_self_state",
            "source_class": "self_state",
            "text": "I feel present and attentive right now.",
        },
    )

    assert knowledge["compatible"] is False
    assert knowledge["reason"] == "source_class_incompatible_with_current_intent"
    assert self_state["compatible"] is True


def test_spine_rejects_unrelated_reasoning_even_when_the_source_class_is_allowed():
    prompt = "How should the garden divide limited water between vegetables and pollinators?"
    intent = {**classify_chat_intent(prompt), "intent": "reasoning", "reasoning_requested": True}
    spine = build_conversation_spine(
        {
            "session_id": 15,
            "prompt": prompt,
            "intent_decision": intent,
            "dialogue_workspace": _dialogue(prompt),
        }
    )

    unrelated = evaluate_candidate_compatibility(
        spine,
        {
            "source_id": "intelligence_os_answer",
            "source_class": "reasoning_answer",
            "text": "A sorting algorithm should be checked against the same input.",
        },
    )
    related = evaluate_candidate_compatibility(
        spine,
        {
            "source_id": "intelligence_os_answer",
            "source_class": "reasoning_answer",
            "text": "Try a measured garden water allocation that supports both vegetables and pollinators.",
        },
    )

    assert unrelated["compatible"] is False
    assert unrelated["reason"] == "candidate_lacks_distinctive_topic_alignment"
    assert related["compatible"] is True
    assert "garden" in related["matched_terms"]


def test_spine_does_not_treat_incidental_one_as_approved_knowledge_alignment():
    prompt = "Which part of that revised staffing plan should we protect first?"
    intent = {**classify_chat_intent(prompt), "intent": "reasoning", "reasoning_requested": True}
    spine = build_conversation_spine(
        {
            "session_id": 151,
            "prompt": prompt,
            "intent_decision": intent,
            "dialogue_workspace": _dialogue(prompt),
        }
    )

    result = evaluate_candidate_compatibility(
        spine,
        {
            "source_id": "approved_comprehension",
            "source_class": "approved_knowledge",
            "text": "Translate every denomination into one common currency unit.",
        },
    )

    assert result["compatible"] is False
    assert result["matched_terms"] == []


def test_spine_response_alignment_is_visible_and_conservative():
    prompt = "Why would the two-zone trial help the garden?"
    intent = {**classify_chat_intent(prompt), "intent": "reasoning", "reasoning_requested": True}
    spine = build_conversation_spine(
        {
            "session_id": 16,
            "prompt": prompt,
            "intent_decision": intent,
            "dialogue_workspace": _dialogue(prompt),
        }
    )

    unrelated = spine_response_alignment(spine, "The result changes when the input changes.")
    related = spine_response_alignment(spine, "The two-zone trial gives the garden a reversible comparison.")

    assert unrelated["aligned"] is False
    assert related["aligned"] is True
    assert "garden" in related["matched_terms"]


def test_downstream_pragmatic_plan_reuses_spine_obligation_ids():
    prompt = "Why would the two-zone trial help the garden?"
    intent = {**classify_chat_intent(prompt), "intent": "reasoning", "reasoning_requested": True}
    dialogue = _dialogue(prompt)
    spine = build_conversation_spine(
        {
            "session_id": 17,
            "prompt": prompt,
            "intent_decision": intent,
            "dialogue_workspace": dialogue,
        }
    )
    downstream = build_pragmatic_plan(
        {
            "prompt": prompt,
            "content_seed": "The trial gives the garden a reversible comparison.",
            "intent_decision": intent,
            "dialogue_workspace": dialogue,
            "conversation_spine": spine,
        }
    )

    assert downstream["conversation_spine_used"] is True
    assert downstream["conversation_spine_turn_id"] == spine["turn_id"]
    assert downstream["obligation_sequence"] == spine["obligation_sequence"]


def test_finalized_spine_records_only_the_visible_turn_summary():
    prompt = "Why would the two-zone trial help the garden?"
    intent = {**classify_chat_intent(prompt), "intent": "reasoning", "reasoning_requested": True}
    spine = build_conversation_spine(
        {
            "session_id": 18,
            "prompt": prompt,
            "intent_decision": intent,
            "dialogue_workspace": _dialogue(prompt),
        }
    )
    completed = finalize_conversation_spine(
        spine,
        {
            "candidate_text": "The two-zone trial gives the garden a reversible comparison.",
            "source_id": "intelligence_os_answer",
            "source_class": "reasoning_answer",
            "response_coverage": {
                "all_required_addressed": True,
                "unresolved_count": 0,
                "answered_loop_ids": ["loop-1"],
            },
            "confidence_vector": {
                "answer_confidence": "bounded",
                "expression_confidence": "clear",
            },
        },
    )

    assert completed["status"] == "conversation_spine_turn_completed"
    assert completed["released_response"]["coverage_complete"] is True
    assert completed["released_response"]["answered_loop_ids"] == ["loop-1"]
    assert completed["confidence_vector"]["answer_confidence"] == "bounded"
    assert completed["updated_after_turn"] is True
    assert completed["memory_write_active"] is False
