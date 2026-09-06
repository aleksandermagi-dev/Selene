from __future__ import annotations

import json
import re
import sqlite3
from hashlib import sha256
from typing import Any

from .input_detangler import detangle_user_input
from .conversation_signals import correction_signal
from .long_thread_endurance import (
    build_long_thread_endurance_plan,
    protected_thread_ids_for_workspace,
    retain_structural_records,
)
from .conversation_thread_loom import build_thread_braid
from .epistemic_revision import (
    build_epistemic_revision_plan,
    compact_epistemic_update,
)
from .dual_horizon_context import (
    build_session_topic_checkpoint,
    merge_session_topic_checkpoints,
)
from .referent_address import resolve_referent_address
from .registry import truncate
from .session_proposition_ledger import (
    prepare_session_proposition_revision,
    record_visible_session_propositions,
)


DIALOGUE_BOUNDARY = (
    "session_scoped_dialogue_continuity_only_not_durable_memory_identity_profile_runtime_recall_or_authority"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "durable_preference_write": False,
}

STOP_WORDS = {
    "a", "about", "and", "are", "as", "at", "be", "but", "can", "could", "do", "does", "for", "from",
    "how", "i", "if", "in", "is", "it", "me", "my", "of", "on", "or", "please", "should", "so", "that",
    "the", "this", "to", "we", "what", "when", "where", "which", "who", "why", "will", "with", "would",
    "you", "your", "selene",
}


def dialogue_workspace_status(conn: sqlite3.Connection, session_id: int) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM selene_dialogue_workspaces WHERE session_id = ?", (int(session_id),)).fetchone()
    if row is None:
        return _with_guards(
            {
                "status": "dialogue_workspace_empty",
                "session_id": int(session_id),
                "active_topic": "",
                "side_topics": [],
                "entities": [],
                "referents": {},
                "open_loops": [],
                "completed_loops": [],
                "corrections": [],
                "epistemic_updates": [],
                "session_proposition_ledger": {},
                "preferences": {},
                "session_landmarks": [],
                "topic_checkpoints": [],
                "review_destination": "Status",
                "review_status": "status_only",
                "provenance_boundary": DIALOGUE_BOUNDARY,
            }
        )
    return _decode(row)


