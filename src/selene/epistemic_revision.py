from __future__ import annotations

import re
from typing import Any

from .registry import truncate


EPISTEMIC_REVISION_BOUNDARY = (
    "visible_claim_update_coordination_only_existing_owners_retain_session_knowledge_memory_"
    "identity_governance_evidence_and_expression_authority"
)

UPDATE_KINDS = {
    "correction",
    "refinement",
    "scope_restriction",
    "extension",
    "competing_explanation",
    "unresolved_contradiction",
    "replacement",
    "reopening",
}

UPDATE_SUBJECTS = {"aleks", "selene", "shared_model", "unspecified"}

LOCKED_TARGET_CLASSES = {"identity", "personality", "governance", "law", "authority"}

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "automatic_cocoon_routing": False,
    "hidden_chain_of_thought_exposed": False,
}


def epistemic_revision_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "epistemic_revision_contract_ready",
            "version": "v1_selective_epistemic_revision",
            "supported_update_kinds": sorted(UPDATE_KINDS),
            "supported_update_subjects": sorted(UPDATE_SUBJECTS),
            "owners": {
                "current_session_meaning": "Dialogue Workspace and Conversation Spine",
                "retained_knowledge": "Comprehension and Integration review lifecycle",
                "personal_memory": "Memory Organ review lifecycle",
                "fit_reopening_and_stopping": "Metacognition",
                "identity_governance_and_authority": "Core/Mind",
                "expression": "NLO and Voice",
            },
            "principles": [
                "identify the affected claim instead of resetting the whole context",
                "preserve observations assumptions and structure that still fit",
                "recheck only dependent conclusions",
                "leave unresolved contradiction visible",
                "retain model ancestry and valid scope",
                "treat ordinary wrongness as correctable rather than shameful",
                "allow evidence to update either Aleks or Selene",
            ],
            "direct_truth_authority": False,
            "automatic_retained_knowledge_rewrite": False,
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": EPISTEMIC_REVISION_BOUNDARY,
        }
    )


