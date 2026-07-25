from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.conversation_spine import build_conversation_spine
from selene.db import connect, init_db
from selene.dialogue_workspace import prepare_dialogue_turn
from selene.figurative_interpretation import interpret_figurative_language
from selene.native_language_organ import realize_native_language


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    conn.execute(
        "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES (?, ?, ?)",
        ("Figurative interpretation test", "selene_chat_active_supervised", "selene_supervised_speech"),
    )
    conn.commit()
    session_id = int(
        conn.execute("SELECT id FROM selene_chat_sessions ORDER BY id DESC LIMIT 1").fetchone()[0]
    )
    return conn, session_id


def _assert_locked(packet):
    assert packet["session_scoped_only"] is True
    assert packet["durable_memory_write"] is False
    assert packet["memory_write_active"] is False
    assert packet["runtime_memory_recall"] is False
    assert packet["identity_change"] is False
    assert packet["personality_change"] is False
    assert packet["governance_change"] is False
    assert packet["authority_change"] is False
    assert packet["training_allowed"] is False
    assert packet["lora_allowed"] is False
    assert packet["autonomous_action_allowed"] is False


def test_conventional_idiom_preserves_words_and_supplies_intended_meaning():
    packet = interpret_figurative_language(
        {"text": "Let's not beat a dead horse; move on to Phase 2."}
    )

    assert packet["selected_reading"] == "figurative"
    assert packet["literal_reading"].startswith("Let's not beat a dead horse")
    assert "keep pushing a settled or unproductive topic" in packet["interpreted_text"]
    assert packet["clarification_required"] is False
    assert packet["original_words_preserved"] is True
    _assert_locked(packet)


def test_slow_down_uses_visible_context_before_selecting_a_reading():
    conversational = interpret_figurative_language(
        {"text": "Slow down and explain it one step at a time."}
    )
    physical = interpret_figurative_language(
        {"text": "Slow down on this road while driving the car."}
    )

    assert conversational["selected_reading"] == "figurative"
    assert "conversational pace" in conversational["interpreted_text"]
    assert physical["selected_reading"] == "literal"
    assert physical["interpreted_text"] == physical["original_text"]


def test_analogy_maps_a_relationship_without_claiming_equivalence():
    packet = interpret_figurative_language(
        {"text": "The conversation spine works like a bookmark in a long book."}
    )

    mapping = packet["analogy_mapping"]
    assert packet["selected_reading"] == "figurative"
    assert "analogy" in packet["detected_forms"]
    assert mapping["equivalence_claimed"] is False
    assert mapping["mapping_limit"] == "unmapped properties are not carried across"
    assert packet["analogy_is_equivalence"] is False


def test_sarcasm_requires_explicit_or_multiple_visible_cues():
    ordinary = interpret_figurative_language({"text": "Great."})
    explicit = interpret_figurative_language(
        {"text": "Great, another crash. /s"}
    )

    assert ordinary["selected_reading"] == "literal"
    assert "sarcasm" not in ordinary["detected_forms"]
    assert explicit["selected_reading"] == "figurative"
    assert "sarcasm" in explicit["detected_forms"]


def test_ambiguous_figure_only_requests_clarification_when_answer_depends_on_it():
    statement = interpret_figurative_language({"text": "The storm passed."})
    material_question = interpret_figurative_language(
        {"text": "The storm passed; what should we do now?"}
    )

    assert statement["selected_reading"] == "unresolved"
    assert statement["clarification_required"] is False
    assert material_question["clarification_required"] is True
    assert "weather" in material_question["clarification_question"]


def test_explicit_correction_revises_only_the_prior_interpretation():
    previous = interpret_figurative_language(
        {"text": "The conversation spine works like a bookmark in a long book."}
    )
    correction = interpret_figurative_language(
        {
            "text": "I meant that literally.",
            "previous_interpretation": previous,
        }
    )

    update = correction["interpretation_update"]
    assert update["detected"] is True
    assert update["to_reading"] == "literal"
    assert update["scope"] == "current_session_interpretation_only"
    assert update["preserve_surrounding_conversation"] is True
    assert update["durable_memory_write"] is False


def test_dialogue_spine_and_nlo_keep_the_figurative_packet_inspectable(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "Slow down and explain it one step at a time."
    figurative = interpret_figurative_language({"text": text})
    intent = classify_chat_intent(figurative["interpreted_text"])
    dialogue = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "interpreted_text": figurative["interpreted_text"],
            "figurative_interpretation": figurative,
            "intent_decision": intent,
        },
    )
    spine = build_conversation_spine(
        {
            "session_id": session_id,
            "prompt": text,
            "interpreted_text": figurative["interpreted_text"],
            "figurative_interpretation": figurative,
            "intent_decision": intent,
            "dialogue_workspace": dialogue,
        }
    )
    nlo = realize_native_language(
        conn,
        {
            "prompt": figurative["interpreted_text"],
            "content_seed": "I will take it one step at a time.",
            "figurative_interpretation": figurative,
            "intent_decision": intent,
            "dialogue_workspace": dialogue,
            "conversation_spine": spine,
        },
    )

    assert dialogue["preferences"]["pacing"] == "spacious"
    assert dialogue["pragmatics"]["figurative_interpretation"]["selected_reading"] == "figurative"
    assert spine["literal_prompt"] == text
    assert spine["interpreted_prompt"] != text
    assert spine["literal_and_nonliteral_readings_remain_distinct"] is True
    assert nlo["version"] == "v22_contextual_figurative_meaning"
    assert nlo["meaning_packet"]["figurative_interpretation"]["selected_reading"] == "figurative"
    assert nlo["meaning_packet"]["analogy_is_equivalence"] is False
