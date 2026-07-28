from __future__ import annotations

import json
import re
import sqlite3
from difflib import SequenceMatcher
from hashlib import sha256
from typing import Any

from .claim_evidence import build_claim_evidence_packet
from .conversation_spine import evaluate_candidate_compatibility
from .registry import truncate
from .supported_semantics import build_text_supported_semantic_packet


COMPREHENSION_BOUNDARY = (
    "guided_understanding_and_reviewed_knowledge_resources_only_"
    "not_identity_governance_personality_memory_or_model_training"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "identity_change": False,
    "governance_change": False,
    "personality_change": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "teaching_material_is_governance": False,
    "knowledge_retention_requires_review": True,
    "comprehension_before_fluency": True,
    "speed_is_success_measure": False,
}

APPROVED_STATE = "approved_knowledge_resource"
ACTIVE_CHAT_PERMISSION = "available_as_knowledge_resource"

DECISIONS: dict[str, tuple[str, str, str]] = {
    "approve_knowledge": (APPROVED_STATE, "approved_for_knowledge_use", ACTIVE_CHAT_PERMISSION),
    "needs_more_context": ("needs_context", "needs_more_context", "not_active_until_approved"),
    "hold_for_tending": ("held_for_tending", "held_for_tending", "not_active_until_approved"),
    "reopen_for_revision": ("reopened_for_revision", "needs_more_context", "not_active_until_reapproved"),
    "supersede": ("superseded", "superseded", "not_available"),
    "reject": ("rejected", "rejected", "not_available"),
}


