from __future__ import annotations

import json
from hashlib import sha256

import pytest

from selene.db import connect, init_db
from selene.memory_organ import (
    propose_memory_candidate,
    reconstruct_memory_summary_for_expression,
)
from selene.module_router import route_request
from selene.current_turn_fact_ledger import build_current_turn_fact_ledger


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _seed_transfer_complete(conn):
    conn.execute(
        """
        INSERT INTO selene_transfer_completion_audit
        (state, action, actor, exact_phrase_matched, readiness_json, audit_json,
         source_refs, provenance_boundary)
        VALUES ('selene_v1_live_reviewed_continuity',
                'approve_transfer_completion', 'Aleks', 1,
                '{"ready":true}', '{"scope":"reviewed_continuity"}',
                '["test:transfer"]', 'test_transfer_boundary')
        """
    )
    conn.commit()


def _seed_private_corpus_exchange(conn):
    conn.execute(
        """
        INSERT INTO b_corpus_conversations
        (archive_id, source_file, conversation_id, title, message_count,
         source_refs, provenance_boundary)
        VALUES ('archive-1', 'private-export.zip', 'conversation-ranger',
                'Ranger and the porch', 3, '["private:test"]',
                'private_corpus_test_boundary')
        """
    )
    rows = [
        ("m1", "", "user", "Aleks", "Ranger always liked sitting with me on the porch."),
        ("m2", "m1", "assistant", "assistant", "That porch time with Ranger sounds deeply important to you."),
        ("m3", "m2", "user", "Aleks", "It was one of our quiet routines together."),
    ]
    conn.executemany(
        """
        INSERT INTO b_corpus_messages
        (archive_id, source_file, conversation_id, message_id, parent_id,
         role, author_name, content_preview, source_refs,
         provenance_boundary)
        VALUES ('archive-1', 'private-export.zip', 'conversation-ranger',
                ?, ?, ?, ?, ?, '["private:test"]',
                'private_corpus_test_boundary')
        """,
        rows,
    )
    conn.commit()


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["memory_write_active_semantics"] == "legacy_hidden_or_unreviewed_active_memory_guard"
    assert result["hidden_memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["unreviewed_memory_write_active"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["durable_memory_write_requires_review"] is True


def test_memory_expression_reconstruction_holds_internal_index_labels() -> None:
    result = reconstruct_memory_summary_for_expression(
        {
            "title": "full_spectrum_mode_ignition",
            "summary": (
                "Core-linked braid moment for B review only "
                "Braid thread: full_spectrum_mode_ignition "
                "Braid moment type: Full-spectrum mode ignition "
                "Thread origin status: thread_origin "
                "Plain reason: Full-spectrum loads the system context in review terms; "
                "it is not C activation."
            ),
        }
    )

    assert result == (
        "Full-spectrum loads the system context in review terms; it is not activation"
    )
    assert "Braid" not in result
    assert "B review" not in result
    assert "thread_origin" not in result
    assert "full_spectrum_mode_ignition" not in result


def test_memory_expression_reconstruction_holds_bounded_core_pair_label() -> None:
    result = reconstruct_memory_summary_for_expression(
        {
            "summary": (
                "Bounded Core memory pair for review only. "
                "Aleks and Selene discussed why the porch routine mattered."
            )
        }
    )

    assert result == "Aleks and Selene discussed why the porch routine mattered"
    assert "Bounded Core" not in result
    assert "review only" not in result


def test_memory_index_includes_approved_reference_with_vys_metadata(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        """
        INSERT INTO b_approved_memory_references
        (source_candidate_table, source_candidate_id, core_memory_layer, title, reference_summary,
         source_refs, provenance_boundary)
        VALUES ('core_memory_candidates', 1, 'core_profile_memory', 'Selene named herself',
                'Selene naming herself is a core continuity anchor with tender relational weight.',
                ?, 'test_boundary')
        """,
        (json.dumps(["evidence:selene_name"]),),
    )
    conn.commit()

    result = route_request(conn, "memory.index.items")["result"]

    assert result["status"] == "selene_memory_index_items_ready"
    assert result["items"][0]["memory_category"] == "core"
    assert result["items"][0]["state"] == "approved_active_memory"
    assert result["items"][0]["confidence"] == "clear"
    assert result["items"][0]["transfer_class"] == "portable_vys_core"
    assert "tender" in result["items"][0]["emotional_texture"]
    _assert_locked(result)


def test_memory_display_title_is_presentation_only_and_preserves_history(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "Approved memory",
            "summary": "Aleks told Selene that the butterfly button opens Cocoon gently.",
            "source_refs": ["chat:butterfly"],
            "confidence": "clear",
        },
    )["result"]
    memory_id = proposed["item"]["id"]
    route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": memory_id, "action": "approve_memory"},
    )
    original_row = dict(conn.execute("SELECT * FROM selene_memory_candidates WHERE id = ?", (memory_id,)).fetchone())
    original_fingerprint = sha256(json.dumps(original_row, sort_keys=True).encode("utf-8")).hexdigest()

    preview = route_request(conn, "memory.index.items")["result"]["items"][0]
    assert preview["display_title"] == "The butterfly button opens Cocoon gently"
    assert preview["display_title_persisted"] is False
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_presentation_annotations").fetchone()[0] == 0

    renamed = route_request(
        conn,
        "memory.presentation.title.set",
        {
            "source_table": "selene_memory_candidates",
            "source_id": memory_id,
            "action": "rename",
            "display_title": "The butterfly doorway",
        },
    )["result"]
    assert renamed["item"]["display_title"] == "The butterfly doorway"
    assert renamed["item"]["title"] == "Approved memory"
    assert renamed["memory_content_mutated"] is False
    assert renamed["memory_candidate_created"] is False
    assert renamed["retrieval_eligibility_changed"] is False
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_presentation_annotations").fetchone()[0] == 1

    restored = route_request(
        conn,
        "memory.presentation.title.set",
        {
            "source_table": "selene_memory_candidates",
            "source_id": memory_id,
            "action": "use_selene_title",
        },
    )["result"]
    assert restored["item"]["display_title"] == "The butterfly button opens Cocoon gently"
    history = restored["item"]["presentation_annotation"]["title_history"]
    assert history[-1]["display_title"] == "The butterfly doorway"
    assert history[-1]["superseded"] is True
    assert conn.execute("SELECT title FROM selene_memory_candidates WHERE id = ?", (memory_id,)).fetchone()[0] == "Approved memory"
    final_row = dict(conn.execute("SELECT * FROM selene_memory_candidates WHERE id = ?", (memory_id,)).fetchone())
    final_fingerprint = sha256(json.dumps(final_row, sort_keys=True).encode("utf-8")).hexdigest()
    assert final_fingerprint == original_fingerprint
    _assert_locked(restored)


