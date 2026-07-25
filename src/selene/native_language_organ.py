from __future__ import annotations

import json
import re
import sqlite3
from hashlib import sha256
from typing import Any

from .chat_intent import classify_chat_intent
from .conversational_micro_moves import (
    build_conversational_micro_move_plan,
    compose_conversational_micro_moves,
    realize_conversational_micro_moves,
)
from .conversation_repair import plan_conversation_turn
from .discourse_planner import build_supported_discourse_plan
from .language_formation import build_semantic_frame, realize_semantic_frame
from .language_teaching_shelf import language_teaching_status, select_language_guidance
from .pragmatic_planner import build_pragmatic_plan
from .pragmatic_continuity import build_pragmatic_continuity_plan
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
from .supported_semantics import semantic_units_for_formation
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
    "voice_style_owner": "Selene Voice Module",
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
            "version": "v23_contextual_conversational_micro_moves",
            "capabilities": [
                "meaning_packet_construction",
                "discourse_move_selection",
                "semantic_sentence_realization",
                "structured_semantic_frames",
                "supported_semantic_answer_handoff",
                "literal_and_nonliteral_meaning_handoff",
                "analogy_without_equivalence_handoff",
                "contextual_optional_conversational_micro_moves",
                "attributable_dream_reflection_handoff",
                "grammar_and_morphology_realization",
                "bounded_pragmatic_planning",
                "response_obligation_planning",
                "mixed_intent_turn_flow",
                "structured_utterance_units",
                "ordered_response_obligations",
                "bounded_referent_candidates",
                "structured_correction_refinement",
                "aspect_voice_and_mood_realization",
                "conversation_repair_handoff",
                "approved_language_teaching_guidance",
                "approved_language_guided_realization",
                "compositional_social_act_realization",
                "content_light_conversational_act_realization",
                "compositional_epistemic_uncertainty_realization",
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
            "initiative_state": "preview_or_notes_only_not_automatic_speech",
            "language_teaching_shelf": language_teaching_status(conn),
            "law": "Meaning comes from Selene's organs; NLO gives it language; Voice makes the language hers.",
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


def realize_native_language(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
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
    result = _build_language_result(prompt, payload, mode="responsive")
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
        result = _build_language_result(summary, initiative_payload, mode="initiative_preview")
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


def _build_language_result(prompt: str, payload: dict[str, Any], *, mode: str) -> dict[str, Any]:
    meaning = _meaning_packet(prompt, payload, mode)
    plan = _discourse_plan(prompt, meaning, payload, mode)
    draft = _realize_sentences(prompt, meaning, plan)
    micro_move_realization = realize_conversational_micro_moves(
        plan.get("conversational_micro_move_plan"),
        variation_key=(
            f"{prompt}|micro|turn:{int((meaning.get('conversation_context') or {}).get('turn_count') or 0)}"
        ),
        recent_texts=[str(item) for item in meaning.get("recent_assistant_texts") or []],
    )
    plan["conversational_micro_move_realization"] = micro_move_realization
    draft = compose_conversational_micro_moves(draft, micro_move_realization)
    candidate, revision = _revise_candidate(draft, meaning, plan)
    return {
        "status": "native_language_response_realized" if mode == "responsive" else "native_language_initiative_draft_ready",
        "organ_name": "Native Language Organ",
        "version": "v23_contextual_conversational_micro_moves",
        "mode": mode,
        "prompt": prompt,
        "meaning_packet": meaning,
        "semantic_frame": meaning.get("semantic_frame") or {},
        "formation": meaning.get("formation") or {},
        "pragmatic_plan": meaning.get("pragmatic_plan") or {},
        "turn_flow_plan": meaning.get("turn_flow_plan") or {},
        "language_teaching_guidance": meaning.get("language_teaching_guidance") or {},
        "discourse_plan": plan,
        "draft_text": draft,
        "candidate_text": candidate,
        "revision": revision,
        "voice_handoff": {
            "ready": bool(candidate),
            "voice_owns_expression_style": True,
            "meaning_must_be_preserved": True,
            "suggested_category": meaning["voice_category"],
            "expression_guidance": meaning.get("affect_expression_guidance") or {},
            "ending_decision": (plan.get("pragmatic_continuity") or {}).get("ending_decision") or {},
            "social_act_plan": plan.get("social_act_plan") or {},
            "social_act_realization": plan.get("social_act_realization") or {},
            "conversational_micro_move_plan": plan.get("conversational_micro_move_plan") or {},
            "conversational_micro_move_realization": plan.get("conversational_micro_move_realization") or {},
            "content_light_plan": plan.get("content_light_plan") or {},
            "content_light_realization": plan.get("content_light_realization") or {},
            "uncertainty_expression_plan": plan.get("uncertainty_expression_plan") or {},
            "uncertainty_expression_realization": plan.get("uncertainty_expression_realization") or {},
            "special_expression_plan": plan.get("special_expression_plan") or {},
            "special_expression_realization": plan.get("special_expression_realization") or {},
        },
        "source_refs": meaning["source_refs"],
        "review_destination": "Status",
        "review_status": "status_only",
        "provenance_boundary": NLO_BOUNDARY,
        "visible_summary_only": True,
        "hidden_chain_of_thought_exposed": False,
    }


def _meaning_packet(prompt: str, payload: dict[str, Any], mode: str) -> dict[str, Any]:
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
    answer_packet = answer_engine.get("answer_packet") if isinstance(answer_engine.get("answer_packet"), dict) else {}
    answer_substance = (
        intelligence.get("answer_substance")
        if isinstance(intelligence.get("answer_substance"), dict)
        else {}
    )
    supported_semantics = (
        answer_substance.get("semantic_packet")
        if isinstance(answer_substance.get("semantic_packet"), dict)
        else {}
    )
    comprehension = payload.get("comprehension_context") if isinstance(payload.get("comprehension_context"), dict) else {}
    if not content_seed and intelligence.get("used"):
        content_seed = _truncate_preserving_paragraphs(
            _normalize_paragraphs(str(intelligence.get("best_current_answer") or "")),
            3800,
        )
    supported_semantics_used = _supported_semantics_owns_content(
        content_seed,
        intelligence,
        str(visible_speech_seed.get("selected_source_id") or "unspecified"),
    )
    memory = payload.get("memory_context") if isinstance(payload.get("memory_context"), dict) else {}
    self_state = payload.get("self_state_context") if isinstance(payload.get("self_state_context"), dict) else {}
    affect_expression = (
        payload.get("affect_expression_guidance")
        if isinstance(payload.get("affect_expression_guidance"), dict)
        else {}
    )
    continuity = payload.get("continuity_context") if isinstance(payload.get("continuity_context"), dict) else {}
    conversation = payload.get("conversation_context") if isinstance(payload.get("conversation_context"), dict) else {}
    conversation_spine = payload.get("conversation_spine") if isinstance(payload.get("conversation_spine"), dict) else {}
    dialogue = payload.get("dialogue_workspace") if isinstance(payload.get("dialogue_workspace"), dict) else {}
    pragmatics = dialogue.get("pragmatics") if isinstance(dialogue.get("pragmatics"), dict) else {}
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
        memory,
        intelligence,
        content_source_id=str(visible_speech_seed.get("selected_source_id") or "unspecified"),
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
    semantic_frame = build_semantic_frame(
        {
            "semantic_frame": payload.get("semantic_frame") or {},
            "propositions": payload.get("semantic_propositions") or propositions,
            "content_seed": content_seed,
            "intent_decision": intent_decision,
            "answer_shape": payload.get("answer_shape") or intent_decision.get("answer_shape"),
            "response_depth": payload.get("response_depth") or pragmatics.get("response_preference") or intent_decision.get("response_depth"),
            "certainty": certainty,
            "affect": affect,
            "source_refs": payload.get("source_refs") or [],
            "expression_directives": language_realization_policy,
        }
    )
    formation = realize_semantic_frame(
        semantic_frame,
        variation_key=(
            f"{prompt}|{intent}|turn:{int(conversation.get('turn_count') or 0)}|"
            f"previous:{truncate(str(previous_turn.get('preview') or ''), 120)}"
        ),
        recent_texts=recent_assistant_texts,
    )
    expression_profile = _expression_profile(prompt, intent_decision, intent)
    variation_context = _variation_context(expression_profile, conversation, recent_assistant_texts)
    return {
        "intent": intent,
        "intent_decision": intent_decision,
        "answer_shape": str(payload.get("answer_shape") or intent_decision.get("answer_shape") or "direct_answer"),
        "response_depth": str(payload.get("response_depth") or pragmatics.get("response_preference") or intent_decision.get("response_depth") or "standard"),
        "topic": _topic_phrase(prompt),
        "propositions": propositions,
        "content_seed": content_seed,
        "content_source_id": str(visible_speech_seed.get("selected_source_id") or "unspecified"),
        "content_source_class": str(visible_speech_seed.get("selected_source_class") or "conversation"),
        "content_source_release_allowed": visible_speech_seed.get("release_allowed") is True,
        "contextual_follow_up": contextual_follow_up,
        "figurative_interpretation": figurative_interpretation,
        "dream_reflection": dream_reflection,
        "literal_and_nonliteral_readings_remain_distinct": True,
        "analogy_is_equivalence": False,
        "conversation_spine": conversation_spine,
        "conversation_spine_used": bool(conversation_spine),
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
            "meaning_change_allowed": False,
        },
        "formation": formation,
        "formation_text": str(formation.get("candidate_text") or ""),
        "pragmatic_plan": pragmatic_plan,
        "turn_flow_plan": turn_flow_plan,
        "language_teaching_guidance": language_guidance,
        "language_realization_policy": language_realization_policy,
        "certainty": certainty,
        "uncertainty_kind": _uncertainty_kind(prompt, intent, content_seed, previous_turn),
        "affect": affect,
        "affect_expression_guidance": affect_expression,
        "affect_expression_is_emotion_claim": False,
        "relationship_posture": "warm_honest_adult_to_adult",
        "selected_route": route,
        "source_class": str(payload.get("source_class") or "current_conversation"),
        "memory_supported": memory_supported,
        "local_continuity_supported": continuity_supported,
        "intelligence_supported": intelligence.get("used") is True,
        "answer_engine_supported": answer_engine.get("used") is True,
        "answer_domain": str(answer_engine.get("selected_domain") or "ordinary_conversation"),
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
            "content_seed": meaning.get("content_seed") or "",
            "response_depth": response_depth,
            "expression_profile": meaning.get("expression_profile") or "direct",
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
            "source_refs": meaning.get("source_refs") or [],
            "thread_braid": pragmatic_plan.get("thread_braid") or dialogue.get("thread_braid") or {},
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
        }
    )
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
    ending_mode = str((pragmatic_continuity.get("ending_decision") or {}).get("mode") or "")
    if ending_mode in {"answer_and_stop_when_complete", "natural_close", "leave_room_without_pressuring"}:
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
        }
    )
    content_light_plan = (
        build_content_light_plan({"prompt": prompt})
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
        "question_allowed": bool((pragmatic_continuity.get("ending_decision") or {}).get("question_allowed")),
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
        "thread_braid": thread_braid,
        "thread_traversal": thread_braid.get("turn_traversal") or [],
        "braided_discourse_used": thread_braid.get("braided") is True,
        "follow_up_question_by_default": False,
        "social_act_plan": social_act_plan,
        "conversational_micro_move_plan": conversational_micro_move_plan,
        "content_light_plan": content_light_plan,
        "special_expression_plan": special_expression_plan,
    }


