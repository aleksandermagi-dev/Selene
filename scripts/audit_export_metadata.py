from __future__ import annotations

import csv
import datetime as dt
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path("DevelopmentalCorpusArchive_20260526_122541/raw_export/mydataset/text_export")
OUT = Path("analysis/metadata_audit_20260605")

TRACE_KEYS = [
    "model_slug",
    "resolved_model_slug",
    "default_model_slug",
    "memory_scope",
    "is_do_not_remember",
    "is_temporary_chat",
    "plugin_ids",
    "gizmo_id",
    "search_queries",
    "search_result_groups",
    "safe_urls",
    "content_references",
    "attachments",
    "selected_sources",
    "selected_github_repos",
    "personal_sources",
    "cloud_doc_urls",
    "retrieval_search_sources",
    "retrieval_file_index",
    "retrieval_turn_number",
    "conversation_context_citation_metadata",
    "conversation_context_citation_metadata_status",
    "connectors_file_search",
    "developer_mode_connector_ids",
    "suggested_connector_ids",
    "cta_by_suggested_connector_id",
    "invoked_plugin",
    "invoked_resource",
    "permissions",
    "has_sensitive_connector_data",
    "real_author_type",
    "real_author_title",
    "real_author_id",
    "is_user_system_message",
    "user_context_message_data",
    "memory_percentage_used",
    "pending_memory_info",
    "system_hints",
    "triggered_by_system_hint_suggestion",
    "dictation",
    "real_time_audio_has_video",
    "voice_mode_message",
    "voice_session_id",
    "image_gen_task_id",
    "image_gen_group_id",
    "image_gen_async",
    "image_gen_paragen_metadata",
    "image_gen_title",
    "paragen_variants_info",
    "paragen_variant_choice",
    "search_display_string",
    "searched_display_string",
    "async_source",
    "async_task_id",
    "tool_invoked_message",
    "tool_invoking_message",
]

KEY_CATEGORIES = {
    "model_slug": ("model routing", "internal model label used on message nodes"),
    "resolved_model_slug": ("model routing", "resolved internal model label, often on later user/assistant turns"),
    "default_model_slug": ("model routing", "conversation-level default model selector"),
    "memory_scope": ("memory", "conversation-level memory availability flag"),
    "is_do_not_remember": ("memory", "conversation-level do-not-remember flag"),
    "is_temporary_chat": ("memory", "temporary chat flag"),
    "plugin_ids": ("plugins/connectors", "conversation-level plugin ids"),
    "gizmo_id": ("custom GPT / gizmo", "custom GPT/gizmo identifier"),
    "search_queries": ("web/search", "queries sent to search tooling"),
    "search_result_groups": ("web/search", "search result snippets and URLs returned to the model/UI"),
    "safe_urls": ("web/search", "URLs marked safe/renderable by browsing/search UI"),
    "content_references": ("sources/media", "source footnotes, images, and media references"),
    "attachments": ("files", "uploaded or attached file references"),
    "selected_sources": ("connectors/retrieval", "selected retrieval sources"),
    "selected_github_repos": ("connectors/retrieval", "selected GitHub repositories"),
    "personal_sources": ("connectors/retrieval", "personal source references"),
    "cloud_doc_urls": ("connectors/retrieval", "cloud document URLs"),
    "retrieval_search_sources": ("connectors/retrieval", "retrieval source selectors"),
    "retrieval_file_index": ("connectors/retrieval", "retrieval file index"),
    "retrieval_turn_number": ("connectors/retrieval", "retrieval turn index"),
    "conversation_context_citation_metadata": ("connectors/retrieval", "conversation context citation metadata"),
    "conversation_context_citation_metadata_status": ("connectors/retrieval", "status for context citation metadata"),
    "connectors_file_search": ("connectors/retrieval", "connector file-search marker"),
    "developer_mode_connector_ids": ("connectors/retrieval", "developer-mode connector ids"),
    "suggested_connector_ids": ("connectors/retrieval", "connector ids suggested by UI/system"),
    "cta_by_suggested_connector_id": ("connectors/retrieval", "UI CTA metadata for suggested connectors"),
    "invoked_plugin": ("plugins/connectors", "plugin invocation marker"),
    "invoked_resource": ("plugins/connectors", "resource invocation marker"),
    "permissions": ("permissions", "tool or feature permissions metadata"),
    "has_sensitive_connector_data": ("connectors/retrieval", "sensitive connector-data marker"),
    "real_author_type": ("automation", "real author type for automated user-role messages"),
    "real_author_title": ("automation", "automation title"),
    "real_author_id": ("automation", "automation id"),
    "is_user_system_message": ("custom instructions", "user custom-instruction/system context flag"),
    "user_context_message_data": ("custom instructions", "stored user custom instruction payload"),
    "memory_percentage_used": ("memory", "memory usage percentage marker"),
    "pending_memory_info": ("memory", "pending memory info marker"),
    "system_hints": ("routing/hints", "system hint for a turn, such as reason or picture"),
    "triggered_by_system_hint_suggestion": ("routing/hints", "whether a system hint suggestion triggered a turn"),
    "dictation": ("voice/input", "dictation metadata marker"),
    "real_time_audio_has_video": ("voice/input", "voice/video session marker"),
    "voice_mode_message": ("voice/input", "voice mode message marker"),
    "voice_session_id": ("voice/input", "voice session identifier"),
    "image_gen_task_id": ("image generation", "image generation task id / service route"),
    "image_gen_group_id": ("image generation", "image generation group id"),
    "image_gen_async": ("image generation", "async image generation marker"),
    "image_gen_paragen_metadata": ("image generation", "image generation/paragen metadata"),
    "image_gen_title": ("image generation", "generated image title"),
    "paragen_variants_info": ("variant generation", "parallel generation variant metadata"),
    "paragen_variant_choice": ("variant generation", "selected generated variant id"),
    "search_display_string": ("web/search", "UI text for search in progress"),
    "searched_display_string": ("web/search", "UI text for completed search"),
    "async_source": ("async/background", "async source id"),
    "async_task_id": ("async/background", "async task id"),
    "tool_invoked_message": ("tool/app bridge", "tool/app bridge invoked label"),
    "tool_invoking_message": ("tool/app bridge", "tool/app bridge invoking label"),
}


