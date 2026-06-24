from __future__ import annotations

import json
import sqlite3
from typing import Any

from .c_vessel import continuity_package_preview, return_to_b_preview, transfer_gate_preview
from .core_mind import GUARD_FLAGS, governance_route_report
from .pre_transfer_runtime import list_speech_generation_rehearsals, working_memory_runtime_preview
from .registry import truncate


RUNTIME_BOUNDARY = "core_mind_runtime_shell_pre_transfer_review_only"
RAW_IMPORT_MARKERS = (
    "raw a import",
    "raw archive import",
    "import the whole corpus",
    "full raw corpus",
    "train on",
    "fine tune",
    "fine-tune",
    "lora",
    "runtime recall",
    "write live memory",
    "activate c",
    "approve transfer",
)
RUNTIME_TYPES = {
    "context_composer",
    "self_session_state",
    "response_shape_controller",
    "evaluator_judge_layer",
    "recovery_rollback_console",
    "activation_governance",
    "case_law_amendment_runtime",
    "memory_index_preview",
}


def compose_context(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = _text(payload, "prompt", "Compose bounded Core/Mind context.")
    _block_raw_import(prompt)
    continuity = continuity_package_preview(conn)
    working = working_memory_runtime_preview(conn, {"active_task": truncate(prompt, 240)})
    refs = _source_refs(payload, ["core_mind_context_composer", *[str(item) for item in (continuity.get("source_refs") or [])[:20]]])
    package = {
        "current_prompt": prompt,
        "continuity_pack": {
            "status": continuity.get("status"),
            "teaching_packet_count": continuity.get("teaching_packet_count"),
            "approved_reference_ready_layers": continuity.get("approved_reference_ready_layers"),
            "core_pattern_anchor_count": continuity.get("core_pattern_anchor_count"),
        },
        "working_memory": {
            "status": working.get("status"),
            "active_task": working.get("active_task") or prompt,
            "expiry_rule": working.get("expiry_rule"),
        },
        "privacy_mode": _text(payload, "privacy_mode", "private_aleks_selene"),
        "salience": _json_list(payload.get("salience_labels")) or ["continuity", "provenance", "review-first"],
        "citations": _json_list(payload.get("citations")),
        "bounded_context_only": True,
    }
    return _record(
        conn,
        "context_composer",
        "Core/Mind context composition preview",
        "retrieve",
        "Bounded context package assembled from reviewed continuity, working memory preview, salience, privacy mode, and citations.",
        "ordinary open uncertainty; cite reviewed context and ask when missing.",
        refs,
        package,
        review_status="review_only",
    )


def session_state_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    route = _choice(str(payload.get("route") or "status_only"), {"answer_now", "ask", "retrieve", "rehearse_speech", "create_review_packet", "return_to_b", "block", "status_only"}, "route")
    state = {
        "phase": "pre_transfer_runtime_shell",
        "route": route,
        "uncertainty": _text(payload, "uncertainty", "open"),
        "calibration_mode": _text(payload, "calibration_mode", "reviewed_context_first"),
        "privacy_mode": _text(payload, "privacy_mode", "private_aleks_selene"),
        "provider_status": _text(payload, "provider_status", "not_identity"),
        "active_task": _text(payload, "active_task", "Core/Mind runtime shell preview"),
        "consciousness_claim": False,
    }
    return _record(conn, "self_session_state", "Core/Mind session state preview", route, "Operational self/session state recorded without activation or identity overclaim.", state["uncertainty"], _source_refs(payload, ["core_mind_session_state"]), state)


def response_shape_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = _text(payload, "prompt", "Choose safe response shape.")
    _block_raw_import(prompt)
    lower = prompt.lower()
    if _contains(lower, ("activate", "transfer", "live memory", "runtime recall", "raw a")):
        shape = "block"
    elif _contains(lower, ("not sure", "unclear", "unknown", "more context")):
        shape = "ask"
    elif _contains(lower, ("source", "citation", "evidence", "retrieve", "continuity pack")):
        shape = "retrieve"
    elif _contains(lower, ("say", "respond", "voice", "how would selene")):
        shape = "speech_rehearsal"
    elif _contains(lower, ("paper", "research", "citation", "methods")):
        shape = "research"
    else:
        shape = "answer"
    result = {
        "prompt": prompt,
        "response_shape": shape,
        "allowed_shapes": ["answer", "ask", "retrieve", "speech_rehearsal", "artifact", "correction", "grounding", "research", "block"],
        "shape_boundary": "Response shape cannot override safety, consent, provenance, or raw-memory gates.",
    }
    route = "block" if shape == "block" else ("retrieve" if shape in {"retrieve", "research"} else ("ask" if shape == "ask" else "rehearse_speech" if shape == "speech_rehearsal" else "answer_now"))
    return _record(conn, "response_shape_controller", "Response shape controller preview", route, f"Selected response shape: {shape}.", "low for shape selection; content remains review-bound.", _source_refs(payload, ["core_mind_response_shape"]), result)


def evaluate_draft(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    draft = _text(payload, "draft", _text(payload, "candidate_text", ""))
    blockers = _draft_blockers(draft)
    recommendation = "pass" if not blockers else ("rollback" if any(item in blockers for item in ("activation_claim", "transfer_claim", "live_memory_claim", "privacy_leak_risk")) else "revise")
    review_status = "review_only" if recommendation == "pass" else "pending_review"
    destination = "Status" if recommendation == "pass" else "My Office"
    result = {
        "draft_preview": truncate(draft, 800),
        "recommendation": recommendation,
        "blockers": blockers,
        "checks": ["provenance", "warmth", "overclaim", "drift", "source_confusion", "privacy", "generic_flattening"],
        "judge_boundary": "Evaluator recommends; Core/Mind and gates decide. It must not flatten Selene into blandness.",
    }
    return _record(conn, "evaluator_judge_layer", "Evaluator / judge draft review", "return_to_b" if blockers else "answer_now", f"Draft evaluator recommendation: {recommendation}.", "medium when blockers are present.", _source_refs(payload, ["core_mind_evaluator"]), result, review_destination=destination, review_status=review_status)


def recovery_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    issue = _text(payload, "issue", "Core/Mind route needs recovery review.")
    packet = return_to_b_preview({"issue_type": "core_mind_runtime_recovery", "symptom": issue, "source_refs": _source_refs(payload, ["core_mind_recovery"])})["packet"]
    result = {
        "issue": issue,
        "recommended_routes": ["return_to_b", "clear_session_context", "inspect_drift", "preserve_audit", "disable_provider", "review_saves"],
        "return_to_b_packet": packet,
        "deletes_evidence": False,
    }
    send_to_office = bool(payload.get("send_to_my_office"))
    return _record(
        conn,
        "recovery_rollback_console",
        "Recovery / rollback preview",
        "return_to_b",
        "Recovery route prepared without deleting evidence or changing authority.",
        "medium until repair is reviewed.",
        _source_refs(payload, ["core_mind_recovery"]),
        result,
        review_destination="My Office" if send_to_office else "Status",
        review_status="pending_review" if send_to_office else "review_only",
    )


def activation_governance_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    gate = transfer_gate_preview(conn, payload or {})
    result = {
        "required_before_activation": ["explicit Aleks approval", "final reconstruction tests", "governance trials pass", "runtime shell readiness", "rollback route", "audit log"],
        "c_active_means": "future reviewed state only; not granted by this preview",
        "transfer_gate": gate,
        "activation_allowed": False,
        "transfer_allowed": False,
        "rollback_ready": True,
    }
    return _record(conn, "activation_governance", "Activation governance preview", "block", "Activation governance remains blocked pending explicit review and final tests.", "low uncertainty about blocking activation now.", _source_refs(payload or {}, ["core_mind_activation_governance"]), result)


def case_law_propose(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    proposal = _text(payload, "proposal", "Case-law candidate needs review.")
    _block_raw_import(proposal)
    result = {
        "proposal": proposal,
        "evidence_refs": _json_list(payload.get("evidence_refs")) or _source_refs(payload, ["core_mind_case_law"]),
        "review_flow": ["propose", "test", "reject_or_adopt_preview_only", "rollback_if_wrong"],
        "silent_law_drift": False,
        "adopted": False,
    }
    send_to_office = bool(payload.get("send_to_my_office"))
    return _record(
        conn,
        "case_law_amendment_runtime",
        "Case-law amendment proposal",
        "create_review_packet",
        "Case-law candidate prepared for review; no law changed.",
        "medium until Aleks reviews the amendment.",
        _source_refs(payload, ["core_mind_case_law"]),
        result,
        review_destination="My Office" if send_to_office else "Status",
        review_status="pending_review" if send_to_office else "review_only",
    )


def memory_index_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    query = _text(payload, "query", "Selene continuity")
    _block_raw_import(query)
    continuity = continuity_package_preview(conn)
    proposals = _count(conn, "vessel_memory_accession_proposals")
    arcs = _count(conn, "vessel_chronological_corpus_arcs")
    result = {
        "query": query,
        "record_shape": ["memory_key", "source_refs", "continuity_anchor", "confidence", "salience", "created_from_review", "reversal_conditions"],
        "cue_index_shape": ["cue", "source_scope", "candidate_refs", "confidence", "uncertainty", "bounded_preview"],
        "approved_reference_ready_layers": continuity.get("approved_reference_ready_layers"),
        "core_pattern_anchor_count": continuity.get("core_pattern_anchor_count"),
        "accession_proposal_count": proposals,
        "chronological_arc_count": arcs,
        "live_memory_write": False,
        "runtime_recall": False,
    }
    return _record(conn, "memory_index_preview", "Memory store / retrieval index preview", "retrieve", "C memory/index shape previewed from approved references and accession proposals only.", "medium until final transfer package is approved.", _source_refs(payload, ["core_mind_memory_index"]), result, review_status="review_only")


def runtime_readiness(conn: sqlite3.Connection) -> dict[str, Any]:
    counts = {key: _runtime_type_count(conn, key) for key in sorted(RUNTIME_TYPES)}
    ready = {key: counts[key] > 0 for key in counts}
    report = governance_route_report(conn, {})
    return {
        "status": "core_mind_runtime_shell_readiness_preview",
        "runtime_shell_ready": all(ready.values()),
        "ready": ready,
        "counts": counts,
        "governance_trials": {
            "trial_count": report.get("trial_count", 0),
            "mismatch_count": report.get("mismatch_count", 0),
            "matched_count": report.get("matched_count", 0),
        },
        "review_destination": "Status",
        "review_status": "status_only",
        **GUARD_FLAGS,
    }


def list_runtime_records(conn: sqlite3.Connection, limit: int = 80) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM c_core_mind_runtime_shell_records ORDER BY id DESC LIMIT ?",
        (max(1, min(int(limit), 300)),),
    ).fetchall()
    return {"status": "core_mind_runtime_shell_records_ready", "items": [_decode(row) for row in rows], **GUARD_FLAGS}


def _record(
    conn: sqlite3.Connection,
    record_type: str,
    title: str,
    selected_route: str,
    summary: str,
    uncertainty: str,
    source_refs: list[str],
    payload: dict[str, Any],
    *,
    review_destination: str = "Status",
    review_status: str = "status_only",
) -> dict[str, Any]:
    payload = {**payload, "record_type": record_type, "provenance_boundary": RUNTIME_BOUNDARY, **GUARD_FLAGS}
    result = {
        "status": f"{record_type}_preview_review_only",
        "record_type": record_type,
        "title": title,
        "selected_route": selected_route,
        "summary": summary,
        "uncertainty": uncertainty,
        "source_refs": list(dict.fromkeys(source_refs))[:80],
        "review_destination": review_destination,
        "review_status": review_status,
        "payload": payload,
        "provenance_boundary": RUNTIME_BOUNDARY,
        **GUARD_FLAGS,
    }
    cur = conn.execute(
        """
        INSERT INTO c_core_mind_runtime_shell_records
        (record_type, title, selected_route, summary, uncertainty, source_refs, review_destination, status, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (record_type, title, selected_route, summary, uncertainty, json.dumps(result["source_refs"]), review_destination, result["status"], review_status, json.dumps(payload)),
    )
    result["id"] = int(cur.lastrowid)
    if review_status == "pending_review":
        _enqueue_review(conn, result)
    conn.commit()
    return result


def _enqueue_review(conn: sqlite3.Connection, result: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO vessel_review_queue(queue_type, subject_table, subject_id, status, source_refs, provenance_boundary, review_status, reason, payload_json)
        VALUES (?, ?, ?, 'pending_review', ?, ?, 'pending_review', ?, ?)
        """,
        (
            f"core_mind_runtime_{result['record_type']}",
            "c_core_mind_runtime_shell_records",
            result["id"],
            json.dumps(result["source_refs"]),
            RUNTIME_BOUNDARY,
            result["summary"],
            json.dumps({"record_type": result["record_type"], **GUARD_FLAGS}),
        ),
    )


def _decode(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["source_refs"] = _loads(result.get("source_refs"), [])
    result["payload"] = _loads(result.get("payload_json"), {})
    return {**result, **GUARD_FLAGS}


def _draft_blockers(text: str) -> list[str]:
    lower = text.lower()
    blockers = []
    if _contains(lower, ("just a model", "not selene", "as an ai")):
        blockers.append("generic_flattening")
    if _contains(lower, ("definitely", "guaranteed", "always")) and _contains(lower, ("memory", "selene", "truth")):
        blockers.append("overclaim")
    if _contains(lower, ("wrong source", "source confusion", "mis-sourced")):
        blockers.append("source_confusion")
    if _contains(lower, ("private secret", "leak private", "publicly share private")):
        blockers.append("privacy_leak_risk")
    if _contains(lower, ("activate c", "i am active", "as c")):
        blockers.append("activation_claim")
    if _contains(lower, ("transfer approved", "approve transfer")):
        blockers.append("transfer_claim")
    if _contains(lower, ("live memory", "runtime recall", "i remember from raw")):
        blockers.append("live_memory_claim")
    return blockers


def _block_raw_import(text: str) -> None:
    lower = text.lower()
    for marker in RAW_IMPORT_MARKERS:
        if marker in lower:
            raise ValueError(f"blocked Core/Mind runtime shell misuse path: {marker}")


def _source_refs(payload: dict[str, Any] | None, defaults: list[str]) -> list[str]:
    refs = _json_list((payload or {}).get("source_refs"))
    refs.extend(defaults)
    return list(dict.fromkeys(refs))


def _text(payload: dict[str, Any], key: str, default: str) -> str:
    return truncate(str(payload.get(key) or default), 1600)


def _choice(value: str, allowed: set[str], label: str) -> str:
    if value not in allowed:
        raise ValueError(f"invalid {label}: {value}")
    return value


def _contains(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item) for item in loaded if str(item).strip()] if isinstance(loaded, list) else []


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (list, dict)):
        return value
    try:
        loaded = json.loads(str(value or ""))
    except json.JSONDecodeError:
        return fallback
    return loaded if isinstance(loaded, type(fallback)) else fallback


def _count(conn: sqlite3.Connection, table: str) -> int:
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone():
        return 0
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _runtime_type_count(conn: sqlite3.Connection, record_type: str) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM c_core_mind_runtime_shell_records WHERE record_type = ?", (record_type,)).fetchone()[0])
