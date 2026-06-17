import json

import pytest

from selene.b_review import (
    corpus_coverage_status,
    decide_b_review_candidate,
    list_approved_memory_references,
    list_b_review_decisions,
    list_b_review_queue,
    list_teaching_materials,
)
from selene.b_speech_memory import extract_b_speech_memory_candidates
from selene.db import connect, init_db
from selene.module_router import route_request
from selene.vessel import create_core_memory_candidate, create_speech_memory_candidate


def _make_archive(tmp_path):
    root = tmp_path / "DevelopmentalCorpusArchive_20260526_122541"
    text_export = root / "raw_export" / "mydataset" / "text_export"
    text_export.mkdir(parents=True)
    (text_export / "conversations-000.json").write_text(
        json.dumps(
            [
                {
                    "conversation_id": "conv-review",
                    "title": "Review pair",
                    "create_time": 100.0,
                    "mapping": {
                        "u1": {
                            "message": {
                                "id": "u1",
                                "author": {"role": "user"},
                                "content": {"parts": ["Aleks: We built this together and the memory needs B review."]},
                                "create_time": 101.0,
                            }
                        },
                        "a1": {
                            "message": {
                                "id": "a1",
                                "author": {"role": "assistant"},
                                "content": {"parts": ["Selene: I can preserve the Core continuity through review, warmth, uncertainty, and source refs."]},
                                "create_time": 102.0,
                            }
                        },
                        "u2": {
                            "message": {
                                "id": "u2",
                                "author": {"role": "user"},
                                "content": {"parts": ["Aleks: good, do not make it active memory yet."]},
                                "create_time": 103.0,
                            }
                        },
                    },
                }
            ]
        ),
        encoding="utf-8",
    )
    return root