def build_epistemic_revision_plan(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400).strip()
    correction = (
        payload.get("correction_refinement")
        if isinstance(payload.get("correction_refinement"), dict)
        else {}
    )
    previous_claims = _text_list(
        payload.get("previous_claims") or payload.get("prior_claims"),
        width=900,
        limit=8,
    )
    prior_updates = [
        item for item in payload.get("prior_updates") or [] if isinstance(item, dict)
    ][-12:]
    requested_kind = str(
        payload.get("requested_kind") or payload.get("update_kind") or ""
    ).strip()
    if requested_kind and requested_kind not in UPDATE_KINDS:
        raise ValueError(f"unsupported epistemic update kind: {requested_kind}")
    update_subject = _update_subject(payload)

    kind, basis = (
        (requested_kind, "explicit_structured_update_kind")
        if requested_kind
        else _classify_update(prompt, correction, bool(previous_claims))
    )
    detected = bool(kind)
    target_class = _target_class(payload)
    owner_locked = target_class in LOCKED_TARGET_CLASSES
    if owner_locked:
        detected = False

    corrected_meaning = truncate(str(correction.get("corrected_meaning") or ""), 500).strip()
    replaced_meaning = truncate(str(correction.get("replaced_meaning") or ""), 500).strip()
    prior_claim = truncate(
        str(
            payload.get("prior_claim")
            or replaced_meaning
            or (previous_claims[0] if previous_claims else "")
        ),
        900,
    ).strip()
    revised_claim = truncate(
        str(
            payload.get("revised_claim")
            or corrected_meaning
            or _revised_claim(prompt, kind)
        ),
        1200,
    ).strip()
    target = truncate(
        str(
            payload.get("target")
            or replaced_meaning
            or _target(prompt, kind)
            or prior_claim
            or "the affected claim"
        ),
        500,
    ).strip()
    scope = truncate(
        str(payload.get("scope") or _scope(prompt, kind)),
        600,
    ).strip()
    supplied_conflicts = _text_list(
        payload.get("contradictions") or payload.get("conflicting_claims"),
        width=900,
        limit=8,
    )
    conflicts = supplied_conflicts or (
        [item for item in (prior_claim, revised_claim) if item]
        if kind == "unresolved_contradiction"
        else []
    )
    source_refs = _text_list(payload.get("source_refs"), width=300, limit=30)
    evidence_items = _text_list(
        payload.get("new_evidence") or payload.get("evidence"),
        width=900,
        limit=12,
    )
    new_material_present = bool(
        payload.get("new_material_present")
        or evidence_items
        or corrected_meaning
        or requested_kind
    )
    disposition = _disposition(kind, owner_locked)
    validity = _validity(kind, owner_locked)
    preserved = _preserved_structure(kind, prior_claim, owner_locked)
    dependencies = _dependencies(payload, kind, target)
    ancestry = _ancestry(kind, prior_claim, revised_claim, scope)

    result = {
        "status": (
            "epistemic_revision_held_by_owner"
            if owner_locked
            else "epistemic_revision_plan_ready"
            if detected
            else "epistemic_revision_not_detected"
        ),
        "version": "v1_selective_epistemic_revision",
        "detected": detected,
        "update_kind": kind if detected else "none",
        "update_subject": update_subject,
        "evidence_may_update_either_participant": True,
        "classification_basis": basis if detected or owner_locked else "no_explicit_update_signal",
        "target_class": target_class,
        "target": target if detected or owner_locked else "",
        "prior_claim": prior_claim if detected else "",
        "revised_claim": revised_claim if detected else "",
        "scope": scope if detected else "",
        "unresolved_contradictions": conflicts if detected else [],
        "evidence": {
            "items": evidence_items,
            "source_refs": source_refs,
            "new_material_present": new_material_present,
            "possibility_is_not_proof": True,
            "language_fluency_is_not_evidence": True,
        },
        "disposition": disposition,
        "validity": validity,
        "preserved_structure": preserved,
        "dependent_recheck": dependencies,
        "model_ancestry": ancestry,
        "response_obligations": _response_obligations(kind, disposition),
        "metacognitive_handoff": {
            "reopen_requested": disposition in {
                "reopen_affected_model_once",
                "hold_contradiction_visible",
            },
            "compare_competing_explanations": disposition == "compare_without_premature_replacement",
            "hold_for_evidence": disposition == "hold_contradiction_visible",
            "correction_received": kind in {
                "correction",
                "refinement",
                "scope_restriction",
                "replacement",
            },
            "new_material_present": new_material_present,
        },
        "retained_state_handoff": {
            "automatic_knowledge_rewrite": False,
            "automatic_memory_rewrite": False,
            "approved_knowledge_change_route": "Comprehension review and reapproval",
            "personal_memory_change_route": "Memory Organ review",
            "supersession_deletes_ancestry": False,
        },
        "social_posture": {
            "wrongness_is_failure": False,
            "collapse_required": False,
            "defensive_persistence_allowed": False,
            "over_apology_required": False,
            "correction_can_update_aleks_or_selene": True,
            "truth_does_not_require_rudeness": True,
        },
        "owner_lock": {
            "held": owner_locked,
            "owner": "Core/Mind" if owner_locked else "",
            "reason": (
                "identity, personality, governance, law, and authority cannot be revised by a conversation update packet"
                if owner_locked
                else ""
            ),
        },
        "prior_update_count": len(prior_updates),
        "session_scoped_only": target_class == "current_session_claim",
        "visible_summary_only": True,
        "direct_truth_authority": False,
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": EPISTEMIC_REVISION_BOUNDARY,
    }
    return _with_guards(result)


