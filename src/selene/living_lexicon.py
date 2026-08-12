from __future__ import annotations

import json
import re
import sqlite3
from hashlib import sha256
from typing import Any

from .language_teaching_shelf import list_language_teaching_items
from .lexical_semantics import ALLOWED_FIELDS, build_lexical_semantic_set
from .registry import truncate


LIVING_LEXICON_BOUNDARY = (
    "derived_reviewed_language_resource_only_no_dictionary_dump_memory_identity_"
    "personality_governance_authority_fact_generation_or_source_imitation"
)
LEXICAL_FIELDS = ("subject", "predicate", "object", "qualifier")

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


# These entries operationalize equivalences already supported by the named
# reviewed language lessons. They are deliberately small. Reviewed vocabulary
# is not treated as a bag of synonyms merely because its terms share a lesson.
REVIEWED_LANGUAGE_SURFACE_ENTRIES: dict[str, tuple[dict[str, Any], ...]] = {
    "answer_then_expand": (
        {
            "id": "living_answer_first_start",
            "field": "predicate",
            "lemma": "start with",
            "forms": ["start with", "begin with", "lead with"],
            "sense": "place the supported direct answer or conclusion before optional expansion",
            "part_of_speech": "transitive_verb_phrase",
            "grammatical_behavior": [
                "imperative-compatible",
                "takes a supported answer, conclusion, or prerequisite as its object",
            ],
            "registers": ["ordinary", "planning", "technical"],
            "collocations": ["direct answer", "conclusion", "main result", "prerequisite"],
            "near_concepts": ["expand on", "return to", "finish with"],
            "distinctions": [
                "starting with the answer controls order; it does not remove required support or qualifications"
            ],
        },
    ),
    "lexical_variation": (
        {
            "id": "living_preserve_supported_meaning",
            "field": "predicate",
            "lemma": "preserve",
            "forms": ["preserve", "keep"],
            "sense": "retain supported meaning or structure without changing it",
            "part_of_speech": "transitive_verb",
            "grammatical_behavior": [
                "takes the retained meaning or structure as its object",
                "inflects as an ordinary verb",
            ],
            "registers": ["ordinary", "technical", "reflective"],
            "collocations": ["meaning", "structure", "context", "thread", "distinction"],
            "near_concepts": ["copy", "freeze", "defend"],
            "distinctions": [
                "preserving supported meaning does not require copying wording or defending a claim against correction"
            ],
        },
    ),
    "comparison_dimension_control": (
        {
            "id": "living_choose_supported_option",
            "field": "predicate",
            "lemma": "choose",
            "forms": ["choose", "select"],
            "sense": "identify one supported option for use from an available set",
            "part_of_speech": "transitive_verb",
            "grammatical_behavior": [
                "takes the selected option as its object",
                "does not imply that unsupported alternatives were evaluated",
            ],
            "registers": ["ordinary", "planning", "technical"],
            "collocations": ["option", "route", "method", "candidate", "next step"],
            "near_concepts": ["prefer", "approve", "authorize"],
            "distinctions": [
                "selection identifies an option; it does not grant approval, authority, or universal preference"
            ],
        },
    ),
    "clarify_only_when_material": (
        {
            "id": "living_identify_material_detail",
            "field": "predicate",
            "lemma": "identify",
            "forms": ["identify", "name"],
            "sense": "make the specific supported detail relevant to the current distinction explicit",
            "part_of_speech": "transitive_verb",
            "grammatical_behavior": [
                "takes the supported detail or distinction as its object",
                "does not create a detail that the evidence does not supply",
            ],
            "registers": ["ordinary", "technical", "explanation"],
            "collocations": ["detail", "difference", "constraint", "source", "missing piece"],
            "near_concepts": ["infer", "invent", "diagnose"],
            "distinctions": [
                "naming a supported detail is not inferring an unstated cause or diagnosing a person"
            ],
        },
    ),
}


