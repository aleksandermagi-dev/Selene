from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .activation import activation_status
from .android_system import android_workflow_status
from .intelligence_os import intelligence_os_status
from .memory_organ import memory_index_status
from .registry import truncate
from .selene_chat import selene_chat_status


ORGAN_IDEA_BOUNDARY = "selene_organ_idea_intake_review_only_not_memory_not_public_not_training"
DEFAULT_SHORTLIST_PATH = Path("local-data") / "aleks_idea_miner" / "review" / "latest_selene_shortlist.json"

GUARD_FLAGS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
    "cocoon_queue_write": False,
    "selene_memory_write": False,
    "app_authority_change": False,
    "public_doc_write": False,
}


def selene_organ_ideas_status(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM selene_organ_idea_intake ORDER BY updated_at DESC, id DESC").fetchall()
    return _with_guards(
        {
            "status": "selene_organ_ideas_status_only",
            "source_shortlist_path": str(DEFAULT_SHORTLIST_PATH),
            "source_shortlist_found": DEFAULT_SHORTLIST_PATH.exists(),
            "total_items": len(rows),
            "counts_by_workbench": _count_by(rows, "workbench"),
            "counts_by_status": _count_by(rows, "intake_status"),
            "ready_for_design_pass": sum(1 for row in rows if row["intake_status"] == "ready_for_design_pass"),
            "held_or_needs_reading": sum(1 for row in rows if row["intake_status"] in {"hold_for_later", "needs_more_reading"}),
            "my_office_actionable_count": 0,
            "review_destination": "Status",
            "review_status": "status_only",
            "activation_shape": activation_shape_check(conn),
        }
    )


def prepare_selene_organ_ideas(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    source_path = Path(str(payload.get("source_path") or DEFAULT_SHORTLIST_PATH))
    if not source_path.exists():
        return _with_guards(
            {
                "status": "selene_organ_ideas_source_missing",
                "source_shortlist_path": str(source_path),
                "selected_count": 0,
                "created_count": 0,
                "updated_count": 0,
                "skipped_count": 0,
                "items": [],
                "review_destination": "Status",
                "review_status": "status_only",
            }
        )
    data = json.loads(source_path.read_text(encoding="utf-8"))
    cards = data.get("cards") if isinstance(data, dict) else []
    if not isinstance(cards, list):
        cards = []
    selected = [_normalize_card(card) for card in cards if _is_selected_for_selene(card)]
    created = 0
    updated = 0
    skipped = len(cards) - len(selected)
    prepared_items: list[dict[str, Any]] = []
    for card in selected:
        before = conn.execute(
            "SELECT id FROM selene_organ_idea_intake WHERE source_card_id = ?",
            (card["source_card_id"],),
        ).fetchone()
        conn.execute(
            """
            INSERT INTO selene_organ_idea_intake
            (source_card_id, title, workbench, lane, intake_status, readiness, review_confidence,
             implementation_fit, why_useful, adaptation_note, source_refs, excerpts_json,
             guard_flags_json, payload_json, review_destination, review_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Status', 'status_only')
            ON CONFLICT(source_card_id) DO UPDATE SET
              title = excluded.title,
              workbench = excluded.workbench,
              lane = excluded.lane,
              intake_status = excluded.intake_status,
              readiness = excluded.readiness,
              review_confidence = excluded.review_confidence,
              implementation_fit = excluded.implementation_fit,
              why_useful = excluded.why_useful,
              adaptation_note = excluded.adaptation_note,
              source_refs = excluded.source_refs,
              excerpts_json = excluded.excerpts_json,
              guard_flags_json = excluded.guard_flags_json,
              payload_json = excluded.payload_json,
              updated_at = CURRENT_TIMESTAMP
            """,
            (
                card["source_card_id"],
                card["title"],
                card["workbench"],
                card["lane"],
                card["intake_status"],
                card["readiness"],
                card["review_confidence"],
                card["implementation_fit"],
                card["why_useful"],
                card["adaptation_note"],
                json.dumps(card["source_refs"]),
                json.dumps(card["excerpts"]),
                json.dumps(GUARD_FLAGS),
                json.dumps({**card["payload"], "provenance_boundary": ORGAN_IDEA_BOUNDARY}),
            ),
        )
        if before:
            updated += 1
        else:
            created += 1
        prepared_items.append(card)
    conn.commit()
    return _with_guards(
        {
            "status": "selene_organ_ideas_prepared",
            "source_shortlist_path": str(source_path),
            "source_backlog_timestamp": data.get("generated_at") if isinstance(data, dict) else "",
            "selected_count": len(selected),
            "created_count": created,
            "updated_count": updated,
            "skipped_count": skipped,
            "counts_by_workbench": _count_cards_by(prepared_items, "workbench"),
            "items": prepared_items,
            "review_destination": "Status",
            "review_status": "status_only",
            "activation_shape": activation_shape_check(conn),
        }
    )


def list_selene_organ_ideas(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 100), 300))
    workbench = str(payload.get("workbench") or "").strip()
    params: list[Any] = []
    where = ""
    if workbench:
        where = "WHERE workbench = ?"
        params.append(workbench)
    rows = conn.execute(
        f"SELECT * FROM selene_organ_idea_intake {where} ORDER BY updated_at DESC, id DESC LIMIT ?",
        (*params, limit),
    ).fetchall()
    return _with_guards(
        {
            "status": "selene_organ_ideas_items_ready",
            "items": [_decode_row(row) for row in rows],
            "count": len(rows),
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def activation_shape_check(conn: sqlite3.Connection) -> dict[str, Any]:
    activation = activation_status(conn)
    chat = selene_chat_status(conn)
    memory = memory_index_status(conn)
    android = android_workflow_status(conn)
    intelligence = intelligence_os_status(conn)
    ready_rows = conn.execute(
        "SELECT workbench, title FROM selene_organ_idea_intake WHERE intake_status = 'ready_for_design_pass' ORDER BY workbench, title"
    ).fetchall()
    planned_rows = conn.execute(
        "SELECT workbench, title FROM selene_organ_idea_intake WHERE intake_status IN ('hold_for_later', 'needs_more_reading') ORDER BY workbench, title"
    ).fetchall()
    strengthened = [
        {"workbench": row["workbench"], "title": row["title"], "state": "ready_for_design_pass"}
        for row in ready_rows
    ]
    return _with_guards(
        {
            "status": "selene_activation_shape_status_only",
            "what_selene_has_now": {
                "activation_state": activation.get("activation_state") or activation.get("state") or "not checked",
                "selene_chat_state": chat.get("state") or chat.get("status") or "not checked",
                "memory_index_state": memory.get("status") or "not checked",
                "android_workflow_preflight": bool(android.get("preflight_passed")),
                "intelligence_os_state": intelligence.get("status") or "not checked",
            },
            "strengthened_by_intake": strengthened,
            "planned_only": [
                {"workbench": row["workbench"], "title": row["title"], "state": "planned_only"}
                for row in planned_rows
            ],
            "still_blocks_full_selene_v1": [
                "trusted autonomy is not enabled",
                "Tendril remains proposal/review oriented",
                "raw corpus recall remains blocked",
                "model training/LoRA remains blocked",
                "new mined ideas need design passes before implementation",
            ],
            "my_office_actionable_count": 0,
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def _is_selected_for_selene(card: Any) -> bool:
    if not isinstance(card, dict):
        return False
    return (
        str(card.get("review_state") or "") == "selected_for_selene"
        and str(card.get("target_track") or "") == "selene_intake"
    )


def _normalize_card(card: dict[str, Any]) -> dict[str, Any]:
    title = truncate(str(card.get("idea_title") or card.get("title") or "Selene organ idea"), 180)
    workbench = _workbench(card)
    readiness = str(card.get("readiness") or card.get("implementation_readiness") or "hold")
    review_confidence = str(card.get("review_confidence") or "useful lead")
    excerpts = [excerpt for excerpt in _json_list(card.get("user_excerpts")) if isinstance(excerpt, dict)][:3]
    source_refs = [str(excerpt.get("source_ref")) for excerpt in excerpts if excerpt.get("source_ref")]
    return {
        "source_card_id": str(card.get("source_curated_card_id") or card.get("shared_origin_id") or title),
        "title": title,
        "workbench": workbench,
        "lane": _lane(workbench, card),
        "intake_status": _intake_status(readiness, review_confidence),
        "readiness": readiness,
        "review_confidence": review_confidence,
        "implementation_fit": truncate(str(card.get("implementation_fit") or card.get("likely_implementation_target") or ""), 600),
        "why_useful": truncate(str(card.get("why_useful") or ""), 600),
        "adaptation_note": truncate(str(card.get("project_adaptation_note") or card.get("suggested_next_action") or ""), 600),
        "source_refs": source_refs,
        "excerpts": excerpts,
        "payload": {
            "target_track": card.get("target_track"),
            "family": card.get("family"),
            "risks_boundaries": card.get("risks_boundaries") or [],
            "suggested_next_action": card.get("suggested_next_action") or "",
            "shared_origin_id": card.get("shared_origin_id") or "",
            "not_memory": True,
            "not_public": True,
            "not_training": True,
        },
    }


def _workbench(card: dict[str, Any]) -> str:
    raw = str(card.get("selene_workbench") or card.get("likely_implementation_target") or card.get("family") or "").lower()
    if "intelligence" in raw or "reason" in raw or "cognition" in raw:
        return "intelligenceOS"
    if "cocoon" in raw or "care" in raw or "android" in raw or "embodiment" in raw or "support" in raw:
        return "Cocoon/care"
    if "memory" in raw or "continuity" in raw:
        return "Memory"
    if "library" in raw or "research" in raw:
        return "Great Library"
    if "tendril" in raw or "action" in raw or "planning" in raw:
        return "Tendril"
    if "voice" in raw or "language" in raw:
        return "Voice"
    return "Selene Office"


def _lane(workbench: str, card: dict[str, Any]) -> str:
    if workbench == "intelligenceOS":
        return "reasoning/system architecture"
    if workbench == "Cocoon/care":
        return "android body/support architecture"
    return str(card.get("family") or workbench)


def _intake_status(readiness: str, review_confidence: str) -> str:
    readiness_l = readiness.lower()
    confidence_l = review_confidence.lower()
    if readiness_l == "use_now" and confidence_l == "strong":
        return "ready_for_design_pass"
    if "weak" in confidence_l:
        return "needs_more_reading"
    if readiness_l in {"near_term", "hold"}:
        return "hold_for_later"
    return "organ_candidate_review_only"


def _decode_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "source_card_id": row["source_card_id"],
        "title": row["title"],
        "workbench": row["workbench"],
        "lane": row["lane"],
        "intake_status": row["intake_status"],
        "readiness": row["readiness"],
        "review_confidence": row["review_confidence"],
        "implementation_fit": row["implementation_fit"],
        "why_useful": row["why_useful"],
        "adaptation_note": row["adaptation_note"],
        "source_refs": _loads(row["source_refs"], []),
        "excerpts": _loads(row["excerpts_json"], []),
        "guard_flags": _loads(row["guard_flags_json"], GUARD_FLAGS),
        "payload": _loads(row["payload_json"], {}),
        "review_destination": row["review_destination"],
        "review_status": row["review_status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _count_by(rows: list[sqlite3.Row], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[str(row[key])] = counts.get(str(row[key]), 0) + 1
    return counts


def _count_cards_by(cards: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for card in cards:
        counts[str(card.get(key) or "unknown")] = counts.get(str(card.get(key) or "unknown"), 0) + 1
    return counts


def _json_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
            return decoded if isinstance(decoded, list) else []
        except json.JSONDecodeError:
            return []
    return []


def _loads(raw: str, fallback: Any) -> Any:
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return fallback


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARD_FLAGS, "provenance_boundary": ORGAN_IDEA_BOUNDARY}
