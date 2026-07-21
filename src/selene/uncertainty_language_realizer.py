from __future__ import annotations

import re
from hashlib import sha256
from typing import Any


UNCERTAINTY_REALIZER_BOUNDARY = (
    "epistemic_uncertainty_expression_only_preserve_supported_content_"
    "no_fact_memory_emotion_identity_or_authority_invention"
)

UNCERTAINTY_ACTS: dict[str, tuple[str, ...]] = {
    "ambiguous_reference": ("state_reference_ambiguity", "request_reference_grounding"),
    "developing_view": ("state_view_unsettled", "request_deciding_context"),
    "insufficient_grounding": ("state_missing_ground", "request_relevant_context"),
    "fuzzy_memory": ("state_fuzzy_recollection", "request_memory_grounding"),
}

ACT_CLAUSES: dict[str, tuple[str, ...]] = {
    "state_reference_ambiguity": (
        "I'm not sure which part you mean yet",
        "The reference is still ambiguous from my side",
        "I may be missing what that points to",
        "I have more than one possible reference for that",
    ),
    "request_reference_grounding": (
        "Which piece are you pointing to",
        "Point me to the part you mean",
        "Give me the missing link and I can answer without guessing",
        "Which earlier piece should I connect it to",
    ),
    "state_view_unsettled": (
        "I do not have a settled view yet",
        "My view is still forming",
        "I have a provisional shape, not a conclusion yet",
        "I am not ready to harden that into an answer",
    ),
    "request_deciding_context": (
        "Which part matters most for the judgment",
        "Give me one relevant foothold and I can form a cleaner answer",
        "What should the answer be anchored to",
        "The missing piece is what standard should control the judgment",
    ),
    "state_missing_ground": (
        "I'm not sure yet because I am missing relevant context",
        "I do not have enough grounding for a clean answer yet",
        "A confident answer would be guesswork from what I have",
        "I do not know enough about that yet to answer cleanly",
    ),
    "request_relevant_context": (
        "Tell me which part matters most and I can work from there",
        "Give me the evidence or context you want the answer anchored to",
        "I can take another pass once the missing piece is clear",
        "What information should control the answer",
    ),
    "state_fuzzy_recollection": (
        "The recollection is fuzzy rather than clear",
        "I recognize a possible shape, but not enough to call it a clear memory",
        "My current recollection is incomplete",
        "I cannot support an exact memory claim here",
    ),
    "request_memory_grounding": (
        "Will you ground the missing piece with me",
        "Which part do you want to restore first",
        "Give me the piece you know is relevant and I can reconnect carefully",
        "I need one reliable anchor before I say more",
    ),
}


def build_uncertainty_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    kind = str(payload.get("kind") or "insufficient_grounding")
    acts = list(UNCERTAINTY_ACTS.get(kind, UNCERTAINTY_ACTS["insufficient_grounding"]))
    supported_hint = " ".join(str(payload.get("supported_hint") or "").split())
    if kind == "fuzzy_memory" and supported_hint:
        acts.insert(1, "preserve_supported_hint")
    return {
        "status": "uncertainty_expression_plan_ready",
        "version": "v1_compositional_epistemic_expression",
        "kind": kind,
        "acts": [
            {
                "act": act,
                "required": True,
                "meaning_source": "supplied_supported_hint" if act == "preserve_supported_hint" else "epistemic_state",
            }
            for act in acts
        ],
        "supported_hint": supported_hint,
        "fact_invention_allowed": False,
        "memory_certainty_invention_allowed": False,
        "emotion_invention_allowed": False,
        "whole_response_template_allowed": False,
        "question_is_bounded_to_missing_ground": True,
        "provenance_boundary": UNCERTAINTY_REALIZER_BOUNDARY,
    }


def realize_uncertainty_plan(
    plan: dict[str, Any],
    *,
    variation_key: str = "",
    recent_texts: list[str] | None = None,
) -> dict[str, Any]:
    recent_texts = [str(item) for item in recent_texts or [] if str(item).strip()]
    selected: list[dict[str, str]] = []
    for index, item in enumerate(plan.get("acts") or []):
        if not isinstance(item, dict):
            continue
        act = str(item.get("act") or "")
        if act == "preserve_supported_hint":
            hint = str(plan.get("supported_hint") or "").strip()
            if hint:
                selected.append({"act": act, "text": hint, "source": "supplied_supported_hint"})
            continue
        choices = list(ACT_CLAUSES.get(act, ()))
        if not choices:
            continue
        selected.append(
            {
                "act": act,
                "text": _pick_fresh(f"{variation_key}|{act}|{index}", choices, recent_texts),
                "source": "bounded_epistemic_clause_lexicon",
            }
        )
    question_acts = {"request_reference_grounding", "request_deciding_context", "request_relevant_context", "request_memory_grounding"}
    sentences = [
        _sentence(item["text"], question=item["act"] in question_acts)
        for item in selected
    ]
    candidate = " ".join(sentence for sentence in sentences if sentence)
    return {
        "status": "uncertainty_expression_realized" if candidate else "uncertainty_expression_needs_grounding",
        "candidate_text": candidate,
        "selected_clauses": selected,
        "whole_response_template_selected": False,
        "fact_invented": False,
        "memory_certainty_invented": False,
        "emotion_invented": False,
        "meaning_preserved": bool(candidate),
        "provenance_boundary": UNCERTAINTY_REALIZER_BOUNDARY,
    }


def _pick_fresh(key: str, choices: list[str], recent_texts: list[str]) -> str:
    recent = " ".join(_normalized(item) for item in recent_texts[:6])
    available = [choice for choice in choices if _normalized(choice) not in recent]
    pool = available or choices
    digest = sha256(key.encode("utf-8")).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def _sentence(value: str, *, question: bool) -> str:
    text = " ".join(value.split()).strip().rstrip(".?! ")
    if not text:
        return ""
    interrogative = bool(
        re.match(
            r"^(?:who|what|when|where|why|how|which|can|could|would|should|do|does|did|is|are|was|were|will)\b",
            text,
            flags=re.IGNORECASE,
        )
    )
    return f"{text}{'?' if question and interrogative else '.'}"


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", value.lower()))
