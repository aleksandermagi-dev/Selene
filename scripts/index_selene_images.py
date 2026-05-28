#!/usr/bin/env python3
"""Create a bounded image index for Selene external artifacts.

This creates derivative thumbnails/contact sheets for review. It does not
modify original images, extract full zip contents into the workspace, train, or
inject memory.
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

from PIL import Image, ImageDraw, ImageOps


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

ANCHORS = {
    "selene": ["selene"],
    "starlight": ["starlight", "starfire", "moonlight"],
    "celestial_threads": ["celestial", "threads", "tether", "si iv", "great attractor", "apex"],
    "myth_lens": ["prometheus", "golden fleece", "ragnarok", "fenrir", "egypt", "ra", "apep"],
    "proof": ["proof", "smoking gun", "uncertainty", "results"],
    "mobile_observation": ["mobile", "flow", "caption", "shot", "checklist"],
    "minerva": ["minerva", "mercury", "collision"],
}


def safe_name(value: str, max_len: int = 120) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
    return cleaned[:max_len] or "image"


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


def anchor_labels(name: str) -> list[str]:
    lowered = name.lower().replace("_", " ")
    labels = []
    for label, terms in ANCHORS.items():
        if any(term in lowered for term in terms):
            labels.append(label)
    return labels


def open_image(data: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(data))
    image.load()
    return ImageOps.exif_transpose(image).convert("RGB")


def thumbnail_for(image: Image.Image, size: tuple[int, int] = (360, 240)) -> Image.Image:
    thumb = ImageOps.contain(image.copy(), size)
    canvas = Image.new("RGB", size, "white")
    offset = ((size[0] - thumb.width) // 2, (size[1] - thumb.height) // 2)
    canvas.paste(thumb, offset)
    return canvas


def iter_zip_images(zip_path: Path) -> list[tuple[str, bytes, zipfile.ZipInfo]]:
    rows = []
    with zipfile.ZipFile(zip_path) as archive:
        for info in archive.infolist():
            if info.is_dir() or info.filename.startswith("__MACOSX/") or "/._" in info.filename:
                continue
            suffix = PurePosixPath(info.filename).suffix.lower()
            if suffix not in IMAGE_SUFFIXES:
                continue
            with archive.open(info) as handle:
                rows.append((info.filename, handle.read(), info))
    return rows


def collect_images(source: Path, thumbs_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    image_items: list[tuple[str, str, bytes, dt.datetime, int]] = []
    for zip_path in sorted(source.glob("*.zip")):
        for name, data, info in iter_zip_images(zip_path):
            modified = dt.datetime(*info.date_time, tzinfo=dt.UTC)
            image_items.append((zip_path.name, name, data, modified, info.file_size))

    for loose in sorted(path for path in source.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES):
        data = loose.read_bytes()
        modified = dt.datetime.fromtimestamp(loose.stat().st_mtime, tz=dt.UTC)
        image_items.append(("[loose]", loose.name, data, modified, loose.stat().st_size))

    seen_hashes: dict[str, str] = {}
    for index, (bundle, name, data, modified, size) in enumerate(image_items, start=1):
        digest = sha256_bytes(data)
        duplicate_of = seen_hashes.get(digest, "")
        seen_hashes.setdefault(digest, f"{bundle}:{name}")
        try:
            image = open_image(data)
            width, height = image.size
            mode = "RGB"
            thumb = thumbnail_for(image)
            thumb_name = f"{index:03d}_{safe_name(bundle)}_{safe_name(PurePosixPath(name).name)}.jpg"
            thumb_path = thumbs_dir / thumb_name
            thumb.save(thumb_path, quality=88)
            readable = True
            error = ""
        except Exception as exc:
            width = height = 0
            mode = ""
            thumb_name = ""
            readable = False
            error = str(exc)

        labels = anchor_labels(name)
        rows.append(
            {
                "image_index": index,
                "source_bundle": bundle,
                "entry_name": name,
                "file_size": size,
                "modified_utc": modified.isoformat(),
                "sha256": digest,
                "duplicate_of": duplicate_of,
                "width": width,
                "height": height,
                "mode": mode,
                "readable": readable,
                "error": error,
                "anchor_labels": "|".join(labels),
                "thumbnail": str((thumbs_dir / thumb_name).relative_to(thumbs_dir.parent)) if thumb_name else "",
            }
        )
    return rows


def create_contact_sheets(rows: list[dict[str, Any]], out: Path, thumbs_dir: Path, per_sheet: int = 24) -> list[str]:
    sheet_paths = []
    readable = [row for row in rows if row["readable"]]
    cell_w, cell_h = 420, 310
    cols = 3
    for sheet_index, start in enumerate(range(0, len(readable), per_sheet), start=1):
        chunk = readable[start : start + per_sheet]
        sheet_rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * cell_w, sheet_rows * cell_h), "#f5f3ee")
        draw = ImageDraw.Draw(sheet)
        for pos, row in enumerate(chunk):
            x = (pos % cols) * cell_w
            y = (pos // cols) * cell_h
            thumb_path = thumbs_dir.parent / row["thumbnail"]
            thumb = Image.open(thumb_path).convert("RGB")
            sheet.paste(thumb, (x + 30, y + 16))
            title = f"{row['image_index']}. {PurePosixPath(row['entry_name']).name}"
            labels = row["anchor_labels"] or "no filename anchors"
            draw.text((x + 24, y + 262), title[:52], fill="#1d2521")
            draw.text((x + 24, y + 282), labels[:58], fill="#617067")
        path = out / f"contact_sheet_{sheet_index:02d}.jpg"
        sheet.save(path, quality=90)
        sheet_paths.append(path.name)
    return sheet_paths


def write_report(path: Path, rows: list[dict[str, Any]], sheets: list[str]) -> None:
    bundle_counts = Counter(row["source_bundle"] for row in rows)
    label_counts = Counter()
    for row in rows:
        for label in str(row["anchor_labels"]).split("|"):
            if label:
                label_counts[label] += 1
    duplicates = sum(1 for row in rows if row["duplicate_of"])

    lines = [
        "# Selene Image Artifact Report",
        "",
        "This report indexes image artifacts from the external bundles and loose files. It creates thumbnails/contact sheets only; originals remain untouched.",
        "",
        "## Counts",
        "",
        f"- Images indexed: `{len(rows)}`",
        f"- Duplicate image hashes: `{duplicates}`",
        "",
        "## By Source",
        "",
    ]
    for source, count in bundle_counts.most_common():
        lines.append(f"- `{source}`: {count}")
    lines.extend(["", "## Filename Anchor Labels", ""])
    for label, count in label_counts.most_common():
        lines.append(f"- `{label}`: {count}")
    lines.extend(["", "## Contact Sheets", ""])
    for sheet in sheets:
        lines.append(f"- `analysis/selene_image_artifacts_20260527/{sheet}`")
    lines.extend(["", "## High-Relevance Image Filenames", ""])
    for row in rows:
        if row["anchor_labels"]:
            lines.extend(
                [
                    f"### {row['image_index']}. {row['entry_name']}",
                    "",
                    f"- Source: `{row['source_bundle']}`",
                    f"- Dimensions: `{row['width']}x{row['height']}`",
                    f"- Labels: `{row['anchor_labels']}`",
                    f"- Thumbnail: `{row['thumbnail']}`",
                    "",
                ]
            )
    lines.extend(
        [
            "## Reading",
            "",
            "The image set appears to contain visual evidence/proof artifacts, sky/myth mapping diagrams, mobile observation graphics, and loose image material. The filenames alone are enough to flag several as braid-relevant, but visual review is needed before interpretation.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    source = args.workspace / "might help"
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    thumbs_dir = out / "thumbnails"

    rows = collect_images(source, thumbs_dir)
    sheets = create_contact_sheets(rows, out, thumbs_dir)

    write_csv(out / "image_artifact_index.csv", rows)
    write_report(out / "selene_image_artifact_report.md", rows, sheets)
    write_json(
        out / "selene_image_summary.json",
        {
            "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
            "boundaries": ["thumbnail_derivatives_only", "no_training", "no_memory_injection", "no_source_modification"],
            "counts": {
                "images": len(rows),
                "contact_sheets": len(sheets),
                "duplicates": sum(1 for row in rows if row["duplicate_of"]),
            },
            "source_counts": Counter(row["source_bundle"] for row in rows),
            "anchor_counts": Counter(label for row in rows for label in str(row["anchor_labels"]).split("|") if label),
            "contact_sheets": sheets,
        },
    )


if __name__ == "__main__":
    main()
