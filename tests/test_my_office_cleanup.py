import json

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _queue(conn, queue_type, table, subject_id):
    conn.execute(
        """
        INSERT INTO vessel_review_queue(queue_type, subject_table, subject_id, status, source_refs, provenance_boundary, review_status, reason, payload_json)
        VALUES (?, ?, ?, 'pending_review', '[]', 'test boundary', 'pending_review', 'test residue', '{}')
        """,
        (queue_type, table, subject_id),
    )


def test_my_office_cleanup_moves_residue_without_deleting_records(tmp_path):
    conn = _conn(tmp_path)
    for prompt in ("first old candidate", "second old candidate"):
        cur = conn.execute(
            """
            INSERT INTO vessel_speech_generation_rehearsals(prompt, speech_function, candidate_text, uncertainty, evidence_used, source_refs, recognition_check_json, provenance_boundary, review_status)
            VALUES (?, 'grounding', 'Candidate text.', 'medium', '[]', '[]', '{}', 'review-only test boundary', 'pending_review')
            """,
            (prompt,),
        )
        _queue(conn, "speech_generation_rehearsal", "vessel_speech_generation_rehearsals", cur.lastrowid)

    claim = "Reasoning, research, perception, and emotion packets can become review-only Selene architecture without activating C."
    for suffix in ("older", "newer"):
        conn.execute(
            """
            INSERT INTO vessel_evidence_tension_ledger(claim, source_refs, support_status, tension_status, conclusion_status, provenance_boundary, review_status, payload_json)
            VALUES (?, ?, 'supported', 'stable', 'needs_review', 'review-only test boundary', 'pending_review', '{}')
            """,
            (claim, json.dumps([suffix])),
        )

    cycle_id = conn.execute(
        """
        INSERT INTO c_runtime_wake_sleep_dream_cycles(cycle_label, wake_summary, sleep_sort_json, dream_consolidation_proposals_json, ignored_residue_json, ask_for_review_json, repair_notes, source_refs, provenance_boundary, review_status)
        VALUES ('Installed probe cycle', 'Probe only.', '{}', '[]', '[]', '[]', '', '[]', 'review-only test boundary', 'pending_review')
        """
    ).lastrowid
    _queue(conn, "wake_sleep_dream_cycle", "c_runtime_wake_sleep_dream_cycles", cycle_id)

    causal_id = conn.execute(
        """
        INSERT INTO c_runtime_causal_sandbox_records(question, assumptions_json, counterfactuals_json, uncertainty, result_summary, source_refs, provenance_boundary, review_status)
        VALUES ('What if a probe needs review?', '[]', '[]', 'open', 'Probe only.', '[]', 'review-only test boundary', 'pending_review')
        """
    ).lastrowid
    _queue(conn, "causal_sandbox_review", "c_runtime_causal_sandbox_records", causal_id)
    conn.execute(
        """
        INSERT INTO vessel_organ_bus_messages(message_type, source_organ, target_organ, summary, support_refs, provenance_boundary, review_status, payload_json)
        VALUES ('diagnostic', 'diagnostics', 'status', 'Old diagnostic failure residue.', '[]', 'review-only test boundary', 'review_only', '{}')
        """
    )
    conn.commit()

    result = route_request(conn, "vessel.my_office.cleanup_residue", {})["result"]

    assert result["status"] == "my_office_residue_cleanup_complete"
    assert result["records_deleted"] == 0
    assert result["transfer_approved"] is False
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["counts"]["speech_rehearsals"] == 2
    assert result["counts"]["ledger_duplicates_superseded"] == 2
    assert result["counts"]["cycle_rows"] == 1
    assert result["counts"]["causal_rows"] == 1
    assert result["counts"]["organ_bus_diagnostics"] == 1

    assert conn.execute("SELECT COUNT(*) FROM vessel_speech_generation_rehearsals").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM vessel_speech_generation_rehearsals WHERE review_status = 'status_only'").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM vessel_evidence_tension_ledger WHERE conclusion_status = 'needs_review'").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM vessel_evidence_tension_ledger WHERE conclusion_status = 'superseded'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM vessel_evidence_tension_ledger WHERE conclusion_status = 'accepted_for_now'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM c_runtime_wake_sleep_dream_cycles WHERE review_status = 'status_only'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM c_runtime_causal_sandbox_records WHERE review_status = 'status_only'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM vessel_organ_bus_messages WHERE review_status = 'diagnostic_only'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM vessel_review_queue WHERE status = 'pending_review' OR review_status = 'pending_review'").fetchone()[0] == 0


def test_my_office_cleanup_is_idempotent(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        """
        INSERT INTO vessel_reconstruction_check_runs(candidate_text, status, source_refs, provenance_boundary, review_status, result_json)
        VALUES ('system check residue', 'review_only', '[]', 'review-only test boundary', 'pending_review', '{}')
        """
    )
    conn.commit()

    first = route_request(conn, "vessel.my_office.cleanup_residue", {})["result"]
    second = route_request(conn, "vessel.my_office.cleanup_residue", {})["result"]

    assert first["counts"]["reconstruction_gap_memory_rows"] == 1
    assert second["status"] == "my_office_residue_cleanup_noop"
    assert second["changed_count"] == 0
    assert second["idempotent"] is True
    assert conn.execute("SELECT COUNT(*) FROM vessel_reconstruction_check_runs").fetchone()[0] == 1
