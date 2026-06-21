from __future__ import annotations

import sqlite3
from typing import Any

from .chat import get_session, list_sessions, send_chat_message
from .registry import truncate
from .vessel_construction import create_chest_holding_item


MOBILE_BOUNDARY_FLAGS: dict[str, Any] = {
    "mobile_surface": "chat_only",
    "desktop_remains_control_room": True,
    "activation_change": "none",
    "transfer_approved": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "cocoon_actions_allowed": False,
    "review_decisions_allowed": False,
    "diagnostics_allowed": False,
    "public_release_sync_allowed": False,
}


def mobile_guard_flags() -> dict[str, Any]:
    return dict(MOBILE_BOUNDARY_FLAGS)


def mobile_health(health: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "status": "mobile_chat_ready",
        "surface": "ios_private_web_companion",
        "allowed_actions": ["chat_send", "session_list", "session_detail", "review_capture"],
        "blocked_actions": [
            "my_office_decisions",
            "cocoon_build_actions",
            "diagnostics",
            "public_release_sync",
            "transfer",
            "activation",
            "live_memory_write",
            "runtime_recall",
            "raw_archive_import",
            "file_browsing",
            "admin_routes",
        ],
        "boundary_note": "Phone is a chat doorway; desktop Selene remains the control room.",
        "guard_flags": mobile_guard_flags(),
    }
    if health is not None:
        payload["sidecar"] = health
    return payload


def mobile_send_chat(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    result = send_chat_message(
        conn,
        str(payload.get("text") or ""),
        int(payload["session_id"]) if payload.get("session_id") else None,
        "disabled",
    )
    result["mobile"] = {
        "status": "mobile_chat_message_recorded",
        "review_capture_created": bool(result.get("save_request")),
        "guard_flags": mobile_guard_flags(),
    }
    return result


def mobile_list_sessions(conn: sqlite3.Connection) -> dict[str, Any]:
    return {
        "items": list_sessions(conn),
        "guard_flags": mobile_guard_flags(),
    }


def mobile_get_session(conn: sqlite3.Connection, session_id: int) -> dict[str, Any] | None:
    session = get_session(conn, session_id)
    if session is None:
        return None
    session["guard_flags"] = mobile_guard_flags()
    return session


def mobile_capture_review(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    text = truncate(str(payload.get("text") or payload.get("note") or ""), 1000)
    if not text.strip():
        raise ValueError("capture text is required")
    session_id = int(payload["session_id"]) if payload.get("session_id") else None
    result = send_chat_message(conn, f"save this for desktop My Office review: {text}", session_id, "disabled")
    save_request = result.get("save_request") or {}
    refs = [f"mobile_chat_session:{result['session_id']}"]
    if save_request.get("id"):
        refs.append(f"continuity_save_requests:{save_request['id']}")
    chest_item = create_chest_holding_item(conn, {
        "item_type": "mobile_capture",
        "title": "Mobile review capture",
        "summary": "Phone capture saved for desktop review as holding-space material. It is not durable memory.",
        "salience_labels": ["mobile_capture", "desktop_review", "not_memory_yet"],
        "source_refs": refs,
        "linked_packet_refs": refs,
        "review_status": "review_only",
        "payload_json": {
            "mobile_capture": True,
            "session_id": result["session_id"],
            "save_request_id": save_request.get("id"),
            "desktop_review_only": True,
        },
    })
    return {
        "status": "mobile_review_capture_recorded",
        "session_id": result["session_id"],
        "save_request": save_request,
        "chest_item": chest_item,
        "review_destination": "desktop_my_office",
        "guard_flags": mobile_guard_flags(),
    }


def mobile_blocked_action(action: str) -> dict[str, Any]:
    return {
        "status": "mobile_action_blocked",
        "action": action,
        "reason": "Mobile v1 is chat and review capture only. Open the desktop Selene console for cocoon, review, build, diagnostic, release, memory, transfer, or activation work.",
        "guard_flags": mobile_guard_flags(),
    }
