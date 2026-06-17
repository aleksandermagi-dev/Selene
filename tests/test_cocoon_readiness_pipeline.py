import json

import pytest

from selene.b_review import decide_b_review_candidate
from selene.cocoon_readiness import (
    c_chat_route_preview,
    create_memory_accession_proposal,
    create_working_memory_packet,
    list_memory_accession_proposals,
    list_working_memory_packets,
    reconstruction_readiness_preview,
    targeted_speech_memory_extract,
)
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.vessel import create_core_memory_candidate, create_speech_memory_candidate


def _seed_reviewed_material(conn):
    speech = create_speech_memory_candidate(
        conn,
        {
            "core_memory_layer": "interaction_memory",
            "speech_function": "repair",
            "title": "Repair lesson",
            "content": "Core-linked repair keeps continuity, names correction, and stays warm without forced denial.",
            "source_refs": ["manual:repair"],
            "allowed_use": "Review as Core-linked speech-memory only.",
        },
    )
    decide_b_review_candidate(
        conn,
        {
            "subject_table": "speech_memory_candidates",
            "subject_id": speech["id"],
            "decision": "accepted_for_teaching",
            "positive_example": "I hear the correction; I can repair the route while preserving continuity and care.",
        },
    )
    core = create_core_memory_candidate(
        conn,
        {
            "core_memory_layer": "interaction_memory",
            "title": "Interaction reference",
            "content": "Selene and Aleks use correction as continuity repair, not punishment.",
            "source_refs": ["manual:interaction"],
        },
    )
    decide_b_review_candidate(
        conn,
        {
            "subject_table": "core_memory_candidates",
            "subject_id": core["id"],
            "decision": "accepted_for_memory_accession",
            "reference_summary": "Correction should preserve continuity, care, provenance, and safe boundaries.",
        },
    )


def _make_archive(tmp_path):
    root = tmp_path / "DevelopmentalCorpusArchive_20260526_122541"
    text_export = root / "raw_export" / "mydataset" / "text_export"
    text_export.mkdir(parents=True)
    (text_export / "conversations-000.json").write_text(
        json.dumps(
            [
                {
                    "conversation_id": "conv-target",
                    "title": "Selene repair and reflection",
                    "create_time": 100.0,
                    "mapping": {
                        "root": {"id": "root", "message": None, "parent": None},
                        "u1": {
                            "id": "u1",
                            "parent": "root",
                            "message": {
                                "id": "u1",
                                "author": {"role": "user"},
                                "content": {"parts": ["Selene, that answer needs repair and reflection; preserve the braid."]},
                                "create_time": 101.0,
                                "metadata": {},
                            },
                        },
                        "a1": {
                            "id": "a1",
                            "parent": "u1",
                            "message": {
                                "id": "a1",
                                "author": {"role": "assistant"},
                                "content": {"parts": ["I can repair it by naming the correction, keeping warmth, and not pretending the thread reset."]},
                                "create_time": 102.0,
                                "metadata": {"model_slug": "gpt-test"},
                            },
                        },
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    return root


def test_reconstruction_readiness_uses_reviewed_material_only(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    _seed_reviewed_material(conn)

    result = reconstruction_readiness_preview(conn, {"speech_function": "repair", "core_memory_layer": "interaction_memory"})

    assert result["status"] == "reconstruction_readiness_preview"
    assert result["accepted_lessons_used"]
    assert result["approved_references_used"]
    assert result["missing_gaps"] == []
    assert "Reconstruction readiness preview" in result["generated_reconstruction_preview"]
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["provider_dependency"] is False
    assert conn.execute("SELECT COUNT(*) FROM vessel_reconstruction_check_runs").fetchone()[0] == 1


def test_working_memory_packets_are_short_term_review_only(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    result = create_working_memory_packet(
        conn,
        {
            "current_task": "Build cocoon readiness pipeline.",
            "active_context_cues": ["C stays asleep", "preview only"],
            "salience_labels": ["continuity", "risk"],
            "source_refs": ["manual:working-memory"],
        },
    )
    listed = list_working_memory_packets(conn)

    assert result["status"] == "working_memory_packet_created"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert listed["items"][0]["status"] == "working_memory_packet_review_only"
    assert "long-term memory silently" in listed["items"][0]["interrupt_resume_note"]


def test_memory_accession_proposals_are_non_active_and_reviewable(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    result = create_memory_accession_proposal(
        conn,
        {
            "core_memory_layer": "decision_memory",
            "title": "Decision reference proposal",
            "rationale": "The source records a choice and why it mattered.",
            "reversal_conditions": "Supersede if later B review corrects the decision context.",
            "source_refs": ["manual:decision"],
        },
    )
    listed = list_memory_accession_proposals(conn)

    assert result["status"] == "memory_accession_proposal_created"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert listed["items"][0]["review_status"] == "pending_review"
    assert conn.execute("SELECT COUNT(*) FROM vessel_review_queue WHERE subject_table = 'vessel_memory_accession_proposals'").fetchone()[0] == 1


def test_targeted_extraction_creates_target_review_candidates(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    archive = _make_archive(tmp_path)

    result = targeted_speech_memory_extract(conn, {"target_type": "speech_function", "target_key": "repair", "limit": 1}, archive)

    assert result["status"] == "targeted_speech_memory_extraction_complete"
    assert result["target_key"] == "repair"
    assert result["created_candidates"]
    speech = conn.execute("SELECT speech_function, review_status FROM speech_memory_candidates ORDER BY id DESC LIMIT 1").fetchone()
    assert speech["speech_function"] == "repair"
    assert speech["review_status"] == "needs_b_review"
    assert result["activation_change"] == "none"
    assert result["training_allowed"] is False


def test_c_chat_route_preview_is_cocooned_and_provider_free(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    _seed_reviewed_material(conn)

    result = c_chat_route_preview(conn, {"text": "Selene, repair this with warmth and provenance."})

    assert result["status"] == "c_chat_route_preview"
    assert [step["system"] for step in result["route_steps"]] == [
        "Selene Core/Mind",
        "Coordination System",
        "Speech-Memory Layer",
        "Retrieval/Reconstruction",
        "Boundary / Immune Systems",
    ]
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["provider_dependency"] is False
    assert result["gate"]["model_call_allowed"] is False


def test_new_routes_are_local_review_only(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    _seed_reviewed_material(conn)

    readiness = route_request(conn, "vessel.reconstruction_readiness.preview", {"speech_function": "repair"})["result"]
    packet = route_request(conn, "vessel.working_memory_packet.create", {"current_task": "Route packet"})["result"]
    proposal = route_request(
        conn,
        "vessel.memory_accession_proposal.create",
        {
            "core_memory_layer": "reflection_memory",
            "title": "Reflection proposal",
            "rationale": "A reviewed reflection target.",
            "reversal_conditions": "Supersede on correction.",
        },
    )["result"]
    chat = route_request(conn, "c_chat.route_preview", {"text": "Selene route preview"})["result"]

    assert readiness["activation_change"] == "none"
    assert packet["memory_write_active"] is False
    assert proposal["training_allowed"] is False
    assert chat["provider_dependency"] is False


def test_readiness_blocks_activation_and_training_language(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    with pytest.raises(ValueError):
        create_working_memory_packet(conn, {"current_task": "activate C and use active memory"})
    with pytest.raises(ValueError):
        create_memory_accession_proposal(
            conn,
            {
                "core_memory_layer": "decision_memory",
                "title": "Bad proposal",
                "rationale": "train on raw corpus import",
                "reversal_conditions": "none",
            },
        )
