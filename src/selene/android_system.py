from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from .c_blueprint import ANDROID_ORGAN_SYSTEMS
from .cocoon_readiness import ORGAN_TABLES, organ_blueprints_status
from .registry import truncate


ANDROID_WORKFLOW_BOUNDARY = "android_system_workflow_check_status_only_no_activation"
EXPECTED_ANDROID_SYSTEM_KEYS = {
    "boundary_system",
    "structural_system",
    "tendril_movement_system",
    "coordination_system",
    "salience_system",
    "context_transport_system",
    "immune_protection_system",
    "exchange_system",
    "evidence_metabolism_system",
    "cleanup_system",
    "development_growth_system",
}

GUARD_FLAGS: dict[str, Any] = {
    "transfer_approved": False,
    "transfer_approval_changed": False,
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
}

SYSTEM_WORKFLOW_MAP: dict[str, dict[str, Any]] = {
    "boundary_system": {
        "routes": ["transfer.law.status", "core_mind.activation_governance.preview", "archive.audit"],
        "shelves": ["transfer_protocol_records", "gate_events"],
        "failure_mode": "privacy, consent, raw-import, or identity membrane gap",
    },
    "structural_system": {
        "routes": ["kernel.status", "c_blueprint.status", "vessel.construction.status"],
        "shelves": ["module_contracts", "transfer_c_readable_packages"],
        "failure_mode": "schema, contract, or vessel-shape mismatch",
    },
    "tendril_movement_system": {
        "routes": ["vessel.tendril.plan_preview", "c_core.action_reflection.preview", "core_mind.activation_governance.preview"],
        "shelves": ["c_core_mind_runtime_shell_records", "vessel_chest_holding_items"],
        "failure_mode": "action proposal lacks approval, reversibility, or rollback",
    },
    "coordination_system": {
        "routes": ["core_mind.route_preview", "core_mind.runtime_readiness", "selene_chat.status"],
        "shelves": ["c_core_mind_route_previews", "selene_chat_sessions"],
        "failure_mode": "Core/Mind routing, attention, or response selection mismatch",
    },
    "salience_system": {
        "routes": ["vessel.emotion_salience_packet.list", "vessel.goal_drive.preview", "c_core.uncertainty.preview"],
        "shelves": ["vessel_emotion_salience_packets", "c_runtime_goal_drive_records"],
        "failure_mode": "salience, uncertainty, or repair pressure not visible",
    },
    "context_transport_system": {
        "routes": ["vessel.organ_bus_message.list", "core_mind.context.compose", "vessel.retrieval_runtime.preview"],
        "shelves": ["vessel_organ_bus_messages", "vessel_retrieval_reconstruction_previews"],
        "failure_mode": "context/source refs cannot move without raw recall",
    },
    "immune_protection_system": {
        "routes": ["core_mind.recovery.preview", "c_core.drift_warning.preview", "c_vessel.organ_fault.resilience_check"],
        "shelves": ["transfer_protocol_records", "vessel_reconstruction_check_runs"],
        "failure_mode": "drift, source confusion, or bypass cannot return to B",
    },
    "exchange_system": {
        "routes": ["selene_chat.status", "vessel.academic_packet.list", "vessel.perception_packet.list"],
        "shelves": ["selene_chat_messages", "vessel_academic_packets", "vessel_perception_packets"],
        "failure_mode": "chat, research, artifact, or source intake boundary unclear",
    },
    "evidence_metabolism_system": {
        "routes": ["vessel.evidence_tension.list", "b.approved_memory_references.list", "vessel.chronological_corpus.status"],
        "shelves": ["vessel_evidence_tension_ledger", "b_approved_memory_references", "vessel_chronological_corpus_arcs"],
        "failure_mode": "evidence cannot move from A audit through B review to C-readable metadata",
    },
    "cleanup_system": {
        "routes": ["vessel.my_office.cleanup_residue", "core_mind.recovery.preview", "vessel.memory_lifecycle.status"],
        "shelves": ["vessel_review_queue", "c_memory_reconsolidation_reviews"],
        "failure_mode": "stale, superseded, or noisy records cannot be cleared without deleting provenance",
    },
    "development_growth_system": {
        "routes": ["vessel.cycle.prepare_night", "core_mind.runtime_readiness", "memory.fractional_corpus.status"],
        "shelves": ["memory_fractional_corpus_manifests", "post_transfer_inspection_runs", "c_runtime_wake_sleep_dream_cycles"],
        "failure_mode": "growth, dream-state, reconstruction, or fraction memory preflight missing",
    },
}


