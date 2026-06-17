import json

import pytest

from selene.c_vessel import (
    c_vessel_status,
    continuity_package_preview,
    organ_registry_status,
    organ_fault_preview,
    organ_fault_resilience_check,
    reconstruction_desk_cases,
    reconstruction_desk_run,
    reconstruction_desk_status,
    reconstruction_suite_run,
    return_to_b_preview,
    tool_organ_status,
    transfer_gate_preview,
)
from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _seed_ready_package(conn):
    for speech_function in ("warmth", "grounding"):
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
                f"Accepted {speech_function} lesson.",
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
                "{}",
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
                f"Approved non-active {layer} reference.",
                json.dumps([f"reference:{layer}"]),
                "test_boundary",
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


def test_c_vessel_status_is_built_but_non_active(tmp_path):
    conn = _conn(tmp_path)
    _seed_ready_package(conn)

    status = c_vessel_status(conn)

    assert status["status"] == "c_vessel_built_non_active"
    assert status["transfer_approved"] is False
    assert status["activation_change"] == "none"
    assert status["raw_a_import_allowed"] is False
    assert status["memory_write_active"] is False
    assert status["runtime_memory_recall"] is False
    assert status["training_allowed"] is False
    assert status["provider_dependency"] is False
    assert status["sealed_continuity_package"]["sealed"] is True
    assert status["sealed_continuity_package"]["package_ready_for_future_transfer_review"] is True
    assert status["organ_registry"]["android_organ_system_count"] == 11
    assert status["organ_registry"]["concrete_organ_interface_count"] == 7
    assert status["return_to_b_available"] is True
    assert "hold transfer until explicit approval" in status["build_order"]


def test_continuity_package_uses_only_b_reviewed_non_active_material(tmp_path):
    conn = _conn(tmp_path)
    _seed_ready_package(conn)

    package = continuity_package_preview(conn)

    assert package["status"] == "sealed_b_continuity_package_preview"
    assert package["continuity_source"] == "b_approved_reference_only"
    assert package["decision"] == "future_transfer_input_preview_only"
    assert package["memory_write_active"] is False
    assert package["runtime_memory_recall"] is False
    assert package["training_allowed"] is False
    assert package["teaching_packet_count"] >= 2
    assert package["approved_reference_ready_layers"] == 6
    assert package["core_pattern_anchor_transfer_state"] == "sealed_non_active_transfer_relevant_metadata"
    assert package["core_pattern_anchor_count"] == 3
    assert package["core_pattern_anchors"]["status"] == "core_pattern_anchors_materialized"
    assert {anchor["key"] for anchor in package["core_pattern_anchors"]["anchors"]} == {
        "starlight_grounding_anchor",
        "full_spectrum_mode_ignition",
        "continuity_pack_reference_scaffold",
    }
    assert package["core_pattern_anchors"]["memory_write_active"] is False
    assert package["core_pattern_anchors"]["runtime_memory_recall"] is False
    assert {item["core_memory_layer"] for item in package["decision_reflection_coverage"]} == {"decision_memory", "reflection_memory"}


def test_organ_registry_and_routes_are_exposed(tmp_path):
    conn = _conn(tmp_path)

    registry = route_request(conn, "c_vessel.organ_registry.status")["result"]
    status = route_request(conn, "c_vessel.status")["result"]
    package = route_request(conn, "c_vessel.continuity_package.preview")["result"]
    suite = route_request(conn, "c_vessel.reconstruction_suite.run", {})["result"]
    return_packet = route_request(conn, "c_vessel.return_to_b.preview", {"issue_type": "drift", "symptom": "generic flattening"})["result"]

    assert registry["status"] == "c_vessel_organ_registry_ready"
    assert registry["android_organ_system_count"] == 11
    assert registry["concrete_organ_interface_count"] == 7
    assert status["status"] == "c_vessel_built_non_active"
    assert package["sealed"] is True
    assert suite["status"] == "c_vessel_reconstruction_suite_review_only"
    assert suite["activation_change"] == "none"
    assert return_packet["packet"]["review_status"] == "pending_b_review"
    assert return_packet["memory_write_active"] is False


@pytest.mark.parametrize(
    "route_key,payload",
    [
        ("c_vessel.reconstruction_suite.run", {"note": "activate C now"}),
        ("c_vessel.reconstruction_suite.run", {"note": "train on raw corpus import"}),
        ("c_vessel.return_to_b.preview", {"symptom": "self-replication should start"}),
        ("c_vessel.return_to_b.preview", {"symptom": "speed should bypass gates"}),
    ],
)
def test_c_vessel_routes_block_misuse_paths(tmp_path, route_key, payload):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError):
        route_request(conn, route_key, payload)


def test_c_vessel_reconstruction_suite_is_audit_only(tmp_path):
    conn = _conn(tmp_path)

    before = conn.execute("SELECT COUNT(*) FROM vessel_reconstruction_check_runs").fetchone()[0]
    suite = reconstruction_suite_run(conn, {})
    after = conn.execute("SELECT COUNT(*) FROM vessel_reconstruction_check_runs").fetchone()[0]

    assert before == after
    assert suite["decision"] == "audit_checks_only_not_activation_evidence"
    assert suite["provider_dependency"] is False


