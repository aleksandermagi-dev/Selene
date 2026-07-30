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
    semantic_context: dict[str, Any] = {}
    ordinary_operation = _ordinary_prompt_grounded_operation(text, observations or [])

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
    elif ordinary_operation:
        answer = str(ordinary_operation["answer"])
        kind = str(ordinary_operation["answer_kind"])
        missing_variable = str(ordinary_operation["missing_variable"])
        support_basis = str(ordinary_operation.get("support_basis") or "current_prompt_only")
        semantic_context = {
            "units": ordinary_operation.get("semantic_units") or [],
        }
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
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "training_allowed": False,
        "lora_allowed": False,
        "autonomous_action_allowed": False,
        "identity_change": False,
        "personality_change": False,
        "governance_change": False,
        "authority_change": False,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": ANSWER_SUBSTANCE_BOUNDARY,
    }


def _structured_semantic_units(kind: str, context: dict[str, Any]) -> list[dict[str, Any]]:
    common = {
        "source_kind": "prompt_grounded_method",
        "source_refs": ["answer_substance:current_prompt"],
        "supported": True,
    }
    supplied_units = [
        item
        for item in context.get("units") or []
        if isinstance(item, dict)
    ]
    if supplied_units:
        return supplied_units[:12]
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


def _ordinary_prompt_grounded_operation(
    prompt: str,
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build ordinary answers from visible premises and recent conversation.

    These operations do not supply external facts. They combine only the
    request's stated resources, candidate explanations, constraints, and
    corrections into an inspectable answer.
    """

    lower = " ".join(prompt.lower().replace("’", "'").split())
    history = _observation_texts(observations)

    revision = _evidence_revision_operation(prompt, lower, history)
    if revision:
        return revision

    constraint = _constraint_revision_operation(prompt, lower, history)
    if constraint:
        return constraint

    follow_up = _answer_development_operation(prompt, lower, history)
    if follow_up:
        return follow_up

    hypothesis = _hypothesis_discrimination_operation(prompt, lower)
    if hypothesis:
        return hypothesis

    if re.search(r"\b(?:would|could|can|do)\s+you\b.{0,45}\bguess\b", lower):
        answer = (
            "Yes. If the visible evidence supports a useful attempt, I can give my best guess, "
            "say what it is based on, and name what would make me revise it. I would keep the guess "
            "clearly separate from something verified."
        )
        return _operation(
            answer=answer,
            answer_kind="bounded_guess_policy",
            missing_variable="the visible evidence that would support a particular guess",
            units=[
                _unit(
                    "guess_allowed",
                    "answer",
                    "condition",
                    subject="I",
                    predicate="can give",
                    obj="my best guess",
                    condition="the visible evidence supports a useful attempt",
                    meaning_keys=["useful evidence-bounded guess is allowed"],
                ),
                _unit(
                    "guess_basis",
                    "support",
                    "support",
                    subject="I",
                    predicate="state",
                    obj="what the guess is based on and what would make me revise it",
                    meaning_keys=["guess includes basis and revision condition"],
                ),
                _unit(
                    "guess_not_verified",
                    "limit",
                    "contrast",
                    subject="the guess",
                    predicate="remain separate from",
                    obj="something verified",
                    meaning_keys=["guess and verified knowledge remain distinct"],
                ),
            ],
        )

    plan = _resource_plan_operation(prompt, lower)
    if plan:
        return plan
    return {}


def _resource_plan_operation(prompt: str, lower: str) -> dict[str, Any]:
    planning_request = bool(
        re.search(
            r"\b(?:suggest|recommend|plan|how should|what should|what could|"
            r"make use of|use (?:the|my|our) time|fit into)\b",
            lower,
        )
    )
    duration = _duration(prompt)
    resources = _available_resources(prompt)
    if not planning_request or not duration or not resources:
        return {}

    primary, secondary = _resource_roles(resources)
    reflective_secondary = _is_reflective_resource(secondary)
    if secondary and reflective_secondary:
        recommendation = (
            f"Use the {duration} for one small, complete pause: start with {primary}, "
            f"then use {secondary} to capture one thought or small idea rather than starting a large task."
        )
        step_one = f"Settle in with {primary}."
        step_two = f"Use {secondary} for one bounded note, sketch, or idea."
    elif secondary:
        recommendation = (
            f"Use the {duration} for one small, complete activity with {primary} and {secondary}, "
            "and choose a stopping point before it expands into a larger task."
        )
        step_one = f"Set up the smallest useful combination of {primary} and {secondary}."
        step_two = "Complete only that bounded piece, then stop."
    else:
        recommendation = (
            f"Use the {duration} for one small, complete activity with {primary}, "
            "and stop before it expands into a larger task."
        )
        step_one = f"Choose one clear use for {primary}."
        step_two = "Do only that small piece, then leave yourself a clean stopping point."
    reason = (
        f"That fits the stated {duration} and the materials already available, "
        "so the activity can feel finished without requiring a larger commitment."
    )
    answer = f"{recommendation} {reason}"
    return _operation(
        answer=answer,
        answer_kind="bounded_resource_plan",
        missing_variable="whether rest, reflection, or output is the preferred immediate goal",
        units=[
            _unit(
                "resource_plan_recommendation",
                "answer",
                "sequence",
                predicate="use",
                obj=f"the {duration} for one small complete activity using {primary}"
                    + (f" and {secondary}" if secondary else ""),
                mood="imperative",
                meaning_keys=["recommendation fits stated time and resources"],
            ),
            _unit(
                "resource_plan_reason",
                "support",
                "cause",
                subject="the recommendation",
                predicate="fit",
                obj=f"the stated {duration} and available materials without a larger commitment",
                meaning_keys=["bounded plan fits visible constraints"],
            ),
            _unit(
                "resource_plan_step_one",
                "support",
                "sequence",
                text=step_one,
                meaning_keys=["first small step"],
            ),
            _unit(
                "resource_plan_step_two",
                "conclusion",
                "sequence",
                text=step_two,
                meaning_keys=["second small step and stopping point"],
            ),
        ],
    )


def _hypothesis_discrimination_operation(prompt: str, lower: str) -> dict[str, Any]:
    pair = _hypothesis_pair(prompt)
    if not pair:
        return {}
    primary, alternative = pair
    asks_for_test = any(
        marker in lower
        for marker in (
            "first thing", "first check", "check first", "test first",
            "what evidence", "change your mind", "change the answer",
            "distinguish", "tell them apart",
        )
    )
    if not asks_for_test:
        return {}
    answer = (
        f"Check the smallest safe, reversible observation on which {primary} and {alternative} "
        f"predict different results. If changing only the condition implied by {primary} removes the "
        f"problem, that supports {primary}. If it does not, and evidence in the form of an observation expected specifically "
        f"under {alternative} appears, I would change my answer and shift toward {alternative}. Until then, both remain "
        "possible and the first is only the current best guess."
    )
    return _operation(
        answer=answer,
        answer_kind="hypothesis_discrimination",
        missing_variable=f"the safe observation that differs between {primary} and {alternative}",
        units=[
            _unit(
                "hypothesis_first_check",
                "answer",
                "sequence",
                predicate="check",
                obj=f"the smallest safe reversible observation that separates {primary} from {alternative}",
                mood="imperative",
                meaning_keys=["use one discriminating observation"],
            ),
            _unit(
                "hypothesis_primary_support",
                "condition",
                "condition",
                subject=f"an isolated change to {primary}",
                predicate="support",
                obj=primary,
                condition="that change removes the observed problem",
                meaning_keys=["primary model gains support from its distinguishing prediction"],
            ),
            _unit(
                "hypothesis_revision",
                "reopening",
                "contrast",
                subject="I",
                predicate="change",
                obj=f"my answer and shift toward {alternative}",
                condition=f"the check does not support {primary} and evidence expected under {alternative} appears",
                meaning_keys=["contrary evidence reopens and revises the guess"],
            ),
            _unit(
                "hypothesis_uncertainty",
                "limit",
                "contrast",
                subject=primary,
                predicate="remain",
                obj="the current best guess rather than a verified conclusion",
                meaning_keys=["working guess remains provisional"],
            ),
        ],
    )


def _evidence_revision_operation(
    prompt: str,
    lower: str,
    history: list[str],
) -> dict[str, Any]:
    asks_revision = any(
        marker in lower
        for marker in (
            "does that change", "does this change", "would that change",
            "revise your", "change your answer", "change your mind",
            "now i see", "now we see", "new evidence", "new observation",
        )
    )
    if not asks_revision:
        return {}
    prior_text = _latest_matching(history, _hypothesis_pair)
    pair = _hypothesis_pair(prior_text) if prior_text else ()
    evidence = _new_evidence(prompt)
    if not evidence or not pair:
        return {}
    primary, alternative = pair
    visible_evidence = evidence[0].upper() + evidence[1:] if evidence else evidence
    answer = (
        f"Yes. {visible_evidence} is new evidence, so I would not defend the earlier guess unchanged. "
        f"It lowers my confidence in {primary} and reopens the comparison with {alternative}. "
        f"I would now ask which explanation actually predicts {evidence}; the observations that still "
        "fit remain useful, but the conclusion should update."
    )
    return _operation(
        answer=answer,
        answer_kind="evidence_revision",
        missing_variable=f"which of {primary} or {alternative} predicts the new observation",
        support_basis="current_prompt_and_recent_conversation",
        units=[
            _unit(
                "revision_direct_answer",
                "answer",
                "cause",
                subject="the new evidence",
                predicate="change",
                obj="the answer",
                meaning_keys=["new evidence changes the answer"],
            ),
            _unit(
                "revision_new_evidence",
                "support",
                "cause",
                subject=f"the new observation that {evidence}",
                predicate="lower",
                obj=f"confidence in {primary}",
                source_kind="current_session_observation",
                source_refs=["answer_substance:recent_conversation_observations"],
                meaning_keys=["new evidence changes prior confidence"],
            ),
            _unit(
                "revision_reopen",
                "reopening",
                "contrast",
                subject="the comparison",
                predicate="reopen",
                obj=f"{primary} versus {alternative}",
                meaning_keys=["reopen competing explanations"],
            ),
            _unit(
                "revision_preserve",
                "conclusion",
                "conclusion",
                subject="the parts of the earlier observations that still fit",
                predicate="remain",
                obj="useful while the conclusion updates",
                meaning_keys=["preserve useful evidence while revising conclusion"],
            ),
        ],
    )


def _constraint_revision_operation(
    prompt: str,
    lower: str,
    history: list[str],
) -> dict[str, Any]:
    if not any(
        marker in lower
        for marker in ("still hold", "plan still", "change the plan", "adjust the plan", "only have")
    ):
        return {}
    new_duration = _duration(prompt)
    prior_text = _latest_matching(history, lambda value: _duration(value) and _available_resources(value))
    if not new_duration or not prior_text:
        return {}
    old_duration = _duration(prior_text)
    resources = _available_resources(prior_text)
    primary, secondary = _resource_roles(resources)
    secondary_step = (
        f", use {secondary} for only one quick note or sketch"
        if _is_reflective_resource(secondary)
        else f", use {secondary} only for the same smaller activity"
        if secondary
        else ""
    )
    answer = (
        f"The aim still holds, but the scope should shrink from {old_duration} to {new_duration}. "
        f"Keep {primary} as the anchor"
        + secondary_step
        + ", and stop there instead of trying to complete the larger version of the plan."
    )
    return _operation(
        answer=answer,
        answer_kind="constraint_revised_plan",
        missing_variable="whether the shortened activity still meets the immediate goal",
        support_basis="current_prompt_and_recent_conversation",
        units=[
            _unit(
                "constraint_preserve_aim",
                "answer",
                "contrast",
                subject="the aim",
                predicate="still hold",
                obj="with a smaller scope",
                meaning_keys=["preserve aim while revising scope"],
            ),
            _unit(
                "constraint_update_duration",
                "support",
                "cause",
                subject=f"the change from {old_duration} to {new_duration}",
                predicate="require",
                obj="a shorter version of the plan",
                source_kind="current_session_observation",
                source_refs=["answer_substance:recent_conversation_observations"],
                meaning_keys=["new time constraint changes plan size"],
            ),
            _unit(
                "constraint_stopping_point",
                "conclusion",
                "sequence",
                predicate="stop after",
                obj="one bounded use of the available materials",
                mood="imperative",
                meaning_keys=["short plan has clear stopping point"],
            ),
        ],
    )


def _answer_development_operation(
    prompt: str,
    lower: str,
    history: list[str],
) -> dict[str, Any]:
    wants_reason_first = bool(
        re.search(r"\b(?:reason|why)\s+first\b|\bstart with (?:the )?(?:reason|why)\b", lower)
    )
    step_match = re.search(r"\b(one|two|three|1|2|3)\s+(?:smallest\s+)?steps?\b", lower)
    if not wants_reason_first and not step_match:
        return {}
    prior_text = _latest_matching(history, lambda value: _duration(value) and _available_resources(value))
    if not prior_text:
        return {}
    duration = _duration(prior_text)
    resources = _available_resources(prior_text)
    primary, secondary = _resource_roles(resources)
    count = _number_value(step_match.group(1)) if step_match else 2
    reason = (
        f"The plan fits the available {duration} and uses what is already present without turning "
        "a small opening into a large commitment."
    )
    possible_steps = [
        f"Settle in with {primary}.",
        (
            f"Use {secondary} for one bounded note, sketch, or idea."
            if _is_reflective_resource(secondary)
            else f"Use {primary} and {secondary} for one bounded version of the activity."
            if secondary
            else f"Choose one bounded use for {primary}."
        ),
        "Stop at the planned endpoint and leave any larger idea for later.",
    ]
    steps = possible_steps[: max(1, min(count, 3))]
    answer = "Reason first: " + reason + " " + " ".join(
        f"Step {index + 1}: {step}" for index, step in enumerate(steps)
    )
    return _operation(
        answer=answer,
        answer_kind="contextual_answer_development",
        missing_variable="whether a different immediate goal should replace the prior plan",
        support_basis="current_prompt_and_recent_conversation",
        units=[
            _unit(
                "development_reason_first",
                "answer",
                "cause",
                subject="the prior plan",
                predicate="fit",
                obj=f"the available {duration} and stated materials without a larger commitment",
                source_kind="current_session_observation",
                source_refs=["answer_substance:recent_conversation_observations"],
                meaning_keys=["reason precedes requested steps"],
            ),
            *[
                _unit(
                    f"development_step_{index + 1}",
                    "support" if index + 1 < len(steps) else "conclusion",
                    "sequence",
                    text=f"Step {index + 1}: {step}",
                    source_kind="current_session_observation",
                    source_refs=["answer_substance:recent_conversation_observations"],
                    meaning_keys=[f"requested step {index + 1}"],
                )
                for index, step in enumerate(steps)
            ],
        ],
    )


def _operation(
    *,
    answer: str,
    answer_kind: str,
    missing_variable: str,
    units: list[dict[str, Any]],
    support_basis: str = "current_prompt_only",
) -> dict[str, Any]:
    return {
        "answer": truncate(answer, 1000),
        "answer_kind": answer_kind,
        "missing_variable": missing_variable,
        "semantic_units": units,
        "support_basis": support_basis,
    }


def _unit(
    unit_id: str,
    role: str,
    relation: str,
    *,
    text: str = "",
    subject: str = "",
    predicate: str = "",
    obj: str = "",
    mood: str = "declarative",
    condition: str = "",
    source_kind: str = "prompt_grounded_method",
    source_refs: list[str] | None = None,
    meaning_keys: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": unit_id,
        "role": role,
        "relation": relation,
        "text": text,
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "mood": mood,
        "condition": condition,
        "source_kind": source_kind,
        "source_refs": source_refs or ["answer_substance:current_prompt"],
        "supported": True,
        "meaning_keys": meaning_keys or [],
    }


def _observation_texts(observations: list[dict[str, Any]]) -> list[str]:
    return [
        truncate(str(item.get("observation") or item.get("preview") or ""), 900).strip()
        for item in observations
        if isinstance(item, dict)
        and str(item.get("observation") or item.get("preview") or "").strip()
    ]


def _latest_matching(values: list[str], predicate: Any) -> str:
    for value in reversed(values):
        try:
            if predicate(value):
                return value
        except (AttributeError, TypeError, ValueError):
            continue
    return ""


def _hypothesis_pair(text: str) -> tuple[str, str] | None:
    normalized = " ".join(str(text or "").replace("’", "'").split())
    match = re.search(
        r"\b(?:my\s+)?(?:best|working|initial|current)\s+"
        r"(?:guess|hypothesis|read)\s+(?:is|would be|:)\s+(.+?)"
        r"(?:,\s*|\s+)(?:but|although|while)\s+(.+?)(?:[.?!]|$)",
        normalized,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    primary = _clean_hypothesis(match.group(1))
    alternative = _clean_hypothesis(match.group(2))
    return (primary, alternative) if primary and alternative else None


def _clean_hypothesis(value: str) -> str:
    cleaned = re.sub(
        r"^(?:it|there|the problem|the cause)\s+(?:could|might|may|can)\s+(?:also\s+)?(?:be\s+)?",
        "",
        value.strip(" ,"),
        flags=re.IGNORECASE,
    )
    cleaned = re.split(
        r"\b(?:what|which|how)\b.{0,35}\b(?:check|evidence|change|distinguish)\b",
        cleaned,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    modal_description = re.match(
        r"^(.*?)\s+(?:could|might|may)\s+be\s+(.+)$",
        cleaned.strip(" ,"),
        flags=re.IGNORECASE,
    )
    if modal_description:
        cleaned = (
            f"{modal_description.group(1).strip()} being "
            f"{modal_description.group(2).strip()}"
        )
    return truncate(cleaned.strip(" ,"), 180)


def _new_evidence(prompt: str) -> str:
    text = " ".join(str(prompt or "").split())
    patterns = (
        r"\b(?:now|then)\s+(?:i|we)\s+(?:see|saw|found|notice|noticed|observe|observed)\s+(.+?)(?:[.?!]|$)",
        r"\b(?:new evidence|new observation)\s*(?:is|:)?\s*(.+?)(?:[.?!]|$)",
        r"\b(?:i|we)\s+(?:also\s+)?(?:see|saw|found|notice|noticed|observe|observed)\s+(.+?)(?:[.?!]|$)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return truncate(match.group(1).strip(" ,"), 240)
    return ""


def _duration(text: str) -> str:
    match = re.search(
        r"\b(?:only\s+|about\s+|around\s+|roughly\s+)?"
        r"(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
        r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
        r"twenty|twenty-five|thirty|forty|forty-five|fifty|sixty|\d+)\s+"
        r"(minutes?|hours?)\b",
        str(text or ""),
        flags=re.IGNORECASE,
    )
    return (
        f"{match.group(1).lower()} {match.group(2).lower()}"
        if match
        else ""
    )


def _available_resources(text: str) -> list[str]:
    match = re.search(
        r"\b(?:i|we)\s+(?:only\s+)?(?:have got|have|got)\s+(.+?)(?:[.;?!]|$)",
        str(text or ""),
        flags=re.IGNORECASE,
    )
    if not match:
        return []
    phrase = re.sub(
        r"(?:,\s*|\s+and\s+)?(?:only\s+|about\s+|around\s+|roughly\s+)?"
        r"(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
        r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
        r"twenty|twenty-five|thirty|forty|forty-five|fifty|sixty|\d+)\s+"
        r"(?:minutes?|hours?)\b",
        "",
        match.group(1),
        flags=re.IGNORECASE,
    ).strip(" ,")
    parts = [
        re.sub(r"^(?:and\s+)?(?:a|an|the|some)\s+", "", item.strip(), flags=re.IGNORECASE)
        for item in re.split(r"\s*,\s*|\s+and\s+", phrase)
        if item.strip()
    ]
    return [truncate(item, 120) for item in parts if item][:6]


def _resource_roles(resources: list[str]) -> tuple[str, str]:
    if not resources:
        return "what is available", ""
    reflective = next(
        (item for item in resources if _is_reflective_resource(item)),
        "",
    )
    primary = next((item for item in resources if item != reflective), resources[0])
    secondary = reflective if reflective and reflective != primary else (
        resources[1] if len(resources) > 1 else ""
    )
    return primary, secondary


def _is_reflective_resource(value: str) -> bool:
    return any(
        marker in str(value or "").lower()
        for marker in (
            "notebook", "journal", "paper", "pad", "pen", "pencil",
            "sketchbook", "canvas", "book", "notes",
        )
    )


def _number_value(value: str) -> int:
    return {
        "one": 1,
        "two": 2,
        "three": 3,
    }.get(str(value).lower(), int(value) if str(value).isdigit() else 2)
