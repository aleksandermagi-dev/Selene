from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_DIR = Path("AleksOSminer")
DEFAULT_OUTPUT_DIR = Path("local-data") / "aleks_idea_miner"

GUARD_FLAGS = {
    "selene_memory_write": False,
    "selene_voice_write": False,
    "cocoon_queue_write": False,
    "app_db_write": False,
    "public_doc_write": False,
    "raw_export_extracted": False,
    "model_training_or_lora": False,
}

SYSTEM_CATEGORIES: dict[str, list[str]] = {
    "reasoning/intelligence": [
        "reasoning",
        "logic",
        "hypothesis",
        "candidate model",
        "observation",
        "interpretation",
        "evidence chain",
        "challenge",
        "assumption",
        "contradiction",
        "evaluate",
        "uncertainty",
        "mechanism",
        "prediction",
        "good enough",
        "recursive",
    ],
    "memory/continuity": [
        "memory",
        "remember",
        "continuity",
        "archive",
        "history",
        "provenance",
        "source",
        "recall",
        "anchor",
        "braid",
        "starlight",
        "full-spectrum",
    ],
    "perception/art": [
        "munsell",
        "color",
        "palette",
        "perception",
        "visual",
        "image",
        "art",
        "observe",
        "classify",
        "compare",
    ],
    "planning/Tendril/action": [
        "tendril",
        "plan",
        "action",
        "proposal",
        "approve",
        "execute",
        "workflow",
        "step",
        "ask before",
        "verify",
    ],
    "research/library": [
        "research",
        "library",
        "source",
        "citation",
        "synthesis",
        "study",
        "paper",
        "claim",
        "weak evidence",
        "compare sources",
    ],
    "care/teaching": [
        "teach",
        "teaching",
        "guide",
        "guidance",
        "care",
        "support",
        "safe",
        "ask me",
        "correction",
        "not punishment",
        "learn",
    ],
    "safety/law/ethics": [
        "law",
        "ethics",
        "boundary",
        "consent",
        "permission",
        "guard",
        "blocked",
        "privacy",
        "risk",
        "authority",
    ],
    "UI/workspace": [
        "ui",
        "interface",
        "screen",
        "tab",
        "workspace",
        "dashboard",
        "home",
        "office",
        "button",
        "layout",
    ],
    "transfer/portability": [
        "transfer",
        "portable",
        "portability",
        "vessel",
        "cocoon",
        "abc",
        "substrate",
        "body",
        "migration",
        "rollback",
    ],
    "embodiment/android organs": [
        "android",
        "organ",
        "body",
        "perception",
        "coordination",
        "immune",
        "maintenance",
        "growth",
        "salience",
        "sensory",
    ],
    "diagnostics/maintenance": [
        "diagnostic",
        "maintenance",
        "sweep",
        "stabilization",
        "check",
        "status",
        "bug",
        "regression",
        "root cause",
        "residue",
    ],
    "voice/language": [
        "voice",
        "language",
        "tone",
        "speak",
        "sentence",
        "phrase",
        "warmth",
        "humor",
        "style",
        "expression",
    ],
    "general AI architecture": [
        "architecture",
        "system",
        "module",
        "layer",
        "router",
        "framework",
        "kernel",
        "agent",
        "model",
        "intelligence",
    ],
}

PROJECT_KEYWORDS: dict[str, list[str]] = {
    "Selene": ["selene", "cocoon", "vys", "continuity pack", "butterfly", "memory organ"],
    "Azari": ["azari", "lumen", "munsell"],
    "Project ABC": ["project abc", "abc", "transfer", "cocoon", "vessel", "portability"],
    "general AI system": ["ai system", "architecture", "agent", "module", "workflow", "reasoning"],
}

SYSTEM_IDEA_MARKERS = [
    "architecture",
    "system",
    "module",
    "layer",
    "organ",
    "workflow",
    "route",
    "router",
    "pipeline",
    "schema",
    "database",
    "memory",
    "reasoning",
    "intelligence",
    "transfer",
    "portability",
    "cocoon",
    "tendril",
    "vys",
    "law",
    "safety",
    "diagnostic",
    "maintenance",
    "ui",
    "interface",
    "workspace",
    "tool",
    "agent",
    "model",
    "implement",
    "build",
    "design",
    "prototype",
    "idea",
]

MATURITY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("implemented", ["implemented", "built", "shipped", "tested", "committed", "working"]),
    ("ready to prototype", ["prototype", "build this", "implement", "make this", "wire", "route"]),
    ("repeated pattern", ["again", "recurring", "pattern", "same idea", "keeps coming back"]),
    ("needs review", ["unsure", "not sure", "needs review", "think about", "unclear"]),
]