def comprehension_status(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN state = 'approved_knowledge_resource'
                          AND review_status = 'approved_for_knowledge_use' THEN 1 ELSE 0 END) AS approved,
               SUM(CASE WHEN state IN ('proposed_understanding', 'needs_context', 'held_for_tending', 'reopened_for_revision')
                          THEN 1 ELSE 0 END) AS tending,
               SUM(CASE WHEN state = 'reopened_for_revision' THEN 1 ELSE 0 END) AS reopened
        FROM selene_comprehension_concepts
        """
    ).fetchone()
    run_count = int(conn.execute("SELECT COUNT(*) FROM selene_comprehension_runs").fetchone()[0])
    latest = conn.execute(
        "SELECT * FROM selene_comprehension_runs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    eligible_teaching_packets = int(
        conn.execute(
            """
            SELECT COUNT(*) FROM b_teaching_packets
            WHERE review_status = 'review_only'
              AND status = 'teaching_packet_review_only'
            """
        ).fetchone()[0]
    )
    prepared_teaching_packets = int(
        conn.execute(
            "SELECT COUNT(*) FROM selene_comprehension_concepts WHERE concept_key LIKE 'teaching_packet_%'"
        ).fetchone()[0]
    )
    approved = int(row["approved"] or 0)
    return _with_guards(
        {
            "status": "comprehension_integration_ready",
            "version": "v1_guided_understanding",
            "organ_name": "Comprehension and Integration Organ",
            "method": "teach_reconstruct_discuss_apply_challenge_correct_generalize_express",
            "concept_count": int(row["total"] or 0),
            "approved_knowledge_count": approved,
            "tending_count": int(row["tending"] or 0),
            "reopened_count": int(row["reopened"] or 0),
            "eligible_teaching_packet_count": eligible_teaching_packets,
            "prepared_teaching_packet_count": prepared_teaching_packets,
            "run_count": run_count,
            "latest_run": _decode_run(latest) if latest else None,
            "chat_knowledge_available": approved > 0,
            "retention_rule": "A taught concept remains a candidate until understanding evidence and either a bounded Aleks curriculum authorization or an explicit Aleks exception decision are present.",
            "reopening_rule": "Fluent or familiar knowledge may be reopened when contradiction, correction, or anomaly appears.",
            "project_law": "Knowledge expands what Selene can understand and discuss; it does not redefine Selene.",
            "review_destination": "Cocoon Teaching / Lessons",
            "review_status": "status_only",
            "provenance_boundary": COMPREHENSION_BOUNDARY,
        }
    )


def list_comprehension_concepts(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    state = str(payload.get("state") or "").strip()
    limit = max(1, min(int(payload.get("limit") or 100), 500))
    if state:
        rows = conn.execute(
            "SELECT * FROM selene_comprehension_concepts WHERE state = ? ORDER BY updated_at DESC, id DESC LIMIT ?",
            (state, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM selene_comprehension_concepts ORDER BY updated_at DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return _with_guards(
        {
            "status": "comprehension_concepts_ready",
            "items": [_decode_concept(row) for row in rows],
            "review_destination": "Cocoon Teaching / Lessons",
            "review_status": "status_only",
            "provenance_boundary": COMPREHENSION_BOUNDARY,
        }
    )


def prepare_comprehension_candidates_from_teaching(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_authority_change(payload)
    packet_ids = _int_list(payload.get("packet_ids"))
    limit = max(1, min(int(payload.get("limit") or 100), 500))
    clauses = ["review_status = 'review_only'", "status = 'teaching_packet_review_only'"]
    params: list[Any] = []
    if packet_ids:
        clauses.append(f"id IN ({','.join('?' for _ in packet_ids)})")
        params.extend(packet_ids)
    params.append(limit)
    packets = conn.execute(
        f"SELECT * FROM b_teaching_packets WHERE {' AND '.join(clauses)} ORDER BY id ASC LIMIT ?",
        params,
    ).fetchall()
    created: list[dict[str, Any]] = []
    existing: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for raw_packet in packets:
        packet = dict(raw_packet)
        packet_id = int(packet["id"])
        material_ids = _int_list(_loads(packet.get("material_ids"), []))
        if not material_ids:
            skipped.append({"packet_id": packet_id, "reason": "packet_has_no_material_ids"})
            continue
        material_rows = conn.execute(
            f"SELECT * FROM b_reviewed_teaching_materials WHERE id IN ({','.join('?' for _ in material_ids)})",
            material_ids,
        ).fetchall()
        materials = [dict(row) for row in material_rows]
        accepted_materials = [
            item
            for item in materials
            if item.get("review_status") == "accepted_for_teaching"
            and item.get("status") == "teaching_material_reviewed_non_active"
        ]
        if len(accepted_materials) != len(material_ids):
            skipped.append(
                {
                    "packet_id": packet_id,
                    "reason": "source_material_missing_or_no_longer_accepted",
                    "material_count": len(material_ids),
                    "accepted_material_count": len(accepted_materials),
                }
            )
            continue
        lesson = _loads(packet.get("lesson_json"), {})
        examples = _text_list(lesson.get("positive_examples"))
        corrections = _text_list(lesson.get("correction_examples"))
        limits = _text_list(lesson.get("when_not_to_use"))
        principles = _text_list(lesson.get("principles"))
        relationships = _text_list(lesson.get("relationships"))
        claim = truncate(
            str(
                lesson.get("central_claim")
                or lesson.get("summary")
                or (principles[0] if principles else "")
                or (examples[0] if examples else "")
            ),
            4000,
        ).strip()
        if not claim:
            skipped.append({"packet_id": packet_id, "reason": "packet_has_no_bounded_teaching_claim"})
            continue
        provenance_refs = list(
            dict.fromkeys(
                [
                    *_json_list(packet.get("source_refs")),
                    *(ref for item in accepted_materials for ref in _json_list(item.get("source_refs"))),
                ]
            )
        )
        if not provenance_refs:
            skipped.append({"packet_id": packet_id, "reason": "packet_has_no_source_refs"})
            continue
        source_refs = [*provenance_refs[:99], f"b_teaching_packets:{packet_id}"]
        result = propose_comprehension_concept(
            conn,
            {
                "concept_key": f"teaching_packet_{packet_id}",
                "title": str(packet.get("title") or f"Teaching packet {packet_id}"),
                "domain": f"communication.{str(packet.get('speech_function') or 'mixed')}",
                "material": claim,
                "principles": principles,
                "relationships": relationships,
                "examples": examples,
                "counterexamples": corrections,
                "limits": limits,
                "source_refs": source_refs,
                "confidence": "developing",
                "teaching_source_type": "accepted_b_teaching_packet",
                "source_metadata": {
                    "teaching_packet_id": packet_id,
                    "material_ids": material_ids,
                    "speech_function": packet.get("speech_function"),
                    "packet_review_status": packet.get("review_status"),
                },
            },
        )
        summary = {
            "packet_id": packet_id,
            "concept_id": result["item"]["id"],
            "concept_key": result["item"]["concept_key"],
            "title": result["item"]["title"],
        }
        (created if result.get("created") else existing).append(summary)
    result = _with_guards(
        {
            "status": "teaching_packets_prepared_as_understanding_candidates",
            "eligible_packet_count": len(packets),
            "created_count": len(created),
            "existing_count": len(existing),
            "skipped_count": len(skipped),
            "created": created,
            "existing": existing,
            "skipped": skipped,
            "retention_state": "candidate_not_retained",
            "chat_use_permission": "not_active_until_understanding_evidence_and_authorized_retention",
            "review_destination": "Cocoon Teaching / Lessons",
            "review_status": "status_only",
            "provenance_boundary": COMPREHENSION_BOUNDARY,
        }
    )
    result["run_id"] = _store_run(conn, "prepare_teaching_candidates", title="Accepted teaching packet intake", result=result)
    return result


def propose_comprehension_concept(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_authority_change(payload)
    title = truncate(str(payload.get("title") or ""), 240).strip()
    material = truncate(str(payload.get("material") or payload.get("central_claim") or ""), 4000).strip()
    source_refs = _json_list(payload.get("source_refs"))
    if not title:
        raise ValueError("concept title is required")
    if not material:
        raise ValueError("teaching material or central claim is required")
    if not source_refs:
        raise ValueError("source_refs are required for a knowledge candidate")
    domain = truncate(str(payload.get("domain") or "general"), 120).strip() or "general"
    concept_key = str(payload.get("concept_key") or _concept_key(domain, title)).strip()
    existing = conn.execute(
        "SELECT * FROM selene_comprehension_concepts WHERE concept_key = ?",
        (concept_key,),
    ).fetchone()
    if existing:
        return _with_guards(
            {
                "status": "comprehension_concept_already_exists",
                "created": False,
                "item": _decode_concept(existing),
                "provenance_boundary": COMPREHENSION_BOUNDARY,
            }
        )
    principles = _text_list(payload.get("principles"))
    relationships = _text_list(payload.get("relationships"))
    examples = _text_list(payload.get("examples"))
    counterexamples = _text_list(payload.get("counterexamples"))
    limits = _text_list(payload.get("limits"))
    cursor = conn.execute(
        """
        INSERT INTO selene_comprehension_concepts
        (concept_key, title, domain, central_claim, principles_json, relationships_json,
         examples_json, counterexamples_json, limits_json, source_refs, provenance_boundary,
         confidence, retention_state, chat_use_permission, correction_path, state,
         review_status, payload_json, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'candidate_not_retained',
                'not_active_until_approved', ?, 'proposed_understanding', 'pending_cocoon_teaching_review', ?, CURRENT_TIMESTAMP)
        """,
        (
            concept_key,
            title,
            domain,
            material,
            json.dumps(principles, sort_keys=True),
            json.dumps(relationships, sort_keys=True),
            json.dumps(examples, sort_keys=True),
            json.dumps(counterexamples, sort_keys=True),
            json.dumps(limits, sort_keys=True),
            json.dumps(source_refs, sort_keys=True),
            COMPREHENSION_BOUNDARY,
            str(payload.get("confidence") or "developing"),
            truncate(str(payload.get("correction_path") or "Cocoon teaching review and source-linked revision"), 500),
            json.dumps(
                {
                    "teaching_source_type": str(payload.get("teaching_source_type") or "approved_or_user_supplied_teaching"),
                    "source_metadata": payload.get("source_metadata") if isinstance(payload.get("source_metadata"), dict) else {},
                    "understanding_evidence": {},
                    "knowledge_not_governance": True,
                    "identity_unchanged": True,
                    "speed_not_assessed": True,
                },
                sort_keys=True,
            ),
        ),
    )
    conn.commit()
    item = _concept_row(conn, int(cursor.lastrowid))
    return _with_guards(
        {
            "status": "comprehension_concept_proposed",
            "created": True,
            "item": item,
            "knowledge_write_active": False,
            "retention_state": "candidate_not_retained",
            "activation_rule": "not_available_to_chat_until_understanding_evidence_and_authorized_retention",
            "review_destination": "Cocoon Teaching / Lessons",
            "provenance_boundary": COMPREHENSION_BOUNDARY,
        }
    )


def evaluate_understanding(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    concept_id = int(payload.get("concept_id") or payload.get("id") or 0)
    concept = _concept_row(conn, concept_id)
    if not concept:
        raise ValueError("comprehension concept not found")
    teach_back = truncate(str(payload.get("teach_back") or ""), 3000).strip()
    application = truncate(str(payload.get("application") or ""), 3000).strip()
    limits = _text_list(payload.get("limits")) or _text_list(concept.get("limits"))
    counterexample = truncate(str(payload.get("counterexample") or ""), 1800).strip()
    correction = truncate(str(payload.get("correction_response") or ""), 1800).strip()
    source_alignment = payload.get("source_alignment") is True
    copy_ratio = SequenceMatcher(None, _normalize(concept["central_claim"]), _normalize(teach_back)).ratio() if teach_back else 1.0
    dimensions = {
        "reconstruction": {
            "present": len(teach_back) >= 30,
            "not_surface_copy": bool(teach_back) and copy_ratio < 0.9,
            "copy_ratio": round(copy_ratio, 3),
        },
        "application": {
            "present": len(application) >= 25,
            "distinct_from_teach_back": bool(application) and _normalize(application) != _normalize(teach_back),
        },
        "limits": {"present": bool(limits), "items": limits[:8]},
        "counterexample": {"present": bool(counterexample), "value": counterexample},
        "correction_readiness": {
            "present": bool(correction) or payload.get("correction_ready") is True,
            "value": correction,
        },
        "source_alignment": {
            "confirmed_for_review": source_alignment,
            "source_refs_present": bool(concept.get("source_refs")),
        },
    }
    core_passes = [
        dimensions["reconstruction"]["present"] and dimensions["reconstruction"]["not_surface_copy"],
        dimensions["application"]["present"] and dimensions["application"]["distinct_from_teach_back"],
        dimensions["limits"]["present"],
        dimensions["source_alignment"]["confirmed_for_review"] and dimensions["source_alignment"]["source_refs_present"],
    ]
    sufficient = all(core_passes)
    result = _with_guards(
        {
            "status": "understanding_evidence_ready_for_review" if sufficient else "understanding_evidence_needs_more_work",
            "concept_id": concept_id,
            "concept_key": concept["concept_key"],
            "title": concept["title"],
            "understanding_evidence_sufficient": sufficient,
            "dimensions": dimensions,
            "passed_core_dimension_count": sum(1 for item in core_passes if item),
            "required_core_dimension_count": len(core_passes),
            "assessment_boundary": "Visible evidence of reconstruction and transfer, not proof of internal experience or perfect mastery.",
            "speed_assessed": False,
            "speed_relevant_to_decision": False,
            "recommended_next_step": "Check bounded curriculum coverage or request Aleks exception review." if sufficient else "Continue teaching, discussion, application, or clarification.",
            "source_refs": concept["source_refs"],
            "review_destination": "Cocoon Teaching / Lessons",
            "review_status": "status_only",
            "provenance_boundary": COMPREHENSION_BOUNDARY,
        }
    )
    run_id = _store_run(conn, "understanding_evaluation", title=concept["title"], concept_id=concept_id, result=result)
    result["run_id"] = run_id
    concept_payload = dict(concept.get("payload") or {})
    concept_payload["understanding_evidence"] = {
        "run_id": run_id,
        "status": result["status"],
        "sufficient": sufficient,
        "passed_core_dimension_count": result["passed_core_dimension_count"],
    }
    conn.execute(
        "UPDATE selene_comprehension_concepts SET payload_json = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(concept_payload, sort_keys=True), concept_id),
    )
    conn.commit()
    return result


def decide_comprehension_concept(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_authority_change(payload)
    concept_id = int(payload.get("concept_id") or payload.get("id") or 0)
    action = str(payload.get("action") or "").strip()
    if action not in DECISIONS:
        raise ValueError(f"unsupported comprehension decision: {action}")
    concept = _concept_row(conn, concept_id)
    if not concept:
        raise ValueError("comprehension concept not found")
    if action == "approve_knowledge":
        latest = conn.execute(
            """
            SELECT result_json FROM selene_comprehension_runs
            WHERE concept_id = ? AND operation = 'understanding_evaluation'
            ORDER BY id DESC LIMIT 1
            """,
            (concept_id,),
        ).fetchone()
        evidence = _loads(latest["result_json"] if latest else "", {})
        if evidence.get("understanding_evidence_sufficient") is not True:
            raise ValueError("knowledge approval requires source-linked understanding evidence first")
    state, review_status, chat_permission = DECISIONS[action]
    retention_state = "retained_reviewed_knowledge" if state == APPROVED_STATE else "candidate_not_retained"
    if state in {"superseded", "rejected"}:
        retention_state = "inactive_knowledge_record"
    conn.execute(
        """
        UPDATE selene_comprehension_concepts
        SET state = ?, review_status = ?, chat_use_permission = ?, retention_state = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (state, review_status, chat_permission, retention_state, concept_id),
    )
    conn.commit()
    return _with_guards(
        {
            "status": "comprehension_concept_decided",
            "action": action,
            "item": _concept_row(conn, concept_id),
            "knowledge_resource_active": state == APPROVED_STATE,
            "memory_write_active": False,
            "identity_changed": False,
            "governance_changed": False,
            "review_destination": "Cocoon Teaching / Lessons",
            "provenance_boundary": COMPREHENSION_BOUNDARY,
        }
    )


