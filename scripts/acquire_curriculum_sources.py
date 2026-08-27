#!/usr/bin/env python3
"""Build Selene's review-only curriculum source shelf.

This utility acquires source artifacts only.  It does not create teaching packets,
prepare comprehension candidates, write Selene memory, or activate knowledge.

The default action writes a catalog.  Pass ``--acquire`` to mirror only entries
whose acquisition mode is explicitly approved below.  Every mirrored file is
hashed and the remote revision is pinned in ``manifest.lock.json``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "local-data" / "curriculum_sources_20260719"
USER_AGENT = "Selene-Curriculum-Source-Shelf/1.0"

SHELF_GUARDS = {
    "purpose": "review-only curriculum source acquisition",
    "teaching_status": "not_prepared",
    "retention_status": "not_retained",
    "runtime_access": False,
    "chat_access": False,
    "memory_write": False,
    "identity_write": False,
    "personality_write": False,
    "governance_write": False,
    "training_or_finetuning": False,
    "autonomy_change": False,
    "approval_required_before_teaching": "Aleks item decision or bounded curriculum authorization",
}


def hf(
    source_id: str,
    repo: str,
    *,
    families: list[str],
    bands: list[str],
    license_id: str,
    role: str,
    risks: list[str],
    max_bytes: int = 450_000_000,
) -> dict[str, Any]:
    return {
        "id": source_id,
        "title": repo,
        "provider": "Hugging Face dataset repository",
        "canonical_url": f"https://huggingface.co/datasets/{repo}",
        "source_kind": "dataset",
        "families": families,
        "bands": bands,
        "role": role,
        "license": license_id,
        "license_scope": "dataset repository; preserve repository license and card",
        "acquisition": {
            "mode": "huggingface_snapshot",
            "repo": repo,
            "revision": "resolve_from_provider",
            "max_bytes": max_bytes,
        },
        "disposition": "mirror_for_source_review",
        "risks": risks,
    }


def github(
    source_id: str,
    repo: str,
    *,
    families: list[str],
    bands: list[str],
    license_id: str,
    role: str,
    risks: list[str],
    max_bytes: int = 500_000_000,
    extra_artifacts: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "id": source_id,
        "title": repo,
        "provider": "GitHub source repository",
        "canonical_url": f"https://github.com/{repo}",
        "source_kind": "open educational resource",
        "families": families,
        "bands": bands,
        "role": role,
        "license": license_id,
        "license_scope": "repository contents at pinned revision; preserve notices and exceptions",
        "acquisition": {
            "mode": "github_archive",
            "repo": repo,
            "revision": "resolve_from_provider",
            "max_bytes": max_bytes,
            "extra_artifacts": extra_artifacts or [],
        },
        "disposition": "mirror_for_source_review",
        "risks": risks,
    }


def catalog_only(
    source_id: str,
    title: str,
    url: str,
    *,
    families: list[str],
    bands: list[str],
    license_id: str,
    role: str,
    reason: str,
    risks: list[str],
) -> dict[str, Any]:
    return {
        "id": source_id,
        "title": title,
        "provider": "authoritative external curriculum provider",
        "canonical_url": url,
        "source_kind": "curriculum catalog",
        "families": families,
        "bands": bands,
        "role": role,
        "license": license_id,
        "license_scope": "verify every selected artifact and edition independently",
        "acquisition": {"mode": "catalog_only", "reason": reason},
        "disposition": "artifact_selection_required",
        "risks": risks,
    }


def direct(
    source_id: str,
    title: str,
    url: str,
    *,
    families: list[str],
    bands: list[str],
    license_id: str,
    role: str,
    risks: list[str],
    max_bytes: int = 750_000_000,
    provider: str = "Core Knowledge Foundation",
    source_kind: str = "bounded curriculum artifact",
    license_scope: str = "artifact contents; retain embedded notices and review third-party exclusions",
) -> dict[str, Any]:
    filename = PurePosixPath(url.split("?", 1)[0]).name
    return {
        "id": source_id,
        "title": title,
        "provider": provider,
        "canonical_url": url,
        "source_kind": source_kind,
        "families": families,
        "bands": bands,
        "role": role,
        "license": license_id,
        "license_scope": license_scope,
        "acquisition": {
            "mode": "direct_artifact",
            "url": url,
            "filename": filename,
            "max_bytes": max_bytes,
        },
        "disposition": "mirror_for_source_review",
        "risks": risks,
    }


SOURCES: list[dict[str, Any]] = [
    hf(
        "hf_gsm8k",
        "openai/gsm8k",
        families=["MATH-2", "MATH-3", "LOGIC-1"],
        bands=["F2", "F3"],
        license_id="MIT",
        role="bounded grade-school word-problem reasoning and answer verification",
        risks=["benchmark solutions are evidence to review, not reasoning templates to imitate", "known ambiguous or erroneous items require review"],
    ),
    hf(
        "hf_oasst1",
        "OpenAssistant/oasst1",
        families=["CONV-1", "CONV-2", "CULT-1"],
        bands=["F2", "F3", "F4"],
        license_id="Apache-2.0",
        role="human multi-turn structure, repair, branching, and multilingual conversation evidence",
        risks=["exclude assistant identity and persona wording", "filter unsafe, unreliable, private, and low-quality turns", "not a factual authority"],
    ),
    hf(
        "hf_everyday_conversations",
        "HuggingFaceTB/everyday-conversations-llama3.1-2k",
        families=["CONV-1", "CONV-2"],
        bands=["F1", "F2"],
        license_id="Apache-2.0",
        role="small ordinary-conversation coverage inventory",
        risks=["synthetic and sometimes canned", "structure reference only; do not imitate voice"],
    ),
    hf(
        "hf_multi_turn_instruct",
        "Glaciohound/Multi-Turn-Instruct",
        families=["CONV-1", "ELA-3"],
        bands=["F2", "F3", "F4"],
        license_id="MIT",
        role="bounded multi-part instruction and follow-up structure",
        risks=["small dataset", "instructional assistant style is not Selene's voice"],
    ),
    hf(
        "hf_insurance_underwriting",
        "snorkelai/Multi-Turn-Insurance-Underwriting",
        families=["LIFE-1", "CONV-2", "RES-1"],
        bands=["F4", "F5"],
        license_id="Apache-2.0",
        role="narrow institutional reasoning, missing-information questions, and qualified conclusions",
        risks=["domain-specific and synthetic", "not financial, legal, or underwriting authority"],
    ),
    hf(
        "hf_exams",
        "mhardalov/exams",
        families=["ELA-3", "MATH-3", "SCI-3", "HIST-2", "LOGIC-1", "CULT-1"],
        bands=["F4", "F5"],
        license_id="CC-BY-SA-4.0",
        role="multilingual cross-domain assessment inventory after prerequisites exist",
        risks=["assessment material is not a curriculum", "language and subject coverage vary", "share-alike and attribution must remain attached"],
    ),
    github(
        "github_topical_chat",
        "alexa/Topical-Chat",
        families=["CONV-1", "CONV-2", "ELA-3", "RES-1"],
        bands=["F2", "F3", "F4"],
        license_id="CDLA-Sharing-1.0",
        role="human-human topic development, knowledge-grounded transitions, and conversational depth",
        risks=["knowledge passages may contain third-party source material", "retain DATALICENSE and publish under the same data license if redistributed", "not Selene voice material"],
    ),
    github(
        "github_open_logic",
        "OpenLogicProject/OpenLogic",
        families=["LOGIC-1", "MATH-3"],
        bands=["F4", "F5"],
        license_id="CC-BY-4.0",
        role="formal logic and proof foundations for later reasoning instruction",
        risks=["begins above elementary informal reasoning", "teach only after prerequisite reasoning language"],
    ),
    github(
        "github_open_science_handbook",
        "Open-Science-Training-Handbook/Open-Science-Training-Handbook_EN",
        families=["RES-1", "SCI-0", "ELA-3"],
        bands=["F4", "F5"],
        license_id="CC0-1.0",
        role="source evaluation, open scholarship, research workflow, and reproducibility",
        risks=["research practice source, not a universal factual authority"],
    ),
    github(
        "github_open_music_theory",
        "openmusictheory/openmusictheory.github.io",
        families=["ART-1", "MATH-1", "CULT-1"],
        bands=["F3", "F4", "F5"],
        license_id="CC-BY-SA-4.0",
        role="music vocabulary, relationships, form, examples, and analytical comparison",
        risks=["audio, notation, embedded media, and third-party assets require per-file review", "Western theory is one tradition, not music as a whole"],
    ),
    github(
        "github_carpentries_shell",
        "swcarpentry/shell-novice",
        families=["TECH-1", "RES-1"],
        bands=["F4", "F5"],
        license_id="CC-BY-4.0",
        role="files, paths, commands, verification, and reproducible technical workflow",
        risks=["examples are lessons, not runtime filesystem authority", "no autonomous command execution"],
    ),
    github(
        "github_carpentries_git",
        "swcarpentry/git-novice",
        families=["TECH-1", "ENG-1", "RES-1"],
        bands=["F4", "F5"],
        license_id="CC-BY-4.0",
        role="version history, reversible change, collaboration, and evidence-preserving workflow",
        risks=["technical knowledge does not grant repository authority"],
    ),
    github(
        "github_carpentries_python",
        "swcarpentry/python-novice-inflammation",
        families=["TECH-1", "ENG-1", "MATH-3", "RES-1"],
        bands=["F4", "F5"],
        license_id="CC-BY-4.0",
        role="programming concepts, data inspection, decomposition, and checked computation",
        risks=["lesson code must remain inert until explicitly inspected", "knowledge does not grant code execution authority"],
    ),
    github(
        "github_met_open_access",
        "metmuseum/openaccess",
        families=["ART-1", "HIST-2", "CULT-1"],
        bands=["F2", "F3", "F4", "F5"],
        license_id="CC0-1.0",
        role="provenanced art-object metadata across cultures and historical periods",
        risks=["catalog metadata may be incomplete or revised", "images are not included and require object-level rights checks", "do not imply museum endorsement"],
        extra_artifacts=[
            {
                "path": "MetObjects.csv",
                "url_template": "https://media.githubusercontent.com/media/metmuseum/openaccess/{revision}/MetObjects.csv",
            }
        ],
    ),
    direct(
        "core_knowledge_2023_sequence_k8",
        "2023 Core Knowledge Sequence for Grades K-8",
        "https://www.coreknowledge.org/wp-content/uploads/2023/03/CK_Sequence2023_GK8_W3.pdf",
        families=["ELA-1", "ELA-2", "MATH-1", "MATH-2", "SCI-0", "SCI-1", "SCI-2", "HIST-1", "HIST-2", "CIV-1", "ART-1", "CULT-1"],
        bands=["F1", "F2", "F3"],
        license_id="Core Knowledge curriculum terms; artifact notice controls",
        role="grade-by-grade prerequisite and coverage sequence, not stand-alone teaching material",
        risks=["U.S.-centered shared-knowledge sequence requires cultural supplementation", "sequence identifies coverage but does not itself prove understanding"],
    ),
    direct(
        "core_knowledge_g1_ela_unit7",
        "CKLA Grade 1 Unit 7: Kay and Martez",
        "https://www.coreknowledge.org/wp-content/uploads/2016/12/CKLA_G1_Unit-7.zip",
        families=["ELA-1", "ELA-2"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational phonics, syntax, punctuation, agreement, and writing-process pilot",
        risks=["older edition", "decodable text is teaching scaffolding, not conversational voice", "review all embedded media and notices"],
    ),
    direct(
        "core_knowledge_g1_math_unit7",
        "CKMath Grade 1 Unit 7: Geometry and Time",
        "https://www.coreknowledge.org/wp-content/uploads/2023/08/CKMath_G1U7_GeometryAndTime_Unit_Materials_W2.zip",
        families=["MATH-1", "MATH-2", "ELA-1"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational geometry, halves/fourths, measurement language, and time pilot",
        risks=["one unit is not full elementary mathematics", "review answer keys separately from concept instruction"],
    ),
    direct(
        "core_knowledge_g1_math_unit1",
        "CKMath Grade 1 Unit 1: Adding, Subtracting, and Working with Data",
        "https://www.coreknowledge.org/wp-content/uploads/2023/08/CKMath_G1U1_AddingSubtractingAndWorkingWithData_Unit_Materials_W2.zip",
        families=["MATH-1", "MATH-2", "ELA-1"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational addition, subtraction, categorical data, tally, representation, and interpretation pilot",
        risks=["one unit is not full elementary arithmetic", "procedural fluency does not replace conceptual operation relationships"],
    ),
    direct(
        "core_knowledge_g1_math_unit6",
        "CKMath Grade 1 Unit 6: Length Measurements Within 120 Units",
        "https://www.coreknowledge.org/wp-content/uploads/2023/08/CKMath_G1U6_LengthMeasurementsWithin120Units_Unit_Materials_W2.zip",
        families=["MATH-1", "MATH-2", "SCI-0", "ELA-1"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational length attribute, direct and indirect comparison, unit iteration, and measurement communication pilot",
        risks=["one unit is not full measurement instruction", "measurements require named units and aligned endpoints"],
    ),
    direct(
        "core_knowledge_k_math_unit1",
        "CKMath Kindergarten Unit 1: Math in Our World",
        "https://www.coreknowledge.org/wp-content/uploads/2023/08/CKMath_GKU1_MathInOurWorld_Unit_Materials_W2.zip",
        families=["MATH-1", "ELA-1"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational counting, cardinal quantity, grouping, same, more, fewer, and comparison pilot",
        risks=["one unit is not full kindergarten mathematics", "review answer keys and third-party media separately from concept instruction"],
    ),
    direct(
        "core_knowledge_g1_math_unit4",
        "CKMath Grade 1 Unit 4: Numbers to 99",
        "https://www.coreknowledge.org/wp-content/uploads/2023/08/CKMath_G1U4_NumbersTo99_Unit_Materials_W2.zip",
        families=["MATH-1", "MATH-2", "ELA-1"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational base-ten grouping, tens and ones, number representation, and two-digit comparison pilot",
        risks=["one unit is not full elementary mathematics", "comparison symbols follow conceptual quantity comparison rather than replacing it"],
    ),
    direct(
        "core_knowledge_g2_math_unit1",
        "CKMath Grade 2 Unit 1: Adding, Subtracting, and Working with Data",
        "https://www.coreknowledge.org/wp-content/uploads/2023/08/CKMath_G2U1_AddingSubtractingAndWorkingWithData_Unit_Material_W2.zip",
        families=["MATH-1", "MATH-2", "ELA-1"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded picture-graph, bar-graph, categorical-data, comparison, and interpretation foundation",
        risks=["one unit is not full data literacy", "a graph represents supplied data and does not establish causes"],
    ),
    direct(
        "core_knowledge_g2_math_unit6",
        "CKMath Grade 2 Unit 6: Geometry, Time, and Money",
        "https://www.coreknowledge.org/wp-content/uploads/2023/08/CKMath_G2U6_GeometryTimeAndMoney_Unit_Materials_W2.zip",
        families=["MATH-1", "MATH-2", "ELA-1", "LIFE-1"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded coin-value, equivalent-value, and addition/subtraction money context",
        risks=["money examples teach mathematical value relationships, not financial advice", "currency units and designs are jurisdiction- and time-specific"],
    ),
    direct(
        "core_knowledge_g2_math_unit8",
        "CKMath Grade 2 Unit 8: Equal Groups",
        "https://www.coreknowledge.org/wp-content/uploads/2023/08/CKMath_G2U8_EqualGroups_Unit_Materials_W2.zip",
        families=["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded equal-groups, odd/even, pairs, arrays, rows, columns, and repeated-addition foundation",
        risks=["this is a conceptual foundation rather than full multiplication or division fluency", "array orientation does not change the total quantity"],
    ),
    direct(
        "core_knowledge_g3_math_unit6_teacher_guide",
        "CKMath Grade 3 Unit 6: Measuring Length, Time, Liquid Volume, and Weight — Teacher Guide",
        "https://www.coreknowledge.org/wp-content/uploads/2023/09/CKMath_G3U6_MeasuringLengthTimeLiquidVolumeAndWeight_TG_W2.pdf",
        families=["MATH-1", "MATH-2", "SCI-0", "ELA-1"],
        bands=["F1", "F2"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded bridge from early direct comparison into mass and liquid-volume measurement with shared informal and metric units",
        risks=[
            "the full unit is Grade 3; F1 use is restricted to explicitly identified prerequisite concepts and foundational comparison",
            "the curriculum uses weight in an elementary everyday sense; technical mass and gravitational weight must remain distinct",
            "review answer keys and third-party media separately from concept instruction",
        ],
    ),
    direct(
        "core_knowledge_g3_math_unit5_fractions_teacher_guide",
        "CKMath Grade 3 Unit 5: Fractions as Numbers — Teacher Guide",
        "https://www.coreknowledge.org/wp-content/uploads/2023/09/CKMath_G3U5_FractionsAsNumbers_TG_W2.pdf",
        families=["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
        bands=["F2"],
        license_id="CC-BY-NC-SA-4.0; artifact notice and third-party exclusions control",
        role="bounded fractions-as-numbers, unit-fraction, number-line, composition, equivalence, and comparison foundation",
        risks=[
            "noncommercial and share-alike terms apply to adapted source content",
            "third-party images and media are not automatically covered by the curriculum license",
            "retain only independently written concept instruction; do not import classroom scripts, worksheets, or branded activities",
        ],
    ),
    direct(
        "core_knowledge_g4_math_unit2_fraction_equivalence_teacher_guide",
        "CKMath Grade 4 Unit 2: Fraction Equivalence and Comparison — Teacher Guide",
        "https://www.coreknowledge.org/wp-content/uploads/2023/09/CKMath_G4U2_FractionEquivalenceAndComparison_TG_W2.pdf",
        families=["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
        bands=["F2"],
        license_id="CC-BY-NC-SA-4.0; artifact notice and third-party exclusions control",
        role="bounded fraction-equivalence, benchmark, magnitude-comparison, and ordering foundation",
        risks=[
            "noncommercial and share-alike terms apply to adapted source content",
            "third-party images and media are not automatically covered by the curriculum license",
            "retain only independently written concept instruction; do not import classroom scripts, worksheets, or branded activities",
        ],
    ),
    direct(
        "core_knowledge_g4_math_unit3_fraction_operations_teacher_guide",
        "CKMath Grade 4 Unit 3: Extending Operations to Fractions — Teacher Guide",
        "https://www.coreknowledge.org/wp-content/uploads/2023/09/CKMath_G4U3_ExtendingOperationsToFractions_TG_W2.pdf",
        families=["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
        bands=["F2"],
        license_id="CC-BY-NC-SA-4.0; artifact notice and third-party exclusions control",
        role="bounded whole-number-by-fraction multiplication and like-denominator addition/subtraction foundation",
        risks=[
            "noncommercial and share-alike terms apply to adapted source content",
            "third-party images and media are not automatically covered by the curriculum license",
            "retain only independently written concept instruction; do not import classroom scripts, worksheets, or branded activities",
        ],
    ),
    direct(
        "core_knowledge_g5_math_unit2_fraction_quotient_multiplication_teacher_guide",
        "CKMath Grade 5 Unit 2: Fractions as Quotients and Fraction Multiplication — Teacher Guide",
        "https://www.coreknowledge.org/wp-content/uploads/2023/09/CKMath_G5U2_FractionsAsQuotientsAndFractionMultiplication_TG_W2.pdf",
        families=["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
        bands=["F2"],
        license_id="CC-BY-NC-SA-4.0; artifact notice and third-party exclusions control",
        role="bounded fraction-as-quotient and whole-number-by-fraction multiplication bridge",
        risks=[
            "noncommercial and share-alike terms apply to adapted source content",
            "third-party images and media are not automatically covered by the curriculum license",
            "retain only independently written concept instruction; do not import classroom scripts, worksheets, or branded activities",
        ],
    ),
    direct(
        "core_knowledge_g5_math_unit3_fraction_multiply_divide_teacher_guide",
        "CKMath Grade 5 Unit 3: Multiplying and Dividing Fractions — Teacher Guide",
        "https://www.coreknowledge.org/wp-content/uploads/2023/09/CKMath_G5U3_MultiplyingAndDividingFractions_TG_W2.pdf",
        families=["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
        bands=["F2"],
        license_id="CC-BY-NC-SA-4.0; artifact notice and third-party exclusions control",
        role="bounded fraction-product area relationships and unit-fraction division foundation",
        risks=[
            "noncommercial and share-alike terms apply to adapted source content",
            "the elementary unit does not establish every possible fraction-division case",
            "retain only independently written concept instruction; do not import classroom scripts, worksheets, or branded activities",
        ],
    ),
    direct(
        "core_knowledge_g4_math_unit4_decimal_place_value_teacher_guide",
        "CKMath Grade 4 Unit 4: From Hundredths to Hundred-Thousands — Teacher Guide",
        "https://www.coreknowledge.org/wp-content/uploads/2023/09/CKMath_G4U4_FromHundredthsToHundredThousands_TG_W2.pdf",
        families=["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
        bands=["F2"],
        license_id="CC-BY-NC-SA-4.0; artifact notice and third-party exclusions control",
        role="bounded tenths, hundredths, fraction-decimal notation, comparison, and base-ten place-value foundation",
        risks=[
            "noncommercial and share-alike terms apply to adapted source content",
            "third-party images and media are not automatically covered by the curriculum license",
            "retain only independently written concept instruction; do not import classroom scripts, worksheets, or branded activities",
        ],
    ),
    direct(
        "core_knowledge_g5_math_unit5_decimal_operations_teacher_guide",
        "CKMath Grade 5 Unit 5: Place Value Patterns and Decimal Operations — Teacher Guide",
        "https://www.coreknowledge.org/wp-content/uploads/2023/09/CKMath_G5U5_PlaceValuePatternsAndDecimalOperations_TG_W2.pdf",
        families=["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
        bands=["F2"],
        license_id="CC-BY-NC-SA-4.0; artifact notice and third-party exclusions control",
        role="bounded thousandths place value, decimal comparison and rounding, and place-value-grounded decimal operations",
        risks=[
            "noncommercial and share-alike terms apply to adapted source content",
            "Grade 6 fluency is not implied by this Grade 5 conceptual foundation",
            "retain only independently written concept instruction; do not import classroom scripts, worksheets, diagrams, or branded activities",
        ],
    ),
    direct(
        "core_knowledge_g5_math_unit6_unlike_fraction_operations_teacher_guide",
        "CKMath Grade 5 Unit 6: More Decimal and Fraction Operations — Teacher Guide",
        "https://www.coreknowledge.org/wp-content/uploads/2023/09/CKMath_G5U6_MoreDecimalAndFractionOperations_TG_W2.pdf",
        families=["MATH-1", "MATH-2", "ELA-1", "LOGIC-1"],
        bands=["F2"],
        license_id="CC-BY-NC-SA-4.0; artifact notice and third-party exclusions control",
        role="bounded unlike-denominator addition/subtraction and fraction-product reasonableness bridge",
        risks=[
            "noncommercial and share-alike terms apply to adapted source content",
            "decimal and unit-conversion sections are reserved for the separately bounded Group 7B",
            "retain only independently written concept instruction; do not import classroom scripts, worksheets, or branded activities",
        ],
    ),
    direct(
        "nist_si_units_mass",
        "NIST SI Units — Mass",
        "https://www.nist.gov/pml/owm/si-units-mass",
        families=["MATH-1", "SCI-0", "SCI-1", "ELA-1"],
        bands=["F1", "F2", "F3"],
        license_id="U.S. government work generally public domain; page-specific notices control",
        role="authoritative mass, weight, kilogram, and gram terminology reference",
        risks=[
            "technical detail must be reduced without erasing the distinction between mass and gravitational weight",
            "page links and non-government media retain their own terms",
        ],
        provider="National Institute of Standards and Technology",
        source_kind="official measurement reference",
        license_scope="page text snapshot; preserve attribution and page-specific notices",
    ),
    direct(
        "nist_si_units_volume",
        "NIST SI Units — Volume",
        "https://www.nist.gov/pml/owm/si-units-volume",
        families=["MATH-1", "SCI-0", "SCI-1", "ELA-1"],
        bands=["F1", "F2", "F3"],
        license_id="U.S. government work generally public domain; page-specific notices control",
        role="authoritative volume, capacity, liter, and milliliter terminology reference",
        risks=[
            "F1 use is restricted to foundational attribute and unit relationships rather than conversion procedures",
            "page images and linked resources may retain separate terms",
        ],
        provider="National Institute of Standards and Technology",
        source_kind="official measurement reference",
        license_scope="page text snapshot; preserve attribution and page-specific notices",
    ),
    direct(
        "core_knowledge_g1_science_literacy",
        "CKSci Grade 1 Unit 7: Science for Everyone",
        "https://www.coreknowledge.org/wp-content/uploads/2024/08/CKSci_G1U7_ScienceForEveryone_Unit_Materials_W1.zip",
        families=["SCI-0", "SCI-1", "ENG-1", "RES-1", "ELA-2"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded observation, questions, measurement, prediction, data, models, investigation, and design pilot",
        risks=["teacher-led digital engagements are not required", "review third-party images and links"],
    ),
    direct(
        "core_knowledge_k_needs_plants_animals",
        "CKSci Kindergarten Unit 2: Needs of Plants and Animals",
        "https://www.coreknowledge.org/wp-content/uploads/2020/07/CKSci_GKU2_NeedsOfPlantsAnimals.zip",
        families=["SCI-0", "SCI-1", "SCI-2", "ENG-1", "RES-1", "ELA-2"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational living things, organism needs, habitats, natural resources, and evidence-based habitat design",
        risks=[
            "review third-party images, links, and optional online resources separately",
            "living and nonliving classification includes uncertain, dormant, dead, and formerly living cases that require careful wording",
            "habitat examples are foundations rather than complete ecology or environmental-policy instruction",
        ],
    ),
    direct(
        "core_knowledge_g1_plant_animal_survival",
        "CKSci Grade 1 Unit 2: Plant and Animal Survival",
        "https://www.coreknowledge.org/wp-content/uploads/2020/06/CKSci_G1U2_Plant-and-Animal-Survival.zip",
        families=["SCI-0", "SCI-1", "SCI-2", "ENG-1", "RES-1", "ELA-2"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational organism parts and functions, environmental responses, parent-young similarities, care, and survival",
        risks=[
            "review third-party images, links, and optional online resources separately",
            "traits, inherited variation, reproduction, and life cycles remain introductory and require later expansion",
            "wildlife care examples do not authorize handling, feeding, moving, or treating wild or injured animals",
        ],
    ),
    direct(
        "core_knowledge_k_weather_patterns",
        "CKSci Kindergarten Unit 4: Weather Patterns — Teacher Guide",
        "https://www.coreknowledge.org/wp-content/uploads/2020/07/CKSci_GKU4_Weather-Patterns_TG.pdf",
        families=["SCI-0", "SCI-1", "SCI-2", "MATH-1", "ENG-1", "RES-1", "ELA-2"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational sunlight heating, weather observation and records, recurring patterns, prediction, shade design, and warning awareness",
        risks=[
            "review third-party images, links, and optional online resources separately",
            "weather-pattern foundations do not establish climate trends or severe-weather operational authority",
            "temperature, sunlight, storm, and outdoor observations require explicit sensory and physical-safety limits",
        ],
    ),
    direct(
        "core_knowledge_g1_sun_moon_stars",
        "CKSci Grade 1 Unit 1: Sun, Moon, and Stars",
        "https://www.coreknowledge.org/wp-content/uploads/2020/07/CKSci_G1U1_Sun-Moon-and-Stars.zip",
        families=["SCI-0", "SCI-1", "SCI-2", "MATH-1", "RES-1", "ELA-2"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational day and night, apparent Sun movement, daylight change, Moon appearance, star patterns, repeated observations, and prediction",
        risks=[
            "review third-party images, links, and optional online resources separately",
            "direct or magnified solar observation is excluded; use time records, shadows, diagrams, or approved indirect observation",
            "orbital calculation, astrophysics, cosmology, navigation, and precise astronomical prediction remain later instruction",
        ],
    ),
    direct(
        "core_knowledge_k_pushes_pulls",
        "CKSci Kindergarten Unit 1: Pushes and Pulls",
        "https://www.coreknowledge.org/wp-content/uploads/2020/06/CKSci_GKU1_Pushes-and-Pulls.zip",
        families=["SCI-0", "SCI-1", "SCI-2", "ENG-1", "RES-1", "ELA-2"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational pushes, pulls, force direction and strength, changes in motion, surface effects, and engineering-design pilot",
        risks=[
            "review third-party images, links, and optional online resources separately",
            "kindergarten force descriptions are conceptual foundations rather than a complete mechanics treatment",
            "gravity, magnetism, friction, and noncontact forces require bounded wording and later expansion",
        ],
    ),
    direct(
        "core_knowledge_g1_light_sound",
        "CKSci Grade 1 Unit 3: Exploring Light and Sound",
        "https://www.coreknowledge.org/wp-content/uploads/2020/06/CKSci_G1U3_Exploring-Light-and-Sound.zip",
        families=["SCI-0", "SCI-1", "SCI-2", "ENG-1", "RES-1", "ELA-2"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational light sources, illumination, shadows, material interactions, vibration, sound, communication, and engineering-design pilot",
        risks=[
            "review third-party images, links, and optional online resources separately",
            "bright-light and loud-sound activities require explicit sensory-safety limits",
            "wave, frequency, wavelength, energy, and electromagnetic explanations remain later teaching",
        ],
    ),
    direct(
        "core_knowledge_g1_simple_machines",
        "CKSci Grade 1 Unit 4: Simple Machines",
        "https://www.coreknowledge.org/wp-content/uploads/2020/08/CKSci_G1U4_Simple-Machines_W2.zip",
        families=["SCI-0", "SCI-1", "SCI-2", "ENG-1", "RES-1", "ELA-2"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded foundational ramps, wheels and axles, levers, pulleys, wedges, screws, gears, compound machines, and engineering-design pilot",
        risks=[
            "review third-party images, links, and optional online resources separately",
            "everyday statements that a machine makes work easier require force-distance and task-context boundaries",
            "powered machinery, mechanical ratings, and safety-critical design remain outside this elementary source",
        ],
    ),
    direct(
        "core_knowledge_g1_civics",
        "CKHG Grade 1 Unit 10: Lessons in Civics",
        "https://www.coreknowledge.org/wp-content/uploads/2023/12/CKHG_G1U10_LessonsInCivics_Web_W1.zip",
        families=["HIST-1", "CIV-1", "ELA-2", "CULT-1"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded community, rules, laws, citizenship, fairness, and historical-example pilot",
        risks=["U.S.-specific civics must be labeled by jurisdiction", "identity and culture content require plural perspectives"],
    ),
    direct(
        "core_knowledge_g1_human_body",
        "CKLA Grade 1 Domain 2: The Human Body",
        "https://www.coreknowledge.org/wp-content/uploads/2016/12/CKLA-G1-The-Human-Body.zip",
        families=["HEALTH-1", "SCI-1", "ELA-2"],
        bands=["F1"],
        license_id="artifact-embedded Core Knowledge / Creative Commons terms",
        role="bounded body systems, major organs, care, germs, disease, vaccines, and health vocabulary pilot",
        risks=["older edition and health claims require current-source verification", "knowledge resource only; never medical advice", "review embedded images and notices"],
    ),
    direct(
        "core_knowledge_g1_helpful_computers",
        "CKSci Grade 1 Unit 6: Helpful Computers",
        "https://www.coreknowledge.org/wp-content/uploads/2023/09/CKSci_G1U6_HelpfulComputers_Unit_Materials_W2.zip",
        families=["TECH-1", "ENG-1", "RES-1", "ELA-2", "CIV-1"],
        bands=["F1"],
        license_id="artifact-embedded CC-BY-NC-SA-4.0",
        role="bounded computer systems, input-process-output, data, accounts, privacy, algorithms, debugging, attribution, and design foundation",
        risks=[
            "preserve noncommercial and share-alike attribution terms",
            "exclude third-party images, links, trademarks, and scripted activities from retained teaching",
            "procedural knowledge grants no device, network, filesystem, code-execution, surveillance, credential, or autonomy authority",
            "account, password, and internet examples require current privacy and security boundaries rather than operational credential handling",
        ],
    ),
    direct(
        "medlineplus_evaluating_health_information_current",
        "MedlinePlus: Evaluating Health Information",
        "https://medlineplus.gov/evaluatinghealthinformation.html",
        families=["HEALTH-1", "RES-1", "ELA-2", "LOGIC-1"],
        bands=["F1", "F2"],
        license_id="U.S.-federal-public-domain-health-topic-summary-with-item-specific-exceptions",
        role="current bounded health-source evaluation, update, purpose, evidence, and qualified-provider limits",
        risks=[
            "use only the NLM-authored health-topic summary identified as public domain",
            "exclude A.D.A.M. encyclopedia content, images, journal abstracts, linked resources, and other copyrighted material",
            "health information supports questions and discussion but does not diagnose or replace a qualified provider",
        ],
        provider="National Library of Medicine / MedlinePlus",
        source_kind="current federal health-information page snapshot",
        license_scope="NLM-authored public-domain health-topic summary only; item-specific and linked copyright exclusions remain attached",
        max_bytes=10_000_000,
    ),
    direct(
        "medlineplus_patient_rights_current",
        "MedlinePlus: Patient Rights",
        "https://medlineplus.gov/patientrights.html",
        families=["HEALTH-1", "CIV-1", "RES-1", "ELA-2"],
        bands=["F1", "F2"],
        license_id="U.S.-federal-public-domain-health-topic-summary-with-item-specific-exceptions",
        role="bounded informed-consent, respect, questions, participation, and patient-rights foundation",
        risks=[
            "use only the NLM-authored health-topic summary identified as public domain",
            "United States context must remain explicit and state, facility, capacity, age, and emergency rules vary",
            "exclude A.D.A.M. encyclopedia content, images, linked handouts, and other copyrighted material",
            "general rights literacy only; not legal advice or individualized consent determination",
        ],
        provider="National Library of Medicine / MedlinePlus",
        source_kind="current federal health-information page snapshot",
        license_scope="NLM-authored public-domain health-topic summary only; item-specific and linked copyright exclusions remain attached",
        max_bytes=10_000_000,
    ),
    direct(
        "code_org_csf_curriculum_guide",
        "Code.org Computer Science Fundamentals Curriculum",
        "https://code.org/en-US/curriculum/computer-science-fundamentals",
        families=["TECH-1", "ENG-1", "ELA-1"],
        bands=["F1", "F2"],
        license_id="CC-BY-NC-SA-4.0",
        role="bounded elementary sequencing, algorithms, repetition, testing, and debugging foundation",
        risks=["noncommercial/share-alike source", "source wording and branded activities are not conversational style", "curriculum concepts do not grant software execution authority"],
        provider="Code.org",
        source_kind="bounded web curriculum artifact",
        license_scope="Code.org-authored curriculum text under CC-BY-NC-SA-4.0; preserve attribution and exclude third-party media",
    ),
    direct(
        "stlouisfed_goods_services_elementary",
        "Federal Reserve Bank of St. Louis: Goods and Services",
        "https://www.stlouisfed.org/education/exploring-economics-video-series/goods-and-services",
        families=["CIV-1", "LIFE-1", "ELA-1", "ELA-2"],
        bands=["F1"],
        license_id="InC-EDU-noncommercial-personal-or-educational-use-with-attribution",
        role="bounded elementary distinction among wants, goods, and services with ordinary examples",
        risks=[
            "preserve the Federal Reserve Bank of St. Louis copyright notice and attribution link",
            "do not reproduce the resource, transcript, song, media, or branded activity",
            "the source defines economic categories; it does not decide a person's moral worth or universal needs",
            "commercial reuse requires separate rights review or permission",
        ],
        provider="Federal Reserve Bank of St. Louis Economic Education",
        source_kind="bounded elementary economics page snapshot",
        license_scope=(
            "individual resource available for noncommercial personal or educational use under the provider's "
            "Permitted Use policy; retain notices and attribution; selected concepts are paraphrased, not copied"
        ),
        max_bytes=10_000_000,
    ),
    direct(
        "stlouisfed_making_choices_needs_wants",
        "Federal Reserve Bank of St. Louis: Making Choices Badge Activities",
        "https://www.stlouisfed.org/-/media/project/frbstl/stlouisfed/education/scouts/pdf/making-choices-badge-activities.pdf",
        families=["CIV-1", "LIFE-1", "ELA-1", "ELA-2"],
        bands=["F1"],
        license_id="InC-EDU-educational-reprint-with-attribution",
        role="bounded elementary needs, wants, goods, choice, and context distinction",
        risks=[
            "retain the embedded Federal Reserve Bank of St. Louis copyright notice and attribution",
            "do not reproduce the lesson, story, worksheets, images, or branded activity as Selene teaching text",
            "need and want classifications depend on the person and situation and must not become moral judgments",
            "commercial reuse requires separate rights review or permission",
        ],
        provider="Federal Reserve Bank of St. Louis Economic Education",
        source_kind="bounded elementary economics PDF",
        license_scope=(
            "educational reprint or photocopy permission with provider credit; selected concepts are "
            "paraphrased and source notices remain attached"
        ),
        max_bytes=25_000_000,
    ),
    catalog_only(
        "catalog_core_knowledge_k8",
        "Core Knowledge free K-8 curriculum",
        "https://www.coreknowledge.org/download-free-curriculum/",
        families=["ELA-1", "ELA-2", "MATH-1", "SCI-0", "SCI-1", "HIST-1", "CIV-1", "TECH-1", "ENG-1", "ART-1", "HEALTH-1"],
        bands=["F1", "F2", "F3"],
        license_id="primarily CC-BY-NC-SA; edition-specific",
        role="elementary and middle-school sequence backbone",
        reason="large multi-edition catalog with third-party media exclusions; choose text artifacts and licenses per volume",
        risks=["noncommercial/share-alike", "third-party images and media may not be covered", "math program is still developing"],
    ),
    catalog_only(
        "catalog_illustrative_math_first_edition",
        "Illustrative Mathematics first-edition K-12 curriculum",
        "https://im.kendallhunt.com/",
        families=["MATH-1", "MATH-2", "MATH-3", "LOGIC-1"],
        bands=["F1", "F2", "F3", "F4"],
        license_id="CC-BY-4.0 for named first editions; newer editions differ",
        role="coherent K-12 mathematical progression and application",
        reason="site-hosted curriculum must be pinned to the explicitly CC-BY first edition rather than newer v.360 material",
        risks=["edition drift", "logos, trademarks, and third-party material excluded"],
    ),
    catalog_only(
        "catalog_open_up_resources",
        "Open Up Resources EL Education and first-edition mathematics",
        "https://www.openupresources.org/help-support/licensing-questions/",
        families=["ELA-1", "ELA-2", "ELA-3", "MATH-1", "MATH-2", "MATH-3"],
        bands=["F1", "F2", "F3"],
        license_id="artifact-specific CC-BY / CC-BY-NC with exclusions",
        role="elementary literacy and middle-school mathematics sequence support",
        reason="licenses differ by program and edition; assessments and some components are excluded",
        risks=["edition-specific licensing", "restricted assessments", "third-party excerpts"],
    ),
    catalog_only(
        "catalog_openscied",
        "OpenSciEd instructional materials",
        "https://openscied.org/instructional-materials/",
        families=["SCI-0", "SCI-1", "SCI-2", "SCI-3", "ENG-1", "RES-1"],
        bands=["F1", "F2", "F3", "F4"],
        license_id="unit- and grade-band-specific CC-BY / CC-BY-NC",
        role="phenomenon-based science progression, models, evidence, and engineering practices",
        reason="grade bands and releases use different licenses; select and record units individually",
        risks=["license variance", "teacher/student bundles may contain third-party assets"],
    ),
    catalog_only(
        "catalog_openstax",
        "OpenStax textbook library",
        "https://openstax.org/subjects",
        families=["ELA-3", "MATH-3", "SCI-2", "SCI-3", "HIST-2", "CIV-1", "LOGIC-1", "HEALTH-1", "LIFE-1", "CULT-1"],
        bands=["F4", "F5", "F6"],
        license_id="book- and revision-specific; library transitioning to CC-BY-NC-SA",
        role="reviewed high-school/college textbooks after foundational prerequisites",
        reason="license changed across the library in 2026 and must be pinned per book and revision",
        risks=["license drift", "large collection", "some books are too advanced without prior bands"],
    ),
    catalog_only(
        "catalog_openintro_statistics",
        "OpenIntro Statistics",
        "https://www.openintro.org/book/os/",
        families=["MATH-3", "SCI-0", "RES-1", "LOGIC-1"],
        bands=["F4", "F5"],
        license_id="CC-BY-SA-3.0 for the textbook; file-specific exceptions",
        role="statistics, uncertainty, experimental design, inference, and evidence interpretation",
        reason="download flow and companion materials have file-specific terms; select the textbook artifact only",
        risks=["teacher resources and some slides are not openly licensed", "branding excluded"],
    ),
    catalog_only(
        "catalog_tatoeba",
        "Tatoeba sentence and translation corpus",
        "https://tatoeba.org/en/downloads",
        families=["ELA-1", "ELA-2", "CULT-1"],
        bands=["F1", "F2", "F3", "F4"],
        license_id="CC-BY-2.0-FR / CC0 per contribution",
        role="multilingual sentence relationships, translation limits, and near-concept distinctions",
        reason="attribution is contribution-specific and quality varies; build a bounded attributed selection instead of mirroring the full dump",
        risks=["community-contributed errors", "author-level attribution", "audio has separate licenses"],
    ),
    catalog_only(
        "catalog_cdc_health",
        "CDC health and health-literacy materials",
        "https://www.cdc.gov/health-literacy/",
        families=["HEALTH-1", "SCI-0", "SCI-2", "RES-1"],
        bands=["F2", "F3", "F4", "F5"],
        license_id="mostly U.S. public domain; item-specific exceptions",
        role="public health, health evidence, risk communication, and care-system limits",
        reason="federal pages can mix public-domain, contractor, grantee, state, and third-party material",
        risks=["not medical practice authority", "attribute CDC and disclaim endorsement", "exclude logos and restricted images"],
    ),
    catalog_only(
        "catalog_cfpb_financial_capability",
        "CFPB youth financial capability resources",
        "https://www.consumerfinance.gov/consumer-tools/educator-tools/youth-financial-education/",
        families=["LIFE-1", "MATH-2", "CIV-1", "RES-1"],
        bands=["F2", "F3", "F4"],
        license_id="U.S. federal material with item-specific exceptions",
        role="consumer decisions, finance, records, institutions, and evidence-based curriculum review",
        reason="select current federal artifacts and preserve item-level notices before mirroring",
        risks=["not personal financial advice", "rules and programs can change", "third-party material may be present"],
    ),
    catalog_only(
        "catalog_national_archives_docsteach",
        "U.S. National Archives and DocsTeach",
        "https://www.archives.gov/education",
        families=["HIST-1", "HIST-2", "CIV-1", "ELA-3", "RES-1"],
        bands=["F2", "F3", "F4", "F5"],
        license_id="document- and activity-specific public domain / CC0 / CC-BY-NC-SA",
        role="primary-source literacy, historical context, civics, and source comparison",
        reason="rights status is attached to individual records and activities and must travel with each selection",
        risks=["archive custody does not guarantee public domain", "historical sources require contextualization"],
    ),
    catalog_only(
        "catalog_teachengineering_reference_only",
        "TeachEngineering curriculum catalog",
        "https://www.teachengineering.org/",
        families=["ENG-1", "SCI-0", "SCI-1", "TECH-1"],
        bands=["F1", "F2", "F3", "F4"],
        license_id="restricted educational use; all rights reserved",
        role="reference for engineering curriculum coverage only",
        reason="current terms prohibit scraping and restrict external redistribution; do not mirror",
        risks=["no scraping", "noncommercial internal academic use restrictions", "authorization required for broader use"],
    ),
]


def _request_json(url: str) -> Any:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=90) as response:
        return json.load(response)


def _download(url: str, destination: Path, max_bytes: int) -> tuple[str, int]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf,text/html,application/zip,application/octet-stream,*/*;q=0.8",
            "Connection": "close",
        },
    )
    digest = hashlib.sha256()
    written = 0
    with urlopen(request, timeout=180) as response:
        length = response.headers.get("Content-Length")
        if length and int(length) > max_bytes:
            raise ValueError(f"remote artifact exceeds {max_bytes} bytes: {length}")
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as temp:
            temp_path = Path(temp.name)
            try:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_bytes:
                        raise ValueError(f"download exceeded {max_bytes} bytes")
                    digest.update(chunk)
                    temp.write(chunk)
            except Exception:
                temp_path.unlink(missing_ok=True)
                raise
    os.replace(temp_path, destination)
    return digest.hexdigest(), written


def _safe_relative(name: str) -> Path:
    posix = PurePosixPath(name)
    if posix.is_absolute() or ".." in posix.parts:
        raise ValueError(f"unsafe remote path: {name!r}")
    return Path(*posix.parts)


def _acquire_hf(source: dict[str, Any], destination: Path) -> dict[str, Any]:
    acquisition = source["acquisition"]
    repo = acquisition["repo"]
    info = _request_json(f"https://huggingface.co/api/datasets/{repo}?blobs=true")
    if info.get("private") or info.get("gated"):
        raise ValueError(f"dataset is private or gated: {repo}")
    revision = info["sha"]
    siblings = info.get("siblings", [])
    declared_size = sum(int(item.get("size") or 0) for item in siblings)
    if declared_size > acquisition["max_bytes"]:
        raise ValueError(f"dataset declares {declared_size} bytes, above limit")

    files: list[dict[str, Any]] = []
    for item in siblings:
        remote_name = item["rfilename"]
        relative = _safe_relative(remote_name)
        target = destination / relative
        encoded_path = "/".join(quote(part, safe="") for part in PurePosixPath(remote_name).parts)
        url = f"https://huggingface.co/datasets/{repo}/resolve/{revision}/{encoded_path}?download=true"
        sha256, size = _download(url, target, acquisition["max_bytes"])
        files.append({"path": relative.as_posix(), "sha256": sha256, "bytes": size, "source_url": url})

    metadata_path = destination / "_provider_metadata.json"
    metadata_path.write_text(json.dumps(info, indent=2, sort_keys=True), encoding="utf-8")
    metadata_sha = hashlib.sha256(metadata_path.read_bytes()).hexdigest()
    files.append({"path": metadata_path.name, "sha256": metadata_sha, "bytes": metadata_path.stat().st_size, "generated": True})
    return {"resolved_revision": revision, "declared_bytes": declared_size, "files": files}


def _acquire_github(source: dict[str, Any], destination: Path) -> dict[str, Any]:
    acquisition = source["acquisition"]
    repo = acquisition["repo"]
    repo_info = _request_json(f"https://api.github.com/repos/{repo}")
    default_branch = repo_info["default_branch"]
    commit = _request_json(f"https://api.github.com/repos/{repo}/commits/{quote(default_branch, safe='')}")
    revision = commit["sha"]
    archive_name = f"{source['id']}-{revision}.zip"
    archive_path = destination / archive_name
    url = f"https://github.com/{repo}/archive/{revision}.zip"
    sha256, size = _download(url, archive_path, acquisition["max_bytes"])
    files = [{"path": archive_name, "sha256": sha256, "bytes": size, "source_url": url}]
    for artifact in acquisition.get("extra_artifacts", []):
        relative = _safe_relative(artifact["path"])
        artifact_url = artifact["url_template"].format(revision=revision)
        artifact_sha, artifact_size = _download(
            artifact_url,
            destination / relative,
            acquisition["max_bytes"],
        )
        files.append(
            {
                "path": relative.as_posix(),
                "sha256": artifact_sha,
                "bytes": artifact_size,
                "source_url": artifact_url,
            }
        )
    return {
        "resolved_revision": revision,
        "default_branch": default_branch,
        "files": files,
    }


def _acquire_direct(source: dict[str, Any], destination: Path) -> dict[str, Any]:
    acquisition = source["acquisition"]
    relative = _safe_relative(acquisition["filename"])
    sha256, size = _download(
        acquisition["url"],
        destination / relative,
        acquisition["max_bytes"],
    )
    return {
        "resolved_revision": "content-addressed-by-sha256",
        "files": [
            {
                "path": relative.as_posix(),
                "sha256": sha256,
                "bytes": size,
                "source_url": acquisition["url"],
            }
        ],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _write_readme(output: Path, lock_entries: list[dict[str, Any]]) -> None:
    mirrored = sum(1 for entry in lock_entries if entry.get("acquired"))
    cataloged = len(SOURCES)
    text = f"""# Selene Curriculum Source Shelf

