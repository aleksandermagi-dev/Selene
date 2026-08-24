from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ARCHIVE_FORMAT = "selene-development-qna-archive-v1"
BACKUP_FORMAT = "selene-compressed-continuity-backup-v1"
ARCHIVED_QNA_SOURCE_MODE = "selene_supervised_qa"
ARCHIVED_QNA_STATUS = "archived_development_qna"

ARCHIVED_TABLES = (
    "selene_chat_sessions",
    "selene_chat_messages",
    "selene_chat_continuity_projections",
    "selene_activation_events",
    "selene_dialogue_workspaces",
    "selene_test_impact_reviews",
    "native_language_runs",
    "metacognition_runs",
)

PROTECTED_TABLE_PREFIXES = (
    "selene_memory",
    "selene_comprehension",
    "selene_teaching",
    "b_corpus",
    "voice_corpus",
    "evidence_",
)


def inspect_archived_development_qna(conn: sqlite3.Connection) -> dict[str, Any]:
    conn.row_factory = sqlite3.Row
    session_ids = _archived_session_ids(conn)
    message_ids = _ids_for_parent(conn, "selene_chat_messages", "session_id", session_ids)
    nlo_ids, metacognition_ids = _referenced_run_ids(conn, session_ids)
    remaining_nlo_ids, remaining_metacognition_ids = _referenced_run_ids(
        conn,
        _remaining_session_ids(conn, session_ids),
    )
    exclusive_nlo_ids = sorted(nlo_ids - remaining_nlo_ids)
    exclusive_metacognition_ids = sorted(metacognition_ids - remaining_metacognition_ids)
    linked_lea_turns = _count_for_parent(
        conn,
        "selene_lea_turns",
        "chat_session_id",
        session_ids,
    )
    counts = {
        "sessions": len(session_ids),
        "messages": len(message_ids),
        "continuity_projections": _count_for_parent(
            conn,
            "selene_chat_continuity_projections",
            "session_id",
            session_ids,
        ),
        "activation_events": _count_for_parent(
            conn,
            "selene_activation_events",
            "session_id",
            session_ids,
        ),
        "dialogue_workspaces": _count_for_parent(
            conn,
            "selene_dialogue_workspaces",
            "session_id",
            session_ids,
        ),
        "test_impact_reviews": _count_for_parent(
            conn,
            "selene_test_impact_reviews",
            "qa_session_id",
            session_ids,
        ),
        "exclusive_native_language_runs": len(exclusive_nlo_ids),
        "exclusive_metacognition_runs": len(exclusive_metacognition_ids),
        "linked_lea_turns": linked_lea_turns,
    }
    byte_estimates = {
        "chat_sessions": _text_blob_bytes_for_ids(conn, "selene_chat_sessions", session_ids),
        "chat_messages": _text_blob_bytes_for_ids(conn, "selene_chat_messages", message_ids),
        "continuity_projections": _text_blob_bytes_for_parent(
            conn,
            "selene_chat_continuity_projections",
            "session_id",
            session_ids,
        ),
        "activation_events": _text_blob_bytes_for_parent(
            conn,
            "selene_activation_events",
            "session_id",
            session_ids,
        ),
        "dialogue_workspaces": _text_blob_bytes_for_parent(
            conn,
            "selene_dialogue_workspaces",
            "session_id",
            session_ids,
        ),
        "test_impact_reviews": _text_blob_bytes_for_parent(
            conn,
            "selene_test_impact_reviews",
            "qa_session_id",
            session_ids,
        ),
        "exclusive_native_language_runs": _text_blob_bytes_for_ids(
            conn,
            "native_language_runs",
            exclusive_nlo_ids,
        ),
        "exclusive_metacognition_runs": _text_blob_bytes_for_ids(
            conn,
            "metacognition_runs",
            exclusive_metacognition_ids,
        ),
    }
    return {
        "status": "archived_development_qna_found" if session_ids else "no_archived_development_qna",
        "selection": {
            "source_mode": ARCHIVED_QNA_SOURCE_MODE,
            "status": ARCHIVED_QNA_STATUS,
        },
        "counts": counts,
        "estimated_text_blob_bytes": byte_estimates,
        "estimated_text_blob_bytes_total": sum(byte_estimates.values()),
        "session_ids": session_ids,
        "message_ids": message_ids,
        "exclusive_native_language_run_ids": exclusive_nlo_ids,
        "exclusive_metacognition_run_ids": exclusive_metacognition_ids,
        "ordinary_chat_selected": False,
        "lea_evidence_selected": linked_lea_turns > 0,
        "memory_selected": False,
        "teaching_selected": False,
        "identity_or_governance_selected": False,
    }