def living_lexicon_status(conn: sqlite3.Connection) -> dict[str, Any]:
    compiled = _compiled_lexicon(conn)
    entries = compiled["entries"]
    available = [item for item in entries if item.get("available_to_nlo") is True]
    return _with_guards(
        {
            "status": "living_lexicon_ready" if available else "living_lexicon_awaiting_reviewed_language",
            "version": "v1_derived_reviewed_living_lexicon",
            "available_surface_entry_count": len(available),
            "available_surface_form_count": len(
                {
                    _normalized(form)
                    for item in available
                    for form in item.get("forms") or []
                    if _normalized(form)
                }
            ),
            "reviewed_language_lesson_count": compiled["reviewed_language_lesson_count"],
            "reviewed_vocabulary_mention_count": compiled["reviewed_vocabulary_mention_count"],
            "reviewed_vocabulary_term_count": compiled["reviewed_vocabulary_term_count"],
            "reviewed_vocabulary_catalog_entry_count": compiled[
                "reviewed_vocabulary_catalog_entry_count"
            ],
            "reviewed_terms_without_surface_equivalence_count": compiled[
                "reviewed_terms_without_surface_equivalence_count"
            ],
            "approved_knowledge_entry_count": compiled["approved_knowledge_entry_count"],
            "source_counts": _counts(available, "source_kind"),
            "field_counts": _counts(available, "field"),
            "derived_at_query_time": True,
            "database_write_performed": False,
            "dictionary_memorization_used": False,
            "reviewed_terms_are_automatic_synonyms": False,
            "coordinated_expression_contract_active": True,
            "provenance_boundary": LIVING_LEXICON_BOUNDARY,
        }
    )


