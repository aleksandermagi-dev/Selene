from __future__ import annotations

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.pragmatic_planner import build_pragmatic_plan, evaluate_response_coverage


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