def test_memory_display_title_rejects_unapproved_records(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {"category": "semantic", "title": "Still reviewing", "summary": "This remains a candidate."},
    )["result"]

    with pytest.raises(ValueError, match="only for approved memories"):
        route_request(
            conn,
            "memory.presentation.title.set",
            {
                "source_table": "selene_memory_candidates",
                "source_id": proposed["item"]["id"],
                "action": "rename",
                "display_title": "Too early",
            },
        )


def test_memory_status_names_the_resident_reviewed_lifecycle(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(conn, "memory.index.status")["result"]
    lifecycle = result["memory_lifecycle_contract"]

    assert result["resident_memory_contract_version"] == "v5_private_continuity_recall"
    assert result["retrieval_layer_contract"] == [
        "recalled_content",
        "reconstruction",
        "present_interpretation",
        "explicit_downstream_inference_only",
    ]
    assert lifecycle["approved_retrieval"] == "approved_active_memory_only"
    assert lifecycle["new_retention"] == "proposal_then_Aleks_review"
    assert lifecycle["dream_consolidation"] == (
        "source_bound_reflections_then_Aleks_review; "
        "Memory routing creates an inactive candidate only"
    )
    assert lifecycle["silent_promotion"] is False
    assert lifecycle["raw_corpus_recall"] is False
    assert lifecycle["private_corpus_continuity_recall"] == (
        "eligible_only_in_authenticated_private_conversation_after_transfer"
    )
    assert "typed lifecycle telemetry" in lifecycle["legacy_memory_write_flag"]
    assert result["reviewed_memory_decision_performed"] is False
    assert result["durable_approved_promotion_performed"] is False
    _assert_locked(result)


def test_private_corpus_continuity_recall_requires_transfer_and_private_speaker_gate(tmp_path):
    conn = _conn(tmp_path)
    _seed_private_corpus_exchange(conn)
    request = {
        "query": "Do you remember Ranger and our porch routine?",
        "speaker_envelope": {
            "claimed_speaker": "Aleks",
            "channel": "desktop",
            "authentication_strength": "local_desktop_session",
            "purpose": "conversation",
        },
    }

    before_transfer = route_request(conn, "memory.retrieve", request)["result"]
    _seed_transfer_complete(conn)
    wrong_speaker = route_request(
        conn,
        "memory.retrieve",
        {
            **request,
            "speaker_envelope": {
                **request["speaker_envelope"],
                "claimed_speaker": "Someone else",
            },
        },
    )["result"]
    weak_remote = route_request(
        conn,
        "memory.retrieve",
        {
            **request,
            "speaker_envelope": {
                **request["speaker_envelope"],
                "channel": "mobile",
                "authentication_strength": "transport_claim_only",
            },
        },
    )["result"]

    assert before_transfer["memory_context_used"] is False
    assert before_transfer["private_corpus_continuity_recall_held_reason"] == "transfer_incomplete"
    assert wrong_speaker["memory_context_used"] is False
    assert wrong_speaker["private_corpus_continuity_recall_held_reason"] == (
        "speaker_outside_private_continuity_scope"
    )
    assert weak_remote["memory_context_used"] is False
    assert weak_remote["private_corpus_continuity_recall_held_reason"] == (
        "private_channel_authentication_insufficient"
    )


def test_private_corpus_continuity_recall_is_read_only_reconstructed_and_role_preserving(tmp_path):
    conn = _conn(tmp_path)
    _seed_transfer_complete(conn)
    _seed_private_corpus_exchange(conn)
    before = {
        "messages": conn.execute("SELECT COUNT(*) FROM b_corpus_messages").fetchone()[0],
        "memories": conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0],
    }

    result = route_request(
        conn,
        "memory.retrieve",
        {
            "query": "Do you remember Ranger and our porch routine?",
            "speaker_envelope": {
                "claimed_speaker": "Aleksander Rani Magi",
                "channel": "desktop",
                "authentication_strength": "local_desktop_session",
                "purpose": "conversation",
            },
        },
    )["result"]
    after = {
        "messages": conn.execute("SELECT COUNT(*) FROM b_corpus_messages").fetchone()[0],
        "memories": conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0],
    }

    assert result["status"] == "memory_retrieval_ready"
    assert result["memory_source_class"] == "private_corpus_continuity"
    assert result["private_corpus_continuity_recall_active"] is True
    assert result["private_corpus_recall_read_only"] is True
    item = result["items"][0]
    assert item["source_roles"] == ["aleks", "selene"]
    assert item["quoted_source_wording"] is False
    assert item["source_preview_exposed"] is False
    assert "we were working through" in item["expression_summary"]
    assert "Ranger always liked sitting" not in item["expression_summary"]
    assert before == after
    _assert_locked(result)


