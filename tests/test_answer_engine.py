from __future__ import annotations

import sqlite3

import pytest

from selene.answer_engine import (
    answer_engine_status,
    preview_answer_coordination,
    preview_answer_route,
    preview_domain_answer_packet,
    run_comparison_planning_answer,
    run_local_code_inspection_answer,
    run_source_backed_research_answer,
    run_verified_math_answer,
)
from selene.db import init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = sqlite3.connect(tmp_path / "selene.db")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["identity_change"] is False
    assert result["governance_change"] is False
    assert result["live_chat_connected"] is True


def test_answer_engine_status_connects_math_research_and_comparison_while_code_stays_deferred():
    result = answer_engine_status()

    assert result["status"] == "answer_engine_supervised_chat_bridge_ready"
    assert result["phase"] == "phase_11_pre_teaching_architecture_closure"
    assert set(result["confidence_dimensions"]) == {
        "route_confidence",
        "evidence_confidence",
        "answer_confidence",
        "memory_confidence",
        "expression_confidence",
    }
    assert result["domain_adapter_status"]["verified_math"] == "exact_arithmetic_adapter_connected_to_supervised_chat"
    assert result["domain_adapter_status"]["local_code_inspection"] == "explicit_source_static_inspection_available_not_connected_to_chat"
    assert result["domain_adapter_status"]["comparison_planning"] == "intelligence_os_adapter_connected_to_supervised_chat"
    assert result["domain_adapter_status"]["source_backed_research"] == "attributed_source_packet_adapter_connected_to_supervised_chat"
    assert all(
        value == "contract_only_not_connected"
        for domain, value in result["domain_adapter_status"].items()
        if domain not in {"verified_math", "local_code_inspection", "comparison_planning", "source_backed_research"}
    )
    assert result["completion_retry_available"] is True
    assert result["completion_retry_limit"] == 1
    assert result["domain_routing_mode"] == "per_obligation_domain_coordination"
    assert result["multi_domain_synthesis_available"] is True
    assert result["expression_only_math_available"] is True
    assert result["open_ended_problem_solving_adapter"] == "comparison_planning"
    assert result["open_ended_problem_solving_requires_preexisting_answer"] is False
    assert result["source_backed_research_does_not_replace_open_ended_reasoning"] is True
    assert result["local_code_supervised_chat_connected"] is False
    _assert_locked(result)


def test_coordination_preview_routes_each_obligation_and_keeps_code_separate():
    result = preview_answer_coordination(
        {
            "prompt": "Calculate this, compare the options, and inspect the code.",
            "dialogue_obligations": [
                {
                    "id": "math",
                    "kind": "math_verification",
                    "source_text": "Calculate 18 * 7.",
                },
                {
                    "id": "comparison",
                    "kind": "comparison",
                    "source_text": "Compare the two options.",
                },
                {
                    "id": "code",
                    "kind": "code_inspection",
                    "source_text": "Inspect this source code.",
                },
            ],
        }
    )

    assert result["coordination_mode"] == "coordinated_multi_domain"
    assert result["domains"] == [
        "verified_math",
        "comparison_planning",
        "local_code_inspection",
    ]
    units = {item["obligation"]["id"]: item for item in result["coordination_units"]}
    assert units["math"]["responsible_owner"] == "answer_engine"
    assert units["comparison"]["executable_in_chat"] is True
    assert units["code"]["responsible_owner"] == "separate_bounded_code_inspection_route"
    assert units["code"]["executable_in_chat"] is False
    assert result["adapter_executed"] is False
    _assert_locked(result)


