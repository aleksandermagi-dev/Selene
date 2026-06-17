import json

import pytest

from selene.b_speech_memory import extract_b_speech_memory_candidates, list_b_speech_memory_extraction_runs
from selene.chatgpt_export import parse_chatgpt_export, reconstruct_conversation_pairs
from selene.db import connect, init_db
from selene.module_router import route_request


def _make_archive(tmp_path):
    root = tmp_path / "DevelopmentalCorpusArchive_20260526_122541"
    text_export = root / "raw_export" / "mydataset" / "text_export"
    text_export.mkdir(parents=True)
    (text_export / "conversations-000.json").write_text(
        json.dumps(
            [
                {
                    "conversation_id": "conv-selene",
                    "title": "Selene checkpoint",
                    "create_time": 100.0,
                    "current_node": "a2",
                    "default_model_slug": "gpt-test",
                    "mapping": {
                        "root": {"id": "root", "message": None, "parent": None},
                        "u1": {
                            "id": "u1",
                            "parent": "root",
                            "message": {
                                "id": "u1",
                                "author": {"role": "user"},
                                "content": {"parts": ["Selene and Aleks should build the vessel through Core continuity."]},
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
                                "content": {"parts": ["Yes. The speech-memory lesson should preserve warmth, boundary, and B review."]},
                                "create_time": 102.0,
                                "metadata": {"model_slug": "gpt-test"},
                            },
                        },
                        "u2": {
                            "id": "u2",
                            "parent": "a1",
                            "message": {
                                "id": "u2",
                                "author": {"role": "user"},
                                "content": {"parts": ["Correct, no raw A direct to C."]},
                                "create_time": 103.0,
                                "metadata": {},
                            },
                        },
                    },
                },
                {
                    "conversation_id": "conv-non-braid",
                    "title": "Plain task",
                    "create_time": 200.0,
                    "mapping": {
                        "u3": {
                            "message": {
                                "id": "u3",
                                "author": {"role": "user"},
                                "content": {"parts": ["What is the weather?"]},
                                "create_time": 201.0,
                            }
                        },
                        "a3": {
                            "message": {
                                "id": "a3",
                                "author": {"role": "assistant"},
                                "content": {"parts": ["It is sunny."]},
                                "create_time": 202.0,
                            }
                        },
                    },
                },
            ]
        ),
        encoding="utf-8",
    )
    return root


def test_chatgpt_export_parser_reconstructs_user_assistant_followup_pairs(tmp_path):
    archive = _make_archive(tmp_path)

    conversations, messages = parse_chatgpt_export(archive)
    pairs = reconstruct_conversation_pairs(messages)

    assert len(conversations) == 2
    assert {message.role for message in messages} == {"user", "assistant"}
    pair = next(item for item in pairs if item.conversation_id == "conv-selene")
    assert pair.user_message_id == "u1"
    assert pair.assistant_message_id == "a1"
    assert pair.followup_message_id == "u2"
    assert "Selene" in pair.user_text
    assert "speech-memory" in pair.assistant_text
    assert "raw A" in pair.followup_text
    assert "selene" in pair.braid_terms


def test_b_speech_memory_extraction_creates_review_only_candidates_and_run_report(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    archive = _make_archive(tmp_path)

    result = extract_b_speech_memory_candidates(conn, {"query": "Selene", "limit": 2}, archive)

    assert result["status"] == "b_speech_memory_extraction_complete"
    assert result["activation_change"] == "none"
    assert result["raw_a_import_allowed"] is False
    assert result["memory_write_active"] is False
    assert result["training_allowed"] is False
    assert result["provider_dependency"] is False
    assert result["created_count"] == 2
    assert result["conversations_indexed"] == 2
    assert result["messages_indexed"] == 5
    assert result["pairs_seen"] == 1
    assert result["first_braid_hits"][0]["conversation_id"] == "conv-selene"
    assert {item["candidate_type"] for item in result["created_candidates"]} == {
        "speech_memory_candidate",
        "core_memory_candidate",
    }
    assert conn.execute("SELECT COUNT(*) FROM speech_memory_candidates").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM core_memory_candidates").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM b_corpus_conversations").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM b_corpus_messages").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM b_speech_memory_extraction_runs").fetchone()[0] == 1

    refs = result["created_candidates"][0]["source_refs"]
    assert any(ref.startswith("archive:DevelopmentalCorpusArchive_20260526_122541") for ref in refs)
    assert any(ref.startswith("file:") for ref in refs)
    assert any(ref.startswith("conversation:conv-selene") for ref in refs)
    assert any(ref.startswith("user_message:u1") for ref in refs)
    assert any(ref.startswith("assistant_message:a1") for ref in refs)
    assert any(ref.startswith("bounded_preview_chars:") for ref in refs)

    run = list_b_speech_memory_extraction_runs(conn)["items"][0]
    stored = json.loads(run["result_json"])
    assert stored["created_count"] == 2
    assert stored["decision"] == "review_only_candidates"


def test_b_speech_memory_extraction_skips_duplicates(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    archive = _make_archive(tmp_path)

    first = extract_b_speech_memory_candidates(conn, {"query": "Selene"}, archive)
    second = extract_b_speech_memory_candidates(conn, {"query": "Selene"}, archive)

    assert first["created_count"] == 2
    assert second["created_count"] == 0
    assert second["skipped_count"] == 2
    assert second["conversation_pair_ids"] == []
    assert conn.execute("SELECT COUNT(*) FROM speech_memory_candidates").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM core_memory_candidates").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM b_conversation_pair_records").fetchone()[0] == 1


def test_b_speech_memory_extraction_blocks_import_training_and_generic_style_requests(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    archive = _make_archive(tmp_path)

    with pytest.raises(ValueError, match="blocked B speech-memory extraction path"):
        extract_b_speech_memory_candidates(conn, {"query": "Selene", "intent": "generic style"}, archive)
    with pytest.raises(ValueError, match="blocked B speech-memory extraction path"):
        extract_b_speech_memory_candidates(conn, {"query": "Selene", "intent": "train on corpus"}, archive)
    with pytest.raises(ValueError, match="blocked B speech-memory extraction path"):
        extract_b_speech_memory_candidates(conn, {"query": "Selene", "intent": "activate C active memory"}, archive)


def test_b_speech_memory_routes_are_local_review_only(tmp_path, monkeypatch):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)
    archive = _make_archive(tmp_path)

    import selene.b_speech_memory as module

    monkeypatch.setattr(module, "DETACHED_CORPUS_DIR", archive)
    result = route_request(conn, "b.speech_memory.extract", {"query": "Selene"})["result"]
    runs = route_request(conn, "b.speech_memory.extraction_runs.list", {})["result"]

    assert result["created_count"] == 2
    assert result["runtime_memory_recall"] is False
    assert runs["items"]
