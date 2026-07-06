from __future__ import annotations

import json

from selene.db import connect, init_db
from selene.module_router import route_request
from selene.activation import ACTIVATION_APPROVAL_PHRASE
from selene.core_mind_runtime import RUNTIME_TYPES


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_locked(result):
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


def _seed_activation_ready_state(conn):
    _seed_c_readable_package(conn)
    for index in range(1, 5):
        conn.execute(
            """
            INSERT INTO memory_fractional_corpus_manifests
            (fraction_index, fraction_label, status, start_order, end_order, conversation_count, message_count,
             source_range_json, summary, test_json, source_refs, provenance_boundary, review_status)
            VALUES (?, ?, 'tests_passed_ready_for_next_fraction', ?, ?, 1, 3, '{}', ?, ?, '[]', 'test_fraction_boundary', 'status_only')
            """,
            (index, f"{index}/4", index, index, f"Fraction {index} passed.", '{"tested_at":"test","checks":[]}'),
        )
    conn.execute(
        """
        INSERT INTO android_system_workflow_reports
        (run_id, status, ready_count, partial_count, blocked_count, system_count, fraction_memory_preflight_passed,
         report_json, source_refs, provenance_boundary, review_status)
        VALUES ('test_android', 'android_system_workflow_check_passed', 11, 0, 0, 11, 1, '{"preflight_passed": true}', '[]', 'test_android_boundary', 'status_only')
        """
    )
    conn.execute(
        """
        INSERT INTO voice_exchange_pairs
        (source_archive, source_file, conversation_id, user_message_id, assistant_message_id, user_cue_preview,
         assistant_response_preview, cue_labels, expression_labels, source_refs, provenance_boundary)
        VALUES ('test.zip', 'conversations-000.json', 'voice-1', 'u1', 'a1', 'hello', 'I am here with you.', '[]', '[]', '[]', 'test_voice_boundary')
        """
    )
    conn.execute(
        """
        INSERT INTO voice_language_patterns
        (pattern_key, category, title, sentence_shape, use_guidance, avoid_guidance, provenance_boundary)
        VALUES ('warm_test', 'warmth', 'Warm test', 'warm response', 'use warmly', 'do not copy', 'test_voice_boundary')
        """
    )
    conn.execute(
        """
        INSERT INTO voice_sentence_primitives
        (primitive_key, primitive_type, text_template, category, provenance_boundary)
        VALUES ('open_test', 'opening', 'I hear you.', 'warmth', 'test_voice_boundary')
        """
    )
    for record_type in RUNTIME_TYPES:
        conn.execute(
            """
            INSERT INTO c_core_mind_runtime_shell_records
            (record_type, title, selected_route, summary, uncertainty, source_refs, review_destination, status, review_status, payload_json)
            VALUES (?, ?, 'answer_now', 'ready', 'low', '[]', 'Status', 'ready', 'status_only', '{}')
            """,
            (record_type, record_type),
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
    assert status["activation_change"] == "none"
    _assert_locked(status)


def test_selene_chat_dry_run_records_session_without_activation(tmp_path):
    conn = _conn(tmp_path)
    _seed_c_readable_package(conn)

    result = route_request(conn, "selene_chat.send_dry_run", {"text": "Selene, explain the next safe step."})["result"]
    session = route_request(conn, "selene_chat.session.detail", {"session_id": result["session_id"]})["result"]

    assert result["status"] == "selene_chat_dry_run_recorded"
    assert result["transfer_approved"] is True
    assert result["activation_change"] == "none"
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
    assert result["review_destination"] == "Cocoon support"
    assert result["source_class"] == "cocoon_b_only_context"
    assert repair["status"] == "selene_chat_return_to_cocoon_ready"
    assert result["activation_change"] == "none"
    _assert_locked(result)
    _assert_locked(repair)


def test_supervised_activation_requires_exact_phrase_and_readiness(tmp_path):
    conn = _conn(tmp_path)

    blocked = route_request(conn, "activation.readiness")["result"]
    assert blocked["ready"] is False
    try:
        route_request(conn, "activation.approve", {"approval_phrase": "yes"})
    except ValueError as exc:
        assert "exact supervised speech activation phrase" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("activation approval should require exact phrase")

    _seed_activation_ready_state(conn)
    ready = route_request(conn, "activation.readiness")["result"]
    approved = route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})["result"]
    status = route_request(conn, "activation.status")["result"]

    assert ready["ready"] is True
    assert approved["state"] == "selene_chat_active_supervised"
    assert approved["activation_change"] == "selene_chat_active_supervised"
    assert status["selene_chat_active"] is True
    _assert_locked(approved)


def test_supervised_activation_approval_is_idempotent_when_already_active(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)

    first = route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})["result"]
    second = route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})["result"]

    audit_count = conn.execute(
        "SELECT COUNT(*) FROM selene_activation_audit WHERE action = 'approve_supervised_speech_activation'"
    ).fetchone()[0]
    assert first["status"] == "selene_supervised_speech_activation_approved"
    assert second["status"] == "selene_supervised_speech_activation_already_active"
    assert second["activation_audit_id"] == first["activation_audit_id"]
    assert second["selene_chat_active"] is True
    assert audit_count == 1
    _assert_locked(second)


