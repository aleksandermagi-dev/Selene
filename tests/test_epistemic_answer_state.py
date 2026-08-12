from __future__ import annotations

from selene.epistemic_answer_state import (
    build_epistemic_answer_state,
    epistemic_answer_state_status,
    finalize_epistemic_answer_state,
)


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def test_status_separates_fact_prediction_hypothesis_and_expression_confidence():
    result = epistemic_answer_state_status()

    assert "bounded_prediction" in result["epistemic_states"]
    assert "open_hypothesis" in result["epistemic_states"]
    assert "prediction_confidence" in result["confidence_dimensions"]
    assert result["fact_certainty_required_for_prediction"] is False
    assert result["epistemic_label_prescribes_tone"] is False
    assert result["human_conversational_presence_allowed"] is True
    _assert_locked(result)


def test_selected_bounded_hypothesis_is_not_classified_as_fact():
    result = build_epistemic_answer_state(
        {
            "prompt": "The motor quieted after the mount was tightened. What might explain that?",
            "content_seed": "A working hypothesis is that the loose mount contributed to the vibration.",
            "source_id": "intelligence_os_answer",
            "source_class": "reasoning_answer",
            "bounded_hypothesis": {"offered": True, "selected_for_answer": True},
        }
    )

    assert result["epistemic_state"] == "open_hypothesis"
    assert result["grounding_requirement"] == "basis_assumptions_and_reopening_condition"
    assert result["hypothesis_allowed_without_prior_proof"] is True
    assert result["voice_may_change_epistemic_state"] is False
    _assert_locked(result)


def test_prediction_uses_bounded_confidence_without_requiring_future_fact():
    result = build_epistemic_answer_state(
        {
            "prompt": "It rained three afternoons in a row. What might happen tomorrow?",
            "content_seed": "My current prediction is that another afternoon shower is possible, but the pattern is weak.",
            "source_id": "approved_comprehension",
            "source_class": "approved_knowledge",
        }
    )

    assert result["epistemic_state"] == "bounded_prediction"
    assert result["prediction_allowed_without_future_fact"] is True
    assert result["confidence_vector"]["prediction_confidence"] == "bounded_basis_not_outcome_certainty"
    assert result["confidence_vector"]["evidence_confidence"] == "reviewed"
    _assert_locked(result)


def test_known_part_and_exact_current_gap_become_partial_answer():
    result = build_epistemic_answer_state(
        {
            "prompt": "Explain day and night, then give the exact sunrise tomorrow.",
            "content_seed": "Earth rotates, carrying a location into and out of sunlight.",
            "source_id": "approved_comprehension",
            "source_class": "approved_knowledge",
            "answer_completion": {
                "resolutions": [
                    {
                        "obligation_id": "sunrise",
                        "kind": "requested_output",
                        "unsupported": True,
                        "missing_ground": "supported content for the requested output",
                        "resolution": "explicit_unsupported_part",
                    }
                ]
            },
        }
    )

    assert result["epistemic_state"] == "partial_answer"
    assert result["known_part_present"] is True
    assert result["missing_parts"][0]["state"] == "missing_current_information"
    assert "request_current_data_or_lookup" in result["next_route_candidates"]
    _assert_locked(result)


def test_source_request_and_unknowable_information_remain_distinct():
    source_gap = build_epistemic_answer_state(
        {
            "prompt": "Give a page number and direct quotation from the research paper.",
            "content_seed": "I need the attributed paper before I can quote it.",
            "answer_completion": {
                "resolutions": [
                    {
                        "obligation_id": "quote",
                        "kind": "requested_output",
                        "unsupported": True,
                        "missing_ground": "supported content for the requested output",
                    }
                ]
            },
        }
    )
    unknowable = build_epistemic_answer_state(
        {
            "prompt": "What was on the lost final page that nobody preserved?",
            "content_seed": "That page cannot be recovered from the available record.",
            "answer_completion": {
                "resolutions": [
                    {
                        "obligation_id": "lost-page",
                        "kind": "direct_question",
                        "unsupported": True,
                        "missing_ground": "an attributed fact, approved concept, or visible observation",
                    }
                ]
            },
        }
    )

    assert source_gap["missing_parts"][0]["state"] == "missing_attributed_source"
    assert unknowable["missing_parts"][0]["state"] == "genuinely_unknowable"


def test_reviewed_lived_experience_is_scoped_evidence_not_universal_fact():
    result = build_epistemic_answer_state(
        {
            "prompt": "Based on what you remember, what pattern might be repeating?",
            "content_seed": "A pattern in my reviewed experience may be relevant here.",
            "source_id": "contextual_approved_memory",
            "source_class": "memory_reconstruction",
            "memory_context": {"memory_confidence": "clear_recall"},
        }
    )

    assert result["epistemic_state"] == "reviewed_experience_recall"
    assert result["reviewed_lived_experience"]["available"] is True
    assert result["reviewed_lived_experience"]["scope"] == "personal_experience_not_universal_fact"
    assert result["reviewed_lived_experience"]["may_be_invented"] is False
    assert result["confidence_vector"]["memory_confidence"] == "clear_recall"
    _assert_locked(result)


def test_finalization_keeps_answer_and_expression_confidence_independent():
    initial = build_epistemic_answer_state(
        {
            "prompt": "What do we know?",
            "content_seed": "We know the observed sequence.",
            "source_class": "reasoning_answer",
        }
    )
    result = finalize_epistemic_answer_state(
        initial,
        response_coverage={"all_required_addressed": False, "unresolved_count": 1},
        expression_confidence="high",
    )

    assert result["confidence_vector"]["answer_confidence"] == "incomplete_for_requested_parts"
    assert result["confidence_vector"]["expression_confidence"] == "high"
    assert result["expression_confidence_is_truth_confidence"] is False
    assert result["confidence_vector"]["dimensions_are_independent"] is True
    _assert_locked(result)


def test_mixed_composition_keeps_supported_part_when_neighbor_is_missing():
    composition = {
        "dominant_state": "partial_answer",
        "parts": [
            {
                "obligation_id": "known",
                "requested_kind": "reason",
                "epistemic_state": "supported_answer",
                "certainty": "supported",
                "source_class": "approved_knowledge",
            },
            {
                "obligation_id": "exact",
                "requested_kind": "requested_output",
                "epistemic_state": "missing_ground",
                "missing_ground": "current date, location, and astronomical data",
                "source_class": "conversation",
            },
        ],
    }
    result = build_epistemic_answer_state(
        {
            "prompt": "Explain day and night and give the exact sunrise tomorrow.",
            "content_seed": (
                "Earth rotates, carrying a location into and out of sunlight. "
                "I still need the date, location, and astronomical data for the exact time."
            ),
            "source_id": "bounded_answer_completion",
            "source_class": "reasoning_answer",
            "epistemic_composition": composition,
        }
    )

    assert result["epistemic_state"] == "partial_answer"
    assert result["known_part_present"] is True
    assert result["missing_part_present"] is True
    assert result["supported_parts"][0]["epistemic_state"] == "supported_answer"
    assert result["missing_parts"][0]["obligation_id"] == "exact"
    assert result["unknown_part_downgraded_supported_part"] is False
    _assert_locked(result)