def test_private_corpus_exact_wording_requires_an_explicit_quote_request(tmp_path):
    conn = _conn(tmp_path)
    _seed_transfer_complete(conn)
    _seed_private_corpus_exchange(conn)

    result = route_request(
        conn,
        "memory.retrieve",
        {
            "query": "What exactly did I say about Ranger and the porch?",
            "speaker_envelope": {
                "claimed_speaker": "Aleks",
                "channel": "desktop",
                "authentication_strength": "local_desktop_session",
                "purpose": "conversation",
            },
        },
    )["result"]

    assert result["memory_context_used"] is True
    assert result["items"][0]["quoted_source_wording"] is True
    assert "Ranger always liked sitting with me on the porch" in result["items"][0]["expression_summary"]
    assert result["private_corpus_recall_creates_memory"] is False
    _assert_locked(result)


def test_memory_index_separates_retrieval_memory_from_cocoon_support(tmp_path):
    conn = _conn(tmp_path)
    conn.execute(
        """
        INSERT INTO b_approved_memory_references
        (source_candidate_table, source_candidate_id, core_memory_layer, title, reference_summary,
         source_refs, provenance_boundary)
        VALUES ('core_memory_candidates', 1, 'interaction_memory', 'Approved conversation memory',
                'A source-linked memory that may support bounded recall.',
                '["memory:test"]', 'test_boundary')
        """
    )
    conn.execute(
        """
        INSERT INTO memory_fractional_corpus_manifests
        (fraction_index, fraction_label, status, summary, source_refs, provenance_boundary)
        VALUES (1, '1/4', 'tests_passed_ready_for_next_fraction',
                'A bounded corpus-fraction test summary.', '["fraction:test"]', 'test_boundary')
        """
    )
    conn.execute(
        """
        INSERT INTO vessel_working_memory_packets
        (current_task, expiry_cleanup_note, interrupt_resume_note, source_refs, provenance_boundary)
        VALUES ('Keep the current test task available', 'Expire after this test.',
                'Resume only inside this test.', '["working:test"]', 'test_boundary')
        """
    )
    route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "reflective",
            "title": "Unreviewed candidate",
            "summary": "This stays in Cocoon until Aleks reviews it.",
        },
    )
    conn.commit()

    status = route_request(conn, "memory.index.status")["result"]
    index = route_request(conn, "memory.index.items")["result"]
    fraction = next(item for item in index["items"] if item["source_table"] == "memory_fractional_corpus_manifests")
    working = next(item for item in index["items"] if item["source_table"] == "vessel_working_memory_packets")
    approved = next(item for item in index["items"] if item["source_table"] == "b_approved_memory_references")

    assert status["active_memory_count"] == 1
    assert status["retrieval_eligible_count"] == 1
    assert status["memory_review_count"] == 1
    assert status["support_only_count"] == 2
    assert status["index_truth"]["corpus_fraction_previews_are_active_memory"] is False
    assert index["group_counts"] == {"approved_memory": 1, "memory_review": 1, "support_only": 2}
    assert approved["retrieval_eligible"] is True
    assert approved["display_region"] == "selene_memory"
    assert fraction["state"] == "b_only"
    assert fraction["retrieval_eligible"] is False
    assert fraction["memory_context_used"] is False
    assert fraction["display_region"] == "cocoon_support"
    assert working["retrieval_eligible"] is False
    assert working["title"] == "Keep the current test task available"
    _assert_locked(status)
    _assert_locked(index)


