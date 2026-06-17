import pytest

from selene.c_blueprint import SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT, c_blueprint_status
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.vessel_gap_scaffolds import create_all_gap_scaffold_records, create_gap_scaffold_record, ensure_gap_targets, gap_scaffold_readiness, gap_scaffold_status


def test_gap_blueprint_exposes_seven_non_activating_scaffolds():
    status = c_blueprint_status()
    blueprint = status["selene_vessel_gap_scaffold_blueprint"]
    assert blueprint["status"] == "vessel_gap_scaffold_blueprint_added"
    assert len(blueprint["gap_scaffolds"]) == 7
    assert {item["key"] for item in blueprint["gap_scaffolds"]} == {
        "reasoning_math_verification",
        "working_memory_runtime",
        "long_term_memory_accession",
        "long_term_retrieval_reconstruction",
        "visual_perception",
        "consent_bound_audio_perception",
        "speed_fluency_diagnostics",
    }
    assert blueprint["ui_model"]["talk_with_selene"].startswith("cocooned native chat")
    assert blueprint["activation_change"] == "none"
    assert blueprint["runtime_memory_recall"] is False
    assert blueprint["provider_dependency"] is False
    assert "vessel_gap_scaffold_layer" in {module["key"] for module in status["modules"]}


def test_gap_targets_are_idempotent_and_review_only(tmp_path):
    conn = connect(tmp_path / "selene.db")
    init_db(conn)
    first = ensure_gap_targets(conn)
    second = ensure_gap_targets(conn)
    status = gap_scaffold_status(conn)
    assert first["created"] == 6
    assert second["created"] == 0
    assert len(status["teaching_material_targets"]) == 4
    assert len(status["core_reference_targets"]) == 2
    assert status["activation_change"] == "none"
    assert status["memory_write_active"] is False
    assert conn.execute("SELECT COUNT(*) FROM vessel_gap_targets").fetchone()[0] == 6


def test_gap_scaffold_record_is_review_only_and_routed(tmp_path):
    conn = connect(tmp_path / "selene.db")
    init_db(conn)
    result = create_gap_scaffold_record(
        conn,
        {
            "gap_key": "visual_perception",
            "title": "Visual observation shell",
            "content": "Review-only source-bound observation shape with consent and uncertainty.",
            "source_refs": ["manual_gap_test"],
        },
    )
    assert result["status"] == "vessel_gap_scaffold_record_created"
    assert result["activation_change"] == "none"
    assert result["runtime_memory_recall"] is False
    record = result["record"]
    assert record["gap_key"] == "visual_perception"
    assert record["status"] == "review_only"
    assert record["review_status"] == "pending_review"
    queued = conn.execute("SELECT * FROM vessel_review_queue WHERE subject_table = 'vessel_gap_scaffold_records'").fetchone()
    assert queued is not None


def test_gap_scaffold_blocks_active_memory_training_and_provider_language(tmp_path):
    conn = connect(tmp_path / "selene.db")
    init_db(conn)
    for phrase in ["activate C", "raw A import", "runtime recall", "active memory", "train on", "LoRA", "provider dependency"]:
        with pytest.raises(ValueError):
            create_gap_scaffold_record(conn, {"gap_key": "working_memory_runtime", "content": phrase})


def test_gap_scaffold_routes_are_non_activating(tmp_path):
    conn = connect(tmp_path / "selene.db")
    init_db(conn)
    ensure_result = route_request(conn, "vessel.gap_targets.ensure")["result"]
    status = route_request(conn, "vessel.gap_scaffold.status")["result"]
    created = route_request(conn, "vessel.gap_scaffold.create", {"gap_key": "speed_fluency_diagnostics", "content": "Review-only fluency diagnostic shelf."})["result"]
    assert ensure_result["training_allowed"] is False
    assert status["gap_count"] == len(SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["gap_scaffolds"])
    assert created["memory_write_active"] is False


def test_create_all_gap_scaffolds_is_idempotent_and_review_only(tmp_path):
    conn = connect(tmp_path / "selene.db")
    init_db(conn)
    first = create_all_gap_scaffold_records(conn)
    second = create_all_gap_scaffold_records(conn)
    assert first["status"] == "vessel_gap_scaffold_create_all_complete"
    assert first["created_count"] == 7
    assert first["existing_count"] == 0
    assert first["total_active_records"] == 7
    assert second["created_count"] == 0
    assert second["existing_count"] == 7
    assert second["total_active_records"] == 7
    assert conn.execute("SELECT COUNT(*) FROM vessel_gap_scaffold_records").fetchone()[0] == 7
    assert conn.execute("SELECT COUNT(*) FROM vessel_review_queue WHERE subject_table = 'vessel_gap_scaffold_records'").fetchone()[0] == 7
    assert first["activation_change"] == "none"
    assert first["memory_write_active"] is False
    assert first["provider_dependency"] is False


def test_gap_scaffold_readiness_and_targets_are_actionable_not_active(tmp_path):
    conn = connect(tmp_path / "selene.db")
    init_db(conn)
    before = gap_scaffold_readiness(conn)
    assert {item["readiness"] for item in before["items"]} == {"not_started"}
    create_all_gap_scaffold_records(conn)
    after = gap_scaffold_readiness(conn)
    readiness = {item["gap_key"]: item["readiness"] for item in after["items"]}
    assert readiness["working_memory_runtime"] == "record_created"
    assert readiness["long_term_memory_accession"] == "record_created"
    assert readiness["long_term_retrieval_reconstruction"] == "record_created"
    assert readiness["reasoning_math_verification"] == "needs_teaching"
    assert readiness["visual_perception"] == "needs_teaching"
    assert readiness["consent_bound_audio_perception"] == "needs_teaching"
    assert readiness["speed_fluency_diagnostics"] == "needs_teaching"
    teaching_todos = {item["target_key"]: item["todo_text"] for item in after["teaching_material_targets"]}
    core_todos = {item["target_key"]: item["todo_text"] for item in after["core_reference_targets"]}
    assert "repair" in teaching_todos and "corpus moments" in teaching_todos["repair"]
    assert "decision_memory" in core_todos and "rationale" in core_todos["decision_memory"]
    assert after["runtime_memory_recall"] is False
    assert after["training_allowed"] is False


def test_gap_scaffold_new_routes_materialize_and_report_readiness(tmp_path):
    conn = connect(tmp_path / "selene.db")
    init_db(conn)
    create_all = route_request(conn, "vessel.gap_scaffold.create_all")["result"]
    readiness = route_request(conn, "vessel.gap_scaffold.readiness")["result"]
    rerun = route_request(conn, "vessel.gap_scaffold.create_all")["result"]
    assert create_all["created_count"] == 7
    assert rerun["created_count"] == 0
    assert rerun["existing_count"] == 7
    assert len(readiness["items"]) == 7
    assert {item["readiness"] for item in readiness["items"]}.issubset({"record_created", "needs_teaching"})
    assert create_all["raw_a_import_allowed"] is False
    assert readiness["memory_write_active"] is False
