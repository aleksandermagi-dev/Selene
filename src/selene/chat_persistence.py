from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any


CHAT_TRACE_SCHEMA_VERSION = "selene_chat_trace_v2"
CONTINUITY_PROJECTION_SCHEMA_VERSION = "selene_chat_continuity_projection_v1"
ACTIVATION_TRACE_RECEIPT_SCHEMA_VERSION = "selene_activation_trace_receipt_v1"


def json_dumps(value: Any) -> str:
    """Serialize persisted JSON deterministically so its receipt can be verified."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_chat_trace(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the durable Chat trace without copying records owned by other shelves."""
    trace = dict(payload)
    trace["native_language_organ"] = _run_reference(
        payload.get("native_language_organ"),
        shelf="native_language_runs",
        summary_keys=("status", "mode", "candidate_text", "review_status", "source_refs"),
    )
    trace["metacognition"] = _run_reference(
        payload.get("metacognition"),
        shelf="metacognition_runs",
        summary_keys=(
            "status",
            "fit_state",
            "recommended_action",
            "sufficiency_state",
            "confidence_vector",
            "review_status",
            "source_refs",
        ),
    )
    trace["local_chat_continuity"] = _continuity_reference(
        payload.get("local_chat_continuity")
    )
    trace["dialogue_workspace"] = _workspace_reference(payload.get("dialogue_workspace"))
    trace["trace_storage_contract"] = {
        "schema_version": CHAT_TRACE_SCHEMA_VERSION,
        "canonical_owner": "selene_chat_messages.payload_json",
        "referenced_records_remain_inspectable": True,
        "legacy_trace_reads_supported": True,
        "history_rewritten": False,
    }
    return trace


def trace_receipt(*, message_id: int, session_id: int, serialized_trace: str) -> dict[str, Any]:
    encoded = serialized_trace.encode("utf-8")
    return {
        "schema_version": CHAT_TRACE_SCHEMA_VERSION,
        "canonical_table": "selene_chat_messages",
        "canonical_column": "payload_json",
        "message_id": int(message_id),
        "session_id": int(session_id),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "size_bytes": len(encoded),
    }


def continuity_projection(
    payload: dict[str, Any],
    *,
    trace_reference: dict[str, Any],
) -> dict[str, Any]:
    metacognition = _dict(payload.get("metacognition"))
    answer_engine = _dict(payload.get("answer_engine_support"))
    intelligence = _dict(payload.get("intelligence_os_support"))
    voice = _dict(payload.get("voice_preview"))
    metacognition_vector = _dict(metacognition.get("confidence_vector"))
    answer_vector = _dict(answer_engine.get("confidence_vector"))
    return {
        "schema_version": CONTINUITY_PROJECTION_SCHEMA_VERSION,
        "canonical_trace": trace_reference,
        "figurative_interpretation": _dict(payload.get("figurative_interpretation")),
        "conversational_energy": _dict(payload.get("conversational_energy")),
        "conversational_contribution": _dict(payload.get("conversational_contribution")),
        "confidence_vector": {
            "answer_confidence": _first_assessed(
                metacognition_vector.get("answer_confidence"),
                answer_vector.get("answer_confidence"),
                intelligence.get("confidence"),
            ),
            "evidence_confidence": _first_assessed(
                metacognition_vector.get("evidence_confidence"),
                answer_vector.get("evidence_confidence"),
            ),
            "expression_confidence": _first_assessed(
                metacognition_vector.get("expression_confidence"),
                voice.get("voice_confidence"),
            ),
            "dimensions_are_independent": True,
        },
        "projection_scope": "conversation continuity only",
        "memory_write_active": False,
        "identity_change": False,
        "governance_change": False,
        "authority_change": False,
    }


