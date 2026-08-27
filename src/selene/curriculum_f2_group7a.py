from __future__ import annotations

from typing import Any


AUTHORIZATION_KEY = "f2_fraction_operation_relationships_v1"
GROUP_KEY = "f2_fraction_operation_relationships_group_7a"

SOURCE_REFS = [
    "curriculum_source:core_knowledge_g4_math_unit3_fraction_operations_teacher_guide",
    "sha256:8533241d98212fd527b9c1c57e19bdc575cdc86db5d460b8d6a6794ac8ffab7b",
    "https://www.coreknowledge.org/free-resource/ckmath-unit-3-extending-operations-to-fractions/",
    "curriculum_source:core_knowledge_g5_math_unit2_fraction_quotient_multiplication_teacher_guide",
    "sha256:6ebb771fea9c5a99ef6da8a34adc0926855f7bdb3ebdd1b5e4e8d085cdcce0a5",
    "https://www.coreknowledge.org/free-resource/ckmath-unit-2-fractions-as-quotients-and-fraction-multiplication/",
    "curriculum_source:core_knowledge_g5_math_unit3_fraction_multiply_divide_teacher_guide",
    "sha256:d1d5f3d1b5447228336163af139a70284f27e09e2bfe1f41a0acd26a19daf5e1",
    "https://www.coreknowledge.org/free-resource/ckmath-unit-3-multiplying-and-dividing-fractions/",
    "curriculum_source:core_knowledge_g5_math_unit6_unlike_fraction_operations_teacher_guide",
    "sha256:3835e997b90ca2501dec58fdf9af886c40aac5183b4319a5bdbba99861d7be79",
    "https://www.coreknowledge.org/free-resource/ckmath-unit-6-more-decimal-and-fraction-operations/",
    "license:CC-BY-NC-SA-4.0-source-artifacts-with-third-party-exclusions",
]

