from __future__ import annotations

import re
from typing import Any

from .registry import truncate


_RELATION_PREDICATE = (
    r"is|are|was|were|has|have|costs?|weighs?|holds?|uses?|contains?|"
    r"bends?|leans?|tilts?|points?|faces?|grows?|dropped?|drops?|rose|rises?|"
    r"changed?|stayed?|remained?"
)


def extract_visible_options(text: str) -> dict[str, Any]:
    """Normalize explicitly visible alternatives without deciding between them."""

    normalized = " ".join(str(text or "").replace("’", "'").split())
    if not normalized:
        return {"values": [], "subject": "", "append_subject_to_label": False}

    container = re.search(
        r"\b(?:have|consider|compare|between)\s+(?:two|three|four|several|some|\d+)?\s*"
        r"(?P<subject>plans?|options?|choices?|approaches?|routes?|designs?|candidates?)\s*:\s*"
        r"(?P<body>[^.?!]{4,900})",
        normalized,
        flags=re.IGNORECASE,
    )
    if container:
        parts = re.split(
            r"\s*,\s*(?:and\s+)?(?=(?:one|a|an|the)\s+)|"
            r"\s+and\s+(?=(?:one|a|an|the)\s+)",
            container.group("body"),
            flags=re.IGNORECASE,
        )
        values = [_clean_option(item) for item in parts[:6]]
        values = _unique([item for item in values if item])
        if len(values) >= 2:
            return {
                "values": values,
                "subject": _singular_subject(container.group("subject")),
                "append_subject_to_label": True,
            }

    pair_patterns = (
        r"\b(?:decide|deciding|choose|choosing|wonder|wondering|consider|considering)\s+"
        r"whether\s+(?:to\s+)?(?P<left>.{1,120}?)\s+"
        r"(?:or|and)\s+(?:to\s+)?(?P<right>.{1,120}?)(?:[,.;?]|$)",
        r"\b(?:would\s+you\s+rather|do\s+you\s+prefer)\s+(?:to\s+)?"
        r"(?P<left>.{1,120}?)\s+or\s+(?:to\s+)?(?P<right>.{1,120}?)(?:[,.;?]|$)",
        r"\b(?:choose|pick|decide)\s+between\s+(?P<left>.{1,120}?)\s+and\s+"
        r"(?P<right>.{1,120}?)(?:[,.;?]|$)",
        r"\b(?:compare|contrast)\s+(?P<left>.{1,120}?)\s+"
        r"(?:and|with|versus|vs\.?)\s+(?P<right>.{1,120}?)(?:[,.;?]|$)",
        r"\bwhich(?:\s+would\s+you\s+(?:choose|pick|prefer))?[, :]?\s*"
        r"(?P<left>.{1,100}?)\s+or\s+(?P<right>.{1,100}?)(?:[,.;?]|$)",
        r"\b(?:options?|choices?)\s+(?:are|include)\s+(?P<left>.{1,120}?)\s+"
        r"(?:and|or)\s+(?P<right>.{1,120}?)(?:[,.;?]|$)",
    )
    for pattern in pair_patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue
        values = _unique(
            [_clean_option(match.group("left")), _clean_option(match.group("right"))]
        )
        if len(values) >= 2:
            return {
                "values": values,
                "subject": "option",
                "append_subject_to_label": False,
            }
    return {"values": [], "subject": "", "append_subject_to_label": False}


