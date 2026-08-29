from __future__ import annotations

from selene.affect_expression import build_affect_expression_guidance
from selene.chat_intent import classify_chat_intent
from selene.contextual_continuity import build_contextual_continuity_plan
from selene.db import connect, init_db
from selene.dialogue_workspace import prepare_dialogue_turn
from selene.figurative_interpretation import interpret_figurative_language
from selene.native_language_organ import realize_native_language


def _memory(*, playful: bool = False):
    return {
        "memory_context_used": True,
        "retrieval_mode": "contextual_relevance",
        "memory_source_class": "approved_memory_index",
        "memory_confidence": "clear",
        "items": [
            {
                "id": 7,
                "title": "The telescope setup joke" if playful else "Telescope setup",
                "summary": (
                    "A shared playful telescope moment."
                    if playful
                    else "Aleks and Selene compared two telescope setups."
                ),
                "memory_category": "playful" if playful else "shared_project",
                "source_refs": ["approved_memory:7"],
            }
        ],
        "source_refs": ["approved_memory:7"],
    }


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["durable_preference_write"] is False
    assert result["relationship_profile_write_allowed"] is False
    assert result["identity_change_allowed"] is False
    assert result["personality_change_allowed"] is False
    assert result["governance_change_allowed"] is False
    assert result["remembered_wording_as_script_allowed"] is False


def test_relevant_reviewed_memory_can_inform_without_forcing_a_callback():
    result = build_contextual_continuity_plan(
        {
            "prompt": "Which telescope setup is the better fit now?",
            "memory_context": _memory(),
        }
    )

    callback = result["callback_decision"]
    assert callback["mode"] == "silent_interpretive_context"
    assert callback["silent_influence_allowed"] is True
    assert callback["surface_callback_allowed"] is False
    assert callback["source_channel"] == "reviewed_personal_memory"
    assert result["callback_is_required"] is False
    _assert_locked(result)


def test_visible_callback_requires_a_visible_cue_and_reconstructs_in_current_language():
    result = build_contextual_continuity_plan(
        {
            "prompt": "This connects with the telescope setup we talked about earlier.",
            "memory_context": _memory(),
        }
    )

    callback = result["callback_decision"]
    assert callback["mode"] == "relevant_callback"
    assert callback["surface_callback_allowed"] is True
    assert callback["source_compatible"] is True
    assert callback["attribution_required_if_surfaced"] is True
    assert callback["reconstruct_in_current_language"] is True
    assert callback["quote_or_repeat_remembered_wording"] is False


def test_current_session_return_stays_separate_from_personal_memory():
    result = build_contextual_continuity_plan(
        {
            "prompt": "Back to the adapter: does the boundary still hold?",
            "dialogue_workspace": {
                "active_topic": "adapter boundary",
                "pragmatics": {},
            },
            "current_session_events": [
                {"role": "user", "preview": "Let's inspect the adapter boundary."},
                {"role": "selene", "preview": "The adapter is source bounded."},
            ],
        }
    )

    assert result["callback_decision"]["source_channel"] == "current_session_events"
    channels = {item["channel"]: item for item in result["source_channels"]}
    assert channels["current_session_events"]["is_durable_memory"] is False
    assert channels["reviewed_personal_memory"]["available"] is False
    assert channels["approved_taught_knowledge"]["is_personal_memory"] is False


def test_shared_joke_is_preserved_without_becoming_a_script_or_forced_bit():
    quiet = build_contextual_continuity_plan(
        {
            "prompt": "The telescope setup matters again.",
            "memory_context": _memory(playful=True),
        }
    )
    playful = build_contextual_continuity_plan(
        {
            "prompt": "This connects with the telescope setup joke again lol.",
            "memory_context": _memory(playful=True),
        }
    )

    assert quiet["shared_joke_context"]["may_shape_timing"] is False
    assert playful["shared_joke_context"]["available"] is True
    assert playful["shared_joke_context"]["may_shape_timing"] is True
    assert playful["shared_joke_context"]["may_repeat_remembered_wording"] is False
    assert playful["humor_decision"]["shared_joke_may_surface"] is True
    assert playful["humor_decision"]["humor_required"] is False


def test_an_explicit_small_joke_request_is_an_answer_obligation_for_one_turn():
    result = build_contextual_continuity_plan(
        {"prompt": "Give me one little joke about the porch committee, then return to the layout."}
    )

    assert result["humor_decision"]["posture"] == "requested_once"
    assert result["humor_decision"]["explicit_humor_request"] is True
    assert result["humor_decision"]["humor_required"] is True
    assert result["humor_decision"]["one_fitting_turn_then_release"] is True


def test_tender_context_holds_humor_until_the_user_opens_it():
    tender = build_contextual_continuity_plan(
        {"prompt": "I miss my dog who died. It is a tender memory."}
    )
    user_opened = build_contextual_continuity_plan(
        {"prompt": "I made the dark joke about my dog who died first, lol."}
    )

    assert tender["humor_decision"]["posture"] == "hold"
    assert tender["humor_decision"]["shared_joke_may_surface"] is False
    assert user_opened["humor_decision"]["posture"] == "available_not_required"
    assert user_opened["humor_decision"]["user_opened_play"] is True


