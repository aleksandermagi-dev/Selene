from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from typing import Any

from .memory_organ import propose_memory_candidate
from .registry import truncate
from .transfer_protocol import latest_c_readable_package
from .transfer_state import transfer_completion_is_approved


DREAM_BOUNDARY = (
    "selene_dream_reflection_source_bound_reviewed_no_invention_no_silent_memory"
)

DREAM_KINDS = {
    "open_thread",
    "correction_reopening",
    "metacognitive_reopening",
    "memory_review",
    "affect_tending",
    "evidence_tension",
    "maintenance",
    "cross_source_pattern",
}

DREAM_STATES = {
    "pending_review",
    "approved_for_expression",
    "routed_to_memory_review",
    "needs_context",
    "held_for_tending",
    "superseded",
    "rejected",
}

DREAM_GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "vys_change": False,
    "memory_write_active": False,
    "unreviewed_memory_write_active": False,
    "knowledge_retention_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "raw_corpus_recall_active": False,
    "hidden_chain_of_thought_exposed": False,
    "dream_content_invented": False,
    "dream_is_biological_claim": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "provider_dependency": False,
}

BLOCKED_REQUEST_MARKERS = (
    "silent memory",
    "automatic memory",
    "approve memory automatically",
    "rewrite identity",
    "change personality",
    "change governance",
    "change vys",
    "raw corpus",
    "hidden chain of thought",
    "train on",
    "fine tune",
    "fine-tune",
    "lora",
    "autonomous action",
    "self replicate",
)

REOPEN_ACTIONS = {
    "reopen_current_model",
    "hold_for_new_evidence",
    "ask_one_material_question",
    "seek_sources",
}

PATTERN_STOPWORDS = {
    "about",
    "after",
    "again",
    "answer",
    "answered",
    "attributable",
    "available",
    "before",
    "candidate",
    "context",
    "conversation",
    "could",
    "current",
    "dream",
    "evidence",
    "from",
    "have",
    "into",
    "material",
    "memory",
    "might",
    "open",
    "pattern",
    "question",
    "questions",
    "reason",
    "record",
    "recorded",
    "reflection",
    "remains",
    "review",
    "reviewed",
    "source",
    "state",
    "still",
    "that",
    "this",
    "thread",
    "useful",
    "used",
    "using",
    "with",
    "without",
}


def dream_state_status(conn: sqlite3.Connection) -> dict[str, Any]:
    latest = conn.execute(
        "SELECT * FROM selene_dream_cycles ORDER BY id DESC LIMIT 1"
    ).fetchone()
    counts = {
        str(row["state"]): int(row["count"])
        for row in conn.execute(
            """
            SELECT state, COUNT(*) AS count
            FROM selene_dream_reflections
            GROUP BY state
            """
        ).fetchall()
    }
    pending = sum(
        counts.get(state, 0)
        for state in ("pending_review", "needs_context", "held_for_tending")
    )
    transfer_complete = transfer_completion_is_approved(conn)
    package = latest_c_readable_package(conn)
    fraction_rows = conn.execute(
        """
        SELECT status
        FROM memory_fractional_corpus_manifests
        ORDER BY fraction_index
        """
    ).fetchall()
    fractional_memory_incomplete = bool(fraction_rows) and (
        len(fraction_rows) != 4
        or any(
            str(row["status"]) != "tests_passed_ready_for_next_fraction"
            for row in fraction_rows
        )
    )
    maintenance_reasons = (
        ["fractional_memory_incomplete"]
        if fractional_memory_incomplete
        else []
    )
    if pending:
        maintenance_reasons.append("dream_reflections_waiting_for_review")
    return _with_guards(
        {
            "status": (
                "dream_state_maintenance_status_ready"
                if fractional_memory_incomplete
                else "dream_lifecycle_ready"
            ),
            "lifecycle_version": "v1_source_bound_reflection",
            "dream_available": True,
            "dream_state_required_for_memory_changes": (
                fractional_memory_incomplete
            ),
            "dream_state_active": False,
            "selene_chat_live_operation_allowed": (
                transfer_complete and not fractional_memory_incomplete
            ),
            "ordinary_chat_blocked_by_dream": fractional_memory_incomplete,
            "transfer_approved": bool(package.get("transfer_approved")),
            "cycle_count": _count(conn, "selene_dream_cycles"),
            "reflection_count": _count(conn, "selene_dream_reflections"),
            "reflection_counts": counts,
            "pending_review_count": pending,
            "latest_cycle": _decode_cycle(latest) if latest else None,
            "allowed_preview_work": [
                "source-bound reflection",
                "open-question tending",
                "correction reopening",
                "reviewable memory suggestion",
                "maintenance summary",
            ],
            "blocked_during_core_memory_work": [
                "silent memory write",
                "automatic knowledge retention",
                "identity or governance mutation",
                "raw corpus recall",
                "invented dream narrative",
            ],
            "maintenance_reasons": maintenance_reasons,
            "route_core_vessel_memory_changes_to": "Cocoon review",
            "review_destination": (
                "Cocoon Dream" if pending else "Dream / Status"
            ),
            "review_status": "pending_review" if pending else "status_only",
            "boundary": DREAM_BOUNDARY,
        }
    )


