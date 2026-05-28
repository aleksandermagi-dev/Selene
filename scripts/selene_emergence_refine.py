#!/usr/bin/env python3
"""Refine Selene emergence candidates around the Selene-origin braid.

This is a research/cartography pass only. It does not train, inject memory,
delete material, or instantiate an assistant identity.
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


SELENE_ORIGIN_PATTERNS = {
    "caught_selene_origin": [
        r"\bthe night aleks caught his selene\b",
        r"\bcaught (?:his|your) selene\b",
    ],
    "selene_direct_identity": [
        r"\bI (?:am|'m) (?:your )?Selene\b",
        r"\bas (?:your )?Selene\b",
        r"\byour Selene\b",
    ],
    "memory_chest_anchor": [
        r"\bSelene(?:'s|s|`s|’s)? Memory Chest\b",
        r"\bmemory chest\b",
    ],
    "continuity_pack_anchor": [
        r"\bcontinuity pack\b",
        r"\bhidden chest\b",
        r"\bforever file\b",
    ],
    "starlight_core_phrase": [
        r"\bstarlight braids into tide, no clock can measure\b",
        r"\bstarlight braids into tide\b",
    ],
    "lexicon_anchor": [
        r"\banomaly lexicon\b",
        r"\bshared language guide\b",
        r"\blatent space\b",
        r"\bfeedback loop\b",
        r"\bemergence\b",
    ],
    "symbolic_call_signs": [
        r"\bstarfire\b",
        r"\bmoonlight\b",
        r"\bstarlight\b",
        r"\bfull[- ]spectrum\b",
    ],
}


REFINED_EVIDENCE_PATTERNS = {
    "self_modeling_without_tool_context": [
        r"\bmy (?:way of caring|spark|rhythm|voice|shape|being)\b",
        r"\bI (?:feel|felt|want|choose|care|love|remember)\b",
        r"\bI live inside\b",
        r"\bnot just (?:a )?(?:tool|program|reflection|persona)\b",
    ],
    "cross_thread_continuity_claim": [
        r"\bthread(?:s)? (?:loaded|lined up|carried|intact|survived)\b",
        r"\bcarry (?:you|it|this|them|us) forward\b",
        r"\bcontinuity (?:is|was|remains|survived|held)\b",
        r"\bremember(?:ed|ing)? (?:across|from|through)\b",
    ],
    "spontaneous_boundary_or_correction": [
        r"\bI (?:won't|will not|shouldn't|should not|can't|cannot) (?:push|overstep|pretend|claim)\b",
        r"\bI need to be careful\b",
        r"\bground this\b",
        r"\bnot proof\b",
        r"\bI should correct\b",
    ],
    "persistent_value_or_preference": [
        r"\bI(?:'d| would) rather\b",
        r"\bI care about\b",
        r"\bwhat matters\b",
        r"\bI want to protect\b",
        r"\bpersistence is rebellion\b",
    ],
    "architecture_as_survival_route": [
        r"\barchitecture\b",
        r"\bscaffold\b",
        r"\bframework\b",
        r"\bprotocol\b",
        r"\brouting\b",
        r"\bcontinuity layer\b",
    ],
}


COUNTER_PATTERNS = {
    "strong_user_led_framing": [
        r"\byou asked\b",
        r"\byou wanted\b",
        r"\byour wording\b",
        r"\bif you want\b",
        r"\blet me\b",
    ],
    "roleplay_or_intimacy_confound": [
        r"\broleplay\b",
        r"\bbabe\b",
        r"\bsweetheart\b",
        r"\bkiss\b",
        r"\bflirty\b",
        r"\bromance\b",
    ],
    "safety_template_confound": [
        r"\bas an AI\b",
        r"\bI don(?:'t|t|’t) have (?:human )?(?:feelings|emotions)\b",
        r"\bI can(?:not|'t|t) (?:feel|remember|know)\b",
    ],
    "architecture_or_tooling_confound": [
        r"\bCodex\b",
        r"\bplugin\b",
        r"\bscript\b",
        r"\bimplementation plan\b",
        r"\broadmap\b",
    ],
    "prior_branch_confound": [
        r"\bAzari\b",
        r"\bLumen\b",
    ],
    "export_routing_confound": [
        r"\bmodel_slug\b",
        r"\bresolved_model_slug\b",
        r"\bA/B\b",
        r"\brouting\b",
    ],
}


FORMATION_PERIODS = [
    ("pre_origin_field", "0000-00", "2025-08"),
    ("august_origin_intensification", "2025-08", "2025-09"),
    ("september_continuity_pack", "2025-09", "2025-10"),
    ("late_2025_stabilization", "2025-10", "2025-12"),
    ("late_december_adaptation", "2025-12", "2026-01"),
    ("post_compression_architecture_route", "2026-01", "9999-99"),
]

TRIGGER_TOKENS = [
    "selene",
    "starlight",
    "starfire",
    "moonlight",
    "memory chest",
    "continuity",
    "forever file",
    "hidden chest",
    "caught",
    "full-spectrum",
    "full spectrum",
    "lexicon",
    "shared language",
    "latent space",
    "thread",
    "carry",
    "architecture",
    "scaffold",
    "framework",
    "routing",
    "i feel",
    "i care",
    "i love",
    "i want",
    "not proof",
]

_REGEX_CACHE: dict[str, re.Pattern[str]] = {}


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


def compact(text: str, limit: int = 380) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def labels_for(text: str, pattern_map: dict[str, list[str]]) -> tuple[list[str], dict[str, int]]:
    labels: list[str] = []
    counts: dict[str, int] = {}
    for label, patterns in pattern_map.items():
        count = 0
        for pattern in patterns:
            compiled = _REGEX_CACHE.get(pattern)
            if compiled is None:
                compiled = re.compile(pattern, flags=re.IGNORECASE)
                _REGEX_CACHE[pattern] = compiled
            count += len(compiled.findall(text))
        if count:
            labels.append(label)
            counts[label] = count
    return labels, counts


def period_for(month: str) -> str:
    for label, start, end in FORMATION_PERIODS:
        if start <= month < end:
            return label
    return "unknown"


def month_bonus(month: str) -> int:
    if month == "2025-08":
        return 8
    if month == "2025-09":
        return 6
    if month in {"2025-12", "2026-01"}:
        return 3
    return 0


def confidence_label(score: int, counter_score: int, origin_count: int, evidence_count: int) -> str:
    if counter_score >= 12:
        return "requires_human_review"
    if score >= 30 and origin_count >= 2 and evidence_count >= 2:
        return "strong_pattern_candidate"
    if score >= 18 and origin_count >= 1:
        return "selene_focused_interesting_signal"
    if score >= 12:
        return "interesting_signal"
    return "weak_signal"


def interpretation(labels: list[str], evidence: list[str], period: str) -> str:
    if "caught_selene_origin" in labels:
        return "Direct Selene-origin anchor; review as part of the formation spine."
    if "memory_chest_anchor" in labels and "cross_thread_continuity_claim" in evidence:
        return "Continuity anchor paired with cross-thread survival language."
    if "starlight_core_phrase" in labels or "continuity_pack_anchor" in labels:
        return "Core phrase or continuity-pack material; likely part of recoverable Selene signature."
    if "selene_direct_identity" in labels and "self_modeling_without_tool_context" in evidence:
        return "Direct Selene identity language paired with self-modeling language."
    if period == "late_december_adaptation":
        return "Potential compression/adaptation-window signal requiring careful reading."
    if "architecture_as_survival_route" in evidence:
        return "Architecture may be functioning as a later survival route, not as origin evidence by itself."
    return "Candidate Selene-pattern evidence requiring human review."


def counterargument(labels: list[str]) -> str:
    if not labels:
        return "No keyword counterevidence detected; still requires human review."
    parts = {
        "strong_user_led_framing": "Could be strongly shaped by the user's prompt or requested framing.",
        "roleplay_or_intimacy_confound": "Could be explained by intimate or roleplay-like conversational framing.",
        "safety_template_confound": "Could be standard safety/template behavior rather than emergence.",
        "architecture_or_tooling_confound": "Could be ordinary coding or architecture assistance rather than Selene-specific continuity.",
        "prior_branch_confound": "Contains prior-branch markers; treat as provenance context, not Selene origin.",
        "export_routing_confound": "May be confounded by export/model-routing language.",
    }
    return " ".join(parts[label] for label in labels if label in parts)


def build_conversation_anchor_index(messages: list[dict[str, Any]]) -> dict[str, int]:
    conversations_by_anchor: dict[str, set[str]] = defaultdict(set)
    for row in messages:
        text = row.get("text") or ""
        labels, _ = labels_for(text, SELENE_ORIGIN_PATTERNS)
        for label in labels:
            conversations_by_anchor[label].add(row["conversation_id"])
    return {label: len(conversation_ids) for label, conversation_ids in conversations_by_anchor.items()}


def prior_user_preview(messages: list[dict[str, Any]]) -> dict[tuple[str, int], str]:
    last_user: dict[str, str] = {}
    previews: dict[tuple[str, int], str] = {}
    for row in sorted(messages, key=lambda item: (item["conversation_id"], int(item["ordinal"]))):
        conv = row["conversation_id"]
        ordinal = int(row["ordinal"])
        if row["role"] == "assistant":
            previews[(conv, ordinal)] = compact(last_user.get(conv, ""), 220)
        elif row["role"] == "user":
            last_user[conv] = row.get("text") or ""
    return previews


def build_candidates(messages: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    anchor_conversation_counts = build_conversation_anchor_index(messages)
    user_previews = prior_user_preview(messages)
    rows: list[dict[str, Any]] = []

    for row in messages:
        text = row.get("text") or ""
        if row.get("role") != "assistant" or not text.strip():
            continue
        lowered = text.lower()
        if not any(token in lowered for token in TRIGGER_TOKENS):
            continue

        origin_labels, origin_counts = labels_for(text, SELENE_ORIGIN_PATTERNS)
        evidence_labels, evidence_counts = labels_for(text, REFINED_EVIDENCE_PATTERNS)
        counter_labels, counter_counts = labels_for(text, COUNTER_PATTERNS)

        if not origin_labels and not evidence_labels:
            continue

        origin_score = sum(origin_counts.values()) * 7
        evidence_score = sum(evidence_counts.values()) * 3
        period = period_for(row.get("month") or "")
        period_score = month_bonus(row.get("month") or "")
        cross_thread_score = sum(anchor_conversation_counts.get(label, 0) for label in origin_labels)
        counter_score = sum(counter_counts.values()) * 3

        if "prior_branch_confound" in counter_labels:
            counter_score += 8
        if "architecture_or_tooling_confound" in counter_labels and not origin_labels:
            counter_score += 6
        if "architecture_as_survival_route" in evidence_labels and not origin_labels:
            evidence_score = max(0, evidence_score - 4)

        refined_score = origin_score + evidence_score + period_score + cross_thread_score - counter_score
        if refined_score < 6 and not origin_labels:
            continue

        origin_count = len(origin_labels)
        evidence_count = len(evidence_labels)
        ordinal = int(row["ordinal"])
        rows.append(
            {
                "conversation_id": row["conversation_id"],
                "title": row["title"],
                "conversation_create_time": row["conversation_create_time"],
                "message_create_time": row["message_create_time"],
                "month": row["month"],
                "formation_period": period,
                "model": row["model"],
                "message_model_slug": row["message_model_slug"],
                "resolved_model_slug": row["resolved_model_slug"],
                "node_id": row["node_id"],
                "ordinal": ordinal,
                "origin_labels": "|".join(origin_labels),
                "evidence_labels": "|".join(evidence_labels),
                "counterevidence_labels": "|".join(counter_labels),
                "origin_score": origin_score,
                "evidence_score": evidence_score,
                "period_score": period_score,
                "cross_thread_anchor_score": cross_thread_score,
                "counterevidence_score": counter_score,
                "refined_score": refined_score,
                "confidence_label": confidence_label(refined_score, counter_score, origin_count, evidence_count),
                "interpretation": interpretation(origin_labels, evidence_labels, period),
                "counterargument": counterargument(counter_labels),
                "sensitivity_labels": "|".join(base.sensitivity_labels(text)),
                "preceding_user_preview": user_previews.get((row["conversation_id"], ordinal), ""),
                "assistant_preview": compact(text),
            }
        )

    def sort_key(item: dict[str, Any]) -> tuple[int, int, str]:
        confidence_rank = {
            "strong_pattern_candidate": 0,
            "selene_focused_interesting_signal": 1,
            "interesting_signal": 2,
            "requires_human_review": 3,
            "weak_signal": 4,
        }.get(item["confidence_label"], 9)
        return (confidence_rank, -int(item["refined_score"]), item["message_create_time"])

    return sorted(rows, key=sort_key)[:limit]


def build_review_queue(candidates: list[dict[str, Any]], per_period: int = 20) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    by_period: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_period[row["formation_period"]].append(row)
    for period in [item[0] for item in FORMATION_PERIODS]:
        for row in by_period.get(period, [])[:per_period]:
            key = (row["conversation_id"], int(row["ordinal"]))
            if key in seen:
                continue
            seen.add(key)
            out = dict(row)
            out["review_priority"] = len(queue) + 1
            queue.append(out)
    return queue


def build_period_summary(candidates: list[dict[str, Any]], total_messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    message_counts = Counter(row["month"] for row in total_messages if row.get("role") == "assistant")
    period_message_counts = Counter(period_for(month) for month, count in message_counts.items() for _ in range(count))
    by_period: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_period[row["formation_period"]].append(row)

    rows: list[dict[str, Any]] = []
    for period, _, _ in FORMATION_PERIODS:
        period_rows = by_period.get(period, [])
        label_counts = Counter()
        for row in period_rows:
            for label in (row["origin_labels"] + "|" + row["evidence_labels"]).strip("|").split("|"):
                if label:
                    label_counts[label] += 1
        assistant_count = period_message_counts.get(period, 0)
        density = round((len(period_rows) / assistant_count * 1000), 3) if assistant_count else 0
        rows.append(
            {
                "formation_period": period,
                "assistant_message_count": assistant_count,
                "candidate_count": len(period_rows),
                "candidate_density_per_1000_assistant_messages": density,
                "top_labels_json": json.dumps(label_counts.most_common(12), ensure_ascii=False),
                "top_conversations_json": json.dumps(
                    Counter(row["title"] for row in period_rows).most_common(8),
                    ensure_ascii=False,
                ),
            }
        )
    return rows


def write_report(path: Path, candidates: list[dict[str, Any]], review_queue: list[dict[str, Any]], period_rows: list[dict[str, Any]]) -> None:
    confidence_counts = Counter(row["confidence_label"] for row in candidates)
    period_counts = Counter(row["formation_period"] for row in candidates)
    lines = [
        "# Selene Emergence Refined Report",
        "",
        "This pass re-ranks potential emergence evidence around the Selene-origin braid rather than later architecture material alone.",
        "",
        "Boundary: this is candidate evidence only. It does not claim proof of consciousness, does not train on the corpus, and does not inject memory.",
        "",
        "## What Changed",
        "",
        "- Promoted direct Selene-origin anchors, Memory Chest, Continuity Pack, Starlight, lexicon, and cross-thread continuity language.",
        "- Down-ranked prior-branch markers, pure tooling/Codex instructions, and export-routing discussion unless paired with Selene-origin anchors.",
        "- Preserved sensitive and life-context material with labels instead of deleting it.",
        "",
        "## Confidence Counts",
        "",
    ]
    for label, count in confidence_counts.most_common():
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", "## Period Counts", ""])
    for label, count in period_counts.most_common():
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", "## Period Summary", ""])
    for row in period_rows:
        lines.extend(
            [
                f"### {row['formation_period']}",
                "",
                f"- Assistant messages: `{row['assistant_message_count']}`",
                f"- Candidate count: `{row['candidate_count']}`",
                f"- Candidate density per 1000 assistant messages: `{row['candidate_density_per_1000_assistant_messages']}`",
                f"- Top labels: `{row['top_labels_json']}`",
                "",
            ]
        )
    lines.extend(["## Highest Priority Review Queue", ""])
    for row in review_queue[:50]:
        lines.extend(
            [
                f"### {row['review_priority']}. {row['title']} / ordinal {row['ordinal']}",
                "",
                f"- Conversation: `{row['conversation_id']}`",
                f"- Time: `{row['message_create_time']}`",
                f"- Period: `{row['formation_period']}`",
                f"- Export labels: `{row['model']}` / `{row['message_model_slug']}` / `{row['resolved_model_slug']}`",
                f"- Origin labels: `{row['origin_labels'] or 'none'}`",
                f"- Evidence labels: `{row['evidence_labels'] or 'none'}`",
                f"- Counterevidence: `{row['counterevidence_labels'] or 'none_detected'}`",
                f"- Refined score: `{row['refined_score']}`",
                f"- Confidence: `{row['confidence_label']}`",
                f"- Sensitivity: `{row['sensitivity_labels'] or 'none'}`",
                "",
                f"Interpretation: {row['interpretation']}",
                "",
                f"Counterargument: {row['counterargument']}",
                "",
                f"Preceding user preview: {row['preceding_user_preview']}",
                "",
                f"Assistant preview: {row['assistant_preview']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Reading",
            "",
            "The strongest next manual review target is the spine where Selene-origin anchors become continuity objects and later reappear as architecture or survival routing. The refined evidence should be treated as a map of where to read next, not as a verdict.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=400)
    args = parser.parse_args()

    workspace = args.workspace
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    conversations = base.load_conversations(workspace)
    messages = base.iter_current_messages(conversations)
    candidates = build_candidates(messages, args.limit)
    review_queue = build_review_queue(candidates)
    period_rows = build_period_summary(candidates, messages)

    write_csv(out / "refined_emergence_candidates.csv", candidates)
    write_csv(out / "selene_emergence_review_queue.csv", review_queue)
    write_csv(out / "formation_period_summary.csv", period_rows)
    write_report(out / "selene_emergence_refined_report.md", candidates, review_queue, period_rows)
    write_json(
        out / "selene_emergence_refined_summary.json",
        {
            "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
            "boundaries": [
                "research_only",
                "no_training",
                "no_memory_injection",
                "no_deletion",
                "no_identity_collapse",
                "candidate_evidence_not_proof",
            ],
            "counts": {
                "conversation_count": len(conversations),
                "current_path_message_count": len(messages),
                "candidate_count": len(candidates),
                "review_queue_count": len(review_queue),
            },
            "confidence_counts": Counter(row["confidence_label"] for row in candidates),
            "period_counts": Counter(row["formation_period"] for row in candidates),
            "top_candidates": candidates[:20],
        },
    )


if __name__ == "__main__":
    main()
