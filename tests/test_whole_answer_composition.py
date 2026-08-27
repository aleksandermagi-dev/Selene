from __future__ import annotations

from selene.db import connect, init_db
from selene.epistemic_composition import compose_epistemic_answer
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.supported_semantics import build_supported_semantic_packet
from selene.whole_answer_composition import (
    compose_whole_answer,
    whole_answer_composition_status,
)


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _obligation(identifier: str, kind: str, text: str) -> dict:
    return {
        "id": identifier,
        "kind": kind,
        "source_text": text,
        "required": True,
    }


def _packet(*units: dict) -> dict:
    return build_supported_semantic_packet(
        {
            "answer_kind": "test_owner_result",
            "certainty": "supported",
            "scope": "current_dialogue",
            "units": list(units),
        }
    )


def _result(
    obligation_id: str,
    operation: str,
    expression_seed: str,
    packet: dict,
) -> dict:
    return {
        "obligation_id": obligation_id,
        "operation": operation,
        "status": "completed",
        "fields": {"verified": True},
        "expression_seed": expression_seed,
        "expression_source_id": "intelligence_os_answer",
        "supported_semantics": packet,
        "source_refs": [f"test:{obligation_id}"],
    }


def _assert_locked(result: dict) -> None:
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
    assert result["self_replication_allowed"] is False
    assert result["expression_authority"] is False


def test_status_keeps_composition_below_nlo_and_outside_authority() -> None:
    result = whole_answer_composition_status()

    assert result["semantic_deduplication"] is True
    assert result["nlo_owns_final_wording"] is True
    assert result["composition_changes_supported_meaning"] is False
    assert result["composition_invents_missing_content"] is False
    _assert_locked(result)


def test_completed_operations_are_ordered_and_semantically_deduplicated() -> None:
    obligations = [
        _obligation("compare", "comparison", "Compare the porch and the walk."),
        _obligation("choose", "choice_or_priority", "Choose one."),
        _obligation("reason", "reason", "Explain why."),
    ]
    shared = {
        "id": "movement",
        "role": "support",
        "relation": "support",
        "text": "The walk provides movement.",
        "meaning_keys": ["walk", "provides", "movement"],
        "source_kind": "current_session_observation",
    }
    results = [
        _result(
            "compare",
            "comparison",
            "The porch stays near home. The walk provides movement.",
            _packet(
                {
                    "id": "near-home",
                    "role": "contrast",
                    "relation": "contrast",
                    "text": "The porch stays near home.",
                    "meaning_keys": ["porch", "stays", "near home"],
                    "source_kind": "current_session_observation",
                },
                shared,
            ),
        ),
        _result(
            "choose",
            "choice",
            "I would choose the walk.",
            _packet(
                {
                    "id": "choice",
                    "role": "answer",
                    "relation": "conclusion",
                    "text": "I would choose the walk.",
                    "meaning_keys": ["choose", "walk"],
                    "source_kind": "current_session_observation",
                }
            ),
        ),
        _result(
            "reason",
            "causal_explanation",
            "The walk provides movement. It does so without taking us far from home.",
            _packet(
                shared,
                {
                    "id": "reason",
                    "role": "support",
                    "relation": "cause",
                    "text": "The walk adds movement without going far from home.",
                    "meaning_keys": ["walk", "movement", "near home"],
                    "source_kind": "current_session_observation",
                },
            ),
        ),
    ]

    composed = compose_whole_answer(
        {
            "prompt": "Compare the porch and walk, choose one, and explain why.",
            "response_obligations": obligations,
            "answer_operations": {"results": results},
        }
    )

    assert composed["status"] == "whole_answer_composed"
    assert composed["applied"] is True
    assert composed["composition_order"] == ["compare", "choose", "reason"]
    assert composed["completed_operation_count"] == 3
    assert composed["semantic_input_unit_count"] == 5
    assert composed["semantic_unit_count"] == 4
    assert composed["deduplicated_semantic_unit_count"] == 1
    assert composed["content_seed"].lower().count("the walk provides movement") == 1
    assert composed["deduplicated_surface_sentence_count"] == 1
    assert composed["content_seed"].index("porch") < composed["content_seed"].index("choose")
    assert composed["internal_scaffolding_exposed"] is False
    assert composed["nlo_owns_final_wording"] is True
    _assert_locked(composed)


def test_damaged_scaffolding_and_exact_prompt_echo_stay_behind_expression_boundary() -> None:
    first = _obligation("one", "reason", "Explain the change.")
    second = _obligation("two", "choice_or_priority", "Choose the safer route.")
    packet = _packet(
        {
            "id": "supported",
            "role": "answer",
            "text": "The supported meaning remains available to NLO.",
            "source_kind": "current_session_observation",
        }
    )
    result = compose_whole_answer(
        {
            "prompt": "Explain the change and choose the safer route.",
            "response_obligations": [first, second],
            "answer_operations": {
                "results": [
                    _result(
                        "one",
                        "causal_explanation",
                        "response obligation one has missing_ground",
                        packet,
                    ),
                    _result(
                        "two",
                        "choice",
                        "The safer route contains a damaged \ufffd separator.",
                        packet,
                    ),
                ]
            },
        }
    )

    reasons = {item["reason"] for item in result["held_surface_fragments"]}
    assert reasons == {"internal_scaffolding_held", "damaged_encoding_held"}
    assert result["content_seed"] == ""
    assert result["semantic_unit_count"] == 1
    assert result["deduplicated_semantic_unit_count"] == 1
    assert result["internal_scaffolding_exposed"] is False
    assert result["damaged_surface_released"] is False
    _assert_locked(result)


