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


def test_discourse_plan_binds_a_supported_next_step_and_preserves_answer_order():
    result = build_supported_discourse_plan(
        {
            "content_seed": (
                "Both plans are reversible. "
                "Plan A is local while Plan B is remote. "
                "Location is the deciding difference. "
                "Test the local plan first."
            ),
            "response_obligations": [
                {
                    "id": "compare",
                    "kind": "comparison",
                    "source_text": "Compare the two plans.",
                    "coverage_terms": ["compare", "plan"],
                    "required": True,
                },
                {
                    "id": "difference",
                    "kind": "comparison",
                    "source_text": "Explain the deciding difference.",
                    "coverage_terms": ["deciding", "difference"],
                    "required": True,
                },
                {
                    "id": "next",
                    "kind": "direct_request",
                    "source_text": "Give the next step.",
                    "coverage_terms": ["next", "step"],
                    "required": True,
                },
            ],
        }
    )

    bindings = {item["obligation_id"]: item for item in result["obligation_bindings"]}
    paragraph_ids = result["paragraph_plan"][0]["content_unit_ids"]

    assert result["all_obligations_grounded"] is True
    assert result["uncovered_obligation_ids"] == []
    assert "content_3" in bindings["difference"]["content_unit_ids"]
    assert bindings["next"]["content_unit_ids"] == ["content_4"]
    assert paragraph_ids == ["content_1", "content_2", "content_3", "content_4"]


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


def test_discourse_spine_carries_purpose_sections_sources_epistemics_and_terminal_stop():
    result = build_supported_discourse_plan(
        {
            "supported_content_units": [
                {
                    "id": "claim",
                    "text": "Use the reversible pilot first.",
                    "role": "thesis",
                    "supported": True,
                    "source_kind": "prompt_grounded_method",
                    "source_refs": ["prompt:pilot"],
                    "certainty": "supported_recommendation",
                    "scope": "current pilot only",
                    "obligation_ids": ["recommend"],
                },
                {
                    "id": "why",
                    "text": "It creates evidence without locking in the design.",
                    "role": "explanation",
                    "supported": True,
                    "source_kind": "verified_domain_answer",
                    "source_refs": ["answer:pilot"],
                    "certainty": "bounded",
                    "scope": "tested conditions",
                    "obligation_ids": ["reason"],
                },
                {
                    "id": "limit",
                    "text": "The result remains local to the tested conditions.",
                    "role": "qualification",
                    "supported": True,
                    "source_kind": "attributed_source",
                    "source_refs": ["source:trial"],
                    "certainty": "attributed",
                    "scope": "source statement",
                },
            ],
            "response_depth": "developed",
            "discourse_purpose": "recommend a bounded next step",
            "audience": "Aleks",
            "register": "technical_conversational",
            "response_obligations": [
                {
                    "id": "recommend",
                    "kind": "choice_or_priority",
                    "source_text": "Which pilot should come first?",
                    "coverage_terms": ["pilot", "first"],
                    "required": True,
                },
                {
                    "id": "reason",
                    "kind": "reason",
                    "source_text": "Explain why.",
                    "coverage_terms": ["evidence"],
                    "required": True,
                },
            ],
            "source_compatibility": {
                "compatible_source_classes": ["reasoning_answer", "domain_answer"],
                "topic_alignment_required_for_content_sources": True,
            },
            "selected_source_class": "reasoning_answer",
            "release_alignment": {"state": "eligible_for_release_check"},
        }
    )

    spine = result["discourse_spine"]
    assert spine["purpose"] == "recommend a bounded next step"
    assert spine["audience"] == "Aleks"
    assert spine["register"] == "technical_conversational"
    assert spine["thesis"]["content_unit_id"] == "claim"
    assert [item["function"] for item in spine["section_plan"]] == [
        "thesis",
        "explanation",
        "qualification",
    ]
    assert all(item["completeness_state"] == "complete_from_supported_units" for item in spine["section_plan"])
    explanation = spine["section_plan"][1]
    assert explanation["source_bindings"] == [
        {"source_kind": "verified_domain_answer", "source_refs": ["answer:pilot"]}
    ]
    assert explanation["epistemic_bindings"] == [
        {"certainty": "bounded", "scope": "tested conditions"}
    ]
    assert spine["source_compatibility"]["selected_source_class"] == "reasoning_answer"
    assert spine["release_alignment"] == {"state": "eligible_for_release_check"}
    assert all(item["correction_state"] == {} for item in spine["section_plan"])
    assert all(
        item["source_compatibility"]["selected_source_class"] == "reasoning_answer"
        for item in spine["section_plan"]
    )
    assert all(
        item["release_alignment"] == {"state": "eligible_for_release_check"}
        for item in spine["section_plan"]
    )
    assert result["stopping_receipt"]["terminal"] is True
    assert result["stopping_receipt"]["generation_pass_count"] == 1
    assert result["stopping_receipt"]["further_generation_allowed"] is False
    assert result["hard_limits"] == {
        "content_units": 30,
        "sections": 8,
        "paragraphs": 8,
        "planning_passes": 1,
    }


