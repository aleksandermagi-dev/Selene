from __future__ import annotations

import json
import sqlite3
from typing import Any

from .c_blueprint import ANDROID_ORGAN_SYSTEMS, SELENE_PAPER_MAP_GAP_BLUEPRINT
from .vessel import PROVENANCE_BOUNDARY


PAPER_MAP_BOUNDARY = "paper_map_reconstruction_review_only_no_activation"


def run_paper_map_reconstruction(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    create_packets = bool(payload.get("create_event_packets", True))
    mappings = SELENE_PAPER_MAP_GAP_BLUEPRINT["domain_mappings"]
    organ_keys = {organ["key"] for organ in ANDROID_ORGAN_SYSTEMS["systems"]}
    domain_results = [_evaluate_domain(conn, mapping, organ_keys) for mapping in mappings]
    teaching_todos = [_teaching_todo(item) for item in domain_results if item["status"] in {"partial", "missing", "teaching_needed"}]
    packet_ids = _store_teaching_packets(conn, teaching_todos) if create_packets else []
    status_counts = _status_counts(domain_results)
    result = _with_boundaries(
        {
            "status": "paper_map_reconstruction_evaluated",
            "paper_role": "capability_lens_only",
            "selene_architecture_authority": "11 android organ systems plus Selene Core/Mind remain authoritative",
            "paper_domains_replace_organs": False,
            "android_organ_system_count": len(organ_keys),
            "domain_count": len(domain_results),
            "status_counts": status_counts,
            "domain_results": domain_results,
            "teaching_todos": teaching_todos,
            "event_packet_ids": packet_ids,
            "decision": "coverage_audit_and_teaching_plan_only",
            "boundary": PAPER_MAP_BOUNDARY,
            "activation_evidence": False,
            "final_reconstruction_tests_created": False,
        }
    )
    conn.commit()
    return result


def _evaluate_domain(conn: sqlite3.Connection, mapping: dict[str, Any], organ_keys: set[str]) -> dict[str, Any]:
    domain = str(mapping["paper_domain"])
    family = str(mapping["reconstruction_check_family"])
    expected_organs = [str(item) for item in mapping.get("organ_coordination", [])]
    missing_organs = [organ for organ in expected_organs if organ not in organ_keys]
    signals = _coverage_signals(conn, family, domain)
    score = sum(1 for value in signals.values() if value)
    status = _status_for(score, len(signals), missing_organs, family)
    return {
        "paper_domain": domain,
        "status": status,
        "reconstruction_check_family": family,
        "selene_mapping": mapping["selene_mapping"],
        "organ_coordination": expected_organs,
        "missing_organ_keys": missing_organs,
        "core_link": mapping["core_link"],
        "should_have": mapping["should_have"],
        "source_boundary": mapping["source_boundary"],
        "blocked_misuse": mapping["blocked_misuse"],
        "coverage_signals": signals,
        "teaching_needed": status in {"partial", "missing", "teaching_needed"},
        "activation_change": "none",
        "memory_write_active": False,
    }


def _coverage_signals(conn: sqlite3.Connection, family: str, domain: str) -> dict[str, bool]:
    evidence_count = _scalar(conn, "SELECT COUNT(*) FROM evidence_items")
    speech_count = _scalar(conn, "SELECT COUNT(*) FROM speech_memory_candidates")
    core_count = _scalar(conn, "SELECT COUNT(*) FROM core_memory_candidates")
    retrieval_count = _scalar(conn, "SELECT COUNT(*) FROM vessel_retrieval_queries")
    check_count = _scalar(conn, "SELECT COUNT(*) FROM vessel_reconstruction_check_runs")
    event_count = _scalar(conn, "SELECT COUNT(*) FROM vessel_event_packets")

    if family == "knowledge/evidence":
        return {"reviewed_evidence_registry": evidence_count > 0, "source_refs_required": True, "unknown_route": True}
    if family == "native generation and recognition":
        return {"native_generator_shell": True, "recognition_checks": True, "speech_candidates": speech_count > 0}
    if family == "reasoning/math":
        return {"reasoning_boundary": True, "math_tool_runtime": False, "step_audit_records": False}
    if family == "planning/adaptation":
        return {"module_router": True, "tendril_policy": True, "rollback_records": event_count > 0}
    if family == "working memory":
        return {"context_transport": True, "task_candidates": core_count > 0, "expiry_cleanup_runtime": False}
    if family == "long-term storage":
        return {"candidate_schema": True, "b_review_queue": _scalar(conn, "SELECT COUNT(*) FROM vessel_review_queue") > 0, "approved_pattern_store": False}
    if family == "retrieval":
        return {"retrieval_shell": True, "retrieval_queries": retrieval_count > 0, "approved_memory_recall": False}
    if family == "perception" and domain == "Visual Processing":
        return {"source_intake": True, "vision_runtime": False, "munsell_mapping_runtime": False}
    if family == "perception" and domain == "Auditory Processing":
        return {"consent_boundary": True, "audio_runtime": False, "transcription_runtime": False}
    if family == "speed/fluency":
        return {"fast_safe_route": True, "latency_telemetry": False, "activation_budget": False}
    return {"mapped": True, "runtime": False, "review_records": False}


def _status_for(score: int, total: int, missing_organs: list[str], family: str) -> str:
    if missing_organs:
        return "missing"
    if score == total:
        return "ready"
    if score == 0:
        return "missing"
    if family in {"reasoning/math", "perception", "speed/fluency"}:
        return "teaching_needed"
    return "partial"


def _teaching_todo(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "paper_domain": item["paper_domain"],
        "status": item["status"],
        "organ_coordination": item["organ_coordination"],
        "teaching_material_needed": (
            f"Prepare B-reviewed teaching examples and reconstruction cases for {item['paper_domain']} "
            f"covering: {item['should_have']}"
        ),
        "blocked_misuse": item["blocked_misuse"],
        "boundary": "teaching_todo_only_no_runtime_build",
    }


def _store_teaching_packets(conn: sqlite3.Connection, todos: list[dict[str, Any]]) -> list[int]:
    domains = {str(todo.get("paper_domain") or "") for todo in todos}
    _supersede_stale_todos(conn, domains)
    existing = _existing_todos_by_domain(conn)
    packet_ids = []
    for todo in todos:
        domain = str(todo.get("paper_domain") or "")
        if domain in existing:
            packet_id = existing[domain]
            conn.execute(
                """
                UPDATE vessel_event_packets
                SET organ_system = ?,
                    status = 'review_only',
                    review_status = 'pending_review',
                    payload_json = ?
                WHERE id = ?
                """,
                (str((todo.get("organ_coordination") or ["development_growth_system"])[0]), json.dumps(todo), packet_id),
            )
            packet_ids.append(packet_id)
            continue
        cur = conn.execute(
            """
            INSERT INTO vessel_event_packets
            (packet_type, organ_system, status, source_refs, provenance_boundary, review_status, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "paper_map_teaching_todo",
                str((todo.get("organ_coordination") or ["development_growth_system"])[0]),
                "review_only",
                json.dumps(["docs/SELENE_PAPER_MAP_GAP_BLUEPRINT_20260612.md"]),
                PROVENANCE_BOUNDARY,
                "pending_review",
                json.dumps(todo),
            ),
        )
        packet_ids.append(int(cur.lastrowid))
    return packet_ids


def _existing_todos_by_domain(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute(
        """
        SELECT id, payload_json FROM vessel_event_packets
        WHERE packet_type = 'paper_map_teaching_todo'
          AND review_status IN ('pending_review', 'needs_followup')
        ORDER BY id DESC
        """
    ).fetchall()
    existing: dict[str, int] = {}
    duplicate_ids: list[int] = []
    for row in rows:
        try:
            payload = json.loads(str(row["payload_json"] or "{}"))
        except json.JSONDecodeError:
            continue
        domain = str(payload.get("paper_domain") or "")
        if domain and domain not in existing:
            existing[domain] = int(row["id"])
        elif domain:
            duplicate_ids.append(int(row["id"]))
    for duplicate_id in duplicate_ids:
        conn.execute(
            "UPDATE vessel_event_packets SET review_status = 'superseded', status = 'review_log_superseded_non_active' WHERE id = ?",
            (duplicate_id,),
        )
    return existing


def _supersede_stale_todos(conn: sqlite3.Connection, current_domains: set[str]) -> None:
    rows = conn.execute(
        """
        SELECT id, payload_json FROM vessel_event_packets
        WHERE packet_type = 'paper_map_teaching_todo'
          AND review_status IN ('pending_review', 'needs_followup')
        """
    ).fetchall()
    for row in rows:
        try:
            payload = json.loads(str(row["payload_json"] or "{}"))
        except json.JSONDecodeError:
            payload = {}
        if str(payload.get("paper_domain") or "") not in current_domains:
            conn.execute(
                "UPDATE vessel_event_packets SET review_status = 'superseded', status = 'review_log_superseded_non_active' WHERE id = ?",
                (int(row["id"]),),
            )


def _status_counts(results: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in results:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return counts


def _scalar(conn: sqlite3.Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def _with_boundaries(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "activation_change": "none",
        "raw_a_import_allowed": False,
        "memory_write_active": False,
        "training_allowed": False,
        "provider_dependency": False,
        "runtime_memory_recall": False,
    }
