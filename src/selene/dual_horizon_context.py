from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .registry import truncate


DUAL_HORIZON_BOUNDARY = (
    "selective_active_and_approved_long_range_context_only_no_raw_corpus_"
    "durable_memory_write_identity_personality_governance_authority_or_autonomy_change"
)

CHECKPOINT_BOUNDARY = (
    "session_topic_checkpoint_only_visible_source_bound_context_not_durable_"
    "memory_hidden_reasoning_training_identity_governance_or_authority"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "raw_corpus_loaded": False,
    "retained_knowledge_write_active": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
}

_STOP = {
    "about", "after", "again", "also", "and", "are", "back", "because", "been",
    "before", "being", "can", "could", "does", "for", "from", "have", "hello",
    "hey", "how", "into", "just", "more", "that", "the", "then", "there", "these",
    "they", "this", "those", "what", "when", "where", "which", "with", "would",
    "your", "selene",
}


def build_session_topic_checkpoint(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one visible, session-only landing packet when the turn warrants it."""
    payload = payload or {}
    session_id = int(payload.get("session_id") or 0)
    candidate = truncate(str(payload.get("candidate_text") or ""), 5000).strip()
    dialogue = _dict(payload.get("dialogue_workspace"))
    pragmatics = _dict(dialogue.get("pragmatics"))
    spine = _dict(payload.get("conversation_spine"))
    coverage = _dict(payload.get("response_coverage"))
    answer_engine = _dict(payload.get("answer_engine_support"))
    answer_packet = _dict(answer_engine.get("answer_packet"))
    metacognition = _dict(payload.get("metacognition"))
    epistemic = _dict(
        payload.get("epistemic_revision")
        or spine.get("epistemic_revision")
        or pragmatics.get("epistemic_update_plan")
    )
    claim_evidence = _dict(payload.get("claim_evidence_packet"))
    structural = _dict(payload.get("structural_discovery"))
    prior = [
        item
        for item in payload.get("prior_checkpoints") or pragmatics.get(
            "topic_checkpoints"
        )
        or []
        if isinstance(item, dict)
    ][-16:]
    topic = truncate(
        str(dialogue.get("active_topic") or spine.get("active_topic") or ""),
        300,
    )
    thread_braid = _dict(pragmatics.get("thread_braid") or spine.get("thread_braid"))
    thread_id = str(
        thread_braid.get("active_thread_id") or spine.get("active_thread_id") or ""
    )
    obligation_ids = [
        str(item.get("id") or "")
        for item in spine.get("open_obligations") or []
        if isinstance(item, dict) and str(item.get("id") or "")
    ]
    sentences = _sentences(candidate)
    decisions = [
        item
        for item in sentences
        if re.search(
            r"\b(?:recommend|choose|prefer|should|next step|start with|decide)\b",
            item,
            flags=re.IGNORECASE,
        )
    ][:4]
    limits = [
        item
        for item in sentences
        if re.search(
            r"\b(?:limit|cannot|can't|does not|doesn't|only|unless|however|but)\b",
            item,
            flags=re.IGNORECASE,
        )
    ][:4]
    examples = [
        item
        for item in sentences
        if re.search(
            r"\b(?:for example|for instance|such as|analogy)\b",
            item,
            flags=re.IGNORECASE,
        )
    ][:4]
    last_action = str(
        next(
            (
                item.get("action")
                for item in reversed(thread_braid.get("turn_traversal") or [])
                if isinstance(item, dict)
            ),
            "",
        )
        or ""
    )
    revision_detected = epistemic.get("detected") is True
    complete_landing = (
        coverage.get("all_required_addressed") is True
        and bool(obligation_ids or decisions or limits)
    )
    explicit_landing = last_action in {"land", "revise_with_dependency"}
    meaningful_topic = bool(_terms(topic))
    eligible = bool(
        session_id > 0
        and candidate
        and meaningful_topic
        and (complete_landing or revision_detected or explicit_landing)
    )
    if not eligible:
        return {
            "status": "session_topic_checkpoint_not_created",
            "eligible": False,
            "reason": (
                "no_visible_candidate"
                if not candidate
                else "no_meaningful_topic"
                if not meaningful_topic
                else "turn_has_not_reached_a_checkpoint_landing"
            ),
            "session_only": True,
            "memory_proposal_created": False,
            "retention_eligible": False,
            "hidden_chain_of_thought_exposed": False,
            "provenance_boundary": CHECKPOINT_BOUNDARY,
            **GUARDS,
        }

    same_thread = [
        item
        for item in prior
        if str(item.get("thread_id") or "") == thread_id
        or (
            not thread_id
            and _meaningful_overlap(_terms(topic), _terms(str(item.get("topic") or "")))
        )
    ]
    parent = same_thread[-1] if same_thread else {}
    revision = int(parent.get("revision") or 0) + 1
    source_refs = list(
        dict.fromkeys(
            [
                *_text_list(payload.get("source_refs")),
                *_text_list(answer_packet.get("source_refs")),
                *_text_list(claim_evidence.get("source_refs")),
                f"selene_chat_session:{session_id}:visible_turn",
            ]
        )
    )[:40]
    corrections = [
        item
        for item in dialogue.get("corrections") or []
        if isinstance(item, dict)
    ][-4:]
    unresolved = [
        {
            "obligation_id": str(item.get("id") or ""),
            "question": truncate(str(item.get("source_text") or ""), 480),
            "kind": str(item.get("kind") or ""),
        }
        for item in spine.get("open_obligations") or []
        if isinstance(item, dict)
        and str(item.get("id") or "")
        not in {
            str(covered)
            for covered in coverage.get("domain_owned_obligation_ids") or []
        }
        and not next(
            (
                coverage_item.get("addressed") is True
                for coverage_item in coverage.get("items") or []
                if isinstance(coverage_item, dict)
                and str(coverage_item.get("obligation_id") or "")
                == str(item.get("id") or "")
            ),
            False,
        )
    ][:8]
    checkpoint_id = "topic-checkpoint-" + sha256(
        f"{session_id}|{thread_id}|{topic}|{revision}|{candidate}".encode("utf-8")
    ).hexdigest()[:16]
    direct_evidence_refs = list(
        dict.fromkeys(
            [
                *source_refs,
                *[
                    str(ref)
                    for claim in claim_evidence.get("claims") or []
                    if isinstance(claim, dict)
                    for ref in claim.get("evidence_refs") or []
                    if str(ref)
                ],
            ]
        )
    )[:40]
    exact_results = [
        str(item)
        for item in payload.get("exact_results")
        or (
            answer_engine.get("required_answer_fragments")
            if str(answer_packet.get("domain") or "") == "verified_math"
            else []
        )
        or []
        if str(item).strip()
    ][:8]
    checkpoint = {
        "status": "session_topic_checkpoint_ready",
        "version": "v1_session_topic_checkpoint",
        "checkpoint_id": checkpoint_id,
        "parent_checkpoint_id": str(parent.get("checkpoint_id") or ""),
        "revision": revision,
        "session_id": session_id,
        "topic": topic,
        "topic_keys": sorted(_terms(topic))[:20],
        "thread_id": thread_id,
        "branch_ids": [
            str(item.get("id") or "")
            for item in thread_braid.get("threads") or []
            if isinstance(item, dict) and str(item.get("id") or "")
        ][:16],
        "established_visible_statements": sentences[:8],
        "decisions_and_why": decisions,
        "examples_or_applications": examples,
        "known_limits": limits,
        "unresolved_questions": unresolved,
        "open_obligation_ids": [
            item["obligation_id"] for item in unresolved if item["obligation_id"]
        ],
        "corrections": corrections,
        "superseded_claims": [
            str(item)
            for item in (
                [epistemic.get("original_claim")]
                if epistemic.get("detected") is True
                and str(epistemic.get("original_claim") or "").strip()
                else []
            )
        ],
        "entities": [
            item for item in dialogue.get("entities") or [] if isinstance(item, dict)
        ][:16],
        "referents": (
            dialogue.get("referents")
            if isinstance(dialogue.get("referents"), dict)
            else {}
        ),
        "source_refs": source_refs,
        "reasoning_state_capsule": {
            "current_conclusion": sentences[0] if sentences else "",
            "direct_evidence_refs": direct_evidence_refs,
            "inference_labels": [
                str(item.get("claim_type") or "")
                for item in claim_evidence.get("claims") or []
                if isinstance(item, dict) and str(item.get("claim_type") or "")
            ][:12],
            "assumptions": _text_list(answer_packet.get("assumptions"))[:12],
            "competing_explanations_alive": [
                str(item.get("label") or item.get("summary") or "")
                for item in structural.get("candidate_relations") or []
                if isinstance(item, dict)
                and str(item.get("label") or item.get("summary") or "")
            ][:8],
            "unresolved_contradictions": _text_list(
                epistemic.get("unresolved_contradictions")
            )[:8],
            "confidence_vector": _dict(metacognition.get("confidence_vector")),
            "correction_ancestry": epistemic.get("model_ancestry") or {},
            "what_would_change_the_answer": _text_list(
                answer_packet.get("what_would_change_the_answer")
            )[:8],
            "stopping_reason": str(
                _dict(metacognition.get("stopping")).get("reason") or ""
            ),
            "exact_domain_results": exact_results,
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
        },
        "landing_basis": (
            "epistemic_revision"
            if revision_detected
            else "explicit_thread_landing"
            if explicit_landing
            else "current_obligations_completed"
        ),
        "scope": "current_session_only",
        "expiry": "expires_with_selene_chat_session_context",
        "session_only": True,
        "durable_memory": False,
        "memory_proposal_created": False,
        "retention_eligible": False,
        "automatic_memory_promotion": False,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": CHECKPOINT_BOUNDARY,
        **GUARDS,
    }
    return checkpoint


def merge_session_topic_checkpoints(
    existing: list[dict[str, Any]],
    checkpoint: dict[str, Any],
    *,
    limit: int = 64,
) -> list[dict[str, Any]]:
    bounded_limit = max(1, min(limit, 64))
    items = [item for item in existing if isinstance(item, dict)][-64:]
    if checkpoint.get("status") != "session_topic_checkpoint_ready":
        return _retain_checkpoint_threads(items, bounded_limit)
    checkpoint_id = str(checkpoint.get("checkpoint_id") or "")
    merged = [
        item
        for item in items
        if str(item.get("checkpoint_id") or "") != checkpoint_id
    ]
    merged.append(checkpoint)
    return _retain_checkpoint_threads(merged, bounded_limit)


def _retain_checkpoint_threads(
    items: list[dict[str, Any]], limit: int
) -> list[dict[str, Any]]:
    if len(items) <= limit:
        return items
    latest_by_thread: dict[str, int] = {}
    for index, item in enumerate(items):
        thread_id = str(item.get("thread_id") or "")
        if thread_id:
            latest_by_thread[thread_id] = index
    selected = set(latest_by_thread.values())
    for index in range(len(items) - 1, -1, -1):
        if len(selected) >= limit:
            break
        selected.add(index)
    if len(selected) > limit:
        protected = set(latest_by_thread.values())
        selected = set(sorted(protected, reverse=True)[:limit])
    return [item for index, item in enumerate(items) if index in selected]


def build_dual_horizon_context(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Select current-session and approved long-range context packets."""
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or ""), 3000)
    query_terms = _terms(prompt)
    dialogue = _dict(payload.get("dialogue_workspace"))
    pragmatics = _dict(dialogue.get("pragmatics"))
    spine = _dict(payload.get("conversation_spine"))
    memory = _dict(payload.get("memory_context"))
    comprehension = _dict(payload.get("comprehension_context"))
    knowledge = _dict(comprehension.get("knowledge_context"))
    source_packets = [
        item
        for item in payload.get("source_packets") or []
        if isinstance(item, dict)
    ][:16]
    max_active = max(1, min(int(payload.get("max_active_items") or 8), 16))
    max_approved = max(1, min(int(payload.get("max_approved_items") or 6), 12))
    active_items = _active_horizon_items(
        prompt,
        dialogue=dialogue,
        pragmatics=pragmatics,
        spine=spine,
    )
    approved_items = _approved_horizon_items(
        prompt,
        memory=memory,
        knowledge=knowledge,
        checkpoints=[
            item
            for item in pragmatics.get("topic_checkpoints") or []
            if isinstance(item, dict)
        ],
        source_packets=source_packets,
        epistemic=_dict(spine.get("epistemic_revision")),
        active_thread_id=str(
            _dict(pragmatics.get("thread_braid")).get("active_thread_id") or ""
        ),
    )
    selected_active = _select_items(
        active_items,
        query_terms=query_terms,
        limit=max_active,
        keep_current=True,
    )
    selected_approved = _select_items(
        approved_items,
        query_terms=query_terms,
        limit=max_approved,
        keep_current=False,
    )
    active_refs = [
        str(item.get("context_id") or "") for item in selected_active
    ]
    approved_refs = [
        str(item.get("context_id") or "") for item in selected_approved
    ]
    grounding_text = _grounding_text(selected_active, selected_approved)
    return {
        "status": "dual_horizon_context_ready",
        "version": "v1_dual_horizon_context",
        "is_organ": False,
        "selection_layer_only": True,
        "active_horizon": {
            "scope": "current_session_only",
            "selected_items": selected_active,
            "selected_count": len(selected_active),
            "candidate_count": len(active_items),
            "maximum": max_active,
            "selected_context_ids": active_refs,
        },
        "approved_long_range_horizon": {
            "scope": (
                "retrieval_selected_approved_memory_approved_knowledge_current_"
                "attributed_sources_and_session_checkpoint_bridge"
            ),
            "selected_items": selected_approved,
            "selected_count": len(selected_approved),
            "candidate_count": len(approved_items),
            "maximum": max_approved,
            "selected_context_ids": approved_refs,
        },
        "shared_selection_fields": [
            "topic_keys",
            "entity_keys",
            "semantic_cue_keys",
            "relationship_type",
            "time_relevance",
            "source_class",
            "certainty",
            "approval_or_retention_state",
            "contradiction_status",
            "retrieval_reason",
        ],
        "grounding_text": grounding_text,
        "grounding_uses_selected_packets_only": True,
        "ineligible_source_classes": [
            "raw_corpus_messages",
            "review_only_teaching_material",
            "unapproved_memory_proposals",
            "superseded_memory",
            "b_only_support_records",
            "hidden_reasoning_or_scratch_work",
        ],
        "raw_items_loaded": 0,
        "review_only_items_loaded": 0,
        "unapproved_memory_items_loaded": 0,
        "topic_checkpoint_count_available": len(
            pragmatics.get("topic_checkpoints") or []
        ),
        "memory_context_used": memory.get("memory_context_used") is True,
        "approved_knowledge_context_used": bool(
            knowledge.get("answer_eligible_items")
        ),
        "current_attributed_sources_used": bool(
            [
                item
                for item in selected_approved
                if item.get("source_class") == "current_attributed_source"
            ]
        ),
        "memory_ownership_unchanged": True,
        "checkpoint_is_memory": False,
        "great_library_remains_external": True,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": DUAL_HORIZON_BOUNDARY,
        **GUARDS,
    }


