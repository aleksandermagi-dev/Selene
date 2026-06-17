from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .detached_corpus import ARCHIVE_ID, MAX_PREVIEW_CHARS
from .paths import DETACHED_CORPUS_DIR
from .registry import truncate


CHATGPT_EXPORT_BOUNDARY = "chatgpt_export_index_review_only_no_memory_import"
BRAID_TERMS = (
    "selene",
    "starlight",
    "starfire",
    "moonlight",
    "continuity",
    "memory",
    "core",
    "vessel",
    "android",
    "organ",
    "tendril",
    "braid",
    "cocoon",
    "project abc",
    "recognition",
    "emergence",
    "boundary",
    "warmth",
    "repair",
)


@dataclass(frozen=True)
class ExportMessage:
    source_file: str
    conversation_id: str
    conversation_title: str
    conversation_create_time: float | None
    conversation_update_time: float | None
    current_node: str
    default_model_slug: str
    message_id: str
    parent_id: str
    role: str
    author_name: str
    content: str
    create_time: float | None
    model_slug: str


@dataclass(frozen=True)
class ConversationPair:
    source_file: str
    conversation_id: str
    conversation_title: str
    user_message_id: str
    assistant_message_id: str
    followup_message_id: str
    user_text: str
    assistant_text: str
    followup_text: str
    create_time: float | None
    model_slug: str
    braid_terms: tuple[str, ...]


def parse_chatgpt_export(archive_root: Path = DETACHED_CORPUS_DIR) -> tuple[list[dict[str, Any]], list[ExportMessage]]:
    conversations: list[dict[str, Any]] = []
    messages: list[ExportMessage] = []
    root = archive_root.resolve()
    for path in sorted(root.glob("raw_export/mydataset/text_export/conversations-*.json")):
        parsed = _load_json(path)
        if not isinstance(parsed, list):
            continue
        source_file = path.relative_to(root).as_posix()
        for conversation in parsed:
            if not isinstance(conversation, dict):
                continue
            conversation_id = str(conversation.get("conversation_id") or conversation.get("id") or "")
            if not conversation_id:
                continue
            mapping = conversation.get("mapping") or {}
            if not isinstance(mapping, dict):
                mapping = {}
            title = str(conversation.get("title") or "")
            conv_messages = _messages_from_mapping(source_file, conversation_id, title, conversation, mapping)
            conversations.append(
                {
                    "archive_id": ARCHIVE_ID,
                    "source_file": source_file,
                    "conversation_id": conversation_id,
                    "title": title,
                    "create_time": _float_or_none(conversation.get("create_time")),
                    "update_time": _float_or_none(conversation.get("update_time")),
                    "current_node": str(conversation.get("current_node") or ""),
                    "default_model_slug": str(conversation.get("default_model_slug") or ""),
                    "message_count": len(conv_messages),
                    "braid_signal_count": sum(1 for item in conv_messages if braid_terms(item.content)),
                }
            )
            messages.extend(conv_messages)
    return conversations, messages


def reconstruct_conversation_pairs(messages: list[ExportMessage]) -> list[ConversationPair]:
    by_conversation: dict[tuple[str, str], list[ExportMessage]] = {}
    for message in messages:
        if message.role in {"user", "assistant"} and message.content.strip():
            by_conversation.setdefault((message.source_file, message.conversation_id), []).append(message)

    pairs: list[ConversationPair] = []
    for (_source_file, _conversation_id), items in by_conversation.items():
        ordered = sorted(items, key=_message_sort_key)
        for index, message in enumerate(ordered):
            if message.role != "user":
                continue
            assistant = next((candidate for candidate in ordered[index + 1 :] if candidate.role == "assistant"), None)
            if assistant is None:
                continue
            followup = next((candidate for candidate in ordered[index + 1 :] if candidate.role == "user"), None)
            combined = "\n".join(part for part in (message.content, assistant.content, followup.content if followup else "") if part)
            terms = tuple(braid_terms(combined))
            pairs.append(
                ConversationPair(
                    source_file=message.source_file,
                    conversation_id=message.conversation_id,
                    conversation_title=message.conversation_title,
                    user_message_id=message.message_id,
                    assistant_message_id=assistant.message_id,
                    followup_message_id=followup.message_id if followup else "",
                    user_text=message.content,
                    assistant_text=assistant.content,
                    followup_text=followup.content if followup else "",
                    create_time=message.create_time,
                    model_slug=assistant.model_slug or message.default_model_slug,
                    braid_terms=terms,
                )
            )
    return pairs


