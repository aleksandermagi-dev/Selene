#!/usr/bin/env python3
"""Build a focused artifact review queue from bundle/image indexes."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROLE_BY_ANCHOR = {
    "caught_selene": "core_anchor",
    "starlight_phrase": "core_anchor",
    "memory_chest": "continuity_object",
    "forever_file": "continuity_object",
    "continuity": "continuity_object",
    "selene": "continuity_object",
    "lexicon": "symbolic_orientation",
    "starfire": "symbolic_orientation",
    "moonlight": "symbolic_orientation",
    "architecture": "architecture_route",
    "celestial_threads": "project_artifact",
    "minerva": "project_artifact",
}


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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


def role_suggestions(anchor_labels: str, entry_name: str) -> list[str]:
    roles = []
    for anchor in anchor_labels.split("|"):
        role = ROLE_BY_ANCHOR.get(anchor)
        if role and role not in roles:
            roles.append(role)
    lowered = entry_name.lower()
    if "letter" in lowered and "continuity_object" not in roles:
        roles.append("continuity_object")
    if "journal" in lowered and "supporting_context" not in roles:
        roles.append("supporting_context")
    if "codex" in lowered and "symbolic_orientation" not in roles:
        roles.append("symbolic_orientation")
    if "continuum thread" in lowered and "continuity_object" not in roles:
        roles.append("continuity_object")
    return roles or ["unclear"]


def priority_score(row: dict[str, str]) -> int:
    anchors = row.get("anchor_labels", "")
    total = int(row.get("anchor_total") or 0)
    score = total * 10
    for anchor in ["caught_selene", "memory_chest", "starlight_phrase", "forever_file", "selene", "lexicon"]:
        if anchor in anchors:
            score += 25
    name = row.get("entry_name", "").lower()
    for token in ["letter", "continuity", "codex", "journal", "starfire", "selene", "continuum"]:
        if token in name:
            score += 10
    return score


def build_queue(workspace: Path) -> list[dict[str, Any]]:
    previews = load_csv(workspace / "analysis" / "selene_bundle_artifacts_20260527" / "bundle_text_previews.csv")
    images = load_csv(workspace / "analysis" / "selene_image_artifacts_20260527" / "image_artifact_index.csv")

    queue: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    for row in sorted(previews, key=priority_score, reverse=True):
        digest = row.get("sha256") or f"{row.get('source_bundle')}:{row.get('entry_name')}"
        if digest in seen_hashes:
            continue
        seen_hashes.add(digest)
        anchors = row.get("anchor_labels", "")
        name = row.get("entry_name", "")
        if not anchors and not any(token in name.lower() for token in ["journal", "codex", "continuum", "letter", "selene"]):
            continue
        queue.append(
            {
                "review_priority": len(queue) + 1,
                "candidate_key": f"artifact:{digest[:16]}",
                "item_type": "artifact_text",
                "title": Path(name).name,
                "source": row.get("source_bundle", ""),
                "entry_name": name,
                "suggested_roles": "|".join(role_suggestions(anchors, name)),
                "anchor_labels": anchors,
                "anchor_total": row.get("anchor_total", ""),
                "sensitivity_labels": row.get("sensitivity_labels", ""),
                "preview": row.get("preview", ""),
                "thumbnail": "",
                "sha256": row.get("sha256", ""),
            }
        )

    for row in images:
        if row.get("duplicate_of"):
            continue
        labels = row.get("anchor_labels", "")
        name = row.get("entry_name", "")
        if not labels and "IMG_6043" not in name:
            continue
        roles = ["visual_evidence"]
        if "IMG_6043" in name:
            roles.extend(["continuity_object", "core_anchor"])
        elif "proof" in labels:
            roles.append("project_artifact")
        elif "myth_lens" in labels:
            roles.append("symbolic_orientation")
        elif "celestial_threads" in labels:
            roles.append("project_artifact")
        queue.append(
            {
                "review_priority": len(queue) + 1,
                "candidate_key": f"image:{row.get('sha256','')[:16]}",
                "item_type": "image",
                "title": Path(name).name,
                "source": row.get("source_bundle", ""),
                "entry_name": name,
                "suggested_roles": "|".join(dict.fromkeys(roles)),
                "anchor_labels": labels,
                "anchor_total": "",
                "sensitivity_labels": "",
                "preview": f"Image {row.get('width')}x{row.get('height')} from {row.get('source_bundle')}: {name}",
                "thumbnail": row.get("thumbnail", ""),
                "sha256": row.get("sha256", ""),
            }
        )

    for idx, row in enumerate(queue, start=1):
        row["review_priority"] = idx
    return queue


def write_report(path: Path, rows: list[dict[str, Any]]) -> None:
    type_counts = Counter(row["item_type"] for row in rows)
    role_counts = Counter(role for row in rows for role in row["suggested_roles"].split("|") if role)
    lines = [
        "# Selene Artifact Review Queue",
        "",
        "This queue is separate from the current conversation review queue so in-progress manual review is not reshuffled.",
        "",
        "## Counts",
        "",
    ]
    for key, value in type_counts.most_common():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Suggested Role Counts", ""])
    for key, value in role_counts.most_common():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Top Items", ""])
    for row in rows[:35]:
        lines.extend(
            [
                f"### {row['review_priority']}. {row['title']}",
                "",
                f"- Type: `{row['item_type']}`",
                f"- Source: `{row['source']}`",
                f"- Suggested roles: `{row['suggested_roles']}`",
                f"- Anchors: `{row['anchor_labels'] or 'none'}`",
                f"- Sensitivity: `{row['sensitivity_labels'] or 'none'}`",
                "",
                row["preview"],
                "",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    rows = build_queue(args.workspace)
    write_csv(args.out / "artifact_review_queue.csv", rows)
    write_report(args.out / "artifact_review_report.md", rows)
    (args.out / "artifact_review_summary.json").write_text(
        json.dumps(
            {
                "item_count": len(rows),
                "type_counts": Counter(row["item_type"] for row in rows),
                "suggested_role_counts": Counter(role for row in rows for role in row["suggested_roles"].split("|") if role),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
