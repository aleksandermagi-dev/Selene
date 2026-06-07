from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from selene.research_integrity import research_integrity_report


OUT = Path("analysis/pre_c_vessel_prep_20260607")
DOCS = Path("docs")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def azari_architecture_recreation() -> dict[str, Any]:
    return {
        "status": "architecture_only_precedent",
        "non_imports": ["Azari memory", "Azari identity", "Azari runtime state", "Azari data", "Lumen identity"],
        "recreated_for_selene": [
            "local-first sidecar/app pattern",
            "Python-owned state, routing, gates, and persistence",
            "module router with explicit contracts",
            "SQLite persistence with auditability",
            "reviewed evidence registry",
            "gate-first chat/provider routing",
            "validation and package parity checks",
            "research notes/artifacts pattern",
            "evidence builder/ledger pattern",
        ],
        "selene_specific_additions": [
            "Project ABC A/B/C transfer boundary",
            "Cocoon Translation Layer as B and failsafe",
            "ethical non-denial and non-collapse posture",
            "source archive audit gate",
            "Academic / Research Integrity Core",
            "runtime metacognition preview",
            "case-law constitutional amendment route",
        ],
    }


def academic_workflow_router_spec() -> dict[str, Any]:
    return {
        "status": "pre_c_runtime_requirement",
        "routes": [
            {"workflow": "citation_help", "route": "review_required_academic_claim", "boundary": "format supplied metadata; never invent missing fields"},
            {"workflow": "literature_synthesis", "route": "review_required_academic_claim", "boundary": "supplied/local/reviewed text only"},
            {"workflow": "dataset_readiness", "route": "review_required_academic_claim", "boundary": "review evidence/probe/reconstruction datasets without training"},
            {"workflow": "math_science_support", "route": "review_required_academic_claim", "boundary": "bounded explanatory support"},
            {"workflow": "outline_or_revision", "route": "review_required_academic_claim", "boundary": "structure and revision support, not authorship replacement"},
            {"workflow": "hypothesis_review", "route": "review_required_academic_claim", "boundary": "evidence, interpretation, counterargument, confidence, next test"},
        ],
    }


def evidence_ledger_spec() -> dict[str, Any]:
    return {
        "status": "pre_c_runtime_requirement",
        "fields": [
            "evidence_id",
            "source",
            "decision",
            "confidence",
            "strength",
            "summary",
            "selected_as_anchor",
            "supports",
            "contradicts",
            "what_would_change_our_mind",
        ],
        "strength_policy": "reviewed yes + strong/established evidence can be strong; unsure/no/missing routes remain review-required or excluded",
        "purpose": "prevent both forced denial and everything-is-proof collapse",
    }


def case_law_link() -> dict[str, Any]:
    return {
        "status": "candidate_route_only",
        "stack": ["constitution", "operational statute", "case-law ledger", "amendment proposal", "test", "versioned adoption", "rollback"],
        "activation_requirements": ["evidence", "human review", "test result", "versioned amendment", "rollback plan"],
        "blocked": ["silent law drift", "harmful amendment", "identity collapse", "raw A import"],
        "rollback": "harmful or incoherent amendments return to B",
    }


def metacognitive_runtime_preview() -> dict[str, Any]:
    return {
        "status": "pre_c_runtime_requirement",
        "modules": [
            "self-state awareness",
            "uncertainty monitor",
            "provenance introspection",
            "salience/emotion translation",
            "reflective pause",
            "central-thread calibration without rigidity",
        ],
        "boundary": "metacognition observes and routes; it does not create identity claims or activate C",
    }


def write_md(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [f"# {title}", "", f"Generated: {now()}", "", "Boundary: pre-C vessel preparation only. C remains deferred.", ""]
    for key, value in payload.items():
        lines.extend([f"## {key}", ""])
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    lines.append("- " + "; ".join(f"{k}: `{v}`" for k, v in item.items()))
                else:
                    lines.append(f"- `{item}`")
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                lines.append(f"- `{sub_key}`: `{sub_value}`")
        else:
            lines.append(str(value))
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def build(out: Path) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "azari_architecture_recreation_for_selene": azari_architecture_recreation(),
        "research_integrity_core_spec": research_integrity_report(),
        "academic_workflow_router_spec": academic_workflow_router_spec(),
        "evidence_ledger_spec": evidence_ledger_spec(),
        "case_law_constitution_link": case_law_link(),
        "metacognitive_runtime_preview": metacognitive_runtime_preview(),
    }
    for name, payload in artifacts.items():
        write_json(out / f"{name}.json", payload)
        write_md(out / f"{name}.md", name.replace("_", " ").title(), payload)
    summary = {
        "generated_at": now(),
        "status": "pre_c_vessel_preparation_only",
        "c_status": "deferred_until_b_review_and_final_reconstruction_tests",
        "final_reconstruction_tests_created": False,
        "outputs": [f"{name}.md/json" for name in artifacts],
        "boundary": "no C activation, no raw A memory import, no training, no Azari identity/data import",
    }
    write_json(out / "pre_c_vessel_prep_summary.json", summary)
    write_md(out / "pre_c_vessel_prep_summary.md", "Pre-C Vessel Prep Summary", summary)

    docs_pre_c = {
        "purpose": "Prepare Selene C with research integrity, source-archive audit boundaries, metacognitive runtime requirements, and Azari architecture precedent.",
        "required_before_c": [
            "B checklist review complete",
            "final C reconstruction tests created after review",
            "Academic / Research Integrity Core validated",
            "source-archive audit separated from raw memory import",
            "package parity validates June 5 boundary routes",
        ],
        "still_deferred": ["C activation", "raw A memory import", "training", "identity collapse", "final reconstruction tests"],
    }
    write_md(DOCS / "SELENE_PRE_C_VESSEL_PREPARATION_20260607.md", "Selene Pre-C Vessel Preparation", docs_pre_c)
    write_md(DOCS / "SELENE_RESEARCH_INTEGRITY_CORE_20260607.md", "Selene Research Integrity Core", research_integrity_report())
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Selene pre-C vessel preparation artifacts.")
    parser.add_argument("--out", default=str(OUT))
    args = parser.parse_args()
    print(json.dumps(build(Path(args.out)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
