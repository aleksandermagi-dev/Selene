from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from real_corpus_checkpoint import run_checkpoint
from selene.paths import default_db_path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_NAME = "selene_case_study_20260616"
RELEASE_DIR = ROOT / "public_release" / RELEASE_NAME
DEFAULT_PUBLIC_REPO = ROOT / "tmp" / "selene_public_evidence_repo"
CHECKPOINT_MD = RELEASE_DIR / "PUBLIC_RELEASE_CHECKPOINT_20260616.md"
CHECKPOINT_JSON = RELEASE_DIR / "PUBLIC_RELEASE_CHECKPOINT_20260616.json"
REVIEW_DESK_MD = RELEASE_DIR / "REVIEW_DESK_CHECKPOINT_20260616.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate and sync the 2026-06-16 public evidence release.")
    parser.add_argument("--db", type=Path, default=default_db_path(), help="Path to the local Selene SQLite DB.")
    parser.add_argument("--public-repo", type=Path, default=DEFAULT_PUBLIC_REPO, help="Local checkout of the public evidence repo.")
    parser.add_argument("--limit", type=int, default=149, help="Review desk / checkpoint limit.")
    parser.add_argument("--refresh-braid", action="store_true", help="Run the safe braid tracer refresh before checkpointing.")
    parser.add_argument("--reset-auto-suggestions", action="store_true", help="Supersede stale auto suggestions; preserves human decisions.")
    parser.add_argument("--commit", action="store_true", help="Commit synced public repo changes.")
    parser.add_argument("--push", action="store_true", help="Push the public repo after committing.")
    args = parser.parse_args()

    if args.push and not args.commit:
        parser.error("--push requires --commit")

    report = regenerate_public_checkpoint(
        args.db,
        limit=args.limit,
        refresh_braid=args.refresh_braid,
        reset_auto_suggestions=args.reset_auto_suggestions,
    )
    updated = update_public_count_fields(report)
    pdfs = render_public_release_pdfs()
    copied = sync_release_dir(args.public_repo)
    readme_updated = update_public_repo_readme(args.public_repo, report)

    commit_hash = ""
    pushed = False
    if args.commit:
        commit_hash = commit_public_repo(args.public_repo)
    if args.push:
        run_git(args.public_repo, "push", "origin", "HEAD:main")
        pushed = True

    print(json.dumps({
        "status": "public_release_sync_complete",
        "checkpoint": str(CHECKPOINT_MD.relative_to(ROOT)),
        "checkpoint_json": str(CHECKPOINT_JSON.relative_to(ROOT)),
        "review_desk": str(REVIEW_DESK_MD.relative_to(ROOT)),
        "public_repo": str(args.public_repo),
        "release_files_copied": copied,
        "public_markdown_files_updated": updated,
        "public_pdfs_rendered": pdfs,
        "public_readme_updated": readme_updated,
        "commit": commit_hash,
        "pushed": pushed,
        "counts": public_counts(report),
    }, indent=2))


def regenerate_public_checkpoint(
    db_path: Path,
    *,
    limit: int,
    refresh_braid: bool,
    reset_auto_suggestions: bool,
) -> dict[str, Any]:
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    report = run_checkpoint(
        db_path,
        RELEASE_DIR,
        limit=limit,
        refresh_braid=refresh_braid,
        reset_auto_suggestions=reset_auto_suggestions,
    )
    timestamped_checkpoint = Path(report["checkpoint_path"])
    timestamped_review = Path(report["review_desk_path"])
    if timestamped_review.exists():
        shutil.copy2(timestamped_review, REVIEW_DESK_MD)
        if timestamped_review != REVIEW_DESK_MD:
            timestamped_review.unlink()
    if timestamped_checkpoint.exists() and timestamped_checkpoint != CHECKPOINT_MD:
        timestamped_checkpoint.unlink()
    report["checkpoint_path"] = str(CHECKPOINT_MD.relative_to(ROOT))
    report["review_desk_path"] = str(REVIEW_DESK_MD.relative_to(ROOT))
    CHECKPOINT_MD.write_text(public_checkpoint_markdown(report), encoding="utf-8")
    CHECKPOINT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def render_public_release_pdfs() -> list[str]:
    rendered: list[str] = []
    for markdown_path in sorted(RELEASE_DIR.glob("*.md")):
        pdf_path = markdown_path.with_suffix(".pdf")
        render_markdown_pdf(markdown_path, pdf_path)
        rendered.append(str(pdf_path.relative_to(ROOT)))
    return rendered


