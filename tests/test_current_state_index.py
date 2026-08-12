from pathlib import Path

from selene import curriculum_authorization as curriculum
from selene.dream_state import (
    decide_dream_reflection,
    dream_state_status,
    run_dream_cycle,
    wake_from_dream_cycle,
)
from selene.language_teaching_shelf import (
    LANGUAGE_QOL_LESSONS,
    _lesson_group_metadata,
)


ROOT = Path(__file__).resolve().parents[1]
CURRENT_INDEX = ROOT / "docs" / "evidence" / "SELENE_CURRENT_STATE_INDEX_20260811.md"


def _f1_groups():
    groups = [curriculum.FOUNDATION_GROUP, curriculum.F1_LANGUAGE_MATH_GROUP]
    groups.extend(
        getattr(curriculum, f"F1_GROUP{number}_LESSONS")
        for number in range(3, 18)
    )
    return groups


def test_current_state_index_matches_repository_defined_curriculum_counts():
    groups = _f1_groups()
    concept_keys = {
        str(lesson["concept_key"])
        for group in groups
        for lesson in group
    }
    index = CURRENT_INDEX.read_text(encoding="utf-8")

    assert len(groups) == 17
    assert sum(len(group) for group in groups) == 106
    assert len(concept_keys) == 106
    assert "| F1 curriculum groups | 17 |" in index
    assert "| F1 concepts | 106 unique concepts |" in index


def test_current_state_index_matches_repository_defined_language_counts():
    group_orders = {
        int(_lesson_group_metadata(lesson)["group_order"])
        for lesson in LANGUAGE_QOL_LESSONS
    }
    index = CURRENT_INDEX.read_text(encoding="utf-8")

    assert len(LANGUAGE_QOL_LESSONS) == 52
    assert len(group_orders) == 9
    assert "| Language groups | 9 |" in index
    assert "| Language capabilities | 52 |" in index


def test_current_facing_docs_do_not_describe_dream_as_unfinished():
    quick_readme = (ROOT / "QUICK_README.md").read_text(encoding="utf-8")
    quick_readme_words = " ".join(quick_readme.split())
    index = CURRENT_INDEX.read_text(encoding="utf-8")

    assert "academic coverage, Dream, and" not in quick_readme
    assert "Dream's source-bound lifecycle is implemented" in quick_readme_words
    assert "| Source-bound Dream lifecycle | Implemented and synthetically verified |" in index
    assert all(
        callable(operation)
        for operation in (
            dream_state_status,
            run_dream_cycle,
            decide_dream_reflection,
            wake_from_dream_cycle,
        )
    )
