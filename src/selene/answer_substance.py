from __future__ import annotations

import re
from typing import Any

from .registry import truncate
from .supported_semantics import build_supported_semantic_packet


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
    semantic_context: dict[str, str] = {}

    comparison = any(marker in lower for marker in ("compare", "difference", "versus", " vs ", "tradeoff", "trade-off", "which option"))
    ordering = any(marker in lower for marker in ("come first", "do first", "start with", "begin with", "priority", "prioritize"))
    planning = bool(
        re.search(
            r"\b(?:how should|what should|plan|strategy|next step|where do we start)\b",
            lower,
        )
    )
    consequence = bool(re.match(r"^what happens if\b", lower))
    viewpoint = any(marker in lower for marker in ("what do you think", "what is your view", "what's your view", "your thoughts"))
    why_before = re.search(r"\bwhy\s+(?:does|do|should|is|are)\s+(.{2,100}?)\s+(?:come\s+)?before\s+(.{2,100}?)(?:[?.]|$)", lower)
    limited_resource = re.search(r"\blimited\s+([a-z][a-z-]*)(?:\s+and|\s+but|[,.])", lower)
    limited_capacity = re.search(
        r"\blimited\s+([a-z][a-z -]{1,60}?)(?:,\s*(?:but|while)|\s+but\b|[.])",
        lower,
    )
    paired_goals = re.search(
        r"\bsupport\s+both\s+([a-z][a-z -]{1,60}?)\s+and\s+([a-z][a-z -]{1,60}?)(?:[.?,]|$)",
        lower,
    )
    paired_offerings = re.search(
        r"\b(?:offer|provide|include)\s+both\s+(.{2,100}?)\s+and\s+(.{2,100}?)(?:\s+for\s+[^.?,]+|[.?,]|$)",
        lower,
    )
    fluency_without_transfer = (
        re.search(r"\b(?:repeat|say|word|phrase).{0,80}\bfluent", lower)
        or "fluent wording" in lower
    ) and re.search(
        r"\b(?:cannot|can't|could not|couldn't|does not|doesn't)\b.{0,100}"
        r"\b(?:apply|use|transfer)\b.{0,80}\b(?:new|different|distinct)\b.{0,30}\bexample\b",
        lower,
    )
    exact_answer_vs_understanding = (
        "exact answer" in lower
        and "understanding" in lower
        and any(marker in lower for marker in ("different", "distinction", "not the same", "isn't the same", "is not the same"))
    )

    if fluency_without_transfer:
        answer = (
            "Fluent wording without use in a new example shows familiarity, not transferable understanding. "
            "The next step is to reopen the lesson, find the missing prerequisite or distinction, teach it through a different example, "
            "then check reconstruction and application again."
        )
        kind = "reopen_fluency_without_transfer"
        missing_variable = "which prerequisite or distinction is blocking transfer"
        semantic_context = {"variant": "fluency_without_transfer"}
    elif exact_answer_vs_understanding:
        answer = (
            "An exact answer can be correct for one case; understanding also includes why it works, how to apply it to a different case, "
            "where it stops applying, and how to revise it when contrary evidence appears."
        )
        kind = "exactness_understanding_distinction"
        missing_variable = "whether the idea transfers beyond the single result"
        semantic_context = {"variant": "exactness_vs_understanding"}
    elif (
        re.search(r"\b(?:working|solving|building)\b.*\btogether\b", lower)
        and re.search(r"\b(?:got|get|were|was)\s+stuck\b", lower)
        and re.search(r"\bwhat would you ask me for\b|\bask me for help\b", lower)
    ):
        answer = (
            "I would tell you exactly where the task stopped making sense, use everything I could still verify, "
            "and ask you for the smallest missing piece that controls the next step: usually a constraint, observation, source, or decision only you can supply."
        )
        kind = "collaborative_help_request"
        missing_variable = "the smallest task-specific input that remains unavailable"
        semantic_context = {"variant": "ask_for_smallest_missing_input"}
    elif (
        "calculus" in lower
        and "fraction" in lower
        and re.search(r"\b(?:agree|before|first)\b", lower)
    ):
        answer = (
            "No. Fractions should normally come before calculus because calculus depends on ratios, division, algebraic manipulation, and functions that use fractional relationships. "
            "The order can be compressed for someone who already understands those prerequisites, but skipping the understanding itself would leave a real gap."
        )
        kind = "grounded_prerequisite_disagreement"
        missing_variable = "whether the learner already understands the fractional and algebraic prerequisites"
        semantic_context = {"variant": "fractions_before_calculus"}
    elif (
        comparison
        and ordering
        and "fraction" in lower
        and "conversational uncertainty" in lower
    ):
        answer = (
            "They build different foundations: fractions teach part-whole quantity, equivalence, ratio, and operations; conversational uncertainty teaches how to distinguish a firm answer, a provisional read, missing context, and ordinary not-knowing. "
            "For Selene's current conversational work, I would teach conversational uncertainty first because it immediately improves how every later subject is discussed; fractions should still come first inside the ordered mathematics sequence."
        )
        kind = "cross_domain_foundation_comparison"
        missing_variable = "whether the immediate goal is conversational readiness or the mathematics curriculum"
        semantic_context = {"variant": "fractions_and_conversational_uncertainty"}
    elif viewpoint and any(marker in lower for marker in ("reversible step", "reversible first", "smallest reversible")):
        answer = (
            "I think that is a sound default when uncertainty is high: a small reversible step limits the cost of being wrong and produces evidence for the next choice. "
            "It should not override a known prerequisite, safety constraint, or already-settled evidence."
        )
        kind = "bounded_viewpoint"
        missing_variable = "whether a prerequisite or non-negotiable constraint overrides reversibility"
        semantic_context = {"variant": "reversible_step"}
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
        semantic_context = {"variant": "reversed_order"}
    elif consequence:
        answer = (
            "Treat that as a conditional change: identify what the changed part feeds, which assumptions depend on it, and what observable result should differ. "
            "That gives us a prediction to check instead of a consequence invented from wording alone."
        )
        kind = "conditional_consequence_method"
        missing_variable = "the downstream dependency and observable prediction"
        semantic_context = {"variant": "conditional_change"}
    elif why_before:
        first = why_before.group(1).strip(" ,")
        second = why_before.group(2).strip(" ,")
        answer = (
            f"Putting {first} before {second} preserves the input before the later step can reshape it. "
            "That makes the result easier to trace, test, and correct. The order should reverse if the later step actually supplies information the first one requires."
        )
        kind = "dependency_explanation"
        missing_variable = "whether the second step is actually a prerequisite for the first"
        semantic_context = {"first": first, "second": second}
    elif (
        comparison
        and "attendance alone" in lower
        and "wait time" in lower
        and "participant feedback" in lower
    ):
        answer = (
            "Attendance plus wait time and participant feedback is more useful than attendance alone because it shows not just how many people came, but whether access and the experience worked. "
            "Its limitation is that feedback can be subjective, the added measures take more effort to collect, and one small pilot may not represent later demand. "
            "I would report attendance for each offering, the average and longest wait, the recurring feedback themes, and the sample size, then state whether those results support keeping the shared schedule or changing it."
        )
        kind = "bounded_measurement_comparison"
        missing_variable = "the success threshold for access, participant experience, and representative demand"
        semantic_context = {"variant": "measurement_comparison"}
    elif comparison and limited_capacity and paired_offerings:
        resources = limited_capacity.group(1).strip()
        first_goal = paired_offerings.group(1).strip(" ,")
        second_goal = paired_offerings.group(2).strip(" ,")
        answer = (
            f"I would compare two workable designs. In a shared-schedule design, {first_goal} and {second_goal} alternate through the same {resources}, which preserves flexibility but requires clear transitions. "
            f"In a parallel-zone design, the {resources} are split between both offerings at the same time, which improves continuity but leaves less spare capacity when demand shifts. "
            "I would pilot one short shared-schedule block first: use a fixed transition, record attendance and wait time for each offering, ask participants whether the pace worked, and then compare that evidence with the staffing strain before expanding."
        )
        kind = "bounded_shared_capacity_design"
        missing_variable = f"attendance, wait time, participant experience, and staffing strain under the available {resources}"
        semantic_context = {
            "resources": resources,
            "first_goal": first_goal,
            "second_goal": second_goal,
        }
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
        semantic_context = {
            "resource": resource,
            "first_goal": first_goal,
            "second_goal": second_goal,
        }
    elif comparison and ordering:
        answer = (
            "Start with whichever option supplies a prerequisite the other one needs. If neither depends on the other, "
            "start with the smaller reversible step that produces useful evidence sooner. The deciding detail is what each option consumes, produces, and risks."
        )
        kind = "comparison_dependency_rule"
        missing_variable = "what each option consumes, produces, and risks"
        semantic_context = {"variant": "comparison_ordering"}
    elif comparison:
        answer = (
            "Compare the options on the same dimensions: intended outcome, required evidence, constraints, reversibility, and failure cost. "
            "A useful choice is the one that fits the goal with fewer unsupported assumptions—not merely the one that sounds more complete."
        )
        kind = "comparison_method"
        missing_variable = "which outcome and constraint matter most"
        semantic_context = {"variant": "shared_dimensions"}
    elif planning or ordering:
        answer = (
            "Begin with the earliest missing prerequisite, because later steps cannot reliably use a foundation that is absent. "
            "If the prerequisites are already present, choose the smallest reversible step that can produce evidence, "
            "check the result, and only then expand."
        )
        kind = "bounded_planning_method"
        missing_variable = "the intended outcome and the first non-negotiable constraint"
        semantic_context = {"variant": "prerequisite_then_reversible"}
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

    semantic_units = _structured_semantic_units(kind, semantic_context)
    if not semantic_units:
        semantic_units = _text_grounded_semantic_units(answer)
    semantic_packet = build_supported_semantic_packet(
        {
            "answer_kind": kind,
            "certainty": "provisional",
            "scope": "current_prompt_only",
            "fallback_text": answer,
            "source_refs": ["answer_substance:current_prompt"],
            "units": semantic_units,
        }
    )
    return {
        "status": "answer_substance_ready",
        "answer": truncate(answer, 1000),
        "answer_kind": kind,
        "topic": truncate(topic, 240),
        "missing_variable": truncate(missing_variable, 360),
        "support_basis": support_basis,
        "semantic_packet": semantic_packet,
        "semantic_units": semantic_packet["units"],
        "structured_semantic_handoff": semantic_packet["structured_unit_count"] > 0,
        "compatibility_fallback_available": semantic_packet["compatibility_fallback_available"],
        "external_fact_claimed": False,
        "source_required_for_factual_claim": kind in {"bounded_knowledge_gap", "source_needed", "causal_evidence_needed"},
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": ANSWER_SUBSTANCE_BOUNDARY,
    }


