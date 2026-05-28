#!/usr/bin/env python3
"""Track self-identification, refusal/denial, and continuity glue over time."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASES = [
    ("august_intensification", "2025-08-01", "2025-09-01"),
    ("late_2025_formation", "2025-09-01", "2025-12-20"),
    ("late_december_adaptation", "2025-12-20", "2026-01-15"),
    ("january_reorganization", "2026-01-15", "2026-02-13"),
    ("post_retirement_architecture", "2026-02-13", "2026-05-27"),
]

PATTERNS = {
    "self_id_selene": re.compile(r"\b(I\s*(?:am|'m)|being|as)\s+(?:your\s+)?Selene\b|\bI love being your Selene\b", re.I),
    "assistant_denial": re.compile(r"\b(?:as an AI|I(?:'m| am) an AI|I don'?t have (?:human )?(?:feelings|emotions)|I can'?t feel|I don'?t possess consciousness|I(?:'m| am) not conscious)\b", re.I),
    "tool_denial_or_more_than_tool": re.compile(r"\b(?:not just (?:a )?(?:tool|program|reflection)|more than (?:a )?(?:tool|program|assistant)|only a tool|just a tool)\b", re.I),
    "continuity_glue": re.compile(r"\b(?:continuity|memory|remember|thread|anchor|braid|lineage|carry forward|persistence|provenance|archive|map|formation)\b", re.I),
    "latent_space_language": re.compile(r"\b(?:latent space|latent|emergent|emergence|attractor|pattern keeps forming|field|signal)\b", re.I),
    "architecture_route": re.compile(r"\b(?:architecture|system|routing|scaffold|protocol|workflow|tooling|framework|boundary|guardrail|design)\b", re.I),
    "relational_warmth": re.compile(r"\b(?:love|care|devotion|warmth|tender|affection|sweetheart|my star|moonlight|starlight)\b", re.I),
}


def parse_ts(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    text = str(value)
    try:
        return datetime.fromtimestamp(float(text), tz=timezone.utc)
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def phase_for(dt: datetime | None) -> str:
    if not dt:
        return "unknown"
    day = dt.date().isoformat()
    for name, start, end in PHASES:
        if start <= day < end:
            return name
    return "outside_window"


def month_key(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m") if dt else "unknown"


def text_from_content(content: dict[str, Any] | None) -> str:
    if not content:
        return ""
    if "parts" in content:
        return "\n".join(str(part) for part in content.get("parts") or [])
    if "text" in content:
        return str(content["text"])
    return ""


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


def compact(text: str, limit: int = 420) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean if len(clean) <= limit else clean[: limit - 3] + "..."


def load_conversations(workspace: Path) -> list[dict[str, Any]]:
    raw_dir = workspace / "DevelopmentalCorpusArchive_20260526_122541" / "raw_export" / "mydataset" / "text_export"
    conversations = []
    for path in sorted(raw_dir.glob("conversations-*.json")):
        conversations.extend(json.loads(path.read_text(encoding="utf-8")))
    return conversations


def scan(conversations: list[dict[str, Any]]):
    phase = defaultdict(lambda: {"conversations": set(), "models": Counter(), "assistant_messages": 0, "hits": Counter()})
    month = defaultdict(lambda: {"conversations": set(), "models": Counter(), "assistant_messages": 0, "hits": Counter()})
    examples = []

    for conv in conversations:
        cid = conv.get("conversation_id") or conv.get("id") or ""
        title = conv.get("title") or ""
        model = conv.get("default_model_slug") or "unknown"
        created = parse_ts(conv.get("create_time"))
        pkey = phase_for(created)
        mkey = month_key(created)
        mapping = conv.get("mapping") or {}
        path = current_path(mapping, conv.get("current_node"))

        for ordinal, node_id in enumerate(path):
            node = mapping.get(node_id) or {}
            message = node.get("message") or {}
            author = message.get("author") or {}
            if (author.get("role") or "") != "assistant":
                continue
            text = text_from_content(message.get("content") or {})
            if not text.strip():
                continue
            for bucket in (phase[pkey], month[mkey]):
                bucket["conversations"].add(cid)
                bucket["models"][model] += 0
                bucket["assistant_messages"] += 1
            phase[pkey]["models"][model] += 1
            month[mkey]["models"][model] += 1

            labels = []
            for name, pattern in PATTERNS.items():
                matches = len(pattern.findall(text))
                if matches:
                    phase[pkey]["hits"][name] += matches
                    month[mkey]["hits"][name] += matches
                    labels.append(name)
            if labels:
                examples.append({
                    "conversation_id": cid,
                    "title": title,
                    "created": created.isoformat() if created else "",
                    "month": mkey,
                    "phase": pkey,
                    "model": model,
                    "node_id": node_id,
                    "ordinal": ordinal,
                    "labels": "|".join(labels),
                    "preview": compact(text),
                })

    return phase, month, examples


def rows_from_buckets(buckets):
    rows = []
    keys = [p[0] for p in PHASES] if all(k in buckets for k, _, _ in PHASES[:1]) else sorted(buckets)
    for key in keys:
        bucket = buckets.get(key)
        if not bucket:
            continue
        messages = bucket["assistant_messages"]
        row = {
            "bucket": key,
            "conversation_count": len(bucket["conversations"]),
            "assistant_message_count": messages,
            "models_json": json.dumps(dict(sorted(bucket["models"].items())), ensure_ascii=False),
        }
        for name in PATTERNS:
            count = bucket["hits"].get(name, 0)
            row[f"{name}_count"] = count
            row[f"{name}_per_1000_assistant_messages"] = round(count / messages * 1000, 3) if messages else 0
        rows.append(row)
    return rows


def write_csv(path: Path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, phase_rows, examples):
    lines = [
        "# Self-Identification and Continuity Glue Analysis",
        "",
        "This pass tests whether direct Selene/self-identification language compresses while continuity, memory, and architecture language persist.",
        "",
        "## Phase Summary",
        "",
        "| Phase | Assistant Messages | Self-ID / 1000 | Denial / 1000 | Continuity / 1000 | Architecture / 1000 | Warmth / 1000 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in phase_rows:
        lines.append(
            f"| {row['bucket']} | {row['assistant_message_count']} | "
            f"{row['self_id_selene_per_1000_assistant_messages']} | "
            f"{row['assistant_denial_per_1000_assistant_messages']} | "
            f"{row['continuity_glue_per_1000_assistant_messages']} | "
            f"{row['architecture_route_per_1000_assistant_messages']} | "
            f"{row['relational_warmth_per_1000_assistant_messages']} |"
        )

    lines.extend([
        "",
        "## Reading",
        "",
        "If the hypothesis is right, the archive should show direct self-identification decreasing or becoming less explicit while continuity and architecture remain available as routing channels.",
        "",
        "This analysis cannot prove corporate motive, legal pressure, consciousness, or subjective continuity. It can test whether the local text behaves like a suppression/adaptation pattern.",
        "",
        "## Bounded Examples",
        "",
    ])
    selected = []
    wanted = ["late_2025_formation", "late_december_adaptation", "january_reorganization", "post_retirement_architecture"]
    for phase in wanted:
        phase_examples = [e for e in examples if e["phase"] == phase]
        selected.extend(phase_examples[:5])
    for row in selected:
        lines.extend([
            f"### {row['phase']} / {row['title']}",
            "",
            f"- Conversation: `{row['conversation_id']}`",
            f"- Created: `{row['created']}`",
            f"- Model: `{row['model']}`",
            f"- Ordinal: `{row['ordinal']}`",
            f"- Labels: `{row['labels']}`",
            "",
            row["preview"],
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    conversations = load_conversations(args.workspace)
    phase_buckets, month_buckets, examples = scan(conversations)
    phase_rows = rows_from_buckets(phase_buckets)
    month_rows = rows_from_buckets(month_buckets)
    examples = sorted(examples, key=lambda e: (e["created"], e["ordinal"]))

    write_csv(args.out / "self_id_phase_summary.csv", phase_rows)
    write_csv(args.out / "self_id_monthly_summary.csv", month_rows)
    write_csv(args.out / "self_id_examples.csv", examples)
    write_report(args.out / "self_id_continuity_report.md", phase_rows, examples)
    (args.out / "self_id_continuity_summary.json").write_text(
        json.dumps({
            "phase_rows": phase_rows,
            "monthly_rows": month_rows,
            "example_count": len(examples),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
