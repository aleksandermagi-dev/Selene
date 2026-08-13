from __future__ import annotations

from typing import Any


LONG_THREAD_ENDURANCE_BOUNDARY = (
    "current_session_structural_saturation_coordination_only_no_raw_transcript_"
    "archive_memory_identity_personality_governance_authority_training_or_action"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "retained_knowledge_write_active": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
}

DEFAULT_LIMITS = {
    "working_threads": 16,
    "thread_index": 64,
    "open_loops": 64,
    "completed_loops": 30,
    "corrections": 32,
    "epistemic_updates": 24,
    "session_landmarks": 64,
    "topic_checkpoints": 64,
}


def long_thread_endurance_status() -> dict[str, Any]:
    return _locked(
        {
            "status": "long_thread_endurance_ready",
            "version": "v1_structural_saturation_and_return_integrity",
            "owners": [
                "Dialogue Workspace",
                "Conversation Thread Loom",
                "Conversation Spine",
                "Conversation Continuity",
                "Dual-Horizon Context",
            ],
            "limits": dict(DEFAULT_LIMITS),
            "preserves": [
                "active thread",
                "paused threads with open obligations",
                "explicit branch return dependency and update edges",
                "unresolved loops",
                "active corrections and epistemic revisions",
                "latest visible checkpoint for each retained thread",
                "bounded visible landmarks and referents",
            ],
            "raw_transcript_is_endurance_state": False,
            "session_checkpoint_is_memory": False,
            "automatic_durable_promotion": False,
            "visible_summary_only": True,
        }
    )


def protected_thread_ids_for_workspace(
    workspace: dict[str, Any] | None = None,
) -> set[str]:
    workspace = workspace or {}
    pragmatics = _dict(workspace.get("pragmatics"))
    braid = _dict(pragmatics.get("thread_braid"))
    protected: set[str] = {
        str(braid.get("active_thread_id") or ""),
        str(braid.get("prior_active_thread_id") or ""),
    }
    for item in workspace.get("open_loops") or []:
        if isinstance(item, dict):
            protected.add(str(item.get("thread_id") or ""))
    for item in pragmatics.get("topic_checkpoints") or workspace.get("topic_checkpoints") or []:
        if isinstance(item, dict) and item.get("status") == "session_topic_checkpoint_ready":
            protected.add(str(item.get("thread_id") or ""))
    for edge in braid.get("edges") or []:
        if not isinstance(edge, dict) or str(edge.get("relation") or "") not in {
            "returns_to",
            "depends_on",
            "updates",
        }:
            continue
        protected.add(str(edge.get("source_thread_id") or ""))
        protected.add(str(edge.get("target_thread_id") or ""))
    return {item for item in protected if item}


def retain_structural_records(
    values: list[dict[str, Any]] | None,
    *,
    limit: int,
    protected_thread_ids: set[str] | None = None,
    unresolved_first: bool = False,
) -> list[dict[str, Any]]:
    """Bound session summaries by structural value instead of recency alone."""
    records = [item for item in values or [] if isinstance(item, dict)]
    if len(records) <= max(1, limit):
        return records
    protected = protected_thread_ids or set()
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(records):
        thread_id = str(item.get("thread_id") or "")
        status = str(item.get("status") or "")
        unresolved = status in {
            "open",
            "active_refinement",
            "unresolved",
            "reopened",
            "pending",
        }
        score = (
            (1000 if thread_id in protected else 0)
            + (800 if unresolved_first and unresolved else 0)
            + (500 if item.get("required") is True else 0)
            + (350 if item.get("coverage_complete_at_recording") is True else 0)
            + (250 if item.get("revision") else 0)
            + index
        )
        ranked.append((score, index, item))
    ranked.sort(key=lambda value: (value[0], value[1]), reverse=True)
    selected = {index for _, index, _ in ranked[: max(1, limit)]}
    return [item for index, item in enumerate(records) if index in selected]


