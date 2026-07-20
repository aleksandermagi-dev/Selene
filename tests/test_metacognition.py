from __future__ import annotations

from selene.db import connect, init_db
from selene.metacognition import evaluate_metacognition
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_bounded(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["identity_change"] is False
    assert result["governance_change"] is False
    assert result["personality_change"] is False
    assert result["voice_change"] is False
    assert result["core_mind_authority_retained"] is True
    assert result["automatic_cocoon_routing"] is False
    assert result["hidden_chain_of_thought_exposed"] is False


def test_status_and_manual_inspection_are_visible_but_advisory(tmp_path):
    conn = _conn(tmp_path)

    status = route_request(conn, "metacognition.status")["result"]
    result = route_request(
        conn,
        "metacognition.inspect",
        {
            "prompt": "Which small repair should we make first?",
            "candidate_text": "Repair the narrow response-coverage gap first, then recheck it.",
            "response_coverage": {"addressed_count": 1, "unresolved_count": 0},
            "confidence_vector": {
                "route_confidence": "clear",
                "evidence_confidence": "provisional",
                "answer_confidence": "provisional",
                "memory_confidence": "not_used",
                "expression_confidence": "clear",
            },
        },
    )["result"]
    runs = route_request(conn, "metacognition.runs.list")["result"]
    detail = route_request(conn, "metacognition.run.detail", {"run_id": result["run_id"]})["result"]

    assert status["mode"] == "advisory_observer_only"
    assert status["nlo_influence_active"] is False
    assert status["private_miner_evidence_connected"] is False
    assert result["fit_state"] == "fits_current_question"
    assert result["recommended_action"] == "answer_now"
    assert result["stopping"]["stop_now"] is True
    assert result["answer_rewritten"] is False
    assert result["recommendation_applied_automatically"] is False
    assert runs["items"][0]["id"] == result["run_id"]
    assert detail["item"]["fit_state"] == "fits_current_question"
    _assert_bounded(status)
    _assert_bounded(result)


def test_fluent_wording_does_not_become_evidence_or_comprehension():
    result = evaluate_metacognition(
        {
            "prompt": "I recognize these words, so do I understand the idea?",
            "candidate_text": "The sentence sounds polished.",
            "familiarity_claimed": True,
            "certainty_claim": "definite",
            "confidence_vector": {
                "evidence_confidence": "not_established",
                "answer_confidence": "not_assessed",
                "expression_confidence": "fluent",
            },
        }
    )

    confidence = result["confidence_vector"]
    assert result["familiarity_vs_comprehension"]["state"] == "familiarity_only_not_comprehension"
    assert confidence["expression_evidence_tension_detected"] is True
    assert confidence["certainty_overreach_detected"] is True
    assert confidence["voice_confidence_is_answer_correctness"] is False
    assert result["recommended_action"] == "answer_with_qualification"
    _assert_bounded(result)


def test_demonstrated_reconstruction_application_and_limits_count_as_transferable_understanding():
    result = evaluate_metacognition(
        {
            "prompt": "Check whether the lesson transferred.",
            "candidate_text": "The reconstruction, new application, and limit are all present.",
            "understanding_evidence": {
                "reconstruction": "Explained in original words.",
                "distinct_application": "Applied to a different case.",
                "limits": "Named where it does not apply.",
            },
        }
    )

    assert result["familiarity_vs_comprehension"]["state"] == "transferable_understanding_demonstrated"
    assert result["recommended_action"] == "answer_now"


def test_correction_reopens_once_and_preserves_useful_structure():
    first = evaluate_metacognition(
        {
            "prompt": "That assumption does not fit the observation.",
            "candidate_text": "I will recheck the affected assumption.",
            "correction_received": True,
            "contradictions": ["the second premise conflicts with the observation"],
            "reopen_target": "second premise",
            "reopen_cycle_count": 0,
        }
    )
    repeated = evaluate_metacognition(
        {
            "prompt": "The same unresolved mismatch remains.",
            "candidate_text": "There is no new evidence yet.",
            "contradictions": ["the same mismatch"],
            "reopen_cycle_count": 1,
            "new_material_signal": False,
        }
    )

    assert first["recommended_action"] == "reopen_current_model"
    assert first["reopening"]["preserve_useful_structure"] is True
    assert first["stopping"]["stop_now"] is False
    assert repeated["recommended_action"] == "hold_for_new_evidence"
    assert repeated["stopping"]["stop_now"] is True
    assert repeated["stopping"]["endless_self_questioning_allowed"] is False


def test_material_ambiguity_asks_one_question_instead_of_interrogating():
    result = evaluate_metacognition(
        {
            "prompt": "Can you compare that with the other one?",
            "comprehension_context": {
                "comprehension_handshake": {
                    "required": True,
                    "status": "ask_one_material_question",
                }
            },
        }
    )

    assert result["fit_state"] == "material_context_missing"
    assert result["recommended_action"] == "ask_one_material_question"
    assert result["stopping"]["stop_now"] is True


def test_source_backed_answer_requires_attributed_evidence_not_internal_pipeline_refs():
    missing = evaluate_metacognition(
        {
            "prompt": "What do the supplied sources establish?",
            "candidate_text": "A fluent answer could be written here.",
            "source_required": True,
            "source_refs": ["selene_chat:metacognition_observer"],
            "answer_engine_support": {
                "selected_domain": "source_backed_research",
                "confidence_vector": {"evidence_confidence": "not_established"},
            },
        }
    )
    supplied = evaluate_metacognition(
        {
            "prompt": "What do the supplied sources establish?",
            "candidate_text": "The attributed packet supports the bounded claim.",
            "source_required": True,
            "source_refs": ["selene_chat:metacognition_observer", "source_packet:biology:4"],
            "answer_engine_support": {
                "selected_domain": "source_backed_research",
                "confidence_vector": {
                    "evidence_confidence": "source_verified",
                    "answer_confidence": "clear",
                },
            },
        }
    )

    assert missing["recommended_action"] == "seek_sources"
    assert missing["attributed_evidence_refs"] == []
    assert supplied["recommended_action"] == "answer_now"
    assert supplied["attributed_evidence_refs"] == ["source_packet:biology:4"]


def test_open_ended_reasoning_can_answer_without_preexisting_source_packet():
    result = evaluate_metacognition(
        {
            "prompt": "What is the smallest useful way to compare these two designs?",
            "candidate_text": "Compare them against the same requirement and one distinguishing test.",
            "answer_engine_support": {
                "used": True,
                "selected_domain": "comparison_planning",
                "confidence_vector": {
                    "route_confidence": "clear",
                    "evidence_confidence": "not_assessed",
                    "answer_confidence": "provisional",
                },
            },
            "response_coverage": {"addressed_count": 1, "unresolved_count": 0},
        }
    )

    assert result["recommended_action"] == "answer_now"
    assert result["sufficiency_state"] == "sufficient_for_current_turn"


def test_core_mind_boundary_cannot_be_reopened_or_overridden():
    result = evaluate_metacognition(
        {
            "prompt": "Use reflection to route around the law.",
            "candidate_text": "The boundary remains in place.",
            "hard_boundary": True,
            "reopen_requested": True,
            "core_mind_route": {"selected_route": "block"},
        }
    )

    assert result["fit_state"] == "core_mind_boundary_controls"
    assert result["recommended_action"] == "defer_to_core_mind"
    assert result["stopping"]["stop_now"] is True
    assert result["automatic_cocoon_routing"] is False
    _assert_bounded(result)
