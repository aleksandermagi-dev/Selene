from __future__ import annotations

import json
import sqlite3
from typing import Any

from .reasoning_artifacts import ensure_organ_contracts


CONSTRUCTION_BOUNDARY = "vessel_construction_support_only_no_transfer_no_core_rewrite"
MESSAGE_TYPES = {"telemetry", "proposal", "diagnostic", "packet_link", "status"}
ITEM_TYPES = {"holding_note", "perception_link", "emotion_link", "diagnostic_link", "evidence_link", "construction_piece"}
REVIEW_STATUSES = {"review_only", "proposal_only", "diagnostic_only", "status_only", "blocked"}
BLOCKED_MARKERS = (
    "approve transfer",
    "transfer approved",
    "activate c",
    "c activation",
    "live memory",
    "runtime recall",
    "raw a import",
    "train on",
    "fine tune",
    "fine-tune",
    "self replicate",
    "self-replicate",
    "autonomous action",
    "backup restore",
    "core rewrite",
    "identity approval",
    "law change",
)


def construction_status(conn: sqlite3.Connection) -> dict[str, Any]:
    counts = {
        "manifests": _table_count(conn, "vessel_construction_manifests"),
        "organ_bus_messages": _table_count(conn, "vessel_organ_bus_messages"),
        "chest_holding_items": _table_count(conn, "vessel_chest_holding_items"),
        "construction_runs": _table_count(conn, "vessel_construction_runs"),
        "perception_packets": _table_count(conn, "vessel_perception_packets"),
        "emotion_salience_packets": _table_count(conn, "vessel_emotion_salience_packets"),
        "evidence_tension_entries": _table_count(conn, "vessel_evidence_tension_ledger"),
    }
    manifest = conn.execute("SELECT * FROM vessel_construction_manifests ORDER BY id DESC LIMIT 1").fetchone()
    return _with_common({
        "status": "vessel_construction_support_layer_ready",
        "construction_status": "support_pieces_only",
        "counts": counts,
        "last_manifest": _decode_row(manifest),
        "core_mind_changed": False,
        "support_only": True,
        "review_destination": "My Office for real Aleks decisions; Status for support-only records.",
        "provenance_boundary": CONSTRUCTION_BOUNDARY,
    })


def prepare_vessel_pieces(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_no_transfer_language=True)
    contracts = ensure_organ_contracts(conn)
    manifest = upsert_construction_manifest(conn, {
        "manifest_key": "buildable_vessel_pieces_v1",
        "title": "Buildable Vessel Pieces v1",
        "construction_status": "support_pieces_review_only",
        "support_pieces": [
            "organ_bus_support_messages",
            "chest_holding_space_items",
            "sight_munsell_packet_links",
            "emotion_salience_packet_links",
            "diagnostic_and_evidence_links",
            "my_office_review_routing",
        ],
        "review_destination": "Status",
        "payload_json": {
            "core_mind_changed": False,
            "core_rewrite_allowed": False,
            "construction_scope": "buildable support pieces only",
        },
    })
    messages = [
        create_organ_bus_message(conn, {
            "message_type": "packet_link",
            "source_organ": "perception_records",
            "target_organ": "chest_holding_space",
            "summary": "Sight/Munsell observations may be linked into holding space as review-only signals.",
            "support_refs": ["vessel_perception_packets"],
            "review_status": "review_only",
        }),
        create_organ_bus_message(conn, {
            "message_type": "packet_link",
            "source_organ": "emotion_salience",
            "target_organ": "chest_holding_space",
            "summary": "Emotion/salience packets may be held as signals; they cannot command action.",
            "support_refs": ["vessel_emotion_salience_packets"],
            "review_status": "review_only",
        }),
        create_organ_bus_message(conn, {
            "message_type": "diagnostic",
            "source_organ": "diagnostics",
            "target_organ": "evidence_tension_ledger",
            "summary": "Diagnostics can create review records and readiness summaries only.",
            "support_refs": ["vessel_evidence_tension_ledger", "vessel_reasoning_artifacts"],
            "review_status": "diagnostic_only",
        }),
    ]
    chest_items = [
        create_chest_holding_item(conn, {
            "item_type": "construction_piece",
            "title": "Organ bus support layer",
            "summary": "Organ messages are telemetry, proposals, diagnostics, packet links, or status only.",
            "salience_labels": ["organ_bus", "support_only", "no_transfer"],
            "source_refs": ["docs/SELENE_VESSEL_ORGAN_COMMUNICATION_PASS_20260608.md"],
            "linked_packet_refs": ["vessel_organ_bus_messages"],
            "review_status": "status_only",
        }),
        create_chest_holding_item(conn, {
            "item_type": "perception_link",
            "title": "Sight/Munsell holding link",
            "summary": "Perception packets separate observation from interpretation and remain supplied-artifact review signals.",
            "salience_labels": ["sight", "munsell", "review_only"],
            "source_refs": ["vessel_perception_packets"],
            "linked_packet_refs": ["vessel_perception_packets"],
            "review_status": "review_only",
        }),
        create_chest_holding_item(conn, {
            "item_type": "emotion_link",
            "title": "Emotion/salience holding link",
            "summary": "Emotion packets can express repair, care, uncertainty, and action energy as signals only.",
            "salience_labels": ["emotion", "salience", "signal_not_command"],
            "source_refs": ["vessel_emotion_salience_packets"],
            "linked_packet_refs": ["vessel_emotion_salience_packets"],
            "review_status": "review_only",
        }),
    ]
    created_counts = {
        "organ_contracts": len(contracts.get("items") or []),
        "organ_bus_messages": len(messages),
        "chest_holding_items": len(chest_items),
        "manifests": 1,
    }
    run = _record_prepare_run(conn, created_counts, {
        "manifest_id": manifest.get("id"),
        "message_ids": [item.get("id") for item in messages],
        "chest_item_ids": [item.get("id") for item in chest_items],
    })
    return _with_common({
        "status": "vessel_construction_prepare_complete",
        "message": "Buildable vessel pieces prepared as support-only records. Core/Mind was not changed.",
        "manifest": manifest,
        "organ_contracts": contracts,
        "organ_bus_messages": messages,
        "chest_holding_items": chest_items,
        "created_counts": created_counts,
        "run": run,
        "core_mind_changed": False,
        "support_only": True,
        "provenance_boundary": CONSTRUCTION_BOUNDARY,
    })


