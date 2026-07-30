from __future__ import annotations

import json

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["durable_memory_write_requires_review"] is True


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


def test_memory_status_names_the_resident_reviewed_lifecycle(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(conn, "memory.index.status")["result"]
    lifecycle = result["memory_lifecycle_contract"]

    assert result["resident_memory_contract_version"] == "v2_dream_review_bridge"
    assert lifecycle["approved_retrieval"] == "approved_active_memory_only"
    assert lifecycle["new_retention"] == "proposal_then_Aleks_review"
    assert lifecycle["dream_consolidation"] == (
        "source_bound_reflections_then_Aleks_review; "
        "Memory routing creates an inactive candidate only"
    )
    assert lifecycle["silent_promotion"] is False
    assert lifecycle["raw_corpus_recall"] is False
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
    excluded = route_request(
        conn,
        "memory.candidates.decide",
        {"candidate_id": proposed["item"]["id"], "action": "mark_do_not_transfer"},
    )["result"]["item"]
    status = route_request(conn, "memory.index.status")["result"]

    assert excluded["state"] == "approved_active_memory"
    assert excluded["transfer_class"] == "do_not_transfer"
    assert excluded["retrieval_eligible"] is False
    assert excluded["memory_context_used"] is False
    assert excluded["display_region"] == "cocoon_memory_review"
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
    assert before["items"][0]["state"] == "proposed"
    assert approved["item"]["state"] == "approved_active_memory"
    assert approved["item"]["chat_use_permission"] == "can_use_in_chat"
    assert approved["item"]["review_status"] == "accepted_for_memory"
    _assert_locked(proposed)
    _assert_locked(approved)


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
