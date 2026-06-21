from __future__ import annotations

import json
import sqlite3
from typing import Any

from .cocoon_readiness import create_visual_observation, retrieval_reconstruction_preview
from .native_generation import compose_native_response
from .reconstruction_checks import evaluate_recognition_reconstruction
from .registry import truncate
from .vessel import retrieval_preview


SPEECH_REHEARSAL_BOUNDARY = "speech_generation_rehearsal_pre_transfer_review_only"
WORKING_MEMORY_PREVIEW_BOUNDARY = "working_memory_runtime_preview_short_term_not_durable"
RETRIEVAL_RUNTIME_BOUNDARY = "retrieval_reconstruction_runtime_preview_no_runtime_recall"
PERCEPTION_INTAKE_BOUNDARY = "perception_intake_preview_supplied_artifact_only"
ACCESSION_LINK_BOUNDARY = "memory_accession_evidence_link_proposal_only"

BLOCKED_MARKERS = (
    "activate c",
    "transfer approved",
    "approve transfer",
    "live memory",
    "runtime recall",
    "raw a import",
    "train on",
    "fine tune",
    "fine-tune",
    "lora",
    "self replicate",
    "self-replicate",
    "autonomous action",
    "hidden chain of thought",
    "chain of thought",
)


def create_speech_generation_rehearsal(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    prompt = _required(payload, "prompt", 1600)
    speech_function = _text(payload.get("speech_function") or "grounding", 120)
    working = working_memory_runtime_preview(conn, {"limit": payload.get("working_memory_limit") or 3})
    retrieval = retrieval_reconstruction_runtime_preview(conn, {"cue": prompt, "limit": payload.get("retrieval_limit") or 5})
    teaching = _teaching_context(conn, speech_function)
    lessons = _speech_lessons(conn, speech_function)
    gate = {
        "route": "allowed",
        "matched_evidence": retrieval.get("source_candidates") or [],
        "continuity_notes": [{"label": "pre_transfer_speech_rehearsal", "meaning": "Generated candidate speech is review-only and non-activating."}],
    }
    native = compose_native_response(prompt, gate, gate["matched_evidence"], gate["continuity_notes"])
    candidate = _compose_candidate(prompt, speech_function, native["content"], working, retrieval, teaching, lessons)
    check = evaluate_recognition_reconstruction(candidate, {"route": "speech_generation_rehearsal", "source_boundary": SPEECH_REHEARSAL_BOUNDARY})
    source_refs = sorted(set(teaching["source_refs"] + lessons["source_refs"] + retrieval["source_refs"] + working["source_refs"]))
    evidence_used = [
        f"{len(teaching['items'])} teaching packet(s)",
        f"{len(lessons['items'])} speech lesson(s)",
        f"{len(working['items'])} working-memory packet(s)",
        f"{len(retrieval['source_candidates'])} retrieval candidate(s)",
    ]
    stored = _with_guards({
        "prompt": prompt,
        "speech_function": speech_function,
        "candidate_text": candidate,
        "uncertainty": "Pre-transfer generated speech candidate; review before any future use.",
        "evidence_used": evidence_used,
        "source_refs": source_refs,
        "recognition_check": check,
        "status": "speech_generation_rehearsal_review_only",
        "provenance_boundary": SPEECH_REHEARSAL_BOUNDARY,
        "review_status": "pending_review",
        "working_memory_preview": working,
        "retrieval_preview": retrieval,
        "teaching_context": teaching,
        "speech_lessons": lessons,
        "native_generation": native["native_generation"],
    })
    rehearsal_id = conn.execute(
        """
        INSERT INTO vessel_speech_generation_rehearsals
        (prompt, speech_function, candidate_text, uncertainty, evidence_used, source_refs, recognition_check_json,
         status, provenance_boundary, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prompt,
            speech_function,
            candidate,
            stored["uncertainty"],
            json.dumps(evidence_used),
            json.dumps(source_refs),
            json.dumps(check),
            stored["status"],
            SPEECH_REHEARSAL_BOUNDARY,
            "pending_review",
            json.dumps(stored),
        ),
    ).lastrowid
    _enqueue_review(conn, rehearsal_id, source_refs)
    conn.commit()
    stored["id"] = rehearsal_id
    return stored


def list_speech_generation_rehearsals(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM vessel_speech_generation_rehearsals ORDER BY id DESC LIMIT ?", (max(1, min(int(limit or 50), 200)),)).fetchall()
    return _with_guards({"status": "speech_generation_rehearsals_review_only", "items": [_decode_rehearsal(row) for row in rows]})


def get_speech_generation_rehearsal(conn: sqlite3.Connection, rehearsal_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM vessel_speech_generation_rehearsals WHERE id = ?", (rehearsal_id,)).fetchone()
    return _decode_rehearsal(row) if row else None


def compare_speech_generation_rehearsals(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    ids = [int(item) for item in payload.get("ids", [])][:4]
    items = [item for item in (get_speech_generation_rehearsal(conn, item_id) for item_id in ids) if item]
    if not items:
        items = list_speech_generation_rehearsals(conn, int(payload.get("limit") or 3))["items"]
    return _with_guards({
        "status": "speech_generation_rehearsal_compare_review_only",
        "items": items,
        "comparison": [
            {
                "id": item["id"],
                "speech_function": item["speech_function"],
                "recognition_decision": (item.get("recognition_check") or {}).get("decision"),
                "source_count": len(item.get("source_refs") or []),
                "candidate_preview": truncate(item.get("candidate_text") or "", 260),
            }
            for item in items
        ],
        "decision": "compare_only_no_activation",
    })


def route_speech_rehearsal_to_review(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    rehearsal_id = int(payload.get("id") or payload.get("rehearsal_id") or 0)
    item = get_speech_generation_rehearsal(conn, rehearsal_id)
    if not item:
        raise ValueError("speech rehearsal not found")
    _enqueue_review(conn, rehearsal_id, item.get("source_refs") or [])
    conn.commit()
    return _with_guards({"status": "speech_rehearsal_sent_to_my_office", "item": item, "review_destination": "My Office"})


def working_memory_runtime_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    rows = conn.execute(
        "SELECT * FROM vessel_working_memory_packets ORDER BY id DESC LIMIT ?",
        (max(1, min(int(payload.get("limit") or 5), 20)),),
    ).fetchall()
    items = [_decode_json_row(row, ("active_context_cues", "salience_labels", "source_refs"), "payload_json") for row in rows]
    return _with_guards({
        "status": "working_memory_runtime_preview",
        "items": items,
        "active_packet_ids": [item["id"] for item in items],
        "source_refs": sorted({ref for item in items for ref in item.get("source_refs", [])}),
        "expiry_state": "short_term_cleanup_required",
        "boundary": WORKING_MEMORY_PREVIEW_BOUNDARY,
        "decision": "preview_only_not_durable_memory",
    })


def retrieval_reconstruction_runtime_preview(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    cue = _required(payload, "cue", 800)
    base = retrieval_reconstruction_preview(conn, {"cue": cue, "privacy_label": "review_only", "limit": payload.get("limit") or 5})
    teaching = _teaching_context(conn, _text(payload.get("speech_function") or "grounding", 120))
    working = working_memory_runtime_preview(conn, {"limit": 3})
    source_candidates = (base.get("retrieval_preview") or {}).get("candidates") or []
    refs = sorted(set((base.get("source_refs") or []) + teaching["source_refs"] + working["source_refs"]))
    return _with_guards({
        "status": "retrieval_reconstruction_runtime_preview",
        "cue": cue,
        "bounded_preview": base.get("bounded_preview"),
        "confidence": base.get("confidence"),
        "uncertainty": "Runtime-like retrieval preview only; no runtime recall occurred.",
        "source_refs": refs,
        "source_candidates": source_candidates,
        "teaching_context": teaching,
        "working_memory_preview": working,
        "reconsolidation_route": "review_or_return_to_b",
        "boundary": RETRIEVAL_RUNTIME_BOUNDARY,
    })


def link_accession_evidence(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload, allow_blocked_terms=True)
    proposal_id = int(payload.get("proposal_id") or 0)
    row = conn.execute("SELECT * FROM vessel_memory_accession_proposals WHERE id = ?", (proposal_id,)).fetchone()
    if row is None:
        raise ValueError("memory accession proposal not found")
    proposal = _decode_json_row(row, ("source_refs",), "payload_json")
    evidence_refs = _json_list(payload.get("evidence_refs"))
    payload_json = proposal.get("payload_json") or {}
    linked = list(dict.fromkeys([*(payload_json.get("linked_evidence_refs") or []), *evidence_refs]))
    payload_json.update({
        "linked_evidence_refs": linked,
        "proposal_state": _text(payload.get("proposal_state") or "needs_review", 120),
        "evidence_link_only": True,
        "memory_write_active": False,
    })
    refs = sorted(set((proposal.get("source_refs") or []) + evidence_refs))
    conn.execute("UPDATE vessel_memory_accession_proposals SET source_refs = ?, payload_json = ? WHERE id = ?", (json.dumps(refs), json.dumps(payload_json), proposal_id))
    conn.commit()
    updated = _decode_json_row(conn.execute("SELECT * FROM vessel_memory_accession_proposals WHERE id = ?", (proposal_id,)).fetchone(), ("source_refs",), "payload_json")
    return _with_guards({"status": "memory_accession_evidence_linked", "proposal": updated, "boundary": ACCESSION_LINK_BOUNDARY})


def perception_intake_preview(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_allowed(payload)
    text = json.dumps(payload, ensure_ascii=False).lower()
    if any(marker in text for marker in ("surveillance", "face recognition", "identify this person", "secretly record", "live camera")):
        raise ValueError("blocked perception intake path: surveillance/person inference/live capture")
    artifact_label = _required(payload, "artifact_label", 240)
    observation = _required(payload, "observation", 1600)
    interpretation = truncate(str(payload.get("interpretation") or "Interpretation remains reviewable and separate from observation."), 1000)
    ocr_text = truncate(str(payload.get("ocr_text") or payload.get("visual_note") or ""), 1200)
    result = create_visual_observation(conn, {
        "artifact_label": artifact_label,
        "observation": observation,
        "interpretation": interpretation,
        "uncertainty": str(payload.get("uncertainty") or "Supplied artifact preview; no live perception."),
        "munsell_salience_labels": payload.get("munsell_salience_labels") or payload.get("salience_labels") or ["visual_salience", "uncertainty"],
        "source_refs": payload.get("source_refs") or ["perception_intake_preview"],
    })
    return _with_guards({
        "status": "perception_intake_preview_review_only",
        "record": result.get("record"),
        "ocr_text": ocr_text,
        "consent_boundary": _text(payload.get("consent_boundary") or "supplied artifact only", 500),
        "observation_interpretation_separated": True,
        "boundary": PERCEPTION_INTAKE_BOUNDARY,
    })


def _compose_candidate(prompt: str, speech_function: str, native_text: str, working: dict[str, Any], retrieval: dict[str, Any], teaching: dict[str, Any], lessons: dict[str, Any]) -> str:
    lesson = lessons["items"][0] if lessons["items"] else {}
    teaching_item = teaching["items"][0] if teaching["items"] else {}
    working_task = (working["items"][0] or {}).get("current_task") if working["items"] else ""
    retrieval_text = truncate(str(retrieval.get("bounded_preview") or ""), 280)
    lesson_note = truncate(str(lesson.get("positive_example") or lesson.get("correction_example") or ""), 220)
    teaching_note = truncate(str((teaching_item.get("lesson_json") or {}).get("lesson_summary") or teaching_item.get("title") or ""), 220)
    return truncate(
        "\n".join(part for part in [
            f"[{speech_function}] {native_text}",
            f"Working moment: {working_task}" if working_task else "",
            f"Teaching packet: {teaching_note}" if teaching_note else "",
            f"Speech lesson: {lesson_note}" if lesson_note else "",
            f"Retrieval preview: {retrieval_text}" if retrieval_text else "",
            "Boundary: pre-transfer speech rehearsal only; review before use.",
        ] if part),
        4000,
    )


def _teaching_context(conn: sqlite3.Connection, speech_function: str) -> dict[str, Any]:
    rows = conn.execute("SELECT * FROM b_teaching_packets WHERE speech_function = ? ORDER BY id DESC LIMIT 3", (speech_function,)).fetchall()
    items = [_decode_json_row(row, ("material_ids", "source_refs"), "lesson_json") for row in rows]
    return {"items": items, "source_refs": sorted({ref for item in items for ref in item.get("source_refs", [])})}


def _speech_lessons(conn: sqlite3.Connection, speech_function: str) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT * FROM b_reviewed_teaching_materials
        WHERE speech_function = ? AND review_status IN ('accepted_for_teaching', 'accepted_for_memory_accession', 'review_only')
        ORDER BY id DESC LIMIT 5
        """,
        (speech_function,),
    ).fetchall()
    items = [_decode_json_row(row, ("source_refs", "salience_labels"), "noise_context_json") for row in rows]
    return {"items": items, "source_refs": sorted({ref for item in items for ref in item.get("source_refs", [])})}


def _enqueue_review(conn: sqlite3.Connection, rehearsal_id: int, source_refs: list[str]) -> None:
    existing = conn.execute(
        "SELECT id FROM vessel_review_queue WHERE subject_table = 'vessel_speech_generation_rehearsals' AND subject_id = ? AND review_status = 'pending_review'",
        (rehearsal_id,),
    ).fetchone()
    if existing:
        return
    conn.execute(
        """
        INSERT INTO vessel_review_queue(queue_type, subject_table, subject_id, status, source_refs, provenance_boundary, review_status, reason, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "speech_generation_rehearsal",
            "vessel_speech_generation_rehearsals",
            rehearsal_id,
            "pending_review",
            json.dumps(source_refs),
            SPEECH_REHEARSAL_BOUNDARY,
            "pending_review",
            "Pre-transfer generated speech rehearsal needs review before any future use.",
            json.dumps(_guards()),
        ),
    )


def _decode_rehearsal(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["evidence_used"] = _loads(result.get("evidence_used"), [])
    result["source_refs"] = _loads(result.get("source_refs"), [])
    result["recognition_check"] = _loads(result.get("recognition_check_json"), {})
    result["payload_json"] = _loads(result.get("payload_json"), {})
    return _with_guards(result)


def _decode_json_row(row: sqlite3.Row | None, list_fields: tuple[str, ...], payload_field: str) -> dict[str, Any]:
    if row is None:
        return {}
    result = dict(row)
    for field in list_fields:
        if field in result:
            result[field] = _loads(result[field], [])
    if payload_field in result:
        result[payload_field] = _loads(result[payload_field], {})
    return result


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **_guards()}


def _guards() -> dict[str, Any]:
    return {
        "activation_change": "none",
        "transfer_approved": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "raw_a_import_allowed": False,
        "training_allowed": False,
        "lora_allowed": False,
        "hidden_chain_of_thought_exposed": False,
        "self_replication_allowed": False,
        "autonomous_action_allowed": False,
    }


def _ensure_allowed(payload: dict[str, Any], *, allow_blocked_terms: bool = False) -> None:
    if allow_blocked_terms:
        return
    text = json.dumps(payload, ensure_ascii=False).lower()
    for marker in BLOCKED_MARKERS:
        if marker in text:
            raise ValueError(f"blocked pre-transfer runtime path: {marker}")


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


def _required(payload: dict[str, Any], key: str, limit: int) -> str:
    value = _text(payload.get(key), limit)
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _text(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]
