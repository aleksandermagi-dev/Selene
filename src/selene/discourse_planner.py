from __future__ import annotations

import json
import re
from copy import deepcopy
from hashlib import sha256
from typing import Any

from .registry import truncate


DISCOURSE_BOUNDARY = (
    "supported_content_organization_only_no_fact_generation_memory_identity_authority_or_hidden_reasoning"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
}

STOP_WORDS = {
    "a", "about", "and", "are", "as", "at", "be", "but", "can", "could", "did", "do", "does",
    "explain", "for", "from", "how", "i", "if", "in", "is", "it", "me", "my", "of", "on", "or",
    "please", "should", "so", "that", "the", "this", "to", "we", "what", "when", "where", "which",
    "who", "why", "will", "with", "would", "you", "your",
}

MAX_CONTENT_UNITS = 30
MAX_SECTIONS = 8
MAX_PARAGRAPHS = 8
MAX_PLANNING_PASSES = 1

SUPPORTED_SECTION_FUNCTIONS = {
    "thesis",
    "correction",
    "explanation",
    "example",
    "analogy",
    "comparison",
    "qualification",
    "counterpressure",
    "return",
    "summary",
    "conclusion",
    "story",
    "dialogue",
    "technical_walkthrough",
}

ELIGIBLE_SOURCE_KINDS = {
    "prompt_grounded_method",
    "approved_knowledge",
    "verified_domain_answer",
    "attributed_source",
    "reviewed_memory",
    "current_session_observation",
    "labeled_inference",
    "fictional_invention",
    "compatibility_fallback",
}

ROLE_TO_SECTION_FUNCTION = {
    "thesis": "thesis",
    "correction": "correction",
    "support": "explanation",
    "explanation": "explanation",
    "assumption": "qualification",
    "example": "example",
    "analogy": "analogy",
    "comparison": "comparison",
    "counterexample": "counterpressure",
    "counterpressure": "counterpressure",
    "limitation": "qualification",
    "qualification": "qualification",
    "reopening": "return",
    "return": "return",
    "summary": "summary",
    "conclusion": "conclusion",
    "story": "story",
    "dialogue": "dialogue",
    "technical_walkthrough": "technical_walkthrough",
}


def build_supported_discourse_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    seed = truncate(str(payload.get("content_seed") or ""), 5000).strip()
    depth = str(payload.get("response_depth") or "standard")
    profile = str(payload.get("expression_profile") or "direct")
    obligations = [item for item in payload.get("response_obligations") or [] if isinstance(item, dict)][:12]
    correction = payload.get("correction_refinement") if isinstance(payload.get("correction_refinement"), dict) else {}
    answer_support = payload.get("answer_support") if isinstance(payload.get("answer_support"), dict) else {}
    thread_braid = payload.get("thread_braid") if isinstance(payload.get("thread_braid"), dict) else {}
    source_holds: list[dict[str, Any]] = []
    units = _content_units(
        payload.get("supported_content_units"),
        seed,
        payload.get("content_seed_metadata") if isinstance(payload.get("content_seed_metadata"), dict) else {},
        payload.get("support_points"),
        payload.get("examples"),
        payload.get("next_steps"),
        answer_support,
        correction,
        source_holds,
    )
    bindings = _bind_obligations(obligations, units)
    uncovered = [
        str(item.get("obligation_id") or "")
        for item in bindings
        if item.get("required") is True and item.get("grounded") is not True
    ]
    paragraphs = _paragraph_plan(depth, units, bindings)
    closure = _closure_plan(units)
    requested_roles = _requested_discourse_roles(payload, obligations)
    unsupported_role_holds = _unsupported_role_holds(requested_roles, units)
    discourse_spine = _build_discourse_spine(
        payload,
        units,
        bindings,
        correction=correction,
        thread_braid=thread_braid,
        unsupported_role_holds=unsupported_role_holds,
    )
    discourse_spine = _apply_local_section_revision(
        discourse_spine,
        units,
        bindings,
        payload.get("section_revision"),
    )
    if (discourse_spine.get("local_revision_receipt") or {}).get("status") == "local_section_revision_applied":
        paragraphs = _paragraphs_from_sections(discourse_spine.get("section_plan") or [])
    held_visible = bool(uncovered or unsupported_role_holds or source_holds)
    stopping_receipt = {
        "status": "terminal_discourse_stop",
        "terminal": True,
        "reason": (
            "unsupported_roles_or_obligations_held_visible"
            if held_visible
            else "supported_closure_reached"
            if str(closure.get("content_unit_id") or "")
            else "supported_content_exhausted"
        ),
        "closure_mode": str(closure.get("mode") or "stop_after_supported_content"),
        "supported_closure_content_unit_id": str(closure.get("content_unit_id") or ""),
        "uncovered_obligation_ids": uncovered,
        "unsupported_role_holds": unsupported_role_holds,
        "source_hold_count": len(source_holds),
        "generation_pass_count": MAX_PLANNING_PASSES,
        "further_generation_allowed": False,
        "forced_closure_added": False,
    }
    return _with_guards(
        {
            "status": "supported_discourse_plan_ready",
            "version": "v2_typed_bounded_section_discourse",
            "response_depth": depth,
            "expression_profile": profile,
            "thesis_unit_id": next((item["id"] for item in units if item["role"] == "thesis"), ""),
            "content_units": units,
            "obligation_bindings": bindings,
            "thread_braid": thread_braid,
            "thread_traversal": thread_braid.get("turn_traversal") or [],
            "thread_obligation_bindings": _thread_obligation_bindings(bindings, obligations),
            "uncovered_obligation_ids": uncovered,
            "all_obligations_grounded": not uncovered,
            "paragraph_plan": paragraphs,
            "closure_plan": closure,
            "discourse_spine": discourse_spine,
            "section_plan": discourse_spine.get("section_plan") or [],
            "unsupported_role_holds": unsupported_role_holds,
            "source_holds": source_holds,
            "stopping_receipt": stopping_receipt,
            "hard_limits": {
                "content_units": MAX_CONTENT_UNITS,
                "sections": MAX_SECTIONS,
                "paragraphs": MAX_PARAGRAPHS,
                "planning_passes": MAX_PLANNING_PASSES,
            },
            "content_generation_allowed": False,
            "unsupported_gaps_must_remain_visible": True,
            "source_refs": _strings(payload.get("source_refs"))[:30],
            "visible_summary_only": True,
            "hidden_chain_of_thought_exposed": False,
            "provenance_boundary": DISCOURSE_BOUNDARY,
        }
    )


