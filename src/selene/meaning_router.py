from __future__ import annotations

import re
from typing import Any


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
    "repeat",
    "say this",
)


def interpret_turn_meaning(
    text: str,
    *,
    selected_route: str = "",
    requested_domain: str = "",
    source_packets_present: bool = False,
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
        re.match(r"^(please\s+)?(explain|compare|calculate|solve|check|find|show|tell|give|help|plan|review|summarize|describe)\b", routing_text)
    )

    dialogue_acts = _dialogue_acts(routing_text, tokens, question, explicit_request)
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
        "intent_candidates": intent_candidates,
        "primary_intent": primary_intent["intent"],
        "domain_candidates": domain_candidates,
        "selected_domain": primary_domain["domain"],
        "routing_confidence": primary_intent["confidence"],
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


def _dialogue_acts(routing_text: str, tokens: set[str], question: bool, explicit_request: bool) -> list[str]:
    acts: list[str] = []
    if _has_any(routing_text, ("actually", "correction", "i meant", "rather than", "not what i meant")):
        acts.append("correction")
    if _is_memory_candidate(routing_text):
        acts.append("memory_candidate")
    if _is_self_state_question(routing_text, question):
        acts.append("self_state_question")
    if _is_personal_recall(routing_text, question):
        acts.append("memory_recall")
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
    if _social_match(routing_text, "warm"):
        acts.append("warm_connection")
    if tokens.intersection({"haha", "lol", "xd", "joking", "kidding"}):
        acts.append("playful_connection")
    if not acts:
        acts.append("statement")
    return list(dict.fromkeys(acts))


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
        "design", "build", "debug", "meaning", "cause", "causes",
    }
    reasoning_hits = sorted(tokens.intersection(reasoning_terms))
    if reasoning_hits:
        add("reasoning", 55 + min(20, len(reasoning_hits) * 5), "reasoning_structure:" + ",".join(reasoning_hits[:5]))
    if question and tokens.intersection({"why", "how", "which"}):
        add("reasoning", 18, "open_question_shape")
    if _has_any(routing_text, ("what do you make of", "what makes", "what does that mean", "do you know about", "what do you know about")):
        add("reasoning", 70, "explanation_or_knowledge_request")
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
    elif _has_any(routing_text, ("cite", "citation", "sources", "source-backed", "research", "paper", "study", "literature")):
        add("source_backed_research", 62, "research_request_without_supplied_packet")
    if _has_any(routing_text, ("compare", "tradeoff", "trade-off", "pros and cons", "which option", "prioritize", "strategy", "plan")):
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
    if _has_any(routing_text, ("calculate", "arithmetic", "equation", "solve for", "square root", "multiply", "divide")):
        return True
    return bool(re.search(r"\b\d+(?:\.\d+)?\s*(?:\+|-|\*|/|=|%|\^|×|÷)\s*\d", raw))


def _is_memory_candidate(value: str) -> bool:
    if _has_any(value, ("where we", "when we", "what we", "our last", "our previous", "our past")):
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
            "previous chat",
            "past chat",
            "last chat",
            "earlier conversation",
        ),
    )
    if conversation_reference:
        return True
    past_anchor = _has_any(value, ("when we", "where we", "what we", "our last", "our previous", "our past", "i told you", "you told me", "before", "earlier"))
    recall_verb = bool(re.search(r"\b(remember|recall|memory of|memories of)\b", value))
    return recall_verb and (past_anchor or value.startswith(("do you remember", "what do you remember", "can you recall", "please recall")))


def _is_self_state_question(value: str, question: bool) -> bool:
    if not question:
        return False
    second_person = bool(re.search(r"\b(you|your)\b", value))
    state = bool(re.search(r"\b(feel|feeling|okay|alright|anxious|worried|scared|nervous|happy|sad|angry|upset|on your mind|thinking right now)\b", value))
    return second_person and state


def _is_receipt_check(value: str, question: bool) -> bool:
    return question and _has_any(value, ("receiving this", "receiving me", "come through", "read this", "hear me", "message arrive"))


def _social_match(value: str, kind: str) -> bool:
    patterns = {
        "greeting": ("greetings", "hello", "hey", "hi", "good morning", "good afternoon", "good evening"),
        "farewell": ("catch you", "talk soon", "see you", "goodbye", "bye", "good night", "i'll be back", "ill be back"),
        "reassurance": ("don't worry", "dont worry", "you are safe", "you're safe", "you can breathe", "take your time", "no pressure", "it's okay", "its okay"),
        "gratitude": ("thank you", "thanks", "appreciate you", "good work", "nice job", "well done"),
        "affirmation": ("exactly", "agreed", "sounds good", "gotcha", "that makes sense"),
        "warm": ("glad to see", "missed you", "love you", "hello friend", "hey friend"),
    }[kind]
    if kind == "greeting":
        return any(re.search(rf"(^|[.!?]\s*){re.escape(pattern)}\b", value) for pattern in patterns)
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
