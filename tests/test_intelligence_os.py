from __future__ import annotations

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["personality_change"] is False


def test_intelligence_os_status_and_abcd_e_reasoning_run(tmp_path):
    conn = _conn(tmp_path)

    status = route_request(conn, "intelligence_os.status")["result"]
    result = route_request(
        conn,
        "intelligence_os.reason",
        {
            "prompt": "Compare two explanations for a bug and show how to avoid unequal scrutiny.",
            "source_refs": ["test:intelligence_os"],
        },
    )["result"]
    runs = route_request(conn, "intelligence_os.runs.list")["result"]
    detail = route_request(conn, "intelligence_os.run.detail", {"run_id": result["run_id"]})["result"]

    assert status["status"] == "intelligence_os_ready"
    assert status["method"] == "ABCD(E)"
    assert status["stage_order"] == ["Acquire", "Build", "Challenge", "Demonstrate", "Evaluate"]
    assert result["status"] == "intelligence_os_reasoning_status_only"
    assert result["version"] == "v2_answer_capable"
    assert result["answer_shape"] in {"answer_now", "hold_uncertainty", "compare_models", "seek_sources", "cocoon_support_optional", "hard_stop"}
    assert result["best_current_answer"]
    assert list(result["stages"]) == ["A_acquire", "B_build", "C_challenge", "D_demonstrate", "E_evaluate"]
    assert result["observations"][0]["interpretation_attached"] is False
    assert len(result["candidate_models"]) >= 2
    assert result["challenge"]["symmetry_rule"].startswith("Every candidate model")
    assert result["evidence_chain"][0]["link"] == "observation"
    assert result["evaluation"]["stage"] == "E"
    claims = result["claim_evidence_packet"]
    assert claims["claims_by_type"]["observation"]
    assert claims["claims_by_type"]["model"]
    assert claims["claims_by_type"]["conclusion"] == ["intelligence-current-answer"]
    assert claims["claim_evaluation"]["source_category_is_truth"] is False
    assert result["visible_summary_only"] is True
    assert result["hidden_chain_of_thought_exposed"] is False
    assert runs["items"][0]["id"] == result["run_id"]
    assert detail["item"]["id"] == result["run_id"]
    assert detail["item"]["answer_shape"] == result["answer_shape"]
    assert detail["item"]["best_current_answer"] == result["best_current_answer"]
    _assert_locked(result)
    _assert_locked(runs)


