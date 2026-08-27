from __future__ import annotations

import re
from typing import Any

from .registry import truncate
from .supported_semantics import (
    build_supported_semantic_packet,
    build_text_supported_semantic_packet,
    semantic_units_for_formation,
)


WHOLE_ANSWER_COMPOSITION_BOUNDARY = (
    "current_visible_answer_semantic_assembly_only_no_fact_invention_memory_"
    "identity_personality_governance_authority_training_or_action_change"
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "retained_knowledge_write_active": False,
    "identity_change": False,
    "personality_change": False,
    "governance_change": False,
    "authority_change": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "expression_authority": False,
    "hidden_chain_of_thought_exposed": False,
}

_INTERNAL_SCAFFOLD_MARKERS = (
    "response obligation",
    "obligation_id",
    "typed operation result",
    "semantic fulfillment receipt",
    "semantic unit id",
    "missing_ground",
    "responsible_owner",
    "internal reasoning scaffold",
)


def whole_answer_composition_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "whole_answer_composition_ready",
            "version": "v1_ordered_semantic_whole_answer",
            "semantic_deduplication": True,
            "prompt_echo_is_answer": False,
            "damaged_surface_is_released": False,
            "internal_scaffolding_is_released": False,
            "nlo_owns_final_wording": True,
            "composition_changes_supported_meaning": False,
            "composition_invents_missing_content": False,
            "provenance_boundary": WHOLE_ANSWER_COMPOSITION_BOUNDARY,
        }
    )


