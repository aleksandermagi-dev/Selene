from __future__ import annotations

import re
from typing import Any

from .registry import truncate


ANSWER_SUBSTANCE_BOUNDARY = (
    "prompt_grounded_answer_substance_only_no_external_fact_invention_memory_identity_governance_or_action"
)

_STOP_WORDS = {
    "a", "about", "and", "are", "as", "at", "be", "but", "can", "could", "do", "does", "for",
    "from", "how", "i", "if", "in", "is", "it", "me", "my", "of", "on", "or", "please", "should",
    "so", "that", "the", "this", "to", "we", "what", "when", "where", "which", "who", "why", "will",
    "with", "would", "you", "your",
}


def build_answer_substance(
    prompt: str,
    observations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    text = truncate(str(prompt or "").strip(), 2400)
    lower = " ".join(text.lower().replace("’", "'").split())
    topics = _topic_terms(text)
    topic = " ".join(topics[:6]) or "the question"
    answer = ""
    kind = "unsupported_fact"
    missing_variable = "the specific claim or observation the answer must fit"
    support_basis = "current_prompt_only"

    comparison = any(marker in lower for marker in ("compare", "difference", "versus", " vs ", "tradeoff", "trade-off", "which option"))
    ordering = any(marker in lower for marker in ("come first", "do first", "start with", "begin with", "priority", "prioritize"))
    planning = any(marker in lower for marker in ("how should", "what should", "plan", "strategy", "next step", "where do we start"))
    consequence = bool(re.match(r"^what happens if\b", lower))
    viewpoint = any(marker in lower for marker in ("what do you think", "what is your view", "what's your view", "your thoughts"))
    why_before = re.search(r"\bwhy\s+(?:does|do|should|is|are)\s+(.{2,100}?)\s+(?:come\s+)?before\s+(.{2,100}?)(?:[?.]|$)", lower)
    limited_resource = re.search(r"\blimited\s+([a-z][a-z-]*)(?:\s+and|\s+but|[,.])", lower)
    paired_goals = re.search(
        r"\bsupport\s+both\s+([a-z][a-z -]{1,60}?)\s+and\s+([a-z][a-z -]{1,60}?)(?:[.?,]|$)",
        lower,
    )

    if viewpoint and any(marker in lower for marker in ("reversible step", "reversible first", "smallest reversible")):
        answer = (
            "I think that is a sound default when uncertainty is high: a small reversible step limits the cost of being wrong and produces evidence for the next choice. "
            "It should not override a known prerequisite, safety constraint, or already-settled evidence."
        )
        kind = "bounded_viewpoint"
        missing_variable = "whether a prerequisite or non-negotiable constraint overrides reversibility"
    elif viewpoint:
        answer = (
            "My current read is that the idea is worth examining, but I would separate what we have observed from what we are inferring before settling on it. "
            "The part that would sharpen my view is the consequence you most want the idea to explain."
        )
        kind = "bounded_viewpoint"
        missing_variable = "the consequence the idea is meant to explain"
    elif consequence and any(marker in lower for marker in ("reverse the order", "reversed the order", "change the order", "swap the order")):
        answer = (
            "Reversing the order works only if the later step does not depend on an output from the earlier one. "
            "If that dependency exists, the reversed sequence removes a required input; if it does not, compare which order gives clearer evidence with less irreversible cost."
        )
        kind = "conditional_dependency_answer"
        missing_variable = "whether either step depends on an output from the other"
    elif consequence:
        answer = (
            "Treat that as a conditional change: identify what the changed part feeds, which assumptions depend on it, and what observable result should differ. "
            "That gives us a prediction to check instead of a consequence invented from wording alone."
        )
        kind = "conditional_consequence_method"
        missing_variable = "the downstream dependency and observable prediction"
    elif why_before:
        first = why_before.group(1).strip(" ,")
        second = why_before.group(2).strip(" ,")
        answer = (
            f"Putting {first} before {second} preserves the input before the later step can reshape it. "
            "That makes the result easier to trace, test, and correct. The order should reverse if the later step actually supplies information the first one requires."
        )
        kind = "dependency_explanation"
        missing_variable = "whether the second step is actually a prerequisite for the first"
    elif comparison and limited_resource and paired_goals:
        resource = limited_resource.group(1).strip()
        first_goal = paired_goals.group(1).strip()
        second_goal = paired_goals.group(2).strip()
        answer = (
            f"I would compare two approaches: first, use the limited {resource} where one intervention can support both {first_goal} and {second_goal}; "
            f"second, divide the available {resource} into measured zones with a visible share for each goal. "
            f"My recommendation for the next small step is a reversible two-zone trial: use the same short observation period, track {resource} used and the visible outcome for both goals, then keep or revise the allocation from that evidence."
        )
        kind = "bounded_shared_resource_comparison"
        missing_variable = f"the measured outcome for {first_goal} and {second_goal} per unit of {resource}"
    elif comparison and ordering:
        answer = (
            "Start with whichever option supplies a prerequisite the other one needs. If neither depends on the other, "
            "start with the smaller reversible step that produces useful evidence sooner. The deciding detail is what each option consumes, produces, and risks."
        )
        kind = "comparison_dependency_rule"
        missing_variable = "what each option consumes, produces, and risks"
    elif comparison:
        answer = (
            "Compare the options on the same dimensions: intended outcome, required evidence, constraints, reversibility, and failure cost. "
            "A useful choice is the one that fits the goal with fewer unsupported assumptions—not merely the one that sounds more complete."
        )
        kind = "comparison_method"
        missing_variable = "which outcome and constraint matter most"
    elif planning or ordering:
        answer = (
            "Begin with the earliest missing prerequisite. If the prerequisites are already present, choose the smallest reversible step that can produce evidence, "
            "check the result, and only then expand."
        )
        kind = "bounded_planning_method"
        missing_variable = "the intended outcome and the first non-negotiable constraint"
    elif lower.startswith(("do you know about ", "what do you know about ")):
        subject = re.sub(r"^(?:do you know about|what do you know about)\s+", "", lower).strip(" ?.\t\n")
        subject = subject or topic
        answer = (
            f"I do not have enough grounded knowledge about {subject} to answer reliably yet. "
            "Which part matters here: what it is, how it works, or why it matters?"
        )
        kind = "bounded_knowledge_gap"
        missing_variable = f"the part of {subject} the answer should cover"
    elif re.match(r"^(?:what|who|when|where)\b", lower):
        answer = (
            f"I do not have a grounded factual answer about {topic} available yet. "
            "An attributed source or approved teaching item would let me answer without guessing."
        )
        kind = "source_needed"
        missing_variable = f"an attributed fact or approved concept for {topic}"
    elif lower.startswith("why"):
        answer = (
            "I do not have enough evidence to name the cause yet. The useful missing piece is a mechanism that connects the observation to the proposed explanation, "
            "plus something we would expect to see if that mechanism is right."
        )
        kind = "causal_evidence_needed"
        missing_variable = "a mechanism and a distinguishing observation"
    else:
        supplied = [
            str(item.get("observation") or "").strip()
            for item in observations or []
            if isinstance(item, dict) and str(item.get("observation") or "").strip()
        ]
        if supplied:
            missing_variable = "which supplied observation should control the conclusion"
        answer = (
            "I do not have enough grounded detail to give the conclusion itself yet. "
            f"The missing piece is {missing_variable}."
        )

    return {
        "status": "answer_substance_ready",
        "answer": truncate(answer, 1000),
        "answer_kind": kind,
        "topic": truncate(topic, 240),
        "missing_variable": truncate(missing_variable, 360),
        "support_basis": support_basis,
        "external_fact_claimed": False,
        "source_required_for_factual_claim": kind in {"bounded_knowledge_gap", "source_needed", "causal_evidence_needed"},
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": ANSWER_SUBSTANCE_BOUNDARY,
    }


def _topic_terms(value: str) -> list[str]:
    words = [word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", value)]
    return list(dict.fromkeys(word for word in words if word not in _STOP_WORDS))[:12]
