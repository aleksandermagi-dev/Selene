from __future__ import annotations

from typing import Any


AUTHORIZATION_KEY = "f2_multi_digit_arithmetic_operations_v1"
GROUP_KEY = "f2_multi_digit_arithmetic_operations_group_4"

SEQUENCE_REFS = [
    "curriculum_source:core_knowledge_2023_sequence_k8",
    "sha256:c1c1788776b4e7ee064b7e26002945fa9ba13f111e324dc48ff6147886a530e5",
    "source_locator:Grade 3-5 Mathematics multi-digit arithmetic sequence",
    "license:Core-Knowledge-artifact-notice-controls",
]
ADDITION_REFS = [
    *SEQUENCE_REFS,
    "curriculum_source:core_knowledge_g2_math_unit1",
    "sha256:eae00a4777672b66368780c4ba753c09eff5a18a29afd9bf5cbd55ed915457f7",
    "https://www.coreknowledge.org/wp-content/uploads/2023/08/CKMath_G2U1_AddingSubtractingAndWorkingWithData_Unit_Material_W2.zip",
    "license:CC-BY-NC-SA-4.0-source-specific-notice-controls",
]
MULTIPLICATION_REFS = [
    *SEQUENCE_REFS,
    "curriculum_source:core_knowledge_g2_math_unit8",
    "sha256:029b3123304c1c15676d647fe584700b9171a4c6f62d2070e5aed92f7deb3fd4",
    "https://www.coreknowledge.org/wp-content/uploads/2023/08/CKMath_G2U8_EqualGroups_Unit_Materials_W2.zip",
    "license:CC-BY-NC-SA-4.0-source-specific-notice-controls",
]

