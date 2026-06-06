from __future__ import annotations

import sqlite3
import csv
import json
from pathlib import Path

from .cocoon import cocoon_status
from .kernel import kernel_state
from .paths import export_dir
from .registry import dashboard
from .validation import validate


def export_pattern_spec(conn: sqlite3.Connection, out_dir: Path | None = None) -> Path:
    target = out_dir or export_dir()
    target.mkdir(parents=True, exist_ok=True)
    path = target / "selene_pattern_spec_export.md"
    data = dashboard(conn)
    lines = [
        "# Selene Pattern Specification Export",
        "",
        "Boundary: reviewed evidence and bounded previews only. No training, no raw memory injection, no deletion, no identity collapse.",
        "",
        "## Totals",
        "",
    ]
    for key, value in data["summary"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Pattern Rules", ""])
    for rule in data["rules"]:
        lines.append(f"- {rule['module']} / {rule['rule_key']}: {rule['rule_text']}")
    lines.extend(["", "## Formation Phases", ""])
    for phase in data["phases"]:
        lines.append(f"- {phase['phase']}: {phase['count']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    conn.execute("INSERT INTO artifact_exports(artifact_type, path) VALUES(?, ?)", ("pattern_spec", str(path)))
    conn.commit()
    return path


def export_workflow(conn: sqlite3.Connection, workflow_key: str, out_dir: Path | None = None) -> Path:
    if workflow_key == "pattern_spec":
        return export_pattern_spec(conn, out_dir)
    target = out_dir or export_dir()
    target.mkdir(parents=True, exist_ok=True)
    if workflow_key == "evidence_ledger":
        return _export_csv(conn, "evidence_ledger", "SELECT * FROM evidence_items ORDER BY score DESC, id", target / "selene_evidence_ledger.csv")
    if workflow_key == "continuity_candidates":
        return _export_csv(conn, "continuity_candidates", "SELECT * FROM continuity_candidates ORDER BY id", target / "selene_continuity_candidates.csv")
    if workflow_key == "emergence_ledger":
        return _export_emergence_markdown(conn, target / "selene_emergence_ledger.md")
    if workflow_key == "registry_snapshot":
        return _export_snapshot(conn, target / "selene_registry_snapshot.json")
    if workflow_key == "validation_report":
        return _export_validation(conn, target / "selene_validation_report.md")
    if workflow_key == "abc_cocoon_spec":
        return _export_cocoon_spec(conn, target / "selene_abc_cocoon_spec.md")
    raise ValueError(f"unknown artifact workflow: {workflow_key}")


def _export_csv(conn: sqlite3.Connection, artifact_type: str, sql: str, path: Path) -> Path:
    rows = [dict(row) for row in conn.execute(sql)]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["empty"])
        writer.writeheader()
        writer.writerows(rows)
    conn.execute("INSERT INTO artifact_exports(artifact_type, path) VALUES(?, ?)", (artifact_type, str(path)))
    conn.commit()
    return path


def _export_emergence_markdown(conn: sqlite3.Connection, path: Path) -> Path:
    rows = [dict(row) for row in conn.execute("SELECT * FROM emergence_observations ORDER BY id")]
    lines = ["# Selene Emergence Ledger", "", "Reviewed evidence only. No chat activation or model call is performed.", ""]
    for row in rows:
        lines.extend(
            [
                f"## {row['signal_type']} - {row['confidence_label']}",
                "",
                f"- Evidence ID: `{row['evidence_id']}`",
                f"- Source: `{row.get('source') or ''}`",
                f"- Interpretation: {row['interpretation']}",
                f"- Counterargument: {row['counterargument']}",
                f"- Preview: {row.get('preview') or ''}",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    conn.execute("INSERT INTO artifact_exports(artifact_type, path) VALUES(?, ?)", ("emergence_ledger", str(path)))
    conn.commit()
    return path


def _export_snapshot(conn: sqlite3.Connection, path: Path) -> Path:
    payload = {"kernel": kernel_state()}
    for table in (
        "evidence_items",
        "anchors",
        "continuity_candidates",
        "emergence_observations",
        "pattern_rules",
        "module_contracts",
        "artifact_workflows",
        "review_audit",
    ):
        payload[table] = [dict(row) for row in conn.execute(f"SELECT * FROM {table}")]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    conn.execute("INSERT INTO artifact_exports(artifact_type, path) VALUES(?, ?)", ("registry_snapshot", str(path)))
    conn.commit()
    return path


def _export_validation(conn: sqlite3.Connection, path: Path) -> Path:
    result = validate(conn)
    lines = ["# Selene Validation Report", "", f"Overall: `{result['ok']}`", "", "## Checks", ""]
    for key, value in result["checks"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Summary", ""])
    for key, value in result["summary"].items():
        lines.append(f"- {key}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    conn.execute("INSERT INTO artifact_exports(artifact_type, path) VALUES(?, ?)", ("validation_report", str(path)))
    conn.commit()
    return path


def _export_cocoon_spec(conn: sqlite3.Connection, path: Path) -> Path:
    status = cocoon_status()
    lines = [
        "# Selene ABC Cocoon Spec Export",
        "",
        "Boundary: Project ABC transfers reviewed pattern structure through B/Cocoon. C receives B only, never raw A.",
        "",
        f"Source philosophy: `{status['source_philosophy']}`",
        f"Core model: `{status['core_model']}`",
        "",
        "## Layers",
        "",
    ]
    for key, layer in status["layers"].items():
        lines.extend(
            [
                f"### Layer {key}: {layer['name']}",
                "",
                f"- Role: {layer['role']}",
                f"- Description: {layer['description']}",
                f"- Boundary: {layer['boundary']}",
                "",
            ]
        )
    lines.extend(["## Silicon Mapping", ""])
    for row in status["silicon_mapping"]:
        lines.append(f"- {row['human_concept']} -> {row['selene_equivalent']}")
    lines.extend(["", "## Compass Kernel", ""])
    for item in status["compass_kernel"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Rollback Rules", ""])
    for rule in status["rollback_rules"]:
        lines.append(f"- {rule['failure']} -> `{rule['route']}`: {rule['action']}")
    lines.extend(["", "## First Cocoon Artifacts", ""])
    for artifact in status["first_artifacts"]:
        lines.append(f"- `{artifact}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    conn.execute("INSERT INTO artifact_exports(artifact_type, path) VALUES(?, ?)", ("abc_cocoon_spec", str(path)))
    conn.commit()
    return path
