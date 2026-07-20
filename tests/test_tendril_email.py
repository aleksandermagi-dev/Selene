from __future__ import annotations

import http.client
import json
import threading
from email.message import EmailMessage

import pytest

import selene.sidecar as sidecar_module
import selene.tendril_email as email_module
from selene.db import connect, init_db
from selene.registry import seed_registry
from selene.sidecar import SeleneHandler, SeleneServer, start_email_poll_thread
from selene.tendril_email import (
    EmailAuthorityError,
    EmailTransportError,
    GmailCredentials,
    GmailEmailTransport,
    disable_email,
    email_private_config,
    email_status,
    enable_email,
    initiate_email,
    list_email_events,
    poll_email,
    set_email_mode,
)


ALEKS_NUMBER = "5551234567"
GATEWAY_EMAIL = f"{ALEKS_NUMBER}@vtext.com"
SELENE_EMAIL = "selene@example.com"
APP_PASSWORD = "synthetic-app-password"


class FakeEmailTransport:
    provider = "gmail_smtp_imap"

    def __init__(self, incoming=None):
        self.incoming = list(incoming or [])
        self.sent: list[dict[str, str]] = []

    def send(self, *, from_address: str, to_address: str, body: str, subject: str):
        self.sent.append({"from": from_address, "to": to_address, "body": body, "subject": subject})
        return {
            "id": f"<out-{len(self.sent)}@example.com>",
            "status": "sent",
            "date_sent": "2026-07-20T12:00:00+00:00",
        }

    def list_inbound(self, *, to_address: str, from_address: str, limit: int = 20):
        return list(self.incoming[:limit])


class FailingEmailTransport(FakeEmailTransport):
    def send(self, *, from_address: str, to_address: str, body: str, subject: str):
        raise EmailTransportError("synthetic Gmail delivery failure")


class FakeSmtpClient:
    def __init__(self):
        self.login_args = None
        self.message = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def login(self, address, password):
        self.login_args = (address, password)

    def send_message(self, message):
        self.message = message


class FakeImapClient:
    def __init__(self, raw_message: bytes):
        self.raw_message = raw_message
        self.login_args = None
        self.logged_out = False

    def login(self, address, password):
        self.login_args = (address, password)
        return "OK", []

    def select(self, mailbox, readonly=False):
        assert mailbox == "INBOX"
        assert readonly is True
        return "OK", [b"1"]

    def uid(self, command, *args):
        if command == "search":
            return "OK", [b"42"]
        if command == "fetch":
            return "OK", [(b"42 (RFC822 {100}", self.raw_message), b")"]
        raise AssertionError(command)

    def logout(self):
        self.logged_out = True