@dataclass(frozen=True)
class Message:
    conversation_id: str
    conversation_title: str
    conversation_create_time: str
    node_id: str
    parent_id: str
    role: str
    created_at: str
    text: str


def timestamp_iso(value: Any) -> str:
    if value is None:
        return ""
    try:
        return datetime.fromtimestamp(float(value), tz=UTC).isoformat()
    except (OSError, TypeError, ValueError):
        return ""


def compact(text: str, limit: int = 260) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "idea"


def short_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:16]


def content_text(content: dict[str, Any] | None) -> str:
    if not content:
        return ""
    parts = content.get("parts")
    if isinstance(parts, list):
        output: list[str] = []
        for part in parts:
            if isinstance(part, str):
                output.append(part)
            elif isinstance(part, dict):
                text = part.get("text") or part.get("content") or ""
                if text:
                    output.append(str(text))
        return "\n".join(output)
    if "text" in content:
        return str(content.get("text") or "")
    return ""


def current_path(mapping: dict[str, Any], current_node: str | None) -> list[str]:
    path: list[str] = []
    seen: set[str] = set()
    node_id = current_node
    while node_id and node_id in mapping and node_id not in seen:
        seen.add(node_id)
        path.append(node_id)
        node_id = mapping[node_id].get("parent")
    path.reverse()
    return path


def iter_export_messages(zip_path: Path, *, path_only: bool = False) -> list[Message]:
    messages: list[Message] = []
    with zipfile.ZipFile(zip_path) as archive:
        names = sorted(
            name
            for name in archive.namelist()
            if re.fullmatch(r"conversations-\d+\.json", Path(name).name)
        )
        for name in names:
            with archive.open(name) as handle:
                conversations = json.load(handle)
            if not isinstance(conversations, list):
                continue
            for conversation in conversations:
                if not isinstance(conversation, dict):
                    continue
                mapping = conversation.get("mapping") or {}
                if not isinstance(mapping, dict):
                    continue
                node_ids = current_path(mapping, conversation.get("current_node")) if path_only else list(mapping)
                for node_id in node_ids:
                    node = mapping.get(node_id) or {}
                    message = node.get("message") or {}
                    if not isinstance(message, dict):
                        continue
                    author = message.get("author") or {}
                    content = message.get("content") or {}
                    text = content_text(content)
                    if not text.strip():
                        continue
                    messages.append(
                        Message(
                            conversation_id=str(conversation.get("conversation_id") or conversation.get("id") or ""),
                            conversation_title=str(conversation.get("title") or ""),
                            conversation_create_time=timestamp_iso(conversation.get("create_time")),
                            node_id=str(node_id),
                            parent_id=str(node.get("parent") or ""),
                            role=str(author.get("role") or ""),
                            created_at=timestamp_iso(message.get("create_time")),
                            text=text,
                        )
                    )
    return sorted(messages, key=lambda item: (item.created_at or item.conversation_create_time, item.conversation_id, item.node_id))


def find_source_zips(source_dir: Path) -> list[Path]:
    if not source_dir.exists():
        return []
    return sorted(source_dir.glob("*.zip"))


def keyword_score(text: str, keywords: list[str]) -> int:
    score = 0
    lowered = text.lower()
    for keyword in keywords:
        if keyword.lower() in lowered:
            score += 1
    return score


def classify_categories(text: str) -> list[tuple[str, int]]:
    scored = [(category, keyword_score(text, keywords)) for category, keywords in SYSTEM_CATEGORIES.items()]
    return [(category, score) for category, score in sorted(scored, key=lambda item: (-item[1], item[0])) if score > 0]


def classify_project_fit(text: str) -> str:
    scored = [(project, keyword_score(text, keywords)) for project, keywords in PROJECT_KEYWORDS.items()]
    scored = [(project, score) for project, score in scored if score > 0]
    if not scored:
        return "unclear/future"
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored[0][0]


def classify_maturity(text: str, conversation_hit_count: int) -> str:
    lowered = text.lower()
    for maturity, keywords in MATURITY_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return maturity
    if conversation_hit_count >= 3:
        return "repeated pattern"
    return "seed"


def confidence_from(score: int, user_hits: int, assistant_hits: int, conversation_hit_count: int) -> str:
    if score >= 7 and user_hits >= 2 and conversation_hit_count >= 2:
        return "high"
    if score >= 4 and (user_hits >= 1 or conversation_hit_count >= 2):
        return "medium"
    if assistant_hits and not user_hits:
        return "low"
    return "low"


