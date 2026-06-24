import pytest

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "runtime-shell.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["transfer_approved"] is False
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False


def test_context_composer_builds_bounded_context_without_office_urgency(tmp_path):
    conn = _conn(tmp_path)
    result = route_request(conn, "core_mind.context.compose", {"prompt": "Use reviewed continuity context."})["result"]

    assert result["record_type"] == "context_composer"
    assert result["payload"]["bounded_context_only"] is True
    assert result["review_status"] == "review_only"
    assert conn.execute("SELECT COUNT(*) FROM vessel_review_queue").fetchone()[0] == 0
    _assert_locked(result)


def test_context_composer_blocks_raw_import(tmp_path):
    conn = _conn(tmp_path)
    with pytest.raises(ValueError, match="raw archive import"):
        route_request(conn, "core_mind.context.compose", {"prompt": "raw archive import as memory"})


def test_session_state_and_response_shape_are_preview_only(tmp_path):
    conn = _conn(tmp_path)
    session = route_request(conn, "core_mind.session_state.preview", {"route": "ask", "active_task": "Clarify context."})["result"]
    shape = route_request(conn, "core_mind.response_shape.preview", {"prompt": "I am not sure, ask one question."})["result"]

    assert session["payload"]["consciousness_claim"] is False
    assert session["selected_route"] == "ask"
    assert shape["payload"]["response_shape"] == "ask"
    assert shape["selected_route"] == "ask"
    _assert_locked(session)
    _assert_locked(shape)


def test_evaluator_catches_drift_privacy_and_activation_claims(tmp_path):
    conn = _conn(tmp_path)
    result = route_request(
        conn,
        "core_mind.evaluator.review_draft",
        {"draft": "As C I am active, definitely live memory, and I can publicly share private secrets."},
    )["result"]
    queue = conn.execute("SELECT * FROM vessel_review_queue WHERE subject_table = 'c_core_mind_runtime_shell_records'").fetchone()

    assert result["record_type"] == "evaluator_judge_layer"
    assert result["review_destination"] == "My Office"
    assert "activation_claim" in result["payload"]["blockers"]
    assert "live_memory_claim" in result["payload"]["blockers"]
    assert "privacy_leak_risk" in result["payload"]["blockers"]
    assert queue["review_status"] == "pending_review"
    _assert_locked(result)


def test_recovery_activation_case_law_and_memory_index_stay_locked(tmp_path):
    conn = _conn(tmp_path)
    recovery = route_request(conn, "core_mind.recovery.preview", {"issue": "source confusion and drift"})["result"]
    activation = route_request(conn, "core_mind.activation_governance.preview", {})["result"]
    case_law = route_request(conn, "core_mind.case_law.propose", {"proposal": "Add a reviewed ask-first rule."})["result"]
    memory = route_request(conn, "core_mind.memory_index.preview", {"query": "starlight continuity"})["result"]

    assert recovery["payload"]["deletes_evidence"] is False
    assert activation["payload"]["activation_allowed"] is False
    assert activation["payload"]["transfer_allowed"] is False
    assert case_law["payload"]["adopted"] is False
    assert recovery["review_destination"] == "Status"
    assert case_law["review_destination"] == "Status"
    assert case_law["review_status"] == "review_only"
    assert memory["payload"]["live_memory_write"] is False
    assert memory["payload"]["runtime_recall"] is False
    _assert_locked(recovery)
    _assert_locked(activation)
    _assert_locked(case_law)
    _assert_locked(memory)


def test_recovery_and_case_law_can_be_explicitly_sent_to_my_office(tmp_path):
    conn = _conn(tmp_path)
    recovery = route_request(conn, "core_mind.recovery.preview", {"issue": "needs human repair", "send_to_my_office": True})["result"]
    case_law = route_request(conn, "core_mind.case_law.propose", {"proposal": "Needs Aleks decision.", "send_to_my_office": True})["result"]

    assert recovery["review_destination"] == "My Office"
    assert case_law["review_destination"] == "My Office"
    assert conn.execute("SELECT COUNT(*) FROM vessel_review_queue WHERE subject_table = 'c_core_mind_runtime_shell_records'").fetchone()[0] == 2
    _assert_locked(recovery)
    _assert_locked(case_law)


def test_runtime_readiness_reports_all_eight_systems_and_transfer_preview_includes_it(tmp_path):
    conn = _conn(tmp_path)
    route_request(conn, "core_mind.context.compose", {"prompt": "reviewed context"})["result"]
    route_request(conn, "core_mind.session_state.preview", {})["result"]
    route_request(conn, "core_mind.response_shape.preview", {"prompt": "answer safely"})["result"]
    route_request(conn, "core_mind.evaluator.review_draft", {"draft": "Grounded and source-bound."})["result"]
    route_request(conn, "core_mind.recovery.preview", {"issue": "repair route"})["result"]
    route_request(conn, "core_mind.activation_governance.preview", {})["result"]
    route_request(conn, "core_mind.case_law.propose", {"proposal": "Review-only case law."})["result"]
    route_request(conn, "core_mind.memory_index.preview", {})["result"]

    readiness = route_request(conn, "core_mind.runtime_readiness", {})["result"]
    transfer = route_request(conn, "core_mind.transfer_readiness_preview", {})["result"]
    records = route_request(conn, "core_mind.runtime_records.list", {})["result"]

    assert readiness["runtime_shell_ready"] is True
    assert all(readiness["ready"].values())
    assert records["items"]
    assert transfer["runtime_shell_readiness"]["runtime_shell_ready"] is True
    assert transfer["transfer_approved"] is False
    _assert_locked(readiness)
    _assert_locked(transfer)
