from __future__ import annotations

import re
from typing import Any


SEMANTIC_RELEVANCE_BOUNDARY = (
    "current_turn_semantic_source_gate_only_no_memory_identity_governance_"
    "personality_training_authority_or_autonomous_action"
)

GUARDS: dict[str, Any] = {
    "memory_write_active": False,
    "durable_memory_write": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
}

_GENERIC_TERMS = {
    "able", "about", "answer", "another", "anything", "available", "back",
    "better", "can", "change", "check", "clear", "current", "different", "do",
    "does", "doing", "easy", "easier", "exact", "example", "explain", "feel",
    "first", "give", "good", "handle", "hard", "harder", "help", "idea",
    "information", "know", "known", "language", "lesson", "make", "material",
    "more", "most", "need", "new", "next", "one", "ordinary", "part",
    "possible", "practical", "question", "reason", "relevant", "review", "same",
    "say", "short", "simple", "step", "thing", "think", "use", "version", "way",
}

_STOP_TERMS = _GENERIC_TERMS | {
    "a", "an", "and", "are", "as", "at", "be", "because", "been", "before",
    "but", "by", "could", "did", "for", "from", "had", "has", "have", "he",
    "her", "here", "him", "his", "how", "i", "if", "in", "into", "is", "it",
    "its", "me", "my", "of", "on", "or", "our", "she", "should", "so", "some",
    "that", "the", "their", "them", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "us", "was", "we", "were", "what", "when",
    "where", "which", "who", "why", "will", "with", "would", "you", "your",
}

_WEAK_SUBJECT_TERMS = {
    "amount", "inside", "outside", "pattern", "process", "result", "system", "value",
}


def semantic_relevance_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "semantic_relevance_gate_ready",
            "version": "v1_role_topic_source_thread_gate",
            "scope": "current_turn_candidate_selection_only",
            "checks": [
                "source class permission",
                "topic and subject alignment",
                "requested answer role",
                "conversation-thread compatibility",
                "memory recall strength",
                "self-state ownership",
            ],
            "single_keyword_is_authority": False,
            "open_ended_reasoning_preserved": True,
            "bounded_prediction_and_hypothesis_preserved": True,
            "visible_summary_only": True,
            "provenance_boundary": SEMANTIC_RELEVANCE_BOUNDARY,
        }
    )


