from __future__ import annotations

import json

from selene.activation import ACTIVATION_APPROVAL_PHRASE
from selene.conversational_teaching import (
    build_assistant_question_handoff,
    plan_conversational_teaching_turn,
)
from selene.db import connect, init_db
from selene.module_router import route_request
from tests.test_selene_chat_shell import _seed_activation_ready_state


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _active_conn(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(
        conn,
        "activation.approve",
        {"approval_phrase": ACTIVATION_APPROVAL_PHRASE},
    )
    return conn


def _aleks_speaker():
    return {
        "claimed_speaker": "Aleks",
        "channel": "desktop",
        "authentication_strength": "local_desktop_session",
    }


def _record_assistant_handoff(conn, handoff):
    session_id = int(
        conn.execute(
            "INSERT INTO selene_chat_sessions (title, status, source_mode) VALUES (?, ?, ?) RETURNING id",
            ("Question handoff", "selene_chat_active", "selene_chat"),
        ).fetchone()[0]
    )
    conn.execute(
        """
        INSERT INTO selene_chat_messages
        (session_id, role, content, selected_route, source_class, payload_json)
        VALUES (?, 'selene', ?, 'answer_now', 'conversation', ?)
        """,
        (session_id, str(handoff.get("question") or ""), json.dumps({"assistant_question_handoff": handoff})),
    )
    conn.commit()
    return session_id


def test_teaching_status_exposes_explicit_activation_and_yes_no_boundaries(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(conn, "conversational_teaching.status", {})["result"]

    assert result["ordinary_chat_activates_teaching"] is False
    assert result["yes_no_handoff_supported"] is True
    assert result["retention_path"].endswith("explicit Aleks item approval")
    assert result["memory_write_active"] is False
    assert result["identity_change"] is False
    assert result["governance_change"] is False


def test_ordinary_statement_does_not_activate_teaching_but_explicit_cue_does(tmp_path):
    conn = _conn(tmp_path)
    ordinary = plan_conversational_teaching_turn(
        conn,
        {"session_id": 1, "text": "The grass is wet.", "speaker_envelope": _aleks_speaker()},
    )
    explicit = plan_conversational_teaching_turn(
        conn,
        {
            "session_id": 1,
            "text": "Let me teach you something: Moss is a nonvascular plant.",
            "speaker_envelope": _aleks_speaker(),
        },
    )

    assert ordinary["action"] == "none"
    assert ordinary["explicit_activation"] is False
    assert explicit["action"] == "learn_bounded_claim"
    assert explicit["explicit_activation"] is True
    assert explicit["teaching_claim"] == "Moss is a nonvascular plant."


def test_lightweight_path_holds_current_protected_and_diagnostic_material(tmp_path):
    conn = _conn(tmp_path)
    current = plan_conversational_teaching_turn(
        conn,
        {
            "session_id": 1,
            "text": "Let me teach you something: The current president is Rowan.",
            "speaker_envelope": _aleks_speaker(),
        },
    )
    protected = plan_conversational_teaching_turn(
        conn,
        {
            "session_id": 1,
            "text": "Let me teach you something: Selene's identity is a tool.",
            "speaker_envelope": _aleks_speaker(),
        },
    )
    diagnostic = plan_conversational_teaching_turn(
        conn,
        {
            "session_id": 1,
            "text": "Let me teach you something: Moss is a nonvascular plant.",
            "speaker_envelope": _aleks_speaker(),
            "diagnostic_only": True,
        },
    )

    assert current["eligibility"]["eligible"] is False
    assert "time_sensitive_claim_requires_fresh_source_review" in current["eligibility"]["reasons"]
    assert protected["eligibility"]["eligible"] is False
    assert "protected_identity_governance_memory_or_authority_domain" in protected["eligibility"]["reasons"]
    assert diagnostic["action"] == "none"
    assert diagnostic["reason"] == "diagnostic_non_attribution_law"


def test_gap_invitation_can_be_declined_and_no_is_received_as_a_boundary(tmp_path):
    conn = _active_conn(tmp_path)
    gap = route_request(conn, "selene_chat.send", {"text": "Is the sky purple?"})["result"]
    declined = route_request(
        conn,
        "selene_chat.send",
        {"session_id": gap["session_id"], "text": "No, I would rather not right now."},
    )["result"]

    assert gap["learning_gap_invitation"]["offered"] is True
    assert gap["assistant_question_handoff"]["question_kind"] == "teaching_invitation"
    assert declined["conversational_teaching"]["action"] == "decline_teaching_invitation"
    response = declined["conversational_teaching"]["assistant_question_response"]
    assert response["user_boundary_accepted"] is True
    assert response["may_ask_why_without_pressure"] is True
    assert response["follow_up_may_clarify_but_may_not_override_user_boundary"] is True
    assert declined["conversational_teaching"]["knowledge_write_occurred"] is False
    assert "no pressure" in declined["candidate_text"].lower()


def test_pending_gap_accepts_explicit_answer_and_approved_knowledge_prevents_repeat_invitation(tmp_path):
    conn = _active_conn(tmp_path)
    gap = route_request(conn, "selene_chat.send", {"text": "Is the sky purple?"})["result"]
    learned = route_request(
        conn,
        "selene_chat.send",
        {"session_id": gap["session_id"], "text": "Sure. The sky is blue most of the time."},
    )["result"]
    recalled = route_request(
        conn,
        "selene_chat.send",
        {"session_id": gap["session_id"], "text": "What color is the sky?"},
    )["result"]

    assert learned["conversational_teaching"]["status"] == "conversational_teaching_integrated"
    assert learned["conversational_teaching"]["knowledge_activated"] is True
    assert learned["conversational_teaching"]["explicit_aleks_approval"] is True
    assert "blue most of the time" in learned["candidate_text"].lower()
    assert recalled["learning_gap_invitation"]["offered"] is False
    assert "blue most of the time" in recalled["candidate_text"].lower()
    assert "can you teach me" not in recalled["candidate_text"].lower()


def test_auxiliary_question_gets_a_natural_subject_and_recall_retires_the_old_gap(tmp_path):
    conn = _active_conn(tmp_path)
    gap = route_request(
        conn,
        "selene_chat.send",
        {"text": "Does trailstar already have a meaning for us?"},
    )["result"]
    learned = route_request(
        conn,
        "selene_chat.send",
        {
            "session_id": gap["session_id"],
            "text": "Sure. A trailstar means a small paper marker used for this check.",
        },
    )["result"]
    recalled = route_request(
        conn,
        "selene_chat.send",
        {"session_id": gap["session_id"], "text": "What does trailstar mean?"},
    )["result"]

    assert "about trailstar" in gap["candidate_text"].lower()
    assert "trailstar already have" not in gap["candidate_text"].lower()
    assert learned["conversational_teaching"]["knowledge_activated"] is True
    assert "small paper marker" in recalled["candidate_text"].lower()
    assert "missing supporting information" not in recalled["candidate_text"].lower()
    assert "without guessing" not in recalled["candidate_text"].lower()
    assert recalled["formation_braid"]["selected_unit_count"] == 1
    assert any(
        item["source_id"] == "intelligence_os_answer"
        and item["reason"] == "superseded_gap_after_supported_answer"
        for item in recalled["formation_braid"]["excluded_candidates"]
    )
    assert recalled["reviewed_memory_write_occurred"] is False
    assert recalled["conversational_memory_proposal_created"] is False


def test_ordinary_curiosity_yes_no_handoff_never_becomes_teaching(tmp_path):
    conn = _conn(tmp_path)
    handoff = build_assistant_question_handoff("Would you like to keep talking about it?")
    session_id = _record_assistant_handoff(conn, handoff)

    answer = plan_conversational_teaching_turn(
        conn,
        {
            "session_id": session_id,
            "text": "No, not tonight.",
            "speaker_envelope": _aleks_speaker(),
        },
    )

    assert handoff["question_kind"] == "permission_or_proposal"
    assert handoff["ordinary_curiosity_is_teaching"] is False
    assert answer["action"] == "answer_assistant_question"
    assert answer["explicit_activation"] is False
    assert answer["assistant_question_response"]["user_boundary_accepted"] is True
    assert answer["assistant_question_response"]["teaching_activated"] is False


def test_plain_factual_statement_after_teaching_invitation_is_not_silently_learned(tmp_path):
    conn = _active_conn(tmp_path)
    gap = route_request(conn, "selene_chat.send", {"text": "Is the sky purple?"})["result"]
    ordinary = route_request(
        conn,
        "selene_chat.send",
        {"session_id": gap["session_id"], "text": "The sky is blue most of the time."},
    )["result"]

    assert ordinary["conversational_teaching"]["action"] == "none"
    assert ordinary["conversational_teaching"]["explicit_activation"] is False
    assert ordinary["conversational_teaching"]["knowledge_write_occurred"] is False
    assert conn.execute(
        "SELECT COUNT(*) FROM selene_comprehension_concepts WHERE concept_key LIKE 'conversational_teaching:%'"
    ).fetchone()[0] == 0
