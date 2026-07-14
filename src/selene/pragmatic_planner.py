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


def build_pragmatic_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    dialogue = payload.get("dialogue_workspace") if isinstance(payload.get("dialogue_workspace"), dict) else {}
    pragmatics = dialogue.get("pragmatics") if isinstance(dialogue.get("pragmatics"), dict) else {}
    questions = [truncate(str(item), 480) for item in pragmatics.get("question_units") or [] if str(item).strip()]
    open_loops = [item for item in dialogue.get("open_loops") or [] if isinstance(item, dict)]
    new_ids = {str(item) for item in dialogue.get("new_loop_ids") or [] if str(item)}
    relevant_loops = [item for item in open_loops if not new_ids or str(item.get("id") or "") in new_ids]
    reference = pragmatics.get("resolved_reference") if isinstance(pragmatics.get("resolved_reference"), dict) else None
    indirect = pragmatics.get("indirect_request") if isinstance(pragmatics.get("indirect_request"), dict) else {}
    implicit = _implicit_meaning(prompt, previous_available=pragmatics.get("previous_turn_available") is True)
    ellipsis = _ellipsis_resolution(prompt, reference, str(dialogue.get("active_topic") or ""))
    obligations = _question_obligations(questions, relevant_loops)
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
    ambiguity = _ambiguity_posture(prompt, reference, implicit, ellipsis)
    return _with_guards(
        {
            "status": "pragmatic_plan_ready",
            "version": "v1_bounded_pragmatic_planning",
            "literal_utterance": prompt,
            "dialogue_act": str(intent.get("dialogue_act") or intent.get("intent") or "direct_conversation"),
            "inferred_goal": str(implicit.get("goal") or intent.get("answer_shape") or "respond_directly"),
            "implicit_meaning": implicit,
            "ellipsis_resolution": ellipsis,
            "resolved_reference": reference,
            "response_obligations": obligations,
            "response_units": response_units,
            "answer_strategy": ambiguity["answer_strategy"],
            "ambiguity": ambiguity,
            "meaning_constraints": [
                "answer the literal request before optional expansion",
                "treat implied meaning as bounded inference, not fact",
                "preserve supplied content and uncertainty",
                "leave unsupported questions visibly open",
            ],
            "session_scoped_only": True,
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "provenance_boundary": PRAGMATIC_BOUNDARY,
        }
    )


def evaluate_response_coverage(
    plan: dict[str, Any] | None,
    candidate_text: str,
) -> dict[str, Any]:
    plan = plan if isinstance(plan, dict) else {}
    candidate = truncate(str(candidate_text or ""), 3000)
    candidate_lower = candidate.lower()
    candidate_terms = set(_content_terms(candidate))
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
        score = max(lexical_score, signal_score if expected else 0.0)
        if expected and signal_score > 0:
            score = min(1.0, lexical_score + signal_score)
        addressed = bool(candidate.strip()) and score >= 0.5
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
                "required_terms": sorted(expected),
                "status": "addressed" if addressed else "still_open",
            }
        )
    required = [item for item in items if item.get("status")]
    addressed_count = sum(1 for item in required if item["addressed"])
    return _with_guards(
        {
            "status": "response_coverage_checked",
            "candidate_present": bool(candidate.strip()),
            "obligation_count": len(required),
            "addressed_count": addressed_count,
            "all_required_addressed": addressed_count == len(required),
            "unresolved_count": len(required) - addressed_count,
            "answered_loop_ids": answered_loop_ids,
            "items": items,
            "method": "conservative_visible_text_coverage_not_semantic_certainty",
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "provenance_boundary": PRAGMATIC_BOUNDARY,
        }
    )


def _question_obligations(questions: list[str], loops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    obligations: list[dict[str, Any]] = []
    unused = list(loops)
    for index, question in enumerate(questions):
        loop = next((item for item in unused if str(item.get("question") or "").strip() == question.strip()), None)
        if loop is not None:
            unused.remove(loop)
        obligations.append(
            {
                "id": _obligation_id(question, index),
                "loop_id": str((loop or {}).get("id") or ""),
                "kind": _question_kind(question),
                "source_text": question,
                "topic": str((loop or {}).get("topic") or ""),
                "coverage_terms": _content_terms(question),
                "required": True,
                "inference_level": "literal",
                "goal": "answer_question",
            }
        )
    return obligations


def _question_kind(question: str) -> str:
    lower = question.lower().strip()
    if any(token in lower for token in ("compare", "difference", "versus", " vs ")):
        return "comparison"
    if lower.startswith("why") or " why " in lower:
        return "reason"
    if lower.startswith("how") or " how " in lower:
        return "method"
    if any(token in lower for token in ("which", "what should", "first", "priority")):
        return "choice_or_priority"
    if re.match(r"^(is|are|do|does|did|can|could|would|will|should|have|has)\b", lower):
        return "yes_or_no"
    return "direct_question"


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
) -> dict[str, Any]:
    lower = prompt.lower()
    explicit_uncertainty = any(item in lower for item in ("maybe", "i think", "not sure", "unclear"))
    unresolved_ellipsis = ellipsis.get("detected") is True and not ellipsis.get("resolved_to")
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
        "yes_or_no": ("yes", "no", "can", "cannot", "is", "isn't", "are", "aren't"),
        "implied_request": ("can", "let's", "we can", "start", "help"),
    }
    return 0.5 if any(token in candidate for token in signals.get(kind, ())) else 0.0


def _content_terms(value: str) -> list[str]:
    words = [word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", value)]
    return list(dict.fromkeys(word for word in words if word not in CONTENT_STOP_WORDS))[:20]


def _sentences(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", value.strip()) if item.strip()]


def _obligation_id(value: str, index: int) -> str:
    digest = sha256(f"{index}:{value}".encode("utf-8")).hexdigest()[:12]
    return f"response_obligation_{digest}"


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
