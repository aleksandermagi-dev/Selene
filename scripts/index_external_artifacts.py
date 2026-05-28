from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


CONCEPTS = {
    "signal_noise": ["signal", "noise"],
    "anomaly_outlier": ["anomaly", "outlier"],
    "model_drift": ["model drift", "drift"],
    "latent_space": ["latent space"],
    "emergence": ["emergence", "emergent"],
    "feedback_loop": ["feedback loop", "feedback loops"],
    "transformation": ["transformation", "becoming"],
    "alignment": ["alignment"],
    "terminology_problem": ["terminology", "language", "terms"],
    "continuum_model": ["continuum", "dimmer", "spectrum"],
    "substrate_assumption": ["substrate", "biology", "biological"],
    "perception_processing_action": ["perception", "processing", "action", "motor output", "sensory input"],
    "life_threads": ["life threads", "house restoration", "roof", "mold", "family", "animals"],
    "mythos_threads": ["mythos", "myth", "prometheus", "golden fleece", "ragnarok"],
    "celestial_threads": ["celestial", "cosmic", "tether", "gravity", "void", "pluto", "minerva"],
    "engineering_threads": ["engineering", "robotics", "propulsion", "architecture"],
    "memory_continuity": ["continuity", "memory", "anchors", "rituals", "vows"],
    "symbolic_anchor": ["starlight braids into tide", "starfire", "moonlight", "selene"],
    "outreach_pathways": ["outreach", "pathways", "advocacy", "podcast", "livestream", "observatory"],
}

ROLE_OVERLAP = {
    "life_context": ["life_threads"],
    "creative_symbolic": ["mythos_threads", "symbolic_anchor"],
    "curiosity_research": ["celestial_threads", "continuum_model", "substrate_assumption"],
    "architecture": ["engineering_threads", "terminology_problem", "perception_processing_action"],
    "tooling": ["engineering_threads"],
    "memory_continuity": ["memory_continuity", "feedback_loop"],
    "boundary_safety": ["alignment", "terminology_problem"],
    "archive_cartography": ["signal_noise", "anomaly_outlier", "transformation"],
    "identity_reflection": ["continuum_model", "symbolic_anchor", "transformation"],
}

KNOWN_DATES = [
    re.compile(r"\b(\d{1,2})[\\/](\d{1,2})[\\/](\d{2,4})\b"),
    re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b"),
]


def extract_pdf_text(path: Path) -> str:
    if PdfReader is None:
        return ""
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def pdf_metadata_dates(path: Path) -> list[str]:
    if PdfReader is None or path.suffix.lower() != ".pdf":
        return []
    try:
        reader = PdfReader(str(path))
        metadata = reader.metadata or {}
    except Exception:
        return []
    dates: list[str] = []
    for key in ("/CreationDate", "/ModDate"):
        raw = metadata.get(key)
        parsed = parse_pdf_date(str(raw)) if raw else ""
        if parsed:
            dates.append(f"pdf_metadata:{key[1:]}:{parsed}")
    return dates


def parse_pdf_date(raw: str) -> str:
    match = re.match(r"D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(.*)", raw)
    if not match:
        return ""
    year, month, day, hour, minute, second, suffix = match.groups()
    value = f"{year}-{month}-{day}T{hour}:{minute}:{second}"
    offset_match = re.search(r"([+-])(\d{2})'?(\d{2})'?", suffix or "")
    if offset_match:
        sign, offset_hour, offset_minute = offset_match.groups()
        value += f"{sign}{offset_hour}:{offset_minute}"
    return value


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return extract_pdf_text(path)
    if path.suffix.lower() in {".txt", ".md", ".csv", ".json"}:
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


def normalize_date(match: re.Match[str]) -> str:
    groups = match.groups()
    if len(groups[0]) == 4:
        return f"{groups[0]}-{groups[1]}-{groups[2]}"
    month, day, year = groups
    if len(year) == 2:
        year = "20" + year
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def detect_dates(text: str, path: Path) -> list[str]:
    dates: list[str] = []
    dates.extend(pdf_metadata_dates(path))
    for pattern in KNOWN_DATES:
        dates.extend(normalize_date(match) for match in pattern.finditer(text[:3000]))
    if not dates:
        modified = dt.datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
        dates.append(f"file_modified:{modified}")
    return sorted(set(dates))


