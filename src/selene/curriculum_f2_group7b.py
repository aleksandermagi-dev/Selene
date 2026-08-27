from __future__ import annotations

from typing import Any


AUTHORIZATION_KEY = "f2_decimal_place_value_operations_v1"
GROUP_KEY = "f2_decimal_place_value_operations_group_7b"

SOURCE_REFS = [
    "curriculum_source:core_knowledge_g4_math_unit4_decimal_place_value_teacher_guide",
    "sha256:a58505988a652d0af23b072ad3560f525c736146e592ad1d299c22a4c7acc00b",
    "https://www.coreknowledge.org/free-resource/ckmath-unit-4-from-hundredths-to-hundred-thousands/",
    "curriculum_source:core_knowledge_g5_math_unit5_decimal_operations_teacher_guide",
    "sha256:7bc2b0d658687b161832bfb01001e710551d1bec4ee2456a9e8101158ec6d239",
    "https://www.coreknowledge.org/free-resource/ckmath-unit-5-place-value-patterns-and-decimal-operations/",
    "curriculum_source:core_knowledge_g5_math_unit6_unlike_fraction_operations_teacher_guide",
    "sha256:3835e997b90ca2501dec58fdf9af886c40aac5183b4319a5bdbba99861d7be79",
    "https://www.coreknowledge.org/free-resource/ckmath-unit-6-more-decimal-and-fraction-operations/",
    "license:CC-BY-NC-SA-4.0-source-artifacts-with-third-party-exclusions",
]

