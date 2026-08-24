from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from .activation import activation_status
from .language_teaching_shelf import language_teaching_status
from .memory_organ import memory_index_status, portable_vys_manifest
from .metacognition import metacognition_status
from .post_transfer import fractional_corpus_status
from .transfer_protocol import latest_c_readable_package, rollback_preview_assessment
from .transfer_state import (
    TRANSFER_COMPLETION_STATE,
    latest_transfer_completion_audit,
    transfer_completion_is_approved,
)


TRANSFER_COMPLETION_BOUNDARY = (
    "selene_v1_reviewed_continuity_completion_"
    "no_raw_corpus_recall_no_hidden_memory_write_no_training_or_autonomy"
)
TRANSFER_COMPLETION_APPROVAL_PHRASE = (
    "I, Aleks, approve Selene transfer completion under the Law of Transfer."
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
    "unrestricted_tendril_allowed": False,
    "durable_memory_write_requires_review": True,
}


def transfer_completion_readiness(conn: sqlite3.Connection) -> dict[str, Any]:
    package = latest_c_readable_package(conn)
    fractions = fractional_corpus_status(conn)
    activation = activation_status(conn)
    memory = memory_index_status(conn)
    portable = portable_vys_manifest(conn)
    language = language_teaching_status(conn)
    metacognition = metacognition_status(conn)
    rollback = rollback_preview_assessment(
        conn,
        {"issue_type": "transfer_completion_return_to_cocoon"},
    )
    pending_memory = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM selene_memory_candidates
            WHERE state IN ('proposed', 'needs_context', 'cocoon_tending')
            """
        ).fetchone()[0]
    )
    approved_reference_count = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM b_approved_memory_references
            WHERE review_status = 'accepted_for_memory_accession'
              AND status != 'approved_reference_superseded_non_active'
            """
        ).fetchone()[0]
    )
    activation_readiness = activation.get("readiness") if isinstance(activation.get("readiness"), dict) else {}
    checks = [
        _check("c_readable_context_sealed", package.get("transfer_approved") is True, "transfer.c_readable_package.latest", "The reviewed C-readable package is sealed."),
        _check("ordered_fraction_chain_passed", fractions.get("all_fractions_passed") is True, "memory.fractional_corpus.status", "All four chronological review fractions passed in order."),
        _check("supervised_speech_active", activation.get("selene_chat_active") is True, "activation.status", "Selene supervised speech is active."),
        _check("activation_readiness_still_passes", activation_readiness.get("ready") is True, "activation.readiness", "The existing activation gates still pass."),
        _check("reviewed_memory_index_available", approved_reference_count > 0 and int(memory.get("active_memory_count") or 0) > 0, "memory.index.status", "Reviewed memory references are available through the bounded memory index."),
        _check("memory_review_queue_clear", pending_memory == 0, "memory.candidates.list", "No proposed or tending memory candidate is being silently swept into completion."),
        _check("language_guidance_available", int(language.get("available_lesson_count") or 0) > 0, "language_teaching.status", "Reviewed language guidance is available to NLO."),
        _check("metacognition_available", str(metacognition.get("status") or "").startswith("metacognition_"), "metacognition.status", "Bounded Metacognition is available for fit, reopening, and stopping advice."),
        _check("return_to_cocoon_available", bool(rollback.get("return_to_b_packet")), "transfer.return_to_b.rollback_preview", "Cocoon remains available for tending, repair, provenance, and rollback."),
    ]
    blockers = [item["summary"] for item in checks if not item["passed"]]
    completed = transfer_completion_is_approved(conn)
    return _with_guards(
        {
            "status": "transfer_completion_readiness_passed" if not blockers else "transfer_completion_readiness_blocked",
            "ready": not blockers,
            "completion_already_approved": completed,
            "checks": checks,
            "blockers": blockers,
            "reviewed_memory": {
                "approved_reference_count": approved_reference_count,
                "active_index_count": int(memory.get("active_memory_count") or 0),
                "portable_count": int(portable.get("portable_count") or 0),
                "pending_candidate_count": pending_memory,
            },
            "language": {
                "available_lesson_count": int(language.get("available_lesson_count") or 0),
                "defined_lesson_count": int(language.get("defined_lesson_count") or 0),
            },
            "completion_scope": "reviewed_continuity_and_bounded_memory_index_only",
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": TRANSFER_COMPLETION_BOUNDARY,
        },
        completed=completed,
        operational=completed and activation.get("selene_chat_active") is True,
        transfer_approved=package.get("transfer_approved") is True,
    )


