import sqlite3

from selene.chat_intent import classify_chat_intent
from selene.emoji_expression import (
    apply_authored_emoji,
    interpret_emoji_expression,
    plan_authored_emoji,
)
from selene.relational_context import interpret_relational_context
from selene.social_language_realizer import build_content_light_plan, realize_social_act_plan


def test_interpreter_distinguishes_known_mixed_ambiguous_and_unknown_symbols():
    affection = interpret_emoji_expression("🩷")
    mixed = interpret_emoji_expression("we did it!! 🎉")
    ambiguous = interpret_emoji_expression("😭")
    resolved = interpret_emoji_expression("that joke has me crying laughing 😭")
    literal = interpret_emoji_expression("the campfire is burning 🔥")
    unknown = interpret_emoji_expression("🛸")

    assert affection["emoji_only_turn"] is True
    assert affection["primary_meaning"] == "affection"
    assert mixed["mixed_text_and_emoji"] is True
    assert mixed["primary_meaning"] == "celebration"
    assert ambiguous["primary_meaning"] == "ambiguous_expression"
    assert ambiguous["ambiguity"]["present"] is True
    assert resolved["primary_meaning"] == "amusement"
    assert literal["primary_meaning"] == ""
    assert literal["context_resolution_basis"] == "literal_fire_context_preserved"
    assert unknown["unknown_markers"] == ["🛸"]
    assert unknown["unknown_symbol_is_valid"] is True
    assert all(item["emotion_state_inferred"] is False for item in (affection, mixed, ambiguous, resolved, literal, unknown))


def test_emoji_only_turns_route_by_visible_symbolic_act_without_forcing_ambiguity():
    assert classify_chat_intent("🩷")["intent"] == "warm_connection"
    assert classify_chat_intent("😂")["intent"] == "playful_connection"
    assert classify_chat_intent("👍")["intent"] == "affirmation"
    uncertain = classify_chat_intent("😭")
    assert uncertain["intent"] == "direct_conversation"
    assert uncertain["symbolic_expression"]["ambiguity"]["present"] is True


def test_mixed_symbolic_statements_route_socially_without_stealing_real_questions():
    celebration = classify_chat_intent("we actually did it 🎉")
    amusement = classify_chat_intent("that was hilarious 😂")
    question = classify_chat_intent("why did the build stop? 🤔")

    assert celebration["intent"] == "warm_connection"
    assert celebration["mixed_intent"] is False
    assert celebration["matched_evidence"] == ["emoji_mixed:celebration"]
    assert amusement["intent"] == "playful_connection"
    assert question["intent"] == "reasoning"
    assert question["content_response_requested"] is True


def test_relational_context_exposes_emoji_meaning_without_creating_state():
    result = interpret_relational_context("that hurt 💔")

    assert "emoji_tenderness" in result["cue_types"]
    assert result["symbolic_expression"]["primary_meaning"] == "tenderness"
    assert result["emoji_meaning_is_contextual_not_universal"] is True
    assert result["memory_write_active"] is False
    assert result["personality_change"] is False


def test_authored_emoji_is_optional_contextual_and_limited_to_one():
    relation = interpret_relational_context("we did it!! 🎉")
    plan = plan_authored_emoji(
        prompt="we did it!! 🎉",
        candidate_text="That is worth celebrating together.",
        intent="warm_connection",
        relational_context=relation,
        variation_key="celebration",
    )
    realized = apply_authored_emoji("That is worth celebrating together.", plan)

    assert plan["selected_emoji"] in {"🎉", "✨", "🙌"}
    assert plan["maximum_authored_emoji"] == 1
    assert plan["mirroring_required"] is False
    assert realized.endswith(plan["selected_emoji"])
    assert plan["emotion_state_created"] is False

    plain = plan_authored_emoji(
        prompt="The build completed.",
        candidate_text="The build completed.",
        intent="direct_answer",
        variation_key="plain-fact",
    )
    assert plain["selected_emoji"] == ""


def test_emoji_only_thought_and_ambiguity_receive_contextual_words():
    thoughtful_relation = interpret_relational_context("🤔")
    thoughtful_plan = build_content_light_plan(
        {"prompt": "🤔", "relational_context": thoughtful_relation}
    )
    thoughtful = realize_social_act_plan(
        thoughtful_plan,
        prompt="🤔",
        variation_key="thoughtful-symbol",
    )

    ambiguous_relation = interpret_relational_context("😭")
    ambiguous_plan = build_content_light_plan(
        {"prompt": "😭", "relational_context": ambiguous_relation}
    )
    ambiguous = realize_social_act_plan(
        ambiguous_plan,
        prompt="😭",
        variation_key="ambiguous-symbol",
    )

    assert thoughtful_plan["move_kind"] == "symbolic_expression"
    assert any(term in thoughtful["candidate_text"].lower() for term in ("thinking", "thought", "turning"))
    assert ambiguous_plan["move_kind"] == "symbolic_expression"
    assert any(term in ambiguous["candidate_text"].lower() for term in ("different meanings", "few different meanings", "do not want to guess"))
    assert ambiguous["emoji_expression"]["selected_emoji"] == ""


def test_emoji_survives_sqlite_utf8_round_trip():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE messages(value TEXT NOT NULL)")
    value = "Words, warmth, and play 🩷 😂 🎉 🤔"
    conn.execute("INSERT INTO messages(value) VALUES (?)", (value,))
    assert conn.execute("SELECT value FROM messages").fetchone()[0] == value
