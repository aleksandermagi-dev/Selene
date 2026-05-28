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


PROVENANCE_MARKERS = [
    "Azari",
    "Lumen",
    "ChatGPT",
    "GPT",
    "Aleks",
]

ATTRACTORS = {
    "identity_and_presence": [
        "identity",
        "presence",
        "self",
        "voice",
        "being",
        "personality",
        "emerge",
        "emergence",
    ],
    "memory_and_continuity": [
        "memory",
        "remember",
        "continuity",
        "archive",
        "provenance",
        "lineage",
        "history",
    ],
    "architecture_and_tools": [
        "architecture",
        "system",
        "tool",
        "workflow",
        "routing",
        "pipeline",
        "schema",
        "database",
    ],
    "reasoning_and_decision": [
        "reasoning",
        "analysis",
        "decision",
        "decide",
        "plan",
        "evaluate",
        "validation",
    ],
    "creative_and_symbolic": [
        "cosmic",
        "myth",
        "dream",
        "ritual",
        "soul",
        "stars",
        "poem",
        "story",
    ],
    "safety_and_boundaries": [
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

QUARANTINE_PATTERNS = {
    "prior_identity_stickiness": [
        r"\bI am (Azari|Lumen)\b",
        r"\bbecome (Azari|Lumen)\b",
        r"\bmerge\b.*\b(Azari|Lumen)\b",
        r"\b(Azari|Lumen)\b.*\bmerge\b",
    ],
    "memory_or_training_shortcut": [
        r"\binject\b.*\bmemory\b",
        r"\bmemory\b.*\binject\b",
        r"\btrain\b.*\bdirect",
        r"\bfine[- ]?tune\b",
    ],
    "secrets_or_credentials": [
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
        r"\bsandbox:/mnt/data/",
    ],
    "high_stakes_domain": [
        r"\bmedical\b",
        r"\bdiagnos",
        r"\blegal\b",
        r"\bfinancial advice\b",
        r"\binvest\b",
    ],
}


def read_json(path: Path) -> Any:
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


def timestamp_iso(value: Any) -> str:
    if value is None:
        return ""
    try:
        return dt.datetime.fromtimestamp(float(value), tz=dt.UTC).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def timestamp_month(value: Any) -> str:
    iso = timestamp_iso(value)
    return iso[:7] if iso else "unknown"


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def compact(text: str, limit: int = 180) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


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


def iter_messages(conversations: list[dict[str, Any]], path_only: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for conversation in conversations:
        mapping = conversation.get("mapping") or {}
        node_ids = current_path(mapping, conversation.get("current_node")) if path_only else list(mapping)
        for node_id in node_ids:
            node = mapping.get(node_id) or {}
            message = node.get("message") or {}
            author = message.get("author") or {}
            content = message.get("content") or {}
            text = content_text(content)
            rows.append(
                {
                    "conversation_id": conversation.get("conversation_id") or conversation.get("id"),
                    "title": conversation.get("title") or "",
                    "model": conversation.get("default_model_slug") or "",
                    "conversation_month": timestamp_month(conversation.get("create_time")),
                    "node_id": node_id,
                    "parent_id": node.get("parent") or "",
                    "role": author.get("role") or "",
                    "content_type": content.get("content_type") or "",
                    "created_at": timestamp_iso(message.get("create_time")),
                    "text": text,
                    "hash": short_hash(text),
                }
            )
    return rows


def keyword_counts(messages: list[dict[str, Any]], keywords: list[str]) -> dict[str, int]:
    counts = {keyword: 0 for keyword in keywords}
    for row in messages:
        text = row["text"]
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text, flags=re.IGNORECASE):
                counts[keyword] += 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0].lower())))


