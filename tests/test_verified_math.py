from __future__ import annotations

import pytest

from selene.verified_math import verified_math_status, verify_bounded_math


def test_status_names_the_exact_bounded_math_contract():
    result = verified_math_status()

    assert result["status"] == "verified_math_bounded_arithmetic_ready"
    assert result["deterministic"] is True
    assert result["uses_python_eval"] is False
    assert result["writes_records"] is False
    assert "general symbolic algebra beyond one linear variable" in result["unsupported"]
    assert "simple one-variable linear equations" in result["supported"]
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


def test_number_word_addition_and_equal_slice_remainder_are_verified():
    addition = verify_bounded_math({"prompt": "What is two plus two, and why?"})
    remainder = verify_bounded_math(
        {
            "prompt": (
                "One pizza is cut into four equal slices and I eat one slice. "
                "What fraction remains?"
            )
        }
    )

    assert addition["expression"] == "2 + 2"
    assert addition["result_value"] == "4"
    assert remainder["result_value"] == "3/4"
    assert remainder["word_problem"]["kind"] == "equal_part_remainder"
    assert remainder["result_summary"] == "3/4 remains."


def test_high_confidence_equal_group_word_problem_is_verified_without_guessing():
    result = verify_bounded_math(
        {"prompt": "Three shelves hold four jars each. How many jars are there altogether?"}
    )

    assert result["status"] == "verified_math_result_ready"
    assert result["expression"] == "3 * 4"
    assert result["result_value"] == "12"


def test_explicit_numeric_comparison_can_verify_the_requested_subtraction():
    result = verify_bounded_math(
        {"prompt": "Compare 34 vs 29 and show the subtraction difference."}
    )

    assert result["status"] == "verified_math_result_ready"
    assert result["expression"] == "34 - 29"
    assert result["result_value"] == "5"


@pytest.mark.parametrize(
    "payload",
    [
        {"expression": "1 / 0"},
        {"expression": "2 ^ 21"},
        {"expression": "sqrt(9)"},
        {"expression": "value + 1"},
        {"prompt": "Solve for x and y: x + y = 5"},
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


@pytest.mark.parametrize(
    ("prompt", "stage", "value"),
    [
        ("Convert 2.5 meters to centimeters.", "units_and_measurement", "250"),
        ("Add 1/2 and 1/3.", "fractions_and_decimals", "5/6"),
        ("What is 3/4 as a decimal?", "fractions_and_decimals", "0.75"),
        ("Simplify the ratio 12:18.", "ratios_and_proportions", "2:3"),
        ("If 3 notebooks cost 12 dollars, what would 5 notebooks cost at the same rate?", "ratios_and_proportions", "20"),
        ("Solve for x: 3x + 5 = 20.", "simple_algebraic_relationships", "5"),
        ("Find the area of a rectangle 6 cm by 4 cm.", "elementary_geometry", "24"),
        ("Find the area of a triangle with base 8 m and height 3 m.", "elementary_geometry", "12"),
        ("Find the mean, median, and range of 2, 4, 6, 8.", "bounded_descriptive_statistics", "mean = 5, median = 5, range = 6"),
    ],
)
def test_prerequisite_ordered_math_domains_are_exact_and_independently_verified(prompt, stage, value):
    result = verify_bounded_math({"prompt": prompt})

    assert result["status"] == "verified_math_result_ready"
    assert result["domain_stage"] == stage
    assert result["result_value"] == value
    assert result["independent_verification"]["performed"] is True
    assert result["independent_verification"]["matches_released_result"] is True
    assert result["checked_steps"]
