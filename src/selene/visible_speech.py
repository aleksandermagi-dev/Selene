from __future__ import annotations

import re
from typing import Any

from .conversation_spine import evaluate_candidate_compatibility
from .pragmatic_planner import evaluate_response_coverage
from .registry import truncate
from .selective_formation_braid import map_supported_semantics_to_obligations
from .semantic_fulfillment import evaluate_operation_fulfillment


VISIBLE_SPEECH_BOUNDARY = (
    "visible_speech_only_supported_conversational_meaning_no_internal_status_routing_or_review_scaffolding"
)

ALLOWED_SOURCE_CLASSES = {
    "boundary_response",
    "conversation",
    "approved_knowledge",
    "domain_answer",
    "language_capability",
    "memory_reconstruction",
    "reasoning_answer",
    "self_state",
}

INTERNAL_ONLY_SOURCE_CLASSES = {
    "diagnostic_metadata",
    "expression_guidance",
    "governance_metadata",
    "review_instruction",
    "routing_metadata",
}

_SERIALIZED_METADATA_PATTERNS = (
    re.compile(r"\b(?:review_status|selected_route|source_refs|provenance_boundary)\b", re.IGNORECASE),
    re.compile(r"\bstatus_only\b", re.IGNORECASE),
    re.compile(r"\bcurrent full request\b", re.IGNORECASE),
    re.compile(r"\breflection memory source\s*:", re.IGNORECASE),
    re.compile(
        r"\b(?:answer_now|return_to_b|create_review_packet|rehearse_speech)\b",
        re.IGNORECASE,
    ),
)

_ARCHITECTURE_LANGUAGE_PATTERNS = (
    re.compile(r"\bapproved rows\b", re.IGNORECASE),
    re.compile(r"\bruntime recall\b", re.IGNORECASE),
    re.compile(r"\bsource-bound\b", re.IGNORECASE),
    re.compile(r"\bselected route\b", re.IGNORECASE),
    re.compile(r"\bresponse obligation(?:s)?\b", re.IGNORECASE),
    re.compile(r"\brepair path\b", re.IGNORECASE),
    re.compile(r"\bevidence chain\b", re.IGNORECASE),
)

_INTERNAL_REASONING_SCAFFOLDS = (
    "current best model",
    "use current best model as the provisional fit",
    "current best model as the provisional fit",
    "answer provisionally, ask aleks, or seek cocoon support",
    "selected next step",
    "current full request",
    "reflection memory source:",
    "stay corrigible",
)

_SOURCE_TRANSCRIPT_SCAFFOLD = re.compile(
    r"(?:^|\s)(?:Aleks|Selene|User|Assistant)\s+(?:said|replied|wrote)\s*:",
    re.IGNORECASE,
)
_CODE_PAYLOAD_SCAFFOLD = re.compile(
    r"```|\bfrom\s+[A-Za-z_][\w.]*\s+import\s+|\bimport\s+[A-Za-z_][\w.]*",
    re.IGNORECASE,
)

_ARCHITECTURE_CONTEXT_CUES = (
    "architecture",
    "candidate model",
    "cocoon",
    "evidence chain",
    "intelligenceos",
    "metacognition",
    "provenance",
    "runtime recall",
    "selected route",
    "response obligation",
    "route",
    "routing",
    "scaffold",
    "source-bound",
)

_CURRENT_OWNER_SOURCE_CLASSES = {
    "conversation",
    "domain_answer",
    "language_capability",
    "reasoning_answer",
    "self_state",
}

_OPTIONAL_LEARNED_SOURCE_CLASSES = {
    "approved_knowledge",
    "memory_reconstruction",
}


