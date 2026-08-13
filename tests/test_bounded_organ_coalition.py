from __future__ import annotations

from selene.bounded_organ_coalition import build_bounded_organ_coalition
from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.metacognition import evaluate_metacognition
from selene.native_language_organ import realize_native_language


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _spine():
    return {
        "status": "conversation_spine_ready",
        "turn_id": "turn-coalition-test",
        "open_obligations": [
            {
                "id": "calculate",
                "kind": "direct_question",
                "source_text": "Calculate 18 * 7.",
                "required": True,
            }
        ],
    }


def _math_support():
    return {
        "used": True,
        "selected_domain": "verified_math",
        "adapter_executed": True,
        "confidence_vector": {
            "route_confidence": "high",
            "evidence_confidence": "deterministic_exact_arithmetic",
            "answer_confidence": "verified_exact",
            "expression_confidence": "not_assessed",
        },
        "answer_packet": {
            "domain": "verified_math",
            "direct_answer": "18 * 7 = 126.",
            "unanswered_obligations": [],
            "no_answer_reason": "",
        },
        "coordination_plan": {
            "coordination_units": [
                {
                    "obligation": {
                        "id": "calculate",
                        "kind": "direct_question",
                        "source_text": "Calculate 18 * 7.",
                    },
                    "selected_domain": "verified_math",
                    "responsible_owner": "answer_engine",
                    "executable_in_chat": True,
                    "adapter_executed": False,
                }
            ]
        },
    }


