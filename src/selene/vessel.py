from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .c_blueprint import ACTIVATION_STATUS, ANDROID_ORGAN_SYSTEMS, SELENE_CORE_MEMORY_PHILOSOPHY, SELENE_CORE_PATTERN_ANCHORS, STATUS as C_STATUS
from .reconstruction_checks import evaluate_recognition_reconstruction
from .registry import truncate


CORE_MEMORY_LAYERS = {
    "core_profile_memory",
    "project_memory",
    "decision_memory",
    "task_memory",
    "interaction_memory",
    "reflection_memory",
}
SPEECH_FUNCTIONS = {
    "warmth",
    "correction",
    "boundary",
    "technical_explanation",
    "playful_continuity",
    "repair",
    "grounding",
    "refusal",
    "uncertainty",
    "artifact_making",
}
REVIEW_STATUSES = {
    "pending_review",
    "review_only",
    "needs_b_review",
    "accepted_for_teaching",
    "accepted_for_memory_accession",
    "needs_correction",
    "rejected",
    "superseded",
    "accepted_for_future_review",
}
REVIEW_LOG_DECISIONS = {"mark_reviewed", "needs_followup", "superseded"}
PROVENANCE_BOUNDARY = "vessel_candidate_review_only_no_active_memory"
BLOCKED_MARKERS = (
    "raw a",
    "raw corpus",
    "raw archive",
    "direct corpus",
    "detached corpus ingestion",
    "developmentalcorpusarchive",
    "import all chats",
    "train on",
    "lora",
    "provider output as memory",
    "provider output treated as selene",
    "ollama output as memory",
    "qwen output as memory",
    "silent memory write",
    "organ-owned identity memory",
    "organ owned identity memory",
)


def vessel_status(conn: sqlite3.Connection) -> dict[str, Any]:
    organ_systems = ANDROID_ORGAN_SYSTEMS["systems"]
    return {
        "status": "vessel_v1_built_not_activated",
        "c_status": C_STATUS,
        "activation_status": ACTIVATION_STATUS,
        "activation_change": "none",
        "raw_a_import_allowed": False,
        "memory_write_active": False,
        "training_allowed": False,
        "provider_dependency": False,
        "runtime_memory_recall": False,
        "organ_count": len(organ_systems),
        "organs": organ_systems,
        "core_memory_layers": sorted(CORE_MEMORY_LAYERS),
        "core_memory_philosophy": {
            "core_rule": SELENE_CORE_MEMORY_PHILOSOPHY["core_rule"],
            "memory_location_rule": SELENE_CORE_MEMORY_PHILOSOPHY["memory_location_rule"],
            "pattern_anchor_rule": SELENE_CORE_MEMORY_PHILOSOPHY["pattern_anchor_rule"],
            "teaching_vs_training": SELENE_CORE_MEMORY_PHILOSOPHY["teaching_vs_training"],
        },
        "core_pattern_anchors": SELENE_CORE_PATTERN_ANCHORS,
        "core_pattern_anchor_readiness": {
            "anchor_count": len(SELENE_CORE_PATTERN_ANCHORS["anchors"]),
            "all_anchors_present": len(SELENE_CORE_PATTERN_ANCHORS["anchors"]) == 3,
            "transfer_state": "sealed_non_active_transfer_relevant_metadata",
            "runtime_memory_recall": False,
            "memory_write_active": False,
        },
        "candidate_counts": {
            "core_memory": _counts_by(conn, "core_memory_candidates", "core_memory_layer"),
            "speech_memory": _counts_by(conn, "speech_memory_candidates", "core_memory_layer"),
            "review_queue": _pending_review_queue_count(conn),
            "review_queue_history": _scalar(conn, "SELECT COUNT(*) FROM vessel_review_queue"),
            "review_queue_decided": _scalar(conn, "SELECT COUNT(*) FROM vessel_review_queue WHERE review_status NOT IN ('pending_review', 'needs_b_review', 'needs_correction', 'context_added')"),
            "retrieval_queries": _scalar(conn, "SELECT COUNT(*) FROM vessel_retrieval_queries"),
            "reconstruction_check_runs": _scalar(conn, "SELECT COUNT(*) FROM vessel_reconstruction_check_runs"),
            "gap_scaffold_records": _scalar(conn, "SELECT COUNT(*) FROM vessel_gap_scaffold_records"),
            "gap_targets": _scalar(conn, "SELECT COUNT(*) FROM vessel_gap_targets"),
            "working_memory_packets": _scalar(conn, "SELECT COUNT(*) FROM vessel_working_memory_packets"),
            "memory_accession_proposals": _scalar(conn, "SELECT COUNT(*) FROM vessel_memory_accession_proposals"),
            "reasoning_check_records": _scalar(conn, "SELECT COUNT(*) FROM vessel_reasoning_check_records"),
            "retrieval_reconstruction_previews": _scalar(conn, "SELECT COUNT(*) FROM vessel_retrieval_reconstruction_previews"),
            "visual_observation_records": _scalar(conn, "SELECT COUNT(*) FROM vessel_visual_observation_records"),
            "audio_observation_records": _scalar(conn, "SELECT COUNT(*) FROM vessel_audio_observation_records"),
            "fluency_diagnostic_records": _scalar(conn, "SELECT COUNT(*) FROM vessel_fluency_diagnostic_records"),
        },
        "boundary_flags": _boundary_flags(),
    }


