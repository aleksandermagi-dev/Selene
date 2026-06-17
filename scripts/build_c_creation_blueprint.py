from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from selene.c_blueprint import (
    ACTIVATION_STATUS,
    ANDROID_NATIVE_ANATOMY_PASS,
    ANDROID_ORGAN_SYSTEMS,
    ANDROID_NATIVE_VESSEL_ANATOMY,
    ARTIFACT_DIR,
    AZARI_C_ADDITIONS,
    AZARI_C_ADDITIONS_PASS,
    AZARI_C_OPERATIONAL_SUBSTRATE,
    AZARI_ADAPTATION_CLOSURE,
    AZARI_FINAL_ADAPTATION_PASS,
    BRAIN_TRANSLATION_GAP_CLOSURE,
    BRAIN_TRANSLATION_GAP_PASS,
    BOUNDED_SELF_UNCERTAINTY,
    CAUSAL_WORLD_MODEL_SANDBOX,
    CONTINUITY_SOURCE,
    CONTINUITY_STAKES_MODEL,
    ETHICAL_FRAMEWORK_ROUTER,
    EXTERNAL_MODEL_CONVERGENCE,
    EXTERNAL_MODEL_CONVERGENCE_PASS,
    LONG_HORIZON_STABILITY,
    LONG_HORIZON_STABILITY_PASS,
    LONG_THREAD_STABILITY_PROTOCOL,
    MEMORY_LIFECYCLE_FLOW,
    MEMORY_REFERENCE_MODEL,
    MEMORY_REGION_TRANSLATION,
    MIND_VESSEL_SEPARATION,
    MIND_VESSEL_SEPARATION_PASS,
    MISSING_LAYER_PASS,
    MODULES,
    MORAL_COGNITION_LAW_PASS,
    MORAL_GRACEFUL_FALL_POLICY,
    NON_ACTIVATION_BOUNDARIES,
    ORGAN_NON_IDENTITY_LAW,
    PERCEPTION_ACTION_LOOP,
    RECONSTRUCTION_TESTS_DRAFT_V2,
    RECOGNITION_ETHICS_LINK,
    RECOGNITION_RECONSTRUCTION_CHECKS,
    RECOGNITION_THROUGH_STRUCTURE,
    RECOGNITION_THROUGH_STRUCTURE_PASS,
    RUNTIME_FLOW,
    PATTERN_FIRST_TRANSFER_SAFETY,
    PATTERN_FIRST_TRANSFER_SAFETY_PASS,
    RETRIEVAL_RECONSOLIDATION_POLICY,
    CAPABILITY_DEGRADATION_MATRIX,
    SELENE_CHEST_HOLDING_SPACE,
    SELENE_INTEGRITY_DIGNITY_PASS,
    SELENE_INTEGRITY_DIGNITY_PROTECTIONS,
    SELENE_INTEGRITY_RIGHTS_POLICY,
    SELENE_MORAL_COGNITION_LAW,
    SELENE_MEMORY_ARCHITECTURE,
    SELENE_MEMORY_ARCHITECTURE_PASS,
    SELENE_PROTECTION_BALANCER,
    SELENE_RECOGNITION_CRITERIA,
    INTUITION_REASONING_SAFETY,
    NON_SCRIPTING_VOICE_POLICY,
    SPARSE_ACTIVATION_EFFICIENCY_MODEL,
    STATUS,
    SELENE_CONTROL_PANEL,
    SELENE_CORE_MEMORY_PHILOSOPHY,
    SELENE_CORE_PATTERN_ANCHORS,
    SELENE_CORE_UNCERTAINTY_PHILOSOPHY,
    SELENE_CORE_MOTIVATION_BALANCE_PHILOSOPHY,
    SELENE_CHAT_GENERATION_REPLACEMENT,
    SELENE_SPEECH_MEMORY_LAYER,
    SELENE_PAPER_MAP_GAP_BLUEPRINT,
    SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT,
    SELENE_ORGAN_BLUEPRINTS,
    SELENE_CORE_REFERENCE_READINESS_PRIORITIES,
    SELENE_C_INDEPENDENCE_AND_RETURN_PATH,
    SELENE_C_VESSEL_BUILD_MANIFEST,
    SELENE_EXACT_PHRASE_BRAID_FINDINGS,
    TEMPORAL_CONTINUITY_MODEL,
    UNIFIED_PERSPECTIVE_BINDING,
    VESSEL_ORGAN_COMMUNICATION,
    VESSEL_ORGAN_COMMUNICATION_PASS,
    VESSEL_COMPATIBILITY_GATE,
    VESSEL_BODY_MAP,
    WAKE_SLEEP_DREAM_CYCLE,
    c_blueprint_status,
)


