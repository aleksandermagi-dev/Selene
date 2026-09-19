from __future__ import annotations

import re


def explicit_correction_signal(value: str) -> bool:
    """Recognize a visible interactional correction, not its topic word."""
    normalized = " ".join(str(value or "").lower().replace("’", "'").split())
    if any(
        marker in normalized
        for marker in ("i meant", "what i meant was", "not what i meant")
    ):
        return True
    if re.search(r"^(?:update|revision)\s*[:,-]\s+\S", normalized):
        return True
    return bool(
        re.search(
            r"^(?:(?:one|a)\s+)?(?:(?:small|quick)\s+)?correction\b"
            r"(?:\s*[:,-]|\s+to\b|\s*$)",
            normalized,
        )
    )


def actually_marks_correction(value: str, *, topic_shift: bool = False) -> bool:
    """Treat ``actually`` as revision only when it visibly revises content."""
    normalized = " ".join(str(value or "").lower().replace("’", "'").split())
    if topic_shift or "actually" not in normalized:
        return False
    if re.search(
        r"\b(?:do|does|did|can|could|would|will|is|are|was|were|have|has)\s+"
        r"(?:we|i|you|it|that|this|they|he|she)\s+actually\b",
        normalized,
    ):
        return False
    return bool(
        re.search(
            r"(?:^|[.!?;]\s*|\bbut\s+)actually\s*,?\s+"
            r"(?:the|a|an|i|we|you|it|that|this|they|he|she)\b",
            normalized,
        )
    )


def correction_signal(value: str, *, topic_shift: bool = False) -> bool:
    return explicit_correction_signal(value) or actually_marks_correction(
        value,
        topic_shift=topic_shift,
    )


def explicit_humor_request(value: str) -> bool:
    """Recognize one visibly requested joke or pun across conversation owners."""

    normalized = " ".join(str(value or "").lower().replace("’", "'").split())
    coordinated_nominal_request = bool(
        re.match(
            r"^(?:please\s+)?(?:give|tell|make|write|share|add|include|put in)\b",
            normalized,
        )
        and re.search(
            r"\b(?:and|then)\s+(?:one|a|an)\s+"
            r"(?:tiny\s+|little\s+|small\s+|quick\s+|short\s+)?"
            r"(?:[a-z][a-z0-9'-]*\s+){0,3}(?:joke|pun)\b",
            normalized,
        )
    )
    return bool(
        re.search(
            r"\b(?:give|tell|make|write|share|add|include|put in)\s+"
            r"(?:me\s+)?(?:one\s+|a\s+|an\s+)?"
            r"(?:tiny\s+|little\s+|small\s+|quick\s+|short\s+)?"
            r"(?:[a-z][a-z0-9'-]*\s+){0,3}(?:joke|pun)\b",
            normalized,
        )
        or re.search(
            r"\bgive\s+(?:the\s+)?[a-z][a-z0-9' -]{1,100}?\s+"
            r"(?:one|a|an)\s+(?:tiny\s+|little\s+|small\s+|quick\s+|short\s+)?"
            r"(?:joke|pun)\b",
            normalized,
        )
        or coordinated_nominal_request
    )


def explicit_conversational_closure_request(value: str) -> bool:
    """Recognize an explicit request to land conversation, not close an object."""

    normalized = " ".join(str(value or "").lower().replace("’", "'").split())
    return bool(
        re.search(
            r"\b(?:let|allow)\b.*\b(?:conversation|chat|exchange)\b.*\bend\b|"
            r"\bend\b.*\bnaturally\b|"
            r"\b(?:leave|stop|pause)\s+(?:it|this|that|the\s+[a-z][a-z0-9' -]{0,80})\s+"
            r"(?:here|there)(?:\s+for\s+now)?\b|"
            r"\b(?:talk|chat|speak)(?:\s+again)?\s+"
            r"(?:later|tomorrow|next time|another time)\b|"
            r"\b(?:get|come|go|return)\s+back\s+to\b.{0,100}"
            r"\b(?:later|tomorrow|next time|another time)\b|"
            r"\bclose(?:\s+(?:the\s+)?(?:conversation|chat|exchange|thread|topic))?\s+"
            r"(?:naturally|without\s+(?:a\s+)?(?:follow-up\s+)?question)\b|"
            r"\bclose\s+(?:this|that|it)\s+out\b",
            normalized,
        )
    )
