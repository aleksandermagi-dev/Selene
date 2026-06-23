from __future__ import annotations

import json
import re
import sqlite3
from typing import Any


GUARD_FLAGS: dict[str, Any] = {
    "transfer_approved": False,
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
}

PENDING_REVIEW_STATUSES = ("pending_review", "needs_followup", "needs_b_review", "needs_correction")


def clean_up_my_office_residue(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _reject_forbidden_payload(payload)
    counts = {
        "speech_rehearsals": _mark_table_status_only(conn, "vessel_speech_generation_rehearsals"),
        "ledger_duplicates_superseded": _dedupe_evidence_ledger(conn),
        "ledger_rows_accepted_for_context": _accept_single_residue_ledger_rows(conn),
        "cycle_rows": _mark_table_status_only(conn, "c_runtime_wake_sleep_dream_cycles"),
        "causal_rows": _mark_table_status_only(conn, "c_runtime_causal_sandbox_records"),
        "reconstruction_gap_memory_rows": 0,
        "organ_bus_diagnostics": _mark_organ_bus_diagnostics(conn),
        "review_queue_rows": 0,
    }
    for table in (
        "vessel_reconstruction_check_runs",
        "vessel_gap_scaffold_records",
        "vessel_gap_targets",
        "vessel_memory_accession_proposals",
    ):
        counts["reconstruction_gap_memory_rows"] += _mark_table_status_only(conn, table)

    counts["review_queue_rows"] = _mark_review_queue_residue_status_only(conn)
    changed_count = sum(int(value) for value in counts.values())
    conn.commit()
    return {
        "status": "my_office_residue_cleanup_complete" if changed_count else "my_office_residue_cleanup_noop",
        "message": "Office residue moved to Status/History; no records were deleted." if changed_count else "Nothing new needed cleanup.",
        "changed_count": changed_count,
        "counts": counts,
        "idempotent": changed_count == 0,
        "records_deleted": 0,
        "review_destination": "Status",
        "decision": "review_residue_moved_to_status_only_not_deleted",
        **GUARD_FLAGS,
    }


def _mark_table_status_only(conn: sqlite3.Connection, table: str, extra_where: str | None = None) -> int:
    if not _table_has_columns(conn, table, {"review_status"}):
        return 0
    where = "review_status IN ({})".format(",".join("?" for _ in PENDING_REVIEW_STATUSES))
    params: list[Any] = list(PENDING_REVIEW_STATUSES)
    if extra_where:
        where = f"({where}) AND ({extra_where})"
    cur = conn.execute(
        f"UPDATE {table} SET review_status = 'status_only' WHERE {where}",
        params,
    )
    return int(cur.rowcount if cur.rowcount != -1 else 0)


def _mark_review_queue_residue_status_only(conn: sqlite3.Connection) -> int:
    if not _table_has_columns(conn, "vessel_review_queue", {"subject_table", "status", "review_status"}):
        return 0
    residue_tables = (
        "vessel_speech_generation_rehearsals",
        "vessel_reconstruction_check_runs",
        "vessel_gap_scaffold_records",
        "vessel_gap_targets",
        "vessel_memory_accession_proposals",
        "c_runtime_wake_sleep_dream_cycles",
        "c_runtime_causal_sandbox_records",
        "vessel_organ_bus_messages",
    )
    placeholders = ",".join("?" for _ in residue_tables)
    status_placeholders = ",".join("?" for _ in PENDING_REVIEW_STATUSES)
    cur = conn.execute(
        f"""
        UPDATE vessel_review_queue
           SET status = 'status_only',
               review_status = 'status_only'
         WHERE subject_table IN ({placeholders})
           AND (status IN ({status_placeholders}) OR review_status IN ({status_placeholders}))
        """,
        (*residue_tables, *PENDING_REVIEW_STATUSES, *PENDING_REVIEW_STATUSES),
    )
    return int(cur.rowcount if cur.rowcount != -1 else 0)


def _mark_organ_bus_diagnostics(conn: sqlite3.Connection) -> int:
    if not _table_has_columns(conn, "vessel_organ_bus_messages", {"message_type", "review_status"}):
        return 0
    cur = conn.execute(
        """
        UPDATE vessel_organ_bus_messages
           SET review_status = 'diagnostic_only'
         WHERE message_type LIKE '%diagnostic%'
           AND review_status NOT IN ('diagnostic_only', 'status_only', 'blocked')
        """
    )
    return int(cur.rowcount if cur.rowcount != -1 else 0)


def _dedupe_evidence_ledger(conn: sqlite3.Connection) -> int:
    if not _table_has_columns(conn, "vessel_evidence_tension_ledger", {"id", "claim", "conclusion_status", "payload_json"}):
        return 0
    rows = [
        dict(row)
        for row in conn.execute(
            """
            SELECT * FROM vessel_evidence_tension_ledger
             WHERE conclusion_status = 'needs_review'
             ORDER BY claim, id DESC
            """
        ).fetchall()
    ]
    by_claim: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_claim.setdefault(_normalize_claim(str(row.get("claim") or "")), []).append(row)

    changed = 0
    for duplicates in by_claim.values():
        if len(duplicates) < 2:
            continue
        keep = duplicates[0]
        if _set_ledger_status(conn, keep, "accepted_for_now", "review_only", "Ledger", {"cleanup_resolution": "kept_newest_duplicate_as_context_preview"}):
            changed += 1
        for duplicate in duplicates[1:]:
            if _set_ledger_status(
                conn,
                duplicate,
                "superseded",
                "review_only",
                "Ledger",
                {"cleanup_resolution": "duplicate_superseded", "superseded_by": keep["id"]},
            ):
                changed += 1
    return changed


def _accept_single_residue_ledger_rows(conn: sqlite3.Connection) -> int:
    if not _table_has_columns(conn, "vessel_evidence_tension_ledger", {"id", "claim", "conclusion_status", "payload_json"}):
        return 0
    rows = [
        dict(row)
        for row in conn.execute(
            """
            SELECT * FROM vessel_evidence_tension_ledger
             WHERE conclusion_status = 'needs_review'
             ORDER BY id DESC
            """
        ).fetchall()
    ]
    changed = 0
    for row in rows:
        claim = str(row.get("claim") or "").lower()
        if any(token in claim for token in ("review-only", "review only", "architecture", "packet", "diagnostic", "pre-core")):
            if _set_ledger_status(
                conn,
                row,
                "accepted_for_now",
                "review_only",
                "Ledger",
                {"cleanup_resolution": "system_residue_accepted_for_context_preview"},
            ):
                changed += 1
    return changed


def _set_ledger_status(
    conn: sqlite3.Connection,
    row: dict[str, Any],
    conclusion_status: str,
    review_status: str,
    review_destination: str,
    payload_updates: dict[str, Any],
) -> bool:
    if (
        str(row.get("conclusion_status") or "") == conclusion_status
        and str(row.get("review_status") or "") == review_status
        and str(row.get("review_destination") or "") == review_destination
    ):
        return False
    payload_json = _decode_json(row.get("payload_json"))
    payload_json.update(
        {
            "my_office_cleanup": True,
            "records_deleted": 0,
            **payload_updates,
            **GUARD_FLAGS,
        }
    )
    conn.execute(
        """
        UPDATE vessel_evidence_tension_ledger
           SET conclusion_status = ?,
               review_status = ?,
               review_destination = ?,
               payload_json = ?
         WHERE id = ?
        """,
        (conclusion_status, review_status, review_destination, json.dumps(payload_json), int(row["id"])),
    )
    return True


def _table_has_columns(conn: sqlite3.Connection, table: str, columns: set[str]) -> bool:
    table_row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table,),
    ).fetchone()
    if not table_row:
        return False
    found = {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    return columns.issubset(found)


def _decode_json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    try:
        parsed = json.loads(str(value or "{}"))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _normalize_claim(claim: str) -> str:
    return re.sub(r"\s+", " ", claim.strip().casefold())


def _reject_forbidden_payload(payload: dict[str, Any]) -> None:
    haystack = json.dumps(payload, sort_keys=True).lower()
    forbidden = (
        "transfer approved",
        "activate c",
        "live memory write",
        "runtime recall",
        "raw a import",
        "train model",
        "self replicate",
    )
    if any(term in haystack for term in forbidden):
        raise ValueError("Cleanup cannot carry activation, transfer, memory-write, raw-import, training, or self-replication instructions.")
