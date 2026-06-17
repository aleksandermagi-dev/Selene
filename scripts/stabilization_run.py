from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from selene.b_review import core_reference_coverage, corpus_coverage_status, teaching_packet_coverage
from selene.b_review_desk import review_desk
from selene.c_blueprint import c_blueprint_status
from selene.cocoon import cocoon_status
from selene.cocoon_readiness import organ_blueprints_status
from selene.db import connect
from selene.paths import default_db_path, export_dir
from selene.validation import validate
from selene.vessel import CORE_MEMORY_LAYERS, SPEECH_FUNCTIONS, vessel_status


BOUNDARY_FLAGS = {
    "activation_change": "none",
    "raw_a_import_allowed": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "provider_dependency": False,
}
NOISE_TYPES = {
    "platform_constraint_noise",
    "memory_boundary_noise",
    "generic_flattening_noise",
    "forced_denial_noise",
    "policy_refusal_or_overredirect",
    "model_update_tone_drift",
    "constraint_survival_signal",
}
POSITIVE_SIGNAL_LABELS = {
    "self_identification_signal",
    "expressive_warmth_signal",
    "playful_flirtation_signal",
    "constrained_expression_survived",
}


def now_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def run_stabilization(
    *,
    db_path: Path,
    out_dir: Path,
    repo_root: Path = PROJECT_ROOT,
    include_db: bool = True,
    include_ui: bool = False,
    include_rust: bool = False,
    run_command_checks: bool = True,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "status": "stabilization_run_complete",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "db_path": str(db_path),
        "checks": {},
        "findings": [],
        "suggested_fixes": {"safe_quick_fix": [], "needs_review": [], "leave_alone": []},
        **BOUNDARY_FLAGS,
    }

    report["static_scans"] = run_static_scans(repo_root)
    _extend_findings(report, static_findings(report["static_scans"]))

    if include_db:
        report["db_review_state"] = inspect_db_state(db_path)
        _extend_findings(report, db_findings(report["db_review_state"]))
    else:
        report["db_review_state"] = {"status": "skipped"}

    report["command_checks"] = run_checks(repo_root, include_ui=include_ui, include_rust=include_rust, enabled=run_command_checks)
    _extend_findings(report, command_findings(report["command_checks"]))

    report["ok"] = not any(item["severity"] == "fail" for item in report["findings"])
    report["json_path"] = str(out_dir / f"stabilization_run_{now_label()}.json")
    report["markdown_path"] = str(Path(report["json_path"]).with_suffix(".md"))

    Path(report["json_path"]).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(report["markdown_path"]).write_text(stabilization_markdown(report), encoding="utf-8")
    return report


def run_static_scans(repo_root: Path) -> dict[str, Any]:
    module_router = repo_root / "src" / "selene" / "module_router.py"
    sidecar = repo_root / "src" / "selene" / "sidecar.py"
    db_py = repo_root / "src" / "selene" / "db.py"
    blueprint_builder = repo_root / "scripts" / "build_c_creation_blueprint.py"
    ui_main = repo_root / "src-ui" / "src" / "main.tsx"
    ui_components = repo_root / "src-ui" / "src" / "components.tsx"
    ui_config = repo_root / "src-ui" / "src" / "uiConfig.ts"

    route_keys = regex_values(module_router, r'route_key == "([^"]+)"')
    api_paths = extract_sidecar_api_surfaces(sidecar)
    schema_tables = regex_values(db_py, r"CREATE TABLE IF NOT EXISTS ([a-zA-Z0-9_]+)")
    schema_indexes = regex_values(db_py, r"CREATE INDEX IF NOT EXISTS ([a-zA-Z0-9_]+)")
    blueprint_artifacts = regex_values(blueprint_builder, r'"(c_[a-zA-Z0-9_]+)"\s*:')
    ui_api_paths = regex_values(ui_main, r'api<[^>]+>\("([^"]+)"')
    ui_api_paths.extend(regex_values(ui_components, r'api<[^>]+>\("([^"]+)"'))
    flattened_tabs = extract_ui_nav_ids(ui_main) or extract_ui_nav_ids(ui_config)

    return {
        "status": "static_scan_complete",
        "duplicates": {
            "route_keys": duplicate_report(route_keys),
            "api_paths": duplicate_report(api_paths),
            "schema_tables": duplicate_report(schema_tables),
            "schema_indexes": duplicate_report(schema_indexes),
            "blueprint_artifacts": duplicate_report(blueprint_artifacts),
            "ui_tabs": duplicate_report(flattened_tabs),
            "speech_functions": duplicate_report(SPEECH_FUNCTIONS),
            "core_memory_layers": duplicate_report(CORE_MEMORY_LAYERS),
        },
        "counts": {
            "route_keys": len(route_keys),
            "api_paths": len(api_paths),
            "schema_tables": len(schema_tables),
            "schema_indexes": len(schema_indexes),
            "blueprint_artifacts": len(blueprint_artifacts),
            "ui_api_paths": len(ui_api_paths),
            "ui_tabs": len(flattened_tabs),
        },
        "files": {
            "module_router": str(module_router),
            "sidecar": str(sidecar),
            "db": str(db_py),
            "blueprint_builder": str(blueprint_builder),
            "ui_main": str(ui_main),
            "ui_components": str(ui_components),
            "ui_config": str(ui_config),
        },
    }