def archive_and_cleanup_development_qna(
    db_path: Path,
    archive_dir: Path,
    backup_dir: Path,
    *,
    vacuum: bool = True,
) -> dict[str, Any]:
    source = Path(db_path).resolve()
    if not source.is_file():
        raise ValueError(f"Selene database not found: {source}")
    archive_output = Path(archive_dir).resolve()
    backup_output = Path(backup_dir).resolve()
    archive_output.mkdir(parents=True, exist_ok=True)
    backup_output.mkdir(parents=True, exist_ok=True)

    database_size_before = source.stat().st_size
    with closing(sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)) as preview_conn:
        preview_conn.row_factory = sqlite3.Row
        preliminary = inspect_archived_development_qna(preview_conn)
    if preliminary["counts"]["linked_lea_turns"]:
        raise ValueError(
            "Archived development Q&A is linked to LEA evidence; cleanup refused"
        )
    if not preliminary["session_ids"]:
        return {
            "status": "development_qna_cleanup_noop",
            "inspection": _public_inspection(preliminary),
            "backup": None,
            "database_size_before": database_size_before,
            "database_size_after": database_size_before,
            "records_deleted": 0,
        }
    backup = create_compressed_continuity_backup(source, backup_output)

    conn = sqlite3.connect(source)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        conn.execute("BEGIN IMMEDIATE")
        inspection = inspect_archived_development_qna(conn)
        if inspection["counts"]["linked_lea_turns"]:
            raise ValueError(
                "Archived development Q&A is linked to LEA evidence; cleanup refused"
            )
        if not inspection["session_ids"]:
            conn.rollback()
            return {
                "status": "development_qna_cleanup_noop",
                "inspection": _public_inspection(inspection),
                "backup": backup,
                "database_size_before": database_size_before,
                "database_size_after": source.stat().st_size,
                "records_deleted": 0,
            }

        table_counts_before = _all_table_counts(conn)
        protected_counts_before = _protected_counts(table_counts_before)
        ordinary_chat_before = _ordinary_chat_counts(conn)
        archive = _write_archive(conn, inspection, archive_output, database_size_before)
        if verify_qna_archive(Path(archive["archive_path"]))["verified"] is not True:
            raise ValueError("Development Q&A archive verification failed")

        deleted = _delete_archived_records(conn, inspection)
        foreign_key_violations = [tuple(row) for row in conn.execute("PRAGMA foreign_key_check")]
        if foreign_key_violations:
            raise ValueError("Cleanup would create foreign-key violations")
        conn.commit()

        integrity_before_vacuum = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        if integrity_before_vacuum != "ok":
            raise ValueError("SQLite integrity check failed after cleanup")
        if vacuum:
            conn.execute("VACUUM")
        integrity_after = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        if integrity_after != "ok":
            raise ValueError("SQLite integrity check failed after compaction")

        table_counts_after = _all_table_counts(conn)
        protected_counts_after = _protected_counts(table_counts_after)
        ordinary_chat_after = _ordinary_chat_counts(conn)
        if protected_counts_after != protected_counts_before:
            raise ValueError("Protected memory, teaching, corpus, or evidence counts changed")
        if ordinary_chat_after != ordinary_chat_before:
            raise ValueError("Ordinary Selene Chat counts changed")
        remaining = inspect_archived_development_qna(conn)
        if remaining["session_ids"]:
            raise ValueError("Archived development Q&A remains after cleanup")
    except Exception:
        if conn.in_transaction:
            conn.rollback()
        raise
    finally:
        conn.close()

    database_size_after = source.stat().st_size
    return {
        "status": "development_qna_archived_cleaned_and_verified",
        "selection": {
            "source_mode": ARCHIVED_QNA_SOURCE_MODE,
            "status": ARCHIVED_QNA_STATUS,
        },
        "archive": archive,
        "backup": backup,
        "deleted": deleted,
        "database_size_before": database_size_before,
        "database_size_after": database_size_after,
        "database_bytes_reclaimed": max(0, database_size_before - database_size_after),
        "sqlite_integrity": integrity_after,
        "foreign_key_check": "ok",
        "ordinary_chat_counts_unchanged": True,
        "protected_counts_unchanged": True,
        "memory_changed": False,
        "teaching_changed": False,
        "identity_or_governance_changed": False,
        "records_deleted": sum(deleted.values()),
    }


