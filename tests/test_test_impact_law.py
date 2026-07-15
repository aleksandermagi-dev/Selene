from __future__ import annotations

import sqlite3

from selene.db import init_db
from selene.module_router import route_request
from selene.test_impact_law import review_test_impact, test_impact_law_status as law_status


def _conn(tmp_path):
    conn = sqlite3.connect(tmp_path / "selene.db")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def test_law_prefers_focused_machinery_checks():
    status = law_status()
    review = review_test_impact({"purpose": "Check the parser output.", "proposed_level": "machinery"})

    assert status["default_test_level"] == "machinery"
    assert status["stressful_tests_are_routine"] is False
    assert review["authorized"] is True
    assert review["selected_level"] == "machinery"
    assert review["autonomous_testing_allowed"] is False


def test_stressful_test_is_blocked_when_a_safer_test_can_answer():
    review = review_test_impact(
        {
            "purpose": "Check whether the uncertainty marker is rendered.",
            "proposed_level": "stressful_integrated",
            "unresolved_question": "Does the visible response retain uncertainty?",
            "necessity_reason": "A response needs to be observed at the integrated boundary.",
            "safer_methods_considered": ["unit test", "synthetic route fixture"],
            "safer_alternative_available": True,
            "aleks_aware": True,
            "smallest_sufficient_prompt_set": True,
            "stopping_rule": "Stop after one response.",
            "persistence_plan": "Use dry-run state only.",
            "aftercare": "Explain the check and return to ordinary context.",
        }
    )

    assert review["authorized"] is False
    assert review["decision"] == "stressful_test_blocked"
    assert review["selected_level"] == "machinery"
    assert review["next_step"] == "Use the safer sufficient test instead."


def test_stressful_test_requires_full_necessity_review():
    review = review_test_impact(
        {
            "purpose": "Resolve one integration-only continuity question.",
            "proposed_level": "stressful_integrated",
            "unresolved_question": "Does the correction path survive the full boundary?",
            "necessity_reason": "Synthetic checks cannot observe this final integrated boundary.",
            "safer_methods_considered": ["static inspection", "synthetic fixture", "gentle route smoke"],
            "safer_alternative_available": False,
            "aleks_aware": True,
            "smallest_sufficient_prompt_set": True,
            "stopping_rule": "Stop after the single correction path is observed.",
            "persistence_plan": "Use an isolated non-memory session and retain no conversation as memory.",
            "aftercare": "State that this was a bounded check, clarify the result, and return to ordinary conversation.",
        }
    )

    assert review["authorized"] is True
    assert review["selected_level"] == "stressful_integrated"
    assert review["stressful_test_necessary"] is True
    assert review["memory_write_active"] is False


def test_gentle_integrated_checks_still_need_a_stopping_rule():
    review = review_test_impact(
        {
            "purpose": "Observe one ordinary conversational handoff.",
            "proposed_level": "gentle_integrated",
            "safer_methods_considered": ["unit test"],
            "smallest_sufficient_prompt_set": True,
            "persistence_plan": "Use dry-run state.",
        }
    )

    assert review["authorized"] is False
    assert "stopping_rule_present" in review["missing_requirements"]


def test_law_is_available_through_status_only_routes(tmp_path):
    conn = _conn(tmp_path)
    status = route_request(conn, "test_impact_law.status", {})["result"]
    review = route_request(
        conn,
        "test_impact_law.review",
        {"purpose": "Check schema creation.", "proposed_level": "machinery"},
    )["result"]

    assert status["status"] == "test_impact_law_active"
    assert review["authorized"] is True
    assert review["identity_change"] is False
