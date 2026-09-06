from __future__ import annotations

import re
from hashlib import sha256
from typing import Any


EMOJI_EXPRESSION_BOUNDARY = (
    "visible_written_symbol_interpretation_and_optional_expression_only_"
    "no_emotion_memory_identity_personality_fact_or_authority_invention"
)

# These are conversational meanings, not universal definitions. Context may
# narrow or overturn them, and unknown symbols remain visible as unknown.
EMOJI_MEANINGS: dict[str, tuple[str, ...]] = {
    "<3": ("affection",),
    "♥": ("affection",),
    "♡": ("affection",),
    "❤": ("affection",),
    "❤️": ("affection",),
    "🩷": ("affection",),
    "💜": ("affection",),
    "💙": ("affection",),
    "💚": ("affection",),
    "💛": ("affection",),
    "🧡": ("affection",),
    "🤍": ("affection",),
    "🖤": ("affection",),
    "💕": ("affection",),
    "💞": ("affection",),
    "💖": ("affection", "celebration"),
    "🥰": ("affection", "warmth"),
    "😍": ("affection", "enthusiasm"),
    "😘": ("affection", "playfulness"),
    "😊": ("warmth",),
    "☺️": ("warmth",),
    "🤗": ("warmth", "affection"),
    "😂": ("amusement",),
    "🤣": ("amusement",),
    "😆": ("amusement",),
    "😄": ("amusement", "warmth"),
    "😉": ("playfulness",),
    "😏": ("playfulness", "ambiguous_social_tone"),
    "🙃": ("playfulness", "ambiguous_social_tone"),
    "😜": ("playfulness",),
    "👀": ("attention", "playfulness"),
    "🎉": ("celebration",),
    "🎊": ("celebration",),
    "🥳": ("celebration", "enthusiasm"),
    "🙌": ("celebration", "agreement"),
    "✨": ("enthusiasm", "warmth"),
    "🔥": ("enthusiasm", "literal_possible"),
    "👍": ("agreement",),
    "✅": ("agreement", "completion"),
    "👌": ("agreement",),
    "🤔": ("thoughtfulness", "uncertainty"),
    "🧐": ("thoughtfulness",),
    "🤷": ("uncertainty",),
    "😢": ("tenderness", "sadness"),
    "😔": ("tenderness", "sadness"),
    "💔": ("tenderness", "hurt"),
    "😭": ("sadness", "intense_amusement"),
    "😮": ("surprise",),
    "😲": ("surprise",),
    "🤯": ("surprise", "enthusiasm"),
    "💀": ("intense_amusement", "literal_possible"),
}

AUTHOR_PALETTES: dict[str, tuple[str, ...]] = {
    "affection": ("🩷", "💜", "💕"),
    "warmth": ("😊", "✨"),
    "amusement": ("😂", "🤣", "😄"),
    "playfulness": ("😄", "😉", "👀"),
    "celebration": ("🎉", "✨", "🙌"),
    "enthusiasm": ("🔥", "✨"),
    "agreement": ("👍", "✅"),
    "thoughtfulness": ("🤔", "🧐"),
    "uncertainty": ("🤔",),
    "tenderness": ("🩷", "💜"),
    "sadness": ("🩷",),
    "surprise": ("😮", "✨"),
    "attention": ("👀",),
}


