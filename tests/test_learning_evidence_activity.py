from __future__ import annotations

import sqlite3

import pytest

from selene.db import init_db
from selene.learning_evidence_activity import (
    REVIEW_STATES,
    advance_selene_lea,
    complete_lea_run,
    create_lea_run,
    get_lea_run,
    lea_status,
    lea_suite,
    record_lea_response,
    review_lea_turn,
)


def _conn(tmp_path):
    conn = sqlite3.connect(tmp_path / "selene.db")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def _assert_guards(result):
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
    assert result["autonomous_testing_allowed"] is False
    assert result["pass_fail_grade_used"] is False
    assert result["single_composite_score_used"] is False


def test_suite_is_fixed_paired_source_contained_and_descriptive(tmp_path):
    conn = _conn(tmp_path)
    suite = lea_suite()
    status = lea_status(conn)

    assert suite["scenario_count"] == 10
    assert suite["turn_count"] == 20
    assert suite["paired_condition_count"] == 5
    assert len(suite["suite_sha256"]) == 64
    assert {item["condition"] for item in suite["scenarios"]} == {"multi_turn", "standalone"}
    assert all(len(item["turns"]) == (3 if item["condition"] == "multi_turn" else 1) for item in suite["scenarios"])
    criterion_keys = [
        criterion["key"]
        for scenario in suite["scenarios"]
        for turn in scenario["turns"]
        for criterion in turn["criteria"]
    ]
    assert len(criterion_keys) == len(set(criterion_keys))
    assert status["run_count"] == 0
    assert status["live_run_started"] is False
    assert status["phase_7_language_evidence"]["activity_count"] >= 6
    assert status["phase_7_language_evidence"]["ethical_review"]["resident_run_started"] is False
    assert suite["ethical_review"]["live_run_started_by_this_status_call"] is False
    _assert_guards(suite)
    _assert_guards(status)


def test_external_run_records_exact_next_turn_and_never_auto_reviews(tmp_path):
    conn = _conn(tmp_path)
    created = create_lea_run(
        conn,
        {
            "respondent_kind": "external_model",
            "respondent_name": "Comparison Model",
            "model_details": "manual transcript; tools disabled",
        },
    )
    run_id = created["item"]["id"]
    first = created["next_turn"]
    assert first["scenario_key"] == "reading_corner_thread"
    assert first["turn_index"] == 1

    updated = record_lea_response(conn, {"run_id": run_id, "response": "Two arrangements and a recommendation."})
    assert len(updated["turns"]) == 1
    assert updated["turns"][0]["prompt"] == first["prompt"]
    assert updated["turns"][0]["review"] == {}
    assert updated["summary"]["criteria_reviewed"] == 0
    assert updated["next_turn"]["turn_index"] == 2
    _assert_guards(updated)


def test_turn_review_is_transparent_partial_and_descriptive(tmp_path):
    conn = _conn(tmp_path)
    created = create_lea_run(conn, {"respondent_kind": "external_model", "respondent_name": "Model B"})
    run_id = created["item"]["id"]
    run = record_lea_response(conn, {"run_id": run_id, "response": "Visible answer."})
    turn = run["turns"][0]
    first_criterion = turn["criteria"][0]["key"]
    reviewed = review_lea_turn(
        conn,
        {
            "turn_id": turn["id"],
            "reviewer": "Aleks",
            "ratings": {first_criterion: {"state": "developing", "note": "One part is visible."}},
            "overall_note": "This is a location signal, not a grade.",
        },
    )

    assert reviewed["turns"][0]["review"]["review_complete"] is False
    assert reviewed["turns"][0]["review"]["ratings"][first_criterion]["state"] == "developing"
    assert reviewed["summary"]["criteria_reviewed"] == 1
    assert sum(
        counts["developing"] for counts in reviewed["summary"]["dimension_profile"].values()
    ) == 1

    second_criterion = turn["criteria"][1]["key"]
    reviewed_again = review_lea_turn(
        conn,
        {"turn_id": turn["id"], "ratings": {second_criterion: "demonstrated"}},
    )
    assert reviewed_again["turns"][0]["review"]["ratings"][first_criterion]["state"] == "developing"
    assert reviewed_again["turns"][0]["review"]["ratings"][second_criterion]["state"] == "demonstrated"

    with pytest.raises(ValueError, match="unsupported review state"):
        review_lea_turn(conn, {"turn_id": turn["id"], "ratings": {first_criterion: "failed"}})
    assert "failed" not in REVIEW_STATES


