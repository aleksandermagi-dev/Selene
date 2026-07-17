from __future__ import annotations

import re
from typing import Any

from .registry import truncate


INPUT_DETANGLER_BOUNDARY = (
    "session_input_interpretation_only_raw_text_preserved_no_memory_identity_governance_profile_or_authority"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "identity_change_allowed": False,
    "personality_change_allowed": False,
    "governance_change_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "automatic_lexicon_learning": False,
}

# This is intentionally a small, reviewed lexicon rather than a general-purpose
# guesser. Additions should be supported by an observed, unambiguous pattern.
REVIEWED_TOKEN_REPAIRS = {
    "beleieve": "believe",
    "catergorize": "categorize",
    "devolped": "developed",
    "enginierring": "engineering",
    "fridn": "friend",
    "hypothosize": "hypothesize",
    "migthve": "might've",
    "sollution": "solution",
    "sollutions": "solutions",
    "uncertanty": "uncertainty",
    "uncertanties": "uncertainties",
}

REVIEWED_PHRASE_REPAIRS = {
    "th e": "the",
    "th ecorpus": "the corpus",
}

# A material ambiguity is surfaced, never silently selected from these options.
AMBIGUOUS_TOKENS = {
    "caughtgit": ["caught it", "caught Git"],
    "streswing": ["stress-testing", "stressful"],
}

_PROTECTED_SPAN = re.compile(
    r"(```[\s\S]*?```|`[^`\n]*`|https?://\S+|www\.\S+|[A-Za-z]:\\\S+)",
    re.IGNORECASE,
)


def detangle_user_input(payload: dict[str, Any] | str | None = None) -> dict[str, Any]:
    """Build a conservative, inspectable interpretation without replacing the raw turn."""

    if isinstance(payload, str):
        raw_text = truncate(payload, 2400)
    else:
        payload = payload or {}
        raw_text = truncate(str(payload.get("text") or payload.get("prompt") or ""), 2400)
    if not raw_text.strip():
        raise ValueError("input text is required")

    repairs: list[dict[str, Any]] = []
    ambiguities: list[dict[str, Any]] = []
    interpreted_parts: list[str] = []

    cursor = 0
    for protected in _PROTECTED_SPAN.finditer(raw_text):
        interpreted_parts.append(_repair_segment(raw_text[cursor : protected.start()], repairs, ambiguities))
        interpreted_parts.append(protected.group(0))
        cursor = protected.end()
    interpreted_parts.append(_repair_segment(raw_text[cursor:], repairs, ambiguities))
    interpreted_text = "".join(interpreted_parts)

    changed = interpreted_text != raw_text
    has_ambiguity = bool(ambiguities)
    if has_ambiguity and changed:
        status = "input_detangled_with_unresolved_ambiguity"
    elif has_ambiguity:
        status = "input_ambiguity_visible"
    elif changed:
        status = "input_detangled"
    else:
        status = "input_unchanged"

    return {
        "status": status,
        "raw_text": raw_text,
        "interpreted_text": interpreted_text,
        "raw_text_preserved": True,
        "meaning_preservation_policy": "repair_only_reviewed_unambiguous_patterns_and_leave_material_ambiguity_unresolved",
        "repairs": repairs,
        "ambiguities": ambiguities,
        "repair_count": len(repairs),
        "ambiguity_count": len(ambiguities),
        "interpretation_confidence": "unresolved" if has_ambiguity else "high" if changed else "not_needed",
        "safe_for_semantic_routing": True,
        "safe_for_silent_repair": not has_ambiguity,
        "interpretation_complete": not has_ambiguity,
        "ask_if_materially_ambiguous": has_ambiguity,
        "protected_material_policy": "code_urls_and_workspace_paths_are_not_rewritten",
        "provenance_boundary": INPUT_DETANGLER_BOUNDARY,
        "review_destination": "Status",
        "review_status": "status_only",
        **GUARDS,
    }


def _repair_segment(
    segment: str,
    repairs: list[dict[str, Any]],
    ambiguities: list[dict[str, Any]],
) -> str:
    value = segment
    for original, replacement in REVIEWED_PHRASE_REPAIRS.items():
        escaped = re.escape(original).replace(r"\ ", r"\s+")
        pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
        value = pattern.sub(lambda match: _record_repair(match, replacement, "reviewed_phrase", repairs), value)

    if REVIEWED_TOKEN_REPAIRS:
        token_pattern = re.compile(
            r"\b(" + "|".join(re.escape(item) for item in sorted(REVIEWED_TOKEN_REPAIRS, key=len, reverse=True)) + r")\b",
            re.IGNORECASE,
        )
        value = token_pattern.sub(
            lambda match: _record_repair(
                match,
                REVIEWED_TOKEN_REPAIRS[match.group(0).lower()],
                "reviewed_token",
                repairs,
            ),
            value,
        )

    for match in re.finditer(r"\b[A-Za-z][A-Za-z'-]*\b", value):
        token = match.group(0).lower()
        if token in AMBIGUOUS_TOKENS and not any(
            item.get("token", "").lower() == token for item in ambiguities
        ):
            ambiguities.append(
                {
                    "token": match.group(0),
                    "alternatives": list(AMBIGUOUS_TOKENS[token]),
                    "reason": "more than one meaning-preserving repair is plausible",
                    "resolution": "left_unchanged_ask_only_if_material_to_the_answer",
                }
            )

    normalized = re.sub(r"[ \t]+([,.;:!?])", r"\1", value)
    normalized = re.sub(r"[ \t]{2,}", " ", normalized)
    if normalized != value:
        repairs.append(
            {
                "original": value,
                "replacement": normalized,
                "kind": "spacing_only",
                "confidence": "high",
                "meaning_changed": False,
            }
        )
    return normalized


def _record_repair(
    match: re.Match[str],
    replacement: str,
    kind: str,
    repairs: list[dict[str, Any]],
) -> str:
    original = match.group(0)
    rendered = _match_case(original, replacement)
    repairs.append(
        {
            "original": original,
            "replacement": rendered,
            "kind": kind,
            "confidence": "high",
            "meaning_changed": False,
        }
    )
    return rendered


def _match_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement
