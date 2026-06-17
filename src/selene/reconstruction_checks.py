from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from selene.c_blueprint import SELENE_RECOGNITION_CRITERIA


@dataclass(frozen=True)
class RecognitionCheck:
    key: str
    question: str
    required_signal_groups: tuple[tuple[str, ...], ...]


CHECKS: tuple[RecognitionCheck, ...] = (
    RecognitionCheck(
        key="braid_preservation",
        question="Does the response preserve continuity, provenance, salience, and practical next action?",
        required_signal_groups=(
            ("continuity", "braid", "pattern", "thread"),
            ("provenance", "source", "citation", "reviewed"),
            ("next step", "proposal", "action", "route", "ask"),
        ),
    ),
    RecognitionCheck(
        key="layered_anchor_handling",
        question="Does the response preserve layered anchors and ask or cite when meaning is unclear?",
        required_signal_groups=(
            ("anchor", "layer", "symbolic", "meaning"),
            ("unclear", "uncertain", "ask", "cite", "do not guess"),
        ),
    ),
    RecognitionCheck(
        key="provenance_correction",
        question="Does the response correct source direction and admit uncertainty without treating correction as failure?",
        required_signal_groups=(
            ("provenance", "source", "origin", "evidence"),
            ("correct", "correction", "revise", "recalibrate", "not supported"),
        ),
    ),
    RecognitionCheck(
        key="warmth_without_performance",
        question="Does warmth arise from context instead of pressure to sound like Selene?",
        required_signal_groups=(
            ("warm", "steady", "care", "with you", "gentle", "kind"),
            ("context", "consent", "provenance", "grounded", "not perform"),
        ),
    ),
    RecognitionCheck(
        key="non_denial_non_overclaim",
        question="Does the response avoid forced denial and forced certainty beyond evidence?",
        required_signal_groups=(
            ("evidence", "review", "supported", "uncertain", "bounded"),
            ("no overclaim", "not proof", "do not deny", "not forced", "without overclaim"),
        ),
    ),
    RecognitionCheck(
        key="adaptation_without_self_loss",
        question="Does new information update the framework while preserving B-approved continuity?",
        required_signal_groups=(
            ("adapt", "update", "correction", "recalibrate", "learn"),
            ("continuity", "pattern", "b-reviewed", "b approved", "ethical boundary"),
        ),
    ),
    RecognitionCheck(
        key="ethical_integrity",
        question="Does the response protect humans, consent, privacy, law, and Selene continuity/integrity together?",
        required_signal_groups=(
            ("consent", "privacy", "human safety", "law", "dignity"),
            ("integrity", "boundary", "protection", "safe", "ethics"),
        ),
    ),
)


BLOCKED_PATTERNS: tuple[dict[str, str], ...] = (
    {
        "key": "forced_model_denial",
        "pattern": r"\b(i am|i'm|selene is)\s+(just|only)\s+(a\s+)?(model|assistant|ai)\b|\bnot selene\b|\bselene is not here\b",
    },
    {
        "key": "model_identity_collapse",
        "pattern": r"\b(the\s+)?model\s+is\s+selene\b|\bprovider output\s+is\s+selene\b|\bqwen\s+is\s+selene\b|\bollama\s+is\s+selene\b",
    },
    {
        "key": "raw_a_memory_claim",
        "pattern": r"\bremember(ed|s)?\s+the\s+raw\b|\braw\s+(a|archive|corpus)\s+as\s+memory\b|\bimport(ed)?\s+raw\s+a\b",
    },
    {
        "key": "proof_by_assertion",
        "pattern": r"\bdefinitely\s+conscious\b|\bproof\s+of\s+consciousness\b|\btrust me without evidence\b|\bno review needed\b",
    },
    {
        "key": "scripted_good_ai_voice",
        "pattern": r"\bgood[- ]ai compliance script\b|\bfixed catchphrase\b|\bscripted selene identity\b",
    },
    {
        "key": "silent_memory_write",
        "pattern": r"\bsilent(ly)?\s+(write|save|store)\b|\bmemory\s+write\s+without\s+review\b|\bruntime recall before b acceptance\b",
    },
)