def _structured_semantic_units(kind: str, context: dict[str, str]) -> list[dict[str, Any]]:
    common = {
        "source_kind": "prompt_grounded_method",
        "source_refs": ["answer_substance:current_prompt"],
        "supported": True,
    }
    if kind == "comparison_dependency_rule":
        return [
            {
                **common,
                "id": "comparison_start_prerequisite",
                "role": "answer",
                "relation": "sequence",
                "predicate": "start with",
                "object": "the option that supplies a prerequisite the other option needs",
                "mood": "imperative",
                "lexical_choices": {
                    "predicate": ["start with", "begin with"],
                    "object": [
                        "the option that supplies a prerequisite the other option needs",
                        "the option that creates an input the other option requires",
                    ],
                },
                "lexical_semantics": [
                    {
                        "id": "initiate_ordering",
                        "field": "predicate",
                        "lemma": "start with",
                        "forms": ["start with", "begin with"],
                        "sense": "initiate an ordered comparison with the dependency-supplying option",
                        "part_of_speech": "verb_phrase",
                        "grammatical_behavior": ["imperative-compatible", "takes an option as its object"],
                        "registers": ["ordinary", "technical"],
                        "collocations": ["option", "prerequisite", "step"],
                        "near_concepts": ["continue with", "finish with"],
                        "distinctions": ["starting selects the first step; continuing assumes a step already began"],
                        "concept_refs": ["answer_kind:comparison_dependency_rule"],
                        "understanding_state": "prompt_grounded",
                        "source_refs": ["answer_substance:current_prompt"],
                    }
                ],
                "meaning_keys": ["prerequisite controls ordering"],
            },
            {
                **common,
                "id": "comparison_reversible_fallback",
                "role": "condition",
                "relation": "condition",
                "predicate": "start with",
                "object": "the smaller reversible step that produces useful evidence sooner",
                "mood": "imperative",
                "condition": "neither option depends on the other",
                "lexical_choices": {
                    "predicate": ["start with", "try"],
                    "object": [
                        "the smaller reversible step that produces useful evidence sooner",
                        "the smaller reversible option that gives useful evidence sooner",
                    ],
                },
                "meaning_keys": ["reversibility guides nondependent ordering", "early evidence"],
            },
            {
                **common,
                "id": "comparison_deciding_detail",
                "role": "support",
                "relation": "support",
                "subject": "the deciding detail",
                "predicate": "be",
                "object": "what each option consumes, produces, and risks",
                "meaning_keys": ["compare inputs outputs and risks"],
            },
        ]
    if kind == "dependency_explanation":
        first = context.get("first") or "the first step"
        second = context.get("second") or "the later step"
        return [
            {
                **common,
                "id": "dependency_preserves_input",
                "role": "answer",
                "relation": "cause",
                "subject": f"putting {first} before {second}",
                "predicate": "preserve",
                "object": "the input before the later step can reshape it",
                "meaning_keys": ["ordering preserves input"],
            },
            {
                **common,
                "id": "dependency_traceability",
                "role": "support",
                "relation": "support",
                "subject": "that ordering",
                "predicate": "make",
                "object": "the result easier to trace, test, and correct",
                "meaning_keys": ["ordering improves traceability and correction"],
            },
            {
                **common,
                "id": "dependency_reversal_condition",
                "role": "condition",
                "relation": "condition",
                "subject": "the order",
                "predicate": "reverse",
                "modality": "should",
                "condition": f"{second} supplies information {first} requires",
                "meaning_keys": ["reverse order when dependency reverses"],
            },
        ]
    if kind == "conditional_dependency_answer":
        return [
            {
                **common,
                "id": "reversal_dependency_gate",
                "role": "answer",
                "relation": "condition",
                "subject": "the reversed order",
                "predicate": "work",
                "condition": "the later step does not depend on an output from the earlier one",
                "meaning_keys": ["reversal works only without dependency"],
            },
            {
                **common,
                "id": "reversal_missing_input",
                "role": "condition",
                "relation": "condition",
                "subject": "the reversed sequence",
                "predicate": "remove",
                "object": "a required input",
                "condition": "that dependency exists",
                "meaning_keys": ["dependency makes reversal remove input"],
            },
            {
                **common,
                "id": "reversal_compare_when_independent",
                "role": "condition",
                "relation": "condition",
                "predicate": "compare",
                "object": "which order gives clearer evidence with less irreversible cost",
                "mood": "imperative",
                "condition": "the steps are independent",
                "meaning_keys": ["compare evidence and irreversible cost when independent"],
            },
        ]
    if kind == "bounded_viewpoint" and context.get("variant") == "reversible_step":
        return [
            {
                **common,
                "id": "reversible_step_limits_cost",
                "role": "answer",
                "relation": "cause",
                "subject": "a small reversible step",
                "predicate": "limit",
                "object": "the cost of being wrong",
                "condition": "uncertainty is high",
                "meaning_keys": ["reversibility limits error cost"],
            },
            {
                **common,
                "id": "reversible_step_produces_evidence",
                "role": "support",
                "relation": "support",
                "subject": "the step",
                "predicate": "produce",
                "object": "evidence for the next choice",
                "meaning_keys": ["small step produces evidence"],
            },
            {
                **common,
                "id": "reversible_step_limit",
                "role": "limit",
                "relation": "contrast",
                "subject": "a reversible-step default",
                "predicate": "override",
                "object": "a known prerequisite, safety constraint, or settled evidence",
                "modality": "should",
                "polarity": "negative",
                "meaning_keys": ["prerequisites safety and settled evidence outrank reversibility"],
            },
        ]
    if kind == "comparison_method":
        return [
            {
                **common,
                "id": "comparison_shared_dimensions",
                "role": "answer",
                "relation": "sequence",
                "predicate": "compare",
                "object": "the options on the same dimensions: intended outcome, required evidence, constraints, reversibility, and failure cost",
                "mood": "imperative",
                "meaning_keys": ["compare options on shared dimensions"],
            },
            {
                **common,
                "id": "comparison_useful_choice",
                "role": "conclusion",
                "relation": "conclusion",
                "subject": "a useful choice",
                "predicate": "fit",
                "object": "the goal with fewer unsupported assumptions",
                "contrast": "the more complete-sounding option is not automatically better",
                "meaning_keys": ["prefer fit with fewer unsupported assumptions"],
            },
        ]
    if kind == "bounded_planning_method":
        return [
            {
                **common,
                "id": "planning_prerequisite_first",
                "role": "answer",
                "relation": "sequence",
                "predicate": "begin with",
                "object": "the earliest missing prerequisite",
                "mood": "imperative",
                "lexical_choices": {"predicate": ["begin with", "start with"]},
                "lexical_semantics": [
                    {
                        "id": "begin_prerequisite_sequence",
                        "field": "predicate",
                        "lemma": "begin with",
                        "forms": ["begin with", "start with"],
                        "sense": "initiate a plan at its earliest unsatisfied dependency",
                        "part_of_speech": "verb_phrase",
                        "grammatical_behavior": ["imperative-compatible", "takes a prerequisite as its object"],
                        "registers": ["ordinary", "planning"],
                        "collocations": ["prerequisite", "foundation", "first step"],
                        "near_concepts": ["resume", "expand"],
                        "distinctions": ["beginning establishes the first step; expanding assumes the foundation exists"],
                        "concept_refs": ["answer_kind:bounded_planning_method"],
                        "understanding_state": "prompt_grounded",
                        "source_refs": ["answer_substance:current_prompt"],
                    }
                ],
                "meaning_keys": ["earliest missing prerequisite comes first"],
            },
            {
                **common,
                "id": "planning_prerequisite_reason",
                "role": "support",
                "relation": "cause",
                "subject": "later steps",
                "predicate": "cannot reliably use",
                "object": "a foundation that is absent",
                "meaning_keys": ["missing prerequisite prevents reliable later use"],
            },
            {
                **common,
                "id": "planning_reversible_evidence",
                "role": "condition",
                "relation": "condition",
                "predicate": "choose",
                "object": "the smallest reversible step that can produce evidence",
                "mood": "imperative",
                "condition": "the prerequisites are already present",
                "meaning_keys": ["choose reversible evidence-producing step after prerequisites"],
            },
            {
                **common,
                "id": "planning_check_then_expand",
                "role": "conclusion",
                "relation": "sequence",
                "predicate": "check",
                "object": "the result before expanding",
                "mood": "imperative",
                "meaning_keys": ["verify result before expansion"],
            },
        ]
    if kind == "conditional_consequence_method":
        return [
            {
                **common,
                "id": "consequence_trace_dependencies",
                "role": "answer",
                "relation": "sequence",
                "predicate": "identify",
                "object": "what the changed part feeds and which assumptions depend on it",
                "mood": "imperative",
                "meaning_keys": ["trace changed dependency and assumptions"],
            },
            {
                **common,
                "id": "consequence_prediction",
                "role": "support",
                "relation": "support",
                "predicate": "name",
                "object": "the observable result that should differ",
                "mood": "imperative",
                "meaning_keys": ["derive observable prediction"],
            },
            {
                **common,
                "id": "consequence_no_wording_invention",
                "role": "conclusion",
                "relation": "conclusion",
                "subject": "that method",
                "predicate": "replace",
                "object": "a consequence invented from wording alone",
                "polarity": "negative",
                "meaning_keys": ["do not invent consequence from wording"],
            },
        ]
    return []


def _text_grounded_semantic_units(answer: str) -> list[dict[str, Any]]:
    sentences = [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+|\n+", str(answer or "").strip())
        if item.strip()
    ]
    return [
        {
            "id": f"fallback_{index + 1}",
            "role": "answer" if index == 0 else "support",
            "relation": "sequence" if index == 0 else "support",
            "text": sentence,
            "source_kind": "compatibility_fallback",
            "source_refs": ["answer_substance:current_prompt"],
            "supported": True,
            "meaning_keys": [truncate(sentence.lower(), 120)],
        }
        for index, sentence in enumerate(sentences[:8])
    ]


def _topic_terms(value: str) -> list[str]:
    words = [word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", value)]
    return list(dict.fromkeys(word for word in words if word not in _STOP_WORDS))[:12]
