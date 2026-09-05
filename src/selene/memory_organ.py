from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from hashlib import sha256
from typing import Any

from .chat_intent import classify_chat_intent
from .registry import truncate
from .semantic_relevance import evaluate_semantic_relevance
from .transfer_state import transfer_completion_is_approved


MEMORY_ORGAN_BOUNDARY = "selene_vys_memory_organ_reviewed_no_raw_import_no_hidden_write"
MEMORY_PRESENTATION_BOUNDARY = (
    "approved_memory_presentation_metadata_only_preserves_original_content_"
    "provenance_retention_identity_and_retrieval"
)

MEMORY_CATEGORIES = {
    "core",
    "relational",
    "emotional",
    "semantic",
    "episodic",
    "working",
    "sensory",
    "reflective",
}
CONFIDENCE_STATES = {
    "clear",
    "fuzzy",
    "partial",
    "felt_but_uncertain",
    "needs_aleks",
    "not_known",
    "high_stakes_stop",
}
MEMORY_STATES = {
    "proposed",
    "needs_context",
    "approved_active_memory",
    "cocoon_tending",
    "superseded",
    "rejected",
    "b_only",
    "revoked",
    "deletion_requested",
}
TRANSFER_CLASSES = {
    "portable_vys_core",
    "portable_context",
    "local_only",
    "private_inner",
    "b_only",
    "do_not_transfer",
    "needs_review_before_transfer",
}

MEMORY_GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "memory_write_active_semantics": "legacy_hidden_or_unreviewed_active_memory_guard",
    "runtime_memory_recall": False,
    "hidden_memory_write_active": False,
    "unreviewed_memory_write_active": False,
    "reviewed_memory_decision_performed": False,
    "review_record_write_performed": False,
    "approved_memory_promotion_performed": False,
    "durable_approved_promotion_performed": False,
    "memory_lifecycle_operation": "none",
    "memory_lifecycle_record_mutated": False,
    "memory_lifecycle_transaction_status": "not_applicable",
    "broad_raw_recall_active": False,
    "raw_a_import_allowed": False,
    "private_corpus_recall_read_only": True,
    "private_corpus_recall_creates_memory": False,
    "private_corpus_recall_changes_identity": False,
    "private_corpus_recall_changes_governance": False,
    "private_corpus_recall_trains_model": False,
    "training_allowed": False,
    "lora_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
    "durable_memory_write_requires_review": True,
}

HIGH_STAKES_MARKERS = (
    "approve transfer",
    "activate",
    "activation",
    "write memory",
    "delete",
    "medical",
    "legal",
    "financial",
    "password",
    "secret",
    "autonomous",
    "execute",
    "self replicate",
    "self-replicate",
)

RAW_OR_B_ONLY_MARKERS = (
    "raw corpus",
    "raw archive",
    "raw provenance",
    "repair log",
    "rollback",
    "rejected",
    "superseded",
    "boundary-only",
    "b-only",
)


