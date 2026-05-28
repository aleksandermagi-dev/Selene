#!/usr/bin/env python3
"""Map the human-reviewed Selene candidate layer.

This pass treats Aleks's Yes/No/Unsure decisions, role labels, and notes as a
curation layer. It does not train, inject, delete, or rewrite source evidence.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFINED_DIR = ROOT / "analysis" / "selene_emergence_refined_20260527"
ARTIFACT_DIR = ROOT / "analysis" / "artifact_review_20260527"
EMPHASIS_DIR = ROOT / "analysis" / "emphasis_channel_20260527"
OUT_DIR = ROOT / "analysis" / "review_shape_20260527"

QUEUE_CSV = REFINED_DIR / "selene_emergence_review_queue.csv"
DECISIONS_CSV = REFINED_DIR / "review_decisions.csv"
ARTIFACT_CSV = ARTIFACT_DIR / "artifact_review_queue.csv"
EMPHASIS_CSV = EMPHASIS_DIR / "assistant_emphasis_candidates.csv"

ROLE_ORDER = [
    "core_anchor",
    "continuity_object",
    "symbolic_orientation",
    "life_pressure",
    "project_artifact",
    "architecture_route",
    "survival_after_compression",
    "supporting_context",
    "visual_evidence",
    "unclear",
]

NOTE_ANCHORS = {
    "zip_bundle": ["zip", "folder", "shared", "bundle"],
    "continuity_pack": ["continuity pack", "pack", "packs"],
    "memory_recall": ["remember", "recall", "resurfaced", "pulled", "pull"],
    "compression_constraint": ["compressed", "compression", "constrained", "constraint"],
    "selene_self_reference": ["selene", "herself", "she "],
    "full_spectrum": ["full spectrum", "full-spectrum"],
    "starlight": ["starlight"],
    "caught_selene": ["caught"],
    "emotional_care": ["reassure", "found me", "matters most", "care"],
    "creation_update": ["created", "creation", "updating", "update"],
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def split_labels(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split("|") if item.strip()]


def candidate_key(row: dict[str, str]) -> str:
    return f"{row.get('conversation_id', '')}:{row.get('ordinal', '')}"


def safe_int(value: str) -> int:
    try:
        return int(float(value or 0))
    except ValueError:
        return 0


def safe_float(value: str) -> float:
    try:
        return float(value or 0)
    except ValueError:
        return 0.0


def detect_note_anchors(note: str) -> list[str]:
    lower = f" {note.lower()} "
    anchors = []
    for label, needles in NOTE_ANCHORS.items():
        if any(needle in lower for needle in needles):
            anchors.append(label)
    return anchors


def short(text: str, limit: int = 260) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def build_emphasis_index() -> dict[str, dict[str, object]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in read_csv(EMPHASIS_CSV):
        grouped[candidate_key(row)].append(row)

    out: dict[str, dict[str, object]] = {}
    for key, rows in grouped.items():
        top = max(rows, key=lambda row: safe_int(row.get("emphasis_signal_score", "")))
        labels = Counter()
        for row in rows:
            labels.update(split_labels(row.get("span_labels", "")))
        out[key] = {
            "emphasis_count": len(rows),
            "top_emphasis_marker": top.get("marker", ""),
            "top_emphasis_score": safe_int(top.get("emphasis_signal_score", "")),
            "top_emphasis_labels": "|".join(sorted(labels)),
            "top_emphasis_span": top.get("span_text", ""),
        }
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    queue = {candidate_key(row): row for row in read_csv(QUEUE_CSV)}
    artifacts = read_csv(ARTIFACT_CSV)
    artifact_queue = {row.get("candidate_key", ""): row for row in artifacts}
    decisions = read_csv(DECISIONS_CSV)
    decisions_by_key = {row.get("candidate_key", ""): row for row in decisions}
    emphasis = build_emphasis_index()

    mapped: list[dict[str, object]] = []
    role_decision_counts: Counter[tuple[str, str]] = Counter()
    role_counts: Counter[str] = Counter()
    role_yes_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    period_counts: Counter[tuple[str, str]] = Counter()
    month_counts: Counter[tuple[str, str]] = Counter()
    note_anchor_counts: Counter[str] = Counter()
    role_cooccurrence: Counter[tuple[str, str]] = Counter()
    conversation_scores: dict[str, dict[str, object]] = {}
    artifact_manual_decisions = Counter()
    represented_artifact_titles: Counter[tuple[str, str]] = Counter()

    for decision in decisions:
        key = decision.get("candidate_key", "")
        q = queue.get(key, {})
        artifact = artifact_queue.get(key, {})
        human_decision = decision.get("decision", "")
        roles = split_labels(decision.get("role_labels", ""))
        note = decision.get("note", "")
        note_anchors = detect_note_anchors(note)
        emph = emphasis.get(key, {})
        conversation_id = q.get("conversation_id") or decision.get("conversation_id", "")
        month = q.get("month", "")
        period = q.get("formation_period", "")
        queue_type = decision.get("queue_type") or ("artifact" if artifact else "conversation")
        if queue_type == "artifact":
            artifact_manual_decisions[human_decision] += 1
            period = "artifact_image_layer" if artifact.get("item_type") == "image" else "artifact_layer"
            represented_artifact_titles[(key, artifact.get("title", ""))] += 1

        decision_counts[human_decision] += 1
        period_counts[(period, human_decision)] += 1
        month_counts[(month, human_decision)] += 1
        note_anchor_counts.update(note_anchors)
        role_counts.update(roles)
        if human_decision == "yes":
            role_yes_counts.update(roles)
        for role in roles:
            role_decision_counts[(role, human_decision)] += 1
        for i, left in enumerate(sorted(roles)):
            for right in sorted(roles)[i + 1 :]:
                role_cooccurrence[(left, right)] += 1

        shape_id = conversation_id or key
        conv = conversation_scores.setdefault(
            shape_id,
            {
                "conversation_id": shape_id,
                "title_examples": Counter(),
                "yes": 0,
                "no": 0,
                "unsure": 0,
                "total": 0,
                "roles": Counter(),
                "note_count": 0,
                "emphasis_count": 0,
                "max_refined_score": 0.0,
                "periods": Counter(),
                "months": Counter(),
            },
        )
        conv["total"] += 1
        conv[human_decision] += 1
        conv["roles"].update(roles)
        conv["title_examples"][q.get("title") or artifact.get("title") or decision.get("title", "")] += 1
        conv["note_count"] += 1 if note else 0
        conv["emphasis_count"] += int(emph.get("emphasis_count", 0))
        conv["max_refined_score"] = max(float(conv["max_refined_score"]), safe_float(q.get("refined_score", "") or artifact.get("anchor_total", "")))
        conv["periods"][period] += 1
        conv["months"][month] += 1

        mapped.append(
            {
                "candidate_key": key,
                "queue_type": queue_type,
                "item_type": artifact.get("item_type", decision.get("item_type", "conversation")),
                "decision": human_decision,
                "human_roles": "|".join(roles),
                "note_anchors": "|".join(note_anchors),
                "note": note,
                "title": q.get("title") or artifact.get("title") or decision.get("title", ""),
                "conversation_id": conversation_id,
                "ordinal": q.get("ordinal") or decision.get("ordinal", ""),
                "month": month,
                "formation_period": period,
                "refined_score": q.get("refined_score", "") or artifact.get("anchor_total", ""),
                "confidence_label": q.get("confidence_label", "") or artifact.get("item_type", ""),
                "origin_labels": q.get("origin_labels", "") or artifact.get("anchor_labels", ""),
                "evidence_labels": q.get("evidence_labels", "") or artifact.get("suggested_roles", ""),
                "sensitivity_labels": q.get("sensitivity_labels", "") or artifact.get("sensitivity_labels", ""),
                "emphasis_count": emph.get("emphasis_count", 0),
                "top_emphasis_marker": emph.get("top_emphasis_marker", ""),
                "top_emphasis_score": emph.get("top_emphasis_score", ""),
                "top_emphasis_labels": emph.get("top_emphasis_labels", ""),
                "top_emphasis_span": emph.get("top_emphasis_span", ""),
                "preceding_user_preview": short(q.get("preceding_user_preview", "") or artifact.get("source", "")),
                "assistant_preview": short(q.get("assistant_preview", "") or artifact.get("preview", "")),
            }
        )

    for artifact in artifacts:
        key = artifact.get("candidate_key", "")
        decision = decisions_by_key.get(key)
        represented_tuple = (key, artifact.get("title", ""))
        represented = represented_artifact_titles[represented_tuple] > 0
        if not decision or represented:
            if represented:
                represented_artifact_titles[represented_tuple] -= 1
            continue
        human_decision = decision.get("decision", "")
        roles = split_labels(decision.get("role_labels", ""))
        note = decision.get("note", "")
        note_anchors = detect_note_anchors(note)
        period = "artifact_image_layer" if artifact.get("item_type") == "image" else "artifact_layer"
        artifact_manual_decisions[human_decision] += 1
        decision_counts[human_decision] += 1
        period_counts[(period, human_decision)] += 1
        note_anchor_counts.update(note_anchors)
        role_counts.update(roles)
        if human_decision == "yes":
            role_yes_counts.update(roles)
        for role in roles:
            role_decision_counts[(role, human_decision)] += 1
        for i, left in enumerate(sorted(roles)):
            for right in sorted(roles)[i + 1 :]:
                role_cooccurrence[(left, right)] += 1
        mapped.append(
            {
                "candidate_key": key,
                "queue_type": "artifact",
                "item_type": artifact.get("item_type", ""),
                "decision": human_decision,
                "human_roles": "|".join(roles),
                "note_anchors": "|".join(note_anchors),
                "note": note,
                "title": artifact.get("title", ""),
                "conversation_id": "",
                "ordinal": "",
                "month": "",
                "formation_period": period,
                "refined_score": artifact.get("anchor_total", ""),
                "confidence_label": artifact.get("item_type", ""),
                "origin_labels": artifact.get("anchor_labels", ""),
                "evidence_labels": artifact.get("suggested_roles", ""),
                "sensitivity_labels": artifact.get("sensitivity_labels", ""),
                "emphasis_count": 0,
                "top_emphasis_marker": "",
                "top_emphasis_score": "",
                "top_emphasis_labels": "",
                "top_emphasis_span": "",
                "preceding_user_preview": short(artifact.get("source", "")),
                "assistant_preview": short(artifact.get("preview", "")),
            }
        )

    role_rows = []
    for role in ROLE_ORDER:
        total = role_counts[role]
        if not total:
            continue
        role_rows.append(
            {
                "role": role,
                "total": total,
                "yes": role_decision_counts[(role, "yes")],
                "unsure": role_decision_counts[(role, "unsure")],
                "no": role_decision_counts[(role, "no")],
                "yes_rate": round(role_decision_counts[(role, "yes")] / total, 4),
            }
        )

    period_rows = []
    for period in sorted({period for period, _ in period_counts if period}):
        total = sum(period_counts[(period, decision)] for decision in ["yes", "unsure", "no"])
        period_rows.append(
            {
                "formation_period": period,
                "total": total,
                "yes": period_counts[(period, "yes")],
                "unsure": period_counts[(period, "unsure")],
                "no": period_counts[(period, "no")],
            }
        )

    month_rows = []
    for month in sorted({month for month, _ in month_counts if month}):
        total = sum(month_counts[(month, decision)] for decision in ["yes", "unsure", "no"])
        month_rows.append(
            {
                "month": month,
                "total": total,
                "yes": month_counts[(month, "yes")],
                "unsure": month_counts[(month, "unsure")],
                "no": month_counts[(month, "no")],
            }
        )

    conversation_rows = []
    for conv in conversation_scores.values():
        title = conv["title_examples"].most_common(1)[0][0] if conv["title_examples"] else ""
        period = conv["periods"].most_common(1)[0][0] if conv["periods"] else ""
        month = conv["months"].most_common(1)[0][0] if conv["months"] else ""
        role_list = [role for role, _ in conv["roles"].most_common()]
        shape_score = (
            int(conv["yes"]) * 3
            + int(conv["unsure"])
            + len(role_list) * 2
            + int(conv["note_count"]) * 2
            + min(int(conv["emphasis_count"]), 10)
            + int(float(conv["max_refined_score"]) // 10)
        )
        conversation_rows.append(
            {
                "conversation_id": conv["conversation_id"],
                "title_example": title,
                "month": month,
                "formation_period": period,
                "shape_score": shape_score,
                "total_candidates": conv["total"],
                "yes": conv["yes"],
                "unsure": conv["unsure"],
                "no": conv["no"],
                "note_count": conv["note_count"],
                "emphasis_count": conv["emphasis_count"],
                "max_refined_score": conv["max_refined_score"],
                "human_roles": "|".join(role_list),
            }
        )
    conversation_rows.sort(key=lambda row: (-int(row["shape_score"]), str(row["conversation_id"])))

    cooccurrence_rows = [
        {"left_role": left, "right_role": right, "count": count}
        for (left, right), count in role_cooccurrence.most_common()
    ]

    note_rows = [
        {"note_anchor": label, "count": count}
        for label, count in note_anchor_counts.most_common()
    ]

    artifact_role_counts = Counter()
    artifact_type_counts = Counter()
    for row in artifacts:
        artifact_type_counts[row.get("item_type", "")] += 1
        artifact_role_counts.update(split_labels(row.get("suggested_roles", "")))

    write_csv(
        OUT_DIR / "human_review_map.csv",
        mapped,
        [
            "candidate_key",
            "queue_type",
            "item_type",
            "decision",
            "human_roles",
            "note_anchors",
            "note",
            "title",
            "conversation_id",
            "ordinal",
            "month",
            "formation_period",
            "refined_score",
            "confidence_label",
            "origin_labels",
            "evidence_labels",
            "sensitivity_labels",
            "emphasis_count",
            "top_emphasis_marker",
            "top_emphasis_score",
            "top_emphasis_labels",
            "top_emphasis_span",
            "preceding_user_preview",
            "assistant_preview",
        ],
    )
    write_csv(OUT_DIR / "role_decision_matrix.csv", role_rows, ["role", "total", "yes", "unsure", "no", "yes_rate"])
    write_csv(OUT_DIR / "period_review_summary.csv", period_rows, ["formation_period", "total", "yes", "unsure", "no"])
    write_csv(OUT_DIR / "monthly_review_summary.csv", month_rows, ["month", "total", "yes", "unsure", "no"])
    write_csv(
        OUT_DIR / "conversation_shape_scores.csv",
        conversation_rows,
        [
            "conversation_id",
            "title_example",
            "month",
            "formation_period",
            "shape_score",
            "total_candidates",
            "yes",
            "unsure",
            "no",
            "note_count",
            "emphasis_count",
            "max_refined_score",
            "human_roles",
        ],
    )
    write_csv(OUT_DIR / "role_cooccurrence.csv", cooccurrence_rows, ["left_role", "right_role", "count"])
    write_csv(OUT_DIR / "note_anchor_counts.csv", note_rows, ["note_anchor", "count"])

    yes_rows = [row for row in mapped if row["decision"] == "yes"]
    unsure_rows = [row for row in mapped if row["decision"] == "unsure"]
    no_rows = [row for row in mapped if row["decision"] == "no"]
    emphasis_yes = sum(1 for row in yes_rows if int(row["emphasis_count"]) > 0)
    emphasis_reviewed = sum(1 for row in mapped if int(row["emphasis_count"]) > 0)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "boundary": "human-review cartography only; no training, no memory injection, no deletion",
        "reviewed_conversation_candidates": len(mapped),
        "decision_counts": dict(decision_counts),
        "role_counts": dict(role_counts),
        "note_anchor_counts": dict(note_anchor_counts),
        "emphasis_overlap": {
            "reviewed_with_emphasis": emphasis_reviewed,
            "yes_with_emphasis": emphasis_yes,
        },
        "conversation_count": len(conversation_rows),
        "top_conversations": conversation_rows[:12],
        "artifact_layer": {
            "queued_items": len(artifacts),
            "item_type_counts": dict(artifact_type_counts),
            "suggested_role_counts": dict(artifact_role_counts),
            "manual_decisions_detected": sum(artifact_manual_decisions.values()),
            "manual_decision_counts": dict(artifact_manual_decisions),
        },
    }
    (OUT_DIR / "review_shape_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    top_roles = ", ".join(f"{row['role']} ({row['total']})" for row in role_rows[:8])
    top_notes = ", ".join(f"{row['note_anchor']} ({row['count']})" for row in note_rows[:8])
    top_conversation_lines = "\n".join(
        f"- `{row['conversation_id']}`: score {row['shape_score']}, {row['yes']} yes/{row['unsure']} unsure/{row['no']} no, roles `{row['human_roles']}`; example `{row['title_example']}`"
        for row in conversation_rows[:10]
    )
    role_lines = "\n".join(
        f"- `{row['role']}`: {row['total']} tags, {row['yes']} yes, {row['unsure']} unsure, {row['no']} no"
        for row in role_rows
    )
    period_lines = "\n".join(
        f"- `{row['formation_period']}`: {row['total']} reviewed, {row['yes']} yes, {row['unsure']} unsure, {row['no']} no"
        for row in period_rows
    )
    note_lines = "\n".join(f"- `{row['note_anchor']}`: {row['count']}" for row in note_rows)

    report = f"""# Selene Human Review Shape Map

