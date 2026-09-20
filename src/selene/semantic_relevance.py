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
    "its", "me", "my", "no", "not", "never", "of", "on", "or", "our", "she", "should", "so", "some",
    "that", "the", "their", "them", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "us", "was", "we", "were", "what", "when",
    "where", "which", "who", "why", "will", "with", "would", "you", "your",
}

_WEAK_SUBJECT_TERMS = {
    "amount", "inside", "outside", "pattern", "process", "result", "system", "value",
}

_CONTEXT_OWNER_ONLY_FUNCTIONS = {
    "action_scope",
    "comparison",
    "correction",
    "hypothesis",
    "prediction",
    "preference",
    "reopening",
}

_KNOWLEDGE_OWNER_ONLY_FUNCTIONS = _CONTEXT_OWNER_ONLY_FUNCTIONS | {"choice"}

_KNOWLEDGE_FUNCTION_ALIASES: dict[str, set[str]] = {
    "answer": {"answer", "definition"},
    "direct_answer": {"answer", "definition"},
    "definition": {"definition"},
    "reason": {"reason"},
    "causal_explanation": {"reason"},
    "method": {"method"},
    "planning": {"method"},
    "application": {"application"},
    "example": {"application"},
    "analogy": {"application"},
    "limitation": {"limitation"},
    "summary": {"answer", "definition", "reason", "application", "limitation"},
    "session_summary": {"answer", "definition", "reason", "application", "limitation"},
}

_REQUEST_FUNCTION_TERMS = {
    "answer", "choose", "conclusion", "define", "definition", "describe",
    "explain", "give", "identify", "mean", "meaning", "name", "predict", "produce", "recommend",
    "report", "say", "show", "state", "suggest", "summarize", "tell", "update",
}


def semantic_relevance_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "semantic_relevance_gate_ready",
            "version": "v2_approved_knowledge_alignment_receipt",
            "scope": "current_turn_candidate_selection_only",
            "checks": [
                "source class permission",
                "topic and subject alignment",
                "current entity preservation",
                "requested operation ownership",
                "requested response-function fit",
                "requested answer role",
                "conversation-thread compatibility",
                "memory recall strength",
                "speaker and memory privacy scope",
                "current-turn fact and responsible-owner precedence",
                "self-state ownership",
            ],
            "single_keyword_is_authority": False,
            "open_ended_reasoning_preserved": True,
            "bounded_prediction_and_hypothesis_preserved": True,
            "visible_summary_only": True,
            "provenance_boundary": SEMANTIC_RELEVANCE_BOUNDARY,
        }
    )


