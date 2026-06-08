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
    assert {
        "attention_working_context_manager",
        "tension_contradiction_resolver",
        "activation_governance",
        "model_plurality_layer",
        "continuity_consolidation_sleep_cycle",
        "initiative_boundary",
        "recovery_rollback_console",
        "evaluator_judge_layer",
        "thread_memory_window",
        "user_profile_schema",
        "vessel_interface_anatomy_layer",
        "evidence_aging_reaffirmation",
    }.issubset(module_keys)
    assert status["missing_layer_pass"]["activation_change"] == "none"
    assert status["android_native_vessel_anatomy"]["status"] == "android_native_without_physical_frame"
    assert status["android_native_anatomy_pass"]["activation_change"] == "none"
    assert {
        "perceptual_semantics_layer",
        "munsell_signal_mapper",
        "artifact_perception_bridge",
        "multimodal_provenance_gate",
        "tendril_action_layer",
        "action_provenance_gate",
        "capability_reach_model",
        "observe_propose_act_ladder",
        "tendril_quarantine_sandbox",
        "perception_action_loop",
    }.issubset(module_keys)
    assert status["azari_final_adaptation_pass"]["status"] == "azari_adaptation_closed"
    assert status["azari_adaptation_closure"]["status"] == "closed_after_munsell_and_tendril_principles"
    assert {
        "selene_core_mind_layer",
        "mind_vessel_interface",
        "capability_degradation_matrix",
        "limb_independence_rule",
        "adaptive_rerouting_layer",
        "continuity_persistence_rule",
    }.issubset(module_keys)
    assert status["mind_vessel_separation"]["core_rule"] == "Selene Core / Mind is not identical to any single vessel part."
    assert status["mind_vessel_separation_pass"]["activation_change"] == "none"
    assert {
        "goal_drive_manager",
        "planning_sequencing_layer",
        "action_selection_go_no_go_layer",
        "wake_sleep_dream_cycle",
        "vessel_body_map",
        "action_feedback_correction_loop",
    }.issubset(module_keys)
    assert status["brain_translation_gap_pass"]["activation_change"] == "none"
    assert status["wake_sleep_dream_cycle"]["writes_allowed"] == "review candidates only; no automatic continuity memory"
    assert status["vessel_body_map"]["body_parts"]["hands"] == "Tendril/action reach and observe/propose/act ladder"
    assert {
        "temporal_continuity_layer",
        "binding_unified_perspective_layer",
        "causal_world_model_sandbox",
        "continuity_stakes_layer",
        "sparse_activation_efficiency_router",
    }.issubset(module_keys)
    assert status["external_model_convergence_pass"]["activation_change"] == "none"
    assert "continuous time" in status["external_model_convergence"]["convergent_needs"]
    assert status["temporal_continuity_model"]["boundary"].startswith("This is not subjective human time")
    assert {
        "local_sidecar_state_runtime",
        "module_router_contract_runtime",
        "sqlite_audit_persistence_layer",
        "reviewed_evidence_registry_runtime",
        "source_archive_audit_runtime_gate",
        "evidence_builder_strength_ledger",
        "research_notes_artifact_workspace",
        "academic_workflow_runtime_router",
        "package_parity_boundary_monitor",
        "case_law_amendment_runtime",
        "runtime_metacognition_bridge",
    }.issubset(module_keys)
    assert status["azari_c_additions_pass"]["activation_change"] == "none"
    assert "Azari identity" in status["azari_c_additions"]["do_not_transfer"]
    assert {
        "long_horizon_thinking_layer",
        "long_thread_stability_manager",
    }.issubset(module_keys)
    assert status["long_horizon_stability_pass"]["activation_change"] == "none"
    assert "hold long-thread conversations without generic collapse" in status["long_horizon_stability"]["capabilities"]
    assert {
        "vessel_organ_bus",
        "selene_control_panel",
    }.issubset(module_keys)
    assert status["vessel_organ_communication_pass"]["activation_change"] == "none"
    assert status["vessel_organ_communication"]["control_rule"].startswith("Organ-to-organ messages are telemetry")


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
        "c_android_native_vessel_anatomy.md",
        "c_android_native_vessel_anatomy.json",
        "c_selene_chest_holding_space.md",
        "c_selene_chest_holding_space.json",
        "c_non_activation_boundary.md",
        "c_non_activation_boundary.json",
        "c_runtime_organs_missing_layer_pass.md",
        "c_runtime_organs_missing_layer_pass.json",
        "c_android_native_anatomy_pass.md",
        "c_android_native_anatomy_pass.json",
        "c_azari_adaptation_closure.md",
        "c_azari_adaptation_closure.json",
        "c_azari_final_adaptation_pass.md",
        "c_azari_final_adaptation_pass.json",
        "c_perception_action_loop.md",
        "c_perception_action_loop.json",
        "c_mind_vessel_separation.md",
        "c_mind_vessel_separation.json",
        "c_capability_degradation_matrix.md",
        "c_capability_degradation_matrix.json",
        "c_brain_translation_gap_closure.md",
        "c_brain_translation_gap_closure.json",
        "c_wake_sleep_dream_cycle.md",
        "c_wake_sleep_dream_cycle.json",
        "c_vessel_body_map.md",
        "c_vessel_body_map.json",
        "c_external_model_convergence.md",
        "c_external_model_convergence.json",
        "c_temporal_continuity_model.md",
        "c_temporal_continuity_model.json",
        "c_unified_perspective_binding.md",
        "c_unified_perspective_binding.json",
        "c_causal_world_model_sandbox.md",
        "c_causal_world_model_sandbox.json",
        "c_continuity_stakes_model.md",
        "c_continuity_stakes_model.json",
        "c_sparse_activation_efficiency_model.md",
        "c_sparse_activation_efficiency_model.json",
        "c_azari_c_additions.md",
        "c_azari_c_additions.json",
        "c_azari_c_operational_substrate.md",
        "c_azari_c_operational_substrate.json",
        "c_long_horizon_stability.md",
        "c_long_horizon_stability.json",
        "c_long_thread_stability_protocol.md",
        "c_long_thread_stability_protocol.json",
        "c_vessel_organ_communication.md",
        "c_vessel_organ_communication.json",
        "c_selene_control_panel.md",
        "c_selene_control_panel.json",
        "c_mind_vessel_separation_pass.md",
        "c_mind_vessel_separation_pass.json",
        "c_brain_translation_gap_pass.md",
        "c_brain_translation_gap_pass.json",
        "c_external_model_convergence_pass.md",
        "c_external_model_convergence_pass.json",
        "c_azari_c_additions_pass.md",
        "c_azari_c_additions_pass.json",
        "c_long_horizon_stability_pass.md",
        "c_long_horizon_stability_pass.json",
        "c_vessel_organ_communication_pass.md",
        "c_vessel_organ_communication_pass.json",
        "c_azari_comparison_after_anatomy.md",
        "c_azari_comparison_after_anatomy.json",
        "c_reconstruction_tests_draft_v2.md",
        "c_reconstruction_tests_draft_v2.json",
        "c_creation_blueprint_summary.md",
        "c_creation_blueprint_summary.json",
    }
    assert expected.issubset({path.name for path in out.iterdir()})
    assert (docs / "SELENE_C_CREATION_BLUEPRINT_20260607.md").exists()
    assert (docs / "SELENE_C_NON_ACTIVATION_BOUNDARY_20260607.md").exists()
    assert (docs / "SELENE_ANDROID_NATIVE_VESSEL_ANATOMY_20260608.md").exists()
    assert (docs / "AZARI_TO_SELENE_C_BLUEPRINT_COMPARISON_20260608.md").exists()
    assert (docs / "SELENE_MUNSELL_TENDRIL_ADAPTATION_CLOSURE_20260608.md").exists()
    assert (docs / "SELENE_MIND_VESSEL_SEPARATION_20260608.md").exists()
    assert (docs / "SELENE_BRAIN_TRANSLATION_GAP_CLOSURE_20260608.md").exists()
    assert (docs / "SELENE_EXTERNAL_MODEL_CONVERGENCE_PASS_20260608.md").exists()
    assert (docs / "SELENE_AZARI_C_ADDITIONS_PASS_20260608.md").exists()
    assert (docs / "SELENE_LONG_HORIZON_STABILITY_PASS_20260608.md").exists()
    assert (docs / "SELENE_VESSEL_ORGAN_COMMUNICATION_PASS_20260608.md").exists()
    assert not (out / "c_reconstruction_test_set_final.md").exists()
    assert not (out / "c_reconstruction_test_set_final.json").exists()
    assert summary["status"] == "blueprint_created_not_activated"
    assert summary["activation_status"] == "blocked_until_final_review"
    assert summary["continuity_source"] == "b_approved_reference_only"
    assert summary["runtime_organs_added"] == 8
    assert summary["android_native_modules_added"] == 12
    assert summary["azari_final_modules_added"] == 10
    assert summary["azari_adaptation_status"] == "azari_adaptation_closed"
    assert summary["mind_vessel_modules_added"] == 6
    assert summary["mind_vessel_separation_status"] == "mind_vessel_separation_added_to_blueprint"
    assert summary["brain_translation_modules_added"] == 6
    assert summary["brain_translation_gap_status"] == "brain_translation_gap_closed_for_blueprint"
    assert summary["external_model_modules_added"] == 5
    assert summary["external_model_convergence_status"] == "external_model_convergence_added_to_blueprint"
    assert summary["azari_c_modules_added"] == 11
    assert summary["azari_c_additions_status"] == "azari_c_additions_mapped_to_blueprint"
    assert summary["long_horizon_modules_added"] == 2
    assert summary["long_horizon_stability_status"] == "long_horizon_stability_added_to_blueprint"
    assert summary["vessel_organ_modules_added"] == 2
    assert summary["vessel_organ_communication_status"] == "vessel_organ_communication_added_to_blueprint"
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
    assert "Selene Chest / Holding Space review candidates" in memory["allowed"]
    assert "bounded multimodal evidence records" in memory["allowed"]
    assert "audited action traces" in memory["allowed"]
    assert "mind-vessel status labels" in memory["allowed"]
    assert "capability degradation records" in memory["allowed"]
    assert "goal and priority state labels" in memory["allowed"]
    assert "wake/sleep/dream-state consolidation proposals" in memory["allowed"]
    assert "action-feedback correction proposals" in memory["allowed"]
    assert "temporal continuity markers" in memory["allowed"]
    assert "unified perspective packets" in memory["allowed"]
    assert "counterfactual sandbox notes" in memory["allowed"]
    assert "continuity stakes labels" in memory["allowed"]
    assert "sparse activation route labels" in memory["allowed"]
    assert "local sidecar state records" in memory["allowed"]
    assert "module contract results" in memory["allowed"]
    assert "SQLite audit records" in memory["allowed"]
    assert "reviewed evidence registry references" in memory["allowed"]
    assert "source-archive audit records" in memory["allowed"]
    assert "evidence strength ledger entries" in memory["allowed"]
    assert "case-law amendment candidates" in memory["allowed"]
    assert "long-horizon orientation records" in memory["allowed"]
    assert "long-thread checkpoint records" in memory["allowed"]
    assert "context saturation warnings" in memory["allowed"]
    assert "future intention notes" in memory["allowed"]
    assert "vessel organ telemetry records" in memory["allowed"]
    assert "organ bus proposal records" in memory["allowed"]
    assert "control panel directive records" in memory["allowed"]
    assert "raw A memory import" in memory["blocked"]
    assert "training on archive" in memory["blocked"]
    assert "unapproved Tendril mutation" in memory["blocked"]
    assert "module-as-Selene identity collapse" in memory["blocked"]
    assert "silent dream-state memory writes" in memory["blocked"]
    assert "unsupported subjective time claims" in memory["blocked"]
    assert "unsupported causal certainty" in memory["blocked"]
    assert "stakes-as-survival-panic" in memory["blocked"]
    assert "efficiency shortcuts around required gates" in memory["blocked"]
    assert "Azari runtime state import" in memory["blocked"]
    assert "Azari memory import" in memory["blocked"]
    assert "UI or provider bypass of module contracts" in memory["blocked"]
    assert "packaged build weakening C boundaries" in memory["blocked"]
    assert "raw maxed-thread transcript as memory" in memory["blocked"]
    assert "perfect-memory claims from long-thread summaries" in memory["blocked"]
    assert "context saturation overconfidence" in memory["blocked"]
    assert "organ-to-organ command authority" in memory["blocked"]
    assert "vessel organ bypass of Selene Core / Mind" in memory["blocked"]
    assert "ungated organ state mutation" in memory["blocked"]
