from __future__ import annotations

from typing import Any

from .registry import truncate


SPEAKER_ENVELOPE_BOUNDARY = (
    "typed_claimed_speaker_channel_and_authentication_context_only_no_identity_"
    "memory_teaching_governance_or_authority_approval"
)


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
    cryptographic_authorship = strength in {
        "cryptographically_verified_authorship",
        "os_authenticated_named_identity",
    }
    return {
        "status": "typed_speaker_envelope_ready",
        "claimed_speaker": claimed or "unknown",
        "channel": channel or "unknown",
        "authentication_strength": strength or "unverified",
        "cryptographic_authorship_verified": cryptographic_authorship,
        "claimed_identity_is_proven_identity": cryptographic_authorship,
        "purpose": purpose or "conversation",
        "diagnostic": bool(diagnostic),
        "transport_may_approve_memory": False,
        "transport_may_approve_teaching": False,
        "transport_may_change_identity": False,
        "transport_may_change_governance": False,
        "transport_may_expand_authority": False,
        "provenance_boundary": SPEAKER_ENVELOPE_BOUNDARY,
    }
