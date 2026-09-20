from __future__ import annotations

from selene.capability_self_assessment import (
    build_capability_self_assessment,
    capability_status_request_signal,
)
from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_capability_status_requires_selene_subject_status_and_question_shape():
    for prompt in (
        "What gaps are we missing to get you to 100%?",
        "What remains unfinished in your current system?",
        "What can't you do yet?",
        "Where does Selene's architecture still need work?",
    ):
        assert capability_status_request_signal(prompt)["requested"] is True

    for prompt in (
        "How are you?",
        "What gaps remain in this project?",
        "Why is the sky blue?",
        "Can you remember where we left off?",
        "What do you need?",
        "Are you missing Ranger?",
        "Are you ready to continue?",
        (
            "Now compare attendance alone with attendance plus wait time and feedback. "
            "Which is more useful, what is its limitation, and what would you report?"
        ),
        (
            "If Selene can repeat an idea fluently but cannot use it in a new example, "
            "what should we do next?"
        ),
    ):
        assert capability_status_request_signal(prompt)["requested"] is False


def test_capability_status_has_a_distinct_current_owner():
    decision = classify_chat_intent("What gaps are we missing to get you to 100%?")

    assert decision["intent"] == "capability_status"
    assert decision["primary_organ"] == "organ_maturity_ledger"
    assert decision["capability_status_requested"] is True
    assert decision["content_response_requested"] is True
    frame = decision["meaning_route"]["canonical_meaning_frame"]
    assert frame["academic_knowledge_posture"] == "hold_for_current_system_status"


def test_capability_self_assessment_is_read_only_current_and_identity_preserving(tmp_path):
    conn = _conn(tmp_path)
    before = conn.total_changes

    result = build_capability_self_assessment(
        conn,
        "What remains unfinished in your current system?",
    )

    assert result["status"] == "capability_self_assessment_ready"
    assert result["requested"] is True
    assert result["single_percentage_claimed"] is False
    assert result["availability_changes_identity"] is False
    assert {"perception", "audible_voice", "tendril_action", "embodiment"} <= set(
        result["unfinished_capability_keys"]
    )
    assert "not identity gaps" in result["response_seed"]
    assert result["writes_state"] is False
    assert result["memory_write_active"] is False
    assert conn.total_changes == before
    conn.close()


def test_non_status_question_does_not_read_or_answer_from_maturity_ledger(tmp_path):
    conn = _conn(tmp_path)

    result = build_capability_self_assessment(conn, "What gaps remain in the porch plan?")

    assert result["status"] == "capability_self_assessment_not_requested"
    assert result["requested"] is False
    assert result["response_seed"] == ""
    conn.close()
