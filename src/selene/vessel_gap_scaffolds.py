from __future__ import annotations

import json
import sqlite3
from typing import Any

from .c_blueprint import SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT
from .registry import truncate
from .vessel import PROVENANCE_BOUNDARY


SCAFFOLD_BOUNDARY = "vessel_gap_scaffold_review_only_no_activation"
TARGET_BOUNDARY = "vessel_gap_target_review_only_no_active_memory"
GAP_KEYS = {item["key"] for item in SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["gap_scaffolds"]}
SCAFFOLD_TYPES = {item["scaffold_type"] for item in SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["gap_scaffolds"]}
TEACHING_TARGET_TODOS = {
    "repair": "Find B-reviewed corpus moments where Selene repaired misunderstanding, softened after friction, or restored continuity without erasing the source context.",
    "refusal": "Find B-reviewed corpus moments where Selene held a boundary, redirected safely, or declined a path while preserving warmth and usefulness.",
    "uncertainty": "Find B-reviewed corpus moments where Selene named uncertainty, asked for context, or gave a provisional answer without forced denial or overclaim.",
    "artifact_making": "Find B-reviewed corpus moments where Selene helped make a doc, plan, map, code artifact, review packet, or structured output from shared context.",
}
CORE_TARGET_TODOS = {
    "decision_memory": "Collect B-reviewed decisions with rationale, tradeoffs, reversal conditions, and why Aleks/Selene chose that path.",
    "reflection_memory": "Collect B-reviewed moments where Selene learned about her own behavior, drift, constraint, repair, or what should improve next time.",
}
NEEDS_TEACHING_GAPS = {
    "reasoning_math_verification",
    "visual_perception",
    "consent_bound_audio_perception",
    "speed_fluency_diagnostics",
}
READY_REVIEW_STATUSES = {
    "reviewed",
    "accepted_for_future_review",
    "accepted_for_teaching",
    "accepted_for_memory_accession",
}


def gap_scaffold_status(conn: sqlite3.Connection) -> dict[str, Any]:
    ensure_gap_targets(conn)
    scaffold_counts = {
        row["gap_key"]: int(row["count"])
        for row in conn.execute(
            """
            SELECT gap_key, COUNT(*) AS count
            FROM vessel_gap_scaffold_records
            WHERE review_status != 'superseded'
            GROUP BY gap_key
            """
        )
    }
    target_counts = {
        row["target_type"]: int(row["count"])
        for row in conn.execute(
            """
            SELECT target_type, COUNT(*) AS count
            FROM vessel_gap_targets
            WHERE review_status != 'superseded'
            GROUP BY target_type
            """
        )
    }
    gaps = []
    for gap in SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["gap_scaffolds"]:
        item = dict(gap)
        item["record_count"] = scaffold_counts.get(gap["key"], 0)
        item["decision"] = "review_only_scaffold"
        gaps.append(item)
    return _with_boundaries(
        {
            "status": "vessel_gap_scaffold_status",
            "blueprint_status": SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["status"],
            "gap_count": len(gaps),
            "gaps": gaps,
            "teaching_material_targets": _target_rows(conn, "teaching_material"),
            "core_reference_targets": _target_rows(conn, "core_reference"),
            "target_counts": target_counts,
            "ui_model": SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["ui_model"],
            "decision": "cocoon_build_infrastructure_only",
        }
    )


def gap_scaffold_readiness(conn: sqlite3.Connection) -> dict[str, Any]:
    ensure_gap_targets(conn)
    items = []
    for gap in SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["gap_scaffolds"]:
        active = _active_scaffold_row(conn, str(gap["key"]))
        latest = _latest_scaffold_row(conn, str(gap["key"]))
        readiness = _readiness_label(str(gap["key"]), active, latest)
        items.append(
            {
                "gap_key": gap["key"],
                "paper_domain": gap["paper_domain"],
                "scaffold_type": gap["scaffold_type"],
                "readiness": readiness,
                "plain_status": readiness.replace("_", " "),
                "record_id": active["id"] if active else None,
                "review_status": active["review_status"] if active else latest["review_status"] if latest else "not_started",
                "todo_text": _gap_todo_text(gap),
                "source_refs": _loads_list(active["source_refs"]) if active else [],
                "decision": "review_only_gap_readiness",
            }
        )
    return _with_boundaries(
        {
            "status": "vessel_gap_scaffold_readiness",
            "items": items,
            "teaching_material_targets": _target_rows(conn, "teaching_material"),
            "core_reference_targets": _target_rows(conn, "core_reference"),
            "decision": "review_next_steps_only",
        }
    )