def attach_dual_horizon_to_spine(
    spine: dict[str, Any],
    dual_horizon: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(spine, dict)
        or dual_horizon.get("status") != "dual_horizon_context_ready"
    ):
        return spine
    interpreted = truncate(
        str(spine.get("interpreted_prompt") or spine.get("literal_prompt") or ""),
        2400,
    )
    grounding = truncate(str(dual_horizon.get("grounding_text") or ""), 1200)
    grounded_prompt = (
        truncate(f"{interpreted} {grounding}", 3600)
        if grounding
        else interpreted
    )
    return {
        **spine,
        "version": "v3_dual_horizon_grounding",
        "grounded_prompt": grounded_prompt,
        "grounded_prompt_source": "dual_horizon_selected_context_packets",
        "dual_horizon_context": dual_horizon,
        "active_horizon_context_ids": (
            dual_horizon.get("active_horizon") or {}
        ).get("selected_context_ids")
        or [],
        "approved_horizon_context_ids": (
            dual_horizon.get("approved_long_range_horizon") or {}
        ).get("selected_context_ids")
        or [],
        "raw_context_concatenation_used": False,
        "raw_corpus_loaded": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
    }


def _active_horizon_items(
    prompt: str,
    *,
    dialogue: dict[str, Any],
    pragmatics: dict[str, Any],
    spine: dict[str, Any],
) -> list[dict[str, Any]]:
    active_topic = str(dialogue.get("active_topic") or "")
    entity_keys = [
        str(item.get("name") or "")
        for item in dialogue.get("entities") or []
        if isinstance(item, dict) and str(item.get("name") or "")
    ][:20]
    items: list[dict[str, Any]] = [
        _context_item(
            "active-current-utterance",
            summary=prompt,
            source_class="current_utterance",
            scope="current_turn",
            topic=active_topic,
            relationship_type="current_input",
            time_relevance="now",
            approval_state="current_session_input",
            certainty="speaker_supplied",
            retrieval_reason="always_current",
            entity_keys=entity_keys,
            current=True,
        )
    ]
    for unit in pragmatics.get("utterance_units") or []:
        if not isinstance(unit, dict) or not str(unit.get("text") or "").strip():
            continue
        items.append(
            _context_item(
                f"active-{unit.get('id') or 'utterance-unit'}",
                summary=str(unit.get("text") or ""),
                source_class="current_utterance_unit",
                scope="current_turn",
                topic=active_topic,
                relationship_type=f"current_{unit.get('kind') or 'utterance'}",
                time_relevance="now",
                approval_state="current_session_input",
                certainty="speaker_supplied",
                retrieval_reason="current_utterance_structure",
                entity_keys=entity_keys,
                current=True,
            )
        )
    if active_topic:
        items.append(
            _context_item(
                "active-topic",
                summary=active_topic,
                source_class="dialogue_workspace",
                scope="current_session_only",
                topic=active_topic,
                relationship_type="active_topic",
                time_relevance="current_session",
                approval_state="session_state",
                certainty="visible_session_state",
                retrieval_reason="active_topic",
                entity_keys=entity_keys,
            )
        )
    for index, side_topic in enumerate(dialogue.get("side_topics") or []):
        if not str(side_topic or "").strip():
            continue
        items.append(
            _context_item(
                f"active-side-topic-{index + 1}",
                summary=str(side_topic),
                source_class="dialogue_workspace",
                scope="current_session_only",
                topic=str(side_topic),
                relationship_type="nearby_paused_topic",
                time_relevance="current_session",
                approval_state="session_state",
                certainty="visible_session_state",
                retrieval_reason="semantic_side_topic_match",
                entity_keys=entity_keys,
            )
        )
    thread_braid = _dict(pragmatics.get("thread_braid"))
    traversal = [
        item
        for item in thread_braid.get("turn_traversal") or []
        if isinstance(item, dict) and str(item.get("text") or "").strip()
    ]
    if traversal:
        items.append(
            _context_item(
                "active-thread-traversal",
                summary=" ".join(str(item.get("text") or "") for item in traversal),
                source_class="conversation_thread_braid",
                scope="current_turn",
                topic=active_topic,
                relationship_type="visible_topic_branch_return_and_landing",
                time_relevance="now",
                approval_state="current_session_state",
                certainty="visible_discourse_structure",
                retrieval_reason="preserve_current_thread_traversal",
                entity_keys=entity_keys,
                current=True,
            )
        )
    previous = _dict(spine.get("previous_answer"))
    if previous.get("available") is True and str(previous.get("preview") or ""):
        items.append(
            _context_item(
                "active-previous-answer",
                summary=str(previous.get("preview") or ""),
                source_class="visible_previous_answer",
                scope="current_session_only",
                topic=active_topic,
                relationship_type="immediate_callback",
                time_relevance="immediately_prior",
                approval_state="visible_session_state",
                certainty="previously_expressed",
                retrieval_reason="contextual_follow_up",
                entity_keys=entity_keys,
            )
        )
    for index, obligation in enumerate(spine.get("open_obligations") or []):
        if not isinstance(obligation, dict):
            continue
        items.append(
            _context_item(
                f"active-obligation-{obligation.get('id') or index + 1}",
                summary=str(obligation.get("source_text") or ""),
                source_class="conversation_spine",
                scope="current_turn",
                topic=str(obligation.get("topic") or active_topic),
                relationship_type="open_response_obligation",
                time_relevance="now",
                approval_state="current_turn_required",
                certainty="literal_request",
                retrieval_reason="required_current_obligation",
                entity_keys=entity_keys,
                current=True,
            )
        )
    resolved = _dict(pragmatics.get("resolved_reference"))
    if str(resolved.get("resolved_to") or ""):
        items.append(
            _context_item(
                "active-resolved-reference",
                summary=str(resolved.get("resolved_to") or ""),
                source_class="dialogue_workspace",
                scope="current_session_only",
                topic=active_topic,
                relationship_type="resolved_referent",
                time_relevance="current_turn",
                approval_state="session_state",
                certainty=str(resolved.get("confidence") or "bounded"),
                retrieval_reason="current_referent",
                entity_keys=entity_keys,
                current=True,
            )
        )
    transient = _dict(_dict(dialogue.get("preferences")).get("transient"))
    directives = _dict(transient.get("directives"))
    if transient.get("active") is True and directives:
        items.append(
            _context_item(
                "active-transient-response-preference",
                summary="; ".join(
                    f"{key}: {value}"
                    for key, value in directives.items()
                    if str(value).strip()
                ),
                source_class="current_session_preference",
                scope="current_session_only_bounded_expiry",
                topic=active_topic,
                relationship_type="temporary_response_shape",
                time_relevance=(
                    f"{int(transient.get('remaining_turns') or 0)}_turns_remaining"
                ),
                approval_state="explicit_current_session_instruction",
                certainty="speaker_supplied",
                retrieval_reason="active_transient_preference",
                entity_keys=entity_keys,
                current=True,
            )
        )
    corrections = [
        item
        for item in dialogue.get("corrections") or []
        if isinstance(item, dict)
    ]
    if corrections:
        latest = corrections[-1]
        items.append(
            _context_item(
                "active-latest-correction",
                summary=" ".join(
                    str(
                        latest.get(key)
                        or ""
                    )
                    for key in (
                        "corrected_meaning",
                        "revised_claim",
                        "intended_meaning",
                    )
                    if str(latest.get(key) or "")
                ),
                source_class="current_session_correction",
                scope="current_session_only",
                topic=active_topic,
                relationship_type="correction",
                time_relevance="latest_correction",
                approval_state="session_state",
                certainty="speaker_correction",
                retrieval_reason="correction_must_be_preserved",
                entity_keys=entity_keys,
                current=True,
            )
        )
    return [item for item in items if str(item.get("summary") or "").strip()]