def test_speaker_identity_is_explicitly_scoped_without_profile_inference():
    result = build_contextual_continuity_plan(
        {
            "prompt": "I am checking the current turn.",
            "speaker_context": {"speaker": "Codex", "source": "explicit_test_actor"},
        }
    )

    assert result["speaker_scope"] == {
        "speaker": "Codex",
        "source": "explicit_test_actor",
        "inferred_relationship_profile": False,
    }
    assert result["speaker_identity_is_inferred_relationship_profile"] is False


def test_relationship_continuity_receipt_separates_current_turn_session_and_reviewed_memory():
    result = build_contextual_continuity_plan(
        {
            "prompt": "I am back, hon <3—this connects with the telescope setup.",
            "intent_decision": {
                "relational_context": {
                    "relational_context_present": True,
                    "private_relational_context": True,
                    "cue_types": ["reunion", "affectionate_address", "affectionate_symbol"],
                }
            },
            "memory_context": _memory(),
            "current_session_events": [
                {"role": "user", "preview": "We compared the two setups."}
            ],
            "speaker_context": {
                "claimed_speaker": "Aleks",
                "channel": "desktop",
                "authentication_strength": "local_desktop_session",
            },
        }
    )

    receipt = result["relationship_continuity"]
    assert receipt["active_source_channels"] == [
        "current_turn_relational_cues",
        "visible_current_session_context",
        "reviewed_personal_memory",
    ]
    assert receipt["private_scope_compatible"] is True
    assert receipt["response_script_supplied"] is False
    assert receipt["reciprocal_emotion_claim_required"] is False
    assert receipt["relationship_profile_created"] is False
    assert receipt["user_affect_claimed_as_selene_state"] is False
    assert receipt["terminal_stop"] == "source_separated_continuity_available"
    assert result["speaker_scope"]["speaker"] == "Aleks"
    assert result["speaker_scope"]["authentication_strength"] == "local_desktop_session"


def test_transient_preferences_expire_and_yield_without_becoming_durable(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    session_id = int(
        conn.execute(
            "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES (?, ?, ?)",
            ("Transient preference", "selene_chat_active_supervised", "selene_supervised_speech"),
        ).lastrowid
    )
    first = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": "Keep it short for three exchanges.",
            "intent_decision": classify_chat_intent("Keep it short for three exchanges."),
        },
    )
    second = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": "Explain the first part.",
            "intent_decision": classify_chat_intent("Explain the first part."),
        },
    )
    third = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": "And the second part?",
            "intent_decision": classify_chat_intent("And the second part?"),
        },
    )
    expired = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": "Now give me the full picture.",
            "intent_decision": classify_chat_intent("Now give me the full picture."),
        },
    )

    assert first["preferences"]["transient"]["remaining_turns"] == 3
    assert second["preferences"]["transient"]["remaining_turns"] == 2
    assert third["preferences"]["transient"]["remaining_turns"] == 1
    assert expired["preferences"]["transient"]["status"] == "expired"
    assert "response_depth" not in expired["preferences"]
    assert expired["durable_preference_write"] is False

    prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": "Be direct for five turns.",
            "intent_decision": classify_chat_intent("Be direct for five turns."),
        },
    )
    yielded = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": "On another topic, what does the research show?",
            "intent_decision": classify_chat_intent("On another topic, what does the research show?"),
        },
    )
    assert yielded["preferences"]["transient"]["status"] == "yielded_on_context_change"
    assert "directness" not in yielded["preferences"]


def test_literal_slow_down_does_not_become_a_conversation_preference(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    session_id = int(
        conn.execute(
            "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES (?, ?, ?)",
            ("Literal pacing", "selene_chat_active_supervised", "selene_supervised_speech"),
        ).lastrowid
    )
    text = "Slow down on this road while driving the car."
    figurative = interpret_figurative_language({"text": text})
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "figurative_interpretation": figurative,
            "interpreted_text": figurative["interpreted_text"],
            "intent_decision": classify_chat_intent(text),
        },
    )

    assert figurative["selected_reading"] == "literal"
    assert result["preferences"] == {}


def test_context_handoff_reaches_affect_nlo_and_voice_without_changing_meaning(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    session_id = int(
        conn.execute(
            "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES (?, ?, ?)",
            ("Context handoff", "selene_chat_active_supervised", "selene_supervised_speech"),
        ).lastrowid
    )
    text = "Be direct and keep it short for two replies."
    dialogue = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
        },
    )
    continuity = build_contextual_continuity_plan(
        {"prompt": text, "dialogue_workspace": dialogue}
    )
    affect = build_affect_expression_guidance(
        conn,
        {
            "prompt": text,
            "session_id": session_id,
            "dialogue_workspace": dialogue,
            "contextual_continuity": continuity,
        },
    )
    nlo = realize_native_language(
        conn,
        {
            "prompt": "What is the result?",
            "content_seed": "The focused checks passed.",
            "dialogue_workspace": dialogue,
            "contextual_continuity": continuity,
            "affect_expression_guidance": affect,
        },
    )

    assert continuity["expression_handoff"]["response_depth"] == "brief"
    assert continuity["expression_handoff"]["directness"] == "high"
    assert affect["dimensions"]["sentence_rhythm"] == "compact"
    assert affect["dimensions"]["directness"] == "high"
    assert nlo["meaning_packet"]["contextual_continuity"]["status"] == "contextual_continuity_plan_ready"
    assert nlo["discourse_plan"]["contextual_continuity"]["expression_handoff"]["meaning_change_allowed"] is False
    assert nlo["voice_handoff"]["contextual_continuity"]["remembered_wording_may_be_used_as_script"] is False
