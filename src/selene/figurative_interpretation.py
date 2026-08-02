from __future__ import annotations

import re
from typing import Any

from .registry import truncate


FIGURATIVE_INTERPRETATION_BOUNDARY = (
    "session_scoped_meaning_support_no_identity_personality_memory_or_authority_change"
)

_GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "session_scoped_only": True,
    "durable_memory_write": False,
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "hidden_chain_of_thought_exposed": False,
}

_IDIOMS: tuple[tuple[str, str], ...] = (
    ("sardine can", "feel cramped or overcrowded, with too little comfortable room to move"),
    ("beat a dead horse", "keep pushing a settled or unproductive topic"),
    ("beating a dead horse", "keep pushing a settled or unproductive topic"),
    ("walk on eggshells", "act with excessive caution from fear of causing a problem"),
    ("walking on eggshells", "act with excessive caution from fear of causing a problem"),
    ("step on eggshells", "act with excessive caution from fear of causing a problem"),
    ("stepping on eggshells", "act with excessive caution from fear of causing a problem"),
    ("shoot the shit", "chat casually"),
    ("piece of cake", "very easy"),
    ("break the ice", "ease the initial social tension"),
    ("hit the nail on the head", "identify the point accurately"),
    ("back to the drawing board", "revise or restart the plan"),
)

_TASK_PACING_CUES = (
    "explain",
    "one step",
    "step at a time",
    "too fast",
    "conversation",
    "talking",
    "answer",
    "detail",
    "pace",
    "go through",
)
_PHYSICAL_PACING_CUES = (
    "car",
    "drive",
    "driving",
    "road",
    "vehicle",
    "walking",
    "running",
    "speed limit",
    "miles per hour",
    "mph",
)
_WEATHER_CUES = (
    "weather",
    "rain",
    "thunder",
    "lightning",
    "wind",
    "radar",
    "power",
    "outside",
)
_NON_WEATHER_CUES = (
    "argument",
    "crisis",
    "rough patch",
    "emotion",
    "tension",
    "problem",
    "work",
    "phase",
)


