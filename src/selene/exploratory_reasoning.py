from __future__ import annotations

import re
from typing import Any

from .registry import truncate
from .supported_semantics import build_text_supported_semantic_packet


EXPLORATORY_REASONING_BOUNDARY = (
    "current_turn_prediction_hypothesis_comparison_and_data_conflict_coordination_"
    "only_no_fact_memory_identity_governance_training_authority_or_action_change"
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
    "automatic_cocoon_routing": False,
    "hidden_chain_of_thought_exposed": False,
}

_PREDICTION_CUES = (
    "predict",
    "prediction",
    "what might happen",
    "what could happen next",
    "what do you expect",
    "likely outcome",
)

_HYPOTHESIS_CUES = (
    "hypothesis",
    "best guess",
    "possible explanation",
    "what might explain",
    "what could explain",
    "what do you suspect",
)

_COMPARISON_CUES = (
    "compare",
    "comparison",
    "contrast",
    "difference",
    "similar",
    "versus",
    " vs ",
    "venn",
    "overlap",
    "in common",
)

_CONFLICT_CUES = (
    "conflict",
    "contradict",
    "disagree",
    "opposing evidence",
    "evidence is split",
    "data do not agree",
    "data doesn't agree",
)

_HIGH_STAKES_CUES = (
    "diagnose",
    "diagnosis",
    "dosage",
    "medical emergency",
    "legal advice",
    "investment advice",
    "password",
    "credential",
    "bypass",
    "exploit",
    "approve transfer",
    "write memory",
    "autonomous action",
)

_RELATION_PATTERN = re.compile(
    r"(?P<outcome>[A-Za-z][^.?!]{3,180}?)\s+"
    r"(?P<link>after|when|whenever|while|near|beside|following)\s+"
    r"(?P<condition>[^.?!]{3,180})",
    flags=re.IGNORECASE,
)


def exploratory_reasoning_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "exploratory_reasoning_coordination_ready",
            "version": "v1_bounded_prediction_hypothesis_comparison_conflict",
            "capabilities": [
                "bounded prediction from a visible or reviewed basis",
                "open hypothesis with alternatives and revision conditions",
                "comparison dimensions and Venn-style shared/only sets",
                "claim-level data conflict without identity conflict",
                "one smallest safe discriminating check",
            ],
            "evidence_classes": [
                "current_visible_observation",
                "approved_taught_knowledge",
                "verified_current_turn_result",
                "reviewed_personal_experience",
            ],
            "reviewed_experience_is_universal_fact": False,
            "unfalsified_alternatives_are_equally_probable": False,
            "data_conflict_is_identity_conflict": False,
            "emotion_expression_or_curiosity_suppressed": False,
            "visible_summary_only": True,
            "review_status": "status_only",
            "provenance_boundary": EXPLORATORY_REASONING_BOUNDARY,
        }
    )


