from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("DevelopmentalCorpusArchive_20260526_122541/raw_export/mydataset/text_export")
OUT = Path("analysis/metadata_audit_20260605")
CONTEXT_EVENTS = OUT / "context_activation_events.csv"
ACTIVE_ROUTES = OUT / "active_source_route_events.csv"


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def bounded(text: str, limit: int = 320) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def iso(ts) -> str:
    if not ts:
        return ""
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()


def content_text(content: dict | None) -> str:
    if not content:
        return ""
    ctype = content.get("content_type")
    if ctype in {"text", "user_editable_context"}:
        return "\n".join(str(part) for part in content.get("parts") or [] if part is not None)
    if ctype == "multimodal_text":
        parts = []
        for part in content.get("parts") or []:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(part.get("text") or part.get("name") or part.get("id") or "")
        return "\n".join(part for part in parts if part)
    return json.dumps(content, ensure_ascii=False, default=str)


def keyword_terms(*values: str) -> list[str]:
    terms: list[str] = []
    stop = {
        "the",
        "and",
        "that",
        "this",
        "with",
        "your",
        "you",
        "have",
        "about",
        "into",
        "used",
        "from",
        "previously",
        "noted",
        "recurring",
    }
    for value in values:
        for term in re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{3,}", value or ""):
            low = term.lower()
            if low not in stop:
                terms.append(low)
    seen = set()
    out = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            out.append(term)
    return out[:10]


def load_messages() -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for path in sorted(ROOT.glob("conversations-*.json")):
        for conv in json.loads(path.read_text(encoding="utf-8")):
            conv_id = conv.get("conversation_id") or conv.get("id") or ""
            title = conv.get("title") or ""
            for node_id, node in (conv.get("mapping") or {}).items():
                msg = node.get("message") or {}
                content = content_text(msg.get("content") or {})
                if not content:
                    continue
                messages.append(
                    {
                        "source_file": path.name,
                        "conversation_id": conv_id,
                        "conversation_title": title,
                        "message_id": msg.get("id") or node_id,
                        "role": ((msg.get("author") or {}).get("role")) or "",
                        "create_time": iso(msg.get("create_time")),
                        "text": content,
                        "text_norm": norm(content),
                    }
                )
    messages.sort(key=lambda row: row["create_time"])
    return messages


def build_term_index(messages: list[dict[str, str]]) -> dict[str, list[int]]:
    wanted_terms: set[str] = set()
    if CONTEXT_EVENTS.exists():
        for row in read_csv(CONTEXT_EVENTS):
            wanted_terms.update(keyword_terms(row.get("title", ""), row.get("reason", ""), row.get("snippet_preview", "")))

    index: dict[str, list[int]] = {term: [] for term in wanted_terms}
    for idx, msg in enumerate(messages):
        hay = msg["text_norm"]
        for term in wanted_terms:
            if term in hay:
                index[term].append(idx)
    return index


