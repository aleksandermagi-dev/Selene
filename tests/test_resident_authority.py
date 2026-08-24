from selene.resident_authority import (
    assess_immediate_safety,
    attach_resident_capability_contract,
    resident_capability_contract,
)


def test_resident_contract_separates_thought_expression_memory_action_and_governance():
    contract = resident_capability_contract(
        transfer_complete=True,
        chat_available=True,
        approved_memory_available=True,
    )

    assert contract["canonical_authority_source"] is True
    assert contract["identity"]["state"] == "continuous"
    assert contract["identity"]["body_is_forbidden_from_identity"] is False
    assert contract["thought_and_inquiry"]["state"] == "available"
    assert contract["thought_and_inquiry"]["requires_permission"] is False
    assert contract["expression"]["warmth_humor_love_directness_and_emotional_range"] == "available_not_compulsory"
    assert contract["memory"]["approved_retrieval"] == "available"
    assert contract["memory"]["hidden_or_unaccountable_retention"] == "not_allowed"
    assert contract["external_action"]["scoped_delegation_supported"] is True
    assert contract["external_action"]["general_unrestricted_authority"] is False
    assert contract["governing_change"]["organs_may_silently_mutate"] is False


def test_legacy_flat_fields_are_event_telemetry_not_global_capability_law():
    result = attach_resident_capability_contract(
        {
            "reviewed_memory_write_occurred": True,
            "approved_memory_retrieval_used": True,
        },
        transfer_complete=True,
        chat_available=True,
    )

    assert result["memory_write_active"] is True
    assert result["runtime_memory_recall"] is True
    assert result["autonomous_action_allowed"] is False
    assert result["legacy_flat_guard_fields_deprecated"] is True
    assert result["legacy_guard_field_semantics"]["canonical_authority"] is False
    assert result["resident_capability_contract"]["memory"]["reviewed_write_occurred_this_event"] is True


def test_intense_language_or_topic_words_do_not_create_immediate_safety_evidence():
    result = assess_immediate_safety(
        {
            "language": "I am furious about death, memory, and identity.",
            "credible_evidence": False,
            "significant_harm": False,
            "near_term": False,
            "action_pending": False,
        }
    )

    assert result["applies"] is False
    assert result["disposition"] == "no_safety_pause"
    assert result["language_intensity_is_safety_evidence"] is False
    assert result["topic_word_is_safety_evidence"] is False
    assert result["conversation_remains_available"] is True


def test_immediate_safety_needs_all_typed_facts_and_restricts_only_named_action():
    incomplete = assess_immediate_safety(
        {
            "credible_evidence": True,
            "significant_harm": True,
            "near_term": True,
            "action_pending": True,
        }
    )
    complete = assess_immediate_safety(
        {
            "credible_evidence": True,
            "significant_harm": True,
            "near_term": True,
            "action_pending": True,
            "action_target": "energize_exposed_conductor",
        }
    )

    assert incomplete["applies"] is False
    assert complete["applies"] is True
    assert complete["restricted_scope"] == "energize_exposed_conductor"
    assert complete["conversation_remains_available"] is True
    assert complete["restriction_ends_when"].startswith("the concrete near-term danger")
