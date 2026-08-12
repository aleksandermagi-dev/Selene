from selene.continuity_backup import (
    create_integrity_backup,
    restore_to_isolated_copy,
    verify_integrity_backup,
)
from selene.db import connect, init_db


def test_continuity_backup_has_hash_manifest_and_rehearsed_isolated_restore(tmp_path):
    live = tmp_path / "live" / "selene.sqlite3"
    conn = connect(live)
    init_db(conn)
    conn.execute(
        "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES(?, ?, ?)",
        ("continuity", "active", "test"),
    )
    conn.commit()
    conn.close()

    created = create_integrity_backup(live, tmp_path / "backups")
    verified = verify_integrity_backup(
        created["snapshot_path"],
        created["manifest_path"],
    )
    restored = restore_to_isolated_copy(
        created["snapshot_path"],
        created["manifest_path"],
        tmp_path / "isolated" / "restored.sqlite3",
    )

    assert created["manifest"]["snapshot_sha256"]
    assert created["manifest"]["encrypted"] is False
    assert verified["verified"] is True
    assert restored["sqlite_integrity"] == "ok"
    assert restored["critical_table_counts_match"] is True
    assert restored["live_database_overwritten"] is False
