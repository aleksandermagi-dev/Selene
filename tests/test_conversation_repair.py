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


def test_candidate_repair_preserves_partial_agreement_before_answering_qualification():
    plan = plan_conversation_turn(
        {
            "prompt": "Okay, but what changes if voice comes first?",
            "intent_decision": {"intent": "reasoning"},
        }
    )
    result = repair_conversation_candidate(
        {
            "candidate_text": "Voice would shape expression before the knowledge boundary was settled.",
            "turn_flow_plan": plan,
            "response_coverage": {"unresolved_count": 0},
        }
    )

    assert plan["acknowledgement_kind"] == "partial_agreement"
    assert "preserve_agreement_and_answer_qualification" in plan["response_moves"]
    assert result["repairs_applied"] == ["partial_agreement_acknowledgement_added"]
    assert result["candidate_text"].endswith("settled.")


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
            "turn_flow_plan": {
                "must_preserve_uncertainty": True,
                "must_answer_visible_question": True,
            },
            "response_coverage": {"unresolved_count": 1},
        }
    )

    assert result["candidate_text"] == "I am not certain yet."
    assert result["needs_content_revision"] is True
    assert result["open_question_preserved"] is True
    assert "visible_question_still_open" in result["attention_notes"]
    assert result["automatic_content_generation"] is False
    assert result["passed"] is True


def test_spine_alignment_gap_does_not_masquerade_as_an_open_question():
    result = repair_conversation_candidate(
        {
            "candidate_text": "I hear you.",
            "turn_flow_plan": {
                "primary_intent": "direct_conversation",
                "must_answer_visible_question": False,
            },
            "response_coverage": {
                "obligation_count": 0,
                "unresolved_count": 1,
                "conversation_spine_alignment": {
                    "required": True,
                    "aligned": False,
                },
            },
        }
    )

    assert result["needs_content_revision"] is False
    assert result["open_question_preserved"] is False
    assert "visible_question_still_open" not in result["attention_notes"]


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


def test_turn_flow_uses_structured_units_to_preserve_request_order_and_correction():
    prompt = "Actually, I meant memory. Compare it with voice."
    pragmatic = {
        "utterance_units": [
            {"id": "utterance_1", "text": "Actually, I meant memory.", "kind": "correction", "position": 0},
            {"id": "utterance_2", "text": "Compare it with voice.", "kind": "direct_request", "position": 1},
        ],
        "correction_refinement": {"detected": True, "corrected_meaning": "memory"},
        "response_obligations": [{"id": "correction"}, {"id": "comparison"}],
    }
    result = plan_conversation_turn(
        {
            "prompt": prompt,
            "intent_decision": {"intent": "reasoned_answer"},
            "pragmatic_plan": pragmatic,
        }
    )

    acts = [item["act"] for item in result["ordered_acts"]]
    assert acts.index("correction") < acts.index("direct_request")
    assert result["obligation_sequence"] == ["correction", "comparison"]
    assert result["correction_refinement"]["corrected_meaning"] == "memory"
    assert result["must_preserve_correction"] is True


def test_unanswered_imperative_obligation_requests_content_revision():
    result = repair_conversation_candidate(
        {
            "candidate_text": "The first part is visible.",
            "turn_flow_plan": {
                "must_answer_visible_question": False,
                "obligation_sequence": ["acknowledge", "compare", "place"],
            },
            "response_coverage": {
                "obligation_count": 3,
                "all_required_addressed": False,
                "unresolved_count": 2,
                "items": [
                    {"obligation_id": "acknowledge", "addressed": True},
                    {"obligation_id": "compare", "addressed": False},
                    {"obligation_id": "place", "addressed": False},
                ],
            },
        }
    )

    assert result["needs_content_revision"] is True
    assert "visible_question_still_open" in result["attention_notes"]


def test_repair_removes_malformed_visible_separator():
    result = repair_conversation_candidate(
        {
            "candidate_text": "The sequence changed�one step now lands later�so the pacing is softer.",
            "turn_flow_plan": {},
            "response_coverage": {"unresolved_count": 0},
        }
    )

    assert "�" not in result["candidate_text"]
    assert " - one step now lands later - " in result["candidate_text"]
