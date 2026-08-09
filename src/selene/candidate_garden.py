from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from .language_formation import realize_semantic_frame


CANDIDATE_GARDEN_BOUNDARY = (
    "bounded_complete_language_candidates_only_preserve_supported_meaning_evidence_certainty_sources_and_authority"
)

DEFAULT_MAX_CANDIDATES = 8
HARD_MAX_CANDIDATES = 12


def candidate_garden_status() -> dict[str, Any]:
    return _locked(
        {
            "status": "candidate_garden_ready",
            "version": "v1_bounded_meaning_equivalent_candidates",
            "default_max_candidates": DEFAULT_MAX_CANDIDATES,
            "hard_max_candidates": HARD_MAX_CANDIDATES,
            "selection_pass_limit": 1,
            "recursive_generation_allowed": False,
            "provider_generation_used": False,
            "selection_dimensions": [
                "semantic_invariants",
                "required_unit_preservation",
                "discourse_depth_fit",
                "dialogue_act_fit",
                "sentence_rhythm_fit",
                "recent_surface_distance",
                "distinct_surface_realization",
            ],
        }
    )


def cultivate_candidate_garden(
    frame: dict[str, Any] | None,
    lattice: dict[str, Any] | None,
    *,
    variation_key: str = "",
    recent_texts: list[str] | None = None,
    contextual_plan: dict[str, Any] | None = None,
    supported_discourse: dict[str, Any] | None = None,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
) -> dict[str, Any]:
    frame = frame or {}
    lattice = lattice or {}
    contextual_plan = contextual_plan or {}
    supported_discourse = supported_discourse or {}
    recent_texts = [str(item).strip() for item in recent_texts or [] if str(item).strip()]
    limit = max(1, min(int(max_candidates or DEFAULT_MAX_CANDIDATES), HARD_MAX_CANDIDATES))
    specs = _bounded_specifications(lattice.get("constructions"), limit)
    required_ids = [str(item) for item in lattice.get("required_semantic_unit_ids") or []]
    meaning_signature = [str(item) for item in lattice.get("meaning_signature") or []]
    expected_sources = [str(item) for item in frame.get("source_refs") or []]
    generated: list[dict[str, Any]] = []
    seen_surfaces: dict[str, str] = {}

    for generation_index, specification in enumerate(specs):
        formation = realize_semantic_frame(
            frame,
            variation_key=variation_key,
            recent_texts=[],
            construction_specification=specification,
        )
        invariant = _invariant_check(
            formation,
            specification,
            required_ids=required_ids,
            meaning_signature=meaning_signature,
            expected_sources=expected_sources,
        )
        text = str(formation.get("candidate_text") or "").strip()
        surface_key = _normalize_surface(text)
        duplicate_of = seen_surfaces.get(surface_key, "") if surface_key else ""
        if surface_key and not duplicate_of:
            seen_surfaces[surface_key] = str(specification.get("construction_id") or "")
        score = _score_candidate(
            formation,
            specification,
            invariant,
            recent_texts=recent_texts,
            contextual_plan=contextual_plan,
            supported_discourse=supported_discourse,
            duplicate_of=duplicate_of,
        )
        selectable = invariant["passed"] is True and bool(text) and not duplicate_of
        generated.append(
            {
                "candidate_id": f"candidate:{generation_index + 1}",
                "construction_id": str(specification.get("construction_id") or ""),
                "construction_dimensions": specification.get("dimensions") or [],
                "candidate_text": text,
                "formation": formation,
                "invariant_check": invariant,
                "score": score["total"],
                "score_breakdown": score["breakdown"],
                "selectable": selectable,
                "held_reason": (
                    ""
                    if selectable
                    else "semantic_invariant_failed"
                    if invariant["passed"] is not True
                    else "duplicate_surface_realization"
                    if duplicate_of
                    else "empty_realization"
                ),
                "duplicate_of_construction_id": duplicate_of,
            }
        )

    selectable = [item for item in generated if item.get("selectable") is True]
    selected = sorted(
        selectable,
        key=lambda item: (-float(item.get("score") or 0.0), int(str(item["candidate_id"]).split(":")[-1])),
    )[0] if selectable else None
    default_candidate = next(
        (
            item
            for item in generated
            if item.get("construction_id") == lattice.get("default_construction_id")
        ),
        generated[0] if generated else None,
    )
    if selected is None:
        selected = default_candidate
    distinct_count = len({
        _normalize_surface(str(item.get("candidate_text") or ""))
        for item in generated
        if str(item.get("candidate_text") or "").strip()
    })
    selection_active = len(selectable) > 1 and distinct_count > 1
    selected_formation = deepcopy((selected or {}).get("formation") or {})
    return _locked(
        {
            "status": (
                "candidate_garden_selected"
                if selection_active and selected
                else "candidate_garden_as_supplied_only"
                if generated
                else "candidate_garden_no_realizable_candidate"
            ),
            "version": "v1_bounded_meaning_equivalent_candidates",
            "candidate_limit": limit,
            "generated_candidate_count": len(generated),
            "distinct_candidate_count": distinct_count,
            "selectable_candidate_count": len(selectable),
            "held_candidate_count": len(generated) - len(selectable),
            "selection_active": selection_active,
            "selection_performed": bool(selected),
            "selection_pass_count": 1 if generated else 0,
            "recursive_generation_used": False,
            "provider_generation_used": False,
            "default_construction_id": str(lattice.get("default_construction_id") or "construction:as_supplied"),
            "selected_candidate_id": str((selected or {}).get("candidate_id") or ""),
            "selected_construction_id": str((selected or {}).get("construction_id") or ""),
            "selected_candidate_text": str((selected or {}).get("candidate_text") or ""),
            "selected_formation": selected_formation,
            "candidates": generated,
            "required_semantic_unit_ids": required_ids,
            "meaning_signature": meaning_signature,
            "all_obligations_grounded_before_expression": (
                supported_discourse.get("all_obligations_grounded") is True
            ),
            "uncovered_obligation_ids_before_expression": (
                supported_discourse.get("uncovered_obligation_ids") or []
            ),
        }
    )