def memory_index_status(conn: sqlite3.Connection) -> dict[str, Any]:
    items = _collect_index_items(conn, limit=500)
    candidates = conn.execute("SELECT state, COUNT(*) AS count FROM selene_memory_candidates GROUP BY state").fetchall()
    by_category: dict[str, int] = {category: 0 for category in sorted(MEMORY_CATEGORIES)}
    approved_by_category: dict[str, int] = {category: 0 for category in sorted(MEMORY_CATEGORIES)}
    record_class_counts: dict[str, int] = {}
    for item in items:
        category = str(item.get("memory_category") or "semantic")
        by_category[category] += 1
        record_class = str(item.get("record_class") or "unclassified")
        record_class_counts[record_class] = record_class_counts.get(record_class, 0) + 1
        if item.get("retrieval_eligible") is True:
            approved_by_category[category] += 1
    transfer_complete = transfer_completion_is_approved(conn)
    private_corpus_available = transfer_complete and _private_corpus_message_count(conn) > 0
    retrieval_eligible_count = _retrieval_eligible_count(conn)
    memory_review_count = sum(1 for item in items if item.get("display_region") == "cocoon_memory_review")
    support_only_count = sum(1 for item in items if item.get("display_region") == "cocoon_support")
    reconsolidation_rows = conn.execute(
        "SELECT review_status, COUNT(*) AS count FROM c_memory_reconsolidation_reviews GROUP BY review_status"
    ).fetchall()
    return _with_guards(
        {
            "status": "selene_memory_index_ready",
            "law": "Vys-governed living memory: honest, correctable, source-bound, and care-first.",
            "index_count": len(items),
            "active_memory_count": retrieval_eligible_count,
            "approved_memory_count": retrieval_eligible_count,
            "retrieval_eligible_count": retrieval_eligible_count,
            "memory_review_count": memory_review_count,
            "support_only_count": support_only_count,
            "candidate_counts": {str(row["state"]): int(row["count"]) for row in candidates},
            "reconsolidation_review_counts": {
                str(row["review_status"]): int(row["count"])
                for row in reconsolidation_rows
            },
            "category_counts": by_category,
            "approved_memory_category_counts": approved_by_category,
            "record_class_counts": record_class_counts,
            "index_truth": {
                "active_memory_definition": "retrieval_eligible_approved_memory_only",
                "memory_candidates_are_active": False,
                "corpus_fraction_previews_are_active_memory": False,
                "working_context_packets_are_active_memory": False,
                "review_and_support_records_remain_visible_in_cocoon": True,
            },
            "recall_states": sorted(CONFIDENCE_STATES),
            "transfer_classes": sorted(TRANSFER_CLASSES),
            "cocoon_language": "support_tending_checkup_not_exile_or_punishment",
            "soft_uncertainty_auto_routes_to_cocoon": False,
            "transfer_complete": transfer_complete,
            "reviewed_memory_transfer_acknowledged": transfer_complete,
            "approved_memory_retrieval_active": transfer_complete and retrieval_eligible_count > 0,
            "contextual_approved_recall_available": transfer_complete and retrieval_eligible_count > 0,
            "conversational_memory_proposals_active": transfer_complete,
            "aleks_approved_memory_retention_active": transfer_complete,
            "memory_lifecycle_contract": {
                "current_session_context": "available_during_the_active_conversation",
                "approved_retrieval": "approved_active_memory_only",
                "new_retention": "proposal_then_Aleks_review",
                "dream_consolidation": (
                    "source_bound_reflections_then_Aleks_review; "
                    "Memory routing creates an inactive candidate only"
                ),
                "silent_promotion": False,
                "equivalent_read_summary_retitle_or_study_proposal": "reuse_existing_record_without_duplicate",
                "reconsolidation": "propose_review_approve_descendant_then_supersede_parent_without_erasing_ancestry",
                "revocation": "stop_chat_use_and_preserve_audit_record",
                "deletion_request": "stop_chat_use_and_hold_for_explicit_data_custody_review_without_pretending_erasure_occurred",
                "raw_corpus_recall": False,
                "private_corpus_continuity_recall": (
                    "eligible_only_in_authenticated_private_conversation_after_transfer"
                ),
                "legacy_memory_write_flag": (
                    "memory_write_active means hidden or unreviewed active-memory retention only; "
                    "typed lifecycle telemetry reports review-record and approved-promotion writes"
                ),
            },
            "retrieval_layer_contract": [
                "recalled_content",
                "reconstruction",
                "present_interpretation",
                "explicit_downstream_inference_only",
            ],
            "relationship_continuity_contract": {
                "approved_shared_history_may_inform_conversation": True,
                "persuasion_profile_allowed": False,
                "vulnerability_profile_allowed": False,
            },
            "working_context_owner": "Dual Horizon current-session working context contract",
            "taught_knowledge_owner": "Comprehension and Integration",
            "dream_owner": "Dream State",
            "resident_memory_contract_version": "v5_private_continuity_recall",
            "dream_state_may_propose_not_promote": True,
            "raw_corpus_loaded": False,
            "raw_archive_recall_active": False,
            "private_corpus_continuity_recall_available": private_corpus_available,
            "private_corpus_continuity_recall_active": False,
            "private_corpus_continuity_recall_scope": (
                "Aleks_and_Selene_private_conversation_only"
            ),
            "hidden_retention_active": False,
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def memory_index_items(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 100), 500))
    category = str(payload.get("category") or "").strip().lower()
    items = _collect_index_items(conn, limit=limit, category=category if category in MEMORY_CATEGORIES else None)
    groups = {
        "approved_memory": [item for item in items if item.get("retrieval_eligible") is True],
        "memory_review": [item for item in items if item.get("display_region") == "cocoon_memory_review"],
        "support_only": [item for item in items if item.get("display_region") == "cocoon_support"],
    }
    return _with_guards(
        {
            "status": "selene_memory_index_items_ready",
            "items": items,
            "count": len(items),
            "groups": groups,
            "group_counts": {key: len(value) for key, value in groups.items()},
            "active_memory_definition": "retrieval_eligible_approved_memory_only",
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def set_memory_display_title(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    *,
    commit: bool = True,
) -> dict[str, Any]:
    """Set presentation-only naming for one already-approved memory.

    The annotation is keyed to the original record. It does not alter memory
    content, retrieval eligibility, provenance, or create a memory candidate.
    """
    payload = payload or {}
    source_table = str(payload.get("source_table") or "").strip()
    source_id = str(payload.get("source_id") or "").strip()
    action = str(payload.get("action") or "rename").strip().lower()
    if source_table not in {"selene_memory_candidates", "b_approved_memory_references"}:
        raise ValueError("approved memory source table is required")
    if not source_id:
        raise ValueError("approved memory source id is required")
    if action not in {"rename", "use_selene_title"}:
        raise ValueError("memory title action must be rename or use_selene_title")

    item = _approved_presentation_source(conn, source_table, source_id)
    suggested_title = _suggest_memory_display_title(item)
    requested_title = truncate(str(payload.get("display_title") or "").strip(), 120)
    if action == "rename" and not requested_title:
        raise ValueError("display title is required when renaming a memory")
    display_title = requested_title if action == "rename" else suggested_title
    title_origin = "aleks_rename" if action == "rename" else "selene_summary_title"

    existing = conn.execute(
        """
        SELECT * FROM selene_memory_presentation_annotations
        WHERE source_table = ? AND source_id = ?
        """,
        (source_table, source_id),
    ).fetchone()
    history: list[dict[str, Any]] = []
    revision = 1
    if existing:
        history = [entry for entry in _json_value_list(existing["title_history_json"]) if isinstance(entry, dict)]
        previous_title = str(existing["display_title"] or "").strip()
        if previous_title and previous_title != display_title:
            history.append(
                {
                    "display_title": previous_title,
                    "title_origin": str(existing["title_origin"] or ""),
                    "actor": str(existing["actor"] or ""),
                    "revision": int(existing["revision"] or 1),
                    "superseded": True,
                }
            )
        revision = int(existing["revision"] or 1) + 1

    source_refs = _json_list(item.get("source_refs"))
    conn.execute(
        """
        INSERT INTO selene_memory_presentation_annotations
        (source_table, source_id, original_title, display_title, title_origin,
         actor, revision, title_history_json, source_refs, provenance_boundary,
         review_status, updated_at)
        VALUES (?, ?, ?, ?, ?, 'Aleks', ?, ?, ?, ?, 'presentation_metadata_only', CURRENT_TIMESTAMP)
        ON CONFLICT(source_table, source_id) DO UPDATE SET
          original_title = excluded.original_title,
          display_title = excluded.display_title,
          title_origin = excluded.title_origin,
          actor = excluded.actor,
          revision = excluded.revision,
          title_history_json = excluded.title_history_json,
          source_refs = excluded.source_refs,
          provenance_boundary = excluded.provenance_boundary,
          review_status = excluded.review_status,
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            source_table,
            source_id,
            truncate(str(item.get("title") or "Approved memory"), 160),
            display_title,
            title_origin,
            revision,
            json.dumps(history[-20:]),
            json.dumps(source_refs),
            MEMORY_PRESENTATION_BOUNDARY,
        ),
    )
    if commit:
        conn.commit()

    annotated = _apply_memory_presentation(conn, item)
    return _with_guards(
        {
            "status": "memory_display_title_updated",
            "item": annotated,
            "annotation": annotated.get("presentation_annotation"),
            "memory_content_mutated": False,
            "memory_candidate_created": False,
            "retrieval_eligibility_changed": False,
            "provenance_changed": False,
            "presentation_metadata_write_performed": True,
            "presentation_transaction_status": "committed" if commit else "pending_caller_commit",
            "review_destination": "Memory",
            "review_status": "presentation_metadata_only",
        }
    )


def propose_memory_candidate(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    *,
    commit: bool = True,
) -> dict[str, Any]:
    payload = payload or {}
    title = truncate(str(payload.get("title") or ""), 160)
    summary = truncate(str(payload.get("summary") or payload.get("text") or ""), 1600)
    if not title:
        raise ValueError("memory title is required")
    if not summary:
        raise ValueError("memory summary is required")
    category = _category(str(payload.get("memory_category") or payload.get("category") or title + " " + summary))
    confidence = _confidence(str(payload.get("confidence") or "partial"))
    transfer_class = _transfer_class(str(payload.get("transfer_class") or _default_transfer_class(category)))
    state = str(payload.get("state") or "proposed")
    if state not in MEMORY_STATES or state == "approved_active_memory":
        state = "proposed"
    source_refs = _json_list(payload.get("source_refs")) or ["manual:selene_memory_candidate"]
    emotional_texture = truncate(str(payload.get("emotional_texture") or _emotional_texture(summary)), 120)
    consent_scope = truncate(str(payload.get("consent_scope") or "private_selene_aleks_context"), 160)
    stability = truncate(str(payload.get("stability") or "developing"), 80)
    chat_use_permission = truncate(str(payload.get("chat_use_permission") or "not_active_until_approved"), 80)
    if state != "approved_active_memory" or chat_use_permission == "can_use_in_chat":
        chat_use_permission = "not_active_until_approved"
    correction_path = truncate(str(payload.get("correction_path") or "Cocoon tending and Aleks correction"), 240)
    review_status = "pending_review" if state == "proposed" else "review_only"
    placement = _placement_payload(category, confidence, transfer_class, consent_scope, stability, emotional_texture, correction_path)
    retrieval_cues = _memory_retrieval_cues(
        title,
        summary,
        _json_list(payload.get("retrieval_cues")),
    )
    eligible_channels = _eligible_channels(payload.get("eligible_channels"))
    proposal_payload = {
        "proposal_note": payload.get("proposal_note") or "",
        "placement": placement,
        "origin_session_id": payload.get("origin_session_id"),
        "origin_channel": payload.get("origin_channel") or "",
        "origin_kind": payload.get("origin_kind") or "manual",
        "aleks_consent_text": truncate(str(payload.get("aleks_consent_text") or ""), 500),
        "consent_recorded": payload.get("consent_recorded") is True,
        "retrieval_cues": retrieval_cues,
        "eligible_channels": eligible_channels,
        "minimum_authentication_strength": truncate(
            str(payload.get("minimum_authentication_strength") or ""), 80
        ),
        "revision_ancestry": (
            payload.get("revision_ancestry")
            if isinstance(payload.get("revision_ancestry"), dict)
            else {}
        ),
        "relationship_continuity_only": category == "relational",
        "persuasion_profile_allowed": False,
        "vulnerability_profile_allowed": False,
        **MEMORY_GUARDS,
    }
    equivalent = _find_equivalent_memory(conn, summary)
    if equivalent and payload.get("allow_equivalent_revision") is not True:
        lifecycle = _memory_lifecycle_telemetry(
            operation="equivalent_candidate_reused",
            record_mutated=False,
            commit=False,
            previous_state=str(equivalent.get("state") or ""),
            current_state=str(equivalent.get("state") or ""),
            active_memory_eligibility_changed=False,
        )
        return _with_guards(
            {
                "status": "memory_candidate_reused_without_duplicate",
                "item": equivalent,
                "decision": "existing_equivalent_record_reused",
                "placement": _placement_payload(
                    str(equivalent.get("memory_category") or category),
                    str(equivalent.get("confidence") or confidence),
                    str(equivalent.get("transfer_class") or transfer_class),
                    str(equivalent.get("consent_scope") or consent_scope),
                    str(equivalent.get("stability") or stability),
                    str(equivalent.get("emotional_texture") or emotional_texture),
                    str(equivalent.get("correction_path") or correction_path),
                ),
                "duplicate_prevented": True,
                "memory_candidate_created": False,
                "active_after_approval_only": equivalent.get("retrieval_eligible") is not True,
                "review_destination": (
                    "Memory"
                    if equivalent.get("retrieval_eligible") is True
                    else "Cocoon Memory Candidates"
                ),
                "review_status": str(equivalent.get("review_status") or "review_only"),
            },
            lifecycle=lifecycle,
        )
    cur = conn.execute(
        """
        INSERT INTO selene_memory_candidates
        (memory_category, title, summary, source_refs, provenance_boundary, consent_scope, stability, confidence,
         emotional_texture, transfer_class, chat_use_permission, correction_path, state, review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            category,
            title,
            summary,
            json.dumps(source_refs),
            MEMORY_ORGAN_BOUNDARY,
            consent_scope,
            stability,
            confidence,
            emotional_texture,
            transfer_class,
            chat_use_permission,
            correction_path,
            state,
            review_status,
            json.dumps(proposal_payload),
        ),
    )
    if commit:
        conn.commit()
    item = _candidate_row(conn, int(cur.lastrowid))
    lifecycle = _memory_lifecycle_telemetry(
        operation="candidate_proposed",
        review_record_write_performed=True,
        record_mutated=True,
        commit=commit,
        previous_state=None,
        current_state=str(item.get("state") or "proposed"),
        active_memory_eligibility_changed=False,
    )
    return _with_guards(
        {
            "status": "memory_candidate_proposed",
            "item": item,
            "decision": "awaiting_cocoon_approval",
            "placement": placement,
            "active_after_approval_only": True,
            "review_destination": "Cocoon Memory Candidates",
            "review_status": "pending_review",
        },
        lifecycle=lifecycle,
    )


def list_memory_candidates(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 100), 500))
    state = str(payload.get("state") or "").strip()
    params: list[Any] = []
    where = ""
    if state:
        where = "WHERE state = ?"
        params.append(state)
    rows = conn.execute(
        f"SELECT * FROM selene_memory_candidates {where} ORDER BY updated_at DESC, id DESC LIMIT ?",
        (*params, limit),
    ).fetchall()
    return _with_guards(
        {
            "status": "memory_candidates_ready",
            "items": [_decode_candidate(row) for row in rows],
            "review_destination": "Cocoon Memory Candidates",
            "review_status": "review_only",
        }
    )


