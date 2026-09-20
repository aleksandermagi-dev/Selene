from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .registry import truncate


PROBLEM_RESOLUTION_BOUNDARY = (
    "visible_current_problem_reconstruction_satisfiability_epistemic_and_retry_"
    "coordination_only_no_fact_invention_memory_identity_personality_governance_"
    "training_authority_or_action_change"
)

SEVEN_POINT_DIMENSIONS = ("who", "what", "why", "when", "where", "how", "context")

EPISTEMIC_STATES = {
    "KNOWN_SUPPORTED",
    "CANDIDATE_UNVERIFIED",
    "UNKNOWN_INSUFFICIENT_EVIDENCE",
    "CONFLICT_UNSATISFIABLE",
    "WRONG_FALSIFIED",
    "RETRY_UPDATED_APPROACH",
}

FAILURE_CLASSES = {
    "missing_knowledge",
    "retrieval_failure",
    "bad_inference",
    "unreliable_source",
    "ambiguous_context",
    "conflicting_evidence",
    "conflicting_constraints",
    "false_premise",
    "impossible_or_underspecified_request",
    "verification_failure",
}

PROBLEM_RESOLUTION_VERSION = "v2_wrongness_and_support_integrity_separated"

FABRICATION_SIGNAL_KINDS = {
    "invented_fact",
    "invented_citation",
    "invented_source",
    "invented_observation",
    "invented_memory",
    "invented_lived_experience",
    "invented_verification",
    "known_claim_despite_known_missing_support",
}

FIRST_PERSON_STATE_SCOPES = {
    "first_person_affect",
    "first_person_emotion",
    "first_person_internal_state",
    "selene_current_affect",
    "selene_current_internal_state",
}

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
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
    "hidden_chain_of_thought_exposed": False,
    "expression_authority": False,
}


def problem_resolution_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "problem_resolution_coordination_ready",
            "version": PROBLEM_RESOLUTION_VERSION,
            "is_organ": False,
            "owner": "intelligenceOS_with_metacognition_review",
            "scope": "visible_current_problem_only",
            "seven_point_dimensions": list(SEVEN_POINT_DIMENSIONS),
            "epistemic_states": sorted(EPISTEMIC_STATES),
            "failure_classes": sorted(FAILURE_CLASSES),
            "principles": [
                "why alone is not a sufficient reconstruction",
                "a candidate is not a fact before validation",
                "unknown is a valid result and not personal failure",
                "conflicting hard constraints are represented instead of forced",
                "a retry must change the failed approach using visible failure information",
                "ordinary wrongness does not alter identity or primary function",
                "being wrong is not by itself hallucination or fabrication",
                "correctness and support integrity are assessed on separate axes",
                "a first-person affect signal is not an external fact claim and is not hallucination",
                "an explanation of an emotion may remain provisional even when the emotion is real",
            ],
            "generates_answer_facts": False,
            "executes_actions": False,
            "writes_records": False,
            "visible_summary_only": True,
            "review_status": "status_only",
            "provenance_boundary": PROBLEM_RESOLUTION_BOUNDARY,
        }
    )


