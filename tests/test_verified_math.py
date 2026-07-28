from __future__ import annotations

import pytest

from selene.verified_math import verified_math_status, verify_bounded_math


def test_status_names_the_exact_bounded_math_contract():
    result = verified_math_status()

    assert result["status"] == "verified_math_bounded_arithmetic_ready"
    assert result["deterministic"] is True
    assert result["uses_python_eval"] is False
    assert result["writes_records"] is False
    assert "symbolic algebra" in result["unsupported"]
    assert result["hidden_chain_of_thought_exposed"] is False


@pytest.mark.parametrize(
    ("expression", "value"),
    [
        ("18 * 7", "126"),
        ("2 + 3 * 4", "14"),
        ("(2 + 3) * 4", "20"),
        ("0.1 + 0.2", "0.3"),
        ("1 / 3", "1/3"),
        ("2 ^ 10", "1024"),
        ("-7 // 3", "-3"),
        ("7 % 3", "1"),
    ],
)
def test_exact_arithmetic_is_deterministic(expression, value):
    result = verify_bounded_math({"expression": expression})

    assert result["status"] == "verified_math_result_ready"
    assert result["result_value"] == value
    assert result["verified"] is True
    assert result["answer_confidence"] == "verified_exact"
    assert result["checked_steps"]


def test_prompt_wrapper_and_equality_checks_are_bounded():
    extracted = verify_bounded_math({"prompt": "What is 12 ÷ 4?"})
    correct = verify_bounded_math({"prompt": "Check whether 2 + 2 = 4."})
    incorrect = verify_bounded_math({"expression": "2 + 2 = 5"})

    assert extracted["result_value"] == "3"
    assert extracted["expression_source"] == "prompt_extracted"
    assert correct["exact_result"]["equal"] is True
    assert incorrect["exact_result"]["equal"] is False
    assert "not correct" in incorrect["result_summary"]


def test_plain_language_binary_arithmetic_is_extracted_without_broad_interpretation():
    result = verify_bounded_math(
        {"prompt": "What is 18 times 7? Then return to the lesson question."}
    )

    assert result["status"] == "verified_math_result_ready"
    assert result["expression"] == "18 * 7"
    assert result["result_value"] == "126"
    assert result["expression_source"] == "prompt_extracted"


@pytest.mark.parametrize(
    "payload",
    [
        {"expression": "1 / 0"},
        {"expression": "2 ^ 21"},
        {"expression": "sqrt(9)"},
        {"expression": "value + 1"},
        {"prompt": "Solve for x: x + 2 = 5"},
        {"prompt": "What is 15% of 80?"},
        {"expression": "2 + 2 = 4 = 4"},
        {"expression": "1+" * 121 + "1"},
    ],
)
def test_unsupported_or_unsafe_math_returns_honest_no_answer(payload):
    result = verify_bounded_math(payload)

    assert result["status"] == "verified_math_unable_to_verify"
    assert result["verified"] is False
    assert result["no_answer_reason"]
    assert result["checked_steps"] == []
    assert result["uses_python_eval"] is False
    assert result["answer_confidence"] == "unable_to_verify"
