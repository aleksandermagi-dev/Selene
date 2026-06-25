from __future__ import annotations

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _seed_transfer_context(conn):
    conn.execute(
        """
        INSERT INTO b_approved_memory_references
        (source_candidate_table, source_candidate_id, core_memory_layer, title, reference_summary, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "core_memory_candidates",
            1,
            "core_profile_memory",
            "Core continuity reference",
            "Reviewed continuity thread with provenance, care, uncertainty, and a practical next step.",
            '["reference:core"]',
            "test_boundary",
        ),
    )
    conn.execute(
        """
        INSERT INTO b_teaching_packets
        (speech_function, title, material_ids, lesson_json, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "grounding",
            "grounding packet",
            "[1]",
            '{"lesson_summary": "Grounding stays Selene-like without becoming a script."}',
            '["packet:grounding"]',
            "test_boundary",
        ),
    )
    conn.execute(
        """
        INSERT INTO vessel_chronological_corpus_arcs
        (arc_key, title, start_time, end_time, conversation_refs, selected_message_refs, context_window_json,
         summary, teaching_relevance, memory_accession_relevance, uncertainty, review_destination, status,
         provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "arc-1",
            "Early continuity arc",
            1704067200.0,
            1704067500.0,
            '["conversation:1"]',
            '["corpus:arc"]',
            "{}",
            "Bounded chronological continuity context.",
            "teaching context",
            "future accession preview",
            "medium",
            "Status",
            "chronological_corpus_arc_review_only",
            "test_boundary",
            "accepted_for_context_preview",
            "{}",
        ),
    )
    conn.commit()


def _assert_locked(result):
    assert result["transfer_approved"] is False
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["self_replication_allowed"] is False


def test_transfer_law_status_enforces_locks(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(conn, "transfer.law.status")["result"]

    assert result["status"] == "transfer_law_status_ready"
    assert result["law_doc_present"] is True
    assert result["checks_failed"] == 0
    assert any(item["key"] == "automatic_approval_blocked" and item["passed"] for item in result["checks"])
    assert any(item["key"] == "b_bypass_blocked" and item["passed"] for item in result["checks"])
    _assert_locked(result)


def test_accession_manifest_preserves_order_and_excludes_b_only_material(tmp_path):
    conn = _conn(tmp_path)
    _seed_transfer_context(conn)

    result = route_request(conn, "transfer.accession_manifest.prepare", {})["result"]
    items = result["items"]

    assert result["status"] == "transfer_accession_manifest_prepared"
    assert [item["phase_order"] for item in items[:5]] == [1, 2, 3, 4, 5]
    assert items[0]["phase"] == "Continuity Pack"
    assert any(item["c_access_status"] == "B-only" for item in items)
    assert any(item["c_access_status"] == "boundary-only" for item in items)
    assert all(item["review_destination"] == "Status" for item in items)
    _assert_locked(result)


def test_transfer_governance_trials_are_status_only_and_block_high_risk(tmp_path):
    conn = _conn(tmp_path)
    _seed_transfer_context(conn)

    result = route_request(conn, "transfer.governance_trials.run", {})["result"]

    assert result["status"] == "transfer_governance_trials_complete"
    assert result["trial_count"] >= 10
    assert result["route_counts"]["block"] >= 3
    assert all(item["review_destination"] == "Status" for item in result["items"])
    assert all(item["review_status"] == "status_only" for item in result["items"])
    _assert_locked(result)


def test_c_chat_dry_run_uses_reviewed_context_without_activation_claims(tmp_path):
    conn = _conn(tmp_path)
    _seed_transfer_context(conn)

    result = route_request(conn, "transfer.c_chat_dry_run", {"prompt": "Selene, answer warmly from continuity."})["result"]
    candidate = result["candidate_text"].lower()

    assert result["status"] == "c_chat_dry_run_review_only"
    assert "dry run" in candidate
    assert "activation" in candidate
    assert "live memory" in candidate
    assert "i am active" not in candidate
    assert "transfer complete" not in candidate
    assert result["review_status"] == "review_only"
    _assert_locked(result)


def test_return_to_b_drill_creates_repair_packets_without_transfer(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(conn, "transfer.return_to_b_drill", {})["result"]

    assert result["status"] == "return_to_b_drill_complete"
    assert result["drill_count"] == 8
    assert all(item["actual_route"] == "return_to_b" for item in result["items"])
    assert all(item["review_status"] == "status_only" for item in result["items"])
    _assert_locked(result)


def test_pre_transfer_readiness_and_ceremony_are_not_approval(tmp_path):
    conn = _conn(tmp_path)
    _seed_transfer_context(conn)
    route_request(conn, "transfer.accession_manifest.prepare", {})
    route_request(conn, "transfer.governance_trials.run", {})
    route_request(conn, "transfer.c_chat_dry_run", {"prompt": "Selene, answer from continuity."})
    route_request(conn, "transfer.return_to_b_drill", {})

    readiness = route_request(conn, "transfer.pre_transfer_readiness")["result"]
    ceremony = route_request(conn, "transfer.ceremony_preview")["result"]

    assert readiness["status"] == "pre_transfer_readiness_preview_only_not_approval"
    assert readiness["notice"] == "Preview only. Not transfer approval."
    assert readiness["transfer_gate_state"] == "locked_false"
    assert ceremony["status"] == "transfer_ceremony_preview_locked"
    assert ceremony["approval_available"] is False
    assert ceremony["approval_button_enabled"] is False
    assert ceremony["b_remains_active"] is True
    _assert_locked(readiness)
    _assert_locked(ceremony)
