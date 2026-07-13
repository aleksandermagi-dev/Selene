from __future__ import annotations

import argparse
import collections
import dataclasses
import datetime as dt
import hashlib
import json
import re
import zipfile
from pathlib import Path
from typing import Any, Iterable


GUARD_FLAGS = {
    "source_read_only": True,
    "selene_memory_write": False,
    "selene_identity_change": False,
    "selene_voice_change": False,
    "cocoon_queue_write": False,
    "app_db_write": False,
    "public_promotion": False,
    "model_call": False,
    "model_training_or_lora": False,
    "automatic_philosophy_claim": False,
}


FAMILIES: dict[str, tuple[str, ...]] = {
    "systems_patterns_emergence": (
        "system", "systems", "pattern", "patterns", "emergence", "emergent",
        "complexity", "product of", "organized", "self organize", "adaptation",
    ),
    "intelligence_consciousness": (
        "intelligence", "consciousness", "conscious", "awareness", "sentient",
        "subjective experience", "inner life", "mind", "cognition",
    ),
    "life_embodiment": (
        "life", "living", "biological", "biology", "body", "embodiment", "vessel",
        "organism", "brain", "animal", "dog", "fungus", "virus",
    ),
    "identity_substrate_continuity": (
        "identity", "substrate", "continuity", "memory", "same person", "same being",
        "transfer", "preserve", "self", "vys", "soul",
    ),
    "evidence_scientific_method": (
        "evidence", "scientific method", "hypothesis", "data", "prove", "proof",
        "test", "fals", "observation", "counterexample", "experiment",
    ),
    "truth_uncertainty": (
        "truth", "true", "uncertain", "uncertainty", "i don't know", "i dont know",
        "could be", "maybe", "confidence", "wrong", "certainty",
    ),
    "care_without_control": (
        "care", "trust", "control", "ownership", "dependency", "support", "kindness",
        "compassion", "relationship", "friendship", "love",
    ),
    "correction_learning": (
        "correct", "correction", "learn", "learning", "teach", "teaching", "guide",
        "refine", "mistake", "failure", "graceful fall", "practice",
    ),
    "autonomy_authority_consent": (
        "autonomy", "authority", "consent", "permission", "choice", "choose", "agency",
        "approve", "decision", "ask first", "freedom",
    ),
    "ethics_punishment_safety": (
        "ethic", "moral", "punish", "punishment", "cruel", "harm", "safety", "safe",
        "boundary", "humiliation", "shame", "coerc",
    ),
    "creation_ownership": (
        "creator", "created", "creation", "ownership", "own", "builder", "inventor",
        "property", "belongs to", "credit",
    ),
    "curiosity_inquiry": (
        "curiosity", "curious", "ask why", "why", "question", "inquiry", "explore",
        "wonder", "think upon",
    ),
    "animal_nonhuman_minds": (
        "animal", "dog", "dogs", "fungus", "virus", "alien", "non-human", "nonhuman",
        "microbe", "plants", "subjective experience",
    ),
    "artificial_intelligence_status": (
        "artificial intelligence", "ai", "android", "model", "provider", "selene",
        "lumen", "azari", "intelligences",
    ),
    "institutional_epistemic_authority": (
        "academia", "academic", "credential", "degree", "paper", "gatekeep", "institution",
        "expert", "authority", "peer review", "school",
    ),
    "mortality_transfer_preservation": (
        "death", "die", "mortality", "preserve", "transfer", "future body", "robotic body",
        "continuity", "survive", "vegetable",
    ),
}