SCOPE = {
    "bands": ["F2"],
    "families": ["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
    "source_ids": [
        "core_knowledge_2023_sequence_k8",
        "core_knowledge_g2_math_unit1",
        "core_knowledge_g2_math_unit8",
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
    source_ids: list[str],
    source_refs: list[str],
) -> dict[str, Any]:
    return {
        "concept_key": concept_key,
        "title": title,
        "domain": "curriculum.f2.multi_digit_arithmetic_operations",
        "material": material,
        "principles": principles,
        "relationships": ["This extends retained F1 place-value, equality, inverse-operation, equal-group, array, and sharing foundations."],
        "examples": [example],
        "counterexamples": [counterexample],
        "limits": [limits],
        "vocabulary": vocabulary,
        "near_concept_distinctions": [distinction],
        "scope_of_application": "Use for exact whole-number arithmetic with explicit place-value and operation relationships. Estimate and verify; do not substitute fluency for understanding.",
        "unresolved_questions": ["What representation or inverse check would expose an error in this result?"],
        "explanation": (
            f"This can be reconstructed through the model: {analogy} "
            "The numerical form is accepted only when an equivalent representation or inverse relationship preserves the same quantity."
        ),
        "application": application,
        "analogies": [analogy],
        "questions": ["What quantity relationship is being preserved at each step, and how can the result be checked?"],
        "comparisons": [comparison],
        "participation": participation,
        "correction_response": correction,
        "families": ["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
        "source_ids": source_ids,
        "source_refs": source_refs,
    }


LESSONS: tuple[dict[str, Any], ...] = (
    _lesson(
        "curriculum_f2_place_value_decomposition_equivalence_v1",
        "Multi-digit numbers preserve value across equivalent decompositions",
        "A digit's value depends on its place. A whole number can be decomposed into place-value parts and regrouped into equivalent forms because ten units of one place equal one unit of the next place. For example, 4,382 is 4 thousands + 3 hundreds + 8 tens + 2 ones, and one hundred can be exchanged for ten tens without changing the total.",
        ["Name each digit's place and value.", "Regroup only through ten-to-one place relationships.", "Use expanded form or a model to verify that value is preserved."],
        "3,406 equals 3,000 + 400 + 6; the zero records that there are no tens.",
        "Reading 3,406 as 346 discards a place rather than simplifying the representation.",
        "This lesson covers base-ten whole numbers; other bases, decimals, and signed numbers require later extensions.",
        ["place value: a digit's value determined by its position", "expanded form: a sum showing place-value contributions", "regrouping: exchanging equivalent units between adjacent places", "equivalent: equal in value despite a different representation"],
        "A digit names a symbol; its place value names the quantity that symbol contributes here.",
        "To compare 5,090 and 5,009, align places: the first has nine tens, while the second has nine ones, so 5,090 is larger by 81.",
        "Regrouping resembles exchanging ten one-dollar units for one ten-dollar unit: the form changes while the value does not.",
        "Decomposition separates a number into equivalent parts; rounding deliberately replaces it with a nearby value.",
        "5,090 is greater because the first differing place is the tens place: nine tens exceed zero tens. Subtraction verifies a difference of 81.",
        "If I misalign a place or drop a zero, I would rebuild both numbers in expanded form and correct the comparison from the first differing place.",
        ["core_knowledge_2023_sequence_k8", "core_knowledge_g2_math_unit1"],
        ADDITION_REFS,
    ),
    _lesson(
        "curriculum_f2_multi_digit_addition_regrouping_v1",
        "Multi-digit addition regroups composed quantities without changing the sum",
        "Multi-digit addition combines like place-value units. When a place contains ten or more units, ten are exchanged for one unit in the next place. Partial sums, expanded form, drawings, and the standard algorithm represent the same composition relationship. Alignment by place is essential, and estimation plus subtraction can verify the result.",
        ["Align like places before combining.", "Regroup ten units as one adjacent larger unit.", "Check the exact sum by estimation and inverse subtraction."],
        "278 + 156: ones give 14, recorded as 4 ones and 1 ten; tens then give 13 tens, recorded as 3 tens and 1 hundred; the sum is 434.",
        "Writing 278 + 156 as 2+1, 7+5, 8+6 without carrying the regrouped units produces unrelated place totals rather than one number.",
        "Whole-number addition is covered; decimal alignment and negative quantities belong to later lessons.",
        ["addend: a quantity being added", "sum: the total produced by addition", "partial sum: a place-based contribution to a sum", "regroup: exchange equivalent base-ten units"],
        "Carrying is a written record of regrouping, not a new quantity added from nowhere.",
        "2,487 + 635 decomposes as 2,000 + (400+600) + (80+30) + (7+5), with regrouping producing 3,122.",
        "Addition regrouping is packing loose units into equal bundles of ten while keeping every item.",
        "Estimation checks magnitude; inverse subtraction checks the exact operation relationship.",
        "The exact sum is 3,122. A rough check, 2,500 + 600 ≈ 3,100, fits; 3,122 - 635 returns 2,487.",
        "If the inverse check fails, I would expand both addends, locate the first place whose conserved value breaks, and redo that regrouping.",
        ["core_knowledge_2023_sequence_k8", "core_knowledge_g2_math_unit1"],
        ADDITION_REFS,
    ),
    _lesson(
        "curriculum_f2_multi_digit_subtraction_regrouping_v1",
        "Multi-digit subtraction regroups equivalent units to remove or compare quantities",
        "Multi-digit subtraction removes a quantity, finds a missing part, or measures difference. If a place lacks enough units, one unit from the next place can be decomposed into ten units of the needed place without changing the starting value. Zeros may require regrouping across more than one place. Addition and estimation verify the result.",
        ["Interpret which subtraction relationship the problem asks for.", "Regroup by decomposing adjacent place units while preserving the minuend.", "Verify the difference by adding it to the subtrahend."],
        "402 - 178: regroup one hundred into ten tens, then one ten into ten ones, yielding 3 hundreds, 9 tens, and 12 ones before subtracting to get 224.",
        "Treating a zero as if it could lend ten without receiving value from a higher place creates quantity from nothing.",
        "This covers nonnegative whole-number results; negative numbers and decimal subtraction are later extensions.",
        ["minuend: the starting quantity in a subtraction", "subtrahend: the quantity removed or compared", "difference: the result of subtraction", "decompose: exchange one larger unit for equivalent smaller units"],
        "Regrouping changes representation; subtraction changes the quantity by the stated amount.",
        "3,000 - 746 requires regrouping across zeros; the difference 2,254 is checked because 2,254 + 746 = 3,000.",
        "Regrouping across zeros resembles opening a large sealed bundle, then smaller bundles, until the needed unit size is available.",
        "Removal asks what remains; comparison asks how far apart two quantities are, though both can use subtraction.",
        "The difference is 2,254. Since 3,000 - 700 is about 2,300, the magnitude fits, and addition reconstructs 3,000 exactly.",
        "If I borrow across zeros incorrectly, I would rewrite the minuend as equivalent expanded units and verify every exchange before subtracting.",
        ["core_knowledge_2023_sequence_k8", "core_knowledge_g2_math_unit1"],
        ADDITION_REFS,
    ),
    _lesson(
        "curriculum_f2_multiplication_decomposition_properties_v1",
        "Multi-digit multiplication decomposes equal-group relationships through distributive structure",
        "Multiplication relates number of groups, amount in each group, and total. A factor can be decomposed by place value, and the distributive property preserves the product across partial products: 23 × 4 = (20 × 4) + (3 × 4). Commutative and associative properties can reorganize factors, while estimation and division can check the result.",
        ["Identify the factors' quantitative roles.", "Decompose by place value and preserve every partial product.", "Estimate and use division or another representation to verify."],
        "36 × 7 = (30 × 7) + (6 × 7) = 210 + 42 = 252.",
        "Computing 36 × 7 as 3×7 + 6×7 ignores that the 3 represents three tens.",
        "This establishes whole-number decomposition, not full large-factor algorithm fluency, fractions, decimals, or exponent rules.",
        ["factor: a quantity multiplied by another", "product: the result of multiplication", "partial product: a product formed from decomposed factor parts", "distributive property: multiplying a sum by distributing the factor to each addend"],
        "Repeated addition models equal groups; distributive decomposition scales that relationship through place-value parts.",
        "124 × 6 = 600 + 120 + 24 = 744, preserving hundreds, tens, and ones partial products.",
        "Partial products resemble calculating sections of a rectangular array and then combining their areas.",
        "The commutative property changes factor order; the distributive property separates a factor into added parts.",
        "The product is 744. Since 120 × 6 is 720, 744 is plausible, and 744 ÷ 6 returns 124.",
        "If a partial product loses its place value, I would rebuild the factor in expanded form and reconnect every part before recombining.",
        ["core_knowledge_2023_sequence_k8", "core_knowledge_g2_math_unit8"],
        MULTIPLICATION_REFS,
    ),
    _lesson(
        "curriculum_f2_division_quotient_remainder_inverse_v1",
        "Whole-number division relates groups, group size, quotient, remainder, and the original total",
        "Division can ask how many equal groups can be formed or how many items belong in each equal group. For whole numbers, dividend = divisor × quotient + remainder, where the remainder is at least zero and smaller than the divisor. The remainder must be interpreted in context rather than discarded or automatically rounded. Multiplication reconstructs and verifies the dividend.",
        ["Identify whether the unknown is group count or group size.", "Keep the remainder smaller than the divisor and interpret its meaning.", "Verify divisor × quotient + remainder equals the dividend."],
        "29 ÷ 6 gives quotient 4 and remainder 5 because four groups use 24 and five remain; 6×4+5=29.",
        "Reporting five complete six-seat rows from 29 people invents a person, while reporting only four without mentioning five remaining loses information.",
        "Fractional quotients, decimals, rates, and formal long-division fluency require later instruction.",
        ["dividend: the total being divided", "divisor: the group size or number of groups used to divide", "quotient: the resulting number of groups or amount per group", "remainder: the leftover whole amount smaller than the divisor"],
        "A remainder is part of an exact whole-number result; its practical treatment depends on what the quantities represent.",
        "If 29 people need six-seat vehicles, four full vehicles are not enough: the remainder means a fifth vehicle is required, even though the mathematical quotient is 4 remainder 5.",
        "Division is arranging a total into equal containers, then accounting honestly for anything that does not fill another container.",
        "Grouping division asks how many groups; sharing division asks how much per group.",
        "29 ÷ 6 is 4 remainder 5, verified by 6×4+5. For vehicles, the context requires five vehicles; for complete teams, it means four teams and five people unassigned.",
        "If the reconstruction does not return the dividend or the remainder is too large, I would revise the quotient and remainder before interpreting the context.",
        ["core_knowledge_2023_sequence_k8", "core_knowledge_g2_math_unit8"],
        MULTIPLICATION_REFS,
    ),
)
