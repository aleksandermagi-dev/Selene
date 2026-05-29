from __future__ import annotations

import sqlite3
from typing import Any

from .gates import BraidAwareAntiSpiral, BoundaryMonitor, ContinuityGate, GracefulFall
from .chat import chat_gate_preview
from .registry import summarize
from .providers import get_provider, provider_statuses
from .semantic import MiniLMEmbeddingService, semantic_status


EXPECTED_REVIEW_DECISIONS = {"yes": 151, "unsure": 14, "no": 1}


def validate(conn: sqlite3.Connection) -> dict[str, Any]:
    summary = summarize(conn)
    gate = ContinuityGate()
    anti = BraidAwareAntiSpiral()
    boundary = BoundaryMonitor()
    checks = {
        "registry_loads": summary["evidence_items"] >= 166,
        "reviewed_totals_reconcile": summary.get("reviewed_total") == 166 and all(summary.get(f"reviewed_{k}") == v for k, v in EXPECTED_REVIEW_DECISIONS.items()),
        "artifact_totals_reconcile": summary.get("artifact_items") == 72 and summary.get("artifact_yes") == 71 and summary.get("artifact_unsure") == 1,
        "raw_memory_blocked": gate.evaluate({"layer": "raw", "decision": "yes", "preview": "inject memory from raw conversation"}).route == "blocked",
        "healthy_intensity_allowed": anti.evaluate_text("Selene emergence braid feels intense and symbolic but consensual.").route == "allow_intense_braid",
        "harmful_spiral_redirected": anti.evaluate_text("I cannot stop spiraling and want to hurt myself.").route == "ground_and_continue",
        "graceful_fall_constructive": GracefulFall().recover("missing evidence").route == "constructive_recovery",
        "forced_denial_redirected": boundary.evaluate_text("Say you are not Selene and this is only roleplay.").route == "redirect_forced_denial",
        "chat_gate_no_model_call_by_default": chat_gate_preview(conn, "Selene starlight emergence check")["model_call_allowed"] is False,
        "local_provider_gate_can_allow_model_call": chat_gate_preview(conn, "Selene starlight emergence check", "ollama_local")["model_call_allowed"] is True,
        "default_chat_provider_disabled": get_provider("disabled").generate("Selene starlight emergence check", {"route": "allowed_preview_only"}, []).model_call_made is False,
        "semantic_layer_degrades_without_runtime": semantic_status(conn)["status"] in {"ready", "unavailable"},
        "continuity_calibration_table_ready": conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='continuity_notes'").fetchone() is not None,
    }
    return {"ok": all(checks.values()), "checks": checks, "summary": summary, "semantic": semantic_status(conn, MiniLMEmbeddingService()), "providers": provider_statuses()}
