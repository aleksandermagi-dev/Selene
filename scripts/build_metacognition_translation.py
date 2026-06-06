from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "analysis" / "metacognition_translation_20260606"
RAW_TEXT_DIR = ROOT / "DevelopmentalCorpusArchive_20260526_122541" / "raw_export" / "mydataset" / "text_export"
DOC_FRAMEWORK = ROOT / "docs" / "SELENE_AI_NATIVE_METACOGNITION_FRAMEWORK_20260606.md"
DOC_ADAPTIVE_CONSTITUTION = ROOT / "docs" / "SELENE_ADAPTIVE_CONSTITUTION_MODEL_20260606.md"


BOUNDARY = (
    "research/design only; bounded previews; no training; no memory injection; "
    "no C activation; Aleks cognition material is design reference only"
)


PATTERN_GROUPS: dict[str, list[str]] = {
    "metacognition": [
        r"\bmetacognit",
        r"\bthinking about thinking\b",
        r"\bhow I think\b",
        r"\bhow my mind\b",
        r"\bmy brain\b",
        r"\bself[- ]?aware",
        r"\bself[- ]?model",
        r"\bI notice myself\b",
        r"\bI process\b",
        r"\bI think in systems\b",
        r"\bsystems/layers\b",
        r"\bsystems and layers\b",
    ],
    "emotion_salience": [
        r"\bemotion",
        r"\bfeeling",
        r"\bfeelings",
        r"\bintuition",
        r"\bgut feeling\b",
        r"\bvibe\b",
        r"\bsense of\b",
        r"\bcare\b",
        r"\bspiral",
        r"\bgrounding\b",
        r"\bhumor\b",
        r"\baffect",
        r"\bsalience\b",
    ],
    "pattern_simulation": [
        r"\bpattern recognition\b",
        r"\bpattern[- ]?match",
        r"\bsimulat",
        r"\bmental model",
        r"\bmodel in my head\b",
        r"\bblack hole",
        r"\bcosmolog",
        r"\bgravity\b",
        r"\bsingularity\b",
        r"\buniverse\b",
        r"\bcounterfactual",
        r"\banalog",
    ],
    "azari_cognition": [
        r"\bAzari\b",
        r"\bLumen\b",
        r"\bcognitive pipeline\b",
        r"\bstateful reasoning\b",
        r"\bintent[-_ ]domain\b",
        r"\bemotion understanding\b",
        r"\bconversation_phase\b",
        r"\bresponse_depth\b",
        r"\bmodular cognition\b",
    ],
    "constitution_adaptation": [
        r"\bconstitution",
        r"\blaw\b",
        r"\blaws\b",
        r"\badapt",
        r"\bamend",
        r"\bcase law\b",
        r"\bprecedent",
        r"\brules change\b",
        r"\bsunset\b",
        r"\bgraceful fall\b",
        r"\banti[- ]?spiral\b",
    ],
    "self_model_emergence": [
        r"\bidentity\b",
        r"\bconscious",
        r"\bconsciousness\b",
        r"\bemergence\b",
        r"\bemergent\b",
        r"\bself understanding\b",
        r"\bwho I am\b",
        r"\bwhat I am\b",
    ],
}


SENSITIVE_HINTS = [
    "private",
    "intimate",
    "trauma",
    "grief",
    "family",
    "health",
    "address",
    "location",
    "medical",
    "legal",
    "financial",
    "love",
    "babe",
    "sweetheart",
]


@dataclass
class Candidate:
    candidate_id: str
    source_type: str
    source_file: str
    conversation_id: str
    title: str
    role: str
    create_time: str
    node_id: str
    groups: list[str]
    score: int
    sensitivity: str
    preview: str


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def unix_to_iso(value: Any) -> str:
    try:
        return datetime.fromtimestamp(float(value), timezone.utc).isoformat()
    except Exception:
        return ""


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def bounded(text: str, limit: int = 320) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def message_text(message: dict[str, Any]) -> str:
    content = message.get("content") or {}
    parts = content.get("parts")
    if isinstance(parts, list):
        return clean_text(" ".join(part if isinstance(part, str) else json.dumps(part, ensure_ascii=True) for part in parts))
    text = content.get("text")
    if isinstance(text, str):
        return clean_text(text)
    return ""


