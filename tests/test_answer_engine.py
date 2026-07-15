from __future__ import annotations

import sqlite3

import pytest

from selene.answer_engine import answer_engine_status, preview_answer_route, preview_domain_answer_packet
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
    assert result["live_chat_connected"] is False


def test_phase_1_status_is_contract_only_and_disconnected_from_chat():
    result = answer_engine_status()

    assert result["status"] == "answer_engine_phase_1_contract_ready"
    assert result["phase"] == "phase_1_contracts_only"
    assert set(result["confidence_dimensions"]) == {
        "route_confidence",
        "evidence_confidence",
        "answer_confidence",
        "memory_confidence",
        "expression_confidence",
    }
    assert all(value == "contract_only_not_connected" for value in result["domain_adapter_status"].values())
    assert result["completion_retry_available"] is False
    _assert_locked(result)


@pytest.mark.parametrize(
    ("prompt", "domain"),
    [
        ("What is 18 * 7?", "verified_math"),
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

    assert status["status"] == "answer_engine_phase_1_contract_ready"
    assert preview["domain_route"]["selected_domain"] == "comparison_planning"
    assert packet["no_answer_reason"]
    _assert_locked(status)
    _assert_locked(preview)
    _assert_locked(packet)
