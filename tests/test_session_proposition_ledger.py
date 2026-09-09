from __future__ import annotations

from selene.conversation_continuity import resolve_conversation_continuity
from selene.db import connect, init_db
from selene.dialogue_workspace import prepare_dialogue_turn, record_dialogue_response
from selene.chat_intent import classify_chat_intent
from selene.module_router import route_request
from selene.session_proposition_ledger import (
    coordinate_session_revision_completion,
    prepare_session_proposition_revision,
    record_visible_session_propositions,
)
from selene.current_turn_fact_ledger import build_current_turn_fact_ledger


def _prior_ledger() -> dict:
    return {
        "session_id": 1,
        "propositions": [
            {
                "id": "premise-warm",
                "kind": "premise",
                "text": "The evening is warm.",
                "status": "active",
                "depends_on": [],
                "thread_id": "thread-drink",
            },
            {
                "id": "result-tea",
                "kind": "result",
                "text": "Tea fits the warm evening.",
                "status": "active",
                "depends_on": ["premise-warm"],
                "thread_id": "thread-drink",
            },
            {
                "id": "premise-book",
                "kind": "premise",
                "text": "The book is on the desk.",
                "status": "active",
                "depends_on": [],
                "thread_id": "thread-room",
            },
        ],
        "revision_history": [],
    }


def _revision(prior: dict) -> dict:
    return prepare_session_proposition_revision(
        {
            "session_id": 1,
            "prior_ledger": prior,
            "correction_refinement": {
                "detected": True,
                "corrected_meaning": "The evening is cool.",
                "replaced_meaning": "The evening is warm.",
            },
            "epistemic_revision_plan": {
                "detected": True,
                "update_kind": "correction",
                "prior_claim": "The evening is warm.",
                "revised_claim": "The evening is cool.",
                "target": "The evening is warm.",
            },
            "turn_id": "turn-2",
            "thread_id": "thread-drink",
        }
    )


