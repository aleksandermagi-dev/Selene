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


def test_dialogue_workspace_recognizes_learning_activity_request_verbs(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = (
        "Separate the observation from the interpretation, then describe a fair investigation, "
        "and explain why the conclusion can be revised."
    )
    prepared = prepare_dialogue_turn(
        conn,
        {"session_id": session_id, "text": text, "intent_decision": classify_chat_intent(text)},
    )
    plan = build_pragmatic_plan({"prompt": text, "dialogue_workspace": prepared})

    sources = [item["source_text"].lower() for item in plan["response_obligations"]]
    assert len(sources) == 3
    assert sources[0].startswith("separate the observation")
    assert sources[1].startswith("describe a fair investigation")
    assert sources[2].startswith("explain why the conclusion")


def test_learning_activity_statement_is_not_treated_as_a_correction(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "This is not pass or fail. It is a way to see what is connected and what needs more study."
    prepared = prepare_dialogue_turn(
        conn,
        {"session_id": session_id, "text": text, "intent_decision": classify_chat_intent(text)},
    )

    assert prepared["pragmatics"]["correction_refinement"]["detected"] is False
    assert all(item["kind"] != "correction" for item in prepared["pragmatics"]["utterance_units"])


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


def test_unanswered_loop_is_preserved_but_does_not_silently_enter_a_new_topic(tmp_path):
    conn, session_id = _conn(tmp_path)
    first_text = "How can I make a paper pinwheel spin?"
    first = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": first_text,
            "intent_decision": classify_chat_intent(first_text),
        },
    )
    record_dialogue_response(
        conn,
        {
            "session_id": session_id,
            "candidate_text": "I need to work that through more carefully.",
            "coverage_evaluation": {"answered_loop_ids": [], "items": []},
        },
    )

    second_text = "Tell me something playful about the garden."
    second = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": second_text,
            "intent_decision": classify_chat_intent(second_text),
        },
    )
    plan = build_pragmatic_plan({"prompt": second_text, "dialogue_workspace": second})

    prior_loop = next(item for item in second["open_loops"] if item["id"] in first["new_loop_ids"])
    assert prior_loop["lifecycle_state"] == "held_for_supported_return"
    assert prior_loop["eligible_current_turn"] is False
    assert all(item.get("loop_id") != prior_loop["id"] for item in plan["response_obligations"])


def test_named_callback_releases_a_preserved_loop_and_correction_supersedes_it(tmp_path):
    conn, session_id = _conn(tmp_path)
    first_text = "Which pinwheel material should we use?"
    first = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": first_text,
            "intent_decision": classify_chat_intent(first_text),
        },
    )
    record_dialogue_response(
        conn,
        {
            "session_id": session_id,
            "candidate_text": "I am holding that question for a supported return.",
            "coverage_evaluation": {"answered_loop_ids": [], "items": []},
        },
    )

    callback_text = "Back to the pinwheel material question."
    callback = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": callback_text,
            "intent_decision": classify_chat_intent(callback_text),
            "contextual_follow_up": {
                "detected": True,
                "kind": "named_callback",
                "preserve_active_topic": True,
            },
        },
    )
    released = next(item for item in callback["open_loops"] if item["id"] in first["new_loop_ids"])
    assert released["lifecycle_state"] == "released_for_callback"
    assert released["eligible_current_turn"] is True

    correction_text = "Actually, I meant the paper shape, not the material."
    corrected = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": correction_text,
            "intent_decision": classify_chat_intent(correction_text),
            "conversation_events": [{"role": "selene", "preview": "We were comparing pinwheel materials."}],
        },
    )
    retired = next(item for item in corrected["completed_loops"] if item["id"] in first["new_loop_ids"])
    assert retired["status"] == "superseded_by_correction"
    assert retired["lifecycle_state"] == "superseded"


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


def test_dialogue_workspace_carries_selective_revision_and_ancestry_in_session_only(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "Newtonian mechanics applies only at low speeds and weak gravity."
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
            "conversation_events": [
                {"role": "selene", "preview": "Newtonian mechanics explains motion."}
            ],
        },
    )

    revision = result["pragmatics"]["epistemic_update_plan"]
    update = result["epistemic_updates"][-1]
    assert revision["update_kind"] == "scope_restriction"
    assert revision["model_ancestry"]["preserved"] is True
    assert update["validity"] == "earlier_claim_valid_only_in_stated_scope"
    assert update["durable_memory_write"] is False
    assert result["memory_write_active"] is False


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


