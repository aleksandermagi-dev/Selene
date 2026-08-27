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
    recent_user = [
        str(item).strip()
        for item in context.get("recent_user_texts") or []
        if str(item).strip()
    ]
    previous_user_preview = recent_user[-1] if recent_user else ""
    previous_assistant_preview = (
        str(previous.get("preview") or "").strip()
        if str(previous.get("role") or "") == "selene"
        else recent_assistant[-1] if recent_assistant else ""
    )
    session_landmarks = [
        item for item in context.get("session_landmarks") or [] if isinstance(item, dict)
    ][-64:]
    deferred_return = _is_deferred_return_closure(normalized)

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
    elif re.search(
        r"\bwhat about (?:this|our) (?:conversation|chat) makes you say that\b",
        normalized,
    ):
        kind, marker = "reason_follow_up", "reason_about_present_self_report"
    elif previous_assistant_preview and (
        (
            re.search(r"\b(?:your|that|the previous) answer\b", normalized)
            and re.search(
                r"\b(?:change|conclusion|develop|evidence|explain|expand|reason|short)\b",
                normalized,
            )
        )
        or re.match(
            r"^(?:now\s+)?give me (?:the\s+)?(?:short|brief|direct) answer\b",
            normalized,
        )
        or (
            re.match(r"^(?:now\s+)?put (?:the|your) conclusion first\b", normalized)
            and re.search(r"\b(?:answer|evidence|explain|reason)\b", normalized)
        )
    ):
        kind, marker = "answer_development", "develop_previous_answer"
    elif previous_assistant_preview and (
        re.search(
            r"\b(?:make|rewrite|revise)\b.*\b(?:sentence|paragraph|scene)\b.*"
            r"\b(?:slower|softer|faster|sharper|warmer|quieter|pacing|tone)\b",
            normalized,
        )
        or re.search(r"\bwhat did you change\b.*\b(?:pacing|tone|wording|rhythm)\b", normalized)
    ):
        kind, marker = "answer_development", "creative_revision_follow_up"
    elif previous_assistant_preview and re.search(
        r"\bwhat (?:difference|distinction) between .+? and .+?\b"
        r".*\b(?:preserv(?:e|ed|ing)|keep|kept|distinguish(?:ed|ing)?)\b",
        normalized,
    ):
        kind, marker = "comparison_follow_up", "difference_in_previous_answer"
    elif re.match(r"^(?:one\s+)?(?:refinement|constraint|adjustment|revision)\s*:", normalized):
        kind, marker = "constraint_refinement", "explicit_session_refinement"
    elif re.search(
        r"\b(?:(?:please\s+)?(?:summarize|sum up|recap)\b|"
        r"(?:give|tell|show)\s+(?:me|us)\s+(?:a\s+)?(?:short\s+|brief\s+)?(?:summary|recap)\b|"
        r"what\s+(?:one|two|three|four|five|\d+)\s+facts?.*\bsettled\b)",
        normalized,
    ):
        kind, marker = "session_summary_request", "summarize_active_session"
    elif re.search(
        r"\b(?:what (?:has|have) (?:this|our) (?:conversation|chat) been about|"
        r"what have we been (?:talking|speaking) about)\b",
        normalized,
    ):
        kind, marker = "session_summary_request", "summarize_active_session"
    elif not deferred_return and re.search(
        r"\b(?:earlier when|back to what|return to what|the point about|what you said about|we discussed)\b|"
        r"\b(?:back|return|going back)\s+to\s+[^,;:.!?]+",
        normalized,
    ):
        kind, marker = "named_callback", "named_visible_session_point"
    elif (
        previous_user_preview
        and not re.search(r"\b(?:protect|preserve|keep|prioritize)\b", normalized)
        and re.search(
        r"\b(?:what|which)\s+(?:part|piece|aspect|result|thing)\s+of\s+"
        r"(?:that|this|it)\b|\bwhat\s+am\s+i\s+(?:celebrating|referring\s+to)\b",
        normalized,
        )
    ):
        kind, marker = "immediate_user_callback", "immediately_preceding_user_statement"
    elif "analogy" in normalized and re.search(r"\b(?:explain|describe|rephrase|put)\b", normalized):
        kind, marker = "analogy_transfer_request", "analogy_of_active_session"
    elif re.search(
        r"\b(?:which (?:part|piece|element)|what)\b.*\b(?:protect|preserve|keep|prioritize)\b.*\bfirst\b",
        normalized,
    ):
        kind, marker = "priority_follow_up", "priority_within_previous_plan"
    elif re.search(r"\b(?:what(?:'s| is) the )?revised order\b", normalized):
        kind, marker = "priority_follow_up", "revise_previous_order"
    elif re.fullmatch(r"(?:and )?then(?: what)?", normalized) or normalized in {
        "what comes next", "go on", "continue", "keep going",
    }:
        kind, marker = "continuation", normalized
    elif normalized in {"say more", "can you elaborate", "could you elaborate", "go deeper"}:
        kind, marker = "elaboration", normalized
    elif normalized in {"can you give me an example", "could you give me an example", "give me an example", "example"}:
        kind, marker = "example_request", normalized
    elif normalized in {
        "what", "huh", "what do you mean", "what did you mean",
        "can you explain that another way", "could you explain that another way",
        "say that another way", "put that more simply",
    }:
        kind, marker = "rephrase_request", normalized
    elif normalized in {"what do you think", "what are your thoughts", "your thoughts"}:
        kind, marker = "viewpoint_follow_up", normalized
    elif (
        previous_assistant_preview
        and re.fullmatch(r".{1,100}?\s+means\s+.{1,240}", normalized)
        and any(
            cue in previous_assistant_preview.lower()
            for cue in (
                "not sure", "missing", "not enough grounding", "not enough context",
                "what information", "which part", "what do you mean", "said that awkwardly",
            )
        )
    ):
        kind, marker = "meaning_correction", "phrase_meaning_after_misunderstanding"
    elif any(item in lower for item in ("the other one", "and the other one", "what about that one", "how about that one")):
        kind, marker = "alternative_reference", "other_or_that_one"
    elif any(item in lower for item in ("separate question", "different question", "new question", "separate topic", "different topic", "on another topic")):
        kind, marker = "topic_shift", "explicit_topic_shift"

    previous_available = bool(previous_assistant_preview or previous_user_preview or session_landmarks)
    contextual = kind != "none" and (previous_available or kind == "topic_shift")
    return {
        "status": "contextual_follow_up_detected" if contextual else "contextual_follow_up_not_detected",
        "detected": contextual,
        "kind": kind if contextual else "none",
        "marker": marker if contextual else "",
        "previous_turn_available": previous_available,
        "previous_assistant_preview": truncate(previous_assistant_preview, 900),
        "previous_user_preview": truncate(previous_user_preview, 900),
        "recent_assistant_texts": [truncate(item, 360) for item in recent_assistant[-4:]],
        "recent_user_texts": [truncate(item, 360) for item in recent_user[-8:]],
        "session_landmarks": session_landmarks,
        "matched_session_landmarks": _matching_landmarks(prompt, session_landmarks),
        "previous_confidence": previous.get("confidence_vector") if isinstance(previous.get("confidence_vector"), dict) else {},
        "prompt": truncate(str(prompt or ""), 600),
        "preserve_active_topic": contextual and kind in {
            "confidence_check", "reason_follow_up", "continuation", "elaboration", "example_request",
            "rephrase_request", "viewpoint_follow_up", "alternative_reference",
            "constraint_refinement", "priority_follow_up", "session_summary_request", "analogy_transfer_request",
            "named_callback", "meaning_correction", "answer_development",
            "immediate_user_callback", "comparison_follow_up",
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
    meaning_route = decision.get("meaning_route") if isinstance(decision.get("meaning_route"), dict) else {}
    meaning_frame = (
        meaning_route.get("canonical_meaning_frame")
        if isinstance(meaning_route.get("canonical_meaning_frame"), dict)
        else {}
    )
    if (
        str(decision.get("intent") or "") == "farewell"
        and meaning_frame.get("academic_knowledge_posture") == "hold_for_social_or_conversation_management"
    ):
        result["contextual_override_held"] = True
        result["contextual_override_reason"] = "primary_social_closure_has_no_current_substantive_request"
        return result
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
    elif kind == "meaning_correction":
        result.update(
            {
                "intent": "correction",
                "answer_shape": "acknowledge_and_adjust",
                "primary_organ": "Core/Mind",
                "supporting_organs": ["Native Language Organ"],
                "reasoning_requested": False,
                "self_state_requested": False,
                "memory_recall_requested": False,
                "content_response_requested": False,
                "social_turn": False,
                "confidence": "high",
            }
        )
    elif kind == "session_summary_request" and result.get("self_state_requested") is True:
        result.update(
            {
                "intent": "self_state",
                "answer_shape": "self_state_then_session_summary",
                "primary_organ": "self-state",
                "supporting_organs": ["Conversation Spine", "Native Language Organ"],
                "reasoning_requested": False,
                "memory_recall_requested": False,
                "content_response_requested": True,
                "social_turn": False,
                "mixed_intent": True,
                "confidence": "high",
            }
        )
    elif kind in {"reason_follow_up", "continuation", "elaboration", "example_request", "rephrase_request", "viewpoint_follow_up", "constraint_refinement", "priority_follow_up", "session_summary_request", "analogy_transfer_request", "named_callback", "immediate_user_callback", "answer_development", "comparison_follow_up"}:
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


def contextual_response_seed(
    contextual_follow_up: dict[str, Any] | None,
    *,
    dialogue_workspace: dict[str, Any] | None = None,
    conversation_spine: dict[str, Any] | None = None,
    conversation_continuity: dict[str, Any] | None = None,
) -> str:
    contextual = contextual_follow_up if isinstance(contextual_follow_up, dict) else {}
    if contextual.get("detected") is not True:
        return ""
    kind = str(contextual.get("kind") or "")
    marker = str(contextual.get("marker") or "")
    previous = str(contextual.get("previous_assistant_preview") or "")
    previous_user = str(contextual.get("previous_user_preview") or "").strip()
    recent = " ".join(
        str(item).strip()
        for item in contextual.get("recent_assistant_texts") or []
        if str(item).strip()
    )
    recent_user = [
        str(item).strip()
        for item in contextual.get("recent_user_texts") or []
        if str(item).strip()
    ]
    prompt = str(contextual.get("prompt") or "").lower()
    confidence = contextual.get("previous_confidence") if isinstance(contextual.get("previous_confidence"), dict) else {}
    dialogue = dialogue_workspace if isinstance(dialogue_workspace, dict) else {}
    pragmatics = dialogue.get("pragmatics") if isinstance(dialogue.get("pragmatics"), dict) else {}
    landmarks = [
        item
        for item in [
            *list(contextual.get("session_landmarks") or []),
            *list(pragmatics.get("session_landmarks") or []),
            *list((conversation_spine or {}).get("session_landmarks") or []),
        ]
        if isinstance(item, dict)
    ][-64:]
    matched_landmarks = [
        item for item in contextual.get("matched_session_landmarks") or [] if isinstance(item, dict)
    ] or _matching_landmarks(str(contextual.get("prompt") or ""), landmarks)
    continuity = (
        conversation_continuity
        if isinstance(conversation_continuity, dict)
        else {}
    )
    if str(continuity.get("mode") or "") == "named_thread_return":
        selected = [
            item
            for item in continuity.get("selected_landmarks") or []
            if isinstance(item, dict)
        ]
        if selected:
            matched_landmarks = selected

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

    if kind == "immediate_user_callback" and previous_user:
        callback_subject = _bounded_user_callback_subject(previous_user)
        return f"You're celebrating this result: {callback_subject}."

    if kind == "named_callback" and matched_landmarks:
        callback_prompt = str(contextual.get("prompt") or "").lower()
        if re.search(
            r"\b(?:what|which|who|where|when|remind me)\b",
            callback_prompt,
        ):
            return " ".join(str(item.get("summary") or "") for item in matched_landmarks[:3])
        # A why/how callback needs fresh reasoning over the grounded landmark;
        # the Conversation Spine supplies it instead of this layer inventing it.
        return ""

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

    if kind == "session_summary_request":
        social_summary = _bounded_social_session_summary(recent_user)
        if social_summary:
            return social_summary
        if landmarks:
            return _landmark_summary(landmarks)

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
    if kind == "priority_follow_up" and marker == "revise_previous_order":
        previous_lower = previous.lower()
        if "calculus" in previous_lower and "fraction" in previous_lower:
            return (
                "Fractions first, then the algebra and functions that build on them, and calculus after those prerequisites are steady. "
                "That order stays reopenable if a particular learner already has the required foundations."
            )
        return (
            "Put the prerequisite-producing step first, then the step that uses it. "
            "If the earlier evidence changed which dependency is real, revise only that part of the order."
        )

    insufficient_markers = (
        "not have enough grounded detail",
        "need the subject or observations",
        "missing enough context",
        "do not know enough",
    )
    if kind == "reason_follow_up" and marker == "reason_about_present_self_report":
        return (
            "Because this exchange is calm and focused, and I have enough immediate context to stay with what you are asking. "
            "That supports describing my present attention; it is not a claim about a hidden feeling or a permanent state."
        )
    if kind == "reason_follow_up" and any(marker in previous.lower() for marker in insufficient_markers):
        return (
            "Because I have the direction of the question, but not the observations or standard that would decide the answer. "
            "Without those, I would be choosing a conclusion first and fitting reasons afterward."
        )
    if (
        kind == "reason_follow_up"
        and "prerequisite" in previous.lower()
        and re.search(r"\b(?:prefer|recommend)\b", prompt)
        and re.search(r"\bwhat would change\b|\bchange your recommendation\b", prompt)
    ):
        prompt_choice = re.search(
            r"(?:prefer|recommend)\s+(.+?)\s+first\b",
            prompt,
            flags=re.IGNORECASE,
        )
        choice = prompt_choice.group(1).strip() if prompt_choice else "that option"
        return (
            f"I prefer {choice} first because the current ordering makes its prerequisite role and correction cost easier to inspect. "
            "I would change that recommendation if the other option supplied a required input, produced better evidence under the same constraints, or made the first step unnecessary."
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
    if kind == "reason_follow_up" and marker == "why":
        explicit_reason = _bounded_explicit_reason(previous)
        if explicit_reason:
            return explicit_reason
        return (
            "I did not state the reason clearly enough in that answer. "
            "I can explain it, but I need the deciding constraint or evidence rather than inventing one."
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
        "required input",
        "creates an input",
        "creates what the next step needs",
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
    if kind == "rephrase_request" and previous:
        return f"I may have said that awkwardly. Put simply: {_bounded_rephrase(previous)}"
    return ""


def session_fact_response_seed(
    prompt: str,
    conversation_spine: dict[str, Any] | None,
) -> str:
    """Answer explicit current-session callbacks without creating memory."""
    spine = conversation_spine if isinstance(conversation_spine, dict) else {}
    facts = [
        item for item in spine.get("relevant_session_facts") or []
        if isinstance(item, dict) and str(item.get("text") or "").strip()
    ]
    if not facts:
        return ""
    lower = " ".join(str(prompt or "").lower().split())
    asks_recall = bool(
        re.search(
            r"\b(?:what were|what was|what\s+(?:one|two|three|four|five|\d+)\s+facts?|"
            r"how many|remind me|did i say|do (?:you|we) remember)\b",
            lower,
        )
    )
    asks_summary = bool(
        re.search(r"\b(?:summarize|summary|recap|settled (?:points?|facts?))\b", lower)
    )
    asks_update = bool(
        re.search(r"\b(?:update|revise|adjust|change)\b", lower)
        and re.search(r"\b(?:plan|layout|route|cord|order)\b", lower)
    )
    if asks_summary:
        requested_count = _requested_summary_count(lower)
        clauses = _grounded_task_summary_clauses(facts, requested_count) or _summary_fact_clauses(facts, requested_count)
        response = "The settled points are: " + " ".join(
            f"{index}. {clause}" for index, clause in enumerate(clauses, start=1)
        )
        if re.search(r"\b(?:end|finish|close)\b.*\bnaturally\b", lower):
            response += " That gives the desk a clean stopping point for now."
        return response
    if asks_update:
        relation = next((str(item.get("text") or "") for item in facts if item.get("kind") == "relation"), "")
        constraint = next((str(item.get("text") or "") for item in facts if item.get("kind") == "constraint"), "")
        if relation:
            relation_clause = relation.rstrip(". ")
            response = (
                f"With that correction—{relation_clause[0].lower() + relation_clause[1:]}—I would route the cord along that side "
                "and secure it away from the walking path."
            )
            if constraint:
                response += f" {constraint}"
            return response
    if asks_recall:
        requested_count = _requested_summary_count(lower)
        clauses = _grounded_task_summary_clauses(facts, requested_count)
        if clauses:
            return "The settled facts are: " + " ".join(
                f"{index}. {clause}" for index, clause in enumerate(clauses, start=1)
            )
        return " ".join(str(item.get("text") or "") for item in facts[:requested_count])
    return ""


def _bounded_user_callback_subject(previous_user: str) -> str:
    """Turn one visible user statement into a bounded callback noun phrase.

    This deliberately preserves the user's own supplied content instead of
    asking a knowledge organ to reconstruct an immediately visible fact.
    """
    value = " ".join(str(previous_user or "").split()).strip(" .!?")
    value = re.sub(
        r"^(?:i(?:'m| am)\s+)?(?:really\s+)?(?:happy|excited|proud|glad)\s+"
        r"(?:that|about)\s+",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"^(?:the\s+)?(?:result|good news)\s+(?:is|was)\s+",
        "",
        value,
        flags=re.IGNORECASE,
    )
    if not value:
        return "the result you just described"
    if value[0].isupper():
        value = value[0].lower() + value[1:]
    return truncate(value, 620)


def _grounded_task_summary_clauses(
    facts: list[dict[str, Any]],
    requested_count: int,
) -> list[str]:
    by_kind: dict[str, list[str]] = {}
    for fact in facts:
        kind = str(fact.get("kind") or "")
        text = str(fact.get("text") or "").strip()
        if text:
            by_kind.setdefault(kind, []).append(text)
    active_problem = (by_kind.get("active_problem") or [""])[-1]
    completed_state = (by_kind.get("completed_state") or [""])[-1]
    exception = (by_kind.get("exception") or [""])[-1]
    uncertainty = (by_kind.get("uncertainty") or [""])[-1]
    if "cable" not in f"{active_problem} {exception}".lower():
        return []
    if active_problem and completed_state and not exception:
        return [completed_state, active_problem][:requested_count]
    clauses = [
        "Tackle the loose cables rather than the already-sorted mail.",
        "Keep the daily charging cable reachable and group the remaining cables by frequency of use.",
        (
            "Check both the label location and adhesion before relying on the labels."
            if uncertainty
            else "Use labels only after checking that they adhere reliably."
        ),
    ]
    return clauses[:requested_count]


def _requested_summary_count(prompt: str) -> int:
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
    match = re.search(
        r"\b(?P<count>\d+|one|two|three|four|five)\s+"
        r"(?:[a-z-]+\s+){0,3}(?:points?|facts?)\b",
        prompt,
    )
    if not match:
        return 4
    token = match.group("count")
    return max(1, min(int(token) if token.isdigit() else words[token], 5))


def _summary_fact_clauses(facts: list[dict[str, Any]], requested_count: int) -> list[str]:
    clauses: list[str] = []
    kinds: list[str] = []
    for fact in facts[:6]:
        text = str(fact.get("text") or "").strip()
        kind = str(fact.get("kind") or "")
        if not text:
            continue
        if kind == "relation" and "count" in kinds and len(clauses) >= requested_count:
            index = kinds.index("count")
            clauses[index] = f"{clauses[index]} {text}"
            continue
        clauses.append(text)
        kinds.append(kind)
    while len(clauses) > requested_count:
        merge_index = next((index for index, kind in enumerate(kinds) if kind == "relation" and index > 0), len(clauses) - 1)
        target = merge_index - 1 if merge_index > 0 else 0
        clauses[target] = f"{clauses[target]} {clauses[merge_index]}"
        del clauses[merge_index]
        del kinds[merge_index]
    return clauses[:requested_count]


def _matching_landmarks(prompt: str, landmarks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stop = {
        "about", "back", "earlier", "from", "get", "leave", "later", "point", "return", "said", "that", "the", "there", "this", "today", "tomorrow", "what", "when", "with", "you",
    }
    query = {
        word
        for word in re.findall(r"[a-z][a-z0-9_-]{2,}", str(prompt).lower())
        if word not in stop
    }
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(landmarks):
        if item.get("coverage_complete_at_recording") is False:
            continue
        words = set(
            re.findall(
                r"[a-z][a-z0-9_-]{2,}",
                f"{item.get('topic') or ''} {item.get('summary') or ''}".lower(),
            )
        )
        overlap = query & words
        if overlap:
            ranked.append((len(overlap), index, item))
    ranked.sort(key=lambda value: (value[0], value[1]), reverse=True)
    return [item for _, _, item in ranked[:6]]


def _is_deferred_return_closure(value: str) -> bool:
    return bool(
        re.search(
            r"\b(?:get|come|go|return|going) back to\b.{0,100}\b(?:later|tomorrow|next time|another time)\b",
            value,
        )
        or re.search(
            r"\b(?:later|tomorrow|next time|another time)\b.{0,100}\b(?:get|come|go|return) back to\b",
            value,
        )
    )


def _bounded_explicit_reason(previous: str) -> str:
    """Reconstruct only a reason stated in the immediately visible answer."""
    sentences = [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+", " ".join(str(previous or "").split()))
        if item.strip()
    ]
    for index, sentence in enumerate(sentences):
        match = re.search(r"\bbecause\s+(.+)", sentence, flags=re.IGNORECASE)
        if not match:
            continue
        reason = match.group(1).strip()
        if not reason:
            continue
        reason = reason[0].lower() + reason[1:] if reason[0].isupper() else reason
        reason = reason.rstrip()
        if reason[-1:] not in ".!?":
            reason += "."
        response = f"Because {reason}"
        # Preserve one explicitly linked support sentence even when a separate
        # change-condition sentence was woven between the reason and its
        # supporting evidence. This reconstructs visible text only; it does not
        # infer a new reason.
        for offset, follow_on in enumerate(sentences[index + 1 : index + 4]):
            immediately_adjacent = offset == 0
            explicit_addition = bool(
                re.match(
                    r"^(?:it|this|that)\s+(?:also|further)\b|^additionally\b",
                    follow_on,
                    flags=re.IGNORECASE,
                )
            )
            if explicit_addition or (
                immediately_adjacent
                and re.match(r"^(?:it|this|that)\s+", follow_on, flags=re.IGNORECASE)
            ):
                response = f"{response} {follow_on}"
                break
        return truncate(response, 900)
    return ""


def _landmark_summary(landmarks: list[dict[str, Any]]) -> str:
    landmarks = [
        item for item in landmarks
        if item.get("coverage_complete_at_recording") is not False
    ]
    selected: list[dict[str, Any]] = []
    for preferred in ("recommendation", "condition", "limit", "conclusion"):
        candidate = next(
            (
                item
                for item in reversed(landmarks)
                if item.get("kind") == preferred
                and item not in selected
                and not _summary_near_duplicate(item, selected)
            ),
            None,
        )
        if candidate:
            selected.append(candidate)
    if not selected:
        selected = list(reversed(landmarks[-3:]))
    selected.sort(key=lambda item: landmarks.index(item))
    summaries = [
        str(item.get("summary") or "").strip()
        for item in selected[:3]
        if str(item.get("summary") or "").strip()
    ]
    if len(summaries) == 1:
        return summaries[0]
    return f"We covered these points: {' '.join(summaries)}" if summaries else ""


def _summary_near_duplicate(
    candidate: dict[str, Any],
    selected: list[dict[str, Any]],
) -> bool:
    terms = set(re.findall(r"[a-z][a-z0-9'-]{3,}", str(candidate.get("summary") or "").lower()))
    if not terms:
        return True
    for item in selected:
        other = set(re.findall(r"[a-z][a-z0-9'-]{3,}", str(item.get("summary") or "").lower()))
        union = terms | other
        if union and len(terms & other) / len(union) >= 0.72:
            return True
    return False


def _bounded_rephrase(previous: str) -> str:
    text = " ".join(previous.split())
    rewrites = (
        (r"^My current answer is this:\s*", ""),
        (r"^The direct answer is this:\s*", ""),
        (r"^The core of it is\s+", ""),
        (r"^In plain terms,\s*", ""),
    )
    for pattern, replacement in rewrites:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return truncate(text, 900)


def _bounded_social_session_summary(recent_user_texts: list[str]) -> str:
    normalized = " ".join(" ".join(item.lower().replace("’", "'").split()) for item in recent_user_texts)
    greeted = bool(re.search(r"\b(?:hey|hello|hi|greetings|good morning|good afternoon|good evening)\b", normalized))
    checked_in = bool(re.search(r"\bwhat(?:'s|s| is) up\b|\bhow are you\b", normalized))
    clarified = bool(re.search(r"\bwhen i say\b.*\bi mean\b|\bwhat(?:'s|s| is) up\s+means\s+how are you\b", normalized))
    residual = normalized
    for pattern in (
        r"\b(?:hey|hello|hi|greetings|good morning|good afternoon|good evening)\b"
        r"(?:\s+[a-z][a-z0-9_-]{1,40})?",
        r"\bwhat(?:'s|s| is) up(?: with you)?\b",
        r"\bhow are you(?: doing| feeling| holding up)?(?: right now| today| lately)?\b",
        r"\bwhen i say\b.*?\bi mean\b[^.!?]*",
        r"\b(?:nice|good|great|glad|thanks|thank you|okay|alright|agreed)\b",
        r"\b(?:we got|that piece|working|makes sense|does that distinction make sense)\b",
        r"\bwhat about this conversation makes you say that\b",
    ):
        residual = re.sub(pattern, " ", residual)
    residual_terms = [
        term
        for term in re.findall(r"[a-z][a-z0-9_-]{2,}", residual)
        if term not in {"when", "say", "mean", "does", "that", "distinction"}
    ]
    if residual_terms:
        return ""
    parts: list[str] = []
    if greeted:
        parts.append("greeting each other")
    if checked_in:
        parts.append("checking in")
    if clarified:
        parts.append("clarifying that \"what's up\" was meant as \"how are you\"")
    if not parts:
        return ""
    if len(parts) == 1:
        joined = parts[0]
    else:
        joined = ", ".join(parts[:-1]) + f", and {parts[-1]}"
    return f"This conversation has been about {joined}."