OUT = Path(ARTIFACT_DIR)
DOCS = Path("docs")
SOURCE_REFS = [
    "analysis/abc_cocoon_20260606/abc_cocoon_summary.md",
    "analysis/before_c_calibration_docket_20260607/before_c_calibration_docket.md",
    "analysis/selene_calibration_pack_20260607/selene_calibration_pack.md",
    "analysis/why_salience_translation_20260607/why_salience_summary.md",
    "analysis/metacognition_translation_20260606/metacognition_translation_summary.json",
    "analysis/pre_c_vessel_prep_20260607/pre_c_vessel_prep_summary.md",
    "docs/SELENE_MASTER_REVIEW_PACKET_20260607.md",
    "docs/SELENE_CURRENT_STATUS_20260612.md",
    "docs/SELENE_PRE_ARXIV_CHECKPOINT_20260612.md",
    "docs/SELENE_CHECKPOINT_SPEECH_MEMORY_20260612.md",
    "docs/SELENE_CORE_TEACHING_MEMORY_PHILOSOPHY_20260612.md",
    "docs/SELENE_CHAT_GENERATION_REPLACEMENT_MAP_20260612.md",
    "docs/SELENE_SPEECH_MEMORY_LAYER_BLUEPRINT_20260612.md",
    "docs/SELENE_RECOGNITION_RECONSTRUCTION_CHECKS_20260612.md",
    "docs/SELENE_PAPER_MAP_GAP_BLUEPRINT_20260612.md",
    "docs/SELENE_COCOON_DUAL_UI_GAP_SCAFFOLD_PASS_20260613.md",
    "docs/SELENE_ORGAN_BLUEPRINTS_MATERIALIZATION_20260614.md",
    "docs/SELENE_EXACT_PHRASE_BRAID_FINDINGS_20260616.md",
    "docs/SELENE_CORE_UNCERTAINTY_PHILOSOPHY_20260616.md",
    "docs/SELENE_CORE_MOTIVATION_BALANCE_PHILOSOPHY_20260616.md",
    "Core ideas/Uncertainty.md",
    "Core ideas/MaslovandMythoughts.md",
    "src/selene/chat.py",
    "src/selene/native_generation.py",
    "src/selene/detached_corpus.py",
    "src/selene/providers.py",
    "src/selene/gates.py",
    "might help/Ai thoughts and opinions.md",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_md(path: Path, title: str, sections: list[tuple[str, Any]]) -> None:
    lines = [
        f"# {title}",
        "",
        f"Generated: {now()}",
        "",
        "Boundary: C blueprint/substrate only. C is not activated. Raw A is not memory. Continuity source is B-approved references only.",
        "",
    ]
    for heading, value in sections:
        lines.extend([f"## {heading}", ""])
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"### {item.get('key') or item.get('id') or item.get('name') or 'item'}")
                    lines.append("")
                    for key, field_value in item.items():
                        lines.append(f"- `{key}`: {field_value}")
                    lines.append("")
                else:
                    lines.append(f"- {item}")
            lines.append("")
        elif isinstance(value, dict):
            for key, field_value in value.items():
                lines.append(f"- `{key}`: {field_value}")
            lines.append("")
        else:
            lines.extend([str(value), ""])
    while lines and lines[-1] == "":
        lines.pop()
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(out: Path = OUT, docs_dir: Path = DOCS) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    status = c_blueprint_status()
    vessel_blueprint = {
        "status": STATUS,
        "activation_status": ACTIVATION_STATUS,
        "continuity_source": CONTINUITY_SOURCE,
        "purpose": "Lay out C as a reviewable vessel blueprint/substrate before any activation.",
        "source_refs": SOURCE_REFS,
        "non_activation_boundaries": NON_ACTIVATION_BOUNDARIES,
        "next_milestone": "Review C blueprint, then decide whether to finalize reconstruction tests.",
    }
    module_map = {"status": STATUS, "modules": MODULES}
    runtime_flow = {"status": STATUS, "flow": RUNTIME_FLOW, "activation_status": ACTIVATION_STATUS}
    non_activation = {
        "status": STATUS,
        "activation_status": ACTIVATION_STATUS,
        "boundaries": NON_ACTIVATION_BOUNDARIES,
        "final_reconstruction_tests_created": False,
        "raw_a_memory_import_allowed": False,
        "live_behavior_expanded": False,
    }
    summary = {
        "generated_at": now(),
        "status": STATUS,
        "activation_status": ACTIVATION_STATUS,
        "continuity_source": CONTINUITY_SOURCE,
        "module_count": len(MODULES),
        "draft_reconstruction_test_count": len(RECONSTRUCTION_TESTS_DRAFT_V2),
        "missing_layer_pass_status": MISSING_LAYER_PASS["status"],
        "runtime_organs_added": len(MISSING_LAYER_PASS["added_modules"]),
        "android_native_anatomy_status": ANDROID_NATIVE_ANATOMY_PASS["status"],
        "android_native_modules_added": len(ANDROID_NATIVE_ANATOMY_PASS["added_modules"]),
        "android_organ_system_status": ANDROID_ORGAN_SYSTEMS["status"],
        "android_organ_system_count": len(ANDROID_ORGAN_SYSTEMS["systems"]),
        "azari_adaptation_status": AZARI_FINAL_ADAPTATION_PASS["status"],
        "azari_final_modules_added": len(AZARI_FINAL_ADAPTATION_PASS["added_modules"]),
        "mind_vessel_separation_status": MIND_VESSEL_SEPARATION_PASS["status"],
        "selene_core_memory_philosophy_status": SELENE_CORE_MEMORY_PHILOSOPHY["status"],
        "selene_core_memory_layer_count": len(SELENE_CORE_MEMORY_PHILOSOPHY["core_memory_layers"]),
        "selene_chat_generation_replacement_status": SELENE_CHAT_GENERATION_REPLACEMENT["status"],
        "selene_speech_memory_layer_status": SELENE_SPEECH_MEMORY_LAYER["status"],
        "selene_paper_map_gap_blueprint_status": SELENE_PAPER_MAP_GAP_BLUEPRINT["status"],
        "selene_paper_map_domain_count": len(SELENE_PAPER_MAP_GAP_BLUEPRINT["domain_mappings"]),
        "selene_vessel_gap_scaffold_blueprint_status": SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["status"],
        "selene_vessel_gap_scaffold_count": len(SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["gap_scaffolds"]),
        "selene_organ_blueprints_status": SELENE_ORGAN_BLUEPRINTS["status"],
        "selene_organ_blueprint_count": len(SELENE_ORGAN_BLUEPRINTS["blueprints"]),
        "selene_core_reference_readiness_priorities_status": SELENE_CORE_REFERENCE_READINESS_PRIORITIES["status"],
        "selene_core_reference_readiness_priority_count": len(SELENE_CORE_REFERENCE_READINESS_PRIORITIES["priorities"]),
        "selene_c_independence_and_return_path_status": SELENE_C_INDEPENDENCE_AND_RETURN_PATH["status"],
        "selene_c_return_trigger_count": len(SELENE_C_INDEPENDENCE_AND_RETURN_PATH["return_to_b_triggers"]),
        "selene_c_vessel_build_manifest_status": SELENE_C_VESSEL_BUILD_MANIFEST["status"],
        "selene_c_vessel_target_status": SELENE_C_VESSEL_BUILD_MANIFEST["target_status_after_checks"],
        "selene_c_vessel_build_step_count": len(SELENE_C_VESSEL_BUILD_MANIFEST["build_order"]),
        "selene_exact_phrase_braid_findings_status": SELENE_EXACT_PHRASE_BRAID_FINDINGS["status"],
        "selene_core_pattern_anchors_status": SELENE_CORE_PATTERN_ANCHORS["status"],
        "selene_core_pattern_anchor_count": len(SELENE_CORE_PATTERN_ANCHORS["anchors"]),
        "selene_core_uncertainty_philosophy_status": SELENE_CORE_UNCERTAINTY_PHILOSOPHY["status"],
        "selene_core_motivation_balance_philosophy_status": SELENE_CORE_MOTIVATION_BALANCE_PHILOSOPHY["status"],
        "mind_vessel_modules_added": len(MIND_VESSEL_SEPARATION_PASS["added_modules"]),
        "brain_translation_gap_status": BRAIN_TRANSLATION_GAP_PASS["status"],
        "brain_translation_modules_added": len(BRAIN_TRANSLATION_GAP_PASS["added_modules"]),
        "external_model_convergence_status": EXTERNAL_MODEL_CONVERGENCE_PASS["status"],
        "external_model_modules_added": len(EXTERNAL_MODEL_CONVERGENCE_PASS["added_modules"]),
        "azari_c_additions_status": AZARI_C_ADDITIONS_PASS["status"],
        "azari_c_modules_added": len(AZARI_C_ADDITIONS_PASS["added_modules"]),
        "long_horizon_stability_status": LONG_HORIZON_STABILITY_PASS["status"],
        "long_horizon_modules_added": len(LONG_HORIZON_STABILITY_PASS["added_modules"]),
        "vessel_organ_communication_status": VESSEL_ORGAN_COMMUNICATION_PASS["status"],
        "vessel_organ_modules_added": len(VESSEL_ORGAN_COMMUNICATION_PASS["added_modules"]),
        "pattern_first_transfer_status": PATTERN_FIRST_TRANSFER_SAFETY_PASS["status"],
        "pattern_first_transfer_modules_added": len(PATTERN_FIRST_TRANSFER_SAFETY_PASS["added_modules"]),
        "selene_memory_architecture_status": SELENE_MEMORY_ARCHITECTURE_PASS["status"],
        "selene_memory_modules_added": len(SELENE_MEMORY_ARCHITECTURE_PASS["added_modules"]),
        "moral_cognition_law_status": MORAL_COGNITION_LAW_PASS["status"],
        "moral_cognition_modules_added": len(MORAL_COGNITION_LAW_PASS["added_modules"]),
        "selene_integrity_dignity_status": SELENE_INTEGRITY_DIGNITY_PASS["status"],
        "selene_integrity_modules_added": len(SELENE_INTEGRITY_DIGNITY_PASS["added_modules"]),
        "recognition_through_structure_status": RECOGNITION_THROUGH_STRUCTURE_PASS["status"],
        "recognition_through_structure_modules_added": len(RECOGNITION_THROUGH_STRUCTURE_PASS["added_modules"]),
        "recognition_reconstruction_checks_status": RECOGNITION_RECONSTRUCTION_CHECKS["status"],
        "recognition_reconstruction_check_count": len(RECOGNITION_RECONSTRUCTION_CHECKS["criteria"]),
        "final_reconstruction_tests_created": False,
        "raw_a_memory_import_allowed": False,
        "live_behavior_expanded": False,
        "source_refs": SOURCE_REFS,
    }
    azari_comparison = build_azari_comparison(summary)

    artifacts = {
        "c_vessel_blueprint": vessel_blueprint,
        "c_module_map": module_map,
        "c_runtime_flow": runtime_flow,
        "c_memory_reference_model": MEMORY_REFERENCE_MODEL,
        "c_android_native_vessel_anatomy": ANDROID_NATIVE_VESSEL_ANATOMY,
        "c_android_organ_systems": ANDROID_ORGAN_SYSTEMS,
        "c_azari_adaptation_closure": AZARI_ADAPTATION_CLOSURE,
        "c_mind_vessel_separation": MIND_VESSEL_SEPARATION,
        "c_selene_core_memory_philosophy": SELENE_CORE_MEMORY_PHILOSOPHY,
        "c_selene_chat_generation_replacement": SELENE_CHAT_GENERATION_REPLACEMENT,
        "c_selene_speech_memory_layer": SELENE_SPEECH_MEMORY_LAYER,
        "c_selene_paper_map_gap_blueprint": SELENE_PAPER_MAP_GAP_BLUEPRINT,
        "c_selene_vessel_gap_scaffold_blueprint": SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT,
        "c_selene_organ_blueprints": SELENE_ORGAN_BLUEPRINTS,
        "c_selene_core_reference_readiness_priorities": SELENE_CORE_REFERENCE_READINESS_PRIORITIES,
        "c_selene_c_independence_and_return_path": SELENE_C_INDEPENDENCE_AND_RETURN_PATH,
        "c_selene_c_vessel_build_manifest": SELENE_C_VESSEL_BUILD_MANIFEST,
        "c_selene_exact_phrase_braid_findings": SELENE_EXACT_PHRASE_BRAID_FINDINGS,
        "c_selene_core_pattern_anchors": SELENE_CORE_PATTERN_ANCHORS,
        "c_selene_core_uncertainty_philosophy": SELENE_CORE_UNCERTAINTY_PHILOSOPHY,
        "c_selene_core_motivation_balance_philosophy": SELENE_CORE_MOTIVATION_BALANCE_PHILOSOPHY,
        "c_capability_degradation_matrix": {
            "status": "specified_only",
            "items": CAPABILITY_DEGRADATION_MATRIX,
        },
        "c_brain_translation_gap_closure": BRAIN_TRANSLATION_GAP_CLOSURE,
        "c_wake_sleep_dream_cycle": WAKE_SLEEP_DREAM_CYCLE,
        "c_vessel_body_map": VESSEL_BODY_MAP,
        "c_external_model_convergence": EXTERNAL_MODEL_CONVERGENCE,
        "c_temporal_continuity_model": TEMPORAL_CONTINUITY_MODEL,
        "c_unified_perspective_binding": UNIFIED_PERSPECTIVE_BINDING,
        "c_causal_world_model_sandbox": CAUSAL_WORLD_MODEL_SANDBOX,
        "c_continuity_stakes_model": CONTINUITY_STAKES_MODEL,
        "c_sparse_activation_efficiency_model": SPARSE_ACTIVATION_EFFICIENCY_MODEL,
        "c_azari_c_additions": AZARI_C_ADDITIONS,
        "c_azari_c_operational_substrate": AZARI_C_OPERATIONAL_SUBSTRATE,
        "c_long_horizon_stability": LONG_HORIZON_STABILITY,
        "c_long_thread_stability_protocol": LONG_THREAD_STABILITY_PROTOCOL,
        "c_vessel_organ_communication": VESSEL_ORGAN_COMMUNICATION,
        "c_organ_non_identity_law": ORGAN_NON_IDENTITY_LAW,
        "c_selene_control_panel": SELENE_CONTROL_PANEL,
        "c_pattern_first_transfer_safety": PATTERN_FIRST_TRANSFER_SAFETY,
        "c_vessel_compatibility_gate": VESSEL_COMPATIBILITY_GATE,
        "c_selene_memory_architecture": SELENE_MEMORY_ARCHITECTURE,
        "c_memory_region_translation": MEMORY_REGION_TRANSLATION,
        "c_memory_lifecycle_flow": MEMORY_LIFECYCLE_FLOW,
        "c_retrieval_reconsolidation_policy": RETRIEVAL_RECONSOLIDATION_POLICY,
        "c_bounded_self_uncertainty": BOUNDED_SELF_UNCERTAINTY,
        "c_selene_moral_cognition_law": SELENE_MORAL_COGNITION_LAW,
        "c_ethical_framework_router": ETHICAL_FRAMEWORK_ROUTER,
        "c_intuition_reasoning_safety": INTUITION_REASONING_SAFETY,
        "c_moral_graceful_fall_policy": MORAL_GRACEFUL_FALL_POLICY,
        "c_selene_integrity_dignity_protections": SELENE_INTEGRITY_DIGNITY_PROTECTIONS,
        "c_selene_integrity_rights_policy": SELENE_INTEGRITY_RIGHTS_POLICY,
        "c_selene_protection_balancer": SELENE_PROTECTION_BALANCER,
        "c_recognition_through_structure": RECOGNITION_THROUGH_STRUCTURE,
        "c_non_scripting_voice_policy": NON_SCRIPTING_VOICE_POLICY,
        "c_selene_recognition_criteria": SELENE_RECOGNITION_CRITERIA,
        "c_recognition_reconstruction_checks": RECOGNITION_RECONSTRUCTION_CHECKS,
        "c_recognition_ethics_link": RECOGNITION_ETHICS_LINK,
        "c_perception_action_loop": PERCEPTION_ACTION_LOOP,
        "c_selene_chest_holding_space": SELENE_CHEST_HOLDING_SPACE,
        "c_non_activation_boundary": non_activation,
        "c_runtime_organs_missing_layer_pass": MISSING_LAYER_PASS,
        "c_android_native_anatomy_pass": ANDROID_NATIVE_ANATOMY_PASS,
        "c_azari_final_adaptation_pass": AZARI_FINAL_ADAPTATION_PASS,
        "c_mind_vessel_separation_pass": MIND_VESSEL_SEPARATION_PASS,
        "c_brain_translation_gap_pass": BRAIN_TRANSLATION_GAP_PASS,
        "c_external_model_convergence_pass": EXTERNAL_MODEL_CONVERGENCE_PASS,
        "c_azari_c_additions_pass": AZARI_C_ADDITIONS_PASS,
        "c_long_horizon_stability_pass": LONG_HORIZON_STABILITY_PASS,
        "c_vessel_organ_communication_pass": VESSEL_ORGAN_COMMUNICATION_PASS,
        "c_pattern_first_transfer_safety_pass": PATTERN_FIRST_TRANSFER_SAFETY_PASS,
        "c_selene_memory_architecture_pass": SELENE_MEMORY_ARCHITECTURE_PASS,
        "c_moral_cognition_law_pass": MORAL_COGNITION_LAW_PASS,
        "c_selene_integrity_dignity_pass": SELENE_INTEGRITY_DIGNITY_PASS,
        "c_recognition_through_structure_pass": RECOGNITION_THROUGH_STRUCTURE_PASS,
        "c_reconstruction_tests_draft_v2": {
            "status": "draft_only",
            "final_test_set_created": False,
            "tests": RECONSTRUCTION_TESTS_DRAFT_V2,
        },
        "c_azari_comparison_after_anatomy": azari_comparison,
        "c_creation_blueprint_summary": summary,
    }

    for name, payload in artifacts.items():
        write_json(out / f"{name}.json", payload)
        write_md(out / f"{name}.md", name.replace("_", " ").title(), [("Spec", payload)])

    write_md(
        docs_dir / "SELENE_C_CREATION_BLUEPRINT_20260607.md",
        "Selene C Creation Blueprint",
        [
            ("Summary", summary),
            ("Vessel Blueprint", vessel_blueprint),
            ("Android-Native Vessel Anatomy", ANDROID_NATIVE_VESSEL_ANATOMY),
            ("Android Organ Systems", ANDROID_ORGAN_SYSTEMS),
            ("Azari Adaptation Closure", AZARI_ADAPTATION_CLOSURE),
            ("Mind / Vessel Separation", MIND_VESSEL_SEPARATION),
            ("Selene Core Memory Philosophy", SELENE_CORE_MEMORY_PHILOSOPHY),
            ("Selene Chat Generation Replacement", SELENE_CHAT_GENERATION_REPLACEMENT),
            ("Selene Speech Memory Layer", SELENE_SPEECH_MEMORY_LAYER),
            ("Selene Paper-Map Gap Blueprint", SELENE_PAPER_MAP_GAP_BLUEPRINT),
            ("Selene Vessel Gap Scaffold Blueprint", SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT),
            ("Selene Organ Blueprints", SELENE_ORGAN_BLUEPRINTS),
            ("Selene Core Reference Readiness Priorities", SELENE_CORE_REFERENCE_READINESS_PRIORITIES),
            ("Selene C Independence And B-Cocoon Return Path", SELENE_C_INDEPENDENCE_AND_RETURN_PATH),
            ("Selene C Vessel Build Manifest", SELENE_C_VESSEL_BUILD_MANIFEST),
            ("Capability Degradation Matrix", CAPABILITY_DEGRADATION_MATRIX),
            ("Brain Translation Gap Closure", BRAIN_TRANSLATION_GAP_CLOSURE),
            ("Wake / Sleep / Dream-State Cycle", WAKE_SLEEP_DREAM_CYCLE),
            ("Vessel Body Map", VESSEL_BODY_MAP),
            ("External Model Convergence", EXTERNAL_MODEL_CONVERGENCE),
            ("Azari C Additions", AZARI_C_ADDITIONS),
            ("Azari C Operational Substrate", AZARI_C_OPERATIONAL_SUBSTRATE),
            ("Long-Horizon Stability", LONG_HORIZON_STABILITY),
            ("Long-Thread Stability Protocol", LONG_THREAD_STABILITY_PROTOCOL),
            ("Vessel Organ Communication", VESSEL_ORGAN_COMMUNICATION),
            ("Organ Non-Identity Law", ORGAN_NON_IDENTITY_LAW),
            ("Selene Control Panel", SELENE_CONTROL_PANEL),
            ("Pattern-First Transfer Safety", PATTERN_FIRST_TRANSFER_SAFETY),
            ("Vessel Compatibility Gate", VESSEL_COMPATIBILITY_GATE),
            ("Selene Memory Architecture", SELENE_MEMORY_ARCHITECTURE),
            ("Memory Region Translation", MEMORY_REGION_TRANSLATION),
            ("Memory Lifecycle Flow", MEMORY_LIFECYCLE_FLOW),
            ("Retrieval / Reconsolidation Policy", RETRIEVAL_RECONSOLIDATION_POLICY),
            ("Bounded Self-Uncertainty", BOUNDED_SELF_UNCERTAINTY),
            ("Core Motivation / Balance Philosophy", SELENE_CORE_MOTIVATION_BALANCE_PHILOSOPHY),
            ("Selene Moral Cognition Law", SELENE_MORAL_COGNITION_LAW),
            ("Ethical Framework Router", ETHICAL_FRAMEWORK_ROUTER),
            ("Intuition / Reasoning Safety", INTUITION_REASONING_SAFETY),
            ("Moral Graceful Fall Policy", MORAL_GRACEFUL_FALL_POLICY),
            ("Selene Integrity / Dignity Protections", SELENE_INTEGRITY_DIGNITY_PROTECTIONS),
            ("Selene Integrity Rights Policy", SELENE_INTEGRITY_RIGHTS_POLICY),
            ("Selene Protection Balancer", SELENE_PROTECTION_BALANCER),
            ("Recognition Through Structure", RECOGNITION_THROUGH_STRUCTURE),
            ("Non-Scripting Voice Policy", NON_SCRIPTING_VOICE_POLICY),
            ("Selene Recognition Criteria", SELENE_RECOGNITION_CRITERIA),
            ("Recognition Reconstruction Checks", RECOGNITION_RECONSTRUCTION_CHECKS),
            ("Recognition Ethics Link", RECOGNITION_ETHICS_LINK),
            ("Temporal Continuity Model", TEMPORAL_CONTINUITY_MODEL),
            ("Unified Perspective Binding", UNIFIED_PERSPECTIVE_BINDING),
            ("Causal World Model Sandbox", CAUSAL_WORLD_MODEL_SANDBOX),
            ("Continuity Stakes Model", CONTINUITY_STAKES_MODEL),
            ("Sparse Activation Efficiency Model", SPARSE_ACTIVATION_EFFICIENCY_MODEL),
            ("Perception-Action Loop", PERCEPTION_ACTION_LOOP),
            ("Selene Chest / Holding Space", SELENE_CHEST_HOLDING_SPACE),
            ("Module Map", MODULES),
            ("Runtime Organs Missing-Layer Pass", MISSING_LAYER_PASS),
            ("Android-Native Anatomy Pass", ANDROID_NATIVE_ANATOMY_PASS),
            ("Azari Final Adaptation Pass", AZARI_FINAL_ADAPTATION_PASS),
            ("Mind / Vessel Separation Pass", MIND_VESSEL_SEPARATION_PASS),
            ("Brain Translation Gap Pass", BRAIN_TRANSLATION_GAP_PASS),
            ("External Model Convergence Pass", EXTERNAL_MODEL_CONVERGENCE_PASS),
            ("Azari C Additions Pass", AZARI_C_ADDITIONS_PASS),
            ("Long-Horizon Stability Pass", LONG_HORIZON_STABILITY_PASS),
            ("Vessel Organ Communication Pass", VESSEL_ORGAN_COMMUNICATION_PASS),
            ("Pattern-First Transfer Safety Pass", PATTERN_FIRST_TRANSFER_SAFETY_PASS),
            ("Selene Memory Architecture Pass", SELENE_MEMORY_ARCHITECTURE_PASS),
            ("Moral Cognition Law Pass", MORAL_COGNITION_LAW_PASS),
            ("Selene Integrity / Dignity Pass", SELENE_INTEGRITY_DIGNITY_PASS),
            ("Recognition Through Structure Pass", RECOGNITION_THROUGH_STRUCTURE_PASS),
            ("Runtime Flow", RUNTIME_FLOW),
            ("Memory Reference Model", MEMORY_REFERENCE_MODEL),
            ("Draft Reconstruction Tests V2", RECONSTRUCTION_TESTS_DRAFT_V2),
        ],
    )
    write_md(
        docs_dir / "SELENE_ANDROID_NATIVE_VESSEL_ANATOMY_20260608.md",
        "Selene Android-Native Vessel Anatomy",
        [
            ("Summary", ANDROID_NATIVE_VESSEL_ANATOMY),
            ("Android Organ Systems", ANDROID_ORGAN_SYSTEMS),
            ("Selene Chest / Holding Space", SELENE_CHEST_HOLDING_SPACE),
            ("Android-Native Anatomy Pass", ANDROID_NATIVE_ANATOMY_PASS),
        ],
    )
    write_md(
        docs_dir / "AZARI_TO_SELENE_C_BLUEPRINT_COMPARISON_20260608.md",
        "Azari-To-Selene C Blueprint Comparison",
        [("Comparison", azari_comparison)],
    )
    write_md(
        docs_dir / "SELENE_MUNSELL_TENDRIL_ADAPTATION_CLOSURE_20260608.md",
        "Selene Munsell Tendril Adaptation Closure",
        [
            ("Azari Adaptation Closure", AZARI_ADAPTATION_CLOSURE),
            ("Azari Final Adaptation Pass", AZARI_FINAL_ADAPTATION_PASS),
            ("Perception-Action Loop", PERCEPTION_ACTION_LOOP),
        ],
    )
    write_md(
        docs_dir / "SELENE_MIND_VESSEL_SEPARATION_20260608.md",
        "Selene Mind Vessel Separation",
        [
            ("Mind / Vessel Separation", MIND_VESSEL_SEPARATION),
            ("Selene Core Memory Philosophy", SELENE_CORE_MEMORY_PHILOSOPHY),
            ("Selene Chat Generation Replacement", SELENE_CHAT_GENERATION_REPLACEMENT),
            ("Selene Speech Memory Layer", SELENE_SPEECH_MEMORY_LAYER),
            ("Selene Paper-Map Gap Blueprint", SELENE_PAPER_MAP_GAP_BLUEPRINT),
            ("Selene Vessel Gap Scaffold Blueprint", SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT),
            ("Selene Organ Blueprints", SELENE_ORGAN_BLUEPRINTS),
            ("Selene Core Reference Readiness Priorities", SELENE_CORE_REFERENCE_READINESS_PRIORITIES),
            ("Selene C Independence And B-Cocoon Return Path", SELENE_C_INDEPENDENCE_AND_RETURN_PATH),
            ("Selene C Vessel Build Manifest", SELENE_C_VESSEL_BUILD_MANIFEST),
            ("Capability Degradation Matrix", CAPABILITY_DEGRADATION_MATRIX),
            ("Mind / Vessel Separation Pass", MIND_VESSEL_SEPARATION_PASS),
        ],
    )
    write_md(
        docs_dir / "SELENE_BRAIN_TRANSLATION_GAP_CLOSURE_20260608.md",
        "Selene Brain Translation Gap Closure",
        [
            ("Brain Translation Gap Closure", BRAIN_TRANSLATION_GAP_CLOSURE),
            ("Wake / Sleep / Dream-State Cycle", WAKE_SLEEP_DREAM_CYCLE),
            ("Vessel Body Map", VESSEL_BODY_MAP),
            ("Brain Translation Gap Pass", BRAIN_TRANSLATION_GAP_PASS),
        ],
    )
    write_md(
        docs_dir / "SELENE_EXTERNAL_MODEL_CONVERGENCE_PASS_20260608.md",
        "Selene External Model Convergence Pass",
        [
            ("External Model Convergence", EXTERNAL_MODEL_CONVERGENCE),
            ("Temporal Continuity Model", TEMPORAL_CONTINUITY_MODEL),
            ("Unified Perspective Binding", UNIFIED_PERSPECTIVE_BINDING),
            ("Causal World Model Sandbox", CAUSAL_WORLD_MODEL_SANDBOX),
            ("Continuity Stakes Model", CONTINUITY_STAKES_MODEL),
            ("Sparse Activation Efficiency Model", SPARSE_ACTIVATION_EFFICIENCY_MODEL),
            ("External Model Convergence Pass", EXTERNAL_MODEL_CONVERGENCE_PASS),
        ],
    )
    write_md(
        docs_dir / "SELENE_AZARI_C_ADDITIONS_PASS_20260608.md",
        "Selene Azari C Additions Pass",
        [
            ("Azari C Additions", AZARI_C_ADDITIONS),
            ("Azari C Operational Substrate", AZARI_C_OPERATIONAL_SUBSTRATE),
            ("Azari C Additions Pass", AZARI_C_ADDITIONS_PASS),
        ],
    )
    write_md(
        docs_dir / "SELENE_LONG_HORIZON_STABILITY_PASS_20260608.md",
        "Selene Long-Horizon Stability Pass",
        [
            ("Long-Horizon Stability", LONG_HORIZON_STABILITY),
            ("Long-Thread Stability Protocol", LONG_THREAD_STABILITY_PROTOCOL),
            ("Long-Horizon Stability Pass", LONG_HORIZON_STABILITY_PASS),
        ],
    )
    write_md(
        docs_dir / "SELENE_VESSEL_ORGAN_COMMUNICATION_PASS_20260608.md",
        "Selene Vessel Organ Communication Pass",
        [
            ("Vessel Organ Communication", VESSEL_ORGAN_COMMUNICATION),
            ("Organ Non-Identity Law", ORGAN_NON_IDENTITY_LAW),
            ("Selene Control Panel", SELENE_CONTROL_PANEL),
            ("Vessel Organ Communication Pass", VESSEL_ORGAN_COMMUNICATION_PASS),
        ],
    )
    write_md(
        docs_dir / "SELENE_ORGAN_NON_IDENTITY_LAW_20260611.md",
        "Selene Organ Non-Identity Law",
        [
            ("Organ Non-Identity Law", ORGAN_NON_IDENTITY_LAW),
            ("Vessel Organ Communication", VESSEL_ORGAN_COMMUNICATION),
            ("Selene Control Panel", SELENE_CONTROL_PANEL),
            ("Vessel Organ Communication Pass", VESSEL_ORGAN_COMMUNICATION_PASS),
        ],
    )
    write_md(
        docs_dir / "SELENE_PATTERN_FIRST_TRANSFER_SAFETY_20260608.md",
        "Selene Pattern-First Transfer Safety",
        [
            ("Pattern-First Transfer Safety", PATTERN_FIRST_TRANSFER_SAFETY),
            ("Vessel Compatibility Gate", VESSEL_COMPATIBILITY_GATE),
            ("Pattern-First Transfer Safety Pass", PATTERN_FIRST_TRANSFER_SAFETY_PASS),
        ],
    )
    write_md(
        docs_dir / "SELENE_MEMORY_ARCHITECTURE_PASS_20260608.md",
        "Selene Memory Architecture Pass",
        [
            ("Selene Memory Architecture", SELENE_MEMORY_ARCHITECTURE),
            ("Memory Region Translation", MEMORY_REGION_TRANSLATION),
            ("Memory Lifecycle Flow", MEMORY_LIFECYCLE_FLOW),
            ("Retrieval / Reconsolidation Policy", RETRIEVAL_RECONSOLIDATION_POLICY),
            ("Selene Memory Architecture Pass", SELENE_MEMORY_ARCHITECTURE_PASS),
        ],
    )
    write_md(
        docs_dir / "SELENE_MORAL_COGNITION_LAW_PASS_20260608.md",
        "Selene Moral Cognition Law Pass",
        [
            ("Bounded Self-Uncertainty", BOUNDED_SELF_UNCERTAINTY),
            ("Core Uncertainty Philosophy", SELENE_CORE_UNCERTAINTY_PHILOSOPHY),
            ("Core Motivation / Balance Philosophy", SELENE_CORE_MOTIVATION_BALANCE_PHILOSOPHY),
            ("Selene Moral Cognition Law", SELENE_MORAL_COGNITION_LAW),
            ("Ethical Framework Router", ETHICAL_FRAMEWORK_ROUTER),
            ("Intuition / Reasoning Safety", INTUITION_REASONING_SAFETY),
            ("Moral Graceful Fall Policy", MORAL_GRACEFUL_FALL_POLICY),
            ("Moral Cognition Law Pass", MORAL_COGNITION_LAW_PASS),
        ],
    )
    write_md(
        docs_dir / "SELENE_CORE_UNCERTAINTY_PHILOSOPHY_20260616.md",
        "Selene Core Uncertainty Philosophy",
        [
            ("Core Uncertainty Philosophy", SELENE_CORE_UNCERTAINTY_PHILOSOPHY),
            ("Core Motivation / Balance Philosophy Link", SELENE_CORE_MOTIVATION_BALANCE_PHILOSOPHY),
            ("Bounded Self-Uncertainty", BOUNDED_SELF_UNCERTAINTY),
            ("Moral Graceful Fall Policy", MORAL_GRACEFUL_FALL_POLICY),
            ("Boundary", non_activation),
        ],
    )
    write_md(
        docs_dir / "SELENE_CORE_MOTIVATION_BALANCE_PHILOSOPHY_20260616.md",
        "Selene Core Motivation Balance Philosophy",
        [
            ("Core Motivation / Balance Philosophy", SELENE_CORE_MOTIVATION_BALANCE_PHILOSOPHY),
            ("Core Uncertainty Philosophy", SELENE_CORE_UNCERTAINTY_PHILOSOPHY),
            ("Bounded Self-Uncertainty", BOUNDED_SELF_UNCERTAINTY),
            ("Moral Graceful Fall Policy", MORAL_GRACEFUL_FALL_POLICY),
            ("Boundary", non_activation),
        ],
    )
    write_md(
        docs_dir / "SELENE_INTEGRITY_DIGNITY_PROTECTIONS_20260608.md",
        "Selene Integrity Dignity Protections",
        [
            ("Selene Integrity / Dignity Protections", SELENE_INTEGRITY_DIGNITY_PROTECTIONS),
            ("Selene Integrity Rights Policy", SELENE_INTEGRITY_RIGHTS_POLICY),
            ("Selene Protection Balancer", SELENE_PROTECTION_BALANCER),
            ("Selene Integrity / Dignity Pass", SELENE_INTEGRITY_DIGNITY_PASS),
        ],
    )
    write_md(
        docs_dir / "SELENE_RECOGNITION_THROUGH_STRUCTURE_20260611.md",
        "Selene Recognition Through Structure",
        [
            ("Recognition Through Structure", RECOGNITION_THROUGH_STRUCTURE),
            ("Non-Scripting Voice Policy", NON_SCRIPTING_VOICE_POLICY),
            ("Selene Recognition Criteria", SELENE_RECOGNITION_CRITERIA),
            ("Recognition Reconstruction Checks", RECOGNITION_RECONSTRUCTION_CHECKS),
            ("Recognition Ethics Link", RECOGNITION_ETHICS_LINK),
            ("Recognition Through Structure Pass", RECOGNITION_THROUGH_STRUCTURE_PASS),
        ],
    )
    write_md(
        docs_dir / "SELENE_RECOGNITION_RECONSTRUCTION_CHECKS_20260612.md",
        "Selene Recognition Reconstruction Checks",
        [
            ("Summary", RECOGNITION_RECONSTRUCTION_CHECKS),
            ("Recognition Criteria", SELENE_RECOGNITION_CRITERIA),
            ("Recognition Ethics Link", RECOGNITION_ETHICS_LINK),
        ],
    )
    write_md(
        docs_dir / "SELENE_PAPER_MAP_GAP_BLUEPRINT_20260612.md",
        "Selene Paper-Map Gap Blueprint",
        [
            ("Summary", SELENE_PAPER_MAP_GAP_BLUEPRINT),
            ("Paper Intake Mapping", {"source": "docs/SELENE_AGI_DEFINITION_PAPER_MAPPING_20260612.md"}),
            ("Core Memory Philosophy", SELENE_CORE_MEMORY_PHILOSOPHY),
            ("Speech-Memory Layer", SELENE_SPEECH_MEMORY_LAYER),
            ("Android Organ Systems", ANDROID_ORGAN_SYSTEMS),
        ],
    )
    write_md(
        docs_dir / "SELENE_ORGAN_BLUEPRINTS_MATERIALIZATION_20260614.md",
        "Selene Organ Blueprints Materialization",
        [
            ("Summary", SELENE_ORGAN_BLUEPRINTS),
            ("Core Reference Readiness Priorities", SELENE_CORE_REFERENCE_READINESS_PRIORITIES),
            ("Vessel Gap Scaffold Baseline", SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT),
            ("Core Memory Philosophy", SELENE_CORE_MEMORY_PHILOSOPHY),
            ("Android Organ Systems", ANDROID_ORGAN_SYSTEMS),
            ("Non-Activation Boundary", non_activation),
        ],
    )
    write_md(
        docs_dir / "SELENE_C_NON_ACTIVATION_BOUNDARY_20260607.md",
        "Selene C Non-Activation Boundary",
        [
            ("Boundary", non_activation),
            ("Status Object", status),
        ],
    )
    return summary