def prepare_dialogue_turn(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    *,
    commit: bool = True,
) -> dict[str, Any]:
    payload = payload or {}
    session_id = int(payload.get("session_id") or 0)
    if session_id <= 0:
        raise ValueError("session_id is required")
    text = truncate(str(payload.get("text") or payload.get("prompt") or ""), 2400)
    if not text.strip():
        raise ValueError("dialogue text is required")
    input_interpretation = (
        payload.get("input_interpretation")
        if isinstance(payload.get("input_interpretation"), dict)
        else detangle_user_input(text)
    )
    figurative_interpretation = (
        payload.get("figurative_interpretation")
        if isinstance(payload.get("figurative_interpretation"), dict)
        else {}
    )
    interpreted_text = truncate(
        str(
            payload.get("interpreted_text")
            or figurative_interpretation.get("interpreted_text")
            or input_interpretation.get("interpreted_text")
            or text
        ),
        2400,
    )
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    contextual_follow_up = (
        payload.get("contextual_follow_up")
        if isinstance(payload.get("contextual_follow_up"), dict)
        else {}
    )
    prior = dialogue_workspace_status(conn, session_id)
    prior_pragmatics = prior.get("pragmatics") if isinstance(prior.get("pragmatics"), dict) else {}
    events = _events(conn, session_id, payload.get("conversation_events"))
    previous = events[-1] if events else {}
    active_topic = _active_topic(
        interpreted_text,
        str(prior.get("active_topic") or ""),
        str(intent.get("intent") or ""),
        preserve_prior=contextual_follow_up.get("preserve_active_topic") is True,
    )
    questions = _question_units(interpreted_text)
    loops = list(prior.get("open_loops") or [])
    new_loops = [
        {
            "id": _loop_id(session_id, question, index),
            "question": question,
            "status": "open",
            "topic": _topic(question) or active_topic,
            "age_turns": 0,
            "lifecycle_state": "active_current_turn",
            "eligible_current_turn": True,
            "hold_reason": "",
        }
        for index, question in enumerate(questions)
    ]
    existing_ids = {str(item.get("id") or "") for item in loops if isinstance(item, dict)}
    loops.extend(item for item in new_loops if item["id"] not in existing_ids)
    referents = dict(prior.get("referents") or {})
    reference = _resolve_reference(
        interpreted_text,
        previous,
        active_topic,
        prior_referents=referents,
        recent_events=events,
    )
    if reference:
        referents[reference["token"]] = reference
    referent_address = resolve_referent_address(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "interpreted_text": interpreted_text,
            "speaker_context": payload.get("speaker_context"),
            "prior_state": prior_pragmatics.get("referent_address") or {},
        },
    )
    direct_address = (
        referent_address.get("direct_address")
        if isinstance(referent_address.get("direct_address"), dict)
        else {}
    )
    if direct_address:
        referents[f"address:{direct_address.get('normalized') or direct_address.get('token')}"] = {
            "token": direct_address.get("token"),
            "resolved_to": direct_address.get("referent"),
            "resolution_status": direct_address.get("resolution_status"),
            "confidence": direct_address.get("confidence"),
            "reference_kind": "direct_address",
            "session_scoped": True,
        }
    for assertion in referent_address.get("alias_assertions") or []:
        if not isinstance(assertion, dict):
            continue
        for alias in assertion.get("aliases") or []:
            referents[f"alias:{str(alias).casefold()}"] = {
                "token": str(alias),
                "resolved_to": str(assertion.get("referent") or "current_user"),
                "resolution_status": "explicit_session_alias",
                "confidence": "high",
                "reference_kind": "name_or_alias",
                "session_scoped": True,
                "identity_change": False,
            }
    entities = _merge_entities(prior.get("entities") or [], _extract_entities(interpreted_text))
    corrections = list(prior.get("corrections") or [])
    correction = _correction_refinement(
        interpreted_text,
        previous,
        contextual_follow_up=contextual_follow_up,
    )
    topic_transition = str(contextual_follow_up.get("kind") or "") == "topic_shift" or any(
        marker in interpreted_text.lower()
        for marker in (
            "separate topic",
            "different topic",
            "new topic",
            "on another topic",
            "separate question",
            "different question",
            "new question",
        )
    )
    corrections = _advance_correction_lifecycle(
        corrections,
        current_correction_detected=correction.get("detected") is True,
        topic_transition=topic_transition,
        prior_recomputation=(
            (prior_pragmatics.get("session_proposition_ledger") or {}).get("recomputation")
            if isinstance(prior_pragmatics.get("session_proposition_ledger"), dict)
            else {}
        ),
    )
    epistemic_updates = [
        item for item in prior_pragmatics.get("epistemic_updates") or [] if isinstance(item, dict)
    ][-12:]
    epistemic_update_plan = build_epistemic_revision_plan(
        {
            "prompt": interpreted_text,
            "correction_refinement": correction,
            "previous_claims": [str(previous.get("preview") or "")],
            "prior_updates": epistemic_updates,
            "source_refs": [f"selene_chat_session:{session_id}:current_turn"],
        }
    )
    if epistemic_update_plan.get("detected") is True:
        epistemic_updates.append(compact_epistemic_update(epistemic_update_plan))
    if str(intent.get("intent") or "") == "correction" or correction.get("detected") is True:
        corrections.append({**correction, "status": "active_refinement"})
    figurative_update = (
        figurative_interpretation.get("interpretation_update")
        if isinstance(figurative_interpretation.get("interpretation_update"), dict)
        else {}
    )
    if figurative_update.get("detected") is True:
        corrections.append({**figurative_update, "status": "active_refinement"})
    preferences = _advance_session_preferences(
        prior.get("preferences") if isinstance(prior.get("preferences"), dict) else {},
        original_text=text,
        interpreted_text=interpreted_text,
        figurative_interpretation=figurative_interpretation,
        contextual_follow_up=contextual_follow_up,
    )
    utterance_units = _utterance_units(
        interpreted_text,
        contextual_follow_up=contextual_follow_up,
    )
    thread_braid = build_thread_braid(
        {
            "session_id": session_id,
            "prompt": interpreted_text,
            "utterance_units": utterance_units,
            "prior_braid": prior_pragmatics.get("thread_braid") or {},
            "active_topic": active_topic,
            "thread_hints": payload.get("thread_hints") or [],
            "protected_thread_ids": sorted(
                protected_thread_ids_for_workspace(prior)
            ),
        }
    )
    active_thread_id = str(thread_braid.get("active_thread_id") or "")
    new_loop_ids = {str(item.get("id") or "") for item in new_loops}
    loops = [
        {
            **item,
            **(
                {"thread_id": active_thread_id}
                if isinstance(item, dict)
                and str(item.get("id") or "") in new_loop_ids
                and active_thread_id
                else {}
            ),
        }
        if isinstance(item, dict)
        else item
        for item in loops
    ]
    active_thread = next(
        (
            item
            for item in thread_braid.get("threads") or []
            if isinstance(item, dict)
            and str(item.get("id") or "")
            == str(thread_braid.get("active_thread_id") or "")
        ),
        {},
    )
    session_proposition_ledger = prepare_session_proposition_revision(
        {
            "session_id": session_id,
            "prior_ledger": prior_pragmatics.get("session_proposition_ledger") or {},
            "correction_refinement": correction,
            "epistemic_revision_plan": epistemic_update_plan,
            "turn_id": _loop_id(session_id, interpreted_text, 0).replace("dialogue_loop", "dialogue_turn"),
            "thread_id": active_thread_id,
            "topic_transition": topic_transition,
        }
    )
    returned_to_prior_thread = bool(
        str(thread_braid.get("active_thread_id") or "")
        and str(thread_braid.get("prior_active_thread_id") or "")
        and str(thread_braid.get("active_thread_id") or "")
        != str(thread_braid.get("prior_active_thread_id") or "")
        and any(
            str(item.get("relation") or "") == "returns_to"
            and str(item.get("target_thread_id") or "")
            == str(thread_braid.get("active_thread_id") or "")
            for item in thread_braid.get("edges") or []
            if isinstance(item, dict)
        )
    )
    if (
        str(contextual_follow_up.get("kind") or "") in {"named_callback", "topic_shift"}
        or returned_to_prior_thread
        or any(
            str(item.get("action") or "")
            in {"branch", "land", "revise_with_dependency"}
            for item in thread_braid.get("turn_traversal") or []
            if isinstance(item, dict)
        )
    ) and str(active_thread.get("topic") or "").strip():
        active_topic = truncate(str(active_thread.get("topic") or ""), 500)
    loops, retired_loops = _advance_loop_lifecycle(
        loops,
        new_loop_ids=new_loop_ids,
        active_thread_id=active_thread_id,
        active_topic=active_topic,
        current_text=interpreted_text,
        contextual_follow_up=contextual_follow_up,
        correction=correction,
        intent=str(intent.get("intent") or ""),
        returned_to_prior_thread=returned_to_prior_thread,
    )
    braided_side_topics = [
        str(item.get("topic") or "")
        for item in thread_braid.get("threads") or []
        if isinstance(item, dict)
        and str(item.get("id") or "") != str(thread_braid.get("active_thread_id") or "")
        and str(item.get("topic") or "")
    ]
    side_topics = list(
        dict.fromkeys(
            [
                *list(prior.get("side_topics") or []),
                *[_topic(item) for item in questions[1:] if _topic(item)],
                *braided_side_topics,
            ]
        )
    )[-12:]
    pragmatics = {
        "dialogue_act": str(intent.get("dialogue_act") or intent.get("intent") or "direct_conversation"),
        "active_topic": active_topic,
        "resolved_reference": reference,
        "referent_address": referent_address,
        "reference_candidates": (reference or {}).get("candidates") or [],
        "correction_refinement": correction,
        "epistemic_update_plan": epistemic_update_plan,
        "epistemic_updates": retain_structural_records(
            epistemic_updates,
            limit=24,
            unresolved_first=True,
        ),
        "session_proposition_ledger": session_proposition_ledger,
        "utterance_units": utterance_units,
        "question_units": questions,
        "multi_part_prompt": len(questions) > 1,
        "indirect_request": _indirect_request(interpreted_text),
        "quoted_material": _quotes(interpreted_text),
        "input_interpretation": input_interpretation,
        "figurative_interpretation": figurative_interpretation,
        "response_preference": preferences.get("response_depth") or "",
        "previous_turn_available": bool(previous),
        "previous_turn": previous,
        "contextual_follow_up": contextual_follow_up,
        "thread_braid": thread_braid,
        "session_facts": [
            item
            for item in prior_pragmatics.get("session_facts") or []
            if isinstance(item, dict)
        ][-20:],
        "session_landmarks": retain_structural_records(
            [item for item in prior_pragmatics.get("session_landmarks") or [] if isinstance(item, dict)],
            limit=64,
            protected_thread_ids=protected_thread_ids_for_workspace(prior),
        ),
        "topic_checkpoints": retain_structural_records(
            [item for item in prior_pragmatics.get("topic_checkpoints") or [] if isinstance(item, dict)],
            limit=64,
            protected_thread_ids=protected_thread_ids_for_workspace(prior),
        ),
    }
    state = {
        "status": "dialogue_workspace_turn_prepared",
        "session_id": session_id,
        "active_topic": active_topic,
        "side_topics": side_topics,
        "entities": entities,
        "referents": referents,
        "open_loops": retain_structural_records(
            [item for item in loops if isinstance(item, dict)],
            limit=64,
            protected_thread_ids=protected_thread_ids_for_workspace(prior),
            unresolved_first=True,
        ),
        "completed_loops": [
            *list(prior.get("completed_loops") or []),
            *retired_loops,
        ][-30:],
        "corrections": retain_structural_records(
            [item for item in corrections if isinstance(item, dict)],
            limit=32,
            protected_thread_ids=protected_thread_ids_for_workspace(prior),
            unresolved_first=True,
        ),
        "epistemic_updates": retain_structural_records(
            epistemic_updates,
            limit=24,
            unresolved_first=True,
        ),
        "session_proposition_ledger": session_proposition_ledger,
        "preferences": preferences,
        "last_dialogue_act": pragmatics["dialogue_act"],
        "last_user_preview": truncate(text, 360),
        "last_selene_preview": str(prior.get("last_selene_preview") or ""),
        "pragmatics": pragmatics,
        "new_loop_ids": [item["id"] for item in new_loops],
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": DIALOGUE_BOUNDARY,
    }
    endurance = build_long_thread_endurance_plan(
        {"dialogue_workspace": state}
    )
    state["long_thread_endurance"] = endurance
    state["pragmatics"]["long_thread_endurance"] = endurance
    _upsert(conn, state)
    if commit:
        conn.commit()
    return _with_guards(state)