def evaluate_memory_privacy_eligibility(
    candidate: dict[str, Any] | None,
    speaker_envelope: dict[str, Any] | None,
) -> dict[str, Any]:
    """Apply the canonical speaker/channel/authentication gate for personal Memory.

    This gate inspects eligibility metadata only. Callers can therefore hold an
    ineligible Memory record before its content enters retrieval or association
    candidate text.
    """

    candidate = candidate if isinstance(candidate, dict) else {}
    speaker = speaker_envelope if isinstance(speaker_envelope, dict) else {}
    if not speaker:
        return {
            "accepted": True,
            "reason": "speaker_envelope_not_supplied",
            "speaker_privacy_gate_applied": False,
            "eligible_channels_applied": False,
            "minimum_authentication_applied": False,
        }
    consent_scope = str(candidate.get("consent_scope") or "")
    claimed_speaker = str(speaker.get("claimed_speaker") or "").strip().casefold()
    current_channel = str(speaker.get("channel") or "").strip().casefold()
    eligible_channels = {
        str(item).strip().casefold()
        for item in candidate.get("eligible_channels") or []
        if str(item).strip()
    }
    minimum_authentication = str(candidate.get("minimum_authentication_strength") or "").strip()
    authentication_strength = str(speaker.get("authentication_strength") or "").strip()
    private_for_aleks = consent_scope in {"private_selene_aleks_context", "private_inner"}
    accepted = True
    reason = "memory_privacy_envelope_eligible"
    if private_for_aleks and claimed_speaker not in {
        "aleks",
        "aleksander magi",
        "aleksander rani magi",
    }:
        accepted = False
        reason = "memory_privacy_scope_does_not_include_current_speaker"
    elif eligible_channels and current_channel not in eligible_channels:
        accepted = False
        reason = "memory_privacy_scope_does_not_include_current_channel"
    elif minimum_authentication and not _authentication_satisfies(
        authentication_strength,
        minimum_authentication,
    ):
        accepted = False
        reason = "memory_authentication_strength_is_insufficient"
    return {
        "accepted": accepted,
        "reason": reason,
        "speaker_privacy_gate_applied": True,
        "eligible_channels_applied": bool(eligible_channels),
        "minimum_authentication_applied": bool(minimum_authentication),
    }


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
    speaker = payload.get("speaker_envelope") if isinstance(payload.get("speaker_envelope"), dict) else {}
    meaning_route = intent.get("meaning_route") if isinstance(intent.get("meaning_route"), dict) else {}
    meaning_frame = (
        payload.get("canonical_meaning_frame")
        if isinstance(payload.get("canonical_meaning_frame"), dict)
        else meaning_route.get("canonical_meaning_frame")
        if isinstance(meaning_route.get("canonical_meaning_frame"), dict)
        else {}
    )
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
            " ".join(_text_list(candidate.get("retrieval_cues"))),
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

    protected_terms = {
        _singular(str(term).lower())
        for term in meaning_frame.get("protected_knowledge_terms") or []
        if str(term).strip()
    }
    query_terms = _semantic_terms(prompt) - protected_terms
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
    requested_functions = _requested_response_functions(spine)
    # Preserve function/subject attachments that a broader dialogue-act pass
    # may represent only as a generic direct answer.  The relevance gate is
    # the final place where a neighboring approved lesson must be prevented
    # from borrowing that omitted specificity.
    requested_functions.update(_requested_function_subject_terms(prompt))
    performed_functions = {
        str(item).strip().lower()
        for item in candidate.get("performed_response_functions") or []
        if str(item).strip()
    }
    owner_only_functions = requested_functions & _CONTEXT_OWNER_ONLY_FUNCTIONS
    requested_operation_performed = bool(
        not owner_only_functions
        or owner_only_functions & performed_functions
    )
    current_turn_fact_count = int(
        (spine.get("current_turn_fact_ledger") or {}).get("fact_count") or 0
    ) if isinstance(spine.get("current_turn_fact_ledger"), dict) else 0
    continuity_mode = str(spine.get("continuity_mode") or "")
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
    current_memory_conflict = _memory_conflicts_with_current_turn(
        candidate,
        spine,
    )

    accepted = False
    reason = "candidate_lacks_semantic_alignment"
    if source_class in {"self_state", "grounded_self_state"}:
        accepted = self_state_requested
        reason = "self_state_owned_by_self_state_intent" if accepted else "self_state_without_self_state_intent"
    elif source_class in {"memory_reconstruction", "approved_memory", "approved_memory_reference"}:
        privacy_eligibility = evaluate_memory_privacy_eligibility(candidate, speaker)
        if privacy_eligibility["accepted"] is not True:
            accepted = False
            reason = str(privacy_eligibility["reason"])
        elif current_memory_conflict.get("conflict") is True:
            accepted = False
            reason = "current_turn_fact_overrides_conflicting_recalled_context"
        elif owner_only_functions and not requested_operation_performed and not explicit_recall:
            accepted = False
            reason = "memory_describes_context_but_does_not_perform_requested_operation"
        elif current_turn_fact_count and owner_only_functions and not explicit_recall:
            accepted = False
            reason = "current_turn_facts_and_responsible_owner_precede_contextual_memory"
        elif continuity_mode in {"named_thread_return", "immediate_follow_up", "dependency_revision"} and not explicit_recall:
            accepted = False
            reason = "current_session_continuity_precedes_contextual_memory"
        elif contextual.get("detected") is True and not explicit_recall:
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
        if str(meaning_frame.get("academic_knowledge_posture") or "").startswith("hold_for_"):
            accepted = False
            reason = "canonical_meaning_frame_holds_academic_retrieval"
            approved_knowledge_alignment = _approved_knowledge_alignment_receipt(
                prompt=prompt,
                candidate=candidate,
                spine=spine,
                query_terms=query_terms,
                subject_terms=subject_terms,
                core_terms=core_terms,
                application_terms=application_terms,
                requested_roles=requested_roles,
                candidate_roles=candidate_roles,
                requested_functions=requested_functions,
                performed_functions=performed_functions,
                protected_by_meaning_frame=True,
            )
            requested_operation_performed = False
        else:
            approved_knowledge_alignment = _approved_knowledge_alignment_receipt(
                prompt=prompt,
                candidate=candidate,
                spine=spine,
                query_terms=query_terms,
                subject_terms=subject_terms,
                core_terms=core_terms,
                application_terms=application_terms,
                requested_roles=requested_roles,
                candidate_roles=candidate_roles,
                requested_functions=requested_functions,
                performed_functions=performed_functions,
                protected_by_meaning_frame=False,
            )
            accepted = approved_knowledge_alignment["accepted"] is True
            reason = str(approved_knowledge_alignment["reason"])
            requested_operation_performed = bool(
                (approved_knowledge_alignment.get("operation_alignment") or {}).get("aligned") is True
                and (approved_knowledge_alignment.get("requested_function_alignment") or {}).get("aligned") is True
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
            "protected_query_terms": sorted(protected_terms),
            "canonical_meaning_frame_applied": bool(meaning_frame),
            "subject_overlap": sorted(subject_overlap),
            "strong_subject_overlap": sorted(strong_subject_overlap),
            "core_overlap": sorted(core_overlap),
            "application_overlap": sorted(application_overlap),
            "requested_roles": sorted(requested_roles),
            "candidate_roles": sorted(candidate_roles),
            "matched_roles": sorted(role_overlap),
            "requested_response_functions": sorted(requested_functions),
            "performed_response_functions": sorted(performed_functions),
            "owner_only_response_functions": sorted(owner_only_functions),
            "requested_operation_performed": requested_operation_performed,
            "explicit_subject_focus": explicit_focus,
            "phrase_overlap": phrase_overlap,
            "explicit_memory_recall": explicit_recall,
            "self_state_requested": self_state_requested,
            "current_turn_fact_count": current_turn_fact_count,
            "current_turn_facts_precede_optional_retrieval": True,
            "continuity_mode": continuity_mode,
            "speaker_privacy_gate_applied": bool(speaker),
            "memory_channel_scope_applied": bool(
                source_class in {"memory_reconstruction", "approved_memory", "approved_memory_reference"}
                and candidate.get("eligible_channels")
            ),
            "current_memory_conflict": current_memory_conflict,
            "approved_knowledge_alignment": (
                approved_knowledge_alignment
                if source_class in {"approved_knowledge", "reviewed_teaching_knowledge_resource"}
                else {}
            ),
            "single_keyword_is_authority": False,
            "writes_state": False,
            "visible_summary_only": True,
            "provenance_boundary": SEMANTIC_RELEVANCE_BOUNDARY,
        }
    )