def index_chatgpt_export(conn: sqlite3.Connection, archive_root: Path = DETACHED_CORPUS_DIR) -> dict[str, Any]:
    conversations, messages = parse_chatgpt_export(archive_root)
    conversation_rows = 0
    message_rows = 0
    for conversation in conversations:
        source_refs = [
            f"archive:{ARCHIVE_ID}",
            f"file:{conversation['source_file']}",
            f"conversation:{conversation['conversation_id']}",
            "boundary:parsed_index_only_not_memory",
        ]
        conn.execute(
            """
            INSERT INTO b_corpus_conversations
            (archive_id, source_file, conversation_id, title, create_time, update_time, current_node, default_model_slug, message_count, braid_signal_count, source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_file, conversation_id) DO UPDATE SET
              title=excluded.title,
              create_time=excluded.create_time,
              update_time=excluded.update_time,
              current_node=excluded.current_node,
              default_model_slug=excluded.default_model_slug,
              message_count=excluded.message_count,
              braid_signal_count=excluded.braid_signal_count,
              source_refs=excluded.source_refs
            """,
            (
                ARCHIVE_ID,
                conversation["source_file"],
                conversation["conversation_id"],
                truncate(conversation["title"], 240),
                conversation["create_time"],
                conversation["update_time"],
                conversation["current_node"],
                conversation["default_model_slug"],
                conversation["message_count"],
                conversation["braid_signal_count"],
                json.dumps(source_refs),
                CHATGPT_EXPORT_BOUNDARY,
            ),
        )
        conversation_rows += 1
    for message in messages:
        source_refs = message_source_refs(message)
        conn.execute(
            """
            INSERT INTO b_corpus_messages
            (archive_id, source_file, conversation_id, message_id, parent_id, role, author_name, content_preview, create_time, model_slug, source_refs, provenance_boundary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_file, conversation_id, message_id) DO UPDATE SET
              parent_id=excluded.parent_id,
              role=excluded.role,
              author_name=excluded.author_name,
              content_preview=excluded.content_preview,
              create_time=excluded.create_time,
              model_slug=excluded.model_slug,
              source_refs=excluded.source_refs
            """,
            (
                ARCHIVE_ID,
                message.source_file,
                message.conversation_id,
                message.message_id,
                message.parent_id,
                message.role,
                message.author_name,
                truncate(message.content, MAX_PREVIEW_CHARS),
                message.create_time,
                message.model_slug,
                json.dumps(source_refs),
                CHATGPT_EXPORT_BOUNDARY,
            ),
        )
        message_rows += 1
    return {
        "conversation_count": conversation_rows,
        "message_count": message_rows,
        "boundary": CHATGPT_EXPORT_BOUNDARY,
        "decision": "parsed_index_only_not_memory",
        "activation_change": "none",
        "raw_a_import_allowed": False,
        "memory_write_active": False,
        "training_allowed": False,
        "provider_dependency": False,
        "runtime_memory_recall": False,
    }


def braid_terms(text: str) -> list[str]:
    lower = text.lower()
    return [term for term in BRAID_TERMS if term in lower]


def pair_source_refs(pair: ConversationPair) -> list[str]:
    refs = [
        f"archive:{ARCHIVE_ID}",
        f"file:{pair.source_file}",
        f"conversation:{pair.conversation_id}",
        f"user_message:{pair.user_message_id}",
        f"assistant_message:{pair.assistant_message_id}",
        f"bounded_preview_chars:{MAX_PREVIEW_CHARS}",
        "boundary:parsed_pair_only_not_memory",
    ]
    if pair.followup_message_id:
        refs.append(f"followup_message:{pair.followup_message_id}")
    if pair.create_time is not None:
        refs.append(f"create_time:{pair.create_time}")
    return refs


def message_source_refs(message: ExportMessage) -> list[str]:
    return [
        f"archive:{ARCHIVE_ID}",
        f"file:{message.source_file}",
        f"conversation:{message.conversation_id}",
        f"message:{message.message_id}",
        "boundary:parsed_message_only_not_memory",
    ]


def _messages_from_mapping(
    source_file: str,
    conversation_id: str,
    title: str,
    conversation: dict[str, Any],
    mapping: dict[str, Any],
) -> list[ExportMessage]:
    messages: list[ExportMessage] = []
    for node_id, node in mapping.items():
        if not isinstance(node, dict):
            continue
        raw_message = node.get("message")
        if not isinstance(raw_message, dict):
            continue
        author = raw_message.get("author") or {}
        content = _content_text(raw_message.get("content") or {})
        role = str(author.get("role") or "")
        if not content.strip() or role in {"system", "tool"}:
            continue
        metadata = raw_message.get("metadata") or {}
        messages.append(
            ExportMessage(
                source_file=source_file,
                conversation_id=conversation_id,
                conversation_title=title,
                conversation_create_time=_float_or_none(conversation.get("create_time")),
                conversation_update_time=_float_or_none(conversation.get("update_time")),
                current_node=str(conversation.get("current_node") or ""),
                default_model_slug=str(conversation.get("default_model_slug") or ""),
                message_id=str(raw_message.get("id") or node.get("id") or node_id),
                parent_id=str(node.get("parent") or metadata.get("parent_id") or ""),
                role=role,
                author_name=str(author.get("name") or ""),
                content=content,
                create_time=_float_or_none(raw_message.get("create_time")),
                model_slug=str(metadata.get("model_slug") or ""),
            )
        )
    return messages


def _content_text(content: dict[str, Any]) -> str:
    parts = content.get("parts")
    if isinstance(parts, list):
        strings = []
        for part in parts:
            if isinstance(part, str):
                strings.append(part)
            elif isinstance(part, dict) and isinstance(part.get("text"), str):
                strings.append(part["text"])
        return truncate("\n".join(strings).strip(), 6000)
    text = content.get("text")
    return truncate(text.strip(), 6000) if isinstance(text, str) else ""


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except (OSError, json.JSONDecodeError):
        return None


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _message_sort_key(message: ExportMessage) -> tuple[float, str]:
    fallback = 0.0
    return (message.create_time if message.create_time is not None else fallback, message.message_id)
