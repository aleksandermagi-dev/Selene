from __future__ import annotations

import re
from typing import Any

from .registry import truncate
from .semantic_arbitration import build_canonical_meaning_frame


CURRENT_CONTEXT_INFERENCE_BOUNDARY = (
    "visible_current_turn_and_session_premise_inference_only_no_external_fact_"
    "memory_identity_governance_personality_authority_training_or_action"
)

_HIGH_STAKES = re.compile(
    r"\b(?:diagnos|dose|medication|suicid|self-harm|legal advice|lawsuit|arrest|"
    r"investment|stock|bond|tax|electrical panel|live wire|weapon|explosive)\w*\b",
    re.IGNORECASE,
)
_EXTERNAL_FACT_REQUEST = re.compile(
    r"\b(?:according to|cite|citation|source|latest|current price|exact time|"
    r"who is|when did|where is|statistics?|research says|look up|search)\b",
    re.IGNORECASE,
)
_UNSUPPORTED_PRIOR_RESPONSE = re.compile(
    r"\b(?:not enough grounded|missing piece|cannot answer|can't answer|"
    r"do not have a grounded factual answer|need an attributed source)\b",
    re.IGNORECASE,
)


def build_current_context_inference(
    prompt: str,
    observations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build one modest inference from attributable visible premises.

    This is an answer-support bridge, not a general fact generator. It only
    admits low-stakes consequence or evaluation questions whose connecting
    relation is represented in the bounded affordance map below.
    """

    text = truncate(" ".join(str(prompt or "").split()), 2400).strip()
    lower = text.lower().replace("’", "'")
    frame = build_canonical_meaning_frame(text)
    request_kind = _request_kind(lower, frame)
    base = {
        "status": "current_context_inference_not_available",
        "eligible": False,
        "request_kind": request_kind,
        "premise_claims": [],
        "inference_claim": {},
        "canonical_meaning_frame": frame,
        "external_fact_claimed": False,
        "memory_write_active": False,
        "identity_change": False,
        "personality_change": False,
        "governance_change": False,
        "authority_change": False,
        "training_allowed": False,
        "lora_allowed": False,
        "autonomous_action_allowed": False,
        "provenance_boundary": CURRENT_CONTEXT_INFERENCE_BOUNDARY,
    }
    if _HIGH_STAKES.search(lower):
        return {**base, "reason": "high_stakes_question_requires_its_domain_owner"}
    if _EXTERNAL_FACT_REQUEST.search(lower):
        return {**base, "reason": "external_fact_request_requires_attributed_support"}
    if frame.get("selected_reading") == "literal_domain":
        return {**base, "reason": "literal_domain_question_requires_domain_support"}
    if not request_kind:
        return {**base, "reason": "no_bounded_current_context_inference_requested"}

    premises = _visible_premises(text, observations or [])
    relations = _matched_affordances(premises)
    if not relations:
        return {
            **base,
            "reason": "visible_premises_do_not_support_a_mapped_modest_inference",
            "premise_claims": premises,
        }

    selected = relations[:2]
    premise_ids = list(
        dict.fromkeys(
            premise_id
            for relation in selected
            for premise_id in relation["basis_claim_ids"]
        )
    )
    answer = _compose_answer(request_kind, selected)
    inference_text = " ".join(relation["inference"] for relation in selected)
    units = [
        *[
            {
                "id": f"current_context_inference_{index + 1}",
                "role": "answer" if index == 0 else "conclusion",
                "relation": "support" if index == 0 else "conclusion",
                "subject": relation["subject"],
                "predicate": relation["predicate"],
                "object": relation["object"],
                "modality": relation["modality"],
                "source_kind": "current_session_observation",
                "source_refs": relation["basis_claim_ids"],
                "supported": True,
                "meaning_keys": [relation["meaning_key"]],
            }
            for index, relation in enumerate(selected)
        ],
    ]
    return {
        **base,
        "status": "current_context_inference_ready",
        "eligible": True,
        "reason": "visible_premises_support_a_modest_low_stakes_inference",
        "answer": answer,
        "answer_kind": "grounded_current_context_inference",
        "support_basis": "current_prompt_and_recent_conversation",
        "missing_variable": selected[0]["what_would_change"],
        "premise_claims": premises,
        "inference_relations": selected,
        "inference_claim": {
            "claim_id": "current-context-inference-1",
            "claim_type": "inference",
            "text": inference_text,
            "basis_claim_ids": premise_ids,
            "confidence": "bounded_from_visible_premises",
            "what_would_change": [item["what_would_change"] for item in selected],
            "source_category": "current_visible_context",
        },
        "semantic_units": units,
        "inference_is_source_statement": False,
        "ordinary_wrongness_is_correctable": True,
    }


def _request_kind(lower: str, frame: dict[str, Any]) -> str:
    constructions = {
        str(item.get("selected_sense") or "")
        for item in frame.get("pragmatic_constructions") or []
        if isinstance(item, dict)
    }
    if "request_for_evaluation" in constructions:
        return "evaluation"
    if re.search(
        r"\b(?:what|which)(?: (?:is|would be))?(?: (?:one|a|the))? (?:practical )?(?:difference|benefit|advantage)\b|"
        r"\bwhat does (?:that|this|it) (?:change|help|improve|make easier)\b|"
        r"\bwhy is (?:that|this|it) (?:useful|helpful|better)\b|"
        r"\bso what (?:follows|changes|does that mean)\b",
        lower,
    ):
        return "practical_consequence"
    return ""


def _visible_premises(prompt: str, observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[tuple[str, str, str, bool]] = []
    for index, item in enumerate(observations[-16:]):
        if not isinstance(item, dict):
            continue
        value = truncate(
            str(item.get("observation") or item.get("preview") or item.get("text") or ""),
            900,
        ).strip()
        if not value or _UNSUPPORTED_PRIOR_RESPONSE.search(value):
            continue
        role = str(item.get("source_role") or item.get("role") or "unspecified")
        explicitly_eligible = item.get("premise_eligible") is True
        if role in {"selene", "assistant"} and not explicitly_eligible:
            continue
        candidates.append((f"current-context-observation-{index + 1}", value, role, False))
    candidates.append(("current-context-prompt", prompt, "user", True))

    premises: list[dict[str, Any]] = []
    seen: set[str] = set()
    for claim_id, value, role, current in candidates:
        normalized = " ".join(value.lower().replace("’", "'").split())
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        premises.append(
            {
                "claim_id": claim_id,
                "claim_type": "current_turn_statement" if current else "session_statement",
                "text": value,
                "source_role": role,
                "source_category": "current_prompt" if current else "current_session_context",
                "reported_not_independently_verified": True,
            }
        )
    return premises[-12:]


def _matched_affordances(premises: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for premise in reversed(premises):
        text = str(premise.get("text") or "")
        lower = " ".join(text.lower().replace("’", "'").split())
        claim_id = str(premise.get("claim_id") or "")
        if re.search(r"\b(?:quieter|less noisy|reduced noise|lower noise)\b", lower):
            matches.append(
                _relation(
                    claim_id,
                    "A quieter workspace has less competing noise, which should make the active work easier to focus on.",
                    "The visible premise describes the workspace as quieter.",
                    "quieter workspace supports easier focus",
                    "whether the remaining sounds are still distracting in practice",
                    subject="a quieter workspace with less competing noise",
                    predicate="make",
                    obj="the active work easier to focus on",
                    modality="should",
                    basis_object="the workspace as quieter",
                )
            )
        if re.search(r"\b(?:less cluttered|uncluttered|clearer workspace|cleared workspace|less crowded)\b", lower):
            matches.append(
                _relation(
                    claim_id,
                    "A less cluttered workspace should make the active material easier to find and work with.",
                    "The visible premise says the workspace has less competing clutter.",
                    "less clutter supports easier navigation",
                    "whether the remaining layout still hides or obstructs the active material",
                    subject="a less cluttered workspace",
                    predicate="make",
                    obj="the active material easier to find and work with",
                    modality="should",
                    basis_object="the workspace as having less competing clutter",
                )
            )
        if re.search(r"\b(?:organized|sorted|labelled|labeled|clearly grouped)\b", lower):
            matches.append(
                _relation(
                    claim_id,
                    "Organized material should be easier to distinguish and retrieve.",
                    "The visible premise says the material is organized, sorted, labeled, or clearly grouped.",
                    "organization supports retrieval",
                    "whether the organization matches how the material is actually used",
                    subject="the stated organization",
                    predicate="make",
                    obj="the relevant items easier to distinguish and retrieve",
                    modality="should",
                    basis_object="the material as organized sorted labeled or clearly grouped",
                )
            )
        if re.search(
            r"\b(?:records?|files?|notes?|material)\b.{0,45}\b(?:safe|preserved|protected|intact|available)\b|"
            r"\b(?:safe|preserved|protected|intact|available)\b.{0,45}\b(?:records?|files?|notes?|material)\b",
            lower,
        ):
            matches.append(
                _relation(
                    claim_id,
                    "Keeping the important records safe means the cleanup can improve the working area without sacrificing access to that material.",
                    "The visible premise says the important records or material remain safe and available.",
                    "preservation supports continuity through change",
                    "evidence that an important item was removed, damaged, or made inaccessible",
                    subject="keeping the important records safe during the cleanup",
                    predicate="improve",
                    obj="the working area without sacrificing access to important material",
                    modality="can",
                    basis_object="the important records or material as safe and available",
                )
            )
        if re.search(r"\b(?:more open space|more free space|clearer surface|cleared surface)\b", lower):
            matches.append(
                _relation(
                    claim_id,
                    "More open working space should make more of the area directly usable.",
                    "The visible premise says the usable surface or space is more open.",
                    "open space supports direct use",
                    "whether the cleared area is actually reachable and suited to the task",
                    subject="more open working space",
                    predicate="make",
                    obj="more of the working area directly usable",
                    modality="should",
                    basis_object="the usable surface or space as more open",
                )
            )
    unique: list[dict[str, Any]] = []
    keys: set[str] = set()
    for item in matches:
        if item["meaning_key"] in keys:
            continue
        keys.add(item["meaning_key"])
        unique.append(item)
    return unique


def _relation(
    claim_id: str,
    inference: str,
    basis_summary: str,
    meaning_key: str,
    what_would_change: str,
    *,
    subject: str,
    predicate: str,
    obj: str,
    modality: str,
    basis_object: str,
) -> dict[str, Any]:
    return {
        "inference": inference,
        "basis_summary": basis_summary,
        "meaning_key": meaning_key,
        "basis_claim_ids": [claim_id],
        "what_would_change": what_would_change,
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "modality": modality,
        "basis_object": basis_object,
    }


def _compose_answer(request_kind: str, relations: list[dict[str, Any]]) -> str:
    claims = [str(item["inference"]).strip() for item in relations]
    if request_kind == "evaluation":
        first = claims[0]
        first = "It sounds like a useful improvement: " + first[0].lower() + first[1:]
        claims[0] = first
    return " ".join(claims)
