from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .registry import truncate


KNOWLEDGE_LANGUAGE_GROWTH_BOUNDARY = (
    "approved_understood_teaching_to_language_affordances_only_no_script_identity_memory_governance_or_fact_generation"
)

APPROVED_LIFECYCLE_STATUSES = {
    "approved_by_aleks",
    "approved_under_curriculum_authorization",
    "approved_under_language_capability_authorization",
}

ROLE_FIELDS = (
    ("central_claim", "thesis"),
    ("principles", "support"),
    ("relationships", "support"),
    ("examples", "example"),
    ("counterexamples", "counterexample"),
    ("limits", "limitation"),
)


def knowledge_language_growth_status(conn: sqlite3.Connection) -> dict[str, Any]:
    resources = _compile_resources(conn)
    available = [item for item in resources if item.get("available_to_nlo") is True]
    held = [item for item in resources if item.get("available_to_nlo") is not True]
    return _locked(
        {
            "status": (
                "knowledge_language_growth_ready"
                if available
                else "knowledge_language_growth_awaiting_approved_teaching"
            ),
            "version": "v1_approved_teaching_language_affordances",
            "resource_count": len(resources),
            "available_resource_count": len(available),
            "held_resource_count": len(held),
            "reviewed_vocabulary_term_count": len(
                {
                    _normalize(term)
                    for item in available
                    for term in item.get("reviewed_vocabulary") or []
                    if _normalize(term)
                }
            ),
            "explicit_lexical_entry_count": sum(
                int(item.get("explicit_lexical_entry_count") or 0) for item in available
            ),
            "construction_affordance_counts": _affordance_counts(available),
            "derived_at_query_time": True,
            "teaching_answers_used_as_templates": False,
            "source_wording_imitation_allowed": False,
        }
    )