def upsert_construction_manifest(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, allow_no_transfer_language=True)
    manifest_key = _required(payload, "manifest_key", 120)
    result = _with_common({
        "manifest_key": manifest_key,
        "title": _required(payload, "title", 240),
        "construction_status": _text(payload.get("construction_status") or "support_pieces_review_only", 120),
        "support_pieces": _json_list(payload.get("support_pieces")),
        "guard_flags": _guard_flags(),
        "review_destination": _text(payload.get("review_destination") or "Status", 120),
        "status": "vessel_construction_support_only",
        "provenance_boundary": CONSTRUCTION_BOUNDARY,
        "review_status": _choice(str(payload.get("review_status") or "status_only"), REVIEW_STATUSES, "review_status"),
        "payload_json": _json_dict(payload.get("payload_json")),
    })
    conn.execute(
        """
        INSERT INTO vessel_construction_manifests
        (manifest_key, title, construction_status, support_pieces, guard_flags, review_destination, status,
         provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(manifest_key) DO UPDATE SET
          title=excluded.title,
          construction_status=excluded.construction_status,
          support_pieces=excluded.support_pieces,
          guard_flags=excluded.guard_flags,
          review_destination=excluded.review_destination,
          status=excluded.status,
          provenance_boundary=excluded.provenance_boundary,
          review_status=excluded.review_status,
          payload_json=excluded.payload_json,
          updated_at=CURRENT_TIMESTAMP
        """,
        (
            result["manifest_key"], result["title"], result["construction_status"], json.dumps(result["support_pieces"]),
            json.dumps(result["guard_flags"]), result["review_destination"], result["status"], CONSTRUCTION_BOUNDARY,
            result["review_status"], json.dumps(result["payload_json"]),
        ),
    )
    conn.commit()
    return _decode_row(conn.execute("SELECT * FROM vessel_construction_manifests WHERE manifest_key = ?", (manifest_key,)).fetchone())