def _content_units(
    supported_content_units_value: Any,
    seed: str,
    seed_metadata: dict[str, Any],
    support_points_value: Any,
    examples_value: Any,
    next_steps_value: Any,
    answer_support: dict[str, Any],
    correction: dict[str, Any],
    source_holds: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    raw: list[tuple[str, str, str, dict[str, Any]]] = []
    allowed_roles = set(ROLE_TO_SECTION_FUNCTION)
    for item in supported_content_units_value or []:
        if not isinstance(item, dict) or item.get("supported") is not True:
            continue
        text = truncate(str(item.get("text") or ""), 900).strip()
        role = _normalized_discourse_role(str(item.get("role") or "support"))
        if not text or role not in allowed_roles:
            continue
        source_kind = str(item.get("source_kind") or "compatibility_fallback")
        if source_kind not in ELIGIBLE_SOURCE_KINDS:
            source_holds.append(
                {
                    "content_unit_id": str(item.get("id") or ""),
                    "source_kind": source_kind,
                    "state": "held_before_discourse_planning",
                    "reason": "source_kind_not_eligible_for_supported_discourse",
                    "content_entered_plan": False,
                }
            )
            continue
        raw.append((text, role, str(item.get("source") or "supplied_supported_content"), item))
    for index, sentence in enumerate(_sentences(seed)):
        raw.append((sentence, "thesis" if index == 0 else "support", "supplied_content_seed", seed_metadata))
    for value in _strings(support_points_value):
        raw.append((value, "support", "intelligence_support", {}))
    for value in _strings(examples_value):
        raw.append((value, "example", "supplied_semantic_example", {}))
    for value in _strings(next_steps_value):
        raw.append((value, "conclusion", "intelligence_support", {}))
    for value in _strings(answer_support.get("supporting_claims")):
        raw.append((value, "support", "answer_engine_support", {}))
    for value in _strings(answer_support.get("assumptions")):
        raw.append((value, "assumption", "answer_engine_support", {}))
    for value in _strings(answer_support.get("limitations")):
        raw.append((value, "limitation", "answer_engine_support", {}))
    for value in _strings(answer_support.get("what_would_change_the_answer")):
        raw.append((value, "reopening", "answer_engine_support", {}))
    corrected = truncate(str(correction.get("corrected_meaning") or ""), 300).strip()
    replaced = truncate(str(correction.get("replaced_meaning") or ""), 300).strip()
    if correction.get("detected") is True and corrected:
        text = f"{corrected} rather than {replaced}" if replaced else corrected
        raw.append((text, "correction", "current_session_correction", {}))

    units: list[dict[str, Any]] = []
    seen: set[str] = set()
    used_ids: set[str] = set()
    for text, role, source, metadata in raw:
        normalized = truncate(" ".join(text.split()), 900).strip()
        key = normalized.lower().rstrip(". ")
        if not key or key in seen:
            continue
        seen.add(key)
        preferred_id = truncate(str(metadata.get("id") or ""), 120).strip()
        unit_id = preferred_id if preferred_id and preferred_id not in used_ids else f"content_{len(units) + 1}"
        while unit_id in used_ids:
            unit_id = f"content_{len(units) + 2}"
        used_ids.add(unit_id)
        source_kind = str(metadata.get("source_kind") or _default_source_kind(source))
        units.append(
            {
                "id": unit_id,
                "text": normalized,
                "role": role,
                "source": source,
                "source_kind": source_kind,
                "terms": _terms(normalized),
                "supported": True,
                "source_refs": _strings(metadata.get("source_refs"))[:20],
                "certainty": truncate(str(metadata.get("certainty") or "supported_unspecified"), 80),
                "scope": truncate(str(metadata.get("scope") or "current_response"), 240),
                "relation": truncate(str(metadata.get("relation") or ""), 80),
                "obligation_ids": _strings(metadata.get("obligation_ids"))[:20],
                "response_functions": _strings(metadata.get("response_functions"))[:12],
                "origin_packet_id": truncate(str(metadata.get("origin_packet_id") or ""), 120),
                "origin_unit_id": truncate(str(metadata.get("origin_unit_id") or ""), 120),
                "origin_source_class": truncate(str(metadata.get("origin_source_class") or ""), 80),
                "knowledge_concept_id": metadata.get("concept_id"),
                "knowledge_field": str(metadata.get("knowledge_field") or ""),
                "text_was_already_selected_for_answer": (
                    metadata.get("text_was_already_selected_for_answer") is True
                ),
                "text_generated_by_growth_bridge": (
                    metadata.get("text_generated_by_growth_bridge") is True
                ),
            }
        )
    return units[:MAX_CONTENT_UNITS]


def _normalized_discourse_role(value: str) -> str:
    aliases = {
        "answer": "thesis",
        "condition": "qualification",
        "contrast": "comparison",
        "limit": "limitation",
        "request": "return",
    }
    normalized = str(value or "support").strip().lower().replace("-", "_").replace(" ", "_")
    return aliases.get(normalized, normalized)


def _default_source_kind(source: str) -> str:
    return {
        "intelligence_support": "verified_domain_answer",
        "answer_engine_support": "verified_domain_answer",
        "supplied_semantic_example": "compatibility_fallback",
        "current_session_correction": "current_session_observation",
    }.get(source, "compatibility_fallback")


def _requested_discourse_roles(
    payload: dict[str, Any],
    obligations: list[dict[str, Any]],
) -> list[str]:
    requested = [
        _normalized_section_function(item)
        for item in _strings(payload.get("requested_discourse_roles"))
    ]
    markers = {
        "example": ("example", "illustrate", "instance"),
        "analogy": ("analogy", "analogous"),
        "comparison": ("compare", "comparison", "versus", "difference"),
        "qualification": ("qualification", "caveat", "limit", "limitation"),
        "counterpressure": ("counterexample", "counterpressure", "objection"),
        "return": ("return to", "come back to", "revisit"),
        "summary": ("summary", "summarize", "recap"),
        "conclusion": ("conclusion", "conclude", "next step"),
        "story": ("story", "narrative", "scene"),
        "dialogue": ("dialogue", "conversation between"),
        "technical_walkthrough": ("technical walkthrough", "walkthrough", "step by step"),
    }
    for obligation in obligations:
        for value in obligation.get("requested_response_functions") or []:
            function = _normalized_section_function(str(value))
            if function in SUPPORTED_SECTION_FUNCTIONS:
                requested.append(function)
        source_text = str(obligation.get("source_text") or "").lower()
        for function, terms in markers.items():
            if any(term in source_text for term in terms):
                requested.append(function)
    return list(dict.fromkeys(item for item in requested if item in SUPPORTED_SECTION_FUNCTIONS))


def _normalized_section_function(value: str) -> str:
    aliases = {
        "support": "explanation",
        "reason": "explanation",
        "limitation": "qualification",
        "counterexample": "counterpressure",
        "reopening": "return",
        "technical": "technical_walkthrough",
    }
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return aliases.get(normalized, normalized)


def _unsupported_role_holds(
    requested_roles: list[str],
    units: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    available = {
        ROLE_TO_SECTION_FUNCTION.get(str(item.get("role") or "support"), "explanation")
        for item in units
    }
    return [
        {
            "role": role,
            "state": "held_no_supported_unit",
            "reason": "requested_discourse_role_has_no_supported_content_unit",
            "content_added": False,
        }
        for role in requested_roles
        if role not in available
    ]


def _build_discourse_spine(
    payload: dict[str, Any],
    units: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    *,
    correction: dict[str, Any],
    thread_braid: dict[str, Any],
    unsupported_role_holds: list[dict[str, Any]],
) -> dict[str, Any]:
    sections = _section_plan(units, bindings)
    thesis = next((item for item in units if item.get("role") == "thesis"), units[0] if units else {})
    controlling_question = next(
        (
            str(item.get("source_text") or "")
            for item in payload.get("response_obligations") or []
            if isinstance(item, dict) and "?" in str(item.get("source_text") or "")
        ),
        "",
    )
    source_compatibility = (
        deepcopy(payload.get("source_compatibility"))
        if isinstance(payload.get("source_compatibility"), dict)
        else {}
    )
    source_compatibility["selected_source_class"] = str(payload.get("selected_source_class") or "")
    release_alignment = (
        deepcopy(payload.get("release_alignment"))
        if isinstance(payload.get("release_alignment"), dict)
        else {}
    )
    for section in sections:
        section["correction_state"] = deepcopy(correction)
        section["source_compatibility"] = deepcopy(source_compatibility)
        section["release_alignment"] = deepcopy(release_alignment)
        section["section_fingerprint"] = _section_fingerprint(section)
    spine = {
        "status": "typed_discourse_spine_ready" if sections else "typed_discourse_spine_no_supported_sections",
        "version": "v1_bounded_purpose_thesis_section_spine",
        "purpose": truncate(str(payload.get("discourse_purpose") or "answer_supported_request"), 240),
        "audience": truncate(str(payload.get("audience") or "current_interlocutor"), 120),
        "register": truncate(str(payload.get("register") or "conversational"), 120),
        "requested_form": truncate(str(payload.get("requested_form") or "bounded_response"), 120),
        "thesis": {
            "content_unit_id": str(thesis.get("id") or ""),
            "text": str(thesis.get("text") or ""),
            "supported": bool(thesis),
        },
        "controlling_question": controlling_question,
        "section_plan": sections,
        "unsupported_role_holds": unsupported_role_holds,
        "correction_state": deepcopy(correction),
        "thread_traversal": deepcopy(thread_braid.get("turn_traversal") or []),
        "source_compatibility": source_compatibility,
        "release_alignment": release_alignment,
        "hard_limits": {
            "content_units": MAX_CONTENT_UNITS,
            "sections": MAX_SECTIONS,
            "paragraphs": MAX_PARAGRAPHS,
            "planning_passes": MAX_PLANNING_PASSES,
        },
        "planning_pass_count": MAX_PLANNING_PASSES,
        "recursive_generation_allowed": False,
        "filler_generation_allowed": False,
        "meaning_change_allowed": False,
    }
    plan_id = "discourse_plan:" + _fingerprint(
        {
            "purpose": spine["purpose"],
            "thesis": spine["thesis"],
            "sections": sections,
            "unsupported_role_holds": unsupported_role_holds,
        }
    )[:20]
    spine["plan_id"] = plan_id
    spine["lineage"] = {
        "root_plan_id": plan_id,
        "parent_plan_id": "",
        "revision_number": 1,
    }
    spine["local_revision_receipt"] = {
        "status": "no_local_section_revision_requested",
        "target_section_id": "",
        "revision_pass_count": 0,
        "conversation_reset": False,
        "other_sections_changed": False,
    }
    return spine


def _section_plan(
    units: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: list[tuple[str, list[dict[str, Any]]]] = []
    for unit in units:
        function = ROLE_TO_SECTION_FUNCTION.get(str(unit.get("role") or "support"), "explanation")
        if grouped and grouped[-1][0] == function:
            grouped[-1][1].append(unit)
        elif len(grouped) < MAX_SECTIONS:
            grouped.append((function, [unit]))
        else:
            grouped[-1][1].append(unit)
    sections: list[dict[str, Any]] = []
    for index, (function, group) in enumerate(grouped, start=1):
        section_id = f"section:{index}:{function}"
        section = _section_receipt(
            section_id,
            index,
            function,
            [str(item.get("id") or "") for item in group],
            units,
            bindings,
            transition_relation=("none" if index == 1 else str(group[0].get("relation") or "sequence")),
        )
        sections.append(section)
    return sections


def _section_receipt(
    section_id: str,
    index: int,
    function: str,
    content_unit_ids: list[str],
    units: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    *,
    transition_relation: str,
    parent_section_fingerprint: str = "",
    revision_number: int = 1,
) -> dict[str, Any]:
    unit_by_id = {str(item.get("id") or ""): item for item in units}
    selected = [unit_by_id[item] for item in content_unit_ids if item in unit_by_id]
    obligation_ids = list(
        dict.fromkeys(
            [
                str(binding.get("obligation_id") or "")
                for binding in bindings
                if set(content_unit_ids) & {str(item) for item in binding.get("content_unit_ids") or []}
            ]
            + [
                str(obligation_id)
                for item in selected
                for obligation_id in item.get("obligation_ids") or []
            ]
        )
    )
    obligation_ids = [item for item in obligation_ids if item]
    thread_bindings = [
        {
            "obligation_id": str(binding.get("obligation_id") or ""),
            "thread_id": str(binding.get("thread_id") or ""),
            "thread_action": str(binding.get("thread_action") or ""),
            "thread_traversal_index": int(binding.get("thread_traversal_index") or 0),
            "dependency_thread_id": str(binding.get("dependency_thread_id") or ""),
        }
        for binding in bindings
        if str(binding.get("thread_id") or "")
        and set(content_unit_ids) & {str(item) for item in binding.get("content_unit_ids") or []}
    ]
    source_bindings = _unique_dicts(
        [
            {
                "source_kind": str(item.get("source_kind") or "compatibility_fallback"),
                "source_refs": [str(ref) for ref in item.get("source_refs") or []],
            }
            for item in selected
        ]
    )
    epistemic_bindings = _unique_dicts(
        [
            {
                "certainty": str(item.get("certainty") or "supported_unspecified"),
                "scope": str(item.get("scope") or "current_response"),
            }
            for item in selected
        ]
    )
    section = {
        "section_id": section_id,
        "index": index,
        "function": function,
        "content_unit_ids": content_unit_ids,
        "obligation_ids": obligation_ids,
        "thread_bindings": thread_bindings,
        "dependency_thread_ids": list(
            dict.fromkeys(
                str(item.get("dependency_thread_id") or "")
                for item in thread_bindings
                if str(item.get("dependency_thread_id") or "")
            )
        ),
        "source_bindings": source_bindings,
        "epistemic_bindings": epistemic_bindings,
        "transition_relation": transition_relation,
        "completeness_state": (
            "complete_from_supported_units" if len(selected) == len(content_unit_ids) and selected else "held_missing_supported_units"
        ),
        "unsupported_role_hold": False,
        "parent_section_fingerprint": parent_section_fingerprint,
        "revision_number": revision_number,
    }
    section["section_fingerprint"] = _section_fingerprint(section)
    return section


def _apply_local_section_revision(
    spine: dict[str, Any],
    units: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    revision_value: Any,
) -> dict[str, Any]:
    if not isinstance(revision_value, dict):
        return spine
    prior = revision_value.get("prior_discourse_spine")
    target_id = str(revision_value.get("target_section_id") or "")
    replacement_ids = list(
        dict.fromkeys(str(item) for item in revision_value.get("replacement_content_unit_ids") or [] if str(item))
    )[:MAX_CONTENT_UNITS]
    if not isinstance(prior, dict) or not target_id or not replacement_ids:
        spine["local_revision_receipt"] = {
            "status": "local_section_revision_held_invalid_request",
            "target_section_id": target_id,
            "revision_pass_count": 0,
            "conversation_reset": False,
            "other_sections_changed": False,
        }
        return spine
    unit_by_id = {str(item.get("id") or ""): item for item in units}
    if any(item not in unit_by_id for item in replacement_ids):
        spine["local_revision_receipt"] = {
            "status": "local_section_revision_held_unsupported_replacement",
            "target_section_id": target_id,
            "revision_pass_count": 0,
            "conversation_reset": False,
            "other_sections_changed": False,
        }
        return spine
    prior_sections = [deepcopy(item) for item in prior.get("section_plan") or [] if isinstance(item, dict)]
    target = next((item for item in prior_sections if str(item.get("section_id") or "") == target_id), None)
    if not target or len(prior_sections) > MAX_SECTIONS:
        spine["local_revision_receipt"] = {
            "status": "local_section_revision_held_unknown_target",
            "target_section_id": target_id,
            "revision_pass_count": 0,
            "conversation_reset": False,
            "other_sections_changed": False,
        }
        return spine
    old_fingerprint = str(target.get("section_fingerprint") or "")
    retired_content_unit_ids = [
        str(item) for item in target.get("content_unit_ids") or [] if str(item)
    ]
    replacement_function = ROLE_TO_SECTION_FUNCTION.get(
        str(unit_by_id[replacement_ids[0]].get("role") or "support"),
        str(target.get("function") or "explanation"),
    )
    replacement = _section_receipt(
        target_id,
        int(target.get("index") or 1),
        replacement_function,
        replacement_ids,
        units,
        bindings,
        transition_relation=str(target.get("transition_relation") or "sequence"),
        parent_section_fingerprint=old_fingerprint,
        revision_number=int(target.get("revision_number") or 1) + 1,
    )
    replacement["correction_state"] = deepcopy(target.get("correction_state") or {})
    replacement["source_compatibility"] = deepcopy(target.get("source_compatibility") or {})
    replacement["release_alignment"] = deepcopy(target.get("release_alignment") or {})
    replacement["section_fingerprint"] = _section_fingerprint(replacement)
    revised_sections = [replacement if str(item.get("section_id") or "") == target_id else item for item in prior_sections]
    prior_plan_id = str(prior.get("plan_id") or "")
    prior_lineage = prior.get("lineage") if isinstance(prior.get("lineage"), dict) else {}
    root_plan_id = str(prior_lineage.get("root_plan_id") or prior_plan_id)
    new_plan_id = "discourse_plan:" + _fingerprint(
        {"parent_plan_id": prior_plan_id, "sections": revised_sections}
    )[:20]
    unchanged_ids = [
        str(item.get("section_id") or "")
        for item in prior_sections
        if str(item.get("section_id") or "") != target_id
    ]
    result = {
        **spine,
        "plan_id": new_plan_id,
        "section_plan": revised_sections,
        "lineage": {
            "root_plan_id": root_plan_id,
            "parent_plan_id": prior_plan_id,
            "revision_number": int(prior_lineage.get("revision_number") or 1) + 1,
        },
        "local_revision_receipt": {
            "status": "local_section_revision_applied",
            "target_section_id": target_id,
            "revision_reason": truncate(str(revision_value.get("revision_reason") or "supported_local_revision"), 240),
            "root_plan_id": root_plan_id,
            "parent_plan_id": prior_plan_id,
            "prior_section_fingerprint": old_fingerprint,
            "revised_section_fingerprint": replacement["section_fingerprint"],
            "unchanged_section_ids": unchanged_ids,
            "unchanged_section_fingerprints": {
                str(item.get("section_id") or ""): str(item.get("section_fingerprint") or "")
                for item in prior_sections
                if str(item.get("section_id") or "") != target_id
            },
            "retired_target_content_unit_ids": retired_content_unit_ids,
            "replacement_content_unit_ids": replacement_ids,
            "revision_pass_count": 1,
            "conversation_reset": False,
            "other_sections_changed": False,
            "meaning_change_allowed_outside_target": False,
        },
    }
    return result


def _paragraphs_from_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "index": index,
            "role": str(section.get("function") or "development"),
            "content_unit_ids": [str(item) for item in section.get("content_unit_ids") or []],
            "transition": str(section.get("transition_relation") or "sequence"),
            "section_id": str(section.get("section_id") or ""),
        }
        for index, section in enumerate(sections[:MAX_PARAGRAPHS], start=1)
        if section.get("content_unit_ids")
    ]


def _unique_dicts(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in values:
        marker = json.dumps(item, sort_keys=True, separators=(",", ":"))
        if marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result


def _fingerprint(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _section_fingerprint(section: dict[str, Any]) -> str:
    return _fingerprint(
        {
            key: value
            for key, value in section.items()
            if key not in {"section_fingerprint", "parent_section_fingerprint"}
        }
    )


def _bind_obligations(obligations: list[dict[str, Any]], units: list[dict[str, Any]]) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for index, obligation in enumerate(obligations):
        obligation_id = str(obligation.get("id") or f"obligation_{index + 1}")
        kind = str(obligation.get("kind") or "direct_request")
        required = obligation.get("required") is not False
        expected = {
            str(item).lower()
            for item in obligation.get("coverage_terms") or _terms(str(obligation.get("source_text") or ""))
            if str(item).strip()
        }
        candidates: list[tuple[float, dict[str, Any]]] = []
        for unit in units:
            if kind == "correction_update" and unit.get("role") != "correction":
                continue
            if kind != "correction_update" and unit.get("role") == "correction":
                continue
            overlap = expected & set(unit.get("terms") or [])
            score = len(overlap) / len(expected) if expected else 0.0
            role_bonus = _role_bonus(
                kind,
                str(unit.get("role") or ""),
                str(unit.get("text") or "").lower(),
                str(obligation.get("source_text") or "").lower(),
            )
            semantic_bonus = _semantic_binding_bonus(
                kind,
                str(unit.get("text") or "").lower(),
                str(obligation.get("source_text") or "").lower(),
            )
            declared_obligation_bonus = (
                2.0
                if obligation_id in {str(item) for item in unit.get("obligation_ids") or []}
                else 0.0
            )
            requested_functions = {
                _normalized_section_function(str(item))
                for item in obligation.get("requested_response_functions") or []
            }
            unit_function = ROLE_TO_SECTION_FUNCTION.get(str(unit.get("role") or "support"), "explanation")
            declared_function_bonus = 1.0 if unit_function in requested_functions else 0.0
            score += role_bonus + semantic_bonus + declared_obligation_bonus + declared_function_bonus
            if (
                overlap
                or role_bonus >= 0.75
                or semantic_bonus >= 0.75
                or declared_obligation_bonus
                or declared_function_bonus
                or (not expected and score > 0)
            ):
                candidates.append((score, unit))
        candidates.sort(key=lambda item: (-item[0], str(item[1].get("id") or "")))
        selected = [item for _, item in candidates[:2]]
        grounded = bool(selected)
        bindings.append(
            {
                "obligation_id": obligation_id,
                "kind": kind,
                "required": required,
                "source_text": truncate(str(obligation.get("source_text") or ""), 480),
                "content_unit_ids": [str(item.get("id") or "") for item in selected],
                "grounded": grounded,
                "coverage_state": "covered_by_supported_content" if grounded else "supported_content_gap",
                "binding_confidence": "bounded_lexical" if grounded else "unresolved",
                "thread_id": str(obligation.get("thread_id") or ""),
                "thread_action": str(obligation.get("thread_action") or ""),
                "thread_traversal_index": int(obligation.get("thread_traversal_index") or 0),
                "dependency_thread_id": str(obligation.get("dependency_thread_id") or ""),
            }
        )
    return bindings


def _thread_obligation_bindings(
    bindings: list[dict[str, Any]],
    obligations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    obligation_by_id = {str(item.get("id") or ""): item for item in obligations}
    return [
        {
            "thread_id": str(item.get("thread_id") or ""),
            "thread_action": str(item.get("thread_action") or ""),
            "thread_traversal_index": int(item.get("thread_traversal_index") or 0),
            "dependency_thread_id": str(item.get("dependency_thread_id") or ""),
            "obligation_id": str(item.get("obligation_id") or ""),
            # Thread traversal needs one attributable anchor per ordered move.
            # Broader obligation coverage remains available on the canonical
            # obligation binding without letting a weaker lexical match consume
            # a later return's exact unit.
            "content_unit_ids": (item.get("content_unit_ids") or [])[:1],
            "grounded": item.get("grounded") is True,
            "source_text": str(
                obligation_by_id.get(str(item.get("obligation_id") or ""), {}).get("source_text") or ""
            ),
        }
        for item in bindings
        if str(item.get("thread_id") or "")
    ]


def _role_bonus(kind: str, role: str, text: str, request_text: str = "") -> float:
    if kind == "correction_update" and role == "correction":
        return 1.0
    role_requests = {
        "example": ("example", "instance", "illustrate", "illustration"),
        "counterexample": ("counterexample", "failure case", "case that breaks"),
        "limitation": ("limit", "limitation", "scope", "boundary", "caveat"),
        "reopening": ("what would change", "reopen", "revise", "revision condition"),
        "conclusion": ("conclude", "conclusion", "summarize", "summary", "next step"),
    }
    if role in role_requests and any(marker in request_text for marker in role_requests[role]):
        return 1.0
    if kind == "reason" and role == "support":
        return 0.25
    if kind == "choice_or_priority" and any(word in text for word in ("first", "start", "priority", "before")):
        return 0.25
    if kind == "comparison" and any(word in text for word in ("both", "while", "whereas", "difference", "compare")):
        return 0.25
    if kind == "method" and any(word in text for word in ("first", "then", "step", "start")):
        return 0.25
    return 0.0


def _semantic_binding_bonus(kind: str, text: str, request_text: str) -> float:
    """Bind request language to visible supported answer language without inventing content."""
    comparison_markers = ("both", "while", "whereas", "difference", "compared", "than", "versus")
    action_markers = (
        "first", "next", "then", "start", "begin", "test", "try", "check", "use", "choose",
        "recommend", "step", "move", "follow up", "follow-up",
    )
    reason_markers = ("because", "since", "reason", "explains", "therefore", "so that")

    if kind == "comparison" and any(marker in text for marker in comparison_markers):
        return 0.75
    if kind == "reason" and any(marker in text for marker in reason_markers):
        return 0.75
    if kind in {"method", "choice_or_priority"} and any(marker in text for marker in action_markers):
        return 0.75
    if (
        kind in {"direct_question", "direct_request", "requested_output", "requested_section"}
        and any(marker in request_text for marker in ("next step", "next move", "what should", "what do we do"))
        and any(marker in text for marker in action_markers)
    ):
        return 1.0
    return 0.0


def _paragraph_plan(
    depth: str,
    units: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    thesis = [str(item["id"]) for item in units if item.get("role") == "thesis"][:1]
    bound_ids = {
        unit_id
        for binding in bindings
        for unit_id in binding.get("content_unit_ids") or []
        if unit_id not in thesis
    }
    # The supported answer already carries an intentional source order. Coverage
    # bindings may overlap or score in a different order; they must not scramble it.
    bound = [str(item["id"]) for item in units if str(item["id"]) in bound_ids]
    support = [
        str(item["id"])
        for item in units
        if item.get("role") in {"support", "assumption", "example", "counterexample"}
        and str(item["id"]) not in thesis
        and str(item["id"]) not in bound
    ]
    limits = [str(item["id"]) for item in units if item.get("role") in {"limitation", "reopening", "conclusion"}]
    if depth == "brief":
        return [{"index": 1, "role": "answer", "content_unit_ids": [*thesis, *bound][:2], "transition": "none"}]
    if depth != "developed":
        return [
            {"index": 1, "role": "answer", "content_unit_ids": [*thesis, *bound], "transition": "none"},
            *(
                [{"index": 2, "role": "limit_or_reopening", "content_unit_ids": limits, "transition": "limit"}]
                if limits
                else []
            ),
        ]
    paragraphs = [
        {"index": 1, "role": "answer", "content_unit_ids": thesis, "transition": "none"},
    ]
    development = [*bound, *support]
    if development:
        paragraphs.append(
            {
                "index": len(paragraphs) + 1,
                "role": "development",
                "content_unit_ids": development,
                "transition": "support",
            }
        )
    if limits:
        paragraphs.append(
            {
                "index": len(paragraphs) + 1,
                "role": "limit_and_closure",
                "content_unit_ids": limits,
                "transition": "reopening",
            }
        )
    return paragraphs


def _closure_plan(units: list[dict[str, Any]]) -> dict[str, Any]:
    reopening = next((item for item in units if item.get("role") == "reopening"), None)
    limitation = next((item for item in units if item.get("role") == "limitation"), None)
    conclusion = next((item for item in units if item.get("role") == "conclusion"), None)
    selected = reopening or limitation or conclusion
    return {
        "mode": (
            "what_would_change"
            if reopening
            else "bounded_limit"
            if limitation
            else "supported_next_step"
            if conclusion
            else "stop_after_supported_content"
        ),
        "content_unit_id": str((selected or {}).get("id") or ""),
        "text": str((selected or {}).get("text") or ""),
        "question_required": False,
    }


def _sentences(value: str) -> list[str]:
    return [
        truncate(item.strip(), 900)
        for item in re.split(r"(?<=[.!?])\s+|\n+", value.strip())
        if item.strip()
    ][:16]


def _terms(value: str) -> list[str]:
    words = [word.lower() for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", value)]
    return list(dict.fromkeys(word for word in words if word not in STOP_WORDS))[:24]


def _strings(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [truncate(str(item), 900).strip() for item in value if str(item).strip()]


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