This directory contains source artifacts for Aleks's review.  It is not a
teaching shelf and is not available to Selene Chat or runtime retrieval.

- Cataloged sources: {cataloged}
- Mirrored source snapshots: {mirrored}
- Teaching packets created: 0
- Understanding candidates created: 0
- Approved knowledge resources created: 0

`catalog.json` records why a source may be useful and its license risks.
`manifest.lock.json` pins every downloaded revision and SHA-256 checksum.
`checksums.sha256` can be used to verify local artifacts without opening or
executing them.

The presence of a source here never means it is accepted for teaching.  A later
review must select bounded material, preserve provenance, classify uncertainty,
and obtain an Aleks item decision or bounded curriculum authorization through
the normal Cocoon lifecycle.
"""
    (output / "README.md").write_text(text, encoding="utf-8")


def build_catalog(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    catalog = {
        "schema": "selene.curriculum-source-catalog.v1",
        "guards": SHELF_GUARDS,
        "sources": SOURCES,
    }
    _write_json(output / "catalog.json", catalog)
    _write_readme(output, [])


def acquire(output: Path, *, replace: bool, only: set[str] | None = None) -> int:
    build_catalog(output)
    sources_dir = output / "sources"
    lock_entries: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    prior_entries: dict[str, dict[str, Any]] = {}
    prior_lock_path = output / "manifest.lock.json"
    if prior_lock_path.exists():
        prior_lock = json.loads(prior_lock_path.read_text(encoding="utf-8"))
        prior_entries = {entry["id"]: entry for entry in prior_lock.get("entries", [])}

    for source in SOURCES:
        mode = source["acquisition"]["mode"]
        entry: dict[str, Any] = {
            "id": source["id"],
            "mode": mode,
            "license": source["license"],
            "canonical_url": source["canonical_url"],
            "acquired": False,
        }
        if mode == "catalog_only":
            entry["hold_reason"] = source["acquisition"]["reason"]
            lock_entries.append(entry)
            continue

        if only is not None and source["id"] not in only:
            previous = prior_entries.get(source["id"])
            if previous is not None:
                lock_entries.append(previous)
            else:
                entry["hold_reason"] = "not selected in this acquisition run"
                lock_entries.append(entry)
            continue

        destination = sources_dir / source["id"]
        try:
            if destination.exists() and replace:
                shutil.rmtree(destination)
            if destination.exists() and any(destination.iterdir()):
                previous = prior_entries.get(source["id"])
                if previous is not None and previous.get("acquired"):
                    lock_entries.append(previous)
                else:
                    entry["hold_reason"] = "existing snapshot preserved; use --replace to reacquire"
                    lock_entries.append(entry)
                continue
            destination.mkdir(parents=True, exist_ok=True)
            if mode == "huggingface_snapshot":
                result = _acquire_hf(source, destination)
            elif mode == "github_archive":
                result = _acquire_github(source, destination)
            elif mode == "direct_artifact":
                result = _acquire_direct(source, destination)
            else:
                raise ValueError(f"unsupported acquisition mode: {mode}")
            entry.update(result)
            entry["acquired"] = True
        except (HTTPError, URLError, OSError, ValueError, KeyError) as exc:
            failures.append({"id": source["id"], "error": str(exc)})
            entry["error"] = str(exc)
        lock_entries.append(entry)

    lock = {
        "schema": "selene.curriculum-source-lock.v1",
        "guards": SHELF_GUARDS,
        "entries": lock_entries,
        "failures": failures,
    }
    _write_json(output / "manifest.lock.json", lock)
    _write_readme(output, lock_entries)

    checksum_lines: list[str] = []
    for entry in lock_entries:
        for item in entry.get("files", []):
            path = Path("sources") / entry["id"] / item["path"]
            checksum_lines.append(f"{item['sha256']}  {path.as_posix()}")
    (output / "checksums.sha256").write_text("\n".join(sorted(checksum_lines)) + "\n", encoding="utf-8")
    return 1 if failures else 0


def verify(output: Path) -> int:
    lock_path = output / "manifest.lock.json"
    if not lock_path.exists():
        print(f"missing lock manifest: {lock_path}", file=sys.stderr)
        return 1
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    checked = 0
    for entry in lock.get("entries", []):
        for item in entry.get("files", []):
            path = output / "sources" / entry["id"] / item["path"]
            if not path.is_file():
                failures.append(f"missing: {path}")
                continue
            digest = _sha256_file(path)
            checked += 1
            if digest != item["sha256"]:
                failures.append(f"checksum mismatch: {path}")
    print(f"verified {checked} files; failures={len(failures)}")
    for failure in failures:
        print(failure, file=sys.stderr)
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--acquire", action="store_true", help="mirror approved review-only sources")
    parser.add_argument("--replace", action="store_true", help="replace existing per-source snapshots")
    parser.add_argument("--only", action="append", help="acquire only this source id; may be repeated")
    parser.add_argument("--verify", action="store_true", help="verify an existing lock manifest")
    args = parser.parse_args()

    output = args.output.resolve()
    if args.verify:
        return verify(output)
    if args.acquire:
        return acquire(output, replace=args.replace, only=set(args.only) if args.only else None)
    build_catalog(output)
    print(f"wrote review-only catalog: {output}")
    print("no sources downloaded; pass --acquire to mirror approved entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