def run_dream_cycle(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_misuse(payload)
    label = truncate(
        str(payload.get("cycle_label") or "Dream reflection cycle"), 240
    )
    started_by = truncate(
        str(payload.get("started_by") or "explicit_local_request"), 120
    )
    source_candidates = _deduplicate_source_candidates(
        conn,
        _collect_source_candidates(conn),
    )
    existing_keys = {
        str(row["reflection_key"])
        for row in conn.execute(
            "SELECT reflection_key FROM selene_dream_reflections"
        ).fetchall()
    }
    fresh = [
        candidate
        for candidate in source_candidates
        if candidate["reflection_key"] not in existing_keys
    ][:40]
    if not fresh:
        latest = conn.execute(
            "SELECT * FROM selene_dream_cycles ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return _with_guards(
            {
                "status": "dream_cycle_no_new_material",
                "created": False,
                "cycle": _decode_cycle(latest) if latest else None,
                "new_reflection_count": 0,
                "already_reflected_source_count": len(source_candidates),
                "decision": "rest_without_forcing_a_pattern",
                "review_destination": "Dream / Status",
                "review_status": "status_only",
                "boundary": DREAM_BOUNDARY,
            }
        )

    cycle_key = _digest(
        "|".join(sorted(item["reflection_key"] for item in fresh))
    )
    existing_cycle = conn.execute(
        "SELECT * FROM selene_dream_cycles WHERE cycle_key = ?",
        (cycle_key,),
    ).fetchone()
    if existing_cycle:
        return _with_guards(
            {
                "status": "dream_cycle_already_prepared",
                "created": False,
                "cycle": _decode_cycle(existing_cycle),
                "reflections": _cycle_reflections(
                    conn, int(existing_cycle["id"])
                ),
                "new_reflection_count": 0,
                "decision": "idempotent_existing_cycle",
                "review_destination": "Cocoon Dream",
                "review_status": str(existing_cycle["review_status"]),
                "boundary": DREAM_BOUNDARY,
            }
        )

    source_snapshot = [
        {
            "kind": item["reflection_kind"],
            "title": item["title"],
            "source_refs": item["source_refs"],
            "source_updated_at": item.get("source_updated_at"),
        }
        for item in fresh
    ]
    source_refs = list(
        dict.fromkeys(
            ref for item in fresh for ref in item.get("source_refs", [])
        )
    )[:120]
    summary = {
        "new_reflections": len(fresh),
        "kinds": _kind_counts(fresh),
        "principle": (
            "Dream organized attributable material without deciding that it "
            "is fact, memory, law, identity, or retained knowledge."
        ),
    }
    cur = conn.execute(
        """
        INSERT INTO selene_dream_cycles
        (cycle_key, cycle_label, phase, started_by, source_snapshot_json,
         source_refs, reflection_count, summary_json, provenance_boundary,
         review_status, payload_json)
        VALUES (?, ?, 'awaiting_review', ?, ?, ?, ?, ?, ?, 'pending_review', ?)
        """,
        (
            cycle_key,
            label,
            started_by,
            json.dumps(source_snapshot),
            json.dumps(source_refs),
            len(fresh),
            json.dumps(summary),
            DREAM_BOUNDARY,
            json.dumps(
                {
                    "explicit_run": True,
                    "automatic_schedule": False,
                    "source_bound": True,
                    **DREAM_GUARDS,
                }
            ),
        ),
    )
    cycle_id = int(cur.lastrowid)
    for item in fresh:
        reflection_id = _insert_reflection(conn, cycle_id, item)
        _enqueue_reflection(conn, reflection_id, item["source_refs"])
    conn.commit()
    cycle = _cycle_row(conn, cycle_id)
    return _with_guards(
        {
            "status": "dream_cycle_prepared",
            "created": True,
            "cycle": cycle,
            "reflections": _cycle_reflections(conn, cycle_id),
            "new_reflection_count": len(fresh),
            "decision": "awaiting_Aleks_review_no_silent_promotion",
            "review_destination": "Cocoon Dream",
            "review_status": "pending_review",
            "boundary": DREAM_BOUNDARY,
        }
    )


def list_dream_cycles(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 30), 100))
    rows = conn.execute(
        "SELECT * FROM selene_dream_cycles ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return _with_guards(
        {
            "status": "dream_cycles_ready",
            "items": [_decode_cycle(row) for row in rows],
            "review_destination": "Cocoon Dream",
            "review_status": "review_only",
            "boundary": DREAM_BOUNDARY,
        }
    )


