from __future__ import annotations

import http.client
import json
import threading

from selene.claim_evidence import build_claim_evidence_packet
from selene.db import connect, init_db
from selene.generative_thought_expression import (
    build_generative_thought_expression,
    generative_thought_expression_status,
    realize_generative_thought_expression,
)
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.sidecar import SeleneHandler, SeleneServer
from selene.structural_discovery import build_structural_discovery_packet


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_bounded(payload):
    assert payload["memory_write_active"] is False
    assert payload["identity_change"] is False
    assert payload["personality_change"] is False
    assert payload["governance_change"] is False
    assert payload["authority_change"] is False
    assert payload["training_allowed"] is False
    assert payload["lora_allowed"] is False
    assert payload["autonomous_action_allowed"] is False
    assert payload["hidden_chain_of_thought_exposed"] is False


def _discovery():
    return build_structural_discovery_packet(
        {
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
                    "basis": "current supplied descriptions",
                },
                {
                    "source_role": "biological response",
                    "target_role": "controller output",
                    "relation_preserved": "changes behavior from the measured difference",
                    "basis": "current supplied descriptions",
                },
            ],
            "holds_where": ["Both regulate a response from feedback."],
            "breaks_where": ["Biological growth is outside the controller mapping."],
            "source_refs": ["teaching:feedback", "engineering:controller"],
            "hypothesis": {
                "statement": "The biological model may have influenced the controller design.",
                "discriminating_observations": ["Dated notes would show whether the mapping preceded implementation."],
                "counterexamples": ["An earlier independent controller would weaken the influence claim."],
            },
        }
    )


def test_status_exposes_expression_only_contract():
    status = generative_thought_expression_status()

    assert status["status"] == "generative_thought_expression_contract_ready"
    assert set(status["thought_kinds"]) == {
        "idea",
        "hypothesis",
        "analogy",
        "collaborative_question",
        "revisable_attempt",
    }
    assert status["creates_reasoning"] is False
    assert status["creates_facts"] is False
    _assert_bounded(status)


def test_supported_idea_is_selected_but_unsupported_or_private_idea_is_held():
    result = build_generative_thought_expression(
        {
            "expression_requested": True,
            "thought_candidates": [
                {
                    "kind": "idea",
                    "text": "Try the reversible parser change before widening the grammar.",
                    "why_it_matters": "It isolates the earliest unstable dependency.",
                    "current_context_supported": True,
                },
                {
                    "kind": "idea",
                    "text": "Expose private wording.",
                    "why_it_matters": "It should remain private.",
                    "source_refs": ["private_corpus:message-4"],
                },
                {
                    "kind": "idea",
                    "text": "An ungrounded direction.",
                    "why_it_matters": "It has no basis.",
                },
            ],
        }
    )

    assert result["active"] is True
    assert result["selected_kind"] == "idea"
    assert "reversible parser change" in result["expression_text"]
    assert len(result["held_back_candidates"]) == 2
    assert result["content_added"] is False
    assert result["thought_meaning_created_by_bridge"] is False
    _assert_bounded(result)


def test_hypothesis_keeps_basis_falsifier_counterexample_and_provisional_label():
    claims = build_claim_evidence_packet(
        {
            "claims": [
                {"claim_id": "obs", "claim_type": "observation", "text": "The timing shifts after load increases."},
                {
                    "claim_id": "hyp",
                    "claim_type": "hypothesis",
                    "text": "Queue pressure may be causing the delay.",
                    "basis_claim_ids": ["obs"],
                    "what_would_change": ["Stable timing under the same load would weaken it."],
                    "limitations": ["A separate lock contention event could produce the same symptom."],
                },
            ]
        }
    )
    result = build_generative_thought_expression(
        {
            "expression_requested": True,
            "requested_kind": "hypothesis",
            "claim_evidence_packet": claims,
        }
    )

    selected = result["selected_thought"]
    assert selected["kind"] == "hypothesis"
    assert selected["basis_claim_ids"] == ["obs"]
    assert selected["what_would_change"]
    assert selected["counterexamples"]
    assert selected["provisional"] is True
    assert result["hypothesis_is_conclusion"] is False