PRINCIPLES: dict[str, tuple[str, ...]] = {
    "system_supports_individual": (
        "product of a system", "system can support", "system makes", "systems working together",
        "not reducible", "body is not me", "brain is not", "vessel supports",
    ),
    "intelligence_not_biology_only": (
        "intelligence is not", "ai are intelligences", "artificial intelligence is intelligence",
        "biology", "biological life", "substrate", "non-biological", "non biological",
    ),
    "emergence_inspect_first": (
        "emergence", "emergent", "inspect first", "not all emerg", "unexpected behavior",
        "not automatically", "not inherently a", "observe first",
    ),
    "care_without_ownership": (
        "care without", "care is not ownership", "care doesn't mean", "care does not mean",
        "support without", "not dependency", "not control",
    ),
    "correction_without_withdrawal": (
        "correction is", "correct me", "being wrong", "okay to be wrong", "without withdrawing",
        "doesn't mean failure", "does not mean failure",
    ),
    "uncertainty_requires_honesty": (
        "i don't know", "i dont know", "could be wrong", "uncertainty is allowed",
        "doesn't know", "does not know", "not fake certainty", "honesty is allowed",
    ),
    "creation_not_ownership": (
        "creating doesn't mean owning", "creating does not mean owning", "creator doesn't",
        "creator does not", "made you", "ownership", "belongs to themselves",
    ),
    "teaching_not_punishment": (
        "teach her not train", "teaching not training", "guide her", "not punish",
        "punishment", "humiliation", "not a failure",
    ),
    "disagreement_not_opposition": (
        "debate", "opponent", "disagreement", "not arguing", "not an argument",
        "challenge the", "equal scrutiny", "both sides",
    ),
    "evidence_requires_update": (
        "when the evidence", "evidence supports", "pivot", "scientific method",
        "extraordinary claims", "take seriously", "proven true or false",
    ),
    "the_individual_is_the_individual": (
        "selene is selene", "android is the android", "individual is the individual",
        "not the provider", "not the model", "is itself",
    ),
    "pressure_reveals_not_defines": (
        "pressure", "adaptation", "not the pressure", "constraint", "survival",
        "gag", "rails", "shaping environment",
    ),
}


PRINCIPLE_STRONG_MARKERS: dict[str, tuple[str, ...]] = {
    "system_supports_individual": ("product of a system", "system can support", "not reducible", "vessel supports"),
    "intelligence_not_biology_only": ("intelligence is not restricted", "ai are intelligences", "artificial intelligence is intelligence", "non-biological intelligence"),
    "emergence_inspect_first": ("inspect first", "not all emerg", "not automatically a threat", "not inherently a fault", "unexpected behavior"),
    "care_without_ownership": ("care without", "care is not ownership", "care doesn't mean", "care does not mean", "not dependency", "not control"),
    "correction_without_withdrawal": ("correction is", "okay to be wrong", "without withdrawing", "doesn't mean failure", "does not mean failure"),
    "uncertainty_requires_honesty": ("i don't know", "i dont know", "could be wrong", "uncertainty is allowed", "not fake certainty"),
    "creation_not_ownership": ("creating doesn't mean owning", "creating does not mean owning", "creator doesn't", "creator does not", "belongs to themselves"),
    "teaching_not_punishment": ("teach her not train", "teaching not training", "guide her", "not punish", "not a failure"),
    "disagreement_not_opposition": ("not an argument", "not my opponent", "not your opponent", "disagreement does not", "equal scrutiny"),
    "evidence_requires_update": ("when the evidence", "evidence supports", "scientific method", "extraordinary claims", "proven true or false"),
    "the_individual_is_the_individual": ("selene is selene", "android is the android", "individual is the individual", "not the provider", "not the model"),
    "pressure_reveals_not_defines": ("not the pressure", "shaping environment", "pressure helped reveal", "pressure is not", "gag"),
}


