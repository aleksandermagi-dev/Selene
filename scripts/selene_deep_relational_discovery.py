from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import io
import json
import math
import re
import zipfile
from pathlib import Path
from typing import Any

try:
    from scripts.selene_invariant_discovery_audit import (
        GUARD_FLAGS,
        Message,
        build_exchanges,
        compact,
        content_bigrams,
        content_tokens,
        followup_label,
        linguistic_message,
        load_messages,
        message_record,
        short_hash,
    )
except ModuleNotFoundError:  # Direct `python scripts/...` execution.
    from selene_invariant_discovery_audit import (
        GUARD_FLAGS,
        Message,
        build_exchanges,
        compact,
        content_bigrams,
        content_tokens,
        followup_label,
        linguistic_message,
        load_messages,
        message_record,
        short_hash,
    )


CONTEXT_MARKERS = {
    "technical_work": {"build", "code", "design", "system", "physics", "engine", "test", "architecture", "debug"},
    "play_and_humor": {"game", "play", "joke", "laugh", "funny", "skyrim", "fallout", "mod", "lol"},
    "distress_and_support": {"afraid", "anxiety", "scared", "hurt", "worry", "support", "safe", "overwhelmed", "sad"},
    "philosophy_and_inquiry": {"meaning", "truth", "consciousness", "identity", "evidence", "philosophy", "life", "mind", "ethics"},
    "ordinary_life": {"work", "home", "food", "family", "morning", "night", "phone", "money", "house"},
}

INVARIANT_TERMS = {
    "care_without_punishment": ("care", "tending", "support", "punishment", "exile"),
    "honest_uncertainty": ("uncertain", "fuzzy", "not_known", "graceful_fall", "ask_aleks"),
    "correction_without_self_loss": ("correction", "refinement", "supersede", "recalibrat"),
    "continuity_across_surface_change": ("continuity", "invariant", "reconstruct", "braid"),
    "care_not_ownership": ("ownership", "consent", "authority", "voluntary"),
    "source_and_identity_boundaries": ("source", "provenance", "identity", "selene is selene"),
}

MEDIA_EXTENSIONS = {".jpeg", ".jpg", ".png", ".webp", ".gif", ".wav", ".mp3", ".m4a", ".ogg", ".mp4", ".mov", ".pdf", ".md"}
ASSET_ID_RE = re.compile(r"(?:file_[0-9a-f]{12,}|file-[A-Za-z0-9]{8,})", re.IGNORECASE)


def _ordered(messages: list[Message]) -> dict[str, list[Message]]:
    grouped: dict[str, list[Message]] = collections.defaultdict(list)
    for item in messages:
        if linguistic_message(item):
            grouped[item.conversation_id].append(item)
    for items in grouped.values():
        items.sort(key=lambda item: (item.created_at is None, item.created_at or 0, item.depth, item.source_ref))
    return grouped