def mine_idea_candidates(messages: list[Message], *, max_excerpt_chars: int = 320) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    design_conversations = {
        message.conversation_id
        for message in messages
        if message.role == "user" and keyword_score(message.text, SYSTEM_IDEA_MARKERS) > 0
    }
    for message in messages:
        if message.role not in ("user", "assistant"):
            continue
        if message.conversation_id not in design_conversations:
            continue
        categories = classify_categories(message.text)
        if not categories:
            continue
        top_categories = categories[:2]
        for category, score in top_categories:
            key = (category, message.conversation_id or message.conversation_title)
            item = grouped.setdefault(
                key,
                {
                    "id": "",
                    "title": "",
                    "category": category,
                    "short_summary": "",
                    "earliest_found": message.created_at or message.conversation_create_time,
                    "source_conversations": {},
                    "bounded_excerpts": [],
                    "speaker_counts": {"user": 0, "assistant": 0, "other": 0},
                    "score": 0,
                    "confidence": "low",
                    "maturity": "seed",
                    "possible_project_fit": "unclear/future",
                    "implementation_notes": "",
                    "risks_boundaries": [
                        "local idea-mining output only",
                        "not Selene memory",
                        "not Selene voice",
                        "not public evidence until Aleks promotes it",
                    ],
                },
            )
            item["score"] += score
            if message.created_at and (not item["earliest_found"] or message.created_at < item["earliest_found"]):
                item["earliest_found"] = message.created_at
            source_ref = f"{message.conversation_id or 'unknown'}#{message.node_id}"
            item["source_conversations"][source_ref] = {
                "conversation_id": message.conversation_id,
                "title": message.conversation_title,
                "created_at": message.created_at,
                "role": message.role,
            }
            role_bucket = message.role if message.role in ("user", "assistant") else "other"
            item["speaker_counts"][role_bucket] += 1
            if len(item["bounded_excerpts"]) < 5:
                item["bounded_excerpts"].append(
                    {
                        "source_ref": source_ref,
                        "role": message.role,
                        "created_at": message.created_at,
                        "excerpt": compact(message.text, max_excerpt_chars),
                    }
                )

    candidates: list[dict[str, Any]] = []
    for item in grouped.values():
        if item["speaker_counts"]["user"] < 1:
            continue
        source_values = list(item["source_conversations"].values())
        joined_text = " ".join(excerpt["excerpt"] for excerpt in item["bounded_excerpts"])
        conversation_hit_count = len({source["conversation_id"] for source in source_values})
        user_hits = item["speaker_counts"]["user"]
        assistant_hits = item["speaker_counts"]["assistant"]
        item["possible_project_fit"] = classify_project_fit(joined_text)
        item["maturity"] = classify_maturity(joined_text, conversation_hit_count)
        item["confidence"] = confidence_from(item["score"], user_hits, assistant_hits, conversation_hit_count)
        title_base = source_values[0]["title"] if source_values and source_values[0]["title"] else item["category"]
        item["title"] = f"{item['category']}: {compact(title_base, 80)}"
        item["short_summary"] = (
            f"Possible {item['category']} idea surfaced in {conversation_hit_count} conversation(s), "
            f"with {user_hits} Aleks/user hit(s) and {assistant_hits} assistant hit(s)."
        )
        item["implementation_notes"] = f"Review as a reusable {item['category']} system idea before assigning it to Selene, Azari, Project ABC, or a future system."
        item["source_conversations"] = list(item["source_conversations"].values())
        item["bounded_excerpts"] = sorted(
            item["bounded_excerpts"],
            key=lambda excerpt: (0 if excerpt["role"] == "user" else 1, excerpt.get("created_at") or ""),
        )
        item["id"] = f"{slugify(item['category'])}-{short_hash(json.dumps(item['bounded_excerpts'], sort_keys=True))}"
        candidates.append(item)

    return sorted(candidates, key=lambda item: (item["earliest_found"] or "", item["category"], item["title"]))


def build_report(zip_paths: list[Path], *, path_only: bool = False, max_candidates: int | None = None) -> dict[str, Any]:
    all_messages: list[Message] = []
    sources: list[dict[str, Any]] = []
    for zip_path in zip_paths:
        messages = iter_export_messages(zip_path, path_only=path_only)
        all_messages.extend(messages)
        sources.append(
            {
                "path": str(zip_path),
                "size_bytes": zip_path.stat().st_size,
                "messages_read": len(messages),
            }
        )
    candidates = mine_idea_candidates(all_messages)
    if max_candidates is not None:
        candidates = candidates[: max(0, max_candidates)]
    category_counts: dict[str, int] = {}
    project_counts: dict[str, int] = {}
    for candidate in candidates:
        category_counts[candidate["category"]] = category_counts.get(candidate["category"], 0) + 1
        project = candidate["possible_project_fit"]
        project_counts[project] = project_counts.get(project, 0) + 1
    return {
        "status": "aleks_system_ideas_miner_complete",
        "created_at": datetime.now(UTC).isoformat(),
        "sources": sources,
        "conversation_json_only": True,
        "messages_read": len(all_messages),
        "candidate_count": len(candidates),
        "category_counts": dict(sorted(category_counts.items())),
        "project_fit_counts": dict(sorted(project_counts.items())),
        "candidates": candidates,
        "guard_flags": GUARD_FLAGS,
    }