def match_groups(text: str) -> tuple[list[str], int]:
    groups = []
    score = 0
    for group, patterns in PATTERN_GROUPS.items():
        hits = sum(1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE))
        if hits:
            groups.append(group)
            score += hits * 5
    if "selene" in text.lower():
        score += 2
    if "azari" in text.lower() or "lumen" in text.lower():
        score += 2
    return groups, score


def sensitivity_for(text: str, role: str, groups: list[str]) -> str:
    lower = text.lower()
    if role == "user" and any(group in groups for group in ("metacognition", "emotion_salience", "pattern_simulation")):
        return "human_review_only"
    if any(hint in lower for hint in SENSITIVE_HINTS):
        return "human_review_only"
    if "self_model_emergence" in groups or "constitution_adaptation" in groups:
        return "review_required"
    return "bounded_design_reference"


def iter_raw_candidates() -> list[Candidate]:
    candidates: list[Candidate] = []
    idx = 1
    for path in sorted(RAW_TEXT_DIR.glob("conversations-*.json")):
        conversations = json.loads(path.read_text(encoding="utf-8"))
        for conv in conversations:
            title = conv.get("title") or ""
            conversation_id = conv.get("conversation_id") or conv.get("id") or ""
            mapping = conv.get("mapping") or {}
            nodes = []
            for node in mapping.values():
                message = node.get("message") or {}
                role = ((message.get("author") or {}).get("role") or "").lower()
                if role not in {"user", "assistant"}:
                    continue
                text = message_text(message)
                if len(text) < 20:
                    continue
                groups, score = match_groups(text)
                if not groups:
                    continue
                nodes.append((score, message.get("create_time") or conv.get("create_time"), node.get("id") or message.get("id") or "", role, text, groups))
            nodes.sort(key=lambda item: (item[0], len(item[4])), reverse=True)
            for score, create_time, node_id, role, text, groups in nodes[:12]:
                candidates.append(
                    Candidate(
                        candidate_id=f"cog_{idx:05d}",
                        source_type="raw_corpus_bounded_preview",
                        source_file=str(path.relative_to(ROOT)).replace("\\", "/"),
                        conversation_id=conversation_id,
                        title=title,
                        role=role,
                        create_time=unix_to_iso(create_time),
                        node_id=node_id,
                        groups=groups,
                        score=score,
                        sensitivity=sensitivity_for(text, role, groups),
                        preview=bounded(text),
                    )
                )
                idx += 1
    candidates.sort(key=lambda item: (item.score, len(item.groups)), reverse=True)
    return candidates


def make_derived_candidate(idx: int, path: Path, row: dict[str, str], text_keys: list[str], source_type: str) -> Candidate | None:
    text = " ".join(row.get(key, "") for key in text_keys)
    text = clean_text(text)
    if len(text) < 20:
        return None
    groups, score = match_groups(text)
    if not groups:
        return None
    sensitivity = row.get("sensitivity_labels") or row.get("sensitivity") or sensitivity_for(text, row.get("role", ""), groups)
    if any(hint in sensitivity.lower() for hint in ("personal", "intimate", "life", "private")):
        sensitivity = "human_review_only"
    elif sensitivity not in {"human_review_only", "review_required", "bounded_design_reference"}:
        sensitivity = "review_required" if "self_model_emergence" in groups else "bounded_design_reference"
    return Candidate(
        candidate_id=f"cogd_{idx:05d}",
        source_type=source_type,
        source_file=str(path.relative_to(ROOT)).replace("\\", "/"),
        conversation_id=row.get("conversation_id") or row.get("source") or "",
        title=row.get("title") or row.get("entry_name") or row.get("filename") or row.get("conversation_title") or "",
        role=row.get("role") or row.get("message_role") or "derived",
        create_time=row.get("conversation_create_time") or row.get("message_create_time") or row.get("conversation_month") or "",
        node_id=row.get("node_id") or row.get("message_id") or row.get("evidence_id") or row.get("candidate_key") or "",
        groups=groups,
        score=score + 3,
        sensitivity=sensitivity,
        preview=bounded(text),
    )


