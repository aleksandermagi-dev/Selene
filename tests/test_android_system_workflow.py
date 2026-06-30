from __future__ import annotations

from selene.android_system import EXPECTED_ANDROID_SYSTEM_KEYS
from selene.cocoon_readiness import ORGAN_TABLES
from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_workflow_locked(result):
    assert result["transfer_approved"] is False
    assert result["transfer_approval_changed"] is False
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def test_android_workflow_report_requires_run_first(tmp_path):
    conn = _conn(tmp_path)

    status = route_request(conn, "android_system.workflow.status")["result"]
    report = route_request(conn, "android_system.workflow.report")["result"]

    assert status["status"] == "android_system_workflow_status_ready"
    assert status["preflight_passed"] is False
    assert report["status"] == "android_system_workflow_report_missing"
    assert report["preflight_passed"] is False
    _assert_workflow_locked(status)
    _assert_workflow_locked(report)


def test_android_workflow_check_covers_11_systems_and_7_concrete_shelves(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(conn, "android_system.workflow.check", {})["result"]
    report = route_request(conn, "android_system.workflow.report")["result"]

    assert result["status"] == "android_system_workflow_check_passed"
    assert result["preflight_passed"] is True
    assert result["system_count"] == 11
    assert {item["key"] for item in result["systems"]} == EXPECTED_ANDROID_SYSTEM_KEYS
    assert all(item["status"] == "ready" for item in result["systems"])
    assert result["concrete_organ_shelves"]["count"] == len(ORGAN_TABLES) == 7
    assert all(item["record_shelf_ready"] for item in result["concrete_organ_shelves"]["items"])
    assert result["fraction_memory_support_allowed"] is True
    assert report["preflight_passed"] is True
    _assert_workflow_locked(result)
    _assert_workflow_locked(report)


def test_android_workflow_check_is_status_only_and_routes_failures_to_b(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(conn, "android_system.workflow.check", {"run_id": "workflow-test"})["result"]

    assert result["run_id"] == "workflow-test"
    assert result["review_status"] == "status_only"
    assert result["review_destination"] == "Status"
    assert result["failure_route"] == "return_to_b"
    assert all(item["return_to_b_path"] == "Cocoon / B repair route" for item in result["systems"])
    assert all(item["guard_flags_confirmed"] is True for item in result["systems"])
    _assert_workflow_locked(result)
