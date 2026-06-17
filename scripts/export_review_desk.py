from __future__ import annotations

import argparse
from pathlib import Path

from selene.b_review_desk import review_desk_markdown
from selene.braid_tracer import run_braid_tracer
from selene.db import connect, init_db
from selene.paths import default_db_path, export_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the Selene B review desk as one plain-English Markdown file.")
    parser.add_argument("--db", type=Path, default=default_db_path(), help="Path to selene.sqlite3")
    parser.add_argument("--out", type=Path, default=None, help="Output Markdown path")
    parser.add_argument("--limit", type=int, default=100, help="Maximum grouped pieces to export")
    parser.add_argument("--refresh-braid", action="store_true", help="Run the review-only braid tracer before exporting")
    parser.add_argument("--reset-auto-suggestions", action="store_true", help="Supersede stale pending auto-created braid suggestions before refreshing; preserves human decisions")
    args = parser.parse_args()

    conn = connect(args.db)
    try:
        init_db(conn)
        if args.refresh_braid:
            run_braid_tracer(conn, {"limit": args.limit, "reset_auto_suggestions": args.reset_auto_suggestions})
        markdown = review_desk_markdown(conn, args.limit)
    finally:
        conn.close()

    out = args.out or (export_dir() / "review_desk_current.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(markdown, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
