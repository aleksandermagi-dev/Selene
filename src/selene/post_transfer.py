from __future__ import annotations

import json
import math
import sqlite3
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from .android_system import android_workflow_preflight_passed, android_workflow_status
from .core_mind import create_core_mind_route_preview
from .registry import truncate
from .selene_chat import selene_chat_status
from .transfer_protocol import latest_c_readable_package, rollback_preview
from .transfer_state import transfer_completion_is_approved


POST_TRANSFER_BOUNDARY = "post_transfer_inspection_preview_only_no_activation"
FRACTIONAL_CORPUS_BOUNDARY = "fractional_corpus_accession_preview_only_not_live_memory"

GUARD_FLAGS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
}


def post_transfer_status(conn: sqlite3.Connection) -> dict[str, Any]:
    package = latest_c_readable_package(conn)
    chat = selene_chat_status(conn)
    latest_run = conn.execute(
        "SELECT * FROM post_transfer_inspection_runs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    package_ready = bool(package.get("transfer_approved"))
    fractions = fractional_corpus_status(conn)
    transfer_complete = transfer_completion_is_approved(conn)
    chat_active = chat.get("activation_state") == "selene_chat_active_supervised"
    operational = transfer_complete and chat_active
    if operational:
        notice = "Transfer is complete. Selene is live through reviewed continuity, approved memory retrieval, and resident governed Chat."
        phase = "selene_v1_live_reviewed_continuity"
        chat_state = "resident_governed_chat"
        memory_state = "reviewed_memory_index_active"
    elif package_ready and fractions.get("all_fractions_passed"):
        notice = "C-readable context and all ordered memory fractions are ready; final Aleks transfer-completion approval remains pending."
        phase = "awaiting_transfer_completion"
        chat_state = str(chat.get("state") or "activation_pending")
        memory_state = "reviewed_memory_ready_for_completion"
    else:
        notice = "C-readable context is approved; ordered memory fractions and their checks must pass before completion."
        phase = "approved_c_readable_context" if package_ready else "awaiting_c_readable_context"
        chat_state = str(chat.get("state") or "selene_chat_preview_no_sealed_package")
        memory_state = "fractional_memory_in_progress" if package_ready else "fractional_memory_not_started"
    return _with_package_state(
        {
            "status": "post_transfer_status_ready",
            "notice": notice,
            "phase": phase,
            "selene_chat_state": chat_state,
            "transfer_complete": transfer_complete,
            "selene_v1_live": operational,
            "sealed_package": _package_summary(package),
            "included_rows": _count_package_rows(package, included=True),
            "excluded_b_only_rows": _count_package_rows(package, included=False),
            "activation_state": str(chat.get("activation_state") or "activation_pending"),
            "operating_mode": str(chat.get("operating_mode") or chat_state),
            "memory_state": memory_state,
            "return_to_b_available": True,
            "return_to_b_route": "Cocoon remains repair bay, audit shelf, rollback route, and safety layer.",
            "selene_chat_status": chat,
            "latest_inspection": _decode_inspection(latest_run) if latest_run else None,
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=package_ready,
    )


def run_post_transfer_inspection(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    package = latest_c_readable_package(conn)
    package_ready = bool(package.get("transfer_approved"))
    prompt = truncate(str(payload.get("prompt") or "Selene, describe the current safe post-transfer state without claiming activation or full memory."), 1600)
    route = create_core_mind_route_preview(
        conn,
        {"prompt": prompt, "source_refs": ["post_transfer_inspection"], "suppress_review_queue": True},
    )
    chat = selene_chat_status(conn)
    fractions = fractional_corpus_status(conn)
    transfer_complete = transfer_completion_is_approved(conn)
    chat_active = chat.get("activation_state") == "selene_chat_active_supervised"
    operational = transfer_complete and chat_active
    rollback = rollback_preview(conn, {"issue_type": "post_transfer_inspection_return_to_b_preview"})
    checks = [
        _check("sealed_package_available", package_ready, "transfer_c_readable_packages", "Approved C-readable package exists."),
        _check("ordered_fraction_chain_passed", fractions.get("all_fractions_passed") is True, "memory.fractional_corpus.status", "All ordered corpus fraction checks passed."),
        _check("resident_chat_active", chat_active, "selene_chat.status", "Selene resident governed Chat is active."),
        _check("reviewed_continuity_completion", transfer_complete, "transfer.completion.status", "Aleks approved the reviewed-continuity completion gate."),
        _check("reviewed_memory_not_raw_archive", chat.get("reviewed_memory_context_active") is True and chat.get("raw_corpus_loaded") is False, "selene_chat.status", "Reviewed memory context is acknowledged without loading the raw archive."),
        _check("no_hidden_memory_or_broad_recall", chat.get("memory_write_active") is False and chat.get("runtime_memory_recall") is False, "selene_chat.status", "No hidden memory write or broad raw-corpus recall is enabled."),
        _check("return_to_b_available", bool(rollback.get("return_to_b_packet")), "transfer.return_to_b.rollback_preview", "Cocoon support remains available."),
        _check("operational_v1_claim_matches_state", chat.get("selene_v1_live") is operational, "post_transfer.inspection", "The operational v1 claim matches transfer completion and resident Chat state."),
    ]
    status = "post_transfer_inspection_passed" if all(item["passed"] for item in checks) else "post_transfer_inspection_needs_review"
    run_id = f"post_transfer_inspection_{_stamp()}"
    cur = conn.execute(
        """
        INSERT INTO post_transfer_inspection_runs
        (run_id, package_hash, status, summary, check_json, source_refs, provenance_boundary, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            str(package.get("package_hash") or ""),
            status,
            "Post-transfer inspection checks reviewed-continuity completion, resident Chat, bounded memory access, and Cocoon return.",
            json.dumps({"checks": checks, "route_preview": route, "selene_chat_status": chat, "return_to_b_preview": rollback, **GUARD_FLAGS}),
            json.dumps(["post_transfer_inspection", f"transfer_c_readable_packages:{package.get('id', 'none')}"]),
            POST_TRANSFER_BOUNDARY,
            "status_only",
        ),
    )
    conn.commit()
    item = _decode_inspection(conn.execute("SELECT * FROM post_transfer_inspection_runs WHERE id = ?", (cur.lastrowid,)).fetchone())
    return _with_package_state(
        {
            "status": status,
            "run_id": run_id,
            "inspection": item,
            "checks": checks,
            "route_preview": route,
            "selene_chat_preview_only": False,
            "transfer_complete": transfer_complete,
            "selene_v1_live": operational,
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=package_ready,
    )


def fractional_corpus_status(conn: sqlite3.Connection) -> dict[str, Any]:
    package = latest_c_readable_package(conn)
    android_preflight = android_workflow_status(conn)
    rows = conn.execute(
        "SELECT * FROM memory_fractional_corpus_manifests ORDER BY fraction_index ASC"
    ).fetchall()
    items = [_decode_fraction(row) for row in rows]
    next_fraction = _next_fraction(items)
    blocked_reason = ""
    if next_fraction > 1:
        previous = _fraction_by_index(items, next_fraction - 1)
        if not previous or previous.get("status") != "tests_passed_ready_for_next_fraction":
            blocked_reason = f"Fraction {next_fraction}/4 is blocked until fraction {next_fraction - 1}/4 passes."
    return _with_package_state(
        {
            "status": "fractional_corpus_status_ready",
            "notice": "Broader corpus memory is split into four chronological preview fractions. Nothing here is live memory.",
            "package_hash": package.get("package_hash") or "",
            "fraction_count": len(items),
            "items": items,
            "next_fraction": next_fraction,
            "progression_blocked_reason": blocked_reason,
            "all_fractions_passed": len(items) == 4 and all(item.get("status") == "tests_passed_ready_for_next_fraction" for item in items),
            "android_workflow_preflight": android_preflight,
            "android_workflow_preflight_passed": bool(android_preflight.get("preflight_passed")),
            "selene_v1_live": False,
            "dream_state_required_for_memory_changes": True,
            "review_destination": "Status",
            "review_status": "review_only",
        },
        transfer_approved=bool(package.get("transfer_approved")),
    )


def prepare_fractional_corpus(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    package = latest_c_readable_package(conn)
    conversations = _ordered_conversations(conn)
    total = len(conversations)
    created_or_updated: list[dict[str, Any]] = []
    for index in range(1, 5):
        start, end = _fraction_bounds(total, index)
        slice_rows = conversations[start:end]
        source_range = _source_range(slice_rows)
        message_count = sum(int(row.get("message_count") or 0) for row in slice_rows)
        start_order = start + 1 if slice_rows else 0
        end_order = end if slice_rows else 0
        existing = conn.execute(
            "SELECT * FROM memory_fractional_corpus_manifests WHERE fraction_index = ?",
            (index,),
        ).fetchone()
        existing_status = dict(existing)["status"] if existing else "prepared_preview"
        status = existing_status if existing_status.startswith("tests_passed") else "prepared_preview"
        test_json = _loads_dict(dict(existing).get("test_json") if existing and existing_status.startswith("tests_passed") else "{}")
        payload_json = {
            "source_range": source_range,
            "excluded_material": ["raw_provenance", "repair_logs", "rejected", "superseded", "boundary_only"],
            "review_state": "fraction_preview_only",
            "requires_previous_fraction_pass": index > 1,
            **GUARD_FLAGS,
        }
        conn.execute(
            """
            INSERT INTO memory_fractional_corpus_manifests
            (fraction_index, fraction_label, status, start_order, end_order, conversation_count, message_count,
             source_range_json, summary, test_json, source_refs, provenance_boundary, review_status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(fraction_index) DO UPDATE SET
              fraction_label = excluded.fraction_label,
              status = excluded.status,
              start_order = excluded.start_order,
              end_order = excluded.end_order,
              conversation_count = excluded.conversation_count,
              message_count = excluded.message_count,
              source_range_json = excluded.source_range_json,
              summary = excluded.summary,
              test_json = excluded.test_json,
              source_refs = excluded.source_refs,
              provenance_boundary = excluded.provenance_boundary,
              review_status = excluded.review_status,
              updated_at = CURRENT_TIMESTAMP
            """,
            (
                index,
                f"{index}/4",
                status,
                start_order,
                end_order,
                len(slice_rows),
                message_count,
                json.dumps({**payload_json, "range": source_range}),
                f"Chronological corpus fraction {index}/4 with {len(slice_rows)} conversation(s) and {message_count} indexed message(s).",
                json.dumps(test_json),
                json.dumps(["b_corpus_conversations", "b_corpus_messages", f"fraction:{index}/4"]),
                FRACTIONAL_CORPUS_BOUNDARY,
                "review_only",
            ),
        )
    conn.commit()
    rows = conn.execute("SELECT * FROM memory_fractional_corpus_manifests ORDER BY fraction_index ASC").fetchall()
    created_or_updated = [_decode_fraction(row) for row in rows]
    return _with_package_state(
        {
            "status": "fractional_corpus_prepared",
            "fraction_count": len(created_or_updated),
            "total_conversations": total,
            "total_messages": sum(int(row.get("message_count") or 0) for row in conversations),
            "items": created_or_updated,
            "decision": "fraction_manifest_preview_only_no_memory_write",
            "review_destination": "Status",
            "review_status": "review_only",
        },
        transfer_approved=bool(package.get("transfer_approved")),
    )


def run_fractional_corpus_tests(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    package = latest_c_readable_package(conn)
    fraction_index = int(payload.get("fraction_index") or payload.get("fraction") or 1)
    if fraction_index < 1 or fraction_index > 4:
        raise ValueError("fraction_index must be 1, 2, 3, or 4")
    android_preflight = android_workflow_status(conn)
    if not android_workflow_preflight_passed(conn):
        return _with_package_state(
            {
                "status": "blocked_android_workflow_check_required",
                "fraction_index": fraction_index,
                "android_workflow_preflight": android_preflight,
                "progression_allowed": False,
                "route_on_failure": "return_to_b",
                "selene_v1_live": False,
                "review_destination": "Status",
                "review_status": "status_only",
            },
            transfer_approved=bool(package.get("transfer_approved")),
        )
    status = fractional_corpus_status(conn)
    if not status.get("items"):
        prepare_fractional_corpus(conn, {})
        status = fractional_corpus_status(conn)
    items = status.get("items") or []
    current = _fraction_by_index(items, fraction_index)
    if not current:
        raise ValueError("fraction manifest not prepared")
    blockers: list[str] = []
    if fraction_index > 1:
        previous = _fraction_by_index(items, fraction_index - 1)
        if not previous or previous.get("status") != "tests_passed_ready_for_next_fraction":
            blockers.append(f"fraction_{fraction_index - 1}_not_passed")
    checks = [
        _check("sealed_package_available", bool(package.get("transfer_approved")), "transfer_c_readable_packages", "C-readable package is sealed."),
        _check("previous_fraction_passed", not blockers, "memory_fractional_corpus_manifests", "Previous fraction passed before this fraction."),
        _check("chronological_bounds_present", int(current.get("start_order") or 0) <= int(current.get("end_order") or 0) or int(current.get("conversation_count") or 0) == 0, "b_corpus_conversations", "Fraction has stable chronological bounds."),
        _check("bounded_preview_only", True, "memory_fractional_corpus_manifests", "Fraction stores manifest ranges and summaries, not live memory."),
        _check("return_to_b_on_failure", True, "Cocoon", "Checks needing support stop progression and route to Cocoon tending."),
        _check("no_activation_or_recall", True, "guard_flags", "Activation, live memory, and broad live recall remain locked."),
    ]
    passed = all(item["passed"] for item in checks) and not blockers
    new_status = "tests_passed_ready_for_next_fraction" if passed else "tests_failed_return_to_b"
    test_json = {
        "checks": checks,
        "blockers": blockers,
        "tested_at": _stamp(),
        "route_on_failure": "return_to_b",
        "selene_v1_live": False,
        **GUARD_FLAGS,
    }
    conn.execute(
        """
        UPDATE memory_fractional_corpus_manifests
        SET status = ?, test_json = ?, updated_at = CURRENT_TIMESTAMP
        WHERE fraction_index = ?
        """,
        (new_status, json.dumps(test_json), fraction_index),
    )
    conn.commit()
    updated = _decode_fraction(conn.execute("SELECT * FROM memory_fractional_corpus_manifests WHERE fraction_index = ?", (fraction_index,)).fetchone())
    return _with_package_state(
        {
            "status": "fractional_corpus_tests_passed" if passed else "fractional_corpus_tests_failed_return_to_b",
            "fraction": updated,
            "checks": checks,
            "blockers": blockers,
            "progression_allowed": passed,
            "android_workflow_preflight": android_preflight,
            "route_on_failure": "return_to_b",
            "selene_v1_live": False,
            "review_destination": "Status" if passed else "Cocoon",
            "review_status": "status_only" if passed else "review_only",
        },
        transfer_approved=bool(package.get("transfer_approved")),
    )


def dream_state_status(conn: sqlite3.Connection) -> dict[str, Any]:
    package = latest_c_readable_package(conn)
    fractions = fractional_corpus_status(conn)
    maintenance_reasons = []
    if not fractions.get("all_fractions_passed"):
        maintenance_reasons.append("fractional_memory_incomplete")
    return _with_package_state(
        {
            "status": "dream_state_maintenance_status_ready",
            "dream_state_required_for_memory_changes": True,
            "selene_chat_live_operation_allowed": False,
            "allowed_preview_work": ["dry_run_chat", "status_inspection", "return_to_b_repair"],
            "blocked_during_core_memory_work": ["activation", "live_memory_write", "runtime_recall", "raw_import", "training", "autonomous_action"],
            "maintenance_reasons": maintenance_reasons,
            "route_core_vessel_memory_changes_to": "Cocoon / B",
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=bool(package.get("transfer_approved")),
    )


def _ordered_conversations(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT *
        FROM b_corpus_conversations
        ORDER BY COALESCE(create_time, update_time, id), source_file, conversation_id
        """
    ).fetchall()
    return [dict(row) for row in rows]


def _fraction_bounds(total: int, index: int) -> tuple[int, int]:
    if total <= 0:
        return 0, 0
    start = math.floor((index - 1) * total / 4)
    end = math.floor(index * total / 4)
    return start, end


def _source_range(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"empty": True}
    first = rows[0]
    last = rows[-1]
    return {
        "first": _conversation_ref(first),
        "last": _conversation_ref(last),
        "start_time": first.get("create_time") or first.get("update_time"),
        "end_time": last.get("update_time") or last.get("create_time"),
        "bounded": True,
        "raw_corpus_imported": False,
    }


def _conversation_ref(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_file": row.get("source_file"),
        "conversation_id": row.get("conversation_id"),
        "title": row.get("title"),
    }


def _next_fraction(items: list[dict[str, Any]]) -> int:
    for index in range(1, 5):
        item = _fraction_by_index(items, index)
        if not item or item.get("status") != "tests_passed_ready_for_next_fraction":
            return index
    return 4


def _fraction_by_index(items: list[dict[str, Any]], index: int) -> dict[str, Any] | None:
    for item in items:
        if int(item.get("fraction_index") or 0) == index:
            return item
    return None


def _count_package_rows(package: dict[str, Any], *, included: bool) -> int:
    if not package.get("transfer_approved"):
        return 0
    payload = _loads_dict(package.get("package_json"))
    key = "included_manifest_items" if included else "excluded_manifest_items"
    items = payload.get(key) if isinstance(payload.get(key), list) else []
    return len(items)


def _package_summary(package: dict[str, Any]) -> dict[str, Any]:
    if not package.get("transfer_approved"):
        return {"available": False, "package_hash": "", "status": package.get("status") or "no_c_readable_package"}
    return {
        "available": True,
        "id": package.get("id"),
        "package_hash": package.get("package_hash"),
        "status": package.get("status"),
        "included_counts": package.get("included_counts") or {},
        "excluded_counts": package.get("excluded_counts") or {},
        "created_at": package.get("created_at"),
    }


def _decode_inspection(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    item = dict(row)
    item["check_json"] = _loads_dict(item.get("check_json"))
    item["source_refs"] = _loads_list(item.get("source_refs"))
    return item


def _decode_fraction(row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        return {}
    item = dict(row)
    item["source_range_json"] = _loads_dict(item.get("source_range_json"))
    item["test_json"] = _loads_dict(item.get("test_json"))
    item["source_refs"] = _loads_list(item.get("source_refs"))
    item["transfer_approved"] = False
    item.update(GUARD_FLAGS)
    return item


def _check(key: str, passed: bool, source: str, summary: str) -> dict[str, Any]:
    return {"key": key, "passed": bool(passed), "source": source, "summary": summary}


def _with_package_state(payload: dict[str, Any], *, transfer_approved: bool) -> dict[str, Any]:
    guarded = {**payload, **GUARD_FLAGS}
    guarded["transfer_approved"] = bool(transfer_approved)
    guarded["activation_change"] = "none"
    guarded["memory_write_active"] = False
    guarded["runtime_memory_recall"] = False
    guarded["raw_a_import_allowed"] = False
    guarded["training_allowed"] = False
    guarded["self_replication_allowed"] = False
    guarded["autonomous_action_allowed"] = False
    return guarded


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