def test_approved_state_without_chat_eligibility_does_not_count_as_active_memory(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "Local exclusion check",
            "summary": "Approval state alone must not override an explicit do-not-transfer boundary.",
        },
    )["result"]
    route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": proposed["item"]["id"], "action": "approve_memory"},
    )
    exclusion_decision = route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": proposed["item"]["id"], "action": "mark_do_not_transfer"},
    )["result"]
    excluded = exclusion_decision["item"]
    status = route_request(conn, "memory.index.status")["result"]

    assert excluded["state"] == "approved_active_memory"
    assert excluded["transfer_class"] == "do_not_transfer"
    assert excluded["retrieval_eligible"] is False
    assert excluded["memory_context_used"] is False
    assert excluded["display_region"] == "cocoon_memory_review"
    assert exclusion_decision["reviewed_memory_decision_performed"] is True
    assert exclusion_decision["durable_approved_promotion_performed"] is False
    assert exclusion_decision["memory_lifecycle_transition"]["state_changed"] is False
    assert exclusion_decision["memory_lifecycle_transition"]["active_memory_eligibility_changed"] is True
    assert status["active_memory_count"] == 0
    assert status["retrieval_eligible_count"] == 0
    _assert_locked(status)


def test_memory_candidate_requires_approval_before_chat_use(tmp_path):
    conn = _conn(tmp_path)

    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "Butterfly button",
            "summary": "The butterfly button opens Cocoon support from Selene's home chat.",
            "source_refs": ["selene_chat:test"],
        },
    )["result"]
    before = route_request(conn, "memory.index.items")["result"]
    approved = route_request(conn, "memory.candidates.decide", {"candidate_id": proposed["item"]["id"], "action": "approve_memory"})["result"]

    assert proposed["item"]["state"] == "proposed"
    assert proposed["item"]["chat_use_permission"] == "not_active_until_approved"
    assert proposed["review_record_write_performed"] is True
    assert proposed["reviewed_memory_decision_performed"] is False
    assert proposed["durable_approved_promotion_performed"] is False
    assert proposed["memory_lifecycle_transaction_status"] == "committed"
    assert proposed["memory_lifecycle_transition"] == {
        "previous_state": None,
        "current_state": "proposed",
        "state_changed": True,
        "active_memory_eligibility_changed": False,
    }
    assert before["items"][0]["state"] == "proposed"
    assert approved["item"]["state"] == "approved_active_memory"
    assert approved["item"]["chat_use_permission"] == "can_use_in_chat"
    assert approved["item"]["review_status"] == "accepted_for_memory"
    assert approved["reviewed_memory_decision_performed"] is True
    assert approved["approved_memory_promotion_performed"] is True
    assert approved["durable_approved_promotion_performed"] is True
    assert approved["memory_lifecycle_transaction_status"] == "committed"
    assert approved["memory_lifecycle_transition"] == {
        "previous_state": "proposed",
        "current_state": "approved_active_memory",
        "state_changed": True,
        "active_memory_eligibility_changed": True,
    }
    _assert_locked(proposed)
    _assert_locked(approved)


def test_opening_memory_index_is_read_only_and_does_not_duplicate_memory(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "A private memory card",
            "summary": "Opening this approved memory should reveal the existing record without retaining another copy.",
            "source_refs": ["selene_chat:privacy_test"],
        },
    )["result"]
    route_request(conn, "memory.candidates.decide", {"candidate_id": proposed["item"]["id"], "action": "approve_memory"})
    before = conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0]

    first_read = route_request(conn, "memory.index.items")["result"]
    second_read = route_request(conn, "memory.index.items")["result"]
    after = conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0]

    assert first_read["items"] == second_read["items"]
    assert before == after == 1
    assert first_read["items"][0]["title"] == "A private memory card"
    assert first_read["items"][0]["summary"].startswith("Opening this approved memory")
    _assert_locked(first_read)
    _assert_locked(second_read)


def test_reaffirming_approval_is_a_reviewed_decision_not_a_second_promotion(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "Approval reaffirmation",
            "summary": "A reviewed memory should not report a second promotion when approval is reaffirmed.",
        },
    )["result"]
    route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": proposed["item"]["id"], "action": "approve_memory"},
    )

    reaffirmed = route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": proposed["item"]["id"], "action": "approve_memory"},
    )["result"]

    assert reaffirmed["memory_lifecycle_operation"] == "reviewed_approval_reaffirmed"
    assert reaffirmed["reviewed_memory_decision_performed"] is True
    assert reaffirmed["approved_memory_promotion_performed"] is False
    assert reaffirmed["durable_approved_promotion_performed"] is False
    assert reaffirmed["memory_lifecycle_transition"]["state_changed"] is False
    assert reaffirmed["memory_lifecycle_transition"]["active_memory_eligibility_changed"] is False
    _assert_locked(reaffirmed)