def _approved_horizon_items(
    prompt: str,
    *,
    memory: dict[str, Any],
    knowledge: dict[str, Any],
    checkpoints: list[dict[str, Any]],
    source_packets: list[dict[str, Any]],
    epistemic: dict[str, Any],
    active_thread_id: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if memory.get("memory_context_used") is True:
        for memory_item in memory.get("items") or []:
            if (
                not isinstance(memory_item, dict)
                or memory_item.get("retrieval_eligible") is not True
            ):
                continue
            items.append(
                _context_item(
                    f"approved-memory-{memory_item.get('id')}",
                    summary=str(
                        memory_item.get("summary")
                        or memory_item.get("title")
                        or ""
                    ),
                    source_class="approved_personal_memory",
                    scope=str(
                        memory_item.get("transfer_class") or "approved_context"
                    ),
                    topic=str(memory_item.get("title") or ""),
                    relationship_type="approved_memory_relevance",
                    time_relevance="reviewed_long_range",
                    approval_state="approved_memory",
                    certainty=str(memory_item.get("confidence") or "reviewed"),
                    retrieval_reason=str(
                        memory.get("retrieval_mode") or "approved_retrieval"
                    ),
                    source_refs=_text_list(memory_item.get("source_refs")),
                )
            )
    for knowledge_item in knowledge.get("answer_eligible_items") or []:
        if (
            not isinstance(knowledge_item, dict)
            or not str(knowledge_item.get("central_claim") or "").strip()
            or not _text_list(knowledge_item.get("source_refs"))
        ):
            continue
        items.append(
            _context_item(
                f"approved-knowledge-{knowledge_item.get('id') or knowledge_item.get('concept_id')}",
                summary=str(knowledge_item.get("central_claim") or ""),
                source_class="approved_general_knowledge",
                scope="; ".join(
                    str(item) for item in knowledge_item.get("limits") or []
                ),
                topic=str(knowledge_item.get("domain") or ""),
                relationship_type="approved_knowledge_relevance",
                time_relevance="reviewed_long_range",
                approval_state="approved_knowledge_resource",
                certainty=str(knowledge_item.get("confidence") or "reviewed"),
                retrieval_reason="strong_current_question_alignment",
                source_refs=_text_list(knowledge_item.get("source_refs")),
            )
        )
    for checkpoint in checkpoints[-64:]:
        if checkpoint.get("status") != "session_topic_checkpoint_ready":
            continue
        items.append(
            _context_item(
                f"checkpoint-{checkpoint.get('checkpoint_id')}",
                summary=str(
                    _dict(checkpoint.get("reasoning_state_capsule")).get(
                        "current_conclusion"
                    )
                    or next(
                        iter(checkpoint.get("established_visible_statements") or []),
                        "",
                    )
                ),
                source_class="session_topic_checkpoint",
                scope="current_session_only",
                topic=str(checkpoint.get("topic") or ""),
                relationship_type=(
                    "active_thread_checkpoint"
                    if active_thread_id
                    and str(checkpoint.get("thread_id") or "") == active_thread_id
                    else "prior_session_topic_checkpoint"
                ),
                time_relevance="earlier_current_session",
                approval_state="session_only_not_memory",
                certainty="previously_visible",
                retrieval_reason=(
                    "active_thread_checkpoint"
                    if active_thread_id
                    and str(checkpoint.get("thread_id") or "") == active_thread_id
                    else "semantic_topic_match"
                ),
                source_refs=_text_list(checkpoint.get("source_refs")),
                checkpoint_id=str(checkpoint.get("checkpoint_id") or ""),
            )
        )
    for index, packet in enumerate(source_packets):
        source_ref = str(packet.get("source_ref") or "").strip()
        summary = truncate(
            str(
                packet.get("statement")
                or packet.get("content")
                or packet.get("summary")
                or packet.get("title")
                or ""
            ),
            1000,
        )
        if not source_ref or not summary:
            continue
        items.append(
            _context_item(
                f"attributed-source-{index + 1}",
                summary=summary,
                source_class="current_attributed_source",
                scope="current_turn_only",
                topic=str(packet.get("title") or ""),
                relationship_type="supplied_source_evidence",
                time_relevance="current_turn",
                approval_state="attributed_current_source_not_retained",
                certainty=str(packet.get("confidence") or "source_supplied"),
                retrieval_reason="explicit_current_source_packet",
                source_refs=[source_ref],
                current=True,
            )
        )
    if epistemic.get("detected") is True:
        items.append(
            _context_item(
                "correction-ancestry-current-session",
                summary=str(
                    epistemic.get("revised_claim")
                    or epistemic.get("target")
                    or ""
                ),
                source_class="current_session_correction_ancestry",
                scope="current_session_only",
                topic=str(epistemic.get("target") or ""),
                relationship_type="correction_ancestry",
                time_relevance="current_revision",
                approval_state="visible_session_revision",
                certainty=str(epistemic.get("validity") or "revised"),
                retrieval_reason="preserve_current_correction_ancestry",
                current=True,
            )
        )
    return [item for item in items if str(item.get("summary") or "").strip()]


def _context_item(
    context_id: str,
    *,
    summary: str,
    source_class: str,
    scope: str,
    topic: str,
    relationship_type: str,
    time_relevance: str,
    approval_state: str,
    certainty: str,
    retrieval_reason: str,
    entity_keys: list[str] | None = None,
    source_refs: list[str] | None = None,
    checkpoint_id: str = "",
    current: bool = False,
) -> dict[str, Any]:
    topic_keys = sorted(_terms(f"{topic} {summary}"))[:24]
    return {
        "context_id": truncate(context_id, 160),
        "summary": truncate(summary, 1000),
        "topic_keys": topic_keys,
        "entity_keys": list(dict.fromkeys(entity_keys or []))[:20],
        "semantic_cue_keys": topic_keys,
        "relationship_type": relationship_type,
        "time_relevance": time_relevance,
        "source_class": source_class,
        "certainty": certainty,
        "scope": truncate(scope, 300),
        "approval_or_retention_state": approval_state,
        "contradiction_status": "none_visible",
        "retrieval_reason": retrieval_reason,
        "source_refs": source_refs or [],
        "checkpoint_id": checkpoint_id,
        "current": current,
        "writes_memory": False,
        "raw_corpus": False,
    }


def _select_items(
    items: list[dict[str, Any]],
    *,
    query_terms: set[str],
    limit: int,
    keep_current: bool,
) -> list[dict[str, Any]]:
    relationship_priority = {
        "open_response_obligation": 80,
        "current_input": 75,
        "correction": 70,
        "resolved_referent": 65,
        "temporary_response_shape": 60,
        "visible_topic_branch_return_and_landing": 55,
        "immediate_callback": 50,
        "active_topic": 45,
        "current_question": 40,
        "current_direct_request": 40,
        "current_indirect_request": 40,
        "current_correction": 40,
        "current_session_preference": 40,
        "current_statement": 35,
        "nearby_paused_topic": 10,
    }
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(items):
        item_terms = set(item.get("semantic_cue_keys") or [])
        overlap = query_terms & item_terms
        current = item.get("current") is True
        active_checkpoint = item.get("retrieval_reason") == "active_thread_checkpoint"
        relationship = str(item.get("relationship_type") or "")
        score = (
            (100 if keep_current and current else 0)
            + (40 if active_checkpoint else 0)
            + relationship_priority.get(relationship, 0)
            + 10 * len(overlap)
            + (5 if item.get("relationship_type") == "correction_ancestry" else 0)
        )
        if current or active_checkpoint or overlap or not query_terms:
            ranked.append((score, -index, item))
    ranked.sort(key=lambda value: (value[0], value[1]), reverse=True)
    return [
        {
            **item,
            "relevance_score": score,
            "matched_query_keys": sorted(
                query_terms & set(item.get("semantic_cue_keys") or [])
            ),
        }
        for score, _, item in ranked[:limit]
    ]


def _grounding_text(
    active_items: list[dict[str, Any]],
    approved_items: list[dict[str, Any]],
) -> str:
    active = [
        str(item.get("summary") or "")
        for item in active_items
        if item.get("source_class")
        in {
            "visible_previous_answer",
            "current_session_correction",
            "dialogue_workspace",
        }
        and str(item.get("summary") or "")
    ][:3]
    approved = [
        str(item.get("summary") or "")
        for item in approved_items
        if item.get("source_class")
        in {
            "approved_personal_memory",
            "approved_general_knowledge",
            "session_topic_checkpoint",
            "current_session_correction_ancestry",
        }
        and str(item.get("summary") or "")
    ][:3]
    parts: list[str] = []
    if active:
        parts.append("Selected current-session context: " + " ".join(active))
    if approved:
        parts.append("Selected approved or session-checkpoint context: " + " ".join(approved))
    return truncate(" ".join(parts), 1200)


def _terms(value: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-z0-9][a-z0-9_-]{2,}", value.lower())
        if word not in _STOP
    }


def _meaningful_overlap(left: set[str], right: set[str]) -> bool:
    overlap = left & right
    return len(overlap) >= 2 or bool(
        len(overlap) == 1 and len(next(iter(overlap))) >= 7
    )


def _sentences(value: str) -> list[str]:
    return [
        truncate(item.strip(), 1000)
        for item in re.split(r"(?<=[.!?])\s+|\n+", value)
        if item.strip()
    ][:16]


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [
        truncate(str(item).strip(), 300)
        for item in value
        if str(item).strip()
    ][:40]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