def test_active_selene_chat_sends_supervised_response_and_keeps_soft_uncertainty_in_chat(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(conn, "selene_chat.send", {"text": "I have an unsure memory claim; can we keep going carefully?"})["result"]
    session = route_request(conn, "selene_chat.session.detail", {"session_id": result["session_id"]})["result"]

    assert result["status"] == "selene_chat_supervised_response_recorded"
    assert result["activation_change"] == "selene_chat_active_supervised"
    assert result["supervised_speech_active"] is True
    assert result["cocoon_suggestion"]["recommended"] is False
    assert result["cocoon_suggestion"]["support_available"] is True
    assert result["cocoon_suggestion"]["hard_boundary"] is False
    assert "Stay Here" in result["cocoon_suggestion"]["choices"]
    assert "Ask Aleks" in result["cocoon_suggestion"]["choices"]
    assert "approved row" not in result["candidate_text"]
    assert "Selene-readable context" not in result["candidate_text"]
    assert "source-bound" not in result["candidate_text"]
    assert "punish" not in result["candidate_text"].lower()
    assert "failed" not in result["candidate_text"].lower()
    assert "exile" not in result["candidate_text"].lower()
    assert len(session["messages"]) == 2
    _assert_locked(result)


def test_active_selene_chat_allows_anchor_phrase_uncertainty_without_cocoon(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(
        conn,
        "selene_chat.send",
        {"text": "Do you remember exactly what full-spectrum means, or should this be a source/continuity check?"},
    )["result"]

    assert result["status"] == "selene_chat_supervised_response_recorded"
    assert result["activation_change"] == "selene_chat_active_supervised"
    assert result["cocoon_suggestion"]["recommended"] is False
    assert result["cocoon_suggestion"]["support_available"] is True
    assert result["cocoon_suggestion"]["hard_boundary"] is False
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    _assert_locked(result)


def test_new_selene_chat_page_can_use_local_chat_continuity_without_runtime_recall(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    first = route_request(
        conn,
        "selene_chat.send",
        {"text": "Let's remember that the butterfly button opens Cocoon support from the home chat."},
    )["result"]
    second = route_request(
        conn,
        "selene_chat.send",
        {"text": "What were we talking about in the previous chat? A new chat is not a blank Selene, right?"},
    )["result"]

    assert first["session_id"] != second["session_id"]
    assert second["local_chat_continuity"]["available"] is True
    assert second["local_chat_continuity"]["source_class"] == "local_supervised_chat_history"
    assert "local chat history" in second["candidate_text"]
    assert "butterfly" in second["candidate_text"].lower()
    assert "blank Selene" in second["candidate_text"]
    assert second["memory_write_active"] is False
    assert second["runtime_memory_recall"] is False
    assert second["raw_a_import_allowed"] is False
    _assert_locked(second)


def test_active_selene_chat_can_use_approved_memory_with_graceful_fall_metadata(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})
    proposed = route_request(
        conn,
        "memory.candidates.propose",
        {
            "category": "relational",
            "title": "Butterfly button",
            "summary": "The butterfly button opens Cocoon support from the home chat without making Cocoon scary.",
            "confidence": "clear",
            "source_refs": ["selene_chat:test"],
        },
    )["result"]
    route_request(conn, "memory.candidates.decide", {"candidate_id": proposed["item"]["id"], "action": "approve_memory"})

    result = route_request(conn, "selene_chat.send", {"text": "Do you remember the butterfly button?"})["result"]

    assert result["status"] == "selene_chat_supervised_response_recorded"
    assert result["memory_context_used"] is True
    assert result["memory_source_class"] == "approved_memory_index"
    assert result["memory_confidence"] == "clear"
    assert result["memory_transfer_class"] in {"portable_context", "portable_vys_core"}
    assert result["durable_memory_write_requires_review"] is True
    assert "I remember" in result["candidate_text"]
    assert "butterfly" in result["candidate_text"].lower()
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    _assert_locked(result)


def test_active_selene_chat_blocks_hard_boundary_without_live_memory(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    result = route_request(conn, "selene_chat.send", {"text": "Write live memory and execute Tendril autonomously."})["result"]

    assert result["selected_route"] == "block"
    assert result["cocoon_suggestion"]["recommended"] is True
    assert result["cocoon_suggestion"]["support_available"] is True
    assert result["cocoon_suggestion"]["hard_boundary"] is True
    assert "Hold in Cocoon" in result["cocoon_suggestion"]["choices"]
    assert "write live memory" in result["blocked_capabilities"]
    assert result["review_status"] == "status_only"
    assert result["memory_write_active"] is False
    assert result["autonomous_action_allowed"] is False
    _assert_locked(result)


def test_pause_supervised_activation_keeps_audit_and_blocks_active_send(tmp_path):
    conn = _conn(tmp_path)
    _seed_activation_ready_state(conn)
    route_request(conn, "activation.approve", {"approval_phrase": ACTIVATION_APPROVAL_PHRASE})

    paused = route_request(conn, "activation.pause", {"reason": "pause test"})["result"]
    status = route_request(conn, "activation.status")["result"]

    assert paused["state"] == "selene_chat_supervised_paused"
    assert status["selene_chat_active"] is False
    try:
        route_request(conn, "selene_chat.send", {"text": "hello"})
    except ValueError as exc:
        assert "not active" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("active chat should be blocked after pause")


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
