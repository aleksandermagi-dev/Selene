from selene.chat_persistence import continuity_projection
from selene.speaker_envelope import (
    build_speaker_envelope,
    normalize_speaker_key,
    speaker_attribution,
)


def test_transport_claim_is_not_silently_promoted_to_proven_identity_or_authority():
    envelope = build_speaker_envelope(
        {
            "claimed_speaker": "Aleks",
            "channel": "paired_email_gateway",
            "authentication_strength": "transport_filtered_not_cryptographic_authorship",
            "purpose": "conversation",
        }
    )

    assert envelope["claimed_speaker"] == "Aleks"
    assert envelope["cryptographic_authorship_verified"] is False
    assert envelope["claimed_identity_is_proven_identity"] is False
    assert envelope["transport_may_approve_memory"] is False
    assert envelope["transport_may_approve_teaching"] is False
    assert envelope["transport_may_change_identity"] is False
    assert envelope["transport_may_change_governance"] is False
    assert envelope["transport_may_expand_authority"] is False


def test_named_speakers_receive_stable_non_authority_attribution_keys():
    codex = build_speaker_envelope(
        {
            "claimed_speaker": "OpenAI Codex",
            "channel": "local_codex_check_in",
            "authentication_strength": "local_tool_declared",
            "purpose": "ordinary_conversational_check_in",
            "attribution_source": "explicit_payload",
        }
    )

    assert normalize_speaker_key("Aleksander Rani Magi") == "aleks"
    assert codex["speaker_key"] == "codex"
    assert codex["speaker_kind"] == "codex"
    assert codex["speaker_attribution"]["speaker_label"] == "OpenAI Codex"
    assert codex["speaker_attribution_is_identity_authority"] is False
    assert codex["transport_may_approve_memory"] is False
    assert codex["transport_may_approve_teaching"] is False


def test_continuity_projection_preserves_compact_speaker_provenance():
    envelope = build_speaker_envelope(
        {
            "claimed_speaker": "Codex",
            "channel": "local_codex_check_in",
            "authentication_strength": "local_tool_declared",
            "purpose": "ordinary_conversational_check_in",
            "attribution_source": "explicit_payload",
        }
    )
    projection = continuity_projection(
        {"speaker_envelope": envelope},
        trace_reference={"message_id": 1, "session_id": 1},
    )

    assert projection["speaker_envelope_present"] is True
    assert projection["speaker_attribution"] == speaker_attribution(envelope)
    assert projection["speaker_attribution"]["speaker_key"] == "codex"
    assert projection["memory_write_active"] is False
    assert projection["identity_change"] is False