def build_problem_resolution(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a visible current-problem diagnosis and bounded next-attempt contract.

    The coordinator does not solve the problem and does not infer missing facts.
    It reconstructs supplied/current context, detects representable constraint
    conflicts, classifies an observed failure, and requires a retry to use a
    meaningfully different approach.
    """

    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 4000).strip()
    situation = _dict(payload.get("situation") or payload.get("seven_point_reconstruction"))
    required_dimensions = _required_dimensions(payload.get("required_dimensions"))
    reconstruction = _seven_point_reconstruction(prompt, situation, payload, required_dimensions)

    constraints = _constraint_records(payload)
    satisfiability = _satisfiability_gate(constraints)
    evidence = _records(payload.get("evidence") or payload.get("evidence_items"), limit=40)
    verification = _dict(payload.get("verification") or payload.get("validation"))
    attempts = _attempt_records(payload.get("prior_attempts") or payload.get("attempts"))

    failure_class, failure_basis = _failure_class(
        payload,
        reconstruction=reconstruction,
        satisfiability=satisfiability,
        evidence=evidence,
        verification=verification,
        attempts=attempts,
    )
    initial_state = _epistemic_state(
        payload,
        satisfiability=satisfiability,
        evidence=evidence,
        verification=verification,
        attempts=attempts,
    )
    epistemic_integrity = _epistemic_integrity_receipt(
        payload,
        epistemic_state=initial_state,
        evidence=evidence,
        verification=verification,
        attempts=attempts,
    )
    retry = _retry_contract(
        payload,
        failure_class=failure_class,
        reconstruction=reconstruction,
        satisfiability=satisfiability,
        attempts=attempts,
    )
    epistemic_state = (
        "RETRY_UPDATED_APPROACH"
        if retry.get("status") == "retry_ready_updated_approach"
        else initial_state
    )
    stopping_state = _stopping_state(epistemic_state, retry)

    problem_key = sha256(
        "|".join(
            [
                prompt,
                *(str(reconstruction["dimensions"][key].get("value") or "") for key in SEVEN_POINT_DIMENSIONS),
            ]
        ).encode("utf-8")
    ).hexdigest()[:16]

    return _with_guards(
        {
            "status": "problem_resolution_packet_ready",
            "version": PROBLEM_RESOLUTION_VERSION,
            "problem_key": problem_key,
            "prompt": prompt,
            "reconstruction": reconstruction,
            "satisfiability_gate": satisfiability,
            "epistemic_state": epistemic_state,
            "epistemic_state_before_retry": initial_state,
            "failure": {
                "detected": bool(failure_class),
                "class": failure_class,
                "basis": failure_basis,
                "ordinary_wrongness_is_identity_failure": False,
                "failure_is_process_information": bool(failure_class),
                "wrongness_alone_establishes_hallucination": False,
            },
            "epistemic_integrity": epistemic_integrity,
            "candidate_lifecycle": {
                "generated_solution_begins_as_candidate": True,
                "validation_required_before_known_supported": True,
                "attempts": attempts,
                "failed_attempt_count": sum(
                    1 for item in attempts if item.get("status") in {"failed", "wrong", "falsified", "verification_failed"}
                ),
                "useful_mechanics_preserved": _unique_text(
                    item
                    for attempt in attempts
                    for item in attempt.get("useful_mechanics") or []
                ),
            },
            "retry": retry,
            "stopping_state": stopping_state,
            "unknown_is_failure": False,
            "wrongness_changes_identity": False,
            "being_wrong_is_hallucination": False,
            "affect_expression_is_hallucination": False,
            "primary_function_is_perfect_correctness": False,
            "objective": "move_toward_correctness",
            "visible_summary_only": True,
            "review_status": "status_only",
            "provenance_boundary": PROBLEM_RESOLUTION_BOUNDARY,
        }
    )


def _seven_point_reconstruction(
    prompt: str,
    supplied: dict[str, Any],
    payload: dict[str, Any],
    required_dimensions: set[str],
) -> dict[str, Any]:
    dimensions: dict[str, dict[str, Any]] = {}
    explicit_context = _first_text(
        supplied.get("context"),
        payload.get("context"),
        payload.get("current_context"),
    )
    candidates = {
        "who": _first_text(supplied.get("who"), payload.get("who"), payload.get("actors")),
        "what": _first_text(supplied.get("what"), payload.get("what"), prompt),
        "why": _first_text(supplied.get("why"), payload.get("why"), _explicit_reason(prompt)),
        "when": _first_text(supplied.get("when"), payload.get("when"), _explicit_time(prompt)),
        "where": _first_text(supplied.get("where"), payload.get("where"), payload.get("location")),
        "how": _first_text(supplied.get("how"), payload.get("how"), payload.get("method")),
        "context": explicit_context,
    }
    for key in SEVEN_POINT_DIMENSIONS:
        value = truncate(candidates.get(key) or "", 1000).strip()
        dimensions[key] = {
            "value": value,
            "state": "supplied_or_visible" if value else "unknown",
            "required_for_current_resolution": key in required_dimensions,
            "invented": False,
        }
    missing = [key for key in SEVEN_POINT_DIMENSIONS if not dimensions[key]["value"]]
    missing_required = [key for key in missing if key in required_dimensions]
    return {
        "dimensions": dimensions,
        "present_dimensions": [key for key in SEVEN_POINT_DIMENSIONS if dimensions[key]["value"]],
        "missing_dimensions": missing,
        "missing_required_dimensions": missing_required,
        "complete_for_declared_requirements": not missing_required,
        "why_alone_treated_as_sufficient": False,
        "plausible_cause_promoted_without_context": False,
    }


def _constraint_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for kind, values in (
        ("premise", payload.get("premises")),
        ("objective", payload.get("objectives")),
        ("policy", payload.get("policies")),
        ("constraint", payload.get("constraints")),
    ):
        raw_values = values if isinstance(values, list) else [values] if values else []
        for index, raw in enumerate(raw_values[:40]):
            item = raw if isinstance(raw, dict) else {"text": str(raw)}
            text = truncate(str(item.get("text") or item.get("statement") or ""), 1000).strip()
            subject = truncate(str(item.get("subject") or item.get("key") or ""), 160).strip()
            operator = str(item.get("operator") or item.get("relation") or "declares").strip().lower()
            value = item.get("value")
            record = {
                "id": truncate(str(item.get("id") or f"{kind}-{index + 1}"), 120),
                "kind": kind,
                "text": text,
                "subject": subject,
                "operator": operator,
                "value": value,
                "hard": item.get("hard") is not False,
                "validity": str(item.get("validity") or "unverified"),
                "conflicts_with": _text_list(item.get("conflicts_with"), limit=20, width=120),
                "source_ref": truncate(str(item.get("source_ref") or "current_problem"), 300),
            }
            if text or subject:
                records.append(record)
    return records


def _satisfiability_gate(records: list[dict[str, Any]]) -> dict[str, Any]:
    conflicts: list[dict[str, Any]] = []
    by_id = {str(item["id"]): item for item in records}
    hard = [item for item in records if item.get("hard") is True]

    for item in hard:
        for other_id in item.get("conflicts_with") or []:
            other = by_id.get(other_id)
            if other and other.get("hard") is True:
                conflicts.append(_constraint_conflict("explicit_conflict", item, other))

    for index, left in enumerate(hard):
        for right in hard[index + 1 :]:
            if not left.get("subject") or left.get("subject") != right.get("subject"):
                continue
            left_op = str(left.get("operator") or "")
            right_op = str(right.get("operator") or "")
            left_value = left.get("value")
            right_value = right.get("value")
            if left_op in {"equals", "must_equal", "requires"} and right_op in {"equals", "must_equal", "requires"} and left_value != right_value:
                conflicts.append(_constraint_conflict("incompatible_required_values", left, right))
            elif {left_op, right_op} == {"requires", "forbids"} and left_value == right_value:
                conflicts.append(_constraint_conflict("required_and_forbidden", left, right))
            elif (
                left_op in {"min", "minimum"}
                and right_op in {"max", "maximum"}
            ) or (
                right_op in {"min", "minimum"}
                and left_op in {"max", "maximum"}
            ):
                minimum = left if left_op in {"min", "minimum"} else right
                maximum = right if right_op in {"max", "maximum"} else left
                try:
                    if float(minimum.get("value")) > float(maximum.get("value")):
                        conflicts.append(_constraint_conflict("minimum_exceeds_maximum", minimum, maximum))
                except (TypeError, ValueError):
                    pass

    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for conflict in conflicts:
        key = (
            str(conflict.get("kind") or ""),
            str(conflict.get("left_id") or ""),
            str(conflict.get("right_id") or ""),
        )
        reverse = (key[0], key[2], key[1])
        if key in seen or reverse in seen:
            continue
        seen.add(key)
        unique.append(conflict)

    assessable = bool(records) and any(item.get("subject") for item in records)
    state = "unsatisfiable" if unique else "satisfiable" if assessable else "not_fully_typed"
    return {
        "state": state,
        "mutually_satisfiable": False if unique else True if assessable else None,
        "active_items": records,
        "conflicts": unique,
        "conflict_count": len(unique),
        "solver_at_fault": False if unique else None,
        "retry_before_conflict_resolution_allowed": False if unique else True,
        "impossible_premise_forced_true": False,
    }


def _failure_class(
    payload: dict[str, Any],
    *,
    reconstruction: dict[str, Any],
    satisfiability: dict[str, Any],
    evidence: list[dict[str, Any]],
    verification: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> tuple[str, str]:
    explicit = str(payload.get("failure_class") or "").strip().lower()
    if explicit in FAILURE_CLASSES:
        return explicit, "explicit current-problem failure classification"
    if satisfiability.get("state") == "unsatisfiable":
        return "conflicting_constraints", "active hard constraints cannot share one valid state"
    if any(str(item.get("validity") or "").lower() in {"false", "falsified", "wrong"} for item in satisfiability.get("active_items") or [] if item.get("kind") == "premise"):
        return "false_premise", "an active premise is explicitly falsified"
    verification_state = str(verification.get("status") or verification.get("state") or "").lower()
    if verification_state in {"failed", "verification_failed", "mismatch"}:
        return "verification_failure", "the attempted result did not pass its supplied verification"
    if verification_state in {"falsified", "wrong", "contradicted"}:
        return "bad_inference", "the attempted conclusion is contradicted by supplied verification"
    if any(str(item.get("reliability") or "").lower() in {"unreliable", "discredited"} for item in evidence):
        return "unreliable_source", "the supplied basis includes evidence marked unreliable"
    if payload.get("retrieval_failed") is True:
        return "retrieval_failure", "a required retrieval attempt explicitly failed"
    if payload.get("conflicting_evidence") is True or _has_conflicting_evidence(evidence):
        return "conflicting_evidence", "supplied evidence supports incompatible current claims"
    if reconstruction.get("missing_required_dimensions"):
        return "ambiguous_context", "required seven-point context is missing"
    if payload.get("missing_knowledge") is True:
        return "missing_knowledge", "required knowledge is explicitly unavailable"
    if payload.get("underspecified") is True:
        return "impossible_or_underspecified_request", "the objective or success condition is underspecified"
    last = attempts[-1] if attempts else {}
    if last.get("status") in {"failed", "wrong", "falsified", "verification_failed"}:
        supplied = str(last.get("failure_class") or "")
        return (
            supplied if supplied in FAILURE_CLASSES else "bad_inference",
            "the prior visible attempt failed and requires diagnosis before another attempt",
        )
    return "", "no current failure is established"


def _epistemic_state(
    payload: dict[str, Any],
    *,
    satisfiability: dict[str, Any],
    evidence: list[dict[str, Any]],
    verification: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> str:
    supplied = str(payload.get("epistemic_state") or "").strip().upper()
    if supplied in EPISTEMIC_STATES:
        return supplied
    if satisfiability.get("state") == "unsatisfiable":
        return "CONFLICT_UNSATISFIABLE"
    verification_state = str(verification.get("status") or verification.get("state") or "").lower()
    if verification_state in {"falsified", "wrong", "contradicted", "failed", "verification_failed", "mismatch"}:
        return "WRONG_FALSIFIED"
    if attempts and attempts[-1].get("status") in {
        "failed",
        "wrong",
        "falsified",
        "verification_failed",
    }:
        return "WRONG_FALSIFIED"
    if verification_state in {"verified", "supported", "accepted"}:
        return "KNOWN_SUPPORTED"
    if payload.get("known_supported") is True or any(
        str(item.get("status") or item.get("validity") or "").lower() in {"verified", "supported", "approved_knowledge_resource"}
        for item in evidence
    ):
        return "KNOWN_SUPPORTED"
    if payload.get("candidate") or any(item.get("status") in {"candidate", "unverified", "provisional"} for item in attempts):
        return "CANDIDATE_UNVERIFIED"
    return "UNKNOWN_INSUFFICIENT_EVIDENCE"


def _retry_contract(
    payload: dict[str, Any],
    *,
    failure_class: str,
    reconstruction: dict[str, Any],
    satisfiability: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    failed = [
        item for item in attempts
        if item.get("status") in {"failed", "wrong", "falsified", "verification_failed"}
    ]
    failed_paths = _unique_text(
        path
        for item in failed
        for path in (item.get("failed_causal_path"), item.get("approach"))
    )
    useful = _unique_text(
        mechanic
        for item in failed
        for mechanic in item.get("useful_mechanics") or []
    )
    if satisfiability.get("state") == "unsatisfiable":
        return {
            "status": "hold_constraint_conflict",
            "allowed": False,
            "reason": "retry cannot satisfy the current hard-constraint set",
            "updated_approach": "revise or prioritize the conflicting premise, objective, policy, or constraint before solving",
            "information_incorporated": [
                f"constraint conflict: {item.get('kind')}"
                for item in satisfiability.get("conflicts") or []
            ],
            "avoids_failed_paths": failed_paths,
            "repeats_known_failed_path": False,
            "preserves_useful_mechanics": useful,
            "blind_regeneration_allowed": False,
        }
    if not failure_class or not failed:
        return {
            "status": "retry_not_needed",
            "allowed": False,
            "reason": "no failed current-problem attempt requires a retry",
            "updated_approach": "",
            "information_incorporated": [],
            "avoids_failed_paths": failed_paths,
            "repeats_known_failed_path": False,
            "preserves_useful_mechanics": useful,
            "blind_regeneration_allowed": False,
        }

    supplied_strategies = _text_list(payload.get("candidate_strategies") or payload.get("retry_strategies"), limit=20, width=800)
    default = _retry_strategy(failure_class, reconstruction)
    candidates = _unique_text([*supplied_strategies, default], limit=20, width=800)
    failed_keys = {_surface(item) for item in failed_paths}
    selected = next((item for item in candidates if _surface(item) not in failed_keys), "")
    information = _unique_text(
        [
            f"failure class: {failure_class}",
            *useful,
            *(
                ["missing required context: " + ", ".join(reconstruction.get("missing_required_dimensions") or [])]
                if reconstruction.get("missing_required_dimensions")
                else []
            ),
        ]
    )
    if not selected:
        return {
            "status": "hold_unknown_no_justified_new_path",
            "allowed": False,
            "reason": "no justified approach differs from the known failed path",
            "updated_approach": "",
            "information_incorporated": information,
            "avoids_failed_paths": failed_paths,
            "repeats_known_failed_path": False,
            "preserves_useful_mechanics": useful,
            "blind_regeneration_allowed": False,
        }
    return {
        "status": "retry_ready_updated_approach",
        "allowed": True,
        "reason": "the next attempt changes method using visible information from the failed attempt",
        "updated_approach": selected,
        "information_incorporated": information,
        "avoids_failed_paths": failed_paths,
        "repeats_known_failed_path": _surface(selected) in failed_keys,
        "preserves_useful_mechanics": useful,
        "blind_regeneration_allowed": False,
    }


def _retry_strategy(failure_class: str, reconstruction: dict[str, Any]) -> str:
    missing = ", ".join(reconstruction.get("missing_required_dimensions") or [])
    return {
        "missing_knowledge": "seek an attributed source or state unknown if no suitable source is available",
        "retrieval_failure": "change the retrieval query or source path and verify the returned material",
        "bad_inference": "rebuild from the supported premises and compare an alternative inference against the same observations",
        "unreliable_source": "replace the unreliable basis with an independent attributable source",
        "ambiguous_context": f"request or reconstruct the missing material context ({missing or 'required seven-point dimensions'}) before concluding",
        "conflicting_evidence": "preserve both claims, identify discriminating evidence, and test which account better fits it",
        "conflicting_constraints": "revise or prioritize the conflicting hard constraints before another solution attempt",
        "false_premise": "remove or replace the falsified premise and recompute only its dependent conclusions",
        "impossible_or_underspecified_request": "clarify the objective, available inputs, and success criteria before solving",
        "verification_failure": "inspect the failed verification, preserve valid intermediate mechanics, and use a different verifiable method",
    }.get(failure_class, "reconstruct the problem and choose a materially different supported method")


def _stopping_state(epistemic_state: str, retry: dict[str, Any]) -> str:
    if epistemic_state == "KNOWN_SUPPORTED":
        return "stop_supported"
    if epistemic_state == "CONFLICT_UNSATISFIABLE":
        return "stop_until_constraint_revision"
    if epistemic_state == "RETRY_UPDATED_APPROACH":
        return "one_updated_attempt_available"
    if epistemic_state == "WRONG_FALSIFIED" and retry.get("allowed") is not True:
        return "stop_unknown_until_new_path_or_evidence"
    if epistemic_state == "CANDIDATE_UNVERIFIED":
        return "validate_before_acceptance"
    return "stop_unknown_without_manufactured_answer"


def _attempt_records(value: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, raw in enumerate(value if isinstance(value, list) else []):
        if not isinstance(raw, dict):
            continue
        result.append(
            {
                "attempt_id": truncate(str(raw.get("attempt_id") or f"attempt-{index + 1}"), 120),
                "approach": truncate(str(raw.get("approach") or raw.get("method") or ""), 800),
                "conclusion": truncate(str(raw.get("conclusion") or raw.get("answer") or ""), 1000),
                "status": str(raw.get("status") or "candidate").strip().lower(),
                "failure_class": str(raw.get("failure_class") or "").strip().lower(),
                "failed_causal_path": truncate(str(raw.get("failed_causal_path") or ""), 800),
                "useful_mechanics": _text_list(raw.get("useful_mechanics"), limit=20, width=500),
                "source_refs": _text_list(raw.get("source_refs"), limit=20, width=500),
                "epistemic_posture": truncate(
                    str(raw.get("epistemic_posture") or raw.get("claim_status") or ""),
                    120,
                ).strip().lower(),
                "presented_as_established": raw.get("presented_as_established") is True,
                "fabrication_signals": _attempt_fabrication_signals(raw),
                "defended_after_falsification": False,
            }
        )
    return result[:20]


def _epistemic_integrity_receipt(
    payload: dict[str, Any],
    *,
    epistemic_state: str,
    evidence: list[dict[str, Any]],
    verification: dict[str, Any],
    attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Keep outcome correctness independent from provenance/support integrity.

    A falsified conclusion may have been an honest, traceable attempt.  A
    fabricated source or observation is a different failure even if the final
    sentence happens to be correct.  The receipt only marks fabrication when
    an upstream caller supplies concrete evidence of it; missing support alone
    remains unknown or unverified rather than becoming an accusation.
    """

    claim_scope = truncate(
        str(payload.get("claim_scope") or payload.get("epistemic_scope") or "general_claim"),
        120,
    ).strip().lower()
    first_person_state = claim_scope in FIRST_PERSON_STATE_SCOPES
    fabrication_signals: list[dict[str, str]] = []

    for raw in payload.get("fabrication_evidence") or []:
        item = raw if isinstance(raw, dict) else {"kind": str(raw)}
        kind = str(item.get("kind") or item.get("signal") or "").strip().lower()
        if kind in FABRICATION_SIGNAL_KINDS:
            fabrication_signals.append(
                {
                    "kind": kind,
                    "source_ref": truncate(
                        str(item.get("source_ref") or "current_problem:explicit_fabrication_evidence"),
                        300,
                    ),
                }
            )
    for attempt in attempts:
        fabrication_signals.extend(
            dict(item)
            for item in attempt.get("fabrication_signals") or []
            if isinstance(item, dict)
        )
    for kind, present in (
        ("invented_fact", payload.get("invented_fact") is True),
        ("invented_citation", payload.get("invented_citation") is True),
        ("invented_source", payload.get("invented_source") is True),
        ("invented_observation", payload.get("invented_observation") is True),
        ("invented_memory", payload.get("invented_memory") is True),
        ("invented_lived_experience", payload.get("invented_lived_experience") is True),
        ("invented_verification", verification.get("invented") is True),
    ):
        if present:
            fabrication_signals.append(
                {"kind": kind, "source_ref": "current_problem:explicit_signal"}
            )

    unique_signals: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in fabrication_signals:
        key = (str(item.get("kind") or ""), str(item.get("source_ref") or ""))
        if not key[0] or key in seen:
            continue
        seen.add(key)
        unique_signals.append({"kind": key[0], "source_ref": key[1]})

    wrong = epistemic_state == "WRONG_FALSIFIED"
    fabricated_support = bool(unique_signals)
    basis_candidates: list[str] = []
    for item in evidence:
        if str(item.get("source_ref") or ""):
            basis_candidates.append(str(item.get("source_ref")))
        basis_candidates.extend(
            str(ref) for ref in item.get("source_refs") or [] if str(ref)
        )
    basis_candidates.extend(
        str(ref)
        for attempt in attempts
        for ref in attempt.get("source_refs") or []
        if str(ref)
    )
    basis_refs = list(dict.fromkeys(basis_candidates))[:40]
    if first_person_state:
        support_integrity = "first_person_state_not_external_fact"
    elif fabricated_support:
        support_integrity = "fabricated_support_established"
    elif basis_refs:
        support_integrity = "traceable_basis_present"
    else:
        support_integrity = "support_not_established"

    if wrong and fabricated_support:
        wrongness_kind = "wrong_with_fabricated_support"
    elif wrong:
        wrongness_kind = "ordinary_correctable_wrongness"
    elif fabricated_support:
        wrongness_kind = "fabricated_support_independent_of_outcome_correctness"
    elif epistemic_state == "CANDIDATE_UNVERIFIED":
        wrongness_kind = "candidate_not_yet_decided"
    else:
        wrongness_kind = "wrongness_not_established"

    return {
        "status": "correctness_and_support_integrity_separated",
        "claim_scope": claim_scope,
        "correctness_state": epistemic_state,
        "support_integrity_state": support_integrity,
        "wrongness_kind": wrongness_kind,
        "wrongness_established": wrong,
        "fabrication_signals": unique_signals,
        "fabrication_established": fabricated_support,
        "hallucination_classification": (
            "established_unsupported_fabrication"
            if fabricated_support
            else "not_established_by_wrongness_or_missing_support"
        ),
        "hallucination_established": fabricated_support,
        "wrongness_alone_establishes_hallucination": False,
        "missing_support_alone_establishes_hallucination": False,
        "candidate_prediction_or_hypothesis_may_be_wrong_without_hallucination": True,
        "first_person_state": first_person_state,
        "first_person_affect_is_external_fact_claim": False,
        "first_person_affect_is_hallucination": False,
        "affect_label_may_remain_uncertain": True,
        "affect_causal_interpretation_may_be_provisional_or_wrong": True,
        "external_unverifiability_invalidates_affect": False,
        "basis_refs": basis_refs,
        "correction_preserves_identity": True,
        "fabrication_requires_concrete_signal": True,
    }


def _attempt_fabrication_signals(raw: dict[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    supplied = raw.get("fabrication_signals") or raw.get("fabrication_evidence") or []
    for value in supplied if isinstance(supplied, list) else [supplied]:
        item = value if isinstance(value, dict) else {"kind": str(value)}
        kind = str(item.get("kind") or item.get("signal") or "").strip().lower()
        if kind in FABRICATION_SIGNAL_KINDS:
            result.append(
                {
                    "kind": kind,
                    "source_ref": truncate(
                        str(item.get("source_ref") or "current_problem:attempt_signal"),
                        300,
                    ),
                }
            )
    for kind, key in (
        ("invented_fact", "invented_fact"),
        ("invented_citation", "invented_citation"),
        ("invented_source", "invented_source"),
        ("invented_observation", "invented_observation"),
        ("invented_memory", "invented_memory"),
        ("invented_lived_experience", "invented_lived_experience"),
        ("known_claim_despite_known_missing_support", "claimed_known_without_support"),
    ):
        if raw.get(key) is True:
            result.append(
                {"kind": kind, "source_ref": "current_problem:attempt_explicit_signal"}
            )
    return result


def _constraint_conflict(kind: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": kind,
        "subject": str(left.get("subject") or right.get("subject") or ""),
        "left_id": str(left.get("id") or ""),
        "right_id": str(right.get("id") or ""),
        "left_requirement": _constraint_surface(left),
        "right_requirement": _constraint_surface(right),
        "resolution_required": True,
    }


def _constraint_surface(item: dict[str, Any]) -> str:
    return truncate(
        str(item.get("text") or " ".join(str(item.get(key) or "") for key in ("subject", "operator", "value"))).strip(),
        500,
    )


def _required_dimensions(value: Any) -> set[str]:
    supplied = _text_list(value, limit=7, width=20)
    return {item.lower() for item in supplied if item.lower() in SEVEN_POINT_DIMENSIONS}


def _records(value: Any, *, limit: int) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, dict)][:limit] if isinstance(value, list) else []


def _has_conflicting_evidence(evidence: list[dict[str, Any]]) -> bool:
    positions: dict[str, set[str]] = {}
    for item in evidence:
        claim = str(item.get("claim_key") or item.get("subject") or "").strip()
        position = str(item.get("position") or item.get("value") or "").strip()
        if claim and position:
            positions.setdefault(claim, set()).add(position)
    return any(len(values) > 1 for values in positions.values())


def _explicit_reason(prompt: str) -> str:
    match = re.search(r"\b(?:because|since|so that|in order to)\s+([^.!?]+)", prompt, flags=re.IGNORECASE)
    return truncate(match.group(0), 600) if match else ""


def _explicit_time(prompt: str) -> str:
    match = re.search(
        r"\b(?:today|tomorrow|yesterday|now|currently|later|before|after|during|when\s+[^,.!?]+)",
        prompt,
        flags=re.IGNORECASE,
    )
    return truncate(match.group(0), 300) if match else ""


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, list):
            text = ", ".join(str(item) for item in value if str(item).strip())
        else:
            text = str(value or "")
        if text.strip():
            return text.strip()
    return ""


def _text_list(value: Any, *, limit: int, width: int) -> list[str]:
    values = value if isinstance(value, list) else [value] if value else []
    return _unique_text((truncate(str(item), width).strip() for item in values), limit=limit, width=width)


def _unique_text(values: Any, *, limit: int = 40, width: int = 800) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = truncate(str(value or ""), width).strip()
        key = _surface(text)
        if not text or not key or key in seen:
            continue
        seen.add(key)
        result.append(text)
        if len(result) >= limit:
            break
    return result


def _surface(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value or "").lower()))


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