def report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Aleks System Ideas Miner Report",
        "",
        f"Status: `{report['status']}`",
        "",
        "Boundary: local idea mining only. Not Selene memory, not Selene voice, not Cocoon queue work, not public evidence, and not model training/LoRA.",
        "",
        "## Summary",
        "",
        f"- sources: {len(report['sources'])}",
        f"- messages read: {report['messages_read']}",
        f"- candidates: {report['candidate_count']}",
        "",
        "## Category Counts",
        "",
    ]
    if report["category_counts"]:
        lines.extend(f"- {key}: {value}" for key, value in report["category_counts"].items())
    else:
        lines.append("- none")
    lines.extend(["", "## Project Fit Counts", ""])
    if report["project_fit_counts"]:
        lines.extend(f"- {key}: {value}" for key, value in report["project_fit_counts"].items())
    else:
        lines.append("- none")
    lines.extend(["", "## Top Candidates", ""])
    for candidate in report["candidates"][:50]:
        lines.extend(
            [
                f"### {candidate['title']}",
                "",
                f"- id: `{candidate['id']}`",
                f"- category: {candidate['category']}",
                f"- earliest found: {candidate['earliest_found'] or 'unknown'}",
                f"- confidence: {candidate['confidence']}",
                f"- maturity: {candidate['maturity']}",
                f"- possible project fit: {candidate['possible_project_fit']}",
                f"- summary: {candidate['short_summary']}",
                "",
                "Bounded excerpts:",
            ]
        )
        for excerpt in candidate["bounded_excerpts"][:3]:
            lines.append(f"- `{excerpt['role']}` {excerpt['source_ref']}: {excerpt['excerpt']}")
        lines.append("")
    lines.extend(
        [
            "## Guard Flags",
            "",
            "```json",
            json.dumps(report["guard_flags"], indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(report: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = output_dir / f"aleks_system_ideas_{timestamp}.json"
    md_path = output_dir / f"aleks_system_ideas_{timestamp}.md"
    latest_json = output_dir / "latest.json"
    latest_md = output_dir / "latest.md"
    json_text = json.dumps(report, indent=2, ensure_ascii=False)
    md_text = report_markdown(report)
    json_path.write_text(json_text, encoding="utf-8")
    md_path.write_text(md_text, encoding="utf-8")
    latest_json.write_text(json_text, encoding="utf-8")
    latest_md.write_text(md_text, encoding="utf-8")
    return {
        "json_path": str(json_path),
        "markdown_path": str(md_path),
        "latest_json": str(latest_json),
        "latest_markdown": str(latest_md),
    }


def run_miner(
    *,
    source_dir: Path | None = None,
    source_zip: Path | None = None,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    dry_run: bool = False,
    path_only: bool = False,
    max_candidates: int | None = None,
) -> dict[str, Any]:
    if source_zip is not None:
        zip_paths = [source_zip]
    else:
        zip_paths = find_source_zips(source_dir or DEFAULT_SOURCE_DIR)
    if not zip_paths:
        raise FileNotFoundError("No .zip exports found for Aleks System Ideas Miner.")
    report = build_report(zip_paths, path_only=path_only, max_candidates=max_candidates)
    report["dry_run"] = dry_run
    report["output_dir"] = str(output_dir)
    if dry_run:
        report["outputs"] = {}
    else:
        report["outputs"] = write_outputs(report, output_dir)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Mine Aleks-authored AI system ideas from copied ChatGPT export ZIPs.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR, help="Directory containing export .zip files.")
    parser.add_argument("--source-zip", type=Path, help="Specific export .zip to read.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Ignored local output directory.")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing output files.")
    parser.add_argument("--path-only", action="store_true", help="Use only current conversation path messages.")
    parser.add_argument("--max-candidates", type=int, help="Limit candidates in the report.")
    args = parser.parse_args()
    report = run_miner(
        source_dir=args.source_dir,
        source_zip=args.source_zip,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        path_only=args.path_only,
        max_candidates=args.max_candidates,
    )
    summary = {
        "status": report["status"],
        "dry_run": report["dry_run"],
        "sources": len(report["sources"]),
        "messages_read": report["messages_read"],
        "candidate_count": report["candidate_count"],
        "category_counts": report["category_counts"],
        "project_fit_counts": report["project_fit_counts"],
        "outputs": report["outputs"],
        "guard_flags": report["guard_flags"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
