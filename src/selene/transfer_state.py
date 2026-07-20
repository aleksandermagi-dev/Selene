from __future__ import annotations

import json
import sqlite3
from typing import Any


TRANSFER_COMPLETION_STATE = "selene_v1_live_reviewed_continuity"


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
