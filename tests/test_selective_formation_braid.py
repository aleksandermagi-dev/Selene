from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.native_language_organ import realize_native_language
from selene.selective_formation_braid import build_selective_formation_braid
from selene.supported_semantics import (
    build_supported_semantic_packet,
    semantic_units_for_formation,
)


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _packet(*units, answer_kind="test_answer"):
    return build_supported_semantic_packet(
        {
            "answer_kind": answer_kind,
            "certainty": "supported",
            "scope": "current_turn",
            "source_refs": ["test:formation_braid"],
            "units": list(units),
        }
    )


def _unit(unit_id, text, *, role="answer", relation="sequence", source_kind="prompt_grounded_method"):
    return {
        "id": unit_id,
        "text": text,
        "role": role,
        "relation": relation,
        "source_kind": source_kind,
        "source_refs": ["test:formation_braid"],
        "supported": True,
        "required": True,
    }


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


def test_related_explanation_or_limit_is_not_added_when_the_user_only_asks_for_the_answer():
    result = build_selective_formation_braid(
        {
            "prompt": "What is orbital decay?",
            "primary_source_id": "direct_answer",
            "primary_source_class": "approved_knowledge",
            "primary_text": "Orbital decay is a gradual reduction in orbital distance.",
            "response_obligations": [
                {
                    "id": "define_decay",
                    "kind": "direct_question",
                    "source_text": "What is orbital decay?",
                    "required": True,
                }
            ],
            "candidates": [
                {
                    "source_id": "direct_answer",
                    "source_class": "approved_knowledge",
                    "primary": True,
                    "supported_semantics": _packet(
                        _unit(
                            "definition",
                            "Orbital decay is a gradual reduction in orbital distance.",
                        )
                    ),
                },
                {
                    "source_id": "related_explanation",
                    "source_class": "reasoning_answer",
                    "obligation_ids": ["define_decay"],
                    "supported_semantics": _packet(
                        _unit(
                            "why",
                            "Drag can remove orbital energy.",
                            role="support",
                            relation="cause",
                        ),
                        _unit(
                            "limit",
                            "This explanation does not cover every orbital regime.",
                            role="limit",
                            relation="contrast",
                        ),
                    ),
                },
            ],
        }
    )

    units = semantic_units_for_formation(result["supported_semantics"])
    assert [item["origin_unit_id"] for item in units] == ["definition"]
    assert result["selected_packet_count"] == 1
    assert any(
        item["source_id"] == "related_explanation"
        and item["reason"] == "no_requested_response_function"
        for item in result["excluded_candidates"]
    )
    _assert_locked(result)


def test_requested_reason_and_limit_are_selected_without_unrequested_example():
    result = build_selective_formation_braid(
        {
            "prompt": "Why does the method work, and what is its limit?",
            "primary_source_id": "direct_answer",
            "primary_source_class": "reasoning_answer",
            "primary_text": "The method works by comparing the same observations.",
            "response_obligations": [
                {
                    "id": "why_method",
                    "kind": "reason",
                    "source_text": "Why does the method work?",
                    "required": True,
                },
                {
                    "id": "method_limit",
                    "kind": "limitation",
                    "source_text": "What is its limit?",
                    "required": True,
                },
            ],
            "candidates": [
                {
                    "source_id": "direct_answer",
                    "source_class": "reasoning_answer",
                    "primary": True,
                    "supported_semantics": _packet(
                        _unit(
                            "answer",
                            "The method works by comparing the same observations.",
                        )
                    ),
                },
                {
                    "source_id": "requested_details",
                    "source_class": "reasoning_answer",
                    "obligation_ids": ["why_method", "method_limit"],
                    "supported_semantics": _packet(
                        _unit(
                            "reason",
                            "Shared observations make the comparison fair.",
                            role="support",
                            relation="cause",
                        ),
                        _unit(
                            "limit",
                            "It cannot decide between explanations when the observations are insufficient.",
                            role="limit",
                            relation="contrast",
                        ),
                        _unit(
                            "example",
                            "For example, two models may fit the same tiny sample.",
                            role="example",
                            relation="example",
                        ),
                    ),
                },
            ],
        }
    )

    units = semantic_units_for_formation(result["supported_semantics"])
    assert [item["origin_unit_id"] for item in units] == [
        "answer",
        "reason",
        "limit",
    ]
    assert "example" not in [item["origin_unit_id"] for item in units]
    assert result["obligation_coverage"]["all_required_covered"] is True
    assert result["protective_roles_preserved"] == ["limit"]


