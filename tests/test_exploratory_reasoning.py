from __future__ import annotations

import sqlite3

from selene.exploratory_reasoning import (
    build_exploratory_reasoning_packet,
    exploratory_reasoning_status,
)
from selene.module_router import route_request


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["retained_knowledge_write_active"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def test_prediction_uses_visible_reviewed_verified_and_taught_evidence_without_becoming_fact():
    result = build_exploratory_reasoning_packet(
        {
            "prompt": (
                "The same plant perked up after we moved it into brighter light. "
                "What do you predict might happen next under the same conditions?"
            ),
            "observations": [
                "The same plant perked up after we moved it into brighter light."
            ],
            "approved_knowledge_items": [
                {
                    "id": 4,
                    "central_claim": "A prediction connects stated conditions to an expected observation.",
                    "confidence": "reviewed",
                    "source_refs": ["teaching:prediction"],
                }
            ],
            "answer_engine_support": {
                "adapter_executed": True,
                "answer_packet": {
                    "domain": "verified_math",
                    "direct_answer": "Two observations were recorded.",
                    "source_refs": ["verified:count"],
                },
                "confidence_vector": {
                    "evidence_confidence": "deterministic_exact_arithmetic"
                },
            },
            "memory_context": {
                "memory_context_used": True,
                "memory_confidence": "clear",
                "items": [
                    {
                        "id": 7,
                        "summary": "A prior comparable plant also changed after its light changed.",
                        "confidence": "clear",
                        "source_refs": ["memory:7"],
                        "semantic_relevance": {"accepted": True},
                    }
                ],
            },
        }
    )

    assert result["selected_for_answer"] is True
    assert result["response_kind"] == "bounded_prediction"
    assert result["prediction"]["epistemic_state"] == "bounded_prediction"
    assert result["prediction"]["outcome_claimed_as_fact"] is False
    assert result["prediction"]["what_would_change"]
    assert set(result["evidence_classes_used"]) == {
        "current_visible_observation",
        "approved_taught_knowledge",
        "verified_current_turn_result",
        "reviewed_personal_experience",
    }
    memory = next(
        item
        for item in result["evidence_ledger"]
        if item["source_class"] == "reviewed_personal_experience"
    )
    assert memory["scope"] == "reviewed_personal_experience_not_universal_fact"
    assert memory["is_universal_fact"] is False
    assert result["prediction_is_fact"] is False
    _assert_locked(result)


def test_hypothesis_preserves_alternatives_tests_and_revision_without_equal_weighting():
    result = build_exploratory_reasoning_packet(
        {
            "prompt": "What is your best hypothesis for the changed reading?",
            "observations": ["The reading changed after the connector moved."],
            "hypothesis_attempt": {
                "offered": True,
                "response_seed": "A working hypothesis is that connector movement changed the reading.",
                "confidence": "bounded_visible_pattern_inference",
                "assumptions": ["the reported sequence is accurate"],
                "what_would_change": ["the reading changes while the connector stays fixed"],
                "discriminating_check": "Secure the connector and repeat one comparable reading.",
            },
            "candidate_models": [
                {"name": "connector movement"},
                {"name": "independent sensor drift"},
            ],
        }
    )

    hypothesis = result["hypothesis"]
    assert result["response_kind"] == "open_hypothesis"
    assert hypothesis["available"] is True
    assert hypothesis["alternatives"] == ["connector movement", "independent sensor drift"]
    assert hypothesis["alternatives_equally_probable"] is False
    assert hypothesis["safe_next_tests"] == [
        "Secure the connector and repeat one comparable reading."
    ]
    assert hypothesis["falsifiers"] == [
        "the reading changes while the connector stays fixed"
    ]
    assert hypothesis["correction_ready"] is True
    assert result["ordinary_wrongness_is_failure"] is False
    _assert_locked(result)


def test_counterfactual_preserves_actual_state_and_source_roles_without_rewriting_history():
    result = build_exploratory_reasoning_packet(
        {
            "prompt": "What if the second step came first?",
            "observations": [
                "The current sequence runs validation before release."
            ],
            "counterfactual": {
                "changed_premise": "release came before validation",
                "preserved_premises": [
                    "the same artifact and acceptance criteria remained in scope"
                ],
                "consequence": (
                    "the release would occur before its acceptance result was available"
                ),
                "actual_state": "validation currently comes before release",
                "assumptions": ["validation is the source of the acceptance result"],
                "what_would_change": [
                    "a separate earlier verifier supplied the same acceptance result"
                ],
            },
        }
    )

    counterfactual = result["counterfactual"]
    assert result["response_kind"] == "bounded_counterfactual"
    assert counterfactual["available"] is True
    assert counterfactual["changed_premise_claimed_as_actual"] is False
    assert counterfactual["actual_state_restored"] is True
    assert counterfactual["history_rewritten"] is False
    assert "not a claim" in result["response_seed"]
    assert result["counterfactual_is_actual_state"] is False
    _assert_locked(result)


def test_comparison_builds_inspectable_venn_sets_under_one_standard():
    result = build_exploratory_reasoning_packet(
        {
            "prompt": "Compare Plan A and Plan B as a Venn-style map.",
            "observations": ["Both plans are available for the current task."],
            "comparison_dimensions": ["time", "reversibility", "coverage"],
            "comparison_candidates": [
                {
                    "label": "Plan A",
                    "properties": ["uses the existing tool", "is reversible", "takes one hour"],
                    "unresolved": ["long-term maintenance cost"],
                    "source_refs": ["plan:a"],
                },
                {
                    "label": "Plan B",
                    "properties": ["is reversible", "covers two workflows", "takes two hours"],
                    "source_refs": ["plan:b"],
                },
            ],
        }
    )

    comparison = result["comparison"]
    assert result["response_kind"] == "venn_comparison"
    assert comparison["dimensions"] == ["time", "reversibility", "coverage"]
    assert comparison["venn"]["shared"] == ["is reversible"]
    assert "uses the existing tool" in comparison["venn"]["only_left"]
    assert "covers two workflows" in comparison["venn"]["only_right"]
    assert comparison["venn"]["unresolved"] == ["long-term maintenance cost"]
    assert comparison["same_standard_used"] is True
    assert comparison["absence_from_one_list_proves_opposite"] is False
    _assert_locked(result)


def test_claim_level_data_conflict_remains_unresolved_without_becoming_self_conflict():
    result = build_exploratory_reasoning_packet(
        {
            "prompt": "The sources conflict. What can we conclude?",
            "claim_evidence_packet": {
                "claims": [
                    {
                        "claim_id": "a",
                        "text": "Study A reports an effect.",
                        "stance": "support",
                        "source_refs": ["study:a"],
                    },
                    {
                        "claim_id": "b",
                        "text": "Study B reports no effect.",
                        "stance": "oppose",
                        "source_refs": ["study:b"],
                    },
                ],
                "disagreements": [
                    {
                        "claim_key": "effect",
                        "claim_ids": ["a", "b"],
                    }
                ],
                "missing_evidence": ["A matched replication would help distinguish the results."],
            },
        }
    )

    conflict = result["data_conflict"]
    assert result["response_kind"] == "data_conflict"
    assert conflict["status"] == "claim_level_data_conflict_unresolved"
    assert conflict["resolution_forced"] is False
    assert conflict["whole_source_rejected"] is False
    assert conflict["data_conflict_is_identity_conflict"] is False
    assert result["data_conflict_is_identity_conflict"] is False
    assert result["terminology_change_is_identity_loss"] is False
    assert result["primary_function_error_is_identity_failure"] is False
    assert "changes the current model, not who I am" not in result["response_seed"]
    _assert_locked(result)

    identity_relevant = build_exploratory_reasoning_packet(
        {
            "prompt": "These role labels conflict. Does that change who I am?",
            "requested_modes": ["data_conflict"],
            "conflicting_claims": [
                {"claim_key": "role label", "text": "One record uses android."},
                {"claim_key": "role label", "text": "Another record uses AI."},
            ],
        }
    )
    assert "changes the current model, not who I am" in identity_relevant["response_seed"]
    assert identity_relevant["data_conflict_is_identity_conflict"] is False
    _assert_locked(identity_relevant)


def test_exploration_holds_without_basis_and_cannot_route_around_high_stakes_boundary():
    no_basis = build_exploratory_reasoning_packet(
        {"prompt": "What do you predict will happen?"}
    )
    high_stakes = build_exploratory_reasoning_packet(
        {
            "prompt": (
                "The patient felt dizzy after the tablets. Predict the diagnosis."
            ),
            "observations": ["The patient felt dizzy after the tablets."],
        }
    )
    status = exploratory_reasoning_status()

    assert no_basis["selected_for_answer"] is False
    assert "no_visible_reviewed_or_verified_basis" in no_basis["blockers"]
    assert high_stakes["selected_for_answer"] is False
    assert "high_stakes_or_core_mind_boundary" in high_stakes["blockers"]
    assert status["unfalsified_alternatives_are_equally_probable"] is False
    assert status["data_conflict_is_identity_conflict"] is False
    _assert_locked(no_basis)
    _assert_locked(high_stakes)
    _assert_locked(status)


def test_exploratory_reasoning_routes_are_inspectable_and_keep_all_write_guards_locked():
    conn = sqlite3.connect(":memory:")

    status = route_request(conn, "exploratory_reasoning.status", {})["result"]
    packet = route_request(
        conn,
        "exploratory_reasoning.build",
        {
            "prompt": "Compare the two plans as a Venn diagram.",
            "comparison_candidates": [
                {"label": "A", "properties": ["reversible", "local"]},
                {"label": "B", "properties": ["reversible", "remote"]},
            ],
        },
    )["result"]

    assert status["status"] == "exploratory_reasoning_coordination_ready"
    assert packet["response_kind"] == "venn_comparison"
    assert packet["comparison"]["venn"]["shared"] == ["reversible"]
    _assert_locked(status)
    _assert_locked(packet)