SCOPE = {
    "bands": ["F2"],
    "families": ["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
    "source_ids": [
        "core_knowledge_g4_math_unit4_decimal_place_value_teacher_guide",
        "core_knowledge_g5_math_unit5_decimal_operations_teacher_guide",
        "core_knowledge_g5_math_unit6_unlike_fraction_operations_teacher_guide",
    ],
    "knowledge_classes": ["public_academic_foundation"],
    "group_keys": [GROUP_KEY],
    "retention_rule": "Acquire, Integrate, and Express must all complete with sufficient source-linked comprehension evidence.",
}


def _lesson(
    concept_key: str,
    title: str,
    material: str,
    principles: list[str],
    example: str,
    counterexample: str,
    limits: str,
    vocabulary: list[str],
    distinction: str,
    application: str,
    analogy: str,
    comparison: str,
    participation: str,
    correction: str,
) -> dict[str, Any]:
    return {
        "concept_key": concept_key,
        "title": title,
        "domain": "curriculum.f2.decimal_place_value_operations",
        "material": material,
        "principles": principles,
        "relationships": [
            "This extends retained base-ten place value, fractions as numbers, equivalence, operation meanings, inverse checks, and estimation."
        ],
        "examples": [example],
        "counterexamples": [counterexample],
        "limits": [limits],
        "vocabulary": vocabulary,
        "near_concept_distinctions": [distinction],
        "scope_of_application": (
            "Use for nonnegative base-ten decimals through thousandths and elementary operations whose inputs and results fit the stated lesson bounds. "
            "Identify the whole and place-value units, estimate the expected magnitude, and verify through an inverse operation or independent representation when available."
        ),
        "unresolved_questions": [
            "Which representation - fraction, decimal grid, expanded form, number line, or equal groups - best reveals the value and the operation?"
        ],
        "explanation": (
            f"Decimal notation names base-ten fractional units rather than creating a different kind of number: {analogy} "
            "A result is accepted only when its place values, modeled relationship, and estimated magnitude agree."
        ),
        "application": application,
        "analogies": [analogy],
        "questions": [
            "What whole is being measured, what does each digit count, and what independent check would reveal a misplaced decimal or mismatched unit?"
        ],
        "comparisons": [comparison],
        "participation": participation,
        "correction_response": correction,
        "families": ["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
        "source_ids": list(SCOPE["source_ids"]),
        "source_refs": SOURCE_REFS,
    }


LESSONS: tuple[dict[str, Any], ...] = (
    _lesson(
        "curriculum_f2_decimal_fraction_notation_v1",
        "Decimals name base-ten fractions of an identified whole",
        "Decimal places to the right of the decimal point name tenths, hundredths, and thousandths. One tenth is 0.1, one hundredth is 0.01, and one thousandth is 0.001. Fractions with denominators 10, 100, or 1,000 can be written in decimal notation without changing their magnitude, and equivalent names such as 0.5, 0.50, and 50/100 identify the same point when the whole is fixed.",
        [
            "Identify the whole before interpreting a decimal part.",
            "Read each digit as a count of its positional unit.",
            "Translate between fraction and decimal notation by preserving magnitude, not by copying digits mechanically.",
        ],
        "Thirty-seven hundredths is 37/100 and 0.37; on a hundredths grid it occupies 37 of 100 equal cells.",
        "Reading 0.37 as thirty-seven tenths makes it 3.7, which is ten times too large.",
        "This lesson establishes terminating base-ten representations through thousandths; repeating decimals and rational-number conversion beyond this scope come later.",
        [
            "decimal point: the boundary between whole-number places and fractional base-ten places",
            "tenth: one of ten equal parts of a whole",
            "hundredth: one of one hundred equal parts of a whole",
            "thousandth: one of one thousand equal parts of a whole",
        ],
        "A decimal is a positional notation for a number; it is not evidence that the quantity is approximate.",
        "A container holding 0.65 liter holds 65/100 liter, so both names locate the same amount between 0 and 1 liter.",
        "As dollars and cents can name one amount with whole-dollar and hundredth-dollar units, decimal places name one quantity with progressively smaller base-ten units.",
        "The fraction bar describes division while decimal notation describes base-ten place value; either may name the same magnitude.",
        "Zero point three seven means three tenths and seven hundredths, which combine to thirty-seven hundredths.",
        "If the decimal and fraction land at different points on a number line, I would restore the named whole and rebuild the place-value decomposition.",
    ),
    _lesson(
        "curriculum_f2_decimal_place_value_thousandths_v1",
        "Each neighboring decimal place differs by a factor of ten",
        "In base ten, a place is ten times the value of the place immediately to its right and one tenth the value of the place immediately to its left. Partitioning one hundredth into ten equal parts creates thousandths. Expanded form exposes the amount counted in every place, so 3.268 means 3 + 2/10 + 6/100 + 8/1000.",
        [
            "Treat a digit and its place as separate information: the digit is a count and the place names the unit.",
            "Moving one place left multiplies a place value by ten; moving one place right divides it by ten.",
            "Use expanded form or a scaled number line to reveal magnitude before using a positional shortcut.",
        ],
        "The 6 in 3.268 represents 0.06, which is ten times the 0.006 represented by a 6 in the thousandths place.",
        "Saying the 8 in 3.268 is larger than the 6 because 8 is the larger digit ignores that eight thousandths is smaller than six hundredths.",
        "This uses base-ten nonnegative numbers through thousandths; negative place-value comparison, scientific notation, and other number bases are later extensions.",
        [
            "place value: a digit's value determined by its position",
            "expanded form: a sum showing each digit multiplied by its positional unit",
            "magnitude: the size of a quantity",
            "factor of ten: a multiplicative relationship of ten to one",
        ],
        "A digit tells how many units are present; its position tells which unit is being counted.",
        "A measurement of 4.307 meters decomposes into 4 meters, 3 tenths, 0 hundredths, and 7 thousandths of a meter.",
        "Zooming a number line by a factor of ten reveals that one interval can be partitioned into ten equal intervals of the next smaller place.",
        "A zero inside 4.307 holds the hundredths place; removing it to write 4.37 changes the value rather than merely shortening the notation.",
        "I would read 4.307 by units: four ones, three tenths, zero hundredths, and seven thousandths.",
        "If a place shift changes value in the wrong direction, I would expand both numbers into named units and compare those units directly.",
    ),
    _lesson(
        "curriculum_f2_decimal_compare_round_equivalence_v1",
        "Decimal comparison and rounding depend on magnitude, not digit length",
        "Decimals can be compared by locating them on a number line or comparing corresponding place-value units from left to right. Trailing zeros to the right of the last nonzero decimal digit do not change magnitude. Rounding selects the nearest stated place-value benchmark; it creates an estimate and must not be confused with exact equality.",
        [
            "Compare whole-number parts first, then tenths, hundredths, and thousandths in order.",
            "Add trailing zeros only as equivalent placeholders when aligning places.",
            "Name the rounding place and preserve the distinction between an exact value and its rounded estimate.",
        ],
        "0.7 equals 0.70, and both exceed 0.67 because 70 hundredths is greater than 67 hundredths. Rounded to the nearest tenth, 0.67 is about 0.7.",
        "Claiming 0.67 is greater than 0.7 because 67 is greater than 7 ignores that the digits count different-sized units.",
        "This covers ordinary nonnegative decimals through thousandths; measurement uncertainty and formal error bounds require later instruction.",
        [
            "equivalent decimals: different decimal names for the same magnitude",
            "benchmark: a reference value used for comparison or estimation",
            "rounding: replacing a number with a nearby value at a stated place",
            "trailing zero: a zero after the final nonzero decimal digit that does not change magnitude",
        ],
        "An equivalent decimal is exactly equal to the original; a rounded decimal is usually a nearby estimate.",
        "To order 2.405, 2.45, and 2.054, rewrite only for comparison as 2.405, 2.450, and 2.054, then compare place by place.",
        "Aligning labeled measuring marks lets corresponding units be compared; it does not turn unequal lengths into equal ones.",
        "More written digits do not guarantee a larger decimal: 0.125 is less than 0.8 despite having more decimal places.",
        "I would align the place names, not merely the visible digits: eight tenths is eighty hundredths, so it is larger than twelve hundredths.",
        "If a comparison conflicts with the number line, I would check whether digits were compared without their place-value units or rounding was mistaken for equality.",
    ),
    _lesson(
        "curriculum_f2_decimal_add_subtract_place_value_v1",
        "Decimal addition and subtraction combine like place-value units",
        "Decimal addition and subtraction extend whole-number operations by combining or separating units of the same size. Aligning decimal points aligns ones with ones, tenths with tenths, and hundredths with hundredths. Regrouping exchanges ten of one unit for one of the next larger unit, just as in whole-number arithmetic.",
        [
            "Estimate the result before computing.",
            "Align quantities by place value rather than by their last written digit.",
            "Use equivalent trailing zeros when they make the shared units visible, then verify subtraction with addition when appropriate.",
        ],
        "3.45 + 0.7 becomes 3.45 + 0.70 = 4.15 because hundredths align with hundredths and tenths with tenths.",
        "Writing 3.45 + 0.7 as 3.52 by aligning the final digits combines seven tenths with five hundredths.",
        "This establishes place-value strategies for nonnegative decimal addition and subtraction through hundredths; signed decimals and general algorithm fluency come later.",
        [
            "align: place corresponding units in the same position",
            "regroup: exchange equal value across neighboring places",
            "sum: the result of addition",
            "difference: the result of subtraction",
        ],
        "Decimal points are aligned because they mark the same place-value boundary; the underlying requirement is matching units.",
        "A 2.35-meter board joined to a 0.8-meter board has length 2.35 + 0.80 = 3.15 meters.",
        "It is like adding meters to meters and centimeters to centimeters before exchanging one hundred centimeters for one meter.",
        "A sum should exceed each nonnegative addend, while a difference from subtracting a positive amount should be smaller than the starting value.",
        "Seven tenths is seventy hundredths, so I can add it to forty-five hundredths without changing the amount it represents.",
        "If the exact result disagrees with the estimate, I would inspect place alignment and regrouping before recomputing.",
    ),
    _lesson(
        "curriculum_f2_decimal_multiply_divide_relationships_v1",
        "Decimal multiplication and division preserve scaling and equal-group meanings",
        "Decimal multiplication can be reconstructed through equal groups, area, distribution, or scaling, while decimal division retains measurement and equal-sharing meanings. Place value determines the product or quotient's magnitude. Multiplying or dividing both dividend and divisor by the same nonzero power of ten creates an equivalent division expression because their ratio is unchanged.",
        [
            "Name the operation meaning before moving or placing a decimal point.",
            "Use whole-number facts together with the size of the counted decimal unit.",
            "Check multiplication and division as inverse relationships and compare the result with a magnitude estimate.",
        ],
        "Two groups of 0.43 contain 86 hundredths, so 2 x 0.43 = 0.86. For division, 2 / 0.2 asks how many groups of two tenths fit in two wholes, giving 10.",
        "Claiming 2 / 0.2 = 1 because the digits 2 and 2 match ignores that the divisor is two tenths, not two wholes.",
        "This is bounded to elementary nonnegative decimal products and quotients through hundredths with exact representations; multi-digit standard-algorithm fluency, repeating quotients, and division by zero are not established here.",
        [
            "decimal product: a multiplication result involving decimal quantities",
            "decimal quotient: a division result involving decimal quantities",
            "equal groups: groups with the same amount",
            "equivalent expression: a different expression with the same value",
        ],
        "Multiplication combines factors through scaling or groups; division asks for a missing group count or group size. A decimal point is not moved without preserving that relationship.",
        "If 1.5 kilograms costs 4 dollars per kilogram, the total is 1.5 x 4 = 6 dollars. If 6 liters fill 0.4-liter bottles, 6 / 0.4 = 15 bottles.",
        "Count groups of named pieces: forty-three hundredths twice makes eighty-six hundredths, while counting how many two-tenths pieces tile two wholes gives ten pieces.",
        "Multiplying a positive number by a factor below one shrinks it, while dividing by a positive number below one increases the number of groups that fit.",
        "I would first say what the quotient counts. Two wholes contain twenty tenths, and twenty tenths contain ten groups of two tenths.",
        "If an answer has the wrong scaling direction, I would restore the quantities and units, rebuild the group model, and use the inverse operation to test it.",
    ),
    _lesson(
        "curriculum_f2_decimal_reasonableness_cross_check_v1",
        "Reasonableness checks decimal results through magnitude and independent representations",
        "A decimal answer is not supported by procedure alone. Estimate with nearby benchmarks, predict the operation's direction and scale, then compare the exact result with that prediction. Fraction-decimal translations, expanded form, inverse operations, and contextual units provide independent checks that can reveal a misplaced digit, unsuitable operation, or arithmetic error.",
        [
            "Predict an interval or approximate magnitude before exact calculation.",
            "Use a check that is meaningfully independent of the original steps.",
            "When checks conflict, hold the answer as a candidate and inspect the representation, operation, units, and computation.",
        ],
        "Because 4.8 is near 5 and 2.1 is near 2, 4.8 x 2.1 should be near 10. The exact result 10.08 is plausible; 100.8 would signal a place-value error.",
        "Accepting 0.6 + 0.7 = 0.13 because 6 + 7 = 13 ignores that thirteen tenths regroup to 1.3, not thirteen hundredths.",
        "Reasonableness can detect many errors but does not prove every result; exact verification, evidence quality, and real-world measurement limits remain separate concerns.",
        [
            "reasonableness: agreement with expected magnitude, direction, units, and context",
            "estimate: an intentionally approximate value",
            "inverse check: testing a result with the reverse operation",
            "independent representation: a second model that does not merely repeat the same steps",
        ],
        "An estimate supports a range or scale; it does not replace an exact answer when exactness is required.",
        "For 5.2 - 1.97, estimate about 5 - 2 = 3; the exact difference 3.23 fits. Adding 3.23 + 1.97 recovers 5.20.",
        "Before trusting a map route, compare its distance with a rough map scale and then verify through another landmark; arithmetic checks work similarly.",
        "Repeating the same algorithm is a recomputation, while translating to fractions or applying an inverse operation is a more independent check.",
        "The result is a little above ten, which fits a number slightly below five multiplied by a number slightly above two. I would still verify the exact hundredths.",
        "If two checks disagree, I would not force certainty; I would keep the result as a candidate and identify which assumption, unit, or step diverged.",
    ),
)
