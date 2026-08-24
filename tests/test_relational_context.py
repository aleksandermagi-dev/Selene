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
