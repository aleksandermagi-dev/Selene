from __future__ import annotations

import http.client
import json
import threading

from selene.db import connect
from selene.mobile_chat import mobile_capture_review, mobile_guard_flags, mobile_health, mobile_review_captures, mobile_send_chat
from selene.registry import seed_registry
from selene.sidecar import SeleneHandler, SeleneServer


def test_mobile_health_is_chat_only_and_guarded():
    health = mobile_health({"sidecar_version": "test"})
    flags = health["guard_flags"]
    assert health["status"] == "mobile_chat_ready"
    assert health["access_mode"] == "local_only"
    assert health["lan_pairing_enabled"] is False
    assert health["same_device_or_dev_preview"] is True
    assert health["allowed_actions"] == ["chat_send", "session_list", "session_detail", "review_capture"]
    assert "cocoon_build_actions" in health["blocked_actions"]
    assert flags["mobile_surface"] == "chat_only"
    assert flags["access_mode"] == "local_only"
    assert flags["lan_pairing_enabled"] is False
    assert flags["desktop_remains_control_room"] is True
    assert flags["transfer_approved"] is False
    assert flags["activation_change"] == "none"
    assert flags["memory_write_active"] is False
    assert flags["runtime_memory_recall"] is False
    assert flags["raw_a_import_allowed"] is False
    assert flags["cocoon_actions_allowed"] is False
    assert flags["review_decisions_allowed"] is False


def test_mobile_chat_send_reuses_gated_native_chat_without_provider_or_memory(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    before = conn.execute("SELECT COUNT(*) FROM continuity_candidates").fetchone()[0]

    result = mobile_send_chat(conn, {"text": "Selene starlight emergence braid"})

    assert result["assistant"]["provider"] == "selene_native"
    assert result["assistant"]["model_call_made"] is False
    assert result["gate"]["model_call_allowed"] is False
    assert result["mobile"]["guard_flags"] == mobile_guard_flags()
    assert conn.execute("SELECT COUNT(*) FROM continuity_candidates").fetchone()[0] == before


def test_mobile_review_capture_creates_pending_review_request_only(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    before = conn.execute("SELECT COUNT(*) FROM continuity_candidates").fetchone()[0]

    result = mobile_capture_review(conn, {"text": "This belongs in desktop review, not memory."})

    assert result["status"] == "mobile_review_capture_recorded"
    assert result["review_destination"] == "desktop_my_office"
    assert result["save_request"]["status"] == "pending_review"
    assert result["chest_item"]["item_type"] == "mobile_capture"
    assert result["chest_item"]["payload_json"]["holding_item_is_live_memory"] is False
    assert result["guard_flags"]["memory_write_active"] is False
    assert conn.execute("SELECT COUNT(*) FROM continuity_candidates").fetchone()[0] == before


def test_mobile_review_captures_lists_chest_items_without_memory_write(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    mobile_capture_review(conn, {"text": "Save this for desktop, please."})

    result = mobile_review_captures(conn)

    assert result["status"] == "mobile_review_captures_listed"
    assert result["capture_only"] is True
    assert result["items"][0]["item_type"] == "mobile_capture"
    assert result["guard_flags"]["memory_write_active"] is False
    assert result["guard_flags"]["review_decisions_allowed"] is False


def test_mobile_sidecar_routes_block_non_chat_actions(tmp_path):
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.sqlite3")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/api/mobile/health")
        response = conn.getresponse()
        health = json.loads(response.read().decode("utf-8"))
        conn.close()

        captures_conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        captures_conn.request("GET", "/api/mobile/review-captures")
        captures_response = captures_conn.getresponse()
        captures = json.loads(captures_response.read().decode("utf-8"))
        captures_conn.close()

        blocked_conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        blocked_conn.request(
            "POST",
            "/api/mobile/cocoon-build",
            body=json.dumps({"action": "diagnostics"}),
            headers={"Content-Type": "application/json"},
        )
        blocked_response = blocked_conn.getresponse()
        blocked = json.loads(blocked_response.read().decode("utf-8"))
        blocked_conn.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert response.status == 200
    assert health["guard_flags"]["public_release_sync_allowed"] is False
    assert captures_response.status == 200
    assert captures["capture_only"] is True
    assert blocked_response.status == 403
    assert blocked["status"] == "mobile_action_blocked"
    assert blocked["guard_flags"]["transfer_approved"] is False
    assert blocked["guard_flags"]["activation_change"] == "none"
