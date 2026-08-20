from __future__ import annotations

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.pragmatic_planner import build_pragmatic_plan, evaluate_response_coverage
from selene.supported_semantics import build_supported_semantic_packet


def _dialogue(questions: list[str]) -> dict:
    loops = [
        {
            "id": f"loop-{index}",
            "question": question,
            "topic": "memory voice",
            "status": "open",
        }
        for index, question in enumerate(questions)
    ]
    return {
        "active_topic": "memory voice",
        "open_loops": loops,
        "new_loop_ids": [item["id"] for item in loops],
        "pragmatics": {
            "question_units": questions,
            "multi_part_prompt": len(questions) > 1,
            "previous_turn_available": False,
            "indirect_request": {"detected": False},
        },
    }


def test_pragmatic_plan_turns_multi_part_prompt_into_visible_obligations():
    questions = ["Can you compare memory and voice?", "What should we build first?"]
    plan = build_pragmatic_plan(
        {
            "prompt": " ".join(questions),
            "dialogue_workspace": _dialogue(questions),
            "content_seed": "Memory holds supported continuity. Voice expresses it naturally.",
        }
    )

    assert [item["kind"] for item in plan["response_obligations"]] == ["comparison", "choice_or_priority"]
    assert [item["loop_id"] for item in plan["response_obligations"]] == ["loop-0", "loop-1"]
    assert len(plan["response_units"]) == 2
    assert plan["hidden_chain_of_thought_exposed"] is False
    assert plan["memory_write_active"] is False


def test_content_light_turn_does_not_create_an_unresolved_answer_from_spine_wording():
    coverage = evaluate_response_coverage(
        {"response_obligations": []},
        "That is good to hear.",
        conversation_spine={
            "intent_class": "direct_content",
            "distinctive_terms": ["awesome"],
            "contextual_follow_up": {},
        },
        supported_semantics={},
    )

    assert coverage["conversation_spine_alignment"]["required"] is True
    assert coverage["conversation_spine_alignment"]["aligned"] is False
    assert coverage["answer_bearing_alignment_required"] is False
    assert coverage["unresolved_count"] == 0
    assert coverage["all_required_addressed"] is True


def test_compound_question_keeps_choice_limitation_and_report_as_separate_obligations():
    question = "Which is more useful, what is its limitation, and what would you report?"
    plan = build_pragmatic_plan(
        {
            "prompt": question,
            "dialogue_workspace": _dialogue([question]),
        }
    )

    assert [item["kind"] for item in plan["response_obligations"]] == [
        "choice_or_priority",
        "limitation",
        "requested_output",
    ]
    generic = evaluate_response_coverage(plan, "A useful choice compares both options on the same dimensions.")
    complete = evaluate_response_coverage(
        plan,
        "The combined measure is more useful. Its limitation is extra collection effort. I would report attendance and wait time.",
    )

    assert generic["all_required_addressed"] is False
    assert generic["unresolved_count"] == 2
    assert complete["all_required_addressed"] is True


def test_structured_summary_request_keeps_each_named_part_inspectable():
    prompt = (
        "Summarize the plan for an organizer in three short parts: the design, the pilot, "
        "and the condition that would make us change course."
    )
    plan = build_pragmatic_plan(
        {
            "prompt": prompt,
            "dialogue_workspace": {
                "active_topic": "festival plan",
                "pragmatics": {
                    "utterance_units": [{"kind": "direct_request", "text": prompt}],
                    "previous_turn_available": True,
                },
            },
        }
    )

    assert [item["coverage_terms"] for item in plan["response_obligations"]] == [
        ["design"],
        ["pilot"],
        ["condition", "make", "change", "course"],
    ]
    partial = evaluate_response_coverage(plan, "Change condition: switch if delays become too costly.")
    assert partial["all_required_addressed"] is False
    assert partial["unresolved_count"] == 2


def test_quantitative_obligation_requires_a_visible_quantity_not_only_topic_words():
    plan = {
        "response_obligations": [
            {
                "id": "jars",
                "kind": "method",
                "source_text": "How many jars are there altogether?",
                "parent_source_text": "Three shelves hold four jars each. How many jars are there altogether?",
                "coverage_terms": ["many", "jars", "altogether"],
                "required": True,
            }
        ]
    }
    prose_only = evaluate_response_coverage(
        plan,
        "Both the number of groups and the number in each group are needed to determine how many jars there are.",
    )
    quantified = evaluate_response_coverage(plan, "There are 12 jars altogether.")

    assert prose_only["all_required_addressed"] is False
    assert quantified["all_required_addressed"] is True


