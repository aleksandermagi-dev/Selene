from __future__ import annotations

from selene.conversational_micro_moves import build_conversational_micro_move_plan
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language
from selene.quotation_echo import (
    build_quotation_echo_plan,
    quotation_echo_status,
    realize_quotation_echo,
)


def _assert_bounded(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_corpus_access_allowed"] is False
    assert result["private_corpus_wording_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["fact_generation_allowed"] is False
    assert result["hidden_chain_of_thought_exposed"] is False


def _modes(result):
    return set(result["selected_mode_names"])


def test_status_distinguishes_legitimate_expression_modes_and_private_replay():
    status = quotation_echo_status()

    assert status["status"] == "quotation_echo_coordination_ready"
    assert "attributed_quotation" in status["expression_modes"]
    assert "playful_mimicry" in status["expression_modes"]
    assert "affectionate_echo" in status["expression_modes"]
    assert status["technical_exactness_requires_persona_copying"] is False
    assert status["shared_callback_is_plagiarism"] is False
    assert status["reviewed_memory_wording_may_be_replayed"] is False
    assert status["address_term_echo_required"] is False
    _assert_bounded(status)


def test_attributed_quote_requires_source_and_private_corpus_wording_is_held():
    ready = build_quotation_echo_plan(
        {
            "prompt": "Quote the source exactly as written.",
            "knowledge_expression_handoff": {
                "source_wording_is_surface_requirement": True,
                "source_refs": ["source_packet:history:4"],
            },
        }
    )
    missing = build_quotation_echo_plan(
        {"prompt": "Quote the source exactly as written."}
    )
    private = build_quotation_echo_plan(
        {
            "prompt": "Quote the source exactly as written.",
            "source_refs": ["private_corpus:message:22"],
        }
    )

    assert "attributed_quotation" in _modes(ready)
    assert ready["selected_modes"][0]["source_refs"] == ["source_packet:history:4"]
    assert "attributed_quotation" not in _modes(missing)
    assert any(item["mode"] == "attributed_quotation" for item in missing["held_or_unavailable"])
    assert private["private_source_detected"] is True
    assert "attributed_quotation" not in _modes(private)
    _assert_bounded(ready)
    _assert_bounded(private)


def test_approved_knowledge_defaults_to_paraphrase_while_exact_domains_keep_structure():
    paraphrase = build_quotation_echo_plan(
        {
            "knowledge_expression_handoff": {
                "active": True,
                "original_expression_required": True,
                "source_refs": ["teaching_material:7"],
            }
        }
    )
    exact = build_quotation_echo_plan(
        {"answer_domain": "verified_math"}
    )

    assert "meaning_preserving_paraphrase" in _modes(paraphrase)
    assert "attributed_quotation" not in _modes(paraphrase)
    assert "technical_exactness" in _modes(exact)
    assert exact["technical_exactness_is_persona_copying"] is False


def test_memory_callback_reconstructs_language_and_never_replays_remembered_wording():
    plan = build_quotation_echo_plan(
        {
            "contextual_continuity": {
                "callback_decision": {
                    "surface_callback_allowed": True,
                    "source_channel": "reviewed_personal_memory",
                    "reconstruct_in_current_language": True,
                }
            }
        }
    )

    callback = next(item for item in plan["selected_modes"] if item["mode"] == "shared_callback")
    assert callback["reconstruct_in_current_language"] is True
    assert callback["exact_wording_allowed"] is False
    assert plan["shared_callback_is_raw_memory_recall"] is False
    assert any(item["mode"] == "memory_wording_replay" for item in plan["held_or_unavailable"])
    assert plan["visible_echo_selected"] is False
    _assert_bounded(plan)


def test_short_visible_phrase_can_be_playfully_mimicked_without_copying_the_response():
    plan = build_quotation_echo_plan(
        {
            "prompt": 'Echo this: "THAT WORKED" lol',
            "intent": "playful_connection",
            "contextual_continuity": {
                "humor_decision": {"user_opened_play": True}
            },
        }
    )
    realized = realize_quotation_echo(
        "Okay, you got me with that one.",
        plan,
        variation_key="visible-echo",
    )

    assert "playful_mimicry" in _modes(plan)
    assert plan["visible_echo"]["fragment"] == "THAT WORKED"
    assert plan["visible_echo"]["source_channel"] == "current_turn_visible_quotation"
    assert plan["suppress_generic_playful_move"] is True
    assert realized["addition_applied"] is True
    assert "THAT WORKED" in realized["candidate_text"]
    assert "Okay, you got me" in realized["candidate_text"]
    assert realized["whole_response_copied"] is False
    assert realized["fact_added"] is False
    _assert_bounded(realized)


def test_long_or_unbounded_echo_request_is_held_instead_of_truncated_as_a_quote():
    plan = build_quotation_echo_plan(
        {
            "prompt": (
                "Echo this: one two three four five six seven eight nine ten "
                "eleven twelve thirteen"
            ),
            "intent": "playful_connection",
        }
    )

    assert "playful_mimicry" not in _modes(plan)
    assert plan["visible_echo_selected"] is False
    assert any(item["mode"] == "playful_mimicry" for item in plan["held_or_unavailable"])


def test_visible_affection_mark_may_be_echoed_but_address_terms_are_not_forced():
    affectionate = build_quotation_echo_plan(
        {"prompt": "Good work, my friend <3", "intent": "warm_connection"}
    )
    addressed = build_quotation_echo_plan(
        {
            "prompt": "Hey sweetie, can we compare these?",
            "intent": "direct_answer",
            "referent_address": {
                "direct_address": {"token": "sweetie", "must_be_echoed_in_reply": False}
            },
        }
    )

    assert "affectionate_echo" in _modes(affectionate)
    assert affectionate["visible_echo"]["fragment"] == "<3"
    assert affectionate["address_term_must_be_echoed"] is False
    assert addressed["direct_address_observed"] is True
    assert addressed["direct_address_token"] == "sweetie"
    assert addressed["visible_echo_selected"] is False


def test_source_visible_echo_owns_the_single_playful_micro_move():
    echo = build_quotation_echo_plan(
        {
            "prompt": 'Say it with me: "WE GOT IT" lol',
            "intent": "playful_connection",
        }
    )
    micro = build_conversational_micro_move_plan(
        {
            "prompt": 'Say it with me: "WE GOT IT" lol',
            "intent": "playful_connection",
            "quotation_echo_plan": echo,
            "affect_expression_guidance": {
                "dimensions": {"humor": "available_not_required"}
            },
        }
    )

    assert echo["suppress_generic_playful_move"] is True
    assert not any(item["move"] == "one_playful_turn" for item in micro["moves"])
    assert any(
        item["move"] == "one_playful_turn"
        and "source-visible playful echo" in item["reason"]
        for item in micro["held_or_omitted"]
    )


def test_nlo_and_read_only_routes_expose_playful_echo_without_memory_write(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    result = realize_native_language(
        conn,
        {
            "prompt": 'Echo this: "THAT WORKED" lol',
            "communicative_intent": "playful_connection",
            "intent_decision": {
                "intent": "playful_connection",
                "answer_shape": "social_response",
                "response_depth": "brief",
            },
        },
    )
    changes_before_routes = conn.total_changes
    status = route_request(conn, "native_language.quotation_echo.status")["result"]
    preview = route_request(
        conn,
        "native_language.quotation_echo.preview",
        {"prompt": 'Echo this: "WE DID IT" lol', "intent": "playful_connection"},
    )["result"]

    plan = result["quotation_echo"]
    realization = result["discourse_plan"]["quotation_echo_realization"]
    assert "playful_mimicry" in plan["selected_mode_names"]
    assert realization["addition_applied"] is True
    assert result["candidate_text"].count("THAT WORKED") == 1
    assert result["voice_handoff"]["quotation_echo_plan"] == plan
    assert result["voice_handoff"]["quotation_echo_realization"] == realization
    assert status["status"] == "quotation_echo_coordination_ready"
    assert preview["visible_echo_selected"] is True
    assert conn.total_changes == changes_before_routes
    _assert_bounded(plan)
