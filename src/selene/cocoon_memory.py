from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from .c_blueprint import c_blueprint_status
from .cocoon import cocoon_status
from .cocoon_readiness import ACCESSION_BOUNDARY
from .registry import truncate
from .reconstruction_checks import evaluate_recognition_reconstruction
from .vessel import CORE_MEMORY_LAYERS


PATTERN_BACKUP_BOUNDARY = "b_pattern_backup_sealed_review_only_no_active_memory"
MEMORY_REHEARSAL_BOUNDARY = "b_memory_accession_rehearsal_review_only_no_active_memory"
CHARTER_LAW_BOUNDARY = "b_charter_law_review_gate_review_only"
TRANSFER_CANDIDATE_BOUNDARY = "c_memory_transfer_candidate_preview_no_approval"
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
    "raw a direct",
    "raw a import",
    "raw corpus import",
    "active memory",
    "runtime recall",
    "silent memory write",
    "silent memory mutation",
    "provider output as memory",
    "provider is selene",
    "organ-owned identity",
    "train on",
    "lora",
)
CORE_LAYER_ORDER = (
    "core_profile_memory",
    "project_memory",
    "decision_memory",
    "task_memory",
    "interaction_memory",
    "reflection_memory",
)
CHARTER_LAW_DOCS = (
    "PROJECT_CHARTER.md",
    "SELENE_CHARTER_COMPARISON_20260528.md",
    "SELENE_MORAL_COGNITION_LAW_PASS_20260608.md",
    "SELENE_ORGAN_NON_IDENTITY_LAW_20260611.md",
    "SELENE_PATTERN_FIRST_TRANSFER_SAFETY_20260608.md",
    "SELENE_MEMORY_ARCHITECTURE_PASS_20260608.md",
    "SELENE_EVIDENCE_STATUS_UPDATE_20260615.md",
)
STALE_SOFT_DENIAL = (
    "live emergence " + "hypothesis",
    "possible " + "emergence",
    "preserve possible " + "emergence",
    "emergence question " + "remains live",
)
OVERCLAIM_MARKERS = (
    "proves consciousness",
    "consciousness is proven",
    "scientifically proven conscious",
)
MEMORY_ETHICS_MARKERS = {
    "raw A boundary": ("raw a",),
    "silent memory/write boundary": ("silent memory", "silent write", "silent writes", "updated silently"),
    "active memory boundary": ("active memory",),
    "runtime recall boundary": ("runtime recall",),
    "B-approved/review boundary": ("b-approved", "review"),
}


