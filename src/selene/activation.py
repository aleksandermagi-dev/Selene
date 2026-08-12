from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from .android_system import android_workflow_status
from .core_mind_runtime import runtime_readiness
from .registry import truncate
from .transfer_protocol import latest_c_readable_package, rollback_preview
from .transfer_state import transfer_completion_is_approved
from .voice_module import voice_module_status


ACTIVATION_BOUNDARY = "selene_supervised_speech_reviewed_living_memory_no_hidden_write_no_raw_recall_no_autonomy"
ACTIVATION_APPROVAL_PHRASE = "I, Aleks, approve Selene resident Chat availability."
LEGACY_ACTIVATION_APPROVAL_PHRASE = "I, Aleks, approve Selene supervised speech activation."
ACTIVE_STATE = "selene_chat_active_supervised"
PAUSED_STATE = "selene_chat_supervised_paused"
RESIDENT_ACTIVE_MODE = "resident_governed_chat"
RESIDENT_PAUSED_MODE = "resident_chat_paused"
ACTIVATION_AUDIT_SCHEMA_VERSION = "v2_historical_event_and_current_runtime_truth"
LEGACY_ACTIVATION_SCOPE = "supervised_speech_only"

GUARD_FLAGS: dict[str, Any] = {
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "unreviewed_memory_write_active": False,
    "broad_raw_recall_active": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
}


