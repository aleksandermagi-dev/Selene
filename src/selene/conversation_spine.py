from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .pragmatic_planner import build_pragmatic_plan
from .registry import truncate


CONVERSATION_SPINE_BOUNDARY = (
    "current_session_conversation_grounding_only_no_durable_memory_identity_personality_"
    "governance_training_authority_or_autonomous_action"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "durable_memory_write": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
}

_TERM_STOP_WORDS = {
    "about", "after", "again", "also", "and", "answer", "are", "because", "before", "being", "between",
    "could", "does", "from", "have", "into", "just", "make", "more", "one", "question", "result",
    "how", "mean", "means", "should", "some", "that", "the", "their", "them", "then", "there", "these", "thing", "this",
    "those", "through", "too", "what", "whats", "when", "where", "which", "while", "with", "would", "you", "your",
}

_SOURCE_CLASSES = {
    "boundary_response",
    "conversation",
    "approved_knowledge",
    "domain_answer",
    "language_capability",
    "memory_reconstruction",
    "reasoning_answer",
    "self_state",
}


def conversation_spine_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "conversation_spine_ready",
            "version": "v2_braided_turn_grounding",
            "organ_name": "Conversation Spine",
            "scope": "current_chat_session_only",
            "carries": [
                "current intent and dialogue acts",
                "active topic and distinctive anchors",
                "bounded referents",
                "previous visible answer claims and recommendations",
                "bounded visible session landmarks",
                "open response obligations",
                "session topic branches returns dependencies and landings",
                "compatible visible source classes",
                "separate route evidence answer memory and expression confidence",
            ],
            "coordinates": [
                "meaning routing",
                "comprehension candidate selection",
                "Answer Engine",
                "intelligenceOS",
                "response coverage and bounded repair",
                "Native Language Organ and Voice",
            ],
            "persistent_state_owner": "Dialogue Workspace",
            "durable_memory_store": False,
            "hidden_reasoning_store": False,
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": CONVERSATION_SPINE_BOUNDARY,
        }
    )


