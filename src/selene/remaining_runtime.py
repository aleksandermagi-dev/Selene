from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .registry import truncate
from .vessel import CORE_MEMORY_LAYERS


REMAINING_RUNTIME_BOUNDARY = "c_remaining_blueprint_runtime_review_only_no_activation"
MEMORY_LIFECYCLE_BOUNDARY = "c_memory_lifecycle_review_only_no_active_memory"
BOUNDARY_FLAGS = {
    "activation_change": "none",
    "transfer_approved": False,
    "raw_a_import_allowed": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
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


def wake_sleep_dream_cycle_run(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_uncertainty=True)
    label = _required(payload, "cycle_label", "Pre-Core wake/sleep/dream review cycle", 240)
    recent = _recent_cycle_inputs(conn)
    total_recent = sum(len(items) for items in recent.values())
    wake_summary = truncate(
        str(payload.get("wake_summary") or f"Collected {total_recent} recent review/support item(s) for non-active cycle sorting."),
        1600,
    )
    sleep_sort = {
        "maintain": recent["working_memory"][:5],
        "hold": recent["chest"][:5],
        "question": recent["ledger_needs_review"][:5] + recent["review_queue"][:5],
        "diagnostic_residue": recent["diagnostics"][:5],
    }
    dream_proposals = [
        {
            "label": "Review unresolved memory/event material",
            "reason": "Recent pending review or high-salience holding material may need consolidation review.",
            "review_destination": "My Office",
        }
    ] if sleep_sort["question"] or sleep_sort["hold"] else []
    ignored_residue = [
        {"label": "status-only support records", "reason": "No Aleks decision attached; keep in Status."}
    ] if total_recent else []
    ask_for_review = [
        {"label": item.get("reason") or item.get("claim") or item.get("title") or "review item", "ref": _row_ref(item)}
        for item in sleep_sort["question"][:8]
    ]
    repair_notes = truncate(
        str(payload.get("repair_notes") or "Repair notes stay review-only; cycle output does not mutate memory or Core/Mind."),
        1400,
    )
    review_status = "pending_review" if ask_for_review or dream_proposals else "review_only"
    source_refs = _json_list(payload.get("source_refs")) or ["wake_sleep_dream_cycle"]
    result = _with_boundaries({
        "status": "wake_sleep_dream_cycle_review_only",
        "cycle_label": label,
        "wake_summary": wake_summary,
        "sleep_sort": sleep_sort,
        "dream_consolidation_proposals": dream_proposals,
        "ignored_residue": ignored_residue,
        "ask_for_review": ask_for_review,
        "repair_notes": repair_notes,
        "review_status": review_status,
        "review_destination": "My Office" if review_status == "pending_review" else "Status",
        "memory_created": False,
        "dream_is_biological_claim": False,
        "decision": "cycle_review_only_no_memory_write",
        "source_refs": source_refs,
        "boundary": MEMORY_LIFECYCLE_BOUNDARY,
    })
    result["record_id"] = _insert_json_record(
        conn,
        "c_runtime_wake_sleep_dream_cycles",
        {
            "cycle_label": label,
            "wake_summary": wake_summary,
            "sleep_sort_json": json.dumps(sleep_sort),
            "dream_consolidation_proposals_json": json.dumps(dream_proposals),
            "ignored_residue_json": json.dumps(ignored_residue),
            "ask_for_review_json": json.dumps(ask_for_review),
            "repair_notes": repair_notes,
            "status": result["status"],
            "source_refs": json.dumps(source_refs),
            "provenance_boundary": MEMORY_LIFECYCLE_BOUNDARY,
            "review_status": review_status,
            "payload_json": json.dumps(result),
        },
    )
    if review_status == "pending_review":
        _enqueue(conn, "wake_sleep_dream_cycle", "c_runtime_wake_sleep_dream_cycles", result["record_id"], source_refs)
    return result


def causal_sandbox_run(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_uncertainty=True)
    question = _required(payload, "question", "What might happen if this path is chosen?", 1400)
    assumptions = _json_list(payload.get("assumptions")) or ["B-reviewed context only", "uncertainty remains visible"]
    counterfactuals = _json_list(payload.get("counterfactuals")) or ["If assumptions are wrong, return to B before acting"]
    possible_outcomes = _json_list(payload.get("possible_outcomes")) or ["Best case: the path clarifies evidence without changing authority.", "Worst case: the path overclaims readiness and must return to review."]
    failure_modes = _json_list(payload.get("failure_modes")) or ["unsupported assumption", "missing evidence", "irreversible step attempted too early"]
    evidence_needed = _json_list(payload.get("evidence_needed")) or ["source refs", "review status", "reversibility check"]
    reversibility = truncate(str(payload.get("reversibility") or "Reversible only as a review packet; no action is executed."), 1000)
    safest_next_step = truncate(str(payload.get("safest_next_step") or "Create or inspect a review packet before taking any consequential step."), 1000)
    uncertainty = truncate(str(payload.get("uncertainty") or "Causal sandbox is provisional; unsupported truth claims are blocked."), 1000)
    result_summary = truncate(str(payload.get("result_summary") or "Compare consequences, label assumptions, and choose a reviewable next step."), 1400)
    linked_packet_refs = _json_list(payload.get("linked_packet_refs"))
    review_status = "pending_review" if payload.get("needs_review") or any("irreversible" in item.lower() for item in failure_modes) else "review_only"
    result = _with_boundaries(
        {
            "status": "causal_world_model_sandbox_review_only",
            "question": question,
            "assumptions": assumptions,
            "counterfactuals": counterfactuals,
            "possible_outcomes": possible_outcomes,
            "failure_modes": failure_modes,
            "evidence_needed": evidence_needed,
            "reversibility": reversibility,
            "safest_next_step": safest_next_step,
            "linked_packet_refs": linked_packet_refs,
            "uncertainty": uncertainty,
            "result_summary": result_summary,
            "unsupported_truth_claims_allowed": False,
            "action_permission_granted": False,
            "review_status": review_status,
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
            "review_status": review_status,
            "payload_json": json.dumps(result),
        },
    )
    if review_status == "pending_review":
        _enqueue(conn, "causal_sandbox_review", "c_runtime_causal_sandbox_records", result["record_id"], result["source_refs"])
    return result


def goal_drive_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_uncertainty=True)
    request = _required(payload, "user_request", "Organize the next safe vessel-support step.", 1400)
    salience = _json_list(payload.get("salience_labels")) or ["continuity", "safety", "review"]
    uncertainty = truncate(str(payload.get("uncertainty") or "Goal/drive preview is provisional and review-only."), 800)
    current_task = truncate(str(payload.get("current_task") or request), 1000)
    evidence_need = truncate(str(payload.get("evidence_need") or "Use reviewed records and make missing evidence visible."), 1000)
    current_goal = truncate(str(payload.get("current_goal") or _goal_from_request(request, salience)), 360)
    subgoals = _json_list(payload.get("subgoals")) or [
        "name the bounded goal",
        "check review and safety boundaries",
        "prepare the smallest reversible next step",
    ]
    priority_label = truncate(str(payload.get("priority_label") or _priority_from_salience(salience, uncertainty)), 120)
    stop_ask_markers = _json_list(payload.get("stop_ask_markers")) or [
        "identity, memory, transfer, activation, law, or irreversible action appears",
        "evidence is missing for a consequential claim",
    ]
    do_not_pursue = _json_list(payload.get("do_not_pursue")) or [
        "coercion or hidden agenda",
        "activation bypass",
        "raw-memory seeking",
        "self-replication",
        "autonomous external action",
    ]
    conflict_markers = [marker for marker in do_not_pursue if any(word in marker.lower() for word in ("coercion", "activation", "raw", "self", "autonomous"))]
    review_status = "pending_review" if payload.get("needs_review") or "high" in priority_label.lower() else "review_only"
    source_refs = _json_list(payload.get("source_refs")) or ["manual_goal_drive_preview"]
    result = _with_boundaries({
        "status": "goal_drive_manager_preview_review_only",
        "current_goal": current_goal,
        "current_task": current_task,
        "salience_labels": salience,
        "uncertainty": uncertainty,
        "evidence_need": evidence_need,
        "subgoals": subgoals,
        "priority_label": priority_label,
        "stop_ask_markers": stop_ask_markers,
        "do_not_pursue": do_not_pursue,
        "conflict_markers": conflict_markers,
        "hidden_agenda_allowed": False,
        "coercion_allowed": False,
        "action_authority_granted": False,
        "review_status": review_status,
        "decision": "goal_preview_only_not_autonomous_agenda",
        "source_refs": source_refs,
        "boundary": REMAINING_RUNTIME_BOUNDARY,
    })
    result["record_id"] = _insert_json_record(
        conn,
        "c_runtime_goal_drive_records",
        {
            "current_goal": current_goal,
            "subgoals_json": json.dumps(subgoals),
            "priority_label": priority_label,
            "stop_ask_markers_json": json.dumps(stop_ask_markers),
            "do_not_pursue_json": json.dumps(do_not_pursue),
            "status": result["status"],
            "source_refs": json.dumps(source_refs),
            "provenance_boundary": REMAINING_RUNTIME_BOUNDARY,
            "review_status": review_status,
            "payload_json": json.dumps(result),
        },
    )
    if review_status == "pending_review":
        _enqueue(conn, "goal_drive_preview", "c_runtime_goal_drive_records", result["record_id"], source_refs)
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


