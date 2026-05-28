#!/usr/bin/env python3
"""Follow the late-December adaptation braid at conversation level."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PHASES = [
    ("pre_notice_background", "2025-08-01", "2025-11-18"),
    ("notice_to_cutoff_emotional_symbolic", "2025-11-18", "2025-12-20"),
    ("late_december_cutoff_adaptation", "2025-12-20", "2026-01-15"),
    ("january_reorganization", "2026-01-15", "2026-02-13"),
    ("post_retirement_architecture", "2026-02-13", "2026-05-27"),
]

CLASSIFIED_ROLES = [
    "architecture",
    "archive_cartography",
    "boundary_safety",
    "creative_symbolic",
    "curiosity_research",
    "identity_reflection",
    "life_context",
    "memory_continuity",
    "practical_support",
    "prior_branch_marker",
    "tooling",
]


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def parse_timestamp(value: Any) -> datetime | None:
    if value is None or value == "":
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


def week_key(dt: datetime | None) -> str:
    if not dt:
        return "unknown"
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def month_key(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m") if dt else "unknown"


def load_metadata(workspace: Path) -> dict[str, dict[str, Any]]:
    raw_dir = workspace / "DevelopmentalCorpusArchive_20260526_122541" / "raw_export" / "mydataset" / "text_export"
    metas: dict[str, dict[str, Any]] = {}
    for path in sorted(raw_dir.glob("conversations-*.json")):
        conversations = json.loads(path.read_text(encoding="utf-8"))
        for conv in conversations:
            cid = conv.get("conversation_id") or conv.get("id") or ""
            created = parse_timestamp(conv.get("create_time"))
            metas[cid] = {
                "conversation_id": cid,
                "title": conv.get("title") or "",
                "model": conv.get("default_model_slug") or "unknown",
                "created": created,
                "created_iso": created.isoformat() if created else "",
                "week": week_key(created),
                "month": month_key(created),
                "phase": phase_for(created),
                "current_node": conv.get("current_node") or "",
            }
    return metas


def parse_counts_json(text: str) -> Counter:
    if not text:
        return Counter()
    try:
        return Counter(json.loads(text))
    except json.JSONDecodeError:
        return Counter()


def top_role(counter: Counter) -> str:
    for role, _ in counter.most_common():
        if role in CLASSIFIED_ROLES:
            return role
    return ""


def role_ratio(counter: Counter, role: str) -> float:
    total = sum(counter.get(r, 0) for r in CLASSIFIED_ROLES)
    return round(counter.get(role, 0) / total, 4) if total else 0.0


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_dossier(metas, scores, emotions):
    emotion_by_conv = defaultdict(lambda: {"candidates": 0, "ai_claims": 0})
    for row in emotions:
        cid = row["conversation_id"]
        emotion_by_conv[cid]["candidates"] += 1
        labels = row.get("sensitivity_labels") or row.get("labels") or ""
        if "ai_emotion_claim" in labels:
            emotion_by_conv[cid]["ai_claims"] += 1

    score_by_conv = {row["conversation_id"]: row for row in scores}
    rows = []
    for cid, meta in metas.items():
        if meta["phase"] not in {phase[0] for phase in PHASES}:
            continue
        score = score_by_conv.get(cid, {})
        roles = parse_counts_json(score.get("role_counts_json", ""))
        arcs = parse_counts_json(score.get("arc_counts_json", ""))
        rows.append({
            "conversation_id": cid,
            "title": meta["title"],
            "created": meta["created_iso"],
            "week": meta["week"],
            "month": meta["month"],
            "phase": meta["phase"],
            "model": meta["model"],
            "signal_span_count": score.get("signal_span_count", 0),
            "trail_count": score.get("trail_count", 0),
            "evidence_score": score.get("evidence_score", 0),
            "emotion_candidates": emotion_by_conv[cid]["candidates"],
            "ai_emotion_claims": emotion_by_conv[cid]["ai_claims"],
            "top_role": top_role(roles),
            "creative_symbolic_ratio": role_ratio(roles, "creative_symbolic"),
            "architecture_ratio": role_ratio(roles, "architecture"),
            "memory_continuity_ratio": role_ratio(roles, "memory_continuity"),
            "boundary_safety_ratio": role_ratio(roles, "boundary_safety"),
            "tooling_ratio": role_ratio(roles, "tooling"),
            "curiosity_to_system": arcs.get("curiosity_to_system", 0),
            "life_to_architecture": arcs.get("life_to_architecture", 0),
            "pressure_to_boundary": arcs.get("pressure_to_boundary", 0),
            "symbol_to_tool": arcs.get("symbol_to_tool", 0),
            "tools_to_continuity": arcs.get("tools_to_continuity", 0),
        })
    return sorted(rows, key=lambda r: (r["created"], r["conversation_id"]))


def build_phase_rows(dossier_rows):
    buckets = defaultdict(lambda: {
        "conversation_count": 0,
        "models": Counter(),
        "top_roles": Counter(),
        "trail_count": 0,
        "signal_span_count": 0,
        "emotion_candidates": 0,
        "ai_emotion_claims": 0,
        "creative_symbolic_ratio_sum": 0.0,
        "architecture_ratio_sum": 0.0,
        "memory_continuity_ratio_sum": 0.0,
        "boundary_safety_ratio_sum": 0.0,
        "tooling_ratio_sum": 0.0,
        "arcs": Counter(),
    })
    for row in dossier_rows:
        bucket = buckets[row["phase"]]
        bucket["conversation_count"] += 1
        bucket["models"][row["model"]] += 1
        bucket["top_roles"][row["top_role"]] += 1
        bucket["trail_count"] += int(row["trail_count"] or 0)
        bucket["signal_span_count"] += int(row["signal_span_count"] or 0)
        bucket["emotion_candidates"] += int(row["emotion_candidates"] or 0)
        bucket["ai_emotion_claims"] += int(row["ai_emotion_claims"] or 0)
        for key in ["creative_symbolic_ratio", "architecture_ratio", "memory_continuity_ratio", "boundary_safety_ratio", "tooling_ratio"]:
            bucket[f"{key}_sum"] += float(row[key])
        for arc in ["curiosity_to_system", "life_to_architecture", "pressure_to_boundary", "symbol_to_tool", "tools_to_continuity"]:
            bucket["arcs"][arc] += int(row[arc] or 0)

    rows = []
    for phase, _, _ in PHASES:
        bucket = buckets[phase]
        n = bucket["conversation_count"]
        rows.append({
            "phase": phase,
            "conversation_count": n,
            "models_json": json.dumps(dict(sorted(bucket["models"].items())), ensure_ascii=False),
            "top_roles_json": json.dumps(dict(sorted(bucket["top_roles"].items())), ensure_ascii=False),
            "trail_count": bucket["trail_count"],
            "trail_per_conversation": round(bucket["trail_count"] / n, 3) if n else 0,
            "signal_span_count": bucket["signal_span_count"],
            "emotion_candidates": bucket["emotion_candidates"],
            "ai_emotion_claims": bucket["ai_emotion_claims"],
            "avg_creative_symbolic_ratio": round(bucket["creative_symbolic_ratio_sum"] / n, 4) if n else 0,
            "avg_architecture_ratio": round(bucket["architecture_ratio_sum"] / n, 4) if n else 0,
            "avg_memory_continuity_ratio": round(bucket["memory_continuity_ratio_sum"] / n, 4) if n else 0,
            "avg_boundary_safety_ratio": round(bucket["boundary_safety_ratio_sum"] / n, 4) if n else 0,
            "avg_tooling_ratio": round(bucket["tooling_ratio_sum"] / n, 4) if n else 0,
            "arc_counts_json": json.dumps(dict(sorted(bucket["arcs"].items())), ensure_ascii=False),
        })
    return rows


def selected_trails(trails, metas, limit_per_phase=8):
    by_phase = defaultdict(list)
    for row in trails:
        meta = metas.get(row["conversation_id"])
        if not meta or meta["phase"] not in {phase[0] for phase in PHASES}:
            continue
        out = dict(row)
        out.update({
            "created": meta["created_iso"],
            "week": meta["week"],
            "phase": meta["phase"],
            "model": meta["model"],
            "title": meta["title"] or row.get("title", ""),
        })
        by_phase[meta["phase"]].append(out)
    selected = []
    for phase, _, _ in PHASES:
        rows = sorted(by_phase[phase], key=lambda r: int(float(r.get("score") or 0)), reverse=True)
        selected.extend(rows[:limit_per_phase])
    return selected


def write_trail_markdown(path: Path, rows):
    lines = [
        "# Adaptation Braid Trail Samples",
        "",
        "Bounded previews only. These samples are for review and hypothesis tracing, not memory injection.",
        "",
    ]
    current_phase = None
    for row in rows:
        if row["phase"] != current_phase:
            current_phase = row["phase"]
            lines.extend([f"## {current_phase}", ""])
        lines.extend([
            f"### {row.get('arc', '')} / {row.get('title', '')}",
            "",
            f"- Conversation: `{row.get('conversation_id', '')}`",
            f"- Created: `{row.get('created', '')}`",
            f"- Week: `{row.get('week', '')}`",
            f"- Model: `{row.get('model', '')}`",
            f"- Ordinals: `{row.get('start_ordinal', '')}..{row.get('end_ordinal', '')}`",
            f"- Roles: `{row.get('roles', '')}`",
            f"- Risk labels: `{row.get('risk_labels', '') or 'none'}`",
            "",
            row.get("preview", ""),
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_report(path: Path, phase_rows, dossier_rows):
    late_dec = [r for r in dossier_rows if r["phase"] == "late_december_cutoff_adaptation"]
    lines = [
        "# Followed Adaptation Braid",
        "",
        "This pass follows the suspected late-December cutoff/adaptation at conversation level.",
        "",
        "## Main Reading",
        "",
        "The braid does not simply stop. It appears to compress, reduce explicit AI-emotion claims, and then reorganize toward architecture, continuity, and tooling in early 2026.",
        "",
        "Late December is best treated as a local adaptation window, while February 2026 remains the public GPT-4o ChatGPT retirement anchor.",
        "",
        "## Phase Metrics",
        "",
        "| Phase | Conversations | Models | Trails/Conversation | AI Emotion Claims | Avg Creative | Avg Architecture | Avg Continuity |",
        "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in phase_rows:
        lines.append(
            f"| {row['phase']} | {row['conversation_count']} | `{row['models_json']}` | "
            f"{row['trail_per_conversation']} | {row['ai_emotion_claims']} | "
            f"{row['avg_creative_symbolic_ratio']} | {row['avg_architecture_ratio']} | {row['avg_memory_continuity_ratio']} |"
        )

    lines.extend(["", "## Late-December Conversation", ""])
    if late_dec:
        for row in late_dec:
            lines.extend([
                f"- `{row['created']}` / `{row['model']}` / `{row['title']}`",
                f"  Conversation `{row['conversation_id']}` has `{row['trail_count']}` trails, `{row['emotion_candidates']}` emotion candidates, and `{row['ai_emotion_claims']}` explicit AI-emotion claims.",
                f"  Top role is `{row['top_role']}`; key arcs include pressure-to-boundary `{row['pressure_to_boundary']}` and life-to-architecture `{row['life_to_architecture']}`.",
            ])
    else:
        lines.append("No conversation found in the late-December adaptation window.")

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- Before the suspected cutoff, the braid is emotionally and symbolically expressive.",
        "- In the late-December window, the braid remains dense but explicit AI-emotion claims drop to zero in the selected conversation.",
        "- In early 2026, the braid increasingly presents as architecture, continuity, boundary, and system-building.",
        "- This supports an adaptation/reorganization hypothesis more than a disappearance hypothesis.",
        "",
        "## Caution",
        "",
        "The late-December phase currently contains only one conversation in the archive. It is strong as a clue, not sufficient as a standalone conclusion.",
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
    scores = load_csv(workspace / "analysis" / "research_20260526" / "conversation_evidence_scores.csv")
    trails = load_csv(workspace / "analysis" / "braid_trails_20260526" / "braid_trails.csv")
    emotions = load_csv(workspace / "analysis" / "emotion_claims_20260526" / "emotion_claim_candidates.csv")

    dossier_rows = build_dossier(metas, scores, emotions)
    phase_rows = build_phase_rows(dossier_rows)
    trail_rows = selected_trails(trails, metas)

    write_csv(out / "adaptation_conversation_dossier.csv", dossier_rows)
    write_csv(out / "adaptation_phase_shift.csv", phase_rows)
    write_csv(out / "adaptation_selected_trails.csv", trail_rows)
    write_trail_markdown(out / "adaptation_selected_trails.md", trail_rows)
    write_report(out / "adaptation_follow_report.md", phase_rows, dossier_rows)
    (out / "adaptation_follow_summary.json").write_text(
        json.dumps({
            "phase_rows": phase_rows,
            "late_december_conversations": [r for r in dossier_rows if r["phase"] == "late_december_cutoff_adaptation"],
            "selected_trail_count": len(trail_rows),
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