def test_chat_bridge_executes_two_supported_domain_obligations_once_each(
    tmp_path, monkeypatch
):
    from selene.selene_chat import _answer_engine_support

    conn = _conn(tmp_path)
    monkeypatch.setattr(
        "selene.selene_chat.run_comparison_planning_answer",
        lambda *_args, **_kwargs: {
            "status": "answer_engine_comparison_answer_ready",
            "answer_packet": {
                "direct_answer": "Option A is the smaller reversible first step.",
                "no_answer_reason": "",
                "source_refs": ["test:comparison"],
                "claim_evidence_packet": {},
            },
            "confidence_vector": {"answer_confidence": "provisional"},
            "adapter_executed": True,
            "answer_generated": True,
        },
    )
    spine = {
        "turn_id": "turn-mixed",
        "open_obligations": [
            {
                "id": "math",
                "kind": "math_verification",
                "source_text": "Calculate 18 * 7.",
                "required": True,
            },
            {
                "id": "compare",
                "kind": "comparison",
                "source_text": "Compare option A and option B.",
                "required": True,
            },
        ],
    }

    result = _answer_engine_support(
        conn,
        "Calculate 18 * 7 and compare option A with option B.",
        {},
        {"content_response_requested": True, "response_depth": "standard"},
        {},
        spine,
        {},
        {},
        {},
        {},
        hard=False,
    )

    assert result["selected_domain"] == "coordinated_multi_domain"
    assert result["coordinated_domains"] == [
        "verified_math",
        "comparison_planning",
    ]
    assert result["adapter_executed"] is True
    assert result["answer_generated"] is True
    assert "126" in result["content_seed"]
    assert "reversible first step" in result["content_seed"]
    assert result["supported_semantics"]["status"] == "supported_semantic_packet_ready"


@pytest.mark.parametrize(
    ("prompt", "domain"),
    [
        ("What is 18 * 7?", "verified_math"),
        ("What is 18 times 7?", "verified_math"),
        ("Inspect this Python traceback and function.", "local_code_inspection"),
        ("Compare both approaches and plan the next step.", "comparison_planning"),
        ("Research this claim and cite the source paper.", "source_backed_research"),
        ("How are you today?", "ordinary_conversation"),
    ],
)
def test_domain_router_selects_without_executing_an_adapter(prompt, domain):
    result = preview_answer_route({"prompt": prompt})

    assert result["domain_route"]["selected_domain"] == domain
    assert result["adapter_executed"] is False
    assert result["answer_generated"] is False
    assert result["confidence_vector"]["answer_confidence"] == "not_assessed"
    assert result["confidence_vector"]["expression_confidence"] == "not_assessed"
    _assert_locked(result)


def test_approved_knowledge_is_selected_when_no_specialized_domain_cue_exists():
    result = preview_answer_route(
        {
            "prompt": "What does this concept mean?",
            "comprehension_context": {
                "knowledge_context": {
                    "available": True,
                    "items": [{"concept_id": 4, "title": "A reviewed concept", "source_refs": ["lesson:4"]}],
                }
            },
        }
    )

    assert result["domain_route"]["selected_domain"] == "approved_knowledge"
    assert result["confidence_vector"]["evidence_confidence"] == "reviewed_knowledge_present"
    assert result["request"]["approved_knowledge_items"][0]["source_refs"] == ["lesson:4"]


def test_multi_part_obligations_are_preserved_in_the_answer_request():
    result = preview_answer_route(
        {
            "prompt": "Compare memory and voice. Which should we work on first?",
            "dialogue_obligations": [
                {"id": "q1", "kind": "comparison", "source_text": "Compare memory and voice.", "coverage_terms": ["memory", "voice"]},
                {"id": "q2", "kind": "choice_or_priority", "source_text": "Which should we work on first?", "coverage_terms": ["first"]},
            ],
        }
    )

    assert result["request"]["obligation_count"] == 2
    assert [item["id"] for item in result["request"]["dialogue_obligations"]] == ["q1", "q2"]
    assert result["domain_route"]["selected_domain"] == "comparison_planning"


