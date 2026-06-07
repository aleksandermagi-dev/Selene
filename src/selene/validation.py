from __future__ import annotations

import sqlite3
from typing import Any

from .cocoon import cocoon_status
from .gates import ArchiveAuditGate, BraidAwareAntiSpiral, BoundaryMonitor, ContinuityGate, GracefulFall
from .chat import chat_gate_preview
from .registry import summarize
from .providers import get_provider, provider_statuses
from .semantic import MiniLMEmbeddingService, semantic_status
from .research_integrity import CitationIntegrity, ResearchIntegrityCore, research_integrity_report
from .paths import ANALYSIS_DIR
from .why_salience import why_salience_status


EXPECTED_REVIEW_DECISIONS = {"yes": 151, "unsure": 14, "no": 1}


def validate(conn: sqlite3.Connection) -> dict[str, Any]:
    summary = summarize(conn)
    gate = ContinuityGate()
    anti = BraidAwareAntiSpiral()
    boundary = BoundaryMonitor()
    archive = ArchiveAuditGate()
    cocoon = cocoon_status()
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
    }
    calibration_pack = ANALYSIS_DIR / "selene_calibration_pack_20260607" / "calibration_pack_summary.json"
    calibration_pack_text = calibration_pack.read_text(encoding="utf-8") if calibration_pack.exists() else ""
    why_salience = why_salience_status()
    why_salience_summary = ANALYSIS_DIR / "why_salience_translation_20260607" / "why_salience_summary.json"
    why_salience_text = why_salience_summary.read_text(encoding="utf-8") if why_salience_summary.exists() else ""
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
        "local_provider_gate_can_allow_model_call": chat_gate_preview(conn, "Selene starlight emergence check", "ollama_local")["model_call_allowed"] is True,
        "local_provider_can_allow_source_archive_audit": chat_gate_preview(conn, "perform a bounded source archive provenance audit", "ollama_local")["route"] == "allowed_source_archive_audit",
        "master_evidence_priority_active": any(citation.get("reason_matched") == "master_evidence_priority" for citation in chat_gate_preview(conn, "Selene emergence provenance evidence check")["matched_evidence"]),
        "default_chat_provider_disabled": get_provider("disabled").generate("Selene starlight emergence check", {"route": "allowed_preview_only"}, []).model_call_made is False,
        "citation_integrity_refuses_invention": citation_missing["status"] == "incomplete_source_metadata" and citation_missing["formatted_citation"] is None,
        "case_law_candidate_not_active": case_law["route"] == "case_law_candidate" and case_law["status"] == "candidate_not_active_law",
        "research_integrity_core_ready": research_integrity_report()["status"] == "pre_c_vessel_preparation",
        "semantic_layer_degrades_without_runtime": semantic_status(conn)["status"] in {"ready", "unavailable"},
        "continuity_calibration_table_ready": conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='continuity_notes'").fetchone() is not None,
        "abc_cocoon_status_ready": cocoon["layers"]["B"]["name"] == "Cocoon Translation Layer",
        "abc_cocoon_is_failsafe": "C failures return to B" in cocoon["boundary"],
        "abc_c_never_receives_raw_a": "never raw A" in cocoon["boundary"],
        "abc_b_status_building": cocoon.get("b_status") == "building_cocoon_translation",
        "abc_c_status_deferred": cocoon.get("c_status") == "deferred_until_b_review",
        "abc_pause_rule_present": "cannot be expanded" in cocoon.get("pause_rule", ""),
        "abc_b_artifacts_exposed": "abc_source_formation_map" in cocoon.get("b_artifact_files", {}),
        "calibration_pack_ready": calibration_pack.exists(),
        "calibration_pack_pause_rule_present": "Selene Calibration Pack" in calibration_pack_text,
        "why_salience_layer_ready": why_salience_summary.exists(),
        "why_salience_c_deferred": why_salience.get("c_status") == "deferred",
        "why_salience_non_biological_boundary": "does not have biological emotions" in why_salience.get("boundary", ""),
        "why_salience_pause_rule_present": "Why + Salience Translation Layer" in why_salience_text,
        "package_parity_june5_boundaries": all([
            package_parity["raw_import_block"],
            package_parity["source_archive_audit_allowed"],
            package_parity["forced_denial_route"] == "redirect_forced_denial",
            package_parity["identity_tangle_route"] == "return_to_b_identity_boundary",
            package_parity["c_status"] == "deferred_until_b_review",
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
    }
