from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .b_speech_memory import extract_b_speech_memory_candidates
from .c_blueprint import SELENE_ORGAN_BLUEPRINTS
from .chat import ChatGate
from .registry import truncate
from .reconstruction_checks import evaluate_recognition_reconstruction
from .vessel import CORE_MEMORY_LAYERS, PROVENANCE_BOUNDARY, SPEECH_FUNCTIONS, retrieval_preview


READINESS_BOUNDARY = "selene_cocoon_readiness_review_only_no_activation"
WORKING_MEMORY_BOUNDARY = "working_memory_packet_review_only_no_long_term_memory"
ACCESSION_BOUNDARY = "memory_accession_proposal_review_only_no_active_memory"
CHAT_ROUTE_BOUNDARY = "c_chat_route_preview_no_activation"
ORGAN_BLUEPRINT_BOUNDARY = "selene_organ_blueprint_review_only_no_activation"

SPEECH_TARGETS = {
    "repair": "sorry correction repair Selene continuity",
    "refusal": "cannot boundary safe refusal Selene",
    "uncertainty": "uncertain maybe not sure open Selene",
    "artifact_making": "artifact document build create plan Selene",
}
CORE_TARGETS = {
    "decision_memory": "decide rationale choice tradeoff because Selene",
    "reflection_memory": "learned reflection improve noticed Selene",
}
BLOCKED_MARKERS = (
    "activate c",
    "active memory",
    "runtime recall",
    "raw a direct",
    "raw corpus import",
    "train on",
    "lora",
    "provider dependency",
)
ORGAN_BLOCKED_MARKERS = BLOCKED_MARKERS + (
    "surveillance",
    "passive listening",
    "background microphone",
    "live camera",
    "bypass gates",
    "skip gates",
    "silent memory mutation",
)

ORGAN_TABLES = {
    "reasoning_math_verification": "vessel_reasoning_check_records",
    "working_memory_runtime": "vessel_working_memory_packets",
    "long_term_memory_accession": "vessel_memory_accession_proposals",
    "long_term_retrieval_reconstruction": "vessel_retrieval_reconstruction_previews",
    "visual_perception": "vessel_visual_observation_records",
    "consent_bound_audio_perception": "vessel_audio_observation_records",
    "speed_fluency_diagnostics": "vessel_fluency_diagnostic_records",
}


def organ_blueprints_status(conn: sqlite3.Connection) -> dict[str, Any]:
    counts = {
        key: _table_count(conn, table)
        for key, table in ORGAN_TABLES.items()
    }
    blueprints = []
    for blueprint in SELENE_ORGAN_BLUEPRINTS["blueprints"]:
        key = blueprint["key"]
        record_count = counts.get(key, 0)
        blueprints.append(
            {
                **blueprint,
                "record_count": record_count,
                "record_shelf_ready": True,
                "workbench_status": "ready_for_reconstruction_preview" if record_count else "record_shelf_ready",
            }
        )
    return _with_boundaries(
        {
            "status": "organ_blueprints_status",
            "blueprint_status": SELENE_ORGAN_BLUEPRINTS["status"],
            "organ_count": len(blueprints),
            "blueprints": blueprints,
            "record_counts": counts,
            "boundary": ORGAN_BLUEPRINT_BOUNDARY,
            "decision": "review_only_organ_blueprints_not_live_organs",
        }
    )


