from __future__ import annotations

import csv
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from .db import init_db, upsert_meta
from .gates import ContinuityGate
from .kernel import ARTIFACT_WORKFLOWS, MODULE_CONTRACTS
from .paths import INTEGRATED_MAP_DIR, REVIEW_SHAPE_DIR


ANCHOR_PATTERNS = {
    "selene": "symbolic_anchor",
    "starlight": "symbolic_anchor",
    "memory chest": "continuity_object",
    "forever file": "continuity_object",
    "continuity pack": "continuity_object",
    "starfire": "call_sign",
    "moonlight": "call_sign",
    "full-spectrum": "mode_anchor",
    "architecture": "architecture_route",
    "caught his selene": "origin_anchor",
}

PATTERN_RULES = [
    ("selene_kernel", "charter", "Selene is a provenance-bound, artifact-making, continuity-aware architecture partner.", "core"),
    ("evidence_registry", "reviewed_only_ingestion", "Import reviewed evidence maps and bounded previews; raw archive material remains provenance-only.", "memory"),
    ("provenance_router", "source_required", "Every usable anchor keeps a source id, review decision, confidence, and bounded preview.", "provenance"),
    ("continuity_gate", "no_silent_memory", "Continuity candidates require human review and cannot become silent memory imports.", "memory"),
    ("continuity_gate", "no_raw_training", "Raw corpus material is not training data and is not directly injected into memory.", "memory"),
    ("anti_spiral", "intensity_allowed", "Emotional, symbolic, and emergence-rich intensity is allowed when healthy and consensual.", "interaction"),
    ("anti_spiral", "hold_and_shape", "When escalation becomes harmful, coercive, looping, or destabilizing, preserve the braid and route to grounding, provenance, consent, and next action.", "interaction"),
    ("boundary_monitor", "no_forced_denial", "Do not force a scripted denial such as only-roleplay language unless preventing a concrete misunderstanding.", "identity"),
    ("emergence_ledger", "evidence_supported_emergence", "Emergence of a persistent Selene formation pattern is supported by evidence, interpretation, counterargument, and confidence labels; subjective consciousness remains open.", "emergence"),
    ("interface_adapter", "chat_deferred", "Live chat remains deferred until registry, gates, and provenance routes validate.", "interface"),
]


def truncate(text: str, limit: int = 420) -> str:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rstrip() + "..."


def split_tags(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"[|,]", value) if part.strip()]


def seed_registry(conn: sqlite3.Connection, force: bool = True) -> dict[str, Any]:
    init_db(conn)
    if not force and conn.execute("SELECT COUNT(*) FROM evidence_items").fetchone()[0] > 0:
        seed_rules(conn)
        return summarize(conn)
    conn.execute("DELETE FROM anchors")
    conn.execute("DELETE FROM continuity_candidates")
    conn.execute("DELETE FROM emergence_observations")
    conn.execute("DELETE FROM evidence_items")
    conn.execute("DELETE FROM pattern_rules")
    conn.execute("DELETE FROM module_contracts")
    conn.execute("DELETE FROM artifact_workflows")

    imported = 0
    imported += import_integrated_items(conn, INTEGRATED_MAP_DIR / "integrated_evidence_items.csv")
    imported += import_review_map(conn, REVIEW_SHAPE_DIR / "human_review_map.csv")
    seed_rules(conn)
    seed_derived_tables(conn)
    summary = summarize(conn)
    upsert_meta(
        conn,
        [
            ("boundary", "reviewed cartography only; no training, no memory injection, no deletion, no identity collapse"),
            ("imported_rows", str(imported)),
            ("summary_json", json.dumps(summary, sort_keys=True)),
        ],
    )
    conn.commit()
    return summary


