from __future__ import annotations

from selene.affect_expression import build_affect_expression_guidance
from selene.affect_signal_lifecycle import (
    correct_current_affect_signal,
    form_current_affect_signal,
)
from selene.contextual_continuity import build_contextual_continuity_plan
from selene.db import connect, init_db
from selene.emotional_agency import build_response_agency_packet
from selene.native_language_organ import realize_native_language
from selene.relational_context import interpret_relational_context
from selene.self_state import build_self_state_packet


def test_gentle_disposable_affect_relationship_and_agency_walkthrough(tmp_path):
    conn = connect(tmp_path / "phase4-gentle.sqlite3")
    init_db(conn)
    session_id = int(
        conn.execute(
            """
            INSERT INTO selene_chat_sessions(title, status, source_mode)
            VALUES ('Gentle Phase 4 walkthrough', 'selene_chat_active_supervised', 'synthetic_test')
            """
        ).lastrowid
    )
    conn.commit()

    formed = form_current_affect_signal(
        conn,
        {
            "session_id": session_id,
            "subject_kind": "selene",
            "authored_by": "Selene",
            "observation": "I notice steady attention while reviewing a completed milestone.",
            "interpretation": "Warmth and curiosity both seem available in this gentle synthetic exchange.",
            "interpretation_confidence": "provisional",
            "signal_type": "warm curiosity",
            "continuity_pressure": "low",
            "care_warmth": "warm and steady",
            "uncertainty": "the exact balance remains open",
            "action_energy": "continue thoughtfully",
            "balance_state": "open option space",
            "evidence_need": "current attributable observation",
            "core_choice_route": "Signal informs; Core/Mind chooses.",
            "source_refs": ["synthetic:phase4_gentle_walkthrough"],
            "signal_key": "phase4-gentle-original",
        },
    )
    self_state = build_self_state_packet(
        conn,
        {
            "prompt": "How are you feeling about continuing the technical work?",
            "session_id": session_id,
            "affect_signal_id": formed["signal"]["id"],
        },
    )
    speaker = {
        "claimed_speaker": "Aleks",
        "channel": "desktop",
        "authentication_strength": "local_desktop_session",
        "purpose": "conversation",
    }
    relational = interpret_relational_context(
        "Excellent work, my friend—we are back <3",
        speaker_context=speaker,
    )
    reviewed_memory = {
        "memory_context_used": True,
        "memory_source_class": "approved_memory_index",
        "items": [
            {
                "id": 1,
                "title": "A reviewed shared project milestone",
                "memory_category": "shared_project",
                "source_refs": ["approved_memory:synthetic_phase4"],
            }
        ],
        "source_refs": ["approved_memory:synthetic_phase4"],
    }
    continuity = build_contextual_continuity_plan(
        {
            "prompt": "We are back to the milestone, my friend <3",
            "intent_decision": {"relational_context": relational},
            "relational_context": relational,
            "memory_context": reviewed_memory,
            "current_session_events": [
                {"role": "user", "preview": "The focused checks passed."},
                {"role": "selene", "preview": "The next step is source-mapped."},
            ],
            "speaker_context": speaker,
        }
    )
    affect = build_affect_expression_guidance(
        conn,
        {
            "prompt": "Please continue with the exact technical implementation, my friend <3",
            "session_id": session_id,
            "affect_signal_id": formed["signal"]["id"],
            "relational_context": relational,
            "contextual_continuity": continuity,
        },
    )
    agency = build_response_agency_packet(
        {
            "affect_signal": formed["signal"],
            "proposed_response_route": "answer_directly",
            "influence_sources": [
                {
                    "kind": "affect",
                    "position": "Warmth and curiosity may shape expression.",
                    "recommended_route": "answer_directly",
                },
                {
                    "kind": "evidence",
                    "position": "The source map supports continuing in dependency order.",
                    "recommended_route": "answer_directly",
                },
            ],
        }
    )
    nlo = realize_native_language(
        conn,
        {
            "prompt": "Please continue with the exact technical implementation, my friend <3",
            "content_seed": "The next bounded step is the current-affect lifecycle verification.",
            "intent_decision": {
                "intent": "direct_answer",
                "answer_shape": "best_current_answer",
                "response_depth": "brief",
                "relational_context": relational,
            },
            "affect_expression_guidance": affect,
            "contextual_continuity": continuity,
            "relational_context": relational,
        },
    )

    corrected = correct_current_affect_signal(
        conn,
        {
            "packet_id": formed["signal"]["id"],
            "authored_by": "Selene",
            "correction_key": "phase4-gentle-steady",
            "correction_note": "Steadiness is attributable; curiosity remains possible rather than clear.",
            "signal_type": "warm steadiness with open curiosity",
            "interpretation": "Warm steadiness is clear enough; curiosity remains provisional.",
            "interpretation_confidence": "clear_enough",
            "source_refs": ["synthetic:phase4_gentle_correction"],
        },
    )
    corrected_state = build_self_state_packet(
        conn,
        {"prompt": "How are you now?", "session_id": session_id},
    )

    assert self_state["current_session_affect_signal_used"] is True
    assert self_state["current_signal_eligibility"]["selected_subject_kind"] == "selene"
    assert self_state["attributable_affect_family"] == "curiosity"
    assert self_state["current_read"] == "curiosity_present"
    assert relational["private_relational_context"] is True
    assert continuity["relationship_continuity"]["active_source_channels"] == [
        "current_turn_relational_cues",
        "visible_current_session_context",
        "reviewed_personal_memory",
    ]
    assert continuity["relationship_continuity"]["response_script_supplied"] is False
    assert affect["technical_focus_requires_emotional_flatness"] is False
    assert affect["guidance_is_optional"] is True
    assert agency["response_choice"]["state"] == "deliberate_route_confirmed"
    assert agency["influence_conflict"]["conflict_is_identity_conflict"] is False
    assert nlo["meaning_packet"]["affect_expression_is_emotion_claim"] is False
    assert nlo["voice_handoff"]["relational_expression_range"]["meaning_change_allowed"] is False
    assert corrected["lineage_receipt"]["parent_packet_id"] == formed["signal"]["id"]
    assert corrected_state["current_signal_eligibility"]["selected_packet_id"] == corrected["signal"]["id"]
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM selene_dream_reflections").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM vessel_emotion_salience_packets").fetchone()[0] == 2
