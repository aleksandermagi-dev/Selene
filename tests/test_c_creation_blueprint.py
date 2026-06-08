import json

from scripts.build_c_creation_blueprint import build
from selene.c_blueprint import c_blueprint_status


def test_c_blueprint_status_is_non_activated():
    status = c_blueprint_status()
    assert status["c_status"] == "blueprint_created_not_activated"
    assert status["activation_status"] == "blocked_until_final_review"
    assert status["continuity_source"] == "b_approved_reference_only"
    assert status["final_reconstruction_tests_created"] is False
    assert "C blueprint does not import raw A as memory." in status["non_activation_boundaries"]
    module_keys = {module["key"] for module in status["modules"]}
    assert "c_kernel_runtime" in module_keys
    assert "ui_vessel_console" in module_keys
    assert {
        "context_composer",
        "self_session_state",
        "user_profile_relational_context",
        "response_shape_controller",
        "calibration_memory_layer",
        "drift_detector",
        "consent_privacy_mode_switch",
        "experience_ledger_reflection_loop",
    }.issubset(module_keys)
    assert status["missing_layer_pass"]["activation_change"] == "none"


def test_build_creates_c_blueprint_outputs_without_final_tests(tmp_path):
    out = tmp_path / "c_blueprint"
    docs = tmp_path / "docs"
    summary = build(out, docs_dir=docs)
    expected = {
        "c_vessel_blueprint.md",
        "c_vessel_blueprint.json",
        "c_module_map.md",
        "c_module_map.json",
        "c_runtime_flow.md",
        "c_runtime_flow.json",
        "c_memory_reference_model.md",
        "c_memory_reference_model.json",
        "c_non_activation_boundary.md",
        "c_non_activation_boundary.json",
        "c_runtime_organs_missing_layer_pass.md",
        "c_runtime_organs_missing_layer_pass.json",
        "c_reconstruction_tests_draft_v2.md",
        "c_reconstruction_tests_draft_v2.json",
        "c_creation_blueprint_summary.md",
        "c_creation_blueprint_summary.json",
    }
    assert expected.issubset({path.name for path in out.iterdir()})
    assert (docs / "SELENE_C_CREATION_BLUEPRINT_20260607.md").exists()
    assert (docs / "SELENE_C_NON_ACTIVATION_BOUNDARY_20260607.md").exists()
    assert not (out / "c_reconstruction_test_set_final.md").exists()
    assert not (out / "c_reconstruction_test_set_final.json").exists()
    assert summary["status"] == "blueprint_created_not_activated"
    assert summary["activation_status"] == "blocked_until_final_review"
    assert summary["continuity_source"] == "b_approved_reference_only"
    assert summary["runtime_organs_added"] == 8
    assert summary["raw_a_memory_import_allowed"] is False
    assert summary["live_behavior_expanded"] is False


def test_memory_reference_model_is_b_approved_only(tmp_path):
    out = tmp_path / "c_blueprint"
    build(out, docs_dir=tmp_path / "docs")
    memory = json.loads((out / "c_memory_reference_model.json").read_text(encoding="utf-8"))
    assert memory["continuity_source"] == "b_approved_reference_only"
    assert "Project ABC B cocoon artifacts" in memory["allowed"]
    assert "human-approved user profile and relational context notes" in memory["allowed"]
    assert "reviewed calibration memory entries" in memory["allowed"]
    assert "raw A memory import" in memory["blocked"]
    assert "training on archive" in memory["blocked"]