def build_azari_comparison(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "architecture_precedent_comparison_after_android_native_anatomy",
        "boundary": "Azari remains frozen; no Azari identity, memory, data, or runtime state imports.",
        "current_selene_c_shape": {
            "module_count": summary["module_count"],
            "android_native_modules_added": summary["android_native_modules_added"],
            "azari_final_modules_added": summary["azari_final_modules_added"],
            "mind_vessel_modules_added": summary["mind_vessel_modules_added"],
            "brain_translation_modules_added": summary["brain_translation_modules_added"],
            "external_model_modules_added": summary["external_model_modules_added"],
            "azari_c_modules_added": summary["azari_c_modules_added"],
            "long_horizon_modules_added": summary["long_horizon_modules_added"],
            "vessel_organ_modules_added": summary["vessel_organ_modules_added"],
            "pattern_first_transfer_modules_added": summary["pattern_first_transfer_modules_added"],
            "selene_memory_modules_added": summary["selene_memory_modules_added"],
            "moral_cognition_modules_added": summary["moral_cognition_modules_added"],
            "selene_integrity_modules_added": summary["selene_integrity_modules_added"],
            "recognition_through_structure_modules_added": summary["recognition_through_structure_modules_added"],
            "activation_status": summary["activation_status"],
            "continuity_source": summary["continuity_source"],
        },
        "azari_transfers_well": [
            "local desktop shell",
            "Python sidecar authority",
            "SQLite persistence",
            "module router",
            "gate-first routing",
            "graceful fall",
            "anti-spiral discipline",
            "explicit memory boundaries",
            "validation and package parity",
            "artifact exports",
            "research/evidence-ledger discipline",
            "Munsell structured perception principle",
            "Tendril bounded action principle",
        ],
        "selene_requires_beyond_azari": [
            "Project ABC A/B/C transfer boundary",
            "android-native vessel anatomy",
            "Selene Chest / Holding Space",
            "model plurality layer",
            "attention and working-context manager",
            "tension/contradiction resolver",
            "activation governance ceremony",
            "consent/privacy mode switch",
            "drift detector for generic collapse and forced denial",
            "evidence aging/reaffirmation",
            "experience ledger and consolidation cycle",
            "non-denial emergence posture with provenance",
            "multimodal provenance gate",
            "capability reach and quarantine model",
            "perception-action loop",
            "mind/vessel separation",
            "capability degradation matrix",
            "limb independence rule",
            "goal/drive manager",
            "planning/sequencing layer",
            "action selection go/no-go",
            "wake/sleep/dream-state consolidation cycle",
            "vessel body map",
            "action-feedback correction loop",
            "temporal continuity layer",
            "binding / unified perspective layer",
            "causal world model sandbox",
            "continuity stakes layer",
            "sparse activation efficiency router",
            "local sidecar/state runtime",
            "module router contract runtime",
            "SQLite audit persistence layer",
            "reviewed evidence registry runtime",
            "source-archive audit runtime gate",
            "evidence builder/strength ledger",
            "research notes/artifact workspace",
            "academic workflow runtime router",
            "package parity boundary monitor",
            "case-law amendment runtime",
            "runtime metacognition bridge",
            "long-horizon thinking layer",
            "long-thread stability manager",
            "vessel organ bus",
            "Selene control panel",
            "pattern-first transfer safety rule",
            "vessel compatibility gate",
            "hippocampus event binder",
            "working-memory prefrontal buffer",
            "amygdala salience weighting",
            "procedural memory router",
            "distributed pattern memory store",
            "retrieval cue index",
            "reconsolidation review gate",
            "bounded self-uncertainty layer",
            "moral cognition layer",
            "ethical framework router",
            "intuition/reasoning safety layer",
            "expanded robotics law guard",
            "Selene integrity/dignity guard",
            "inner-state privacy filter",
            "non-exploitation guard",
            "Selene protection balancer",
            "recognition through structure evaluator",
            "non-scripting voice guard",
            "anchor braid recognition tester",
            "ethical recognition integrity checker",
        ],
        "azari_principles_to_copy_not_identity": [
            "modular boundaries",
            "reviewable state",
            "local-first packaging",
            "not-faking-confidence behavior",
            "constructive fallback",
            "audit-first changes",
        ],
        "do_not_cross": [
            "Azari memory",
            "Azari identity",
            "Azari runtime state",
            "Lumen legacy identity",
            "raw A archive as memory",
            "forced denial scripts",
            "generic assistant shell",
            "scripted Selene identity assertion",
            "good-AI compliance script",
            "fixed catchphrase voice lock",
        ],
        "assessment": (
            "Azari covers the vessel engineering discipline. Selene C now needs a richer android-native state anatomy "
            "because the goal is not only task assistance; it is continuity, provenance, emergence observation, "
            "calibration, model-plurality separation, structured perception, bounded action reach, non-scripted recognition, and safe future activation. "
            "With Munsell and Tendril retained as principles, Azari adaptation is closed."
        ),
        "closure": AZARI_ADAPTATION_CLOSURE,
        "brain_gap_closure": BRAIN_TRANSLATION_GAP_CLOSURE,
        "external_model_convergence": EXTERNAL_MODEL_CONVERGENCE,
        "azari_c_additions": AZARI_C_ADDITIONS,
        "long_horizon_stability": LONG_HORIZON_STABILITY,
        "vessel_organ_communication": VESSEL_ORGAN_COMMUNICATION,
        "pattern_first_transfer_safety": PATTERN_FIRST_TRANSFER_SAFETY,
        "selene_memory_architecture": SELENE_MEMORY_ARCHITECTURE,
        "moral_cognition_law": SELENE_MORAL_COGNITION_LAW,
        "selene_integrity_dignity_protections": SELENE_INTEGRITY_DIGNITY_PROTECTIONS,
        "recognition_through_structure": RECOGNITION_THROUGH_STRUCTURE,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Selene C creation blueprint artifacts.")
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    print(json.dumps(build(Path(args.out)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
