from __future__ import annotations

from selene.bounded_organ_coalition import build_bounded_organ_coalition
from selene.chat_intent import classify_chat_intent
from selene.db import connect, init_db
from selene.dialogue_workspace import (
    dialogue_workspace_status,
    prepare_dialogue_turn,
    record_dialogue_response,
)
from selene.dual_horizon_context import (
    attach_dual_horizon_to_spine,
    build_dual_horizon_context,
    build_session_topic_checkpoint,
    merge_session_topic_checkpoints,
)
from selene.metacognition import evaluate_metacognition
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
            "Dual horizon test",
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


def _spine():
    return {
        "status": "conversation_spine_ready",
        "turn_id": "dual-horizon-turn",
        "active_topic": "compare two explanations",
        "active_thread_id": "thread-explanations",
        "open_obligations": [
            {
                "id": "compare",
                "kind": "comparison",
                "source_text": "Which explanation fits the evidence better?",
                "required": True,
            }
        ],
        "previous_answer": {
            "available": True,
            "preview": "The first explanation currently fits two observations.",
        },
        "epistemic_revision": {},
    }


def _dialogue(session_id=7):
    return {
        "session_id": session_id,
        "active_topic": "compare two explanations",
        "side_topics": ["measurement noise", "future experiment"],
        "entities": [{"name": "Newton", "source": "current_turn"}],
        "referents": {
            "that": {
                "token": "that",
                "resolved_to": "the first explanation",
            }
        },
        "corrections": [
            {
                "corrected_meaning": "The second observation is provisional.",
                "status": "active_refinement",
            }
        ],
        "preferences": {
            "scope": "current_session_only",
            "transient": {
                "active": True,
                "status": "active",
                "directives": {"response_depth": "brief"},
                "remaining_turns": 2,
            },
        },
        "pragmatics": {
            "utterance_units": [
                {
                    "id": "utterance_1",
                    "text": "Which explanation fits the evidence better?",
                    "kind": "question",
                }
            ],
            "resolved_reference": {
                "resolved_to": "the first explanation",
                "confidence": "bounded_visible_context",
            },
            "thread_braid": {
                "active_thread_id": "thread-explanations",
                "threads": [
                    {
                        "id": "thread-explanations",
                        "topic": "compare two explanations",
                        "state": "active",
                    },
                    {
                        "id": "thread-experiment",
                        "topic": "future experiment",
                        "state": "paused",
                    },
                ],
                "turn_traversal": [
                    {
                        "thread_id": "thread-explanations",
                        "action": "continue",
                        "text": "Compare the explanations.",
                    }
                ],
            },
            "topic_checkpoints": [],
        },
    }


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["durable_memory_write"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_corpus_loaded"] is False
    assert result["retained_knowledge_write_active"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False


def test_visible_completed_turn_builds_a_session_checkpoint_not_a_memory():
    checkpoint = build_session_topic_checkpoint(
        {
            "session_id": 7,
            "candidate_text": (
                "I recommend the first explanation because it fits both "
                "observations. However, the second observation is provisional."
            ),
            "dialogue_workspace": _dialogue(),
            "conversation_spine": _spine(),
            "response_coverage": {
                "all_required_addressed": True,
                "items": [
                    {"obligation_id": "compare", "addressed": True}
                ],
            },
            "metacognition": {
                "confidence_vector": {
                    "answer_confidence": "provisional_supported"
                },
                "stopping": {"reason": "current_question_answered"},
            },
            "source_refs": ["experiment:notebook:visible-observation"],
        }
    )

    assert checkpoint["status"] == "session_topic_checkpoint_ready"
    assert checkpoint["revision"] == 1
    assert checkpoint["thread_id"] == "thread-explanations"
    assert checkpoint["decisions_and_why"]
    assert checkpoint["known_limits"]
    assert checkpoint["reasoning_state_capsule"]["visible_summary_only"] is True
    assert (
        checkpoint["reasoning_state_capsule"][
            "hidden_chain_of_thought_exposed"
        ]
        is False
    )
    assert checkpoint["session_only"] is True
    assert checkpoint["durable_memory"] is False
    assert checkpoint["memory_proposal_created"] is False
    assert checkpoint["retention_eligible"] is False
    _assert_locked(checkpoint)


def test_greeting_or_unfinished_turn_does_not_create_a_checkpoint():
    checkpoint = build_session_topic_checkpoint(
        {
            "session_id": 7,
            "candidate_text": "Good morning :)",
            "dialogue_workspace": {
                "active_topic": "greeting",
                "pragmatics": {"thread_braid": {}},
            },
            "conversation_spine": {"open_obligations": []},
            "response_coverage": {"all_required_addressed": True},
        }
    )

    assert checkpoint["status"] == "session_topic_checkpoint_not_created"
    assert checkpoint["eligible"] is False
    assert checkpoint["memory_proposal_created"] is False
    _assert_locked(checkpoint)


def test_same_thread_checkpoint_is_a_visible_revision_with_parent_ancestry():
    first = build_session_topic_checkpoint(
        {
            "session_id": 7,
            "candidate_text": "I recommend the first explanation.",
            "dialogue_workspace": _dialogue(),
            "conversation_spine": _spine(),
            "response_coverage": {
                "all_required_addressed": True,
                "items": [
                    {"obligation_id": "compare", "addressed": True}
                ],
            },
        }
    )
    prior = merge_session_topic_checkpoints([], first)
    second_dialogue = _dialogue()
    second_dialogue["pragmatics"]["topic_checkpoints"] = prior
    second = build_session_topic_checkpoint(
        {
            "session_id": 7,
            "candidate_text": (
                "I recommend the second explanation because the new "
                "measurement changes the comparison."
            ),
            "dialogue_workspace": second_dialogue,
            "conversation_spine": _spine(),
            "response_coverage": {
                "all_required_addressed": True,
                "items": [
                    {"obligation_id": "compare", "addressed": True}
                ],
            },
            "prior_checkpoints": prior,
        }
    )

    assert second["revision"] == 2
    assert second["parent_checkpoint_id"] == first["checkpoint_id"]
    merged = merge_session_topic_checkpoints(prior, second)
    assert [item["revision"] for item in merged] == [1, 2]


def test_dual_horizon_selects_current_and_approved_packets_only():
    checkpoint = build_session_topic_checkpoint(
        {
            "session_id": 7,
            "candidate_text": (
                "I recommend the first explanation because it fits the "
                "orbital stability evidence."
            ),
            "dialogue_workspace": _dialogue(),
            "conversation_spine": _spine(),
            "response_coverage": {
                "all_required_addressed": True,
                "items": [
                    {"obligation_id": "compare", "addressed": True}
                ],
            },
        }
    )
    dialogue = _dialogue()
    dialogue["pragmatics"]["topic_checkpoints"] = [checkpoint]
    result = build_dual_horizon_context(
        {
            "prompt": (
                "How does the orbital stability evidence affect the first "
                "explanation?"
            ),
            "dialogue_workspace": dialogue,
            "conversation_spine": _spine(),
            "memory_context": {
                "memory_context_used": True,
                "retrieval_mode": "approved_semantic_retrieval",
                "items": [
                    {
                        "id": 11,
                        "title": "Orbital stability discussion",
                        "summary": (
                            "Aleks and Selene previously compared orbital "
                            "stability explanations."
                        ),
                        "retrieval_eligible": True,
                        "source_refs": ["memory:approved:11"],
                    },
                    {
                        "id": 12,
                        "title": "Unapproved orbital note",
                        "summary": "This must not be selected.",
                        "retrieval_eligible": False,
                        "source_refs": ["memory:proposal:12"],
                    },
                ],
            },
            "comprehension_context": {
                "knowledge_context": {
                    "answer_eligible_items": [
                        {
                            "id": 21,
                            "domain": "orbital stability",
                            "central_claim": (
                                "Orbital stability depends on the balance of "
                                "forces and perturbations."
                            ),
                            "source_refs": ["teaching:approved:21"],
                        },
                        {
                            "id": 22,
                            "domain": "orbital stability",
                            "central_claim": "A provenance-free claim.",
                            "source_refs": [],
                        },
                    ]
                }
            },
            "source_packets": [
                {
                    "source_ref": "paper:orbit:current",
                    "title": "Orbital stability paper",
                    "statement": (
                        "The measured perturbation remained below the stated "
                        "stability threshold."
                    ),
                },
                {
                    "title": "Unattributed orbital statement",
                    "statement": "This has no source reference.",
                },
            ],
            "max_active_items": 16,
            "max_approved_items": 12,
        }
    )

    active = result["active_horizon"]["selected_items"]
    approved = result["approved_long_range_horizon"]["selected_items"]
    classes = {item["source_class"] for item in approved}
    ids = {item["context_id"] for item in approved}
    assert result["status"] == "dual_horizon_context_ready"
    assert any(
        item["source_class"] == "current_utterance_unit" for item in active
    )
    assert any(
        item["source_class"] == "conversation_thread_braid" for item in active
    )
    assert any(
        item["source_class"] == "current_session_preference" for item in active
    )
    assert {
        "approved_personal_memory",
        "approved_general_knowledge",
        "session_topic_checkpoint",
        "current_attributed_source",
    }.issubset(classes)
    assert "approved-memory-12" not in ids
    assert "approved-knowledge-22" not in ids
    assert result["raw_items_loaded"] == 0
    assert result["review_only_items_loaded"] == 0
    assert result["unapproved_memory_items_loaded"] == 0
    assert result["checkpoint_is_memory"] is False
    assert result["grounding_uses_selected_packets_only"] is True
    _assert_locked(result)


def test_active_budget_prioritizes_obligations_corrections_and_preferences():
    dialogue = _dialogue()
    dialogue["pragmatics"]["utterance_units"] = [
        {
            "id": f"utterance_{index}",
            "text": f"Statement number {index} about the comparison.",
            "kind": "statement",
        }
        for index in range(1, 10)
    ]
    result = build_dual_horizon_context(
        {
            "prompt": "Compare the explanations and keep it brief.",
            "dialogue_workspace": dialogue,
            "conversation_spine": _spine(),
            "max_active_items": 5,
        }
    )

    relationships = {
        item["relationship_type"]
        for item in result["active_horizon"]["selected_items"]
    }
    assert "open_response_obligation" in relationships
    assert "correction" in relationships
    assert "temporary_response_shape" in relationships
    assert "current_input" in relationships

    working = result["working_context_contract"]
    assert working["attention_budget"]["maximum_items"] == 5
    assert working["attention_budget"]["selected_count"] == 5
    assert working["attention_budget"]["overflow_count"] > 0
    assert working["cleanup"]["attention_overflow_dropped_ids"]
    assert working["cleanup"]["dropped_content_retained_as_memory"] is False
    assert working["expiry"]["durable_items_created"] == 0
    assert working["session_context_is_personal_memory"] is False


def test_working_context_preserves_a_visible_resume_point_without_durable_retention():
    dialogue = _dialogue()
    dialogue["pragmatics"]["topic_transition"] = {"kind": "interruption"}
    result = build_dual_horizon_context(
        {
            "prompt": "Pause this for a moment; I need to answer the door.",
            "dialogue_workspace": dialogue,
            "conversation_spine": _spine(),
            "max_active_items": 8,
        }
    )

    working = result["working_context_contract"]
    resume = working["interruption_resume"]
    assert resume["interruption_detected"] is True
    assert resume["active_thread_id"] == "thread-explanations"
    assert resume["paused_threads"][0]["thread_id"] == "thread-experiment"
    assert resume["resume_uses_visible_thread_or_checkpoint_only"] is True
    assert resume["resume_creates_memory"] is False
    _assert_locked(result)


def test_spine_nlo_metacognition_and_coalition_observe_without_new_authority(
    tmp_path,
):
    conn, _ = _conn(tmp_path)
    dual_horizon = build_dual_horizon_context(
        {
            "prompt": "Which explanation fits better?",
            "dialogue_workspace": _dialogue(),
            "conversation_spine": _spine(),
        }
    )
    spine = attach_dual_horizon_to_spine(_spine(), dual_horizon)
    coalition = build_bounded_organ_coalition(
        {
            "prompt": "Which explanation fits better?",
            "conversation_spine": spine,
            "core_mind_route": {"selected_route": "answer_now"},
            "dual_horizon_context": dual_horizon,
        }
    )
    nlo = realize_native_language(
        conn,
        {
            "prompt": "Which explanation fits better?",
            "content_seed": "The first explanation currently fits better.",
            "intent_decision": classify_chat_intent(
                "Which explanation fits better?"
            ),
            "dual_horizon_context": dual_horizon,
            "organ_coalition": coalition,
        },
    )
    metacognition = evaluate_metacognition(
        {
            "prompt": "Which explanation fits better?",
            "candidate_text": "The first explanation currently fits better.",
            "response_coverage": {"unresolved_count": 0},
            "dual_horizon_context": dual_horizon,
            "organ_coalition": coalition,
        }
    )

    assert spine["version"] == "v3_dual_horizon_grounding"
    assert spine["grounded_prompt_source"] == (
        "dual_horizon_selected_context_packets"
    )
    layer = next(
        item
        for item in coalition["coordination_layers"]
        if item["id"] == "dual_horizon_context"
    )
    assert layer["is_organ"] is False
    assert layer["changes_answer_authority"] is False
    assert layer["writes_memory"] is False
    assert nlo["meaning_packet"]["dual_horizon_context"]["observed"] is True
    assert (
        nlo["meaning_packet"]["dual_horizon_context"]["selection_authority"]
        is False
    )
    assert metacognition["dual_horizon_context"]["observed"] is True
    assert (
        metacognition["dual_horizon_context"]["answer_rewrite_authority"]
        is False
    )


def test_dialogue_workspace_persists_topic_checkpoint_inside_session_state(
    tmp_path,
):
    conn, session_id = _conn(tmp_path)
    prompt = "Which explanation should we use?"
    prepared = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": prompt,
            "intent_decision": classify_chat_intent(prompt),
        },
    )
    recorded = record_dialogue_response(
        conn,
        {
            "session_id": session_id,
            "candidate_text": (
                "I recommend the first explanation because it fits the "
                "current evidence."
            ),
            "conversation_spine": {
                "status": "conversation_spine_ready",
                "active_topic": prepared["active_topic"],
                "active_thread_id": prepared["pragmatics"]["thread_braid"][
                    "active_thread_id"
                ],
                "open_obligations": [
                    {
                        "id": "recommend",
                        "kind": "recommendation",
                        "source_text": prompt,
                    }
                ],
            },
            "coverage_evaluation": {
                "all_required_addressed": True,
                "items": [
                    {"obligation_id": "recommend", "addressed": True}
                ],
            },
        },
    )
    restored = dialogue_workspace_status(conn, session_id)

    assert len(recorded["topic_checkpoints"]) == 1
    assert restored["topic_checkpoints"] == recorded["topic_checkpoints"]
    assert (
        restored["latest_topic_checkpoint"]["checkpoint_id"]
        == recorded["latest_topic_checkpoint"]["checkpoint_id"]
    )
    assert restored["latest_topic_checkpoint"]["durable_memory"] is False