def test_life_out_there_is_not_misread_as_a_previous_turn_reference(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "Do you think there could be life out there?"
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
            "conversation_events": [
                {"role": "selene", "preview": "We were discussing the garden gate."}
            ],
        },
    )

    assert result["pragmatics"]["resolved_reference"] is None


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


def test_explicit_topic_shift_with_actually_is_not_a_correction_unit(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "Actually, separate question: how should uncertainty sound?"
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
            "contextual_follow_up": {
                "detected": True,
                "kind": "topic_shift",
                "preserve_active_topic": False,
            },
            "conversation_events": [
                {"role": "selene", "preview": "We were discussing memory sequencing."}
            ],
        },
    )

    assert result["pragmatics"]["correction_refinement"]["detected"] is False
    assert all(
        unit["kind"] != "correction"
        for unit in result["pragmatics"]["utterance_units"]
    )


def test_dialogue_workspace_keeps_then_return_and_explain_as_a_direct_request(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = (
        "What is 18 times 7? "
        "Then return to the lesson question and explain why an exact answer is not the same as understanding."
    )
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
        },
    )
    plan = build_pragmatic_plan(
        {"prompt": text, "dialogue_workspace": result}
    )

    assert [item["kind"] for item in result["pragmatics"]["utterance_units"]] == [
        "question",
        "direct_request",
    ]
    assert [item["kind"] for item in plan["response_obligations"]] == [
        "direct_question",
        "reason",
    ]


def test_dialogue_workspace_extracts_phrase_meaning_correction_without_memory_write(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = "whats up means how are you"
    contextual = {
        "detected": True,
        "kind": "meaning_correction",
        "preserve_active_topic": True,
    }
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": {"intent": "correction", "dialogue_act": "correction"},
            "contextual_follow_up": contextual,
            "conversation_events": [
                {"role": "selene", "preview": "I'm not sure because I am missing context."}
            ],
        },
    )

    correction = result["pragmatics"]["correction_refinement"]
    assert correction["detected"] is True
    assert correction["replaced_meaning"] == "whats up"
    assert correction["corrected_meaning"] == "how are you"
    assert correction["durable_memory_write"] is False


def test_dialogue_workspace_splits_quoted_correction_from_confirmation_question(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = 'When I say "what\'s up," I mean "how are you." Does that distinction make sense?'
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
            "conversation_events": [{"role": "selene", "preview": "I am present and attentive."}],
        },
    )

    correction = result["pragmatics"]["correction_refinement"]
    assert correction["replaced_meaning"] == "what's up"
    assert correction["corrected_meaning"] == "how are you"
    assert result["pragmatics"]["question_units"] == ["Does that distinction make sense?"]
    assert [item["kind"] for item in result["pragmatics"]["utterance_units"]] == ["correction", "question"]


def test_dialogue_workspace_keeps_correction_and_followup_ask_separate_in_one_sentence(tmp_path):
    conn, session_id = _conn(tmp_path)
    text = (
        "Actually, I meant conversational uncertainty, not mathematical uncertainty, "
        "and can you compare them now?"
    )
    result = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "intent_decision": classify_chat_intent(text),
            "conversation_events": [{"role": "selene", "preview": "I compared the wrong concepts."}],
        },
    )

    correction = result["pragmatics"]["correction_refinement"]
    assert correction["corrected_meaning"] == "conversational uncertainty"
    assert correction["replaced_meaning"] == "mathematical uncertainty"
    assert [item["kind"] for item in result["pragmatics"]["utterance_units"]] == [
        "correction",
        "question",
    ]
    assert result["pragmatics"]["question_units"] == ["can you compare them now?"]


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


def test_dialogue_workspace_keeps_bounded_visible_response_landmarks_in_session_only(tmp_path):
    conn, session_id = _conn(tmp_path)
    prompt = "Which garden pilot should we run first?"
    prepare_dialogue_turn(
        conn,
        {"session_id": session_id, "text": prompt, "intent_decision": classify_chat_intent(prompt)},
    )
    recorded = record_dialogue_response(
        conn,
        {
            "session_id": session_id,
            "candidate_text": (
                "I recommend the reversible garden pilot first. "
                "If water use rises beyond the limit, I would reopen that recommendation."
            ),
            "coverage_evaluation": {"all_required_addressed": True, "answered_loop_ids": []},
        },
    )
    restored = dialogue_workspace_status(conn, session_id)

    assert [item["kind"] for item in recorded["session_landmarks"]] == ["recommendation", "condition"]
    assert restored["session_landmarks"] == recorded["session_landmarks"]
    assert all(item["scope"] == "current_session_only" for item in restored["session_landmarks"])
    assert restored["memory_write_active"] is False
    assert restored["runtime_memory_recall"] is False
