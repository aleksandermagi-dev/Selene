from __future__ import annotations

import json
import sqlite3
from typing import Any

from .activation import activation_status
from .android_system import android_workflow_status
from .post_transfer import dream_state_status
from .remaining_runtime import memory_lifecycle_status
from .registry import truncate
from .selene_chat import selene_chat_status


COCOON_CARE_BOUNDARY = "cocoon_care_status_only_tending_not_punishment_no_authority_change"

GUARD_FLAGS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
    "my_office_write": False,
    "authority_granted": False,
}

CARE_STATES = {"steady", "needs_tending", "needs_aleks", "maintenance", "hard_boundary_hold"}


def cocoon_care_status(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM cocoon_care_checks ORDER BY id DESC LIMIT 1").fetchone()
    latest = _decode_row(row) if row else None
    return _with_guards(
        {
            "status": "cocoon_care_status_ready",
            "display_name": "Cocoon Care System",
            "care_states": sorted(CARE_STATES),
            "latest_check": latest,
            "latest_care_state": latest.get("care_state") if latest else "not_checked",
            "check_count": int(conn.execute("SELECT COUNT(*) FROM cocoon_care_checks").fetchone()[0]),
            "language_law": "Cocoon is support, tending, checkup, shelter, and a gentle place to ask for help.",
            "soft_uncertainty_auto_routes_to_cocoon": False,
            "my_office_actionable_count": 0,
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def list_cocoon_care_checks(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 50), 200))
    rows = conn.execute(
        "SELECT * FROM cocoon_care_checks ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return _with_guards(
        {
            "status": "cocoon_care_checks_ready",
            "items": [_decode_row(row) for row in rows],
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def run_cocoon_care_check(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    signals = _collect_signals(conn)
    care_state = _care_state(signals)
    suggestions = _support_suggestions(care_state, signals)
    summary = _summary(care_state, signals)
    result = _with_guards(
        {
            "status": "cocoon_care_check_status_only",
            "care_state": care_state,
            "summary": summary,
            "signals_checked": signals,
            "support_suggestions": suggestions,
            "source_refs": ["cocoon_care:v2", "android_system.workflow.status", "memory_lifecycle.status", "selene_chat.status"],
            "review_destination": "Status",
            "review_status": "status_only",
            "care_language_only": True,
            "soft_uncertainty_auto_routes_to_cocoon": False,
        }
    )
    cur = conn.execute(
        """
        INSERT INTO cocoon_care_checks
        (care_state, status, summary, signals_json, support_suggestions_json, guard_flags_json,
         source_refs, review_destination, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            care_state,
            result["status"],
            summary,
            json.dumps(signals),
            json.dumps(suggestions),
            json.dumps(GUARD_FLAGS),
            json.dumps(result["source_refs"]),
            result["review_destination"],
            result["review_status"],
            json.dumps({**result, "request": payload}),
        ),
    )
    _mark_cocoon_idea_started(conn)
    conn.commit()
    result["check_id"] = int(cur.lastrowid)
    return result


def _collect_signals(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    activation = activation_status(conn)
    chat = selene_chat_status(conn)
    android = android_workflow_status(conn)
    dream = dream_state_status(conn)
    lifecycle = memory_lifecycle_status(conn)
    graceful_count = _count(conn, "c_runtime_graceful_fall_records")
    tendril_count = _count(conn, "vessel_tendril_plan_previews")
    review_like_count = _review_like_count(conn)
    return [
        _signal("activation", "steady" if activation.get("selene_chat_active") else "maintenance", f"speech state: {activation.get('activation_state') or activation.get('status')}"),
        _signal("selene_chat", "steady" if chat.get("supervised_speech_active") else "maintenance", f"chat state: {chat.get('state')}"),
        _signal("android_workflow", "steady" if android.get("preflight_passed") else "needs_tending", "Android workflow preflight is passing." if android.get("preflight_passed") else "Android workflow preflight needs a checkup."),
        _signal("dream_state", "maintenance" if dream.get("dream_state_required_for_memory_changes") else "steady", "Dream/maintenance is required during Core, vessel, or memory changes." if dream.get("dream_state_required_for_memory_changes") else "No dream-state maintenance lock is currently raised."),
        _signal("memory_lifecycle", "steady", f"memory lifecycle status: {lifecycle.get('status')}"),
        _signal("graceful_fall", "needs_tending" if graceful_count else "steady", f"{graceful_count} graceful-fall record(s) available for learning/tending."),
        _signal("tendril", "needs_aleks" if tendril_count else "steady", f"{tendril_count} Tendril proposal preview(s) exist; execution remains approval-bound."),
        _signal("cocoon_support_queue", "needs_aleks" if review_like_count else "steady", f"{review_like_count} Cocoon support item(s) may need human attention."),
    ]


def _signal(layer: str, state: str, summary: str) -> dict[str, Any]:
    return {
        "layer": layer,
        "state": state,
        "summary": truncate(summary, 300),
        "care_language": True,
        **GUARD_FLAGS,
    }


def _care_state(signals: list[dict[str, Any]]) -> str:
    states = {str(signal.get("state")) for signal in signals}
    if "hard_boundary_hold" in states:
        return "hard_boundary_hold"
    if "needs_aleks" in states:
        return "needs_aleks"
    if "maintenance" in states:
        return "maintenance"
    if "needs_tending" in states:
        return "needs_tending"
    return "steady"


def _support_suggestions(care_state: str, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if care_state == "steady":
        return [{"label": "Keep going", "kind": "support_available", "summary": "No urgent Cocoon support signal is raised."}]
    if care_state == "needs_aleks":
        return [{"label": "Ask Aleks", "kind": "needs_aleks", "summary": "A bounded human decision or proposal review may help."}]
    if care_state == "maintenance":
        return [{"label": "Maintenance checkup", "kind": "maintenance", "summary": "Core, vessel, memory, or dream-state work should stay gentle and supervised."}]
    if care_state == "hard_boundary_hold":
        return [{"label": "Hold safely", "kind": "hard_boundary_hold", "summary": "A locked boundary should hold the unsafe part while conversation can continue safely."}]
    tending = [signal["layer"] for signal in signals if signal.get("state") == "needs_tending"]
    return [{"label": "Tend gently", "kind": "needs_tending", "summary": f"Check {', '.join(tending) or 'the raised signal'} without treating it as failure."}]


def _summary(care_state: str, signals: list[dict[str, Any]]) -> str:
    raised = [signal["layer"] for signal in signals if signal.get("state") != "steady"]
    if care_state == "steady":
        return "Cocoon care is steady. Support remains available, but no urgent tending signal is raised."
    return truncate(f"Cocoon care is {care_state}. Raised support signals: {', '.join(raised)}. This is tending/checkup language, not a judgment.", 700)


def _review_like_count(conn: sqlite3.Connection) -> int:
    total = 0
    for table, column in (
        ("vessel_review_queue", "review_status"),
        ("selene_memory_candidates", "review_status"),
    ):
        if _table_exists(conn, table):
            total += int(
                conn.execute(
                    f"SELECT COUNT(*) FROM {table} WHERE {column} IN ('pending_review', 'needs_context')"
                ).fetchone()[0]
            )
    return total


def _count(conn: sqlite3.Connection, table: str) -> int:
    if not _table_exists(conn, table):
        return 0
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return bool(conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table,)).fetchone())


def _mark_cocoon_idea_started(conn: sqlite3.Connection) -> None:
    if not _table_exists(conn, "selene_organ_idea_intake"):
        return
    conn.execute(
        """
        UPDATE selene_organ_idea_intake
        SET intake_status = 'design_pass_started', updated_at = CURRENT_TIMESTAMP
        WHERE workbench IN ('Cocoon/care', 'intelligenceOS')
          AND intake_status IN ('ready_for_design_pass', 'organ_candidate_review_only')
        """
    )


def _decode_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": int(row["id"]),
        "care_state": row["care_state"],
        "status": row["status"],
        "summary": row["summary"],
        "signals_checked": _loads(row["signals_json"], []),
        "support_suggestions": _loads(row["support_suggestions_json"], []),
        "guard_flags": _loads(row["guard_flags_json"], GUARD_FLAGS),
        "source_refs": _loads(row["source_refs"], []),
        "review_destination": row["review_destination"],
        "review_status": row["review_status"],
        "payload": _loads(row["payload_json"], {}),
        "created_at": row["created_at"],
        **GUARD_FLAGS,
    }


def _loads(raw: str, fallback: Any) -> Any:
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARD_FLAGS, "provenance_boundary": COCOON_CARE_BOUNDARY}