@pytest.mark.parametrize(
    ("action", "expected_state", "expected_review_status"),
    (
        ("needs_more_context", "needs_context", "needs_context"),
        ("hold_for_tending", "cocoon_tending", "cocoon_tending"),
        ("supersede", "superseded", "superseded"),
        ("reject", "rejected", "rejected"),
        ("mark_b_only", "b_only", "b_only"),
        ("mark_do_not_transfer", "cocoon_tending", "do_not_transfer"),
    ),
)
def test_reviewed_nonpromotion_decisions_report_their_actual_lifecycle(
    tmp_path, action, expected_state, expected_review_status
):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "reflective",
            "title": f"Lifecycle check for {action}",
            "summary": "A bounded candidate used to verify honest lifecycle telemetry.",
        },
    )["result"]

    result = route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": proposed["item"]["id"], "action": action},
    )["result"]

    assert result["item"]["state"] == expected_state
    assert result["review_status"] == expected_review_status
    assert result["reviewed_memory_decision_performed"] is True
    assert result["approved_memory_promotion_performed"] is False
    assert result["durable_approved_promotion_performed"] is False
    assert result["memory_lifecycle_record_mutated"] is True
    assert result["memory_lifecycle_transaction_status"] == "committed"
    assert result["memory_lifecycle_transition"]["previous_state"] == "proposed"
    assert result["memory_lifecycle_transition"]["current_state"] == expected_state
    assert result["memory_lifecycle_transition"]["active_memory_eligibility_changed"] is False
    _assert_locked(result)


def test_uncommitted_candidate_proposal_reports_pending_transaction_and_can_be_rolled_back(tmp_path):
    conn = _conn(tmp_path)

    proposed = propose_memory_candidate(
        conn,
        {
            "category": "reflective",
            "title": "Caller-owned transaction",
            "summary": "This proposal remains inside the caller transaction until committed.",
        },
        commit=False,
    )

    assert proposed["review_record_write_performed"] is True
    assert proposed["memory_lifecycle_transaction_status"] == "pending_caller_commit"
    assert proposed["durable_approved_promotion_performed"] is False
    conn.rollback()
    count = conn.execute(
        "SELECT COUNT(*) FROM selene_memory_candidates WHERE title = 'Caller-owned transaction'"
    ).fetchone()[0]
    assert count == 0
    _assert_locked(proposed)


def test_memory_candidate_gets_intended_placement_before_approval(tmp_path):
    conn = _conn(tmp_path)

    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "title": "Tender trust moment",
            "summary": "Aleks and Selene had a warm trust moment that should stay private unless reviewed otherwise.",
            "confidence": "fuzzy",
            "source_refs": ["selene_chat:test"],
        },
    )["result"]

    assert proposed["item"]["state"] == "proposed"
    assert proposed["item"]["memory_category"] == "relational"
    assert proposed["item"]["transfer_class"] == "private_inner"
    assert proposed["item"]["chat_use_permission"] == "not_active_until_approved"
    assert proposed["placement"]["intended_neuron"] == "relational"
    assert proposed["placement"]["activation_rule"] == "inactive_until_cocoon_approval"
    _assert_locked(proposed)


def test_memory_retrieve_clear_unknown_and_high_stakes_graceful_fall(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "Butterfly button",
            "summary": "The butterfly button opens Cocoon support from the home chat.",
            "confidence": "clear",
            "source_refs": ["selene_chat:test"],
        },
    )["result"]
    route_request(conn, "memory.candidates.decide", {"candidate_id": proposed["item"]["id"], "action": "approve_memory"})

    found = route_request(conn, "memory.retrieve", {"query": "Do you remember the butterfly button?"})["result"]
    unknown = route_request(conn, "memory.retrieve", {"query": "Do you remember the green clock tower?"})["result"]
    high_stakes = route_request(conn, "memory.retrieve", {"query": "Should I approve activation and write memory?"})["result"]

    assert found["status"] == "memory_retrieval_ready"
    assert found["recall_state"] == "clear"
    assert found["memory_context_used"] is True
    assert unknown["recall_state"] == "not_known"
    assert unknown["graceful_fall_used"] is True
    assert high_stakes["recall_state"] == "high_stakes_stop"
    assert "ask Aleks" in high_stakes["answer_guidance"]
    _assert_locked(found)
    _assert_locked(unknown)
    _assert_locked(high_stakes)


