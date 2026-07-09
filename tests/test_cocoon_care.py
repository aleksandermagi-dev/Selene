from __future__ import annotations

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["my_office_write"] is False
    assert result["authority_granted"] is False


def test_cocoon_care_status_and_check_are_status_only(tmp_path):
    conn = _conn(tmp_path)

    status = route_request(conn, "cocoon_care.status")["result"]
    result = route_request(conn, "cocoon_care.check")["result"]
    checks = route_request(conn, "cocoon_care.checks")["result"]
    status_after = route_request(conn, "cocoon_care.status")["result"]

    assert status["status"] == "cocoon_care_status_ready"
    assert result["status"] == "cocoon_care_check_status_only"
    assert result["care_state"] in {"steady", "needs_tending", "needs_aleks", "maintenance", "hard_boundary_hold"}
    assert result["review_destination"] == "Status"
    assert result["review_status"] == "status_only"
    assert result["care_language_only"] is True
    assert result["soft_uncertainty_auto_routes_to_cocoon"] is False
    assert checks["items"][0]["care_state"] == result["care_state"]
    assert status_after["latest_care_state"] == result["care_state"]
    assert status_after["my_office_actionable_count"] == 0
    assert "failure" not in result["summary"].lower()
    assert "punishment" not in status_after["language_law"].lower()
    _assert_locked(result)
    _assert_locked(status_after)


def test_cocoon_care_marks_selene_organ_design_pass_without_miner_data(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        """
        INSERT INTO selene_organ_idea_intake
        (source_card_id, title, workbench, lane, intake_status, readiness, review_confidence)
        VALUES ('idea-1', 'Reasoning organ idea', 'intelligenceOS', 'reasoning', 'ready_for_design_pass', 'use_now', 'strong')
        """
    )
    conn.commit()

    route_request(conn, "cocoon_care.check")
    items = route_request(conn, "selene_organ_ideas.items")["result"]["items"]

    assert items[0]["intake_status"] == "design_pass_started"
    assert items[0]["review_status"] == "status_only"
