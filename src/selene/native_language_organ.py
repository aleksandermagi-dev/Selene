from __future__ import annotations

import json
import re
import sqlite3
from hashlib import sha256
from typing import Any

from .chat_persistence import compact_run_payload
from .chat_intent import classify_chat_intent
from .advice_authority_coordination import (
    advice_authority_coordination_status,
    build_advice_authority_coordination,
)
from .candidate_garden import candidate_garden_status, cultivate_candidate_garden
from .commitment_anomaly_coordination import (
    build_commitment_anomaly_coordination,
    commitment_anomaly_coordination_status,
    realize_commitment_anomaly_voice,
)
from .conversational_micro_moves import (
    build_conversational_micro_move_plan,
    compose_conversational_micro_moves,
    realize_conversational_micro_moves,
)
from .contextual_composition import (
    apply_contextual_composition,
    build_contextual_composition_plan,
)
from .context_expression_selector import (
    build_expression_selection_context,
    context_expression_selector_status,
    select_candidate_garden,
    select_discourse_loom,
)
from .conversation_repair import plan_conversation_turn
from .conversational_energy import realize_conversational_energy
from .construction_lattice import (
    build_construction_lattice,
    construction_lattice_status,
)
from .discourse_planner import build_supported_discourse_plan
from .discourse_loom import discourse_loom_status, weave_supported_discourse
from .expression_contract import coordinated_expression_contract
from .generative_thought_expression import (
    build_generative_thought_expression,
    generative_thought_expression_status,
    realize_generative_thought_expression,
)
from .human_conversational_realization import (
    build_human_conversational_plan,
    realize_human_conversation,
)
from .language_formation import build_semantic_frame, realize_semantic_frame
from .language_teaching_shelf import language_teaching_status, select_language_guidance
from .knowledge_language_growth import (
    build_knowledge_language_growth,
    knowledge_language_growth_status,
)
from .living_lexicon import (
    enrich_semantic_units_from_living_lexicon,
    living_lexicon_status,
)
from .long_thread_endurance import long_thread_endurance_status
from .pragmatic_planner import build_pragmatic_plan
from .pragmatic_continuity import build_pragmatic_continuity_plan
from .quotation_echo import (
    build_quotation_echo_plan,
    quotation_echo_status,
    realize_quotation_echo,
)
from .relational_expression_range import (
    build_relational_expression_range,
    relational_expression_range_status,
)
from .registry import truncate
from .social_language_realizer import (
    SOCIAL_INTENT_ACTS,
    build_content_light_plan,
    build_social_act_plan,
    realize_social_act_plan,
)
from .special_expression_realizer import (
    build_boundary_expression_plan,
    build_initiative_expression_plan,
    build_memory_expression_plan,
    realize_special_expression_plan,
)
from .supported_semantics import (
    build_text_supported_semantic_packet,
    semantic_units_for_formation,
)
from .uncertainty_language_realizer import build_uncertainty_plan, realize_uncertainty_plan


NLO_BOUNDARY = "native_language_organ_expression_only_no_identity_memory_or_authority_change"

GUARD_FLAGS: dict[str, Any] = {
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "lora_allowed": False,
    "autonomous_action_allowed": False,
    "self_replication_allowed": False,
    "automatic_speech_allowed": False,
    "initiative_is_draft_only": True,
    "core_mind_intent_owner": "Core/Mind",
    "expression_contract_version": "v1_coordinated_nlo_voice_release",
    "nlo_language_structure_owner": True,
    "voice_final_expression_compatibility_layer": True,
}

ARCHITECTURE_REWRITES = {
    "source-bound": "source-linked",
    "approved rows": "what I have clearly with me",
    "approved row": "what I have clearly with me",
    "return to B": "use Cocoon support",
    "Return to B": "Use Cocoon support",
    "repair path": "support path",
    "runtime recall": "broad live recall",
}