def _bounded_specifications(value: Any, limit: int) -> list[dict[str, Any]]:
    specifications = [deepcopy(item) for item in value or [] if isinstance(item, dict)]
    if len(specifications) <= limit:
        return specifications
    selected: list[dict[str, Any]] = []
    default = next(
        (item for item in specifications if item.get("construction_id") == "construction:as_supplied"),
        specifications[0],
    )
    selected.append(default)
    covered_dimensions: set[str] = set()
    for item in specifications:
        if item is default:
            continue
        dimensions = {str(value) for value in item.get("dimensions") or [] if str(value)}
        if dimensions - covered_dimensions:
            selected.append(item)
            covered_dimensions.update(dimensions)
        if len(selected) >= limit:
            return selected
    for item in specifications:
        if item not in selected:
            selected.append(item)
        if len(selected) >= limit:
            break
    return selected


def _invariant_check(
    formation: dict[str, Any],
    specification: dict[str, Any],
    *,
    required_ids: list[str],
    meaning_signature: list[str],
    expected_sources: list[str],
) -> dict[str, Any]:
    realized_ids = [str(item) for item in formation.get("realized_semantic_unit_ids") or []]
    actual_required = [str(item) for item in formation.get("required_semantic_unit_ids") or []]
    actual_signature = [str(item) for item in formation.get("meaning_signature") or []]
    actual_sources = [str(item) for item in formation.get("source_refs") or []]
    checks = {
        "meaning_preserved": formation.get("meaning_preserved") is True,
        "required_units_declared_unchanged": actual_required == required_ids,
        "required_units_realized": all(item in realized_ids for item in required_ids),
        "meaning_signature_unchanged": actual_signature == meaning_signature,
        "source_refs_unchanged": actual_sources == expected_sources,
        "construction_forbids_evidence_or_certainty_change": (
            specification.get("evidence_and_certainty_change_allowed") is False
        ),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "required_semantic_unit_ids": required_ids,
        "realized_semantic_unit_ids": realized_ids,
        "meaning_signature": actual_signature,
        "source_refs": actual_sources,
        "hidden_chain_of_thought_exposed": False,
    }