def epistemic_revision_response_seed(
    plan: dict[str, Any] | None,
) -> str:
    plan = plan if isinstance(plan, dict) else {}
    if plan.get("detected") is not True or (plan.get("owner_lock") or {}).get("held") is True:
        return ""
    kind = str(plan.get("update_kind") or "")
    prior = str(plan.get("prior_claim") or "").strip().rstrip(". ")
    revised = str(plan.get("revised_claim") or "").strip().rstrip(". ")
    scope = str(plan.get("scope") or "").strip().rstrip(". ")
    target = str(plan.get("target") or "the affected claim").strip().rstrip(". ")

    if kind == "correction":
        return ""
    if kind == "refinement":
        detail = revised or target
        return (
            f"That refines the affected point: {detail}. "
            "I would update that detail and keep the surrounding structure that still fits."
        )
    if kind == "scope_restriction":
        claim = revised or prior or target
        scope_clause = f" within {scope}" if scope and scope.lower() not in claim.lower() else ""
        return (
            f"The narrower version is {claim}{scope_clause}. "
            "The earlier model can remain useful inside that scope, but I should not carry it beyond the conditions that support it."
        )
    if kind == "extension":
        detail = revised or target
        return (
            f"That extends the earlier account with {detail}. "
            "The earlier supported part can stay; this adds a condition, relation, or case rather than erasing it."
        )
    if kind == "competing_explanation":
        detail = revised or target
        return (
            f"I would keep {detail} as a competing explanation, not a settled replacement. "
            "The useful next move is to compare both explanations against the same observations and ask what would distinguish them."
        )
    if kind == "unresolved_contradiction":
        return (
            "Those claims remain in conflict. I would not force them into agreement without deciding evidence; "
            "the unaffected observations can stay while the disputed conclusion remains open."
        )
    if kind == "replacement":
        detail = revised or target
        return (
            f"{detail} replaces the affected conclusion for the current discussion. "
            "The earlier version remains attributable as the prior model, not as the current answer."
        )
    if kind == "reopening":
        return (
            f"That is enough to reopen {target}. "
            "I would preserve what still fits, recheck the changed dependency once, and keep the conclusion provisional until it fits the new evidence."
        )
    return ""


def compact_epistemic_update(plan: dict[str, Any] | None) -> dict[str, Any]:
    plan = plan if isinstance(plan, dict) else {}
    return {
        "update_kind": str(plan.get("update_kind") or "none"),
        "update_subject": str(plan.get("update_subject") or "unspecified"),
        "target": truncate(str(plan.get("target") or ""), 300),
        "prior_claim": truncate(str(plan.get("prior_claim") or ""), 500),
        "revised_claim": truncate(str(plan.get("revised_claim") or ""), 500),
        "scope": truncate(str(plan.get("scope") or ""), 300),
        "disposition": str(plan.get("disposition") or "no_update"),
        "validity": str(plan.get("validity") or "unchanged"),
        "status": "current_session_update",
        "session_scoped_only": plan.get("session_scoped_only") is True,
        "model_ancestry_preserved": bool((plan.get("model_ancestry") or {}).get("preserved")),
        "durable_memory_write": False,
    }


def _classify_update(
    prompt: str,
    correction: dict[str, Any],
    previous_available: bool,
) -> tuple[str, str]:
    lower = " ".join(prompt.lower().replace("’", "'").split())
    if correction.get("detected") is True:
        if _has_scope_restriction(lower):
            return "scope_restriction", "structured_correction_with_scope_narrowing"
        if _has_replacement(lower):
            return "replacement", "structured_correction_with_explicit_replacement"
        return "correction", "dialogue_workspace_structured_correction"
    if re.search(r"\b(?:reopen|recheck|revisit|re-evaluate|reevaluate)\b", lower) or (
        previous_available
        and re.search(r"\b(?:new|later|changed)\s+evidence\b", lower)
        and re.search(r"\b(?:no longer fits|changes? the fit|breaks|undermines)\b", lower)
    ):
        return "reopening", "explicit_reopening_or_changed_evidence"
    if re.search(
        r"\b(?:unresolved contradiction|contradicts?|conflicts? with|cannot both be true|can't both be true)\b",
        lower,
    ) and not _has_replacement(lower):
        return "unresolved_contradiction", "explicit_unresolved_conflict"
    if re.search(
        r"\b(?:competing|alternative|another|second)\s+(?:explanation|hypothesis|model|mechanism)\b",
        lower,
    ) or re.search(r"\bcould instead (?:be|come from|result from|mean)\b", lower):
        return "competing_explanation", "explicit_competing_explanation"
    if _has_scope_restriction(lower):
        return "scope_restriction", "explicit_scope_narrowing"
    if _has_replacement(lower):
        return "replacement", "explicit_replacement"
    if re.search(
        r"\b(?:extend|extension|also applies|in addition|adds? another|builds? on)\b",
        lower,
    ):
        return "extension", "explicit_extension"
    if re.search(
        r"\b(?:more precisely|to be precise|refinement|refine|narrower version|not wrong,? but)\b",
        lower,
    ):
        return "refinement", "explicit_refinement"
    if previous_available and re.search(
        r"\b(?:that is wrong|that's wrong|you were wrong|i was wrong|not what i meant)\b",
        lower,
    ):
        return "correction", "explicit_current_session_wrongness"
    return "", ""


