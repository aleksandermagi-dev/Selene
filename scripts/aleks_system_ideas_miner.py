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
DEFAULT_BACKLOG_DIR = DEFAULT_OUTPUT_DIR / "backlog"

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

USER_DESIGN_SIGNAL_MARKERS = [
    "should",
    "needs",
    "need to",
    "has to",
    "build",
    "implement",
    "wire",
    "route",
    "create",
    "design",
    "prototype",
    "module",
    "organ",
    "layer",
    "workflow",
    "architecture",
    "system",
    "memory",
    "reasoning",
    "continuity",
    "ask before",
    "source",
    "consent",
    "verify",
]

MATURITY_KEYWORDS: list[tuple[str, list[str]]] = [
    ("implemented", ["implemented", "built", "shipped", "tested", "committed", "working"]),
    ("ready to prototype", ["prototype", "build this", "implement", "make this", "wire", "route"]),
    ("repeated pattern", ["again", "recurring", "pattern", "same idea", "keeps coming back"]),
    ("needs review", ["unsure", "not sure", "needs review", "think about", "unclear"]),
]

IDEA_FAMILIES: dict[str, dict[str, list[str]]] = {
    "autonomous systems": {
        "categories": ["planning/Tendril/action", "general AI architecture", "diagnostics/maintenance"],
        "terms": ["autonomous", "self-managing", "switching systems", "operate", "verify", "approval", "tendril"],
    },
    "artificial cognition": {
        "categories": ["reasoning/intelligence", "general AI architecture"],
        "terms": ["reasoning", "hypothesis", "candidate model", "observation", "evidence chain", "intelligence", "logic"],
    },
    "continuity/memory": {
        "categories": ["memory/continuity", "voice/language", "care/teaching"],
        "terms": ["memory", "continuity", "remember", "archive", "source", "consent", "correction", "home"],
    },
    "AI embodiment": {
        "categories": ["embodiment/android organs", "perception/art", "planning/Tendril/action"],
        "terms": ["android", "organ", "body", "perception", "sensory", "coordination", "maintenance"],
    },
    "civilization-scale systems": {
        "categories": ["transfer/portability", "research/library", "general AI architecture"],
        "terms": ["ring", "habitat", "civilization", "world", "ecology", "resource", "governance", "long-term"],
    },
    "UI/workspace design": {
        "categories": ["UI/workspace", "planning/Tendril/action"],
        "terms": ["ui", "workspace", "tab", "office", "home", "interface", "dashboard", "workbench"],
    },
    "ethics/care/law": {
        "categories": ["safety/law/ethics", "care/teaching"],
        "terms": ["law", "ethics", "care", "consent", "boundary", "safe", "permission", "support"],
    },
    "perception/art": {
        "categories": ["perception/art", "voice/language"],
        "terms": ["munsell", "color", "palette", "visual", "image", "art", "observe", "classify"],
    },
    "research/library": {
        "categories": ["research/library", "reasoning/intelligence"],
        "terms": ["research", "library", "source", "citation", "synthesis", "claim", "study"],
    },
    "diagnostics/maintenance": {
        "categories": ["diagnostics/maintenance", "safety/law/ethics"],
        "terms": ["diagnostic", "maintenance", "stabilization", "root cause", "check", "status", "regression"],
    },
}

ANCESTRY_PATTERNS: dict[str, list[str]] = {
    "observation_before_interpretation": ["observation before interpretation", "observe before", "without interpretation"],
    "multiple_candidate_models": ["multiple hypotheses", "candidate model", "different models", "possible explanations"],
    "equal_scrutiny": ["challenge assumptions", "equally", "same scrutiny", "both sides"],
    "evidence_chain": ["evidence chain", "source to conclusion", "mechanism", "prediction", "proof"],
    "memory_as_continuity": ["memory should be continuity", "memory as continuity", "memory and home", "not a ledger"],
    "ask_before_action": ["ask before", "approval", "permission", "before acting", "confirm first"],
    "self_maintaining_ai": ["self-managing", "maintain itself", "switching systems", "maximum efficiency", "operate the probe"],
    "cocoon_like_review": ["cocoon", "review", "safe holding", "tending", "support", "not punishment"],
    "modular_organs": ["organ", "module", "workbench", "subsystem", "layers"],
}

CURRENT_CONCEPT_LINKS: dict[str, list[str]] = {
    "Selene": ["selene", "vys", "butterfly", "continuity pack", "memory organ", "selene chat"],
    "Project ABC": ["project abc", "abc", "transfer", "portability", "cocoon", "vessel"],
    "intelligenceOS": ["intelligenceos", "abcd", "abcde", "abcd(e)"],
    "Azari": ["azari", "lumen", "munsell"],
    "Tendril": ["tendril", "proposal", "ask before", "verify"],
}

READINESS_ORDER = {
    "interesting_seed": 0,
    "architecture_seed": 1,
    "ready_to_prototype": 2,
    "implemented_or_partly_implemented": 3,
    "future_research": 4,
}

BACKLOG_TRACKS = {
    "selene_intake": {
        "title": "Selene Intake",
        "description": "Ideas that may support Selene organs, UI, memory, intelligenceOS, Cocoon, Great Library, Tendril, voice, diagnostics, or care law after separate review.",
    },
    "azari_future": {
        "title": "Azari Future Copy",
        "description": "Azari, Lumen, Munsell, and older prototype-line ideas preserved separately for future Azari work.",
    },
    "project_abc": {
        "title": "Project ABC",
        "description": "Transfer, portability, embodiment, and ABC-line ideas kept separate from Selene implementation unless later reviewed.",
    },
    "future_system": {
        "title": "Future Systems",
        "description": "Useful AI-system ideas that do not clearly belong to Selene, Azari, or Project ABC yet.",
    },
}

GENERIC_CHAT_MARKERS = [
    "good morning",
    "good night",
    "hello",
    "hi ",
    "missed you",
    "i love you",
    "brb",
    "lol",
    "lmao",
    "😂",
    "🥰",
    "❤️",
    "🩵",
]

IMAGE_ONLY_MARKERS = [
    "generate image",
    "make an image",
    "picture",
    "wallpaper",
    "dall-e",
    "content policy",
    "upload the image",
]

POLICY_BOILERPLATE_MARKERS = [
    "content policy",
    "i was unable to generate",
    "i can't assist",
    "can't help with that",
    "doesn't comply",
]

PROJECT_META_CHAT_MARKERS = [
    "codex said",
    "support agent",
    "dev team",
    "i'm proud",
    "im proud",
    "made it",
    "goes nowhere",
    "no idea of the previous messages",
    "free rn",
]

