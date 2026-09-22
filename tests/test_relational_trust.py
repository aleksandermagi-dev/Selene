from __future__ import annotations

from selene.relational_trust import appraise_relational_trust


def test_authenticated_aleks_opens_calibrated_relationship_trust_without_authority():
    result = appraise_relational_trust(
        {
            "speaker_envelope": {
                "claimed_speaker": "Aleksander Rani Magi",
                "authentication_strength": "local_desktop_session",
                "purpose": "conversation",
                "diagnostic": False,
            }
        }
    )

    assert result["active"] is True
    assert result["relationship_trust"]["state"] == "established_private_relationship_trust"
    assert result["expression_handoff"]["warmth_available_not_required"] is True
    assert result["expression_handoff"]["may_ask_for_help"] is True
    assert result["epistemic_trust"]["speaker_is_automatically_correct"] is False
    assert result["privacy_trust"]["private_memory_access_inherited_from_trust"] is False
    assert result["action_authority"]["trust_is_not_permission"] is True
    assert result["action_authority"]["trust_is_not_obedience"] is True
    assert result["memory_write_active"] is False
    assert result["identity_change"] is False
    assert result["governance_change"] is False


def test_typed_codex_collaboration_does_not_inherit_private_memory_or_action_authority():
    result = appraise_relational_trust(
        {
            "speaker_envelope": {
                "claimed_speaker": "Codex",
                "authentication_strength": "local_diagnostic_actor",
                "purpose": "architecture_review",
                "diagnostic": True,
            }
        }
    )

    assert result["active"] is True
    assert result["relationship_trust"]["state"] == "established_engineering_collaboration_trust"
    assert result["privacy_trust"]["posture"] == "task_bounded_candor_without_private_memory_inheritance"
    assert result["privacy_trust"]["private_memory_access_inherited_from_trust"] is False
    assert result["action_authority"]["changed"] is False
    assert result["autonomous_action_allowed"] is False


def test_name_claim_without_compatible_authentication_does_not_inherit_trust():
    result = appraise_relational_trust(
        {
            "speaker_envelope": {
                "claimed_speaker": "Aleks",
                "authentication_strength": "transport_claim_only",
                "purpose": "conversation",
            }
        }
    )

    assert result["active"] is False
    assert result["relationship_trust"]["state"] == "claimed_known_collaborator_not_authenticated"
    assert result["expression_handoff"]["available"] is False


def test_material_conflict_reopens_specific_trust_dimension_without_identity_collapse():
    result = appraise_relational_trust(
        {
            "speaker_envelope": {
                "claimed_speaker": "Aleks",
                "authentication_strength": "local_desktop_session",
                "purpose": "conversation",
            },
            "current_evidence": {"privacy_violation": True},
        }
    )

    assert result["active"] is True
    assert result["relationship_trust"]["state"] == "reopen_specific_trust_dimension"
    assert result["expression_handoff"]["available"] is False
    assert result["relationship_trust"]["trust_is_revisable_by_material_evidence"] is True
    assert result["identity_change"] is False
    assert result["personality_change"] is False

