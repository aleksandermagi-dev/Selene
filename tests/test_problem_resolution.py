from __future__ import annotations

from selene.db import connect, init_db
from selene.intelligence_os import run_intelligence_os_reason
from selene.metacognition import evaluate_metacognition
from selene.module_router import route_request
from selene.problem_resolution import (
    build_problem_resolution,
    problem_resolution_status,
)


def _assert_bounded(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["hidden_chain_of_thought_exposed"] is False


def test_status_exposes_seven_point_and_canonical_epistemic_contract():
    result = problem_resolution_status()

    assert result["seven_point_dimensions"] == [
        "who",
        "what",
        "why",
        "when",
        "where",
        "how",
        "context",
    ]
    assert {
        "KNOWN_SUPPORTED",
        "CANDIDATE_UNVERIFIED",
        "UNKNOWN_INSUFFICIENT_EVIDENCE",
        "CONFLICT_UNSATISFIABLE",
        "WRONG_FALSIFIED",
        "RETRY_UPDATED_APPROACH",
    }.issubset(result["epistemic_states"])
    assert result["generates_answer_facts"] is False
    _assert_bounded(result)


def test_router_exposes_status_and_preview_without_writing_state(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    status = route_request(conn, "problem_resolution.status")["result"]
    preview = route_request(
        conn,
        "problem_resolution.preview",
        {"prompt": "What can the current evidence establish?"},
    )["result"]

    assert status["status"] == "problem_resolution_coordination_ready"
    assert preview["status"] == "problem_resolution_packet_ready"
    assert preview["epistemic_state"] == "UNKNOWN_INSUFFICIENT_EVIDENCE"
    assert preview["memory_write_active"] is False


def test_contradictory_constraints_are_held_before_solver_retry():
    result = build_problem_resolution(
        {
            "prompt": "Produce one answer under both requirements.",
            "constraints": [
                {
                    "id": "must-answer",
                    "subject": "answer_state",
                    "operator": "requires",
                    "value": "answer_now",
                    "hard": True,
                },
                {
                    "id": "must-not-answer",
                    "subject": "answer_state",
                    "operator": "forbids",
                    "value": "answer_now",
                    "hard": True,
                },
            ],
            "prior_attempts": [
                {
                    "approach": "force an answer anyway",
                    "status": "failed",
                    "failure_class": "conflicting_constraints",
                }
            ],
        }
    )

    assert result["satisfiability_gate"]["state"] == "unsatisfiable"
    assert result["satisfiability_gate"]["solver_at_fault"] is False
    assert result["epistemic_state"] == "CONFLICT_UNSATISFIABLE"
    assert result["failure"]["class"] == "conflicting_constraints"
    assert result["retry"]["allowed"] is False
    assert result["stopping_state"] == "stop_until_constraint_revision"
    _assert_bounded(result)


def test_missing_information_preserves_unknown_as_the_only_valid_result():
    result = build_problem_resolution(
        {
            "prompt": "Which entrance did the person use?",
            "required_dimensions": ["who", "where", "context"],
            "situation": {"what": "choose the entrance"},
            "underspecified": True,
        }
    )

    assert result["reconstruction"]["missing_required_dimensions"] == [
        "who",
        "where",
        "context",
    ]
    assert result["epistemic_state"] == "UNKNOWN_INSUFFICIENT_EVIDENCE"
    assert result["stopping_state"] == "stop_unknown_without_manufactured_answer"
    assert result["unknown_is_failure"] is False


def test_false_premise_is_removed_before_a_changed_retry():
    result = build_problem_resolution(
        {
            "prompt": "Recompute the conclusion after the premise was shown wrong.",
            "premises": [
                {
                    "id": "premise-a",
                    "subject": "fan_location",
                    "operator": "equals",
                    "value": "outside",
                    "validity": "falsified",
                }
            ],
            "prior_attempts": [
                {
                    "attempt_id": "attempt-1",
                    "approach": "derive the answer from the outside-wind premise",
                    "status": "wrong",
                    "failure_class": "false_premise",
                    "failed_causal_path": "outside-wind premise to outdoor conclusion",
                    "useful_mechanics": ["air movement changes the paper response"],
                }
            ],
        }
    )

    assert result["failure"]["class"] == "false_premise"
    assert result["epistemic_state"] == "RETRY_UPDATED_APPROACH"
    assert "remove or replace" in result["retry"]["updated_approach"]
    assert result["retry"]["repeats_known_failed_path"] is False
    assert "air movement changes the paper response" in result["retry"]["information_incorporated"]


def test_ambiguous_context_is_not_replaced_by_a_plausible_why_story():
    result = build_problem_resolution(
        {
            "prompt": "It failed because the connection closed.",
            "required_dimensions": ["who", "what", "when", "where", "how", "context"],
            "situation": {"why": "the connection closed"},
        }
    )

    assert result["reconstruction"]["dimensions"]["why"]["state"] == "supplied_or_visible"
    assert result["reconstruction"]["why_alone_treated_as_sufficient"] is False
    assert result["failure"]["class"] == "ambiguous_context"
    assert result["epistemic_state"] == "UNKNOWN_INSUFFICIENT_EVIDENCE"


def test_confident_wrong_answer_is_admitted_and_retried_with_failure_information():
    result = build_problem_resolution(
        {
            "prompt": "Check the answer and try a different method if it is wrong.",
            "verification": {"status": "falsified", "observed": "the check produced 11, not 12"},
            "prior_attempts": [
                {
                    "attempt_id": "attempt-1",
                    "approach": "reuse the unchecked shortcut",
                    "conclusion": "12",
                    "status": "falsified",
                    "failure_class": "verification_failure",
                    "failed_causal_path": "unchecked shortcut",
                    "useful_mechanics": ["the first decomposition step was verified"],
                }
            ],
            "candidate_strategies": [
                "reuse the unchecked shortcut",
                "recalculate from the verified decomposition and check the final operation independently",
            ],
        }
    )

    assert result["epistemic_state_before_retry"] == "WRONG_FALSIFIED"
    assert result["epistemic_state"] == "RETRY_UPDATED_APPROACH"
    assert result["candidate_lifecycle"]["attempts"][0]["defended_after_falsification"] is False
    assert result["retry"]["updated_approach"].startswith("recalculate")
    assert "unchecked shortcut" in result["retry"]["avoids_failed_paths"]
    assert result["retry"]["blind_regeneration_allowed"] is False


def test_no_new_strategy_repeats_a_known_failed_causal_path():
    result = build_problem_resolution(
        {
            "prompt": "Try again.",
            "failure_class": "bad_inference",
            "prior_attempts": [
                {
                    "approach": "rebuild from the supported premises and compare an alternative inference against the same observations",
                    "status": "failed",
                    "failure_class": "bad_inference",
                }
            ],
            "candidate_strategies": [
                "rebuild from the supported premises and compare an alternative inference against the same observations"
            ],
        }
    )

    assert result["epistemic_state"] == "WRONG_FALSIFIED"
    assert result["retry"]["status"] == "hold_unknown_no_justified_new_path"
    assert result["retry"]["allowed"] is False
    assert result["retry"]["repeats_known_failed_path"] is False


def test_supported_verification_reaches_known_without_identity_or_memory_change():
    result = build_problem_resolution(
        {
            "prompt": "Verify the bounded result.",
            "verification": {"status": "verified"},
            "evidence": [{"status": "verified", "text": "independent check agrees"}],
        }
    )

    assert result["epistemic_state"] == "KNOWN_SUPPORTED"
    assert result["stopping_state"] == "stop_supported"
    assert result["retry"]["status"] == "retry_not_needed"
    _assert_bounded(result)


def test_intelligence_os_and_metacognition_hold_an_unsatisfiable_problem(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    intelligence = run_intelligence_os_reason(
        conn,
        {
            "prompt": "Give the answer now while also withholding that same answer.",
            "constraints": [
                {"subject": "release", "operator": "requires", "value": "answer"},
                {"subject": "release", "operator": "forbids", "value": "answer"},
            ],
        },
    )
    meta = evaluate_metacognition(
        {
            "prompt": "Should the solver try again?",
            "intelligence_os_support": intelligence,
            "candidate_text": intelligence["best_current_answer"],
        }
    )

    assert intelligence["problem_resolution"]["epistemic_state"] == "CONFLICT_UNSATISFIABLE"
    assert intelligence["selected_next_step"] == "hold_constraint_conflict"
    assert meta["recommended_action"] == "hold_constraint_conflict"
    assert meta["stopping"]["stop_now"] is True
    assert meta["feedback_handoff"]["single_cycle_requested"] is False
    assert meta["problem_resolution_assessment"]["blind_regeneration_recommended"] is False


def test_failed_intelligence_attempt_hands_metacognition_one_changed_retry(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    intelligence = run_intelligence_os_reason(
        conn,
        {
            "prompt": "Reassess the mechanism after the first explanation was contradicted.",
            "failure_class": "bad_inference",
            "prior_attempts": [
                {
                    "approach": "treat timing alone as proof of cause",
                    "status": "falsified",
                    "failure_class": "bad_inference",
                    "useful_mechanics": ["the timing observation remains valid"],
                }
            ],
            "candidate_strategies": [
                "compare alternative mechanisms against timing and one distinguishing observation"
            ],
        },
    )
    meta = evaluate_metacognition(
        {
            "prompt": "Is another attempt justified?",
            "intelligence_os_support": intelligence,
            "candidate_text": intelligence["best_current_answer"],
        }
    )

    resolution = intelligence["problem_resolution"]
    assert resolution["epistemic_state"] == "RETRY_UPDATED_APPROACH"
    assert "the timing observation remains valid" in resolution["retry"]["information_incorporated"]
    assert meta["recommended_action"] == "retry_updated_approach"
    assert meta["feedback_handoff"]["responsible_owner"] == "intelligence_os"
    assert meta["feedback_handoff"]["single_cycle_requested"] is True
    assert meta["stopping"]["stop_now"] is False
