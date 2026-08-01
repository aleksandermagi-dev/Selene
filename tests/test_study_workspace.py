from __future__ import annotations

import sqlite3

import pytest

from selene.comprehension_integration import propose_comprehension_concept
from selene.db import init_db
from selene.module_router import route_request
from selene.study_workspace import (
    answer_study_question,
    ask_study_question,
    start_study_session,
    study_workspace_status,
    update_study_session,
)


def _conn(tmp_path):
    conn = sqlite3.connect(tmp_path / "selene.db")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def _concept(conn, *, approved: bool = True) -> int:
    result = propose_comprehension_concept(
        conn,
        {
            "concept_key": f"study-test-equal-shares-{'approved' if approved else 'candidate'}",
            "title": "Equal shares",
            "domain": "mathematics.fractions",
            "material": "Equal fractional shares must have the same size.",
            "source_refs": ["curriculum:test:equal-shares"],
        },
    )
    concept_id = int(result["item"]["id"])
    if approved:
        conn.execute(
            """
            UPDATE selene_comprehension_concepts
            SET state = 'approved_knowledge_resource',
                review_status = 'approved_for_knowledge_use',
                retention_state = 'retained_reviewed_knowledge',
                chat_use_permission = 'available_as_knowledge_resource'
            WHERE id = ?
            """,
            (concept_id,),
        )
        conn.commit()
    return concept_id


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["training_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["hidden_retention_allowed"] is False


def test_study_workspace_uses_only_approved_knowledge_and_keeps_visible_evidence(tmp_path):
    conn = _conn(tmp_path)
    approved_id = _concept(conn)
    session = start_study_session(
        conn,
        {"title": "Fractions study", "focus": "Why equal size matters", "concept_ids": [approved_id]},
    )
    session_id = int(session["item"]["id"])
    reflected = update_study_session(
        conn,
        {
            "session_id": session_id,
            "current_understanding": "Fourth means one of four equal shares.",
            "connections": ["Equal shares connect division and fractions."],
            "uncertainties": ["How should an uneven drawing be described?"],
        },
    )

    assert reflected["item"]["current_understanding"].startswith("Fourth means")
    assert len(reflected["learning_evidence"]) == 2
    assert all(item["review_status"] == "descriptive_learning_evidence" for item in reflected["learning_evidence"])
    _assert_locked(reflected)

    unapproved_id = _concept(conn, approved=False)
    with pytest.raises(ValueError, match="approved"):
        start_study_session(conn, {"concept_ids": [unapproved_id]})


def test_aleks_answer_resolves_question_in_session_and_proposes_attributed_update(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _concept(conn)
    started = start_study_session(conn, {"concept_ids": [concept_id]})
    session_id = int(started["item"]["id"])
    asked = ask_study_question(
        conn,
        {
            "session_id": session_id,
            "concept_id": concept_id,
            "question_text": "Why must fourths be equal in size?",
            "formation_state": "ready",
        },
    )
    question_id = int(asked["questions"][0]["id"])
    answered = answer_study_question(
        conn,
        {
            "question_id": question_id,
            "answer": "Because the whole is divided into four shares of the same size; unequal pieces are not four equal shares.",
        },
    )

    question = answered["questions"][0]
    candidate = answered["teaching_update_candidate"]
    assert question["status"] == "answered_in_session"
    assert question["answered_by"] == "Aleks"
    assert answered["answer_use"]["usable_in_current_study_session"] is True
    assert answered["answer_use"]["durable_chat_use"] is False
    assert candidate["state"] == "proposed_understanding"
    assert candidate["chat_use_permission"] == "not_active_until_approved"
    assert "speaker:Aleks" in candidate["source_refs"]
    assert question["teaching_candidate_id"] == candidate["id"]
    _assert_locked(answered)


def test_question_without_words_is_supported_without_inventing_content(tmp_path):
    conn = _conn(tmp_path)
    concept_id = _concept(conn)
    session_id = int(start_study_session(conn, {"concept_ids": [concept_id]})["item"]["id"])
    result = ask_study_question(
        conn,
        {
            "session_id": session_id,
            "formation_state": "question_without_words",
            "uncertainty_context": "Something about equal size and the whole does not connect yet.",
        },
    )

    assert result["questions"][0]["question_text"] == ""
    assert result["questions"][0]["formation_state"] == "question_without_words"
    _assert_locked(result)


def test_study_routes_are_registered_and_status_is_selene_owned(tmp_path):
    conn = _conn(tmp_path)
    direct = study_workspace_status(conn)
    routed = route_request(conn, "study.status")["result"]

    assert direct["owner"] == "Selene"
    assert routed["status"] == "selene_study_workspace_ready"
    assert routed["study_is_cocoon"] is False
    _assert_locked(routed)
