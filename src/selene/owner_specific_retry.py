from __future__ import annotations

import re
from typing import Any

from .conversation_spine import evaluate_candidate_compatibility
from .registry import truncate


OWNER_SPECIFIC_RETRY_BOUNDARY = (
    "one_current_turn_owner_obligation_retry_only_no_new_fact_generation_memory_"
    "identity_personality_governance_training_authority_or_action_change"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "raw_a_import_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "hidden_chain_of_thought_exposed": False,
}

_GENERIC_FALLBACK_MARKERS = (
    "do not have enough grounded detail",
    "do not have a grounded factual answer",
    "cannot answer that part reliably",
    "cannot answer that with a reliable yes or no",
    "would need an attributed fact",
    "without guessing",
    "support for this requested part",
)


def attempt_owner_specific_retry(
    candidate: str,
    coverage: dict[str, Any] | None,
    *,
    requested: bool,
    hard_boundary: bool,
    feedback_handoff: dict[str, Any] | None = None,
    owner_outputs: list[dict[str, Any]] | None = None,
    conversation_spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attempt one current-turn completion from the exact obligation owner.

    This function cannot invoke an organ or generate answer content.  It may
    only select a novel fragment that an already-run owner supplied for the
    named unresolved obligation.
    """

    coverage = coverage or {}
    handoff = feedback_handoff or {}
    target_id = str(handoff.get("target_obligation_id") or "")
    owner = str(handoff.get("responsible_owner") or "")
    base = {
        "status": "owner_specific_retry_not_needed",
        "requested_by_metacognition": requested,
        "attempted": False,
        "accepted": False,
        "count": 0,
        "maximum_count": 1,
        "recursion_allowed": False,
        "content_generation_allowed": False,
        "hard_boundary_respected": True,
        "candidate_text": candidate,
        "unresolved_before": int(coverage.get("unresolved_count") or 0),
        "responsible_owner": owner,
        "target_obligation_id": target_id,
        "target_missing_state": str(handoff.get("target_missing_state") or ""),
        "target_missing_ground": str(handoff.get("target_missing_ground") or ""),
        "owner_invoked": False,
        "existing_current_turn_output_only": True,
        "provenance_boundary": OWNER_SPECIFIC_RETRY_BOUNDARY,
        **GUARDS,
    }
    if hard_boundary:
        return {**base, "status": "owner_specific_retry_blocked_by_core_mind"}
    if not requested:
        return base
    if not owner or owner in {"none", "core_mind", "source_evidence_owner"}:
        return {**base, "status": "owner_specific_retry_has_no_content_owner"}
    if not target_id:
        return {**base, "status": "owner_specific_retry_has_no_exact_obligation"}

    matching = [
        item
        for item in owner_outputs or []
        if isinstance(item, dict)
        and str(item.get("owner") or "") == owner
        and target_id
        in {
            str(obligation_id)
            for obligation_id in item.get("obligation_ids") or []
            if str(obligation_id)
        }
    ]
    if not matching:
        return {**base, "status": "owner_specific_retry_owner_has_no_current_turn_output"}

    for output in matching:
        fragment = _novel_supported_fragment(
            candidate,
            str(output.get("text") or ""),
        )
        if not fragment:
            continue
        source_id = str(output.get("source_id") or owner)
        source_class = str(output.get("source_class") or "conversation")
        compatibility = evaluate_candidate_compatibility(
            conversation_spine,
            {
                "source_id": source_id,
                "source_class": source_class,
                "text": fragment,
                "obligation_ids": [target_id],
            },
        )
        if compatibility.get("compatible") is not True:
            continue
        joined = f"{candidate.rstrip()}\n\n{fragment}" if candidate.strip() else fragment
        return {
            **base,
            "status": "owner_specific_retry_attempted",
            "attempted": True,
            "count": 1,
            "candidate_text": truncate(joined, 5000),
            "selected_fragment": fragment,
            "source": "existing_exact_owner_current_turn_output",
            "source_id": source_id,
            "source_class": source_class,
            "conversation_spine_compatibility": compatibility,
        }

    return {
        **base,
        "status": "owner_specific_retry_has_no_novel_supported_fragment",
    }


def apply_owner_retry_to_composition(
    composition: dict[str, Any] | None,
    retry: dict[str, Any] | None,
) -> dict[str, Any]:
    """Reflect an accepted retry in the visible epistemic audit packet."""

    result = dict(composition or {})
    retry = retry or {}
    if retry.get("accepted") is not True:
        return result
    target_id = str(retry.get("target_obligation_id") or "")
    fragment = truncate(str(retry.get("selected_fragment") or "").strip(), 1800)
    if not target_id or not fragment:
        return result
    source_id = str(retry.get("source_id") or "")
    source_class = str(retry.get("source_class") or "conversation")
    state = (
        "supported_answer"
        if source_class in {"approved_knowledge", "domain_answer"}
        else "reviewed_experience_recall"
        if source_class == "memory_reconstruction"
        else "supported_inference"
    )
    parts = []
    changed = False
    for raw in result.get("parts") or []:
        if not isinstance(raw, dict):
            continue
        part = dict(raw)
        if str(part.get("obligation_id") or "") == target_id:
            part.update(
                {
                    "epistemic_state": state,
                    "certainty": (
                        "supported"
                        if state == "supported_answer"
                        else "reviewed_personal_scope"
                        if state == "reviewed_experience_recall"
                        else "provisional_from_supported_premises"
                    ),
                    "text": fragment,
                    "addressed": True,
                    "unsupported": False,
                    "missing_ground": "",
                    "source_id": source_id,
                    "source_class": source_class,
                    "visible_label_required": False,
                    "visible_label_present": True,
                    "completed_by_owner_specific_retry": True,
                }
            )
            changed = True
        parts.append(part)
    if not changed:
        return result
    states = list(
        dict.fromkeys(str(item.get("epistemic_state") or "") for item in parts)
    )
    supported_states = {
        "supported_answer",
        "supported_inference",
        "bounded_prediction",
        "open_hypothesis",
        "labeled_speculation",
        "reviewed_experience_recall",
    }
    supported_count = sum(
        1 for item in parts if item.get("epistemic_state") in supported_states
    )
    missing_count = sum(
        1 for item in parts if item.get("epistemic_state") == "missing_ground"
    )
    dominant_state = (
        "partial_answer"
        if supported_count and missing_count
        else states[0]
        if len(states) == 1
        else "mixed_epistemic_answer"
        if states
        else str(result.get("dominant_state") or "missing_ground")
    )
    return {
        **result,
        "status": "epistemic_answer_composed_after_owner_specific_retry",
        "content_seed": str(retry.get("candidate_text") or result.get("content_seed") or ""),
        "parts": parts,
        "supported_part_count": supported_count,
        "missing_part_count": missing_count,
        "epistemic_states_present": states,
        "dominant_state": dominant_state,
        "mixed_epistemic_answer": len(states) > 1,
        "known_part_preserved_with_missing_part": bool(supported_count and missing_count),
        "owner_specific_retry_applied": True,
        "owner_specific_retry_target_obligation_id": target_id,
        "unknown_part_downgraded_supported_part": False,
        **GUARDS,
    }


def _novel_supported_fragment(candidate: str, supplied: str) -> str:
    supplied = truncate(str(supplied or "").strip(), 3000)
    if not supplied:
        return ""
    candidate_surface = _surface(candidate)
    fragments = [
        part.strip()
        for part in re.split(r"\n\s*\n+", supplied)
        if part.strip()
    ]
    if len(fragments) == 1:
        sentence_fragments = [
            part.strip()
            for part in re.split(r"(?<=[.!?])\s+", fragments[0])
            if part.strip()
        ]
        if len(sentence_fragments) > 1:
            fragments = sentence_fragments
    novel = []
    for fragment in fragments:
        surface = _surface(fragment)
        if not surface or surface in candidate_surface:
            continue
        if _generic_fallback_only(fragment):
            continue
        novel.append(fragment)
    return truncate(" ".join(novel), 1800).strip()


def _generic_fallback_only(text: str) -> bool:
    surface = _surface(text)
    return any(marker in surface for marker in _GENERIC_FALLBACK_MARKERS)


def _surface(value: str) -> str:
    return " ".join(str(value or "").lower().split())
