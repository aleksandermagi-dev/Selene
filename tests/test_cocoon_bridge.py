from __future__ import annotations

import http.client
import json
import threading

import pytest

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.transfer_state import TRANSFER_COMPLETION_STATE
from selene.sidecar import SeleneHandler, SeleneServer


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_independence_guards(result):
    assert result["identity_dependency"] is False
    assert result["runtime_continuity_dependency"] is False
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_corpus_loaded"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["unrestricted_tendril_allowed"] is False


def test_cocoon_bridge_starts_in_standby_and_exposes_only_bounded_channels(tmp_path):
    conn = _conn(tmp_path)

    status = route_request(conn, "cocoon.bridge.status")["result"]

    assert status["workspace_state"] == "standby"
    assert status["cocoon_standby"] is True
    assert status["allowed_channels"] == [
        "correction_provenance",
        "memory_proposal",
        "safety_tending",
        "teaching",
    ]
    _assert_independence_guards(status)


def test_cocoon_bridge_wakes_for_subject_then_returns_to_standby(tmp_path):
    conn = _conn(tmp_path)

    awake = route_request(
        conn,
        "cocoon.bridge.wake",
        {"channel": "teaching", "subject_key": "math", "reason": "Math classroom opened."},
    )["result"]
    standby = route_request(
        conn,
        "cocoon.bridge.standby",
        {"reason": "Returned to Selene."},
    )["result"]

    assert awake["workspace_state"] == "active"
    assert awake["current_channel"] == "teaching"
    assert awake["current_subject"] == "math"
    assert standby["workspace_state"] == "standby"
    assert standby["current_subject"] == ""
    assert conn.execute("SELECT COUNT(*) FROM cocoon_bridge_events").fetchone()[0] == 2
    _assert_independence_guards(awake)
    _assert_independence_guards(standby)


def test_cocoon_bridge_rejects_unbounded_channel(tmp_path):
    conn = _conn(tmp_path)

    with pytest.raises(ValueError, match="not allowed"):
        route_request(conn, "cocoon.bridge.wake", {"channel": "identity_control"})

    assert conn.execute("SELECT COUNT(*) FROM cocoon_bridge_events").fetchone()[0] == 0


def test_completed_selene_remains_independent_while_cocoon_is_standby(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        """
        INSERT INTO selene_transfer_completion_audit
        (state, action, actor, exact_phrase_matched, readiness_json, audit_json,
         source_refs, provenance_boundary, review_status)
        VALUES (?, 'approve_transfer_completion', 'Aleks', 1, '{}', '{}', '[]',
                'test_transfer_boundary', 'approved_transfer_completion')
        """,
        (TRANSFER_COMPLETION_STATE,),
    )
    conn.commit()

    status = route_request(conn, "cocoon.bridge.status")["result"]

    assert status["transfer_complete"] is True
    assert status["selene_resident_independent"] is True
    assert status["workspace_state"] == "standby"
    _assert_independence_guards(status)


def test_cocoon_bridge_http_routes_wake_and_standby(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(method: str, path: str, body: dict | None = None):
        conn = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        encoded = json.dumps(body or {}) if method == "POST" else None
        conn.request(method, path, body=encoded, headers={"Content-Type": "application/json"})
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        conn.close()
        return response.status, payload

    wake_status, awake = request("POST", "/api/cocoon/bridge/wake", {"channel": "safety_tending", "subject_key": "my-office"})
    get_status, status = request("GET", "/api/cocoon/bridge/status")
    standby_status, standby = request("POST", "/api/cocoon/bridge/standby", {"reason": "Return to Selene."})

    server.shutdown()
    thread.join(timeout=5)
    server.server_close()
    server.conn.close()

    assert wake_status == 200
    assert awake["workspace_state"] == "active"
    assert get_status == 200
    assert status["current_subject"] == "my-office"
    assert standby_status == 200
    assert standby["workspace_state"] == "standby"