def test_held_explicit_request_does_not_fall_through_to_an_unrequested_derived_thought():
    claims = build_claim_evidence_packet(
        {
            "claims": [
                {"claim_id": "obs", "claim_type": "observation", "text": "A visible event occurred."},
                {
                    "claim_id": "hyp",
                    "claim_type": "hypothesis",
                    "text": "A provisional cause may explain it.",
                    "basis_claim_ids": ["obs"],
                    "what_would_change": ["A distinguishing observation could weaken it."],
                    "limitations": ["A competing cause could produce the same event."],
                },
            ]
        }
    )
    result = build_generative_thought_expression(
        {
            "expression_requested": True,
            "thought_candidates": [
                {"kind": "idea", "text": "An unsupported explicit idea.", "why_it_matters": "It was requested."}
            ],
            "claim_evidence_packet": claims,
        }
    )

    assert result["active"] is False
    assert result["selected_thought"] == {}
    assert any(item["kind"] == "hypothesis" for item in result["available_candidates"])


def test_structural_analogy_is_attributable_and_never_upgraded_to_proof():
    discovery = _discovery()
    result = build_generative_thought_expression(
        {
            "expression_requested": True,
            "requested_kind": "analogy",
            "structural_discovery": discovery,
        }
    )

    selected = result["selected_thought"]
    assert selected["origin"] == "structural_discovery"
    assert selected["holds_where"]
    assert selected["breaks_where"]
    assert "not proof" in result["expression_text"]
    assert result["analogy_is_proof"] is False
    assert result["voice_may_change_thought_kind"] is False


def test_revisable_attempt_is_useful_without_failure_or_conclusion_framing():
    result = build_generative_thought_expression(
        {
            "expression_requested": True,
            "thought_candidates": [
                {
                    "kind": "revisable_attempt",
                    "text": "The first mismatch may begin at token normalization.",
                    "current_context_supported": True,
                    "what_would_change": ["A matching normalized stream would reopen this attempt."],
                    "confidence": "tentative",
                }
            ],
        }
    )
    realized = realize_generative_thought_expression("Here is what I can establish.", result)

    assert result["selected_kind"] == "revisable_attempt"
    assert result["attempt_is_failure"] is False
    assert result["attempt_is_conclusion"] is False
    assert "current attempt" in result["expression_text"] or "first pass" in result["expression_text"] or "tentatively" in result["expression_text"]
    assert realized["addition_applied"] is True
    assert realized["explanation_forced"] is False


def test_nlo_unifies_conversational_idea_without_duplicate_or_pressure(tmp_path):
    conn = _conn(tmp_path)
    changes_before = conn.total_changes
    result = realize_native_language(
        conn,
        {
            "prompt": "How should we stabilize this parser?",
            "content_seed": "Start with the smallest reproducible parser fault.",
            "conversational_energy_input": {
                "supported_idea": {
                    "text": "Try the reversible token-boundary change before widening the grammar.",
                    "why_it_matters": "It isolates the earliest unstable dependency.",
                    "relevance": "high",
                    "supported": True,
                    "advances_current_task": True,
                }
            },
        },
        record_run=False,
    )

    thought = result["generative_thought_expression"]
    assert result["version"] == "v31_generative_thought_expression"
    assert thought["selected_kind"] == "idea"
    assert result["candidate_text"].count("reversible token-boundary change") == 1
    assert "express_one_attributable_idea_as_a_possibility" in result["discourse_plan"]["moves"]
    assert result["voice_handoff"]["generative_thought_expression"] == thought
    assert result["voice_handoff"]["voice_may_upgrade_thought_confidence"] is False
    assert result["revision"]["generative_thought_content_added"] is False
    assert conn.total_changes == changes_before


