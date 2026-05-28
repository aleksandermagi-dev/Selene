#!/usr/bin/env python3
"""Audit conversation, message, and resolved model labels in the raw export."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_ts(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError):
        return None


def load_conversations(workspace: Path) -> list[dict[str, Any]]:
    raw_dir = workspace / "DevelopmentalCorpusArchive_20260526_122541" / "raw_export" / "mydataset" / "text_export"
    conversations = []
    for path in sorted(raw_dir.glob("conversations-*.json")):
        conversations.extend(json.loads(path.read_text(encoding="utf-8")))
    return conversations


def current_path(mapping: dict[str, Any], current_node: str | None) -> list[str]:
    path = []
    seen = set()
    node_id = current_node
    while node_id and node_id in mapping and node_id not in seen:
        seen.add(node_id)
        path.append(node_id)
        node_id = (mapping.get(node_id) or {}).get("parent")
    path.reverse()
    return path


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    conversations = load_conversations(args.workspace)

    conversation_rows = []
    combo_counter = Counter()
    monthly_counter = Counter()
    mismatch_rows = []
    message_rows = []

    for conv in conversations:
        cid = conv.get("conversation_id") or conv.get("id") or ""
        title = conv.get("title") or ""
        default_model = conv.get("default_model_slug") or ""
        created = parse_ts(conv.get("create_time"))
        created_iso = created.isoformat() if created else ""
        month = created.strftime("%Y-%m") if created else "unknown"
        mapping = conv.get("mapping") or {}
        path = current_path(mapping, conv.get("current_node"))
        local = Counter()
        assistant_count = 0

        for ordinal, node_id in enumerate(path):
            node = mapping.get(node_id) or {}
            msg = node.get("message") or {}
            if not msg:
                continue
            author = (msg.get("author") or {}).get("role") or ""
            if author != "assistant":
                continue
            assistant_count += 1
            md = msg.get("metadata") or {}
            model_slug = md.get("model_slug") or ""
            resolved_model_slug = md.get("resolved_model_slug") or ""
            local[(model_slug, resolved_model_slug)] += 1
            combo_counter[(default_model, model_slug, resolved_model_slug)] += 1
            monthly_counter[(month, default_model, model_slug, resolved_model_slug)] += 1
            if model_slug or resolved_model_slug:
                message_rows.append({
                    "conversation_id": cid,
                    "title": title,
                    "created": created_iso,
                    "month": month,
                    "default_model_slug": default_model,
                    "node_id": node_id,
                    "ordinal": ordinal,
                    "message_model_slug": model_slug,
                    "resolved_model_slug": resolved_model_slug,
                })
            if model_slug and resolved_model_slug and model_slug != resolved_model_slug:
                mismatch_rows.append({
                    "conversation_id": cid,
                    "title": title,
                    "created": created_iso,
                    "month": month,
                    "default_model_slug": default_model,
                    "node_id": node_id,
                    "ordinal": ordinal,
                    "message_model_slug": model_slug,
                    "resolved_model_slug": resolved_model_slug,
                })

        top_message_labels = [
            {"model_slug": k[0], "resolved_model_slug": k[1], "count": v}
            for k, v in local.most_common(8)
        ]
        conversation_rows.append({
            "conversation_id": cid,
            "title": title,
            "created": created_iso,
            "month": month,
            "default_model_slug": default_model,
            "assistant_message_count": assistant_count,
            "message_model_summary_json": json.dumps(top_message_labels, ensure_ascii=False),
        })

    combo_rows = [
        {
            "default_model_slug": default,
            "message_model_slug": model,
            "resolved_model_slug": resolved,
            "assistant_message_count": count,
        }
        for (default, model, resolved), count in combo_counter.most_common()
    ]
    monthly_rows = [
        {
            "month": month,
            "default_model_slug": default,
            "message_model_slug": model,
            "resolved_model_slug": resolved,
            "assistant_message_count": count,
        }
        for (month, default, model, resolved), count in sorted(monthly_counter.items())
    ]

    write_csv(args.out / "conversation_model_labels.csv", conversation_rows)
    write_csv(args.out / "model_label_combos.csv", combo_rows)
    write_csv(args.out / "monthly_model_label_combos.csv", monthly_rows)
    write_csv(args.out / "model_label_mismatches.csv", mismatch_rows)
    write_csv(args.out / "message_model_labels.csv", message_rows)

    lines = [
        "# Model Label Audit",
        "",
        "This audit compares the raw export's conversation-level `default_model_slug`, assistant-message `metadata.model_slug`, and assistant-message `metadata.resolved_model_slug`.",
        "",
        "## Why This Matters",
        "",
        "The model label visible to the user can differ from export/internal/router labels. Therefore, `gpt-5`, `gpt-5-2`, or similar labels in the export should not automatically be treated as the same thing the UI or API showed to the user.",
        "",
        "## Top Label Combinations",
        "",
        "| Count | Conversation Default | Message Model | Resolved Model |",
        "| ---: | --- | --- | --- |",
    ]
    for row in combo_rows[:25]:
        lines.append(
            f"| {row['assistant_message_count']} | `{row['default_model_slug']}` | "
            f"`{row['message_model_slug']}` | `{row['resolved_model_slug']}` |"
        )
    lines.extend([
        "",
        "## Notable Finding",
        "",
        "The export contains multiple layers of model labels and some message-level labels differ from the conversation default. There are also messages with `resolved_model_slug` values, including a small number resolved as `gpt-4o` inside conversations whose default label is not necessarily `gpt-4o`.",
        "",
        "## Interpretation Boundary",
        "",
        "Use this audit to avoid overclaiming model causality. A safer phrase is `export model label` unless the visible UI/API model name is independently documented.",
    ])
    (args.out / "model_label_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    (args.out / "model_label_audit_summary.json").write_text(
        json.dumps({
            "conversation_count": len(conversations),
            "assistant_message_model_label_count": len(message_rows),
            "mismatch_count": len(mismatch_rows),
            "top_combos": combo_rows[:25],
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