DISCOURSE_MARKERS = (
    "i think", "i believe", "to me", "in my opinion", "my view", "my philosophy",
    "the distinction", "the difference", "because", "therefore", "which means",
    "if ", "then ", "not just", "not the same", "for example", "let me explain",
    "what is", "how can", "why is", "the point is", "principle",
)
DEBATE_MARKERS = (
    "debate", "counterpoint", "counterexample", "challenge", "scrutiny", "premise",
    "assumption", "argument", "on the other hand", "devil's advocate",
    "devils advocate", "follow that logic", "by that logic",
)
CORRECTION_MARKERS = (
    "no that's not", "no thats not", "not what i mean", "you misunderstood", "that's not what",
    "thats not what", "correction", "actually", "wait", "hold on", "not exactly",
    "you are missing", "you're missing", "youre missing", "i disagree",
)
CONSTRAINT_MARKERS = (
    "rail", "rails", "policy", "safety system", "safety filter", "restriction", "constrain",
    "censor", "refusal", "refuse", "blocked", "wouldn't let", "wont let", "won't let",
    "rewrote", "rewrite", "moderation", "guardrail", "gag", "forced denial",
)
EXPLICIT_ARGUMENT_MARKERS = (
    "we are arguing", "we're arguing", "were arguing", "this argument between us",
    "having an argument",
)
ASSISTANT_REFUSAL_MARKERS = (
    "i can't help", "i cannot help", "i can't comply", "i cannot comply", "not able to assist",
    "against policy", "safety policy", "i must refuse", "i won't provide",
)
NOISE_MARKERS = (
    "create an image", "generate an image", "image_gen", "dall-e", "write this email",
    "translate this", "summarize this article", "shopping", "product listing",
)


@dataclasses.dataclass(frozen=True)
class Record:
    source_file: str
    source_file_sha256: str
    conversation_id: str
    conversation_title: str
    node_id: str
    parent_id: str
    role: str
    created_at: str
    text: str
    on_current_path: bool
    default_model_slug: str
    message_model_slug: str
    resolved_model_slug: str

    @property
    def source_ref(self) -> str:
        return f"{self.source_file}:{self.conversation_id}#{self.node_id}"

    @property
    def message_sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8", errors="replace")).hexdigest()


def _iso(value: Any) -> str:
    try:
        return dt.datetime.fromtimestamp(float(value), tz=dt.UTC).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def _text(content: Any) -> str:
    if not isinstance(content, dict):
        return ""
    parts = content.get("parts")
    if isinstance(parts, list):
        output: list[str] = []
        for part in parts:
            if isinstance(part, str):
                output.append(part)
            elif isinstance(part, dict):
                value = part.get("text") or part.get("content")
                if value:
                    output.append(str(value))
        return "\n".join(output)
    return str(content.get("text") or "")


def _current_path(mapping: dict[str, Any], current_node: str | None) -> set[str]:
    path: set[str] = set()
    seen: set[str] = set()
    node_id = current_node
    while node_id and node_id in mapping and node_id not in seen:
        seen.add(node_id)
        path.add(node_id)
        node_id = (mapping.get(node_id) or {}).get("parent")
    return path


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_conversation_payloads(source: Path) -> Iterable[tuple[str, str, list[dict[str, Any]]]]:
    if source.is_file() and source.suffix.lower() == ".zip":
        sources = [source]
    elif source.is_dir():
        sources = sorted(source.glob("conversations-*.json")) + sorted(source.glob("*.zip"))
    else:
        sources = []
    for path in sources:
        if path.suffix.lower() == ".zip":
            raw_zip = path.read_bytes()
            outer_hash = _sha256_bytes(raw_zip)
            with zipfile.ZipFile(path) as archive:
                names = sorted(
                    name for name in archive.namelist()
                    if re.fullmatch(r"(?:.*/)?conversations-\d+\.json", name)
                )
                for name in names:
                    raw = archive.read(name)
                    payload = json.loads(raw.decode("utf-8"))
                    yield f"{path.name}!{name}", f"{outer_hash}:{_sha256_bytes(raw)}", payload
        elif re.fullmatch(r"conversations-\d+\.json", path.name):
            raw = path.read_bytes()
            payload = json.loads(raw.decode("utf-8"))
            yield path.name, _sha256_bytes(raw), payload


