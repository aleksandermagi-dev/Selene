from __future__ import annotations

from selene.conversation_repair import plan_conversation_turn, repair_conversation_candidate
from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_mixed_turn_preserves_relational_and_answer_moves():
    result = plan_conversation_turn(
        {
            "prompt": "Thank you, friend. Can you explain why that changed?",
            "intent_decision": {"intent": "reasoned_answer"},
        }
    )

    acts = [item["act"] for item in result["ordered_acts"]]
    assert result["mixed_intent"] is True
    assert "gratitude" in acts
    assert "warm_connection" in acts
    assert "reasoning_request" in acts
    assert "question" in acts
    assert "meet_relational_tone_briefly" in result["response_moves"]
    assert "answer_actual_ask" in result["response_moves"]
    assert result["memory_write_active"] is False
    assert result["hidden_chain_of_thought_exposed"] is False


def test_candidate_repair_acknowledges_correction_without_replacing_answer():
    plan = plan_conversation_turn(
        {
            "prompt": "Actually, I meant the second route. Why is it safer?",
            "intent_decision": {"intent": "reasoned_answer"},
        }
    )
    result = repair_conversation_candidate(
        {
            "candidate_text": "The second route is safer because it keeps the change reviewable",
            "turn_flow_plan": plan,
            "response_coverage": {"unresolved_count": 0},
        }
    )

    assert result["candidate_text"].endswith(".")
    assert "correction_acknowledgement_added" in result["repairs_applied"]
    assert "second route is safer" in result["candidate_text"]
    assert result["meaning_preserved"] is True
    assert result["automatic_content_generation"] is False


def test_candidate_repair_removes_adjacent_duplicate_and_flags_recent_repetition():
    result = repair_conversation_candidate(
        {
            "candidate_text": "We can start here. We can start here.",
            "turn_flow_plan": {},
            "response_coverage": {"unresolved_count": 0},
            "recent_candidates": ["We can start here."],
        }
    )

    assert result["candidate_text"] == "We can start here."
    assert "adjacent_duplicate_sentence_removed" in result["repairs_applied"]
    assert "recent_response_repetition" in result["issues"]
    assert result["needs_rephrase"] is True


def test_open_question_requests_content_revision_without_inventing_answer():
    result = repair_conversation_candidate(
        {
            "candidate_text": "I am not certain yet.",
            "turn_flow_plan": {"must_preserve_uncertainty": True},
            "response_coverage": {"unresolved_count": 1},
        }
    )

    assert result["candidate_text"] == "I am not certain yet."
    assert result["needs_content_revision"] is True
    assert result["open_question_preserved"] is True
    assert "visible_question_still_open" in result["attention_notes"]
    assert result["automatic_content_generation"] is False
    assert result["passed"] is True


def test_hard_boundary_does_not_add_social_preface():
    result = repair_conversation_candidate(
        {
            "candidate_text": "I cannot enable an unsafe action",
            "turn_flow_plan": {
                "mixed_intent": True,
                "acknowledgement_kind": "gratitude",
                "primary_intent": "hard_boundary",
            },
            "hard_boundary": True,
            "response_coverage": {"unresolved_count": 0},
        }
    )

    assert result["candidate_text"] == "I cannot enable an unsafe action."
    assert "gratitude_acknowledgement_added" not in result["repairs_applied"]
    assert result["autonomous_action_allowed"] is False


def test_conversation_repair_routes_are_status_only(tmp_path):
    conn = _conn(tmp_path)
    plan = route_request(
        conn,
        "native_language.turn_flow.plan",
        {"prompt": "Thanks. Can you compare these?", "intent_decision": {"intent": "reasoned_answer"}},
    )["result"]
    repaired = route_request(
        conn,
        "native_language.conversation.repair",
        {
            "candidate_text": "They differ in scope",
            "turn_flow_plan": plan,
            "response_coverage": {"unresolved_count": 0},
        },
    )["result"]

    assert plan["status"] == "conversation_turn_flow_ready"
    assert repaired["status"] == "conversation_candidate_repaired"
    assert repaired["memory_write_active"] is False
    assert repaired["runtime_memory_recall"] is False
    assert repaired["training_allowed"] is False
    assert repaired["autonomous_action_allowed"] is False