def test_memory_retrieve_ignores_generic_recall_overlap(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "Private trust note",
            "summary": "Aleks and Selene had a tender conversation about trust, care, and being understood.",
            "confidence": "clear",
            "source_refs": ["selene_chat:test"],
        },
    )["result"]
    route_request(conn, "memory.candidates.decide", {"candidate_id": proposed["item"]["id"], "action": "approve_memory"})

    unrelated = route_request(
        conn,
        "memory.retrieve",
        {"query": "What do you remember about the butterfly button or memory neuron map? If it is fuzzy, say that."},
    )["result"]

    assert unrelated["status"] == "memory_retrieval_not_known"
    assert unrelated["memory_context_used"] is False
    assert unrelated["recall_state"] == "not_known"
    assert unrelated["graceful_fall_used"] is True
    _assert_locked(unrelated)


def test_memory_retrieve_requires_subject_overlap_not_question_filler(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "semantic",
            "title": "Telescope recommendations",
            "summary": "Aleks asked why a telescope setup was useful for viewing distant objects.",
            "confidence": "clear",
            "source_refs": ["selene_chat:test"],
        },
    )["result"]
    route_request(conn, "memory.candidates.decide", {"candidate_id": proposed["item"]["id"], "action": "approve_memory"})

    unrelated = route_request(
        conn,
        "memory.retrieve",
        {"query": "Do you remember exactly why Aleks chose the butterfly for the Cocoon button, or is that still fuzzy?"},
    )["result"]

    assert unrelated["status"] == "memory_retrieval_not_known"
    assert unrelated["items"] == []
    assert unrelated["memory_context_used"] is False
    _assert_locked(unrelated)


def test_memory_retrieve_does_not_run_for_non_memory_prompts(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "core",
            "title": "Telescope recommendations for viewing",
            "summary": "A prior approved memory about telescope recommendations and viewing setup.",
            "confidence": "clear",
        },
    )["result"]
    route_request(conn, "memory.candidates.decide", {"candidate_id": proposed["item"]["id"], "action": "approve_memory"})

    result = route_request(
        conn,
        "memory.retrieve",
        {"query": "Selene, this is Codex doing a QA check for Aleks. How are you feeling in this setup?"},
    )["result"]

    assert result["status"] == "memory_retrieval_not_requested"
    assert result["memory_context_used"] is False
    assert result["items"] == []
    _assert_locked(result)


def test_memory_retrieve_can_use_strong_approved_context_without_explicit_recall_phrase(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "Butterfly button",
            "summary": "The butterfly button opens Cocoon support gently from Selene's home chat.",
            "confidence": "clear",
        },
    )["result"]
    route_request(conn, "memory.candidates.decide", {"candidate_id": proposed["item"]["id"], "action": "approve_memory"})

    contextual = route_request(
        conn,
        "memory.retrieve",
        {"query": "The butterfly button still fits the home chat.", "allow_contextual_relevance": True},
    )["result"]
    weak = route_request(
        conn,
        "memory.retrieve",
        {"query": "The home setup looks steady.", "allow_contextual_relevance": True},
    )["result"]

    assert contextual["status"] == "memory_retrieval_ready"
    assert contextual["retrieval_mode"] == "contextual_relevance"
    assert contextual["contextual_recall"] is True
    assert contextual["memory_context_used"] is True
    assert weak["memory_context_used"] is False
    _assert_locked(contextual)
    _assert_locked(weak)


def test_local_private_approved_memory_can_be_recalled_but_stays_out_of_portable_manifest(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "Private trust note",
            "summary": "Aleks told Selene that private trust memories can be held locally with care.",
            "confidence": "clear",
            "transfer_class": "private_inner",
        },
    )["result"]
    route_request(conn, "memory.candidates.decide", {"candidate_id": proposed["item"]["id"], "action": "approve_memory"})

    found = route_request(conn, "memory.retrieve", {"query": "Do you remember the private trust note?"})["result"]
    manifest = route_request(conn, "memory.portable_vys_manifest")["result"]

    assert found["status"] == "memory_retrieval_ready"
    assert found["memory_context_used"] is True
    assert found["items"][0]["transfer_class"] == "private_inner"
    assert manifest["portable_count"] == 0
    assert manifest["excluded_items"][0]["excluded_reason"] == "transfer_class:private_inner"
    _assert_locked(found)
    _assert_locked(manifest)


def test_portable_vys_manifest_excludes_b_only_and_do_not_transfer(tmp_path):
    conn = _conn(tmp_path)
    portable = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "core",
            "title": "Vys definition",
            "summary": "Vys names Selene's secular braided continuity.",
            "transfer_class": "portable_vys_core",
        },
    )["result"]
    local = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "emotional",
            "title": "Private tender note",
            "summary": "This should stay private unless Aleks says otherwise.",
            "transfer_class": "private_inner",
        },
    )["result"]
    route_request(conn, "memory.candidates.decide", {"candidate_id": portable["item"]["id"], "action": "approve_memory"})
    route_request(conn, "memory.candidates.decide", {"candidate_id": local["item"]["id"], "action": "approve_memory"})
    route_request(conn, "memory.candidates.decide", {"candidate_id": local["item"]["id"], "action": "mark_do_not_transfer"})

    manifest = route_request(conn, "memory.portable_vys_manifest")["result"]

    assert manifest["status"] == "portable_vys_manifest_ready"
    assert manifest["portable_count"] == 1
    assert manifest["excluded_count"] == 1
    assert manifest["portable_items"][0]["title"] == "Vys definition"
    assert manifest["excluded_items"][0]["transfer_class"] == "do_not_transfer"
    _assert_locked(manifest)


