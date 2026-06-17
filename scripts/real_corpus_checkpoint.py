from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from selene.b_review import corpus_coverage_status
from selene.b_review_desk import review_desk, review_desk_markdown
from selene.braid_tracer import run_braid_tracer
from selene.db import connect, init_db
from selene.paths import default_db_path, export_dir
from selene.validation import validate


def now_label() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def run_checkpoint(
    db_path: Path,
    out_dir: Path,
    *,
    limit: int = 149,
    refresh_braid: bool = False,
    reset_auto_suggestions: bool = False,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    try:
        init_db(conn)
        tracer_result: dict[str, Any] | None = None
        if refresh_braid:
            tracer_result = run_braid_tracer(
                conn,
                {
                    "limit": limit,
                    "reset_auto_suggestions": reset_auto_suggestions,
                },
            )
        desk = review_desk(conn, limit)
        coverage = corpus_coverage_status(conn)
        validation = validate(conn)
        markdown = review_desk_markdown(conn, limit)
    finally:
        conn.close()

    review_path = out_dir / "review_desk_current.md"
    checkpoint_path = out_dir / f"real_corpus_checkpoint_{now_label()}.md"
    review_path.write_text(markdown, encoding="utf-8")

    noise_counts = _noise_counts(desk.get("pieces") or [])
    report = {
        "status": "real_corpus_checkpoint_complete",
        "limit": limit,
        "refresh_braid": refresh_braid,
        "reset_auto_suggestions": reset_auto_suggestions,
        "tracer": tracer_result or {"status": "not_run"},
        "review_desk": {
            "pieces_to_review": desk["summary"]["pieces_to_review"],
            "pieces_before_filters": desk["summary"].get("pieces_before_filters"),
            "parsed_conversations": desk["summary"]["parsed_conversations"],
            "parsed_messages": desk["summary"]["parsed_messages"],
            "accepted_lessons": desk["summary"]["accepted_lessons"],
            "approved_future_references": desk["summary"]["approved_future_references"],
            "noise_tag_counts": noise_counts,
        },
        "coverage": coverage,
        "validation_ok": validation["ok"],
        "checkpoint_path": str(checkpoint_path),
        "review_desk_path": str(review_path),
        "activation_change": "none",
        "raw_a_import_allowed": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "training_allowed": False,
        "provider_dependency": False,
    }
    checkpoint_path.write_text(_checkpoint_markdown(report), encoding="utf-8")
    return report


def _noise_counts(pieces: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for piece in pieces:
        for noise_type in piece.get("noise_type") or []:
            key = str(noise_type)
            if not key:
                continue
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _checkpoint_markdown(report: dict[str, Any]) -> str:
    tracer = report["tracer"]
    review = report["review_desk"]
    lines = [
        "# Selene Real Corpus Checkpoint",
        "",
        f"Status: `{report['status']}`",
        "",
        "Boundary: B-review/cocoon only. No C activation, raw A direct import, active memory, runtime recall, model training, LoRA, or provider dependency.",
        "",
        "## Corpus / Braid Run",
        "",
        f"- refresh braid: {report['refresh_braid']}",
        f"- reset stale auto suggestions: {report['reset_auto_suggestions']}",
        f"- limit: {report['limit']}",
        f"- conversations indexed: {tracer.get('conversations_indexed', 'not run')}",
        f"- messages indexed: {tracer.get('messages_indexed', 'not run')}",
        f"- pairs seen: {tracer.get('pairs_seen', 'not run')}",
        f"- braid moments created: {tracer.get('created_count', 'not run')}",
        f"- braid moments skipped: {tracer.get('skipped_count', 'not run')}",
        "",
        "## Review Desk",
        "",
        f"- pieces to review: {review['pieces_to_review']}",
        f"- pieces before filters: {review['pieces_before_filters']}",
        f"- parsed conversations: {review['parsed_conversations']}",
        f"- parsed messages: {review['parsed_messages']}",
        f"- accepted lessons: {review['accepted_lessons']}",
        f"- approved future references: {review['approved_future_references']}",
        "",
        "## Noise Tag Counts",
        "",
    ]
    if review["noise_tag_counts"]:
        lines.extend(f"- {key}: {value}" for key, value in review["noise_tag_counts"].items())
    else:
        lines.append("- none in current filtered review desk")
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- validation ok: {report['validation_ok']}",
            "",
            "## Outputs",
            "",
            f"- review desk: `{report['review_desk_path']}`",
            f"- checkpoint: `{report['checkpoint_path']}`",
            "",
            "## Boundary Flags",
            "",
            f"- activation_change: {report['activation_change']}",
            f"- raw_a_import_allowed: {report['raw_a_import_allowed']}",
            f"- memory_write_active: {report['memory_write_active']}",
            f"- runtime_memory_recall: {report['runtime_memory_recall']}",
            f"- training_allowed: {report['training_allowed']}",
            f"- provider_dependency: {report['provider_dependency']}",
            "",
            "## JSON",
            "",
            "```json",
            json.dumps(report, indent=2),
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a repeatable Selene real-corpus B-review checkpoint.")
    parser.add_argument("--db", type=Path, default=default_db_path(), help="Path to selene.sqlite3")
    parser.add_argument("--out-dir", type=Path, default=export_dir(), help="Directory for checkpoint output")
    parser.add_argument("--limit", type=int, default=149, help="Review desk / braid limit")
    parser.add_argument("--refresh-braid", action="store_true", help="Run safe braid tracer refresh before exporting")
    parser.add_argument("--reset-auto-suggestions", action="store_true", help="Supersede stale pending auto-created suggestions; preserves human decisions")
    args = parser.parse_args()
    report = run_checkpoint(
        args.db,
        args.out_dir,
        limit=args.limit,
        refresh_braid=args.refresh_braid,
        reset_auto_suggestions=args.reset_auto_suggestions,
    )
    print(report["checkpoint_path"])


if __name__ == "__main__":
    main()