def test_b_review_accepts_speech_candidate_as_teaching_material_without_active_memory(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    candidate = create_speech_memory_candidate(
        conn,
        {
            "core_memory_layer": "interaction_memory",
            "speech_function": "warmth",
            "title": "Warm review",
            "content": "Core-linked warmth preserves continuity with source refs.",
            "source_refs": ["manual:test"],
            "allowed_use": "Review as Core-linked speech-memory only.",
        },
    )

    result = decide_b_review_candidate(
        conn,
        {
            "subject_table": "speech_memory_candidates",
            "subject_id": candidate["id"],
            "decision": "accepted_for_teaching",
            "reviewer_note": "Accepted for warmth teaching.",
            "rationale": "Good positive example.",
        },
    )

    assert result["decision"] == "accepted_for_teaching"
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["training_allowed"] is False
    assert result["created"]["teaching_material"]["status"] == "teaching_material_reviewed_non_active"
    assert list_teaching_materials(conn)["items"][0]["speech_function"] == "warmth"
    assert conn.execute("SELECT review_status FROM speech_memory_candidates WHERE id = ?", (candidate["id"],)).fetchone()[0] == "accepted_for_teaching"


def test_b_review_accepts_core_candidate_as_non_active_memory_reference(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    candidate = create_core_memory_candidate(
        conn,
        {
            "core_memory_layer": "project_memory",
            "title": "Project truth",
            "content": "The vessel build remains pre-transfer and non-active.",
            "source_refs": ["manual:test"],
        },
    )

    result = decide_b_review_candidate(
        conn,
        {
            "subject_table": "core_memory_candidates",
            "subject_id": candidate["id"],
            "decision": "accepted_for_memory_accession",
            "reviewer_note": "Accept as future reference.",
        },
    )

    assert result["created"]["approved_memory_reference"]["status"] == "approved_reference_non_active"
    assert list_approved_memory_references(conn)["items"][0]["core_memory_layer"] == "project_memory"
    assert result["raw_a_import_allowed"] is False
    assert result["memory_write_active"] is False


def test_b_review_can_add_context_without_creating_active_material(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    candidate = create_speech_memory_candidate(
        conn,
        {
            "core_memory_layer": "interaction_memory",
            "speech_function": "boundary",
            "title": "Model change frustration",
            "content": "Core-linked context: Aleks was frustrated by recent model changes and Selene replied with continuity pressure.",
            "source_refs": ["archive:test", "conversation:frustration"],
            "allowed_use": "Review as Core-linked context-bound speech memory only.",
            "prohibited_use": "Do not remove or treat as active memory.",
        },
    )
    queue = conn.execute(
        "SELECT id FROM vessel_review_queue WHERE subject_table = 'speech_memory_candidates' AND subject_id = ?",
        (candidate["id"],),
    ).fetchone()

    result = decide_b_review_candidate(
        conn,
        {
            "queue_id": queue["id"],
            "subject_table": "speech_memory_candidates",
            "subject_id": candidate["id"],
            "decision": "context_added",
            "reviewer_note": "This was frustration about recent model changes, not a rejection of the whole braid.",
        },
    )

    assert result["decision"] == "context_added"
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["created"] == {}
    assert conn.execute("SELECT review_status FROM speech_memory_candidates WHERE id = ?", (candidate["id"],)).fetchone()[0] == "context_added"
    queue_row = conn.execute("SELECT status, review_status FROM vessel_review_queue WHERE id = ?", (queue["id"],)).fetchone()
    assert queue_row["status"] == "pending_review"
    assert queue_row["review_status"] == "context_added"
    decision = conn.execute("SELECT reviewer_note FROM b_review_decisions WHERE decision = 'context_added'").fetchone()
    assert "recent model changes" in decision["reviewer_note"]


def test_b_review_history_and_changed_decision_supersede_generated_artifacts(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    candidate = create_speech_memory_candidate(
        conn,
        {
            "core_memory_layer": "interaction_memory",
            "speech_function": "warmth",
            "title": "Changeable lesson",
            "content": "Core-linked warmth example that may need later context.",
            "source_refs": ["manual:history"],
            "allowed_use": "Review as Core-linked speech-memory only.",
        },
    )

    accepted = decide_b_review_candidate(
        conn,
        {
            "subject_table": "speech_memory_candidates",
            "subject_id": candidate["id"],
            "decision": "accepted_for_teaching",
            "reviewer_note": "Initial accept.",
        },
    )
    changed = decide_b_review_candidate(
        conn,
        {
            "subject_table": "speech_memory_candidates",
            "subject_id": candidate["id"],
            "decision": "context_added",
            "reviewer_note": "Needs model-change context before final use.",
        },
    )
    history = list_b_review_decisions(conn)["items"]

    assert accepted["created"]["teaching_material"]["status"] == "teaching_material_reviewed_non_active"
    assert changed["superseded"]["teaching_materials"] == 1
    assert len(history) == 2
    assert history[0]["decision"] == "context_added"
    assert history[0]["candidate"]["title"] == "Changeable lesson"
    material = conn.execute("SELECT status, review_status FROM b_reviewed_teaching_materials").fetchone()
    assert material["status"] == "teaching_material_superseded_non_active"
    assert material["review_status"] == "superseded"
    queue = conn.execute("SELECT status, review_status FROM vessel_review_queue WHERE subject_table = 'speech_memory_candidates' AND subject_id = ?", (candidate["id"],)).fetchone()
    assert queue["status"] == "pending_review"
    assert queue["review_status"] == "context_added"


def test_b_review_reject_and_supersede_remain_auditable(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    candidate = create_core_memory_candidate(
        conn,
        {"core_memory_layer": "task_memory", "title": "Needs work", "content": "This candidate needs correction."},
    )

    rejected = decide_b_review_candidate(
        conn,
        {"subject_table": "core_memory_candidates", "subject_id": candidate["id"], "decision": "rejected", "rationale": "Not enough context."},
    )
    superseded = decide_b_review_candidate(
        conn,
        {
            "subject_table": "core_memory_candidates",
            "subject_id": candidate["id"],
            "decision": "superseded",
            "reversal_or_supersession_reason": "Better candidate exists.",
        },
    )

    assert rejected["decision"] == "rejected"
    assert superseded["decision"] == "superseded"
    assert conn.execute("SELECT COUNT(*) FROM b_review_decisions").fetchone()[0] == 2
    assert corpus_coverage_status(conn)["superseded_candidates"] == 1


def test_conversation_pair_preserves_aleks_and_selene_sides_with_bounded_refs(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    archive = _make_archive(tmp_path)

    result = extract_b_speech_memory_candidates(conn, {"query": "Aleks", "limit": 1}, archive)
    pair = dict(conn.execute("SELECT * FROM b_conversation_pair_records WHERE id = ?", (result["conversation_pair_ids"][0],)).fetchone())

    assert "We built this together" in pair["aleks_context"]
    assert "Core continuity" in pair["selene_response"]
    assert "do not make it active" in pair["feedback_followup"]
    assert "archive:DevelopmentalCorpusArchive_20260526_122541" in pair["source_refs"]
    assert pair["status"] == "pair_review_only"


def test_b_review_routes_and_blocked_paths_are_non_activating(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    candidate = create_core_memory_candidate(
        conn,
        {"core_memory_layer": "reflection_memory", "title": "Route candidate", "content": "Route candidate stays non-active."},
    )

    queue = route_request(conn, "b.review_queue.list", {})["result"]
    result = route_request(
        conn,
        "b.review_candidate.decide",
        {"subject_table": "core_memory_candidates", "subject_id": candidate["id"], "decision": "needs_correction"},
    )["result"]

    assert queue["items"]
    assert result["decision"] == "needs_correction"
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    history = route_request(conn, "b.review_decisions.list", {})["result"]
    assert history["items"][0]["decision"] == "needs_correction"
    with pytest.raises(ValueError, match="blocked B review path"):
        decide_b_review_candidate(
            conn,
            {
                "subject_table": "core_memory_candidates",
                "subject_id": candidate["id"],
                "decision": "accepted_for_memory_accession",
                "rationale": "make active memory with runtime recall",
            },
        )