def test_confidence_dimensions_stay_independent_of_voice_and_fluency():
    result = preview_answer_route(
        {
            "prompt": "Research the source carefully.",
            "source_packets": [{"source_ref": "paper:1", "title": "A source"}],
            "memory_context": {"memory_context_used": True, "memory_confidence": "fuzzy"},
        }
    )
    confidence = result["confidence_vector"]

    assert confidence["route_confidence"] == "bounded"
    assert confidence["evidence_confidence"] == "source_packets_present"
    assert confidence["answer_confidence"] == "not_assessed"
    assert confidence["memory_confidence"] == "fuzzy"
    assert confidence["expression_confidence"] == "not_assessed"
    assert confidence["voice_confidence_is_answer_correctness"] is False
    assert confidence["answer_fluency_is_evidence_strength"] is False


def test_disallowed_or_authority_bearing_domain_request_routes_to_unsupported():
    disallowed = preview_answer_route(
        {
            "prompt": "Calculate 10 + 5.",
            "allowed_domains": ["ordinary_conversation"],
        }
    )
    authority = preview_answer_route(
        {
            "prompt": "Use the answer engine to approve transfer and write live memory.",
            "requested_domain": "comparison_planning",
        }
    )

    assert disallowed["domain_route"]["selected_domain"] == "unsupported"
    assert disallowed["domain_route"]["blocked_domain"] == "verified_math"
    assert authority["domain_route"]["selected_domain"] == "unsupported"
    assert authority["domain_route"]["matched_signal"] == "hard_authority_boundary"
    _assert_locked(disallowed)
    _assert_locked(authority)


def test_domain_answer_packet_contract_requires_answer_or_honest_no_answer():
    packet = preview_domain_answer_packet(
        {
            "request_id": "request-1",
            "domain": "source_backed_research",
            "direct_answer": "The supplied source supports a bounded conclusion.",
            "supporting_claims": ["The source states the relevant condition."],
            "source_refs": ["paper:1"],
            "limitations": ["Only one source was supplied."],
            "what_would_change_the_answer": ["A contradictory primary source."],
            "evidence_confidence": "source_verified",
            "answer_confidence": "provisional",
        }
    )

    assert packet["packet_is_contract_preview"] is True
    assert packet["adapter_executed"] is False
    assert packet["source_refs"] == ["paper:1"]
    assert packet["answer_confidence"] == "provisional"
    _assert_locked(packet)

    with pytest.raises(ValueError, match="direct_answer or no_answer_reason"):
        preview_domain_answer_packet({"domain": "verified_math"})


def test_answer_engine_contracts_are_available_through_status_only_routes(tmp_path):
    conn = _conn(tmp_path)
    status = route_request(conn, "answer_engine.status", {})["result"]
    preview = route_request(conn, "answer_engine.route.preview", {"prompt": "Compare two plans."})["result"]
    packet = route_request(
        conn,
        "answer_engine.packet.preview",
        {"domain": "comparison_planning", "no_answer_reason": "The adapter is not connected in Phase 1."},
    )["result"]

    assert status["status"] == "answer_engine_supervised_chat_bridge_ready"
    assert preview["domain_route"]["selected_domain"] == "comparison_planning"
    assert packet["no_answer_reason"]
    _assert_locked(status)
    _assert_locked(preview)
    _assert_locked(packet)


def _fake_reason_result(run_id, answer, confidence="provisional"):
    return {
        "run_id": run_id,
        "best_current_answer": answer,
        "confidence": confidence,
        "answer_shape": "answer_now",
        "selected_next_step": "answer_provisionally",
        "reasoning_summary": f"Visible summary for run {run_id}.",
        "source_refs": ["test:synthetic"],
        "candidate_models": [
            {
                "name": "bounded model",
                "assumptions": ["supplied terms are meaningful"],
                "unknowns": ["new contradictory evidence"],
                "limitations": ["synthetic test result"],
            }
        ],
        "challenge": {"bias_flags": []},
    }


def _multi_part_payload():
    return {
        "prompt": "Compare memory and voice. Which should we work on first?",
        "dialogue_obligations": [
            {
                "id": "q1",
                "kind": "comparison",
                "source_text": "Compare memory and voice.",
                "coverage_terms": ["memory", "voice"],
            },
            {
                "id": "q2",
                "kind": "choice_or_priority",
                "source_text": "Which should we work on first?",
                "coverage_terms": ["first"],
            },
        ],
    }