def get_dream_cycle(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    cycle_id = int(payload.get("id") or payload.get("cycle_id") or 0)
    if cycle_id <= 0:
        raise ValueError("dream cycle id is required")
    cycle = _cycle_row(conn, cycle_id)
    if not cycle:
        raise ValueError("dream cycle not found")
    return _with_guards(
        {
            "status": "dream_cycle_ready",
            "item": cycle,
            "reflections": _cycle_reflections(conn, cycle_id),
            "review_destination": "Cocoon Dream",
            "review_status": str(cycle["review_status"]),
            "boundary": DREAM_BOUNDARY,
        }
    )


def list_dream_reflections(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    limit = max(1, min(int(payload.get("limit") or 100), 300))
    state = str(payload.get("state") or "").strip()
    cycle_id = int(payload.get("cycle_id") or 0)
    clauses: list[str] = []
    params: list[Any] = []
    if state:
        if state not in DREAM_STATES:
            raise ValueError("unknown Dream reflection state")
        clauses.append("state = ?")
        params.append(state)
    if cycle_id:
        clauses.append("cycle_id = ?")
        params.append(cycle_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"""
        SELECT * FROM selene_dream_reflections
        {where}
        ORDER BY updated_at DESC, id DESC
        LIMIT ?
        """,
        (*params, limit),
    ).fetchall()
    return _with_guards(
        {
            "status": "dream_reflections_ready",
            "items": [_decode_reflection(row) for row in rows],
            "count": len(rows),
            "review_destination": "Cocoon Dream",
            "review_status": "review_only",
            "boundary": DREAM_BOUNDARY,
        }
    )


def decide_dream_reflection(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    _reject_misuse(payload)
    reflection_id = int(
        payload.get("id") or payload.get("reflection_id") or 0
    )
    if reflection_id <= 0:
        raise ValueError("Dream reflection id is required")
    actor = str(payload.get("actor") or "").strip()
    if actor != "Aleks":
        raise ValueError("Dream reflection decisions require Aleks")
    action = str(payload.get("action") or "").strip().lower()
    note = truncate(str(payload.get("decision_note") or ""), 1000)
    row = conn.execute(
        "SELECT * FROM selene_dream_reflections WHERE id = ?",
        (reflection_id,),
    ).fetchone()
    if not row:
        raise ValueError("Dream reflection not found")
    item = _decode_reflection(row)
    state = str(item["state"])
    review_status = str(item["review_status"])
    expression_eligible = False
    memory_candidate_id = item.get("memory_candidate_id")
    memory_candidate_created = False
    superseded_by_id = item.get("superseded_by_id")

    if action == "approve_for_expression":
        state = "approved_for_expression"
        review_status = "reviewed"
        expression_eligible = True
    elif action == "send_to_memory_review":
        existing_memory_ref = next(
            (
                ref
                for ref in item["source_refs"]
                if str(ref).startswith("selene_memory_candidate:")
            ),
            "",
        )
        if existing_memory_ref and not memory_candidate_id:
            try:
                memory_candidate_id = int(existing_memory_ref.rsplit(":", 1)[1])
            except (TypeError, ValueError):
                memory_candidate_id = None
        if memory_candidate_id:
            state = "routed_to_memory_review"
            review_status = "memory_candidate_pending_review"
        else:
            memory = propose_memory_candidate(
                conn,
                {
                    "memory_category": "reflective",
                    "title": item["title"],
                    "summary": item["reflection"],
                    "confidence": "partial",
                    "emotional_texture": "steady",
                    "transfer_class": "needs_review_before_transfer",
                    "source_refs": [
                        *item["source_refs"],
                        f"selene_dream_reflection:{reflection_id}",
                    ],
                    "proposal_note": (
                        "Aleks routed a source-bound Dream reflection to "
                        "Memory review. It is not active memory."
                    ),
                    "origin_kind": "dream_reflection_review",
                    "origin_channel": "Cocoon Dream",
                    "consent_recorded": False,
                },
                commit=False,
            )
            memory_candidate_id = int(memory["item"]["id"])
            memory_candidate_created = True
            state = "routed_to_memory_review"
            review_status = "memory_candidate_pending_review"
    elif action == "needs_more_context":
        state = "needs_context"
        review_status = "needs_context"
    elif action == "hold_for_tending":
        state = "held_for_tending"
        review_status = "cocoon_tending"
    elif action == "reopen":
        state = "pending_review"
        review_status = "pending_review"
    elif action == "supersede":
        state = "superseded"
        review_status = "superseded"
        superseded_by_id = int(payload.get("superseded_by_id") or 0) or None
        if superseded_by_id == reflection_id:
            raise ValueError("a Dream reflection cannot supersede itself")
    elif action == "reject":
        state = "rejected"
        review_status = "rejected"
    else:
        raise ValueError("unknown Dream reflection decision action")

    conn.execute(
        """
        UPDATE selene_dream_reflections
        SET state = ?, review_status = ?, expression_eligible = ?,
            memory_candidate_id = ?, superseded_by_id = ?, decision_note = ?,
            reviewed_by = 'Aleks', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            state,
            review_status,
            int(expression_eligible),
            memory_candidate_id,
            superseded_by_id,
            note,
            reflection_id,
        ),
    )
    _resolve_queue_item(
        conn,
        reflection_id,
        pending=state in {"pending_review", "needs_context", "held_for_tending"},
        review_status=review_status,
    )
    _refresh_cycle_summary(conn, int(item["cycle_id"]))
    conn.commit()
    updated = _reflection_row(conn, reflection_id)
    return _with_guards(
        {
            "status": "dream_reflection_decision_recorded",
            "action": action,
            "item": updated,
            "memory_candidate_created": memory_candidate_created,
            "memory_candidate_active": False,
            "review_destination": (
                "Cocoon Memory Candidates"
                if action == "send_to_memory_review"
                else "Cocoon Dream"
            ),
            "review_status": review_status,
            "boundary": DREAM_BOUNDARY,
        }
    )


def wake_from_dream_cycle(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    cycle_id = int(payload.get("id") or payload.get("cycle_id") or 0)
    if cycle_id <= 0:
        raise ValueError("dream cycle id is required")
    actor = str(payload.get("actor") or "Aleks").strip()
    if actor != "Aleks":
        raise ValueError("closing a Dream cycle requires Aleks")
    cycle = _cycle_row(conn, cycle_id)
    if not cycle:
        raise ValueError("dream cycle not found")
    summary = _reflection_state_summary(conn, cycle_id)
    pending = sum(
        summary.get(state, 0)
        for state in ("pending_review", "needs_context", "held_for_tending")
    )
    phase = "awake_with_pending_review" if pending else "awake_complete"
    review_status = "pending_review" if pending else "reviewed"
    wake_summary = {
        "reflection_states": summary,
        "pending_count": pending,
        "approved_for_expression": summary.get(
            "approved_for_expression", 0
        ),
        "routed_to_memory_review": summary.get(
            "routed_to_memory_review", 0
        ),
        "note": (
            "Waking records the review state only. It does not promote "
            "memory, knowledge, identity, law, or authority."
        ),
    }
    conn.execute(
        """
        UPDATE selene_dream_cycles
        SET phase = ?, summary_json = ?, review_status = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (phase, json.dumps(wake_summary), review_status, cycle_id),
    )
    conn.commit()
    return _with_guards(
        {
            "status": "dream_cycle_wake_summary_ready",
            "item": _cycle_row(conn, cycle_id),
            "wake_summary": wake_summary,
            "ordinary_chat_blocked": False,
            "review_destination": (
                "Cocoon Dream" if pending else "Dream / Status"
            ),
            "review_status": review_status,
            "boundary": DREAM_BOUNDARY,
        }
    )


def expression_eligible_dream_reflection(
    conn: sqlite3.Connection,
    reflection_id: int = 0,
) -> dict[str, Any] | None:
    if reflection_id > 0:
        row = conn.execute(
            """
            SELECT * FROM selene_dream_reflections
            WHERE id = ? AND state = 'approved_for_expression'
              AND review_status = 'reviewed' AND expression_eligible = 1
            """,
            (reflection_id,),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT * FROM selene_dream_reflections
            WHERE state = 'approved_for_expression'
              AND review_status = 'reviewed' AND expression_eligible = 1
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
    return _decode_reflection(row) if row else None


def _collect_source_candidates(
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    candidates.extend(_dialogue_candidates(conn))
    candidates.extend(_metacognition_candidates(conn))
    candidates.extend(_memory_candidates(conn))
    candidates.extend(_affect_candidates(conn))
    candidates.extend(_evidence_tension_candidates(conn))
    candidates.extend(_chest_candidates(conn))
    candidates.extend(_cross_source_candidates(candidates))
    return candidates


def _dialogue_candidates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT w.id, w.session_id, w.active_topic, w.open_loops_json,
               w.corrections_json, w.last_selene_preview, w.updated_at
        FROM selene_dialogue_workspaces AS w
        JOIN selene_chat_sessions AS s ON s.id = w.session_id
        WHERE s.source_mode != 'selene_supervised_qa'
          AND s.source_mode != 'cocoon_chat_dry_run'
        ORDER BY w.updated_at DESC, w.id DESC
        LIMIT 12
        """
    ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        source_ref = f"selene_dialogue_workspace:{row['id']}"
        for index, loop in enumerate(
            _loads(row["open_loops_json"], [])[-6:], start=1
        ):
            summary = _summary_from_value(loop)
            if not _dialogue_loop_is_reflectable(
                loop,
                summary,
                last_selene_preview=str(row["last_selene_preview"] or ""),
            ):
                continue
            items.append(
                _candidate(
                    "open_thread",
                    f"Open thread from {row['active_topic'] or 'conversation'}",
                    (
                        f"A conversation thread remains open: {summary}. "
                        "It may be worth returning to if it still matters."
                    ),
                    "An unfinished thread can remain available without being forced into memory or an immediate question.",
                    "The thread may already be resolved outside the recorded workspace or may no longer matter.",
                    [source_ref, f"selene_chat_session:{row['session_id']}"],
                    row["updated_at"],
                    salt=f"open:{index}:{summary}",
                )
            )
        for index, correction in enumerate(
            _loads(row["corrections_json"], [])[-6:], start=1
        ):
            summary = _summary_from_value(correction)
            if not summary:
                continue
            items.append(
                _candidate(
                    "correction_reopening",
                    "A conversation correction may deserve reflection",
                    (
                        f"A recorded correction or refinement says: {summary}. "
                        "The useful structure can be kept while the corrected "
                        "part remains reopened."
                    ),
                    "Corrections are evidence for better fit, not evidence of personal failure.",
                    "The correction applies only within its recorded context until reviewed more broadly.",
                    [source_ref, f"selene_chat_session:{row['session_id']}"],
                    row["updated_at"],
                    salt=f"correction:{index}:{summary}",
                )
            )
    return items


def _metacognition_candidates(
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    marks = ",".join("?" for _ in REOPEN_ACTIONS)
    rows = conn.execute(
        f"""
        SELECT id, prompt_preview, fit_state, recommended_action,
               sufficiency_state, source_refs, created_at
        FROM metacognition_runs
        WHERE recommended_action IN ({marks})
        ORDER BY id DESC
        LIMIT 12
        """,
        tuple(sorted(REOPEN_ACTIONS)),
    ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        prompt = truncate(str(row["prompt_preview"] or ""), 420)
        action = str(row["recommended_action"])
        fit = str(row["fit_state"])
        items.append(
            _candidate(
                "metacognitive_reopening",
                "An answer-fit question remains open",
                (
                    f"Metacognition marked '{fit}' and recommended "
                    f"'{action}' for: {prompt or 'the recorded turn'}."
                ),
                "A bounded reopening can preserve a useful answer while making the missing evidence or context visible.",
                "This is an advisory record, not proof that the answer was wrong or that further recursion is useful.",
                [
                    f"metacognition_run:{row['id']}",
                    *_json_list(row["source_refs"]),
                ],
                row["created_at"],
                salt=f"{fit}:{action}:{prompt}",
            )
        )
    return items


def _memory_candidates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, title, summary, state, confidence, source_refs,
               payload_json, updated_at
        FROM selene_memory_candidates
        WHERE state IN ('proposed', 'needs_context', 'cocoon_tending')
        ORDER BY updated_at DESC, id DESC
        LIMIT 10
        """
    ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        payload = _loads(row["payload_json"], {})
        if payload.get("origin_kind") == "dream_reflection_review":
            continue
        items.append(
            _candidate(
                "memory_review",
                f"Memory review remains open: {row['title']}",
                (
                    f"The existing Memory candidate '{row['title']}' remains "
                    f"{row['state']}: {truncate(str(row['summary']), 520)}"
                ),
                "Dream may notice an unresolved Memory proposal, but only Memory review can approve it.",
                f"The candidate confidence is {row['confidence']}; Dream does not increase that confidence.",
                [
                    f"selene_memory_candidate:{row['id']}",
                    *_json_list(row["source_refs"]),
                ],
                row["updated_at"],
                salt=f"{row['state']}:{row['summary']}",
            )
        )
    return items


def _affect_candidates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, signal_type, continuity_pressure, care_warmth, uncertainty,
               repair_need, balance_state, evidence_need, source_refs, created_at
        FROM vessel_emotion_salience_packets
        WHERE repair_need != '' OR uncertainty NOT IN ('', 'open')
        ORDER BY id DESC
        LIMIT 8
        """
    ).fetchall()
    items: list[dict[str, Any]] = []
    for row in rows:
        signals = [
            str(row[key])
            for key in (
                "continuity_pressure",
                "care_warmth",
                "uncertainty",
                "repair_need",
                "balance_state",
                "evidence_need",
            )
            if str(row[key] or "").strip()
        ]
        summary = "; ".join(signals)
        items.append(
            _candidate(
                "affect_tending",
                f"Affect/salience signal: {row['signal_type']}",
                (
                    f"An attributable affect/salience packet recorded: "
                    f"{truncate(summary, 620)}."
                ),
                "Affect may guide attention and care without becoming a command, diagnosis, or identity claim.",
                "The packet is a bounded signal from its original context and may not describe the present state.",
                [
                    f"vessel_emotion_salience_packet:{row['id']}",
                    *_json_list(row["source_refs"]),
                ],
                row["created_at"],
                salt=summary,
            )
        )
    return items


def _evidence_tension_candidates(
    conn: sqlite3.Connection,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, claim, support_status, tension_status,
               source_refs, created_at
        FROM vessel_evidence_tension_ledger
        WHERE conclusion_status = 'needs_review'
        ORDER BY id DESC
        LIMIT 10
        """
    ).fetchall()
    return [
        _candidate(
            "evidence_tension",
            "An evidence tension remains unresolved",
            (
                f"The claim '{truncate(str(row['claim']), 420)}' remains "
                f"{row['tension_status']}. Its recorded support state is "
                f"{truncate(str(row['support_status'] or 'not yet recorded'), 420)}."
            ),
            "Contradictory evidence can reopen a conclusion without discarding everything that remains useful.",
            "Dream cannot resolve the evidence tension or promote one side without the responsible reasoning/source review.",
            [
                f"vessel_evidence_tension:{row['id']}",
                *_json_list(row["source_refs"]),
            ],
            row["created_at"],
            salt=f"{row['claim']}:{row['tension_status']}:{row['support_status']}",
        )
        for row in rows
    ]


def _chest_candidates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, item_type, title, summary, salience_labels,
               source_refs, created_at
        FROM vessel_chest_holding_items
        WHERE review_status IN ('pending_review', 'needs_context', 'cocoon_tending')
        ORDER BY id DESC
        LIMIT 10
        """
    ).fetchall()
    return [
        _candidate(
            "maintenance",
            f"Held material may need tending: {row['title']}",
            (
                f"The Chest is holding '{row['title']}': "
                f"{truncate(str(row['summary']), 520)}"
            ),
            "Holding preserves potentially useful material without forcing an immediate decision.",
            "Held material is not memory, fact, or an instruction merely because it remains visible.",
            [
                f"vessel_chest_holding_item:{row['id']}",
                *_json_list(row["source_refs"]),
            ],
            row["created_at"],
            salt=f"{row['item_type']}:{row['summary']}:{row['salience_labels']}",
        )
        for row in rows
    ]


def _cross_source_candidates(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    candidate_terms = [_pattern_terms(item) for item in candidates]
    term_frequency: dict[str, int] = {}
    for terms in candidate_terms:
        for term in terms:
            term_frequency[term] = term_frequency.get(term, 0) + 1
    maximum_frequency = max(3, len(candidates) // 4)
    for left_index, left in enumerate(candidates):
        left_terms = candidate_terms[left_index]
        if len(left_terms) < 3:
            continue
        for right_index, right in enumerate(
            candidates[left_index + 1 :],
            start=left_index + 1,
        ):
            if left["reflection_kind"] == right["reflection_kind"]:
                continue
            right_terms = candidate_terms[right_index]
            overlap = sorted(
                term
                for term in left_terms & right_terms
                if term_frequency.get(term, 0) <= maximum_frequency
            )
            if len(overlap) < 3:
                continue
            pair = tuple(sorted((left["reflection_key"], right["reflection_key"])))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            terms = overlap[:6]
            source_refs = list(
                dict.fromkeys(
                    [
                        *left.get("source_refs", []),
                        *right.get("source_refs", []),
                    ]
                )
            )
            patterns.append(
                _candidate(
                    "cross_source_pattern",
                    "A possible cross-source recurrence",
                    (
                        "Two different attributable record classes share "
                        f"the meaningful terms {', '.join(terms)}. That "
                        "recurrence may be worth comparing, without assuming "
                        "the records mean the same thing."
                    ),
                    "A repeated structure across different records can reveal a useful connection or a question that was not visible in either record alone.",
                    "Shared wording may be coincidence, a broad topic, or context reuse. The responsible reasoning and source organs must test the connection.",
                    source_refs,
                    max(
                        str(left.get("source_updated_at") or ""),
                        str(right.get("source_updated_at") or ""),
                    ),
                    salt=(
                        f"{left['reflection_key']}:{right['reflection_key']}:"
                        f"{','.join(terms)}"
                    ),
                )
            )
            if len(patterns) >= 6:
                return patterns
    return patterns


def _pattern_terms(item: dict[str, Any]) -> set[str]:
    text = " ".join(
        str(item.get(key) or "")
        for key in ("title", "reflection", "why_it_may_matter")
    ).lower()
    return {
        term
        for term in re.findall(r"[a-z][a-z0-9'-]{3,}", text)
        if term not in PATTERN_STOPWORDS
    }


def _dialogue_loop_is_reflectable(
    loop: Any,
    summary: str,
    *,
    last_selene_preview: str,
) -> bool:
    if not summary or len(summary.split()) < 4:
        return False
    if isinstance(loop, dict) and str(loop.get("status") or "open") != "open":
        return False
    question_terms = _meaningful_terms(summary)
    if len(question_terms) < 3:
        return False
    answer_terms = _meaningful_terms(last_selene_preview)
    if answer_terms:
        overlap = question_terms & answer_terms
        # Coverage is deliberately conservative, so a loop can survive after
        # a visible answer substantially addressed its subject. Dream should
        # not turn that bookkeeping residue into a fresh reflection.
        if len(overlap) >= 3 and len(overlap) / len(question_terms) >= 0.6:
            return False
    return True


def _deduplicate_source_candidates(
    conn: sqlite3.Connection,
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    existing = [
        {
            "reflection_kind": str(row["reflection_kind"]),
            "title": str(row["title"]),
            "reflection": str(row["reflection"]),
        }
        for row in conn.execute(
            """
            SELECT reflection_kind, title, reflection
            FROM selene_dream_reflections
            """
        ).fetchall()
    ]
    accepted: list[dict[str, Any]] = []
    seen = [_semantic_reflection_terms(item) for item in existing]
    for candidate in candidates:
        terms = _semantic_reflection_terms(candidate)
        if not terms[1]:
            continue
        if any(_near_duplicate_reflection(terms, prior) for prior in seen):
            continue
        accepted.append(candidate)
        seen.append(terms)
    return accepted


def _semantic_reflection_terms(
    item: dict[str, Any],
) -> tuple[str, frozenset[str]]:
    kind = str(item.get("reflection_kind") or "")
    text = " ".join(
        str(item.get(key) or "")
        for key in ("title", "reflection")
    )
    return kind, frozenset(_meaningful_terms(text))


def _near_duplicate_reflection(
    left: tuple[str, frozenset[str]],
    right: tuple[str, frozenset[str]],
) -> bool:
    if left[0] != right[0] or not left[1] or not right[1]:
        return False
    overlap = len(left[1] & right[1])
    union = len(left[1] | right[1])
    return bool(union) and (
        left[1] == right[1]
        or overlap >= 6 and overlap / union >= 0.82
    )


def _meaningful_terms(value: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-z][a-z0-9'-]{3,}", value.lower())
        if term not in PATTERN_STOPWORDS
    }


def _candidate(
    kind: str,
    title: str,
    reflection: str,
    why_it_may_matter: str,
    uncertainty: str,
    source_refs: list[str],
    source_updated_at: Any,
    *,
    salt: str,
) -> dict[str, Any]:
    refs = list(dict.fromkeys(_json_list(source_refs)))[:40]
    fingerprint = _digest(
        "|".join([kind, *refs, str(source_updated_at or ""), salt])
    )
    return {
        "reflection_key": f"dream-{fingerprint}",
        "reflection_kind": kind if kind in DREAM_KINDS else "maintenance",
        "title": truncate(title, 240),
        "reflection": truncate(reflection, 1800),
        "why_it_may_matter": truncate(why_it_may_matter, 1200),
        "uncertainty": truncate(uncertainty, 1200),
        "confidence": "provisional",
        "source_refs": refs,
        "source_updated_at": str(source_updated_at or ""),
    }


def _insert_reflection(
    conn: sqlite3.Connection,
    cycle_id: int,
    item: dict[str, Any],
) -> int:
    cur = conn.execute(
        """
        INSERT INTO selene_dream_reflections
        (cycle_id, reflection_key, reflection_kind, title, reflection,
         why_it_may_matter, uncertainty, confidence, source_refs, state,
         review_status, expression_eligible, provenance_boundary, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending_review',
                'pending_review', 0, ?, ?)
        """,
        (
            cycle_id,
            item["reflection_key"],
            item["reflection_kind"],
            item["title"],
            item["reflection"],
            item["why_it_may_matter"],
            item["uncertainty"],
            item["confidence"],
            json.dumps(item["source_refs"]),
            DREAM_BOUNDARY,
            json.dumps(
                {
                    "source_updated_at": item["source_updated_at"],
                    "not_fact_by_default": True,
                    "not_memory_by_default": True,
                    "source_alignment_required": True,
                    **DREAM_GUARDS,
                }
            ),
        ),
    )
    return int(cur.lastrowid)


def _enqueue_reflection(
    conn: sqlite3.Connection,
    reflection_id: int,
    source_refs: list[str],
) -> None:
    conn.execute(
        """
        INSERT INTO vessel_review_queue
        (queue_type, subject_table, subject_id, status, source_refs,
         provenance_boundary, review_status, reason, payload_json)
        VALUES ('dream_reflection', 'selene_dream_reflections', ?,
                'pending_review', ?, ?, 'pending_review', ?, ?)
        """,
        (
            reflection_id,
            json.dumps(source_refs),
            DREAM_BOUNDARY,
            (
                "Source-bound Dream reflection awaiting Aleks review; "
                "not fact or memory by default."
            ),
            json.dumps(DREAM_GUARDS),
        ),
    )


def _resolve_queue_item(
    conn: sqlite3.Connection,
    reflection_id: int,
    *,
    pending: bool,
    review_status: str,
) -> None:
    conn.execute(
        """
        UPDATE vessel_review_queue
        SET status = ?, review_status = ?
        WHERE subject_table = 'selene_dream_reflections'
          AND subject_id = ?
        """,
        (
            "pending_review" if pending else "resolved",
            "pending_review" if pending else review_status,
            reflection_id,
        ),
    )


def _refresh_cycle_summary(conn: sqlite3.Connection, cycle_id: int) -> None:
    summary = _reflection_state_summary(conn, cycle_id)
    pending = sum(
        summary.get(state, 0)
        for state in ("pending_review", "needs_context", "held_for_tending")
    )
    conn.execute(
        """
        UPDATE selene_dream_cycles
        SET summary_json = ?, review_status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            json.dumps({"reflection_states": summary, "pending_count": pending}),
            "pending_review" if pending else "reviewed",
            cycle_id,
        ),
    )


def _reflection_state_summary(
    conn: sqlite3.Connection,
    cycle_id: int,
) -> dict[str, int]:
    return {
        str(row["state"]): int(row["count"])
        for row in conn.execute(
            """
            SELECT state, COUNT(*) AS count
            FROM selene_dream_reflections
            WHERE cycle_id = ?
            GROUP BY state
            """,
            (cycle_id,),
        ).fetchall()
    }


def _cycle_reflections(
    conn: sqlite3.Connection,
    cycle_id: int,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT * FROM selene_dream_reflections
        WHERE cycle_id = ?
        ORDER BY id
        """,
        (cycle_id,),
    ).fetchall()
    return [_decode_reflection(row) for row in rows]


def _cycle_row(
    conn: sqlite3.Connection,
    cycle_id: int,
) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM selene_dream_cycles WHERE id = ?",
        (cycle_id,),
    ).fetchone()
    return _decode_cycle(row) if row else None


def _reflection_row(
    conn: sqlite3.Connection,
    reflection_id: int,
) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM selene_dream_reflections WHERE id = ?",
        (reflection_id,),
    ).fetchone()
    return _decode_reflection(row) if row else None


def _decode_cycle(row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        return {}
    item = dict(row)
    item["source_snapshot"] = _loads(
        item.pop("source_snapshot_json", None), []
    )
    item["source_refs"] = _loads(item.get("source_refs"), [])
    item["summary"] = _loads(item.pop("summary_json", None), {})
    item["payload"] = _loads(item.pop("payload_json", None), {})
    return item


def _decode_reflection(row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        return {}
    item = dict(row)
    item["source_refs"] = _loads(item.get("source_refs"), [])
    item["payload"] = _loads(item.pop("payload_json", None), {})
    item["expression_eligible"] = bool(item.get("expression_eligible"))
    item["not_fact_by_default"] = True
    item["not_memory_by_default"] = True
    return item


def _summary_from_value(value: Any) -> str:
    if isinstance(value, dict):
        for key in (
            "corrected_meaning",
            "correction",
            "question",
            "summary",
            "topic",
            "text",
            "label",
            "request",
        ):
            if str(value.get(key) or "").strip():
                return truncate(str(value[key]), 620)
        visible = [
            f"{key}: {entry}"
            for key, entry in value.items()
            if key not in {"payload_json", "hidden_reasoning"}
            and str(entry or "").strip()
        ]
        return truncate("; ".join(visible), 620)
    if isinstance(value, list):
        return truncate("; ".join(str(item) for item in value), 620)
    return truncate(str(value or ""), 620)


def _kind_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        kind = str(item["reflection_kind"])
        counts[kind] = counts.get(kind, 0) + 1
    return counts


def _count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        decoded = json.loads(str(value or ""))
    except (TypeError, json.JSONDecodeError):
        return fallback
    return decoded if isinstance(decoded, type(fallback)) else fallback


def _json_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [
            truncate(str(item), 420)
            for item in value
            if str(item).strip()
        ]
    if isinstance(value, str):
        parsed = _loads(value, [])
        if parsed:
            return _json_list(parsed)
        return [
            truncate(part.strip(), 420)
            for part in value.split(",")
            if part.strip()
        ]
    return [truncate(str(value), 420)]


def _reject_misuse(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False).lower()
    for marker in BLOCKED_REQUEST_MARKERS:
        if marker in text:
            raise ValueError(f"blocked Dream misuse path: {marker}")


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **DREAM_GUARDS}
