from selene.speaker_envelope import build_speaker_envelope


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