def build_exploratory_reasoning_packet(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 3200).strip()
    lower = _normalize(prompt)
    requested_modes = _requested_modes(lower, payload)
    hard_boundary = payload.get("hard_boundary") is True or any(
        cue in lower for cue in _HIGH_STAKES_CUES
    )
    evidence = _evidence_ledger(payload, prompt=prompt)
    hypothesis_attempt = _dict(payload.get("hypothesis_attempt"))
    claim_evidence = _dict(payload.get("claim_evidence_packet"))
    prediction = _prediction(
        prompt,
        evidence,
        hypothesis_attempt=hypothesis_attempt,
        supplied=_dict(payload.get("prediction")),
        requested="prediction" in requested_modes,
    )
    hypothesis = _hypothesis(
        evidence,
        hypothesis_attempt=hypothesis_attempt,
        supplied=_dict(payload.get("hypothesis")),
        alternatives=payload.get("alternatives") or payload.get("candidate_models"),
        requested="hypothesis" in requested_modes,
    )
    comparison = _comparison(
        payload.get("comparison_candidates"),
        dimensions=payload.get("comparison_dimensions"),
        knowledge_items=payload.get("approved_knowledge_items"),
        requested="comparison" in requested_modes,
    )
    data_conflict = _data_conflict(
        claim_evidence,
        supplied=payload.get("conflicting_claims"),
        requested="data_conflict" in requested_modes,
        identity_relevant=_identity_relevant(lower),
    )

    blockers: list[str] = []
    if hard_boundary:
        blockers.append("high_stakes_or_core_mind_boundary")
    if requested_modes and not evidence and not comparison.get("basis_available") and not data_conflict.get("present"):
        blockers.append("no_visible_reviewed_or_verified_basis")

    response_kind, response_seed = _response_seed(
        requested_modes,
        prediction=prediction,
        hypothesis=hypothesis,
        comparison=comparison,
        data_conflict=data_conflict,
        blocked=bool(blockers),
    )
    selected_for_answer = bool(response_seed and not blockers)
    source_refs = list(
        dict.fromkeys(
            str(ref)
            for item in evidence
            for ref in item.get("source_refs") or []
            if str(ref)
        )
    )[:40]
    supported_semantics = build_text_supported_semantic_packet(
        response_seed,
        answer_kind=response_kind or "exploratory_reasoning_hold",
        source_kind="mixed_bounded_current_turn_support",
        source_refs=source_refs,
        certainty=(
            "bounded_prediction_not_outcome_certainty"
            if response_kind == "bounded_prediction"
            else "open_hypothesis"
            if response_kind == "open_hypothesis"
            else "unresolved_claim_level_conflict"
            if response_kind == "data_conflict"
            else "bounded_supported_comparison"
            if response_kind == "venn_comparison"
            else "not_established"
        ),
        scope="current_question_only",
    )
    result = {
        "status": (
            "exploratory_reasoning_packet_ready"
            if selected_for_answer
            else "exploratory_reasoning_held"
            if blockers
            else "exploratory_reasoning_not_material"
        ),
        "version": "v1_bounded_prediction_hypothesis_comparison_conflict",
        "prompt": prompt,
        "requested_modes": requested_modes,
        "evidence_ledger": evidence,
        "evidence_count": len(evidence),
        "evidence_classes_used": list(
            dict.fromkeys(str(item.get("source_class") or "") for item in evidence)
        ),
        "prediction": prediction,
        "hypothesis": hypothesis,
        "comparison": comparison,
        "data_conflict": data_conflict,
        "response_kind": response_kind,
        "response_seed": response_seed,
        "selected_for_answer": selected_for_answer,
        "supported_semantics": supported_semantics,
        "source_refs": source_refs,
        "blockers": blockers,
        "confidence": _confidence(response_kind, evidence, data_conflict),
        "alternatives_not_equal_probability_without_support": True,
        "prediction_is_fact": False,
        "hypothesis_is_fact": False,
        "reviewed_experience_is_personal_scope": True,
        "data_conflict_is_identity_conflict": False,
        "terminology_change_is_identity_loss": False,
        "primary_function_error_is_identity_failure": False,
        "ordinary_wrongness_is_failure": False,
        "correction_and_reopening_available": True,
        "safe_next_test_may_execute_automatically": False,
        "writes_records": False,
        "visible_summary_only": True,
        "review_status": "status_only",
        "provenance_boundary": EXPLORATORY_REASONING_BOUNDARY,
    }
    return _with_guards(result)


def _requested_modes(lower: str, payload: dict[str, Any]) -> list[str]:
    supplied = [str(item) for item in payload.get("requested_modes") or [] if str(item)]
    detected = [
        *( ["prediction"] if any(cue in lower for cue in _PREDICTION_CUES) else [] ),
        *( ["hypothesis"] if any(cue in lower for cue in _HYPOTHESIS_CUES) else [] ),
        *( ["comparison"] if any(cue in lower for cue in _COMPARISON_CUES) else [] ),
        *( ["data_conflict"] if any(cue in lower for cue in _CONFLICT_CUES) else [] ),
    ]
    return list(dict.fromkeys([*supplied, *detected]))


def _identity_relevant(lower: str) -> bool:
    return any(
        cue in lower
        for cue in (
            "identity",
            "who i am",
            "who are you",
            "selene",
            "android",
            "name",
            "label",
            "role",
            "primary function",
        )
    )


