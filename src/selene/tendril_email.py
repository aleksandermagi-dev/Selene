from __future__ import annotations

import hashlib
import imaplib
import json
import os
import re
import smtplib
import sqlite3
import ssl
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage, Message
from email.parser import BytesParser
from email.utils import make_msgid, parseaddr, parsedate_to_datetime
from typing import Any, Callable, Protocol

from .activation import activation_is_active
from .mobile_chat import mobile_send_chat
from .paths import local_data_dir
from .registry import truncate


EMAIL_CONFIG_FILE = "selene_tendril_email.json"
EMAIL_PROVIDER = "gmail_smtp_imap"
EMAIL_CONTACT_ID = "aleks_primary"
EMAIL_MODES = {"available", "quiet", "offline"}
EMAIL_PURPOSES = {"reply", "initiative"}
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
DEFAULT_MAX_UNACKNOWLEDGED = 3
DEFAULT_POLL_INTERVAL_SECONDS = 15
MAX_EMAIL_BODY_CHARS = 4000
MAX_SUBJECT_CHARS = 120
RETURN_TO_DESKTOP_PHRASE = "return to desktop"


class EmailMessengerError(RuntimeError):
    """Base error for Selene's bounded paired-email messenger."""


class EmailConfigurationError(EmailMessengerError):
    """Raised when Gmail or paired-contact configuration is incomplete."""


class EmailAuthorityError(EmailMessengerError):
    """Raised when a send is outside Selene's delegated messaging authority."""


class EmailTransportError(EmailMessengerError):
    """Raised for a sanitized Gmail delivery or retrieval failure."""


