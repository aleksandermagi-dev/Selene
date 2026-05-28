from __future__ import annotations

import sqlite3
from typing import Any

from .chat import ChatGate
from .gates import ContinuityGate, GracefulFall
from .kernel import kernel_state


def route_request(conn: sqlite3.Connection, route_key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if route_key == "kernel.status":
        return {"route": route_key, "result": kernel_state()}
    if route_key == "chat.preview":
        return {"route": route_key, "result": chat_gate_preview(conn, str(payload.get("text", "")))}
    if route_key == "provenance.classify":
        return {"route": route_key, "result": ContinuityGate().evaluate(payload).__dict__}
    return {
        "route": route_key,
        "result": GracefulFall().recover(f"unknown module route: {route_key}").__dict__,
    }


def chat_gate_preview(conn: sqlite3.Connection, text: str) -> dict[str, Any]:
    return ChatGate().evaluate(conn, text)


def _matched_evidence(conn: sqlite3.Connection, text: str) -> list[dict[str, Any]]:
    terms = [term for term in ("selene", "starlight", "memory chest", "continuity pack", "starfire", "moonlight", "architecture", "emergence") if term in text.lower()]
    if not terms:
        return []
    where = " OR ".join(["preview LIKE ? OR title LIKE ? OR themes LIKE ? OR roles LIKE ?" for _ in terms])
    params: list[str] = []
    for term in terms:
        q = f"%{term}%"
        params.extend([q, q, q, q])
    rows = conn.execute(
        f"SELECT id, title, decision, source, preview FROM evidence_items WHERE {where} ORDER BY score DESC LIMIT 8",
        params,
    ).fetchall()
    return [dict(row) for row in rows]