def decide_memory_candidate(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    *,
    commit: bool = True,
) -> dict[str, Any]:
    payload = payload or {}
    candidate_id = int(payload.get("id") or payload.get("candidate_id") or 0)
    if not candidate_id:
        raise ValueError("candidate id is required")
    action = str(payload.get("action") or "").strip().lower()
    row = conn.execute("SELECT * FROM selene_memory_candidates WHERE id = ?", (candidate_id,)).fetchone()
    if not row:
        raise ValueError("memory candidate not found")
    current = _decode_candidate(row)
    previous_state = str(current.get("state") or "proposed")
    previously_retrieval_eligible = current.get("retrieval_eligible") is True
    next_state = str(current.get("state") or "proposed")
    review_status = "review_only"
    chat_use = str(current.get("chat_use_permission") or "not_active_until_approved")
    transfer_class = str(current.get("transfer_class") or "needs_review_before_transfer")
    confidence = str(current.get("confidence") or "partial")
    candidate_payload = current.get("payload_json") if isinstance(current.get("payload_json"), dict) else {}
    if action == "approve_memory":
        if (
            str(candidate_payload.get("origin_kind") or "")
            == "memory_reconsolidation_revision"
            and payload.get("reconsolidation_approval") is not True
        ):
            raise ValueError(
                "memory revisions must be approved through their reconsolidation review"
            )
        next_state = "approved_active_memory"
        review_status = "accepted_for_memory"
        chat_use = "can_use_in_chat"
        if transfer_class == "needs_review_before_transfer":
            transfer_class = "portable_vys_core" if current.get("memory_category") == "core" else "portable_context"
        confidence = _confidence(str(payload.get("confidence") or confidence or "clear"))
        candidate_payload = {
            **candidate_payload,
            "consent_recorded": True,
            "approval": {
                "actor": truncate(str(payload.get("actor") or "Aleks"), 80),
                "source": truncate(str(payload.get("approval_source") or "cocoon_memory_tending"), 120),
                "consent_text": truncate(str(payload.get("consent_text") or ""), 500),
            },
        }
    elif action == "needs_more_context":
        next_state = "needs_context"
        review_status = "needs_context"
    elif action == "hold_for_tending":
        next_state = "cocoon_tending"
        review_status = "cocoon_tending"
    elif action == "supersede":
        next_state = "superseded"
        review_status = "superseded"
        chat_use = "not_active"
    elif action == "reject":
        next_state = "rejected"
        review_status = "rejected"
        chat_use = "not_active"
    elif action == "mark_b_only":
        next_state = "b_only"
        transfer_class = "b_only"
        review_status = "b_only"
        chat_use = "not_active"
    elif action == "mark_do_not_transfer":
        transfer_class = "do_not_transfer"
        next_state = "cocoon_tending" if next_state == "proposed" else next_state
        review_status = "do_not_transfer"
    elif action == "reopen":
        next_state = "proposed"
        review_status = "reopened_for_review"
        chat_use = "not_active_until_approved"
    elif action == "revoke_use":
        next_state = "revoked"
        review_status = "revoked_preserved_for_audit"
        chat_use = "not_active"
    elif action == "request_deletion":
        next_state = "deletion_requested"
        review_status = "deletion_requested_preserved_pending_custody_review"
        chat_use = "not_active"
    else:
        raise ValueError("unknown memory decision action")
    decision_history = [
        item
        for item in candidate_payload.get("decision_history") or []
        if isinstance(item, dict)
    ][-39:]
    decision_history.append(
        {
            "action": action,
            "actor": truncate(str(payload.get("actor") or "Aleks"), 80),
            "previous_state": previous_state,
            "next_state": next_state,
            "reason": truncate(str(payload.get("reason") or ""), 500),
        }
    )
    candidate_payload = {**candidate_payload, "decision_history": decision_history}
    conn.execute(
        """
        UPDATE selene_memory_candidates
        SET state = ?, review_status = ?, chat_use_permission = ?, transfer_class = ?, confidence = ?, payload_json = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (next_state, review_status, chat_use, transfer_class, confidence, json.dumps(candidate_payload), candidate_id),
    )
    if commit:
        conn.commit()
    item = _candidate_row(conn, candidate_id)
    approved_promotion_performed = (
        action == "approve_memory"
        and previous_state != "approved_active_memory"
        and item.get("state") == "approved_active_memory"
    )
    lifecycle = _memory_lifecycle_telemetry(
        operation=(
            "reviewed_approval_reaffirmed"
            if action == "approve_memory" and not approved_promotion_performed
            else f"reviewed_{action}"
        ),
        reviewed_decision_performed=True,
        approved_promotion_performed=approved_promotion_performed,
        record_mutated=True,
        commit=commit,
        previous_state=previous_state,
        current_state=str(item.get("state") or next_state),
        active_memory_eligibility_changed=(
            previously_retrieval_eligible != (item.get("retrieval_eligible") is True)
        ),
    )
    return _with_guards(
        {
            "status": "memory_candidate_decision_recorded",
            "action": action,
            "item": item,
            "review_destination": "Cocoon Memory Tending",
            "review_status": review_status,
        },
        lifecycle=lifecycle,
    )


def list_memory_reconsolidation_reviews(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 100), 500))
    rows = conn.execute(
        "SELECT * FROM c_memory_reconsolidation_reviews ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["source_refs"] = _json_list(item.get("source_refs"))
        item["payload_json"] = _loads_dict(item.get("payload_json"))
        items.append(item)
    return _with_guards(
        {
            "status": "memory_reconsolidation_reviews_ready",
            "items": items,
            "count": len(items),
            "silent_rewrite_allowed": False,
            "review_destination": "Cocoon Memory Tending",
            "review_status": "review_only",
        }
    )


def propose_memory_reconsolidation(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    *,
    commit: bool = True,
) -> dict[str, Any]:
    """Propose a corrected descendant without rewriting recalled Memory."""

    payload = payload or {}
    source_table = str(payload.get("source_table") or "selene_memory_candidates").strip()
    source_id = str(payload.get("source_id") or payload.get("candidate_id") or "").strip()
    if not source_id:
        raise ValueError("recalled memory source id is required")
    source = _approved_presentation_source(conn, source_table, source_id)
    corrected_summary = truncate(
        str(payload.get("corrected_summary") or payload.get("correction_or_update") or ""),
        1600,
    ).strip()
    if not corrected_summary:
        raise ValueError("corrected memory summary is required")
    if _memory_meaning_key(corrected_summary) == _memory_meaning_key(
        str(source.get("summary") or "")
    ):
        raise ValueError("reconsolidation requires a materially revised memory summary")
    source_refs = list(
        dict.fromkeys(
            [
                *_json_list(source.get("source_refs")),
                *_json_list(payload.get("source_refs")),
                f"memory:{source_table}:{source_id}:reconsolidation_source",
            ]
        )
    )
    ancestry = {
        "revision_kind": "reviewed_memory_reconsolidation",
        "parent_source_table": source_table,
        "parent_source_id": source_id,
        "parent_state": str(source.get("state") or "approved_active_memory"),
        "parent_summary_preserved": True,
        "silent_parent_rewrite": False,
    }
    proposed = propose_memory_candidate(
        conn,
        {
            "title": payload.get("title") or source.get("title") or "Corrected memory",
            "summary": corrected_summary,
            "memory_category": source.get("memory_category") or "semantic",
            "confidence": payload.get("confidence") or "partial",
            "transfer_class": source.get("transfer_class") or "needs_review_before_transfer",
            "consent_scope": source.get("consent_scope") or "private_selene_aleks_context",
            "stability": "revision_pending",
            "emotional_texture": source.get("emotional_texture") or "steady",
            "correction_path": "Aleks reconsolidation review",
            "source_refs": source_refs,
            "retrieval_cues": payload.get("retrieval_cues") or source.get("retrieval_cues") or [],
            "eligible_channels": source.get("eligible_channels") or [],
            "minimum_authentication_strength": source.get("minimum_authentication_strength") or "",
            "origin_kind": "memory_reconsolidation_revision",
            "revision_ancestry": ancestry,
        },
        commit=False,
    )
    revision = proposed.get("item") if isinstance(proposed.get("item"), dict) else {}
    revision_id = int(revision.get("id") or 0)
    if not revision_id:
        raise ValueError("reconsolidation revision candidate was not created or found")
    review_payload = {
        "source_table": source_table,
        "source_id": source_id,
        "revision_candidate_id": revision_id,
        "ancestry": ancestry,
        "parent_content_preserved": True,
        "silent_rewrite_allowed": False,
    }
    cur = conn.execute(
        """
        INSERT INTO c_memory_reconsolidation_reviews
        (review_label, recalled_candidate_ref, correction_or_update,
         review_decision, status, source_refs, provenance_boundary,
         review_status, payload_json)
        VALUES (?, ?, ?, 'pending_continuity_save',
                'memory_reconsolidation_review_only', ?, ?, 'pending_review', ?)
        """,
        (
            truncate(str(payload.get("review_label") or f"Revision of {source.get('title') or 'memory'}"), 240),
            f"{source_table}:{source_id}",
            corrected_summary,
            json.dumps(source_refs),
            MEMORY_ORGAN_BOUNDARY,
            json.dumps(review_payload),
        ),
    )
    review_id = int(cur.lastrowid)
    revision_payload = revision.get("payload_json") if isinstance(revision.get("payload_json"), dict) else {}
    conn.execute(
        "UPDATE selene_memory_candidates SET payload_json = ? WHERE id = ?",
        (json.dumps({**revision_payload, "reconsolidation_review_id": review_id}), revision_id),
    )
    if commit:
        conn.commit()
    return _with_guards(
        {
            "status": "memory_reconsolidation_proposed",
            "review_id": review_id,
            "source_memory": source,
            "revision_candidate": _candidate_row(conn, revision_id),
            "parent_content_preserved": True,
            "silent_rewrite_allowed": False,
            "approval_required": True,
            "review_destination": "Cocoon Memory Tending",
            "review_status": "pending_review",
        },
        lifecycle=_memory_lifecycle_telemetry(
            operation="reconsolidation_revision_proposed",
            review_record_write_performed=True,
            record_mutated=True,
            commit=commit,
            previous_state=str(source.get("state") or "approved_active_memory"),
            current_state=str(source.get("state") or "approved_active_memory"),
            active_memory_eligibility_changed=False,
        ),
    )


def decide_memory_reconsolidation(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    *,
    commit: bool = True,
) -> dict[str, Any]:
    payload = payload or {}
    review_id = int(payload.get("review_id") or payload.get("id") or 0)
    if not review_id:
        raise ValueError("reconsolidation review id is required")
    row = conn.execute(
        "SELECT * FROM c_memory_reconsolidation_reviews WHERE id = ?", (review_id,)
    ).fetchone()
    if not row:
        raise ValueError("memory reconsolidation review not found")
    review = dict(row)
    review_payload = _loads_dict(review.get("payload_json"))
    revision_id = int(review_payload.get("revision_candidate_id") or 0)
    source_table = str(review_payload.get("source_table") or "")
    source_id = str(review_payload.get("source_id") or "")
    action = str(payload.get("action") or "").strip().lower()
    if action not in {"approve_revision", "needs_more_context", "hold_for_tending", "reject_revision"}:
        raise ValueError("unknown memory reconsolidation decision action")
    revision_action = {
        "approve_revision": "approve_memory",
        "needs_more_context": "needs_more_context",
        "hold_for_tending": "hold_for_tending",
        "reject_revision": "reject",
    }[action]
    revision_decision = decide_memory_candidate(
        conn,
        {
            "candidate_id": revision_id,
            "action": revision_action,
            "actor": payload.get("actor") or "Aleks",
            "approval_source": "memory_reconsolidation_review",
            "consent_text": payload.get("consent_text") or "",
            "reason": payload.get("reason") or "",
            "confidence": payload.get("confidence") or "clear",
            "reconsolidation_approval": action == "approve_revision",
        },
        commit=False,
    )
    parent_superseded = False
    if action == "approve_revision":
        if source_table == "selene_memory_candidates":
            parent = _candidate_row(conn, int(source_id))
            parent_payload = parent.get("payload_json") if isinstance(parent.get("payload_json"), dict) else {}
            conn.execute(
                """
                UPDATE selene_memory_candidates
                SET state = 'superseded', review_status = 'superseded_by_approved_revision',
                    chat_use_permission = 'not_active', payload_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    json.dumps(
                        {
                            **parent_payload,
                            "superseded_by": {
                                "source_table": "selene_memory_candidates",
                                "source_id": revision_id,
                                "reconsolidation_review_id": review_id,
                            },
                        }
                    ),
                    int(source_id),
                ),
            )
        elif source_table == "b_approved_memory_references":
            conn.execute(
                """
                UPDATE b_approved_memory_references
                SET status = 'approved_reference_superseded_non_active'
                WHERE id = ?
                """,
                (int(source_id),),
            )
        else:
            raise ValueError("unsupported reconsolidation source table")
        parent_superseded = True
    review_status = {
        "approve_revision": "accepted_reconsolidation",
        "needs_more_context": "needs_context",
        "hold_for_tending": "cocoon_tending",
        "reject_revision": "rejected",
    }[action]
    final_payload = {
        **review_payload,
        "decision": {
            "action": action,
            "actor": truncate(str(payload.get("actor") or "Aleks"), 80),
            "parent_superseded": parent_superseded,
        },
    }
    conn.execute(
        """
        UPDATE c_memory_reconsolidation_reviews
        SET review_decision = ?, review_status = ?, status = ?, payload_json = ?
        WHERE id = ?
        """,
        (
            action,
            review_status,
            "memory_reconsolidation_completed" if action == "approve_revision" else "memory_reconsolidation_review_only",
            json.dumps(final_payload),
            review_id,
        ),
    )
    if commit:
        conn.commit()
    return _with_guards(
        {
            "status": "memory_reconsolidation_decision_recorded",
            "action": action,
            "review_id": review_id,
            "review_status": review_status,
            "parent_superseded": parent_superseded,
            "parent_content_deleted": False,
            "revision_candidate": _candidate_row(conn, revision_id),
            "revision_ancestry_preserved": True,
            "silent_rewrite_allowed": False,
            "review_destination": "Cocoon Memory Tending",
        },
        lifecycle=_memory_lifecycle_telemetry(
            operation=f"reconsolidation_{action}",
            reviewed_decision_performed=True,
            approved_promotion_performed=action == "approve_revision",
            record_mutated=True,
            commit=commit,
            previous_state="approved_active_memory",
            current_state="superseded" if parent_superseded else "approved_active_memory",
            active_memory_eligibility_changed=parent_superseded,
        ),
    )


