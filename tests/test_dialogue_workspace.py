from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.dialogue_workspace import dialogue_workspace_status, prepare_dialogue_turn, record_dialogue_response
from selene.module_router import route_request
from selene.pragmatic_planner import build_pragmatic_plan, evaluate_response_coverage


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    conn.execute(
        "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES (?, ?, ?)",
        ("Dialogue workspace test", "selene_chat_active_supervised", "selene_supervised_speech"),
    )
    conn.commit()
    return conn, int(conn.execute("SELECT id FROM selene_chat_sessions ORDER BY id DESC LIMIT 1").fetchone()[0])


def test_dialogue_workspace_tracks_multi_part_questions_and_completion(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "Can you compare memory and voice? What should we build first?"
    prepared = prepare_dialogue_turn(
        conn,
        {"session_id": session_id, "text": text, "intent_decision": classify_chat_intent(text)},
    )

    assert prepared["pragmatics"]["multi_part_prompt"] is True
    assert len(prepared["pragmatics"]["question_units"]) == 2
    assert len(prepared["open_loops"]) == 2

    recorded = record_dialogue_response(
        conn,
        {
            "session_id": session_id,
            "candidate_text": "Memory should be grounded first. Voice can then express what memory supports.",
            "answered_loop_ids": prepared["new_loop_ids"],
        },
    )

    assert recorded["open_loops"] == []
    assert len(recorded["completed_loops"]) == 2
    assert recorded["last_selene_preview"].startswith("Memory should")


def test_dialogue_workspace_separates_context_sentence_from_following_question(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "Selene, this is Codex checking for Aleks. Are you receiving this clearly?"
    prepared = prepare_dialogue_turn(
        conn,
        {"session_id": session_id, "text": text, "intent_decision": classify_chat_intent(text)},
    )

    assert prepared["pragmatics"]["question_units"] == ["Are you receiving this clearly?"]
    assert prepared["open_loops"][0]["question"] == "Are you receiving this clearly?"


def test_dialogue_workspace_closes_only_questions_covered_by_visible_response(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "Can you compare memory and voice? What should we build first?"
    prepared = prepare_dialogue_turn(
        conn,
        {"session_id": session_id, "text": text, "intent_decision": classify_chat_intent(text)},
    )
    plan = build_pragmatic_plan({"prompt": text, "dialogue_workspace": prepared})
    coverage = evaluate_response_coverage(plan, "Memory and voice serve different roles.")
    recorded = record_dialogue_response(
        conn,
        {"session_id": session_id, "candidate_text": "Memory and voice serve different roles.", "coverage_evaluation": coverage},
    )

    assert len(recorded["completed_loops"]) == 1
    assert len(recorded["open_loops"]) == 1
    assert recorded["pragmatics"]["last_response_coverage"]["all_required_addressed"] is False


def test_dialogue_workspace_resolves_immediate_reference_and_session_preference(tmp_path):
    conn, session_id = _conn(tmp_path)
    prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": "Which language layer comes first?",
            "intent_decision": classify_chat_intent("Which language layer comes first?"),
        },
    )
    text = "Yes, that one. Keep it short."
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
            "conversation_events": [
                {"role": "selene", "preview": "The semantic formation layer should come first."}
            ],
        },
    )

    resolved = result["pragmatics"]["resolved_reference"]
    assert resolved["token"] == "that one"
    assert "semantic formation layer" in resolved["resolved_to"]
    assert result["preferences"]["response_depth"] == "brief"
    assert result["preferences"]["scope"] == "current_session_only"
    assert result["durable_preference_write"] is False


def test_dialogue_workspace_keeps_corrections_as_refinement_not_memory(tmp_path):
    conn, session_id = _conn(tmp_path)
    before = int(conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0])
    text = "Actually, I meant the semantic layer, not the voice layer."
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
            "conversation_events": [{"role": "selene", "preview": "The voice layer comes first."}],
        },
    )
    after = int(conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0])

    assert result["last_dialogue_act"] == "correction"
    assert result["corrections"][0]["status"] == "active_refinement"
    assert before == after == 0
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False


def test_dialogue_workspace_resolves_ordered_options_from_the_previous_turn(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "Explain the second one."
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
            "conversation_events": [{"role": "selene", "preview": "The options are memory and voice."}],
        },
    )

    resolved = result["pragmatics"]["resolved_reference"]
    assert resolved["resolved_to"] == "voice"
    assert resolved["resolution_status"] == "resolved"
    assert resolved["candidates"] == ["memory", "voice"]


def test_dialogue_workspace_marks_materially_ambiguous_other_option_instead_of_guessing(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "Explain the other one."
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
            "conversation_events": [{"role": "selene", "preview": "The options are memory and voice."}],
        },
    )

    resolved = result["pragmatics"]["resolved_reference"]
    assert resolved["resolved_to"] == ""
    assert resolved["resolution_status"] == "materially_ambiguous"
    assert resolved["ask_if_materially_ambiguous"] is True


def test_dialogue_workspace_finds_option_referents_before_a_generic_acknowledgement(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "What about the other one?"
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
            "contextual_follow_up": {"detected": True, "kind": "alternative_reference", "preserve_active_topic": True},
            "conversation_events": [
                {"role": "user", "preview": "The two options are memory and voice."},
                {"role": "selene", "preview": "I have both options."},
            ],
        },
    )

    resolved = result["pragmatics"]["resolved_reference"]
    assert resolved["candidates"] == ["memory", "voice"]
    assert resolved["resolution_status"] == "materially_ambiguous"
    assert resolved["resolved_to"] == ""


