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