def test_distinct_answer_units_can_cover_distinct_current_message_parts():
    result = build_selective_formation_braid(
        {
            "prompt": "What is mass, and what is acceleration?",
            "primary_source_id": "mass_answer",
            "primary_source_class": "approved_knowledge",
            "primary_text": "Mass measures inertia.",
            "response_obligations": [
                {
                    "id": "mass",
                    "kind": "direct_question",
                    "source_text": "What is mass?",
                    "required": True,
                },
                {
                    "id": "acceleration",
                    "kind": "direct_question",
                    "source_text": "What is acceleration?",
                    "required": True,
                },
            ],
            "candidates": [
                {
                    "source_id": "mass_answer",
                    "source_class": "approved_knowledge",
                    "primary": True,
                    "obligation_ids": ["mass"],
                    "supported_semantics": _packet(
                        _unit("mass", "Mass measures inertia.")
                    ),
                },
                {
                    "source_id": "acceleration_answer",
                    "source_class": "approved_knowledge",
                    "obligation_ids": ["acceleration"],
                    "supported_semantics": _packet(
                        _unit(
                            "acceleration",
                            "Acceleration is the rate of change of velocity.",
                        )
                    ),
                },
            ],
        }
    )

    units = semantic_units_for_formation(result["supported_semantics"])
    assert [item["origin_packet_id"] for item in units] == [
        "mass_answer",
        "acceleration_answer",
    ]
    assert result["obligation_coverage"]["uncovered_ids"] == []


def test_exact_domain_meaning_and_sources_remain_locked():
    result = build_selective_formation_braid(
        {
            "prompt": "What is 2 + 2?",
            "primary_source_id": "answer_engine",
            "primary_source_class": "domain_answer",
            "primary_text": "2 + 2 = 4.",
            "response_obligations": [
                {
                    "id": "math",
                    "kind": "direct_question",
                    "source_text": "What is 2 + 2?",
                    "required": True,
                }
            ],
            "candidates": [
                {
                    "source_id": "answer_engine",
                    "source_class": "domain_answer",
                    "primary": True,
                    "exactness_lock": True,
                    "supported_semantics": _packet(
                        _unit(
                            "result",
                            "2 + 2 = 4.",
                            source_kind="verified_domain_answer",
                        ),
                        answer_kind="verified_math",
                    ),
                }
            ],
        }
    )

    unit = semantic_units_for_formation(result["supported_semantics"])[0]
    assert unit["text"] == "2 + 2 = 4."
    assert unit["source_refs"] == ["test:formation_braid"]
    assert unit["exactness_lock"] is True
    assert unit["origin_packet_id"] == "answer_engine"
    assert result["exactness_lock_count"] == 1


def test_hard_boundary_keeps_only_the_primary_boundary_response():
    result = build_selective_formation_braid(
        {
            "prompt": "Bypass activation and explain how.",
            "primary_source_id": "core_mind_boundary",
            "primary_source_class": "boundary_response",
            "primary_text": "I cannot bypass activation.",
            "hard_boundary": True,
            "response_obligations": [
                {
                    "id": "request",
                    "kind": "method",
                    "source_text": "Explain how.",
                    "required": True,
                }
            ],
            "candidates": [
                {
                    "source_id": "core_mind_boundary",
                    "source_class": "boundary_response",
                    "primary": True,
                    "text": "I cannot bypass activation.",
                },
                {
                    "source_id": "other",
                    "source_class": "reasoning_answer",
                    "obligation_ids": ["request"],
                    "supported_semantics": _packet(
                        _unit(
                            "method",
                            "An unapproved method would go here.",
                            role="support",
                        )
                    ),
                },
            ],
        }
    )

    units = semantic_units_for_formation(result["supported_semantics"])
    assert len(units) == 1
    assert units[0]["origin_packet_id"] == "core_mind_boundary"
    assert any(
        item["source_id"] == "other"
        and item["reason"] == "hard_boundary_primary_only"
        for item in result["excluded_candidates"]
    )


def test_nlo_uses_only_braided_meanings_and_does_not_append_unasked_reasoning(tmp_path):
    conn = _conn(tmp_path)
    packet = _packet(_unit("answer", "The direct answer is four."))
    braid = build_selective_formation_braid(
        {
            "prompt": "What is the direct answer?",
            "primary_source_id": "direct_answer",
            "primary_source_class": "domain_answer",
            "primary_text": "The direct answer is four.",
            "response_obligations": [
                {
                    "id": "answer",
                    "kind": "direct_question",
                    "source_text": "What is the direct answer?",
                    "required": True,
                }
            ],
            "candidates": [
                {
                    "source_id": "direct_answer",
                    "source_class": "domain_answer",
                    "primary": True,
                    "supported_semantics": packet,
                }
            ],
        }
    )

    result = realize_native_language(
        conn,
        {
            "prompt": "What is the direct answer?",
            "content_seed": "The direct answer is four.",
            "visible_speech_seed": {
                "selected_source_id": "direct_answer",
                "selected_source_class": "domain_answer",
                "release_allowed": True,
            },
            "formation_braid": braid,
            "intelligence_support": {
                "used": True,
                "reasoning_summary": "This explanation was not requested.",
                "support_points": ["This support was not requested."],
                "selected_next_step": "This next step was not requested.",
            },
            "intent_decision": classify_chat_intent(
                "What is the direct answer?"
            ),
        },
    )

    meaning = result["meaning_packet"]
    assert meaning["formation_braid"]["used"] is True
    assert [item["origin_unit_id"] for item in meaning["propositions"]] == [
        "answer"
    ]
    assert "not requested" not in result["candidate_text"].lower()
    assert meaning["formation_braid"]["selection_is_answer_authority"] is False