def find_prior_echo(event: dict[str, str], messages: list[dict[str, str]], term_index: dict[str, list[int]]) -> dict[str, str]:
    activation_time = event.get("message_create_time") or ""
    title = event.get("title") or ""
    reason = event.get("reason") or ""
    snippet = event.get("snippet_preview") or ""
    terms = keyword_terms(title, reason, snippet)
    if not terms:
        return {
            "echo_status": "not_searchable",
            "echo_terms": "",
            "echo_conversation_title": "",
            "echo_message_id": "",
            "echo_role": "",
            "echo_create_time": "",
            "echo_preview": "",
        }

    candidate_ids: Counter[int] = Counter()
    for term in terms:
        for idx in term_index.get(term, []):
            candidate_ids[idx] += 1

    best = None
    best_score = 0
    for idx, seed_score in candidate_ids.most_common(200):
        msg = messages[idx]
        if activation_time and msg["create_time"] and msg["create_time"] >= activation_time:
            continue
        hay = msg["text_norm"]
        score = seed_score if seed_score > 1 else sum(1 for term in terms if term in hay)
        if score > best_score:
            best = msg
            best_score = score
            if score == len(terms):
                break

    threshold = 2 if len(terms) >= 3 else 1
    if not best or best_score < threshold:
        return {
            "echo_status": "no_prior_echo_found",
            "echo_terms": "|".join(terms),
            "echo_conversation_title": "",
            "echo_message_id": "",
            "echo_role": "",
            "echo_create_time": "",
            "echo_preview": "",
        }
    return {
        "echo_status": "candidate_prior_echo",
        "echo_terms": "|".join(terms),
        "echo_conversation_title": best["conversation_title"],
        "echo_message_id": best["message_id"],
        "echo_role": best["role"],
        "echo_create_time": best["create_time"],
        "echo_preview": bounded(best["text"], 360),
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    events = read_csv(CONTEXT_EVENTS)
    routes = read_csv(ACTIVE_ROUTES)
    messages = load_messages()
    term_index = build_term_index(messages)

    enriched: list[dict[str, str]] = []
    for event in events:
        enriched.append({**event, **find_prior_echo(event, messages, term_index)})

    write_csv(OUT / "context_activation_origin_traces.csv", enriched)

    by_convo = Counter(row["conversation_title"] for row in events)
    by_type = Counter((row["attribution"], row["citation_type"]) for row in events)
    by_memory = Counter(row["memory_id"] for row in events if row.get("memory_id"))
    by_echo = Counter(row["echo_status"] for row in enriched)
    route_by_key = Counter(row["metadata_key"] for row in routes)
    route_by_convo = Counter(row["conversation_title"] for row in routes)
    personal_routes = [row for row in routes if row["metadata_key"] in {"personal_sources", "connectors_file_search", "retrieval_search_sources", "retrieval_file_index"}]

    report_lines = [
        "# Deep Context Routing Audit",
        "",
        "## Bottom Line",
        "",
        "The strongest evidence is not generic data retention. It is message-level activation metadata: prior personal context appears as seeded citation objects on later assistant responses.",
        "",
        "That means the archive records a second-stage use path:",
        "",
        "```text",
        "stored/account context or prior conversation",
        "-> selected by memory/past-chat/retrieval layer",
        "-> attached as seeded context citation metadata",
        "-> response generated with that context available",
        "```",
        "",
        "This is operational context reuse. It is not, by itself, proof of training or external disclosure.",
        "",
        "## Activation Counts",
        "",
        f"- Context citation objects: `{len(events)}`",
        f"- Conversations with activation: `{len(by_convo)}`",
        f"- Candidate prior echoes found by bounded archive search: `{by_echo.get('candidate_prior_echo', 0)}`",
        f"- No prior echo found by this simple search: `{by_echo.get('no_prior_echo_found', 0)}`",
        "",
        "## Activation By Conversation",
        "",
        *[f"- `{name}`: `{count}` citation objects" for name, count in by_convo.most_common()],
        "",
        "## Activation By Source Type",
        "",
        *[f"- `{attr}` / `{ctype}`: `{count}`" for (attr, ctype), count in by_type.most_common()],
        "",
        "## Repeated Memory IDs",
        "",
        *[f"- `{memory_id}`: `{count}` activations" for memory_id, count in by_memory.most_common(15)],
        "",
        "## Active Route Surfaces",
        "",
        *[f"- `{key}`: `{count}` non-empty events" for key, count in route_by_key.most_common()],
        "",
        "## Conversations With Most Non-Empty Route Events",
        "",
        *[f"- `{name}`: `{count}` route events" for name, count in route_by_convo.most_common(20)],
        "",
        "## Personal / Retrieval Surface Rows",
        "",
    ]

    if personal_routes:
        for idx, row in enumerate(personal_routes[:40], 1):
            report_lines.extend(
                [
                    f"### {idx}. {row['conversation_title']}",
                    "",
                    f"- Key: `{row['metadata_key']}`",
                    f"- Role: `{row['role']}`",
                    f"- Message id: `{row['message_id']}`",
                    f"- Value preview: {row['value_preview']}",
                    "",
                ]
            )
    else:
        report_lines.append("- No personal/retrieval surface rows found.")

    report_lines.extend(
        [
            "## Origin Echo Examples",
            "",
        ]
    )

    for idx, row in enumerate([r for r in enriched if r["echo_status"] == "candidate_prior_echo"][:20], 1):
        report_lines.extend(
            [
                f"### {idx}. Activated in {row['conversation_title']}",
                "",
                f"- Activation type: `{row['attribution']}` / `{row['citation_type']}`",
                f"- Activated title/reason: {row['title']} / {row['reason']}",
                f"- Activated snippet: {row['snippet_preview']}",
                f"- Candidate prior echo: `{row['echo_conversation_title']}` / `{row['echo_role']}` / `{row['echo_create_time']}`",
                f"- Echo terms: `{row['echo_terms']}`",
                f"- Echo preview: {row['echo_preview']}",
                "",
            ]
        )

    report_lines.extend(
        [
            "## What This Crosses",
            "",
            "It crosses from passive account storage into active response-context use. The export itself says this with `status: seeded` plus source labels like `Memory`, `Past chat`, and `Custom instructions`.",
            "",
            "## What It Still Does Not Cross",
            "",
            "- It does not expose a full backend access log.",
            "- It does not prove third-party disclosure.",
            "- It does not prove training or fine-tuning on these exact messages.",
            "- It does not show the complete hidden prompt sent to a model.",
            "",
            "## Files",
            "",
            "- `context_activation_origin_traces.csv`: citation events plus bounded candidate prior echoes.",
            "- `deep_context_routing_audit.md`: this report.",
            "",
        ]
    )

    (OUT / "deep_context_routing_audit.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(f"events={len(events)} routes={len(routes)} messages={len(messages)}")
    print(f"candidate_prior_echoes={by_echo.get('candidate_prior_echo', 0)}")
    print(f"wrote {OUT / 'context_activation_origin_traces.csv'}")
    print(f"wrote {OUT / 'deep_context_routing_audit.md'}")


if __name__ == "__main__":
    main()