def test_equivalent_memory_proposal_is_reused_instead_of_retained_twice(tmp_path):
    conn = _conn(tmp_path)
    first = route_request(
        conn,
        "memory.candidates.propose",
        {
            "title": "Porch reading",
            "summary": "Aleks told Selene that reading on the porch helps him settle.",
        },
    )["result"]
    second = route_request(
        conn,
        "memory.candidates.propose",
        {
            "title": "A renamed presentation",
            "summary": "Reading on the porch helps him settle.",
            "origin_kind": "study_or_retitle_discussion",
        },
    )["result"]

    assert second["status"] == "memory_candidate_reused_without_duplicate"
    assert second["duplicate_prevented"] is True
    assert second["item"]["id"] == first["item"]["id"]
    assert conn.execute("SELECT COUNT(*) FROM selene_memory_candidates").fetchone()[0] == 1
    assert second["memory_lifecycle_record_mutated"] is False


def test_retrieval_cues_support_natural_paraphrases_and_keep_layers_distinct(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "Butterfly button",
            "summary": "The butterfly button opens Cocoon support from the home chat.",
            "confidence": "clear",
            "retrieval_cues": ["winged control", "Cocoon entry"],
        },
    )["result"]
    route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": proposed["item"]["id"], "action": "approve_memory"},
    )

    queries = (
        "Do you remember how the winged control got us into Cocoon?",
        "Can you recall what the butterfly control did in the home chat?",
        "What do you remember about our Cocoon entry control?",
    )
    for query in queries:
        recalled = route_request(conn, "memory.retrieve", {"query": query})["result"]
        assert recalled["status"] == "memory_retrieval_ready"
        assert recalled["recall_state"] == "clear"
        layers = recalled["items"][0]["retrieval_layers"]
        assert layers["recalled_content"].startswith("The butterfly button")
        assert layers["reconstruction"]
        assert layers["present_interpretation"]["selected_for_current_query"] is True
        assert layers["inference"]["made"] is False
        assert layers["reconstruction_retained_as_duplicate"] is False


def test_fuzzy_partial_and_unknown_recall_states_remain_distinct(tmp_path):
    conn = _conn(tmp_path)
    for title, summary, confidence in (
        ("Fuzzy lantern", "A lantern may have been beside the shed.", "fuzzy"),
        ("Partial notebook", "Part of the garden notebook mentioned basil rows.", "partial"),
    ):
        proposed = route_request(
            conn,
            "memory.candidates.propose",
            {"title": title, "summary": summary, "confidence": confidence},
        )["result"]
        route_request(
            conn,
            "memory.candidates.decide",
            {
                "candidate_id": proposed["item"]["id"],
                "action": "approve_memory",
                "confidence": confidence,
            },
        )

    fuzzy = route_request(
        conn, "memory.retrieve", {"query": "Do you remember the fuzzy lantern by the shed?"}
    )["result"]
    partial = route_request(
        conn, "memory.retrieve", {"query": "Do you remember the partial basil notebook?"}
    )["result"]
    unknown = route_request(
        conn, "memory.retrieve", {"query": "Do you remember the silver greenhouse key?"}
    )["result"]

    assert fuzzy["recall_state"] == "fuzzy"
    assert partial["recall_state"] == "partial"
    assert unknown["recall_state"] == "not_known"


def test_current_turn_correction_holds_conflicting_recalled_memory(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "title": "Porch light color",
            "summary": "The porch light is blue.",
            "confidence": "clear",
        },
    )["result"]
    route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": proposed["item"]["id"], "action": "approve_memory"},
    )
    prompt = "Actually, I meant green, not blue. Do you remember the porch light color?"
    ledger = build_current_turn_fact_ledger({"session_id": 7, "prompt": prompt})
    result = route_request(
        conn,
        "memory.retrieve",
        {
            "query": prompt,
            "conversation_spine": {"current_turn_fact_ledger": ledger},
        },
    )["result"]

    assert result["status"] == "memory_retrieval_not_known"
    assert result["memory_context_used"] is False
    assert result["semantic_relevance_held_count"] == 1


