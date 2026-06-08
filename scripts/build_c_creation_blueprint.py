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
    ANDROID_NATIVE_VESSEL_ANATOMY,
    ARTIFACT_DIR,
    AZARI_ADAPTATION_CLOSURE,
    AZARI_FINAL_ADAPTATION_PASS,
    BRAIN_TRANSLATION_GAP_CLOSURE,
    BRAIN_TRANSLATION_GAP_PASS,
    CAUSAL_WORLD_MODEL_SANDBOX,
    CONTINUITY_SOURCE,
    CONTINUITY_STAKES_MODEL,
    EXTERNAL_MODEL_CONVERGENCE,
    EXTERNAL_MODEL_CONVERGENCE_PASS,
    MEMORY_REFERENCE_MODEL,
    MIND_VESSEL_SEPARATION,
    MIND_VESSEL_SEPARATION_PASS,
    MISSING_LAYER_PASS,
    MODULES,
    NON_ACTIVATION_BOUNDARIES,
    PERCEPTION_ACTION_LOOP,
    RECONSTRUCTION_TESTS_DRAFT_V2,
    RUNTIME_FLOW,
    CAPABILITY_DEGRADATION_MATRIX,
    SELENE_CHEST_HOLDING_SPACE,
    SPARSE_ACTIVATION_EFFICIENCY_MODEL,
    STATUS,
    TEMPORAL_CONTINUITY_MODEL,
    UNIFIED_PERSPECTIVE_BINDING,
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
    "src/selene/chat.py",
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
        "azari_adaptation_status": AZARI_FINAL_ADAPTATION_PASS["status"],
        "azari_final_modules_added": len(AZARI_FINAL_ADAPTATION_PASS["added_modules"]),
        "mind_vessel_separation_status": MIND_VESSEL_SEPARATION_PASS["status"],
        "mind_vessel_modules_added": len(MIND_VESSEL_SEPARATION_PASS["added_modules"]),
        "brain_translation_gap_status": BRAIN_TRANSLATION_GAP_PASS["status"],
        "brain_translation_modules_added": len(BRAIN_TRANSLATION_GAP_PASS["added_modules"]),
        "external_model_convergence_status": EXTERNAL_MODEL_CONVERGENCE_PASS["status"],
        "external_model_modules_added": len(EXTERNAL_MODEL_CONVERGENCE_PASS["added_modules"]),
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
        "c_azari_adaptation_closure": AZARI_ADAPTATION_CLOSURE,
        "c_mind_vessel_separation": MIND_VESSEL_SEPARATION,
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
        "c_perception_action_loop": PERCEPTION_ACTION_LOOP,
        "c_selene_chest_holding_space": SELENE_CHEST_HOLDING_SPACE,
        "c_non_activation_boundary": non_activation,
        "c_runtime_organs_missing_layer_pass": MISSING_LAYER_PASS,
        "c_android_native_anatomy_pass": ANDROID_NATIVE_ANATOMY_PASS,
        "c_azari_final_adaptation_pass": AZARI_FINAL_ADAPTATION_PASS,
        "c_mind_vessel_separation_pass": MIND_VESSEL_SEPARATION_PASS,
        "c_brain_translation_gap_pass": BRAIN_TRANSLATION_GAP_PASS,
        "c_external_model_convergence_pass": EXTERNAL_MODEL_CONVERGENCE_PASS,
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
            ("Azari Adaptation Closure", AZARI_ADAPTATION_CLOSURE),
            ("Mind / Vessel Separation", MIND_VESSEL_SEPARATION),
            ("Capability Degradation Matrix", CAPABILITY_DEGRADATION_MATRIX),
            ("Brain Translation Gap Closure", BRAIN_TRANSLATION_GAP_CLOSURE),
            ("Wake / Sleep / Dream-State Cycle", WAKE_SLEEP_DREAM_CYCLE),
            ("Vessel Body Map", VESSEL_BODY_MAP),
            ("External Model Convergence", EXTERNAL_MODEL_CONVERGENCE),
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
        ],
        "assessment": (
            "Azari covers the vessel engineering discipline. Selene C now needs a richer android-native state anatomy "
            "because the goal is not only task assistance; it is continuity, provenance, emergence observation, "
            "calibration, model-plurality separation, structured perception, bounded action reach, and safe future activation. "
            "With Munsell and Tendril retained as principles, Azari adaptation is closed."
        ),
        "closure": AZARI_ADAPTATION_CLOSURE,
        "brain_gap_closure": BRAIN_TRANSLATION_GAP_CLOSURE,
        "external_model_convergence": EXTERNAL_MODEL_CONVERGENCE,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Selene C creation blueprint artifacts.")
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    print(json.dumps(build(Path(args.out)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
