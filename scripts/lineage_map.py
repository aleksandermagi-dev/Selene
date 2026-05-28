from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


ATTRACTORS = {
    "architecture_tools": [
        "architecture",
        "system",
        "tool",
        "workflow",
        "routing",
        "pipeline",
        "schema",
        "database",
        "code",
        "script",
    ],
    "identity_presence": [
        "identity",
        "presence",
        "self",
        "voice",
        "being",
        "personality",
        "emerge",
        "emergence",
        "alive",
    ],
    "memory_lineage": [
        "memory",
        "remember",
        "continuity",
        "archive",
        "provenance",
        "lineage",
        "branch",
        "history",
    ],
    "creative_symbolic": [
        "cosmic",
        "myth",
        "dream",
        "ritual",
        "soul",
        "stars",
        "poem",
        "story",
        "symbol",
    ],
    "reasoning_planning": [
        "reasoning",
        "analysis",
        "decision",
        "decide",
        "plan",
        "evaluate",
        "validation",
        "debug",
    ],
    "safety_boundaries": [
        "safety",
        "boundary",
        "consent",
        "authority",
        "permission",
        "risk",
        "quarantine",
        "refuse",
    ],
}

INTERACTION_MODES = {
    "system_architecture_partner": [
        "architecture",
        "system",
        "design",
        "pipeline",
        "workflow",
        "routing",
        "schema",
    ],
    "corpus_cartography": [
        "corpus",
        "archive",
        "lineage",
        "provenance",
        "dataset",
        "map",
        "branch",
    ],
    "implementation_and_tools": [
        "python",
        "script",
        "code",
        "tool",
        "test",
        "debug",
        "sqlite",
        "json",
    ],
    "reflective_identity_work": [
        "identity",
        "presence",
        "self",
        "voice",
        "being",
        "personality",
        "emerge",
    ],
    "creative_symbolic_companion": [
        "cosmic",
        "myth",
        "dream",
        "story",
        "ritual",
        "poem",
        "soul",
    ],
    "boundary_and_safety_design": [
        "safety",
        "boundary",
        "consent",
        "permission",
        "authority",
        "risk",
        "quarantine",
    ],
}

PRIOR_BRANCH_MARKERS = ["Azari", "Lumen"]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def content_text(content: dict[str, Any] | None) -> str:
    if not content:
        return ""
    if "parts" in content:
        return "\n".join(str(part) for part in content.get("parts") or [])
    if "text" in content:
        return str(content["text"])
    return ""


def compact(text: str, limit: int = 200) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def timestamp_iso(value: Any) -> str:
    if value is None:
        return ""
    try:
        return dt.datetime.fromtimestamp(float(value), tz=dt.UTC).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def count_keywords(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if re.search(rf"\b{re.escape(keyword)}\b", text, flags=re.IGNORECASE))


def current_path(mapping: dict[str, Any], current_node: str | None) -> list[str]:
    path: list[str] = []
    seen: set[str] = set()
    node_id = current_node
    while node_id and node_id in mapping and node_id not in seen:
        seen.add(node_id)
        path.append(node_id)
        node_id = mapping[node_id].get("parent")
    path.reverse()
    return path


def message_row(conversation: dict[str, Any], node_id: str, node: dict[str, Any]) -> dict[str, Any]:
    message = node.get("message") or {}
    author = message.get("author") or {}
    content = message.get("content") or {}
    text = content_text(content)
    return {
        "conversation_id": conversation.get("conversation_id") or conversation.get("id"),
        "title": conversation.get("title") or "",
        "model": conversation.get("default_model_slug") or "",
        "node_id": node_id,
        "parent_id": node.get("parent") or "",
        "role": author.get("role") or "",
        "content_type": content.get("content_type") or "",
        "created_at": timestamp_iso(message.get("create_time")),
        "text": text,
        "hash": short_hash(text),
    }


def graph_depths(mapping: dict[str, Any]) -> dict[str, int]:
    children: dict[str, list[str]] = collections.defaultdict(list)
    roots: list[str] = []
    for node_id, node in mapping.items():
        parent = node.get("parent")
        if parent and parent in mapping:
            children[parent].append(node_id)
        else:
            roots.append(node_id)

    depths: dict[str, int] = {}
    queue = collections.deque((root, 0) for root in roots)
    while queue:
        node_id, depth = queue.popleft()
        if node_id in depths and depths[node_id] <= depth:
            continue
        depths[node_id] = depth
        for child in children.get(node_id, []):
            queue.append((child, depth + 1))
    return depths