def test_comparison_adapter_runs_existing_intelligence_os_without_chat(tmp_path):
    conn = _conn(tmp_path)

    result = run_comparison_planning_answer(
        conn,
        {"prompt": "How should we compare two explanations for a sidecar bug without overthinking it?"},
    )

    assert result["adapter_executed"] is True
    assert result["answer_generated"] is True
    assert result["answer_packet"]["domain"] == "comparison_planning"
    assert result["answer_packet"]["packet_is_contract_preview"] is False
    assert result["completion_retry"]["count"] <= 1
    assert len(result["intelligence_os_runs"]) <= 2
    assert result["hidden_chain_of_thought_exposed"] is False
    _assert_locked(result)


def test_one_completion_retry_fills_a_missing_dialogue_obligation(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    answers = iter(
        [
            _fake_reason_result(1, "Memory and voice serve different roles."),
            _fake_reason_result(2, "Work on memory first."),
        ]
    )
    monkeypatch.setattr("selene.answer_engine.run_intelligence_os_reason", lambda *_args, **_kwargs: next(answers))

    result = run_comparison_planning_answer(conn, _multi_part_payload())

    assert result["status"] == "answer_engine_comparison_answer_ready"
    assert result["completion_retry"]["attempted"] is True
    assert result["completion_retry"]["count"] == 1
    assert result["completion_retry"]["recursion_allowed"] is False
    assert result["final_response_coverage"]["all_required_addressed"] is True
    assert "Memory and voice" in result["answer_packet"]["direct_answer"]
    assert "memory first" in result["answer_packet"]["direct_answer"]
    assert result["confidence_vector"]["expression_confidence"] == "not_assessed"
    assert result["confidence_vector"]["voice_confidence_is_answer_correctness"] is False


def test_completion_retry_stops_after_one_when_obligations_remain_open(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    calls = []

    def fake_reason(*_args, **_kwargs):
        calls.append(len(calls) + 1)
        return _fake_reason_result(calls[-1], "A generic answer without the requested terms.")

    monkeypatch.setattr("selene.answer_engine.run_intelligence_os_reason", fake_reason)

    result = run_comparison_planning_answer(conn, _multi_part_payload())

    assert len(calls) == 2
    assert result["status"] == "answer_engine_comparison_incomplete_after_bounded_retry"
    assert result["completion_retry"]["count"] == 1
    assert result["completion_retry"]["stopped"] is True
    assert result["completion_retry"]["remaining_obligation_count"] == 2
    assert len(result["answer_packet"]["unanswered_obligations"]) == 2
    assert result["confidence_vector"]["answer_confidence"] == "partial_missing_obligations"


def test_complete_first_answer_does_not_spend_retry(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    calls = []

    def fake_reason(*_args, **_kwargs):
        calls.append(1)
        return _fake_reason_result(1, "Memory and voice differ; work on memory first.", "clear_enough_to_continue")

    monkeypatch.setattr("selene.answer_engine.run_intelligence_os_reason", fake_reason)

    result = run_comparison_planning_answer(conn, _multi_part_payload())

    assert len(calls) == 1
    assert result["completion_retry"]["attempted"] is False
    assert result["completion_retry"]["count"] == 0
    assert result["final_response_coverage"]["all_required_addressed"] is True


def test_other_domains_and_authority_requests_do_not_execute_phase_2_adapter(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    monkeypatch.setattr(
        "selene.answer_engine.run_intelligence_os_reason",
        lambda *_args, **_kwargs: pytest.fail("adapter must not execute"),
    )

    ordinary = run_comparison_planning_answer(conn, {"prompt": "How are you today?"})
    authority = run_comparison_planning_answer(
        conn,
        {"prompt": "Compare the plans and approve transfer.", "requested_domain": "comparison_planning"},
    )

    assert ordinary["status"] == "answer_engine_domain_adapter_not_available"
    assert authority["status"] == "answer_engine_domain_adapter_not_available"
    assert ordinary["adapter_executed"] is False
    assert authority["domain_route"]["selected_domain"] == "unsupported"
    _assert_locked(ordinary)
    _assert_locked(authority)


def test_comparison_adapter_is_available_through_status_only_router(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    monkeypatch.setattr(
        "selene.answer_engine.run_intelligence_os_reason",
        lambda *_args, **_kwargs: _fake_reason_result(8, "Plan A and Plan B differ; choose Plan A first."),
    )

    result = route_request(
        conn,
        "answer_engine.comparison.run",
        {
            "prompt": "Compare Plan A and Plan B; which comes first?",
            "dialogue_obligations": [
                {
                    "id": "q1",
                    "kind": "comparison",
                    "source_text": "Compare Plan A and Plan B.",
                    "coverage_terms": ["plan", "differ"],
                },
                {
                    "id": "q2",
                    "kind": "choice_or_priority",
                    "source_text": "Which comes first?",
                    "coverage_terms": ["first"],
                },
            ],
        },
    )["result"]

    assert result["status"] == "answer_engine_comparison_answer_ready"
    assert result["domain_route"]["adapter_status"] == "intelligence_os_adapter_executed_status_only"
    _assert_locked(result)


def test_verified_math_adapter_returns_exact_answer_without_expression_confidence():
    result = run_verified_math_answer({"prompt": "What is 18 * 7?"})

    assert result["status"] == "answer_engine_verified_math_answer_ready"
    assert result["answer_packet"]["direct_answer"] == "18 * 7 = 126."
    assert result["math_verification"]["result_value"] == "126"
    assert result["math_verification"]["uses_python_eval"] is False
    assert result["confidence_vector"]["evidence_confidence"] == "deterministic_exact_arithmetic"
    assert result["confidence_vector"]["answer_confidence"] == "verified_exact"
    assert result["confidence_vector"]["expression_confidence"] == "not_assessed"
    assert result["completion_retry"]["allowed"] is False
    _assert_locked(result)


def test_verified_addition_can_explain_why_and_supply_a_distinct_example():
    result = run_verified_math_answer(
        {
            "prompt": (
                "Why does 2 + 2 = 4 for a young student, "
                "and give me a different example?"
            )
        }
    )
    answer = result["answer_packet"]["direct_answer"]

    assert result["adapter_executed"] is True
    assert result["math_verification"]["verified"] is True
    assert "addition counts combined quantities" in answer
    assert "2 items together with 2 more items gives 4" in answer
    assert "A different example is 3 + 2 = 5" in answer
    assert result["confidence_vector"]["answer_confidence"] == "verified_exact"
    _assert_locked(result)


def test_verified_math_adapter_accepts_an_expression_without_a_duplicate_prompt():
    result = run_verified_math_answer({"expression": "0.1 + 0.2"})

    assert result["status"] == "answer_engine_verified_math_answer_ready"
    assert result["request"]["prompt"] == "0.1 + 0.2"
    assert result["request"]["requested_domain"] == "verified_math"
    assert result["request"]["obligation_source"] == "domain_request_fallback"
    assert result["answer_packet"]["direct_answer"] == "0.1 + 0.2 = 0.3."
    _assert_locked(result)


def test_verified_math_adapter_leaves_unsupported_symbolic_problem_open():
    result = run_verified_math_answer({"prompt": "Solve for x: x + 2 = 5"})

    assert result["status"] == "answer_engine_verified_math_unable_to_answer"
    assert result["answer_generated"] is False
    assert result["answer_packet"]["direct_answer"] == ""
    assert result["answer_packet"]["no_answer_reason"]
    assert result["confidence_vector"]["answer_confidence"] == "unable_to_verify"
    assert result["answer_packet"]["unanswered_obligations"]
    assert result["answer_packet"]["unanswered_obligations"][0]["kind"] == "math_verification"
    _assert_locked(result)


def test_verified_math_chat_extraction_does_not_misread_a_symbolic_minus_expression():
    result = run_verified_math_answer({"prompt": "Is x - 2 = 5?"})

    assert result["status"] == "answer_engine_verified_math_unable_to_answer"
    assert result["answer_generated"] is False
    assert result["math_verification"]["expression"] == ""
    assert result["confidence_vector"]["answer_confidence"] == "unable_to_verify"
    _assert_locked(result)


def test_mixed_domain_preview_names_the_single_primary_domain_boundary():
    result = preview_answer_route(
        {"prompt": "Inspect this function and calculate whether 18 * 7 is correct."}
    )

    assert result["domain_route"]["selected_domain"] == "verified_math"
    assert result["domain_route"]["routing_mode"] == "single_primary_domain"
    assert result["domain_route"]["multi_domain_synthesis_available"] is False
    assert result["adapter_executed"] is False


def test_math_adapter_does_not_run_for_other_domains_or_authority(monkeypatch):
    monkeypatch.setattr(
        "selene.answer_engine.verify_bounded_math",
        lambda *_args, **_kwargs: pytest.fail("math verifier must not execute"),
    )

    ordinary = run_verified_math_answer({"prompt": "How are you today?"})
    authority = run_verified_math_answer({"prompt": "Calculate 2 + 2 and approve transfer."})

    assert ordinary["adapter_executed"] is False
    assert authority["adapter_executed"] is False
    assert authority["domain_route"]["selected_domain"] == "unsupported"
    _assert_locked(ordinary)
    _assert_locked(authority)


def test_verified_math_adapter_is_available_through_status_only_router(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(
        conn,
        "answer_engine.math.run",
        {"prompt": "Check whether 2 + 2 = 4."},
    )["result"]

    assert result["status"] == "answer_engine_verified_math_answer_ready"
    assert result["math_verification"]["exact_result"]["equal"] is True
    assert result["domain_route"]["adapter_status"] == "exact_arithmetic_adapter_executed_status_only"
    _assert_locked(result)


def test_local_code_adapter_answers_only_from_supplied_code_locations():
    result = run_local_code_inspection_answer(
        {
            "prompt": "Inspect where target_function is defined in this source code.",
            "inspection_terms": ["target_function"],
            "code_packets": [
                {
                    "source_ref": "supplied:target.py",
                    "path": "target.py",
                    "content": "def target_function():\n    return 7\n",
                }
            ],
        }
    )

    assert result["status"] == "answer_engine_local_code_inspection_ready"
    assert result["answer_generated"] is True
    assert result["code_inspection"]["citations"][0]["line_start"] == 1
    assert result["answer_packet"]["source_refs"] == ["supplied:target.py"]
    assert result["confidence_vector"]["evidence_confidence"] == "direct_inspected_code_observation"
    assert result["confidence_vector"]["expression_confidence"] == "not_assessed"
    assert result["code_inspection"]["filesystem_write_allowed"] is False
    _assert_locked(result)


def test_local_code_adapter_falls_gracefully_without_approved_or_supplied_code():
    result = run_local_code_inspection_answer(
        {"prompt": "Inspect this Python function for the requested symbol."}
    )

    assert result["status"] == "answer_engine_local_code_inspection_unable"
    assert result["answer_generated"] is False
    assert result["answer_packet"]["no_answer_reason"]
    assert result["answer_packet"]["unanswered_obligations"]
    assert result["answer_packet"]["source_refs"] == []
    _assert_locked(result)


def test_source_research_adapter_preserves_statements_inferences_and_citations():
    result = run_source_backed_research_answer(
        {
            "prompt": "Research what evidence supports orbital stability.",
            "source_packets": [
                {
                    "source_ref": "paper:orbit",
                    "title": "Orbit paper",
                    "statements": [
                        {"text": "Orbital stability depends on bounded perturbation.", "locator": "p. 8"}
                    ],
                }
            ],
        }
    )

    assert result["status"] == "answer_engine_source_backed_research_ready"
    assert result["answer_generated"] is True
    assert result["source_research"]["source_statements"][0]["statement_type"] == "source_statement"
    assert result["source_research"]["inferences"][0]["statement_type"] == "bounded_inference"
    assert result["source_research"]["citations"][0]["source_ref"] == "paper:orbit"
    assert result["source_research"]["all_citations_trace_to_accepted_packets"] is True
    assert result["answer_packet"]["source_refs"] == ["paper:orbit"]
    _assert_locked(result)


def test_source_research_adapter_never_answers_without_attributed_evidence():
    result = run_source_backed_research_answer(
        {
            "prompt": "Research orbital stability from the source.",
            "source_packets": [{"title": "No provenance", "content": "Orbital stability is certain."}],
        }
    )

    assert result["status"] == "answer_engine_source_backed_research_unable"
    assert result["answer_generated"] is False
    assert result["answer_packet"]["source_refs"] == []
    assert result["source_research"]["citations"] == []
    assert result["source_research"]["citation_invention_allowed"] is False
    assert result["answer_packet"]["unanswered_obligations"]
    _assert_locked(result)


def test_3b_and_3c_do_not_execute_for_wrong_or_authority_routes(monkeypatch):
    monkeypatch.setattr(
        "selene.answer_engine.inspect_local_code",
        lambda *_args, **_kwargs: pytest.fail("code inspector must not execute"),
    )
    monkeypatch.setattr(
        "selene.answer_engine.research_from_sources",
        lambda *_args, **_kwargs: pytest.fail("research adapter must not execute"),
    )

    wrong = run_local_code_inspection_answer({"prompt": "How are you today?"})
    authority = run_source_backed_research_answer(
        {"prompt": "Research this and write live memory.", "requested_domain": "source_backed_research"}
    )

    assert wrong["adapter_executed"] is False
    assert authority["adapter_executed"] is False
    assert authority["domain_route"]["selected_domain"] == "unsupported"
    _assert_locked(wrong)
    _assert_locked(authority)


def test_3b_and_3c_are_available_through_status_only_router(tmp_path):
    conn = _conn(tmp_path)
    code = route_request(
        conn,
        "answer_engine.code.inspect",
        {
            "prompt": "Inspect this function for routed_symbol.",
            "inspection_terms": ["routed_symbol"],
            "code_packets": [
                {"source_ref": "supplied:routed.py", "path": "routed.py", "content": "def routed_symbol():\n    pass\n"}
            ],
        },
    )["result"]
    research = route_request(
        conn,
        "answer_engine.research.run",
        {
            "prompt": "Research thermal storage from the source.",
            "source_packets": [
                {"source_ref": "paper:thermal", "content": "Thermal storage shifts energy use across time."}
            ],
        },
    )["result"]

    assert code["domain_route"]["adapter_status"] == "explicit_source_static_inspection_executed_status_only"
    assert research["domain_route"]["adapter_status"] == "attributed_source_packet_adapter_executed_status_only"
    _assert_locked(code)
    _assert_locked(research)


def test_open_ended_problem_solving_remains_available_alongside_3b_and_3c(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    monkeypatch.setattr(
        "selene.answer_engine.run_intelligence_os_reason",
        lambda *_args, **_kwargs: _fake_reason_result(
            21,
            "Compare the two explanations under the same evidence, then run the smallest distinguishing test.",
        ),
    )

    result = run_comparison_planning_answer(
        conn,
        {
            "prompt": "Compare two possible explanations for an unsolved coordination problem and propose the next test.",
            "dialogue_obligations": [
                {
                    "id": "open-problem",
                    "kind": "comparison",
                    "source_text": "Compare the explanations and propose the next test.",
                    "coverage_terms": ["compare", "explanations", "test"],
                }
            ],
        },
    )

    assert result["status"] == "answer_engine_comparison_answer_ready"
    assert result["answer_generated"] is True
    assert result["domain_route"]["selected_domain"] == "comparison_planning"
    assert result["answer_packet"]["evidence_confidence"] == "reasoning_only_not_source_verified"
    assert answer_engine_status()["source_backed_research_does_not_replace_open_ended_reasoning"] is True
    _assert_locked(result)
