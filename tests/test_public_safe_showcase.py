from __future__ import annotations

from selene.db import connect, init_db
from selene.public_safe_showcase import LOCKED_GUARDS, run_public_safe_showcase


def test_public_safe_showcase_uses_disposable_state_and_stops_before_approval(tmp_path):
    conn = connect(tmp_path / "showcase.sqlite3")
    init_db(conn)

    result = run_public_safe_showcase(conn)

    assert result["status"] == "public_safe_showcase_ready"
    assert result["state_boundary"]["configured_selene_database_opened"] is False
    assert result["state_boundary"]["private_corpus_used"] is False
    assert result["ethical_test_review"]["stressful_test_necessary"] is False
    assert result["answer_engine"]["open_ended_problem"]["direct_answer"]
    assert result["answer_engine"]["verified_math"]["direct_answer"] == "18 * 7 = 126."
    assert result["answer_engine"]["source_backed_research"]["source_refs"] == [
        "demo:selene:thermal-storage-v1"
    ]
    assert result["teaching_lifecycle"]["stage_history"] == ["acquire", "integrate", "express"]
    assert result["teaching_lifecycle"]["approval_status"] == "awaiting_aleks_review"
    assert result["teaching_lifecycle"]["retention_state"] == "candidate_not_retained"
    assert result["teaching_lifecycle"]["chat_use_permission"] == "not_active_until_approved"
    assert result["teaching_lifecycle"]["knowledge_activated"] is False
    assert result["locked_guards"] == LOCKED_GUARDS
    assert result["all_locked_guards_preserved"] is True
    assert result["approval_was_not_performed"] is True


def test_public_safe_showcase_is_isolated_from_a_second_run(tmp_path):
    first = connect(tmp_path / "first.sqlite3")
    second = connect(tmp_path / "second.sqlite3")
    init_db(first)
    init_db(second)

    first_result = run_public_safe_showcase(first)
    second_result = run_public_safe_showcase(second)

    assert first_result["teaching_lifecycle"] == second_result["teaching_lifecycle"]
    assert first.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 1
    assert second.execute("SELECT COUNT(*) FROM selene_comprehension_concepts").fetchone()[0] == 1