def test_discourse_spine_holds_requested_unsupported_roles_instead_of_filling_them():
    result = build_supported_discourse_plan(
        {
            "content_seed": "Memory preserves reviewed continuity.",
            "requested_discourse_roles": ["analogy", "technical_walkthrough"],
            "response_obligations": [
                {
                    "id": "analogy",
                    "kind": "requested_section",
                    "source_text": "Add an analogy.",
                    "coverage_terms": ["analogy"],
                    "required": True,
                    "requested_response_functions": ["analogy"],
                }
            ],
        }
    )

    spine = result["discourse_spine"]
    assert [item["role"] for item in spine["unsupported_role_holds"]] == [
        "analogy",
        "technical_walkthrough",
    ]
    assert all(item["state"] == "held_no_supported_unit" for item in spine["unsupported_role_holds"])
    assert all(item["content_added"] is False for item in spine["unsupported_role_holds"])
    assert spine["section_plan"] == [
        {
            **spine["section_plan"][0],
            "content_unit_ids": ["content_1"],
        }
    ]
    assert result["stopping_receipt"]["reason"] == "unsupported_roles_or_obligations_held_visible"
    assert result["content_generation_allowed"] is False


def test_supported_analogy_role_binds_by_declared_function_without_inventing_content():
    result = build_supported_discourse_plan(
        {
            "supported_content_units": [
                {
                    "id": "answer",
                    "text": "The gate separates review from release.",
                    "role": "thesis",
                    "supported": True,
                },
                {
                    "id": "analogy_unit",
                    "text": "A vestibule provides the same kind of pause between outside and inside.",
                    "role": "analogy",
                    "supported": True,
                    "source_kind": "fictional_invention",
                    "certainty": "illustrative_only",
                    "obligation_ids": ["analogy_request"],
                },
            ],
            "response_obligations": [
                {
                    "id": "analogy_request",
                    "kind": "requested_section",
                    "source_text": "Give an analogy.",
                    "coverage_terms": ["analogy"],
                    "requested_response_functions": ["analogy"],
                    "required": True,
                }
            ],
        }
    )

    assert result["unsupported_role_holds"] == []
    assert result["obligation_bindings"][0]["content_unit_ids"] == ["analogy_unit"]
    assert result["all_obligations_grounded"] is True
    analogy = next(item for item in result["section_plan"] if item["function"] == "analogy")
    assert analogy["epistemic_bindings"] == [
        {"certainty": "illustrative_only", "scope": "current_response"}
    ]


def test_discourse_spine_rejects_an_ineligible_source_before_section_planning():
    result = build_supported_discourse_plan(
        {
            "supported_content_units": [
                {
                    "id": "supported",
                    "text": "The observed result is provisional.",
                    "role": "thesis",
                    "supported": True,
                    "source_kind": "current_session_observation",
                },
                {
                    "id": "hidden_guess",
                    "text": "An unowned claim should not enter the plan.",
                    "role": "explanation",
                    "supported": True,
                    "source_kind": "unowned_generation",
                },
            ]
        }
    )

    assert [item["id"] for item in result["content_units"]] == ["supported"]
    assert result["source_holds"] == [
        {
            "content_unit_id": "hidden_guess",
            "source_kind": "unowned_generation",
            "state": "held_before_discourse_planning",
            "reason": "source_kind_not_eligible_for_supported_discourse",
            "content_entered_plan": False,
        }
    ]


def test_local_section_revision_preserves_other_sections_and_records_ancestry():
    payload = {
        "supported_content_units": [
            {"id": "thesis", "text": "Run the pilot.", "role": "thesis", "supported": True},
            {"id": "reason", "text": "It is reversible.", "role": "explanation", "supported": True},
            {"id": "limit", "text": "The result is local.", "role": "qualification", "supported": True},
        ],
        "response_depth": "developed",
    }
    initial = build_supported_discourse_plan(payload)
    target = initial["discourse_spine"]["section_plan"][1]
    before = {
        item["section_id"]: item["section_fingerprint"]
        for item in initial["discourse_spine"]["section_plan"]
    }

    revised = build_supported_discourse_plan(
        {
            **payload,
            "supported_content_units": [
                *payload["supported_content_units"],
                {
                    "id": "revised_reason",
                    "text": "It is reversible and observable.",
                    "role": "explanation",
                    "supported": True,
                    "source_kind": "prompt_grounded_method",
                },
            ],
            "section_revision": {
                "prior_discourse_spine": initial["discourse_spine"],
                "target_section_id": target["section_id"],
                "replacement_content_unit_ids": ["revised_reason"],
                "revision_reason": "make the supported reason more precise",
            },
        }
    )

    spine = revised["discourse_spine"]
    receipt = spine["local_revision_receipt"]
    after = {item["section_id"]: item for item in spine["section_plan"]}
    assert receipt["status"] == "local_section_revision_applied"
    assert receipt["target_section_id"] == target["section_id"]
    assert receipt["parent_plan_id"] == initial["discourse_spine"]["plan_id"]
    assert receipt["root_plan_id"] == initial["discourse_spine"]["plan_id"]
    assert receipt["revision_pass_count"] == 1
    assert after[target["section_id"]]["content_unit_ids"] == ["revised_reason"]
    assert after[target["section_id"]]["parent_section_fingerprint"] == before[target["section_id"]]
    for section_id in receipt["unchanged_section_ids"]:
        assert after[section_id]["section_fingerprint"] == before[section_id]
    assert receipt["conversation_reset"] is False
    assert receipt["other_sections_changed"] is False