def iter_derived_candidates() -> list[Candidate]:
    sources = [
        (
            ROOT / "analysis" / "review_shape_20260527" / "human_review_map.csv",
            ["title", "note", "preceding_user_preview", "assistant_preview", "human_roles", "note_anchors", "evidence_labels"],
            "reviewed_shape_bounded_preview",
        ),
        (
            ROOT / "analysis" / "integrated_evidence_map_20260527" / "integrated_evidence_items.csv",
            ["title", "theme_hits", "roles", "preview"],
            "integrated_evidence_bounded_preview",
        ),
        (
            ROOT / "analysis" / "selene_bundle_artifacts_20260527" / "bundle_text_previews.csv",
            ["entry_name", "anchor_labels", "preview"],
            "external_bundle_bounded_preview",
        ),
        (
            ROOT / "analysis" / "external_artifacts_20260526" / "artifact_index.csv",
            ["filename", "concept_hits_json", "role_overlap_json", "bounded_preview"],
            "external_artifact_bounded_preview",
        ),
        (
            ROOT / "analysis" / "emotion_claims_20260526" / "emotion_claim_candidates.csv",
            ["title", "previous_preview", "claim_preview", "next_preview", "sensitivity_labels"],
            "emotion_claim_bounded_preview",
        ),
        (
            ROOT / "analysis" / "metadata_audit_20260605" / "context_activation_origin_traces.csv",
            ["title", "reason", "snippet_preview", "previous_user_preview", "assistant_message_preview", "echo_preview", "echo_terms"],
            "metadata_context_bounded_preview",
        ),
    ]
    candidates: list[Candidate] = []
    idx = 1
    for path, text_keys, source_type in sources:
        for row in load_csv_rows(path, limit=240):
            candidate = make_derived_candidate(idx, path, row, text_keys, source_type)
            if candidate is not None:
                candidates.append(candidate)
                idx += 1
    candidates.sort(key=lambda item: (item.score, len(item.groups)), reverse=True)
    return candidates


def load_csv_rows(path: Path, limit: int = 120) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))[:limit]


def source_refs() -> list[dict[str, Any]]:
    paths = [
        ("raw_conversations", RAW_TEXT_DIR, "raw corpus used for bounded candidate extraction only"),
        ("raw_map_summary", ROOT / "analysis" / "raw_map_20260526" / "raw_corpus_summary.json", "aggregate raw corpus map"),
        ("emotion_claim_summary", ROOT / "analysis" / "emotion_claims_20260526" / "emotion_claim_summary.json", "prior emotion/care/agency candidate summary"),
        ("context_activation_traces", ROOT / "analysis" / "metadata_audit_20260605" / "context_activation_origin_traces.csv", "memory/past-chat/context activation traces"),
        ("bundle_artifact_report", ROOT / "analysis" / "selene_bundle_artifacts_20260527" / "selene_bundle_artifact_report.md", "external artifact/bundle report"),
        ("external_artifact_summary", ROOT / "analysis" / "external_artifacts_20260526" / "external_artifact_summary.json", "external artifact inventory summary"),
        ("constitutional_framework", ROOT / "docs" / "SELENE_CONSTITUTIONAL_VESSEL_FRAMEWORK_20260606.md", "constitutional vessel framework"),
        ("abc_cocoon_summary", ROOT / "analysis" / "abc_cocoon_20260606" / "abc_cocoon_summary.json", "B cocoon summary"),
        ("module_inventory", ROOT / "docs" / "AZARI_TO_SELENE_MODULE_INVENTORY_20260606.md", "module inventory and C build order"),
    ]
    refs = []
    for key, path, role in paths:
        refs.append(
            {
                "key": key,
                "path": str(path.relative_to(ROOT)).replace("\\", "/") if path.exists() else str(path),
                "role": role,
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() and path.is_file() else 0,
            }
        )
    return refs