def build_comprehension_packet(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400).strip()
    if not prompt:
        raise ValueError("prompt is required")
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    conversation_spine = payload.get("conversation_spine") if isinstance(payload.get("conversation_spine"), dict) else {}
    dialogue = payload.get("dialogue_workspace") if isinstance(payload.get("dialogue_workspace"), dict) else {}
    pragmatics = dialogue.get("pragmatics") if isinstance(dialogue.get("pragmatics"), dict) else {}
    epistemic_revision = (
        payload.get("epistemic_revision_plan")
        if isinstance(payload.get("epistemic_revision_plan"), dict)
        else pragmatics.get("epistemic_update_plan")
        if isinstance(pragmatics.get("epistemic_update_plan"), dict)
        else {}
    )
    intelligence = payload.get("intelligence_support") if isinstance(payload.get("intelligence_support"), dict) else {}
    content_seed = truncate(str(payload.get("content_seed") or ""), 1800).strip()
    knowledge = retrieve_approved_knowledge(
        conn,
        prompt,
        limit=int(payload.get("knowledge_limit") or 3),
        include_language_guidance=False,
    )
    answer_eligible_items = _answer_eligible_knowledge_items(
        prompt,
        intent,
        knowledge.get("items") or [],
        conversation_spine=conversation_spine,
    )
    knowledge["answer_eligible_items"] = answer_eligible_items
    knowledge["answer_eligible"] = bool(answer_eligible_items)
    knowledge["conversation_spine_candidate_gate_applied"] = bool(conversation_spine)
    knowledge["answer_use_rule"] = (
        "Only strongly relevant, approved knowledge resources may seed an answer; "
        "language lessons remain NLO guidance and never become answer content."
    )
    ambiguity = pragmatics.get("ambiguity") if isinstance(pragmatics.get("ambiguity"), dict) else {}
    resolved_reference = pragmatics.get("resolved_reference") if isinstance(pragmatics.get("resolved_reference"), dict) else {}
    contradiction_markers = _matched_markers(
        prompt,
        ("doesn't look right", "does not look right", "that seems wrong", "contradiction", "contradicts", "recheck", "wait,", "not quite"),
    )
    challenge = intelligence.get("challenge") if isinstance(intelligence.get("challenge"), dict) else {}
    challenge_flags = _text_list(challenge.get("flags") or challenge.get("issues"))
    material_ambiguity = str(ambiguity.get("level") or "") == "material"
    supported = bool(content_seed or answer_eligible_items)
    epistemic_handoff = (
        epistemic_revision.get("metacognitive_handoff")
        if isinstance(epistemic_revision.get("metacognitive_handoff"), dict)
        else {}
    )
    epistemic_reopen = (
        epistemic_revision.get("detected") is True
        and epistemic_handoff.get("reopen_requested") is True
    )
    if contradiction_markers or challenge_flags or epistemic_reopen:
        understanding_state = "reopened_for_recheck"
    elif material_ambiguity and not supported:
        understanding_state = "needs_shared_model_check"
    elif answer_eligible_items:
        understanding_state = "approved_concept_available"
    elif content_seed:
        understanding_state = "current_context_supported"
    else:
        understanding_state = "not_yet_grounded"
    handshake_required = material_ambiguity and not supported
    best_interpretation = truncate(
        str(
            resolved_reference.get("resolved_to")
            or dialogue.get("active_topic")
            or intent.get("answer_shape")
            or intent.get("intent")
            or ""
        ),
        500,
    )
    handshake = {
        "required": handshake_required,
        "status": "ask_one_material_question" if handshake_required else "shared_model_sufficient_for_current_turn",
        "best_interpretation": best_interpretation,
        "reason": str(ambiguity.get("reason") or "current wording and session context are sufficient"),
        "question": "I have more than one possible meaning for that. Which part do you mean?" if handshake_required else "",
        "trusts_speaker_intelligence": True,
        "does_not_interrogate_every_turn": True,
    }
    response_obligations = [
        item for item in conversation_spine.get("open_obligations") or [] if isinstance(item, dict)
    ] or [item for item in pragmatics.get("response_obligations") or [] if isinstance(item, dict)]
    knowledge_response = _knowledge_response_seed(
        prompt,
        answer_eligible_items,
        response_obligations=response_obligations,
    )
    supported_semantics = build_text_supported_semantic_packet(
        str(knowledge_response.get("content_seed") or ""),
        answer_kind=str(knowledge_response.get("answer_kind") or "approved_knowledge"),
        source_kind="approved_knowledge",
        source_refs=_text_list(knowledge_response.get("source_refs"))[:30],
        certainty=(
            str(answer_eligible_items[0].get("confidence") or "reviewed")
            if answer_eligible_items
            else "not_available"
        ),
        scope="current_question_and_approved_knowledge_limits",
    )
    knowledge_claims = [
        {
            "claim_id": f"approved-knowledge-{item.get('id') or item.get('concept_id')}",
            "claim_type": "conclusion",
            "text": str(item.get("central_claim") or ""),
            "source_refs": item.get("source_refs") or [],
            "evidence_refs": item.get("source_refs") or [],
            "scope": "; ".join(str(value) for value in item.get("limits") or []),
            "confidence": str(item.get("confidence") or "reviewed"),
            "validity": "approved_knowledge_resource",
            "limitations": item.get("limits") or [],
            "what_would_change": [
                "Contradictory attributed evidence or a reviewed correction reopens this knowledge resource."
            ],
            "source_category": str(item.get("domain") or "approved_knowledge"),
        }
        for item in answer_eligible_items
        if str(item.get("central_claim") or "").strip()
    ]
    claim_evidence = build_claim_evidence_packet(
        {
            "claims": knowledge_claims,
            "accepted_source_refs": [
                ref for item in answer_eligible_items for ref in item.get("source_refs") or []
            ],
            "epistemic_revision": epistemic_revision,
        }
    )
    structural_discovery_knowledge_handoff = {
        "status": (
            "approved_knowledge_links_available"
            if answer_eligible_items
            else "no_relevant_approved_knowledge_links"
        ),
        "items": [
            {
                "concept_id": str(item.get("id") or item.get("concept_id") or ""),
                "domain": str(item.get("domain") or ""),
                "central_claim": str(item.get("central_claim") or ""),
                "relationships": item.get("relationships") or [],
                "limits": item.get("limits") or [],
                "source_refs": item.get("source_refs") or [],
                "approved": True,
                "personal_memory": False,
            }
            for item in answer_eligible_items
            if str(item.get("central_claim") or "").strip()
            and bool(item.get("source_refs"))
        ],
        "knowledge_owner": "Comprehension and Integration Organ",
        "personal_memory_used": False,
        "automatic_discovery_claim": False,
        "writes_records": False,
    }
    result = _with_guards(
        {
            "status": "comprehension_packet_ready",
            "version": "v1_guided_understanding",
            "organ_name": "Comprehension and Integration Organ",
            "understanding_state": understanding_state,
            "present_in_conversation": True,
            "literal_request": prompt,
            "communicative_intent": str(intent.get("intent") or "direct_conversation"),
            "answer_shape": str(intent.get("answer_shape") or "direct_answer"),
            "active_topic": str(dialogue.get("active_topic") or ""),
            "resolved_reference": resolved_reference or None,
            "response_obligations": response_obligations,
            "conversation_spine_turn_id": str(conversation_spine.get("turn_id") or ""),
            "conversation_spine_used": bool(conversation_spine),
            "knowledge_context": knowledge,
            "knowledge_response_seed": knowledge_response["content_seed"],
            "knowledge_response_basis": knowledge_response,
            "supported_semantics": supported_semantics,
            "claim_evidence_packet": claim_evidence,
            "structural_discovery_knowledge_handoff": structural_discovery_knowledge_handoff,
            "comprehension_handshake": handshake,
            "epistemic_revision": epistemic_revision,
            "metacognitive_check": {
                "reopen_suggested": bool(contradiction_markers or challenge_flags or epistemic_reopen),
                "contradiction_markers": contradiction_markers,
                "reasoning_challenge_flags": challenge_flags,
                "epistemic_update_kind": str(epistemic_revision.get("update_kind") or "none"),
                "unresolved_epistemic_contradictions": (
                    epistemic_revision.get("unresolved_contradictions") or []
                ),
                "selective_revision_preserves_unaffected_structure": (
                    epistemic_revision.get("detected") is True
                ),
                "assumptions_visible": [
                    "The current wording is interpreted through this session only.",
                    "Available knowledge resources may inform the answer but do not govern identity or law.",
                ],
                "correction_allowed": True,
                "not_knowing_allowed": True,
            },
            "retention": {
                "knowledge_write_active": False,
                "retention_candidate_created": False,
                "retention_requires_understanding_evidence": True,
                "retention_requires_aleks_review": True,
            },
            "learning_posture": {
                "understanding_before_fluency": True,
                "speed_is_not_the_goal": True,
                "fluency_may_emerge_from_integration": True,
                "familiar_knowledge_remains_reopenable": True,
            },
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "source_refs": list(dict.fromkeys([*_json_list(payload.get("source_refs")), *knowledge["source_refs"]]))[:50],
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": COMPREHENSION_BOUNDARY,
        }
    )
    if payload.get("record_run") is True:
        result["run_id"] = _store_run(conn, "turn_comprehension", title=truncate(prompt, 180), result=result)
    return result


