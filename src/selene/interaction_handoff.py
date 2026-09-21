from __future__ import annotations

import re
from typing import Any

from .registry import truncate
from .social_language_realizer import realize_acknowledgement


INTERACTION_HANDOFF_BOUNDARY = (
    "session_scoped_question_and_response_handoff_only_no_teaching_memory_"
    "identity_governance_profile_authority_or_action"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "session_scoped": True,
    "ordinary_curiosity_is_teaching": False,
    "teaching_activated": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
}

_AFFIRMATIVE = {
    "yes", "yeah", "yep", "yup", "sure", "okay", "ok", "absolutely",
    "go ahead", "please do", "i can", "i will", "of course",
}
_NEGATIVE = {
    "no", "nope", "nah", "not now", "i'd rather not", "id rather not",
    "do not", "don't", "dont",
}
_TENTATIVE = {
    "maybe", "maybe so", "possibly", "not sure", "i'm not sure",
    "im not sure", "i don't know yet", "i dont know yet", "not sure yet",
}
_RESERVED_ACCEPTANCE = {"fine", "all right", "alright"}
_DEFER_MARKERS = (
    "but later", "maybe later", "not right now", "not now", "another time",
    "tomorrow", "when i'm ready", "when im ready",
)


def build_assistant_question_handoff(
    candidate_text: str,
    *,
    explicit_handoff: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preserve one visible Selene question for the next user turn.

    This is general conversation state.  Teaching may use it, but does not own
    ordinary curiosity, permission, or proposal answers.
    """

    if isinstance(explicit_handoff, dict) and explicit_handoff:
        supplied = dict(explicit_handoff)
        supplied.setdefault(
            "expected_response_shape",
            _expected_response_shape(str(supplied.get("question") or "")),
        )
        supplied.setdefault("interaction_owner", "session_question_handoff")
        return _with_guards(supplied)
    questions = [
        item.strip()
        for item in re.findall(
            r"(?:^|(?<=[.!]))\s*([^?]{2,300}\?)",
            str(candidate_text or ""),
        )
    ]
    if not questions:
        return _with_guards(
            {"status": "no_assistant_question_handoff", "question_kind": "none"}
        )
    question = truncate(questions[-1], 320)
    lower = " ".join(question.lower().split())
    direct = bool(re.search(r"\b(?:you|your|we|us)\b", lower))
    if not direct:
        return _with_guards(
            {
                "status": "no_assistant_question_handoff",
                "question_kind": "none",
                "reason": "question_not_directed_to_user",
            }
        )
    if "teach me" in lower or "teach me about" in lower:
        kind = "teaching_invitation"
    elif re.search(r"\bwhy\b", lower):
        kind = "reason_question"
    elif re.search(
        r"\b(?:how was your day|did your day|has your day|are you doing|how are you)\b",
        lower,
    ):
        kind = "personal_curiosity"
    elif re.match(r"^(?:can|could|would|do|did|should|will|are|is|was|were|has|have)\b", lower):
        kind = "permission_or_proposal"
    else:
        kind = "ordinary_curiosity"
    return _with_guards(
        {
            "status": "assistant_question_handoff_ready",
            "question_kind": kind,
            "question": question,
            "expected_response_shape": _expected_response_shape(question),
            "interaction_owner": "session_question_handoff",
            "one_turn_answer_context": True,
            "review_status": "status_only",
        }
    )


def classify_question_response(
    text: str,
    handoff: dict[str, Any] | None,
) -> dict[str, Any]:
    handoff = handoff if isinstance(handoff, dict) else {}
    kind = str(handoff.get("question_kind") or "none")
    normalized = _normalize(text)
    expected = str(
        handoff.get("expected_response_shape")
        or _expected_response_shape(str(handoff.get("question") or ""))
    )
    if not normalized or kind == "none":
        return _response("not_applicable", text, handoff, expected, recognized=False)

    negative = _leading_member(normalized, _NEGATIVE)
    affirmative = _leading_member(normalized, _AFFIRMATIVE)
    reserved = normalized in _RESERVED_ACCEPTANCE
    if expected == "open" and (negative or affirmative or reserved):
        return _response(
            "unclear_for_open_question",
            text,
            handoff,
            expected,
            materially_ambiguous=True,
        )
    if negative:
        answer_kind = "negative_with_reason" if _has_following_content(normalized, negative) else "negative"
        return _response(answer_kind, text, handoff, expected)
    if any(marker in normalized for marker in _DEFER_MARKERS):
        return _response("deferred", text, handoff, expected)
    if normalized in _TENTATIVE or any(
        normalized.startswith(f"{item} ") for item in _TENTATIVE
    ):
        return _response("tentative", text, handoff, expected)
    if affirmative:
        answer_kind = (
            "qualified_affirmative"
            if _has_following_content(normalized, affirmative)
            else "affirmative"
        )
        return _response(answer_kind, text, handoff, expected)
    if reserved and expected == "yes_no":
        return _response("affirmative_reserved", text, handoff, expected)
    if kind == "reason_question" and len(normalized.split()) >= 2:
        return _response("stated_reason", text, handoff, expected)
    if expected == "open":
        return _response("expanded_answer", text, handoff, expected)
    return _response("unrecognized", text, handoff, expected, recognized=False)


def realize_question_response(
    response: dict[str, Any] | None,
    *,
    recent_texts: list[str] | None = None,
) -> dict[str, Any]:
    response = response if isinstance(response, dict) else {}
    answer_kind = str(response.get("answer_kind") or "")
    question_kind = str(response.get("question_kind") or "ordinary_curiosity")
    question = str(response.get("question") or "")
    user_answer = str(response.get("user_answer") or "")
    variation_key = f"{question_kind}|{question}|{answer_kind}|{user_answer}"

    if answer_kind == "stated_reason":
        acknowledgement_kind = "handoff_reason_received"
    elif answer_kind == "deferred":
        acknowledgement_kind = "handoff_deferred"
    elif answer_kind == "tentative":
        acknowledgement_kind = "handoff_tentative"
    elif answer_kind == "affirmative_reserved":
        acknowledgement_kind = "handoff_reserved_acceptance"
    elif answer_kind in {"negative", "negative_with_reason"}:
        acknowledgement_kind = "handoff_negative"
    elif answer_kind == "affirmative":
        acknowledgement_kind = "handoff_affirmative"
    else:
        acknowledgement_kind = ""

    realization = realize_acknowledgement(
        acknowledgement_kind,
        variation_key=variation_key,
        recent_texts=recent_texts,
    )
    candidate = str(realization.get("candidate_text") or "")
    return {
        **response,
        "status": (
            "assistant_question_response_realized"
            if candidate
            else "assistant_question_response_context_only"
        ),
        "response_seed": candidate,
        "response_act": acknowledgement_kind,
        "visible_response_required": bool(candidate),
        "whole_response_template_selected": False,
        "unsupported_content_generated": False,
        **GUARDS,
        "provenance_boundary": INTERACTION_HANDOFF_BOUNDARY,
    }


def _response(
    answer_kind: str,
    text: str,
    handoff: dict[str, Any],
    expected: str,
    *,
    recognized: bool = True,
    materially_ambiguous: bool = False,
) -> dict[str, Any]:
    return {
        "status": (
            "assistant_question_response_interpreted"
            if recognized
            else "assistant_question_response_not_interpreted"
        ),
        "question_kind": str(handoff.get("question_kind") or "ordinary_curiosity"),
        "question": truncate(str(handoff.get("question") or ""), 320),
        "expected_response_shape": expected,
        "answer_kind": answer_kind,
        "user_answer": truncate(str(text or ""), 360),
        "recognized": recognized,
        "materially_ambiguous": materially_ambiguous,
        "user_boundary_accepted": answer_kind in {"negative", "negative_with_reason", "deferred"},
        "may_ask_why_without_pressure": answer_kind in {"negative", "negative_with_reason"},
        "stated_reason_must_be_received_not_overruled": answer_kind in {
            "negative_with_reason",
            "stated_reason",
        },
        "stated_reason_is_user_authored": answer_kind in {
            "negative_with_reason",
            "stated_reason",
        },
        "follow_up_may_clarify_but_may_not_override_user_boundary": True,
        "interaction_owner": "session_question_handoff",
        **GUARDS,
        "provenance_boundary": INTERACTION_HANDOFF_BOUNDARY,
    }


def _expected_response_shape(question: str) -> str:
    normalized = _normalize(question)
    if re.match(
        r"^(?:can|could|would|do|does|did|should|will|are|is|was|were|has|have|had|may|might)\b",
        normalized,
    ):
        return "yes_no"
    return "open"


def _leading_member(value: str, choices: set[str]) -> str:
    return next(
        (
            item
            for item in sorted(choices, key=len, reverse=True)
            if value == item or value.startswith(f"{item} ")
        ),
        "",
    )


def _has_following_content(value: str, opening: str) -> bool:
    remainder = value[len(opening) :].strip()
    return bool(remainder and remainder not in {"please", "thanks", "thank you"})


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9']+", " ", str(value or "").lower().replace("’", "'")).strip()


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        **GUARDS,
        "provenance_boundary": INTERACTION_HANDOFF_BOUNDARY,
    }