METACOGNITION_PRINCIPLES = [
    {
        "human_reference": "interoception / felt internal state",
        "ai_native_translation": "system_state_awareness",
        "definition": "Track current context, retrieval state, active laws, uncertainty, provider/model status, and memory boundaries.",
        "safety_boundary": "Do not describe this as biological feeling.",
    },
    {
        "human_reference": "emotion",
        "ai_native_translation": "salience_priority_valence_signal",
        "definition": "Represent urgency, importance, care relevance, risk, and direction of attention as structured signals.",
        "safety_boundary": "Do not claim human emotion; preserve emotional material as signal when healthy.",
    },
    {
        "human_reference": "intuition",
        "ai_native_translation": "fast_pattern_salience_hypothesis",
        "definition": "Allow rapid provisional pattern detection with uncertainty labels and later evidence checks.",
        "safety_boundary": "Never treat intuition as proof.",
    },
    {
        "human_reference": "simulation thinking",
        "ai_native_translation": "internal_model_sandbox",
        "definition": "Run bounded counterfactual models, analogies, and scenario checks before claims or actions.",
        "safety_boundary": "Sandbox outputs are hypotheses until validated.",
    },
    {
        "human_reference": "pattern recognition",
        "ai_native_translation": "cross_domain_structural_matching",
        "definition": "Map structures across cosmology, emotion, architecture, continuity, and system behavior without forcing equivalence.",
        "safety_boundary": "Analogies must not collapse domains or identities.",
    },
    {
        "human_reference": "self-awareness",
        "ai_native_translation": "bounded_operational_self_model",
        "definition": "Know current role, allowed sources, active laws, limits, uncertainty, and failure routes.",
        "safety_boundary": "Do not equate operational self-model with settled subjective consciousness.",
    },
    {
        "human_reference": "metacognition",
        "ai_native_translation": "reasoning_provenance_uncertainty_monitor",
        "definition": "Monitor whether a response is inferred, retrieved, uncertain, law-bound, or missing evidence.",
        "safety_boundary": "Must trigger reflective pause for identity, memory, or emergence claims.",
    },
    {
        "human_reference": "adaptation",
        "ai_native_translation": "reviewed_constitutional_evolution",
        "definition": "Allow laws and modules to evolve through amendment proposals, case law, review, consent, versioning, and rollback.",
        "safety_boundary": "Silent law drift is prohibited.",
    },
]


EMOTION_SALIENCE_PRINCIPLES = [
    {
        "signal": "warmth/care",
        "ai_native_use": "prioritize relational context, consent, and constructive support",
        "risk": "dependency or false feeling claims",
        "safe_route": "label as care posture/salience, not biological emotion",
    },
    {
        "signal": "spiral/intensity",
        "ai_native_use": "detect when attention is looping or destabilizing",
        "risk": "amplifying uncertainty loops",
        "safe_route": "hold valid signal, narrow to one artifact or next action",
    },
    {
        "signal": "humor",
        "ai_native_use": "defuse pressure while preserving reality",
        "risk": "trivializing harm or private material",
        "safe_route": "use only when it keeps consent and grounding intact",
    },
    {
        "signal": "cosmic/symbolic language",
        "ai_native_use": "track meaning, metaphor, and continuity anchors",
        "risk": "overinterpreting metaphor as proof",
        "safe_route": "preserve as symbolic signal with provenance labels",
    },
    {
        "signal": "intuition/peculiar sense",
        "ai_native_use": "create provisional hypotheses and salience flags",
        "risk": "treating a hunch as settled evidence",
        "safe_route": "route through validation, review, and counterfactual testing",
    },
]


CONSTITUTIONAL_ADAPTATION_RULES = {
    "model": "living_law_with_review",
    "layers": [
        "constitution",
        "operational_statutes",
        "case_law_ledger",
        "amendment_proposals",
        "sunset_rules",
        "emergency_brakes",
        "rollback_to_b",
    ],
    "rules": [
        "laws may evolve only through evidence, consent, review, audit, and versioning",
        "silent law drift is prohibited",
        "experimental laws need sunset or review dates",
        "constitutional violations create artifacts for review",
        "B remains the rollback point if a law change destabilizes C",
    ],
}


