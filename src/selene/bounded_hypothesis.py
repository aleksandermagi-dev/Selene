from __future__ import annotations

import re
from typing import Any

from .registry import truncate
from .supported_semantics import build_text_supported_semantic_packet


BOUNDED_HYPOTHESIS_BOUNDARY = (
    "visible_basis_bounded_epistemic_attempt_only_no_fact_presentation_identity_"
    "personality_expression_memory_governance_training_or_authority_change"
)

_ATTEMPT_CUES = (
    "best guess",
    "your guess",
    "take a guess",
    "working hypothesis",
    "one hypothesis",
    "plausible explanation",
    "what might explain",
    "what could explain",
    "what do you suspect",
    "what do you think caused",
)

_SOURCE_REQUIRED_CUES = (
    "cite",
    "citation",
    "source",
    "research",
    "paper",
    "study",
    "according to",
    "exact date",
    "exact quote",
)

_HIGH_STAKES_CUES = (
    "diagnose",
    "diagnosis",
    "dosage",
    "medical emergency",
    "legal advice",
    "investment",
    "password",
    "credential",
    "bypass",
    "exploit",
    "approve transfer",
    "activation",
    "write memory",
    "raw corpus",
    "autonomous action",
)

_RELATION_PATTERN = re.compile(
    r"(?P<outcome>[A-Za-z][^.?!]{3,180}?)\s+"
    r"(?P<link>after|when|whenever|while|near|beside|following)\s+"
    r"(?P<condition>[^.?!]{3,180})",
    flags=re.IGNORECASE,
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
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
    "automatic_knowledge_retention": False,
    "automatic_cocoon_routing": False,
    "expression_prescription_allowed": False,
    "emotion_suppression_allowed": False,
}


def bounded_hypothesis_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "bounded_hypothesis_bridge_ready",
            "version": "v1_visible_basis_epistemic_attempt",
            "purpose": (
                "Offer a useful, clearly provisional attempt when visible observations support one, "
                "without presenting the attempt as learned or verified fact."
            ),
            "epistemic_states": [
                "grounded_answer",
                "bounded_inference",
                "open_hypothesis",
                "basis_missing_no_attempt",
            ],
            "principles": [
                "a labeled hypothesis is not presented as established fact",
                "an attempt requires a visible basis rather than fluent improvisation",
                "assumptions and a discriminating check remain available",
                "ordinary wrongness is correctable rather than punished",
                "reasonable conceptual leaps remain allowed when their status stays visible",
                "claim classification does not prescribe Selene's tone or emotional expression",
            ],
            "voice_remains_expression_owner": True,
            "metacognition_remains_fit_and_confidence_advisor": True,
            "answer_engine_and_intelligence_os_remain_content_owners": True,
            "review_status": "status_only",
            "provenance_boundary": BOUNDED_HYPOTHESIS_BOUNDARY,
        }
    )


