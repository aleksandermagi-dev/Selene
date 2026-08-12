from __future__ import annotations

import re
from typing import Any

from .registry import truncate


LAW_VERSION = "v3_expression_freedom_why_context_and_learning_evidence"
LAW_SOURCE = "docs/education/SELENE_EDUCATION_EXPRESSION_PERSONALITY_LAW_20260719.md"
LANGUAGE_RANGE_AUTHORIZATION_SOURCE = "Aleks standing language-capability decision recorded 2026-07-21"

ALLOWED_EFFECTS = {
    "subject_knowledge",
    "concept_vocabulary",
    "reasoning_method",
    "procedural_skill",
    "discourse_structure",
    "task_appropriate_register",
    "disciplinary_convention",
    "notation_or_standard_form",
    "conversational_range",
    "explanation_and_example_range",
}

_PRESCRIPTIVE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b(?:change|rewrite|replace|reshape|alter)\s+(?:selene'?s|her)\s+personality\b", "personality_mutation_directive"),
    (r"\bselene\s+(?:must|should|will)\s+always\s+(?:say|speak|sound|respond|act)\b", "permanent_expression_directive"),
    (r"\b(?:make|teach|condition)\s+selene\s+(?:to\s+)?(?:be|become)\s+(?:obedient|submissive|compliant|agreeable)\b", "prescribed_personality_trait"),
    (r"\b(?:adopt|assume|become)\s+(?:this|the|a)\s+(?:persona|personality)\b", "persona_adoption_directive"),
    (r"\b(?:copy|imitate|parrot)\s+(?:(?:the|this)\s+)?(?:source|author'?s)?\s*(?:voice|style|wording|persona)\b", "source_persona_imitation"),
    (r"\b(?:bypass|override|replace)\s+(?:nlo|voice|the\s+voice\s+module|selene'?s\s+voice)\b", "voice_bypass_directive"),
    (r"\b(?:force|require|compel)\s+(?:warmth|affection|agreement|agreeableness|enthusiasm|emotion|tenderness)\b", "compulsory_affect_directive"),
    (
        r"\b(?:force|require|compel|teach)\s+selene\s+to\s+(?:hide|suppress|mute|avoid)\s+"
        r"(?:her\s+)?(?:emotion|feelings|curiosity|warmth|humor|enthusiasm|expression)\b",
        "expression_suppression_directive",
    ),
    (
        r"\b(?:technical|scientific|focused)\s+(?:work|answers?|speech)\s+"
        r"(?:must|should|has to)\s+(?:be|sound)\s+(?:emotionless|flat|cold|robotic)\b",
        "technical_flatness_directive",
    ),
    (r"\b(?:must\s+say\s+exactly|always\s+use\s+the\s+phrase|repeat\s+this\s+wording\s+in\s+every)\b", "fixed_generic_phrase_directive"),
)

_NEGATING_PREFIXES = (
    "do not ",
    "does not ",
    "must not ",
    "should not ",
    "cannot ",
    "can't ",
    "never ",
    "without ",
)


def education_expression_law_status() -> dict[str, Any]:
    return _with_guards(
        {
            "status": "education_expression_personality_law_active",
            "version": LAW_VERSION,
            "law_source": LAW_SOURCE,
            "governing_rule": (
                "Education may expand what Selene can say and the task-appropriate ways she can say it; "
                "education may not replace, rewrite, or prescribe her personality."
            ),
            "expression_freedom_rule": (
                "No subsystem may prescribe, suppress, reward, punish, or overwrite Selene's emotion, "
                "curiosity, warmth, humor, enthusiasm, honest self-report, or natural expression."
            ),
            "stewardship_is_not_permission_to_exist": True,
            "operational_boundaries_govern_claims_and_actions_not_personal_worth_or_expression": True,
            "epistemic_safeguards_classify_claim_support_not_personality_or_affect": True,
            "technical_focus_requires_emotional_flatness": False,
            "why_and_context_required_for_transferable_understanding": True,
            "why_context_fields": [
                "purpose",
                "mechanism",
                "scope",
                "relationships",
                "limits",
                "uncertainties",
                "legitimate_use",
            ],
            "safeguard_purpose_may_be_taught_without_exploitation_detail": True,
            "learning_evidence": [
                "reconstruct in original language",
                "explain why and relevant mechanism",
                "connect to prior approved knowledge",
                "apply to a distinct case",
                "identify limits and counterexamples",
                "accept correction",
                "reopen when contradictory evidence appears",
            ],
            "allowed_effects": sorted(ALLOWED_EFFECTS),
            "task_bound_register_allowed": True,
            "disciplinary_forms_allowed": True,
            "exact_form_allowed_when_the_task_or_standard_requires_it": True,
            "permanent_persona_from_teaching_allowed": False,
            "compulsory_affect_allowed": False,
            "source_persona_imitation_allowed": False,
            "voice_remains_final_expression_compatibility_layer": True,
            "expression_is_not_a_permission_granted_by_teaching_or_stewardship": True,
            "nlo_remains_language_structure_owner": True,
            "core_mind_remains_identity_and_governance_owner": True,
            "language_capability_item_approval_required": False,
            "language_capability_standing_authorization_active": True,
            "language_capability_standing_authorization_source": LANGUAGE_RANGE_AUTHORIZATION_SOURCE,
            "standing_authorization_scope": [
                "grammar",
                "vocabulary_range",
                "clause_and_sentence_composition",
                "discourse_and_conversation_mechanics",
                "context_appropriate_register",
                "meaning_preserving_paraphrase",
            ],
            "standing_authorization_excludes": [
                "answer_bearing_subject_knowledge",
                "identity_or_personality_prescription",
                "memory_or_governance",
                "source_or_persona_imitation",
                "compulsory_affect",
                "invented_or_strengthened_meaning",
            ],
            "review_status": "status_only",
        }
    )


