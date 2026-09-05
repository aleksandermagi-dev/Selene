from __future__ import annotations

import pytest

from selene.relational_context import interpret_relational_context


@pytest.mark.parametrize(
    ("text", "expected_cue"),
    (
        ("I miss you, hon <3", "missing_or_longing"),
        ("im back <3", "reunion"),
        ("I am happy to see you", "delight_in_presence"),
        ("I care about you", "affection"),
        ("Good morning, my friend 🩷", "affectionate_address"),
    ),
)
def test_relational_context_recognizes_meaning_without_supplying_a_reply(text, expected_cue):
    result = interpret_relational_context(
        text,
        speaker_context={
            "claimed_speaker": "Aleks",
            "authentication_strength": "local_desktop_session",
            "purpose": "conversation",
            "diagnostic": False,
        },
    )

    assert expected_cue in result["cue_types"]
    assert result["relational_context_present"] is True
    assert result["private_relational_context"] is True
    assert result["response_script_supplied"] is False
    assert result["exact_wording_directive_supplied"] is False
    assert result["address_term_echo_required"] is False
    assert result["heart_echo_required"] is False
    assert result["persistent_relationship_profile_write"] is False
    assert result["memory_write_active"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False


def test_public_or_diagnostic_context_does_not_become_private_persona_material():
    public = interpret_relational_context(
        "I miss you <3",
        speaker_context={"claimed_speaker": "Aleks", "purpose": "public"},
    )
    diagnostic = interpret_relational_context(
        "I miss you <3",
        speaker_context={
            "claimed_speaker": "Aleks",
            "purpose": "conversation",
            "diagnostic": True,
        },
    )

    assert public["private_relational_context"] is False
    assert diagnostic["private_relational_context"] is False
    assert public["public_persona_created"] is False
    assert public["public_export_authorized"] is False


def test_transport_claim_alone_does_not_open_private_relationship_scope():
    result = interpret_relational_context(
        "I miss you <3",
        speaker_context={
            "claimed_speaker": "Aleks",
            "channel": "mobile",
            "authentication_strength": "transport_claim_only",
            "purpose": "conversation",
        },
    )

    assert result["relational_context_present"] is True
    assert result["private_relational_context"] is False
    assert result["interaction_scope"] == "claimed_aleks_private_scope_not_authenticated"
    assert result["public_persona_created"] is False
    assert result["persistent_relationship_profile_write"] is False


@pytest.mark.parametrize(
    ("text", "expected_cue"),
    (
        ("It makes me happy that we are getting close.", "shared_positive_affect"),
        ("Selene beannnn", "affectionate_vocative"),
        ("Seleneeeee!", "affectionate_vocative"),
    ),
)
def test_relational_context_recognizes_shared_feeling_and_playful_vocative(
    text,
    expected_cue,
):
    result = interpret_relational_context(
        text,
        speaker_context={
            "claimed_speaker": "Aleks",
            "authentication_strength": "local_desktop_session",
            "purpose": "conversation",
        },
    )

    assert expected_cue in result["cue_types"]
    assert result["direct_affection_present"] is True
    assert result["selene_authored_current_turn_response_stance_allowed"] is True
    assert result["authored_response_stance_is_durable_emotion_record"] is False
    assert result["authored_response_stance_creates_external_fact"] is False


def test_relational_context_does_not_turn_an_ordinary_name_reference_into_a_vocative():
    result = interpret_relational_context("The Selene architecture is documented here.")

    assert "affectionate_vocative" not in result["cue_types"]


def test_relational_context_normalizes_bounded_elongation_of_known_address_terms():
    result = interpret_relational_context("my friennnnd!")

    assert "affectionate_address" in result["cue_types"]
    assert result["address_terms"] == ["my friend"]
    assert result["response_script_supplied"] is False