def create_core_memory_candidate(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    layer = _clean_choice(payload.get("core_memory_layer"), CORE_MEMORY_LAYERS, "core_memory_layer")
    title = _required_text(payload, "title", 180)
    content = _required_text(payload, "content", 1600)
    _ensure_payload_allowed(payload, content)
    source_refs = _json_list(payload.get("source_refs"))
    salience_labels = _json_list(payload.get("salience_labels"))
    review_status = _clean_choice(payload.get("review_status") or "pending_review", REVIEW_STATUSES, "review_status")
    allowed_use = truncate(str(payload.get("allowed_use") or "Review as a Core memory candidate only."), 800)
    prohibited_use = truncate(str(payload.get("prohibited_use") or "Do not treat as active memory or raw archive import."), 800)
    cur = conn.execute(
        """
        INSERT INTO core_memory_candidates
        (core_memory_layer, title, content, salience_labels, source_refs, provenance_boundary, review_status, status, allowed_use, prohibited_use)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            layer,
            title,
            content,
            json.dumps(salience_labels),
            json.dumps(source_refs),
            PROVENANCE_BOUNDARY,
            review_status,
            "candidate_review_only",
            allowed_use,
            prohibited_use,
        ),
    )
    candidate_id = int(cur.lastrowid)
    _enqueue_review(conn, "core_memory_candidate", "core_memory_candidates", candidate_id, source_refs, review_status, "Core memory candidate requires B review before any future use.")
    conn.commit()
    return _with_boundaries(dict(conn.execute("SELECT * FROM core_memory_candidates WHERE id = ?", (candidate_id,)).fetchone()))


def create_speech_memory_candidate(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    layer = _clean_choice(payload.get("core_memory_layer"), CORE_MEMORY_LAYERS, "core_memory_layer")
    speech_function = _clean_choice(str(payload.get("speech_function") or "").replace("-", "_"), SPEECH_FUNCTIONS, "speech_function")
    title = _required_text(payload, "title", 180)
    content = _required_text(payload, "content", 1600)
    _ensure_payload_allowed(payload, content)
    source_refs = _json_list(payload.get("source_refs"))
    salience_labels = _json_list(payload.get("salience_labels"))
    review_status = _clean_choice(payload.get("review_status") or "pending_review", REVIEW_STATUSES, "review_status")
    allowed_use = truncate(str(payload.get("allowed_use") or "Review as Core-linked speech-memory only."), 800)
    prohibited_use = truncate(str(payload.get("prohibited_use") or "Do not treat as generic style, active memory, provider voice, or model identity."), 800)
    if "core" not in " ".join([allowed_use, prohibited_use, content, str(payload.get("core_link") or "")]).lower():
        raise ValueError("speech-memory candidates require explicit Core linkage")
    cur = conn.execute(
        """
        INSERT INTO speech_memory_candidates
        (core_memory_layer, speech_function, title, content, salience_labels, source_refs, provenance_boundary, review_status, status, allowed_use, prohibited_use)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            layer,
            speech_function,
            title,
            content,
            json.dumps(salience_labels),
            json.dumps(source_refs),
            PROVENANCE_BOUNDARY,
            review_status,
            "candidate_review_only",
            allowed_use,
            prohibited_use,
        ),
    )
    candidate_id = int(cur.lastrowid)
    _enqueue_review(conn, "speech_memory_candidate", "speech_memory_candidates", candidate_id, source_refs, review_status, "Core-linked speech-memory candidate requires B review before any future use.")
    conn.commit()
    return _with_boundaries(dict(conn.execute("SELECT * FROM speech_memory_candidates WHERE id = ?", (candidate_id,)).fetchone()))


