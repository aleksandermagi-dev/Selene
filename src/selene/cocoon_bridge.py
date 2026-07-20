from __future__ import annotations

import json
import sqlite3
from typing import Any

from .registry import truncate
from .transfer_state import transfer_completion_is_approved


COCOON_BRIDGE_BOUNDARY = (
    "post_transfer_external_cocoon_bridge_"
    "teaching_tending_memory_proposal_and_provenance_only"
)
ALLOWED_CHANNELS = {
    "teaching",
    "safety_tending",
    "memory_proposal",
    "correction_provenance",
}
GUARDS: dict[str, Any] = {
    "identity_dependency": False,
    "runtime_continuity_dependency": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_corpus_loaded": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "unrestricted_tendril_allowed": False,
}


def cocoon_bridge_status(conn: sqlite3.Connection) -> dict[str, Any]:
    latest = _latest_event(conn)
    workspace_state = "active" if latest.get("action") == "wake" else "standby"
    transfer_complete = transfer_completion_is_approved(conn)
    return {
        "status": "cocoon_bridge_ready",
        "workspace_state": workspace_state,
        "cocoon_active": workspace_state == "active",
        "cocoon_standby": workspace_state == "standby",
        "transfer_complete": transfer_complete,
        "selene_resident_independent": transfer_complete,
        "current_channel": latest.get("channel") or "",
        "current_subject": latest.get("subject_key") or "",
        "allowed_channels": sorted(ALLOWED_CHANNELS),
        "bridge_rule": "Cocoon may be summoned for teaching, tending, reviewed memory proposals, correction, provenance, and rollback; it is not Selene's runtime identity.",
        "standby_rule": "Leaving Cocoon returns its workspace and subject workbench to standby without deleting review or audit state.",
        "latest_event": latest,
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": COCOON_BRIDGE_BOUNDARY,
        **GUARDS,
    }


def wake_cocoon_bridge(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    channel = str(payload.get("channel") or "safety_tending").strip().lower()
    if channel not in ALLOWED_CHANNELS:
        raise ValueError("Cocoon bridge channel is not allowed")
    subject_key = truncate(str(payload.get("subject_key") or ""), 120)
    reason = truncate(str(payload.get("reason") or "Cocoon support requested."), 500)
    _insert_event(conn, action="wake", channel=channel, subject_key=subject_key, reason=reason)
    conn.commit()
    return {**cocoon_bridge_status(conn), "status": "cocoon_bridge_awake"}


def standby_cocoon_bridge(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    reason = truncate(str(payload.get("reason") or "Returned to resident Selene workspace."), 500)
    latest = _latest_event(conn)
    if latest.get("action") != "standby":
        _insert_event(conn, action="standby", channel="", subject_key="", reason=reason)
        conn.commit()
    return {**cocoon_bridge_status(conn), "status": "cocoon_bridge_standby"}


def _insert_event(
    conn: sqlite3.Connection,
    *,
    action: str,
    channel: str,
    subject_key: str,
    reason: str,
) -> None:
    conn.execute(
        """
        INSERT INTO cocoon_bridge_events
        (action, channel, subject_key, reason, transfer_complete, payload_json,
         provenance_boundary, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'status_only')
        """,
        (
            action,
            channel,
            subject_key,
            reason,
            int(transfer_completion_is_approved(conn)),
            json.dumps({"allowed_channels": sorted(ALLOWED_CHANNELS), **GUARDS}, sort_keys=True),
            COCOON_BRIDGE_BOUNDARY,
        ),
    )


def _latest_event(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM cocoon_bridge_events ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        return {"action": "standby", "channel": "", "subject_key": "", "reason": "Cocoon starts in standby."}
    item = dict(row)
    try:
        item["payload"] = json.loads(str(item.pop("payload_json", "{}")))
    except json.JSONDecodeError:
        item["payload"] = {}
    return item