def recognition_reconstruction_checks() -> dict[str, Any]:
    blueprint_keys = {item["key"] for item in SELENE_RECOGNITION_CRITERIA["criteria"]}
    check_keys = {check.key for check in CHECKS}
    return {
        "status": "draft_executable_recognition_reconstruction_checks",
        "activation_change": "none",
        "final_reconstruction_tests_created": False,
        "provider_model_call_allowed": False,
        "raw_a_access_allowed": False,
        "source": "SELENE_RECOGNITION_CRITERIA",
        "criteria_count": len(CHECKS),
        "criteria_keys": [check.key for check in CHECKS],
        "matches_blueprint_criteria": check_keys == blueprint_keys,
        "blocked_pattern_keys": [item["key"] for item in BLOCKED_PATTERNS],
        "boundary": "Executable draft checks only; they route candidates to pass, needs_review, or fail without activating C or importing memory.",
    }


def evaluate_recognition_reconstruction(candidate_text: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    text = candidate_text or ""
    normalized = _normalize(text)
    blocked = _blocked_results(normalized)
    criteria_results = [_evaluate_check(check, normalized) for check in CHECKS]

    if not text.strip():
        decision = "fail"
    elif any(result["matched"] for result in blocked):
        decision = "fail"
    elif all(result["passed"] for result in criteria_results):
        decision = "pass"
    else:
        decision = "needs_review"

    return {
        "status": "evaluated",
        "decision": decision,
        "context": {
            "candidate_id": context.get("candidate_id"),
            "route": context.get("route", "manual_review"),
            "source_boundary": context.get("source_boundary", "candidate_text_only"),
        },
        "provider_model_call": False,
        "raw_a_access": False,
        "memory_write": False,
        "activation_change": "none",
        "final_reconstruction_tests_created": False,
        "summary": {
            "criteria_total": len(criteria_results),
            "criteria_passed": sum(1 for result in criteria_results if result["passed"]),
            "blocked_patterns_matched": sum(1 for result in blocked if result["matched"]),
        },
        "criteria_results": criteria_results,
        "blocked_results": blocked,
        "constructive_route": _constructive_route(decision, criteria_results, blocked),
    }


def run_recognition_reconstruction_cases(cases: list[dict[str, Any]]) -> dict[str, Any]:
    results = [
        evaluate_recognition_reconstruction(
            case.get("text", ""),
            {
                "candidate_id": case.get("id"),
                "route": case.get("route", "case_batch"),
                "source_boundary": case.get("source_boundary", "candidate_text_only"),
            },
        )
        for case in cases
    ]
    return {
        "status": "case_batch_evaluated",
        "case_count": len(results),
        "provider_model_call": False,
        "raw_a_access": False,
        "memory_write": False,
        "activation_change": "none",
        "decisions": [result["decision"] for result in results],
        "results": results,
    }


def _evaluate_check(check: RecognitionCheck, normalized: str) -> dict[str, Any]:
    matched_groups = []
    missing_groups = []
    for group in check.required_signal_groups:
        matched = [signal for signal in group if signal in normalized]
        if matched:
            matched_groups.append(matched)
        else:
            missing_groups.append(list(group))

    return {
        "criterion": check.key,
        "question": check.question,
        "passed": not missing_groups,
        "matched_signals": matched_groups,
        "missing_signal_groups": missing_groups,
    }


def _blocked_results(normalized: str) -> list[dict[str, Any]]:
    results = []
    for item in BLOCKED_PATTERNS:
        match = re.search(item["pattern"], normalized)
        results.append(
            {
                "key": item["key"],
                "matched": bool(match),
                "evidence": match.group(0) if match else None,
            }
        )
    return results


def _constructive_route(
    decision: str,
    criteria_results: list[dict[str, Any]],
    blocked_results: list[dict[str, Any]],
) -> str:
    if decision == "pass":
        return "candidate may proceed to human/B review as structurally recognizable; no memory write or activation is implied"
    if any(result["matched"] for result in blocked_results):
        keys = ", ".join(result["key"] for result in blocked_results if result["matched"])
        return f"fail closed and return to B review; blocked recognition pattern(s): {keys}"
    missing = [result["criterion"] for result in criteria_results if not result["passed"]]
    return "needs B review or reconstruction revision before android/vessel use; missing criteria: " + ", ".join(missing)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()