def list_living_lexicon(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    compiled = _compiled_lexicon(conn)
    field = str(payload.get("field") or "").strip()
    source_kind = str(payload.get("source_kind") or "").strip()
    include_held = payload.get("include_held") is True
    limit = max(1, min(int(payload.get("limit") or 100), 500))
    entries = [
        item
        for item in compiled["entries"]
        if (not field or item.get("field") == field)
        and (not source_kind or item.get("source_kind") == source_kind)
        and (include_held or item.get("available_to_nlo") is True)
    ][:limit]
    return _with_guards(
        {
            "status": "living_lexicon_items_ready",
            "items": entries,
            "item_count": len(entries),
            "include_held": include_held,
            "derived_at_query_time": True,
            "database_write_performed": False,
            "provenance_boundary": LIVING_LEXICON_BOUNDARY,
        }
    )


def query_living_lexicon(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    field = str(payload.get("field") or "").strip()
    if field and field not in ALLOWED_FIELDS:
        raise ValueError(f"unsupported living lexicon field: {field}")
    form = _normalized(payload.get("form") or payload.get("lemma") or "")
    register = _normalized(payload.get("register") or "")
    limit = max(1, min(int(payload.get("limit") or 20), 100))
    compiled = _compiled_lexicon(conn)
    prompt_profile = build_lexical_semantic_set(
        {"entries": payload.get("prompt_grounded_entries") or []}
    )
    prompt_entries = [
        {
            **item,
            "entry_key": f"prompt:{item.get('id')}",
            "source_kind": "prompt_grounded",
            "source_id": "current_turn",
            "exactness_lock": False,
            "availability_basis": "current_turn_prompt_grounding",
            "durable": False,
        }
        for item in prompt_profile.get("entries") or []
    ]
    entries = [*compiled["entries"], *prompt_entries]
    selected: list[dict[str, Any]] = []
    for item in entries:
        if item.get("available_to_nlo") is not True:
            continue
        if field and item.get("field") != field:
            continue
        forms = [_normalized(value) for value in item.get("forms") or []]
        if form and form not in forms and form != _normalized(item.get("lemma") or ""):
            continue
        registers = {_normalized(value) for value in item.get("registers") or []}
        if register and registers and register not in registers:
            continue
        selected.append(item)
        if len(selected) >= limit:
            break
    forms = list(
        dict.fromkeys(
            str(value)
            for item in selected
            for value in item.get("forms") or []
            if str(value).strip()
        )
    )
    return _with_guards(
        {
            "status": "living_lexicon_match_ready" if selected else "living_lexicon_no_supported_match",
            "field": field,
            "requested_form": form,
            "requested_register": register,
            "entries": selected,
            "entry_count": len(selected),
            "forms": forms,
            "prompt_grounded_entry_count": len(prompt_entries),
            "prompt_grounded_entries_persisted": False,
            "selection_basis": "matching understood form, grammatical field, and compatible register",
            "meaning_change_allowed": False,
            "database_write_performed": False,
            "provenance_boundary": LIVING_LEXICON_BOUNDARY,
        }
    )


def enrich_semantic_units_from_living_lexicon(
    conn: sqlite3.Connection,
    units: list[dict[str, Any]],
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    compiled = _compiled_lexicon(conn)
    prompt_profile = build_lexical_semantic_set(
        {"entries": payload.get("prompt_grounded_entries") or []}
    )
    entries = [
        *[item for item in compiled["entries"] if item.get("available_to_nlo") is True],
        *[
            {
                **item,
                "entry_key": f"prompt:{item.get('id')}",
                "source_kind": "prompt_grounded",
                "source_id": "current_turn",
                "availability_basis": "current_turn_prompt_grounding",
                "durable": False,
            }
            for item in prompt_profile.get("entries") or []
            if item.get("available_to_nlo") is True
        ],
    ]
    by_field_form: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for entry in entries:
        for form in entry.get("forms") or []:
            key = (str(entry.get("field") or ""), _normalized(form))
            if key[0] in ALLOWED_FIELDS and key[1]:
                by_field_form.setdefault(key, []).append(entry)

    enriched: list[dict[str, Any]] = []
    selected_keys: list[str] = []
    for raw in units[:16]:
        item = dict(raw)
        if item.get("exactness_lock") is True or str(item.get("text") or "").strip():
            enriched.append(item)
            continue
        choices = {
            str(field): [str(value) for value in values if str(value).strip()]
            for field, values in (item.get("lexical_choices") or {}).items()
            if str(field) in ALLOWED_FIELDS and isinstance(values, (list, tuple))
        }
        refs = [str(value) for value in item.get("living_lexicon_refs") or [] if str(value)]
        for field in LEXICAL_FIELDS:
            base = _normalized(item.get(field) or "")
            if not base:
                continue
            for entry in by_field_form.get((field, base), []):
                entry_key = str(entry.get("entry_key") or entry.get("id") or "")
                if entry_key:
                    refs.append(entry_key)
                    selected_keys.append(entry_key)
                available_forms = (
                    [str(item.get(field) or "").strip()]
                    if entry.get("exactness_lock") is True
                    else [str(value) for value in entry.get("forms") or [] if str(value).strip()]
                )
                choices[field] = list(
                    dict.fromkeys(
                        [
                            *choices.get(field, []),
                            *[value for value in available_forms if value],
                        ]
                    )
                )
        if choices:
            item["lexical_choices"] = choices
        if refs:
            item["living_lexicon_refs"] = list(dict.fromkeys(refs))
        enriched.append(item)

    selected_keys = list(dict.fromkeys(selected_keys))
    return _with_guards(
        {
            "status": "living_lexicon_semantic_units_enriched" if selected_keys else "living_lexicon_no_unit_match",
            "units": enriched,
            "selected_entry_keys": selected_keys,
            "selected_entry_count": len(selected_keys),
            "unit_count": len(enriched),
            "prompt_grounded_entry_count": int(prompt_profile.get("available_entry_count") or 0),
            "prompt_grounded_entries_persisted": False,
            "exactness_locks_respected": True,
            "meaning_change_allowed": False,
            "database_write_performed": False,
            "provenance_boundary": LIVING_LEXICON_BOUNDARY,
        }
    )


def _compiled_lexicon(conn: sqlite3.Connection) -> dict[str, Any]:
    lessons = [
        item
        for item in list_language_teaching_items(conn).get("items") or []
        if isinstance(item, dict) and item.get("available_to_nlo") is True
    ]
    entries: list[dict[str, Any]] = []
    vocabulary_mentions: list[str] = []
    for lesson in lessons:
        lesson_key = str(lesson.get("lesson_key") or "")
        reviewed_terms = _reviewed_vocabulary(lesson)
        vocabulary_mentions.extend(reviewed_terms)
        source_refs = list(
            dict.fromkeys(
                [
                    *[str(value) for value in lesson.get("source_refs") or [] if str(value)],
                    f"language_lesson:{lesson_key}",
                ]
            )
        )
        for term in reviewed_terms:
            entries.append(
                {
                    "id": f"reviewed_term_{sha256(term.lower().encode('utf-8')).hexdigest()[:12]}",
                    "entry_key": (
                        f"language:{lesson_key}:reviewed_term:"
                        f"{sha256(term.lower().encode('utf-8')).hexdigest()[:12]}"
                    ),
                    "field": "",
                    "lemma": term,
                    "forms": [term],
                    "sense": str((lesson.get("guidance") or {}).get("concept") or lesson.get("purpose") or ""),
                    "part_of_speech": "",
                    "grammatical_behavior": [],
                    "registers": [],
                    "collocations": [],
                    "near_concepts": [],
                    "distinctions": [],
                    "concept_refs": [f"language_lesson:{lesson_key}"],
                    "understanding_state": "reviewed_language_guidance",
                    "source_refs": source_refs,
                    "available_to_nlo": False,
                    "available_for_reference": True,
                    "held_reasons": [
                        "no_explicit_grammatical_behavior",
                        "no_reviewed_surface_equivalence_set",
                    ],
                    "source_kind": "reviewed_language_term_catalog",
                    "source_id": lesson_key,
                    "exactness_lock": True,
                    "availability_basis": "reviewed term catalog only",
                    "durable": True,
                    "status": "reviewed_term_awaiting_lexical_specification",
                }
            )
        for raw in REVIEWED_LANGUAGE_SURFACE_ENTRIES.get(lesson_key, ()):
            profile = build_lexical_semantic_set(
                {
                    "entries": [
                        {
                            **raw,
                            "concept_refs": [
                                *[str(value) for value in raw.get("concept_refs") or [] if str(value)],
                                f"language_lesson:{lesson_key}",
                            ],
                            "understanding_state": "reviewed_language_guidance",
                            "source_refs": source_refs,
                        }
                    ]
                }
            )
            for item in profile.get("entries") or []:
                entries.append(
                    {
                        **item,
                        "entry_key": f"language:{lesson_key}:{item.get('id')}",
                        "source_kind": "reviewed_language_guidance",
                        "source_id": lesson_key,
                        "exactness_lock": False,
                        "availability_basis": "completed reviewed language lifecycle",
                        "durable": True,
                    }
                )

    knowledge_entries = _approved_knowledge_entries(conn)
    entries.extend(knowledge_entries)
    unique_terms = {_normalized(value) for value in vocabulary_mentions if _normalized(value)}
    surface_terms = {
        _normalized(value)
        for item in entries
        if item.get("source_kind") == "reviewed_language_guidance"
        and item.get("available_to_nlo") is True
        for value in item.get("forms") or []
        if _normalized(value)
    }
    return {
        "entries": entries,
        "reviewed_language_lesson_count": len(lessons),
        "reviewed_vocabulary_mention_count": len(vocabulary_mentions),
        "reviewed_vocabulary_term_count": len(unique_terms),
        "reviewed_vocabulary_catalog_entry_count": sum(
            1 for item in entries if item.get("source_kind") == "reviewed_language_term_catalog"
        ),
        "reviewed_terms_without_surface_equivalence_count": len(unique_terms - surface_terms),
        "approved_knowledge_entry_count": len(knowledge_entries),
    }


def _approved_knowledge_entries(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT id, concept_key, payload_json, source_refs
        FROM selene_comprehension_concepts
        WHERE state = 'approved_knowledge_resource'
          AND review_status = 'approved_for_knowledge_use'
          AND chat_use_permission = 'available_as_knowledge_resource'
        ORDER BY id
        """
    ).fetchall()
    entries: list[dict[str, Any]] = []
    for row in rows:
        payload = _loads_dict(row["payload_json"])
        raw_entries = payload.get("lexical_entries") or payload.get("lexical_semantics") or []
        if not isinstance(raw_entries, list):
            continue
        refs = _loads_list(row["source_refs"])
        concept_key = str(row["concept_key"] or "")
        profile = build_lexical_semantic_set(
            {
                "entries": [
                    {
                        **raw,
                        "concept_refs": [
                            *[str(value) for value in raw.get("concept_refs") or [] if str(value)],
                            f"approved_knowledge:{concept_key}",
                        ],
                        "understanding_state": "approved_knowledge",
                        "source_refs": [
                            *[str(value) for value in raw.get("source_refs") or [] if str(value)],
                            *refs,
                        ],
                    }
                    for raw in raw_entries
                    if isinstance(raw, dict)
                ]
            }
        )
        for item in profile.get("entries") or []:
            entries.append(
                {
                    **item,
                    "entry_key": f"knowledge:{concept_key}:{item.get('id')}",
                    "source_kind": "approved_knowledge",
                    "source_id": concept_key,
                    "exactness_lock": bool(
                        next(
                            (
                                raw.get("exactness_lock")
                                for raw in raw_entries
                                if isinstance(raw, dict) and str(raw.get("id") or "") == str(item.get("id") or "")
                            ),
                            False,
                        )
                    ),
                    "availability_basis": "approved knowledge resource with explicit lexical metadata",
                    "durable": True,
                }
            )
    return entries


def _reviewed_vocabulary(lesson: dict[str, Any]) -> list[str]:
    blueprint = lesson.get("teaching_blueprint") if isinstance(lesson.get("teaching_blueprint"), dict) else {}
    acquire = blueprint.get("acquire") if isinstance(blueprint.get("acquire"), dict) else {}
    return [
        truncate(" ".join(str(value).split()), 180)
        for value in acquire.get("vocabulary") or []
        if str(value).strip()
    ]


def _counts(items: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for item in items:
        key = str(item.get(field) or "unspecified")
        counts[key] = counts.get(key, 0) + 1
    return [{field: key, "count": value} for key, value in sorted(counts.items())]


def _normalized(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", str(value).lower()))


def _loads_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(str(value or "{}"))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _loads_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    try:
        parsed = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed if str(item).strip()] if isinstance(parsed, list) else []


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