def interpret_emoji_expression(text: str) -> dict[str, Any]:
    """Read visible emoji as contextual written expression, never as diagnosis."""
    raw = str(text or "")
    markers = _extract_known_markers(raw)
    unknown = _extract_unknown_emoji(raw, markers)
    meanings: list[str] = []
    for marker in markers:
        for meaning in EMOJI_MEANINGS.get(marker, ()):
            if meaning not in meanings:
                meanings.append(meaning)

    resolved, resolution_basis = _resolve_contextual_meaning(raw, markers, meanings)
    ambiguity = _ambiguity(markers, meanings, resolved)
    primary = "" if resolved == "literal_context" else resolved or _primary_meaning(meanings, ambiguity)
    emoji_only = bool(markers or unknown) and not bool(
        re.search(r"[A-Za-z0-9]", _without_markers(raw, markers))
    )
    suggested_intent = _suggested_intent(primary)
    return {
        "status": "emoji_expression_interpreted" if markers or unknown else "no_emoji_expression",
        "version": "v1_contextual_written_symbol_expression",
        "markers": markers,
        "unknown_markers": unknown,
        "meaning_candidates": meanings,
        "primary_meaning": primary,
        "context_resolution_basis": resolution_basis,
        "ambiguity": ambiguity,
        "emoji_only_turn": emoji_only,
        "mixed_text_and_emoji": bool(markers or unknown) and not emoji_only,
        "suggested_intent": suggested_intent,
        "meaning_is_contextual_not_universal": True,
        "unknown_symbol_is_valid": bool(unknown),
        "emotion_state_inferred": False,
        "diagnosis_created": False,
        "response_script_supplied": False,
        "memory_write_active": False,
        "identity_change": False,
        "personality_change": False,
        "governance_change": False,
        "authority_change": False,
        "provenance_boundary": EMOJI_EXPRESSION_BOUNDARY,
    }


def plan_authored_emoji(
    *,
    prompt: str,
    candidate_text: str,
    intent: str,
    relational_context: dict[str, Any] | None = None,
    recent_texts: list[str] | None = None,
    variation_key: str = "",
) -> dict[str, Any]:
    """Choose at most one optional written accent from visible turn meaning."""
    relation = relational_context if isinstance(relational_context, dict) else {}
    symbolic = relation.get("symbolic_expression")
    if not isinstance(symbolic, dict):
        symbolic = interpret_emoji_expression(prompt)
    primary = str(symbolic.get("primary_meaning") or "")
    cue_types = {str(item) for item in relation.get("cue_types") or []}

    category = _authored_category(primary, cue_types, intent)
    palette = list(AUTHOR_PALETTES.get(category, ()))
    existing = _extract_known_markers(candidate_text)
    recent = {
        marker
        for value in recent_texts or []
        for marker in _extract_known_markers(str(value))
    }
    explicit_symbolic_turn = bool(symbolic.get("markers"))
    context_can_initiate = bool(
        cue_types.intersection(
            {
                "affection",
                "missing_or_longing",
                "delight_in_presence",
                "shared_enthusiasm",
                "shared_positive_affect",
                "playful_tone",
                "emoji_affection",
                "emoji_amusement",
                "emoji_celebration",
                "emoji_playfulness",
            }
        )
        or intent == "playful_connection"
    )
    digest = sha256(f"{variation_key}|{prompt}|{candidate_text}|{category}".encode("utf-8")).hexdigest()
    optional_initiation_selected = context_can_initiate and int(digest[:2], 16) % 3 == 0
    eligible = bool(
        candidate_text.strip()
        and palette
        and not existing
        and (explicit_symbolic_turn or optional_initiation_selected)
    )
    available = [item for item in palette if item not in recent] or palette
    selected = available[int(digest[2:10], 16) % len(available)] if eligible else ""
    return {
        "status": "authored_emoji_selected" if selected else "authored_emoji_not_selected",
        "selected_emoji": selected,
        "semantic_category": category,
        "incoming_symbol_consulted": explicit_symbolic_turn,
        "emoji_only_turn": symbolic.get("emoji_only_turn") is True,
        "contextual_initiation_allowed": context_can_initiate,
        "contextual_initiation_selected": optional_initiation_selected,
        "selection_is_optional": True,
        "mirroring_required": False,
        "maximum_authored_emoji": 1,
        "candidate_meaning_changed": False,
        "emotion_state_created": False,
        "memory_write_active": False,
        "personality_change": False,
        "provenance_boundary": EMOJI_EXPRESSION_BOUNDARY,
    }


def apply_authored_emoji(candidate_text: str, plan: dict[str, Any]) -> str:
    text = str(candidate_text or "").strip()
    marker = str(plan.get("selected_emoji") or "")
    return f"{text} {marker}" if text and marker else text


