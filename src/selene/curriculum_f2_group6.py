from __future__ import annotations

from typing import Any


AUTHORIZATION_KEY = "f2_fractions_numbers_equivalence_v1"
GROUP_KEY = "f2_fractions_numbers_equivalence_group_6"

SOURCE_REFS = [
    "curriculum_source:core_knowledge_g3_math_unit5_fractions_teacher_guide",
    "sha256:48819bde5ca8585a3370c2b99c3a082b03d968d9b05503cfa598a857c7c4df45",
    "https://www.coreknowledge.org/free-resource/ckmath-unit-5-fractions-as-numbers/",
    "curriculum_source:core_knowledge_g4_math_unit2_fraction_equivalence_teacher_guide",
    "sha256:7636a5fe8e12774c426a9b135089c58e5d9f843851664e634ce6414fcdb463c1",
    "https://www.coreknowledge.org/free-resource/ckmath-unit-2-fraction-equivalence-and-comparison/",
    "license:CC-BY-NC-SA-4.0-source-artifacts-with-third-party-exclusions",
]

SCOPE = {
    "bands": ["F2"],
    "families": ["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
    "source_ids": [
        "core_knowledge_g3_math_unit5_fractions_teacher_guide",
        "core_knowledge_g4_math_unit2_fraction_equivalence_teacher_guide",
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
        "domain": "curriculum.f2.fractions_numbers_equivalence",
        "material": material,
        "principles": principles,
        "relationships": [
            "This extends retained equal-share, division, multiplication, factor, multiple, measurement, and number-line relationships."
        ],
        "examples": [example],
        "counterexamples": [counterexample],
        "limits": [limits],
        "vocabulary": vocabulary,
        "near_concept_distinctions": [distinction],
        "scope_of_application": (
            "Use for fractions of a clearly identified whole, lengths, and number-line magnitudes. "
            "Preserve the same whole during comparison and verify claims with a diagram, number line, decomposition, or equivalent relationship."
        ),
        "unresolved_questions": [
            "Which representation would make the whole, the equal parts, and the claimed magnitude easiest to inspect?"
        ],
        "explanation": (
            f"This relationship can be reconstructed by identifying the whole and simulating how it is partitioned or traversed: {analogy} "
            "The notation is accepted only when the represented magnitude stays consistent across the chosen model."
        ),
        "application": application,
        "analogies": [analogy],
        "questions": [
            "What is the whole, how large is one part, how many such parts are present, and what second representation can check the result?"
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
        "curriculum_f2_unit_fraction_equal_whole_v1",
        "A unit fraction names one equal part of a specified whole",
        "A fraction describes a magnitude relative to a whole. Partitioning one whole into b equal parts makes each part 1/b of that whole. Equal means equal in the relevant measure, such as length, area, volume, or quantity; pieces that merely look different can still be equal in that measure.",
        [
            "Identify the whole before naming a fraction.",
            "The denominator records how many equal parts make one whole.",
            "One selected part of that partition is the unit fraction 1/b.",
        ],
        "If one identical strip is divided into 4 equal lengths, each length is 1/4 of that strip.",
        "Four unequal pieces do not each become fourths merely because there are four of them.",
        "A fraction of one whole cannot be compared directly with a fraction of a differently sized whole unless the wholes are related explicitly.",
        [
            "whole: the complete quantity chosen as one",
            "partition: a division of a whole into non-overlapping parts",
            "unit fraction: one equal part of a whole, written 1/b",
            "denominator: the number of equal unit parts in one whole",
        ],
        "The denominator names the partition scale; it does not count how many parts are selected.",
        "To interpret one slice from a pan divided into six equal-area slices, identify the pan as the whole and the slice as 1/6 of it.",
        "Imagine folding the same strip into equal sections: the folds set the unit before any sections are counted.",
        "Dividing a fixed whole into more equal parts makes each individual part smaller, so 1/8 is smaller than 1/4 of that same whole.",
        "First I would name the whole. If the six sections are equal in the measure we care about, each section is one sixth; if they are not equal, the fraction label does not fit yet.",
        "If the chosen pieces are unequal or the whole changes, I would revise the model before revising the arithmetic.",
    ),
    _lesson(
        "curriculum_f2_fraction_number_line_composition_v1",
        "A fraction is a number made by counting unit-fraction lengths",
        "The numerator counts how many unit-fraction parts are present. The fraction a/b is a copies of 1/b. On a number line, start at zero and count a intervals of length 1/b. This treats fractions as numbers, allows fractions greater than one, and shows whole numbers as fraction locations.",
        [
            "Count equal intervals rather than tick marks when locating a fraction.",
            "The numerator counts unit-fraction copies; the denominator defines each copy's size.",
            "Fractions greater than one remain ordinary numbers rather than special failures.",
        ],
        "Five intervals of length 1/4 from zero reach 5/4, which is one whole and 1/4 beyond it.",
        "Placing 3/4 at the third tick mark on a line whose intervals are not equal does not establish the fraction.",
        "This lesson builds magnitude and location; mixed-number notation and formal fraction operations receive later treatment.",
        [
            "numerator: the number of unit-fraction parts being counted",
            "interval: the distance between two neighboring number-line marks",
            "improper fraction: a fraction whose numerator is at least its denominator",
            "magnitude: a number's size or position relative to other numbers",
        ],
        "A fraction bar records a division relationship, while a number-line point records the resulting magnitude; they refer to the same number in different ways.",
        "Locate 7/3 by marking thirds and moving seven equal intervals from zero; the point lies at 2 and 1/3.",
        "Unit fractions are equal-sized steps; the numerator says how many steps to take from zero.",
        "The fraction 4/4 and the whole number 1 have different notation but occupy the same number-line location.",
        "Seven thirds means seven one-third steps. Three steps make one whole, six make two wholes, and the seventh lands one third farther.",
        "If I counted marks instead of intervals, I would restart at zero and recount the equal distances, preserving the unit size.",
    ),
    _lesson(
        "curriculum_f2_fraction_equivalence_magnitude_v1",
        "Equivalent fractions are different partitions of the same magnitude",
        "Two fractions are equivalent when they represent the same magnitude relative to the same whole. Splitting every selected part and every part in the whole by the same factor changes the count and the unit size together, so the magnitude stays fixed. Equivalent fractions occupy the same point on a number line.",
        [
            "Keep the whole fixed when testing equivalence.",
            "Change numerator and denominator through the same nonzero scale factor.",
            "Verify equivalence through equal magnitude, not matching appearance alone.",
        ],
        "Dividing each fourth into two equal pieces turns 3/4 into 6/8 without changing the shaded amount or its number-line location.",
        "Changing only 3/4 to 6/4 doubles the counted parts without shrinking the unit parts, so it changes the magnitude.",
        "This establishes elementary positive-fraction equivalence; negative fractions, algebraic rational expressions, and zero denominators are outside this group.",
        [
            "equivalent fractions: fractions with the same magnitude",
            "scale factor: a multiplier applied to both numerator and denominator",
            "decompose: split a unit into smaller equal units without changing the total",
            "common point: one number-line location shared by equivalent names",
        ],
        "Equivalent does not mean written identically; it means preserving the same quantity under a valid transformation.",
        "To test whether 2/3 equals 8/12, split each third into four equal parts or scale both terms by four, then confirm the same point on a number line.",
        "It is the same distance measured with a finer ruler: more marks are counted because every mark represents a smaller unit.",
        "Multiplying both terms by the same factor preserves magnitude; adding the same number to both terms generally does not.",
        "Two thirds and eight twelfths name the same amount because every third was repartitioned into four twelfths and both the selected count and whole-part count changed together.",
        "If a proposed transformation changes only one term or changes the whole, I would reject the equivalence claim and rebuild it from a shared model.",
    ),
    _lesson(
        "curriculum_f2_fraction_comparison_strategy_v1",
        "Fractions are compared by magnitude using a strategy that fits the numbers",
        "Fraction comparison requires the same whole and a valid magnitude relationship. Useful strategies include common denominators, common numerators, number-line location, and benchmarks such as 0, 1/2, and 1. A larger denominator does not by itself mean a larger fraction because it makes each unit part smaller for a fixed whole.",
        [
            "Confirm the fractions refer to the same-sized whole.",
            "Choose a comparison strategy that preserves both magnitudes.",
            "State the comparison and the reason; do not infer it from one symbol alone.",
        ],
        "5/8 is greater than 3/8 because both count eighths and five equal eighths exceed three; 5/8 is also greater than 1/2 because 1/2 equals 4/8.",
        "Concluding that 3/10 is greater than 3/4 because 10 is greater than 4 reverses the unit-size relationship for a fixed whole.",
        "Comparison across different wholes requires first relating those wholes; decimal and percentage comparison are deferred to later groups.",
        [
            "benchmark: a familiar reference magnitude used for comparison",
            "common denominator: a shared unit-fraction size",
            "common numerator: a shared count of differently sized unit fractions",
            "order: an arrangement from lesser to greater magnitude or the reverse",
        ],
        "A comparison symbol records a justified magnitude relationship; it does not create that relationship.",
        "Compare 7/12 and 2/3 by rewriting 2/3 as 8/12; seven twelfths is one twelfth less, so 7/12 < 2/3.",
        "Place both distances on the same path from zero; whichever endpoint is farther right is the greater positive number.",
        "With equal denominators, compare selected-part counts; with equal numerators, the fraction with larger unit parts is greater.",
        "I would first make sure the wholes match, then use a common unit or a benchmark. Here, 2/3 is 8/12, so it is slightly larger than 7/12.",
        "If two strategies disagree, I would inspect the whole, partition sizes, and equivalence step before choosing a result.",
    ),
    _lesson(
        "curriculum_f2_fraction_compose_decompose_v1",
        "Fractions can be composed and decomposed through a shared unit",
        "A fraction can be built by joining copies of one unit fraction and decomposed into sums that preserve the same unit and total magnitude. For example, 5/4 is five one-fourths, which can be regrouped as 4/4 + 1/4 or 1 + 1/4. This supplies the meaning beneath later fraction addition and subtraction procedures.",
        [
            "Name the shared unit fraction before combining or separating parts.",
            "Preserve total magnitude while regrouping unit-fraction copies.",
            "Use equivalence when a different unit is needed; do not combine unlike denominators as bare counts.",
        ],
        "7/6 can be decomposed as 6/6 + 1/6 = 1 + 1/6, or as 3/6 + 4/6, because every term counts sixths.",
        "Adding 1/2 and 1/3 as 2/5 treats unlike unit sizes as though they were one shared unit and does not preserve the magnitude.",
        "This is a conceptual bridge only; general algorithms for adding, subtracting, multiplying, and dividing fractions belong to Group 7.",
        [
            "compose: join parts to form a total",
            "decompose: separate a total into parts that still sum to it",
            "shared unit: one common-sized part used by every term",
            "regroup: rewrite a quantity in an equivalent arrangement",
        ],
        "Decomposition changes how a number is grouped; subtraction changes the magnitude unless the removed part is represented elsewhere in an equality.",
        "If a recipe uses 5 quarter-cups, regroup them as one full cup plus one quarter-cup while preserving all five quarter-cup units.",
        "Five identical quarter-cup scoops can be packed into a group of four and one extra scoop; the container changes, not the amount.",
        "Whole-number regrouping exchanges units by place value; fraction regrouping here exchanges a complete set of denominator-sized parts for one whole.",
        "Five fourths is not a strange exception: it is five equal quarter steps, and four of those steps compose one whole.",
        "If the parts use different units, I would pause the combination and first find an equivalent shared unit rather than add the labels directly.",
    ),
)