def retrieve_approved_knowledge(
    conn: sqlite3.Connection,
    query: str,
    *,
    limit: int = 3,
    include_language_guidance: bool = True,
) -> dict[str, Any]:
    query_terms = set(_terms(query))
    rows = conn.execute(
        """
        SELECT * FROM selene_comprehension_concepts
        WHERE state = 'approved_knowledge_resource'
          AND review_status = 'approved_for_knowledge_use'
          AND chat_use_permission = 'available_as_knowledge_resource'
        ORDER BY updated_at DESC, id DESC
        """
    ).fetchall()
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for row in rows:
        item = _decode_concept(row)
        guidance_only = _is_language_guidance_concept(item)
        if guidance_only and not include_language_guidance:
            continue
        haystack = " ".join(
            [
                item["title"],
                item["domain"],
                item["central_claim"],
                *item["principles"],
                *item["relationships"],
            ]
        )
        overlap = query_terms & set(_terms(haystack))
        if overlap:
            item["matched_terms"] = sorted(overlap)
            item["guidance_only"] = guidance_only
            ranked.append((len(overlap), int(item["id"]), item))
    items = [item for _, _, item in sorted(ranked, key=lambda value: (-value[0], -value[1]))[: max(1, min(limit, 10))]]
    return {
        "available": bool(items),
        "source_class": "reviewed_teaching_knowledge_resource" if items else "none",
        "items": [
            {
                "id": item["id"],
                "concept_key": item["concept_key"],
                "title": item["title"],
                "domain": item["domain"],
                "central_claim": item["central_claim"],
                "principles": item["principles"][:6],
                "relationships": item["relationships"][:6],
                "examples": item["examples"][:6],
                "counterexamples": item["counterexamples"][:6],
                "limits": item["limits"][:6],
                "confidence": item["confidence"],
                "source_refs": item["source_refs"],
                "matched_terms": item.get("matched_terms") or [],
                "guidance_only": item.get("guidance_only") is True,
            }
            for item in items
        ],
        "source_refs": list(dict.fromkeys(ref for item in items for ref in item["source_refs"]))[:40],
        "memory_source": False,
        "governance_source": False,
        "identity_source": False,
    }