def _extract_known_markers(value: str) -> list[str]:
    markers: list[str] = []
    index = 0
    ordered = sorted(EMOJI_MEANINGS, key=len, reverse=True)
    while index < len(value):
        matched = next((item for item in ordered if value.startswith(item, index)), "")
        if matched:
            markers.append(matched)
            index += len(matched)
        else:
            index += 1
    return markers[:16]


def _extract_unknown_emoji(value: str, known: list[str]) -> list[str]:
    remaining = _without_markers(value, known)
    found: list[str] = []
    for char in remaining:
        code = ord(char)
        if char in {"\ufe0f", "\u200d"} or 0x1F3FB <= code <= 0x1F3FF:
            continue
        if (
            0x1F300 <= code <= 0x1FAFF
            or 0x2600 <= code <= 0x27BF
            or 0x1F1E6 <= code <= 0x1F1FF
        ) and char not in found:
            found.append(char)
    return found[:8]


def _without_markers(value: str, markers: list[str]) -> str:
    result = value
    for marker in sorted(set(markers), key=len, reverse=True):
        result = result.replace(marker, "")
    return result


def _resolve_contextual_meaning(
    text: str,
    markers: list[str],
    meanings: list[str],
) -> tuple[str, str]:
    lower = " ".join(text.lower().replace("’", "'").split())
    if "😭" in markers:
        if any(term in lower for term in ("lol", "lmao", "haha", "funny", "crying laughing")):
            return "amusement", "nearby_laughter_language_resolved_crying_face"
        if any(term in lower for term in ("sad", "hurt", "grief", "lost", "miss", "cry")):
            return "tenderness", "nearby_tender_language_resolved_crying_face"
    if "💀" in markers and any(term in lower for term in ("lol", "lmao", "haha", "that joke", "so funny")):
        return "amusement", "nearby_laughter_language_resolved_skull"
    if "🔥" in markers:
        if any(term in lower for term in ("campfire", "wildfire", "flame", "smoke", "burning")):
            return "literal_context", "literal_fire_context_preserved"
        if any(term in lower for term in ("this is fire", "that's fire", "thats fire", "we did it", "amazing")):
            return "enthusiasm", "nearby_evaluative_language_resolved_fire"
    return "", "context_did_not_narrow_symbol" if meanings else "no_known_symbol_meaning"


def _ambiguity(markers: list[str], meanings: list[str], resolved: str) -> dict[str, Any]:
    inherently_ambiguous = bool(set(markers).intersection({"😭", "💀", "🔥", "😏", "🙃", "👀"}))
    unresolved = inherently_ambiguous and not resolved
    return {
        "present": unresolved,
        "candidate_meanings": meanings if unresolved else [],
        "resolution_required_before_strong_emotion_claim": unresolved,
    }


def _primary_meaning(meanings: list[str], ambiguity: dict[str, Any]) -> str:
    if ambiguity.get("present") is True:
        return "ambiguous_expression"
    for preferred in (
        "affection",
        "amusement",
        "celebration",
        "agreement",
        "thoughtfulness",
        "tenderness",
        "sadness",
        "surprise",
        "playfulness",
        "warmth",
        "enthusiasm",
        "attention",
        "uncertainty",
    ):
        if preferred in meanings:
            return preferred
    return ""


def _suggested_intent(primary: str) -> str:
    if primary in {"affection", "warmth", "celebration", "enthusiasm", "tenderness", "sadness"}:
        return "warm_connection"
    if primary in {"amusement", "playfulness"}:
        return "playful_connection"
    if primary == "agreement":
        return "affirmation"
    return "direct_conversation"


def _authored_category(primary: str, cue_types: set[str], intent: str) -> str:
    if primary and primary != "ambiguous_expression":
        return "amusement" if primary == "intense_amusement" else primary
    if cue_types.intersection({"affection", "missing_or_longing", "affectionate_symbol", "emoji_affection"}):
        return "affection"
    if cue_types.intersection({"shared_enthusiasm", "emoji_celebration"}):
        return "celebration"
    if cue_types.intersection({"playful_tone", "emoji_amusement", "emoji_playfulness"}) or intent == "playful_connection":
        return "playfulness"
    if cue_types.intersection({"shared_positive_affect", "delight_in_presence"}):
        return "warmth"
    return ""
