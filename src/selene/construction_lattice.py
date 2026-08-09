from __future__ import annotations

from copy import deepcopy
from typing import Any


CONSTRUCTION_LATTICE_BOUNDARY = (
    "grammatical_construction_options_only_preserve_supported_meaning_evidence_certainty_and_authority"
)

SUPPORTED_DIMENSIONS = (
    "condition_position",
    "reason_position",
    "clause_linking",
    "development_depth",
    "dialogue_act",
    "voice_focus",
)


def construction_lattice_status() -> dict[str, Any]:
    return _locked(
        {
            "status": "construction_lattice_ready",
            "version": "v1_meaning_preserving_construction_specs",
            "supported_dimensions": list(SUPPORTED_DIMENSIONS),
            "default_behavior": "as_supplied",
            "complete_response_candidates_generated": False,
            "candidate_selection_active": False,
            "candidate_garden_operates_downstream": True,
        }
    )


def build_construction_lattice(frame: dict[str, Any] | None = None) -> dict[str, Any]:
    frame = frame or {}
    propositions = [
        deepcopy(item)
        for item in frame.get("propositions") or []
        if isinstance(item, dict)
    ]
    unit_ids = [
        str(item.get("id") or f"semantic_{index + 1}")
        for index, item in enumerate(propositions)
    ]
    required_ids = [
        unit_id
        for unit_id, item in zip(unit_ids, propositions)
        if item.get("required", True)
    ]
    meaning_signature = list(
        dict.fromkeys(
            str(marker)
            for item in propositions
            for marker in item.get("meaning_keys") or []
            if str(marker).strip()
        )
    )
    exactness_locked_ids = [
        unit_id
        for unit_id, item in zip(unit_ids, propositions)
        if item.get("exactness_lock") is True
    ]
    text_grounded_ids = [
        unit_id
        for unit_id, item in zip(unit_ids, propositions)
        if str(item.get("text") or "").strip()
    ]
    constructions: list[dict[str, Any]] = [
        _spec(
            "construction:as_supplied",
            "as supplied",
            required_ids,
            meaning_signature,
            dimensions=[],
            style={},
            unit_overrides={},
            description="Keep the supplied grammatical shape while preserving every supported unit.",
        )
    ]
    held: list[dict[str, str]] = []

    if not propositions:
        held.append({"dimension": "all", "reason": "no_semantic_units"})
    elif text_grounded_ids:
        held.append(
            {
                "dimension": "all",
                "reason": "text_grounded_prose_remains_fixed_until_structured_meaning_is_available",
            }
        )
    elif exactness_locked_ids:
        held.append(
            {
                "dimension": "all",
                "reason": "exactness_locked_units_hold_response_construction_fixed",
            }
        )
    else:
        for index, (unit_id, item) in enumerate(zip(unit_ids, propositions)):
            if str(item.get("condition") or "").strip():
                for position in ("front", "end"):
                    condition_controls: dict[str, Any] = {
                        "condition_position": position
                    }
                    condition_dimensions = ["condition_position"]
                    if str(item.get("reason") or "").strip():
                        condition_controls["reason_position"] = (
                            "end" if position == "front" else "front"
                        )
                        condition_dimensions.append("reason_position")
                    _append(
                        constructions,
                        _spec(
                            f"construction:condition_{position}:{unit_id}",
                            f"condition {position}",
                            required_ids,
                            meaning_signature,
                            dimensions=condition_dimensions,
                            style={},
                            unit_overrides={unit_id: condition_controls},
                            description=f"Place {unit_id}'s supplied condition at the {position} of its clause.",
                        ),
                    )
            if str(item.get("reason") or "").strip():
                for position in ("front", "end"):
                    reason_controls: dict[str, Any] = {"reason_position": position}
                    reason_dimensions = ["reason_position"]
                    if str(item.get("condition") or "").strip():
                        reason_controls["condition_position"] = (
                            "end" if position == "front" else "front"
                        )
                        reason_dimensions.append("condition_position")
                    _append(
                        constructions,
                        _spec(
                            f"construction:reason_{position}:{unit_id}",
                            f"reason {position}",
                            required_ids,
                            meaning_signature,
                            dimensions=reason_dimensions,
                            style={},
                            unit_overrides={unit_id: reason_controls},
                            description=f"Place {unit_id}'s supplied reason at the {position} of its clause.",
                        ),
                    )

            allowed_moods = _string_list(item.get("allowed_moods"))
            supplied_mood = str(item.get("mood") or "declarative").lower()
            for mood in allowed_moods:
                mood = mood.lower()
                if mood == supplied_mood or mood not in {"declarative", "interrogative", "imperative"}:
                    continue
                _append(
                    constructions,
                    _spec(
                        f"construction:{mood}:{unit_id}",
                        f"{mood} dialogue act",
                        required_ids,
                        meaning_signature,
                        dimensions=["dialogue_act"],
                        style={},
                        unit_overrides={unit_id: {"mood": mood}},
                        description=f"Express {unit_id} as an explicitly permitted {mood} act.",
                    ),
                )
            if not allowed_moods:
                held.append(
                    {
                        "dimension": f"dialogue_act:{unit_id}",
                        "reason": "no_explicit_allowed_moods",
                    }
                )

            voice_alternatives = item.get("voice_alternatives")
            if isinstance(voice_alternatives, dict):
                for voice, mapping in voice_alternatives.items():
                    voice = str(voice).lower()
                    if voice not in {"active", "passive"} or not isinstance(mapping, dict):
                        continue
                    if mapping.get("meaning_equivalent") is not True:
                        held.append(
                            {
                                "dimension": f"voice_focus:{unit_id}:{voice}",
                                "reason": "voice_mapping_not_marked_meaning_equivalent",
                            }
                        )
                        continue
                    grammatical_fields = {
                        key: deepcopy(value)
                        for key, value in mapping.items()
                        if key
                        in {
                            "subject",
                            "subject_number",
                            "predicate",
                            "object",
                            "agent",
                            "voice",
                        }
                    }
                    grammatical_fields["voice"] = voice
                    if not grammatical_fields.get("predicate"):
                        grammatical_fields["predicate"] = item.get("predicate") or item.get("verb")
                    _append(
                        constructions,
                        _spec(
                            f"construction:{voice}_focus:{unit_id}",
                            f"{voice} focus",
                            required_ids,
                            meaning_signature,
                            dimensions=["voice_focus"],
                            style={},
                            unit_overrides={unit_id: grammatical_fields},
                            description=f"Use the explicitly mapped {voice} construction for {unit_id}.",
                        ),
                    )
            else:
                held.append(
                    {
                        "dimension": f"voice_focus:{unit_id}",
                        "reason": "no_explicit_meaning_equivalent_role_mapping",
                    }
                )

        if len(propositions) >= 2:
            moods = {str(item.get("mood") or "declarative").lower() for item in propositions}
            if moods == {"declarative"}:
                for linking in ("split", "joined"):
                    _append(
                        constructions,
                        _spec(
                            f"construction:clauses_{linking}",
                            f"{linking} clauses",
                            required_ids,
                            meaning_signature,
                            dimensions=["clause_linking"],
                            style={"clause_linking": linking},
                            unit_overrides={},
                            description=f"Keep the same clauses in a {linking} response shape.",
                        ),
                    )
            else:
                held.append(
                    {
                        "dimension": "clause_linking",
                        "reason": "mixed_dialogue_acts_remain_separate",
                    }
                )
            for depth in ("compact", "developed"):
                _append(
                    constructions,
                    _spec(
                        f"construction:{depth}",
                        f"{depth} development",
                        required_ids,
                        meaning_signature,
                        dimensions=["development_depth"],
                        style={"response_depth": depth},
                        unit_overrides={},
                        description=f"Realize every supported unit in a {depth} response shape.",
                    ),
                )
        else:
            held.extend(
                [
                    {"dimension": "clause_linking", "reason": "requires_multiple_units"},
                    {"dimension": "development_depth", "reason": "requires_multiple_units"},
                ]
            )

    available_dimensions = list(
        dict.fromkeys(
            dimension
            for item in constructions
            for dimension in item.get("dimensions") or []
        )
    )
    return _locked(
        {
            "status": (
                "construction_lattice_ready"
                if len(constructions) > 1
                else "construction_lattice_as_supplied_only"
            ),
            "version": "v1_meaning_preserving_construction_specs",
            "formation_mode": str(frame.get("formation_mode") or "text_grounded"),
            "default_construction_id": "construction:as_supplied",
            "construction_count": len(constructions),
            "available_dimensions": available_dimensions,
            "constructions": constructions,
            "held_options": held,
            "required_semantic_unit_ids": required_ids,
            "meaning_signature": meaning_signature,
            "exactness_locked_unit_ids": exactness_locked_ids,
            "text_grounded_unit_ids": text_grounded_ids,
            "complete_response_candidates_generated": False,
            "candidate_selection_active": False,
        }
    )


