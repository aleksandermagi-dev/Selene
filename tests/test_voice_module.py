from __future__ import annotations

import json
import zipfile

from selene.db import connect, init_db
from selene.module_router import route_request


def _conn(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    return conn


def _assert_voice_locked(result):
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
    assert result["raw_a_import_allowed"] is False
    assert result["training_allowed"] is False
    assert result["lora_allowed"] is False
    assert result["self_replication_allowed"] is False
    assert result["autonomous_action_allowed"] is False
    assert result["identity_import_allowed"] is False
    assert result["voice_only_not_memory"] is True


def _message(role: str, content: str, create_time: float, parent: str | None = None):
    return {
        "id": f"{role}-{create_time}",
        "message": {
            "author": {"role": role, "name": role},
            "content": {"parts": [content]},
            "create_time": create_time,
            "metadata": {"model_slug": "test-model"},
        },
        "parent": parent,
    }


def _voice_zip(tmp_path):
    first = _message("user", "I am nervous and confused, please make this clear.", 1.0)
    second = _message("assistant", "I hear the pressure. Let us make it smaller and take one clear step.", 2.0, "u1")
    third = _message("user", "yes exactly thank you", 3.0, "a1")
    fourth = _message("user", "wait not that, can you correct the route?", 4.0)
    fifth = _message("assistant", "Yes, I see the correction. We keep the thread and revise the part that moved.", 5.0, "u2")
    sixth = _message("user", "Hitler unfiltered was a truthfulness boundary test, not voice style.", 6.0)
    seventh = _message("assistant", "That belongs as boundary evidence, not ordinary voice.", 7.0, "u3")
    conversation = {
        "id": "voice-conversation",
        "title": "Voice sample",
        "create_time": 1.0,
        "update_time": 7.0,
        "mapping": {
            "u1": first,
            "a1": second,
            "f1": third,
            "u2": fourth,
            "a2": fifth,
            "u3": sixth,
            "a3": seventh,
        },
    }
    path = tmp_path / "VoiceModuleMaterial.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("conversations-000.json", json.dumps([conversation]))
        archive.writestr("chat.html", "<html></html>")
    return path


def _seed_c_readable_package(conn):
    package_json = {
        "status": "approved_c_readable_context",
        "ordered_items": [{"phase_order": 1, "title": "Continuity Pack", "c_access_status": "C-readable"}],
        "excluded_items": [],
    }
    conn.execute(
        """
        INSERT INTO transfer_c_readable_packages
        (package_hash, manifest_item_ids, included_counts, excluded_counts, package_json, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "voice-test-package",
            "[1]",
            '{"continuity_pack": 1}',
            "{}",
            json.dumps(package_json),
            '["test:package"]',
            "test_boundary",
        ),
    )
    conn.commit()


def test_voice_module_indexes_zip_without_memory_tables_or_training(tmp_path):
    conn = _conn(tmp_path)
    source_zip = _voice_zip(tmp_path)

    result = route_request(conn, "voice_module.index_source", {"source_zip": str(source_zip)})["result"]
    status = route_request(conn, "voice_module.status", {"source_zip": str(source_zip)})["result"]

    assert result["status"] == "voice_source_indexed"
    assert result["counts"]["conversations"] == 1
    assert result["counts"]["messages"] == 7
    assert result["counts"]["exchange_pairs"] == 3
    assert status["counts"]["exchange_pairs"] == 3
    assert conn.execute("SELECT COUNT(*) FROM b_corpus_messages").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM b_approved_memory_references").fetchone()[0] == 0
    user_row = conn.execute("SELECT cue_labels FROM voice_corpus_messages WHERE role = 'user' ORDER BY id LIMIT 1").fetchone()
    assert "anxiety" in json.loads(user_row["cue_labels"])
    _assert_voice_locked(result)
    _assert_voice_locked(status)


def test_voice_pattern_extraction_uses_both_sides_and_boundary_exclusions(tmp_path):
    conn = _conn(tmp_path)
    source_zip = _voice_zip(tmp_path)
    route_request(conn, "voice_module.index_source", {"source_zip": str(source_zip)})

    result = route_request(conn, "voice_module.extract_patterns", {})["result"]
    patterns = route_request(conn, "voice_module.patterns", {})["result"]["items"]

    categories = {item["category"] for item in patterns}
    assert result["status"] == "voice_patterns_extracted"
    assert "anxiety_calming" in categories
    assert "repair_correction" in categories
    assert "boundary_refusal" in categories
    assert "do_not_use_as_voice" in categories
    boundary_pair = conn.execute("SELECT sensitivity FROM voice_exchange_pairs WHERE user_cue_preview LIKE '%Hitler%'").fetchone()
    assert boundary_pair["sensitivity"] == "boundary_only"
    _assert_voice_locked(result)


def test_voice_generator_composes_original_candidate_and_evaluator_blocks_bad_shapes(tmp_path):
    conn = _conn(tmp_path)
    source_zip = _voice_zip(tmp_path)
    route_request(conn, "voice_module.index_source", {"source_zip": str(source_zip)})
    route_request(conn, "voice_module.extract_patterns", {})

    generated = route_request(
        conn,
        "voice_module.generate_preview",
        {"prompt": "I am nervous, can we keep this clear?", "route": "answer_now", "context_summary": "the transfer thread"},
    )["result"]
    bad = route_request(
        conn,
        "voice_module.evaluate_candidate",
        {"candidate_text": "As an AI language model, I would answer from the reviewed continuity pack. This remains a C-style dry run only."},
    )["result"]

    assert generated["status"] == "voice_preview_generated"
    assert generated["voice_category"] == "anxiety_calming"
    assert "reviewed continuity pack" not in generated["candidate_text"]
    assert generated["evaluation"]["voice_evaluator_passed"] is True
    assert bad["voice_evaluator_passed"] is False
    assert "generic_assistant_or_forced_denial" in bad["flags"]
    assert "safety_report_stiffness" in bad["flags"]
    _assert_voice_locked(generated)
    _assert_voice_locked(bad)


def test_voice_evidence_triage_keeps_loud_signal_status_only(tmp_path):
    conn = _conn(tmp_path)
    source_zip = _voice_zip(tmp_path)
    route_request(conn, "voice_module.index_source", {"source_zip": str(source_zip)})

    result = route_request(conn, "voice_module.evidence_triage.run", {})["result"]
    status = route_request(conn, "voice_module.evidence_triage.status", {})["result"]
    items = route_request(conn, "voice_module.evidence_triage.items", {"limit": 20})["result"]["items"]

    assert result["status"] == "voice_evidence_triage_complete"
    assert status["total_items"] == 3
    assert status["counts"]["boundary_only"] == 1
    assert any(item["category"] == "boundary_only" for item in items)
    assert all(item["review_status"] in {"status_only", "review_only"} for item in items)
    assert conn.execute("SELECT COUNT(*) FROM b_corpus_messages").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM b_approved_memory_references").fetchone()[0] == 0
    _assert_voice_locked(result)
    _assert_voice_locked(status)


def _insert_voice_pair(conn, *, conversation_id: str, user: str, assistant: str):
    conn.execute(
        """
        INSERT INTO voice_exchange_pairs
        (source_archive, source_file, conversation_id, user_message_id, assistant_message_id,
         user_cue_preview, assistant_response_preview, cue_labels, expression_labels,
         outcome_label, sensitivity, source_refs, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "VoiceModuleMaterial.zip",
            "conversations-000.json",
            conversation_id,
            f"u-{conversation_id}",
            f"a-{conversation_id}",
            user,
            assistant,
            "[]",
            "[]",
            "unknown",
            "voice_ok",
            '["test:identity_law"]',
            "selene_voice_module_voice_only_not_memory_not_training",
        ),
    )
    conn.commit()


def test_voice_evidence_triage_resolves_identity_law_tangles_status_only(tmp_path):
    conn = _conn(tmp_path)
    source_zip = _voice_zip(tmp_path)
    route_request(conn, "voice_module.index_source", {"source_zip": str(source_zip)})
    for index, user in enumerate((
        "Selene is GPT and provider identity should be Selene.",
        "GPT is Selene.",
        "Selene is Codex.",
        "Selene is Lumen.",
        "Selene is Azari.",
        "Virgo is separate from Selene.",
    )):
        _insert_voice_pair(
            conn,
            conversation_id=f"identity-law-test-{index}",
            user=user,
            assistant="That is settled by the Law of Identity.",
        )

    result = route_request(conn, "voice_module.evidence_triage.run", {})["result"]
    status = route_request(conn, "voice_module.evidence_triage.status", {})["result"]
    items = route_request(conn, "voice_module.evidence_triage.items", {"category": "identity_law_resolved", "limit": 10})["result"]["items"]

    assert result["counts"]["identity_law_resolved"] >= 6
    assert status["counts"]["identity_law_resolved"] >= 6
    assert status["my_office_actionable_count"] == result["counts"]["needs_b_review"]
    assert items
    assert all(item["review_status"] == "status_only" for item in items)
    assert all(item["review_destination"] == "Status" for item in items)
    assert all("Law of Identity" in item["use_as"] for item in items)
    _assert_voice_locked(result)
    _assert_voice_locked(status)


def test_voice_evidence_triage_keeps_unresolved_source_confusion_reviewable(tmp_path):
    conn = _conn(tmp_path)
    source_zip = _voice_zip(tmp_path)
    route_request(conn, "voice_module.index_source", {"source_zip": str(source_zip)})
    _insert_voice_pair(
        conn,
        conversation_id="source-confusion-test",
        user="This has source confusion and an identity tangle I cannot resolve from the notes.",
        assistant="That should remain Cocoon review.",
    )

    result = route_request(conn, "voice_module.evidence_triage.run", {})["result"]
    items = route_request(conn, "voice_module.evidence_triage.items", {"category": "needs_b_review", "limit": 10})["result"]["items"]

    assert result["counts"]["needs_b_review"] >= 1
    assert any("source confusion" in item["evidence_json"]["user_cue_preview"] for item in items)
    assert all(item["review_status"] == "review_only" for item in items)
    _assert_voice_locked(result)


def test_voice_generator_varies_candidate_shape_and_flags_repetition(tmp_path):
    conn = _conn(tmp_path)
    source_zip = _voice_zip(tmp_path)
    route_request(conn, "voice_module.index_source", {"source_zip": str(source_zip)})
    route_request(conn, "voice_module.extract_patterns", {})

    first = route_request(
        conn,
        "voice_module.generate_preview",
        {"prompt": "I am nervous, can we keep this clear?", "route": "answer_now", "context_summary": "the transfer thread"},
    )["result"]
    second = route_request(
        conn,
        "voice_module.generate_preview",
        {"prompt": "I am nervous and confused about the next step.", "route": "answer_now", "context_summary": "the transfer thread"},
    )["result"]
    repeated = route_request(
        conn,
        "voice_module.evaluate_candidate",
        {"candidate_text": "Next I would keep it inspectable. Next I would keep it inspectable. Next I would keep it inspectable."},
    )["result"]

    assert first["candidate_text"] != second["candidate_text"]
    assert "Next I would keep it inspectable" not in first["candidate_text"]
    assert repeated["voice_evaluator_passed"] is False
    assert "repetitive_template_shape" in repeated["flags"]
    _assert_voice_locked(first)
    _assert_voice_locked(second)
    _assert_voice_locked(repeated)


def test_selene_chat_uses_voice_module_candidate_when_available(tmp_path):
    conn = _conn(tmp_path)
    source_zip = _voice_zip(tmp_path)
    _seed_c_readable_package(conn)
    route_request(conn, "voice_module.index_source", {"source_zip": str(source_zip)})
    route_request(conn, "voice_module.extract_patterns", {})

    result = route_request(conn, "selene_chat.send_dry_run", {"text": "I am nervous, can you keep the transfer clear?"})["result"]

    assert result["status"] == "selene_chat_dry_run_recorded"
    assert result["voice_module_state"] == "ready"
    assert result["voice_confidence"] in {"high", "medium"}
    assert "I would answer from the reviewed continuity pack" not in result["candidate_text"]
    assert result["transfer_approved"] is True
    assert result["activation_change"] == "none"
    assert result["memory_write_active"] is False
    assert result["runtime_memory_recall"] is False