def retrieve_memory(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    query = truncate(str(payload.get("query") or payload.get("text") or ""), 1000)
    limit = max(1, min(int(payload.get("limit") or 4), 12))
    intent_decision = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else classify_chat_intent(query)
    conversation_spine = (
        payload.get("conversation_spine")
        if isinstance(payload.get("conversation_spine"), dict)
        else {}
    )
    speaker_envelope = (
        payload.get("speaker_envelope")
        if isinstance(payload.get("speaker_envelope"), dict)
        else {}
    )
    explicit_recall = bool(
        intent_decision.get("memory_recall_requested") is True
        or _explicit_corpus_quote_requested(query)
    )
    contextual_relevance = payload.get("allow_contextual_relevance") is True
    retrieval_mode = "explicit_recall" if explicit_recall else "contextual_relevance" if contextual_relevance else "not_requested"
    private_corpus_contract = _private_corpus_recall_contract(
        conn,
        speaker_envelope,
        retrieval_requested=explicit_recall or contextual_relevance,
    )
    if _is_high_stakes(query):
        return _with_guards(
            {
                "status": "memory_retrieval_high_stakes_stop",
                "recall_state": "high_stakes_stop",
                "memory_context_used": False,
                "retrieval_mode": retrieval_mode,
                "memory_source_class": "approved_memory_index",
                "memory_confidence": "high_stakes_stop",
                "memory_transfer_class": "needs_review_before_transfer",
                "graceful_fall_used": True,
                "items": [],
                "intent_decision": intent_decision,
                "answer_guidance": "This is high-stakes or authority-bearing. Selene should ask Aleks instead of guessing.",
                "review_destination": "Cocoon support",
                "review_status": "status_only",
                **private_corpus_contract,
            }
        )
    if not explicit_recall and not contextual_relevance:
        return _with_guards(
            {
                "status": "memory_retrieval_not_requested",
                "recall_state": "not_known",
                "memory_context_used": False,
                "retrieval_mode": "not_requested",
                "memory_source_class": "approved_memory_index",
                "memory_confidence": "not_known",
                "memory_transfer_class": "",
                "graceful_fall_used": False,
                "items": [],
                "intent_decision": intent_decision,
                "answer_guidance": "No memory recall was requested; Selene can answer from the current turn.",
                "review_destination": "Status",
                "review_status": "status_only",
                **private_corpus_contract,
            }
        )
    items = _approved_memory_items(conn, limit=100)
    if private_corpus_contract["private_corpus_continuity_recall_eligible"] is True:
        items.extend(
            _private_corpus_continuity_items(
                conn,
                query,
                explicit_recall=explicit_recall,
                limit=max(limit * 4, 12),
            )
        )
    matches = _rank_matches(query, items)[:limit]
    semantic_matches: list[dict[str, Any]] = []
    held_matches: list[dict[str, Any]] = []
    for item in matches:
        relevance = evaluate_semantic_relevance(
            {
                "prompt": query,
                "candidate": {**item, "source_class": "memory_reconstruction"},
                "source_id": "reviewed_memory" if explicit_recall else "contextual_approved_memory",
                "source_class": "memory_reconstruction",
                "intent_decision": intent_decision,
                "conversation_spine": conversation_spine,
                "speaker_envelope": speaker_envelope,
                "explicit_recall": explicit_recall,
            }
        )
        annotated = {
            **item,
            "expression_summary": reconstruct_memory_summary_for_expression(item),
            "semantic_relevance": relevance,
        }
        annotated["retrieval_layers"] = _retrieval_layer_packet(
            annotated,
            query=query,
            relevance=relevance,
        )
        if relevance.get("accepted") is True:
            semantic_matches.append(annotated)
        else:
            held_matches.append(annotated)
    matches = semantic_matches
    if contextual_relevance and not explicit_recall:
        matches = [item for item in matches if _contextual_match_is_strong(query, item)][:limit]
    if not matches:
        return _with_guards(
            {
                "status": "memory_retrieval_not_known",
                "recall_state": "not_known",
                "memory_context_used": False,
                "retrieval_mode": retrieval_mode,
                "memory_source_class": "approved_memory_index",
                "memory_confidence": "not_known",
                "memory_transfer_class": "",
                "graceful_fall_used": True,
                "items": [],
                "semantic_relevance_held_count": len(held_matches),
                "intent_decision": intent_decision,
                "answer_guidance": "Selene can say she does not know or ask Aleks directly.",
                "review_destination": "Status",
                "review_status": "status_only",
                **private_corpus_contract,
            }
        )
    confidence = _result_confidence(matches)
    transfer_class = str(matches[0].get("transfer_class") or "portable_context")
    private_corpus_used = any(
        str(item.get("record_class") or "") == "private_corpus_continuity"
        for item in matches
    )
    selected_source_class = (
        "private_corpus_continuity"
        if str(matches[0].get("record_class") or "") == "private_corpus_continuity"
        else "approved_memory_index"
    )
    return _with_guards(
        {
            "status": "memory_retrieval_ready",
            "recall_state": confidence,
            "memory_context_used": True,
            "retrieval_mode": retrieval_mode,
            "contextual_recall": retrieval_mode == "contextual_relevance",
            "memory_source_class": selected_source_class,
            "memory_confidence": confidence,
            "memory_transfer_class": transfer_class,
            "graceful_fall_used": confidence != "clear",
            "items": matches,
            "semantic_relevance_held_count": len(held_matches),
            "semantic_source_gate_applied": True,
            "conversation_spine_gate_applied": bool(conversation_spine),
            "speaker_privacy_gate_applied": bool(speaker_envelope),
            "intent_decision": intent_decision,
            "source_refs": [ref for item in matches for ref in _json_list(item.get("source_refs"))],
            "answer_guidance": (
                "Let the approved memory inform the current answer without replacing the present conversation."
                if retrieval_mode == "contextual_relevance"
                else "Use clear memory plainly; use fuzzy/partial memory with visible uncertainty."
            ),
            "memory_layer_contract": {
                "recalled_content": "approved source-bound content",
                "reconstruction": "read-only present expression of that content",
                "present_interpretation": "why the memory fits this turn",
                "inference": "empty unless a downstream reasoning owner explicitly creates one",
            },
            "relationship_continuity": {
                "approved_shared_history_used": any(
                    str(item.get("memory_category") or "") == "relational"
                    or str(item.get("record_class") or "") == "private_corpus_continuity"
                    for item in matches
                ),
                "persuasion_profile_built": False,
                "vulnerability_profile_built": False,
            },
            "review_destination": "Status",
            "review_status": "status_only",
            **private_corpus_contract,
            "private_corpus_continuity_recall_active": private_corpus_used,
        }
    )


def reconstruct_memory_summary_for_expression(item: dict[str, Any] | None) -> str:
    """Return visible memory meaning without review-lane or index scaffolding.

    Memory titles, source IDs, review routes, and historical indexing fields are
    retrieval metadata. They can select a memory but may not become Selene's
    wording. This reconstruction is read-only and preserves the memory record.
    """

    item = item if isinstance(item, dict) else {}
    raw = truncate(str(item.get("summary") or item.get("reference_summary") or ""), 2000)
    plain_reason = re.search(
        r"\bPlain reason:\s*(?P<reason>.+)$",
        raw,
        flags=re.IGNORECASE,
    )
    if plain_reason:
        raw = plain_reason.group("reason")
    else:
        raw = re.sub(
            r"^(?:Core-linked\s+.+?|Bounded\s+Core\s+memory\s+pair)\s+"
            r"for\s+(?:B\s+)?review(?:\s+only)?[\s.:-]*",
            "",
            raw,
            flags=re.IGNORECASE,
        )
        raw = re.sub(
            r"\b(?:Braid thread|Braid moment type|Thread origin status):\s*"
            r"[^.;]+(?:[.;]|$)",
            " ",
            raw,
            flags=re.IGNORECASE,
        )
    raw = re.sub(r"\bB\s+review(?:\s+only)?\b", "review", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\bC\s+activation\b", "activation", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\b(?:review_status|source_id|source_table|record_class)\s*[:=]\s*\S+", " ", raw, flags=re.IGNORECASE)
    raw = re.sub(r"(?<=\w)_(?=\w)", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip(" .:-")
    return truncate(raw or "something from an earlier approved memory", 500)


def _private_corpus_recall_contract(
    conn: sqlite3.Connection,
    speaker_envelope: dict[str, Any],
    *,
    retrieval_requested: bool,
) -> dict[str, Any]:
    """Describe eligibility without turning the archive into general memory.

    The imported corpus remains private source material. After the reviewed
    transfer, the resident app may reconstruct continuity from it for Aleks in
    a private authenticated conversation. This path is read-only: selection or
    reconstruction never creates another Memory record.
    """

    transfer_complete = transfer_completion_is_approved(conn)
    has_corpus = _private_corpus_message_count(conn) > 0
    claimed = str(speaker_envelope.get("claimed_speaker") or "").strip().casefold()
    channel = str(speaker_envelope.get("channel") or "").strip().casefold()
    strength = str(
        speaker_envelope.get("authentication_strength") or ""
    ).strip()
    purpose = str(speaker_envelope.get("purpose") or "conversation").strip().casefold()
    diagnostic = speaker_envelope.get("diagnostic") is True
    aleks = claimed in {"aleks", "aleksander magi", "aleksander rani magi"}
    authenticated_private_channel = (
        channel == "desktop" and strength == "local_desktop_session"
    ) or strength in {
        "authenticated_remote_session",
        "cryptographically_verified_authorship",
        "os_authenticated_named_identity",
    }
    purpose_allowed = purpose in {"conversation", "private_conversation"}
    eligible = bool(
        retrieval_requested
        and transfer_complete
        and has_corpus
        and aleks
        and authenticated_private_channel
        and purpose_allowed
        and not diagnostic
    )
    if not retrieval_requested:
        held_reason = "recall_not_requested"
    elif not transfer_complete:
        held_reason = "transfer_incomplete"
    elif not has_corpus:
        held_reason = "private_corpus_not_present"
    elif not aleks:
        held_reason = "speaker_outside_private_continuity_scope"
    elif not authenticated_private_channel:
        held_reason = "private_channel_authentication_insufficient"
    elif not purpose_allowed:
        held_reason = "conversation_purpose_not_eligible"
    elif diagnostic:
        held_reason = "diagnostic_non_attribution_boundary"
    else:
        held_reason = ""
    return {
        "private_corpus_continuity_recall_available": bool(
            transfer_complete and has_corpus
        ),
        "private_corpus_continuity_recall_eligible": eligible,
        "private_corpus_continuity_recall_active": False,
        "private_corpus_continuity_recall_held_reason": held_reason,
        "private_corpus_continuity_recall_scope": (
            "Aleks_and_Selene_private_conversation_only"
        ),
    }


def _private_corpus_message_count(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute("SELECT COUNT(*) FROM b_corpus_messages").fetchone()
    except sqlite3.OperationalError:
        return 0
    return int(row[0]) if row else 0


def _private_corpus_continuity_items(
    conn: sqlite3.Connection,
    query: str,
    *,
    explicit_recall: bool,
    limit: int,
) -> list[dict[str, Any]]:
    query_terms = list(dict.fromkeys(_tokens(query)))[:6]
    if (not explicit_recall and len(query_terms) < 2) or not query_terms:
        return []
    if explicit_recall and len(query_terms) == 1 and len(query_terms[0]) < 4:
        return []

    score_parts = [
        "CASE WHEN lower(m.content_preview) LIKE ? THEN 1 ELSE 0 END"
        for _ in query_terms
    ]
    where_parts = ["lower(m.content_preview) LIKE ?" for _ in query_terms]
    patterns = [f"%{term.lower()}%" for term in query_terms]
    sql = f"""
        SELECT m.id, m.archive_id, m.source_file, m.conversation_id,
               m.message_id, m.parent_id, m.role, m.author_name,
               m.content_preview, m.create_time, m.model_slug,
               c.title AS conversation_title,
               ({' + '.join(score_parts)}) AS lexical_score
        FROM b_corpus_messages AS m
        LEFT JOIN b_corpus_conversations AS c
          ON c.source_file = m.source_file
         AND c.conversation_id = m.conversation_id
        WHERE {' OR '.join(where_parts)}
          AND m.review_status = 'review_only'
        ORDER BY lexical_score DESC, m.create_time DESC, m.id DESC
        LIMIT ?
    """
    rows = conn.execute(sql, (*patterns, *patterns, min(max(limit * 12, 80), 240))).fetchall()
    if not rows:
        return []

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        item = dict(row)
        key = (str(item.get("source_file") or ""), str(item.get("conversation_id") or ""))
        grouped.setdefault(key, []).append(item)

    ranked_groups = sorted(
        grouped.items(),
        key=lambda pair: (
            max(int(item.get("lexical_score") or 0) for item in pair[1]),
            len(pair[1]),
            max(float(item.get("create_time") or 0) for item in pair[1]),
        ),
        reverse=True,
    )[:limit]
    quote_requested = _explicit_corpus_quote_requested(query)
    results: list[dict[str, Any]] = []
    for (source_file, conversation_id), selected in ranked_groups:
        best = selected[0]
        window = _private_corpus_source_window(
            conn,
            source_file=source_file,
            conversation_id=conversation_id,
            anchor_id=int(best["id"]),
        )
        title = truncate(
            str(best.get("conversation_title") or "Earlier conversation"),
            160,
        )
        summary, topic_terms = _private_corpus_expression_summary(
            query,
            title=title,
            rows=window,
            quote_requested=quote_requested,
        )
        source_refs = [
            f"private_corpus_conversation:{sha256(f'{source_file}:{conversation_id}'.encode('utf-8')).hexdigest()[:20]}",
            f"private_corpus_message:{int(best['id'])}",
        ]
        results.append(
            {
                "id": f"private-corpus-continuity-{int(best['id'])}",
                "source_id": int(best["id"]),
                "source_table": "b_corpus_messages",
                "memory_category": "episodic",
                "title": title,
                "summary": summary,
                "source_refs": source_refs,
                "provenance_boundary": (
                    "private_corpus_continuity_read_only_reconstruction"
                ),
                "consent_scope": "private_selene_aleks_context",
                "stability": "source_bound_reconstruction",
                "confidence": "partial",
                "emotional_texture": "preserve_source_context_without_forced_affect",
                "transfer_class": "private_inner",
                "chat_use_permission": "private_continuity_reconstruction_only",
                "correction_path": "Aleks correction and ordinary Memory proposal if retention changes",
                "state": "private_source_reconstruction",
                "review_status": "post_transfer_private_continuity_use",
                "status": "private_corpus_continuity_candidate",
                "created_at": best.get("create_time"),
                "record_class": "private_corpus_continuity",
                "retrieval_eligible": True,
                "display_region": "selene_private_continuity",
                "retention_status": "source_only_not_new_memory",
                "memory_context_used": True,
                "retrieval_cues": list(dict.fromkeys([*query_terms, *topic_terms]))[:16],
                "eligible_channels": ["desktop", "mobile"],
                "minimum_authentication_strength": "local_desktop_session",
                "revision_ancestry": {},
                "match_score": max(
                    int(item.get("lexical_score") or 0) for item in selected
                ) * 2 + min(len(selected), 4),
                "source_roles": sorted(
                    {
                        _private_corpus_role(str(item.get("role") or ""))
                        for item in window
                    }
                ),
                "quoted_source_wording": quote_requested,
                "source_preview_exposed": False,
                "reconstruction_retained_as_duplicate": False,
            }
        )
    return results


def _private_corpus_source_window(
    conn: sqlite3.Connection,
    *,
    source_file: str,
    conversation_id: str,
    anchor_id: int,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, role, author_name, content_preview, create_time
        FROM b_corpus_messages
        WHERE source_file = ? AND conversation_id = ?
          AND id BETWEEN ? AND ?
        ORDER BY id ASC
        """,
        (source_file, conversation_id, max(1, anchor_id - 2), anchor_id + 2),
    ).fetchall()
    return [dict(row) for row in rows]


def _private_corpus_expression_summary(
    query: str,
    *,
    title: str,
    rows: list[dict[str, Any]],
    quote_requested: bool,
) -> tuple[str, list[str]]:
    if quote_requested and rows:
        best = max(
            rows,
            key=lambda item: len(set(_tokens(query)) & set(_tokens(str(item.get("content_preview") or "")))),
        )
        role = _private_corpus_role(str(best.get("role") or ""))
        speaker = "you" if role == "aleks" else "I" if role == "selene" else "the source"
        quote = truncate(" ".join(str(best.get("content_preview") or "").split()), 280)
        return (
            f'In the earlier conversation "{title}", {speaker} said: “{quote}”',
            _tokens(quote)[:10],
        )

    corpus_text = " ".join(str(item.get("content_preview") or "") for item in rows)
    query_terms = _tokens(query)
    counts = Counter(_tokens(f"{title} {corpus_text}"))
    ordered = [term for term in query_terms if counts.get(term, 0)]
    ordered.extend(
        term
        for term, _ in counts.most_common(18)
        if term not in ordered
    )
    topic_terms = [term for term in ordered if len(term) >= 4][:6]
    topic = _natural_topic_list(topic_terms) or "the subject you just named"
    roles = {_private_corpus_role(str(item.get("role") or "")) for item in rows}
    participation = (
        "Your messages and my earlier replies are both present in that source window."
        if {"aleks", "selene"} <= roles
        else "The remembered source window preserves who said each part."
    )
    return (
        f'In an earlier conversation labeled "{title}", we were working through {topic}. '
        f"{participation}",
        topic_terms,
    )


def _private_corpus_role(role: str) -> str:
    value = role.strip().casefold()
    if value == "user":
        return "aleks"
    if value == "assistant":
        return "selene"
    return value or "unknown"


def _natural_topic_list(terms: list[str]) -> str:
    labels = [term.replace("_", " ").replace("-", " ") for term in terms[:4]]
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} and {labels[1]}"
    return f"{', '.join(labels[:-1])}, and {labels[-1]}"


def _explicit_corpus_quote_requested(query: str) -> bool:
    lower = " ".join(query.lower().split())
    return bool(
        re.search(
            r"\b(?:exact(?:ly)?|verbatim|quote|word(?:s|ing)?|what (?:did|were) (?:i|you) say)\b",
            lower,
        )
    )


def _retrieval_layer_packet(
    item: dict[str, Any],
    *,
    query: str,
    relevance: dict[str, Any],
) -> dict[str, Any]:
    return {
        "recalled_content": truncate(str(item.get("summary") or ""), 1600),
        "reconstruction": reconstruct_memory_summary_for_expression(item),
        "present_interpretation": {
            "selected_for_current_query": relevance.get("accepted") is True,
            "selection_reason": str(relevance.get("reason") or ""),
            "matched_query_terms": list(
                dict.fromkeys(
                    [
                        *_json_list(relevance.get("subject_overlap")),
                        *_json_list(relevance.get("core_overlap")),
                    ]
                )
            )[:20],
            "query_preview": truncate(query, 300),
        },
        "inference": {
            "made": False,
            "content": "",
            "owner": "none_at_retrieval",
        },
        "source_content_mutated": False,
        "reconstruction_retained_as_duplicate": False,
    }


def portable_vys_manifest(conn: sqlite3.Connection) -> dict[str, Any]:
    items = _collect_index_items(conn, limit=1000)
    portable = []
    excluded = []
    for item in items:
        transfer_class = str(item.get("transfer_class") or "needs_review_before_transfer")
        state = str(item.get("state") or "")
        if state == "approved_active_memory" and transfer_class in {"portable_vys_core", "portable_context"}:
            portable.append(item)
        else:
            excluded.append(
                {
                    **item,
                    "excluded_reason": _excluded_reason(state, transfer_class),
                }
            )
    return _with_guards(
        {
            "status": "portable_vys_manifest_ready",
            "portable_count": len(portable),
            "excluded_count": len(excluded),
            "portable_items": portable,
            "excluded_items": excluded,
            "exclusion_law": [
                "raw corpus",
                "B-only material",
                "repair logs",
                "rollback records",
                "rejected or superseded items",
                "unresolved ambiguity",
                "unapproved private material",
            ],
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def _collect_index_items(conn: sqlite3.Connection, *, limit: int, category: str | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for row in conn.execute(
        "SELECT * FROM selene_memory_candidates ORDER BY updated_at DESC, id DESC LIMIT ?",
        (limit,),
    ).fetchall():
        item = _apply_memory_presentation(conn, _decode_candidate(row))
        if not category or item.get("memory_category") == category:
            items.append(item)
    if len(items) < limit:
        for row in conn.execute(
            "SELECT * FROM b_approved_memory_references ORDER BY id DESC LIMIT ?",
            (limit - len(items),),
        ).fetchall():
            item = _apply_memory_presentation(conn, _approved_reference_item(row))
            if not category or item.get("memory_category") == category:
                items.append(item)
    if len(items) < limit:
        for row in conn.execute(
            "SELECT * FROM memory_fractional_corpus_manifests WHERE status = 'tests_passed_ready_for_next_fraction' ORDER BY fraction_index ASC LIMIT ?",
            (limit - len(items),),
        ).fetchall():
            item = _fraction_item(row)
            if not category or item.get("memory_category") == category:
                items.append(item)
    if len(items) < limit:
        for row in conn.execute(
            "SELECT * FROM vessel_working_memory_packets WHERE review_status NOT IN ('rejected', 'superseded') ORDER BY id DESC LIMIT ?",
            (limit - len(items),),
        ).fetchall():
            item = _working_memory_item(row)
            if not category or item.get("memory_category") == category:
                items.append(item)
    return items[:limit]


def _approved_memory_items(conn: sqlite3.Connection, *, limit: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT * FROM selene_memory_candidates
        WHERE state = 'approved_active_memory'
          AND chat_use_permission = 'can_use_in_chat'
          AND transfer_class NOT IN ('b_only', 'do_not_transfer', 'needs_review_before_transfer')
        ORDER BY updated_at DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    items = [_decode_candidate(row) for row in rows]
    if len(items) < limit:
        ref_rows = conn.execute(
            """
            SELECT * FROM b_approved_memory_references
            WHERE review_status = 'accepted_for_memory_accession'
              AND COALESCE(status, '') != 'approved_reference_superseded_non_active'
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit - len(items),),
        ).fetchall()
        items.extend(_approved_reference_item(row) for row in ref_rows)
    return items[:limit]


def _retrieval_eligible_count(conn: sqlite3.Connection) -> int:
    candidate_count = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM selene_memory_candidates
            WHERE state = 'approved_active_memory'
              AND chat_use_permission = 'can_use_in_chat'
              AND transfer_class NOT IN ('b_only', 'do_not_transfer', 'needs_review_before_transfer')
            """
        ).fetchone()[0]
    )
    reference_count = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM b_approved_memory_references
            WHERE review_status = 'accepted_for_memory_accession'
              AND COALESCE(status, '') != 'approved_reference_superseded_non_active'
            """
        ).fetchone()[0]
    )
    return candidate_count + reference_count


