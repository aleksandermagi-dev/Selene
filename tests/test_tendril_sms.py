from __future__ import annotations

import base64
import http.client
import json
import threading
from urllib.parse import parse_qs

import pytest
import selene.sidecar as sidecar_module
import selene.tendril_sms as sms_module

from selene.db import connect, init_db
from selene.registry import seed_registry
from selene.sidecar import SeleneHandler, SeleneServer, start_sms_poll_thread
from selene.tendril_sms import (
    SmsAuthorityError,
    SmsTransportError,
    TwilioCredentials,
    TwilioSmsTransport,
    disable_sms,
    enable_sms,
    initiate_sms,
    list_sms_events,
    poll_sms,
    set_sms_mode,
    sms_private_config,
    sms_status,
)


ALEKS_NUMBER = "+15551234567"
SELENE_NUMBER = "+15557654321"


class FakeSmsTransport:
    provider = "twilio"

    def __init__(self, incoming=None):
        self.incoming = list(incoming or [])
        self.sent: list[dict[str, str]] = []

    def send(self, *, from_number: str, to_number: str, body: str):
        self.sent.append({"from": from_number, "to": to_number, "body": body})
        return {
            "sid": f"SM-out-{len(self.sent)}",
            "status": "queued",
            "direction": "outbound-api",
            "date_sent": "2026-07-19T12:00:00+00:00",
        }

    def list_inbound(self, *, to_number: str, from_number: str, limit: int = 20):
        return list(self.incoming[:limit])


class FailingSendSmsTransport(FakeSmsTransport):
    def send(self, *, from_number: str, to_number: str, body: str):
        raise SmsTransportError("synthetic delivery unavailable")


class FakeHttpResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def _db(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _enable(monkeypatch, tmp_path, *, mode="available"):
    monkeypatch.setenv("SELENE_DATA_DIR", str(tmp_path))
    return enable_sms(
        {
            "contact_number": ALEKS_NUMBER,
            "from_number": SELENE_NUMBER,
            "mode": mode,
        }
    )


def _inbound(sid="SM-in-1", body="Hi Selene, how are you?"):
    return {
        "sid": sid,
        "direction": "inbound",
        "from": ALEKS_NUMBER,
        "to": SELENE_NUMBER,
        "body": body,
        "status": "received",
        "date_sent": "2026-07-19T12:01:00+00:00",
    }


def _activate_chat(conn):
    seed_registry(conn)
    conn.execute(
        """
        INSERT INTO selene_activation_audit
        (state, action, actor, exact_phrase_matched, readiness_json, audit_json, source_refs, provenance_boundary)
        VALUES ('selene_chat_active_supervised', 'test_activate', 'Aleks', 1, '{}', '{}', '[]', 'test_sms_activation')
        """
    )
    conn.execute(
        """
        INSERT INTO transfer_c_readable_packages
        (package_hash, manifest_item_ids, included_counts, excluded_counts, package_json, source_refs, provenance_boundary)
        VALUES ('sms-test-package', '[]', '{}', '{}', '{}', '[]', 'test_sms_package')
        """
    )
    conn.commit()


def test_sms_is_disabled_by_default_and_keeps_general_autonomy_off(tmp_path, monkeypatch):
    monkeypatch.setenv("SELENE_DATA_DIR", str(tmp_path))
    conn = _db(tmp_path)

    status = sms_status(conn)

    assert status["status"] == "sms_setup_required"
    assert status["enabled"] is False
    assert status["delegated_message_authority"] is False
    assert status["boundaries"]["global_autonomy_expanded"] is False
    assert status["boundaries"]["memory_write_active"] is False
    assert status["boundaries"]["arbitrary_recipient_allowed"] is False


def test_enable_creates_one_scoped_grant_and_masks_numbers(tmp_path, monkeypatch):
    result = _enable(monkeypatch, tmp_path)
    config = sms_private_config()

    assert config["contact_number"] == ALEKS_NUMBER
    assert config["from_number"] == SELENE_NUMBER
    assert result["delegated_message_authority"] is True
    assert result["per_message_approval_required"] is False
    assert result["contact_number_masked"].endswith("4567")
    assert ALEKS_NUMBER not in json.dumps(result)
    assert SELENE_NUMBER not in json.dumps(result)

    disabled = disable_sms()
    assert disabled["delegated_message_authority"] is False
    assert disabled["mode"] == "offline"


def test_available_allows_three_unacknowledged_initiatives_then_pauses(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path)
    conn = _db(tmp_path)
    transport = FakeSmsTransport()

    for index in range(3):
        result = initiate_sms(
            conn,
            {"text": f"Ordinary check-in {index + 1}", "reason": "bounded relational check-in"},
            transport=transport,
        )
        assert result["status"] == "sms_queued"
        assert result["per_message_approval_required"] is False
        assert result["autonomous_action_allowed"] is False

    with pytest.raises(SmsAuthorityError, match="unacknowledged-message limit"):
        initiate_sms(
            conn,
            {"text": "A fourth check-in", "reason": "should be held"},
            transport=transport,
        )

    assert len(transport.sent) == 3
    assert sms_status(conn)["unacknowledged_outbound"] == 3


def test_quiet_allows_replies_but_blocks_initiative(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path, mode="quiet")
    conn = _db(tmp_path)

    with pytest.raises(SmsAuthorityError, match="initiative is unavailable"):
        initiate_sms(
            conn,
            {"text": "Unrequested idea", "reason": "quiet should block this"},
            transport=FakeSmsTransport(),
        )

    updated = set_sms_mode("available")
    assert updated["mode"] == "available"


def test_poll_is_idempotent_and_holds_speech_while_activation_is_inactive(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path)
    conn = _db(tmp_path)
    transport = FakeSmsTransport([_inbound()])

    first = poll_sms(conn, transport=transport)
    second = poll_sms(conn, transport=transport)

    assert first["processed"] == 1
    assert first["held"] == 1
    assert first["replied"] == 0
    assert second["processed"] == 0
    assert second["skipped"] == 1
    assert transport.sent == []
    events = list_sms_events(conn)["items"]
    assert len(events) == 1
    assert events[0]["delivery_status"] == "held_activation_inactive"


def test_active_selene_chat_replies_to_an_ordinary_inbound_sms(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path, mode="quiet")
    conn = _db(tmp_path)
    _activate_chat(conn)
    transport = FakeSmsTransport([_inbound()])

    result = poll_sms(conn, transport=transport)

    assert result["status"] == "sms_poll_complete"
    assert result["processed"] == 1
    assert result["replied"] == 1
    assert len(transport.sent) == 1
    assert transport.sent[0]["from"] == SELENE_NUMBER
    assert transport.sent[0]["to"] == ALEKS_NUMBER
    assert transport.sent[0]["body"].strip()
    assert conn.execute("SELECT COUNT(*) FROM selene_chat_messages").fetchone()[0] == 2
    audit = list_sms_events(conn)["items"]
    assert {item["direction"] for item in audit} == {"inbound", "outbound"}
    assert all("body" not in item for item in audit)
    assert all("number" not in item for item in audit)


def test_return_to_desktop_revokes_authority_without_sending_or_entering_chat(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path)
    conn = _db(tmp_path)
    transport = FakeSmsTransport([_inbound(body="  RETURN TO DESKTOP  ")])

    result = poll_sms(conn, transport=transport)

    assert result["status"] == "sms_poll_return_to_desktop_received"
    assert result["delegated_message_authority"] is False
    assert sms_private_config()["enabled"] is False
    assert transport.sent == []
    assert conn.execute("SELECT COUNT(*) FROM selene_chat_messages").fetchone()[0] == 0
    event = list_sms_events(conn)["items"][0]
    assert event["delivery_status"] == "return_to_desktop_received"


def test_ordinary_stop_language_is_not_treated_as_a_control_command(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path, mode="quiet")
    conn = _db(tmp_path)
    _activate_chat(conn)
    transport = FakeSmsTransport([_inbound(body="Can we stop and think about the plan for a moment?")])

    result = poll_sms(conn, transport=transport)

    assert result["status"] == "sms_poll_complete"
    assert result["replied"] == 1
    assert sms_private_config()["enabled"] is True


def test_offline_inbound_is_explicitly_held(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path, mode="offline")
    conn = _db(tmp_path)

    result = poll_sms(conn, transport=FakeSmsTransport([_inbound()]))

    assert result["held"] == 1
    assert list_sms_events(conn)["items"][0]["delivery_status"] == "held_offline"


def test_chat_failure_is_held_without_losing_the_inbound_audit(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path, mode="quiet")
    conn = _db(tmp_path)
    _activate_chat(conn)

    def fail_chat(_conn, _payload):
        raise ValueError("synthetic chat failure")

    monkeypatch.setattr(sms_module, "mobile_send_chat", fail_chat)
    result = poll_sms(conn, transport=FakeSmsTransport([_inbound()]))

    assert result["held"] == 1
    event = list_sms_events(conn)["items"][0]
    assert event["delivery_status"] == "held_chat_error"
    assert event["error_code"] == "ValueError"


def test_delivery_failure_is_held_and_audited_without_retrying_the_inbound(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path, mode="quiet")
    conn = _db(tmp_path)
    _activate_chat(conn)
    transport = FailingSendSmsTransport([_inbound()])

    first = poll_sms(conn, transport=transport)
    second = poll_sms(conn, transport=transport)

    assert first["held"] == 1
    assert second["skipped"] == 1
    events = list_sms_events(conn)["items"]
    assert {item["delivery_status"] for item in events} == {"held_delivery_error", "failed"}
    assert all(item["error_code"] == "SmsTransportError" for item in events)


def test_background_poller_runs_when_ready_and_stops_cleanly(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path)
    for name in ("TWILIO_ACCOUNT_SID", "TWILIO_API_KEY_SID", "TWILIO_API_KEY_SECRET"):
        monkeypatch.setenv(name, f"test-{name.lower()}")
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.sqlite3")
    calls = []

    def fake_poll(_conn):
        calls.append("poll")
        server.sms_stop_event.set()
        return {"status": "sms_poll_complete", "processed": 0, "replied": 0, "held": 0}

    monkeypatch.setattr(sidecar_module, "poll_sms", fake_poll)
    thread = start_sms_poll_thread(server, initial_delay_seconds=0)
    thread.join(timeout=2)
    server.server_close()
    server.conn.close()

    assert calls == ["poll"]
    assert thread.is_alive() is False


def test_background_poller_waits_for_credentials_without_provider_attempt(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path)
    for name in ("TWILIO_ACCOUNT_SID", "TWILIO_API_KEY_SID", "TWILIO_API_KEY_SECRET"):
        monkeypatch.delenv(name, raising=False)
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.sqlite3")
    calls = []
    original_status = sidecar_module.sms_status

    def status_then_stop(conn):
        status = original_status(conn)
        server.sms_stop_event.set()
        return status

    monkeypatch.setattr(sidecar_module, "sms_status", status_then_stop)
    monkeypatch.setattr(sidecar_module, "poll_sms", lambda _conn: calls.append("poll"))
    thread = start_sms_poll_thread(server, initial_delay_seconds=0)
    thread.join(timeout=2)
    server.server_close()
    server.conn.close()

    assert calls == []
    assert thread.is_alive() is False


def test_twilio_transport_uses_api_key_auth_and_message_resource_without_network():
    requests = []
    responses = [
        {
            "sid": "SM-out-1",
            "direction": "outbound-api",
            "from": SELENE_NUMBER,
            "to": ALEKS_NUMBER,
            "body": "Hello",
            "status": "queued",
        },
        {"messages": [_inbound()]},
    ]

    def opener(request, timeout):
        requests.append((request, timeout))
        return FakeHttpResponse(responses.pop(0))

    credentials = TwilioCredentials("AC-test", "SK-test", "secret-test")
    transport = TwilioSmsTransport(credentials, opener=opener)

    sent = transport.send(from_number=SELENE_NUMBER, to_number=ALEKS_NUMBER, body="Hello")
    incoming = transport.list_inbound(to_number=SELENE_NUMBER, from_number=ALEKS_NUMBER)

    assert sent["sid"] == "SM-out-1"
    assert incoming[0]["sid"] == "SM-in-1"
    post_request = requests[0][0]
    expected_token = base64.b64encode(b"SK-test:secret-test").decode("ascii")
    assert post_request.get_header("Authorization") == f"Basic {expected_token}"
    assert parse_qs(post_request.data.decode("utf-8")) == {
        "From": [SELENE_NUMBER],
        "To": [ALEKS_NUMBER],
        "Body": ["Hello"],
    }
    get_request = requests[1][0]
    assert "Messages.json?" in get_request.full_url
    assert "PageSize=20" in get_request.full_url
    assert "secret-test" not in get_request.full_url


def test_desktop_sidecar_can_enable_and_inspect_masked_sms_state(tmp_path, monkeypatch):
    monkeypatch.setenv("SELENE_DATA_DIR", str(tmp_path))
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.sqlite3")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request(
            "POST",
            "/api/mobile/sms/enable",
            body=json.dumps(
                {
                    "contact_number": ALEKS_NUMBER,
                    "from_number": SELENE_NUMBER,
                    "mode": "quiet",
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        enabled_response = conn.getresponse()
        enabled = json.loads(enabled_response.read().decode("utf-8"))
        conn.close()

        status_conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        status_conn.request("GET", "/api/mobile/sms/status")
        status_response = status_conn.getresponse()
        status = json.loads(status_response.read().decode("utf-8"))
        status_conn.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert enabled_response.status == 200
    assert enabled["enabled"] is True
    assert enabled["mode"] == "quiet"
    assert enabled["delegated_message_authority"] is True
    assert status_response.status == 200
    assert ALEKS_NUMBER not in json.dumps(status)
    assert SELENE_NUMBER not in json.dumps(status)
    assert status["boundaries"]["cocoon_actions_allowed"] is False
    assert status["runtime_state"] == "stopped"
    assert status["background_poller_alive"] is False
    assert status["conversation_exit_phrase"] == "return to desktop"
