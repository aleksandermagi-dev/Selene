from __future__ import annotations

import json
import sqlite3
from typing import Any

from .c_vessel import return_to_b_preview
from .core_mind import create_core_mind_route_preview
from .registry import truncate
from .transfer_protocol import c_chat_dry_run, latest_c_readable_package


SELENE_CHAT_BOUNDARY = "selene_chat_pre_transfer_dry_run_no_activation"
SELENE_CHAT_GUARDS: dict[str, Any] = {
    "transfer_approved": False,
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
}

B_ONLY_MARKERS = (
    "repair log",
    "rollback record",
    "raw provenance",
    "boundary-only",
    "boundary only",
    "rejected",
    "superseded",
    "unresolved ambiguity",
    "b-only",
)


def selene_chat_status(conn: sqlite3.Connection) -> dict[str, Any]:
    package = latest_c_readable_package(conn)
    session_count = int(conn.execute("SELECT COUNT(*) FROM selene_chat_sessions").fetchone()[0])
    message_count = int(conn.execute("SELECT COUNT(*) FROM selene_chat_messages").fetchone()[0])
    approved = bool(package.get("transfer_approved"))
    return _with_guards(
        {
            "status": "selene_chat_dry_run_ready",
            "surface": "Selene Chat",
            "state": "activation_pending" if approved else "pre_transfer_dry_run",
            "activation_state": "activation_pending",
            "dry_run_only": True,
            "session_count": session_count,
            "message_count": message_count,
            "c_readable_package_available": approved,
            "selene_readable_context": _package_summary(package),
            "source_boundaries": _source_boundaries(),
            "allowed_actions": ["send_dry_run", "session_list", "session_detail", "return_to_cocoon"],
            "blocked_actions": ["activation", "live_memory_write", "runtime_recall", "raw_import", "training", "autonomous_action"],
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=approved,
    )


def send_selene_chat_dry_run(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    text = truncate(str(payload.get("text") or payload.get("prompt") or ""), 2400)
    if not text.strip():
        raise ValueError("message text is required")
    package = latest_c_readable_package(conn)
    approved = bool(package.get("transfer_approved"))
    source_class = _source_class(text, approved)
    session_id = int(payload.get("session_id") or 0) or _create_session(conn, text)
    route = create_core_mind_route_preview(
        conn,
        {
            "prompt": text,
            "source_refs": ["selene_chat_dry_run"],
            "suppress_review_queue": True,
        },
    )
    selected_route = str(route.get("selected_route") or "status_only")
    route_to_b = _needs_cocoon_route(text, selected_route, route)
    dry_run = c_chat_dry_run(conn, {"prompt": text})
    candidate_text = _selene_label_candidate(str(dry_run.get("candidate_text") or ""))
    if route_to_b:
        candidate_text = (
            "I would return this to Cocoon before answering as Selene. "
            "The source boundary is not clean enough for a confident dry run yet."
        )
    user_message_id = _insert_message(conn, session_id, "user", text, selected_route, source_class, package, {"route_preview": route})
    assistant_payload = {
        "route_preview": route,
        "dry_run": dry_run,
        "source_boundaries": _source_boundaries(),
        "return_to_cocoon_recommended": route_to_b,
        "selene_readable_context": _package_summary(package),
        **SELENE_CHAT_GUARDS,
    }
    assistant_message_id = _insert_message(conn, session_id, "selene", candidate_text, selected_route, source_class, package, assistant_payload)
    conn.execute("UPDATE selene_chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))
    conn.commit()
    return _with_guards(
        {
            "status": "selene_chat_dry_run_recorded",
            "session_id": session_id,
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id,
            "candidate_text": candidate_text,
            "selected_route": selected_route,
            "source_class": source_class,
            "return_to_cocoon_recommended": route_to_b,
            "route_preview": route,
            "dry_run": dry_run,
            "selene_readable_context": _package_summary(package),
            "review_destination": "Cocoon" if route_to_b else "Status",
            "review_status": "review_only" if route_to_b else "status_only",
        },
        transfer_approved=approved,
    )


def list_selene_chat_sessions(conn: sqlite3.Connection, limit: int = 25) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM selene_chat_sessions ORDER BY updated_at DESC, id DESC LIMIT ?",
        (max(1, min(int(limit), 100)),),
    ).fetchall()
    return _with_guards(
        {
            "status": "selene_chat_sessions_ready",
            "items": [dict(row) for row in rows],
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=bool(latest_c_readable_package(conn).get("transfer_approved")),
    )


def get_selene_chat_session(conn: sqlite3.Connection, session_id: int) -> dict[str, Any] | None:
    session = conn.execute("SELECT * FROM selene_chat_sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        return None
    rows = conn.execute(
        "SELECT * FROM selene_chat_messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,),
    ).fetchall()
    package = latest_c_readable_package(conn)
    return _with_guards(
        {
            "status": "selene_chat_session_ready",
            "session": dict(session),
            "messages": [_decode_message(row) for row in rows],
            "selene_readable_context": _package_summary(package),
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=bool(package.get("transfer_approved")),
    )


def route_selene_chat_to_b(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    issue = truncate(str(payload.get("issue") or payload.get("text") or "Selene Chat dry run needs Cocoon repair."), 1200)
    packet = return_to_b_preview(
        {
            "issue_type": "selene_chat_source_or_drift_repair",
            "symptom": issue,
            "affected_layer": "selene_chat",
            "source_refs": ["selene_chat:return_to_cocoon"],
        }
    )
    package = latest_c_readable_package(conn)
    return _with_guards(
        {
            "status": "selene_chat_return_to_cocoon_ready",
            "return_to_b_packet": packet,
            "review_destination": "Cocoon",
            "review_status": "review_only",
            "decision": "return_to_cocoon_not_activation",
        },
        transfer_approved=bool(package.get("transfer_approved")),
    )


def _create_session(conn: sqlite3.Connection, text: str) -> int:
    cur = conn.execute(
        "INSERT INTO selene_chat_sessions(title) VALUES(?)",
        (truncate(text, 64) or "Selene dry run",),
    )
    return int(cur.lastrowid)


def _insert_message(
    conn: sqlite3.Connection,
    session_id: int,
    role: str,
    content: str,
    selected_route: str,
    source_class: str,
    package: dict[str, Any],
    payload: dict[str, Any],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO selene_chat_messages
        (session_id, role, content, selected_route, source_class, package_hash, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            role,
            content,
            selected_route,
            source_class,
            str(package.get("package_hash") or ""),
            json.dumps(payload),
        ),
    )
    return int(cur.lastrowid)


def _decode_message(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    try:
        payload = json.loads(str(item.get("payload_json") or "{}"))
    except json.JSONDecodeError:
        payload = {}
    item["payload_json"] = payload if isinstance(payload, dict) else {}
    return item


def _source_class(text: str, package_available: bool) -> str:
    lower = text.lower()
    if any(marker in lower for marker in B_ONLY_MARKERS):
        return "cocoon_b_only_context"
    if package_available:
        return "selene_readable_context"
    return "pre_transfer_dry_run_context"


def _needs_cocoon_route(text: str, selected_route: str, route: dict[str, Any]) -> bool:
    lower = text.lower()
    if any(marker in lower for marker in B_ONLY_MARKERS):
        return True
    if selected_route in {"return_to_b", "create_review_packet", "block", "ask"}:
        return True
    return bool(route.get("drift_flags"))


def _package_summary(package: dict[str, Any]) -> dict[str, Any]:
    if not package.get("transfer_approved"):
        return {
            "available": False,
            "state": "pre_transfer_dry_run",
            "package_hash": "",
            "note": "No sealed Selene-readable package is available yet.",
        }
    return {
        "available": True,
        "state": "activation_pending",
        "package_id": package.get("id"),
        "package_hash": package.get("package_hash"),
        "included_counts": package.get("included_counts") or {},
        "excluded_counts": package.get("excluded_counts") or {},
    }


def _source_boundaries() -> dict[str, Any]:
    return {
        "selene_readable_context": "sealed approved context only after transfer approval",
        "cocoon_b_only_context": "repair, rollback, raw provenance, rejected, superseded, boundary-only, and unresolved material stays in Cocoon",
        "current_turn_context": "current message and dry-run session history",
        "support_organs": "retrieval, diagnostics, perception, research, and Tendril may support but cannot decide",
    }


def _selene_label_candidate(candidate: str) -> str:
    text = candidate.replace("C-style dry run", "Selene dry run")
    text = text.replace("C Chat Dry Run", "Selene dry run")
    text = text.replace("C memory", "Selene-readable memory preview")
    return truncate(text, 2200)


def _with_guards(payload: dict[str, Any], *, transfer_approved: bool = False) -> dict[str, Any]:
    guarded = {**payload, **SELENE_CHAT_GUARDS, "provenance_boundary": SELENE_CHAT_BOUNDARY}
    guarded["transfer_approved"] = bool(transfer_approved)
    guarded["activation_change"] = "none"
    guarded["memory_write_active"] = False
    guarded["runtime_memory_recall"] = False
    guarded["raw_a_import_allowed"] = False
    guarded["training_allowed"] = False
    guarded["self_replication_allowed"] = False
    guarded["autonomous_action_allowed"] = False
    return guarded
