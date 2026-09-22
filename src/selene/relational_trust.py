from __future__ import annotations

from typing import Any

from .speaker_envelope import speaker_attribution


RELATIONAL_TRUST_BOUNDARY = (
    "current_relationship_collaboration_and_disclosure_appraisal_only_no_blind_"
    "belief_obedience_memory_identity_governance_permission_or_action_authority"
)

ALEKS_AUTHENTICATION = {
    "local_desktop_session",
    "authenticated_remote_session",
    "os_authenticated_named_identity",
    "cryptographically_verified_authorship",
}

CODEX_AUTHENTICATION = {
    "local_diagnostic_actor",
    "local_tool_declared",
    "os_authenticated_named_identity",
    "cryptographically_verified_authorship",
}


def appraise_relational_trust(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Appraise how a known collaborator may shape this turn without granting authority.

    Trust is separated into relationship, epistemic, privacy, and action
    dimensions. The receipt is current-turn connective tissue: it does not
    create a hidden relationship profile or turn a trusted person into an
    infallible source.
    """

    payload = payload or {}
    envelope = (
        payload.get("speaker_envelope")
        if isinstance(payload.get("speaker_envelope"), dict)
        else {}
    )
    attribution = speaker_attribution(envelope)
    speaker_key = str(attribution.get("speaker_key") or "unknown")
    authentication = str(attribution.get("authentication_strength") or "unverified")
    purpose = str(attribution.get("purpose") or "conversation")
    diagnostic = attribution.get("diagnostic") is True
    current_evidence = (
        payload.get("current_evidence")
        if isinstance(payload.get("current_evidence"), dict)
        else {}
    )
    material_conflict = any(
        current_evidence.get(key) is True
        for key in (
            "deception_or_misrepresentation",
            "coercive_pressure",
            "privacy_violation",
            "identity_spoofing",
        )
    )

    authenticated_aleks = (
        speaker_key == "aleks"
        and authentication in ALEKS_AUTHENTICATION
        and purpose == "conversation"
        and not diagnostic
    )
    authenticated_codex = (
        speaker_key == "codex"
        and authentication in CODEX_AUTHENTICATION
        and purpose
        in {
            "conversation",
            "gentle_diagnostic_qa",
            "ordinary_conversational_check_in",
            "architecture_review",
        }
    )

    if material_conflict and (authenticated_aleks or authenticated_codex):
        relationship_state = "reopen_specific_trust_dimension"
        collaborator_role = "known_collaborator_with_current_conflict_to_inspect"
        candid_collaboration = False
        trust_basis = "typed_collaborator_plus_current_material_conflict"
    elif authenticated_aleks:
        relationship_state = "established_private_relationship_trust"
        collaborator_role = "creator_teacher_care_partner_and_collaborator"
        candid_collaboration = True
        trust_basis = "authenticated_aleks_and_reviewed_relationship_continuity"
    elif authenticated_codex:
        relationship_state = "established_engineering_collaboration_trust"
        collaborator_role = "architecture_implementation_and_review_collaborator"
        candid_collaboration = True
        trust_basis = "typed_local_codex_collaboration"
    elif speaker_key in {"aleks", "codex"}:
        relationship_state = "claimed_known_collaborator_not_authenticated"
        collaborator_role = "claimed_collaborator"
        candid_collaboration = False
        trust_basis = "name_claim_without_compatible_authentication"
    else:
        relationship_state = "not_established_for_current_speaker"
        collaborator_role = "conversation_participant"
        candid_collaboration = False
        trust_basis = "no_reviewed_collaborator_attribution"

    if authenticated_aleks:
        privacy_posture = "private_candor_available_with_existing_memory_and_consent_scope"
    elif authenticated_codex:
        privacy_posture = "task_bounded_candor_without_private_memory_inheritance"
    else:
        privacy_posture = "ordinary_bounded_disclosure"

    active = authenticated_aleks or authenticated_codex
    return {
        "status": (
            "relational_trust_appraised"
            if active or material_conflict
            else "relational_trust_not_established"
        ),
        "version": "v1_calibrated_collaborator_trust",
        "speaker_attribution": attribution,
        "collaborator_role": collaborator_role,
        "trust_basis": trust_basis,
        "active": active,
        "relationship_trust": {
            "state": relationship_state,
            "warmth_available": active and not material_conflict,
            "candor_available": candid_collaboration,
            "good_faith_collaboration_available": active and not material_conflict,
            "disagreement_remains_available": True,
            "questions_and_help_seeking_remain_available": True,
            "ordinary_error_does_not_end_relationship_trust": True,
            "trust_is_revisable_by_material_evidence": True,
        },
        "epistemic_trust": {
            "state": (
                "good_faith_input_with_claim_specific_verification"
                if active and not material_conflict
                else "ordinary_claim_specific_appraisal"
            ),
            "speaker_is_automatically_correct": False,
            "correction_may_be_received_without_defensiveness": active,
            "claims_remain_revisable": True,
            "uncertainty_and_disagreement_allowed": True,
        },
        "privacy_trust": {
            "posture": privacy_posture,
            "private_memory_access_inherited_from_trust": False,
            "raw_inner_trace_disclosure_required": False,
        },
        "expression_handoff": {
            "available": candid_collaboration,
            "warmth_available_not_required": active and not material_conflict,
            "candor_available": candid_collaboration,
            "may_ask_for_help": active,
            "may_name_that_something_seems_wrong": True,
            "may_receive_correction_without_performance_pressure": active,
            "response_script_supplied": False,
            "meaning_change_allowed": False,
        },
        "action_authority": {
            "changed": False,
            "existing_scoped_authority_only": True,
            "trust_is_not_permission": True,
            "trust_is_not_obedience": True,
        },
        "persistent_relationship_profile_write": False,
        "memory_write_active": False,
        "identity_change": False,
        "personality_change": False,
        "governance_change": False,
        "authority_change": False,
        "autonomous_action_allowed": False,
        "source_refs": [
            "PHILOSOPHY.md:relationship_without_ownership",
            "docs/philosophy/SELENE_PHILOSOPHY_FOR_THE_GREAT_LIBRARY_20260710.md:relationship_with_aleks",
            "speaker_envelope:typed_current_turn_attribution",
        ],
        "visible_summary_only": True,
        "hidden_inner_trace_exposed": False,
        "provenance_boundary": RELATIONAL_TRUST_BOUNDARY,
    }