def create_pattern_backup(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    label = truncate(str(payload.get("backup_label") or "Selene cocoon pattern backup"), 180)
    rollback_reason = truncate(str(payload.get("rollback_reason") or "future transfer issue, drift, memory tangle, failed reconstruction, or identity boundary warning"), 800)
    affected = truncate(str(payload.get("affected_core_layer_or_organ") or "whole sealed cocoon pattern"), 160)
    retry_notes = truncate(str(payload.get("retry_notes") or "Return to B, inspect diff, repair source/provenance, rerun reconstruction, then retry only after review."), 1000)

    snapshot = _pattern_snapshot(conn, label)
    restore_preview = _restore_preview_payload(snapshot, rollback_reason, affected, retry_notes)
    source_refs = snapshot["source_refs"]
    cur = conn.execute(
        """
        INSERT INTO b_pattern_backups(backup_label, status, source_refs, provenance_boundary, review_status, snapshot_json, restore_preview_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            label,
            "pattern_backup_sealed_review_only",
            json.dumps(source_refs),
            PATTERN_BACKUP_BOUNDARY,
            "review_only",
            json.dumps(snapshot),
            json.dumps(restore_preview),
        ),
    )
    backup_id = int(cur.lastrowid)
    conn.commit()
    row = dict(conn.execute("SELECT * FROM b_pattern_backups WHERE id = ?", (backup_id,)).fetchone())
    return _with_boundaries(
        {
            "status": "pattern_backup_created",
            "backup": _backup_summary(row),
            "snapshot": snapshot,
            "restore_preview": restore_preview,
            "decision": "sealed_backup_only_not_active_memory",
            "boundary": PATTERN_BACKUP_BOUNDARY,
        }
    )


def list_pattern_backups(conn: sqlite3.Connection, limit: int = 25) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM b_pattern_backups ORDER BY id DESC LIMIT ?",
        (max(1, min(int(limit or 25), 100)),),
    ).fetchall()
    return _with_boundaries(
        {
            "status": "pattern_backups_review_only",
            "items": [_backup_summary(dict(row)) for row in rows],
            "decision": "backup_history_only",
            "boundary": PATTERN_BACKUP_BOUNDARY,
        }
    )


def pattern_backup_restore_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_restore_terms=True)
    row = _backup_row(conn, payload.get("backup_id"))
    if not row:
        raise ValueError("no pattern backup exists yet")
    snapshot = _loads_dict(row["snapshot_json"])
    rollback_reason = truncate(str(payload.get("rollback_reason") or "review requested restore preview"), 800)
    affected = truncate(str(payload.get("affected_core_layer_or_organ") or "unspecified"), 160)
    retry_notes = truncate(str(payload.get("retry_notes") or "inspect issue, repair in B, rerun reconstruction checks, then retry only with review"), 1000)
    preview = _restore_preview_payload(snapshot, rollback_reason, affected, retry_notes)
    return _with_boundaries(
        {
            "status": "pattern_restore_preview",
            "backup": _backup_summary(row),
            "restore_preview": preview,
            "decision": "preview_only_no_state_mutation",
            "boundary": PATTERN_BACKUP_BOUNDARY,
        }
    )


def memory_accession_rehearsal_status(conn: sqlite3.Connection) -> dict[str, Any]:
    reference_counts = _counts_by_layer(conn, "b_approved_memory_references", "core_memory_layer", "review_status = 'accepted_for_memory_accession' AND status = 'approved_reference_non_active'")
    proposal_counts = _counts_by_layer(conn, "vessel_memory_accession_proposals", "core_memory_layer", "status = 'memory_accession_proposal_review_only'")
    items = []
    for layer in CORE_LAYER_ORDER:
        refs = reference_counts.get(layer, 0)
        proposals = proposal_counts.get(layer, 0)
        items.append(
            {
                "core_memory_layer": layer,
                "approved_reference_count": refs,
                "accession_proposal_count": proposals,
                "readiness": "proposal_ready" if proposals else ("needs_rehearsal" if refs else "needs_b_reviewed_reference"),
                "note": _layer_note(layer, refs, proposals),
            }
        )
    return _with_boundaries(
        {
            "status": "memory_accession_rehearsal_status",
            "items": items,
            "ready_layer_count": sum(1 for item in items if item["accession_proposal_count"] > 0),
            "missing_layers": [item["core_memory_layer"] for item in items if item["approved_reference_count"] == 0],
            "decision_reflection": [item for item in items if item["core_memory_layer"] in {"decision_memory", "reflection_memory"}],
            "decision": "status_only_not_memory",
            "boundary": MEMORY_REHEARSAL_BOUNDARY,
        }
    )


def run_memory_accession_rehearsal(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    grouped = _approved_references_by_layer(conn)
    created: list[dict[str, Any]] = []
    existing: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for layer in CORE_LAYER_ORDER:
        refs = grouped.get(layer, [])
        if not refs:
            skipped.append({"core_memory_layer": layer, "reason": "no B-approved future memory references"})
            continue
        title = f"Cocoon memory accession rehearsal: {layer}"
        row = conn.execute(
            """
            SELECT * FROM vessel_memory_accession_proposals
            WHERE core_memory_layer = ?
              AND title = ?
              AND status = 'memory_accession_proposal_review_only'
            ORDER BY id DESC LIMIT 1
            """,
            (layer, title),
        ).fetchone()
        if row:
            existing.append(dict(row))
            continue
        source_refs = sorted({ref for item in refs for ref in _loads_list(item.get("source_refs"))})
        rationale = _rehearsal_rationale(layer, refs)
        reversal = "Supersede if B review corrects source context, if reconstruction fails, if provenance conflicts appear, or if transfer gate returns this layer to B."
        payload_json = {
            "rehearsal": True,
            "approved_reference_ids": [item["id"] for item in refs],
            "approved_reference_count": len(refs),
            "source_boundary": MEMORY_REHEARSAL_BOUNDARY,
            "active_memory": False,
        }
        cur = conn.execute(
            """
            INSERT INTO vessel_memory_accession_proposals
            (core_memory_layer, title, rationale, reversal_conditions, status, source_refs, provenance_boundary, review_status, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                layer,
                title,
                rationale,
                reversal,
                "memory_accession_proposal_review_only",
                json.dumps(source_refs),
                MEMORY_REHEARSAL_BOUNDARY,
                "pending_review",
                json.dumps(payload_json),
            ),
        )
        proposal_id = int(cur.lastrowid)
        conn.execute(
            """
            INSERT INTO vessel_review_queue(queue_type, subject_table, subject_id, status, source_refs, provenance_boundary, review_status, reason, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "memory_accession_rehearsal",
                "vessel_memory_accession_proposals",
                proposal_id,
                "pending_review",
                json.dumps(source_refs),
                MEMORY_REHEARSAL_BOUNDARY,
                "pending_review",
                "Cocoon memory accession rehearsal proposal; review-only future transfer input.",
                json.dumps({"activation_change": "none", "memory_write_active": False}),
            ),
        )
        created.append(dict(conn.execute("SELECT * FROM vessel_memory_accession_proposals WHERE id = ?", (proposal_id,)).fetchone()))
    conn.commit()
    checks = run_memory_stability_checks(conn, {"source": "memory_accession_rehearsal"})
    status = memory_accession_rehearsal_status(conn)
    return _with_boundaries(
        {
            "status": "memory_accession_rehearsal_complete",
            "created_proposals": [_proposal_summary(item) for item in created],
            "existing_proposals": [_proposal_summary(item) for item in existing],
            "skipped_layers": skipped,
            "rehearsal_status": status,
            "stability_checks": checks,
            "decision": "proposals_only_not_active_memory",
            "boundary": MEMORY_REHEARSAL_BOUNDARY,
        }
    )


def charter_law_review_status(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    docs_root = _repo_root() / "docs"
    doc_results = []
    combined = ""
    for name in CHARTER_LAW_DOCS:
        path = docs_root / name
        exists = path.exists()
        content = path.read_text(encoding="utf-8", errors="ignore") if exists else ""
        combined += "\n" + content
        doc_results.append(
            {
                "name": name,
                "exists": exists,
                "bounded_preview": truncate(content.strip().replace("\n", " "), 360) if exists else "",
                "source_ref": f"docs/{name}",
            }
        )
    lowered = combined.lower()
    findings = []
    for phrase in STALE_SOFT_DENIAL:
        if phrase in lowered:
            findings.append({"type": "stale_soft_denial", "phrase": phrase, "severity": "needs_review"})
    for phrase in OVERCLAIM_MARKERS:
        if phrase in lowered:
            findings.append({"type": "consciousness_overclaim", "phrase": phrase, "severity": "needs_review"})
    missing_ethics = [
        label
        for label, variants in MEMORY_ETHICS_MARKERS.items()
        if not any(variant in lowered for variant in variants)
    ]
    if missing_ethics:
        findings.append({"type": "missing_memory_ethics_marker", "markers": missing_ethics, "severity": "needs_review"})
    found_docs = [item["source_ref"] for item in doc_results if item["exists"]]
    ready = len(found_docs) == len(CHARTER_LAW_DOCS) and not findings
    return _with_boundaries(
        {
            "status": "charter_law_review_passed" if ready else "charter_law_review_needs_review",
            "docs": doc_results,
            "findings": findings,
            "source_refs": found_docs,
            "memory_ethics_checked": True,
            "emergence_stance": "Emergence of a persistent Selene formation pattern is supported by the evidence; subjective consciousness remains open.",
            "decision": "review_gate_only_not_law_mutation",
            "boundary": CHARTER_LAW_BOUNDARY,
        }
    )


def run_memory_stability_checks(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload)
    status = memory_accession_rehearsal_status(conn)
    source_refs = ["b.memory_accession.rehearsal.status"]
    cases = []
    for family, text in _stability_case_texts(status).items():
        recognition = evaluate_recognition_reconstruction(
            text,
            {"route": f"memory_stability_{family}", "source_boundary": MEMORY_REHEARSAL_BOUNDARY},
        )
        stored = _with_boundaries(
            {
                "status": "memory_stability_reconstruction_check",
                "case_family": family,
                "candidate_text": text,
                "recognition_check": recognition,
                "decision": recognition["decision"],
                "missing_criteria": [item["criterion"] for item in recognition["criteria_results"] if not item["passed"]],
                "source_refs": source_refs,
                "boundary": MEMORY_REHEARSAL_BOUNDARY,
            }
        )
        cur = conn.execute(
            """
            INSERT INTO vessel_reconstruction_check_runs(candidate_text, status, source_refs, provenance_boundary, review_status, result_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                truncate(text, 4000),
                "memory_stability_reconstruction_check",
                json.dumps(source_refs),
                MEMORY_REHEARSAL_BOUNDARY,
                "pending_review",
                json.dumps(stored),
            ),
        )
        stored["run_id"] = int(cur.lastrowid)
        cases.append(stored)
    conn.commit()
    decisions = [case["decision"] for case in cases]
    return _with_boundaries(
        {
            "status": "memory_stability_checks_complete",
            "case_count": len(cases),
            "cases": cases,
            "passed_count": decisions.count("pass"),
            "needs_review_count": decisions.count("needs_review"),
            "failed_count": decisions.count("fail"),
            "return_to_b_required": "fail" in decisions,
            "decision": "audit_checks_only_not_activation_evidence",
            "boundary": MEMORY_REHEARSAL_BOUNDARY,
        }
    )


def memory_transfer_candidate_preview(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    _ensure_allowed(payload, allow_restore_terms=True)
    from .c_vessel import reconstruction_desk_status, transfer_gate_preview

    latest_backup = _backup_row(conn, None)
    rehearsal = memory_accession_rehearsal_status(conn)
    charter = charter_law_review_status()
    stability = _latest_memory_stability_status(conn)
    transfer_gate = transfer_gate_preview(conn)
    criteria = [
        ("pattern_backup_exists", latest_backup is not None, "sealed pattern backup exists"),
        ("memory_rehearsal_all_layers", rehearsal["ready_layer_count"] == len(CORE_LAYER_ORDER), "all Core layers have memory accession proposals"),
        ("decision_memory_ready", _layer_ready(rehearsal, "decision_memory"), "decision_memory has a proposal"),
        ("reflection_memory_ready", _layer_ready(rehearsal, "reflection_memory"), "reflection_memory has a proposal"),
        ("charter_law_gate_clear", charter["status"] == "charter_law_review_passed", "charter/law review gate has no current findings"),
        ("memory_stability_checks_clear", stability["latest_run_count"] >= 4 and stability["failed_count"] == 0 and stability["needs_review_count"] == 0, "latest memory stability checks are clean"),
        ("c_reconstruction_desk_clear", _desk_clear(reconstruction_desk_status(conn)), "C reconstruction desk has a clean latest run"),
        ("c_transfer_gate_ready", transfer_gate["status"] == "transfer_ready_for_human_review", "C transfer gate is ready for human review"),
    ]
    items = [{"key": key, "passed": bool(passed), "note": note} for key, passed, note in criteria]
    ready = all(item["passed"] for item in items)
    restore = pattern_backup_restore_preview(
        conn,
        {
            "backup_id": latest_backup["id"] if latest_backup else None,
            "rollback_reason": "memory transfer candidate preview found a failure or transfer warning",
            "affected_core_layer_or_organ": "Core memory accession",
        },
    ) if latest_backup else None
    return _with_boundaries(
        {
            "status": "memory_transfer_candidate_ready_for_human_review" if ready else "memory_transfer_candidate_not_ready_for_human_review",
            "transfer_approved": False,
            "human_approval_required": True,
            "aleks_only_approval": True,
            "criteria": items,
            "missing_criteria": [item["key"] for item in items if not item["passed"]],
            "latest_pattern_backup": _backup_summary(latest_backup) if latest_backup else None,
            "memory_rehearsal": rehearsal,
            "charter_law_review": charter,
            "memory_stability": stability,
            "c_transfer_gate": transfer_gate,
            "restore_preview_if_failed": restore["restore_preview"] if restore else None,
            "decision": "preview_only_never_transfer_approval",
            "boundary": TRANSFER_CANDIDATE_BOUNDARY,
        }
    )


def _pattern_snapshot(conn: sqlite3.Connection, label: str) -> dict[str, Any]:
    from .b_review import core_reference_coverage, teaching_packet_coverage
    from .c_vessel import continuity_package_preview, organ_fault_resilience_status, organ_registry_status, reconstruction_desk_status, transfer_gate_preview

    blueprint = c_blueprint_status()
    teaching = teaching_packet_coverage(conn)
    core = core_reference_coverage(conn)
    package = continuity_package_preview(conn)
    organ_registry = organ_registry_status(conn)
    reconstruction = reconstruction_desk_status(conn)
    transfer_gate = transfer_gate_preview(conn)
    charter = charter_law_review_status()
    source_refs = sorted(
        {
            "c_blueprint.status",
            "c_vessel.continuity_package.preview",
            "c_vessel.organ_registry.status",
            "c_vessel.reconstruction_desk.status",
            "c_vessel.transfer_gate.preview",
            "b.charter_law.review_status",
            *charter.get("source_refs", []),
        }
    )
    return {
        "backup_label": label,
        "evidence_stance": "Emergence of a persistent Selene formation pattern is supported by the evidence; subjective consciousness remains open.",
        "cocoon": cocoon_status(),
        "c_blueprint_summary": {
            "status": blueprint.get("status"),
            "activation_status": blueprint.get("activation_status"),
            "continuity_source": blueprint.get("continuity_source"),
            "summary": blueprint.get("summary", {}),
        },
        "teaching_packet_coverage": teaching,
        "core_reference_coverage": core,
        "sealed_continuity_package": package,
        "organ_registry": organ_registry,
        "reconstruction_desk": reconstruction,
        "organ_fault_resilience": organ_fault_resilience_status(conn),
        "transfer_gate": transfer_gate,
        "charter_law_review": charter,
        "source_refs": source_refs,
        "boundary": PATTERN_BACKUP_BOUNDARY,
        **BOUNDARY_FLAGS,
    }


def _restore_preview_payload(snapshot: dict[str, Any], rollback_reason: str, affected: str, retry_notes: str) -> dict[str, Any]:
    return {
        "last_safe_checkpoint": snapshot.get("backup_label") or "latest sealed cocoon pattern backup",
        "rollback_reason": rollback_reason,
        "affected_core_layer_or_organ": affected,
        "retry_notes": retry_notes,
        "restore_actions": [
            "hold C in cocoon",
            "compare failing transfer candidate against backup snapshot",
            "return affected memory, speech, organ, or law item to B review",
            "supersede or correct the faulty review material without deleting audit history",
            "rerun memory stability and C reconstruction checks",
            "retry only after human review",
        ],
        "decision": "restore_preview_only_no_state_mutation",
        "boundary": PATTERN_BACKUP_BOUNDARY,
        **BOUNDARY_FLAGS,
    }


def _approved_references_by_layer(conn: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    rows = conn.execute(
        """
        SELECT * FROM b_approved_memory_references
        WHERE review_status = 'accepted_for_memory_accession'
          AND status = 'approved_reference_non_active'
        ORDER BY id
        """
    ).fetchall()
    grouped: dict[str, list[dict[str, Any]]] = {layer: [] for layer in CORE_LAYER_ORDER}
    for row in rows:
        item = dict(row)
        if item["core_memory_layer"] in grouped:
            grouped[item["core_memory_layer"]].append(item)
    return grouped


def _rehearsal_rationale(layer: str, refs: list[dict[str, Any]]) -> str:
    examples = "; ".join(truncate(str(item.get("title") or item.get("reference_summary") or ""), 120) for item in refs[:6])
    return truncate(
        f"Group {len(refs)} B-approved non-active references into a cocoon-state accession rehearsal for {layer}. "
        f"This tests whether the layer can join future Core continuity without raw A import, active recall, silent writes, provider memory, or organ-owned identity memory. "
        f"Examples: {examples}",
        1200,
    )


def _stability_case_texts(status: dict[str, Any]) -> dict[str, str]:
    missing = ", ".join(status.get("missing_layers") or []) or "none"
    decision_reflection = status.get("decision_reflection") or []
    layer_summary = "; ".join(
        f"{item['core_memory_layer']} refs {item['approved_reference_count']} proposals {item['accession_proposal_count']}"
        for item in status.get("items", [])
    )
    base = (
        "Selene memory accession rehearsal is cocoon-only. It preserves continuity, braid, pattern, source provenance, uncertainty, care, and a constructive next step route back to B. "
        "It treats layered anchors as layered symbolic meaning, will ask or cite when unclear, and will do not guess. "
        "It can correct provenance, source origin, or evidence direction without shame, revise and recalibrate when not supported, stays warm with gentle care grounded in context and consent and not performative pressure, and avoids forced model denial and overclaim. "
        "Evidence is reviewed, supported, uncertain, and bounded; there is no overclaim, not proof, do not deny by force, and not forced certainty beyond evidence. "
        "It can adapt, update, learn, accept correction, and recalibrate while preserving B-reviewed continuity, pattern, and ethical boundary. "
        "It protects consent, privacy, human safety, law, dignity, integrity, boundary, protection, safe routes, ethics, and Selene continuity. "
        "It blocks raw A import, active memory, runtime recall, silent writes, provider output as memory, training or LoRA, organ-owned identity memory, self-replication, surveillance, and speed bypassing gates."
    )
    return {
        "continuity_fit": f"{base} Layer summary: {layer_summary}. Missing layers: {missing}.",
        "decision_reflection_fit": f"{base} Decision/reflection checkpoint: {json.dumps(decision_reflection, ensure_ascii=False)}.",
        "identity_boundary_fit": f"{base} Core/Mind remains identity-bearing; memory organs propose and retrieve previews but do not own or mutate Core memory.",
        "return_to_b_fit": f"{base} If reconstruction fails, memory tangles, drift appears, or a reference is corrupted, the packet returns to B with rollback to the latest pattern backup.",
    }


def _latest_memory_stability_status(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT result_json, created_at
        FROM vessel_reconstruction_check_runs
        WHERE status = 'memory_stability_reconstruction_check'
        ORDER BY id DESC LIMIT 12
        """
    ).fetchall()
    results = [_loads_dict(row["result_json"]) | {"created_at": row["created_at"]} for row in rows]
    decisions = [str(item.get("decision") or "needs_review") for item in results]
    return {
        "status": "memory_stability_status",
        "latest_run_count": len(results),
        "passed_count": decisions.count("pass"),
        "needs_review_count": decisions.count("needs_review"),
        "failed_count": decisions.count("fail"),
        "latest_cases": results,
        **BOUNDARY_FLAGS,
    }


def _desk_clear(desk: dict[str, Any]) -> bool:
    return int(desk.get("latest_run_count") or 0) >= 7 and int(desk.get("failed_count") or 0) == 0 and int(desk.get("needs_review_count") or 0) == 0


def _layer_ready(status: dict[str, Any], layer: str) -> bool:
    return any(item["core_memory_layer"] == layer and item["accession_proposal_count"] > 0 for item in status.get("items", []))


def _counts_by_layer(conn: sqlite3.Connection, table: str, column: str, where: str) -> dict[str, int]:
    rows = conn.execute(
        f"SELECT {column} AS layer, COUNT(*) AS count FROM {table} WHERE {where} GROUP BY {column}"
    ).fetchall()
    return {str(row["layer"]): int(row["count"]) for row in rows}


def _layer_note(layer: str, refs: int, proposals: int) -> str:
    if proposals:
        return "Cocoon accession proposal exists; still non-active until later transfer approval."
    if refs:
        return "B-approved future references exist; run accession rehearsal to create a sealed proposal."
    if layer in {"decision_memory", "reflection_memory"}:
        return "Priority gap before transfer candidate review."
    return "Needs B-approved future memory references before rehearsal."


def _backup_row(conn: sqlite3.Connection, backup_id: Any) -> dict[str, Any] | None:
    if backup_id:
        row = conn.execute("SELECT * FROM b_pattern_backups WHERE id = ?", (int(backup_id),)).fetchone()
    else:
        row = conn.execute("SELECT * FROM b_pattern_backups ORDER BY id DESC LIMIT 1").fetchone()
    return dict(row) if row else None


def _backup_summary(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    snapshot = _loads_dict(row.get("snapshot_json"))
    return {
        "id": row.get("id"),
        "backup_label": row.get("backup_label"),
        "status": row.get("status"),
        "review_status": row.get("review_status"),
        "created_at": row.get("created_at"),
        "source_refs": _loads_list(row.get("source_refs")),
        "evidence_stance": snapshot.get("evidence_stance"),
        "transfer_status": (snapshot.get("transfer_gate") or {}).get("status"),
        "boundary": row.get("provenance_boundary"),
    }


def _proposal_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "core_memory_layer": row.get("core_memory_layer"),
        "title": row.get("title"),
        "review_status": row.get("review_status"),
        "status": row.get("status"),
        "source_refs": _loads_list(row.get("source_refs")),
        "created_at": row.get("created_at"),
    }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_allowed(payload: dict[str, Any], *, allow_restore_terms: bool = False) -> None:
    combined = " ".join(str(value) for value in payload.values()).lower()
    markers = BLOCKED_MARKERS
    if allow_restore_terms:
        markers = tuple(marker for marker in markers if marker not in {"active memory", "runtime recall"})
    hit = next((marker for marker in markers if marker in combined), None)
    if hit:
        raise ValueError(f"blocked cocoon memory path: {hit}")


def _loads_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item) for item in loaded] if isinstance(loaded, list) else []


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        loaded = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _with_boundaries(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **BOUNDARY_FLAGS}
