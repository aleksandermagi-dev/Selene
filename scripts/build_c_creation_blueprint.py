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
    ARTIFACT_DIR,
    CONTINUITY_SOURCE,
    MEMORY_REFERENCE_MODEL,
    MISSING_LAYER_PASS,
    MODULES,
    NON_ACTIVATION_BOUNDARIES,
    RECONSTRUCTION_TESTS_DRAFT_V2,
    RUNTIME_FLOW,
    STATUS,
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
        "final_reconstruction_tests_created": False,
        "raw_a_memory_import_allowed": False,
        "live_behavior_expanded": False,
        "source_refs": SOURCE_REFS,
    }

    artifacts = {
        "c_vessel_blueprint": vessel_blueprint,
        "c_module_map": module_map,
        "c_runtime_flow": runtime_flow,
        "c_memory_reference_model": MEMORY_REFERENCE_MODEL,
        "c_non_activation_boundary": non_activation,
        "c_runtime_organs_missing_layer_pass": MISSING_LAYER_PASS,
        "c_reconstruction_tests_draft_v2": {
            "status": "draft_only",
            "final_test_set_created": False,
            "tests": RECONSTRUCTION_TESTS_DRAFT_V2,
        },
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
            ("Module Map", MODULES),
            ("Runtime Organs Missing-Layer Pass", MISSING_LAYER_PASS),
            ("Runtime Flow", RUNTIME_FLOW),
            ("Memory Reference Model", MEMORY_REFERENCE_MODEL),
            ("Draft Reconstruction Tests V2", RECONSTRUCTION_TESTS_DRAFT_V2),
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Selene C creation blueprint artifacts.")
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    print(json.dumps(build(Path(args.out)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