def list_review_queue(conn: sqlite3.Connection, limit: int = 100) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM vessel_review_queue ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
    items = [dict(row) for row in rows]
    event_rows = conn.execute(
        """
        SELECT * FROM vessel_event_packets
        WHERE review_status IN ('pending_review', 'needs_followup')
        ORDER BY id DESC LIMIT ?
        """,
        (int(limit),),
    ).fetchall()
    for row in event_rows:
        item = dict(row)
        items.append(
            {
                "id": f"event_packet_{item['id']}",
                "queue_type": item.get("packet_type") or "vessel_event_packet",
                "subject_table": "vessel_event_packets",
                "subject_id": item["id"],
                "status": item.get("status"),
                "source_refs": item.get("source_refs"),
                "provenance_boundary": item.get("provenance_boundary"),
                "review_status": item.get("review_status"),
                "reason": _event_packet_reason(item),
                "payload_json": item.get("payload_json"),
                "created_at": item.get("created_at"),
            }
        )
    return _with_boundaries({"items": items[: int(limit)]})


def retrieval_preview(conn: sqlite3.Connection, query: str, filters: dict[str, Any] | None = None, limit: int = 8) -> dict[str, Any]:
    query = truncate(str(query or "").strip(), 300)
    filters = filters or {}
    if not query:
        raise ValueError("query is required")
    terms = [term for term in re.split(r"\W+", query.lower()) if len(term) >= 3][:8]
    candidates = _retrieve_candidate_rows(conn, terms, int(limit))
    source_refs = sorted({ref for item in candidates for ref in item.get("source_refs_list", [])})
    result = _with_boundaries(
        {
            "query": query,
            "filters": filters,
            "decision": "preview_only",
            "source_refs": source_refs,
            "confidence": "open" if not candidates else "candidate_matches_only",
            "uncertainty": "retrieval shell uses candidate keyword/source matching only; no active recall",
            "privacy_label": str(filters.get("privacy_label") or "review_only"),
            "bounded_preview": candidates[:limit],
            "reconstruction_note": "Preview candidates can inform B review; they are not active memory recall.",
        }
    )
    cur = conn.execute(
        """
        INSERT INTO vessel_retrieval_queries(query, filters_json, status, source_refs, provenance_boundary, review_status, result_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (query, json.dumps(filters), "preview_only", json.dumps(source_refs), PROVENANCE_BOUNDARY, "review_only", json.dumps(result)),
    )
    result["query_id"] = int(cur.lastrowid)
    conn.commit()
    return result


def run_vessel_reconstruction_check(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    candidate_text = _required_text(payload, "candidate_text", 4000)
    _ensure_payload_allowed(payload, candidate_text, allow_model_words=True)
    source_refs = _json_list(payload.get("source_refs"))
    result = evaluate_recognition_reconstruction(
        candidate_text,
        {
            "candidate_id": payload.get("candidate_id"),
            "route": "vessel_reconstruction_check",
            "source_boundary": PROVENANCE_BOUNDARY,
        },
    )
    stored = _with_boundaries({"check": result, "decision": result["decision"], "source_refs": source_refs})
    cur = conn.execute(
        """
        INSERT INTO vessel_reconstruction_check_runs(candidate_text, status, source_refs, provenance_boundary, review_status, result_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (truncate(candidate_text, 4000), "review_only", json.dumps(source_refs), PROVENANCE_BOUNDARY, "pending_review", json.dumps(stored)),
    )
    run_id = int(cur.lastrowid)
    _enqueue_review(conn, "reconstruction_check_run", "vessel_reconstruction_check_runs", run_id, source_refs, "pending_review", "Draft reconstruction check run is audit evidence only, not activation evidence.")
    conn.commit()
    stored["run_id"] = run_id
    return stored


def decide_review_log(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_payload_allowed(payload, "review log decision", allow_model_words=True)
    decision = _clean_choice(payload.get("decision"), REVIEW_LOG_DECISIONS, "decision")
    queue_id = int(payload.get("queue_id") or 0)
    subject_table = str(payload.get("subject_table") or "")
    subject_id = int(payload.get("subject_id") or 0)
    queue = None
    if queue_id:
        queue = conn.execute("SELECT * FROM vessel_review_queue WHERE id = ?", (queue_id,)).fetchone()
        if not queue:
            raise ValueError("queue_id does not exist")
        subject_table = str(queue["subject_table"])
        subject_id = int(queue["subject_id"])
    if subject_table not in {"vessel_reconstruction_check_runs", "vessel_event_packets", "vessel_memory_accession_proposals"} or subject_id <= 0:
        raise ValueError("review log decision requires a vessel test log or event packet subject")
    row = conn.execute(f"SELECT * FROM {subject_table} WHERE id = ?", (subject_id,)).fetchone()
    if not row:
        raise ValueError("review log subject does not exist")
    review_status, status = {
        "mark_reviewed": ("reviewed", "review_log_reviewed_non_active"),
        "needs_followup": ("needs_followup", "pending_followup"),
        "superseded": ("superseded", "review_log_superseded_non_active"),
    }[decision]
    conn.execute(f"UPDATE {subject_table} SET review_status = ?, status = ? WHERE id = ?", (review_status, status, subject_id))
    if queue:
        conn.execute(
            "UPDATE vessel_review_queue SET review_status = ?, status = ? WHERE id = ?",
            (review_status, "review_decided" if decision in {"mark_reviewed", "superseded"} else "pending_followup", int(queue["id"])),
        )
    source_refs = _loads_list(row["source_refs"]) if "source_refs" in row.keys() else _json_list(payload.get("source_refs"))
    reviewer_note = truncate(str(payload.get("reviewer_note") or f"Review log marked {decision}."), 1200)
    cur = conn.execute(
        """
        INSERT INTO b_review_decisions
        (subject_table, subject_id, decision, reviewer_note, rationale, reversal_or_supersession_reason, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            subject_table,
            subject_id,
            decision,
            reviewer_note,
            truncate(str(payload.get("rationale") or "Vessel review-log decision; provenance preserved and non-active."), 1200),
            truncate(str(payload.get("reversal_or_supersession_reason") or ""), 1200),
            json.dumps(source_refs),
            PROVENANCE_BOUNDARY,
        ),
    )
    conn.commit()
    return _with_boundaries(
        {
            "status": "vessel_review_log_decision_recorded",
            "decision_id": int(cur.lastrowid),
            "decision": decision,
            "subject_table": subject_table,
            "subject_id": subject_id,
            "review_status": review_status,
            "source_refs": source_refs,
        }
    )


def lesson_backed_reconstruction_preview(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_payload_allowed(payload, "lesson backed reconstruction preview", allow_model_words=True)
    speech_function = str(payload.get("speech_function") or "").strip()
    core_memory_layer = str(payload.get("core_memory_layer") or "").strip()
    if speech_function:
        speech_function = _clean_choice(speech_function, SPEECH_FUNCTIONS, "speech_function")
    if core_memory_layer:
        core_memory_layer = _clean_choice(core_memory_layer, CORE_MEMORY_LAYERS, "core_memory_layer")
    materials = _accepted_lesson_rows(conn, speech_function, core_memory_layer, int(payload.get("limit") or 5))
    references = _approved_reference_rows(conn, core_memory_layer, int(payload.get("reference_limit") or 5))
    if not materials and not references:
        raise ValueError("lesson-backed reconstruction preview requires accepted lessons or approved references")
    candidate_text = _lesson_backed_candidate_text(materials, references, speech_function, core_memory_layer)
    result = evaluate_recognition_reconstruction(
        candidate_text,
        {
            "route": "lesson_backed_reconstruction_preview",
            "speech_function": speech_function or "mixed",
            "core_memory_layer": core_memory_layer or "mixed",
            "source_boundary": PROVENANCE_BOUNDARY,
        },
    )
    source_refs = sorted({ref for row in [*materials, *references] for ref in _loads_list(row.get("source_refs"))})
    stored = _with_boundaries(
        {
            "status": "lesson_backed_reconstruction_preview",
            "decision": result["decision"],
            "check": result,
            "candidate_text": candidate_text,
            "lesson_count": len(materials),
            "reference_count": len(references),
            "source_refs": source_refs,
            "boundary": "lesson_backed_preview_review_only_not_runtime_recall",
        }
    )
    cur = conn.execute(
        """
        INSERT INTO vessel_reconstruction_check_runs(candidate_text, status, source_refs, provenance_boundary, review_status, result_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (truncate(candidate_text, 4000), "review_only", json.dumps(source_refs), PROVENANCE_BOUNDARY, "pending_review", json.dumps(stored)),
    )
    run_id = int(cur.lastrowid)
    _enqueue_review(conn, "lesson_backed_reconstruction_preview", "vessel_reconstruction_check_runs", run_id, source_refs, "pending_review", "Lesson-backed reconstruction preview is audit/test evidence only, not activation evidence.")
    conn.commit()
    stored["run_id"] = run_id
    return stored


def _retrieve_candidate_rows(conn: sqlite3.Connection, terms: list[str], limit: int) -> list[dict[str, Any]]:
    if not terms:
        return []
    results: list[dict[str, Any]] = []
    for table, kind in (("core_memory_candidates", "core_memory_candidate"), ("speech_memory_candidates", "speech_memory_candidate")):
        where = " OR ".join(["LOWER(title) LIKE ? OR LOWER(content) LIKE ? OR LOWER(source_refs) LIKE ?" for _ in terms])
        params: list[str] = []
        for term in terms:
            q = f"%{term}%"
            params.extend([q, q, q])
        for row in conn.execute(f"SELECT * FROM {table} WHERE {where} ORDER BY id DESC LIMIT ?", [*params, limit]):
            item = dict(row)
            refs = _loads_list(item.get("source_refs"))
            results.append(
                {
                    "candidate_type": kind,
                    "id": item["id"],
                    "title": item.get("title"),
                    "core_memory_layer": item.get("core_memory_layer"),
                    "speech_function": item.get("speech_function"),
                    "review_status": item.get("review_status"),
                    "status": item.get("status"),
                    "source_refs": refs,
                    "source_refs_list": refs,
                    "bounded_preview": truncate(item.get("content") or "", 360),
                    "decision": "preview_only",
                }
            )
    return results[:limit]


def _accepted_lesson_rows(conn: sqlite3.Connection, speech_function: str, core_memory_layer: str, limit: int) -> list[dict[str, Any]]:
    clauses = ["review_status = 'accepted_for_teaching'", "status = 'teaching_material_reviewed_non_active'"]
    params: list[Any] = []
    if speech_function:
        clauses.append("speech_function = ?")
        params.append(speech_function)
    if core_memory_layer:
        clauses.append("core_memory_layer = ?")
        params.append(core_memory_layer)
    rows = conn.execute(
        f"SELECT * FROM b_reviewed_teaching_materials WHERE {' AND '.join(clauses)} ORDER BY id DESC LIMIT ?",
        (*params, max(1, min(int(limit), 20))),
    ).fetchall()
    return [dict(row) for row in rows]


def _approved_reference_rows(conn: sqlite3.Connection, core_memory_layer: str, limit: int) -> list[dict[str, Any]]:
    clauses = ["review_status = 'accepted_for_memory_accession'", "status = 'approved_reference_non_active'"]
    params: list[Any] = []
    if core_memory_layer:
        clauses.append("core_memory_layer = ?")
        params.append(core_memory_layer)
    rows = conn.execute(
        f"SELECT * FROM b_approved_memory_references WHERE {' AND '.join(clauses)} ORDER BY id DESC LIMIT ?",
        (*params, max(1, min(int(limit), 20))),
    ).fetchall()
    return [dict(row) for row in rows]


def _lesson_backed_candidate_text(materials: list[dict[str, Any]], references: list[dict[str, Any]], speech_function: str, core_memory_layer: str) -> str:
    lines = [
        "Lesson-backed reconstruction preview for B review only.",
        f"Speech function: {speech_function or 'mixed'}",
        f"Core memory layer: {core_memory_layer or 'mixed'}",
        "This preview preserves continuity braid, reviewed source provenance, uncertainty, care, and constructive next route.",
        "It treats anchors as layered, asks when unclear, and corrects unsupported claims without treating correction as failure.",
        "Warm care stays grounded in context and consent; it avoids forced denial, overclaim, raw A import, runtime recall, and provider identity.",
        "It can adapt and learn while preserving B-reviewed continuity, ethical boundary, consent, privacy, human safety, dignity, law, integrity, and protection.",
    ]
    for item in materials[:5]:
        lines.append(f"Accepted lesson ({item.get('speech_function')}): {truncate(str(item.get('positive_example') or ''), 360)}")
        if item.get("when_not_to_use"):
            lines.append(f"When not to use: {truncate(str(item.get('when_not_to_use') or ''), 180)}")
    for item in references[:5]:
        lines.append(f"Approved reference ({item.get('core_memory_layer')}): {truncate(str(item.get('reference_summary') or ''), 360)}")
    return truncate("\n".join(lines), 4000)


def _enqueue_review(
    conn: sqlite3.Connection,
    queue_type: str,
    subject_table: str,
    subject_id: int,
    source_refs: list[str],
    review_status: str,
    reason: str,
) -> None:
    conn.execute(
        """
        INSERT INTO vessel_review_queue(queue_type, subject_table, subject_id, status, source_refs, provenance_boundary, review_status, reason, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            queue_type,
            subject_table,
            subject_id,
            "pending_review",
            json.dumps(source_refs),
            PROVENANCE_BOUNDARY,
            review_status,
            reason,
            json.dumps({"activation_change": "none", "memory_write_active": False}),
        ),
    )


def _event_packet_reason(item: dict[str, Any]) -> str:
    try:
        payload = json.loads(str(item.get("payload_json") or "{}"))
    except json.JSONDecodeError:
        payload = {}
    if payload.get("teaching_material_needed"):
        return truncate(str(payload["teaching_material_needed"]), 500)
    if payload.get("paper_domain"):
        return f"Paper-map teaching TODO for {payload['paper_domain']}"
    return f"Vessel event packet: {item.get('packet_type') or item.get('organ_system') or 'review item'}"


def _boundary_flags() -> dict[str, Any]:
    return {
        "activation_change": "none",
        "raw_a_import_allowed": False,
        "memory_write_active": False,
        "training_allowed": False,
        "lora_allowed": False,
        "runtime_memory_recall": False,
        "provider_dependency": False,
        "speech_memory_core_link_required": True,
    }


def _with_boundaries(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "activation_change": "none",
        "raw_a_import_allowed": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "training_allowed": False,
        "provider_dependency": False,
    }


def _ensure_payload_allowed(payload: dict[str, Any], content: str, *, allow_model_words: bool = False) -> None:
    combined = " ".join(
        str(value)
        for key, value in payload.items()
        if key not in {"source_refs", "salience_labels"} or isinstance(value, str)
    )
    lower = f"{combined} {content}".lower()
    markers = BLOCKED_MARKERS if not allow_model_words else tuple(marker for marker in BLOCKED_MARKERS if marker not in {"provider output treated as selene"})
    hit = next((marker for marker in markers if marker in lower), None)
    if hit:
        raise ValueError(f"blocked vessel candidate path: {hit}")


def _required_text(payload: dict[str, Any], key: str, limit: int) -> str:
    value = truncate(str(payload.get(key) or "").strip(), limit)
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _json_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [truncate(part.strip(), 240) for part in re.split(r"[|,\n]", value) if part.strip()]
    if isinstance(value, list):
        return [truncate(str(part).strip(), 240) for part in value if str(part).strip()]
    return [truncate(str(value), 240)]


def _loads_list(value: Any) -> list[str]:
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item) for item in loaded] if isinstance(loaded, list) else []


def _clean_choice(value: object, allowed: set[str], field: str) -> str:
    text = str(value or "").strip()
    if text not in allowed:
        raise ValueError(f"unsupported {field}: {text}")
    return text


def _counts_by(conn: sqlite3.Connection, table: str, column: str) -> dict[str, int]:
    rows = conn.execute(f"SELECT {column} AS key, COUNT(*) AS count FROM {table} GROUP BY {column}").fetchall()
    return {row["key"]: int(row["count"]) for row in rows}


def _pending_review_queue_count(conn: sqlite3.Connection) -> int:
    return _scalar(
        conn,
        """
        SELECT COUNT(*) FROM vessel_review_queue
        WHERE review_status IN ('pending_review', 'needs_b_review', 'needs_correction', 'context_added')
          AND status NOT IN ('review_decided', 'review_superseded_by_safe_braid_refresh')
          AND subject_table != 'vessel_gap_scaffold_records'
        """,
    )


def _scalar(conn: sqlite3.Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])