def record_dialogue_response(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    *,
    commit: bool = True,
) -> dict[str, Any]:
    payload = payload or {}
    session_id = int(payload.get("session_id") or 0)
    if session_id <= 0:
        raise ValueError("session_id is required")
    candidate = truncate(str(payload.get("candidate_text") or payload.get("text") or ""), 2400)
    state = dialogue_workspace_status(conn, session_id)
    coverage = payload.get("coverage_evaluation") if isinstance(payload.get("coverage_evaluation"), dict) else {}
    answered_source = coverage.get("answered_loop_ids") if coverage else payload.get("answered_loop_ids")
    answered_ids = {str(item) for item in answered_source or [] if str(item)}
    coverage_by_loop = {
        str(item.get("loop_id") or ""): item
        for item in coverage.get("items") or []
        if isinstance(item, dict) and str(item.get("loop_id") or "")
    }
    open_loops = []
    completed = list(state.get("completed_loops") or [])
    for item in state.get("open_loops") or []:
        if isinstance(item, dict) and str(item.get("id") or "") in answered_ids:
            completed.append(
                {
                    **item,
                    "status": "answered_in_current_turn",
                    "lifecycle_state": "completed",
                    "eligible_current_turn": False,
                    "hold_reason": "",
                }
            )
        else:
            loop_id = str(item.get("id") or "") if isinstance(item, dict) else ""
            loop_coverage = coverage_by_loop.get(loop_id, {})
            resolution_state = str(loop_coverage.get("resolution_state") or "")
            if isinstance(item, dict):
                open_loops.append(
                    {
                        **item,
                        "status": (
                            "supported_hold"
                            if resolution_state in {"explicitly_held", "supported_route"}
                            else "open"
                        ),
                        "lifecycle_state": "held_for_supported_return",
                        "eligible_current_turn": False,
                        "hold_reason": (
                            resolution_state
                            if resolution_state in {"explicitly_held", "supported_route"}
                            else "unanswered_current_turn"
                        ),
                    }
                )
            else:
                open_loops.append(item)
    pragmatics = state.get("pragmatics") if isinstance(state.get("pragmatics"), dict) else {}
    conversation_spine = (
        payload.get("conversation_spine")
        if isinstance(payload.get("conversation_spine"), dict)
        else {}
    )
    session_facts = [
        item
        for item in conversation_spine.get("session_facts") or pragmatics.get("session_facts") or []
        if isinstance(item, dict)
    ][-20:]
    prior_landmarks = [
        item for item in pragmatics.get("session_landmarks") or [] if isinstance(item, dict)
    ]
    new_landmarks = _response_landmarks(
        candidate,
        active_topic=str(state.get("active_topic") or ""),
        thread_braid=pragmatics.get("thread_braid") if isinstance(pragmatics.get("thread_braid"), dict) else {},
        coverage=coverage,
    )
    session_proposition_ledger = record_visible_session_propositions(
        {
            "session_id": session_id,
            "ledger": pragmatics.get("session_proposition_ledger") or {},
            "candidate_text": candidate,
            "turn_id": str(conversation_spine.get("turn_id") or ""),
            "thread_id": str(
                (
                    pragmatics.get("thread_braid")
                    if isinstance(pragmatics.get("thread_braid"), dict)
                    else {}
                ).get("active_thread_id")
                or ""
            ),
            "response_landmarks": new_landmarks,
            "coverage_evaluation": coverage,
            "answer_operations": payload.get("answer_operations") or {},
            "claim_evidence_packet": payload.get("claim_evidence_packet") or {},
        }
    )
    landmark_propositions = {
        str(item.get("landmark_id") or ""): str(item.get("id") or "")
        for item in session_proposition_ledger.get("propositions") or []
        if isinstance(item, dict) and str(item.get("landmark_id") or "")
    }
    recomputed_proposition_id = str(
        (session_proposition_ledger.get("recomputation") or {}).get(
            "recomputed_proposition_id"
        )
        or ""
    )
    new_landmarks = [
        {
            **item,
            "proposition_id": (
                landmark_propositions.get(str(item.get("id") or ""), "")
                or recomputed_proposition_id
            ),
        }
        for item in new_landmarks
    ]
    session_landmarks = _merge_landmarks(prior_landmarks, new_landmarks)
    prior_checkpoints = [
        item
        for item in pragmatics.get("topic_checkpoints") or []
        if isinstance(item, dict)
    ]
    checkpoint = build_session_topic_checkpoint(
        {
            **payload,
            "session_id": session_id,
            "candidate_text": candidate,
            "dialogue_workspace": state,
            "response_coverage": coverage,
            "prior_checkpoints": prior_checkpoints,
        }
    )
    topic_checkpoints = merge_session_topic_checkpoints(
        prior_checkpoints,
        checkpoint,
    )
    updated = {
        **state,
        "status": "dialogue_workspace_response_recorded",
        "open_loops": retain_structural_records(
            [item for item in open_loops if isinstance(item, dict)],
            limit=64,
            protected_thread_ids=protected_thread_ids_for_workspace(state),
            unresolved_first=True,
        ),
        "completed_loops": completed[-30:],
        "last_selene_preview": truncate(candidate, 360),
        "pragmatics": {
            **pragmatics,
            "session_facts": session_facts,
            "last_response_coverage": coverage,
            "session_landmarks": session_landmarks,
            "topic_checkpoints": topic_checkpoints,
            "latest_topic_checkpoint": (
                checkpoint
                if checkpoint.get("status") == "session_topic_checkpoint_ready"
                else {}
            ),
            "session_proposition_ledger": session_proposition_ledger,
        },
        "session_proposition_ledger": session_proposition_ledger,
        "session_landmarks": session_landmarks,
        "topic_checkpoints": topic_checkpoints,
        "latest_topic_checkpoint": (
            checkpoint
            if checkpoint.get("status") == "session_topic_checkpoint_ready"
            else {}
        ),
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": DIALOGUE_BOUNDARY,
    }
    endurance = build_long_thread_endurance_plan(
        {
            "dialogue_workspace": updated,
            "conversation_spine": conversation_spine,
            "dual_horizon_context": payload.get("dual_horizon_context") or {},
        }
    )
    updated["long_thread_endurance"] = endurance
    updated["pragmatics"]["long_thread_endurance"] = endurance
    _upsert(conn, updated)
    if commit:
        conn.commit()
    return _with_guards(updated)