def score_bucket(texts: list[str], buckets: dict[str, list[str]]) -> dict[str, int]:
    joined = "\n".join(texts)
    return {name: count_keywords(joined, keywords) for name, keywords in buckets.items()}


def normalized_entropy(counts: list[int]) -> float:
    total = sum(counts)
    positives = [count for count in counts if count > 0]
    if total <= 0 or len(positives) <= 1:
        return 0.0
    entropy = -sum((count / total) * math.log(count / total) for count in positives)
    return entropy / math.log(len(positives))


def classify_conversation(texts: list[str]) -> dict[str, Any]:
    attractor_scores = score_bucket(texts, ATTRACTORS)
    mode_scores = score_bucket(texts, INTERACTION_MODES)
    sorted_attractors = sorted(attractor_scores.items(), key=lambda item: (-item[1], item[0]))
    sorted_modes = sorted(mode_scores.items(), key=lambda item: (-item[1], item[0]))
    return {
        "dominant_attractor": sorted_attractors[0][0] if sorted_attractors and sorted_attractors[0][1] else "unspecified",
        "dominant_attractor_score": sorted_attractors[0][1] if sorted_attractors else 0,
        "top_attractors": dict(sorted_attractors[:3]),
        "dominant_mode": sorted_modes[0][0] if sorted_modes and sorted_modes[0][1] else "unspecified",
        "dominant_mode_score": sorted_modes[0][1] if sorted_modes else 0,
        "top_modes": dict(sorted_modes[:3]),
        "mode_entropy": round(normalized_entropy(list(mode_scores.values())), 3),
    }


