from __future__ import annotations

import re
from typing import Any


SEMANTIC_FULFILLMENT_BOUNDARY = (
    "current_visible_answer_operation_fulfillment_receipts_only_no_content_generation_"
    "expression_memory_identity_personality_governance_authority_training_or_action_change"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "expression_authority": False,
}

_GENERIC_MISSING_MARKERS = (
    "i cannot",
    "i can't",
    "i do not know",
    "i don't know",
    "i do not have enough",
    "i don't have enough",
    "i need",
    "i would need",
    "i'd need",
    "i am missing",
    "i'm missing",
    "not enough evidence",
    "not enough information",
    "remains open",
)

_ROUTE_MARKERS = (
    "i need",
    "i would need",
    "i'd need",
    "if you give me",
    "if you can give me",
    "what would help",
    "the next useful check",
    "the smallest useful check",
)

_STOP = {
    "a", "an", "and", "are", "as", "at", "be", "because", "by", "can", "could",
    "current", "for", "from", "has", "have", "how", "if", "in", "is", "it", "may",
    "of", "on", "or", "should", "that", "the", "their", "then", "this", "to", "was",
    "what", "when", "where", "which", "with", "would", "you", "your",
}


def semantic_fulfillment_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "semantic_fulfillment_receipts_ready",
            "version": "v1_typed_operation_visible_fulfillment",
            "obligation_ids_are_proof": False,
            "generic_missing_statement_is_answer": False,
            "typed_owner_result_required_for_typed_operation": True,
            "visible_realization_required": True,
            "review_status": "status_only",
            "provenance_boundary": SEMANTIC_FULFILLMENT_BOUNDARY,
        }
    )


