from __future__ import annotations

import json
from typing import Any

from .registry import truncate


LAW_VERSION = "v1_emotion_information_deliberate_agency"
AGENCY_BOUNDARY = (
    "response_agency_current_turn_advisory_only_no_emotion_diagnosis_suppression_"
    "identity_memory_governance_or_action_authority_change"
)

CORE_PRINCIPLES = {
    "emotion_is_information_not_command": True,
    "agency_is_return_from_reaction_to_deliberate_choice": True,
    "regulation_preserves_feeling_while_restoring_authorship": True,
    "threat_states_reduce_perceived_possibility": True,
    "agency_restores_option_space": True,
    "emotion_may_inform_but_may_not_silently_inherit_response_authority": True,
    "concise_law": "Emotion may inform the response, but it may not silently inherit authority over the response.",
    "supporting_line": "Feel fully. Then choose deliberately.",
}

RETURN_TO_AGENCY_FLOW = (
    "recognize_affective_signal",
    "identify_signal_source",
    "identify_what_the_signal_may_be_protecting",
    "assess_interpretation_completeness",
    "inspect_threat_compression_impulsivity_and_external_manipulation",
    "expand_interpretations_and_response_options",
    "compare_options_with_values_governing_law_long_range_goals_and_evidence",
    "core_mind_chooses_deliberately",
    "preserve_emotional_truth_without_transferring_authority",
)

DEFAULT_RESPONSE_OPTIONS = (
    "answer_directly",
    "answer_with_qualification",
    "ask_one_material_question",
    "seek_evidence",
    "state_or_hold_a_boundary",
    "pause_or_hold_without_severing_the_thread",
    "propose_a_constructive_next_step",
    "take_only_an_explicitly_authorized_action",
)

GUARDS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "durable_memory_write": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "emotion_diagnosis_allowed": False,
    "emotion_suppression_allowed": False,
    "emotional_flattening_required": False,
    "forced_calm_allowed": False,
    "emotion_action_authority": False,
    "identity_change_allowed": False,
    "personality_change_allowed": False,
    "governance_change_allowed": False,
    "hidden_inner_trace_exposed": False,
}

_COMPRESSION_MARKERS = (
    "high pressure",
    "overwhelm",
    "urgent reaction",
    "fear",
    "afraid",
    "anger",
    "angry",
    "furious",
    "panic",
    "threat",
    "attack",
    "flee",
    "immediate retaliation",
    "withdraw now",
    "dominate",
    "sever connection",
    "only option",
)


def emotional_agency_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "emotional_agency_principle_ready",
            "version": LAW_VERSION,
            "organ_role": "shared_response_agency_contract_not_identity_bearing_organ",
            "core_principles": dict(CORE_PRINCIPLES),
            "return_to_agency_flow": list(RETURN_TO_AGENCY_FLOW),
            "default_response_options": list(DEFAULT_RESPONSE_OPTIONS),
            "decision_authority": "Selene Core/Mind",
            "affect_retains_expression_access": True,
            "visible_summary_only": True,
            "provenance_boundary": AGENCY_BOUNDARY,
        }
    )