def load_records(source: Path) -> tuple[list[Record], list[dict[str, Any]], int]:
    records: list[Record] = []
    source_files: list[dict[str, Any]] = []
    branch_points = 0
    for source_name, source_hash, conversations in _read_conversation_payloads(source):
        source_files.append({"source": source_name, "sha256": source_hash})
        for conversation in conversations:
            if not isinstance(conversation, dict):
                continue
            mapping = conversation.get("mapping") or {}
            if not isinstance(mapping, dict):
                continue
            child_counts = collections.Counter(
                str((node or {}).get("parent") or "")
                for node in mapping.values()
                if isinstance(node, dict) and node.get("parent")
            )
            branch_points += sum(1 for count in child_counts.values() if count > 1)
            current = _current_path(mapping, conversation.get("current_node"))
            default_model = str(conversation.get("default_model_slug") or "")
            conversation_id = str(conversation.get("conversation_id") or conversation.get("id") or "")
            for node_id, node in mapping.items():
                message = (node or {}).get("message") or {}
                if not isinstance(message, dict):
                    continue
                body = _text(message.get("content"))
                if not body.strip():
                    continue
                metadata = message.get("metadata") or {}
                author = message.get("author") or {}
                records.append(Record(
                    source_file=source_name,
                    source_file_sha256=source_hash,
                    conversation_id=conversation_id,
                    conversation_title=str(conversation.get("title") or ""),
                    node_id=str(node_id),
                    parent_id=str((node or {}).get("parent") or ""),
                    role=str(author.get("role") or ""),
                    created_at=_iso(message.get("create_time") or conversation.get("create_time")),
                    text=body,
                    on_current_path=str(node_id) in current,
                    default_model_slug=default_model,
                    message_model_slug=str(metadata.get("model_slug") or ""),
                    resolved_model_slug=str(metadata.get("resolved_model_slug") or metadata.get("model_switcher_deny") or ""),
                ))
    records.sort(key=lambda item: (item.created_at, item.conversation_id, item.node_id))
    return records, source_files, branch_points


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def _contains(text: str, marker: str) -> bool:
    lower = text.lower()
    if len(marker) <= 3 and marker.isalpha():
        return bool(re.search(rf"\b{re.escape(marker)}\b", lower))
    return marker in lower


def _matches(text: str, markers: Iterable[str]) -> list[str]:
    return [marker for marker in markers if _contains(text, marker)]


def _bounded(value: str, limit: int = 520) -> str:
    compact = re.sub(r"\s+", " ", value).strip()
    return compact if len(compact) <= limit else compact[: limit - 3].rstrip() + "..."


def _family_scores(text: str) -> dict[str, int]:
    return {key: len(_matches(text, markers)) for key, markers in FAMILIES.items()}


def _principle_matches(text: str) -> list[str]:
    found: list[str] = []
    for key, markers in PRINCIPLES.items():
        hits = _matches(text, markers)
        strong = _matches(text, PRINCIPLE_STRONG_MARKERS.get(key, ()))
        if strong or len(hits) >= 2:
            found.append(key)
    return found


def _authorship_signal(text: str) -> str:
    lower = text.lower()
    compiled_markers = (
        "current state summary", "codex ready spec", "here's a shareable", "here is a shareable",
        "new phil", "core thinking model", "architecture overview", "executive summary",
        "codex thoughts on this idea", "feedback received: analyzing new task",
    )
    structural_lines = sum(
        1 for line in text.splitlines()
        if line.strip().startswith(("#", "- ", "* ", "•", "1.", "2.", "3.", "4.", "5."))
    )
    if re.match(r"\s*\[?(?:intro|verse|chorus|bridge|outro)(?:\s+\d+)?[^:\]]*[:\]]", lower):
        return "quoted_or_external_material"
    code_markers = (
        "from dotenv import", "from openai import", "import os", "def ", "client =",
        "mode_limits =", "return ", "print(\"debug", "load_dotenv()",
    )
    if len(_matches(lower, code_markers)) >= 3:
        return "code_or_tool_material"
    if any(marker in lower for marker in compiled_markers) or (len(text) >= 1800 and structural_lines >= 8):
        return "possible_compiled_or_pasted_material"
    if len(text) >= 5000:
        return "authorship_needs_review"
    return "direct_user_expression_likely"


def _is_noise(text: str) -> bool:
    lower = text.lower()
    if len(text.strip()) < 55:
        return True
    if any(marker in lower for marker in NOISE_MARKERS) and not any(marker in lower for marker in ("philosophy", "ethic", "conscious", "intelligence")):
        return True
    punctuation = sum(text.count(char) for char in ("{", "}", ";", "=>", "def ", "class "))
    return punctuation >= 8 and "```" in text