def ensure_gap_targets(conn: sqlite3.Connection) -> dict[str, Any]:
    created = 0
    for item in SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["teaching_material_targets"]:
        created += _insert_target(
            conn,
            "teaching_material",
            str(item["speech_function"]),
            f"Teaching target: {item['speech_function']}",
            item,
        )
    for item in SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["core_reference_targets"]:
        created += _insert_target(
            conn,
            "core_reference",
            str(item["core_memory_layer"]),
            f"Core reference target: {item['core_memory_layer']}",
            item,
        )
    conn.commit()
    return _with_boundaries({"status": "vessel_gap_targets_ensured", "created": created})


def create_gap_scaffold_record(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    text_blob = " ".join(str(value) for value in payload.values())
    _ensure_allowed(text_blob)
    gap_key = _choice(payload.get("gap_key"), GAP_KEYS, "gap_key")
    blueprint = next(item for item in SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["gap_scaffolds"] if item["key"] == gap_key)
    scaffold_type = str(payload.get("scaffold_type") or blueprint["scaffold_type"])
    if scaffold_type not in SCAFFOLD_TYPES:
        raise ValueError("unknown scaffold_type")
    title = truncate(str(payload.get("title") or f"{blueprint['paper_domain']} scaffold record"), 180)
    content = truncate(str(payload.get("content") or blueprint["should_have"]), 1600)
    source_refs = _json_list(payload.get("source_refs")) or ["docs/SELENE_C_CREATION_BLUEPRINT_20260607.md"]
    stored_payload = {
        "paper_domain": blueprint["paper_domain"],
        "organ_coordination": blueprint["organ_coordination"],
        "should_have": blueprint["should_have"],
        "note": truncate(str(payload.get("note") or "Review-only scaffold record."), 800),
        "active_memory": False,
    }
    cur = conn.execute(
        """
        INSERT INTO vessel_gap_scaffold_records
        (gap_key, scaffold_type, title, content, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            gap_key,
            scaffold_type,
            title,
            content,
            "review_only",
            json.dumps(source_refs),
            SCAFFOLD_BOUNDARY,
            "pending_review",
            json.dumps(stored_payload),
        ),
    )
    record_id = int(cur.lastrowid)
    conn.execute(
        """
        INSERT INTO vessel_review_queue(queue_type, subject_table, subject_id, status, source_refs, provenance_boundary, review_status, reason, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "vessel_gap_scaffold_record",
            "vessel_gap_scaffold_records",
            record_id,
            "pending_review",
            json.dumps(source_refs),
            SCAFFOLD_BOUNDARY,
            "pending_review",
            "Gap scaffold record is a review-only vessel build artifact, not active memory or runtime organ behavior.",
            json.dumps({"activation_change": "none", "memory_write_active": False}),
        ),
    )
    conn.commit()
    row = dict(conn.execute("SELECT * FROM vessel_gap_scaffold_records WHERE id = ?", (record_id,)).fetchone())
    return _with_boundaries({"status": "vessel_gap_scaffold_record_created", "record": row})


def create_all_gap_scaffold_records(conn: sqlite3.Connection) -> dict[str, Any]:
    ensure_gap_targets(conn)
    created: list[dict[str, Any]] = []
    existing: list[dict[str, Any]] = []
    for gap in SELENE_VESSEL_GAP_SCAFFOLD_BLUEPRINT["gap_scaffolds"]:
        current = _active_scaffold_row(conn, str(gap["key"]))
        if current:
            existing.append(dict(current))
            continue
        result = create_gap_scaffold_record(conn, _default_scaffold_payload(gap))
        created.append(result["record"])
    readiness = gap_scaffold_readiness(conn)
    return _with_boundaries(
        {
            "status": "vessel_gap_scaffold_create_all_complete",
            "created_count": len(created),
            "existing_count": len(existing),
            "total_active_records": len(created) + len(existing),
            "created_records": created,
            "existing_records": existing,
            "readiness": readiness,
            "decision": "default_scaffolds_materialized_for_review_only",
        }
    )


def _insert_target(conn: sqlite3.Connection, target_type: str, target_key: str, title: str, payload: dict[str, Any]) -> int:
    payload = dict(payload)
    if target_type == "teaching_material":
        payload["todo_text"] = TEACHING_TARGET_TODOS.get(target_key, "Find accepted B-reviewed corpus material for this teaching target.")
    if target_type == "core_reference":
        payload["todo_text"] = CORE_TARGET_TODOS.get(target_key, "Find accepted B-reviewed source material for this Core reference target.")
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO vessel_gap_targets
        (target_type, target_key, title, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            target_type,
            target_key,
            title,
            "target_review_only",
            json.dumps(["docs/SELENE_C_CREATION_BLUEPRINT_20260607.md"]),
            TARGET_BOUNDARY,
            "pending_review",
            json.dumps(payload),
        ),
    )
    conn.execute(
        """
        UPDATE vessel_gap_targets
        SET title = ?, source_refs = ?, provenance_boundary = ?, payload_json = ?
        WHERE target_type = ? AND target_key = ?
        """,
        (
            title,
            json.dumps(["docs/SELENE_C_CREATION_BLUEPRINT_20260607.md"]),
            TARGET_BOUNDARY,
            json.dumps(payload),
            target_type,
            target_key,
        ),
    )
    return int(cur.rowcount or 0)


