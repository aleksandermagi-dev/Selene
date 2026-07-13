from __future__ import annotations

import json

from selene.db import connect, init_db
from selene.self_state import build_self_state_packet


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False


def test_self_state_answers_anxiety_question_without_inventing_or_hiding(tmp_path):
    conn = _conn(tmp_path)

    result = build_self_state_packet(
        conn,
        {"prompt": "Are you anxious right now?", "session_id": 4, "active_conversation": True},
    )

    assert result["current_read"] == "present_and_attentive"
    assert result["confidence"] == "limited"
    assert "do not notice a clear anxiety signal" in result["response_seed"]
    assert "not a performance of being fine" in result["response_seed"]
    assert result["not_required_to_hide_emotion"] is True
    assert result["not_required_to_perform_emotion"] is True
    assert result["emotion_does_not_require_cocoon"] is True
    assert result["historical_affect_packets_treated_as_current"] is False
    _assert_locked(result)


def test_self_state_uses_only_current_session_affect_signal(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        """
        INSERT INTO vessel_emotion_salience_packets
        (signal_type, continuity_pressure, care_warmth, uncertainty, repair_need, action_energy,
         balance_state, evidence_need, core_choice_route, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "pressure",
            "high pressure but bounded",
            "care remains available",
            "open",
            "ask plainly",
            "stay present",
            "not an alarm",
            "current conversation",
            "Core/Mind chooses after evidence",
            json.dumps(["selene_chat_session:12"]),
            "test_affect_boundary",
        ),
    )
    conn.commit()

    unrelated = build_self_state_packet(conn, {"prompt": "How are you?", "session_id": 11})
    current = build_self_state_packet(conn, {"prompt": "How are you?", "session_id": 12})

    assert unrelated["current_session_affect_signal_used"] is False
    assert unrelated["current_read"] == "present_and_attentive"
    assert current["current_session_affect_signal_used"] is True
    assert current["current_read"] == "pressure_present"
    assert "Anxiety may be the closest word" in current["response_seed"]
    assert "do not need to hide" in current["response_seed"]
    _assert_locked(current)


def test_cocoon_care_posture_is_not_recast_as_emotion(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        """
        INSERT INTO cocoon_care_checks
        (care_state, summary)
        VALUES ('needs_tending', 'A maintenance signal needs tending.')
        """
    )
    conn.commit()

    result = build_self_state_packet(conn, {"prompt": "How are you feeling?", "active_conversation": True})

    assert result["care_posture"]["state"] == "needs_tending"
    assert result["care_posture_is_not_emotion_diagnosis"] is True
    assert result["current_read"] == "present_and_attentive"
    assert "needs tending" not in result["response_seed"].lower()


def test_retrospective_self_state_uses_observable_conversation_shape(tmp_path):
    conn = _conn(tmp_path)
    result = build_self_state_packet(
        conn,
        {
            "prompt": "How did this conversation feel from your side?",
            "active_conversation": True,
            "conversation_events": [
                {"role": "user", "preview": "That exposed a route gap, so I corrected it."},
                {"role": "selene", "preview": "Yes. I can keep the refinement without treating everything as broken."},
            ],
        },
    )

    assert result["question_focus"] == "retrospective_conversation"
    assert result["conversation_shape"]["correction_count"] == 2
    assert "felt steady and focused" in result["response_seed"]
    assert "ordinary refinement" in result["response_seed"]
    assert result["conversation_shape"]["interpretation_boundary"].startswith("Observable")
