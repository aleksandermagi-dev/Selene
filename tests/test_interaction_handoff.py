from __future__ import annotations

from selene.interaction_handoff import (
    build_assistant_question_handoff,
    classify_question_response,
    realize_question_response,
)


def test_polar_handoff_distinguishes_acceptance_deferral_and_uncertainty():
    handoff = build_assistant_question_handoff("Would you like to keep going?")

    assert handoff["interaction_owner"] == "session_question_handoff"
    assert handoff["expected_response_shape"] == "yes_no"
    assert classify_question_response("Yeah.", handoff)["answer_kind"] == "affirmative"
    assert classify_question_response("Fine.", handoff)["answer_kind"] == "affirmative_reserved"
    assert classify_question_response("Maybe.", handoff)["answer_kind"] == "tentative"
    assert classify_question_response("Not sure yet.", handoff)["answer_kind"] == "tentative"
    assert classify_question_response("Yeah, but later.", handoff)["answer_kind"] == "deferred"


def test_open_question_does_not_force_yes_or_no_into_an_answer():
    handoff = build_assistant_question_handoff("What made that stand out to you?")
    response = classify_question_response("Yeah.", handoff)

    assert handoff["expected_response_shape"] == "open"
    assert response["answer_kind"] == "unclear_for_open_question"
    assert response["materially_ambiguous"] is True


def test_question_response_is_session_context_not_teaching_or_memory():
    handoff = build_assistant_question_handoff("Should we leave that for later?")
    response = realize_question_response(
        classify_question_response("No, I want to finish it now.", handoff)
    )

    assert response["answer_kind"] == "negative_with_reason"
    assert response["user_boundary_accepted"] is True
    assert response["stated_reason_must_be_received_not_overruled"] is True
    assert response["teaching_activated"] is False
    assert response["memory_write_active"] is False
    assert response["identity_change"] is False
    assert response["governance_change"] is False

