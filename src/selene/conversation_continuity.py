from __future__ import annotations

import re
from typing import Any

from .registry import truncate


CONVERSATION_CONTINUITY_BOUNDARY = (
    "current_session_landmark_thread_referent_and_mixed_intent_binding_only_no_"
    "durable_memory_identity_personality_governance_training_authority_or_action"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "durable_memory_write": False,
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

_IMMEDIATE_FOLLOW_UP_KINDS = {
    "confidence_check",
    "reason_follow_up",
    "continuation",
    "elaboration",
    "example_request",
    "rephrase_request",
    "viewpoint_follow_up",
    "constraint_refinement",
    "priority_follow_up",
    "analogy_transfer_request",
    "meaning_correction",
    "answer_development",
    "comparison_follow_up",
    "alternative_reference",
}

_RETURN_CUES = (
    "back to",
    "return to",
    "going back to",
    "earlier when",
    "the point about",
    "what you said about",
    "we discussed",
)

_TOPIC_SHIFT_CUES = (
    "separate topic",
    "different topic",
    "new topic",
    "on another topic",
    "separate question",
    "different question",
    "new question",
)

_STOP = {
    "about", "after", "again", "also", "and", "are", "back", "because",
    "been", "before", "can", "could", "did", "does", "earlier", "for",
    "from", "going", "have", "how", "into", "just", "more", "return",
    "said", "say", "separate", "that", "the", "then", "there", "these",
    "they", "this", "those", "topic", "what", "when", "where", "which",
    "with", "would", "you", "your",
}


def conversation_continuity_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "conversation_continuity_resolution_ready",
            "version": "v1_session_landmark_and_thread_binding",
            "is_organ": False,
            "owner": "Conversation Spine and Dialogue Workspace",
            "resolves": [
                "immediate follow-up",
                "named thread return",
                "bounded pronoun or implied reference",
                "explicit topic shift",
                "mixed dialogue acts",
                "session summary scope",
                "active-thread continuation",
            ],
            "material_ambiguity_may_request_clarification": True,
            "ordinary_ambiguity_forces_question": False,
            "multiple_threads_may_remain_open": True,
            "session_context_is_durable_memory": False,
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "review_status": "status_only",
            "provenance_boundary": CONVERSATION_CONTINUITY_BOUNDARY,
        }
    )


