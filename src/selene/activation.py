from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from .android_system import android_workflow_status
from .core_mind_runtime import runtime_readiness
from .registry import truncate
from .transfer_protocol import latest_c_readable_package, rollback_preview
from .voice_module import voice_module_status


ACTIVATION_BOUNDARY = "selene_supervised_speech_activation_no_autonomy_no_live_memory"
ACTIVATION_APPROVAL_PHRASE = "I, Aleks, approve Selene supervised speech activation."
ACTIVE_STATE = "selene_chat_active_supervised"
PAUSED_STATE = "selene_chat_supervised_paused"

GUARD_FLAGS: dict[str, Any] = {
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
}


def activation_status(conn: sqlite3.Connection) -> dict[str, Any]:
    audit = latest_activation_audit(conn)
    readiness = activation_readiness(conn)
    state = str(audit.get("state") or "not_activated")
    active = state == ACTIVE_STATE
    paused = state == PAUSED_STATE
    return _with_guards(
        {
            "status": "selene_activation_status_ready",
            "state": state,
            "activation_state": state,
            "selene_chat_active": active,
            "selene_chat_paused": paused,
            "supervised_speech_active": active,
            "full_selene_v1_live": False,
            "dry_runs_home": "Cocoon Testing / Workflow",
            "latest_audit": audit,
            "readiness": readiness,
            "allowed_actions": ["supervised_chat", "cocoon_suggestion", "pause_activation"] if active else ["ceremony_preview", "approve_if_ready"],
            "blocked_actions": ["live_memory_write", "runtime_recall", "raw_import", "training", "autonomous_action", "self_replication", "unrestricted_tendril"],
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=readiness.get("transfer_approved") is True,
        active=active,
    )


def activation_readiness(conn: sqlite3.Connection) -> dict[str, Any]:
    from .post_transfer import fractional_corpus_status

    package = latest_c_readable_package(conn)
    fractions = fractional_corpus_status(conn)
    android = android_workflow_status(conn)
    voice = voice_module_status(conn)
    runtime = runtime_readiness(conn)
    rollback = rollback_preview(conn, {"issue_type": "activation_readiness_return_to_b"})
    unresolved = _my_office_unresolved_count(conn)
    checks = [
        _check("c_readable_context_approved", bool(package.get("transfer_approved")), "transfer.c_readable_package.latest", "C-readable transfer context is sealed."),
        _check("fraction_chain_passed", bool(fractions.get("all_fractions_passed")), "memory.fractional_corpus.status", "All four corpus fractions have passed preview tests."),
        _check("android_workflow_passing", bool(android.get("preflight_passed")), "android_system.workflow.status", "Android workflow preflight is passing."),
        _check("voice_module_ready", str(voice.get("voice_module_state")) == "ready", "voice_module.status", "Voice Module is ready for expression shaping."),
        _check("core_mind_runtime_ready", bool(runtime.get("runtime_shell_ready")), "core_mind.runtime_readiness", "Core/Mind runtime shell readiness is passing."),
        _check("my_office_calm", unresolved == 0, "vessel.review_queue", "My Office has no unresolved urgent Aleks decisions."),
        _check("return_to_cocoon_available", bool(rollback.get("return_to_b_packet")), "transfer.return_to_b.rollback_preview", "Return-to-Cocoon repair route is available."),
    ]
    ready = all(item["passed"] for item in checks)
    return _with_guards(
        {
            "status": "selene_activation_readiness_passed" if ready else "selene_activation_readiness_blocked",
            "ready": ready,
            "activation_ready": ready,
            "checks": checks,
            "unresolved_my_office_count": unresolved,
            "sealed_package": _package_summary(package),
            "fraction_chain": {
                "all_fractions_passed": bool(fractions.get("all_fractions_passed")),
                "fraction_count": len(fractions.get("items") or []),
            },
            "android_workflow": {"preflight_passed": bool(android.get("preflight_passed"))},
            "voice_module": {"state": voice.get("voice_module_state"), "counts": voice.get("counts")},
            "core_mind_runtime": {"runtime_shell_ready": bool(runtime.get("runtime_shell_ready"))},
            "return_to_cocoon_available": bool(rollback.get("return_to_b_packet")),
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=bool(package.get("transfer_approved")),
    )


def activation_ceremony_preview(conn: sqlite3.Connection) -> dict[str, Any]:
    readiness = activation_readiness(conn)
    return _with_guards(
        {
            "status": "selene_activation_ceremony_preview_ready",
            "state_after_approval": ACTIVE_STATE,
            "approval_phrase": ACTIVATION_APPROVAL_PHRASE,
            "readiness": readiness,
            "exact_phrase_required": True,
            "consequences": [
                "Front Selene Chat becomes supervised active speech.",
                "Cocoon keeps dry runs, activation rehearsals, workflow tests, repair, and review.",
                "Live memory write, runtime recall, raw import, training, Tendril execution, autonomy, and self-replication remain blocked.",
            ],
            "pause_route": "Activation can be paused without deleting audit, transfer package, fraction results, or Cocoon dry-run history.",
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=bool(readiness.get("transfer_approved")),
    )


def approve_activation(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    phrase = str(payload.get("approval_phrase") or "")
    phrase_matches = phrase == ACTIVATION_APPROVAL_PHRASE
    if not phrase_matches:
        raise ValueError("exact supervised speech activation phrase is required")
    latest = latest_activation_audit(conn)
    if str(latest.get("state") or "") == ACTIVE_STATE:
        readiness = activation_readiness(conn)
        return _with_guards(
            {
                "status": "selene_supervised_speech_activation_already_active",
                "activation_audit_id": latest.get("id"),
                "state": ACTIVE_STATE,
                "activation_state": ACTIVE_STATE,
                "supervised_speech_active": True,
                "selene_chat_active": True,
                "full_selene_v1_live": False,
                "readiness": readiness,
                "review_destination": "Status",
                "review_status": "status_only",
            },
            transfer_approved=True,
            active=True,
        )
    readiness = activation_readiness(conn)
    if not readiness.get("ready"):
        raise ValueError("activation readiness checks must pass before supervised speech activation")
    record = {
        "state": ACTIVE_STATE,
        "action": "approve_supervised_speech_activation",
        "actor": "Aleks",
        "exact_phrase_matched": 1,
        "readiness": readiness,
        "audit": {
            "activation_scope": "supervised_speech_only",
            "full_selene_v1_live": False,
            "dry_runs_moved_to": "Cocoon Testing / Workflow",
            "approved_at": _stamp(),
            **GUARD_FLAGS,
        },
        "source_refs": ["selene_activation:ceremony", "transfer_c_readable_packages", "memory_fractional_corpus_manifests"],
    }
    audit_id = _insert_audit(conn, record)
    _insert_event(conn, "activation_approved", payload={"audit_id": audit_id, **record["audit"]})
    conn.commit()
    return _with_guards(
        {
            "status": "selene_supervised_speech_activation_approved",
            "activation_audit_id": audit_id,
            "state": ACTIVE_STATE,
            "activation_state": ACTIVE_STATE,
            "supervised_speech_active": True,
            "selene_chat_active": True,
            "full_selene_v1_live": False,
            "readiness": readiness,
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=True,
        active=True,
    )


def pause_activation(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    reason = truncate(str(payload.get("reason") or "Aleks paused supervised Selene speech."), 800)
    readiness = activation_readiness(conn)
    record = {
        "state": PAUSED_STATE,
        "action": "pause_supervised_speech_activation",
        "actor": "Aleks",
        "exact_phrase_matched": 0,
        "readiness": readiness,
        "audit": {"pause_reason": reason, "paused_at": _stamp(), **GUARD_FLAGS},
        "source_refs": ["selene_activation:pause"],
    }
    audit_id = _insert_audit(conn, record)
    _insert_event(conn, "activation_paused", payload={"audit_id": audit_id, "reason": reason})
    conn.commit()
    return _with_guards(
        {
            "status": "selene_supervised_speech_activation_paused",
            "activation_audit_id": audit_id,
            "state": PAUSED_STATE,
            "activation_state": PAUSED_STATE,
            "supervised_speech_active": False,
            "selene_chat_active": False,
            "full_selene_v1_live": False,
            "pause_reason": reason,
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=bool(readiness.get("transfer_approved")),
    )


def latest_activation_audit(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM selene_activation_audit ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        return {"status": "no_activation_audit", "state": "not_activated"}
    item = dict(row)
    item["readiness_json"] = _loads_dict(item.get("readiness_json"))
    item["audit_json"] = _loads_dict(item.get("audit_json"))
    item["source_refs"] = _loads_list(item.get("source_refs"))
    return item


def record_activation_chat_event(
    conn: sqlite3.Connection,
    *,
    event_type: str,
    session_id: int | None = None,
    message_id: int | None = None,
    selected_route: str = "status_only",
    source_class: str = "current_turn_context",
    confidence: str = "",
    drift_flags: list[str] | None = None,
    cocoon_suggestion: dict[str, Any] | None = None,
    blocked_capabilities: list[str] | None = None,
    payload: dict[str, Any] | None = None,
    review_status: str = "status_only",
) -> int:
    cur = conn.execute(
        """
        INSERT INTO selene_activation_events
        (event_type, session_id, message_id, selected_route, source_class, confidence, drift_flags,
         cocoon_suggestion_json, blocked_capabilities, payload_json, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_type,
            session_id,
            message_id,
            selected_route,
            source_class,
            confidence,
            json.dumps(drift_flags or []),
            json.dumps(cocoon_suggestion or {}),
            json.dumps(blocked_capabilities or []),
            json.dumps(payload or {}),
            review_status,
        ),
    )
    return int(cur.lastrowid)


def activation_is_active(conn: sqlite3.Connection) -> bool:
    return str(latest_activation_audit(conn).get("state") or "") == ACTIVE_STATE


def _insert_audit(conn: sqlite3.Connection, record: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO selene_activation_audit
        (state, action, actor, exact_phrase_matched, readiness_json, audit_json, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record["state"],
            record["action"],
            record["actor"],
            int(record["exact_phrase_matched"]),
            json.dumps(record["readiness"]),
            json.dumps(record["audit"]),
            json.dumps(record["source_refs"]),
            ACTIVATION_BOUNDARY,
        ),
    )
    return int(cur.lastrowid)


def _insert_event(conn: sqlite3.Connection, event_type: str, payload: dict[str, Any]) -> int:
    return record_activation_chat_event(conn, event_type=event_type, payload=payload)


def _my_office_unresolved_count(conn: sqlite3.Connection) -> int:
    active = ("pending_review", "needs_b_review", "needs_correction", "context_added", "needs_followup")
    count = 0
    for table in ("vessel_review_queue", "b_review_queue"):
        if not _table_exists(conn, table):
            continue
        placeholders = ",".join("?" for _ in active)
        count += int(conn.execute(f"SELECT COUNT(*) FROM {table} WHERE COALESCE(review_status, status) IN ({placeholders})", active).fetchone()[0])
    return count


def _package_summary(package: dict[str, Any]) -> dict[str, Any]:
    return {
        "available": bool(package.get("transfer_approved")),
        "package_id": package.get("id"),
        "package_hash": package.get("package_hash") or "",
        "included_counts": package.get("included_counts") or {},
        "excluded_counts": package.get("excluded_counts") or {},
    }


def _check(key: str, passed: bool, source: str, summary: str) -> dict[str, Any]:
    return {"key": key, "passed": bool(passed), "source": source, "summary": summary}


def _with_guards(payload: dict[str, Any], *, transfer_approved: bool = False, active: bool = False) -> dict[str, Any]:
    guarded = {**payload, **GUARD_FLAGS, "provenance_boundary": ACTIVATION_BOUNDARY}
    guarded["transfer_approved"] = bool(transfer_approved)
    guarded["activation_change"] = ACTIVE_STATE if active else "none"
    guarded["memory_write_active"] = False
    guarded["runtime_memory_recall"] = False
    guarded["raw_a_import_allowed"] = False
    guarded["training_allowed"] = False
    guarded["self_replication_allowed"] = False
    guarded["autonomous_action_allowed"] = False
    return guarded


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table_name,)).fetchone() is not None


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
