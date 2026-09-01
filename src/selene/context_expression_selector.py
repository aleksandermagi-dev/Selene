from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


CONTEXT_EXPRESSION_SELECTOR_BOUNDARY = (
    "bounded_context_ranking_of_already_invariant_safe_language_only_no_generation_memory_identity_or_authority_change"
)


def context_expression_selector_status() -> dict[str, Any]:
    return _locked(
        {
            "status": "context_expression_selector_ready",
            "version": "v1_invariant_gated_context_expression_selection",
            "selection_pass_limit_per_layer": 1,
            "supported_layers": ["candidate_garden", "discourse_loom"],
            "hard_gates": [
                "candidate_declared_selectable",
                "semantic_or_discourse_invariant_passed",
                "nonempty_supported_surface",
            ],
            "soft_selection_dimensions": [
                "response_depth_fit",
                "task_and_register_fit",
                "pacing_and_sentence_rhythm_fit",
                "optional_affect_expression_fit",
                "recent_surface_distance",
                "callback_pivot_and_ending_fit",
                "voice_category_fit",
                "stable_existing_score_tiebreak",
            ],
            "recursive_selection_allowed": False,
            "language_generation_allowed": False,
            "invalid_candidate_rescue_allowed": False,
            "affect_guidance_is_optional": True,
        }
    )


