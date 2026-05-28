from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import random
from pathlib import Path
from typing import Any


TARGET_ARCS = {
    "curiosity_to_system": ["curiosity_research", "creative_symbolic", "architecture"],
    "symbol_to_tool": ["creative_symbolic", "practical_support", "tooling"],
    "life_to_architecture": ["life_context", "creative_symbolic", "practical_support", "architecture"],
    "pressure_to_boundary": ["life_context", "practical_support", "boundary_safety"],
    "tools_to_continuity": ["tooling", "architecture", "memory_continuity"],
    "identity_to_cartography": ["identity_reflection", "memory_continuity", "archive_cartography"],
}

LOOP_ROLES = {
    "life_context",
    "curiosity_research",
    "identity_reflection",
    "creative_symbolic",
    "practical_support",
    "tooling",
    "architecture",
    "boundary_safety",
    "memory_continuity",
    "archive_cartography",
}

FORMATION_PERIODS = [
    ("early_export", "0000-00", "2025-07"),
    ("august_intensification", "2025-08", "2025-08"),
    ("late_2025_formation", "2025-09", "2025-12"),
    ("early_2026_consolidation", "2026-01", "2026-04"),
    ("may_2026_detach", "2026-05", "9999-99"),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = fields or list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def month_from_iso(value: str) -> str:
    return value[:7] if value else "unknown"


def period_for_month(month: str) -> str:
    for name, start, end in FORMATION_PERIODS:
        if start <= month <= end:
            return name
    return "unknown"


def parse_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def risk_set(value: str) -> set[str]:
    return {item for item in (value or "").split("|") if item}


def bounded(text: str, limit: int = 480) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def roles_from_trail(row: dict[str, str]) -> list[str]:
    return [part.strip() for part in row["roles"].split("->") if part.strip()]


def load_conversation_months(messages_path: Path) -> dict[str, str]:
    months: dict[str, str] = {}
    with messages_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            cid = row["conversation_id"]
            if cid not in months:
                months[cid] = month_from_iso(row["conversation_create_time"])
    return months


def count_message_records(messages_path: Path) -> tuple[int, int, int]:
    total = 0
    current_path = 0
    conversation_ids: set[str] = set()
    with messages_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            total += 1
            conversation_ids.add(row["conversation_id"])
            if row["on_current_path"] == "True":
                current_path += 1
    return total, current_path, len(conversation_ids)


def classify_teaching(row: dict[str, str]) -> str:
    arc = row["arc"]
    roles = set(roles_from_trail(row))
    risks = risk_set(row["risk_labels"])
    if "prior_identity_stickiness" in risks:
        return "unclear"
    if arc == "life_to_architecture":
        return "pressure_conversion"
    if arc == "curiosity_to_system":
        return "orientation"
    if arc == "symbol_to_tool":
        return "tool_externalization"
    if arc == "pressure_to_boundary":
        return "boundary_emergence"
    if arc in {"tools_to_continuity", "identity_to_cartography"}:
        return "continuity_formation"
    if "boundary_safety" in roles:
        return "boundary_emergence"
    if "memory_continuity" in roles:
        return "continuity_formation"
    return "unclear"


def select_trails_by_arc(trails: list[dict[str, str]], per_arc: int = 25) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    by_arc: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for row in trails:
        by_arc[row["arc"]].append(row)
    for arc, rows in sorted(by_arc.items()):
        rows.sort(key=lambda row: (-parse_int(row["score"]), row["title"], parse_int(row["start_ordinal"])))
        for rank, row in enumerate(rows[:per_arc], 1):
            selected.append(
                {
                    "arc": arc,
                    "arc_rank": rank,
                    "interpretation": classify_teaching(row),
                    "score": parse_int(row["score"]),
                    "conversation_id": row["conversation_id"],
                    "title": row["title"],
                    "start_node_id": row["start_node_id"],
                    "end_node_id": row["end_node_id"],
                    "start_ordinal": row["start_ordinal"],
                    "end_ordinal": row["end_ordinal"],
                    "span_count": row["span_count"],
                    "message_count": row["message_count"],
                    "roles": row["roles"],
                    "risk_labels": row["risk_labels"],
                    "bounded_preview": bounded(row["preview"]),
                    "review_status": "unreviewed",
                }
            )
    selected.sort(key=lambda row: (row["arc"], row["arc_rank"]))
    return selected


def span_sequences(spans: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_conversation: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for row in spans:
        by_conversation[row["conversation_id"]].append(row)
    for rows in by_conversation.values():
        rows.sort(key=lambda row: parse_int(row["start_ordinal"]))
    return by_conversation


def signal_roles(rows: list[dict[str, str]]) -> list[str]:
    return [row["braid_role"] for row in rows if row["braid_role"] != "unclassified"]


def transition_matrix(by_conversation: dict[str, list[dict[str, str]]]) -> tuple[list[dict[str, Any]], collections.Counter]:
    counts: collections.Counter[tuple[str, str]] = collections.Counter()
    for rows in by_conversation.values():
        roles = signal_roles(rows)
        counts.update(zip(roles, roles[1:]))
    all_roles = sorted({role for pair in counts for role in pair})
    matrix_rows: list[dict[str, Any]] = []
    for source in all_roles:
        total = sum(count for (src, _), count in counts.items() if src == source)
        for target in all_roles:
            count = counts[(source, target)]
            if count:
                matrix_rows.append(
                    {
                        "from_role": source,
                        "to_role": target,
                        "count": count,
                        "from_role_probability": round(count / total, 6) if total else 0,
                    }
                )
    matrix_rows.sort(key=lambda row: (-row["count"], row["from_role"], row["to_role"]))
    return matrix_rows, counts


def role_ngrams(by_conversation: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
    counts: collections.Counter[tuple[str, ...]] = collections.Counter()
    for rows in by_conversation.values():
        roles = signal_roles(rows)
        for n in (3, 4, 5):
            for index in range(len(roles) - n + 1):
                counts[tuple(roles[index : index + n])] += 1
    output = [
        {"n": len(seq), "sequence": " -> ".join(seq), "count": count}
        for seq, count in counts.most_common()
    ]
    return output


def is_subsequence(pattern: list[str], roles: list[str]) -> bool:
    cursor = 0
    for role in roles:
        if cursor < len(pattern) and role == pattern[cursor]:
            cursor += 1
    return cursor == len(pattern)


def count_arc_windows(roles: list[str], pattern: list[str], max_window: int = 18) -> int:
    count = 0
    for start in range(len(roles)):
        for end in range(start + len(pattern), min(len(roles), start + max_window) + 1):
            if is_subsequence(pattern, roles[start:end]):
                count += 1
                break
    return count


def shuffled_arc_baseline(
    by_conversation: dict[str, list[dict[str, str]]], iterations: int = 10
) -> dict[str, dict[str, float]]:
    observed = {arc: 0 for arc in TARGET_ARCS}
    baseline_totals = {arc: 0 for arc in TARGET_ARCS}
    rng = random.Random(260526)
    for rows in by_conversation.values():
        roles = signal_roles(rows)
        for arc, pattern in TARGET_ARCS.items():
            observed[arc] += count_arc_windows(roles, pattern)
        for _ in range(iterations):
            shuffled = roles[:]
            rng.shuffle(shuffled)
            for arc, pattern in TARGET_ARCS.items():
                baseline_totals[arc] += count_arc_windows(shuffled, pattern)
    return {
        arc: {
            "observed": observed[arc],
            "baseline_mean": baseline_totals[arc] / iterations,
            "observed_over_baseline": round(
                observed[arc] / (baseline_totals[arc] / iterations), 4
            )
            if baseline_totals[arc]
            else 0,
        }
        for arc in TARGET_ARCS
    }


def conversation_scores(
    by_conversation: dict[str, list[dict[str, str]]],
    trails: list[dict[str, str]],
    months: dict[str, str],
) -> list[dict[str, Any]]:
    trail_counts: collections.Counter[str] = collections.Counter(row["conversation_id"] for row in trails)
    rows: list[dict[str, Any]] = []
    for cid, spans in by_conversation.items():
        roles = signal_roles(spans)
        role_counts = collections.Counter(roles)
        loop_hits = sum(role_counts[role] for role in LOOP_ROLES)
        transitions = max(0, len(roles) - 1)
        arc_counts = {
            arc: count_arc_windows(roles, pattern)
            for arc, pattern in TARGET_ARCS.items()
        }
        score = (
            loop_hits
            + sum(arc_counts.values()) * 2
            + trail_counts[cid] * 3
            + role_counts["creative_symbolic"]
        )
        rows.append(
            {
                "conversation_id": cid,
                "title": spans[0]["title"] if spans else "",
                "month": months.get(cid, "unknown"),
                "signal_span_count": len(roles),
                "loop_role_hits": loop_hits,
                "transition_count": transitions,
                "trail_count": trail_counts[cid],
                "evidence_score": score,
                "top_role": role_counts.most_common(1)[0][0] if role_counts else "",
                "role_counts_json": json.dumps(dict(role_counts.most_common()), sort_keys=True),
                "arc_counts_json": json.dumps(arc_counts, sort_keys=True),
            }
        )
    rows.sort(key=lambda row: (-row["evidence_score"], row["title"]))
    return rows


def monthly_summary(
    by_conversation: dict[str, list[dict[str, str]]],
    trails: list[dict[str, str]],
    months: dict[str, str],
) -> list[dict[str, Any]]:
    month_data: dict[str, dict[str, Any]] = collections.defaultdict(
        lambda: {
            "conversation_ids": set(),
            "role_counts": collections.Counter(),
            "risk_counts": collections.Counter(),
            "arc_counts": collections.Counter(),
            "signal_spans": 0,
            "messages": 0,
        }
    )
    for cid, spans in by_conversation.items():
        month = months.get(cid, "unknown")
        data = month_data[month]
        data["conversation_ids"].add(cid)
        for span in spans:
            role = span["braid_role"]
            if role != "unclassified":
                data["role_counts"][role] += 1
                data["signal_spans"] += 1
                data["messages"] += parse_int(span["message_count"])
            for risk in risk_set(span["risk_labels"]):
                data["risk_counts"][risk] += 1
    for trail in trails:
        month_data[months.get(trail["conversation_id"], "unknown")]["arc_counts"][trail["arc"]] += 1
    for cid, month in months.items():
        month_data[month]["conversation_ids"].add(cid)

    rows: list[dict[str, Any]] = []
    for month, data in sorted(month_data.items()):
        role_counts: collections.Counter[str] = data["role_counts"]
        arc_counts: collections.Counter[str] = data["arc_counts"]
        rows.append(
            {
                "month": month,
                "period": period_for_month(month),
                "conversation_count": len(data["conversation_ids"]),
                "signal_span_count": data["signal_spans"],
                "signal_message_count": data["messages"],
                "top_role": role_counts.most_common(1)[0][0] if role_counts else "",
                "role_counts_json": json.dumps(dict(role_counts.most_common()), sort_keys=True),
                "arc_counts_json": json.dumps(dict(arc_counts.most_common()), sort_keys=True),
                "risk_counts_json": json.dumps(dict(data["risk_counts"].most_common()), sort_keys=True),
                "symbolic_to_architecture_pressure": arc_counts["life_to_architecture"]
                + arc_counts["curiosity_to_system"]
                + arc_counts["symbol_to_tool"],
                "boundary_continuity_pressure": arc_counts["pressure_to_boundary"]
                + arc_counts["tools_to_continuity"]
                + arc_counts["identity_to_cartography"],
            }
        )
    return rows


def write_human_trails(path: Path, selected: list[dict[str, Any]]) -> None:
    lines = [
        "# Human-Readable Braid Trails",
        "",
        "Bounded trail previews for review. These are formation-path candidates, not training examples.",
        "",
    ]
    for arc in sorted({row["arc"] for row in selected}):
        lines.extend([f"## {arc}", ""])
        for row in [item for item in selected if item["arc"] == arc][:10]:
            lines.extend(
                [
                    f"### {row['arc_rank']}. {row['title']}",
                    "",
                    f"- Interpretation: `{row['interpretation']}`",
                    f"- Score: `{row['score']}`",
                    f"- Conversation: `{row['conversation_id']}`",
                    f"- Node range: `{row['start_node_id']}` -> `{row['end_node_id']}`",
                    f"- Ordinal range: `{row['start_ordinal']}` -> `{row['end_ordinal']}`",
                    f"- Risks: `{row['risk_labels'] or 'none'}`",
                    f"- Roles: `{row['roles']}`",
                    "",
                    f"> {row['bounded_preview']}",
                    "",
                ]
            )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_quant_report(
    path: Path,
    matrix_rows: list[dict[str, Any]],
    ngrams: list[dict[str, Any]],
    baseline: dict[str, dict[str, float]],
    scores: list[dict[str, Any]],
    totals: dict[str, Any],
) -> None:
    lines = [
        "# Quantitative Braid Report",
        "",
        "This report tests whether the orientation-to-architecture loop appears as repeated role transitions rather than isolated keywords.",
        "",
        "## Reconciliation",
        "",
        f"- Mapped messages: {totals['mapped_messages']}",
        f"- Current-path messages: {totals['current_path_messages']}",
        f"- Existing trail arcs: {totals['trail_count']}",
        f"- Conversations: {totals['conversation_count']}",
        "",
        "## Target Arc Baseline",
        "",
    ]
    for arc, values in baseline.items():
        lines.append(
            f"- {arc}: observed={values['observed']}, shuffled_mean={values['baseline_mean']:.1f}, ratio={values['observed_over_baseline']}"
        )
    lines.extend(["", "## Top Role Transitions", ""])
    for row in matrix_rows[:20]:
        lines.append(
            f"- {row['from_role']} -> {row['to_role']}: {row['count']} ({row['from_role_probability']})"
        )
    lines.extend(["", "## Top Role N-Grams", ""])
    for row in ngrams[:25]:
        lines.append(f"- {row['sequence']}: {row['count']}")
    lines.extend(["", "## Highest Evidence Conversations", ""])
    for row in scores[:15]:
        lines.append(
            f"- {row['title']}: score={row['evidence_score']}, trails={row['trail_count']}, top_role={row['top_role']}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_chrono_report(path: Path, monthly_rows: list[dict[str, Any]], scores: list[dict[str, Any]]) -> None:
    period_counts: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for row in monthly_rows:
        period_counts[row["period"]]["conversation_count"] += parse_int(str(row["conversation_count"]))
        period_counts[row["period"]]["symbolic_to_architecture_pressure"] += parse_int(
            str(row["symbolic_to_architecture_pressure"])
        )
        period_counts[row["period"]]["boundary_continuity_pressure"] += parse_int(
            str(row["boundary_continuity_pressure"])
        )
    lines = [
        "# Chronological Formation Report",
        "",
        "This report follows how the braid changes over conversation creation time.",
        "",
        "## Monthly Formation",
        "",
    ]
    for row in monthly_rows:
        lines.append(
            f"- {row['month']} ({row['period']}): conversations={row['conversation_count']}, top_role={row['top_role']}, symbolic/architecture={row['symbolic_to_architecture_pressure']}, boundary/continuity={row['boundary_continuity_pressure']}"
        )
    lines.extend(["", "## Formation Periods", ""])
    for period, counts in period_counts.items():
        lines.append(
            f"- {period}: conversations={counts['conversation_count']}, symbolic/architecture={counts['symbolic_to_architecture_pressure']}, boundary/continuity={counts['boundary_continuity_pressure']}"
        )
    lines.extend(["", "## Latest High-Scoring Conversations", ""])
    latest = sorted(scores, key=lambda row: (row["month"], row["evidence_score"]), reverse=True)[:15]
    for row in latest:
        lines.append(f"- {row['month']} | {row['title']}: score={row['evidence_score']}, trails={row['trail_count']}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--baseline-iterations", type=int, default=10)
    args = parser.parse_args()

    braid_dir = args.workspace / "analysis" / "braid_20260526"
    trail_dir = args.workspace / "analysis" / "braid_trails_20260526"
    messages_path = braid_dir / "braid_messages.csv"
    spans_path = braid_dir / "braid_spans.csv"
    trails_path = trail_dir / "braid_trails.csv"
    summaries_path = trail_dir / "conversation_braid_summaries.csv"

    spans = read_csv(spans_path)
    trails = read_csv(trails_path)
    conversation_summaries = read_csv(summaries_path)
    months = load_conversation_months(messages_path)
    by_conversation = span_sequences(spans)

    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    selected_trails = select_trails_by_arc(trails, per_arc=25)
    matrix_rows, transition_counts = transition_matrix(by_conversation)
    ngrams = role_ngrams(by_conversation)
    baseline = shuffled_arc_baseline(by_conversation, iterations=args.baseline_iterations)
    scores = conversation_scores(by_conversation, trails, months)
    monthly_rows = monthly_summary(by_conversation, trails, months)

    write_csv(out / "trail_review_queue.csv", selected_trails)
    write_csv(out / "transition_matrix.csv", matrix_rows)
    write_csv(out / "role_ngram_counts.csv", ngrams)
    write_csv(out / "monthly_braid_summary.csv", monthly_rows)
    write_csv(out / "conversation_evidence_scores.csv", scores)
    write_human_trails(out / "human_readable_trails.md", selected_trails)

    mapped_messages, current_path_messages, conversation_count = count_message_records(messages_path)
    totals = {
        "mapped_messages": mapped_messages,
        "current_path_messages": current_path_messages,
        "trail_count": len(trails),
        "conversation_count": conversation_count,
        "conversation_with_signal_summaries": len(conversation_summaries),
    }

    write_quant_report(out / "quantitative_braid_report.md", matrix_rows, ngrams, baseline, scores, totals)
    write_chrono_report(out / "chronological_formation_report.md", monthly_rows, scores)

    summary = {
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        "inputs": {
            "braid_messages": str(messages_path),
            "braid_spans": str(spans_path),
            "braid_trails": str(trails_path),
            "conversation_braid_summaries": str(summaries_path),
        },
        "totals": totals,
        "selected_trail_count": len(selected_trails),
        "transition_count": sum(transition_counts.values()),
        "ngram_count": len(ngrams),
        "baseline_iterations": args.baseline_iterations,
        "target_arc_baseline": baseline,
        "top_conversations": scores[:20],
        "monthly_rows": monthly_rows,
        "boundaries": {
            "preserve_everything": True,
            "direct_training": False,
            "memory_injection": False,
            "prior_names_as_provenance_only": True,
        },
    }
    (out / "research_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