def apply_construction_specification(
    frame: dict[str, Any],
    specification: dict[str, Any] | None,
) -> dict[str, Any]:
    result = deepcopy(frame)
    specification = deepcopy(specification or {})
    if not specification:
        return result
    allowed_ids = {
        str(item.get("id") or f"semantic_{index + 1}")
        for index, item in enumerate(result.get("propositions") or [])
        if isinstance(item, dict)
    }
    overrides = specification.get("unit_overrides")
    overrides = overrides if isinstance(overrides, dict) else {}
    propositions: list[dict[str, Any]] = []
    for index, raw in enumerate(result.get("propositions") or []):
        if not isinstance(raw, dict):
            continue
        item = deepcopy(raw)
        unit_id = str(item.get("id") or f"semantic_{index + 1}")
        requested = overrides.get(unit_id) if unit_id in allowed_ids else None
        if isinstance(requested, dict) and item.get("exactness_lock") is not True and not str(item.get("text") or "").strip():
            construction_controls = {
                key: value
                for key, value in requested.items()
                if key in {"condition_position", "reason_position"}
            }
            if construction_controls:
                item["construction_controls"] = construction_controls
            for key in (
                "mood",
                "voice",
                "subject",
                "subject_number",
                "predicate",
                "object",
                "agent",
            ):
                if key in requested:
                    item[key] = requested[key]
        propositions.append(item)
    result["propositions"] = propositions
    style = specification.get("style") if isinstance(specification.get("style"), dict) else {}
    if str(style.get("response_depth") or "") in {"compact", "standard", "developed"}:
        result["response_depth"] = str(style["response_depth"])
    result["construction_style"] = {
        key: value
        for key, value in style.items()
        if key in {"clause_linking", "response_depth"}
    }
    result["construction_specification"] = specification
    return result


def _spec(
    construction_id: str,
    label: str,
    required_ids: list[str],
    meaning_signature: list[str],
    *,
    dimensions: list[str],
    style: dict[str, Any],
    unit_overrides: dict[str, Any],
    description: str,
) -> dict[str, Any]:
    return {
        "construction_id": construction_id,
        "label": label,
        "description": description,
        "dimensions": dimensions,
        "style": style,
        "unit_overrides": unit_overrides,
        "required_semantic_unit_ids": list(required_ids),
        "meaning_signature": list(meaning_signature),
        "meaning_preservation_required": True,
        "evidence_and_certainty_change_allowed": False,
        "eligible": True,
    }


def _append(items: list[dict[str, Any]], item: dict[str, Any]) -> None:
    if item["construction_id"] not in {existing["construction_id"] for existing in items}:
        items.append(item)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return list(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


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
        "provenance_boundary": CONSTRUCTION_LATTICE_BOUNDARY,
    }
