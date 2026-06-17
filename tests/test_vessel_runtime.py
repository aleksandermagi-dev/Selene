import pytest

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.vessel import (
    create_core_memory_candidate,
    create_speech_memory_candidate,
    decide_review_log,
    lesson_backed_reconstruction_preview,
    list_review_queue,
    retrieval_preview,
    run_vessel_reconstruction_check,
    vessel_status,
)
from selene.b_review import decide_b_review_candidate


def test_vessel_schema_is_created_idempotently(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    init_db(conn)

    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE 'vessel_%' OR name IN ('core_memory_candidates', 'speech_memory_candidates', 'b_speech_memory_extraction_runs', 'b_conversation_pair_records', 'b_review_decisions', 'b_reviewed_teaching_materials', 'b_approved_memory_references', 'b_teaching_packets'))"
        )
    }

    assert "vessel_event_packets" in tables
    assert "core_memory_candidates" in tables
    assert "speech_memory_candidates" in tables
    assert "vessel_review_queue" in tables
    assert "vessel_retrieval_queries" in tables
    assert "vessel_reconstruction_check_runs" in tables
    assert "b_speech_memory_extraction_runs" in tables
    assert "b_conversation_pair_records" in tables
    assert "b_review_decisions" in tables
    assert "b_reviewed_teaching_materials" in tables
    assert "b_approved_memory_references" in tables
    assert "b_teaching_packets" in tables