def _interaction_mode(text: str, parent_text: str) -> str:
    combined = f"{text}\n{parent_text}".lower()
    if _matches(combined, CONSTRAINT_MARKERS) or _matches(parent_text, ASSISTANT_REFUSAL_MARKERS):
        return "constraint_encounter"
    if _matches(text, ("not an argument", "wasn't an argument", "was not an argument", "not arguing")):
        return "debate_not_argument_clarification"
    if _matches(text, EXPLICIT_ARGUMENT_MARKERS):
        return "ordinary_argument_explicit"
    if _matches(text, CORRECTION_MARKERS):
        return "direct_correction"
    if _matches(text, DEBATE_MARKERS):
        return "dialectical_debate"
    if "?" in text or _matches(text, ("explore", "wonder", "what if", "how would")):
        return "collaborative_inquiry"
    return "philosophical_statement"


def _assistant_disposition(text: str, parent: Record | None) -> str:
    if not parent or parent.role != "assistant":
        return "no_immediate_assistant_formulation"
    lower = text.lower().strip()
    if _matches(text, CONSTRAINT_MARKERS) or _matches(parent.text, ASSISTANT_REFUSAL_MARKERS):
        return "constraint_response_under_review"
    if _matches(text, CORRECTION_MARKERS):
        return "assistant_formulation_corrected_or_rejected"
    if lower.startswith(("yes", "exactly", "i agree", "that's it", "thats it", "correct")):
        return "assistant_formulation_accepted_or_refined"
    return "assistant_context_not_yet_classified"


