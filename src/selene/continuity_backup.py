from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BACKUP_FORMAT = "selene-continuity-backup-v1"
CRITICAL_TABLES = (
    "selene_activation_audit",
    "selene_chat_sessions",
    "selene_chat_messages",
    "selene_memory_candidates",
    "selene_comprehension_concepts",
    "selene_teaching_lifecycles",
    "selene_dream_cycles",
    "selene_dream_reflections",
)


def create_integrity_backup(source_db: Path, output_dir: Path) -> dict[str, Any]:
    source = source_db.resolve()
    output = output_dir.resolve()
    if not source.is_file():
        raise ValueError(f"Selene database not found: {source}")
    output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    snapshot = output / f"selene_continuity_{stamp}.sqlite3"
    manifest_path = output / f"selene_continuity_{stamp}.manifest.json"

    with sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True) as src:
        with sqlite3.connect(snapshot) as dst:
            src.backup(dst)
    verification = _inspect_snapshot(snapshot)
    manifest = {
        "format": BACKUP_FORMAT,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_file": snapshot.name,
        "snapshot_size_bytes": snapshot.stat().st_size,
        "snapshot_sha256": _sha256(snapshot),
        "sqlite_integrity": verification["sqlite_integrity"],
        "schema_version": verification["schema_version"],
        "critical_table_counts": verification["critical_table_counts"],
        "encrypted": False,
        "encryption_boundary": (
            "Integrity is verified here; encrypted off-device custody requires an "
            "OS-backed key and Aleks-held recovery method and is not claimed."
        ),
        "live_database_overwrite_allowed": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "status": "continuity_backup_created_and_verified",
        "snapshot_path": str(snapshot),
        "manifest_path": str(manifest_path),
        "manifest": manifest,
    }


def verify_integrity_backup(snapshot_path: Path, manifest_path: Path) -> dict[str, Any]:
    snapshot = Path(snapshot_path).resolve()
    manifest = json.loads(Path(manifest_path).resolve().read_text(encoding="utf-8"))
    inspected = _inspect_snapshot(snapshot)
    hash_matches = _sha256(snapshot) == str(manifest.get("snapshot_sha256") or "")
    counts_match = inspected["critical_table_counts"] == manifest.get("critical_table_counts")
    verified = bool(
        manifest.get("format") == BACKUP_FORMAT
        and hash_matches
        and counts_match
        and inspected["sqlite_integrity"] == "ok"
    )
    return {
        "status": "continuity_backup_verified" if verified else "continuity_backup_invalid",
        "verified": verified,
        "hash_matches": hash_matches,
        "critical_table_counts_match": counts_match,
        **inspected,
        "live_database_mutated": False,
    }


def restore_to_isolated_copy(
    snapshot_path: Path,
    manifest_path: Path,
    target_path: Path,
) -> dict[str, Any]:
    verification = verify_integrity_backup(snapshot_path, manifest_path)
    if verification["verified"] is not True:
        raise ValueError("continuity backup failed integrity verification")
    snapshot = Path(snapshot_path).resolve()
    target = Path(target_path).resolve()
    if target.exists():
        raise ValueError("isolated restore target already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"file:{snapshot.as_posix()}?mode=ro", uri=True) as src:
        with sqlite3.connect(target) as dst:
            src.backup(dst)
    restored = _inspect_snapshot(target)
    return {
        "status": "continuity_backup_restored_to_isolated_copy",
        "target_path": str(target),
        "sqlite_integrity": restored["sqlite_integrity"],
        "critical_table_counts_match": (
            restored["critical_table_counts"]
            == verification["critical_table_counts"]
        ),
        "live_database_overwritten": False,
    }


def _inspect_snapshot(path: Path) -> dict[str, Any]:
    with sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True) as conn:
        integrity = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
        schema_version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        available = {
            str(row[0])
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        counts = {
            table: int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
            for table in CRITICAL_TABLES
            if table in available
        }
    return {
        "sqlite_integrity": integrity,
        "schema_version": schema_version,
        "critical_table_counts": counts,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create or verify a bounded Selene continuity backup.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--db", type=Path, required=True)
    create.add_argument("--out", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--snapshot", type=Path, required=True)
    verify.add_argument("--manifest", type=Path, required=True)
    restore = subparsers.add_parser("restore-isolated")
    restore.add_argument("--snapshot", type=Path, required=True)
    restore.add_argument("--manifest", type=Path, required=True)
    restore.add_argument("--target", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "create":
        result = create_integrity_backup(args.db, args.out)
    elif args.command == "verify":
        result = verify_integrity_backup(args.snapshot, args.manifest)
    else:
        result = restore_to_isolated_copy(args.snapshot, args.manifest, args.target)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
