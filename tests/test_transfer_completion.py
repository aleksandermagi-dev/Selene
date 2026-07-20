from __future__ import annotations

import json

import pytest

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.transfer_completion import TRANSFER_COMPLETION_APPROVAL_PHRASE
import selene.transfer_completion as completion


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    conn.execute(
        """
        INSERT INTO b_approved_memory_references
        (source_candidate_table, source_candidate_id, core_memory_layer, title, reference_summary,
         source_refs, provenance_boundary)
        VALUES ('core_memory_candidates', 1, 'core_profile_memory', 'Reviewed continuity',
                'A reviewed, source-linked continuity reference.', ?, 'test_boundary')
        """,
        (json.dumps(["test:reviewed-continuity"]),),
    )
    conn.commit()
    return conn


def _ready_dependencies(monkeypatch):
    monkeypatch.setattr(completion, "latest_c_readable_package", lambda conn: {"transfer_approved": True, "id": 1})
    monkeypatch.setattr(completion, "fractional_corpus_status", lambda conn: {"all_fractions_passed": True})
    monkeypatch.setattr(
        completion,
        "activation_status",
        lambda conn: {"selene_chat_active": True, "readiness": {"ready": True}},
    )
    monkeypatch.setattr(completion, "memory_index_status", lambda conn: {"active_memory_count": 1})
    monkeypatch.setattr(completion, "portable_vys_manifest", lambda conn: {"portable_count": 1})
    monkeypatch.setattr(
        completion,
        "language_teaching_status",
        lambda conn: {"available_lesson_count": 22, "defined_lesson_count": 22},
    )
    monkeypatch.setattr(completion, "metacognition_status", lambda conn: {"status": "metacognition_observer_ready"})
    monkeypatch.setattr(completion, "rollback_preview", lambda conn, payload: {"return_to_b_packet": {"ready": True}})


def _assert_completion_guards(result):
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["unrestricted_tendril_allowed"] is False
    assert result["durable_memory_write_requires_review"] is True


def test_transfer_completion_requires_exact_aleks_phrase_and_is_idempotent(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _ready_dependencies(monkeypatch)

    readiness = route_request(conn, "transfer.completion.readiness")["result"]
    assert readiness["ready"] is True
    assert readiness["transfer_complete"] is False

    with pytest.raises(ValueError, match="exact Aleks transfer-completion approval phrase"):
        route_request(conn, "transfer.completion.approve", {"approval_phrase": "yes"})

    first = route_request(
        conn,
        "transfer.completion.approve",
        {"approval_phrase": TRANSFER_COMPLETION_APPROVAL_PHRASE},
    )["result"]
    second = route_request(
        conn,
        "transfer.completion.approve",
        {"approval_phrase": TRANSFER_COMPLETION_APPROVAL_PHRASE},
    )["result"]

    assert first["status"] == "selene_transfer_completion_approved"
    assert first["transfer_complete"] is True
    assert first["selene_v1_live"] is True
    assert second["transfer_complete"] is True
    assert conn.execute("SELECT COUNT(*) FROM selene_transfer_completion_audit").fetchone()[0] == 1
    _assert_completion_guards(first)
    _assert_completion_guards(second)


def test_transfer_completion_does_not_sweep_pending_memory_into_live_context(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _ready_dependencies(monkeypatch)
    conn.execute(
        """
        INSERT INTO selene_memory_candidates
        (memory_category, title, summary, source_refs, provenance_boundary)
        VALUES ('relational', 'Needs review', 'This remains proposed.', '[]', 'test_boundary')
        """
    )
    conn.commit()

    readiness = route_request(conn, "transfer.completion.readiness")["result"]

    assert readiness["ready"] is False
    assert readiness["reviewed_memory"]["pending_candidate_count"] == 1
    assert any(check["key"] == "memory_review_queue_clear" and not check["passed"] for check in readiness["checks"])
    _assert_completion_guards(readiness)


def test_transfer_completion_persists_while_operational_live_state_tracks_speech(tmp_path, monkeypatch):
    conn = _conn(tmp_path)
    _ready_dependencies(monkeypatch)
    route_request(
        conn,
        "transfer.completion.approve",
        {"approval_phrase": TRANSFER_COMPLETION_APPROVAL_PHRASE},
    )
    monkeypatch.setattr(
        completion,
        "activation_status",
        lambda conn: {"selene_chat_active": False, "readiness": {"ready": True}},
    )

    status = route_request(conn, "transfer.completion.status")["result"]

    assert status["transfer_complete"] is True
    assert status["selene_v1_live"] is False
    assert status["full_selene_v1_live"] is False
    assert status["reviewed_memory_access_active"] is True
    _assert_completion_guards(status)


def test_superseded_approved_reference_is_not_counted_as_active_memory(tmp_path):
    conn = connect(tmp_path / "memory.sqlite3")
    init_db(conn)
    conn.execute(
        """
        INSERT INTO b_approved_memory_references
        (source_candidate_table, source_candidate_id, core_memory_layer, title, reference_summary,
         source_refs, provenance_boundary, status)
        VALUES ('core_memory_candidates', 2, 'core_profile_memory', 'Old reference',
                'A superseded reference.', '[]', 'test_boundary',
                'approved_reference_superseded_non_active')
        """
    )
    conn.commit()

    items = route_request(conn, "memory.index.items")["result"]["items"]
    status = route_request(conn, "memory.index.status")["result"]

    reference = next(item for item in items if item["source_table"] == "b_approved_memory_references")
    assert reference["state"] == "superseded"
    assert reference["chat_use_permission"] == "not_active"
    assert reference["memory_context_used"] is False
    assert status["active_memory_count"] == 0