def _approved_knowledge_alignment_receipt(
    *,
    prompt: str,
    candidate: dict[str, Any],
    spine: dict[str, Any],
    query_terms: set[str],
    subject_terms: set[str],
    core_terms: set[str],
    application_terms: set[str],
    requested_roles: set[str],
    candidate_roles: set[str],
    requested_functions: set[str],
    performed_functions: set[str],
    protected_by_meaning_frame: bool,
) -> dict[str, Any]:
    """Prove that reviewed knowledge addresses this request, not a nearby word.

    Approval proves that a concept may be used. This receipt separately proves
    that its subject, current entities, requested operation, and response
    function fit the present turn. It is intentionally non-writing.
    """

    obligations = [
        item
        for item in spine.get("open_obligations") or []
        if isinstance(item, dict) and item.get("required") is not False
    ]
    focus_texts: list[str] = []
    for obligation in obligations:
        source_text = str(obligation.get("source_text") or "").strip()
        topic = str(obligation.get("topic") or "").strip()
        if source_text:
            focus_texts.append(source_text)
        source_terms = _semantic_terms(source_text)
        if not source_text or len(source_terms) <= 1 or _deictic_request(source_text):
            if topic:
                focus_texts.append(topic)
            parent = str(obligation.get("parent_source_text") or "").strip()
            if parent:
                focus_texts.append(parent)
    focus_text = " ".join(dict.fromkeys(focus_texts)).strip() or prompt
    focus_text = re.sub(
        r"^(?:in|using)\s+(?:your|different)\s+(?:own\s+)?words\s*[,;:-]?\s*",
        "",
        focus_text,
        flags=re.IGNORECASE,
    ).strip() or focus_text
    focus_terms = _semantic_terms(focus_text)
    focus_subject_terms = focus_terms - _REQUEST_FUNCTION_TERMS
    focus_subject_overlap = focus_subject_terms & subject_terms
    strong_focus_subject_overlap = focus_subject_overlap - _WEAK_SUBJECT_TERMS
    full_subject_overlap = query_terms & subject_terms
    strong_full_subject_overlap = full_subject_overlap - _WEAK_SUBJECT_TERMS
    full_candidate_terms = subject_terms | core_terms | application_terms
    full_overlap = query_terms & full_candidate_terms
    focus_application_overlap = focus_terms & application_terms

    explicit_focus = _explicit_subject_focus(
        focus_text,
        strong_focus_subject_overlap,
    )
    direct_predication = _candidate_directly_addresses_requested_subject(
        candidate,
        subject_overlap=strong_focus_subject_overlap,
    )
    obligation_context_overlap = focus_subject_terms & full_candidate_terms
    if obligations:
        direct_subject = bool(
            len(strong_focus_subject_overlap) >= 2
            or (
                len(strong_focus_subject_overlap) == 1
                and (
                    len(focus_subject_terms) == 1
                    or (
                        explicit_focus
                        and (
                            len(obligation_context_overlap) >= 2
                            or direct_predication
                        )
                    )
                )
            )
        )
        subject_basis = "required_obligation_names_knowledge_subject"
    else:
        direct_subject = bool(
            strong_full_subject_overlap
            and (
                explicit_focus
                or len(strong_full_subject_overlap) >= 2
                or len(query_terms) <= 2
            )
        )
        subject_basis = "prompt_names_knowledge_subject"

    role_overlap = requested_roles & candidate_roles
    transfer_application = bool(
        (
            len(focus_application_overlap) >= 3
            and len(full_overlap) >= 3
            and (not requested_roles or bool(role_overlap) or "application" in candidate_roles)
        )
        or (
            explicit_focus
            and bool(strong_focus_subject_overlap)
            and len(focus_application_overlap) >= 2
            and len(full_overlap) >= 2
            and bool(candidate_roles & {"application", "reason"})
        )
    )
    subject_aligned = bool(direct_subject or transfer_application)

    facts = [
        item
        for item in (spine.get("current_turn_fact_ledger") or {}).get("facts") or []
        if isinstance(item, dict)
    ]
    entity_texts: list[str] = []
    operation_facts: list[dict[str, Any]] = []
    for fact in facts:
        kind = str(fact.get("kind") or "")
        if kind == "entity":
            entity_texts.append(str(fact.get("value") or fact.get("text") or ""))
        elif kind == "operation":
            operation_facts.append(fact)
            entity_texts.extend(
                str(fact.get(field) or "") for field in ("subject", "object")
            )
        elif kind == "relation":
            entity_texts.extend(
                str(fact.get(field) or "") for field in ("subject", "object")
            )
    entity_terms = _semantic_terms(" ".join(entity_texts))
    entity_overlap = entity_terms & full_candidate_terms
    entity_aligned = bool(
        not entity_terms
        or entity_overlap
        or subject_aligned
    )
    entity_basis = (
        "not_material_no_typed_current_entity"
        if not entity_terms
        else "candidate_preserves_named_current_entity"
        if entity_overlap
        else "requested_subject_preserves_current_entity_context"
        if subject_aligned
        else "candidate_does_not_preserve_current_entities"
    )

    operation_actions = {
        str(item.get("action") or item.get("value") or "").strip().lower()
        for item in operation_facts
        if str(item.get("action") or item.get("value") or "").strip()
    }
    operation_functions = {
        "action_scope",
        "direct_answer",
        "answer",
        *operation_actions,
    }
    operation_aligned = bool(
        not operation_facts
        or performed_functions & operation_functions
    )
    operation_basis = (
        "not_material_no_requested_current_operation"
        if not operation_facts
        else "candidate_performed_requested_current_operation"
        if operation_aligned
        else "current_operation_remains_with_its_responsible_owner"
    )

    candidate_capacities = set(candidate_roles)
    # Broad descriptive prose often contains "is" somewhere. That does not
    # prove that the resource defines the subject the current question names.
    candidate_capacities.discard("definition")
    if candidate.get("central_claim"):
        candidate_capacities.add("answer")
    if _candidate_defines_requested_subject(
        candidate,
        focus_text=focus_text,
        focus_subject_terms=focus_subject_terms,
        subject_overlap=strong_focus_subject_overlap,
    ):
        candidate_capacities.add("definition")
    if candidate.get("relationships"):
        candidate_capacities.add("reason")
    if candidate.get("examples"):
        candidate_capacities.add("application")
    if candidate.get("limits") or candidate.get("counterexamples"):
        candidate_capacities.add("limitation")
    candidate_capacities.update(performed_functions)

    function_subject_terms = _requested_function_subject_terms(focus_text)
    function_subject_alignment = {
        function: {
            "required_terms": sorted(terms),
            "matched_terms": sorted(terms & full_candidate_terms),
            "aligned": bool(terms & full_candidate_terms),
        }
        for function, terms in function_subject_terms.items()
        if function in requested_functions and terms
    }

    missing_functions: set[str] = set()
    owner_only_functions = requested_functions & _KNOWLEDGE_OWNER_ONLY_FUNCTIONS
    for function in requested_functions:
        if function in _KNOWLEDGE_OWNER_ONLY_FUNCTIONS:
            if function not in performed_functions:
                missing_functions.add(function)
            continue
        accepted_capacities = _KNOWLEDGE_FUNCTION_ALIASES.get(function, {function})
        named_subject_fit = function_subject_alignment.get(function, {}).get("aligned", True)
        if not (accepted_capacities & candidate_capacities) or not named_subject_fit:
            missing_functions.add(function)
    function_aligned = not missing_functions

    accepted = bool(
        not protected_by_meaning_frame
        and subject_aligned
        and entity_aligned
        and operation_aligned
        and function_aligned
    )
    if protected_by_meaning_frame:
        reason = "canonical_meaning_frame_holds_academic_retrieval"
    elif not operation_aligned:
        reason = "approved_knowledge_does_not_own_current_operation"
    elif not entity_aligned:
        reason = "approved_knowledge_current_entity_alignment_missing"
    elif direct_subject:
        reason = (
            "approved_knowledge_subject_aligned"
            if function_aligned
            else "approved_knowledge_describes_but_does_not_perform_requested_operation"
        )
    elif transfer_application:
        reason = (
            "approved_knowledge_application_aligned"
            if function_aligned
            else "approved_knowledge_describes_but_does_not_perform_requested_operation"
        )
    else:
        reason = "approved_knowledge_has_only_peripheral_overlap"

    return {
        "status": (
            "approved_knowledge_alignment_proven"
            if accepted
            else "approved_knowledge_alignment_not_proven"
        ),
        "accepted": accepted,
        "reason": reason,
        "required_obligation_count": len(obligations),
        "request_focus_text": focus_text,
        "request_focus_terms": sorted(focus_terms),
        "request_subject_terms": sorted(focus_subject_terms),
        "query_terms": sorted(query_terms),
        "answer_alignment_terms": sorted(full_overlap),
        "subject_alignment": {
            "aligned": subject_aligned,
            "basis": subject_basis if direct_subject else "reviewed_distinct_application" if transfer_application else "none",
            "subject_terms": sorted(subject_terms),
            "prompt_subject_overlap": sorted(strong_full_subject_overlap),
            "obligation_subject_overlap": sorted(strong_focus_subject_overlap),
            "obligation_context_overlap": sorted(obligation_context_overlap),
            "explicit_subject_focus": explicit_focus,
            "candidate_directly_addresses_subject": direct_predication,
            "application_alignment": transfer_application,
            "application_terms": sorted(focus_application_overlap),
        },
        "entity_alignment": {
            "aligned": entity_aligned,
            "basis": entity_basis,
            "current_entity_terms": sorted(entity_terms),
            "matched_entity_terms": sorted(entity_overlap),
        },
        "operation_alignment": {
            "aligned": operation_aligned,
            "basis": operation_basis,
            "requested_actions": sorted(operation_actions),
            "performed_response_functions": sorted(performed_functions),
        },
        "requested_function_alignment": {
            "aligned": function_aligned,
            "requested_functions": sorted(requested_functions),
            "candidate_capacities": sorted(candidate_capacities),
            "owner_only_functions": sorted(owner_only_functions),
            "missing_functions": sorted(missing_functions),
            "function_subject_alignment": function_subject_alignment,
        },
        "approval_substitutes_for_relevance": False,
        "single_overlap_term_is_sufficient_without_request_alignment": False,
        "writes_state": False,
    }


