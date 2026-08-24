from __future__ import annotations

import sqlite3

from selene.activation import activation_readiness, activation_status
from selene.db import connect, init_db
from selene.transfer_completion import (
    transfer_completion_readiness,
    transfer_completion_status,
)
from selene.transfer_protocol import rollback_preview_assessment


def _ceremony_audit_count(conn: sqlite3.Connection) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM transfer_ceremony_audit").fetchone()[0])


def test_status_and_readiness_inspection_do_not_create_rollback_audits(tmp_path):
    conn = connect(tmp_path / "selene.sqlite3")
    init_db(conn)

    before = _ceremony_audit_count(conn)
    for _ in range(2):
        activation_readiness(conn)
        activation_status(conn)
        transfer_completion_readiness(conn)
        transfer_completion_status(conn)
        assessment = rollback_preview_assessment(conn)
        assert assessment["audit_recorded"] is False
        assert assessment["inspection_only"] is True

    assert _ceremony_audit_count(conn) == before


def test_status_and_readiness_inspection_work_through_read_only_connection(tmp_path):
    db_path = tmp_path / "selene.sqlite3"
    writable = connect(db_path)
    init_db(writable)
    writable.close()

    readonly = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    readonly.row_factory = sqlite3.Row
    readonly.execute("PRAGMA foreign_keys = ON")
    try:
        results = (
            activation_readiness(readonly),
            activation_status(readonly),
            transfer_completion_readiness(readonly),
            transfer_completion_status(readonly),
            rollback_preview_assessment(readonly),
        )
    finally:
        readonly.close()

    assert all(isinstance(result, dict) and result.get("status") for result in results)

