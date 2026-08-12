from __future__ import annotations

from typing import Any

from .registry import truncate


LEXICAL_SEMANTICS_BOUNDARY = (
    "sense_grounded_lexical_availability_only_no_dictionary_memorization_fact_"
    "invention_memory_identity_personality_governance_authority_or_voice_change"
)

AVAILABLE_UNDERSTANDING_STATES = {
    "prompt_grounded",
    "approved_knowledge",
    "reviewed_language_guidance",
}

ALLOWED_FIELDS = {"subject", "predicate", "object", "qualifier"}

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


def build_lexical_semantic_set(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize words and phrases as understood sense-bearing options.

    Availability depends on an attributable understanding state. Merely
    supplying a form does not make it available to NLO.
    """
    payload = payload or {}
    entries: list[dict[str, Any]] = []
    for index, raw in enumerate(payload.get("entries") or []):
        if not isinstance(raw, dict):
            continue
        entry = _normalize_entry(raw, index)
        if entry:
            entries.append(entry)
    available = [item for item in entries if item["available_to_nlo"]]
    return {
        "status": "lexical_semantic_set_ready" if entries else "lexical_semantic_set_empty",
        "version": "v1_sense_grounded_lexicon",
        "entries": entries,
        "entry_count": len(entries),
        "available_entry_count": len(available),
        "held_entry_count": len(entries) - len(available),
        "availability_rule": (
            "A form is available only with a declared sense, grammatical behavior, "
            "source provenance, and prompt-grounded or reviewed understanding."
        ),
        "dictionary_memorization_used": False,
        "meaning_change_allowed": False,
        "coordinated_expression_contract_active": True,
        "provenance_boundary": LEXICAL_SEMANTICS_BOUNDARY,
        **GUARDS,
    }


def available_lexical_forms(profile: dict[str, Any] | None, field: str) -> list[str]:
    if field not in ALLOWED_FIELDS or not isinstance(profile, dict):
        return []
    return list(
        dict.fromkeys(
            form
            for item in profile.get("entries") or []
            if isinstance(item, dict)
            and item.get("available_to_nlo") is True
            and item.get("field") == field
            for form in item.get("forms") or []
            if str(form).strip()
        )
    )


def _normalize_entry(raw: dict[str, Any], index: int) -> dict[str, Any] | None:
    field = str(raw.get("field") or "")
    if field not in ALLOWED_FIELDS:
        return None
    lemma = truncate(" ".join(str(raw.get("lemma") or "").split()), 160).strip()
    forms = _texts(raw.get("forms"), 12, 360)
    if lemma and lemma not in forms:
        forms.insert(0, lemma)
    sense = truncate(" ".join(str(raw.get("sense") or "").split()), 500).strip()
    part_of_speech = truncate(str(raw.get("part_of_speech") or ""), 80).strip()
    grammatical_behavior = _texts(raw.get("grammatical_behavior"), 12, 240)
    registers = _texts(raw.get("registers"), 10, 120)
    collocations = _texts(raw.get("collocations"), 20, 180)
    near_concepts = _texts(raw.get("near_concepts"), 20, 180)
    distinctions = _texts(raw.get("distinctions"), 20, 360)
    concept_refs = _texts(raw.get("concept_refs"), 20, 240)
    source_refs = _texts(raw.get("source_refs"), 20, 240)
    understanding_state = truncate(str(raw.get("understanding_state") or "unreviewed"), 80)
    missing: list[str] = []
    if not forms:
        missing.append("forms")
    if not sense:
        missing.append("sense")
    if not part_of_speech:
        missing.append("part_of_speech")
    if not grammatical_behavior:
        missing.append("grammatical_behavior")
    if not source_refs:
        missing.append("source_provenance")
    if understanding_state not in AVAILABLE_UNDERSTANDING_STATES:
        missing.append("approved_understanding")
    available = not missing
    return {
        "id": truncate(str(raw.get("id") or f"lexical_{index + 1}"), 120),
        "field": field,
        "lemma": lemma,
        "forms": forms,
        "sense": sense,
        "part_of_speech": part_of_speech,
        "grammatical_behavior": grammatical_behavior,
        "registers": registers,
        "collocations": collocations,
        "near_concepts": near_concepts,
        "distinctions": distinctions,
        "concept_refs": concept_refs,
        "understanding_state": understanding_state,
        "source_refs": source_refs,
        "available_to_nlo": available,
        "held_reasons": missing,
        "meaning_may_not_change_between_forms": True,
        "personality_effect": "none",
    }


def _texts(value: Any, limit: int, width: int) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return list(
        dict.fromkeys(
            truncate(" ".join(str(item).split()), width)
            for item in value
            if str(item).strip()
        )
    )[:limit]