def _assert_bounded(result: dict) -> None:
    assert result["durable_memory_write"] is False
    assert result["runtime_memory_recall"] is False
    assert result["identity_change"] is False
    assert result["personality_change"] is False
    assert result["governance_change"] is False
    assert result["authority_change"] is False
    assert result["training_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def test_revision_invalidates_only_dependents_and_preserves_unrelated_context() -> None:
    revised = _revision(_prior_ledger())
    by_id = {item["id"]: item for item in revised["propositions"]}

    assert by_id["premise-warm"]["status"] == "superseded"
    assert by_id["result-tea"]["status"] == "invalidated"
    assert by_id["premise-book"]["status"] == "active"
    assert revised["recomputation"]["state"] == "required"
    assert revised["recomputation"]["invalidated_result_ids"] == ["result-tea"]
    assert revised["recomputation"]["preserved_proposition_ids"] == ["premise-book"]
    assert revised["ordinary_wrongness_is_failure"] is False
    _assert_bounded(revised)


def test_extracted_replacement_pair_prefers_visible_premise_over_downstream_result() -> None:
    prior = {
        "session_id": 4,
        "propositions": [
            {
                "id": "equal-groups-premise",
                "kind": "premise",
                "text": "The groups improved equally.",
                "status": "active",
                "depends_on": [],
                "thread_id": "thread-seedlings",
            },
            {
                "id": "equal-groups-result",
                "kind": "result",
                "text": "Neither treatment outperformed the other because the groups improved equally.",
                "status": "active",
                "depends_on": ["equal-groups-premise"],
                "thread_id": "thread-seedlings",
            },
        ],
        "revision_history": [],
    }
    revised = prepare_session_proposition_revision(
        {
            "session_id": 4,
            "prior_ledger": prior,
            "correction_refinement": {
                "detected": True,
                "corrected_meaning": "The fertilizer group improved more.",
                "replaced_meaning": "The groups improved equally.",
                "replacement_pair_extracted": True,
            },
            "epistemic_revision_plan": {
                "detected": True,
                "update_kind": "correction",
                "target": "The groups improved equally.",
            },
        }
    )
    by_id = {item["id"]: item for item in revised["propositions"]}

    assert revised["current_revision"]["matched_proposition_ids"] == [
        "equal-groups-premise"
    ]
    assert by_id["equal-groups-premise"]["status"] == "superseded"
    assert by_id["equal-groups-result"]["status"] == "invalidated"
    assert revised["recomputation"]["state"] == "required"
    _assert_bounded(revised)


def test_visible_owner_result_completes_recomputation_once_without_erasing_ancestry() -> None:
    revised = _revision(_prior_ledger())
    completed = record_visible_session_propositions(
        {
            "session_id": 1,
            "ledger": revised,
            "candidate_text": "Because the evening is cool, cocoa fits better than iced tea.",
            "turn_id": "turn-2",
            "thread_id": "thread-drink",
            "coverage_evaluation": {"all_required_addressed": True},
            "answer_operations": {
                "results": [
                    {
                        "operation": "correction",
                        "status": "completed",
                        "source_refs": ["test:corrected-owner-result"],
                    }
                ]
            },
        }
    )

    assert completed["recomputation"]["state"] == "completed"
    recomputed_id = completed["recomputation"]["recomputed_proposition_id"]
    recomputed = next(item for item in completed["propositions"] if item["id"] == recomputed_id)
    assert recomputed["status"] == "recomputed"
    assert recomputed["recomputed_from"] == ["result-tea"]
    assert any(item["id"] == "result-tea" and item["status"] == "invalidated" for item in completed["propositions"])
    assert any(item["id"] == "premise-book" and item["status"] == "active" for item in completed["propositions"])


def test_revision_remains_held_when_no_owner_visibly_recomputes_the_result() -> None:
    revised = _revision(_prior_ledger())
    held = record_visible_session_propositions(
        {
            "session_id": 1,
            "ledger": revised,
            "candidate_text": "I noticed the correction.",
            "coverage_evaluation": {"all_required_addressed": False},
            "answer_operations": {"results": []},
        }
    )

    assert held["recomputation"]["state"] == "held_pending_owner_result"
    assert held["recomputation"]["owner_result_received"] is False
    assert held["recomputation"]["visible_recomputation_received"] is False

    next_turn = prepare_session_proposition_revision(
        {
            "session_id": 1,
            "prior_ledger": held,
            "correction_refinement": {"detected": False},
            "epistemic_revision_plan": {"detected": False},
        }
    )
    assert next_turn["status"] == "session_proposition_revision_held"
    assert next_turn["recomputation"]["state"] == "held_pending_owner_result"
    assert next_turn["recomputation"]["preserved_across_turn"] is True


def test_revision_completion_accepts_only_owner_result_for_active_revision() -> None:
    revised = _revision(_prior_ledger())
    revision_id = revised["recomputation"]["revision_id"]
    completion = coordinate_session_revision_completion(
        {
            "session_id": 1,
            "session_proposition_ledger": revised,
            "owner_candidates": [
                {
                    "source_id": "current_session_facts",
                    "response_seed": "The evening is cool, so cocoa now fits the recommendation.",
                    "supported_operations": ["correction", "choice"],
                    "revision_id": revision_id,
                    "consumed_revision_text": "The evening is cool.",
                    "legacy_fixture_compatibility": False,
                    "typed_owner_result": True,
                    "responsible_owner": True,
                    "current_turn_inputs_accounted_for": True,
                }
            ],
        }
    )

    assert completion["status"] == "session_revision_owner_result_ready"
    assert completion["owner_result_ready"] is True
    assert completion["selected_owner_id"] == "current_session_facts"
    assert completion["revision_id"] == revision_id
    assert completion["maximum_owner_recompute_passes"] == 1
    assert completion["previous_answer_replay_is_recomputation"] is False
    assert completion["candidate_receipts"][0]["revision_input_accounted_for"] is True
    _assert_bounded(completion)


def test_revision_completion_holds_stale_fixture_or_mismatched_owner_result() -> None:
    revised = _revision(_prior_ledger())
    completion = coordinate_session_revision_completion(
        {
            "session_id": 1,
            "session_proposition_ledger": revised,
            "owner_candidates": [
                {
                    "source_id": "old_answer_replay",
                    "response_seed": "Tea fits the warm evening.",
                    "supported_operations": ["correction"],
                    "revision_id": "a-different-revision",
                },
                {
                    "source_id": "legacy_fixture",
                    "response_seed": "A scenario-specific corrected answer.",
                    "supported_operations": ["correction"],
                    "revision_id": revised["recomputation"]["revision_id"],
                    "legacy_fixture_compatibility": True,
                },
                {
                    "source_id": "generic_change_notice",
                    "response_seed": "The latest condition changed.",
                    "supported_operations": ["correction"],
                    "revision_id": revised["recomputation"]["revision_id"],
                    "consumed_revision_text": "the latest condition changed",
                    "legacy_fixture_compatibility": False,
                    "typed_owner_result": True,
                    "responsible_owner": True,
                    "current_turn_inputs_accounted_for": True,
                },
            ],
        }
    )

    assert completion["status"] == "session_revision_owner_result_held"
    assert completion["owner_result_ready"] is False
    assert completion["response_seed"] == ""
    assert not any(item["accepted"] for item in completion["candidate_receipts"])
    generic_receipt = next(
        item
        for item in completion["candidate_receipts"]
        if item["source_id"] == "generic_change_notice"
    )
    assert generic_receipt["matches_active_revision"] is True
    assert generic_receipt["revision_input_accounted_for"] is False
    _assert_bounded(completion)


def test_real_topic_transition_expires_pending_revision_to_inspectable_ancestry() -> None:
    revised = _revision(_prior_ledger())
    held = record_visible_session_propositions(
        {
            "session_id": 1,
            "ledger": revised,
            "candidate_text": "I noticed the correction.",
            "coverage_evaluation": {"all_required_addressed": False},
            "answer_operations": {"results": []},
        }
    )

    next_turn = prepare_session_proposition_revision(
        {
            "session_id": 1,
            "prior_ledger": held,
            "correction_refinement": {"detected": False},
            "epistemic_revision_plan": {"detected": False},
            "topic_transition": True,
        }
    )

    assert next_turn["status"] == "session_proposition_revision_expired_to_ancestry"
    assert next_turn["recomputation"]["state"] == "expired_on_topic_transition"
    assert next_turn["recomputation"]["eligible_current_turn"] is False
    assert next_turn["propositions"]
    _assert_bounded(next_turn)


def test_unknown_correction_target_holds_precisely_without_resetting_context() -> None:
    held = prepare_session_proposition_revision(
        {
            "session_id": 1,
            "prior_ledger": _prior_ledger(),
            "correction_refinement": {
                "detected": True,
                "corrected_meaning": "The unseen count is eleven.",
                "replaced_meaning": "a count that was never stated",
            },
            "epistemic_revision_plan": {
                "detected": True,
                "update_kind": "correction",
                "revised_claim": "The unseen count is eleven.",
                "target": "a count that was never stated",
            },
        }
    )

    assert held["status"] == "session_proposition_revision_held"
    assert held["recomputation"]["state"] == "held_target_not_found"
    assert set(held["active_proposition_ids"]) == {
        "premise-warm",
        "result-tea",
        "premise-book",
    }


def test_dialogue_workspace_persists_session_ledger_without_memory_write(tmp_path) -> None:
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    session_id = int(
        conn.execute(
            "INSERT INTO selene_chat_sessions (title) VALUES (?) RETURNING id",
            ("phase 4",),
        ).fetchone()[0]
    )
    first_text = "The evening is warm. Which drink fits?"
    first_fact_ledger = build_current_turn_fact_ledger(
        {"session_id": session_id, "prompt": first_text}
    )
    first = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": first_text,
            "intent_decision": classify_chat_intent(first_text),
            "conversation_events": [],
        },
    )
    recorded = record_dialogue_response(
        conn,
        {
            "session_id": session_id,
            "candidate_text": "Because the evening is warm, tea fits well.",
            "coverage_evaluation": {
                "all_required_addressed": True,
                "answered_loop_ids": first["new_loop_ids"],
                "items": [],
            },
            "conversation_spine": {
                "turn_id": "turn-one",
                "session_facts": [],
                "current_turn_fact_ledger": first_fact_ledger,
            },
            "claim_evidence_packet": {
                "claims": [
                    {
                        "claim_id": "warm-observation",
                        "claim_type": "observation",
                        "text": "The evening is warm.",
                        "validity": "reported_observation",
                        "basis_claim_ids": [],
                        "source_refs": [],
                    }
                ]
            },
            "answer_operations": {"results": []},
        },
    )
    correction_text = "Actually, I meant the evening is cool, not the evening is warm."
    corrected = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": correction_text,
            "intent_decision": classify_chat_intent(correction_text),
            "conversation_events": [
                {"role": "selene", "preview": "Because the evening is warm, tea fits well."}
            ],
        },
    )

    ledger = corrected["session_proposition_ledger"]
    refinement = corrected["pragmatics"]["correction_refinement"]
    assert refinement["corrected_meaning"] == "the evening is cool"
    assert refinement["replaced_meaning"] == "the evening is warm"
    assert refinement["replacement_pair_extracted"] is True
    assert recorded["session_proposition_ledger"]["active_proposition_ids"]
    assert any(
        item.get("source") == "current_visible_user_turn"
        for item in recorded["session_proposition_ledger"]["propositions"]
    )
    assert ledger["recomputation"]["state"] == "required"
    assert ledger["recomputation"]["invalidated_result_ids"]
    assert ledger["durable_memory_write"] is False
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 0


