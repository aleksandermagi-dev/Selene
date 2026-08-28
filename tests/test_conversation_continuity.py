from __future__ import annotations

import sqlite3

from selene.conversation_continuity import (
    conversation_continuity_status,
    resolve_conversation_continuity,
)
from selene.conversation_spine import build_conversation_spine
from selene.conversation_thread_loom import build_thread_braid
from selene.module_router import route_request


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["durable_memory_write"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def _landmark(identifier: str, thread_id: str, topic: str, summary: str) -> dict:
    return {
        "id": identifier,
        "thread_id": thread_id,
        "topic": topic,
        "summary": summary,
        "coverage_complete_at_recording": True,
        "scope": "current_session_only",
    }


def test_immediate_follow_up_binds_only_to_the_immediate_visible_answer():
    result = resolve_conversation_continuity(
        {
            "prompt": "Why is that?",
            "contextual_follow_up": {
                "detected": True,
                "kind": "reason_follow_up",
                "previous_assistant_preview": "A reversible trial is safer first.",
            },
            "dialogue_workspace": {
                "pragmatics": {
                    "thread_braid": {
                        "active_thread_id": "thread-garden",
                        "threads": [
                            {"id": "thread-garden", "topic": "garden trial", "state": "active"}
                        ],
                    }
                }
            },
        }
    )

    assert result["mode"] == "immediate_follow_up"
    assert result["immediate_previous_answer_relevant"] is True
    assert result["selected_target"]["kind"] == "immediate_answer"
    assert "reversible trial" in result["grounding_text"]
    assert result["session_context_is_durable_memory"] is False
    _assert_locked(result)


def test_named_return_selects_the_older_thread_landmark_not_the_last_answer():
    garden = _landmark(
        "garden-landmark",
        "thread-garden",
        "garden water plan",
        "The two-zone trial is reversible and uses less water.",
    )
    sources = _landmark(
        "source-landmark",
        "thread-sources",
        "source trust",
        "The most recent answer concerned source attribution.",
    )
    result = resolve_conversation_continuity(
        {
            "prompt": "Back to the garden water plan: why was the trial first?",
            "contextual_follow_up": {
                "detected": True,
                "kind": "named_callback",
                "previous_assistant_preview": sources["summary"],
                "session_landmarks": [garden, sources],
            },
            "dialogue_workspace": {
                "pragmatics": {
                    "session_landmarks": [garden, sources],
                    "thread_braid": {
                        "active_thread_id": "thread-garden",
                        "prior_active_thread_id": "thread-sources",
                        "threads": [
                            {"id": "thread-garden", "topic": "garden water plan", "state": "active"},
                            {"id": "thread-sources", "topic": "source trust", "state": "paused"},
                        ],
                        "edges": [
                            {
                                "source_thread_id": "thread-sources",
                                "target_thread_id": "thread-garden",
                                "relation": "returns_to",
                            }
                        ],
                    },
                }
            },
        }
    )

    assert result["mode"] == "named_thread_return"
    assert result["selected_thread_id"] == "thread-garden"
    assert result["selected_landmark_ids"] == ["garden-landmark"]
    assert result["immediate_previous_answer_relevant"] is False
    assert "two-zone trial" in result["grounding_text"]
    assert "source attribution" not in result["grounding_text"]
    assert result["multiple_threads_preserved"] is True
    _assert_locked(result)


def test_materially_ambiguous_return_holds_only_that_binding_in_a_mixed_turn():
    result = resolve_conversation_continuity(
        {
            "prompt": "Back to that one, and summarize the settled points.",
            "intent_decision": {
                "mixed_intent": True,
                "dialogue_acts": ["request", "question"],
            },
            "contextual_follow_up": {"detected": True, "kind": "named_callback"},
            "dialogue_workspace": {
                "pragmatics": {
                    "resolved_reference": {
                        "token": "that one",
                        "resolution_status": "materially_ambiguous",
                        "ask_if_materially_ambiguous": True,
                    },
                    "thread_braid": {
                        "unresolved_returns": [
                            {
                                "requested_topic": "that one",
                                "ask_only_if_material": True,
                            }
                        ]
                    },
                }
            },
        }
    )

    assert result["mode"] == "material_ambiguity_hold"
    assert result["clarification_needed"] is True
    assert result["other_supported_parts_may_continue"] is True
    assert result["clarification_question_generated"] is False
    assert result["grounding_fragments"] == []
    _assert_locked(result)


def test_old_unresolved_return_does_not_override_an_immediate_answer_follow_up():
    result = resolve_conversation_continuity(
        {
            "prompt": "That answer can be provisional. What observation would change it?",
            "contextual_follow_up": {
                "detected": True,
                "kind": "answer_development",
                "previous_assistant_preview": (
                    "My current guess is surface contamination; a cleaned test spot "
                    "would distinguish it from an adhesive mismatch."
                ),
            },
            "dialogue_workspace": {
                "pragmatics": {
                    "thread_braid": {
                        "unresolved_returns": [
                            {
                                "requested_topic": "an older topic",
                                "ask_only_if_material": True,
                            }
                        ]
                    },
                    "topic_checkpoints": [
                        {
                            "checkpoint_id": "older-checkpoint",
                            "topic": "an older unrelated plan",
                            "reasoning_state_capsule": {
                                "current_conclusion": "Keep the charging cable on the desk."
                            },
                        }
                    ],
                }
            },
        }
    )

    assert result["mode"] == "immediate_follow_up"
    assert result["clarification_needed"] is False
    assert result["immediate_previous_answer_relevant"] is True
    assert "surface contamination" in result["grounding_text"]
    assert "charging cable" not in result["grounding_text"]
    _assert_locked(result)


def test_session_summary_preserves_landmarks_from_more_than_one_open_thread():
    landmarks = [
        _landmark("garden", "thread-garden", "garden", "The garden trial remains reversible."),
        _landmark("sources", "thread-sources", "sources", "Source claims remain attributed."),
    ]
    result = resolve_conversation_continuity(
        {
            "prompt": "Can you summarize what we settled?",
            "contextual_follow_up": {
                "detected": True,
                "kind": "session_summary_request",
                "session_landmarks": landmarks,
            },
            "dialogue_workspace": {
                "pragmatics": {
                    "session_landmarks": landmarks,
                    "thread_braid": {
                        "active_thread_id": "thread-sources",
                        "threads": [
                            {"id": "thread-garden", "topic": "garden", "state": "paused"},
                            {"id": "thread-sources", "topic": "sources", "state": "active"},
                        ],
                    },
                }
            },
        }
    )

    assert result["mode"] == "session_summary"
    assert result["summary_scope"] == "visible_current_session"
    assert result["selected_landmark_ids"] == ["garden", "sources"]
    assert result["multiple_threads_preserved"] is True
    assert "garden trial" in result["grounding_text"]
    assert "Source claims" in result["grounding_text"]
    _assert_locked(result)


def test_bounded_pronoun_uses_the_resolved_session_referent_without_guessing():
    result = resolve_conversation_continuity(
        {
            "prompt": "Would it still be reversible?",
            "contextual_follow_up": {
                "previous_assistant_preview": (
                    "The two-zone trial is reversible under the current constraints."
                )
            },
            "dialogue_workspace": {
                "pragmatics": {
                    "resolved_reference": {
                        "token": "it",
                        "resolved_to": "the two-zone trial",
                        "resolution_status": "resolved",
                        "confidence": "bounded",
                    }
                }
            },
        }
    )

    assert result["mode"] == "implied_reference"
    assert result["selected_target"] == {
        "kind": "session_referent",
        "id": "it",
        "label": "the two-zone trial",
    }
    assert result["immediate_previous_answer_relevant"] is True
    assert "Resolved visible referent: the two-zone trial" in result["grounding_text"]
    assert result["binding_invents_prior_context"] is False
    _assert_locked(result)


def test_completed_correction_remains_ancestry_not_an_active_dependency_revision():
    result = resolve_conversation_continuity(
        {
            "prompt": "What should we work on next?",
            "contextual_follow_up": {"detected": False, "kind": ""},
            "dialogue_workspace": {
                "pragmatics": {
                    "correction_refinement": {"detected": False},
                    "epistemic_update_plan": {"detected": False},
                    "session_proposition_ledger": {
                        "recomputation": {
                            "state": "completed",
                            "recomputed_proposition_id": "recomputed-result",
                        }
                    },
                }
            },
        }
    )

    assert result["mode"] != "dependency_revision"
    assert result["revision_active"] is False
    _assert_locked(result)


def test_thread_loom_branches_on_a_named_new_topic_then_returns_to_the_old_one():
    initial = build_thread_braid(
        {
            "session_id": 31,
            "prompt": "Let us compare the garden water plans.",
            "active_topic": "garden water plans",
        }
    )
    branched = build_thread_braid(
        {
            "session_id": 31,
            "prompt": "Separate topic: source trust.",
            "prior_braid": initial,
        }
    )
    returned = build_thread_braid(
        {
            "session_id": 31,
            "prompt": "Back to the garden water plans: why was the trial first?",
            "prior_braid": branched,
        }
    )

    initial_id = initial["active_thread_id"]
    assert branched["active_thread_id"] != initial_id
    assert returned["active_thread_id"] == initial_id
    assert any(item["relation"] == "returns_to" for item in returned["edges"])
    assert returned["unresolved_returns"] == []
    _assert_locked(returned)


def test_spine_grounds_a_named_return_from_the_selected_landmark_only():
    garden = _landmark(
        "garden-landmark",
        "thread-garden",
        "garden plan",
        "The reversible garden trial was selected first.",
    )
    spine = build_conversation_spine(
        {
            "session_id": 41,
            "prompt": "Back to the garden plan: why was it first?",
            "contextual_follow_up": {
                "detected": True,
                "kind": "named_callback",
                "previous_assistant_preview": "The last answer discussed source attribution.",
                "session_landmarks": [garden],
            },
            "dialogue_workspace": {
                "active_topic": "garden plan",
                "pragmatics": {
                    "session_landmarks": [garden],
                    "thread_braid": {
                        "active_thread_id": "thread-garden",
                        "prior_active_thread_id": "thread-sources",
                        "threads": [
                            {"id": "thread-garden", "topic": "garden plan", "state": "active"},
                            {"id": "thread-sources", "topic": "sources", "state": "paused"},
                        ],
                        "edges": [
                            {
                                "source_thread_id": "thread-sources",
                                "target_thread_id": "thread-garden",
                                "relation": "returns_to",
                            }
                        ],
                    },
                    "question_units": ["Back to the garden plan: why was it first?"],
                    "utterance_units": [
                        {"kind": "question", "text": "Back to the garden plan: why was it first?"}
                    ],
                },
                "open_loops": [],
            },
        }
    )

    assert spine["continuity_mode"] == "named_thread_return"
    assert "reversible garden trial" in spine["grounded_prompt"]
    assert "source attribution" not in spine["grounded_prompt"]
    assert spine["source_compatibility"]["named_return_prefers_selected_landmark"] is True
    _assert_locked(spine)


def test_continuity_routes_are_inspectable_and_write_locked():
    conn = sqlite3.connect(":memory:")
    status = route_request(conn, "conversation_continuity.status", {})["result"]
    resolved = route_request(
        conn,
        "conversation_continuity.resolve",
        {"prompt": "A new ordinary question."},
    )["result"]

    assert status["status"] == "conversation_continuity_resolution_ready"
    assert resolved["mode"] == "ordinary_session_continuation"
    _assert_locked(status)
    _assert_locked(resolved)
