from __future__ import annotations

from selene.contextual_speech import (
    apply_contextual_intent,
    contextual_response_seed,
    inspect_contextual_follow_up,
)


def _context(previous: str, *, answer_confidence: str = "provisional") -> dict:
    return {
        "previous_turn": {
            "role": "selene",
            "preview": previous,
            "confidence_vector": {
                "answer_confidence": answer_confidence,
                "expression_confidence": "clear",
                "dimensions_are_independent": True,
            },
        },
        "recent_assistant_texts": [previous],
    }


def test_short_follow_ups_are_bounded_to_the_immediate_session_turn():
    context = _context("Memory should come first because it supplies supported meaning to Voice.")

    confidence = inspect_contextual_follow_up("Are you sure?", context)
    reason = inspect_contextual_follow_up("Why?", context)
    continuation = inspect_contextual_follow_up("And then?", context)
    elaboration = inspect_contextual_follow_up("Can you elaborate?", context)

    assert confidence["kind"] == "confidence_check"
    assert reason["kind"] == "reason_follow_up"
    assert continuation["kind"] == "continuation"
    assert elaboration["kind"] == "elaboration"
    for result in (confidence, reason, continuation, elaboration):
        assert result["detected"] is True
        assert result["preserve_active_topic"] is True
        assert result["session_scoped_only"] is True
        assert result["memory_write_active"] is False


def test_short_words_without_a_previous_turn_do_not_invent_context():
    result = inspect_contextual_follow_up("Why?", {})

    assert result["detected"] is False
    assert result["kind"] == "none"


def test_confidence_follow_up_uses_answer_confidence_not_expression_confidence():
    weak = inspect_contextual_follow_up(
        "Are you sure?",
        _context("That is my current answer.", answer_confidence="provisional"),
    )
    decision = apply_contextual_intent({"intent": "direct_conversation"}, weak)
    response = contextual_response_seed(weak)

    assert decision["intent"] == "confidence_check"
    assert decision["primary_organ"] == "Metacognition"
    assert "Not completely" in response
    assert "call it certain" in response


def test_topic_shift_is_not_treated_as_a_correction():
    result = inspect_contextual_follow_up(
        "Actually, separate question: how should uncertainty sound?",
        _context("We were discussing memory sequencing."),
    )

    assert result["kind"] == "topic_shift"
    assert result["preserve_active_topic"] is False


def test_dependency_answer_supports_example_rephrase_and_viewpoint_follow_ups():
    previous = (
        "Start with whichever option supplies a prerequisite the other one needs. "
        "If neither depends on the other, start with the smaller reversible step."
    )
    context = _context(previous, answer_confidence="clear_enough_to_continue")

    example = inspect_contextual_follow_up("Can you give me an example?", context)
    rephrase = inspect_contextual_follow_up("Put that more simply.", context)
    viewpoint = inspect_contextual_follow_up("What do you think?", context)

    assert example["kind"] == "example_request"
    assert rephrase["kind"] == "rephrase_request"
    assert viewpoint["kind"] == "viewpoint_follow_up"
    assert "if step B needs a result" in contextual_response_seed(example)
    assert "do the step that creates" in contextual_response_seed(rephrase)
    assert "dependency rule is the stronger part" in contextual_response_seed(viewpoint)


def test_explicit_reason_and_reconsideration_callback_uses_the_previous_recommendation():
    previous = (
        "My recommendation for the next small step is a reversible two-zone trial: "
        "track water used and the visible outcome for both goals."
    )
    result = inspect_contextual_follow_up(
        "That makes sense. Why do you prefer the two-zone trial first, and what result would make you change your recommendation?",
        _context(previous, answer_confidence="clear_enough_to_continue"),
    )
    response = contextual_response_seed(result)

    assert result["detected"] is True
    assert result["kind"] == "reason_follow_up"
    assert result["preserve_active_topic"] is True
    assert "two-zone trial" in response
    assert "change that recommendation" in response
    assert "both stated goals" in response