def resolve_conversation_continuity(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind the current turn to one visible session target without inventing one."""

    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400).strip()
    lower = _normalize(prompt)
    dialogue = _dict(payload.get("dialogue_workspace"))
    pragmatics = _dict(dialogue.get("pragmatics"))
    proposition_ledger = _dict(pragmatics.get("session_proposition_ledger"))
    stale_propositions = [
        item
        for item in proposition_ledger.get("propositions") or []
        if isinstance(item, dict)
        and str(item.get("status") or "") in {"invalidated", "superseded"}
    ]
    contextual = _dict(payload.get("contextual_follow_up"))
    intent = _dict(payload.get("intent_decision"))
    events = [
        item for item in payload.get("conversation_events") or [] if isinstance(item, dict)
    ][-16:]
    braid = _dict(pragmatics.get("thread_braid") or dialogue.get("thread_braid"))
    threads = [item for item in braid.get("threads") or [] if isinstance(item, dict)][-16:]
    traversal = [
        item for item in braid.get("turn_traversal") or [] if isinstance(item, dict)
    ][:20]
    all_landmarks = [
        item
        for item in (
            contextual.get("session_landmarks")
            or pragmatics.get("session_landmarks")
            or dialogue.get("session_landmarks")
            or []
        )
        if isinstance(item, dict)
    ][-64:]
    landmarks = [
        item for item in all_landmarks if _landmark_is_current(item, stale_propositions)
    ]
    checkpoints = [
        item
        for item in (
            pragmatics.get("topic_checkpoints")
            or dialogue.get("topic_checkpoints")
            or []
        )
        if isinstance(item, dict)
    ][-64:]
    resolved_reference = _dict(
        pragmatics.get("resolved_reference")
        or _dict(pragmatics.get("referents")).get("resolved_current")
    )
    resolved_reference = _bind_reference_after_revision(
        resolved_reference,
        proposition_ledger,
    )
    previous_answer = _previous_assistant(contextual, events)
    recomputation = _dict(proposition_ledger.get("recomputation"))
    revision_active = str(recomputation.get("state") or "") in {
        "required",
        "held_pending_owner_result",
        "premise_revised_no_dependent_result",
        "completed",
    }
    revised_proposition = next(
        (
            item
            for item in proposition_ledger.get("propositions") or []
            if isinstance(item, dict)
            and str(item.get("id") or "")
            == str(recomputation.get("revised_proposition_id") or "")
        ),
        {},
    )
    contextual_kind = str(contextual.get("kind") or "none")
    active_thread_id = str(braid.get("active_thread_id") or "")
    active_thread = next(
        (item for item in threads if str(item.get("id") or "") == active_thread_id),
        {},
    )
    explicit_return = _explicit_return(
        lower,
        contextual_kind=contextual_kind,
        braid=braid,
    )
    summary_requested = contextual_kind == "session_summary_request"
    topic_shift = contextual_kind == "topic_shift" or any(
        cue in lower for cue in _TOPIC_SHIFT_CUES
    )
    immediate_follow_up = contextual_kind in _IMMEDIATE_FOLLOW_UP_KINDS
    mixed_intent = intent.get("mixed_intent") is True
    dialogue_acts = _dialogue_acts(intent, pragmatics)
    material_referent_ambiguity = (
        str(resolved_reference.get("resolution_status") or "")
        == "materially_ambiguous"
    )
    unresolved_returns = [
        item for item in braid.get("unresolved_returns") or [] if isinstance(item, dict)
    ]
    material_return_ambiguity = bool(
        explicit_return
        and unresolved_returns
        and any(item.get("ask_only_if_material") is True for item in unresolved_returns)
    )
    clarification_needed = material_referent_ambiguity or material_return_ambiguity

    selected_landmarks = _select_landmarks(
        prompt,
        landmarks,
        contextual=contextual,
        active_thread_id=active_thread_id,
        explicit_return=explicit_return,
        summary_requested=summary_requested,
        resolved_reference=resolved_reference,
    )
    selected_checkpoint = _select_checkpoint(
        prompt,
        checkpoints,
        active_thread_id=active_thread_id,
        explicit_return=explicit_return,
    )
    if immediate_follow_up and not explicit_return:
        # An explicit immediate follow-up is grounded by the immediately
        # preceding answer. A loosely matching older checkpoint can otherwise
        # contaminate a well-bound local continuation with stale subject matter.
        selected_checkpoint = {}

    if clarification_needed:
        mode = "material_ambiguity_hold"
    elif summary_requested:
        mode = "session_summary"
    elif revision_active:
        mode = "dependency_revision"
    elif topic_shift:
        mode = "explicit_topic_shift"
    elif explicit_return:
        mode = "named_thread_return"
    elif immediate_follow_up:
        mode = "immediate_follow_up"
    elif resolved_reference.get("resolution_status") in {
        "resolved",
        "resolved_to_previous_turn",
        "explicit_session_alias",
        "resolved_to_revised_proposition",
    }:
        mode = "implied_reference"
    elif mixed_intent:
        mode = "mixed_intent"
    elif len(threads) > 1:
        mode = "active_thread_continuation"
    else:
        mode = "ordinary_session_continuation"

    immediate_relevant = bool(
        previous_answer
        and mode in {"immediate_follow_up", "implied_reference"}
        and not explicit_return
        and not revision_active
    )
    grounding_fragments = _grounding_fragments(
        mode,
        previous_answer="" if revision_active else previous_answer,
        selected_landmarks=selected_landmarks,
        selected_checkpoint=selected_checkpoint,
        resolved_reference=resolved_reference,
    )
    selected_target = _selected_target(
        mode,
        active_thread=active_thread,
        previous_answer="" if revision_active else previous_answer,
        selected_landmarks=selected_landmarks,
        selected_checkpoint=selected_checkpoint,
        resolved_reference=resolved_reference,
    )
    if revision_active and revised_proposition:
        selected_target = {
            "kind": "revised_session_proposition",
            "id": str(revised_proposition.get("id") or ""),
            "label": truncate(str(revised_proposition.get("text") or ""), 240),
        }
        revised_text = str(revised_proposition.get("text") or "").strip()
        if revised_text:
            grounding_fragments = [f"Revised visible premise: {revised_text}"]
    open_thread_ids = [
        str(item.get("id") or "")
        for item in threads
        if str(item.get("state") or "") in {"active", "paused", "resumed"}
        and str(item.get("id") or "")
    ]
    signals = list(
        dict.fromkeys(
            [
                *(["explicit_return"] if explicit_return else []),
                *(["immediate_follow_up"] if immediate_follow_up else []),
                *(["topic_shift"] if topic_shift else []),
                *(["session_summary"] if summary_requested else []),
                *(["mixed_intent"] if mixed_intent else []),
                *(["resolved_reference"] if resolved_reference else []),
                *(["dependency_revision"] if revision_active else []),
            ]
        )
    )
    return _with_guards(
        {
            "status": (
                "conversation_continuity_needs_material_clarification"
                if clarification_needed
                else "conversation_continuity_resolved"
            ),
            "version": "v1_session_landmark_and_thread_binding",
            "mode": mode,
            "signals": signals,
            "selected_target": selected_target,
            "selected_thread": active_thread,
            "selected_thread_id": active_thread_id,
            "selected_landmarks": selected_landmarks,
            "selected_landmark_ids": [
                str(item.get("id") or "") for item in selected_landmarks if str(item.get("id") or "")
            ],
            "selected_checkpoint": selected_checkpoint,
            "selected_checkpoint_id": str(selected_checkpoint.get("checkpoint_id") or ""),
            "resolved_reference": resolved_reference,
            "previous_answer": {
                "available": bool(previous_answer),
                "preview": previous_answer,
                "relevant_to_current_turn": immediate_relevant,
            },
            "immediate_previous_answer_relevant": immediate_relevant,
            "immediate_previous_answer_excluded_as_stale": bool(
                revision_active and previous_answer
            ),
            "grounding_fragments": grounding_fragments,
            "grounding_text": truncate(" ".join(grounding_fragments), 1800),
            "dialogue_acts": dialogue_acts,
            "mixed_intent": mixed_intent,
            "multiple_threads_preserved": len(open_thread_ids) > 1,
            "open_thread_ids": open_thread_ids,
            "thread_traversal": traversal,
            "summary_scope": "visible_current_session" if summary_requested else "not_requested",
            "clarification_needed": clarification_needed,
            "clarification_reason": (
                "materially_ambiguous_referent"
                if material_referent_ambiguity
                else "materially_ambiguous_thread_return"
                if material_return_ambiguity
                else ""
            ),
            "other_supported_parts_may_continue": clarification_needed and mixed_intent,
            "clarification_question_generated": False,
            "binding_invents_prior_context": False,
            "session_context_is_durable_memory": False,
            "selected_landmarks_require_visible_complete_response": True,
            "stale_landmark_ids_excluded": [
                str(item.get("id") or "")
                for item in all_landmarks
                if item not in landmarks and str(item.get("id") or "")
            ],
            "stale_propositions_eligible_for_grounding": False,
            "session_proposition_ledger_observed": bool(proposition_ledger),
            "dependency_revision": recomputation if revision_active else {},
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "review_status": "status_only",
            "provenance_boundary": CONVERSATION_CONTINUITY_BOUNDARY,
        }
    )


def _explicit_return(lower: str, *, contextual_kind: str, braid: dict[str, Any]) -> bool:
    if contextual_kind == "named_callback" or any(cue in lower for cue in _RETURN_CUES):
        return True
    active_id = str(braid.get("active_thread_id") or "")
    prior_id = str(braid.get("prior_active_thread_id") or "")
    return bool(
        active_id
        and prior_id
        and active_id != prior_id
        and any(
            str(item.get("relation") or "") == "returns_to"
            and str(item.get("target_thread_id") or "") == active_id
            for item in braid.get("edges") or []
            if isinstance(item, dict)
        )
    )


def _landmark_is_current(
    landmark: dict[str, Any],
    stale_propositions: list[dict[str, Any]],
) -> bool:
    proposition_id = str(landmark.get("proposition_id") or "")
    if proposition_id:
        return not any(
            str(item.get("id") or "") == proposition_id for item in stale_propositions
        )
    summary = _normalize(str(landmark.get("summary") or ""))
    if not summary:
        return True
    return not any(
        _text_overlap(summary, _normalize(str(item.get("text") or ""))) >= 0.8
        for item in stale_propositions
    )


def _bind_reference_after_revision(
    reference: dict[str, Any],
    ledger: dict[str, Any],
) -> dict[str, Any]:
    if not reference:
        return reference
    resolved = _normalize(str(reference.get("resolved_to") or ""))
    if not resolved:
        return reference
    propositions = [
        item for item in ledger.get("propositions") or [] if isinstance(item, dict)
    ]
    stale = next(
        (
            item
            for item in reversed(propositions)
            if str(item.get("status") or "") in {"invalidated", "superseded"}
            and _text_overlap(resolved, _normalize(str(item.get("text") or ""))) >= 0.65
        ),
        {},
    )
    if not stale:
        return reference
    replacement_id = str(stale.get("replaced_by_proposition_id") or "")
    replacement = next(
        (
            item
            for item in propositions
            if str(item.get("id") or "") == replacement_id
            and str(item.get("status") or "") in {"active", "recomputed"}
        ),
        {},
    )
    if replacement:
        return {
            **reference,
            "resolved_to": str(replacement.get("text") or ""),
            "resolution_status": "resolved_to_revised_proposition",
            "revision_binding": {
                "prior_proposition_id": str(stale.get("id") or ""),
                "current_proposition_id": str(replacement.get("id") or ""),
            },
        }
    return {
        **reference,
        "resolved_to": "",
        "resolution_status": "materially_ambiguous",
        "revision_binding": {
            "prior_proposition_id": str(stale.get("id") or ""),
            "current_proposition_id": "",
            "reason": "the referenced proposition was revised and has no active replacement result",
        },
    }


def _text_overlap(left: str, right: str) -> float:
    left_terms = set(left.split())
    right_terms = set(right.split())
    if not left_terms or not right_terms:
        return 0.0
    return len(left_terms & right_terms) / max(1, min(len(left_terms), len(right_terms)))


def _select_landmarks(
    prompt: str,
    landmarks: list[dict[str, Any]],
    *,
    contextual: dict[str, Any],
    active_thread_id: str,
    explicit_return: bool,
    summary_requested: bool,
    resolved_reference: dict[str, Any],
) -> list[dict[str, Any]]:
    eligible = [
        item for item in landmarks if item.get("coverage_complete_at_recording") is not False
    ]
    if summary_requested:
        return eligible[-8:]
    matched = [
        item
        for item in contextual.get("matched_session_landmarks") or []
        if isinstance(item, dict)
        and item.get("coverage_complete_at_recording") is not False
        and any(
            str(candidate.get("id") or "") == str(item.get("id") or "")
            for candidate in eligible
        )
    ]
    if not (explicit_return or summary_requested):
        matched = []
    if matched and explicit_return and active_thread_id:
        matched_thread = [
            item
            for item in matched
            if str(item.get("thread_id") or "") == active_thread_id
        ]
        if matched_thread:
            matched = matched_thread
    if matched:
        return _dedupe_records(matched)[:6]
    pool = eligible
    if explicit_return and active_thread_id:
        same_thread = [
            item for item in eligible if str(item.get("thread_id") or "") == active_thread_id
        ]
        if same_thread:
            pool = same_thread
    query = set(
        _terms(
            " ".join(
                [prompt, str(resolved_reference.get("resolved_to") or "")]
            )
        )
    )
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(pool):
        text = " ".join((str(item.get("topic") or ""), str(item.get("summary") or "")))
        score = len(query & set(_terms(text)))
        if score or (
            explicit_return
            and bool(active_thread_id)
            and str(item.get("thread_id") or "") == active_thread_id
        ):
            ranked.append((score, index, item))
    ranked.sort(key=lambda value: (value[0], value[1]), reverse=True)
    return [item for _, _, item in ranked[:6]]


def _select_checkpoint(
    prompt: str,
    checkpoints: list[dict[str, Any]],
    *,
    active_thread_id: str,
    explicit_return: bool,
) -> dict[str, Any]:
    query = set(_terms(prompt))
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(checkpoints):
        thread_match = bool(
            active_thread_id
            and str(item.get("thread_id") or "") == active_thread_id
        )
        overlap = len(query & set(_terms(str(item.get("topic") or ""))))
        if overlap or (explicit_return and thread_match):
            ranked.append((overlap + (3 if thread_match else 0), index, item))
    ranked.sort(key=lambda value: (value[0], value[1]), reverse=True)
    return ranked[0][2] if ranked else {}


def _grounding_fragments(
    mode: str,
    *,
    previous_answer: str,
    selected_landmarks: list[dict[str, Any]],
    selected_checkpoint: dict[str, Any],
    resolved_reference: dict[str, Any],
) -> list[str]:
    if mode == "material_ambiguity_hold":
        return []
    values: list[str] = []
    if mode in {"immediate_follow_up", "implied_reference"} and previous_answer:
        values.append(f"Immediate prior answer: {previous_answer}")
    if mode in {"named_thread_return", "session_summary", "active_thread_continuation"}:
        values.extend(
            f"Visible session landmark: {str(item.get('summary') or '')}"
            for item in selected_landmarks[:6]
            if str(item.get("summary") or "").strip()
        )
    if selected_checkpoint:
        conclusion = str(
            _dict(selected_checkpoint.get("reasoning_state_capsule")).get("current_conclusion")
            or (selected_checkpoint.get("established_visible_statements") or [""])[0]
        ).strip()
        if conclusion:
            values.append(f"Visible session checkpoint: {conclusion}")
    if mode == "implied_reference" and str(resolved_reference.get("resolved_to") or "").strip():
        values.append(f"Resolved visible referent: {resolved_reference['resolved_to']}")
    return list(dict.fromkeys(truncate(item, 720) for item in values if item))[:8]


def _selected_target(
    mode: str,
    *,
    active_thread: dict[str, Any],
    previous_answer: str,
    selected_landmarks: list[dict[str, Any]],
    selected_checkpoint: dict[str, Any],
    resolved_reference: dict[str, Any],
) -> dict[str, Any]:
    if mode == "material_ambiguity_hold":
        return {"kind": "unresolved", "id": "", "label": ""}
    if mode == "immediate_follow_up":
        return {"kind": "immediate_answer", "id": "", "label": truncate(previous_answer, 240)}
    if mode == "implied_reference":
        return {
            "kind": "session_referent",
            "id": str(resolved_reference.get("token") or ""),
            "label": truncate(str(resolved_reference.get("resolved_to") or ""), 240),
        }
    if selected_checkpoint:
        return {
            "kind": "session_checkpoint",
            "id": str(selected_checkpoint.get("checkpoint_id") or ""),
            "label": truncate(str(selected_checkpoint.get("topic") or ""), 240),
        }
    if selected_landmarks:
        return {
            "kind": "session_landmark",
            "id": str(selected_landmarks[0].get("id") or ""),
            "label": truncate(str(selected_landmarks[0].get("topic") or ""), 240),
        }
    if active_thread:
        return {
            "kind": "session_thread",
            "id": str(active_thread.get("id") or ""),
            "label": truncate(str(active_thread.get("topic") or ""), 240),
        }
    return {"kind": "current_turn", "id": "", "label": ""}


def _previous_assistant(contextual: dict[str, Any], events: list[dict[str, Any]]) -> str:
    supplied = truncate(str(contextual.get("previous_assistant_preview") or ""), 900).strip()
    if supplied:
        return supplied
    return next(
        (
            truncate(str(item.get("preview") or item.get("content") or ""), 900).strip()
            for item in reversed(events)
            if str(item.get("role") or "") == "selene"
            and str(item.get("preview") or item.get("content") or "").strip()
        ),
        "",
    )


def _dialogue_acts(intent: dict[str, Any], pragmatics: dict[str, Any]) -> list[str]:
    values = [str(item) for item in intent.get("dialogue_acts") or [] if str(item)]
    values.extend(
        str(item.get("kind") or "")
        for item in pragmatics.get("utterance_units") or []
        if isinstance(item, dict) and str(item.get("kind") or "")
    )
    return list(dict.fromkeys(values))[:16]


def _dedupe_records(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in values:
        key = str(item.get("id") or "") or _normalize(str(item.get("summary") or ""))
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _terms(value: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", value.lower())
    return list(dict.fromkeys(word for word in words if word not in _STOP))[:30]


def _normalize(value: str) -> str:
    return " ".join(value.lower().replace("’", "'").split())


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
