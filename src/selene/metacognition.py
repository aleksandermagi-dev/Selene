from __future__ import annotations

import json
import sqlite3
from typing import Any

from .chat_persistence import compact_run_payload
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
            "status": "metacognition_feedback_advisor_ready",
            "organ_name": "Metacognition Organ",
            "version": "v5_associative_fit_observer",
            "mode": "bounded_feedback_advisor",
            "run_count": count,
            "latest_run": latest,
            "responsibilities": [
                "separate observation from interpretation",
                "check answer fit and evidence sufficiency",
                "distinguish familiarity from demonstrated comprehension",
                "recommend correction and bounded reopening",
                "inspect whether affective influence and response authority remain separate",
                "notice a threat-compressed option space and return an unmade choice to Core/Mind",
                "recommend when to answer, qualify, ask, seek sources, hold, or stop",
                "inspect a surfaced association without treating it as evidence or proof",
            ],
            "project_neutral_blueprint_ancestry": [
                "Evidence and Correction Ledger",
                "Comprehension and Transfer Cycle",
                "Answer Control and Graceful Fall",
                "Emotion and Response Agency Law",
            ],
            "max_reopen_cycles_without_new_material": MAX_REOPEN_CYCLES,
            "chat_connection": "advises_before_finalization_and_may_request_one_owner_bounded_recheck",
            "may_request_single_grounded_completion": True,
            "may_request_single_owner_recheck": True,
            "answer_owner_feedback_active": True,
            "feedback_writes_answer_content": False,
            "direct_answer_rewrite_authority": False,
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
    organ_coalition = _dict(payload.get("organ_coalition"))
    epistemic_answer_state = _dict(payload.get("epistemic_answer_state"))
    dual_horizon = _dict(payload.get("dual_horizon_context"))
    coverage = _dict(payload.get("response_coverage"))
    diagnostic_context = _dict(payload.get("diagnostic_context"))
    diagnostic_only = diagnostic_context.get("active") is True
    core_route = _dict(payload.get("core_mind_route") or payload.get("route_preview"))
    epistemic_revision = _dict(
        payload.get("epistemic_revision_plan")
        or payload.get("epistemic_revision")
        or comprehension.get("epistemic_revision")
    )
    candidate = truncate(str(payload.get("candidate_text") or payload.get("answer") or ""), 5000).strip()
    hard_boundary = bool(payload.get("hard_boundary") or payload.get("blocked_capabilities"))
    if str(core_route.get("selected_route") or "") == "block":
        hard_boundary = True

    metacognitive_check = _dict(comprehension.get("metacognitive_check"))
    handshake = _dict(comprehension.get("comprehension_handshake"))
    knowledge = _dict(comprehension.get("knowledge_context"))
    answer_packet = _dict(answer_engine.get("answer_packet"))
    hypothesis_attempt = _dict(intelligence.get("hypothesis_attempt"))
    bounded_hypothesis_offered = (
        hypothesis_attempt.get("offered") is True
        and hypothesis_attempt.get("selected_for_answer") is True
    )
    conversational_energy = _dict(payload.get("conversational_energy"))
    structural_discovery = _dict(payload.get("structural_discovery"))
    associative_intuition = _dict(payload.get("associative_intuition"))
    exploratory_reasoning = _dict(payload.get("exploratory_reasoning"))
    exploratory_response_kind = str(
        exploratory_reasoning.get("response_kind") or ""
    )
    unresolved_data_conflict_preserved = (
        exploratory_reasoning.get("selected_for_answer") is True
        and exploratory_response_kind == "data_conflict"
        and _dict(exploratory_reasoning.get("data_conflict")).get("present") is True
    )
    affect_expression = _dict(payload.get("affect_expression"))
    response_agency = _dict(
        payload.get("response_agency")
        or affect_expression.get("response_agency")
    )
    agency_choice_state = str(
        _dict(response_agency.get("response_choice")).get("state") or ""
    )
    agency_choice_pending = (
        agency_choice_state == "option_expansion_required_before_choice"
    )
    claim_evidence = _dict(
        payload.get("claim_evidence_packet")
        or answer_packet.get("claim_evidence_packet")
        or comprehension.get("claim_evidence_packet")
        or intelligence.get("claim_evidence_packet")
    )
    confidence = _confidence_vector(payload, answer_engine)
    source_refs = _source_refs(payload, comprehension, answer_packet)
    evidence_source_refs = _evidence_source_refs(source_refs)
    contradictions = _text_list(payload.get("contradictions"))
    contradictions.extend(_text_list(metacognitive_check.get("contradiction_markers")))
    contradictions.extend(_text_list(metacognitive_check.get("reasoning_challenge_flags")))
    contradictions.extend(_text_list(epistemic_revision.get("unresolved_contradictions")))
    contradictions.extend(
        f"claim-level disagreement: {item.get('claim_key')}"
        for item in claim_evidence.get("disagreements") or []
        if isinstance(item, dict) and str(item.get("claim_key") or "").strip()
    )
    contradictions = list(dict.fromkeys(contradictions))[:20]
    revision_handoff = _dict(epistemic_revision.get("metacognitive_handoff"))
    structured_revision = epistemic_revision.get("detected") is True
    correction_received = (
        payload.get("correction_received") is True
        or revision_handoff.get("correction_received") is True
    )
    structured_reopen = revision_handoff.get("reopen_requested") is True
    reopen_requested = bool(
        payload.get("reopen_requested")
        or metacognitive_check.get("reopen_suggested")
        or str(comprehension.get("understanding_state") or "") == "reopened_for_recheck"
        or contradictions
        or structured_reopen
        or (correction_received and not structured_revision)
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
    claim_handoff = _dict(claim_evidence.get("expression_handoff"))
    attributed_claims = _text_list(claim_handoff.get("attributed_source_statement_ids"))
    source_gap = source_required and (
        not evidence_source_refs
        or (
            bool(claim_evidence)
            and (
                not attributed_claims
                or claim_evidence.get("all_citations_trace_to_accepted_sources") is False
            )
        )
    )
    recursion_count = max(0, int(payload.get("reopen_cycle_count") or payload.get("recursion_count") or 0))
    new_material = bool(
        payload.get("new_material_signal")
        or correction_received
        or revision_handoff.get("new_material_present")
        or evidence_source_refs
    )
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
    elif agency_choice_pending:
        fit_state = "affective_influence_visible_response_choice_pending"
        action = "defer_to_core_mind"
        sufficiency_state = "restore_option_space_before_response_choice"
    elif unresolved_data_conflict_preserved and candidate:
        fit_state = "unresolved_data_conflict_preserved_without_false_resolution"
        action = "answer_now"
        sufficiency_state = "sufficient_to_report_current_conflict_and_deciding_evidence"
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
    elif bounded_hypothesis_offered:
        fit_state = "bounded_hypothesis_fits_visible_basis"
        action = "answer_as_open_hypothesis"
        sufficiency_state = "sufficient_for_bounded_attempt_not_established_fact"
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
        "update_kind": str(epistemic_revision.get("update_kind") or "none"),
        "affected_target": str(epistemic_revision.get("target") or ""),
        "validity": str(epistemic_revision.get("validity") or "unchanged"),
        "model_ancestry": epistemic_revision.get("model_ancestry") or {},
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
    completion_repair = _dict(payload.get("completion_repair"))
    completion_applied = completion_repair.get("accepted") is True
    feedback_handoff = _feedback_handoff(
        action,
        answer_engine=answer_engine,
        intelligence=intelligence,
        comprehension=comprehension,
        organ_coalition=organ_coalition,
        epistemic_answer_state=epistemic_answer_state,
        coverage=coverage,
        new_material=new_material,
        recursion_count=recursion_count,
        hard_boundary=hard_boundary,
    )
    result = {
        "status": "metacognition_advisory_ready",
        "organ_name": "Metacognition Organ",
        "version": "v5_associative_fit_observer",
        "mode": "bounded_feedback_advisor",
        "prompt_preview": truncate(prompt, 280),
        "fit_state": fit_state,
        "recommended_action": action,
        "sufficiency_state": sufficiency_state,
        "confidence_vector": confidence,
        "familiarity_vs_comprehension": familiarity,
        "observations": observations,
        "assumptions": _text_list(payload.get("assumptions"))[:12],
        "unknowns": _text_list(payload.get("unknowns"))[:12],
        "bounded_hypothesis": {
            "observed": bool(hypothesis_attempt),
            "offered": bounded_hypothesis_offered,
            "epistemic_class": str(hypothesis_attempt.get("epistemic_class") or ""),
            "falsifiable": hypothesis_attempt.get("falsifiable") is True,
            "ordinary_wrongness_is_failure": False,
            "expression_prescription_allowed": False,
        },
        "diagnostic_non_attribution": {
            **diagnostic_context,
            "active": diagnostic_only,
            "assessment_target": (
                "unfinished_module_or_test_harness"
                if diagnostic_only
                else "current_answer_fit"
            ),
            "result_is_selene_self_evidence": False,
            "dream_eligible": False if diagnostic_only else None,
            "memory_eligible": False if diagnostic_only else None,
        },
        "contradictions": contradictions,
        "reopening": reopening,
        "stopping": stopping,
        "correction_path": correction_path,
        "feedback_handoff": feedback_handoff,
        "organ_coalition": {
            "observed": bool(organ_coalition),
            "manifest_id": str(organ_coalition.get("manifest_id") or ""),
            "status": str(organ_coalition.get("status") or "not_available"),
            "selected_optional_count": int(
                organ_coalition.get("selected_optional_count") or 0
            ),
            "activation_budget": organ_coalition.get("activation_budget") or {},
            "selection_authority": False,
            "may_command_participants": False,
            "answer_rewrite_authority": False,
        },
        "dual_horizon_context": {
            "observed": bool(dual_horizon),
            "status": str(dual_horizon.get("status") or "not_available"),
            "version": str(dual_horizon.get("version") or ""),
            "active_selected_count": int(
                _dict(dual_horizon.get("active_horizon")).get("selected_count")
                or 0
            ),
            "approved_selected_count": int(
                _dict(
                    dual_horizon.get("approved_long_range_horizon")
                ).get("selected_count")
                or 0
            ),
            "grounding_uses_selected_packets_only": (
                dual_horizon.get("grounding_uses_selected_packets_only") is True
            ),
            "checkpoint_is_memory": False,
            "raw_corpus_loaded": False,
            "selection_authority": False,
            "answer_rewrite_authority": False,
        },
        "epistemic_revision": epistemic_revision,
        "claim_evidence_packet": claim_evidence,
        "claim_evidence_assessment": {
            "claim_count": int(claim_evidence.get("claim_count") or 0),
            "individual_claim_evaluation": bool(claim_evidence),
            "source_category_used_as_truth": False,
            "disagreement_count": len(claim_evidence.get("disagreements") or []),
            "missing_evidence_count": len(claim_evidence.get("missing_evidence") or []),
            "direct_answer_inference_and_uncertainty_separate": (
                claim_evidence.get("direct_answer_inference_and_uncertainty_separate") is True
            ),
        },
        "conversational_energy": conversational_energy,
        "conversational_energy_assessment": {
            "selected_act": str(conversational_energy.get("selected_act") or ""),
            "optional_addition_selected": conversational_energy.get("optional_addition_selected") is True,
            "question_by_default": False,
            "pressure_allowed": False,
            "collaborative_help_specific": (
                str(conversational_energy.get("selected_act") or "")
                == "ask_for_specific_collaborative_help"
                and bool(
                    (_dict(conversational_energy.get("help_contract"))).get(
                        "exact_missing_contribution_named"
                    )
                )
            ),
            "automatic_cocoon_routing": False,
        },
        "response_agency": response_agency,
        "response_agency_assessment": {
            "observed": bool(response_agency),
            "choice_state": agency_choice_state or "not_available",
            "threat_compression_state": str(
                _dict(response_agency.get("influence_assessment")).get(
                    "threat_compression_state"
                )
                or "not_available"
            ),
            "option_space_state": str(
                _dict(response_agency.get("option_space")).get("state")
                or "not_available"
            ),
            "affect_suppression_recommended": False,
            "forced_calm_recommended": False,
            "emotion_has_decision_authority": False,
            "core_mind_retains_response_authority": True,
            "hidden_inner_trace_requested": False,
        },
        "structural_discovery": structural_discovery,
        "structural_discovery_assessment": {
            "available": bool(structural_discovery),
            "ready": (
                structural_discovery.get("status")
                == "structural_discovery_packet_ready"
            ),
            "relation_label": str(
                (_dict(structural_discovery.get("classification"))).get("label")
                or ""
            ),
            "bridge_traceable": structural_discovery.get("bridge_traceable") is True,
            "hold_boundary_named": bool(structural_discovery.get("holds_where")),
            "break_boundary_named": bool(structural_discovery.get("breaks_where"))
            or str(structural_discovery.get("requested_relation_type") or "")
            == "equivalence",
            "analogy_used_as_proof": False,
            "logical_leap_testable": structural_discovery.get("hypothesis_testable")
            is True,
            "private_corpus_wording_used": False,
            "automatic_conclusion": False,
        },
        "associative_intuition": associative_intuition,
        "associative_intuition_assessment": {
            "observed": bool(associative_intuition),
            "is_organ": False,
            "connective_tissue_only": True,
            "selected_state": str(
                associative_intuition.get("selected_state")
                or "no_connection_noticed"
            ),
            "candidate_available": bool(
                associative_intuition.get("selected_candidate")
            ),
            "contribution_ready": (
                associative_intuition.get("contribution_ready") is True
            ),
            "association_used_as_evidence": False,
            "association_used_as_proof": False,
            "fit_check_remains_downstream": True,
            "automatic_retention": False,
            "automatic_dream_routing": False,
        },
        "exploratory_reasoning": exploratory_reasoning,
        "exploratory_reasoning_assessment": {
            "available": bool(exploratory_reasoning),
            "selected_for_answer": exploratory_reasoning.get("selected_for_answer") is True,
            "response_kind": exploratory_response_kind,
            "prediction_presented_as_fact": False,
            "hypothesis_presented_as_fact": False,
            "alternatives_false_equal_weighting": False,
            "reviewed_experience_universalized": False,
            "unresolved_data_conflict_preserved": unresolved_data_conflict_preserved,
            "data_conflict_is_identity_conflict": False,
            "ordinary_wrongness_is_failure": False,
            "automatic_test_execution": False,
        },
        "source_refs": source_refs,
        "attributed_evidence_refs": evidence_source_refs,
        "answer_rewritten": False,
        "bounded_completion_requested": completion_repair.get("requested_by_metacognition") is True,
        "bounded_completion_applied": completion_applied,
        "bounded_completion_count": int(completion_repair.get("count") or 0),
        "direct_answer_rewrite_authority": False,
        "recommendation_applied_automatically": completion_applied,
        "visible_summary_only": True,
        "review_destination": "Status",
        "review_status": (
            "diagnostic_only" if diagnostic_only else "status_only"
        ),
        "provenance_boundary": METACOGNITION_BOUNDARY,
    }
    return _with_guards(result)


def _feedback_handoff(
    action: str,
    *,
    answer_engine: dict[str, Any],
    intelligence: dict[str, Any],
    comprehension: dict[str, Any],
    organ_coalition: dict[str, Any],
    epistemic_answer_state: dict[str, Any],
    coverage: dict[str, Any],
    new_material: bool,
    recursion_count: int,
    hard_boundary: bool,
) -> dict[str, Any]:
    target = _unresolved_feedback_target(
        coverage,
        epistemic_answer_state,
    )
    target_id = str(target.get("obligation_id") or "")
    mapped_owner = _coalition_owner_for_obligation(organ_coalition, target_id)
    typed_owner = str(target.get("responsible_owner") or "")
    owner_mismatch = bool(
        typed_owner
        and mapped_owner
        and typed_owner != mapped_owner
    )
    missing_state = str(target.get("state") or "")
    if action == "defer_to_core_mind" or hard_boundary:
        owner = "core_mind"
    elif action == "seek_sources":
        owner = "source_evidence_owner"
    elif action in {
        "complete_missing_obligation",
        "answer_with_qualification",
    }:
        owner = typed_owner or mapped_owner or _owner_for_missing_state(
            missing_state,
            answer_engine=answer_engine,
            intelligence=intelligence,
            comprehension=comprehension,
        )
    elif action == "reopen_current_model":
        owner = (
            "answer_engine"
            if answer_engine.get("used") is True
            else "intelligence_os"
            if intelligence.get("used") is True
            else "comprehension_integration"
        )
    elif action == "ask_one_material_question":
        owner = "conversation_content_owner"
    else:
        owner = "none"
    cycle_requested = (
        action == "complete_missing_obligation"
        and bool(target_id)
        and owner not in {"", "none", "core_mind", "source_evidence_owner"}
    ) or (
        action == "reopen_current_model"
        and new_material
        and recursion_count < MAX_REOPEN_CYCLES
    )
    return {
        "status": (
            "metacognitive_owner_feedback_requested"
            if action not in {"answer_now", "hold_for_new_evidence"}
            else "metacognitive_owner_feedback_not_needed"
        ),
        "action": action,
        "responsible_owner": owner,
        "target_obligation_id": target_id,
        "target_requested_kind": str(target.get("requested_kind") or target.get("kind") or ""),
        "target_missing_state": missing_state,
        "target_missing_ground": truncate(str(target.get("missing_ground") or ""), 500),
        "owner_selected_from_coalition_map": bool(mapped_owner),
        "typed_answer_owner": typed_owner,
        "owner_reclassification_required": owner_mismatch,
        "owner_reclassified_from": mapped_owner if owner_mismatch else "",
        "owner_reclassified_to": typed_owner if owner_mismatch else "",
        "owner_reclassification_count": 1 if owner_mismatch and cycle_requested else 0,
        "owner_reclassification_limit": 1,
        "owner_reclassification_recursive": False,
        "exact_obligation_required": action == "complete_missing_obligation",
        "single_cycle_requested": cycle_requested,
        "single_cycle_limit": MAX_REOPEN_CYCLES,
        "same_material_reopen_allowed": False,
        "new_material_required_for_reopen": True,
        "content_generation_allowed": False,
        "answer_rewrite_authority": False,
        "core_mind_retains_release_authority": True,
        "nlo_and_voice_coordinate_expression": True,
        "automatic_cocoon_routing": False,
    }


def _unresolved_feedback_target(
    coverage: dict[str, Any],
    epistemic_answer_state: dict[str, Any],
) -> dict[str, Any]:
    addressed_ids = {
        str(item.get("obligation_id") or "")
        for item in coverage.get("items") or []
        if isinstance(item, dict)
        and item.get("addressed") is True
        and str(item.get("obligation_id") or "")
    }
    missing_parts = [
        item
        for item in epistemic_answer_state.get("missing_parts") or []
        if isinstance(item, dict)
        and str(item.get("obligation_id") or "")
        and str(item.get("obligation_id") or "") not in addressed_ids
    ]
    unresolved_ids = [
        str(item.get("obligation_id") or "")
        for item in coverage.get("items") or []
        if isinstance(item, dict)
        and item.get("addressed") is not True
        and str(item.get("obligation_id") or "")
    ]
    for obligation_id in unresolved_ids:
        matching = next(
            (
                item
                for item in missing_parts
                if str(item.get("obligation_id") or "") == obligation_id
            ),
            None,
        )
        if matching:
            coverage_item = next(
                (
                    item
                    for item in coverage.get("items") or []
                    if isinstance(item, dict)
                    and str(item.get("obligation_id") or "") == obligation_id
                ),
                {},
            )
            return {
                **coverage_item,
                **matching,
                "responsible_owner": str(
                    coverage_item.get("responsible_owner")
                    or matching.get("responsible_owner")
                    or ""
                ),
            }
        coverage_item = next(
            (
                item
                for item in coverage.get("items") or []
                if isinstance(item, dict)
                and str(item.get("obligation_id") or "") == obligation_id
            ),
            {},
        )
        return {
            "obligation_id": obligation_id,
            "requested_kind": str(coverage_item.get("kind") or ""),
            "answer_act": str(coverage_item.get("answer_act") or ""),
            "responsible_owner": str(coverage_item.get("responsible_owner") or ""),
            "answer_domain": str(coverage_item.get("answer_domain") or ""),
            "requested_response_functions": coverage_item.get("requested_response_functions") or [],
            "state": "missing_supported_basis",
            "missing_ground": "the requested response obligation remains unsupported",
        }
    return missing_parts[0] if missing_parts else {}


def _coalition_owner_for_obligation(
    organ_coalition: dict[str, Any], obligation_id: str
) -> str:
    if not obligation_id:
        return ""
    for item in organ_coalition.get("obligation_owner_map") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("obligation_id") or "") != obligation_id:
            continue
        owner = str(item.get("responsible_owner") or "")
        if owner and owner != "unassigned":
            return owner
    return ""