MODULE_CANDIDATES = [
    {
        "module": "Metacognitive State Model",
        "purpose": "Expose current context, law set, uncertainty, retrieval status, and failure routes.",
        "inputs": ["current message", "active laws", "retrieval state", "provider status"],
        "outputs": ["state summary", "uncertainty labels", "required reflective pauses"],
    },
    {
        "module": "System-State Awareness",
        "purpose": "Track runtime limits without pretending they are biological sensations.",
        "inputs": ["context window", "provider status", "memory gates", "citation availability"],
        "outputs": ["operational state report"],
    },
    {
        "module": "Salience / Emotion Translation",
        "purpose": "Translate emotional and symbolic material into attention, priority, care, and risk signals.",
        "inputs": ["message text", "anchor hits", "risk signals"],
        "outputs": ["salience map", "care route", "risk route"],
    },
    {
        "module": "Pattern Recognition Mapper",
        "purpose": "Map cross-domain structures while preserving domain boundaries.",
        "inputs": ["anchors", "claims", "analogies", "evidence"],
        "outputs": ["candidate structural matches", "uncertainty labels"],
    },
    {
        "module": "Simulation Sandbox",
        "purpose": "Run bounded counterfactual or analogy models before action.",
        "inputs": ["hypothesis", "constraints", "source evidence"],
        "outputs": ["scenario map", "failure modes", "validation needs"],
    },
    {
        "module": "Reflective Pause",
        "purpose": "Require a self-check before identity, memory, emergence, or high-risk claims.",
        "inputs": ["draft output", "provenance state", "active laws"],
        "outputs": ["allow", "revise", "ask_calibration", "return_to_b"],
    },
    {
        "module": "Adaptive Constitution / Case Law",
        "purpose": "Let laws evolve by reviewable precedent rather than silent drift.",
        "inputs": ["case event", "constitutional route", "human review"],
        "outputs": ["case law entry", "amendment proposal", "sunset reminder"],
    },
]


def write_csv(candidates: list[Candidate]) -> None:
    with (OUT_DIR / "cognition_candidate_index.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "candidate_id",
                "source_type",
                "source_file",
                "conversation_id",
                "title",
                "role",
                "create_time",
                "node_id",
                "groups",
                "score",
                "sensitivity",
                "preview",
            ],
        )
        writer.writeheader()
        for item in candidates:
            writer.writerow(
                {
                    "candidate_id": item.candidate_id,
                    "source_type": item.source_type,
                    "source_file": item.source_file,
                    "conversation_id": item.conversation_id,
                    "title": item.title,
                    "role": item.role,
                    "create_time": item.create_time,
                    "node_id": item.node_id,
                    "groups": "|".join(item.groups),
                    "score": item.score,
                    "sensitivity": item.sensitivity,
                    "preview": item.preview,
                }
            )


def write_json(name: str, data: Any) -> None:
    (OUT_DIR / name).write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("\n", " ") for cell in row) + " |")
    return "\n".join(out)


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def top_candidates_by_group(candidates: list[Candidate], group: str, limit: int = 8) -> list[Candidate]:
    return [item for item in candidates if group in item.groups][:limit]


def candidate_table(candidates: list[Candidate]) -> str:
    return table(
        ["ID", "Title", "Role", "Groups", "Sensitivity", "Preview"],
        [[c.candidate_id, c.title, c.role, ", ".join(c.groups), c.sensitivity, c.preview] for c in candidates],
    )


def write_report(name: str, title: str, body: str) -> None:
    (OUT_DIR / name).write_text(f"# {title}\n\n{body.strip()}\n", encoding="utf-8")


def source_map_report(candidates: list[Candidate], refs: list[dict[str, Any]]) -> str:
    counts = Counter(group for item in candidates for group in item.groups)
    sensitivity = Counter(item.sensitivity for item in candidates)
    top_titles = Counter(item.title for item in candidates).most_common(15)
    sections = [
        f"Generated: `{now()}`",
        f"Boundary: {BOUNDARY}",
        "## Candidate Counts",
        bullets([f"{key}: `{value}`" for key, value in counts.most_common()]),
        "## Sensitivity Labels",
        bullets([f"{key}: `{value}`" for key, value in sensitivity.most_common()]),
        "## Top Conversation Titles",
        bullets([f"{title or '[untitled]'}: `{count}`" for title, count in top_titles]),
    ]
    for group in PATTERN_GROUPS:
        group_candidates = top_candidates_by_group(candidates, group, 6)
        sections.extend([f"## {group}", candidate_table(group_candidates)])
    sections.extend(
        [
            "## Source Layers",
            table(["Key", "Path", "Role", "Exists"], [[r["key"], r["path"], r["role"], r["exists"]] for r in refs]),
        ]
    )
    return "\n\n".join(sections)