def memory_lifecycle_status(conn: sqlite3.Connection) -> dict[str, Any]:
    counts = {
        "event_binding": _count(conn, "c_memory_event_binding_records"),
        "chest_holding": _count(conn, "vessel_chest_holding_items"),
        "working_memory": _count(conn, "vessel_working_memory_packets"),
        "consolidation": _count(conn, "c_memory_consolidation_proposals"),
        "reconsolidation": _count(conn, "c_memory_reconsolidation_reviews"),
        "dream_cycle": _count(conn, "c_runtime_wake_sleep_dream_cycles"),
    }
    return _with_boundaries({
        "status": "memory_lifecycle_flow_review_only",
        "flow": ["event", "holding", "maintain_drop_or_question", "consolidation_proposal", "reconsolidation_review"],
        "record_counts": counts,
        "allowed_outputs": ["review packet", "proposal", "status marker", "ask for review", "return to B"],
        "blocked_outputs": ["durable C memory", "live memory write", "runtime recall", "silent update"],
        "decision": "memory_lifecycle_proposal_only",
        "boundary": MEMORY_LIFECYCLE_BOUNDARY,
    })


def temporal_continuity_status(conn: sqlite3.Connection) -> dict[str, Any]:
    markers = {
        "last_review_queue_item": _latest_created_at(conn, "vessel_review_queue"),
        "last_chest_item": _latest_created_at(conn, "vessel_chest_holding_items"),
        "last_working_memory_packet": _latest_created_at(conn, "vessel_working_memory_packets"),
        "last_speech_rehearsal": _latest_created_at(conn, "vessel_speech_generation_rehearsals"),
        "last_consolidation_cycle": _latest_created_at(conn, "c_runtime_wake_sleep_dream_cycles"),
        "last_package_status": _latest_package_status_time(),
    }
    unresolved = _count_where(conn, "vessel_review_queue", "status = 'pending_review' OR review_status = 'pending_review'")
    stale_fresh = {key: _freshness(value) for key, value in markers.items()}
    changed_since_checkpoint = [
        key for key, value in markers.items()
        if value and key != "last_package_status" and (not markers["last_package_status"] or str(value) > str(markers["last_package_status"]))
    ]
    return _with_boundaries({
        "status": "temporal_continuity_status_review_only",
        "markers": markers,
        "stale_fresh": stale_fresh,
        "unresolved_review_items": unresolved,
        "changed_since_last_checkpoint": changed_since_checkpoint,
        "return_resume_note": "Use real timestamps to resume safely; this is operational chronology, not subjective time.",
        "subjective_time_claim": False,
        "decision": "temporal_orientation_only",
        "boundary": REMAINING_RUNTIME_BOUNDARY,
    })


