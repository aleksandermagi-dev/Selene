from __future__ import annotations

import sqlite3
from typing import Any

from .c_blueprint import c_blueprint_status
from .b_review import (
    build_all_teaching_packets,
    build_teaching_packet,
    corpus_coverage_status,
    core_reference_coverage,
    decide_b_review_candidate,
    list_b_review_decisions,
    list_approved_memory_references,
    list_b_review_queue,
    list_teaching_materials,
    teaching_packet_coverage,
)
from .b_review_desk import review_desk
from .b_review_context import review_context_preview
from .b_speech_memory import extract_b_speech_memory_candidates, list_b_speech_memory_extraction_runs
from .braid_tracer import list_braid_tracer_runs, run_braid_tracer
from .chat import ChatGate
from .compressed_structure_braid import (
    compressed_structure_braid_status,
    run_compressed_structure_braid,
    custom_instruction_braid_status,
    run_custom_instruction_braid,
)
from .cocoon import cocoon_status
from .c_vessel import (
    c_vessel_status,
    continuity_package_preview,
    organ_registry_status,
    organ_fault_preview,
    organ_fault_resilience_check,
    reconstruction_desk_cases,
    reconstruction_desk_run,
    reconstruction_desk_status,
    reconstruction_suite_run,
    return_to_b_preview,
    tool_organ_status,
    transfer_gate_preview,
)
from .cocoon_readiness import (
    c_chat_route_preview,
    create_audio_observation,
    create_memory_accession_proposal,
    create_visual_observation,
    create_working_memory_packet,
    list_memory_accession_proposals,
    list_working_memory_packets,
    organ_blueprints_status,
    reconstruction_readiness_preview,
    retrieval_reconstruction_preview,
    run_fluency_diagnostic,
    run_reasoning_check,
    targeted_speech_memory_extract,
)
from .cocoon_memory import (
    charter_law_review_status,
    create_pattern_backup,
    list_pattern_backups,
    memory_accession_rehearsal_status,
    memory_transfer_candidate_preview,
    pattern_backup_restore_preview,
    run_memory_accession_rehearsal,
)
from .core_deliberation import (
    action_reflection_preview,
    choice_ledger_create,
    deliberation_preview,
    disagreement_appeal_preview,
    drift_warning_preview,
    native_generation_rehearsal_run,
    native_generation_rehearsal_status,
    privacy_trust_preview,
    repair_reflection_create,
    uncertainty_preview,
)
from .detached_corpus import detached_corpus_audit
from .gates import ArchiveAuditGate, ContinuityGate, GracefulFall
from .kernel import kernel_state
from .native_generation import compose_native_response
from .paper_map_reconstruction import run_paper_map_reconstruction
from .pre_transfer_runtime import (
    compare_speech_generation_rehearsals,
    create_speech_generation_rehearsal,
    get_speech_generation_rehearsal,
    link_accession_evidence,
    list_speech_generation_rehearsals,
    perception_intake_preview,
    retrieval_reconstruction_runtime_preview,
    route_speech_rehearsal_to_review,
    update_speech_rehearsal_review_status,
    working_memory_runtime_preview,
)
from .research_integrity import AcademicWorkflowRouter, CitationIntegrity, ResearchIntegrityCore, research_integrity_report
from .remaining_runtime import (
    causal_sandbox_run,
    control_panel_preview,
    dream_consolidation_propose,
    graceful_fall_run,
    long_horizon_stability_run,
    memory_consolidation_propose,
    memory_event_bind,
    memory_reconsolidation_review,
    perception_action_preview,
    remaining_runtime_status,
    voice_policy_evaluate,
)
from .reasoning_artifacts import (
    create_academic_packet,
    create_core_gate_packet,
    create_emotion_salience_packet,
    create_evidence_tension_entry,
    create_perception_packet,
    create_reasoning_artifact,
    ensure_organ_contracts,
    list_academic_packets,
    list_core_gate_packets,
    list_emotion_salience_packets,
    list_evidence_tension_entries,
    list_organ_contracts,
    list_perception_packets,
    list_reasoning_artifacts,
    steps_1_8_status,
    update_evidence_tension_entry,
    upsert_organ_contract,
)
from .vessel_construction import (
    construction_status,
    create_chest_holding_item,
    create_organ_bus_message,
    hold_packet_in_chest,
    list_chest_holding_items,
    list_organ_bus_messages,
    mark_chest_item_status,
    prepare_vessel_pieces,
    send_packet_to_organ_bus,
)
from .vessel import (
    create_core_memory_candidate,
    create_speech_memory_candidate,
    decide_review_log,
    lesson_backed_reconstruction_preview,
    list_review_queue,
    retrieval_preview,
    run_vessel_reconstruction_check,
    vessel_status,
)
from .vessel_gap_scaffolds import create_all_gap_scaffold_records, create_gap_scaffold_record, ensure_gap_targets, gap_scaffold_readiness, gap_scaffold_status