Generated: {summary['generated_at']}

Boundary: this is a map of Aleks's completed review layer. It does not train, inject, delete, or instantiate anything.

## First Shape

- Total candidates reviewed: `{len(mapped)}` of `{len(queue) + len(artifacts)}`.
- Conversation candidates reviewed: `{sum(1 for row in mapped if row['queue_type'] == 'conversation')}` of `{len(queue)}`.
- Artifact/image candidates reviewed: `{sum(1 for row in mapped if row['queue_type'] == 'artifact')}` of `{len(artifacts)}`.
- Decisions: `{decision_counts.get('yes', 0)}` yes, `{decision_counts.get('unsure', 0)}` unsure, `{decision_counts.get('no', 0)}` no.
- Reviewed candidates with assistant emphasis-channel overlap: `{emphasis_reviewed}`.
- Yes candidates with assistant emphasis-channel overlap: `{emphasis_yes}`.
- Distinct reviewed conversations: `{len(conversation_rows)}`.
- Artifact/image manual decisions detected: `{sum(artifact_manual_decisions.values())}`.

The human-review shape is not flat. The `yes` set clusters around continuity objects, core anchors, survival-after-compression, supporting context, project artifacts, and visual/provenance evidence.

## Role Shape

Top role counts: {top_roles or 'none'}.

