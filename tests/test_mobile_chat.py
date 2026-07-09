from __future__ import annotations

import http.client
import json
import threading

from selene.db import connect
from selene.mobile_chat import (
    mobile_capture_review,
    mobile_guard_flags,
    mobile_health,
    mobile_pairing_code_valid,
    mobile_pairing_disable,
    mobile_pairing_enable,
    mobile_pairing_state,
    mobile_review_captures,
    mobile_send_chat,
)
from selene.registry import seed_registry
from selene.sidecar import SeleneHandler, SeleneServer


def test_mobile_health_is_chat_only_and_guarded(tmp_path, monkeypatch):
    monkeypatch.setenv("SELENE_DATA_DIR", str(tmp_path))
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


def test_mobile_pairing_is_disabled_by_default_and_desktop_gated(tmp_path, monkeypatch):
    monkeypatch.setenv("SELENE_DATA_DIR", str(tmp_path))

    state = mobile_pairing_state()
    assert state["status"] == "mobile_pairing_disabled"
    assert state["lan_pairing_enabled"] is False
    assert state["bind"] == "127.0.0.1"
    assert mobile_pairing_code_valid("anything") is False

    enabled = mobile_pairing_enable("127.0.0.1")
    assert enabled["lan_pairing_enabled"] is True
    assert enabled["restart_required"] is True
    assert enabled["pairing_code"]
    assert mobile_pairing_code_valid(enabled["pairing_code"]) is True

    disabled = mobile_pairing_disable()
    assert disabled["lan_pairing_enabled"] is False
    assert mobile_pairing_code_valid(enabled["pairing_code"]) is False


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


def test_mobile_chat_send_uses_supervised_selene_chat_when_active(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    conn.execute(
        """
        INSERT INTO selene_activation_audit
        (state, action, actor, exact_phrase_matched, readiness_json, audit_json, source_refs, provenance_boundary)
        VALUES ('selene_chat_active_supervised', 'test_activate', 'Aleks', 1, '{}', '{}', '[]', 'test_mobile_activation')
        """
    )
    conn.execute(
        """
        INSERT INTO transfer_c_readable_packages
        (package_hash, manifest_item_ids, included_counts, excluded_counts, package_json, source_refs, provenance_boundary)
        VALUES ('mobile-test-package', '[]', '{}', '{}', '{}', '[]', 'test_mobile_package')
        """
    )
    conn.commit()

    result = mobile_send_chat(conn, {"text": "Good morning Selene, this is a phone check."})

    assert result["status"] == "selene_chat_supervised_response_recorded"
    assert result["mobile_chat_engine"] == "selene_chat_active_supervised"
    assert result["mobile"]["source_class"] == "local_supervised_chat_history"
    assert result["mobile"]["guard_flags"] == mobile_guard_flags()
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def test_mobile_capture_uses_selene_chat_session_when_supervised_active(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    seed_registry(conn)
    conn.execute(
        """
        INSERT INTO selene_activation_audit
        (state, action, actor, exact_phrase_matched, readiness_json, audit_json, source_refs, provenance_boundary)
        VALUES ('selene_chat_active_supervised', 'test_activate', 'Aleks', 1, '{}', '{}', '[]', 'test_mobile_activation')
        """
    )
    conn.commit()

    result = mobile_capture_review(conn, {"text": "Save this phone note for desktop tending."})

    assert result["status"] == "mobile_review_capture_recorded"
    assert result["session_id"]
    assert result["save_request"] == {}
    assert result["chest_item"]["item_type"] == "mobile_capture"
    assert result["chest_item"]["summary"] == "Save this phone note for desktop tending."
    assert result["guard_flags"]["memory_write_active"] is False
    assert conn.execute("SELECT COUNT(*) FROM selene_chat_sessions WHERE id = ?", (result["session_id"],)).fetchone()[0] == 1


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
