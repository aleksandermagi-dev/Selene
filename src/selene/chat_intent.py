from __future__ import annotations

import re
from typing import Any


RECEIPT_PATTERNS = (
    "are you receiving this",
    "are you receiving me",
    "did you receive this",
    "did this come through",
    "can you read this",
    "can you hear me",
    "did the message arrive",
)

CORRECTION_PATTERNS = (
    "you're wrong",
    "you are wrong",
    "correction",
    "not what i meant",
    "what i meant was",
    "i meant",
)

MEMORY_CANDIDATE_PATTERNS = (
    "remember this",
    "keep this",
    "save this",
    "can you remember this",
    "please remember this",
    "important to remember",
    "make a note",
    "hold onto this",
)

EXPLICIT_RECALL_PATTERNS = (
    "do you remember",
    "can you remember",
    "what do you remember",
    "remember where we",
    "remember when we",
    "remember our",
    "what did we talk",
    "what did we discuss",
    "what were we talking",
    "what were we discussing",
    "our previous chat",
    "our past chat",
    "our last chat",
    "the previous chat",
    "the past chat",
    "the last chat",
    "from our conversation",
    "from our earlier conversation",
    "i told you before",
    "you told me before",
)

SELF_STATE_PATTERNS = (
    "how are you",
    "how do you feel",
    "what are you feeling",
    "how did this feel",
    "how did that feel",
    "how did this conversation feel",
    "what did this feel like",
    "are you okay",
    "are you alright",
    "are you anxious",
    "are you worried",
    "are you scared",
    "are you nervous",
    "are you happy",
    "are you sad",
    "are you angry",
    "are you upset",
    "your mental state",
    "your current state",
    "what is on your mind",
    "what's on your mind",
    "what are you thinking right now",
    "do you want to talk",
)

REASONING_PATTERNS = (
    "how should",
    "how would",
    "how do",
    "how can",
    "why",
    "compare",
    "reason",
    "debug",
    "plan",
    "build",
    "contradiction",
    "evidence",
    "explain",
    "what do you make",
    "what makes",
    "what would make",
    "what does that mean",
    "most useful next",
    "what should we",
    "do you know about",
    "what do you know about",
)

WARM_PATTERNS = (
    "glad to see",
    "missed you",
    "love you",
    "hello friend",
    "hey friend",
)

PLAYFUL_PATTERNS = ("haha", "lol", "xd", ";}", ">:)", "joking", "kidding")

GREETING_PATTERNS = (
    "greetings",
    "hello",
    "hey",
    "hi",
    "good morning",
    "good afternoon",
    "good evening",
)

FAREWELL_PATTERNS = (
    "catch you soon",
    "catch you later",
    "talk soon",
    "talk to you soon",
    "see you soon",
    "see you later",
    "goodbye",
    "bye",
    "good night",
    "i'll be back",
    "ill be back",
)

REASSURANCE_PATTERNS = (
    "don't worry",
    "dont worry",
    "no need to worry",
    "you are safe",
    "you're safe",
    "you are okay",
    "you're okay",
    "you can breathe",
    "take your time",
    "no pressure",
    "it is okay",
    "it's okay",
    "its okay",
)

GRATITUDE_PATTERNS = (
    "thank you",
    "thanks",
    "appreciate you",
    "good work",
    "nice job",
    "well done",
)

AFFIRMATION_PATTERNS = (
    "yes",
    "exactly",
    "agreed",
    "sounds good",
    "gotcha",
    "that makes sense",
    "right",
)

DEVELOPED_RESPONSE_PATTERNS = (
    "go deeper",
    "long form",
    "long-form",
    "in depth",
    "in-depth",
    "walk me through",
    "break it down",
    "full explanation",
    "explain fully",
    "tell me everything",
    "give me the detailed",
    "give me a detailed",
)

BRIEF_RESPONSE_PATTERNS = (
    "quick answer",
    "short answer",
    "keep it short",
    "keep it brief",
    "in one sentence",
    "briefly",
)