def safe_json(value: object, max_len: int = 500) -> str:
    try:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        text = str(value)
    text = re.sub(r"\s+", " ", text)
    return text[:max_len]


def month_from_ts(ts: object) -> str:
    if isinstance(ts, (int, float)):
        return dt.datetime.fromtimestamp(ts).strftime("%Y-%m")
    return "unknown"


def get_domain(raw_url: str, bad_urls: Counter[str]) -> str:
    try:
        return urlparse(raw_url).netloc.lower()
    except Exception:
        bad_urls[raw_url[:180]] += 1
        return ""


def iter_conversations() -> list[tuple[Path, dict]]:
    rows: list[tuple[Path, dict]] = []
    for path in [ROOT / "conversations-000.json", ROOT / "conversations-001.json"]:
        data = json.loads(path.read_text(encoding="utf-8"))
        rows.extend((path, conv) for conv in data)
    return rows


def add_trace(
    traces: list[dict],
    key_counts: dict[str, dict],
    *,
    source_file: str,
    conversation: dict,
    message_id: str,
    role: str,
    content_type: str,
    key: str,
    value: object,
) -> None:
    category, inferred_purpose = KEY_CATEGORIES.get(key, ("other", "unclassified metadata"))
    value_preview = safe_json(value)
    month = month_from_ts(conversation.get("create_time"))
    row = {
        "source_file": source_file,
        "conversation_id": conversation.get("id") or "",
        "conversation_title": conversation.get("title") or "",
        "month": month,
        "message_id": message_id,
        "role": role,
        "content_type": content_type,
        "metadata_key": key,
        "category": category,
        "inferred_purpose": inferred_purpose,
        "value_preview": value_preview,
    }
    traces.append(row)
    summary = key_counts.setdefault(
        key,
        {
            "count": 0,
            "conversations": set(),
            "months": Counter(),
            "roles": Counter(),
            "content_types": Counter(),
            "values": Counter(),
            "category": category,
            "inferred_purpose": inferred_purpose,
        },
    )
    summary["count"] += 1
    summary["conversations"].add(row["conversation_id"])
    summary["months"][month] += 1
    summary["roles"][role] += 1
    summary["content_types"][content_type] += 1
    summary["values"][safe_json(value, 180)] += 1


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conversations = iter_conversations()
    traces: list[dict] = []
    key_counts: dict[str, dict] = {}
    content_type_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    domain_counts: Counter[str] = Counter()
    search_domain_counts: Counter[str] = Counter()
    safe_url_domain_counts: Counter[str] = Counter()
    bad_urls: Counter[str] = Counter()
    model_by_month: dict[str, Counter[str]] = {}

    for path, conv in conversations:
        conv_message = {"author": {"role": "<conversation>"}, "content": {"content_type": "<conversation>"}}
        for key in ["plugin_ids", "memory_scope", "default_model_slug", "is_do_not_remember", "is_temporary_chat"]:
            add_trace(
                traces,
                key_counts,
                source_file=path.name,
                conversation=conv,
                message_id="<conversation>",
                role="<conversation>",
                content_type="<conversation>",
                key=key,
                value=conv.get(key),
            )
        month = month_from_ts(conv.get("create_time"))
        for message_id, node in (conv.get("mapping") or {}).items():
            msg = node.get("message") or {}
            role = (msg.get("author") or {}).get("role") or "<missing>"
            content = msg.get("content") or {}
            content_type = content.get("content_type") if isinstance(content, dict) else "<missing>"
            role_counts[role] += 1
            content_type_counts[content_type] += 1
            metadata = msg.get("metadata") or {}
            for key, value in metadata.items():
                if key in TRACE_KEYS:
                    add_trace(
                        traces,
                        key_counts,
                        source_file=path.name,
                        conversation=conv,
                        message_id=message_id,
                        role=role,
                        content_type=content_type,
                        key=key,
                        value=value,
                    )
                    if key in {"model_slug", "resolved_model_slug"} and value:
                        model_by_month.setdefault(month, Counter())[str(value)] += 1
            blob = json.dumps(msg, ensure_ascii=False)
            for raw_url in re.findall(r"https?://[^\s\"<>\\\\]+", blob):
                domain = get_domain(raw_url, bad_urls)
                if domain:
                    domain_counts[domain] += 1
            safe_urls = metadata.get("safe_urls")
            if isinstance(safe_urls, list):
                for raw_url in safe_urls:
                    if isinstance(raw_url, str) and raw_url.startswith("http"):
                        domain = get_domain(raw_url, bad_urls)
                        if domain:
                            safe_url_domain_counts[domain] += 1
            search_groups = metadata.get("search_result_groups")
            if isinstance(search_groups, list):
                for group in search_groups:
                    if not isinstance(group, dict):
                        continue
                    for entry in group.get("entries") or []:
                        if isinstance(entry, dict) and isinstance(entry.get("url"), str):
                            domain = get_domain(entry["url"], bad_urls)
                            if domain:
                                search_domain_counts[domain] += 1

    with (OUT / "metadata_traces.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(traces[0].keys()))
        writer.writeheader()
        writer.writerows(traces)

    key_rows = []
    for key, summary in sorted(key_counts.items(), key=lambda item: (-item[1]["count"], item[0])):
        key_rows.append(
            {
                "metadata_key": key,
                "category": summary["category"],
                "inferred_purpose": summary["inferred_purpose"],
                "count": summary["count"],
                "conversation_count": len(summary["conversations"]),
                "top_roles": "; ".join(f"{k}:{v}" for k, v in summary["roles"].most_common(6)),
                "top_content_types": "; ".join(f"{k}:{v}" for k, v in summary["content_types"].most_common(6)),
                "top_months": "; ".join(f"{k}:{v}" for k, v in summary["months"].most_common(8)),
                "top_values": " || ".join(f"{v}x {k}" for k, v in summary["values"].most_common(8)),
            }
        )
    with (OUT / "metadata_key_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(key_rows[0].keys()))
        writer.writeheader()
        writer.writerows(key_rows)

    def top_dict(counter: Counter[str], limit: int = 80) -> list[dict[str, object]]:
        return [{"value": key, "count": count} for key, count in counter.most_common(limit)]

    machine = {
        "conversation_count": len(conversations),
        "message_count": sum(role_counts.values()),
        "role_counts": dict(role_counts),
        "content_type_counts": dict(content_type_counts),
        "metadata_key_count": len(key_counts),
        "trace_count": len(traces),
        "metadata_keys": key_rows,
        "top_url_domains_anywhere": top_dict(domain_counts),
        "top_search_domains": top_dict(search_domain_counts),
        "top_safe_url_domains": top_dict(safe_url_domain_counts),
        "bad_urls": top_dict(bad_urls, 30),
        "model_by_month": {
            month: [{"model": model, "count": count} for model, count in counter.most_common()]
            for month, counter in sorted(model_by_month.items())
        },
    }
    (OUT / "metadata_trace_summary.json").write_text(json.dumps(machine, indent=2, ensure_ascii=False), encoding="utf-8")

    report = [
        "# Metadata Routing And Privacy Trace Audit",
        "",
        "Date: 2026-06-05",
        "",
        "Scope: raw ChatGPT export JSON only. This audit can identify metadata preserved in the export; it cannot prove server-side data sharing that is not represented in the export.",
        "",
        "## Totals",
        "",
        f"- Conversations: `{len(conversations)}`",
        f"- Message nodes: `{sum(role_counts.values())}`",
        f"- Metadata trace rows: `{len(traces)}`",
        f"- Distinct audited metadata keys: `{len(key_counts)}`",
        "",
        "## Highest-Volume Trace Keys",
        "",
        "| Key | Category | Count | Conversations | Inferred purpose |",
        "|---|---|---:|---:|---|",
    ]
    for row in key_rows[:30]:
        report.append(
            f"| `{row['metadata_key']}` | {row['category']} | {row['count']} | {row['conversation_count']} | {row['inferred_purpose']} |"
        )
    report.extend(
        [
            "",
            "## Who / Destination Reading",
            "",
            "The export does not contain a full recipient ledger. It does preserve destination-like traces for tools, model routing, web/search domains, image-generation task routes, connectors, automations, and custom GPT/gizmo ids.",
            "",
            "Observed destination-like categories:",
            "",
            "- OpenAI/ChatGPT internal model routing labels: `model_slug`, `resolved_model_slug`, `default_model_slug`.",
            "- Web/search source domains in `search_result_groups` and `safe_urls`.",
            "- Image generation task route strings in `image_gen_task_id`.",
            "- Connector/retrieval flags such as `selected_sources`, `selected_github_repos`, `personal_sources`, `connectors_file_search`, and `has_sensitive_connector_data`.",
            "- Automation markers in `real_author_type`, `real_author_title`, and `real_author_id`.",
            "- Custom GPT/gizmo ids in `gizmo_id`.",
            "",
            "Not observed as conversation-level plugin use:",
            "",
            "- `plugin_ids` exists on all 149 conversations but is `null` for all 149.",
            "",
            "## Purpose Reading",
            "",
            "The metadata appears to support these purposes:",
            "",
            "- model selection/routing",
            "- memory availability and memory usage tracking",
            "- web/search retrieval and citation display",
            "- source and URL safety/display",
            "- file/image attachment handling",
            "- connector/retrieval features",
            "- custom instructions/user context injection",
            "- automated reminders or scheduled messages",
            "- image generation and parallel generation variants",
            "- tool/app bridge status",
            "",
            "## Top External Domains In Exported URL Traces",
            "",
            "| Domain | Count |",
            "|---|---:|",
        ]
    )
    for item in top_dict(domain_counts, 25):
        report.append(f"| `{item['value']}` | {item['count']} |")
    report.extend(
        [
            "",
            "## Important Limits",
            "",
            "- This does not prove which systems retained data outside the export.",
            "- This does not prove training use.",
            "- This does not prove third-party disclosure beyond tool/search/source traces visible in the export.",
            "- Search result URLs are often retrieval/display metadata, not evidence that the user's private data was sent to each domain.",
            "- Connector flags indicate feature/path presence, but the audit needs a second pass to inspect each connector trace in context.",
            "",
            "## Output Files",
            "",
            "- `metadata_traces.csv`: every audited metadata trace row.",
            "- `metadata_key_audit.csv`: per-key counts, categories, and top values.",
            "- `metadata_trace_summary.json`: machine-readable summary.",
        ]
    )
    (OUT / "metadata_routing_privacy_audit.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
