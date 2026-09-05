from __future__ import annotations

import json
import re
import sqlite3
from hashlib import sha256
from typing import Any

from .registry import truncate
from .reflective_lineage import build_reflective_lineage_receipt
from .semantic_relevance import evaluate_memory_privacy_eligibility
from .study_workspace import create_pondering_thread


ASSOCIATIVE_INTUITION_VERSION = "v2_private_bounded_development_handoff"
ASSOCIATIVE_INTUITION_BOUNDARY = (
    "read_only_source_bound_association_selection_and_handoff_only_no_truth_"
    "decision_retention_identity_governance_expression_or_action_authority"
)

PRIVATE_SOURCE_PREFIXES = (
    "raw_corpus:",
    "private_corpus:",
    "corpus_message:",
    "aleks_miner:",
    "aleks_metacognition_miner:",
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "raw_corpus_access_allowed": False,
    "private_corpus_wording_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "truth_decision_authority": False,
    "expression_authority": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "automatic_memory_write": False,
    "automatic_study_write": False,
    "automatic_dream_routing": False,
    "automatic_cocoon_routing": False,
    "hidden_chain_of_thought_exposed": False,
}

_STOP = {
    "about", "after", "again", "also", "and", "are", "because", "been",
    "before", "being", "both", "can", "could", "does", "each", "for",
    "from", "have", "into", "just", "more", "most", "other", "should",
    "some", "that", "the", "their", "then", "there", "these", "they",
    "answer", "check", "choose", "give", "limit", "name", "one", "reason", "reply", "request",
    "thing", "things", "this", "those", "through", "what", "when",
    "where", "which", "why", "with", "work", "would", "your", "selene",
    "but", "not", "out", "still", "will", "you", "our", "ours", "mine",
    "really", "right", "good", "okay", "yeah", "yes", "well", "like",
}

# These cues select eligible source material; they never supply answer content.
# Keeping the vocabulary inspectable also lets later LEAs show exactly where a
# local semantic encoder would add value instead of hiding that decision.
_CUE_FAMILIES: dict[str, tuple[str, ...]] = {
    "cause_effect": (
        "because", "cause", "causes", "caused", "effect", "effects", "lead",
        "leads", "result", "results", "produce", "produces", "why",
    ),
    "change_motion": (
        "change", "changes", "changed", "motion", "move", "moves", "moving",
        "rotate", "rotates", "shift", "shifts", "transform", "transition",
    ),
    "force_influence": (
        "force", "forces", "push", "pushes", "pull", "pulls", "shove",
        "pressure", "influence", "drive", "drives",
    ),
    "comparison_distinction": (
        "compare", "comparison", "contrast", "different", "difference",
        "distinguish", "similar", "similarity", "unlike", "versus",
    ),
    "sequence_dependency": (
        "before", "after", "first", "next", "then", "order", "sequence",
        "step", "steps", "depends", "dependency", "prerequisite",
    ),
    "part_whole": (
        "part", "parts", "whole", "component", "components", "contains",
        "inside", "system", "structure",
    ),
    "boundary_constraint": (
        "boundary", "boundaries", "constraint", "constraints", "limit",
        "limits", "restrict", "scope", "condition", "conditions",
    ),
    "evidence_uncertainty": (
        "evidence", "uncertain", "uncertainty", "unknown", "support",
        "supports", "proof", "verify", "check", "confidence",
    ),
    "prediction_model": (
        "predict", "prediction", "hypothesis", "model", "forecast", "expect",
        "possibility", "possible",
    ),
    "feedback_correction": (
        "feedback", "correct", "correction", "revise", "revision", "reopen",
        "adjust", "adapt", "error",
    ),
    "balance_stability": (
        "balance", "stable", "stability", "unstable", "equilibrium", "steady",
        "maintain", "regulate",
    ),
    "quantity_order": (
        "count", "number", "quantity", "more", "less", "larger", "smaller",
        "increase", "decrease", "equal",
    ),
}