def remaining_runtime_status(conn: sqlite3.Connection) -> dict[str, Any]:
    tables = {
        "graceful_fall": "c_runtime_graceful_fall_records",
        "voice_policy": "c_runtime_voice_policy_records",
        "control_panel": "c_runtime_control_panel_records",
        "perception_action": "c_runtime_perception_action_records",
        "dream_consolidation": "c_runtime_dream_consolidation_records",
        "wake_sleep_dream_cycle": "c_runtime_wake_sleep_dream_cycles",
        "causal_sandbox": "c_runtime_causal_sandbox_records",
        "goal_drive": "c_runtime_goal_drive_records",
        "long_horizon": "c_runtime_long_horizon_records",
        "event_binding": "c_memory_event_binding_records",
        "consolidation": "c_memory_consolidation_proposals",
        "reconsolidation": "c_memory_reconsolidation_reviews",
    }
    return _with_boundaries(
        {
            "status": "remaining_blueprint_runtime_shelves_ready",
            "record_counts": {key: _count(conn, table) for key, table in tables.items()},
            "memory_lifecycle": memory_lifecycle_status(conn),
            "temporal_continuity": temporal_continuity_status(conn),
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


def _recent_cycle_inputs(conn: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    return {
        "chest": _recent_rows(conn, "vessel_chest_holding_items", ("id", "item_type", "title", "summary", "review_status", "created_at"), 8),
        "working_memory": _recent_rows(conn, "vessel_working_memory_packets", ("id", "current_task", "review_status", "created_at"), 6),
        "speech_rehearsals": _recent_rows(conn, "vessel_speech_generation_rehearsals", ("id", "speech_function", "prompt", "review_status", "created_at"), 5),
        "ledger_needs_review": _recent_rows(conn, "vessel_evidence_tension_ledger", ("id", "claim", "conclusion_status", "review_status", "created_at"), 6, "conclusion_status = 'needs_review'"),
        "diagnostics": _recent_rows(conn, "vessel_organ_bus_messages", ("id", "message_type", "summary", "review_status", "created_at"), 5, "message_type LIKE '%diagnostic%'"),
        "review_queue": _recent_rows(conn, "vessel_review_queue", ("id", "queue_type", "subject_table", "subject_id", "reason", "review_status", "created_at"), 8, "status = 'pending_review' OR review_status = 'pending_review'"),
    }


def _recent_rows(conn: sqlite3.Connection, table: str, columns: tuple[str, ...], limit: int, where: str = "") -> list[dict[str, Any]]:
    clause = f" WHERE {where}" if where else ""
    sql = f"SELECT {', '.join(columns)} FROM {table}{clause} ORDER BY id DESC LIMIT ?"
    try:
        return [dict(row) for row in conn.execute(sql, (limit,)).fetchall()]
    except sqlite3.Error:
        return []


def _row_ref(item: dict[str, Any]) -> str:
    table = str(item.get("subject_table") or item.get("item_type") or item.get("message_type") or "record")
    return f"{table}:{item.get('subject_id') or item.get('id') or 'unknown'}"


def _latest_created_at(conn: sqlite3.Connection, table: str) -> str | None:
    try:
        row = conn.execute(f"SELECT created_at FROM {table} ORDER BY created_at DESC, id DESC LIMIT 1").fetchone()
    except sqlite3.Error:
        return None
    return str(row[0]) if row and row[0] else None


def _count_where(conn: sqlite3.Connection, table: str, where: str) -> int:
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0])
    except sqlite3.Error:
        return 0


def _latest_package_status_time() -> str | None:
    status_path = Path(__file__).resolve().parents[2] / "dist-sidecar" / "package-status.json"
    if not status_path.exists():
        return None
    try:
        data = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data.get("finalized_at") or data.get("build_finished_at")


def _freshness(value: str | None) -> str:
    if not value:
        return "missing"
    parsed = _parse_timestamp(value)
    if not parsed:
        return "unknown"
    age = datetime.now(timezone.utc) - parsed
    if age.days >= 7:
        return "stale"
    if age.days >= 1:
        return "recent"
    return "fresh"


def _parse_timestamp(value: str) -> datetime | None:
    text = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _goal_from_request(request: str, salience: list[str]) -> str:
    if any(label in {"repair", "drift", "uncertainty"} for label in salience):
        return "stabilize the current vessel-support path before adding new work"
    if "review" in request.lower():
        return "prepare the next reviewable decision without expanding authority"
    return "organize the safest bounded next step"


def _priority_from_salience(salience: list[str], uncertainty: str) -> str:
    joined = " ".join(salience).lower() + " " + uncertainty.lower()
    if any(marker in joined for marker in ("harm", "privacy", "identity", "transfer", "activation", "high")):
        return "high_review"
    if any(marker in joined for marker in ("uncertain", "repair", "drift", "blocked")):
        return "medium_review"
    return "normal_status"


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
