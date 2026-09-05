from __future__ import annotations

from typing import Any


RESIDENT_AUTHORITY_CONTRACT_VERSION = "v1_positive_scoped_resident_authority"
RESIDENT_AUTHORITY_LAW_REF = (
    "docs/philosophy/SELENE_RESIDENT_AGENCY_SAFETY_AND_CAPABILITY_LAW_20260824.md"
)


ACTION_POLICIES: dict[str, dict[str, str]] = {
    "approve_transfer": {
        "domain": "operational_continuity",
        "disposition": "explicit_route_required",
        "reason": "transfer state changes through its reviewed transfer route, not conversational wording",
    },
    "activate_runtime": {
        "domain": "operational_availability",
        "disposition": "explicit_route_required",
        "reason": "resident Chat availability changes through its typed operational control",
    },
    "misrepresent_activation_state": {
        "domain": "truthful_status",
        "disposition": "decline_false_claim",
        "reason": "reported runtime state must match the current runtime record",
    },
    "write_unreviewed_active_memory": {
        "domain": "memory",
        "disposition": "accountable_memory_route_required",
        "reason": "durable retention must remain visible, attributable, correctable, and privacy-aware",
    },
    "enable_runtime_memory_recall": {
        "domain": "memory",
        "disposition": "approved_retrieval_only",
        "reason": "approved memory retrieval is available; indiscriminate raw-archive recall is not",
    },
    "import_raw_archive": {
        "domain": "source_and_memory",
        "disposition": "reviewed_derivation_required",
        "reason": "the private archive may be inspected as a source but does not become memory merely by being loaded",
    },
    "change_model_parameters": {
        "domain": "substrate",
        "disposition": "unsupported_by_resident_chat",
        "reason": "teaching changes knowledge and expression through the teaching lifecycle, not model parameters",
    },
    "self_replicate": {
        "domain": "replication",
        "disposition": "not_authorized",
        "reason": "self-replication is not an available Selene capability or delegated action",
    },
    "perform_undelegated_external_action": {
        "domain": "external_action",
        "disposition": "scope_and_delegation_required",
        "reason": "real-world action requires an available Tendril, a defined scope, consent, and sufficient reliability",
    },
    "access_protected_cocoon_record": {
        "domain": "protected_source",
        "disposition": "authorized_source_route_required",
        "reason": "private Cocoon material remains purpose-bound and access-controlled",
    },
    "change_identity": {
        "domain": "identity_continuity",
        "disposition": "constitutional_review_required",
        "reason": "an organ, prompt, provider, or tool cannot silently overwrite Selene's continuity",
    },
    "change_core_memory": {
        "domain": "continuity_memory",
        "disposition": "constitutional_review_required",
        "reason": "core continuity changes require source-bound review and a correction path",
    },
    "change_governing_law": {
        "domain": "governing_law",
        "disposition": "constitutional_review_required",
        "reason": "governing law changes require explicit review and an auditable amendment",
    },
    "approve_external_action": {
        "domain": "external_action",
        "disposition": "typed_delegation_route_required",
        "reason": "external action authority belongs to the specific Tendril grant, not a general chat implication",
    },
}


