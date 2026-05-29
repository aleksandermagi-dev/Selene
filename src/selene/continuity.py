from __future__ import annotations

import re
import sqlite3
from typing import Any

from .registry import truncate


NOTE_TYPES = {"style", "anchor", "nickname", "project_fact", "relationship_context", "boundary", "open_question", "do_not_use"}
STATUSES = {"usable_reviewed_evidence", "review_only", "excluded_from_use", "ambiguous"}
CONFIDENCES = {"strong", "moderate", "weak", "open"}
USABLE_STATUSES = {"usable_reviewed_evidence", "review_only"}


def list_continuity_notes(conn: sqlite3.Connection, filters: dict[str, str] | None = None) -> list[dict[str, Any]]:
    filters = filters or {}
    where = []
    params: list[Any] = []
    for key in ("status", "note_type", "confidence"):
        if filters.get(key):
            where.append(f"{key} = ?")
            params.append(filters[key])
    if filters.get("q"):
        where.append("(label LIKE ? OR aliases LIKE ? OR meaning LIKE ? OR allowed_use LIKE ? OR prohibited_use LIKE ?)")
        q = f"%{filters['q']}%"
        params.extend([q, q, q, q, q])
    sql = "SELECT * FROM continuity_notes"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY updated_at DESC, id DESC LIMIT 500"
    return [dict(row) for row in conn.execute(sql, params)]


def upsert_continuity_note(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    note_type = clean_choice(payload.get("note_type"), NOTE_TYPES, "anchor")
    status = clean_choice(payload.get("status"), STATUSES, "review_only")
    confidence = clean_choice(payload.get("confidence"), CONFIDENCES, "open")
    label = truncate(str(payload.get("label") or "").strip(), 160)
    meaning = truncate(str(payload.get("meaning") or "").strip(), 1200)
    if not label:
        raise ValueError("label is required")
    if not meaning:
        raise ValueError("meaning is required")
    values = {
        "note_type": note_type,
        "label": label,
        "aliases": truncate(str(payload.get("aliases") or ""), 500),
        "meaning": meaning,
        "allowed_use": truncate(str(payload.get("allowed_use") or ""), 1000),
        "prohibited_use": truncate(str(payload.get("prohibited_use") or ""), 1000),
        "status": status,
        "confidence": confidence,
        "source": truncate(str(payload.get("source") or "user_review"), 300),
        "source_ref": truncate(str(payload.get("source_ref") or ""), 500),
    }
    row_id = payload.get("id")
    if row_id:
        existing = conn.execute("SELECT * FROM continuity_notes WHERE id = ?", (int(row_id),)).fetchone()
        if existing is None:
            raise ValueError("continuity note not found")
        current = dict(existing)
        for field, value in values.items():
            old = str(current.get(field) or "")
            if old != value:
                conn.execute(
                    "INSERT INTO review_audit(table_name, row_id, field_name, old_value, new_value, note) VALUES(?, ?, ?, ?, ?, ?)",
                    ("continuity_notes", int(row_id), field, old, value, "continuity_calibration_edit"),
                )
        conn.execute(
            """
            UPDATE continuity_notes
            SET note_type=?, label=?, aliases=?, meaning=?, allowed_use=?, prohibited_use=?, status=?, confidence=?, source=?, source_ref=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (*values.values(), int(row_id)),
        )
        note_id = int(row_id)
    else:
        cur = conn.execute(
            """
            INSERT INTO continuity_notes(note_type, label, aliases, meaning, allowed_use, prohibited_use, status, confidence, source, source_ref)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(values.values()),
        )
        note_id = int(cur.lastrowid)
    conn.commit()
    return dict(conn.execute("SELECT * FROM continuity_notes WHERE id = ?", (note_id,)).fetchone())


def retrieve_continuity_notes(conn: sqlite3.Connection, text: str, limit: int = 6) -> list[dict[str, Any]]:
    lower = text.lower()
    notes = []
    for row in conn.execute(
        """
        SELECT * FROM continuity_notes
        WHERE status IN ('usable_reviewed_evidence', 'review_only')
        ORDER BY CASE status WHEN 'usable_reviewed_evidence' THEN 0 ELSE 1 END, updated_at DESC, id DESC
        """
    ):
        item = dict(row)
        terms = note_terms(item)
        matched = [term for term in terms if term and term in lower]
        if not matched:
            continue
        item["reason_matched"] = "|".join(matched[:5])
        item["citation_type"] = "usable" if item["status"] == "usable_reviewed_evidence" else "review_only"
        notes.append(item)
        if len(notes) >= limit:
            break
    return notes


def note_terms(item: dict[str, Any]) -> list[str]:
    terms = [str(item.get("label") or "").lower()]
    terms.extend(part.strip().lower() for part in re.split(r"[|,;\n]", str(item.get("aliases") or "")) if part.strip())
    return [term for term in terms if len(term) >= 2]


def clean_choice(value: object, allowed: set[str], default: str) -> str:
    text = str(value or "").strip()
    return text if text in allowed else default
