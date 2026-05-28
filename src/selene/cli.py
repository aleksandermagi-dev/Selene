from __future__ import annotations

import argparse
import json
from pathlib import Path

from .db import connect, init_db
from .paths import default_db_path
from .registry import seed_registry
from .semantic import backfill_evidence_embeddings, semantic_status
from .validation import validate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Selene local-first vessel tools.")
    parser.add_argument("--db", default=str(default_db_path()))
    sub = parser.add_subparsers(dest="cmd", required=True)
    seed = sub.add_parser("seed", help="Import reviewed evidence maps into the local SQLite registry.")
    seed.add_argument("--if-empty", action="store_true", help="Do not overwrite an existing seeded registry.")
    sub.add_parser("validate", help="Run local registry and gate validation.")
    sub.add_parser("semantic-status", help="Report optional MiniLM semantic retrieval status.")
    semantic = sub.add_parser("semantic-backfill", help="Embed reviewed evidence with optional local MiniLM runtime.")
    semantic.add_argument("--limit", type=int)
    sidecar = sub.add_parser("sidecar", help="Run the local sidecar API.")
    sidecar.add_argument("--port", type=int, default=8766)
    sidecar.add_argument("--seed", action="store_true")
    args = parser.parse_args(argv)

    if args.cmd == "sidecar":
        from .sidecar import main as sidecar_main

        sidecar_args = ["--port", str(args.port), "--db", args.db]
        if args.seed:
            sidecar_args.append("--seed")
        return sidecar_main(sidecar_args)

    conn = connect(default_db_path() if args.db is None else Path(args.db))
    init_db(conn)
    if args.cmd == "seed":
        print(json.dumps(seed_registry(conn, force=not args.if_empty), indent=2, ensure_ascii=False))
    elif args.cmd == "validate":
        print(json.dumps(validate(conn), indent=2, ensure_ascii=False))
    elif args.cmd == "semantic-status":
        print(json.dumps(semantic_status(conn), indent=2, ensure_ascii=False))
    elif args.cmd == "semantic-backfill":
        print(json.dumps(backfill_evidence_embeddings(conn, limit=args.limit), indent=2, ensure_ascii=False))
    return 0