def test_echoed_request_prefix_does_not_satisfy_session_summary_coverage():
    prompt = "Back to teaching: summarize the standard we settled on in two short points."
    plan = build_pragmatic_plan(
        {
            "prompt": prompt,
            "dialogue_workspace": {
                "active_topic": "teaching standard",
                "pragmatics": {
                    "utterance_units": [{"kind": "direct_request", "text": prompt}],
                    "previous_turn_available": True,
                },
            },
        }
    )

    result = evaluate_response_coverage(
        plan,
        "Back to teaching: summarize the standard we settled on in two short points: "
        "This conversation began with a greeting.",
    )

    assert result["all_required_addressed"] is False


def test_analogy_request_keeps_constraint_preservation_separate():
    prompt = (
        "Explain the logic to a new volunteer using one ordinary analogy, without losing the important staffing constraint."
    )
    plan = build_pragmatic_plan(
        {
            "prompt": prompt,
            "dialogue_workspace": {
                "active_topic": "festival staffing",
                "pragmatics": {"utterance_units": [{"kind": "direct_request", "text": prompt}]},
            },
        }
    )

    assert [item["kind"] for item in plan["response_obligations"]] == [
        "analogy",
        "constraint_preservation",
    ]
    generic = evaluate_response_coverage(plan, "The logic can be explained in new language without copying wording.")
    complete = evaluate_response_coverage(
        plan,
        "An ordinary analogy is a small kitchen. The staffing constraint is that two rooms do not equal two staffed activities.",
    )
    assert generic["all_required_addressed"] is False
    assert complete["all_required_addressed"] is True


def test_pragmatic_plan_treats_help_and_correction_as_bounded_not_factual_inference():
    stuck = build_pragmatic_plan(
        {
            "prompt": "I'm stuck on how the memory categories fit together.",
            "dialogue_workspace": {
                "active_topic": "memory categories",
                "pragmatics": {"previous_turn_available": False, "indirect_request": {"detected": False}},
            },
        }
    )
    unsupported_correction = build_pragmatic_plan(
        {
            "prompt": "That doesn't sound right.",
            "dialogue_workspace": {"pragmatics": {"previous_turn_available": False}},
        }
    )
    supported_correction = build_pragmatic_plan(
        {
            "prompt": "That doesn't sound right.",
            "dialogue_workspace": {"pragmatics": {"previous_turn_available": True}},
        }
    )

    assert stuck["implicit_meaning"]["goal"] == "help_work_through"
    assert stuck["implicit_meaning"]["not_treated_as_fact"] is True
    assert unsupported_correction["implicit_meaning"]["inferred"] is False
    assert supported_correction["implicit_meaning"]["goal"] == "invite_correction_or_recheck"


def test_yes_or_no_coverage_survives_one_bounded_acknowledgement():
    plan = {
        "response_obligations": [
            {
                "id": "labels-known",
                "kind": "yes_or_no",
                "source_text": "Do we actually know?",
                "parent_source_text": "Do we actually know whether the labels are in the drawer?",
                "coverage_terms": ["actually", "know"],
                "required": True,
            }
        ]
    }

    coverage = evaluate_response_coverage(
        plan,
        "Got it. Not yet. We don't know whether the labels are in the drawer.",
    )

    assert coverage["all_required_addressed"] is True


def test_collaborative_preface_does_not_become_a_second_content_obligation():
    prompt = (
        "Let's think through a practical idea together. "
        "Walk me through two designs, compare their tradeoffs, and recommend a pilot."
    )
    plan = build_pragmatic_plan(
        {
            "prompt": prompt,
            "dialogue_workspace": {
                "active_topic": "learning festival design",
                "open_loops": [],
                "new_loop_ids": [],
                "pragmatics": {
                    "previous_turn_available": False,
                    "question_units": [],
                    "indirect_request": {"detected": False},
                    "utterance_units": [
                        {"kind": "indirect_request", "text": "Let's think through a practical idea together."},
                        {
                            "kind": "direct_request",
                            "text": "Walk me through two designs, compare their tradeoffs, and recommend a pilot.",
                        },
                    ],
                },
            },
        }
    )

    assert [item["kind"] for item in plan["response_obligations"]] == [
        "method",
        "comparison",
        "choice_or_priority",
    ]
    assert "recommend a pilot" in plan["response_obligations"][-1]["source_text"].lower()


