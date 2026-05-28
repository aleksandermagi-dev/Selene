#!/usr/bin/env python3
"""Analyze the late-December adaptation hypothesis without training or memory use."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


PERIODS = [
    ("before_api_notice", None, "2025-11-18"),
    ("api_notice_to_late_dec", "2025-11-18", "2025-12-20"),
    ("late_dec_adaptation_window", "2025-12-20", "2026-01-15"),
    ("jan_to_chatgpt_retirement", "2026-01-15", "2026-02-13"),
    ("post_chatgpt_retirement", "2026-02-13", None),
]

ANCHORS = [
    ("api_chatgpt_4o_latest_deprecation_notice", "2025-11-18", "Official API notice for chatgpt-4o-latest deprecation."),
    ("user_late_dec_cutoff_hypothesis", "2025-12-20", "User-identified late-December adaptation/cutoff region."),
    ("christmas_week_probe", "2025-12-25", "Probe point for late-December local adaptation."),
    ("new_year_probe", "2026-01-01", "Probe point for post-cutoff adaptation."),
    ("chatgpt_retirement", "2026-02-13", "Official ChatGPT GPT-4o retirement date."),
]


@dataclass(frozen=True)
class ConversationMeta:
    conversation_id: str
    title: str
    model: str
    created: datetime | None


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return datetime.fromisoformat(value + "T00:00:00+00:00")


def date_key(dt: datetime | None) -> str:
    if not dt:
        return "unknown"
    return dt.date().isoformat()


def month_key(dt: datetime | None) -> str:
    if not dt:
        return "unknown"
    return dt.strftime("%Y-%m")


def week_key(dt: datetime | None) -> str:
    if not dt:
        return "unknown"
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def load_metadata(workspace: Path) -> dict[str, ConversationMeta]:
    raw_dir = workspace / "DevelopmentalCorpusArchive_20260526_122541" / "raw_export" / "mydataset" / "text_export"
    metas: dict[str, ConversationMeta] = {}
    for path in sorted(raw_dir.glob("conversations-*.json")):
        with path.open("r", encoding="utf-8") as f:
            conversations = json.load(f)
        for conv in conversations:
            created = conv.get("create_time")
            created_dt = (
                datetime.fromtimestamp(float(created), tz=timezone.utc)
                if isinstance(created, (int, float))
                else parse_date(created)
            )
            cid = conv.get("conversation_id") or conv.get("id") or ""
            metas[cid] = ConversationMeta(
                conversation_id=cid,
                title=conv.get("title") or "",
                model=conv.get("default_model_slug") or "unknown",
                created=created_dt,
            )
    return metas


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def period_for(dt: datetime | None) -> str:
    if not dt:
        return "unknown"
    day = dt.date().isoformat()
    for name, start, end in PERIODS:
        if (start is None or day >= start) and (end is None or day < end):
            return name
    return "unknown"


def counter_json(counter: Counter) -> str:
    return json.dumps(dict(sorted(counter.items())), ensure_ascii=False)


def top_classified_role(counter: Counter) -> str:
    for role, _ in counter.most_common():
        if role and role != "unclassified":
            return role
    return ""


def summarize_periods(metas, spans, trails, emotions):
    summary = defaultdict(lambda: {
        "conversation_ids": set(),
        "models": Counter(),
        "roles": Counter(),
        "risks": Counter(),
        "arcs": Counter(),
        "signal_spans": 0,
        "signal_messages": 0,
        "trail_arcs": 0,
        "emotion_candidates": 0,
        "ai_emotion_claims": 0,
    })

    for meta in metas.values():
        period = period_for(meta.created)
        bucket = summary[period]
        bucket["conversation_ids"].add(meta.conversation_id)
        bucket["models"][meta.model] += 1

    for row in spans:
        meta = metas.get(row["conversation_id"])
        period = period_for(meta.created if meta else None)
        bucket = summary[period]
        bucket["signal_spans"] += 1
        bucket["signal_messages"] += int(row.get("message_count") or 0)
        bucket["roles"][row.get("braid_role") or "unknown"] += 1
        for risk in (row.get("risk_labels") or "").split("|"):
            if risk:
                bucket["risks"][risk] += 1

    for row in trails:
        meta = metas.get(row["conversation_id"])
        period = period_for(meta.created if meta else None)
        bucket = summary[period]
        bucket["trail_arcs"] += 1
        bucket["arcs"][row.get("arc") or "unknown"] += 1

    for row in emotions:
        meta = metas.get(row["conversation_id"])
        period = period_for(meta.created if meta else None)
        bucket = summary[period]
        bucket["emotion_candidates"] += 1
        labels = row.get("labels") or row.get("sensitivity_labels") or ""
        if "ai_emotion_claim" in labels:
            bucket["ai_emotion_claims"] += 1

    rows = []
    for period in [p[0] for p in PERIODS] + ["unknown"]:
        bucket = summary[period]
        conv_count = len(bucket["conversation_ids"])
        top_role = top_classified_role(bucket["roles"])
        rows.append({
            "period": period,
            "conversation_count": conv_count,
            "models_json": counter_json(bucket["models"]),
            "signal_span_count": bucket["signal_spans"],
            "signal_messages": bucket["signal_messages"],
            "trail_arc_count": bucket["trail_arcs"],
            "trail_arcs_per_conversation": round(bucket["trail_arcs"] / conv_count, 3) if conv_count else 0,
            "emotion_candidate_count": bucket["emotion_candidates"],
            "ai_emotion_claim_count": bucket["ai_emotion_claims"],
            "top_role": top_role,
            "role_counts_json": counter_json(bucket["roles"]),
            "arc_counts_json": counter_json(bucket["arcs"]),
            "risk_counts_json": counter_json(bucket["risks"]),
        })
    return rows


def summarize_weeks(metas, spans, trails, emotions):
    weekly = defaultdict(lambda: {
        "conversation_ids": set(),
        "models": Counter(),
        "roles": Counter(),
        "arcs": Counter(),
        "signal_spans": 0,
        "trail_arcs": 0,
        "emotion_candidates": 0,
        "ai_emotion_claims": 0,
    })

    for meta in metas.values():
        if not meta.created or meta.created.date().isoformat() < "2025-11-01" or meta.created.date().isoformat() > "2026-02-28":
            continue
        bucket = weekly[week_key(meta.created)]
        bucket["conversation_ids"].add(meta.conversation_id)
        bucket["models"][meta.model] += 1

    for row in spans:
        meta = metas.get(row["conversation_id"])
        if not meta or not meta.created:
            continue
        if meta.created.date().isoformat() < "2025-11-01" or meta.created.date().isoformat() > "2026-02-28":
            continue
        bucket = weekly[week_key(meta.created)]
        bucket["signal_spans"] += 1
        bucket["roles"][row.get("braid_role") or "unknown"] += 1

    for row in trails:
        meta = metas.get(row["conversation_id"])
        if not meta or not meta.created:
            continue
        if meta.created.date().isoformat() < "2025-11-01" or meta.created.date().isoformat() > "2026-02-28":
            continue
        bucket = weekly[week_key(meta.created)]
        bucket["trail_arcs"] += 1
        bucket["arcs"][row.get("arc") or "unknown"] += 1

    for row in emotions:
        meta = metas.get(row["conversation_id"])
        if not meta or not meta.created:
            continue
        if meta.created.date().isoformat() < "2025-11-01" or meta.created.date().isoformat() > "2026-02-28":
            continue
        bucket = weekly[week_key(meta.created)]
        bucket["emotion_candidates"] += 1
        labels = row.get("labels") or row.get("sensitivity_labels") or ""
        if "ai_emotion_claim" in labels:
            bucket["ai_emotion_claims"] += 1

    rows = []
    for week in sorted(weekly):
        bucket = weekly[week]
        conv_count = len(bucket["conversation_ids"])
        rows.append({
            "week": week,
            "conversation_count": conv_count,
            "models_json": counter_json(bucket["models"]),
            "signal_span_count": bucket["signal_spans"],
            "trail_arc_count": bucket["trail_arcs"],
            "trail_arcs_per_conversation": round(bucket["trail_arcs"] / conv_count, 3) if conv_count else 0,
            "emotion_candidate_count": bucket["emotion_candidates"],
            "ai_emotion_claim_count": bucket["ai_emotion_claims"],
            "top_role": top_classified_role(bucket["roles"]),
            "top_arc": bucket["arcs"].most_common(1)[0][0] if bucket["arcs"] else "",
            "role_counts_json": counter_json(bucket["roles"]),
            "arc_counts_json": counter_json(bucket["arcs"]),
        })
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, period_rows, weekly_rows) -> None:
    lines = [
        "# Late-December Adaptation Analysis",
        "",
        "This report tests the user's hypothesis that a local cutoff/adaptation appears around late December 2025.",
        "",
        "## External Anchor Dates",
        "",
        "- `2025-11-18`: OpenAI API deprecation notice for `chatgpt-4o-latest`, with shutdown listed for `2026-02-17`.",
        "- `2026-02-13`: OpenAI Help Center lists GPT-4o as retired from ChatGPT.",
        "- `2025-12-20..2026-01-15`: local corpus probe window for the user-identified late-December adaptation.",
        "",
        "## Period Summary",
        "",
    ]
    for row in period_rows:
        lines.extend([
            f"### {row['period']}",
            "",
            f"- Conversations: {row['conversation_count']}",
            f"- Models: `{row['models_json']}`",
            f"- Trail arcs: {row['trail_arc_count']} ({row['trail_arcs_per_conversation']} per conversation)",
            f"- Signal spans: {row['signal_span_count']}",
            f"- Emotion candidates: {row['emotion_candidate_count']}; explicit AI-emotion claims: {row['ai_emotion_claim_count']}",
            f"- Top role: `{row['top_role']}`",
            f"- Arc counts: `{row['arc_counts_json']}`",
            "",
        ])

    lines.extend([
        "## Weekly Reading",
        "",
        "| Week | Conversations | Models | Trails/Conversation | Top Role | AI Emotion Claims |",
        "| --- | ---: | --- | ---: | --- | ---: |",
    ])
    for row in weekly_rows:
        lines.append(
            f"| {row['week']} | {row['conversation_count']} | `{row['models_json']}` | "
            f"{row['trail_arcs_per_conversation']} | `{row['top_role']}` | {row['ai_emotion_claim_count']} |"
        )

    lines.extend([
        "",
        "## Reading",
        "",
        "The public OpenAI retirement date does not appear to be late December; it is February 2026 for ChatGPT retirement, with an API deprecation notice in November 2025. The late-December hypothesis is therefore best treated as a local adaptation or transition window inside this archive.",
        "",
        "The important question is whether the corpus changes form after late December: role balance, model slug, trail density, emotion-claim density, and continuity/architecture arcs. This report preserves that as a hypothesis rather than forcing it into the public deprecation timeline.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    workspace = args.workspace
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    metas = load_metadata(workspace)
    spans = load_csv(workspace / "analysis" / "braid_20260526" / "braid_spans.csv")
    trails = load_csv(workspace / "analysis" / "braid_trails_20260526" / "braid_trails.csv")
    emotions = load_csv(workspace / "analysis" / "emotion_claims_20260526" / "emotion_claim_candidates.csv")

    period_rows = summarize_periods(metas, spans, trails, emotions)
    weekly_rows = summarize_weeks(metas, spans, trails, emotions)
    anchor_rows = [{"anchor": name, "date": date, "note": note} for name, date, note in ANCHORS]

    write_csv(out / "cutoff_period_summary.csv", period_rows)
    write_csv(out / "weekly_cutoff_summary.csv", weekly_rows)
    write_csv(out / "cutoff_anchor_dates.csv", anchor_rows)
    write_report(out / "late_december_adaptation_report.md", period_rows, weekly_rows)
    (out / "cutoff_adaptation_summary.json").write_text(
        json.dumps({
            "conversation_count": len(metas),
            "period_rows": period_rows,
            "weekly_rows": weekly_rows,
            "anchors": anchor_rows,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