def compact_activation_payload(
    payload: dict[str, Any],
    *,
    trace_reference: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": ACTIVATION_TRACE_RECEIPT_SCHEMA_VERSION,
        "canonical_trace": trace_reference,
        "diagnostic_context": _dict(payload.get("diagnostic_context")),
        "source_boundaries": _dict(payload.get("source_boundaries")),
        "transfer_complete": payload.get("transfer_complete") is True,
        "memory_context_used": payload.get("memory_context_used") is True,
        "reviewed_memory_write_occurred": payload.get("reviewed_memory_write_occurred") is True,
        "conversational_memory_proposal_created": payload.get("conversational_memory_proposal_created") is True,
        "durable_memory_write_requires_review": payload.get("durable_memory_write_requires_review") is not False,
        "identity_change": False,
        "governance_change": False,
        "training_allowed": False,
        "self_replication_allowed": False,
        "autonomous_action_allowed": False,
        "history_rewritten": False,
    }


def load_trace_reference(conn: sqlite3.Connection, message_id: int) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT session_id, canonical_trace_sha256, canonical_trace_size_bytes,
               trace_schema_version
        FROM selene_chat_continuity_projections
        WHERE message_id = ?
        """,
        (int(message_id),),
    ).fetchone()
    if row is None:
        return {
            "schema_version": "legacy_trace_without_projection",
            "canonical_table": "selene_chat_messages",
            "canonical_column": "payload_json",
            "message_id": int(message_id),
            "legacy_fallback_required": True,
        }
    item = dict(row)
    return {
        "schema_version": str(item.get("trace_schema_version") or CHAT_TRACE_SCHEMA_VERSION),
        "canonical_table": "selene_chat_messages",
        "canonical_column": "payload_json",
        "message_id": int(message_id),
        "session_id": int(item.get("session_id") or 0),
        "sha256": str(item.get("canonical_trace_sha256") or ""),
        "size_bytes": int(item.get("canonical_trace_size_bytes") or 0),
    }


def compact_run_payload(
    result: dict[str, Any],
    *,
    schema_version: str,
    column_owned_keys: set[str],
) -> dict[str, Any]:
    """Keep only non-column fields in a run envelope; columns remain canonical."""
    return {
        "storage_contract": {
            "schema_version": schema_version,
            "column_owned_keys": sorted(column_owned_keys),
            "legacy_full_payload_reads_supported": True,
        },
        **{key: value for key, value in result.items() if key not in column_owned_keys},
    }


def _run_reference(value: Any, *, shelf: str, summary_keys: tuple[str, ...]) -> dict[str, Any]:
    run = _dict(value)
    run_id = run.get("run_id")
    if not run_id:
        return run
    return {
        "storage_contract": "canonical_run_reference",
        "shelf": shelf,
        "run_id": run_id,
        "summary": {key: run[key] for key in summary_keys if key in run},
        "full_record_available_by_run_id": True,
    }


def _continuity_reference(value: Any) -> dict[str, Any]:
    continuity = _dict(value)
    return {
        "storage_contract": "continuity_projection_reference",
        "current_session_id": continuity.get("current_session_id"),
        "diagnostic_only": continuity.get("diagnostic_only") is True,
        "current_session_event_count": len(continuity.get("current_session_events") or []),
        "recent_event_count": len(continuity.get("recent_events") or []),
        "relevant_prior_event_count": len(continuity.get("relevant_prior_events") or []),
        "source_refs": list(continuity.get("source_refs") or [])[:20],
        "full_prior_traces_not_nested": True,
    }


def _workspace_reference(value: Any) -> dict[str, Any]:
    workspace = _dict(value)
    return {
        "storage_contract": "dialogue_workspace_reference",
        "shelf": "selene_dialogue_workspaces",
        "id": workspace.get("id"),
        "session_id": workspace.get("session_id"),
        "status": workspace.get("status"),
        "active_topic": workspace.get("active_topic"),
        "full_record_available_by_session_id": bool(workspace.get("session_id")),
    }


def _first_assessed(*values: Any) -> str:
    normalized = [str(value or "").strip() for value in values]
    return next(
        (
            value
            for value in normalized
            if value and value.lower() not in {"not_assessed", "not_used", "none"}
        ),
        "not_assessed",
    )


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}