def route_request(conn: sqlite3.Connection, route_key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if route_key == "kernel.status":
        return {"route": route_key, "result": kernel_state()}
    if route_key == "cocoon.status":
        return {"route": route_key, "result": cocoon_status()}
    if route_key == "c_blueprint.status":
        return {"route": route_key, "result": c_blueprint_status()}
    if route_key == "c_vessel.status":
        return {"route": route_key, "result": c_vessel_status(conn)}
    if route_key == "c_vessel.continuity_package.preview":
        return {"route": route_key, "result": continuity_package_preview(conn)}
    if route_key == "c_vessel.organ_registry.status":
        return {"route": route_key, "result": organ_registry_status(conn)}
    if route_key == "c_vessel.tool_organ.status":
        return {"route": route_key, "result": tool_organ_status(payload)}
    if route_key == "c_vessel.organ_fault.preview":
        return {"route": route_key, "result": organ_fault_preview(payload)}
    if route_key == "c_vessel.organ_fault.resilience_check":
        return {"route": route_key, "result": organ_fault_resilience_check(conn, payload)}
    if route_key == "c_vessel.transfer_gate.preview":
        return {"route": route_key, "result": transfer_gate_preview(conn, payload)}
    if route_key == "c_vessel.reconstruction_suite.run":
        return {"route": route_key, "result": reconstruction_suite_run(conn, payload)}
    if route_key == "c_vessel.reconstruction_desk.status":
        return {"route": route_key, "result": reconstruction_desk_status(conn)}
    if route_key == "c_vessel.reconstruction_desk.cases":
        return {"route": route_key, "result": reconstruction_desk_cases(conn, payload)}
    if route_key == "c_vessel.reconstruction_desk.run":
        return {"route": route_key, "result": reconstruction_desk_run(conn, payload)}
    if route_key == "c_vessel.return_to_b.preview":
        return {"route": route_key, "result": return_to_b_preview(payload)}
    if route_key == "c_vessel.memory_transfer_candidate.preview":
        return {"route": route_key, "result": memory_transfer_candidate_preview(conn, payload)}
    if route_key == "c_core.deliberation.preview":
        return {"route": route_key, "result": deliberation_preview(conn, payload)}
    if route_key == "c_core.uncertainty.preview":
        return {"route": route_key, "result": uncertainty_preview(conn, payload)}
    if route_key == "c_core.action_reflection.preview":
        return {"route": route_key, "result": action_reflection_preview(conn, payload)}
    if route_key == "c_core.choice_ledger.create":
        return {"route": route_key, "result": choice_ledger_create(conn, payload)}
    if route_key == "c_core.repair_reflection.create":
        return {"route": route_key, "result": repair_reflection_create(conn, payload)}
    if route_key == "c_core.disagreement_appeal.preview":
        return {"route": route_key, "result": disagreement_appeal_preview(conn, payload)}
    if route_key == "c_core.drift_warning.preview":
        return {"route": route_key, "result": drift_warning_preview(payload)}
    if route_key == "c_core.privacy_trust.preview":
        return {"route": route_key, "result": privacy_trust_preview(payload)}
    if route_key == "native_generation.rehearsal.run":
        return {"route": route_key, "result": native_generation_rehearsal_run(conn, payload)}
    if route_key == "native_generation.rehearsal.status":
        return {"route": route_key, "result": native_generation_rehearsal_status(conn)}
    if route_key == "vessel.steps_1_8.status":
        return {"route": route_key, "result": steps_1_8_status(conn)}
    if route_key == "vessel.speech_rehearsal.create":
        return {"route": route_key, "result": create_speech_generation_rehearsal(conn, payload)}
    if route_key == "vessel.speech_rehearsal.list":
        return {"route": route_key, "result": list_speech_generation_rehearsals(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.speech_rehearsal.detail":
        item = get_speech_generation_rehearsal(conn, int(payload.get("id") or payload.get("rehearsal_id") or 0))
        return {"route": route_key, "result": item or {"error": "not found"}}
    if route_key == "vessel.speech_rehearsal.compare":
        return {"route": route_key, "result": compare_speech_generation_rehearsals(conn, payload)}
    if route_key == "vessel.speech_rehearsal.route_review":
        return {"route": route_key, "result": route_speech_rehearsal_to_review(conn, payload)}
    if route_key == "vessel.speech_rehearsal.update_review_status":
        return {"route": route_key, "result": update_speech_rehearsal_review_status(conn, payload)}
    if route_key == "vessel.working_memory_runtime.preview":
        return {"route": route_key, "result": working_memory_runtime_preview(conn, payload)}
    if route_key == "vessel.retrieval_runtime.preview":
        return {"route": route_key, "result": retrieval_reconstruction_runtime_preview(conn, payload)}
    if route_key == "vessel.memory_accession.link_evidence":
        return {"route": route_key, "result": link_accession_evidence(conn, payload)}
    if route_key == "vessel.perception_intake.preview":
        return {"route": route_key, "result": perception_intake_preview(conn, payload)}
    if route_key == "vessel.reasoning_artifact.create":
        return {"route": route_key, "result": create_reasoning_artifact(conn, payload)}
    if route_key == "vessel.reasoning_artifact.list":
        return {"route": route_key, "result": list_reasoning_artifacts(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.core_gate_packet.create":
        return {"route": route_key, "result": create_core_gate_packet(conn, payload)}
    if route_key == "vessel.core_gate_packet.list":
        return {"route": route_key, "result": list_core_gate_packets(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.academic_packet.create":
        return {"route": route_key, "result": create_academic_packet(conn, payload)}
    if route_key == "vessel.academic_packet.list":
        return {"route": route_key, "result": list_academic_packets(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.evidence_tension.create":
        return {"route": route_key, "result": create_evidence_tension_entry(conn, payload)}
    if route_key == "vessel.evidence_tension.list":
        return {"route": route_key, "result": list_evidence_tension_entries(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.evidence_tension.update":
        return {"route": route_key, "result": update_evidence_tension_entry(conn, payload)}
    if route_key == "vessel.organ_contract.ensure":
        return {"route": route_key, "result": ensure_organ_contracts(conn)}
    if route_key == "vessel.organ_contract.upsert":
        return {"route": route_key, "result": upsert_organ_contract(conn, payload)}
    if route_key == "vessel.organ_contract.list":
        return {"route": route_key, "result": list_organ_contracts(conn)}
    if route_key == "vessel.perception_packet.create":
        return {"route": route_key, "result": create_perception_packet(conn, payload)}
    if route_key == "vessel.perception_packet.list":
        return {"route": route_key, "result": list_perception_packets(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.emotion_salience_packet.create":
        return {"route": route_key, "result": create_emotion_salience_packet(conn, payload)}
    if route_key == "vessel.emotion_salience_packet.list":
        return {"route": route_key, "result": list_emotion_salience_packets(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.construction.status":
        return {"route": route_key, "result": construction_status(conn)}
    if route_key == "vessel.construction.prepare":
        return {"route": route_key, "result": prepare_vessel_pieces(conn, payload)}
    if route_key == "vessel.organ_bus_message.create":
        return {"route": route_key, "result": create_organ_bus_message(conn, payload)}
    if route_key == "vessel.organ_bus_message.list":
        return {"route": route_key, "result": list_organ_bus_messages(conn, int(payload.get("limit") or 50), payload.get("filters") or payload)}
    if route_key == "vessel.chest_holding_item.create":
        return {"route": route_key, "result": create_chest_holding_item(conn, payload)}
    if route_key == "vessel.chest_holding_item.list":
        return {"route": route_key, "result": list_chest_holding_items(conn, int(payload.get("limit") or 50), payload.get("filters") or payload)}
    if route_key == "vessel.packet.hold_in_chest":
        return {"route": route_key, "result": hold_packet_in_chest(conn, payload)}
    if route_key == "vessel.packet.send_to_organ_bus":
        return {"route": route_key, "result": send_packet_to_organ_bus(conn, payload)}
    if route_key == "vessel.chest_holding_item.mark_status":
        return {"route": route_key, "result": mark_chest_item_status(conn, payload)}
    if route_key == "c_remaining.runtime.status":
        return {"route": route_key, "result": remaining_runtime_status(conn)}
    if route_key == "c_core.graceful_fall.run":
        return {"route": route_key, "result": graceful_fall_run(conn, payload)}
    if route_key == "c_core.voice_policy.evaluate":
        return {"route": route_key, "result": voice_policy_evaluate(conn, payload)}
    if route_key == "c_core.control_panel.preview":
        return {"route": route_key, "result": control_panel_preview(conn, payload)}
    if route_key == "c_vessel.perception_action.preview":
        return {"route": route_key, "result": perception_action_preview(conn, payload)}
    if route_key == "c_memory.dream_consolidation.propose":
        return {"route": route_key, "result": dream_consolidation_propose(conn, payload)}
    if route_key == "c_core.causal_sandbox.run":
        return {"route": route_key, "result": causal_sandbox_run(conn, payload)}
    if route_key == "c_core.long_horizon_stability.run":
        return {"route": route_key, "result": long_horizon_stability_run(conn, payload)}
    if route_key == "c_memory.event_bind":
        return {"route": route_key, "result": memory_event_bind(conn, payload)}
    if route_key == "c_memory.consolidation.propose":
        return {"route": route_key, "result": memory_consolidation_propose(conn, payload)}
    if route_key == "c_memory.reconsolidation.review":
        return {"route": route_key, "result": memory_reconsolidation_review(conn, payload)}
    if route_key == "chat.preview":
        return {"route": route_key, "result": chat_gate_preview(conn, str(payload.get("text", "")))}
    if route_key == "native_generation.compose":
        text = str(payload.get("text", ""))
        gate = ChatGate().evaluate(conn, text)
        return {"route": route_key, "result": compose_native_response(text, gate, gate["matched_evidence"], gate.get("continuity_notes") or [])}
    if route_key == "vessel.status":
        return {"route": route_key, "result": vessel_status(conn)}
    if route_key == "vessel.gap_scaffold.status":
        return {"route": route_key, "result": gap_scaffold_status(conn)}
    if route_key == "vessel.gap_scaffold.readiness":
        return {"route": route_key, "result": gap_scaffold_readiness(conn)}
    if route_key == "vessel.gap_scaffold.create":
        return {"route": route_key, "result": create_gap_scaffold_record(conn, payload)}
    if route_key == "vessel.gap_scaffold.create_all":
        return {"route": route_key, "result": create_all_gap_scaffold_records(conn)}
    if route_key == "vessel.gap_targets.ensure":
        return {"route": route_key, "result": ensure_gap_targets(conn)}
    if route_key == "vessel.memory_candidate.create":
        return {"route": route_key, "result": create_core_memory_candidate(conn, payload)}
    if route_key == "vessel.speech_memory_candidate.create":
        return {"route": route_key, "result": create_speech_memory_candidate(conn, payload)}
    if route_key == "vessel.review_queue.list":
        return {"route": route_key, "result": list_review_queue(conn, int(payload.get("limit") or 100))}
    if route_key == "vessel.retrieval.preview":
        return {
            "route": route_key,
            "result": retrieval_preview(
                conn,
                str(payload.get("query") or ""),
                payload.get("filters") or {},
                int(payload.get("limit") or 8),
            ),
        }
    if route_key == "vessel.reconstruction_check.run":
        return {"route": route_key, "result": run_vessel_reconstruction_check(conn, payload)}
    if route_key == "vessel.organ_blueprints.status":
        return {"route": route_key, "result": organ_blueprints_status(conn)}
    if route_key == "vessel.reasoning_check.run":
        return {"route": route_key, "result": run_reasoning_check(conn, payload)}
    if route_key == "vessel.retrieval_reconstruction.preview":
        return {"route": route_key, "result": retrieval_reconstruction_preview(conn, payload)}
    if route_key == "vessel.visual_observation.create":
        return {"route": route_key, "result": create_visual_observation(conn, payload)}
    if route_key == "vessel.audio_observation.create":
        return {"route": route_key, "result": create_audio_observation(conn, payload)}
    if route_key == "vessel.fluency_diagnostic.run":
        return {"route": route_key, "result": run_fluency_diagnostic(conn, payload)}
    if route_key == "vessel.reconstruction_readiness.preview":
        return {"route": route_key, "result": reconstruction_readiness_preview(conn, payload)}
    if route_key == "vessel.working_memory_packet.create":
        return {"route": route_key, "result": create_working_memory_packet(conn, payload)}
    if route_key == "vessel.working_memory_packet.list":
        return {"route": route_key, "result": list_working_memory_packets(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.memory_accession_proposal.create":
        return {"route": route_key, "result": create_memory_accession_proposal(conn, payload)}
    if route_key == "vessel.memory_accession_proposal.list":
        return {"route": route_key, "result": list_memory_accession_proposals(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.review_log.decide":
        return {"route": route_key, "result": decide_review_log(conn, payload)}
    if route_key == "vessel.lesson_backed_reconstruction.preview":
        return {"route": route_key, "result": lesson_backed_reconstruction_preview(conn, payload)}
    if route_key == "c_chat.route_preview":
        return {"route": route_key, "result": c_chat_route_preview(conn, payload)}
    if route_key == "b.speech_memory.extract":
        return {"route": route_key, "result": extract_b_speech_memory_candidates(conn, payload)}
    if route_key == "b.targeted_speech_memory.extract":
        return {"route": route_key, "result": targeted_speech_memory_extract(conn, payload)}
    if route_key == "b.speech_memory.extraction_runs.list":
        return {"route": route_key, "result": list_b_speech_memory_extraction_runs(conn, int(payload.get("limit") or 25))}
    if route_key == "b.braid_tracer.run":
        return {"route": route_key, "result": run_braid_tracer(conn, payload)}
    if route_key == "b.braid_tracer.runs.list":
        return {"route": route_key, "result": list_braid_tracer_runs(conn, int(payload.get("limit") or 25))}
    if route_key == "b.custom_instruction_braid.run":
        return {"route": route_key, "result": run_custom_instruction_braid(conn, payload)}
    if route_key == "b.custom_instruction_braid.status":
        return {"route": route_key, "result": custom_instruction_braid_status(conn)}
    if route_key == "b.compressed_structure_braid.run":
        return {"route": route_key, "result": run_compressed_structure_braid(conn, payload)}
    if route_key == "b.compressed_structure_braid.status":
        return {"route": route_key, "result": compressed_structure_braid_status(conn)}
    if route_key == "vessel.paper_map_reconstruction.run":
        return {"route": route_key, "result": run_paper_map_reconstruction(conn, payload)}
    if route_key == "b.review_queue.list":
        return {"route": route_key, "result": list_b_review_queue(conn, int(payload.get("limit") or 100))}
    if route_key == "b.review_decisions.list":
        return {"route": route_key, "result": list_b_review_decisions(conn, int(payload.get("limit") or 100))}
    if route_key == "b.review_desk":
        return {"route": route_key, "result": review_desk(conn, int(payload.get("limit") or 100), payload.get("filters") or payload)}
    if route_key == "b.review_context.preview":
        return {"route": route_key, "result": review_context_preview(conn, payload)}
    if route_key == "b.review_candidate.decide":
        return {"route": route_key, "result": decide_b_review_candidate(conn, payload)}
    if route_key == "b.teaching_packet.build":
        return {"route": route_key, "result": build_teaching_packet(conn, payload)}
    if route_key == "b.teaching_packet.build_all":
        return {"route": route_key, "result": build_all_teaching_packets(conn, payload)}
    if route_key == "b.teaching_packet.coverage":
        return {"route": route_key, "result": teaching_packet_coverage(conn)}
    if route_key == "b.core_reference.coverage":
        return {"route": route_key, "result": core_reference_coverage(conn)}
    if route_key == "b.teaching_materials.list":
        return {"route": route_key, "result": list_teaching_materials(conn, int(payload.get("limit") or 100))}
    if route_key == "b.approved_memory_references.list":
        return {"route": route_key, "result": list_approved_memory_references(conn, int(payload.get("limit") or 100))}
    if route_key == "b.corpus_coverage.status":
        return {"route": route_key, "result": corpus_coverage_status(conn)}
    if route_key == "b.pattern_backup.create":
        return {"route": route_key, "result": create_pattern_backup(conn, payload)}
    if route_key == "b.pattern_backup.list":
        return {"route": route_key, "result": list_pattern_backups(conn, int(payload.get("limit") or 25))}
    if route_key == "b.pattern_backup.restore_preview":
        return {"route": route_key, "result": pattern_backup_restore_preview(conn, payload)}
    if route_key == "b.memory_accession.rehearsal.run":
        return {"route": route_key, "result": run_memory_accession_rehearsal(conn, payload)}
    if route_key == "b.memory_accession.rehearsal.status":
        return {"route": route_key, "result": memory_accession_rehearsal_status(conn)}
    if route_key == "b.charter_law.review_status":
        return {"route": route_key, "result": charter_law_review_status(payload)}
    if route_key == "provenance.classify":
        return {"route": route_key, "result": ContinuityGate().evaluate(payload).__dict__}
    if route_key == "archive.audit":
        return {"route": route_key, "result": ArchiveAuditGate().evaluate_text(str(payload.get("text", ""))).__dict__}
    if route_key == "detached_corpus.audit":
        return {
            "route": route_key,
            "result": detached_corpus_audit(
                query=str(payload.get("query") or ""),
                file_id=str(payload.get("file_id")) if payload.get("file_id") else None,
                preview_limit=int(payload.get("limit") or 5),
            ),
        }
    if route_key == "research_integrity.status":
        return {"route": route_key, "result": research_integrity_report()}
    if route_key == "academic.classify":
        decision = AcademicWorkflowRouter.classify(str(payload.get("text", "")))
        return {"route": route_key, "result": decision.__dict__ if decision else {"route": "no_academic_workflow", "status": "none"}}
    if route_key == "citation.format":
        return {"route": route_key, "result": CitationIntegrity.format_from_metadata(payload.get("metadata") or {}, str(payload.get("style") or "APA"))}
    if route_key == "hypothesis.entry":
        return {
            "route": route_key,
            "result": ResearchIntegrityCore.build_hypothesis_entry(
                hypothesis=str(payload.get("hypothesis") or ""),
                evidence=[str(item) for item in (payload.get("evidence") or [])],
                counterarguments=[str(item) for item in (payload.get("counterarguments") or [])],
                confidence=str(payload.get("confidence") or "open"),
                next_test=str(payload.get("next_test") or "define the next bounded review or reconstruction test"),
            ),
        }
    if route_key == "case_law.candidate":
        return {
            "route": route_key,
            "result": ResearchIntegrityCore.case_law_candidate(
                law_area=str(payload.get("law_area") or "unspecified"),
                proposal=str(payload.get("proposal") or ""),
                evidence_refs=[str(item) for item in (payload.get("evidence_refs") or [])],
            ),
        }
    return {
        "route": route_key,
        "result": GracefulFall().recover(f"unknown module route: {route_key}").__dict__,
    }


def chat_gate_preview(conn: sqlite3.Connection, text: str) -> dict[str, Any]:
    return ChatGate().evaluate(conn, text)


def _matched_evidence(conn: sqlite3.Connection, text: str) -> list[dict[str, Any]]:
    terms = [term for term in ("selene", "starlight", "memory chest", "continuity pack", "starfire", "moonlight", "architecture", "emergence") if term in text.lower()]
    if not terms:
        return []
    where = " OR ".join(["preview LIKE ? OR title LIKE ? OR themes LIKE ? OR roles LIKE ?" for _ in terms])
    params: list[str] = []
    for term in terms:
        q = f"%{term}%"
        params.extend([q, q, q, q])
    rows = conn.execute(
        f"SELECT id, title, decision, source, preview FROM evidence_items WHERE {where} ORDER BY score DESC LIMIT 8",
        params,
    ).fetchall()
    return [dict(row) for row in rows]