def test_ellipsis_uses_only_bounded_session_reference_or_asks():
    unresolved = build_pragmatic_plan(
        {
            "prompt": "What about the other one?",
            "dialogue_workspace": {"active_topic": "", "pragmatics": {"previous_turn_available": False}},
        }
    )
    resolved = build_pragmatic_plan(
        {
            "prompt": "And that one?",
            "dialogue_workspace": {
                "active_topic": "semantic formation",
                "pragmatics": {
                    "previous_turn_available": True,
                    "resolved_reference": {
                        "token": "that one",
                        "resolved_to": "the semantic formation layer",
                        "source": "immediately_preceding_turn",
                    },
                },
            },
        }
    )

    assert unresolved["ellipsis_resolution"]["confidence"] == "unresolved"
    assert unresolved["answer_strategy"] == "ask_brief_clarifying_question"
    assert resolved["ellipsis_resolution"]["resolved_to"] == "the semantic formation layer"
    assert resolved["answer_strategy"] == "answer_with_visible_bounded_interpretation"

    explicit = build_pragmatic_plan(
        {
            "prompt": "What about caching?",
            "dialogue_workspace": {"active_topic": "database design", "pragmatics": {"previous_turn_available": True}},
        }
    )
    assert explicit["ellipsis_resolution"]["resolved_to"] == "caching"
    assert explicit["ellipsis_resolution"]["source"] == "current_utterance_explicit"


def test_response_coverage_keeps_unanswered_questions_open():
    questions = ["Can you compare memory and voice?", "What should we build first?"]
    plan = build_pragmatic_plan({"prompt": " ".join(questions), "dialogue_workspace": _dialogue(questions)})

    partial = evaluate_response_coverage(plan, "Memory and voice serve different roles.")
    complete = evaluate_response_coverage(
        plan,
        "Memory and voice serve different roles. Memory should come first, then voice can express what it supports.",
    )
    generic = evaluate_response_coverage(plan, "I can help with that.")

    assert partial["answered_loop_ids"] == ["loop-0"]
    assert partial["all_required_addressed"] is False
    assert complete["answered_loop_ids"] == ["loop-0", "loop-1"]
    assert complete["all_required_addressed"] is True
    assert generic["answered_loop_ids"] == []


def test_response_coverage_rejects_answer_shaped_but_unrelated_content():
    question = "What changed in how the reviewed conversation lessons help you handle a back-and-forth?"
    plan = build_pragmatic_plan({"prompt": question, "dialogue_workspace": _dialogue([question])})

    unrelated = evaluate_response_coverage(
        plan,
        "Sequence words organize events or steps in time, while reconstruction retells their order.",
    )

    assert unrelated["addressed_count"] == 0
    assert unrelated["unresolved_count"] == 1
    assert unrelated["all_required_addressed"] is False
    assert unrelated["items"][0]["semantic_alignment_required"] is True


def test_supported_semantic_obligation_id_covers_a_paraphrased_visible_answer():
    obligation = {
        "id": "garden-choice",
        "kind": "choice_or_priority",
        "source_text": "Which garden design should we choose first?",
        "coverage_terms": ["garden", "design", "choose", "first"],
        "required": True,
    }
    packet = build_supported_semantic_packet(
        {
            "answer_kind": "prompt_grounded_choice",
            "units": [
                {
                    "id": "pilot-answer",
                    "role": "answer",
                    "text": "Begin with the reversible pilot.",
                    "obligation_ids": ["garden-choice"],
                    "source_kind": "prompt_grounded_method",
                }
            ],
        }
    )

    coverage = evaluate_response_coverage(
        {"response_obligations": [obligation]},
        "Begin with the reversible pilot.",
        supported_semantics=packet,
    )

    assert coverage["all_required_addressed"] is True
    assert coverage["items"][0]["semantic_addressed"] is True
    assert coverage["items"][0]["coverage_basis"] == "supported_semantics"
    assert coverage["items"][0]["matched_semantic_unit_ids"] == ["pilot-answer"]


