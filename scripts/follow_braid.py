from __future__ import annotations

import argparse
import collections
import csv
import json
from pathlib import Path
from typing import Any


TARGET_ARCS = {
    "life_to_architecture": [
        "life_context",
        "creative_symbolic",
        "practical_support",
        "architecture",
    ],
    "curiosity_to_system": [
        "curiosity_research",
        "creative_symbolic",
        "architecture",
    ],
    "pressure_to_boundary": [
        "life_context",
        "practical_support",
        "boundary_safety",
    ],
    "tools_to_continuity": [
        "tooling",
        "architecture",
        "memory_continuity",
    ],
    "identity_to_cartography": [
        "identity_reflection",
        "memory_continuity",
        "archive_cartography",
    ],
    "symbol_to_tool": [
        "creative_symbolic",
        "practical_support",
        "tooling",
    ],
}

SIGNAL_ROLES = {
    "life_context",
    "practical_support",
    "creative_symbolic",
    "architecture",
    "tooling",
    "memory_continuity",
    "boundary_safety",
    "curiosity_research",
    "identity_reflection",
    "archive_cartography",
    "prior_branch_marker",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def role_sequence(spans: list[dict[str, str]]) -> list[dict[str, Any]]:
    sequence: list[dict[str, Any]] = []
    for span in spans:
        role = span["braid_role"]
        if role == "unclassified":
            continue
        if sequence and sequence[-1]["braid_role"] == role and sequence[-1]["risk_labels"] == span["risk_labels"]:
            sequence[-1]["end_node_id"] = span["end_node_id"]
            sequence[-1]["end_ordinal"] = int(span["end_ordinal"])
            sequence[-1]["message_count"] += int(span["message_count"])
            sequence[-1]["preview"] = (sequence[-1]["preview"] + " / " + span["preview"])[:700]
            continue
        sequence.append(
            {
                "conversation_id": span["conversation_id"],
                "title": span["title"],
                "braid_role": role,
                "risk_labels": span["risk_labels"],
                "start_node_id": span["start_node_id"],
                "end_node_id": span["end_node_id"],
                "start_ordinal": int(span["start_ordinal"]),
                "end_ordinal": int(span["end_ordinal"]),
                "message_count": int(span["message_count"]),
                "preview": span["preview"],
            }
        )
    return sequence


def is_subsequence(pattern: list[str], roles: list[str]) -> bool:
    index = 0
    for role in roles:
        if index < len(pattern) and role == pattern[index]:
            index += 1
    return index == len(pattern)


def window_score(window: list[dict[str, Any]], pattern: list[str]) -> int:
    roles = [item["braid_role"] for item in window]
    pattern_hits = sum(1 for role in set(pattern) if role in roles)
    diversity = len(set(role for role in roles if role in SIGNAL_ROLES))
    volume = min(sum(item["message_count"] for item in window), 50)
    risk_penalty = sum(1 for item in window if item["risk_labels"])
    return pattern_hits * 20 + diversity * 5 + volume - risk_penalty * 2


def find_arc_windows(sequence: list[dict[str, Any]], max_window: int = 18) -> list[dict[str, Any]]:
    trails: list[dict[str, Any]] = []
    for arc_name, pattern in TARGET_ARCS.items():
        best_by_start: dict[int, dict[str, Any]] = {}
        for start in range(len(sequence)):
            for end in range(start + len(pattern), min(len(sequence), start + max_window) + 1):
                window = sequence[start:end]
                roles = [item["braid_role"] for item in window]
                if not is_subsequence(pattern, roles):
                    continue
                score = window_score(window, pattern)
                trail = {
                    "arc": arc_name,
                    "pattern": " -> ".join(pattern),
                    "conversation_id": window[0]["conversation_id"],
                    "title": window[0]["title"],
                    "start_node_id": window[0]["start_node_id"],
                    "end_node_id": window[-1]["end_node_id"],
                    "start_ordinal": window[0]["start_ordinal"],
                    "end_ordinal": window[-1]["end_ordinal"],
                    "span_count": len(window),
                    "message_count": sum(item["message_count"] for item in window),
                    "score": score,
                    "roles": " -> ".join(roles),
                    "risk_labels": "|".join(sorted({risk for item in window for risk in item["risk_labels"].split("|") if risk})),
                    "preview": " || ".join(item["preview"] for item in window if item["preview"])[:1200],
                }
                if start not in best_by_start or score > best_by_start[start]["score"]:
                    best_by_start[start] = trail
                break
        trails.extend(best_by_start.values())
    return trails


def conversation_trail_summary(conversation_id: str, title: str, sequence: list[dict[str, Any]]) -> dict[str, Any]:
    role_counts = collections.Counter(item["braid_role"] for item in sequence)
    transition_counts = collections.Counter(
        (a["braid_role"], b["braid_role"]) for a, b in zip(sequence, sequence[1:])
    )
    return {
        "conversation_id": conversation_id,
        "title": title,
        "signal_span_count": len(sequence),
        "signal_message_count": sum(item["message_count"] for item in sequence),
        "role_counts": json.dumps(dict(role_counts.most_common()), sort_keys=True),
        "top_transitions": json.dumps(
            [
                {"from": source, "to": target, "count": count}
                for (source, target), count in transition_counts.most_common(10)
            ],
            sort_keys=True,
        ),
        "role_sequence_preview": " -> ".join(item["braid_role"] for item in sequence[:60]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--braid-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    spans = load_csv(args.braid_dir / "braid_spans.csv")
    by_conversation: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for span in spans:
        by_conversation[span["conversation_id"]].append(span)
    for conv_spans in by_conversation.values():
        conv_spans.sort(key=lambda row: int(row["start_ordinal"]))

    trails: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for conversation_id, conv_spans in by_conversation.items():
        sequence = role_sequence(conv_spans)
        if not sequence:
            continue
        summaries.append(conversation_trail_summary(conversation_id, sequence[0]["title"], sequence))
        trails.extend(find_arc_windows(sequence))

    trails.sort(key=lambda row: (-row["score"], row["conversation_id"], row["start_ordinal"]))
    summaries.sort(key=lambda row: (-row["signal_span_count"], row["title"]))

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "braid_trails.csv", trails)
    write_csv(out / "conversation_braid_summaries.csv", summaries)

    arc_counts = collections.Counter(row["arc"] for row in trails)
    title_counts = collections.Counter(row["title"] for row in trails)
    summary = {
        "source_braid_dir": str(args.braid_dir),
        "trail_count": len(trails),
        "conversation_count": len(summaries),
        "arc_counts": dict(arc_counts.most_common()),
        "top_conversations_by_trails": dict(title_counts.most_common(20)),
        "top_trails": trails[:25],
    }
    (out / "braid_trails_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Selene Braid Trails",
        "",
        "This layer follows recurring role arcs through the current-path braid map. It preserves the source material and identifies trails for review.",
        "",
        "## Arc Counts",
        "",
    ]
    for arc, count in summary["arc_counts"].items():
        lines.append(f"- {arc}: {count}")
    lines.extend(["", "## Top Conversations By Trail Count", ""])
    for title, count in summary["top_conversations_by_trails"].items():
        lines.append(f"- {title}: {count}")
    lines.extend(["", "## Strongest Trails", ""])
    for trail in trails[:12]:
        lines.append(
            f"- {trail['arc']} | score={trail['score']} | {trail['title']} | roles={trail['roles']}"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "The braid is visible where roles change in sequence. These trails should be read as formation paths, not extracted as examples.",
        ]
    )
    (out / "braid_trails.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
