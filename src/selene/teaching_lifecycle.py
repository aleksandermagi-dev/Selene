from __future__ import annotations

import json
import re
import sqlite3
from difflib import SequenceMatcher
from typing import Any

from .comprehension_integration import (
    decide_comprehension_concept,
    evaluate_understanding,
    retrieve_approved_knowledge,
)
from .education_expression_law import review_education_expression
from .intelligence_os import run_intelligence_os_reason
from .registry import truncate


TEACHING_LIFECYCLE_BOUNDARY = (
    "inspectable_acquire_integrate_express_knowledge_lifecycle_only_"
    "not_identity_governance_personality_memory_training_or_authority"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "identity_change": False,
    "governance_change": False,
    "personality_change": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "teaching_material_is_governance": False,
    "knowledge_retention_requires_review": True,
    "knowledge_retention_requires_aleks_approval": "bounded_curriculum_authorization_or_item_exception",
    "source_parroting_allowed": False,
}

CONTRADICTION_CLASSES = {
    "none_identified",
    "compatible_scope_difference",
    "tension_requires_review",
    "direct_conflict",
    "insufficient_evidence",
}

INTEGRATION_CONFIDENCE_LEVELS = {"low", "developing", "bounded", "strong"}


def teaching_lifecycle_status(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN acquire_status = 'complete' THEN 1 ELSE 0 END) AS acquired,
               SUM(CASE WHEN integrate_status = 'complete' THEN 1 ELSE 0 END) AS integrated,
               SUM(CASE WHEN express_status = 'complete' THEN 1 ELSE 0 END) AS expressed,
               SUM(CASE WHEN approval_status IN ('approved_by_aleks', 'approved_under_curriculum_authorization') THEN 1 ELSE 0 END) AS approved
        FROM selene_teaching_lifecycles
        """
    ).fetchone()
    return _with_guards(
        {
            "status": "teaching_lifecycle_ready",
            "version": "phase_4_acquire_integrate_express",
            "lifecycle_count": int(row["total"] or 0),
            "acquired_count": int(row["acquired"] or 0),
            "integrated_count": int(row["integrated"] or 0),
            "expressed_count": int(row["expressed"] or 0),
            "approved_count": int(row["approved"] or 0),
            "stages": [
                {"stage": "acquire", "owner": "Comprehension", "retains_knowledge": False},
                {"stage": "integrate", "owner": "intelligenceOS + Comprehension", "retains_knowledge": False},
                {"stage": "express", "owner": "NLO + Voice", "retains_knowledge": False},
            ],
            "approval_rule": "Retention requires either an explicit Aleks item decision or an active bounded curriculum authorization recorded by Aleks; exceptions always return to Cocoon.",
            "education_expression_personality_law_active": True,
            "education_may_expand_capability_and_contextual_expression": True,
            "education_may_change_personality": False,
            "review_destination": "Cocoon Teaching / Lessons",
            "review_status": "status_only",
            "provenance_boundary": TEACHING_LIFECYCLE_BOUNDARY,
        }
    )


def list_teaching_lifecycles(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 100), 500))
    rows = conn.execute(
        """
        SELECT lifecycle.*, concept.title, concept.domain, concept.state AS concept_state,
               concept.retention_state, concept.chat_use_permission
        FROM selene_teaching_lifecycles AS lifecycle
        JOIN selene_comprehension_concepts AS concept ON concept.id = lifecycle.concept_id
        ORDER BY lifecycle.updated_at DESC, lifecycle.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return _with_guards(
        {
            "status": "teaching_lifecycles_ready",
            "items": [_decode_lifecycle(row) for row in rows],
            "review_destination": "Cocoon Teaching / Lessons",
            "review_status": "status_only",
            "provenance_boundary": TEACHING_LIFECYCLE_BOUNDARY,
        }
    )