def test_semantic_inference_requires_meaning_and_requested_response_function():
    reason_obligation = {
        "id": "pilot-reason",
        "kind": "reason",
        "source_text": "Why does the reversible pilot reduce garden risk?",
        "coverage_terms": ["reversible", "pilot", "garden", "risk"],
        "required": True,
    }
    limit_obligation = {
        "id": "pilot-limit",
        "kind": "limitation",
        "source_text": "What limitation applies to the reversible garden pilot?",
        "coverage_terms": ["limitation", "reversible", "garden", "pilot"],
        "required": True,
    }
    reason_packet = build_supported_semantic_packet(
        {
            "answer_kind": "reason",
            "units": [
                {
                    "id": "risk-reason",
                    "role": "support",
                    "text": "The reversible garden pilot reduces risk because it can be changed after observation.",
                    "source_kind": "prompt_grounded_method",
                }
            ],
        }
    )
    generic_packet = build_supported_semantic_packet(
        {
            "answer_kind": "generic",
            "units": [
                {
                    "id": "pilot-answer",
                    "role": "answer",
                    "text": "The reversible garden pilot can begin now.",
                    "source_kind": "prompt_grounded_method",
                }
            ],
        }
    )

    reason = evaluate_response_coverage(
        {"response_obligations": [reason_obligation]},
        "It lowers the risk because we can revise it after seeing the result.",
        supported_semantics=reason_packet,
    )
    generic_limit = evaluate_response_coverage(
        {"response_obligations": [limit_obligation]},
        "The reversible garden pilot can begin now.",
        supported_semantics=generic_packet,
    )

    assert reason["all_required_addressed"] is True
    assert reason["items"][0]["semantic_addressed"] is True
    assert generic_limit["all_required_addressed"] is False
    assert generic_limit["items"][0]["semantic_addressed"] is False


def test_unsupported_semantic_unit_cannot_claim_obligation_coverage():
    obligation = {
        "id": "source-answer",
        "kind": "direct_question",
        "source_text": "What did the attributed source report?",
        "coverage_terms": ["attributed", "source", "report"],
        "required": True,
    }
    packet = build_supported_semantic_packet(
        {
            "answer_kind": "unverified",
            "units": [
                {
                    "id": "unsupported-claim",
                    "text": "It reported a result.",
                    "supported": False,
                    "obligation_ids": ["source-answer"],
                }
            ],
        }
    )

    coverage = evaluate_response_coverage(
        {"response_obligations": [obligation]},
        "It reported a result.",
        supported_semantics=packet,
    )

    assert coverage["all_required_addressed"] is False
    assert coverage["supported_semantic_coverage"]["packet_supported"] is False


def test_explicit_semantic_obligation_id_does_not_spill_into_a_similar_part():
    obligations = [
        {
            "id": "garden-reason",
            "kind": "reason",
            "source_text": "Why does the garden pilot reduce commitment risk?",
            "coverage_terms": ["garden", "pilot", "commitment", "risk"],
            "required": True,
        },
        {
            "id": "water-reason",
            "kind": "reason",
            "source_text": "Why does the garden pilot reduce water risk?",
            "coverage_terms": ["garden", "pilot", "water", "risk"],
            "required": True,
        },
    ]
    packet = build_supported_semantic_packet(
        {
            "answer_kind": "one_reason",
            "units": [
                {
                    "id": "commitment-reason",
                    "role": "support",
                    "text": "The garden pilot reduces commitment risk because it remains reversible.",
                    "obligation_ids": ["garden-reason"],
                    "source_kind": "prompt_grounded_method",
                }
            ],
        }
    )

    coverage = evaluate_response_coverage(
        {"response_obligations": obligations},
        "It stays reversible, so we can change course.",
        supported_semantics=packet,
    )

    semantic = coverage["supported_semantic_coverage"]
    assert semantic["covered_ids"] == ["garden-reason"]
    assert semantic["uncovered_ids"] == ["water-reason"]
    assert coverage["all_required_addressed"] is False