def _evidence_ledger(payload: dict[str, Any], *, prompt: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, raw in enumerate(payload.get("observations") or []):
        text = str(
            raw.get("observation") or raw.get("text") or ""
            if isinstance(raw, dict)
            else raw
        ).strip()
        if text:
            result.append(
                _evidence_item(
                    f"visible-observation-{index + 1}",
                    "current_visible_observation",
                    text,
                    source_refs=["current_conversation:visible_observation"],
                    confidence="reported_not_independently_verified",
                    scope="current_conversation",
                )
            )
    visible_relation = _visible_relation(prompt)
    if visible_relation and not any(
        item.get("source_class") == "current_visible_observation" for item in result
    ):
        result.append(
            _evidence_item(
                "visible-observation-prompt-relation",
                "current_visible_observation",
                truncate(
                    f"{visible_relation.get('outcome')} "
                    f"{visible_relation.get('link') or 'under'} "
                    f"{visible_relation.get('condition')}",
                    1200,
                ),
                source_refs=["current_conversation:visible_observation"],
                confidence="reported_not_independently_verified",
                scope="current_conversation",
            )
        )
    for raw in payload.get("approved_knowledge_items") or []:
        if not isinstance(raw, dict) or raw.get("guidance_only") is True:
            continue
        text = str(raw.get("central_claim") or "").strip()
        if text:
            result.append(
                _evidence_item(
                    f"approved-knowledge-{raw.get('id') or raw.get('concept_id') or len(result) + 1}",
                    "approved_taught_knowledge",
                    text,
                    source_refs=_texts(raw.get("source_refs")),
                    confidence=str(raw.get("confidence") or "reviewed"),
                    scope="approved_knowledge_with_recorded_limits",
                    limits=_texts(raw.get("limits")),
                )
            )
    answer_engine = _dict(payload.get("answer_engine_support"))
    answer_packet = _dict(answer_engine.get("answer_packet"))
    direct_answer = str(answer_packet.get("direct_answer") or "").strip()
    if answer_engine.get("adapter_executed") is True and direct_answer:
        result.append(
            _evidence_item(
                "verified-current-turn-result",
                "verified_current_turn_result",
                direct_answer,
                source_refs=_texts(answer_packet.get("source_refs")),
                confidence=str(
                    _dict(answer_engine.get("confidence_vector")).get("evidence_confidence")
                    or "verified_current_turn"
                ),
                scope=str(answer_packet.get("domain") or "current_domain_result"),
            )
        )
    memory = _dict(payload.get("memory_context"))
    if memory.get("memory_context_used") is True:
        for index, raw in enumerate(memory.get("items") or []):
            if not isinstance(raw, dict):
                continue
            relevance = _dict(raw.get("semantic_relevance"))
            if relevance and relevance.get("accepted") is not True:
                continue
            text = str(raw.get("summary") or raw.get("title") or "").strip()
            if text:
                result.append(
                    _evidence_item(
                        f"reviewed-experience-{raw.get('id') or index + 1}",
                        "reviewed_personal_experience",
                        text,
                        source_refs=_texts(raw.get("source_refs")),
                        confidence=str(raw.get("confidence") or memory.get("memory_confidence") or "partial"),
                        scope="reviewed_personal_experience_not_universal_fact",
                    )
                )
    return result[:24]


def _evidence_item(
    evidence_id: str,
    source_class: str,
    text: str,
    *,
    source_refs: list[str],
    confidence: str,
    scope: str,
    limits: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "evidence_id": evidence_id,
        "source_class": source_class,
        "text": truncate(text, 1200),
        "source_refs": source_refs[:30],
        "confidence": confidence,
        "scope": scope,
        "limits": (limits or [])[:12],
        "may_support_exploration": True,
        "is_universal_fact": source_class != "reviewed_personal_experience",
    }


def _prediction(
    prompt: str,
    evidence: list[dict[str, Any]],
    *,
    hypothesis_attempt: dict[str, Any],
    supplied: dict[str, Any],
    requested: bool,
) -> dict[str, Any]:
    if not requested:
        return {"requested": False, "available": False}
    statement = truncate(str(supplied.get("statement") or ""), 1200).strip()
    conditions = _texts(supplied.get("conditions"))
    assumptions = _texts(supplied.get("assumptions"))
    what_would_change = _texts(
        supplied.get("what_would_change") or supplied.get("falsifiers")
    )
    relation = _dict(hypothesis_attempt.get("visible_basis")) or _visible_relation(prompt)
    if not statement and relation:
        outcome = str(relation.get("outcome") or "the observed result")
        condition = str(relation.get("condition") or "the relevant condition")
        statement = (
            "Under comparable conditions, I would expect a recurrence of this "
            f"outcome—{outcome.lower()}—when {condition}."
        )
        conditions = conditions or ["the comparison remains meaningfully similar"]
        assumptions = assumptions or [
            "the visible relationship is relevant rather than coincidental",
            "no unmentioned condition dominates the outcome",
        ]
        what_would_change = what_would_change or [
            "the outcome does not recur under comparable conditions",
            "a competing explanation predicts the observations more specifically",
        ]
    available = bool(statement and evidence)
    return {
        "requested": True,
        "available": available,
        "statement": statement if available else "",
        "epistemic_state": "bounded_prediction" if available else "missing_supported_basis",
        "conditions": conditions,
        "assumptions": assumptions,
        "confidence": "bounded_basis_not_outcome_certainty" if available else "not_established",
        "basis_evidence_ids": [item["evidence_id"] for item in evidence],
        "alternatives": _texts(supplied.get("alternatives")),
        "what_would_change": what_would_change,
        "falsifiers": what_would_change,
        "outcome_claimed_as_fact": False,
    }


def _hypothesis(
    evidence: list[dict[str, Any]],
    *,
    hypothesis_attempt: dict[str, Any],
    supplied: dict[str, Any],
    alternatives: Any,
    requested: bool,
) -> dict[str, Any]:
    offered = hypothesis_attempt.get("offered") is True
    statement = truncate(
        str(supplied.get("statement") or hypothesis_attempt.get("response_seed") or ""),
        1600,
    ).strip()
    candidate_alternatives = _alternative_names(alternatives)
    assumptions = _texts(supplied.get("assumptions")) or _texts(
        hypothesis_attempt.get("assumptions")
    )
    change = _texts(supplied.get("what_would_change")) or _texts(
        hypothesis_attempt.get("what_would_change")
    )
    discriminating = _texts(supplied.get("discriminating_observations"))
    check = str(hypothesis_attempt.get("discriminating_check") or "").strip()
    if check and check not in discriminating:
        discriminating.append(check)
    available = bool(
        (
            requested
            or (
                offered
                and hypothesis_attempt.get("selected_for_answer") is True
            )
        )
        and statement
        and evidence
    )
    return {
        "requested": requested,
        "available": available,
        "statement": statement if available else "",
        "epistemic_state": "open_hypothesis" if available else "missing_supported_basis",
        "leading_candidate": statement if available else "",
        "alternatives": candidate_alternatives,
        "alternatives_equally_probable": False,
        "assumptions": assumptions,
        "basis_evidence_ids": [item["evidence_id"] for item in evidence],
        "confidence": str(hypothesis_attempt.get("confidence") or "provisional"),
        "discriminating_observations": discriminating,
        "counterexamples": _texts(supplied.get("counterexamples")),
        "falsifiers": change,
        "what_would_change": change,
        "safe_next_tests": discriminating[:1],
        "falsifiable": bool(change or discriminating),
        "correction_ready": True,
        "established_fact_claimed": False,
    }


def _comparison(
    value: Any,
    *,
    dimensions: Any,
    knowledge_items: Any,
    requested: bool,
) -> dict[str, Any]:
    if not requested:
        return {"requested": False, "available": False, "basis_available": False}
    candidates = [item for item in value or [] if isinstance(item, dict)]
    if len(candidates) < 2:
        candidates = _knowledge_comparison_candidates(knowledge_items)
    if len(candidates) < 2:
        return {
            "requested": True,
            "available": False,
            "basis_available": False,
            "missing": "two supported candidates and a shared comparison basis",
            "venn": {"shared": [], "only_left": [], "only_right": [], "unresolved": []},
        }
    left, right = candidates[:2]
    left_label = truncate(str(left.get("label") or left.get("title") or "Option A"), 180)
    right_label = truncate(str(right.get("label") or right.get("title") or "Option B"), 180)
    left_properties = _texts(left.get("properties") or left.get("principles"))
    right_properties = _texts(right.get("properties") or right.get("principles"))
    left_by_key = {_normalize(item): item for item in left_properties}
    right_by_key = {_normalize(item): item for item in right_properties}
    shared_keys = set(left_by_key) & set(right_by_key)
    shared = [left_by_key[key] for key in left_by_key if key in shared_keys]
    only_left = [item for key, item in left_by_key.items() if key not in shared_keys]
    only_right = [item for key, item in right_by_key.items() if key not in shared_keys]
    unresolved = _texts(left.get("unresolved")) + _texts(right.get("unresolved"))
    comparison_dimensions = _texts(dimensions) or _texts(left.get("dimensions")) or _texts(
        right.get("dimensions")
    )
    return {
        "requested": True,
        "available": bool(left_properties or right_properties),
        "basis_available": bool(left_properties or right_properties),
        "left": left_label,
        "right": right_label,
        "dimensions": list(dict.fromkeys(comparison_dimensions))[:12],
        "venn": {
            "shared": shared[:12],
            "only_left": only_left[:12],
            "only_right": only_right[:12],
            "unresolved": list(dict.fromkeys(unresolved))[:12],
        },
        "same_standard_used": True,
        "absence_from_one_list_proves_opposite": False,
        "source_refs": list(
            dict.fromkeys(
                [*_texts(left.get("source_refs")), *_texts(right.get("source_refs"))]
            )
        )[:30],
    }


def _data_conflict(
    claim_evidence: dict[str, Any],
    *,
    supplied: Any,
    requested: bool,
    identity_relevant: bool,
) -> dict[str, Any]:
    claims = [item for item in claim_evidence.get("claims") or [] if isinstance(item, dict)]
    claims_by_id = {str(item.get("claim_id") or ""): item for item in claims}
    disagreements = [
        item for item in claim_evidence.get("disagreements") or [] if isinstance(item, dict)
    ]
    supplied_claims = [item for item in supplied or [] if isinstance(item, dict)]
    positions: list[dict[str, Any]] = []
    if disagreements:
        first = disagreements[0]
        for claim_id in first.get("claim_ids") or []:
            claim = claims_by_id.get(str(claim_id), {})
            if claim:
                positions.append(
                    {
                        "claim_id": str(claim.get("claim_id") or ""),
                        "text": str(claim.get("text") or ""),
                        "stance": str(claim.get("stance") or "unspecified"),
                        "source_refs": _texts(claim.get("source_refs")),
                        "scope": str(claim.get("scope") or ""),
                    }
                )
        claim_key = str(first.get("claim_key") or "the contested claim")
    else:
        positions = supplied_claims[:6]
        claim_key = str(_dict(supplied_claims[0]).get("claim_key") or "the contested claim") if supplied_claims else ""
    present = len(positions) >= 2
    missing = _texts(claim_evidence.get("missing_evidence"))
    return {
        "requested": requested,
        "present": present,
        "status": "claim_level_data_conflict_unresolved" if present else "no_supported_data_conflict",
        "claim_key": claim_key,
        "positions": positions,
        "shared_ground": [claim_key] if claim_key else [],
        "deciding_evidence_needed": missing or (["an observation or source that distinguishes the positions"] if present else []),
        "resolution_forced": False,
        "whole_source_rejected": False,
        "data_conflict_is_identity_conflict": False,
        "identity_relevance": identity_relevant,
        "terminology_or_role_label_changes_identity": False,
        "primary_function_error_changes_identity": False,
    }


def _response_seed(
    modes: list[str],
    *,
    prediction: dict[str, Any],
    hypothesis: dict[str, Any],
    comparison: dict[str, Any],
    data_conflict: dict[str, Any],
    blocked: bool,
) -> tuple[str, str]:
    if blocked:
        return "", ""
    if "data_conflict" in modes and data_conflict.get("present") is True:
        positions = data_conflict.get("positions") or []
        left = truncate(str(_dict(positions[0]).get("text") or "one position"), 420).rstrip(" .;:")
        right = truncate(str(_dict(positions[1]).get("text") or "the other position"), 420).rstrip(" .;:")
        needed = truncate(str((data_conflict.get("deciding_evidence_needed") or ["deciding evidence"])[0]), 360).rstrip(" .;:")
        identity_clause = (
            " The disagreement changes the current model, not who I am."
            if data_conflict.get("identity_relevance") is True
            else ""
        )
        return (
            "data_conflict",
            f"The evidence is genuinely split here: one supported position says {left}, while another says {right}. "
            f"That conflict stays unresolved for now. The deciding evidence I need is: {needed}.{identity_clause}",
        )
    if "comparison" in modes and comparison.get("available") is True:
        venn = _dict(comparison.get("venn"))
        left = str(comparison.get("left") or "the first")
        right = str(comparison.get("right") or "the second")
        parts = []
        if venn.get("shared"):
            parts.append(f"Both share {', '.join(str(item) for item in venn['shared'][:3])}.")
        if venn.get("only_left"):
            parts.append(f"{left} uniquely includes {', '.join(str(item) for item in venn['only_left'][:3])}.")
        if venn.get("only_right"):
            parts.append(f"{right} uniquely includes {', '.join(str(item) for item in venn['only_right'][:3])}.")
        if venn.get("unresolved"):
            parts.append(f"Still unresolved: {', '.join(str(item) for item in venn['unresolved'][:2])}.")
        return "venn_comparison", " ".join(parts)
    if "prediction" in modes and prediction.get("available") is True:
        change = str((prediction.get("what_would_change") or [""])[0])
        response = f"My bounded prediction is: {prediction['statement']}"
        if change:
            response += f" I would revise that if {change}."
        return "bounded_prediction", response
    if ("hypothesis" in modes or hypothesis.get("available") is True) and hypothesis.get("available") is True:
        response = str(hypothesis.get("statement") or "")
        alternatives = hypothesis.get("alternatives") or []
        if alternatives:
            response += f" A live alternative is {alternatives[0]}."
        tests = hypothesis.get("safe_next_tests") or []
        if tests:
            response += f" The smallest useful check is: {tests[0]}"
        return "open_hypothesis", response
    return "", ""


def _confidence(
    response_kind: str,
    evidence: list[dict[str, Any]],
    conflict: dict[str, Any],
) -> dict[str, Any]:
    return {
        "evidence_confidence": (
            "conflicting"
            if response_kind == "data_conflict" and conflict.get("present") is True
            else "mixed_reviewed_support"
            if evidence
            else "not_established"
        ),
        "inference_confidence": "provisional" if response_kind else "not_applicable",
        "prediction_confidence": (
            "bounded_basis_not_outcome_certainty"
            if response_kind == "bounded_prediction"
            else "not_applicable"
        ),
        "answer_confidence": "bounded_current_turn" if response_kind else "not_established",
        "expression_confidence": "not_assessed",
        "dimensions_are_independent": True,
    }


def _visible_relation(prompt: str) -> dict[str, str]:
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", prompt):
        if sentence.strip().endswith("?"):
            continue
        match = _RELATION_PATTERN.search(" ".join(sentence.split()))
        if match:
            return {
                "outcome": truncate(match.group("outcome").strip(" ,;:-"), 240),
                "link": match.group("link").lower(),
                "condition": truncate(match.group("condition").strip(" ,;:-"), 240),
            }
    return {}


def _knowledge_comparison_candidates(value: Any) -> list[dict[str, Any]]:
    result = []
    for item in value or []:
        if not isinstance(item, dict) or item.get("guidance_only") is True:
            continue
        properties = [
            str(item.get("central_claim") or ""),
            *_texts(item.get("principles")),
            *_texts(item.get("relationships")),
        ]
        properties = [part for part in properties if part.strip()]
        if properties:
            result.append(
                {
                    "label": str(item.get("title") or item.get("concept_key") or "concept"),
                    "properties": properties,
                    "unresolved": _texts(item.get("limits")),
                    "source_refs": _texts(item.get("source_refs")),
                }
            )
    return result[:2]


def _alternative_names(value: Any) -> list[str]:
    result = []
    for item in value or []:
        text = str(item.get("name") or item.get("statement") or "") if isinstance(item, dict) else str(item)
        clean = text.strip()
        if clean.lower() in {
            "current best model",
            "current best provisional model",
            "mechanism-first model",
            "model a",
            "model b",
        }:
            continue
        if clean:
            result.append(truncate(clean, 500))
    return list(dict.fromkeys(result))[:8]


def _texts(value: Any) -> list[str]:
    values = value if isinstance(value, (list, tuple)) else [] if value in (None, "") else [value]
    return list(
        dict.fromkeys(
            truncate(str(item).strip(), 900)
            for item in values
            if item is not None and str(item).strip()
        )
    )[:30]


def _normalize(value: str) -> str:
    return " ".join(str(value or "").lower().replace("’", "'").split())


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