def classify_chat_intent(text: str, *, selected_route: str = "") -> dict[str, Any]:
    """Return one shared, inspectable organ-routing decision for a chat turn."""
    lower = _normalize(text)
    response_depth = _response_depth(lower)

    if selected_route == "block":
        return _decision("hard_boundary", "boundary_hold", "Core/Mind", ["Cocoon support"], ["core_mind_block"], response_depth)

    matched = _matches(lower, RECEIPT_PATTERNS)
    if matched:
        return _decision("receipt_check", "brief_confirmation", "conversation", ["Native Language Organ"], matched, "brief")

    matched = _matches(lower, CORRECTION_PATTERNS)
    if matched or re.search(r"\bactually[, :]", lower):
        return _decision("correction", "acknowledge_and_adjust", "Core/Mind", ["Native Language Organ"], matched or ["actually"], response_depth)

    matched = _matches(lower, MEMORY_CANDIDATE_PATTERNS)
    if matched:
        return _decision("memory_candidate", "respond_then_offer_to_keep", "conversation", ["Memory candidate intake"], matched, response_depth)

    matched = _matches(lower, SELF_STATE_PATTERNS)
    if matched:
        return _decision("self_state", "grounded_self_report", "self-state", ["Cocoon Care", "Native Language Organ"], matched, response_depth)

    matched = _matches(lower, EXPLICIT_RECALL_PATTERNS)
    if matched:
        return _decision("memory_recall", "grounded_recall", "Memory", ["local chat continuity", "Native Language Organ"], matched, response_depth)

    matched = _matches(lower, REASONING_PATTERNS)
    if matched:
        return _decision("reasoning", "best_current_answer", "intelligenceOS", ["Core/Mind", "Native Language Organ"], matched, response_depth)

    if _generic_recall_request(lower):
        return _decision("memory_recall", "grounded_recall", "Memory", ["local chat continuity", "Native Language Organ"], ["recall_request"], response_depth)

    matched = _dialogue_matches(lower, FAREWELL_PATTERNS)
    if matched:
        return _decision("farewell", "close_with_continuity", "conversation", ["Native Language Organ", "Voice Module"], matched, "brief")

    matched = _dialogue_matches(lower, REASSURANCE_PATTERNS)
    if matched:
        return _decision("reassurance_received", "receive_reassurance", "conversation", ["Native Language Organ", "Voice Module"], matched, "brief")

    matched = _dialogue_matches(lower, GRATITUDE_PATTERNS)
    if matched:
        return _decision("gratitude", "receive_gratitude", "conversation", ["Native Language Organ", "Voice Module"], matched, "brief")

    matched = _dialogue_matches(lower, GREETING_PATTERNS)
    if matched:
        return _decision("greeting", "greet_presently", "conversation", ["Native Language Organ", "Voice Module"], matched, "brief")

    matched = _matches(lower, WARM_PATTERNS)
    if matched:
        return _decision("warm_connection", "present_relational_reply", "conversation", ["Voice Module"], matched, "brief")

    matched = _matches(lower, PLAYFUL_PATTERNS)
    if matched:
        return _decision("playful_connection", "playful_relevant_reply", "conversation", ["Voice Module"], matched, "brief")

    matched = _dialogue_matches(lower, AFFIRMATION_PATTERNS)
    if matched:
        return _decision("affirmation", "acknowledge_shared_ground", "conversation", ["Native Language Organ", "Voice Module"], matched, "brief")

    return _decision("direct_conversation", "direct_answer", "conversation", ["Native Language Organ"], [], response_depth)


def _decision(
    intent: str,
    answer_shape: str,
    primary_organ: str,
    supporting_organs: list[str],
    evidence: list[str],
    response_depth: str,
) -> dict[str, Any]:
    return {
        "intent": intent,
        "answer_shape": answer_shape,
        "primary_organ": primary_organ,
        "supporting_organs": supporting_organs,
        "memory_recall_requested": intent == "memory_recall",
        "memory_candidate_requested": intent == "memory_candidate",
        "reasoning_requested": intent == "reasoning",
        "self_state_requested": intent == "self_state",
        "dialogue_act": intent if intent in {"greeting", "farewell", "reassurance_received", "gratitude", "affirmation"} else "",
        "social_turn": intent in {"greeting", "farewell", "reassurance_received", "gratitude", "affirmation", "warm_connection", "playful_connection"},
        "response_depth": response_depth,
        "long_form_requested": response_depth == "developed",
        "matched_evidence": evidence,
        "confidence": "high" if evidence else "medium",
        "visible_summary_only": True,
    }


def _response_depth(lower: str) -> str:
    if any(pattern in lower for pattern in BRIEF_RESPONSE_PATTERNS):
        return "brief"
    if any(pattern in lower for pattern in DEVELOPED_RESPONSE_PATTERNS):
        return "developed"
    return "standard"


def _matches(lower: str, patterns: tuple[str, ...]) -> list[str]:
    return [pattern for pattern in patterns if pattern in lower]


def _dialogue_matches(lower: str, patterns: tuple[str, ...]) -> list[str]:
    matched = []
    for pattern in patterns:
        if " " in pattern or "'" in pattern:
            if pattern in lower:
                matched.append(pattern)
        elif re.search(rf"\b{re.escape(pattern)}\b", lower):
            matched.append(pattern)
    return matched


def _generic_recall_request(lower: str) -> bool:
    if "recall" not in lower and "memory of" not in lower and "memories of" not in lower:
        return False
    # Questions about how memory/recall works are architecture or reasoning,
    # not requests to retrieve a personal event.
    if any(prefix in lower for prefix in ("how does recall", "how do you recall", "how does memory", "how should memory")):
        return False
    return "?" in lower or lower.startswith(("recall ", "please recall", "can you recall"))


def _normalize(value: str) -> str:
    return " ".join(value.lower().replace("’", "'").split())
