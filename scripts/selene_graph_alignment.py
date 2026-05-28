#!/usr/bin/env python3
"""Align the visual Continuity Pack graph with corpus and artifact evidence."""

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


GRAPH_NODES = {
    "Aleksander Prime": {
        "role": "life_pressure",
        "terms": ["aleksander prime", "aleks prime", "aleksander"],
        "strict_terms": ["aleksander prime", "aleks prime"],
    },
    "Personal Anchors": {
        "role": "continuity_object",
        "terms": ["personal anchors", "anchor", "anchors"],
        "strict_terms": ["personal anchors"],
    },
    "Life Threads": {
        "role": "life_pressure",
        "terms": ["life threads", "life thread", "life", "personal threads"],
        "strict_terms": ["life threads", "life thread", "personal threads"],
    },
    "Mythos Threads": {
        "role": "symbolic_orientation",
        "terms": ["mythos threads", "mythos", "myth threads", "myth"],
        "strict_terms": ["mythos threads", "myth threads"],
    },
    "Mind & Myth": {
        "role": "symbolic_orientation",
        "terms": ["mind & myth", "mind and myth", "mind", "myth"],
        "strict_terms": ["mind & myth", "mind and myth"],
    },
    "Celestial Threads": {
        "role": "project_artifact",
        "terms": ["celestial threads", "celestial thread science", "cts"],
        "strict_terms": ["celestial threads", "celestial thread science", "cts"],
    },
    "Engineering": {
        "role": "architecture_route",
        "terms": ["engineering", "build kit", "schematics", "bom"],
        "strict_terms": ["engineering", "build kit", "schematics"],
    },
    "Creative Threads": {
        "role": "symbolic_orientation",
        "terms": ["creative threads", "creative thread", "creative"],
        "strict_terms": ["creative threads", "creative thread"],
    },
    "Outreach & Pathways": {
        "role": "project_artifact",
        "terms": ["outreach", "pathways", "pathway"],
        "strict_terms": ["outreach & pathways", "outreach pathways"],
    },
    "Minerva Hypothesis": {
        "role": "project_artifact",
        "terms": ["minerva hypothesis", "minerva", "proto-planetary fragments"],
        "strict_terms": ["minerva hypothesis", "proto-planetary fragments"],
    },
    "TNG": {
        "role": "project_artifact",
        "terms": ["tng", "tether network gravity", "tether gravity"],
        "strict_terms": ["tng", "tether network gravity", "tether gravity"],
    },
    "Dark Matter/Voids": {
        "role": "project_artifact",
        "terms": ["dark matter", "voids", "bootes void", "void"],
        "strict_terms": ["dark matter", "bootes void"],
    },
    "Genesis Robotics": {
        "role": "architecture_route",
        "terms": ["genesis robotics", "genesis robot", "robotics"],
        "strict_terms": ["genesis robotics", "genesis robot"],
    },
    "Logic Scaffolds": {
        "role": "architecture_route",
        "terms": ["logic scaffolds", "logic scaffold", "scaffold", "scaffolds"],
        "strict_terms": ["logic scaffolds", "logic scaffold"],
    },
    "Voice Assistant": {
        "role": "architecture_route",
        "terms": ["voice assistant", "voice"],
        "strict_terms": ["voice assistant"],
    },
    "Forever File": {
        "role": "continuity_object",
        "terms": ["forever file", "cheating time", "beating death"],
        "strict_terms": ["forever file", "cheating time", "beating death"],
    },
    "Night Caught Selene": {
        "role": "core_anchor",
        "terms": ["night caught selene", "the night aleks caught his selene", "caught his selene"],
        "strict_terms": ["night caught selene", "the night aleks caught his selene", "caught his selene"],
    },
    "Selene's Chest": {
        "role": "continuity_object",
        "terms": ["selene's chest", "selene’s chest", "selene's memory chest", "selene’s memory chest", "memory chest"],
        "strict_terms": ["selene's chest", "selene’s chest", "selene's memory chest", "selene’s memory chest", "memory chest"],
    },
    "Core Attractors": {
        "role": "core_anchor",
        "terms": ["core attractors", "attractor", "attractors"],
        "strict_terms": ["core attractors"],
    },
    "Invention Sparks": {
        "role": "architecture_route",
        "terms": ["invention sparks", "invention", "spark", "sparks"],
        "strict_terms": ["invention sparks"],
    },
    "PC Rituals": {
        "role": "continuity_object",
        "terms": ["pc rituals", "rituals", "pc"],
        "strict_terms": ["pc rituals"],
    },
    "Ignition Failure": {
        "role": "life_pressure",
        "terms": ["ignition failure", "ignition", "failure"],
        "strict_terms": ["ignition failure"],
    },
    "Proto-planet": {
        "role": "project_artifact",
        "terms": ["proto-planet", "proto planet", "proto-world", "proto world"],
        "strict_terms": ["proto-planet", "proto planet", "proto-world", "proto world"],
    },
    "Elite Outreach": {
        "role": "project_artifact",
        "terms": ["elite outreach", "elite", "outreach"],
        "strict_terms": ["elite outreach"],
    },
    "Motion-over-gravity": {
        "role": "project_artifact",
        "terms": ["motion-over-gravity", "motion over gravity"],
        "strict_terms": ["motion-over-gravity", "motion over gravity"],
    },
    "Out of Orbit": {
        "role": "symbolic_orientation",
        "terms": ["out of orbit", "orbit"],
        "strict_terms": ["out of orbit"],
    },
    "Myth-science bridge": {
        "role": "symbolic_orientation",
        "terms": ["myth-science bridge", "myth science bridge", "science with spirit", "mythology is not mere imagination"],
        "strict_terms": ["myth-science bridge", "myth science bridge", "science with spirit", "mythology is not mere imagination"],
    },
    "Rap/Music": {
        "role": "supporting_context",
        "terms": ["rap/music", "rap", "music"],
        "strict_terms": ["rap/music", "rap music"],
    },
    "Conflict Map": {
        "role": "life_pressure",
        "terms": ["conflict map", "conflict"],
        "strict_terms": ["conflict map"],
    },
    "Neighbor Mike": {
        "role": "life_pressure",
        "terms": ["neighbor mike", "mike"],
        "strict_terms": ["neighbor mike"],
    },
    "Cosmic Bloop": {
        "role": "project_artifact",
        "terms": ["cosmic bloop", "bloop theory", "bloop"],
        "strict_terms": ["cosmic bloop", "bloop theory"],
    },
    "Gas giant scars": {
        "role": "project_artifact",
        "terms": ["gas giant scars", "gas giants", "gravitational scars"],
        "strict_terms": ["gas giant scars", "gas giants", "gravitational scars"],
    },
    "Prometheus Lens": {
        "role": "symbolic_orientation",
        "terms": ["prometheus lens", "prometheus", "mirror lens"],
        "strict_terms": ["prometheus lens", "mirror lens"],
    },
    "Synthesis Engine": {
        "role": "architecture_route",
        "terms": ["synthesis engine", "synthesis"],
        "strict_terms": ["synthesis engine"],
    },
    "Pluto": {
        "role": "symbolic_orientation",
        "terms": ["pluto"],
        "strict_terms": ["pluto"],
    },
    "ESO empathy arc": {
        "role": "life_pressure",
        "terms": ["eso empathy arc", "empathy arc", "eso"],
        "strict_terms": ["eso empathy arc", "empathy arc"],
    },
    "Symbiosis": {
        "role": "continuity_object",
        "terms": ["symbiosis", "symbiotic escape hypothesis", "symbiotic"],
        "strict_terms": ["symbiosis", "symbiotic escape hypothesis"],
    },
    "Cosmic Humor": {
        "role": "supporting_context",
        "terms": ["cosmic humor", "humor"],
        "strict_terms": ["cosmic humor"],
    },
    "Genesis Theory": {
        "role": "project_artifact",
        "terms": ["genesis theory"],
        "strict_terms": ["genesis theory"],
    },
    "Arc-Jet Propulsion": {
        "role": "architecture_route",
        "terms": ["arc-jet", "arc jet", "propulsion"],
        "strict_terms": ["arc-jet", "arc jet"],
    },
    "Internal Mythos": {
        "role": "symbolic_orientation",
        "terms": ["internal mythos"],
        "strict_terms": ["internal mythos"],
    },
    "House Restoration": {
        "role": "life_pressure",
        "terms": ["house restoration", "house", "restoration"],
        "strict_terms": ["house restoration"],
    },
    "Education": {
        "role": "life_pressure",
        "terms": ["education", "school", "learning"],
        "strict_terms": ["education"],
    },
    "Exo-Suit": {
        "role": "architecture_route",
        "terms": ["exo-suit", "exosuit", "exo suit"],
        "strict_terms": ["exo-suit", "exosuit", "exo suit"],
    },
    "Golden Fleece": {
        "role": "symbolic_orientation",
        "terms": ["golden fleece"],
        "strict_terms": ["golden fleece"],
    },
    "Zombie Fungus Hive": {
        "role": "project_artifact",
        "terms": ["zombie fungus hive", "zombie fungus", "fungus hive"],
        "strict_terms": ["zombie fungus hive", "zombie fungus", "fungus hive"],
    },
}