def compose_whole_answer(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Assemble typed current-turn results once before NLO realization.

    This layer does not solve requested operations. It orders the results that
    their responsible owners already completed, merges duplicate supported
    meaning, and keeps diagnostic scaffolding behind the expression boundary.
    """

    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or ""), 3000)
    seed = _clean_surface(str(payload.get("content_seed") or ""))
    obligations = [
        item
        for item in payload.get("response_obligations") or []
        if isinstance(item, dict) and item.get("required") is not False
    ][:24]
    operations = (
        payload.get("answer_operations")
        if isinstance(payload.get("answer_operations"), dict)
        else {}
    )
    results = [
        item for item in operations.get("results") or [] if isinstance(item, dict)
    ][:24]
    result_by_id = {
        str(item.get("obligation_id") or ""): item
        for item in results
        if str(item.get("obligation_id") or "")
    }
    obligation_by_id = {
        str(item.get("id") or ""): item
        for item in obligations
        if str(item.get("id") or "")
    }
    ordered_ids = [
        str(item.get("id") or "")
        for item in obligations
        if str(item.get("id") or "") in result_by_id
    ]
    ordered_ids.extend(
        obligation_id
        for obligation_id in result_by_id
        if obligation_id not in ordered_ids
    )

    completed = [
        result_by_id[obligation_id]
        for obligation_id in ordered_ids
        if result_by_id[obligation_id].get("status") == "completed"
    ]
    unresolved = [
        result_by_id[obligation_id]
        for obligation_id in ordered_ids
        if result_by_id[obligation_id].get("status") in {"missing_input", "unsupported"}
    ]
    material_result_count = len(completed) + len(unresolved)
    if material_result_count < 2:
        return _with_guards(
            {
                "status": "whole_answer_composition_not_needed",
                "version": "v1_ordered_semantic_whole_answer",
                "applied": False,
                "content_seed": seed,
                "supported_semantics": {},
                "operation_count": material_result_count,
                "completed_operation_count": len(completed),
                "unresolved_operation_count": len(unresolved),
                "composition_order": ordered_ids,
                "segments": [],
                "semantic_unit_count": 0,
                "deduplicated_semantic_unit_count": 0,
                "surface_fragment_count": 0,
                "held_surface_fragments": [],
                "nlo_owns_final_wording": True,
                "composition_changes_supported_meaning": False,
                "composition_invents_missing_content": False,
                "provenance_boundary": WHOLE_ANSWER_COMPOSITION_BOUNDARY,
            }
        )

    prompt_keys = {
        _surface_key(prompt),
        *(
            _surface_key(str(item.get("source_text") or ""))
            for item in obligations
        ),
    }
    prompt_keys.discard("")
    surface_fragments: list[str] = []
    surface_keys: set[str] = set()
    surface_sentence_keys: set[str] = set()
    deduplicated_surface_sentence_count = 0
    held_surface_fragments: list[dict[str, str]] = []
    segments: list[dict[str, Any]] = []
    semantic_units: list[dict[str, Any]] = []
    semantic_index: dict[str, int] = {}
    semantic_input_count = 0
    source_refs: list[str] = []

    if seed:
        seed_key = _surface_key(seed)
        seed_hold_reason = _surface_hold_reason(seed, prompt_keys)
        if seed_key and not seed_hold_reason:
            deduplicated_seed, removed = _deduplicate_surface_sentences(
                seed, surface_sentence_keys
            )
            deduplicated_surface_sentence_count += removed
            if deduplicated_seed:
                surface_fragments.append(deduplicated_seed)
                surface_keys.add(_surface_key(deduplicated_seed))
        elif seed_hold_reason:
            held_surface_fragments.append(
                {"obligation_id": "existing-content-seed", "reason": seed_hold_reason}
            )

    for obligation_id in ordered_ids:
        result = result_by_id[obligation_id]
        obligation = obligation_by_id.get(obligation_id, {})
        status = str(result.get("status") or "")
        operation = str(result.get("operation") or "")
        refs = _texts(result.get("source_refs"))
        source_refs.extend(refs)
        segment: dict[str, Any] = {
            "obligation_id": obligation_id,
            "operation": operation,
            "status": status,
            "surface_included": False,
            "semantic_unit_ids": [],
            "source_refs": refs,
        }

        if status == "completed":
            packet = (
                result.get("supported_semantics")
                if isinstance(result.get("supported_semantics"), dict)
                else {}
            )
            units = semantic_units_for_formation(packet)
            expression = _clean_surface(str(result.get("expression_seed") or ""))
            if not units and expression:
                fallback_packet = build_text_supported_semantic_packet(
                    expression,
                    answer_kind=f"whole_answer_{operation or 'operation'}",
                    source_kind=_supported_source_kind(result),
                    source_refs=refs,
                    certainty="owner_supported_current_turn",
                    scope="current_dialogue_obligation",
                )
                units = semantic_units_for_formation(fallback_packet)
            for position, raw_unit in enumerate(units):
                semantic_input_count += 1
                unit = {
                    **raw_unit,
                    "id": truncate(
                        f"whole_{obligation_id}_{raw_unit.get('id') or position + 1}",
                        120,
                    ),
                    "obligation_ids": list(
                        dict.fromkeys(
                            [
                                *[
                                    str(item)
                                    for item in raw_unit.get("obligation_ids") or []
                                    if str(item)
                                ],
                                obligation_id,
                            ]
                        )
                    ),
                    "response_functions": list(
                        dict.fromkeys(
                            [
                                *[
                                    str(item)
                                    for item in raw_unit.get("response_functions") or []
                                    if str(item)
                                ],
                                operation,
                            ]
                        )
                    ),
                    "ownership_validated": True,
                    "origin_unit_id": str(raw_unit.get("id") or ""),
                    "origin_source_class": str(
                        result.get("expression_source_id") or "typed_answer_owner"
                    ),
                }
                semantic_key = _semantic_key(unit)
                if semantic_key in semantic_index:
                    existing = semantic_units[semantic_index[semantic_key]]
                    existing["obligation_ids"] = list(
                        dict.fromkeys(
                            [*existing.get("obligation_ids", []), obligation_id]
                        )
                    )
                    existing["response_functions"] = list(
                        dict.fromkeys(
                            [*existing.get("response_functions", []), operation]
                        )
                    )
                    existing["source_refs"] = list(
                        dict.fromkeys([*existing.get("source_refs", []), *refs])
                    )[:40]
                    segment["semantic_unit_ids"].append(str(existing.get("id") or ""))
                    continue
                semantic_index[semantic_key] = len(semantic_units)
                semantic_units.append(unit)
                segment["semantic_unit_ids"].append(str(unit.get("id") or ""))

            surface_reason = _surface_hold_reason(expression, prompt_keys)
            surface_key = _surface_key(expression)
            if surface_reason:
                if expression:
                    held_surface_fragments.append(
                        {
                            "obligation_id": obligation_id,
                            "reason": surface_reason,
                        }
                    )
            elif surface_key and surface_key not in surface_keys:
                deduplicated_expression, removed = _deduplicate_surface_sentences(
                    expression, surface_sentence_keys
                )
                deduplicated_surface_sentence_count += removed
                if deduplicated_expression:
                    surface_fragments.append(deduplicated_expression)
                    surface_keys.add(_surface_key(deduplicated_expression))
                    segment["surface_included"] = True
        else:
            missing_input = _clean_surface(str(result.get("missing_input") or ""))
            if missing_input:
                hold_unit = {
                    "id": truncate(f"whole_{obligation_id}_missing_input", 120),
                    "role": "limit",
                    "relation": "contrast",
                    "subject": "I",
                    "predicate": "still need",
                    "object": missing_input,
                    "text": f"I still need {missing_input} for that part.",
                    "required": True,
                    "supported": True,
                    "source_kind": "current_session_observation",
                    "source_refs": refs,
                    "certainty": "missing_input_visible",
                    "scope": "current_dialogue_obligation",
                    "obligation_ids": [obligation_id],
                    "response_functions": [operation],
                    "ownership_validated": True,
                }
                semantic_input_count += 1
                semantic_key = _semantic_key(hold_unit)
                if semantic_key not in semantic_index:
                    semantic_index[semantic_key] = len(semantic_units)
                    semantic_units.append(hold_unit)
                hold_text = str(hold_unit["text"])
                hold_key = _surface_key(hold_text)
                if hold_key not in surface_keys:
                    deduplicated_hold, removed = _deduplicate_surface_sentences(
                        hold_text, surface_sentence_keys
                    )
                    deduplicated_surface_sentence_count += removed
                    if deduplicated_hold:
                        surface_fragments.append(deduplicated_hold)
                        surface_keys.add(_surface_key(deduplicated_hold))
                        segment["surface_included"] = True
                segment["semantic_unit_ids"].append(str(hold_unit["id"]))
        segments.append(segment)

    composed_seed = _join_fragments(surface_fragments)
    packet = build_supported_semantic_packet(
        {
            "answer_kind": "whole_answer_composition",
            "certainty": "mixed_current_turn_owner_results",
            "scope": "current_dialogue_obligations",
            "source_refs": list(dict.fromkeys(source_refs))[:40],
            "fallback_text": composed_seed,
            "units": semantic_units,
            "expression_mode": "nlo_owned_whole_answer_realization",
            "source_wording_is_surface_requirement": False,
            "original_expression_required": False,
        }
    )
    return _with_guards(
        {
            "status": "whole_answer_composed",
            "version": "v1_ordered_semantic_whole_answer",
            "applied": True,
            "content_seed": _bounded_surface(composed_seed, 5000),
            "supported_semantics": packet,
            "operation_count": material_result_count,
            "completed_operation_count": len(completed),
            "unresolved_operation_count": len(unresolved),
            "composition_order": ordered_ids,
            "segments": segments,
            "semantic_input_unit_count": semantic_input_count,
            "semantic_unit_count": len(semantic_units),
            "deduplicated_semantic_unit_count": max(
                0, semantic_input_count - len(semantic_units)
            ),
            "surface_fragment_count": len(surface_fragments),
            "deduplicated_surface_sentence_count": (
                deduplicated_surface_sentence_count
            ),
            "held_surface_fragments": held_surface_fragments,
            "internal_scaffolding_exposed": False,
            "prompt_echo_used_as_answer": False,
            "damaged_surface_released": False,
            "nlo_owns_final_wording": True,
            "composition_changes_supported_meaning": False,
            "composition_invents_missing_content": False,
            "provenance_boundary": WHOLE_ANSWER_COMPOSITION_BOUNDARY,
        }
    )


def _surface_hold_reason(value: str, prompt_keys: set[str]) -> str:
    if not value:
        return "owner_returned_no_surface"
    if "\ufffd" in value or _contains_mojibake(value):
        return "damaged_encoding_held"
    if _contains_internal_scaffold(value):
        return "internal_scaffolding_held"
    if _surface_key(value) in prompt_keys:
        return "exact_prompt_echo_held"
    return ""


def _contains_internal_scaffold(value: str) -> bool:
    lower = value.lower()
    return any(marker in lower for marker in _INTERNAL_SCAFFOLD_MARKERS)


def _contains_mojibake(value: str) -> bool:
    return any(marker in value for marker in ("\u00c3\u00a2", "\u00e2\u20ac", "\u00c2\u00a0"))


def _clean_surface(value: str) -> str:
    value = "".join(character for character in str(value or "") if character in "\n\t" or ord(character) >= 32)
    paragraphs = [
        " ".join(item.split())
        for item in re.split(r"\n\s*\n", value.strip())
        if item.strip()
    ]
    return "\n\n".join(paragraphs)


def _surface_key(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", str(value or "").lower()))


def _semantic_key(unit: dict[str, Any]) -> str:
    meaning_keys = sorted(
        {
            _surface_key(str(item))
            for item in unit.get("meaning_keys") or []
            if _surface_key(str(item))
        }
    )
    if meaning_keys:
        qualifiers = "|".join(
            _surface_key(str(unit.get(field) or ""))
            for field in (
                "relation",
                "polarity",
                "condition",
                "reason",
                "contrast",
                "qualifier",
            )
        )
        return "meaning:" + "|".join(meaning_keys) + "|" + qualifiers
    structured = "|".join(
        _surface_key(str(unit.get(field) or ""))
        for field in ("subject", "predicate", "object", "condition", "reason")
    ).strip("|")
    if structured:
        return "structured:" + structured
    return "text:" + _surface_key(str(unit.get("text") or ""))


def _supported_source_kind(result: dict[str, Any]) -> str:
    source_id = str(result.get("expression_source_id") or "")
    if source_id == "answer_engine":
        return "verified_domain_answer"
    if source_id in {"reviewed_memory", "contextual_approved_memory"}:
        return "reviewed_memory"
    return "current_session_observation"


def _join_fragments(fragments: list[str]) -> str:
    return "\n\n".join(fragment for fragment in fragments if fragment).strip()


def _deduplicate_surface_sentences(
    value: str,
    seen: set[str],
) -> tuple[str, int]:
    paragraphs: list[str] = []
    removed = 0
    for paragraph in re.split(r"\n\s*\n", value):
        kept: list[str] = []
        sentences = [
            item.strip()
            for item in re.split(r"(?<=[.!?])\s+", paragraph.strip())
            if item.strip()
        ]
        for sentence in sentences:
            key = _surface_key(sentence)
            if key and key in seen:
                removed += 1
                continue
            if key:
                seen.add(key)
            kept.append(sentence)
        if kept:
            paragraphs.append(" ".join(kept))
    return "\n\n".join(paragraphs), removed


def _bounded_surface(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _texts(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [truncate(str(item).strip(), 500) for item in value if str(item).strip()][:40]


def _with_guards(payload: dict[str, Any]) -> dict[str, Any]:
    return {**payload, **GUARDS}
