from __future__ import annotations

from selene.chat_intent import classify_chat_intent
from selene.conversation_continuity import resolve_conversation_continuity
from selene.conversation_thread_loom import build_thread_braid
from selene.db import connect, init_db
from selene.dialogue_workspace import dialogue_workspace_status, prepare_dialogue_turn
from selene.long_thread_endurance import (
    build_long_thread_endurance_plan,
    long_thread_endurance_status,
    retain_structural_records,
)
from selene.module_router import route_request
from selene.native_language_organ import realize_native_language


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    conn.execute(
        """
        INSERT INTO selene_chat_sessions(title, status, source_mode)
        VALUES (?, ?, ?)
        """,
        (
            "Long thread endurance test",
            "selene_chat_active_supervised",
            "selene_supervised_speech",
        ),
    )
    conn.commit()
    session_id = int(
        conn.execute(
            "SELECT id FROM selene_chat_sessions ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
    )
    return conn, session_id


def _assert_bounded(result):
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["hidden_chain_of_thought_exposed"] is False


def _branch(prior, number, *, protected=()):
    return build_thread_braid(
        {
            "session_id": 73,
            "prompt": f"Separate topic: marker{number}.",
            "prior_braid": prior,
            "protected_thread_ids": list(protected),
        }
    )


def test_status_uses_structural_summaries_instead_of_raw_transcript_growth():
    status = long_thread_endurance_status()

    assert status["status"] == "long_thread_endurance_ready"
    assert status["limits"]["working_threads"] == 16
    assert status["limits"]["thread_index"] == 64
    assert status["raw_transcript_is_endurance_state"] is False
    assert status["session_checkpoint_is_memory"] is False
    assert status["automatic_durable_promotion"] is False
    _assert_bounded(status)


def test_named_return_reaches_a_thread_older_than_the_working_set():
    braid = build_thread_braid(
        {
            "session_id": 73,
            "prompt": "Let us begin with the cedar garden plan.",
            "active_topic": "cedar garden plan",
        }
    )
    original_id = braid["active_thread_id"]
    for number in range(1, 25):
        braid = _branch(braid, number)

    assert len(braid["threads"]) == 16
    assert len(braid["thread_index"]) == 25
    assert original_id not in {item["id"] for item in braid["threads"]}
    assert original_id in {item["id"] for item in braid["thread_index"]}

    returned = build_thread_braid(
        {
            "session_id": 73,
            "prompt": "Back to the cedar garden plan: why did we start there?",
            "prior_braid": braid,
        }
    )

    assert returned["active_thread_id"] == original_id
    assert original_id in {item["id"] for item in returned["threads"]}
    assert any(item["relation"] == "returns_to" for item in returned["edges"])
    assert returned["unresolved_returns"] == []
    assert returned["saturation_compaction"]["active"] is True
    _assert_bounded(returned)


def test_open_obligation_protects_an_old_paused_thread_during_index_saturation():
    braid = build_thread_braid(
        {
            "session_id": 73,
            "prompt": "Begin the amber bridge question.",
            "active_topic": "amber bridge question",
        }
    )
    protected_id = braid["active_thread_id"]
    for number in range(1, 71):
        braid = _branch(braid, number, protected=(protected_id,))

    index_ids = {item["id"] for item in braid["thread_index"]}
    working_ids = {item["id"] for item in braid["threads"]}
    assert len(braid["thread_index"]) == 64
    assert protected_id in index_ids
    assert protected_id in working_ids
    assert braid["saturation_compaction"]["protected_threads_preserved"] is True


def test_dialogue_workspace_keeps_more_than_twenty_unresolved_questions(tmp_path):
    conn, session_id = _conn(tmp_path)
    first_loop_id = ""
    for number in range(1, 31):
        prompt = f"Separate topic: orchard question {number}. What should we inspect for case {number}?"
        state = prepare_dialogue_turn(
            conn,
            {
                "session_id": session_id,
                "text": prompt,
                "intent_decision": classify_chat_intent(prompt),
            },
        )
        if number == 1:
            first_loop_id = state["new_loop_ids"][0]

    restored = dialogue_workspace_status(conn, session_id)
    loop_ids = {item["id"] for item in restored["open_loops"]}
    assert len(restored["open_loops"]) == 30
    assert first_loop_id in loop_ids
    assert all(item.get("thread_id") for item in restored["open_loops"])
    assert restored["long_thread_endurance"]["counts"]["open_loops"] == 30
    assert restored["long_thread_endurance"]["integrity"]["open_obligations_present"] is True


def test_structural_retention_keeps_required_unresolved_record_over_newer_noise():
    values = [
        {
            "id": "old-required",
            "status": "open",
            "required": True,
            "thread_id": "thread-old",
        }
    ] + [
        {"id": f"recent-{number}", "status": "completed"}
        for number in range(1, 12)
    ]
    retained = retain_structural_records(
        values,
        limit=5,
        protected_thread_ids={"thread-old"},
        unresolved_first=True,
    )

    assert "old-required" in {item["id"] for item in retained}
    assert len(retained) == 5


def test_endurance_plan_exposes_unresolved_return_without_inventing_a_question():
    workspace = {
        "open_loops": [{"id": "loop-1", "status": "open", "thread_id": "thread-a"}],
        "pragmatics": {
            "thread_braid": {
                "active_thread_id": "thread-b",
                "threads": [{"id": "thread-b", "topic": "current", "state": "active"}],
                "thread_index": [
                    {"id": "thread-a", "topic": "older", "state": "paused"},
                    {"id": "thread-b", "topic": "current", "state": "active"},
                ],
                "unresolved_returns": [
                    {
                        "requested_topic": "that earlier one",
                        "ask_only_if_material": True,
                    }
                ],
            }
        },
    }
    plan = build_long_thread_endurance_plan({"dialogue_workspace": workspace})

    assert plan["needs_material_clarification"] is True
    assert plan["automatic_question_generated"] is False
    assert plan["integrity"]["open_obligations_present"] is True
    assert set(plan["protected_thread_ids"]) == {"thread-a", "thread-b"}
    assert plan["continuation_handoff"]["open_loop_ids"] == ["loop-1"]
    _assert_bounded(plan)


def test_continuity_uses_old_structural_index_after_return_becomes_active():
    braid = build_thread_braid(
        {
            "session_id": 73,
            "prompt": "Start with the violet engine comparison.",
            "active_topic": "violet engine comparison",
        }
    )
    original_id = braid["active_thread_id"]
    for number in range(1, 23):
        braid = _branch(braid, number)
    returned = build_thread_braid(
        {
            "session_id": 73,
            "prompt": "Back to the violet engine comparison.",
            "prior_braid": braid,
        }
    )
    continuity = resolve_conversation_continuity(
        {
            "prompt": "Back to the violet engine comparison.",
            "contextual_follow_up": {"detected": True, "kind": "named_callback"},
            "dialogue_workspace": {"pragmatics": {"thread_braid": returned}},
        }
    )

    assert continuity["mode"] == "named_thread_return"
    assert continuity["selected_thread_id"] == original_id
    assert continuity["selected_target"]["kind"] == "session_thread"


def test_named_return_can_recover_an_old_thread_checkpoint_beyond_recent_window():
    checkpoints = [
        {
            "status": "session_topic_checkpoint_ready",
            "checkpoint_id": f"checkpoint-{number}",
            "thread_id": f"thread-{number}",
            "topic": f"marker{number} discussion",
            "established_visible_statements": [
                f"The settled thesis for marker{number} remains revisable."
            ],
            "reasoning_state_capsule": {
                "current_conclusion": (
                    f"The settled thesis for marker{number} remains revisable."
                )
            },
        }
        for number in range(1, 51)
    ]
    result = resolve_conversation_continuity(
        {
            "prompt": "Back to the marker2 discussion.",
            "contextual_follow_up": {"detected": True, "kind": "named_callback"},
            "dialogue_workspace": {
                "pragmatics": {
                    "topic_checkpoints": checkpoints,
                    "thread_braid": {
                        "active_thread_id": "thread-2",
                        "prior_active_thread_id": "thread-50",
                        "threads": [
                            {"id": "thread-2", "topic": "marker2 discussion", "state": "active"},
                            {"id": "thread-50", "topic": "marker50 discussion", "state": "paused"},
                        ],
                        "edges": [
                            {
                                "source_thread_id": "thread-50",
                                "target_thread_id": "thread-2",
                                "relation": "returns_to",
                            }
                        ],
                    },
                }
            },
        }
    )

    assert result["selected_checkpoint_id"] == "checkpoint-2"
    assert "settled thesis for marker2" in result["grounding_text"]


def test_nlo_and_read_only_routes_observe_endurance_without_owning_selection(tmp_path):
    conn, _ = _conn(tmp_path)
    plan = build_long_thread_endurance_plan(
        {
            "dialogue_workspace": {
                "pragmatics": {
                    "thread_braid": {
                        "active_thread_id": "thread-one",
                        "threads": [
                            {"id": "thread-one", "topic": "one", "state": "active"}
                        ],
                    }
                }
            }
        }
    )
    nlo = realize_native_language(
        conn,
        {
            "prompt": "Continue the current point.",
            "content_seed": "The current point remains open for one more comparison.",
            "intent_decision": classify_chat_intent("Continue the current point."),
            "long_thread_endurance": plan,
        },
    )
    before = conn.total_changes
    status = route_request(conn, "conversation.long_thread_endurance.status", {})["result"]
    preview = route_request(
        conn,
        "conversation.long_thread_endurance.preview",
        {"dialogue_workspace": {}},
    )["result"]

    handoff = nlo["long_thread_endurance"]
    assert handoff["observed"] is True
    assert handoff["selection_authority"] is False
    assert nlo["meaning_packet"]["long_thread_endurance"] == handoff
    assert nlo["discourse_plan"]["long_thread_endurance"] == handoff
    assert nlo["voice_handoff"]["long_thread_endurance"] == handoff
    assert status["status"] == "long_thread_endurance_ready"
    assert preview["status"] == "long_thread_endurance_plan_ready"
    assert conn.total_changes == before
    _assert_bounded(status)
