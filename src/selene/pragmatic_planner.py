from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .registry import truncate


PRAGMATIC_BOUNDARY = (
    "conversation_pragmatics_and_response_coverage_only_no_memory_identity_profile_authority_or_hidden_reasoning"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
}

CONTENT_STOP_WORDS = {
    "a", "about", "and", "are", "as", "at", "be", "but", "can", "could", "did", "do", "does", "for",
    "from", "how", "i", "if", "in", "is", "it", "me", "my", "of", "on", "or", "please", "should", "so",
    "that", "the", "this", "to", "we", "what", "when", "where", "which", "who", "why", "will", "with",
    "would", "you", "your", "selene",
}

GENERIC_ALIGNMENT_TERMS = {
    "answer", "change", "first", "make", "next", "question", "reason", "result", "step",
}


def build_pragmatic_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    conversation_spine = (
        payload.get("conversation_spine")
        if isinstance(payload.get("conversation_spine"), dict)
        else {}
    )
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    dialogue = payload.get("dialogue_workspace") if isinstance(payload.get("dialogue_workspace"), dict) else {}
    pragmatics = dialogue.get("pragmatics") if isinstance(dialogue.get("pragmatics"), dict) else {}
    questions = [
        truncate(str(item), 480)
        for item in pragmatics.get("question_units") or []
        if str(item).strip() and not _is_response_format_directive(str(item))
    ]
    open_loops = [item for item in dialogue.get("open_loops") or [] if isinstance(item, dict)]
    new_ids = {str(item) for item in dialogue.get("new_loop_ids") or [] if str(item)}
    relevant_loops = [item for item in open_loops if not new_ids or str(item.get("id") or "") in new_ids]
    reference = pragmatics.get("resolved_reference") if isinstance(pragmatics.get("resolved_reference"), dict) else None
    indirect = pragmatics.get("indirect_request") if isinstance(pragmatics.get("indirect_request"), dict) else {}
    input_interpretation = (
        pragmatics.get("input_interpretation")
        if isinstance(pragmatics.get("input_interpretation"), dict)
        else {}
    )
    utterance_units = [item for item in pragmatics.get("utterance_units") or [] if isinstance(item, dict)] or _utterance_units(prompt)
    correction = pragmatics.get("correction_refinement") if isinstance(pragmatics.get("correction_refinement"), dict) else {}
    contextual = pragmatics.get("contextual_follow_up") if isinstance(pragmatics.get("contextual_follow_up"), dict) else {}
    implicit = _implicit_meaning(prompt, previous_available=pragmatics.get("previous_turn_available") is True)
    ellipsis = _ellipsis_resolution(prompt, reference, str(dialogue.get("active_topic") or ""))
    obligations = _question_obligations(questions, relevant_loops)
    obligations.extend(_unit_obligations(utterance_units, obligations, correction, str(dialogue.get("active_topic") or "")))
    if intent.get("self_state_requested") is True or str(intent.get("intent") or "") == "self_state":
        specialized: list[dict[str, Any]] = []
        for item in obligations:
            source_text = str(item.get("source_text") or "")
            if _contains_self_state_check_in(source_text):
                specialized.append({**item, "kind": "self_state_check_in", "coverage_terms": [], "goal": "answer_present_state"})
            elif _contains_session_summary_request(source_text):
                specialized.append({**item, "kind": "session_summary", "coverage_terms": [], "goal": "summarize_current_session"})
            elif len(obligations) == 1 and str(item.get("kind") or "") == "direct_question":
                specialized.append({**item, "kind": "self_state_check_in", "coverage_terms": [], "goal": "answer_present_state"})
            else:
                specialized.append(item)
        obligations = specialized
    elif str(contextual.get("kind") or "") == "rephrase_request":
        obligations = [
            {
                **item,
                "kind": "rephrase_request" if str(item.get("kind") or "") == "direct_question" else item.get("kind"),
                "coverage_terms": [] if str(item.get("kind") or "") == "direct_question" else item.get("coverage_terms") or [],
                "goal": "rephrase_previous_answer" if str(item.get("kind") or "") == "direct_question" else item.get("goal"),
            }
            for item in obligations
        ]
    if not obligations and (indirect.get("detected") is True or implicit.get("inferred") is True):
        inferred_goal = str(implicit.get("goal") or "respond_to_request")
        obligations.append(
            {
                "id": _obligation_id(prompt, 0),
                "loop_id": "",
                "kind": "implied_request",
                "source_text": prompt,
                "topic": str(dialogue.get("active_topic") or ""),
                "coverage_terms": _content_terms(prompt),
                "required": True,
                "inference_level": "bounded",
                "goal": inferred_goal,
            }
        )
    spine_obligations = [
        item
        for item in conversation_spine.get("open_obligations") or []
        if isinstance(item, dict)
    ]
    if spine_obligations:
        # Once the turn spine exists, downstream organs share its obligation
        # identities instead of reconstructing a slightly different list.
        obligations = [dict(item) for item in spine_obligations]
    thread_braid = (
        conversation_spine.get("thread_braid")
        if isinstance(conversation_spine.get("thread_braid"), dict)
        else pragmatics.get("thread_braid")
        if isinstance(pragmatics.get("thread_braid"), dict)
        else {}
    )
    obligations = _bind_obligations_to_threads(obligations, thread_braid)
    content_seed = truncate(str(payload.get("content_seed") or ""), 1800)
    response_units = [
        {
            "id": _obligation_id(sentence, index),
            "kind": "supported_content",
            "text": sentence,
            "source": "supplied_content_seed",
            "required": True,
        }
        for index, sentence in enumerate(_sentences(content_seed)[:8])
    ]
    ambiguity = _ambiguity_posture(prompt, reference, implicit, ellipsis, input_interpretation)
    return _with_guards(
        {
            "status": "pragmatic_plan_ready",
            "version": (
                "v3_conversation_spine_grounded_obligations"
                if conversation_spine
                else "v2_compositional_dialogue_obligations"
            ),
            "conversation_spine_turn_id": str(conversation_spine.get("turn_id") or ""),
            "conversation_spine_used": bool(conversation_spine),
            "literal_utterance": prompt,
            "dialogue_act": str(intent.get("dialogue_act") or intent.get("intent") or "direct_conversation"),
            "inferred_goal": str(implicit.get("goal") or intent.get("answer_shape") or "respond_directly"),
            "implicit_meaning": implicit,
            "ellipsis_resolution": ellipsis,
            "resolved_reference": reference,
            "utterance_units": utterance_units,
            "correction_refinement": correction,
            "response_obligations": obligations,
            "obligation_sequence": [str(item.get("id") or "") for item in obligations],
            "thread_braid": thread_braid,
            "thread_traversal": thread_braid.get("turn_traversal") or [],
            "response_units": response_units,
            "answer_strategy": ambiguity["answer_strategy"],
            "ambiguity": ambiguity,
            "meaning_constraints": [
                "answer the literal request before optional expansion",
                "treat implied meaning as bounded inference, not fact",
                "preserve supplied content and uncertainty",
                "leave unsupported questions visibly open",
                "carry explicit corrections into the relevant obligation only",
                "preserve visible topic branches, returns, dependencies, and landings",
            ],
            "response_constraints": _response_constraints(pragmatics, correction),
            "session_scoped_only": True,
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "provenance_boundary": PRAGMATIC_BOUNDARY,
        }
    )


