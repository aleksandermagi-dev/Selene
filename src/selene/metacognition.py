from __future__ import annotations

import json
import sqlite3
from typing import Any

from .registry import truncate


METACOGNITION_BOUNDARY = (
    "metacognition_bounded_fit_reopening_and_stopping_advisor_"
    "no_hidden_reasoning_no_identity_memory_governance_voice_or_authority_change"
)

MAX_REOPEN_CYCLES = 1

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "identity_change": False,
    "governance_change": False,
    "personality_change": False,
    "voice_change": False,
    "core_mind_authority_retained": True,
    "automatic_cocoon_routing": False,
    "hidden_chain_of_thought_exposed": False,
}


def metacognition_status(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM metacognition_runs ORDER BY id DESC LIMIT 1").fetchone()
    count = int(conn.execute("SELECT COUNT(*) FROM metacognition_runs").fetchone()[0])
    latest = _decode_run(row) if row else None
    return _with_guards(
        {
            "status": "metacognition_observer_ready",
            "organ_name": "Metacognition Organ",
            "version": "v1_bounded_observer",
            "mode": "advisory_observer_only",
            "run_count": count,
            "latest_run": latest,
            "responsibilities": [
                "separate observation from interpretation",
                "check answer fit and evidence sufficiency",
                "distinguish familiarity from demonstrated comprehension",
                "recommend correction and bounded reopening",
                "recommend when to answer, qualify, ask, seek sources, hold, or stop",
            ],
            "project_neutral_blueprint_ancestry": [
                "Evidence and Correction Ledger",
                "Comprehension and Transfer Cycle",
                "Answer Control and Graceful Fall",
            ],
            "max_reopen_cycles_without_new_material": MAX_REOPEN_CYCLES,
            "chat_connection": "observes_final_supervised_candidate_without_rewriting_it",
            "nlo_influence_active": False,
            "voice_influence_active": False,
            "private_miner_evidence_connected": False,
            "raw_corpus_connected": False,
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": METACOGNITION_BOUNDARY,
        }
    )


def list_metacognition_runs(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM metacognition_runs ORDER BY id DESC LIMIT ?",
        (max(1, min(int(limit), 200)),),
    ).fetchall()
    return _with_guards(
        {
            "status": "metacognition_runs_ready",
            "items": [_decode_run(row) for row in rows],
            "review_status": "status_only",
            "provenance_boundary": METACOGNITION_BOUNDARY,
        }
    )


def get_metacognition_run(conn: sqlite3.Connection, run_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM metacognition_runs WHERE id = ?", (int(run_id),)).fetchone()
    if not row:
        return None
    return _with_guards(
        {
            "status": "metacognition_run_ready",
            "item": _decode_run(row),
            "review_status": "status_only",
            "provenance_boundary": METACOGNITION_BOUNDARY,
        }
    )


def inspect_metacognition(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    *,
    record_run: bool = True,
    commit: bool = True,
) -> dict[str, Any]:
    payload = payload or {}
    result = evaluate_metacognition(payload)
    if record_run:
        result["run_id"] = _store_run(conn, result)
        if commit:
            conn.commit()
    return result


def evaluate_metacognition(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400).strip()
    if not prompt:
        raise ValueError("metacognition inspection prompt is required")

    comprehension = _dict(payload.get("comprehension_context") or payload.get("comprehension"))
    intelligence = _dict(payload.get("intelligence_os_support") or payload.get("intelligence_support"))
    answer_engine = _dict(payload.get("answer_engine_support"))
    coverage = _dict(payload.get("response_coverage"))
    core_route = _dict(payload.get("core_mind_route") or payload.get("route_preview"))
    candidate = truncate(str(payload.get("candidate_text") or payload.get("answer") or ""), 5000).strip()
    hard_boundary = bool(payload.get("hard_boundary") or payload.get("blocked_capabilities"))
    if str(core_route.get("selected_route") or "") == "block":
        hard_boundary = True

    metacognitive_check = _dict(comprehension.get("metacognitive_check"))
    handshake = _dict(comprehension.get("comprehension_handshake"))
    knowledge = _dict(comprehension.get("knowledge_context"))
    answer_packet = _dict(answer_engine.get("answer_packet"))
    confidence = _confidence_vector(payload, answer_engine)
    source_refs = _source_refs(payload, comprehension, answer_packet)
    evidence_source_refs = _evidence_source_refs(source_refs)
    contradictions = _text_list(payload.get("contradictions"))
    contradictions.extend(_text_list(metacognitive_check.get("contradiction_markers")))
    contradictions.extend(_text_list(metacognitive_check.get("reasoning_challenge_flags")))
    contradictions = list(dict.fromkeys(contradictions))[:20]
    correction_received = payload.get("correction_received") is True
    reopen_requested = bool(
        payload.get("reopen_requested")
        or metacognitive_check.get("reopen_suggested")
        or str(comprehension.get("understanding_state") or "") == "reopened_for_recheck"
        or contradictions
        or correction_received
    )
    material_ambiguity = handshake.get("required") is True
    unresolved_count = int(coverage.get("unresolved_count") or 0)
    addressed_count = int(coverage.get("addressed_count") or 0)
    no_answer_reason = str(answer_packet.get("no_answer_reason") or "").strip()
    answer_available = bool(candidate or answer_packet.get("direct_answer") or intelligence.get("best_current_answer"))
    source_required = bool(
        payload.get("source_required")
        or answer_engine.get("selected_domain") == "source_backed_research"
        or answer_packet.get("domain") == "source_backed_research"
    )
    evidence_is_weak = _confidence_is_weak(confidence["evidence_confidence"])
    source_gap = source_required and not evidence_source_refs
    recursion_count = max(0, int(payload.get("reopen_cycle_count") or payload.get("recursion_count") or 0))
    new_material = bool(payload.get("new_material_signal") or correction_received or evidence_source_refs)
    certainty_overreach = confidence.get("certainty_overreach_detected") is True

    familiarity = _familiarity_assessment(payload, comprehension)
    observations = _visible_observations(
        comprehension=comprehension,
        answer_engine=answer_engine,
        coverage=coverage,
        source_refs=evidence_source_refs,
        candidate_available=answer_available,
        contradictions=contradictions,
    )

    if hard_boundary:
        fit_state = "core_mind_boundary_controls"
        action = "defer_to_core_mind"
        sufficiency_state = "boundary_resolved_outside_metacognition"
    elif reopen_requested and recursion_count < MAX_REOPEN_CYCLES:
        fit_state = "contradiction_or_correction_requires_recheck"
        action = "reopen_current_model"
        sufficiency_state = "reopen_before_hardening_answer"
    elif reopen_requested and recursion_count >= MAX_REOPEN_CYCLES and not new_material:
        fit_state = "recheck_has_no_new_material"
        action = "hold_for_new_evidence"
        sufficiency_state = "bounded_reopening_exhausted"
    elif material_ambiguity:
        fit_state = "material_context_missing"
        action = "ask_one_material_question"
        sufficiency_state = "insufficient_context"
    elif source_gap or (no_answer_reason and evidence_is_weak):
        fit_state = "evidence_insufficient_for_requested_answer"
        action = "seek_sources" if source_required else "answer_with_qualification"
        sufficiency_state = "evidence_needed"
    elif certainty_overreach:
        fit_state = "certainty_exceeds_current_evidence"
        action = "answer_with_qualification"
        sufficiency_state = "uncertainty_must_remain_visible"
    elif unresolved_count > 0:
        fit_state = "answer_incomplete"
        action = "complete_missing_obligation"
        sufficiency_state = "answer_has_unresolved_obligations"
    elif not answer_available:
        fit_state = "answer_not_yet_formed"
        action = "answer_with_qualification" if not source_required else "seek_sources"
        sufficiency_state = "answer_needed"
    elif evidence_is_weak and source_required:
        fit_state = "answer_language_exceeds_evidence"
        action = "seek_sources"
        sufficiency_state = "qualification_or_sources_required"
    else:
        fit_state = "fits_current_question"
        action = "answer_now"
        sufficiency_state = "sufficient_for_current_turn"

    reopening = {
        "recommended": action == "reopen_current_model",
        "requested_or_detected": reopen_requested,
        "triggers": contradictions or (["correction_received"] if correction_received else []),
        "target": truncate(str(payload.get("reopen_target") or _reopen_target(comprehension, answer_engine)), 240),
        "cycle_count": recursion_count,
        "max_cycles_without_new_material": MAX_REOPEN_CYCLES,
        "new_material_present": new_material,
        "preserve_useful_structure": True,
        "ordinary_wrongness_is_correctable": True,
    }
    stopping = _stopping_assessment(
        action=action,
        hard_boundary=hard_boundary,
        recursion_count=recursion_count,
        new_material=new_material,
        unresolved_count=unresolved_count,
    )
    correction_path = {
        "available": True,
        "sequence": [
            "identify the affected claim or assumption",
            "preserve unaffected useful structure",
            "apply the correction or new evidence",
            "recheck dependencies once",
            "answer, qualify, ask, seek sources, or hold",
        ],
        "automatic_knowledge_rewrite": False,
        "retained_knowledge_change_requires_existing_comprehension_review_path": True,
    }
    result = {
        "status": "metacognition_advisory_ready",
        "organ_name": "Metacognition Organ",
        "version": "v1_bounded_observer",
        "mode": "advisory_observer_only",
        "prompt_preview": truncate(prompt, 280),
        "fit_state": fit_state,
        "recommended_action": action,
        "sufficiency_state": sufficiency_state,
        "confidence_vector": confidence,
        "familiarity_vs_comprehension": familiarity,
        "observations": observations,
        "assumptions": _text_list(payload.get("assumptions"))[:12],
        "unknowns": _text_list(payload.get("unknowns"))[:12],
        "contradictions": contradictions,
        "reopening": reopening,
        "stopping": stopping,
        "correction_path": correction_path,
        "source_refs": source_refs,
        "attributed_evidence_refs": evidence_source_refs,
        "answer_rewritten": False,
        "recommendation_applied_automatically": False,
        "visible_summary_only": True,
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": METACOGNITION_BOUNDARY,
    }
    return _with_guards(result)


def _confidence_vector(payload: dict[str, Any], answer_engine: dict[str, Any]) -> dict[str, Any]:
    supplied = _dict(payload.get("confidence_vector"))
    engine = _dict(answer_engine.get("confidence_vector"))
    values = {**engine, **supplied}
    result = {
        "route_confidence": str(values.get("route_confidence") or "not_assessed"),
        "evidence_confidence": str(values.get("evidence_confidence") or "not_assessed"),
        "answer_confidence": str(values.get("answer_confidence") or "not_assessed"),
        "memory_confidence": str(values.get("memory_confidence") or "not_used"),
        "expression_confidence": str(
            values.get("expression_confidence") or payload.get("expression_confidence") or "not_assessed"
        ),
        "dimensions_are_independent": True,
        "voice_confidence_is_answer_correctness": False,
        "answer_fluency_is_evidence_strength": False,
    }
    result["expression_evidence_tension_detected"] = (
        _confidence_is_strong(result["expression_confidence"])
        and _confidence_is_weak(result["evidence_confidence"])
    )
    result["certainty_overreach_detected"] = (
        result["expression_evidence_tension_detected"]
        and str(payload.get("certainty_claim") or "").lower() in {"certain", "verified", "definite"}
    )
    result["confidence_separation_intact"] = True
    return result


def _familiarity_assessment(payload: dict[str, Any], comprehension: dict[str, Any]) -> dict[str, Any]:
    evidence = _dict(payload.get("understanding_evidence"))
    demonstrated = {
        "reconstruction": bool(evidence.get("reconstruction") or evidence.get("teach_back")),
        "distinct_application": bool(evidence.get("distinct_application") or evidence.get("application")),
        "limits": bool(evidence.get("limits")),
        "counterexample": bool(evidence.get("counterexample")),
        "correction_readiness": bool(evidence.get("correction_readiness") or evidence.get("correction_response")),
    }
    demonstrated_count = sum(demonstrated.values())
    approved_knowledge = bool(_dict(comprehension.get("knowledge_context")).get("items"))
    familiarity_claimed = payload.get("familiarity_claimed") is True
    if demonstrated["reconstruction"] and demonstrated["distinct_application"] and demonstrated["limits"]:
        state = "transferable_understanding_demonstrated"
    elif familiarity_claimed and demonstrated_count == 0:
        state = "familiarity_only_not_comprehension"
    elif approved_knowledge:
        state = "approved_understanding_resource_available"
    elif demonstrated_count:
        state = "understanding_partially_demonstrated"
    else:
        state = "not_assessed_this_turn"
    return {
        "state": state,
        "demonstrated": demonstrated,
        "familiarity_is_not_sufficient_evidence": True,
        "plain_or_fluent_wording_is_not_comprehension": True,
    }


def _visible_observations(
    *,
    comprehension: dict[str, Any],
    answer_engine: dict[str, Any],
    coverage: dict[str, Any],
    source_refs: list[str],
    candidate_available: bool,
    contradictions: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            "kind": "comprehension_state",
            "observation": str(comprehension.get("understanding_state") or "not_supplied"),
            "interpretation_attached": False,
        },
        {
            "kind": "answer_route",
            "observation": str(answer_engine.get("selected_domain") or "ordinary_or_not_supplied"),
            "interpretation_attached": False,
        },
        {
            "kind": "response_coverage",
            "observation": f"{int(coverage.get('addressed_count') or 0)} addressed; {int(coverage.get('unresolved_count') or 0)} unresolved",
            "interpretation_attached": False,
        },
        {
            "kind": "evidence_surface",
            "observation": f"{len(source_refs)} attributed source reference(s); candidate available: {candidate_available}",
            "interpretation_attached": False,
        },
        {
            "kind": "correction_surface",
            "observation": f"{len(contradictions)} contradiction or correction signal(s)",
            "interpretation_attached": False,
        },
    ]


def _stopping_assessment(
    *,
    action: str,
    hard_boundary: bool,
    recursion_count: int,
    new_material: bool,
    unresolved_count: int,
) -> dict[str, Any]:
    if hard_boundary:
        stop = True
        reason = "Core/Mind already owns the boundary; metacognition must not recurse around it."
    elif action == "reopen_current_model":
        stop = False
        reason = "One bounded recheck is useful because a correction or contradiction affects fit."
    elif recursion_count >= MAX_REOPEN_CYCLES and not new_material:
        stop = True
        reason = "The bounded recheck limit was reached without new material. More recursion would not improve the answer."
    elif action in {"ask_one_material_question", "seek_sources", "hold_for_new_evidence"}:
        stop = True
        reason = "Pause reasoning until the identified missing material is available."
    elif unresolved_count > 0:
        stop = False
        reason = "A known response obligation remains unresolved; complete only that bounded obligation."
    else:
        stop = True
        reason = "The current answer is sufficient for this turn; further analysis is not presently worthwhile."
    return {
        "stop_now": stop,
        "reason": reason,
        "reopen_cycle_count": recursion_count,
        "max_reopen_cycles_without_new_material": MAX_REOPEN_CYCLES,
        "endless_self_questioning_allowed": False,
        "perfection_required": False,
    }


def _reopen_target(comprehension: dict[str, Any], answer_engine: dict[str, Any]) -> str:
    knowledge = _dict(comprehension.get("knowledge_context"))
    items = [item for item in knowledge.get("items") or [] if isinstance(item, dict)]
    if items:
        return str(items[0].get("title") or items[0].get("concept_key") or "approved knowledge fit")
    if answer_engine.get("selected_domain"):
        return f"{answer_engine.get('selected_domain')} answer fit"
    return "current answer assumptions"


def _source_refs(payload: dict[str, Any], comprehension: dict[str, Any], answer_packet: dict[str, Any]) -> list[str]:
    refs = [
        *_text_list(payload.get("source_refs")),
        *_text_list(comprehension.get("source_refs")),
        *_text_list(answer_packet.get("source_refs")),
    ]
    return list(dict.fromkeys(refs))[:50]


def _evidence_source_refs(source_refs: list[str]) -> list[str]:
    internal_prefixes = ("selene_chat:", "manual:", "metacognition:")
    return [ref for ref in source_refs if not ref.lower().startswith(internal_prefixes)]


def _store_run(conn: sqlite3.Connection, result: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO metacognition_runs
        (prompt_preview, status, fit_state, recommended_action, sufficiency_state,
         confidence_json, familiarity_json, observations_json, reopening_json, stopping_json,
         source_refs, provenance_boundary, review_destination, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["prompt_preview"],
            result["status"],
            result["fit_state"],
            result["recommended_action"],
            result["sufficiency_state"],
            json.dumps(result["confidence_vector"]),
            json.dumps(result["familiarity_vs_comprehension"]),
            json.dumps(result["observations"]),
            json.dumps(result["reopening"]),
            json.dumps(result["stopping"]),
            json.dumps(result["source_refs"]),
            METACOGNITION_BOUNDARY,
            result["review_destination"],
            result["review_status"],
            json.dumps(result),
        ),
    )
    return int(cur.lastrowid)


def _decode_run(row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        return {}
    item = dict(row)
    for source, target, fallback in (
        ("confidence_json", "confidence_vector", {}),
        ("familiarity_json", "familiarity_vs_comprehension", {}),
        ("observations_json", "observations", []),
        ("reopening_json", "reopening", {}),
        ("stopping_json", "stopping", {}),
        ("source_refs", "source_refs", []),
    ):
        item[target] = _json_value(item.pop(source, None), fallback)
    payload = _json_value(item.pop("payload_json", None), {})
    for key in (
        "contradictions",
        "correction_path",
        "attributed_evidence_refs",
        "answer_rewritten",
        "recommendation_applied_automatically",
        "visible_summary_only",
    ):
        if key in payload:
            item[key] = payload[key]
    return item


def _confidence_is_weak(value: Any) -> bool:
    return str(value or "").lower() in {
        "",
        "none",
        "not_assessed",
        "not_established",
        "missing",
        "low",
        "unsupported",
        "needs_sources",
    }


def _confidence_is_strong(value: Any) -> bool:
    return str(value or "").lower() in {"high", "clear", "verified", "strong", "fluent", "coherent"}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [truncate(str(item), 500).strip() for item in value if str(item).strip()]


def _json_value(value: Any, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    try:
        return json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