SCOPE = {
    "bands": ["F2"],
    "families": ["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
    "source_ids": [
        "core_knowledge_g4_math_unit3_fraction_operations_teacher_guide",
        "core_knowledge_g5_math_unit2_fraction_quotient_multiplication_teacher_guide",
        "core_knowledge_g5_math_unit3_fraction_multiply_divide_teacher_guide",
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
        "domain": "curriculum.f2.fraction_operation_relationships",
        "material": material,
        "principles": principles,
        "relationships": [
            "This extends retained fraction magnitude, equivalence, composition, whole-number operation meanings, inverse checks, factors, and distributive reasoning."
        ],
        "examples": [example],
        "counterexamples": [counterexample],
        "limits": [limits],
        "vocabulary": vocabulary,
        "near_concept_distinctions": [distinction],
        "scope_of_application": (
            "Use for nonnegative elementary fraction operations with an identified whole and justified shared units. "
            "Represent the relationship before applying a procedure, estimate the expected magnitude, and verify with an inverse or independent model when available."
        ),
        "unresolved_questions": [
            "Which model—equal sharing, number line, tape diagram, area, or inverse relationship—would best reveal whether this operation fits the situation?"
        ],
        "explanation": (
            f"The operation can be reconstructed from the quantities and their units: {analogy} "
            "A symbolic result is accepted only when it preserves the modeled relationship and has a reasonable magnitude."
        ),
        "application": application,
        "analogies": [analogy],
        "questions": [
            "What does each quantity represent, what unit is being combined or transformed, and how can the result be checked another way?"
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
        "curriculum_f2_fraction_add_subtract_shared_unit_v1",
        "Fraction addition and subtraction require a shared unit",
        "Addition joins quantities measured in the same-sized unit, and subtraction removes or compares quantities in that unit. Fractions with a common denominator already count the same unit fraction. Fractions with unlike denominators must first be rewritten as equivalent fractions with a useful shared denominator; only the unit-fraction counts are then combined or separated.",
        [
            "Identify the whole and the fractional unit before combining quantities.",
            "Use equivalence to create a shared unit without changing either magnitude.",
            "Combine or subtract numerators only after the denominators name the same-sized parts.",
        ],
        "To add 2/3 and 1/4, rewrite them as 8/12 and 3/12, then combine eleven twelfths: 2/3 + 1/4 = 11/12.",
        "Writing 2/3 + 1/4 as 3/7 adds the labels for two different unit sizes and does not preserve the quantity.",
        "This lesson covers nonnegative fractions and mixed numbers; signed rational arithmetic and algebraic rational expressions come later.",
        [
            "like denominators: denominators already naming the same unit size",
            "unlike denominators: denominators naming different unit sizes",
            "common denominator: one shared partition scale used by every term",
            "sum or difference: the result of joining or separating quantities",
        ],
        "A common denominator is a shared measurement unit, not merely matching symbols produced by a rule.",
        "If a board is 1 1/2 meters long and another is 3/4 meter, rewrite 1/2 as 2/4 and add 1 + 2/4 + 3/4 = 2 1/4 meters.",
        "It is like converting feet and inches to one unit before adding lengths: the quantities stay the same while their labels become compatible.",
        "Equivalent rewriting changes the name of a fraction; addition or subtraction changes the total magnitude.",
        "The thirds and fourths are different-sized pieces, so I would first express both in twelfths. Then the addition is a count of one shared unit.",
        "If the result conflicts with a number-line estimate, I would inspect the equivalence step and the named whole before recomputing.",
    ),
    _lesson(
        "curriculum_f2_fraction_as_quotient_equal_sharing_v1",
        "A fraction can represent the quotient of equal sharing",
        "The fraction a/b can represent a divided by b: a total amount shared equally among b groups gives a/b to each group. This connects fraction notation to the measurement meaning of division and remains valid when the quotient is less than, equal to, or greater than one.",
        [
            "State the total amount, the number of equal groups, and what the quotient measures.",
            "Equal sharing may divide each original whole into smaller parts.",
            "The numerator is the amount shared and the denominator is the number of equal recipient groups in this interpretation.",
        ],
        "Sharing 5 identical loaves equally among 4 tables gives each table 5/4 loaf, or 1 1/4 loaves.",
        "Giving one table 2 loaves and three tables 1 loaf each distributes all 5 loaves but is not equal sharing, so it does not model 5 ÷ 4.",
        "This interpretation assumes divisible quantities and equal sharing; indivisible objects, leftovers, fairness constraints, and real allocation rules may require different treatment.",
        [
            "quotient: the result of division",
            "equal sharing: dividing a total into groups with the same amount",
            "partitive division: finding the size of each group when the group count is known",
            "divisible quantity: a quantity that can meaningfully be partitioned for the situation",
        ],
        "A fraction as quotient describes a division result; a fraction of a quantity describes scaling that quantity, though the two relationships can produce the same value.",
        "Seven liters poured equally into three containers gives 7/3 liters per container, assuming the containers can hold that amount.",
        "Imagine cutting every whole item into enough equal pieces that each recipient can receive the same collection of pieces.",
        "Five divided by four asks for each share; four divided by five asks a different sharing question and produces a different quotient.",
        "Five loaves across four tables means each table receives one whole loaf and one quarter of the remaining loaf, so the equal share is five fourths.",
        "If the proposed shares are unequal or do not recombine to the total, I would rebuild the sharing model rather than defend the quotient.",
    ),
    _lesson(
        "curriculum_f2_whole_number_fraction_multiplication_v1",
        "Multiplying a fraction by a whole number can represent equal fractional groups or scaling",
        "A whole number times a fraction can mean repeated equal groups of the fraction or a scale comparison. The product n × a/b contains n groups of a/b, so it can be represented as (n × a)/b and simplified through equivalence. Distribution preserves mixed-number structure.",
        [
            "Name whether multiplication represents equal groups, area, or multiplicative comparison.",
            "Preserve the denominator when repeating a fixed unit fraction.",
            "Estimate whether the product should be less than, equal to, or greater than the whole-number factor.",
        ],
        "Four groups of 3/5 kilometer total 12/5 kilometers, which is 2 2/5 kilometers.",
        "Changing 4 × 3/5 to 12/20 multiplies the denominator as though each group created a finer partition; the equal-group total is 12/5.",
        "This lesson uses a whole-number factor and nonnegative fraction; products of two fractions are handled in the next relationship.",
        [
            "fractional group: an equal group whose amount is a fraction",
            "scale factor: the multiplicative amount by which a quantity changes",
            "repeated groups: several copies of one equal quantity",
            "distribute: multiply across composed parts while preserving the total",
        ],
        "Repeated addition describes whole-number copies of a fraction; scaling describes how one quantity compares multiplicatively with another.",
        "If each of 6 shelves holds 2/3 meter of books, the occupied length is 6 × 2/3 = 4 meters.",
        "Copy one fraction strip the stated number of times, then join the strips and regroup complete wholes.",
        "Multiplying by a fraction less than one may shrink a quantity, but multiplying that fraction by a whole number larger than one may still create a product larger than one.",
        "Six copies of two thirds contain twelve one-third parts. Three thirds make a whole, so the total is four wholes.",
        "If the denominator changed without repartitioning the whole, I would restore the fixed unit fraction and recount the groups.",
    ),
    _lesson(
        "curriculum_f2_fraction_by_fraction_area_scaling_v1",
        "Multiplying two fractions finds a fraction of a fraction and can be modeled by area",
        "The product a/b × c/d can represent taking a/b of c/d. In an area model, partition one dimension into b equal parts and the other into d equal parts; the overlap occupies a × c of the b × d equal cells. This gives (a × c)/(b × d), with equivalence used to simplify without changing magnitude.",
        [
            "Interpret the product before applying the numerator-and-denominator pattern.",
            "Use the intersecting partitions to explain why both denominators contribute to the new unit size.",
            "Check scaling direction: multiplying a positive quantity by a fraction below one makes it smaller.",
        ],
        "Two thirds of three fifths is 2/3 × 3/5 = 6/15 = 2/5; an area grid shows six selected cells out of fifteen equal cells.",
        "Claiming that 1/2 × 1/3 = 1/5 treats multiplication like fraction addition and does not represent one half of one third.",
        "This is nonnegative elementary fraction multiplication; signed products, algebraic rational expressions, and probability dependence require later teaching.",
        [
            "fraction of a fraction: a multiplicative portion of an already fractional quantity",
            "area model: a rectangle whose side lengths and overlap represent factors and product",
            "overlap: the cells satisfying both fractional selections",
            "multiplicative scaling: changing magnitude by a factor rather than adding an amount",
        ],
        "Multiplication by a fraction is scaling; addition of a fraction is joining another quantity.",
        "If 3/4 of a garden is planted and 2/3 of the planted part is vegetables, vegetables occupy 2/3 × 3/4 = 1/2 of the whole garden.",
        "Shade one fractional direction, then cross-shade the fraction of that region; the overlap is the product.",
        "For positive values, multiplying by 3/2 enlarges while multiplying by 2/3 shrinks; multiplication does not always make a number larger.",
        "I would model two thirds of three fourths as an overlap. Six of twelve equal cells are selected, so the product is one half.",
        "If a product below-one factor unexpectedly enlarges a positive quantity, I would inspect whether the operation or whole was misidentified.",
    ),
    _lesson(
        "curriculum_f2_unit_fraction_division_relationships_v1",
        "Division with unit fractions preserves the two meanings of division",
        "Division can ask either how many groups of a given size fit in a quantity or what one group receives when a quantity is split equally. A whole number divided by 1/b counts b unit-fraction groups per whole. The unit fraction 1/b divided by a whole number n splits that unit fraction into n equal parts, producing 1/(b × n). Multiplication provides an inverse check.",
        [
            "Identify whether the unknown is the number of groups or the size of each group.",
            "Use a tape or number line to preserve the unit-fraction size.",
            "Check the quotient by multiplying it by the divisor to recover the dividend.",
        ],
        "Four divided by 1/3 asks how many thirds fit in four wholes: 12. One third divided by 4 asks for one of four equal parts of a third: 1/12.",
        "Treating 4 ÷ 1/3 and 1/3 ÷ 4 as the same ignores the roles of dividend and divisor and reverses the question.",
        "This elementary lesson covers a whole number divided by a unit fraction and a unit fraction divided by a nonzero whole number. General fraction-by-fraction division is deferred.",
        [
            "measurement division: finding how many groups of a known size fit",
            "partitive division: finding each group's size when the group count is known",
            "dividend: the quantity being divided",
            "divisor: the group size or group count used to divide",
        ],
        "The reciprocal shortcut is a later generalized procedure; this lesson establishes the quantities that any such procedure must preserve.",
        "To find how many quarter-hour blocks fit in 3 hours, calculate 3 ÷ 1/4 = 12 and check that 12 × 1/4 = 3.",
        "For measurement division, tile the whole with known pieces; for sharing division, cut the available piece into the stated number of equal shares.",
        "Dividing by a number below one can increase the group count, while dividing a fraction into several equal groups decreases each group's size.",
        "The wording matters: 'how many thirds fit in four' gives twelve groups, while 'share one third among four' gives one twelfth to each group.",
        "If the quotient answers the reversed division question, I would restore the dividend and divisor roles and verify through multiplication.",
    ),
)