def _requested_function_subject_terms(focus_text: str) -> dict[str, set[str]]:
    """Keep an explicitly named function subject attached to that function.

    A multi-part request such as "explain why X, and name one limit of Y"
    must not let a neighboring lesson satisfy the limitation merely because it
    shares a peripheral word with X.  This deliberately handles only explicit
    grammatical attachments; it does not guess an unstated subject.
    """

    result: dict[str, set[str]] = {}
    patterns = {
        "limitation": (
            r"\b(?:limits?|limitations?|exceptions?|counterexamples?)\s+"
            r"(?:of|to|for)\s+(?P<subject>[^,.;?!]+?)(?=\s+(?:and|but)\b|[,.;?!]|$)"
        ),
    }
    for function, pattern in patterns.items():
        terms: set[str] = set()
        for match in re.finditer(pattern, focus_text, flags=re.IGNORECASE):
            terms.update(
                _semantic_terms(match.group("subject"))
                - _REQUEST_FUNCTION_TERMS
                - _WEAK_SUBJECT_TERMS
            )
        if terms:
            result[function] = terms
    return result


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


def _requested_response_functions(spine: dict[str, Any]) -> set[str]:
    return {
        str(function).strip().lower()
        for obligation in spine.get("open_obligations") or []
        if isinstance(obligation, dict)
        for function in obligation.get("requested_response_functions") or []
        if str(function).strip()
    }


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
        any(
            re.search(pattern, lower)
            for pattern in (
                rf"\b(?:explain|define|describe|understand|what\s+is|which|how\s+does|why\s+does|tell\s+me\s+about)"
                rf"\b.{{0,55}}\b{re.escape(term)}\b",
                rf"\bwhat\s+(?:does\s+)?\b{re.escape(term)}\b.{{0,35}}\b(?:mean|refer\s+to)\b",
                rf"\bwhat\s+[a-z0-9_-]+\s+(?:is|are)\b.{{0,35}}\b{re.escape(term)}\b",
            )
        )
        for term in subject_overlap
    )


