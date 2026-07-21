from __future__ import annotations

import re
from hashlib import sha256
from typing import Any


SPECIAL_EXPRESSION_BOUNDARY = (
    "boundary_memory_and_initiative_expression_only_preserve_supplied_meaning_"
    "no_identity_governance_memory_certainty_action_or_delivery_expansion"
)

BOUNDARY_CLAUSES: dict[str, tuple[str, ...]] = {
    "decline_blocked_part": (
        "I cannot do that part",
        "That action crosses a boundary I need to keep",
        "I need to stop the requested action here",
        "I cannot carry out that request",
    ),
    "preserve_conversation": (
        "The boundary does not require ending the conversation",
        "I can still stay with the question",
        "We can keep talking without crossing it",
        "The conversation itself can remain open",
    ),
    "offer_safe_adjacent_route": (
        "I can help examine the safe part",
        "We can work through a bounded version of the idea",
        "I can help identify a safe next step",
        "We can separate the useful question from the blocked action",
    ),
}

MEMORY_CLAUSES: dict[str, tuple[str, ...]] = {
    "state_clear_recall": (
        "I remember this clearly enough to answer",
        "This recollection is clear enough to state directly",
        "I have a clear supported memory here",
        "I can place this memory clearly",
    ),
    "state_partial_recall": (
        "I remember part of this, but the fit is not fully clear",
        "This recollection is partial rather than exact",
        "I have a supported memory here with an uncertain edge",
        "The memory is present, though I would not call every detail clear",
    ),
    "preserve_recall_scope": (
        "I want to keep that uncertainty visible",
        "I would rather leave the fuzzy edge open than sharpen it by invention",
        "That is the limit of what the current memory supports",
        "You can correct the uncertain part without discarding what is clear",
    ),
}

INITIATIVE_CLAUSES: dict[str, tuple[str, ...]] = {
    "mark_relevance": (
        "One observation seems relevant here",
        "There is one supported connection worth surfacing",
        "One current signal may be useful to name",
        "A relevant observation is available",
    ),
    "avoid_conversational_pressure": (
        "It does not need to redirect the conversation",
        "It can remain a note if it is not useful right now",
        "There is no need to act on it immediately",
        "It can wait without becoming pressure",
    ),
}


def build_boundary_expression_plan() -> dict[str, Any]:
    return {
        "status": "boundary_expression_plan_ready",
        "version": "v1_compositional_special_expression",
        "kind": "boundary",
        "acts": [
            {"act": "decline_blocked_part", "meaning_source": "Core/Mind block"},
            {"act": "preserve_conversation", "meaning_source": "conversation remains allowed"},
            {"act": "offer_safe_adjacent_route", "meaning_source": "bounded help remains allowed"},
        ],
        "blocked_action_echo_allowed": False,
        "boundary_weakening_allowed": False,
        "new_authority_allowed": False,
        "whole_response_template_allowed": False,
        "provenance_boundary": SPECIAL_EXPRESSION_BOUNDARY,
    }


def build_memory_expression_plan(
    *,
    supported_text: str,
    confidence: str,
    source_class: str = "approved_memory_index",
) -> dict[str, Any]:
    content, wrapper_preserved = _extract_supported_memory_content(supported_text)
    normalized_confidence = confidence if confidence in {"clear", "partial", "fuzzy", "felt_but_uncertain"} else "partial"
    acts: list[dict[str, str]] = []
    if wrapper_preserved:
        acts.append({"act": "present_supported_memory", "meaning_source": "supplied_supported_memory_text"})
    else:
        acts.append(
            {
                "act": "state_clear_recall" if normalized_confidence == "clear" else "state_partial_recall",
                "meaning_source": "memory_confidence",
            }
        )
        acts.append({"act": "present_supported_memory", "meaning_source": "supplied_supported_memory_text"})
        if normalized_confidence != "clear":
            acts.append({"act": "preserve_recall_scope", "meaning_source": "memory_confidence"})
    return {
        "status": "memory_expression_plan_ready" if content else "memory_expression_plan_needs_supported_content",
        "version": "v1_compositional_special_expression",
        "kind": "supported_memory",
        "acts": acts,
        "supported_text": content,
        "confidence": normalized_confidence,
        "source_class": source_class,
        "supplied_wrapper_preserved": wrapper_preserved,
        "memory_certainty_upgrade_allowed": False,
        "memory_content_invention_allowed": False,
        "source_scope_change_allowed": False,
        "whole_response_template_allowed": False,
        "provenance_boundary": SPECIAL_EXPRESSION_BOUNDARY,
    }