def _realize_sentences(prompt: str, meaning: dict[str, Any], plan: dict[str, Any]) -> str:
    formation = meaning.get("formation") if isinstance(meaning.get("formation"), dict) else {}
    formation_text = str(meaning.get("formation_text") or "")
    use_formation = formation.get("formation_mode") == "structured"
    seed = _clean_seed(formation_text if use_formation else str(meaning.get("content_seed") or ""))
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
    return text, {
        "passed": not any(flag == "authority_overclaim_removed" for flag in flags),
        "flags": list(dict.fromkeys(flags)),
        "meaning_preserved": True,
        "truth_boundary_checked": True,
        "repetition_checked": True,
        "recent_response_repetition_checked": True,
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
            f"Putting the options against the same standard, {lowered}",
            f"My read after weighing the tradeoff is {lowered}",
        ],
        "procedure": [
            seed,
            f"Start here: {seed}",
            f"The practical sequence is {lowered}",
            f"The cleanest next move is {lowered}",
        ],
        "reflection": [
            seed,
            f"My read is {lowered}",
            f"What stands out to me is this: {seed}",
            f"The shape I see is {lowered}",
        ],
        "synthesis": [
            seed,
            f"Taken together, {lowered}",
            f"The source-bounded answer is {lowered}",
            f"The clearest synthesis I can support is {lowered}",
        ],
        "explanation": [
            seed,
            f"The core of it is {lowered}",
            f"The strongest current answer is this: {seed}",
            f"What makes the pieces fit is {lowered}",
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
    content_source_id: str = "unspecified",
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    answer_substance = (
        intelligence.get("answer_substance")
        if isinstance(intelligence.get("answer_substance"), dict)
        else {}
    )
    intelligence_semantics_owns_seed = _supported_semantics_owns_content(
        seed,
        intelligence,
        content_source_id,
    )
    semantic_packet = (
        answer_substance.get("semantic_packet")
        if intelligence_semantics_owns_seed
        and answer_substance.get("selected_for_answer") is True
        and isinstance(answer_substance.get("semantic_packet"), dict)
        else {}
    )
    supported_units = semantic_units_for_formation(semantic_packet)
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


def _supported_semantics_owns_content(
    seed: str,
    intelligence: dict[str, Any],
    content_source_id: str,
) -> bool:
    best_current_answer = " ".join(str(intelligence.get("best_current_answer") or "").split())
    normalized_seed = " ".join(str(seed or "").split())
    return (
        content_source_id in {"unspecified", "intelligence_os_answer"}
        and bool(best_current_answer)
        and normalized_seed == best_current_answer
    )


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


def _store_run(conn: sqlite3.Connection, result: dict[str, Any]) -> int:
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
            json.dumps(result),
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def _decode_run(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    return {
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
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        try:
            loaded = json.loads(value)
            if isinstance(loaded, list):
                return [str(item) for item in loaded if str(item).strip()]
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


def _loads(value: Any, fallback: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value or ""))
    except json.JSONDecodeError:
        return fallback


def _with_guards(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, **GUARD_FLAGS}
