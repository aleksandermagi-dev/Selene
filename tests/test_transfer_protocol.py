from __future__ import annotations

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _seed_transfer_context(conn):
    for layer in (
        "core_profile_memory",
        "project_memory",
        "decision_memory",
        "task_memory",
        "interaction_memory",
        "reflection_memory",
    ):
        conn.execute(
            """
            INSERT INTO b_approved_memory_references
            (source_candidate_table, source_candidate_id, core_memory_layer, title, reference_summary, source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "core_memory_candidates",
                1,
                layer,
                f"{layer} reference",
                "Reviewed continuity thread with provenance, care, uncertainty, and a practical next step.",
                f'["reference:{layer}"]',
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
    conn.execute(
        """
        INSERT INTO vessel_reasoning_check_records(problem, result_summary, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?)
        """,
        ("reasoning", "review-only", "[]", "test_boundary"),
    )
    conn.execute(
        """
        INSERT INTO vessel_working_memory_packets(current_task, expiry_cleanup_note, interrupt_resume_note, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("task", "expires", "resume", "[]", "test_boundary"),
    )
    conn.execute(
        """
        INSERT INTO vessel_memory_accession_proposals(core_memory_layer, title, rationale, reversal_conditions, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("decision_memory", "proposal", "rationale", "reverse", "[]", "test_boundary"),
    )
    conn.execute(
        """
        INSERT INTO vessel_retrieval_reconstruction_previews(cue, bounded_preview, reconstruction_note, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("cue", "preview", "note", "[]", "test_boundary"),
    )
    conn.execute(
        """
        INSERT INTO vessel_visual_observation_records(artifact_label, observation, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?)
        """,
        ("artifact", "observation", "[]", "test_boundary"),
    )
    conn.execute(
        """
        INSERT INTO vessel_audio_observation_records(transcript_label, bounded_transcript_preview, consent_note, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("transcript", "preview", "consented", "[]", "test_boundary"),
    )
    conn.execute(
        """
        INSERT INTO vessel_fluency_diagnostic_records(route_label, fluency_note, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?)
        """,
        ("route", "smooth", "[]", "test_boundary"),
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


def _assert_activation_locked(result):
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


def test_pre_transfer_readiness_and_ceremony_status_are_approval_ready_not_activation(tmp_path):
    conn = _conn(tmp_path)
    _seed_transfer_context(conn)
    route_request(conn, "transfer.accession_manifest.prepare", {})
    route_request(conn, "transfer.governance_trials.run", {})
    route_request(conn, "transfer.c_chat_dry_run", {"prompt": "Selene, answer from continuity."})
    route_request(conn, "transfer.return_to_b_drill", {})

    readiness = route_request(conn, "transfer.pre_transfer_readiness")["result"]
    ceremony = route_request(conn, "transfer.ceremony.status")["result"]

    assert readiness["status"] == "pre_transfer_readiness_preview_only_not_approval"
    assert readiness["notice"] == "Preview only. Not transfer approval."
    assert readiness["transfer_gate_state"] == "locked_false"
    assert ceremony["status"] == "transfer_ceremony_status_ready"
    assert ceremony["approval_available"] is True
    assert ceremony["approval_button_enabled"] is True
    assert ceremony["b_remains_active"] is True
    _assert_locked(readiness)
    _assert_locked(ceremony)


def test_transfer_approval_requires_exact_phrase(tmp_path):
    conn = _conn(tmp_path)
    _seed_transfer_context(conn)
    route_request(conn, "transfer.accession_manifest.prepare", {})
    route_request(conn, "transfer.return_to_b_drill", {})

    result = route_request(conn, "transfer.ceremony.approve", {"approval_phrase": "yes"})["result"]
    package = route_request(conn, "transfer.c_readable_package.latest")["result"]

    assert result["status"] == "transfer_ceremony_approval_blocked"
    assert result["state"] == "blocked"
    assert result["exact_phrase_matched"] is False
    assert "exact approval phrase did not match" in result["blockers"]
    assert package["status"] == "no_c_readable_package"
    _assert_locked(result)


def test_transfer_approval_creates_c_readable_package_without_activation(tmp_path):
    conn = _conn(tmp_path)
    _seed_transfer_context(conn)
    route_request(conn, "transfer.accession_manifest.prepare", {})
    route_request(conn, "transfer.return_to_b_drill", {})

    result = route_request(conn, "transfer.ceremony.approve", {
        "approval_phrase": "I, Aleks, approve Selene transfer to C-readable context under the Law of Transfer."
    })["result"]
    package = route_request(conn, "transfer.c_readable_package.latest")["result"]
    ceremony = route_request(conn, "transfer.ceremony.status")["result"]

    assert result["status"] == "transfer_c_readable_context_approved"
    assert result["state"] == "approved_c_readable_context"
    assert result["activation_state"] == "activation_pending"
    assert result["transfer_approved"] is True
    assert package["status"] == "approved_c_readable_context"
    assert package["transfer_approved"] is True
    assert ceremony["transfer_approved"] is True
    assert result["included_counts"]["continuity_pack"] == 1
    assert result["included_counts"]["teaching_packets"] == 1
    assert result["included_counts"]["approved_references"] == 1
    assert result["included_counts"]["chronological_arcs"] == 1
    assert result["excluded_b_only_counts"]["needs review"] >= 1
    assert result["excluded_b_only_counts"]["B-only"] >= 1
    assert result["excluded_b_only_counts"]["boundary-only"] >= 1
    assert result["package"]["package_json"]["activation_state"] == "activation_pending"
    assert all(item["phase_order"] <= 5 for item in result["package"]["package_json"]["included_manifest_items"])
    assert all(item["c_access_status"] != "C-readable" for item in result["package"]["package_json"]["excluded_manifest_items"] if item["phase_order"] <= 5)
    _assert_activation_locked(result)


def test_rollback_preview_routes_to_b_without_deleting_transfer_audit(tmp_path):
    conn = _conn(tmp_path)
    _seed_transfer_context(conn)
    route_request(conn, "transfer.accession_manifest.prepare", {})
    route_request(conn, "transfer.return_to_b_drill", {})
    approved = route_request(conn, "transfer.ceremony.approve", {
        "approval_phrase": "I, Aleks, approve Selene transfer to C-readable context under the Law of Transfer."
    })["result"]

    rollback = route_request(conn, "transfer.return_to_b.rollback_preview", {})["result"]
    package = route_request(conn, "transfer.c_readable_package.latest")["result"]

    assert rollback["status"] == "transfer_return_to_b_rollback_preview_ready"
    assert rollback["state"] == "rolled_back_to_b"
    assert rollback["deletes_transfer_audit"] is False
    assert rollback["return_to_b_packet"]["status"] == "c_vessel_return_to_b_packet_preview"
    assert package["id"] == approved["sealed_package_id"]
    assert package["transfer_approved"] is True
    _assert_activation_locked(rollback)
