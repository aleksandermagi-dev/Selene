from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .activation import activation_is_active
from .mobile_chat import mobile_send_chat
from .paths import local_data_dir
from .registry import truncate


SMS_CONFIG_FILE = "sms_messaging.json"
SMS_PROVIDER = "twilio"
SMS_CONTACT_ID = "aleks_primary"
SMS_MODES = {"available", "quiet", "offline"}
SMS_PURPOSES = {"reply", "initiative"}
E164_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")
DEFAULT_MAX_UNACKNOWLEDGED = 3
DEFAULT_POLL_INTERVAL_SECONDS = 15
MAX_SMS_BODY_CHARS = 1200
STOP_KEYWORDS = {"stop", "stopall", "unsubscribe", "cancel", "end", "quit"}


class SmsError(RuntimeError):
    """Base error for the bounded SMS messenger."""


class SmsConfigurationError(SmsError):
    """Raised when local provider configuration is incomplete."""


class SmsAuthorityError(SmsError):
    """Raised when a request is outside the delegated SMS authority."""


class SmsTransportError(SmsError):
    """Raised for a sanitized provider delivery or retrieval failure."""


class SmsTransport(Protocol):
    provider: str

    def send(self, *, from_number: str, to_number: str, body: str) -> dict[str, Any]: ...

    def list_inbound(self, *, to_number: str, from_number: str, limit: int = 20) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class TwilioCredentials:
    account_sid: str
    api_key_sid: str
    api_key_secret: str

    @classmethod
    def from_environment(cls) -> "TwilioCredentials":
        values = {
            "account_sid": os.environ.get("TWILIO_ACCOUNT_SID", "").strip(),
            "api_key_sid": os.environ.get("TWILIO_API_KEY_SID", "").strip(),
            "api_key_secret": os.environ.get("TWILIO_API_KEY_SECRET", "").strip(),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise SmsConfigurationError(f"Twilio credentials are incomplete: {', '.join(missing)}")
        return cls(**values)


class TwilioSmsTransport:
    provider = SMS_PROVIDER

    def __init__(
        self,
        credentials: TwilioCredentials | None = None,
        *,
        opener: Callable[..., Any] = urlopen,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.credentials = credentials or TwilioCredentials.from_environment()
        self._opener = opener
        self._timeout_seconds = timeout_seconds
        self._messages_url = (
            "https://api.twilio.com/2010-04-01/Accounts/"
            f"{self.credentials.account_sid}/Messages.json"
        )

    def send(self, *, from_number: str, to_number: str, body: str) -> dict[str, Any]:
        payload = self._request(
            self._messages_url,
            method="POST",
            form={"From": from_number, "To": to_number, "Body": body},
        )
        return _normalize_twilio_message(payload)

    def list_inbound(self, *, to_number: str, from_number: str, limit: int = 20) -> list[dict[str, Any]]:
        query = urlencode({"To": to_number, "From": from_number, "PageSize": max(1, min(int(limit), 100))})
        payload = self._request(f"{self._messages_url}?{query}", method="GET")
        messages = payload.get("messages") if isinstance(payload, dict) else []
        if not isinstance(messages, list):
            return []
        normalized = [_normalize_twilio_message(item) for item in messages if isinstance(item, dict)]
        inbound = [item for item in normalized if item.get("direction") == "inbound"]
        return sorted(inbound, key=lambda item: (_message_timestamp(item), str(item.get("sid") or "")))

    def _request(self, url: str, *, method: str, form: dict[str, str] | None = None) -> dict[str, Any]:
        body = urlencode(form).encode("utf-8") if form is not None else None
        token = base64.b64encode(
            f"{self.credentials.api_key_sid}:{self.credentials.api_key_secret}".encode("utf-8")
        ).decode("ascii")
        request = Request(
            url,
            data=body,
            method=method,
            headers={
                "Authorization": f"Basic {token}",
                "Accept": "application/json",
                **({"Content-Type": "application/x-www-form-urlencoded"} if body is not None else {}),
            },
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            raise SmsTransportError(f"Twilio request failed with HTTP {exc.code}") from None
        except (URLError, TimeoutError, OSError):
            raise SmsTransportError("Twilio could not be reached") from None
        try:
            payload = json.loads(raw or "{}")
        except json.JSONDecodeError:
            raise SmsTransportError("Twilio returned an unreadable response") from None
        if not isinstance(payload, dict):
            raise SmsTransportError("Twilio returned an unexpected response")
        return payload


def sms_config_path() -> Any:
    return local_data_dir() / SMS_CONFIG_FILE


def sms_private_config() -> dict[str, Any]:
    try:
        data = json.loads(sms_config_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    return _normalize_config(data if isinstance(data, dict) else {})


def sms_status(conn: sqlite3.Connection | None = None) -> dict[str, Any]:
    config = sms_private_config()
    credential_state = _credential_state()
    counts: dict[str, int] = {}
    state: dict[str, Any] = {}
    if conn is not None:
        counts = {
            str(row["direction"]): int(row["count"])
            for row in conn.execute(
                "SELECT direction, COUNT(*) AS count FROM sms_messaging_events GROUP BY direction"
            ).fetchall()
        }
        row = conn.execute(
            "SELECT * FROM sms_messaging_state WHERE contact_id = ?",
            (SMS_CONTACT_ID,),
        ).fetchone()
        if row:
            state = dict(row)
    return {
        "status": "sms_ready" if _is_ready(config, credential_state) else "sms_setup_required",
        "tool": "tendril_paired_device_messenger",
        "transport": "carrier_sms",
        "provider": config["provider"],
        "enabled": config["enabled"],
        "mode": config["mode"],
        "contact_id": config["contact_id"],
        "contact_number_masked": _mask_number(config["contact_number"]),
        "sender_number_masked": _mask_number(config["from_number"]),
        "delegated_message_authority": config["delegated_message_authority"],
        "per_message_approval_required": False,
        "autonomous_action_allowed": False,
        "reply_allowed": config["reply_allowed"],
        "initiative_allowed": config["initiative_allowed"],
        "max_unacknowledged": config["max_unacknowledged"],
        "unacknowledged_outbound": int(state.get("unacknowledged_outbound") or 0),
        "poll_interval_seconds": config["poll_interval_seconds"],
        "credentials": credential_state,
        "event_counts": counts,
        "last_inbound_at": state.get("last_inbound_at") or "",
        "last_outbound_at": state.get("last_outbound_at") or "",
        "last_poll_at": state.get("last_poll_at") or "",
        "last_poll_status": state.get("last_poll_status") or "not_run",
        "boundaries": _sms_boundaries(config),
    }


def enable_sms(
    payload: dict[str, Any] | None = None,
    *,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    contact_number = _e164(str(payload.get("contact_number") or ""), "Aleks contact number")
    from_number = _e164(str(payload.get("from_number") or ""), "Selene SMS number")
    mode = str(payload.get("mode") or "available").strip().lower()
    if mode not in SMS_MODES:
        raise ValueError("SMS mode must be available, quiet, or offline")
    config = _normalize_config(
        {
            "enabled": True,
            "provider": SMS_PROVIDER,
            "contact_id": SMS_CONTACT_ID,
            "contact_number": contact_number,
            "from_number": from_number,
            "mode": mode,
            "delegated_message_authority": True,
            "reply_allowed": True,
            "initiative_allowed": True,
            "max_unacknowledged": DEFAULT_MAX_UNACKNOWLEDGED,
            "poll_interval_seconds": int(payload.get("poll_interval_seconds") or DEFAULT_POLL_INTERVAL_SECONDS),
        }
    )
    _write_config(config)
    if conn is not None:
        _reset_delivery_window(conn)
    return {
        **sms_status(),
        "status": "sms_delegated_authority_enabled",
        "message": "Aleks's paired number may receive replies and bounded initiative without per-message approval.",
    }


def disable_sms(*, reason: str = "desktop_revocation") -> dict[str, Any]:
    config = sms_private_config()
    config.update(
        {
            "enabled": False,
            "mode": "offline",
            "delegated_message_authority": False,
            "reply_allowed": False,
            "initiative_allowed": False,
        }
    )
    _write_config(config)
    return {
        **sms_status(),
        "status": "sms_delegated_authority_revoked",
        "reason": reason,
        "message": "SMS delivery authority is off. Existing chat and memory boundaries are unchanged.",
    }


def set_sms_mode(mode: str) -> dict[str, Any]:
    normalized = str(mode or "").strip().lower()
    if normalized not in SMS_MODES:
        raise ValueError("SMS mode must be available, quiet, or offline")
    config = sms_private_config()
    if not config["enabled"] or not config["delegated_message_authority"]:
        raise SmsAuthorityError("SMS delegated authority is not enabled")
    config["mode"] = normalized
    _write_config(config)
    return {**sms_status(), "status": "sms_presence_mode_updated"}


def list_sms_events(conn: sqlite3.Connection, limit: int = 25) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT id, provider, provider_message_id, direction, contact_id, purpose,
               delivery_status, chat_session_id, chat_message_id, character_count,
               acknowledged, error_code, occurred_at, created_at
        FROM sms_messaging_events
        ORDER BY id DESC
        LIMIT ?
        """,
        (max(1, min(int(limit), 100)),),
    ).fetchall()
    return {
        "status": "sms_events_listed",
        "items": [dict(row) for row in rows],
        "content_included": False,
        "phone_numbers_included": False,
        "boundaries": _sms_boundaries(sms_private_config()),
    }


def send_sms(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    transport: SmsTransport | None = None,
) -> dict[str, Any]:
    config = sms_private_config()
    text = truncate(str(payload.get("text") or ""), MAX_SMS_BODY_CHARS)
    if not text.strip():
        raise ValueError("SMS text is required")
    purpose = str(payload.get("purpose") or "initiative").strip().lower()
    if purpose not in SMS_PURPOSES:
        raise ValueError("SMS purpose must be reply or initiative")
    _assert_send_authority(conn, config, purpose)
    if purpose == "initiative" and not str(payload.get("reason") or "").strip():
        raise ValueError("A bounded Tendril reason is required for initiative")
    active_transport = transport or _build_transport(config)
    try:
        delivered = active_transport.send(
            from_number=config["from_number"],
            to_number=config["contact_number"],
            body=text,
        )
    except SmsTransportError as exc:
        _record_event(
            conn,
            provider=config["provider"],
            provider_message_id=None,
            direction="outbound",
            purpose=purpose,
            delivery_status="failed",
            text=text,
            chat_session_id=_optional_int(payload.get("chat_session_id")),
            chat_message_id=_optional_int(payload.get("chat_message_id")),
            error_code=type(exc).__name__,
            occurred_at=_utc_now(),
        )
        raise
    provider_sid = str(delivered.get("sid") or "")
    event_id = _record_event(
        conn,
        provider=config["provider"],
        provider_message_id=provider_sid or None,
        direction="outbound",
        purpose=purpose,
        delivery_status=str(delivered.get("status") or "queued"),
        text=text,
        chat_session_id=_optional_int(payload.get("chat_session_id")),
        chat_message_id=_optional_int(payload.get("chat_message_id")),
        occurred_at=str(delivered.get("date_sent") or _utc_now()),
    )
    _increment_unacknowledged(conn)
    return {
        "status": "sms_queued",
        "event_id": event_id,
        "provider_message_id": provider_sid,
        "delivery_status": str(delivered.get("status") or "queued"),
        "purpose": purpose,
        "contact_id": SMS_CONTACT_ID,
        "character_count": len(text),
        "delegated_message_authority": True,
        "per_message_approval_required": False,
        "autonomous_action_allowed": False,
        "boundaries": _sms_boundaries(config),
    }


def initiate_sms(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    transport: SmsTransport | None = None,
) -> dict[str, Any]:
    return send_sms(conn, {**payload, "purpose": "initiative"}, transport=transport)


def poll_sms(
    conn: sqlite3.Connection,
    *,
    transport: SmsTransport | None = None,
    inbound_messages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    config = sms_private_config()
    if not config["enabled"]:
        return {"status": "sms_poll_disabled", "processed": 0, "replied": 0, "skipped": 0}
    if not config["delegated_message_authority"]:
        return {"status": "sms_poll_authority_revoked", "processed": 0, "replied": 0, "skipped": 0}
    active_transport = transport or _build_transport(config)
    try:
        incoming = inbound_messages if inbound_messages is not None else active_transport.list_inbound(
            to_number=config["from_number"],
            from_number=config["contact_number"],
            limit=20,
        )
    except SmsTransportError:
        _update_poll_state(conn, "provider_error")
        raise
    processed = 0
    replied = 0
    skipped = 0
    held = 0
    for message in incoming:
        sid = str(message.get("sid") or "").strip()
        text = truncate(str(message.get("body") or ""), MAX_SMS_BODY_CHARS)
        if not sid or not text.strip() or _event_exists(conn, sid):
            skipped += 1
            continue
        if not _message_matches_pair(message, config):
            skipped += 1
            continue
        _acknowledge_outbound(conn)
        inbound_event_id = _record_event(
            conn,
            provider=config["provider"],
            provider_message_id=sid,
            direction="inbound",
            purpose="reply",
            delivery_status=str(message.get("status") or "received"),
            text=text,
            occurred_at=str(message.get("date_sent") or _utc_now()),
        )
        processed += 1
        if text.strip().lower() in STOP_KEYWORDS:
            disable_sms(reason="sms_stop_received")
            _update_poll_state(conn, "authority_revoked_by_stop")
            return {
                "status": "sms_poll_stop_received",
                "processed": processed,
                "replied": replied,
                "skipped": skipped,
                "held": held,
                "inbound_event_id": inbound_event_id,
                "delegated_message_authority": False,
            }
        if config["mode"] == "offline" or not config["reply_allowed"]:
            held += 1
            continue
        if not activation_is_active(conn):
            _set_event_status(conn, inbound_event_id, "held_activation_inactive")
            held += 1
            continue
        session_id = _sms_session_id(conn)
        chat_result = mobile_send_chat(conn, {"text": text, "session_id": session_id})
        candidate = truncate(str(chat_result.get("candidate_text") or ""), MAX_SMS_BODY_CHARS)
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
        send_sms(
            conn,
            {
                "text": candidate,
                "purpose": "reply",
                "chat_session_id": chat_result.get("session_id"),
                "chat_message_id": chat_result.get("assistant_message_id"),
            },
            transport=active_transport,
        )
        replied += 1
    _update_poll_state(conn, "complete")
    return {
        "status": "sms_poll_complete",
        "processed": processed,
        "replied": replied,
        "skipped": skipped,
        "held": held,
        "delegated_message_authority": config["delegated_message_authority"],
        "autonomous_action_allowed": False,
        "boundaries": _sms_boundaries(config),
    }


def _normalize_config(data: dict[str, Any]) -> dict[str, Any]:
    mode = str(data.get("mode") or "offline").lower()
    if mode not in SMS_MODES:
        mode = "offline"
    interval = int(data.get("poll_interval_seconds") or DEFAULT_POLL_INTERVAL_SECONDS)
    return {
        "enabled": bool(data.get("enabled")),
        "provider": SMS_PROVIDER,
        "contact_id": SMS_CONTACT_ID,
        "contact_number": str(data.get("contact_number") or ""),
        "from_number": str(data.get("from_number") or ""),
        "mode": mode,
        "delegated_message_authority": bool(data.get("delegated_message_authority")),
        "reply_allowed": bool(data.get("reply_allowed")),
        "initiative_allowed": bool(data.get("initiative_allowed")),
        "max_unacknowledged": max(1, min(int(data.get("max_unacknowledged") or DEFAULT_MAX_UNACKNOWLEDGED), 3)),
        "poll_interval_seconds": max(10, min(interval, 300)),
    }


def _write_config(config: dict[str, Any]) -> None:
    path = sms_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_normalize_config(config), indent=2), encoding="utf-8")


def _credential_state() -> dict[str, Any]:
    variables = ("TWILIO_ACCOUNT_SID", "TWILIO_API_KEY_SID", "TWILIO_API_KEY_SECRET")
    missing = [name for name in variables if not os.environ.get(name, "").strip()]
    return {
        "ready": not missing,
        "missing_environment_variables": missing,
        "secret_values_exposed": False,
        "auth_method": "revocable_api_key",
    }


def _is_ready(config: dict[str, Any], credential_state: dict[str, Any]) -> bool:
    return bool(
        config["enabled"]
        and config["delegated_message_authority"]
        and config["contact_number"]
        and config["from_number"]
        and credential_state["ready"]
    )


def _sms_boundaries(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "scope": "paired_sms_with_aleks_only",
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
    }


def _build_transport(config: dict[str, Any]) -> SmsTransport:
    if config.get("provider") != SMS_PROVIDER:
        raise SmsConfigurationError("Configured SMS provider is unsupported")
    return TwilioSmsTransport()


def _assert_send_authority(conn: sqlite3.Connection, config: dict[str, Any], purpose: str) -> None:
    if not config["enabled"] or not config["delegated_message_authority"]:
        raise SmsAuthorityError("SMS delegated authority is not enabled")
    if config["mode"] == "offline":
        raise SmsAuthorityError("SMS mode is offline")
    if purpose == "initiative" and (config["mode"] != "available" or not config["initiative_allowed"]):
        raise SmsAuthorityError("SMS initiative is unavailable in the current mode")
    if purpose == "reply" and not config["reply_allowed"]:
        raise SmsAuthorityError("SMS replies are not allowed")
    unacknowledged = _unacknowledged_count(conn)
    if unacknowledged >= int(config["max_unacknowledged"]):
        raise SmsAuthorityError("SMS paused at the unacknowledged-message limit")


def _record_event(
    conn: sqlite3.Connection,
    *,
    provider: str,
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
        INSERT INTO sms_messaging_events
        (provider, provider_message_id, direction, contact_id, purpose, delivery_status,
         chat_session_id, chat_message_id, body_sha256, character_count, acknowledged,
         error_code, occurred_at, provenance_boundary, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
        """,
        (
            provider,
            provider_message_id,
            direction,
            SMS_CONTACT_ID,
            purpose,
            delivery_status,
            chat_session_id,
            chat_message_id,
            hashlib.sha256(text.encode("utf-8")).hexdigest(),
            len(text),
            error_code,
            occurred_at,
            "tendril_sms_paired_contact_no_memory_no_general_autonomy",
            json.dumps({"content_stored": False, "phone_numbers_stored": False}),
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def _event_exists(conn: sqlite3.Connection, provider_message_id: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sms_messaging_events WHERE provider_message_id = ?",
        (provider_message_id,),
    ).fetchone()
    return row is not None


def _link_inbound_event(conn: sqlite3.Connection, event_id: int, session_id: int | None, message_id: int | None) -> None:
    conn.execute(
        "UPDATE sms_messaging_events SET chat_session_id = ?, chat_message_id = ? WHERE id = ?",
        (session_id, message_id, event_id),
    )
    conn.execute(
        """
        INSERT INTO sms_messaging_state(contact_id, chat_session_id, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(contact_id) DO UPDATE SET chat_session_id = excluded.chat_session_id, updated_at = CURRENT_TIMESTAMP
        """,
        (SMS_CONTACT_ID, session_id),
    )
    conn.commit()


def _set_event_status(conn: sqlite3.Connection, event_id: int, status: str) -> None:
    conn.execute("UPDATE sms_messaging_events SET delivery_status = ? WHERE id = ?", (status, event_id))
    conn.commit()


def _sms_session_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute(
        "SELECT chat_session_id FROM sms_messaging_state WHERE contact_id = ?",
        (SMS_CONTACT_ID,),
    ).fetchone()
    return _optional_int(row["chat_session_id"] if row else None)


def _unacknowledged_count(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT unacknowledged_outbound FROM sms_messaging_state WHERE contact_id = ?",
        (SMS_CONTACT_ID,),
    ).fetchone()
    return int(row["unacknowledged_outbound"] or 0) if row else 0


def _increment_unacknowledged(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT INTO sms_messaging_state(contact_id, unacknowledged_outbound, last_outbound_at, updated_at)
        VALUES (?, 1, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(contact_id) DO UPDATE SET
          unacknowledged_outbound = unacknowledged_outbound + 1,
          last_outbound_at = excluded.last_outbound_at,
          updated_at = CURRENT_TIMESTAMP
        """,
        (SMS_CONTACT_ID, _utc_now()),
    )
    conn.commit()


def _acknowledge_outbound(conn: sqlite3.Connection) -> None:
    conn.execute(
        "UPDATE sms_messaging_events SET acknowledged = 1 WHERE direction = 'outbound' AND acknowledged = 0"
    )
    conn.execute(
        """
        INSERT INTO sms_messaging_state(contact_id, unacknowledged_outbound, last_inbound_at, updated_at)
        VALUES (?, 0, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(contact_id) DO UPDATE SET
          unacknowledged_outbound = 0,
          last_inbound_at = excluded.last_inbound_at,
          updated_at = CURRENT_TIMESTAMP
        """,
        (SMS_CONTACT_ID, _utc_now()),
    )
    conn.commit()


def _reset_delivery_window(conn: sqlite3.Connection) -> None:
    conn.execute(
        "UPDATE sms_messaging_events SET acknowledged = 1 WHERE direction = 'outbound' AND acknowledged = 0"
    )
    conn.execute(
        """
        INSERT INTO sms_messaging_state(contact_id, unacknowledged_outbound, updated_at)
        VALUES (?, 0, CURRENT_TIMESTAMP)
        ON CONFLICT(contact_id) DO UPDATE SET
          unacknowledged_outbound = 0,
          updated_at = CURRENT_TIMESTAMP
        """,
        (SMS_CONTACT_ID,),
    )
    conn.commit()


def _update_poll_state(conn: sqlite3.Connection, status: str) -> None:
    conn.execute(
        """
        INSERT INTO sms_messaging_state(contact_id, last_poll_at, last_poll_status, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(contact_id) DO UPDATE SET
          last_poll_at = excluded.last_poll_at,
          last_poll_status = excluded.last_poll_status,
          updated_at = CURRENT_TIMESTAMP
        """,
        (SMS_CONTACT_ID, _utc_now(), status),
    )
    conn.commit()


def _message_matches_pair(message: dict[str, Any], config: dict[str, Any]) -> bool:
    return (
        str(message.get("from") or "") == config["contact_number"]
        and str(message.get("to") or "") == config["from_number"]
        and str(message.get("direction") or "") == "inbound"
    )


def _normalize_twilio_message(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "sid": str(payload.get("sid") or ""),
        "direction": str(payload.get("direction") or ""),
        "from": str(payload.get("from") or ""),
        "to": str(payload.get("to") or ""),
        "body": str(payload.get("body") or ""),
        "status": str(payload.get("status") or ""),
        "date_sent": str(payload.get("date_sent") or payload.get("date_created") or ""),
        "error_code": str(payload.get("error_code") or ""),
    }


def _message_timestamp(message: dict[str, Any]) -> float:
    raw = str(message.get("date_sent") or "").strip()
    if not raw:
        return 0.0
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except ValueError:
        try:
            return parsedate_to_datetime(raw).timestamp()
        except (TypeError, ValueError, OverflowError):
            return 0.0


def _e164(value: str, label: str) -> str:
    normalized = value.strip()
    if not E164_PATTERN.fullmatch(normalized):
        raise ValueError(f"{label} must use E.164 format, such as +15551234567")
    return normalized


def _mask_number(value: str) -> str:
    if not value:
        return ""
    return f"{value[:2]}{'*' * max(0, len(value) - 6)}{value[-4:]}"


def _optional_int(value: Any) -> int | None:
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError):
        return None
    return parsed or None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
