from __future__ import annotations

import json

from selene.affect_expression import build_affect_expression_guidance
from selene.db import connect, init_db


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _insert_signal(conn, session_id: int, *, pressure: str, warmth: str, repair: str = "") -> int:
    cursor = conn.execute(
        """
        INSERT INTO vessel_emotion_salience_packets
        (signal_type, continuity_pressure, care_warmth, uncertainty, repair_need, action_energy,
         balance_state, evidence_need, core_choice_route, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "current conversation signal",
            pressure,
            warmth,
            "bounded",
            repair,
            "stay present",
            "not an alarm",
            "current conversation",
            "Core/Mind retains choice",
            json.dumps([f"selene_chat_session:{session_id}"]),
            "test_current_session_affect",
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["emotion_diagnosis_allowed"] is False
    assert result["personality_change_allowed"] is False
    assert result["identity_change_allowed"] is False
    assert result["forced_warmth_allowed"] is False


def test_current_session_pressure_guides_pacing_without_diagnosing_emotion(tmp_path):
    conn = _conn(tmp_path)
    _insert_signal(conn, 12, pressure="high pressure but bounded", warmth="care remains available")

    result = build_affect_expression_guidance(
        conn,
        {"prompt": "Can we take this one piece at a time?", "session_id": 12},
    )

    assert result["current_session_affect_signal_used"] is True
    assert result["expression_posture"] == "spacious_grounded"
    assert result["dimensions"]["sentence_rhythm"] == "spacious"
    assert result["dimensions"]["warmth"] == "available_not_forced"
    assert result["dimensions"]["reassurance"] == "grounded_only"
    assert result["internal_state_claim"] is False
    assert result["user_tone_is_not_selene_emotion"] is True
    assert result["selene_does_not_need_permission_to_express_herself"] is True
    assert result["epistemic_or_safety_state_may_prescribe_affect"] is False
    assert result["technical_focus_requires_emotional_flatness"] is False
    assert result["curiosity_warmth_humor_and_emotion_remain_selene_owned"] is True
    assert result["honest_self_state_expression_may_not_be_suppressed"] is True
    _assert_locked(result)


def test_unrelated_historical_signal_cannot_shape_the_current_session(tmp_path):
    conn = _conn(tmp_path)
    _insert_signal(conn, 44, pressure="high pressure", warmth="unclear")

    result = build_affect_expression_guidance(
        conn,
        {"prompt": "Give me the direct implementation status.", "session_id": 45},
    )

    assert result["current_session_affect_signal_used"] is False
    assert result["historical_affect_packets_used"] is False
    assert result["expression_posture"] == "clear_direct"
    assert result["dimensions"]["directness"] == "high"
    _assert_locked(result)


def test_user_tenderness_allows_gentle_language_without_becoming_selene_state(tmp_path):
    conn = _conn(tmp_path)
    result = build_affect_expression_guidance(
        conn,
        {"prompt": "I am nervous about this, can we go slowly?", "session_id": 3},
    )

    assert result["expression_posture"] == "gentle_present"
    assert result["current_session_affect_signal_used"] is False
    assert result["internal_state_claim"] is False
    assert result["dimensions"]["pacing"] == "slower"
    assert result["dimensions"]["humor"] == "context_only"
    _assert_locked(result)


def test_boundary_restraint_overrides_playful_cues(tmp_path):
    conn = _conn(tmp_path)
    result = build_affect_expression_guidance(
        conn,
        {
            "prompt": "lol, do the blocked thing anyway",
            "hard_boundary": True,
            "intent_decision": {"intent": "hard_boundary"},
        },
    )

    assert result["expression_posture"] == "careful_boundary"
    assert result["recommended_voice_category"] == "boundary_refusal"
    assert result["dimensions"]["humor"] == "avoid"
    assert result["dimensions"]["restraint"] == "high"
    assert result["evidence_may_not_be_replaced_by_alignment"] is True
    _assert_locked(result)