def build_semantic_fulfillment_packet(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    spine = payload.get("conversation_spine") if isinstance(payload.get("conversation_spine"), dict) else {}
    ledger = spine.get("obligation_ledger") if isinstance(spine.get("obligation_ledger"), dict) else {}
    obligations = [
        item
        for item in (
            payload.get("response_obligations")
            or ledger.get("obligations")
            or spine.get("open_obligations")
            or []
        )
        if isinstance(item, dict)
    ]
    operations = payload.get("answer_operations") if isinstance(payload.get("answer_operations"), dict) else {}
    results = {
        str(item.get("obligation_id") or ""): item
        for item in operations.get("results") or []
        if isinstance(item, dict) and str(item.get("obligation_id") or "")
    }
    candidate = str(payload.get("candidate_text") or "")
    receipts = [
        evaluate_operation_fulfillment(
            obligation,
            candidate,
            results.get(str(obligation.get("id") or "")),
        )
        for obligation in obligations
        if str(obligation.get("id") or "") in results
    ]
    fulfilled = sum(1 for item in receipts if item.get("fulfilled") is True)
    release_resolved = sum(1 for item in receipts if item.get("resolved_for_release") is True)
    return _with_guards(
        {
            "status": (
                "semantic_fulfillment_complete"
                if receipts and fulfilled == len(receipts)
                else "semantic_fulfillment_release_resolved"
                if receipts and release_resolved == len(receipts)
                else "semantic_fulfillment_incomplete"
                if receipts
                else "semantic_fulfillment_not_material"
            ),
            "version": "v1_typed_operation_visible_fulfillment",
            "receipt_count": len(receipts),
            "fulfilled_count": fulfilled,
            "release_resolved_count": release_resolved,
            "all_operations_visibly_fulfilled": bool(receipts and fulfilled == len(receipts)),
            "all_operations_release_resolved": bool(
                receipts and release_resolved == len(receipts)
            ),
            "receipts": receipts,
            "obligation_ids_are_proof": False,
            "generic_missing_statement_is_answer": False,
            "review_status": "status_only",
            "provenance_boundary": SEMANTIC_FULFILLMENT_BOUNDARY,
        }
    )


def evaluate_operation_fulfillment(
    obligation: dict[str, Any] | None,
    candidate_text: str,
    operation_result: dict[str, Any] | None,
) -> dict[str, Any]:
    """Verify that one visible answer performs one typed owner operation.

    A completed owner result proves that supported substance exists. It does
    not prove that NLO/Voice actually expressed the operation. Conversely, a
    visible missing-input statement can be an honest release state without
    becoming the requested answer.
    """

    obligation = obligation if isinstance(obligation, dict) else {}
    result = operation_result if isinstance(operation_result, dict) else {}
    obligation_id = str(obligation.get("id") or "")
    operation = str(result.get("operation") or "")
    candidate = " ".join(str(candidate_text or "").replace("’", "'").split())
    result_state = str(result.get("status") or "missing_result")
    missing_input = str(result.get("missing_input") or "").strip()
    owner = str(obligation.get("responsible_owner") or "")
    result_owner = str(result.get("responsible_owner") or "")
    owner_fit = bool(owner and result_owner and owner == result_owner)

    base = {
        "status": "semantic_fulfillment_checked",
        "obligation_id": obligation_id,
        "operation": operation,
        "typed_operation_required": bool(operation),
        "operation_result_state": result_state,
        "owner_fit": owner_fit,
        "declared_obligation_id_accepted_as_proof": False,
        "generic_prose_accepted_as_performance": False,
        "missing_input": missing_input,
        "fulfilled": False,
        "resolved_for_release": False,
        "missing_state_visible": False,
        "supported_route_visible": False,
        "unresolved_reason": "",
        "provenance_boundary": SEMANTIC_FULFILLMENT_BOUNDARY,
    }
    if not result:
        return _with_guards(
            {
                **base,
                "unresolved_reason": "no typed owner result exists for this operation",
            }
        )

    if result_state != "completed":
        missing_visible = _missing_state_visible(candidate, missing_input)
        route_visible = bool(missing_visible and _contains_any(candidate.lower(), _ROUTE_MARKERS))
        return _with_guards(
            {
                **base,
                "missing_state_visible": missing_visible,
                "supported_route_visible": route_visible,
                "resolved_for_release": missing_visible,
                "resolution_state": (
                    "supported_route" if route_visible else "explicitly_held" if missing_visible else "unresolved"
                ),
                "unresolved_reason": (
                    missing_input
                    or str(result.get("reason") or "the typed owner operation is not complete")
                ),
            }
        )

    fields = result.get("fields") if isinstance(result.get("fields"), dict) else {}
    requirements = _visible_requirements(operation, fields, obligation)
    receipts = []
    for requirement in requirements:
        phrases = requirement["phrases"]
        matched = [phrase for phrase in phrases if _phrase_realized(candidate, phrase)]
        receipts.append(
            {
                **requirement,
                "matched_phrases": matched,
                "matched_count": len(matched),
                "satisfied": len(matched) >= int(requirement["minimum_count"]),
            }
        )

    field_fit = bool(receipts and all(item["satisfied"] for item in receipts))
    if operation == "closure":
        field_fit = _closure_realized(candidate)
    elif operation == "disagreement":
        field_fit = field_fit and _disagreement_realized(candidate)

    requested_count = int(obligation.get("requested_count") or 0)
    performed_count = _performed_count(operation, receipts)
    count_fit = not requested_count or performed_count >= requested_count
    response_shape = (
        obligation.get("response_shape")
        if isinstance(obligation.get("response_shape"), dict)
        else {}
    )
    shape_receipt = _shape_receipt(candidate, response_shape, requested_count)
    constraint_fit = shape_receipt["satisfied"]
    condition = obligation.get("condition") if isinstance(obligation.get("condition"), dict) else {}
    condition_fit = _condition_fit(condition, fields, candidate)
    topic_fit = field_fit or _expression_seed_realized(
        candidate,
        str(result.get("expression_seed") or ""),
    )
    fulfilled = bool(
        candidate
        and owner_fit
        and field_fit
        and topic_fit
        and count_fit
        and condition_fit
        and constraint_fit
    )
    unresolved = []
    if not owner_fit:
        unresolved.append("the typed result does not belong to the obligation's responsible owner")
    if not field_fit:
        unresolved.append("the visible answer does not realize the operation's required meaning")
    if not count_fit:
        unresolved.append(
            f"the visible answer performs {performed_count} of {requested_count} requested items"
        )
    if not condition_fit:
        unresolved.append("the operation result does not preserve the obligation condition")
    if not constraint_fit:
        unresolved.append("the visible answer does not preserve the requested response shape")

    return _with_guards(
        {
            **base,
            "visible_field_receipts": receipts,
            "visible_semantics_performed": field_fit,
            "topic_fit": topic_fit,
            "condition_fit": condition_fit,
            "requested_count": requested_count,
            "performed_count": performed_count,
            "count_fit": count_fit,
            "response_shape_receipt": shape_receipt,
            "constraint_fit": constraint_fit,
            "fulfilled": fulfilled,
            "resolved_for_release": fulfilled,
            "resolution_state": "answered" if fulfilled else "unresolved",
            "unresolved_reason": "; ".join(unresolved),
            "productive_alternate_path": {
                "responsible_owner": result_owner or owner,
                "operation": operation,
                "required_visible_fields": [
                    item["field"] for item in receipts if item["satisfied"] is not True
                ],
                "use_existing_current_turn_owner_output_only": True,
                "generate_new_fact": False,
            },
        }
    )


def _visible_requirements(
    operation: str,
    fields: dict[str, Any],
    obligation: dict[str, Any],
) -> list[dict[str, Any]]:
    requested_count = int(obligation.get("requested_count") or 0)
    if operation == "method":
        return [_requirement("steps", fields.get("steps"), requested_count or 1)]
    if operation == "causal_explanation":
        return [
            _requirement("conclusion", fields.get("conclusion")),
            _requirement("mechanism_or_reason", fields.get("mechanism_or_reason")),
        ]
    if operation == "prediction":
        return [
            _requirement("predicted_change", fields.get("predicted_change")),
            _requirement("revision_conditions", fields.get("revision_conditions")),
        ]
    if operation == "hypothesis":
        return [
            _requirement("hypothesis", fields.get("hypothesis")),
            _requirement("revision_conditions", fields.get("revision_conditions")),
        ]
    if operation == "comparison":
        return [
            _requirement("candidates", fields.get("candidates"), 2),
            _requirement("findings", fields.get("findings"), 1),
        ]
    if operation == "choice":
        return [
            _requirement("selected_option", fields.get("selected_option")),
            _requirement("criteria", fields.get("criteria"), 1),
        ]
    if operation == "disagreement":
        return [
            _requirement("claim_evaluated", fields.get("claim_evaluated")),
            _requirement("premises", fields.get("premises"), 1),
        ]
    if operation == "correction":
        application = fields.get("current_application") or fields.get("corrected_input")
        return [_requirement("corrected_application", application, 1)]
    if operation == "preference":
        return [_requirement("authored_preference", fields.get("authored_preference"))]
    if operation == "summary":
        return [_requirement("points", fields.get("points"), requested_count or 1)]
    if operation == "closure":
        return [_requirement("closure_intent", fields.get("closure_intent"))]
    return []


def _requirement(field: str, value: Any, minimum_count: int = 1) -> dict[str, Any]:
    phrases = _phrases(value)
    return {
        "field": field,
        "phrases": phrases,
        "minimum_count": min(max(1, int(minimum_count)), max(1, len(phrases))),
    }


def _phrases(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for nested in value.values():
            values.extend(_phrases(nested))
    elif isinstance(value, (list, tuple, set)):
        for nested in value:
            values.extend(_phrases(nested))
    elif value is not None and str(value).strip():
        values.append(str(value).strip())
    return list(dict.fromkeys(values))[:40]


def _phrase_realized(candidate: str, phrase: str) -> bool:
    candidate_surface = _surface(candidate)
    phrase_surface = _surface(phrase)
    if not candidate_surface or not phrase_surface:
        return False
    if phrase_surface in candidate_surface:
        return True
    phrase_terms = set(_terms(phrase_surface))
    if not phrase_terms:
        return False
    candidate_terms = set(_terms(candidate_surface))
    overlap = phrase_terms & candidate_terms
    minimum = 1 if len(phrase_terms) <= 2 else max(2, (len(phrase_terms) + 1) // 2)
    return len(overlap) >= minimum


def _expression_seed_realized(candidate: str, expression_seed: str) -> bool:
    if not expression_seed.strip():
        return False
    seed_terms = set(_terms(expression_seed))
    if not seed_terms:
        return False
    candidate_terms = set(_terms(candidate))
    minimum = max(1, (len(seed_terms) + 2) // 3)
    return len(seed_terms & candidate_terms) >= minimum


def _missing_state_visible(candidate: str, missing_input: str) -> bool:
    lower = candidate.lower()
    if not candidate or not _contains_any(lower, _GENERIC_MISSING_MARKERS):
        return False
    missing_terms = set(_terms(missing_input))
    return not missing_terms or bool(missing_terms & set(_terms(candidate)))


def _closure_realized(candidate: str) -> bool:
    lower = candidate.lower().strip()
    return bool(
        re.search(
            r"\b(?:goodbye|goodnight|take care|talk (?:to you )?later|see you|catch you later|"
            r"until next time|i'll be here|enjoy|rest well|clean stopping point|"
            r"leave (?:it|things) there)\b",
            lower,
        )
    )


def _disagreement_realized(candidate: str) -> bool:
    lower = candidate.lower().strip()
    return bool(
        re.search(
            r"^(?:no\b|not quite\b)|\b(?:i (?:gently )?disagree|i do not agree|i don't agree|"
            r"that does not follow|that doesn't follow|the evidence conflicts)\b",
            lower,
        )
    )


def _condition_fit(condition: dict[str, Any], fields: dict[str, Any], candidate: str) -> bool:
    if not condition or condition.get("present") is not True:
        return True
    result_condition = fields.get("condition")
    if isinstance(result_condition, dict) and result_condition:
        return True
    condition_text = " ".join(
        str(condition.get(key) or "")
        for key in ("text", "condition", "clause", "source_text")
    ).strip()
    if condition_text and _phrase_realized(candidate, condition_text):
        return True
    # The canonical ledger already established that the current instruction is
    # conditional. A completed result tied to this exact obligation may act
    # under that condition without parroting it, but must not erase it.
    return any(key in fields for key in ("condition", "conditions", "assumptions"))


def _performed_count(operation: str, receipts: list[dict[str, Any]]) -> int:
    count_fields = {
        "method": "steps",
        "comparison": "findings",
        "summary": "points",
    }
    target = count_fields.get(operation)
    if target:
        receipt = next((item for item in receipts if item.get("field") == target), {})
        return int(receipt.get("matched_count") or 0)
    return 1 if receipts and all(item.get("satisfied") is True for item in receipts) else 0


def _shape_receipt(candidate: str, shape: dict[str, Any], requested_count: int) -> dict[str, Any]:
    if not shape or shape.get("explicit") is not True:
        return {
            "required": False,
            "ordered_required": False,
            "ordered_present": True,
            "brevity_required": "",
            "word_count": len(candidate.split()),
            "word_limit": 0,
            "brevity_fit": True,
            "satisfied": True,
        }
    count = int(shape.get("requested_count") or requested_count or 0)
    ordered_required = shape.get("ordered") is True and count > 1
    lower = candidate.lower()
    numbered = len(re.findall(r"(?:^|\s)(?:[1-9][.):]|[-*])\s+", candidate))
    named = sum(
        1
        for marker in ("first", "second", "third", "fourth", "fifth")[:count]
        if re.search(rf"\b{marker}\b", lower)
    )
    ordered_present = not ordered_required or numbered >= count or named >= count
    brevity = str(shape.get("brevity") or "").lower()
    word_count = len(candidate.split())
    word_limit = (40 * max(1, count)) if brevity in {"short", "brief", "concise"} else (
        24 * max(1, count) if brevity in {"tiny", "little", "small"} else 0
    )
    brevity_fit = not word_limit or word_count <= word_limit
    return {
        "required": True,
        "counted_unit": str(shape.get("counted_unit") or ""),
        "ordered_required": ordered_required,
        "ordered_present": ordered_present,
        "brevity_required": brevity,
        "word_count": word_count,
        "word_limit": word_limit,
        "brevity_fit": brevity_fit,
        "satisfied": ordered_present and brevity_fit,
    }


def _terms(value: str) -> list[str]:
    words = [
        _term_key(word.lower())
        for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{1,}", str(value or ""))
    ]
    return list(dict.fromkeys(word for word in words if word not in _STOP))[:160]


def _term_key(word: str) -> str:
    aliases = {
        "choices": "choice",
        "compared": "compare",
        "compares": "compare",
        "comparisons": "compare",
        "conditions": "condition",
        "constraints": "constraint",
        "depends": "depend",
        "differences": "difference",
        "findings": "finding",
        "hypotheses": "hypothesis",
        "limitations": "limit",
        "limited": "limit",
        "predictions": "prediction",
        "reasons": "reason",
        "relationships": "relationship",
        "revisions": "revision",
        "steps": "step",
        "summaries": "summary",
    }
    if word in aliases:
        return aliases[word]
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _surface(value: str) -> str:
    return " ".join(str(value or "").lower().replace("’", "'").split())


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    return any(marker in value for marker in markers)


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