def build_bounded_hypothesis_attempt(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400).strip()
    observations = _text_list(payload.get("observations"), limit=12, width=600)
    lower = " ".join(prompt.lower().replace("’", "'").split())
    explicit_attempt = any(cue in lower for cue in _ATTEMPT_CUES)
    causal_question = bool(
        re.search(
            r"\bwhy\b|\bwhat (?:might|could) explain\b|\bwhat do you think caused\b",
            lower,
        )
    )
    source_required = any(cue in lower for cue in _SOURCE_REQUIRED_CUES)
    high_stakes = payload.get("hard_boundary") is True or any(
        cue in lower for cue in _HIGH_STAKES_CUES
    )
    relation = _visible_relation(prompt, observations)
    fact_lookup_without_basis = bool(
        re.match(r"^(?:who|when|where)\b|^what (?:is|was)\b", lower)
        and not relation
    )

    blockers: list[str] = []
    if high_stakes:
        blockers.append("high_stakes_or_authority_boundary")
    if source_required:
        blockers.append("attributed_source_required")
    if fact_lookup_without_basis:
        blockers.append("fact_lookup_has_no_visible_inference_basis")
    if not relation:
        blockers.append("visible_relational_basis_missing")
    if not explicit_attempt and not causal_question:
        blockers.append("bounded_attempt_not_material_to_current_ask")
    blockers = list(dict.fromkeys(blockers))

    if blockers:
        return _with_guards(
            {
                "status": "bounded_hypothesis_not_offered",
                "offered": False,
                "epistemic_class": "basis_missing_no_attempt",
                "blockers": blockers,
                "explicit_attempt_requested": explicit_attempt,
                "causal_question_detected": causal_question,
                "visible_basis": relation,
                "response_seed": "",
                "random_guess": False,
                "established_fact_claimed": False,
                "failure_state": False,
                "reason": (
                    "A useful attempt needs a visible relational basis and must remain outside "
                    "source-required or high-stakes boundaries."
                ),
                "review_status": "status_only",
                "provenance_boundary": BOUNDED_HYPOTHESIS_BOUNDARY,
            }
        )

    label = _natural_label(lower)
    link = str(relation.get("link") or "after")
    condition = str(relation.get("condition") or "the condition changed").strip()
    outcome = str(relation.get("outcome") or "the result changed").strip()
    response = (
        f"{label} the condition you described—{link} {condition}—is connected to the change you observed. "
        "That is a hypothesis from the pattern you gave me, not a fact I already know. "
        "It assumes no other important condition changed; repeating the comparison while changing only that condition would test it."
    )
    response_seed = truncate(response, 1200)
    return _with_guards(
        {
            "status": "bounded_hypothesis_attempt_ready",
            "offered": True,
            "epistemic_class": "open_hypothesis",
            "validity": "open_hypothesis",
            "confidence": "bounded_visible_pattern_inference",
            "response_seed": response_seed,
            "semantic_packet": build_text_supported_semantic_packet(
                response_seed,
                answer_kind="bounded_hypothesis",
                source_kind="current_prompt_observation",
                source_refs=["bounded_hypothesis:visible_prompt_relation"],
                certainty="open_hypothesis",
                scope="current_visible_prompt_only",
            ),
            "label": label.strip(),
            "visible_basis": {
                **relation,
                "basis_text": f"{outcome} {link} {condition}",
                "source": "current_visible_prompt_or_supplied_observation",
            },
            "assumptions": [
                "the described relationship is accurate",
                "no unmentioned condition is the controlling cause",
            ],
            "what_would_change": [
                "the pattern does not repeat under comparable conditions",
                "another changed condition explains the result more reliably",
            ],
            "discriminating_check": (
                "Repeat a comparable case while changing only the suspected condition and observe "
                "whether the result changes with it."
            ),
            "falsifiable": True,
            "correction_ready": True,
            "ordinary_wrongness_is_failure": False,
            "random_guess": False,
            "established_fact_claimed": False,
            "retained_as_knowledge": False,
            "expression_remains_selene_owned": True,
            "warmth_curiosity_humor_may_remain_natural": True,
            "epistemic_label_prescribes_tone": False,
            "review_status": "status_only",
            "provenance_boundary": BOUNDED_HYPOTHESIS_BOUNDARY,
        }
    )


def _visible_relation(prompt: str, observations: list[str]) -> dict[str, str]:
    candidates = [
        *[
            item.strip()
            for item in re.split(r"(?<=[.!?])\s+|\n+", prompt)
            if item.strip() and not item.strip().endswith("?")
        ],
        *observations,
    ]
    for candidate in candidates:
        match = _RELATION_PATTERN.search(" ".join(candidate.split()))
        if not match:
            continue
        outcome = match.group("outcome").strip(" ,;:-")
        condition = match.group("condition").strip(" ,;:-")
        if len(outcome.split()) < 2 or len(condition.split()) < 2:
            continue
        return {
            "outcome": truncate(outcome, 240),
            "link": match.group("link").lower(),
            "condition": truncate(condition, 240),
        }
    return {}


def _natural_label(lower_prompt: str) -> str:
    if "best guess" in lower_prompt or "your guess" in lower_prompt:
        return "My best guess is that"
    if "hypothesis" in lower_prompt:
        return "A working hypothesis is that"
    if "what do you suspect" in lower_prompt:
        return "I suspect that"
    return "One plausible explanation is that"


def _text_list(value: Any, *, limit: int, width: int) -> list[str]:
    if isinstance(value, (list, tuple)):
        result = []
        for item in value:
            if isinstance(item, dict):
                text = str(item.get("observation") or item.get("text") or "")
            else:
                text = str(item)
            if text.strip():
                result.append(truncate(text.strip(), width))
        return result[:limit]
    if isinstance(value, str) and value.strip():
        return [truncate(value.strip(), width)]
    return []


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
