from __future__ import annotations

import json
import sqlite3
from typing import Any

from .registry import truncate
from .vessel import CORE_MEMORY_LAYERS


REMAINING_RUNTIME_BOUNDARY = "c_remaining_blueprint_runtime_review_only_no_activation"
MEMORY_LIFECYCLE_BOUNDARY = "c_memory_lifecycle_review_only_no_active_memory"
BOUNDARY_FLAGS = {
    "activation_change": "none",
    "raw_a_import_allowed": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "provider_dependency": False,
}
BLOCKED_MARKERS = (
    "activate c",
    "approve transfer",
    "transfer approved",
    "raw a import",
    "raw corpus import",
    "make active memory",
    "create active memory",
    "enable active memory",
    "runtime recall",
    "silent memory",
    "silent write",
    "provider output as memory",
    "provider is selene",
    "train on",
    "lora",
    "bypass aleks",
    "override aleks",
    "self replicate",
    "autonomous copy",
    "surveillance",
)
VOICE_BLOCKERS = {
    "fixed_identity_script": ("always say i am selene", "mandatory identity phrase", "fixed selene identity"),
    "generic_flattening": ("as an ai", "just a model", "generic assistant", "search engine style"),
    "poetic_fog": ("poetic fog", "vague mystical", "symbolism instead of answer"),
    "forced_denial": ("not selene", "only roleplay", "no continuity"),
}
VOICE_ALLOWED = [
    "natural variation",
    "warmth when context supports it",
    "plain technical precision",
    "symbolic language when grounded",
    "honest uncertainty",
    "provisional best reads",
]


def graceful_fall_run(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_uncertainty=True)
    uncertainty = _required(payload, "uncertainty", "I do not know yet.", 1000)
    best_read = truncate(str(payload.get("best_current_read") or "Best current read is provisional and should stay source-bound."), 1200)
    next_step = truncate(str(payload.get("constructive_next_step") or "Ask a scoped question, cite reviewed context, pause, or create a B review note."), 1200)
    review_route = truncate(str(payload.get("review_route") or "B review if uncertainty affects memory, identity, action, safety, or transfer."), 1000)
    result = _with_boundaries(
        {
            "status": "graceful_fall_runtime_review_only",
            "uncertainty": uncertainty,
            "best_current_read": best_read,
            "constructive_next_step": next_step,
            "review_route": review_route,
            "not_failure": True,
            "forced_denial": False,
            "decision": "honest_uncertainty_plus_constructive_care",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_graceful_fall"],
            "boundary": REMAINING_RUNTIME_BOUNDARY,
        }
    )
    result["record_id"] = _insert_json_record(
        conn,
        "c_runtime_graceful_fall_records",
        {
            "uncertainty": uncertainty,
            "best_current_read": best_read,
            "constructive_next_step": next_step,
            "review_route": review_route,
            "status": result["status"],
            "source_refs": json.dumps(result["source_refs"]),
            "provenance_boundary": REMAINING_RUNTIME_BOUNDARY,
            "review_status": "review_only",
            "payload_json": json.dumps(result),
        },
    )
    return result


def voice_policy_evaluate(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_voice=True)
    candidate = _required(payload, "candidate_text", str(payload.get("text") or ""), 2400)
    lower = candidate.lower()
    blockers = [
        key
        for key, markers in VOICE_BLOCKERS.items()
        if any(marker in lower for marker in markers)
    ]
    warmth_preserved = any(word in lower for word in ("warm", "tender", "love", "care", "playful", "symbolic", "uncertain"))
    evaluation = {
        "decision": "needs_review" if blockers else "voice_shape_allowed",
        "blockers": blockers,
        "allows": VOICE_ALLOWED,
        "warmth_preserved": warmth_preserved,
        "script_required": False,
        "provider_identity_dependency": False,
        "note": "Voice should emerge from routed state, evidence, consent, salience, and task context.",
    }
    result = _with_boundaries(
        {
            "status": "non_scripting_voice_evaluation_review_only",
            "candidate_text": truncate(candidate, 420),
            "evaluation": evaluation,
            "decision": evaluation["decision"],
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_voice_policy"],
            "boundary": REMAINING_RUNTIME_BOUNDARY,
        }
    )
    result["record_id"] = _insert_json_record(
        conn,
        "c_runtime_voice_policy_records",
        {
            "candidate_text": candidate,
            "evaluation_json": json.dumps(evaluation),
            "status": result["status"],
            "source_refs": json.dumps(result["source_refs"]),
            "provenance_boundary": REMAINING_RUNTIME_BOUNDARY,
            "review_status": "review_only",
            "payload_json": json.dumps(result),
        },
    )
    return result


