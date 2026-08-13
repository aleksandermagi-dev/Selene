from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


DISCOURSE_LOOM_BOUNDARY = (
    "supported_discourse_arrangement_only_no_fact_example_memory_identity_authority_or_hidden_reasoning_generation"
)

MAX_DISCOURSE_CANDIDATES = 4

ROLE_ORDER = {
    "thesis": 0,
    "correction": 1,
    "support": 2,
    "assumption": 3,
    "example": 4,
    "counterexample": 5,
    "limitation": 6,
    "reopening": 7,
    "conclusion": 8,
}


def discourse_loom_status() -> dict[str, Any]:
    return _locked(
        {
            "status": "discourse_loom_ready",
            "version": "v1_supported_role_discourse_candidates",
            "candidate_limit": MAX_DISCOURSE_CANDIDATES,
            "selection_pass_limit": 1,
            "supported_roles": list(ROLE_ORDER),
            "recursive_generation_allowed": False,
            "provider_generation_used": False,
            "missing_content_generation_allowed": False,
            "natural_stop_without_forced_closure": True,
        }
    )


def weave_supported_discourse(
    supported_discourse: dict[str, Any] | None,
    *,
    selected_formation: dict[str, Any] | None = None,
    response_depth: str = "standard",
    contextual_plan: dict[str, Any] | None = None,
    recent_texts: list[str] | None = None,
) -> dict[str, Any]:
    discourse = supported_discourse or {}
    selected_formation = selected_formation or {}
    contextual_plan = contextual_plan or {}
    recent_texts = [str(item).strip() for item in recent_texts or [] if str(item).strip()]
    depth = _depth(response_depth or contextual_plan.get("response_depth"))
    exact_structure = contextual_plan.get("exact_domain_structure_locked") is True
    specialized_social = contextual_plan.get("social_act_structure_owned_elsewhere") is True
    units, collapsed_seed_ids = _active_units(
        discourse,
        {} if exact_structure or specialized_social else selected_formation,
    )
    structured_formation_used = any(
        str(item.get("id") or "") == "structured_formation" for item in units
    )
    unit_by_id = {str(item.get("id") or ""): item for item in units}
    required_ids = _required_unit_ids(
        discourse,
        units,
        collapsed_seed_ids=collapsed_seed_ids,
        depth=depth,
    )
    obligation_ids = _obligation_unit_ids(
        discourse,
        collapsed_seed_ids=collapsed_seed_ids,
        structured_id="structured_formation" if collapsed_seed_ids else "",
    )
    closure_id = _mapped_unit_id(
        str((discourse.get("closure_plan") or {}).get("content_unit_id") or ""),
        collapsed_seed_ids,
    )
    hold_reason = (
        "exact_domain_structure_locked"
        if exact_structure
        else "specialized_social_structure_owned_elsewhere"
        if specialized_social
        else ""
    )
    specifications = _specifications(
        discourse,
        units,
        required_ids=required_ids,
        depth=depth,
        as_supplied_only=bool(hold_reason),
    )
    candidates: list[dict[str, Any]] = []
    seen_surfaces: dict[str, str] = {}
    for index, specification in enumerate(specifications[:MAX_DISCOURSE_CANDIDATES]):
        realization = _realize_specification(specification, unit_by_id)
        text = str(realization.get("candidate_text") or "").strip()
        normalized = _normalize_structure(text)
        duplicate_of = seen_surfaces.get(normalized, "") if normalized else ""
        if normalized and not duplicate_of:
            seen_surfaces[normalized] = str(specification.get("loom_specification_id") or "")
        invariant = _invariant_check(
            realization,
            specification,
            unit_by_id=unit_by_id,
            required_ids=required_ids,
            obligation_ids=obligation_ids,
            closure_id=closure_id,
            expected_source_refs=[str(item) for item in discourse.get("source_refs") or []],
        )
        score = _score(
            realization,
            specification,
            invariant,
            depth=depth,
            contextual_plan=contextual_plan,
            recent_texts=recent_texts,
            duplicate_of=duplicate_of,
        )
        selectable = invariant["passed"] is True and bool(text) and not duplicate_of
        candidates.append(
            {
                "discourse_candidate_id": f"discourse_candidate:{index + 1}",
                "loom_specification_id": str(specification.get("loom_specification_id") or ""),
                "candidate_text": text,
                "paragraphs": realization.get("paragraphs") or [],
                "included_content_unit_ids": realization.get("included_content_unit_ids") or [],
                "invariant_check": invariant,
                "score": score["total"],
                "score_breakdown": score["breakdown"],
                "selectable": selectable,
                "held_reason": (
                    ""
                    if selectable
                    else "discourse_invariant_failed"
                    if invariant["passed"] is not True
                    else "duplicate_surface_realization"
                    if duplicate_of
                    else "empty_realization"
                ),
                "duplicate_of_loom_specification_id": duplicate_of,
            }
        )

    selectable = [item for item in candidates if item.get("selectable") is True]
    selected = sorted(
        selectable,
        key=lambda item: (
            -float(item.get("score") or 0.0),
            int(str(item.get("discourse_candidate_id") or "0").split(":")[-1]),
        ),
    )[0] if selectable else (candidates[0] if candidates else None)
    distinct_count = len(
        {
            _normalize_structure(str(item.get("candidate_text") or ""))
            for item in candidates
            if str(item.get("candidate_text") or "").strip()
        }
    )
    selection_active = len(selectable) > 1 and distinct_count > 1 and not hold_reason
    return _locked(
        {
            "status": (
                "discourse_loom_selected"
                if selection_active and selected
                else "discourse_loom_as_supplied_only"
                if selected
                else "discourse_loom_no_supported_content"
            ),
            "version": "v1_supported_role_discourse_candidates",
            "response_depth": depth,
            "candidate_limit": MAX_DISCOURSE_CANDIDATES,
            "generated_candidate_count": len(candidates),
            "distinct_candidate_count": distinct_count,
            "selectable_candidate_count": len(selectable),
            "held_candidate_count": len(candidates) - len(selectable),
            "selection_active": selection_active,
            "selection_performed": bool(selected),
            "selection_pass_count": 1 if candidates else 0,
            "recursive_generation_used": False,
            "provider_generation_used": False,
            "hold_reason": hold_reason,
            "selected_discourse_candidate_id": str(
                (selected or {}).get("discourse_candidate_id") or ""
            ),
            "selected_loom_specification_id": str(
                (selected or {}).get("loom_specification_id") or ""
            ),
            "selected_candidate_text": str((selected or {}).get("candidate_text") or ""),
            "selected_paragraphs": (selected or {}).get("paragraphs") or [],
            "candidates": candidates,
            "content_unit_ids": list(unit_by_id),
            "required_content_unit_ids": required_ids,
            "obligation_bound_content_unit_ids": obligation_ids,
            "closure_content_unit_id": closure_id,
            "collapsed_seed_content_unit_ids": collapsed_seed_ids,
            "structured_formation_used_as_thesis": structured_formation_used,
            "uncovered_obligation_ids_before_expression": (
                discourse.get("uncovered_obligation_ids") or []
            ),
            "natural_stop_used": not bool(closure_id),
            "forced_closure_added": False,
        }
    )


