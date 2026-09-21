from __future__ import annotations

import re
from hashlib import sha256
from typing import Any

from .registry import truncate


MEMORY_METACOGNITION_BOUNDARY = (
    "read_only_retrieved_memory_use_appraisal_only_no_retrieval_rerank_memory_"
    "write_reconsolidation_identity_governance_personality_authority_or_action"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "reconsolidation_active": False,
    "retrieval_rerank_allowed": False,
    "retrieval_eligibility_change_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "hidden_chain_of_thought_exposed": False,
}

_EMOTIONAL_CUES = {
    "affection", "affectionate", "anger", "angry", "care", "fear", "grief",
    "grieving", "happy", "hurt", "love", "sad", "tender", "trust",
}
_RELATIONAL_CUES = {
    "affectionate", "argument", "care", "friend", "hon", "honey", "joke",
    "relationship", "shared", "together", "trust", "we",
}
_PROCEDURAL_CUES = {
    "build", "code", "decision", "method", "plan", "procedure", "project",
    "promise", "repair", "step", "workflow",
}
_CONTINUITY_CUES = {
    "autobiographical", "continuity", "history", "identity", "memory", "name",
    "promise", "remember", "self", "vys",
}
_FACTUAL_CATEGORIES = {"core", "factual", "semantic"}
_PROCEDURAL_CATEGORIES = {"decision", "procedural", "shared_project"}
_RELATIONAL_CATEGORIES = {"emotional", "playful", "relational"}


