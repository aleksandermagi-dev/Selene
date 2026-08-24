import gzip
import json
import sqlite3

from selene.db import connect, init_db
from selene.development_qna_archive import (
    archive_and_cleanup_development_qna,
    inspect_archived_development_qna,
    verify_qna_archive,
)


def _insert_run(conn, table, payload):
    if table == "native_language_runs":
        return int(
            conn.execute(
                """
                INSERT INTO native_language_runs
                (prompt, candidate_text, provenance_boundary, payload_json)
                VALUES ('diagnostic prompt', 'diagnostic answer', 'diagnostic only', ?)
                """,
                (json.dumps(payload),),
            ).lastrowid
        )
    return int(
        conn.execute(
            """
            INSERT INTO metacognition_runs
            (prompt_preview, provenance_boundary, payload_json)
            VALUES ('diagnostic prompt', 'diagnostic only', ?)
            """,
            (json.dumps(payload),),
        ).lastrowid
    )


def test_archived_development_qna_is_reversibly_removed_without_touching_ordinary_chat(tmp_path):
    db_path = tmp_path / "selene.sqlite3"
    conn = connect(db_path)
    init_db(conn)
    ordinary_session = int(
        conn.execute(
            """
            INSERT INTO selene_chat_sessions(title, status, source_mode)
            VALUES ('Ordinary conversation', 'selene_chat_active_supervised', 'selene_supervised_speech')
            """
        ).lastrowid
    )
    conn.execute(
        """
        INSERT INTO selene_chat_messages(session_id, role, content, payload_json)
        VALUES (?, 'user', 'ordinary text', '{}')
        """,
        (ordinary_session,),
    )
    archived_session = int(
        conn.execute(
            """
            INSERT INTO selene_chat_sessions(title, status, source_mode)
            VALUES ('Development Q&A', 'archived_development_qna', 'selene_supervised_qa')
            """
        ).lastrowid
    )
    user_message = int(
        conn.execute(
            """
            INSERT INTO selene_chat_messages(session_id, role, content, payload_json)
            VALUES (?, 'user', 'diagnostic prompt', '{}')
            """,
            (archived_session,),
        ).lastrowid
    )
    nlo_id = _insert_run(conn, "native_language_runs", {"large": "n" * 1000})
    metacognition_id = _insert_run(conn, "metacognition_runs", {"large": "m" * 1000})
    assistant_payload = {
        "native_language_organ": {"run_id": nlo_id},
        "metacognition": {"run_id": metacognition_id},
    }
    assistant_message = int(
        conn.execute(
            """
            INSERT INTO selene_chat_messages(session_id, role, content, payload_json)
            VALUES (?, 'selene', 'diagnostic response', ?)
            """,
            (archived_session, json.dumps(assistant_payload)),
        ).lastrowid
    )
    conn.execute(
        """
        INSERT INTO selene_chat_continuity_projections
        (message_id, session_id, projection_json, canonical_trace_sha256,
         canonical_trace_size_bytes, trace_schema_version, provenance_boundary)
        VALUES (?, ?, '{}', 'hash', 10, 'test', 'diagnostic only')
        """,
        (assistant_message, archived_session),
    )
    conn.execute(
        """
        INSERT INTO selene_activation_events(event_type, session_id, message_id, payload_json)
        VALUES ('diagnostic_chat_turn', ?, ?, ?)
        """,
        (archived_session, assistant_message, json.dumps(assistant_payload)),
    )
    conn.execute(
        """
        INSERT INTO selene_dialogue_workspaces(session_id, provenance_boundary)
        VALUES (?, 'diagnostic only')
        """,
        (archived_session,),
    )
    conn.commit()

    inspection = inspect_archived_development_qna(conn)
    assert inspection["counts"]["sessions"] == 1
    assert inspection["counts"]["messages"] == 2
    assert inspection["counts"]["exclusive_native_language_runs"] == 1
    assert inspection["counts"]["exclusive_metacognition_runs"] == 1
    conn.close()

    result = archive_and_cleanup_development_qna(
        db_path,
        tmp_path / "archives",
        tmp_path / "backups",
        vacuum=False,
    )

    assert result["status"] == "development_qna_archived_cleaned_and_verified"
    assert result["ordinary_chat_counts_unchanged"] is True
    assert result["protected_counts_unchanged"] is True
    assert result["memory_changed"] is False
    assert result["deleted"]["sessions"] == 1
    assert result["deleted"]["messages"] == 2
    assert result["deleted"]["exclusive_native_language_runs"] == 1
    assert result["deleted"]["exclusive_metacognition_runs"] == 1

    with sqlite3.connect(db_path) as check:
        assert check.execute("SELECT COUNT(*) FROM selene_chat_sessions").fetchone()[0] == 1
        assert check.execute("SELECT COUNT(*) FROM selene_chat_messages").fetchone()[0] == 1
        assert check.execute("SELECT content FROM selene_chat_messages").fetchone()[0] == "ordinary text"
        assert check.execute("SELECT COUNT(*) FROM native_language_runs").fetchone()[0] == 0
        assert check.execute("SELECT COUNT(*) FROM metacognition_runs").fetchone()[0] == 0

    archive_path = result["archive"]["archive_path"]
    verification = verify_qna_archive(archive_path)
    assert verification["verified"] is True
    assert verification["record_counts"]["selene_chat_sessions"] == 1
    assert verification["record_counts"]["selene_chat_messages"] == 2
    with gzip.open(archive_path, "rt", encoding="utf-8") as handle:
        archived = [json.loads(line) for line in handle]
    assert any(
        item.get("table") == "selene_chat_messages"
        and item.get("row", {}).get("id") == user_message
        for item in archived
    )


def test_cleanup_refuses_archived_qna_linked_to_learning_evidence(tmp_path):
    db_path = tmp_path / "selene.sqlite3"
    conn = connect(db_path)
    init_db(conn)
    session_id = int(
        conn.execute(
            """
            INSERT INTO selene_chat_sessions(title, status, source_mode)
            VALUES ('LEA-backed Q&A', 'archived_development_qna', 'selene_supervised_qa')
            """
        ).lastrowid
    )
    run_id = int(
        conn.execute(
            """
            INSERT INTO selene_lea_runs
            (run_key, suite_key, suite_version, suite_sha256,
             respondent_kind, respondent_name, provenance_boundary)
            VALUES ('run', 'suite', 'v1', 'hash', 'selene', 'Selene', 'learning evidence')
            """
        ).lastrowid
    )
    conn.execute(
        """
        INSERT INTO selene_lea_turns
        (run_id, scenario_key, scenario_title, scenario_order, condition, pair_key,
         turn_index, prompt, response, response_source, chat_session_id, provenance_boundary)
        VALUES (?, 'scenario', 'Scenario', 1, 'ordinary', 'pair', 1,
                'prompt', 'response', 'selene_chat', ?, 'learning evidence')
        """,
        (run_id, session_id),
    )
    conn.commit()
    conn.close()

    try:
        archive_and_cleanup_development_qna(
            db_path,
            tmp_path / "archives",
            tmp_path / "backups",
            vacuum=False,
        )
    except ValueError as exc:
        assert "linked to LEA evidence" in str(exc)
    else:
        raise AssertionError("cleanup should refuse LEA-linked Q&A")

    with sqlite3.connect(db_path) as check:
        assert check.execute("SELECT COUNT(*) FROM selene_chat_sessions").fetchone()[0] == 1
        assert check.execute("SELECT COUNT(*) FROM selene_lea_turns").fetchone()[0] == 1