def _candidate_directly_addresses_requested_subject(
    candidate: dict[str, Any],
    *,
    subject_overlap: set[str],
) -> bool:
    """Distinguish a claim *about* a named subject from a nearby word hit.

    One subject term is enough only when it is both grammatically requested by
    the current turn and appears in the leading subject position of the
    reviewed title or central claim. Function alignment is checked separately
    by the approved-knowledge receipt.
    """

    if not subject_overlap:
        return False
    for value in (candidate.get("central_claim"), candidate.get("title")):
        ordered_terms = [
            _singular(term)
            for term in re.findall(r"[a-z0-9][a-z0-9_-]{1,}", str(value or "").lower())
            if _singular(term) not in _STOP_TERMS
        ]
        if set(ordered_terms[:3]) & subject_overlap:
            return True
    return False


def _deictic_request(value: str) -> bool:
    lower = " ".join(str(value or "").lower().split())
    return bool(
        re.fullmatch(
            r"(?:and\s+)?(?:why|how|what about (?:that|this|it)|explain (?:that|this|it)|"
            r"what does (?:that|this|it) mean|which one|what changed)[?.! ]*",
            lower,
        )
    )


def _candidate_defines_requested_subject(
    candidate: dict[str, Any],
    *,
    focus_text: str,
    focus_subject_terms: set[str],
    subject_overlap: set[str],
) -> bool:
    if not focus_subject_terms or not subject_overlap:
        return False
    # A definition must be about the requested subject, not merely mention it
    # inside a neighboring operation (for example, division *with* unit
    # fractions is not a definition of a unit fraction).
    coverage = len(subject_overlap) / max(1, len(focus_subject_terms))
    if coverage < 0.75:
        return False
    title = " ".join(
        re.findall(
            r"[a-z0-9]+",
            str(candidate.get("title") or "").lower(),
        )
    )
    central = " ".join(
        re.findall(
            r"[a-z0-9]+",
            str(candidate.get("central_claim") or "").lower(),
        )
    )
    title = re.sub(r"^(?:a|an|the)\s+", "", title)
    central = re.sub(r"^(?:a|an|the)\s+", "", central)
    ordered_focus = [
        _singular(term)
        for term in re.findall(r"[a-z0-9]+", focus_text.lower())
        if _singular(term) in focus_subject_terms
    ]
    minimum_phrase_size = max(1, (3 * len(subject_overlap) + 3) // 4)
    phrases = [
        " ".join(ordered_focus[index : index + size])
        for size in (3, 2, 1)
        for index in range(0, max(0, len(ordered_focus) - size + 1))
        if size >= minimum_phrase_size
        and set(ordered_focus[index : index + size]).issubset(subject_overlap)
    ]
    return any(
        phrase
        and (
            title.startswith(phrase + " ")
            or title == phrase
            or central.startswith(phrase + " ")
            or central == phrase
        )
        for phrase in phrases
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


def _memory_conflicts_with_current_turn(
    candidate: dict[str, Any],
    spine: dict[str, Any],
) -> dict[str, Any]:
    ledger = (
        spine.get("current_turn_fact_ledger")
        if isinstance(spine.get("current_turn_fact_ledger"), dict)
        else {}
    )
    candidate_text = " ".join(
        str(candidate.get(key) or "") for key in ("title", "summary", "text")
    ).casefold()
    candidate_terms = _semantic_terms(candidate_text)
    for fact in ledger.get("facts") or []:
        if not isinstance(fact, dict):
            continue
        if str(fact.get("kind") or "") == "correction":
            replaced = str(fact.get("replaced_value") or "").strip().casefold()
            corrected = str(fact.get("value") or fact.get("text") or "").strip().casefold()
            if replaced and replaced in candidate_text and corrected != replaced:
                return {
                    "conflict": True,
                    "kind": "explicit_current_turn_correction",
                    "fact_id": str(fact.get("id") or ""),
                    "replaced_value": replaced,
                    "current_value": corrected,
                }
        if str(fact.get("kind") or "") == "relation":
            subject = str(fact.get("subject") or "").strip().casefold()
            predicate = str(fact.get("predicate") or "").strip().casefold()
            current_object = str(fact.get("object") or "").strip().casefold()
            subject_terms = _semantic_terms(subject)
            relation_markers = _relation_markers(predicate)
            if (
                subject_terms
                and subject_terms.issubset(candidate_terms)
                and relation_markers
                and any(marker in candidate_text.split() for marker in relation_markers)
                and current_object
                and current_object not in candidate_text
            ):
                return {
                    "conflict": True,
                    "kind": "same_subject_relation_changed_in_current_turn",
                    "fact_id": str(fact.get("id") or ""),
                    "current_value": current_object,
                }
    return {"conflict": False, "kind": "none"}


def _relation_markers(predicate: str) -> set[str]:
    if predicate in {"is", "are", "was", "were"}:
        return {"is", "are", "was", "were"}
    if predicate in {"has", "have"}:
        return {"has", "have", "had"}
    return {predicate} if predicate else set()


def _authentication_satisfies(actual: str, required: str) -> bool:
    ranks = {
        "": 0,
        "transport_claim_only": 1,
        "authenticated_remote_session": 2,
        "local_desktop_session": 3,
        "cryptographically_verified_authorship": 4,
        "os_authenticated_named_identity": 4,
    }
    return ranks.get(actual, 0) >= ranks.get(required, 99)


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