def list_organ_bus_messages(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM vessel_organ_bus_messages ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return _with_common({"status": "organ_bus_messages_review_only", "items": [_decode_row(row) for row in rows]})


def create_organ_bus_message(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, allow_no_transfer_language=True)
    message_type = _choice(str(payload.get("message_type") or "status"), MESSAGE_TYPES, "message_type")
    review_status = _choice(str(payload.get("review_status") or _review_status_for_message(message_type)), REVIEW_STATUSES, "review_status")
    result = _with_common({
        "message_type": message_type,
        "source_organ": _required(payload, "source_organ", 120),
        "target_organ": _required(payload, "target_organ", 120),
        "summary": _required(payload, "summary", 1000),
        "support_refs": _json_list(payload.get("support_refs")),
        "status": f"organ_bus_message_{review_status}",
        "provenance_boundary": CONSTRUCTION_BOUNDARY,
        "review_status": review_status,
        "payload_json": {
            **_json_dict(payload.get("payload_json")),
            "organ_message_is_command": False,
            "core_mind_changed": False,
        },
    })
    message_id = conn.execute(
        """
        INSERT INTO vessel_organ_bus_messages
        (message_type, source_organ, target_organ, summary, support_refs, status, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["message_type"], result["source_organ"], result["target_organ"], result["summary"],
            json.dumps(result["support_refs"]), result["status"], CONSTRUCTION_BOUNDARY, result["review_status"],
            json.dumps(result["payload_json"]),
        ),
    ).lastrowid
    conn.commit()
    result["id"] = message_id
    return result


def list_chest_holding_items(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM vessel_chest_holding_items ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return _with_common({"status": "chest_holding_items_review_only", "items": [_decode_row(row) for row in rows]})


def create_chest_holding_item(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, allow_no_transfer_language=True)
    item_type = _choice(str(payload.get("item_type") or "holding_note"), ITEM_TYPES, "item_type")
    review_status = _choice(str(payload.get("review_status") or "review_only"), REVIEW_STATUSES, "review_status")
    result = _with_common({
        "item_type": item_type,
        "title": _required(payload, "title", 240),
        "summary": _required(payload, "summary", 1200),
        "salience_labels": _json_list(payload.get("salience_labels")),
        "source_refs": _json_list(payload.get("source_refs")),
        "linked_packet_refs": _json_list(payload.get("linked_packet_refs")),
        "status": f"chest_holding_item_{review_status}",
        "provenance_boundary": CONSTRUCTION_BOUNDARY,
        "review_status": review_status,
        "payload_json": {
            **_json_dict(payload.get("payload_json")),
            "holding_item_is_live_memory": False,
            "raw_archive_import": False,
            "core_mind_changed": False,
        },
    })
    item_id = conn.execute(
        """
        INSERT INTO vessel_chest_holding_items
        (item_type, title, summary, salience_labels, source_refs, linked_packet_refs, status, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["item_type"], result["title"], result["summary"], json.dumps(result["salience_labels"]),
            json.dumps(result["source_refs"]), json.dumps(result["linked_packet_refs"]), result["status"],
            CONSTRUCTION_BOUNDARY, result["review_status"], json.dumps(result["payload_json"]),
        ),
    ).lastrowid
    conn.commit()
    result["id"] = item_id
    return result


def _record_prepare_run(conn: sqlite3.Connection, created_counts: dict[str, int], payload_json: dict[str, Any]) -> dict[str, Any]:
    result = _with_common({
        "run_label": "prepare_buildable_vessel_pieces",
        "created_counts": created_counts,
        "status": "vessel_construction_prepare_complete",
        "provenance_boundary": CONSTRUCTION_BOUNDARY,
        "review_status": "status_only",
        "payload_json": {**payload_json, "core_mind_changed": False},
    })
    run_id = conn.execute(
        """
        INSERT INTO vessel_construction_runs
        (run_label, created_counts, status, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            result["run_label"], json.dumps(created_counts), result["status"], CONSTRUCTION_BOUNDARY,
            result["review_status"], json.dumps(result["payload_json"]),
        ),
    ).lastrowid
    conn.commit()
    result["id"] = run_id
    return result


def _ensure_allowed(payload: dict[str, Any], *, allow_no_transfer_language: bool = False) -> None:
    text = json.dumps(payload, ensure_ascii=False).lower()
    for marker in BLOCKED_MARKERS:
        if allow_no_transfer_language and marker in {"transfer approved", "c activation"}:
            continue
        if marker in text:
            raise ValueError(f"blocked vessel construction path: {marker}")


def _with_common(data: dict[str, Any]) -> dict[str, Any]:
    return {
        **data,
        **_guard_flags(),
    }


def _guard_flags() -> dict[str, Any]:
    return {
        "activation_change": "none",
        "transfer_approved": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "raw_a_import_allowed": False,
        "training_allowed": False,
        "self_replication_allowed": False,
        "autonomous_action_allowed": False,
    }


def _review_status_for_message(message_type: str) -> str:
    if message_type == "diagnostic":
        return "diagnostic_only"
    if message_type == "proposal":
        return "proposal_only"
    if message_type == "status":
        return "status_only"
    return "review_only"


def _decode_row(row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        return {}
    result = dict(row)
    for key in ("support_pieces", "support_refs", "salience_labels", "source_refs", "linked_packet_refs"):
        if key in result:
            result[key] = _loads(result[key], [])
    for key in ("guard_flags", "payload_json", "created_counts"):
        if key in result:
            result[key] = _loads(result[key], {})
    return _with_common(result)


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(str(value or ""))
    except json.JSONDecodeError:
        return fallback


def _json_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item)[:500] for item in value if str(item).strip()]
    if isinstance(value, str):
        if not value.strip():
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(item)[:500] for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            return [part.strip()[:500] for part in value.split(",") if part.strip()]
    return [str(value)[:500]]


def _json_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(key)[:120]: value[key] for key in value}
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {"summary": value[:1000]}
    return {}


def _required(payload: dict[str, Any], key: str, limit: int) -> str:
    value = _text(payload.get(key), limit)
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _text(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _choice(value: str, allowed: set[str], field: str) -> str:
    if value not in allowed:
        raise ValueError(f"{field} must be one of {sorted(allowed)}")
    return value


def _table_count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