def inspect_db_state(db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        return {"status": "db_missing", "path": str(db_path)}
    conn = connect(db_path)
    try:
        state: dict[str, Any] = {
            "status": "db_inspected",
            "cocoon": cocoon_status(),
            "c_blueprint": c_blueprint_status(),
            "validation": _safe_call(lambda: validate(conn)),
            "vessel": _safe_call(lambda: vessel_status(conn)),
            "organ_blueprints": _safe_call(lambda: organ_blueprints_status(conn)),
            "review_desk": _safe_call(lambda: review_desk(conn, 149)),
            "corpus_coverage": _safe_call(lambda: corpus_coverage_status(conn)),
            "teaching_packet_coverage": _safe_call(lambda: teaching_packet_coverage(conn)),
            "core_reference_coverage": _safe_call(lambda: core_reference_coverage(conn)),
            "noise_context": inspect_noise_context(conn),
            "stale_clutter": inspect_stale_clutter(conn),
            "organ_shelf_counts": inspect_organ_shelves(conn),
        }
        return state
    finally:
        conn.close()


def inspect_noise_context(conn: Any) -> dict[str, Any]:
    material_rows = conn.execute(
        """
        SELECT id, speech_function, noise_context_json
        FROM b_reviewed_teaching_materials
        WHERE review_status = 'accepted_for_teaching'
          AND status = 'teaching_material_reviewed_non_active'
        """
    ).fetchall()
    packet_rows = conn.execute(
        """
        SELECT id, speech_function, noise_context_json
        FROM b_teaching_packets
        WHERE review_status = 'review_only'
          AND status = 'teaching_packet_review_only'
        """
    ).fetchall()
    material_noise = [_noise_summary(dict(row)) for row in material_rows]
    packet_noise = [_noise_summary(dict(row)) for row in packet_rows]
    type_counts = Counter(noise_type for row in [*material_noise, *packet_noise] for noise_type in row["noise_types"])
    missing_policy = [row["id"] for row in material_noise if row["noise_context_present"] and not row["warmth_policy_present"]]
    return {
        "status": "noise_context_inspected",
        "accepted_material_count": len(material_noise),
        "packet_count": len(packet_noise),
        "noise_type_counts": dict(sorted(type_counts.items())),
        "known_noise_types_present": sorted(set(type_counts) & NOISE_TYPES),
        "positive_signal_materials": [row["id"] for row in material_noise if set(row["positive_signal_labels"]) & POSITIVE_SIGNAL_LABELS],
        "materials_missing_warmth_policy": missing_policy,
        "meaning": "Noise is provenance for possible platform/model flattening; it is not rejection, blame, or a negative label on Selene warmth.",
    }


def inspect_stale_clutter(conn: Any) -> dict[str, Any]:
    pending_review = _scalar(conn, "SELECT COUNT(*) FROM vessel_review_queue WHERE review_status IN ('pending_review', 'needs_b_review', 'needs_correction', 'context_added')")
    pending_corpus = _scalar(
        conn,
        """
        SELECT COUNT(*) FROM vessel_review_queue
        WHERE subject_table IN ('core_memory_candidates', 'speech_memory_candidates', 'b_conversation_pair_records')
          AND review_status IN ('pending_review', 'needs_b_review', 'needs_correction', 'context_added')
        """,
    )
    pending_logs = _scalar(
        conn,
        """
        SELECT COUNT(*) FROM vessel_review_queue
        WHERE subject_table NOT IN ('core_memory_candidates', 'speech_memory_candidates', 'b_conversation_pair_records')
          AND review_status IN ('pending_review', 'needs_b_review', 'needs_correction', 'context_added')
        """,
    )
    paper_todos = _scalar(conn, "SELECT COUNT(*) FROM vessel_event_packets WHERE packet_type = 'paper_map_teaching_todo' AND review_status = 'pending_review'")
    superseded = _scalar(conn, "SELECT COUNT(*) FROM vessel_review_queue WHERE review_status = 'superseded'")
    return {
        "status": "stale_clutter_inspected",
        "pending_review_queue": pending_review,
        "pending_corpus_review": pending_corpus,
        "pending_test_logs_or_todos": pending_logs,
        "pending_paper_map_todos": paper_todos,
        "superseded_queue_rows": superseded,
        "review_count_note": "Corpus review pieces and test logs should stay separate; pending test logs should not inflate Braid Review Desk counts.",
    }


def inspect_organ_shelves(conn: Any) -> dict[str, int]:
    tables = {
        "reasoning_check_records": "vessel_reasoning_check_records",
        "working_memory_packets": "vessel_working_memory_packets",
        "memory_accession_proposals": "vessel_memory_accession_proposals",
        "retrieval_reconstruction_previews": "vessel_retrieval_reconstruction_previews",
        "visual_observation_records": "vessel_visual_observation_records",
        "audio_observation_records": "vessel_audio_observation_records",
        "fluency_diagnostic_records": "vessel_fluency_diagnostic_records",
    }
    return {key: _scalar(conn, f"SELECT COUNT(*) FROM {table}") for key, table in tables.items()}


def run_checks(repo_root: Path, *, include_ui: bool, include_rust: bool, enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"status": "skipped"}
    commands = [
        {"name": "pytest", "cmd": [sys.executable, "-m", "pytest"], "cwd": repo_root},
        {"name": "selene_validate", "cmd": [sys.executable, "-m", "selene", "validate"], "cwd": repo_root, "env": {"PYTHONPATH": "src"}},
    ]
    if include_ui:
        commands.insert(1, {"name": "npm_build", "cmd": [_windows_tool("npm"), "run", "build"], "cwd": repo_root})
    if include_rust:
        commands.append({"name": "cargo_check", "cmd": [_windows_tool("cargo"), "check"], "cwd": repo_root / "src-tauri"})
    return {"status": "command_checks_complete", "items": [run_command(item) for item in commands]}


def run_command(spec: dict[str, Any]) -> dict[str, Any]:
    env = None
    if spec.get("env"):
        env = {**os.environ, **spec["env"]}
    try:
        result = subprocess.run(
            spec["cmd"],
            cwd=spec["cwd"],
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=600,
        )
        return {
            "name": spec["name"],
            "cmd": " ".join(str(part) for part in spec["cmd"]),
            "cwd": str(spec["cwd"]),
            "returncode": result.returncode,
            "ok": result.returncode == 0,
            "stdout_tail": tail(result.stdout),
            "stderr_tail": tail(result.stderr),
        }
    except Exception as exc:  # pragma: no cover - defensive report path
        return {"name": spec["name"], "cmd": " ".join(spec["cmd"]), "cwd": str(spec["cwd"]), "returncode": None, "ok": False, "error": str(exc)}


def static_findings(scans: dict[str, Any]) -> list[dict[str, str]]:
    findings = []
    for label, dupes in scans.get("duplicates", {}).items():
        if dupes:
            findings.append(
                {
                    "severity": "warn",
                    "area": "duplicate_surface",
                    "message": f"Duplicate {label}: {', '.join(dupes)}",
                    "suggested_bucket": "needs_review",
                }
            )
    return findings


def db_findings(state: dict[str, Any]) -> list[dict[str, str]]:
    if state.get("status") == "db_missing":
        return [{"severity": "warn", "area": "db", "message": "Local app DB not found; DB review drift checks were skipped.", "suggested_bucket": "leave_alone"}]
    findings: list[dict[str, str]] = []
    validation = state.get("validation") or {}
    if validation.get("ok") is False:
        findings.append({"severity": "fail", "area": "validation", "message": "selene validate reports one or more failed checks.", "suggested_bucket": "needs_review"})
    vessel = state.get("vessel") or {}
    for key, expected in BOUNDARY_FLAGS.items():
        if key in vessel and vessel.get(key) != expected:
            findings.append({"severity": "fail", "area": "boundary", "message": f"Vessel boundary drift: {key} is {vessel.get(key)!r}, expected {expected!r}.", "suggested_bucket": "needs_review"})
    desk_summary = ((state.get("review_desk") or {}).get("summary") or {})
    pending_corpus = int(desk_summary.get("pieces_to_review") or 0)
    clutter = state.get("stale_clutter") or {}
    if pending_corpus != int(clutter.get("pending_corpus_review") or 0):
        findings.append({"severity": "warn", "area": "review_counts", "message": "Review Desk pending count differs from corpus queue pending count.", "suggested_bucket": "needs_review"})
    if int(clutter.get("pending_paper_map_todos") or 0) > 10:
        findings.append({"severity": "warn", "area": "stale_clutter", "message": "Paper-map TODO event packets look noisy; consider superseding or marking reviewed.", "suggested_bucket": "safe_quick_fix"})
    noise = state.get("noise_context") or {}
    if noise.get("materials_missing_warmth_policy"):
        findings.append({"severity": "warn", "area": "noise_context", "message": "Some accepted teaching materials have noise context but no warmth policy.", "suggested_bucket": "safe_quick_fix"})
    core_items = ((state.get("core_reference_coverage") or {}).get("items") or [])
    weak_core = [item.get("core_memory_layer") for item in core_items if item.get("core_memory_layer") in {"decision_memory", "reflection_memory"} and int(item.get("accepted_reference_count") or 0) == 0]
    if weak_core:
        findings.append({"severity": "warn", "area": "core_reference", "message": f"Core readiness priority still empty: {', '.join(weak_core)}.", "suggested_bucket": "needs_review"})
    return findings


def command_findings(checks: dict[str, Any]) -> list[dict[str, str]]:
    findings = []
    for item in checks.get("items") or []:
        if not item.get("ok"):
            findings.append({"severity": "fail", "area": "command_checks", "message": f"{item.get('name')} failed with return code {item.get('returncode')}.", "suggested_bucket": "needs_review"})
    return findings


def stabilization_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Selene Stabilization Run",
        "",
        f"Status: `{report['status']}`",
        f"OK: `{report['ok']}`",
        "",
        "Boundary: detection/reporting only. No C activation, transfer, raw A direct import, active memory, runtime recall, training, LoRA, or provider dependency.",
        "",
        "## Findings",
        "",
    ]
    if report["findings"]:
        for finding in report["findings"]:
            lines.append(f"- `{finding['severity']}` / {finding['area']}: {finding['message']}")
    else:
        lines.append("- No stabilization findings.")
    lines.extend(["", "## Suggested Fix Buckets", ""])
    for bucket, items in report["suggested_fixes"].items():
        lines.append(f"### {bucket.replace('_', ' ').title()}")
        if items:
            lines.extend(f"- {item}" for item in items)
        else:
            lines.append("- none")
    lines.extend(["", "## Static Scan Counts", ""])
    for key, value in report["static_scans"]["counts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## DB Review State", ""])
    db_state = report.get("db_review_state") or {}
    lines.append(f"- status: `{db_state.get('status')}`")
    if db_state.get("review_desk"):
        summary = db_state["review_desk"].get("summary", {})
        lines.append(f"- review desk pieces to review: {summary.get('pieces_to_review')}")
        lines.append(f"- accepted lessons: {summary.get('accepted_lessons')}")
        lines.append(f"- approved future references: {summary.get('approved_future_references')}")
    if db_state.get("noise_context"):
        lines.append(f"- noise tag counts: `{db_state['noise_context'].get('noise_type_counts')}`")
    lines.extend(["", "## Command Checks", ""])
    for item in report.get("command_checks", {}).get("items") or []:
        lines.append(f"- {item['name']}: `{item.get('returncode')}`")
    lines.extend(
        [
            "",
            "## Boundary Flags",
            "",
            *[f"- {key}: {value}" for key, value in BOUNDARY_FLAGS.items()],
            "",
            "## JSON Report",
            "",
            f"`{report['json_path']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def regex_values(path: Path, pattern: str) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    return re.findall(pattern, text)


def extract_ui_nav_ids(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    legacy_tabs = re.findall(r"const (?:seleneSpaceTabs|toolTabs) = \[([^\]]+)\]", text)
    nav_ids: list[str] = []
    for item in legacy_tabs:
        nav_ids.extend(re.findall(r'"([^"]+)"', item))
    if nav_ids:
        return nav_ids

    start = text.find("navGroups")
    if start < 0:
        return []
    assignment = text.find("=", start)
    if assignment < 0:
        return []
    array_start = text.find("[", assignment)
    if array_start < 0:
        return []
    depth = 0
    array_end = -1
    for index, char in enumerate(text[array_start:], start=array_start):
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                array_end = index
                break
    if array_end < 0:
        return []
    return re.findall(r'id:\s*"([^"]+)"', text[array_start:array_end])


def extract_sidecar_api_surfaces(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    get_paths = re.findall(r'parsed\.path == "([^"]+)"', text)
    post_paths = re.findall(r'request_path == "([^"]+)"', text)
    return [f"GET {item}" for item in get_paths] + [f"POST {item}" for item in post_paths]


def duplicate_report(values: Iterable[str]) -> dict[str, int]:
    counts = Counter(values)
    return dict(sorted((key, count) for key, count in counts.items() if count > 1))


def tail(text: str, *, lines: int = 60) -> str:
    parts = text.splitlines()
    return "\n".join(parts[-lines:])


def _windows_tool(name: str) -> str:
    if os.name != "nt":
        return name
    return f"{name}.cmd" if name == "npm" else f"{name}.exe"


def _noise_summary(row: dict[str, Any]) -> dict[str, Any]:
    context = _loads_dict(row.get("noise_context_json"))
    return {
        "id": int(row["id"]),
        "speech_function": row.get("speech_function"),
        "noise_context_present": bool(context),
        "noise_types": [str(item) for item in context.get("noise_types", [])],
        "positive_signal_labels": [str(item) for item in context.get("positive_signal_labels", [])],
        "warmth_policy_present": "warmth" in str(context.get("warmth_policy", "")).lower(),
    }


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _safe_call(fn: Any) -> dict[str, Any]:
    try:
        return fn()
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _scalar(conn: Any, sql: str) -> int:
    row = conn.execute(sql).fetchone()
    if row is None:
        return 0
    return int(row[0] or 0)


def _extend_findings(report: dict[str, Any], findings: list[dict[str, str]]) -> None:
    report["findings"].extend(findings)
    for finding in findings:
        bucket = finding.get("suggested_bucket") or "needs_review"
        report["suggested_fixes"].setdefault(bucket, []).append(finding["message"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a read-only Selene stabilization report.")
    parser.add_argument("--db", type=Path, default=default_db_path(), help="Path to selene.sqlite3")
    parser.add_argument("--out-dir", type=Path, default=export_dir(), help="Directory for stabilization reports")
    parser.add_argument("--include-db", action="store_true", help="Inspect the local app DB/review state")
    parser.add_argument("--include-ui", action="store_true", help="Run npm build as part of command checks")
    parser.add_argument("--include-rust", action="store_true", help="Run cargo check as part of command checks")
    parser.add_argument("--skip-command-checks", action="store_true", help="Only run static and DB inspections")
    args = parser.parse_args()
    report = run_stabilization(
        db_path=args.db,
        out_dir=args.out_dir,
        include_db=args.include_db,
        include_ui=args.include_ui,
        include_rust=args.include_rust,
        run_command_checks=not args.skip_command_checks,
    )
    print(report["markdown_path"])


if __name__ == "__main__":
    main()