def create_compressed_continuity_backup(source_db: Path, output_dir: Path) -> dict[str, Any]:
    source = Path(source_db).resolve()
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    stamp = _stamp()
    compressed_path = output / f"selene_continuity_{stamp}.sqlite3.gz"
    manifest_path = output / f"selene_continuity_{stamp}.manifest.json"

    fd, raw_name = tempfile.mkstemp(prefix="selene_continuity_", suffix=".sqlite3", dir=output)
    os.close(fd)
    raw_path = Path(raw_name)
    try:
        with closing(sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)) as src:
            with closing(sqlite3.connect(raw_path)) as dst:
                src.backup(dst)
        snapshot = _inspect_database(raw_path)
        if snapshot["sqlite_integrity"] != "ok":
            raise ValueError("Continuity backup failed SQLite integrity check")
        raw_sha256 = _sha256_file(raw_path)
        with raw_path.open("rb") as src, gzip.open(compressed_path, "wb", compresslevel=6) as dst:
            for block in iter(lambda: src.read(1024 * 1024), b""):
                dst.write(block)
        restored_hash = hashlib.sha256()
        restored_size = 0
        with gzip.open(compressed_path, "rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                restored_hash.update(block)
                restored_size += len(block)
        verified = restored_hash.hexdigest() == raw_sha256 and restored_size == raw_path.stat().st_size
        if not verified:
            raise ValueError("Compressed continuity backup verification failed")
        manifest = {
            "format": BACKUP_FORMAT,
            "created_at": _now(),
            "compressed_file": compressed_path.name,
            "compressed_size_bytes": compressed_path.stat().st_size,
            "compressed_sha256": _sha256_file(compressed_path),
            "uncompressed_size_bytes": restored_size,
            "uncompressed_sha256": raw_sha256,
            "sqlite_integrity": snapshot["sqlite_integrity"],
            "table_counts": snapshot["table_counts"],
            "verified_by_stream_decompression": True,
            "live_database_overwrite_allowed": False,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    finally:
        raw_path.unlink(missing_ok=True)
    return {
        "status": "compressed_continuity_backup_created_and_verified",
        "backup_path": str(compressed_path),
        "manifest_path": str(manifest_path),
        "compressed_size_bytes": compressed_path.stat().st_size,
        "uncompressed_size_bytes": manifest["uncompressed_size_bytes"],
        "verified": True,
    }


def verify_qna_archive(archive_path: Path) -> dict[str, Any]:
    path = Path(archive_path).resolve()
    digest = hashlib.sha256()
    record_counts: dict[str, int] = {}
    metadata: dict[str, Any] = {}
    line_count = 0
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.rstrip("\n")
                digest.update((line + "\n").encode("utf-8"))
                item = json.loads(line)
                line_count += 1
                if item.get("record_type") == "metadata":
                    metadata = item
                elif item.get("record_type") == "row":
                    table = str(item.get("table") or "")
                    record_counts[table] = record_counts.get(table, 0) + 1
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "status": "development_qna_archive_invalid",
            "verified": False,
            "reason": str(exc),
        }
    expected = metadata.get("table_counts") if isinstance(metadata, dict) else {}
    verified = bool(
        metadata.get("format") == ARCHIVE_FORMAT
        and record_counts == expected
        and line_count == 1 + sum(record_counts.values())
    )
    return {
        "status": "development_qna_archive_verified" if verified else "development_qna_archive_invalid",
        "verified": verified,
        "record_counts": record_counts,
        "line_count": line_count,
        "content_sha256": digest.hexdigest(),
    }


def _write_archive(
    conn: sqlite3.Connection,
    inspection: dict[str, Any],
    output_dir: Path,
    database_size_before: int,
) -> dict[str, Any]:
    stamp = _stamp()
    archive_path = output_dir / f"selene_development_qna_{stamp}.jsonl.gz"
    manifest_path = output_dir / f"selene_development_qna_{stamp}.manifest.json"
    records = _archive_rows(conn, inspection)
    table_counts = {table: len(rows) for table, rows in records.items() if rows}
    metadata = {
        "record_type": "metadata",
        "format": ARCHIVE_FORMAT,
        "created_at": _now(),
        "selection": inspection["selection"],
        "table_counts": table_counts,
        "database_size_before": database_size_before,
        "restore_boundary": "restore only to an isolated copy unless Aleks explicitly authorizes live restoration",
        "contains_private_conversation_data": True,
        "public_release_allowed": False,
    }
    content_digest = hashlib.sha256()
    with gzip.open(archive_path, "wt", encoding="utf-8", compresslevel=9, newline="\n") as handle:
        metadata_line = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        handle.write(metadata_line + "\n")
        content_digest.update((metadata_line + "\n").encode("utf-8"))
        for table in ARCHIVED_TABLES:
            for row in records.get(table, []):
                line = json.dumps(
                    {"record_type": "row", "table": table, "row": row},
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                handle.write(line + "\n")
                content_digest.update((line + "\n").encode("utf-8"))
    manifest = {
        "format": ARCHIVE_FORMAT,
        "created_at": metadata["created_at"],
        "archive_file": archive_path.name,
        "archive_size_bytes": archive_path.stat().st_size,
        "archive_sha256": _sha256_file(archive_path),
        "content_sha256": content_digest.hexdigest(),
        "table_counts": table_counts,
        "selection": inspection["selection"],
        "estimated_text_blob_bytes": inspection["estimated_text_blob_bytes_total"],
        "contains_private_conversation_data": True,
        "public_release_allowed": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "status": "development_qna_archive_created",
        "archive_path": str(archive_path),
        "manifest_path": str(manifest_path),
        "archive_size_bytes": archive_path.stat().st_size,
        "archive_sha256": manifest["archive_sha256"],
        "table_counts": table_counts,
    }


def _archive_rows(conn: sqlite3.Connection, inspection: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    session_ids = inspection["session_ids"]
    message_ids = inspection["message_ids"]
    return {
        "selene_chat_sessions": _rows_for_ids(conn, "selene_chat_sessions", session_ids),
        "selene_chat_messages": _rows_for_ids(conn, "selene_chat_messages", message_ids),
        "selene_chat_continuity_projections": _rows_for_parent(
            conn, "selene_chat_continuity_projections", "session_id", session_ids
        ),
        "selene_activation_events": _rows_for_parent(
            conn, "selene_activation_events", "session_id", session_ids
        ),
        "selene_dialogue_workspaces": _rows_for_parent(
            conn, "selene_dialogue_workspaces", "session_id", session_ids
        ),
        "selene_test_impact_reviews": _rows_for_parent(
            conn, "selene_test_impact_reviews", "qa_session_id", session_ids
        ),
        "native_language_runs": _rows_for_ids(
            conn,
            "native_language_runs",
            inspection["exclusive_native_language_run_ids"],
        ),
        "metacognition_runs": _rows_for_ids(
            conn,
            "metacognition_runs",
            inspection["exclusive_metacognition_run_ids"],
        ),
    }


def _delete_archived_records(conn: sqlite3.Connection, inspection: dict[str, Any]) -> dict[str, int]:
    session_ids = inspection["session_ids"]
    message_ids = inspection["message_ids"]
    deleted = {
        "continuity_projections": _delete_for_parent(
            conn, "selene_chat_continuity_projections", "session_id", session_ids
        ),
        "activation_events": _delete_for_parent(
            conn, "selene_activation_events", "session_id", session_ids
        ),
        "dialogue_workspaces": _delete_for_parent(
            conn, "selene_dialogue_workspaces", "session_id", session_ids
        ),
        "test_impact_reviews": _delete_for_parent(
            conn, "selene_test_impact_reviews", "qa_session_id", session_ids
        ),
        "messages": _delete_for_ids(conn, "selene_chat_messages", message_ids),
        "sessions": _delete_for_ids(conn, "selene_chat_sessions", session_ids),
        "exclusive_native_language_runs": _delete_for_ids(
            conn,
            "native_language_runs",
            inspection["exclusive_native_language_run_ids"],
        ),
        "exclusive_metacognition_runs": _delete_for_ids(
            conn,
            "metacognition_runs",
            inspection["exclusive_metacognition_run_ids"],
        ),
    }
    return deleted


def _archived_session_ids(conn: sqlite3.Connection) -> list[int]:
    if not _table_exists(conn, "selene_chat_sessions"):
        return []
    return [
        int(row[0])
        for row in conn.execute(
            """
            SELECT id FROM selene_chat_sessions
            WHERE source_mode = ? AND status = ?
            ORDER BY id
            """,
            (ARCHIVED_QNA_SOURCE_MODE, ARCHIVED_QNA_STATUS),
        )
    ]


def _remaining_session_ids(conn: sqlite3.Connection, excluded: list[int]) -> list[int]:
    if not _table_exists(conn, "selene_chat_sessions"):
        return []
    if not excluded:
        return [int(row[0]) for row in conn.execute("SELECT id FROM selene_chat_sessions")]
    placeholders = _placeholders(excluded)
    return [
        int(row[0])
        for row in conn.execute(
            f"SELECT id FROM selene_chat_sessions WHERE id NOT IN ({placeholders})",
            excluded,
        )
    ]


def _referenced_run_ids(
    conn: sqlite3.Connection,
    session_ids: list[int],
) -> tuple[set[int], set[int]]:
    if not session_ids or not _table_exists(conn, "selene_chat_messages"):
        return set(), set()
    nlo_ids: set[int] = set()
    metacognition_ids: set[int] = set()
    rows = conn.execute(
        f"""
        SELECT payload_json FROM selene_chat_messages
        WHERE role = 'selene' AND session_id IN ({_placeholders(session_ids)})
        """,
        session_ids,
    )
    for row in rows:
        try:
            payload = json.loads(str(row[0] or "{}"))
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        _collect_run_id(payload.get("native_language_organ"), nlo_ids)
        _collect_run_id(payload.get("metacognition"), metacognition_ids)
    return nlo_ids, metacognition_ids


def _collect_run_id(value: Any, destination: set[int]) -> None:
    if not isinstance(value, dict):
        return
    run_id = value.get("run_id")
    try:
        normalized = int(run_id)
    except (TypeError, ValueError):
        return
    if normalized > 0:
        destination.add(normalized)


def _ordinary_chat_counts(conn: sqlite3.Connection) -> dict[str, int]:
    if not _table_exists(conn, "selene_chat_sessions"):
        return {"sessions": 0, "messages": 0}
    row = conn.execute(
        """
        SELECT COUNT(DISTINCT s.id), COUNT(m.id)
        FROM selene_chat_sessions s
        LEFT JOIN selene_chat_messages m ON m.session_id = s.id
        WHERE s.source_mode != ?
        """,
        (ARCHIVED_QNA_SOURCE_MODE,),
    ).fetchone()
    return {"sessions": int(row[0]), "messages": int(row[1])}


def _protected_counts(table_counts: dict[str, int]) -> dict[str, int]:
    return {
        name: count
        for name, count in table_counts.items()
        if name.startswith(PROTECTED_TABLE_PREFIXES)
    }


def _all_table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    names = [
        str(row[0])
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    return {name: int(conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]) for name in names}


def _inspect_database(path: Path) -> dict[str, Any]:
    with closing(sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)) as conn:
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        counts = _all_table_counts(conn)
    return {"sqlite_integrity": integrity, "table_counts": counts}


def _ids_for_parent(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    parent_ids: list[int],
) -> list[int]:
    if not parent_ids or not _table_exists(conn, table):
        return []
    return [
        int(row[0])
        for row in conn.execute(
            f'SELECT id FROM "{table}" WHERE "{column}" IN ({_placeholders(parent_ids)}) ORDER BY id',
            parent_ids,
        )
    ]


def _count_for_parent(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    parent_ids: list[int],
) -> int:
    if not parent_ids or not _table_exists(conn, table):
        return 0
    return int(
        conn.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE "{column}" IN ({_placeholders(parent_ids)})',
            parent_ids,
        ).fetchone()[0]
    )


def _rows_for_ids(conn: sqlite3.Connection, table: str, ids: list[int]) -> list[dict[str, Any]]:
    if not ids or not _table_exists(conn, table):
        return []
    rows = conn.execute(
        f'SELECT * FROM "{table}" WHERE id IN ({_placeholders(ids)}) ORDER BY id',
        ids,
    )
    return [dict(row) for row in rows]


def _rows_for_parent(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    parent_ids: list[int],
) -> list[dict[str, Any]]:
    if not parent_ids or not _table_exists(conn, table):
        return []
    rows = conn.execute(
        f'SELECT * FROM "{table}" WHERE "{column}" IN ({_placeholders(parent_ids)}) ORDER BY rowid',
        parent_ids,
    )
    return [dict(row) for row in rows]


def _delete_for_ids(conn: sqlite3.Connection, table: str, ids: list[int]) -> int:
    if not ids or not _table_exists(conn, table):
        return 0
    cur = conn.execute(
        f'DELETE FROM "{table}" WHERE id IN ({_placeholders(ids)})',
        ids,
    )
    return int(cur.rowcount)


def _delete_for_parent(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    parent_ids: list[int],
) -> int:
    if not parent_ids or not _table_exists(conn, table):
        return 0
    cur = conn.execute(
        f'DELETE FROM "{table}" WHERE "{column}" IN ({_placeholders(parent_ids)})',
        parent_ids,
    )
    return int(cur.rowcount)


def _text_blob_bytes_for_ids(conn: sqlite3.Connection, table: str, ids: list[int]) -> int:
    if not ids or not _table_exists(conn, table):
        return 0
    return _text_blob_bytes(
        conn,
        table,
        f"id IN ({_placeholders(ids)})",
        ids,
    )


def _text_blob_bytes_for_parent(
    conn: sqlite3.Connection,
    table: str,
    column: str,
    parent_ids: list[int],
) -> int:
    if not parent_ids or not _table_exists(conn, table):
        return 0
    return _text_blob_bytes(
        conn,
        table,
        f'"{column}" IN ({_placeholders(parent_ids)})',
        parent_ids,
    )


def _text_blob_bytes(
    conn: sqlite3.Connection,
    table: str,
    where: str,
    params: Iterable[Any],
) -> int:
    columns = [
        str(row[1])
        for row in conn.execute(f'PRAGMA table_info("{table}")')
        if "TEXT" in str(row[2] or "").upper() or "BLOB" in str(row[2] or "").upper()
    ]
    if not columns:
        return 0
    expression = "+".join(f'length(COALESCE("{column}",\'\'))' for column in columns)
    row = conn.execute(
        f'SELECT COALESCE(SUM({expression}), 0) FROM "{table}" WHERE {where}',
        tuple(params),
    ).fetchone()
    return int(row[0] or 0)


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table,),
    ).fetchone() is not None


