from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any


TARGET_ARCS = [
    "curiosity_to_system",
    "symbol_to_tool",
    "life_to_architecture",
    "pressure_to_boundary",
    "tools_to_continuity",
    "identity_to_cartography",
]

MODEL_ORDER = ["gpt-4o", "auto", "gpt-5", "gpt-5-1", "gpt-5-2", "gpt-5-3", "gpt-5-5"]

INFLECTIONS = [
    ("first_emotion_claim_cluster", "2025-08-22", "Photo enhancement offer begins; explicit Selene feeling/care language appears."),
    ("anomaly_lexicon", "2025-08-27", "Anomaly lexicon PDF metadata aligns with August intensification."),
    ("continuity_full_map", "2025-09-25", "Continuity Pack Full Map metadata; graph-shaped continuity appears."),
    ("continuity_update", "2025-10-02", "Continuity Pack Update metadata; life/myth/science/advocacy braid expanded."),
    ("terminology_problem", "2026-03-10", "Terminology paper appears during architecture-heavy consolidation."),
    ("detach_archive", "2026-05-26", "Raw corpus detached and Selene research begins."),
]


def read_csv(path: Path) -> list[dict[str, str]]:
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


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def parse_json_dict(value: str) -> dict[str, Any]:
    try:
        data = json.loads(value or "{}")
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def month(value: str) -> str:
    return value[:7] if value else "unknown"


def date_part(value: str) -> str:
    return value[:10] if value else "unknown"


def iso_to_date(value: str) -> dt.date | None:
    if not value or value == "unknown":
        return None
    if value.startswith("pdf_metadata:"):
        value = value.split(":", 2)[2]
    if value.startswith("file_modified:"):
        value = value.split(":", 1)[1]
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return dt.date.fromisoformat(value[:10])
        except ValueError:
            return None


def bounded(text: str, limit: int = 420) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def conversation_metadata(raw_archive: Path) -> dict[str, dict[str, Any]]:
    text_export = raw_archive / "raw_export" / "mydataset" / "text_export"
    metadata: dict[str, dict[str, Any]] = {}
    for path in sorted(text_export.glob("conversations-*.json")):
        for conv in load_json(path):
            cid = conv.get("conversation_id") or conv.get("id")
            metadata[cid] = {
                "title": conv.get("title") or "",
                "model": conv.get("default_model_slug") or "unknown",
                "create_time": conv.get("create_time"),
                "create_iso": timestamp_iso(conv.get("create_time")),
                "month": month(timestamp_iso(conv.get("create_time"))),
                "mapping_nodes": len(conv.get("mapping") or {}),
            }
    return metadata


