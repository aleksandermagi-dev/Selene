from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .chat_intent import classify_chat_intent
from .registry import truncate
from .semantic_relevance import evaluate_semantic_relevance
from .transfer_state import transfer_completion_is_approved


MEMORY_ORGAN_BOUNDARY = "selene_vys_memory_organ_reviewed_no_raw_import_no_hidden_write"

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
    retrieval_eligible_count = _retrieval_eligible_count(conn)
    memory_review_count = sum(1 for item in items if item.get("display_region") == "cocoon_memory_review")
    support_only_count = sum(1 for item in items if item.get("display_region") == "cocoon_support")
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
                "raw_corpus_recall": False,
                "legacy_memory_write_flag": (
                    "memory_write_active means hidden or unreviewed active-memory retention only; "
                    "typed lifecycle telemetry reports review-record and approved-promotion writes"
                ),
            },
            "resident_memory_contract_version": "v3_typed_lifecycle_telemetry",
            "dream_state_may_propose_not_promote": True,
            "raw_corpus_loaded": False,
            "raw_archive_recall_active": False,
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
    proposal_payload = {
        "proposal_note": payload.get("proposal_note") or "",
        "placement": placement,
        "origin_session_id": payload.get("origin_session_id"),
        "origin_channel": payload.get("origin_channel") or "",
        "origin_kind": payload.get("origin_kind") or "manual",
        "aleks_consent_text": truncate(str(payload.get("aleks_consent_text") or ""), 500),
        "consent_recorded": payload.get("consent_recorded") is True,
        **MEMORY_GUARDS,
    }
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
    else:
        raise ValueError("unknown memory decision action")
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


def retrieve_memory(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    query = truncate(str(payload.get("query") or payload.get("text") or ""), 1000)
    limit = max(1, min(int(payload.get("limit") or 4), 12))
    intent_decision = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else classify_chat_intent(query)
    explicit_recall = intent_decision.get("memory_recall_requested") is True
    contextual_relevance = payload.get("allow_contextual_relevance") is True
    retrieval_mode = "explicit_recall" if explicit_recall else "contextual_relevance" if contextual_relevance else "not_requested"
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
            }
        )
    items = _approved_memory_items(conn, limit=100)
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
                "explicit_recall": explicit_recall,
            }
        )
        annotated = {**item, "semantic_relevance": relevance}
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
            }
        )
    confidence = _result_confidence(matches)
    transfer_class = str(matches[0].get("transfer_class") or "portable_context")
    return _with_guards(
        {
            "status": "memory_retrieval_ready",
            "recall_state": confidence,
            "memory_context_used": True,
            "retrieval_mode": retrieval_mode,
            "contextual_recall": retrieval_mode == "contextual_relevance",
            "memory_source_class": "approved_memory_index",
            "memory_confidence": confidence,
            "memory_transfer_class": transfer_class,
            "graceful_fall_used": confidence != "clear",
            "items": matches,
            "semantic_relevance_held_count": len(held_matches),
            "semantic_source_gate_applied": True,
            "intent_decision": intent_decision,
            "source_refs": [ref for item in matches for ref in _json_list(item.get("source_refs"))],
            "answer_guidance": (
                "Let the approved memory inform the current answer without replacing the present conversation."
                if retrieval_mode == "contextual_relevance"
                else "Use clear memory plainly; use fuzzy/partial memory with visible uncertainty."
            ),
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


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
        item = _decode_candidate(row)
        if not category or item.get("memory_category") == category:
            items.append(item)
    if len(items) < limit:
        for row in conn.execute(
            "SELECT * FROM b_approved_memory_references ORDER BY id DESC LIMIT ?",
            (limit - len(items),),
        ).fetchall():
            item = _approved_reference_item(row)
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
    }


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
    tokens = set(query_tokens)
    ranked: list[tuple[int, dict[str, Any]]] = []
    for item in items:
        haystack = " ".join(
            [
                str(item.get("title") or ""),
                str(item.get("summary") or ""),
                str(item.get("memory_category") or ""),
                str(item.get("emotional_texture") or ""),
            ]
        )
        haystack_tokens = _tokens(haystack)
        item_tokens = set(haystack_tokens)
        overlap = tokens & item_tokens
        score = len(overlap)
        if tokens and score == 0:
            continue
        if not _meaningful_memory_overlap(overlap, item, query_tokens=query_tokens, haystack_tokens=haystack_tokens):
            continue
        ranked.append((score, {**item, "match_score": score}))
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
