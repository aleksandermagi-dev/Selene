from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.dialogue_workspace import prepare_dialogue_turn
from selene.input_detangler import build_input_clarification, detangle_user_input
from selene.module_router import route_request
from selene.pragmatic_planner import build_pragmatic_plan


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def test_detangler_preserves_raw_input_and_repairs_only_reviewed_patterns():
    raw = "lets catergorize th e material and compare both sollutions"
    result = detangle_user_input(raw)

    assert result["raw_text"] == raw
    assert result["interpreted_text"] == "lets categorize the material and compare both solutions"
    assert result["raw_text_preserved"] is True
    assert result["repair_count"] == 3
    assert result["interpretation_confidence"] == "high"
    assert result["safe_for_semantic_routing"] is True
    assert result["memory_write_active"] is False
    assert result["identity_change_allowed"] is False
    assert result["governance_change_allowed"] is False
    assert result["automatic_lexicon_learning"] is False


def test_detangler_repairs_observed_unambiguous_doubled_pronoun_phrase():
    raw = "whats on you your mind?"
    result = detangle_user_input(raw)

    assert result["raw_text"] == raw
    assert result["interpreted_text"] == "whats on your mind?"
    assert result["repair_count"] == 1
    assert classify_chat_intent(result["interpreted_text"])["intent"] == "self_state"


def test_detangler_repairs_split_article_attached_to_the_following_word():
    raw = "The warmth I do not understand th eissue"
    result = detangle_user_input(raw)

    assert result["interpreted_text"] == "The warmth I do not understand the issue"
    assert result["repairs"][0]["kind"] == "reviewed_structural_spacing"
    assert result["safe_for_silent_repair"] is True


def test_detangler_does_not_apply_split_article_repair_inside_protected_material():
    raw = "please inspect `th eissue` and https://example.test/th%20eissue"
    result = detangle_user_input(raw)

    assert result["interpreted_text"] == raw
    assert result["repair_count"] == 0


def test_detangler_leaves_material_ambiguity_unresolved():
    raw = "only run streswing tests when necessary"
    result = detangle_user_input(raw)

    assert result["interpreted_text"] == raw
    assert result["ambiguities"][0]["token"] == "streswing"
    assert result["ambiguities"][0]["alternatives"] == ["stress-testing", "stressful"]
    assert result["safe_for_semantic_routing"] is True
    assert result["safe_for_silent_repair"] is False
    assert result["interpretation_complete"] is False
    assert result["ask_if_materially_ambiguous"] is True
    assert result["interpretation_confidence"] == "unresolved"


def test_material_ambiguity_builds_one_user_attributed_ordinary_clarification():
    interpretation = detangle_user_input("only run streswing tests when necessary")
    result = build_input_clarification(interpretation)

    assert result["required"] is True
    assert result["single_question_only"] is True
    assert result["ordinary_conversation_not_teaching"] is True
    assert "streswing" in result["response_seed"]
    assert "stress-testing or stressful" in result["response_seed"]
    assert result["user_input_remains_user_authored"] is True
    assert result["selene_failure_inferred"] is False
    assert result["memory_retrieval_eligible"] is False


def test_detangler_does_not_rewrite_code_urls_or_workspace_paths():
    raw = r"inspect C:\repo\sollution.py, `catergorize()` and https://example.test/sollution"
    result = detangle_user_input(raw)

    assert result["interpreted_text"] == raw
    assert result["repair_count"] == 0


def test_dialogue_workspace_uses_interpretation_but_keeps_raw_preview(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES (?, ?, ?)",
        ("Input detangler test", "selene_chat_active_supervised", "selene_supervised_speech"),
    )
    session_id = int(conn.execute("SELECT id FROM selene_chat_sessions").fetchone()[0])
    raw = "What is th e sollution?"
    interpretation = detangle_user_input(raw)

    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": raw,
            "input_interpretation": interpretation,
            "intent_decision": classify_chat_intent(interpretation["interpreted_text"]),
        },
    )

    assert result["last_user_preview"] == raw
    assert result["pragmatics"]["question_units"] == ["What is the solution?"]
    assert result["pragmatics"]["input_interpretation"]["raw_text"] == raw
    assert result["pragmatics"]["input_interpretation"]["interpreted_text"] == "What is the solution?"


def test_pragmatic_plan_carries_unresolved_input_ambiguity_without_guessing(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES (?, ?, ?)",
        ("Input ambiguity test", "selene_chat_active_supervised", "selene_supervised_speech"),
    )
    session_id = int(conn.execute("SELECT id FROM selene_chat_sessions").fetchone()[0])
    raw = "only run streswing tests when necessary"
    interpretation = detangle_user_input(raw)
    dialogue = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": raw,
            "input_interpretation": interpretation,
            "intent_decision": classify_chat_intent(raw),
        },
    )

    plan = build_pragmatic_plan({"prompt": interpretation["interpreted_text"], "dialogue_workspace": dialogue})

    assert plan["ambiguity"]["level"] == "material_input_ambiguity"
    assert plan["answer_strategy"] == "answer_from_unambiguous_context_or_ask_briefly_if_word_changes_answer"
    assert plan["ambiguity"]["input_ambiguities"][0]["token"] == "streswing"


def test_detangler_has_an_inspectable_router_entry(tmp_path):
    conn = _conn(tmp_path)
    result = route_request(conn, "native_language.input.detangle", {"text": "beleieve th e evidence"})["result"]

    assert result["interpreted_text"] == "believe the evidence"
    assert result["review_status"] == "status_only"
    assert result["training_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def test_chat_dry_run_records_raw_message_and_exposes_interpretation(tmp_path):
    conn = _conn(tmp_path)
    raw = "can you compare both sollutions"

    result = route_request(conn, "selene_chat.send_dry_run", {"text": raw})["result"]
    session = route_request(
        conn,
        "selene_chat.session.detail",
        {"session_id": result["session_id"]},
    )["result"]

    assert result["input_interpretation"]["interpreted_text"] == "can you compare both solutions"
    assert session["messages"][0]["content"] == raw
    assert session["messages"][0]["payload_json"]["input_interpretation"]["raw_text"] == raw
    assert session["messages"][0]["payload_json"]["input_interpretation"]["interpreted_text"] == (
        "can you compare both solutions"
    )