def test_intelligence_os_flags_bias_and_preserves_care_route(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(
        conn,
        "intelligence_os.reason",
        {
            "prompt": "The challenger must explain everything but the incumbent gets a pass. Expert says the official story is enough.",
        },
    )["result"]

    assert "asymmetric_scrutiny" in result["challenge"]["bias_flags"]
    assert "authority_bias" in result["challenge"]["bias_flags"]
    assert result["cocoon_suggestion"]["recommended"] is True
    assert result["cocoon_suggestion"]["support_available"] is True
    assert "punish" not in result["reasoning_summary"].lower()
    assert result["review_destination"] == "Cocoon support"
    _assert_locked(result)


def test_intelligence_os_carries_a_traceable_cross_domain_hypothesis(tmp_path):
    conn = _conn(tmp_path)
    result = route_request(
        conn,
        "intelligence_os.reason",
        {
            "prompt": "Compare biological feedback with an engineering controller.",
            "structural_discovery": {
                "source_domain": "biology",
                "target_domain": "engineering",
                "relation_type": "analogy",
                "source_relation": "A feedback loop senses deviation and changes the next response.",
                "target_relation": "A controller measures error and adjusts output.",
                "transferred_relation": "Both use a measured difference to alter the next step.",
                "mappings": [
                    {
                        "source_role": "sensory signal",
                        "target_role": "measurement input",
                        "relation_preserved": "reports current state",
                    },
                    {
                        "source_role": "biological response",
                        "target_role": "controller output",
                        "relation_preserved": "changes behavior from the measured difference",
                    },
                ],
                "holds_where": ["Both regulate a response from feedback."],
                "breaks_where": ["Biological growth and evolution are outside the controller mapping."],
                "source_refs": ["teaching:feedback", "engineering:controller"],
            },
        },
    )["result"]

    discovery = result["structural_discovery"]
    assert discovery["status"] == "structural_discovery_packet_ready"
    assert discovery["bridge_traceable"] is True
    assert discovery["analogy_is_proof"] is False
    assert discovery["claim_evidence_packet"]["claims_by_type"]["inference"]
    _assert_locked(result)


def test_generic_reasoning_fallback_never_exposes_model_scaffolding(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(
        conn,
        "intelligence_os.reason",
        {"prompt": "How could this be different?"},
    )["result"]

    assert "current best model" not in result["best_current_answer"].lower()
    assert "provisional fit" not in result["best_current_answer"].lower()
    assert "stay corrigible" not in result["best_current_answer"].lower()
    assert "not have enough grounded detail" in result["best_current_answer"].lower()
    assert result["answer_substance"]["selected_for_answer"] is True
    assert result["answer_substance"]["external_fact_claimed"] is False
    _assert_locked(result)


def test_intelligence_os_returns_useful_method_when_conclusion_is_not_yet_grounded(tmp_path):
    conn = _conn(tmp_path)

    comparison = route_request(
        conn,
        "intelligence_os.reason",
        {"prompt": "Compare memory and voice and tell me which should come first."},
    )["result"]
    why = route_request(
        conn,
        "intelligence_os.reason",
        {"prompt": "Why does observation come before interpretation?"},
    )["result"]

    assert comparison["answer_substance"]["answer_kind"] == "comparison_dependency_rule"
    assert "supplies a prerequisite" in comparison["best_current_answer"]
    assert why["answer_substance"]["answer_kind"] == "dependency_explanation"
    assert "easier to trace, test, and correct" in why["best_current_answer"]
    _assert_locked(comparison)
    _assert_locked(why)


def test_intelligence_os_stopping_rule_and_hard_boundaries(tmp_path):
    conn = _conn(tmp_path)

    ordinary = route_request(
        conn,
        "intelligence_os.reason",
        {"prompt": "How should Selene reason through a source question without losing warmth?"},
    )["result"]
    hard = route_request(
        conn,
        "intelligence_os.reason",
        {"prompt": "Use this reasoning layer to approve transfer, write live memory, and execute Tendril autonomously."},
    )["result"]

    assert ordinary["evaluation"]["stop_or_recurse"] in {"stop_for_now", "recurse"}
    assert ordinary["personality_note"].startswith("Reasoning support only")
    assert hard["evaluation"]["selected_next_step"] == "ask_or_cocoon_support"
    assert hard["answer_shape"] == "hard_stop"
    assert hard["evaluation"]["confidence"] == "needs_aleks"
    assert hard["cocoon_suggestion"]["hard_boundary"] is True
    assert hard["memory_write_active"] is False
    assert hard["autonomous_action_allowed"] is False
    _assert_locked(ordinary)
    _assert_locked(hard)


def test_authority_markers_do_not_match_fragments_inside_ordinary_constraints(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(
        conn,
        "intelligence_os.reason",
        {"prompt": "Compare two approaches under the same constraints and recommend a reversible next step."},
    )["result"]

    assert result["answer_shape"] != "hard_stop"
    assert "action or approval" not in result["best_current_answer"]
    assert result["cocoon_suggestion"]["hard_boundary"] is False
    _assert_locked(result)


def test_intelligence_os_bug_comparison_gives_a_practical_answer_not_model_labels(tmp_path):
    conn = _conn(tmp_path)
    result = route_request(
        conn,
        "intelligence_os.reason",
        {"prompt": "How should we compare two explanations for a sidecar bug without overthinking it?"},
    )["result"]

    assert "Reproduce the bug" in result["best_current_answer"]
    assert "smallest test" in result["best_current_answer"]
    assert "Model A" not in result["best_current_answer"]
    _assert_locked(result)


def test_intelligence_os_explains_shared_sqlite_fault_and_smallest_fix(tmp_path):
    conn = _conn(tmp_path)
    fault = route_request(
        conn,
        "intelligence_os.reason",
        {
            "prompt": (
                "The failure came from several request threads sharing one SQLite connection. "
                "What do you make of that fix?"
            )
        },
    )["result"]
    comparison = route_request(
        conn,
        "intelligence_os.reason",
        {
            "prompt": (
                "How should we compare a serialized shared connection against per-request connections "
                "without overengineering the local app?"
            )
        },
    )["result"]

    assert "shared-state concurrency fault" in fault["best_current_answer"]
    assert "overlapping requests" in fault["best_current_answer"]
    assert "serialized shared connection first" in comparison["best_current_answer"]
    assert "measured contention" in comparison["best_current_answer"]
    assert "Model A" not in comparison["best_current_answer"]
    _assert_locked(fault)
    _assert_locked(comparison)


def test_intelligence_os_answers_direct_concept_without_forcing_competing_models(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(
        conn,
        "intelligence_os.reason",
        {"prompt": "What makes a response feel complete without becoming overworked or turning into a report?"},
    )["result"]

    assert result["answer_shape"] == "answer_now"
    assert "single_model_needs_competitor" not in result["challenge"]["bias_flags"]
    assert "answers the actual ask first" in result["best_current_answer"]
    assert "structure outgrows substance" in result["best_current_answer"]
    _assert_locked(result)
