from __future__ import annotations

import json
import sqlite3
from typing import Any

from .registry import truncate


READ_SUFFIXES = (
    ".status",
    ".list",
    ".items",
    ".get",
    ".preview",
    ".readiness",
    ".health",
    ".events",
)
MUTATION_ACTIONS = {
    "approve",
    "pause",
    "decide",
    "create",
    "propose",
    "enable",
    "disable",
    "start",
    "complete",
    "save",
    "teach",
    "acquire",
    "integrate",
    "express",
    "reopen",
    "supersede",
    "reject",
    "update",
    "set",
    "prepare",
    "record",
    "review",
    "capture",
    "send",
}


def derive_authority_event(
    route_key: str,
    payload: dict[str, Any] | None,
    result: Any,
) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    result_dict = result if isinstance(result, dict) else {}
    route = truncate(str(route_key or "unknown"), 240)
    requested_mutation = _mutation_requested(route)
    blocked = _blocked_result(result_dict)
    performed = bool(requested_mutation and not blocked)
    mutation_class = _mutation_class(route) if performed else "none"
    actor = truncate(
        str(payload.get("actor") or payload.get("approved_by") or "local_caller"),
        120,
    )
    recipient = truncate(
        str(
            payload.get("recipient")
            or payload.get("to")
            or payload.get("contact_id")
            or ""
        ),
        240,
    )
    consent_record = truncate(
        str(
            payload.get("authorization_id")
            or payload.get("approval_phrase")
            or payload.get("decision")
            or payload.get("qa_review_receipt")
            or ""
        ),
        240,
    )
    return {
        "status": "typed_authority_event_derived",
        "route_key": route,
        "actor": actor,
        "scope": route.split(".", 1)[0] if "." in route else route,
        "recipient": recipient,
        "consent_record": consent_record,
        "mutation_requested": requested_mutation,
        "performed_mutation": performed,
        "mutation_class": mutation_class,
        "reviewed_memory_write_occurred": bool(
            result_dict.get("reviewed_memory_write_occurred") is True
            or mutation_class == "reviewed_memory"
        ),
        "scoped_external_action_occurred": bool(
            performed and mutation_class == "external_messaging"
        ),
        "identity_change": False,
        "personality_change": False,
        "governance_change": False,
        "training_or_parameter_change": False,
        "autonomy_expansion": False,
        "negative_invariants_are_derived_with_the_event": True,
        "static_guard_booleans_are_not_mutation_evidence": True,
        "provenance_boundary": (
            "actual_route_actor_scope_recipient_consent_and_mutation_summary_only_"
            "no_authority_identity_governance_training_or_autonomy_grant"
        ),
    }


def record_authority_event(
    conn: sqlite3.Connection,
    event: dict[str, Any],
) -> dict[str, Any]:
    if event.get("performed_mutation") is not True:
        return {**event, "persisted": False, "event_id": 0}
    cur = conn.execute(
        """
        INSERT INTO selene_authority_events(
          route_key, actor, scope, recipient, consent_record,
          mutation_class, performed_mutation, event_json
        ) VALUES(?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (
            str(event.get("route_key") or ""),
            str(event.get("actor") or "local_caller"),
            str(event.get("scope") or ""),
            str(event.get("recipient") or ""),
            str(event.get("consent_record") or ""),
            str(event.get("mutation_class") or "none"),
            json.dumps(event, sort_keys=True),
        ),
    )
    conn.commit()
    return {**event, "persisted": True, "event_id": int(cur.lastrowid)}


def _mutation_requested(route: str) -> bool:
    if route.endswith(READ_SUFFIXES):
        return False
    return any(part in MUTATION_ACTIONS for part in route.split("."))


def _blocked_result(result: dict[str, Any]) -> bool:
    status = str(result.get("status") or "").lower()
    decision = str(result.get("decision") or "").lower()
    return any(
        marker in f"{status} {decision}"
        for marker in ("blocked", "unable", "rejected_request", "not_authorized", "needs_review")
    )


def _mutation_class(route: str) -> str:
    if "memory" in route:
        return "reviewed_memory"
    if any(marker in route for marker in ("teaching", "curriculum", "comprehension")):
        return "reviewed_knowledge"
    if route.startswith("activation."):
        return "resident_chat_availability"
    if any(marker in route for marker in ("tendril", "sms", "mobile.pairing")):
        return "external_messaging"
    if route.startswith("selene_chat."):
        return "conversation_record"
    if route.startswith("test_impact_law."):
        return "diagnostic_review_record"
    return "reviewed_local_record"