def test_dialogue_workspace_extracts_changed_clauses_and_quoted_referents(tmp_path) -> None:
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    session_id = int(
        conn.execute(
            "INSERT INTO selene_chat_sessions (title) VALUES (?) RETURNING id",
            ("phase 5 correction grammar",),
        ).fetchone()[0]
    )
    cases = [
        (
            "Small correction: the fertilizer group improved more, not equally. Update the conclusion.",
            "the fertilizer group improved more",
            "equally",
        ),
        (
            "Correction: by 'it stopped' I meant the monitor stopped flashing. Update the observation.",
            "the monitor stopped flashing",
            "it stopped",
        ),
    ]

    for text, corrected_meaning, replaced_meaning in cases:
        prepared = prepare_dialogue_turn(
            conn,
            {
                "session_id": session_id,
                "text": text,
                "intent_decision": classify_chat_intent(text),
                "conversation_events": [
                    {"role": "selene", "preview": "A visible prior answer."}
                ],
            },
        )
        refinement = prepared["pragmatics"]["correction_refinement"]
        assert refinement["detected"] is True
        assert refinement["corrected_meaning"] == corrected_meaning
        assert refinement["replaced_meaning"] == replaced_meaning
        assert refinement["replacement_pair_extracted"] is True
        _assert_bounded(prepared["session_proposition_ledger"])


