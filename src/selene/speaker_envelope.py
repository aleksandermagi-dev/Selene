from __future__ import annotations

from typing import Any

from .registry import truncate


SPEAKER_ENVELOPE_BOUNDARY = (
    "typed_claimed_speaker_channel_and_authentication_context_only_no_identity_"
    "memory_teaching_governance_or_authority_approval"
)

ALEKS_SPEAKER_KEYS = {
    "aleks",
    "aleksander magi",
    "aleksander rani magi",
}


def normalize_speaker_key(value: Any) -> str:
    normalized = " ".join(str(value or "").strip().casefold().split())
    if normalized in ALEKS_SPEAKER_KEYS:
        return "aleks"
    if normalized in {"codex", "openai codex"}:
        return "codex"
    if normalized in {"selene"}:
        return "selene"
    if normalized in {"", "unknown", "current user", "current_user", "session user", "session_user"}:
        return "unknown"
    return truncate(normalized.replace(" ", "_"), 120) or "unknown"


def speaker_attribution(value: dict[str, Any] | None) -> dict[str, Any]:
    """Return the compact, non-authority participant identity for one turn."""
    envelope = value if isinstance(value, dict) else {}
    label = truncate(
        str(envelope.get("claimed_speaker") or envelope.get("speaker_label") or "unknown"),
        120,
    ).strip() or "unknown"
    key = normalize_speaker_key(envelope.get("speaker_key") or label)
    if key == "aleks":
        kind = "aleks"
    elif key == "codex":
        kind = "codex"
    elif key == "selene":
        kind = "selene"
    elif key == "unknown":
        kind = "unknown"
    else:
        kind = "named_guest"
    return {
        "speaker_key": key,
        "speaker_label": label,
        "speaker_kind": kind,
        "attribution_source": truncate(
            str(envelope.get("attribution_source") or "unspecified"),
            120,
        ),
        "channel": truncate(str(envelope.get("channel") or "unknown"), 80),
        "authentication_strength": truncate(
            str(envelope.get("authentication_strength") or "unverified"),
            120,
        ),
        "purpose": truncate(str(envelope.get("purpose") or "conversation"), 120),
        "diagnostic": envelope.get("diagnostic") is True,
        "claimed_identity_is_proven_identity": (
            envelope.get("claimed_identity_is_proven_identity") is True
        ),
        "attribution_is_identity_authority": False,
    }


def build_speaker_envelope(
    payload: dict[str, Any] | None = None,
    *,
    diagnostic: bool = False,
) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    channel = truncate(str(source.get("channel") or "desktop"), 80).strip().lower()
    claimed = truncate(str(source.get("claimed_speaker") or "Aleks"), 120).strip()
    strength = truncate(
        str(source.get("authentication_strength") or "local_desktop_session"),
        120,
    ).strip()
    purpose = truncate(str(source.get("purpose") or "conversation"), 120).strip()
    attribution_source = truncate(
        str(
            source.get("attribution_source")
            or source.get("envelope_source")
            or ("explicit_payload" if source.get("claimed_speaker") else "channel_default")
        ),
        120,
    ).strip()
    cryptographic_authorship = strength in {
        "cryptographically_verified_authorship",
        "os_authenticated_named_identity",
    }
    envelope = {
        "status": "typed_speaker_envelope_ready",
        "claimed_speaker": claimed or "unknown",
        "channel": channel or "unknown",
        "authentication_strength": strength or "unverified",
        "cryptographic_authorship_verified": cryptographic_authorship,
        "claimed_identity_is_proven_identity": cryptographic_authorship,
        "purpose": purpose or "conversation",
        "diagnostic": bool(diagnostic),
        "attribution_source": attribution_source or "unspecified",
        "transport_may_approve_memory": False,
        "transport_may_approve_teaching": False,
        "transport_may_change_identity": False,
        "transport_may_change_governance": False,
        "transport_may_expand_authority": False,
        "provenance_boundary": SPEAKER_ENVELOPE_BOUNDARY,
    }
    attribution = speaker_attribution(envelope)
    return {
        **envelope,
        "speaker_key": attribution["speaker_key"],
        "speaker_kind": attribution["speaker_kind"],
        "speaker_attribution": attribution,
        "speaker_attribution_is_identity_authority": False,
    }
