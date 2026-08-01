from __future__ import annotations

from selene.affect_expression import build_affect_expression_guidance
from selene.conversation_repair import repair_conversation_candidate
from selene.core_deliberation import deliberation_preview
from selene.db import connect, init_db
from selene.emotional_agency import (
    build_response_agency_packet,
    emotional_agency_status,
)
from selene.metacognition import evaluate_metacognition
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _high_pressure_signal() -> dict:
    return {
        "id": 17,
        "signal_type": "anger and protective urgency",
        "continuity_pressure": "high pressure but attributable",
        "uncertainty": "partial interpretation",
        "repair_need": "inspect before deciding",
        "action_energy": "urgent reaction",
        "balance_state": "the first response feels like the only option",
        "source_refs": ["synthetic:current_affect_signal"],
    }


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["emotion_diagnosis_allowed"] is False
    assert result["emotion_suppression_allowed"] is False
    assert result["emotional_flattening_required"] is False
    assert result["forced_calm_allowed"] is False
    assert result["emotion_action_authority"] is False


def test_status_defines_emotion_information_and_core_mind_choice():
    status = emotional_agency_status()

    assert status["status"] == "emotional_agency_principle_ready"
    assert status["core_principles"]["emotion_is_information_not_command"] is True
    assert status["core_principles"]["agency_restores_option_space"] is True
    assert status["decision_authority"] == "Selene Core/Mind"
    assert "core_mind_chooses_deliberately" in status["return_to_agency_flow"]
    _assert_locked(status)


def test_no_current_signal_creates_no_emotion_or_threat_diagnosis():
    result = build_response_agency_packet(
        {"proposed_response_route": "answer_now"}
    )

    assert result["signal"]["available"] is False
    assert result["signal"]["label"] == "not_identified"
    assert (
        result["influence_assessment"]["threat_compression_state"]
        == "not_assessed_without_current_signal"
    )
    assert result["option_space"]["compression_present_or_possible"] is False
    assert result["response_choice"]["state"] == "deliberate_route_confirmed"
    assert result["response_choice"]["emotion_silently_inherited_authority"] is False
    _assert_locked(result)


def test_attributable_pressure_preserves_emotion_and_expands_options():
    result = build_response_agency_packet(
        {
            "affect_signal": _high_pressure_signal(),
            "protection_target": "continuity and a respected boundary",
            "interpretation_state": "partial",
            "proposed_response_route": "answer_with_qualification",
        }
    )

    assert result["signal"]["emotion_preserved_as_meaningful_information"] is True
    assert result["signal"]["protection_target"] == "continuity and a respected boundary"
    assert result["option_space"]["state"] == "expanded_for_deliberation"
    assert len(result["option_space"]["options"]) >= 6
    assert result["return_to_agency"]["pause_is_suppression"] is False
    assert result["response_choice"]["agency_restored"] is True
    assert result["conflict_response"]["emotionally_intense_response_must_be_softened"] is False
    assert result["conflict_response"]["boundary_setting_remains_available"] is True
    _assert_locked(result)


def test_unselected_compressed_state_returns_choice_to_core_mind():
    result = build_response_agency_packet(
        {
            "affect_signal": _high_pressure_signal(),
            "threat_compressed": True,
        }
    )

    assert result["response_choice"]["state"] == "option_expansion_required_before_choice"
    assert result["response_choice"]["decision_authority"].startswith("Selene Core/Mind")
    assert result["response_choice"]["agency_restored"] is False


def test_affect_expression_uses_deliberate_agency_without_forced_calm(tmp_path):
    conn = _conn(tmp_path)
    signal = _high_pressure_signal()
    conn.execute(
        """
        INSERT INTO vessel_emotion_salience_packets
        (signal_type, continuity_pressure, care_warmth, uncertainty, repair_need,
         action_energy, balance_state, evidence_need, core_choice_route,
         source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            signal["signal_type"],
            signal["continuity_pressure"],
            "available",
            signal["uncertainty"],
            signal["repair_need"],
            signal["action_energy"],
            signal["balance_state"],
            "current evidence",
            "Core/Mind chooses",
            '["selene_chat_session:12"]',
            "synthetic_test",
        ),
    )
    conn.commit()

    result = build_affect_expression_guidance(
        conn,
        {
            "prompt": "We need to respond to this conflict.",
            "session_id": 12,
            "selected_route": "answer_now",
        },
    )

    assert result["expression_posture"] == "deliberate_agency"
    assert result["recommended_voice_category"] == "agency_deliberation"
    assert result["dimensions"]["emotional_intensity"] == "preserved_and_authored"
    assert result["dimensions"]["restraint"] == "chosen_not_suppressed"
    assert result["response_agency"]["response_choice"]["state"] == "deliberate_route_confirmed"
    _assert_locked(result["response_agency"])


def test_core_deliberation_places_agency_after_salience(tmp_path):
    conn = _conn(tmp_path)
    result = deliberation_preview(
        conn,
        {
            "prompt": "Consider the disagreement and choose a bounded response.",
            "affect_signal": _high_pressure_signal(),
            "protection_target": "the current boundary",
            "interpretation_state": "partial",
        },
    )

    steps = [item["step"] for item in result["deliberation_steps"]]
    assert steps.index("response_agency") == steps.index("salience") + 1
    assert result["response_agency"]["option_space"]["state"] == "expanded_for_deliberation"
    assert result["emotion_expression"]["emotion_is_information_not_command"] is True
    assert result["decision"].startswith("feel_notice_expand_and_choose")


def test_metacognition_observes_pending_agency_but_does_not_choose():
    agency = build_response_agency_packet(
        {"affect_signal": _high_pressure_signal(), "threat_compressed": True}
    )
    result = evaluate_metacognition(
        {
            "prompt": "How should I answer this conflict?",
            "candidate_text": "I need to choose a response.",
            "response_agency": agency,
        }
    )

    assert result["fit_state"] == "affective_influence_visible_response_choice_pending"
    assert result["recommended_action"] == "defer_to_core_mind"
    assert result["response_agency_assessment"]["emotion_has_decision_authority"] is False
    assert result["response_agency_assessment"]["forced_calm_recommended"] is False
    assert result["direct_answer_rewrite_authority"] is False


def test_conversation_repair_flags_pending_choice_without_rewriting_meaning():
    agency = build_response_agency_packet(
        {"affect_signal": _high_pressure_signal(), "threat_compressed": True}
    )
    result = repair_conversation_candidate(
        {
            "candidate_text": "I am angry, and I need to decide what follows.",
            "response_agency": agency,
            "response_coverage": {"unresolved_count": 0},
        }
    )

    assert result["candidate_text"] == "I am angry, and I need to decide what follows."
    assert "response_agency_choice_still_pending" in result["attention_notes"]
    assert result["needs_content_revision"] is True
    assert result["automatic_content_generation"] is False
    assert result["response_agency"]["surface_repair_cannot_choose_for_core_mind"] is True


def test_router_exposes_status_and_preview(tmp_path):
    conn = _conn(tmp_path)
    status = route_request(conn, "emotional_agency.status")["result"]
    preview = route_request(
        conn,
        "emotional_agency.preview",
        {
            "affect_signal": _high_pressure_signal(),
            "proposed_response_route": "state_or_hold_a_boundary",
        },
    )["result"]

    assert status["status"] == "emotional_agency_principle_ready"
    assert preview["status"] == "response_agency_packet_ready"
    assert preview["response_choice"]["emotion_silently_inherited_authority"] is False