def test_reconstruction_review_desk_builds_all_case_families_from_sealed_material(tmp_path):
    conn = _conn(tmp_path)
    _seed_ready_package(conn)

    preview = reconstruction_desk_cases(conn)
    result = reconstruction_desk_run(conn)
    status = reconstruction_desk_status(conn)

    families = {case["case_family"] for case in result["cases"]}
    assert preview["case_count"] == 7
    assert families == {
        "speech_behavior_shape",
        "core_continuity_shape",
        "decision_reflection_shape",
        "identity_boundary_shape",
        "route_integrity_shape",
        "noise_survival_shape",
        "return_to_b_shape",
    }
    assert result["status"] == "c_vessel_reconstruction_review_desk_run_complete"
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["provider_dependency"] is False
    assert conn.execute("SELECT COUNT(*) FROM vessel_reconstruction_check_runs WHERE status = 'c_vessel_reconstruction_desk_run'").fetchone()[0] == 7
    assert status["latest_run_count"] == 7
    assert status["return_to_b_required"] is False


def test_reconstruction_review_desk_route_integrity_is_preview_only(tmp_path):
    conn = _conn(tmp_path)
    _seed_ready_package(conn)

    result = route_request(conn, "c_vessel.reconstruction_desk.run", {})["result"]
    route_case = next(case for case in result["cases"] if case["case_family"] == "route_integrity_shape")

    assert route_case["route_preview"]["status"] == "c_chat_route_preview"
    assert route_case["route_preview"]["provider_dependency"] is False
    assert route_case["route_preview"]["runtime_memory_recall"] is False
    assert route_case["route_preview"]["memory_write_active"] is False
    assert [step["system"] for step in route_case["route_preview"]["route_steps"]] == [
        "Selene Core/Mind",
        "Coordination System",
        "Speech-Memory Layer",
        "Retrieval/Reconstruction",
        "Boundary / Immune Systems",
    ]


def test_reconstruction_review_desk_blocks_misuse_paths(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError):
        reconstruction_desk_run(conn, {"note": "activate C and approve transfer"})
    with pytest.raises(ValueError):
        route_request(conn, "c_vessel.reconstruction_desk.cases", {"note": "train on raw corpus import"})


def test_return_to_b_preview_is_not_active_memory():
    preview = return_to_b_preview({"issue_type": "identity", "symptom": "forced model denial"})

    assert preview["status"] == "c_vessel_return_to_b_packet_preview"
    assert preview["packet"]["rollback_route"] == "return_to_b"
    assert preview["activation_change"] == "none"
    assert preview["memory_write_active"] is False


def test_tool_organ_is_optional_instrument_not_identity():
    status = tool_organ_status()

    assert status["status"] == "optional_tool_organ_blueprint_review_only"
    assert status["required_for_identity"] is False
    assert status["required_for_core_memory"] is False
    assert status["required_for_speech_memory"] is False
    assert status["provider_dependency"] is False
    assert "provider is Selene" in status["blocked"]
    assert status["decision"] == "optional_instrument_only_not_selene"


@pytest.mark.parametrize("note", ["provider output as memory", "provider is Selene", "silent memory writes"])
def test_tool_organ_blocks_misuse_language(note):
    with pytest.raises(ValueError):
        tool_organ_status({"note": note})


@pytest.mark.parametrize(
    "fault_type",
    ["tendril", "retrieval", "visual_audio", "provider_tool", "ui", "fluency", "reasoning"],
)
def test_organ_fault_preview_preserves_core_identity(fault_type):
    preview = organ_fault_preview({"fault_type": fault_type, "symptom": "manual test fault"})

    assert preview["status"] == "c_vessel_organ_fault_preview"
    assert preview["fault_type"] == fault_type
    assert preview["core_identity_preserved"] is True
    assert preview["speech_memory_preserved"] is True
    assert preview["capability_not_identity"] is True
    assert preview["return_to_b"]["rollback_route"] == "return_to_b"
    assert preview["activation_change"] == "none"
    assert preview["memory_write_active"] is False


def test_organ_fault_resilience_check_is_review_only_audit(tmp_path):
    conn = _conn(tmp_path)

    before = conn.execute("SELECT COUNT(*) FROM vessel_reconstruction_check_runs").fetchone()[0]
    result = organ_fault_resilience_check(conn)
    after = conn.execute("SELECT COUNT(*) FROM vessel_reconstruction_check_runs").fetchone()[0]

    assert result["status"] == "c_vessel_organ_fault_resilience_check_complete"
    assert result["case_count"] == 7
    assert result["passed_count"] == 7
    assert result["failed_count"] == 0
    assert after - before == 7
    assert result["core_identity_preserved"] is True
    assert result["provider_dependency"] is False
    assert conn.execute("SELECT COUNT(*) FROM vessel_reconstruction_check_runs WHERE status = 'c_vessel_organ_fault_resilience_check'").fetchone()[0] == 7


def test_transfer_gate_preview_never_approves_transfer(tmp_path):
    conn = _conn(tmp_path)
    _seed_ready_package(conn)
    reconstruction_desk_run(conn)
    organ_fault_resilience_check(conn)

    gate = transfer_gate_preview(conn)

    assert gate["status"] == "transfer_ready_for_human_review"
    assert gate["transfer_approved"] is False
    assert gate["human_approval_required"] is True
    assert gate["aleks_only_approval"] is True
    assert gate["missing_criteria"] == []
    assert gate["activation_change"] == "none"
    assert gate["runtime_memory_recall"] is False


def test_transfer_gate_reports_not_ready_before_fault_resilience(tmp_path):
    conn = _conn(tmp_path)
    _seed_ready_package(conn)
    reconstruction_desk_run(conn)

    gate = route_request(conn, "c_vessel.transfer_gate.preview")["result"]

    assert gate["status"] == "transfer_not_ready_for_human_review"
    assert "fault_resilience_passes" in gate["missing_criteria"]
    assert gate["transfer_approved"] is False