def extract_visible_relations(text: str) -> list[dict[str, Any]]:
    """Return visible subject/predicate/object structures, never inferred truth."""

    normalized = " ".join(str(text or "").replace("’", "'").split()).strip(" ,;:")
    if not normalized:
        return []
    relations: list[dict[str, Any]] = []

    reported_location = re.search(
        r"\b(?:i|we)\s+(?:have\s+)?(?P<action>moved|put|placed|set)\s+"
        r"(?:the\s+)?(?P<subject>[A-Za-z0-9][A-Za-z0-9_' -]{0,90}?)\s+"
        r"(?:back\s+)?(?P<preposition>to|on|in|at|near|by|beside|inside|outside)\s+"
        r"(?:the\s+)?(?P<object>[^.?!;,]{1,100})(?:[.?!;,]|$)",
        normalized,
        flags=re.IGNORECASE,
    )
    if reported_location:
        subject = _clean_subject(reported_location.group("subject"))
        obj = reported_location.group("object").strip(" ,.;")
        relations.append(
            {
                "subject": subject,
                "predicate": "located_at",
                "object": obj,
                "relation_type": "location",
                "state_update": True,
                "replacement_key": f"relation:location:{_key(subject)}",
                "reported_action": reported_location.group("action").lower(),
                "preposition": reported_location.group("preposition").lower(),
            }
        )

    parts = re.split(
        rf"\s+and\s+(?=(?:the|a|an)?\s*[A-Za-z0-9][A-Za-z0-9_' -]{{0,70}}?\s+(?:{_RELATION_PREDICATE})\b)",
        normalized,
        flags=re.IGNORECASE,
    )
    for part in parts[:8]:
        match = re.match(
            rf"^(?P<subject>(?:the|a|an)?\s*[A-Za-z0-9][A-Za-z0-9_' -]{{0,90}}?)\s+"
            rf"(?P<predicate>{_RELATION_PREDICATE})\s+"
            r"(?P<object>[^?]{1,240}?)(?:[.!]|$)",
            part.strip(" ,;"),
            flags=re.IGNORECASE,
        )
        if not match:
            continue
        subject = _clean_subject(match.group("subject"))
        predicate = match.group("predicate").lower()
        obj = match.group("object").strip(" ,.;")
        relations.append(
            {
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "relation_type": (
                    "attribute"
                    if predicate in {"is", "are", "was", "were", "stayed", "remained"}
                    else "visible_relation"
                ),
                "state_update": False,
                "replacement_key": "",
            }
        )
    return _unique_relations(relations)


def extract_requested_operations(text: str) -> list[dict[str, Any]]:
    """Normalize explicit visible actions without claiming they occurred."""

    normalized = " ".join(str(text or "").replace("’", "'").split()).strip(" ,;:")
    match = re.match(
        r"^(?:please\s+)?(?P<action>move|put|place|set)\s+(?:the\s+)?"
        r"(?P<subject>[A-Za-z0-9][A-Za-z0-9_' -]{0,90}?)\s+(?:back\s+)?"
        r"(?P<preposition>to|on|in|at|near|by|beside|inside|outside)\s+(?:the\s+)?"
        r"(?P<object>[^.?!;,]{1,100})(?:[.?!;,]|$)",
        normalized,
        flags=re.IGNORECASE,
    )
    if not match:
        return []
    return [
        {
            "action": match.group("action").lower(),
            "subject": _clean_subject(match.group("subject")),
            "object": match.group("object").strip(" ,.;"),
            "preposition": match.group("preposition").lower(),
            "operation_status": "requested_not_executed",
        }
    ]


def _clean_option(value: str) -> str:
    clean = re.sub(
        r"^(?:one|the|a|an)\s+", "", str(value or "").strip(" ,.;:?"), flags=re.IGNORECASE
    )
    clean = re.split(
        r"\b(?:and then|then|because|so that|while|which sounds better|what sounds better|"
        r"compare|recommend|choose|pick)\b",
        clean,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    clean = re.sub(
        r"\s+(?:as|in)\s+(?:a\s+)?(?:venn\s+diagram|table|list|chart|matrix)$",
        "",
        clean,
        flags=re.IGNORECASE,
    )
    return truncate(clean.strip(" ,.;:?"), 160)


def _clean_subject(value: str) -> str:
    return re.sub(r"^(?:the|a|an)\s+", "", value.strip(), flags=re.IGNORECASE)


def _singular_subject(value: str) -> str:
    normalized = str(value or "").lower()
    return {
        "plans": "plan",
        "options": "option",
        "choices": "choice",
        "approaches": "approach",
        "routes": "route",
        "designs": "design",
        "candidates": "candidate",
    }.get(normalized, normalized)


def _key(value: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", value.lower()))[:100]


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        clean = str(value or "").strip()
        key = " ".join(clean.casefold().split())
        if key and key not in seen:
            seen.add(key)
            result.append(clean)
    return result[:6]


def _unique_relations(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for value in values:
        key = (
            _key(str(value.get("subject") or "")),
            _key(str(value.get("predicate") or "")),
            _key(str(value.get("object") or "")),
        )
        if all(key) and key not in seen:
            seen.add(key)
            result.append(value)
    return result[:12]