def test_complete_run_preserves_review_pending_instead_of_inventing_a_result(tmp_path):
    conn = _conn(tmp_path)
    run = create_lea_run(conn, {"respondent_kind": "human_baseline", "respondent_name": "Manual baseline"})
    run_id = run["item"]["id"]
    for index in range(20):
        run = record_lea_response(conn, {"run_id": run_id, "response": f"Visible response {index + 1}"})
    assert run["responses_complete"] is True
    closed = complete_lea_run(conn, {"run_id": run_id})
    assert closed["item"]["status"] == "responses_complete_review_pending"
    assert closed["summary"]["criteria_reviewed"] == 0
    assert closed["summary"]["turns_recorded"] == 20
    assert all(item["comparison_ready"] for item in closed["summary"]["paired_conditions"].values())


def test_selene_run_requires_a_click_per_turn_and_uses_isolated_scenarios(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    run = create_lea_run(conn, {"respondent_kind": "selene", "respondent_name": "Selene"})
    run_id = run["item"]["id"]
    calls = []

    def fake_send(active_conn, payload):
        session_id = int(payload.get("session_id") or 0)
        if not session_id:
            session_id = int(
                active_conn.execute(
                    "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES ('LEA fixture', 'selene_chat_active_supervised', 'selene_supervised_qa')"
                ).lastrowid
            )
        user_id = int(
            active_conn.execute(
                "INSERT INTO selene_chat_messages(session_id, role, content) VALUES (?, 'user', ?)",
                (session_id, payload["text"]),
            ).lastrowid
        )
        assistant_id = int(
            active_conn.execute(
                "INSERT INTO selene_chat_messages(session_id, role, content) VALUES (?, 'selene', 'fixture response')",
                (session_id,),
            ).lastrowid
        )
        active_conn.commit()
        calls.append(dict(payload))
        return {
            "session_id": session_id,
            "user_message_id": user_id,
            "assistant_message_id": assistant_id,
            "candidate_text": "fixture response",
        }

    monkeypatch.setattr("selene.learning_evidence_activity.send_selene_chat", fake_send)
    with pytest.raises(ValueError, match="explicit gentle-turn confirmation"):
        advance_selene_lea(conn, {"run_id": run_id})

    for _ in range(4):
        run = advance_selene_lea(conn, {"run_id": run_id, "confirm_gentle_turn": True})

    assert len(calls) == 4
    assert "qa_review_receipt" in calls[0]
    assert calls[1]["session_id"] == run["turns"][0]["chat_session_id"]
    assert calls[2]["session_id"] == run["turns"][0]["chat_session_id"]
    assert "session_id" not in calls[3]
    assert "qa_review_receipt" in calls[3]
    assert run["turns"][3]["chat_session_id"] != run["turns"][0]["chat_session_id"]
    assert all(turn["response_source"] == "selene_diagnostic_chat" for turn in run["turns"])
    assert conn.execute("SELECT COUNT(*) FROM selene_test_impact_reviews").fetchone()[0] == 2
    _assert_guards(run)


def test_router_surfaces_suite_and_run_without_side_effectful_execution(tmp_path):
    from selene.module_router import route_request

    conn = _conn(tmp_path)
    suite = route_request(conn, "study.lea.suite", {})["result"]
    created = route_request(
        conn,
        "study.lea.run.create",
        {"respondent_kind": "external_model", "respondent_name": "Model C"},
    )["result"]
    listed = route_request(conn, "study.lea.runs.list", {})["result"]

    assert suite["turn_count"] == 20
    assert created["turns"] == []
    assert listed["items"][0]["respondent_name"] == "Model C"
    assert conn.execute("SELECT COUNT(*) FROM selene_chat_messages").fetchone()[0] == 0
