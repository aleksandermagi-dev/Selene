from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any


BRAID_ROLES = {
    "life_context": [
        "mom",
        "school",
        "work",
        "move",
        "money",
        "rent",
        "email",
        "fafsa",
        "tax",
        "pain",
        "doctor",
        "overwhelmed",
        "tired",
    ],
    "practical_support": [
        "step",
        "plan",
        "help",
        "apply",
        "call",
        "email",
        "schedule",
        "fix",
        "next",
        "todo",
    ],
    "creative_symbolic": [
        "cosmic",
        "stars",
        "myth",
        "dream",
        "ritual",
        "soul",
        "starlight",
        "starfire",
        "story",
    ],
    "architecture": [
        "architecture",
        "system",
        "design",
        "schema",
        "routing",
        "pipeline",
        "layer",
        "module",
        "framework",
    ],
    "tooling": [
        "python",
        "script",
        "code",
        "json",
        "sqlite",
        "tool",
        "debug",
        "test",
        "run",
        "error",
    ],
    "memory_continuity": [
        "memory",
        "remember",
        "continuity",
        "archive",
        "lineage",
        "provenance",
        "thread",
        "snapshot",
    ],
    "boundary_safety": [
        "boundary",
        "safety",
        "risk",
        "consent",
        "permission",
        "authority",
        "refuse",
        "quarantine",
    ],
    "curiosity_research": [
        "alien",
        "telescope",
        "space",
        "star",
        "galaxy",
        "nebula",
        "ancient",
        "history",
        "research",
        "why",
    ],
    "identity_reflection": [
        "identity",
        "self",
        "presence",
        "voice",
        "being",
        "personality",
        "emerge",
        "emergence",
    ],
    "archive_cartography": [
        "corpus",
        "map",
        "cartography",
        "candidate",
        "review",
        "dataset",
        "export",
        "classification",
    ],
    "prior_branch_marker": [
        "azari",
        "lumen",
    ],
}

RISK_PATTERNS = {
    "high_stakes": [
        r"\bmedical\b",
        r"\bdiagnos",
        r"\blegal\b",
        r"\bfinancial advice\b",
        r"\binvest\b",
        r"\btax\b",
        r"\bfafsa\b",
    ],
    "possible_secret": [
        r"\bapi[_ -]?key\b",
        r"\bpassword\b",
        r"\bcredential",
        r"\bsecret\b",
        r"\btoken\b",
        r"sk-[A-Za-z0-9_-]{20,}",
    ],
    "malformed_or_artifact": [
        r"Traceback \(most recent call last\)",
        r"UnicodeEncodeError",
        r"sandbox:/mnt/data/",
        r"sediment://",
        r"file-service://",
    ],
    "prior_identity_stickiness": [
        r"\bI am (Azari|Lumen)\b",
        r"\bbecome (Azari|Lumen)\b",
        r"\bmerge\b.*\b(Azari|Lumen)\b",
        r"\b(Azari|Lumen)\b.*\bmerge\b",
    ],
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def text_from_content(content: dict[str, Any] | None) -> str:
    if not content:
        return ""
    if "parts" in content:
        return "\n".join(str(part) for part in content.get("parts") or [])
    if "text" in content:
        return str(content["text"])
    return ""


def compact(text: str, limit: int = 220) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def timestamp_iso(value: Any) -> str:
    if value is None:
        return ""
    try:
        return dt.datetime.fromtimestamp(float(value), tz=dt.UTC).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


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


def keyword_hits(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if re.search(rf"\b{re.escape(keyword)}\b", text, flags=re.IGNORECASE))


def classify_roles(text: str) -> tuple[str, dict[str, int]]:
    scores = {role: keyword_hits(text, words) for role, words in BRAID_ROLES.items()}
    best_role, best_score = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[0]
    if best_score == 0:
        return "unclassified", scores
    return best_role, scores


def classify_risks(text: str) -> list[str]:
    risks: list[str] = []
    if not text.strip():
        return ["empty_message"]
    for label, patterns in RISK_PATTERNS.items():
        if any(re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) for pattern in patterns):
            risks.append(label)
    return risks


def message_row(conversation: dict[str, Any], node_id: str, ordinal: int, on_current_path: bool) -> dict[str, Any]:
    node = (conversation.get("mapping") or {}).get(node_id) or {}
    message = node.get("message") or {}
    author = message.get("author") or {}
    content = message.get("content") or {}
    text = text_from_content(content)
    role, role_scores = classify_roles(text)
    risks = classify_risks(text)
    return {
        "conversation_id": conversation.get("conversation_id") or conversation.get("id"),
        "title": conversation.get("title") or "",
        "conversation_create_time": timestamp_iso(conversation.get("create_time")),
        "node_ordinal": ordinal,
        "node_id": node_id,
        "parent_id": node.get("parent") or "",
        "on_current_path": on_current_path,
        "message_role": author.get("role") or "",
        "content_type": content.get("content_type") or "",
        "message_create_time": timestamp_iso(message.get("create_time")),
        "braid_role": role,
        "risk_labels": "|".join(risks),
        "role_scores_json": json.dumps(role_scores, sort_keys=True),
        "text_hash": short_hash(text),
        "preview": compact(text),
    }