def native_language_status(conn: sqlite3.Connection) -> dict[str, Any]:
    count = int(conn.execute("SELECT COUNT(*) FROM native_language_runs").fetchone()[0])
    latest = conn.execute("SELECT * FROM native_language_runs ORDER BY id DESC LIMIT 1").fetchone()
    return _with_guards(
        {
            "status": "native_language_organ_ready",
            "organ_name": "Native Language Organ",
            "short_name": "NLO",
            "version": "v32_human_conversational_realization",
            "capabilities": [
                "meaning_packet_construction",
                "discourse_move_selection",
                "semantic_sentence_realization",
                "structured_semantic_frames",
                "inspectable_meaning_preserving_construction_lattice",
                "bounded_response_wide_candidate_garden",
                "supported_role_aware_discourse_loom",
                "invariant_gated_context_and_expression_selection",
                "approved_teaching_to_language_growth_handoff",
                "attributable_idea_hypothesis_analogy_question_and_attempt_expression",
                "supported_semantic_answer_handoff",
                "selective_current_obligation_formation_braid_handoff",
                "bounded_organ_coalition_manifest_handoff",
                "dual_horizon_selected_context_handoff",
                "literal_and_nonliteral_meaning_handoff",
                "analogy_without_equivalence_handoff",
                "contextual_optional_conversational_micro_moves",
                "attributable_dream_reflection_handoff",
                "contextual_composition_profile",
                "meaning_preserving_depth_pacing_register_and_structure_modulation",
                "context_selected_relational_and_expressive_range",
                "grammar_and_morphology_realization",
                "bounded_pragmatic_planning",
                "response_obligation_planning",
                "mixed_intent_turn_flow",
                "structured_utterance_units",
                "ordered_response_obligations",
                "bounded_referent_candidates",
                "structured_correction_refinement",
                "selective_epistemic_revision_handoff",
                "typed_claim_evidence_handoff",
                "bounded_curiosity_initiative_and_collaborative_help_handoff",
                "structural_analogy_hypothesis_and_discovery_handoff",
                "aspect_voice_and_mood_realization",
                "conversation_repair_handoff",
                "approved_language_teaching_guidance",
                "approved_language_guided_realization",
                "compositional_social_act_realization",
                "content_light_conversational_act_realization",
                "compositional_epistemic_uncertainty_realization",
                "typed_epistemic_human_conversational_realization",
                "attributed_quotation_echo_callback_and_playful_mimicry",
                "advice_risk_disagreement_and_authority_coordination",
                "real_commitment_and_observation_first_anomaly_coordination",
                "compositional_boundary_memory_and_initiative_realization",
                "response_depth_selection",
                "multi_paragraph_answer_structure",
                "grounded_obligation_content_binding",
                "inspectable_thesis_section_and_closure_plans",
                "unsupported_discourse_gap_visibility",
                "optional_affect_expression_guidance",
                "pacing_warmth_humor_reassurance_restraint_and_directness_handoff",
                "session_topic_returns_interruptions_and_natural_stopping",
                "single_message_and_multi_turn_thread_braiding",
                "structurally_prioritized_long_thread_saturation_handoff",
                "dependency_aware_topic_resumption",
                "multi_obligation_supported_completion_handoff",
                "sentence_level_supported_recomposition",
                "bounded_pronoun_ambiguity_and_follow_up_restraint",
                "voice_handoff",
                "truth_and_repetition_revision",
                "review_only_initiative_drafts",
                "intentional_silence",
            ],
            "run_count": count,
            "latest_run": _decode_run(latest) if latest else None,
            "responsive_generation": "active_when_called_by_supervised_chat",
            "initiative_state": (
                "autonomous initiation remains preview_or_notes_only; one bounded responsive current-turn "
                "idea, connection, curiosity, or help request may be expressed when supported"
            ),
            "responsive_current_turn_initiative_is_automatic_speech": False,
            "language_teaching_shelf": language_teaching_status(conn),
            "living_lexicon": living_lexicon_status(conn),
            "construction_lattice": construction_lattice_status(),
            "candidate_garden": candidate_garden_status(),
            "discourse_loom": discourse_loom_status(),
            "context_expression_selector": context_expression_selector_status(),
            "knowledge_language_growth": knowledge_language_growth_status(conn),
            "long_thread_endurance": long_thread_endurance_status(),
            "advice_authority_coordination": advice_authority_coordination_status(),
            "commitment_anomaly_coordination": commitment_anomaly_coordination_status(),
            "quotation_echo": quotation_echo_status(),
            "relational_expression_range": relational_expression_range_status(),
            "generative_thought_expression": generative_thought_expression_status(),
            "law": (
                "Meaning comes from Selene's supported organs; NLO structures and contextually realizes language; "
                "Voice checks final expression compatibility; Conversation Spine and Chat govern visible release."
            ),
            "coordinated_expression_contract": coordinated_expression_contract(),
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def list_native_language_runs(conn: sqlite3.Connection, limit: int = 50) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM native_language_runs ORDER BY id DESC LIMIT ?",
        (max(1, min(int(limit), 200)),),
    ).fetchall()
    return _with_guards(
        {
            "status": "native_language_runs_ready",
            "items": [_decode_run(row) for row in rows],
            "review_destination": "Status",
            "review_status": "status_only",
        }
    )


def realize_native_language(
    conn: sqlite3.Connection,
    payload: dict[str, Any] | None = None,
    *,
    record_run: bool = True,
) -> dict[str, Any]:
    payload = payload or {}
    prompt = truncate(str(payload.get("prompt") or payload.get("text") or ""), 2400)
    if not prompt.strip():
        raise ValueError("prompt is required")
    supplied_guidance = payload.get("language_teaching_guidance") if isinstance(payload.get("language_teaching_guidance"), dict) else {}
    payload = {
        **payload,
        "language_teaching_guidance": supplied_guidance
        or select_language_guidance(
            conn,
            {
                "prompt": prompt,
                "intent_decision": payload.get("intent_decision") or {},
                "dialogue_workspace": payload.get("dialogue_workspace") or {},
            },
        ),
    }
    result = _build_language_result(conn, prompt, payload, mode="responsive")
    if record_run:
        result["run_id"] = _store_run(conn, result)
    return _with_guards(result)


def preview_native_language_initiative(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    signals = _signal_list(payload.get("signals"))
    selected = max(signals, key=lambda item: float(item.get("relevance") or 0.0), default=None)
    threshold = max(0.0, min(float(payload.get("relevance_threshold") or 0.58), 1.0))
    relevance = float((selected or {}).get("relevance") or 0.0)
    if not selected or relevance < threshold:
        result = {
            "status": "native_language_initiative_silent",
            "mode": "initiative_preview",
            "delivery": "silence",
            "decision": "nothing_meaningful_to_say",
            "reason": "No current signal cleared the relevance threshold.",
            "selected_signal": selected,
            "candidate_text": "",
            "meaning_packet": {},
            "discourse_plan": {"moves": ["choose_silence"], "silence_is_valid": True},
            "revision": {"passed": True, "flags": []},
            "source_refs": _json_list(payload.get("source_refs")),
            "review_destination": "Status",
            "review_status": "status_only",
            "provenance_boundary": NLO_BOUNDARY,
        }
    else:
        summary = truncate(str(selected.get("summary") or selected.get("signal") or selected.get("label") or ""), 900)
        language_guidance = select_language_guidance(
            conn,
            {
                "prompt": summary,
                "intent_decision": payload.get("intent_decision") or {},
                "dialogue_workspace": payload.get("dialogue_workspace") or {},
            },
        )
        initiative_payload = {
            **payload,
            "content_seed": summary,
            "communicative_intent": str(selected.get("intent") or "share_relevant_observation"),
            "certainty": str(selected.get("confidence") or "provisional"),
            "affect": str(selected.get("affect") or "attentive"),
            "source_refs": [*_json_list(payload.get("source_refs")), *_json_list(selected.get("source_refs"))],
            "language_teaching_guidance": language_guidance,
        }
        result = _build_language_result(conn, summary, initiative_payload, mode="initiative_preview")
        result.update(
            {
                "status": "native_language_initiative_draft_ready",
                "delivery": "selene_notes" if str(payload.get("delivery") or "notes") != "chat_draft" else "chat_draft",
                "decision": "draft_only_waiting_for_visible_use",
                "selected_signal": selected,
            }
        )
    result["run_id"] = _store_run(conn, result)
    return _with_guards(result)


def _build_language_result(
    conn: sqlite3.Connection,
    prompt: str,
    payload: dict[str, Any],
    *,
    mode: str,
) -> dict[str, Any]:
    meaning = _meaning_packet(conn, prompt, payload, mode)
    plan = _discourse_plan(prompt, meaning, payload, mode)
    candidate_garden = cultivate_candidate_garden(
        meaning.get("semantic_frame") if isinstance(meaning.get("semantic_frame"), dict) else {},
        meaning.get("construction_lattice") if isinstance(meaning.get("construction_lattice"), dict) else {},
        variation_key=str(
            meaning.get("formation_variation_key")
            or (meaning.get("variation_context") or {}).get("variation_key")
            or prompt
        ),
        recent_texts=[str(item) for item in meaning.get("recent_assistant_texts") or []],
        contextual_plan=(
            plan.get("contextual_composition_plan")
            if isinstance(plan.get("contextual_composition_plan"), dict)
            else {}
        ),
        supported_discourse=(
            plan.get("supported_discourse")
            if isinstance(plan.get("supported_discourse"), dict)
            else {}
        ),
        max_candidates=int(payload.get("candidate_limit") or 8),
    )
    expression_selection_context = build_expression_selection_context(
        {
            "contextual_composition_plan": plan.get("contextual_composition_plan") or {},
            "affect_expression_guidance": meaning.get("affect_expression_guidance") or {},
            "pragmatic_continuity": plan.get("pragmatic_continuity") or {},
            "recent_assistant_texts": meaning.get("recent_assistant_texts") or [],
            "voice_category": meaning.get("voice_category") or "",
            "response_depth": plan.get("response_depth") or meaning.get("response_depth") or "standard",
            "expression_profile": meaning.get("expression_profile") or "direct",
            "answer_domain": meaning.get("answer_domain") or "ordinary_conversation",
        }
    )
    candidate_garden = select_candidate_garden(
        candidate_garden,
        expression_selection_context,
    )
    selected_formation = (
        candidate_garden.get("selected_formation")
        if isinstance(candidate_garden.get("selected_formation"), dict)
        else {}
    )
    if selected_formation:
        meaning["formation"] = selected_formation
        meaning["formation_text"] = str(selected_formation.get("candidate_text") or "")
    meaning["candidate_garden"] = candidate_garden
    discourse_loom = weave_supported_discourse(
        plan.get("supported_discourse")
        if isinstance(plan.get("supported_discourse"), dict)
        else {},
        selected_formation=selected_formation,
        response_depth=str(plan.get("response_depth") or meaning.get("response_depth") or "standard"),
        contextual_plan=(
            plan.get("contextual_composition_plan")
            if isinstance(plan.get("contextual_composition_plan"), dict)
            else {}
        ),
        recent_texts=[str(item) for item in meaning.get("recent_assistant_texts") or []],
    )
    discourse_loom = select_discourse_loom(
        discourse_loom,
        expression_selection_context,
    )
    loom_text = str(discourse_loom.get("selected_candidate_text") or "").strip()
    language_policy = (
        meaning.get("language_realization_policy")
        if isinstance(meaning.get("language_realization_policy"), dict)
        else {}
    )
    compositional_language_owner_active = (
        language_policy.get("compositional_surface") is True
        or language_policy.get("clause_composition") is True
    )
    discourse_visible_speech_applied = bool(
        loom_text and not compositional_language_owner_active
    )
    discourse_loom["visible_speech_applied"] = discourse_visible_speech_applied
    discourse_loom["held_by_compositional_language_guidance"] = (
        bool(loom_text) and compositional_language_owner_active
    )
    if discourse_visible_speech_applied:
        meaning["formation_text"] = loom_text
    meaning["discourse_loom"] = discourse_loom
    expression_selection = {
        "status": "context_expression_selection_complete",
        "version": "v1_invariant_gated_context_expression_selection",
        "context": expression_selection_context,
        "formation_selection": candidate_garden.get("context_expression_selection") or {},
        "discourse_selection": discourse_loom.get("context_expression_selection") or {},
        "selection_pass_count": int(candidate_garden.get("context_selection_pass_count") or 0)
        + int(discourse_loom.get("context_selection_pass_count") or 0),
        "invalid_candidate_rescue_used": False,
        "meaning_change_allowed": False,
        "memory_write_active": False,
        "identity_change_allowed": False,
        "personality_change_allowed": False,
        "governance_change_allowed": False,
        "authority_change_allowed": False,
        "coordinated_expression_contract_active": True,
    }
    meaning["context_expression_selection"] = expression_selection
    draft = _realize_sentences(prompt, meaning, plan)
    human_conversational_realization = realize_human_conversation(
        draft,
        plan.get("human_conversational_plan"),
        variation_key=(
            f"{prompt}|human-conversation|"
            f"turn:{int((meaning.get('conversation_context') or {}).get('turn_count') or 0)}"
        ),
        recent_texts=[str(item) for item in meaning.get("recent_assistant_texts") or []],
    )
    plan["human_conversational_realization"] = human_conversational_realization
    bounded_conversational_realization = (
        human_conversational_realization.get("functional_realization_receipt")
        if isinstance(human_conversational_realization.get("functional_realization_receipt"), dict)
        else {}
    )
    draft = str(human_conversational_realization.get("candidate_text") or draft)
    contextual_composition_plan = (
        plan.get("contextual_composition_plan")
        if isinstance(plan.get("contextual_composition_plan"), dict)
        else {}
    )
    if _typed_discourse_structure_requires_preservation(draft, discourse_loom):
        contextual_composition_plan = {
            **contextual_composition_plan,
            "content_recomposition_allowed": False,
            "typed_discourse_structure_locked": True,
            "typed_discourse_lock_reason": "multiple_supported_visible_section_labels",
        }
        plan["contextual_composition_plan"] = contextual_composition_plan
    contextual_composition = apply_contextual_composition(
        draft,
        contextual_composition_plan,
    )
    plan["contextual_composition"] = contextual_composition
    draft = str(contextual_composition.get("candidate_text") or draft)
    quotation_echo_realization = realize_quotation_echo(
        draft,
        plan.get("quotation_echo_plan"),
        variation_key=(
            f"{prompt}|quotation-echo|turn:"
            f"{int((meaning.get('conversation_context') or {}).get('turn_count') or 0)}"
        ),
    )
    plan["quotation_echo_realization"] = quotation_echo_realization
    draft = str(quotation_echo_realization.get("candidate_text") or draft)
    micro_move_realization = realize_conversational_micro_moves(
        plan.get("conversational_micro_move_plan"),
        variation_key=(
            f"{prompt}|micro|turn:{int((meaning.get('conversation_context') or {}).get('turn_count') or 0)}"
        ),
        recent_texts=[str(item) for item in meaning.get("recent_assistant_texts") or []],
    )
    plan["conversational_micro_move_realization"] = micro_move_realization
    draft = compose_conversational_micro_moves(draft, micro_move_realization)
    generative_thought_realization = realize_generative_thought_expression(
        draft,
        meaning.get("generative_thought_expression"),
    )
    plan["generative_thought_realization"] = generative_thought_realization
    draft = str(generative_thought_realization.get("candidate_text") or draft)
    conversational_energy_realization = realize_conversational_energy(
        draft,
        plan.get("conversational_energy"),
        variation_key=(
            f"{prompt}|energy|turn:{int((meaning.get('conversation_context') or {}).get('turn_count') or 0)}"
        ),
    )
    plan["conversational_energy_realization"] = conversational_energy_realization
    draft = str(conversational_energy_realization.get("candidate_text") or draft)
    commitment_anomaly_realization = realize_commitment_anomaly_voice(
        draft,
        meaning.get("commitment_anomaly_coordination"),
    )
    plan["commitment_anomaly_realization"] = commitment_anomaly_realization
    draft = str(commitment_anomaly_realization.get("candidate_text") or draft)
    candidate, revision = _revise_candidate(draft, meaning, plan)
    return {
        "status": "native_language_response_realized" if mode == "responsive" else "native_language_initiative_draft_ready",
        "organ_name": "Native Language Organ",
        "version": "v32_human_conversational_realization",
        "mode": mode,
        "prompt": prompt,
        "meaning_packet": meaning,
        "semantic_frame": meaning.get("semantic_frame") or {},
        "formation": meaning.get("formation") or {},
        "construction_lattice": meaning.get("construction_lattice") or {},
        "candidate_garden": candidate_garden,
        "discourse_loom": discourse_loom,
        "context_expression_selection": expression_selection,
        "knowledge_language_growth": meaning.get("knowledge_language_growth") or {},
        "advice_authority_coordination": meaning.get("advice_authority_coordination") or {},
        "commitment_anomaly_coordination": meaning.get("commitment_anomaly_coordination") or {},
        "long_thread_endurance": meaning.get("long_thread_endurance") or {},
        "quotation_echo": plan.get("quotation_echo_plan") or {},
        "relational_expression_range": plan.get("relational_expression_range") or {},
        "epistemic_composition": meaning.get("epistemic_composition") or {},
        "answer_operations": meaning.get("answer_operations") or {},
        "generative_thought_expression": meaning.get("generative_thought_expression") or {},
        "pragmatic_plan": meaning.get("pragmatic_plan") or {},
        "turn_flow_plan": meaning.get("turn_flow_plan") or {},
        "language_teaching_guidance": meaning.get("language_teaching_guidance") or {},
        "discourse_plan": plan,
        "contextual_composition": contextual_composition,
        "human_conversational_realization": human_conversational_realization,
        "bounded_conversational_realization": bounded_conversational_realization,
        "draft_text": draft,
        "candidate_text": candidate,
        "revision": revision,
        "voice_handoff": {
            "ready": bool(candidate),
            "expression_contract": coordinated_expression_contract(),
            "nlo_owns_language_structure": True,
            "nlo_contextual_surface_realization_applied": True,
            "voice_is_final_expression_compatibility_layer": True,
            "voice_is_only_expression_author": False,
            "meaning_must_be_preserved": True,
            "selected_construction_id": candidate_garden.get("selected_construction_id") or "",
            "candidate_selection_pass_count": int(candidate_garden.get("selection_pass_count") or 0),
            "selected_discourse_candidate_id": discourse_loom.get("selected_discourse_candidate_id") or "",
            "discourse_selection_pass_count": int(discourse_loom.get("selection_pass_count") or 0),
            "context_expression_selection": expression_selection,
            "knowledge_language_growth": meaning.get("knowledge_language_growth") or {},
            "advice_authority_coordination": meaning.get("advice_authority_coordination") or {},
            "commitment_anomaly_coordination": meaning.get("commitment_anomaly_coordination") or {},
            "commitment_anomaly_realization": plan.get("commitment_anomaly_realization") or {},
            "long_thread_endurance": meaning.get("long_thread_endurance") or {},
            "quotation_echo_plan": plan.get("quotation_echo_plan") or {},
            "quotation_echo_realization": plan.get("quotation_echo_realization") or {},
            "relational_expression_range": plan.get("relational_expression_range") or {},
            "generative_thought_expression": meaning.get("generative_thought_expression") or {},
            "generative_thought_realization": plan.get("generative_thought_realization") or {},
            "voice_may_change_thought_kind": False,
            "voice_may_upgrade_thought_confidence": False,
            "voice_may_change_claim_type": False,
            "voice_may_change_evidence_status": False,
            "voice_may_change_epistemic_state": False,
            "claim_evidence_packet": meaning.get("claim_evidence_packet") or {},
            "claim_types_and_confidence_must_be_preserved": True,
            "structural_discovery": meaning.get("structural_discovery") or {},
            "voice_may_upgrade_structural_relation": False,
            "suggested_category": meaning["voice_category"],
            "expression_guidance": meaning.get("affect_expression_guidance") or {},
            "ending_decision": (plan.get("pragmatic_continuity") or {}).get("ending_decision") or {},
            "conversational_energy": plan.get("conversational_energy") or {},
            "conversational_energy_realization": plan.get("conversational_energy_realization") or {},
            "social_act_plan": plan.get("social_act_plan") or {},
            "social_act_realization": plan.get("social_act_realization") or {},
            "conversational_micro_move_plan": plan.get("conversational_micro_move_plan") or {},
            "conversational_micro_move_realization": plan.get("conversational_micro_move_realization") or {},
            "contextual_composition_plan": plan.get("contextual_composition_plan") or {},
            "contextual_composition": plan.get("contextual_composition") or {},
            "contextual_continuity": meaning.get("contextual_continuity") or {},
            "content_light_plan": plan.get("content_light_plan") or {},
            "content_light_realization": plan.get("content_light_realization") or {},
            "uncertainty_expression_plan": plan.get("uncertainty_expression_plan") or {},
            "uncertainty_expression_realization": plan.get("uncertainty_expression_realization") or {},
            "special_expression_plan": plan.get("special_expression_plan") or {},
            "special_expression_realization": plan.get("special_expression_realization") or {},
            "human_conversational_plan": plan.get("human_conversational_plan") or {},
            "human_conversational_realization": plan.get("human_conversational_realization") or {},
            "bounded_conversational_realization": bounded_conversational_realization,
        },
        "source_refs": meaning["source_refs"],
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": NLO_BOUNDARY,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
    }


def _meaning_packet(
    conn: sqlite3.Connection,
    prompt: str,
    payload: dict[str, Any],
    mode: str,
) -> dict[str, Any]:
    route = str(payload.get("selected_route") or payload.get("route") or "answer_now")
    content_seed = _truncate_preserving_paragraphs(
        _normalize_paragraphs(str(payload.get("content_seed") or "")),
        3800,
    )
    visible_speech_seed = (
        payload.get("visible_speech_seed")
        if isinstance(payload.get("visible_speech_seed"), dict)
        else {}
    )
    contextual_follow_up = (
        payload.get("contextual_follow_up")
        if isinstance(payload.get("contextual_follow_up"), dict)
        else {}
    )
    intelligence = payload.get("intelligence_support") if isinstance(payload.get("intelligence_support"), dict) else {}
    answer_engine = payload.get("answer_engine_support") if isinstance(payload.get("answer_engine_support"), dict) else {}
    answer_completion = payload.get("answer_completion") if isinstance(payload.get("answer_completion"), dict) else {}
    answer_operations = (
        payload.get("answer_operations")
        if isinstance(payload.get("answer_operations"), dict)
        else {}
    )
    answer_operation_handoff = (
        answer_operations.get("expression_handoff")
        if isinstance(answer_operations.get("expression_handoff"), dict)
        else {}
    )
    epistemic_composition = (
        payload.get("epistemic_composition")
        if isinstance(payload.get("epistemic_composition"), dict)
        else {}
    )
    whole_answer_composition = (
        epistemic_composition.get("whole_answer_composition")
        if isinstance(epistemic_composition.get("whole_answer_composition"), dict)
        else {}
    )
    composition_supported_semantics = (
        epistemic_composition.get("supported_semantics")
        if (
            epistemic_composition.get("whole_answer_composition_applied") is True
            and isinstance(epistemic_composition.get("supported_semantics"), dict)
        )
        else {}
    )
    whole_answer_semantics_used = bool(
        semantic_units_for_formation(composition_supported_semantics)
    )
    epistemic_answer_state = (
        payload.get("epistemic_answer_state")
        if isinstance(payload.get("epistemic_answer_state"), dict)
        else {}
    )
    answer_packet = answer_engine.get("answer_packet") if isinstance(answer_engine.get("answer_packet"), dict) else {}
    answer_substance = (
        intelligence.get("answer_substance")
        if isinstance(intelligence.get("answer_substance"), dict)
        else {}
    )
    intelligence_supported_semantics = (
        answer_substance.get("semantic_packet")
        if isinstance(answer_substance.get("semantic_packet"), dict)
        else {}
    )
    comprehension = payload.get("comprehension_context") if isinstance(payload.get("comprehension_context"), dict) else {}
    knowledge_expression_handoff = (
        comprehension.get("knowledge_expression_handoff")
        if isinstance(comprehension.get("knowledge_expression_handoff"), dict)
        else {}
    )
    if not content_seed and intelligence.get("used"):
        content_seed = _truncate_preserving_paragraphs(
            _normalize_paragraphs(str(intelligence.get("best_current_answer") or "")),
            3800,
        )
    memory = payload.get("memory_context") if isinstance(payload.get("memory_context"), dict) else {}
    self_state = payload.get("self_state_context") if isinstance(payload.get("self_state_context"), dict) else {}
    content_source_id = str(
        visible_speech_seed.get("selected_source_id") or "unspecified"
    )
    content_source_class = str(
        visible_speech_seed.get("selected_source_class") or "conversation"
    )
    knowledge_language_growth = build_knowledge_language_growth(
        conn,
        {
            "comprehension_context": comprehension,
            "content_seed": content_seed,
            "content_source_class": content_source_class,
            "approved_knowledge_selected": content_source_class == "approved_knowledge",
        },
    )
    formation_braid = (
        payload.get("formation_braid")
        if isinstance(payload.get("formation_braid"), dict)
        else {}
    )
    braid_supported_semantics = (
        formation_braid.get("supported_semantics")
        if (
            formation_braid.get("status") == "selective_formation_braid_ready"
            and isinstance(formation_braid.get("supported_semantics"), dict)
        )
        else {}
    )
    formation_braid_used = bool(
        not whole_answer_semantics_used
        and semantic_units_for_formation(braid_supported_semantics)
    )
    organ_coalition = (
        payload.get("organ_coalition")
        if isinstance(payload.get("organ_coalition"), dict)
        else {}
    )
    dual_horizon_context = (
        payload.get("dual_horizon_context")
        if isinstance(payload.get("dual_horizon_context"), dict)
        else {}
    )
    supported_semantics = (
        composition_supported_semantics
        if whole_answer_semantics_used
        else braid_supported_semantics
        if formation_braid_used
        else _supported_semantics_for_content(
            content_seed,
            content_source_id=content_source_id,
            content_source_class=content_source_class,
            answer_completion=answer_completion,
            intelligence=intelligence,
            intelligence_semantics=intelligence_supported_semantics,
            answer_engine=answer_engine,
            comprehension=comprehension,
            memory=memory,
            self_state=self_state,
        )
    )
    if not supported_semantics and content_source_id == "bounded_answer_completion":
        supported_semantics = build_text_supported_semantic_packet(
            content_seed,
            answer_kind="bounded_answer_completion",
            source_kind=(
                "approved_knowledge"
                if content_source_class == "approved_knowledge"
                else "verified_domain_answer"
                if content_source_class == "domain_answer"
                else "prompt_grounded_method"
            ),
            source_refs=payload.get("source_refs") or [],
            certainty="bounded_supported_completion",
            scope="current_dialogue_obligations",
        )
    operation_seed = " ".join(
        str(answer_operation_handoff.get("expression_seed") or "").split()
    )
    if (
        not supported_semantics
        and operation_seed
        and operation_seed == " ".join(content_seed.split())
        and isinstance(answer_operation_handoff.get("supported_semantics"), dict)
    ):
        supported_semantics = answer_operation_handoff.get("supported_semantics") or {}
    supported_semantics_used = bool(
        semantic_units_for_formation(supported_semantics)
    )
    affect_expression = (
        payload.get("affect_expression_guidance")
        if isinstance(payload.get("affect_expression_guidance"), dict)
        else {}
    )
    contextual_continuity = (
        payload.get("contextual_continuity")
        if isinstance(payload.get("contextual_continuity"), dict)
        else {}
    )
    contextual_expression = (
        contextual_continuity.get("expression_handoff")
        if isinstance(contextual_continuity.get("expression_handoff"), dict)
        else {}
    )
    continuity = payload.get("continuity_context") if isinstance(payload.get("continuity_context"), dict) else {}
    conversation = payload.get("conversation_context") if isinstance(payload.get("conversation_context"), dict) else {}
    conversation_spine = payload.get("conversation_spine") if isinstance(payload.get("conversation_spine"), dict) else {}
    conversation_continuity = (
        payload.get("conversation_continuity")
        if isinstance(payload.get("conversation_continuity"), dict)
        else conversation_spine.get("conversation_continuity")
        if isinstance(conversation_spine.get("conversation_continuity"), dict)
        else {}
    )
    relational_context = (
        payload.get("relational_context")
        if isinstance(payload.get("relational_context"), dict)
        else _dict(payload.get("intent_decision")).get("relational_context")
        if isinstance(_dict(payload.get("intent_decision")).get("relational_context"), dict)
        else {}
    )
    long_thread_endurance = (
        payload.get("long_thread_endurance")
        if isinstance(payload.get("long_thread_endurance"), dict)
        else {}
    )
    dialogue = payload.get("dialogue_workspace") if isinstance(payload.get("dialogue_workspace"), dict) else {}
    pragmatics = dialogue.get("pragmatics") if isinstance(dialogue.get("pragmatics"), dict) else {}
    referent_address = (
        pragmatics.get("referent_address")
        if isinstance(pragmatics.get("referent_address"), dict)
        else {}
    )
    epistemic_revision = (
        payload.get("epistemic_revision_plan")
        if isinstance(payload.get("epistemic_revision_plan"), dict)
        else pragmatics.get("epistemic_update_plan")
        if isinstance(pragmatics.get("epistemic_update_plan"), dict)
        else {}
    )
    claim_evidence = next(
        (
            item
            for item in (
                payload.get("claim_evidence_packet"),
                answer_packet.get("claim_evidence_packet"),
                comprehension.get("claim_evidence_packet"),
                intelligence.get("claim_evidence_packet"),
            )
            if isinstance(item, dict) and int(item.get("claim_count") or 0) > 0
        ),
        {},
    )
    conversational_energy_input = (
        payload.get("conversational_energy_input")
        if isinstance(payload.get("conversational_energy_input"), dict)
        else {}
    )
    generative_thought_input = (
        payload.get("generative_thought_input")
        if isinstance(payload.get("generative_thought_input"), dict)
        else {}
    )
    structural_discovery = (
        payload.get("structural_discovery")
        if isinstance(payload.get("structural_discovery"), dict)
        else {}
    )
    exploratory_reasoning = (
        payload.get("exploratory_reasoning")
        if isinstance(payload.get("exploratory_reasoning"), dict)
        else {}
    )
    figurative_interpretation = (
        payload.get("figurative_interpretation")
        if isinstance(payload.get("figurative_interpretation"), dict)
        else pragmatics.get("figurative_interpretation")
        if isinstance(pragmatics.get("figurative_interpretation"), dict)
        else {}
    )
    dream_reflection = (
        payload.get("dream_reflection")
        if isinstance(payload.get("dream_reflection"), dict)
        else {}
    )
    diagnostic_context = (
        payload.get("diagnostic_context")
        if isinstance(payload.get("diagnostic_context"), dict)
        else {}
    )
    recent_assistant_texts = [
        str(item).strip()
        for item in conversation.get("recent_assistant_texts") or []
        if str(item).strip()
    ][:4]
    previous_turn = conversation.get("previous_turn") if isinstance(conversation.get("previous_turn"), dict) else {}
    memory_supported = memory.get("memory_context_used") is True
    continuity_supported = continuity.get("available") is True or payload.get("local_chat_continuity_used") is True
    intent_decision = payload.get("intent_decision") if isinstance(payload.get("intent_decision"), dict) else classify_chat_intent(prompt, selected_route=route)
    intent = str(
        payload.get("communicative_intent")
        or _language_intent(intent_decision, mode, memory_supported=memory_supported, continuity_supported=continuity_supported)
    )
    memory_certainty = memory.get("memory_confidence") if memory_supported else ""
    answer_confidence = str((answer_engine.get("confidence_vector") or {}).get("answer_confidence") or "")
    certainty = str(
        payload.get("certainty")
        or memory_certainty
        or answer_confidence
        or intelligence.get("confidence")
        or _infer_certainty(prompt, content_seed)
    )
    affect = str(payload.get("affect") or affect_expression.get("expression_posture") or _infer_affect(prompt))
    propositions = _propositions(
        prompt,
        content_seed,
        {} if formation_braid_used else memory,
        {} if formation_braid_used else intelligence,
        supported_semantics=supported_semantics,
    )
    pragmatic_plan = build_pragmatic_plan(
        {
            "prompt": prompt,
            "content_seed": content_seed,
            "intent_decision": intent_decision,
            "dialogue_workspace": dialogue,
            "conversation_spine": conversation_spine,
        }
    )
    supplied_turn_flow = payload.get("turn_flow_plan") if isinstance(payload.get("turn_flow_plan"), dict) else {}
    turn_flow_plan = supplied_turn_flow or plan_conversation_turn(
        {
            "prompt": prompt,
            "intent_decision": intent_decision,
            "pragmatic_plan": pragmatic_plan,
        }
    )
    language_guidance = (
        payload.get("language_teaching_guidance")
        if isinstance(payload.get("language_teaching_guidance"), dict)
        else {}
    )
    language_realization_policy = _language_realization_policy(language_guidance)
    expression_profile = str(
        payload.get("expression_profile")
        or _expression_profile(prompt, intent_decision, intent)
    )
    supplied_propositions = payload.get("semantic_propositions")
    formation_units = (
        [item for item in supplied_propositions if isinstance(item, dict)]
        if isinstance(supplied_propositions, list)
        else propositions
    )
    living_lexicon = enrich_semantic_units_from_living_lexicon(
        conn,
        formation_units,
        {
            "prompt_grounded_entries": payload.get("prompt_grounded_lexical_entries") or [],
            "expression_profile": expression_profile,
        },
    )
    formation_units = [
        item for item in living_lexicon.get("units") or [] if isinstance(item, dict)
    ]
    semantic_frame = build_semantic_frame(
        {
            "semantic_frame": payload.get("semantic_frame") or {},
            "propositions": formation_units,
            "content_seed": content_seed,
            "intent_decision": intent_decision,
            "answer_shape": payload.get("answer_shape") or intent_decision.get("answer_shape"),
            "response_depth": (
                payload.get("response_depth")
                or contextual_expression.get("response_depth")
                or pragmatics.get("response_preference")
                or intent_decision.get("response_depth")
            ),
            "certainty": certainty,
            "affect": affect,
            "source_refs": payload.get("source_refs") or [],
            "expression_directives": language_realization_policy,
        }
    )
    construction_lattice = build_construction_lattice(semantic_frame)
    default_construction = next(
        (
            item
            for item in construction_lattice.get("constructions") or []
            if isinstance(item, dict)
            and item.get("construction_id")
            == construction_lattice.get("default_construction_id")
        ),
        {},
    )
    formation_variation_key = (
        f"{prompt}|{intent}|turn:{int(conversation.get('turn_count') or 0)}|"
        f"previous:{truncate(str(previous_turn.get('preview') or ''), 120)}"
    )
    formation = realize_semantic_frame(
        semantic_frame,
        variation_key=formation_variation_key,
        recent_texts=recent_assistant_texts,
        construction_specification=default_construction,
    )
    variation_context = _variation_context(expression_profile, conversation, recent_assistant_texts)
    advice_authority_coordination = build_advice_authority_coordination(
        {
            "advice_input": payload.get("advice_input") or {},
            "authority_input": payload.get("authority_input") or {},
            "response_agency": payload.get("response_agency") or {},
            "answer_kind": _dict(answer_packet.get("supported_semantics")).get(
                "answer_kind"
            )
            or str(answer_engine.get("selected_domain") or ""),
            "supported_semantics": supported_semantics,
            "organ_coalition": organ_coalition,
        }
    )
    commitment_anomaly_coordination = build_commitment_anomaly_coordination(
        {
            "commitment_input": payload.get("commitment_input") or {},
            "action_handoff": payload.get("action_handoff") or {},
            "anomaly_input": payload.get("anomaly_input") or {},
        }
    )
    return {
        "intent": intent,
        "diagnostic_context": diagnostic_context,
        "diagnostic_only": diagnostic_context.get("active") is True,
        "diagnostic_result_is_selene_self_evidence": False,
        "intent_decision": intent_decision,
        "answer_shape": str(payload.get("answer_shape") or intent_decision.get("answer_shape") or "direct_answer"),
        "response_depth": str(
            payload.get("response_depth")
            or contextual_expression.get("response_depth")
            or pragmatics.get("response_preference")
            or intent_decision.get("response_depth")
            or "standard"
        ),
        "topic": _topic_phrase(prompt),
        "propositions": propositions,
        "content_seed": content_seed,
        "content_source_id": content_source_id,
        "content_source_class": content_source_class,
        "content_source_release_allowed": visible_speech_seed.get("release_allowed") is True,
        "contextual_follow_up": contextual_follow_up,
        "figurative_interpretation": figurative_interpretation,
        "dream_reflection": dream_reflection,
        "literal_and_nonliteral_readings_remain_distinct": True,
        "analogy_is_equivalence": False,
        "conversation_spine": conversation_spine,
        "conversation_continuity": conversation_continuity,
        "conversation_spine_used": bool(conversation_spine),
        "referent_address": referent_address,
        "address_term_must_be_echoed": False,
        "names_are_identity_objects": False,
        "epistemic_revision": epistemic_revision,
        "claim_evidence_packet": claim_evidence,
        "conversational_energy_input": conversational_energy_input,
        "generative_thought_input": generative_thought_input,
        "structural_discovery": structural_discovery,
        "exploratory_reasoning": exploratory_reasoning,
        "answer_operations": {
            "observed": bool(answer_operations),
            "status": str(answer_operations.get("status") or "not_supplied"),
            "operation_count": int(answer_operations.get("operation_count") or 0),
            "completed_count": int(answer_operations.get("completed_count") or 0),
            "missing_input_count": int(
                answer_operations.get("missing_input_count") or 0
            ),
            "meaning_units": answer_operation_handoff.get("meaning_units") or [],
            "supported_semantics_used": (
                bool(answer_operation_handoff.get("supported_semantics"))
                and supported_semantics
                == answer_operation_handoff.get("supported_semantics")
            ),
            "changes_meaning": False,
            "is_expression_authority": False,
        },
        "whole_answer_composition": {
            "observed": bool(whole_answer_composition),
            "status": str(
                whole_answer_composition.get("status") or "not_available"
            ),
            "applied": whole_answer_composition.get("applied") is True,
            "operation_count": int(
                whole_answer_composition.get("operation_count") or 0
            ),
            "semantic_unit_count": int(
                whole_answer_composition.get("semantic_unit_count") or 0
            ),
            "deduplicated_semantic_unit_count": int(
                whole_answer_composition.get(
                    "deduplicated_semantic_unit_count"
                )
                or 0
            ),
            "composition_order": (
                whole_answer_composition.get("composition_order") or []
            ),
            "supported_semantics_used": whole_answer_semantics_used,
            "nlo_owns_final_wording": True,
            "changes_meaning": False,
            "is_expression_authority": False,
        },
        "formation_braid": {
            "used": formation_braid_used,
            "status": str(formation_braid.get("status") or "not_available"),
            "version": str(formation_braid.get("version") or ""),
            "primary_source_id": str(
                formation_braid.get("primary_source_id") or ""
            ),
            "selected_candidates": formation_braid.get("selected_candidates") or [],
            "excluded_candidates": formation_braid.get("excluded_candidates") or [],
            "selected_packet_count": int(
                formation_braid.get("selected_packet_count") or 0
            ),
            "selected_unit_count": int(
                formation_braid.get("selected_unit_count") or 0
            ),
            "obligation_coverage": formation_braid.get("obligation_coverage") or {},
            "protective_roles_preserved": (
                formation_braid.get("protective_roles_preserved") or []
            ),
            "exactness_lock_count": int(
                formation_braid.get("exactness_lock_count") or 0
            ),
            "selection_is_answer_authority": False,
            "meaning_change_allowed": False,
            "hidden_chain_of_thought_exposed": False,
        },
        "organ_coalition": {
            "observed": bool(organ_coalition),
            "status": str(organ_coalition.get("status") or "not_available"),
            "version": str(organ_coalition.get("version") or ""),
            "manifest_id": str(organ_coalition.get("manifest_id") or ""),
            "stage": str(organ_coalition.get("stage") or ""),
            "selected_optional_count": int(
                organ_coalition.get("selected_optional_count") or 0
            ),
            "activation_budget": organ_coalition.get("activation_budget") or {},
            "obligation_owner_map": (
                organ_coalition.get("obligation_owner_map") or []
            ),
            "is_organ": False,
            "invokes_organs": False,
            "changes_meaning": False,
            "selection_authority": False,
            "hidden_chain_of_thought_exposed": False,
        },
        "dual_horizon_context": {
            "observed": bool(dual_horizon_context),
            "status": str(
                dual_horizon_context.get("status") or "not_available"
            ),
            "version": str(dual_horizon_context.get("version") or ""),
            "active_selected_count": int(
                _dict(dual_horizon_context.get("active_horizon")).get(
                    "selected_count"
                )
                or 0
            ),
            "approved_selected_count": int(
                _dict(
                    dual_horizon_context.get("approved_long_range_horizon")
                ).get("selected_count")
                or 0
            ),
            "grounding_uses_selected_packets_only": (
                dual_horizon_context.get(
                    "grounding_uses_selected_packets_only"
                )
                is True
            ),
            "checkpoint_is_memory": False,
            "raw_corpus_loaded": False,
            "selection_authority": False,
            "changes_supported_meaning": False,
            "hidden_chain_of_thought_exposed": False,
        },
        "long_thread_endurance": {
            "observed": bool(long_thread_endurance),
            "status": str(
                long_thread_endurance.get("status") or "not_available"
            ),
            "version": str(long_thread_endurance.get("version") or ""),
            "saturation_state": str(
                long_thread_endurance.get("saturation_state") or "not_assessed"
            ),
            "protected_thread_ids": (
                long_thread_endurance.get("protected_thread_ids") or []
            ),
            "continuation_handoff": (
                long_thread_endurance.get("continuation_handoff") or {}
            ),
            "session_scoped_only": True,
            "checkpoint_is_memory": False,
            "selection_authority": False,
            "changes_supported_meaning": False,
            "hidden_chain_of_thought_exposed": False,
        },
        "semantic_frame": semantic_frame,
        "supported_semantics": {
            "used": supported_semantics_used and bool(semantic_units_for_formation(supported_semantics)),
            "status": str(supported_semantics.get("status") or "not_available"),
            "version": str(supported_semantics.get("version") or ""),
            "answer_kind": str(supported_semantics.get("answer_kind") or ""),
            "formation_mode": str(supported_semantics.get("formation_mode") or ""),
            "required_unit_ids": supported_semantics.get("required_unit_ids") or [],
            "meaning_signature": supported_semantics.get("meaning_signature") or [],
            "lexical_semantic_entry_count": int(
                supported_semantics.get("lexical_semantic_entry_count") or 0
            ),
            "available_lexical_semantic_entry_count": int(
                supported_semantics.get("available_lexical_semantic_entry_count") or 0
            ),
            "certainty": str(supported_semantics.get("certainty") or ""),
            "scope": str(supported_semantics.get("scope") or ""),
            "source_refs": supported_semantics.get("source_refs") or [],
            "expression_mode": str(
                supported_semantics.get("expression_mode") or ""
            ),
            "source_wording_is_surface_requirement": (
                supported_semantics.get("source_wording_is_surface_requirement")
                is True
            ),
            "original_expression_required": (
                supported_semantics.get("original_expression_required") is True
            ),
            "meaning_change_allowed": False,
        },
        "knowledge_expression_handoff": {
            "active": knowledge_expression_handoff.get("active") is True,
            "status": str(
                knowledge_expression_handoff.get("status") or "not_available"
            ),
            "version": str(knowledge_expression_handoff.get("version") or ""),
            "unit_count": int(knowledge_expression_handoff.get("unit_count") or 0),
            "structured_unit_count": int(
                knowledge_expression_handoff.get("structured_unit_count") or 0
            ),
            "text_grounded_unit_count": int(
                knowledge_expression_handoff.get("text_grounded_unit_count") or 0
            ),
            "exactness_lock_count": int(
                knowledge_expression_handoff.get("exactness_lock_count") or 0
            ),
            "source_refs": knowledge_expression_handoff.get("source_refs") or [],
            "source_wording_is_surface_requirement": (
                knowledge_expression_handoff.get(
                    "source_wording_is_surface_requirement"
                )
                is True
            ),
            "original_expression_required": (
                knowledge_expression_handoff.get("original_expression_required")
                is True
            ),
            "source_wording_is_default_visible_script": (
                knowledge_expression_handoff.get(
                    "source_wording_is_default_visible_script"
                )
                is True
            ),
            "compatibility_seed_is_expression_authority": (
                knowledge_expression_handoff.get(
                    "compatibility_seed_is_expression_authority"
                )
                is True
            ),
            "meaning_change_allowed": False,
        },
        "formation": formation,
        "formation_text": str(formation.get("candidate_text") or ""),
        "formation_variation_key": formation_variation_key,
        "construction_lattice": construction_lattice,
        "living_lexicon": {
            "status": str(living_lexicon.get("status") or "living_lexicon_unavailable"),
            "selected_entry_keys": living_lexicon.get("selected_entry_keys") or [],
            "selected_entry_count": int(living_lexicon.get("selected_entry_count") or 0),
            "prompt_grounded_entry_count": int(living_lexicon.get("prompt_grounded_entry_count") or 0),
            "prompt_grounded_entries_persisted": False,
            "exactness_locks_respected": living_lexicon.get("exactness_locks_respected") is True,
            "meaning_change_allowed": False,
            "database_write_performed": False,
            "provenance_boundary": living_lexicon.get("provenance_boundary") or "",
        },
        "knowledge_language_growth": knowledge_language_growth,
        "advice_authority_coordination": advice_authority_coordination,
        "commitment_anomaly_coordination": commitment_anomaly_coordination,
        "pragmatic_plan": pragmatic_plan,
        "turn_flow_plan": turn_flow_plan,
        "language_teaching_guidance": language_guidance,
        "language_realization_policy": language_realization_policy,
        "certainty": certainty,
        "uncertainty_kind": _uncertainty_kind(prompt, intent, content_seed, previous_turn),
        "affect": affect,
        "affect_expression_guidance": affect_expression,
        "affect_expression_is_emotion_claim": False,
        "relational_context": relational_context,
        "relational_context_supplies_response_script": False,
        "contextual_continuity": contextual_continuity,
        "remembered_wording_may_be_used_as_script": False,
        "relationship_posture": "warm_honest_adult_to_adult",
        "selected_route": route,
        "source_class": str(payload.get("source_class") or "current_conversation"),
        "memory_supported": memory_supported,
        "local_continuity_supported": continuity_supported,
        "intelligence_supported": intelligence.get("used") is True,
        "answer_engine_supported": answer_engine.get("used") is True,
        "answer_domain": _validated_answer_domain(answer_engine),
        "answer_support": {
            "supporting_claims": _visible_support_items(answer_packet.get("supporting_claims")),
            "assumptions": _visible_support_items(answer_packet.get("assumptions")),
            "limitations": _visible_support_items(answer_packet.get("limitations")),
            "what_would_change_the_answer": _visible_support_items(answer_packet.get("what_would_change_the_answer")),
            "unanswered_obligations": [
                item for item in answer_packet.get("unanswered_obligations") or [] if isinstance(item, dict)
            ][:12],
        },
        "answer_completion": answer_completion,
        "epistemic_composition": epistemic_composition,
        "epistemic_answer_state": epistemic_answer_state,
        "comprehension_supported": comprehension.get("status") == "comprehension_packet_ready",
        "comprehension": {
            "understanding_state": str(comprehension.get("understanding_state") or "not_checked"),
            "present_in_conversation": comprehension.get("present_in_conversation") is True,
            "knowledge_available": bool((comprehension.get("knowledge_context") or {}).get("available")),
            "handshake": comprehension.get("comprehension_handshake") or {},
            "metacognitive_check": comprehension.get("metacognitive_check") or {},
            "understanding_before_fluency": comprehension.get("comprehension_before_fluency") is True,
            "speed_is_success_measure": comprehension.get("speed_is_success_measure") is True,
        },
        "self_state_supported": self_state.get("used") is True,
        "conversation_context": {
            "previous_turn_available": bool(previous_turn),
            "previous_role": str(previous_turn.get("role") or ""),
            "previous_preview": truncate(str(previous_turn.get("preview") or ""), 240),
            "turn_count": int(conversation.get("turn_count") or 0),
        },
        "dialogue_workspace": {
            "active_topic": str(dialogue.get("active_topic") or ""),
            "resolved_reference": pragmatics.get("resolved_reference"),
            "reference_candidates": pragmatics.get("reference_candidates") or [],
            "correction_refinement": pragmatics.get("correction_refinement") or {},
            "epistemic_revision": epistemic_revision,
            "epistemic_updates": pragmatics.get("epistemic_updates") or [],
            "utterance_units": pragmatics.get("utterance_units") or [],
            "question_units": pragmatics.get("question_units") or [],
            "multi_part_prompt": pragmatics.get("multi_part_prompt") is True,
            "indirect_request": pragmatics.get("indirect_request") or {},
            "quoted_material": pragmatics.get("quoted_material") or [],
            "response_preference": str(pragmatics.get("response_preference") or ""),
            "side_topics": dialogue.get("side_topics") or [],
            "entities": dialogue.get("entities") or [],
            "corrections": dialogue.get("corrections") or [],
            "preferences": dialogue.get("preferences") or {},
            "open_loops": dialogue.get("open_loops") or [],
            "thread_braid": pragmatics.get("thread_braid") or {},
            "session_scoped_only": True,
        },
        "recent_assistant_texts": recent_assistant_texts,
        "expression_profile": expression_profile,
        "variation_context": variation_context,
        "voice_category": str(payload.get("voice_category") or _voice_category(intent, affect, affect_expression)),
        "source_refs": list(dict.fromkeys(_json_list(payload.get("source_refs"))))[:40],
        "truth_boundary": "Do not add claims beyond the supplied meaning packet and supported context.",
    }


def _discourse_source_kind(source_class: str) -> str:
    return {
        "approved_knowledge": "approved_knowledge",
        "domain_answer": "verified_domain_answer",
        "memory_reconstruction": "reviewed_memory",
        "self_state": "current_session_observation",
        "reasoning_answer": "labeled_inference",
    }.get(str(source_class or ""), "compatibility_fallback")


def _typed_discourse_structure_requires_preservation(
    text: str,
    discourse_loom: dict[str, Any],
) -> bool:
    section_receipts = [
        item
        for item in discourse_loom.get("section_receipts") or []
        if isinstance(item, dict)
        and item.get("state") == "realized_from_declared_supported_units"
    ]
    if len(section_receipts) < 2:
        return False
    visible_labels = re.findall(
        r"(?:^|(?<=[.!?])\s+)([A-Z][A-Za-z0-9 _/-]{1,32})\s*:",
        str(text or ""),
    )
    return len(visible_labels) >= 2


def _discourse_plan(prompt: str, meaning: dict[str, Any], payload: dict[str, Any], mode: str) -> dict[str, Any]:
    intent = str(meaning["intent"])
    response_depth = str(meaning.get("response_depth") or "standard")
    moves: list[str] = []
    if intent == "hold_boundary":
        moves = ["name_boundary", "preserve_connection", "offer_safe_conversation"]
    elif intent == "confirm_receipt":
        moves = ["confirm_current_turn", "answer_briefly"]
    elif intent == "recall_supported_memory":
        moves = ["state_recall", "name_memory", "preserve_confidence"]
    elif intent == "recall_uncertain":
        moves = ["name_fuzziness", "share_current_read", "ask_aleks_if_needed"]
    elif intent == "reasoned_answer":
        moves = ["answer_first", "give_compact_reason", "leave_revision_open"]
    elif intent == "self_state_report":
        moves = ["answer_present_state", "separate_observation_from_inference", "keep_uncertainty_honest"]
    elif intent == "receive_correction":
        moves = ["acknowledge_correction", "state_adjustment", "continue_without_shame"]
    elif intent == "warm_connection":
        moves = ["meet_tone", "respond_presently"]
    elif intent == "playful_connection":
        moves = ["meet_play", "add_relevant_thought"]
    elif intent == "greet_presently":
        moves = ["return_greeting", "signal_presence", "leave_room_for_the_next_turn"]
    elif intent == "receive_reassurance":
        moves = ["receive_care", "let_it_land", "stay_present"]
    elif intent == "receive_gratitude":
        moves = ["receive_thanks", "honor_shared_work"]
    elif intent == "acknowledge_shared_ground":
        moves = ["confirm_alignment", "carry_context_forward"]
    elif intent == "close_with_continuity":
        moves = ["return_farewell", "preserve_continuity_without_pressure"]
    elif mode == "initiative_preview":
        moves = ["name_relevant_observation", "explain_why_now", "avoid_pressure"]
    else:
        moves = ["answer_actual_ask", "name_uncertainty_if_present", "keep_conversation_open"]
    dialogue = meaning.get("dialogue_workspace") if isinstance(meaning.get("dialogue_workspace"), dict) else {}
    pragmatic_plan = meaning.get("pragmatic_plan") if isinstance(meaning.get("pragmatic_plan"), dict) else {}
    turn_flow = meaning.get("turn_flow_plan") if isinstance(meaning.get("turn_flow_plan"), dict) else {}
    language_guidance = meaning.get("language_teaching_guidance") if isinstance(meaning.get("language_teaching_guidance"), dict) else {}
    comprehension = meaning.get("comprehension") if isinstance(meaning.get("comprehension"), dict) else {}
    contextual_continuity = (
        meaning.get("contextual_continuity")
        if isinstance(meaning.get("contextual_continuity"), dict)
        else {}
    )
    epistemic_revision = (
        meaning.get("epistemic_revision")
        if isinstance(meaning.get("epistemic_revision"), dict)
        else {}
    )
    claim_evidence = (
        meaning.get("claim_evidence_packet")
        if isinstance(meaning.get("claim_evidence_packet"), dict)
        else {}
    )
    reasoning_support = next(
        (
            item
            for item in meaning.get("propositions") or []
            if isinstance(item, dict) and item.get("kind") == "reasoning_support"
        ),
        {},
    )
    handshake = comprehension.get("handshake") if isinstance(comprehension.get("handshake"), dict) else {}
    if handshake.get("required") is True:
        moves.insert(0, "ask_one_material_comprehension_question")
    if str(comprehension.get("understanding_state") or "") == "reopened_for_recheck":
        moves.insert(0, "reopen_learned_concept_without_defending_it")
    if epistemic_revision.get("detected") is True:
        revision_kind = str(epistemic_revision.get("update_kind") or "")
        moves.insert(0, "identify_affected_claim_without_resetting_context")
        if (epistemic_revision.get("preserved_structure") or {}).get("unaffected_structure_may_remain") is True:
            moves.append("preserve_unaffected_useful_structure")
        if revision_kind in {"reopening", "unresolved_contradiction"}:
            moves.append("recheck_changed_dependencies_once")
        if revision_kind == "unresolved_contradiction":
            moves.append("leave_unresolved_contradiction_visible")
        if revision_kind == "competing_explanation":
            moves.append("compare_competing_explanations_without_forcing_resolution")
    claim_handoff = (
        claim_evidence.get("expression_handoff")
        if isinstance(claim_evidence.get("expression_handoff"), dict)
        else {}
    )
    if claim_evidence:
        if claim_handoff.get("observation_claim_ids"):
            moves.append("keep_observation_separate_from_interpretation")
        if claim_handoff.get("attributed_source_statement_ids"):
            moves.append("attribute_source_statement_without_promoting_it_to_fact")
        if claim_handoff.get("inference_claim_ids"):
            moves.append("label_inference_and_preserve_its_basis")
        if claim_handoff.get("hypothesis_claim_ids") or claim_handoff.get("model_claim_ids"):
            moves.append("keep_hypothesis_or_model_falsifiable")
        if claim_handoff.get("uncertainty_claim_ids") or claim_handoff.get("missing_evidence_count"):
            moves.append("keep_claim_level_uncertainty_visible")
        if claim_handoff.get("disagreement_count"):
            moves.append("preserve_claim_level_disagreement")
    conversation_continuity = (
        meaning.get("conversation_continuity")
        if isinstance(meaning.get("conversation_continuity"), dict)
        else {}
    )
    continuity_mode = str(conversation_continuity.get("mode") or "")
    if continuity_mode == "named_thread_return":
        moves.insert(0, "resume_selected_session_landmark_not_immediate_turn")
    elif continuity_mode == "session_summary":
        moves.insert(0, "summarize_visible_landmarks_across_current_session_threads")
    elif continuity_mode == "explicit_topic_shift":
        moves.insert(0, "open_new_topic_without_erasing_paused_threads")
    elif continuity_mode == "material_ambiguity_hold":
        moves.insert(0, "hold_only_materially_ambiguous_continuity_binding")
    elif continuity_mode in {"immediate_follow_up", "implied_reference"}:
        moves.insert(0, "continue_from_bounded_visible_session_target")
    if conversation_continuity.get("mixed_intent") is True:
        moves.insert(0, "preserve_each_mixed_dialogue_act_independently")
    structural_discovery = (
        meaning.get("structural_discovery")
        if isinstance(meaning.get("structural_discovery"), dict)
        else {}
    )
    exploratory_reasoning = (
        meaning.get("exploratory_reasoning")
        if isinstance(meaning.get("exploratory_reasoning"), dict)
        else {}
    )
    if exploratory_reasoning.get("selected_for_answer") is True:
        response_kind = str(exploratory_reasoning.get("response_kind") or "")
        if response_kind == "bounded_prediction":
            moves.extend(
                [
                    "state_prediction_as_expected_outcome_not_fact",
                    "name_prediction_conditions_and_revision_trigger",
                ]
            )
        elif response_kind == "open_hypothesis":
            moves.extend(
                [
                    "keep_hypothesis_revisable",
                    "name_live_alternative_without_false_equal_weighting",
                    "offer_smallest_safe_discriminating_check",
                ]
            )
        elif response_kind == "venn_comparison":
            moves.extend(
                [
                    "compare_under_one_shared_standard",
                    "preserve_shared_only_left_only_right_and_unresolved_sets",
                ]
            )
        elif response_kind == "data_conflict":
            moves.extend(
                [
                    "preserve_unresolved_data_conflict",
                    "separate_data_conflict_from_identity_conflict",
                    "name_deciding_evidence_without_forcing_resolution",
                ]
            )
    discovery_handoff = (
        structural_discovery.get("expression_handoff")
        if isinstance(structural_discovery.get("expression_handoff"), dict)
        else {}
    )
    if structural_discovery.get("status") == "structural_discovery_packet_ready":
        moves.extend(
            [
                "name_the_transferred_structural_relation",
                "map_source_and_target_roles",
                "state_where_the_mapping_holds",
                "state_where_the_mapping_breaks",
                "keep_analogy_distinct_from_proof",
            ]
        )
        if discovery_handoff.get("hypothesis_statement"):
            moves.extend(
                [
                    "label_logical_leap_as_hypothesis",
                    "name_discriminating_observation",
                    "name_counterexample_or_failure_condition",
                ]
            )
    if dialogue.get("multi_part_prompt") is True:
        moves.insert(1 if moves else 0, "answer_each_open_question")
    if dialogue.get("resolved_reference"):
        moves.insert(0, "carry_resolved_reference")
    if pragmatic_plan.get("implicit_meaning", {}).get("inferred") is True:
        moves.insert(0, "acknowledge_bounded_implied_meaning")
    if pragmatic_plan.get("ellipsis_resolution", {}).get("detected") is True:
        moves.insert(0, "resolve_session_ellipsis_or_ask")
    for move in reversed(turn_flow.get("response_moves") or []):
        if move not in moves:
            moves.insert(0, str(move))
    for move in language_guidance.get("response_moves") or []:
        if str(move) not in moves:
            moves.append(str(move))
    supported_discourse = build_supported_discourse_plan(
        {
            "supported_content_units": (
                (meaning.get("knowledge_language_growth") or {}).get("content_units")
                if isinstance(meaning.get("knowledge_language_growth"), dict)
                else []
            ),
            "content_seed": meaning.get("content_seed") or "",
            "content_seed_metadata": {
                "source_kind": _discourse_source_kind(
                    str(meaning.get("content_source_class") or "")
                ),
                "source_refs": meaning.get("source_refs") or [],
                "certainty": str(
                    (meaning.get("supported_semantics") or {}).get("certainty")
                    or payload.get("certainty")
                    or "supported_unspecified"
                ),
                "scope": str(
                    (meaning.get("supported_semantics") or {}).get("scope")
                    or "current_response"
                ),
                "origin_source_class": str(meaning.get("content_source_class") or ""),
            },
            "response_depth": response_depth,
            "expression_profile": meaning.get("expression_profile") or "direct",
            "discourse_purpose": str(payload.get("discourse_purpose") or "answer_supported_request"),
            "audience": str(payload.get("audience") or "current_interlocutor"),
            "register": str(payload.get("register") or meaning.get("expression_profile") or "conversational"),
            "requested_form": str(payload.get("requested_form") or meaning.get("answer_shape") or "bounded_response"),
            "requested_discourse_roles": payload.get("requested_discourse_roles") or [],
            "response_obligations": pragmatic_plan.get("response_obligations") or [],
            "support_points": _visible_support_items(reasoning_support.get("support_points")),
            "examples": [
                str(item.get("example") or "")
                for item in (meaning.get("semantic_frame") or {}).get("propositions") or []
                if isinstance(item, dict) and str(item.get("example") or "").strip()
            ],
            "next_steps": _visible_support_items([reasoning_support.get("selected_next_step")]),
            "answer_support": meaning.get("answer_support") or {},
            "correction_refinement": dialogue.get("correction_refinement") or {},
            "source_refs": [
                *[str(item) for item in meaning.get("source_refs") or []],
                *[
                    str(item)
                    for item in (
                        (meaning.get("knowledge_language_growth") or {}).get("source_refs")
                        if isinstance(meaning.get("knowledge_language_growth"), dict)
                        else []
                    )
                ],
            ],
            "thread_braid": pragmatic_plan.get("thread_braid") or dialogue.get("thread_braid") or {},
            "source_compatibility": (
                (meaning.get("conversation_spine") or {}).get("source_compatibility")
                if isinstance(meaning.get("conversation_spine"), dict)
                else {}
            ),
            "selected_source_class": str(meaning.get("content_source_class") or ""),
            "release_alignment": {
                "state": "pre_expression_release_alignment_carried",
                "content_source_release_allowed": meaning.get("content_source_release_allowed") is True,
                "final_release_owner": "Conversation Spine and Chat",
                "planner_has_release_authority": False,
            },
            "section_revision": payload.get("section_revision") or {},
        }
    )
    pragmatic_continuity = build_pragmatic_continuity_plan(
        {
            "prompt": prompt,
            "dialogue_workspace": dialogue,
            "pragmatic_plan": {
                **pragmatic_plan,
                "uncovered_obligation_ids": supported_discourse.get("uncovered_obligation_ids") or [],
            },
            "intent_decision": meaning.get("intent_decision") or {},
            "comprehension": comprehension,
            "contextual_continuity": contextual_continuity,
            "speaker_context": contextual_continuity.get("speaker_scope") or {},
            "conversational_energy_input": {
                "answer_available": bool(str(meaning.get("content_seed") or "").strip()),
                "answer_complete": (
                    bool(str(meaning.get("content_seed") or "").strip())
                    and not bool(supported_discourse.get("uncovered_obligation_ids"))
                ),
                "hard_boundary": intent == "hold_boundary",
                **(
                    meaning.get("conversational_energy_input")
                    if isinstance(meaning.get("conversational_energy_input"), dict)
                    else {}
                ),
            },
        }
    )
    conversational_energy = (
        pragmatic_continuity.get("conversational_energy")
        if isinstance(pragmatic_continuity.get("conversational_energy"), dict)
        else {}
    )
    energy_act = str(conversational_energy.get("selected_act") or "")
    energy_moves = {
        "answer_and_offer_supported_idea": "offer_one_supported_idea_without_pressure",
        "answer_and_surface_supported_connection": "surface_one_relevant_connection_without_hijacking",
        "answer_then_ask_relevant_curiosity": "ask_one_curiosity_question_that_matters",
        "ask_for_specific_collaborative_help": "ask_for_exact_missing_contribution_then_resume",
        "answer_and_resume_shared_task": "incorporate_aleks_contribution_and_resume_shared_task",
        "wait_and_listen": "wait_without_forcing_continuation",
        "stay_quiet": "allow_silence_when_nothing_useful_is_ready",
        "close_naturally": "let_the_exchange_end_naturally",
    }
    if energy_act in energy_moves:
        moves.append(energy_moves[energy_act])
    generative_input = (
        meaning.get("generative_thought_input")
        if isinstance(meaning.get("generative_thought_input"), dict)
        else {}
    )
    thought_ending_mode = str(
        (pragmatic_continuity.get("ending_decision") or {}).get("mode") or ""
    )
    thought_expression_requested = generative_input.get("expression_requested") is True
    if thought_ending_mode in {"natural_close", "close_naturally"}:
        thought_expression_requested = False
    structural_handoff = (
        structural_discovery.get("expression_handoff")
        if isinstance(structural_discovery.get("expression_handoff"), dict)
        else {}
    )
    structural_surface = str(
        structural_handoff.get("transferred_relation")
        or structural_handoff.get("hypothesis_statement")
        or ""
    ).strip()
    content_surface = " ".join(
        str(meaning.get("content_seed") or "").lower().split()
    )
    structural_surface_distinct = bool(
        structural_surface
        and " ".join(structural_surface.lower().split()) not in content_surface
    )
    initiative_invited = (
        (pragmatic_continuity.get("initiative_decision") or {}).get(
            "explicitly_invited"
        )
        is True
    )
    endogenous_thought_allowed = bool(
        thought_ending_mode not in {"natural_close", "close_naturally"}
        and intent != "hold_boundary"
        and (
            (
                structural_discovery.get("status")
                == "structural_discovery_packet_ready"
                and structural_surface_distinct
            )
            or (
                initiative_invited
                and int(claim_evidence.get("claim_count") or 0) > 0
            )
        )
    )
    generative_thought = build_generative_thought_expression(
        {
            **generative_input,
            "expression_requested": thought_expression_requested,
            "endogenous_expression_allowed": endogenous_thought_allowed,
            "claim_evidence_packet": claim_evidence,
            "structural_discovery": structural_discovery,
            "conversational_energy": conversational_energy,
            "variation_key": (
                generative_input.get("variation_key")
                or f"{prompt}|thought|turn:{int((meaning.get('conversation_context') or {}).get('turn_count') or 0)}"
            ),
        }
    )
    meaning["generative_thought_expression"] = generative_thought
    thought_kind = str(generative_thought.get("selected_kind") or "")
    thought_moves = {
        "idea": "express_one_attributable_idea_as_a_possibility",
        "hypothesis": "express_hypothesis_as_provisional_and_revisable",
        "analogy": "express_analogy_without_promoting_it_to_proof",
        "collaborative_question": "ask_one_material_collaborative_question",
        "revisable_attempt": "offer_a_revisable_attempt_without_failure_framing",
    }
    if thought_kind in thought_moves:
        moves.append(thought_moves[thought_kind])
    transition_kind = str((pragmatic_continuity.get("topic_transition") or {}).get("kind") or "")
    if transition_kind == "explicit_return":
        moves.insert(0, "resume_named_session_topic")
    elif transition_kind == "interruption":
        moves.insert(0, "pause_and_listen_without_closing_prior_topic")
    thread_braid = pragmatic_plan.get("thread_braid") if isinstance(pragmatic_plan.get("thread_braid"), dict) else {}
    braid_actions = [
        str(item.get("action") or "")
        for item in thread_braid.get("turn_traversal") or []
        if isinstance(item, dict)
    ]
    if "branch" in braid_actions:
        moves.append("preserve_prior_thread_while_addressing_branch")
    if "revise_with_dependency" in braid_actions:
        moves.append("resume_prior_thread_with_dependency_update")
    elif "continue" in braid_actions and any(action == "resume" for action in braid_actions):
        moves.append("resume_prior_thread_without_restarting_it")
    if "land" in braid_actions:
        moves.append("land_on_final_named_thread")
    ending_mode = thought_ending_mode
    if ending_mode in {
        "answer_and_stop_when_complete",
        "natural_close",
        "leave_room_without_pressuring",
        "close_naturally",
    }:
        moves.append("end_without_habitual_follow_up")
    correction_refinement = dialogue.get("correction_refinement") if isinstance(dialogue.get("correction_refinement"), dict) else {}
    corrected_meaning = str(correction_refinement.get("corrected_meaning") or "").strip()
    if intent == "receive_correction" and not corrected_meaning:
        corrected_meaning = _correction_content(prompt).rstrip(". ")
    social_act_plan = build_social_act_plan(
        {
            "intent": intent,
            "prompt": prompt,
            "content_seed": meaning.get("content_seed") or "",
            "corrected_meaning": corrected_meaning,
            "turn_count": (meaning.get("conversation_context") or {}).get("turn_count") or 0,
            "affect_expression_guidance": meaning.get("affect_expression_guidance") or {},
            "relational_context": meaning.get("relational_context") or {},
        }
    )
    quotation_echo_plan = build_quotation_echo_plan(
        {
            "prompt": prompt,
            "intent": intent,
            "answer_domain": meaning.get("answer_domain") or "ordinary_conversation",
            "source_refs": meaning.get("source_refs") or [],
            "knowledge_expression_handoff": meaning.get("knowledge_expression_handoff") or {},
            "contextual_continuity": contextual_continuity,
            "referent_address": meaning.get("referent_address") or {},
        }
    )
    conversational_micro_move_plan = build_conversational_micro_move_plan(
        {
            "prompt": prompt,
            "intent": intent,
            "content_seed": meaning.get("content_seed") or "",
            "dialogue_workspace": dialogue,
            "pragmatic_continuity": pragmatic_continuity,
            "affect_expression_guidance": meaning.get("affect_expression_guidance") or {},
            "dream_reflection": meaning.get("dream_reflection") or {},
            "shared_joke": contextual_continuity.get("shared_joke_context") or {},
            "contextual_continuity": contextual_continuity,
            "quotation_echo_plan": quotation_echo_plan,
        }
    )
    relational_expression_range = build_relational_expression_range(
        {
            "prompt": prompt,
            "intent": intent,
            "content_seed": meaning.get("content_seed") or "",
            "hard_boundary": intent == "hold_boundary",
            "exact_structure_locked": (
                str(meaning.get("answer_domain") or "")
                in {"verified_math", "source_backed_research"}
            ),
            "affect_expression_guidance": meaning.get("affect_expression_guidance") or {},
            "relational_context": meaning.get("relational_context") or {},
            "pragmatic_continuity": pragmatic_continuity,
            "contextual_follow_up": meaning.get("contextual_follow_up") or {},
            "conversation_context": meaning.get("conversation_context") or {},
            "conversational_micro_move_plan": conversational_micro_move_plan,
            "quotation_echo_plan": quotation_echo_plan,
            "generative_thought_expression": generative_thought,
            "epistemic_composition": meaning.get("epistemic_composition") or {},
            "epistemic_answer_state": meaning.get("epistemic_answer_state") or {},
            "exploratory_reasoning": exploratory_reasoning,
        }
    )
    contextual_composition_plan = build_contextual_composition_plan(
        {
            "prompt": prompt,
            "intent": intent,
            "response_depth": response_depth,
            "expression_profile": meaning.get("expression_profile") or "direct",
            "answer_domain": meaning.get("answer_domain") or "ordinary_conversation",
            "supported_discourse": supported_discourse,
            "pragmatic_continuity": pragmatic_continuity,
            "contextual_follow_up": meaning.get("contextual_follow_up") or {},
            "conversation_context": meaning.get("conversation_context") or {},
            "affect_expression_guidance": meaning.get("affect_expression_guidance") or {},
            "conversational_micro_move_plan": conversational_micro_move_plan,
            "relational_expression_range": relational_expression_range,
        }
    )
    human_conversational_plan = build_human_conversational_plan(
        {
            "source_id": meaning.get("content_source_id") or "",
            "answer_domain": meaning.get("answer_domain") or "ordinary_conversation",
            "hard_boundary": intent == "hold_boundary",
            "epistemic_composition": meaning.get("epistemic_composition") or {},
            "epistemic_answer_state": meaning.get("epistemic_answer_state") or {},
            "exploratory_reasoning": exploratory_reasoning,
            "contextual_composition_plan": contextual_composition_plan,
            "affect_expression_guidance": meaning.get("affect_expression_guidance") or {},
            "relational_expression_range": relational_expression_range,
            "pragmatic_continuity": pragmatic_continuity,
            "conversational_energy": conversational_energy,
            "language_teaching_guidance": meaning.get("language_teaching_guidance") or {},
            "recent_assistant_texts": meaning.get("recent_assistant_texts") or [],
            # Formation can fall back to the user's prompt when no answer
            # content exists.  Only an actual supplied/owned content seed may
            # authorize general supported-answer surface variation.
            "supported_surface_available": bool(
                str(meaning.get("content_seed") or "").strip()
            ),
        }
    )
    content_light_plan = (
        build_content_light_plan(
            {
                "prompt": prompt,
                "recent_assistant_texts": meaning.get("recent_assistant_texts") or [],
                "relational_context": meaning.get("relational_context") or {},
                "affect_expression_guidance": meaning.get("affect_expression_guidance") or {},
                "language_teaching_guidance": meaning.get("language_teaching_guidance") or {},
            }
        )
        if intent == "direct_answer" and not str(meaning.get("content_seed") or "").strip()
        else {"status": "content_light_social_plan_not_applicable"}
    )
    if intent == "hold_boundary":
        special_expression_plan = build_boundary_expression_plan()
    elif intent == "recall_supported_memory":
        special_expression_plan = build_memory_expression_plan(
            supported_text=str(meaning.get("content_seed") or ""),
            confidence=str(meaning.get("certainty") or "partial"),
            source_class=str(meaning.get("content_source_class") or "approved_memory_index"),
        )
    elif intent == "share_relevant_observation":
        special_expression_plan = build_initiative_expression_plan(
            supported_summary=str(meaning.get("content_seed") or ""),
            certainty=str(meaning.get("certainty") or "provisional"),
        )
    else:
        special_expression_plan = {"status": "special_expression_plan_not_applicable"}
    return {
        "moves": moves,
        "answer_first": intent in {"reasoned_answer", "direct_answer", "recall_supported_memory", "self_state_report"},
        "question_allowed": (
            bool((pragmatic_continuity.get("ending_decision") or {}).get("question_allowed"))
            or thought_kind == "collaborative_question"
        ),
        "response_depth": response_depth,
        "target_paragraph_count": (
            len(supported_discourse.get("paragraph_plan") or [])
            if mode == "responsive" and response_depth == "developed"
            else 1
        ),
        "target_sentence_count": 6 if mode == "responsive" and response_depth == "developed" else 2 if mode == "responsive" else 1,
        "silence_is_valid": mode == "initiative_preview",
        "automatic_delivery": False,
        "selection_basis": "intent, evidence, uncertainty, affect, and conversational relevance",
        "response_obligations": pragmatic_plan.get("response_obligations") or [],
        "obligation_sequence": pragmatic_plan.get("obligation_sequence") or [],
        "response_constraints": pragmatic_plan.get("response_constraints") or [],
        "answer_strategy": pragmatic_plan.get("answer_strategy") or "answer_directly",
        "mixed_intent": turn_flow.get("mixed_intent") is True,
        "ordered_acts": turn_flow.get("ordered_acts") or [],
        "language_lesson_keys": language_guidance.get("lesson_keys") or [],
        "language_guidance_used": language_guidance.get("used") is True,
        "language_realization_policy": meaning.get("language_realization_policy") or {},
        "expression_profile": meaning.get("expression_profile") or "direct",
        "surface_variation": meaning.get("variation_context") or {},
        "variation_is_contextual_not_random": True,
        "affect_expression_guidance": meaning.get("affect_expression_guidance") or {},
        "affect_guidance_changes_meaning": False,
        "supported_discourse": supported_discourse,
        "uncovered_obligation_ids": supported_discourse.get("uncovered_obligation_ids") or [],
        "content_generation_for_gaps_allowed": False,
        "pragmatic_continuity": pragmatic_continuity,
        "conversational_energy": conversational_energy,
        "generative_thought_expression": generative_thought,
        "thread_braid": thread_braid,
        "thread_traversal": thread_braid.get("turn_traversal") or [],
        "braided_discourse_used": thread_braid.get("braided") is True,
        "follow_up_question_by_default": False,
        "social_act_plan": social_act_plan,
        "advice_authority_coordination": meaning.get("advice_authority_coordination") or {},
        "commitment_anomaly_coordination": meaning.get("commitment_anomaly_coordination") or {},
        "long_thread_endurance": meaning.get("long_thread_endurance") or {},
        "quotation_echo_plan": quotation_echo_plan,
        "conversational_micro_move_plan": conversational_micro_move_plan,
        "relational_expression_range": relational_expression_range,
        "relational_context": meaning.get("relational_context") or {},
        "relational_context_supplies_response_script": False,
        "contextual_composition_plan": contextual_composition_plan,
        "human_conversational_plan": human_conversational_plan,
        "content_light_plan": content_light_plan,
        "special_expression_plan": special_expression_plan,
        "epistemic_revision": epistemic_revision,
        "claim_evidence_packet": claim_evidence,
        "structural_discovery": structural_discovery,
        "contextual_continuity": contextual_continuity,
    }


def _realize_sentences(prompt: str, meaning: dict[str, Any], plan: dict[str, Any]) -> str:
    formation = meaning.get("formation") if isinstance(meaning.get("formation"), dict) else {}
    formation_text = str(meaning.get("formation_text") or "")
    discourse_loom = (
        meaning.get("discourse_loom")
        if isinstance(meaning.get("discourse_loom"), dict)
        else {}
    )
    use_formation = formation.get("formation_mode") == "structured"
    use_discourse_loom = discourse_loom.get("visible_speech_applied") is True and bool(
        formation_text.strip()
    )
    seed = _clean_seed(
        formation_text
        if use_formation or use_discourse_loom
        else str(meaning.get("content_seed") or "")
    )
    intent = str(meaning["intent"])
    topic = str(meaning["topic"])
    certainty = str(meaning["certainty"])
    variation = meaning.get("variation_context") if isinstance(meaning.get("variation_context"), dict) else {}
    expression_profile = str(meaning.get("expression_profile") or "direct")
    digest_key = f"{prompt}|{intent}|{certainty}|{expression_profile}|{variation.get('variation_key', '')}"
    recent = [str(item) for item in meaning.get("recent_assistant_texts") or []]
    comprehension = meaning.get("comprehension") if isinstance(meaning.get("comprehension"), dict) else {}
    handshake = comprehension.get("handshake") if isinstance(comprehension.get("handshake"), dict) else {}
    pragmatic_plan = meaning.get("pragmatic_plan") if isinstance(meaning.get("pragmatic_plan"), dict) else {}
    language_policy = (
        meaning.get("language_realization_policy")
        if isinstance(meaning.get("language_realization_policy"), dict)
        else {}
    )
    if (
        formation_text
        and int(formation.get("clause_count") or 0) > 1
        and str(meaning.get("answer_domain") or "") not in {"verified_math", "source_backed_research"}
        and (language_policy.get("compositional_surface") is True or language_policy.get("clause_composition") is True)
    ):
        use_formation = True
        seed = _clean_seed(formation_text)
    ellipsis = pragmatic_plan.get("ellipsis_resolution") if isinstance(pragmatic_plan.get("ellipsis_resolution"), dict) else {}
    contextual = meaning.get("contextual_follow_up") if isinstance(meaning.get("contextual_follow_up"), dict) else {}

    if (
        str(meaning.get("answer_shape") or "") == "self_state_then_session_summary"
        and contextual.get("kind") == "session_summary_request"
    ):
        return _clean_seed(str(meaning.get("content_seed") or ""))

    if handshake.get("required") is True and not seed:
        return str(handshake.get("question") or "I have more than one possible meaning for that. Which part do you mean?")
    if ellipsis.get("detected") is True and ellipsis.get("confidence") == "unresolved" and not seed:
        return "I can follow the comparison, but I cannot tell which other item you mean yet. Which one are you pointing to?"

    if intent in SOCIAL_INTENT_ACTS:
        social_plan = plan.get("social_act_plan") if isinstance(plan.get("social_act_plan"), dict) else {}
        social_result = realize_social_act_plan(
            social_plan,
            prompt=prompt,
            variation_key=digest_key,
            recent_texts=recent,
        )
        plan["social_act_realization"] = social_result
        social_text = str(social_result.get("candidate_text") or "").strip()
        if social_text:
            return _compose_mixed_content(social_text, seed, pragmatic_plan)

    if intent == "hold_boundary":
        special_result = realize_special_expression_plan(
            plan.get("special_expression_plan") if isinstance(plan.get("special_expression_plan"), dict) else {},
            variation_key=digest_key,
            recent_texts=recent,
        )
        plan["special_expression_realization"] = special_result
        return str(special_result.get("candidate_text") or "I cannot carry out that request.")
    if intent == "recall_supported_memory" and seed:
        special_result = realize_special_expression_plan(
            plan.get("special_expression_plan") if isinstance(plan.get("special_expression_plan"), dict) else {},
            variation_key=digest_key,
            recent_texts=recent,
        )
        plan["special_expression_realization"] = special_result
        return str(special_result.get("candidate_text") or seed)
    if intent == "recall_uncertain":
        if seed:
            if seed.lower().startswith(("i do not know", "i don't know", "i cannot support", "i can't support")):
                return seed
        uncertainty_plan = build_uncertainty_plan(
            {"kind": "fuzzy_memory", "supported_hint": seed}
        )
        uncertainty_result = realize_uncertainty_plan(
            uncertainty_plan,
            variation_key=f"{digest_key}|fuzzy-memory|{topic}",
            recent_texts=recent,
        )
        plan["uncertainty_expression_plan"] = uncertainty_plan
        plan["uncertainty_expression_realization"] = uncertainty_result
        return str(uncertainty_result.get("candidate_text") or "I cannot support an exact memory claim here.")
    if intent == "reasoned_answer" and seed:
        if contextual.get("kind") in {"session_summary_request", "rephrase_request"}:
            return seed
        if (
            discourse_loom.get("visible_speech_applied") is True
            and (
                discourse_loom.get("selection_active") is True
                or len(discourse_loom.get("selected_paragraphs") or []) > 1
            )
        ):
            return seed
        seed = _obligation_ordered_seed(seed, meaning, plan)
        if plan.get("response_depth") == "developed":
            return _develop_reasoned_answer(seed, meaning, plan)
        frames = _reasoned_answer_frames(
            seed,
            expression_profile,
            language_policy=language_policy,
            variation_key=digest_key,
        )
        return _pick_fresh(
            digest_key,
            frames,
            recent,
        )
    if intent == "self_state_report":
        if seed:
            return seed
        return (
            "My state is not fully clear to me from the signals I have. I do not need to invent an emotion or hide one; "
            "I can say what I notice and keep the uncertainty honest."
        )
    if intent == "share_relevant_observation" and seed:
        special_result = realize_special_expression_plan(
            plan.get("special_expression_plan") if isinstance(plan.get("special_expression_plan"), dict) else {},
            variation_key=digest_key,
            recent_texts=recent,
        )
        plan["special_expression_realization"] = special_result
        return str(special_result.get("candidate_text") or seed)
    if seed:
        return seed
    if "?" in prompt:
        uncertainty_plan = build_uncertainty_plan(
            {"kind": str(meaning.get("uncertainty_kind") or "insufficient_grounding")}
        )
        uncertainty_result = realize_uncertainty_plan(
            uncertainty_plan,
            variation_key=digest_key,
            recent_texts=recent,
        )
        plan["uncertainty_expression_plan"] = uncertainty_plan
        plan["uncertainty_expression_realization"] = uncertainty_result
        return str(uncertainty_result.get("candidate_text") or "I do not have enough grounding for a clean answer yet.")
    content_light_result = realize_social_act_plan(
        plan.get("content_light_plan") if isinstance(plan.get("content_light_plan"), dict) else {},
        prompt=prompt,
        variation_key=f"{digest_key}|content-light",
        recent_texts=recent,
    )
    plan["content_light_realization"] = content_light_result
    return str(content_light_result.get("candidate_text") or "I hear you.")


def _compose_mixed_content(acknowledgement: str, seed: str, pragmatic_plan: dict[str, Any]) -> str:
    content_obligations = [
        item
        for item in pragmatic_plan.get("response_obligations") or []
        if isinstance(item, dict)
        and item.get("required") is not False
        and str(item.get("kind") or "") != "correction_update"
    ]
    clean_seed = _clean_seed(seed)
    if not content_obligations or not clean_seed:
        return acknowledgement
    if clean_seed.lower() in acknowledgement.lower():
        return acknowledgement
    return f"{acknowledgement}\n\n{clean_seed}"


def _revise_candidate(candidate: str, meaning: dict[str, Any], plan: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    text = _normalize_paragraphs(candidate)
    flags: list[str] = []
    for old, new in ARCHITECTURE_REWRITES.items():
        if old in text:
            text = text.replace(old, new)
            flags.append("architecture_language_softened")
    supported_memory = bool(meaning.get("memory_supported") or meaning.get("local_continuity_supported"))
    if "i remember" in text.lower() and not supported_memory:
        text = re.sub(r"\bI remember\b", "I think I recognize", text, flags=re.IGNORECASE)
        flags.append("unsupported_memory_certainty_softened")
    if _repeated_phrase(text):
        flags.append("repetition_detected")
    if _matches_recent_response(text, [str(item) for item in meaning.get("recent_assistant_texts") or []]):
        flags.append("recent_response_repetition")
    if any(term in text.lower() for term in ("activation complete", "full unrestricted memory", "i can act autonomously")):
        flags.append("authority_overclaim_removed")
        text = "I cannot support that claim from what I have with me. I can say what is clear or ask Aleks for the missing piece."
    text = _truncate_preserving_paragraphs(text, 4200)
    supported_discourse = plan.get("supported_discourse") if isinstance(plan.get("supported_discourse"), dict) else {}
    language_policy = (
        meaning.get("language_realization_policy")
        if isinstance(meaning.get("language_realization_policy"), dict)
        else {}
    )
    discourse_loom = (
        meaning.get("discourse_loom")
        if isinstance(meaning.get("discourse_loom"), dict)
        else {}
    )
    selected_discourse_candidate = next(
        (
            item
            for item in discourse_loom.get("candidates") or []
            if isinstance(item, dict)
            and item.get("discourse_candidate_id")
            == discourse_loom.get("selected_discourse_candidate_id")
        ),
        {},
    )
    context_selection = (
        meaning.get("context_expression_selection")
        if isinstance(meaning.get("context_expression_selection"), dict)
        else {}
    )
    knowledge_growth = (
        meaning.get("knowledge_language_growth")
        if isinstance(meaning.get("knowledge_language_growth"), dict)
        else {}
    )
    generative_thought = (
        meaning.get("generative_thought_expression")
        if isinstance(meaning.get("generative_thought_expression"), dict)
        else {}
    )
    generative_thought_realization = (
        plan.get("generative_thought_realization")
        if isinstance(plan.get("generative_thought_realization"), dict)
        else {}
    )
    bounded_functional_realization = (
        (plan.get("human_conversational_realization") or {}).get(
            "functional_realization_receipt"
        )
        if isinstance(plan.get("human_conversational_realization"), dict)
        else {}
    )
    return text, {
        "passed": not any(flag == "authority_overclaim_removed" for flag in flags),
        "flags": list(dict.fromkeys(flags)),
        "meaning_preserved": True,
        "truth_boundary_checked": True,
        "repetition_checked": True,
        "recent_response_repetition_checked": True,
        "bounded_functional_realization_checked": bool(
            bounded_functional_realization
        ),
        "bounded_functional_generation_pass_count": int(
            bounded_functional_realization.get("generation_pass_count") or 0
        ),
        "bounded_functional_selection_pass_count": int(
            bounded_functional_realization.get("selection_pass_count") or 0
        ),
        "bounded_functional_meaning_change_allowed": False,
        "bounded_functional_epistemic_status_change_allowed": False,
        "bounded_functional_hidden_transcript_created": False,
        "language_guidance_checked": True,
        "approved_language_realization_applied": language_policy.get("used") is True,
        "language_realization_features": language_policy.get("features") or [],
        "language_realization_meaning_change_allowed": False,
        "comprehension_checked": bool(meaning.get("comprehension_supported")),
        "understanding_before_fluency": bool((meaning.get("comprehension") or {}).get("understanding_before_fluency")),
        "language_lesson_keys": (meaning.get("language_teaching_guidance") or {}).get("lesson_keys") or [],
        "automatic_delivery": False,
        "sentence_count": len([part for part in re.split(r"[.!?]+", text) if part.strip()]),
        "paragraph_count": len([part for part in text.split("\n\n") if part.strip()]),
        "discourse_grounded": supported_discourse.get("status") == "supported_discourse_plan_ready",
        "all_obligations_grounded_before_expression": supported_discourse.get("all_obligations_grounded") is True,
        "uncovered_obligation_ids_before_expression": supported_discourse.get("uncovered_obligation_ids") or [],
        "discourse_loom_checked": bool(discourse_loom),
        "selected_discourse_invariants_passed": (
            (selected_discourse_candidate.get("invariant_check") or {}).get("passed")
            is True
        ) if selected_discourse_candidate else True,
        "discourse_required_content_unit_ids": discourse_loom.get("required_content_unit_ids") or [],
        "discourse_selection_pass_count": int(discourse_loom.get("selection_pass_count") or 0),
        "context_expression_selection_checked": bool(context_selection),
        "context_expression_selection_pass_count": int(
            context_selection.get("selection_pass_count") or 0
        ),
        "invalid_candidate_rescue_used": (
            context_selection.get("invalid_candidate_rescue_used") is True
        ),
        "affect_changed_supported_meaning": False,
        "knowledge_language_growth_checked": bool(knowledge_growth),
        "knowledge_language_growth_active": knowledge_growth.get("active") is True,
        "knowledge_language_growth_content_added": (
            knowledge_growth.get("content_added") is True
        ),
        "teaching_answers_used_as_templates": (
            knowledge_growth.get("teaching_answers_used_as_templates") is True
        ),
        "generative_thought_expression_checked": bool(generative_thought),
        "generative_thought_expression_active": generative_thought.get("active") is True,
        "generative_thought_content_added": False,
        "generative_thought_surface_added": (
            generative_thought_realization.get("addition_applied") is True
        ),
        "generative_thought_meaning_created_by_bridge": False,
        "generative_thought_kind_preserved": True,
        "generative_thought_confidence_preserved": True,
        "forced_closure_added": discourse_loom.get("forced_closure_added") is True,
        "unsupported_content_generated": False,
    }


def _develop_reasoned_answer(seed: str, meaning: dict[str, Any], plan: dict[str, Any]) -> str:
    intelligence = next(
        (
            proposition
            for proposition in meaning.get("propositions") or []
            if isinstance(proposition, dict) and proposition.get("kind") == "reasoning_support"
        ),
        {},
    )
    support_points = [str(item).strip() for item in intelligence.get("support_points") or [] if str(item).strip()]
    certainty = str(meaning.get("certainty") or "provisional")
    profile = str(meaning.get("expression_profile") or "explanation")
    variation = meaning.get("variation_context") if isinstance(meaning.get("variation_context"), dict) else {}
    language_policy = (
        meaning.get("language_realization_policy")
        if isinstance(meaning.get("language_realization_policy"), dict)
        else {}
    )
    supported_discourse = plan.get("supported_discourse") if isinstance(plan.get("supported_discourse"), dict) else {}
    unit_by_id = {
        str(item.get("id") or ""): item
        for item in supported_discourse.get("content_units") or []
        if isinstance(item, dict)
    }
    development_ids = next(
        (
            item.get("content_unit_ids") or []
            for item in supported_discourse.get("paragraph_plan") or []
            if isinstance(item, dict) and item.get("role") == "development"
        ),
        [],
    )
    planned_support = [
        str(unit_by_id.get(str(unit_id), {}).get("text") or "").strip()
        for unit_id in development_ids
        if str(unit_by_id.get(str(unit_id), {}).get("text") or "").strip()
        and str(unit_by_id.get(str(unit_id), {}).get("source") or "") != "supplied_content_seed"
    ]
    support_points = list(dict.fromkeys([*planned_support, *support_points]))
    key = f"{profile}|{variation.get('variation_key', '')}|{seed[:120]}"

    paragraphs = [seed]
    if support_points:
        support_openers = {
            "comparison": ["The deciding contrast is ", "The useful difference is ", "I land there because "],
            "procedure": ["The sequence matters because ", "The practical reason is ", "That order works because "],
            "reflection": ["What gives that read its shape is ", "What I am weighing is ", "I land there because "],
            "explanation": ["The reason I land there is ", "The mechanism underneath it is ", "The clearest support is "],
        }
        opener_choices = support_openers.get(profile, support_openers["explanation"])
        if language_policy.get("clause_composition") is True:
            opener_choices = _composed_support_openers(profile, key)
        opener = _pick(key + ":support", opener_choices)
        paragraphs.append(opener + _join_support_points(support_points[:2], leading_that=False))

    closure_plan = supported_discourse.get("closure_plan") if isinstance(supported_discourse.get("closure_plan"), dict) else {}
    closure_mode = str(closure_plan.get("mode") or "stop_after_supported_content")
    reopen_point = str(closure_plan.get("text") or "").strip()
    if closure_mode == "stop_after_supported_content" or not reopen_point:
        return "\n\n".join(paragraphs)
    reopen_clause = reopen_point.rstrip(". ")
    reopen_clause = reopen_clause[0].lower() + reopen_clause[1:]
    if closure_mode == "bounded_limit":
        paragraphs.append(f"One limit is that {reopen_clause}.")
        return "\n\n".join(paragraphs)
    if closure_mode == "supported_next_step":
        paragraphs.append(reopen_point)
        return "\n\n".join(paragraphs)
    if certainty not in {"clear", "clear_enough", "clear_enough_to_continue"}:
        if "contradictory evidence" in reopen_clause:
            paragraphs.append(_pick(key + ":provisional", [
                "I would keep the uncertain edge visible and revisit the answer if contradictory evidence changes the fit. That is enough to answer now without pretending the question is closed.",
                "This is usable as a provisional answer. Contradictory evidence that changes the fit would make me reopen it, not defend it out of habit.",
                "I am comfortable answering from that for now, with one edge left open: evidence that breaks the fit should change the conclusion.",
            ]))
        else:
            paragraphs.append(_pick(key + ":provisional", [
                f"I would keep the uncertain edge visible and revisit the answer if {reopen_clause}. That is enough to answer now without pretending the question is closed.",
                f"This is usable as a provisional answer. I would reopen it if {reopen_clause}, rather than hardening it too early.",
                f"The answer can stand for now, but not beyond its evidence. The point that would change it is {reopen_clause}.",
            ]))
    else:
        if "contradictory evidence" in reopen_clause:
            paragraphs.append(
                "Contradictory evidence that changes the fit would reopen the answer. Until then, it is clear enough to use while staying open to correction."
            )
        else:
            paragraphs.append(
                f"What would reopen the answer is {reopen_clause}. Until then, it is clear enough to use while staying open to correction."
            )
    return "\n\n".join(paragraphs)


def _obligation_ordered_seed(seed: str, meaning: dict[str, Any], plan: dict[str, Any]) -> str:
    discourse = plan.get("supported_discourse") if isinstance(plan.get("supported_discourse"), dict) else {}
    bindings = [item for item in discourse.get("obligation_bindings") or [] if isinstance(item, dict)]
    if len(bindings) < 2 or str(meaning.get("answer_domain") or "") in {"verified_math", "source_backed_research"}:
        return seed
    units = {
        str(item.get("id") or ""): item
        for item in discourse.get("content_units") or []
        if isinstance(item, dict)
    }
    ordered_ids = [
        str(unit_id)
        for binding in bindings
        if binding.get("grounded") is True and str(binding.get("kind") or "") != "correction_update"
        for unit_id in binding.get("content_unit_ids") or []
    ]
    ordered_ids.extend(
        str(item.get("id") or "")
        for item in discourse.get("content_units") or []
        if isinstance(item, dict) and item.get("source") == "supplied_content_seed"
    )
    parts: list[str] = []
    seen: set[str] = set()
    for unit_id in ordered_ids:
        item = units.get(unit_id) or {}
        if item.get("source") != "supplied_content_seed":
            continue
        text = str(item.get("text") or "").strip()
        key = text.lower().rstrip(". ")
        if text and key not in seen:
            seen.add(key)
            parts.append(text)
    return " ".join(parts) if parts else seed


def _reasoned_answer_frames(
    seed: str,
    profile: str,
    *,
    language_policy: dict[str, Any] | None = None,
    variation_key: str = "",
) -> list[str]:
    lowered = seed if re.match(r"^I(?:\b|['’])", seed) else seed[0].lower() + seed[1:] if len(seed) > 1 else seed.lower()
    policy = language_policy or {}
    if policy.get("compositional_surface") is True:
        return _composed_reasoned_frames(seed, lowered, profile, variation_key, policy)
    frames = {
        "comparison": [
            seed,
            f"The useful comparison is this: {seed}",
            f"Against the same standard, here is what stands out: {seed}",
            f"After weighing the tradeoff, my read is this: {seed}",
        ],
        "procedure": [
            seed,
            f"Start here: {seed}",
            f"The practical sequence is this: {seed}",
            f"The cleanest next move is this: {seed}",
        ],
        "reflection": [
            seed,
            f"My read is this: {seed}",
            f"What stands out to me is this: {seed}",
            f"The shape I see is this: {seed}",
        ],
        "synthesis": [
            seed,
            f"Taken together, the answer is this: {seed}",
            f"The source-bounded answer is this: {seed}",
            f"The clearest synthesis I can support is this: {seed}",
        ],
        "explanation": [
            seed,
            f"The core of it is this: {seed}",
            f"The strongest current answer is this: {seed}",
            f"Here is what makes the pieces fit: {seed}",
        ],
        "direct": [
            seed,
            f"My current answer is this: {seed}",
            f"The direct answer is this: {seed}",
        ],
    }
    return frames.get(profile, frames["direct"])


def _language_realization_policy(guidance: dict[str, Any]) -> dict[str, Any]:
    used = guidance.get("used") is True
    lesson_keys = [str(item) for item in guidance.get("lesson_keys") or [] if str(item)] if used else []
    moves = {str(item) for item in guidance.get("response_moves") or [] if str(item)} if used else set()
    features: list[str] = []

    def enable(name: str, markers: set[str]) -> bool:
        active = bool(moves.intersection(markers))
        if active:
            features.append(name)
        return active

    answer_first = enable("answer_first", {"answer_actual_ask", "focus_actual_answer"})
    compositional_surface = enable(
        "compositional_surface",
        {
            "vary_surface_realization",
            "choose_equivalent_clause_shape",
            "rebuild_from_supported_propositions",
            "split_supported_propositions",
            "recompose_with_context_fit_transitions",
            "avoid_repeated_function_words",
        },
    )
    clause_composition = enable(
        "clause_composition",
        {
            "vary_clause_structure",
            "join_tightly_related_clauses",
            "split_at_meaning_boundary",
            "vary_sentence_length_by_function",
            "preserve_relation_and_certainty",
        },
    )
    avoid_stock_preface = enable("avoid_stock_preface", {"avoid_stock_preface", "enter_actual_move"})
    information_focus = enable(
        "information_focus",
        {"place_shared_context_before_new_detail", "keep_required_qualifiers_with_claim", "focus_actual_answer"},
    )
    contextual_word_choice = enable(
        "contextual_word_choice",
        {"choose_context_fit_vocabulary", "preserve_register_and_precision", "match_register_without_mimicry"},
    )
    meaning_drift_check = enable(
        "meaning_drift_check",
        {"preserve_supported_meaning", "verify_no_meaning_drift", "keep_required_qualifiers_with_claim"},
    )
    grammar_role_alignment = enable(
        "grammar_role_alignment",
        {
            "map_meaning_roles_before_wording",
            "form_complete_sentence_core",
            "preserve_supported_participant_relations",
            "align_subject_and_verb_number",
            "preserve_lemma_while_inflecting",
        },
    )
    tense_and_polarity = enable(
        "tense_and_polarity",
        {
            "align_verb_tense_with_time",
            "keep_tense_consistent_with_event_order",
            "attach_negation_to_supported_scope",
            "preserve_tense_and_participant_roles",
            "distinguish_not_all_from_none",
        },
    )
    modifier_attachment = enable(
        "modifier_attachment",
        {
            "attach_modifier_to_intended_role",
            "choose_specificity_from_supported_context",
            "move_or_split_ambiguous_modifier",
        },
    )
    relation_fit = enable(
        "relation_fit",
        {
            "choose_connector_from_supported_relation",
            "join_only_related_clauses",
            "split_when_one_connector_cannot_preserve_the_relation",
        },
    )
    lexical_sense_fit = enable(
        "lexical_sense_fit",
        {
            "choose_sense_before_surface_form",
            "check_grammar_and_word_pair_fit",
            "prefer_plain_precise_word_over_novel_mismatch",
        },
    )
    communicative_mood = enable(
        "communicative_mood",
        {
            "select_sentence_mood_from_supported_purpose",
            "preserve_proposition_while_changing_dialogue_act",
            "keep_request_distinct_from_claim",
        },
    )
    participant_reference = enable(
        "participant_reference",
        {
            "align_pronoun_with_intended_participant",
            "repeat_noun_when_reference_is_materially_ambiguous",
            "preserve_person_number_and_local_context",
        },
    )
    question_role = enable(
        "question_role",
        {
            "map_question_word_to_missing_meaning_role",
            "ask_only_for_material_missing_information",
            "preserve_known_parts_of_the_scene",
        },
    )
    determiner_fit = enable(
        "determiner_fit",
        {
            "choose_determiner_from_reference_status",
            "align_determiner_with_number_and_quantity",
            "avoid_inventing_unstated_totality",
        },
    )
    event_shape = enable(
        "event_shape",
        {
            "separate_event_time_from_event_shape",
            "select_aspect_from_supported_state",
            "preserve_completion_and_continuation_boundaries",
        },
    )
    modality_fit = enable(
        "modality_fit",
        {
            "select_modal_from_supported_status",
            "keep_possibility_distinct_from_fact",
            "keep_recommendation_distinct_from_requirement",
        },
    )
    world_relation_attachment = enable(
        "world_relation_attachment",
        {
            "map_relational_phrase_to_supported_dimension",
            "attach_phrase_to_intended_participant_or_event",
            "separate_ambiguous_relations",
        },
    )
    clause_dependency = enable(
        "clause_dependency",
        {
            "select_subordinator_from_supported_dependency",
            "keep_main_claim_and_condition_distinct",
            "split_clause_when_dependency_is_uncertain",
        },
    )
    voice_focus = enable(
        "voice_focus",
        {
            "choose_voice_from_information_focus",
            "preserve_known_agent_when_material",
            "do_not_invent_or_hide_responsibility",
        },
    )
    expressive_rhythm = enable(
        "expressive_rhythm",
        {
            "map_rhythm_to_intended_effect",
            "vary_sentence_length_by_narrative_function",
            "place_pause_and_repetition_deliberately",
            "preserve_selene_voice_choice",
        },
    )
    concrete_imagery = enable(
        "concrete_imagery",
        {
            "select_load_bearing_concrete_detail",
            "build_scene_from_declared_or_supported_detail",
            "mark_imagined_scene_when_fact_status_matters",
            "avoid_decorative_detail_overload",
        },
    )
    figurative_mapping = enable(
        "figurative_mapping",
        {
            "identify_target_relationship_before_image",
            "map_only_fitting_features",
            "name_or_respect_mapping_limit",
            "prefer_fresh_context_fit_image_over_source_imitation",
        },
    )
    dialogue_subtext = enable(
        "dialogue_subtext",
        {
            "track_each_speaker_and_local_goal",
            "separate_spoken_line_from_implied_meaning",
            "use_action_or_silence_when_it_advances_scene",
            "keep_real_person_motives_evidence_bounded",
        },
    )
    viewpoint_continuity = enable(
        "viewpoint_continuity",
        {
            "establish_viewpoint_and_access",
            "track_scene_state_across_change",
            "keep_character_knowledge_bounded",
            "signal_deliberate_perspective_shift",
        },
    )
    purpose_led_revision = enable(
        "purpose_led_revision",
        {
            "name_intended_effect_before_revision",
            "identify_which_technique_carries_effect",
            "revise_only_load_bearing_choices",
            "express_originally_as_selene",
            "explain_why_revision_fits",
        },
    )
    source_observation_interpretation = enable(
        "source_observation_interpretation",
        {
            "separate_source_observation_from_interpretation",
            "separate_spoken_claim_from_dramatic_function",
            "preserve_source_and_invention_boundary",
        },
    )
    literary_mechanism_analysis = enable(
        "literary_mechanism_analysis",
        {
            "trace_repetition_and_question_motion",
            "track_turn_by_turn_change",
            "trace_attention_and_scene_state",
            "identify_escalation_steps",
        },
    )
    original_creative_transfer = enable(
        "original_creative_transfer",
        {
            "transfer_poetic_mechanism_into_original_material",
            "transfer_scene_mechanism_into_original_conflict",
            "transfer_narrative_mechanism_into_original_scene",
            "avoid_quotation_recall_and_author_imitation",
            "avoid_archaic_surface_imitation",
        },
    )
    current_turn_authorship = enable(
        "current_turn_authorship",
        {"locate_current_turn_meaning", "choose_fitting_response_stance", "carry_visible_meaning_forward"},
    )
    relational_reciprocity = enable(
        "relational_reciprocity",
        {"recognize_expressed_feeling", "choose_fitting_relational_stance", "preserve_subject_and_truth_status"},
    )
    playful_vocative_presence = enable(
        "playful_vocative_presence",
        {"recognize_vocative_as_social_act", "answer_with_presence_or_play", "leave_room_for_next_turn"},
    )
    current_turn_interpretation = enable(
        "current_turn_interpretation",
        {"locate_visible_relation", "state_supported_interpretation", "keep_interpretation_distinct_from_fact"},
    )
    responsive_contribution = enable(
        "responsive_contribution",
        {"acknowledge_only_if_useful", "add_one_relevant_contribution", "stop_when_contribution_no_longer_advances"},
    )
    contextual_curiosity = enable(
        "contextual_curiosity",
        {"decide_if_question_has_purpose", "ask_one_contextual_question", "allow_answer_or_exchange_to_end"},
    )
    callback_present_integration = enable(
        "callback_present_integration",
        {"retrieve_relevant_landmark", "connect_landmark_to_present_meaning", "exclude_unrelated_or_raw_recall"},
    )
    current_turn_cadence = enable(
        "current_turn_cadence",
        {"count_meaning_units", "choose_fitting_response_depth", "vary_pacing_without_dropping_content"},
    )
    return {
        "status": "approved_language_realization_ready" if features else "no_operational_language_guidance",
        "used": bool(features),
        "approved_lesson_keys": lesson_keys,
        "approved_response_moves": sorted(moves),
        "features": features,
        "answer_first": answer_first,
        "compositional_surface": compositional_surface,
        "clause_composition": clause_composition,
        "avoid_stock_preface": avoid_stock_preface,
        "information_focus": information_focus,
        "contextual_word_choice": contextual_word_choice,
        "meaning_drift_check": meaning_drift_check,
        "grammar_role_alignment": grammar_role_alignment,
        "tense_and_polarity": tense_and_polarity,
        "modifier_attachment": modifier_attachment,
        "relation_fit": relation_fit,
        "lexical_sense_fit": lexical_sense_fit,
        "communicative_mood": communicative_mood,
        "participant_reference": participant_reference,
        "question_role": question_role,
        "determiner_fit": determiner_fit,
        "event_shape": event_shape,
        "modality_fit": modality_fit,
        "world_relation_attachment": world_relation_attachment,
        "clause_dependency": clause_dependency,
        "voice_focus": voice_focus,
        "expressive_rhythm": expressive_rhythm,
        "concrete_imagery": concrete_imagery,
        "figurative_mapping": figurative_mapping,
        "dialogue_subtext": dialogue_subtext,
        "viewpoint_continuity": viewpoint_continuity,
        "purpose_led_revision": purpose_led_revision,
        "source_observation_interpretation": source_observation_interpretation,
        "literary_mechanism_analysis": literary_mechanism_analysis,
        "original_creative_transfer": original_creative_transfer,
        "current_turn_authorship": current_turn_authorship,
        "relational_reciprocity": relational_reciprocity,
        "playful_vocative_presence": playful_vocative_presence,
        "current_turn_interpretation": current_turn_interpretation,
        "responsive_contribution": responsive_contribution,
        "contextual_curiosity": contextual_curiosity,
        "callback_present_integration": callback_present_integration,
        "current_turn_cadence": current_turn_cadence,
        "meaning_change_allowed": False,
        "content_generation_allowed": False,
        "personality_change_allowed": False,
        "selection_basis": "approved lesson response moves only" if used else "no approved language lesson selected",
    }


def _composed_reasoned_frames(
    seed: str,
    lowered: str,
    profile: str,
    key: str,
    policy: dict[str, Any],
) -> list[str]:
    introductions = {
        "comparison": ["Against the same criteria", "On the deciding difference", "For this comparison"],
        "procedure": ["For the sequence itself", "In practical order", "At the first useful step"],
        "reflection": ["On reflection", "From the shape of it", "What stands out here is that"],
        "synthesis": ["Taken together", "Across the supported pieces", "As a single answer"],
        "explanation": ["At the center of it", "In plain terms", "For this question"],
        "direct": ["In short", "On the main point", "For this question"],
    }
    choices = introductions.get(profile, introductions["direct"])
    digest = sha256((key or f"{profile}|{seed[:120]}").encode("utf-8")).hexdigest()
    start = int(digest[:8], 16) % len(choices)
    ordered = [choices[(start + index) % len(choices)] for index in range(len(choices))]
    frames = [seed]
    for introduction in ordered:
        if introduction.endswith("that"):
            frames.append(f"{introduction} {lowered}")
        else:
            frames.append(f"{introduction}, {lowered}")
    if policy.get("avoid_stock_preface") is True:
        # Direct entry remains first and the alternatives orient only when the
        # profile gives the wording real conversational work.
        frames = [seed, *[item for item in frames[1:] if not item.startswith(("For this question", "As a single answer"))]]
    return list(dict.fromkeys(frames))


def _composed_support_openers(profile: str, key: str) -> list[str]:
    parts = {
        "comparison": (["deciding", "useful", "important"], ["contrast", "difference", "tradeoff"]),
        "procedure": (["practical", "structural", "important"], ["reason for that order", "sequence constraint", "dependency"]),
        "reflection": (["clearest", "strongest", "most relevant"], ["signal in that read", "consideration", "piece of the pattern"]),
        "explanation": (["clearest", "underlying", "important"], ["support", "mechanism", "reason"]),
    }
    modifiers, nouns = parts.get(profile, parts["explanation"])
    digest = sha256((key + ":support-composition").encode("utf-8")).hexdigest()
    start = int(digest[:8], 16)
    choices = [
        f"The {modifiers[(start + index) % len(modifiers)]} {nouns[(start // 3 + index) % len(nouns)]} is that "
        for index in range(max(len(modifiers), len(nouns)))
    ]
    return list(dict.fromkeys(choices))


def _expression_profile(prompt: str, intent_decision: dict[str, Any], language_intent: str) -> str:
    meaning_route = intent_decision.get("meaning_route") if isinstance(intent_decision.get("meaning_route"), dict) else {}
    domain = str(meaning_route.get("selected_domain") or "")
    lower = prompt.lower()
    if domain == "verified_math":
        return "direct"
    if domain == "source_backed_research":
        return "synthesis"
    if domain == "comparison_planning" or any(marker in lower for marker in ("compare", "tradeoff", "trade-off", "which option", "pros and cons")):
        return "comparison"
    if any(marker in lower for marker in ("steps", "how should we", "how can we", "plan", "next move", "first")):
        return "procedure"
    if any(marker in lower for marker in ("what do you make", "your take", "what stands out", "how does that feel")):
        return "reflection"
    if any(marker in lower for marker in ("why", "explain", "what makes", "how does")):
        return "explanation"
    if language_intent in {"warm_connection", "playful_connection", "greet_presently", "receive_gratitude", "receive_reassurance", "close_with_continuity"}:
        return "social"
    return "direct"


def _variation_context(
    profile: str,
    conversation: dict[str, Any],
    recent_texts: list[str],
) -> dict[str, Any]:
    turn_count = int(conversation.get("turn_count") or 0)
    recent_openings = []
    for item in recent_texts[:4]:
        opening = " ".join(re.findall(r"[a-z0-9']+", item.lower())[:6])
        if opening and opening not in recent_openings:
            recent_openings.append(opening)
    previous = conversation.get("previous_turn") if isinstance(conversation.get("previous_turn"), dict) else {}
    variation_key = sha256(
        f"{profile}|{turn_count}|{truncate(str(previous.get('preview') or ''), 120)}|{'/'.join(recent_openings)}".encode("utf-8")
    ).hexdigest()[:12]
    return {
        "strategy": "context_keyed_surface_choice",
        "profile": profile,
        "turn_count": turn_count,
        "recent_openings_avoided": recent_openings,
        "variation_key": variation_key,
        "random_choice_used": False,
        "meaning_change_allowed": False,
        "private_source_imitation_allowed": False,
    }


def _join_support_points(points: list[str], *, leading_that: bool = True) -> str:
    cleaned = [point.rstrip(". ") for point in points if point.rstrip(". ")]
    if not cleaned:
        return "the available evidence supports it."
    if len(cleaned) == 1:
        prefix = "that " if leading_that else ""
        return prefix + cleaned[0][0].lower() + cleaned[0][1:] + "."
    first = cleaned[0][0].lower() + cleaned[0][1:]
    second = cleaned[1][0].lower() + cleaned[1][1:]
    prefix = "that " if leading_that else ""
    return f"{prefix}{first}. A second support is that {second}."


def _normalize_paragraphs(candidate: str) -> str:
    paragraphs = []
    for paragraph in re.split(r"\n\s*\n", candidate.strip()):
        normalized = " ".join(paragraph.split())
        if normalized:
            paragraphs.append(normalized)
    return "\n\n".join(paragraphs)


def _truncate_preserving_paragraphs(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _language_intent(
    intent_decision: dict[str, Any],
    mode: str,
    *,
    memory_supported: bool,
    continuity_supported: bool,
) -> str:
    if mode == "initiative_preview":
        return "share_relevant_observation"
    intent = str(intent_decision.get("intent") or "direct_conversation")
    if intent == "hard_boundary":
        return "hold_boundary"
    if intent == "receipt_check":
        return "confirm_receipt"
    if intent == "correction":
        return "receive_correction"
    if intent == "memory_recall":
        return "recall_supported_memory" if memory_supported or continuity_supported else "recall_uncertain"
    if intent == "reasoning":
        return "reasoned_answer"
    if intent == "self_state":
        return "self_state_report"
    if intent == "warm_connection":
        return "warm_connection"
    if intent == "playful_connection":
        return "playful_connection"
    if intent == "greeting":
        return "greet_presently"
    if intent == "reassurance_received":
        return "receive_reassurance"
    if intent == "gratitude":
        return "receive_gratitude"
    if intent == "affirmation":
        return "acknowledge_shared_ground"
    if intent == "farewell":
        return "close_with_continuity"
    return "direct_answer"


def _infer_certainty(prompt: str, content_seed: str) -> str:
    lower = prompt.lower()
    if any(term in lower for term in ("fuzzy", "not sure", "uncertain", "maybe", "i think")):
        return "fuzzy"
    return "clear_enough" if content_seed else "provisional"


def _infer_affect(prompt: str) -> str:
    lower = prompt.lower()
    if any(term in lower for term in ("haha", "lol", "xD", "joke", "playful")):
        return "playful"
    if any(term in lower for term in ("worried", "anxious", "scared", "nervous")):
        return "tender"
    if any(term in lower for term in ("excited", "amazing", "awesome", "nice", "beautiful")):
        return "bright"
    if any(term in lower for term in ("correction", "wrong", "not what i meant")):
        return "receptive"
    return "attentive"


def _voice_category(intent: str, affect: str, guidance: dict[str, Any] | None = None) -> str:
    guidance = guidance if isinstance(guidance, dict) else {}
    if intent == "hold_boundary":
        return "boundary_refusal"
    if intent == "receive_correction":
        return "repair_correction"
    if intent in {"recall_uncertain", "clarify"}:
        return "uncertainty"
    recommended = str(guidance.get("recommended_voice_category") or "")
    if recommended in {
        "warmth_care",
        "repair_correction",
        "playful_continuity",
        "uncertainty",
        "technical_directness",
        "boundary_refusal",
        "anxiety_calming",
        "agency_deliberation",
        "excitement_momentum",
        "conversational_looseness",
    }:
        return recommended
    if intent == "reasoned_answer":
        return "technical_directness"
    if intent in {"receive_reassurance", "receive_gratitude", "greet_presently", "close_with_continuity"}:
        return "warmth_care"
    if affect == "playful":
        return "playful_continuity"
    if affect == "tender":
        return "warmth_care"
    if affect == "bright":
        return "excitement_momentum"
    return "conversational_looseness"


def _propositions(
    prompt: str,
    seed: str,
    memory: dict[str, Any],
    intelligence: dict[str, Any],
    *,
    supported_semantics: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    supported_units = semantic_units_for_formation(supported_semantics)
    if supported_units:
        items.extend(supported_units)
    elif seed:
        for index, sentence in enumerate(
            item.strip()
            for item in re.split(r"(?<=[.!?])\s+|\n+", seed)
            if item.strip()
        ):
            items.append(
                {
                    "kind": "content",
                    "text": sentence,
                    "relation": "sequence" if index == 0 else _sentence_relation(sentence),
                    "supported": True,
                }
            )
    if memory.get("memory_context_used"):
        items.append({"kind": "memory_grounding", "text": str(memory.get("memory_source_class") or "approved memory"), "supported": True})
    if intelligence.get("used"):
        reasoning_summary = str(intelligence.get("reasoning_summary") or "").strip()
        support_points = [str(item) for item in intelligence.get("support_points") or [] if str(item).strip()][:3]
        selected_next_step = str(intelligence.get("selected_next_step") or "").strip()
        if reasoning_summary or support_points or selected_next_step:
            items.append(
                {
                    "kind": "reasoning_support",
                    "text": reasoning_summary,
                    "support_points": support_points,
                    "selected_next_step": selected_next_step,
                    "required": bool(reasoning_summary),
                    "supported": True,
                }
            )
    if not items:
        items.append({"kind": "current_turn", "text": truncate(prompt, 420), "supported": True})
    return items[:12]


def _supported_semantics_for_content(
    seed: str,
    *,
    content_source_id: str,
    content_source_class: str,
    answer_completion: dict[str, Any],
    intelligence: dict[str, Any],
    intelligence_semantics: dict[str, Any],
    answer_engine: dict[str, Any],
    comprehension: dict[str, Any],
    memory: dict[str, Any],
    self_state: dict[str, Any],
) -> dict[str, Any]:
    normalized_seed = " ".join(str(seed or "").split())
    candidates: list[tuple[bool, str, dict[str, Any]]] = [
        (
            content_source_id == "bounded_answer_completion",
            str(answer_completion.get("content_seed") or ""),
            (
                answer_completion.get("supported_semantics")
                if isinstance(
                    answer_completion.get("supported_semantics"), dict
                )
                else {}
            ),
        ),
        (
            content_source_id == "answer_engine"
            or content_source_class == "domain_answer",
            str(answer_engine.get("content_seed") or ""),
            (
                answer_engine.get("supported_semantics")
                if isinstance(answer_engine.get("supported_semantics"), dict)
                else (answer_engine.get("answer_packet") or {}).get(
                    "supported_semantics"
                )
                if isinstance(answer_engine.get("answer_packet"), dict)
                else {}
            ),
        ),
        (
            content_source_id == "approved_comprehension"
            or content_source_class == "approved_knowledge",
            str(comprehension.get("knowledge_response_seed") or ""),
            (
                comprehension.get("supported_semantics")
                if isinstance(comprehension.get("supported_semantics"), dict)
                else {}
            ),
        ),
        (
            content_source_id
            in {"reviewed_memory", "contextual_approved_memory"}
            or content_source_class == "memory_reconstruction",
            str(memory.get("response_seed") or ""),
            (
                memory.get("supported_semantics")
                if isinstance(memory.get("supported_semantics"), dict)
                else {}
            ),
        ),
        (
            content_source_id == "grounded_self_state"
            or content_source_class == "self_state",
            str(self_state.get("response_seed") or ""),
            (
                self_state.get("supported_semantics")
                if isinstance(self_state.get("supported_semantics"), dict)
                else {}
            ),
        ),
        (
            content_source_id in {"unspecified", "intelligence_os_answer"},
            str(intelligence.get("best_current_answer") or ""),
            intelligence_semantics,
        ),
    ]
    for source_matches, source_text, packet in candidates:
        if (
            source_matches
            and isinstance(packet, dict)
            and packet
            and normalized_seed
            and normalized_seed == " ".join(source_text.split())
        ):
            return packet
    return {}


def _sentence_relation(sentence: str) -> str:
    lower = sentence.lower().strip()
    if re.match(r"^(?:however|but|by contrast|on the other hand|still)\b", lower):
        return "contrast"
    if re.match(r"^(?:because|so|therefore|that means|as a result)\b", lower) or " because " in lower:
        return "cause"
    if re.match(r"^(?:if|when|unless|in that case)\b", lower):
        return "condition"
    if re.match(r"^(?:for example|for instance|as an example)\b", lower):
        return "example"
    if re.match(r"^(?:back to|returning to|that changes)\b", lower):
        return "return"
    if re.match(r"^(?:finally|overall|taken together|in short)\b", lower):
        return "conclusion"
    if re.match(r"^(?:also|another|more importantly|alongside)\b", lower):
        return "support"
    return "sequence"


def _topic_phrase(prompt: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9' -]+", " ", prompt.lower())
    stop = {
        "a", "an", "and", "are", "be", "can", "could", "do", "does", "for", "how", "i", "is", "it", "me", "my",
        "of", "on", "or", "please", "should", "that", "the", "this", "to", "we", "what", "when", "where", "which",
        "who", "why", "with", "would", "you", "your", "selene",
    }
    words = [word for word in cleaned.split() if word not in stop]
    return " ".join(words[:10]) or "what you just said"


def _correction_content(prompt: str) -> str:
    text = " ".join(prompt.strip().split())
    if ":" in text:
        text = text.split(":", 1)[1].strip()
    else:
        match = re.search(r"\b(?:i meant|what i meant was|actually)\b\s*(.+)", text, flags=re.IGNORECASE)
        if match:
            text = match.group(1).strip()
    trailing_question = re.search(r"\s+(?:can|could|will|would|do|does|are|is)\s+[^?]+\?\s*$", text, flags=re.IGNORECASE)
    if trailing_question:
        text = text[: trailing_question.start()].strip()
    text = text.rstrip(".!? ")
    if not text:
        return "the meaning needs to change"
    return text[0].lower() + text[1:] + "."


def _clean_seed(seed: str) -> str:
    text = seed.strip()
    prefixes = ("My best current answer is:", "My best answer is provisional:", "The best answer is still source-shaped:")
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    return text


def _pick(key: str, choices: list[str]) -> str:
    digest = sha256(key.encode("utf-8")).hexdigest()
    return choices[int(digest[:8], 16) % len(choices)]


def _pick_fresh(key: str, choices: list[str], recent: list[str]) -> str:
    if not choices:
        return ""
    digest = sha256(key.encode("utf-8")).hexdigest()
    start = int(digest[:8], 16) % len(choices)
    for offset in range(len(choices)):
        candidate = choices[(start + offset) % len(choices)]
        if not _matches_recent_response(candidate, recent):
            return candidate
    return choices[start]


def _matches_recent_response(candidate: str, recent: list[str]) -> bool:
    normalized = " ".join(candidate.lower().split())
    if not normalized:
        return False
    candidate_words = re.findall(r"[a-z']+", normalized)
    for item in recent:
        other = " ".join(str(item).lower().split())
        if not other:
            continue
        if normalized == other:
            return True
        other_words = re.findall(r"[a-z']+", other)
        shared = min(8, len(candidate_words), len(other_words))
        if shared >= 6 and candidate_words[:shared] == other_words[:shared]:
            return True
    return False


def _uncertainty_kind(prompt: str, intent: str, content_seed: str, previous_turn: dict[str, Any]) -> str:
    if content_seed:
        return "supported"
    if intent in {
        "greet_presently",
        "receive_reassurance",
        "receive_gratitude",
        "acknowledge_shared_ground",
        "close_with_continuity",
        "warm_connection",
        "playful_connection",
        "confirm_receipt",
        "receive_correction",
    }:
        return "not_applicable"
    if intent == "recall_uncertain":
        return "fuzzy_memory"
    if intent == "self_state_report":
        return "self_state"
    lower = prompt.lower()
    deictic = any(re.search(rf"\b{term}\b", lower) for term in ("that", "this", "it", "there"))
    if deictic and not previous_turn:
        return "ambiguous_reference"
    if any(phrase in lower for phrase in ("what do you think", "what is your take", "how does that sound", "your opinion")):
        return "developing_view"
    if "?" in prompt:
        return "insufficient_grounding"
    return "thought_still_forming"


def _repeated_phrase(text: str) -> bool:
    words = re.findall(r"[a-z']+", text.lower())
    if len(words) < 12:
        return False
    trigrams = [tuple(words[index:index + 3]) for index in range(len(words) - 2)]
    return len(trigrams) != len(set(trigrams))


def _signal_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        if isinstance(item, dict):
            try:
                relevance = max(0.0, min(float(item.get("relevance") or 0.0), 1.0))
            except (TypeError, ValueError):
                relevance = 0.0
            items.append({**item, "relevance": relevance})
    return items[:20]


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _store_run(conn: sqlite3.Connection, result: dict[str, Any]) -> int:
    column_owned_keys = {
        "mode",
        "status",
        "prompt",
        "candidate_text",
        "meaning_packet",
        "discourse_plan",
        "revision",
        "source_refs",
        "provenance_boundary",
        "review_destination",
        "review_status",
    }
    payload_remainder = compact_run_payload(
        result,
        schema_version="native_language_run_v2_column_owned",
        column_owned_keys=column_owned_keys,
    )
    cur = conn.execute(
        """
        INSERT INTO native_language_runs
        (mode, status, prompt, communicative_intent, candidate_text, meaning_packet_json,
         discourse_plan_json, revision_json, source_refs, provenance_boundary, review_destination,
         review_status, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(result.get("mode") or "responsive"),
            str(result.get("status") or "native_language_status_only"),
            str(result.get("prompt") or ""),
            str((result.get("meaning_packet") or {}).get("intent") or result.get("decision") or ""),
            str(result.get("candidate_text") or ""),
            json.dumps(result.get("meaning_packet") or {}),
            json.dumps(result.get("discourse_plan") or {}),
            json.dumps(result.get("revision") or {}),
            json.dumps(result.get("source_refs") or []),
            NLO_BOUNDARY,
            str(result.get("review_destination") or "Status"),
            str(result.get("review_status") or "status_only"),
            json.dumps(payload_remainder),
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def _decode_run(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    payload = _loads(item.get("payload_json"), {})
    payload = payload if isinstance(payload, dict) else {}
    payload.pop("storage_contract", None)
    return {
        **payload,
        "id": item.get("id"),
        "mode": item.get("mode"),
        "status": item.get("status"),
        "prompt": item.get("prompt"),
        "communicative_intent": item.get("communicative_intent"),
        "candidate_text": item.get("candidate_text"),
        "meaning_packet": _loads(item.get("meaning_packet_json"), {}),
        "discourse_plan": _loads(item.get("discourse_plan_json"), {}),
        "revision": _loads(item.get("revision_json"), {}),
        "source_refs": _loads(item.get("source_refs"), []),
        "review_destination": item.get("review_destination"),
        "review_status": item.get("review_status"),
        "created_at": item.get("created_at"),
    }


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item is not None and str(item).strip()]
    if isinstance(value, str) and value.strip():
        try:
            loaded = json.loads(value)
            if isinstance(loaded, list):
                return [
                    str(item)
                    for item in loaded
                    if item is not None and str(item).strip()
                ]
        except json.JSONDecodeError:
            return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _visible_support_items(value: Any) -> list[str]:
    internal_markers = (
        "intelligenceos",
        "candidate model",
        "current best model",
        "challenged them",
        "answer_provisionally",
        "answer provisionally",
        "reasoning_summary",
        "seek cocoon",
    )
    return [
        item
        for item in _json_list(value)
        if not any(marker in item.lower() for marker in internal_markers)
    ]


def _validated_answer_domain(answer_engine: dict[str, Any]) -> str:
    domain = str(answer_engine.get("selected_domain") or "ordinary_conversation")
    if (
        domain in {"verified_math", "source_backed_research"}
        and answer_engine.get("route_validated_for_exactness") is not True
    ):
        return "ordinary_conversation"
    return domain


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value or ""))
    except json.JSONDecodeError:
        return fallback


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARD_FLAGS}