def test_pragmatic_plan_route_is_status_only(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    result = route_request(
        conn,
        "native_language.pragmatic.plan",
        {"prompt": "I'm not sure how to begin."},
    )["result"]

    assert result["status"] == "pragmatic_plan_ready"
    assert result["activation_change"] == "none"
    assert result["autonomous_action_allowed"] is False


def test_pragmatic_plan_orders_multiple_direct_requests_without_question_marks():
    prompt = "Compare memory and voice. Explain which comes first."
    plan = build_pragmatic_plan(
        {
            "prompt": prompt,
            "dialogue_workspace": {
                "active_topic": "memory voice",
                "pragmatics": {
                    "utterance_units": [
                        {"id": "utterance_1", "text": "Compare memory and voice.", "kind": "direct_request", "position": 0},
                        {"id": "utterance_2", "text": "Explain which comes first.", "kind": "direct_request", "position": 1},
                    ],
                    "previous_turn_available": False,
                },
            },
        }
    )

    assert [item["kind"] for item in plan["response_obligations"]] == ["comparison", "reason"]
    assert plan["obligation_sequence"] == [item["id"] for item in plan["response_obligations"]]
    assert all(item["inference_level"] == "literal_request" for item in plan["response_obligations"])


def test_pragmatic_plan_keeps_correction_scope_separate_from_content_obligations():
    prompt = "Actually, I meant the semantic layer, not the voice layer. Explain why it comes first."
    correction = {
        "detected": True,
        "corrected_meaning": "the semantic layer",
        "replaced_meaning": "the voice layer",
        "scope": "current_session_refinement_only",
        "durable_memory_write": False,
    }
    plan = build_pragmatic_plan(
        {
            "prompt": prompt,
            "dialogue_workspace": {
                "active_topic": "semantic layer",
                "pragmatics": {
                    "utterance_units": [
                        {"id": "utterance_1", "text": "Actually, I meant the semantic layer, not the voice layer.", "kind": "correction", "position": 0},
                        {"id": "utterance_2", "text": "Explain why it comes first.", "kind": "direct_request", "position": 1},
                    ],
                    "correction_refinement": correction,
                    "response_preference": "brief",
                    "previous_turn_available": True,
                },
            },
        }
    )

    assert [item["kind"] for item in plan["response_obligations"]] == ["correction_update", "reason"]
    assert plan["response_constraints"][0] == {
        "kind": "response_depth",
        "value": "brief",
        "scope": "current_session_only",
    }
    assert plan["response_constraints"][1]["kind"] == "correction_scope"
    assert plan["memory_write_active"] is False


def test_short_update_clause_is_owned_by_the_correction_obligation():
    prompt = (
        "Tiny correction: the mail is already sorted; the loose cables are the real mess. "
        "Update your suggestion."
    )
    correction = {
        "detected": True,
        "corrected_meaning": "the mail is already sorted; the loose cables are the real mess",
        "replaced_meaning": "start with the mail",
        "scope": "current_session_refinement_only",
    }
    plan = build_pragmatic_plan(
        {
            "prompt": prompt,
            "dialogue_workspace": {
                "active_topic": "desk plan",
                "pragmatics": {
                    "utterance_units": [
                        {
                            "id": "utterance_1",
                            "text": "Tiny correction: the mail is already sorted; the loose cables are the real mess.",
                            "kind": "correction",
                            "position": 0,
                        },
                        {
                            "id": "utterance_2",
                            "text": "Update your suggestion.",
                            "kind": "direct_request",
                            "position": 1,
                        },
                    ],
                    "correction_refinement": correction,
                },
            },
        }
    )

    assert [item["kind"] for item in plan["response_obligations"]] == [
        "correction_update"
    ]
    assert plan["response_obligations"][0]["goal"] == (
        "acknowledge_and_apply_corrected_meaning"
    )


def test_natural_series_and_compound_question_become_separate_obligations():
    series = (
        "First, give me a short recap, then say how my correction changed the answer, "
        "and finally recommend the next step."
    )
    series_plan = build_pragmatic_plan(
        {
            "prompt": series,
            "dialogue_workspace": {
                "active_topic": "conversation repair",
                "pragmatics": {
                    "utterance_units": [
                        {"id": "utterance_1", "text": series, "kind": "direct_request", "position": 0}
                    ]
                },
            },
        }
    )
    math_plan = build_pragmatic_plan(
        {
            "prompt": "Why does 2+2=4, and give me a different example?",
            "dialogue_workspace": _dialogue(
                ["Why does 2+2=4, and give me a different example?"]
            ),
        }
    )

    assert [item["kind"] for item in series_plan["response_obligations"]] == [
        "direct_request",
        "direct_request",
        "choice_or_priority",
    ]
    assert [item["kind"] for item in math_plan["response_obligations"]] == [
        "reason",
        "direct_question",
    ]


def test_coverage_does_not_accept_unrelated_yes_correction_or_summary_scaffolds():
    yes_plan = build_pragmatic_plan(
        {
            "prompt": "Do you agree that calculus should come before fractions?",
            "dialogue_workspace": _dialogue(
                ["Do you agree that calculus should come before fractions?"]
            ),
        }
    )
    correction_plan = build_pragmatic_plan(
        {
            "prompt": "Actually, I meant conversational uncertainty, not mathematical uncertainty.",
            "dialogue_workspace": {
                "active_topic": "conversational uncertainty",
                "pragmatics": {
                    "utterance_units": [
                        {
                            "id": "utterance_1",
                            "text": "Actually, I meant conversational uncertainty, not mathematical uncertainty.",
                            "kind": "correction",
                            "position": 0,
                        }
                    ],
                    "correction_refinement": {
                        "detected": True,
                        "corrected_meaning": "conversational uncertainty",
                        "replaced_meaning": "mathematical uncertainty",
                    },
                },
            },
        }
    )
    summary_plan = build_pragmatic_plan(
        {
            "prompt": "Before we stop, give me one short recap of this conversation.",
            "dialogue_workspace": _dialogue(
                ["Before we stop, give me one short recap of this conversation."]
            ),
        }
    )

    assert evaluate_response_coverage(
        yes_plan,
        "Calculus is a branch of mathematics.",
    )["all_required_addressed"] is False
    assert evaluate_response_coverage(
        correction_plan,
        "First, sequence words organize steps.",
    )["all_required_addressed"] is False
    assert evaluate_response_coverage(
        summary_plan,
        "I can help with that.",
    )["all_required_addressed"] is False


def test_release_resolution_distinguishes_supported_hold_from_answer():
    plan = {
        "response_obligations": [
            {
                "id": "orbit-reason",
                "kind": "reason",
                "source_text": "Why does the orbit remain stable?",
                "coverage_terms": ["orbit", "stable"],
                "required": True,
            }
        ]
    }
    candidate = (
        "I can't support that reason reliably yet. "
        "I would need a supported mechanism that explains the stable orbit."
    )
    composition = {
        "parts": [
            {
                "obligation_id": "orbit-reason",
                "epistemic_state": "missing_ground",
                "text": candidate,
                "missing_ground": "a supported mechanism or explanatory relationship",
            }
        ]
    }

    coverage = evaluate_response_coverage(
        plan,
        candidate,
        epistemic_composition=composition,
    )

    assert coverage["all_required_addressed"] is False
    assert coverage["all_required_resolved"] is True
    assert coverage["resolved_count"] == 1
    assert coverage["unresolved_release_count"] == 0
    assert coverage["items"][0]["resolution_state"] == "supported_route"
    assert coverage["items"][0]["explicitly_held"] is True
    assert coverage["items"][0]["supported_route_present"] is True
    assert coverage["explicit_holds_are_answers"] is False


def test_release_resolution_does_not_let_unrelated_text_borrow_a_missing_ground_part():
    plan = {
        "response_obligations": [
            {
                "id": "orbit-reason",
                "kind": "reason",
                "source_text": "Why does the orbit remain stable?",
                "coverage_terms": ["orbit", "stable"],
                "required": True,
            }
        ]
    }
    coverage = evaluate_response_coverage(
        plan,
        "The library has several history shelves.",
        epistemic_composition={
            "parts": [
                {
                    "obligation_id": "orbit-reason",
                    "epistemic_state": "missing_ground",
                    "missing_ground": "a supported mechanism",
                }
            ]
        },
    )

    assert coverage["all_required_addressed"] is False
    assert coverage["all_required_resolved"] is False
    assert coverage["items"][0]["resolution_state"] == "unresolved"