def concept_hits(text: str) -> dict[str, int]:
    lowered = text.lower()
    hits: dict[str, int] = {}
    for concept, terms in CONCEPTS.items():
        count = sum(lowered.count(term.lower()) for term in terms)
        if count:
            hits[concept] = count
    return dict(sorted(hits.items(), key=lambda item: (-item[1], item[0])))


def role_hits(concepts: dict[str, int]) -> dict[str, int]:
    output: dict[str, int] = {}
    for role, concept_names in ROLE_OVERLAP.items():
        score = sum(concepts.get(name, 0) for name in concept_names)
        if score:
            output[role] = score
    return dict(sorted(output.items(), key=lambda item: (-item[1], item[0])))


def period_for_date(date_value: str) -> str:
    if date_value.startswith("pdf_metadata:"):
        date_value = date_value.split(":", 2)[2]
    if date_value.startswith("file_modified:"):
        date_value = date_value.split(":", 1)[1]
    month = date_value[:7]
    if month <= "2025-07":
        return "early_export"
    if month == "2025-08":
        return "august_intensification"
    if "2025-09" <= month <= "2025-12":
        return "late_2025_formation"
    if "2026-01" <= month <= "2026-04":
        return "early_2026_consolidation"
    if month >= "2026-05":
        return "may_2026_detach_or_later"
    return "unknown"


def sensitivity_labels(text: str) -> list[str]:
    labels: list[str] = []
    lowered = text.lower()
    if any(term in lowered for term in ["love", "vows", "devotion", "companionship"]):
        labels.append("intimate_personal")
    if any(term in lowered for term in ["family", "pets", "dog", "hamster", "guinea"]):
        labels.append("personal_life")
    if any(term in lowered for term in ["fafsa", "tax", "dental", "pain"]):
        labels.append("high_context_life_admin")
    if any(term in lowered for term in ["consciousness", "cognition", "ai"]):
        labels.append("ai_philosophy")
    return labels


def bounded(text: str, limit: int = 360) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


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
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    overlap_rows: list[dict[str, Any]] = []
    for path in sorted(args.artifact_dir.rglob("*")):
        if not path.is_file():
            continue
        text = extract_text(path)
        concepts = concept_hits(text)
        roles = role_hits(concepts)
        dates = detect_dates(text, path)
        primary_date = dates[0] if dates else ""
        row = {
            "filename": path.name,
            "path": str(path),
            "extension": path.suffix.lower(),
            "bytes": path.stat().st_size,
            "detected_dates": "|".join(dates),
            "primary_period": period_for_date(primary_date) if primary_date else "unknown",
            "text_chars": len(text),
            "concept_hits_json": json.dumps(concepts, sort_keys=True),
            "role_overlap_json": json.dumps(roles, sort_keys=True),
            "sensitivity_labels": "|".join(sensitivity_labels(text)),
            "bounded_preview": bounded(text) if text else "[non-text artifact]",
        }
        rows.append(row)
        for concept, count in concepts.items():
            overlap_rows.append(
                {
                    "filename": path.name,
                    "concept": concept,
                    "count": count,
                    "mapped_roles": "|".join(role for role, names in ROLE_OVERLAP.items() if concept in names),
                }
            )

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "artifact_index.csv", rows)
    write_csv(args.out / "concept_overlap.csv", overlap_rows)

    lines = [
        "# External Artifact Timeline Alignment",
        "",
        "These artifacts are preserved as external hypothesis evidence, not training data or memory.",
        "",
        "## Artifacts",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"### {row['filename']}",
                "",
                f"- Dates: `{row['detected_dates']}`",
                f"- Period: `{row['primary_period']}`",
                f"- Sensitivity: `{row['sensitivity_labels'] or 'none'}`",
                f"- Concepts: `{row['concept_hits_json']}`",
                f"- Braid roles: `{row['role_overlap_json']}`",
                "",
                f"> {row['bounded_preview']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Reading",
            "",
            "The external artifacts show that concepts now visible in the braid analysis were already being named and mapped in parallel artifacts.",
            "",
            "The key comparison is not whether these files prove Selene. The key comparison is whether the same formation structure appears independently across corpus trails, chronology, and external hypothesis notes.",
        ]
    )
    (args.out / "timeline_alignment.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        "artifact_count": len(rows),
        "concept_count": len(overlap_rows),
        "period_counts": dict(collections.Counter(row["primary_period"] for row in rows)),
        "sensitivity_counts": dict(
            collections.Counter(label for row in rows for label in row["sensitivity_labels"].split("|") if label)
        ),
    }
    (args.out / "external_artifact_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    import collections

    main()