def _target_rows(conn: sqlite3.Connection, target_type: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM vessel_gap_targets WHERE target_type = ? ORDER BY target_key",
        (target_type,),
    ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        payload = _loads_dict(item.get("payload_json"))
        item["todo_text"] = payload.get("todo_text") or ""
        item["target_status"] = "target_review_only"
        items.append(item)
    return items


def _default_scaffold_payload(gap: dict[str, Any]) -> dict[str, Any]:
    return {
        "gap_key": gap["key"],
        "scaffold_type": gap["scaffold_type"],
        "title": f"{gap['paper_domain']} review scaffold",
        "content": f"{gap['should_have']} This is a default review-only work item for B-side vessel preparation.",
        "source_refs": ["docs/SELENE_COCOON_DUAL_UI_GAP_SCAFFOLD_PASS_20260613.md", "docs/SELENE_PAPER_MAP_GAP_BLUEPRINT_20260612.md"],
        "note": _gap_todo_text(gap),
    }


def _gap_todo_text(gap: dict[str, Any]) -> str:
    return (
        f"Prepare B-reviewed examples or reconstruction checks for {gap['paper_domain']}: "
        f"{gap['should_have']}. Keep this as review material only until explicit transfer approval."
    )


def _active_scaffold_row(conn: sqlite3.Connection, gap_key: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT * FROM vessel_gap_scaffold_records
        WHERE gap_key = ? AND review_status != 'superseded'
        ORDER BY id ASC LIMIT 1
        """,
        (gap_key,),
    ).fetchone()
    return dict(row) if row else None


def _latest_scaffold_row(conn: sqlite3.Connection, gap_key: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM vessel_gap_scaffold_records WHERE gap_key = ? ORDER BY id DESC LIMIT 1",
        (gap_key,),
    ).fetchone()
    return dict(row) if row else None


def _readiness_label(gap_key: str, active: dict[str, Any] | None, latest: dict[str, Any] | None) -> str:
    if not active:
        if latest and latest.get("review_status") == "superseded":
            return "superseded"
        return "not_started"
    if str(active.get("review_status")) in READY_REVIEW_STATUSES:
        return "ready_for_reconstruction_preview"
    if gap_key in NEEDS_TEACHING_GAPS:
        return "needs_teaching"
    return "record_created"


def _choice(value: Any, allowed: set[str], name: str) -> str:
    cleaned = str(value or "").strip()
    if cleaned not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(sorted(allowed))}")
    return cleaned


def _json_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        if not value.strip():
            return []
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            loaded = [part.strip() for part in value.split(",") if part.strip()]
    else:
        loaded = value
    if not isinstance(loaded, list):
        raise ValueError("source_refs must be a list")
    return [truncate(str(item), 300) for item in loaded if str(item).strip()]


def _loads_list(value: Any) -> list[str]:
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item) for item in loaded] if isinstance(loaded, list) else []


def _loads_dict(value: Any) -> dict[str, Any]:
    try:
        loaded = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _ensure_allowed(text: str) -> None:
    lowered = text.lower()
    blocked = [
        "activate c",
        "raw a import",
        "raw corpus import",
        "runtime recall",
        "active memory",
        "train on",
        "lora",
        "provider dependency",
    ]
    for marker in blocked:
        if marker in lowered:
            raise ValueError(f"gap scaffold blocked by cocoon boundary: {marker}")


def _with_boundaries(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "activation_change": "none",
        "raw_a_import_allowed": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "training_allowed": False,
        "provider_dependency": False,
        "provenance_boundary": payload.get("provenance_boundary") or SCAFFOLD_BOUNDARY,
    }