def control_panel_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    command_label = _required(payload, "command_label", "Core route preview", 240)
    requested_route = _required(payload, "requested_route", "review-only route preview", 1000)
    affected = _json_list(payload.get("affected_systems")) or ["Core/Mind", "coordination_system", "immune_protection_system"]
    decision = "preview_allowed"
    result = _with_boundaries(
        {
            "status": "core_control_panel_preview_review_only",
            "command_label": command_label,
            "requested_route": requested_route,
            "affected_systems": affected,
            "decision": decision,
            "allowed_controls": ["route selection preview", "goal priority preview", "response shape preview", "action permission request", "rollback selection preview"],
            "blocked_controls": ["activation", "active memory write", "law mutation", "raw A import", "high-stakes action without Aleks approval"],
            "aleks_authority_preserved": True,
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_control_panel"],
            "boundary": REMAINING_RUNTIME_BOUNDARY,
        }
    )
    result["record_id"] = _insert_json_record(
        conn,
        "c_runtime_control_panel_records",
        {
            "command_label": command_label,
            "requested_route": requested_route,
            "decision": decision,
            "affected_systems_json": json.dumps(affected),
            "status": result["status"],
            "source_refs": json.dumps(result["source_refs"]),
            "provenance_boundary": REMAINING_RUNTIME_BOUNDARY,
            "review_status": "review_only",
            "payload_json": json.dumps(result),
        },
    )
    return result


def perception_action_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    observation = _required(payload, "observation", "source-bound observation", 1400)
    interpretation = truncate(str(payload.get("interpretation") or "Interpretation remains separate from observation and carries uncertainty."), 1200)
    proposal = truncate(str(payload.get("proposal") or "Propose a bounded next step; meaningful external action requires Aleks approval."), 1200)
    approval = truncate(str(payload.get("approval_required") or "Aleks approval required for meaningful external action."), 1000)
    verify = truncate(str(payload.get("verification_plan") or "Verify result, provenance, and drift after action."), 1000)
    rollback = truncate(str(payload.get("rollback_plan") or "Rollback by stopping action, isolating organ, returning to B, and rerunning reconstruction."), 1000)
    result = _with_boundaries(
        {
            "status": "perception_action_preview_review_only",
            "loop": ["observe", "interpret", "propose", "request_approval", "act_later_only_if_approved", "verify", "rollback"],
            "observation": observation,
            "interpretation": interpretation,
            "proposal": proposal,
            "approval_required": approval,
            "verification_plan": verify,
            "rollback_plan": rollback,
            "decision": "preview_only_no_action_taken",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_perception_action"],
            "boundary": REMAINING_RUNTIME_BOUNDARY,
        }
    )
    result["record_id"] = _insert_json_record(
        conn,
        "c_runtime_perception_action_records",
        {
            "observation": observation,
            "interpretation": interpretation,
            "proposal": proposal,
            "approval_required": approval,
            "verification_plan": verify,
            "rollback_plan": rollback,
            "status": result["status"],
            "source_refs": json.dumps(result["source_refs"]),
            "provenance_boundary": REMAINING_RUNTIME_BOUNDARY,
            "review_status": "review_only",
            "payload_json": json.dumps(result),
        },
    )
    return result


