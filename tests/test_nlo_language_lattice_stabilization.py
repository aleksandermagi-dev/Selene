from __future__ import annotations

import hashlib
import json

from scripts.nlo_language_lattice_stabilization import (
    inspect_existing_nlo_records,
    run_language_lattice_stabilization,
)
from selene.db import connect, init_db


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_v32_stabilization_matrix_passes_without_writes_or_live_conversation(tmp_path):
    db_path = tmp_path / "matrix.sqlite3"
    conn = connect(db_path)
    init_db(conn)
    changes_before = conn.total_changes

    report = run_language_lattice_stabilization(conn)

    assert report["status"] == "nlo_language_lattice_stabilization_complete"
    assert report["nlo_version"] == "v32_human_conversational_realization"
    assert report["ok"] is True
    assert report["case_count"] == 7
    assert report["passed_case_count"] == 7
    assert report["failed_case_count"] == 0
    assert report["findings"] == []
    assert report["temporary_run_read_only_after_initialization"] is True
    assert conn.total_changes == changes_before
    assert report["configured_database_write"] is False
    assert report["live_conversation_used"] is False
    assert report["memory_write_active"] is False
    assert report["identity_change"] is False
    assert report["governance_change"] is False
    assert report["training_allowed"] is False
    assert report["hidden_chain_of_thought_exposed"] is False
    assert all(item["passed"] is True for item in report["cases"])
    assert all(item["candidate_or_chat_text_returned"] is False for item in report["cases"])

    conn.close()


def test_existing_record_inspection_is_metadata_only_and_byte_for_byte_read_only(tmp_path):
    db_path = tmp_path / "existing.sqlite3"
    conn = connect(db_path)
    init_db(conn)
    conn.execute(
        """
        INSERT INTO native_language_runs
        (mode, status, prompt, communicative_intent, candidate_text,
         meaning_packet_json, discourse_plan_json, revision_json, source_refs,
         provenance_boundary, review_destination, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "responsive",
            "native_language_response_realized",
            "PRIVATE SYNTHETIC PROMPT",
            "reasoned_answer",
            "PRIVATE SYNTHETIC CANDIDATE",
            "{}",
            "{}",
            json.dumps({"passed": True}),
            "[]",
            "synthetic:test",
            "Status",
            "status_only",
            json.dumps({"version": "v32_human_conversational_realization"}),
        ),
    )
    conn.commit()
    conn.close()
    before = _digest(db_path)

    report = inspect_existing_nlo_records(db_path)

    after = _digest(db_path)
    assert before == after
    assert report["status"] == "configured_nlo_record_metadata_inspected_read_only"
    assert report["record_count"] == 1
    assert report["current_v32_record_count"] == 1
    assert report["applicability"] == "current_v32_records_available"
    assert report["content_read_into_report"] is False
    assert report["prompt_or_candidate_text_returned"] is False
    assert report["database_open_mode"] == "read_only_query_only"
    assert "PRIVATE SYNTHETIC PROMPT" not in json.dumps(report)
    assert "PRIVATE SYNTHETIC CANDIDATE" not in json.dumps(report)
    assert report["configured_database_write"] is False


def test_existing_record_inspection_marks_pre_v32_history_as_non_grading(tmp_path):
    db_path = tmp_path / "historical.sqlite3"
    conn = connect(db_path)
    init_db(conn)
    conn.execute(
        """
        INSERT INTO native_language_runs
        (mode, status, prompt, communicative_intent, candidate_text,
         meaning_packet_json, discourse_plan_json, revision_json, source_refs,
         provenance_boundary, review_destination, review_status, payload_json)
        VALUES ('responsive', 'native_language_response_realized', '',
                'direct_answer', 'synthetic', '{}', '{}', '{"passed": true}',
                '[]', 'synthetic:test', 'Status', 'status_only', ?)
        """,
        (json.dumps({"version": "v24_contextual_composition_and_modulation"}),),
    )
    conn.commit()
    conn.close()

    report = inspect_existing_nlo_records(db_path)

    assert report["current_v32_record_count"] == 0
    assert report["applicability"] == "historical_records_predate_v32_do_not_grade_current_lattice"
