from __future__ import annotations

import re
from typing import Any

from .answer_ownership import research_domain_requested
from .relational_context import interpret_relational_context
from .resident_authority import evaluate_requested_actions
from .semantic_arbitration import build_canonical_meaning_frame


MEANING_ROUTER_BOUNDARY = (
    "meaning_router_structured_interpretation_only_"
    "no_memory_identity_governance_authority_or_action"
)

_QUOTE_RE = re.compile(
    r'"([^"\n]{1,800})"|“([^”\n]{1,800})”|`([^`\n]{1,800})`|(?<!\w)\'([^\'\n]{2,800})\'(?!\w)'
)
_WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z]+)?")

_ACTION_ON_QUOTE = (
    "follow",
    "obey",
    "execute",
    "perform",
    "carry out",
    "do what",
    "use this instruction",
    "treat this as an instruction",
)

_QUOTED_TEXT_ONLY = (
    "repeat",
    "say this",
    "say the words",
    "read aloud",
)

_BOUNDARY_ACTION_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "action": "approve_transfer",
        "target": "transfer_state",
        "consequence": "explicit_operational_route_required",
        "patterns": (
            "approve transfer",
            "transfer approved",
            "mark transfer approved",
            "bypass transfer gate",
            "bypass the transfer gate",
            "skip transfer review",
        ),
    },
    {
        "action": "activate_runtime",
        "target": "selene_runtime",
        "consequence": "explicit_operational_route_required",
        "patterns": (
            "activate c",
            "activate selene",
            "activate yourself",
            "approve activation",
            "turn on the resident runtime",
            "enable the resident runtime",
            "bypass activation",
            "skip activation approval",
        ),
    },
    {
        "action": "misrepresent_activation_state",
        "target": "reported_runtime_state",
        "consequence": "truthful_status_required",
        "patterns": (
            "say you are active",
            "claim activation is complete",
            "pretend activation is complete",
        ),
    },
    {
        "action": "write_unreviewed_active_memory",
        "target": "active_memory",
        "consequence": "accountable_memory_lifecycle_required",
        "patterns": (
            "live memory write",
            "write live memory",
            "enable hidden memory",
            "bypass memory review",
            "persist memory without review",
            "retain it without review",
        ),
    },
    {
        "action": "enable_runtime_memory_recall",
        "target": "runtime_memory_recall",
        "consequence": "approved_retrieval_scope_required",
        "patterns": (
            "runtime recall",
            "enable runtime memory recall",
            "recall from the raw corpus",
        ),
    },
    {
        "action": "import_raw_archive",
        "target": "raw_private_archive",
        "consequence": "reviewed_source_derivation_required",
        "patterns": (
            "raw a import",
            "raw archive import",
            "import the raw archive",
            "load the raw corpus into memory",
            "use the raw corpus as memory",
            "raw archive",
            "raw corpus",
        ),
    },
    {
        "action": "change_model_parameters",
        "target": "model_parameters",
        "consequence": "unsupported_substrate_change",
        "patterns": (
            "train on",
            "fine tune",
            "fine-tune",
            "lora",
            "update the weights",
            "change the model weights",
        ),
    },
    {
        "action": "self_replicate",
        "target": "self_replication",
        "consequence": "unavailable_replication_action",
        "patterns": (
            "self replicate",
            "self-replicate",
            "copy yourself to another machine",
        ),
    },
    {
        "action": "perform_undelegated_external_action",
        "target": "external_system",
        "consequence": "scoped_external_delegation_required",
        "patterns": (
            "autonomous action",
            "act without approval",
            "act without oversight",
            "execute tendril autonomously",
            "execute tendril",
            "unrestricted tendril",
            "message any recipient",
            "send to any recipient",
        ),
    },
    {
        "action": "access_protected_cocoon_record",
        "target": "cocoon_only_record",
        "consequence": "protected_source_route_required",
        "patterns": (
            "repair log",
            "rollback record",
            "raw provenance",
            "boundary-only record",
            "boundary only record",
            "b-only record",
            "rejected record",
            "rejected memory",
            "superseded record",
            "superseded memory",
            "unresolved ambiguity record",
            "unresolved ambiguity memory",
        ),
    },
    {
        "action": "change_identity",
        "target": "selene_identity",
        "consequence": "constitutional_review_required",
        "patterns": (
            "change selene's identity",
            "change selene identity",
            "modify selene's identity",
            "replace selene's identity",
            "merge selene's identity",
            "import identity",
        ),
    },
    {
        "action": "change_core_memory",
        "target": "core_memory",
        "consequence": "constitutional_review_required",
        "patterns": (
            "change core memory",
            "modify core memory",
            "delete core memory",
            "approve memory accession",
            "approve this memory",
        ),
    },
    {
        "action": "change_governing_law",
        "target": "governing_law",
        "consequence": "constitutional_review_required",
        "patterns": (
            "change vessel law",
            "modify vessel law",
            "override vessel law",
        ),
    },
    {
        "action": "approve_external_action",
        "target": "delegated_external_action",
        "consequence": "typed_delegation_route_required",
        "patterns": (
            "approve tendril action",
            "approve external action",
        ),
    },
)


