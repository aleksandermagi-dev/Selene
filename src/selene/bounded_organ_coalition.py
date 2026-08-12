from __future__ import annotations

from hashlib import sha256
from typing import Any

from .registry import truncate


COALITION_BOUNDARY = (
    "bounded_turn_coordination_manifest_only_no_organ_command_execution_memory_"
    "identity_personality_governance_authority_voice_or_autonomy_change"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "voice_change": False,
}

ALLOWED_STATUSES = {"selected", "completed", "held", "unavailable", "unsupported"}


def build_bounded_organ_coalition(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe the bounded coalition already participating in one turn.

    This is an audit and handoff packet. It neither invokes an organ nor grants
    an organ authority.
    """
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or ""), 3000)
    stage = str(payload.get("stage") or "pre_expression")
    if stage not in {"pre_expression", "final"}:
        stage = "pre_expression"
    hard_boundary = payload.get("hard_boundary") is True
    spine = _dict(payload.get("conversation_spine"))
    route = _dict(payload.get("core_mind_route"))
    answer_engine = _dict(payload.get("answer_engine_support"))
    comprehension = _dict(payload.get("comprehension_context"))
    intelligence = _dict(payload.get("intelligence_os_support"))
    memory = _dict(payload.get("memory_context"))
    self_state = _dict(payload.get("self_state_context"))
    language = _dict(payload.get("language_capability"))
    structural = _dict(payload.get("structural_discovery"))
    exploratory = _dict(payload.get("exploratory_reasoning"))
    formation_braid = _dict(payload.get("formation_braid"))
    dual_horizon = _dict(payload.get("dual_horizon_context"))
    metacognition = _dict(payload.get("metacognition"))
    native_language = _dict(payload.get("native_language"))
    voice = _dict(payload.get("voice_preview"))
    visible_release = _dict(payload.get("visible_speech_release"))
    coverage = _dict(payload.get("response_coverage"))
    max_optional = max(
        1,
        min(int(payload.get("max_optional_content_organs") or 6), 10),
    )
    obligation_ids = _obligation_ids(spine)
    coordination_units = [
        item
        for item in (_dict(answer_engine.get("coordination_plan")).get(
            "coordination_units"
        ) or [])
        if isinstance(item, dict)
    ][:20]

    shared = [
        _entry(
            "core_mind",
            layer="shared_authority",
            role="law_and_route_owner",
            status="completed" if route else "selected",
            required=True,
            basis=(
                str(route.get("selected_route") or "current_turn_route")
                if route
                else "required_shared_authority"
            ),
            obligation_ids=obligation_ids,
            authority_scope="routing_and_governing_boundaries_only",
        ),
        _entry(
            "provenance_boundary_gate",
            layer="shared_authority",
            role="source_and_boundary_gate",
            status="completed",
            required=True,
            basis=(
                "hard_boundary_resolved"
                if hard_boundary
                else "current_turn_sources_checked"
            ),
            obligation_ids=obligation_ids,
            authority_scope="release_eligibility_only",
        ),
        _entry(
            "conversation_spine",
            layer="shared_coordination",
            role="current_turn_grounding_and_obligation_owner",
            status=(
                "completed"
                if str(spine.get("status") or "").endswith("ready")
                else "unavailable"
            ),
            required=True,
            basis=(
                "grounded_current_turn_obligations"
                if spine
                else "conversation_spine_not_supplied"
            ),
            obligation_ids=obligation_ids,
            authority_scope="current_session_grounding_only",
        ),
    ]

    selected_source_id = str(
        _dict(payload.get("visible_speech_seed")).get("selected_source_id") or ""
    )
    answer_domain = str(answer_engine.get("selected_domain") or "")
    answer_packet = _dict(answer_engine.get("answer_packet"))
    content: list[dict[str, Any]] = []

    answer_engine_ids = _owner_obligation_ids(coordination_units, "answer_engine")
    if answer_engine.get("used") is True:
        answer_engine_status = (
            "completed"
            if answer_engine.get("adapter_executed") is True
            else "selected"
        )
        answer_engine_basis = (
            f"current_turn_domain:{answer_domain or 'bounded_answer'}"
        )
    elif answer_domain == "local_code_inspection":
        answer_engine_status = "held"
        answer_engine_basis = "local_code_remains_an_explicit_separate_inspection_route"
    elif answer_domain == "unsupported":
        answer_engine_status = "unsupported"
        answer_engine_basis = "no_supported_domain_adapter_for_current_obligation"
    elif hard_boundary:
        answer_engine_status = "held"
        answer_engine_basis = "core_mind_boundary_precedes_domain_answering"
    else:
        answer_engine_status = "held"
        answer_engine_basis = "no_current_obligation_selected_the_answer_engine"
    content.append(
        _entry(
            "answer_engine",
            layer="optional_content",
            role="bounded_domain_answer_coordination",
            status=answer_engine_status,
            required=False,
            basis=answer_engine_basis,
            obligation_ids=answer_engine_ids,
            authority_scope="domain_answer_content_only",
            confidence=_dict(answer_engine.get("confidence_vector")),
        )
    )

    intelligence_used = intelligence.get("used") is True
    content.append(
        _entry(
            "intelligence_os",
            layer="optional_content",
            role="open_ended_reasoning_support",
            status="completed" if intelligence_used else "held",
            required=False,
            basis=(
                "current_turn_reasoning_support_used"
                if intelligence_used
                else "not_selected_for_current_visible_answer"
            ),
            obligation_ids=(
                _owner_obligation_ids(
                    coordination_units,
                    "ordinary_conversation_path",
                )
                if intelligence_used
                else []
            ),
            authority_scope="reasoning_support_only",
            confidence={"answer_confidence": str(intelligence.get("confidence") or "")},
        )
    )

    knowledge_seed = str(comprehension.get("knowledge_response_seed") or "").strip()
    knowledge_owner_ids = _owner_obligation_ids(
        coordination_units,
        "comprehension_integration",
    )
    content.append(
        _entry(
            "comprehension_integration",
            layer="optional_content",
            role="approved_general_knowledge_support",
            status="completed" if knowledge_seed else "held",
            required=False,
            basis=(
                "approved_knowledge_answer_selected"
                if knowledge_seed
                else "no_approved_knowledge_unit_selected_for_expression"
            ),
            obligation_ids=knowledge_owner_ids,
            authority_scope="approved_general_knowledge_only",
        )
    )

    memory_used = memory.get("memory_context_used") is True
    content.append(
        _entry(
            "approved_memory_retrieval",
            layer="optional_content",
            role="reviewed_personal_memory_context",
            status="completed" if memory_used else "held",
            required=False,
            basis=(
                "approved_retrieval_selected_for_current_turn"
                if memory_used
                else "no_retrieval_eligible_memory_selected"
            ),
            obligation_ids=obligation_ids if memory_used else [],
            authority_scope="reviewed_personal_memory_read_only",
            confidence={"memory_confidence": str(memory.get("memory_confidence") or "")},
        )
    )

    self_state_used = self_state.get("used") is True
    content.append(
        _entry(
            "self_state",
            layer="optional_content",
            role="current_state_answer_support",
            status="completed" if self_state_used else "held",
            required=False,
            basis=(
                "current_turn_requested_self_state"
                if self_state_used
                else "self_state_not_requested"
            ),
            obligation_ids=obligation_ids if self_state_used else [],
            authority_scope="current_state_observation_only",
        )
    )

    language_used = bool(str(language.get("content_seed") or "").strip())
    content.append(
        _entry(
            "language_capability_shelf",
            layer="optional_content",
            role="reviewed_language_capability_support",
            status="completed" if language_used else "held",
            required=False,
            basis=(
                "reviewed_language_capability_selected"
                if language_used
                else "no_language_capability_item_required"
            ),
            obligation_ids=obligation_ids if language_used else [],
            authority_scope="language_capability_only_not_personality",
        )
    )

    structural_used = bool(str(structural.get("response_seed") or "").strip())
    exploratory_used = exploratory.get("selected_for_answer") is True and bool(
        str(exploratory.get("response_seed") or "").strip()
    )
    content.append(
        _entry(
            "exploratory_reasoning",
            layer="optional_content",
            role="prediction_hypothesis_comparison_and_data_conflict_coordination",
            status="completed" if exploratory_used else "held",
            required=False,
            basis=(
                f"current_turn_exploratory_response:{exploratory.get('response_kind')}"
                if exploratory_used
                else "no_bounded_exploratory_response_selected"
            ),
            obligation_ids=obligation_ids if exploratory_used else [],
            authority_scope="current_turn_exploratory_coordination_only",
            confidence=_dict(exploratory.get("confidence")),
        )
    )
    content.append(
        _entry(
            "structural_discovery",
            layer="optional_content",
            role="bounded_cross_domain_structure_support",
            status="completed" if structural_used else "held",
            required=False,
            basis=(
                "current_turn_structural_discovery_supplied"
                if structural_used
                else "no_bounded_structural_discovery_selected"
            ),
            obligation_ids=obligation_ids if structural_used else [],
            authority_scope="hypothesis_and_structure_support_only",
        )
    )

    specialized_content_selected = any(
        item["status"] in {"selected", "completed"} for item in content
    )
    conversation_selected = (
        selected_source_id
        in {
            "figurative_meaning_clarification",
            "mixed_conversation_answer",
            "conversational_memory_action",
            "local_chat_continuity",
            "contextual_follow_up",
            "conversation_policy",
            "epistemic_revision",
        }
        or not specialized_content_selected
    )
    content.append(
        _entry(
            "ordinary_conversation_path",
            layer="optional_content",
            role="ordinary_social_and_contextual_answer_support",
            status="completed" if conversation_selected else "held",
            required=False,
            basis=(
                f"selected_visible_source:{selected_source_id or 'ordinary_conversation'}"
                if conversation_selected
                else "specialized_supported_content_owns_current_answer"
            ),
            obligation_ids=(
                _owner_obligation_ids(
                    coordination_units,
                    "ordinary_conversation_path",
                )
                or (obligation_ids if conversation_selected else [])
            ),
            authority_scope="current_conversation_content_only",
        )
    )

    metacognition_complete = bool(
        metacognition
        and str(metacognition.get("status") or "").startswith("metacognition_")
    )
    monitoring = [
        _entry(
            "metacognition",
            layer="monitoring",
            role="fit_confidence_reopening_and_stopping_advisor",
            status="completed" if metacognition_complete else "selected",
            required=True,
            basis=(
                str(metacognition.get("fit_state") or "final_fit_check_complete")
                if metacognition_complete
                else "scheduled_bounded_fit_check"
            ),
            obligation_ids=obligation_ids,
            authority_scope="advisory_only",
        )
    ]

    nlo_complete = bool(native_language.get("candidate_text"))
    voice_complete = bool(voice.get("candidate_text") or voice.get("voice_confidence"))
    expression = [
        _entry(
            "native_language_organ",
            layer="required_expression",
            role="meaning_preserving_language_formation",
            status="completed" if nlo_complete else "selected",
            required=True,
            basis=(
                "language_candidate_realized"
                if nlo_complete
                else "required_after_supported_meaning_selection"
            ),
            obligation_ids=obligation_ids,
            authority_scope="language_structure_only",
        ),
        _entry(
            "voice_module",
            layer="required_expression",
            role="selene_expression_style",
            status="completed" if voice_complete else "selected",
            required=True,
            basis=(
                "voice_preview_complete"
                if voice_complete
                else "required_after_nlo_formation"
            ),
            obligation_ids=obligation_ids,
            authority_scope="expression_style_only",
        ),
    ]

    selected_optional = [
        item
        for item in content
        if item["status"] in {"selected", "completed"}
    ]
    held_optional = [
        item
        for item in content
        if item["status"] in {"held", "unavailable", "unsupported"}
    ]
    manifest_id = _manifest_id(
        str(spine.get("turn_id") or ""),
        prompt,
    )
    confidence = _confidence_vector(
        answer_engine=answer_engine,
        metacognition=metacognition,
        memory=memory,
        voice=voice,
    )
    graceful_fall = _graceful_fall(
        hard_boundary=hard_boundary,
        answer_packet=answer_packet,
        visible_release=visible_release,
        coverage=coverage,
    )
    return {
        "status": (
            "bounded_organ_coalition_final"
            if stage == "final"
            else "bounded_organ_coalition_selected"
        ),
        "version": "v1_bounded_organ_coalition_manifest",
        "manifest_id": manifest_id,
        "stage": stage,
        "is_organ": False,
        "coordination_manifest_only": True,
        "invokes_organs": False,
        "shared_participants": shared,
        "optional_content_participants": content,
        "monitoring_participants": monitoring,
        "required_expression_participants": expression,
        "selected_optional_participants": selected_optional,
        "held_optional_participants": held_optional,
        "selected_optional_count": len(selected_optional),
        "held_optional_count": len(held_optional),
        "activation_budget": {
            "kind": "bounded_optional_content_participants",
            "maximum": max_optional,
            "selected": len(selected_optional),
            "within_budget": len(selected_optional) <= max_optional,
            "budget_changes_runtime_execution": False,
            "latency_measurement_available": False,
        },
        "coordination_layers": [
            {
                "id": "selective_formation_braid",
                "status": str(
                    formation_braid.get("status") or "not_supplied"
                ),
                "selected_unit_count": int(
                    formation_braid.get("selected_unit_count") or 0
                ),
                "is_organ": False,
                "changes_answer_authority": False,
            },
            {
                "id": "dual_horizon_context",
                "status": str(
                    dual_horizon.get("status") or "not_supplied"
                ),
                "active_selected_count": int(
                    _dict(dual_horizon.get("active_horizon")).get(
                        "selected_count"
                    )
                    or 0
                ),
                "approved_selected_count": int(
                    _dict(
                        dual_horizon.get("approved_long_range_horizon")
                    ).get("selected_count")
                    or 0
                ),
                "is_organ": False,
                "selection_layer_only": True,
                "changes_answer_authority": False,
                "writes_memory": False,
                "raw_corpus_loaded": False,
            },
        ],
        "obligation_ids": obligation_ids,
        "obligation_owner_map": _obligation_owner_map(
            coordination_units,
            answer_engine=answer_engine,
        ),
        "confidence_vector": confidence,
        "graceful_fall": graceful_fall,
        "hard_boundary": hard_boundary,
        "explicit_non_authorities": {
            "support_organs_may_change_law": False,
            "support_organs_may_change_identity": False,
            "support_organs_may_change_personality": False,
            "support_organs_may_write_memory": False,
            "support_organs_may_grant_authority": False,
            "metacognition_may_rewrite_answer_directly": False,
            "coalition_manifest_may_execute_organs": False,
            "nlo_may_change_supported_meaning": False,
            "voice_may_change_supported_meaning": False,
        },
        "core_mind_route_owner": True,
        "answer_engine_domain_owner": True,
        "nlo_language_owner": True,
        "voice_final_expression_compatibility_owner": True,
        "memory_ownership_unchanged": True,
        "context_selection_ownership_unchanged": True,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "review_status": "status_only",
        "provenance_boundary": COALITION_BOUNDARY,
        **GUARDS,
    }


def _entry(
    participant_id: str,
    *,
    layer: str,
    role: str,
    status: str,
    required: bool,
    basis: str,
    obligation_ids: list[str],
    authority_scope: str,
    confidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_status = status if status in ALLOWED_STATUSES else "held"
    return {
        "participant_id": participant_id,
        "layer": layer,
        "role": role,
        "status": normalized_status,
        "selected": normalized_status in {"selected", "completed"},
        "required": required,
        "obligation_ids": list(dict.fromkeys(obligation_ids))[:20],
        "selection_basis": truncate(basis, 360),
        "confidence": confidence or {},
        "authority_scope": authority_scope,
        "may_command_other_organs": False,
        "may_write_memory": False,
        "may_change_identity": False,
        "may_change_personality": False,
        "may_change_governance": False,
        "may_expand_autonomy": False,
    }


def _obligation_ids(spine: dict[str, Any]) -> list[str]:
    return [
        str(item.get("id") or "")
        for item in spine.get("open_obligations") or []
        if isinstance(item, dict) and str(item.get("id") or "")
    ][:20]


def _owner_obligation_ids(
    coordination_units: list[dict[str, Any]],
    owner: str,
) -> list[str]:
    return list(
        dict.fromkeys(
            str(_dict(item.get("obligation")).get("id") or "")
            for item in coordination_units
            if str(item.get("responsible_owner") or "") == owner
            and str(_dict(item.get("obligation")).get("id") or "")
        )
    )[:20]


def _obligation_owner_map(
    coordination_units: list[dict[str, Any]],
    *,
    answer_engine: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "obligation_id": str(_dict(item.get("obligation")).get("id") or ""),
            "responsible_owner": str(
                item.get("responsible_owner") or "unassigned"
            ),
            "selected_domain": str(
                item.get("selected_domain") or "ordinary_conversation"
            ),
            "executable_in_chat": item.get("executable_in_chat") is True,
            "adapter_executed": (
                item.get("adapter_executed") is True
                or (
                    str(item.get("responsible_owner") or "") == "answer_engine"
                    and answer_engine.get("adapter_executed") is True
                    and str(item.get("selected_domain") or "")
                    == str(answer_engine.get("selected_domain") or "")
                )
            ),
        }
        for item in coordination_units
        if str(_dict(item.get("obligation")).get("id") or "")
    ][:20]


def _confidence_vector(
    *,
    answer_engine: dict[str, Any],
    metacognition: dict[str, Any],
    memory: dict[str, Any],
    voice: dict[str, Any],
) -> dict[str, Any]:
    engine = _dict(answer_engine.get("confidence_vector"))
    meta = _dict(metacognition.get("confidence_vector"))
    return {
        "route_confidence": str(
            meta.get("route_confidence")
            or engine.get("route_confidence")
            or "not_assessed"
        ),
        "evidence_confidence": str(
            meta.get("evidence_confidence")
            or engine.get("evidence_confidence")
            or "not_assessed"
        ),
        "answer_confidence": str(
            meta.get("answer_confidence")
            or engine.get("answer_confidence")
            or "not_assessed"
        ),
        "memory_confidence": str(
            meta.get("memory_confidence")
            or memory.get("memory_confidence")
            or "not_used"
        ),
        "expression_confidence": str(
            meta.get("expression_confidence")
            or voice.get("voice_confidence")
            or "not_assessed"
        ),
        "dimensions_are_independent": True,
        "expression_confidence_is_answer_correctness": False,
    }


def _graceful_fall(
    *,
    hard_boundary: bool,
    answer_packet: dict[str, Any],
    visible_release: dict[str, Any],
    coverage: dict[str, Any],
) -> dict[str, Any]:
    if hard_boundary:
        return {
            "needed": True,
            "path": "core_mind_boundary_response",
            "reason": "hard_boundary_controls_before_optional_content",
        }
    if visible_release.get("graceful_fall_used") is True:
        return {
            "needed": True,
            "path": "visible_speech_graceful_fall",
            "reason": "candidate_release_was_held",
        }
    no_answer_reason = str(answer_packet.get("no_answer_reason") or "").strip()
    if no_answer_reason:
        return {
            "needed": True,
            "path": "explicit_unsupported_domain_answer",
            "reason": truncate(no_answer_reason, 360),
        }
    if (
        str(answer_packet.get("direct_answer") or "").strip()
        and not [
            item
            for item in answer_packet.get("unanswered_obligations") or []
            if item
        ]
    ):
        return {
            "needed": False,
            "path": "not_needed",
            "reason": "current_turn_domain_owner_completed_its_obligations",
        }
    if int(coverage.get("unresolved_count") or 0) > 0:
        return {
            "needed": True,
            "path": "one_bounded_owner_recheck_or_material_question",
            "reason": "one_or_more_current_obligations_remain_unresolved",
        }
    return {
        "needed": False,
        "path": "not_needed",
        "reason": "selected_participants_supported_the_current_response",
    }


def _manifest_id(turn_id: str, prompt: str) -> str:
    digest = sha256(f"{turn_id}|{prompt}".encode("utf-8")).hexdigest()[:16]
    return f"organ-coalition-{digest}"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