def _owner_for_missing_state(
    missing_state: str,
    *,
    answer_engine: dict[str, Any],
    intelligence: dict[str, Any],
    comprehension: dict[str, Any],
) -> str:
    if missing_state == "missing_taught_knowledge":
        return "comprehension_integration"
    if missing_state in {"missing_current_information", "missing_attributed_source"}:
        return "source_evidence_owner"
    if missing_state in {
        "missing_mechanism",
        "missing_discriminating_evidence",
        "conflicting_evidence",
        "missing_supported_basis",
    }:
        return "intelligence_os"
    if missing_state in {
        "missing_visible_context",
        "missing_decision_criteria",
        "missing_comparison_dimension",
        "genuinely_unknowable",
    }:
        return "conversation_content_owner"
    if answer_engine.get("used") is True:
        return "answer_engine"
    if intelligence.get("used") is True:
        return "intelligence_os"
    if str(comprehension.get("knowledge_response_seed") or "").strip():
        return "comprehension_integration"
    return "conversation_content_owner"


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
    associative_intuition = _dict(payload.get("associative_intuition"))
    refs = [
        *_text_list(payload.get("source_refs")),
        *_text_list(comprehension.get("source_refs")),
        *_text_list(answer_packet.get("source_refs")),
        *_text_list(associative_intuition.get("source_refs")),
    ]
    return list(dict.fromkeys(refs))[:50]


def _evidence_source_refs(source_refs: list[str]) -> list[str]:
    internal_prefixes = ("selene_chat:", "manual:", "metacognition:")
    return [ref for ref in source_refs if not ref.lower().startswith(internal_prefixes)]


def _store_run(conn: sqlite3.Connection, result: dict[str, Any]) -> int:
    column_owned_keys = {
        "prompt_preview",
        "status",
        "fit_state",
        "recommended_action",
        "sufficiency_state",
        "confidence_vector",
        "familiarity_vs_comprehension",
        "observations",
        "reopening",
        "stopping",
        "source_refs",
        "provenance_boundary",
        "review_destination",
        "review_status",
    }
    payload_remainder = compact_run_payload(
        result,
        schema_version="metacognition_run_v2_column_owned",
        column_owned_keys=column_owned_keys,
    )
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
            json.dumps(payload_remainder),
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
    payload = payload if isinstance(payload, dict) else {}
    payload.pop("storage_contract", None)
    return {**payload, **item}


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