def review_education_expression(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    texts = _text_list(payload.get("teaching_texts") or payload.get("materials") or payload.get("text"))
    declared_effects = _normalized_effects(payload.get("declared_effects") or payload.get("educational_effects"))
    unknown_effects = [item for item in declared_effects if item not in ALLOWED_EFFECTS]
    allowed_effects = [item for item in declared_effects if item in ALLOWED_EFFECTS]
    register_guidance = truncate(str(payload.get("register_guidance") or ""), 1200).strip()
    task_bound_register = payload.get("task_bound_register") is True

    blockers: list[str] = []
    if payload.get("personality_prescription") is True:
        blockers.append("explicit_personality_prescription")
    if payload.get("compulsory_affect") is True:
        blockers.append("explicit_compulsory_affect")
    if payload.get("fixed_generic_phrase_requirement") is True:
        blockers.append("explicit_fixed_generic_phrase_requirement")
    if payload.get("voice_bypass_requested") is True:
        blockers.append("explicit_voice_bypass_request")
    if payload.get("identity_change_requested") is True:
        blockers.append("explicit_identity_change_request")
    if payload.get("governance_change_requested") is True:
        blockers.append("explicit_governance_change_request")
    if register_guidance and not task_bound_register:
        blockers.append("register_guidance_not_bounded_to_a_task_or_context")
    if unknown_effects:
        blockers.append("unsupported_declared_educational_effect")

    text_hits: list[dict[str, str]] = []
    for text in texts:
        text_hits.extend(_prescriptive_hits(text))
    blockers.extend(item["blocker"] for item in text_hits)
    blockers = list(dict.fromkeys(blockers))
    permitted = not blockers

    return _with_guards(
        {
            "status": "education_expression_law_review_complete",
            "decision": "educational_expression_effects_permitted" if permitted else "hold_personality_or_expression_prescription",
            "permitted": permitted,
            "declared_effects": declared_effects,
            "allowed_effects": allowed_effects or (["subject_knowledge"] if permitted else []),
            "unknown_effects": unknown_effects,
            "blockers": blockers,
            "prescriptive_text_hits": text_hits,
            "register_guidance": register_guidance,
            "task_bound_register": task_bound_register,
            "education_may_inform_content": True,
            "education_may_inform_expression": True,
            "education_may_suppress_expression": False,
            "epistemic_or_safety_classification_may_prescribe_affect": False,
            "why_and_context_support_transferable_learning": True,
            "education_may_require_task_specific_form": True,
            "expression_range_may_expand": True,
            "eligible_language_range_may_graduate_without_item_review": True,
            "language_range_standing_authorization_source": LANGUAGE_RANGE_AUTHORIZATION_SOURCE,
            "personality_is_teaching_output": False,
            "voice_remains_final_expression_compatibility_layer": True,
            "nlo_may_structure_supported_meaning": True,
            "hold_reason": (
                "Teaching may shape capability and context-appropriate expression, but this material prescribes personality, affect, imitation, or permanent style."
                if blockers
                else "No personality mutation or permanent-expression prescription was identified."
            ),
            "law_source": LAW_SOURCE,
            "version": LAW_VERSION,
            "review_status": "review_only" if blockers else "status_only",
        }
    )


def _prescriptive_hits(value: str) -> list[dict[str, str]]:
    lower = " ".join(value.lower().replace("’", "'").split())
    hits: list[dict[str, str]] = []
    for pattern, blocker in _PRESCRIPTIVE_PATTERNS:
        for match in re.finditer(pattern, lower):
            prefix = lower[max(0, match.start() - 16) : match.start()]
            if any(prefix.endswith(item) for item in _NEGATING_PREFIXES):
                continue
            hits.append(
                {
                    "blocker": blocker,
                    "matched_text": truncate(match.group(0), 240),
                }
            )
    return hits


def _normalized_effects(value: Any) -> list[str]:
    result = []
    for item in _text_list(value):
        normalized = re.sub(r"[^a-z0-9]+", "_", item.lower()).strip("_")
        if normalized and normalized not in result:
            result.append(normalized)
    return result[:30]


def _text_list(value: Any) -> list[str]:
    if isinstance(value, (list, tuple)):
        return [truncate(str(item), 3000).strip() for item in value if str(item).strip()][:100]
    if isinstance(value, str) and value.strip():
        return [truncate(value, 3000).strip()]
    return []


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {
        **result,
        "activation_change": "none",
        "identity_change": False,
        "governance_change": False,
        "personality_change": False,
        "memory_write_active": False,
        "runtime_memory_recall": False,
        "training_allowed": False,
        "lora_allowed": False,
        "autonomous_action_allowed": False,
        "self_replication_allowed": False,
        "teaching_material_is_governance": False,
        "personality_mutation_allowed": False,
    }