def test_continuity_excludes_stale_landmark_and_rebinds_revised_reference() -> None:
    revised = _revision(_prior_ledger())
    stale_result = next(item for item in revised["propositions"] if item["id"] == "result-tea")
    stale_result["replaced_by_proposition_id"] = revised["recomputation"]["revised_proposition_id"]
    result = resolve_conversation_continuity(
        {
            "prompt": "Return to that warm-evening point.",
            "contextual_follow_up": {"kind": "named_callback"},
            "dialogue_workspace": {
                "pragmatics": {
                    "session_proposition_ledger": revised,
                    "resolved_reference": {
                        "token": "that warm-evening point",
                        "resolved_to": "Tea fits the warm evening.",
                        "resolution_status": "resolved",
                    },
                    "session_landmarks": [
                        {
                            "id": "old-warm-answer",
                            "summary": "Tea fits the warm evening.",
                            "proposition_id": "result-tea",
                            "thread_id": "thread-drink",
                        },
                        {
                            "id": "unrelated-book",
                            "summary": "The book is on the desk.",
                            "proposition_id": "premise-book",
                            "thread_id": "thread-room",
                        },
                    ],
                    "thread_braid": {"threads": [], "turn_traversal": []},
                }
            },
        }
    )

    assert "old-warm-answer" in result["stale_landmark_ids_excluded"]
    assert result["resolved_reference"]["resolution_status"] == "resolved_to_revised_proposition"
    assert result["resolved_reference"]["resolved_to"] == "The evening is cool."
    assert "Tea fits the warm evening" not in result["grounding_text"]


def test_router_exposes_bounded_session_proposition_contract(tmp_path) -> None:
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    status = route_request(conn, "session_propositions.status")["result"]

    assert status["status"] == "session_proposition_ledger_ready"
    assert status["generates_answers"] is False
    assert status["automatic_retention"] is False
    _assert_bounded(status)


def test_visible_turn_facts_enter_session_ledger_and_state_updates_supersede_selectively() -> None:
    first_facts = build_current_turn_fact_ledger(
        {
            "session_id": 22,
            "prompt": "I moved the green cup to the shelf. A silver cup is new.",
        }
    )
    first = record_visible_session_propositions(
        {
            "session_id": 22,
            "ledger": {},
            "turn_id": "turn-green-one",
            "thread_id": "thread-cups",
            "current_turn_fact_ledger": first_facts,
            "answer_operations": {"results": []},
        }
    )
    second_facts = build_current_turn_fact_ledger(
        {
            "session_id": 22,
            "prompt": "I moved the green cup to the cabinet.",
        }
    )
    second = record_visible_session_propositions(
        {
            "session_id": 22,
            "ledger": first,
            "turn_id": "turn-green-two",
            "thread_id": "thread-cups",
            "current_turn_fact_ledger": second_facts,
            "answer_operations": {"results": []},
        }
    )

    locations = [
        item
        for item in second["propositions"]
        if item.get("relation_type") == "location"
    ]
    assert [item["object"] for item in locations if item["status"] == "active"] == [
        "cabinet"
    ]
    assert [item["object"] for item in locations if item["status"] == "superseded"] == [
        "shelf"
    ]
    assert any(
        item.get("subject") == "silver cup" and item["status"] == "active"
        for item in second["propositions"]
    )
    assert all(
        item.get("scope") == "current_session_only"
        for item in second["propositions"]
    )
    _assert_bounded(second)