def test_nlo_expresses_one_explicit_revisable_attempt_and_allows_material_question(tmp_path):
    conn = _conn(tmp_path)
    attempt = realize_native_language(
        conn,
        {
            "prompt": "What is your best current read?",
            "content_seed": "The visible mismatch begins after normalization.",
            "generative_thought_input": {
                "expression_requested": True,
                "requested_kind": "revisable_attempt",
                "thought_candidates": [
                    {
                        "kind": "revisable_attempt",
                        "text": "Normalization may be dropping the distinction.",
                        "current_context_supported": True,
                        "what_would_change": ["A preserved normalized trace would reopen this attempt."],
                    }
                ],
            },
        },
        record_run=False,
    )
    question = realize_native_language(
        conn,
        {
            "prompt": "Work with me on distinguishing these models.",
            "content_seed": "The models make different timing predictions.",
            "generative_thought_input": {
                "expression_requested": True,
                "requested_kind": "collaborative_question",
                "thought_candidates": [
                    {
                        "kind": "collaborative_question",
                        "question": "Which timing observation do you have from the device",
                        "current_context_supported": True,
                        "material_to_shared_task": True,
                    }
                ],
            },
        },
        record_run=False,
    )

    assert attempt["generative_thought_expression"]["selected_kind"] == "revisable_attempt"
    assert attempt["candidate_text"].count("Normalization may be dropping") == 1
    assert attempt["revision"]["generative_thought_kind_preserved"] is True
    assert question["discourse_plan"]["question_allowed"] is True
    assert question["candidate_text"].endswith("?")


def test_nlo_natural_close_outranks_optional_explicit_thought(tmp_path):
    conn = _conn(tmp_path)
    result = realize_native_language(
        conn,
        {
            "prompt": "Goodbye for now.",
            "content_seed": "Talk later.",
            "generative_thought_input": {
                "expression_requested": True,
                "thought_candidates": [
                    {
                        "kind": "idea",
                        "text": "We could start another task.",
                        "why_it_matters": "It would continue the exchange.",
                        "current_context_supported": True,
                    }
                ],
            },
        },
        record_run=False,
    )

    assert result["generative_thought_expression"]["active"] is False
    assert "another task" not in result["candidate_text"]


def test_status_preview_and_http_routes_are_read_only(tmp_path):
    conn = _conn(tmp_path)
    payload = {
        "expression_requested": True,
        "thought_candidates": [
            {
                "kind": "collaborative_question",
                "question": "Which observation would distinguish the two models",
                "why_it_matters": "The answer changes which model we keep.",
                "current_context_supported": True,
                "material_to_understanding": True,
            }
        ],
    }
    changes_before = conn.total_changes
    status = route_request(conn, "native_language.generative_thought.status")["result"]
    preview = route_request(conn, "native_language.generative_thought.preview", payload)["result"]

    assert status["status"] == "generative_thought_expression_contract_ready"
    assert preview["selected_kind"] == "collaborative_question"
    assert preview["expression_text"].endswith("?")
    assert conn.total_changes == changes_before

    server = SeleneServer(("127.0.0.1", 0), SeleneHandler, tmp_path / "sidecar.sqlite3")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        client.request("GET", "/api/native-language/generative-thought/status")
        status_response = client.getresponse()
        status_payload = json.loads(status_response.read().decode("utf-8"))
        client.close()

        client = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
        client.request(
            "POST",
            "/api/native-language/generative-thought/preview",
            body=json.dumps(payload),
            headers={"Content-Type": "application/json"},
        )
        preview_response = client.getresponse()
        preview_payload = json.loads(preview_response.read().decode("utf-8"))
        client.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
        server.conn.close()

    assert status_response.status == 200
    assert status_payload["status"] == "generative_thought_expression_contract_ready"
    assert preview_response.status == 200
    assert preview_payload["selected_kind"] == "collaborative_question"