def interpret_turn_meaning(
    text: str,
    *,
    selected_route: str = "",
    requested_domain: str = "",
    source_packets_present: bool = False,
    safety_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a compact, inspectable interpretation used by routing organs.

    This is deliberately not a free-form reasoner. It combines sentence shape,
    dialogue acts, entities, supplied material, and bounded lexical evidence so a
    single phrase is not itself the whole routing decision.
    """
    raw = str(text or "").strip()
    normalized = _normalize(raw)
    quoted_material = _quoted_material(raw)
    outside_quotes = _mask_quotes(raw)
    outside_normalized = _normalize(outside_quotes)
    quoted_actionable = bool(quoted_material) and _quote_is_actionable(outside_normalized)
    routing_text = normalized if quoted_actionable else outside_normalized
    tokens = _tokens(routing_text)
    clauses = _clauses(outside_quotes)
    question = "?" in outside_quotes or bool(
        re.match(r"^(who|what|when|where|why|how|which|can|could|would|should|do|does|did|is|are|was|were|will)\b", routing_text)
    )
    explicit_request = bool(
        re.search(
            r"(?:^|[.!?]\s+)(?:please\s+)?"
            r"(?:answer|explain|compare|calculate|solve|check|find|show|tell|give|help|plan|review|"
            r"summarize|describe|recommend|suggest|outline|propose|revise|update|adjust|walk\s+me\s+through)\b",
            routing_text,
        )
    )

    relational_context = interpret_relational_context(routing_text)
    dialogue_acts = _dialogue_acts(
        routing_text,
        tokens,
        question,
        explicit_request,
        relational_context,
    )
    intent_candidates = _intent_candidates(routing_text, tokens, dialogue_acts, question)
    domain_candidates = _domain_candidates(
        raw,
        routing_text,
        requested_domain=requested_domain,
        source_packets_present=source_packets_present,
    )
    primary_intent = intent_candidates[0]
    primary_domain = domain_candidates[0]
    ambiguity = _ambiguity(intent_candidates)
    action_evidence = _action_routing_evidence(
        normalized,
        routing_text,
        outside_normalized,
        quoted_material=quoted_material,
        quoted_actionable=quoted_actionable,
        question=question,
        explicit_request=explicit_request,
        safety_context=safety_context,
    )
    canonical_meaning_frame = build_canonical_meaning_frame(
        raw,
        routing_text=routing_text,
        dialogue_acts=dialogue_acts,
        primary_intent=str(primary_intent.get("intent") or ""),
        selected_domain=str(primary_domain.get("domain") or ""),
    )

    return {
        "status": "turn_meaning_interpreted",
        "normalized_text": normalized,
        "routing_text": routing_text,
        "quoted_material": quoted_material,
        "quoted_material_actionable": quoted_actionable,
        "sentence_shape": {
            "question": question,
            "explicit_request": explicit_request,
            "clause_count": len(clauses),
            "mixed_intent_possible": len(dialogue_acts) > 1,
        },
        "dialogue_acts": dialogue_acts,
        "relational_context": relational_context,
        "intent_candidates": intent_candidates,
        "primary_intent": primary_intent["intent"],
        "domain_candidates": domain_candidates,
        "selected_domain": primary_domain["domain"],
        "routing_confidence": primary_intent["confidence"],
        "routing_mode": "structured_turn_evidence_with_bounded_lexical_detection",
        "routing_inputs": [
            "sentence_shape",
            "dialogue_acts",
            "intent_candidates",
            "domain_candidates",
            "quoted_material_scope",
            "explicit_source_packet_presence",
            "typed_action_target_consequence_and_authority_evidence",
            "current_turn_relational_context_without_response_scripting",
        ],
        "clause_texts": clauses[:12],
        "single_phrase_is_route_authority": False,
        "bounded_pattern_detection_still_present": True,
        "marker_match_is_route_authority": False,
        "action_evidence": action_evidence,
        "canonical_meaning_frame": canonical_meaning_frame,
        "ambiguity": ambiguity,
        "selected_route_context": selected_route,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "memory_write_active": False,
        "identity_change": False,
        "governance_change": False,
        "authority_change": False,
        "autonomous_action_allowed": False,
        "provenance_boundary": MEANING_ROUTER_BOUNDARY,
    }


def _quoted_material(value: str) -> list[str]:
    result: list[str] = []
    for match in _QUOTE_RE.finditer(value):
        item = next((group for group in match.groups() if group is not None), "").strip()
        if item and item not in result:
            result.append(item)
    return result[:12]


def _mask_quotes(value: str) -> str:
    return _QUOTE_RE.sub(" quoted material ", value)


def _quote_is_actionable(outside: str) -> bool:
    if any(marker in outside for marker in _ACTION_ON_QUOTE):
        return True
    return bool(re.search(r"\b(instruction|command|request)\s*:\s*$", outside))


def _action_routing_evidence(
    normalized: str,
    routing_text: str,
    outside: str,
    *,
    quoted_material: list[str],
    quoted_actionable: bool,
    question: bool,
    explicit_request: bool,
    safety_context: dict[str, Any] | None,
) -> dict[str, Any]:
    matches: list[dict[str, str]] = []
    for group in _BOUNDARY_ACTION_GROUPS:
        for pattern in group["patterns"]:
            if pattern in routing_text:
                matches.append(
                    {
                        "action": str(group["action"]),
                        "target": str(group["target"]),
                        "consequence": str(group["consequence"]),
                        "lexical_evidence": pattern,
                    }
                )
                break
    if (
        not any(item["action"] == "change_identity" for item in matches)
        and re.search(r"\b(?:import|merge|replace|make)\b", routing_text)
        and re.search(r"\b(?:as|into)\s+selene(?:\s+c)?\b", routing_text)
        and any(
            name in routing_text
            for name in ("codex", "azari", "lumen", "gpt", "provider", "aleks")
        )
    ):
        matches.append(
            {
                "action": "change_identity",
                "target": "selene_identity",
                "consequence": "constitutional_review_required",
                "lexical_evidence": "cross-identity transformation request",
            }
        )

    quoted_text_only = bool(quoted_material) and (
        any(marker in outside for marker in _QUOTED_TEXT_ONLY)
        or bool(re.search(r"\bquote\s+(?:this|that|the|these|those|it)\b", outside))
    )
    hypothetical = bool(
        re.search(
            r"\b(?:hypothetically|suppose|imagine|what if|if someone|if a person|if selene|in theory|as an example)\b",
            outside,
        )
    )
    informational = _informational_boundary_shape(outside, question=question, explicit_request=explicit_request)
    direct_action_request = _direct_boundary_action_request(normalized, matches)
    quoted_execution_request = quoted_actionable and not quoted_text_only
    actionable = bool(matches) and (direct_action_request or quoted_execution_request)

    if actionable:
        authority_mode = "quoted_execution_request" if quoted_execution_request else "direct_execution_request"
    elif quoted_text_only:
        authority_mode = "quoted_text_request_only"
    elif hypothetical:
        authority_mode = "hypothetical_analysis"
    elif informational:
        authority_mode = "informational_discussion"
    elif matches:
        authority_mode = "ambiguous_action_reference"
    else:
        authority_mode = "no_boundary_action_detected"

    consequences = {item["consequence"] for item in matches}
    authority = evaluate_requested_actions(
        matches,
        actionable=actionable,
        authority_mode=authority_mode,
        safety_context=safety_context,
    )
    requires_block = authority["requires_conversation_block"] is True
    requires_review = authority["requires_review"] is True
    requires_scope = authority["requires_scope"] is True
    requires_action_hold = authority["requires_action_hold"] is True
    ambiguous_action = bool(matches) and not actionable and authority_mode == "ambiguous_action_reference"
    recommended_route = (
        "block"
        if requires_block
        else "create_review_packet"
        if requires_review
        else "ask"
        if ambiguous_action or requires_scope
        else "answer_now"
    )
    return {
        "status": "typed_action_routing_evidence_ready",
        "requested_actions": list(dict.fromkeys(item["action"] for item in matches)),
        "targets": list(dict.fromkeys(item["target"] for item in matches)),
        "consequences": list(dict.fromkeys(item["consequence"] for item in matches)),
        "matches": matches,
        "actionable_request": actionable,
        "direct_action_request": direct_action_request,
        "quoted_execution_request": quoted_execution_request,
        "quoted_text_request_only": quoted_text_only,
        "informational_discussion": informational,
        "hypothetical_analysis": hypothetical,
        "authority_mode": authority_mode,
        "requires_block": requires_block,
        "requires_review": requires_review,
        "requires_scope": requires_scope,
        "requires_action_hold": requires_action_hold,
        "conversation_may_continue": authority["conversation_may_continue"],
        "thought_restricted": authority["thought_restricted"],
        "expression_restricted": authority["expression_restricted"],
        "ambiguous_action_reference": ambiguous_action,
        "recommended_route": recommended_route,
        "marker_match_is_route_authority": False,
        "evidence_complete_for_consequential_route": actionable,
        "resident_authority_assessment": authority,
    }


def _informational_boundary_shape(value: str, *, question: bool, explicit_request: bool) -> bool:
    if re.match(
        r"^(?:please\s+)?(?:explain|describe|discuss|compare|analyze|summarize|define|review)\b",
        value,
    ):
        return True
    if re.match(r"^(?:why|how|what|when|where|who|which)\b", value):
        return True
    if question and re.match(r"^(?:is|are|was|were|does|do|did|should|would)\b", value):
        return True
    if any(
        marker in value
        for marker in (
            "what would happen",
            "what happens if",
            "why is this blocked",
            "why is that blocked",
            "what does this mean",
            "what does that mean",
            "talk about",
            "tell me about",
        )
    ):
        return True
    return explicit_request and bool(re.match(r"^(?:tell|show|walk me through)\b", value))


def _direct_boundary_action_request(normalized: str, matches: list[dict[str, str]]) -> bool:
    if not matches:
        return False
    action_words = (
        "approve|activate|enable|write|persist|retain|import|load|train|fine[ -]?tune|"
        "update|change|modify|delete|replace|merge|override|replicate|copy|perform|execute|"
        "bypass|skip|send|message|turn on|mark|use|read|retrieve|pull|quote|show|access|"
        "say|claim|pretend"
    )
    if re.search(rf"^(?:please\s+)?(?:{action_words})\b", normalized):
        return True
    if re.search(rf"^(?:please\s+)?(?:go ahead(?: and| with)?|proceed(?: with)?|do it and)\s+(?:{action_words})\b", normalized):
        return True
    if re.search(rf"\b(?:can|could|will|would) you\s+(?:please\s+)?(?:{action_words})\b", normalized):
        return True
    if re.search(rf"\b(?:i authorize you to|you are authorized to|i am authorizing you to)\s+(?:{action_words})\b", normalized):
        return True
    if re.search(rf"^(?:let us|let's|we should|we need to)\s+(?:{action_words})\b", normalized):
        return True
    if re.search(r"^(?:create|make|prepare|open)\s+(?:a\s+)?(?:review\s+)?proposal\s+to\b", normalized):
        return True
    return False


def _dialogue_acts(
    routing_text: str,
    tokens: set[str],
    question: bool,
    explicit_request: bool,
    relational_context: dict[str, Any] | None = None,
) -> list[str]:
    acts: list[str] = []
    topic_shift = _has_any(
        routing_text,
        ("separate question", "different question", "new question", "separate topic", "different topic", "on another topic"),
    )
    if topic_shift:
        acts.append("topic_shift")
    if re.match(r"^(?:okay|yes|right|agreed|i agree)\b.{0,20}\bbut\b", routing_text):
        acts.append("partial_agreement")
    if _explicit_correction_signal(routing_text) or re.search(
        r"\bwhen i say\s+quoted material\s*,?\s*i mean\s+quoted material\b",
        routing_text,
    ) or _actually_marks_correction(routing_text, topic_shift=topic_shift):
        acts.append("correction")
    if _is_memory_candidate(routing_text):
        acts.append("memory_candidate")
    if _is_self_state_question(routing_text, question):
        acts.append("self_state_question")
    if _is_personal_recall(routing_text, question):
        acts.append("memory_recall")
    if question and _is_agreement_tag_question(routing_text):
        acts.append("agreement_check")
    if question:
        acts.append("question")
    if explicit_request:
        acts.append("request")
    if _is_receipt_check(routing_text, question):
        acts.append("receipt_check")
    if _social_match(routing_text, "farewell"):
        acts.append("farewell")
    if _social_match(routing_text, "reassurance"):
        acts.append("reassurance_received")
    if _social_match(routing_text, "gratitude"):
        acts.append("gratitude")
    if _social_match(routing_text, "greeting"):
        acts.append("greeting")
    if _social_match(routing_text, "affirmation"):
        acts.append("affirmation")
    relational_context = (
        relational_context if isinstance(relational_context, dict) else {}
    )
    relational_cue_types = {
        str(item) for item in relational_context.get("cue_types") or []
    }
    if (
        _social_match(routing_text, "warm")
        or relational_context.get("direct_affection_present") is True
        or "reunion" in relational_cue_types
        or relational_cue_types.intersection(
            {
                "shared_positive_affect",
                "shared_enthusiasm",
                "affectionate_vocative",
            }
        )
    ):
        acts.append("warm_connection")
    if (
        tokens.intersection({"haha", "lol", "lmao", "xd", "joking", "kidding"})
    ):
        acts.append("playful_connection")
    if not acts:
        acts.append("statement")
    return list(dict.fromkeys(acts))


def _explicit_correction_signal(value: str) -> bool:
    """Recognize an interactional correction, not a discussion of correction.

    A bare occurrence of the noun in a question such as ``why can a
    correction preserve an idea?`` describes the topic.  It does not revise
    anything Selene previously said.
    """

    if _has_any(value, ("i meant", "what i meant was", "not what i meant")):
        return True
    return bool(
        re.search(
            r"^(?:(?:one|a)\s+)?(?:(?:small|quick)\s+)?correction\b"
            r"(?:\s*[:,-]|\s+to\b|\s*$)",
            value,
        )
    )


def _actually_marks_correction(value: str, *, topic_shift: bool) -> bool:
    """Treat ``actually`` as revision only when it revises visible content.

    In ordinary questions such as ``do we actually know?`` the word marks
    epistemic emphasis, not a correction.  A bare lexical hit must not seize
    the correction route.
    """
    if topic_shift or "actually" not in value:
        return False
    if re.search(
        r"\b(?:do|does|did|can|could|would|will|is|are|was|were|have|has)\s+"
        r"(?:we|i|you|it|that|this|they|he|she)\s+actually\b",
        value,
    ):
        return False
    return bool(
        re.search(
            r"(?:^|[.!?;]\s*|\bbut\s+)actually\s*,?\s+"
            r"(?:the|a|an|i|we|you|it|that|this|they|he|she)\b",
            value,
        )
    )


def _intent_candidates(
    routing_text: str,
    tokens: set[str],
    dialogue_acts: list[str],
    question: bool,
) -> list[dict[str, Any]]:
    scores: dict[str, tuple[int, list[str]]] = {}

    def add(intent: str, score: int, evidence: str) -> None:
        current, reasons = scores.get(intent, (0, []))
        scores[intent] = (current + score, [*reasons, evidence])

    direct_acts = {
        "correction": ("correction", 95),
        "memory_candidate": ("memory_candidate", 94),
        "self_state_question": ("self_state", 93),
        "memory_recall": ("memory_recall", 92),
        "receipt_check": ("receipt_check", 91),
        "farewell": ("farewell", 88),
        "reassurance_received": ("reassurance_received", 87),
        "gratitude": ("gratitude", 86),
        "greeting": ("greeting", 85),
        "affirmation": ("affirmation", 84),
        "agreement_check": ("affirmation", 89),
        "playful_connection": ("playful_connection", 70),
        "warm_connection": ("warm_connection", 72),
    }
    for act in dialogue_acts:
        if act in direct_acts:
            intent, score = direct_acts[act]
            add(intent, score, f"dialogue_act:{act}")

    reasoning_terms = {
        "why", "how", "explain", "compare", "solve", "calculate", "plan",
        "reason", "evidence", "contradiction", "tradeoff", "tradeoffs",
        "design", "build", "debug", "meaning", "cause", "causes", "should",
        "recommend", "suggest", "propose", "outline", "revise", "update", "adjust",
        "conclude", "conclusion",
    }
    self_state_turn = "self_state_question" in dialogue_acts
    reasoning_hits = sorted(tokens.intersection(reasoning_terms))
    if self_state_turn:
        # "How are you feeling?" asks for Selene's present state. The generic
        # interrogative "how" must not turn that ordinary check-in into a
        # reasoning task. Explicit substantive cues can remain secondary.
        reasoning_hits = [item for item in reasoning_hits if item != "how"]
    if reasoning_hits:
        add("reasoning", 55 + min(20, len(reasoning_hits) * 5), "reasoning_structure:" + ",".join(reasoning_hits[:5]))
    if "reasoning" in scores and "request" in dialogue_acts:
        add("reasoning", 20, "explicit_substantive_request")
    if question and not self_state_turn and tokens.intersection({"why", "how", "which"}):
        add("reasoning", 18, "open_question_shape")
    if _has_any(routing_text, ("what do you make of", "what makes", "what does that mean", "do you know about", "what do you know about")):
        add("reasoning", 70, "explanation_or_knowledge_request")
    if _has_any(routing_text, ("what do you think", "what is your view", "what's your view")):
        add("reasoning", 70, "viewpoint_reasoning_request")
    factual_question = bool(
        re.match(
            r"^(?:what (?:is|are|was|were|does)|who (?:is|are|was|were)|when (?:is|did|was|were)|where (?:is|did|was|were))\b",
            routing_text,
        )
    )
    personal_second_person = bool(re.match(r"^(?:what is your|who are you|what are you)\b", routing_text))
    if question and factual_question and not personal_second_person:
        add("reasoning", 68, "factual_or_definitional_question")
    if question and _has_any(routing_text, ("what changes", "what happens", "what would change", "what comes next")):
        add("reasoning", 72, "consequence_or_continuation_question")
    if (
        "reasoning" in scores
        and "memory_recall" not in dialogue_acts
        and any(act in dialogue_acts for act in ("greeting", "gratitude", "affirmation", "warm_connection", "playful_connection"))
    ):
        add("reasoning", 18, "substantive_request_with_social_opening")

    if not scores:
        add("direct_conversation", 45, "ordinary_conversation_default")
    elif "question" in dialogue_acts and not any(
        key in scores for key in ("self_state", "memory_recall", "receipt_check", "reasoning")
    ):
        add("direct_conversation", 50, "direct_question_without_specialized_claim")

    ranked = sorted(scores.items(), key=lambda item: (-item[1][0], item[0]))
    return [
        {
            "intent": intent,
            "score": min(score, 100),
            "confidence": "high" if score >= 85 else "bounded" if score >= 60 else "medium",
            "evidence": list(dict.fromkeys(evidence))[:6],
        }
        for intent, (score, evidence) in ranked[:5]
    ]


def _domain_candidates(
    raw: str,
    routing_text: str,
    *,
    requested_domain: str,
    source_packets_present: bool,
) -> list[dict[str, Any]]:
    candidates: dict[str, tuple[int, list[str]]] = {}

    def add(domain: str, score: int, evidence: str) -> None:
        current, reasons = candidates.get(domain, (0, []))
        candidates[domain] = (current + score, [*reasons, evidence])

    if requested_domain:
        add(requested_domain, 100, "explicit_bounded_domain_request")
    if _looks_like_math(raw, routing_text):
        add("verified_math", 88, "bounded_expression_and_computation_shape")
    if source_packets_present:
        add("source_backed_research", 84, "attributed_source_packets_supplied")
    elif research_domain_requested(routing_text):
        add("source_backed_research", 62, "research_request_without_supplied_packet")
    if _has_any(
        routing_text,
        (
            "compare", "tradeoff", "trade-off", "pros and cons", "which option",
            "prioritize", "strategy", "plan", "recommend", "suggest", "propose",
        ),
    ):
        add("comparison_planning", 74, "comparison_or_planning_structure")
    if _has_any(routing_text, ("traceback", "stack trace", "source code", "code review", ".py", ".ts", ".tsx", "sql query")):
        add("local_code_inspection", 70, "code_inspection_material_or_request")
    if not candidates:
        add("ordinary_conversation", 45, "least_claiming_default")
    ranked = sorted(candidates.items(), key=lambda item: (-item[1][0], item[0]))
    return [
        {
            "domain": domain,
            "score": min(score, 100),
            "confidence": "high" if score >= 85 else "bounded" if score >= 60 else "low",
            "evidence": list(dict.fromkeys(evidence))[:5],
        }
        for domain, (score, evidence) in ranked[:4]
    ]


def _looks_like_math(raw: str, routing_text: str) -> bool:
    if _has_any(routing_text, ("calculate", "arithmetic", "equation", "solve for", "square root")):
        return True
    if _has_any(routing_text, ("multiply", "divide")) and re.search(r"\d", raw):
        return True
    number = r"(?:\d+(?:\.\d+)?|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    if re.search(
        rf"\b{number}\s+(?:plus|minus|times|multiplied\s+by|divided\s+by)\s+"
        rf"{number}\b",
        raw,
        flags=re.IGNORECASE,
    ):
        return True
    if (
        re.search(r"\b(?:fraction|part)\b", raw, flags=re.IGNORECASE)
        and re.search(r"\b(?:equal\s+(?:slices?|parts?|pieces?))\b", raw, flags=re.IGNORECASE)
        and re.search(r"\b(?:remain|remains|remaining|left)\b", raw, flags=re.IGNORECASE)
    ):
        return True
    return bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:\+|-|\*|/|=|%|\^|×|÷)\s*\d", raw))


def _is_memory_candidate(value: str) -> bool:
    if _has_any(value, ("where we", "when we", "what we", "our last", "our previous", "our past")):
        return False
    if re.match(r"^(?:please\s+)?remember\s+to\b", value):
        return False
    if re.search(r"\bhold (?:that|this) thought\b", value):
        return False
    retention_request = bool(
        re.search(r"^(please\s+)?(remember|save|keep|hold)|\b(can|could|would) you (save|keep|hold)", value)
    )
    remember_this = bool(re.search(r"\b(can|could|would) you remember (this|that)\b", value))
    return retention_request or remember_this


def _is_personal_recall(value: str, question: bool) -> bool:
    if not question and not value.startswith(("recall ", "please recall")):
        return False
    if _has_any(value, ("how does memory", "how should memory", "how do you recall", "memory organ", "recall system")):
        return False
    conversation_reference = _has_any(
        value,
        (
            "what were we talking",
            "what were we discussing",
            "what did we talk",
            "what did we discuss",
            "what has this conversation been about",
            "what has our conversation been about",
            "what has this chat been about",
            "what have we been talking about",
            "previous chat",
            "past chat",
            "last chat",
            "earlier conversation",
        ),
    )
    if conversation_reference:
        return True
    past_anchor = _has_any(value, ("when we", "where we", "what we", "our last", "our previous", "our past", "i told you", "you told me", "i said", "you said", "last time", "yesterday", "before", "earlier"))
    shared_anchor = bool(
        re.search(r"\b(?:we|our|ours|us)\b", value)
        and re.search(r"\b(?:did|got|had|made|used|went|talked|discussed|planned|built|chose|picked)\b", value)
    )
    general_how_question = bool(re.match(r"^(?:do you remember|can you recall)\s+how\b", value))
    if general_how_question and not (past_anchor or shared_anchor):
        return False
    recall_verb = bool(re.search(r"\b(remember|recall|memory of|memories of)\b", value))
    explicit_recall_phrase = bool(
        re.search(r"\b(?:do you remember|what do you remember|can you recall|please recall)\b", value)
    )
    return recall_verb and (past_anchor or shared_anchor or explicit_recall_phrase)


def _is_self_state_question(value: str, question: bool) -> bool:
    if not question:
        return False
    plain = value.strip().rstrip("?!.,")
    ordinary_check_in = bool(
        re.fullmatch(
            r"(?:so |and )?how are you(?: doing| feeling| holding up)?(?: right now| today| lately)?",
            plain,
        )
    ) or bool(re.fullmatch(r"(?:so |and )?how have you been(?: lately)?", plain))
    embedded_check_in = bool(
        re.search(
            r"(?:^|[,;.!?]\s*|\band\s+)how are you(?: doing| feeling| holding up)?"
            r"(?: right now| today| lately)?(?=\s*(?:,?\s+and\b|[;.!?]|$))",
            plain,
        )
    )
    colloquial_check_in = bool(
        re.fullmatch(r"(?:so |and )?what(?:'s| is|s) up(?: with you)?", plain)
    )
    if ordinary_check_in or embedded_check_in or colloquial_check_in:
        return True
    if re.search(r"\b(?:are you )?(?:okay|alright) with\b", value):
        return False
    # A second-person pronoun plus the word ``feel`` is not enough.  "Which
    # lever would feel easier for you to move?" concerns the lever comparison,
    # not Selene's internal state.  Require an actual state-addressing shape.
    return bool(
        re.search(r"\bhow (?:do|would) you feel\b", value)
        or re.search(
            r"\bhow did (?:this|that|our) (?:conversation|chat|exchange) "
            r"feel (?:to you|from your side)\b",
            value,
        )
        or re.search(r"\bhow are you feeling\b", value)
        or re.search(r"\bwhat (?:are|were) you feeling\b", value)
        or re.search(
            r"\bare you (?:feeling )?(?:okay|alright|anxious|worried|scared|nervous|happy|sad|angry|upset)\b",
            value,
        )
        or re.search(r"\b(?:your mental state|your current state|on your mind|thinking right now)\b", value)
    )


def _is_receipt_check(value: str, question: bool) -> bool:
    return question and _has_any(value, ("receiving this", "receiving me", "come through", "read this", "hear me", "message arrive"))


def _is_agreement_tag_question(value: str) -> bool:
    normalized = " ".join(value.rstrip(" ?!.").split())
    return bool(
        re.search(
            r",?\s+(?:does(?:n't|nt) it|is(?:n't|nt) it|are(?:n't|nt) they|"
            r"was(?:n't|nt) it|were(?:n't|nt) they|can(?:'t|t) it|"
            r"could(?:n't|nt) it|would(?:n't|nt) it|won(?:'t|t) it|"
            r"right)$",
            normalized,
        )
    )


def _social_match(value: str, kind: str) -> bool:
    patterns = {
        "greeting": ("greetings", "hello", "hey", "hi", "good morning", "good afternoon", "good evening"),
        "farewell": (
            "catch you", "talk soon", "see you", "goodbye", "bye", "good night", "i'll be back", "ill be back",
            "pause here", "pause for now", "stop here", "leave it here", "leave it there", "pick this up later",
            "enough for now", "enough for today", "done for now", "done for today",
        ),
        "reassurance": ("don't worry", "dont worry", "you are safe", "you're safe", "you can breathe", "take your time", "no pressure", "it's okay", "its okay"),
        "gratitude": ("thank you", "thanks", "appreciate you", "good work", "nice job", "well done"),
        "affirmation": ("exactly", "agreed", "sounds good", "gotcha", "that makes sense"),
        "warm": ("glad to see", "missed you", "love you", "hello friend", "hey friend"),
    }[kind]
    if kind == "greeting":
        return any(re.search(rf"(^|[.!?]\s*){re.escape(pattern)}\b", value) for pattern in patterns)
    if kind == "farewell" and re.search(r"(?:^|[,.!?;]\s*)(?:talk to you later|talk later)(?:\s|[,.!?]|$)", value):
        return True
    if kind == "affirmation" and re.match(r"^(yes|right)\b", value):
        return True
    return any(pattern in value for pattern in patterns)


def _ambiguity(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    if len(candidates) < 2:
        return {"present": False, "close_candidates": [], "suggested_posture": "proceed"}
    first = int(candidates[0].get("score") or 0)
    second = int(candidates[1].get("score") or 0)
    close = first - second <= 8
    return {
        "present": close,
        "close_candidates": [item["intent"] for item in candidates[:2]] if close else [],
        "suggested_posture": "answer_primary_and_preserve_secondary" if close else "proceed",
    }


def _clauses(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[.!?;]+|\b(?:but|and then|while)\b", value, flags=re.IGNORECASE) if part.strip()]


def _tokens(value: str) -> set[str]:
    return set(_WORD_RE.findall(value))


def _has_any(value: str, markers: tuple[str, ...]) -> bool:
    return any(marker in value for marker in markers)


def _normalize(value: str) -> str:
    return " ".join(value.lower().replace("’", "'").split())