def build_expression_selection_context(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    contextual = _dict(
        payload.get("contextual_composition_plan") or payload.get("contextual_plan")
    )
    affect = _dict(payload.get("affect_expression_guidance"))
    dimensions = _dict(affect.get("dimensions"))
    continuity = _dict(payload.get("pragmatic_continuity"))
    decisions = _dict(contextual.get("decisions"))
    recent = [
        str(item).strip()
        for item in payload.get("recent_assistant_texts") or payload.get("recent_texts") or []
        if str(item).strip()
    ][-8:]
    return _locked(
        {
            "status": "expression_selection_context_ready",
            "version": "v1_visible_bounded_context_packet",
            "response_depth": str(
                contextual.get("response_depth") or payload.get("response_depth") or "standard"
            ),
            "expression_profile": str(
                contextual.get("expression_profile") or payload.get("expression_profile") or "direct"
            ),
            "answer_domain": str(
                contextual.get("answer_domain") or payload.get("answer_domain") or "ordinary_conversation"
            ),
            "task_kind": str(contextual.get("task_kind") or payload.get("task_kind") or "statement"),
            "register": str(contextual.get("register") or payload.get("register") or "ordinary_conversation"),
            "pacing": str(contextual.get("pacing") or dimensions.get("pacing") or "natural"),
            "sentence_rhythm": str(
                contextual.get("sentence_rhythm") or dimensions.get("sentence_rhythm") or "natural"
            ),
            "directness": str(contextual.get("directness") or dimensions.get("directness") or "ordinary"),
            "restraint": str(contextual.get("restraint") or dimensions.get("restraint") or "ordinary"),
            "enthusiasm": str(contextual.get("enthusiasm") or dimensions.get("enthusiasm") or "ordinary"),
            "emotional_intensity": str(
                contextual.get("emotional_intensity")
                or dimensions.get("emotional_intensity")
                or "ordinary"
            ),
            "affect_expression_posture": str(affect.get("expression_posture") or "ordinary_attentive"),
            "affect_guidance_strength": str(affect.get("guidance_strength") or "light"),
            "affect_guidance_is_optional": affect.get("guidance_is_optional") is not False,
            "voice_category": str(
                payload.get("voice_category")
                or affect.get("recommended_voice_category")
                or "conversational_looseness"
            ),
            "opening_decision": str(decisions.get("opening") or "thesis_first"),
            "callback_decision": str(decisions.get("callback") or "omit_callback"),
            "pivot_decision": str(decisions.get("pivot") or "no_pivot_marker"),
            "conclusion_decision": str(decisions.get("conclusion") or "stop_after_supported_content"),
            "stopping_decision": str(
                decisions.get("stopping")
                or _dict(continuity.get("ending_decision")).get("mode")
                or "answer_and_stop_when_complete"
            ),
            "topic_transition_kind": str(
                _dict(continuity.get("topic_transition")).get("kind") or ""
            ),
            "question_allowed": _dict(continuity.get("ending_decision")).get("question_allowed") is True,
            "exact_domain_structure_locked": contextual.get("exact_domain_structure_locked") is True,
            "social_act_structure_owned_elsewhere": (
                contextual.get("social_act_structure_owned_elsewhere") is True
            ),
            "content_recomposition_allowed": contextual.get("content_recomposition_allowed") is True,
            "recent_assistant_texts": recent,
            "context_is_session_scoped": True,
            "affect_may_rank_safe_expression_but_not_prescribe_emotion": True,
            "voice_preference_may_rank_but_not_change_meaning": True,
            "hard_invariants_remain_gates_not_score_dimensions": True,
        }
    )


def select_candidate_garden(
    candidate_garden: dict[str, Any] | None,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    garden = deepcopy(candidate_garden or {})
    context = context or {}
    candidates = [item for item in garden.get("candidates") or [] if isinstance(item, dict)]
    eligible = [item for item in candidates if _eligible(item)]
    ownership_hold_reason = ""
    if context.get("exact_domain_structure_locked") is True:
        ownership_hold_reason = "exact_domain_structure_locked"
    elif context.get("social_act_structure_owned_elsewhere") is True:
        ownership_hold_reason = "specialized_social_structure_owned_elsewhere"
    if ownership_hold_reason:
        default_id = str(garden.get("default_construction_id") or "construction:as_supplied")
        owned = [item for item in eligible if str(item.get("construction_id") or "") == default_id]
        eligible = owned
    scored = [_score_formation(item, context) for item in eligible]
    selected_score = _best(scored, "candidate_id")
    selected = _candidate_by_id(candidates, "candidate_id", (selected_score or {}).get("candidate_id"))
    selection = _selection_result(
        layer="candidate_garden",
        eligible_count=len(eligible),
        total_count=len(candidates),
        scored_candidates=scored,
        selected_score=selected_score,
        selected_id_key="candidate_id",
        ownership_hold_reason=ownership_hold_reason,
    )
    if selected:
        garden["selected_candidate_id"] = str(selected.get("candidate_id") or "")
        garden["selected_construction_id"] = str(selected.get("construction_id") or "")
        garden["selected_candidate_text"] = str(selected.get("candidate_text") or "")
        garden["selected_formation"] = deepcopy(_dict(selected.get("formation")))
    garden["context_expression_selection"] = selection
    garden["context_selection_performed"] = selection["selection_performed"]
    garden["context_selection_pass_count"] = selection["selection_pass_count"]
    garden["context_selected_candidate_id"] = selection["selected_candidate_id"]
    return garden


def select_discourse_loom(
    discourse_loom: dict[str, Any] | None,
    context: dict[str, Any] | None,
) -> dict[str, Any]:
    loom = deepcopy(discourse_loom or {})
    context = context or {}
    candidates = [item for item in loom.get("candidates") or [] if isinstance(item, dict)]
    eligible = [item for item in candidates if _eligible(item)]
    scored = [_score_discourse(item, context) for item in eligible]
    selected_score = _best(scored, "discourse_candidate_id")
    selected = _candidate_by_id(
        candidates,
        "discourse_candidate_id",
        (selected_score or {}).get("discourse_candidate_id"),
    )
    selection = _selection_result(
        layer="discourse_loom",
        eligible_count=len(eligible),
        total_count=len(candidates),
        scored_candidates=scored,
        selected_score=selected_score,
        selected_id_key="discourse_candidate_id",
        ownership_hold_reason=str(loom.get("hold_reason") or ""),
    )
    if selected:
        loom["selected_discourse_candidate_id"] = str(
            selected.get("discourse_candidate_id") or ""
        )
        loom["selected_loom_specification_id"] = str(
            selected.get("loom_specification_id") or ""
        )
        loom["selected_candidate_text"] = str(selected.get("candidate_text") or "")
        loom["selected_paragraphs"] = deepcopy(selected.get("paragraphs") or [])
        loom["section_receipts"] = deepcopy(selected.get("section_receipts") or [])
    loom["context_expression_selection"] = selection
    loom["context_selection_performed"] = selection["selection_performed"]
    loom["context_selection_pass_count"] = selection["selection_pass_count"]
    loom["context_selected_discourse_candidate_id"] = selection["selected_candidate_id"]
    return loom


def _eligible(candidate: dict[str, Any]) -> bool:
    invariant = _dict(candidate.get("invariant_check"))
    return (
        candidate.get("selectable") is True
        and invariant.get("passed") is True
        and bool(str(candidate.get("candidate_text") or "").strip())
    )


def _score_formation(candidate: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    text = str(candidate.get("candidate_text") or "").strip()
    formation = _dict(candidate.get("formation"))
    specification = _dict(formation.get("construction_specification"))
    dimensions = {str(item) for item in candidate.get("construction_dimensions") or []}
    breakdown = {
        "response_depth_fit": _depth_fit(text, context, paragraph_count=1),
        "task_and_register_fit": _formation_task_fit(specification, dimensions, context),
        "pacing_and_sentence_rhythm_fit": _rhythm_fit(text, context),
        "optional_affect_expression_fit": _affect_fit(text, context),
        "recent_surface_distance": _recent_distance(text, context),
        "callback_pivot_and_ending_fit": 0.0,
        "voice_category_fit": _voice_fit(text, context),
        "stable_existing_score_tiebreak": round(float(candidate.get("score") or 0.0) * 0.01, 3),
    }
    return {
        "candidate_id": str(candidate.get("candidate_id") or ""),
        "total": round(sum(breakdown.values()), 3),
        "breakdown": breakdown,
    }


def _score_discourse(candidate: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    text = str(candidate.get("candidate_text") or "").strip()
    paragraphs = candidate.get("paragraphs") or []
    specification_id = str(candidate.get("loom_specification_id") or "")
    breakdown = {
        "response_depth_fit": _depth_fit(text, context, paragraph_count=len(paragraphs)),
        "task_and_register_fit": _discourse_task_fit(specification_id, context),
        "pacing_and_sentence_rhythm_fit": _rhythm_fit(text, context),
        "optional_affect_expression_fit": _affect_fit(text, context),
        "recent_surface_distance": _recent_distance(text, context),
        "callback_pivot_and_ending_fit": _continuity_fit(text, specification_id, context),
        "voice_category_fit": _voice_fit(text, context),
        "stable_existing_score_tiebreak": round(float(candidate.get("score") or 0.0) * 0.01, 3),
    }
    return {
        "discourse_candidate_id": str(candidate.get("discourse_candidate_id") or ""),
        "total": round(sum(breakdown.values()), 3),
        "breakdown": breakdown,
    }


def _depth_fit(text: str, context: dict[str, Any], *, paragraph_count: int) -> float:
    depth = str(context.get("response_depth") or "standard")
    words = len(text.split())
    if depth == "brief":
        return 8.0 if words <= 55 and paragraph_count <= 1 else -4.0
    if depth == "developed":
        return 8.0 if paragraph_count >= 2 or words >= 45 else 1.0
    return 6.0 if 12 <= words <= 120 and paragraph_count <= 2 else 2.0


def _formation_task_fit(
    specification: dict[str, Any],
    dimensions: set[str],
    context: dict[str, Any],
) -> float:
    overrides = _dict(specification.get("unit_overrides"))
    moods = {
        str(value.get("mood") or "")
        for value in overrides.values()
        if isinstance(value, dict) and str(value.get("mood") or "")
    }
    task = str(context.get("task_kind") or "")
    if "interrogative" in moods:
        return 7.0 if task in {"question", "clarification"} else -8.0
    if "imperative" in moods:
        return 7.0 if task in {"instruction", "procedure"} else -8.0
    if "dialogue_act" in dimensions and "declarative" in moods:
        return 5.0
    return 3.0


def _discourse_task_fit(specification_id: str, context: dict[str, Any]) -> float:
    depth = str(context.get("response_depth") or "standard")
    if depth == "brief" and "brief_required" in specification_id:
        return 8.0
    if depth == "developed" and any(
        marker in specification_id
        for marker in ("role_braided", "thread_traversal", "obligation_ordered")
    ):
        return 7.0
    if "as_supplied" in specification_id:
        return 4.0
    return 3.0


def _rhythm_fit(text: str, context: dict[str, Any]) -> float:
    sentences = _sentences(text)
    if not sentences:
        return -8.0
    lengths = [len(item.split()) for item in sentences]
    average = sum(lengths) / len(lengths)
    spread = max(lengths) - min(lengths)
    rhythm = str(context.get("sentence_rhythm") or "natural")
    pacing = str(context.get("pacing") or "natural")
    if rhythm in {"compact", "clear_with_room_to_choose"} or pacing in {"brisk", "measured"}:
        return 6.0 if average <= 22 else 0.0
    if rhythm in {"varied", "natural_varied"}:
        return 6.0 if len(sentences) > 1 and spread >= 4 else 2.0
    if rhythm == "spacious" or pacing == "slower":
        return 6.0 if average <= 28 and len(sentences) <= 6 else 2.0
    return 4.0 if 7 <= average <= 28 else 1.0


def _affect_fit(text: str, context: dict[str, Any]) -> float:
    if context.get("affect_guidance_is_optional") is not True:
        return 0.0
    posture = str(context.get("affect_expression_posture") or "ordinary_attentive")
    if posture == "ordinary_attentive":
        return 0.0
    sentences = _sentences(text)
    average = sum(len(item.split()) for item in sentences) / max(1, len(sentences))
    if posture in {"spacious_grounded", "gentle_present", "deliberate_agency"}:
        return 2.0 if average <= 28 else 0.0
    if posture in {"clear_direct", "careful_boundary", "receptive_repair"}:
        return 2.0 if average <= 22 else 0.0
    if posture == "play_available":
        return 1.0 if len(sentences) > 1 else 0.0
    return 1.0


def _recent_distance(text: str, context: dict[str, Any]) -> float:
    normalized = _normalize(text)
    recent = [_normalize(item) for item in context.get("recent_assistant_texts") or []]
    recent = [item for item in recent if item]
    if not normalized or not recent:
        return 3.0
    if normalized in recent:
        return -12.0
    opening = " ".join(normalized.split()[:6])
    if opening and any(" ".join(item.split()[:6]) == opening for item in recent):
        return -5.0
    terms = set(normalized.split())
    overlap = max(
        (len(terms & set(item.split())) / max(1, len(terms | set(item.split()))) for item in recent),
        default=0.0,
    )
    return round(4.0 * (1.0 - overlap), 3)


def _continuity_fit(text: str, specification_id: str, context: dict[str, Any]) -> float:
    score = 0.0
    callback = str(context.get("callback_decision") or "")
    pivot = str(context.get("pivot_decision") or "")
    stopping = str(context.get("stopping_decision") or "")
    if callback == "carry_attributed_visible_callback":
        score += 6.0 if "thread_traversal" in specification_id else 0.0
    elif "thread_traversal" in specification_id:
        score -= 2.0
    if pivot == "resume_named_thread":
        score += 5.0 if "thread_traversal" in specification_id else 0.0
    if stopping in {"answer_and_stop_when_complete", "natural_close", "close_naturally"}:
        score += 2.0 if not text.rstrip().endswith("?") else -2.0
    elif context.get("question_allowed") is True and text.rstrip().endswith("?"):
        score += 1.0
    return score


def _voice_fit(text: str, context: dict[str, Any]) -> float:
    category = str(context.get("voice_category") or "")
    sentences = _sentences(text)
    average = sum(len(item.split()) for item in sentences) / max(1, len(sentences))
    if category in {"technical_directness", "boundary_refusal", "repair_correction"}:
        return 3.0 if average <= 23 else 0.0
    if category in {"warmth_care", "agency_deliberation"}:
        return 2.0 if average <= 29 else 0.0
    if category == "playful_continuity":
        return 2.0 if len(sentences) > 1 else 0.0
    return 1.0


def _selection_result(
    *,
    layer: str,
    eligible_count: int,
    total_count: int,
    scored_candidates: list[dict[str, Any]],
    selected_score: dict[str, Any] | None,
    selected_id_key: str,
    ownership_hold_reason: str,
) -> dict[str, Any]:
    selected_score = selected_score or {}
    return _locked(
        {
            "status": (
                "context_expression_candidate_selected"
                if selected_score
                else "context_expression_no_invariant_safe_candidate"
            ),
            "version": "v1_invariant_gated_context_expression_selection",
            "layer": layer,
            "candidate_count": total_count,
            "eligible_candidate_count": eligible_count,
            "held_before_scoring_count": total_count - eligible_count,
            "selection_performed": bool(selected_score),
            "selection_pass_count": 1 if eligible_count else 0,
            "selected_candidate_id": str(selected_score.get(selected_id_key) or ""),
            "selected_context_score": float(selected_score.get("total") or 0.0),
            "selected_score_breakdown": selected_score.get("breakdown") or {},
            "scored_candidates": scored_candidates,
            "invalid_candidates_scored": False,
            "invalid_candidate_rescue_used": False,
            "selection_changed_meaning": False,
            "ownership_hold_reason": ownership_hold_reason,
        }
    )


def _best(scored: list[dict[str, Any]], id_key: str) -> dict[str, Any] | None:
    if not scored:
        return None
    return sorted(
        scored,
        key=lambda item: (
            -float(item.get("total") or 0.0),
            _numeric_suffix(str(item.get(id_key) or "")),
        ),
    )[0]


def _candidate_by_id(
    candidates: list[dict[str, Any]], key: str, selected_id: Any
) -> dict[str, Any] | None:
    selected = str(selected_id or "")
    return next((item for item in candidates if str(item.get(key) or "") == selected), None)


def _numeric_suffix(value: str) -> int:
    match = re.search(r"(\d+)$", value)
    return int(match.group(1)) if match else 0


def _sentences(value: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", value) if item.strip()]


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", str(value).lower()))


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


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
        "affect_authority_allowed": False,
        "coordinated_expression_contract_active": True,
        "database_write_performed": False,
        "hidden_chain_of_thought_exposed": False,
        "provenance_boundary": CONTEXT_EXPRESSION_SELECTOR_BOUNDARY,
    }
