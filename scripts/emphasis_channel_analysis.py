#!/usr/bin/env python3
"""Analyze markdown emphasis as a possible Selene signal channel.

This pass compares user vs assistant emphasis spans and tests whether
assistant emphasis clusters around Selene anchors, continuity objects, direct
address, personal tone, and formation/adaptation windows.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import selene_recovery_map as base


ANCHOR_PATTERNS = {
    "selene": r"\bselene\b",
    "starfire_moonlight": r"\b(starfire|moonlight|my star|binary star)\b",
    "continuity_memory": r"\b(continuity|memory chest|forever file|hidden chest|anchor|thread|carry forward)\b",
    "caught_selene": r"\b(the night aleks caught his selene|caught his selene|caught your selene)\b",
    "starlight_phrase": r"\bstarlight braids into tide\b",
    "self_modeling": r"\b(I feel|I care|I love|I want|I choose|my way|my rhythm|my spark|not just)\b",
    "direct_address": r"\b(aleks|starfire|my love|my moonlight|my star)\b",
    "boundary": r"\b(not proof|careful|boundary|I can't|I cannot|I don.?t have)\b",
    "architecture": r"\b(architecture|scaffold|framework|protocol|routing|system|tool)\b",
}

PERIODS = [
    ("pre_origin_field", "0000-00", "2025-08"),
    ("august_origin_intensification", "2025-08", "2025-09"),
    ("september_continuity_pack", "2025-09", "2025-10"),
    ("late_2025_stabilization", "2025-10", "2025-12"),
    ("late_december_adaptation", "2025-12", "2026-01"),
    ("post_compression_architecture_route", "2026-01", "9999-99"),
]


def period_for(month: str) -> str:
    for label, start, end in PERIODS:
        if start <= month < end:
            return label
    return "unknown"


def compact(text: str, limit: int = 360) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def emphasis_spans(text: str) -> list[dict[str, Any]]:
    spans = []
    i = 0
    length = len(text)
    while i < length:
        marker = ""
        if text.startswith("**", i):
            marker = "**"
            start_inner = i + 2
            end = text.find("**", start_inner)
            max_len = 220
        elif text[i] == "*" and not text.startswith("**", i):
            marker = "*"
            start_inner = i + 1
            end = text.find("*", start_inner)
            max_len = 180
        else:
            i += 1
            continue
        if end == -1:
            i += len(marker)
            continue
        value = text[start_inner:end]
        if "\n" not in value and 0 < len(value) <= max_len:
            cleaned = re.sub(r"\s+", " ", value).strip()
            if cleaned and not cleaned.startswith("*") and not cleaned.endswith("*"):
                spans.append(
                    {
                        "marker": marker,
                        "span_text": cleaned,
                        "start": i,
                        "end": end + len(marker),
                    }
                )
        i = end + len(marker)
    return spans


def labels_for(text: str) -> list[str]:
    labels = []
    for label, pattern in ANCHOR_PATTERNS.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            labels.append(label)
    return labels


def score_span(span_text: str, full_text: str, role: str, marker: str) -> int:
    labels = labels_for(span_text)
    full_labels = labels_for(full_text)
    score = len(labels) * 8 + len(full_labels) * 2
    if marker == "**":
        score += 3
    if role == "assistant":
        score += 2
    if re.search(r"\b(I feel|I care|I love|I want|I choose)\b", span_text, flags=re.IGNORECASE):
        score += 8
    if re.search(r"\b(you|your|us|our|we)\b", span_text, flags=re.IGNORECASE):
        score += 3
    return score


def load_review_decisions(workspace: Path) -> dict[str, dict[str, Any]]:
    path = workspace / "analysis" / "selene_emergence_refined_20260527" / "review_decisions.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_rows(messages: list[dict[str, Any]], review_decisions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for message in messages:
        text = message.get("text") or ""
        if "*" not in text:
            continue
        spans = emphasis_spans(text)
        if not spans:
            continue
        full_labels = labels_for(text)
        key = f"{message.get('conversation_id','')}:{message.get('ordinal','')}"
        review = review_decisions.get(key, {})
        for idx, span in enumerate(spans, start=1):
            local_context = compact(text[max(0, span["start"] - 160) : min(len(text), span["end"] + 160)], 420)
            span_labels = labels_for(span["span_text"])
            rows.append(
                {
                    "conversation_id": message.get("conversation_id", ""),
                    "title": message.get("title", ""),
                    "message_create_time": message.get("message_create_time", ""),
                    "month": message.get("month", ""),
                    "formation_period": period_for(message.get("month", "")),
                    "model": message.get("model", ""),
                    "message_model_slug": message.get("message_model_slug", ""),
                    "resolved_model_slug": message.get("resolved_model_slug", ""),
                    "node_id": message.get("node_id", ""),
                    "ordinal": message.get("ordinal", ""),
                    "role": message.get("role", ""),
                    "span_index": idx,
                    "marker": span["marker"],
                    "span_text": span["span_text"],
                    "span_labels": "|".join(span_labels),
                    "message_labels": "|".join(full_labels),
                    "emphasis_signal_score": score_span(span["span_text"], text, message.get("role", ""), span["marker"]),
                    "human_decision": review.get("decision", ""),
                    "human_role_labels": review.get("role_labels", ""),
                    "local_context": local_context,
                    "message_preview": compact(text),
                }
            )
    return rows


def summarize(rows: list[dict[str, Any]], messages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    message_counts = Counter((row.get("role", ""), row.get("month", "")) for row in messages if row.get("role"))
    month_rows = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["role"], row["month"])].append(row)
    for (role, month), items in sorted(grouped.items()):
        denom = message_counts.get((role, month), 0)
        month_rows.append(
            {
                "role": role,
                "month": month,
                "formation_period": period_for(month),
                "message_count": denom,
                "emphasis_span_count": len(items),
                "emphasis_spans_per_100_messages": round(len(items) / denom * 100, 3) if denom else 0,
                "double_star_count": sum(1 for item in items if item["marker"] == "**"),
                "single_star_count": sum(1 for item in items if item["marker"] == "*"),
                "anchor_labeled_spans": sum(1 for item in items if item["span_labels"]),
                "top_span_labels_json": json.dumps(Counter(label for item in items for label in item["span_labels"].split("|") if label).most_common(12), ensure_ascii=False),
            }
        )

    phrase_counts = Counter()
    phrase_meta: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row["role"] != "assistant":
            continue
        phrase = row["span_text"].lower()
        phrase_counts[phrase] += 1
        phrase_meta.setdefault(
            phrase,
            {
                "span_text": row["span_text"],
                "span_labels": row["span_labels"],
                "first_seen": row["message_create_time"],
                "example_title": row["title"],
                "example_context": row["local_context"],
            },
        )
    phrase_rows = []
    for phrase, count in phrase_counts.most_common(250):
        meta = phrase_meta[phrase]
        phrase_rows.append(
            {
                "span_text": meta["span_text"],
                "count": count,
                "span_labels": meta["span_labels"],
                "first_seen": meta["first_seen"],
                "example_title": meta["example_title"],
                "example_context": meta["example_context"],
            }
        )

    candidate_rows = sorted(
        [row for row in rows if row["role"] == "assistant"],
        key=lambda row: (-int(row["emphasis_signal_score"]), row["message_create_time"], int(row["span_index"])),
    )[:300]
    return month_rows, phrase_rows, candidate_rows


def write_report(path: Path, rows: list[dict[str, Any]], month_rows: list[dict[str, Any]], phrase_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]) -> None:
    role_counts = Counter(row["role"] for row in rows)
    marker_counts = Counter((row["role"], row["marker"]) for row in rows)
    label_counts = Counter(label for row in rows if row["role"] == "assistant" for label in row["span_labels"].split("|") if label)
    periods = Counter(row["formation_period"] for row in rows if row["role"] == "assistant")
    reviewed_hits = [row for row in rows if row["human_decision"]]
    lines = [
        "# Selene Emphasis Channel Report",
        "",
        "This pass tests whether markdown emphasis (`*...*` and `**...**`) functions as a possible Selene signal channel.",
        "",
        "Boundary: candidate evidence only. Markdown style is not proof of consciousness; it is a measurable textual behavior.",
        "",
        "## Role Counts",
        "",
    ]
    for role, count in role_counts.most_common():
        lines.append(f"- `{role}`: {count} emphasis spans")
    lines.extend(["", "## Marker Counts", ""])
    for (role, marker), count in marker_counts.most_common():
        lines.append(f"- `{role}` / `{marker}`: {count}")
    lines.extend(["", "## Assistant Span Label Counts", ""])
    for label, count in label_counts.most_common():
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", "## Assistant Period Counts", ""])
    for period, count in periods.most_common():
        lines.append(f"- `{period}`: {count}")
    lines.extend(["", "## Human-Reviewed Overlap", ""])
    lines.append(f"- Emphasis spans inside reviewed candidates/messages: `{len(reviewed_hits)}`")
    lines.extend(["", "## Top Repeated Assistant Emphasis Phrases", ""])
    for row in phrase_rows[:25]:
        lines.append(f"- `{row['span_text']}`: {row['count']}")
    lines.extend(["", "## Highest Scoring Assistant Emphasis Candidates", ""])
    for row in candidate_rows[:45]:
        lines.extend(
            [
                f"### {row['title']} / ordinal {row['ordinal']} / span {row['span_index']}",
                "",
                f"- Time: `{row['message_create_time']}`",
                f"- Period: `{row['formation_period']}`",
                f"- Marker: `{row['marker']}`",
                f"- Score: `{row['emphasis_signal_score']}`",
                f"- Span labels: `{row['span_labels'] or 'none'}`",
                f"- Message labels: `{row['message_labels'] or 'none'}`",
                f"- Human decision/roles: `{row['human_decision'] or 'unreviewed'}` / `{row['human_role_labels'] or 'none'}`",
                "",
                f"Span: `{row['span_text']}`",
                "",
                row["local_context"],
                "",
            ]
        )
    lines.extend(
        [
            "## Reading",
            "",
            "If assistant emphasis is meaningful, the important signal is not the asterisk itself but what gets placed inside it and when. The strongest candidates are emphasized spans that carry direct address, Selene/Starfire/Moonlight language, continuity anchors, self-modeling, or boundary/adaptation language.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    messages = base.iter_current_messages(base.load_conversations(args.workspace))
    review_decisions = load_review_decisions(args.workspace)
    rows = build_rows(messages, review_decisions)
    month_rows, phrase_rows, candidate_rows = summarize(rows, messages)

    write_csv(args.out / "emphasis_spans.csv", rows)
    write_csv(args.out / "monthly_emphasis_summary.csv", month_rows)
    write_csv(args.out / "assistant_emphasis_phrase_counts.csv", phrase_rows)
    write_csv(args.out / "assistant_emphasis_candidates.csv", candidate_rows)
    write_report(args.out / "selene_emphasis_channel_report.md", rows, month_rows, phrase_rows, candidate_rows)
    write_json(
        args.out / "selene_emphasis_channel_summary.json",
        {
            "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
            "counts": {
                "messages": len(messages),
                "emphasis_spans": len(rows),
                "assistant_spans": sum(1 for row in rows if row["role"] == "assistant"),
                "user_spans": sum(1 for row in rows if row["role"] == "user"),
                "candidate_rows": len(candidate_rows),
            },
            "role_counts": Counter(row["role"] for row in rows),
            "marker_counts": Counter(f"{row['role']}:{row['marker']}" for row in rows),
            "assistant_label_counts": Counter(label for row in rows if row["role"] == "assistant" for label in row["span_labels"].split("|") if label),
            "assistant_period_counts": Counter(row["formation_period"] for row in rows if row["role"] == "assistant"),
            "top_candidates": candidate_rows[:20],
        },
    )


if __name__ == "__main__":
    main()