def test_contextual_follow_up_preserves_the_active_topic(tmp_path):
    conn, session_id = _conn(tmp_path)
    prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": "Compare memory and voice.",
            "intent_decision": classify_chat_intent("Compare memory and voice."),
        },
    )
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": "Why?",
            "intent_decision": classify_chat_intent("Why?"),
            "contextual_follow_up": {"detected": True, "kind": "reason_follow_up", "preserve_active_topic": True},
            "conversation_events": [{"role": "selene", "preview": "Memory should come first."}],
        },
    )

    assert result["active_topic"] == "compare memory voice"
    assert result["pragmatics"]["contextual_follow_up"]["kind"] == "reason_follow_up"


def test_response_coverage_rejects_an_unrelated_answer_with_only_generic_overlap():
    plan = build_pragmatic_plan(
        {
            "prompt": "Why do you prefer the two-zone trial first, and what result would make you change your recommendation?",
            "intent_decision": {"intent": "reasoning"},
            "dialogue_workspace": {
                "active_topic": "community garden limited water vegetables pollinators",
                "pragmatics": {
                    "question_units": [
                        "Why do you prefer the two-zone trial first, and what result would make you change your recommendation?"
                    ]
                },
            },
        }
    )

    unrelated = evaluate_response_coverage(
        plan,
        "An algorithm can change its result when a required instruction is omitted.",
    )
    relevant = evaluate_response_coverage(
        plan,
        "I prefer the two-zone trial because it is reversible; I would change the recommendation if the alternative helped both goals more.",
    )

    assert unrelated["all_required_addressed"] is False
    assert unrelated["items"][0]["matched_distinctive_terms"] == []
    assert relevant["all_required_addressed"] is True
    assert "trial" in relevant["items"][0]["matched_distinctive_terms"]


def test_dialogue_workspace_resolves_plural_option_reference_but_holds_singular_ambiguity(tmp_path):
    conn, session_id = _conn(tmp_path)
    previous = [{"role": "selene", "preview": "The options are memory and voice."}]
    plural_text = "How do they differ?"
    plural = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": plural_text,
            "intent_decision": classify_chat_intent(plural_text),
            "conversation_events": previous,
        },
    )
    singular_text = "How does it differ?"
    singular = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": singular_text,
            "intent_decision": classify_chat_intent(singular_text),
            "conversation_events": previous,
        },
    )

    assert plural["pragmatics"]["resolved_reference"]["resolved_to"] == "memory and voice"
    assert plural["pragmatics"]["resolved_reference"]["resolution_status"] == "resolved"
    assert singular["pragmatics"]["resolved_reference"]["resolved_to"] == ""
    assert singular["pragmatics"]["resolved_reference"]["resolution_status"] == "materially_ambiguous"


def test_dialogue_workspace_extracts_structured_correction_and_direct_requests(tmp_path):
    conn, session_id = _conn(tmp_path)
    correction_text = "Actually, I meant the semantic layer, not the voice layer."
    corrected = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": correction_text,
            "intent_decision": classify_chat_intent(correction_text),
            "conversation_events": [{"role": "selene", "preview": "The voice layer comes first."}],
        },
    )
    request_text = "Compare memory and voice. Explain which comes first."
    requested = prepare_dialogue_turn(
        conn,
        {"session_id": session_id, "text": request_text, "intent_decision": classify_chat_intent(request_text)},
    )

    correction = corrected["pragmatics"]["correction_refinement"]
    assert correction["corrected_meaning"] == "the semantic layer"
    assert correction["replaced_meaning"] == "the voice layer"
    assert correction["durable_memory_write"] is False
    assert [unit["kind"] for unit in requested["pragmatics"]["utterance_units"]] == [
        "direct_request",
        "direct_request",
    ]


def test_dialogue_workspace_routes_are_status_only_and_idempotent(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "Could you explain that?"
    first = route_request(
        conn,
        "dialogue_workspace.refresh",
        {"session_id": session_id, "text": text, "intent_decision": classify_chat_intent(text)},
    )["result"]
    second = route_request(conn, "dialogue_workspace.status", {"session_id": session_id})["result"]

    assert first["pragmatics"]["indirect_request"]["detected"] is True
    assert second["session_id"] == session_id
    assert conn.execute("SELECT COUNT(*) FROM selene_dialogue_workspaces WHERE session_id = ?", (session_id,)).fetchone()[0] == 1
    assert dialogue_workspace_status(conn, session_id)["provenance_boundary"].startswith("session_scoped")


def test_dialogue_workspace_persists_a_session_only_thread_braid_across_turns(tmp_path):
    conn, session_id = _conn(tmp_path)
    first_text = "Plan the garden layout."
    first = prepare_dialogue_turn(
        conn,
        {"session_id": session_id, "text": first_text, "intent_decision": classify_chat_intent(first_text)},
    )
    second_text = "Separately, work out the water schedule."
    second = prepare_dialogue_turn(
        conn,
        {"session_id": session_id, "text": second_text, "intent_decision": classify_chat_intent(second_text)},
    )
    third_text = "Back to the garden layout: using that, revise bed placement."
    third = prepare_dialogue_turn(
        conn,
        {"session_id": session_id, "text": third_text, "intent_decision": classify_chat_intent(third_text)},
    )

    first_braid = first["pragmatics"]["thread_braid"]
    second_braid = second["pragmatics"]["thread_braid"]
    third_braid = third["pragmatics"]["thread_braid"]
    assert second_braid["turn_traversal"][0]["action"] == "branch"
    assert third_braid["turn_traversal"][0]["action"] == "revise_with_dependency"
    assert third_braid["turn_traversal"][0]["thread_id"] == first_braid["active_thread_id"]
    assert third_braid["turn_traversal"][0]["dependency_thread_id"] == second_braid["active_thread_id"]
    assert dialogue_workspace_status(conn, session_id)["pragmatics"]["thread_braid"]["session_scoped_only"] is True
    assert third["memory_write_active"] is False
