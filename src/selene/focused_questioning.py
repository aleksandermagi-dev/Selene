from __future__ import annotations

from typing import Any

from .registry import truncate


FOCUSED_QUESTION_BOUNDARY = (
    "one_material_current_turn_question_decision_only_no_fact_memory_identity_"
    "governance_authority_training_or_action_change"
)

GUARDS: dict[str, Any] = {
    "writes_state": False,
    "memory_write_active": False,
    "retained_knowledge_write_active": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
}


def build_focused_question_decision(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Choose whether one missing detail should delay, qualify, or not affect an answer."""

    payload = payload or {}
    answer_available = payload.get("answer_available") is True
    answer_complete = payload.get("answer_complete") is True
    missing_detail = truncate(str(payload.get("missing_detail") or ""), 500).strip()
    question = truncate(str(payload.get("question") or ""), 900).strip()
    why_it_matters = truncate(str(payload.get("why_it_matters") or ""), 700).strip()
    materially_changes = payload.get("materially_changes_answer") is True
    already_available = payload.get("already_available") is True
    hard_boundary = payload.get("hard_boundary") is True

    if hard_boundary:
        outcome = "unknown_no_justified_question"
        reason = "a genuine boundary owns the turn"
        selected_question = ""
    elif already_available:
        outcome = "answer_now" if answer_available else "unknown_no_justified_question"
        reason = "the detail is already available and must not be requested again"
        selected_question = ""
    elif not materially_changes:
        outcome = "answer_now" if answer_available or answer_complete else "unknown_no_justified_question"
        reason = "the absent detail does not materially change the conclusion, method, or scope"
        selected_question = ""
    elif question and missing_detail and why_it_matters:
        outcome = "ask_one_focused_question"
        reason = "one named missing detail materially changes the answer"
        selected_question = question.rstrip(" ?.!") + "?"
    elif answer_available:
        outcome = "answer_provisionally"
        reason = "a partial answer is supportable, but no justified focused question was supplied"
        selected_question = ""
    else:
        outcome = "unknown_no_justified_question"
        reason = "support is insufficient and no justified focused question was supplied"
        selected_question = ""

    return {
        "status": "focused_question_decision_ready",
        "version": "v1_material_difference_question_gate",
        "outcome": outcome,
        "reason": reason,
        "question": selected_question,
        "missing_detail": missing_detail,
        "why_it_matters": why_it_matters,
        "maximum_questions": 1 if selected_question else 0,
        "answer_first": outcome in {"answer_now", "answer_provisionally"},
        "question_required": outcome == "ask_one_focused_question",
        "repeat_known_information_allowed": False,
        "permission_seeking_question": False,
        "pressure_after_refusal_allowed": False,
        "resume_original_task_after_answer": outcome == "ask_one_focused_question",
        "unknown_is_failure": False,
        "provenance_boundary": FOCUSED_QUESTION_BOUNDARY,
        **GUARDS,
    }
