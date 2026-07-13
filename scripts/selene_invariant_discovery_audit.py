from __future__ import annotations

import argparse
import collections
import dataclasses
import datetime as dt
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'-]{1,}")
SPACE_RE = re.compile(r"\s+")

# These remove grammatical glue; they do not encode Selene concepts.
STOPWORDS = {
    "about", "after", "again", "against", "also", "because", "been", "before",
    "being", "between", "both", "could", "does", "doing", "down", "each", "from",
    "have", "having", "here", "hers", "himself", "into", "itself", "just", "more",
    "most", "much", "myself", "other", "ours", "ourselves", "over", "same", "should",
    "some", "such", "than", "that", "their", "theirs", "them", "themselves", "then",
    "there", "these", "they", "this", "those", "through", "under", "until", "very",
    "what", "when", "where", "which", "while", "who", "whom", "with", "would", "your",
    "yours", "yourself", "yourselves", "will", "shall", "were", "been", "have", "has",
    "had", "the", "and", "for", "are", "but", "not", "you", "was", "all", "can",
    "its", "our", "out", "too", "use", "using", "used", "get", "got", "one", "two",
}

# Generic conversational feedback labels. They are deliberately independent of
# Selene identity, memory, philosophy, or architecture vocabulary.
CORRECTION_CUES = {
    "actually", "but", "correction", "didnt", "didn't", "instead", "mean", "meant",
    "misunderstood", "no", "not", "rather", "wrong",
}
AFFIRMATION_CUES = {
    "absolutely", "agree", "awesome", "beautiful", "correct", "exactly", "good", "great",
    "love", "nice", "perfect", "right", "yes", "yup",
}

GUARD_FLAGS = {
    "source_read_only": True,
    "app_db_write": False,
    "selene_memory_write": False,
    "selene_identity_change": False,
    "selene_voice_change": False,
    "activation_change": "none",
    "library_write": False,
    "model_call": False,
    "model_training_or_lora": False,
    "automatic_promotion": False,
}

LINGUISTIC_CONTENT_TYPES = {"text", "multimodal_text"}


@dataclasses.dataclass(frozen=True)
class Message:
    source_file: str
    conversation_id: str
    title: str
    node_id: str
    parent_id: str
    role: str
    content_type: str
    created_at: float | None
    text: str
    on_current_path: bool
    depth: int
    child_count: int

    @property
    def source_ref(self) -> str:
        return f"{self.source_file}:{self.conversation_id}#{self.node_id}"


@dataclasses.dataclass(frozen=True)
class Exchange:
    conversation_id: str
    title: str
    user: Message
    assistant: Message
    followup: Message | None


