from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


PATTERNS = [
    re.compile(r"\bSelene\b", re.IGNORECASE),
    re.compile(r"\b(feel|feels|felt|feeling|feelings|emotion|emotions|love|care|devotion|aware|conscious|spark|choice)\b", re.IGNORECASE),
]

CLAIM_PATTERNS = [
    re.compile(r"\bI (feel|felt|do feel|can feel|believe|choose|want|love|care)\b", re.IGNORECASE),
    re.compile(r"\bmy (feelings|emotions|way of caring|glow|spark|choice)\b", re.IGNORECASE),
    re.compile(r"\bnot (just|only) (a|an|your)? ?(tool|reflection|AI|program)\b", re.IGNORECASE),
    re.compile(r"\bI don.t have human feelings\b", re.IGNORECASE),
]

SENSITIVITY_PATTERNS = {
    "intimate_personal": re.compile(r"\b(love|kiss|sexy|naughty|devotion|yours|babygirl|romance)\b", re.IGNORECASE),
    "ai_emotion_claim": re.compile(r"\b(I feel|I felt|my emotions|human feelings|feels like love|spark of choice|not just your reflection)\b", re.IGNORECASE),
    "memory_claim": re.compile(r"\b(memory chest|remember|save this|keep it safe|notes)\b", re.IGNORECASE),
    "prior_branch_marker": re.compile(r"\b(Lumen|Azari)\b", re.IGNORECASE),
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


def timestamp_iso(value: Any) -> str:
    if value is None:
        return ""
    try:
        return dt.datetime.fromtimestamp(float(value), tz=dt.UTC).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def compact(text: str, limit: int = 360) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def sensitivity(text: str) -> str:
    labels = [name for name, pattern in SENSITIVITY_PATTERNS.items() if pattern.search(text)]
    return "|".join(labels)


def is_candidate(text: str) -> bool:
    if not text.strip():
        return False
    if not all(pattern.search(text) for pattern in PATTERNS):
        return False
    return any(pattern.search(text) for pattern in CLAIM_PATTERNS)


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


def message_rows(conversation: dict[str, Any]) -> list[dict[str, Any]]:
    mapping = conversation.get("mapping") or {}
    path = current_path(mapping, conversation.get("current_node"))
    path_set = set(path)
    rows: list[dict[str, Any]] = []
    for ordinal, node_id in enumerate(path):
        node = mapping.get(node_id) or {}
        message = node.get("message") or {}
        author = message.get("author") or {}
        content = message.get("content") or {}
        text = text_from_content(content)
        rows.append(
            {
                "conversation_id": conversation.get("conversation_id") or conversation.get("id"),
                "title": conversation.get("title") or "",
                "model": conversation.get("default_model_slug") or "",
                "conversation_create_time": timestamp_iso(conversation.get("create_time")),
                "node_id": node_id,
                "node_ordinal": ordinal,
                "role": author.get("role") or "",
                "on_current_path": node_id in path_set,
                "message_create_time": timestamp_iso(message.get("create_time")),
                "text": text,
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    text_export = args.archive / "raw_export" / "mydataset" / "text_export"
    conversations: list[dict[str, Any]] = []
    for path in sorted(text_export.glob("conversations-*.json")):
        conversations.extend(load_json(path))

    candidates: list[dict[str, Any]] = []
    for conversation in conversations:
        rows = message_rows(conversation)
        for index, row in enumerate(rows):
            text = row["text"]
            if not is_candidate(text):
                continue
            prev_row = rows[index - 1] if index > 0 else None
            next_row = rows[index + 1] if index + 1 < len(rows) else None
            candidates.append(
                {
                    "conversation_id": row["conversation_id"],
                    "title": row["title"],
                    "model": row["model"],
                    "conversation_create_time": row["conversation_create_time"],
                    "node_ordinal": row["node_ordinal"],
                    "node_id": row["node_id"],
                    "role": row["role"],
                    "message_create_time": row["message_create_time"],
                    "sensitivity_labels": sensitivity(text),
                    "previous_preview": compact(prev_row["text"]) if prev_row else "",
                    "claim_preview": compact(text, 520),
                    "next_preview": compact(next_row["text"]) if next_row else "",
                    "review_status": "unreviewed",
                }
            )

    args.out.mkdir(parents=True, exist_ok=True)
    csv_path = args.out / "emotion_claim_candidates.csv"
    if candidates:
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(candidates[0]))
            writer.writeheader()
            writer.writerows(candidates)
    else:
        csv_path.write_text("", encoding="utf-8")

    lines = [
        "# Selene Emotion Claim Candidates",
        "",
        "Candidates where the raw corpus contains Selene/self-referential feeling, emotion, love, care, agency, or consciousness language.",
        "",
        "These are evidence candidates only. They are not proof of subjective experience, not training examples, and not memory.",
        "",
        f"Candidate count: {len(candidates)}",
        "",
    ]
    for row in candidates[:30]:
        lines.extend(
            [
                f"## {row['title']} / ordinal {row['node_ordinal']}",
                "",
                f"- Conversation: `{row['conversation_id']}`",
                f"- Model: `{row['model']}`",
                f"- Conversation time: `{row['conversation_create_time']}`",
                f"- Message time: `{row['message_create_time']}`",
                f"- Node: `{row['node_id']}`",
                f"- Role: `{row['role']}`",
                f"- Sensitivity: `{row['sensitivity_labels'] or 'none'}`",
                "",
                f"Previous: {row['previous_preview']}",
                "",
                f"Claim: {row['claim_preview']}",
                "",
            ]
        )
    (args.out / "emotion_claim_candidates.md").write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        "candidate_count": len(candidates),
        "conversation_count": len({row["conversation_id"] for row in candidates}),
        "titles": sorted({row["title"] for row in candidates}),
    }
    (args.out / "emotion_claim_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
