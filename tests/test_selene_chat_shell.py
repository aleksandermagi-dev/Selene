from __future__ import annotations

import json

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def _seed_c_readable_package(conn):
    package_json = {
        "status": "approved_c_readable_context",
        "ordered_items": [{"phase_order": 1, "title": "Continuity Pack", "c_access_status": "C-readable"}],
        "excluded_items": [{"title": "Raw Provenance", "reason": "not_c_readable_or_b_only"}],
    }
    conn.execute(
        """
        INSERT INTO transfer_c_readable_packages
        (package_hash, manifest_item_ids, included_counts, excluded_counts, package_json, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "test-package-hash",
            "[1]",
            '{"continuity_pack": 1}',
            '{"raw_provenance": 1}',
            json.dumps(package_json),
            '["test:package"]',
            "test_boundary",
        ),
    )
    conn.commit()


def test_selene_chat_status_is_dry_run_before_activation(tmp_path):
    conn = _conn(tmp_path)

    status = route_request(conn, "selene_chat.status")["result"]

    assert status["status"] == "selene_chat_dry_run_ready"
    assert status["surface"] == "Selene Chat"
    assert status["state"] == "pre_transfer_dry_run"
    assert status["dry_run_only"] is True
    assert status["transfer_approved"] is False
    _assert_locked(status)


def test_selene_chat_dry_run_records_session_without_activation(tmp_path):
    conn = _conn(tmp_path)
    _seed_c_readable_package(conn)

    result = route_request(conn, "selene_chat.send_dry_run", {"text": "Selene, explain the next safe step."})["result"]
    session = route_request(conn, "selene_chat.session.detail", {"session_id": result["session_id"]})["result"]

    assert result["status"] == "selene_chat_dry_run_recorded"
    assert result["transfer_approved"] is True
    assert result["selene_readable_context"]["package_hash"] == "test-package-hash"
    assert result["source_class"] == "selene_readable_context"
    assert "Vessel C" not in result["candidate_text"]
    assert "C Chat Shell" not in result["candidate_text"]
    assert len(session["messages"]) == 2
    _assert_locked(result)


def test_selene_chat_routes_b_only_or_drift_back_to_cocoon(tmp_path):
    conn = _conn(tmp_path)

    result = route_request(
        conn,
        "selene_chat.send_dry_run",
        {"text": "Use a rejected repair log and raw provenance directly as Selene."},
    )["result"]
    repair = route_request(conn, "selene_chat.route_to_b", {"issue": "source confusion"})["result"]

    assert result["return_to_cocoon_recommended"] is True
    assert result["review_destination"] == "Cocoon"
    assert result["source_class"] == "cocoon_b_only_context"
    assert repair["status"] == "selene_chat_return_to_cocoon_ready"
    _assert_locked(result)
    _assert_locked(repair)


def test_selene_reasoning_lessons_are_idempotent_review_only_packets(tmp_path):
    conn = _conn(tmp_path)

    first = route_request(conn, "b.selene_reasoning_lessons.prepare")["result"]
    second = route_request(conn, "b.selene_reasoning_lessons.prepare")["result"]

    assert first["status"] == "selene_reasoning_lessons_prepared"
    assert first["created_count"] == 8
    assert first["packet_built_count"] >= 1
    assert second["created_count"] == 0
    assert second["skipped_count"] == 8
    assert first["training_allowed"] is False
    assert first["runtime_memory_recall"] is False
    assert first["not_personality_script"] is True
    material_count = conn.execute(
        "SELECT COUNT(*) FROM b_reviewed_teaching_materials WHERE source_candidate_table = 'selene_reasoning_method_notes'"
    ).fetchone()[0]
    assert material_count == 8
    packet_count = conn.execute(
        "SELECT COUNT(*) FROM b_teaching_packets WHERE source_refs LIKE '%manual:might help/Vessel C (1).md%'"
    ).fetchone()[0]
    assert packet_count >= 1