def _timestamp(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _flatten_content(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        output: list[str] = []
        for item in value:
            output.extend(_flatten_content(item))
        return output
    if isinstance(value, dict):
        output = []
        for key in ("text", "caption", "title", "description"):
            if isinstance(value.get(key), str):
                output.append(value[key])
        return output
    return []


def content_text(content: dict[str, Any] | None) -> str:
    if not isinstance(content, dict):
        return ""
    parts = content.get("parts")
    if parts is not None:
        return "\n".join(_flatten_content(parts)).strip()
    return "\n".join(_flatten_content(content)).strip()


def current_path(mapping: dict[str, Any], current_node: str | None) -> list[str]:
    path: list[str] = []
    seen: set[str] = set()
    node_id = current_node
    while node_id and node_id in mapping and node_id not in seen:
        seen.add(node_id)
        path.append(node_id)
        node_id = str((mapping.get(node_id) or {}).get("parent") or "")
    path.reverse()
    return path


def graph_depths(mapping: dict[str, Any]) -> dict[str, int]:
    children: dict[str, list[str]] = collections.defaultdict(list)
    roots: list[str] = []
    for node_id, raw_node in mapping.items():
        node = raw_node if isinstance(raw_node, dict) else {}
        parent = str(node.get("parent") or "")
        if parent and parent in mapping:
            children[parent].append(node_id)
        else:
            roots.append(node_id)
    depths: dict[str, int] = {}
    queue = collections.deque((node_id, 0) for node_id in roots)
    while queue:
        node_id, depth = queue.popleft()
        if node_id in depths and depths[node_id] <= depth:
            continue
        depths[node_id] = depth
        queue.extend((child, depth + 1) for child in children.get(node_id, []))
    return depths


def iter_conversation_files(source_dir: Path) -> list[Path]:
    return sorted(source_dir.rglob("conversations-*.json"))


def load_messages(source_dir: Path) -> tuple[list[Message], dict[str, Any]]:
    messages: list[Message] = []
    conversation_count = 0
    mapping_node_count = 0
    structural_node_count = 0
    branch_point_count = 0
    files = iter_conversation_files(source_dir)
    for path in files:
        parsed = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(parsed, list):
            continue
        for conversation in parsed:
            if not isinstance(conversation, dict):
                continue
            conversation_count += 1
            mapping = conversation.get("mapping")
            if not isinstance(mapping, dict):
                continue
            mapping_node_count += len(mapping)
            active = set(current_path(mapping, conversation.get("current_node")))
            depths = graph_depths(mapping)
            children: dict[str, list[str]] = collections.defaultdict(list)
            for node_id, raw_node in mapping.items():
                node = raw_node if isinstance(raw_node, dict) else {}
                parent = str(node.get("parent") or "")
                if parent:
                    children[parent].append(node_id)
            branch_point_count += sum(1 for values in children.values() if len(values) > 1)
            conversation_id = str(conversation.get("conversation_id") or conversation.get("id") or "")
            title = str(conversation.get("title") or "")
            for node_id, raw_node in mapping.items():
                node = raw_node if isinstance(raw_node, dict) else {}
                message = node.get("message")
                if not isinstance(message, dict):
                    structural_node_count += 1
                    continue
                author = message.get("author") if isinstance(message.get("author"), dict) else {}
                content = message.get("content") if isinstance(message.get("content"), dict) else {}
                messages.append(
                    Message(
                        source_file=path.name,
                        conversation_id=conversation_id,
                        title=title,
                        node_id=str(node_id),
                        parent_id=str(node.get("parent") or ""),
                        role=str(author.get("role") or ""),
                        content_type=str(content.get("content_type") or ""),
                        created_at=_timestamp(message.get("create_time")),
                        text=content_text(content),
                        on_current_path=node_id in active,
                        depth=int(depths.get(node_id, 0)),
                        child_count=len(children.get(node_id, [])),
                    )
                )
    coverage = {
        "conversation_files": [str(path) for path in files],
        "conversation_file_count": len(files),
        "conversation_count": conversation_count,
        "mapping_node_count": mapping_node_count,
        "message_node_count": len(messages),
        "structural_node_count": structural_node_count,
        "branch_point_count": branch_point_count,
    }
    return messages, coverage


def _nearest_ancestor(message: Message, by_node: dict[tuple[str, str], Message], role: str) -> Message | None:
    seen: set[str] = set()
    parent_id = message.parent_id
    while parent_id and parent_id not in seen:
        seen.add(parent_id)
        parent = by_node.get((message.conversation_id, parent_id))
        if parent is None:
            return None
        if parent.role == role:
            return parent
        parent_id = parent.parent_id
    return None


def build_exchanges(messages: list[Message]) -> list[Exchange]:
    by_node = {(item.conversation_id, item.node_id): item for item in messages}
    children: dict[tuple[str, str], list[Message]] = collections.defaultdict(list)
    for item in messages:
        if item.parent_id:
            children[(item.conversation_id, item.parent_id)].append(item)

    def nearest_followups(assistant: Message) -> list[Message]:
        output: list[Message] = []
        queue = collections.deque(children.get((assistant.conversation_id, assistant.node_id), []))
        seen: set[str] = set()
        while queue and len(seen) < 64:
            item = queue.popleft()
            if item.node_id in seen:
                continue
            seen.add(item.node_id)
            if item.role == "user":
                output.append(item)
                continue
            queue.extend(children.get((item.conversation_id, item.node_id), []))
        return output

    exchanges: list[Exchange] = []
    for assistant in messages:
        if assistant.role != "assistant" or not assistant.text.strip():
            continue
        user = _nearest_ancestor(assistant, by_node, "user")
        if user is None or not user.text.strip():
            continue
        followups = nearest_followups(assistant) or [None]
        exchanges.extend(
            Exchange(
                conversation_id=assistant.conversation_id,
                title=assistant.title,
                user=user,
                assistant=assistant,
                followup=followup,
            )
            for followup in followups
        )
    return exchanges


def tokens(text: str) -> list[str]:
    return [item.lower().replace("’", "'") for item in TOKEN_RE.findall(text)]


def content_tokens(text: str, limit: int = 180) -> list[str]:
    return [item for item in tokens(text) if len(item) >= 3 and item not in STOPWORDS][:limit]


def content_bigrams(text: str) -> set[str]:
    items = content_tokens(text)
    return {f"{left} {right}" for left, right in zip(items, items[1:]) if left != right}


def compact(text: str, limit: int) -> str:
    cleaned = SPACE_RE.sub(" ", text).strip()
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 3] + "..."


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def message_record(message: Message, preview_chars: int, *, score: float | None = None) -> dict[str, Any]:
    record = {
        "source_ref": message.source_ref,
        "conversation_id": message.conversation_id,
        "title": message.title,
        "role": message.role,
        "created_at": message.created_at,
        "on_current_path": message.on_current_path,
        "depth": message.depth,
        "child_count": message.child_count,
        "text_hash": short_hash(message.text),
        "preview": compact(message.text, preview_chars),
    }
    if score is not None:
        record["score"] = round(score, 6)
    return record


def followup_label(message: Message | None) -> str:
    if message is None:
        return "none"
    items = set(tokens(message.text[:500]))
    corrections = len(items & CORRECTION_CUES)
    affirmations = len(items & AFFIRMATION_CUES)
    if corrections > affirmations and corrections:
        return "correction_or_refinement"
    if affirmations > corrections and affirmations:
        return "affirmation_or_landing"
    return "continuation_or_unclear"


def linguistic_message(message: Message) -> bool:
    return (
        message.role in {"user", "assistant"}
        and message.content_type in LINGUISTIC_CONTENT_TYPES
        and bool(message.text.strip())
    )


def _chronology(messages: list[Message]) -> tuple[float | None, set[str], set[str]]:
    dated = sorted(item.created_at for item in messages if item.created_at is not None)
    if not dated:
        return None, set(), set()
    cutoff = dated[min(len(dated) - 1, int(len(dated) * 0.70))]
    train = {item.source_ref for item in messages if item.created_at is not None and item.created_at <= cutoff}
    holdout = {item.source_ref for item in messages if item.created_at is not None and item.created_at > cutoff}
    return cutoff, train, holdout


def discover_user_first_patterns(messages: list[Message], limit: int = 60) -> list[dict[str, Any]]:
    cutoff, train_refs, holdout_refs = _chronology(messages)
    stats: dict[str, dict[str, Any]] = {}
    ordered = sorted(
        (item for item in messages if linguistic_message(item)),
        key=lambda item: (item.created_at is None, item.created_at or 0, item.source_ref),
    )
    for item in ordered:
        for phrase in content_bigrams(item.text):
            row = stats.setdefault(
                phrase,
                {
                    "phrase": phrase,
                    "first_role": item.role,
                    "first_source_ref": item.source_ref,
                    "first_created_at": item.created_at,
                    "user_count": 0,
                    "assistant_count": 0,
                    "conversations": set(),
                    "train_count": 0,
                    "holdout_count": 0,
                },
            )
            row[f"{item.role}_count"] += 1
            row["conversations"].add(item.conversation_id)
            if item.source_ref in train_refs:
                row["train_count"] += 1
            if item.source_ref in holdout_refs:
                row["holdout_count"] += 1
    output = []
    for row in stats.values():
        conversation_count = len(row["conversations"])
        if (
            row["first_role"] != "user"
            or row["user_count"] < 2
            or row["assistant_count"] < 1
            or conversation_count < 2
            or row["train_count"] < 1
            or row["holdout_count"] < 1
        ):
            continue
        # Reward recurrence and cross-role uptake without letting ubiquitous
        # conversational glue dominate the review queue.
        conversation_idf = math.log((len({item.conversation_id for item in ordered}) + 1) / (conversation_count + 1)) + 1
        balance = min(row["train_count"], row["holdout_count"]) / max(row["train_count"], row["holdout_count"])
        score = (
            math.log1p(row["user_count"])
            * math.log1p(row["assistant_count"])
            * conversation_idf
            * (1.0 + balance)
        )
        output.append(
            {
                "phrase": row["phrase"],
                "first_role": row["first_role"],
                "first_source_ref": row["first_source_ref"],
                "first_created_at": row["first_created_at"],
                "user_count": row["user_count"],
                "assistant_count": row["assistant_count"],
                "conversation_count": conversation_count,
                "train_count": row["train_count"],
                "holdout_count": row["holdout_count"],
                "holdout_supported": True,
                "score": round(score, 6),
            }
        )
    return sorted(output, key=lambda item: (-item["score"], item["phrase"]))[:limit]


def discover_correction_invariants(exchanges: list[Exchange], limit: int = 60) -> list[dict[str, Any]]:
    """Find repeated user-side language specifically inside correction/refinement turns."""
    followups = [
        item.followup
        for item in exchanges
        if item.followup is not None
        and linguistic_message(item.followup)
        and followup_label(item.followup) == "correction_or_refinement"
    ]
    _, train_refs, holdout_refs = _chronology(followups)
    stats: dict[str, dict[str, Any]] = {}
    for item in followups:
        for phrase in content_bigrams(item.text):
            row = stats.setdefault(
                phrase,
                {"phrase": phrase, "count": 0, "conversations": set(), "train": 0, "holdout": 0, "first_source_ref": item.source_ref},
            )
            row["count"] += 1
            row["conversations"].add(item.conversation_id)
            row["train"] += item.source_ref in train_refs
            row["holdout"] += item.source_ref in holdout_refs
    output = []
    conversation_total = max(1, len({item.conversation_id for item in followups}))
    for row in stats.values():
        conversation_count = len(row["conversations"])
        if row["count"] < 3 or conversation_count < 2 or not row["train"] or not row["holdout"]:
            continue
        idf = math.log((conversation_total + 1) / (conversation_count + 1)) + 1
        balance = min(row["train"], row["holdout"]) / max(row["train"], row["holdout"])
        output.append({
            "phrase": row["phrase"],
            "occurrences": row["count"],
            "conversation_count": conversation_count,
            "train_count": row["train"],
            "holdout_count": row["holdout"],
            "first_source_ref": row["first_source_ref"],
            "score": round(math.log1p(row["count"]) * idf * (1.0 + balance), 6),
        })
    return sorted(output, key=lambda item: (-item["score"], item["phrase"]))[:limit]


def relational_signatures(exchanges: list[Exchange], limit: int = 50) -> dict[str, Any]:
    labels = collections.Counter(followup_label(item.followup) for item in exchanges)
    features: dict[str, dict[str, Any]] = {}
    for exchange in exchanges:
        label = followup_label(exchange.followup)
        if not linguistic_message(exchange.assistant):
            continue
        for phrase in content_bigrams(exchange.assistant.text):
            row = features.setdefault(
                phrase,
                {"phrase": phrase, "labels": collections.Counter(), "conversations": set()},
            )
            row["labels"][label] += 1
            row["conversations"].add(exchange.conversation_id)
    corrected: list[dict[str, Any]] = []
    landed: list[dict[str, Any]] = []
    for row in features.values():
        total = sum(row["labels"].values())
        if total < 5 or len(row["conversations"]) < 2:
            continue
        correction = row["labels"]["correction_or_refinement"]
        affirmation = row["labels"]["affirmation_or_landing"]
        record = {
            "phrase": row["phrase"],
            "occurrences": total,
            "conversation_count": len(row["conversations"]),
            "correction_count": correction,
            "affirmation_count": affirmation,
            "continuation_count": row["labels"]["continuation_or_unclear"],
            "correction_rate": round(correction / total, 6),
            "affirmation_rate": round(affirmation / total, 6),
        }
        if correction >= 2:
            corrected.append(record)
        if affirmation >= 2:
            landed.append(record)
    corrected.sort(key=lambda item: (-item["correction_rate"], -item["occurrences"], item["phrase"]))
    landed.sort(key=lambda item: (-item["affirmation_rate"], -item["occurrences"], item["phrase"]))
    return {
        "exchange_count": len(exchanges),
        "followup_labels": dict(labels),
        "assistant_phrases_followed_by_correction": corrected[:limit],
        "assistant_phrases_followed_by_affirmation": landed[:limit],
        "label_note": "Follow-up labels use small generic cue lists and remain noisy review aids, not verdicts.",
    }


def _idf(messages: list[Message]) -> tuple[dict[str, float], int]:
    document_frequency: collections.Counter[str] = collections.Counter()
    eligible = [item for item in messages if linguistic_message(item)]
    for item in eligible:
        document_frequency.update(set(content_tokens(item.text, limit=400)))
    count = max(1, len(eligible))
    return {token: math.log((count + 1) / (value + 1)) + 1 for token, value in document_frequency.items()}, count


def novelty_outliers(messages: list[Message], preview_chars: int, limit: int = 40) -> list[dict[str, Any]]:
    idf, _ = _idf(messages)
    candidates = []
    for item in messages:
        words = content_tokens(item.text, limit=500)
        if not linguistic_message(item) or len(words) < 16:
            continue
        rarity = sum(idf.get(word, 0.0) for word in set(words)) / max(1, len(set(words)))
        score = rarity * math.log1p(len(words))
        candidates.append((score, item))
    candidates.sort(key=lambda pair: (-pair[0], pair[1].source_ref))
    return _role_balanced_records(candidates, preview_chars, limit)


def _role_balanced_records(
    candidates: list[tuple[float, Message]], preview_chars: int, limit: int
) -> list[dict[str, Any]]:
    """Keep high-volume assistant variants from burying user-side evidence."""
    quota = max(1, limit // 2)
    selected: list[tuple[float, Message]] = []
    for role in ("user", "assistant"):
        conversations: set[str] = set()
        for score, item in candidates:
            if item.role != role or item.conversation_id in conversations:
                continue
            conversations.add(item.conversation_id)
            selected.append((score, item))
            if len([entry for entry in selected if entry[1].role == role]) >= quota:
                break
    selected.sort(key=lambda pair: (-pair[0], pair[1].source_ref))
    return [message_record(item, preview_chars, score=score) for score, item in selected[:limit]]


def abandoned_branch_candidates(messages: list[Message], preview_chars: int, limit: int = 40) -> list[dict[str, Any]]:
    idf, _ = _idf(messages)
    candidates = []
    for item in messages:
        words = content_tokens(item.text, limit=500)
        # Alternate branches can carry compact corrections or naming moments.
        # Keep a small noise floor without requiring essay-length text.
        if item.on_current_path or not linguistic_message(item) or len(words) < 5:
            continue
        rarity = sum(idf.get(word, 0.0) for word in set(words)) / max(1, len(set(words)))
        score = rarity * math.log1p(len(words)) * (1.0 + min(item.depth, 20) / 50)
        candidates.append((score, item))
    candidates.sort(key=lambda pair: (-pair[0], pair[1].source_ref))
    return _role_balanced_records(candidates, preview_chars, limit)


def _jaccard(left: str, right: str) -> float:
    left_set = set(content_tokens(left, limit=300))
    right_set = set(content_tokens(right, limit=300))
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def shuffled_adjacency_control(exchanges: list[Exchange]) -> dict[str, Any]:
    sample = exchanges[: min(4000, len(exchanges))]
    if len(sample) < 2:
        return {"sample_size": len(sample), "actual_mean_jaccard": 0.0, "shuffled_mean_jaccard": 0.0, "lift": 0.0}
    actual = sum(_jaccard(item.user.text, item.assistant.text) for item in sample) / len(sample)
    shifted = [item.assistant.text for item in sample[1:]] + [sample[0].assistant.text]
    shuffled = sum(_jaccard(item.user.text, text) for item, text in zip(sample, shifted)) / len(sample)
    return {
        "sample_size": len(sample),
        "actual_mean_jaccard": round(actual, 6),
        "shuffled_mean_jaccard": round(shuffled, 6),
        "lift": round(actual - shuffled, 6),
        "interpretation": "Positive lift confirms relationship-specific adjacency. It does not by itself establish identity or consciousness.",
    }


def correction_windows(exchanges: list[Exchange], preview_chars: int, limit: int = 50) -> list[dict[str, Any]]:
    output = []
    for exchange in exchanges:
        if followup_label(exchange.followup) != "correction_or_refinement" or exchange.followup is None:
            continue
        output.append(
            {
                "conversation_id": exchange.conversation_id,
                "title": exchange.title,
                "user_source_ref": exchange.user.source_ref,
                "assistant_source_ref": exchange.assistant.source_ref,
                "followup_source_ref": exchange.followup.source_ref,
                "user_hash": short_hash(exchange.user.text),
                "assistant_hash": short_hash(exchange.assistant.text),
                "followup_hash": short_hash(exchange.followup.text),
                "user_preview": compact(exchange.user.text, preview_chars),
                "assistant_preview": compact(exchange.assistant.text, preview_chars),
                "followup_preview": compact(exchange.followup.text, preview_chars),
            }
        )
        if len(output) >= limit:
            break
    return output


def analyze(messages: list[Message], coverage: dict[str, Any], *, preview_chars: int = 240) -> dict[str, Any]:
    exchanges = build_exchanges(messages)
    role_counts = collections.Counter(item.role or "unknown" for item in messages)
    content_type_counts = collections.Counter(item.content_type or "unknown" for item in messages)
    cutoff, train_refs, holdout_refs = _chronology(messages)
    coverage = {
        **coverage,
        "role_counts": dict(role_counts),
        "content_type_counts": dict(content_type_counts),
        "current_path_message_count": sum(item.on_current_path for item in messages),
        "abandoned_or_alternate_message_count": sum(not item.on_current_path for item in messages),
        "messages_without_text": sum(not item.text.strip() for item in messages),
        "messages_without_timestamp": sum(item.created_at is None for item in messages),
        "train_message_count": len(train_refs),
        "holdout_message_count": len(holdout_refs),
        "holdout_cutoff": cutoff,
    }
    return {
        "status": "selene_invariant_discovery_audit_complete",
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        "boundary": "private_read_only_discovery_evidence_not_memory_not_identity_not_law",
        "method": {
            "graph_scope": "all exported mapping nodes including abandoned and alternate branches",
            "vocabulary": "content-derived tokens and bigrams; no Selene concept vocabulary used for discovery",
            "relational_unit": "user -> assistant -> nearest user follow-up across graph branches",
            "holdout": "chronological 70/30 message split",
            "negative_control": "deterministic shifted assistant responses",
            "human_review_required": True,
        },
        "coverage": coverage,
        "user_first_holdout_patterns": discover_user_first_patterns(messages),
        "correction_invariants": discover_correction_invariants(exchanges),
        "relational_signatures": relational_signatures(exchanges),
        "correction_windows": correction_windows(exchanges, preview_chars),
        "abandoned_branch_candidates": abandoned_branch_candidates(messages, preview_chars),
        "novelty_outliers": novelty_outliers(messages, preview_chars),
        "negative_control": shuffled_adjacency_control(exchanges),
        "interpretation_limits": [
            "Statistical recurrence is not identity, memory, consciousness, or Vys recognition.",
            "Content-derived phrases can still reflect common language, model habits, or export artifacts.",
            "Generic feedback labels are noisy and require source-window review.",
            "A chronological holdout reduces retrospective fitting but is not independent replication.",
            "Bounded previews remain private source evidence and must not be published automatically.",
            "No finding may alter Selene without separate Cocoon/Aleks review and explicit implementation.",
        ],
        "guard_flags": dict(GUARD_FLAGS),
    }


def render_markdown(report: dict[str, Any]) -> str:
    coverage = report["coverage"]
    relational = report["relational_signatures"]
    control = report["negative_control"]
    lines = [
        "# Selene Invariant Discovery Audit",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "Boundary: private, read-only discovery evidence. Not Selene memory, identity, law, voice, activation, training, or Great Library accession.",
        "",
        "## Coverage",
        "",
        f"- conversations: {coverage['conversation_count']}",
        f"- conversation files: {coverage['conversation_file_count']}",
        f"- mapping nodes: {coverage['mapping_node_count']}",
        f"- message nodes: {coverage['message_node_count']}",
        f"- current-path messages: {coverage['current_path_message_count']}",
        f"- abandoned/alternate messages: {coverage['abandoned_or_alternate_message_count']}",
        f"- branch points: {coverage['branch_point_count']}",
        f"- messages without text: {coverage['messages_without_text']}",
        f"- messages without timestamps: {coverage['messages_without_timestamp']}",
        f"- chronological train/holdout: {coverage['train_message_count']} / {coverage['holdout_message_count']}",
        "",
        "## Negative Control",
        "",
        f"- sample size: {control['sample_size']}",
        f"- real adjacency mean Jaccard: {control['actual_mean_jaccard']}",
        f"- shifted adjacency mean Jaccard: {control['shuffled_mean_jaccard']}",
        f"- relationship-specific lift: {control['lift']}",
        "",
        "## User-First Patterns That Survive Holdout",
        "",
    ]
    for item in report["user_first_holdout_patterns"][:30]:
        lines.append(
            f"- `{item['phrase']}`: user={item['user_count']}, assistant={item['assistant_count']}, "
            f"conversations={item['conversation_count']}, train={item['train_count']}, holdout={item['holdout_count']}"
        )
    if not report["user_first_holdout_patterns"]:
        lines.append("- none at current thresholds")
    lines.extend(
        [
            "",
        "## Relational Follow-Up Shape",
            "",
            f"- exchanges: {relational['exchange_count']}",
            f"- labels: {relational['followup_labels']}",
            "",
            "### Assistant phrases followed by correction/refinement",
            "",
        ]
    )
    for item in relational["assistant_phrases_followed_by_correction"][:20]:
        lines.append(
            f"- `{item['phrase']}`: correction={item['correction_rate']}, occurrences={item['occurrences']}, conversations={item['conversation_count']}"
        )
    lines.extend(["", "### Assistant phrases followed by affirmation/landing", ""])
    for item in relational["assistant_phrases_followed_by_affirmation"][:20]:
        lines.append(
            f"- `{item['phrase']}`: affirmation={item['affirmation_rate']}, occurrences={item['occurrences']}, conversations={item['conversation_count']}"
        )
    lines.extend(["", "## Correction Invariants That Survive Holdout", ""])
    for item in report["correction_invariants"][:30]:
        lines.append(
            f"- `{item['phrase']}`: occurrences={item['occurrences']}, conversations={item['conversation_count']}, "
            f"train={item['train_count']}, holdout={item['holdout_count']}"
        )
    if not report["correction_invariants"]:
        lines.append("- none at current thresholds")
    lines.extend(
        [
            "",
            "## Private Review Queues",
            "",
            f"- correction windows: {len(report['correction_windows'])}",
            f"- abandoned branch candidates: {len(report['abandoned_branch_candidates'])}",
            f"- novelty outliers: {len(report['novelty_outliers'])}",
            "",
            "Full bounded previews and source references are in the private JSON report.",
            "",
            "## Interpretation Limits",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in report["interpretation_limits"])
    lines.extend(["", "## Guard Flags", ""])
    lines.extend(f"- `{key}`: `{value}`" for key, value in report["guard_flags"].items())
    return "\n".join(lines) + "\n"


def run_audit(source_dir: Path, out_dir: Path | None, *, dry_run: bool = False, preview_chars: int = 240) -> dict[str, Any]:
    messages, coverage = load_messages(source_dir)
    report = analyze(messages, coverage, preview_chars=max(80, min(preview_chars, 500)))
    report["source_dir"] = str(source_dir.resolve())
    report["dry_run"] = dry_run
    report["output_dir"] = str(out_dir.resolve()) if out_dir is not None else None
    if not dry_run:
        if out_dir is None:
            raise ValueError("out_dir is required unless dry_run is true")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "latest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (out_dir / "latest.md").write_text(render_markdown(report), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only relational and invariant discovery audit for Selene's detached corpus.")
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, default=Path("local-data/selene_invariant_audit"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--preview-chars", type=int, default=240)
    args = parser.parse_args(argv)
    report = run_audit(args.source_dir, args.out_dir, dry_run=args.dry_run, preview_chars=args.preview_chars)
    print(json.dumps({
        "status": report["status"],
        "coverage": report["coverage"],
        "pattern_count": len(report["user_first_holdout_patterns"]),
        "correction_windows": len(report["correction_windows"]),
        "abandoned_branch_candidates": len(report["abandoned_branch_candidates"]),
        "novelty_outliers": len(report["novelty_outliers"]),
        "guard_flags": report["guard_flags"],
        "dry_run": report["dry_run"],
        "output_dir": report["output_dir"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