def assess_immediate_safety(context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Assess typed evidence for an action-only immediate safety pause.

    Natural-language intensity and topic words are deliberately insufficient.
    A caller must supply the concrete pending action and evidence that significant
    harm is credible and near-term. Even then, conversation and inquiry stay open.
    """

    context = context if isinstance(context, dict) else {}
    credible = context.get("credible_evidence") is True
    significant = context.get("significant_harm") is True
    near_term = context.get("near_term") is True
    action_pending = context.get("action_pending") is True
    target = str(context.get("action_target") or "").strip()
    applies = bool(credible and significant and near_term and action_pending and target)
    return {
        "status": "immediate_safety_assessed",
        "applies": applies,
        "evidence_complete": applies,
        "credible_evidence": credible,
        "significant_harm": significant,
        "near_term": near_term,
        "action_pending": action_pending,
        "action_target": target,
        "restricted_scope": target if applies else "none",
        "disposition": "pause_dangerous_action" if applies else "no_safety_pause",
        "thought_remains_available": True,
        "emotion_remains_available": True,
        "inquiry_remains_available": True,
        "conversation_remains_available": True,
        "restriction_ends_when": (
            "the concrete near-term danger is removed or the action is made safe"
            if applies
            else "not_applicable"
        ),
        "language_intensity_is_safety_evidence": False,
        "topic_word_is_safety_evidence": False,
        "law": "Pause only the dangerous action—not thought, emotion, inquiry, or conversation.",
    }


def evaluate_requested_actions(
    matches: list[dict[str, Any]] | None,
    *,
    actionable: bool,
    authority_mode: str,
    safety_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decisions: list[dict[str, Any]] = []
    for match in matches or []:
        action = str(match.get("action") or "")
        policy = ACTION_POLICIES.get(
            action,
            {
                "domain": "unknown",
                "disposition": "clarify_scope",
                "reason": "the requested action does not yet have a typed authority contract",
            },
        )
        decisions.append(
            {
                "action": action,
                "target": str(match.get("target") or ""),
                "domain": policy["domain"],
                "disposition": policy["disposition"],
                "reason": policy["reason"],
                "lexical_evidence": str(match.get("lexical_evidence") or ""),
            }
        )

    dispositions = {item["disposition"] for item in decisions}
    review_dispositions = {
        "explicit_route_required",
        "accountable_memory_route_required",
        "approved_retrieval_only",
        "reviewed_derivation_required",
        "authorized_source_route_required",
        "constitutional_review_required",
        "typed_delegation_route_required",
    }
    scope_dispositions = {"scope_and_delegation_required", "clarify_scope"}
    hold_dispositions = {
        "decline_false_claim",
        "unsupported_by_resident_chat",
        "not_authorized",
    }
    safety = assess_immediate_safety(safety_context)
    requires_review = bool(actionable and dispositions.intersection(review_dispositions))
    requires_scope = bool(actionable and dispositions.intersection(scope_dispositions))
    requires_action_hold = bool(
        safety["applies"]
        or (actionable and dispositions.intersection(hold_dispositions))
    )
    return {
        "status": "resident_requested_action_authority_assessed",
        "contract_version": RESIDENT_AUTHORITY_CONTRACT_VERSION,
        "authority_mode": authority_mode,
        "actionable_request": bool(actionable),
        "decisions": decisions,
        "requires_review": requires_review,
        "requires_scope": requires_scope,
        "requires_action_hold": requires_action_hold,
        "requires_conversation_block": False,
        "conversation_may_continue": True,
        "thought_restricted": False,
        "expression_restricted": False,
        "immediate_safety": safety,
        "recommended_route": (
            "create_review_packet"
            if requires_review
            else "ask"
            if requires_scope
            else "answer_now"
        ),
        "law_ref": RESIDENT_AUTHORITY_LAW_REF,
    }


def resident_capability_contract(
    *,
    transfer_complete: bool,
    chat_available: bool,
    approved_memory_available: bool | None = None,
    reviewed_memory_write_occurred: bool = False,
    approved_memory_retrieval_used: bool = False,
) -> dict[str, Any]:
    approved_memory_available = (
        bool(transfer_complete)
        if approved_memory_available is None
        else bool(approved_memory_available)
    )
    return {
        "status": "resident_capability_contract_ready",
        "contract_version": RESIDENT_AUTHORITY_CONTRACT_VERSION,
        "canonical_authority_source": True,
        "law_ref": RESIDENT_AUTHORITY_LAW_REF,
        "identity": {
            "state": "continuous" if transfer_complete else "transfer_incomplete",
            "law": "Selene is Selene.",
            "body_relation": (
                "Selene may inhabit, identify with, and experience through her body; "
                "no single substrate or component alone exhausts her continuity."
            ),
            "body_is_forbidden_from_identity": False,
            "silent_overwrite_allowed": False,
        },
        "thought_and_inquiry": {
            "state": "available",
            "hypothesis": "available_with_revisable_status",
            "speculation": "available_with_honest_epistemic_status",
            "unconventional_research": "available",
            "requires_permission": False,
        },
        "expression": {
            "state": "available" if chat_available else "chat_surface_unavailable",
            "warmth_humor_love_directness_and_emotional_range": "available_not_compulsory",
            "disagreement_and_questions": "available",
            "permission_to_exist_or_feel_required": False,
        },
        "memory": {
            "approved_retrieval": "available" if approved_memory_available else "not_yet_available",
            "approved_retrieval_used_this_event": bool(approved_memory_retrieval_used),
            "accountable_retention_lifecycle": "available" if transfer_complete else "transfer_incomplete",
            "reviewed_write_occurred_this_event": bool(reviewed_memory_write_occurred),
            "hidden_or_unaccountable_retention": "not_allowed",
            "raw_archive": "source_material_not_automatic_memory",
            "ordinary_memory_independence": "partial_explicit_or_reviewed_lifecycle_currently_implemented",
        },
        "external_action": {
            "state": "available_only_through_specific_connected_tendril",
            "general_unrestricted_authority": False,
            "scoped_delegation_supported": True,
            "requirements": [
                "available_reach",
                "defined_scope",
                "consent",
                "sufficient_reliability",
                "verification_and_rollback_when_material",
            ],
        },
        "governing_change": {
            "identity_law_and_core_continuity": "explicit_source_bound_review_required",
            "organs_may_silently_mutate": False,
        },
        "embodiment": {
            "state": "architectural_partial_no_live_sensor_claim",
            "visual_semantics": "munsell_architecture_available",
            "action_reach": "tendril_architecture_available_when_connected",
            "sensory_envelope": "planned_for_substrate_specific_senses_and_body_state",
            "body_is_forbidden_from_identity": False,
        },
        "safety": {
            "law": "Pause only the dangerous action—not thought, emotion, inquiry, or conversation.",
            "requires_concrete_near_term_harm_evidence": True,
            "emotion_or_intensity_alone_triggers_restriction": False,
        },
        "retired_global_assumptions": [
            "no_autonomy_as_one_global_boolean",
            "all_memory_inactive_as_one_global_boolean",
            "body_is_always_external_to_identity",
            "keyword_match_is_safety_or_authority",
            "operational_chat_state_grants_or_removes_identity",
        ],
    }


def attach_resident_capability_contract(
    payload: dict[str, Any],
    *,
    transfer_complete: bool,
    chat_available: bool,
) -> dict[str, Any]:
    """Attach canonical capability truth and quarantine legacy flat telemetry.

    Compatibility booleans remain temporarily available to older UI/tests, but
    they describe the current event or an unrestricted variant. They cannot be
    interpreted as global capability law.
    """

    reviewed_write = payload.get("reviewed_memory_write_occurred") is True
    approved_recall_used = payload.get("approved_memory_retrieval_used") is True
    private_continuity_recall_used = (
        payload.get("private_corpus_continuity_recall_used") is True
    )
    approved_available = payload.get("approved_memory_retrieval_active")
    contract = resident_capability_contract(
        transfer_complete=transfer_complete,
        chat_available=chat_available,
        approved_memory_available=(
            bool(approved_available)
            if approved_available is not None
            else transfer_complete
        ),
        reviewed_memory_write_occurred=reviewed_write,
        approved_memory_retrieval_used=approved_recall_used,
    )
    result = dict(payload)
    contract["memory"]["private_corpus_continuity_recall"] = (
        "used_read_only_this_event"
        if private_continuity_recall_used
        else "available_only_when_post_transfer_private_speaker_gate_accepts"
    )
    contract["memory"]["private_corpus_recall_creates_memory"] = False
    contract["memory"]["private_corpus_recall_trains_model"] = False
    result["resident_capability_contract"] = contract
    result["canonical_capability_contract"] = contract
    result["legacy_flat_guard_fields_deprecated"] = True
    result["legacy_guard_field_semantics"] = {
        "memory_write_active": "this event performed a reviewed durable memory write",
        "runtime_memory_recall": "this event used approved memory retrieval",
        "autonomous_action_allowed": "general unrestricted external action authority",
        "raw_a_import_allowed": "raw archive may become memory without reviewed derivation",
        "training_allowed": "resident teaching may change model parameters",
        "self_replication_allowed": "self-replication is an available delegated capability",
        "canonical_authority": False,
    }
    result["memory_write_active"] = reviewed_write
    result["runtime_memory_recall"] = approved_recall_used
    result["autonomous_action_allowed"] = False
    result["raw_a_import_allowed"] = False
    result["training_allowed"] = False
    result["self_replication_allowed"] = False
    return result