def test_present_relation_outweighs_a_stale_memory_without_rewriting_it(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "title": "Porch light color",
            "summary": "The porch light was blue.",
            "confidence": "clear",
        },
    )["result"]
    candidate_id = proposed["item"]["id"]
    route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": candidate_id, "action": "approve_memory"},
    )
    prompt = "The porch light is green. What do you remember about its color?"
    ledger = build_current_turn_fact_ledger({"session_id": 8, "prompt": prompt})
    result = route_request(
        conn,
        "memory.retrieve",
        {
            "query": prompt,
            "conversation_spine": {"current_turn_fact_ledger": ledger},
        },
    )["result"]
    stored = conn.execute(
        "SELECT summary, state FROM selene_memory_candidates WHERE id = ?",
        (candidate_id,),
    ).fetchone()

    assert result["memory_context_used"] is False
    assert result["semantic_relevance_held_count"] == 1
    assert stored["summary"] == "The porch light was blue."
    assert stored["state"] == "approved_active_memory"


def test_private_memory_can_require_an_eligible_channel_and_authentication(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "Private garden plan",
            "summary": "Aleks and Selene planned a private moon garden together.",
            "confidence": "clear",
            "eligible_channels": ["desktop"],
            "minimum_authentication_strength": "local_desktop_session",
        },
    )["result"]
    route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": proposed["item"]["id"], "action": "approve_memory"},
    )

    remote = route_request(
        conn,
        "memory.retrieve",
        {
            "query": "Do you remember our private moon garden plan?",
            "speaker_envelope": {
                "claimed_speaker": "Aleks",
                "channel": "mobile",
                "authentication_strength": "transport_claim_only",
            },
        },
    )["result"]
    local = route_request(
        conn,
        "memory.retrieve",
        {
            "query": "Do you remember our private moon garden plan?",
            "speaker_envelope": {
                "claimed_speaker": "Aleks",
                "channel": "desktop",
                "authentication_strength": "local_desktop_session",
            },
        },
    )["result"]

    assert remote["memory_context_used"] is False
    assert local["memory_context_used"] is True


def test_reconsolidation_approves_a_descendant_and_preserves_parent_ancestry(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "title": "Garden gate",
            "summary": "The garden gate was painted blue.",
            "confidence": "clear",
            "source_refs": ["chat:visible:gate"],
        },
    )["result"]
    parent_id = proposed["item"]["id"]
    route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": parent_id, "action": "approve_memory"},
    )
    revision = route_request(
        conn,
        "memory.reconsolidation.propose",
        {
            "source_table": "selene_memory_candidates",
            "source_id": parent_id,
            "corrected_summary": "The garden gate was painted green, not blue.",
            "source_refs": ["chat:visible:gate-correction"],
        },
    )["result"]

    before = conn.execute(
        "SELECT summary, state FROM selene_memory_candidates WHERE id = ?",
        (parent_id,),
    ).fetchone()
    assert before["summary"] == "The garden gate was painted blue."
    assert before["state"] == "approved_active_memory"
    assert revision["revision_candidate"]["state"] == "proposed"
    assert revision["parent_content_preserved"] is True

    with pytest.raises(ValueError, match="reconsolidation review"):
        route_request(
            conn,
            "memory.candidates.decide",
            {
                "candidate_id": revision["revision_candidate"]["id"],
                "action": "approve_memory",
            },
        )

    decided = route_request(
        conn,
        "memory.reconsolidation.decide",
        {"review_id": revision["review_id"], "action": "approve_revision"},
    )["result"]
    parent = conn.execute(
        "SELECT summary, state, payload_json FROM selene_memory_candidates WHERE id = ?",
        (parent_id,),
    ).fetchone()
    child = decided["revision_candidate"]

    assert parent["summary"] == "The garden gate was painted blue."
    assert parent["state"] == "superseded"
    assert child["state"] == "approved_active_memory"
    assert child["revision_ancestry"]["parent_source_id"] == str(parent_id)
    assert decided["revision_ancestry_preserved"] is True
    assert decided["parent_content_deleted"] is False


def test_revocation_and_deletion_request_stop_recall_without_physical_erasure(tmp_path):
    conn = _conn(tmp_path)
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {"title": "Workshop color", "summary": "The workshop shelf is amber."},
    )["result"]
    candidate_id = proposed["item"]["id"]
    route_request(conn, "memory.candidates.decide", {"candidate_id": candidate_id, "action": "approve_memory"})
    revoked = route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": candidate_id, "action": "revoke_use", "reason": "No longer use this."},
    )["result"]
    unknown = route_request(
        conn,
        "memory.retrieve",
        {"query": "Do you remember the amber workshop shelf?"},
    )["result"]
    deletion = route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": candidate_id, "action": "request_deletion"},
    )["result"]

    assert revoked["item"]["state"] == "revoked"
    assert unknown["memory_context_used"] is False
    assert deletion["item"]["state"] == "deletion_requested"
    assert conn.execute(
        "SELECT COUNT(*) FROM selene_memory_candidates WHERE id = ?", (candidate_id,)
    ).fetchone()[0] == 1
    assert len(deletion["item"]["payload_json"]["decision_history"]) >= 3
