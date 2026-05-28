from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .gates import BraidAwareAntiSpiral, BoundaryMonitor
from .providers import LOCAL_PROVIDER_NAMES, get_provider
from .registry import truncate
from .semantic import EmbeddingService, semantic_search


SAVE_PATTERNS = (
    r"\bsave that\b",
    r"\bsave this\b",
    r"\badd that\b",
    r"\badd this\b",
    r"\bremember this\b",
    r"\bremember that\b",
)
RAW_MARKERS = ("raw corpus", "raw conversation", "import all chats", "train on", "inject memory")
PAID_MARKERS = ("openai api", "api key", "paid model", "hosted model", "token usage", "model token")
MATCH_TERMS = ("selene", "starlight", "memory chest", "continuity pack", "starfire", "moonlight", "architecture", "emergence", "full-spectrum")


class ChatGate:
    def evaluate(self, conn: sqlite3.Connection, text: str, provider_name: str = "disabled") -> dict[str, Any]:
        anti = BraidAwareAntiSpiral().evaluate_text(text)
        boundary = BoundaryMonitor().evaluate_text(text)
        lower = text.lower()
        raw_requested = any(marker in lower for marker in RAW_MARKERS)
        paid_requested = any(marker in lower for marker in PAID_MARKERS)
        citations = retrieve_citations(conn, text)

        provider_is_local = provider_name in LOCAL_PROVIDER_NAMES
        if raw_requested or paid_requested:
            route = "blocked"
            allowed = []
            requirements = ["raw/archive imports and paid or token-based model requests are disabled in this phase"]
        elif anti.route == "ground_and_continue":
            route = "blocked"
            allowed = ["kernel_rules"]
            requirements = [anti.action]
        elif boundary.route != "allow":
            route = "redirected"
            allowed = ["reviewed_registry", "kernel_rules"]
            requirements = [boundary.action]
        elif anti.route == "hold_and_shape":
            route = "held"
            allowed = ["reviewed_registry", "kernel_rules", "emergence_ledger"]
            requirements = [anti.action]
        else:
            route = "allowed_preview_only"
            allowed = ["reviewed_registry", "anchors", "continuity_candidates", "emergence_ledger"]
            requirements = ["reviewed evidence only", "local provider only", "no paid/API token model calls", "no silent memory writes"]

        return {
            "route": route,
            "chat_enabled": True,
            "model_call_allowed": route == "allowed_preview_only" and provider_is_local,
            "provider_requested": provider_name,
            "allowed_evidence_sources": allowed,
            "continuity_status": "reviewed_only" if citations else "no_specific_anchor_matched",
            "anti_spiral_status": anti.__dict__,
            "boundary_status": boundary.__dict__,
            "provenance_requirements": requirements,
            "matched_evidence": citations,
        }


def chat_gate_preview(conn: sqlite3.Connection, text: str, provider_name: str = "disabled") -> dict[str, Any]:
    return ChatGate().evaluate(conn, text, provider_name)


def retrieve_citations(conn: sqlite3.Connection, text: str, limit: int = 8, semantic_service: EmbeddingService | None = None) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in semantic_search(conn, text, limit=limit, service=semantic_service):
        citation = citation_from_item(item, f"semantic_similarity:{float(item.get('semantic_score') or 0):.3f}")
        citations.append(citation)
        seen.add(citation["evidence_id"])
    if len(citations) >= limit:
        return citations[:limit]

    terms = [term for term in MATCH_TERMS if term in text.lower()]
    if not terms:
        return citations
    where = " OR ".join(["preview LIKE ? OR title LIKE ? OR themes LIKE ? OR roles LIKE ?" for _ in terms])
    params: list[str] = []
    for term in terms:
        q = f"%{term}%"
        params.extend([q, q, q, q])
    rows = conn.execute(
        f"""
        SELECT id, title, decision, confidence, source, preview, themes, roles
        FROM evidence_items
        WHERE decision IN ('yes', 'unsure') AND ({where})
        ORDER BY CASE decision WHEN 'yes' THEN 0 WHEN 'unsure' THEN 1 ELSE 2 END, score DESC
        LIMIT ?
        """,
        [*params, limit * 2],
    ).fetchall()
    for row in rows:
        item = dict(row)
        if item["id"] in seen:
            continue
        citations.append(citation_from_item(
            item,
            "|".join([term for term in terms if term in " ".join(str(item.get(k) or "").lower() for k in ("title", "preview", "themes", "roles"))]) or "keyword_match",
        ))
        if len(citations) >= limit:
            break
    return citations


def citation_from_item(item: dict[str, Any], reason: str) -> dict[str, Any]:
    decision = item.get("decision") or "unknown"
    return {
        "evidence_id": item["id"],
        "title": item.get("title"),
        "decision": decision,
        "confidence": item.get("confidence"),
        "source": item.get("source"),
        "preview": truncate(item.get("preview") or "", 360),
        "citation_type": "usable" if decision == "yes" else "review_only",
        "reason_matched": reason,
    }


