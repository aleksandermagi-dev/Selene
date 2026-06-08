from __future__ import annotations

import sqlite3
from typing import Any

from .c_blueprint import c_blueprint_status
from .chat import ChatGate
from .cocoon import cocoon_status
from .gates import ArchiveAuditGate, ContinuityGate, GracefulFall
from .kernel import kernel_state
from .research_integrity import AcademicWorkflowRouter, CitationIntegrity, ResearchIntegrityCore, research_integrity_report


def route_request(conn: sqlite3.Connection, route_key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if route_key == "kernel.status":
        return {"route": route_key, "result": kernel_state()}
    if route_key == "cocoon.status":
        return {"route": route_key, "result": cocoon_status()}
    if route_key == "c_blueprint.status":
        return {"route": route_key, "result": c_blueprint_status()}
    if route_key == "chat.preview":
        return {"route": route_key, "result": chat_gate_preview(conn, str(payload.get("text", "")))}
    if route_key == "provenance.classify":
        return {"route": route_key, "result": ContinuityGate().evaluate(payload).__dict__}
    if route_key == "archive.audit":
        return {"route": route_key, "result": ArchiveAuditGate().evaluate_text(str(payload.get("text", ""))).__dict__}
    if route_key == "research_integrity.status":
        return {"route": route_key, "result": research_integrity_report()}
    if route_key == "academic.classify":
        decision = AcademicWorkflowRouter.classify(str(payload.get("text", "")))
        return {"route": route_key, "result": decision.__dict__ if decision else {"route": "no_academic_workflow", "status": "none"}}
    if route_key == "citation.format":
        return {"route": route_key, "result": CitationIntegrity.format_from_metadata(payload.get("metadata") or {}, str(payload.get("style") or "APA"))}
    if route_key == "hypothesis.entry":
        return {
            "route": route_key,
            "result": ResearchIntegrityCore.build_hypothesis_entry(
                hypothesis=str(payload.get("hypothesis") or ""),
                evidence=[str(item) for item in (payload.get("evidence") or [])],
                counterarguments=[str(item) for item in (payload.get("counterarguments") or [])],
                confidence=str(payload.get("confidence") or "open"),
                next_test=str(payload.get("next_test") or "define the next bounded review or reconstruction test"),
            ),
        }
    if route_key == "case_law.candidate":
        return {
            "route": route_key,
            "result": ResearchIntegrityCore.case_law_candidate(
                law_area=str(payload.get("law_area") or "unspecified"),
                proposal=str(payload.get("proposal") or ""),
                evidence_refs=[str(item) for item in (payload.get("evidence_refs") or [])],
            ),
        }
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