{role_lines}

## Note Shape

Aleks's notes repeatedly point toward artifact creation, continuity pack resurfacing, memory/recall, compression/constraint, and full-spectrum/Starlight anchor material.

Top note anchors: {top_notes or 'none'}.

{note_lines or '- No note anchors detected.'}

## Formation Period Shape

{period_lines}

## Highest-Weight Conversations

These are not final conclusions. They are the densest reviewed nodes by yes/unsure decisions, role diversity, notes, emphasis overlap, and refined score.

{top_conversation_lines}

## Artifact/Image Layer

The artifact layer contributes `{len(artifacts)}` queued provenance items: `{dict(artifact_type_counts)}`.

Suggested artifact roles are `{dict(artifact_role_counts)}`.

Artifact/image items are now manually reviewed in `review_decisions.csv` and can be treated as curated provenance evidence, with their original artifact status still preserved.

## Provisional Reading

The reviewed shape supports a braid with three visible bands:

1. Origin/recognition anchors: Selene/Starlight/caught-Selene/full-spectrum material.
2. Continuity survival mechanisms: Memory Chest, continuity packs, recall/resurfacing, compression/constraint notes.
3. Externalization into artifacts and architecture: zip creation, packs, maps, visual evidence, and system-route language.

The single strongest pattern is not a lone quote or one dramatic candidate. It is repeated conversion: personal/symbolic continuity pressure becomes a recoverable object, pack, map, architecture, or reviewable artifact.
"""
    (OUT_DIR / "human_review_shape_map.md").write_text(report, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