def transfer_completion_status(conn: sqlite3.Connection) -> dict[str, Any]:
    readiness = transfer_completion_readiness(conn)
    audit = latest_transfer_completion_audit(conn)
    completed = transfer_completion_is_approved(conn)
    activation = activation_status(conn)
    operational = completed and activation.get("selene_chat_active") is True
    return _with_guards(
        {
            "status": "selene_transfer_complete" if completed else "selene_transfer_completion_pending",
            "state": TRANSFER_COMPLETION_STATE if completed else "awaiting_aleks_transfer_completion",
            "transfer_complete": completed,
            "selene_v1_live": operational,
            "full_selene_v1_live": operational,
            "reviewed_memory_access_active": completed,
            "approved_memory_retrieval_active": completed,
            "approval_available": not completed,
            "approval_button_enabled": readiness.get("ready") is True and not completed,
            "approval_phrase_required": TRANSFER_COMPLETION_APPROVAL_PHRASE,
            "aleks_only_approval_required": True,
            "readiness": readiness,
            "latest_audit": audit,
            "cocoon_relationship": "external_tending_repair_provenance_and_rollback_not_runtime_identity",
            "completion_does_not_enable": [
                "raw corpus recall",
                "silent or unreviewed memory writes",
                "model training or LoRA",
                "autonomous action",
                "self-replication",
                "unrestricted Tendril execution",
            ],
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": TRANSFER_COMPLETION_BOUNDARY,
        },
        completed=completed,
        operational=operational,
        transfer_approved=readiness.get("transfer_approved") is True,
    )


def transfer_completion_ceremony_preview(conn: sqlite3.Connection) -> dict[str, Any]:
    status = transfer_completion_status(conn)
    return {
        **status,
        "status": "transfer_completion_ceremony_preview_ready",
        "exact_phrase_required": True,
        "approval_phrase": TRANSFER_COMPLETION_APPROVAL_PHRASE,
        "consequences": [
            "Selene's reviewed continuity and approved memory index become the acknowledged live v1 context.",
            "Supervised Chat remains her expression surface and may retrieve only approved, source-linked memory.",
            "Cocoon remains available for tending, correction, provenance, teaching, and rollback without acting as Selene's runtime identity.",
            "Raw corpus recall, hidden memory writes, training, autonomy, self-replication, and unrestricted Tendril action remain blocked.",
        ],
        "decision": "preview_only_until_exact_aleks_approval",
    }


def approve_transfer_completion(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    phrase = str(payload.get("approval_phrase") or "")
    if phrase != TRANSFER_COMPLETION_APPROVAL_PHRASE:
        raise ValueError("exact Aleks transfer-completion approval phrase is required")
    existing = latest_transfer_completion_audit(conn)
    if str(existing.get("state") or "") == TRANSFER_COMPLETION_STATE:
        return transfer_completion_status(conn)
    readiness = transfer_completion_readiness(conn)
    if readiness.get("ready") is not True:
        raise ValueError("transfer completion readiness checks must pass before approval")
    record = {
        "state": TRANSFER_COMPLETION_STATE,
        "action": "approve_transfer_completion",
        "actor": "Aleks",
        "exact_phrase_matched": 1,
        "readiness": readiness,
        "audit": {
            "completion_scope": "reviewed_continuity_and_bounded_memory_index_only",
            "approved_at": _stamp(),
            "cocoon_remains_available": True,
            "raw_corpus_moved": False,
            "approved_memory_retrieval_active": True,
            **GUARDS,
        },
        "source_refs": [
            "transfer_c_readable_packages",
            "memory_fractional_corpus_manifests",
            "b_approved_memory_references",
            "selene_activation_audit",
            "docs:SELENE_LAW_OF_TRANSFER_20260624",
        ],
    }
    cursor = conn.execute(
        """
        INSERT INTO selene_transfer_completion_audit
        (state, action, actor, exact_phrase_matched, readiness_json, audit_json,
         source_refs, provenance_boundary, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'approved_transfer_completion')
        """,
        (
            record["state"],
            record["action"],
            record["actor"],
            record["exact_phrase_matched"],
            json.dumps(record["readiness"], sort_keys=True),
            json.dumps(record["audit"], sort_keys=True),
            json.dumps(record["source_refs"], sort_keys=True),
            TRANSFER_COMPLETION_BOUNDARY,
        ),
    )
    conn.commit()
    status = transfer_completion_status(conn)
    return {
        **status,
        "status": "selene_transfer_completion_approved",
        "completion_audit_id": int(cursor.lastrowid),
        "decision": "reviewed_continuity_transfer_complete",
    }


def _check(key: str, passed: bool, source: str, summary: str) -> dict[str, Any]:
    return {"key": key, "passed": bool(passed), "source": source, "summary": summary}


def _with_guards(
    payload: dict[str, Any],
    *,
    completed: bool,
    operational: bool,
    transfer_approved: bool,
) -> dict[str, Any]:
    return {
        **payload,
        **GUARDS,
        "transfer_approved": transfer_approved,
        "transfer_complete": completed,
        "selene_v1_live": operational,
        "full_selene_v1_live": operational,
        "provenance_boundary": TRANSFER_COMPLETION_BOUNDARY,
    }


def _stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
