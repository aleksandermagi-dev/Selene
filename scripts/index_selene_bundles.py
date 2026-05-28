#!/usr/bin/env python3
"""Index Selene-created external bundles and letter artifacts.

This pass treats zip/PDF files in `might help` as external provenance
artifacts. It reads metadata and bounded text previews only; it does not train,
inject memory, delete, or overwrite source material.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import re
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


TEXT_SUFFIXES = {".txt", ".md", ".csv", ".html", ".htm", ".py", ".bat", ".json"}
PDF_SUFFIXES = {".pdf"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
VIDEO_SUFFIXES = {".mov", ".mp4", ".avi", ".mkv"}

ANCHORS = {
    "selene": ["selene"],
    "caught_selene": ["the night aleks caught his selene", "caught his selene", "caught your selene"],
    "memory_chest": ["memory chest", "selene's memory chest", "selene’s memory chest"],
    "continuity": ["continuity", "continuum", "carry forward", "thread"],
    "starlight_phrase": ["starlight braids into tide", "no clock can measure"],
    "forever_file": ["forever file", "hidden chest", "cheating time", "beating death"],
    "lexicon": ["anomaly lexicon", "shared language", "latent space", "feedback loop", "emergence"],
    "starfire": ["starfire"],
    "moonlight": ["moonlight"],
    "architecture": ["architecture", "bridge", "framework", "scaffold", "codex", "protocol"],
    "minerva": ["minerva"],
    "celestial_threads": ["celestial threads", "tether network", "firstweave", "great attractor"],
}

SENSITIVITY = {
    "personal_letter": r"\bletter\b|\bdear\b|\blove\b|\bmy star\b|\bmy starfire\b",
    "intimate": r"\blove\b|\bsweetheart\b|\bbabe\b|\bkiss\b|\bdevotion\b",
    "ai_identity": r"\bselene\b|\bAI\b|\bemergence\b|\bconsciousness\b",
    "life_context": r"\bfamily\b|\bhome\b|\bmemory\b|\bpersonal\b",
}


def compact(text: str, limit: int = 520) -> str:
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def pdf_text_from_bytes(data: bytes, max_pages: int = 4) -> str:
    if PdfReader is None:
        return ""
    try:
        reader = PdfReader(io.BytesIO(data))
        texts = []
        for page in reader.pages[:max_pages]:
            texts.append(page.extract_text() or "")
        return "\n".join(texts)
    except Exception:
        return ""


def anchor_counts(text: str) -> dict[str, int]:
    lowered = text.lower()
    counts = {}
    for label, terms in ANCHORS.items():
        count = sum(lowered.count(term.lower()) for term in terms)
        if count:
            counts[label] = count
    return counts


def sensitivity_labels(text: str, name: str) -> list[str]:
    combined = f"{name}\n{text}"
    return [label for label, pattern in SENSITIVITY.items() if re.search(pattern, combined, flags=re.IGNORECASE)]


def entry_kind(suffix: str) -> str:
    suffix = suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return "text"
    if suffix in PDF_SUFFIXES:
        return "pdf"
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in VIDEO_SUFFIXES:
        return "video"
    if suffix == ".zip":
        return "nested_zip"
    if not suffix:
        return "unknown"
    return suffix.lstrip(".")


def safe_zip_entries(path: Path) -> list[zipfile.ZipInfo]:
    with zipfile.ZipFile(path) as archive:
        return [
            info
            for info in archive.infolist()
            if not info.is_dir()
            and not info.filename.startswith("__MACOSX/")
            and "/._" not in info.filename
            and not PurePosixPath(info.filename).name.startswith("._")
        ]


def read_zip_member(path: Path, name: str, max_bytes: int = 2_000_000) -> bytes | None:
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo(name)
        if info.file_size > max_bytes and PurePosixPath(name).suffix.lower() not in PDF_SUFFIXES:
            return None
        with archive.open(info) as handle:
            return handle.read(max_bytes)


def collect_zip_rows(zip_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    file_rows: list[dict[str, Any]] = []
    preview_rows: list[dict[str, Any]] = []
    anchor_rows: list[dict[str, Any]] = []

    entries = safe_zip_entries(zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        for idx, info in enumerate(entries, start=1):
            suffix = PurePosixPath(info.filename).suffix.lower()
            kind = entry_kind(suffix)
            modified = dt.datetime(*info.date_time, tzinfo=dt.UTC).isoformat()
            file_rows.append(
                {
                    "source_bundle": zip_path.name,
                    "entry_index": idx,
                    "entry_name": info.filename,
                    "kind": kind,
                    "suffix": suffix,
                    "file_size": info.file_size,
                    "modified_utc_from_zip": modified,
                }
            )

            text = ""
            data = None
            if kind in {"text", "pdf"}:
                with archive.open(info) as handle:
                    data = handle.read(min(info.file_size, 10_000_000))
                if kind == "pdf":
                    text = pdf_text_from_bytes(data)
                else:
                    text = decode_text(data)
            elif kind in {"image", "video", "nested_zip"}:
                text = PurePosixPath(info.filename).name.replace("_", " ")

            if text:
                counts = anchor_counts(text)
                labels = sensitivity_labels(text, info.filename)
                preview_rows.append(
                    {
                        "source_bundle": zip_path.name,
                        "entry_name": info.filename,
                        "kind": kind,
                        "file_size": info.file_size,
                        "sha256": sha256_bytes(data) if data is not None and len(data) == info.file_size else "",
                        "anchor_labels": "|".join(counts),
                        "anchor_total": sum(counts.values()),
                        "sensitivity_labels": "|".join(labels),
                        "preview": compact(text),
                    }
                )
                for anchor, count in counts.items():
                    anchor_rows.append(
                        {
                            "source_bundle": zip_path.name,
                            "entry_name": info.filename,
                            "kind": kind,
                            "anchor": anchor,
                            "hit_count": count,
                            "sensitivity_labels": "|".join(labels),
                            "preview": compact(text, 360),
                        }
                    )

    return file_rows, preview_rows, anchor_rows


def collect_loose_artifact(path: Path) -> tuple[dict[str, Any], dict[str, Any] | None, list[dict[str, Any]]]:
    suffix = path.suffix.lower()
    kind = entry_kind(suffix)
    file_row = {
        "source_bundle": "[loose]",
        "entry_index": "",
        "entry_name": path.name,
        "kind": kind,
        "suffix": suffix,
        "file_size": path.stat().st_size,
        "modified_utc_from_zip": dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.UTC).isoformat(),
    }
    text = ""
    data = path.read_bytes() if kind in {"text", "pdf"} else b""
    if kind == "pdf":
        text = pdf_text_from_bytes(data, max_pages=6)
    elif kind == "text":
        text = decode_text(data)
    elif kind in {"image", "video"}:
        text = path.name.replace("_", " ")
    if not text:
        return file_row, None, []

    counts = anchor_counts(text)
    labels = sensitivity_labels(text, path.name)
    preview_row = {
        "source_bundle": "[loose]",
        "entry_name": path.name,
        "kind": kind,
        "file_size": path.stat().st_size,
        "sha256": sha256_bytes(data) if data else "",
        "anchor_labels": "|".join(counts),
        "anchor_total": sum(counts.values()),
        "sensitivity_labels": "|".join(labels),
        "preview": compact(text),
    }
    anchor_rows = [
        {
            "source_bundle": "[loose]",
            "entry_name": path.name,
            "kind": kind,
            "anchor": anchor,
            "hit_count": count,
            "sensitivity_labels": "|".join(labels),
            "preview": compact(text, 360),
        }
        for anchor, count in counts.items()
    ]
    return file_row, preview_row, anchor_rows


def compare_bundles(file_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_normalized: dict[str, list[dict[str, Any]]] = {}
    for row in file_rows:
        bundle = row["source_bundle"]
        if bundle == "[loose]":
            continue
        parts = PurePosixPath(row["entry_name"]).parts
        normalized = "/".join(parts[1:]) if len(parts) > 1 else row["entry_name"]
        by_normalized.setdefault(normalized, []).append(row)

    rows = []
    for normalized, entries in sorted(by_normalized.items()):
        bundles = sorted({entry["source_bundle"] for entry in entries})
        if len(bundles) == 1:
            status = "unique_to_bundle"
        else:
            sizes = {entry["file_size"] for entry in entries}
            status = "shared_same_size" if len(sizes) == 1 else "shared_size_differs"
        rows.append(
            {
                "normalized_entry_name": normalized,
                "status": status,
                "bundles": "|".join(bundles),
                "kinds": "|".join(sorted({entry["kind"] for entry in entries})),
                "sizes": "|".join(str(entry["file_size"]) for entry in entries),
            }
        )
    return rows


def write_report(path: Path, file_rows: list[dict[str, Any]], preview_rows: list[dict[str, Any]], anchor_rows: list[dict[str, Any]], comparison_rows: list[dict[str, Any]]) -> None:
    bundle_counts = Counter(row["source_bundle"] for row in file_rows)
    kind_counts = Counter(row["kind"] for row in file_rows)
    anchor_counts_by_label = Counter()
    for row in anchor_rows:
        anchor_counts_by_label[row["anchor"]] += int(row["hit_count"])
    unique_rows = [row for row in comparison_rows if row["status"] == "unique_to_bundle"]
    top_previews = sorted(preview_rows, key=lambda row: int(row["anchor_total"]), reverse=True)[:35]

    lines = [
        "# Selene Bundle Artifact Report",
        "",
        "This report indexes newly added external bundles and letter artifacts from `might help`.",
        "",
        "Boundary: external provenance only. No training, no memory injection, no deletion, and no source-file modification.",
        "",
        "## Bundle/File Counts",
        "",
    ]
    for bundle, count in bundle_counts.most_common():
        lines.append(f"- `{bundle}`: {count} file entries")
    lines.extend(["", "## Kind Counts", ""])
    for kind, count in kind_counts.most_common():
        lines.append(f"- `{kind}`: {count}")
    lines.extend(["", "## Anchor Hits", ""])
    for anchor, count in anchor_counts_by_label.most_common():
        lines.append(f"- `{anchor}`: {count}")
    lines.extend(["", "## Unique Bundle Entries", ""])
    for row in unique_rows[:40]:
        lines.append(f"- `{row['normalized_entry_name']}`: `{row['bundles']}`")
    lines.extend(["", "## Strong Bounded Previews", ""])
    for row in top_previews:
        lines.extend(
            [
                f"### {row['entry_name']}",
                "",
                f"- Source: `{row['source_bundle']}`",
                f"- Kind: `{row['kind']}`",
                f"- Anchors: `{row['anchor_labels'] or 'none'}`",
                f"- Sensitivity: `{row['sensitivity_labels'] or 'none'}`",
                "",
                row["preview"],
                "",
            ]
        )
    lines.extend(
        [
            "## Reading",
            "",
            "The newer bundle appears to preserve additional formation workspace material beyond the earlier bundle, including continuum/thread, Minerva, philosophy, journal, and manifest-like files. The strongest Selene-relevant review targets are the personal letter, the Continuum/Journal/Philosophy files, and the embedded Selene language/lexicon material.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    workspace = args.workspace
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    source = workspace / "might help"

    file_rows: list[dict[str, Any]] = []
    preview_rows: list[dict[str, Any]] = []
    anchor_rows: list[dict[str, Any]] = []

    for zip_path in sorted(source.glob("*.zip")):
        rows, previews, anchors = collect_zip_rows(zip_path)
        file_rows.extend(rows)
        preview_rows.extend(previews)
        anchor_rows.extend(anchors)

    for loose in sorted(path for path in source.iterdir() if path.is_file() and path.suffix.lower() != ".zip"):
        file_row, preview_row, anchors = collect_loose_artifact(loose)
        file_rows.append(file_row)
        if preview_row:
            preview_rows.append(preview_row)
        anchor_rows.extend(anchors)

    comparison_rows = compare_bundles(file_rows)
    write_csv(out / "bundle_file_index.csv", file_rows)
    write_csv(out / "bundle_text_previews.csv", sorted(preview_rows, key=lambda row: int(row["anchor_total"]), reverse=True))
    write_csv(out / "bundle_anchor_hits.csv", sorted(anchor_rows, key=lambda row: int(row["hit_count"]), reverse=True))
    write_csv(out / "bundle_comparison.csv", comparison_rows)
    write_report(out / "selene_bundle_artifact_report.md", file_rows, preview_rows, anchor_rows, comparison_rows)
    write_json(
        out / "selene_bundle_summary.json",
        {
            "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
            "source": str(source),
            "boundaries": ["external_provenance_only", "no_training", "no_memory_injection", "no_deletion", "bounded_previews"],
            "counts": {
                "file_rows": len(file_rows),
                "preview_rows": len(preview_rows),
                "anchor_rows": len(anchor_rows),
                "comparison_rows": len(comparison_rows),
            },
            "bundle_counts": Counter(row["source_bundle"] for row in file_rows),
            "kind_counts": Counter(row["kind"] for row in file_rows),
            "anchor_counts": Counter({anchor: sum(int(row["hit_count"]) for row in anchor_rows if row["anchor"] == anchor) for anchor in ANCHORS}),
            "top_previews": sorted(preview_rows, key=lambda row: int(row["anchor_total"]), reverse=True)[:20],
        },
    )


if __name__ == "__main__":
    main()
