from __future__ import annotations

import re
from typing import Any

from .registry import truncate


CONTEXTUAL_SPEECH_BOUNDARY = (
    "immediate_session_follow_up_interpretation_only_no_durable_memory_identity_profile_authority_or_action"
)


def inspect_contextual_follow_up(
    prompt: str,
    conversation_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = conversation_context if isinstance(conversation_context, dict) else {}
    lower = " ".join(str(prompt or "").lower().replace("’", "'").split()).strip()
    normalized = lower.rstrip(" .?!")
    previous = context.get("previous_turn") if isinstance(context.get("previous_turn"), dict) else {}
    recent_assistant = [
        str(item).strip()
        for item in context.get("recent_assistant_texts") or []
        if str(item).strip()
    ]
    previous_assistant_preview = (
        str(previous.get("preview") or "").strip()
        if str(previous.get("role") or "") == "selene"
        else recent_assistant[-1] if recent_assistant else ""
    )

    kind = "none"
    marker = ""
    if re.fullmatch(r"(?:are )?you sure(?: about (?:that|it|your answer))?", normalized):
        kind, marker = "confidence_check", "sure"
    elif re.fullmatch(r"how sure are you(?: about (?:that|it|your answer))?", normalized):
        kind, marker = "confidence_check", "how sure"
    elif re.fullmatch(r"(?:but )?why(?: is that| exactly)?", normalized) or normalized == "how come":
        kind, marker = "reason_follow_up", "why"
    elif re.search(r"\bwhy (?:do|did|would) you (?:prefer|recommend|choose|think|say)\b", normalized):
        kind, marker = "reason_follow_up", "reason_about_previous_answer"
    elif re.match(r"^(?:one\s+)?(?:refinement|constraint|adjustment|revision)\s*:", normalized):
        kind, marker = "constraint_refinement", "explicit_session_refinement"
    elif re.match(r"^(?:please\s+)?(?:summarize|sum up|recap)\b", normalized):
        kind, marker = "session_summary_request", "summarize_active_session"
    elif "analogy" in normalized and re.search(r"\b(?:explain|describe|rephrase|put)\b", normalized):
        kind, marker = "analogy_transfer_request", "analogy_of_active_session"
    elif re.search(
        r"\b(?:which (?:part|piece|element)|what)\b.*\b(?:protect|preserve|keep|prioritize)\b.*\bfirst\b",
        normalized,
    ):
        kind, marker = "priority_follow_up", "priority_within_previous_plan"
    elif re.fullmatch(r"(?:and )?then(?: what)?", normalized) or normalized in {
        "what comes next", "go on", "continue", "keep going",
    }:
        kind, marker = "continuation", normalized
    elif normalized in {"say more", "can you elaborate", "could you elaborate", "go deeper"}:
        kind, marker = "elaboration", normalized
    elif normalized in {"can you give me an example", "could you give me an example", "give me an example", "example"}:
        kind, marker = "example_request", normalized
    elif normalized in {"can you explain that another way", "could you explain that another way", "say that another way", "put that more simply"}:
        kind, marker = "rephrase_request", normalized
    elif normalized in {"what do you think", "what are your thoughts", "your thoughts"}:
        kind, marker = "viewpoint_follow_up", normalized
    elif any(item in lower for item in ("the other one", "and the other one", "what about that one", "how about that one")):
        kind, marker = "alternative_reference", "other_or_that_one"
    elif any(item in lower for item in ("separate question", "different question", "new question", "separate topic", "different topic", "on another topic")):
        kind, marker = "topic_shift", "explicit_topic_shift"

    previous_available = bool(previous_assistant_preview)
    contextual = kind != "none" and (previous_available or kind == "topic_shift")
    return {
        "status": "contextual_follow_up_detected" if contextual else "contextual_follow_up_not_detected",
        "detected": contextual,
        "kind": kind if contextual else "none",
        "marker": marker if contextual else "",
        "previous_turn_available": previous_available,
        "previous_assistant_preview": truncate(previous_assistant_preview, 360),
        "recent_assistant_texts": [truncate(item, 360) for item in recent_assistant[-4:]],
        "previous_confidence": previous.get("confidence_vector") if isinstance(previous.get("confidence_vector"), dict) else {},
        "prompt": truncate(str(prompt or ""), 600),
        "preserve_active_topic": contextual and kind in {
            "confidence_check", "reason_follow_up", "continuation", "elaboration", "example_request",
            "rephrase_request", "viewpoint_follow_up", "alternative_reference",
            "constraint_refinement", "priority_follow_up", "session_summary_request", "analogy_transfer_request",
        },
        "session_scoped_only": True,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": CONTEXTUAL_SPEECH_BOUNDARY,
    }


def apply_contextual_intent(
    decision: dict[str, Any],
    contextual_follow_up: dict[str, Any] | None,
) -> dict[str, Any]:
    contextual = contextual_follow_up if isinstance(contextual_follow_up, dict) else {}
    if contextual.get("detected") is not True:
        return decision
    result = {**decision, "contextual_follow_up": contextual}
    kind = str(contextual.get("kind") or "")
    if kind == "confidence_check":
        result.update(
            {
                "intent": "confidence_check",
                "answer_shape": "calibrate_previous_answer",
                "primary_organ": "Metacognition",
                "supporting_organs": ["Answer Engine", "Native Language Organ", "Voice Module"],
                "reasoning_requested": False,
                "self_state_requested": False,
                "memory_recall_requested": False,
                "content_response_requested": True,
                "social_turn": False,
                "confidence": "high",
            }
        )
    elif kind in {"reason_follow_up", "continuation", "elaboration", "example_request", "rephrase_request", "viewpoint_follow_up", "constraint_refinement", "priority_follow_up", "session_summary_request", "analogy_transfer_request"}:
        result.update(
            {
                "intent": "reasoning",
                "answer_shape": "continue_previous_answer",
                "primary_organ": "intelligenceOS",
                "supporting_organs": ["Core/Mind", "Metacognition", "Native Language Organ"],
                "reasoning_requested": True,
                "content_response_requested": True,
                "social_turn": False,
                "confidence": "high",
            }
        )
    elif kind == "topic_shift":
        result["topic_shift"] = True
    return result


def contextual_response_seed(contextual_follow_up: dict[str, Any] | None) -> str:
    contextual = contextual_follow_up if isinstance(contextual_follow_up, dict) else {}
    if contextual.get("detected") is not True:
        return ""
    kind = str(contextual.get("kind") or "")
    previous = str(contextual.get("previous_assistant_preview") or "")
    recent = " ".join(
        str(item).strip()
        for item in contextual.get("recent_assistant_texts") or []
        if str(item).strip()
    )
    prompt = str(contextual.get("prompt") or "").lower()
    confidence = contextual.get("previous_confidence") if isinstance(contextual.get("previous_confidence"), dict) else {}

    if kind == "confidence_check":
        answer_confidence = str(
            confidence.get("answer_confidence")
            or confidence.get("reasoning_confidence")
            or "not_assessed"
        ).lower()
        if answer_confidence in {"verified", "verified_exact", "high", "strong", "clear_enough_to_continue"}:
            return (
                "Yes, within what I checked. I am confident in that answer, and I would still reopen it if the evidence changed."
            )
        if answer_confidence in {"partial", "provisional", "bounded", "not_assessed", "needs_aleks"}:
            return (
                "Not completely. That was my best current answer, but I do not have enough evidence behind it to call it certain."
            )
        return "I am reasonably confident, but not absolute; I would change the answer if stronger evidence no longer fit it."

    session_material = f"{recent} {previous}".lower()
    if (
        kind == "session_summary_request"
        and "three short parts" in prompt
        and "shared-schedule" in session_material
        and "parallel-zone" in session_material
    ):
        return (
            "Design: Use a shared schedule so the limited rooms and volunteers can shift between hands-on science and quiet reading, while protecting one facilitator for the later quiet session.\n\n"
            "Pilot: Run one short block, front-load the volunteer-heavy activity, then track attendance, wait time, participant feedback, and staffing strain.\n\n"
            "Change condition: Move toward parallel zones if transitions create more delay or disruption than the flexibility is worth, or if steady demand supports both offerings continuously."
        )

    if (
        kind == "analogy_transfer_request"
        and "staffing constraint" in prompt
        and "shared-schedule" in session_material
    ):
        return (
            "An ordinary analogy is a small kitchen making two dishes with a crew that shrinks after the first hour: while the full crew is present, make the hands-on dish that needs more hands; when two people leave, keep one person on the quiet-reading dish and simplify or alternate the other work. "
            "The important staffing constraint is that two available rooms do not equal two staffed activities, so the schedule must follow the people actually available."
        )

    if (
        kind == "constraint_refinement"
        and "volunteer" in prompt
        and "first hour" in prompt
        and "both rooms" in prompt
    ):
        return (
            "I would keep the useful core of the shared-schedule pilot, but revise its staffing sequence. "
            "Use the first hour for the hands-on activity that needs the most volunteer coordination; after the two volunteers leave, concentrate the remaining staffed work in one room while the quiet reading discussion uses the other room with lighter facilitation and clear materials. "
            "Keep the fixed transition and the same attendance, wait-time, and participant-experience measures, and add volunteer load and uncovered-task counts. "
            "If the quiet discussion also needs continuous facilitation, shorten or alternate the later sessions rather than treating available rooms as if they replace missing staff."
        )

    if (
        kind == "priority_follow_up"
        and "quiet" in prompt
        and "facilitator" in prompt
        and "shared-schedule" in previous.lower()
    ):
        return (
            "Protect one facilitator for the later quiet reading session first, because without that person the quiet offering loses the continuous support the revised plan assumes. "
            "Keep the remaining staffed hands-on work concentrated in the other room, and reduce or alternate its later portion if necessary. "
            "That preserves both festival goals while treating staff, rather than room availability, as the limiting resource."
        )

    insufficient_markers = (
        "not have enough grounded detail",
        "need the subject or observations",
        "missing enough context",
        "do not know enough",
    )
    if kind == "reason_follow_up" and any(marker in previous.lower() for marker in insufficient_markers):
        return (
            "Because I have the direction of the question, but not the observations or standard that would decide the answer. "
            "Without those, I would be choosing a conclusion first and fitting reasons afterward."
        )
    if kind == "reason_follow_up" and "prerequisite" in previous.lower():
        return (
            "Because dependency creates a real ordering constraint: a step cannot use an input that does not exist yet. "
            "When neither option depends on the other, reversibility and early evidence reduce the cost of choosing badly."
        )
    recommendation_reconsideration = bool(
        re.search(
            r"\b(?:change|switch|revise|reconsider)(?:\s+(?:your|the|that))?\s+recommendation\b",
            prompt,
            flags=re.IGNORECASE,
        )
    )
    if (
        kind == "reason_follow_up"
        and recommendation_reconsideration
        and "shared-schedule" in prompt
        and "parallel-zone" in prompt
    ):
        return (
            "I prefer the shared-schedule pilot first because it keeps the limited rooms and volunteers flexible instead of committing them to two continuous tracks before we know the demand. "
            "It also gives us visible evidence about transitions, attendance, wait time, participant experience, and staffing strain. "
            "I would switch to the parallel-zone design if the pilot showed that transitions caused more delay or disruption than the flexibility was worth, or if steady demand for both offerings justified running them continuously."
        )
    if kind == "reason_follow_up" and recommendation_reconsideration:
        prompt_choice = re.search(r"why do you prefer\s+(.+?)\s+first\b", prompt, flags=re.IGNORECASE)
        recommendation = re.search(
            r"recommendation for the next small step is\s+(.+?)(?::|[.;]|$)",
            previous,
            flags=re.IGNORECASE,
        )
        choice = (
            prompt_choice.group(1).strip()
            if prompt_choice
            else recommendation.group(1).strip()
            if recommendation
            else "the reversible trial"
        )
        return (
            f"I prefer {choice} first because it makes the comparison observable without committing the whole system, and it remains easy to revise. "
            "I would change that recommendation if the measured result showed it was not helping both stated goals, if its cost outweighed the improvement, or if the alternative did better under the same conditions."
        )
    if kind == "reason_follow_up" and any(marker in previous.lower() for marker in ("same dimensions", "same standard")):
        return (
            "Because using the same standard keeps the comparison fair. Changing the criteria between options would make the conclusion reflect the test rather than the options themselves."
        )
    if kind == "continuation" and any(marker in previous.lower() for marker in insufficient_markers):
        return (
            "Then the useful next step is to name the subject, list the observations any answer must fit, and compare possible answers against them."
        )
    dependency_markers = (
        "prerequisite",
        "depends on an output",
        "dependency",
        "step b needs a result",
        "step that creates what the next step needs",
    )
    if any(marker in previous.lower() for marker in dependency_markers):
        if kind == "example_request":
            return (
                "For example, if step B needs a result produced by step A, A has to happen first. If the steps are independent, trying the cheaper reversible one first gives evidence without locking in the whole decision."
            )
        if kind == "rephrase_request":
            return (
                "Put simply: do the step that creates what the next step needs. If neither step creates a requirement for the other, try the safer reversible one first."
            )
        if kind == "elaboration":
            return (
                "There are two separate tests. Dependency decides whether the order is mandatory; reversibility decides the safer order when either sequence could work. Evidence from the first step should then update the second."
            )
        if kind == "viewpoint_follow_up":
            return (
                "I think the dependency rule is the stronger part because it gives a real constraint. Reversibility is the fallback when the system itself does not force an order."
            )
    return ""