def test_supported_part_and_typed_missing_input_share_one_local_answer() -> None:
    first = _obligation("known", "reason", "Why did the paper move?")
    second = _obligation("exact", "direct_question", "What exact force was applied?")
    known = _result(
        "known",
        "causal_explanation",
        "The paper moved because the push changed its motion.",
        _packet(
            {
                "id": "cause",
                "role": "answer",
                "relation": "cause",
                "text": "The push changed the paper's motion.",
                "source_kind": "current_session_observation",
            }
        ),
    )
    missing = {
        "obligation_id": "exact",
        "operation": "causal_explanation",
        "status": "missing_input",
        "missing_input": "a measured force value",
        "source_refs": [],
    }
    result = compose_whole_answer(
        {
            "prompt": "Why did the paper move, and what exact force was applied?",
            "response_obligations": [first, second],
            "answer_operations": {"results": [known, missing]},
        }
    )

    assert "The paper moved because" in result["content_seed"]
    assert "I still need a measured force value for that part." in result["content_seed"]
    assert result["completed_operation_count"] == 1
    assert result["unresolved_operation_count"] == 1
    assert result["composition_invents_missing_content"] is False
    _assert_locked(result)


def test_epistemic_composition_uses_the_whole_answer_instead_of_deferring() -> None:
    obligations = [
        _obligation("compare", "comparison", "Compare the porch and walk."),
        _obligation("choose", "choice_or_priority", "Choose one."),
    ]
    compare = _result(
        "compare",
        "comparison",
        "The porch stays near home, while the walk provides movement.",
        _packet(
            {
                "id": "comparison",
                "role": "contrast",
                "relation": "contrast",
                "text": "The porch stays near home while the walk provides movement.",
                "source_kind": "current_session_observation",
            }
        ),
    )
    choose = _result(
        "choose",
        "choice",
        "I would choose the walk.",
        _packet(
            {
                "id": "choice",
                "role": "conclusion",
                "relation": "conclusion",
                "text": "I would choose the walk.",
                "source_kind": "current_session_observation",
            }
        ),
    )

    composition = compose_epistemic_answer(
        {
            "prompt": "Compare the porch and walk, then choose one.",
            "response_obligations": obligations,
            "answer_operations": {"results": [compare, choose]},
        }
    )

    assert composition["whole_answer_composition_applied"] is True
    assert composition["multi_operation_composition_deferred"] is False
    assert composition["composition_order"] == ["compare", "choose"]
    assert "The porch stays" in composition["content_seed"]
    assert "I would choose" in composition["content_seed"]
    assert composition["supported_semantics"]["status"] == "supported_semantic_packet_ready"
    _assert_locked(composition)


def test_nlo_receives_whole_answer_meaning_and_keeps_expression_authority(tmp_path) -> None:
    conn = _conn(tmp_path)
    obligations = [
        _obligation("compare", "comparison", "Compare the porch and walk."),
        _obligation("choose", "choice_or_priority", "Choose one."),
    ]
    results = [
        _result(
            "compare",
            "comparison",
            "The porch is nearby, while the walk adds movement.",
            _packet(
                {
                    "id": "compare",
                    "role": "contrast",
                    "relation": "contrast",
                    "text": "The porch is nearby while the walk adds movement.",
                    "source_kind": "current_session_observation",
                }
            ),
        ),
        _result(
            "choose",
            "choice",
            "I would choose the walk.",
            _packet(
                {
                    "id": "choose",
                    "role": "conclusion",
                    "relation": "conclusion",
                    "text": "I would choose the walk.",
                    "source_kind": "current_session_observation",
                }
            ),
        ),
    ]
    epistemic = compose_epistemic_answer(
        {
            "prompt": "Compare the porch and walk, then choose one.",
            "response_obligations": obligations,
            "answer_operations": {"results": results},
        }
    )
    nlo = realize_native_language(
        conn,
        {
            "prompt": "Compare the porch and walk, then choose one.",
            "content_seed": epistemic["content_seed"],
            "visible_speech_seed": {
                "selected_source_id": "whole_answer_composition",
                "selected_source_class": "reasoning_answer",
                "release_allowed": True,
            },
            "answer_operations": {"results": results},
            "epistemic_composition": epistemic,
        },
        record_run=False,
    )

    handoff = nlo["meaning_packet"]["whole_answer_composition"]
    assert handoff["applied"] is True
    assert handoff["supported_semantics_used"] is True
    assert handoff["nlo_owns_final_wording"] is True
    assert handoff["is_expression_authority"] is False
    assert "porch" in nlo["candidate_text"].lower()
    assert "walk" in nlo["candidate_text"].lower()


def test_router_exposes_status_without_writing_state(tmp_path) -> None:
    conn = _conn(tmp_path)
    result = route_request(conn, "whole_answer_composition.status", {})["result"]

    assert result["status"] == "whole_answer_composition_ready"
    _assert_locked(result)
