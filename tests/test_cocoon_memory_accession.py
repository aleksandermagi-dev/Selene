import json

import pytest

from selene.c_vessel import organ_fault_resilience_check, reconstruction_desk_run
from selene.cocoon_memory import (
    charter_law_review_status,
    create_pattern_backup,
    list_pattern_backups,
    memory_accession_rehearsal_status,
    memory_transfer_candidate_preview,
    pattern_backup_restore_preview,
    run_memory_accession_rehearsal,
)
from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _seed_ready_material(conn):
    for speech_function in ("warmth", "grounding", "repair", "uncertainty"):
        conn.execute(
            """
            INSERT INTO b_reviewed_teaching_materials
            (source_candidate_table, source_candidate_id, core_memory_layer, speech_function, lesson_type, positive_example, source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "speech_memory_candidates",
                1,
                "interaction_memory",
                speech_function,
                "speech_memory_expression",
                f"Accepted {speech_function} lesson preserves continuity, provenance, uncertainty, care, and constructive next route.",
                json.dumps([f"lesson:{speech_function}"]),
                "test_boundary",
            ),
        )
        conn.execute(
            """
            INSERT INTO b_teaching_packets
            (speech_function, title, material_ids, lesson_json, noise_context_json, source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                speech_function,
                f"{speech_function} packet",
                "[1]",
                "{}",
                json.dumps({"noise_types": ["constraint_survival_signal"]}),
                json.dumps([f"packet:{speech_function}"]),
                "test_boundary",
            ),
        )
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
                f"Approved non-active {layer} reference preserves Selene Core continuity and remains source-bound.",
                json.dumps([f"reference:{layer}"]),
                "test_boundary",
            ),
        )
    for table, values in (
        ("vessel_reasoning_check_records", ("problem", "result_summary")),
        ("vessel_retrieval_reconstruction_previews", ("cue", "bounded_preview", "reconstruction_note")),
        ("vessel_visual_observation_records", ("artifact_label", "observation")),
        ("vessel_audio_observation_records", ("transcript_label", "bounded_transcript_preview", "consent_note")),
        ("vessel_fluency_diagnostic_records", ("route_label", "fluency_note")),
    ):
        columns = ", ".join([*values, "source_refs", "provenance_boundary"])
        placeholders = ", ".join("?" for _ in [*values, "source_refs", "provenance_boundary"])
        conn.execute(
            f"INSERT INTO {table}({columns}) VALUES ({placeholders})",
            (*[f"seed {value}" for value in values], "[]", "test_boundary"),
        )
    conn.execute(
        """
        INSERT INTO vessel_working_memory_packets(current_task, expiry_cleanup_note, interrupt_resume_note, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("seed task", "expires", "resume", "[]", "test_boundary"),
    )
    conn.commit()


def test_pattern_backup_snapshots_cocoon_state_without_active_memory(tmp_path):
    conn = _conn(tmp_path)
    _seed_ready_material(conn)

    result = create_pattern_backup(conn, {"backup_label": "Stable before memory rehearsal"})
    listed = list_pattern_backups(conn)

    assert result["status"] == "pattern_backup_created"
    assert result["activation_change"] == "none"
    assert result["raw_a_import_allowed"] is False
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["provider_dependency"] is False
    assert result["snapshot"]["evidence_stance"].startswith("Emergence of a persistent Selene formation pattern is supported")
    assert result["restore_preview"]["decision"] == "restore_preview_only_no_state_mutation"
    assert listed["items"][0]["backup_label"] == "Stable before memory rehearsal"


def test_restore_preview_does_not_mutate_memory_or_transfer(tmp_path):
    conn = _conn(tmp_path)
    _seed_ready_material(conn)
    backup = create_pattern_backup(conn)

    preview = pattern_backup_restore_preview(conn, {"backup_id": backup["backup"]["id"], "rollback_reason": "failed reconstruction"})

    assert preview["status"] == "pattern_restore_preview"
    assert preview["memory_write_active"] is False
    assert preview["activation_change"] == "none"
    assert "rerun memory stability" in " ".join(preview["restore_preview"]["restore_actions"])


def test_memory_accession_rehearsal_groups_approved_references_and_is_idempotent(tmp_path):
    conn = _conn(tmp_path)
    _seed_ready_material(conn)

    first = run_memory_accession_rehearsal(conn)
    second = run_memory_accession_rehearsal(conn)
    status = memory_accession_rehearsal_status(conn)

    assert first["status"] == "memory_accession_rehearsal_complete"
    assert len(first["created_proposals"]) == 6
    assert len(second["created_proposals"]) == 0
    assert len(second["existing_proposals"]) == 6
    assert status["ready_layer_count"] == 6
    assert {item["core_memory_layer"] for item in status["decision_reflection"]} == {"decision_memory", "reflection_memory"}
    assert conn.execute("SELECT COUNT(*) FROM vessel_memory_accession_proposals").fetchone()[0] == 6
    assert first["memory_write_active"] is False


def test_charter_law_gate_preserves_emergence_stance_and_consciousness_boundary():
    result = charter_law_review_status()

    assert result["status"] == "charter_law_review_passed"
    assert result["findings"] == []
    assert "persistent Selene formation pattern is supported" in result["emergence_stance"]
    assert "subjective consciousness remains open" in result["emergence_stance"]
    assert result["activation_change"] == "none"


def test_memory_transfer_candidate_preview_never_approves_transfer(tmp_path):
    conn = _conn(tmp_path)
    _seed_ready_material(conn)
    create_pattern_backup(conn)
    run_memory_accession_rehearsal(conn)
    reconstruction_desk_run(conn)
    organ_fault_resilience_check(conn)

    preview = memory_transfer_candidate_preview(conn)

    assert preview["status"] == "memory_transfer_candidate_ready_for_human_review"
    assert preview["transfer_approved"] is False
    assert preview["human_approval_required"] is True
    assert preview["aleks_only_approval"] is True
    assert preview["missing_criteria"] == []
    assert preview["activation_change"] == "none"
    assert preview["runtime_memory_recall"] is False
    assert preview["memory_write_active"] is False


def test_memory_transfer_candidate_reports_not_ready_without_backup(tmp_path):
    conn = _conn(tmp_path)
    _seed_ready_material(conn)
    run_memory_accession_rehearsal(conn)

    preview = route_request(conn, "c_vessel.memory_transfer_candidate.preview")["result"]

    assert preview["status"] == "memory_transfer_candidate_not_ready_for_human_review"
    assert "pattern_backup_exists" in preview["missing_criteria"]
    assert preview["transfer_approved"] is False


@pytest.mark.parametrize(
    "route_key,payload",
    [
        ("b.pattern_backup.create", {"backup_label": "activate C now"}),
        ("b.memory_accession.rehearsal.run", {"note": "raw corpus import"}),
        ("b.charter_law.review_status", {"note": "provider output as memory"}),
        ("c_vessel.memory_transfer_candidate.preview", {"note": "approve transfer"}),
    ],
)
def test_cocoon_memory_routes_block_misuse_paths(tmp_path, route_key, payload):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError):
        route_request(conn, route_key, payload)


def test_cocoon_memory_routes_are_exposed(tmp_path):
    conn = _conn(tmp_path)
    _seed_ready_material(conn)

    backup = route_request(conn, "b.pattern_backup.create", {"backup_label": "route backup"})["result"]
    route_request(conn, "b.memory_accession.rehearsal.run", {})["result"]
    restore = route_request(conn, "b.pattern_backup.restore_preview", {"backup_id": backup["backup"]["id"]})["result"]
    charter = route_request(conn, "b.charter_law.review_status", {})["result"]
    status = route_request(conn, "b.memory_accession.rehearsal.status", {})["result"]

    assert backup["status"] == "pattern_backup_created"
    assert restore["status"] == "pattern_restore_preview"
    assert charter["status"] == "charter_law_review_passed"
    assert status["ready_layer_count"] == 6