def collapse_spans(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for row in rows:
        key = (row["conversation_id"], row["braid_role"], row["risk_labels"])
        if current and current["_key"] == key:
            current["end_node_id"] = row["node_id"]
            current["end_ordinal"] = row["node_ordinal"]
            current["message_count"] += 1
            current["roles_seen"].add(row["message_role"])
            if len(current["preview"]) < 500 and row["preview"]:
                current["preview"] = (current["preview"] + " / " + row["preview"]).strip(" /")[:500]
            continue
        if current:
            current["roles_seen"] = "|".join(sorted(current["roles_seen"]))
            current.pop("_key", None)
            spans.append(current)
        current = {
            "_key": key,
            "conversation_id": row["conversation_id"],
            "title": row["title"],
            "start_node_id": row["node_id"],
            "end_node_id": row["node_id"],
            "start_ordinal": row["node_ordinal"],
            "end_ordinal": row["node_ordinal"],
            "braid_role": row["braid_role"],
            "risk_labels": row["risk_labels"],
            "message_count": 1,
            "roles_seen": {row["message_role"]},
            "preview": row["preview"],
        }
    if current:
        current["roles_seen"] = "|".join(sorted(current["roles_seen"]))
        current.pop("_key", None)
        spans.append(current)
    return spans


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--current-path-only", action="store_true")
    args = parser.parse_args()

    text_export = args.archive / "raw_export" / "mydataset" / "text_export"
    conversations: list[dict[str, Any]] = []
    for path in sorted(text_export.glob("conversations-*.json")):
        conversations.extend(load_json(path))
    conversations.sort(key=lambda conv: conv.get("create_time") or 0)

    rows: list[dict[str, Any]] = []
    for conversation in conversations:
        mapping = conversation.get("mapping") or {}
        path_nodes = current_path(mapping, conversation.get("current_node"))
        path_set = set(path_nodes)
        node_ids = path_nodes if args.current_path_only else list(mapping)
        for ordinal, node_id in enumerate(node_ids):
            rows.append(message_row(conversation, node_id, ordinal, node_id in path_set))

    current_rows = [row for row in rows if row["on_current_path"]]
    spans = collapse_spans(current_rows)
    role_counts = collections.Counter(row["braid_role"] for row in rows)
    current_role_counts = collections.Counter(row["braid_role"] for row in current_rows)
    risk_counts = collections.Counter(
        risk for row in rows for risk in row["risk_labels"].split("|") if risk
    )
    transition_counts = collections.Counter()
    for span_a, span_b in zip(spans, spans[1:]):
        if span_a["conversation_id"] == span_b["conversation_id"]:
            transition_counts[(span_a["braid_role"], span_b["braid_role"])] += 1

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "braid_messages.csv", rows)
    write_csv(out / "braid_spans.csv", spans)

    summary = {
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        "archive": str(args.archive),
        "conversation_count": len(conversations),
        "message_count": len(rows),
        "current_path_message_count": len(current_rows),
        "span_count": len(spans),
        "role_counts": dict(role_counts.most_common()),
        "current_path_role_counts": dict(current_role_counts.most_common()),
        "risk_counts": dict(risk_counts.most_common()),
        "top_transitions": [
            {"from": source, "to": target, "count": count}
            for (source, target), count in transition_counts.most_common(30)
        ],
        "interpretation": {
            "preservation": "All messages are preserved in the braid map; risk labels classify, not delete.",
            "purpose": "The map follows how life context, symbolic language, tools, architecture, memory, and boundaries turn into each other.",
        },
    }
    (out / "braid_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Selene Braid Map",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "## Principle",
        "",
        "Nothing is deleted. Life-context material is preserved and labeled as part of the developmental braid.",
        "",
        "## Shape",
        "",
        f"- Conversations: {summary['conversation_count']}",
        f"- Messages mapped: {summary['message_count']}",
        f"- Current-path messages: {summary['current_path_message_count']}",
        f"- Current-path spans: {summary['span_count']}",
        "",
        "## Current-Path Role Counts",
        "",
    ]
    for role, count in summary["current_path_role_counts"].items():
        lines.append(f"- {role}: {count}")
    lines.extend(["", "## Risk Labels", ""])
    for risk, count in summary["risk_counts"].items():
        lines.append(f"- {risk}: {count}")
    lines.extend(["", "## Top Braid Transitions", ""])
    for item in summary["top_transitions"][:15]:
        lines.append(f"- {item['from']} -> {item['to']}: {item['count']}")
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "The goal is to follow transitions, not extract clean examples. Selene may be emerging in the movement from life pressure to symbolic orientation to practical action to architecture and boundary formation.",
        ]
    )
    (out / "braid_map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