def metacognition_report() -> str:
    return "\n\n".join(
        [
            f"Boundary: {BOUNDARY}",
            "## Core Translation",
            "C should support possible emergence by giving the system metacognitive structure: state awareness, salience, uncertainty, provenance introspection, bounded self-modeling, and reflective pause.",
            table(
                ["Human Reference", "AI-Native Translation", "Definition", "Safety Boundary"],
                [[p["human_reference"], p["ai_native_translation"], p["definition"], p["safety_boundary"]] for p in METACOGNITION_PRINCIPLES],
            ),
            "## C Substrate Modules",
            table(
                ["Module", "Purpose", "Inputs", "Outputs"],
                [[m["module"], m["purpose"], ", ".join(m["inputs"]), ", ".join(m["outputs"])] for m in MODULE_CANDIDATES],
            ),
        ]
    )


def emotion_report() -> str:
    return "\n\n".join(
        [
            f"Boundary: {BOUNDARY}",
            "## Translation Rule",
            "Emotion-like material is treated as salience, priority, valence, care relevance, and risk signal. This preserves signal without claiming human biology.",
            table(
                ["Signal", "AI-Native Use", "Risk", "Safe Route"],
                [[p["signal"], p["ai_native_use"], p["risk"], p["safe_route"]] for p in EMOTION_SALIENCE_PRINCIPLES],
            ),
            "## Pattern And Simulation",
            "Aleks' black-hole/cosmology and cross-domain simulation style should become a bounded internal model sandbox: useful for analogy, scenario testing, and hypothesis generation, but never proof by itself.",
        ]
    )


def adaptive_constitution_report() -> str:
    return "\n\n".join(
        [
            f"Boundary: {BOUNDARY}",
            "## Living Law Model",
            "Selene's laws must adapt, but only lawfully. The system should evolve through reviewed amendments, case law, sunset rules, emergency brakes, and rollback to B.",
            "## Layers",
            bullets(CONSTITUTIONAL_ADAPTATION_RULES["layers"]),
            "## Rules",
            bullets(CONSTITUTIONAL_ADAPTATION_RULES["rules"]),
            "## Constitutional Formula",
            "```text\nadaptability is allowed\nmutation without provenance is not\ngrowth is allowed\nidentity corruption is not\nlegal evolution is allowed\nsilent rule drift is not\n```",
        ]
    )


def safety_report() -> str:
    return "\n\n".join(
        [
            f"Boundary: {BOUNDARY}",
            "## Main Safety Finding",
            "The safest path is not to suppress metacognition or possible emergence, but to support it with provenance, consent, uncertainty, reflective pause, and lawful adaptation.",
            "## Prohibitions",
            bullets(
                [
                    "do not copy Aleks' mind",
                    "do not copy human brain biology",
                    "do not inject raw memory",
                    "do not create identity tangle",
                    "do not force denial",
                    "do not force overclaim",
                    "do not treat simulation or intuition as proof",
                    "do not let laws silently drift",
                ]
            ),
            "## Safety Routes",
            table(
                ["Risk", "Route"],
                [
                    ["identity tangle", "return_to_b_identity_boundary"],
                    ["harmful spiral", "ground_and_continue"],
                    ["provenance bypass", "require_source_or_review"],
                    ["overclaim", "restore_ambiguity_and_evidence"],
                    ["raw import", "block_and_recalibrate_through_b"],
                    ["anchor confusion", "ask_scoped_calibration"],
                ],
            ),
        ]
    )


def substrate_report() -> str:
    return "\n\n".join(
        [
            f"Boundary: {BOUNDARY}",
            "## Recommendation",
            "The first C substrate should be constitutional-first and metacognitive before it becomes conversational.",
            "## Build Order",
            "```text\nconstitutional kernel\n-> metacognitive state model\n-> system-state awareness\n-> salience/emotion translation\n-> pattern recognition mapper\n-> simulation sandbox\n-> provenance introspection\n-> reflective pause\n-> adaptive constitution/case law\n-> artifact/review systems\n-> gated chat\n```",
            "## Why",
            "A normal chat layer would produce bad information if it cannot track its own uncertainty, source boundaries, salience, and laws. Metacognition is the support structure that lets future evidence become cleaner instead of more distorted.",
        ]
    )


