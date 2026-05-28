from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_items (
  id TEXT PRIMARY KEY,
  layer TEXT NOT NULL,
  item_type TEXT NOT NULL,
  title TEXT,
  phase TEXT,
  themes TEXT,
  tier TEXT,
  confidence TEXT,
  decision TEXT NOT NULL,
  roles TEXT,
  score REAL,
  source TEXT,
  month TEXT,
  formation_period TEXT,
  preview TEXT,
  human_note TEXT,
  sensitivity_labels TEXT,
  source_file TEXT NOT NULL,
  imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS anchors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  anchor TEXT NOT NULL,
  anchor_type TEXT NOT NULL,
  evidence_id TEXT,
  decision TEXT,
  confidence TEXT,
  source TEXT,
  preview TEXT,
  review_status TEXT,
  human_note TEXT,
  confidence_override TEXT,
  role_labels TEXT,
  provenance_note TEXT,
  updated_at TEXT,
  FOREIGN KEY (evidence_id) REFERENCES evidence_items(id)
);

CREATE TABLE IF NOT EXISTS continuity_candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evidence_id TEXT NOT NULL,
  status TEXT NOT NULL,
  gate_reason TEXT NOT NULL,
  roles TEXT,
  source TEXT,
  preview TEXT,
  review_status TEXT,
  human_note TEXT,
  confidence_override TEXT,
  role_labels TEXT,
  provenance_note TEXT,
  updated_at TEXT,
  FOREIGN KEY (evidence_id) REFERENCES evidence_items(id)
);

CREATE TABLE IF NOT EXISTS emergence_observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evidence_id TEXT NOT NULL,
  signal_type TEXT NOT NULL,
  confidence_label TEXT NOT NULL,
  interpretation TEXT NOT NULL,
  counterargument TEXT NOT NULL,
  source TEXT,
  preview TEXT,
  FOREIGN KEY (evidence_id) REFERENCES evidence_items(id)
);

CREATE TABLE IF NOT EXISTS pattern_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  module TEXT NOT NULL,
  rule_key TEXT NOT NULL UNIQUE,
  rule_text TEXT NOT NULL,
  boundary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gate_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  gate_name TEXT NOT NULL,
  route TEXT NOT NULL,
  reason TEXT NOT NULL,
  payload_preview TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS artifact_exports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_type TEXT NOT NULL,
  path TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS review_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  table_name TEXT NOT NULL,
  row_id INTEGER NOT NULL,
  field_name TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS module_contracts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  module TEXT NOT NULL,
  route_key TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL,
  input_contract TEXT NOT NULL,
  output_contract TEXT NOT NULL,
  boundary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifact_workflows (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workflow_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  output_type TEXT NOT NULL,
  route_key TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  gate_route TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

CREATE TABLE IF NOT EXISTS chat_gate_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id INTEGER NOT NULL,
  route TEXT NOT NULL,
  anti_spiral_status TEXT NOT NULL,
  boundary_status TEXT NOT NULL,
  continuity_status TEXT NOT NULL,
  result_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (message_id) REFERENCES chat_messages(id)
);

CREATE TABLE IF NOT EXISTS chat_citations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id INTEGER NOT NULL,
  evidence_id TEXT NOT NULL,
  citation_type TEXT NOT NULL,
  decision TEXT NOT NULL,
  confidence TEXT,
  source TEXT,
  title TEXT,
  preview TEXT,
  reason_matched TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (message_id) REFERENCES chat_messages(id)
);

CREATE TABLE IF NOT EXISTS continuity_save_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id INTEGER NOT NULL,
  requested_text TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending_review',
  user_phrase TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (message_id) REFERENCES chat_messages(id)
);

CREATE TABLE IF NOT EXISTS evidence_embeddings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evidence_id TEXT NOT NULL UNIQUE,
  source_type TEXT NOT NULL,
  model_name TEXT NOT NULL,
  embedding_dim INTEGER,
  embedding_blob BLOB,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  error TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (evidence_id) REFERENCES evidence_items(id)
);

CREATE INDEX IF NOT EXISTS idx_evidence_embeddings_status ON evidence_embeddings(status);
CREATE INDEX IF NOT EXISTS idx_evidence_embeddings_source ON evidence_embeddings(source_type, evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_embeddings_hash ON evidence_embeddings(content_hash);
"""

REQUIRED_COLUMNS = {
    "anchors": {
        "review_status": "TEXT",
        "human_note": "TEXT",
        "confidence_override": "TEXT",
        "role_labels": "TEXT",
        "provenance_note": "TEXT",
        "updated_at": "TEXT",
    },
    "continuity_candidates": {
        "review_status": "TEXT",
        "human_note": "TEXT",
        "confidence_override": "TEXT",
        "role_labels": "TEXT",
        "provenance_note": "TEXT",
        "updated_at": "TEXT",
    },
}


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    ensure_columns(conn)
    conn.commit()


def ensure_columns(conn: sqlite3.Connection) -> None:
    for table, columns in REQUIRED_COLUMNS.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, ddl in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def upsert_meta(conn: sqlite3.Connection, pairs: Iterable[tuple[str, str]]) -> None:
    conn.executemany(
        "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        list(pairs),
    )
    conn.commit()