def build_long_thread_endurance_plan(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    workspace = _dict(payload.get("dialogue_workspace"))
    pragmatics = _dict(workspace.get("pragmatics"))
    braid = _dict(pragmatics.get("thread_braid"))
    spine = _dict(payload.get("conversation_spine"))
    dual = _dict(payload.get("dual_horizon_context"))
    protected = protected_thread_ids_for_workspace(workspace)
    active_id = str(braid.get("active_thread_id") or spine.get("active_thread_id") or "")
    if active_id:
        protected.add(active_id)
    threads = [
        item
        for item in braid.get("thread_index") or braid.get("threads") or []
        if isinstance(item, dict)
    ]
    working_threads = [item for item in braid.get("threads") or [] if isinstance(item, dict)]
    open_loops = [item for item in workspace.get("open_loops") or [] if isinstance(item, dict)]
    corrections = [item for item in workspace.get("corrections") or [] if isinstance(item, dict)]
    landmarks = [item for item in pragmatics.get("session_landmarks") or [] if isinstance(item, dict)]
    checkpoints = [item for item in pragmatics.get("topic_checkpoints") or [] if isinstance(item, dict)]
    unresolved_returns = [item for item in braid.get("unresolved_returns") or [] if isinstance(item, dict)]
    saturation_reasons: list[str] = []
    for key, count in (
        ("thread_index", len(threads)),
        ("working_threads", len(working_threads)),
        ("open_loops", len(open_loops)),
        ("corrections", len(corrections)),
        ("session_landmarks", len(landmarks)),
        ("topic_checkpoints", len(checkpoints)),
    ):
        if count >= DEFAULT_LIMITS[key]:
            saturation_reasons.append(f"{key}_at_bound")
    active_present = not active_id or any(
        str(item.get("id") or "") == active_id for item in working_threads
    )
    indexed_ids = {str(item.get("id") or "") for item in threads}
    protected_present = protected.issubset(indexed_ids) if protected else True
    checkpoint_thread_ids = {
        str(item.get("thread_id") or "") for item in checkpoints if str(item.get("thread_id") or "")
    }
    return _locked(
        {
            "status": "long_thread_endurance_plan_ready",
            "version": "v1_structural_saturation_and_return_integrity",
            "saturation_state": "bounded_compaction_active" if saturation_reasons else "within_bounds",
            "saturation_reasons": saturation_reasons,
            "counts": {
                "working_threads": len(working_threads),
                "indexed_threads": len(threads),
                "open_loops": len(open_loops),
                "corrections": len(corrections),
                "session_landmarks": len(landmarks),
                "topic_checkpoints": len(checkpoints),
                "dual_horizon_active_selected": int(_dict(dual.get("active_horizon")).get("selected_count") or 0),
                "dual_horizon_approved_selected": int(_dict(dual.get("approved_long_range_horizon")).get("selected_count") or 0),
            },
            "limits": dict(DEFAULT_LIMITS),
            "protected_thread_ids": sorted(protected),
            "integrity": {
                "active_thread_present": active_present,
                "protected_threads_indexed": protected_present,
                "unresolved_return_count": len(unresolved_returns),
                "open_obligations_present": bool(open_loops or spine.get("open_obligations")),
                "checkpoint_thread_count": len(checkpoint_thread_ids),
                "checkpoint_is_memory": False,
                "raw_transcript_loaded_for_compaction": False,
                "hidden_reasoning_compacted": False,
            },
            "continuation_handoff": {
                "active_thread_id": active_id,
                "open_loop_ids": [str(item.get("id") or "") for item in open_loops if str(item.get("id") or "")],
                "unresolved_returns": unresolved_returns,
                "latest_checkpoint_by_thread": _latest_checkpoint_ids(checkpoints),
                "meaning_may_be_reconstructed_from_selected_structural_packets": True,
                "source_wording_is_not_a_required_script": True,
            },
            "needs_material_clarification": bool(unresolved_returns),
            "automatic_question_generated": False,
            "automatic_checkpoint_promotion": False,
            "visible_summary_only": True,
        }
    )


def _latest_checkpoint_ids(values: list[dict[str, Any]]) -> dict[str, str]:
    latest: dict[str, str] = {}
    for item in values:
        thread_id = str(item.get("thread_id") or "")
        checkpoint_id = str(item.get("checkpoint_id") or "")
        if thread_id and checkpoint_id:
            latest[thread_id] = checkpoint_id
    return latest


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _locked(result: dict[str, Any]) -> dict[str, Any]:
    return {
        **result,
        **GUARDS,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": LONG_THREAD_ENDURANCE_BOUNDARY,
    }