def _upsert(conn: sqlite3.Connection, state: dict[str, Any]) -> None:
    conn.execute(
        """
        INSERT INTO selene_dialogue_workspaces
        (session_id, active_topic, side_topics_json, entities_json, referents_json, open_loops_json,
         completed_loops_json, corrections_json, preferences_json, last_dialogue_act,
         last_user_preview, last_selene_preview, state_json, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
          active_topic=excluded.active_topic,
          side_topics_json=excluded.side_topics_json,
          entities_json=excluded.entities_json,
          referents_json=excluded.referents_json,
          open_loops_json=excluded.open_loops_json,
          completed_loops_json=excluded.completed_loops_json,
          corrections_json=excluded.corrections_json,
          preferences_json=excluded.preferences_json,
          last_dialogue_act=excluded.last_dialogue_act,
          last_user_preview=excluded.last_user_preview,
          last_selene_preview=excluded.last_selene_preview,
          state_json=excluded.state_json,
          provenance_boundary=excluded.provenance_boundary,
          updated_at=CURRENT_TIMESTAMP
        """,
        (
            int(state.get("session_id") or 0),
            str(state.get("active_topic") or ""),
            json.dumps(state.get("side_topics") or []),
            json.dumps(state.get("entities") or []),
            json.dumps(state.get("referents") or {}),
            json.dumps(state.get("open_loops") or []),
            json.dumps(state.get("completed_loops") or []),
            json.dumps(state.get("corrections") or []),
            json.dumps(state.get("preferences") or {}),
            str(state.get("last_dialogue_act") or ""),
            str(state.get("last_user_preview") or ""),
            str(state.get("last_selene_preview") or ""),
            json.dumps(state.get("pragmatics") or state.get("state") or {}),
            DIALOGUE_BOUNDARY,
        ),
    )