class EmailTransport(Protocol):
    provider: str

    def send(self, *, from_address: str, to_address: str, body: str, subject: str) -> dict[str, Any]: ...

    def list_inbound(
        self,
        *,
        to_address: str,
        from_address: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class GmailCredentials:
    address: str
    app_password: str

    @classmethod
    def from_environment(cls) -> "GmailCredentials":
        address = os.environ.get("SELENE_GMAIL_ADDRESS", "").strip().lower()
        app_password = os.environ.get("SELENE_GMAIL_APP_PASSWORD", "").replace(" ", "").strip()
        missing = []
        if not address:
            missing.append("SELENE_GMAIL_ADDRESS")
        elif not EMAIL_PATTERN.fullmatch(address):
            raise EmailConfigurationError("SELENE_GMAIL_ADDRESS is not a valid email address")
        if not app_password:
            missing.append("SELENE_GMAIL_APP_PASSWORD")
        if missing:
            raise EmailConfigurationError(f"Gmail credentials are incomplete: {', '.join(missing)}")
        return cls(address=address, app_password=app_password)


class GmailEmailTransport:
    provider = EMAIL_PROVIDER

    def __init__(
        self,
        credentials: GmailCredentials | None = None,
        *,
        smtp_factory: Callable[..., Any] = smtplib.SMTP_SSL,
        imap_factory: Callable[..., Any] = imaplib.IMAP4_SSL,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.credentials = credentials or GmailCredentials.from_environment()
        self._smtp_factory = smtp_factory
        self._imap_factory = imap_factory
        self._timeout_seconds = timeout_seconds

    def send(self, *, from_address: str, to_address: str, body: str, subject: str) -> dict[str, Any]:
        message = EmailMessage()
        message["From"] = from_address
        message["To"] = to_address
        message["Subject"] = truncate(subject, MAX_SUBJECT_CHARS) or "Selene"
        message["Message-ID"] = make_msgid(domain=from_address.split("@", 1)[-1])
        message.set_content(body)
        try:
            with self._smtp_factory(
                "smtp.gmail.com",
                465,
                context=ssl.create_default_context(),
                timeout=self._timeout_seconds,
            ) as client:
                client.login(self.credentials.address, self.credentials.app_password)
                client.send_message(message)
        except (OSError, smtplib.SMTPException):
            raise EmailTransportError("Gmail could not deliver the paired message") from None
        return {
            "id": str(message["Message-ID"]),
            "status": "sent",
            "date_sent": _utc_now(),
        }

    def list_inbound(
        self,
        *,
        to_address: str,
        from_address: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        client: Any = None
        try:
            client = self._imap_factory(
                host="imap.gmail.com",
                port=993,
                ssl_context=ssl.create_default_context(),
                timeout=self._timeout_seconds,
            )
            client.login(self.credentials.address, self.credentials.app_password)
            status, _ = client.select("INBOX", readonly=True)
            if status != "OK":
                raise EmailTransportError("Gmail inbox is unavailable")
            status, rows = client.uid("search", None, "FROM", f'"{from_address}"')
            if status != "OK" or not rows:
                return []
            uids = rows[0].split()[-max(1, min(int(limit), 100)):]
            messages: list[dict[str, Any]] = []
            for uid in uids:
                fetch_status, fetched = client.uid("fetch", uid, "(RFC822)")
                if fetch_status != "OK":
                    continue
                raw = _raw_email_bytes(fetched)
                if not raw:
                    continue
                parsed = _parse_inbound_email(raw, fallback_id=f"gmail-uid-{uid.decode('ascii', errors='ignore')}")
                if _message_matches_pair(parsed, {"contact_email": from_address, "sender_email": to_address}):
                    messages.append(parsed)
            return sorted(messages, key=lambda item: (str(item.get("date_sent") or ""), str(item.get("id") or "")))
        except EmailTransportError:
            raise
        except (OSError, imaplib.IMAP4.error):
            raise EmailTransportError("Gmail could not read the paired inbox") from None
        finally:
            if client is not None:
                try:
                    client.logout()
                except (OSError, imaplib.IMAP4.error):
                    pass


def email_config_path() -> Any:
    return local_data_dir() / "selene_runtime" / "tendril" / EMAIL_CONFIG_FILE


def email_private_config() -> dict[str, Any]:
    try:
        data = json.loads(email_config_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    return _normalize_config(data if isinstance(data, dict) else {})


def email_status(conn: sqlite3.Connection | None = None) -> dict[str, Any]:
    config = email_private_config()
    credentials = _credential_state()
    counts: dict[str, int] = {}
    state: dict[str, Any] = {}
    if conn is not None:
        counts = {
            str(row["direction"]): int(row["count"])
            for row in conn.execute(
                "SELECT direction, COUNT(*) AS count FROM email_messaging_events GROUP BY direction"
            ).fetchall()
        }
        row = conn.execute(
            "SELECT * FROM email_messaging_state WHERE contact_id = ?",
            (EMAIL_CONTACT_ID,),
        ).fetchone()
        if row:
            state = dict(row)
    return {
        "status": "email_ready" if _is_ready(config, credentials) else "email_setup_required",
        "tool": "tendril_paired_email_messenger",
        "transport": "direct_email",
        "provider": EMAIL_PROVIDER,
        "owner": "selene_runtime",
        "cocoon_control": False,
        "enabled": config["enabled"],
        "mode": config["mode"],
        "contact_id": EMAIL_CONTACT_ID,
        "contact_email_masked": _mask_email(config["contact_email"]),
        "sender_email_masked": _mask_email(os.environ.get("SELENE_GMAIL_ADDRESS", "")),
        "delegated_message_authority": config["delegated_message_authority"],
        "per_message_approval_required": False,
        "autonomous_action_allowed": False,
        "reply_allowed": config["reply_allowed"],
        "initiative_allowed": config["initiative_allowed"],
        "max_unacknowledged": config["max_unacknowledged"],
        "unacknowledged_outbound": int(state.get("unacknowledged_outbound") or 0),
        "poll_interval_seconds": config["poll_interval_seconds"],
        "credentials": credentials,
        "event_counts": counts,
        "last_inbound_at": state.get("last_inbound_at") or "",
        "last_outbound_at": state.get("last_outbound_at") or "",
        "last_poll_at": state.get("last_poll_at") or "",
        "last_poll_status": state.get("last_poll_status") or "not_run",
        "conversation_exit_phrase": RETURN_TO_DESKTOP_PHRASE,
        "boundaries": _email_boundaries(config),
    }


def enable_email(payload: dict[str, Any] | None = None, *, conn: sqlite3.Connection | None = None) -> dict[str, Any]:
    payload = payload or {}
    contact_email = _email_address(str(payload.get("contact_email") or ""), "Aleks paired email")
    mode = str(payload.get("mode") or "available").strip().lower()
    if mode not in EMAIL_MODES:
        raise ValueError("Email mode must be available, quiet, or offline")
    config = _normalize_config({
        "enabled": True,
        "contact_email": contact_email,
        "mode": mode,
        "delegated_message_authority": True,
        "reply_allowed": True,
        "initiative_allowed": True,
        "max_unacknowledged": DEFAULT_MAX_UNACKNOWLEDGED,
        "poll_interval_seconds": int(payload.get("poll_interval_seconds") or DEFAULT_POLL_INTERVAL_SECONDS),
    })
    _write_config(config)
    if conn is not None:
        _reset_delivery_window(conn)
    return {
        **email_status(conn),
        "status": "email_delegated_authority_enabled",
        "message": "Selene may reply to Aleks and use bounded initiative through her paired email.",
    }


def disable_email(*, reason: str = "selene_runtime_revocation", conn: sqlite3.Connection | None = None) -> dict[str, Any]:
    config = email_private_config()
    config.update({
        "enabled": False,
        "mode": "offline",
        "delegated_message_authority": False,
        "reply_allowed": False,
        "initiative_allowed": False,
    })
    _write_config(config)
    return {
        **email_status(conn),
        "status": "email_delegated_authority_revoked",
        "reason": reason,
        "message": "Selene's paired-email delivery authority is off.",
    }


def set_email_mode(mode: str, *, conn: sqlite3.Connection | None = None) -> dict[str, Any]:
    normalized = str(mode or "").strip().lower()
    if normalized not in EMAIL_MODES:
        raise ValueError("Email mode must be available, quiet, or offline")
    config = email_private_config()
    if not config["enabled"] or not config["delegated_message_authority"]:
        raise EmailAuthorityError("Paired-email authority is not enabled")
    config["mode"] = normalized
    _write_config(config)
    return {**email_status(conn), "status": "email_presence_mode_updated"}


def list_email_events(conn: sqlite3.Connection, limit: int = 25) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT id, provider, provider_message_id, direction, contact_id, purpose,
               delivery_status, chat_session_id, chat_message_id, character_count,
               acknowledged, error_code, occurred_at, created_at
        FROM email_messaging_events
        ORDER BY id DESC
        LIMIT ?
        """,
        (max(1, min(int(limit), 100)),),
    ).fetchall()
    return {
        "status": "email_events_listed",
        "items": [dict(row) for row in rows],
        "content_included": False,
        "email_addresses_included": False,
        "owner": "selene_runtime",
        "cocoon_control": False,
        "boundaries": _email_boundaries(email_private_config()),
    }


def send_email(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    transport: EmailTransport | None = None,
) -> dict[str, Any]:
    config = email_private_config()
    text = truncate(str(payload.get("text") or ""), MAX_EMAIL_BODY_CHARS)
    if not text.strip():
        raise ValueError("Email text is required")
    purpose = str(payload.get("purpose") or "initiative").strip().lower()
    if purpose not in EMAIL_PURPOSES:
        raise ValueError("Email purpose must be reply or initiative")
    _assert_send_authority(conn, config, purpose)
    if purpose == "initiative" and not str(payload.get("reason") or "").strip():
        raise ValueError("A bounded Tendril reason is required for initiative")
    credentials = GmailCredentials.from_environment()
    active_transport = transport or GmailEmailTransport(credentials)
    subject = truncate(str(payload.get("subject") or "Selene"), MAX_SUBJECT_CHARS) or "Selene"
    try:
        delivered = active_transport.send(
            from_address=credentials.address,
            to_address=config["contact_email"],
            body=text,
            subject=subject,
        )
    except EmailTransportError as exc:
        _record_event(
            conn,
            provider_message_id=None,
            direction="outbound",
            purpose=purpose,
            delivery_status="failed",
            text=text,
            occurred_at=_utc_now(),
            chat_session_id=_optional_int(payload.get("chat_session_id")),
            chat_message_id=_optional_int(payload.get("chat_message_id")),
            error_code=type(exc).__name__,
        )
        raise
    provider_id = str(delivered.get("id") or "")
    event_id = _record_event(
        conn,
        provider_message_id=provider_id or None,
        direction="outbound",
        purpose=purpose,
        delivery_status=str(delivered.get("status") or "sent"),
        text=text,
        occurred_at=str(delivered.get("date_sent") or _utc_now()),
        chat_session_id=_optional_int(payload.get("chat_session_id")),
        chat_message_id=_optional_int(payload.get("chat_message_id")),
    )
    _increment_unacknowledged(conn)
    return {
        "status": "email_sent",
        "event_id": event_id,
        "provider_message_id": provider_id,
        "delivery_status": str(delivered.get("status") or "sent"),
        "purpose": purpose,
        "contact_id": EMAIL_CONTACT_ID,
        "character_count": len(text),
        "delegated_message_authority": True,
        "per_message_approval_required": False,
        "autonomous_action_allowed": False,
        "boundaries": _email_boundaries(config),
    }


def initiate_email(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    transport: EmailTransport | None = None,
) -> dict[str, Any]:
    return send_email(conn, {**payload, "purpose": "initiative"}, transport=transport)


def poll_email(
    conn: sqlite3.Connection,
    *,
    transport: EmailTransport | None = None,
    inbound_messages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    config = email_private_config()
    if not config["enabled"]:
        return {"status": "email_poll_disabled", "processed": 0, "replied": 0, "skipped": 0, "held": 0}
    if not config["delegated_message_authority"]:
        return {"status": "email_poll_authority_revoked", "processed": 0, "replied": 0, "skipped": 0, "held": 0}
    credentials = GmailCredentials.from_environment()
    active_transport = transport or GmailEmailTransport(credentials)
    try:
        incoming = inbound_messages if inbound_messages is not None else active_transport.list_inbound(
            to_address=credentials.address,
            from_address=config["contact_email"],
            limit=20,
        )
    except EmailTransportError:
        _update_poll_state(conn, "provider_error")
        raise
    processed = replied = skipped = held = 0
    for message in incoming:
        provider_id = str(message.get("id") or "").strip()
        text = truncate(str(message.get("body") or ""), MAX_EMAIL_BODY_CHARS)
        if not provider_id or not text.strip() or _event_exists(conn, provider_id):
            skipped += 1
            continue
        if not _message_matches_pair(message, {**config, "sender_email": credentials.address}):
            skipped += 1
            continue
        _acknowledge_outbound(conn)
        inbound_event_id = _record_event(
            conn,
            provider_message_id=provider_id,
            direction="inbound",
            purpose="reply",
            delivery_status="received",
            text=text,
            occurred_at=str(message.get("date_sent") or _utc_now()),
        )
        processed += 1
        if text.strip().casefold() == RETURN_TO_DESKTOP_PHRASE:
            disable_email(reason="email_return_to_desktop_received", conn=conn)
            _set_event_status(conn, inbound_event_id, "return_to_desktop_received")
            _update_poll_state(conn, "authority_revoked_by_return_to_desktop")
            return {
                "status": "email_poll_return_to_desktop_received",
                "processed": processed,
                "replied": replied,
                "skipped": skipped,
                "held": held,
                "delegated_message_authority": False,
            }
        if config["mode"] == "offline" or not config["reply_allowed"]:
            _set_event_status(conn, inbound_event_id, "held_offline")
            held += 1
            continue
        if not activation_is_active(conn):
            _set_event_status(conn, inbound_event_id, "held_activation_inactive")
            held += 1
            continue
        session_id = _email_session_id(conn)
        try:
            chat_result = mobile_send_chat(conn, {"text": text, "session_id": session_id})
        except Exception as exc:  # Isolate a chat-path failure from the inbox poller.
            _set_event_status(conn, inbound_event_id, "held_chat_error", error_code=type(exc).__name__)
            held += 1
            continue
        candidate = truncate(str(chat_result.get("candidate_text") or ""), MAX_EMAIL_BODY_CHARS)
        if not candidate.strip():
            _set_event_status(conn, inbound_event_id, "held_no_response")
            held += 1
            continue
        _link_inbound_event(
            conn,
            inbound_event_id,
            _optional_int(chat_result.get("session_id")),
            _optional_int(chat_result.get("user_message_id")),
        )
        try:
            send_email(
                conn,
                {
                    "text": candidate,
                    "subject": _reply_subject(str(message.get("subject") or "Selene")),
                    "purpose": "reply",
                    "chat_session_id": chat_result.get("session_id"),
                    "chat_message_id": chat_result.get("assistant_message_id"),
                },
                transport=active_transport,
            )
        except (EmailMessengerError, TypeError, ValueError) as exc:
            _set_event_status(conn, inbound_event_id, "held_delivery_error", error_code=type(exc).__name__)
            held += 1
            continue
        replied += 1
    _update_poll_state(conn, "complete")
    return {
        "status": "email_poll_complete",
        "processed": processed,
        "replied": replied,
        "skipped": skipped,
        "held": held,
        "delegated_message_authority": config["delegated_message_authority"],
        "autonomous_action_allowed": False,
        "boundaries": _email_boundaries(config),
    }


def _normalize_config(data: dict[str, Any]) -> dict[str, Any]:
    mode = str(data.get("mode") or "offline").lower()
    if mode not in EMAIL_MODES:
        mode = "offline"
    interval = int(data.get("poll_interval_seconds") or DEFAULT_POLL_INTERVAL_SECONDS)
    return {
        "enabled": bool(data.get("enabled")),
        "contact_email": str(data.get("contact_email") or "").strip().lower(),
        "mode": mode,
        "delegated_message_authority": bool(data.get("delegated_message_authority")),
        "reply_allowed": bool(data.get("reply_allowed")),
        "initiative_allowed": bool(data.get("initiative_allowed")),
        "max_unacknowledged": max(1, min(int(data.get("max_unacknowledged") or DEFAULT_MAX_UNACKNOWLEDGED), 3)),
        "poll_interval_seconds": max(10, min(interval, 300)),
    }


def _write_config(config: dict[str, Any]) -> None:
    path = email_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(_normalize_config(config), indent=2)
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(serialized)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = temporary.name
        os.replace(temporary_path, path)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def _credential_state() -> dict[str, Any]:
    address = os.environ.get("SELENE_GMAIL_ADDRESS", "").strip().lower()
    password_ready = bool(os.environ.get("SELENE_GMAIL_APP_PASSWORD", "").replace(" ", "").strip())
    missing = []
    if not address:
        missing.append("SELENE_GMAIL_ADDRESS")
    if not password_ready:
        missing.append("SELENE_GMAIL_APP_PASSWORD")
    valid_address = bool(EMAIL_PATTERN.fullmatch(address)) if address else False
    return {
        "ready": not missing and valid_address,
        "address_masked": _mask_email(address),
        "missing_environment_variables": missing,
        "address_valid": valid_address,
        "secret_values_exposed": False,
        "auth_method": "revocable_gmail_app_password",
    }


def _is_ready(config: dict[str, Any], credentials: dict[str, Any]) -> bool:
    return bool(
        config["enabled"]
        and config["delegated_message_authority"]
        and config["contact_email"]
        and credentials["ready"]
    )


def _email_boundaries(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "scope": "paired_email_with_aleks_only",
        "owner": "selene_runtime",
        "cocoon_control": False,
        "delegated_message_authority": bool(config.get("delegated_message_authority")),
        "per_message_approval_required": False,
        "autonomous_action_allowed": False,
        "global_autonomy_expanded": False,
        "arbitrary_recipient_allowed": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "governance_change_allowed": False,
        "identity_change_allowed": False,
        "cocoon_actions_allowed": False,
        "review_decisions_allowed": False,
        "file_access_allowed": False,
        "provider_training_allowed": False,
        "conversation_exit_phrase": RETURN_TO_DESKTOP_PHRASE,
    }


def _assert_send_authority(conn: sqlite3.Connection, config: dict[str, Any], purpose: str) -> None:
    if not config["enabled"] or not config["delegated_message_authority"]:
        raise EmailAuthorityError("Paired-email authority is not enabled")
    if config["mode"] == "offline":
        raise EmailAuthorityError("Paired-email mode is offline")
    if purpose == "initiative" and (config["mode"] != "available" or not config["initiative_allowed"]):
        raise EmailAuthorityError("Paired-email initiative is unavailable in the current mode")
    if purpose == "reply" and not config["reply_allowed"]:
        raise EmailAuthorityError("Paired-email replies are not allowed")
    if _unacknowledged_count(conn) >= int(config["max_unacknowledged"]):
        raise EmailAuthorityError("Paired email paused at the unacknowledged-message limit")


def _record_event(
    conn: sqlite3.Connection,
    *,
    provider_message_id: str | None,
    direction: str,
    purpose: str,
    delivery_status: str,
    text: str,
    occurred_at: str,
    chat_session_id: int | None = None,
    chat_message_id: int | None = None,
    error_code: str = "",
) -> int:
    cur = conn.execute(
        """
        INSERT INTO email_messaging_events
        (provider, provider_message_id, direction, contact_id, purpose, delivery_status,
         chat_session_id, chat_message_id, body_sha256, character_count, acknowledged,
         error_code, occurred_at, provenance_boundary, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
        """,
        (
            EMAIL_PROVIDER,
            provider_message_id,
            direction,
            EMAIL_CONTACT_ID,
            purpose,
            delivery_status,
            chat_session_id,
            chat_message_id,
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
            len(text),
            error_code,
            occurred_at,
            "selene_tendril_paired_email_no_cocoon_no_memory_no_general_autonomy",
            json.dumps({"content_stored": False, "email_addresses_stored": False}),
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def _event_exists(conn: sqlite3.Connection, provider_message_id: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM email_messaging_events WHERE provider_message_id = ?",
        (provider_message_id,),
    ).fetchone() is not None


def _link_inbound_event(conn: sqlite3.Connection, event_id: int, session_id: int | None, message_id: int | None) -> None:
    conn.execute(
        "UPDATE email_messaging_events SET chat_session_id = ?, chat_message_id = ? WHERE id = ?",
        (session_id, message_id, event_id),
    )
    conn.execute(
        """
        INSERT INTO email_messaging_state(contact_id, chat_session_id, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(contact_id) DO UPDATE SET chat_session_id = excluded.chat_session_id, updated_at = CURRENT_TIMESTAMP
        """,
        (EMAIL_CONTACT_ID, session_id),
    )
    conn.commit()


def _set_event_status(conn: sqlite3.Connection, event_id: int, status: str, *, error_code: str = "") -> None:
    conn.execute(
        "UPDATE email_messaging_events SET delivery_status = ?, error_code = ? WHERE id = ?",
        (status, error_code, event_id),
    )
    conn.commit()


def _email_session_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute(
        "SELECT chat_session_id FROM email_messaging_state WHERE contact_id = ?",
        (EMAIL_CONTACT_ID,),
    ).fetchone()
    return _optional_int(row["chat_session_id"] if row else None)


def _unacknowledged_count(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT unacknowledged_outbound FROM email_messaging_state WHERE contact_id = ?",
        (EMAIL_CONTACT_ID,),
    ).fetchone()
    return int(row["unacknowledged_outbound"] or 0) if row else 0


def _increment_unacknowledged(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT INTO email_messaging_state(contact_id, unacknowledged_outbound, last_outbound_at, updated_at)
        VALUES (?, 1, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(contact_id) DO UPDATE SET
          unacknowledged_outbound = unacknowledged_outbound + 1,
          last_outbound_at = excluded.last_outbound_at,
          updated_at = CURRENT_TIMESTAMP
        """,
        (EMAIL_CONTACT_ID, _utc_now()),
    )
    conn.commit()


def _acknowledge_outbound(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE email_messaging_events SET acknowledged = 1 WHERE direction = 'outbound' AND acknowledged = 0")
    conn.execute(
        """
        INSERT INTO email_messaging_state(contact_id, unacknowledged_outbound, last_inbound_at, updated_at)
        VALUES (?, 0, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(contact_id) DO UPDATE SET
          unacknowledged_outbound = 0,
          last_inbound_at = excluded.last_inbound_at,
          updated_at = CURRENT_TIMESTAMP
        """,
        (EMAIL_CONTACT_ID, _utc_now()),
    )
    conn.commit()


def _reset_delivery_window(conn: sqlite3.Connection) -> None:
    conn.execute("UPDATE email_messaging_events SET acknowledged = 1 WHERE direction = 'outbound' AND acknowledged = 0")
    conn.execute(
        """
        INSERT INTO email_messaging_state(contact_id, unacknowledged_outbound, updated_at)
        VALUES (?, 0, CURRENT_TIMESTAMP)
        ON CONFLICT(contact_id) DO UPDATE SET unacknowledged_outbound = 0, updated_at = CURRENT_TIMESTAMP
        """,
        (EMAIL_CONTACT_ID,),
    )
    conn.commit()


def _update_poll_state(conn: sqlite3.Connection, status: str) -> None:
    conn.execute(
        """
        INSERT INTO email_messaging_state(contact_id, last_poll_at, last_poll_status, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(contact_id) DO UPDATE SET
          last_poll_at = excluded.last_poll_at,
          last_poll_status = excluded.last_poll_status,
          updated_at = CURRENT_TIMESTAMP
        """,
        (EMAIL_CONTACT_ID, _utc_now(), status),
    )
    conn.commit()


def _message_matches_pair(message: dict[str, Any], config: dict[str, Any]) -> bool:
    return (
        str(message.get("from") or "").strip().lower() == str(config.get("contact_email") or "").strip().lower()
        and str(message.get("to") or "").strip().lower() == str(config.get("sender_email") or "").strip().lower()
    )


def _raw_email_bytes(fetched: Any) -> bytes:
    for item in fetched or []:
        if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], bytes):
            return item[1]
    return b""


def _parse_inbound_email(raw: bytes, *, fallback_id: str) -> dict[str, Any]:
    message = BytesParser(policy=policy.default).parsebytes(raw)
    sender = parseaddr(str(message.get("From") or ""))[1].strip().lower()
    recipient = parseaddr(str(message.get("To") or ""))[1].strip().lower()
    message_id = str(message.get("Message-ID") or fallback_id).strip()
    return {
        "id": message_id,
        "from": sender,
        "to": recipient,
        "subject": truncate(str(message.get("Subject") or "Selene"), MAX_SUBJECT_CHARS),
        "body": _strip_reply_quote(_plain_text(message)),
        "date_sent": _email_date(str(message.get("Date") or "")),
    }


def _plain_text(message: Message) -> str:
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain" and "attachment" not in str(part.get("Content-Disposition") or "").lower():
                try:
                    content = part.get_content()
                except (LookupError, UnicodeDecodeError):
                    continue
                return str(content or "")
        return ""
    try:
        return str(message.get_content() or "")
    except (LookupError, UnicodeDecodeError):
        payload = message.get_payload(decode=True)
        return payload.decode("utf-8", errors="replace") if isinstance(payload, bytes) else str(payload or "")


def _strip_reply_quote(value: str) -> str:
    kept: list[str] = []
    for line in value.replace("\r\n", "\n").split("\n"):
        stripped = line.strip()
        if stripped.startswith(">"):
            continue
        if stripped == "-----Original Message-----" or (stripped.startswith("On ") and stripped.endswith(" wrote:")):
            break
        kept.append(line)
    return truncate("\n".join(kept).strip(), MAX_EMAIL_BODY_CHARS)


def _reply_subject(subject: str) -> str:
    normalized = truncate(subject.strip() or "Selene", MAX_SUBJECT_CHARS)
    return normalized if normalized.lower().startswith("re:") else truncate(f"Re: {normalized}", MAX_SUBJECT_CHARS)


def _email_date(raw: str) -> str:
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError):
        return _utc_now()


def _email_address(value: str, label: str) -> str:
    normalized = value.strip().lower()
    if not EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError(f"{label} must be a valid email address")
    return normalized


def _mask_email(value: str) -> str:
    normalized = str(value or "").strip()
    if "@" not in normalized:
        return ""
    local, domain = normalized.rsplit("@", 1)
    visible = local[:1]
    return f"{visible}{'*' * max(3, len(local) - 1)}@{domain}"


def _optional_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
