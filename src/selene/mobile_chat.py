from __future__ import annotations

import sqlite3
import json
import secrets
import socket
from typing import Any

from .chat import get_session, list_sessions, send_chat_message
from .activation import activation_is_active
from .paths import local_data_dir
from .registry import truncate
from .selene_chat import get_selene_chat_session, list_selene_chat_sessions, send_selene_chat
from .vessel_construction import create_chest_holding_item


MOBILE_BOUNDARY_FLAGS: dict[str, Any] = {
    "mobile_surface": "chat_only",
    "access_mode": "local_only",
    "lan_pairing_enabled": False,
    "same_device_or_dev_preview": True,
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
PAIRING_CONFIG = "mobile_pairing.json"


def mobile_guard_flags() -> dict[str, Any]:
    return dict(MOBILE_BOUNDARY_FLAGS)


def _mobile_guard_flags_for_pairing(pairing: dict[str, Any] | None = None) -> dict[str, Any]:
    pairing = pairing or {}
    flags = mobile_guard_flags()
    flags["lan_pairing_enabled"] = bool(pairing.get("enabled"))
    flags["same_device_or_dev_preview"] = not bool(pairing.get("enabled"))
    flags["access_mode"] = "private_lan_pairing" if pairing.get("enabled") else "local_only"
    return flags


def mobile_pairing_config_path() -> Any:
    return local_data_dir() / PAIRING_CONFIG


def mobile_pairing_state() -> dict[str, Any]:
    path = mobile_pairing_config_path()
    try:
        raw = path.read_text(encoding="utf-8")
        data = raw and json.loads(raw)
    except (OSError, ValueError):
        data = {}
    enabled = bool(data.get("enabled"))
    code = str(data.get("pairing_code") or "")
    bind = "0.0.0.0" if enabled else "127.0.0.1"
    urls = [f"http://{ip}:8766/mobile?pairing={code}" for ip in _local_ipv4_addresses() if enabled and code]
    return {
        "status": "mobile_pairing_enabled" if enabled else "mobile_pairing_disabled",
        "enabled": enabled,
        "lan_pairing_enabled": enabled,
        "bind": bind,
        "pairing_code": code if enabled else "",
        "phone_urls": urls,
        "restart_required": False,
        "guard_flags": _mobile_guard_flags_for_pairing({"enabled": enabled}),
    }


def mobile_pairing_enable(current_bind: str = "127.0.0.1") -> dict[str, Any]:
    code = secrets.token_urlsafe(12)
    path = mobile_pairing_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"enabled": True, "pairing_code": code}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    state = mobile_pairing_state()
    state["status"] = "mobile_pairing_enabled_restart_required" if current_bind == "127.0.0.1" else "mobile_pairing_enabled"
    state["restart_required"] = current_bind == "127.0.0.1"
    state["message"] = "Close and reopen Selene to expose the private LAN mobile doorway." if state["restart_required"] else "Private LAN mobile doorway is enabled."
    return state


def mobile_pairing_disable() -> dict[str, Any]:
    path = mobile_pairing_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"enabled": False}, indent=2), encoding="utf-8")
    state = mobile_pairing_state()
    state["message"] = "Private LAN mobile doorway disabled. Close and reopen Selene if it was currently bound to LAN."
    return state


def mobile_pairing_code_valid(value: str | None) -> bool:
    state = mobile_pairing_state()
    expected = str(state.get("pairing_code") or "")
    return bool(state.get("enabled") and expected and secrets.compare_digest(str(value or ""), expected))


def mobile_health(health: dict[str, Any] | None = None) -> dict[str, Any]:
    pairing = mobile_pairing_state()
    payload: dict[str, Any] = {
        "status": "mobile_chat_ready",
        "surface": "mobile_chat_lan_companion" if pairing["enabled"] else "mobile_chat_same_device_dev_preview",
        "access_mode": "private_lan_pairing" if pairing["enabled"] else "local_only",
        "lan_pairing_enabled": pairing["enabled"],
        "same_device_or_dev_preview": not pairing["enabled"],
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
        "boundary_note": "Mobile v1 is a private chat doorway for speaking or typing with Selene and saving review notes. Desktop Selene remains the control room.",
        "pairing": pairing,
        "guard_flags": _mobile_guard_flags_for_pairing(pairing),
    }
    if health is not None:
        payload["sidecar"] = health
    return payload


