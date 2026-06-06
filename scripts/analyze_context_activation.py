from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("DevelopmentalCorpusArchive_20260526_122541/raw_export/mydataset/text_export")
OUT = Path("analysis/metadata_audit_20260605")
ACTIVATION_KEYS = {
    "conversation_context_citation_metadata",
    "conversation_context_citation_metadata_status",
    "personal_sources",
    "connectors_file_search",
    "search_queries",
    "search_result_groups",
    "retrieval_search_sources",
    "retrieval_file_index",
    "retrieval_turn_number",
    "content_references",
}


def iso(ts: float | int | None) -> str:
    if not ts:
        return ""
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


def text_from_content(content: dict | None) -> str:
    if not content:
        return ""
    ctype = content.get("content_type")
    if ctype in {"text", "user_editable_context"}:
        parts = content.get("parts") or []
        return "\n".join(str(part) for part in parts if part is not None)
    if ctype == "multimodal_text":
        parts = []
        for part in content.get("parts") or []:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(part.get("text") or part.get("name") or part.get("id") or "")
        return "\n".join(part for part in parts if part)
    return json.dumps(content, ensure_ascii=False)[:2000]


def bounded(value: str, limit: int = 360) -> str:
    value = " ".join((value or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 3] + "..."


def author_role(node: dict | None) -> str:
    msg = (node or {}).get("message") or {}
    return ((msg.get("author") or {}).get("role")) or ""


def message_text(node: dict | None) -> str:
    msg = (node or {}).get("message") or {}
    return text_from_content(msg.get("content") or {})


def previous_user(mapping: dict, node: dict) -> tuple[str, str]:
    parent_id = node.get("parent")
    while parent_id:
        parent = mapping.get(parent_id) or {}
        if author_role(parent) == "user":
            msg = parent.get("message") or {}
            return msg.get("id") or parent_id, message_text(parent)
        parent_id = parent.get("parent")
    return "", ""


def iter_conversations():
    for path in sorted(ROOT.glob("conversations-*.json")):
        for conversation in json.loads(path.read_text(encoding="utf-8")):
            yield path.name, conversation


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, str]] = []
    source_rows: list[dict[str, str]] = []
    activation_key_counts = Counter()
    citation_type_counts = Counter()
    attribution_counts = Counter()
    status_counts = Counter()
    conversation_counts = Counter()
    memory_ids = Counter()
    citations_by_conversation = defaultdict(int)

    for source_file, conv in iter_conversations():
        mapping = conv.get("mapping") or {}
        conv_id = conv.get("conversation_id") or conv.get("id") or ""
        title = conv.get("title") or ""
        month = iso(conv.get("create_time"))[:7]
        conversation_memory_scope = conv.get("memory_scope")

        for node_id, node in mapping.items():
            msg = node.get("message") or {}
            metadata = msg.get("metadata") or {}
            active_keys = sorted(key for key in metadata if key in ACTIVATION_KEYS)
            if active_keys:
                for key in active_keys:
                    value = metadata.get(key)
                    if key == "content_references" and value in ([], None):
                        continue
                    if key == "search_result_groups" and value in ([], None):
                        continue
                    if key == "search_queries" and value in ([], None):
                        continue
                    activation_key_counts[key] += 1
                    source_rows.append(
                        {
                            "conversation_id": conv_id,
                            "conversation_title": title,
                            "month": month,
                            "message_id": msg.get("id") or node_id,
                            "role": ((msg.get("author") or {}).get("role")) or "",
                            "metadata_key": key,
                            "value_preview": bounded(json.dumps(value, ensure_ascii=False, default=str), 500),
                        }
                    )

            citations = metadata.get("conversation_context_citation_metadata") or []
            if not citations:
                continue

            status = str(metadata.get("conversation_context_citation_metadata_status") or "")
            status_counts[status] += 1
            conversation_counts[title] += 1
            citations_by_conversation[conv_id] += len(citations)
            prev_user_id, prev_user_text = previous_user(mapping, node)

            for item in citations:
                citation = item.get("citation") or {}
                ctype = citation.get("conversation_context_type") or "<missing>"
                attribution = citation.get("attribution") or "<missing>"
                citation_type_counts[ctype] += 1
                attribution_counts[attribution] += 1
                memory_id = citation.get("memory_id") or ""
                if memory_id:
                    memory_ids[memory_id] += 1
                rows.append(
                    {
                        "source_file": source_file,
                        "conversation_id": conv_id,
                        "conversation_title": title,
                        "conversation_month": month,
                        "conversation_memory_scope": str(conversation_memory_scope),
                        "message_id": msg.get("id") or node_id,
                        "message_role": ((msg.get("author") or {}).get("role")) or "",
                        "message_create_time": iso(msg.get("create_time")),
                        "status": status,
                        "citation_type": ctype,
                        "attribution": attribution,
                        "memory_id": memory_id,
                        "citation_uuid": citation.get("citation_uuid") or item.get("citation_uuid") or "",
                        "title": citation.get("title") or "",
                        "reason": citation.get("reason") or "",
                        "snippet_preview": bounded(citation.get("snippet") or "", 360),
                        "matched_text": bounded(citation.get("matched_text") or "", 180),
                        "url": citation.get("url") or "",
                        "previous_user_message_id": prev_user_id,
                        "previous_user_preview": bounded(prev_user_text, 360),
                        "assistant_message_preview": bounded(message_text(node), 360),
                    }
                )

    context_csv = OUT / "context_activation_events.csv"
    with context_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)

    source_csv = OUT / "active_source_route_events.csv"
    with source_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "conversation_id",
            "conversation_title",
            "month",
            "message_id",
            "role",
            "metadata_key",
            "value_preview",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(source_rows)

    examples = rows[:12]
    report = OUT / "context_activation_boundary_report.md"
    report.write_text(
        "\n".join(
            [
                "# Context Activation Boundary Report",
                "",
                "## Read This First",
                "",
                "This report separates passive exported data from active context-routing evidence.",
                "",
                "- Passive availability: conversation-level flags such as `memory_scope`, which say a feature was available.",
                "- Active activation: message-level metadata such as `conversation_context_citation_metadata` with `status: seeded`, `conversation_context_type`, `memory_id`, `reason`, and bounded `snippet` fields.",
                "",
                "In plain language: this is the line between data merely existing in the account/export and data being selected as context for a specific response.",
                "",
                "## Core Counts",
                "",
                f"- Context citation events: `{len(rows)}` citation objects.",
                f"- Message nodes with citation status: `{sum(status_counts.values())}`.",
                f"- Conversations with citation activation: `{len(citations_by_conversation)}`.",
                f"- Status counts: `{dict(status_counts)}`.",
                f"- Citation type counts: `{dict(citation_type_counts)}`.",
                f"- Attribution counts: `{dict(attribution_counts)}`.",
                f"- Distinct memory ids referenced: `{len(memory_ids)}`.",
                "",
                "## Active Source/Tool Route Counts",
                "",
                *[f"- `{key}`: `{count}` non-empty route events." for key, count in activation_key_counts.most_common()],
                "",
                "## Conversations With Context Citations",
                "",
                *[f"- `{title}`: `{count}` message nodes." for title, count in conversation_counts.most_common()],
                "",
                "## Interpretation",
                "",
                "The export does not merely say memory was enabled. It records specific memory or past-conversation citation objects on assistant message nodes. These citation objects include reasons and snippets. That means the system selected previously stored or retrieved context and attached it to the response path.",
                "",
                "This still does not prove model training. It is stronger and narrower evidence: active personalization/context retrieval happened in those turns.",
                "",
                "## Bounded Examples",
                "",
                *[
                    "\n".join(
                        [
                            f"### {idx}. {row['conversation_title']}",
                            "",
                            f"- Type: `{row['citation_type']}`",
                            f"- Attribution: `{row['attribution']}`",
                            f"- Status: `{row['status']}`",
                            f"- Title/reason: {row['title']} / {row['reason']}",
                            f"- Snippet: {row['snippet_preview']}",
                            f"- Previous user: {row['previous_user_preview']}",
                            f"- Assistant preview: {row['assistant_message_preview']}",
                            "",
                        ]
                    )
                    for idx, row in enumerate(examples, 1)
                ],
                "## Output Files",
                "",
                "- `context_activation_events.csv`: citation-level activation rows.",
                "- `active_source_route_events.csv`: non-empty search/source/retrieval route metadata rows.",
                "- `context_activation_boundary_report.md`: this report.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(f"Wrote {context_csv}")
    print(f"Wrote {source_csv}")
    print(f"Wrote {report}")
    print(f"context_citations={len(rows)} source_routes={len(source_rows)}")


if __name__ == "__main__":
    main()