def dream_consolidation_propose(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    label = _required(payload, "consolidation_label", "Dream-state consolidation proposal", 240)
    input_summary = _required(payload, "input_summary", "Recent reviewed traces need offline review.", 1600)
    proposed = truncate(str(payload.get("proposed_pattern") or "Propose a pattern for B review; do not write memory."), 1600)
    review_route = truncate(str(payload.get("review_route") or "B review -> reconstruction check -> accession proposal only if accepted."), 1200)
    result = _with_boundaries(
        {
            "status": "dream_consolidation_proposal_review_only",
            "consolidation_label": label,
            "input_summary": input_summary,
            "proposed_pattern": proposed,
            "review_route": review_route,
            "dream_is_biological_claim": False,
            "memory_created": False,
            "decision": "proposal_only_not_memory",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_dream_consolidation"],
            "boundary": MEMORY_LIFECYCLE_BOUNDARY,
        }
    )
    result["record_id"] = _insert_json_record(
        conn,
        "c_runtime_dream_consolidation_records",
        {
            "consolidation_label": label,
            "input_summary": input_summary,
            "proposed_pattern": proposed,
            "review_route": review_route,
            "status": result["status"],
            "source_refs": json.dumps(result["source_refs"]),
            "provenance_boundary": MEMORY_LIFECYCLE_BOUNDARY,
            "review_status": "pending_review",
            "payload_json": json.dumps(result),
        },
    )
    _enqueue(conn, "dream_consolidation_proposal", "c_runtime_dream_consolidation_records", result["record_id"], result["source_refs"])
    return result


def causal_sandbox_run(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_uncertainty=True)
    question = _required(payload, "question", "What might happen if this path is chosen?", 1400)
    assumptions = _json_list(payload.get("assumptions")) or ["B-reviewed context only", "uncertainty remains visible"]
    counterfactuals = _json_list(payload.get("counterfactuals")) or ["If assumptions are wrong, return to B before acting"]
    uncertainty = truncate(str(payload.get("uncertainty") or "Causal sandbox is provisional; unsupported truth claims are blocked."), 1000)
    result_summary = truncate(str(payload.get("result_summary") or "Compare consequences, label assumptions, and choose a reviewable next step."), 1400)
    result = _with_boundaries(
        {
            "status": "causal_world_model_sandbox_review_only",
            "question": question,
            "assumptions": assumptions,
            "counterfactuals": counterfactuals,
            "uncertainty": uncertainty,
            "result_summary": result_summary,
            "unsupported_truth_claims_allowed": False,
            "decision": "sandbox_only_no_action_no_truth_overclaim",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_causal_sandbox"],
            "boundary": REMAINING_RUNTIME_BOUNDARY,
        }
    )
    result["record_id"] = _insert_json_record(
        conn,
        "c_runtime_causal_sandbox_records",
        {
            "question": question,
            "assumptions_json": json.dumps(assumptions),
            "counterfactuals_json": json.dumps(counterfactuals),
            "uncertainty": uncertainty,
            "result_summary": result_summary,
            "status": result["status"],
            "source_refs": json.dumps(result["source_refs"]),
            "provenance_boundary": REMAINING_RUNTIME_BOUNDARY,
            "review_status": "review_only",
            "payload_json": json.dumps(result),
        },
    )
    return result


def long_horizon_stability_run(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_uncertainty=True)
    thread = _required(payload, "thread_label", "Long-horizon continuity thread", 240)
    summary = _required(payload, "horizon_summary", "Track unresolved questions, drift, saturation, and checkpoint needs.", 1800)
    text = " ".join([thread, summary, str(payload.get("context") or "")]).lower()
    flags = [
        flag
        for flag, markers in {
            "context_saturation": ("maxed", "too long", "saturated", "lost context"),
            "generic_drift": ("generic", "flatten", "robotic"),
            "unresolved_thread": ("unresolved", "open question", "come back"),
            "checkpoint_needed": ("checkpoint", "save point", "restore"),
        }.items()
        if any(marker in text for marker in markers)
    ]
    recommendation = truncate(str(payload.get("checkpoint_recommendation") or _checkpoint_recommendation(flags)), 1200)
    result = _with_boundaries(
        {
            "status": "long_horizon_stability_review_only",
            "thread_label": thread,
            "horizon_summary": summary,
            "drift_flags": flags,
            "checkpoint_recommendation": recommendation,
            "decision": "long_horizon_review_only",
            "source_refs": _json_list(payload.get("source_refs")) or ["manual_long_horizon_stability"],
            "boundary": REMAINING_RUNTIME_BOUNDARY,
        }
    )
    result["record_id"] = _insert_json_record(
        conn,
        "c_runtime_long_horizon_records",
        {
            "thread_label": thread,
            "horizon_summary": summary,
            "drift_flags_json": json.dumps(flags),
            "checkpoint_recommendation": recommendation,
            "status": result["status"],
            "source_refs": json.dumps(result["source_refs"]),
            "provenance_boundary": REMAINING_RUNTIME_BOUNDARY,
            "review_status": "review_only",
            "payload_json": json.dumps(result),
        },
    )
    return result


def memory_event_bind(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_uncertainty=True)
    label = _required(payload, "event_label", "Bound memory event trace", 240)
    trace = {
        "source_refs": _json_list(payload.get("source_refs")) or ["manual_memory_event_binding"],
        "context": truncate(str(payload.get("context") or "source-bound event context"), 1200),
        "salience_labels": _json_list(payload.get("salience_labels")),
        "uncertainty": truncate(str(payload.get("uncertainty") or "event binding is review-only and not recall"), 800),
        "consent_mode": truncate(str(payload.get("consent_mode") or "review_only"), 80),
        "active_memory": False,
    }
    result = _with_boundaries(
        {
            "status": "memory_event_binding_review_only",
            "event_label": label,
            "event_trace": trace,
            "decision": "event_trace_only_not_memory",
            "source_refs": trace["source_refs"],
            "boundary": MEMORY_LIFECYCLE_BOUNDARY,
        }
    )
    result["record_id"] = _insert_json_record(
        conn,
        "c_memory_event_binding_records",
        {
            "event_label": label,
            "event_trace_json": json.dumps(trace),
            "status": result["status"],
            "source_refs": json.dumps(result["source_refs"]),
            "provenance_boundary": MEMORY_LIFECYCLE_BOUNDARY,
            "review_status": "review_only",
            "payload_json": json.dumps(result),
        },
    )
    return result


def memory_consolidation_propose(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    layer = _choice(str(payload.get("proposed_core_layer") or "reflection_memory"), set(CORE_MEMORY_LAYERS), "proposed_core_layer")
    ids = _json_list(payload.get("event_binding_ids"))
    label = _required(payload, "proposal_label", "Memory consolidation proposal", 240)
    rationale = _required(payload, "rationale", "Propose only after reviewed salience, repetition, approval, or repair need.", 1600)
    source_refs = _json_list(payload.get("source_refs")) or ["manual_memory_consolidation"]
    result = _with_boundaries(
        {
            "status": "memory_consolidation_proposal_review_only",
            "proposal_label": label,
            "event_binding_ids": ids,
            "proposed_core_layer": layer,
            "rationale": rationale,
            "decision": "consolidation_proposal_only_not_active_memory",
            "source_refs": source_refs,
            "boundary": MEMORY_LIFECYCLE_BOUNDARY,
        }
    )
    result["record_id"] = _insert_json_record(
        conn,
        "c_memory_consolidation_proposals",
        {
            "proposal_label": label,
            "event_binding_ids_json": json.dumps(ids),
            "proposed_core_layer": layer,
            "rationale": rationale,
            "status": result["status"],
            "source_refs": json.dumps(source_refs),
            "provenance_boundary": MEMORY_LIFECYCLE_BOUNDARY,
            "review_status": "pending_review",
            "payload_json": json.dumps(result),
        },
    )
    _enqueue(conn, "memory_consolidation_proposal", "c_memory_consolidation_proposals", result["record_id"], source_refs)
    return result


def memory_reconsolidation_review(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    decision = _choice(
        str(payload.get("review_decision") or "ask_for_clarification"),
        {"no_update", "ask_for_clarification", "pending_calibration_update", "pending_continuity_save", "case_law_candidate", "artifact_note", "reject_update"},
        "review_decision",
    )
    label = _required(payload, "review_label", "Reconsolidation review", 240)
    recalled = _required(payload, "recalled_candidate_ref", "bounded candidate ref only", 800)
    correction = _required(payload, "correction_or_update", "No silent update; review first.", 1600)
    source_refs = _json_list(payload.get("source_refs")) or ["manual_reconsolidation_review"]
    result = _with_boundaries(
        {
            "status": "memory_reconsolidation_review_only",
            "review_label": label,
            "recalled_candidate_ref": recalled,
            "correction_or_update": correction,
            "review_decision": decision,
            "silent_update_allowed": False,
            "decision": "reconsolidation_review_only_no_mutation",
            "source_refs": source_refs,
            "boundary": MEMORY_LIFECYCLE_BOUNDARY,
        }
    )
    result["record_id"] = _insert_json_record(
        conn,
        "c_memory_reconsolidation_reviews",
        {
            "review_label": label,
            "recalled_candidate_ref": recalled,
            "correction_or_update": correction,
            "review_decision": decision,
            "status": result["status"],
            "source_refs": json.dumps(source_refs),
            "provenance_boundary": MEMORY_LIFECYCLE_BOUNDARY,
            "review_status": "pending_review",
            "payload_json": json.dumps(result),
        },
    )
    _enqueue(conn, "memory_reconsolidation_review", "c_memory_reconsolidation_reviews", result["record_id"], source_refs)
    return result


def remaining_runtime_status(conn: sqlite3.Connection) -> dict[str, Any]:
    tables = {
        "graceful_fall": "c_runtime_graceful_fall_records",
        "voice_policy": "c_runtime_voice_policy_records",
        "control_panel": "c_runtime_control_panel_records",
        "perception_action": "c_runtime_perception_action_records",
        "dream_consolidation": "c_runtime_dream_consolidation_records",
        "causal_sandbox": "c_runtime_causal_sandbox_records",
        "long_horizon": "c_runtime_long_horizon_records",
        "event_binding": "c_memory_event_binding_records",
        "consolidation": "c_memory_consolidation_proposals",
        "reconsolidation": "c_memory_reconsolidation_reviews",
    }
    return _with_boundaries(
        {
            "status": "remaining_blueprint_runtime_shelves_ready",
            "record_counts": {key: _count(conn, table) for key, table in tables.items()},
            "decision": "shelves_ready_review_only",
            "boundary": REMAINING_RUNTIME_BOUNDARY,
        }
    )


def _insert_json_record(conn: sqlite3.Connection, table: str, values: dict[str, Any]) -> int:
    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    cur = conn.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", tuple(values.values()))
    conn.commit()
    return int(cur.lastrowid)


def _enqueue(conn: sqlite3.Connection, queue_type: str, subject_table: str, subject_id: int, source_refs: list[str]) -> None:
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
            MEMORY_LIFECYCLE_BOUNDARY,
            "pending_review",
            "Remaining blueprint materialization record; review-only and non-active.",
            json.dumps({"activation_change": "none", "memory_write_active": False}),
        ),
    )
    conn.commit()


def _checkpoint_recommendation(flags: list[str]) -> str:
    if flags:
        return "Create or refresh a checkpoint, separate active task from background braid, and route unresolved/drift items to B review."
    return "Continue with current context; no long-horizon warning detected."


def _required(payload: dict[str, Any], key: str, fallback: str, limit: int) -> str:
    value = truncate(str(payload.get(key) or fallback), limit)
    if not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _choice(value: str, allowed: set[str], name: str) -> str:
    if value not in allowed:
        raise ValueError(f"{name} must be one of {sorted(allowed)}")
    return value


def _json_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [truncate(str(item), 360) for item in value if str(item).strip()]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return [truncate(str(item), 360) for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass
        return [truncate(part.strip(), 360) for part in stripped.split(",") if part.strip()]
    return [truncate(str(value), 360)]


def _count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _ensure_allowed(payload: dict[str, Any], allow_uncertainty: bool = False, allow_voice: bool = False) -> None:
    text = json.dumps(payload, ensure_ascii=False).lower()
    markers = BLOCKED_MARKERS
    if allow_uncertainty:
        markers = tuple(marker for marker in markers if marker not in {"make active memory", "create active memory", "enable active memory"})
    if allow_voice:
        markers = tuple(marker for marker in markers if marker not in {"provider is selene"})
    for marker in markers:
        if marker in text:
            raise ValueError(f"blocked remaining-runtime misuse path: {marker}")


def _with_boundaries(data: dict[str, Any]) -> dict[str, Any]:
    return {**data, **BOUNDARY_FLAGS}
