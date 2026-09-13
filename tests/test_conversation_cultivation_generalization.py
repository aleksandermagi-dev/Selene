from __future__ import annotations

from selene.activation import ACTIVATION_APPROVAL_PHRASE
from selene.module_router import route_request
from tests.test_conversational_teaching import _active_conn
from tests.test_selene_chat_shell import _assert_locked, _conn, _seed_activation_ready_state


def _activated_conn(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(
        conn,
        "activation.approve",
        {"approval_phrase": ACTIVATION_APPROVAL_PHRASE},
    )
    return conn


def _operation(result, operation):
    return next(
        item
        for item in result["answer_operations"]["results"]
        if item["operation"] == operation
    )


def test_phase_nine_generalizes_current_owner_revision_across_new_entities_and_clause_order(
    tmp_path,
):
    conn = _activated_conn(tmp_path)
    prompts = [
        (
            "Sturdiness matters most for the greenhouse run. We have two carts: "
            "one quick but fragile, and one slower but sturdy. Compare them and "
            "choose one."
        ),
        (
            "Update: the gate now closes sooner, though sturdiness remains the "
            "priority. What would you change?"
        ),
        (
            "Suppose later inspections show the sturdy cart cracks twice as often. "
            "How would that change your prediction?"
        ),
    ]
    results = []
    session_id = None
    for prompt in prompts:
        payload = {"text": prompt}
        if session_id is not None:
            payload["session_id"] = session_id
        result = route_request(conn, "selene_chat.send", payload)["result"]
        session_id = result["session_id"]
        results.append(result)

    opening, revision, prediction = results
    assert all(
        result["visible_speech_seed"]["selected_source_id"]
        == "current_session_facts"
        for result in results
    )
    assert all(
        result["visible_speech_seed"]["candidate_arbitration"][
            "current_owner_gate"
        ]["priority_applied"]
        is True
        for result in results
    )
    assert all(
        result["response_coverage"]["all_required_addressed"] is True
        for result in results
    )
    assert all(
        result["learning_gap_invitation"]["offered"] is False
        for result in results
    )
    assert "quick but fragile" in opening["candidate_text"].lower()
    assert "slower but sturdy" in opening["candidate_text"].lower()

    completion = revision["session_revision_completion"]
    recomputation = revision["session_proposition_ledger"]["recomputation"]
    assert completion["owner_result_ready"] is True
    assert completion["selected_owner_id"] == "current_session_facts"
    assert completion["candidate_receipts"][0]["revision_input_accounted_for"] is True
    assert recomputation["state"] == "completed"
    assert recomputation["maximum_owner_recompute_passes"] == 1
    assert "gate now closes sooner" in revision["candidate_text"].lower()
    assert "corrected meaning" not in revision["candidate_text"].lower()
    assert "relevant part rather than resetting" not in revision["candidate_text"].lower()
    assert ": ," not in revision["candidate_text"]

    assert _operation(prediction, "prediction")["status"] == "completed"
    assert "cracks twice as often" in prediction["candidate_text"].lower()
    assert prediction["metacognition"]["recommended_action"] == "answer_now"
    for result in results:
        assert result["reviewed_memory_write_occurred"] is False
        assert result["conversational_memory_proposal_created"] is False
        _assert_locked(result)


def test_phase_nine_generalizes_gap_teaching_and_recall_to_a_new_term_and_question_shape(
    tmp_path,
):
    conn = _active_conn(tmp_path)
    gap = route_request(
        conn,
        "selene_chat.send",
        {"text": "Could you tell me whether glimleaf already means anything here?"},
    )["result"]
    learned = route_request(
        conn,
        "selene_chat.send",
        {
            "session_id": gap["session_id"],
            "text": (
                "Sure. A glimleaf means a folded blue marker used to flag a trail "
                "for one afternoon."
            ),
        },
    )["result"]
    recalled = route_request(
        conn,
        "selene_chat.send",
        {
            "session_id": gap["session_id"],
            "text": "In your own words, what does glimleaf mean?",
        },
    )["result"]

    assert gap["learning_gap_invitation"]["offered"] is True
    assert gap["learning_gap_invitation"]["owner_eligibility"][
        "all_answer_paths_exhausted"
    ] is True
    assert learned["conversational_teaching"]["status"] == (
        "conversational_teaching_integrated"
    )
    assert learned["conversational_teaching"]["knowledge_activated"] is True
    assert learned["conversational_teaching"]["explicit_aleks_approval"] is True
    assert recalled["learning_gap_invitation"]["offered"] is False
    assert "folded blue marker" in recalled["candidate_text"].lower()
    assert "teach me" not in recalled["candidate_text"].lower()
    assert recalled["reviewed_memory_write_occurred"] is False
    assert recalled["conversational_memory_proposal_created"] is False
    _assert_locked(gap)
    _assert_locked(learned)
    _assert_locked(recalled)


def test_phase_nine_generalizes_mixed_participation_without_claiming_completion_early(
    tmp_path,
):
    conn = _activated_conn(tmp_path)
    opening = route_request(
        conn,
        "selene_chat.send",
        {
            "text": (
                "For the lantern table, we settled two things: keep the red lens "
                "near the map, and leave the spare wick in the drawer."
            )
        },
    )["result"]
    result = route_request(
        conn,
        "selene_chat.send",
        {
            "session_id": opening["session_id"],
            "text": (
                "Thanks, that helped. Recap those two settled points, add one tiny "
                "joke about the lantern, and then close without a question."
            ),
        },
    )["result"]

    operations = {
        item["operation"]: item for item in result["answer_operations"]["results"]
    }
    assert {"acknowledgement", "summary", "humor", "closure"}.issubset(operations)
    assert all(
        operations[name]["status"] == "completed"
        for name in ("acknowledgement", "summary", "humor", "closure")
    )
    assert result["response_coverage"]["all_required_addressed"] is True
    assert result["response_coverage"]["all_required_resolved"] is True
    visible = result["candidate_text"].lower()
    assert "red lens" in visible
    assert "spare wick" in visible
    assert "lantern" in visible
    assert "?" not in result["candidate_text"]
    assert "missing supporting information" not in visible
    assert "corrected meaning" not in visible
    assert result["reviewed_memory_write_occurred"] is False
    assert result["conversational_memory_proposal_created"] is False
    _assert_locked(result)