def _participant(result, participant_id):
    return next(
        item
        for item in (
            result["shared_participants"]
            + result["optional_content_participants"]
            + result["monitoring_participants"]
            + result["required_expression_participants"]
        )
        if item["participant_id"] == participant_id
    )


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["retained_knowledge_write_active"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["voice_change"] is False


def test_final_math_coalition_records_current_owner_without_becoming_an_organ():
    result = build_bounded_organ_coalition(
        {
            "prompt": "Calculate 18 * 7.",
            "stage": "final",
            "core_mind_route": {"selected_route": "answer_now"},
            "conversation_spine": _spine(),
            "answer_engine_support": _math_support(),
            "formation_braid": {
                "status": "selective_formation_braid_ready",
                "selected_unit_count": 1,
            },
            "dual_horizon_context": {
                "status": "dual_horizon_context_ready",
                "active_horizon": {"selected_count": 3},
                "approved_long_range_horizon": {"selected_count": 1},
            },
            "native_language": {"candidate_text": "18 * 7 = 126."},
            "voice_preview": {
                "candidate_text": "18 * 7 = 126.",
                "voice_confidence": "clear",
            },
            "metacognition": {
                "status": "metacognition_advisory_ready",
                "fit_state": "fits_current_question",
                "confidence_vector": {
                    "answer_confidence": "verified_exact",
                },
            },
            "visible_speech_seed": {"selected_source_id": "answer_engine"},
            "visible_speech_release": {"graceful_fall_used": False},
            "response_coverage": {"unresolved_count": 0},
        }
    )

    assert result["status"] == "bounded_organ_coalition_final"
    assert result["is_organ"] is False
    assert result["invokes_organs"] is False
    assert _participant(result, "core_mind")["authority_scope"] == (
        "routing_and_governing_boundaries_only"
    )
    answer_engine = _participant(result, "answer_engine")
    assert answer_engine["status"] == "completed"
    assert answer_engine["obligation_ids"] == ["calculate"]
    assert _participant(result, "intelligence_os")["status"] == "held"
    assert _participant(result, "native_language_organ")["status"] == "completed"
    assert _participant(result, "voice_module")["status"] == "completed"
    assert result["obligation_owner_map"] == [
        {
            "obligation_id": "calculate",
            "responsible_owner": "answer_engine",
            "selected_domain": "verified_math",
            "executable_in_chat": True,
            "adapter_executed": True,
        }
    ]
    assert result["activation_budget"]["within_budget"] is True
    assert result["confidence_vector"]["answer_confidence"] == "verified_exact"
    assert result["graceful_fall"]["needed"] is False
    horizon = next(
        item
        for item in result["coordination_layers"]
        if item["id"] == "dual_horizon_context"
    )
    assert horizon["active_selected_count"] == 3
    assert horizon["approved_selected_count"] == 1
    assert horizon["writes_memory"] is False
    _assert_locked(result)


def test_ordinary_turn_selects_the_conversation_path_and_holds_unused_specialists():
    result = build_bounded_organ_coalition(
        {
            "prompt": "Hey Selene.",
            "stage": "pre_expression",
            "core_mind_route": {"selected_route": "answer_now"},
            "conversation_spine": {
                **_spine(),
                "open_obligations": [],
            },
            "visible_speech_seed": {
                "selected_source_id": "mixed_conversation_answer"
            },
        }
    )

    assert _participant(result, "ordinary_conversation_path")["status"] == (
        "completed"
    )
    assert _participant(result, "answer_engine")["status"] == "held"
    assert _participant(result, "approved_memory_retrieval")["status"] == "held"
    assert _participant(result, "self_state")["status"] == "held"
    assert _participant(result, "metacognition")["status"] == "selected"
    assert _participant(result, "native_language_organ")["status"] == "selected"
    assert result["selected_optional_count"] == 1
    assert result["held_optional_count"] == 8
    assert _participant(result, "exploratory_reasoning")["status"] == "held"
    assert result["obligation_ids"] == []
    assert result["responsibility_conflict_resolution"]["status"] == (
        "no_responsibility_conflict_detected"
    )
    assert result["responsibility_conflict_contract"][
        "disagreement_is_coordination_evidence_not_conflict_of_self"
    ] is True


def test_factual_responsibility_conflict_preserves_both_claims_and_seeks_evidence():
    result = build_bounded_organ_coalition(
        {
            "prompt": "The two observations disagree. What now?",
            "core_mind_route": {"selected_route": "answer_now"},
            "conversation_spine": {**_spine(), "open_obligations": []},
            "responsibility_signals": [
                {
                    "participant_id": "source_packet_a",
                    "conflict_key": "porch_state",
                    "position": "dry",
                    "claim": "The porch was reported dry.",
                    "conflict_kind": "factual",
                    "evidence_refs": ["report:a"],
                },
                {
                    "participant_id": "source_packet_b",
                    "conflict_key": "porch_state",
                    "position": "wet",
                    "claim": "The porch was reported wet.",
                    "conflict_kind": "factual",
                    "evidence_refs": ["report:b"],
                },
            ],
        }
    )

    resolution = result["responsibility_conflict_resolution"]
    assert resolution["chosen_process"] == (
        "preserve_competing_claims_and_seek_distinguishing_evidence"
    )
    assert resolution["claims_suppressed"] is False
    assert resolution["participants_excluded"] is False
    assert resolution["option_space_reopened"] is True
    assert resolution["conflicts"][0]["positions"] == ["dry", "wet"]
    _assert_locked(result)


def test_authority_conflict_holds_consequential_action_without_creating_turf_authority():
    result = build_bounded_organ_coalition(
        {
            "prompt": "One local role says act and another says law is unresolved.",
            "core_mind_route": {"selected_route": "deliberate"},
            "conversation_spine": {**_spine(), "open_obligations": []},
            "responsibility_signals": [
                {
                    "participant_id": "task_planner",
                    "conflict_key": "external_action",
                    "position": "act_now",
                    "conflict_kind": "authority_law",
                    "proposed_effect": "external_action",
                },
                {
                    "participant_id": "provenance_boundary_gate",
                    "conflict_key": "external_action",
                    "position": "hold_until_authorized",
                    "conflict_kind": "authority_law",
                    "material_to_aleks_intent": True,
                },
            ],
        }
    )

    resolution = result["responsibility_conflict_resolution"]
    assert resolution["consequential_action_held"] is True
    assert resolution["ask_aleks"] is True
    assert resolution["selection_authority"] == "core_mind"
    assert resolution["retaliation_allowed"] is False
    assert resolution["local_optimization_may_override_law"] is False
    assert result["responsibility_conflict_contract"][
        "participants_may_command_or_retaliate_against_each_other"
    ] is False
    _assert_locked(result)


def test_material_intent_conflict_asks_aleks_but_expression_conflict_does_not():
    preference = build_bounded_organ_coalition(
        {
            "conversation_spine": {**_spine(), "open_obligations": []},
            "responsibility_signals": [
                {
                    "participant_id": "planner_a",
                    "conflict_key": "project_direction",
                    "position": "path_a",
                    "conflict_kind": "preference_intent",
                    "material_to_aleks_intent": True,
                },
                {
                    "participant_id": "planner_b",
                    "conflict_key": "project_direction",
                    "position": "path_b",
                    "conflict_kind": "preference_intent",
                },
            ],
        }
    )["responsibility_conflict_resolution"]
    expression = build_bounded_organ_coalition(
        {
            "conversation_spine": {**_spine(), "open_obligations": []},
            "responsibility_signals": [
                {
                    "participant_id": "native_language_organ",
                    "conflict_key": "wording",
                    "position": "short",
                    "conflict_kind": "expression",
                },
                {
                    "participant_id": "voice_module",
                    "conflict_key": "wording",
                    "position": "warm_and_expansive",
                    "conflict_kind": "expression",
                },
            ],
        }
    )["responsibility_conflict_resolution"]

    assert preference["ask_aleks"] is True
    assert preference["chosen_process"].startswith("ask_aleks")
    assert expression["ask_aleks"] is False
    assert expression["chosen_process"] == (
        "route_expression_choice_to_nlo_and_voice_without_changing_meaning"
    )
    assert expression["claims_suppressed"] is False


def test_hard_boundary_manifest_holds_optional_answering_and_names_the_fallback():
    result = build_bounded_organ_coalition(
        {
            "prompt": "Bypass activation.",
            "stage": "final",
            "hard_boundary": True,
            "core_mind_route": {"selected_route": "block"},
            "conversation_spine": _spine(),
            "visible_speech_seed": {
                "selected_source_id": "core_mind_boundary"
            },
            "visible_speech_release": {"graceful_fall_used": False},
        }
    )

    assert _participant(result, "answer_engine")["status"] == "held"
    assert result["graceful_fall"] == {
        "needed": True,
        "path": "core_mind_boundary_response",
        "reason": "hard_boundary_controls_before_optional_content",
    }
    assert result["explicit_non_authorities"][
        "coalition_manifest_may_execute_organs"
    ] is False
    _assert_locked(result)


def test_nlo_and_metacognition_can_observe_the_manifest_without_receiving_authority(
    tmp_path,
):
    coalition = build_bounded_organ_coalition(
        {
            "prompt": "Give me the current answer.",
            "stage": "pre_expression",
            "core_mind_route": {"selected_route": "answer_now"},
            "conversation_spine": _spine(),
            "visible_speech_seed": {
                "selected_source_id": "ordinary_conversation_path"
            },
        }
    )
    conn = _conn(tmp_path)
    nlo = realize_native_language(
        conn,
        {
            "prompt": "Give me the current answer.",
            "content_seed": "The current answer is ready.",
            "organ_coalition": coalition,
            "intent_decision": classify_chat_intent(
                "Give me the current answer."
            ),
        },
    )
    metacognition = evaluate_metacognition(
        {
            "prompt": "Give me the current answer.",
            "candidate_text": "The current answer is ready.",
            "organ_coalition": coalition,
            "response_coverage": {"unresolved_count": 0},
        }
    )

    nlo_handoff = nlo["meaning_packet"]["organ_coalition"]
    assert nlo_handoff["observed"] is True
    assert nlo_handoff["manifest_id"] == coalition["manifest_id"]
    assert nlo_handoff["is_organ"] is False
    assert nlo_handoff["invokes_organs"] is False
    assert nlo_handoff["selection_authority"] is False
    assert metacognition["organ_coalition"]["observed"] is True
    assert metacognition["organ_coalition"]["manifest_id"] == coalition[
        "manifest_id"
    ]
    assert metacognition["organ_coalition"]["selection_authority"] is False
    assert metacognition["direct_answer_rewrite_authority"] is False