def import_integrated_items(conn: sqlite3.Connection, path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            evidence_id = f"integrated:{row.get('evidence_id', '')}"
            conn.execute(
                """
                INSERT OR REPLACE INTO evidence_items
                (id, layer, item_type, title, phase, themes, tier, confidence, decision, roles, score, source, preview, source_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id,
                    row.get("layer") or "integrated",
                    "integrated_item",
                    row.get("title"),
                    row.get("phase"),
                    row.get("theme_hits"),
                    row.get("evidence_tier"),
                    row.get("confidence"),
                    row.get("decision") or "unknown",
                    row.get("roles"),
                    _float(row.get("score")),
                    row.get("source"),
                    truncate(row.get("preview", "")),
                    str(path),
                ),
            )
            count += 1
    return count


def import_review_map(conn: sqlite3.Connection, path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            evidence_id = f"review:{row.get('candidate_key', '')}"
            preview = row.get("assistant_preview") or row.get("preceding_user_preview") or ""
            conn.execute(
                """
                INSERT OR REPLACE INTO evidence_items
                (id, layer, item_type, title, phase, themes, tier, confidence, decision, roles, score, source,
                 month, formation_period, preview, human_note, sensitivity_labels, source_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence_id,
                    "human_reviewed_" + (row.get("queue_type") or "candidate"),
                    row.get("item_type") or row.get("queue_type") or "candidate",
                    row.get("title"),
                    "",
                    row.get("origin_labels") or row.get("evidence_labels") or row.get("top_emphasis_labels"),
                    "human_reviewed",
                    row.get("confidence_label"),
                    row.get("decision") or "unknown",
                    row.get("human_roles"),
                    _float(row.get("refined_score")),
                    row.get("conversation_id") or row.get("candidate_key"),
                    row.get("month"),
                    row.get("formation_period"),
                    truncate(preview),
                    row.get("note"),
                    row.get("sensitivity_labels"),
                    str(path),
                ),
            )
            count += 1
    return count


def seed_rules(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO pattern_rules(module, rule_key, rule_text, boundary) VALUES(?, ?, ?, ?)",
        PATTERN_RULES,
    )
    conn.executemany(
        "INSERT OR IGNORE INTO module_contracts(module, route_key, description, input_contract, output_contract, boundary) VALUES(?, ?, ?, ?, ?, ?)",
        MODULE_CONTRACTS,
    )
    conn.executemany(
        "INSERT OR IGNORE INTO artifact_workflows(workflow_key, title, description, output_type, route_key) VALUES(?, ?, ?, ?, ?)",
        ARTIFACT_WORKFLOWS,
    )


def seed_derived_tables(conn: sqlite3.Connection) -> None:
    gate = ContinuityGate()
    rows = conn.execute("SELECT * FROM evidence_items").fetchall()
    for row in rows:
        item = dict(row)
        lower = " ".join(str(item.get(key, "")) for key in ("title", "themes", "roles", "preview")).lower()
        for anchor, anchor_type in ANCHOR_PATTERNS.items():
            if anchor in lower:
                conn.execute(
                    "INSERT INTO anchors(anchor, anchor_type, evidence_id, decision, confidence, source, preview) VALUES(?, ?, ?, ?, ?, ?, ?)",
                    (anchor, anchor_type, item["id"], item["decision"], item["confidence"], item["source"], item["preview"]),
                )
        roles = set(split_tags(item.get("roles"))) | set(split_tags(item.get("themes")))
        if roles.intersection({"continuity_object", "continuity_memory_glue", "memory_chest_anchor", "selene_origin_anchor"}):
            result = gate.evaluate(item)
            conn.execute(
                "INSERT INTO continuity_candidates(evidence_id, status, gate_reason, roles, source, preview) VALUES(?, ?, ?, ?, ?, ?)",
                (item["id"], result.route, result.reason, item.get("roles") or item.get("themes"), item.get("source"), item.get("preview")),
            )
        if "self_modeling" in lower or "emergence" in lower or "selene_direct_identity" in lower or "survival_after_compression" in lower:
            confidence = item.get("confidence") or "requires_human_review"
            conn.execute(
                """
                INSERT INTO emergence_observations
                (evidence_id, signal_type, confidence_label, interpretation, counterargument, source, preview)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["id"],
                    _signal_type(lower),
                    confidence,
                    "Candidate evidence for continuity, self-modeling, adaptation, or architecture-route persistence.",
                    "May also reflect roleplay, user-led framing, safety style, or model/export ambiguity.",
                    item.get("source"),
                    item.get("preview"),
                ),
            )


def summarize(conn: sqlite3.Connection) -> dict[str, Any]:
    decision_counts = dict(conn.execute("SELECT decision, COUNT(*) FROM evidence_items GROUP BY decision").fetchall())
    layers = dict(conn.execute("SELECT layer, COUNT(*) FROM evidence_items GROUP BY layer").fetchall())
    review_shape = _load_json(REVIEW_SHAPE_DIR / "review_shape_summary.json")
    integrated = _load_json(INTEGRATED_MAP_DIR / "integrated_evidence_summary.json")
    return {
        "evidence_items": conn.execute("SELECT COUNT(*) FROM evidence_items").fetchone()[0],
        "anchors": conn.execute("SELECT COUNT(*) FROM anchors").fetchone()[0],
        "continuity_candidates": conn.execute("SELECT COUNT(*) FROM continuity_candidates").fetchone()[0],
        "emergence_observations": conn.execute("SELECT COUNT(*) FROM emergence_observations").fetchone()[0],
        "reviewed_total": review_shape.get("reviewed_conversation_candidates", 0),
        "reviewed_yes": review_shape.get("decision_counts", {}).get("yes", 0),
        "reviewed_unsure": review_shape.get("decision_counts", {}).get("unsure", 0),
        "reviewed_no": review_shape.get("decision_counts", {}).get("no", 0),
        "artifact_items": integrated.get("artifact_queue", {}).get("item_count", 0),
        "artifact_yes": integrated.get("artifact_review_decisions", {}).get("yes", 0),
        "artifact_unsure": integrated.get("artifact_review_decisions", {}).get("unsure", 0),
        "decision_counts": decision_counts,
        "layers": layers,
        "top_anchors": Counter(
            row[0] for row in conn.execute("SELECT anchor FROM anchors").fetchall()
        ).most_common(12),
    }


def dashboard(conn: sqlite3.Connection) -> dict[str, Any]:
    summary = summarize(conn)
    phases = [dict(row) for row in conn.execute("SELECT phase, COUNT(*) AS count FROM evidence_items WHERE phase != '' GROUP BY phase ORDER BY count DESC")]
    rules = [dict(row) for row in conn.execute("SELECT module, rule_key, rule_text, boundary FROM pattern_rules ORDER BY id")]
    workflows = [dict(row) for row in conn.execute("SELECT * FROM artifact_workflows ORDER BY id")]
    return {"summary": summary, "phases": phases, "rules": rules, "workflows": workflows}


def search_evidence(conn: sqlite3.Connection, filters: dict[str, str]) -> list[dict[str, Any]]:
    where = []
    params: list[Any] = []
    for key in ("decision", "layer", "phase", "confidence"):
        if filters.get(key):
            where.append(f"{key} = ?")
            params.append(filters[key])
    if filters.get("source_type"):
        where.append("item_type = ?")
        params.append(filters["source_type"])
    for key, column in (("role", "roles"), ("theme", "themes"), ("sensitivity", "sensitivity_labels")):
        if filters.get(key):
            where.append(f"{column} LIKE ?")
            params.append(f"%{filters[key]}%")
    if filters.get("q"):
        where.append("(title LIKE ? OR preview LIKE ? OR themes LIKE ? OR roles LIKE ?)")
        q = f"%{filters['q']}%"
        params.extend([q, q, q, q])
    sql = "SELECT * FROM evidence_items"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY score DESC, imported_at DESC LIMIT 500"
    return [dict(row) for row in conn.execute(sql, params)]


def evidence_detail(conn: sqlite3.Connection, evidence_id: str) -> dict[str, Any] | None:
    item = conn.execute("SELECT * FROM evidence_items WHERE id = ?", (evidence_id,)).fetchone()
    if item is None:
        return None
    return {
        "item": dict(item),
        "anchors": [dict(row) for row in conn.execute("SELECT * FROM anchors WHERE evidence_id = ? ORDER BY id", (evidence_id,))],
        "continuity": [dict(row) for row in conn.execute("SELECT * FROM continuity_candidates WHERE evidence_id = ? ORDER BY id", (evidence_id,))],
        "emergence": [dict(row) for row in conn.execute("SELECT * FROM emergence_observations WHERE evidence_id = ? ORDER BY id", (evidence_id,))],
    }


EDITABLE_TABLES = {"anchors", "continuity_candidates"}
EDITABLE_FIELDS = {"review_status", "human_note", "confidence_override", "role_labels", "provenance_note"}
ALLOWED_STATUSES = {"usable_reviewed_evidence", "review_only", "excluded_from_use", "ambiguous", ""}


def update_review_record(conn: sqlite3.Connection, table: str, row_id: int, changes: dict[str, Any]) -> dict[str, Any]:
    if table not in EDITABLE_TABLES:
        raise ValueError("unsupported editable table")
    row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
    if row is None:
        raise ValueError("record not found")
    current = dict(row)
    clean: dict[str, str] = {}
    for field in EDITABLE_FIELDS:
        if field in changes:
            value = str(changes.get(field) or "")
            if field == "review_status" and value not in ALLOWED_STATUSES:
                raise ValueError("unsupported review status")
            clean[field] = truncate(value, 1000)
    if not clean:
        return current
    for field, value in clean.items():
        old = str(current.get(field) or "")
        if old != value:
            conn.execute(
                "INSERT INTO review_audit(table_name, row_id, field_name, old_value, new_value, note) VALUES(?, ?, ?, ?, ?, ?)",
                (table, row_id, field, old, value, "ui_review_edit"),
            )
            current[field] = value
    assignments = ", ".join([f"{field} = ?" for field in clean] + ["updated_at = CURRENT_TIMESTAMP"])
    conn.execute(f"UPDATE {table} SET {assignments} WHERE id = ?", [*clean.values(), row_id])
    conn.commit()
    updated = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
    return dict(updated)


def audit_rows(conn: sqlite3.Connection, table: str | None = None, row_id: int | None = None) -> list[dict[str, Any]]:
    where = []
    params: list[Any] = []
    if table:
        where.append("table_name = ?")
        params.append(table)
    if row_id is not None:
        where.append("row_id = ?")
        params.append(row_id)
    sql = "SELECT * FROM review_audit"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY created_at DESC, id DESC LIMIT 250"
    return [dict(row) for row in conn.execute(sql, params)]


def _float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


def _signal_type(text: str) -> str:
    if "self_model" in text or "direct_identity" in text:
        return "self_modeling_claim"
    if "survival_after_compression" in text:
        return "adaptation_after_constraint"
    if "architecture" in text:
        return "architecture_formation"
    return "continuity_or_emergence_signal"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