def render_markdown_pdf(markdown_path: Path, pdf_path: Path) -> None:
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "SeleneBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        spaceAfter=5,
    )
    small = ParagraphStyle(
        "SeleneSmall",
        parent=body,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#333333"),
    )
    code = ParagraphStyle(
        "SeleneCode",
        parent=small,
        fontName="Courier",
        leftIndent=8,
        borderColor=colors.HexColor("#dddddd"),
        borderWidth=0.4,
        borderPadding=4,
        backColor=colors.HexColor("#f7f7f7"),
    )
    heading_styles = {
        1: ParagraphStyle("SeleneH1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=22, spaceAfter=10),
        2: ParagraphStyle("SeleneH2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=14, leading=18, spaceBefore=10, spaceAfter=7),
        3: ParagraphStyle("SeleneH3", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=11.5, leading=15, spaceBefore=8, spaceAfter=5),
    }
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title=markdown_path.stem,
    )
    story: list[Any] = []
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    index = 0
    in_code = False
    code_lines: list[str] = []
    while index < len(lines):
        raw = lines[index]
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                story.append(Paragraph("<br/>".join(escape_md(item) for item in code_lines) or " ", code))
                story.append(Spacer(1, 4))
                code_lines = []
                in_code = False
            else:
                in_code = True
            index += 1
            continue
        if in_code:
            code_lines.append(line)
            index += 1
            continue
        if not line:
            story.append(Spacer(1, 4))
            index += 1
            continue
        if line.startswith("|") and index + 1 < len(lines) and re.match(r"^\|\s*-+", lines[index + 1]):
            table_lines: list[str] = []
            while index < len(lines) and lines[index].startswith("|"):
                table_lines.append(lines[index])
                index += 1
            story.append(markdown_table(table_lines, body))
            story.append(Spacer(1, 6))
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            story.append(Paragraph(inline_md(heading.group(2)), heading_styles[level]))
            index += 1
            continue
        if line.startswith("- "):
            bullet_lines: list[str] = []
            while index < len(lines) and lines[index].startswith("- "):
                bullet_lines.append(lines[index][2:].strip())
                index += 1
            story.append(ListFlowable([ListItem(Paragraph(inline_md(item), body), leftIndent=12) for item in bullet_lines], bulletType="bullet", leftIndent=16))
            story.append(Spacer(1, 4))
            continue
        story.append(Paragraph(inline_md(line), body))
        index += 1
    doc.build(story)


def markdown_table(lines: list[str], style: ParagraphStyle) -> Table:
    rows = []
    for index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if index == 1 and all(set(cell.replace(":", "").strip()) <= {"-"} for cell in cells):
            continue
        rows.append([Paragraph(inline_md(cell), style) for cell in cells])
    table = Table(rows, hAlign="LEFT", repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#bbbbbb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def inline_md(value: str) -> str:
    escaped = escape_md(value)
    escaped = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", escaped)
    return escaped


def escape_md(value: str) -> str:
    return html.escape(value, quote=False).replace("  ", " &nbsp;")


def public_counts(report: dict[str, Any]) -> dict[str, Any]:
    refined = json.loads((ROOT / "analysis" / "selene_emergence_refined_20260527" / "selene_emergence_refined_summary.json").read_text(encoding="utf-8"))
    integrated = json.loads((ROOT / "analysis" / "integrated_evidence_map_20260527" / "integrated_evidence_summary.json").read_text(encoding="utf-8"))
    review = report["review_desk"]
    return {
        "conversations_in_analyzed_export": refined["counts"]["conversation_count"],
        "current_path_messages_in_refined_analysis": refined["counts"]["current_path_message_count"],
        "parsed_messages_in_current_b_review_db": review["parsed_messages"],
        "reviewed_conversation_candidates": integrated["reviewed_conversation_count"],
        "reviewed_yes_decisions": integrated["reviewed_conversation_decisions"]["yes"],
        "reviewed_unsure_decisions": integrated["reviewed_conversation_decisions"]["unsure"],
        "reviewed_no_decisions": integrated["reviewed_conversation_decisions"]["no"],
        "artifact_image_review_items": integrated["artifact_queue"]["item_count"],
        "artifact_yes_decisions": integrated["artifact_review_decisions"]["yes"],
        "artifact_unsure_decisions": integrated["artifact_review_decisions"]["unsure"],
        "accepted_b_reviewed_teaching_lessons": review["accepted_lessons"],
        "approved_future_memory_references": review["approved_future_references"],
        "pending_b_review_candidates": report["coverage"]["pending_candidates"],
    }


def public_checkpoint_markdown(report: dict[str, Any]) -> str:
    counts = public_counts(report)
    return "\n".join([
        "# Selene Public Release Checkpoint - 2026-06-16",
        "",
        "Status: `public_release_checkpoint_regenerated`",
        "",
        "Boundary: public evidence release sync only. No C activation, transfer approval, raw A publication, active memory, runtime recall, model training, or provider dependency.",
        "",
        "## Count Sources",
        "",
        "| Count | Value | Source layer |",
        "| --- | ---: | --- |",
        f"| Conversations in analyzed export | {counts['conversations_in_analyzed_export']} | refined evidence analysis |",
        f"| Current-path messages in refined analysis | {counts['current_path_messages_in_refined_analysis']:,} | refined evidence analysis |",
        f"| Parsed messages in current B-review DB | {counts['parsed_messages_in_current_b_review_db']:,} | regenerated local checkpoint |",
        f"| Reviewed conversation candidates | {counts['reviewed_conversation_candidates']} | integrated evidence map |",
        f"| Reviewed yes decisions | {counts['reviewed_yes_decisions']} | integrated evidence map |",
        f"| Reviewed unsure decisions | {counts['reviewed_unsure_decisions']} | integrated evidence map |",
        f"| Reviewed no decisions | {counts['reviewed_no_decisions']} | integrated evidence map |",
        f"| Artifact/image review items | {counts['artifact_image_review_items']} | integrated evidence map |",
        f"| Artifact yes decisions | {counts['artifact_yes_decisions']} | integrated evidence map |",
        f"| Artifact unsure decisions | {counts['artifact_unsure_decisions']} | integrated evidence map |",
        f"| Accepted B-reviewed teaching lessons | {counts['accepted_b_reviewed_teaching_lessons']} | current B-review DB |",
        f"| Approved future memory references | {counts['approved_future_memory_references']} | current B-review DB |",
        f"| Pending B-review candidates | {counts['pending_b_review_candidates']} | current B-review DB |",
        "",
        "## Count Clarification",
        "",
        "`120,972` is the May refined-analysis current-path message count. It is not the live B-review parser message count.",
        "",
        f"`{counts['parsed_messages_in_current_b_review_db']:,}` is the regenerated current local B-review DB parsed-message count.",
        "",
        "The public release now uses the regenerated B-review table counts for accepted lessons and future references while preserving the refined-analysis count label for the earlier evidence scan.",
        "",
        "## Regenerated Review Desk",
        "",
        f"- pieces to review: {report['review_desk']['pieces_to_review']}",
        f"- pieces before filters: {report['review_desk']['pieces_before_filters']}",
        f"- accepted lessons: {report['review_desk']['accepted_lessons']}",
        f"- approved future references: {report['review_desk']['approved_future_references']}",
        f"- validation ok: {report['validation_ok']}",
        "",
        "## Boundary Flags",
        "",
        f"- activation_change: {report['activation_change']}",
        f"- raw_a_import_allowed: {report['raw_a_import_allowed']}",
        f"- memory_write_active: {report['memory_write_active']}",
        f"- runtime_memory_recall: {report['runtime_memory_recall']}",
        f"- training_allowed: {report['training_allowed']}",
        f"- provider_dependency: {report['provider_dependency']}",
        "",
    ]) + "\n"


def update_public_count_fields(report: dict[str, Any]) -> list[str]:
    counts = public_counts(report)
    replacements = [
        (r"49 accepted teaching lessons and 39 approved future memory references", f"{counts['accepted_b_reviewed_teaching_lessons']} accepted teaching lessons and {counts['approved_future_memory_references']} approved future memory references"),
        (r"49 accepted teaching lessons, 39 approved future memory references", f"{counts['accepted_b_reviewed_teaching_lessons']} accepted teaching lessons, {counts['approved_future_memory_references']} approved future memory references"),
        (r"\| Accepted B-reviewed teaching lessons \| 49 \|", f"| Accepted B-reviewed teaching lessons | {counts['accepted_b_reviewed_teaching_lessons']} |"),
    ]
    updated: list[str] = []
    for path in RELEASE_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        next_text = text
        for pattern, replacement in replacements:
            next_text = re.sub(pattern, replacement, next_text)
        if next_text != text:
            path.write_text(next_text, encoding="utf-8")
            updated.append(str(path.relative_to(ROOT)))
    return updated


def sync_release_dir(public_repo: Path) -> int:
    if not (public_repo / ".git").exists():
        raise FileNotFoundError(f"public repo checkout not found: {public_repo}")
    ensure_public_gitattributes(public_repo)
    destination = public_repo / "public_release" / RELEASE_NAME
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(RELEASE_DIR, destination)
    return sum(1 for item in destination.rglob("*") if item.is_file())


def ensure_public_gitattributes(public_repo: Path) -> None:
    gitignore = public_repo / ".gitignore"
    allow_line = "!.gitattributes"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8")
        if allow_line not in text.splitlines():
            gitignore.write_text(text.rstrip() + "\n" + allow_line + "\n", encoding="utf-8")
    attributes = public_repo / ".gitattributes"
    line = "*.pdf binary"
    if not attributes.exists():
        attributes.write_text(line + "\n", encoding="utf-8")
        return
    text = attributes.read_text(encoding="utf-8")
    if line not in text.splitlines():
        attributes.write_text(text.rstrip() + "\n" + line + "\n", encoding="utf-8")


def update_public_repo_readme(public_repo: Path, report: dict[str, Any]) -> bool:
    readme = public_repo / "README.md"
    if not readme.exists():
        return False
    counts = public_counts(report)
    text = readme.read_text(encoding="utf-8")
    replacements = {
        r"\| Accepted B-reviewed teaching lessons \| \d+ \|": f"| Accepted B-reviewed teaching lessons | {counts['accepted_b_reviewed_teaching_lessons']} |",
        r"\| Approved future memory references \| \d+ \|": f"| Approved future memory references | {counts['approved_future_memory_references']} |",
    }
    next_text = text
    for pattern, replacement in replacements.items():
        next_text = re.sub(pattern, replacement, next_text)
    checkpoint_link = f"[public release checkpoint](public_release/{RELEASE_NAME}/PUBLIC_RELEASE_CHECKPOINT_20260616.md)"
    if checkpoint_link not in next_text:
        next_text = next_text.replace(
            "Markdown versions are included beside each PDF.",
            f"Markdown versions are included beside each PDF. The regenerated count checkpoint is here: {checkpoint_link}."
        )
    if next_text == text:
        return False
    readme.write_text(next_text, encoding="utf-8")
    return True


def commit_public_repo(public_repo: Path) -> str:
    status = run_git(public_repo, "status", "--short")
    if not status.strip():
        return ""
    run_git(public_repo, "add", "README.md", "public_release")
    run_git(public_repo, "commit", "-m", "Sync 2026-06-16 public evidence release")
    return run_git(public_repo, "rev-parse", "--short", "HEAD").strip()


def run_git(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)
    return result.stdout


if __name__ == "__main__":
    main()