def interpret_figurative_language(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return an inspectable, conservative interpretation of one visible utterance.

    This is a session-scoped language aid. It never stores a speaker profile,
    changes identity or personality, or treats figurative similarity as literal
    equivalence.
    """

    payload = payload or {}
    text = truncate(str(payload.get("text") or payload.get("prompt") or ""), 2400).strip()
    if not text:
        raise ValueError("text is required")
    context = payload.get("conversation_context") if isinstance(payload.get("conversation_context"), dict) else {}
    previous = payload.get("previous_interpretation") if isinstance(payload.get("previous_interpretation"), dict) else {}
    context_text = _context_text(context)
    lower = text.lower()

    correction = _interpretation_correction(text, previous)
    if correction:
        return _packet(
            text,
            interpreted_text=text,
            detected_forms=["interpretation_correction"],
            candidates=correction["candidates"],
            selected_reading=correction["selected_reading"],
            intended_meaning=correction["intended_meaning"],
            confidence="high",
            contextual_cues=correction["cues"],
            materially_changes_response=True,
            interpretation_update=correction["update"],
        )

    matches: list[dict[str, Any]] = []
    interpreted = text
    for phrase, meaning in _IDIOMS:
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        if not pattern.search(text):
            continue
        interpreted = pattern.sub(meaning, interpreted)
        matches.append(
            {
                "form": "idiom",
                "surface": phrase,
                "meaning": meaning,
                "confidence": "high",
                "cues": ["reviewed_conventional_idiom"],
            }
        )

    if re.search(r"\bslow down\b", lower):
        task_cues = [cue for cue in _TASK_PACING_CUES if cue in f"{lower} {context_text}"]
        physical_cues = [cue for cue in _PHYSICAL_PACING_CUES if cue in f"{lower} {context_text}"]
        if task_cues and not physical_cues:
            meaning = "reduce the conversational pace or information density"
            interpreted = re.sub(r"\bslow down\b", meaning, interpreted, flags=re.IGNORECASE)
            matches.append(
                {
                    "form": "contextual_figure_of_speech",
                    "surface": "slow down",
                    "meaning": meaning,
                    "confidence": "bounded",
                    "cues": task_cues[:4],
                }
            )
        elif physical_cues:
            matches.append(
                {
                    "form": "literal_expression",
                    "surface": "slow down",
                    "meaning": "reduce physical speed",
                    "confidence": "bounded",
                    "cues": physical_cues[:4],
                }
            )

    society_metaphor = _emergent_society_metaphor(text)
    if society_metaphor:
        matches.append(society_metaphor)
        interpreted = society_metaphor["meaning"]

    analogy = (
        {}
        if society_metaphor or any(item.get("form") == "idiom" for item in matches)
        else _analogy(text)
    )
    if analogy:
        matches.append(analogy)

    quoted_figure = _quoted_figure_request(text)
    if quoted_figure:
        matches.append(quoted_figure)
        interpreted = _replace_quoted_expression(
            interpreted,
            str(quoted_figure.get("meaning") or ""),
        )

    explicit = _explicit_nonliteral(text)
    if explicit:
        matches.append(explicit)

    sarcasm = _sarcasm(text, context_text)
    if sarcasm:
        matches.append(sarcasm)

    storm = _storm_reading(text, context_text)
    if storm:
        if storm.get("selected"):
            matches.append(storm)
        else:
            return _packet(
                text,
                interpreted_text=text,
                detected_forms=["literal_or_metaphorical"],
                candidates=storm["candidates"],
                selected_reading="unresolved",
                intended_meaning="",
                confidence="unresolved",
                contextual_cues=[],
                materially_changes_response=_material_request(text),
                clarification_required=_material_request(text),
                clarification_question=(
                    "Do you mean the weather passed, or that a difficult situation settled down?"
                    if _material_request(text)
                    else ""
                ),
            )

    selected = [item for item in matches if item.get("form") != "literal_expression"]
    if not selected:
        return _packet(
            text,
            interpreted_text=text,
            detected_forms=[],
            candidates=[
                {
                    "reading_type": "literal",
                    "meaning": text,
                    "confidence": "bounded",
                    "evidence": ["no_supported_nonliteral_reading_selected"],
                }
            ],
            selected_reading="literal",
            intended_meaning=text,
            confidence="bounded",
            contextual_cues=[],
            materially_changes_response=False,
        )

    intended = "; ".join(str(item.get("meaning") or "") for item in selected if item.get("meaning"))
    candidates = [
        {
            "reading_type": "literal",
            "meaning": text,
            "confidence": "possible",
            "evidence": ["original_words_preserved"],
        },
        {
            "reading_type": "figurative",
            "meaning": intended,
            "confidence": _lowest_confidence(selected),
            "evidence": _unique(
                cue
                for item in selected
                for cue in item.get("cues") or []
            ),
        },
    ]
    return _packet(
        text,
        interpreted_text=interpreted,
        detected_forms=_unique(str(item.get("form") or "") for item in selected),
        candidates=candidates,
        selected_reading="figurative",
        intended_meaning=intended,
        confidence=_lowest_confidence(selected),
        contextual_cues=candidates[-1]["evidence"],
        materially_changes_response=interpreted != text,
        analogy_mapping=analogy or {},
    )


def _packet(
    original_text: str,
    *,
    interpreted_text: str,
    detected_forms: list[str],
    candidates: list[dict[str, Any]],
    selected_reading: str,
    intended_meaning: str,
    confidence: str,
    contextual_cues: list[str],
    materially_changes_response: bool,
    clarification_required: bool = False,
    clarification_question: str = "",
    analogy_mapping: dict[str, Any] | None = None,
    interpretation_update: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": "figurative_interpretation_ready",
        "version": "v1_contextual_literal_and_nonliteral_candidates",
        "original_text": original_text,
        "literal_reading": original_text,
        "interpreted_text": interpreted_text,
        "detected_forms": detected_forms,
        "candidate_meanings": candidates,
        "selected_reading": selected_reading,
        "intended_meaning": intended_meaning,
        "confidence": confidence,
        "contextual_cues": contextual_cues,
        "materially_changes_response": materially_changes_response,
        "clarification_required": clarification_required,
        "clarification_question": clarification_question,
        "analogy_mapping": analogy_mapping or {},
        "analogy_is_equivalence": False,
        "interpretation_update": interpretation_update or {},
        "original_words_preserved": True,
        "provenance_boundary": FIGURATIVE_INTERPRETATION_BOUNDARY,
        **_GUARDS,
    }


def _analogy(text: str) -> dict[str, Any]:
    # "I'd like to ..." is an ordinary desiderative, not a similarity claim.
    # Keep the exclusion local to leading ``like`` so genuine ``X is like Y``
    # comparisons remain available to the interpretation layer.
    analogy_text = re.sub(
        r"\b(?:i|we|you|they|he|she)\s*(?:'d| would)?\s+like\s+to\b",
        " ",
        text,
        flags=re.IGNORECASE,
    )
    explicit = re.search(
        r"\b(?:like|similar to|an analogy(?: between| for)?)\s+(.+?)\s+(?:and|to|is like)\s+(.+?)(?:[.!?]|$)",
        analogy_text,
        flags=re.IGNORECASE,
    )
    simile = re.search(
        r"\b(.+?)\s+(?:is|works|feels|acts)\s+like\s+(.+?)(?:[.!?]|$)",
        analogy_text,
        flags=re.IGNORECASE,
    )
    match = simile or explicit
    if not match:
        return {}
    source = truncate(match.group(2).strip() if simile else match.group(1).strip(), 300)
    target = truncate(match.group(1).strip() if simile else match.group(2).strip(), 300)
    return {
        "form": "analogy",
        "surface": truncate(match.group(0).strip(), 500),
        "meaning": f"compare the relationship or structure of {source} with {target}",
        "confidence": "bounded",
        "cues": ["explicit_similarity_marker"],
        "source_domain": source,
        "target_domain": target,
        "mapped_relationship": "similarity is proposed for the relevant relationship or structure",
        "mapping_limit": "unmapped properties are not carried across",
        "equivalence_claimed": False,
    }


def _quoted_figure_request(text: str) -> dict[str, Any]:
    quoted = re.search(r"[\"“'](.+?)[\"”']", text)
    interpretation_request = re.search(
        r"\b(?:what do i mean|what does (?:that|this|it) mean|"
        r"how do you (?:read|interpret|understand) (?:that|this|it)|"
        r"how would you (?:read|interpret|understand) (?:that|this|it))\b",
        text,
        flags=re.IGNORECASE,
    )
    if not quoted or not interpretation_request:
        return {}
    surface = quoted.group(1).strip()
    lower = surface.lower()
    meaning = ""
    form = "metaphor"
    cues = ["speaker_requested_meaning_of_quoted_expression"]
    if (
        re.search(r"\b(?:lay|build|make|put|set)\w*\b.*\b(?:track|foundation|road|bridge)\w*\b", lower)
        and re.search(r"\bbefore\b.*\b(?:driv|use|cross|travel|run)\w*\b", lower)
    ):
        meaning = "establish the needed foundation or prerequisites before trying to use what depends on them"
        cues.append("visible_sequence_mapping")
    elif re.search(r"\bbefore\b", lower):
        first, second = re.split(r"\bbefore\b", surface, maxsplit=1, flags=re.IGNORECASE)
        meaning = (
            f"the first activity, {first.strip()}, supplies or protects something needed before "
            f"the later activity, {second.strip()}"
        )
        cues.append("visible_sequence_mapping")
    else:
        personification = re.match(
            r"^(?:the\s+)?(.+?)\s+(?:is|was|keeps)\s+(?:being\s+)?"
            r"(dramatic|stubborn|grumpy|angry|happy|sulking|complaining|temperamental)\b",
            surface,
            flags=re.IGNORECASE,
        )
        if not personification:
            personification = re.search(
                r"\b(?:i|we)\s+say\s+(?:the\s+)?([a-z][a-z0-9 _-]{0,50}?)\s+"
                r"(?:is|was|keeps)\s+"
                r"[\"“'](?:being\s+)?"
                r"(dramatic|stubborn|grumpy|angry|happy|sulking|complaining|temperamental)"
                r"[,;:!?]?[\"”']",
                text,
                flags=re.IGNORECASE,
            )
        if personification:
            subject = personification.group(1).strip()
            quality = personification.group(2).lower()
            meaning = (
                f"{subject} is being personified: '{quality}' describes how its behavior seems "
                "exaggerated, troublesome, or attention-demanding, not a literal emotional state"
            )
            form = "personification"
            cues.append("nonhuman_subject_given_human_quality")
    if not meaning:
        return {}
    return {
        "form": form,
        "surface": surface,
        "meaning": meaning,
        "confidence": "bounded",
        "cues": cues,
    }


def _replace_quoted_expression(text: str, meaning: str) -> str:
    if not meaning:
        return text
    return re.sub(
        r"[\"“'](.+?)[\"”']",
        meaning,
        text,
        count=1,
    )


def _explicit_nonliteral(text: str) -> dict[str, Any]:
    lower = text.lower()
    if any(marker in lower for marker in ("metaphorically", "as a metaphor", "figure of speech")):
        return {
            "form": "metaphor",
            "surface": text,
            "meaning": "use the stated comparison nonliterally",
            "confidence": "high",
            "cues": ["explicit_nonliteral_marker"],
        }
    if any(marker in lower for marker in ("i'm exaggerating", "i am exaggerating", "that is hyperbole", "that's hyperbole")):
        return {
            "form": "hyperbole",
            "surface": text,
            "meaning": "treat the magnitude as emphasis rather than an exact measurement",
            "confidence": "high",
            "cues": ["explicit_exaggeration_marker"],
        }
    if any(marker in lower for marker in ("i'm understating", "i am understating", "that is an understatement", "that's an understatement")):
        return {
            "form": "understatement",
            "surface": text,
            "meaning": "treat the wording as deliberately milder than the situation",
            "confidence": "high",
            "cues": ["explicit_understatement_marker"],
        }
    return {}


def _emergent_society_metaphor(text: str) -> dict[str, Any]:
    match = re.search(
        r"\b(?:the\s+)?(?P<subject>[a-z][a-z0-9 _-]{1,80}?)\s+"
        r"(?:looks?|seems?)\s+like\s+(?:it\s+)?(?:has\s+)?"
        r"(?:founded|formed|declared|started)\s+(?:a\s+)?(?:tiny\s+|little\s+)?"
        r"(?:republic|nation|kingdom|society|government)\b",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return {}
    subject = match.group("subject").strip()
    return {
        "form": "personification",
        "surface": truncate(match.group(0).strip(), 500),
        "meaning": (
            f"the {subject} has become numerous, tangled, or self-organized enough "
            "to jokingly resemble a small society with a life of its own"
        ),
        "confidence": "bounded",
        "cues": ["nonhuman_group_given_social_agency", "playful_exaggeration"],
    }


def _sarcasm(text: str, context_text: str) -> dict[str, Any]:
    lower = text.lower()
    explicit = "/s" in lower or any(
        marker in lower
        for marker in ("i'm being sarcastic", "i am being sarcastic", "that was sarcasm", "sarcastically")
    )
    contradiction = any(
        marker in lower
        for marker in (
            "great, another",
            "just what i needed",
            "what a wonderful failure",
            "love that for me",
            "wonderfully convenient",
            "very convenient",
        )
    )
    adverse_context = any(
        marker in f"{lower} {context_text}"
        for marker in (
            "broke", "failed", "crashed", "problem", "storm", "lost", "wrong",
            "power went out", "power goes out", "outage", "interrupted",
        )
    )
    if not explicit and not (contradiction and adverse_context):
        return {}
    return {
        "form": "sarcasm",
        "surface": text,
        "meaning": "the approving surface wording likely communicates criticism, frustration, or the opposite evaluation",
        "confidence": "high" if explicit else "provisional",
        "cues": ["explicit_sarcasm_marker"] if explicit else ["surface_context_contradiction", "adverse_visible_context"],
    }


def _storm_reading(text: str, context_text: str) -> dict[str, Any]:
    if not re.search(r"\b(?:the\s+)?storm (?:has )?passed\b", text, flags=re.IGNORECASE):
        return {}
    joined = f"{text.lower()} {context_text}"
    weather = [cue for cue in _WEATHER_CUES if cue in joined]
    non_weather = [cue for cue in _NON_WEATHER_CUES if cue in joined]
    if weather and not non_weather:
        return {
            "form": "literal_expression",
            "surface": "storm passed",
            "meaning": "the weather event moved away or ended",
            "confidence": "bounded",
            "cues": weather[:4],
            "selected": True,
        }
    if non_weather and not weather:
        return {
            "form": "metaphor",
            "surface": "storm passed",
            "meaning": "the difficult or turbulent situation settled down",
            "confidence": "bounded",
            "cues": non_weather[:4],
            "selected": True,
        }
    return {
        "selected": False,
        "candidates": [
            {
                "reading_type": "literal",
                "meaning": "the weather event moved away or ended",
                "confidence": "possible",
                "evidence": [],
            },
            {
                "reading_type": "figurative",
                "meaning": "the difficult or turbulent situation settled down",
                "confidence": "possible",
                "evidence": [],
            },
        ],
    }


def _interpretation_correction(text: str, previous: dict[str, Any]) -> dict[str, Any]:
    lower = text.lower()
    if not previous:
        return {}
    literal = bool(
        re.search(
            r"\b(?:i meant(?: that| it)?|that was|i was speaking) (?:it )?literally\b",
            lower,
        )
    )
    sarcastic = bool(re.search(r"\b(?:i was being sarcastic|that was sarcasm|i meant that sarcastically)\b", lower))
    metaphorical = bool(re.search(r"\b(?:that was|i meant it as) (?:a )?metaphor\b", lower))
    if not (literal or sarcastic or metaphorical):
        return {}
    selected = "literal" if literal else "figurative"
    intended = (
        str(previous.get("literal_reading") or previous.get("original_text") or "")
        if literal
        else "the prior wording was intended sarcastically"
        if sarcastic
        else "the prior wording was intended metaphorically"
    )
    form = "literal" if literal else "sarcasm" if sarcastic else "metaphor"
    return {
        "selected_reading": selected,
        "intended_meaning": intended,
        "cues": [f"explicit_{form}_correction"],
        "candidates": [
            {
                "reading_type": selected,
                "meaning": intended,
                "confidence": "high",
                "evidence": [f"speaker_explicitly_corrected_to_{form}"],
            }
        ],
        "update": {
            "detected": True,
            "kind": "figurative_interpretation_correction",
            "from_reading": str(previous.get("selected_reading") or "unresolved"),
            "to_reading": selected,
            "scope": "current_session_interpretation_only",
            "preserve_surrounding_conversation": True,
            "durable_memory_write": False,
        },
    }


def _context_text(context: dict[str, Any]) -> str:
    values = [
        str((context.get("previous_turn") or {}).get("preview") or ""),
        *[str(item) for item in context.get("recent_user_texts") or []],
        *[str(item) for item in context.get("recent_assistant_texts") or []],
    ]
    return " ".join(values).lower()


def _material_request(text: str) -> bool:
    lower = text.lower()
    return "?" in text or any(
        marker in lower
        for marker in ("what should", "what do", "how should", "can you", "should we", "does that mean")
    )


def _lowest_confidence(items: list[dict[str, Any]]) -> str:
    order = {"high": 3, "bounded": 2, "provisional": 1, "unresolved": 0}
    return min(
        (str(item.get("confidence") or "provisional") for item in items),
        key=lambda value: order.get(value, 1),
        default="provisional",
    )


def _unique(values: Any) -> list[str]:
    return list(dict.fromkeys(str(value).strip() for value in values if str(value).strip()))