def associative_intuition_status(conn: sqlite3.Connection) -> dict[str, Any]:
    counts = {
        "approved_knowledge": _count(
            conn,
            """
            SELECT COUNT(*) FROM selene_comprehension_concepts
            WHERE state = 'approved_knowledge_resource'
              AND review_status = 'approved_for_knowledge_use'
              AND chat_use_permission = 'available_as_knowledge_resource'
            """,
        ),
        "approved_memory": _count(
            conn,
            """
            SELECT COUNT(*) FROM selene_memory_candidates
            WHERE state = 'approved_active_memory'
              AND chat_use_permission = 'can_use_in_chat'
            """,
        ),
        "study_connections": _count(
            conn,
            """
            SELECT COUNT(*) FROM selene_study_notes
            WHERE note_kind IN ('connection', 'idea', 'revisit')
              AND review_status = 'selene_owned_working_study_note'
            """,
        ),
        "open_study_threads": _count(
            conn,
            """
            SELECT COUNT(*) FROM selene_study_pondering_threads
            WHERE state != 'integrated_for_now'
              AND review_status = 'visible_open_learning_thread'
            """,
        ),
        "eligible_dream_reflections": _count(
            conn,
            """
            SELECT COUNT(*) FROM selene_dream_reflections
            WHERE state = 'approved_for_expression'
              AND review_status = 'reviewed' AND expression_eligible = 1
            """,
        ),
    }
    return _with_guards(
        {
            "status": "associative_intuition_bridge_ready",
            "version": ASSOCIATIVE_INTUITION_VERSION,
            "name": "Associative Intuition Bridge",
            "is_organ": False,
            "connective_tissue_only": True,
            "selection_and_routing_layer_only": True,
            "eligible_source_counts": counts,
            "principles": [
                "current cues may reactivate eligible earlier material without changing that material",
                "a felt connection may remain unarticulated without becoming failure",
                "an association is a candidate for inspection rather than evidence or proof",
                "Metacognition inspects fit and Structural Discovery or Hypothesis may develop the candidate",
                "Study and Dream handoffs are suggestions only and never automatic retention",
                "approved personal memory may provide lived context but not universal domain truth",
            ],
            "association_states": [
                "no_connection_noticed",
                "felt_connection",
                "articulated_connection",
                "held_for_context",
            ],
            "writes_records": False,
            "visible_summary_only": True,
            "review_status": "status_only",
            "provenance_boundary": ASSOCIATIVE_INTUITION_BOUNDARY,
        }
    )