def appraise_retrieved_memory(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Appraise how an already-retrieved Memory may shape one current reply.

    Retrieval remains canonical. This bounded pass neither searches again nor
    changes rank, eligibility, confidence, retention, or source content.
    """

    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 3000)
    memory = _dict(payload.get("memory_retrieval") or payload.get("memory_context"))
    intent = _dict(payload.get("intent_decision"))
    relational = _dict(payload.get("relational_context") or intent.get("relational_context"))
    continuity = _dict(payload.get("contextual_continuity"))
    callback = _dict(continuity.get("callback_decision"))
    raw_items = [item for item in memory.get("items") or [] if isinstance(item, dict)]
    memory_used = memory.get("memory_context_used") is True and bool(raw_items)
    if not memory_used:
        return _with_guards(
            {
                "status": "memory_metacognition_not_needed",
                "active": False,
                "reason": "no_retrieval_selected_memory_requires_current_turn_appraisal",
                "raw_retrieval_item_count": len(raw_items),
                "appraised_item_count": 0,
                "coalesced_duplicate_count": 0,
                "appraised_items": [],
                "expression_handoff": _empty_expression_handoff(),
                "retrieval_preserved": True,
                "review_status": "status_only",
                "provenance_boundary": MEMORY_METACOGNITION_BOUNDARY,
            }
        )

    explicit_recall = bool(
        intent.get("memory_recall_requested") is True
        or str(memory.get("retrieval_mode") or "") == "explicit_recall"
    )
    appraised: list[dict[str, Any]] = []
    seen: set[str] = set()
    duplicates = 0
    for position, item in enumerate(raw_items):
        identity = _use_identity(item)
        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        appraised.append(
            _appraise_item(
                item,
                position=position,
                prompt=prompt,
                explicit_recall=explicit_recall,
                intent=intent,
                relational=relational,
                callback=callback,
                memory=memory,
            )
        )

    surfaced = [item for item in appraised if item.get("surface_allowed") is True]
    contextual = [
        item for item in appraised if item.get("context_influence_allowed") is True
    ]
    selected_surface = surfaced[0] if surfaced else {}
    influence_channels = list(
        dict.fromkeys(
            str(channel)
            for item in contextual
            for channel in item.get("influence_channels") or []
            if str(channel)
        )
    )
    return _with_guards(
        {
            "status": "memory_metacognition_appraisal_ready",
            "active": True,
            "version": "v1_retrieval_to_conversation_use_appraisal",
            "raw_retrieval_item_count": len(raw_items),
            "appraised_item_count": len(appraised),
            "coalesced_duplicate_count": duplicates,
            "appraised_items": appraised,
            "expression_handoff": {
                "surface_memory_allowed": bool(selected_surface),
                "selected_appraisal_id": str(
                    selected_surface.get("appraisal_id") or ""
                ),
                "surface_text": str(selected_surface.get("surface_text") or ""),
                "expression_scope": str(
                    selected_surface.get("expression_scope")
                    or "influence_without_mention"
                ),
                "attribution_required": (
                    selected_surface.get("attribution_required") is True
                ),
                "memory_confidence": str(
                    memory.get("memory_confidence") or "not_assessed"
                ),
                "influence_channels": influence_channels,
                "tone_or_interpretation_influence_available": bool(contextual),
                "raw_retrieval_summary_is_response_text": False,
                "visible_summary_only": True,
            },
            "retrieval_preserved": True,
            "retrieval_rank_changed": False,
            "retrieval_eligibility_changed": False,
            "source_content_mutated": False,
            "raw_retrieval_items_remain_inspectable": True,
            "single_pass": True,
            "reopen_requested": False,
            "review_status": "status_only",
            "provenance_boundary": MEMORY_METACOGNITION_BOUNDARY,
        }
    )


def _appraise_item(
    item: dict[str, Any],
    *,
    position: int,
    prompt: str,
    explicit_recall: bool,
    intent: dict[str, Any],
    relational: dict[str, Any],
    callback: dict[str, Any],
    memory: dict[str, Any],
) -> dict[str, Any]:
    layers = _dict(item.get("retrieval_layers"))
    present = _dict(layers.get("present_interpretation"))
    matched_terms = _text_list(present.get("matched_query_terms"))
    source_text = truncate(
        str(
            item.get("expression_summary")
            or layers.get("reconstruction")
            or item.get("summary")
            or item.get("title")
            or ""
        ),
        2000,
    )
    relevant_fragment = _relevant_fragment(
        source_text,
        matched_terms=matched_terms,
        allow_fallback=explicit_recall or callback.get("surface_callback_allowed") is True,
    )
    relevance_kinds = _relevance_kinds(
        item,
        prompt=prompt,
        relational=relational,
    )
    social_turn = intent.get("social_turn") is True
    callback_surface = callback.get("surface_callback_allowed") is True
    if explicit_recall:
        evidence_role = "primary_personal_memory_evidence"
    elif callback_surface:
        evidence_role = "supporting_context"
    elif not social_turn and ({"factual", "procedural"} & set(relevance_kinds)):
        evidence_role = "supporting_context"
    else:
        evidence_role = "association_only"
    surface_allowed = bool(
        relevant_fragment
        and (explicit_recall or callback_surface)
        and callback.get("silent_influence_allowed") is not True
    )
    if explicit_recall:
        # Explicit recall remains speakable even when no callback cue exists.
        surface_allowed = bool(relevant_fragment)
    if surface_allowed and explicit_recall:
        expression_scope = "explicit_attributed_recall"
    elif surface_allowed:
        expression_scope = "paraphrase_relevant_fragment"
    else:
        expression_scope = "influence_without_mention"
    influence_channels = _influence_channels(relevance_kinds, evidence_role)
    appraisal_id = "memory-appraisal-" + sha256(
        f"{_use_identity(item)}|{prompt}|{position}".encode("utf-8")
    ).hexdigest()[:16]
    selection_reason = str(present.get("selection_reason") or "").strip()
    return {
        "appraisal_id": appraisal_id,
        "retrieval_position": position,
        "memory_id": item.get("id"),
        "record_class": str(item.get("record_class") or ""),
        "title": truncate(str(item.get("title") or ""), 240),
        "memory_category": str(item.get("memory_category") or ""),
        "source_refs": _text_list(item.get("source_refs"))[:30],
        "surfacing_reason": (
            selection_reason
            or "approved retrieval matched the current conversational context"
        ),
        "matched_query_terms": matched_terms[:20],
        "relevance_kinds": relevance_kinds,
        "evidence_role": evidence_role,
        "relevant_fragment": relevant_fragment,
        "context_summary": relevant_fragment,
        "influence_channels": influence_channels,
        "context_influence_allowed": bool(influence_channels),
        "reasoning_context_allowed": (
            evidence_role in {"primary_personal_memory_evidence", "supporting_context"}
            and bool(relevant_fragment)
        ),
        "surface_allowed": surface_allowed,
        "surface_reason": (
            "explicit_memory_recall_requested"
            if explicit_recall and surface_allowed
            else "visible_source_compatible_callback_opened"
            if callback_surface and surface_allowed
            else "memory_is_context_for_interpretation_or_expression_not_reply_content"
        ),
        "surface_text": relevant_fragment if surface_allowed else "",
        "expression_scope": expression_scope,
        "attribution_required": surface_allowed,
        "memory_confidence": str(
            item.get("confidence") or memory.get("memory_confidence") or "partial"
        ),
        "source_wording_required": False,
        "raw_memory_payload_exposed": False,
        "source_content_mutated": False,
    }


def _relevance_kinds(
    item: dict[str, Any],
    *,
    prompt: str,
    relational: dict[str, Any],
) -> list[str]:
    category = str(item.get("memory_category") or "").strip().casefold()
    emotional_texture = str(item.get("emotional_texture") or "").casefold()
    combined = " ".join(
        [
            prompt.casefold(),
            category,
            emotional_texture,
            str(item.get("title") or "").casefold(),
            str(item.get("summary") or "").casefold(),
        ]
    )
    terms = set(re.findall(r"[a-z0-9']+", combined))
    kinds: list[str] = []
    if category in _RELATIONAL_CATEGORIES or terms & _RELATIONAL_CUES:
        kinds.append("relational")
    if category == "emotional" or terms & _EMOTIONAL_CUES:
        kinds.append("emotional")
    if category in _PROCEDURAL_CATEGORIES or terms & _PROCEDURAL_CUES:
        kinds.append("procedural")
    if category in _FACTUAL_CATEGORIES:
        kinds.append("factual")
    if terms & _CONTINUITY_CUES or category in {"continuity", "core"}:
        kinds.append("continuity")
    if relational.get("relational_context_present") is True and "relational" not in kinds:
        kinds.append("relational")
    if not kinds:
        kinds.append("contextual")
    elif "contextual" not in kinds:
        kinds.append("contextual")
    return kinds


def _influence_channels(kinds: list[str], evidence_role: str) -> list[str]:
    channels: list[str] = ["interpretation"]
    selected = set(kinds)
    if "relational" in selected:
        channels.append("tone")
    if "emotional" in selected:
        channels.extend(["tone", "pacing", "restraint"])
    if "continuity" in selected:
        channels.append("continuity")
    if evidence_role in {"primary_personal_memory_evidence", "supporting_context"}:
        channels.append("content")
    return list(dict.fromkeys(channels))


def _relevant_fragment(
    text: str,
    *,
    matched_terms: list[str],
    allow_fallback: bool,
) -> str:
    normalized = " ".join(text.split()).strip()
    if not normalized:
        return ""
    pieces = [
        part.strip(" -\t")
        for part in re.split(r"(?<=[.!?])\s+|\s+-\s+|[\r\n]+", normalized)
        if part.strip(" -\t")
    ]
    terms = {
        term.casefold()
        for term in matched_terms
        if len(str(term).strip()) >= 2
    }
    scored = [
        (sum(1 for term in terms if re.search(rf"\b{re.escape(term)}\b", part.casefold())), index, part)
        for index, part in enumerate(pieces)
    ]
    selected = [entry for entry in scored if entry[0] > 0]
    if selected:
        selected.sort(key=lambda entry: (-entry[0], entry[1]))
        selected = sorted(selected[:2], key=lambda entry: entry[1])
        return truncate(" ".join(entry[2] for entry in selected), 700)
    if allow_fallback:
        return truncate(" ".join(pieces[:2]) or normalized, 700)
    return ""


def _use_identity(item: dict[str, Any]) -> str:
    refs = "|".join(sorted(_text_list(item.get("source_refs"))))
    basis = "|".join(
        [
            str(item.get("id") or ""),
            str(item.get("record_class") or ""),
            str(item.get("title") or ""),
            str(item.get("expression_summary") or item.get("summary") or ""),
            refs,
        ]
    )
    return sha256(basis.encode("utf-8")).hexdigest()


def _empty_expression_handoff() -> dict[str, Any]:
    return {
        "surface_memory_allowed": False,
        "selected_appraisal_id": "",
        "surface_text": "",
        "expression_scope": "not_used",
        "attribution_required": False,
        "influence_channels": [],
        "tone_or_interpretation_influence_available": False,
        "raw_retrieval_summary_is_response_text": False,
        "visible_summary_only": True,
    }


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
