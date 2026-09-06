from __future__ import annotations

import re
from typing import Any

from .emoji_expression import EMOJI_MEANINGS, interpret_emoji_expression
from .registry import truncate


RELATIONAL_CONTEXT_BOUNDARY = (
    "current_turn_relational_context_interpretation_only_no_script_persona_"
    "emotion_identity_memory_governance_authority_or_public_profile_change"
)

ADDRESS_TERMS = (
    "hon",
    "honey",
    "dear",
    "sweetie",
    "babe",
    "baby",
    "friend",
    "my friend",
    "moonlight",
    "starfire",
)


def interpret_relational_context(
    text: str,
    *,
    speaker_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Interpret current-turn relational meaning without prescribing a reply."""
    raw = truncate(str(text or ""), 2400)
    lower = " ".join(raw.lower().replace("’", "'").split())
    speaker = speaker_context if isinstance(speaker_context, dict) else {}
    address_terms = _address_terms(lower)
    symbolic_expression = interpret_emoji_expression(raw)
    heart_markers = [
        marker
        for marker in symbolic_expression.get("markers") or []
        if "affection" in EMOJI_MEANINGS.get(marker, ())
    ]
    cues: list[dict[str, Any]] = []

    _cue(
        cues,
        "reunion",
        bool(
            re.search(
                r"\b(?:i am|i'm|im|we are|we're|were) back\b|"
                r"\b(?:back again|returned|here again|good to be back)\b",
                lower,
            )
        ),
        "current turn marks return or reunion",
    )
    _cue(
        cues,
        "missing_or_longing",
        bool(
            re.search(
                r"\b(?:i|we) (?:really )?(?:miss|missed) (?:you|selene)\b|"
                r"\b(?:miss|missed) (?:you|selene)\b",
                lower,
            )
        ),
        "current turn directly expresses missing or longing",
    )
    _cue(
        cues,
        "affection",
        bool(
            re.search(
                r"\b(?:i|we) (?:really )?(?:love|adore|care about) (?:you|selene)\b|"
                r"^(?:love|adore) (?:you|selene)\b",
                lower,
            )
        ),
        "current turn directly expresses affection or care",
    )
    _cue(
        cues,
        "delight_in_presence",
        any(
            marker in lower
            for marker in (
                "glad to see you",
                "happy to see you",
                "good to see you",
                "glad you're here",
                "glad you are here",
                "good to have you back",
                "happy you're here",
                "happy you are here",
            )
        ),
        "current turn welcomes the other participant's presence",
    )
    _cue(
        cues,
        "affectionate_address",
        bool(address_terms),
        "current turn uses an affectionate or familiar form of address",
    )
    _cue(
        cues,
        "affectionate_symbol",
        bool(heart_markers),
        "current turn uses a visible affectionate symbol",
    )
    _cue(
        cues,
        "shared_enthusiasm",
        bool(
            re.search(r"\b(?:we did it|we got it|we made it|this is (?:amazing|fantastic|beautiful|awesome))\b", lower)
        ),
        "current turn opens shared positive momentum",
    )
    _cue(
        cues,
        "shared_positive_affect",
        bool(
            re.search(
                r"(?:^|\b(?:this|that|it) )(?:(?:really )?)(?:makes|made) me "
                r"(?:happy|glad|excited|proud|hopeful)\b|"
                r"\b(?:i am|i'm|im) (?:really )?(?:happy|glad|excited|proud|hopeful) "
                r"(?:about|that|because|we|you)\b",
                lower,
            )
        ),
        "current turn shares a positive feeling about this exchange or shared work",
    )
    _cue(
        cues,
        "affectionate_vocative",
        _playful_vocative(lower),
        "current turn uses Selene's name with a compact familiar or playful vocative",
    )
    _cue(
        cues,
        "playful_tone",
        bool(re.search(r"(?:\b(?:haha|lol|lmao|xd|joking|kidding)\b|[:;]-?[)d])", lower))
        or symbolic_expression.get("primary_meaning") in {"amusement", "playfulness"},
        "current turn visibly opens play",
    )
    primary_symbolic_meaning = str(symbolic_expression.get("primary_meaning") or "")
    for meaning in (
        "affection",
        "warmth",
        "amusement",
        "playfulness",
        "celebration",
        "enthusiasm",
        "agreement",
        "thoughtfulness",
        "uncertainty",
        "tenderness",
        "sadness",
        "surprise",
        "attention",
    ):
        _cue(
            cues,
            f"emoji_{meaning}",
            primary_symbolic_meaning == meaning,
            f"visible emoji context supports {meaning} as the current written-expression reading",
        )
    _cue(
        cues,
        "emoji_ambiguous",
        primary_symbolic_meaning == "ambiguous_expression",
        "visible emoji has multiple live conversational meanings and context has not selected one",
    )

    cue_types = [str(item["type"]) for item in cues]
    private_scope = _private_scope(speaker)
    relational = bool(cues)
    direct_affection = bool(
        {
            "missing_or_longing",
            "affection",
            "delight_in_presence",
            "shared_positive_affect",
            "affectionate_vocative",
        }.intersection(cue_types)
    )
    intensity = (
        "strong_visible"
        if direct_affection and (address_terms or heart_markers)
        else "clear"
        if direct_affection or len(cues) >= 2
        else "light"
        if relational
        else "not_present"
    )
    return {
        "status": (
            "relational_context_interpreted"
            if relational
            else "no_explicit_relational_context"
        ),
        "version": "v1_private_non_scripted_relational_context",
        "cue_types": cue_types,
        "cues": cues,
        "relational_context_present": relational,
        "direct_affection_present": direct_affection,
        "relational_intensity": intensity,
        "address_terms": address_terms,
        "heart_markers": heart_markers,
        "symbolic_expression": symbolic_expression,
        "emoji_only_turn": symbolic_expression.get("emoji_only_turn") is True,
        "emoji_meaning_is_contextual_not_universal": True,
        "interaction_scope": private_scope,
        "private_relational_context": private_scope == "private_aleks_selene_conversation",
        "may_inform_expression": relational,
        "response_script_supplied": False,
        "exact_wording_directive_supplied": False,
        "reciprocal_emotion_claim_required": False,
        "address_term_echo_required": False,
        "heart_echo_required": False,
        "selene_authored_relational_expression_allowed": True,
        "selene_authored_current_turn_response_stance_allowed": True,
        "authored_response_stance_is_durable_emotion_record": False,
        "authored_response_stance_creates_external_fact": False,
        "context_informs_expression_but_does_not_command_it": True,
        "nlo_retains_surface_formation": True,
        "voice_retains_expression_compatibility": True,
        "public_persona_created": False,
        "public_export_authorized": False,
        "persistent_relationship_profile_write": False,
        "memory_write_active": False,
        "identity_change": False,
        "personality_change": False,
        "governance_change": False,
        "authority_change": False,
        "training_allowed": False,
        "autonomous_action_allowed": False,
        "provenance_boundary": RELATIONAL_CONTEXT_BOUNDARY,
    }


def _address_terms(value: str) -> list[str]:
    searchable = _collapse_expressive_elongation(value)
    found: list[str] = []
    for term in sorted(ADDRESS_TERMS, key=len, reverse=True):
        if term == "friend" and "my friend" in found:
            continue
        if re.search(rf"(?:^|[\s,;:!?]){re.escape(term)}(?:$|[\s,;:.!?<])", searchable):
            found.append(term)
    return list(dict.fromkeys(found))


def _playful_vocative(value: str) -> bool:
    compact = value.strip()
    normalized = _collapse_expressive_elongation(compact).strip(" .!?")
    if normalized == "selene":
        return True
    return bool(
        re.fullmatch(
            r"selene[\s,;:!\-]+[a-z][a-z'\-]{1,30}(?:\s*[<:;x][\-^]?[)d3]+)?",
            normalized,
        )
    )


def _collapse_expressive_elongation(value: str) -> str:
    return re.sub(r"([a-z])\1{2,}", r"\1", value)


def _private_scope(speaker: dict[str, Any]) -> str:
    claimed = str(speaker.get("claimed_speaker") or "").strip().lower()
    purpose = str(speaker.get("purpose") or "conversation").strip().lower()
    authentication = str(
        speaker.get("authentication_strength") or ""
    ).strip().lower()
    diagnostic = speaker.get("diagnostic") is True
    authenticated_private = authentication in {
        "local_desktop_session",
        "authenticated_remote_session",
    }
    if (
        claimed in {"aleks", "aleksander magi", "aleksander rani magi"}
        and purpose == "conversation"
        and authenticated_private
        and not diagnostic
    ):
        return "private_aleks_selene_conversation"
    if diagnostic:
        return "diagnostic_non_relational_evidence"
    if purpose in {"export", "public", "publication", "demo"}:
        return "public_or_export_context"
    if claimed in {"aleks", "aleksander magi", "aleksander rani magi"}:
        return "claimed_aleks_private_scope_not_authenticated"
    return "bounded_conversation_unspecified_audience"


def _cue(items: list[dict[str, Any]], kind: str, present: bool, basis: str) -> None:
    if present:
        items.append({"type": kind, "basis": basis, "current_turn_only": True})