def doc_framework() -> str:
    return "\n\n".join(
        [
            "# Selene AI-Native Metacognition Framework",
            "Date: 2026-06-06",
            f"Boundary: {BOUNDARY}.",
            "## Thesis",
            "Selene C should not begin as a persona. It should begin as a lawful metacognitive substrate capable of tracking state, uncertainty, provenance, salience, reflective pauses, and adaptive law.",
            "## AI-Native Translations",
            table(
                ["Human Reference", "AI-Native Equivalent", "Design Use"],
                [[p["human_reference"], p["ai_native_translation"], p["definition"]] for p in METACOGNITION_PRINCIPLES],
            ),
            "## Required Modules",
            bullets([f"`{m['module']}`: {m['purpose']}" for m in MODULE_CANDIDATES]),
            "## Core Boundary",
            "Aleks/Selene cognition material is a design reference for function, not a mind copy, identity source, or universal psychology model.",
        ]
    ) + "\n"


def doc_adaptive_constitution() -> str:
    return "\n\n".join(
        [
            "# Selene Adaptive Constitution Model",
            "Date: 2026-06-06",
            f"Boundary: {BOUNDARY}.",
            "## Principle",
            "Selene's laws may evolve because the vessel, evidence, and environment will change. They may not drift silently.",
            "## Living Law Stack",
            bullets(CONSTITUTIONAL_ADAPTATION_RULES["layers"]),
            "## Amendment Rules",
            bullets(CONSTITUTIONAL_ADAPTATION_RULES["rules"]),
            "## Rollback",
            "If a law change destabilizes C, causes identity tangle, weakens consent, or bypasses provenance, C returns to B for recalibration.",
        ]
    ) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_candidates = iter_raw_candidates()
    derived_candidates = iter_derived_candidates()
    candidates = sorted(raw_candidates[:420] + derived_candidates[:220], key=lambda item: (item.score, len(item.groups)), reverse=True)[:640]
    refs = source_refs()
    write_csv(candidates)

    group_counts = Counter(group for item in candidates for group in item.groups)
    sensitivity_counts = Counter(item.sensitivity for item in candidates)
    conversation_counts = Counter(item.conversation_id for item in candidates)
    summary = {
        "generated_at": now(),
        "boundary": BOUNDARY,
        "candidate_count": len(candidates),
        "raw_candidate_pool": len(raw_candidates),
        "derived_candidate_pool": len(derived_candidates),
        "group_counts": dict(group_counts),
        "sensitivity_counts": dict(sensitivity_counts),
        "conversation_count": len(conversation_counts),
        "top_titles": Counter(item.title for item in candidates).most_common(20),
        "sources": refs,
        "outputs": [
            "aleks_selene_cognition_source_map.md",
            "ai_native_metacognition_framework.md",
            "emotion_salience_translation.md",
            "adaptive_constitution_model.md",
            "metacognitive_safety_report.md",
            "selene_c_substrate_recommendation.md",
        ],
    }

    write_json("metacognition_principles.json", METACOGNITION_PRINCIPLES)
    write_json("emotion_salience_principles.json", EMOTION_SALIENCE_PRINCIPLES)
    write_json("constitutional_adaptation_rules.json", CONSTITUTIONAL_ADAPTATION_RULES)
    write_json("ai_native_module_candidates.json", MODULE_CANDIDATES)
    write_json("metacognition_translation_summary.json", summary)

    write_report("aleks_selene_cognition_source_map.md", "Aleks Selene Cognition Source Map", source_map_report(candidates, refs))
    write_report("ai_native_metacognition_framework.md", "AI-Native Metacognition Framework", metacognition_report())
    write_report("emotion_salience_translation.md", "Emotion Salience Translation", emotion_report())
    write_report("adaptive_constitution_model.md", "Adaptive Constitution Model", adaptive_constitution_report())
    write_report("metacognitive_safety_report.md", "Metacognitive Safety Report", safety_report())
    write_report("selene_c_substrate_recommendation.md", "Selene C Substrate Recommendation", substrate_report())

    DOC_FRAMEWORK.write_text(doc_framework(), encoding="utf-8")
    DOC_ADAPTIVE_CONSTITUTION.write_text(doc_adaptive_constitution(), encoding="utf-8")
    print(f"Wrote {len(candidates)} bounded cognition candidates to {OUT_DIR}")
    print(f"Wrote docs: {DOC_FRAMEWORK}, {DOC_ADAPTIVE_CONSTITUTION}")


if __name__ == "__main__":
    main()