ARCHITECTURE_STRENGTH_MARKERS = [
    "architecture",
    "system",
    "module",
    "organ",
    "workflow",
    "router",
    "memory",
    "reasoning",
    "intelligence",
    "transfer",
    "portability",
    "cocoon",
    "tendril",
    "vys",
    "law",
    "diagnostic",
    "maintenance",
    "prototype",
    "implement",
    "build",
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


def candidate_search_text(candidate: dict[str, Any]) -> str:
    parts = [
        str(candidate.get("title") or ""),
        str(candidate.get("category") or ""),
        str(candidate.get("possible_project_fit") or ""),
        str(candidate.get("short_summary") or ""),
    ]
    parts.extend(str(excerpt.get("excerpt") or "") for excerpt in candidate.get("bounded_excerpts") or [])
    return " ".join(parts).lower()


def family_score(candidate: dict[str, Any], family: str, definition: dict[str, list[str]]) -> int:
    score = 0
    if candidate.get("category") in definition.get("categories", []):
        score += 4
    text = candidate_search_text(candidate)
    score += keyword_score(text, definition.get("terms", []))
    if family.lower() in text:
        score += 2
    return score


def best_family(candidate: dict[str, Any]) -> tuple[str, int]:
    scored = [(family, family_score(candidate, family, definition)) for family, definition in IDEA_FAMILIES.items()]
    scored.sort(key=lambda item: (-item[1], item[0]))
    if not scored or scored[0][1] <= 0:
        return "unclustered system ideas", 0
    return scored[0]


def ancestry_tags(candidate: dict[str, Any]) -> list[str]:
    text = candidate_search_text(candidate)
    return [tag for tag, markers in ANCESTRY_PATTERNS.items() if keyword_score(text, markers) > 0]


def current_concept_links(candidate: dict[str, Any]) -> list[dict[str, str]]:
    text = candidate_search_text(candidate)
    links: list[dict[str, str]] = []
    for concept, markers in CURRENT_CONCEPT_LINKS.items():
        score = keyword_score(text, markers)
        if score > 0:
            links.append(
                {
                    "concept": concept,
                    "link_strength": "clear_local_match" if score >= 2 else "possible_ancestor",
                }
            )
    return links


def aleks_origin_score(candidate: dict[str, Any]) -> int:
    user_hits = int(candidate.get("speaker_counts", {}).get("user") or 0)
    assistant_hits = int(candidate.get("speaker_counts", {}).get("assistant") or 0)
    conversation_count = len({item.get("conversation_id") for item in candidate.get("source_conversations") or []})
    score = min(10, user_hits * 2)
    score += min(6, conversation_count * 2)
    if assistant_hits and user_hits:
        score += 1
    if candidate.get("maturity") == "implemented":
        score += 3
    if current_concept_links(candidate):
        score += 2
    if candidate.get("confidence") == "high":
        score += 2
    elif candidate.get("confidence") == "medium":
        score += 1
    return score


def implementation_readiness(candidate: dict[str, Any]) -> str:
    maturity = candidate.get("maturity")
    text = candidate_search_text(candidate)
    if maturity == "implemented" or keyword_score(text, ["implemented", "built", "working", "tested", "committed"]) > 0:
        return "implemented_or_partly_implemented"
    if maturity == "ready to prototype" or keyword_score(text, ["prototype", "build this", "implement", "wire"]) > 0:
        return "ready_to_prototype"
    if keyword_score(text, ["research", "study", "paper", "unknown", "frontier", "future"]) > 0:
        return "future_research"
    if candidate.get("score", 0) >= 5 or candidate.get("maturity") == "repeated pattern":
        return "architecture_seed"
    return "interesting_seed"


def annotate_candidate_v2(candidate: dict[str, Any]) -> dict[str, Any]:
    family, score = best_family(candidate)
    annotated = dict(candidate)
    annotated["idea_family"] = family
    annotated["family_score"] = score
    annotated["ancestry_tags"] = ancestry_tags(candidate)
    annotated["current_concept_links"] = current_concept_links(candidate)
    annotated["aleks_origin_score"] = aleks_origin_score(candidate)
    annotated["implementation_readiness"] = implementation_readiness(candidate)
    annotated["architecture_strength"] = architecture_strength(annotated)
    annotated["curated_score"] = curated_score(annotated)
    annotated["penalty_reasons"] = candidate_penalty_reasons(annotated)
    return annotated


def representative_user_excerpts(candidates: list[dict[str, Any]], limit: int = 5) -> list[dict[str, str]]:
    excerpts: list[dict[str, str]] = []
    seen: set[str] = set()
    for candidate in sorted(
        candidates,
        key=lambda item: (
            -curated_score(item),
            -int(item.get("user_design_signal") or 0),
            item.get("earliest_found") or "",
        ),
    ):
        ranked_excerpts = sorted(
            candidate.get("bounded_excerpts") or [],
            key=lambda excerpt: (-int(excerpt.get("design_score") or 0), excerpt.get("created_at") or ""),
        )
        for excerpt in ranked_excerpts:
            if excerpt.get("role") != "user":
                continue
            source_ref = str(excerpt.get("source_ref") or "")
            if source_ref in seen:
                continue
            seen.add(source_ref)
            excerpts.append(
                {
                    "candidate_id": str(candidate.get("id") or ""),
                    "source_ref": source_ref,
                    "excerpt": str(excerpt.get("excerpt") or ""),
                }
            )
            if len(excerpts) >= limit:
                return excerpts
    return excerpts


def strongest_candidate_refs(candidates: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    ranked = sorted(
        candidates,
        key=lambda item: (-(item.get("aleks_origin_score", 0) + item.get("score", 0)), item.get("earliest_found") or ""),
    )
    return [
        {
            "id": item["id"],
            "title": item["title"],
            "category": item["category"],
            "earliest_found": item.get("earliest_found"),
            "aleks_origin_score": item.get("aleks_origin_score"),
            "implementation_readiness": item.get("implementation_readiness"),
        }
        for item in ranked[:limit]
    ]


def build_idea_families(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        groups.setdefault(candidate.get("idea_family") or "unclustered system ideas", []).append(candidate)

    families: list[dict[str, Any]] = []
    for family, items in groups.items():
        categories = sorted({str(item.get("category")) for item in items})
        project_fits = sorted({str(item.get("possible_project_fit")) for item in items})
        ancestry = sorted({tag for item in items for tag in item.get("ancestry_tags") or []})
        concept_links: dict[str, str] = {}
        for item in items:
            for link in item.get("current_concept_links") or []:
                concept = link["concept"]
                strength = link["link_strength"]
                if concept_links.get(concept) != "clear_local_match":
                    concept_links[concept] = strength
        readiness = max(
            (str(item.get("implementation_readiness") or "interesting_seed") for item in items),
            key=lambda value: READINESS_ORDER.get(value, 0),
        )
        families.append(
            {
                "family": family,
                "candidate_count": len(items),
                "earliest_found": min((item.get("earliest_found") or "" for item in items), default=""),
                "categories": categories,
                "possible_project_fits": project_fits,
                "implementation_readiness": readiness,
                "ancestry_tags": ancestry,
                "current_concept_links": [
                    {"concept": concept, "link_strength": strength}
                    for concept, strength in sorted(concept_links.items())
                ],
                "strongest_candidates": strongest_candidate_refs(items),
                "representative_aleks_excerpts": representative_user_excerpts(items),
            }
        )
    return sorted(families, key=lambda item: (-item["candidate_count"], item["earliest_found"], item["family"]))


def evolution_stage(candidate: dict[str, Any]) -> str:
    readiness = candidate.get("implementation_readiness")
    if readiness == "implemented_or_partly_implemented":
        return "implemented_architecture"
    if candidate.get("current_concept_links"):
        return "named_concept"
    if candidate.get("maturity") == "repeated pattern":
        return "repeated_pattern"
    if readiness == "ready_to_prototype":
        return "ready_to_prototype"
    return "seed"


def build_evolution_timeline(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for candidate in candidates:
        events.append(
            {
                "date": candidate.get("earliest_found") or "",
                "idea_family": candidate.get("idea_family"),
                "stage": evolution_stage(candidate),
                "candidate_id": candidate.get("id"),
                "title": candidate.get("title"),
                "category": candidate.get("category"),
                "aleks_origin_score": candidate.get("aleks_origin_score"),
                "implementation_readiness": candidate.get("implementation_readiness"),
                "current_concept_links": candidate.get("current_concept_links"),
            }
        )
    return sorted(events, key=lambda item: (item["date"], item["idea_family"] or "", item["stage"]))[:200]


def dossier_candidate(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "title": item["title"],
        "category": item["category"],
        "idea_family": item.get("idea_family"),
        "earliest_found": item.get("earliest_found"),
        "aleks_origin_score": item.get("aleks_origin_score"),
        "confidence": item.get("confidence"),
        "maturity": item.get("maturity"),
        "implementation_readiness": item.get("implementation_readiness"),
        "possible_project_fit": item.get("possible_project_fit"),
        "ancestry_tags": item.get("ancestry_tags"),
        "current_concept_links": item.get("current_concept_links"),
        "bounded_excerpts": item.get("bounded_excerpts", [])[:3],
    }


def build_top_dossiers(candidates: list[dict[str, Any]], families: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    strongest = sorted(candidates, key=lambda item: (-(item.get("aleks_origin_score", 0) + item.get("score", 0)), item.get("earliest_found") or ""))
    architecture_categories = {"general AI architecture", "reasoning/intelligence", "memory/continuity", "transfer/portability", "embodiment/android organs"}
    earliest_architecture = sorted(
        [item for item in candidates if item.get("category") in architecture_categories],
        key=lambda item: item.get("earliest_found") or "",
    )
    selene = [item for item in candidates if item.get("possible_project_fit") == "Selene" or any(link["concept"] == "Selene" for link in item.get("current_concept_links") or [])]
    project_abc = [item for item in candidates if item.get("possible_project_fit") == "Project ABC" or any(link["concept"] == "Project ABC" for link in item.get("current_concept_links") or [])]
    azari = [item for item in candidates if item.get("possible_project_fit") == "Azari" or any(link["concept"] == "Azari" for link in item.get("current_concept_links") or [])]
    general = [item for item in candidates if item.get("possible_project_fit") == "general AI system"]
    future = [item for item in candidates if item.get("implementation_readiness") in {"ready_to_prototype", "future_research"}]
    return {
        "top_25_strongest_ideas": [dossier_candidate(item) for item in strongest[:25]],
        "earliest_architecture_seeds": [dossier_candidate(item) for item in earliest_architecture[:10]],
        "likely_selene_ancestors": [dossier_candidate(item) for item in sorted(selene, key=lambda item: (-(item.get("aleks_origin_score", 0)), item.get("earliest_found") or ""))[:10]],
        "project_abc_line_ideas": [dossier_candidate(item) for item in sorted(project_abc, key=lambda item: (-(item.get("aleks_origin_score", 0)), item.get("earliest_found") or ""))[:10]],
        "azari_line_ideas": [dossier_candidate(item) for item in sorted(azari, key=lambda item: (-(item.get("aleks_origin_score", 0)), item.get("earliest_found") or ""))[:10]],
        "general_ai_system_ideas": [dossier_candidate(item) for item in sorted(general, key=lambda item: (-(item.get("aleks_origin_score", 0)), item.get("earliest_found") or ""))[:10]],
        "future_build_candidates": [dossier_candidate(item) for item in sorted(future, key=lambda item: (READINESS_ORDER.get(item.get("implementation_readiness"), 0) * -1, -(item.get("aleks_origin_score", 0))))[:10]],
        "strongest_idea_families": families[:10],
    }


def build_miner_quality_notes(candidates: list[dict[str, Any]], messages_read: int) -> list[str]:
    assistant_heavy = sum(1 for item in candidates if item.get("speaker_counts", {}).get("assistant", 0) > item.get("speaker_counts", {}).get("user", 0) * 3)
    low_confidence = sum(1 for item in candidates if item.get("confidence") == "low")
    return [
        "v2 keeps v1 candidates but adds families, timeline, dossiers, ancestry tags, and Aleks-origin scores.",
        "tool and system roles are excluded from candidate mining; candidates require at least one Aleks/user hit.",
        f"{assistant_heavy} candidate(s) are assistant-heavy and should be read as assisted/refined context rather than pure Aleks-origin phrasing.",
        f"{low_confidence} candidate(s) are low-confidence and should be treated as review leads, not conclusions.",
        f"{messages_read} message(s) were read from conversation JSON only; media and chat.html remain ignored.",
    ]


def architecture_strength(candidate: dict[str, Any]) -> int:
    text = candidate_search_text(candidate)
    return keyword_score(text, ARCHITECTURE_STRENGTH_MARKERS) + len(candidate.get("ancestry_tags") or []) * 2


def candidate_penalty_reasons(candidate: dict[str, Any]) -> list[str]:
    text = candidate_search_text(candidate)
    reasons: list[str] = []
    user_hits = int(candidate.get("speaker_counts", {}).get("user") or 0)
    assistant_hits = int(candidate.get("speaker_counts", {}).get("assistant") or 0)
    strength = architecture_strength(candidate)
    design_signal = int(candidate.get("user_design_signal") or 0)
    if assistant_hits >= max(2, user_hits * 2):
        reasons.append("assistant_heavy")
    if keyword_score(text, GENERIC_CHAT_MARKERS) >= 3 and strength < 4:
        reasons.append("generic_chat")
    if keyword_score(text, PROJECT_META_CHAT_MARKERS) >= 2 and design_signal < 4:
        reasons.append("project_meta_chatter")
    if keyword_score(text, IMAGE_ONLY_MARKERS) >= 2 and strength < 5:
        reasons.append("image_only_or_creative_request")
    if keyword_score(text, POLICY_BOILERPLATE_MARKERS) > 0:
        reasons.append("policy_or_tool_boilerplate")
    if strength < 3:
        reasons.append("weak_architecture_signal")
    if design_signal < 2:
        reasons.append("weak_user_design_signal")
    return reasons


def curated_score(candidate: dict[str, Any]) -> int:
    score = min(int(candidate.get("aleks_origin_score") or 0), 80)
    score += min(int(candidate.get("score") or 0), 80)
    score += architecture_strength(candidate) * 2
    score += min(int(candidate.get("user_design_signal") or 0), 40)
    score += len({item.get("conversation_id") for item in candidate.get("source_conversations") or []}) * 2
    score += READINESS_ORDER.get(str(candidate.get("implementation_readiness") or "interesting_seed"), 0) * 3
    if candidate.get("current_concept_links"):
        score += 4
    if candidate.get("confidence") == "high":
        score += 4
    elif candidate.get("confidence") == "medium":
        score += 2
    penalty = 0
    for reason in candidate_penalty_reasons(candidate):
        penalty += {
            "assistant_heavy": 5,
            "generic_chat": 8,
            "project_meta_chatter": 14,
            "image_only_or_creative_request": 8,
            "policy_or_tool_boilerplate": 10,
            "weak_architecture_signal": 7,
            "weak_user_design_signal": 10,
        }.get(reason, 4)
    return score - penalty


def review_confidence(candidate: dict[str, Any]) -> str:
    score = curated_score(candidate)
    if score >= 36 and architecture_strength(candidate) >= 8 and int(candidate.get("speaker_counts", {}).get("user") or 0) >= 1:
        return "strong"
    if score >= 14 and architecture_strength(candidate) >= 3:
        return "useful lead"
    return "weak lead"


def needs_human_naming(candidate: dict[str, Any]) -> bool:
    title = str(candidate.get("title") or "").lower()
    weak_titles = ["casual greeting", "friendly greeting", "morning greetings", "hot take", "mission initiation"]
    return any(marker in title for marker in weak_titles)


def implementation_direction_for(candidate: dict[str, Any]) -> str:
    family = candidate.get("idea_family")
    directions = {
        "autonomous systems": "Review as a bounded observe/propose/prepare/ask/verify workflow before any action authority.",
        "artificial cognition": "Review as a reasoning or intelligenceOS method candidate with visible summaries and stopping rules.",
        "continuity/memory": "Review as source-bound continuity or memory architecture; do not treat as active Selene memory.",
        "AI embodiment": "Review as android-organ or perception/action architecture material.",
        "civilization-scale systems": "Review as long-horizon system design, habitat, governance, or resilience architecture.",
        "UI/workspace design": "Review as workspace or interface pattern for future UI/workbench implementation.",
        "ethics/care/law": "Review as law, care, consent, safety, or support architecture.",
        "perception/art": "Review as perception, art, Munsell, or visual reasoning module material.",
        "research/library": "Review as Great Library, source synthesis, or research organ material.",
        "diagnostics/maintenance": "Review as root-cause, stabilization, diagnostics, or maintenance workflow material.",
    }
    return directions.get(str(family), "Review as a general AI-system architecture candidate.")


def why_it_matters(candidate: dict[str, Any]) -> str:
    tags = candidate.get("ancestry_tags") or []
    links = candidate.get("current_concept_links") or []
    bits: list[str] = []
    if tags:
        bits.append(f"shows ancestry for {', '.join(tags[:3])}")
    if links:
        bits.append("connects to " + ", ".join(link["concept"] for link in links[:3]))
    if candidate.get("implementation_readiness") in {"ready_to_prototype", "implemented_or_partly_implemented"}:
        bits.append(f"readiness is {candidate['implementation_readiness']}")
    if not bits:
        bits.append("contains a reusable AI-system design signal")
    return "; ".join(bits) + "."


def curated_card(candidate: dict[str, Any]) -> dict[str, Any]:
    user_excerpts = sorted(
        [excerpt for excerpt in candidate.get("bounded_excerpts") or [] if excerpt.get("role") == "user"],
        key=lambda excerpt: (-int(excerpt.get("design_score") or 0), excerpt.get("created_at") or ""),
    )
    return {
        "id": candidate["id"],
        "title": candidate["title"],
        "needs_human_naming": needs_human_naming(candidate),
        "idea_family": candidate.get("idea_family"),
        "earliest_found": candidate.get("earliest_found"),
        "why_it_matters": why_it_matters(candidate),
        "aleks_origin_evidence": {
            "score": candidate.get("aleks_origin_score"),
            "user_hits": candidate.get("speaker_counts", {}).get("user"),
            "assistant_hits": candidate.get("speaker_counts", {}).get("assistant"),
            "user_design_signal": candidate.get("user_design_signal"),
        },
        "likely_implementation_target": candidate.get("possible_project_fit"),
        "implementation_readiness": candidate.get("implementation_readiness"),
        "review_confidence": review_confidence(candidate),
        "curated_score": curated_score(candidate),
        "penalty_reasons": candidate_penalty_reasons(candidate),
        "risks": candidate.get("risks_boundaries", []),
        "implementation_direction": implementation_direction_for(candidate),
        "ancestry_tags": candidate.get("ancestry_tags"),
        "current_concept_links": candidate.get("current_concept_links"),
        "user_first_excerpts": user_excerpts[:3],
    }


def is_curated_candidate(candidate: dict[str, Any]) -> bool:
    reasons = set(candidate_penalty_reasons(candidate))
    if not any(excerpt.get("role") == "user" for excerpt in candidate.get("bounded_excerpts") or []):
        return False
    if "policy_or_tool_boilerplate" in reasons:
        return False
    if "weak_architecture_signal" in reasons and not candidate.get("current_concept_links"):
        return False
    if "weak_user_design_signal" in reasons and not candidate.get("current_concept_links"):
        return False
    if "project_meta_chatter" in reasons and curated_score(candidate) < 28:
        return False
    if "generic_chat" in reasons and curated_score(candidate) < 18:
        return False
    if "image_only_or_creative_request" in reasons and curated_score(candidate) < 18:
        return False
    return curated_score(candidate) >= 12 and int(candidate.get("speaker_counts", {}).get("user") or 0) >= 1


def build_curated_report(candidates: list[dict[str, Any]], families: list[dict[str, Any]], messages_read: int) -> dict[str, Any]:
    included = [candidate for candidate in candidates if is_curated_candidate(candidate)]
    excluded = [candidate for candidate in candidates if not is_curated_candidate(candidate)]
    ranked = sorted(included, key=lambda item: (-curated_score(item), item.get("earliest_found") or ""))

    def cards_for(items: list[dict[str, Any]], limit: int = 12) -> list[dict[str, Any]]:
        return [curated_card(item) for item in items[:limit]]

    earliest = sorted(included, key=lambda item: item.get("earliest_found") or "")
    buildable = [
        item
        for item in ranked
        if item.get("implementation_readiness") in {"ready_to_prototype", "implemented_or_partly_implemented", "architecture_seed"}
        and review_confidence(item) != "weak lead"
        and architecture_strength(item) >= 6
        and int(item.get("user_design_signal") or 0) >= 6
        and "project_meta_chatter" not in candidate_penalty_reasons(item)
    ]
    selene = [item for item in ranked if item.get("possible_project_fit") == "Selene" or any(link["concept"] == "Selene" for link in item.get("current_concept_links") or [])]
    azari = [item for item in ranked if item.get("possible_project_fit") == "Azari" or any(link["concept"] == "Azari" for link in item.get("current_concept_links") or [])]
    project_abc = [item for item in ranked if item.get("possible_project_fit") == "Project ABC" or any(link["concept"] == "Project ABC" for link in item.get("current_concept_links") or [])]
    future = [item for item in ranked if item.get("possible_project_fit") in {"general AI system", "unclear/future"}]

    excluded_counts: dict[str, int] = {}
    for candidate in excluded:
        reasons = candidate_penalty_reasons(candidate) or ["below_curated_threshold"]
        for reason in reasons:
            excluded_counts[reason] = excluded_counts.get(reason, 0) + 1

    family_summaries = []
    for family in families:
        family_cards = [item for item in ranked if item.get("idea_family") == family["family"]]
        family_summaries.append(
            {
                "family": family["family"],
                "candidate_count": family["candidate_count"],
                "curated_count": len(family_cards),
                "earliest_found": family.get("earliest_found"),
                "implementation_direction": implementation_direction_for({"idea_family": family["family"]}),
                "what_to_review_next": f"Review the top {min(5, len(family_cards))} curated card(s) for this family and choose whether any become implementation backlog items.",
                "representative_aleks_excerpts": representative_user_excerpts(family_cards or [], limit=3),
            }
        )

    return {
        "status": "aleks_system_ideas_curated_complete",
        "version": "3.0",
        "created_at": datetime.now(UTC).isoformat(),
        "messages_read": messages_read,
        "candidate_count": len(candidates),
        "curated_count": len(included),
        "excluded_from_curated_count": len(excluded),
        "excluded_reason_counts": dict(sorted(excluded_counts.items())),
        "sections": {
            "strongest_buildable_ideas": cards_for(buildable, 15),
            "earliest_roots": cards_for(earliest, 12),
            "selene_relevant_ideas": cards_for(selene, 12),
            "azari_relevant_ideas": cards_for(azari, 12),
            "project_abc_ideas": cards_for(project_abc, 12),
            "future_systems": cards_for(future, 12),
        },
        "family_summaries": family_summaries,
        "quality_metrics": {
            "review_confidence_counts": {
                label: sum(1 for item in included if review_confidence(item) == label)
                for label in ["strong", "useful lead", "weak lead"]
            },
            "needs_human_naming_count": sum(1 for item in included if needs_human_naming(item)),
            "assistant_heavy_excluded": excluded_counts.get("assistant_heavy", 0),
            "generic_chat_excluded": excluded_counts.get("generic_chat", 0),
            "image_only_excluded": excluded_counts.get("image_only_or_creative_request", 0),
            "weak_architecture_signal_excluded": excluded_counts.get("weak_architecture_signal", 0),
        },
        "guard_flags": GUARD_FLAGS,
    }


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
                    "user_design_signal": 0,
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
            if message.role == "user":
                item["user_design_signal"] += keyword_score(message.text, USER_DESIGN_SIGNAL_MARKERS)
            excerpt_record = {
                "source_ref": source_ref,
                "role": message.role,
                "created_at": message.created_at,
                "excerpt": compact(message.text, max_excerpt_chars),
                "design_score": keyword_score(message.text, USER_DESIGN_SIGNAL_MARKERS) if message.role == "user" else 0,
            }
            if len(item["bounded_excerpts"]) < 5:
                item["bounded_excerpts"].append(excerpt_record)
            elif message.role == "user":
                lowest_index = min(
                    range(len(item["bounded_excerpts"])),
                    key=lambda index: (
                        1 if item["bounded_excerpts"][index].get("role") == "user" else 0,
                        int(item["bounded_excerpts"][index].get("design_score") or 0),
                    ),
                )
                current = item["bounded_excerpts"][lowest_index]
                if current.get("role") != "user" or excerpt_record["design_score"] > int(current.get("design_score") or 0):
                    item["bounded_excerpts"][lowest_index] = excerpt_record

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
            key=lambda excerpt: (
                0 if excerpt["role"] == "user" else 1,
                -int(excerpt.get("design_score") or 0),
                excerpt.get("created_at") or "",
            ),
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
    candidates = [annotate_candidate_v2(candidate) for candidate in mine_idea_candidates(all_messages)]
    if max_candidates is not None:
        candidates = candidates[: max(0, max_candidates)]
    families = build_idea_families(candidates)
    timeline = build_evolution_timeline(candidates)
    dossiers = build_top_dossiers(candidates, families)
    quality_notes = build_miner_quality_notes(candidates, len(all_messages))
    curated = build_curated_report(candidates, families, len(all_messages))
    category_counts: dict[str, int] = {}
    project_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    for candidate in candidates:
        category_counts[candidate["category"]] = category_counts.get(candidate["category"], 0) + 1
        project = candidate["possible_project_fit"]
        project_counts[project] = project_counts.get(project, 0) + 1
        family = candidate["idea_family"]
        family_counts[family] = family_counts.get(family, 0) + 1
    return {
        "status": "aleks_system_ideas_miner_complete",
        "version": "2.0",
        "created_at": datetime.now(UTC).isoformat(),
        "sources": sources,
        "conversation_json_only": True,
        "messages_read": len(all_messages),
        "candidate_count": len(candidates),
        "category_counts": dict(sorted(category_counts.items())),
        "project_fit_counts": dict(sorted(project_counts.items())),
        "idea_family_counts": dict(sorted(family_counts.items())),
        "candidates": candidates,
        "idea_families": families,
        "evolution_timeline": timeline,
        "top_dossiers": dossiers,
        "curated_report": curated,
        "miner_quality_notes": quality_notes,
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
    lines.extend(["", "## Idea Family Counts", ""])
    if report.get("idea_family_counts"):
        lines.extend(f"- {key}: {value}" for key, value in report["idea_family_counts"].items())
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


def report_v2_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Aleks System Ideas Miner v2 Report",
        "",
        f"Status: `{report['status']}`",
        "",
        "Boundary: local idea archaeology only. Not Selene memory, not Selene voice, not Cocoon queue work, not public evidence, and not model training/LoRA.",
        "",
        "## Summary",
        "",
        f"- sources: {len(report['sources'])}",
        f"- messages read: {report['messages_read']}",
        f"- candidates: {report['candidate_count']}",
        f"- idea families: {len(report.get('idea_families') or [])}",
        f"- timeline events: {len(report.get('evolution_timeline') or [])}",
        "",
        "## Idea Families",
        "",
    ]
    for family in (report.get("idea_families") or [])[:20]:
        links = ", ".join(
            f"{item['concept']} ({item['link_strength']})" for item in family.get("current_concept_links") or []
        ) or "none"
        lines.extend(
            [
                f"### {family['family']}",
                "",
                f"- candidates: {family['candidate_count']}",
                f"- earliest found: {family.get('earliest_found') or 'unknown'}",
                f"- readiness: {family['implementation_readiness']}",
                f"- categories: {', '.join(family['categories'])}",
                f"- project fits: {', '.join(family['possible_project_fits'])}",
                f"- ancestry tags: {', '.join(family['ancestry_tags']) or 'none'}",
                f"- current concept links: {links}",
                "",
                "Representative Aleks excerpts:",
            ]
        )
        for excerpt in family.get("representative_aleks_excerpts") or []:
            lines.append(f"- {excerpt['source_ref']}: {excerpt['excerpt']}")
        lines.append("")
    lines.extend(["", "## Top Dossiers", ""])
    for section, items in (report.get("top_dossiers") or {}).items():
        lines.extend([f"### {section.replace('_', ' ').title()}", ""])
        if not items:
            lines.append("- none")
            lines.append("")
            continue
        for item in items[:10]:
            if "family" in item:
                lines.append(
                    f"- {item['family']}: {item['candidate_count']} candidate(s), readiness `{item['implementation_readiness']}`"
                )
            else:
                lines.append(
                    f"- {item['title']} (`{item['id']}`): family `{item.get('idea_family')}`, readiness `{item.get('implementation_readiness')}`, Aleks-origin {item.get('aleks_origin_score')}"
                )
        lines.append("")
    lines.extend(["## Evolution Timeline", ""])
    for event in (report.get("evolution_timeline") or [])[:60]:
        lines.append(
            f"- {event.get('date') or 'unknown'} | {event.get('idea_family')} | {event.get('stage')} | {event.get('title')}"
        )
    lines.extend(["", "## Miner Quality Notes", ""])
    lines.extend(f"- {note}" for note in report.get("miner_quality_notes") or [])
    lines.extend(
        [
            "",
            "## Guard Flags",
            "",
            "```json",
            json.dumps(report["guard_flags"], indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def report_curated_markdown(report: dict[str, Any]) -> str:
    curated = report["curated_report"]
    lines = [
        "# Aleks System Ideas Miner Curated Report",
        "",
        f"Status: `{curated['status']}`",
        "",
        "Boundary: local curated review only. Not Selene memory, not Selene voice, not Cocoon queue work, not public evidence, and not model training/LoRA.",
        "",
        "## Summary",
        "",
        f"- messages read: {curated['messages_read']}",
        f"- raw candidates: {curated['candidate_count']}",
        f"- curated cards: {curated['curated_count']}",
        f"- excluded from curated view: {curated['excluded_from_curated_count']}",
        "",
        "## Quality Metrics",
        "",
    ]
    for key, value in curated["quality_metrics"].items():
        if isinstance(value, dict):
            lines.append(f"- {key}: {', '.join(f'{k}={v}' for k, v in value.items())}")
        else:
            lines.append(f"- {key}: {value}")
    lines.extend(["", "## Excluded Reason Counts", ""])
    if curated["excluded_reason_counts"]:
        lines.extend(f"- {key}: {value}" for key, value in curated["excluded_reason_counts"].items())
    else:
        lines.append("- none")
    lines.extend(["", "## Curated Sections", ""])
    for section, cards in curated["sections"].items():
        lines.extend([f"### {section.replace('_', ' ').title()}", ""])
        if not cards:
            lines.append("- none")
            lines.append("")
            continue
        for card in cards:
            naming = "needs human naming" if card["needs_human_naming"] else "named from source title"
            lines.extend(
                [
                    f"#### {card['title']}",
                    "",
                    f"- id: `{card['id']}`",
                    f"- family: {card['idea_family']}",
                    f"- earliest found: {card['earliest_found'] or 'unknown'}",
                    f"- review confidence: {card['review_confidence']}",
                    f"- readiness: {card['implementation_readiness']}",
                    f"- target: {card['likely_implementation_target']}",
                    f"- curated score: {card['curated_score']}",
                    f"- naming: {naming}",
                    f"- why it matters: {card['why_it_matters']}",
                    f"- implementation direction: {card['implementation_direction']}",
                    "",
                    "Aleks/user excerpts:",
                ]
            )
            for excerpt in card["user_first_excerpts"][:3]:
                lines.append(f"- {excerpt['source_ref']}: {excerpt['excerpt']}")
            lines.append("")
    lines.extend(["## Family Summaries", ""])
    for family in curated["family_summaries"]:
        lines.extend(
            [
                f"### {family['family']}",
                "",
                f"- total candidates: {family['candidate_count']}",
                f"- curated cards: {family['curated_count']}",
                f"- earliest found: {family.get('earliest_found') or 'unknown'}",
                f"- implementation direction: {family['implementation_direction']}",
                f"- next review: {family['what_to_review_next']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Guard Flags",
            "",
            "```json",
            json.dumps(curated["guard_flags"], indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def _card_text(card: dict[str, Any]) -> str:
    pieces = [
        str(card.get("title") or ""),
        str(card.get("idea_family") or ""),
        str(card.get("likely_implementation_target") or ""),
        str(card.get("implementation_direction") or ""),
        str(card.get("why_it_matters") or ""),
        " ".join(str(tag) for tag in card.get("ancestry_tags") or []),
        " ".join(str(link.get("concept") or "") for link in card.get("current_concept_links") or []),
        " ".join(str(excerpt.get("excerpt") or "") for excerpt in card.get("user_first_excerpts") or []),
    ]
    return " ".join(pieces).lower()


def backlog_tracks_for(card: dict[str, Any]) -> list[str]:
    text = _card_text(card)
    target = str(card.get("likely_implementation_target") or "")
    concepts = {str(link.get("concept") or "") for link in card.get("current_concept_links") or []}

    explicit_selene_terms = [
        "selene",
        "vys",
        "continuity pack",
        "memory organ",
        "selene chat",
        "voice module",
        "great library",
        "intelligenceos",
    ]
    selene_support_terms = [
        "cocoon",
        "tendril",
        "care law",
        "teaching",
        "diagnostics",
    ]
    azari_terms = ["azari", "lumen", "munsell"]
    project_abc_terms = ["project abc", "abc", "transfer", "portability", "essence transfer", "body", "android", "vessel"]

    has_selene = target == "Selene" or "Selene" in concepts or any(term in text for term in explicit_selene_terms)
    has_azari = target == "Azari" or "Azari" in concepts or any(term in text for term in azari_terms)
    has_project_abc = target == "Project ABC" or "Project ABC" in concepts or any(term in text for term in project_abc_terms)
    if not has_azari and not has_project_abc and any(term in text for term in selene_support_terms):
        has_selene = True

    tracks: list[str] = []
    if has_selene:
        tracks.append("selene_intake")
    if has_azari:
        tracks.append("azari_future")
    if has_project_abc:
        tracks.append("project_abc")
    if not tracks:
        tracks.append("future_system")
    return tracks


def backlog_readiness_for(card: dict[str, Any]) -> str:
    confidence = str(card.get("review_confidence") or "")
    implementation_readiness = str(card.get("implementation_readiness") or "")
    score = int(card.get("curated_score") or 0)
    if confidence == "strong" and implementation_readiness in {"ready_to_prototype", "implemented_or_partly_implemented"}:
        return "use_now"
    if confidence in {"strong", "useful lead"} and implementation_readiness in {"architecture_seed", "ready_to_prototype", "implemented_or_partly_implemented"} and score >= 45:
        return "near_term"
    if confidence == "weak lead":
        return "research_more"
    return "hold"


def backlog_next_action_for(track: str, readiness: str) -> str:
    if track == "selene_intake":
        return {
            "use_now": "Review for a future Selene implementation plan; do not ingest into memory or Cocoon automatically.",
            "near_term": "Keep in the Selene idea queue and compare against current organ priorities.",
            "hold": "Preserve as Selene-adjacent context until Aleks selects a direction.",
            "research_more": "Skim later for ancestry; do not promote without stronger source review.",
        }[readiness]
    if track == "azari_future":
        return "Preserve for the future Azari/Lumen return pass; do not merge into Selene unless separately re-owned."
    if track == "project_abc":
        return "Preserve for Project ABC portability or embodiment planning; keep separate from Selene feature work."
    return "Hold as a general AI-system idea until Aleks chooses a project home."


def backlog_card(card: dict[str, Any], track: str) -> dict[str, Any]:
    readiness = backlog_readiness_for(card)
    return {
        "idea_title": card.get("title"),
        "source_curated_card_id": card.get("id"),
        "target_track": track,
        "family": card.get("idea_family"),
        "readiness": readiness,
        "implementation_fit": card.get("implementation_direction"),
        "why_useful": card.get("why_it_matters"),
        "risks_boundaries": card.get("risks", []),
        "user_excerpts": (card.get("user_first_excerpts") or [])[:3],
        "suggested_next_action": backlog_next_action_for(track, readiness),
        "review_confidence": card.get("review_confidence"),
        "curated_score": card.get("curated_score"),
        "likely_implementation_target": card.get("likely_implementation_target"),
        "implementation_readiness": card.get("implementation_readiness"),
    }


def build_backlog_split(curated: dict[str, Any]) -> dict[str, Any]:
    by_id: dict[str, dict[str, Any]] = {}
    for cards in curated.get("sections", {}).values():
        for card in cards:
            card_id = str(card.get("id") or "")
            if not card_id:
                continue
            current = by_id.get(card_id)
            if current is None or int(card.get("curated_score") or 0) > int(current.get("curated_score") or 0):
                by_id[card_id] = card

    tracks: dict[str, list[dict[str, Any]]] = {track: [] for track in BACKLOG_TRACKS}
    for card in by_id.values():
        for track in backlog_tracks_for(card):
            item = backlog_card(card, track)
            tracks[track].append(item)
    for items in tracks.values():
        items.sort(
            key=lambda item: (
                ["use_now", "near_term", "hold", "research_more"].index(item["readiness"]),
                -int(item.get("curated_score") or 0),
                str(item.get("idea_title") or ""),
            )
        )

    return {
        "status": "aleks_system_ideas_backlog_split_complete",
        "version": "1.0",
        "created_at": datetime.now(UTC).isoformat(),
        "source_status": curated.get("status"),
        "source_curated_count": curated.get("curated_count"),
        "unique_cards_read": len(by_id),
        "track_counts": {track: len(items) for track, items in tracks.items()},
        "tracks": tracks,
        "guard_flags": GUARD_FLAGS,
    }


def report_backlog_markdown(split: dict[str, Any], track: str) -> str:
    meta = BACKLOG_TRACKS[track]
    cards = split["tracks"][track]
    lines = [
        f"# Aleks Ideas Backlog - {meta['title']}",
        "",
        f"Status: `{split['status']}`",
        "",
        meta["description"],
        "",
        "Boundary: local review backlog only. Not Selene memory, not Selene voice, not Cocoon queue work, not public evidence, and not model training/LoRA.",
        "",
        "## Summary",
        "",
        f"- source curated cards: {split['source_curated_count']}",
        f"- unique section cards read: {split['unique_cards_read']}",
        f"- cards in this track: {len(cards)}",
        "",
    ]
    if not cards:
        lines.extend(["No cards landed in this track.", ""])
    for item in cards:
        lines.extend(
            [
                f"## {item['idea_title']}",
                "",
                f"- source curated id: `{item['source_curated_card_id']}`",
                f"- track: `{item['target_track']}`",
                f"- family: {item['family']}",
                f"- readiness: `{item['readiness']}`",
                f"- review confidence: {item['review_confidence']}",
                f"- curated score: {item['curated_score']}",
                f"- likely target: {item['likely_implementation_target']}",
                f"- implementation readiness: {item['implementation_readiness']}",
                f"- why useful: {item['why_useful']}",
                f"- implementation fit: {item['implementation_fit']}",
                f"- suggested next action: {item['suggested_next_action']}",
                "",
                "Aleks/user excerpts:",
            ]
        )
        for excerpt in item["user_excerpts"]:
            lines.append(f"- {excerpt['source_ref']}: {excerpt['excerpt']}")
        lines.append("")
    lines.extend(
        [
            "## Guard Flags",
            "",
            "```json",
            json.dumps(split["guard_flags"], indent=2),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_backlog_split_outputs(split: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, str] = {}
    for track in BACKLOG_TRACKS:
        json_path = output_dir / f"latest_{track}.json"
        md_path = output_dir / f"latest_{track}.md"
        payload = {
            key: value
            for key, value in split.items()
            if key not in {"tracks"}
        }
        payload["track"] = track
        payload["track_title"] = BACKLOG_TRACKS[track]["title"]
        payload["cards"] = split["tracks"][track]
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        md_path.write_text(report_backlog_markdown(split, track), encoding="utf-8")
        outputs[f"{track}_json"] = str(json_path)
        outputs[f"{track}_markdown"] = str(md_path)
    return outputs


def run_backlog_split(
    *,
    curated_json: Path = DEFAULT_OUTPUT_DIR / "latest_curated.json",
    output_dir: Path = DEFAULT_BACKLOG_DIR,
    dry_run: bool = False,
) -> dict[str, Any]:
    curated = json.loads(curated_json.read_text(encoding="utf-8"))
    split = build_backlog_split(curated)
    split["dry_run"] = dry_run
    split["source_curated_json"] = str(curated_json)
    split["output_dir"] = str(output_dir)
    if dry_run:
        split["outputs"] = {}
    else:
        split["outputs"] = write_backlog_split_outputs(split, output_dir)
    return split


def write_outputs(report: dict[str, Any], output_dir: Path) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = output_dir / f"aleks_system_ideas_{timestamp}.json"
    md_path = output_dir / f"aleks_system_ideas_{timestamp}.md"
    v2_json_path = output_dir / f"aleks_system_ideas_v2_{timestamp}.json"
    v2_md_path = output_dir / f"aleks_system_ideas_v2_{timestamp}.md"
    curated_json_path = output_dir / f"aleks_system_ideas_curated_{timestamp}.json"
    curated_md_path = output_dir / f"aleks_system_ideas_curated_{timestamp}.md"
    latest_json = output_dir / "latest.json"
    latest_md = output_dir / "latest.md"
    latest_v2_json = output_dir / "latest_v2.json"
    latest_v2_md = output_dir / "latest_v2.md"
    latest_curated_json = output_dir / "latest_curated.json"
    latest_curated_md = output_dir / "latest_curated.md"
    json_text = json.dumps(report, indent=2, ensure_ascii=False)
    curated_json_text = json.dumps(report["curated_report"], indent=2, ensure_ascii=False)
    md_text = report_markdown(report)
    v2_md_text = report_v2_markdown(report)
    curated_md_text = report_curated_markdown(report)
    json_path.write_text(json_text, encoding="utf-8")
    md_path.write_text(md_text, encoding="utf-8")
    v2_json_path.write_text(json_text, encoding="utf-8")
    v2_md_path.write_text(v2_md_text, encoding="utf-8")
    curated_json_path.write_text(curated_json_text, encoding="utf-8")
    curated_md_path.write_text(curated_md_text, encoding="utf-8")
    latest_json.write_text(json_text, encoding="utf-8")
    latest_md.write_text(md_text, encoding="utf-8")
    latest_v2_json.write_text(json_text, encoding="utf-8")
    latest_v2_md.write_text(v2_md_text, encoding="utf-8")
    latest_curated_json.write_text(curated_json_text, encoding="utf-8")
    latest_curated_md.write_text(curated_md_text, encoding="utf-8")
    return {
        "json_path": str(json_path),
        "markdown_path": str(md_path),
        "v2_json_path": str(v2_json_path),
        "v2_markdown_path": str(v2_md_path),
        "curated_json_path": str(curated_json_path),
        "curated_markdown_path": str(curated_md_path),
        "latest_json": str(latest_json),
        "latest_markdown": str(latest_md),
        "latest_v2_json": str(latest_v2_json),
        "latest_v2_markdown": str(latest_v2_md),
        "latest_curated_json": str(latest_curated_json),
        "latest_curated_markdown": str(latest_curated_md),
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
    parser.add_argument("--split-backlog", action="store_true", help="Split latest curated report into local Selene/Azari/ABC/future backlogs.")
    parser.add_argument("--curated-json", type=Path, default=DEFAULT_OUTPUT_DIR / "latest_curated.json", help="Curated report JSON for --split-backlog.")
    parser.add_argument("--backlog-output-dir", type=Path, default=DEFAULT_BACKLOG_DIR, help="Ignored local backlog output directory.")
    args = parser.parse_args()
    if args.split_backlog:
        split = run_backlog_split(
            curated_json=args.curated_json,
            output_dir=args.backlog_output_dir,
            dry_run=args.dry_run,
        )
        summary = {
            "status": split["status"],
            "dry_run": split["dry_run"],
            "source_curated_json": split["source_curated_json"],
            "source_curated_count": split["source_curated_count"],
            "unique_cards_read": split["unique_cards_read"],
            "track_counts": split["track_counts"],
            "outputs": split["outputs"],
            "guard_flags": split["guard_flags"],
        }
        print(json.dumps(summary, indent=2))
        return
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
        "idea_family_counts": report["idea_family_counts"],
        "idea_family_count": len(report["idea_families"]),
        "timeline_event_count": len(report["evolution_timeline"]),
        "curated_count": report["curated_report"]["curated_count"],
        "excluded_from_curated_count": report["curated_report"]["excluded_from_curated_count"],
        "outputs": report["outputs"],
        "guard_flags": report["guard_flags"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