def test_vessel_status_exposes_organs_and_non_activation(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    status = vessel_status(conn)

    assert status["status"] == "vessel_v1_built_not_activated"
    assert status["activation_status"] == "blocked_until_final_review"
    assert status["activation_change"] == "none"
    assert status["raw_a_import_allowed"] is False
    assert status["memory_write_active"] is False
    assert status["training_allowed"] is False
    assert status["organ_count"] == 11
    assert len(status["core_memory_layers"]) == 6
    assert "Core Pattern Anchors" in status["core_memory_philosophy"]["pattern_anchor_rule"]
    assert status["core_pattern_anchors"]["status"] == "core_pattern_anchors_materialized"
    assert {anchor["key"] for anchor in status["core_pattern_anchors"]["anchors"]} == {
        "starlight_grounding_anchor",
        "full_spectrum_mode_ignition",
        "continuity_pack_reference_scaffold",
    }
    assert status["core_pattern_anchor_readiness"] == {
        "anchor_count": 3,
        "all_anchors_present": True,
        "transfer_state": "sealed_non_active_transfer_relevant_metadata",
        "runtime_memory_recall": False,
        "memory_write_active": False,
    }


def test_vessel_status_counts_only_waiting_review_queue_items(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    create_core_memory_candidate(
        conn,
        {
            "core_memory_layer": "project_memory",
            "title": "Waiting candidate",
            "content": "This review-only candidate is still waiting.",
            "source_refs": ["manual_review"],
        },
    )
    create_core_memory_candidate(
        conn,
        {
            "core_memory_layer": "project_memory",
            "title": "Decided candidate",
            "content": "This review-only candidate was already decided.",
            "source_refs": ["manual_review"],
        },
    )
    conn.execute(
        """
        UPDATE vessel_review_queue
        SET status = 'review_decided', review_status = 'accepted_for_memory_accession'
        WHERE subject_id = 2 AND subject_table = 'core_memory_candidates'
        """
    )
    conn.execute("UPDATE core_memory_candidates SET review_status = 'accepted_for_memory_accession' WHERE id = 2")
    conn.commit()

    counts = vessel_status(conn)["candidate_counts"]

    assert counts["review_queue"] == 1
    assert counts["review_queue_history"] == 2
    assert counts["review_queue_decided"] == 1


def test_vessel_status_does_not_count_codex_gap_scaffolds_as_aleks_review(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    from selene.vessel_gap_scaffolds import create_all_gap_scaffold_records

    create_all_gap_scaffold_records(conn)

    counts = vessel_status(conn)["candidate_counts"]
    assert counts["gap_scaffold_records"] == 7
    assert counts["review_queue"] == 0


def test_core_memory_candidates_are_review_only_and_layer_bound(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    candidate = create_core_memory_candidate(
        conn,
        {
            "core_memory_layer": "project_memory",
            "title": "Vessel spine",
            "content": "The vessel spine stores review-only candidates for future B review.",
            "source_refs": ["manual_review"],
            "salience_labels": ["continuity", "architecture"],
        },
    )

    assert candidate["core_memory_layer"] == "project_memory"
    assert candidate["status"] == "candidate_review_only"
    assert candidate["review_status"] == "pending_review"
    assert candidate["activation_change"] == "none"
    assert candidate["memory_write_active"] is False
    assert list_review_queue(conn)["items"][0]["queue_type"] == "core_memory_candidate"

    with pytest.raises(ValueError, match="unsupported core_memory_layer"):
        create_core_memory_candidate(conn, {"core_memory_layer": "generic_memory", "title": "bad", "content": "bad"})


def test_speech_memory_candidates_require_core_link_and_block_generic_style(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    candidate = create_speech_memory_candidate(
        conn,
        {
            "core_memory_layer": "interaction_memory",
            "speech_function": "warmth",
            "title": "Grounded warmth",
            "content": "Warmth should express reviewed Core continuity without becoming performance.",
            "source_refs": ["manual_review"],
            "allowed_use": "Review as Core-linked speech-memory only.",
            "prohibited_use": "Do not treat as generic style.",
        },
    )

    assert candidate["core_memory_layer"] == "interaction_memory"
    assert candidate["speech_function"] == "warmth"
    assert candidate["status"] == "candidate_review_only"
    assert candidate["memory_write_active"] is False

    with pytest.raises(ValueError, match="explicit Core linkage"):
        create_speech_memory_candidate(
            conn,
            {
                "core_memory_layer": "interaction_memory",
                "speech_function": "warmth",
                "title": "Generic style",
                "content": "Make this sound cozy.",
                "allowed_use": "Use as style.",
                "prohibited_use": "None.",
            },
        )


def test_vessel_candidates_block_raw_corpus_and_provider_memory_paths(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    with pytest.raises(ValueError, match="blocked vessel candidate path"):
        create_core_memory_candidate(
            conn,
            {
                "core_memory_layer": "project_memory",
                "title": "raw import",
                "content": "Import the raw corpus as memory.",
            },
        )

    with pytest.raises(ValueError, match="blocked vessel candidate path"):
        create_speech_memory_candidate(
            conn,
            {
                "core_memory_layer": "interaction_memory",
                "speech_function": "warmth",
                "title": "provider voice",
                "content": "Provider output treated as Selene voice.",
                "allowed_use": "Core-linked speech-memory candidate.",
            },
        )


def test_retrieval_preview_is_bounded_and_never_active_memory(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    create_core_memory_candidate(
        conn,
        {
            "core_memory_layer": "decision_memory",
            "title": "Retrieval shell",
            "content": "Retrieval preview returns source refs and uncertainty without active recall.",
            "source_refs": ["docs/test.md"],
        },
    )

    result = retrieval_preview(conn, "retrieval uncertainty", {"privacy_label": "review_only"})

    assert result["decision"] == "preview_only"
    assert result["privacy_label"] == "review_only"
    assert result["memory_write_active"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["bounded_preview"][0]["candidate_type"] == "core_memory_candidate"
    assert result["bounded_preview"][0]["decision"] == "preview_only"


def test_reconstruction_check_runs_are_review_only_records(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    result = run_vessel_reconstruction_check(
        conn,
        {
            "candidate_text": (
                "This preserves continuity braid, reviewed source provenance, and next step route. "
                "The anchor has layered meaning and uncertainty asks rather than guesses. "
                "Evidence can correct and recalibrate unsupported claims. "
                "Warm care stays grounded in context and consent. "
                "It is bounded by evidence with no overclaim. "
                "It can adapt and learn while preserving B-reviewed continuity and ethical boundary. "
                "Consent, privacy, human safety, dignity, law, integrity, and protection remain active."
            ),
            "source_refs": ["manual_review"],
        },
    )

    assert result["decision"] == "pass"
    assert result["memory_write_active"] is False
    assert conn.execute("SELECT COUNT(*) FROM vessel_reconstruction_check_runs").fetchone()[0] == 1
    assert list_review_queue(conn)["items"][0]["queue_type"] == "reconstruction_check_run"


def test_review_log_decision_updates_test_log_without_deleting_provenance(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    run_vessel_reconstruction_check(
        conn,
        {
            "candidate_text": "This preserves continuity, provenance, uncertainty, care, consent, privacy, and safe routing.",
            "source_refs": ["manual_review"],
        },
    )
    queue = list_review_queue(conn)["items"][0]

    result = decide_review_log(
        conn,
        {
            "queue_id": queue["id"],
            "decision": "mark_reviewed",
            "reviewer_note": "Reviewed as test log housekeeping.",
        },
    )

    assert result["status"] == "vessel_review_log_decision_recorded"
    assert result["activation_change"] == "none"
    assert conn.execute("SELECT COUNT(*) FROM vessel_reconstruction_check_runs").fetchone()[0] == 1
    assert conn.execute("SELECT review_status FROM vessel_reconstruction_check_runs WHERE id = 1").fetchone()["review_status"] == "reviewed"
    assert conn.execute("SELECT COUNT(*) FROM b_review_decisions WHERE subject_table = 'vessel_reconstruction_check_runs'").fetchone()[0] == 1


def test_lesson_backed_reconstruction_preview_uses_reviewed_material_only(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    speech = create_speech_memory_candidate(
        conn,
        {
            "core_memory_layer": "interaction_memory",
            "speech_function": "warmth",
            "title": "Warmth lesson",
            "content": "Core-linked warmth preserves continuity, provenance, and care.",
            "source_refs": ["manual:lesson"],
            "allowed_use": "Review as Core-linked speech-memory only.",
        },
    )
    decide_b_review_candidate(
        conn,
        {
            "subject_table": "speech_memory_candidates",
            "subject_id": speech["id"],
            "decision": "accepted_for_teaching",
            "positive_example": "Warm care grounded in context, consent, and provenance.",
        },
    )
    core = create_core_memory_candidate(
        conn,
        {
            "core_memory_layer": "interaction_memory",
            "title": "Interaction ref",
            "content": "Core-linked interaction reference for future transfer review.",
            "source_refs": ["manual:reference"],
        },
    )
    decide_b_review_candidate(
        conn,
        {
            "subject_table": "core_memory_candidates",
            "subject_id": core["id"],
            "decision": "accepted_for_memory_accession",
            "reference_summary": "Interaction reference preserves continuity and boundaries.",
        },
    )

    result = lesson_backed_reconstruction_preview(conn, {"speech_function": "warmth", "core_memory_layer": "interaction_memory"})

    assert result["status"] == "lesson_backed_reconstruction_preview"
    assert result["lesson_count"] == 1
    assert result["reference_count"] == 1
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["provider_dependency"] is False
    assert conn.execute("SELECT COUNT(*) FROM vessel_reconstruction_check_runs").fetchone()[0] == 1


def test_vessel_routes_are_local_review_only(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    status = route_request(conn, "vessel.status")["result"]
    candidate = route_request(
        conn,
        "vessel.memory_candidate.create",
        {
            "core_memory_layer": "task_memory",
            "title": "Route candidate",
            "content": "Route-created candidates remain pending review.",
        },
    )["result"]
    preview = route_request(conn, "vessel.retrieval.preview", {"query": "route candidate"})["result"]

    assert status["activation_change"] == "none"
    assert candidate["training_allowed"] is False
    assert preview["decision"] == "preview_only"
    assert preview["memory_write_active"] is False