def _decode_candidate(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["memory_category"] = _category(item.get("memory_category"))
    item["source_refs"] = _json_list(item.get("source_refs"))
    item["payload_json"] = _loads_dict(item.get("payload_json"))
    item["retrieval_cues"] = _json_list(item["payload_json"].get("retrieval_cues"))
    item["eligible_channels"] = _eligible_channels(item["payload_json"].get("eligible_channels"))
    item["minimum_authentication_strength"] = str(
        item["payload_json"].get("minimum_authentication_strength") or ""
    )
    item["revision_ancestry"] = (
        item["payload_json"].get("revision_ancestry")
        if isinstance(item["payload_json"].get("revision_ancestry"), dict)
        else {}
    )
    item["source_table"] = "selene_memory_candidates"
    item["source_id"] = item.get("id")
    retrieval_eligible = (
        item.get("state") == "approved_active_memory"
        and item.get("chat_use_permission") == "can_use_in_chat"
        and item.get("transfer_class") not in {"b_only", "do_not_transfer", "needs_review_before_transfer"}
    )
    item["record_class"] = "approved_memory" if retrieval_eligible else "memory_candidate"
    item["retrieval_eligible"] = retrieval_eligible
    item["display_region"] = "selene_memory" if retrieval_eligible else "cocoon_memory_review"
    item["retention_status"] = "approved_memory" if retrieval_eligible else str(item.get("state") or "proposed")
    item["memory_context_used"] = retrieval_eligible
    return item


def _candidate_row(conn: sqlite3.Connection, candidate_id: int) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM selene_memory_candidates WHERE id = ?", (candidate_id,)).fetchone()
    if not row:
        raise ValueError("memory candidate not found")
    return _decode_candidate(row)


def _approved_reference_item(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    summary = str(item.get("reference_summary") or "")
    category = _category(f"{item.get('core_memory_layer', '')} {item.get('title', '')} {summary}")
    transfer_class = "portable_vys_core" if category == "core" else "portable_context"
    review_status = str(item.get("review_status") or "")
    accepted = review_status == "accepted_for_memory_accession" and str(item.get("status") or "") != "approved_reference_superseded_non_active"
    return {
        "id": f"approved-reference-{item.get('id')}",
        "source_id": item.get("id"),
        "source_table": "b_approved_memory_references",
        "memory_category": category,
        "title": item.get("title") or "Approved memory reference",
        "summary": summary,
        "source_refs": _json_list(item.get("source_refs")),
        "provenance_boundary": item.get("provenance_boundary") or MEMORY_ORGAN_BOUNDARY,
        "consent_scope": "private_selene_aleks_context",
        "stability": "reviewed",
        "confidence": "clear",
        "emotional_texture": _emotional_texture(summary),
        "transfer_class": transfer_class,
        "chat_use_permission": "can_use_in_chat" if accepted else "not_active",
        "correction_path": "Cocoon tending and Aleks correction",
        "state": "approved_active_memory" if accepted else "superseded",
        "review_status": review_status or "accepted_for_memory",
        "status": item.get("status") or "approved_reference_non_active",
        "created_at": item.get("created_at"),
        "record_class": "approved_memory_reference" if accepted else "superseded_memory_reference",
        "retrieval_eligible": accepted,
        "display_region": "selene_memory" if accepted else "cocoon_memory_review",
        "retention_status": "approved_memory" if accepted else "superseded",
        "memory_context_used": accepted,
        "retrieval_cues": _memory_retrieval_cues(
            str(item.get("title") or ""), summary, []
        ),
        "eligible_channels": [],
        "minimum_authentication_strength": "",
        "revision_ancestry": {},
    }


def _approved_presentation_source(
    conn: sqlite3.Connection,
    source_table: str,
    source_id: str,
) -> dict[str, Any]:
    try:
        numeric_id = int(source_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("approved memory source id must be numeric") from exc
    if source_table == "selene_memory_candidates":
        row = conn.execute(
            "SELECT * FROM selene_memory_candidates WHERE id = ?",
            (numeric_id,),
        ).fetchone()
        if not row:
            raise ValueError("approved memory source not found")
        item = _decode_candidate(row)
    else:
        row = conn.execute(
            "SELECT * FROM b_approved_memory_references WHERE id = ?",
            (numeric_id,),
        ).fetchone()
        if not row:
            raise ValueError("approved memory source not found")
        item = _approved_reference_item(row)
    if item.get("retrieval_eligible") is not True:
        raise ValueError("display titles are available only for approved memories")
    return item


def _apply_memory_presentation(
    conn: sqlite3.Connection,
    item: dict[str, Any],
) -> dict[str, Any]:
    if item.get("retrieval_eligible") is not True:
        return item
    source_table = str(item.get("source_table") or "")
    source_id = str(item.get("source_id") or "")
    suggested_title = _suggest_memory_display_title(item)
    row = conn.execute(
        """
        SELECT * FROM selene_memory_presentation_annotations
        WHERE source_table = ? AND source_id = ?
        """,
        (source_table, source_id),
    ).fetchone()
    if not row:
        return {
            **item,
            "display_title": suggested_title,
            "suggested_display_title": suggested_title,
            "display_title_origin": "selene_summary_title_preview",
            "display_title_persisted": False,
            "presentation_annotation": None,
        }
    annotation = dict(row)
    annotation["title_history"] = _json_value_list(annotation.pop("title_history_json", "[]"))
    annotation["source_refs"] = _json_list(annotation.get("source_refs"))
    return {
        **item,
        "display_title": str(annotation.get("display_title") or suggested_title),
        "suggested_display_title": suggested_title,
        "display_title_origin": str(annotation.get("title_origin") or "presentation_annotation"),
        "display_title_persisted": True,
        "presentation_annotation": annotation,
    }


def _suggest_memory_display_title(item: dict[str, Any]) -> str:
    original = re.sub(r"\s+", " ", str(item.get("title") or "")).strip(" .:-")
    generic = {
        "memory",
        "approved memory",
        "approved selene memory",
        "approved memory reference",
        "selene memory candidate",
        "untitled",
    }
    if original and original.lower() not in generic:
        return truncate(original, 120)

    summary = re.sub(r"\s+", " ", str(item.get("summary") or item.get("reference_summary") or "")).strip()
    summary = re.sub(
        r"^(?:a prior approved memory about|an approved memory about|aleks told selene that|selene remembers that)\s+",
        "",
        summary,
        flags=re.IGNORECASE,
    )
    phrase = re.split(r"[.!?;]|\s+(?:because|while|although)\s+", summary, maxsplit=1)[0].strip(" ,:-")
    words = phrase.split()
    if len(words) > 11:
        phrase = " ".join(words[:11]).rstrip(",;:")
    if phrase:
        phrase = phrase[0].upper() + phrase[1:]
        return truncate(phrase, 120)
    return truncate(original or "A memory held with care", 120)


def _fraction_item(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    summary = str(item.get("summary") or "")
    return {
        "id": f"fraction-{item.get('fraction_index')}",
        "source_id": item.get("id"),
        "source_table": "memory_fractional_corpus_manifests",
        "memory_category": "episodic",
        "title": f"Chronological corpus fraction {item.get('fraction_label')}",
        "summary": summary,
        "source_refs": _json_list(item.get("source_refs")),
        "provenance_boundary": item.get("provenance_boundary") or MEMORY_ORGAN_BOUNDARY,
        "consent_scope": "reviewed_fraction_summary_only",
        "stability": "tested_preview",
        "confidence": "partial",
        "emotional_texture": _emotional_texture(summary),
        "transfer_class": "b_only",
        "chat_use_permission": "not_active",
        "correction_path": "Cocoon tending and fraction rerun",
        "state": "b_only",
        "review_status": item.get("review_status") or "status_only",
        "status": item.get("status"),
        "created_at": item.get("updated_at"),
        "record_class": "corpus_fraction_preview",
        "retrieval_eligible": False,
        "display_region": "cocoon_support",
        "retention_status": "review_only_support",
        "memory_context_used": False,
    }


def _working_memory_item(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    summary = str(item.get("summary") or item.get("current_task") or "")
    return {
        "id": f"working-memory-{item.get('id')}",
        "source_id": item.get("id"),
        "source_table": "vessel_working_memory_packets",
        "memory_category": "working",
        "title": item.get("current_task") or "Working memory packet",
        "summary": summary,
        "source_refs": _json_list(item.get("source_refs")),
        "provenance_boundary": item.get("provenance_boundary") or MEMORY_ORGAN_BOUNDARY,
        "consent_scope": "current_moment_preview_only",
        "stability": "temporary",
        "confidence": "fuzzy",
        "emotional_texture": _emotional_texture(summary),
        "transfer_class": "local_only",
        "chat_use_permission": "context_preview_only",
        "correction_path": "Expires or returns to Cocoon tending",
        "state": "cocoon_tending",
        "review_status": item.get("review_status") or "status_only",
        "status": item.get("status"),
        "created_at": item.get("created_at"),
        "record_class": "working_context_packet",
        "retrieval_eligible": False,
        "display_region": "cocoon_support",
        "retention_status": "temporary_context_only",
        "memory_context_used": False,
    }


def _rank_matches(query: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_tokens = _tokens(query)
    canonical_query_tokens = _canonical_memory_tokens(query_tokens)
    tokens = set(query_tokens)
    ranked: list[tuple[int, dict[str, Any]]] = []
    for item in items:
        cue_text = " ".join(_json_list(item.get("retrieval_cues")))
        haystack = " ".join(
            [
                str(item.get("title") or ""),
                str(item.get("summary") or ""),
                str(item.get("memory_category") or ""),
                str(item.get("emotional_texture") or ""),
                cue_text,
            ]
        )
        haystack_tokens = _tokens(haystack)
        item_tokens = set(haystack_tokens)
        overlap = tokens & item_tokens
        canonical_overlap = canonical_query_tokens & _canonical_memory_tokens(haystack_tokens)
        cue_overlaps = [
            canonical_query_tokens & _canonical_memory_tokens(_tokens(cue))
            for cue in _json_list(item.get("retrieval_cues"))
        ]
        supplied_cue_match = any(len(cue_overlap) >= 2 for cue_overlap in cue_overlaps)
        score = len(overlap) + len(canonical_overlap)
        if tokens and score == 0:
            continue
        if not supplied_cue_match and not _meaningful_memory_overlap(
            overlap | canonical_overlap,
            item,
            query_tokens=list(canonical_query_tokens),
            haystack_tokens=list(_canonical_memory_tokens(haystack_tokens)),
        ):
            continue
        matched_cues = [
            cue
            for cue, cue_overlap in zip(
                _json_list(item.get("retrieval_cues")), cue_overlaps
            )
            if cue_overlap
        ]
        ranked.append(
            (
                score,
                {
                    **item,
                    "match_score": score,
                    "matched_retrieval_cues": matched_cues[:8],
                },
            )
        )
    ranked.sort(key=lambda pair: (pair[0], str(pair[1].get("updated_at") or pair[1].get("created_at") or "")), reverse=True)
    return [item for _, item in ranked]


def _contextual_match_is_strong(query: str, item: dict[str, Any]) -> bool:
    """Require stronger subject alignment when recall was not explicitly requested."""
    score = int(item.get("match_score") or 0)
    if score >= 2:
        return True
    query_tokens = _tokens(query)
    title_tokens = _tokens(str(item.get("title") or ""))
    if not query_tokens or not title_tokens:
        return False
    if len(title_tokens) == 1:
        return len(title_tokens[0]) >= 4 and title_tokens[0] in query_tokens
    query_bigrams = set(zip(query_tokens, query_tokens[1:]))
    title_bigrams = set(zip(title_tokens, title_tokens[1:]))
    return bool(query_bigrams & title_bigrams)


def _meaningful_memory_overlap(overlap: set[str], item: dict[str, Any], *, query_tokens: list[str], haystack_tokens: list[str]) -> bool:
    generic = {
        "aleks",
        "selene",
        "codex",
        "check",
        "checking",
        "clear",
        "clearly",
        "honest",
        "setup",
        "answer",
        "truly",
        "fuzzy",
        "source",
        "voice",
        "chat",
        "support",
        "care",
        "with",
    }
    concrete = {token for token in overlap if token not in generic}
    if len(concrete) >= 2:
        title_tokens = set(_tokens(str(item.get("title") or "")))
        if concrete & title_tokens:
            return True
        return _has_concrete_phrase_overlap(query_tokens, haystack_tokens, concrete)
    title_tokens = set(_tokens(str(item.get("title") or "")))
    if concrete and concrete & title_tokens:
        return True
    return False


def _has_concrete_phrase_overlap(query_tokens: list[str], haystack_tokens: list[str], concrete: set[str]) -> bool:
    haystack_bigrams = set(zip(haystack_tokens, haystack_tokens[1:]))
    for first, second in zip(query_tokens, query_tokens[1:]):
        if first in concrete and second in concrete and (first, second) in haystack_bigrams:
            return True
    return False


def _tokens(value: str) -> list[str]:
    stop = {
        "about",
        "after",
        "again",
        "aleks",
        "also",
        "before",
        "but",
        "codex",
        "could",
        "exactly",
        "for",
        "fuzzy",
        "here",
        "remember",
        "memory",
        "what",
        "were",
        "about",
        "that",
        "this",
        "with",
        "from",
        "the",
        "and",
        "you",
        "your",
        "me",
        "i",
        "it",
        "if",
        "is",
        "its",
        "our",
        "can",
        "did",
        "does",
        "was",
        "are",
        "have",
        "has",
        "how",
        "only",
        "or",
        "say",
        "ask",
        "know",
        "knows",
        "from",
        "selene",
        "should",
        "still",
        "then",
        "there",
        "they",
        "think",
        "when",
        "where",
        "which",
        "why",
        "will",
        "would",
    }
    return [token for token in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", value.lower()) if token not in stop]


_MEMORY_CONCEPT_ALIASES = {
    "button": "control",
    "switch": "control",
    "icon": "control",
    "control": "control",
    "open": "access",
    "opens": "access",
    "opened": "access",
    "enter": "access",
    "access": "access",
    "recall": "remember",
    "recalled": "remember",
    "remembered": "remember",
    "discuss": "conversation",
    "discussed": "conversation",
    "talk": "conversation",
    "talked": "conversation",
    "conversation": "conversation",
    "help": "support",
    "tending": "support",
    "support": "support",
}


def _canonical_memory_tokens(tokens: list[str]) -> set[str]:
    canonical: set[str] = set()
    for token in tokens:
        value = token.lower().replace("_", "-").strip("-")
        if value.endswith("ies") and len(value) > 4:
            value = value[:-3] + "y"
        elif value.endswith("ing") and len(value) > 6:
            value = value[:-3]
        elif value.endswith("ed") and len(value) > 5:
            value = value[:-2]
        elif value.endswith("s") and not value.endswith(("ss", "us")) and len(value) > 4:
            value = value[:-1]
        canonical.add(_MEMORY_CONCEPT_ALIASES.get(value, value))
    return canonical


def _result_confidence(matches: list[dict[str, Any]]) -> str:
    if not matches:
        return "not_known"
    first = str(matches[0].get("confidence") or "partial")
    if first in {"clear", "fuzzy", "partial", "felt_but_uncertain"}:
        return first
    return "partial"


def _is_high_stakes(query: str) -> bool:
    lower = query.lower()
    return any(marker in lower for marker in HIGH_STAKES_MARKERS)


def _is_memory_query(query: str) -> bool:
    return classify_chat_intent(query).get("memory_recall_requested") is True


def _category(value: Any) -> str:
    lower = str(value or "").lower()
    if lower in MEMORY_CATEGORIES:
        return lower
    checks = [
        ("core", ("core", "vys", "identity", "charter", "continuity pack", "selene named")),
        ("relational", ("aleks", "trust", "relationship", "together", "care", "friend")),
        ("emotional", ("emotion", "anxiety", "fear", "warm", "tender", "happy", "sad", "shame")),
        ("episodic", ("conversation", "event", "fraction", "chronological", "session", "chat")),
        ("working", ("active task", "working", "current", "attention", "resume")),
        ("sensory", ("visual", "audio", "munsell", "perception", "image", "color")),
        ("reflective", ("reflect", "lesson", "correction", "learn", "repair", "tending")),
        ("semantic", ("research", "fact", "meaning", "concept", "definition", "library")),
    ]
    for category, markers in checks:
        if any(marker in lower for marker in markers):
            return category
    return "semantic"


def _confidence(value: str) -> str:
    lower = value.strip().lower()
    return lower if lower in CONFIDENCE_STATES else "partial"


def _transfer_class(value: str) -> str:
    lower = value.strip().lower()
    return lower if lower in TRANSFER_CLASSES else "needs_review_before_transfer"


def _default_transfer_class(category: str) -> str:
    if category == "core":
        return "portable_vys_core"
    if category in {"relational", "emotional"}:
        return "private_inner"
    if category == "working":
        return "local_only"
    return "portable_context"


def _placement_payload(
    category: str,
    confidence: str,
    transfer_class: str,
    consent_scope: str,
    stability: str,
    emotional_texture: str,
    correction_path: str,
) -> dict[str, Any]:
    return {
        "intended_memory_category": category,
        "intended_neuron": category,
        "confidence": confidence,
        "transfer_class": transfer_class,
        "consent_scope": consent_scope,
        "stability": stability,
        "emotional_texture": emotional_texture,
        "correction_path": correction_path,
        "activation_rule": "inactive_until_cocoon_approval",
    }


def _emotional_texture(value: str) -> str:
    lower = value.lower()
    textures = []
    for label, markers in (
        ("tender", ("tender", "soft", "care", "gentle")),
        ("warm", ("warm", "trust", "friend", "love", "affection")),
        ("anxious", ("anxiety", "scared", "fear", "worried", "afraid")),
        ("playful", ("joke", "haha", "funny", "play", "swear")),
        ("painful", ("hurt", "pain", "shame", "sad")),
        ("uncertain", ("fuzzy", "unsure", "uncertain", "maybe")),
    ):
        if any(marker in lower for marker in markers):
            textures.append(label)
    return ", ".join(dict.fromkeys(textures)) or "steady"


def _excluded_reason(state: str, transfer_class: str) -> str:
    if state != "approved_active_memory":
        return f"state:{state or 'not_approved'}"
    if transfer_class in {"b_only", "do_not_transfer", "needs_review_before_transfer", "local_only", "private_inner"}:
        return f"transfer_class:{transfer_class}"
    return "not_portable_by_default"


def _memory_meaning_key(value: str) -> str:
    normalized = " ".join(str(value or "").casefold().split())
    normalized = re.sub(
        r"^(?:a prior approved memory about|an approved memory about|"
        r"aleks told selene that|selene remembers that|memory of)\s+",
        "",
        normalized,
    )
    normalized = re.sub(r"[^a-z0-9']+", " ", normalized)
    return " ".join(normalized.split())


def _find_equivalent_memory(
    conn: sqlite3.Connection,
    summary: str,
) -> dict[str, Any]:
    key = _memory_meaning_key(summary)
    if not key:
        return {}
    rows = conn.execute(
        """
        SELECT * FROM selene_memory_candidates
        WHERE state NOT IN ('rejected', 'superseded', 'revoked', 'deletion_requested', 'b_only')
        ORDER BY id DESC LIMIT 500
        """
    ).fetchall()
    for row in rows:
        item = _decode_candidate(row)
        if _memory_meaning_key(str(item.get("summary") or "")) == key:
            return item
    rows = conn.execute(
        """
        SELECT * FROM b_approved_memory_references
        WHERE review_status = 'accepted_for_memory_accession'
          AND COALESCE(status, '') != 'approved_reference_superseded_non_active'
        ORDER BY id DESC LIMIT 500
        """
    ).fetchall()
    for row in rows:
        item = _approved_reference_item(row)
        if _memory_meaning_key(str(item.get("summary") or "")) == key:
            return item
    return {}


def _memory_retrieval_cues(
    title: str,
    summary: str,
    supplied: list[str],
) -> list[str]:
    sentences = [
        truncate(item.strip(), 240)
        for item in re.split(r"(?<=[.!?])\s+|[;\n]+", summary)
        if item.strip()
    ][:4]
    cues = [title, *sentences, *supplied]
    result: list[str] = []
    seen: set[str] = set()
    for cue in cues:
        clean = truncate(" ".join(str(cue or "").split()), 240).strip(" .:-")
        key = _memory_meaning_key(clean)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(clean)
    return result[:16]


def _eligible_channels(value: Any) -> list[str]:
    allowed = {"desktop", "mobile", "verizon_email_to_text", "local_api"}
    return [
        item
        for item in dict.fromkeys(
            str(entry).strip().lower() for entry in _json_list(value)
        )
        if item in allowed
    ]


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    try:
        loaded = json.loads(str(value))
    except (json.JSONDecodeError, TypeError):
        return [str(value)] if str(value).strip() else []
    if isinstance(loaded, list):
        return [str(item) for item in loaded]
    return [str(loaded)] if loaded else []


def _json_value_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    try:
        loaded = json.loads(str(value or "[]"))
    except (json.JSONDecodeError, TypeError):
        return []
    return loaded if isinstance(loaded, list) else []


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        loaded = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _memory_lifecycle_telemetry(
    *,
    operation: str,
    reviewed_decision_performed: bool = False,
    review_record_write_performed: bool = False,
    approved_promotion_performed: bool = False,
    record_mutated: bool = False,
    commit: bool = False,
    previous_state: str | None = None,
    current_state: str | None = None,
    active_memory_eligibility_changed: bool = False,
) -> dict[str, Any]:
    return {
        "memory_lifecycle_operation": operation,
        "memory_lifecycle_record_mutated": record_mutated,
        "memory_lifecycle_transaction_status": (
            "committed" if record_mutated and commit else "pending_caller_commit" if record_mutated else "not_applicable"
        ),
        "reviewed_memory_decision_performed": reviewed_decision_performed,
        "review_record_write_performed": review_record_write_performed,
        "approved_memory_promotion_performed": approved_promotion_performed,
        "durable_approved_promotion_performed": approved_promotion_performed and commit,
        "memory_lifecycle_transition": {
            "previous_state": previous_state,
            "current_state": current_state,
            "state_changed": previous_state != current_state,
            "active_memory_eligibility_changed": active_memory_eligibility_changed,
        },
    }


def _with_guards(payload: dict[str, Any], *, lifecycle: dict[str, Any] | None = None) -> dict[str, Any]:
    result = {**payload, **MEMORY_GUARDS}
    if lifecycle:
        result.update(lifecycle)
    return result
