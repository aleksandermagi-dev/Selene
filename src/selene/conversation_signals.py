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
