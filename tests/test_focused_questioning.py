from __future__ import annotations

from selene.focused_questioning import build_focused_question_decision


def test_missing_detail_that_changes_the_answer_yields_one_focused_question():
    result = build_focused_question_decision(
        {
            "answer_available": True,
            "missing_detail": "the target operating system",
            "question": "Which operating system is the target",
            "why_it_matters": "The installation method changes with the platform.",
            "materially_changes_answer": True,
        }
    )

    assert result["outcome"] == "ask_one_focused_question"
    assert result["question"] == "Which operating system is the target?"
    assert result["maximum_questions"] == 1
    assert result["resume_original_task_after_answer"] is True
    assert result["permission_seeking_question"] is False


def test_nonmaterial_or_already_known_detail_does_not_delay_the_answer():
    nonmaterial = build_focused_question_decision(
        {
            "answer_available": True,
            "missing_detail": "preferred heading color",
            "materially_changes_answer": False,
        }
    )
    known = build_focused_question_decision(
        {
            "answer_available": True,
            "missing_detail": "the selected file",
            "question": "Which file did you select?",
            "why_it_matters": "It determines the target.",
            "materially_changes_answer": True,
            "already_available": True,
        }
    )

    assert nonmaterial["outcome"] == "answer_now"
    assert known["outcome"] == "answer_now"
    assert known["question"] == ""
    assert known["repeat_known_information_allowed"] is False


def test_insufficient_support_without_a_justified_question_can_remain_unknown():
    result = build_focused_question_decision(
        {
            "answer_available": False,
            "materially_changes_answer": True,
        }
    )

    assert result["outcome"] == "unknown_no_justified_question"
    assert result["unknown_is_failure"] is False
    assert result["question_required"] is False