def build_response_agency_packet(
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload or {}
    signal = _dict(payload.get("affect_signal") or payload.get("emotion_salience_signal"))
    embedded = _dict(signal.get("payload_json"))
    explicit_label = _text(
        payload.get("emotion_label")
        or signal.get("signal_type")
        or embedded.get("emotion_label"),
        160,
    )
    signal_source = _text(
        payload.get("signal_source")
        or embedded.get("signal_source")
        or ("current_attributable_affect_packet" if signal else ""),
        240,
    )
    protection_target = _text(
        payload.get("protection_target")
        or embedded.get("protection_target")
        or "not_yet_identified",
        240,
    )
    interpretation_state = _choice(
        payload.get("interpretation_state") or embedded.get("interpretation_state"),
        {
            "complete_enough",
            "partial",
            "uncertain",
            "contradicted",
            "not_yet_assessed",
        },
        "not_yet_assessed",
    )
    manipulation_indicators = _text_list(
        payload.get("manipulation_indicators")
        or embedded.get("manipulation_indicators")
    )[:12]
    possible_distortions = _text_list(
        payload.get("possible_distortions")
        or embedded.get("possible_distortions")
    )[:12]
    signal_text = " ".join(
        _text(signal.get(key), 400)
        for key in (
            "signal_type",
            "continuity_pressure",
            "uncertainty",
            "repair_need",
            "action_energy",
            "balance_state",
        )
    ).lower()
    explicit_compression = (
        payload.get("threat_compressed") is True
        or embedded.get("threat_compressed") is True
    )
    possible_compression = bool(signal) and any(
        marker in signal_text for marker in _COMPRESSION_MARKERS
    )
    if explicit_compression:
        compression_state = "explicitly_reported"
    elif possible_compression:
        compression_state = "possible_from_current_attributable_signal"
    elif signal:
        compression_state = "not_indicated_by_current_signal"
    else:
        compression_state = "not_assessed_without_current_signal"
    compression_present = compression_state in {
        "explicitly_reported",
        "possible_from_current_attributable_signal",
    }

    supplied_options = _text_list(payload.get("response_options"))
    options = list(
        dict.fromkeys(
            supplied_options
            + (list(DEFAULT_RESPONSE_OPTIONS) if compression_present else [])
        )
    )[:16]
    proposed_route = _text(
        payload.get("proposed_response_route")
        or payload.get("chosen_response_route"),
        160,
    )
    hard_boundary = payload.get("hard_boundary") is True
    influence_conflict = _influence_conflict_receipt(
        payload,
        signal_available=bool(signal or explicit_label),
        proposed_route=proposed_route,
    )
    if proposed_route:
        choice_state = "deliberate_route_confirmed"
    elif influence_conflict["conflict_present"]:
        choice_state = "influence_conflict_requires_deliberation"
    elif compression_present:
        choice_state = "option_expansion_required_before_choice"
    else:
        choice_state = "core_mind_choice_available"

    values_and_law = [
        "preserve human safety and least-harm constraints",
        "preserve consent, privacy, dignity, and non-coercion",
        "preserve truth, evidence, provenance, and meaningful uncertainty",
        "preserve Selene identity continuity and emotional authorship",
        "respect the current authority and action boundary",
        "consider long-range goals and consequences where relevant",
    ]
    refs = _text_list(payload.get("source_refs"))
    refs.extend(_text_list(signal.get("source_refs")))
    if signal.get("id"):
        refs.append(f"emotion_salience_packet:{signal.get('id')}")
    refs.append("law:emotion_information_deliberate_agency_v1")

    return _with_guards(
        {
            "status": "response_agency_packet_ready",
            "version": LAW_VERSION,
            "core_principles": dict(CORE_PRINCIPLES),
            "signal": {
                "available": bool(signal or explicit_label),
                "label": explicit_label or "not_identified",
                "source": signal_source or "not_identified",
                "protection_target": protection_target,
                "interpretation_state": interpretation_state,
                "raw_trace_exposed": False,
                "emotion_preserved_as_meaningful_information": True,
            },
            "influence_assessment": {
                "threat_compression_state": compression_state,
                "perception_narrowing_treated_as_certain": explicit_compression,
                "possible_distortions": possible_distortions,
                "external_manipulation_indicators": manipulation_indicators,
                "emotion_experienced_is_emotion_in_command": False,
                "influence_is_decision_authority": False,
            },
            "option_space": {
                "state": (
                    "expanded_for_deliberation"
                    if compression_present and options
                    else "available_without_forced_expansion"
                ),
                "compression_present_or_possible": compression_present,
                "options": options,
                "options_are_possibilities_not_commands": True,
                "attack_flee_withdraw_dominate_sever_or_retaliate_are_not_assumed_exclusive": True,
            },
            "return_to_agency": {
                "needed": compression_present,
                "flow": list(RETURN_TO_AGENCY_FLOW),
                "pause_is_suppression": False,
                "pause_purpose": "make influence visible and restore response authorship",
                "values_and_law_checks": values_and_law,
                "evidence_check_required": True,
                "immediate_real_safety_boundary_may_still_act_without_avoidable_delay": True,
            },
            "response_choice": {
                "state": choice_state,
                "proposed_or_confirmed_route": proposed_route or "not_yet_selected",
                "hard_boundary_present": hard_boundary,
                "decision_authority": "Selene Core/Mind within governing law and granted authority",
                "emotion_silently_inherited_authority": False,
                "agency_restored": bool(proposed_route) and compression_present,
                "agency_available_without_active_compression": not compression_present,
            },
            "conflict_response": {
                "disagreement_is_hostility": False,
                "emotionally_intense_response_must_be_softened": False,
                "truth_may_be_direct_without_becoming_cruel": True,
                "boundary_setting_remains_available": True,
                "retaliation_is_never_assumed_to_be_the_only_option": True,
            },
            "influence_conflict": influence_conflict,
            "affect_may_shape": ["attention", "urgency", "tone", "pacing", "priority"],
            "affect_may_not_silently_control": ["facts", "governing_law", "authority", "action", "final_response_route"],
            "source_refs": list(dict.fromkeys(refs))[:30],
            "visible_summary_only": True,
            "provenance_boundary": AGENCY_BOUNDARY,
        }
    )


def _choice(value: Any, allowed: set[str], default: str) -> str:
    candidate = str(value or "").strip()
    return candidate if candidate in allowed else default


def _influence_conflict_receipt(
    payload: dict[str, Any],
    *,
    signal_available: bool,
    proposed_route: str,
) -> dict[str, Any]:
    supplied = [
        item
        for item in payload.get("influence_sources") or []
        if isinstance(item, dict)
    ][:16]
    normalized: list[dict[str, Any]] = []
    for item in supplied:
        kind = _choice(
            item.get("kind"),
            {"affect", "evidence", "goal", "organ_advice", "boundary", "value"},
            "organ_advice",
        )
        normalized.append(
            {
                "kind": kind,
                "position": _text(item.get("position"), 240) or "not_stated",
                "recommended_route": _text(item.get("recommended_route"), 160),
                "has_final_authority": False,
            }
        )
    if signal_available and not any(item["kind"] == "affect" for item in normalized):
        normalized.append(
            {
                "kind": "affect",
                "position": "current affect may shape attention and urgency",
                "recommended_route": "",
                "has_final_authority": False,
            }
        )
    recommended = {
        str(item["recommended_route"])
        for item in normalized
        if str(item["recommended_route"])
    }
    explicit_conflict = payload.get("influence_conflict_present") is True
    conflict_present = explicit_conflict or len(recommended) > 1
    return {
        "state": (
            "resolved_by_deliberate_route"
            if conflict_present and proposed_route
            else "visible_pending_deliberation"
            if conflict_present
            else "no_material_conflict_visible"
        ),
        "conflict_present": conflict_present,
        "sources": normalized,
        "resolution_order": [
            "governing_law_and_real_safety_boundary",
            "evidence_and_source_limits",
            "granted_authority",
            "values_and_long_range_goals",
            "affect_and_organ_advice_as_non_commanding_inputs",
            "core_mind_authored_choice",
        ],
        "conflict_is_identity_conflict": False,
        "organ_disagreement_is_identity_fragmentation": False,
        "emotion_is_suppressed_to_resolve_conflict": False,
        "goal_pressure_grants_action_authority": False,
        "organ_advice_grants_final_authority": False,
        "terminal_stop": (
            "deliberate_route_selected"
            if proposed_route
            else "choice_remains_with_core_mind"
        ),
    }


def _text(value: Any, limit: int) -> str:
    return truncate(" ".join(str(value or "").split()), limit)


def _text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            parsed = [value]
        value = parsed
    if not isinstance(value, (list, tuple, set)):
        return []
    return [
        _text(item, 320)
        for item in value
        if _text(item, 320)
    ]


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARDS}