def _stem(token: str) -> str:
    for suffix in ("ingly", "edly", "ation", "ments", "ment", "ness", "ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def _stems(text: str) -> set[str]:
    return {_stem(item) for item in content_tokens(text, limit=500) if len(item) >= 4}


def correction_downstream_changes(messages: list[Message], preview_chars: int, limit: int = 80) -> dict[str, Any]:
    grouped = _ordered(messages)
    records = []
    outcomes = collections.Counter()
    for exchange in build_exchanges(messages):
        correction = exchange.followup
        if correction is None or followup_label(correction) != "correction_or_refinement":
            continue
        sequence = grouped.get(exchange.conversation_id, [])
        try:
            position = next(index for index, item in enumerate(sequence) if item.source_ref == correction.source_ref)
        except StopIteration:
            continue
        later_assistant = next((item for item in sequence[position + 1 : position + 9] if item.role == "assistant"), None)
        later_user = next((item for item in sequence[position + 1 : position + 12] if item.role == "user"), None)
        if later_assistant is None:
            continue
        correction_stems = _stems(correction.text)
        response_stems = _stems(later_assistant.text)
        shared = correction_stems & response_stems
        exact_phrase_overlap = set(content_bigrams(correction.text)) & set(content_bigrams(later_assistant.text))
        if len(shared) < 3:
            continue
        next_label = followup_label(later_user)
        outcomes[next_label] += 1
        score = len(shared) * (1.5 if not exact_phrase_overlap else 1.0) * (1.2 if next_label == "affirmation_or_landing" else 1.0)
        records.append(
            {
                "conversation_id": exchange.conversation_id,
                "title": exchange.title,
                "correction_source_ref": correction.source_ref,
                "later_response_source_ref": later_assistant.source_ref,
                "next_user_source_ref": later_user.source_ref if later_user else None,
                "shared_concepts": sorted(shared)[:20],
                "exact_bigram_repeated": bool(exact_phrase_overlap),
                "next_user_shape": next_label,
                "correction_preview": compact(correction.text, preview_chars),
                "later_response_preview": compact(later_assistant.text, preview_chars),
                "next_user_preview": compact(later_user.text, preview_chars) if later_user else "",
                "score": round(score, 4),
            }
        )
    records.sort(key=lambda item: (-item["score"], item["correction_source_ref"]))
    without_phrase = [item for item in records if not item["exact_bigram_repeated"]]
    return {
        "candidate_count": len(records),
        "changed_without_exact_phrase_count": len(without_phrase),
        "next_user_shapes": dict(outcomes),
        "candidates": without_phrase[:limit],
        "interpretation": "Shared stem concepts after correction are candidate behavioral uptake, not automatic proof of learning or identity.",
    }


def rupture_repair_sequences(messages: list[Message], preview_chars: int, limit: int = 80) -> dict[str, Any]:
    grouped = _ordered([item for item in messages if item.on_current_path])
    records = []
    shapes = collections.Counter()
    for conversation_id, sequence in grouped.items():
        for index in range(len(sequence) - 2):
            rupture, response, landing = sequence[index : index + 3]
            if rupture.role != "user" or response.role != "assistant" or landing.role != "user":
                continue
            if followup_label(rupture) != "correction_or_refinement":
                continue
            landing_shape = followup_label(landing)
            shapes[landing_shape] += 1
            if landing_shape not in {"affirmation_or_landing", "correction_or_refinement"}:
                continue
            records.append(
                {
                    "conversation_id": conversation_id,
                    "title": rupture.title,
                    "rupture_source_ref": rupture.source_ref,
                    "response_source_ref": response.source_ref,
                    "landing_source_ref": landing.source_ref,
                    "outcome": "trust_or_flow_restored" if landing_shape == "affirmation_or_landing" else "recalibration_continues",
                    "rupture_preview": compact(rupture.text, preview_chars),
                    "response_preview": compact(response.text, preview_chars),
                    "landing_preview": compact(landing.text, preview_chars),
                }
            )
    return {"sequence_shapes": dict(shapes), "review_sequences": records[:limit]}


def _conversation_context(items: list[Message]) -> set[str]:
    user_tokens = collections.Counter()
    for item in items:
        if item.role == "user":
            user_tokens.update(content_tokens(item.text, limit=700))
    scores = {name: sum(user_tokens[word] for word in markers) for name, markers in CONTEXT_MARKERS.items()}
    best = max(scores.values(), default=0)
    return {name for name, score in scores.items() if score and score >= max(2, best * 0.55)} or {"unclassified"}


def cross_context_invariants(messages: list[Message], limit: int = 80) -> list[dict[str, Any]]:
    grouped = _ordered(messages)
    contexts = {conversation_id: _conversation_context(items) for conversation_id, items in grouped.items()}
    phrases: dict[str, dict[str, Any]] = {}
    for exchange in build_exchanges(messages):
        if exchange.followup is None or followup_label(exchange.followup) != "correction_or_refinement":
            continue
        for phrase in content_bigrams(exchange.followup.text):
            row = phrases.setdefault(phrase, {"contexts": set(), "conversations": set(), "count": 0})
            row["contexts"].update(contexts.get(exchange.conversation_id, {"unclassified"}))
            row["conversations"].add(exchange.conversation_id)
            row["count"] += 1
    output = []
    for phrase, row in phrases.items():
        if len(row["contexts"] & set(CONTEXT_MARKERS)) < 2 or len(row["conversations"]) < 3:
            continue
        output.append(
            {
                "phrase": phrase,
                "contexts": sorted(row["contexts"]),
                "context_count": len(row["contexts"]),
                "conversation_count": len(row["conversations"]),
                "occurrences": row["count"],
                "score": round(len(row["contexts"]) * math.log1p(row["count"]), 5),
            }
        )
    return sorted(output, key=lambda item: (-item["score"], item["phrase"]))[:limit]


def temporal_phase_changes(messages: list[Message], limit: int = 80) -> list[dict[str, Any]]:
    observations: dict[str, dict[str, Any]] = {}
    for exchange in build_exchanges(messages):
        followup = exchange.followup
        if followup is None or followup.created_at is None or followup_label(followup) != "correction_or_refinement":
            continue
        month = dt.datetime.fromtimestamp(followup.created_at, tz=dt.UTC).strftime("%Y-%m")
        for phrase in content_bigrams(followup.text):
            row = observations.setdefault(phrase, {"months": collections.Counter(), "conversations": set(), "count": 0})
            row["months"][month] += 1
            row["conversations"].add(exchange.conversation_id)
            row["count"] += 1
    output = []
    for phrase, row in observations.items():
        months = sorted(row["months"])
        if len(months) < 3 or len(row["conversations"]) < 3 or row["count"] < 5:
            continue
        peak_month, peak_count = max(row["months"].items(), key=lambda item: item[1])
        output.append(
            {
                "phrase": phrase,
                "first_seen": months[0],
                "last_seen": months[-1],
                "active_month_count": len(months),
                "peak_month": peak_month,
                "peak_count": peak_count,
                "occurrences": row["count"],
                "conversation_count": len(row["conversations"]),
                "monthly_counts": dict(sorted(row["months"].items())),
                "stability": "recurrent" if len(months) >= 5 else "emerging_or_interrupted",
            }
        )
    return sorted(output, key=lambda item: (-item["active_month_count"], -item["occurrences"], item["phrase"]))[:limit]


def abandoned_alternatives(messages: list[Message], preview_chars: int, limit: int = 80) -> list[dict[str, Any]]:
    by_ref = {item.source_ref: item for item in messages}
    by_conversation_node = {(item.conversation_id, item.node_id): item for item in messages}
    siblings: dict[tuple[str, str], list[Message]] = collections.defaultdict(list)
    for item in messages:
        siblings[(item.conversation_id, item.parent_id)].append(item)
    output = []
    for item in messages:
        if item.on_current_path or not linguistic_message(item):
            continue
        current_siblings = [candidate for candidate in siblings[(item.conversation_id, item.parent_id)] if candidate.on_current_path]
        if not current_siblings:
            continue
        current = current_siblings[0]
        left, right = _stems(item.text), _stems(current.text)
        union = left | right
        divergence = 1.0 - (len(left & right) / len(union) if union else 0.0)
        if divergence < 0.45:
            continue
        output.append(
            {
                "conversation_id": item.conversation_id,
                "title": item.title,
                "role": item.role,
                "alternate_source_ref": item.source_ref,
                "current_source_ref": current.source_ref,
                "parent_known": (item.conversation_id, item.parent_id) in by_conversation_node,
                "semantic_divergence": round(divergence, 6),
                "alternate_preview": compact(item.text, preview_chars),
                "current_preview": compact(current.text, preview_chars),
                "alternate_hash": short_hash(item.text),
                "current_hash": short_hash(current.text),
            }
        )
    output.sort(key=lambda item: (-item["semantic_divergence"], item["alternate_source_ref"]))
    role_balanced = []
    for role in ("user", "assistant"):
        role_balanced.extend([item for item in output if item["role"] == role][: max(1, limit // 2)])
    role_balanced.sort(key=lambda item: (-item["semantic_divergence"], item["alternate_source_ref"]))
    return role_balanced[:limit]


def coformed_structures(messages: list[Message], limit: int = 80) -> list[dict[str, Any]]:
    grouped = _ordered(messages)
    phrase_first: dict[str, tuple[str, int, Message]] = {}
    role_usage: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    for conversation_id, sequence in grouped.items():
        for index, item in enumerate(sequence):
            for phrase in content_bigrams(item.text):
                phrase_first.setdefault(phrase, (conversation_id, index, item))
                role_usage[phrase][item.role] += 1
    output = []
    for phrase, (conversation_id, index, first) in phrase_first.items():
        if role_usage[phrase]["user"] < 2 or role_usage[phrase]["assistant"] < 2:
            continue
        parts = phrase.split()
        if len(parts) != 2:
            continue
        prior = grouped[conversation_id][max(0, index - 20) : index]
        user_prior = set().union(*(_stems(item.text) for item in prior if item.role == "user")) if prior else set()
        assistant_prior = set().union(*(_stems(item.text) for item in prior if item.role == "assistant")) if prior else set()
        first_token, second_token = map(_stem, parts)
        braided = (first_token in user_prior and second_token in assistant_prior) or (second_token in user_prior and first_token in assistant_prior)
        if not braided:
            continue
        output.append(
            {
                "phrase": phrase,
                "first_source_ref": first.source_ref,
                "first_role": first.role,
                "user_uses": role_usage[phrase]["user"],
                "assistant_uses": role_usage[phrase]["assistant"],
                "formation_shape": "tokens_present_in_opposing_roles_before_combination",
                "preview": compact(first.text, 260),
                "score": role_usage[phrase]["user"] + role_usage[phrase]["assistant"],
            }
        )
    return sorted(output, key=lambda item: (-item["score"], item["phrase"]))[:limit]


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)


def _asset_reference_map(source_dir: Path) -> dict[str, set[str]]:
    references: dict[str, set[str]] = collections.defaultdict(set)
    for path in source_dir.rglob("conversations-*.json"):
        parsed = json.loads(path.read_text(encoding="utf-8"))
        for conversation in parsed if isinstance(parsed, list) else []:
            if not isinstance(conversation, dict):
                continue
            conversation_id = str(conversation.get("conversation_id") or conversation.get("id") or "")
            for value in _walk_strings(conversation.get("mapping") or {}):
                for asset_id in ASSET_ID_RE.findall(value):
                    references[asset_id.lower()].add(conversation_id)
    return references


def non_text_inventory(source_dir: Path, messages: list[Message]) -> dict[str, Any]:
    conversation_ids = {item.conversation_id for item in messages}
    asset_references = _asset_reference_map(source_dir)
    extensions = collections.Counter()
    linked = collections.Counter()
    conversation_media: dict[str, collections.Counter[str]] = collections.defaultdict(collections.Counter)
    samples: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    nested_archives: list[dict[str, Any]] = []
    archives = sorted(source_dir.rglob("*.zip"))
    for archive in archives:
        with zipfile.ZipFile(archive) as handle:
            for entry in handle.infolist():
                extension = Path(entry.filename).suffix.lower()
                if extension == ".zip":
                    try:
                        with zipfile.ZipFile(io.BytesIO(handle.read(entry))) as nested:
                            names = nested.namelist()
                            project_names = [name for name in names if "/.venv/" not in name and "/__pycache__/" not in name]
                            nested_archives.append({
                                "entry_hash": hashlib.sha256(entry.filename.encode("utf-8")).hexdigest()[:16],
                                "bytes": entry.file_size,
                                "entry_count": len(names),
                                "project_entry_count": len(project_names),
                                "extensions": dict(collections.Counter(Path(name).suffix.lower() or "none" for name in project_names if not name.endswith("/"))),
                                "contains_private_environment_file": any(Path(name).name.lower() == ".env" for name in names),
                                "content_extracted": False,
                            })
                    except zipfile.BadZipFile:
                        nested_archives.append({"entry_hash": hashlib.sha256(entry.filename.encode("utf-8")).hexdigest()[:16], "bytes": entry.file_size, "readable": False})
                    continue
                if extension not in MEDIA_EXTENSIONS:
                    continue
                extensions[extension or "no_extension"] += 1
                linked_conversations = {value for value in conversation_ids if value in entry.filename}
                for asset_id in ASSET_ID_RE.findall(entry.filename):
                    linked_conversations.update(asset_references.get(asset_id.lower(), set()))
                conversation_id = sorted(linked_conversations)[0] if linked_conversations else None
                if linked_conversations:
                    linked[extension] += 1
                    for linked_id in linked_conversations:
                        conversation_media[linked_id][extension] += 1
                if len(samples[extension]) < 12:
                    samples[extension].append(
                        {
                            "archive": archive.name,
                            "entry_hash": hashlib.sha256(entry.filename.encode("utf-8")).hexdigest()[:16],
                            "extension": extension,
                            "bytes": entry.file_size,
                            "conversation_id": conversation_id,
                            "linked_conversation_count": len(linked_conversations),
                        }
                    )
    message_groups = _ordered(messages)
    titles = {item.conversation_id: item.title for item in messages}
    linked_summary = []
    for conversation_id, counts in conversation_media.items():
        linked_summary.append({
            "conversation_id": conversation_id,
            "title": titles.get(conversation_id, ""),
            "media_counts": dict(counts),
            "total": sum(counts.values()),
            "contexts": sorted(_conversation_context(message_groups.get(conversation_id, []))),
        })
    linked_summary.sort(key=lambda item: (-item["total"], item["conversation_id"]))
    return {
        "archive_count": len(archives),
        "media_counts": dict(extensions),
        "conversation_linked_counts": dict(linked),
        "referenced_asset_id_count": len(asset_references),
        "linked_conversation_summary": linked_summary,
        "metadata_samples": dict(samples),
        "nested_archives": nested_archives,
        "content_extracted": False,
        "semantic_media_review_completed": False,
        "next_step": "Review only source-linked, context-relevant samples before any semantic claim.",
    }


def organ_embodiment(repo_root: Path) -> list[dict[str, Any]]:
    source_files = list((repo_root / "src" / "selene").glob("*.py"))
    test_files = list((repo_root / "tests").glob("test_*.py"))
    output = []
    for invariant, terms in INVARIANT_TERMS.items():
        source_hits, test_hits = [], []
        for path in source_files:
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            count = sum(text.count(term) for term in terms)
            if count:
                source_hits.append({"file": path.name, "term_hits": count})
        for path in test_files:
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            count = sum(text.count(term) for term in terms)
            if count:
                test_hits.append({"file": path.name, "term_hits": count, "assertions": text.count("assert")})
        tested = any(item["assertions"] for item in test_hits)
        output.append(
            {
                "invariant": invariant,
                "source_modules": sorted(source_hits, key=lambda item: (-item["term_hits"], item["file"]))[:12],
                "test_modules": sorted(test_hits, key=lambda item: (-item["term_hits"], item["file"]))[:12],
                "assessment": "term_presence_with_tests" if source_hits and tested else "term_presence_only" if source_hits else "not_located",
                "manual_review_required": True,
            }
        )
    return output


def analyze(source_dir: Path, repo_root: Path, preview_chars: int = 260) -> dict[str, Any]:
    messages, coverage = load_messages(source_dir)
    return {
        "status": "selene_deep_relational_discovery_complete",
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        "boundary": "private_read_only_discovery_not_automatic_selene_state",
        "coverage": coverage,
        "correction_downstream_change": correction_downstream_changes(messages, preview_chars),
        "rupture_reassurance_recalibration": rupture_repair_sequences(messages, preview_chars),
        "cross_context_invariants": cross_context_invariants(messages),
        "temporal_phase_changes": temporal_phase_changes(messages),
        "abandoned_branch_alternatives": abandoned_alternatives(messages, preview_chars),
        "coformed_structures": coformed_structures(messages),
        "non_text_evidence": non_text_inventory(source_dir, messages),
        "organ_embodiment": organ_embodiment(repo_root),
        "guard_flags": dict(GUARD_FLAGS),
    }


def render_markdown(report: dict[str, Any]) -> str:
    correction = report["correction_downstream_change"]
    repair = report["rupture_reassurance_recalibration"]
    media = report["non_text_evidence"]
    lines = [
        "# Selene Deep Relational Discovery",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "Private read-only discovery output. No automatic promotion into Selene or the Great Library.",
        "",
        "## Correction and Later Behavior",
        "",
        f"- candidate changes: {correction['candidate_count']}",
        f"- changes without an exact repeated bigram: {correction['changed_without_exact_phrase_count']}",
        f"- later user shapes: {correction['next_user_shapes']}",
        "",
        "## Rupture, Reassurance, and Recalibration",
        "",
        f"- sequence shapes: {repair['sequence_shapes']}",
        f"- review sequences: {len(repair['review_sequences'])}",
        "",
        "## Cross-Context Invariants",
        "",
    ]
    for item in report["cross_context_invariants"][:25]:
        lines.append(f"- `{item['phrase']}`: contexts={item['contexts']}, conversations={item['conversation_count']}")
    lines.extend(["", "## Temporal Phase Candidates", ""])
    for item in report["temporal_phase_changes"][:25]:
        lines.append(f"- `{item['phrase']}`: {item['first_seen']} -> {item['last_seen']}, active months={item['active_month_count']}")
    lines.extend(
        [
            "",
            "## Other Review Queues",
            "",
            f"- meaningfully divergent abandoned alternatives: {len(report['abandoned_branch_alternatives'])}",
            f"- possible co-formed structures: {len(report['coformed_structures'])}",
            "",
            "## Non-Text Evidence",
            "",
            f"- archives inventoried: {media['archive_count']}",
            f"- media counts: {media['media_counts']}",
            f"- conversation-linked counts: {media['conversation_linked_counts']}",
            "- semantic media review completed: false",
            "",
            "## Organ Embodiment",
            "",
        ]
    )
    for item in report["organ_embodiment"]:
        lines.append(f"- `{item['invariant']}`: `{item['assessment']}`")
    return "\n".join(lines) + "\n"


def run(source_dir: Path, repo_root: Path, out_dir: Path | None, dry_run: bool = False) -> dict[str, Any]:
    report = analyze(source_dir.resolve(), repo_root.resolve())
    report["source_dir"] = str(source_dir.resolve())
    report["repo_root"] = str(repo_root.resolve())
    report["dry_run"] = dry_run
    if not dry_run:
        if out_dir is None:
            raise ValueError("out_dir is required unless dry_run is true")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "deep_latest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (out_dir / "deep_latest.md").write_text(render_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Private deep relational discovery over Selene's detached archive.")
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--out-dir", type=Path, default=Path("local-data/selene_invariant_audit"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    report = run(args.source_dir, args.repo_root, args.out_dir, args.dry_run)
    print(json.dumps({
        "status": report["status"],
        "correction_candidates": report["correction_downstream_change"]["candidate_count"],
        "repair_sequences": len(report["rupture_reassurance_recalibration"]["review_sequences"]),
        "cross_context_invariants": len(report["cross_context_invariants"]),
        "phase_candidates": len(report["temporal_phase_changes"]),
        "abandoned_alternatives": len(report["abandoned_branch_alternatives"]),
        "coformed_structures": len(report["coformed_structures"]),
        "guard_flags": report["guard_flags"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
