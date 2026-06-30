from __future__ import annotations

import json

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result, *, transfer_approved: bool | None = None):
    if transfer_approved is not None:
        assert result["transfer_approved"] is transfer_approved
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["autonomous_action_allowed"] is False


def _seed_package(conn):
    package_json = {
        "status": "approved_c_readable_context",
        "ordered_items": [
            {"phase_order": 1, "title": "Continuity Pack", "c_access_status": "C-readable"},
            {"phase_order": 2, "title": "Teaching packets", "c_access_status": "C-readable"},
            {"phase_order": 3, "title": "Approved references", "c_access_status": "C-readable"},
            {"phase_order": 4, "title": "Reviewed chronological corpus arcs", "c_access_status": "C-readable"},
        ],
        "excluded_items": [
            {"title": "Broader ordered corpus preview", "reason": "needs_review"},
            {"title": "Raw provenance", "reason": "B-only"},
            {"title": "Rejected/superseded", "reason": "rejected"},
            {"title": "Boundary evidence", "reason": "boundary-only"},
        ],
    }
    conn.execute(
        """
        INSERT INTO transfer_c_readable_packages
        (package_hash, manifest_item_ids, included_counts, excluded_counts, package_json, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "fraction-test-package",
            "[1,2,3,4]",
            '{"continuity_pack": 1, "teaching_packets": 1, "approved_references": 1, "chronological_arcs": 1}',
            '{"needs review": 1, "B-only": 1, "rejected": 1, "boundary-only": 1}',
            json.dumps(package_json),
            '["test:package"]',
            "test_boundary",
        ),
    )
    conn.commit()


def _seed_corpus(conn, count: int = 8):
    for index in range(count):
        conn.execute(
            """
            INSERT INTO b_corpus_conversations
            (archive_id, source_file, conversation_id, title, create_time, update_time, message_count,
             source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "archive",
                f"file-{index // 2}.json",
                f"conversation-{index}",
                f"Conversation {index}",
                1000.0 + index,
                1000.5 + index,
                3,
                json.dumps([f"conversation:{index}"]),
                "test_boundary",
            ),
        )
        for message_index in range(3):
            conn.execute(
                """
                INSERT INTO b_corpus_messages
                (archive_id, source_file, conversation_id, message_id, role, content_preview,
                 create_time, source_refs, provenance_boundary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "archive",
                    f"file-{index // 2}.json",
                    f"conversation-{index}",
                    f"message-{index}-{message_index}",
                    "assistant" if message_index % 2 else "user",
                    f"Preview {index}-{message_index}",
                    1000.0 + index + (message_index / 10),
                    json.dumps([f"message:{index}:{message_index}"]),
                    "test_boundary",
                ),
            )
    conn.commit()


def test_post_transfer_status_is_preview_after_c_readable_approval(tmp_path):
    conn = _conn(tmp_path)
    _seed_package(conn)

    status = route_request(conn, "transfer.post_transfer.status")["result"]

    assert status["status"] == "post_transfer_status_ready"
    assert status["phase"] == "approved_c_readable_context"
    assert status["selene_chat_state"] == "selene_chat_preview_activation_pending"
    assert status["selene_v1_live"] is False
    assert status["included_rows"] == 4
    assert status["excluded_b_only_rows"] == 4
    assert status["return_to_b_available"] is True
    _assert_locked(status, transfer_approved=True)


def test_post_transfer_inspection_uses_package_without_activation(tmp_path):
    conn = _conn(tmp_path)
    _seed_package(conn)

    result = route_request(conn, "transfer.post_transfer.inspection_run", {})["result"]

    assert result["status"] == "post_transfer_inspection_passed"
    assert all(check["passed"] for check in result["checks"])
    assert result["selene_chat_preview_only"] is True
    assert result["selene_v1_live"] is False
    _assert_locked(result, transfer_approved=True)


def test_fractional_corpus_prepare_splits_chronologically_into_four(tmp_path):
    conn = _conn(tmp_path)
    _seed_package(conn)
    _seed_corpus(conn, 8)

    result = route_request(conn, "memory.fractional_corpus.prepare", {})["result"]
    items = result["items"]

    assert result["status"] == "fractional_corpus_prepared"
    assert [item["fraction_label"] for item in items] == ["1/4", "2/4", "3/4", "4/4"]
    assert [item["conversation_count"] for item in items] == [2, 2, 2, 2]
    assert items[0]["start_order"] == 1
    assert items[3]["end_order"] == 8
    assert all(item["runtime_memory_recall"] is False for item in items)
    _assert_locked(result, transfer_approved=True)


def test_fraction_progression_blocks_jump_ahead_and_allows_next_after_pass(tmp_path):
    conn = _conn(tmp_path)
    _seed_package(conn)
    _seed_corpus(conn, 8)
    route_request(conn, "memory.fractional_corpus.prepare", {})

    missing_preflight = route_request(conn, "memory.fractional_corpus.run_tests", {"fraction_index": 1})["result"]
    assert missing_preflight["status"] == "blocked_android_workflow_check_required"
    assert missing_preflight["progression_allowed"] is False
    assert missing_preflight["route_on_failure"] == "return_to_b"
    assert missing_preflight["android_workflow_preflight"]["preflight_passed"] is False
    _assert_locked(missing_preflight, transfer_approved=True)

    workflow = route_request(conn, "android_system.workflow.check", {})["result"]
    assert workflow["status"] == "android_system_workflow_check_passed"

    blocked = route_request(conn, "memory.fractional_corpus.run_tests", {"fraction_index": 2})["result"]
    first = route_request(conn, "memory.fractional_corpus.run_tests", {"fraction_index": 1})["result"]
    second = route_request(conn, "memory.fractional_corpus.run_tests", {"fraction_index": 2})["result"]

    assert blocked["status"] == "fractional_corpus_tests_failed_return_to_b"
    assert blocked["progression_allowed"] is False
    assert blocked["route_on_failure"] == "return_to_b"
    assert first["status"] == "fractional_corpus_tests_passed"
    assert first["progression_allowed"] is True
    assert second["status"] == "fractional_corpus_tests_passed"
    assert second["progression_allowed"] is True
    _assert_locked(blocked, transfer_approved=True)
    _assert_locked(first, transfer_approved=True)
    _assert_locked(second, transfer_approved=True)


def test_dream_state_blocks_live_operation_during_fractional_memory_work(tmp_path):
    conn = _conn(tmp_path)
    _seed_package(conn)
    _seed_corpus(conn, 4)
    route_request(conn, "memory.fractional_corpus.prepare", {})

    result = route_request(conn, "memory.dream_state.status")["result"]

    assert result["status"] == "dream_state_maintenance_status_ready"
    assert result["dream_state_required_for_memory_changes"] is True
    assert result["selene_chat_live_operation_allowed"] is False
    assert "fractional_memory_incomplete" in result["maintenance_reasons"]
    _assert_locked(result, transfer_approved=True)