def android_workflow_status(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM android_system_workflow_reports ORDER BY id DESC LIMIT 1").fetchone()
    latest = _decode_report_row(row) if row else None
    return _with_guards(
        {
            "status": "android_system_workflow_status_ready",
            "latest_report": latest,
            "preflight_passed": bool(latest and latest.get("fraction_memory_preflight_passed")),
            "android_system_count": len(ANDROID_ORGAN_SYSTEMS["systems"]),
            "concrete_organ_shelf_count": len(ORGAN_TABLES),
            "required_before_fraction_memory": True,
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def android_workflow_report(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM android_system_workflow_reports ORDER BY id DESC LIMIT 1").fetchone()
    if row is None:
        return _with_guards(
            {
                "status": "android_system_workflow_report_missing",
                "preflight_passed": False,
                "message": "Run Android System Workflow Check before fraction memory tests.",
                "review_destination": "Status",
                "review_status": "status_only",
            }
        )
    return _with_guards({"status": "android_system_workflow_report_ready", **_decode_report_row(row)})


def run_android_workflow_check(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    run_id = str(payload.get("run_id") or f"android_workflow_{_stamp()}")
    systems = _system_reports(conn)
    concrete = _concrete_organ_shelves(conn)
    expected_missing = sorted(EXPECTED_ANDROID_SYSTEM_KEYS - {item["key"] for item in systems})
    ready_count = sum(1 for item in systems if item["status"] == "ready")
    partial_count = sum(1 for item in systems if item["status"] in {"partial", "missing_route", "missing_shelf", "needs_review"})
    blocked_count = sum(1 for item in systems if item["status"] == "blocked")
    concrete_ready = len(concrete["items"]) == len(ORGAN_TABLES) and all(item["record_shelf_ready"] for item in concrete["items"])
    preflight_passed = (
        len(systems) == 11
        and not expected_missing
        and ready_count == 11
        and blocked_count == 0
        and concrete_ready
    )
    report = {
        "run_id": run_id,
        "status": "android_system_workflow_check_passed" if preflight_passed else "android_system_workflow_check_needs_review",
        "preflight_passed": preflight_passed,
        "ready_count": ready_count,
        "partial_count": partial_count,
        "blocked_count": blocked_count,
        "system_count": len(systems),
        "expected_missing": expected_missing,
        "systems": systems,
        "concrete_organ_shelves": concrete,
        "fraction_memory_support_allowed": preflight_passed,
        "failure_route": "return_to_b",
        "review_destination": "Status" if preflight_passed else "Cocoon",
        "review_status": "status_only" if preflight_passed else "review_only",
        **GUARD_FLAGS,
    }
    conn.execute(
        """
        INSERT INTO android_system_workflow_reports
        (run_id, status, ready_count, partial_count, blocked_count, system_count,
         fraction_memory_preflight_passed, report_json, source_refs, provenance_boundary, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            report["status"],
            ready_count,
            partial_count,
            blocked_count,
            len(systems),
            int(preflight_passed),
            json.dumps(report),
            json.dumps(["android_organ_systems", "selene_organ_blueprints", "fraction_memory_preflight"]),
            ANDROID_WORKFLOW_BOUNDARY,
            report["review_status"],
        ),
    )
    conn.commit()
    return _with_guards(report)


def android_workflow_preflight_passed(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        """
        SELECT fraction_memory_preflight_passed
        FROM android_system_workflow_reports
        ORDER BY id DESC LIMIT 1
        """
    ).fetchone()
    return bool(row and row["fraction_memory_preflight_passed"])


def _system_reports(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for system in ANDROID_ORGAN_SYSTEMS["systems"]:
        key = str(system["key"])
        mapping = SYSTEM_WORKFLOW_MAP.get(key, {})
        route_keys = list(mapping.get("routes") or [])
        shelves = list(mapping.get("shelves") or [])
        missing_routes = [route for route in route_keys if not route]
        missing_shelves = [shelf for shelf in shelves if not _table_exists(conn, shelf)]
        blocked = _system_blocked(key)
        if blocked:
            status = "blocked"
        elif missing_routes:
            status = "missing_route"
        elif missing_shelves:
            status = "missing_shelf"
        elif not route_keys or not shelves:
            status = "partial"
        else:
            status = "ready"
        reports.append(
            {
                "key": key,
                "name": str(system.get("name") or key),
                "android_function": truncate(str(system.get("android_function") or ""), 500),
                "coordinates": list(system.get("coordinates") or []),
                "status": status,
                "routes_checked": route_keys,
                "shelves_checked": shelves,
                "missing_routes": missing_routes,
                "missing_shelves": missing_shelves,
                "guard_flags_confirmed": not blocked,
                "failure_mode": str(mapping.get("failure_mode") or "unknown android workflow gap"),
                "return_to_b_path": "Cocoon / B repair route",
                "fraction_memory_support_allowed": status == "ready",
                **GUARD_FLAGS,
            }
        )
    return reports


def _concrete_organ_shelves(conn: sqlite3.Connection) -> dict[str, Any]:
    status = organ_blueprints_status(conn)
    items = [
        {
            "key": item["key"],
            "title": item.get("title") or item["key"],
            "record_shelf": ORGAN_TABLES.get(item["key"]),
            "record_shelf_ready": bool(item.get("record_shelf_ready")) and _table_exists(conn, str(ORGAN_TABLES.get(item["key"]) or "")),
            "record_count": item.get("record_count", 0),
            "status": "ready" if item.get("record_shelf_ready") else "missing_shelf",
        }
        for item in status.get("blueprints", [])
    ]
    return {
        "status": "concrete_organ_shelves_ready" if len(items) == len(ORGAN_TABLES) and all(item["record_shelf_ready"] for item in items) else "concrete_organ_shelves_need_review",
        "count": len(items),
        "expected_count": len(ORGAN_TABLES),
        "items": items,
    }


def _system_blocked(key: str) -> bool:
    return key not in EXPECTED_ANDROID_SYSTEM_KEYS


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    if not table_name:
        return False
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _decode_report_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    item = dict(row)
    report = _loads_dict(item.get("report_json"))
    return {
        **item,
        "report_json": report,
        "source_refs": _loads_list(item.get("source_refs")),
        **{key: report.get(key) for key in ("systems", "concrete_organ_shelves", "expected_missing", "failure_route") if key in report},
        "preflight_passed": bool(item.get("fraction_memory_preflight_passed")),
    }


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    guarded = {**payload, **GUARD_FLAGS, "provenance_boundary": ANDROID_WORKFLOW_BOUNDARY}
    guarded["activation_change"] = "none"
    guarded["memory_write_active"] = False
    guarded["runtime_memory_recall"] = False
    guarded["raw_a_import_allowed"] = False
    guarded["training_allowed"] = False
    guarded["self_replication_allowed"] = False
    guarded["autonomous_action_allowed"] = False
    return guarded


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        data = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _loads_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    try:
        data = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