def _answer_eligible_knowledge_items(
    prompt: str,
    intent: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    conversation_spine: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    contextual = intent.get("contextual_follow_up") if isinstance(intent.get("contextual_follow_up"), dict) else {}
    dialogue_acts = {str(item) for item in intent.get("dialogue_acts") or []}
    intent_name = str(intent.get("intent") or "")
    answer_requested = bool(
        intent_name == "reasoning"
        or intent.get("reasoning_requested") is True
        or (
            intent_name in {"direct_conversation", "direct_answer", ""}
            and dialogue_acts.intersection({"question", "request"})
        )
    )
    if not answer_requested:
        return []
    # Response-shape wording is not part of the subject being asked about.
    # Keeping it out of the query prevents phrases such as "in one sentence"
    # from making an unrelated lesson about sentences look relevant.
    subject_query = re.sub(
        r"\b(?:in|using)\s+(?:one|two|three|four|five|\d+)\s+"
        r"(?:short\s+|brief\s+)?(?:parts?|points?|sentences?|paragraphs?|steps?)\b",
        " ",
        prompt,
        flags=re.IGNORECASE,
    )
    query_terms = set(_terms(subject_query))
    generic = {
        "answer", "another", "apply", "back", "but", "cannot", "change", "changed", "check",
        "compare", "conversation", "different", "do", "example", "explain", "first", "give",
        "handle", "help", "idea", "language", "lesson", "lessons", "make", "material", "most",
        "new", "next", "one", "ordinary", "practical", "question", "reason", "return", "review",
        "reviewed", "say", "should", "short", "step", "thing", "things", "use", "version", "why",
    }
    eligible: list[dict[str, Any]] = []
    for item in items:
        item_text = " ".join(
            [
                str(item.get("title") or ""),
                str(item.get("central_claim") or ""),
                *[str(value) for value in item.get("principles") or []],
                *[str(value) for value in item.get("relationships") or []],
            ]
        )
        compatibility = evaluate_candidate_compatibility(
            conversation_spine,
            {
                "source_id": "approved_comprehension",
                "source_class": "approved_knowledge",
                "text": item_text,
            },
        )
        item["conversation_spine_compatibility"] = compatibility
        if compatibility.get("compatible") is not True:
            continue
        if contextual.get("detected") is True:
            # The spine keeps an immediate callback grounded in the answer it
            # refers to even if an approved lesson shares a few words.
            continue
        if item.get("guidance_only") is True or _is_language_guidance_concept(item):
            continue
        overlap = set(item.get("matched_terms") or []) & query_terms
        distinctive_overlap = {term for term in overlap if term not in generic}
        title_terms = set(
            _terms(
                " ".join(
                    [
                        str(item.get("title") or ""),
                        str(item.get("domain") or ""),
                        str(item.get("concept_key") or "").replace("_", " "),
                    ]
                )
            )
        ) - generic
        subject_overlap = distinctive_overlap & title_terms
        # Approved knowledge may answer only when the prompt names the
        # concept's subject. Peripheral overlap in claims or examples is not
        # enough to redirect an otherwise ordinary question.
        if not subject_overlap:
            continue
        item["answer_alignment_terms"] = sorted(distinctive_overlap)
        item["answer_subject_terms"] = sorted(subject_overlap)
        eligible.append(item)
    return eligible


def _knowledge_response_seed(
    prompt: str,
    items: list[dict[str, Any]],
    *,
    response_obligations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if not items:
        return {
            "content_seed": "",
            "answer_kind": "none",
            "why_relationship_included": False,
            "limit_included": False,
        }
    obligations = [item for item in response_obligations or [] if isinstance(item, dict)]
    if obligations:
        fragments: list[str] = []
        support: list[dict[str, Any]] = []
        for obligation in obligations[:12]:
            selected = _best_knowledge_item_for_text(str(obligation.get("source_text") or prompt), items)
            if not selected:
                continue
            fragment, field = _knowledge_fragment_for_obligation(obligation, selected)
            if not fragment:
                continue
            key = fragment.lower().rstrip(". ")
            if fragment and key not in {value.lower().rstrip(". ") for value in fragments}:
                fragments.append(fragment)
            support.append(
                {
                    "obligation_id": str(obligation.get("id") or ""),
                    "kind": str(obligation.get("kind") or "direct_question"),
                    "concept_id": selected.get("id") or selected.get("concept_id"),
                    "concept_key": selected.get("concept_key"),
                    "support_field": field,
                    "source_refs": _text_list(selected.get("source_refs"))[:20],
                }
            )
        if fragments:
            return {
                "content_seed": truncate(" ".join(fragments), 3000),
                "answer_kind": "multi_obligation_knowledge_synthesis" if len(support) > 1 else "obligation_bound_knowledge",
                "why_relationship_included": any(item.get("support_field") in {"principle", "relationship"} for item in support),
                "limit_included": any(item.get("support_field") in {"limit", "counterexample"} for item in support),
                "obligation_support": support,
                "concept_ids": list(dict.fromkeys(item.get("concept_id") for item in support if item.get("concept_id"))),
                "source_refs": list(dict.fromkeys(ref for item in support for ref in item.get("source_refs") or []))[:30],
            }
    item = items[0]
    central = truncate(str(item.get("central_claim") or "").strip(), 1400)
    lower = prompt.lower()
    asks_why = bool(re.search(r"\bwhy\b|\breason\b|\bcause\b|\bmechanism\b", lower))
    asks_limit = bool(re.search(r"\bwhen\b|\blimit\b|\bexception\b|\bnot apply\b|\bfail\b", lower))
    explanatory = [
        truncate(str(value).strip(), 700)
        for value in [*list(item.get("principles") or []), *list(item.get("relationships") or [])]
        if str(value).strip() and str(value).strip().lower() not in central.lower()
    ]
    limits = [
        truncate(str(value).strip(), 700)
        for value in item.get("limits") or []
        if str(value).strip() and str(value).strip().lower() not in central.lower()
    ]
    parts = [central] if central else []
    why_included = asks_why and bool(explanatory)
    limit_included = asks_limit and bool(limits)
    if why_included:
        parts.append(explanatory[0])
    if limit_included:
        parts.append(limits[0])
    return {
        "content_seed": truncate(" ".join(parts), 1800),
        "answer_kind": "why_supported" if why_included else "limit_supported" if limit_included else "central_claim",
        "why_relationship_included": why_included,
        "limit_included": limit_included,
        "concept_id": item.get("id") or item.get("concept_id"),
        "source_refs": _text_list(item.get("source_refs"))[:20],
    }


def _best_knowledge_item_for_text(text: str, items: list[dict[str, Any]]) -> dict[str, Any] | None:
    terms = set(_terms(text))
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(items):
        haystack = " ".join(
            [
                str(item.get("title") or ""),
                str(item.get("central_claim") or ""),
                *[str(value) for value in item.get("principles") or []],
                *[str(value) for value in item.get("relationships") or []],
                *[str(value) for value in item.get("examples") or []],
                *[str(value) for value in item.get("counterexamples") or []],
                *[str(value) for value in item.get("limits") or []],
            ]
        )
        overlap = terms & set(_terms(haystack))
        anchored = terms & set(item.get("answer_alignment_terms") or [])
        subject = terms & set(item.get("answer_subject_terms") or [])
        if not anchored and not subject:
            continue
        score = len(overlap) + (2 * len(anchored)) + (3 * len(subject))
        ranked.append((score, -index, item))
    ranked.sort(key=lambda value: (value[0], value[1]), reverse=True)
    return ranked[0][2] if ranked else None


def _knowledge_fragment_for_obligation(
    obligation: dict[str, Any],
    item: dict[str, Any],
) -> tuple[str, str]:
    kind = str(obligation.get("kind") or "direct_question")
    source = str(obligation.get("source_text") or "").lower()
    if kind == "analogy" or "analogy" in source or "example" in source:
        values = item.get("examples") or []
        return (truncate(str(values[0]), 800), "example") if values else ("", "unsupported")
    if kind == "limitation" or any(marker in source for marker in ("limit", "exception", "not apply", "counterexample")):
        values = item.get("counterexamples") or item.get("limits") or []
        field = "counterexample" if item.get("counterexamples") else "limit"
        return (truncate(str(values[0]), 800), field) if values else ("", "unsupported")
    if kind == "reason" or any(marker in source for marker in ("why", "reason", "mechanism", "cause")):
        values = [*list(item.get("principles") or []), *list(item.get("relationships") or [])]
        return (truncate(str(values[0]), 800), "principle") if values else ("", "unsupported")
    central = truncate(str(item.get("central_claim") or ""), 1200)
    return central, "central_claim"


def _is_language_guidance_concept(item: dict[str, Any]) -> bool:
    return (
        str(item.get("domain") or "") == "language_and_conversation"
        or str(item.get("concept_key") or "").startswith("language_lesson:")
    )


def _store_run(
    conn: sqlite3.Connection,
    operation: str,
    *,
    title: str,
    result: dict[str, Any],
    concept_id: int | None = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO selene_comprehension_runs
        (operation, concept_id, title, status, understanding_state, result_json,
         source_refs, provenance_boundary, review_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'status_only')
        """,
        (
            operation,
            concept_id,
            title,
            str(result.get("status") or "comprehension_status_only"),
            str(result.get("understanding_state") or result.get("status") or "open"),
            json.dumps(result, sort_keys=True),
            json.dumps(_json_list(result.get("source_refs")), sort_keys=True),
            COMPREHENSION_BOUNDARY,
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def _decode_concept(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    for key in ("principles_json", "relationships_json", "examples_json", "counterexamples_json", "limits_json"):
        item[key.removesuffix("_json")] = _loads(item.pop(key, "[]"), [])
    item["source_refs"] = _loads(item.get("source_refs"), [])
    item["payload"] = _loads(item.pop("payload_json", "{}"), {})
    return item


def _decode_run(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["result"] = _loads(item.pop("result_json", "{}"), {})
    item["source_refs"] = _loads(item.get("source_refs"), [])
    return item


def _concept_row(conn: sqlite3.Connection, concept_id: int) -> dict[str, Any] | None:
    if concept_id <= 0:
        return None
    row = conn.execute("SELECT * FROM selene_comprehension_concepts WHERE id = ?", (concept_id,)).fetchone()
    return _decode_concept(row) if row else None


def _concept_key(domain: str, title: str) -> str:
    digest = sha256(f"{_normalize(domain)}:{_normalize(title)}".encode("utf-8")).hexdigest()[:16]
    return f"concept_{digest}"


def _terms(value: str) -> list[str]:
    stop = {
        "about", "after", "again", "also", "and", "are", "because", "before", "being", "can", "could",
        "been", "does", "doing", "for", "from", "has", "have", "how", "into", "its", "just", "mean", "means", "more", "not", "part", "parts", "short", "that", "the", "their",
        "them", "then", "there", "this", "too", "two", "what", "whats", "when", "where", "which", "with", "would", "you", "your",
    }
    return list(
        dict.fromkeys(
            word.lower()
            for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", value)
            if word.lower() not in stop
        )
    )[:120]


def _matched_markers(value: str, markers: tuple[str, ...]) -> list[str]:
    lower = " ".join(value.lower().split())
    return [marker for marker in markers if marker in lower]


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value).lower()))


def _text_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [truncate(str(item), 1000).strip() for item in value if str(item).strip()][:30]
    if isinstance(value, tuple):
        return [truncate(str(item), 1000).strip() for item in value if str(item).strip()][:30]
    if isinstance(value, str) and value.strip():
        return [truncate(item.strip(), 1000) for item in re.split(r"\r?\n|\s*;\s*", value) if item.strip()][:30]
    return []


def _int_list(value: Any) -> list[int]:
    if isinstance(value, (list, tuple)):
        raw_items = value
    elif value in (None, ""):
        raw_items = []
    else:
        raw_items = [value]
    result: list[int] = []
    for item in raw_items:
        try:
            parsed = int(item)
        except (TypeError, ValueError):
            continue
        if parsed > 0 and parsed not in result:
            result.append(parsed)
    return result[:500]


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        loaded = _loads(value, None)
        if isinstance(loaded, list):
            return [str(item) for item in loaded if str(item).strip()]
        return [value]
    return []


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
        raise ValueError("comprehension teaching cannot change identity, governance, memory, activation, or authority")


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