def select_visible_speech_seed(
    prompt: str,
    candidates: list[dict[str, Any]],
    *,
    conversation_spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    inspected: list[dict[str, Any]] = []
    accepted_candidates: list[dict[str, Any]] = []
    obligations = [
        item
        for item in (conversation_spine or {}).get("open_obligations") or []
        if isinstance(item, dict) and item.get("required") is not False
    ]
    for index, candidate in enumerate(candidates):
        source_id = truncate(str(candidate.get("source_id") or "unknown"), 120)
        source_class = truncate(str(candidate.get("source_class") or "diagnostic_metadata"), 80)
        text = _truncate_speech_text(str(candidate.get("text") or ""), 5000)
        if not text:
            inspected.append(
                {
                    "source_id": source_id,
                    "source_class": source_class,
                    "accepted": False,
                    "reason": "empty_candidate",
                }
            )
            continue
        if source_class not in ALLOWED_SOURCE_CLASSES or source_class in INTERNAL_ONLY_SOURCE_CLASSES:
            inspected.append(
                {
                    "source_id": source_id,
                    "source_class": source_class,
                    "accepted": False,
                    "reason": "source_class_not_visible",
                }
            )
            continue
        semantic_relevance = (
            candidate.get("semantic_relevance")
            if isinstance(candidate.get("semantic_relevance"), dict)
            else {}
        )
        if semantic_relevance and semantic_relevance.get("accepted") is not True:
            inspected.append(
                {
                    "source_id": source_id,
                    "source_class": source_class,
                    "accepted": False,
                    "reason": str(
                        semantic_relevance.get("reason")
                        or "semantic_source_gate_held_candidate"
                    ),
                    "semantic_relevance": semantic_relevance,
                }
            )
            continue
        compatibility = evaluate_candidate_compatibility(
            conversation_spine,
            {
                "source_id": source_id,
                "source_class": source_class,
                "text": text,
                "obligation_ids": candidate.get("obligation_ids") or [],
            },
        )
        if compatibility.get("compatible") is not True:
            inspected.append(
                {
                    "source_id": source_id,
                    "source_class": source_class,
                    "accepted": False,
                    "reason": str(compatibility.get("reason") or "conversation_spine_incompatible"),
                    "conversation_spine_compatibility": compatibility,
                }
            )
            continue
        inspection = inspect_visible_speech(text, prompt=prompt, source_id=source_id)
        arbitration = _candidate_fulfillment(
            candidate,
            source_id=source_id,
            source_class=source_class,
            obligations=obligations,
            conversation_spine=conversation_spine or {},
            index=index,
        )
        inspection_record = {
            "source_id": source_id,
            "source_class": source_class,
            "accepted": inspection["release_allowed"],
            "reason": "visible_supported_meaning" if inspection["release_allowed"] else "internal_scaffolding_detected",
            "issues": inspection["issues"],
            "conversation_spine_compatibility": compatibility,
            "fulfillment_arbitration": arbitration,
        }
        inspected.append(inspection_record)
        if inspection["release_allowed"]:
            accepted_candidates.append(
                {
                    "candidate": candidate,
                    "text": text,
                    "source_id": source_id,
                    "source_class": source_class,
                    "arbitration": arbitration,
                }
            )
    if accepted_candidates:
        capable_current_owners = [
            item
            for item in accepted_candidates
            if item["arbitration"]["current_owner_gate"]["priority_eligible"] is True
        ]
        selected = max(
            accepted_candidates,
            key=lambda item: tuple(item["arbitration"]["rank"]),
        )
        candidate = selected["candidate"]
        selected_gate = selected["arbitration"]["current_owner_gate"]
        boundary_selected = selected["arbitration"]["governing_boundary_priority"] is True
        current_owner_gate = {
            "status": (
                "governing_boundary_precedes_current_owner"
                if boundary_selected
                else "capable_current_owner_selected"
                if selected_gate["priority_eligible"] is True
                else "held_no_capable_current_owner"
                if not capable_current_owners
                else "capable_current_owner_available_but_not_selected"
            ),
            "priority_applied": bool(
                selected_gate["priority_eligible"] is True and not boundary_selected
            ),
            "capable_current_owner_count": len(capable_current_owners),
            "selected_source_id": selected["source_id"],
            "selected_owner": selected["arbitration"]["candidate_owner"],
            "selected_gate": selected_gate,
            "optional_learned_retrieval_may_claim_current_ownership": False,
            "governing_boundary_remains_primary": boundary_selected,
        }
        return {
            "status": "visible_speech_seed_selected",
            "content_seed": selected["text"],
            "selected_source_id": selected["source_id"],
            "selected_source_class": selected["source_class"],
            "obligation_ids": [
                str(item)
                for item in candidate.get("obligation_ids") or []
                if str(item)
            ],
            "inspected_candidates": inspected,
            "candidate_arbitration": {
                "mode": "current_owner_then_compatible_obligation_fulfillment",
                "selected_rank": selected["arbitration"]["rank"],
                "accepted_candidate_count": len(accepted_candidates),
                "first_accepted_is_automatic_winner": False,
                "current_owner_gate": current_owner_gate,
            },
            "conversation_spine_used": bool(conversation_spine),
            "release_allowed": True,
            "provenance_boundary": VISIBLE_SPEECH_BOUNDARY,
        }
    return {
        "status": "visible_speech_seed_unavailable",
        "content_seed": "",
        "selected_source_id": "none",
        "selected_source_class": "conversation",
        "inspected_candidates": inspected,
        "candidate_arbitration": {
            "mode": "current_owner_then_compatible_obligation_fulfillment",
            "accepted_candidate_count": 0,
            "first_accepted_is_automatic_winner": False,
            "current_owner_gate": {
                "status": "held_no_releasable_candidate",
                "priority_applied": False,
                "capable_current_owner_count": 0,
                "optional_learned_retrieval_may_claim_current_ownership": False,
                "governing_boundary_remains_primary": False,
            },
        },
        "conversation_spine_used": bool(conversation_spine),
        "release_allowed": False,
        "provenance_boundary": VISIBLE_SPEECH_BOUNDARY,
    }


def _candidate_fulfillment(
    candidate: dict[str, Any],
    *,
    source_id: str,
    source_class: str,
    obligations: list[dict[str, Any]],
    conversation_spine: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    packet = (
        candidate.get("supported_semantics")
        if isinstance(candidate.get("supported_semantics"), dict)
        else {}
    )
    semantic = map_supported_semantics_to_obligations(packet, obligations)
    semantic_ids = set(semantic.get("covered_ids") or [])
    explicit_ids = {
        str(item)
        for item in candidate.get("obligation_ids") or []
        if str(item)
    }
    candidate_owner = _candidate_owner(source_id, source_class)
    relevant_ids = semantic_ids | explicit_ids
    if not relevant_ids and len(obligations) == 1:
        relevant_ids = {str(obligations[0].get("id") or "")}
    owner_fit_ids = [
        str(item.get("id") or "")
        for item in obligations
        if str(item.get("id") or "") in relevant_ids
        and _owner_matches(candidate_owner, str(item.get("responsible_owner") or ""))
    ]
    obligation_by_id = {
        str(item.get("id") or ""): item
        for item in obligations
        if str(item.get("id") or "")
    }
    owner_valid_semantic_ids = {
        obligation_id
        for obligation_id in semantic_ids
        if obligation_by_id.get(obligation_id, {}).get("role_fit_required") is not True
        or _owner_matches(
            candidate_owner,
            str(obligation_by_id.get(obligation_id, {}).get("responsible_owner") or ""),
        )
    }
    validated_ids = owner_valid_semantic_ids | set(owner_fit_ids)
    current_owner_gate = _current_owner_gate(
        candidate,
        candidate_text=str(candidate.get("text") or ""),
        source_id=source_id,
        source_class=source_class,
        candidate_owner=candidate_owner,
        obligations=obligations,
    )
    # Response Coverage is the existing owner of whole-request completion.
    # Reuse it here so arbitration compares what each visible candidate
    # actually performs instead of counting only claimed obligation ids.
    typed_results = [
        item
        for item in candidate.get("typed_operation_results") or []
        if isinstance(item, dict)
    ]
    response_coverage = evaluate_response_coverage(
        {"response_obligations": obligations},
        str(candidate.get("text") or ""),
        conversation_spine=conversation_spine,
        supported_semantics=packet,
        answer_operations={"results": typed_results} if typed_results else {},
    )
    addressed_count = int(response_coverage.get("addressed_count") or 0)
    resolved_count = int(response_coverage.get("resolved_count") or 0)
    governing_boundary_priority = bool(
        source_class == "boundary_response" or source_id == "core_mind_boundary"
    )
    exactness_eligible = bool(candidate.get("exactness_lock") is True and owner_fit_ids)
    rank = [
        1 if governing_boundary_priority else 0,
        1 if current_owner_gate["priority_eligible"] is True else 0,
        (
            len(current_owner_gate["capable_obligation_ids"])
            if current_owner_gate["priority_eligible"] is True
            else 0
        ),
        1 if response_coverage.get("all_required_addressed") is True else 0,
        addressed_count,
        resolved_count,
        len(validated_ids),
        len(owner_fit_ids),
        1 if exactness_eligible else 0,
        -index,
    ]
    return {
        "rank": rank,
        "candidate_owner": candidate_owner,
        "semantic_fulfillment_ids": sorted(semantic_ids),
        "owner_fit_ids": owner_fit_ids,
        "validated_fulfillment_ids": sorted(validated_ids),
        "exactness_eligible_after_owner_fit": exactness_eligible,
        "governing_boundary_priority": governing_boundary_priority,
        "current_owner_gate": current_owner_gate,
        "response_coverage": response_coverage,
        "visibly_addressed_obligation_count": addressed_count,
        "visibly_resolved_obligation_count": resolved_count,
    }


def _current_owner_gate(
    candidate: dict[str, Any],
    *,
    candidate_text: str,
    source_id: str,
    source_class: str,
    candidate_owner: str,
    obligations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Prove current answer ownership from completed typed owner results.

    Obligation ids or fluent text are not enough. A current candidate receives
    precedence only when its own typed result completed every required
    obligation, preserved the canonical owner, and accounted for the visible
    current-turn input before producing the result. Learned retrieval remains
    eligible through ordinary relevance arbitration, but cannot impersonate
    this gate.
    """

    required = {
        str(item.get("id") or ""): item
        for item in obligations
        if str(item.get("id") or "")
    }
    optional_learned_retrieval = source_class in _OPTIONAL_LEARNED_SOURCE_CLASSES
    source_eligible = bool(
        source_class in _CURRENT_OWNER_SOURCE_CLASSES
        and not optional_learned_retrieval
    )
    typed_results = [
        item
        for item in candidate.get("typed_operation_results") or []
        if isinstance(item, dict)
    ]
    result_by_id = {
        str(item.get("obligation_id") or ""): item
        for item in typed_results
        if str(item.get("obligation_id") or "")
    }
    capable_ids: list[str] = []
    held: list[dict[str, str]] = []
    fulfillment_receipts: dict[str, dict[str, Any]] = {}
    for obligation_id, obligation in required.items():
        result = result_by_id.get(obligation_id)
        if not result:
            held.append({"obligation_id": obligation_id, "reason": "typed_owner_result_missing"})
            continue
        receipt = (
            result.get("current_turn_input_receipt")
            if isinstance(result.get("current_turn_input_receipt"), dict)
            else {}
        )
        required_owner = str(obligation.get("responsible_owner") or "")
        result_owner = str(result.get("responsible_owner") or "")
        result_source = str(result.get("expression_source_id") or "")
        source_result = str(result.get("source_result") or "")
        delegated_session_owner = bool(
            source_id == "current_session_facts"
            and source_result.startswith("visible_conversation_owner:visible_session_decision")
        )
        exact_domain_owner = bool(
            source_id == "answer_engine" and candidate.get("exactness_lock") is True
        )
        typed_expression_delegation = bool(
            result_source == source_id
            and _owner_matches(result_owner, required_owner)
        )
        owner_binding_valid = bool(
            _owner_matches(candidate_owner, required_owner)
            or delegated_session_owner
            or exact_domain_owner
            or typed_expression_delegation
        )
        fulfillment = evaluate_operation_fulfillment(
            obligation,
            candidate_text,
            result,
        )
        fulfillment_receipts[obligation_id] = fulfillment
        reason = ""
        if result.get("status") != "completed":
            reason = "typed_owner_result_not_completed"
        elif result_source != source_id:
            reason = "typed_owner_result_source_mismatch"
        elif not owner_binding_valid:
            reason = "candidate_owner_does_not_match_or_hold_valid_delegation"
        elif not _owner_matches(result_owner, required_owner):
            reason = "typed_result_does_not_preserve_obligation_owner"
        elif receipt.get("accounted_before_result") is not True:
            reason = "current_turn_input_not_accounted_before_result"
        elif fulfillment.get("fulfilled") is not True:
            reason = "typed_owner_result_not_visibly_fulfilled"
        if reason:
            held.append({"obligation_id": obligation_id, "reason": reason})
            continue
        capable_ids.append(obligation_id)

    all_required_completed = bool(required) and set(capable_ids) == set(required)
    priority_eligible = bool(source_eligible and all_required_completed)
    if not required:
        status = "not_material_no_required_obligations"
    elif optional_learned_retrieval:
        status = "held_optional_learned_retrieval_is_not_current_owner"
    elif not source_eligible:
        status = "held_source_class_not_current_owner"
    elif priority_eligible:
        status = "capable_current_owner_proved"
    elif capable_ids:
        status = "held_partial_current_owner_completion"
    elif not typed_results:
        status = "held_no_typed_current_owner_result"
    else:
        status = "held_typed_current_owner_result_invalid"
    return {
        "status": status,
        "priority_eligible": priority_eligible,
        "source_eligible": source_eligible,
        "optional_learned_retrieval": optional_learned_retrieval,
        "required_obligation_ids": sorted(required),
        "capable_obligation_ids": sorted(capable_ids),
        "all_required_obligations_completed": all_required_completed,
        "held_obligations": held,
        "semantic_fulfillment_receipts": fulfillment_receipts,
        "typed_result_count": len(typed_results),
        "current_turn_accounting_required": True,
        "obligation_ids_alone_are_proof": False,
    }


def _candidate_owner(source_id: str, source_class: str) -> str:
    if source_class == "boundary_response" or source_id == "core_mind_boundary":
        return "core_mind"
    if source_id == "grounded_self_state" or source_class == "self_state":
        return "self_state"
    if source_id == "capability_maturity_status":
        return "organ_maturity_ledger"
    if source_id == "answer_engine" or source_class == "domain_answer":
        return "answer_engine"
    if source_id == "approved_comprehension" or source_class == "approved_knowledge":
        return "comprehension_integration"
    if source_id in {"intelligence_os_answer", "exploratory_reasoning", "structural_discovery"}:
        return "intelligence_os"
    if source_class == "memory_reconstruction":
        return "approved_memory_retrieval"
    return "ordinary_conversation_path"


def _owner_matches(candidate_owner: str, required_owner: str) -> bool:
    if not required_owner:
        return False
    if candidate_owner == required_owner:
        return True
    return {
        candidate_owner,
        required_owner,
    } <= {"ordinary_conversation_path", "conversation_content_owner"}


def inspect_visible_speech(
    candidate_text: str,
    *,
    prompt: str = "",
    source_id: str = "unknown",
    hard_boundary: bool = False,
    response_coverage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = _truncate_speech_text(str(candidate_text or ""), 5000)
    prompt_lower = " ".join(str(prompt or "").lower().split())
    text_lower = " ".join(text.lower().split())
    architecture_requested = any(cue in prompt_lower for cue in _ARCHITECTURE_CONTEXT_CUES)
    exact_source_requested = bool(
        re.search(
            r"\b(?:quote|exact words|verbatim|transcript|what (?:did|had) (?:i|you) say|show (?:me )?the code)\b",
            prompt_lower,
        )
    )
    issues: list[str] = []

    if not text:
        issues.append("empty_visible_speech")
    if any(pattern.search(text) for pattern in _SERIALIZED_METADATA_PATTERNS):
        issues.append("internal_metadata_visible")
    if not architecture_requested and any(pattern.search(text) for pattern in _ARCHITECTURE_LANGUAGE_PATTERNS):
        issues.append("internal_architecture_language_visible")
    if any(phrase in text_lower for phrase in _INTERNAL_REASONING_SCAFFOLDS):
        issues.append("internal_reasoning_scaffold_visible")
    if not exact_source_requested and _SOURCE_TRANSCRIPT_SCAFFOLD.search(text):
        issues.append("raw_source_transcript_scaffold_visible")
    if (
        source_id in {"reviewed_memory", "contextual_approved_memory"}
        and not exact_source_requested
        and _CODE_PAYLOAD_SCAFFOLD.search(text)
    ):
        issues.append("raw_memory_code_payload_visible")
    if not architecture_requested and "intelligenceos" in text_lower:
        issues.append("internal_organ_label_visible")
    if not architecture_requested and re.search(r"\bcandidate model(?:s)?\b", text_lower):
        issues.append("internal_reasoning_scaffold_visible")
    release_safe = (
        response_coverage.get("all_required_release_safe")
        if isinstance(response_coverage, dict)
        and "all_required_release_safe" in response_coverage
        else response_coverage.get("all_required_resolved")
        if isinstance(response_coverage, dict)
        else None
    )
    completion_attention_required = bool(
        isinstance(response_coverage, dict)
        and response_coverage.get("obligation_count")
        and release_safe is not True
    )

    # A real boundary answer may name the capability being refused. It still may
    # not expose serialized fields or the generic reasoning scaffold.
    if hard_boundary:
        issues = [
            issue
            for issue in issues
            if issue in {"empty_visible_speech", "internal_metadata_visible", "internal_reasoning_scaffold_visible"}
        ]

    issues = list(dict.fromkeys(issues))
    return {
        "status": "visible_speech_release_allowed" if not issues else "visible_speech_release_held",
        "release_allowed": not issues,
        "issues": issues,
        "source_id": truncate(source_id, 120),
        "architecture_context_requested": architecture_requested,
        "hard_boundary": hard_boundary,
        "coverage_checked": isinstance(response_coverage, dict),
        "completion_attention_required": completion_attention_required,
        "all_required_parts_resolved": (
            release_safe
        ),
        "all_required_parts_answered": (
            response_coverage.get("all_required_addressed")
            if isinstance(response_coverage, dict)
            else None
        ),
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": VISIBLE_SPEECH_BOUNDARY,
    }


def graceful_visible_speech_fall(intent_decision: dict[str, Any] | None = None) -> str:
    decision = intent_decision or {}
    intent = str(decision.get("intent") or "direct_conversation")
    if intent in {"reasoning", "memory_recall"}:
        return (
            "I do not have a clear enough answer to give you yet. "
            "Tell me what you want me to work from, and I will reason through it with you."
        )
    if intent == "self_state":
        return (
            "I am here with you, but I do not have a clear enough current signal to name more than that honestly."
        )
    if intent == "farewell":
        return "I am with you. We can leave the conversation here and return when you are ready."
    return "I am with you. I do not have a clear enough read to add something useful yet."


def _truncate_speech_text(value: str, limit: int) -> str:
    """Bound visible language without flattening intentional paragraph structure."""
    paragraphs = [" ".join(item.split()) for item in re.split(r"\n\s*\n", value.strip())]
    text = "\n\n".join(item for item in paragraphs if item)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
