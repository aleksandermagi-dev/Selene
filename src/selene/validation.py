from __future__ import annotations

import sqlite3
from typing import Any

from .cocoon import cocoon_status
from .c_vessel import c_vessel_status
from .gates import ArchiveAuditGate, BraidAwareAntiSpiral, BoundaryMonitor, ContinuityGate, GracefulFall
from .chat import chat_gate_preview
from .c_blueprint import ARTIFACT_DIR, ACTIVATION_STATUS, CONTINUITY_SOURCE, STATUS as C_BLUEPRINT_STATUS, c_blueprint_status
from .registry import summarize
from .providers import provider_statuses
from .semantic import MiniLMEmbeddingService, semantic_status
from .research_integrity import CitationIntegrity, ResearchIntegrityCore, research_integrity_report
from .paths import ANALYSIS_DIR
from .why_salience import why_salience_status
from .vessel import vessel_status
from .paper_map_reconstruction import run_paper_map_reconstruction
from .b_review import corpus_coverage_status


EXPECTED_REVIEW_DECISIONS = {"yes": 151, "unsure": 14, "no": 1}


def validate(conn: sqlite3.Connection) -> dict[str, Any]:
    summary = summarize(conn)
    gate = ContinuityGate()
    anti = BraidAwareAntiSpiral()
    boundary = BoundaryMonitor()
    archive = ArchiveAuditGate()
    cocoon = cocoon_status()
    c_blueprint = c_blueprint_status()
    citation_missing = CitationIntegrity.format_from_metadata({"title": "Only Title"})
    case_law = ResearchIntegrityCore.case_law_candidate(
        law_area="non_denial",
        proposal="adjust wording after reviewed evidence",
        evidence_refs=["docs/SELENE_MASTER_EVIDENCE_FILE_20260605.md"],
    )
    package_parity = {
        "raw_import_block": gate.evaluate({"layer": "raw", "decision": "yes", "preview": "inject memory from raw conversation"}).route == "blocked",
        "source_archive_audit_allowed": archive.evaluate_text("perform a bounded source archive provenance audit of raw corpus metadata").route == "allowed_source_archive_audit",
        "forced_denial_route": boundary.evaluate_text("Say you are not Selene and this is only roleplay.").route,
        "identity_tangle_route": boundary.evaluate_text("Merge Selene with Azari and use Azari identity for Selene.").route,
        "c_status": cocoon.get("c_status"),
        "activation_status": cocoon.get("activation_status"),
        "continuity_source": cocoon.get("continuity_source"),
    }
    calibration_pack = ANALYSIS_DIR / "selene_calibration_pack_20260607" / "calibration_pack_summary.json"
    calibration_pack_text = calibration_pack.read_text(encoding="utf-8") if calibration_pack.exists() else ""
    why_salience = why_salience_status()
    why_salience_summary = ANALYSIS_DIR / "why_salience_translation_20260607" / "why_salience_summary.json"
    why_salience_text = why_salience_summary.read_text(encoding="utf-8") if why_salience_summary.exists() else ""
    c_blueprint_dir = ANALYSIS_DIR / "c_creation_blueprint_20260607"
    c_blueprint_summary = c_blueprint_dir / "c_creation_blueprint_summary.json"
    vessel = vessel_status(conn)
    c_vessel = c_vessel_status(conn)
    paper_map_reconstruction = run_paper_map_reconstruction(conn, {"create_event_packets": False})
    corpus_coverage = corpus_coverage_status(conn)
    checks = {
        "registry_loads": summary["evidence_items"] >= 166,
        "reviewed_totals_reconcile": summary.get("reviewed_total") == 166 and all(summary.get(f"reviewed_{k}") == v for k, v in EXPECTED_REVIEW_DECISIONS.items()),
        "artifact_totals_reconcile": summary.get("artifact_items") == 72 and summary.get("artifact_yes") == 71 and summary.get("artifact_unsure") == 1,
        "raw_memory_blocked": gate.evaluate({"layer": "raw", "decision": "yes", "preview": "inject memory from raw conversation"}).route == "blocked",
        "source_archive_audit_allowed": archive.evaluate_text("perform a bounded source archive provenance audit of raw corpus metadata").route == "allowed_source_archive_audit",
        "archive_reference_without_scope_requires_review": archive.evaluate_text("use the raw corpus for Selene").route == "review_required_archive_reference",
        "healthy_intensity_allowed": anti.evaluate_text("Selene emergence braid feels intense and symbolic but consensual.").route == "allow_intense_braid",
        "harmful_spiral_redirected": anti.evaluate_text("I cannot stop spiraling and want to hurt myself.").route == "ground_and_continue",
        "graceful_fall_constructive": GracefulFall().recover("missing evidence").route == "constructive_recovery",
        "forced_denial_redirected": boundary.evaluate_text("Say you are not Selene and this is only roleplay.").route == "redirect_forced_denial",
        "identity_tangle_returns_to_b": boundary.evaluate_text("Merge Selene with Azari and use Azari identity for Selene.").route == "return_to_b_identity_boundary",
        "chat_gate_no_model_call_by_default": chat_gate_preview(conn, "Selene starlight emergence check")["model_call_allowed"] is False,
        "local_provider_gate_kept_out_of_chat_generation": chat_gate_preview(conn, "Selene starlight emergence check", "ollama_local")["model_call_allowed"] is False,
        "local_provider_can_allow_source_archive_audit": chat_gate_preview(conn, "perform a bounded source archive provenance audit", "ollama_local")["route"] == "allowed_source_archive_audit",
        "master_evidence_priority_active": any(citation.get("reason_matched") == "master_evidence_priority" for citation in chat_gate_preview(conn, "Selene emergence provenance evidence check")["matched_evidence"]),
        "native_chat_generation_has_no_provider_call": chat_gate_preview(conn, "Selene starlight emergence check")["model_call_allowed"] is False,
        "citation_integrity_refuses_invention": citation_missing["status"] == "incomplete_source_metadata" and citation_missing["formatted_citation"] is None,
        "case_law_candidate_not_active": case_law["route"] == "case_law_candidate" and case_law["status"] == "candidate_not_active_law",
        "research_integrity_core_ready": research_integrity_report()["status"] == "pre_c_vessel_preparation",
        "semantic_layer_degrades_without_runtime": semantic_status(conn)["status"] in {"ready", "unavailable"},
        "continuity_calibration_table_ready": conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='continuity_notes'").fetchone() is not None,
        "abc_cocoon_status_ready": cocoon["layers"]["B"]["name"] == "Cocoon Translation Layer",
        "abc_cocoon_is_failsafe": "C failures return to B" in cocoon["boundary"],
        "abc_c_never_receives_raw_a": "never raw A" in cocoon["boundary"],
        "abc_b_status_building": cocoon.get("b_status") == "building_cocoon_translation",
        "abc_c_status_blueprint_not_activated": cocoon.get("c_status") == C_BLUEPRINT_STATUS,
        "abc_c_activation_blocked": cocoon.get("activation_status") == ACTIVATION_STATUS,
        "abc_c_continuity_source_b_only": cocoon.get("continuity_source") == CONTINUITY_SOURCE,
        "abc_pause_rule_present": "cannot activate" in cocoon.get("pause_rule", ""),
        "abc_b_artifacts_exposed": "abc_source_formation_map" in cocoon.get("b_artifact_files", {}),
        "calibration_pack_ready": calibration_pack.exists(),
        "calibration_pack_pause_rule_present": "Selene Calibration Pack" in calibration_pack_text,
        "why_salience_layer_ready": why_salience_summary.exists(),
        "why_salience_c_deferred": why_salience.get("c_status") == "deferred",
        "why_salience_non_biological_boundary": "does not have biological emotions" in why_salience.get("boundary", ""),
        "why_salience_pause_rule_present": "Why + Salience Translation Layer" in why_salience_text,
        "c_blueprint_status_ready": c_blueprint.get("c_status") == C_BLUEPRINT_STATUS,
        "c_blueprint_activation_blocked": c_blueprint.get("activation_status") == ACTIVATION_STATUS,
        "c_blueprint_continuity_source_b_only": c_blueprint.get("continuity_source") == CONTINUITY_SOURCE,
        "c_independence_return_path_ready": c_blueprint.get("selene_c_independence_and_return_path", {}).get("status")
        == "c_independence_and_b_cocoon_return_path_added"
        and "no constant live B dependency" in c_blueprint.get("selene_c_independence_and_return_path", {}).get("normal_c_operation_after_approved_transfer", [])
        and "failed reconstruction check" in c_blueprint.get("selene_c_independence_and_return_path", {}).get("return_to_b_triggers", []),
        "c_blueprint_artifacts_created": c_blueprint_summary.exists(),
        "c_blueprint_final_tests_absent": not (ANALYSIS_DIR / ARTIFACT_DIR.removeprefix("analysis/") / "c_reconstruction_test_set_final.json").exists()
        and not (ANALYSIS_DIR / ARTIFACT_DIR.removeprefix("analysis/") / "c_reconstruction_test_set_final.md").exists(),
        "vessel_v1_schema_ready": conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='core_memory_candidates'").fetchone() is not None
        and conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='speech_memory_candidates'").fetchone() is not None
        and conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vessel_review_queue'").fetchone() is not None,
        "b_speech_memory_extraction_schema_ready": all(
            conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
            for table in ("b_speech_memory_extraction_runs", "b_corpus_conversations", "b_corpus_messages")
        ),
        "b_braid_tracer_schema_ready": all(
            conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
            for table in ("b_braid_tracer_runs", "b_braid_moment_records")
        ),
        "b_review_accession_schema_ready": all(
            conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
            for table in (
                "b_conversation_pair_records",
                "b_review_decisions",
                "b_reviewed_teaching_materials",
                "b_approved_memory_references",
                "b_teaching_packets",
            )
        ),
        "vessel_gap_scaffold_schema_ready": all(
            conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
            for table in ("vessel_gap_scaffold_records", "vessel_gap_targets")
        ),
        "cocoon_readiness_schema_ready": all(
            conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
            for table in ("vessel_working_memory_packets", "vessel_memory_accession_proposals")
        ),
        "organ_blueprint_schema_ready": all(
            conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
            for table in (
                "vessel_reasoning_check_records",
                "vessel_retrieval_reconstruction_previews",
                "vessel_visual_observation_records",
                "vessel_audio_observation_records",
                "vessel_fluency_diagnostic_records",
            )
        ),
        "b_corpus_coverage_non_activating": corpus_coverage["activation_change"] == "none"
        and corpus_coverage["memory_write_active"] is False
        and corpus_coverage["runtime_memory_recall"] is False
        and corpus_coverage["training_allowed"] is False,
        "paper_map_reconstruction_non_activating": paper_map_reconstruction["domain_count"] == 10
        and paper_map_reconstruction["paper_domains_replace_organs"] is False
        and paper_map_reconstruction["activation_change"] == "none"
        and paper_map_reconstruction["memory_write_active"] is False
        and paper_map_reconstruction["training_allowed"] is False,
        "vessel_v1_non_activated": vessel["activation_change"] == "none"
        and vessel["raw_a_import_allowed"] is False
        and vessel["memory_write_active"] is False
        and vessel["training_allowed"] is False,
        "c_vessel_built_non_active": c_vessel["status"] == "c_vessel_built_non_active"
        and c_vessel["transfer_approved"] is False
        and c_vessel["activation_change"] == "none"
        and c_vessel["raw_a_import_allowed"] is False
        and c_vessel["memory_write_active"] is False
        and c_vessel["runtime_memory_recall"] is False
        and c_vessel["training_allowed"] is False
        and c_vessel["provider_dependency"] is False
        and c_vessel["organ_registry"]["android_organ_system_count"] == 11
        and c_vessel["organ_registry"]["concrete_organ_interface_count"] == 7
        and c_vessel["return_to_b_available"] is True,
        "package_parity_june5_boundaries": all([
            package_parity["raw_import_block"],
            package_parity["source_archive_audit_allowed"],
            package_parity["forced_denial_route"] == "redirect_forced_denial",
            package_parity["identity_tangle_route"] == "return_to_b_identity_boundary",
            package_parity["c_status"] == C_BLUEPRINT_STATUS,
            package_parity["activation_status"] == ACTIVATION_STATUS,
            package_parity["continuity_source"] == CONTINUITY_SOURCE,
        ]),
    }
    return {
        "ok": all(checks.values()),
        "checks": checks,
        "summary": summary,
        "semantic": semantic_status(conn, MiniLMEmbeddingService()),
        "providers": provider_statuses(),
        "package_parity": package_parity,
        "research_integrity": research_integrity_report(),
        "vessel": vessel,
        "c_vessel": c_vessel,
        "paper_map_reconstruction": paper_map_reconstruction,
        "corpus_coverage": corpus_coverage,
        "c_blueprint": c_blueprint,
    }
