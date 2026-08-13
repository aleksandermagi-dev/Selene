from __future__ import annotations

from selene.claim_evidence import build_claim_evidence_packet
from selene.conversational_contribution import (
    build_conversational_contribution_packet,
    conversational_contribution_status,
)
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.selene_chat import _conversational_energy_input


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_bounded(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["out_of_turn_automatic_speech_allowed"] is False


def _comprehension():
    return {
        "knowledge_context": {
            "answer_eligible_items": [
                {
                    "id": 17,
                    "central_claim": "A stable test isolates one changing variable.",
                    "relationships": [
                        "Reversible changes make the earliest unstable dependency easier to identify."
                    ],
                    "source_refs": ["teaching_item:17"],
                    "confidence": "reviewed",
                }
            ]
        }
    }


def test_status_allows_bounded_responsive_contribution_without_permission_phrase():
    status = conversational_contribution_status()

    assert status["status"] == "conversational_contribution_engine_ready"
    assert status["responsive_contribution_allowed"] is True
    assert status["explicit_invitation_required"] is False
    assert status["out_of_turn_initiative_allowed"] is False
    assert status["maximum_optional_contributions"] == 1
    _assert_bounded(status)


def test_approved_relationship_can_be_selected_without_explicit_invitation():
    result = build_conversational_contribution_packet(
        {
            "content_seed": "Start with the smallest stable test.",
            "comprehension_context": _comprehension(),
        }
    )

    assert result["status"] == "conversational_contribution_selected"
    assert result["explicitly_invited"] is False
    assert result["selected_kind"] == "connection"
    assert result["selected_contribution"]["origin"] == "approved_knowledge_relationship"
    assert "supported_connection" in result["energy_handoff"]
    assert result["selection_count"] == 1
    _assert_bounded(result)


def test_recently_expressed_or_answered_meaning_is_not_repeated():
    relationship = "Reversible changes make the earliest unstable dependency easier to identify."
    in_answer = build_conversational_contribution_packet(
        {
            "content_seed": relationship,
            "comprehension_context": _comprehension(),
        }
    )
    recent = build_conversational_contribution_packet(
        {
            "content_seed": "Use the smallest stable test.",
            "recent_assistant_texts": [relationship],
            "comprehension_context": _comprehension(),
        }
    )

    assert in_answer["selection_count"] == 0
    assert recent["selection_count"] == 0
    assert any(
        item["reason"] == "meaning_already_present_in_answer"
        for item in in_answer["held_back_candidates"]
    )
    assert any(
        item["reason"] == "meaning_repeats_recent_selene_expression"
        for item in recent["held_back_candidates"]
    )


def test_private_or_unsupported_candidate_is_held_without_falling_through():
    result = build_conversational_contribution_packet(
        {
            "upstream_candidates": [
                {
                    "kind": "idea",
                    "text": "Repeat a private line.",
                    "why_it_matters": "It should remain private.",
                    "source_refs": ["private_corpus:message-9"],
                },
                {
                    "kind": "idea",
                    "text": "An unsupported direction.",
                    "why_it_matters": "There is no basis.",
                },
            ]
        }
    )

    assert result["selection_count"] == 0
    assert result["candidate_count"] == 0
    assert len(result["held_back_candidates"]) == 2
    _assert_bounded(result)


def test_hard_boundary_quiet_and_interruption_leave_no_contribution_room():
    base = {
        "content_seed": "The direct answer remains available.",
        "comprehension_context": _comprehension(),
    }
    hard = build_conversational_contribution_packet({**base, "hard_boundary": True})
    quiet = build_conversational_contribution_packet({**base, "requested_posture": "quiet"})
    interrupted = build_conversational_contribution_packet(
        {**base, "interruption_kind": "interruption"}
    )

    assert hard["selection_count"] == 0
    assert quiet["selection_count"] == 0
    assert interrupted["selection_count"] == 0
    assert hard["conversational_room_blocker"].startswith("hard_boundary")


def test_supported_hypothesis_uses_generative_thought_handoff_and_stays_provisional():
    claims = build_claim_evidence_packet(
        {
            "claims": [
                {
                    "claim_id": "obs",
                    "claim_type": "observation",
                    "text": "The delay begins after normalization.",
                },
                {
                    "claim_id": "hyp",
                    "claim_type": "hypothesis",
                    "text": "Normalization may be dropping one distinction.",
                    "basis_claim_ids": ["obs"],
                    "what_would_change": [
                        "A trace preserving the distinction would weaken this model."
                    ],
                    "limitations": [
                        "A later parser stage could produce the same visible delay."
                    ],
                },
            ]
        }
    )
    result = build_conversational_contribution_packet(
        {
            "content_seed": "The visible delay begins after normalization.",
            "claim_evidence_packet": claims,
            "explicitly_invited": True,
        }
    )

    assert result["selected_kind"] == "hypothesis"
    handoff = result["generative_thought_handoff"]
    assert handoff["requested_kind"] == "hypothesis"
    assert handoff["thought_candidates"][0]["what_would_change"]
    assert handoff["thought_candidates"][0]["counterexamples"]


def test_callback_requires_a_real_thread_return_and_visible_session_landmark():
    context = {
        "session_landmarks": [
            {
                "id": "landmark-1",
                "summary": "The reversible pilot should come first.",
                "thread_id": "garden",
            }
        ],
        "thread_braid": {
            "active_thread_id": "garden",
            "turn_traversal": [{"action": "resume", "thread_id": "garden"}],
        },
    }
    selected = build_conversational_contribution_packet(
        {"content_seed": "We are back on the garden plan.", "conversation_context": context}
    )
    absent = build_conversational_contribution_packet(
        {
            "content_seed": "We are still on the garden plan.",
            "conversation_context": {
                **context,
                "thread_braid": {"active_thread_id": "garden", "turn_traversal": []},
            },
        }
    )

    assert selected["selected_kind"] == "callback"
    assert selected["selected_contribution"]["origin"] == "current_session_landmark"
    assert absent["selection_count"] == 0


def test_chat_handoff_and_nlo_realize_one_selected_connection(tmp_path):
    conn = _conn(tmp_path)
    packet = build_conversational_contribution_packet(
        {
            "content_seed": "Start with the smallest stable test.",
            "comprehension_context": _comprehension(),
        }
    )
    energy_input = _conversational_energy_input(
        {},
        intent_decision={"social_turn": False},
        intelligence_support={},
        answer_engine_support={},
        comprehension={"present_in_conversation": True},
        conversation_context={},
        content_seed="Start with the smallest stable test.",
        hard_boundary=False,
        conversational_contribution=packet,
    )
    result = realize_native_language(
        conn,
        {
            "prompt": "How should we approach this test?",
            "content_seed": "Start with the smallest stable test.",
            "conversational_energy_input": energy_input,
        },
        record_run=False,
    )

    assert result["discourse_plan"]["conversational_energy"]["selected_act"] == (
        "answer_and_surface_supported_connection"
    )
    assert result["candidate_text"].count("Reversible changes") == 1


def test_status_and_preview_router_paths_are_read_only(tmp_path):
    conn = _conn(tmp_path)
    changes_before = conn.total_changes
    status_response = route_request(conn, "conversational_contribution.status", {})
    preview_response = route_request(
        conn,
        "conversational_contribution.preview",
        {
            "upstream_candidates": [
                {
                    "kind": "idea",
                    "text": "Try the reversible path first.",
                    "why_it_matters": "It isolates the smallest changing piece.",
                    "current_context_supported": True,
                }
            ]
        },
    )

    assert status_response["result"]["status"] == "conversational_contribution_engine_ready"
    assert preview_response["result"]["selected_kind"] == "idea"
    assert status_response["authority_event"]["persisted"] is False
    assert preview_response["authority_event"]["persisted"] is False
    assert conn.total_changes == changes_before