def list_knowledge_language_resources(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    include_held = payload.get("include_held") is True
    domain = str(payload.get("domain") or "").strip()
    limit = max(1, min(int(payload.get("limit") or 100), 500))
    items = [
        item
        for item in _compile_resources(conn)
        if (include_held or item.get("available_to_nlo") is True)
        and (not domain or str(item.get("domain") or "") == domain)
    ][:limit]
    return _locked(
        {
            "status": "knowledge_language_growth_items_ready",
            "items": items,
            "item_count": len(items),
            "include_held": include_held,
            "derived_at_query_time": True,
        }
    )


def build_knowledge_language_growth(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    comprehension = _dict(payload.get("comprehension_context"))
    knowledge = _dict(comprehension.get("knowledge_context"))
    answer_items = [
        item
        for item in knowledge.get("answer_eligible_items") or []
        if isinstance(item, dict)
    ]
    explicit_ids = {
        _positive_int(value)
        for value in payload.get("concept_ids") or []
        if _positive_int(value) > 0
    }
    selected_ids = {
        _positive_int(item.get("id") or item.get("concept_id"))
        for item in answer_items
        if _positive_int(item.get("id") or item.get("concept_id")) > 0
    } | explicit_ids
    content_seed = truncate(str(payload.get("content_seed") or ""), 5000).strip()
    source_class = str(payload.get("content_source_class") or "")
    resources = [
        item for item in _compile_resources(conn) if int(item.get("concept_id") or 0) in selected_ids
    ]
    available = [item for item in resources if item.get("available_to_nlo") is True]
    item_by_id = {
        _positive_int(item.get("id") or item.get("concept_id")): item
        for item in answer_items
        if _positive_int(item.get("id") or item.get("concept_id")) > 0
    }
    active = bool(
        available
        and content_seed
        and (
            source_class == "approved_knowledge"
            or payload.get("approved_knowledge_selected") is True
            or explicit_ids
        )
    )
    units = (
        _role_labeled_selected_units(content_seed, available, item_by_id)
        if active
        else []
    )
    vocabulary = list(
        dict.fromkeys(
            term
            for item in available
            for term in item.get("reviewed_vocabulary") or []
            if str(term).strip()
        )
    )[:80]
    lexical_keys = list(
        dict.fromkeys(
            key
            for item in available
            for key in item.get("explicit_lexical_entry_keys") or []
            if str(key).strip()
        )
    )[:80]
    affordances = list(
        dict.fromkeys(
            affordance
            for item in available
            for affordance in item.get("construction_affordances") or []
            if str(affordance).strip()
        )
    )
    source_refs = list(
        dict.fromkeys(
            ref
            for item in available
            for ref in item.get("source_refs") or []
            if str(ref).strip()
        )
    )[:50]
    return _locked(
        {
            "status": (
                "knowledge_language_growth_handoff_ready"
                if active and units
                else "knowledge_language_growth_no_relevant_approved_content"
            ),
            "version": "v1_approved_teaching_language_affordances",
            "active": bool(active and units),
            "selected_concept_ids": sorted(selected_ids),
            "available_resource_count": len(available),
            "held_resource_count": len(resources) - len(available),
            "content_units": units,
            "content_unit_count": len(units),
            "available_discourse_roles": list(
                dict.fromkeys(str(item.get("role") or "") for item in units if item.get("role"))
            ),
            "reviewed_vocabulary": vocabulary,
            "reviewed_vocabulary_is_synonym_permission": False,
            "explicit_lexical_entry_keys": lexical_keys,
            "construction_affordances": affordances,
            "construction_affordances_apply_only_to_current_supported_content": True,
            "content_seed_unchanged": True,
            "content_added": False,
            "teaching_answers_used_as_templates": False,
            "source_wording_imitation_allowed": False,
            "source_refs": source_refs,
            "selected_resources": [
                {
                    "concept_id": item.get("concept_id"),
                    "concept_key": item.get("concept_key"),
                    "domain": item.get("domain"),
                    "construction_affordances": item.get("construction_affordances") or [],
                    "source_refs": item.get("source_refs") or [],
                }
                for item in available
            ],
        }
    )


def _compile_resources(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT concept.*, lifecycle.id AS lifecycle_id,
               lifecycle.current_stage AS lifecycle_stage,
               lifecycle.acquire_status, lifecycle.acquire_json,
               lifecycle.integrate_status, lifecycle.integrate_json,
               lifecycle.express_status, lifecycle.express_json,
               lifecycle.approval_status AS lifecycle_approval_status,
               lifecycle.approval_mode AS lifecycle_approval_mode,
               lifecycle.source_refs AS lifecycle_source_refs
        FROM selene_comprehension_concepts AS concept
        LEFT JOIN selene_teaching_lifecycles AS lifecycle
          ON lifecycle.concept_id = concept.id
        ORDER BY concept.id
        """
    ).fetchall()
    resources: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        acquire = _loads_dict(item.get("acquire_json"))
        express = _loads_dict(item.get("express_json"))
        payload = _loads_dict(item.get("payload_json"))
        concept_refs = _loads_list(item.get("source_refs"))
        lifecycle_refs = _loads_list(item.get("lifecycle_source_refs"))
        source_refs = list(dict.fromkeys([*concept_refs, *lifecycle_refs]))
        missing: list[str] = []
        if item.get("state") != "approved_knowledge_resource":
            missing.append("knowledge_not_approved")
        if item.get("review_status") != "approved_for_knowledge_use":
            missing.append("knowledge_review_incomplete")
        if item.get("chat_use_permission") != "available_as_knowledge_resource":
            missing.append("knowledge_not_available_to_chat")
        if not source_refs:
            missing.append("missing_source_provenance")
        if not item.get("lifecycle_id"):
            missing.append("missing_teaching_lifecycle")
        if any(item.get(f"{stage}_status") != "complete" for stage in ("acquire", "integrate", "express")):
            missing.append("acquire_integrate_express_incomplete")
        if item.get("lifecycle_stage") != "approved_knowledge_resource":
            missing.append("lifecycle_not_approved_for_knowledge_use")
        if str(item.get("lifecycle_approval_status") or "") not in APPROVED_LIFECYCLE_STATUSES:
            missing.append("missing_aleks_approval_or_authorization")
        if _dict(express.get("source_parroting_check")).get("passed") is not True:
            missing.append("source_parroting_check_incomplete")
        if _dict(express.get("understanding_evaluation")).get("sufficient") is not True:
            missing.append("understanding_evidence_incomplete")
        if _dict(express.get("education_expression_personality_law")).get("permitted") is not True:
            missing.append("education_expression_personality_law_not_confirmed")
        lexical_entries = payload.get("lexical_entries") or payload.get("lexical_semantics") or []
        lexical_entries = [value for value in lexical_entries if isinstance(value, dict)]
        affordances = _construction_affordances(express)
        resources.append(
            _locked(
                {
                    "status": (
                        "knowledge_language_resource_available"
                        if not missing
                        else "knowledge_language_resource_held"
                    ),
                    "version": "v1_approved_teaching_language_affordances",
                    "concept_id": int(item.get("id") or 0),
                    "concept_key": str(item.get("concept_key") or ""),
                    "title": str(item.get("title") or ""),
                    "domain": str(item.get("domain") or ""),
                    "lifecycle_id": int(item.get("lifecycle_id") or 0) or None,
                    "approval_status": str(item.get("lifecycle_approval_status") or ""),
                    "approval_mode": str(item.get("lifecycle_approval_mode") or ""),
                    "reviewed_vocabulary": _strings(acquire.get("vocabulary"))[:80],
                    "explicit_lexical_entry_count": len(lexical_entries),
                    "explicit_lexical_entry_keys": [
                        f"knowledge:{item.get('concept_key')}:{entry.get('id')}"
                        for entry in lexical_entries
                        if str(entry.get("id") or "").strip()
                    ],
                    "construction_affordances": affordances,
                    "available_to_nlo": not missing,
                    "held_reasons": list(dict.fromkeys(missing)),
                    "source_refs": source_refs[:50],
                    "teaching_answers_exposed_as_templates": False,
                    "personality_instruction_extracted": False,
                }
            )
        )
    return resources


def _construction_affordances(express: dict[str, Any]) -> list[str]:
    affordances: list[str] = []
    checks = (
        (bool(str(express.get("explanation_in_original_language") or "").strip()), "explanation"),
        (bool(_strings(express.get("distinct_examples"))), "distinct_example"),
        (bool(_strings(express.get("analogies"))), "analogy"),
        (bool(_strings(express.get("questions"))), "question"),
        (bool(_strings(express.get("comparisons"))), "comparison"),
        (bool(_strings(express.get("limits"))), "limitation"),
        (bool(_strings(express.get("counterexamples"))), "counterexample"),
        (bool(str(express.get("correction_response") or "").strip()), "correction"),
        (
            bool(str(express.get("natural_conversational_participation") or "").strip()),
            "natural_conversational_participation",
        ),
    )
    for present, name in checks:
        if present:
            affordances.append(name)
    return affordances


def _role_labeled_selected_units(
    content_seed: str,
    resources: list[dict[str, Any]],
    item_by_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    allowed_ids = {int(item.get("concept_id") or 0) for item in resources}
    fields: list[dict[str, Any]] = []
    for concept_id, item in item_by_id.items():
        if concept_id not in allowed_ids:
            continue
        for field, role in ROLE_FIELDS:
            values = [str(item.get(field) or "")] if field == "central_claim" else _strings(item.get(field))
            for value in values:
                if value.strip():
                    fields.append(
                        {
                            "concept_id": concept_id,
                            "field": field,
                            "role": role,
                            "text": truncate(" ".join(value.split()), 900),
                            "normalized": _normalize(value),
                            "source_refs": [str(ref) for ref in item.get("source_refs") or [] if str(ref)],
                        }
                    )
    units: list[dict[str, Any]] = []
    for index, sentence in enumerate(_sentences(content_seed)):
        normalized = _normalize(sentence)
        matched = _best_field_match(normalized, fields)
        role = str((matched or {}).get("role") or ("thesis" if index == 0 else "support"))
        units.append(
            {
                "id": f"knowledge_growth_content_{index + 1}",
                "text": sentence,
                "role": role,
                "source": "approved_knowledge_language_growth",
                "supported": True,
                "concept_id": (matched or {}).get("concept_id"),
                "knowledge_field": str((matched or {}).get("field") or "selected_content_seed"),
                "source_refs": (matched or {}).get("source_refs") or [],
                "text_was_already_selected_for_answer": True,
                "text_generated_by_growth_bridge": False,
            }
        )
    return units


def _best_field_match(normalized: str, fields: list[dict[str, Any]]) -> dict[str, Any] | None:
    exact = next((item for item in fields if item.get("normalized") == normalized), None)
    if exact:
        return exact
    terms = set(normalized.split())
    ranked: list[tuple[float, dict[str, Any]]] = []
    for item in fields:
        field_terms = set(str(item.get("normalized") or "").split())
        if not terms or not field_terms:
            continue
        overlap = len(terms & field_terms) / max(1, len(terms | field_terms))
        if overlap >= 0.72:
            ranked.append((overlap, item))
    return sorted(ranked, key=lambda value: -value[0])[0][1] if ranked else None


def _affordance_counts(resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in resources:
        for affordance in item.get("construction_affordances") or []:
            key = str(affordance)
            counts[key] = counts.get(key, 0) + 1
    return [{"affordance": key, "count": counts[key]} for key in sorted(counts)]


def _sentences(value: str) -> list[str]:
    return [
        truncate(" ".join(item.split()), 900)
        for item in re.split(r"(?<=[.!?])\s+|\n+", value.strip())
        if item.strip()
    ][:20]


def _strings(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [truncate(" ".join(str(item).split()), 1200) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [truncate(" ".join(value.split()), 1200)]
    return []


def _normalize(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", str(value).lower()))


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value or "{}"))
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _loads_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    try:
        parsed = json.loads(str(value or "[]"))
    except (json.JSONDecodeError, TypeError):
        return []
    return [str(item) for item in parsed if str(item).strip()] if isinstance(parsed, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _positive_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _locked(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "meaning_change_allowed": False,
        "fact_generation_allowed": False,
        "certainty_change_allowed": False,
        "evidence_change_allowed": False,
        "source_change_allowed": False,
        "memory_write_active": False,
        "identity_change_allowed": False,
        "personality_change_allowed": False,
        "governance_change_allowed": False,
        "authority_change_allowed": False,
        "training_allowed": False,
        "lora_allowed": False,
        "voice_owns_expression_style": True,
        "database_write_performed": False,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": KNOWLEDGE_LANGUAGE_GROWTH_BOUNDARY,
    }