def _decode(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    pragmatics = _loads(item.get("state_json"), {})
    return _with_guards(
        {
            "status": "dialogue_workspace_ready",
            "id": item.get("id"),
            "session_id": item.get("session_id"),
            "active_topic": item.get("active_topic"),
            "side_topics": _loads(item.get("side_topics_json"), []),
            "entities": _loads(item.get("entities_json"), []),
            "referents": _loads(item.get("referents_json"), {}),
            "open_loops": _loads(item.get("open_loops_json"), []),
            "completed_loops": _loads(item.get("completed_loops_json"), []),
            "corrections": _loads(item.get("corrections_json"), []),
            "epistemic_updates": retain_structural_records(
                [
                    value
                    for value in pragmatics.get("epistemic_updates") or []
                    if isinstance(value, dict)
                ],
                limit=24,
                unresolved_first=True,
            ),
            "session_proposition_ledger": (
                pragmatics.get("session_proposition_ledger")
                if isinstance(pragmatics.get("session_proposition_ledger"), dict)
                else {}
            ),
            "preferences": _loads(item.get("preferences_json"), {}),
            "last_dialogue_act": item.get("last_dialogue_act"),
            "last_user_preview": item.get("last_user_preview"),
            "last_selene_preview": item.get("last_selene_preview"),
            "pragmatics": pragmatics,
            "session_landmarks": retain_structural_records(
                [value for value in pragmatics.get("session_landmarks") or [] if isinstance(value, dict)],
                limit=64,
            ),
            "topic_checkpoints": retain_structural_records(
                [
                    value
                    for value in pragmatics.get("topic_checkpoints") or []
                    if isinstance(value, dict)
                ],
                limit=64,
            ),
            "long_thread_endurance": (
                pragmatics.get("long_thread_endurance")
                if isinstance(pragmatics.get("long_thread_endurance"), dict)
                else {}
            ),
            "latest_topic_checkpoint": (
                pragmatics.get("latest_topic_checkpoint")
                if isinstance(pragmatics.get("latest_topic_checkpoint"), dict)
                else {}
            ),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": DIALOGUE_BOUNDARY,
        }
    )


def _events(conn: sqlite3.Connection, session_id: int, supplied: Any) -> list[dict[str, Any]]:
    if isinstance(supplied, list):
        return [item for item in supplied if isinstance(item, dict)][-8:]
    rows = conn.execute(
        "SELECT role, content AS preview, created_at FROM selene_chat_messages WHERE session_id = ? ORDER BY id DESC LIMIT 8",
        (session_id,),
    ).fetchall()
    return [dict(row) for row in reversed(rows)]


def _active_topic(text: str, prior: str, intent: str, *, preserve_prior: bool = False) -> str:
    if preserve_prior and prior:
        return prior
    if intent in {"greeting", "farewell", "gratitude", "affirmation", "reassurance_received", "warm_connection"}:
        return prior
    return _topic(text) or prior


def _advance_loop_lifecycle(
    loops: list[Any],
    *,
    new_loop_ids: set[str],
    active_thread_id: str,
    active_topic: str,
    current_text: str,
    contextual_follow_up: dict[str, Any],
    correction: dict[str, Any],
    intent: str,
    returned_to_prior_thread: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Preserve unanswered questions without making them perpetual authority."""

    active: list[dict[str, Any]] = []
    retired: list[dict[str, Any]] = []
    callback_kind = str(contextual_follow_up.get("kind") or "")
    explicit_return = bool(
        returned_to_prior_thread
        or contextual_follow_up.get("preserve_active_topic") is True
        or callback_kind in {
            "named_callback",
            "reason_follow_up",
            "alternative_reference",
            "session_summary_request",
        }
    )
    current_terms = set(_topic(current_text).split())
    correction_active = correction.get("detected") is True or intent == "correction"

    for raw in loops:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        loop_id = str(item.get("id") or "")
        if loop_id in new_loop_ids:
            active.append(
                {
                    **item,
                    "thread_id": str(item.get("thread_id") or active_thread_id),
                    "age_turns": 0,
                    "lifecycle_state": "active_current_turn",
                    "eligible_current_turn": True,
                    "hold_reason": "",
                }
            )
            continue

        age = int(item.get("age_turns") or 0) + 1
        loop_thread = str(item.get("thread_id") or "")
        same_thread = bool(active_thread_id and loop_thread == active_thread_id)
        loop_terms = set(_topic(str(item.get("question") or item.get("topic") or "")).split())
        topic_overlap = len(current_terms & loop_terms)

        if intent == "farewell":
            retired.append(
                {
                    **item,
                    "age_turns": age,
                    "status": "closed_on_conversation_end",
                    "lifecycle_state": "closed",
                    "eligible_current_turn": False,
                    "hold_reason": "conversation_closed",
                }
            )
            continue
        if correction_active and (same_thread or topic_overlap >= 1):
            retired.append(
                {
                    **item,
                    "age_turns": age,
                    "status": "superseded_by_correction",
                    "lifecycle_state": "superseded",
                    "eligible_current_turn": False,
                    "hold_reason": "current_correction_replaced_prior_obligation",
                }
            )
            continue

        # Returning to a thread does not reopen every unanswered question on
        # that thread. The current wording must also identify the old subject.
        released = bool(explicit_return and topic_overlap >= 2)
        active.append(
            {
                **item,
                "age_turns": age,
                "status": "open" if released else "held_for_relevance",
                "lifecycle_state": "released_for_callback" if released else "held_for_supported_return",
                "eligible_current_turn": released,
                "hold_reason": "" if released else "not_selected_by_current_topic_or_thread",
            }
        )
    return active, retired


def _topic(text: str) -> str:
    words = [word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text)]
    useful = [word for word in words if word not in STOP_WORDS]
    return " ".join(useful[:8])


def _question_units(text: str) -> list[str]:
    units: list[str] = []
    for sentence in re.split(r"(?<=[.!?])[\"”']?\s+", text.strip()):
        sentence = sentence.strip()
        if not sentence.endswith("?") or not sentence.strip(" ,.;?"):
            continue
        segments = _utterance_units(sentence)
        if any(str(item.get("kind") or "") == "correction" for item in segments):
            units.extend(
                str(item.get("text") or "").strip(" ,.;")
                for item in segments
                if str(item.get("kind") or "") == "question"
                and str(item.get("text") or "").strip(" ,.;?")
            )
        else:
            units.append(sentence.strip(" ,.;"))
    return [item if item.endswith("?") else item + "?" for item in units[:8]]


def _resolve_reference(
    text: str,
    previous: dict[str, Any],
    active_topic: str,
    *,
    prior_referents: dict[str, Any] | None = None,
    recent_events: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    lower = text.lower()
    tokens = (
        "the first one", "the second one", "the third one", "the other one",
        "first one", "second one", "third one", "that one", "this one",
        "the former", "the latter", "former", "latter", "that", "this", "it", "there",
        "they", "them", "those", "he", "she",
    )
    token = next(
        (
            item
            for item in tokens
            if re.search(rf"\b{re.escape(item)}\b", lower)
            and (item != "there" or _there_is_deictic(lower))
        ),
        "",
    )
    if not token or not previous:
        return None
    previous_preview = truncate(str(previous.get("preview") or ""), 480)
    candidates: list[str] = []
    for event in reversed(recent_events or []):
        event_preview = truncate(str(event.get("preview") or ""), 480)
        event_candidates = _reference_candidates(event_preview, "")
        if len(event_candidates) >= 2:
            candidates = event_candidates
            break
    if not candidates:
        candidates = _reference_candidates(previous_preview, active_topic)
    selected = _select_reference_candidate(token, candidates, prior_referents or {})
    if selected:
        status = "resolved"
        confidence = "bounded"
        resolved_to = selected
    elif token in {"the other one", "that one", "this one", "that", "this", "it", "there", "he", "she"} and len(candidates) > 1:
        status = "materially_ambiguous"
        confidence = "unresolved"
        resolved_to = ""
    else:
        status = "resolved_to_previous_turn"
        confidence = "bounded"
        resolved_to = previous_preview or active_topic
    return {
        "token": token,
        "resolved_to": truncate(resolved_to, 240),
        "source": "immediately_preceding_turn",
        "confidence": confidence,
        "resolution_status": status,
        "candidates": candidates,
        "ask_if_materially_ambiguous": status == "materially_ambiguous",
    }


def _reference_candidates(previous_preview: str, active_topic: str) -> list[str]:
    text = " ".join(previous_preview.split())
    candidates: list[str] = []
    numbered = re.findall(r"(?:^|[;.]\s*|\b)(?:option|route|plan|lesson)?\s*(?:one|two|three|1|2|3)\s*[:.)-]\s*([^;.!?]+)", text, flags=re.IGNORECASE)
    candidates.extend(item.strip(" ,") for item in numbered if item.strip(" ,"))
    if len(candidates) < 2:
        pair = re.search(
            r"\b(?:between|compare|options? (?:are|include)|either)\s+(.{2,90}?)\s+(?:and|or|versus|vs\.?)\s+(.{2,90}?)(?:[.!?]|$)",
            text,
            flags=re.IGNORECASE,
        )
        if pair:
            candidates.extend([pair.group(1).strip(" ,"), pair.group(2).strip(" ,")])
    if not candidates and text:
        candidates.append(text)
    elif not candidates and active_topic:
        candidates.append(active_topic)
    return list(dict.fromkeys(truncate(item, 160) for item in candidates if item))[:6]


def _select_reference_candidate(token: str, candidates: list[str], prior_referents: dict[str, Any]) -> str:
    index_map = {
        "the first one": 0, "first one": 0, "the former": 0, "former": 0,
        "the second one": 1, "second one": 1, "the latter": 1, "latter": 1,
        "the third one": 2, "third one": 2,
    }
    if token in index_map and len(candidates) > index_map[token]:
        return candidates[index_map[token]]
    if token == "the other one" and len(candidates) == 2:
        recent_resolutions = [
            str(item.get("resolved_to") or "")
            for item in prior_referents.values()
            if isinstance(item, dict) and str(item.get("resolved_to") or "")
        ]
        if recent_resolutions:
            return next((item for item in candidates if item not in recent_resolutions[-2:]), "")
    if token in {"that one", "this one"} and len(candidates) == 1:
        return candidates[0]
    if token in {"that", "this", "it", "there", "he", "she"} and len(candidates) == 1:
        return candidates[0]
    if token in {"they", "them", "those"} and len(candidates) == 2:
        return " and ".join(candidates)
    return ""


def _correction_refinement(
    text: str,
    previous: dict[str, Any],
    *,
    contextual_follow_up: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = " ".join(text.split())
    if any(
        marker in normalized.lower()
        for marker in ("separate question", "different question", "new question", "separate topic", "different topic", "on another topic")
    ):
        return {
            "detected": False,
            "summary": "",
            "corrected_meaning": "",
            "replaced_meaning": "",
            "replaces_turn": "",
            "scope": "current_session_refinement_only",
            "durable_memory_write": False,
        }
    patterns = (
        r"\b(?:i meant|what i meant was)\s+(.+?)\s*,?\s+not\s+(.+?)"
        r"(?=,\s+(?:and\s+)?(?:can|could|would|will|what|which|how|why|tell|explain)\b|[.!?]|$)",
        r"(?:^|\b(?:actually|correction)\s*[:,]?\s+)not\s+(.+?)\s*[,;]\s*(?:i meant\s+)?(.+?)"
        r"(?=,\s+(?:and\s+)?(?:can|could|would|will|what|which|how|why|tell|explain)\b|[.!?]|$)",
    )
    corrected = ""
    replaced = ""
    quoted_definition = re.search(
        r"\bwhen i say\s+[\"“](.+?)[\"”]\s*,?\s*i mean\s+[\"“](.+?)[\"”]",
        normalized,
        flags=re.IGNORECASE,
    )
    if quoted_definition:
        replaced = quoted_definition.group(1).strip(" ,.!?")
        corrected = quoted_definition.group(2).strip(" ,.!?")
    first = re.search(patterns[0], normalized, flags=re.IGNORECASE)
    if first and not corrected:
        corrected, replaced = first.group(1), first.group(2)
    else:
        second = re.search(patterns[1], normalized, flags=re.IGNORECASE)
        if second:
            replaced, corrected = second.group(1), second.group(2)
    contextual_kind = str((contextual_follow_up or {}).get("kind") or "")
    if not corrected and contextual_kind == "meaning_correction":
        definition = re.fullmatch(r"(.{1,100}?)\s+means\s+(.{1,240}?)[.!?]?", normalized, flags=re.IGNORECASE)
        if definition:
            replaced, corrected = definition.group(1), definition.group(2)
    explicit_marker = bool(
        re.search(r"\b(?:i meant|not what i meant|correction)\b", normalized, flags=re.IGNORECASE)
        or re.search(
            r"(?:^|[.!?;]\s*|\bbut\s+)actually\s*,?\s+"
            r"(?:the|a|an|i|we|you|it|that|this|they|he|she)\b",
            normalized,
            flags=re.IGNORECASE,
        )
    )
    detected = bool(corrected or explicit_marker)
    return {
        "detected": detected,
        "summary": truncate(normalized, 360) if detected else "",
        "corrected_meaning": truncate(corrected.strip(" ,"), 240),
        "replaced_meaning": truncate(replaced.strip(" ,"), 240),
        "replaces_turn": truncate(str(previous.get("preview") or ""), 240) if detected else "",
        "scope": "current_session_refinement_only",
        "durable_memory_write": False,
    }


def _advance_correction_lifecycle(
    corrections: list[Any],
    *,
    current_correction_detected: bool,
    topic_transition: bool,
    prior_recomputation: dict[str, Any] | None,
) -> list[Any]:
    """Retire resolved or stale correction posture without deleting ancestry."""

    recomputation = prior_recomputation if isinstance(prior_recomputation, dict) else {}
    resolved = str(recomputation.get("state") or "") in {
        "completed",
        "premise_revised_no_dependent_result",
        "not_required",
        "expired_on_topic_transition",
    }
    if current_correction_detected:
        return corrections
    result: list[Any] = []
    for item in corrections:
        if not isinstance(item, dict) or str(item.get("status") or "") != "active_refinement":
            result.append(item)
            continue
        if topic_transition:
            result.append(
                {
                    **item,
                    "status": "historical_stale_after_topic_transition",
                    "eligible_current_turn": False,
                    "lifecycle_reason": "a real topic transition ended the correction posture",
                }
            )
        elif resolved:
            result.append(
                {
                    **item,
                    "status": "historical_resolved_refinement",
                    "eligible_current_turn": False,
                    "lifecycle_reason": "the correction was resolved and remains only as session ancestry",
                }
            )
        else:
            result.append(item)
    return result


def _there_is_deictic(lower: str) -> bool:
    """Keep existential/spatial idioms from becoming prior-turn references."""

    if re.search(r"\b(?:is|are|was|were|could be|might be|may be)\s+there\b", lower):
        return False
    if re.search(r"\b(?:out|somewhere|anywhere|nowhere)\s+there\b", lower):
        return False
    if re.search(r"\bthere\s+(?:is|are|was|were|could|might|may|seems?|appears?)\b", lower):
        return False
    return bool(
        re.search(
            r"\b(?:go|went|been|stay|stayed|look|looked|happen|happened|"
            r"from|over|back|right)\s+there\b|\bthere[?!.]?\s*$",
            lower,
        )
    )


def _utterance_units(
    text: str,
    *,
    contextual_follow_up: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    units: list[dict[str, Any]] = []
    contextual_kind = str((contextual_follow_up or {}).get("kind") or "")
    explicit_topic_shift = contextual_kind == "topic_shift"
    raw_units: list[str] = []
    for sentence in re.split(r"(?<=[.!?])[\"”']?\s+|\n+", text.strip()):
        sentence = sentence.strip()
        if not sentence:
            continue
        pieces = [
            part.strip(" ,")
            for part in re.split(
                r"(?i)(?:;\s*|,\s*(?:and\s+)?)(?=(?:can|could|would|will|what|which|how|why|"
                r"compare|explain|give|tell|show|list|summarize|recap|recommend|choose|"
                r"suggest|propose|ask|write|sort|arrange|use|add|include|name|say|put|describe|identify|state|separate|"
                r"distinguish|calculate|count)\b)",
                sentence,
            )
            if part.strip(" ,")
        ]
        raw_units.extend(pieces or [sentence])
    for index, raw in enumerate(raw_units):
        value = raw.strip()
        if not value:
            continue
        lower = value.lower()
        if value.endswith("?"):
            kind = "question"
        elif not explicit_topic_shift and (
            correction_signal(lower)
            or ("when i say" in lower and "i mean" in lower)
        ):
            kind = "correction"
        elif re.match(
            r"^(?:(?:then|next|finally)\s+)?(?:please\s+)?"
            r"(?:compare|explain|show|tell|help|give|list|summarize|check|walk|"
            r"recommend|suggest|propose|ask|acknowledge|write|sort|arrange|use|add|include|name|say|put|describe|identify|state|separate|"
            r"distinguish|calculate|count|revise|update|adjust|return\b.*\b(?:explain|answer|summarize))\b",
            lower,
        ):
            kind = "direct_request"
        elif re.match(
            r"^(?:if|when|given)\b.+,\s*(?:compare|explain|give|tell|show|list|"
            r"recommend|suggest|write|sort|arrange|describe|identify|state)\b",
            lower,
        ):
            kind = "direct_request"
        elif re.search(r"\b(?:could you|would you|can you|i need you to|let's|lets)\b", lower):
            kind = "indirect_request"
        elif re.search(r"\b(?:i prefer|keep it|make it|be brief|go deeper)\b", lower):
            kind = "session_preference"
        else:
            kind = "statement"
        units.append({"id": f"utterance_{index + 1}", "text": truncate(value, 480), "kind": kind, "position": index})
    return units[:12]


def _extract_entities(text: str) -> list[dict[str, str]]:
    names = re.findall(r"\b[A-Z][A-Za-z0-9_-]{2,}\b", text)
    known = [name for name in ("Selene", "Aleks", "Cocoon", "Tendril", "intelligenceOS") if name.lower() in text.lower()]
    return [{"name": name, "source": "current_turn"} for name in dict.fromkeys([*known, *names])][:20]


def _merge_entities(existing: list[Any], new: list[dict[str, str]]) -> list[dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for item in [*existing, *new]:
        if isinstance(item, dict) and str(item.get("name") or ""):
            merged[str(item["name"]).lower()] = {"name": str(item["name"]), "source": str(item.get("source") or "prior_turn")}
    return list(merged.values())[-30:]


def _advance_session_preferences(
    prior: dict[str, Any],
    *,
    original_text: str,
    interpreted_text: str,
    figurative_interpretation: dict[str, Any],
    contextual_follow_up: dict[str, Any],
) -> dict[str, Any]:
    """Advance temporary conversational instructions without making a profile.

    A response-shape request belongs to the visible session and expires after a
    small number of user turns.  Explicit releases and clear topic changes yield
    it immediately.  This state is deliberately unsuitable for durable memory.
    """

    original_lower = " ".join(original_text.lower().replace("’", "'").split())
    interpreted_lower = " ".join(interpreted_text.lower().split())
    prior_transient = (
        prior.get("transient")
        if isinstance(prior.get("transient"), dict)
        else {}
    )
    prior_directives = (
        prior_transient.get("directives")
        if isinstance(prior_transient.get("directives"), dict)
        else {
            key: prior[key]
            for key in ("response_depth", "pacing", "directness")
            if str(prior.get(key) or "")
        }
    )
    prior_remaining = max(0, int(prior_transient.get("remaining_turns") or 0))
    release_requested = any(
        marker in original_lower
        for marker in (
            "back to normal",
            "normal length",
            "regular length",
            "normal pace",
            "regular pace",
            "you can be expansive",
            "you don't need to be brief",
            "you do not need to be brief",
            "don't keep it short",
            "do not keep it short",
            "forget the short",
        )
    )
    topic_change = any(
        marker in original_lower
        for marker in (
            "new topic",
            "different topic",
            "on another topic",
            "separate topic",
            "separate question",
            "moving on to",
        )
    ) or str(contextual_follow_up.get("kind") or "") == "separate_topic"
    new_directives = _session_preference_directives(
        original_lower,
        interpreted_lower,
        figurative_interpretation,
    )

    if new_directives:
        directives = {**prior_directives, **new_directives}
        remaining = _preference_duration(original_lower)
        return _preference_packet(
            directives,
            remaining_turns=remaining,
            status="active",
            source="explicit_current_turn",
            started_this_turn=True,
        )

    if release_requested or topic_change:
        return _preference_packet(
            {},
            remaining_turns=0,
            status="released_by_user" if release_requested else "yielded_on_context_change",
            source="explicit_current_turn",
            started_this_turn=False,
        )

    if prior_directives and prior_remaining > 1:
        return _preference_packet(
            prior_directives,
            remaining_turns=prior_remaining - 1,
            status="active",
            source="carried_current_session_instruction",
            started_this_turn=False,
        )
    if prior_directives:
        return _preference_packet(
            {},
            remaining_turns=0,
            status="expired",
            source="bounded_turn_expiry",
            started_this_turn=False,
        )
    return {}


def _session_preference_directives(
    original_lower: str,
    interpreted_lower: str,
    figurative_interpretation: dict[str, Any],
) -> dict[str, str]:
    directives: dict[str, str] = {}
    if any(
        item in original_lower
        for item in ("keep it short", "short answer", "briefly", "be brief")
    ) or re.search(
        r"\bkeep\s+(?:the\s+)?(?:next\s+)?(?:one|two|three|four|five|six|\d+)?\s*"
        r"(?:replies|answers|turns|exchanges)?\s*brief\b",
        original_lower,
    ):
        directives["response_depth"] = "brief"
    if any(
        item in original_lower
        for item in ("go deeper", "long form", "walk me through", "in detail")
    ):
        directives["response_depth"] = "developed"
    conversational_slow_down = (
        str(figurative_interpretation.get("selected_reading") or "") == "figurative"
        and "conversational pace" in str(
            figurative_interpretation.get("intended_meaning") or interpreted_lower
        ).lower()
    )
    if conversational_slow_down or any(
        item in original_lower for item in ("one step at a time", "less at once")
    ):
        directives["response_depth"] = "brief"
        directives["pacing"] = "spacious"
    if any(
        item in original_lower
        for item in (
            "be direct",
            "straight answer",
            "get to the point",
            "no preamble",
        )
    ):
        directives["directness"] = "high"
    return directives


def _preference_duration(lower: str) -> int:
    numbered = re.search(r"\b(?:for|next)\s+(\d+)\s+(?:turns?|exchanges?|replies|answers?)\b", lower)
    if numbered:
        count = int(numbered.group(1))
        return max(1, min(count + (1 if numbered.group(0).startswith("next") else 0), 7))
    worded = re.search(
        r"\b(?:for|next)\s+(one|two|three|four|five|six)\s+(?:turns?|exchanges?|replies|answers?)\b",
        lower,
    )
    if worded:
        count = {
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
        }[worded.group(1)]
        return min(count + (1 if worded.group(0).startswith("next") else 0), 7)
    if any(marker in lower for marker in ("this answer", "this reply", "this one")):
        return 1
    return 3


def _preference_packet(
    directives: dict[str, str],
    *,
    remaining_turns: int,
    status: str,
    source: str,
    started_this_turn: bool,
) -> dict[str, Any]:
    active = bool(directives) and remaining_turns > 0 and status == "active"
    return {
        **(directives if active else {}),
        "scope": "current_session_only",
        "transient": {
            "active": active,
            "status": status,
            "directives": dict(directives) if active else {},
            "remaining_turns": remaining_turns if active else 0,
            "started_this_turn": started_this_turn,
            "source": source,
            "durable_preference_write": False,
            "expires_automatically": True,
        },
    }


def _indirect_request(text: str) -> dict[str, Any]:
    lower = text.lower()
    marker = next((item for item in ("could you", "would you", "can you", "i was wondering", "do you mind") if item in lower), "")
    return {"detected": bool(marker), "marker": marker, "meaning": "request" if marker else ""}


def _quotes(text: str) -> list[str]:
    return [truncate(item.strip(), 240) for item in re.findall(r'["“](.*?)["”]', text) if item.strip()][:8]


def _response_landmarks(
    candidate: str,
    *,
    active_topic: str,
    thread_braid: dict[str, Any],
    coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    if not candidate.strip():
        return []
    active_thread = str(thread_braid.get("active_thread_id") or "")
    sentences = [
        truncate(item.strip(), 480)
        for item in re.split(r"(?<=[.!?])\s+|\n+", candidate)
        if item.strip()
    ]
    landmarks: list[dict[str, Any]] = []
    for index, sentence in enumerate(sentences[:10]):
        lower = sentence.lower()
        kind = (
            "condition"
            if re.search(r"\b(?:if|unless|when|would change|reopen)\b", lower)
            else "recommendation"
            if re.search(r"\b(?:recommend|should|start with|first|next step|prefer|choose|use)\b", lower)
            else "limit"
            if re.search(r"\b(?:limit|cannot|can't|does not|doesn't|however|but)\b", lower)
            else "conclusion"
        )
        digest = sha256(f"{active_thread}|{sentence.lower()}".encode("utf-8")).hexdigest()[:12]
        landmarks.append(
            {
                "id": f"session_landmark_{digest}",
                "kind": kind,
                "summary": sentence,
                "topic": truncate(active_topic, 240),
                "thread_id": active_thread,
                "response_position": index,
                "coverage_complete_at_recording": coverage.get("all_required_addressed") is True,
                "source": "visible_selene_response",
                "scope": "current_session_only",
            }
        )
    return landmarks


def _merge_landmarks(existing: list[dict[str, Any]], new: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in [*existing, *new]:
        key = str(item.get("id") or "") or " ".join(str(item.get("summary") or "").lower().split())
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return retain_structural_records(merged, limit=64)


def _loop_id(session_id: int, question: str, index: int) -> str:
    digest = sha256(f"{session_id}:{index}:{question}".encode("utf-8")).hexdigest()[:12]
    return f"dialogue_loop_{digest}"


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value or ""))
    except json.JSONDecodeError:
        return fallback


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