def evaluate_response_coverage(
    plan: dict[str, Any] | None,
    candidate_text: str,
    *,
    conversation_spine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = plan if isinstance(plan, dict) else {}
    candidate = truncate(str(candidate_text or ""), 3000)
    candidate_lower = candidate.lower()
    candidate_terms = set(_content_terms(candidate, limit=80))
    items: list[dict[str, Any]] = []
    answered_loop_ids: list[str] = []
    for obligation in plan.get("response_obligations") or []:
        if not isinstance(obligation, dict):
            continue
        expected = {str(item).lower() for item in obligation.get("coverage_terms") or [] if str(item)}
        overlap = sorted(expected & candidate_terms)
        lexical_score = len(overlap) / len(expected) if expected else 0.0
        kind = str(obligation.get("kind") or "direct_question")
        signal_score = _answer_signal_score(kind, candidate_lower)
        minimum_term_matches = 2 if len(expected) >= 6 else 1
        distinctive_expected = expected - GENERIC_ALIGNMENT_TERMS
        distinctive_overlap = sorted(distinctive_expected & candidate_terms)
        topic_terms = set(_content_terms(str(obligation.get("topic") or ""))) - GENERIC_ALIGNMENT_TERMS
        topic_overlap = sorted(topic_terms & candidate_terms)
        distinctive_alignment = not distinctive_expected or bool(distinctive_overlap or topic_overlap)
        semantic_match = len(overlap) >= minimum_term_matches and distinctive_alignment
        signal_can_stand_alone = kind in {
            "correction_update", "yes_or_no", "self_state_check_in", "rephrase_request", "session_summary",
        } or (
            kind == "reason" and not expected
        )
        signal_required = kind in {
            "analogy",
            "constraint_preservation",
            "limitation",
            "reason",
            "requested_output",
            "requested_section",
        }
        score = lexical_score
        if semantic_match and signal_score > 0:
            score = min(1.0, lexical_score + 0.25)
        elif signal_can_stand_alone:
            score = max(score, signal_score)
        addressed = bool(candidate.strip()) and (
            semantic_match and (not signal_required or signal_score > 0)
            or signal_can_stand_alone and signal_score > 0
        )
        loop_id = str(obligation.get("loop_id") or "")
        if addressed and loop_id:
            answered_loop_ids.append(loop_id)
        items.append(
            {
                "obligation_id": str(obligation.get("id") or ""),
                "loop_id": loop_id,
                "kind": kind,
                "addressed": addressed,
                "coverage_score": round(score, 3),
                "matched_terms": overlap,
                "matched_distinctive_terms": distinctive_overlap,
                "matched_topic_terms": topic_overlap,
                "required_terms": sorted(expected),
                "minimum_term_matches": minimum_term_matches,
                "semantic_alignment_required": not signal_can_stand_alone,
                "answer_signal_required": signal_required,
                "distinctive_alignment_required": bool(distinctive_expected),
                "status": "addressed" if addressed else "still_open",
            }
        )
    required = [item for item in items if item.get("status")]
    addressed_count = sum(1 for item in required if item["addressed"])
    obligation_coverage_complete = addressed_count == len(required)
    if conversation_spine:
        # Imported at evaluation time to keep the spine free to construct its
        # initial pragmatic plan without a module-import cycle.
        from .conversation_spine import spine_response_alignment

        spine_alignment = spine_response_alignment(conversation_spine, candidate)
    else:
        spine_alignment = {
            "status": "conversation_spine_not_supplied",
            "aligned": True,
            "required": False,
            "matched_terms": [],
            "distinctive_terms": [],
        }
    grounding_unresolved = int(spine_alignment.get("required") is True and spine_alignment.get("aligned") is not True)
    return _with_guards(
        {
            "status": "response_coverage_checked",
            "candidate_present": bool(candidate.strip()),
            "obligation_count": len(required),
            "addressed_count": addressed_count,
            "all_required_addressed": obligation_coverage_complete and grounding_unresolved == 0,
            "unresolved_count": len(required) - addressed_count + grounding_unresolved,
            "answered_loop_ids": answered_loop_ids,
            "items": items,
            "conversation_spine_alignment": spine_alignment,
            "conversation_spine_used": bool(conversation_spine),
            "method": (
                "conservative_visible_obligation_and_spine_alignment_not_semantic_certainty"
                if conversation_spine
                else "conservative_visible_text_alignment_not_semantic_certainty"
            ),
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "provenance_boundary": PRAGMATIC_BOUNDARY,
        }
    )


def _question_obligations(questions: list[str], loops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    obligations: list[dict[str, Any]] = []
    unused = list(loops)
    for question in questions:
        loop = next((item for item in unused if str(item.get("question") or "").strip() == question.strip()), None)
        if loop is not None:
            unused.remove(loop)
        for part in _compound_question_parts(question):
            if _is_response_format_directive(part):
                continue
            obligations.append(
                {
                    "id": _obligation_id(part, len(obligations)),
                    "loop_id": str((loop or {}).get("id") or ""),
                    "kind": _question_kind(part),
                    "source_text": part,
                    "parent_source_text": question,
                    "topic": str((loop or {}).get("topic") or ""),
                    "coverage_terms": _content_terms(part),
                    "required": True,
                    "inference_level": "literal",
                    "goal": "answer_question",
                }
            )
    return obligations


def _unit_obligations(
    units: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    correction: dict[str, Any],
    active_topic: str,
) -> list[dict[str, Any]]:
    existing_sources = {
        " ".join(str(value or "").lower().split())
        for item in existing
        for value in (item.get("source_text"), item.get("parent_source_text"))
        if str(value or "").strip()
    }
    obligations: list[dict[str, Any]] = []
    substantive_unit_present = any(
        str(item.get("kind") or "") in {"question", "direct_request"}
        for item in units
        if isinstance(item, dict)
    )
    for index, unit in enumerate(units):
        text = truncate(str(unit.get("text") or ""), 480).strip()
        kind = str(unit.get("kind") or "statement")
        if not text or " ".join(text.lower().split()) in existing_sources:
            continue
        if _is_response_format_directive(text):
            continue
        if (
            kind == "indirect_request"
            and substantive_unit_present
            and re.match(r"^(?:let's|lets)\s+think\b.*\btogether[.!]?$", text, flags=re.IGNORECASE)
        ):
            # A collaborative invitation can frame a later concrete request;
            # it is not a second content obligation that the answer must quote.
            continue
        if kind in {"question", "direct_request", "indirect_request"}:
            request_parts = _structured_request_parts(text) if kind != "question" else [text]
            for part in request_parts:
                obligation_kind = (
                    _question_kind(part)
                    if kind == "question"
                    else "requested_section"
                    if len(request_parts) > 1 and ":" in text and re.search(r"\b(?:parts|sections|items)\b", text, flags=re.IGNORECASE)
                    else _request_kind(part)
                )
                obligations.append(
                    {
                        "id": _obligation_id(part, len(existing) + len(obligations) + index),
                        "loop_id": "",
                        "kind": obligation_kind,
                        "dialogue_act": kind,
                        "source_text": part,
                        "parent_source_text": text,
                        "topic": active_topic,
                        "coverage_terms": _content_terms(part),
                        "required": True,
                        "priority": "content",
                        "inference_level": "literal" if kind == "question" else "literal_request",
                        "goal": "answer_question" if kind == "question" else "perform_requested_language_act",
                    }
                )
        elif kind == "correction":
            corrected = str(correction.get("corrected_meaning") or "")
            obligations.append(
                {
                    "id": _obligation_id(text, len(existing) + index),
                    "loop_id": "",
                    "kind": "correction_update",
                    "dialogue_act": "correction",
                    "source_text": text,
                    "topic": active_topic,
                    "coverage_terms": _content_terms(corrected or text),
                    "required": True,
                    "priority": "meaning_update",
                    "inference_level": "literal_correction",
                    "goal": "acknowledge_and_apply_corrected_meaning",
                }
            )
    return obligations


def _request_kind(text: str) -> str:
    lower = text.lower()
    if "analogy" in lower:
        return "analogy"
    if "constraint" in lower or "without losing" in lower or "without dropping" in lower:
        return "constraint_preservation"
    if any(token in lower for token in ("compare", "difference", "versus", " vs ")):
        return "comparison"
    if any(token in lower for token in ("explain", "why", "reason")):
        return "reason"
    if any(token in lower for token in ("steps", "walk me through", "show me how", "how to")):
        return "method"
    if any(token in lower for token in ("choose", "recommend", "priority", "first")):
        return "choice_or_priority"
    return "direct_request"


def _bind_obligations_to_threads(
    obligations: list[dict[str, Any]],
    thread_braid: dict[str, Any],
) -> list[dict[str, Any]]:
    traversal = [item for item in thread_braid.get("turn_traversal") or [] if isinstance(item, dict)]
    if not obligations or not traversal:
        return obligations
    bound: list[tuple[int, int, dict[str, Any]]] = []
    for original_index, obligation in enumerate(obligations):
        terms = set(
            _content_terms(
                " ".join(
                    [
                        str(obligation.get("source_text") or ""),
                        str(obligation.get("topic") or ""),
                    ]
                ),
                limit=40,
            )
        )
        scored: list[tuple[int, int, dict[str, Any]]] = []
        for visit_index, visit in enumerate(traversal):
            overlap = terms & set(_content_terms(str(visit.get("text") or ""), limit=40))
            if overlap:
                scored.append((len(overlap), -visit_index, visit))
        if scored:
            scored.sort(reverse=True, key=lambda item: (item[0], item[1]))
            visit = scored[0][2]
            enriched = {
                **obligation,
                "thread_id": str(visit.get("thread_id") or ""),
                "thread_action": str(visit.get("action") or "continue"),
                "thread_traversal_index": int(visit.get("index") or original_index + 1),
                "dependency_thread_id": str(visit.get("dependency_thread_id") or ""),
            }
            bound.append((int(visit.get("index") or original_index + 1), original_index, enriched))
        else:
            bound.append((len(traversal) + original_index + 1, original_index, dict(obligation)))
    bound.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in bound]


def _response_constraints(pragmatics: dict[str, Any], correction: dict[str, Any]) -> list[dict[str, Any]]:
    constraints: list[dict[str, Any]] = []
    preference = str(pragmatics.get("response_preference") or "")
    if preference:
        constraints.append({"kind": "response_depth", "value": preference, "scope": "current_session_only"})
    if correction.get("detected") is True:
        constraints.append(
            {
                "kind": "correction_scope",
                "corrected_meaning": str(correction.get("corrected_meaning") or ""),
                "replaced_meaning": str(correction.get("replaced_meaning") or ""),
                "scope": "current_session_refinement_only",
            }
        )
    return constraints


def _question_kind(question: str) -> str:
    lower = question.lower().strip()
    if _contains_self_state_check_in(lower):
        return "self_state_check_in"
    if _contains_session_summary_request(lower):
        return "session_summary"
    if any(token in lower for token in ("compare", "difference", "versus", " vs ")):
        return "comparison"
    if lower.startswith("why") or " why " in lower:
        return "reason"
    if lower.startswith("how") or " how " in lower:
        return "method"
    if "limitation" in lower or lower.startswith("what is its limit"):
        return "limitation"
    if re.search(r"\bwhat (?:would|should) you report\b", lower):
        return "requested_output"
    if any(token in lower for token in ("which", "what should", "first", "priority")):
        return "choice_or_priority"
    if re.match(r"^(is|are|do|does|did|can|could|would|will|should|have|has)\b", lower):
        return "yes_or_no"
    return "direct_question"


def _is_response_format_directive(value: str) -> bool:
    text = " ".join(value.lower().strip(" .,:;!?").split())
    return bool(
        re.fullmatch(
            r"(?:in )?(?:one|two|three|four|five|\d+) (?:short |brief )?"
            r"(?:parts|points|sentences|paragraphs|steps)",
            text,
        )
    )


def _contains_self_state_check_in(value: str) -> bool:
    return bool(
        re.search(
            r"\bhow are you(?: doing| feeling| holding up)?\b|\bwhat(?:'s|s| is) up(?: with you)?\b",
            value,
            flags=re.IGNORECASE,
        )
    )


def _contains_session_summary_request(value: str) -> bool:
    return bool(
        re.search(
            r"\b(?:what (?:has|have) (?:this|our) (?:conversation|chat) been about|"
            r"what have we been (?:talking|speaking) about)\b",
            value,
            flags=re.IGNORECASE,
        )
    )


def _compound_question_parts(question: str) -> list[str]:
    """Keep explicit interrogative clauses as separate visible obligations."""
    parts = [
        part.strip(" ,")
        for part in re.split(
            r",\s*(?:and\s+)?(?=(?:what|which|how|why|when|where|who)\b)",
            question,
            flags=re.IGNORECASE,
        )
        if part.strip(" ,")
    ]
    return parts or [question]


def _structured_request_parts(text: str) -> list[str]:
    if "analogy" in text.lower() and re.search(r",\s*without\b", text, flags=re.IGNORECASE):
        parts = [part.strip(" ,.?!") for part in re.split(r",\s*(?=without\b)", text, maxsplit=1, flags=re.IGNORECASE)]
        return [part for part in parts if part]
    if ":" not in text or not re.search(r"\b(?:parts|sections|items)\b", text, flags=re.IGNORECASE):
        return [text]
    tail = text.split(":", 1)[1].strip()
    parts = [
        part.strip(" ,.?!")
        for part in re.split(r",\s*|\s+and\s+", tail, flags=re.IGNORECASE)
        if part.strip(" ,.?!")
    ]
    return parts if len(parts) >= 2 else [text]


def _implicit_meaning(prompt: str, *, previous_available: bool) -> dict[str, Any]:
    lower = " ".join(prompt.lower().split())
    patterns = (
        (("i'm stuck", "im stuck", "i am stuck", "can't figure out", "cannot figure out"), "help_work_through"),
        (("that doesn't sound right", "that does not sound right", "something is off", "not quite"), "invite_correction_or_recheck"),
        (("i'm not sure how", "im not sure how", "i do not know how", "i don't know how"), "explain_or_help_begin"),
        (("we need to think", "let's think", "lets think"), "reason_together"),
    )
    for markers, goal in patterns:
        marker = next((item for item in markers if item in lower), "")
        if marker:
            requires_previous = goal == "invite_correction_or_recheck"
            return {
                "inferred": not requires_previous or previous_available,
                "goal": goal if not requires_previous or previous_available else "",
                "marker": marker,
                "confidence": "bounded",
                "basis": "current wording and immediate dialogue only",
                "not_treated_as_fact": True,
            }
    return {
        "inferred": False,
        "goal": "",
        "marker": "",
        "confidence": "not_inferred",
        "basis": "no bounded pragmatic marker",
        "not_treated_as_fact": True,
    }


def _ellipsis_resolution(prompt: str, reference: dict[str, Any] | None, active_topic: str) -> dict[str, Any]:
    lower = " ".join(prompt.lower().split())
    reference_marker = next(
        (item for item in ("and the other one", "the other one", "that one", "and that") if item in lower),
        "",
    )
    expansion_marker = next((item for item in ("what about", "how about", "why not") if item in lower), "")
    marker = reference_marker or expansion_marker
    if not marker:
        return {"detected": False, "marker": "", "resolved_to": "", "confidence": "not_needed"}
    if reference_marker:
        resolved_to = str((reference or {}).get("resolved_to") or "")
        source = str((reference or {}).get("source") or "")
    else:
        explicit_tail = re.split(re.escape(expansion_marker), lower, maxsplit=1)[-1].strip(" ,.?\t\n")
        resolved_to = explicit_tail or str((reference or {}).get("resolved_to") or active_topic or "")
        source = "current_utterance_explicit" if explicit_tail else str((reference or {}).get("source") or "session_active_topic")
    return {
        "detected": True,
        "marker": marker,
        "resolved_to": truncate(resolved_to, 300),
        "confidence": "bounded" if resolved_to else "unresolved",
        "source": source if resolved_to else "",
        "ask_if_materially_ambiguous": not bool(resolved_to),
    }


def _ambiguity_posture(
    prompt: str,
    reference: dict[str, Any] | None,
    implicit: dict[str, Any],
    ellipsis: dict[str, Any],
    input_interpretation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    lower = prompt.lower()
    explicit_uncertainty = any(item in lower for item in ("maybe", "i think", "not sure", "unclear"))
    unresolved_ellipsis = ellipsis.get("detected") is True and not ellipsis.get("resolved_to")
    input_ambiguities = [
        item
        for item in (input_interpretation or {}).get("ambiguities") or []
        if isinstance(item, dict)
    ]
    if input_ambiguities:
        return {
            "level": "material_input_ambiguity",
            "answer_strategy": "answer_from_unambiguous_context_or_ask_briefly_if_word_changes_answer",
            "reason": "the input detangler found more than one plausible meaning and did not choose one",
            "input_ambiguities": input_ambiguities,
        }
    if unresolved_ellipsis:
        return {
            "level": "material",
            "answer_strategy": "ask_brief_clarifying_question",
            "reason": "elliptical reference has no bounded session referent",
        }
    if explicit_uncertainty:
        return {
            "level": "visible_uncertainty",
            "answer_strategy": "answer_provisionally_and_leave_revision_open",
            "reason": "the user marked uncertainty in the current turn",
        }
    if implicit.get("inferred") is True or reference:
        return {
            "level": "bounded",
            "answer_strategy": "answer_with_visible_bounded_interpretation",
            "reason": "immediate dialogue supports a conservative interpretation",
        }
    return {"level": "low", "answer_strategy": "answer_directly", "reason": "literal request is sufficient"}


def _answer_signal_score(kind: str, candidate: str) -> float:
    signals = {
        "comparison": ("both", "whereas", "while", "difference", "compared", "than"),
        "reason": ("because", "since", "reason", "therefore", "so "),
        "method": ("first", "then", "through", "by ", "step", "start"),
        "choice_or_priority": ("first", "start", "priority", "choose", "should"),
        "limitation": ("limit", "limitation", "but", "however", "only"),
        "requested_output": ("report", "include", "show", "state", "summary"),
        "requested_section": ("design", "pilot", "condition", "section", "part"),
        "analogy": ("analogy", "like", "similar", "think of"),
        "constraint_preservation": ("constraint", "must", "cannot", "do not", "does not"),
        "yes_or_no": ("yes", "no", "can", "cannot", "is", "isn't", "are", "aren't"),
        "implied_request": ("can", "let's", "we can", "start", "help"),
        "direct_request": ("here", "first", "start", "use", "the answer", "result"),
        "correction_update": ("right", "correction", "meant", "changed", "instead", "second", "first"),
        "self_state_check_in": ("i ", "i'm", "my ", "present", "current", "attentive", "here"),
        "rephrase_request": ("put simply", "in plain terms", "said that awkwardly", "what i mean"),
        "session_summary": ("this conversation has been about", "we have been", "we've been"),
    }
    return 0.5 if any(token in candidate for token in signals.get(kind, ())) else 0.0


def _content_terms(value: str, *, limit: int = 20) -> list[str]:
    words = [word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", value)]
    return list(dict.fromkeys(word for word in words if word not in CONTENT_STOP_WORDS))[:limit]


def _sentences(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", value.strip()) if item.strip()]


def _utterance_units(value: str) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    for index, text in enumerate(_sentences(value)):
        lower = text.lower()
        if text.endswith("?"):
            kind = "question"
        elif re.search(r"\b(?:actually|i meant|not what i meant|correction)\b", lower):
            kind = "correction"
        elif re.match(r"^(?:please\s+)?(?:compare|explain|show|tell|help|give|list|summarize|check|walk)\b", lower):
            kind = "direct_request"
        elif re.search(r"\b(?:could you|would you|can you|i need you to|let's|lets)\b", lower):
            kind = "indirect_request"
        else:
            kind = "statement"
        units.append({"id": f"utterance_{index + 1}", "text": truncate(text, 480), "kind": kind, "position": index})
    return units[:12]


def _obligation_id(value: str, index: int) -> str:
    digest = sha256(f"{index}:{value}".encode("utf-8")).hexdigest()[:12]
    return f"response_obligation_{digest}"


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
