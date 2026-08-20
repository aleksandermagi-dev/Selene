from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.contextual_speech import (
    _bounded_social_session_summary,
    _landmark_summary,
    _matching_landmarks,
    apply_contextual_intent,
    contextual_response_seed,
    inspect_contextual_follow_up,
    session_fact_response_seed,
)


def test_social_summary_yields_when_the_session_contains_substantive_work():
    result = _bounded_social_session_summary(
        [
            "Good morning, how are you?",
            "Before another lesson, what prerequisite should we check?",
        ]
    )

    assert result == ""


def test_session_fact_callback_answers_the_visible_details_without_memory():
    spine = {
        "session_facts": [
            {"kind": "dimensions", "text": "The dimensions are six feet by eight feet."},
            {"kind": "count", "text": "There are two chairs."},
        ],
        "relevant_session_facts": [
            {"kind": "dimensions", "text": "The dimensions are six feet by eight feet."},
            {"kind": "count", "text": "There are two chairs."},
        ],
    }

    response = session_fact_response_seed(
        "What were the dimensions and how many chairs did I say?",
        spine,
    )

    assert response == "The dimensions are six feet by eight feet. There are two chairs."


def test_incomplete_landmarks_are_not_used_for_callbacks_or_summaries():
    landmarks = [
        {
            "kind": "conclusion",
            "topic": "teaching",
            "summary": "An unrelated incomplete teaching answer.",
            "coverage_complete_at_recording": False,
        },
        {
            "kind": "recommendation",
            "topic": "teaching",
            "summary": "Check the earliest missing prerequisite first.",
            "coverage_complete_at_recording": True,
        },
    ]

    assert _matching_landmarks("What did we decide about teaching?", landmarks) == [
        landmarks[1]
    ]
    assert _landmark_summary(landmarks) == landmarks[1]["summary"]


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


def test_bare_reason_follow_up_uses_only_the_explicit_reason_in_the_previous_answer():
    previous = (
        "I prefer the shared-schedule pilot first because it keeps the limited rooms and volunteers flexible. "
        "It also gives us visible evidence before we commit to two continuous tracks."
    )

    for prompt in ("Why?", "How come?"):
        follow_up = inspect_contextual_follow_up(
            prompt,
            _context(previous, answer_confidence="clear_enough_to_continue"),
        )
        response = contextual_response_seed(follow_up)

        assert follow_up["kind"] == "reason_follow_up"
        assert follow_up["preserve_active_topic"] is True
        assert response.startswith("Because it keeps the limited rooms and volunteers flexible.")
        assert "visible evidence before we commit" in response
        assert "not have enough evidence" not in response
        assert follow_up["session_scoped_only"] is True
        assert follow_up["memory_write_active"] is False


def test_bare_reason_follow_up_keeps_visible_support_after_a_change_condition():
    previous = (
        "I prefer the shared-schedule pilot first because it keeps the limited rooms and volunteers flexible. "
        "I would switch designs if transitions caused too much disruption. "
        "It also gives us visible evidence about attendance and staffing strain."
    )
    follow_up = inspect_contextual_follow_up("Why?", _context(previous))
    response = contextual_response_seed(follow_up)

    assert response.startswith(
        "Because it keeps the limited rooms and volunteers flexible."
    )
    assert "visible evidence about attendance and staffing strain" in response
    assert "switch designs" not in response


def test_bare_reason_follow_up_does_not_invent_a_reason_when_the_previous_answer_has_none():
    previous = "I would start with the shared-schedule pilot."
    follow_up = inspect_contextual_follow_up("Why?", _context(previous))
    response = contextual_response_seed(follow_up)

    assert response == (
        "I did not state the reason clearly enough in that answer. "
        "I can explain it, but I need the deciding constraint or evidence rather than inventing one."
    )
    assert "mechanism that connects" not in response


def test_bare_confusion_requests_a_bounded_rephrase_of_the_previous_reply():
    previous = "I do not have enough grounding for a clean answer yet."
    follow_up = inspect_contextual_follow_up("what?", _context(previous))
    decision = apply_contextual_intent(classify_chat_intent("what?"), follow_up)
    response = contextual_response_seed(follow_up)

    assert follow_up["kind"] == "rephrase_request"
    assert follow_up["preserve_active_topic"] is True
    assert decision["answer_shape"] == "continue_previous_answer"
    assert response.startswith("I may have said that awkwardly. Put simply:")


def test_phrase_meaning_after_a_misunderstanding_is_a_session_correction():
    previous = "I'm not sure yet because I am missing relevant context."
    follow_up = inspect_contextual_follow_up(
        "whats up means how are you",
        _context(previous),
    )
    decision = apply_contextual_intent(classify_chat_intent("whats up means how are you"), follow_up)

    assert follow_up["kind"] == "meaning_correction"
    assert follow_up["preserve_active_topic"] is True
    assert decision["intent"] == "correction"
    assert decision["reasoning_requested"] is False


def test_mixed_self_state_and_session_summary_preserves_both_requests():
    context = _context("What I can name clearly is presence and attention.")
    context["recent_user_texts"] = [
        "Hey Selene!",
        "What's up?",
        'When I say "what\'s up," I mean "how are you."',
    ]
    prompt = "In two short parts, how are you doing, and what has this conversation been about?"
    follow_up = inspect_contextual_follow_up(prompt, context)
    decision = apply_contextual_intent(classify_chat_intent(prompt), follow_up)
    response = contextual_response_seed(follow_up)

    assert follow_up["kind"] == "session_summary_request"
    assert decision["intent"] == "self_state"
    assert decision["self_state_requested"] is True
    assert decision["answer_shape"] == "self_state_then_session_summary"
    assert "greeting each other" in response
    assert "checking in" in response
    assert "was meant as" in response


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