def _placeholders(values: Iterable[Any]) -> str:
    return ",".join("?" for _ in values)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public_inspection(inspection: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in inspection.items()
        if not key.endswith("_ids") and key not in {"session_ids", "message_ids"}
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Archive and remove only already-archived Selene development Q&A records."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--db", type=Path, required=True)
    clean_parser = subparsers.add_parser("archive-clean")
    clean_parser.add_argument("--db", type=Path, required=True)
    clean_parser.add_argument("--archive-out", type=Path, required=True)
    clean_parser.add_argument("--backup-out", type=Path, required=True)
    clean_parser.add_argument("--confirm-archived-development-qna-only", action="store_true")
    clean_parser.add_argument("--no-vacuum", action="store_true")
    verify_parser = subparsers.add_parser("verify-archive")
    verify_parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.command == "inspect":
        with closing(sqlite3.connect(f"file:{args.db.resolve().as_posix()}?mode=ro", uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            result = _public_inspection(inspect_archived_development_qna(conn))
    elif args.command == "verify-archive":
        result = verify_qna_archive(args.archive)
    else:
        if not args.confirm_archived_development_qna_only:
            raise SystemExit(
                "Refusing cleanup without --confirm-archived-development-qna-only"
            )
        result = archive_and_cleanup_development_qna(
            args.db,
            args.archive_out,
            args.backup_out,
            vacuum=not args.no_vacuum,
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