def get_teaching_lifecycle(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    lifecycle_ref = _lifecycle_for_payload(conn, payload)
    if not lifecycle_ref:
        raise ValueError("teaching lifecycle not found")
    lifecycle = _lifecycle_row(conn, int(lifecycle_ref["id"]))
    runs = conn.execute(
        "SELECT * FROM selene_teaching_lifecycle_runs WHERE lifecycle_id = ? ORDER BY id ASC",
        (lifecycle["id"],),
    ).fetchall()
    return _with_guards(
        {
            "status": "teaching_lifecycle_detail_ready",
            "item": lifecycle,
            "stage_history": [_decode_run(row) for row in runs],
            "review_destination": "Cocoon Teaching / Lessons",
            "review_status": "status_only",
            "provenance_boundary": TEACHING_LIFECYCLE_BOUNDARY,
        }
    )


def acquire_teaching_item(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_authority_change(payload)
    concept = _concept_for_payload(conn, payload)
    _require_editable_candidate(concept)

    concepts = _text_list(payload.get("concepts")) or [
        concept["central_claim"],
        *_json_text_list(concept.get("principles_json")),
    ]
    vocabulary = _text_list(payload.get("vocabulary"))
    relationships = _text_list(payload.get("relationships")) or _json_text_list(concept.get("relationships_json"))
    examples = _text_list(payload.get("examples")) or _json_text_list(concept.get("examples_json"))
    uncertainties = _text_list(payload.get("uncertainties")) or _json_text_list(concept.get("limits_json"))
    distinctions = _text_list(payload.get("near_concept_distinctions")) or _json_text_list(concept.get("counterexamples_json"))
    source_refs = _json_list(concept.get("source_refs"))

    missing = [
        name
        for name, values in (
            ("concepts", concepts),
            ("vocabulary", vocabulary),
            ("examples", examples),
            ("uncertainties", uncertainties),
            ("source_provenance", source_refs),
            ("near_concept_distinctions", distinctions),
        )
        if not values
    ]
    law_review = _education_expression_review(
        payload,
        [*concepts, *vocabulary, *relationships, *examples, *uncertainties, *distinctions],
    )
    if law_review["permitted"] is not True:
        missing.append("education_expression_personality_law")
    snapshot = {
        "stage": "acquire",
        "status": "complete" if not missing else "needs_review",
        "concept_id": int(concept["id"]),
        "concepts": concepts[:30],
        "vocabulary": vocabulary[:30],
        "relationships": relationships[:30],
        "relationship_state": "relationships_recorded" if relationships else "no_relationships_identified",
        "examples": examples[:30],
        "uncertainties": uncertainties[:30],
        "source_provenance": source_refs[:100],
        "near_concept_distinctions": distinctions[:30],
        "education_expression_personality_law": law_review,
        "missing_fields": missing,
        "knowledge_retained": False,
        "review_status": "stage_snapshot_reviewable",
        "provenance_boundary": TEACHING_LIFECYCLE_BOUNDARY,
    }
    lifecycle = _ensure_lifecycle(conn, concept, source_refs)
    conn.execute(
        """
        UPDATE selene_teaching_lifecycles
        SET current_stage = ?, acquire_status = ?, acquire_json = ?,
            integrate_status = 'not_started', integrate_json = '{}',
            express_status = 'not_started', express_json = '{}',
            approval_status = 'awaiting_aleks_review', approval_mode = 'awaiting_decision',
            authorization_id = NULL, authorization_snapshot_json = '{}', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            "acquire_complete" if not missing else "acquire_needs_review",
            snapshot["status"],
            json.dumps(snapshot, sort_keys=True),
            lifecycle["id"],
        ),
    )
    conn.commit()
    run_id = _store_run(conn, lifecycle["id"], int(concept["id"]), "acquire", snapshot, source_refs)
    return _stage_result(conn, lifecycle["id"], "acquire", snapshot, run_id)


def integrate_teaching_item(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_authority_change(payload)
    lifecycle = _require_lifecycle_stage(conn, payload, "acquire")
    concept = _concept_row(conn, int(lifecycle["concept_id"]))
    _require_editable_candidate(concept)

    contradiction_class = str(payload.get("contradiction_classification") or "").strip()
    if contradiction_class not in CONTRADICTION_CLASSES:
        raise ValueError("contradiction_classification must be a supported bounded classification")
    confidence = str(payload.get("integration_confidence") or "").strip()
    if confidence not in INTEGRATION_CONFIDENCE_LEVELS:
        raise ValueError("integration_confidence must be low, developing, bounded, or strong")

    supporting = _approved_concepts(conn, _int_list(payload.get("supporting_concept_ids")))
    conflicting = _approved_concepts(conn, _int_list(payload.get("conflicting_concept_ids")))
    related = _approved_concepts(conn, _int_list(payload.get("related_concept_ids")))
    scope = truncate(str(payload.get("scope_of_application") or ""), 3000).strip()
    unresolved = _text_list(payload.get("unresolved_questions"))
    correction_path = truncate(
        str(payload.get("correction_path") or "Return to source-linked Cocoon review and revise the candidate without discarding useful structure."),
        1200,
    ).strip()
    reopening_path = truncate(
        str(payload.get("reopening_path") or "Reopen when a contradiction, correction, or poor-fit application appears."),
        1200,
    ).strip()
    missing = [name for name, value in (("scope_of_application", scope), ("correction_path", correction_path), ("reopening_path", reopening_path)) if not value]
    if contradiction_class == "direct_conflict" and not conflicting and not unresolved:
        missing.append("conflict_evidence_or_unresolved_question")

    law_review = _education_expression_review(
        payload,
        [scope, *unresolved, correction_path, reopening_path],
    )
    if law_review["permitted"] is not True:
        missing.append("education_expression_personality_law")

    suggestions = retrieve_approved_knowledge(
        conn,
        f"{concept['title']} {concept['central_claim']}",
        limit=10,
    )
    suggested = [item for item in suggestions.get("items") or [] if int(item.get("id") or 0) != int(concept["id"])]
    reasoning = run_intelligence_os_reason(
        conn,
        {
            "prompt": f"Review how the teaching concept '{concept['title']}' fits approved knowledge within its stated scope.",
            "observations": [
                f"Source-bound concept: {concept['central_claim']}",
                f"Scope of application: {scope or 'not yet supplied'}",
                f"Contradiction classification: {contradiction_class}",
                *[f"Unresolved question: {item}" for item in unresolved[:5]],
            ],
            "candidate_models": [
                *[f"supporting relationship with {item['title']}" for item in supporting],
                *[f"conflicting relationship with {item['title']}" for item in conflicting],
                *[f"related relationship with {item['title']}" for item in related],
                "bounded application map with explicit correction and reopening paths",
            ],
            "source_refs": _json_list(concept.get("source_refs")),
        },
    )
    snapshot = {
        "stage": "integrate",
        "status": "complete" if not missing else "needs_review",
        "concept_id": int(concept["id"]),
        "relationships_to_approved_knowledge": {
            "supporting": supporting,
            "conflicting": conflicting,
            "related": related,
            "suggested_for_review_only": suggested,
        },
        "supporting_concepts": supporting,
        "conflicting_concepts": conflicting,
        "scope_of_application": scope,
        "contradiction_classification": contradiction_class,
        "unresolved_questions": unresolved,
        "correction_path": correction_path,
        "reopening_path": reopening_path,
        "integration_confidence": confidence,
        "confidence_boundary": "Integration confidence describes fit of this reviewed map, not factual certainty or sentence fluency.",
        "education_expression_personality_law": law_review,
        "intelligence_os_support": {
            "run_id": reasoning.get("run_id"),
            "status": reasoning.get("status"),
            "reasoning_summary": reasoning.get("reasoning_summary"),
            "selected_next_step": reasoning.get("selected_next_step"),
            "confidence": reasoning.get("confidence"),
            "visible_summary_only": reasoning.get("visible_summary_only") is True,
        },
        "missing_fields": missing,
        "knowledge_retained": False,
        "review_status": "stage_snapshot_reviewable",
        "provenance_boundary": TEACHING_LIFECYCLE_BOUNDARY,
    }
    conn.execute(
        """
        UPDATE selene_teaching_lifecycles
        SET current_stage = ?, integrate_status = ?, integrate_json = ?,
            express_status = 'not_started', express_json = '{}',
            approval_status = 'awaiting_aleks_review', approval_mode = 'awaiting_decision',
            authorization_id = NULL, authorization_snapshot_json = '{}', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            "integrate_complete" if not missing else "integrate_needs_review",
            snapshot["status"],
            json.dumps(snapshot, sort_keys=True),
            lifecycle["id"],
        ),
    )
    conn.commit()
    run_id = _store_run(conn, lifecycle["id"], int(concept["id"]), "integrate", snapshot, _json_list(concept.get("source_refs")))
    return _stage_result(conn, lifecycle["id"], "integrate", snapshot, run_id)


def express_teaching_item(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_authority_change(payload)
    lifecycle = _require_lifecycle_stage(conn, payload, "integrate")
    concept = _concept_row(conn, int(lifecycle["concept_id"]))
    _require_editable_candidate(concept)

    explanation = truncate(str(payload.get("explanation") or payload.get("teach_back") or ""), 3000).strip()
    distinct_examples = _text_list(payload.get("distinct_examples") or payload.get("application"))
    analogies = _text_list(payload.get("analogies"))
    questions = _text_list(payload.get("questions"))
    comparisons = _text_list(payload.get("comparisons"))
    participation = truncate(str(payload.get("conversational_participation") or ""), 3000).strip()
    source_alignment = payload.get("source_alignment") is True
    source_fragments = [
        concept["central_claim"],
        *_json_text_list(concept.get("principles_json")),
        *_json_text_list(concept.get("examples_json")),
    ]
    copy_checks = {
        "explanation": _max_copy_ratio(explanation, source_fragments),
        "distinct_examples": _max_list_copy_ratio(distinct_examples, source_fragments),
        "analogies": _max_list_copy_ratio(analogies, source_fragments),
        "questions": _max_list_copy_ratio(questions, source_fragments),
        "comparisons": _max_list_copy_ratio(comparisons, source_fragments),
        "conversational_participation": _max_copy_ratio(participation, source_fragments),
    }
    no_source_parroting = all(value < 0.9 for value in copy_checks.values())
    acquire = lifecycle.get("acquire") if isinstance(lifecycle.get("acquire"), dict) else {}
    limits = _text_list(payload.get("limits")) or _json_text_list(concept.get("limits_json")) or _text_list(acquire.get("uncertainties"))
    counterexamples = _text_list(payload.get("counterexamples")) or _json_text_list(concept.get("counterexamples_json")) or _text_list(acquire.get("near_concept_distinctions"))
    correction_response = truncate(str(payload.get("correction_response") or ""), 1800).strip()

    missing: list[str] = []
    for name, present in (
        ("explanation_in_original_language", len(explanation) >= 30),
        ("distinct_examples", any(len(item) >= 25 for item in distinct_examples)),
        ("analogies", bool(analogies)),
        ("questions", bool(questions)),
        ("comparisons", bool(comparisons)),
        ("natural_conversational_participation", len(participation) >= 30),
        ("source_alignment", source_alignment),
        ("no_source_parroting", no_source_parroting),
    ):
        if not present:
            missing.append(name)

    evaluation = evaluate_understanding(
        conn,
        {
            "concept_id": int(concept["id"]),
            "teach_back": explanation,
            "application": distinct_examples[0] if distinct_examples else "",
            "limits": limits,
            "counterexample": counterexamples[0] if counterexamples else "",
            "correction_response": correction_response,
            "source_alignment": source_alignment,
        },
    )
    if evaluation.get("understanding_evidence_sufficient") is not True:
        missing.append("comprehension_evidence")
    law_review = _education_expression_review(
        payload,
        [
            explanation,
            *distinct_examples,
            *analogies,
            *questions,
            *comparisons,
            participation,
            *limits,
            *counterexamples,
            correction_response,
        ],
    )
    if law_review["permitted"] is not True:
        missing.append("education_expression_personality_law")
    missing = list(dict.fromkeys(missing))
    snapshot = {
        "stage": "express",
        "status": "complete" if not missing else "needs_review",
        "concept_id": int(concept["id"]),
        "explanation_in_original_language": explanation,
        "distinct_examples": distinct_examples,
        "analogies": analogies,
        "questions": questions,
        "comparisons": comparisons,
        "natural_conversational_participation": participation,
        "limits": limits,
        "counterexamples": counterexamples,
        "correction_response": correction_response,
        "source_alignment_confirmed": source_alignment,
        "source_parroting_check": {
            "passed": no_source_parroting,
            "maximum_copy_ratios": copy_checks,
            "threshold": 0.9,
        },
        "understanding_evaluation": {
            "run_id": evaluation.get("run_id"),
            "status": evaluation.get("status"),
            "sufficient": evaluation.get("understanding_evidence_sufficient") is True,
            "passed_core_dimension_count": evaluation.get("passed_core_dimension_count"),
            "required_core_dimension_count": evaluation.get("required_core_dimension_count"),
        },
        "education_expression_personality_law": law_review,
        "missing_fields": missing,
        "knowledge_retained": False,
        "expression_handoff": {
            "nlo_may_shape_language_after_approval": not missing,
            "voice_remains_selene_expression_layer": True,
            "chat_use_before_approval": False,
        },
        "review_status": "stage_snapshot_reviewable",
        "provenance_boundary": TEACHING_LIFECYCLE_BOUNDARY,
    }
    conn.execute(
        """
        UPDATE selene_teaching_lifecycles
        SET current_stage = ?, express_status = ?, express_json = ?,
            approval_status = 'awaiting_aleks_review', approval_mode = 'awaiting_decision',
            authorization_id = NULL, authorization_snapshot_json = '{}', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            "express_complete_awaiting_aleks_review" if not missing else "express_needs_review",
            snapshot["status"],
            json.dumps(snapshot, sort_keys=True),
            lifecycle["id"],
        ),
    )
    conn.commit()
    run_id = _store_run(conn, lifecycle["id"], int(concept["id"]), "express", snapshot, _json_list(concept.get("source_refs")))
    return _stage_result(conn, lifecycle["id"], "express", snapshot, run_id)


def approve_teaching_lifecycle(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_authority_change(payload)
    lifecycle = _lifecycle_for_payload(conn, payload)
    if not lifecycle:
        raise ValueError("teaching lifecycle not found")
    if payload.get("aleks_approved") is not True or str(payload.get("approval_actor") or "").strip() != "Aleks":
        raise ValueError("retention requires explicit Aleks approval")
    if any(lifecycle[f"{stage}_status"] != "complete" for stage in ("acquire", "integrate", "express")):
        raise ValueError("retention requires complete Acquire, Integrate, and Express stages")

    law_review = _review_stored_lifecycle_expression(lifecycle)
    if law_review["permitted"] is not True:
        raise ValueError("retention requires education-expression-personality law compliance")

    decision = decide_comprehension_concept(
        conn,
        {"concept_id": int(lifecycle["concept_id"]), "action": "approve_knowledge"},
    )
    snapshot = {
        "stage": "approval",
        "status": "approved_by_aleks",
        "concept_id": int(lifecycle["concept_id"]),
        "approval_actor": "Aleks",
        "explicit_approval": True,
        "knowledge_resource_active": decision.get("knowledge_resource_active") is True,
        "retention_state": (decision.get("item") or {}).get("retention_state"),
        "chat_use_permission": (decision.get("item") or {}).get("chat_use_permission"),
        "memory_created": False,
        "identity_changed": False,
        "governance_changed": False,
        "personality_changed": False,
        "education_expression_personality_law": law_review,
        "review_status": "aleks_retention_decision",
        "provenance_boundary": TEACHING_LIFECYCLE_BOUNDARY,
    }
    conn.execute(
        """
        UPDATE selene_teaching_lifecycles
        SET current_stage = 'approved_knowledge_resource', approval_status = 'approved_by_aleks',
            approval_mode = 'item_exception_approval', authorization_id = NULL,
            authorization_snapshot_json = '{}',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (lifecycle["id"],),
    )
    conn.commit()
    concept = decision.get("item") or {}
    run_id = _store_run(conn, lifecycle["id"], int(lifecycle["concept_id"]), "approval", snapshot, _json_list(concept.get("source_refs")))
    result = _stage_result(conn, lifecycle["id"], "approval", snapshot, run_id)
    result["decision"] = decision
    return result


def approve_teaching_lifecycle_under_authorization(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    authorization_decision: dict[str, Any],
) -> dict[str, Any]:
    """Retain a completed lifecycle covered by a previously recorded Aleks authorization.

    This is deliberately not exposed as a router action.  The curriculum
    authorization module must first perform the scope and exception checks.
    """
    _reject_authority_change(payload)
    lifecycle = _lifecycle_for_payload(conn, payload)
    if not lifecycle:
        raise ValueError("teaching lifecycle not found")
    if any(lifecycle[f"{stage}_status"] != "complete" for stage in ("acquire", "integrate", "express")):
        raise ValueError("retention requires complete Acquire, Integrate, and Express stages")
    authorization_id = int(authorization_decision.get("authorization_id") or 0)
    if authorization_decision.get("decision") != "covered_by_active_authorization" or authorization_id <= 0:
        raise ValueError("curriculum authorization did not cover this teaching lifecycle")
    authorization = conn.execute(
        "SELECT * FROM selene_curriculum_authorizations WHERE id = ? AND status = 'active'",
        (authorization_id,),
    ).fetchone()
    if not authorization or authorization["authorized_by"] != "Aleks":
        raise ValueError("an active Aleks curriculum authorization is required")

    law_review = _review_stored_lifecycle_expression(lifecycle)
    if law_review["permitted"] is not True:
        raise ValueError("retention requires education-expression-personality law compliance")
    decision = decide_comprehension_concept(
        conn,
        {"concept_id": int(lifecycle["concept_id"]), "action": "approve_knowledge"},
    )
    snapshot = {
        "stage": "approval",
        "status": "approved_under_curriculum_authorization",
        "concept_id": int(lifecycle["concept_id"]),
        "approval_actor": "Aleks",
        "explicit_item_approval": False,
        "authorization_id": authorization_id,
        "authorization_key": authorization["authorization_key"],
        "authorization_decision": authorization_decision,
        "knowledge_resource_active": decision.get("knowledge_resource_active") is True,
        "retention_state": (decision.get("item") or {}).get("retention_state"),
        "chat_use_permission": (decision.get("item") or {}).get("chat_use_permission"),
        "memory_created": False,
        "identity_changed": False,
        "governance_changed": False,
        "personality_changed": False,
        "education_expression_personality_law": law_review,
        "review_status": "bounded_curriculum_authorization_retention",
        "provenance_boundary": TEACHING_LIFECYCLE_BOUNDARY,
    }
    conn.execute(
        """
        UPDATE selene_teaching_lifecycles
        SET current_stage = 'approved_knowledge_resource',
            approval_status = 'approved_under_curriculum_authorization',
            approval_mode = 'curriculum_authorization', authorization_id = ?,
            authorization_snapshot_json = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (authorization_id, json.dumps(authorization_decision, sort_keys=True), lifecycle["id"]),
    )
    conn.commit()
    concept = decision.get("item") or {}
    run_id = _store_run(
        conn,
        lifecycle["id"],
        int(lifecycle["concept_id"]),
        "approval",
        snapshot,
        _json_list(concept.get("source_refs")),
    )
    result = _stage_result(conn, lifecycle["id"], "approval", snapshot, run_id)
    result["decision"] = decision
    return result


def _stage_result(
    conn: sqlite3.Connection,
    lifecycle_id: int,
    stage: str,
    snapshot: dict[str, Any],
    run_id: int,
) -> dict[str, Any]:
    return _with_guards(
        {
            "status": f"teaching_{stage}_{snapshot['status']}",
            "stage": stage,
            "stage_complete": snapshot["status"] in {"complete", "approved_by_aleks", "approved_under_curriculum_authorization"},
            "snapshot": snapshot,
            "item": _lifecycle_row(conn, lifecycle_id),
            "run_id": run_id,
            "review_destination": "Cocoon Teaching / Lessons",
            "review_status": "status_only",
            "provenance_boundary": TEACHING_LIFECYCLE_BOUNDARY,
        }
    )


def _ensure_lifecycle(conn: sqlite3.Connection, concept: dict[str, Any], source_refs: list[str]) -> dict[str, Any]:
    existing = conn.execute(
        "SELECT * FROM selene_teaching_lifecycles WHERE concept_id = ?",
        (int(concept["id"]),),
    ).fetchone()
    if existing:
        return dict(existing)
    cursor = conn.execute(
        """
        INSERT INTO selene_teaching_lifecycles
        (lifecycle_key, concept_id, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?)
        """,
        (
            f"teaching_lifecycle_concept_{int(concept['id'])}",
            int(concept["id"]),
            json.dumps(source_refs, sort_keys=True),
            TEACHING_LIFECYCLE_BOUNDARY,
        ),
    )
    conn.commit()
    return dict(conn.execute("SELECT * FROM selene_teaching_lifecycles WHERE id = ?", (int(cursor.lastrowid),)).fetchone())


def _require_lifecycle_stage(conn: sqlite3.Connection, payload: dict[str, Any], prerequisite: str) -> dict[str, Any]:
    lifecycle = _lifecycle_for_payload(conn, payload)
    if not lifecycle:
        raise ValueError("teaching lifecycle not found; Acquire must be completed first")
    if lifecycle[f"{prerequisite}_status"] != "complete":
        raise ValueError(f"{prerequisite.title()} must be complete before the next teaching stage")
    return lifecycle


def _lifecycle_for_payload(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any] | None:
    lifecycle_id = int(payload.get("lifecycle_id") or 0)
    concept_id = int(payload.get("concept_id") or payload.get("id") or 0)
    if lifecycle_id > 0:
        row = conn.execute("SELECT * FROM selene_teaching_lifecycles WHERE id = ?", (lifecycle_id,)).fetchone()
    elif concept_id > 0:
        row = conn.execute("SELECT * FROM selene_teaching_lifecycles WHERE concept_id = ?", (concept_id,)).fetchone()
    else:
        row = None
    return _decode_lifecycle(row) if row else None


def _lifecycle_row(conn: sqlite3.Connection, lifecycle_id: int) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT lifecycle.*, concept.title, concept.domain, concept.state AS concept_state,
               concept.retention_state, concept.chat_use_permission
        FROM selene_teaching_lifecycles AS lifecycle
        JOIN selene_comprehension_concepts AS concept ON concept.id = lifecycle.concept_id
        WHERE lifecycle.id = ?
        """,
        (lifecycle_id,),
    ).fetchone()
    if not row:
        raise ValueError("teaching lifecycle not found")
    return _decode_lifecycle(row)


def _concept_for_payload(conn: sqlite3.Connection, payload: dict[str, Any]) -> dict[str, Any]:
    concept_id = int(payload.get("concept_id") or payload.get("id") or 0)
    row = conn.execute("SELECT * FROM selene_comprehension_concepts WHERE id = ?", (concept_id,)).fetchone()
    if not row:
        raise ValueError("comprehension concept not found")
    return dict(row)


def _concept_row(conn: sqlite3.Connection, concept_id: int) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM selene_comprehension_concepts WHERE id = ?", (concept_id,)).fetchone()
    if not row:
        raise ValueError("comprehension concept not found")
    return dict(row)


def _require_editable_candidate(concept: dict[str, Any]) -> None:
    if concept["state"] == "approved_knowledge_resource":
        raise ValueError("approved knowledge must be explicitly reopened before revising its teaching lifecycle")
    if concept["state"] in {"superseded", "rejected"}:
        raise ValueError("inactive comprehension records cannot advance through the teaching lifecycle")
    if not _json_list(concept["source_refs"]):
        raise ValueError("source provenance is required for the teaching lifecycle")


def _approved_concepts(conn: sqlite3.Connection, concept_ids: list[int]) -> list[dict[str, Any]]:
    if not concept_ids:
        return []
    rows = conn.execute(
        f"""
        SELECT id, concept_key, title, domain, central_claim, confidence, source_refs
        FROM selene_comprehension_concepts
        WHERE id IN ({','.join('?' for _ in concept_ids)})
          AND state = 'approved_knowledge_resource'
          AND review_status = 'approved_for_knowledge_use'
          AND chat_use_permission = 'available_as_knowledge_resource'
        """,
        concept_ids,
    ).fetchall()
    found = {int(row["id"]) for row in rows}
    missing = [item for item in concept_ids if item not in found]
    if missing:
        raise ValueError(f"integration relationships require approved knowledge concept ids; unavailable: {missing}")
    by_id = {int(row["id"]): row for row in rows}
    return [
        {
            "id": concept_id,
            "concept_key": by_id[concept_id]["concept_key"],
            "title": by_id[concept_id]["title"],
            "domain": by_id[concept_id]["domain"],
            "central_claim": by_id[concept_id]["central_claim"],
            "confidence": by_id[concept_id]["confidence"],
            "source_refs": _json_list(by_id[concept_id]["source_refs"]),
        }
        for concept_id in concept_ids
    ]


def _store_run(
    conn: sqlite3.Connection,
    lifecycle_id: int,
    concept_id: int,
    stage: str,
    snapshot: dict[str, Any],
    source_refs: list[str],
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO selene_teaching_lifecycle_runs
        (lifecycle_id, concept_id, stage, status, snapshot_json, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lifecycle_id,
            concept_id,
            stage,
            str(snapshot.get("status") or "status_only"),
            json.dumps(snapshot, sort_keys=True),
            json.dumps(source_refs, sort_keys=True),
            TEACHING_LIFECYCLE_BOUNDARY,
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def _decode_lifecycle(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    item = dict(row)
    for stage in ("acquire", "integrate", "express"):
        item[stage] = _loads(item.pop(f"{stage}_json", "{}"), {})
    item["source_refs"] = _loads(item.get("source_refs"), [])
    item["authorization_snapshot"] = _loads(item.pop("authorization_snapshot_json", "{}"), {})
    item["stages"] = [
        {"stage": stage, "status": item[f"{stage}_status"], "snapshot": item[stage]}
        for stage in ("acquire", "integrate", "express")
    ]
    item["retention_gate"] = {
        "aleks_authority_required": True,
        "accepted_authority_modes": ["bounded_curriculum_authorization", "item_exception_approval"],
        "approval_status": item["approval_status"],
        "approval_mode": item.get("approval_mode", "awaiting_decision"),
        "authorization_id": item.get("authorization_id"),
        "all_stages_complete": all(item[f"{stage}_status"] == "complete" for stage in ("acquire", "integrate", "express")),
        "chat_use_permission": item.get("chat_use_permission", "not_active_until_approved"),
    }
    return item


def _decode_run(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["snapshot"] = _loads(item.pop("snapshot_json", "{}"), {})
    item["source_refs"] = _loads(item.get("source_refs"), [])
    return item


def _max_copy_ratio(value: str, source_fragments: list[str]) -> float:
    normalized = _normalize(value)
    if not normalized:
        return 1.0
    ratios = [
        SequenceMatcher(None, normalized, _normalize(source)).ratio()
        for source in source_fragments
        if len(_normalize(source)) >= 20
    ]
    return round(max(ratios, default=0.0), 3)


def _max_list_copy_ratio(values: list[str], source_fragments: list[str]) -> float:
    return max((_max_copy_ratio(value, source_fragments) for value in values), default=0.0)


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value).lower()))


def _text_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [truncate(str(item), 1200).strip() for item in value if str(item).strip()][:50]
    if isinstance(value, str) and value.strip():
        return [truncate(item.strip(), 1200) for item in re.split(r"\r?\n|\s*;\s*", value) if item.strip()][:50]
    return []


def _json_text_list(value: Any) -> list[str]:
    return _text_list(_loads(value, []))


def _json_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        loaded = _loads(value, None)
        return [str(item) for item in loaded if str(item).strip()] if isinstance(loaded, list) else [value]
    return []


def _int_list(value: Any) -> list[int]:
    raw = value if isinstance(value, (list, tuple)) else ([] if value in (None, "") else [value])
    result: list[int] = []
    for item in raw:
        try:
            parsed = int(item)
        except (TypeError, ValueError):
            continue
        if parsed > 0 and parsed not in result:
            result.append(parsed)
    return result[:100]


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value or ""))
    except (json.JSONDecodeError, TypeError):
        return fallback


def _reject_authority_change(payload: dict[str, Any]) -> None:
    protected = (
        "activate",
        "activation_change",
        "identity_change",
        "governance_change",
        "personality_change",
        "memory_write_active",
        "runtime_memory_recall",
        "training_allowed",
        "lora_allowed",
        "autonomous_action_allowed",
        "self_replication_allowed",
    )
    if any(payload.get(key) not in (None, False, "", "none") for key in protected):
        raise ValueError("teaching lifecycle cannot change identity, governance, memory, activation, or authority")


def _education_expression_review(payload: dict[str, Any], teaching_texts: list[str]) -> dict[str, Any]:
    return review_education_expression(
        {
            "teaching_texts": [item for item in teaching_texts if item],
            "declared_effects": payload.get("declared_effects") or payload.get("educational_effects"),
            "register_guidance": payload.get("register_guidance"),
            "task_bound_register": payload.get("task_bound_register") is True,
            "personality_prescription": payload.get("personality_prescription") is True,
            "compulsory_affect": payload.get("compulsory_affect") is True,
            "fixed_generic_phrase_requirement": payload.get("fixed_generic_phrase_requirement") is True,
            "voice_bypass_requested": payload.get("voice_bypass_requested") is True,
            "identity_change_requested": payload.get("identity_change_requested") is True,
            "governance_change_requested": payload.get("governance_change_requested") is True,
        }
    )


def _review_stored_lifecycle_expression(lifecycle: dict[str, Any]) -> dict[str, Any]:
    acquire = lifecycle.get("acquire") if isinstance(lifecycle.get("acquire"), dict) else {}
    integrate = lifecycle.get("integrate") if isinstance(lifecycle.get("integrate"), dict) else {}
    express = lifecycle.get("express") if isinstance(lifecycle.get("express"), dict) else {}
    texts = [
        *_text_list(acquire.get("concepts")),
        *_text_list(acquire.get("vocabulary")),
        *_text_list(acquire.get("relationships")),
        *_text_list(acquire.get("examples")),
        *_text_list(acquire.get("uncertainties")),
        *_text_list(acquire.get("near_concept_distinctions")),
        str(integrate.get("scope_of_application") or ""),
        *_text_list(integrate.get("unresolved_questions")),
        str(integrate.get("correction_path") or ""),
        str(integrate.get("reopening_path") or ""),
        str(express.get("explanation_in_original_language") or ""),
        *_text_list(express.get("distinct_examples")),
        *_text_list(express.get("analogies")),
        *_text_list(express.get("questions")),
        *_text_list(express.get("comparisons")),
        str(express.get("natural_conversational_participation") or ""),
        *_text_list(express.get("limits")),
        *_text_list(express.get("counterexamples")),
        str(express.get("correction_response") or ""),
    ]
    return review_education_expression({"teaching_texts": texts})


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