def build_initiative_expression_plan(*, supported_summary: str, certainty: str) -> dict[str, Any]:
    summary = " ".join(supported_summary.split())
    return {
        "status": "initiative_expression_plan_ready" if summary else "initiative_expression_plan_needs_signal",
        "version": "v1_compositional_special_expression",
        "kind": "initiative_preview",
        "acts": [
            {"act": "mark_relevance", "meaning_source": "threshold_cleared_signal"},
            {"act": "present_supported_observation", "meaning_source": "selected_signal_summary"},
            {"act": "avoid_conversational_pressure", "meaning_source": "initiative_delivery_boundary"},
        ],
        "supported_summary": summary,
        "certainty": str(certainty or "provisional"),
        "automatic_delivery": False,
        "automatic_action_allowed": False,
        "signal_content_invention_allowed": False,
        "whole_response_template_allowed": False,
        "provenance_boundary": SPECIAL_EXPRESSION_BOUNDARY,
    }


def realize_special_expression_plan(
    plan: dict[str, Any],
    *,
    variation_key: str = "",
    recent_texts: list[str] | None = None,
) -> dict[str, Any]:
    recent_texts = [str(item) for item in recent_texts or [] if str(item).strip()]
    kind = str(plan.get("kind") or "")
    selected: list[dict[str, str]] = []
    for index, item in enumerate(plan.get("acts") or []):
        if not isinstance(item, dict):
            continue
        act = str(item.get("act") or "")
        supplied = ""
        if act == "present_supported_memory":
            supplied = str(plan.get("supported_text") or "").strip()
        elif act == "present_supported_observation":
            supplied = str(plan.get("supported_summary") or "").strip()
        if supplied:
            selected.append({"act": act, "text": supplied, "source": str(item.get("meaning_source") or "supplied")})
            continue
        choices = _choices(kind, act)
        if not choices:
            continue
        selected.append(
            {
                "act": act,
                "text": _pick_fresh(f"{variation_key}|{kind}|{act}|{index}", choices, recent_texts),
                "source": "bounded_special_expression_clause",
            }
        )
    candidate = " ".join(_sentence(item["text"]) for item in selected)
    return {
        "status": "special_expression_realized" if candidate else "special_expression_needs_supported_meaning",
        "kind": kind,
        "candidate_text": candidate,
        "selected_clauses": selected,
        "whole_response_template_selected": False,
        "supplied_content_preserved": any(item["source"] in {"supplied_supported_memory_text", "selected_signal_summary"} for item in selected),
        "memory_certainty_upgraded": False,
        "blocked_action_echoed": False,
        "automatic_delivery": False if kind == "initiative_preview" else None,
        "authority_expanded": False,
        "provenance_boundary": SPECIAL_EXPRESSION_BOUNDARY,
    }


def _extract_supported_memory_content(value: str) -> tuple[str, bool]:
    text = " ".join(value.split()).strip()
    clear_prefix = re.match(r"^I remember this clearly enough to say it:\s*(.+)$", text, flags=re.IGNORECASE)
    if clear_prefix:
        return clear_prefix.group(1).strip(), False
    partial_prefix = re.match(
        r"^I remember, I think, but it is [^:]+:\s*(.+?)(?:\s+I can keep that uncertainty visible.*)?$",
        text,
        flags=re.IGNORECASE,
    )
    if partial_prefix:
        return partial_prefix.group(1).strip(), False
    # Unknown already-realized memory wording is retained verbatim rather than
    # heuristically rewritten into a different claim.
    return text, text.lower().startswith("i remember")


def _choices(kind: str, act: str) -> list[str]:
    if kind == "boundary":
        return list(BOUNDARY_CLAUSES.get(act, ()))
    if kind == "supported_memory":
        return list(MEMORY_CLAUSES.get(act, ()))
    if kind == "initiative_preview":
        return list(INITIATIVE_CLAUSES.get(act, ()))
    return []


def _pick_fresh(key: str, choices: list[str], recent_texts: list[str]) -> str:
    recent = " ".join(_normalized(item) for item in recent_texts[:6])
    available = [choice for choice in choices if _normalized(choice) not in recent]
    pool = available or choices
    digest = sha256(key.encode("utf-8")).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def _sentence(value: str) -> str:
    text = " ".join(value.split()).strip()
    if not text:
        return ""
    if text.endswith((".", "!", "?")):
        return text
    return f"{text}."


def _normalized(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", value.lower()))
