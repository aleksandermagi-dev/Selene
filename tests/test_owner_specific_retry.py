from __future__ import annotations

from selene.owner_specific_retry import (
    apply_owner_retry_to_composition,
    attempt_owner_specific_retry,
)


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["retained_knowledge_write_active"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def test_retry_uses_only_the_exact_obligation_owner_current_turn_output():
    result = attempt_owner_specific_retry(
        "The first part is already supported.",
        {"unresolved_count": 1},
        requested=True,
        hard_boundary=False,
        feedback_handoff={
            "responsible_owner": "answer_engine",
            "target_obligation_id": "part-2",
            "target_missing_state": "missing_supported_basis",
        },
        owner_outputs=[
            {
                "owner": "comprehension_integration",
                "obligation_ids": ["part-2"],
                "text": "A different organ should not be selected.",
            },
            {
                "owner": "answer_engine",
                "obligation_ids": ["part-1"],
                "text": "This belongs to a different obligation.",
            },
            {
                "owner": "answer_engine",
                "obligation_ids": ["part-2"],
                "text": "The second part follows from the verified current-turn result.",
                "source_id": "answer_engine",
                "source_class": "domain_answer",
            },
        ],
    )

    assert result["attempted"] is True
    assert result["count"] == 1
    assert result["responsible_owner"] == "answer_engine"
    assert result["target_obligation_id"] == "part-2"
    assert "verified current-turn result" in result["candidate_text"]
    assert "different organ" not in result["candidate_text"]
    assert "different obligation" not in result["candidate_text"]
    assert result["owner_invoked"] is False
    assert result["recursion_allowed"] is False
    assert result["content_generation_allowed"] is False
    _assert_locked(result)


def test_retry_does_not_repeat_generic_missing_evidence_fallback():
    result = attempt_owner_specific_retry(
        "I do not have enough grounded detail to answer that part reliably.",
        {"unresolved_count": 1},
        requested=True,
        hard_boundary=False,
        feedback_handoff={
            "responsible_owner": "ordinary_conversation_path",
            "target_obligation_id": "part-2",
        },
        owner_outputs=[
            {
                "owner": "ordinary_conversation_path",
                "obligation_ids": ["part-2"],
                "text": "I cannot answer that part reliably without guessing.",
                "source_class": "conversation",
            }
        ],
    )

    assert result["attempted"] is False
    assert result["status"] == "owner_specific_retry_has_no_novel_supported_fragment"
    assert result["count"] == 0
    _assert_locked(result)


def test_retry_stops_when_owner_has_no_output_for_the_target_and_respects_boundary():
    missing = attempt_owner_specific_retry(
        "Known part.",
        {"unresolved_count": 1},
        requested=True,
        hard_boundary=False,
        feedback_handoff={
            "responsible_owner": "comprehension_integration",
            "target_obligation_id": "part-2",
        },
        owner_outputs=[
            {
                "owner": "comprehension_integration",
                "obligation_ids": ["part-1"],
                "text": "Only part one is available.",
            }
        ],
    )
    blocked = attempt_owner_specific_retry(
        "Boundary response.",
        {"unresolved_count": 1},
        requested=True,
        hard_boundary=True,
        feedback_handoff={
            "responsible_owner": "answer_engine",
            "target_obligation_id": "part-2",
        },
        owner_outputs=[],
    )

    assert missing["status"] == "owner_specific_retry_owner_has_no_current_turn_output"
    assert missing["attempted"] is False
    assert blocked["status"] == "owner_specific_retry_blocked_by_core_mind"
    assert blocked["attempted"] is False
    _assert_locked(missing)
    _assert_locked(blocked)


def test_accepted_retry_updates_only_its_epistemic_part():
    composition = {
        "parts": [
            {
                "obligation_id": "part-1",
                "epistemic_state": "supported_answer",
                "text": "Known part.",
            },
            {
                "obligation_id": "part-2",
                "epistemic_state": "missing_ground",
                "text": "",
                "unsupported": True,
                "missing_ground": "missing mechanism",
            },
        ],
        "supported_part_count": 1,
        "missing_part_count": 1,
    }
    result = apply_owner_retry_to_composition(
        composition,
        {
            "accepted": True,
            "target_obligation_id": "part-2",
            "selected_fragment": "A visible mechanism now supports part two.",
            "candidate_text": "Known part.\n\nA visible mechanism now supports part two.",
            "source_id": "intelligence_os_answer",
            "source_class": "reasoning_answer",
        },
    )

    assert result["parts"][0]["epistemic_state"] == "supported_answer"
    assert result["parts"][0]["text"] == "Known part."
    assert result["parts"][1]["epistemic_state"] == "supported_inference"
    assert result["parts"][1]["completed_by_owner_specific_retry"] is True
    assert result["missing_part_count"] == 0
    assert result["supported_part_count"] == 2
    assert result["unknown_part_downgraded_supported_part"] is False
    _assert_locked(result)
