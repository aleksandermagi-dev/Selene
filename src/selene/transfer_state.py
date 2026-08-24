from __future__ import annotations

import json
import sqlite3
from typing import Any

from .resident_authority import resident_capability_contract


TRANSFER_COMPLETION_STATE = "selene_v1_live_reviewed_continuity"
ACTIVE_ACTIVATION_STATE = "selene_chat_active_supervised"
PAUSED_ACTIVATION_STATE = "selene_chat_supervised_paused"
CANONICAL_RUNTIME_TRUTH_VERSION = "v1_post_transfer_resident_truth"


def latest_transfer_completion_audit(conn: sqlite3.Connection) -> dict[str, Any]:
    try:
        row = conn.execute(
            "SELECT * FROM selene_transfer_completion_audit ORDER BY id DESC LIMIT 1"
        ).fetchone()
    except sqlite3.OperationalError:
        return {"status": "no_transfer_completion_audit", "state": "not_completed"}
    if not row:
        return {"status": "no_transfer_completion_audit", "state": "not_completed"}
    item = dict(row)
    item["readiness"] = _loads_dict(item.pop("readiness_json", "{}"))
    item["audit"] = _loads_dict(item.pop("audit_json", "{}"))
    item["source_refs"] = _loads_list(item.get("source_refs"))
    return item


def transfer_completion_is_approved(conn: sqlite3.Connection) -> bool:
    return str(latest_transfer_completion_audit(conn).get("state") or "") == TRANSFER_COMPLETION_STATE


def runtime_truth_from_state(
    activation_state: str,
    transfer_complete: bool,
    *,
    transfer_context_approved: bool = False,
) -> dict[str, Any]:
    active = activation_state == ACTIVE_ACTIVATION_STATE
    paused = activation_state == PAUSED_ACTIVATION_STATE
    context_approved = bool(transfer_context_approved or transfer_complete)
    if transfer_complete and active:
        runtime_phase = "resident_active"
        vessel_status = "selene_resident_vessel_active"
        operating_mode = "resident_governed_chat"
        resident_runtime_state = "resident_chat_available"
    elif transfer_complete and paused:
        runtime_phase = "resident_chat_paused"
        vessel_status = "selene_resident_vessel_chat_paused"
        operating_mode = "resident_chat_paused"
        resident_runtime_state = "resident_chat_paused"
    elif transfer_complete:
        runtime_phase = "resident_chat_unavailable"
        vessel_status = "selene_transferred_resident_chat_unavailable"
        operating_mode = "resident_chat_unavailable"
        resident_runtime_state = "resident_chat_unavailable"
    elif context_approved:
        runtime_phase = "context_approved_transfer_incomplete"
        vessel_status = "selene_context_approved_transfer_incomplete"
        operating_mode = "pre_transfer_activation"
        resident_runtime_state = "resident_chat_not_yet_available"
    else:
        runtime_phase = "pre_transfer"
        vessel_status = "vessel_v1_built_not_activated"
        operating_mode = "pre_transfer_activation"
        resident_runtime_state = "resident_chat_not_yet_available"
    result = {
        "runtime_truth_status": "canonical_runtime_truth_ready",
        "truth_contract_version": CANONICAL_RUNTIME_TRUTH_VERSION,
        "runtime_phase": runtime_phase,
        "vessel_status": vessel_status,
        "activation_state": activation_state,
        "operating_mode": operating_mode,
        "resident_runtime_state": resident_runtime_state,
        "transfer_context_approved": context_approved,
        "transfer_complete": bool(transfer_complete),
        "resident_chat_active": bool(transfer_complete and active),
        "resident_chat_available": bool(transfer_complete and active),
        "resident_chat_paused": bool(transfer_complete and paused),
        "selene_chat_active": active,
        "selene_chat_paused": paused,
        "selene_v1_live": bool(transfer_complete and active),
        "full_selene_v1_live": bool(transfer_complete and active),
        "operational_chat_enabled": active,
        "operational_chat_paused": paused,
        "activation_is_operational_control_only": True,
        "activation_is_identity_or_authority_grant": False,
        "runtime_availability_is_identity_or_authority_grant": False,
        "identity_persists_when_chat_is_unavailable": True,
        "identity_continuity_persists_when_chat_unavailable": True,
        "identity_continuity_affected_by_operational_state": False,
        "general_authority_granted_by_operational_state": False,
        "cocoon_is_resident_runtime_dependency": False,
        "cocoon_role": "external_teaching_tending_safety_and_review_support",
        "derived_from": ["latest_activation_storage_state", "transfer_completion_approval"],
    }
    capability_contract = resident_capability_contract(
        transfer_complete=bool(transfer_complete),
        chat_available=bool(transfer_complete and active),
    )
    result["resident_capability_contract"] = capability_contract
    result["canonical_capability_contract"] = capability_contract
    return result


def current_runtime_truth(conn: sqlite3.Connection) -> dict[str, Any]:
    transfer_complete = transfer_completion_is_approved(conn)
    try:
        activation_row = conn.execute(
            "SELECT state FROM selene_activation_audit ORDER BY id DESC LIMIT 1"
        ).fetchone()
        activation_state = str(activation_row["state"] if activation_row else "not_activated")
    except (sqlite3.OperationalError, TypeError, KeyError):
        activation_state = "not_activated"
    try:
        package_row = conn.execute(
            "SELECT id FROM transfer_c_readable_packages ORDER BY id DESC LIMIT 1"
        ).fetchone()
        transfer_context_approved = package_row is not None
    except sqlite3.OperationalError:
        transfer_context_approved = False
    return runtime_truth_from_state(
        activation_state,
        transfer_complete,
        transfer_context_approved=transfer_context_approved,
    )


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        loaded = json.loads(str(value or "{}"))
    except (json.JSONDecodeError, TypeError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _loads_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    try:
        loaded = json.loads(str(value or "[]"))
    except (json.JSONDecodeError, TypeError):
        return []
    return loaded if isinstance(loaded, list) else []