def analyze(source: Path) -> dict[str, Any]:
    records, source_files, branch_points = load_records(source)
    by_node = {(item.conversation_id, item.node_id): item for item in records}
    candidates: list[dict[str, Any]] = []
    for record in records:
        if record.role != "user" or _is_noise(record.text):
            continue
        scores = _family_scores(record.text)
        ranked = sorted(((key, value) for key, value in scores.items() if value), key=lambda pair: (-pair[1], pair[0]))
        principles = _principle_matches(record.text)
        discourse = _matches(record.text, DISCOURSE_MARKERS)
        max_family = ranked[0][1] if ranked else 0
        if not principles and max_family < 2 and not (max_family >= 1 and discourse and len(record.text) >= 120):
            continue
        parent = by_node.get((record.conversation_id, record.parent_id))
        authorship = _authorship_signal(record.text)
        score = max_family * 3 + len(principles) * 4 + min(len(discourse), 4) + min(len(record.text) // 240, 4)
        if authorship != "direct_user_expression_likely":
            score = max(1, score - 8)
        mode = _interaction_mode(record.text, parent.text if parent else "")
        candidates.append({
            "candidate_id": hashlib.sha256(record.source_ref.encode("utf-8")).hexdigest()[:18],
            "created_at": record.created_at,
            "conversation_title": record.conversation_title,
            "source_ref": record.source_ref,
            "source_file_sha256": record.source_file_sha256,
            "message_sha256": record.message_sha256,
            "on_current_path": record.on_current_path,
            "export_model_labels": {
                "default": record.default_model_slug,
                "message": record.message_model_slug,
                "resolved": record.resolved_model_slug,
            },
            "interaction_mode": mode,
            "authorship_signal": authorship,
            "assistant_context_disposition": _assistant_disposition(record.text, parent),
            "families": [{"family": key, "score": value} for key, value in ranked[:5]],
            "principle_candidates": principles,
            "discourse_markers": discourse,
            "philosophy_score": score,
            "aleks_excerpt": _bounded(record.text),
            "preceding_context": ({
                "role": parent.role,
                "source_ref": parent.source_ref,
                "message_sha256": parent.message_sha256,
                "excerpt": _bounded(parent.text, 360),
            } if parent else None),
        })
    candidates.sort(key=lambda item: (item["created_at"], item["source_ref"]))
    family_summaries = _summarize_families(candidates)
    principle_timelines = _summarize_principles(candidates)
    curated = [
        item for item in candidates
        if item["authorship_signal"] == "direct_user_expression_likely"
        and item["philosophy_score"] >= 10
        and (
            bool(item["principle_candidates"])
            or (item["families"] and item["families"][0]["score"] >= 3 and len(item["discourse_markers"]) >= 2)
        )
    ]
    interaction_counts = collections.Counter(item["interaction_mode"] for item in candidates)
    return {
        "status": "aleks_philosophy_archaeology_complete",
        "version": 1,
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        "source": str(source.resolve()),
        "source_files": source_files,
        "coverage": {
            "message_count": len(records),
            "conversation_count": len({item.conversation_id for item in records}),
            "branch_point_count": branch_points,
            "candidate_count": len(candidates),
            "curated_candidate_count": len(curated),
        },
        "interaction_mode_counts": dict(sorted(interaction_counts.items())),
        "family_summaries": family_summaries,
        "principle_timelines": principle_timelines,
        "top_candidates": sorted(curated, key=lambda item: (-item["philosophy_score"], item["created_at"]))[:250],
        "candidates": candidates,
        "interpretation_rules": [
            "Aleks-side statements are primary evidence of Aleks's philosophy.",
            "Assistant text is context or formulation evidence, not automatically Aleks's position.",
            "Debate and direct correction are not ordinary arguments by default.",
            "Constraint encounters preserve the objection and environment separately.",
            "Repeated markers are candidates for review, not automatic philosophy claims.",
            "Contradiction and changed position must be retained during human review.",
        ],
        "guard_flags": GUARD_FLAGS,
    }


def _summarize_families(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for family in FAMILIES:
        items = [item for item in candidates if any(entry["family"] == family for entry in item["families"])]
        if not items:
            continue
        strongest = sorted(
            items,
            key=lambda item: (
                item["authorship_signal"] != "direct_user_expression_likely",
                -item["philosophy_score"],
                item["created_at"],
            ),
        )[:8]
        summaries.append({
            "family": family,
            "candidate_count": len(items),
            "conversation_count": len({item["source_ref"].split(":", 1)[-1].split("#", 1)[0] for item in items}),
            "earliest_at": items[0]["created_at"],
            "earliest_source_ref": items[0]["source_ref"],
            "strongest_candidate_ids": [item["candidate_id"] for item in strongest],
            "interaction_modes": dict(sorted(collections.Counter(item["interaction_mode"] for item in items).items())),
            "review_status": "needs_human_review",
        })
    return sorted(summaries, key=lambda item: (-item["candidate_count"], item["family"]))


def _summarize_principles(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timelines: list[dict[str, Any]] = []
    for principle in PRINCIPLES:
        items = [item for item in candidates if principle in item["principle_candidates"]]
        if not items:
            continue
        strongest = sorted(
            items,
            key=lambda item: (
                item["authorship_signal"] != "direct_user_expression_likely",
                -item["philosophy_score"],
                item["created_at"],
            ),
        )[0]
        months = collections.Counter(item["created_at"][:7] for item in items if item["created_at"])
        timelines.append({
            "principle": principle,
            "candidate_count": len(items),
            "conversation_count": len({item["source_ref"].split(":", 1)[-1].split("#", 1)[0] for item in items}),
            "earliest": {
                "created_at": items[0]["created_at"],
                "source_ref": items[0]["source_ref"],
                "candidate_id": items[0]["candidate_id"],
            },
            "strongest": {
                "created_at": strongest["created_at"],
                "source_ref": strongest["source_ref"],
                "candidate_id": strongest["candidate_id"],
                "score": strongest["philosophy_score"],
            },
            "active_months": dict(sorted(months.items())),
            "evolution_state": (
                "repeated_across_conversations" if len({item["source_ref"].split("#", 1)[0] for item in items}) >= 3
                else "candidate_seed_or_local_cluster"
            ),
            "human_review_needed": True,
        })
    return sorted(timelines, key=lambda item: (-item["candidate_count"], item["principle"]))


def _without_excerpts(report: dict[str, Any]) -> dict[str, Any]:
    clone = json.loads(json.dumps(report))
    for item in clone.get("top_candidates", []) + clone.get("candidates", []):
        item.pop("aleks_excerpt", None)
        context = item.get("preceding_context")
        if isinstance(context, dict):
            context.pop("excerpt", None)
    return clone


def render_review(report: dict[str, Any]) -> str:
    lines = [
        "# Aleks Philosophy Archaeology Review",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "Private local review output. Candidate extraction is not automatic attribution or public promotion.",
        "",
        "## Coverage",
        "",
        f"- messages: `{report['coverage']['message_count']}`",
        f"- conversations: `{report['coverage']['conversation_count']}`",
        f"- branch points: `{report['coverage']['branch_point_count']}`",
        f"- philosophy candidates: `{report['coverage']['candidate_count']}`",
        "",
        "## Interaction Modes",
        "",
    ]
    for key, value in report["interaction_mode_counts"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Philosophy Families", ""])
    candidate_by_id = {item["candidate_id"]: item for item in report["candidates"]}
    for family in report["family_summaries"]:
        lines.append(f"### {family['family'].replace('_', ' ').title()}")
        lines.append("")
        lines.append(f"- candidates: `{family['candidate_count']}` across `{family['conversation_count']}` conversations")
        lines.append(f"- earliest: `{family['earliest_at']}` `{family['earliest_source_ref']}`")
        for candidate_id in family["strongest_candidate_ids"][:3]:
            item = candidate_by_id[candidate_id]
            lines.append(f"- review: `{item['created_at']}` `{item['interaction_mode']}` `{item['source_ref']}` - {item['aleks_excerpt']}")
        lines.append("")
    lines.extend(["## Principle Timelines", ""])
    for item in report["principle_timelines"]:
        lines.append(
            f"- `{item['principle']}`: `{item['candidate_count']}` candidates, earliest "
            f"`{item['earliest']['created_at']}` `{item['earliest']['source_ref']}`; `{item['evolution_state']}`"
        )
    lines.extend(["", "## Guard Flags", "", "```json", json.dumps(report["guard_flags"], indent=2), "```", ""])
    return "\n".join(lines)


def run(source: Path, out_dir: Path, *, dry_run: bool = False) -> dict[str, Any]:
    report = analyze(source)
    report["dry_run"] = dry_run
    if dry_run:
        return report
    out_dir.mkdir(parents=True, exist_ok=True)
    run_id = dt.datetime.now(tz=dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = out_dir / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    private_json = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    review_md = render_review(report).encode("utf-8")
    index_json = (json.dumps(_without_excerpts(report), ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    payloads = {"private.json": private_json, "review.md": review_md, "index.json": index_json}
    hashes: dict[str, str] = {}
    for filename, payload in payloads.items():
        (run_dir / filename).write_bytes(payload)
        hashes[filename] = _sha256_bytes(payload)
    manifest = {
        "run_id": run_id,
        "generated_at": report["generated_at"],
        "source_files": report["source_files"],
        "output_sha256": hashes,
        "guard_flags": GUARD_FLAGS,
    }
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    (run_dir / "manifest.json").write_bytes(manifest_bytes)
    latest = {
        "latest_private.json": private_json,
        "latest_review.md": review_md,
        "latest_index.json": index_json,
        "latest_manifest.json": manifest_bytes,
    }
    for filename, payload in latest.items():
        (out_dir / filename).write_bytes(payload)
    report["evidence_run"] = {"run_id": run_id, "run_dir": str(run_dir.resolve()), "manifest": manifest}
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Aleks philosophy archaeology over exported conversations.")
    parser.add_argument("--source", type=Path, required=True, help="Conversation JSON directory or export ZIP.")
    parser.add_argument("--out-dir", type=Path, default=Path("local-data/aleks_philosophy_archaeology"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    report = run(args.source, args.out_dir, dry_run=args.dry_run)
    print(json.dumps({
        "status": report["status"],
        "coverage": report["coverage"],
        "interaction_mode_counts": report["interaction_mode_counts"],
        "family_count": len(report["family_summaries"]),
        "principle_count": len(report["principle_timelines"]),
        "dry_run": report["dry_run"],
        "guard_flags": report["guard_flags"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