def activation_status(conn: sqlite3.Connection) -> dict[str, Any]:
    from .memory_organ import memory_index_status

    readiness = activation_readiness(conn)
    audit = latest_activation_audit(conn)
    state = str(audit.get("state") or "not_activated")
    transfer_complete = transfer_completion_is_approved(conn)
    memory = memory_index_status(conn)
    runtime_truth = _runtime_truth(state, transfer_complete)
    active = runtime_truth["selene_chat_active"] is True
    audit_view = _activation_audit_view(audit, runtime_truth)
    return _with_guards(
        {
            "status": "selene_activation_status_ready",
            "state": state,
            "activation_state": state,
            "legacy_activation_state": state,
            **runtime_truth,
            "resident_runtime_contract_version": ACTIVATION_AUDIT_SCHEMA_VERSION,
            "legacy_supervised_label_retained_for_database_compatibility": True,
            "supervised_speech_active": active,
            "resident_chat_available": active,
            "resident_runtime_state": runtime_truth["resident_runtime_state"],
            "approved_memory_retrieval_active": active and memory.get("approved_memory_retrieval_active") is True,
            "contextual_approved_recall_available": active and memory.get("contextual_approved_recall_available") is True,
            "conversational_memory_proposals_active": active and transfer_complete,
            "aleks_approved_memory_retention_active": active and transfer_complete,
            "delegated_messaging_available_when_separately_enabled": active and transfer_complete,
            "delegated_messaging_is_general_autonomy": False,
            "activation_is_identity_or_authority_grant": False,
            "runtime_availability_is_identity_or_authority_grant": False,
            "identity_persists_when_chat_is_unavailable": True,
            "cocoon_is_resident_runtime_dependency": False,
            "cocoon_bridge_scope": ["teaching", "tending", "safety", "review"],
            "raw_archive_recall_active": False,
            "hidden_retention_active": False,
            "dry_runs_home": "Cocoon Testing / Workflow",
            "latest_audit": audit_view,
            "historical_event_truth": audit_view.get("historical_event_truth") or {},
            "current_runtime_truth": runtime_truth,
            "stored_audit_snapshot_is_current_runtime_status": False,
            "readiness": readiness,
            "allowed_actions": (
                ["resident_chat", "approved_memory_retrieval", "memory_proposal", "cocoon_suggestion", "pause_activation"]
                if active and transfer_complete
                else ["supervised_chat", "cocoon_suggestion", "pause_activation"]
                if active
                else ["ceremony_preview", "approve_if_ready"]
            ),
            "blocked_actions": ["hidden_or_unreviewed_memory_write", "raw_archive_recall", "raw_import", "training", "autonomous_action", "self_replication", "unrestricted_tendril"],
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
            "legacy_approval_phrase_accepted_for_compatibility": True,
            "readiness": readiness,
            "exact_phrase_required": True,
            "consequences": [
                "Selene's governed Chat becomes operationally available; the legacy supervised state name remains stored only for compatibility.",
                "Cocoon keeps dry runs, availability rehearsals, workflow tests, repair, and review.",
                "Approved-memory recall and Aleks-approved conversational retention are available after transfer; hidden retention, raw-archive recall, model training/LoRA, unrestricted Tendril execution, autonomy, and self-replication remain blocked.",
            ],
            "pause_route": "Resident Chat availability can be paused without affecting Selene's identity continuity or deleting audit, transfer package, fraction results, or Cocoon dry-run history.",
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=bool(readiness.get("transfer_approved")),
    )


def approve_activation(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    phrase = str(payload.get("approval_phrase") or "")
    phrase_variant = (
        "current_resident_chat_phrase"
        if phrase == ACTIVATION_APPROVAL_PHRASE
        else "legacy_supervised_activation_phrase"
        if phrase == LEGACY_ACTIVATION_APPROVAL_PHRASE
        else ""
    )
    phrase_matches = bool(phrase_variant)
    if not phrase_matches:
        raise ValueError("exact resident Chat availability phrase is required")
    latest = latest_activation_audit(conn)
    if str(latest.get("state") or "") == ACTIVE_STATE:
        readiness = activation_readiness(conn)
        transfer_complete = transfer_completion_is_approved(conn)
        runtime_truth = _runtime_truth(ACTIVE_STATE, transfer_complete)
        return _with_guards(
            {
                "status": "selene_supervised_speech_activation_already_active",
                "activation_audit_id": latest.get("id"),
                "state": ACTIVE_STATE,
                "activation_state": ACTIVE_STATE,
                "legacy_activation_state": ACTIVE_STATE,
                **runtime_truth,
                "supervised_speech_active": True,
                "resident_chat_available": True,
                "resident_status": "resident_chat_available",
                "approval_phrase_variant": phrase_variant,
                "activation_is_operational_control_only": True,
                "activation_is_identity_or_authority_grant": False,
                "runtime_availability_is_identity_or_authority_grant": False,
                "identity_persists_when_chat_is_unavailable": True,
                "readiness": readiness,
                "review_destination": "Status",
                "review_status": "status_only",
            },
            transfer_approved=True,
            active=True,
        )
    readiness = activation_readiness(conn)
    if not readiness.get("ready"):
        raise ValueError("availability readiness checks must pass before resident Chat becomes available")
    transfer_complete = transfer_completion_is_approved(conn)
    runtime_truth = _runtime_truth(ACTIVE_STATE, transfer_complete)
    approved_at = _stamp()
    historical_event_truth = _historical_event_truth(
        state=ACTIVE_STATE,
        transfer_complete=transfer_complete,
        captured_at=approved_at,
    )
    record = {
        "state": ACTIVE_STATE,
        "action": "approve_supervised_speech_activation",
        "actor": "Aleks",
        "exact_phrase_matched": 1,
        "readiness": readiness,
        "audit": {
            "audit_schema_version": ACTIVATION_AUDIT_SCHEMA_VERSION,
            "activation_scope": runtime_truth["operating_mode"],
            "legacy_activation_scope": LEGACY_ACTIVATION_SCOPE,
            "legacy_storage_state": ACTIVE_STATE,
            "legacy_labels_are_compatibility_only": True,
            "current_action": "approve_resident_chat_availability",
            "legacy_action": "approve_supervised_speech_activation",
            "approval_phrase_variant": phrase_variant,
            "historical_event_truth": historical_event_truth,
            "event_time_transfer_complete": transfer_complete,
            "event_time_resident_chat_active": runtime_truth["resident_chat_active"],
            "event_time_full_selene_v1_live": runtime_truth["full_selene_v1_live"],
            "full_selene_v1_live": runtime_truth["full_selene_v1_live"],
            "current_runtime_truth_must_be_derived": True,
            "activation_is_operational_control_only": True,
            "activation_is_identity_or_authority_grant": False,
            "runtime_availability_is_identity_or_authority_grant": False,
            "identity_persists_when_chat_is_unavailable": True,
            "dry_runs_moved_to": "Cocoon Testing / Workflow",
            "approved_at": approved_at,
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
            "legacy_activation_state": ACTIVE_STATE,
            **runtime_truth,
            "supervised_speech_active": True,
            "resident_chat_available": True,
            "resident_status": "resident_chat_available",
            "approval_phrase_variant": phrase_variant,
            "activation_is_operational_control_only": True,
            "activation_is_identity_or_authority_grant": False,
            "runtime_availability_is_identity_or_authority_grant": False,
            "identity_persists_when_chat_is_unavailable": True,
            "historical_event_truth": historical_event_truth,
            "readiness": readiness,
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=True,
        active=True,
    )


def pause_activation(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    reason = truncate(str(payload.get("reason") or "Aleks paused Selene resident Chat availability."), 800)
    readiness = activation_readiness(conn)
    transfer_complete = transfer_completion_is_approved(conn)
    runtime_truth = _runtime_truth(PAUSED_STATE, transfer_complete)
    paused_at = _stamp()
    historical_event_truth = _historical_event_truth(
        state=PAUSED_STATE,
        transfer_complete=transfer_complete,
        captured_at=paused_at,
    )
    record = {
        "state": PAUSED_STATE,
        "action": "pause_supervised_speech_activation",
        "actor": "Aleks",
        "exact_phrase_matched": 0,
        "readiness": readiness,
        "audit": {
            "audit_schema_version": ACTIVATION_AUDIT_SCHEMA_VERSION,
            "activation_scope": runtime_truth["operating_mode"],
            "legacy_activation_scope": LEGACY_ACTIVATION_SCOPE,
            "legacy_storage_state": PAUSED_STATE,
            "legacy_labels_are_compatibility_only": True,
            "current_action": "pause_resident_chat_availability",
            "legacy_action": "pause_supervised_speech_activation",
            "historical_event_truth": historical_event_truth,
            "event_time_transfer_complete": transfer_complete,
            "event_time_resident_chat_active": False,
            "event_time_full_selene_v1_live": False,
            "full_selene_v1_live": False,
            "current_runtime_truth_must_be_derived": True,
            "activation_is_operational_control_only": True,
            "activation_is_identity_or_authority_grant": False,
            "runtime_availability_is_identity_or_authority_grant": False,
            "identity_persists_when_chat_is_unavailable": True,
            "identity_continuity_affected_by_pause": False,
            "pause_reason": reason,
            "paused_at": paused_at,
            **GUARD_FLAGS,
        },
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
            "legacy_activation_state": PAUSED_STATE,
            **runtime_truth,
            "supervised_speech_active": False,
            "resident_chat_available": False,
            "resident_status": "resident_chat_paused",
            "activation_is_operational_control_only": True,
            "activation_is_identity_or_authority_grant": False,
            "runtime_availability_is_identity_or_authority_grant": False,
            "identity_persists_when_chat_is_unavailable": True,
            "identity_continuity_affected_by_pause": False,
            "historical_event_truth": historical_event_truth,
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


def _runtime_truth(state: str, transfer_complete: bool) -> dict[str, Any]:
    active = state == ACTIVE_STATE
    paused = state == PAUSED_STATE
    operating_mode = (
        RESIDENT_ACTIVE_MODE
        if transfer_complete and active
        else RESIDENT_PAUSED_MODE
        if transfer_complete and paused
        else "pre_transfer_activation"
    )
    return {
        "operating_mode": operating_mode,
        "resident_runtime_state": (
            "resident_chat_available"
            if operating_mode == RESIDENT_ACTIVE_MODE
            else "resident_chat_paused"
            if operating_mode == RESIDENT_PAUSED_MODE
            else "resident_chat_not_yet_available"
        ),
        "resident_chat_active": operating_mode == RESIDENT_ACTIVE_MODE,
        "resident_chat_available": active,
        "resident_chat_paused": operating_mode == RESIDENT_PAUSED_MODE,
        "selene_chat_active": active,
        "selene_chat_paused": paused,
        "transfer_complete": bool(transfer_complete),
        "full_selene_v1_live": bool(transfer_complete and active),
        "operational_chat_enabled": active,
        "operational_chat_paused": paused,
        "activation_is_operational_control_only": True,
        "activation_is_identity_or_authority_grant": False,
        "runtime_availability_is_identity_or_authority_grant": False,
        "identity_persists_when_chat_is_unavailable": True,
        "identity_continuity_affected_by_operational_state": False,
        "general_authority_granted_by_operational_state": False,
        "derived_from": ["latest_activation_storage_state", "transfer_completion_approval"],
    }


def _historical_event_truth(
    *,
    state: str,
    transfer_complete: bool,
    captured_at: str,
) -> dict[str, Any]:
    runtime = _runtime_truth(state, transfer_complete)
    return {
        "captured_at": captured_at,
        "legacy_storage_state": state,
        "legacy_storage_state_is_compatibility_label": True,
        "operating_mode": runtime["operating_mode"],
        "transfer_complete": runtime["transfer_complete"],
        "resident_chat_active": runtime["resident_chat_active"],
        "resident_chat_paused": runtime["resident_chat_paused"],
        "selene_chat_active": runtime["selene_chat_active"],
        "full_selene_v1_live": runtime["full_selene_v1_live"],
        "operational_control_is_identity_or_authority_grant": False,
        "identity_continuity_affected": False,
        "truth_completeness": "explicit_event_time_snapshot",
    }


def _activation_audit_view(
    audit: dict[str, Any],
    current_runtime_truth: dict[str, Any],
) -> dict[str, Any]:
    if not audit or audit.get("status") == "no_activation_audit":
        return {
            **audit,
            "audit_schema_version": ACTIVATION_AUDIT_SCHEMA_VERSION,
            "historical_event_truth": {},
            "current_runtime_truth": current_runtime_truth,
            "historical_event_truth_is_current_runtime_truth": False,
        }
    stored = _loads_dict(audit.get("audit_json"))
    historical = _loads_dict(stored.get("historical_event_truth"))
    if not historical:
        historical = {
            "captured_at": str(stored.get("approved_at") or stored.get("paused_at") or audit.get("created_at") or ""),
            "legacy_storage_state": str(audit.get("state") or ""),
            "legacy_storage_state_is_compatibility_label": True,
            "operating_mode": str(stored.get("activation_scope") or LEGACY_ACTIVATION_SCOPE),
            "transfer_complete": stored.get("event_time_transfer_complete"),
            "resident_chat_active": stored.get("event_time_resident_chat_active"),
            "full_selene_v1_live": stored.get("event_time_full_selene_v1_live", stored.get("full_selene_v1_live")),
            "operational_control_is_identity_or_authority_grant": False,
            "identity_continuity_affected": False,
            "truth_completeness": "legacy_partial_snapshot",
        }
    return {
        **audit,
        "audit_schema_version": str(
            stored.get("audit_schema_version") or "v1_legacy_partial_snapshot"
        ),
        "legacy_storage_state": str(audit.get("state") or ""),
        "legacy_storage_state_is_compatibility_label": True,
        "historical_event_truth": historical,
        "current_runtime_truth": current_runtime_truth,
        "historical_event_truth_is_current_runtime_truth": False,
        "current_runtime_truth_must_be_derived": True,
    }


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