def test_shared_schedule_callback_understands_switch_as_reconsidering_the_recommendation():
    previous = (
        "I would compare a shared-schedule design with a parallel-zone design. "
        "I would pilot one short shared-schedule block first."
    )
    result = inspect_contextual_follow_up(
        "Why do you prefer the shared-schedule pilot first rather than the parallel-zone design, "
        "and what result would make you switch your recommendation?",
        _context(previous, answer_confidence="clear_enough_to_continue"),
    )
    response = contextual_response_seed(result)

    assert result["kind"] == "reason_follow_up"
    assert "limited rooms and volunteers flexible" in response
    assert "switch to the parallel-zone design" in response
    assert "transitions caused more delay or disruption" in response


def test_explicit_constraint_refinement_revises_the_session_plan_without_replacing_it():
    previous = "I would pilot one short shared-schedule block and track attendance and staffing strain."
    result = inspect_contextual_follow_up(
        "One refinement: assume two volunteers can only stay for the first hour, but both rooms remain "
        "available. Keep the two festival goals the same. How would you revise the pilot?",
        _context(previous, answer_confidence="clear_enough_to_continue"),
    )
    response = contextual_response_seed(result)
    decision = apply_contextual_intent(classify_chat_intent(result["prompt"]), result)

    assert result["kind"] == "constraint_refinement"
    assert result["preserve_active_topic"] is True
    assert decision["intent"] == "reasoning"
    assert "keep the useful core" in response.lower()
    assert "after the two volunteers leave" in response.lower()
    assert "add volunteer load and uncovered-task counts" in response.lower()


def test_priority_callback_protects_the_constrained_part_of_the_revised_plan():
    previous = (
        "I would keep the useful core of the shared-schedule pilot, but revise its staffing sequence. "
        "The quiet reading discussion uses the other room with lighter facilitation."
    )
    result = inspect_contextual_follow_up(
        "If the later quiet session still needs one facilitator, which part of that revised plan should we protect first, and why?",
        _context(previous, answer_confidence="clear_enough_to_continue"),
    )
    response = contextual_response_seed(result)
    decision = apply_contextual_intent(classify_chat_intent(result["prompt"]), result)

    assert result["kind"] == "priority_follow_up"
    assert result["preserve_active_topic"] is True
    assert decision["answer_shape"] == "continue_previous_answer"
    assert "protect one facilitator for the later quiet reading session first" in response.lower()
    assert "staff, rather than room availability" in response.lower()


def test_session_summary_uses_recent_conversation_material_in_three_requested_parts():
    context = _context(
        "Attendance plus wait time and participant feedback is more useful than attendance alone.",
        answer_confidence="clear_enough_to_continue",
    )
    context["recent_assistant_texts"] = [
        "I prefer the shared-schedule pilot first and would switch to the parallel-zone design if transitions caused disruption.",
        "Protect one facilitator for the later quiet reading session.",
    ]
    result = inspect_contextual_follow_up(
        "Summarize the plan for an organizer in three short parts: the design, the pilot, and the condition that would make us change course.",
        context,
    )
    response = contextual_response_seed(result)

    assert result["kind"] == "session_summary_request"
    assert response.count("\n\n") == 2
    assert response.startswith("Design:")
    assert "Pilot:" in response
    assert "Change condition:" in response


def test_analogy_transfer_preserves_the_active_staffing_constraint():
    context = _context("Design: Use a shared schedule for both activities.")
    context["recent_assistant_texts"] = [
        "Use the shared-schedule pilot, then protect one facilitator for quiet reading after two volunteers leave."
    ]
    result = inspect_contextual_follow_up(
        "Explain the logic to a new volunteer using one ordinary analogy, without losing the important staffing constraint.",
        context,
    )
    response = contextual_response_seed(result)

    assert result["kind"] == "analogy_transfer_request"
    assert "ordinary analogy" in response.lower()
    assert "small kitchen" in response.lower()
    assert "two available rooms do not equal two staffed activities" in response.lower()


def test_self_state_reason_callback_stays_bound_to_the_visible_exchange():
    result = inspect_contextual_follow_up(
        "What about this conversation makes you say that?",
        _context("What I can name clearly is presence and attention."),
    )
    response = contextual_response_seed(result)

    assert result["kind"] == "reason_follow_up"
    assert result["marker"] == "reason_about_present_self_report"
    assert "this exchange is calm and focused" in response.lower()
    assert "not a claim about a hidden feeling" in response.lower()


def test_summary_request_can_have_an_ordinary_preface():
    context = _context("We compared two teaching foundations.")
    context["recent_user_texts"] = ["We compared fractions and conversational uncertainty."]
    result = inspect_contextual_follow_up(
        "Before we stop, give me one short recap of this conversation.",
        context,
    )

    assert result["kind"] == "session_summary_request"
    assert result["preserve_active_topic"] is True


def test_immediate_user_result_callback_uses_the_visible_statement():
    context = _context("That sounds like a real milestone.")
    context["recent_user_texts"] = [
        "I'm happy that the first live lesson completed Acquire, Integrate, and Express."
    ]

    result = inspect_contextual_follow_up(
        "What part of that result am I celebrating?",
        context,
    )
    response = contextual_response_seed(result)
    decision = apply_contextual_intent(classify_chat_intent(result["prompt"]), result)

    assert result["kind"] == "immediate_user_callback"
    assert result["previous_user_preview"].startswith("I'm happy")
    assert "first live lesson completed Acquire, Integrate, and Express" in response
    assert decision["intent"] == "reasoning"
    assert result["memory_write_active"] is False
