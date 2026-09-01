from __future__ import annotations

import re
from typing import Any

from .lexical_semantics import available_lexical_forms, build_lexical_semantic_set
from .registry import truncate


SUPPORTED_SEMANTICS_BOUNDARY = (
    "supported_answer_meaning_handoff_only_no_fact_memory_identity_personality_"
    "governance_authority_or_expression_ownership_change"
)

ALLOWED_ROLES = {
    "answer",
    "support",
    "condition",
    "contrast",
    "example",
    "limit",
    "reopening",
    "request",
    "conclusion",
}

ALLOWED_RELATIONS = {
    "sequence",
    "support",
    "cause",
    "condition",
    "contrast",
    "example",
    "return",
    "conclusion",
}

ALLOWED_SOURCE_KINDS = {
    "prompt_grounded_method",
    "approved_knowledge",
    "verified_domain_answer",
    "attributed_source",
    "reviewed_memory",
    "current_session_observation",
    "fictional_invention",
    "compatibility_fallback",
}

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
}


def build_supported_semantic_packet(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize answer meaning before NLO chooses visible language.

    A unit may be structurally realized from subject/predicate/object fields or
    retained as a text-grounded compatibility unit. Both forms keep certainty,
    scope, source, and required meaning inspectable.
    """
    payload = payload or {}
    answer_kind = truncate(str(payload.get("answer_kind") or "ordinary_answer"), 120)
    certainty = truncate(str(payload.get("certainty") or "provisional"), 80)
    scope = truncate(str(payload.get("scope") or "current_prompt_only"), 240)
    packet_refs = _text_list(payload.get("source_refs"), limit=30, width=240)
    fallback_text = truncate(str(payload.get("fallback_text") or ""), 5000).strip()
    units: list[dict[str, Any]] = []
    for index, raw in enumerate(payload.get("units") or []):
        if not isinstance(raw, dict):
            continue
        unit = _normalize_unit(
            raw,
            index=index,
            packet_certainty=certainty,
            packet_scope=scope,
            packet_refs=packet_refs,
        )
        if unit:
            units.append(unit)

    structured_count = sum(1 for item in units if item["realization_mode"] == "structured")
    fallback_count = sum(1 for item in units if item["realization_mode"] == "text_grounded")
    lexical_entry_count = sum(
        int((item.get("lexical_semantics") or {}).get("entry_count") or 0)
        for item in units
    )
    available_lexical_entry_count = sum(
        int((item.get("lexical_semantics") or {}).get("available_entry_count") or 0)
        for item in units
    )
    required_ids = [str(item["id"]) for item in units if item.get("required") is True]
    signature = list(
        dict.fromkeys(
            marker
            for item in units
            for marker in item.get("meaning_keys") or []
            if marker
        )
    )
    return {
        "status": "supported_semantic_packet_ready" if units else "supported_semantic_packet_needs_meaning",
        "version": "v1_supported_semantic_handoff",
        "answer_kind": answer_kind,
        "certainty": certainty,
        "scope": scope,
        "units": units,
        "required_unit_ids": required_ids,
        "meaning_signature": signature,
        "structured_unit_count": structured_count,
        "text_grounded_unit_count": fallback_count,
        "lexical_semantic_entry_count": lexical_entry_count,
        "available_lexical_semantic_entry_count": available_lexical_entry_count,
        "formation_mode": "structured" if structured_count else "text_grounded" if fallback_count else "empty",
        "fallback_text": fallback_text,
        "compatibility_fallback_available": bool(fallback_text),
        "expression_mode": truncate(
            str(payload.get("expression_mode") or "supported_surface_handoff"),
            120,
        ),
        "source_wording_is_surface_requirement": (
            payload.get("source_wording_is_surface_requirement") is True
        ),
        "original_expression_required": (
            payload.get("original_expression_required") is True
        ),
        "source_refs": list(dict.fromkeys([*packet_refs, *(ref for item in units for ref in item["source_refs"])]))[:40],
        "all_units_supported": all(item.get("supported") is True for item in units),
        "fact_generation_allowed": False,
        "meaning_change_allowed": False,
        "coordinated_expression_contract_active": True,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": SUPPORTED_SEMANTICS_BOUNDARY,
        **GUARDS,
    }


def semantic_units_for_formation(packet: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return only supported units that NLO may hand to language formation."""
    if not isinstance(packet, dict) or packet.get("status") != "supported_semantic_packet_ready":
        return []
    return [
        {
            **item,
            "kind": "supported_semantic_unit",
        }
        for item in packet.get("units") or []
        if isinstance(item, dict) and item.get("supported") is True
    ][:16]


def build_text_supported_semantic_packet(
    text: str,
    *,
    answer_kind: str,
    source_kind: str,
    source_refs: list[str] | None = None,
    certainty: str = "provisional",
    scope: str = "current_prompt_only",
) -> dict[str, Any]:
    """Turn already-supported visible content into an inspectable NLO handoff.

    This helper does not infer new facts. It preserves the supplied content as
    source-bound semantic units so NLO can vary expression without losing the
    answer, qualification, contrast, limit, or conclusion that another organ
    already established.
    """
    normalized = truncate(str(text or "").strip(), 5000)
    parts = [
        truncate(" ".join(item.split()), 1200)
        for item in re.split(r"(?<=[.!?])\s+|\n+", normalized)
        if item.strip()
    ][:16]
    units: list[dict[str, Any]] = []
    for index, part in enumerate(parts):
        lower = part.lower()
        if re.match(r"^(?:however|but|by contrast|on the other hand|still)\b", lower):
            role, relation = "contrast", "contrast"
        elif re.match(r"^(?:if|when|unless|in that case)\b", lower):
            role, relation = "condition", "condition"
        elif re.match(r"^(?:for example|for instance|as an example)\b", lower):
            role, relation = "example", "example"
        elif re.match(r"^(?:a limit|the limit|this does not|it does not|that does not)\b", lower):
            role, relation = "limit", "contrast"
        elif re.match(r"^(?:overall|taken together|in short|therefore|so)\b", lower):
            role, relation = "conclusion", "conclusion"
        else:
            role, relation = ("answer", "sequence") if index == 0 else ("support", "support")
        units.append(
            {
                "id": f"{answer_kind}_{index + 1}",
                "role": role,
                "relation": relation,
                "text": part,
                "required": True,
                "supported": True,
                "source_kind": source_kind,
                "source_refs": source_refs or [],
                "certainty": certainty,
                "scope": scope,
            }
        )
    return build_supported_semantic_packet(
        {
            "answer_kind": answer_kind,
            "certainty": certainty,
            "scope": scope,
            "source_refs": source_refs or [],
            "fallback_text": normalized,
            "units": units,
        }
    )


def _normalize_unit(
    raw: dict[str, Any],
    *,
    index: int,
    packet_certainty: str,
    packet_scope: str,
    packet_refs: list[str],
) -> dict[str, Any] | None:
    text = truncate(" ".join(str(raw.get("text") or "").split()), 1200).strip()
    subject = truncate(" ".join(str(raw.get("subject") or "").split()), 360).strip()
    predicate = truncate(" ".join(str(raw.get("predicate") or raw.get("verb") or "").split()), 240).strip()
    obj = truncate(" ".join(str(raw.get("object") or raw.get("complement") or "").split()), 800).strip()
    mood = truncate(str(raw.get("mood") or "declarative"), 40).lower()
    structured = bool(predicate and (subject or mood == "imperative"))
    if not text and not structured:
        return None
    role = str(raw.get("role") or "answer")
    if role not in ALLOWED_ROLES:
        role = "answer"
    relation = str(raw.get("relation") or ("sequence" if index == 0 else "support"))
    if relation not in ALLOWED_RELATIONS:
        relation = "support"
    source_kind = str(raw.get("source_kind") or ("prompt_grounded_method" if structured else "compatibility_fallback"))
    if source_kind not in ALLOWED_SOURCE_KINDS:
        source_kind = "compatibility_fallback"
    refs = _text_list(raw.get("source_refs"), limit=20, width=240) or packet_refs
    lexical_semantics = build_lexical_semantic_set(
        {
            "entries": raw.get("lexical_semantics") or [],
        }
    )
    lexical_choices = _lexical_choices(raw.get("lexical_choices"))
    for field in ("subject", "predicate", "object", "qualifier"):
        available_forms = available_lexical_forms(lexical_semantics, field)
        if available_forms:
            lexical_choices[field] = list(
                dict.fromkeys([*lexical_choices.get(field, []), *available_forms])
            )
    meaning_keys = _text_list(raw.get("meaning_keys"), limit=20, width=120)
    if not meaning_keys:
        meaning_keys = [
            value
            for value in (
                truncate(subject.lower(), 120),
                truncate(predicate.lower(), 120),
                truncate(obj.lower(), 120),
            )
            if value
        ]
    return {
        "id": truncate(str(raw.get("id") or f"semantic_{index + 1}"), 120),
        "role": role,
        "relation": relation,
        "required": raw.get("required") is not False,
        "supported": raw.get("supported") is not False,
        "realization_mode": "structured" if structured else "text_grounded",
        "text": text,
        "subject": subject,
        "subject_number": truncate(
            str(raw.get("subject_number") or ""),
            20,
        ).lower(),
        "preserve_subject_case": (
            raw.get("preserve_subject_case") is True
            if "preserve_subject_case" in raw
            else None
        ),
        "predicate": predicate,
        "object": obj,
        "mood": mood,
        "tense": truncate(str(raw.get("tense") or "present"), 40).lower(),
        "aspect": truncate(str(raw.get("aspect") or "simple"), 40).lower(),
        "voice": truncate(str(raw.get("voice") or "active"), 40).lower(),
        "modality": truncate(str(raw.get("modality") or ""), 40).lower(),
        "polarity": truncate(str(raw.get("polarity") or "positive"), 40).lower(),
        "condition": truncate(" ".join(str(raw.get("condition") or "").split()), 600),
        "reason": truncate(" ".join(str(raw.get("reason") or "").split()), 600),
        "contrast": truncate(" ".join(str(raw.get("contrast") or "").split()), 600),
        "example": truncate(" ".join(str(raw.get("example") or "").split()), 600),
        "qualifier": truncate(" ".join(str(raw.get("qualifier") or "").split()), 240),
        "lexical_choices": lexical_choices,
        "lexical_semantics": lexical_semantics,
        "meaning_keys": meaning_keys,
        "certainty": truncate(str(raw.get("certainty") or packet_certainty), 80),
        "scope": truncate(str(raw.get("scope") or packet_scope), 240),
        "source_kind": source_kind,
        "source_refs": refs,
        "origin_packet_id": truncate(str(raw.get("origin_packet_id") or ""), 120),
        "origin_unit_id": truncate(str(raw.get("origin_unit_id") or ""), 120),
        "origin_source_class": truncate(
            str(raw.get("origin_source_class") or ""),
            80,
        ),
        "obligation_ids": _text_list(
            raw.get("obligation_ids"),
            limit=20,
            width=120,
        ),
        "response_functions": _text_list(
            raw.get("response_functions"),
            limit=12,
            width=80,
        ),
        "ownership_validated": raw.get("ownership_validated") is True,
        "selection_reasons": _text_list(
            raw.get("selection_reasons"),
            limit=12,
            width=120,
        ),
        "exactness_lock": raw.get("exactness_lock") is True,
        "exactness_reason": truncate(
            str(raw.get("exactness_reason") or ""),
            120,
        ),
        "required_terms": _text_list(
            raw.get("required_terms"),
            limit=20,
            width=240,
        ),
        "source_wording_required": raw.get("source_wording_required") is True,
        "knowledge_field": truncate(
            str(raw.get("knowledge_field") or ""),
            120,
        ),
        "origin_concept_id": raw.get("origin_concept_id"),
        "origin_concept_key": truncate(
            str(raw.get("origin_concept_key") or ""),
            180,
        ),
        "meaning_change_allowed": False,
    }


def _lexical_choices(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    allowed_fields = {"subject", "predicate", "object", "qualifier"}
    result: dict[str, list[str]] = {}
    for field, choices in value.items():
        if str(field) not in allowed_fields:
            continue
        normalized = _text_list(choices, limit=8, width=800)
        if normalized:
            result[str(field)] = list(dict.fromkeys(normalized))
    return result


def _text_list(value: Any, *, limit: int, width: int) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [truncate(str(item).strip(), width) for item in value if str(item).strip()][:limit]