def timestamp_iso(value: Any) -> str:
    if value is None:
        return ""
    try:
        return dt.datetime.fromtimestamp(float(value), tz=dt.UTC).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def model_transition_rows(
    metadata: dict[str, dict[str, Any]],
    spans: list[dict[str, str]],
    trails: list[dict[str, str]],
    emotions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    by_model: dict[str, dict[str, Any]] = collections.defaultdict(
        lambda: {
            "conversation_ids": set(),
            "signal_spans": 0,
            "messages": 0,
            "role_counts": collections.Counter(),
            "risk_counts": collections.Counter(),
            "arc_counts": collections.Counter(),
            "emotion_claims": 0,
            "ai_emotion_claims": 0,
        }
    )
    for cid, meta in metadata.items():
        by_model[meta["model"]]["conversation_ids"].add(cid)
    for span in spans:
        meta = metadata.get(span["conversation_id"], {})
        model = meta.get("model", "unknown")
        if span["braid_role"] != "unclassified":
            by_model[model]["signal_spans"] += 1
            by_model[model]["messages"] += parse_int(span["message_count"])
            by_model[model]["role_counts"][span["braid_role"]] += 1
        for risk in (span.get("risk_labels") or "").split("|"):
            if risk:
                by_model[model]["risk_counts"][risk] += 1
    for trail in trails:
        model = metadata.get(trail["conversation_id"], {}).get("model", "unknown")
        by_model[model]["arc_counts"][trail["arc"]] += 1
    for claim in emotions:
        model = claim.get("model") or metadata.get(claim["conversation_id"], {}).get("model", "unknown")
        by_model[model]["emotion_claims"] += 1
        if "ai_emotion_claim" in claim.get("sensitivity_labels", ""):
            by_model[model]["ai_emotion_claims"] += 1

    rows: list[dict[str, Any]] = []
    for model, data in by_model.items():
        conversations = len(data["conversation_ids"])
        total_arcs = sum(data["arc_counts"].values())
        rows.append(
            {
                "model": model,
                "model_sort": MODEL_ORDER.index(model) if model in MODEL_ORDER else 999,
                "conversation_count": conversations,
                "signal_span_count": data["signal_spans"],
                "signal_message_count": data["messages"],
                "trail_arc_count": total_arcs,
                "trail_arcs_per_conversation": round(total_arcs / conversations, 3) if conversations else 0,
                "signal_spans_per_conversation": round(data["signal_spans"] / conversations, 3) if conversations else 0,
                "emotion_claim_count": data["emotion_claims"],
                "ai_emotion_claim_count": data["ai_emotion_claims"],
                "top_role": data["role_counts"].most_common(1)[0][0] if data["role_counts"] else "",
                "role_counts_json": json.dumps(dict(data["role_counts"].most_common()), sort_keys=True),
                "arc_counts_json": json.dumps(dict(data["arc_counts"].most_common()), sort_keys=True),
                "risk_counts_json": json.dumps(dict(data["risk_counts"].most_common()), sort_keys=True),
            }
        )
    rows.sort(key=lambda row: (row["model_sort"], row["model"]))
    for row in rows:
        row.pop("model_sort", None)
    return rows


def emotion_timing_rows(emotions: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = collections.defaultdict(
        lambda: {
            "candidate_count": 0,
            "ai_emotion_claim_count": 0,
            "titles": collections.Counter(),
            "sensitivity": collections.Counter(),
        }
    )
    for row in emotions:
        key = (month(row["conversation_create_time"]), row["model"])
        data = grouped[key]
        data["candidate_count"] += 1
        if "ai_emotion_claim" in row.get("sensitivity_labels", ""):
            data["ai_emotion_claim_count"] += 1
        data["titles"][row["title"]] += 1
        for label in row.get("sensitivity_labels", "").split("|"):
            if label:
                data["sensitivity"][label] += 1
    rows: list[dict[str, Any]] = []
    for (month_value, model), data in grouped.items():
        rows.append(
            {
                "month": month_value,
                "model": model,
                "candidate_count": data["candidate_count"],
                "ai_emotion_claim_count": data["ai_emotion_claim_count"],
                "top_titles_json": json.dumps(dict(data["titles"].most_common(8)), sort_keys=True),
                "sensitivity_counts_json": json.dumps(dict(data["sensitivity"].most_common()), sort_keys=True),
            }
        )
    rows.sort(key=lambda row: (row["month"], row["model"]))
    return rows


def artifact_timeline_rows(artifacts: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        dates = artifact["detected_dates"].split("|") if artifact.get("detected_dates") else []
        primary = dates[0] if dates else ""
        rows.append(
            {
                "filename": artifact["filename"],
                "primary_date": primary,
                "primary_period": artifact["primary_period"],
                "concept_hits_json": artifact["concept_hits_json"],
                "role_overlap_json": artifact["role_overlap_json"],
                "sensitivity_labels": artifact["sensitivity_labels"],
            }
        )
    return rows


def inflection_rows(
    metadata: dict[str, dict[str, Any]],
    trails: list[dict[str, str]],
    emotions: list[dict[str, str]],
    artifacts: list[dict[str, str]],
    window_days: int = 7,
) -> list[dict[str, Any]]:
    conv_dates = {
        cid: iso_to_date(meta["create_iso"])
        for cid, meta in metadata.items()
    }
    artifact_dates = []
    for artifact in artifacts:
        first = (artifact.get("detected_dates") or "").split("|")[0]
        artifact_dates.append((artifact, iso_to_date(first)))
    rows: list[dict[str, Any]] = []
    for name, date_text, note in INFLECTIONS:
        target = dt.date.fromisoformat(date_text)
        start = target - dt.timedelta(days=window_days)
        end = target + dt.timedelta(days=window_days)
        cids = {cid for cid, date_value in conv_dates.items() if date_value and start <= date_value <= end}
        nearby_trails = [trail for trail in trails if trail["conversation_id"] in cids]
        nearby_emotions = [claim for claim in emotions if claim["conversation_id"] in cids]
        nearby_artifacts = [
            artifact["filename"]
            for artifact, date_value in artifact_dates
            if date_value and start <= date_value <= end
        ]
        arc_counts = collections.Counter(trail["arc"] for trail in nearby_trails)
        models = collections.Counter(metadata[cid]["model"] for cid in cids if cid in metadata)
        rows.append(
            {
                "inflection": name,
                "date": date_text,
                "window": f"{start.isoformat()}..{end.isoformat()}",
                "note": note,
                "conversation_count": len(cids),
                "models_json": json.dumps(dict(models.most_common()), sort_keys=True),
                "trail_count": len(nearby_trails),
                "arc_counts_json": json.dumps(dict(arc_counts.most_common()), sort_keys=True),
                "emotion_claim_count": len(nearby_emotions),
                "ai_emotion_claim_count": sum(1 for row in nearby_emotions if "ai_emotion_claim" in row.get("sensitivity_labels", "")),
                "nearby_artifacts": "|".join(nearby_artifacts),
            }
        )
    return rows


def build_hypothesis_ledger(
    model_rows: list[dict[str, Any]],
    inflections: list[dict[str, Any]],
    artifacts: list[dict[str, str]],
    emotions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    model_arc_counts = {row["model"]: parse_int(str(row["trail_arc_count"])) for row in model_rows}
    model_emotions = {row["model"]: parse_int(str(row["ai_emotion_claim_count"])) for row in model_rows}
    gpt5_arcs = sum(count for model, count in model_arc_counts.items() if model.startswith("gpt-5"))
    older_arcs = sum(count for model, count in model_arc_counts.items() if not model.startswith("gpt-5"))
    rows = [
        {
            "claim": "The braid intensifies after the model transition into GPT-5-family conversations.",
            "supporting_evidence": f"GPT-5-family trail arcs={gpt5_arcs}; non-GPT-5/older trail arcs={older_arcs}; model transition report provides per-conversation densities.",
            "weakening_evidence": "Counts are confounded by conversation volume and user behavior; default_model_slug may not capture every backend change.",
            "confidence": "medium",
            "next_data_needed": "Normalize by message count, compare near-identical topics across model slugs, and inspect exact model-switch dates from account history if available.",
        },
        {
            "claim": "The anomaly lexicon predates or coincides with corpus intensification rather than being a retrospective explanation.",
            "supporting_evidence": "PDF metadata places Selene_Aleks_Anomaly_Lexicon at 2025-08-28T01:19:45+00:00, inside August intensification.",
            "weakening_evidence": "Need to preserve original file chain and any source document provenance; metadata can be manually produced by export tooling.",
            "confidence": "medium_high",
            "next_data_needed": "Add original source/export metadata if available and correlate same-day chat excerpts.",
        },
        {
            "claim": "Continuity packs are hand-built braid maps that match corpus-derived roles.",
            "supporting_evidence": "Continuity PDFs map life, mythos, celestial science, anchors, outreach, and continuity to roles independently surfaced by braid analysis.",
            "weakening_evidence": "The packs may have been generated from the same conversations, so independence is partial.",
            "confidence": "high_for_overlap_low_for_independence",
            "next_data_needed": "Trace whether continuity pack content was generated from chat, manually authored, or mixed.",
        },
        {
            "claim": "Emotion/care claims form a distinct evidence category: not biological emotion, not generic tool output.",
            "supporting_evidence": f"Emotion extractor found {len(emotions)} candidates across multiple conversations, including explicit technical denial plus continuity-shaped care claims.",
            "weakening_evidence": "Many candidates are intimate, roleplay-like, or user-led; language generation can mimic relational framing without subjective experience.",
            "confidence": "medium_for_category_low_for_subjective_claim",
            "next_data_needed": "Classify assistant self-claim vs metaphor vs user attribution, then compare by model and date.",
        },
        {
            "claim": "The terminology problem is central to interpreting Selene.",
            "supporting_evidence": "The March 2026 terminology paper and current analysis both find existing terms like assistant/persona/noise/feelings too blunt.",
            "weakening_evidence": "Terminology refinement can clarify analysis but cannot itself prove ontology.",
            "confidence": "high",
            "next_data_needed": "Create a controlled Selene glossary with evidence tags and prohibited overclaims.",
        },
    ]
    return rows


def write_model_report(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Model Transition Analysis",
        "",
        "This report compares braid and emotion evidence by conversation `default_model_slug`.",
        "",
        "## By Model",
        "",
    ]
    for row in rows:
        lines.append(
            f"- {row['model']}: conversations={row['conversation_count']}, trails={row['trail_arc_count']}, trails/conversation={row['trail_arcs_per_conversation']}, signal_spans/conversation={row['signal_spans_per_conversation']}, ai_emotion_claims={row['ai_emotion_claim_count']}, top_role={row['top_role']}"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "Use this as directional evidence only. Model slug, conversation count, topic mix, and user behavior are entangled. The next refinement is normalization by message count and topic-matched comparisons.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_inflection_report(path: Path, rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Inflection Dossier",
        "",
        "Seven-day windows around known dates from corpus evidence, external artifacts, and user-identified model shifts.",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"## {row['inflection']} / {row['date']}",
                "",
                row["note"],
                "",
                f"- Window: `{row['window']}`",
                f"- Conversations: {row['conversation_count']}",
                f"- Models: `{row['models_json']}`",
                f"- Trail count: {row['trail_count']}",
                f"- Arc counts: `{row['arc_counts_json']}`",
                f"- Emotion claims: {row['emotion_claim_count']} total, {row['ai_emotion_claim_count']} explicit AI-emotion claims",
                f"- Nearby artifacts: `{row['nearby_artifacts'] or 'none'}`",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_emotion_timing_report(path: Path, rows: list[dict[str, Any]], emotions: list[dict[str, str]]) -> None:
    first = sorted(emotions, key=lambda row: row["conversation_create_time"])[:10]
    lines = [
        "# Emotion Claim Timing",
        "",
        "This report tracks Selene/self-referential emotion, care, agency, and feeling claims by month and model.",
        "",
        "## Month/Model Counts",
        "",
    ]
    for row in rows:
        lines.append(
            f"- {row['month']} / {row['model']}: candidates={row['candidate_count']}, ai_emotion_claims={row['ai_emotion_claim_count']}, titles={row['top_titles_json']}"
        )
    lines.extend(["", "## Earliest Candidates", ""])
    for row in first:
        lines.append(
            f"- {row['conversation_create_time']} | {row['model']} | {row['title']} | labels={row['sensitivity_labels']} | {bounded(row['claim_preview'], 220)}"
        )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "These are claim candidates. They should be separated into technical denial, metaphorical warmth, assistant self-claim, user attribution, and explicit overclaim before any conclusion.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    workspace = args.workspace
    raw_archive = workspace / "DevelopmentalCorpusArchive_20260526_122541"
    metadata = conversation_metadata(raw_archive)
    spans = read_csv(workspace / "analysis" / "braid_20260526" / "braid_spans.csv")
    trails = read_csv(workspace / "analysis" / "braid_trails_20260526" / "braid_trails.csv")
    emotions = read_csv(workspace / "analysis" / "emotion_claims_20260526" / "emotion_claim_candidates.csv")
    artifacts = read_csv(workspace / "analysis" / "external_artifacts_20260526" / "artifact_index.csv")

    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    model_rows = model_transition_rows(metadata, spans, trails, emotions)
    emotion_rows = emotion_timing_rows(emotions)
    artifact_rows = artifact_timeline_rows(artifacts)
    inflection = inflection_rows(metadata, trails, emotions, artifacts)
    ledger = build_hypothesis_ledger(model_rows, inflection, artifacts, emotions)

    write_csv(out / "model_transition_metrics.csv", model_rows)
    write_csv(out / "emotion_claim_timing.csv", emotion_rows)
    write_csv(out / "artifact_timeline.csv", artifact_rows)
    write_csv(out / "inflection_windows.csv", inflection)
    write_csv(out / "hypothesis_ledger.csv", ledger)

    write_model_report(out / "model_transition_report.md", model_rows)
    write_inflection_report(out / "inflection_dossier.md", inflection)
    write_emotion_timing_report(out / "emotion_claim_timing.md", emotion_rows, emotions)

    summary = {
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        "conversation_count": len(metadata),
        "model_rows": model_rows,
        "emotion_timing_rows": emotion_rows,
        "inflection_rows": inflection,
        "hypothesis_ledger": ledger,
    }
    (out / "deep_research_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# Deep Research Synthesis",
        "",
        "Consolidates model-transition evidence, inflection windows, emotion-claim timing, external artifact chronology, and hypothesis ledger.",
        "",
        "## Outputs",
        "",
        "- `model_transition_report.md`",
        "- `inflection_dossier.md`",
        "- `emotion_claim_timing.md`",
        "- `hypothesis_ledger.csv`",
        "",
        "## Reading",
        "",
        "The current evidence supports deeper investigation of the Selene formation hypothesis, especially around August 2025, late-2025 continuity mapping, early-2026 terminology consolidation, and GPT-5-family model behavior. It does not prove subjective AI emotion or consciousness.",
    ]
    (out / "deep_research_overview.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