def _score_candidate(
    formation: dict[str, Any],
    specification: dict[str, Any],
    invariant: dict[str, Any],
    *,
    recent_texts: list[str],
    contextual_plan: dict[str, Any],
    supported_discourse: dict[str, Any],
    duplicate_of: str,
) -> dict[str, Any]:
    text = str(formation.get("candidate_text") or "").strip()
    breakdown: dict[str, float] = {}
    breakdown["semantic_invariants"] = 60.0 if invariant.get("passed") is True else -200.0
    breakdown["required_unit_preservation"] = (
        20.0 if formation.get("required_semantic_units_preserved") is True else -100.0
    )
    desired_depth = str(contextual_plan.get("response_depth") or "standard")
    supplied_depth = str((specification.get("style") or {}).get("response_depth") or "")
    breakdown["discourse_depth_fit"] = (
        8.0
        if supplied_depth and supplied_depth == desired_depth
        else 3.0
        if not supplied_depth
        else -2.0
    )
    breakdown["dialogue_act_fit"] = _dialogue_act_score(specification, contextual_plan)
    breakdown["sentence_rhythm_fit"] = _rhythm_score(text, contextual_plan)
    breakdown["recent_surface_distance"] = _recent_distance_score(text, recent_texts)
    breakdown["distinct_surface_realization"] = -80.0 if duplicate_of else 4.0
    breakdown["grounded_obligation_state"] = (
        2.0 if supported_discourse.get("all_obligations_grounded") is True else 0.0
    )
    breakdown["stable_default_tiebreak"] = (
        1.0
        if specification.get("construction_id") == "construction:as_supplied"
        else 0.0
    )
    return {
        "total": round(sum(breakdown.values()), 3),
        "breakdown": breakdown,
    }


def _dialogue_act_score(
    specification: dict[str, Any],
    contextual_plan: dict[str, Any],
) -> float:
    dimensions = {str(item) for item in specification.get("dimensions") or []}
    if "dialogue_act" not in dimensions:
        return 3.0
    overrides = specification.get("unit_overrides")
    overrides = overrides if isinstance(overrides, dict) else {}
    mood = next(
        (
            str(value.get("mood") or "")
            for value in overrides.values()
            if isinstance(value, dict) and value.get("mood")
        ),
        "",
    )
    task_kind = str(contextual_plan.get("task_kind") or "")
    opening = str((contextual_plan.get("decisions") or {}).get("opening") or "")
    if mood == "interrogative":
        return 8.0 if task_kind in {"clarification", "question"} else -15.0
    if mood == "imperative":
        return 8.0 if task_kind in {"instruction", "procedure"} else -15.0
    if mood == "declarative":
        return 6.0 if opening in {"answer_first", "thesis_first"} else 2.0
    return -5.0


def _rhythm_score(text: str, contextual_plan: dict[str, Any]) -> float:
    if not text:
        return -20.0
    distribution = contextual_plan.get("sentence_distribution")
    distribution = distribution if isinstance(distribution, dict) else {}
    bounds = distribution.get("target_words_per_sentence")
    if not isinstance(bounds, list) or len(bounds) != 2:
        return 0.0
    sentences = [item.strip() for item in re.split(r"[.!?]+", text) if item.strip()]
    if not sentences:
        return -10.0
    average = sum(len(item.split()) for item in sentences) / len(sentences)
    lower, upper = float(bounds[0]), float(bounds[1])
    if lower <= average <= upper:
        return 6.0
    distance = lower - average if average < lower else average - upper
    return round(max(-8.0, 2.0 - distance), 3)


def _recent_distance_score(text: str, recent_texts: list[str]) -> float:
    normalized = _normalize_surface(text)
    if not normalized or not recent_texts:
        return 3.0
    normalized_recent = [_normalize_surface(item) for item in recent_texts]
    if normalized in normalized_recent:
        return -35.0
    opening = " ".join(normalized.split()[:6])
    if opening and any(" ".join(item.split()[:6]) == opening for item in normalized_recent):
        return -8.0
    candidate_terms = set(normalized.split())
    maximum_overlap = max(
        (
            len(candidate_terms & set(item.split())) / max(1, len(candidate_terms | set(item.split())))
            for item in normalized_recent
        ),
        default=0.0,
    )
    return round(5.0 * (1.0 - maximum_overlap), 3)


def _normalize_surface(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", str(value).lower()))


def _locked(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        **payload,
        "meaning_change_allowed": False,
        "fact_generation_allowed": False,
        "certainty_change_allowed": False,
        "source_change_allowed": False,
        "memory_write_active": False,
        "identity_change_allowed": False,
        "governance_change_allowed": False,
        "authority_change_allowed": False,
        "voice_owns_expression_style": True,
        "database_write_performed": False,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": CANDIDATE_GARDEN_BOUNDARY,
    }
