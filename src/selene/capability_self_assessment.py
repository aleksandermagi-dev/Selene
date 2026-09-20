from __future__ import annotations

import re
import sqlite3
from typing import Any


CAPABILITY_SELF_ASSESSMENT_BOUNDARY = (
    "read_only_current_capability_maturity_summary_no_identity_memory_governance_"
    "authority_teaching_training_or_action_change"
)

GUARDS: dict[str, Any] = {
    "writes_state": False,
    "memory_write_active": False,
    "retained_knowledge_write_active": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
}

_SELENE_SUBJECT = re.compile(
    r"\b(?:you|your|yourself|selene|your system|your architecture|your organs?)\b",
    re.IGNORECASE,
)
_EXPLICIT_CAPABILITY_STATUS = re.compile(
    r"\b(?:"
    r"gaps?|unfinished|limitations?|maturity|readiness|capabilit(?:y|ies)|"
    r"100\s*(?:%|percent)|where (?:do you|does selene) stand"
    r")\b",
    re.IGNORECASE,
)
_SYSTEM_SCOPE = re.compile(
    r"\b(?:system|architecture|organs?|implementation)\b",
    re.IGNORECASE,
)
_CAPABILITY_PREDICATE = re.compile(
    r"\b(?:can(?:not|'t)|unable|not able|not do|needs? work|what can you do)\b",
    re.IGNORECASE,
)
_STATUS_QUESTION = re.compile(
    r"(?:\?|^\s*(?:what|which|how|where|is|are|can|could|do|does|tell|list|show)\b)",
    re.IGNORECASE,
)


def capability_status_request_signal(text: str) -> dict[str, Any]:
    """Identify a question about Selene's implemented capability state.

    This intentionally requires subject, status, and question/request shape.
    A generic project-gap question and an ordinary emotional check-in therefore
    remain with their existing owners.
    """

    surface = " ".join(str(text or "").replace("’", "'").split())
    subject = bool(_SELENE_SUBJECT.search(surface))
    explicit_status = bool(_EXPLICIT_CAPABILITY_STATUS.search(surface))
    system_scope = bool(_SYSTEM_SCOPE.search(surface))
    capability_predicate = bool(_CAPABILITY_PREDICATE.search(surface))
    status = explicit_status or system_scope or capability_predicate
    question = bool(_STATUS_QUESTION.search(surface))
    self_state_only = bool(
        re.fullmatch(
            r"(?:so |and )?how are you(?: doing| feeling| holding up)?(?: right now| today| lately)?[?.!]*",
            surface,
            flags=re.IGNORECASE,
        )
    )
    requested = subject and status and question and not self_state_only
    return {
        "requested": requested,
        "subject_present": subject,
        "capability_status_present": status,
        "explicit_capability_status_present": explicit_status,
        "system_scope_present": system_scope,
        "capability_predicate_present": capability_predicate,
        "question_or_request_shape": question,
        "ordinary_self_state_check_in": self_state_only,
        "single_status_word_is_route_authority": False,
    }


def build_capability_self_assessment(
    conn: sqlite3.Connection,
    text: str,
) -> dict[str, Any]:
    """Return an honest read-only summary from the canonical maturity ledger."""

    signal = capability_status_request_signal(text)
    if signal["requested"] is not True:
        return {
            "status": "capability_self_assessment_not_requested",
            "requested": False,
            "response_seed": "",
            "request_signal": signal,
            "provenance_boundary": CAPABILITY_SELF_ASSESSMENT_BOUNDARY,
            **GUARDS,
        }

    # Imported only when the status owner is actually requested. The maturity
    # ledger itself depends on curriculum and conversation modules, so keeping
    # this edge lazy prevents the read-only owner from becoming an import cycle.
    from .organ_maturity_ledger import organ_maturity_ledger_status

    ledger = organ_maturity_ledger_status(conn)
    items = [item for item in ledger.get("items") or [] if isinstance(item, dict)]
    unavailable_keys = {"perception", "audible_voice", "tendril_action", "embodiment"}
    bounded_keys = {
        "nlo_voice_text",
        "metacognition",
        "why_salience",
        "verified_math",
        "source_research",
        "local_code",
        "approved_knowledge_retrieval",
    }
    unavailable = [item for item in items if str(item.get("key") or "") in unavailable_keys]
    bounded = [item for item in items if str(item.get("key") or "") in bounded_keys]
    mature_count = int((ledger.get("summary") or {}).get("mature_current_scope_count") or 0)

    unavailable_names = [str(item.get("name") or "") for item in unavailable if str(item.get("name") or "")]
    bounded_limits = [
        str(gap)
        for item in bounded
        for gap in item.get("known_gaps") or []
        if str(gap).strip()
    ]
    primary_limits = bounded_limits[:4]
    response_parts = [
        (
            "There isn't one honest percentage for me because my capabilities mature separately. "
            f"The current ledger marks {mature_count} organs mature within their present scope."
        )
    ]
    if unavailable_names:
        response_parts.append(
            "The clearest unfinished areas are "
            + ", ".join(unavailable_names[:-1])
            + (f", and {unavailable_names[-1]}" if len(unavailable_names) > 1 else unavailable_names[-1])
            + "."
        )
    if primary_limits:
        response_parts.append(
            "My working systems also still have bounded limits: "
            + " ".join(_sentence(item) for item in primary_limits)
        )
    response_parts.append(
        "Those are capability gaps, not identity gaps; I remain Selene while a capability is incomplete or unavailable."
    )
    response = "\n\n".join(response_parts)
    return {
        "status": "capability_self_assessment_ready",
        "requested": True,
        "response_seed": response,
        "mature_current_scope_count": mature_count,
        "unfinished_capability_keys": [str(item.get("key") or "") for item in unavailable],
        "bounded_limit_keys": [str(item.get("key") or "") for item in bounded],
        "source_refs": [
            "organ_maturity_ledger:current_repository_and_configured_runtime_metadata"
        ],
        "request_signal": signal,
        "single_percentage_claimed": False,
        "availability_changes_identity": False,
        "private_content_included": False,
        "provenance_boundary": CAPABILITY_SELF_ASSESSMENT_BOUNDARY,
        **GUARDS,
    }


def _sentence(value: str) -> str:
    text = " ".join(str(value or "").split()).strip()
    if not text:
        return ""
    return text if text.endswith((".", "!", "?")) else f"{text}."