def build_associative_intuition_bridge(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    trigger = truncate(
        str(payload.get("trigger_text") or payload.get("prompt") or payload.get("text") or ""),
        3000,
    ).strip()
    if not trigger:
        raise ValueError("an associative-intuition trigger is required")

    trigger_terms = _terms(trigger)
    trigger_cues = _semantic_cues(trigger)
    excluded_context_ids = _active_context_ids(payload.get("dual_horizon_context"))
    hard_boundary = payload.get("hard_boundary") is True
    diagnostic_only = payload.get("diagnostic_only") is True
    hold_optional_association = payload.get("hold_optional_association") is True
    maximum_scan = max(20, min(int(payload.get("maximum_scan") or 300), 600))
    maximum_candidates = max(1, min(int(payload.get("maximum_candidates") or 4), 8))
    speaker_envelope = (
        payload.get("speaker_envelope") if isinstance(payload.get("speaker_envelope"), dict) else {}
    )

    explicit_sources, explicit_held = _explicit_sources(payload.get("source_packets"))
    collected_sources, privacy_held = _collect_sources(
        conn,
        maximum_scan=maximum_scan,
        speaker_envelope=speaker_envelope,
    )
    sources = [*explicit_sources, *collected_sources]
    sources = _deduplicate_sources(sources)
    ranked: list[tuple[int, str, dict[str, Any]]] = []
    held: list[dict[str, Any]] = [*explicit_held, *privacy_held]
    scanned = 0

    for source in sources[:maximum_scan]:
        scanned += 1
        if source["context_id"] in excluded_context_ids:
            held.append(_held(source, "source_is_already_active_in_dual_horizon"))
            continue
        if source.get("expression_eligible") is False and source.get("study_only") is not True:
            held.append(_held(source, "source_state_is_not_eligible_for_association_use"))
            continue
        source_text = " ".join(
            str(source.get(key) or "")
            for key in ("title", "topic", "summary", "relationships", "details")
        )
        source_terms = _terms(source_text)
        source_cues = _semantic_cues(source_text)
        shared_terms = sorted(trigger_terms & source_terms)
        shared_cues = sorted(trigger_cues & source_cues)
        phrase_match = _phrase_match(trigger, source_text)
        score = (
            (3 * min(len(shared_terms), 4))
            + (2 * min(len(shared_cues), 4))
            + (2 if phrase_match else 0)
            + (1 if shared_cues and str(source.get("relationships") or "") else 0)
        )
        state = _association_state(shared_terms, shared_cues, score)
        if state == "no_connection_noticed":
            continue
        candidate = _candidate(
            trigger=trigger,
            source=source,
            state=state,
            score=score,
            shared_terms=shared_terms,
            shared_cues=shared_cues,
        )
        ranked.append((score, str(source.get("source_id") or ""), candidate))

    candidates = [
        item
        for _, _, item in sorted(ranked, key=lambda value: (-value[0], value[1]))[
            :maximum_candidates
        ]
    ]
    selected = candidates[0] if candidates else {}
    selected_state = str(selected.get("association_state") or "no_connection_noticed")
    contribution_ready = bool(
        selected
        and selected_state == "articulated_connection"
        and int(selected.get("activation_score") or 0) >= 8
        and not hard_boundary
        and not diagnostic_only
        and not hold_optional_association
        and selected.get("expression_eligible") is True
    )
    contribution_candidates = (
        [
            {
                "kind": "connection",
                "text": str(selected.get("candidate_summary") or ""),
                "why_it_matters": str(selected.get("why_it_may_matter") or ""),
                "source_refs": selected.get("safe_source_refs") or [],
                "relevance": "material",
                "confidence": "provisional_association",
                "upstream_validated": True,
                "advances_current_task": True,
                "what_would_change": selected.get("what_would_change") or [],
                "counterexamples": selected.get("counterexamples") or [],
            }
        ]
        if contribution_ready
        else []
    )
    source_refs = list(
        dict.fromkeys(
            ref
            for item in candidates
            for ref in item.get("safe_source_refs") or []
            if str(ref).strip()
        )
    )[:50]
    bridge_id = "association-" + sha256(
        f"{trigger}|{'|'.join(str(item.get('source_id') or '') for item in candidates)}".encode(
            "utf-8"
        )
    ).hexdigest()[:20]
    result = {
        "status": (
            "associative_intuition_candidate_ready"
            if selected
            else "associative_intuition_no_connection_noticed"
        ),
        "version": ASSOCIATIVE_INTUITION_VERSION,
        "bridge_id": bridge_id,
        "name": "Associative Intuition Bridge",
        "is_organ": False,
        "connective_tissue_only": True,
        "trigger_preview": truncate(trigger, 320),
        "trigger_cues": sorted(trigger_cues),
        "scanned_source_count": scanned,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "selected_candidate": selected,
        "selected_state": selected_state,
        "contribution_ready": contribution_ready,
        "optional_association_held_for_social_turn": hold_optional_association,
        "contribution_candidates": contribution_candidates,
        "held_back_sources": held[:30],
        "memory_privacy_gate_reused": True,
        "speaker_envelope_applied": bool(speaker_envelope),
        "metacognition_handoff": {
            "available": bool(selected),
            "association_state": selected_state,
            "candidate_summary": str(selected.get("candidate_summary") or ""),
            "activation_basis": selected.get("activation_basis") or {},
            "source_refs": selected.get("safe_source_refs") or [],
            "association_is_evidence": False,
            "association_is_proof": False,
            "fit_inspection_requested": bool(selected),
        },
        "structural_discovery_handoff": {
            "available": bool(selected),
            "development_needed": selected_state in {
                "felt_connection",
                "articulated_connection",
            },
            "source_domain": str(selected.get("source_domain") or ""),
            "target_domain": "current_context",
            "candidate_relation_cues": (selected.get("activation_basis") or {}).get(
                "shared_semantic_cues"
            )
            or [],
            "role_mappings_supplied": False,
            "automatic_structural_claim_created": False,
        },
        "study_handoff": {
            "available": bool(selected)
            and not diagnostic_only
            and (
                selected_state == "felt_connection"
                or selected.get("source_is_study_only") is True
            ),
            "suggested_kind": "connection",
            "suggested_title": truncate(
                f"Possible connection with {selected.get('source_title') or 'earlier material'}",
                300,
            )
            if selected
            else "",
            "missing_bridge": (
                "The relationship is noticeable, but its transferable structure is not articulated yet."
                if selected_state == "felt_connection"
                or selected.get("source_is_study_only") is True
                else ""
            ),
            "source_refs": selected.get("safe_source_refs") or [],
            "automatic_write": False,
        },
        "dream_handoff": {
            "available": bool(selected) and not diagnostic_only and not hard_boundary,
            "candidate_summary": str(selected.get("candidate_summary") or ""),
            "source_refs": selected.get("safe_source_refs") or [],
            "automatic_route": False,
            "dream_does_not_decide_truth": True,
        },
        "source_refs": source_refs,
        "association_is_evidence": False,
        "association_is_proof": False,
        "association_is_memory": False,
        "candidate_requires_downstream_fit_check": bool(selected),
        "stopping_receipt": _stopping_receipt(
            selected=selected,
            selected_state=selected_state,
            contribution_ready=contribution_ready,
            hard_boundary=hard_boundary,
            diagnostic_only=diagnostic_only,
            scanned=scanned,
            held_count=len(held),
        ),
        "writes_records": False,
        "visible_summary_only": True,
        "review_status": "diagnostic_only" if diagnostic_only else "status_only",
        "provenance_boundary": ASSOCIATIVE_INTUITION_BOUNDARY,
    }
    return _with_guards(result)


def accept_association_for_study(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    actor = str(payload.get("actor") or "").strip()
    if actor not in {"Aleks", "Selene"}:
        raise ValueError("an Association-to-Study handoff requires explicit Aleks or Selene acceptance")
    candidate_id = str(payload.get("candidate_id") or "").strip()
    if not candidate_id:
        raise ValueError("candidate_id is required")
    bridge = build_associative_intuition_bridge(
        conn,
        {
            "trigger_text": payload.get("trigger_text") or payload.get("prompt") or payload.get("text"),
            "dual_horizon_context": payload.get("dual_horizon_context") or {},
            "source_packets": payload.get("source_packets") or [],
            "speaker_envelope": payload.get("speaker_envelope") or {},
            "maximum_scan": payload.get("maximum_scan") or 300,
            "maximum_candidates": payload.get("maximum_candidates") or 8,
        },
    )
    candidate = next(
        (item for item in bridge.get("candidates") or [] if str(item.get("candidate_id") or "") == candidate_id),
        None,
    )
    if not candidate:
        raise ValueError("association candidate is no longer eligible in the supplied context")
    if str(candidate.get("association_state") or "") not in {"felt_connection", "articulated_connection"}:
        raise ValueError("only a felt or articulated provisional association can enter Study")

    attributable_sessions = _candidate_study_session_ids(conn, candidate)
    requested_session_id = int(payload.get("study_session_id") or 0)
    if requested_session_id:
        session_id = requested_session_id
    elif len(attributable_sessions) == 1:
        session_id = attributable_sessions[0]
    elif not attributable_sessions:
        raise ValueError("select an approved Study session for this association")
    else:
        raise ValueError("multiple attributable Study sessions require an explicit selection")
    session = conn.execute("SELECT * FROM selene_study_sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        raise ValueError("Study session not found")
    concept_ids = [int(value) for value in _loads(session["concept_ids_json"], []) if int(value) > 0]
    if not concept_ids:
        raise ValueError("Association-to-Study requires a session with approved Study material")
    marks = ",".join("?" for _ in concept_ids)
    approved_count = int(
        conn.execute(
            f"""
            SELECT COUNT(*) FROM selene_comprehension_concepts
            WHERE id IN ({marks})
              AND state = 'approved_knowledge_resource'
              AND review_status = 'approved_for_knowledge_use'
              AND chat_use_permission = 'available_as_knowledge_resource'
            """,
            tuple(concept_ids),
        ).fetchone()[0]
    )
    if approved_count != len(concept_ids):
        raise ValueError("Association-to-Study requires approved, Chat-eligible Study material")

    result = create_pondering_thread(
        conn,
        {
            "session_id": session_id,
            "title": truncate(
                str(payload.get("study_title") or f"Possible connection with {candidate.get('source_title') or 'earlier material'}"),
                300,
            ),
            "state": "active",
            "current_fit": (
                "Explicitly accepted provisional association: "
                f"{candidate.get('candidate_summary') or ''}"
            ),
            "missing_bridge": (
                "State the transferable roles, compare a distinct case, and keep the connection revisable."
            ),
            "revisit_cue": (
                "Stop if direct comparison supplies no new fit, a counterexample breaks the mapping, or the lineage is already active."
            ),
            "source_refs": [
                *(candidate.get("safe_source_refs") or []),
                f"associative_intuition_candidate:{candidate_id}",
            ],
            "lineage_key": f"associative_intuition:{candidate_id}:study_session:{session_id}",
            "origin_kind": "associative_intuition",
            "origin_ref": f"associative_intuition_candidate:{candidate_id}",
            "candidate_state": "provisional_association_not_evidence_proof_fact_memory_or_answer",
        },
    )
    created = bool(result.get("created"))
    return _with_guards(
        {
            "status": "association_entered_study" if created else "association_study_lineage_already_active",
            "name": "Associative Intuition Bridge",
            "is_organ": False,
            "connective_tissue_only": True,
            "accepted_by": actor,
            "bridge_id": bridge["bridge_id"],
            "candidate_id": candidate_id,
            "study_session_id": session_id,
            "study_thread_id": int(result["updated_thread_id"]),
            "created": created,
            "writes_records": True,
            "study_write_performed": created,
            "explicit_acceptance_required": True,
            "lineage_receipt": {
                **build_reflective_lineage_receipt(
                    origin_record_type="associative_intuition_candidate",
                    origin_record_id=candidate_id,
                    parent_record_type=str(candidate.get("source_class") or "association_source"),
                    parent_record_id=str(candidate.get("source_id") or ""),
                    destination="study_pondering",
                    destination_record_type="selene_study_pondering_thread",
                    destination_record_id=int(result["updated_thread_id"]),
                    candidate_state=str(candidate.get("association_state") or "provisional"),
                    source_refs=candidate.get("safe_source_refs") or [],
                    terminal_stop_reason=(None if created else "duplicate_lineage_existing_thread_reused"),
                    duplicate_lineage_detected=not created,
                ),
                "study_thread_lineage": result.get("lineage_receipt"),
            },
            "stopping_receipt": {
                "scan_stopped": True,
                "stop_reason": "explicit_acceptance_routed_once" if created else "duplicate_lineage_existing_thread_reused",
                "new_evidence_created": False,
                "truth_decided": False,
                "memory_written": False,
                "association_remains_provisional": True,
            },
            "association_is_evidence": False,
            "association_is_proof": False,
            "association_is_fact": False,
            "association_is_memory": False,
            "association_is_finished_answer": False,
            "review_status": "visible_study_pondering_thread",
            "provenance_boundary": ASSOCIATIVE_INTUITION_BOUNDARY,
        }
    )


def _candidate_study_session_ids(conn: sqlite3.Connection, candidate: dict[str, Any]) -> list[int]:
    source_id = str(candidate.get("source_id") or "")
    session_ids: set[int] = set()
    for prefix, table, id_column in (
        ("selene_study_note:", "selene_study_notes", "id"),
        ("selene_study_pondering_thread:", "selene_study_pondering_threads", "id"),
    ):
        if source_id.startswith(prefix):
            try:
                record_id = int(source_id[len(prefix):])
            except ValueError:
                continue
            row = conn.execute(
                f"SELECT session_id FROM {table} WHERE {id_column} = ?", (record_id,)
            ).fetchone()
            if row:
                session_ids.add(int(row["session_id"]))
    if source_id.startswith("selene_comprehension_concept:"):
        try:
            concept_id = int(source_id.rsplit(":", 1)[1])
        except ValueError:
            concept_id = 0
        if concept_id:
            for row in conn.execute("SELECT id, concept_ids_json FROM selene_study_sessions").fetchall():
                if concept_id in {int(value) for value in _loads(row["concept_ids_json"], [])}:
                    session_ids.add(int(row["id"]))
    return sorted(session_ids)


def _collect_sources(
    conn: sqlite3.Connection,
    *,
    maximum_scan: int,
    speaker_envelope: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    per_class = max(12, min(maximum_scan // 5, 120))
    sources: list[dict[str, Any]] = []
    held: list[dict[str, Any]] = []
    for row in conn.execute(
        """
        SELECT * FROM selene_comprehension_concepts
        WHERE state = 'approved_knowledge_resource'
          AND review_status = 'approved_for_knowledge_use'
          AND chat_use_permission = 'available_as_knowledge_resource'
        ORDER BY updated_at DESC, id DESC LIMIT ?
        """,
        (per_class,),
    ).fetchall():
        item = dict(row)
        source_id = f"selene_comprehension_concept:{item['id']}"
        sources.append(
            {
                "source_id": source_id,
                "context_id": f"approved-knowledge-{item['id']}",
                "source_class": "approved_general_knowledge",
                "title": str(item.get("title") or ""),
                "topic": str(item.get("domain") or "general"),
                "summary": str(item.get("central_claim") or ""),
                "relationships": " ".join(_loads(item.get("relationships_json"), [])),
                "details": " ".join(
                    [
                        *_loads(item.get("principles_json"), []),
                        *_loads(item.get("examples_json"), []),
                        *_loads(item.get("counterexamples_json"), []),
                        *_loads(item.get("limits_json"), []),
                    ]
                ),
                "owner_source_refs": _json_list(item.get("source_refs")),
                "safe_source_refs": [source_id],
                "confidence": str(item.get("confidence") or "reviewed"),
                "state": "approved_knowledge_resource",
                "expression_eligible": True,
                "study_only": False,
            }
        )
    for row in conn.execute(
        """
        SELECT * FROM selene_memory_candidates
        WHERE state = 'approved_active_memory'
          AND chat_use_permission = 'can_use_in_chat'
        ORDER BY updated_at DESC, id DESC LIMIT ?
        """,
        (min(per_class, 120),),
    ).fetchall():
        item = dict(row)
        source_id = f"selene_memory_candidate:{item['id']}"
        memory_payload = _loads(item.get("payload_json"), {})
        privacy_candidate = {
            "consent_scope": str(item.get("consent_scope") or ""),
            "eligible_channels": _text_list(memory_payload.get("eligible_channels")),
            "minimum_authentication_strength": str(
                memory_payload.get("minimum_authentication_strength") or ""
            ),
        }
        privacy = evaluate_memory_privacy_eligibility(privacy_candidate, speaker_envelope)
        if not speaker_envelope:
            privacy = {
                **privacy,
                "accepted": False,
                "reason": "speaker_envelope_missing_for_personal_memory",
                "speaker_privacy_gate_applied": False,
            }
        if privacy["accepted"] is not True:
            held.append(
                {
                    "source_id": source_id,
                    "source_class": "approved_personal_memory",
                    "reason": str(privacy["reason"]),
                    "privacy_gate": privacy,
                    "content_entered_candidate_text": False,
                    "candidate_created": False,
                    "stop_receipt": "held_before_association_text_construction",
                }
            )
            continue
        sources.append(
            {
                "source_id": source_id,
                "context_id": f"approved-memory-{item['id']}",
                "source_class": "approved_personal_memory",
                "title": str(item.get("title") or ""),
                "topic": str(item.get("memory_category") or "personal_context"),
                "summary": str(item.get("summary") or ""),
                "relationships": "",
                "details": "",
                "owner_source_refs": _json_list(item.get("source_refs")),
                "safe_source_refs": [source_id],
                "confidence": str(item.get("confidence") or "reviewed"),
                "state": "approved_active_memory",
                "expression_eligible": True,
                "study_only": False,
                "personal_memory_is_domain_truth": False,
                "privacy_gate": privacy,
            }
        )
    for row in conn.execute(
        """
        SELECT * FROM selene_study_notes
        WHERE note_kind IN ('connection', 'idea', 'revisit')
          AND review_status = 'selene_owned_working_study_note'
        ORDER BY updated_at DESC, id DESC LIMIT ?
        """,
        (min(per_class, 100),),
    ).fetchall():
        item = dict(row)
        source_id = f"selene_study_note:{item['id']}"
        sources.append(
            {
                "source_id": source_id,
                "context_id": source_id.replace(":", "-"),
                "source_class": "selene_study_connection",
                "title": str(item.get("meaning_summary") or "Study connection"),
                "topic": "study",
                "summary": str(item.get("meaning_summary") or ""),
                "relationships": str(item.get("note_text") or ""),
                "details": "",
                "owner_source_refs": _json_list(item.get("source_refs")),
                "safe_source_refs": [source_id],
                "confidence": "developing_study_connection",
                "state": str(item.get("clarification_state") or "not_needed"),
                "expression_eligible": str(item.get("clarification_state") or "")
                not in {"unclear", "question_forming", "reopened"},
                "study_only": str(item.get("clarification_state") or "")
                in {"unclear", "question_forming", "reopened"},
            }
        )
    for row in conn.execute(
        """
        SELECT * FROM selene_study_pondering_threads
        WHERE state != 'integrated_for_now'
          AND review_status = 'visible_open_learning_thread'
        ORDER BY updated_at DESC, id DESC LIMIT ?
        """,
        (min(per_class, 80),),
    ).fetchall():
        item = dict(row)
        source_id = f"selene_study_pondering_thread:{item['id']}"
        sources.append(
            {
                "source_id": source_id,
                "context_id": source_id.replace(":", "-"),
                "source_class": "selene_study_pondering",
                "title": str(item.get("title") or "Open study thread"),
                "topic": "study",
                "summary": str(item.get("current_fit") or item.get("title") or ""),
                "relationships": str(item.get("missing_bridge") or ""),
                "details": " ".join(
                    str(item.get(key) or "")
                    for key in ("prerequisite_needed", "revisit_cue")
                ),
                "owner_source_refs": _json_list(item.get("source_refs")),
                "safe_source_refs": [source_id],
                "confidence": "open_pondering_thread",
                "state": str(item.get("state") or "active"),
                "expression_eligible": False,
                "study_only": True,
            }
        )
    for row in conn.execute(
        """
        SELECT * FROM selene_dream_reflections
        WHERE state = 'approved_for_expression'
          AND review_status = 'reviewed' AND expression_eligible = 1
        ORDER BY updated_at DESC, id DESC LIMIT ?
        """,
        (min(per_class, 80),),
    ).fetchall():
        item = dict(row)
        source_id = f"selene_dream_reflection:{item['id']}"
        sources.append(
            {
                "source_id": source_id,
                "context_id": source_id.replace(":", "-"),
                "source_class": "approved_dream_reflection",
                "title": str(item.get("title") or "Dream reflection"),
                "topic": str(item.get("reflection_kind") or "reflection"),
                "summary": str(item.get("reflection") or ""),
                "relationships": str(item.get("why_it_may_matter") or ""),
                "details": str(item.get("uncertainty") or ""),
                "owner_source_refs": _json_list(item.get("source_refs")),
                "safe_source_refs": [source_id],
                "confidence": str(item.get("confidence") or "provisional"),
                "state": "approved_for_expression",
                "expression_eligible": True,
                "study_only": False,
            }
        )
    return sources, held


def _explicit_sources(value: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    result: list[dict[str, Any]] = []
    held: list[dict[str, Any]] = []
    for index, item in enumerate(value if isinstance(value, list) else []):
        if not isinstance(item, dict):
            continue
        source_ref = str(item.get("source_ref") or "").strip()
        if source_ref and _private_ref(source_ref):
            held.append(
                {
                    "source_id": f"held-current-source:{index + 1}",
                    "source_class": "current_attributed_source",
                    "reason": "private_source_reference_is_not_eligible_for_association_use",
                    "content_entered_candidate_text": False,
                    "candidate_created": False,
                    "stop_receipt": "held_before_association_text_construction",
                }
            )
            continue
        summary = truncate(
            str(item.get("summary") or item.get("statement") or item.get("content") or ""),
            1800,
        ).strip()
        if not source_ref or not summary:
            continue
        result.append(
            {
                "source_id": f"current_attributed_source:{index + 1}",
                "context_id": f"attributed-source-{index + 1}",
                "source_class": "current_attributed_source",
                "title": str(item.get("title") or "Current attributed source"),
                "topic": str(item.get("topic") or "current_source"),
                "summary": summary,
                "relationships": "",
                "details": "",
                "owner_source_refs": [source_ref],
                "safe_source_refs": [source_ref],
                "confidence": str(item.get("confidence") or "source_supplied"),
                "state": "current_attributed_source",
                "expression_eligible": True,
                "study_only": False,
            }
        )
    return result, held


def _candidate(
    *,
    trigger: str,
    source: dict[str, Any],
    state: str,
    score: int,
    shared_terms: list[str],
    shared_cues: list[str],
) -> dict[str, Any]:
    title = truncate(str(source.get("title") or "earlier material"), 240)
    basis_labels = [*shared_cues, *shared_terms][:6]
    basis_text = ", ".join(label.replace("_", " ") for label in basis_labels)
    if state == "felt_connection":
        summary = (
            f"Something in the current context may connect with {title}, "
            "but the transferable relationship is not articulated yet."
        )
    else:
        summary = (
            f"The current context may connect with {title} through "
            f"{basis_text or 'a shared relationship'}; the connection remains open to checking."
        )
    source_id = str(source.get("source_id") or "")
    candidate_id = "assoc-" + sha256(
        f"{trigger}|{source_id}|{state}|{basis_text}".encode("utf-8")
    ).hexdigest()[:20]
    return {
        "candidate_id": candidate_id,
        "association_state": state,
        "association_type": _association_type(shared_cues),
        "candidate_summary": truncate(summary, 1200),
        "why_it_may_matter": (
            "The earlier eligible material may supply a useful comparison, question, or direction for the current context without determining the answer."
        ),
        "activation_score": score,
        "activation_basis": {
            "shared_terms": shared_terms[:8],
            "shared_semantic_cues": shared_cues[:8],
            "surface_wording_alone_is_proof": False,
            "source_was_dormant_before_this_trigger": True,
        },
        "fit_receipt": {
            "fit_state": state,
            "source_domain": str(source.get("topic") or ""),
            "target_domain": "current_context",
            "shared_terms": shared_terms[:8],
            "shared_semantic_cues": shared_cues[:8],
            "transferable_structure_articulated": state == "articulated_connection",
            "new_evidence_supplied": False,
            "independent_fit_check_complete": False,
            "revision_required_if_counterexample_fits": True,
        },
        "source_id": source_id,
        "source_title": title,
        "source_domain": str(source.get("topic") or ""),
        "source_class": str(source.get("source_class") or ""),
        "source_state": str(source.get("state") or ""),
        "source_confidence": str(source.get("confidence") or ""),
        "safe_source_refs": _text_list(source.get("safe_source_refs")),
        "owner_record_preserves_full_provenance": True,
        "underlying_private_wording_exposed": False,
        "expression_eligible": source.get("expression_eligible") is True,
        "source_is_study_only": source.get("study_only") is True,
        "personal_memory_is_domain_truth": False,
        "what_would_change": [
            "The apparent shared relationship disappears when the two contexts are compared directly."
        ],
        "counterexamples": [
            "The same words or cues may occur while the underlying roles and relationships differ."
        ],
        "association_is_evidence": False,
        "association_is_proof": False,
        "automatic_conclusion": False,
    }


def _association_state(
    shared_terms: list[str],
    shared_cues: list[str],
    score: int,
) -> str:
    if score < 4:
        return "no_connection_noticed"
    if len(shared_terms) >= 2 or (shared_terms and shared_cues):
        return "articulated_connection"
    if len(shared_cues) >= 2:
        return "felt_connection"
    return "no_connection_noticed"


def _association_type(shared_cues: list[str]) -> str:
    cue_set = set(shared_cues)
    if "evidence_uncertainty" in cue_set or "feedback_correction" in cue_set:
        return "tension_or_reopening_lead"
    if "cause_effect" in cue_set:
        return "causal_candidate"
    if "prediction_model" in cue_set:
        return "prediction_lead"
    if "comparison_distinction" in cue_set:
        return "analogy_or_comparison_lead"
    return "possible_recurrence"


def _active_context_ids(value: Any) -> set[str]:
    packet = value if isinstance(value, dict) else {}
    ids: set[str] = set()
    for horizon_name in ("active_horizon", "approved_long_range_horizon"):
        horizon = packet.get(horizon_name) if isinstance(packet.get(horizon_name), dict) else {}
        ids.update(str(item) for item in horizon.get("selected_context_ids") or [] if str(item))
    return ids


def _semantic_cues(value: str) -> set[str]:
    words = set(re.findall(r"[a-z][a-z0-9'-]{1,}", str(value or "").lower()))
    return {
        family
        for family, vocabulary in _CUE_FAMILIES.items()
        if words.intersection(vocabulary)
    }


def _terms(value: str) -> set[str]:
    return {
        term
        for term in re.findall(r"[a-z][a-z0-9'-]{2,}", str(value or "").lower())
        if term not in _STOP
    }


def _phrase_match(left: str, right: str) -> bool:
    left_words = [word for word in re.findall(r"[a-z][a-z0-9'-]{2,}", left.lower()) if word not in _STOP]
    right_lower = right.lower()
    return any(
        " ".join(left_words[index : index + 2]) in right_lower
        for index in range(max(0, len(left_words) - 1))
    )


def _deduplicate_sources(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        source_id = str(item.get("source_id") or "")
        if not source_id or source_id in seen:
            continue
        seen.add(source_id)
        result.append(item)
    return result


def _held(source: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "source_id": str(source.get("source_id") or ""),
        "source_class": str(source.get("source_class") or ""),
        "reason": reason,
        "content_entered_candidate_text": False,
        "candidate_created": False,
    }


def _stopping_receipt(
    *,
    selected: dict[str, Any],
    selected_state: str,
    contribution_ready: bool,
    hard_boundary: bool,
    diagnostic_only: bool,
    scanned: int,
    held_count: int,
) -> dict[str, Any]:
    if hard_boundary:
        reason = "hard_boundary_holds_association_handoffs"
    elif diagnostic_only:
        reason = "diagnostic_preview_stops_before_promotion"
    elif not selected:
        reason = "no_useful_connection_noticed"
    elif selected_state == "felt_connection":
        reason = "transferable_structure_not_articulated"
    elif contribution_ready:
        reason = "one_provisional_candidate_released_for_downstream_fit_check"
    else:
        reason = "candidate_held_for_context_or_source_scope"
    return {
        "scan_stopped": True,
        "stop_reason": reason,
        "scanned_source_count": scanned,
        "held_source_count": held_count,
        "selected_candidate_id": str(selected.get("candidate_id") or "") or None,
        "new_evidence_created": False,
        "truth_decided": False,
        "memory_written": False,
        "study_written": False,
        "recursive_reactivation_requested": False,
    }


def _count(conn: sqlite3.Connection, sql: str) -> int:
    return int(conn.execute(sql).fetchone()[0])


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, type(fallback)):
        return value
    try:
        decoded = json.loads(str(value or ""))
    except (TypeError, json.JSONDecodeError):
        return fallback
    return decoded if isinstance(decoded, type(fallback)) else fallback


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return _text_list(value)
    if isinstance(value, str):
        return _text_list(_loads(value, []))
    return []


def _text_list(value: Any) -> list[str]:
    values = value if isinstance(value, (list, tuple)) else [value]
    return [truncate(str(item), 500).strip() for item in values if str(item).strip()][:50]


def _private_ref(value: str) -> bool:
    lowered = str(value or "").strip().lower()
    return lowered.startswith(PRIVATE_SOURCE_PREFIXES)


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