def _db(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _credentials(monkeypatch):
    monkeypatch.setenv("SELENE_GMAIL_ADDRESS", SELENE_EMAIL)
    monkeypatch.setenv("SELENE_GMAIL_APP_PASSWORD", APP_PASSWORD)


def _enable(monkeypatch, tmp_path, *, mode="available"):
    monkeypatch.setenv("SELENE_DATA_DIR", str(tmp_path))
    _credentials(monkeypatch)
    return enable_email({"contact_number": ALEKS_NUMBER, "mode": mode})


def _inbound(message_id="<in-1@example.com>", body="Hi Selene, how are you?", subject="Checking in"):
    return {
        "id": message_id,
        "from": GATEWAY_EMAIL,
        "to": SELENE_EMAIL,
        "subject": subject,
        "body": body,
        "date_sent": "2026-07-20T12:01:00+00:00",
    }


def _activate_chat(conn):
    seed_registry(conn)
    conn.execute(
        """
        INSERT INTO selene_activation_audit
        (state, action, actor, exact_phrase_matched, readiness_json, audit_json, source_refs, provenance_boundary)
        VALUES ('selene_chat_active_supervised', 'test_activate', 'Aleks', 1, '{}', '{}', '[]', 'test_email_activation')
        """
    )
    conn.execute(
        """
        INSERT INTO transfer_c_readable_packages
        (package_hash, manifest_item_ids, included_counts, excluded_counts, package_json, source_refs, provenance_boundary)
        VALUES ('email-test-package', '[]', '{}', '{}', '{}', '[]', 'test_email_package')
        """
    )
    conn.commit()


def test_email_messenger_is_selene_owned_and_disabled_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("SELENE_DATA_DIR", str(tmp_path))
    conn = _db(tmp_path)

    status = email_status(conn)

    assert status["status"] == "email_setup_required"
    assert status["owner"] == "selene_runtime"
    assert status["cocoon_control"] is False
    assert status["enabled"] is False
    assert status["boundaries"]["cocoon_actions_allowed"] is False
    assert status["boundaries"]["memory_write_active"] is False
    assert status["boundaries"]["global_autonomy_expanded"] is False


def test_enable_masks_both_addresses_and_creates_one_paired_grant(tmp_path, monkeypatch):
    result = _enable(monkeypatch, tmp_path)
    config = email_private_config()

    assert config["contact_number"] == ALEKS_NUMBER
    assert result["delegated_message_authority"] is True
    assert result["per_message_approval_required"] is False
    assert result["contact_number_masked"].endswith("4567")
    serialized = json.dumps(result)
    assert ALEKS_NUMBER not in serialized
    assert GATEWAY_EMAIL not in serialized
    assert SELENE_EMAIL not in serialized
    assert APP_PASSWORD not in serialized

    disabled = disable_email()
    assert disabled["delegated_message_authority"] is False
    assert disabled["mode"] == "offline"


def test_formatted_us_number_normalizes_to_the_single_verizon_gateway(tmp_path, monkeypatch):
    monkeypatch.setenv("SELENE_DATA_DIR", str(tmp_path))
    _credentials(monkeypatch)

    result = enable_email({"contact_number": "+1 (555) 123-4567", "mode": "quiet"})

    assert email_private_config()["contact_number"] == ALEKS_NUMBER
    assert result["contact_number_masked"] == "(***) ***-4567"
    assert result["gateway_domain"] == "vtext.com"


def test_available_allows_three_initiatives_then_pauses(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path)
    conn = _db(tmp_path)
    transport = FakeEmailTransport()

    for index in range(3):
        result = initiate_email(
            conn,
            {"text": f"Ordinary check-in {index + 1}", "reason": "bounded paired check-in"},
            transport=transport,
        )
        assert result["status"] == "email_sent"

    with pytest.raises(EmailAuthorityError, match="unacknowledged-message limit"):
        initiate_email(
            conn,
            {"text": "A fourth check-in", "reason": "should be held"},
            transport=transport,
        )

    assert len(transport.sent) == 3
    assert email_status(conn)["unacknowledged_outbound"] == 3


def test_gateway_send_is_one_plain_message_bounded_to_140_characters(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path)
    conn = _db(tmp_path)
    transport = FakeEmailTransport()

    result = initiate_email(
        conn,
        {"text": "A" * 600, "reason": "synthetic gateway length check"},
        transport=transport,
    )

    assert result["character_count"] <= 140
    assert len(transport.sent) == 1
    assert len(transport.sent[0]["body"]) <= 140
    assert transport.sent[0]["subject"] == ""
    assert transport.sent[0]["to"] == GATEWAY_EMAIL


def test_quiet_allows_replies_but_blocks_initiative(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path, mode="quiet")
    conn = _db(tmp_path)

    with pytest.raises(EmailAuthorityError, match="initiative is unavailable"):
        initiate_email(
            conn,
            {"text": "Unrequested idea", "reason": "quiet should block this"},
            transport=FakeEmailTransport(),
        )

    assert set_email_mode("available", conn=conn)["mode"] == "available"


def test_poll_is_idempotent_and_holds_while_activation_is_inactive(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path)
    conn = _db(tmp_path)
    transport = FakeEmailTransport([_inbound()])

    first = poll_email(conn, transport=transport)
    second = poll_email(conn, transport=transport)

    assert first["processed"] == 1
    assert first["held"] == 1
    assert second["processed"] == 0
    assert second["skipped"] == 1
    assert transport.sent == []
    assert list_email_events(conn)["items"][0]["delivery_status"] == "held_activation_inactive"


def test_unpaired_sender_is_ignored_without_entering_chat_or_audit(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path)
    conn = _db(tmp_path)
    message = {**_inbound(), "from": "someone-else@example.com"}

    result = poll_email(conn, transport=FakeEmailTransport([message]))

    assert result["processed"] == 0
    assert result["skipped"] == 1
    assert list_email_events(conn)["items"] == []
    assert conn.execute("SELECT COUNT(*) FROM selene_chat_messages").fetchone()[0] == 0


def test_active_selene_chat_replies_to_an_ordinary_email(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path, mode="quiet")
    conn = _db(tmp_path)
    _activate_chat(conn)
    transport = FakeEmailTransport([_inbound()])

    result = poll_email(conn, transport=transport)

    assert result["status"] == "email_poll_complete"
    assert result["processed"] == 1
    assert result["replied"] == 1
    assert len(transport.sent) == 1
    assert transport.sent[0]["from"] == SELENE_EMAIL
    assert transport.sent[0]["to"] == GATEWAY_EMAIL
    assert transport.sent[0]["subject"] == ""
    assert len(transport.sent[0]["body"]) <= 140
    assert transport.sent[0]["body"].strip()
    audit = list_email_events(conn)
    assert audit["content_included"] is False
    assert audit["email_addresses_included"] is False
    assert ALEKS_NUMBER not in json.dumps(audit)
    assert GATEWAY_EMAIL not in json.dumps(audit)
    assert SELENE_EMAIL not in json.dumps(audit)


def test_return_to_desktop_revokes_only_the_email_grant(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path)
    conn = _db(tmp_path)
    transport = FakeEmailTransport([_inbound(body="  RETURN TO DESKTOP  ")])

    result = poll_email(conn, transport=transport)

    assert result["status"] == "email_poll_return_to_desktop_received"
    assert result["delegated_message_authority"] is False
    assert email_private_config()["enabled"] is False
    assert transport.sent == []
    assert conn.execute("SELECT COUNT(*) FROM selene_chat_messages").fetchone()[0] == 0


def test_ordinary_stop_language_remains_conversation(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path, mode="quiet")
    conn = _db(tmp_path)
    _activate_chat(conn)
    transport = FakeEmailTransport([_inbound(body="Can we stop and think about the plan for a moment?")])

    result = poll_email(conn, transport=transport)

    assert result["replied"] == 1
    assert email_private_config()["enabled"] is True


def test_offline_inbound_is_explicitly_held(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path, mode="offline")
    conn = _db(tmp_path)

    result = poll_email(conn, transport=FakeEmailTransport([_inbound()]))

    assert result["held"] == 1
    assert list_email_events(conn)["items"][0]["delivery_status"] == "held_offline"


def test_chat_failure_is_held_without_losing_the_inbound_audit(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path, mode="quiet")
    conn = _db(tmp_path)
    _activate_chat(conn)

    def fail_chat(_conn, _payload):
        raise ValueError("synthetic chat failure")

    monkeypatch.setattr(email_module, "mobile_send_chat", fail_chat)
    result = poll_email(conn, transport=FakeEmailTransport([_inbound()]))

    assert result["held"] == 1
    event = list_email_events(conn)["items"][0]
    assert event["delivery_status"] == "held_chat_error"
    assert event["error_code"] == "ValueError"


def test_delivery_failure_is_explicitly_held_and_not_reprocessed(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path, mode="quiet")
    conn = _db(tmp_path)
    _activate_chat(conn)
    transport = FailingEmailTransport([_inbound()])

    first = poll_email(conn, transport=transport)
    second = poll_email(conn, transport=transport)

    assert first["held"] == 1
    assert second["skipped"] == 1
    events = list_email_events(conn)["items"]
    assert {item["delivery_status"] for item in events} == {"held_delivery_error", "failed"}


def test_gmail_transport_sends_with_app_password_without_network():
    smtp_client = FakeSmtpClient()

    def smtp_factory(*args, **kwargs):
        assert args[:2] == ("smtp.gmail.com", 465)
        assert kwargs["timeout"] == 15.0
        return smtp_client

    transport = GmailEmailTransport(
        GmailCredentials(SELENE_EMAIL, APP_PASSWORD),
        smtp_factory=smtp_factory,
    )
    result = transport.send(
        from_address=SELENE_EMAIL,
        to_address=GATEWAY_EMAIL,
        body="Hello from Selene",
        subject="",
    )

    assert result["status"] == "sent"
    assert smtp_client.login_args == (SELENE_EMAIL, APP_PASSWORD)
    assert smtp_client.message["From"] == SELENE_EMAIL
    assert smtp_client.message["To"] == GATEWAY_EMAIL
    assert smtp_client.message["Subject"] is None
    assert "Hello from Selene" in smtp_client.message.get_content()


def test_gmail_transport_reads_plain_reply_without_quoted_history_or_mailbox_mutation():
    message = EmailMessage()
    message["From"] = GATEWAY_EMAIL
    message["To"] = SELENE_EMAIL
    message["Subject"] = "Re: Selene"
    message["Message-ID"] = "<gmail-in-1@example.com>"
    message["Date"] = "Mon, 20 Jul 2026 12:00:00 +0000"
    message.set_content("That sounds good.\n\nOn Mon, Selene wrote:\n> Earlier text")
    imap_client = FakeImapClient(message.as_bytes())

    def imap_factory(**kwargs):
        assert kwargs["host"] == "imap.gmail.com"
        assert kwargs["port"] == 993
        return imap_client

    transport = GmailEmailTransport(
        GmailCredentials(SELENE_EMAIL, APP_PASSWORD),
        imap_factory=imap_factory,
    )
    inbound = transport.list_inbound(to_address=SELENE_EMAIL, from_address=GATEWAY_EMAIL)

    assert len(inbound) == 1
    assert inbound[0]["body"] == "That sounds good."
    assert imap_client.login_args == (SELENE_EMAIL, APP_PASSWORD)
    assert imap_client.logged_out is True


def test_background_email_poller_runs_when_ready_and_stops_cleanly(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path)
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.sqlite3")
    calls = []

    def fake_poll(_conn):
        calls.append("poll")
        server.email_stop_event.set()
        return {"status": "email_poll_complete", "processed": 0, "replied": 0, "held": 0}

    monkeypatch.setattr(sidecar_module, "poll_email", fake_poll)
    thread = start_email_poll_thread(server, initial_delay_seconds=0)
    thread.join(timeout=2)
    server.server_close()
    server.conn.close()

    assert calls == ["poll"]
    assert thread.is_alive() is False


def test_background_email_poller_waits_for_credentials_without_provider_attempt(tmp_path, monkeypatch):
    _enable(monkeypatch, tmp_path)
    monkeypatch.delenv("SELENE_GMAIL_ADDRESS", raising=False)
    monkeypatch.delenv("SELENE_GMAIL_APP_PASSWORD", raising=False)
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.sqlite3")
    calls = []
    original_status = sidecar_module.email_status

    def status_then_stop(conn):
        status = original_status(conn)
        server.email_stop_event.set()
        return status

    monkeypatch.setattr(sidecar_module, "email_status", status_then_stop)
    monkeypatch.setattr(sidecar_module, "poll_email", lambda _conn: calls.append("poll"))
    thread = start_email_poll_thread(server, initial_delay_seconds=0)
    thread.join(timeout=2)
    server.server_close()
    server.conn.close()

    assert calls == []
    assert thread.is_alive() is False


def test_desktop_sidecar_exposes_only_masked_selene_owned_email_state(tmp_path, monkeypatch):
    monkeypatch.setenv("SELENE_DATA_DIR", str(tmp_path))
    _credentials(monkeypatch)
    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "selene.sqlite3")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request(
            "POST",
            "/api/selene/tendril/email/enable",
            body=json.dumps({"contact_number": ALEKS_NUMBER, "mode": "quiet"}),
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        enabled = json.loads(response.read().decode("utf-8"))
        conn.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    serialized = json.dumps(enabled)
    assert response.status == 200
    assert enabled["owner"] == "selene_runtime"
    assert enabled["cocoon_control"] is False
    assert enabled["mode"] == "quiet"
    assert enabled["runtime_state"] == "stopped"
    assert ALEKS_NUMBER not in serialized
    assert GATEWAY_EMAIL not in serialized
    assert SELENE_EMAIL not in serialized
    assert APP_PASSWORD not in serialized