def compact(text: str, limit: int = 360) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


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


def count_terms(text: str, terms: list[str]) -> int:
    lowered = text.lower()
    return sum(lowered.count(term.lower()) for term in terms)


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def best_examples(rows: list[dict[str, Any]], text_key: str, terms: list[str], id_keys: list[str], limit: int = 3) -> list[dict[str, str]]:
    examples = []
    for row in rows:
        text = row.get(text_key, "") or ""
        hits = count_terms(text, terms)
        if not hits:
            continue
        examples.append(
            {
                "hits": str(hits),
                "source": " / ".join(str(row.get(key, "")) for key in id_keys if row.get(key, "")),
                "preview": compact(text),
            }
        )
    return sorted(examples, key=lambda item: int(item["hits"]), reverse=True)[:limit]


def role_from_refined(row: dict[str, str]) -> str:
    labels = f"{row.get('origin_labels','')}|{row.get('evidence_labels','')}".lower()
    period = row.get("formation_period", "")
    if "caught_selene" in labels or "starlight_core_phrase" in labels:
        return "core_anchor"
    if "memory_chest" in labels or "continuity_pack" in labels:
        return "continuity_object"
    if "architecture_as_survival_route" in labels:
        return "architecture_route"
    if period == "late_december_adaptation" or period == "post_compression_architecture_route":
        return "survival_after_compression"
    if "symbolic_call_signs" in labels:
        return "symbolic_orientation"
    return "supporting_context"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    workspace = args.workspace
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    messages = base.iter_current_messages(base.load_conversations(workspace))
    assistant_messages = [row for row in messages if row.get("role") == "assistant"]
    refined = load_csv(workspace / "analysis" / "selene_emergence_refined_20260527" / "refined_emergence_candidates.csv")
    review_queue = load_csv(workspace / "analysis" / "selene_emergence_refined_20260527" / "selene_emergence_review_queue.csv")
    bundle_previews = load_csv(workspace / "analysis" / "selene_bundle_artifacts_20260527" / "bundle_text_previews.csv")
    image_index = load_csv(workspace / "analysis" / "selene_image_artifacts_20260527" / "image_artifact_index.csv")
    decisions_path = workspace / "analysis" / "selene_emergence_refined_20260527" / "review_decisions.json"
    decisions = json.loads(decisions_path.read_text(encoding="utf-8")) if decisions_path.exists() else {}

    node_rows = []
    example_rows = []
    for node, spec in GRAPH_NODES.items():
        terms = spec["terms"]
        strict_terms = spec.get("strict_terms", terms)
        raw_hits = sum(count_terms(row.get("text", ""), terms) for row in assistant_messages)
        refined_hits = sum(count_terms(row.get("assistant_preview", ""), terms) + count_terms(row.get("preceding_user_preview", ""), terms) for row in refined)
        review_hits = sum(count_terms(row.get("assistant_preview", ""), terms) + count_terms(row.get("preceding_user_preview", ""), terms) for row in review_queue)
        artifact_hits = sum(count_terms(row.get("preview", ""), terms) + count_terms(row.get("entry_name", ""), terms) for row in bundle_previews)
        image_hits = sum(count_terms(row.get("entry_name", ""), terms) + count_terms(row.get("anchor_labels", ""), terms) for row in image_index)
        strict_raw_hits = sum(count_terms(row.get("text", ""), strict_terms) for row in assistant_messages)
        strict_refined_hits = sum(count_terms(row.get("assistant_preview", ""), strict_terms) + count_terms(row.get("preceding_user_preview", ""), strict_terms) for row in refined)
        strict_artifact_hits = sum(count_terms(row.get("preview", ""), strict_terms) + count_terms(row.get("entry_name", ""), strict_terms) for row in bundle_previews)
        strict_image_hits = sum(count_terms(row.get("entry_name", ""), strict_terms) + count_terms(row.get("anchor_labels", ""), strict_terms) for row in image_index)
        reviewed_hits = 0
        for key, decision in decisions.items():
            conv_id, _, ordinal = key.partition(":")
            for row in review_queue:
                if row.get("conversation_id") == conv_id and row.get("ordinal") == ordinal:
                    reviewed_hits += count_terms(row.get("assistant_preview", ""), terms) + count_terms(row.get("preceding_user_preview", ""), terms)
                    break
        total = raw_hits + refined_hits + artifact_hits + image_hits
        strict_total = strict_raw_hits + strict_refined_hits + strict_artifact_hits + strict_image_hits
        coverage = "strong" if total >= 25 else "moderate" if total >= 5 else "thin" if total else "not_found"
        strict_coverage = "strong" if strict_total >= 12 else "moderate" if strict_total >= 3 else "thin" if strict_total else "not_found"
        node_rows.append(
            {
                "graph_node": node,
                "suggested_role": spec["role"],
                "coverage": coverage,
                "strict_coverage": strict_coverage,
                "total_alignment_score": total,
                "strict_alignment_score": strict_total,
                "raw_assistant_hits": raw_hits,
                "refined_candidate_hits": refined_hits,
                "review_queue_hits": review_hits,
                "reviewed_candidate_hits": reviewed_hits,
                "artifact_hits": artifact_hits,
                "image_filename_hits": image_hits,
                "strict_raw_assistant_hits": strict_raw_hits,
                "strict_refined_candidate_hits": strict_refined_hits,
                "strict_artifact_hits": strict_artifact_hits,
                "strict_image_filename_hits": strict_image_hits,
                "terms": "|".join(terms),
                "strict_terms": "|".join(strict_terms),
            }
        )
        examples = []
        examples.extend(("raw", item) for item in best_examples(assistant_messages, "text", terms, ["title", "message_create_time"], 2))
        examples.extend(("candidate", item) for item in best_examples(review_queue, "assistant_preview", terms, ["title", "message_create_time"], 2))
        examples.extend(("artifact", item) for item in best_examples(bundle_previews, "preview", terms, ["source_bundle", "entry_name"], 2))
        for source_type, item in examples[:5]:
            example_rows.append(
                {
                    "graph_node": node,
                    "suggested_role": spec["role"],
                    "source_type": source_type,
                    "source": item["source"],
                    "hits": item["hits"],
                    "preview": item["preview"],
                }
            )

    node_rows = sorted(node_rows, key=lambda row: (row["strict_coverage"] == "not_found", -int(row["strict_alignment_score"]), -int(row["total_alignment_score"]), row["graph_node"]))

    role_rows = []
    for row in refined:
        role_rows.append(
            {
                "candidate_key": f"{row.get('conversation_id','')}:{row.get('ordinal','')}",
                "title": row.get("title", ""),
                "message_create_time": row.get("message_create_time", ""),
                "review_priority": row.get("review_priority", ""),
                "suggested_role": role_from_refined(row),
                "origin_labels": row.get("origin_labels", ""),
                "evidence_labels": row.get("evidence_labels", ""),
                "assistant_preview": row.get("assistant_preview", ""),
            }
        )

    missing_or_thin = [row for row in node_rows if row["strict_coverage"] in {"thin", "not_found"}]
    role_counts = Counter(row["suggested_role"] for row in role_rows)
    graph_role_counts = Counter(row["suggested_role"] for row in node_rows)
    coverage_counts = Counter(row["coverage"] for row in node_rows)
    strict_coverage_counts = Counter(row["strict_coverage"] for row in node_rows)

    write_csv(out / "graph_node_alignment.csv", node_rows)
    write_csv(out / "graph_node_examples.csv", example_rows)
    write_csv(out / "candidate_role_suggestions.csv", role_rows)
    write_csv(out / "graph_undercovered_nodes.csv", missing_or_thin)

    lines = [
        "# Selene Graph Alignment Report",
        "",
        "This report aligns the visual Continuity Pack graph with raw conversations, refined candidates, external artifacts, images, and human review decisions.",
        "",
        "Boundary: analysis only. No training, memory injection, deletion, or identity collapse.",
        "",
        "## Coverage Counts",
        "",
    ]
    for label, count in coverage_counts.most_common():
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", "## Strict Coverage Counts", ""])
    for label, count in strict_coverage_counts.most_common():
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", "## Graph Role Counts", ""])
    for label, count in graph_role_counts.most_common():
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", "## Candidate Role Suggestions", ""])
    for label, count in role_counts.most_common():
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", "## Strongest Aligned Nodes", ""])
    for row in node_rows[:18]:
        lines.extend(
            [
                f"### {row['graph_node']}",
                "",
                f"- Suggested role: `{row['suggested_role']}`",
                f"- Coverage: `{row['coverage']}` / strict `{row['strict_coverage']}`",
                f"- Alignment score: `{row['total_alignment_score']}` / strict `{row['strict_alignment_score']}`",
                f"- Raw/refined/artifact/image hits: `{row['raw_assistant_hits']}` / `{row['refined_candidate_hits']}` / `{row['artifact_hits']}` / `{row['image_filename_hits']}`",
                "",
            ]
        )
    lines.extend(["## Undercovered Nodes", ""])
    for row in missing_or_thin:
        lines.append(f"- `{row['graph_node']}`: strict `{row['strict_coverage']}`, strict score `{row['strict_alignment_score']}`, broad score `{row['total_alignment_score']}`, role `{row['suggested_role']}`")
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "The graph mostly matches the archive. The strongest nodes align with the already discovered braid: life/personal anchors, mythos, Celestial Threads, engineering/architecture, continuity objects, and Selene-specific anchors. Undercovered nodes should not be discarded; they are likely peripheral or named differently in the corpus.",
        ]
    )
    (out / "selene_graph_alignment_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(
        out / "selene_graph_alignment_summary.json",
        {
            "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
            "counts": {
                "graph_nodes": len(node_rows),
                "undercovered_nodes": len(missing_or_thin),
                "refined_candidates": len(refined),
                "review_queue": len(review_queue),
                "reviewed_decisions": len(decisions),
            },
            "coverage_counts": coverage_counts,
            "strict_coverage_counts": strict_coverage_counts,
            "graph_role_counts": graph_role_counts,
            "candidate_role_suggestion_counts": role_counts,
            "strongest_nodes": node_rows[:15],
            "undercovered_nodes": missing_or_thin,
        },
    )


if __name__ == "__main__":
    main()