def mobile_send_chat(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text") or "")
    session_id = int(payload["session_id"]) if payload.get("session_id") else None
    if activation_is_active(conn):
        result = send_selene_chat(conn, {"text": text, "session_id": session_id or 0, "speaker": "mobile"})
        result["mobile_chat_engine"] = "selene_chat_active_supervised"
    else:
        result = send_chat_message(conn, text, session_id, "disabled")
        result["mobile_chat_engine"] = "legacy_native_preview"
    result["mobile"] = {
        "status": "mobile_chat_message_recorded",
        "review_capture_created": bool(result.get("save_request")),
        "source_class": "local_supervised_chat_history" if activation_is_active(conn) else "mobile_preview_chat",
        "guard_flags": _mobile_guard_flags_for_pairing(mobile_pairing_state()),
    }
    return result


def mobile_list_sessions(conn: sqlite3.Connection) -> dict[str, Any]:
    if activation_is_active(conn):
        result = list_selene_chat_sessions(conn)
        result["items"] = result.get("items", [])
        result["mobile_chat_engine"] = "selene_chat_active_supervised"
        result["guard_flags"] = mobile_guard_flags()
        return result
    return {
        "items": list_sessions(conn),
        "mobile_chat_engine": "legacy_native_preview",
        "guard_flags": _mobile_guard_flags_for_pairing(mobile_pairing_state()),
    }


def mobile_get_session(conn: sqlite3.Connection, session_id: int) -> dict[str, Any] | None:
    if activation_is_active(conn):
        session = get_selene_chat_session(conn, session_id)
        if session is not None:
            session["mobile_chat_engine"] = "selene_chat_active_supervised"
            session["guard_flags"] = mobile_guard_flags()
        return session
    session = get_session(conn, session_id)
    if session is None:
        return None
    session["guard_flags"] = _mobile_guard_flags_for_pairing(mobile_pairing_state())
    return session


def mobile_capture_review(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    text = truncate(str(payload.get("text") or payload.get("note") or ""), 1000)
    if not text.strip():
        raise ValueError("capture text is required")
    session_id = int(payload["session_id"]) if payload.get("session_id") else None
    if activation_is_active(conn):
        session_id = _ensure_mobile_selene_session(conn, session_id, text)
        save_request: dict[str, Any] = {}
        refs = [f"selene_chat_session:{session_id}", "mobile_capture:review_only"]
    else:
        result = send_chat_message(conn, f"save this for desktop My Office review: {text}", session_id, "disabled")
        session_id = int(result["session_id"])
        save_request = result.get("save_request") or {}
        refs = [f"mobile_chat_session:{session_id}"]
        if save_request.get("id"):
            refs.append(f"continuity_save_requests:{save_request['id']}")
    chest_item = create_chest_holding_item(conn, {
        "item_type": "mobile_capture",
        "title": "Mobile review capture",
        "summary": truncate(text, 700),
        "salience_labels": ["mobile_capture", "desktop_review", "not_memory_yet"],
        "source_refs": refs,
        "linked_packet_refs": refs,
        "review_status": "review_only",
        "payload_json": {
            "mobile_capture": True,
            "session_id": session_id,
            "save_request_id": save_request.get("id"),
            "desktop_review_only": True,
        },
    })
    return {
        "status": "mobile_review_capture_recorded",
        "session_id": session_id,
        "save_request": save_request,
        "chest_item": chest_item,
        "review_destination": "desktop_my_office",
        "guard_flags": _mobile_guard_flags_for_pairing(mobile_pairing_state()),
    }


def mobile_review_captures(conn: sqlite3.Connection, limit: int = 25) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT * FROM vessel_chest_holding_items
        WHERE item_type = 'mobile_capture'
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    items = [dict(row) for row in rows]
    return {
        "status": "mobile_review_captures_listed",
        "items": items,
        "capture_only": True,
        "review_destination": "desktop_my_office",
        "guard_flags": _mobile_guard_flags_for_pairing(mobile_pairing_state()),
    }


def mobile_blocked_action(action: str) -> dict[str, Any]:
    return {
        "status": "mobile_action_blocked",
        "action": action,
        "reason": "Mobile v1 is chat and review capture only. Open the desktop Selene console for cocoon, review, build, diagnostic, release, memory, transfer, or activation work.",
        "guard_flags": _mobile_guard_flags_for_pairing(mobile_pairing_state()),
    }


def _local_ipv4_addresses() -> list[str]:
    addresses: set[str] = set()
    try:
        hostname = socket.gethostname()
        for item in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = str(item[4][0])
            if ip and not ip.startswith("127."):
                addresses.add(ip)
    except OSError:
        pass
    return sorted(addresses)


def _ensure_mobile_selene_session(conn: sqlite3.Connection, session_id: int | None, text: str) -> int:
    if session_id:
        row = conn.execute("SELECT id FROM selene_chat_sessions WHERE id = ?", (session_id,)).fetchone()
        if row:
            return int(row["id"])
    cur = conn.execute(
        "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES(?, 'selene_chat_active_supervised', 'selene_supervised_speech')",
        (truncate(text, 64) or "Mobile capture",),
    )
    return int(cur.lastrowid)
