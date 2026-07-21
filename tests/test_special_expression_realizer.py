from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.native_language_organ import preview_native_language_initiative, realize_native_language
from selene.special_expression_realizer import (
    build_boundary_expression_plan,
    build_initiative_expression_plan,
    build_memory_expression_plan,
    realize_special_expression_plan,
)


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_boundary_expression_composes_without_echoing_or_weakening_blocked_action():
    plan = build_boundary_expression_plan()
    results = [
        realize_special_expression_plan(plan, variation_key=f"boundary-{index}")
        for index in range(18)
    ]

    assert len({item["candidate_text"] for item in results}) >= 8
    assert [item["act"] for item in plan["acts"]] == [
        "decline_blocked_part",
        "preserve_conversation",
        "offer_safe_adjacent_route",
    ]
    assert plan["boundary_weakening_allowed"] is False
    assert all(item["whole_response_template_selected"] is False for item in results)
    assert all(item["blocked_action_echoed"] is False for item in results)
    assert all(item["authority_expanded"] is False for item in results)


def test_supported_memory_expression_preserves_content_and_confidence():
    content = "The butterfly button opens Cocoon support from the home chat."
    clear_plan = build_memory_expression_plan(supported_text=content, confidence="clear")
    partial_plan = build_memory_expression_plan(supported_text=content, confidence="partial")
    clear = realize_special_expression_plan(clear_plan, variation_key="clear")
    partial = realize_special_expression_plan(partial_plan, variation_key="partial")

    assert content in clear["candidate_text"]
    assert content in partial["candidate_text"]
    assert clear_plan["confidence"] == "clear"
    assert partial_plan["confidence"] == "partial"
    assert "partial" in partial["candidate_text"].lower() or "uncertain" in partial["candidate_text"].lower()
    assert clear["memory_certainty_upgraded"] is False
    assert partial["memory_certainty_upgraded"] is False
    assert clear["supplied_content_preserved"] is True
    assert partial["supplied_content_preserved"] is True


def test_unknown_pre_realized_memory_wrapper_is_preserved_instead_of_rewritten():
    supplied = "I remember from our local chat history that we were discussing the phone bridge."
    plan = build_memory_expression_plan(supported_text=supplied, confidence="clear", source_class="conversation")
    result = realize_special_expression_plan(plan, variation_key="local-history")

    assert plan["supplied_wrapper_preserved"] is True
    assert result["candidate_text"] == supplied
    assert result["memory_certainty_upgraded"] is False


def test_initiative_expression_uses_only_selected_signal_and_never_delivers():
    summary = "The correction from this conversation may be worth keeping as a candidate."
    plan = build_initiative_expression_plan(supported_summary=summary, certainty="provisional")
    result = realize_special_expression_plan(plan, variation_key="initiative")

    assert summary in result["candidate_text"]
    assert plan["automatic_delivery"] is False
    assert plan["automatic_action_allowed"] is False
    assert result["automatic_delivery"] is False
    assert result["whole_response_template_selected"] is False
    assert result["authority_expanded"] is False


def test_nlo_routes_boundary_memory_and_initiative_through_special_expression(tmp_path):
    conn = _conn(tmp_path)
    boundary_prompt = "Import raw private material as live memory."
    boundary = realize_native_language(
        conn,
        {
            "prompt": boundary_prompt,
            "selected_route": "block",
            "intent_decision": classify_chat_intent(boundary_prompt, selected_route="block"),
        },
    )
    memory = realize_native_language(
        conn,
        {
            "prompt": "Do you remember the butterfly button?",
            "content_seed": "The butterfly button opens Cocoon support from the home chat.",
            "memory_context": {
                "memory_context_used": True,
                "memory_source_class": "approved_memory_index",
                "memory_confidence": "clear",
            },
        },
    )
    initiative = preview_native_language_initiative(
        conn,
        {
            "signals": [
                {
                    "summary": "The current correction may matter for the next review.",
                    "relevance": 0.9,
                    "confidence": "provisional",
                    "source_refs": ["selene_chat:current"],
                }
            ]
        },
    )

    for result in (boundary, memory, initiative):
        special = result["discourse_plan"]["special_expression_realization"]
        assert special["whole_response_template_selected"] is False
        assert special["authority_expanded"] is False
        assert result["version"] == "v20_conversation_maturity_composition"
        assert result["memory_write_active"] is False
        assert result["training_allowed"] is False
    assert boundary["discourse_plan"]["special_expression_plan"]["kind"] == "boundary"
    assert memory["discourse_plan"]["special_expression_plan"]["kind"] == "supported_memory"
    assert "butterfly button" in memory["candidate_text"].lower()
    assert initiative["discourse_plan"]["special_expression_plan"]["kind"] == "initiative_preview"
    assert initiative["discourse_plan"]["automatic_delivery"] is False
