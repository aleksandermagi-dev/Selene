from __future__ import annotations

from selene.discourse_planner import build_supported_discourse_plan


def test_discourse_plan_binds_only_supported_content_to_ordered_obligations():
    result = build_supported_discourse_plan(
        {
            "content_seed": (
                "Memory should be grounded before voice expresses it. "
                "Voice then gives that supported continuity a conversational form."
            ),
            "support_points": ["Ground memory first because expression should not invent continuity."],
            "examples": ["For example, a fluent sentence cannot supply a missing event."],
            "response_depth": "developed",
            "expression_profile": "comparison",
            "response_obligations": [
                {
                    "id": "compare",
                    "kind": "comparison",
                    "source_text": "Compare memory and voice.",
                    "coverage_terms": ["memory", "voice"],
                    "required": True,
                },
                {
                    "id": "priority",
                    "kind": "choice_or_priority",
                    "source_text": "Which comes first?",
                    "coverage_terms": ["comes", "first"],
                    "required": True,
                },
            ],
            "answer_support": {
                "limitations": ["This ordering does not make Voice less important."],
                "what_would_change_the_answer": ["A design that can preserve continuity without grounded memory."],
            },
        }
    )

    assert result["all_obligations_grounded"] is True
    assert [item["obligation_id"] for item in result["obligation_bindings"]] == ["compare", "priority"]
    assert [item["role"] for item in result["paragraph_plan"]] == [
        "answer",
        "development",
        "limit_and_closure",
    ]
    assert result["closure_plan"]["mode"] == "what_would_change"
    assert any(item["role"] == "example" for item in result["content_units"])
    assert result["content_generation_allowed"] is False
    assert result["memory_write_active"] is False
    assert result["hidden_chain_of_thought_exposed"] is False


def test_discourse_plan_leaves_an_unsupported_obligation_visible_without_filler():
    result = build_supported_discourse_plan(
        {
            "content_seed": "Memory preserves reviewed continuity.",
            "response_obligations": [
                {
                    "id": "answer",
                    "kind": "direct_request",
                    "source_text": "Explain memory.",
                    "coverage_terms": ["memory"],
                    "required": True,
                },
                {
                    "id": "analogy",
                    "kind": "direct_request",
                    "source_text": "Give an analogy.",
                    "coverage_terms": ["give", "analogy"],
                    "required": True,
                },
            ],
        }
    )

    assert result["uncovered_obligation_ids"] == ["analogy"]
    assert result["all_obligations_grounded"] is False
    assert [item["text"] for item in result["content_units"]] == ["Memory preserves reviewed continuity."]
    assert result["unsupported_gaps_must_remain_visible"] is True
    assert result["content_generation_allowed"] is False


def test_discourse_plan_binds_explicit_example_and_limit_requests_to_supported_roles():
    result = build_supported_discourse_plan(
        {
            "content_seed": "The pilot is worth running.",
            "examples": ["A one-week trial can compare both approaches."],
            "answer_support": {
                "limitations": ["The result applies only to the tested conditions."]
            },
            "response_obligations": [
                {
                    "id": "example",
                    "kind": "direct_request",
                    "source_text": "Give the example.",
                    "coverage_terms": ["give", "example"],
                    "required": True,
                },
                {
                    "id": "limit",
                    "kind": "direct_request",
                    "source_text": "State the limit.",
                    "coverage_terms": ["state", "limit"],
                    "required": True,
                },
            ],
        }
    )

    bindings = {item["obligation_id"]: item for item in result["obligation_bindings"]}
    units = {item["id"]: item for item in result["content_units"]}

    assert result["all_obligations_grounded"] is True
    assert result["uncovered_obligation_ids"] == []
    assert units[bindings["example"]["content_unit_ids"][0]]["role"] == "example"
    assert units[bindings["limit"]["content_unit_ids"][0]]["role"] == "limitation"


def test_developed_discourse_does_not_create_empty_paragraphs_to_reach_a_target():
    result = build_supported_discourse_plan(
        {
            "content_seed": "Use one shared-schedule pilot and compare attendance, wait time, and staffing strain.",
            "response_depth": "developed",
        }
    )

    assert [item["role"] for item in result["paragraph_plan"]] == ["answer"]
    assert result["closure_plan"]["mode"] == "stop_after_supported_content"


def test_discourse_plan_keeps_correction_content_session_scoped():
    result = build_supported_discourse_plan(
        {
            "content_seed": "Memory and voice have different roles.",
            "response_obligations": [
                {
                    "id": "correction",
                    "kind": "correction_update",
                    "source_text": "I meant memory, not voice.",
                    "coverage_terms": ["memory"],
                    "required": True,
                }
            ],
            "correction_refinement": {
                "detected": True,
                "corrected_meaning": "memory",
                "replaced_meaning": "voice",
            },
        }
    )

    correction = next(item for item in result["content_units"] if item["role"] == "correction")
    assert correction["text"] == "memory rather than voice"
    assert correction["source"] == "current_session_correction"
    assert result["obligation_bindings"][0]["grounded"] is True
    assert result["runtime_memory_recall"] is False


def test_discourse_plan_preserves_thread_traversal_and_dependency_bindings():
    braid = {
        "braided": True,
        "turn_traversal": [
            {"index": 1, "thread_id": "x", "action": "start"},
            {"index": 2, "thread_id": "y", "action": "branch"},
            {"index": 3, "thread_id": "x", "action": "revise_with_dependency", "dependency_thread_id": "y"},
        ],
    }
    result = build_supported_discourse_plan(
        {
            "content_seed": "Place the beds first. Check the water schedule. Revise bed spacing from that schedule.",
            "response_obligations": [
                {
                    "id": "x-start",
                    "source_text": "Place the beds.",
                    "coverage_terms": ["place", "beds"],
                    "thread_id": "x",
                    "thread_action": "start",
                    "thread_traversal_index": 1,
                },
                {
                    "id": "y",
                    "source_text": "Check the water schedule.",
                    "coverage_terms": ["water", "schedule"],
                    "thread_id": "y",
                    "thread_action": "branch",
                    "thread_traversal_index": 2,
                },
                {
                    "id": "x-return",
                    "source_text": "Revise bed spacing.",
                    "coverage_terms": ["revise", "spacing"],
                    "thread_id": "x",
                    "thread_action": "revise_with_dependency",
                    "thread_traversal_index": 3,
                    "dependency_thread_id": "y",
                },
            ],
            "thread_braid": braid,
        }
    )

    assert result["thread_traversal"] == braid["turn_traversal"]
    assert [item["thread_action"] for item in result["thread_obligation_bindings"]] == [
        "start",
        "branch",
        "revise_with_dependency",
    ]
    assert result["thread_obligation_bindings"][-1]["dependency_thread_id"] == "y"
    assert result["content_generation_allowed"] is False