def _active_units(
    discourse: dict[str, Any],
    selected_formation: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    original = [
        deepcopy(item)
        for item in discourse.get("content_units") or []
        if isinstance(item, dict) and str(item.get("text") or "").strip()
    ]
    formation_text = str(selected_formation.get("candidate_text") or "").strip()
    structured = (
        selected_formation.get("formation_mode") == "structured"
        and selected_formation.get("meaning_preserved") is True
        and bool(formation_text)
    )
    if not structured:
        return original, []
    seed_ids = [
        str(item.get("id") or "")
        for item in original
        if item.get("source") == "supplied_content_seed"
    ]
    remaining = [item for item in original if item.get("source") != "supplied_content_seed"]
    formation_key = _normalize_surface(formation_text)
    subsumed_ids = [
        str(item.get("id") or "")
        for item in remaining
        if _normalize_surface(str(item.get("text") or ""))
        and _normalize_surface(str(item.get("text") or "")) in formation_key
    ]
    covered_ids = list(dict.fromkeys([*seed_ids, *subsumed_ids]))
    structured_unit = {
        "id": "structured_formation",
        "text": formation_text,
        "role": "thesis",
        "source": "candidate_garden_selected_formation",
        "supported": True,
        "covers_content_unit_ids": covered_ids,
    }
    deduped = [
        item
        for item in remaining
        if str(item.get("id") or "") not in subsumed_ids
    ]
    return [structured_unit, *deduped], covered_ids


def _required_unit_ids(
    discourse: dict[str, Any],
    units: list[dict[str, Any]],
    *,
    collapsed_seed_ids: list[str],
    depth: str,
) -> list[str]:
    active_ids = {str(item.get("id") or "") for item in units}
    required = [
        str(item.get("id") or "")
        for item in units
        if item.get("role") in {"thesis", "correction", "limitation", "reopening", "conclusion"}
    ]
    required.extend(
        _obligation_unit_ids(
            discourse,
            collapsed_seed_ids=collapsed_seed_ids,
            structured_id="structured_formation" if collapsed_seed_ids else "",
        )
    )
    if depth != "brief":
        required.extend(
            str(item.get("id") or "")
            for item in units
            if item.get("supported") is True
        )
    return list(dict.fromkeys(item for item in required if item in active_ids))


def _obligation_unit_ids(
    discourse: dict[str, Any],
    *,
    collapsed_seed_ids: list[str],
    structured_id: str,
) -> list[str]:
    return list(
        dict.fromkeys(
            _mapped_unit_id(str(unit_id), collapsed_seed_ids, structured_id)
            for binding in discourse.get("obligation_bindings") or []
            if isinstance(binding, dict)
            and binding.get("required") is True
            and binding.get("grounded") is True
            for unit_id in binding.get("content_unit_ids") or []
            if _mapped_unit_id(str(unit_id), collapsed_seed_ids, structured_id)
        )
    )


def _mapped_unit_id(
    unit_id: str,
    collapsed_seed_ids: list[str],
    structured_id: str = "structured_formation",
) -> str:
    return structured_id if unit_id and unit_id in collapsed_seed_ids else unit_id


def _specifications(
    discourse: dict[str, Any],
    units: list[dict[str, Any]],
    *,
    required_ids: list[str],
    depth: str,
    as_supplied_only: bool,
) -> list[dict[str, Any]]:
    unit_ids = [str(item.get("id") or "") for item in units]
    if not unit_ids:
        return []
    plan_paragraphs = _mapped_plan_paragraphs(discourse, units)
    specifications = [
        {
            "loom_specification_id": "discourse:plan_order",
            "label": "supported plan order",
            "paragraph_unit_ids": plan_paragraphs or [unit_ids],
            "required_content_unit_ids": required_ids,
            "transition_mode": "as_supplied" if as_supplied_only else "role_explicit",
            "meaning_change_allowed": False,
        }
    ]
    if as_supplied_only:
        return specifications
    if depth == "brief":
        brief_ids = [item for item in unit_ids if item in required_ids]
        if brief_ids:
            specifications.insert(
                0,
                {
                    "loom_specification_id": "discourse:brief_required",
                    "label": "brief required content",
                    "paragraph_unit_ids": [brief_ids],
                    "required_content_unit_ids": required_ids,
                    "transition_mode": "role_explicit",
                    "meaning_change_allowed": False,
                },
            )
    role_groups = _role_groups(units)
    if len(unit_ids) > 1:
        specifications.append(
            {
                "loom_specification_id": "discourse:integrated_complete",
                "label": "integrated complete",
                "paragraph_unit_ids": [unit_ids],
                "required_content_unit_ids": required_ids,
                "transition_mode": "role_explicit",
                "meaning_change_allowed": False,
            }
        )
    if len(role_groups) > 1:
        specifications.append(
            {
                "loom_specification_id": "discourse:role_braided",
                "label": "role-braided development",
                "paragraph_unit_ids": role_groups,
                "required_content_unit_ids": required_ids,
                "transition_mode": "role_explicit",
                "meaning_change_allowed": False,
            }
        )
    obligation_order = _obligation_order(discourse, units)
    if obligation_order and obligation_order != unit_ids:
        specifications.append(
            {
                "loom_specification_id": "discourse:obligation_ordered",
                "label": "obligation-ordered development",
                "paragraph_unit_ids": _paragraphize(obligation_order, depth),
                "required_content_unit_ids": required_ids,
                "transition_mode": "role_explicit",
                "meaning_change_allowed": False,
            }
        )
    thread_paragraphs, thread_transition_indexes, thread_transition_actions = _thread_paragraphs(
        discourse,
        units,
    )
    if thread_paragraphs:
        specifications.append(
            {
                "loom_specification_id": "discourse:thread_traversal",
                "label": "attributed thread traversal",
                "paragraph_unit_ids": thread_paragraphs,
                "required_content_unit_ids": required_ids,
                "transition_mode": "thread_attributed",
                "thread_transition_paragraph_indexes": thread_transition_indexes,
                "thread_transition_actions": thread_transition_actions,
                "thread_grounded": True,
                "meaning_change_allowed": False,
            }
        )
    return _dedupe_specifications(specifications)


def _mapped_plan_paragraphs(
    discourse: dict[str, Any],
    units: list[dict[str, Any]],
) -> list[list[str]]:
    active = {str(item.get("id") or "") for item in units}
    structured = "structured_formation" in active
    seed_ids = {
        str(value)
        for item in units
        for value in item.get("covers_content_unit_ids") or []
        if item.get("id") == "structured_formation"
    }
    paragraphs: list[list[str]] = []
    used: set[str] = set()
    for paragraph in discourse.get("paragraph_plan") or []:
        if not isinstance(paragraph, dict):
            continue
        mapped = [
            "structured_formation" if structured and str(unit_id) in seed_ids else str(unit_id)
            for unit_id in paragraph.get("content_unit_ids") or []
        ]
        # Several seed units can collapse into one structured formation.  Do
        # not render that shared replacement once for every covered seed.
        mapped = list(
            dict.fromkeys(item for item in mapped if item in active and item not in used)
        )
        if mapped:
            paragraphs.append(mapped)
            used.update(mapped)
    remaining = [str(item.get("id") or "") for item in units if str(item.get("id") or "") not in used]
    if remaining:
        paragraphs.extend(_role_groups([item for item in units if str(item.get("id") or "") in remaining]))
    return paragraphs


def _role_groups(units: list[dict[str, Any]]) -> list[list[str]]:
    groups: list[list[str]] = []
    thesis = [str(item.get("id") or "") for item in units if item.get("role") == "thesis"]
    development = [
        str(item.get("id") or "")
        for item in units
        if item.get("role") in {"correction", "support", "assumption", "example"}
    ]
    closure = [
        str(item.get("id") or "")
        for item in units
        if item.get("role") in {"limitation", "reopening", "conclusion"}
    ]
    for group in (thesis, development, closure):
        if group:
            groups.append(group)
    return groups


def _obligation_order(
    discourse: dict[str, Any],
    units: list[dict[str, Any]],
) -> list[str]:
    active_ids = [str(item.get("id") or "") for item in units]
    active = set(active_ids)
    ordered: list[str] = [
        str(item.get("id") or "") for item in units if item.get("role") == "thesis"
    ]
    for binding in discourse.get("obligation_bindings") or []:
        if not isinstance(binding, dict) or binding.get("grounded") is not True:
            continue
        for unit_id in binding.get("content_unit_ids") or []:
            value = str(unit_id)
            if value in active and value not in ordered:
                ordered.append(value)
    ordered.extend(item for item in active_ids if item not in ordered)
    return ordered


def _thread_paragraphs(
    discourse: dict[str, Any],
    units: list[dict[str, Any]],
) -> tuple[list[list[str]], list[int], dict[int, str]]:
    bindings = [
        item
        for item in discourse.get("thread_obligation_bindings") or []
        if isinstance(item, dict)
        and item.get("grounded") is True
        and str(item.get("thread_id") or "")
    ]
    if not bindings:
        return [], [], {}
    active_ids = [str(item.get("id") or "") for item in units]
    active = set(active_ids)
    structured = next(
        (item for item in units if item.get("id") == "structured_formation"),
        {},
    )
    collapsed = [str(item) for item in structured.get("covers_content_unit_ids") or []]
    thesis = [
        str(item.get("id") or "") for item in units if item.get("role") == "thesis"
    ]
    paragraphs: list[list[str]] = [thesis] if thesis else []
    used = set(thesis)
    transition_indexes: list[int] = []
    transition_actions: dict[int, str] = {}
    ordered_bindings = sorted(
        bindings,
        key=lambda item: (
            int(item.get("thread_traversal_index") or 0),
            str(item.get("thread_id") or ""),
        ),
    )
    for binding in ordered_bindings:
        group = []
        for raw_id in binding.get("content_unit_ids") or []:
            unit_id = _mapped_unit_id(str(raw_id), collapsed)
            if unit_id in active and unit_id not in used:
                group.append(unit_id)
                used.add(unit_id)
        if group:
            paragraphs.append(group)
            paragraph_index = len(paragraphs) - 1
            transition_indexes.append(paragraph_index)
            transition_actions[paragraph_index] = str(binding.get("thread_action") or "")
    remaining = [item for item in active_ids if item not in used]
    if remaining:
        paragraphs.extend(_role_groups([item for item in units if str(item.get("id") or "") in remaining]))
    if len(paragraphs) < 2 or not transition_indexes:
        return [], [], {}
    return paragraphs, transition_indexes, transition_actions


def _paragraphize(unit_ids: list[str], depth: str) -> list[list[str]]:
    if depth == "brief" or len(unit_ids) <= 2:
        return [unit_ids]
    midpoint = max(1, len(unit_ids) // 2)
    return [unit_ids[:midpoint], unit_ids[midpoint:]]


def _dedupe_specifications(value: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, tuple[tuple[str, ...], ...]]] = set()
    result: list[dict[str, Any]] = []
    for item in value:
        signature = (
            str(item.get("transition_mode") or ""),
            tuple(tuple(group) for group in item.get("paragraph_unit_ids") or []),
        )
        if signature in seen:
            continue
        seen.add(signature)
        result.append(item)
    return result


def _realize_specification(
    specification: dict[str, Any],
    unit_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    paragraphs: list[dict[str, Any]] = []
    included: list[str] = []
    role_explicit = specification.get("transition_mode") == "role_explicit"
    thread_attributed = specification.get("transition_mode") == "thread_attributed"
    thread_transition_indexes = {
        int(item)
        for item in specification.get("thread_transition_paragraph_indexes") or []
    }
    thread_transition_actions = {
        int(index): str(action or "")
        for index, action in (specification.get("thread_transition_actions") or {}).items()
    }
    for paragraph_index, group in enumerate(specification.get("paragraph_unit_ids") or []):
        pieces: list[str] = []
        group_ids: list[str] = []
        for unit_index, unit_id in enumerate(group):
            unit = unit_by_id.get(str(unit_id))
            if not unit:
                continue
            text = _render_unit(
                unit,
                first=(paragraph_index == 0 and unit_index == 0),
                role_explicit=role_explicit,
            )
            if text:
                pieces.append(text)
                group_ids.append(str(unit_id))
                included.append(str(unit_id))
        if pieces:
            paragraph_text = " ".join(pieces)
            if thread_attributed and paragraph_index in thread_transition_indexes:
                prefix = _thread_transition_prefix(
                    thread_transition_actions.get(paragraph_index, ""),
                    paragraph_index,
                )
                paragraph_text = f"{prefix} {paragraph_text}"
            paragraphs.append(
                {
                    "index": len(paragraphs) + 1,
                    "content_unit_ids": group_ids,
                    "text": paragraph_text,
                }
            )
    return {
        "candidate_text": "\n\n".join(str(item["text"]) for item in paragraphs),
        "paragraphs": paragraphs,
        "included_content_unit_ids": list(dict.fromkeys(included)),
    }


def _thread_transition_prefix(action: str, paragraph_index: int) -> str:
    by_action = {
        "branch": "On the related point:",
        "resume": "Back to that thread:",
        "revise_with_dependency": "Bringing that back with the new piece:",
        "land": "For the final point:",
        "continue": "Continuing that thread:",
        "start": "On that thread:",
    }
    if action in by_action:
        return by_action[action]
    return "On the related thread:" if paragraph_index == 1 else "Returning to the earlier thread:"


def _render_unit(
    unit: dict[str, Any],
    *,
    first: bool,
    role_explicit: bool,
) -> str:
    text = _sentence(str(unit.get("text") or ""))
    if not text:
        return ""
    if (
        not role_explicit
        or first
        or unit.get("role") in {"thesis", "support", "conclusion", "correction"}
    ):
        return text
    role = str(unit.get("role") or "support")
    prefix = {
        "example": "For example",
        "counterexample": "One counterexample",
        "assumption": "One assumption",
        "limitation": "One limit",
        "reopening": "What would change this",
    }.get(role, "")
    if not prefix or text.lower().startswith(prefix.lower()):
        return text
    return f"{prefix}: {text}"


def _invariant_check(
    realization: dict[str, Any],
    specification: dict[str, Any],
    *,
    unit_by_id: dict[str, dict[str, Any]],
    required_ids: list[str],
    obligation_ids: list[str],
    closure_id: str,
    expected_source_refs: list[str],
) -> dict[str, Any]:
    included = [str(item) for item in realization.get("included_content_unit_ids") or []]
    declared = [
        str(item)
        for group in specification.get("paragraph_unit_ids") or []
        for item in group
    ]
    unsupported = [item for item in included if item not in unit_by_id]
    first_id = included[0] if included else ""
    first_role = str((unit_by_id.get(first_id) or {}).get("role") or "")
    checks = {
        "required_content_units_preserved": all(item in included for item in required_ids),
        "obligation_bound_units_preserved": all(item in included for item in obligation_ids),
        "closure_preserved_when_supported": not closure_id or closure_id in included,
        "only_declared_units_realized": not unsupported and all(item in declared for item in included),
        "thesis_or_first_supported_unit_leads": first_role == "thesis" or not any(
            item.get("role") == "thesis" for item in unit_by_id.values()
        ),
        "specification_forbids_meaning_change": specification.get("meaning_change_allowed") is False,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "required_content_unit_ids": required_ids,
        "included_content_unit_ids": included,
        "obligation_bound_content_unit_ids": obligation_ids,
        "closure_content_unit_id": closure_id,
        "source_refs": expected_source_refs,
        "hidden_chain_of_thought_exposed": False,
    }


def _score(
    realization: dict[str, Any],
    specification: dict[str, Any],
    invariant: dict[str, Any],
    *,
    depth: str,
    contextual_plan: dict[str, Any],
    recent_texts: list[str],
    duplicate_of: str,
) -> dict[str, Any]:
    paragraphs = realization.get("paragraphs") or []
    paragraph_count = len(paragraphs)
    text = str(realization.get("candidate_text") or "")
    target = 1 if depth == "brief" else max(
        1,
        min(int(contextual_plan.get("supported_content_unit_count") or paragraph_count or 1), 3),
    ) if depth == "developed" else min(2, max(1, paragraph_count))
    breakdown = {
        "discourse_invariants": 80.0 if invariant.get("passed") is True else -240.0,
        "depth_and_paragraph_fit": max(-8.0, 10.0 - 4.0 * abs(paragraph_count - target)),
        "recent_surface_distance": _recent_score(text, recent_texts),
        "distinct_surface_realization": -80.0 if duplicate_of else 4.0,
        "plan_alignment": (
            3.0
            if specification.get("loom_specification_id") == "discourse:plan_order"
            else 0.0
        ),
        "thread_traversal_fit": 6.0 if specification.get("thread_grounded") is True else 0.0,
        "natural_stop": 2.0,
    }
    return {"total": round(sum(breakdown.values()), 3), "breakdown": breakdown}


def _recent_score(text: str, recent_texts: list[str]) -> float:
    normalized = _normalize_surface(text)
    if not normalized or not recent_texts:
        return 3.0
    recent = [_normalize_surface(item) for item in recent_texts]
    if normalized in recent:
        return -35.0
    opening = " ".join(normalized.split()[:8])
    if any(" ".join(item.split()[:8]) == opening for item in recent):
        return -8.0
    return 3.0


def _sentence(value: str) -> str:
    value = " ".join(str(value).split()).strip()
    if not value:
        return ""
    value = value[0].upper() + value[1:]
    return value if value.endswith((".", "!", "?")) else value + "."


def _depth(value: Any) -> str:
    value = str(value or "standard").lower()
    if value in {"brief", "compact", "short"}:
        return "brief"
    if value in {"developed", "long", "deep"}:
        return "developed"
    return "standard"


def _normalize_surface(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", str(value).lower()))


def _normalize_structure(value: str) -> str:
    return " <paragraph> ".join(
        _normalize_surface(item)
        for item in re.split(r"\n\s*\n", str(value))
        if _normalize_surface(item)
    )


def _locked(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "meaning_change_allowed": False,
        "fact_generation_allowed": False,
        "unsupported_example_generation_allowed": False,
        "filler_generation_allowed": False,
        "certainty_change_allowed": False,
        "source_change_allowed": False,
        "memory_write_active": False,
        "identity_change_allowed": False,
        "governance_change_allowed": False,
        "authority_change_allowed": False,
        "coordinated_expression_contract_active": True,
        "database_write_performed": False,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": DISCOURSE_LOOM_BOUNDARY,
    }