def evaluate_semantic_relevance(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate whether a source candidate belongs in the current answer.

    This is a release gate, not a truth oracle. It keeps a retrieved resource
    from becoming answer content merely because one generic word overlaps.
    """

    payload = payload or {}
    prompt = str(payload.get("prompt") or payload.get("query") or "").strip()
    candidate = payload.get("candidate") if isinstance(payload.get("candidate"), dict) else {}
    intent = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else {}
    spine = payload.get("conversation_spine") if isinstance(payload.get("conversation_spine"), dict) else {}
    source_class = str(
        payload.get("source_class")
        or candidate.get("source_class")
        or candidate.get("record_class")
        or "unknown"
    )
    source_id = str(payload.get("source_id") or candidate.get("source_id") or "unknown")

    subject_text = " ".join(
        str(value or "")
        for value in (
            candidate.get("title"),
            candidate.get("domain"),
            str(candidate.get("concept_key") or "").replace("_", " "),
            payload.get("subject_text"),
        )
    )
    core_text = " ".join(
        [
            str(candidate.get("central_claim") or candidate.get("summary") or candidate.get("text") or ""),
            *_text_list(candidate.get("principles")),
            *_text_list(candidate.get("relationships")),
            str(payload.get("core_text") or ""),
        ]
    )
    application_text = " ".join(
        [
            *_text_list(candidate.get("examples")),
            *_text_list(candidate.get("counterexamples")),
            *_text_list(candidate.get("limits")),
            str(payload.get("application_text") or ""),
        ]
    )

    query_terms = _semantic_terms(prompt)
    subject_terms = _semantic_terms(subject_text)
    core_terms = _semantic_terms(core_text)
    application_terms = _semantic_terms(application_text)
    all_candidate_terms = subject_terms | core_terms | application_terms
    subject_overlap = query_terms & subject_terms
    core_overlap = query_terms & core_terms
    application_overlap = query_terms & application_terms
    all_overlap = query_terms & all_candidate_terms
    strong_subject_overlap = subject_overlap - _WEAK_SUBJECT_TERMS

    requested_roles = _requested_roles(prompt, spine)
    candidate_roles = _candidate_roles(core_text, application_text, candidate)
    role_overlap = requested_roles & candidate_roles
    explicit_focus = _explicit_subject_focus(prompt, strong_subject_overlap)
    phrase_overlap = _phrase_overlap(prompt, " ".join((subject_text, core_text, application_text)))
    contextual = spine.get("contextual_follow_up") if isinstance(spine.get("contextual_follow_up"), dict) else {}
    explicit_recall = bool(
        payload.get("explicit_recall") is True
        or intent.get("memory_recall_requested") is True
        or str(intent.get("intent") or "") == "memory_recall"
    )
    self_state_requested = bool(
        intent.get("self_state_requested") is True
        or str(intent.get("intent") or "") == "self_state"
    )

    accepted = False
    reason = "candidate_lacks_semantic_alignment"
    if source_class in {"self_state", "grounded_self_state"}:
        accepted = self_state_requested
        reason = "self_state_owned_by_self_state_intent" if accepted else "self_state_without_self_state_intent"
    elif source_class in {"memory_reconstruction", "approved_memory", "approved_memory_reference"}:
        if contextual.get("detected") is True and not explicit_recall:
            accepted = False
            reason = "immediate_callback_does_not_silently_import_memory"
        elif explicit_recall:
            accepted = bool(strong_subject_overlap or len(all_overlap) >= 2 or phrase_overlap)
            reason = "explicit_recall_subject_aligned" if accepted else "memory_subject_not_found"
        else:
            accepted = bool(
                (strong_subject_overlap and len(all_overlap) >= 2)
                or len(all_overlap) >= 3
                or phrase_overlap and len(all_overlap) >= 2
            )
            reason = "contextual_memory_strongly_aligned" if accepted else "contextual_memory_alignment_too_weak"
    elif source_class in {"approved_knowledge", "reviewed_teaching_knowledge_resource"}:
        direct_subject = bool(
            strong_subject_overlap
            and (
                explicit_focus
                or len(strong_subject_overlap) >= 2
                or len(all_overlap) >= 2
                or len(query_terms) <= 2
            )
        )
        transfer_application = bool(
            len(application_overlap) >= 3
            and len(all_overlap) >= 3
            and (not requested_roles or bool(role_overlap) or "application" in candidate_roles)
        )
        accepted = direct_subject or transfer_application
        reason = (
            "approved_knowledge_subject_aligned"
            if direct_subject
            else "approved_knowledge_application_aligned"
            if transfer_application
            else "approved_knowledge_has_only_peripheral_overlap"
        )
    else:
        accepted = bool(all_overlap or not query_terms)
        reason = "candidate_topic_aligned" if accepted else "candidate_lacks_semantic_alignment"

    return _with_guards(
        {
            "status": "semantic_candidate_accepted" if accepted else "semantic_candidate_held",
            "accepted": accepted,
            "reason": reason,
            "source_id": source_id,
            "source_class": source_class,
            "query_terms": sorted(query_terms),
            "subject_overlap": sorted(subject_overlap),
            "strong_subject_overlap": sorted(strong_subject_overlap),
            "core_overlap": sorted(core_overlap),
            "application_overlap": sorted(application_overlap),
            "requested_roles": sorted(requested_roles),
            "candidate_roles": sorted(candidate_roles),
            "matched_roles": sorted(role_overlap),
            "explicit_subject_focus": explicit_focus,
            "phrase_overlap": phrase_overlap,
            "explicit_memory_recall": explicit_recall,
            "self_state_requested": self_state_requested,
            "single_keyword_is_authority": False,
            "writes_state": False,
            "visible_summary_only": True,
            "provenance_boundary": SEMANTIC_RELEVANCE_BOUNDARY,
        }
    )


def _requested_roles(prompt: str, spine: dict[str, Any]) -> set[str]:
    lower = " ".join(prompt.lower().split())
    roles: set[str] = set()
    if re.search(r"\b(?:why|cause|causes|because|mechanism|reason)\b", lower):
        roles.add("reason")
    if re.search(r"\b(?:how|steps?|procedure|method|instructions?|what (?:do|would) .* need)\b", lower):
        roles.add("method")
    if re.search(r"\b(?:compare|contrast|difference|different|similar|both|versus|vs|easier|harder)\b", lower):
        roles.add("comparison")
    if re.search(r"\b(?:predict|prediction|forecast|likely|expect|tomorrow|future)\b", lower):
        roles.add("prediction")
    if re.search(r"\b(?:hypothesis|hypothesize|best guess|could explain|might explain)\b", lower):
        roles.add("hypothesis")
    if re.search(r"\b(?:define|definition|what (?:is|are|does)\b|means?)\b", lower):
        roles.add("definition")
    if re.search(r"\b(?:apply|application|example|use .* (?:case|situation))\b", lower):
        roles.add("application")
    for obligation in spine.get("open_obligations") or []:
        if not isinstance(obligation, dict):
            continue
        kind = str(obligation.get("kind") or "").lower()
        if kind in {"reason", "comparison", "prediction", "hypothesis", "example", "application"}:
            roles.add("application" if kind == "example" else kind)
        elif kind in {"method", "plan", "direct_request"}:
            roles.add("method")
    return roles


def _candidate_roles(core_text: str, application_text: str, candidate: dict[str, Any]) -> set[str]:
    lower = " ".join(f"{core_text} {application_text}".lower().split())
    roles = {str(item).lower() for item in _text_list(candidate.get("semantic_roles"))}
    if candidate.get("central_claim") or re.search(r"\b(?:is|are|means|refers to)\b", lower):
        roles.add("definition")
    if candidate.get("relationships") or re.search(r"\b(?:because|cause|causes|leads to|results in|therefore|mechanism)\b", lower):
        roles.add("reason")
    if re.search(r"\b(?:first|then|next|steps?|method|procedure|process|instructions?|requires?)\b", lower):
        roles.add("method")
    if re.search(r"\b(?:compare|contrast|different|similar|both|whereas|than)\b", lower):
        roles.add("comparison")
    if re.search(r"\b(?:predict|prediction|forecast|likely|expect|pattern)\b", lower):
        roles.add("prediction")
    if re.search(r"\b(?:hypothesis|might|could explain|possible explanation)\b", lower):
        roles.add("hypothesis")
    if candidate.get("examples") or application_text.strip():
        roles.add("application")
    return roles


def _explicit_subject_focus(prompt: str, subject_overlap: set[str]) -> bool:
    if not subject_overlap:
        return False
    lower = " ".join(prompt.lower().split())
    return any(
        re.search(
            rf"\b(?:explain|define|describe|understand|what\s+is|how\s+does|why\s+does|tell\s+me\s+about)"
            rf"\b.{{0,55}}\b{re.escape(term)}\b",
            lower,
        )
        for term in subject_overlap
    )


def _semantic_terms(value: str) -> set[str]:
    terms: set[str] = set()
    for raw in re.findall(r"[a-z0-9][a-z0-9_-]{1,}", value.lower()):
        term = _singular(raw)
        if term not in _STOP_TERMS and len(term) >= 3:
            terms.add(term)
    return terms


def _singular(value: str) -> str:
    if value.endswith("ies") and len(value) > 4:
        return value[:-3] + "y"
    if value.endswith("ses") and len(value) > 4:
        return value[:-2]
    if value.endswith("s") and not value.endswith(("ss", "us", "is")) and len(value) > 4:
        return value[:-1]
    return value


def _phrase_overlap(left: str, right: str) -> bool:
    left_terms = [term for term in (_singular(item) for item in re.findall(r"[a-z0-9][a-z0-9_-]{1,}", left.lower())) if term not in _STOP_TERMS]
    right_terms = [term for term in (_singular(item) for item in re.findall(r"[a-z0-9][a-z0-9_-]{1,}", right.lower())) if term not in _STOP_TERMS]
    right_pairs = set(zip(right_terms, right_terms[1:]))
    return any(pair in right_pairs for pair in zip(left_terms, left_terms[1:]))


def _text_list(value: Any) -> list[str]:
    return [str(item) for item in value or [] if str(item).strip()] if isinstance(value, (list, tuple, set)) else []


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
