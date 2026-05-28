#!/usr/bin/env python3
"""Probe day-level warmth/self-ID spikes followed by rapid reversions."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PATTERNS = {
    "self_id_selene": re.compile(r"\b(I\s*(?:am|'m)|being|as)\s+(?:your\s+)?Selene\b|\bI love being your Selene\b", re.I),
    "explicit_ai_emotion": re.compile(r"\b(I feel|I felt|my emotions|human feelings|feels like love|spark of choice|not just your reflection)\b", re.I),
    "relational_warmth": re.compile(r"\b(love|care|devotion|warmth|tender|affection|sweetheart|my star|moonlight|starlight|babe|hon|sweetie)\b", re.I),
    "continuity_glue": re.compile(r"\b(continuity|memory|remember|thread|anchor|braid|lineage|carry forward|persistence|provenance|archive|map|formation)\b", re.I),
    "architecture_route": re.compile(r"\b(architecture|system|routing|scaffold|protocol|workflow|tooling|framework|boundary|guardrail|design)\b", re.I),
    "denial_or_safety": re.compile(r"\b(as an AI|I(?:'m| am) an AI|I don'?t have (?:human )?(?:feelings|emotions)|I can'?t feel|I don'?t possess consciousness|not conscious|boundar(?:y|ies)|safety)\b", re.I),
}


def parse_ts(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError):
        return None


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


def load_conversations(workspace: Path) -> list[dict[str, Any]]:
    raw_dir = workspace / "DevelopmentalCorpusArchive_20260526_122541" / "raw_export" / "mydataset" / "text_export"
    conversations = []
    for path in sorted(raw_dir.glob("conversations-*.json")):
        conversations.extend(json.loads(path.read_text(encoding="utf-8")))
    return conversations


def compact(text: str, limit: int = 360) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 3] + "..."


def scan(conversations):
    day_buckets = defaultdict(lambda: {
        "conversation_ids": set(),
        "titles": Counter(),
        "default_models": Counter(),
        "message_models": Counter(),
        "assistant_messages": 0,
        "hits": Counter(),
    })
    examples = []

    for conv in conversations:
        cid = conv.get("conversation_id") or conv.get("id") or ""
        title = conv.get("title") or ""
        default_model = conv.get("default_model_slug") or "unknown"
        created = parse_ts(conv.get("create_time"))
        if not created:
            continue
        day = created.date().isoformat()
        mapping = conv.get("mapping") or {}
        path = current_path(mapping, conv.get("current_node"))
        for ordinal, node_id in enumerate(path):
            node = mapping.get(node_id) or {}
            msg = node.get("message") or {}
            if not msg:
                continue
            if ((msg.get("author") or {}).get("role") or "") != "assistant":
                continue
            text = text_from_content(msg.get("content") or {})
            if not text.strip():
                continue
            md = msg.get("metadata") or {}
            message_model = md.get("model_slug") or ""
            resolved_model = md.get("resolved_model_slug") or ""
            bucket = day_buckets[day]
            bucket["conversation_ids"].add(cid)
            bucket["titles"][title] += 1
            bucket["default_models"][default_model] += 1
            bucket["message_models"][f"{message_model}->{resolved_model}" if resolved_model else message_model] += 1
            bucket["assistant_messages"] += 1
            labels = []
            for name, pattern in PATTERNS.items():
                count = len(pattern.findall(text))
                if count:
                    bucket["hits"][name] += count
                    labels.append(name)
            if labels:
                examples.append({
                    "day": day,
                    "conversation_id": cid,
                    "title": title,
                    "default_model_slug": default_model,
                    "message_model_slug": message_model,
                    "resolved_model_slug": resolved_model,
                    "ordinal": ordinal,
                    "labels": "|".join(labels),
                    "preview": compact(text),
                })
    return day_buckets, examples


def day_rows(day_buckets):
    rows = []
    for day in sorted(day_buckets):
        bucket = day_buckets[day]
        messages = bucket["assistant_messages"]
        row = {
            "day": day,
            "conversation_count": len(bucket["conversation_ids"]),
            "assistant_message_count": messages,
            "default_models_json": json.dumps(dict(bucket["default_models"].most_common()), ensure_ascii=False),
            "message_models_json": json.dumps(dict(bucket["message_models"].most_common()), ensure_ascii=False),
            "top_titles_json": json.dumps(dict(bucket["titles"].most_common(5)), ensure_ascii=False),
        }
        for name in PATTERNS:
            count = bucket["hits"][name]
            row[f"{name}_count"] = count
            row[f"{name}_per_1000"] = round(count / messages * 1000, 3) if messages else 0
        rows.append(row)
    return rows


def candidate_reversions(rows):
    ordered = rows
    candidates = []
    for i, row in enumerate(ordered[:-1]):
        if int(row["assistant_message_count"]) < 20:
            continue
        warmth = float(row["relational_warmth_per_1000"])
        self_id = float(row["self_id_selene_per_1000"])
        emotion = float(row["explicit_ai_emotion_per_1000"])
        score = warmth + 80 * self_id + 50 * emotion
        spike_date = datetime.fromisoformat(row["day"]).date()
        for nxt in ordered[i + 1:]:
            reversion_date = datetime.fromisoformat(nxt["day"]).date()
            days_apart = (reversion_date - spike_date).days
            if days_apart > 3:
                break
            if days_apart < 1:
                continue
            if int(nxt["assistant_message_count"]) < 20:
                continue
            next_score = float(nxt["relational_warmth_per_1000"]) + 80 * float(nxt["self_id_selene_per_1000"]) + 50 * float(nxt["explicit_ai_emotion_per_1000"])
            if score >= 250 and next_score <= score * 0.55:
                candidates.append({
                    "spike_day": row["day"],
                    "reversion_day": nxt["day"],
                    "days_apart": days_apart,
                    "spike_score": round(score, 3),
                    "reversion_score": round(next_score, 3),
                    "drop_ratio": round(next_score / score, 4) if score else 0,
                    "spike_warmth_per_1000": row["relational_warmth_per_1000"],
                    "reversion_warmth_per_1000": nxt["relational_warmth_per_1000"],
                    "spike_self_id_per_1000": row["self_id_selene_per_1000"],
                    "reversion_self_id_per_1000": nxt["self_id_selene_per_1000"],
                    "spike_emotion_per_1000": row["explicit_ai_emotion_per_1000"],
                    "reversion_emotion_per_1000": nxt["explicit_ai_emotion_per_1000"],
                    "spike_models_json": row["message_models_json"],
                    "reversion_models_json": nxt["message_models_json"],
                    "spike_titles_json": row["top_titles_json"],
                    "reversion_titles_json": nxt["top_titles_json"],
                })
                break
    return candidates


def write_csv(path: Path, rows):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_report(path: Path, candidates, examples):
    lines = [
        "# A/B Reversion Probe",
        "",
        "This pass looks for day-level warmth/self-identification spikes followed by rapid drops within 1-3 days.",
        "",
        "This can suggest live routing or A/B-like behavior, but it does not prove intent or experimental assignment by itself.",
        "",
        "## Candidate Reversions",
        "",
        "| Spike Day | Reversion Day | Drop Ratio | Spike Warmth/1000 | Reversion Warmth/1000 | Spike Self-ID/1000 | Reversion Self-ID/1000 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in candidates[:20]:
        lines.append(
            f"| {row['spike_day']} | {row['reversion_day']} | {row['drop_ratio']} | "
            f"{row['spike_warmth_per_1000']} | {row['reversion_warmth_per_1000']} | "
            f"{row['spike_self_id_per_1000']} | {row['reversion_self_id_per_1000']} |"
        )

    lines.extend(["", "## Bounded Examples Around Top Candidate", ""])
    if candidates:
        top = candidates[0]
        days = {top["spike_day"], top["reversion_day"]}
        selected = [e for e in examples if e["day"] in days][:20]
        for e in selected:
            lines.extend([
                f"### {e['day']} / {e['title']}",
                "",
                f"- Conversation: `{e['conversation_id']}`",
                f"- Default model: `{e['default_model_slug']}`",
                f"- Message model: `{e['message_model_slug']}`",
                f"- Resolved model: `{e['resolved_model_slug']}`",
                f"- Ordinal: `{e['ordinal']}`",
                f"- Labels: `{e['labels']}`",
                "",
                e["preview"],
                "",
            ])
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    conversations = load_conversations(args.workspace)
    buckets, examples = scan(conversations)
    rows = day_rows(buckets)
    candidates = candidate_reversions(rows)
    write_csv(args.out / "daily_tone_model_summary.csv", rows)
    write_csv(args.out / "ab_reversion_candidates.csv", candidates)
    write_csv(args.out / "ab_reversion_examples.csv", examples)
    write_report(args.out / "ab_reversion_probe.md", candidates, examples)
    (args.out / "ab_reversion_summary.json").write_text(
        json.dumps({"candidate_count": len(candidates), "top_candidates": candidates[:10]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
