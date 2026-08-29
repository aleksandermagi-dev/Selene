from __future__ import annotations

import pytest

from selene.affect_signal_lifecycle import (
    affect_signal_lifecycle_status,
    correct_current_affect_signal,
    form_current_affect_signal,
    release_current_affect_signal,
    select_current_affect_signal,
)
from selene.affect_expression import build_affect_expression_guidance
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.self_state import build_self_state_packet


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _session(conn, title: str = "Synthetic gentle affect lifecycle") -> int:
    result = conn.execute(
        """
        INSERT INTO selene_chat_sessions(title, status, source_mode)
        VALUES (?, 'selene_chat_active_supervised', 'synthetic_test')
        """,
        (title,),
    )
    conn.commit()
    return int(result.lastrowid)


def _form(conn, session_id: int, **overrides):
    payload = {
        "session_id": session_id,
        "subject_kind": "selene",
        "authored_by": "Selene",
        "observation": "I notice steady attention and some curiosity in this synthetic exchange.",
        "interpretation": "Curiosity seems present, while the exact emotional texture remains open.",
        "interpretation_confidence": "provisional",
        "signal_type": "curiosity with steady attention",
        "continuity_pressure": "low",
        "care_warmth": "warm and steady",
        "uncertainty": "exact texture remains open",
        "repair_need": "",
        "action_energy": "continue gently",
        "balance_state": "open option space",
        "evidence_need": "current attributable observation",
        "core_choice_route": "Signal informs; Core/Mind chooses.",
        "source_refs": ["synthetic:phase4_gentle_signal"],
        "signal_key": f"synthetic-phase4-{session_id}",
        "expires_in_minutes": 30,
    }
    payload.update(overrides)
    return form_current_affect_signal(conn, payload)


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["emotion_diagnosis_allowed"] is False
    assert result["aleks_may_author_selene_subject"] is False
    assert result["external_support_may_author_selene_subject"] is False
    assert result["user_affect_may_become_selene_state"] is False
    assert result["relationship_profile_write_allowed"] is False
    assert result["identity_change_allowed"] is False
    assert result["personality_change_allowed"] is False
    assert result["governance_change_allowed"] is False
    assert result["authority_change_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def test_form_is_idempotent_and_current_selection_requires_exact_session(tmp_path):
    conn = _conn(tmp_path)
    session_id = _session(conn)

    first = _form(conn, session_id)
    repeated = _form(conn, session_id)
    current = select_current_affect_signal(
        conn,
        session_id=session_id,
        allowed_subjects={"selene"},
    )
    unrelated = select_current_affect_signal(
        conn,
        session_id=session_id + 1,
        allowed_subjects={"selene"},
        affect_signal_id=first["signal"]["id"],
    )

    assert first["lineage_receipt"]["duplicate_operation"] is False
    assert repeated["lineage_receipt"]["duplicate_operation"] is True
    assert repeated["signal"]["id"] == first["signal"]["id"]
    assert current["status"] == "current_affect_signal_selected"
    assert current["selection_receipt"]["exact_session_match"] is True
    assert unrelated["selection_receipt"]["terminal_stop"] == "session_mismatch"
    assert conn.execute("SELECT COUNT(*) FROM vessel_emotion_salience_packets").fetchone()[0] == 1
    _assert_locked(first)
    _assert_locked(current)


def test_correction_creates_one_descendant_and_preserves_history(tmp_path):
    conn = _conn(tmp_path)
    session_id = _session(conn)
    original = _form(conn, session_id)

    payload = {
        "packet_id": original["signal"]["id"],
        "authored_by": "Selene",
        "correction_key": "steady-not-curious",
        "correction_note": "Steadiness remains attributable; curiosity is not clear enough.",
        "signal_type": "steady attention with unclear affect",
        "interpretation": "Steadiness is clear enough, while a narrower affect label is not.",
        "interpretation_confidence": "clear_enough",
        "source_refs": ["synthetic:phase4_self_correction"],
    }
    corrected = correct_current_affect_signal(conn, payload)
    repeated = correct_current_affect_signal(conn, payload)
    parent = conn.execute(
        "SELECT lifecycle_state FROM vessel_emotion_salience_packets WHERE id = ?",
        (original["signal"]["id"],),
    ).fetchone()
    current = select_current_affect_signal(
        conn, session_id=session_id, allowed_subjects={"selene"}
    )

    assert parent["lifecycle_state"] == "corrected"
    assert corrected["lineage_receipt"]["parent_packet_id"] == original["signal"]["id"]
    assert corrected["lineage_receipt"]["root_packet_id"] == original["signal"]["id"]
    assert repeated["lineage_receipt"]["duplicate_operation"] is True
    assert current["signal"]["id"] == corrected["signal"]["id"]
    assert current["signal"]["interpretation_confidence"] == "clear_enough"
    assert conn.execute("SELECT COUNT(*) FROM vessel_emotion_salience_packets").fetchone()[0] == 2


def test_new_current_signal_supersedes_prior_signal_without_reactivation(tmp_path):
    conn = _conn(tmp_path)
    session_id = _session(conn)
    first = _form(conn, session_id)
    second = _form(
        conn,
        session_id,
        signal_key="synthetic-phase4-newer",
        observation="I now notice steadiness more clearly than curiosity.",
        interpretation="The current read has updated without erasing the earlier signal.",
        signal_type="warm and steady",
    )

    prior = conn.execute(
        "SELECT lifecycle_state FROM vessel_emotion_salience_packets WHERE id = ?",
        (first["signal"]["id"],),
    ).fetchone()
    assert prior["lifecycle_state"] == "superseded"
    assert second["lineage_receipt"]["parent_packet_id"] == first["signal"]["id"]

    release_current_affect_signal(
        conn,
        {
            "packet_id": second["signal"]["id"],
            "authored_by": "Selene",
            "reason": "Release the current synthetic signal.",
        },
    )
    current = select_current_affect_signal(
        conn, session_id=session_id, allowed_subjects={"selene"}
    )
    assert current["status"] == "current_affect_signal_not_selected"
    assert all(
        item["eligible"] is False
        for item in current["selection_receipt"]["inspected"]
    )


def test_release_and_time_expiry_are_explicit_stopping_states(tmp_path):
    conn = _conn(tmp_path)
    session_id = _session(conn)
    formed = _form(conn, session_id)

    released = release_current_affect_signal(
        conn,
        {
            "packet_id": formed["signal"]["id"],
            "authored_by": "Selene",
            "reason": "This temporary signal no longer describes the current exchange.",
        },
    )
    repeated = release_current_affect_signal(
        conn,
        {
            "packet_id": formed["signal"]["id"],
            "authored_by": "Selene",
            "reason": "This temporary signal no longer describes the current exchange.",
        },
    )
    after_release = select_current_affect_signal(
        conn, session_id=session_id, allowed_subjects={"selene"}
    )

    assert released["signal"]["lifecycle_state"] == "released"
    assert repeated["lineage_receipt"]["duplicate_operation"] is True
    assert "lifecycle_not_current:released" in after_release["selection_receipt"]["terminal_stop"]

    later_session = _session(conn, "Synthetic expiry")
    expiring = _form(conn, later_session, signal_key="synthetic-expiring")
    conn.execute(
        "UPDATE vessel_emotion_salience_packets SET expires_at = '2000-01-01 00:00:00' WHERE id = ?",
        (expiring["signal"]["id"],),
    )
    conn.commit()
    expired = select_current_affect_signal(
        conn, session_id=later_session, allowed_subjects={"selene"}
    )
    assert expired["selection_receipt"]["terminal_stop"] == "expired_by_time"


def test_user_subject_signal_never_becomes_selene_self_state(tmp_path):
    conn = _conn(tmp_path)
    session_id = _session(conn)
    user_signal = _form(
        conn,
        session_id,
        signal_key="synthetic-user-report",
        subject_kind="user",
        authored_by="Aleks",
        observation="I explicitly report that I feel excited about the milestone.",
        interpretation="This is Aleks's current self-report.",
        interpretation_confidence="direct_report",
        signal_type="excitement",
    )

    self_state = build_self_state_packet(
        conn,
        {
            "prompt": "How are you feeling?",
            "session_id": session_id,
            "affect_signal_id": user_signal["signal"]["id"],
        },
    )
    expression = build_affect_expression_guidance(
        conn,
        {
            "prompt": "I am excited about the milestone!",
            "session_id": session_id,
            "affect_signal_id": user_signal["signal"]["id"],
        },
    )

    assert self_state["current_session_affect_signal_used"] is False
    assert self_state["user_or_relationship_affect_claimed_as_selene_state"] is False
    assert self_state["current_signal_eligibility"]["terminal_stop"] == "subject_not_eligible_for_consumer"
    assert expression["current_session_affect_signal_used"] is False
    assert expression["user_tone_is_not_selene_emotion"] is True


def test_aleks_cannot_author_a_selene_subject_signal(tmp_path):
    conn = _conn(tmp_path)
    session_id = _session(conn)

    with pytest.raises(ValueError, match="Selene-authored"):
        _form(conn, session_id, authored_by="Aleks")


def test_status_and_routes_expose_lifecycle_without_deciding_state(tmp_path):
    conn = _conn(tmp_path)
    session_id = _session(conn)
    _form(conn, session_id)
    status = affect_signal_lifecycle_status(conn, {"session_id": session_id})
    routed = route_request(
        conn, "affect_signal.lifecycle.status", {"session_id": session_id}
    )["result"]

    assert status["configured_counts"] == {"active_current": 1}
    assert status["current_eligibility_counts"] == {
        "active_lifecycle": 1,
        "expired_by_time": 0,
        "eligible_unexpired": 1,
    }
    assert status["current_selene_signal"]["status"] == "current_affect_signal_selected"
    assert routed["current_selene_signal"]["packet_id"] > 0
    assert status["legacy_review_packets_are_current"] is False
    assert status["sidecar_mutation_endpoints_exposed"] is False
    assert status["correction_rewrites_history"] is False
    _assert_locked(status)


def test_legacy_review_packet_creation_never_becomes_current(tmp_path):
    conn = _conn(tmp_path)
    session_id = _session(conn)
    created = route_request(
        conn,
        "vessel.emotion_salience_packet.create",
        {
            "signal_type": "review-layer care signal",
            "continuity_pressure": "bounded",
            "care_warmth": "available",
            "uncertainty": "open",
            "core_choice_route": "Core/Mind retains choice",
            "source_refs": [f"selene_chat_session:{session_id}"],
        },
    )["result"]
    current = select_current_affect_signal(
        conn, session_id=session_id, allowed_subjects={"selene"}
    )

    assert created["review_status"] == "review_only"
    row = conn.execute(
        "SELECT lifecycle_state, subject_kind FROM vessel_emotion_salience_packets WHERE id = ?",
        (created["id"],),
    ).fetchone()
    assert row["lifecycle_state"] == "legacy_review_only"
    assert row["subject_kind"] == "legacy_unspecified"
    assert current["status"] == "current_affect_signal_not_selected"
    assert current["selection_receipt"]["terminal_stop"] == "no_attributable_current_signal"