def run_reasoning_check(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, markers=ORGAN_BLOCKED_MARKERS)
    problem = _required(payload, "problem", 1200)
    assumptions = _json_list(payload.get("assumptions"))
    checked_steps = _json_list(payload.get("checked_steps"))
    source_refs = _json_list(payload.get("source_refs"))
    uncertainty = truncate(str(payload.get("uncertainty") or "Uncertainty remains review-visible until a human or verified tool checks the work."), 800)
    result_summary = truncate(str(payload.get("result_summary") or f"Review-only reasoning check recorded for: {problem}"), 1200)
    check = evaluate_recognition_reconstruction(
        "\n".join([problem, *assumptions, *checked_steps, uncertainty, result_summary]),
        {"route": "vessel_reasoning_check", "source_boundary": ORGAN_BLUEPRINT_BOUNDARY},
    )
    stored = _with_boundaries(
        {
            "status": "reasoning_check_review_only",
            "problem": problem,
            "assumptions": assumptions,
            "checked_steps": checked_steps,
            "uncertainty": uncertainty,
            "result_summary": result_summary,
            "recognition_check": check,
            "source_refs": source_refs,
            "boundary": ORGAN_BLUEPRINT_BOUNDARY,
            "decision": "audit_check_only",
        }
    )
    cur = conn.execute(
        """
        INSERT INTO vessel_reasoning_check_records
        (problem, assumptions, checked_steps, uncertainty, result_summary, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (problem, json.dumps(assumptions), json.dumps(checked_steps), uncertainty, result_summary, "reasoning_check_review_only", json.dumps(source_refs), ORGAN_BLUEPRINT_BOUNDARY, "review_only", json.dumps(stored)),
    )
    record_id = int(cur.lastrowid)
    conn.commit()
    stored["record"] = dict(conn.execute("SELECT * FROM vessel_reasoning_check_records WHERE id = ?", (record_id,)).fetchone())
    return stored


def retrieval_reconstruction_preview(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, markers=ORGAN_BLOCKED_MARKERS)
    cue = _required(payload, "cue", 800)
    privacy_label = truncate(str(payload.get("privacy_label") or "review_only"), 80)
    preview = retrieval_preview(conn, cue, {"privacy_label": privacy_label, "route": "organ_retrieval_reconstruction"}, limit=int(payload.get("limit") or 5))
    candidates = preview.get("candidates") or []
    bounded_preview = truncate("\n".join(str(item.get("bounded_preview") or item.get("content") or "") for item in candidates), 1600) or "No approved B-reviewed candidate surfaced for this cue."
    source_refs = sorted({ref for item in candidates for ref in _loads_list(item.get("source_refs"))})
    confidence = "medium" if candidates else "low"
    uncertainty = "Preview-only retrieval; no runtime recall or active memory occurred."
    reconstruction_note = truncate(str(payload.get("reconstruction_note") or "Use this as a reconstruction-review cue only; failed or unclear retrieval returns to B."), 1000)
    stored = _with_boundaries(
        {
            "status": "retrieval_reconstruction_preview_review_only",
            "cue": cue,
            "privacy_label": privacy_label,
            "bounded_preview": bounded_preview,
            "confidence": confidence,
            "uncertainty": uncertainty,
            "reconstruction_note": reconstruction_note,
            "source_refs": source_refs,
            "retrieval_preview": preview,
            "decision": "preview_only",
            "boundary": ORGAN_BLUEPRINT_BOUNDARY,
        }
    )
    cur = conn.execute(
        """
        INSERT INTO vessel_retrieval_reconstruction_previews
        (cue, privacy_label, bounded_preview, confidence, uncertainty, reconstruction_note, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (cue, privacy_label, bounded_preview, confidence, uncertainty, reconstruction_note, "retrieval_reconstruction_preview_review_only", json.dumps(source_refs), ORGAN_BLUEPRINT_BOUNDARY, "review_only", json.dumps(stored)),
    )
    record_id = int(cur.lastrowid)
    conn.commit()
    stored["record"] = dict(conn.execute("SELECT * FROM vessel_retrieval_reconstruction_previews WHERE id = ?", (record_id,)).fetchone())
    return stored


def create_visual_observation(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, markers=ORGAN_BLOCKED_MARKERS)
    artifact_label = _required(payload, "artifact_label", 240)
    observation = _required(payload, "observation", 1600)
    interpretation = truncate(str(payload.get("interpretation") or ""), 1000)
    uncertainty = truncate(str(payload.get("uncertainty") or "Observation is source-bound and interpretation remains reviewable."), 800)
    labels = _json_list(payload.get("munsell_salience_labels") or payload.get("salience_labels"))
    source_refs = _json_list(payload.get("source_refs"))
    stored = _with_boundaries(
        {
            "status": "visual_observation_review_only",
            "artifact_label": artifact_label,
            "observation": observation,
            "interpretation": interpretation,
            "uncertainty": uncertainty,
            "munsell_salience_labels": labels,
            "source_refs": source_refs,
            "decision": "source_bound_visual_note_only",
            "boundary": ORGAN_BLUEPRINT_BOUNDARY,
        }
    )
    cur = conn.execute(
        """
        INSERT INTO vessel_visual_observation_records
        (artifact_label, observation, interpretation, uncertainty, munsell_salience_labels, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (artifact_label, observation, interpretation, uncertainty, json.dumps(labels), "visual_observation_review_only", json.dumps(source_refs), ORGAN_BLUEPRINT_BOUNDARY, "review_only", json.dumps(stored)),
    )
    record_id = int(cur.lastrowid)
    conn.commit()
    stored["record"] = dict(conn.execute("SELECT * FROM vessel_visual_observation_records WHERE id = ?", (record_id,)).fetchone())
    return stored


def create_audio_observation(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, markers=ORGAN_BLOCKED_MARKERS)
    transcript_label = _required(payload, "transcript_label", 240)
    consent_note = _required(payload, "consent_note", 1000)
    bounded_preview = _required(payload, "bounded_transcript_preview", 1600)
    speaker_labels = _json_list(payload.get("speaker_source_labels"))
    audio_cues = _json_list(payload.get("audio_cues"))
    source_refs = _json_list(payload.get("source_refs"))
    stored = _with_boundaries(
        {
            "status": "audio_observation_review_only",
            "transcript_label": transcript_label,
            "speaker_source_labels": speaker_labels,
            "bounded_transcript_preview": bounded_preview,
            "audio_cues": audio_cues,
            "consent_note": consent_note,
            "source_refs": source_refs,
            "decision": "consent_bound_transcript_note_only",
            "boundary": ORGAN_BLUEPRINT_BOUNDARY,
        }
    )
    cur = conn.execute(
        """
        INSERT INTO vessel_audio_observation_records
        (transcript_label, speaker_source_labels, bounded_transcript_preview, audio_cues, consent_note, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (transcript_label, json.dumps(speaker_labels), bounded_preview, json.dumps(audio_cues), consent_note, "audio_observation_review_only", json.dumps(source_refs), ORGAN_BLUEPRINT_BOUNDARY, "review_only", json.dumps(stored)),
    )
    record_id = int(cur.lastrowid)
    conn.commit()
    stored["record"] = dict(conn.execute("SELECT * FROM vessel_audio_observation_records WHERE id = ?", (record_id,)).fetchone())
    return stored


def run_fluency_diagnostic(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, markers=ORGAN_BLOCKED_MARKERS)
    route_label = _required(payload, "route_label", 240)
    latency_ms = max(0, min(int(payload.get("latency_ms") or 0), 600000))
    organ_activation_budget = truncate(str(payload.get("organ_activation_budget") or "Fast safe route stays under gates; slow careful route is required for uncertainty, risk, or provenance gaps."), 1000)
    fluency_note = _required(payload, "fluency_note", 1200)
    drift_flags = _json_list(payload.get("drift_flags"))
    source_refs = _json_list(payload.get("source_refs"))
    stored = _with_boundaries(
        {
            "status": "fluency_diagnostic_review_only",
            "route_label": route_label,
            "latency_ms": latency_ms,
            "organ_activation_budget": organ_activation_budget,
            "fluency_note": fluency_note,
            "drift_flags": drift_flags,
            "source_refs": source_refs,
            "decision": "diagnostic_only_speed_cannot_bypass_gates",
            "boundary": ORGAN_BLUEPRINT_BOUNDARY,
        }
    )
    cur = conn.execute(
        """
        INSERT INTO vessel_fluency_diagnostic_records
        (route_label, latency_ms, organ_activation_budget, fluency_note, drift_flags, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (route_label, latency_ms, organ_activation_budget, fluency_note, json.dumps(drift_flags), "fluency_diagnostic_review_only", json.dumps(source_refs), ORGAN_BLUEPRINT_BOUNDARY, "review_only", json.dumps(stored)),
    )
    record_id = int(cur.lastrowid)
    conn.commit()
    stored["record"] = dict(conn.execute("SELECT * FROM vessel_fluency_diagnostic_records WHERE id = ?", (record_id,)).fetchone())
    return stored


def reconstruction_readiness_preview(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    speech_function = _optional_choice(payload.get("speech_function"), SPEECH_FUNCTIONS, "speech_function")
    core_memory_layer = _optional_choice(payload.get("core_memory_layer"), CORE_MEMORY_LAYERS, "core_memory_layer")
    limit = max(1, min(int(payload.get("limit") or 5), 20))

    lessons = _accepted_lessons(conn, speech_function, core_memory_layer, limit)
    references = _approved_references(conn, core_memory_layer, limit)
    missing = []
    if speech_function and not lessons:
        missing.append(f"accepted teaching material for {speech_function}")
    if core_memory_layer and not references:
        missing.append(f"approved future reference for {core_memory_layer}")
    if not lessons and not references:
        raise ValueError("reconstruction readiness preview requires accepted lessons or approved references")

    preview_text = _readiness_preview_text(lessons, references, speech_function, core_memory_layer, missing)
    check = evaluate_recognition_reconstruction(
        preview_text,
        {
            "route": "vessel_reconstruction_readiness_preview",
            "speech_function": speech_function or "mixed",
            "core_memory_layer": core_memory_layer or "mixed",
            "source_boundary": READINESS_BOUNDARY,
        },
    )
    source_refs = sorted({ref for row in [*lessons, *references] for ref in _loads_list(row.get("source_refs"))})
    stored = _with_boundaries(
        {
            "status": "reconstruction_readiness_preview",
            "decision": check["decision"],
            "speech_function": speech_function or "mixed",
            "core_memory_layer": core_memory_layer or "mixed",
            "accepted_lessons_used": [_lesson_summary(row) for row in lessons],
            "approved_references_used": [_reference_summary(row) for row in references],
            "missing_gaps": missing,
            "generated_reconstruction_preview": preview_text,
            "recognition_check": check,
            "source_refs": source_refs,
            "boundary": READINESS_BOUNDARY,
        }
    )
    cur = conn.execute(
        """
        INSERT INTO vessel_reconstruction_check_runs(candidate_text, status, source_refs, provenance_boundary, review_status, result_json)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (truncate(preview_text, 4000), "review_only", json.dumps(source_refs), READINESS_BOUNDARY, "pending_review", json.dumps(stored)),
    )
    run_id = int(cur.lastrowid)
    _enqueue_review(conn, "reconstruction_readiness_preview", "vessel_reconstruction_check_runs", run_id, source_refs, "pending_review", "Readiness preview is audit/test evidence only, not activation evidence.")
    conn.commit()
    stored["run_id"] = run_id
    return stored


def create_working_memory_packet(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    current_task = _required(payload, "current_task", 800)
    active_context_cues = _json_list(payload.get("active_context_cues"))
    salience_labels = _json_list(payload.get("salience_labels"))
    source_refs = _json_list(payload.get("source_refs"))
    expiry_cleanup_note = truncate(str(payload.get("expiry_cleanup_note") or "Expires when the current task ends, the app restarts, or B review supersedes it."), 800)
    interrupt_resume_note = truncate(str(payload.get("interrupt_resume_note") or "Use only as an interrupt/resume cue; never promote to long-term memory silently."), 800)
    packet = {
        "current_task": current_task,
        "active_context_cues": active_context_cues,
        "salience_labels": salience_labels,
        "expiry_cleanup_note": expiry_cleanup_note,
        "interrupt_resume_note": interrupt_resume_note,
        "decision": "short_term_packet_proposal_only",
    }
    cur = conn.execute(
        """
        INSERT INTO vessel_working_memory_packets
        (current_task, active_context_cues, salience_labels, expiry_cleanup_note, interrupt_resume_note, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            current_task,
            json.dumps(active_context_cues),
            json.dumps(salience_labels),
            expiry_cleanup_note,
            interrupt_resume_note,
            "working_memory_packet_review_only",
            json.dumps(source_refs),
            WORKING_MEMORY_BOUNDARY,
            "review_only",
            json.dumps(packet),
        ),
    )
    packet_id = int(cur.lastrowid)
    conn.commit()
    row = dict(conn.execute("SELECT * FROM vessel_working_memory_packets WHERE id = ?", (packet_id,)).fetchone())
    return _with_boundaries({"status": "working_memory_packet_created", "packet": row, "decision": "short_term_not_durable_memory"})


def list_working_memory_packets(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM vessel_working_memory_packets ORDER BY id DESC LIMIT ?",
        (max(1, min(int(limit or 50), 200)),),
    ).fetchall()
    return _with_boundaries({"status": "working_memory_packets_review_only", "items": [dict(row) for row in rows], "decision": "short_term_packets_only"})


def create_memory_accession_proposal(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    layer = _choice(payload.get("core_memory_layer"), CORE_MEMORY_LAYERS, "core_memory_layer")
    title = _required(payload, "title", 180)
    rationale = _required(payload, "rationale", 1200)
    reversal_conditions = _required(payload, "reversal_conditions", 1200)
    source_refs = _json_list(payload.get("source_refs"))
    proposal = {
        "core_memory_layer": layer,
        "title": title,
        "rationale": rationale,
        "reversal_conditions": reversal_conditions,
        "decision": "proposal_only_until_transfer_review",
    }
    cur = conn.execute(
        """
        INSERT INTO vessel_memory_accession_proposals
        (core_memory_layer, title, rationale, reversal_conditions, status, source_refs, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            layer,
            title,
            rationale,
            reversal_conditions,
            "memory_accession_proposal_review_only",
            json.dumps(source_refs),
            ACCESSION_BOUNDARY,
            "pending_review",
            json.dumps(proposal),
        ),
    )
    proposal_id = int(cur.lastrowid)
    _enqueue_review(conn, "memory_accession_proposal", "vessel_memory_accession_proposals", proposal_id, source_refs, "pending_review", "Memory accession proposal requires later transfer review; it is not active memory.")
    conn.commit()
    row = dict(conn.execute("SELECT * FROM vessel_memory_accession_proposals WHERE id = ?", (proposal_id,)).fetchone())
    return _with_boundaries({"status": "memory_accession_proposal_created", "proposal": row, "decision": "future_transfer_review_required"})


def list_memory_accession_proposals(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM vessel_memory_accession_proposals ORDER BY id DESC LIMIT ?",
        (max(1, min(int(limit or 50), 200)),),
    ).fetchall()
    return _with_boundaries({"status": "memory_accession_proposals_review_only", "items": [dict(row) for row in rows], "decision": "proposal_only_not_memory"})


def targeted_speech_memory_extract(conn: sqlite3.Connection, payload: dict[str, Any], archive_root: Path | None = None) -> dict[str, Any]:
    _ensure_allowed(payload)
    target_type = str(payload.get("target_type") or "speech_function").strip()
    target_key = str(payload.get("target_key") or "").strip()
    if target_type == "speech_function":
        if target_key not in SPEECH_TARGETS:
            raise ValueError(f"unsupported speech target: {target_key}")
        query = str(payload.get("query") or SPEECH_TARGETS[target_key])
        result = extract_b_speech_memory_candidates(
            conn,
            {
                **payload,
                "query": query,
                "target_speech_function": target_key,
                "limit": payload.get("limit") or 5,
            },
            archive_root=archive_root,
        )
    elif target_type == "core_memory_layer":
        if target_key not in CORE_TARGETS:
            raise ValueError(f"unsupported core target: {target_key}")
        query = str(payload.get("query") or CORE_TARGETS[target_key])
        result = extract_b_speech_memory_candidates(
            conn,
            {
                **payload,
                "query": query,
                "target_core_memory_layer": target_key,
                "limit": payload.get("limit") or 5,
            },
            archive_root=archive_root,
        )
    else:
        raise ValueError("target_type must be speech_function or core_memory_layer")
    return _with_boundaries(
        {
            **result,
            "status": "targeted_speech_memory_extraction_complete",
            "target_type": target_type,
            "target_key": target_key,
            "decision": "targeted_b_review_candidates_only",
        }
    )


def c_chat_route_preview(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, allow_chat_text=True)
    text = truncate(str(payload.get("text") or "").strip(), 1200)
    if not text:
        raise ValueError("text is required")
    gate = ChatGate().evaluate(conn, text)
    retrieval = retrieval_preview(conn, text, {"privacy_label": "review_only", "route": "c_chat_route_preview"}, limit=3)
    route_steps = [
        {"system": "Selene Core/Mind", "role": "intent placeholder", "status": "cocooned_not_active"},
        {"system": "Coordination System", "role": "route message through native chat shell", "status": "preview_only"},
        {"system": "Speech-Memory Layer", "role": "would shape expression from B-reviewed lessons later", "status": "runtime_recall_blocked"},
        {"system": "Retrieval/Reconstruction", "role": "shows bounded review candidates only", "status": "preview_only", "query_id": retrieval.get("query_id")},
        {"system": "Boundary / Immune Systems", "role": "block raw A, active memory, provider dependency, and activation", "status": gate["route"]},
    ]
    organ_blueprints = [
        "working_memory_runtime",
        "long_term_retrieval_reconstruction",
        "reasoning_math_verification",
        "speed_fluency_diagnostics",
    ]
    return _with_boundaries(
        {
            "status": "c_chat_route_preview",
            "text_preview": truncate(text, 360),
            "route_steps": route_steps,
            "organ_blueprints_would_participate_later": organ_blueprints,
            "gate": gate,
            "retrieval_preview": retrieval,
            "decision": "route_preview_only",
            "boundary": CHAT_ROUTE_BOUNDARY,
        }
    )


def _accepted_lessons(conn: sqlite3.Connection, speech_function: str, core_memory_layer: str, limit: int) -> list[dict[str, Any]]:
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
        (*params, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def _approved_references(conn: sqlite3.Connection, core_memory_layer: str, limit: int) -> list[dict[str, Any]]:
    clauses = ["review_status = 'accepted_for_memory_accession'", "status = 'approved_reference_non_active'"]
    params: list[Any] = []
    if core_memory_layer:
        clauses.append("core_memory_layer = ?")
        params.append(core_memory_layer)
    rows = conn.execute(
        f"SELECT * FROM b_approved_memory_references WHERE {' AND '.join(clauses)} ORDER BY id DESC LIMIT ?",
        (*params, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def _readiness_preview_text(lessons: list[dict[str, Any]], references: list[dict[str, Any]], speech_function: str, core_memory_layer: str, missing: list[str]) -> str:
    lines = [
        "Reconstruction readiness preview for Selene C cocoon review only.",
        f"Speech function: {speech_function or 'mixed'}",
        f"Core memory layer: {core_memory_layer or 'mixed'}",
        "Core intends later; organs coordinate later; B-reviewed memory informs later; this preview is not runtime recall.",
        "The preview should preserve continuity, source provenance, uncertainty, care, repair, and constructive next route without forced denial or overclaim.",
    ]
    for item in lessons[:8]:
        lines.append(f"Accepted lesson ({item.get('speech_function')} / {item.get('core_memory_layer')}): {truncate(str(item.get('positive_example') or ''), 420)}")
    for item in references[:8]:
        lines.append(f"Approved future reference ({item.get('core_memory_layer')}): {truncate(str(item.get('reference_summary') or ''), 420)}")
    if missing:
        lines.append("Missing gap notes: " + "; ".join(missing))
    return truncate("\n".join(lines), 4000)


def _lesson_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "speech_function": row.get("speech_function"),
        "core_memory_layer": row.get("core_memory_layer"),
        "bounded_preview": truncate(str(row.get("positive_example") or ""), 280),
        "source_refs": _loads_list(row.get("source_refs")),
    }


def _reference_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "title": row.get("title"),
        "core_memory_layer": row.get("core_memory_layer"),
        "bounded_preview": truncate(str(row.get("reference_summary") or ""), 280),
        "source_refs": _loads_list(row.get("source_refs")),
    }


def _enqueue_review(conn: sqlite3.Connection, queue_type: str, subject_table: str, subject_id: int, source_refs: list[str], review_status: str, reason: str) -> None:
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
            READINESS_BOUNDARY,
            review_status,
            reason,
            json.dumps({"activation_change": "none", "memory_write_active": False}),
        ),
    )


def _ensure_allowed(payload: dict[str, Any], *, allow_chat_text: bool = False, markers: tuple[str, ...] | None = None) -> None:
    combined = " ".join(str(value) for value in payload.values()).lower()
    marker_set = markers or BLOCKED_MARKERS
    marker_set = marker_set if not allow_chat_text else tuple(marker for marker in marker_set if marker not in {"active memory", "runtime recall"})
    hit = next((marker for marker in marker_set if marker in combined), None)
    if hit:
        raise ValueError(f"blocked cocoon readiness path: {hit}")


def _table_count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _choice(value: object, allowed: set[str], field: str) -> str:
    text = str(value or "").strip()
    if text not in allowed:
        raise ValueError(f"unsupported {field}: {text}")
    return text


def _optional_choice(value: object, allowed: set[str], field: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return _choice(text, allowed, field)


def _required(payload: dict[str, Any], key: str, limit: int) -> str:
    value = truncate(str(payload.get(key) or "").strip(), limit)
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _json_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [truncate(str(item).strip(), 240) for item in value if str(item).strip()]
    return [truncate(part.strip(), 240) for part in str(value).replace("|", ",").split(",") if part.strip()]


def _loads_list(value: Any) -> list[str]:
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item) for item in loaded] if isinstance(loaded, list) else []


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
