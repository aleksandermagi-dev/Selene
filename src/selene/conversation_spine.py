from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .pragmatic_planner import build_pragmatic_plan
from .conversation_continuity import resolve_conversation_continuity
from .current_turn_fact_ledger import build_current_turn_fact_ledger
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
                "selective current-session epistemic updates and model ancestry",
                "bounded visible session landmarks",
                "open response obligations",
                "typed current-turn entities quantities options criteria observations claims relations conditions corrections and sequence",
                "owner-specific current-turn input receipts before optional retrieval",
                "session topic branches returns dependencies and landings",
                "one selected continuity target across immediate answers threads landmarks checkpoints and referents",
                "bounded long-thread structural index and saturation handoff",
                "mixed dialogue acts without collapsing separate obligations",
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
    figurative_interpretation = (
        payload.get("figurative_interpretation")
        if isinstance(payload.get("figurative_interpretation"), dict)
        else {}
    )
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
    referent_address = (
        pragmatics.get("referent_address")
        if isinstance(pragmatics.get("referent_address"), dict)
        else {}
    )
    epistemic_revision = (
        pragmatics.get("epistemic_update_plan")
        if isinstance(pragmatics.get("epistemic_update_plan"), dict)
        else {}
    )
    epistemic_updates = [
        item for item in pragmatics.get("epistemic_updates") or [] if isinstance(item, dict)
    ][-12:]
    session_proposition_ledger = (
        pragmatics.get("session_proposition_ledger")
        if isinstance(pragmatics.get("session_proposition_ledger"), dict)
        else {}
    )
    thread_braid = pragmatics.get("thread_braid") if isinstance(pragmatics.get("thread_braid"), dict) else {}
    continuity_resolution = (
        payload.get("conversation_continuity")
        if isinstance(payload.get("conversation_continuity"), dict)
        else resolve_conversation_continuity(
            {
                "prompt": interpreted,
                "intent_decision": intent,
                "dialogue_workspace": dialogue,
                "contextual_follow_up": contextual,
                "conversation_events": payload.get("conversation_events") or [],
            }
        )
    )
    previous = _previous_answer(contextual, pragmatics, payload.get("conversation_events"))
    stale_proposition_texts = [
        str(item.get("text") or "")
        for item in session_proposition_ledger.get("propositions") or []
        if isinstance(item, dict)
        and str(item.get("status") or "") in {"invalidated", "superseded"}
        and str(item.get("text") or "").strip()
    ]
    previous_preview = str(previous.get("preview") or "")
    if previous_preview and any(
        _text_overlap(previous_preview, stale_text) >= 0.65
        for stale_text in stale_proposition_texts
    ):
        previous = {
            **previous,
            "preview": "",
            "claims": [],
            "recommendations": [],
            "source": "revision_ancestry_only",
            "stale_preview": previous_preview,
            "eligible_for_answer_grounding": False,
        }
    all_session_landmarks = [
        item for item in pragmatics.get("session_landmarks") or [] if isinstance(item, dict)
    ][-64:]
    stale_proposition_ids = {
        str(item)
        for item in session_proposition_ledger.get("stale_proposition_ids") or []
        if str(item)
    }
    session_landmarks = [
        item
        for item in all_session_landmarks
        if not str(item.get("proposition_id") or "")
        or str(item.get("proposition_id") or "") not in stale_proposition_ids
    ]
    relevant_landmarks = _relevant_landmarks(interpreted, session_landmarks)
    continuity_landmarks = [
        item
        for item in continuity_resolution.get("selected_landmarks") or []
        if isinstance(item, dict)
    ]
    if continuity_landmarks and str(continuity_resolution.get("mode") or "") in {
        "named_thread_return",
        "session_summary",
        "active_thread_continuation",
    }:
        relevant_landmarks = continuity_landmarks
    prior_session_facts = [
        item
        for item in pragmatics.get("session_facts") or []
        if isinstance(item, dict)
    ]
    session_facts = _session_facts(
        payload.get("conversation_events"),
        current_prompt=interpreted,
        prior_facts=prior_session_facts,
    )
    relevant_session_facts = _relevant_session_facts(interpreted, session_facts)
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
    current_turn_fact_ledger = build_current_turn_fact_ledger(
        {
            "session_id": session_id,
            "prompt": prompt,
            "interpreted_text": interpreted,
            "obligations": obligations,
            "correction_refinement": pragmatics.get("correction_refinement") or {},
            "epistemic_revision": epistemic_revision,
        }
    )
    current_turn_facts = [
        item
        for item in current_turn_fact_ledger.get("facts") or []
        if isinstance(item, dict)
    ]
    active_topic = truncate(str(dialogue.get("active_topic") or ""), 500)
    topic_anchors = _unique_text(
        [
            active_topic,
            str((continuity_resolution.get("selected_target") or {}).get("label") or ""),
            str((continuity_resolution.get("selected_thread") or {}).get("topic") or ""),
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
                str(epistemic_revision.get("target") or ""),
                str(epistemic_revision.get("revised_claim") or ""),
                str(resolved_reference.get("resolved_to") or ""),
                *previous["recommendations"],
            ]
        )
    )
    compatible_source_classes = _compatible_source_classes(intent_class, contextual)
    ambiguity = pragmatic_plan.get("ambiguity") if isinstance(pragmatic_plan.get("ambiguity"), dict) else {}
    referent_status = str(resolved_reference.get("resolution_status") or "not_needed")
    grounded_prompt = interpreted
    continuity_grounding = truncate(
        str(continuity_resolution.get("grounding_text") or ""),
        1800,
    )
    if continuity_grounding:
        grounded_prompt = truncate(
            f"{grounded_prompt} {continuity_grounding}",
            3600,
        )
    if relevant_session_facts:
        fact_text = " ".join(str(item.get("text") or "") for item in relevant_session_facts[:6])
        grounded_prompt = truncate(
            f"{grounded_prompt} Relevant user-supplied facts from this session: {fact_text}",
            4000,
        )
    if current_turn_facts:
        current_fact_text = " ".join(
            str(item.get("text") or "")
            for item in current_turn_facts[:12]
            if str(item.get("text") or "").strip()
        )
        grounded_prompt = truncate(
            f"{grounded_prompt} Current-turn supplied facts: {current_fact_text}",
            5000,
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
            "figurative_interpretation": figurative_interpretation,
            "literal_and_nonliteral_readings_remain_distinct": True,
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
            "conversation_continuity": continuity_resolution,
            "continuity_mode": str(continuity_resolution.get("mode") or ""),
            "continuity_target": continuity_resolution.get("selected_target") or {},
            "entities": [item for item in dialogue.get("entities") or [] if isinstance(item, dict)][:20],
            "referents": {
                "resolved_current": resolved_reference or None,
                "address_resolution": referent_address or None,
                "known_session_referents": dialogue.get("referents") if isinstance(dialogue.get("referents"), dict) else {},
                "status": referent_status,
            },
            "referent_address": referent_address,
            "names_are_identity_objects": False,
            "previous_answer": previous,
            "epistemic_revision": epistemic_revision,
            "epistemic_updates": epistemic_updates,
            "selective_revision_active": epistemic_revision.get("detected") is True,
            "session_proposition_ledger": session_proposition_ledger,
            "active_session_propositions": [
                item
                for item in session_proposition_ledger.get("active_propositions") or []
                if isinstance(item, dict)
            ][:64],
            "stale_session_propositions_eligible_for_grounding": False,
            "session_landmarks": session_landmarks,
            "stale_session_landmark_ids_excluded": [
                str(item.get("id") or "")
                for item in all_session_landmarks
                if item not in session_landmarks and str(item.get("id") or "")
            ],
            "relevant_session_landmarks": relevant_landmarks,
            "session_facts": session_facts,
            "relevant_session_facts": relevant_session_facts,
            "session_facts_are_durable_memory": False,
            "current_turn_fact_ledger": current_turn_fact_ledger,
            "current_turn_facts": current_turn_facts,
            "current_turn_owner_inputs": current_turn_fact_ledger.get("owner_inputs") or [],
            "current_turn_facts_precede_optional_retrieval": True,
            "open_obligations": obligations,
            "obligation_sequence": [str(item.get("id") or "") for item in obligations],
            "obligation_ledger": {
                **(
                    pragmatic_plan.get("obligation_ledger")
                    if isinstance(pragmatic_plan.get("obligation_ledger"), dict)
                    else {}
                ),
                "obligations": obligations,
                "obligation_sequence": [str(item.get("id") or "") for item in obligations],
                "downstream_reparse_allowed": False,
            },
            "pragmatic_plan": pragmatic_plan,
            "contextual_follow_up": contextual,
            "ambiguity": ambiguity,
            "source_compatibility": {
                "compatible_source_classes": compatible_source_classes,
                "topic_alignment_required_for_content_sources": intent_class in {
                    "reasoning", "direct_content", "contextual_content"
                },
                "immediate_callback_prefers_previous_answer": (
                    continuity_resolution.get("immediate_previous_answer_relevant") is True
                ),
                "named_return_prefers_selected_landmark": (
                    str(continuity_resolution.get("mode") or "")
                    == "named_thread_return"
                ),
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


_NUMBER_WORD = (
    r"(?:\d+|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|"
    r"forty|fifty|sixty)"
)


def _session_facts(
    events: Any,
    *,
    current_prompt: str,
    prior_facts: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Derive small answerable facts from visible user turns in this session only."""
    source_events = [item for item in events or [] if isinstance(item, dict)][-16:]
    user_events = [
        (str(item.get("id") or index), str(item.get("preview") or ""))
        for index, item in enumerate(source_events)
        if str(item.get("role") or "") == "user" and str(item.get("preview") or "").strip()
    ]
    user_events.append(("current_prompt", current_prompt))
    facts: list[dict[str, Any]] = [
        dict(item)
        for item in prior_facts or []
        if str(item.get("fact_key") or "") and str(item.get("text") or "").strip()
    ][-20:]
    for order, (event_id, text) in enumerate(user_events):
        for fact in _extract_session_facts(text, event_id=event_id, order=order):
            replacement_key = str(fact.get("replacement_key") or "")
            if replacement_key:
                facts = [item for item in facts if str(item.get("replacement_key") or "") != replacement_key]
            duplicate_key = str(fact.get("fact_key") or "")
            facts = [item for item in facts if str(item.get("fact_key") or "") != duplicate_key]
            facts.append(fact)
    return facts[-20:]


def _extract_session_facts(text: str, *, event_id: str, order: int) -> list[dict[str, Any]]:
    normalized = " ".join(str(text or "").replace("’", "'").split())
    lower = normalized.lower()
    if not normalized:
        return []
    facts: list[dict[str, Any]] = []

    duration = re.search(
        rf"\b(?:i|we)\s+(?:only\s+)?have\s+(?P<count>{_NUMBER_WORD})\s+"
        r"(?P<unit>minutes?|hours?)\b",
        lower,
        flags=re.IGNORECASE,
    )
    if duration:
        count, unit = duration.group("count"), duration.group("unit")
        facts.append(
            _session_fact(
                "time_constraint",
                f"The available time is {count} {unit}.",
                f"time:{count}:{unit}",
                "time:available",
                event_id,
                order,
            )
        )

    inventory = re.search(
        r"\b(?:the\s+)?(?P<place>[a-z][a-z-]{1,30})\s+has\s+"
        rf"(?:{_NUMBER_WORD}\s+)?(?P<collection>piles?|groups?|stacks?|areas?|sections?)\s*:\s*"
        r"(?P<items>[^.!?]{3,180})",
        lower,
        flags=re.IGNORECASE,
    )
    if inventory:
        place = inventory.group("place")
        items = [
            re.sub(r"^and\s+", "", item.strip(" ,"), flags=re.IGNORECASE)
            for item in re.split(r",\s*|\s+and\s+", inventory.group("items"))
            if item.strip(" ,")
        ][:8]
        if items:
            joined = ", ".join(items[:-1]) + (f", and {items[-1]}" if len(items) > 1 else items[0])
            facts.append(
                _session_fact(
                    "inventory",
                    f"The {place} has {joined}.",
                    f"inventory:{place}:{'|'.join(items)}",
                    f"inventory:{place}",
                    event_id,
                    order,
                )
            )

    state_patterns = (
        (
            "completed_state",
            r"\b(?:the\s+)?(?P<subject>[a-z][a-z-]*(?:\s+[a-z][a-z-]*){0,4}?)\s+"
            r"(?:is|are)\s+(?P<state>already\s+(?:sorted|finished|done|organized|cleared))\b",
        ),
        (
            "active_problem",
            r"\b(?:the\s+)?(?P<subject>[a-z][a-z-]*(?:\s+[a-z][a-z-]*){0,4}?)\s+"
            r"(?:is|are)\s+(?P<state>the\s+(?:real|actual|main)\s+(?:mess|problem|priority|issue))\b",
        ),
    )
    for kind, pattern in state_patterns:
        for match in re.finditer(pattern, lower, flags=re.IGNORECASE):
            subject = match.group("subject").strip()
            state = match.group("state").strip()
            copula = "are" if subject.endswith("s") else "is"
            facts.append(
                _session_fact(
                    kind,
                    f"The {subject} {copula} {state}.",
                    f"state:{subject}:{state}",
                    f"state:{subject}",
                    event_id,
                    order,
                )
            )

    keep_reason = re.search(
        r"\bkeep\s+(?:the\s+)?(?P<object>[a-z][a-z-]*(?:\s+[a-z][a-z-]*){0,4}?)\s+"
        r"(?P<place>on|in|near|by)\s+(?:the\s+)?(?P<location>[a-z][a-z-]*(?:\s+[a-z][a-z-]*){0,3}?)\s+"
        r"because\s+(?P<reason>[^.!?]{2,100})",
        lower,
        flags=re.IGNORECASE,
    )
    if keep_reason:
        obj = keep_reason.group("object").strip()
        place = keep_reason.group("place")
        location = keep_reason.group("location").strip()
        reason = keep_reason.group("reason").strip(" ,")
        if reason.startswith("i "):
            reason = "I " + reason[2:]
        facts.append(
            _session_fact(
                "exception",
                f"Keep the {obj} {place} the {location} because {reason}.",
                f"exception:{obj}:{place}:{location}:{reason}",
                f"exception:{obj}",
                event_id,
                order,
            )
        )

    unchecked_location = re.search(
        r"\b(?:not\s+sure\s+whether|maybe|may(?:be)?|might)\s+"
        r"(?:the\s+)?(?P<object>[a-z][a-z-]*(?:\s+[a-z][a-z-]*){0,4}?)\s+"
        r"(?:is|are)\s+(?P<location>[^;,.!?]{2,100}).{0,100}\b"
        r"(?:not\s+checked|hasn't\s+been\s+checked|haven't\s+checked|neither\s+of\s+us\s+has\s+checked)\b",
        lower,
        flags=re.IGNORECASE,
    )
    if unchecked_location:
        obj = unchecked_location.group("object").strip()
        facts.append(
            _session_fact(
                "uncertainty",
                f"The location of the {obj} has not been checked.",
                f"uncertainty:location:{obj}",
                f"location:{obj}",
                event_id,
                order,
            )
        )

    dimensions = re.search(
        rf"\b(?P<left>{_NUMBER_WORD})\s*(?P<unit>feet|foot|ft)\s+by\s+"
        rf"(?P<right>{_NUMBER_WORD})\s*(?:feet|foot|ft)?\b",
        lower,
        flags=re.IGNORECASE,
    )
    if dimensions:
        left, right = dimensions.group("left"), dimensions.group("right")
        facts.append(
            _session_fact(
                "dimensions",
                f"The dimensions are {left} feet by {right} feet.",
                f"dimensions:{left}:{right}",
                "dimensions",
                event_id,
                order,
            )
        )

    for match in re.finditer(
        rf"\b(?P<count>{_NUMBER_WORD})\s+(?P<object>chairs?|seats?|tables?|doors?|windows?|outlets?)\b",
        lower,
        flags=re.IGNORECASE,
    ):
        count, obj = match.group("count"), match.group("object")
        facts.append(
            _session_fact(
                "count",
                f"There are {count} {obj}.",
                f"count:{obj}:{count}",
                f"count:{obj.rstrip('s')}",
                event_id,
                order,
            )
        )

    relation = re.search(
        r"\b(?:the\s+)?(?P<subject>[a-z][a-z-]{2,30})\s+(?:is|sits|stands)\s+"
        r"(?P<relation>beside|next\s+to|near|behind|in\s+front\s+of|left\s+of|right\s+of)\s+"
        r"(?:the\s+)?(?P<object>[a-z][a-z-]{2,30})\b",
        lower,
        flags=re.IGNORECASE,
    )
    if relation:
        subject = relation.group("subject")
        rel = " ".join(relation.group("relation").split())
        obj = relation.group("object")
        facts.append(
            _session_fact(
                "relation",
                f"The {subject} is {rel} the {obj}.",
                f"relation:{subject}:{rel}:{obj}",
                f"relation:{subject}",
                event_id,
                order,
            )
        )

    keep = re.search(
        r"\bkeep\s+(?:the\s+)?(?P<object>[a-z][a-z-]*(?:\s+[a-z][a-z-]*){0,4}?)\s+"
        r"(?P<state>open|clear|free|unblocked)\b",
        lower,
        flags=re.IGNORECASE,
    )
    if keep:
        obj, state = keep.group("object"), keep.group("state")
        facts.append(
            _session_fact(
                "constraint",
                f"Keep the {obj} {state}.",
                f"constraint:{obj}:{state}",
                f"constraint:{obj}",
                event_id,
                order,
            )
        )
    return facts


def _session_fact(
    kind: str,
    text: str,
    fact_key: str,
    replacement_key: str,
    event_id: str,
    order: int,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "text": text,
        "fact_key": fact_key,
        "replacement_key": replacement_key,
        "source_event_id": event_id,
        "order": order,
        "terms": _distinctive_terms(text),
        "source_class": "current_session_user_statement",
        "durable_memory": False,
    }


def _relevant_session_facts(prompt: str, facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lower = str(prompt or "").lower()
    summary_request = bool(
        re.search(r"\b(?:summarize|summary|recap|settled (?:points?|facts?))\b", lower)
    )
    query_terms = set(_distinctive_terms(prompt))
    ranked: list[tuple[int, int, dict[str, Any]]] = []
    for index, fact in enumerate(facts):
        terms = set(str(item) for item in fact.get("terms") or [])
        overlap = query_terms & terms
        kind = str(fact.get("kind") or "")
        cue_match = bool(
            kind == "dimensions" and re.search(r"\b(?:dimension|dimensions|size|feet|foot)\b", lower)
            or kind == "count" and overlap
            or kind == "relation" and re.search(r"\b(?:where|beside|near|cord|outlet|chair)\b", lower)
            or kind == "constraint" and re.search(r"\b(?:keep|open|clear|layout|plan|settled)\b", lower)
            or kind == "time_constraint" and re.search(r"\b(?:time|minute|hour|plan|first|tackle)\b", lower)
            or kind == "inventory" and re.search(r"\b(?:desk|pile|group|stack|plan|settled|fact)\b", lower)
            or kind in {"completed_state", "active_problem"} and re.search(
                r"\b(?:correction|update|revise|plan|suggestion|settled|fact|desk|mess|problem|first|tackle)\b",
                lower,
            )
            or kind == "exception" and re.search(r"\b(?:keep|exception|cable|daily|plan|revise|return|settled)\b", lower)
            or kind == "uncertainty" and re.search(r"\b(?:know|checked|sure|location|label|drawer)\b", lower)
        )
        if summary_request or overlap or cue_match:
            ranked.append((4 if cue_match else 2 if overlap else 1, index, fact))
    ranked.sort(key=lambda value: (value[0], value[1]), reverse=True)
    selected = [item for _, _, item in ranked[:6]]
    selected.sort(key=lambda item: int(item.get("order") or 0))
    return selected


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
    open_obligation_ids = {
        str(item.get("id") or "")
        for item in spine.get("open_obligations") or []
        if isinstance(item, dict) and str(item.get("id") or "")
    }
    candidate_obligation_ids = {
        str(item)
        for item in candidate.get("obligation_ids") or []
        if str(item)
    }
    matched_obligation_ids = sorted(
        open_obligation_ids & candidate_obligation_ids
    )
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
    if (
        contextual.get("detected") is True
        and str(contextual.get("kind") or "") != "topic_shift"
        and source_class in {"approved_knowledge", "memory_reconstruction"}
        and not (
            source_class == "approved_knowledge"
            and str(contextual.get("kind") or "") == "answer_development"
        )
    ):
        return _compatibility(False, "callback_must_remain_grounded_in_immediate_conversation", False, matched)
    if matched_obligation_ids:
        return {
            **_compatibility(
                True,
                "candidate_owned_by_current_response_obligation",
                False,
                matched,
            ),
            "matched_obligation_ids": matched_obligation_ids,
        }

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
    contextual = (
        spine.get("contextual_follow_up")
        if isinstance(spine.get("contextual_follow_up"), dict)
        else {}
    )
    immediate_callback = (
        contextual.get("detected") is True
        and str(contextual.get("kind") or "") != "topic_shift"
    )
    required = (
        intent_class in {"reasoning", "direct_content", "contextual_content"}
        and bool(distinctive)
        and not immediate_callback
    )
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
        if item.get("coverage_complete_at_recording") is False:
            continue
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


def _text_overlap(left: str, right: str) -> float:
    left_terms = set(_distinctive_terms(left))
    right_terms = set(_distinctive_terms(right))
    if not left_terms or not right_terms:
        return 0.0
    return len(left_terms & right_terms) / max(1, min(len(left_terms), len(right_terms)))


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
    if (
        contextual.get("detected") is True
        and str(contextual.get("kind") or "") != "topic_shift"
    ):
        if str(contextual.get("kind") or "") == "answer_development":
            return [
                "conversation",
                "domain_answer",
                "approved_knowledge",
                "reasoning_answer",
                "language_capability",
            ]
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
        "parent_source_text": truncate(str(item.get("parent_source_text") or ""), 600),
        "topic": truncate(str(item.get("topic") or ""), 300),
        "coverage_terms": _text_list(item.get("coverage_terms"), limit=24),
        "required": item.get("required") is not False,
        "goal": str(item.get("goal") or "answer_request"),
        "inference_level": str(item.get("inference_level") or "literal"),
        "thread_id": str(item.get("thread_id") or ""),
        "thread_action": str(item.get("thread_action") or ""),
        "thread_traversal_index": int(item.get("thread_traversal_index") or 0),
        "dependency_thread_id": str(item.get("dependency_thread_id") or ""),
        "answer_act": str(item.get("answer_act") or "direct_conversation_answer"),
        "epistemic_basis": str(item.get("epistemic_basis") or "current_turn_conversation"),
        "responsible_owner": str(item.get("responsible_owner") or "ordinary_conversation_path"),
        "answer_domain": str(item.get("answer_domain") or "ordinary_conversation"),
        "external_evidence_required": item.get("external_evidence_required") is True,
        "completion_policy": str(
            item.get("completion_policy")
            or "owner_may_complete_from_current_turn_support"
        ),
        "requested_response_functions": _text_list(
            item.get("requested_response_functions"), limit=8
        ),
        "role_fit_required": item.get("role_fit_required") is True,
        "answer_ownership_classified": item.get("answer_ownership_classified") is True,
        "canonical_index": int(item.get("canonical_index") or 0),
        "canonical": item.get("canonical") is True,
        "source_span": (
            dict(item.get("source_span"))
            if isinstance(item.get("source_span"), dict)
            else {"start": -1, "end": -1}
        ),
        "condition": (
            dict(item.get("condition"))
            if isinstance(item.get("condition"), dict)
            else {"present": False}
        ),
        "requested_count": int(item.get("requested_count") or 0),
        "response_shape": (
            dict(item.get("response_shape"))
            if isinstance(item.get("response_shape"), dict)
            else {"explicit": False}
        ),
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