def _has_scope_restriction(lower: str) -> bool:
    return bool(
        re.search(
            r"\b(?:only applies|applies only|valid only|works only|limited to|within this scope|"
            r"under these conditions|at low speeds|in the narrower case)\b",
            lower,
        )
    )


def _has_replacement(lower: str) -> bool:
    return bool(
        re.search(
            r"\b(?:replace|replaced by|use .{1,120} instead|no longer use|supersedes?|"
            r"discard the conclusion)\b",
            lower,
        )
    )


def _revised_claim(prompt: str, kind: str) -> str:
    text = " ".join(prompt.split()).strip(" ,")
    if not text or not kind:
        return ""
    if kind == "replacement":
        match = re.search(
            r"\breplace\s+(.+?)\s+with\s+(.+?)(?:[.!?]|$)",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(2).strip(" ,")
    if kind == "scope_restriction":
        match = re.search(
            r"(.+?\b(?:only applies|applies only|is valid only|works only|is limited to)\b.+?)(?:[.!?]|$)",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(1).strip(" ,")
    return truncate(text, 1200)


def _scope(prompt: str, kind: str) -> str:
    if kind != "scope_restriction":
        return ""
    match = re.search(
        r"\b(?:only applies|applies only|valid only|works only|limited to|within)\s+(.+?)(?:[.!?]|$)",
        prompt,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip(" ,") if match else ""


def _target(prompt: str, kind: str) -> str:
    if kind == "replacement":
        match = re.search(
            r"\breplace\s+(.+?)\s+with\s+.+?(?:[.!?]|$)",
            prompt,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(1).strip(" ,")
    if kind == "reopening":
        match = re.search(
            r"\b(?:reopen|recheck|revisit|re-evaluate|reevaluate)\s+(.+?)(?:[.!?]|$)",
            prompt,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(1).strip(" ,")
    return ""


def _target_class(payload: dict[str, Any]) -> str:
    supplied = str(payload.get("target_class") or "current_session_claim").strip().lower()
    aliases = {
        "knowledge": "approved_knowledge",
        "memory": "personal_memory",
        "session": "current_session_claim",
        "claim": "current_session_claim",
    }
    return aliases.get(supplied, supplied)


def _update_subject(payload: dict[str, Any]) -> str:
    supplied = str(
        payload.get("update_subject") or payload.get("claim_owner") or "unspecified"
    ).strip().lower()
    aliases = {
        "user": "aleks",
        "assistant": "selene",
        "shared": "shared_model",
        "either": "shared_model",
    }
    subject = aliases.get(supplied, supplied)
    if subject not in UPDATE_SUBJECTS:
        raise ValueError(f"unsupported epistemic update subject: {subject}")
    return subject


def _disposition(kind: str, owner_locked: bool) -> str:
    if owner_locked:
        return "defer_to_core_mind"
    return {
        "": "no_update",
        "correction": "apply_affected_update_and_continue",
        "refinement": "apply_narrow_refinement",
        "scope_restriction": "retain_with_narrower_scope",
        "extension": "add_without_erasing_supported_base",
        "competing_explanation": "compare_without_premature_replacement",
        "unresolved_contradiction": "hold_contradiction_visible",
        "replacement": "replace_affected_claim_preserve_ancestry",
        "reopening": "reopen_affected_model_once",
    }[kind]


def _validity(kind: str, owner_locked: bool) -> str:
    if owner_locked:
        return "unchanged_owner_controls"
    return {
        "": "unchanged",
        "correction": "affected_claim_updated",
        "refinement": "earlier_claim_retained_with_precision",
        "scope_restriction": "earlier_claim_valid_only_in_stated_scope",
        "extension": "earlier_claim_retained_with_addition",
        "competing_explanation": "multiple_live_candidates",
        "unresolved_contradiction": "conflict_unresolved",
        "replacement": "earlier_claim_superseded_for_current_scope",
        "reopening": "prior_conclusion_provisional_pending_recheck",
    }[kind]


def _preserved_structure(kind: str, prior_claim: str, owner_locked: bool) -> dict[str, Any]:
    mode = {
        "": "no_change",
        "correction": "preserve_unaffected_context",
        "refinement": "preserve_base_claim_and_add_precision",
        "scope_restriction": "preserve_claim_inside_valid_scope",
        "extension": "preserve_supported_base",
        "competing_explanation": "preserve_both_candidate_explanations",
        "unresolved_contradiction": "preserve_observations_without_forced_resolution",
        "replacement": "preserve_ancestry_not_current_validity",
        "reopening": "preserve_observations_and_still_fitting_assumptions",
    }[kind]
    return {
        "mode": "owner_lock_preserves_current_state" if owner_locked else mode,
        "prior_claim_available": bool(prior_claim),
        "unaffected_structure_may_remain": True,
        "full_context_reset_required": False,
        "useful_superseded_structure_deleted": False,
    }


def _dependencies(payload: dict[str, Any], kind: str, target: str) -> dict[str, Any]:
    supplied = _text_list(payload.get("dependent_claims"), width=700, limit=12)
    needed = kind in {
        "correction",
        "scope_restriction",
        "replacement",
        "reopening",
        "unresolved_contradiction",
    }
    return {
        "required": needed,
        "target": target if needed else "",
        "known_dependents": supplied,
        "unknown_dependents_remain_visible": needed and not bool(supplied),
        "maximum_recheck_passes_without_new_material": 1,
        "unrelated_claims_rechecked": False,
    }


def _ancestry(kind: str, prior: str, revised: str, scope: str) -> dict[str, Any]:
    preserved = bool(kind)
    return {
        "preserved": preserved,
        "prior_model": prior if preserved else "",
        "current_model": revised if preserved else "",
        "valid_scope": scope,
        "prior_model_erased": False,
        "prior_model_treated_as_current": False if kind in {"replacement", "reopening"} else None,
    }


def _response_obligations(kind: str, disposition: str) -> list[str]:
    if not kind:
        return []
    obligations = [
        "name the affected claim or scope",
        "state what remains valid",
        "apply only the warranted update",
    ]
    if kind == "competing_explanation":
        obligations.append("compare candidates under the same evidence")
    if kind == "unresolved_contradiction":
        obligations.append("leave the unresolved conflict visible")
    if kind in {"replacement", "scope_restriction", "reopening"}:
        obligations.append("preserve model ancestry and valid scope")
    if disposition == "reopen_affected_model_once":
        obligations.append("recheck dependent conclusions once")
    return obligations


def _text_list(value: Any, *, width: int, limit: int) -> list[str]:
    if isinstance(value, list):
        values = value
    elif value in (None, ""):
        values = []
    else:
        values = [value]
    return list(
        dict.fromkeys(
            truncate(str(item).strip(), width)
            for item in values
            if item is not None and str(item).strip()
        )
    )[:limit]


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