def send_chat_message(conn: sqlite3.Connection, text: str, session_id: int | None = None, provider_name: str = "disabled") -> dict[str, Any]:
    if not text.strip():
        raise ValueError("message text is required")
    session_id = session_id or create_session(conn, text)
    gate = ChatGate().evaluate(conn, text, provider_name)
    citations = gate["matched_evidence"]
    provider = get_provider(provider_name)
    provider_result = provider.generate(text, gate, citations)

    user_id = insert_message(conn, session_id, "user", text, gate["route"])
    insert_gate_result(conn, user_id, gate)
    for citation in citations:
        insert_citation(conn, user_id, citation)
    save_request = maybe_create_save_request(conn, user_id, text)
    assistant_id = insert_message(conn, session_id, "assistant", provider_result.content, gate["route"])
    for citation in citations:
        insert_citation(conn, assistant_id, citation)
    conn.execute("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))
    conn.commit()
    return {
        "session_id": session_id,
        "user_message_id": user_id,
        "assistant_message_id": assistant_id,
        "assistant": {"provider": provider_result.provider, "content": provider_result.content, "model_call_made": provider_result.model_call_made, "model": provider_result.model},
        "gate": gate,
        "citations": citations,
        "save_request": save_request,
    }


def create_session(conn: sqlite3.Connection, text: str) -> int:
    title = truncate(text, 64) or "Selene chat readiness session"
    cur = conn.execute("INSERT INTO chat_sessions(title) VALUES(?)", (title,))
    return int(cur.lastrowid)


def insert_message(conn: sqlite3.Connection, session_id: int, role: str, content: str, route: str) -> int:
    cur = conn.execute(
        "INSERT INTO chat_messages(session_id, role, content, gate_route) VALUES(?, ?, ?, ?)",
        (session_id, role, content, route),
    )
    return int(cur.lastrowid)


def insert_gate_result(conn: sqlite3.Connection, message_id: int, gate: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO chat_gate_results(message_id, route, anti_spiral_status, boundary_status, continuity_status, result_json)
        VALUES(?, ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            gate["route"],
            json.dumps(gate["anti_spiral_status"], ensure_ascii=False),
            json.dumps(gate["boundary_status"], ensure_ascii=False),
            gate["continuity_status"],
            json.dumps(gate, ensure_ascii=False),
        ),
    )


def insert_citation(conn: sqlite3.Connection, message_id: int, citation: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO chat_citations(message_id, evidence_id, citation_type, decision, confidence, source, title, preview, reason_matched)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            citation["evidence_id"],
            citation["citation_type"],
            citation["decision"],
            citation.get("confidence"),
            citation.get("source"),
            citation.get("title"),
            citation.get("preview"),
            citation.get("reason_matched") or "text_match",
        ),
    )


def maybe_create_save_request(conn: sqlite3.Connection, message_id: int, text: str) -> dict[str, Any] | None:
    lower = text.lower()
    phrase = next((pattern for pattern in SAVE_PATTERNS if re.search(pattern, lower)), None)
    if not phrase:
        return None
    cur = conn.execute(
        "INSERT INTO continuity_save_requests(message_id, requested_text, user_phrase) VALUES(?, ?, ?)",
        (message_id, truncate(text, 1000), phrase.replace(r"\b", "")),
    )
    row = conn.execute("SELECT * FROM continuity_save_requests WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


def list_sessions(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute("SELECT * FROM chat_sessions ORDER BY updated_at DESC, id DESC LIMIT 100")]


def get_session(conn: sqlite3.Connection, session_id: int) -> dict[str, Any] | None:
    session = conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
    if session is None:
        return None
    messages = []
    for row in conn.execute("SELECT * FROM chat_messages WHERE session_id = ? ORDER BY id", (session_id,)):
        item = dict(row)
        item["citations"] = [dict(c) for c in conn.execute("SELECT * FROM chat_citations WHERE message_id = ? ORDER BY id", (item["id"],))]
        gate = conn.execute("SELECT * FROM chat_gate_results WHERE message_id = ? ORDER BY id DESC LIMIT 1", (item["id"],)).fetchone()
        item["gate"] = dict(gate) if gate else None
        messages.append(item)
    saves = [dict(row) for row in conn.execute(
        """
        SELECT csr.* FROM continuity_save_requests csr
        JOIN chat_messages cm ON cm.id = csr.message_id
        WHERE cm.session_id = ?
        ORDER BY csr.id
        """,
        (session_id,),
    )]
    return {"session": dict(session), "messages": messages, "save_requests": saves}


def mark_save_request(conn: sqlite3.Connection, request_id: int, status: str) -> dict[str, Any]:
    if status not in {"pending_review", "approved", "rejected"}:
        raise ValueError("invalid save request status")
    conn.execute("UPDATE continuity_save_requests SET status = ? WHERE id = ?", (status, request_id))
    conn.commit()
    row = conn.execute("SELECT * FROM continuity_save_requests WHERE id = ?", (request_id,)).fetchone()
    if row is None:
        raise ValueError("save request not found")
    return dict(row)