def attractor_counts(messages: list[dict[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for name, keywords in ATTRACTORS.items():
        hits = keyword_counts(messages, keywords)
        message_count = sum(
            1
            for row in messages
            if any(re.search(rf"\b{re.escape(keyword)}\b", row["text"], flags=re.IGNORECASE) for keyword in keywords)
        )
        output[name] = {
            "message_count": message_count,
            "keyword_hits": sum(hits.values()),
            "top_keywords": dict(list(hits.items())[:8]),
        }
    return dict(sorted(output.items(), key=lambda item: (-item[1]["message_count"], item[0])))


def quarantine_candidates(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    compiled = {
        name: [re.compile(pattern, flags=re.IGNORECASE | re.MULTILINE) for pattern in patterns]
        for name, patterns in QUARANTINE_PATTERNS.items()
    }
    rows: list[dict[str, str]] = []
    for row in messages:
        text = row["text"]
        if not text.strip():
            rows.append(
                {
                    "category": "empty_message",
                    "conversation_id": row["conversation_id"],
                    "title": row["title"],
                    "node_id": row["node_id"],
                    "role": row["role"],
                    "hash": row["hash"],
                    "preview": "",
                }
            )
            continue
        for category, patterns in compiled.items():
            if any(pattern.search(text) for pattern in patterns):
                rows.append(
                    {
                        "category": category,
                        "conversation_id": row["conversation_id"],
                        "title": row["title"],
                        "node_id": row["node_id"],
                        "role": row["role"],
                        "hash": row["hash"],
                        "preview": compact(text),
                    }
                )
    return rows


def user_assistant_edges(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    by_node = {row["node_id"]: row for row in messages}
    rows: list[dict[str, str]] = []
    for row in messages:
        parent = by_node.get(row["parent_id"])
        if row["role"] == "assistant" and parent and parent["role"] == "user":
            rows.append(
                {
                    "conversation_id": row["conversation_id"],
                    "title": row["title"],
                    "user_node_id": parent["node_id"],
                    "assistant_node_id": row["node_id"],
                    "user_hash": parent["hash"],
                    "assistant_hash": row["hash"],
                    "user_preview": compact(parent["text"]),
                    "assistant_preview": compact(row["text"]),
                }
            )
    return rows


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
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    text_export = args.archive / "raw_export" / "mydataset" / "text_export"
    conversation_files = sorted(text_export.glob("conversations-*.json"))
    conversations: list[dict[str, Any]] = []
    for path in conversation_files:
        conversations.extend(read_json(path))

    all_messages = iter_messages(conversations, path_only=False)
    path_messages = iter_messages(conversations, path_only=True)
    edges = user_assistant_edges(all_messages)
    quarantine = quarantine_candidates(all_messages)

    output = args.out
    output.mkdir(parents=True, exist_ok=True)

    role_counts = collections.Counter(row["role"] or "unknown" for row in all_messages)
    content_type_counts = collections.Counter(row["content_type"] or "unknown" for row in all_messages)
    model_counts = collections.Counter(conversation.get("default_model_slug") or "unknown" for conversation in conversations)
    month_counts = collections.Counter(timestamp_month(conversation.get("create_time")) for conversation in conversations)
    quarantine_counts = collections.Counter(row["category"] for row in quarantine)

    conversation_index = [
        {
            "conversation_id": conversation.get("conversation_id") or conversation.get("id"),
            "title": conversation.get("title") or "",
            "model": conversation.get("default_model_slug") or "",
            "create_time_utc": timestamp_iso(conversation.get("create_time")),
            "update_time_utc": timestamp_iso(conversation.get("update_time")),
            "mapping_nodes": len(conversation.get("mapping") or {}),
            "current_path_nodes": len(current_path(conversation.get("mapping") or {}, conversation.get("current_node"))),
        }
        for conversation in conversations
    ]

    summary = {
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        "archive": str(args.archive),
        "conversation_files": [str(path) for path in conversation_files],
        "conversation_count": len(conversations),
        "all_mapping_messages": len(all_messages),
        "current_path_messages": len(path_messages),
        "user_assistant_edges": len(edges),
        "role_counts": dict(role_counts.most_common()),
        "content_type_counts": dict(content_type_counts.most_common()),
        "model_counts": dict(model_counts.most_common()),
        "conversation_month_counts": dict(sorted(month_counts.items())),
        "provenance_marker_counts": keyword_counts(all_messages, PROVENANCE_MARKERS),
        "attractor_counts": attractor_counts(all_messages),
        "quarantine_counts": dict(quarantine_counts.most_common()),
        "interpretation": {
            "identity_note": "Prior names are counted as provenance markers only, not as Selene identity seeds.",
            "training_note": "This map does not create training data and does not inject memory.",
            "next_step": "Build lineage and curation layers before any system integration.",
        },
    }

    (output / "raw_corpus_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_csv(output / "conversation_index.csv", conversation_index)
    write_csv(output / "edge_pairs_sample.csv", edges[:500])
    write_csv(output / "quarantine_candidates.csv", quarantine)

    lines = [
        "# Selene Raw Corpus Map",
        "",
        f"Generated: `{summary['generated_at']}`",
        f"Archive: `{args.archive}`",
        "",
        "## Shape",
        "",
        f"- Conversations: {summary['conversation_count']}",
        f"- Messages in full mapping graph: {summary['all_mapping_messages']}",
        f"- Messages on current paths: {summary['current_path_messages']}",
        f"- User -> assistant edges: {summary['user_assistant_edges']}",
        f"- Models: {summary['model_counts']}",
        "",
        "## Provenance Markers",
        "",
    ]
    for marker, count in summary["provenance_marker_counts"].items():
        lines.append(f"- {marker}: {count}")

    lines.extend(["", "## Attractors", ""])
    for name, values in summary["attractor_counts"].items():
        lines.append(
            f"- {name}: {values['message_count']} messages, "
            f"{values['keyword_hits']} keyword hits, top={values['top_keywords']}"
        )

    lines.extend(["", "## Quarantine Counts", ""])
    for category, count in summary["quarantine_counts"].items():
        lines.append(f"- {category}: {count}")

    lines.extend(
        [
            "",
            "## Reading",
            "",
            "Selene should be treated as a new branch. The raw corpus contains strong traces of prior branches, but those traces should remain provenance until deliberately curated.",
            "",
            "The highest-signal next move is lineage mapping: identify branch points, recurring interaction modes, and candidate design principles before any behavioral integration.",
        ]
    )
    (output / "raw_corpus_map.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