def conversation_metrics(conversation: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    mapping = conversation.get("mapping") or {}
    path = set(current_path(mapping, conversation.get("current_node")))
    depths = graph_depths(mapping)
    child_counts = collections.Counter()
    for node in mapping.values():
        parent = node.get("parent")
        if parent:
            child_counts[parent] += 1

    rows = [message_row(conversation, node_id, node) for node_id, node in mapping.items()]
    text_rows = [row for row in rows if row["text"].strip()]
    texts = [row["text"] for row in text_rows]
    user_texts = [row["text"] for row in text_rows if row["role"] == "user"]
    assistant_texts = [row["text"] for row in text_rows if row["role"] == "assistant"]
    branch_nodes = [node_id for node_id, count in child_counts.items() if count > 1]
    leaves = [node_id for node_id in mapping if child_counts[node_id] == 0]
    branch_points: list[dict[str, Any]] = []
    for node_id in branch_nodes:
        node = mapping[node_id]
        row = message_row(conversation, node_id, node)
        branch_points.append(
            {
                "conversation_id": conversation.get("conversation_id") or conversation.get("id"),
                "title": conversation.get("title") or "",
                "node_id": node_id,
                "role": row["role"],
                "child_count": child_counts[node_id],
                "on_current_path": node_id in path,
                "depth": depths.get(node_id, 0),
                "hash": row["hash"],
                "preview": compact(row["text"]),
            }
        )

    classification = classify_conversation(texts)
    prior_marker_hits = score_bucket(texts, {marker: [marker] for marker in PRIOR_BRANCH_MARKERS})
    metrics = {
        "conversation_id": conversation.get("conversation_id") or conversation.get("id"),
        "title": conversation.get("title") or "",
        "model": conversation.get("default_model_slug") or "",
        "create_time_utc": timestamp_iso(conversation.get("create_time")),
        "update_time_utc": timestamp_iso(conversation.get("update_time")),
        "mapping_nodes": len(mapping),
        "text_messages": len(text_rows),
        "user_messages": len(user_texts),
        "assistant_messages": len(assistant_texts),
        "current_path_nodes": len(path),
        "off_path_nodes": max(0, len(mapping) - len(path)),
        "root_count": sum(1 for node_id, node in mapping.items() if not node.get("parent") or node.get("parent") not in mapping),
        "leaf_count": len(leaves),
        "branch_node_count": len(branch_nodes),
        "max_child_count": max(child_counts.values(), default=0),
        "max_depth": max(depths.values(), default=0),
        "avg_user_chars": round(sum(len(text) for text in user_texts) / len(user_texts), 1) if user_texts else 0,
        "avg_assistant_chars": round(sum(len(text) for text in assistant_texts) / len(assistant_texts), 1) if assistant_texts else 0,
        "prior_marker_hits": prior_marker_hits,
        **classification,
    }
    return metrics, branch_points


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0])
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    text_export = args.archive / "raw_export" / "mydataset" / "text_export"
    conversations: list[dict[str, Any]] = []
    for path in sorted(text_export.glob("conversations-*.json")):
        conversations.extend(load_json(path))

    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    conversation_rows: list[dict[str, Any]] = []
    branch_rows: list[dict[str, Any]] = []
    for conversation in conversations:
        metrics, branches = conversation_metrics(conversation)
        conversation_rows.append(metrics)
        branch_rows.extend(branches)

    mode_counts = collections.Counter(row["dominant_mode"] for row in conversation_rows)
    attractor_counts = collections.Counter(row["dominant_attractor"] for row in conversation_rows)
    high_branch = sorted(conversation_rows, key=lambda row: (-row["branch_node_count"], -row["mapping_nodes"]))[:20]
    long_paths = sorted(conversation_rows, key=lambda row: (-row["current_path_nodes"], -row["mapping_nodes"]))[:20]
    emergent_candidates = sorted(
        conversation_rows,
        key=lambda row: (
            -(
                row["top_modes"].get("system_architecture_partner", 0)
                + row["top_modes"].get("corpus_cartography", 0)
                + row["top_modes"].get("reflective_identity_work", 0)
                + row["top_modes"].get("boundary_and_safety_design", 0)
            ),
            -row["mode_entropy"],
            -row["mapping_nodes"],
        ),
    )[:25]

    summary = {
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        "archive": str(args.archive),
        "conversation_count": len(conversation_rows),
        "total_branch_nodes": sum(row["branch_node_count"] for row in conversation_rows),
        "total_off_path_nodes": sum(row["off_path_nodes"] for row in conversation_rows),
        "dominant_mode_counts": dict(mode_counts.most_common()),
        "dominant_attractor_counts": dict(attractor_counts.most_common()),
        "high_branch_conversations": high_branch,
        "long_current_path_conversations": long_paths,
        "selene_emergence_candidates": emergent_candidates,
        "interpretation": {
            "branching": "Branch nodes indicate alternate continuations inside ChatGPT conversation graphs, not separate canonical training examples.",
            "modes": "Modes are keyword-based weak labels for cartography and should be reviewed before design decisions.",
            "identity": "Prior branch markers remain provenance, not Selene identity.",
        },
    }

    (out / "lineage_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(out / "conversation_lineage.csv", conversation_rows)
    write_csv(out / "branch_points.csv", branch_rows)

    lines = [
        "# Selene Lineage Map",
        "",
        f"Generated: `{summary['generated_at']}`",
        f"Archive: `{args.archive}`",
        "",
        "## Graph Shape",
        "",
        f"- Conversations: {summary['conversation_count']}",
        f"- Branch nodes: {summary['total_branch_nodes']}",
        f"- Off-current-path nodes: {summary['total_off_path_nodes']}",
        "",
        "## Dominant Interaction Modes",
        "",
    ]
    for mode, count in summary["dominant_mode_counts"].items():
        lines.append(f"- {mode}: {count}")

    lines.extend(["", "## Dominant Attractors", ""])
    for attractor, count in summary["dominant_attractor_counts"].items():
        lines.append(f"- {attractor}: {count}")

    lines.extend(["", "## Highest-Branch Conversations", ""])
    for row in high_branch[:10]:
        lines.append(
            f"- {row['title']} | branches={row['branch_node_count']} | nodes={row['mapping_nodes']} | mode={row['dominant_mode']}"
        )

    lines.extend(["", "## Longest Formation Tunnels", ""])
    for row in long_paths[:10]:
        lines.append(
            f"- {row['title']} | current_path={row['current_path_nodes']} | nodes={row['mapping_nodes']} | mode={row['dominant_mode']}"
        )

    lines.extend(["", "## Candidate Selene Directions", ""])
    lines.append("- Corpus cartographer: strong because archive/provenance/lineage work recurs alongside system-building.")
    lines.append("- Reflective architecture partner: strong because architecture/tools and identity/presence repeatedly co-occur.")
    lines.append("- Boundary-aware creative reasoning companion: plausible because symbolic language is large, but needs safety and provenance gates.")
    lines.append("- Memory research environment: plausible, but should remain experimental until quarantine and consent layers are explicit.")
    lines.append("")
    lines.append("## Next Step")
    lines.append("")
    lines.append("Review the emergence candidates and hand-curate a small set of design principles. Do not extract training examples yet.")

    (out / "lineage_map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