def build_conversation_spine(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build one visible, session-scoped grounding packet for the current turn.

    The spine coordinates already available conversational summaries. It does not
    expose hidden reasoning and is not a new memory, identity, or authority store.
    """
    payload = payload or {}
    session_id = int(payload.get("session_id") or 0)
    if session_id <= 0:
        raise ValueError("session_id is required")
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400).strip()
    if not prompt:
        raise ValueError("conversation prompt is required")

    interpreted = truncate(str(payload.get("interpreted_text") or prompt), 2400).strip()
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    dialogue = payload.get("dialogue_workspace") if isinstance(payload.get("dialogue_workspace"), dict) else {}
    contextual = payload.get("contextual_follow_up") if isinstance(payload.get("contextual_follow_up"), dict) else {}
    supplied_plan = payload.get("pragmatic_plan") if isinstance(payload.get("pragmatic_plan"), dict) else {}
    pragmatic_plan = supplied_plan or build_pragmatic_plan(
        {
            "prompt": interpreted,
            "intent_decision": intent,
            "dialogue_workspace": dialogue,
            "content_seed": "",
        }
    )
    pragmatics = dialogue.get("pragmatics") if isinstance(dialogue.get("pragmatics"), dict) else {}
    thread_braid = pragmatics.get("thread_braid") if isinstance(pragmatics.get("thread_braid"), dict) else {}
    previous = _previous_answer(contextual, pragmatics, payload.get("conversation_events"))
    session_landmarks = [
        item for item in pragmatics.get("session_landmarks") or [] if isinstance(item, dict)
    ][-24:]
    relevant_landmarks = _relevant_landmarks(interpreted, session_landmarks)
    resolved_reference = (
        pragmatic_plan.get("resolved_reference")
        if isinstance(pragmatic_plan.get("resolved_reference"), dict)
        else pragmatics.get("resolved_reference")
        if isinstance(pragmatics.get("resolved_reference"), dict)
        else {}
    )
    intent_class = _intent_class(intent, contextual)
    obligations = [
        _normalize_obligation(item)
        for item in pragmatic_plan.get("response_obligations") or []
        if isinstance(item, dict)
    ]
    active_topic = truncate(str(dialogue.get("active_topic") or ""), 500)
    topic_anchors = _unique_text(
        [
            active_topic,
            str(resolved_reference.get("resolved_to") or ""),
            *[str(item.get("topic") or "") for item in obligations],
            *previous["recommendations"],
        ],
        limit=16,
        width=300,
    )
    distinctive_terms = _distinctive_terms(
        " ".join(
            [
                interpreted,
                *topic_anchors,
                str(resolved_reference.get("resolved_to") or ""),
                *previous["recommendations"],
            ]
        )
    )
    compatible_source_classes = _compatible_source_classes(intent_class, contextual)
    ambiguity = pragmatic_plan.get("ambiguity") if isinstance(pragmatic_plan.get("ambiguity"), dict) else {}
    referent_status = str(resolved_reference.get("resolution_status") or "not_needed")
    grounded_prompt = interpreted
    if contextual.get("detected") is True and previous["preview"]:
        grounded_prompt = truncate(
            f"{interpreted} Immediate prior answer: {previous['preview']}",
            3200,
        )
    if relevant_landmarks and (
        contextual.get("detected") is True
        or any(item in interpreted.lower() for item in ("earlier", "back to", "return to", "we discussed", "you said"))
    ):
        landmark_text = " ".join(str(item.get("summary") or "") for item in relevant_landmarks[:4])
        grounded_prompt = truncate(
            f"{grounded_prompt} Relevant visible points from this session: {landmark_text}",
            3600,
        )
    turn_id = "conversation-turn-" + sha256(
        f"{session_id}|{interpreted}|{previous['preview']}".encode("utf-8")
    ).hexdigest()[:16]

    return _with_guards(
        {
            "status": "conversation_spine_ready",
            "version": "v2_braided_turn_grounding",
            "organ_name": "Conversation Spine",
            "session_id": session_id,
            "turn_id": turn_id,
            "literal_prompt": prompt,
            "interpreted_prompt": interpreted,
            "grounded_prompt": grounded_prompt,
            "intent_class": intent_class,
            "intent": str(intent.get("intent") or "direct_conversation"),
            "answer_shape": str(intent.get("answer_shape") or "direct_answer"),
            "dialogue_acts": _dialogue_acts(intent, pragmatics),
            "active_topic": active_topic,
            "topic_anchors": topic_anchors,
            "distinctive_terms": distinctive_terms,
            "side_topics": _text_list(dialogue.get("side_topics"), limit=12),
            "thread_braid": thread_braid,
            "thread_traversal": [
                item for item in thread_braid.get("turn_traversal") or [] if isinstance(item, dict)
            ][:20],
            "entities": [item for item in dialogue.get("entities") or [] if isinstance(item, dict)][:20],
            "referents": {
                "resolved_current": resolved_reference or None,
                "known_session_referents": dialogue.get("referents") if isinstance(dialogue.get("referents"), dict) else {},
                "status": referent_status,
            },
            "previous_answer": previous,
            "session_landmarks": session_landmarks,
            "relevant_session_landmarks": relevant_landmarks,
            "open_obligations": obligations,
            "obligation_sequence": [str(item.get("id") or "") for item in obligations],
            "pragmatic_plan": pragmatic_plan,
            "contextual_follow_up": contextual,
            "ambiguity": ambiguity,
            "source_compatibility": {
                "compatible_source_classes": compatible_source_classes,
                "topic_alignment_required_for_content_sources": intent_class in {
                    "reasoning", "direct_content", "contextual_content"
                },
                "immediate_callback_prefers_previous_answer": contextual.get("detected") is True,
                "memory_requires_recall_intent": True,
                "self_state_requires_self_state_intent": True,
            },
            "confidence_vector": {
                "route_confidence": str(intent.get("confidence") or "not_assessed"),
                "referent_confidence": str(resolved_reference.get("confidence") or "not_needed"),
                "evidence_confidence": "not_assessed",
                "answer_confidence": "not_assessed",
                "memory_confidence": "separate_not_assessed_by_spine",
                "expression_confidence": "not_assessed",
            },
            "session_scoped_only": True,
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": CONVERSATION_SPINE_BOUNDARY,
        }
    )


def evaluate_candidate_compatibility(
    spine: dict[str, Any] | None,
    candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    """Check whether a visible candidate belongs to the current grounded turn."""
    spine = spine if isinstance(spine, dict) else {}
    candidate = candidate if isinstance(candidate, dict) else {}
    if not spine:
        return {
            "compatible": True,
            "reason": "no_conversation_spine_supplied",
            "alignment_required": False,
            "matched_terms": [],
        }
    source_id = str(candidate.get("source_id") or "unknown")
    source_class = str(candidate.get("source_class") or "")
    text = truncate(str(candidate.get("text") or ""), 5000).strip()
    intent_class = str(spine.get("intent_class") or "direct_content")
    contextual = spine.get("contextual_follow_up") if isinstance(spine.get("contextual_follow_up"), dict) else {}
    compatible_classes = set(
        str(item)
        for item in (spine.get("source_compatibility") or {}).get("compatible_source_classes") or []
    )
    distinctive = set(str(item).lower() for item in spine.get("distinctive_terms") or [] if str(item))
    matched = sorted(distinctive & set(_distinctive_terms(text)))
    contextual_approved_memory = source_id == "contextual_approved_memory"

    if not text:
        return _compatibility(False, "empty_candidate", False, matched)
    if source_class not in _SOURCE_CLASSES or (source_class not in compatible_classes and not contextual_approved_memory):
        return _compatibility(False, "source_class_incompatible_with_current_intent", False, matched)
    if contextual_approved_memory and (
        source_class != "memory_reconstruction" or intent_class not in {"reasoning", "direct_content"}
    ):
        return _compatibility(False, "contextual_memory_not_suitable_for_current_intent", False, matched)
    if source_id == "reviewed_memory" and intent_class != "memory_recall":
        return _compatibility(False, "memory_candidate_without_recall_intent", False, matched)
    if source_id == "local_chat_continuity" and intent_class != "memory_recall":
        return _compatibility(False, "continuity_candidate_without_recall_intent", False, matched)
    if source_id == "grounded_self_state" and intent_class != "self_state":
        return _compatibility(False, "self_state_candidate_without_self_state_intent", False, matched)
    if source_id == "contextual_follow_up" and contextual.get("detected") is not True:
        return _compatibility(False, "contextual_candidate_without_callback", False, matched)
    if contextual.get("detected") is True and source_class in {"approved_knowledge", "memory_reconstruction"}:
        return _compatibility(False, "callback_must_remain_grounded_in_immediate_conversation", False, matched)

    alignment_required = (
        intent_class in {"reasoning", "direct_content", "contextual_content"}
        and source_class in {"approved_knowledge", "domain_answer", "language_capability", "memory_reconstruction", "reasoning_answer"}
        and bool(distinctive)
    )
    if alignment_required and not matched:
        return _compatibility(False, "candidate_lacks_distinctive_topic_alignment", True, matched)
    return _compatibility(True, "candidate_matches_turn_intent_topic_and_source_class", alignment_required, matched)


def spine_response_alignment(spine: dict[str, Any] | None, candidate_text: str) -> dict[str, Any]:
    """Visible alignment check used alongside obligation coverage."""
    spine = spine if isinstance(spine, dict) else {}
    candidate = truncate(str(candidate_text or ""), 5000).strip()
    distinctive = set(str(item).lower() for item in spine.get("distinctive_terms") or [] if str(item))
    matched = sorted(distinctive & set(_distinctive_terms(candidate)))
    intent_class = str(spine.get("intent_class") or "")
    required = intent_class in {"reasoning", "direct_content", "contextual_content"} and bool(distinctive)
    aligned = bool(candidate) and (not required or bool(matched))
    return {
        "status": "spine_response_aligned" if aligned else "spine_response_not_aligned",
        "aligned": aligned,
        "required": required,
        "matched_terms": matched,
        "distinctive_terms": sorted(distinctive),
        "method": "visible_distinctive_term_alignment_not_semantic_certainty",
        "session_scoped_only": True,
    }


def finalize_conversation_spine(
    spine: dict[str, Any] | None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach the released answer summary without creating a second state store."""
    spine = spine if isinstance(spine, dict) else {}
    payload = payload or {}
    if not spine:
        return {}
    coverage = payload.get("response_coverage") if isinstance(payload.get("response_coverage"), dict) else {}
    supplied_confidence = payload.get("confidence_vector") if isinstance(payload.get("confidence_vector"), dict) else {}
    confidence = dict(spine.get("confidence_vector") or {})
    for key in (
        "route_confidence",
        "evidence_confidence",
        "answer_confidence",
        "memory_confidence",
        "expression_confidence",
    ):
        if supplied_confidence.get(key) not in (None, ""):
            confidence[key] = str(supplied_confidence[key])
    return _with_guards(
        {
            **spine,
            "status": "conversation_spine_turn_completed",
            "confidence_vector": confidence,
            "released_response": {
                "preview": truncate(str(payload.get("candidate_text") or ""), 900),
                "source_id": str(payload.get("source_id") or "none"),
                "source_class": str(payload.get("source_class") or "conversation"),
                "coverage_complete": coverage.get("all_required_addressed") is True,
                "unresolved_count": int(coverage.get("unresolved_count") or 0),
                "answered_loop_ids": _text_list(coverage.get("answered_loop_ids"), limit=30),
            },
            "updated_after_turn": True,
            "session_scoped_only": True,
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "provenance_boundary": CONVERSATION_SPINE_BOUNDARY,
        }
    )


def _previous_answer(contextual: dict[str, Any], pragmatics: dict[str, Any], supplied_events: Any) -> dict[str, Any]:
    preview = truncate(str(contextual.get("previous_assistant_preview") or ""), 900).strip()
    if not preview:
        previous = pragmatics.get("previous_turn") if isinstance(pragmatics.get("previous_turn"), dict) else {}
        if str(previous.get("role") or "") == "selene":
            preview = truncate(str(previous.get("preview") or ""), 900).strip()
    if not preview and isinstance(supplied_events, list):
        preview = next(
            (
                truncate(str(item.get("preview") or item.get("content") or ""), 900).strip()
                for item in reversed(supplied_events)
                if isinstance(item, dict) and str(item.get("role") or "") == "selene"
            ),
            "",
        )
    sentences = _sentences(preview)
    recommendations = [
        sentence
        for sentence in sentences
        if re.search(r"\b(?:recommend|recommendation|prefer|should|next step|start with|choose|try)\b", sentence, re.IGNORECASE)
    ][:6]
    return {
        "available": bool(preview),
        "preview": preview,
        "claims": sentences[:8],
        "recommendations": recommendations,
        "source": "immediate_session_turn" if preview else "none",
    }


def _relevant_landmarks(prompt: str, landmarks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query = set(_distinctive_terms(prompt))
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, item in enumerate(landmarks):
        text = " ".join(
            [
                str(item.get("topic") or ""),
                str(item.get("summary") or ""),
            ]
        )
        overlap = query & set(_distinctive_terms(text))
        score = len(overlap)
        if score or not query:
            ranked.append((score, index, item))
    ranked.sort(key=lambda value: (value[0], value[1]), reverse=True)
    return [item for _, _, item in ranked[:6]]


def _intent_class(intent: dict[str, Any], contextual: dict[str, Any]) -> str:
    name = str(intent.get("intent") or "direct_conversation")
    if name in {"hard_boundary", "hold_boundary"}:
        return "hard_boundary"
    if intent.get("self_state_requested") is True or name == "self_state":
        return "self_state"
    if intent.get("memory_recall_requested") is True or name == "memory_recall":
        return "memory_recall"
    if contextual.get("detected") is True and str(contextual.get("kind") or "") != "topic_shift":
        return "contextual_content"
    if intent.get("reasoning_requested") is True or name == "reasoning":
        return "reasoning"
    if intent.get("social_turn") is True or name in {
        "greeting", "farewell", "gratitude", "affirmation", "warm_connection", "reassurance_received"
    }:
        return "social"
    return "direct_content"


def _compatible_source_classes(intent_class: str, contextual: dict[str, Any]) -> list[str]:
    if intent_class == "hard_boundary":
        return ["boundary_response"]
    if intent_class == "self_state":
        return ["self_state", "conversation"]
    if intent_class == "memory_recall":
        return ["memory_reconstruction", "conversation"]
    if intent_class == "social":
        return ["conversation", "language_capability"]
    if contextual.get("detected") is True:
        return ["conversation", "domain_answer", "reasoning_answer", "language_capability"]
    return ["conversation", "domain_answer", "approved_knowledge", "language_capability", "reasoning_answer"]


def _dialogue_acts(intent: dict[str, Any], pragmatics: dict[str, Any]) -> list[str]:
    acts = [str(item) for item in intent.get("dialogue_acts") or [] if str(item)]
    primary = str(pragmatics.get("dialogue_act") or intent.get("dialogue_act") or intent.get("intent") or "")
    if primary:
        acts.insert(0, primary)
    acts.extend(
        str(item.get("kind") or "")
        for item in pragmatics.get("utterance_units") or []
        if isinstance(item, dict) and str(item.get("kind") or "")
    )
    return list(dict.fromkeys(acts))[:16]


def _normalize_obligation(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item.get("id") or ""),
        "loop_id": str(item.get("loop_id") or ""),
        "kind": str(item.get("kind") or "direct_question"),
        "source_text": truncate(str(item.get("source_text") or ""), 600),
        "topic": truncate(str(item.get("topic") or ""), 300),
        "coverage_terms": _text_list(item.get("coverage_terms"), limit=24),
        "required": item.get("required") is not False,
        "goal": str(item.get("goal") or "answer_request"),
        "inference_level": str(item.get("inference_level") or "literal"),
        "thread_id": str(item.get("thread_id") or ""),
        "thread_action": str(item.get("thread_action") or ""),
        "thread_traversal_index": int(item.get("thread_traversal_index") or 0),
        "dependency_thread_id": str(item.get("dependency_thread_id") or ""),
    }


def _distinctive_terms(value: str) -> list[str]:
    words = [word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", value)]
    return list(dict.fromkeys(word for word in words if word not in _TERM_STOP_WORDS))[:40]


def _sentences(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", value.strip()) if item.strip()]


def _unique_text(values: list[str], *, limit: int, width: int) -> list[str]:
    return list(dict.fromkeys(truncate(str(item).strip(), width) for item in values if str(item).strip()))[:limit]


def _text_list(value: Any, *, limit: int = 30) -> list[str]:
    if isinstance(value, list):
        items = value
    elif value in (None, ""):
        items = []
    else:
        items = [value]
    return list(dict.fromkeys(str(item).strip() for item in items if str(item).strip()))[:limit]


def _compatibility(compatible: bool, reason: str, alignment_required: bool, matched: list[str]) -> dict[str, Any]:
    return {
        "compatible": compatible,
        "reason": reason,
        "alignment_required": alignment_required,
        "matched_terms": matched,
    }


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
