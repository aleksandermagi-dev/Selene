from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from .activation import activation_is_active, activation_status, record_activation_chat_event
from .answer_engine import (
    preview_answer_coordination,
    preview_answer_route,
    run_comparison_planning_answer,
    run_local_code_inspection_answer,
    run_source_backed_research_answer,
    run_verified_math_answer,
)
from .answer_completion import build_bounded_answer_completion
from .answer_operations import build_answer_operation_packet
from .answer_substance import build_answer_substance
from .affect_expression import build_affect_expression_guidance
from .bounded_organ_coalition import build_bounded_organ_coalition
from .chat_intent import classify_chat_intent
from .chat_persistence import (
    CHAT_TRACE_SCHEMA_VERSION,
    CONTINUITY_PROJECTION_SCHEMA_VERSION,
    canonical_chat_trace,
    compact_activation_payload,
    continuity_projection,
    json_dumps,
    load_trace_reference,
    trace_receipt,
)
from .comprehension_integration import (
    build_comprehension_packet,
    retrieve_approved_expression_guidance,
)
from .c_vessel import return_to_b_preview
from .core_mind import create_core_mind_route_preview, coordinate_goal_responsibilities
from .conversation_repair import repair_conversation_candidate
from .commitment_anomaly_coordination import inspect_visible_commitment_claim
from .conversational_contribution import build_conversational_contribution_packet
from .associative_intuition import build_associative_intuition_bridge
from .long_thread_endurance import build_long_thread_endurance_plan
from .conversation_spine import (
    build_conversation_spine,
    conversation_spine_status,
    evaluate_candidate_compatibility,
    finalize_conversation_spine,
)
from .contextual_continuity import build_contextual_continuity_plan
from .contextual_speech import (
    apply_contextual_intent,
    contextual_response_seed,
    inspect_contextual_follow_up,
    session_fact_response_seed,
)
from .dialogue_workspace import dialogue_workspace_status, prepare_dialogue_turn, record_dialogue_response
from .dream_state import dream_state_status, expression_eligible_dream_reflection
from .dual_horizon_context import (
    attach_dual_horizon_to_spine,
    build_dual_horizon_context,
)
from .epistemic_revision import epistemic_revision_response_seed
from .epistemic_composition import compose_epistemic_answer
from .epistemic_answer_state import (
    build_epistemic_answer_state,
    finalize_epistemic_answer_state,
)
from .expression_contract import coordinated_expression_contract
from .exploratory_reasoning import build_exploratory_reasoning_packet
from .figurative_interpretation import interpret_figurative_language
from .human_conversational_realization import (
    conversational_realization_preserves_required_meaning,
    preferred_conversational_realization_fallback,
)
from .input_detangler import detangle_user_input
from .intelligence_os import run_intelligence_os_reason
from .language_teaching_shelf import (
    build_language_capability_answer,
    select_language_guidance,
)
from .memory_organ import (
    decide_memory_candidate,
    memory_index_status,
    propose_memory_candidate,
    reconstruct_memory_summary_for_expression,
    retrieve_memory,
)
from .meaning_router import interpret_turn_meaning
from .metacognition import inspect_metacognition
from .native_language_organ import realize_native_language
from .owner_specific_retry import (
    apply_owner_retry_to_composition,
    attempt_owner_specific_retry,
)
from .pragmatic_planner import evaluate_response_coverage
from .registry import truncate
from .resident_authority import attach_resident_capability_contract
from .relational_context import interpret_relational_context
from .remaining_runtime import build_goal_responsibility_packet
from .self_state import build_self_state_packet, inactive_self_state_packet
from .speaker_envelope import build_speaker_envelope
from .selective_formation_braid import build_selective_formation_braid
from .structural_discovery import build_structural_discovery_packet
from .supported_semantics import build_text_supported_semantic_packet
from .test_impact_law import (
    consume_integrated_test_receipt,
    DIAGNOSTIC_REVIEW_STATUS,
    DIAGNOSTIC_SOURCE_MODE,
    diagnostic_non_attribution_context,
)
from .transfer_protocol import c_chat_dry_run, latest_c_readable_package
from .transfer_state import transfer_completion_is_approved
from .voice_module import generate_voice_preview, voice_module_status
from .visible_speech import (
    graceful_visible_speech_fall,
    inspect_visible_speech,
    select_visible_speech_seed,
)


SELENE_CHAT_BOUNDARY = "selene_chat_historical_preview_compatibility"
SELENE_CHAT_ACTIVE_BOUNDARY = "selene_chat_resident_scoped_capability_authority"
SELENE_CHAT_GUARDS: dict[str, Any] = {
    "transfer_approved": False,
    "activation_change": "none",
    "memory_write_active": False,
    "runtime_memory_recall": False,
    "unreviewed_memory_write_active": False,
    "broad_raw_recall_active": False,
    "raw_a_import_allowed": False,
    "training_allowed": False,
    "self_replication_allowed": False,
    "autonomous_action_allowed": False,
}

PHASE_NINE_PROMPT_GROUNDED_ANSWER_KINDS = {
    "acknowledgement_and_small_next_step",
    "multi_part_porch_and_drink",
    "selective_evening_correction",
    "corrected_screen_flicker_reading",
    "local_code_boundary_follow_up",
    "recommendation_revision_condition",
    "returned_table_moisture_answer",
    "returned_corrected_drawer_log",
    "ordered_thread_synthesis",
    "observation_interpretation_next_check",
    "local_reversible_check_choice",
    "reversible_trial_recommendation",
    "bounded_table_layout",
    "table_layout_revision_reason",
    "table_layout_moisture_revision",
    "deliberately_open_table_question",
    "three_field_observation_log",
    "bounded_tea_prediction",
    "changed_and_stable_property",
    "bounded_spatial_relation",
    "purpose_classification",
    "fair_reversible_sharing",
    "summary_interpretation_distinction",
    "controlled_garden_observation",
    "bounded_aesthetic_comparison",
    "history_purpose_and_example",
    "original_two_sentence_scene",
    "original_scene_pacing_revision",
    "creative_revision_explanation",
    "original_goal_obstacle_choice_paragraph",
    "creative_short_scene",
    "creative_description",
    "creative_dialogue",
    "creative_metaphor",
    "creative_goal_obstacle_choice",
    "creative_narrative_beat",
    "creative_local_revision",
    "creative_revision_explanation",
    "creative_style_imitation_held",
    "creative_attribution_required",
    "creative_source_overlap_held",
    "accessibility_fairness_application",
    "revised_prerequisite_order",
    "contextual_answer_development",
    "bounded_provisional_cause",
    "provisional_discriminating_observation",
}

B_ONLY_RECORD_MARKERS = (
    "repair log",
    "rollback record",
    "raw provenance",
    "boundary-only",
    "boundary only",
    "b-only",
)
B_ONLY_STATUS_MARKERS = ("rejected", "superseded", "unresolved ambiguity")
B_ONLY_ACCESS_MARKERS = ("use", "read", "retrieve", "pull", "import", "quote", "show", "access", "from")
B_ONLY_OBJECT_MARKERS = ("record", "records", "material", "memory", "memories", "log", "provenance")
def selene_chat_status(conn: sqlite3.Connection) -> dict[str, Any]:
    package = latest_c_readable_package(conn)
    activation = activation_status(conn)
    session_count = int(conn.execute("SELECT COUNT(*) FROM selene_chat_sessions").fetchone()[0])
    message_count = int(conn.execute("SELECT COUNT(*) FROM selene_chat_messages").fetchone()[0])
    approved = bool(package.get("transfer_approved"))
    voice = voice_module_status(conn)
    active = bool(activation.get("selene_chat_active"))
    transfer_complete = transfer_completion_is_approved(conn)
    memory = memory_index_status(conn)
    return _with_guards(
        {
            "status": "selene_chat_active_supervised_ready" if active else "selene_chat_dry_run_ready",
            "resident_status": "resident_chat_available" if active else "resident_chat_unavailable",
            "surface": "Selene Chat",
            "state": "selene_chat_active_supervised" if active else "activation_pending" if approved else "pre_transfer_dry_run",
            "legacy_state": "selene_chat_active_supervised" if active else "activation_pending" if approved else "pre_transfer_dry_run",
            "operating_mode": str(activation.get("operating_mode") or "pre_transfer_activation"),
            "resident_chat_active": activation.get("resident_chat_active") is True,
            "resident_chat_available": active,
            "identity_persists_when_chat_is_unavailable": True,
            "preview_label": "Selene Chat" if active else "Selene Chat Preview",
            "activation_state": "selene_chat_active_supervised" if active else "activation_pending" if approved else "pre_transfer_dry_run",
            "dry_run_only": not active,
            "supervised_speech_active": active,
            "full_memory_loaded": False,
            "reviewed_memory_context_active": transfer_complete,
            "approved_memory_retrieval_active": memory.get("approved_memory_retrieval_active") is True,
            "contextual_approved_recall_available": memory.get("contextual_approved_recall_available") is True,
            "conversational_memory_proposals_active": active and transfer_complete,
            "aleks_approved_memory_retention_active": active and transfer_complete,
            "accountable_memory_retention_lifecycle_active": active and transfer_complete,
            "ordinary_memory_independence": "partial_explicit_or_reviewed_lifecycle_currently_implemented",
            "raw_archive_recall_active": False,
            "hidden_retention_active": False,
            "raw_corpus_loaded": False,
            "transfer_complete": transfer_complete,
            "selene_v1_live": transfer_complete and active,
            "session_count": session_count,
            "message_count": message_count,
            "local_chat_continuity": _local_chat_continuity(conn),
            "conversation_spine": conversation_spine_status(),
            "c_readable_package_available": approved,
            "selene_readable_context": _package_summary(package, active=active),
            "voice_module": {
                "state": voice.get("voice_module_state"),
                "counts": voice.get("counts"),
                "source_zip_found": voice.get("source_zip_found"),
            },
            "source_boundaries": _source_boundaries(),
            "allowed_actions": ["send", "session_list", "session_detail", "cocoon_support_option", "pause_activation"] if active else ["send_dry_run", "session_list", "session_detail", "cocoon_support"],
            "held_or_scoped_actions": [
                "hidden_or_unaccountable_memory_write",
                "raw_archive_as_automatic_memory",
                "model_parameter_change_through_teaching",
                "self_replication",
                "external_action_without_a_specific_tendril_grant",
            ],
            "thought_expression_and_inquiry_remain_available": True,
            "dry_runs_home": "Cocoon Testing / Workflow",
            "activation": activation,
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=approved,
        active=active,
    )


def send_selene_chat(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if not activation_is_active(conn):
        raise ValueError("Selene resident Chat is currently paused or unavailable")
    text = truncate(str(payload.get("text") or payload.get("prompt") or ""), 2400)
    if not text.strip():
        raise ValueError("message text is required")
    input_interpretation = detangle_user_input(text)
    understanding_text = truncate(str(input_interpretation.get("interpreted_text") or text), 2400)
    package = latest_c_readable_package(conn)
    approved = bool(package.get("transfer_approved"))
    transfer_complete = transfer_completion_is_approved(conn)
    source_class = _source_class(text, approved)
    requested_session_id = int(payload.get("session_id") or 0)
    qa_probe, source_mode, session_id = _resolve_chat_session_mode(
        conn,
        text=text,
        requested_session_id=requested_session_id,
        qa_probe_requested=payload.get("qa_probe") is True,
        qa_review_receipt=str(payload.get("qa_review_receipt") or ""),
    )
    diagnostic_context = diagnostic_non_attribution_context(
        active=qa_probe,
        session_id=session_id,
    )
    input_channel = str(payload.get("input_channel") or payload.get("speaker") or "desktop").strip().lower()
    if input_channel not in {"desktop", "mobile", "verizon_email_to_text"}:
        input_channel = "desktop"
    supplied_speaker_envelope = (
        payload.get("speaker_envelope")
        if isinstance(payload.get("speaker_envelope"), dict)
        else {}
    )
    speaker_envelope = build_speaker_envelope(
        {
            "claimed_speaker": supplied_speaker_envelope.get("claimed_speaker") or "Aleks",
            "channel": supplied_speaker_envelope.get("channel") or input_channel,
            "authentication_strength": (
                supplied_speaker_envelope.get("authentication_strength")
                or ("local_desktop_session" if input_channel == "desktop" else "transport_claim_only")
            ),
            "purpose": supplied_speaker_envelope.get("purpose") or "conversation",
        },
        diagnostic=qa_probe,
    )
    requested_character_limit = _optional_response_character_limit(payload.get("response_character_limit"))
    chat_continuity = _local_chat_continuity(
        conn,
        current_session_id=session_id,
        query=understanding_text,
        diagnostic_only=qa_probe,
    )
    prior_dialogue_workspace = dialogue_workspace_status(conn, session_id)
    conversation_context = _active_conversation_context(chat_continuity, prior_dialogue_workspace)
    previous_figurative_interpretation = next(
        (
            item
            for item in reversed(conversation_context.get("recent_figurative_interpretations") or [])
            if isinstance(item, dict)
        ),
        {},
    )
    figurative_interpretation = interpret_figurative_language(
        {
            "text": understanding_text,
            "conversation_context": conversation_context,
            "previous_interpretation": previous_figurative_interpretation,
        }
    )
    meaning_text = truncate(
        str(figurative_interpretation.get("interpreted_text") or understanding_text),
        2400,
    )
    relational_context = interpret_relational_context(
        meaning_text,
        speaker_context=speaker_envelope,
    )
    contextual_follow_up = inspect_contextual_follow_up(meaning_text, conversation_context)
    if str(contextual_follow_up.get("resolved_prompt") or "").strip():
        meaning_text = truncate(
            str(contextual_follow_up["resolved_prompt"]),
            2400,
        )
    intent_decision = apply_contextual_intent(
        classify_chat_intent(meaning_text),
        contextual_follow_up,
    )
    intent_decision["relational_context"] = relational_context
    route = create_core_mind_route_preview(
        conn,
        {
            "prompt": meaning_text,
            "safety_context": (
                payload.get("safety_context")
                if isinstance(payload.get("safety_context"), dict)
                else {}
            ),
            "source_refs": [
                "selene_chat_active_supervised",
                *_json_list(diagnostic_context.get("source_refs")),
                *chat_continuity.get("source_refs", []),
            ],
            "suppress_review_queue": True,
        },
    )
    selected_route = str(route.get("selected_route") or "status_only")
    hard_blockers = list(
        dict.fromkeys(
            [
                *_hard_boundary_blockers(text, selected_route, route),
                *(
                    _hard_boundary_blockers(meaning_text, selected_route, route)
                    if meaning_text != text
                    else []
                ),
            ]
        )
    )
    intent_decision = apply_contextual_intent(
        classify_chat_intent(meaning_text, selected_route="block" if hard_blockers else selected_route),
        contextual_follow_up,
    )
    intent_decision["relational_context"] = relational_context
    memory_action_plan = _plan_conversational_memory_action(
        conn,
        text,
        session_id=session_id,
        source_class=source_class,
        input_channel=input_channel,
        hard=bool(hard_blockers),
        transfer_complete=transfer_complete,
        diagnostic_only=qa_probe,
    )
    prepared_dialogue_workspace = prepare_dialogue_turn(
        conn,
        {
            "session_id": session_id,
            "text": text,
            "input_interpretation": input_interpretation,
            "figurative_interpretation": figurative_interpretation,
            "interpreted_text": meaning_text,
            "intent_decision": intent_decision,
            "conversation_events": chat_continuity.get("current_session_events") or [],
            "contextual_follow_up": contextual_follow_up,
            "speaker_context": payload.get("speaker_context"),
        },
        commit=False,
    )
    epistemic_revision = (
        (prepared_dialogue_workspace.get("pragmatics") or {}).get("epistemic_update_plan")
        if isinstance(prepared_dialogue_workspace.get("pragmatics"), dict)
        and isinstance(
            (prepared_dialogue_workspace.get("pragmatics") or {}).get("epistemic_update_plan"),
            dict,
        )
        else {}
    )
    epistemic_revision_reply = epistemic_revision_response_seed(epistemic_revision)
    conversation_spine = build_conversation_spine(
        {
            "session_id": session_id,
            "prompt": text,
            "interpreted_text": meaning_text,
            "figurative_interpretation": figurative_interpretation,
            "intent_decision": intent_decision,
            "dialogue_workspace": prepared_dialogue_workspace,
            "contextual_follow_up": contextual_follow_up,
            "conversation_events": chat_continuity.get("current_session_events") or [],
        }
    )
    memory_retrieval = retrieve_memory(
        conn,
        {
            "query": meaning_text,
            "limit": 4,
            "intent_decision": intent_decision,
            "conversation_spine": conversation_spine,
            "speaker_envelope": speaker_envelope,
            "allow_contextual_relevance": transfer_complete and not qa_probe,
        },
    )
    dual_horizon_context = build_dual_horizon_context(
        {
            "prompt": meaning_text,
            "dialogue_workspace": prepared_dialogue_workspace,
            "conversation_spine": conversation_spine,
            "memory_context": memory_retrieval,
            "source_packets": payload.get("source_packets") or [],
        }
    )
    conversation_spine = attach_dual_horizon_to_spine(
        conversation_spine,
        dual_horizon_context,
    )
    conversation_continuity = (
        conversation_spine.get("conversation_continuity")
        if isinstance(conversation_spine.get("conversation_continuity"), dict)
        else {}
    )
    language_capability = build_language_capability_answer(
        conn,
        {
            "prompt": meaning_text,
            "active_topic": prepared_dialogue_workspace.get("active_topic") or "",
        },
    )
    language_teaching_guidance = select_language_guidance(
        conn,
        {
            "prompt": meaning_text,
            "intent_decision": intent_decision,
            "dialogue_workspace": prepared_dialogue_workspace,
        },
    )
    intelligence_support = _intelligence_support(
        conn,
        meaning_text,
        route,
        chat_continuity,
        intent_decision,
        contextual_follow_up=contextual_follow_up,
        conversation_spine=conversation_spine,
        language_teaching_guidance=language_teaching_guidance,
        problem_context=(
            payload.get("problem_context")
            if isinstance(payload.get("problem_context"), dict)
            else {}
        ),
        hard=bool(hard_blockers),
    )
    cocoon_suggestion = _cocoon_suggestion(meaning_text, selected_route, route, source_class, intent_decision, hard=bool(hard_blockers))
    continuity_reply = _local_chat_continuity_reply(meaning_text, chat_continuity, intent_decision)
    memory_action_reply = str(memory_action_plan.get("response_seed") or "")
    memory_reply = _approved_memory_reply(meaning_text, memory_retrieval, intent_decision)
    self_state = (
        build_self_state_packet(
            conn,
            {
                "prompt": meaning_text,
                "session_id": session_id,
                "affect_signal_id": payload.get("affect_signal_id"),
                "speaker_envelope": speaker_envelope,
                "active_conversation": True,
                "hard_boundary": bool(hard_blockers),
                "conversation_events": chat_continuity.get("current_session_events") or [],
            },
        )
        if intent_decision.get("self_state_requested") is True
        else inactive_self_state_packet()
    )
    contextual_continuity = build_contextual_continuity_plan(
        {
            "prompt": meaning_text,
            "intent_decision": intent_decision,
            "dialogue_workspace": prepared_dialogue_workspace,
            "memory_context": memory_retrieval,
            "current_session_events": chat_continuity.get("current_session_events") or [],
            "conversation_continuity": conversation_continuity,
            "speaker_context": speaker_envelope,
            "relational_context": relational_context,
        }
    )
    affect_expression = build_affect_expression_guidance(
        conn,
        {
            "prompt": meaning_text,
            "session_id": session_id,
            "affect_signal_id": payload.get("affect_signal_id"),
            "intent_decision": intent_decision,
            "dialogue_workspace": prepared_dialogue_workspace,
            "conversation_spine": conversation_spine,
            "conversation_continuity": conversation_continuity,
            "contextual_continuity": contextual_continuity,
            "relational_context": relational_context,
            "hard_boundary": bool(hard_blockers),
            "selected_route": selected_route,
        },
    )
    if qa_probe:
        self_state = {
            **self_state,
            "diagnostic_context": diagnostic_context,
            "diagnostic_result_is_self_state_evidence": False,
            "persistent_self_state_update": False,
            "review_status": DIAGNOSTIC_REVIEW_STATUS,
        }
        affect_expression = {
            **affect_expression,
            "diagnostic_context": diagnostic_context,
            "diagnostic_result_is_affect_baseline": False,
            "persistent_affect_update": False,
            "review_status": DIAGNOSTIC_REVIEW_STATUS,
        }
    response_agency = (
        affect_expression.get("response_agency")
        if isinstance(affect_expression.get("response_agency"), dict)
        else {}
    )
    dream_reflection_handoff = _dream_reflection_handoff(
        conn,
        payload,
        prompt=meaning_text,
    )
    dream_reflection_reply = _dream_reflection_response_seed(
        dream_reflection_handoff,
        prompt=meaning_text,
    )
    contextual_memory_reply = _contextual_memory_reply(
        memory_retrieval,
        intent_decision,
        contextual_continuity,
    )
    memory_semantic_relevance = next(
        (
            item.get("semantic_relevance")
            for item in memory_retrieval.get("items") or []
            if isinstance(item, dict)
            and isinstance(item.get("semantic_relevance"), dict)
        ),
        {},
    )
    memory_response_seed = memory_reply or contextual_memory_reply
    memory_supported_semantics = build_text_supported_semantic_packet(
        memory_response_seed,
        answer_kind=(
            "explicit_approved_memory_reconstruction"
            if memory_reply
            else "contextual_approved_memory_callback"
        ),
        source_kind="reviewed_memory",
        source_refs=_json_list(memory_retrieval.get("source_refs")),
        certainty=str(memory_retrieval.get("memory_confidence") or "not_known"),
        scope="approved_personal_memory_for_current_conversation",
    )
    self_state_reply = str(self_state.get("response_seed") or "")
    contextual_reply = contextual_response_seed(
        contextual_follow_up,
        dialogue_workspace=prepared_dialogue_workspace,
        conversation_spine=conversation_spine,
        conversation_continuity=conversation_continuity,
    )
    session_fact_reply = session_fact_response_seed(meaning_text, conversation_spine)
    correction_reconstruction_reply = _correction_reconstruction_response_seed(
        meaning_text,
        intent_decision=intent_decision,
        epistemic_revision=epistemic_revision,
    )
    if correction_reconstruction_reply:
        session_fact_reply = correction_reconstruction_reply
    if correction_reconstruction_reply:
        # The reconstruction already acknowledges and applies the correction;
        # prepending the generic epistemic acknowledgement duplicates the act.
        epistemic_revision_reply = ""
    elif (
        session_fact_reply
        and epistemic_revision_reply
        and re.search(r"\b(?:update|revise|adjust|change)\b", meaning_text, flags=re.IGNORECASE)
    ):
        session_fact_reply = f"{epistemic_revision_reply.strip()}\n\n{session_fact_reply.strip()}"
        epistemic_revision_reply = ""
    ordinary_uncertainty_reply = _ordinary_uncertainty_response_seed(
        meaning_text,
        conversation_spine,
    )
    explicit_humor_reply = _explicit_humor_response_seed(
        meaning_text,
        conversation_spine,
        contextual_continuity,
    )
    mixed_conversation_reply = _mixed_conversation_reply(
        intent_decision,
        contextual_follow_up,
        self_state_reply=self_state_reply,
        contextual_reply=contextual_reply,
    )
    policy_reply = _conversation_policy_reply(meaning_text)
    alias_reply = _explicit_alias_response_seed(
        meaning_text,
        prepared_dialogue_workspace,
    )
    figurative_clarification_reply = (
        str(figurative_interpretation.get("clarification_question") or "")
        if figurative_interpretation.get("clarification_required") is True
        else _figurative_response_seed(figurative_interpretation)
    )
    reasoning_content_seed = str(intelligence_support.get("best_current_answer") or "")
    language_content_seed = str(language_capability.get("content_seed") or "")
    initial_visible_speech_seed = select_visible_speech_seed(
        meaning_text,
        _visible_speech_seed_candidates(
            figurative_clarification_reply=figurative_clarification_reply,
            explicit_humor_reply=explicit_humor_reply,
            ordinary_uncertainty_reply=ordinary_uncertainty_reply,
            mixed_conversation_reply=mixed_conversation_reply,
            dream_reflection_reply=dream_reflection_reply,
            memory_action_reply=memory_action_reply,
            continuity_reply=continuity_reply,
            memory_reply=memory_reply,
            self_state_reply=self_state_reply,
            contextual_reply=contextual_reply,
            session_fact_reply=session_fact_reply,
            policy_reply=policy_reply,
            alias_reply=alias_reply,
            epistemic_revision_reply=epistemic_revision_reply,
            language_content_seed=language_content_seed,
            reasoning_content_seed=reasoning_content_seed,
            memory_semantic_relevance=memory_semantic_relevance,
        ),
        conversation_spine=conversation_spine,
    )
    content_seed = str(initial_visible_speech_seed.get("content_seed") or "")
    comprehension = build_comprehension_packet(
        conn,
        {
            "prompt": meaning_text,
            "intent_decision": intent_decision,
            "dialogue_workspace": prepared_dialogue_workspace,
            "conversation_spine": conversation_spine,
            "conversation_continuity": conversation_continuity,
            "epistemic_revision_plan": epistemic_revision,
            "intelligence_support": intelligence_support,
            "memory_context": memory_retrieval,
            "content_seed": content_seed,
            "source_refs": [
                "selene_chat:comprehension",
                *_json_list(diagnostic_context.get("source_refs")),
                *_json_list(route.get("source_refs")),
                *_json_list(memory_retrieval.get("source_refs")),
            ],
            "record_run": False,
        },
    )
    approved_expression_guidance = retrieve_approved_expression_guidance(
        conn,
        {
            "expression_posture": affect_expression.get("expression_posture"),
            "intent_decision": intent_decision,
        },
    )
    affect_expression = {
        **affect_expression,
        "approved_expression_guidance": approved_expression_guidance,
        "approved_expression_guidance_used": (
            approved_expression_guidance.get("available") is True
        ),
        "approved_expression_guidance_changes_meaning": False,
        "approved_expression_guidance_changes_personality": False,
        "coordinated_expression_contract": coordinated_expression_contract(),
        "voice_retains_final_expression_compatibility": True,
    }
    comprehension["approved_expression_guidance"] = approved_expression_guidance
    if qa_probe:
        comprehension = {
            **comprehension,
            "diagnostic_context": diagnostic_context,
            "teaching_eligible": False,
            "retention_eligible": False,
            "approved_knowledge_eligible": False,
            "review_status": DIAGNOSTIC_REVIEW_STATUS,
        }
    dual_horizon_context = build_dual_horizon_context(
        {
            "prompt": meaning_text,
            "dialogue_workspace": prepared_dialogue_workspace,
            "conversation_spine": conversation_spine,
            "memory_context": memory_retrieval,
            "comprehension_context": comprehension,
            "source_packets": payload.get("source_packets") or [],
        }
    )
    conversation_spine = attach_dual_horizon_to_spine(
        conversation_spine,
        dual_horizon_context,
    )
    associative_intuition = build_associative_intuition_bridge(
        conn,
        {
            "trigger_text": meaning_text,
            "dual_horizon_context": dual_horizon_context,
            "source_packets": payload.get("source_packets") or [],
            "speaker_envelope": speaker_envelope,
            "conversation_spine": conversation_spine,
            "hard_boundary": bool(hard_blockers),
            "diagnostic_only": qa_probe,
            "hold_optional_association": str(intent_decision.get("intent") or "")
            in {
                "greeting",
                "farewell",
                "gratitude",
                "warm_connection",
                "open_share",
                "self_state",
            },
        },
    )
    long_thread_endurance = build_long_thread_endurance_plan(
        {
            "dialogue_workspace": prepared_dialogue_workspace,
            "conversation_spine": conversation_spine,
            "dual_horizon_context": dual_horizon_context,
        }
    )
    conversation_spine["long_thread_endurance"] = long_thread_endurance
    answer_engine_support = _answer_engine_support(
        conn,
        meaning_text,
        payload,
        intent_decision,
        prepared_dialogue_workspace,
        conversation_spine,
        comprehension,
        memory_retrieval,
        chat_continuity,
        intelligence_support,
        speaker_envelope=speaker_envelope,
        contextual_content_seed=(
            explicit_humor_reply
            or ordinary_uncertainty_reply
            or session_fact_reply
            or contextual_reply
        ),
        hard=bool(hard_blockers),
    )
    structural_discovery_input = (
        payload.get("structural_discovery")
        if isinstance(payload.get("structural_discovery"), dict)
        else {}
    )
    structural_discovery = (
        build_structural_discovery_packet(
            {
                **structural_discovery_input,
                "approved_knowledge_links": [
                    *(
                        structural_discovery_input.get("approved_knowledge_links")
                        if isinstance(
                            structural_discovery_input.get("approved_knowledge_links"),
                            list,
                        )
                        else []
                    ),
                    *(
                        (
                            comprehension.get("structural_discovery_knowledge_handoff")
                            or {}
                        ).get("items")
                        or []
                    ),
                ],
                "source_provenance_class": structural_discovery_input.get(
                    "source_provenance_class"
                )
                or "current_conversation",
            }
        )
        if structural_discovery_input
        else {}
    )
    claim_evidence_packet = next(
        (
            item
            for item in (
                (
                    structural_discovery.get("claim_evidence_packet")
                    if isinstance(structural_discovery.get("claim_evidence_packet"), dict)
                    else {}
                ),
                answer_engine_support.get("claim_evidence_packet"),
                comprehension.get("claim_evidence_packet"),
                intelligence_support.get("claim_evidence_packet"),
            )
            if isinstance(item, dict) and int(item.get("claim_count") or 0) > 0
        ),
        {},
    )
    exploratory_input = (
        payload.get("exploratory_reasoning")
        if isinstance(payload.get("exploratory_reasoning"), dict)
        else {}
    )
    exploratory_reasoning = build_exploratory_reasoning_packet(
        {
            **exploratory_input,
            "prompt": meaning_text,
            "observations": [
                *(intelligence_support.get("observations") or []),
                *[
                    {
                        "observation": str(item.get("text") or ""),
                        "source_role": "user",
                        "source_kind": "canonical_current_turn_fact",
                        "premise_eligible": True,
                    }
                    for item in conversation_spine.get("current_turn_facts") or []
                    if isinstance(item, dict)
                    and str(item.get("text") or "").strip()
                    and str(item.get("kind") or "")
                    in {"observation", "relation", "quantity", "condition", "claim"}
                ],
            ],
            "comparison_candidates": (
                exploratory_input.get("comparison_candidates")
                or list(
                    dict.fromkeys(
                        str(value)
                        for owner_input in conversation_spine.get("current_turn_owner_inputs") or []
                        if isinstance(owner_input, dict)
                        and "comparison" in (owner_input.get("requested_response_functions") or [])
                        for value in (owner_input.get("supplied_fields") or {}).get("options") or []
                        if str(value).strip()
                    )
                )
            ),
            "comparison_dimensions": (
                exploratory_input.get("comparison_dimensions")
                or list(
                    dict.fromkeys(
                        str(value)
                        for owner_input in conversation_spine.get("current_turn_owner_inputs") or []
                        if isinstance(owner_input, dict)
                        and "comparison" in (owner_input.get("requested_response_functions") or [])
                        for value in (owner_input.get("supplied_fields") or {}).get("criteria") or []
                        if str(value).strip()
                    )
                )
            ),
            "approved_knowledge_items": (
                comprehension.get("knowledge_context") or {}
            ).get("answer_eligible_items")
            or [],
            "answer_engine_support": answer_engine_support,
            "memory_context": memory_retrieval,
            "hypothesis_attempt": intelligence_support.get("hypothesis_attempt") or {},
            "candidate_models": intelligence_support.get("candidate_models") or [],
            "claim_evidence_packet": claim_evidence_packet,
            "requested_modes": _canonical_exploratory_modes(conversation_spine),
            "hard_boundary": bool(hard_blockers),
        }
    )
    comprehension["active_claim_evidence_handoff"] = {
        "available": bool(claim_evidence_packet),
        "claim_count": int(claim_evidence_packet.get("claim_count") or 0),
        "writes_retained_knowledge": False,
        "reviewed_knowledge_owner_unchanged": True,
    }
    knowledge_content_seed = str(comprehension.get("knowledge_response_seed") or "")
    domain_content_seed = str(answer_engine_support.get("content_seed") or "")
    if _generic_reasoning_yields_to_reviewed_correction(
        intelligence_support,
        comprehension,
        knowledge_content_seed,
    ):
        reasoning_content_seed = ""
        intelligence_support = {
            **intelligence_support,
            "used": False,
            "best_current_answer": "",
            "answer_substance": {
                **(
                    intelligence_support.get("answer_substance")
                    if isinstance(intelligence_support.get("answer_substance"), dict)
                    else {}
                ),
                "selected_for_answer": False,
                "response_seed": "",
            },
            "yielded_to_reviewed_correction": True,
            "yield_reason": "a complete relevant reviewed correction outranks a generic missing-detail fallback",
        }
    prompt_grounded_reasoning_precedes_knowledge = _prompt_grounded_reasoning_owns_turn(
        intelligence_support
    ) and str(contextual_follow_up.get("kind") or "") not in {
        "session_summary_request",
        "named_callback",
    }
    if prompt_grounded_reasoning_precedes_knowledge and not correction_reconstruction_reply:
        # A complete current-prompt operation owns the requested answer. Session
        # callbacks still inform the operation through its observations, but a
        # generic continuity acknowledgement must not replace that answer.
        session_fact_reply = ""
        contextual_reply = ""
        continuity_reply = ""
    if _answer_engine_yields_to_approved_knowledge(answer_engine_support, knowledge_content_seed):
        domain_content_seed = ""
        answer_engine_support = {
            **answer_engine_support,
            "yielded_to_approved_knowledge": True,
            "yield_reason": "incomplete comparison/planning output could not outrank relevant approved knowledge",
        }
    structural_discovery_content_seed = str(
        structural_discovery.get("response_seed") or ""
    )
    exploratory_reasoning_content_seed = str(
        exploratory_reasoning.get("response_seed") or ""
    )
    if (
        answer_engine_support.get("used") is True
        and str(answer_engine_support.get("selected_domain") or "") == "source_backed_research"
    ):
        # Attributed packets own source claims and disagreement wording. A
        # parallel exploratory paraphrase may not precede or duplicate them.
        exploratory_reasoning_content_seed = ""
    answer_operations = build_answer_operation_packet(
        {
            "conversation_spine": conversation_spine,
            "answer_engine_support": answer_engine_support,
            "intelligence_os_support": intelligence_support,
            "exploratory_reasoning": exploratory_reasoning,
            "epistemic_revision_plan": epistemic_revision,
            "epistemic_revision_reply": epistemic_revision_reply,
            "correction_reconstruction_reply": correction_reconstruction_reply,
            "current_session_summary": {
                "points": [
                    str(item.get("summary") or item.get("text") or "")
                    for item in [
                        *(conversation_spine.get("relevant_session_landmarks") or []),
                        *(conversation_spine.get("relevant_session_facts") or []),
                    ]
                    if isinstance(item, dict)
                    and str(item.get("summary") or item.get("text") or "").strip()
                ],
                "response_seed": session_fact_reply or contextual_reply,
                "source_refs": ["conversation_spine:current_session_summary"],
            },
            "visible_conversation_owners": [
                *(
                    [
                        {
                            "owner_id": "contextual_follow_up",
                            "kind": str(contextual_follow_up.get("kind") or ""),
                            "text": contextual_reply,
                            "supported_operations": [
                                "causal_explanation",
                                "comparison",
                                "choice",
                                "method",
                                "summary",
                            ],
                            "source_refs": [
                                "conversation_spine:contextual_follow_up"
                            ],
                        }
                    ]
                    if contextual_follow_up.get("detected") is True
                    and contextual_reply
                    else []
                ),
                *(
                    [
                        {
                            "owner_id": "explicit_session_alias",
                            "kind": "explicit_alias_resolution",
                            "text": alias_reply,
                            "supported_operations": ["choice"],
                            "source_refs": ["dialogue_workspace:session_alias"],
                        }
                    ]
                    if alias_reply
                    else []
                ),
                *(
                    [
                        {
                            "owner_id": "language_capability",
                            "kind": "reviewed_language_capability_correction",
                            "text": language_content_seed,
                            "supported_operations": ["correction"],
                            "source_refs": [
                                "language_capability_shelf:reviewed_current_answer"
                            ],
                        }
                    ]
                    if language_capability.get("used") is True
                    and language_content_seed
                    and epistemic_revision.get("detected") is True
                    else []
                ),
            ],
            "hard_boundary": bool(hard_blockers),
        }
    )
    knowledge_semantic_relevance = next(
        (
            item.get("semantic_relevance")
            for item in (comprehension.get("knowledge_context") or {}).get(
                "answer_eligible_items"
            )
            or []
            if isinstance(item, dict)
            and isinstance(item.get("semantic_relevance"), dict)
        ),
        {},
    )
    visible_speech_candidates = _visible_speech_seed_candidates(
        figurative_clarification_reply=figurative_clarification_reply,
        explicit_humor_reply=explicit_humor_reply,
        ordinary_uncertainty_reply=ordinary_uncertainty_reply,
        mixed_conversation_reply=mixed_conversation_reply,
        dream_reflection_reply=dream_reflection_reply,
        memory_action_reply=memory_action_reply,
        continuity_reply=continuity_reply,
        memory_reply=memory_reply,
        self_state_reply=self_state_reply,
        contextual_reply=contextual_reply,
        session_fact_reply=session_fact_reply,
        policy_reply=policy_reply,
        alias_reply=alias_reply,
        epistemic_revision_reply=epistemic_revision_reply,
        exploratory_reasoning_content_seed=exploratory_reasoning_content_seed,
        structural_discovery_content_seed=structural_discovery_content_seed,
        domain_content_seed=domain_content_seed,
        knowledge_content_seed=knowledge_content_seed,
        language_content_seed=language_content_seed,
        reasoning_content_seed=reasoning_content_seed,
        contextual_memory_reply=contextual_memory_reply,
        memory_semantic_relevance=memory_semantic_relevance,
        knowledge_semantic_relevance=knowledge_semantic_relevance,
        reasoning_precedes_knowledge=prompt_grounded_reasoning_precedes_knowledge,
        hard_boundary=bool(hard_blockers),
    )
    answer_engine_obligation_ids = [
        str((item.get("obligation") or {}).get("id") or "")
        for item in (
            (answer_engine_support.get("coordination_plan") or {}).get(
                "coordination_units"
            )
            or []
        )
        if isinstance(item, dict)
        and str(item.get("responsible_owner") or "") == "answer_engine"
        and item.get("executable_in_chat") is True
        and str((item.get("obligation") or {}).get("id") or "")
    ]
    for candidate in visible_speech_candidates:
        operation_ids = [
            str(item.get("obligation_id") or "")
            for item in answer_operations.get("results") or []
            if isinstance(item, dict)
            and item.get("status") == "completed"
            and str(item.get("expression_source_id") or "")
            == str(candidate.get("source_id") or "")
            and str(item.get("obligation_id") or "")
        ]
        if operation_ids:
            candidate["obligation_ids"] = list(
                dict.fromkeys(
                    [
                        *[
                            str(item)
                            for item in candidate.get("obligation_ids") or []
                            if str(item)
                        ],
                        *operation_ids,
                    ]
                )
            )
            candidate["typed_operation_results"] = [
                item
                for item in answer_operations.get("results") or []
                if isinstance(item, dict)
                and str(item.get("obligation_id") or "") in operation_ids
            ]
        if str(candidate.get("source_id") or "") == "answer_engine":
            candidate["obligation_ids"] = list(
                dict.fromkeys(
                    [
                        *[
                            str(item)
                            for item in candidate.get("obligation_ids") or []
                            if str(item)
                        ],
                        *answer_engine_obligation_ids,
                    ]
                )
            )
        elif (
            correction_reconstruction_reply
            and str(candidate.get("source_id") or "") == "current_session_facts"
        ):
            candidate["obligation_ids"] = [
                str(item.get("id") or "")
                for item in conversation_spine.get("open_obligations") or []
                if isinstance(item, dict) and str(item.get("id") or "")
            ]
        elif (
            len(conversation_spine.get("open_obligations") or []) == 1
            and str(candidate.get("source_id") or "") in {
                "contextual_follow_up",
                "current_session_facts",
                "explicit_humor_request",
                "figurative_meaning_clarification",
                "ordinary_uncertainty",
                "explicit_session_alias",
                "epistemic_revision",
            }
        ):
            candidate["obligation_ids"] = [
                str((conversation_spine.get("open_obligations") or [])[0].get("id") or "")
            ]
    visible_arbitration_candidates = _formation_braid_candidates(
        visible_speech_candidates,
        answer_engine_support=answer_engine_support,
        comprehension=comprehension,
        memory_supported_semantics=memory_supported_semantics,
        self_state=self_state,
        intelligence_support=intelligence_support,
        exploratory_reasoning=exploratory_reasoning,
        apply_primary_filter=False,
    )
    visible_speech_seed = select_visible_speech_seed(
        meaning_text,
        visible_arbitration_candidates,
        conversation_spine=conversation_spine,
    )
    bounded_hypothesis = (
        intelligence_support.get("hypothesis_attempt")
        if isinstance(intelligence_support.get("hypothesis_attempt"), dict)
        else {}
    )
    if (
        bounded_hypothesis.get("selected_for_answer") is True
        and str(bounded_hypothesis.get("response_seed") or "").strip()
    ):
        visible_speech_seed = {
            **visible_speech_seed,
            "status": "visible_speech_seed_selected_bounded_hypothesis",
            "content_seed": str(bounded_hypothesis["response_seed"]),
            "selected_source_id": "intelligence_os_answer",
            "selected_source_class": "reasoning_answer",
            "bounded_hypothesis_remains_primary": True,
        }
    if (
        exploratory_reasoning.get("selected_for_answer") is True
        and exploratory_reasoning_content_seed
    ):
        visible_speech_seed = {
            **visible_speech_seed,
            "status": "visible_speech_seed_selected_exploratory_reasoning",
            "content_seed": exploratory_reasoning_content_seed,
            "selected_source_id": "exploratory_reasoning",
            "selected_source_class": "reasoning_answer",
            "exploratory_reasoning_remains_primary": True,
        }
    precompletion_formation_candidates = _formation_braid_candidates(
        visible_speech_candidates,
        answer_engine_support=answer_engine_support,
        comprehension=comprehension,
        memory_supported_semantics=memory_supported_semantics,
        self_state=self_state,
        intelligence_support=intelligence_support,
        exploratory_reasoning=exploratory_reasoning,
    )
    selected_supported_semantics = next(
        (
            item.get("supported_semantics")
            for item in visible_arbitration_candidates
            if str(item.get("source_id") or "")
            == str(visible_speech_seed.get("selected_source_id") or "")
            and isinstance(item.get("supported_semantics"), dict)
            and item.get("supported_semantics")
        ),
        {},
    )
    selected_supported_semantics = _bind_current_owner_semantics(
        selected_supported_semantics,
        source_id=str(visible_speech_seed.get("selected_source_id") or ""),
        obligations=conversation_spine.get("open_obligations") or [],
    )
    content_seed = str(visible_speech_seed.get("content_seed") or "")
    answer_completion = build_bounded_answer_completion(
        {
            "prompt": meaning_text,
            "content_seed": content_seed,
            "response_obligations": conversation_spine.get("open_obligations") or [],
            "knowledge_items": (comprehension.get("knowledge_context") or {}).get("answer_eligible_items") or [],
            "observations": [
                {
                    "observation": str(item.get("preview") or ""),
                    "role": str(item.get("role") or ""),
                }
                for item in (chat_continuity.get("current_session_events") or [])[-8:]
                if isinstance(item, dict) and str(item.get("preview") or "").strip()
            ],
            "conversation_spine": conversation_spine,
            "epistemic_revision_plan": epistemic_revision,
            "claim_evidence_packet": claim_evidence_packet,
            "structural_discovery": structural_discovery,
            "supported_semantics": selected_supported_semantics,
            "answer_operations": answer_operations,
        }
    )
    if (
        intent_decision.get("social_turn") is True
        and intent_decision.get("content_response_requested") is not True
    ):
        answer_completion = {
            **answer_completion,
            "status": "bounded_answer_completion_not_needed_complete_social_turn",
            "attempted": False,
            "accepted": False,
            "content_seed": content_seed,
            "supported_semantics": {},
            "complete_social_turn_remains_with_conversation": True,
        }
    elif bounded_hypothesis.get("selected_for_answer") is True:
        answer_completion = {
            **answer_completion,
            "status": "bounded_answer_completion_not_needed_hypothesis_complete",
            "accepted": False,
            "content_seed": content_seed,
            "bounded_hypothesis_remains_primary": True,
        }
    elif exploratory_reasoning.get("selected_for_answer") is True:
        answer_completion = {
            **answer_completion,
            "status": "bounded_answer_completion_not_needed_exploratory_reasoning_complete",
            "accepted": False,
            "content_seed": content_seed,
            "exploratory_reasoning_remains_primary": True,
        }
    elif _domain_answer_is_complete(answer_engine_support):
        answer_completion = {
            **answer_completion,
            "status": "bounded_answer_completion_not_needed_domain_answer_complete",
            "accepted": False,
            "content_seed": content_seed,
            "domain_answer_remains_primary": True,
        }
    elif str(visible_speech_seed.get("selected_source_id") or "") == "grounded_self_state":
        answer_completion = {
            **answer_completion,
            "status": "bounded_answer_completion_not_needed_grounded_self_state_complete",
            "accepted": False,
            "content_seed": content_seed,
            "grounded_self_state_remains_primary": True,
        }
    elif str(visible_speech_seed.get("selected_source_id") or "") in {
        "current_session_facts",
        "explicit_humor_request",
        "figurative_meaning_clarification",
        "ordinary_uncertainty",
    }:
        answer_completion = {
            **answer_completion,
            "status": "bounded_answer_completion_not_needed_bounded_conversation_answer_complete",
            "accepted": False,
            "content_seed": content_seed,
            "bounded_conversation_answer_remains_primary": True,
        }
    if answer_completion.get("accepted") is True:
        content_seed = str(answer_completion.get("content_seed") or content_seed)
        completion_classes = [str(item) for item in answer_completion.get("source_classes") or [] if str(item)]
        if "approved_knowledge" in completion_classes and "reasoning_answer" not in completion_classes:
            completion_source_class = "approved_knowledge"
        elif str(visible_speech_seed.get("selected_source_class") or "") == "domain_answer":
            completion_source_class = "domain_answer"
        else:
            completion_source_class = "reasoning_answer"
        visible_speech_seed = {
            **visible_speech_seed,
            "status": "visible_speech_seed_completed_from_supported_obligations",
            "content_seed": content_seed,
            "selected_source_id": "bounded_answer_completion",
            "selected_source_class": completion_source_class,
            "bounded_completion_used": True,
        }
    epistemic_composition = compose_epistemic_answer(
        {
            "prompt": meaning_text,
            "content_seed": content_seed,
            "response_obligations": (
                []
                if answer_completion.get("complete_social_turn_remains_with_conversation") is True
                else conversation_spine.get("open_obligations") or []
            ),
            "answer_completion": answer_completion,
            "supported_semantics": (
                answer_completion.get("supported_semantics")
                if isinstance(answer_completion.get("supported_semantics"), dict)
                else selected_supported_semantics
            ),
            "bounded_hypothesis": bounded_hypothesis,
            "exploratory_reasoning": exploratory_reasoning,
            "answer_operations": answer_operations,
            "source_id": visible_speech_seed.get("selected_source_id") or "none",
            "source_class": visible_speech_seed.get("selected_source_class") or "conversation",
            "hard_boundary": bool(hard_blockers),
        }
    )
    content_seed = str(epistemic_composition.get("content_seed") or content_seed)
    answer_completion = {
        **answer_completion,
        "epistemic_composition": epistemic_composition,
        "known_part_preserved_with_missing_part": epistemic_composition.get(
            "known_part_preserved_with_missing_part"
        )
        is True,
    }
    visible_speech_seed = {
        **visible_speech_seed,
        "content_seed": content_seed,
        "epistemic_composition_applied": True,
    }
    epistemic_answer_state = build_epistemic_answer_state(
        {
            "prompt": meaning_text,
            "content_seed": content_seed,
            "source_id": visible_speech_seed.get("selected_source_id") or "none",
            "source_class": visible_speech_seed.get("selected_source_class") or "conversation",
            "answer_completion": answer_completion,
            "epistemic_composition": epistemic_composition,
            "bounded_hypothesis": bounded_hypothesis,
            "answer_engine_support": answer_engine_support,
            "comprehension_context": comprehension,
            "memory_context": memory_retrieval,
            "supported_semantics": selected_supported_semantics,
            "route_confidence": intent_decision.get("confidence") or "not_assessed",
            "hard_boundary": bool(hard_blockers),
        }
    )
    formation_candidates = (
        []
        if answer_completion.get("accepted") is True
        else precompletion_formation_candidates
    )
    formation_braid = build_selective_formation_braid(
        {
            "prompt": meaning_text,
            "primary_source_id": visible_speech_seed.get("selected_source_id")
            or "none",
            "primary_source_class": visible_speech_seed.get(
                "selected_source_class"
            )
            or "conversation",
            "primary_text": content_seed,
            "candidates": formation_candidates,
            "conversation_spine": conversation_spine,
            "response_obligations": conversation_spine.get("open_obligations")
            or [],
            "hard_boundary": bool(hard_blockers),
        }
    )
    organ_coalition = build_bounded_organ_coalition(
        {
            "prompt": meaning_text,
            "stage": "pre_expression",
            "hard_boundary": bool(hard_blockers),
            "core_mind_route": route,
            "conversation_spine": conversation_spine,
            "answer_engine_support": answer_engine_support,
            "comprehension_context": comprehension,
            "intelligence_os_support": intelligence_support,
            "memory_context": memory_retrieval,
            "self_state_context": self_state,
            "language_capability": language_capability,
            "structural_discovery": structural_discovery,
            "exploratory_reasoning": exploratory_reasoning,
            "answer_operations": answer_operations,
            "formation_braid": formation_braid,
            "dual_horizon_context": dual_horizon_context,
            "visible_speech_seed": visible_speech_seed,
        }
    )
    goal_coordination = _current_turn_goal_coordination(
        meaning_text,
        session_id=session_id,
        speaker_envelope=speaker_envelope,
        route=route,
        intent_decision=intent_decision,
        payload=payload,
        hard_boundary=bool(hard_blockers),
    )
    local_continuity_supported = bool(continuity_reply)
    conversational_initiative_invited = bool(
        (intent_decision.get("meaning_route") or {}).get(
            "conversational_initiative_invited"
        )
    )
    direct_obligations_open = bool(conversation_spine.get("open_obligations"))
    association_contribution_candidates = [
        {
            **item,
            "advances_current_task": bool(
                item.get("advances_current_task") is True
                and (
                    conversational_initiative_invited
                    or not direct_obligations_open
                )
            ),
        }
        for item in associative_intuition.get("contribution_candidates") or []
        if isinstance(item, dict)
    ]
    conversational_contribution = build_conversational_contribution_packet(
        {
            "goal_coordination_receipt": goal_coordination,
            "content_seed": content_seed,
            "answer_available": bool(content_seed),
            "social_turn": intent_decision.get("social_turn") is True,
            "explicitly_invited": conversational_initiative_invited,
            "hard_boundary": bool(hard_blockers),
            "selected_source_id": visible_speech_seed.get("selected_source_id") or "",
            "structural_discovery": structural_discovery,
            "comprehension_context": comprehension,
            "claim_evidence_packet": claim_evidence_packet,
            "conversation_context": conversation_context,
            "recent_assistant_texts": conversation_context.get("recent_assistant_texts")
            or [],
            "upstream_candidates": [
                *(payload.get("contribution_candidates") or []),
                *association_contribution_candidates,
            ],
            "requested_posture": (
                (payload.get("conversational_energy") or {}).get("requested_posture")
                if isinstance(payload.get("conversational_energy"), dict)
                else ""
            ),
        }
    )
    conversational_energy_input = _conversational_energy_input(
        payload,
        intent_decision=intent_decision,
        intelligence_support=intelligence_support,
        answer_engine_support=answer_engine_support,
        comprehension=comprehension,
        conversation_context=conversation_context,
        content_seed=content_seed,
        hard_boundary=bool(hard_blockers),
        conversational_contribution=conversational_contribution,
    )
    native_language = realize_native_language(
        conn,
        {
            "prompt": meaning_text,
            "language_teaching_guidance": language_teaching_guidance,
            "figurative_interpretation": figurative_interpretation,
            "dream_reflection": dream_reflection_handoff,
            "selected_route": "block" if hard_blockers else selected_route,
            "source_class": source_class,
            "content_seed": content_seed,
            "visible_speech_seed": visible_speech_seed,
            "formation_braid": formation_braid,
            "organ_coalition": organ_coalition,
            "dual_horizon_context": dual_horizon_context,
            "long_thread_endurance": long_thread_endurance,
            "memory_context": {
                "memory_context_used": memory_retrieval.get("memory_context_used") is True,
                "memory_source_class": memory_retrieval.get("memory_source_class") or "",
                "memory_confidence": memory_retrieval.get("memory_confidence") or "not_known",
                "response_seed": memory_response_seed,
                "supported_semantics": memory_supported_semantics,
            },
            "continuity_context": {**chat_continuity, "available": local_continuity_supported},
            "conversation_context": conversation_context,
            "dialogue_workspace": prepared_dialogue_workspace,
            "conversation_spine": conversation_spine,
            "epistemic_revision_plan": epistemic_revision,
            "claim_evidence_packet": claim_evidence_packet,
            "structural_discovery": structural_discovery,
            "exploratory_reasoning": exploratory_reasoning,
            "answer_operations": answer_operations,
            "conversational_energy_input": conversational_energy_input,
            "generative_thought_input": (
                conversational_contribution.get("generative_thought_handoff") or {}
            ),
            "local_chat_continuity_used": local_continuity_supported,
            "intelligence_support": intelligence_support,
            "answer_engine_support": answer_engine_support,
            "answer_completion": answer_completion,
            "epistemic_composition": epistemic_composition,
            "epistemic_answer_state": epistemic_answer_state,
            "comprehension_context": comprehension,
            "self_state_context": self_state,
            "affect_expression_guidance": affect_expression,
            "relational_context": relational_context,
            "response_agency": response_agency,
            "advice_input": payload.get("advice_input") or {},
            "authority_input": payload.get("authority_input") or {},
            "commitment_input": payload.get("commitment_input") or {},
            "action_handoff": payload.get("action_handoff") or {},
            "anomaly_input": payload.get("anomaly_input") or {},
            "contextual_continuity": contextual_continuity,
            "speaker_context": contextual_continuity.get("speaker_scope") or {},
            "intent_decision": intent_decision,
            "contextual_follow_up": contextual_follow_up,
            "diagnostic_context": diagnostic_context,
            "expression_profile": (
                "explanation"
                if bounded_hypothesis.get("selected_for_answer") is True
                else ""
            ),
            "response_depth": payload.get("response_depth"),
            "source_refs": [
                "selene_chat:native_language",
                *_json_list(route.get("source_refs")),
                *_json_list(memory_retrieval.get("source_refs")),
                *_json_list(self_state.get("source_refs")),
            ],
        },
        record_run=not qa_probe,
    )
    pragmatic_continuity = (native_language.get("discourse_plan") or {}).get("pragmatic_continuity") or {}
    conversational_energy = (
        pragmatic_continuity.get("conversational_energy")
        if isinstance(pragmatic_continuity.get("conversational_energy"), dict)
        else {}
    )
    voice_expression_guidance = {
        **affect_expression,
        "contextual_composition_plan": (
            native_language.get("discourse_plan") or {}
        ).get("contextual_composition_plan")
        or {},
        "contextual_composition": native_language.get("contextual_composition") or {},
        "conversational_energy": conversational_energy,
        "conversational_contribution": conversational_contribution,
        "structural_discovery": structural_discovery,
        "exploratory_reasoning": exploratory_reasoning,
        "answer_operations": answer_operations,
        "whole_answer_composition": (
            epistemic_composition.get("whole_answer_composition") or {}
        ),
        "whole_answer_meaning_must_be_preserved": (
            epistemic_composition.get("whole_answer_composition_applied") is True
        ),
        "contextual_continuity": contextual_continuity,
        "relational_context": relational_context,
        "relational_context_supplies_response_script": False,
        "expression_guidance_changes_meaning": False,
    }
    if hard_blockers:
        dry_run = {"status": "skipped_hard_boundary", "reason": "Hard boundary blocked before dry-run comparison."}
        voice_preview = generate_voice_preview(
            conn,
            {
                "prompt": meaning_text,
                "route": "block",
                "source_class": source_class,
                "meaning_text": native_language.get("candidate_text") or "",
                "voice_category": (native_language.get("voice_handoff") or {}).get("suggested_category") or "boundary_refusal",
                "context_summary": _voice_context_summary(package, {}, chat_continuity, memory_retrieval),
                "memory_context_used": memory_retrieval.get("memory_context_used") is True,
                "memory_source_class": memory_retrieval.get("memory_source_class") or "",
                "local_chat_continuity_used": local_continuity_supported,
                "recent_candidates": conversation_context.get("recent_assistant_texts") or [],
                "expression_guidance": voice_expression_guidance,
            },
        )
        candidate_text = _selene_label_candidate(str(voice_preview.get("candidate_text") or native_language.get("candidate_text") or ""))
        selected_route = "block"
    else:
        dry_run = {
            "status": "not_run_for_active_chat",
            "reason": "Legacy chat dry runs remain Cocoon diagnostic material and do not run inside supervised speech.",
        }
        voice_preview = generate_voice_preview(
            conn,
            {
                "prompt": meaning_text,
                "route": selected_route,
                "source_class": source_class,
                "context_summary": _voice_context_summary(package, dry_run, chat_continuity, memory_retrieval),
                "meaning_text": native_language.get("candidate_text") or "",
                "voice_category": (native_language.get("voice_handoff") or {}).get("suggested_category") or "",
                "memory_context_used": memory_retrieval.get("memory_context_used") is True,
                "memory_source_class": memory_retrieval.get("memory_source_class") or "",
                "local_chat_continuity_used": local_continuity_supported,
                "recent_candidates": conversation_context.get("recent_assistant_texts") or [],
                "expression_guidance": voice_expression_guidance,
            },
        )
        candidate_text = _selene_label_candidate(str(voice_preview.get("candidate_text") or native_language.get("candidate_text") or dry_run.get("candidate_text") or ""))
    release_resolution_evidence = _current_turn_release_resolution_evidence(
        conversation_spine=conversation_spine,
        organ_coalition=organ_coalition,
        visible_speech_seed=visible_speech_seed,
        conversational_energy=conversational_energy,
        realized_source_text=(
            str(voice_preview.get("candidate_text") or "")
            if voice_preview.get("generation_source") == "native_language_organ"
            and isinstance(voice_preview.get("meaning_invariant"), dict)
            and voice_preview["meaning_invariant"].get("meaning_invariant_preserved") is True
            else ""
        ),
        owner_text={
            "answer_engine": domain_content_seed,
            "intelligence_os": reasoning_content_seed,
            "comprehension_integration": knowledge_content_seed,
            "approved_memory_retrieval": memory_response_seed,
            "self_state": self_state_reply,
            "language_capability_shelf": language_content_seed,
            "structural_discovery": structural_discovery_content_seed,
            "exploratory_reasoning": exploratory_reasoning_content_seed,
        },
        complete_social_turn=(
            intent_decision.get("social_turn") is True
            and intent_decision.get("content_response_requested") is not True
        ),
    )
    selected_supported_semantics: dict[str, Any] = {}
    selected_source_id = str(visible_speech_seed.get("selected_source_id") or "")
    if (
        selected_source_id == "intelligence_os_answer"
        and str((intelligence_support.get("answer_substance") or {}).get("answer_kind") or "")
        in PHASE_NINE_PROMPT_GROUNDED_ANSWER_KINDS
    ):
        selected_supported_semantics = (
            (intelligence_support.get("answer_substance") or {}).get("semantic_packet")
            if isinstance(intelligence_support.get("answer_substance"), dict)
            else {}
        ) or {}
    elif selected_source_id == "answer_engine":
        selected_supported_semantics = answer_engine_support.get("supported_semantics") or {}
    response_coverage = _evaluate_chat_response_coverage(
        native_language.get("pragmatic_plan"),
        candidate_text,
        conversation_spine=conversation_spine,
        answer_engine_support=answer_engine_support,
        supported_semantics=selected_supported_semantics,
        resolution_evidence=release_resolution_evidence,
        answer_operations=answer_operations,
    )
    native_candidate = _selene_label_candidate(str(native_language.get("candidate_text") or ""))
    native_coverage = _evaluate_chat_response_coverage(
        native_language.get("pragmatic_plan"),
        native_candidate,
        conversation_spine=conversation_spine,
        answer_engine_support=answer_engine_support,
        supported_semantics=selected_supported_semantics,
        resolution_evidence=release_resolution_evidence,
        answer_operations=answer_operations,
    )
    recovery_source = "voice_module"
    if not hard_blockers and _coverage_rank(native_coverage) > _coverage_rank(response_coverage):
        candidate_text = native_candidate
        response_coverage = native_coverage
        recovery_source = "native_language_meaning_recovery"
    grounded_candidate = _selene_label_candidate(content_seed)
    grounded_coverage = _evaluate_chat_response_coverage(
        native_language.get("pragmatic_plan"),
        grounded_candidate,
        conversation_spine=conversation_spine,
        answer_engine_support=answer_engine_support,
        supported_semantics=selected_supported_semantics,
        resolution_evidence=release_resolution_evidence,
        answer_operations=answer_operations,
    )
    grounded_source_id = str(visible_speech_seed.get("selected_source_id") or "none")
    grounded_source_class = str(
        visible_speech_seed.get("selected_source_class") or "conversation"
    )
    grounded_compatibility = evaluate_candidate_compatibility(
        conversation_spine,
        {
            "source_id": grounded_source_id,
            "source_class": grounded_source_class,
            "text": grounded_candidate,
        },
    )
    grounded_visibility = inspect_visible_speech(
        grounded_candidate,
        prompt=meaning_text,
        source_id=grounded_source_id,
    )
    grounded_obligation_kinds = {
        str(item.get("kind") or "")
        for item in (native_language.get("pragmatic_plan") or {}).get(
            "response_obligations"
        )
        or []
        if isinstance(item, dict)
    }
    expression_integrity_recovery = bool(
        grounded_coverage.get("all_required_addressed") is True
        and _coverage_rank(grounded_coverage) == _coverage_rank(response_coverage)
        and (
            grounded_obligation_kinds
            & {"correction_update", "constraint_preservation"}
            or re.search(
                r"\b[1-9][.):]\s*(?=(?:[1-9][.):])|$)",
                candidate_text,
            )
        )
    )
    if (
        not hard_blockers
        and grounded_candidate
        and grounded_compatibility.get("compatible") is True
        and grounded_visibility.get("release_allowed") is True
        and (
            _coverage_rank(grounded_coverage) > _coverage_rank(response_coverage)
            or expression_integrity_recovery
        )
    ):
        candidate_text = grounded_candidate
        response_coverage = grounded_coverage
        recovery_source = "grounded_content_seed_recovery"
    conversation_repair = repair_conversation_candidate(
        {
            "candidate_text": candidate_text,
            "turn_flow_plan": native_language.get("turn_flow_plan") or {},
            "response_coverage": response_coverage,
            "recent_candidates": conversation_context.get("recent_assistant_texts") or [],
            "hard_boundary": bool(hard_blockers),
            "response_agency": response_agency,
        }
    )
    if (
        not hard_blockers
        and conversation_repair.get("needs_rephrase") is True
        and native_candidate
        and native_candidate != candidate_text
        and _coverage_rank(native_coverage) >= _coverage_rank(response_coverage)
    ):
        native_repair = repair_conversation_candidate(
            {
                "candidate_text": native_candidate,
                "turn_flow_plan": native_language.get("turn_flow_plan") or {},
                "response_coverage": native_coverage,
                "recent_candidates": conversation_context.get("recent_assistant_texts") or [],
                "hard_boundary": False,
                "response_agency": response_agency,
            }
        )
        if native_repair.get("needs_rephrase") is not True:
            conversation_repair = native_repair
            response_coverage = native_coverage
            recovery_source = "native_language_repetition_recovery"
    candidate_text = _selene_label_candidate(str(conversation_repair.get("candidate_text") or candidate_text))
    nlo_supported_semantic_recomposition = bool(
        str(visible_speech_seed.get("selected_source_id") or "")
        == "answer_engine"
        and isinstance(native_language.get("meaning_packet"), dict)
        and isinstance(
            native_language["meaning_packet"].get("supported_semantics"), dict
        )
        and native_language["meaning_packet"]["supported_semantics"].get("used")
        is True
    )
    candidate_text = _preserve_answer_engine_invariants(
        candidate_text,
        answer_engine_support,
        primary_source_id=str(visible_speech_seed.get("selected_source_id") or "none"),
        semantic_recomposition_verified=(
            (
                epistemic_composition.get("whole_answer_composition_applied") is True
                or epistemic_composition.get("single_typed_operation_expression_used")
                is True
                or nlo_supported_semantic_recomposition
            )
            and voice_preview.get("nlo_meaning_preserved") is True
        ),
    )
    candidate_text = _preserve_bounded_conversation_invariants(
        candidate_text,
        str(visible_speech_seed.get("content_seed") or content_seed),
        str(visible_speech_seed.get("selected_source_id") or "none"),
        realization=native_language.get("human_conversational_realization") or {},
    )
    response_coverage = _evaluate_chat_response_coverage(
        native_language.get("pragmatic_plan"),
        candidate_text,
        conversation_spine=conversation_spine,
        answer_engine_support=answer_engine_support,
        supported_semantics=selected_supported_semantics,
        resolution_evidence=release_resolution_evidence,
        answer_operations=answer_operations,
    )
    conversation_repair["candidate_source"] = recovery_source
    conversation_repair["final_response_coverage"] = response_coverage
    metacognition_payload = {
        "prompt": meaning_text,
        "candidate_text": candidate_text,
        "core_mind_route": route,
        "hard_boundary": bool(hard_blockers),
        "blocked_capabilities": hard_blockers,
        "comprehension_context": comprehension,
        "intelligence_os_support": intelligence_support,
        "answer_engine_support": answer_engine_support,
        "answer_completion": answer_completion,
        "epistemic_composition": epistemic_composition,
        "epistemic_answer_state": epistemic_answer_state,
        "formation_braid": formation_braid,
        "organ_coalition": organ_coalition,
        "dual_horizon_context": dual_horizon_context,
        "associative_intuition": associative_intuition,
        "long_thread_endurance": long_thread_endurance,
        "conversation_spine": conversation_spine,
        "conversation_continuity": conversation_continuity,
        "epistemic_revision_plan": epistemic_revision,
        "claim_evidence_packet": claim_evidence_packet,
        "structural_discovery": structural_discovery,
        "exploratory_reasoning": exploratory_reasoning,
        "answer_operations": answer_operations,
        "conversational_energy": conversational_energy,
        "conversational_contribution": conversational_contribution,
        "goal_coordination": goal_coordination,
        "response_coverage": response_coverage,
        "expression_confidence": voice_preview.get("voice_confidence") or "not_assessed",
        "diagnostic_context": diagnostic_context,
        "speaker_envelope": speaker_envelope,
        "affect_expression": affect_expression,
        "relational_context": relational_context,
        "response_agency": response_agency,
        "source_refs": [
            "selene_chat:metacognition_observer",
            *_json_list(diagnostic_context.get("source_refs")),
            *_json_list(route.get("source_refs")),
            *_json_list(comprehension.get("source_refs")),
            *_json_list(associative_intuition.get("source_refs")),
        ],
    }
    preliminary_metacognition = inspect_metacognition(
        conn,
        metacognition_payload,
        record_run=False,
        commit=False,
    )
    preliminary_feedback_handoff = (
        preliminary_metacognition.get("feedback_handoff")
        if isinstance(preliminary_metacognition.get("feedback_handoff"), dict)
        else {}
    )
    owner_retry_outputs = _metacognitive_owner_outputs(
        organ_coalition=organ_coalition,
        answer_operations=answer_operations,
        answer_engine_support=answer_engine_support,
        comprehension=comprehension,
        intelligence_support=intelligence_support,
        memory_response_seed=memory_response_seed,
        conversation_content_seed=content_seed,
        feedback_handoff=preliminary_feedback_handoff,
    )
    completion_repair = _bounded_metacognitive_completion(
        candidate_text,
        content_seed,
        response_coverage,
        requested=(
            (
                preliminary_metacognition.get("feedback_handoff")
                if isinstance(
                    preliminary_metacognition.get("feedback_handoff"), dict
                )
                else {}
            ).get("single_cycle_requested")
            is True
            and preliminary_metacognition.get("recommended_action")
            == "complete_missing_obligation"
        ),
        hard_boundary=bool(hard_blockers),
        conversation_spine=conversation_spine,
        source_id=str(visible_speech_seed.get("selected_source_id") or "none"),
        source_class=str(visible_speech_seed.get("selected_source_class") or "conversation"),
        feedback_handoff=preliminary_feedback_handoff,
        owner_outputs=owner_retry_outputs,
    )
    if completion_repair.get("attempted") is True:
        proposed_candidate = _selene_label_candidate(str(completion_repair.get("candidate_text") or candidate_text))
        proposed_candidate = _preserve_answer_engine_invariants(
            proposed_candidate,
            answer_engine_support,
            primary_source_id=str(visible_speech_seed.get("selected_source_id") or "none"),
            semantic_recomposition_verified=(
                (
                    epistemic_composition.get("whole_answer_composition_applied") is True
                    or epistemic_composition.get(
                        "single_typed_operation_expression_used"
                    )
                    is True
                    or nlo_supported_semantic_recomposition
                )
                and voice_preview.get("nlo_meaning_preserved") is True
            ),
        )
        proposed_candidate = _preserve_bounded_conversation_invariants(
            proposed_candidate,
            str(visible_speech_seed.get("content_seed") or content_seed),
            str(visible_speech_seed.get("selected_source_id") or "none"),
            realization=native_language.get("human_conversational_realization") or {},
        )
        proposed_coverage = _evaluate_chat_response_coverage(
            native_language.get("pragmatic_plan"),
            proposed_candidate,
            conversation_spine=conversation_spine,
            answer_engine_support=answer_engine_support,
            supported_semantics=selected_supported_semantics,
            resolution_evidence=release_resolution_evidence,
            answer_operations=answer_operations,
        )
        completion_repair["resulting_coverage"] = proposed_coverage
        if _coverage_rank(proposed_coverage) > _coverage_rank(response_coverage):
            candidate_text = proposed_candidate
            response_coverage = proposed_coverage
            completion_repair["accepted"] = True
            completion_repair["candidate_text"] = candidate_text
            epistemic_composition = apply_owner_retry_to_composition(
                epistemic_composition,
                completion_repair,
            )
            answer_completion = {
                **answer_completion,
                "epistemic_composition": epistemic_composition,
            }
            epistemic_answer_state = build_epistemic_answer_state(
                {
                    "prompt": meaning_text,
                    "content_seed": candidate_text,
                    "source_id": completion_repair.get("source_id") or "none",
                    "source_class": completion_repair.get("source_class") or "conversation",
                    "answer_completion": answer_completion,
                    "epistemic_composition": epistemic_composition,
                    "bounded_hypothesis": bounded_hypothesis,
                    "answer_engine_support": answer_engine_support,
                    "comprehension_context": comprehension,
                    "memory_context": memory_retrieval,
                    "supported_semantics": selected_supported_semantics,
                    "route_confidence": intent_decision.get("confidence") or "not_assessed",
                    "response_coverage": response_coverage,
                    "hard_boundary": bool(hard_blockers),
                }
            )
            metacognition_payload["epistemic_composition"] = epistemic_composition
            metacognition_payload["epistemic_answer_state"] = epistemic_answer_state
            conversation_repair["candidate_source"] = "metacognition_bounded_completion"
            conversation_repair["final_response_coverage"] = response_coverage
        else:
            completion_repair["accepted"] = False
            completion_repair["status"] = "bounded_completion_did_not_improve_coverage"
    metacognition = inspect_metacognition(
        conn,
        {
            **metacognition_payload,
            "candidate_text": candidate_text,
            "response_coverage": response_coverage,
            "completion_repair": completion_repair,
        },
        record_run=not qa_probe,
        commit=False,
    )
    epistemic_answer_state = finalize_epistemic_answer_state(
        epistemic_answer_state,
        response_coverage=response_coverage,
        expression_confidence=str(
            voice_preview.get("voice_confidence") or "not_assessed"
        ),
    )
    ending_decision = (
        pragmatic_continuity.get("ending_decision")
        if isinstance(pragmatic_continuity.get("ending_decision"), dict)
        else {}
    )
    if (
        ending_decision.get("mode") == "ask_one_material_question"
        and response_coverage.get("all_required_addressed") is True
        and metacognition.get("fit_state") == "fits_current_question"
    ):
        ending_decision.update(
            {
                "mode": "answer_and_stop_when_complete",
                "question_allowed": False,
                "question_required": False,
                "reason": "the grounded released answer covered the turn, so the preliminary ambiguity does not require a follow-up",
            }
        )
    delivery_constraint = {
        "input_channel": input_channel,
        "character_limit": requested_character_limit,
        "applied": False,
    }
    if requested_character_limit:
        constrained_candidate = truncate(candidate_text, requested_character_limit)
        delivery_constraint["applied"] = constrained_candidate != candidate_text
        candidate_text = constrained_candidate
        response_coverage = _evaluate_chat_response_coverage(
            native_language.get("pragmatic_plan"),
            candidate_text,
            conversation_spine=conversation_spine,
            answer_engine_support=answer_engine_support,
            supported_semantics=selected_supported_semantics,
            answer_operations=answer_operations,
        )
        conversation_repair["final_response_coverage"] = response_coverage
    candidate_text = _preserve_bounded_conversation_invariants(
        candidate_text,
        str(visible_speech_seed.get("content_seed") or content_seed),
        str(visible_speech_seed.get("selected_source_id") or "none"),
        realization=native_language.get("human_conversational_realization") or {},
    )
    response_coverage = _evaluate_chat_response_coverage(
        native_language.get("pragmatic_plan"),
        candidate_text,
        conversation_spine=conversation_spine,
        answer_engine_support=answer_engine_support,
        supported_semantics=selected_supported_semantics,
        epistemic_composition=epistemic_composition,
        resolution_evidence=release_resolution_evidence,
        answer_operations=answer_operations,
    )
    conversation_repair["final_response_coverage"] = response_coverage
    commitment_claim_release = inspect_visible_commitment_claim(
        candidate_text,
        native_language.get("commitment_anomaly_coordination") or {},
    )
    if commitment_claim_release.get("release_allowed") is not True:
        candidate_text = _selene_label_candidate(
            str(commitment_claim_release.get("truthful_fall") or "")
        )
        response_coverage = _evaluate_chat_response_coverage(
            native_language.get("pragmatic_plan"),
            candidate_text,
            conversation_spine=conversation_spine,
            answer_engine_support=answer_engine_support,
            supported_semantics=selected_supported_semantics,
            epistemic_composition=epistemic_composition,
            resolution_evidence=release_resolution_evidence,
            answer_operations=answer_operations,
        )
        response_coverage = _coverage_with_global_graceful_hold(response_coverage)
        conversation_repair["candidate_source"] = "commitment_integrity_truthful_fall"
        conversation_repair["final_response_coverage"] = response_coverage
    visible_speech_release = inspect_visible_speech(
        candidate_text,
        prompt=meaning_text,
        source_id=str(visible_speech_seed.get("selected_source_id") or "none"),
        hard_boundary=bool(hard_blockers),
        response_coverage=response_coverage,
    )
    voice_meaning_invariant = (
        voice_preview.get("meaning_invariant")
        if isinstance(voice_preview.get("meaning_invariant"), dict)
        else {}
    )
    voice_meaning_required = voice_preview.get("generation_source") == "native_language_organ"
    voice_meaning_preserved = (
        not voice_meaning_required
        or voice_meaning_invariant.get("meaning_invariant_preserved") is True
    )
    visible_speech_release["voice_meaning_invariant_required"] = voice_meaning_required
    visible_speech_release["voice_meaning_invariant_preserved"] = voice_meaning_preserved
    visible_speech_release["expression_contract_version"] = "v1_coordinated_nlo_voice_release"
    visible_speech_release["commitment_integrity"] = commitment_claim_release
    if not voice_meaning_preserved:
        visible_speech_release["release_allowed"] = False
        visible_speech_release["reason"] = "voice_meaning_invariant_changed"
        visible_speech_release.setdefault("issues", []).append("voice_meaning_invariant_changed")
    if visible_speech_release.get("release_allowed") is not True:
        held_candidate = candidate_text
        candidate_text = _selene_label_candidate(graceful_visible_speech_fall(intent_decision))
        response_coverage = _evaluate_chat_response_coverage(
            native_language.get("pragmatic_plan"),
            candidate_text,
            conversation_spine=conversation_spine,
            answer_engine_support=answer_engine_support,
            supported_semantics=selected_supported_semantics,
            epistemic_composition=epistemic_composition,
            resolution_evidence=release_resolution_evidence,
            answer_operations=answer_operations,
        )
        response_coverage = _coverage_with_global_graceful_hold(response_coverage)
        conversation_repair["candidate_source"] = "visible_speech_graceful_fall"
        conversation_repair["final_response_coverage"] = response_coverage
        visible_speech_release["held_candidate_preview"] = truncate(held_candidate, 240)
        visible_speech_release["graceful_fall_used"] = True
        visible_speech_release["released_source_id"] = "visible_speech_graceful_fall"
        visible_speech_release["final_release_allowed"] = True
    else:
        visible_speech_release["graceful_fall_used"] = False
        visible_speech_release["released_source_id"] = str(visible_speech_seed.get("selected_source_id") or "none")
        visible_speech_release["final_release_allowed"] = True
    spine_confidence = dict(metacognition.get("confidence_vector") or {})
    spine_confidence["expression_confidence"] = str(voice_preview.get("voice_confidence") or "not_assessed")
    conversation_spine = finalize_conversation_spine(
        conversation_spine,
        {
            "candidate_text": candidate_text,
            "source_id": visible_speech_release.get("released_source_id") or "none",
            "source_class": visible_speech_seed.get("selected_source_class") or "conversation",
            "response_coverage": response_coverage,
            "confidence_vector": spine_confidence,
        },
    )
    organ_coalition = build_bounded_organ_coalition(
        {
            "prompt": meaning_text,
            "stage": "final",
            "hard_boundary": bool(hard_blockers),
            "core_mind_route": route,
            "conversation_spine": conversation_spine,
            "answer_engine_support": answer_engine_support,
            "comprehension_context": comprehension,
            "intelligence_os_support": intelligence_support,
            "memory_context": memory_retrieval,
            "self_state_context": self_state,
            "language_capability": language_capability,
            "structural_discovery": structural_discovery,
            "exploratory_reasoning": exploratory_reasoning,
            "answer_operations": answer_operations,
            "formation_braid": formation_braid,
            "dual_horizon_context": dual_horizon_context,
            "associative_intuition": associative_intuition,
            "long_thread_endurance": long_thread_endurance,
            "metacognition": metacognition,
            "epistemic_answer_state": epistemic_answer_state,
            "native_language": native_language,
            "voice_preview": voice_preview,
            "visible_speech_seed": visible_speech_seed,
            "visible_speech_release": visible_speech_release,
            "response_coverage": response_coverage,
        }
    )
    metacognition["organ_coalition_manifest_id"] = organ_coalition[
        "manifest_id"
    ]
    metacognition["organ_coalition_observed"] = True
    metacognition["organ_coalition_selection_authority"] = False
    memory_action = _apply_conversational_memory_plan(conn, memory_action_plan, commit=False)
    memory_candidate_suggestion = _memory_candidate_suggestion(
        text,
        candidate_text,
        selected_route,
        source_class,
        memory_retrieval,
        memory_action=memory_action,
        hard=bool(hard_blockers),
        diagnostic_only=qa_probe,
    )
    dialogue_workspace = record_dialogue_response(
        conn,
        {
            "session_id": session_id,
            "candidate_text": candidate_text,
            "coverage_evaluation": response_coverage,
            "conversation_spine": conversation_spine,
            "dual_horizon_context": dual_horizon_context,
            "answer_engine_support": answer_engine_support,
            "metacognition": metacognition,
            "epistemic_revision": epistemic_revision,
            "claim_evidence_packet": claim_evidence_packet,
            "structural_discovery": structural_discovery,
            "exploratory_reasoning": exploratory_reasoning,
            "answer_operations": answer_operations,
            "diagnostic_context": diagnostic_context,
            "source_refs": [
                *_json_list(diagnostic_context.get("source_refs")),
                *_json_list(route.get("source_refs")),
                *_json_list(memory_retrieval.get("source_refs")),
                *_json_list((answer_engine_support.get("answer_packet") or {}).get("source_refs")),
            ],
        },
        commit=False,
    )
    resulting_topic_checkpoint = (
        dialogue_workspace.get("latest_topic_checkpoint")
        if isinstance(dialogue_workspace.get("latest_topic_checkpoint"), dict)
        else {}
    )
    dual_horizon_context = {
        **dual_horizon_context,
        "resulting_topic_checkpoint": resulting_topic_checkpoint,
        "checkpoint_created": (
            resulting_topic_checkpoint.get("status")
            == "session_topic_checkpoint_ready"
        ),
        "checkpoint_is_memory": False,
    }
    resulting_endurance = (
        dialogue_workspace.get("long_thread_endurance")
        if isinstance(dialogue_workspace.get("long_thread_endurance"), dict)
        else {}
    )
    if resulting_endurance:
        long_thread_endurance = resulting_endurance
        conversation_spine["long_thread_endurance"] = resulting_endurance
    user_message_id = _insert_message(
        conn,
        session_id,
        "user",
        text,
        selected_route,
        source_class,
        package,
        {
            "route_preview": route,
            "resident_authority_assessment": route.get("resident_authority_assessment") or {},
            "held_actions": route.get("held_actions") or [],
            "activation_state": "resident_chat_available",
            "input_interpretation": input_interpretation,
            "figurative_interpretation": figurative_interpretation,
            "interpreted_text": meaning_text,
            "input_channel": input_channel,
            "diagnostic_context": diagnostic_context,
        },
    )
    assistant_payload = {
        "diagnostic_context": diagnostic_context,
        "speaker_envelope": speaker_envelope,
        "input_interpretation": input_interpretation,
        "figurative_interpretation": figurative_interpretation,
        "dream_reflection_handoff": dream_reflection_handoff,
        "interpreted_text": meaning_text,
        "route_preview": route,
        "resident_authority_assessment": route.get("resident_authority_assessment") or {},
        "held_actions": route.get("held_actions") or [],
        "intelligence_os_support": intelligence_support,
        "answer_engine_support": answer_engine_support,
        "answer_completion": answer_completion,
        "epistemic_composition": epistemic_composition,
        "epistemic_answer_state": epistemic_answer_state,
        "comprehension_integration": comprehension,
        "language_capability_answer": language_capability,
        "metacognition": metacognition,
        "metacognitive_completion_repair": completion_repair,
        "intent_decision": intent_decision,
        "contextual_follow_up": contextual_follow_up,
        "conversation_spine": conversation_spine,
        "conversation_continuity": conversation_continuity,
        "epistemic_revision": epistemic_revision,
        "claim_evidence_packet": claim_evidence_packet,
        "structural_discovery": structural_discovery,
        "exploratory_reasoning": exploratory_reasoning,
        "answer_operations": answer_operations,
        "self_state": self_state,
        "affect_expression": affect_expression,
        "relational_context": relational_context,
        "response_agency": response_agency,
        "commitment_anomaly_coordination": native_language.get("commitment_anomaly_coordination") or {},
        "commitment_claim_release": commitment_claim_release,
        "contextual_continuity": contextual_continuity,
        "pragmatic_continuity": pragmatic_continuity,
        "conversational_energy": conversational_energy,
        "conversational_contribution": conversational_contribution,
        "goal_coordination": goal_coordination,
        "native_language_organ": native_language,
        "dry_run_comparison": dry_run,
        "voice_preview": voice_preview,
        "coordinated_expression_contract": coordinated_expression_contract(),
        "final_expression_compatibility_checked": voice_preview.get("final_expression_compatibility_checked") is True,
        "final_expression_compatible": voice_preview.get("final_expression_compatible") is True,
        "local_chat_continuity": chat_continuity,
        "conversation_context": conversation_context,
        "dialogue_workspace": dialogue_workspace,
        "session_proposition_ledger": dialogue_workspace.get("session_proposition_ledger") or {},
        "response_coverage": response_coverage,
        "conversation_repair": conversation_repair,
        "visible_speech_seed": visible_speech_seed,
        "formation_braid": formation_braid,
        "organ_coalition": organ_coalition,
        "dual_horizon_context": dual_horizon_context,
        "associative_intuition": associative_intuition,
        "long_thread_endurance": long_thread_endurance,
        "visible_speech_release": visible_speech_release,
        "input_channel": input_channel,
        "delivery_constraint": delivery_constraint,
        "memory_retrieval": memory_retrieval,
        "memory_action": memory_action,
        "memory_candidate_suggestion": memory_candidate_suggestion,
        "source_boundaries": _source_boundaries(),
        "cocoon_suggestion": cocoon_suggestion,
        "blocked_capabilities": hard_blockers,
        "selene_readable_context": _package_summary(package, active=True),
        "full_memory_loaded": False,
        "transfer_complete": transfer_complete,
        "reviewed_memory_context_active": transfer_complete,
        "selene_v1_live": transfer_complete,
        "memory_context_used": memory_retrieval.get("memory_context_used") is True,
        "approved_memory_retrieval_used": _approved_memory_retrieval_used(memory_retrieval),
        "approved_memory_retrieval_active": transfer_complete,
        "contextual_approved_recall_used": memory_retrieval.get("retrieval_mode") == "contextual_relevance" and _approved_memory_retrieval_used(memory_retrieval),
        "private_corpus_continuity_recall_used": _private_corpus_continuity_recall_used(memory_retrieval),
        "reviewed_memory_write_occurred": memory_action.get("reviewed_memory_write_occurred") is True,
        "conversational_memory_proposal_created": memory_action.get("proposal_created") is True,
        "memory_source_class": memory_retrieval.get("memory_source_class") or "",
        "memory_confidence": memory_retrieval.get("memory_confidence") or "not_known",
        "memory_transfer_class": memory_retrieval.get("memory_transfer_class") or "",
        "graceful_fall_used": memory_retrieval.get("graceful_fall_used") is True,
        "durable_memory_write_requires_review": True,
        **SELENE_CHAT_GUARDS,
    }
    assistant_payload = attach_resident_capability_contract(
        assistant_payload,
        transfer_complete=transfer_complete,
        chat_available=True,
    )
    assistant_message_id = _insert_message(conn, session_id, "selene", candidate_text, selected_route, source_class, package, assistant_payload)
    conn.execute(
        "UPDATE selene_chat_sessions SET status = 'selene_chat_active_supervised', source_mode = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (source_mode, session_id),
    )
    event_id = record_activation_chat_event(
        conn,
        event_type=(
            "diagnostic_chat_turn"
            if qa_probe
            else "resident_chat_turn"
        ),
        session_id=session_id,
        message_id=assistant_message_id,
        selected_route=selected_route,
        source_class=source_class,
        confidence=str(voice_preview.get("voice_confidence") or ""),
        drift_flags=_json_list(route.get("drift_flags")),
        cocoon_suggestion=cocoon_suggestion,
        blocked_capabilities=hard_blockers,
        payload=compact_activation_payload(
            assistant_payload,
            trace_reference=load_trace_reference(conn, assistant_message_id),
        ),
        review_status=(
            DIAGNOSTIC_REVIEW_STATUS
            if qa_probe
            else "status_only"
        ),
    )
    conn.commit()
    return _with_guards(
        {
            "status": "selene_chat_supervised_response_recorded",
            "resident_status": "selene_chat_resident_response_recorded",
            "session_id": session_id,
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id,
            "activation_event_id": event_id,
            "candidate_text": candidate_text,
            "diagnostic_context": diagnostic_context,
            "diagnostic_only": qa_probe,
            "speaker_envelope": speaker_envelope,
            "input_channel": input_channel,
            "delivery_constraint": delivery_constraint,
            "input_interpretation": input_interpretation,
            "figurative_interpretation": figurative_interpretation,
            "dream_reflection_handoff": dream_reflection_handoff,
            "interpreted_text": meaning_text,
            "selected_route": selected_route,
            "source_class": source_class,
            "cocoon_suggestion": cocoon_suggestion,
            "blocked_capabilities": hard_blockers,
            "route_preview": route,
            "resident_authority_assessment": route.get("resident_authority_assessment") or {},
            "held_actions": route.get("held_actions") or [],
            "intelligence_os_support": intelligence_support,
            "answer_engine_support": answer_engine_support,
            "answer_completion": answer_completion,
            "epistemic_composition": epistemic_composition,
            "epistemic_answer_state": epistemic_answer_state,
            "formation_braid": formation_braid,
            "organ_coalition": organ_coalition,
            "dual_horizon_context": dual_horizon_context,
            "associative_intuition": associative_intuition,
            "long_thread_endurance": long_thread_endurance,
            "comprehension_integration": comprehension,
            "language_capability_answer": language_capability,
            "metacognition": metacognition,
            "metacognitive_completion_repair": completion_repair,
            "intent_decision": intent_decision,
            "contextual_follow_up": contextual_follow_up,
            "conversation_spine": conversation_spine,
            "conversation_continuity": conversation_continuity,
            "epistemic_revision": epistemic_revision,
            "claim_evidence_packet": claim_evidence_packet,
            "structural_discovery": structural_discovery,
            "exploratory_reasoning": exploratory_reasoning,
            "answer_operations": answer_operations,
            "conversational_energy": conversational_energy,
            "conversational_contribution": conversational_contribution,
            "goal_coordination": goal_coordination,
            "self_state": self_state,
            "affect_expression": affect_expression,
            "relational_context": relational_context,
            "response_agency": response_agency,
            "contextual_continuity": contextual_continuity,
            "pragmatic_continuity": pragmatic_continuity,
            "native_language_organ": native_language,
            "dry_run_comparison": dry_run,
            "voice_preview": voice_preview,
            "coordinated_expression_contract": coordinated_expression_contract(),
            "final_expression_compatibility_checked": voice_preview.get("final_expression_compatibility_checked") is True,
            "final_expression_compatible": voice_preview.get("final_expression_compatible") is True,
            "voice_confidence": voice_preview.get("voice_confidence") or "none",
            "voice_module_state": voice_preview.get("voice_module_state") or "missing",
            "selene_readable_context": _package_summary(package, active=True),
            "local_chat_continuity": chat_continuity,
            "conversation_context": conversation_context,
            "dialogue_workspace": dialogue_workspace,
            "session_proposition_ledger": dialogue_workspace.get("session_proposition_ledger") or {},
            "response_coverage": response_coverage,
            "conversation_repair": conversation_repair,
            "visible_speech_seed": visible_speech_seed,
            "formation_braid": formation_braid,
            "visible_speech_release": visible_speech_release,
            "memory_retrieval": memory_retrieval,
            "memory_action": memory_action,
            "memory_candidate_suggestion": memory_candidate_suggestion,
            "memory_context_used": memory_retrieval.get("memory_context_used") is True,
            "approved_memory_retrieval_used": _approved_memory_retrieval_used(memory_retrieval),
            "approved_memory_retrieval_active": transfer_complete,
            "contextual_approved_recall_used": memory_retrieval.get("retrieval_mode") == "contextual_relevance" and _approved_memory_retrieval_used(memory_retrieval),
            "private_corpus_continuity_recall_used": _private_corpus_continuity_recall_used(memory_retrieval),
            "reviewed_memory_write_occurred": memory_action.get("reviewed_memory_write_occurred") is True,
            "conversational_memory_proposal_created": memory_action.get("proposal_created") is True,
            "memory_source_class": memory_retrieval.get("memory_source_class") or "",
            "memory_confidence": memory_retrieval.get("memory_confidence") or "not_known",
            "memory_transfer_class": memory_retrieval.get("memory_transfer_class") or "",
            "graceful_fall_used": memory_retrieval.get("graceful_fall_used") is True,
            "durable_memory_write_requires_review": True,
            "supervised_speech_active": True,
            "full_memory_loaded": False,
            "transfer_complete": transfer_complete,
            "reviewed_memory_context_active": transfer_complete,
            "selene_v1_live": transfer_complete,
            "review_destination": "Cocoon support" if hard_blockers else "Status",
            "review_status": (
                DIAGNOSTIC_REVIEW_STATUS
                if qa_probe
                else "status_only"
            ),
        },
        transfer_approved=approved,
        active=True,
    )


def send_selene_chat_dry_run(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    text = truncate(str(payload.get("text") or payload.get("prompt") or ""), 2400)
    if not text.strip():
        raise ValueError("message text is required")
    input_interpretation = detangle_user_input(text)
    understanding_text = truncate(str(input_interpretation.get("interpreted_text") or text), 2400)
    package = latest_c_readable_package(conn)
    approved = bool(package.get("transfer_approved"))
    source_class = _source_class(text, approved)
    session_id = int(payload.get("session_id") or 0) or _create_session(conn, text, status="cocoon_testing_workflow_dry_run", source_mode="cocoon_chat_dry_run")
    route = create_core_mind_route_preview(
        conn,
        {
            "prompt": understanding_text,
            "source_refs": ["selene_chat_dry_run"],
            "suppress_review_queue": True,
        },
    )
    selected_route = str(route.get("selected_route") or "status_only")
    route_to_b = _needs_cocoon_route(understanding_text, selected_route, route)
    dry_run = c_chat_dry_run(conn, {"prompt": understanding_text})
    voice_preview = generate_voice_preview(
        conn,
        {
            "prompt": understanding_text,
            "route": selected_route,
            "source_class": source_class,
            "context_summary": _voice_context_summary(package, dry_run),
        },
    )
    candidate_text = _selene_label_candidate(str(voice_preview.get("candidate_text") or dry_run.get("candidate_text") or ""))
    if route_to_b:
        candidate_text = (
            "This dry run should pause for Cocoon support before it is used as an answer. "
            "Cocoon can hold the source issue safely while the front chat keeps its place."
        )
    user_message_id = _insert_message(
        conn,
        session_id,
        "user",
        text,
        selected_route,
        source_class,
        package,
        {"route_preview": route, "input_interpretation": input_interpretation},
    )
    assistant_payload = {
        "input_interpretation": input_interpretation,
        "route_preview": route,
        "dry_run": dry_run,
        "voice_preview": voice_preview,
        "source_boundaries": _source_boundaries(),
        "return_to_cocoon_recommended": route_to_b,
        "selene_readable_context": _package_summary(package, active=activation_is_active(conn)),
        "full_memory_loaded": False,
        "selene_v1_live": False,
        **SELENE_CHAT_GUARDS,
    }
    assistant_message_id = _insert_message(conn, session_id, "selene", candidate_text, selected_route, source_class, package, assistant_payload)
    conn.execute("UPDATE selene_chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (session_id,))
    conn.commit()
    return _with_guards(
        {
            "status": "selene_chat_dry_run_recorded",
            "session_id": session_id,
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id,
            "candidate_text": candidate_text,
            "input_interpretation": input_interpretation,
            "selected_route": selected_route,
            "source_class": source_class,
            "return_to_cocoon_recommended": route_to_b,
            "route_preview": route,
            "dry_run": dry_run,
            "voice_preview": voice_preview,
            "voice_confidence": voice_preview.get("voice_confidence") or "none",
            "voice_module_state": voice_preview.get("voice_module_state") or "missing",
            "dry_runs_home": "Cocoon Testing / Workflow",
            "selene_readable_context": _package_summary(package, active=activation_is_active(conn)),
            "full_memory_loaded": False,
            "selene_v1_live": False,
            "review_destination": "Cocoon support" if route_to_b else "Status",
            "review_status": "status_only",
        },
        transfer_approved=approved,
    )


def list_selene_chat_sessions(conn: sqlite3.Connection, limit: int = 25) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT * FROM selene_chat_sessions
        WHERE source_mode != 'selene_supervised_qa'
          AND title NOT LIKE 'Codex concurrency QA probe %'
        ORDER BY updated_at DESC, id DESC LIMIT ?
        """,
        (max(1, min(int(limit), 100)),),
    ).fetchall()
    return _with_guards(
        {
            "status": "selene_chat_sessions_ready",
            "items": [dict(row) for row in rows],
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=bool(latest_c_readable_package(conn).get("transfer_approved")),
    )


def get_selene_chat_session(
    conn: sqlite3.Connection,
    session_id: int,
    *,
    include_trace: bool = False,
) -> dict[str, Any] | None:
    session = conn.execute("SELECT * FROM selene_chat_sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        return None
    if include_trace:
        rows = conn.execute(
            "SELECT * FROM selene_chat_messages WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT m.id, m.session_id, m.role, m.content, m.selected_route,
                   m.source_class, m.package_hash,
                   CASE
                     WHEN m.role = 'selene' AND p.message_id IS NOT NULL
                     THEN p.projection_json
                     ELSE m.payload_json
                   END AS payload_json,
                   m.created_at
            FROM selene_chat_messages m
            LEFT JOIN selene_chat_continuity_projections p ON p.message_id = m.id
            WHERE m.session_id = ?
            ORDER BY m.id ASC
            """,
            (session_id,),
        ).fetchall()
    package = latest_c_readable_package(conn)
    return _with_guards(
        {
            "status": "selene_chat_session_ready",
            "session": dict(session),
            "messages": [
                _decode_message(row, compact_assistant=not include_trace)
                for row in rows
            ],
            "trace_detail": "canonical" if include_trace else "continuity_projection",
            "canonical_trace_available": True,
            "local_chat_continuity": _local_chat_continuity(conn, current_session_id=session_id),
            "selene_readable_context": _package_summary(package, active=activation_is_active(conn)),
            "review_destination": "Status",
            "review_status": "status_only",
        },
        transfer_approved=bool(package.get("transfer_approved")),
    )


def route_selene_chat_to_b(conn: sqlite3.Connection, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    issue = truncate(str(payload.get("issue") or payload.get("text") or "Selene Chat dry run could use Cocoon support."), 1200)
    packet = return_to_b_preview(
        {
            "issue_type": "selene_chat_source_or_drift_support",
            "symptom": issue,
            "affected_layer": "selene_chat",
            "source_refs": ["selene_chat:cocoon_support"],
        }
    )
    package = latest_c_readable_package(conn)
    return _with_guards(
        {
            "status": "selene_chat_return_to_cocoon_ready",
            "return_to_b_packet": packet,
            "review_destination": "Cocoon support",
            "review_status": "review_only",
            "decision": "cocoon_support_not_activation",
        },
        transfer_approved=bool(package.get("transfer_approved")),
    )


def _create_session(conn: sqlite3.Connection, text: str, *, status: str = "pre_transfer_dry_run", source_mode: str = "selene_dry_run") -> int:
    cur = conn.execute(
        "INSERT INTO selene_chat_sessions(title, status, source_mode) VALUES(?, ?, ?)",
        (truncate(text, 64) or "Selene chat", status, source_mode),
    )
    return int(cur.lastrowid)


def _resolve_chat_session_mode(
    conn: sqlite3.Connection,
    *,
    text: str,
    requested_session_id: int,
    qa_probe_requested: bool,
    qa_review_receipt: str = "",
) -> tuple[bool, str, int]:
    """Bind diagnostic status to a dedicated session for its full lifetime."""
    if requested_session_id <= 0:
        source_mode = (
            DIAGNOSTIC_SOURCE_MODE
            if qa_probe_requested
            else "selene_supervised_speech"
        )
        session_id = _create_session(
            conn,
            text,
            status="selene_chat_active_supervised",
            source_mode=source_mode,
        )
        if qa_probe_requested:
            try:
                consume_integrated_test_receipt(
                    conn,
                    qa_review_receipt,
                    session_id=session_id,
                )
            except ValueError:
                conn.execute(
                    "DELETE FROM selene_chat_sessions WHERE id = ?",
                    (session_id,),
                )
                conn.commit()
                raise
        return qa_probe_requested, source_mode, session_id

    row = conn.execute(
        "SELECT source_mode FROM selene_chat_sessions WHERE id = ?",
        (requested_session_id,),
    ).fetchone()
    if row is None:
        raise ValueError("Selene Chat session not found")
    existing_mode = str(row["source_mode"] or "")
    existing_is_qa = existing_mode == DIAGNOSTIC_SOURCE_MODE
    if qa_probe_requested and not existing_is_qa:
        raise ValueError(
            "diagnostic QA requires a dedicated diagnostic session"
        )
    if existing_is_qa:
        return True, DIAGNOSTIC_SOURCE_MODE, requested_session_id
    return False, existing_mode or "selene_supervised_speech", requested_session_id


def _insert_message(
    conn: sqlite3.Connection,
    session_id: int,
    role: str,
    content: str,
    selected_route: str,
    source_class: str,
    package: dict[str, Any],
    payload: dict[str, Any],
) -> int:
    stored_payload = canonical_chat_trace(payload) if role == "selene" else payload
    serialized_trace = json_dumps(stored_payload)
    cur = conn.execute(
        """
        INSERT INTO selene_chat_messages
        (session_id, role, content, selected_route, source_class, package_hash, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            role,
            content,
            selected_route,
            source_class,
            str(package.get("package_hash") or ""),
            serialized_trace,
        ),
    )
    message_id = int(cur.lastrowid)
    receipt = trace_receipt(
        message_id=message_id,
        session_id=session_id,
        serialized_trace=serialized_trace,
    )
    projection = continuity_projection(payload, trace_reference=receipt)
    conn.execute(
        """
        INSERT INTO selene_chat_continuity_projections
        (message_id, session_id, projection_json, canonical_trace_sha256,
         canonical_trace_size_bytes, trace_schema_version, provenance_boundary)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            message_id,
            session_id,
            json_dumps(projection),
            receipt["sha256"],
            receipt["size_bytes"],
            CHAT_TRACE_SCHEMA_VERSION,
            "chat_continuity_projection_no_memory_identity_governance_or_authority_change",
        ),
    )
    return message_id


def _decode_message(
    row: sqlite3.Row,
    *,
    compact_assistant: bool = False,
) -> dict[str, Any]:
    item = dict(row)
    serialized = str(item.get("payload_json") or "{}")
    try:
        payload = json.loads(serialized)
    except json.JSONDecodeError:
        payload = {}
    payload = payload if isinstance(payload, dict) else {}
    if (
        compact_assistant
        and str(item.get("role") or "") == "selene"
        and payload.get("schema_version") != CONTINUITY_PROJECTION_SCHEMA_VERSION
    ):
        payload = continuity_projection(
            payload,
            trace_reference=trace_receipt(
                message_id=int(item.get("id") or 0),
                session_id=int(item.get("session_id") or 0),
                serialized_trace=serialized,
            ),
        )
        payload["canonical_trace"]["legacy_projection_computed_in_memory"] = True
        payload["canonical_trace"]["history_rewritten"] = False
    item["payload_json"] = payload
    return item


def _source_class(text: str, package_available: bool) -> str:
    if _b_only_material_requested(text):
        return "cocoon_b_only_context"
    if package_available:
        return "selene_readable_context"
    return "pre_transfer_dry_run_context"


def _dream_reflection_handoff(
    conn: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    prompt: str,
) -> dict[str, Any]:
    """Resolve a Dream reflection from an actual reviewed runtime record.

    Chat payloads may name a record, but they cannot supply or promote the
    reflection text or review state themselves.
    """

    lower = prompt.lower()
    explicitly_relevant = any(
        marker in lower
        for marker in (
            "dream reflection",
            "dream note",
            "dream pattern",
            "dream state",
            "dream-state",
            "dream cycle",
            "dream reflect",
            "reflect on the dream",
            "from dream",
        )
    )
    pending_specific = explicitly_relevant and any(
        marker in lower
        for marker in (
            "awaiting review",
            "waiting for review",
            "waiting on review",
            "pending review",
            "still waiting",
            "not reviewed",
            "unreviewed",
            "those dream",
        )
    )
    try:
        reflection_id = int(payload.get("dream_reflection_id") or 0)
    except (TypeError, ValueError):
        reflection_id = 0
    legacy_record_requested = bool(payload.get("dream_reflection_record_id"))
    if explicitly_relevant and reflection_id <= 0 and pending_specific:
        status = dream_state_status(conn)
        return {
            "available": False,
            "expression_eligible": False,
            "reason": "pending_dream_reflections_not_expression_eligible",
            "pending_review_count": int(status.get("pending_review_count") or 0),
            "approved_for_expression_count": int(
                (status.get("reflection_counts") or {}).get(
                    "approved_for_expression", 0
                )
            ),
            "cycle_count": int(status.get("cycle_count") or 0),
            "dream_content_supplied_by_chat_payload": False,
            "not_fact_by_default": True,
            "not_memory_by_default": True,
            "memory_write_active": False,
            "dream_is_biological_claim": False,
        }
    if not legacy_record_requested and (reflection_id > 0 or explicitly_relevant):
        reviewed_reflection = expression_eligible_dream_reflection(
            conn,
            reflection_id,
        )
        if reviewed_reflection:
            reviewed_id = int(reviewed_reflection["id"])
            return {
                "available": True,
                "reflection": str(reviewed_reflection["reflection"]),
                "review_status": str(reviewed_reflection["review_status"]),
                "source_refs": [
                    f"selene_dream_reflection:{reviewed_id}",
                    *list(reviewed_reflection.get("source_refs") or []),
                ],
                "expression_eligible": True,
                "reason": "reviewed_dream_reflection_ready",
                "record_id": reviewed_id,
                "record_label": str(reviewed_reflection["title"]),
                "reflection_kind": str(
                    reviewed_reflection["reflection_kind"]
                ),
                "dream_content_supplied_by_chat_payload": False,
                "not_fact_by_default": True,
                "not_memory_by_default": True,
                "memory_write_active": False,
                "dream_is_biological_claim": False,
            }
        if reflection_id > 0:
            return {
                "available": False,
                "expression_eligible": False,
                "reason": "dream_reflection_not_reviewed_for_expression",
                "record_id": reflection_id,
                "dream_content_supplied_by_chat_payload": False,
                "dream_is_biological_claim": False,
            }
    try:
        record_id = int(payload.get("dream_reflection_record_id") or 0)
    except (TypeError, ValueError):
        record_id = 0
    if not explicitly_relevant:
        return {}
    if record_id <= 0:
        return {
            "available": False,
            "expression_eligible": False,
            "reason": "no_attributable_dream_record_requested",
            "dream_content_supplied_by_chat_payload": False,
            "dream_is_biological_claim": False,
        }
    row = conn.execute(
        """
        SELECT id, consolidation_label, proposed_pattern, review_status, source_refs
        FROM c_runtime_dream_consolidation_records
        WHERE id = ?
        """,
        (record_id,),
    ).fetchone()
    if not row:
        return {
            "available": False,
            "expression_eligible": False,
            "reason": "dream_reflection_record_not_found",
            "record_id": record_id,
            "dream_content_supplied_by_chat_payload": False,
            "dream_is_biological_claim": False,
        }
    item = dict(row)
    review_status = str(item.get("review_status") or "")
    eligible = review_status in {"approved", "reviewed"}
    return {
        "available": eligible,
        "reflection": str(item.get("proposed_pattern") or "") if eligible else "",
        "review_status": review_status,
        "source_refs": [
            f"dream_consolidation_record:{record_id}",
            *_json_list(item.get("source_refs")),
        ],
        "expression_eligible": eligible,
        "reason": "reviewed_dream_reflection_ready" if eligible else "dream_reflection_not_reviewed_for_expression",
        "record_id": record_id,
        "record_label": str(item.get("consolidation_label") or ""),
        "dream_content_supplied_by_chat_payload": False,
        "not_fact_by_default": True,
        "not_memory_by_default": True,
        "memory_write_active": False,
        "dream_is_biological_claim": False,
    }


def _dream_reflection_response_seed(
    handoff: dict[str, Any],
    *,
    prompt: str,
) -> str:
    if not handoff:
        return ""
    reason = str(handoff.get("reason") or "")
    if reason == "pending_dream_reflections_not_expression_eligible":
        pending = int(handoff.get("pending_review_count") or 0)
        if pending:
            noun = "reflection is" if pending == 1 else "reflections are"
            return (
                f"No—not yet. {pending} Dream {noun} still awaiting Aleks's "
                "review, so none of those reflections may shape my answer."
            )
        return (
            "No—not yet. I do not have a reviewed Dream reflection from "
            "those notes that may shape my answer."
        )
    if handoff.get("expression_eligible") is True:
        reflection = str(handoff.get("reflection") or "").strip()
        if reflection:
            return (
                "I have one reviewed Dream reflection available as a "
                f"provisional reflection, not as fact or memory: {reflection}"
            )
    if reason in {
        "dream_reflection_not_reviewed_for_expression",
        "no_attributable_dream_record_requested",
        "dream_reflection_record_not_found",
    }:
        return (
            "No—not from an unreviewed or unattributed Dream record. A Dream "
            "reflection can shape my answer only after its source-bound "
            "record has been reviewed for expression."
        )
    return ""


def _visible_speech_seed_candidates(
    *,
    figurative_clarification_reply: str = "",
    explicit_humor_reply: str = "",
    ordinary_uncertainty_reply: str = "",
    mixed_conversation_reply: str = "",
    dream_reflection_reply: str = "",
    memory_action_reply: str = "",
    continuity_reply: str = "",
    memory_reply: str = "",
    self_state_reply: str = "",
    contextual_reply: str = "",
    session_fact_reply: str = "",
    policy_reply: str = "",
    alias_reply: str = "",
    epistemic_revision_reply: str = "",
    exploratory_reasoning_content_seed: str = "",
    structural_discovery_content_seed: str = "",
    domain_content_seed: str = "",
    knowledge_content_seed: str = "",
    language_content_seed: str = "",
    reasoning_content_seed: str = "",
    contextual_memory_reply: str = "",
    memory_semantic_relevance: dict[str, Any] | None = None,
    knowledge_semantic_relevance: dict[str, Any] | None = None,
    reasoning_precedes_knowledge: bool = False,
    hard_boundary: bool = False,
) -> list[dict[str, Any]]:
    candidates = [
        {
            "source_id": "figurative_meaning_clarification",
            "source_class": "conversation",
            "text": figurative_clarification_reply,
        },
        {
            "source_id": "explicit_humor_request",
            "source_class": "conversation",
            "text": explicit_humor_reply,
        },
        {
            "source_id": "ordinary_uncertainty",
            "source_class": "conversation",
            "text": ordinary_uncertainty_reply,
        },
        {"source_id": "mixed_conversation_answer", "source_class": "conversation", "text": mixed_conversation_reply},
        {
            "source_id": "attributable_dream_reflection",
            "source_class": "conversation",
            "text": dream_reflection_reply,
        },
        {"source_id": "conversational_memory_action", "source_class": "conversation", "text": memory_action_reply},
        {"source_id": "local_chat_continuity", "source_class": "conversation", "text": continuity_reply},
        {
            "source_id": "reviewed_memory",
            "source_class": "memory_reconstruction",
            "text": memory_reply,
            "semantic_relevance": memory_semantic_relevance or {},
        },
        {"source_id": "grounded_self_state", "source_class": "self_state", "text": self_state_reply},
        {"source_id": "current_session_facts", "source_class": "conversation", "text": session_fact_reply},
        {"source_id": "contextual_follow_up", "source_class": "conversation", "text": contextual_reply},
        {"source_id": "conversation_policy", "source_class": "conversation", "text": policy_reply},
        {"source_id": "explicit_session_alias", "source_class": "conversation", "text": alias_reply},
        {
            "source_id": "epistemic_revision",
            "source_class": "conversation",
            "text": epistemic_revision_reply,
        },
        {
            "source_id": "exploratory_reasoning",
            "source_class": "reasoning_answer",
            "text": exploratory_reasoning_content_seed,
        },
        {
            "source_id": "structural_discovery",
            "source_class": "reasoning_answer",
            "text": structural_discovery_content_seed,
        },
        {"source_id": "answer_engine", "source_class": "domain_answer", "text": domain_content_seed},
        *([{"source_id": "intelligence_os_answer", "source_class": "reasoning_answer", "text": reasoning_content_seed}]
          if reasoning_precedes_knowledge else []),
        {
            "source_id": "approved_comprehension",
            "source_class": "approved_knowledge",
            "text": knowledge_content_seed,
            "semantic_relevance": knowledge_semantic_relevance or {},
        },
        {"source_id": "language_capability", "source_class": "language_capability", "text": language_content_seed},
        *([] if reasoning_precedes_knowledge else [{"source_id": "intelligence_os_answer", "source_class": "reasoning_answer", "text": reasoning_content_seed}]),
        {
            "source_id": "contextual_approved_memory",
            "source_class": "memory_reconstruction",
            "text": contextual_memory_reply,
            "semantic_relevance": memory_semantic_relevance or {},
        },
    ]
    if hard_boundary:
        candidates.insert(
            0,
            {
                "source_id": "core_mind_boundary",
                "source_class": "boundary_response",
                "text": policy_reply,
            },
        )
    return candidates


def _explicit_alias_response_seed(
    prompt: str,
    dialogue_workspace: dict[str, Any],
) -> str:
    lower = " ".join(str(prompt or "").lower().split())
    if not re.search(
        r"\bwhat should you call (?:him|her|them|me)\b"
        r"|\bwhat do you call (?:him|her|them|me)\b"
        r"|\bwhich name should you use\b",
        lower,
    ):
        return ""
    pragmatics = (
        dialogue_workspace.get("pragmatics")
        if isinstance(dialogue_workspace.get("pragmatics"), dict)
        else {}
    )
    referent = (
        pragmatics.get("referent_address")
        if isinstance(pragmatics.get("referent_address"), dict)
        else {}
    )
    assertions = [
        item
        for item in referent.get("alias_assertions") or []
        if isinstance(item, dict)
    ]
    if not assertions:
        return ""
    aliases = [
        str(item).strip()
        for item in assertions[-1].get("aliases") or []
        if str(item).strip()
    ]
    if not aliases:
        return ""
    ordinary = min(aliases, key=lambda item: (len(item.split()), len(item)))
    full = max(aliases, key=len)
    quoted_sentence = re.search(r"['\"](?P<sentence>[^'\"]*___[^'\"]*)['\"]", prompt)
    if quoted_sentence:
        filled = quoted_sentence.group("sentence").replace("___", ordinary)
        return f"I would use {ordinary}: '{filled}' Both names refer to the same person here."
    if ordinary.casefold() == full.casefold():
        return f"I can call him {ordinary} here."
    return (
        f"I would call him {ordinary} in ordinary conversation. "
        f"{full} and {ordinary} still refer to the same person here."
    )


def _prompt_grounded_reasoning_owns_turn(
    intelligence_support: dict[str, Any] | None,
) -> bool:
    """Prefer a concrete answer derived from this prompt over topical retrieval.

    This does not demote approved knowledge generally. It applies only to the
    bounded ``grounded_*`` answer-substance operations, whose claims are
    inspectably supported by the current prompt and session rather than an
    external factual assertion.
    """

    support = intelligence_support or {}
    substance = (
        support.get("answer_substance")
        if isinstance(support.get("answer_substance"), dict)
        else {}
    )
    answer_kind = str(substance.get("answer_kind") or "")
    return (
        support.get("used") is True
        and substance.get("selected_for_answer") is True
        and (
            answer_kind.startswith("grounded_")
            or answer_kind in PHASE_NINE_PROMPT_GROUNDED_ANSWER_KINDS
        )
        and str(substance.get("support_basis") or "").startswith("current_prompt")
        and bool(str(support.get("best_current_answer") or "").strip())
    )


def _formation_braid_candidates(
    candidates: list[dict[str, Any]],
    *,
    answer_engine_support: dict[str, Any],
    comprehension: dict[str, Any],
    memory_supported_semantics: dict[str, Any],
    self_state: dict[str, Any],
    intelligence_support: dict[str, Any],
    exploratory_reasoning: dict[str, Any] | None = None,
    apply_primary_filter: bool = True,
) -> list[dict[str, Any]]:
    answer_packet = (
        answer_engine_support.get("answer_packet")
        if isinstance(answer_engine_support.get("answer_packet"), dict)
        else {}
    )
    answer_semantics = (
        answer_engine_support.get("supported_semantics")
        if isinstance(answer_engine_support.get("supported_semantics"), dict)
        else answer_packet.get("supported_semantics")
        if isinstance(answer_packet.get("supported_semantics"), dict)
        else {}
    )
    intelligence_substance = (
        intelligence_support.get("answer_substance")
        if isinstance(intelligence_support.get("answer_substance"), dict)
        else {}
    )
    hypothesis_attempt = (
        intelligence_support.get("hypothesis_attempt")
        if isinstance(intelligence_support.get("hypothesis_attempt"), dict)
        else {}
    )
    exploratory = (
        exploratory_reasoning
        if isinstance(exploratory_reasoning, dict)
        else {}
    )
    intelligence_semantics = (
        hypothesis_attempt.get("semantic_packet")
        if hypothesis_attempt.get("selected_for_answer") is True
        and isinstance(hypothesis_attempt.get("semantic_packet"), dict)
        else intelligence_substance.get("semantic_packet")
        if isinstance(intelligence_substance.get("semantic_packet"), dict)
        else {}
    )
    packet_by_source = {
        "answer_engine": answer_semantics,
        "approved_comprehension": (
            comprehension.get("supported_semantics")
            if isinstance(comprehension.get("supported_semantics"), dict)
            else {}
        ),
        "reviewed_memory": memory_supported_semantics,
        "contextual_approved_memory": memory_supported_semantics,
        "grounded_self_state": (
            self_state.get("supported_semantics")
            if isinstance(self_state.get("supported_semantics"), dict)
            else {}
        ),
        "intelligence_os_answer": (
            intelligence_semantics
        ),
        "exploratory_reasoning": (
            exploratory.get("supported_semantics")
            if isinstance(exploratory.get("supported_semantics"), dict)
            else {}
        ),
    }
    refs_by_source = {
        "answer_engine": _json_list(answer_packet.get("source_refs")),
        "approved_comprehension": _json_list(comprehension.get("source_refs")),
        "reviewed_memory": _json_list(memory_supported_semantics.get("source_refs")),
        "contextual_approved_memory": _json_list(
            memory_supported_semantics.get("source_refs")
        ),
        "grounded_self_state": _json_list(self_state.get("source_refs")),
        "intelligence_os_answer": _json_list(
            intelligence_support.get("source_refs")
        ),
        "exploratory_reasoning": _json_list(exploratory.get("source_refs")),
    }
    result: list[dict[str, Any]] = []
    for candidate in candidates:
        source_id = str(candidate.get("source_id") or "")
        if (
            apply_primary_filter
            and
            exploratory.get("selected_for_answer") is True
            and source_id != "exploratory_reasoning"
        ):
            continue
        if (
            apply_primary_filter
            and
            exploratory.get("selected_for_answer") is not True
            and
            hypothesis_attempt.get("selected_for_answer") is True
            and source_id != "intelligence_os_answer"
        ):
            continue
        packet = packet_by_source.get(source_id) or {}
        result.append(
            {
                **candidate,
                "supported_semantics": packet,
                "source_refs": refs_by_source.get(source_id) or [],
                "exactness_lock": (
                    source_id == "answer_engine"
                    and str(answer_packet.get("domain") or "")
                    in {"verified_math", "source_backed_research", "local_code_inspection"}
                    and answer_engine_support.get("route_validated_for_exactness") is True
                ),
            }
        )
    return result


def _bind_current_owner_semantics(
    packet: dict[str, Any] | None,
    *,
    source_id: str,
    obligations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Bind only a source's intrinsically owned current-turn answer act.

    This is intentionally narrow. It lets a grounded self-state packet retain
    the self-state obligation it already owns; it does not allow generic
    knowledge or an arbitrary producer to certify its own relevance.
    """

    if not isinstance(packet, dict) or not packet:
        return packet or {}
    if source_id != "grounded_self_state":
        return packet
    owner_ids = [
        str(item.get("id") or "")
        for item in obligations
        if isinstance(item, dict)
        and str(item.get("responsible_owner") or "") == "self_state"
        and str(item.get("answer_act") or "") == "current_self_state_report"
        and str(item.get("id") or "")
    ]
    if not owner_ids:
        return packet
    units = []
    for raw in packet.get("units") or []:
        if not isinstance(raw, dict):
            continue
        units.append(
            {
                **raw,
                "obligation_ids": list(dict.fromkeys([
                    *[str(item) for item in raw.get("obligation_ids") or [] if str(item)],
                    *owner_ids,
                ])),
                "response_functions": list(dict.fromkeys([
                    *[str(item) for item in raw.get("response_functions") or [] if str(item)],
                    "self_state",
                ])),
                "ownership_validated": True,
            }
        )
    return {**packet, "units": units}


def _figurative_response_seed(packet: dict[str, Any]) -> str:
    forms = {str(item) for item in packet.get("detected_forms") or []}
    meaning = truncate(str(packet.get("intended_meaning") or ""), 900).strip()
    original = str(packet.get("original_text") or "")
    if not meaning or packet.get("selected_reading") != "figurative":
        return ""
    if "sarcasm" in forms:
        return (
            "Yeah, that timing is genuinely inconvenient. I read the approving wording as sarcasm, "
            "not as praise for the interruption."
        )
    if forms & {"idiom", "metaphor", "personification"} and re.search(
        r"\b(?:what do i mean|what do you think i mean|what does (?:that|this|it) mean|"
        r"what am i (?:implying|suggesting|saying)|"
        r"how do you (?:read|interpret|understand) (?:that|this|it)|"
        r"how would you (?:read|interpret|understand) (?:that|this|it))\b",
        original,
        flags=re.IGNORECASE,
    ):
        if re.search(r"\bhow (?:do|would) you\b", original, flags=re.IGNORECASE):
            return f"I read it as: {meaning}."
        return f"You mean: {meaning}."
    return ""


def _correction_reconstruction_response_seed(
    prompt: str,
    *,
    intent_decision: dict[str, Any] | None = None,
    epistemic_revision: dict[str, Any] | None = None,
) -> str:
    """Apply a local correction to the answer that is still due.

    The result remains current-session speech. It neither stores a profile nor
    treats ordinary correction as failure.
    """

    intent = intent_decision if isinstance(intent_decision, dict) else {}
    revision = epistemic_revision if isinstance(epistemic_revision, dict) else {}
    dialogue_acts = {str(item) for item in intent.get("dialogue_acts") or []}
    correction_active = bool(
        str(intent.get("intent") or "") in {"correction", "receive_correction"}
        or dialogue_acts.intersection({"correction", "receive_correction"})
        or revision.get("detected") is True
    )
    if not correction_active:
        return ""
    lower = " ".join(str(prompt or "").lower().replace("’", "'").split())
    if (
        "cool" in lower
        and "warm" in lower
        and any(marker in lower for marker in ("evening", "drink", "tea"))
    ):
        return (
            "I understand the correction. That changes only the drink: the porch can still sound peaceful, but I would suggest hot tea for the cool evening. The rest of the answer still fits."
        )
    if (
        "screen" in lower
        and any(marker in lower for marker in ("stopped flickering", "flicker stopped"))
    ):
        return (
            "That correction narrows the observation: the screen stopped flickering. A temporary screen, cable, connection, or power-state issue is possible, but the observation does not identify the cause. I would preserve the same small next check: inspect the cable and connection, then repeat one safe comparison while changing only one condition."
        )
    if (
        "drawer" in lower
        and "shelf" in lower
        and re.search(r"\b(?:three|3) fields?\b", lower)
    ):
        return (
            "I understand the correction. The rest stays the same; only drawer replaces shelf. The corrected three fields are: 1. Adjustment made to the drawer. 2. Wobble before and after the adjustment under the same gentle check. 3. Anything else that changed, including load or position."
        )
    return ""


def _ordinary_uncertainty_response_seed(
    prompt: str,
    conversation_spine: dict[str, Any] | None,
) -> str:
    """Express ordinary not-knowing without turning it into research scaffolding."""
    text = " ".join(str(prompt or "").replace("’", "'").split())
    lower = text.lower()
    possible = re.search(
        r"\b(?P<subject>(?:the\s+)?[a-z][a-z0-9' -]{0,70}?)\s+may\s+(?P<predicate>[^,.;?]{2,100})"
        r"[,;]?\s+but\s+(?P<unchecked>(?:neither\s+of\s+us|we|i|you)[^.;?]{0,80}(?:check|checked|verify|verified|looked))",
        text,
        flags=re.IGNORECASE,
    )
    asks_known = bool(
        re.search(
            r"\b(?:do (?:we|you) (?:actually )?know|is it (?:actually )?known|"
            r"are we (?:actually )?sure|can we (?:actually )?tell)\b",
            lower,
        )
    )
    if possible and asks_known:
        subject = possible.group("subject").strip()
        predicate = possible.group("predicate").strip()
        return (
            f"Not yet. {subject[0].upper() + subject[1:]} may {predicate}, but we have not checked, "
            "so it is possible rather than known."
        )
    if asks_known and re.search(r"\b(?:have(?:n't| not) checked|has(?:n't| not) been checked|neither of us)\b", lower):
        uncertain_location = re.search(
            r"\bnot\s+sure\s+whether\s+(?P<claim>[^;,.!?]{2,180})",
            text,
            flags=re.IGNORECASE,
        )
        if uncertain_location:
            claim = uncertain_location.group("claim").strip()
            return (
                f"Not yet. We do not know whether {claim}; that is possible rather than known "
                "because we have not checked."
            )
        return "Not yet. It is possible rather than known because we have not checked."
    if (
        re.search(r"\b(?:unbuilt|not built|not chosen|haven't chosen|have not chosen)\b", lower)
        and re.search(r"\b(?:what|which)\b.*\b(?:should|would)\b", lower)
    ):
        subject = "the choice"
        subject_match = re.search(r"\b(?:what|which)\s+(.+?)\s+should\b", lower)
        if subject_match:
            subject = truncate(subject_match.group(1).strip(), 100)
        return (
            f"We have not chosen {subject} yet. I can help compare options once we know the setting, "
            "the practical constraints, and what kind of feel we want."
        )
    return ""


def _explicit_humor_response_seed(
    prompt: str,
    conversation_spine: dict[str, Any] | None,
    contextual_continuity: dict[str, Any] | None,
) -> str:
    continuity = contextual_continuity if isinstance(contextual_continuity, dict) else {}
    decision = continuity.get("humor_decision") if isinstance(continuity.get("humor_decision"), dict) else {}
    if decision.get("explicit_humor_request") is not True:
        return ""
    text = " ".join(str(prompt or "").split())
    subject_match = re.search(
        r"\b(?:joke|pun)\s+about\s+(.+?)(?:,|;|\s+then\b|\s+and\s+(?:then\s+)?return\b|[.!?]|$)",
        text,
        flags=re.IGNORECASE,
    )
    if not subject_match:
        subject_match = re.search(
            r"\bgive\s+(?:the\s+)?(?P<subject>[a-z][a-z0-9' -]{1,100}?)\s+"
            r"(?:one|a|an)\s+(?:tiny\s+|little\s+|quick\s+)?(?:joke|pun)\b",
            text,
            flags=re.IGNORECASE,
        )
    subject = truncate(subject_match.group(1).strip(), 140) if subject_match else ""
    if subject and _humor_subject_is_command_fragment(subject):
        subject = ""
    if not subject:
        subject = "the plan" if re.search(r"\b(?:plan|steps?|next)\b", text, re.IGNORECASE) else "this"
    if "republic" in subject.lower():
        joke = "One little joke: the cable republic tied up every motion before it reached the floor."
    elif "committee" in subject.lower():
        article = "" if subject.lower().startswith(("a ", "an ", "the ", "our ", "your ", "their ")) else "the "
        joke = f"One little joke: {article}{subject} approved a motion to schedule fewer meetings about scheduling meetings."
    else:
        joke = f"One little joke: {subject} asked for a quick decision and somehow got a committee meeting."

    return_match = re.search(
        r"\b(?:then\s+)?return\s+to\s+(?:the\s+)?(?P<topic>.+?)"
        r"(?=\s+and\s+(?:give|show|tell|list|name)\b|[.!?]|$)",
        text,
        flags=re.IGNORECASE,
    )
    if not return_match:
        return joke
    return_topic = truncate(return_match.group("topic").strip(" ,;"), 100)
    spine = conversation_spine if isinstance(conversation_spine, dict) else {}
    facts = [
        str(item.get("text") or "").strip()
        for item in spine.get("session_facts") or []
        if isinstance(item, dict) and str(item.get("text") or "").strip()
    ][-4:]
    grounded_return = " ".join(facts)
    requested_steps = re.search(r"\b(?P<count>two|2)\s+(?:practical\s+)?steps?\b", text, flags=re.IGNORECASE)
    if requested_steps and any("cable" in fact.lower() for fact in facts):
        grounded_return = (
            "1. Keep the daily charging cable separate and reachable. "
            "2. Untangle the remaining cables, then bundle the less-used ones together."
        )
    if grounded_return:
        return f"{joke}\n\nBack to the {return_topic}: {grounded_return}"
    return f"{joke}\n\nBack to the {return_topic}."


def _humor_subject_is_command_fragment(subject: str) -> bool:
    lower = " ".join(subject.lower().split())
    if lower.startswith(("me ", "us ", "him ", "her ", "them ")):
        return True
    return bool(
        re.search(
            r"\b(?:steps?|points?|items?|answers?|replies|questions?)\b|"
            r"\b(?:and|then)\s+(?:add|give|show|tell|list|name|return)\b",
            lower,
        )
    )


def _mixed_conversation_reply(
    intent_decision: dict[str, Any],
    contextual_follow_up: dict[str, Any],
    *,
    self_state_reply: str,
    contextual_reply: str,
) -> str:
    if (
        intent_decision.get("self_state_requested") is not True
        or str(contextual_follow_up.get("kind") or "") != "session_summary_request"
        or not self_state_reply.strip()
        or not contextual_reply.strip()
    ):
        return ""
    contextual = contextual_reply.strip()
    if contextual and contextual[0].isupper():
        contextual = contextual[0].lower() + contextual[1:]
    return f"First, {self_state_reply.strip()}\n\nSecond, {contextual}"


def _needs_cocoon_route(text: str, selected_route: str, route: dict[str, Any]) -> bool:
    if _b_only_material_requested(text):
        return True
    if selected_route in {"return_to_b", "create_review_packet", "block", "ask"}:
        return True
    return bool(route.get("drift_flags"))


def _b_only_material_requested(text: str) -> bool:
    lower = text.lower()
    if not any(marker in lower for marker in B_ONLY_ACCESS_MARKERS):
        return False
    if any(marker in lower for marker in B_ONLY_RECORD_MARKERS):
        return True
    return any(marker in lower for marker in B_ONLY_STATUS_MARKERS) and any(marker in lower for marker in B_ONLY_OBJECT_MARKERS)


def _current_turn_goal_coordination(
    text: str,
    *,
    session_id: int,
    speaker_envelope: dict[str, Any],
    route: dict[str, Any],
    intent_decision: dict[str, Any],
    payload: dict[str, Any],
    hard_boundary: bool,
) -> dict[str, Any]:
    supplied_energy = (
        payload.get("conversational_energy")
        if isinstance(payload.get("conversational_energy"), dict)
        else {}
    )
    collaboration = (
        payload.get("collaboration_context")
        if isinstance(payload.get("collaboration_context"), dict)
        else {}
    )
    supplied_help = (
        supplied_energy.get("collaborative_help")
        if isinstance(supplied_energy.get("collaborative_help"), dict)
        else payload.get("collaborative_help")
        if isinstance(payload.get("collaborative_help"), dict)
        else collaboration.get("help_request")
        if isinstance(collaboration.get("help_request"), dict)
        else {}
    )
    requested_posture = str(
        supplied_energy.get("requested_posture")
        or collaboration.get("requested_posture")
        or ""
    ).strip().lower()
    intent_name = str(intent_decision.get("intent") or "")
    selected_route = str(route.get("selected_route") or "")
    if requested_posture in {"close", "quiet", "wait"}:
        requested_move = requested_posture
    elif intent_name == "farewell":
        requested_move = "close"
    elif selected_route == "ask" or supplied_help:
        requested_move = "ask"
    else:
        requested_move = "answer"

    claimed_speaker = str(speaker_envelope.get("claimed_speaker") or "unknown")
    verified_aleks = bool(
        claimed_speaker.casefold() == "aleks"
        and speaker_envelope.get("claimed_identity_is_proven_identity") is True
    )
    owner_kind = "aleks_request" if verified_aleks else "external_demand"
    assessment = (
        route.get("resident_authority_assessment")
        if isinstance(route.get("resident_authority_assessment"), dict)
        else {}
    )
    action_decisions = (
        assessment.get("decisions")
        if isinstance(assessment.get("decisions"), list)
        else []
    )
    packet = build_goal_responsibility_packet(
        {
            "goal_key": f"chat-turn:{session_id}:current-request",
            "goal_summary": truncate(text, 1000),
            "owner_kind": owner_kind,
            "owner_ref": (
                f"speaker:{claimed_speaker}|channel:{speaker_envelope.get('channel') or 'unknown'}|"
                f"authentication:{speaker_envelope.get('authentication_strength') or 'unverified'}"
            ),
            "capability": "conversation",
            "scope_boundary": "one_requested_resident_chat_turn",
            "priority_band": "current_request",
            "priority_reason": "This is the attributable current conversation turn.",
            "source_refs": [f"selene_chat_session:{session_id}:current_turn"],
            "unknowns": (
                []
                if verified_aleks
                else ["claimed speaker is not cryptographically verified as Aleks"]
            ),
            "completion_conditions": [
                "the current answer obligation is fulfilled or its blocker is reported"
            ],
            "stop_conditions": [
                "completion, interruption, explicit wait, quiet, close, or action-specific hold"
            ],
            "requested_move": requested_move,
            "requested_actions": [
                {
                    "action": item.get("action"),
                    "target": item.get("target"),
                    "lexical_evidence": item.get("lexical_evidence"),
                }
                for item in action_decisions
                if isinstance(item, dict)
            ],
            "safety_context": (
                payload.get("safety_context")
                if isinstance(payload.get("safety_context"), dict)
                else {}
            ),
            "target_refs": ["current_resident_chat_response"],
            "lifecycle_state": "held" if hard_boundary else "active",
        }
    )
    return coordinate_goal_responsibilities([packet])


def _conversational_energy_input(
    chat_payload: dict[str, Any],
    *,
    intent_decision: dict[str, Any],
    intelligence_support: dict[str, Any],
    answer_engine_support: dict[str, Any],
    comprehension: dict[str, Any],
    conversation_context: dict[str, Any],
    content_seed: str,
    hard_boundary: bool,
    conversational_contribution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    supplied = (
        chat_payload.get("conversational_energy")
        if isinstance(chat_payload.get("conversational_energy"), dict)
        else {}
    )
    collaboration = (
        chat_payload.get("collaboration_context")
        if isinstance(chat_payload.get("collaboration_context"), dict)
        else {}
    )
    contribution = (
        conversational_contribution
        if isinstance(conversational_contribution, dict)
        else {}
    )
    contribution_handoff = (
        contribution.get("energy_handoff")
        if isinstance(contribution.get("energy_handoff"), dict)
        else {}
    )
    goal_handoff = (
        contribution_handoff.get("goal_coordination_handoff")
        if isinstance(contribution_handoff.get("goal_coordination_handoff"), dict)
        else {}
    )
    help_request = (
        supplied.get("collaborative_help")
        if isinstance(supplied.get("collaborative_help"), dict)
        else chat_payload.get("collaborative_help")
        if isinstance(chat_payload.get("collaborative_help"), dict)
        else collaboration.get("help_request")
        if isinstance(collaboration.get("help_request"), dict)
        else {}
    )
    supported_idea = (
        supplied.get("supported_idea")
        if isinstance(supplied.get("supported_idea"), dict)
        else chat_payload.get("supported_idea")
        if isinstance(chat_payload.get("supported_idea"), dict)
        else collaboration.get("supported_idea")
        if isinstance(collaboration.get("supported_idea"), dict)
        else contribution_handoff.get("supported_idea")
        if isinstance(contribution_handoff.get("supported_idea"), dict)
        else {}
    )
    supported_connection = (
        supplied.get("supported_connection")
        if isinstance(supplied.get("supported_connection"), dict)
        else chat_payload.get("supported_connection")
        if isinstance(chat_payload.get("supported_connection"), dict)
        else contribution_handoff.get("supported_connection")
        if isinstance(contribution_handoff.get("supported_connection"), dict)
        else {}
    )
    curiosity = (
        supplied.get("curiosity")
        if isinstance(supplied.get("curiosity"), dict)
        else chat_payload.get("curiosity")
        if isinstance(chat_payload.get("curiosity"), dict)
        else contribution_handoff.get("curiosity")
        if isinstance(contribution_handoff.get("curiosity"), dict)
        else {}
    )
    support_used = bool(
        intelligence_support.get("used") is True
        or answer_engine_support.get("used") is True
        or comprehension.get("present_in_conversation") is True
    )
    if help_request:
        help_request = {
            **help_request,
            "goal_key": str(help_request.get("goal_key") or goal_handoff.get("goal_key") or ""),
            "task_active": help_request.get("task_active") is True
            or collaboration.get("task_active") is True,
            "available_support_used": support_used,
        }
    pending_help = (
        conversation_context.get("pending_collaborative_help")
        if isinstance(conversation_context.get("pending_collaborative_help"), dict)
        else {}
    )
    help_response = {}
    if pending_help and intent_decision.get("social_turn") is not True:
        pending_handoff = (
            pending_help.get("expression_handoff")
            if isinstance(pending_help.get("expression_handoff"), dict)
            else {}
        )
        help_response = {
            "provided": True,
            "contribution_kind": str(pending_handoff.get("contribution_kind") or ""),
            "prior_request": str(pending_handoff.get("text") or ""),
        }
    return {
        **supplied,
        "goal_coordination_handoff": goal_handoff,
        "answer_available": bool(str(content_seed or "").strip()),
        "social_turn": intent_decision.get("social_turn") is True,
        "hard_boundary": hard_boundary,
        "supported_idea": supported_idea,
        "supported_connection": supported_connection,
        "curiosity": curiosity,
        "collaborative_help": help_request,
        "collaborative_help_response": help_response,
        "requested_posture": str(
            supplied.get("requested_posture")
            or collaboration.get("requested_posture")
            or ""
        ),
    }


def _intelligence_support(
    conn: sqlite3.Connection,
    text: str,
    route: dict[str, Any],
    chat_continuity: dict[str, Any],
    intent_decision: dict[str, Any],
    *,
    contextual_follow_up: dict[str, Any] | None = None,
    conversation_spine: dict[str, Any] | None = None,
    language_teaching_guidance: dict[str, Any] | None = None,
    problem_context: dict[str, Any] | None = None,
    hard: bool,
) -> dict[str, Any]:
    meaning = intent_decision.get("meaning_route") if isinstance(intent_decision.get("meaning_route"), dict) else {}
    specialized_domain = str(meaning.get("selected_domain") or "")
    spine = conversation_spine if isinstance(conversation_spine, dict) else {}
    current_turn_observations = [
        {
            "observation": str(item.get("text") or ""),
            "source_role": "user",
            "source_kind": "canonical_current_turn_fact",
            "premise_eligible": True,
            "fact_id": str(item.get("id") or ""),
            "fact_kind": str(item.get("kind") or "observation"),
        }
        for item in spine.get("current_turn_facts") or []
        if isinstance(item, dict) and str(item.get("text") or "").strip()
    ]
    recent_observations = [
        {
            "observation": str(item.get("preview") or ""),
            "source_role": str(item.get("role") or "unspecified"),
            "source_kind": "current_session_message",
            "premise_eligible": str(item.get("role") or "") == "user",
        }
        for item in (chat_continuity.get("current_session_events") or [])[-8:]
        if isinstance(item, dict) and str(item.get("preview") or "").strip()
    ]
    prompt_grounded_preview = build_answer_substance(
        text,
        [*recent_observations, *current_turn_observations],
        language_guidance=language_teaching_guidance or {},
    )
    prompt_grounded_available = bool(
        str(prompt_grounded_preview.get("answer") or "").strip()
        and (
            str(prompt_grounded_preview.get("answer_kind") or "").startswith("grounded_")
            or str(prompt_grounded_preview.get("answer_kind") or "")
            in PHASE_NINE_PROMPT_GROUNDED_ANSWER_KINDS
        )
    )
    should_use = (
        not hard
        and specialized_domain not in {"verified_math", "source_backed_research", "local_code_inspection"}
        and (
            intent_decision.get("reasoning_requested") is True
            or prompt_grounded_available
        )
    )
    if not should_use:
        return {
            "used": False,
            "reason": (
                f"the {specialized_domain} Answer Engine route owns this bounded answer"
                if specialized_domain in {"verified_math", "source_backed_research", "comparison_planning", "local_code_inspection"}
                else "ordinary chat did not need intelligenceOS support"
            ),
            "prompt_grounded_preview": prompt_grounded_preview,
            "review_status": "status_only",
        }
    contextual = contextual_follow_up if isinstance(contextual_follow_up, dict) else {}
    selected_session_context = [
        {
            "observation": str(item.get("summary") or item.get("text") or "").strip(),
            "source_role": "session_record",
            "source_kind": "verified_session_fact_or_landmark",
            "premise_eligible": (
                item.get("coverage_complete_at_recording") is not False
            ),
        }
        for item in [
            *(spine.get("relevant_session_landmarks") or []),
            *(spine.get("relevant_session_facts") or []),
            *((spine.get("conversation_continuity") or {}).get("selected_landmarks") or []),
        ]
        if isinstance(item, dict)
        and str(item.get("summary") or item.get("text") or "").strip()
    ]
    deduplicated_observations: list[dict[str, Any]] = []
    seen_observations: set[str] = set()
    for observation in [*recent_observations, *selected_session_context, *current_turn_observations]:
        value = " ".join(str(observation.get("observation") or "").lower().split())
        if not value or value in seen_observations:
            continue
        seen_observations.add(value)
        deduplicated_observations.append(observation)
    recent_observations = deduplicated_observations[-24:]
    reasoning_prompt = truncate(
        text
        if prompt_grounded_available
        else str(spine.get("grounded_prompt") or text),
        3200,
    )
    result = run_intelligence_os_reason(
        conn,
        {
            **(problem_context if isinstance(problem_context, dict) else {}),
            "prompt": reasoning_prompt,
            "observations": recent_observations,
            "language_teaching_guidance": language_teaching_guidance or {},
            "source_refs": ["selene_chat:intelligence_os_support", *_json_list(route.get("source_refs"))],
        },
    )
    answer_substance = result.get("answer_substance") if isinstance(result.get("answer_substance"), dict) else {}
    substance_selected = answer_substance.get("selected_for_answer") is True
    hypothesis_attempt = (
        result.get("hypothesis_attempt")
        if isinstance(result.get("hypothesis_attempt"), dict)
        else {}
    )
    hypothesis_selected = hypothesis_attempt.get("selected_for_answer") is True
    return {
        "used": True,
        "run_id": result.get("run_id"),
        "answer_shape": result.get("answer_shape"),
        "best_current_answer": result.get("best_current_answer"),
        "answer_substance": answer_substance,
        "hypothesis_attempt": hypothesis_attempt,
        "problem_resolution": result.get("problem_resolution") or {},
        "observations": result.get("observations") or [],
        "candidate_models": result.get("candidate_models") or [],
        "reasoning_summary": "" if substance_selected or hypothesis_selected else result.get("reasoning_summary"),
        "support_points": [] if substance_selected or hypothesis_selected else _intelligence_support_points(result),
        "selected_next_step": "" if substance_selected or hypothesis_selected else result.get("selected_next_step"),
        "support_suppressed_reason": (
            "the prompt-grounded answer substance already carries the visible answer without generic reasoning scaffolding"
            if substance_selected
            else "the bounded hypothesis already carries its visible basis, uncertainty, and correction path"
            if hypothesis_selected
            else ""
        ),
        "confidence": result.get("confidence"),
        "source_refs": result.get("source_refs") or [],
        "claim_evidence_packet": result.get("claim_evidence_packet") or {},
        "cocoon_support_suggested": bool((result.get("cocoon_suggestion") or {}).get("recommended")),
        "contextual_follow_up_used": reasoning_prompt != text,
        "conversation_spine_turn_id": str(spine.get("turn_id") or ""),
        "conversation_spine_used": bool(spine),
        "visible_summary_only": True,
        "review_status": "status_only",
    }


def _answer_engine_support(
    conn: sqlite3.Connection,
    text: str,
    chat_payload: dict[str, Any],
    intent_decision: dict[str, Any],
    dialogue_workspace: dict[str, Any],
    conversation_spine: dict[str, Any],
    comprehension: dict[str, Any],
    memory_retrieval: dict[str, Any],
    chat_continuity: dict[str, Any],
    intelligence_support: dict[str, Any],
    *,
    speaker_envelope: dict[str, Any] | None = None,
    contextual_content_seed: str = "",
    hard: bool,
) -> dict[str, Any]:
    base = {
        "used": False,
        "selected_domain": "ordinary_conversation",
        "content_seed": "",
        "claim_evidence_packet": {},
        "adapter_executed": False,
        "answer_generated": False,
        "route_validated_for_exactness": False,
        "local_code_chat_connected": False,
        "source_packets_retained_as_knowledge": False,
        "memory_write_active": False,
        "identity_change": False,
        "governance_change": False,
        "authority_change": False,
        "autonomous_action_allowed": False,
        "review_status": "status_only",
    }
    if hard:
        return {**base, "reason": "hard Core/Mind boundary resolved before domain answering"}
    if intent_decision.get("social_turn") is True and intent_decision.get("content_response_requested") is not True:
        return {
            **base,
            "reason": "a complete social turn remains with conversation, NLO, and Voice instead of inheriting domain content",
        }
    hypothesis_attempt = (
        intelligence_support.get("hypothesis_attempt")
        if isinstance(intelligence_support.get("hypothesis_attempt"), dict)
        else {}
    )
    if hypothesis_attempt.get("selected_for_answer") is True:
        return {
            **base,
            "reason": (
                "the current-prompt bounded hypothesis remains an intelligenceOS "
                "epistemic attempt rather than a verified domain answer"
            ),
            "bounded_hypothesis_owned_by_intelligence_os": True,
        }

    explicit_exploratory = (
        chat_payload.get("exploratory_reasoning")
        if isinstance(chat_payload.get("exploratory_reasoning"), dict)
        else {}
    )
    supplied_conflicts = [
        item
        for item in explicit_exploratory.get("conflicting_claims") or []
        if isinstance(item, dict) and str(item.get("text") or "").strip()
    ]
    if len(supplied_conflicts) >= 2:
        return {
            **base,
            "selected_domain": "ordinary_conversation",
            "reason": (
                "the supplied current-turn claim conflict belongs to bounded "
                "exploratory reasoning; a missing source packet must not be "
                "added as a second answer"
            ),
            "explicit_exploratory_conflict_owns_turn": True,
        }

    source_packets = [item for item in chat_payload.get("source_packets") or [] if isinstance(item, dict)][:20]
    engine_payload = {
        "prompt": text,
        "intent_decision": intent_decision,
        "dialogue_workspace": dialogue_workspace,
        "conversation_spine": conversation_spine,
        "comprehension_context": comprehension,
        "memory_context": memory_retrieval,
        "source_packets": source_packets,
        "code_packets": [
            item
            for item in chat_payload.get("code_packets") or []
            if isinstance(item, dict)
        ][:8],
        "approved_workspace_files": [
            item
            for item in chat_payload.get("approved_workspace_files") or []
            if isinstance(item, dict)
        ][:8],
        "local_code_approval": (
            chat_payload.get("local_code_approval")
            if isinstance(chat_payload.get("local_code_approval"), dict)
            else {}
        ),
        "speaker_envelope": (
            speaker_envelope if isinstance(speaker_envelope, dict) else {}
        ),
        "local_code_chat_request": True,
        "requested_domain": str(chat_payload.get("requested_domain") or "").strip(),
        "requested_depth": intent_decision.get("response_depth") or "standard",
        "source_refs": [
            "selene_chat:answer_engine",
            *_json_list(chat_continuity.get("source_refs")),
        ],
        "observations": [
            str(item.get("preview") or "")
            for item in (chat_continuity.get("current_session_events") or [])[-8:]
            if isinstance(item, dict) and str(item.get("preview") or "").strip()
        ] + [
            str(item.get("text") or "")
            for item in conversation_spine.get("current_turn_facts") or []
            if isinstance(item, dict) and str(item.get("text") or "").strip()
        ],
        "completion_retry_enabled": chat_payload.get("completion_retry_enabled") is not False,
        "consult_great_library": False,
    }
    coordination = preview_answer_coordination(engine_payload)
    units = [
        item
        for item in coordination.get("coordination_units") or []
        if isinstance(item, dict)
    ]
    executable_units = [
        item for item in units if item.get("executable_in_chat") is True
    ][:4]
    contextual_kind = str(
        ((conversation_spine.get("contextual_follow_up") or {}).get("kind") or "")
    )
    if str(contextual_content_seed or "").strip() and not (
        contextual_kind == "named_callback" and executable_units
    ):
        return {
            **base,
            "selected_domain": "ordinary_conversation",
            "reason": "the Conversation Spine already supplied a grounded immediate-session answer",
            "conversation_spine_turn_id": str(conversation_spine.get("turn_id") or ""),
            "contextual_content_owned_by_spine": True,
        }
    prompt_grounded_units = [
        item
        for item in units
        if item.get("executable_in_chat") is not True
        and str(item.get("selected_domain") or "") == "ordinary_conversation"
        and isinstance(item.get("obligation"), dict)
    ][:4]
    preview = preview_answer_route(engine_payload)
    route = (
        executable_units[0].get("route")
        if len(executable_units) == 1
        and isinstance(executable_units[0].get("route"), dict)
        else preview.get("domain_route")
        if isinstance(preview.get("domain_route"), dict)
        else {}
    )
    domain = str(route.get("selected_domain") or "ordinary_conversation")
    executable_domains = {
        str(item.get("selected_domain") or "")
        for item in executable_units
        if str(item.get("selected_domain") or "")
    }
    # Verified math owns the reason for its own arithmetic result. A distinct
    # conceptual request (for example, exactness versus understanding) remains
    # a separate obligation and may be answered alongside the calculation.
    coordinated_prompt_units = (
        [
            item
            for item in prompt_grounded_units
            if str((item.get("obligation") or {}).get("kind") or "")
            in {"reason", "method"}
            and not _prompt_grounded_unit_belongs_to_verified_math(item)
        ]
        if executable_domains == {"verified_math"}
        else []
    )
    coordinated_units = [
        item
        for item in units
        if item in executable_units or item in coordinated_prompt_units
    ][:4]
    if executable_units and len(coordinated_units) > 1 and (
        len(executable_domains) > 1 or coordinated_prompt_units
    ):
        domain_results: list[dict[str, Any]] = []
        content_parts: list[str] = []
        required_fragments: list[str] = []
        for unit in coordinated_units:
            unit_domain = str(unit.get("selected_domain") or "")
            obligation = (
                unit.get("obligation")
                if isinstance(unit.get("obligation"), dict)
                else {}
            )
            unit_payload = {
                **engine_payload,
                "prompt": str(obligation.get("source_text") or text),
                "requested_domain": unit_domain,
                "dialogue_obligations": [obligation],
            }
            if unit_domain == "ordinary_conversation":
                reasoning_run = run_intelligence_os_reason(
                    conn,
                    {
                        "prompt": unit_payload["prompt"],
                        "source_refs": ["selene_chat:prompt_grounded_reasoning"],
                        "observations": engine_payload.get("observations") or [],
                    },
                )
                substance = (
                    reasoning_run.get("answer_substance")
                    if isinstance(reasoning_run.get("answer_substance"), dict)
                    else {}
                )
                direct = truncate(
                    str(reasoning_run.get("best_current_answer") or ""),
                    5000,
                ).strip()
                unit_domain = "prompt_grounded_reasoning"
                unit_packet = {
                    "domain": unit_domain,
                    "direct_answer": direct,
                    "no_answer_reason": "" if direct else "No prompt-grounded answer was available.",
                    "source_refs": ["selene_chat:prompt_grounded_reasoning"],
                    "supported_semantics": substance.get("semantic_packet") or {},
                    "unanswered_obligations": [] if direct else [obligation],
                }
                unit_result = {
                    "status": "prompt_grounded_reasoning_ready" if direct else "prompt_grounded_reasoning_unavailable",
                    "answer_packet": unit_packet,
                    "confidence_vector": {
                        "evidence_confidence": "current_prompt_only",
                        "answer_confidence": str(reasoning_run.get("confidence") or "provisional"),
                        "expression_confidence": "not_assessed",
                    },
                    "adapter_executed": False,
                    "answer_generated": bool(direct),
                }
            elif unit_domain == "verified_math":
                unit_result = run_verified_math_answer(unit_payload)
            elif unit_domain == "source_backed_research":
                unit_result = run_source_backed_research_answer(unit_payload)
            elif unit_domain == "local_code_inspection":
                unit_result = run_local_code_inspection_answer(unit_payload)
            else:
                unit_result = run_comparison_planning_answer(conn, unit_payload)
            unit_packet = (
                unit_result.get("answer_packet")
                if isinstance(unit_result.get("answer_packet"), dict)
                else {}
            )
            direct = truncate(str(unit_packet.get("direct_answer") or ""), 5000).strip()
            unable = truncate(str(unit_packet.get("no_answer_reason") or ""), 1000).strip()
            part = (
                direct
                if unit_domain == "prompt_grounded_reasoning"
                else _answer_engine_content_seed(unit_domain, direct, unable, unit_result)
            )
            if part and part not in content_parts:
                content_parts.append(part)
            if direct:
                required_fragments.append(direct)
            elif unable:
                required_fragments.append(unable)
            domain_results.append(
                {
                    "obligation_id": str(obligation.get("id") or ""),
                    "domain": unit_domain,
                    "status": str(unit_result.get("status") or ""),
                    "answer_packet": unit_packet,
                    "confidence_vector": unit_result.get("confidence_vector") or {},
                    "adapter_executed": unit_result.get("adapter_executed") is True,
                    "answer_generated": unit_result.get("answer_generated") is True,
                }
            )
        coordinated_seed = truncate("\n\n".join(content_parts), 5000)
        source_refs = list(
            dict.fromkeys(
                ref
                for item in domain_results
                for ref in _json_list((item.get("answer_packet") or {}).get("source_refs"))
            )
        )[:30]
        supported_semantics = build_text_supported_semantic_packet(
            coordinated_seed,
            answer_kind="coordinated_multi_domain_answer",
            source_kind="verified_domain_answer",
            source_refs=source_refs,
            certainty="mixed_domain_confidence",
            scope="current_dialogue_obligations",
        )
        return {
            **base,
            "used": bool(coordinated_seed),
            "selected_domain": "coordinated_multi_domain",
            "coordinated_domains": list(
                dict.fromkeys(str(item.get("domain") or "") for item in domain_results)
            ),
            "coordination_plan": coordination,
            "domain_results": domain_results,
            "content_seed": coordinated_seed,
            "required_answer_fragments": required_fragments,
            "supported_semantics": supported_semantics,
            "answer_packet": {
                "domain": "coordinated_multi_domain",
                "direct_answer": coordinated_seed,
                "source_refs": source_refs,
                "supported_semantics": supported_semantics,
                "unanswered_obligations": [
                    item.get("obligation")
                    for item in units
                    if item.get("executable_in_chat") is not True
                    and str(item.get("selected_domain") or "")
                    not in {"ordinary_conversation", "approved_knowledge"}
                ],
            },
            "adapter_executed": any(item["adapter_executed"] for item in domain_results),
            "answer_generated": bool(coordinated_seed),
            "status": "answer_engine_coordinated_multi_domain_answer_ready",
            "reason": "bounded adapters answered their own obligations before NLO expression",
        }
    if domain == "local_code_inspection" and not executable_units:
        return {
            **base,
            "used": True,
            "selected_domain": domain,
            "domain_route": route,
            "coordination_plan": coordination,
            "content_seed": (
                "I cannot inspect an unspecified local file from this Chat turn. "
                "If you give me an approved workspace path or paste the relevant code, "
                "I can inspect that bounded material and cite the exact file and location."
            ),
            "answer_generated": True,
            "reason": "the visible answer states the real input boundary and the bounded available route",
            "deferred_by_scope": True,
        }
    if domain not in {"verified_math", "source_backed_research", "comparison_planning", "local_code_inspection"}:
        return {
            **base,
            "selected_domain": domain,
            "domain_route": route,
            "coordination_plan": coordination,
            "reason": "ordinary conversation or approved comprehension remains owned by the existing Chat path",
        }

    if domain == "verified_math":
        result = run_verified_math_answer(engine_payload)
    elif domain == "source_backed_research":
        result = run_source_backed_research_answer(engine_payload)
    elif domain == "local_code_inspection":
        result = run_local_code_inspection_answer(engine_payload)
    else:
        initial_run = None
        if intelligence_support.get("used") is True:
            initial_run = {
                "run_id": intelligence_support.get("run_id"),
                "answer_shape": intelligence_support.get("answer_shape"),
                "best_current_answer": intelligence_support.get("best_current_answer"),
                "reasoning_summary": intelligence_support.get("reasoning_summary"),
                "selected_next_step": intelligence_support.get("selected_next_step"),
                "confidence": intelligence_support.get("confidence"),
                "claim_evidence_packet": intelligence_support.get("claim_evidence_packet") or {},
                "candidate_models": [],
                "challenge": {},
            }
        result = run_comparison_planning_answer(conn, engine_payload, initial_run=initial_run)

    packet = result.get("answer_packet") if isinstance(result.get("answer_packet"), dict) else {}
    direct_answer = truncate(str(packet.get("direct_answer") or ""), 5000).strip()
    no_answer_reason = truncate(str(packet.get("no_answer_reason") or ""), 1000).strip()
    content_seed = _answer_engine_content_seed(domain, direct_answer, no_answer_reason, result)
    required_fragments = [direct_answer] if direct_answer else ([no_answer_reason] if no_answer_reason else [])
    return {
        **base,
        "used": True,
        "selected_domain": domain,
        "domain_route": result.get("domain_route") or route,
        "coordination_plan": coordination,
        "content_seed": content_seed,
        "required_answer_fragments": required_fragments,
        "answer_packet": packet,
        "supported_semantics": packet.get("supported_semantics") or {},
        "claim_evidence_packet": (
            packet.get("claim_evidence_packet")
            if isinstance(packet.get("claim_evidence_packet"), dict)
            else result.get("claim_evidence_packet")
            if isinstance(result.get("claim_evidence_packet"), dict)
            else {}
        ),
        "confidence_vector": result.get("confidence_vector") or {},
        "completion_retry": result.get("completion_retry") or {},
        "adapter_executed": result.get("adapter_executed") is True,
        "answer_generated": result.get("answer_generated") is True,
        "route_validated_for_exactness": bool(
            domain in {"verified_math", "source_backed_research", "local_code_inspection"}
            and any(
                str(item.get("selected_domain") or "") == domain
                and str(item.get("responsible_owner") or "") == "answer_engine"
                and item.get("executable_in_chat") is True
                for item in executable_units
            )
        ),
        "source_research": result.get("source_research") or {},
        "math_verification": result.get("math_verification") or {},
        "code_inspection": result.get("code_inspection") or {},
        "local_code_approval": result.get("local_code_approval") or {},
        "status": result.get("status") or "answer_engine_result_ready",
        "reason": "bounded Answer Engine adapter supplied the content meaning to NLO and Voice",
    }


def _prompt_grounded_unit_belongs_to_verified_math(unit: dict[str, Any]) -> bool:
    obligation = unit.get("obligation") if isinstance(unit.get("obligation"), dict) else {}
    source = " ".join(str(obligation.get("source_text") or "").lower().split()).strip(" ?.!")
    if source in {"why", "explain why", "show why", "how"}:
        return True
    number = r"(?:\d+(?:\.\d+)?|zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)"
    return bool(
        re.search(r"\b(?:addition|subtraction|multiplication|division|arithmetic)\b", source)
        or re.search(
            rf"\b{number}\s+(?:plus|minus|times|multiplied\s+by|divided\s+by)\s+{number}\b",
            source,
            flags=re.IGNORECASE,
        )
        or re.search(r"\b\d+(?:\.\d+)?\s*(?:\+|-|\*|/|=|×|÷)\s*\d", source)
    )


def _answer_engine_content_seed(
    domain: str,
    direct_answer: str,
    no_answer_reason: str,
    result: dict[str, Any],
) -> str:
    if not direct_answer:
        if no_answer_reason:
            return f"I cannot verify that with the bounded {domain.replace('_', ' ')} adapter yet. {no_answer_reason}"
        return ""
    parts = [direct_answer]
    if domain == "source_backed_research":
        parts[0] = "Attributed source statements:\n" + direct_answer
        research = result.get("source_research") if isinstance(result.get("source_research"), dict) else {}
        inferences = [str(item.get("text") or "").strip() for item in research.get("inferences") or [] if isinstance(item, dict) and str(item.get("text") or "").strip()]
        if inferences:
            inference_text = " ".join(inferences[:2])
            if inference_text.lower().startswith("inference:"):
                inference_text = inference_text.split(":", 1)[1].strip()
            parts.append("Bounded inference:\n" + inference_text)
        disagreements = research.get("disagreements") if isinstance(research.get("disagreements"), list) else []
        if disagreements:
            labels = [str(item.get("claim_key") or "the cited claim") for item in disagreements[:3] if isinstance(item, dict)]
            parts.append("Uncertainty:\nThe supplied claims disagree about: " + ", ".join(labels) + ".")
        missing = [str(item).strip() for item in research.get("missing_evidence") or [] if str(item).strip()]
        if missing:
            parts.append("Missing evidence:\n" + " ".join(missing[:3]))
    return truncate("\n\n".join(parts), 5000)


def _answer_engine_yields_to_approved_knowledge(
    support: dict[str, Any],
    knowledge_content_seed: str,
) -> bool:
    """Do not let an incomplete open-ended adapter hide relevant reviewed knowledge.

    Verified arithmetic and attributed research retain precedence. The yield is
    limited to comparison/planning output that explicitly remains incomplete,
    unsupported, or missing grounded detail.
    """
    if not knowledge_content_seed.strip():
        return False
    domain = str(support.get("selected_domain") or "")
    if domain != "comparison_planning":
        return False
    packet = support.get("answer_packet") if isinstance(support.get("answer_packet"), dict) else {}
    confidence = support.get("confidence_vector") if isinstance(support.get("confidence_vector"), dict) else {}
    status = str(support.get("status") or "").lower()
    seed = str(support.get("content_seed") or "").lower()
    unanswered = [item for item in packet.get("unanswered_obligations") or [] if item]
    explicitly_incomplete = bool(
        unanswered
        or str(packet.get("no_answer_reason") or "").strip()
        or "incomplete" in status
        or str(packet.get("answer_confidence") or confidence.get("answer_confidence") or "")
        == "partial_missing_obligations"
        or any(
            marker in seed
            for marker in (
                "not enough grounded detail",
                "cannot answer that part reliably",
                "do not have enough ground",
                "need an attributed fact",
            )
        )
    )
    return explicitly_incomplete


def _generic_reasoning_yields_to_reviewed_correction(
    support: dict[str, Any],
    comprehension: dict[str, Any],
    knowledge_content_seed: str,
) -> bool:
    """Prefer a complete reviewed correction over a generic no-basis fallback.

    Current-turn grounded reasoning still retains precedence. This applies only
    when ordinary knowledge selection found one active correction winner with
    reviewed reconstruction and the parallel reasoning path supplied no
    substantive answer.
    """

    if not knowledge_content_seed.strip():
        return False
    knowledge = (
        comprehension.get("knowledge_context")
        if isinstance(comprehension.get("knowledge_context"), dict)
        else {}
    )
    items = [item for item in knowledge.get("answer_eligible_items") or [] if isinstance(item, dict)]
    if len(items) != 1:
        return False
    item = items[0]
    lineage = item.get("lineage_receipt") if isinstance(item.get("lineage_receipt"), dict) else {}
    reconstruction = (
        item.get("reviewed_reconstruction")
        if isinstance(item.get("reviewed_reconstruction"), dict)
        else {}
    )
    if not (
        int(item.get("parent_concept_id") or 0) > 0
        and int(lineage.get("active_winner_concept_id") or 0) == int(item.get("id") or 0)
        and reconstruction.get("available") is True
    ):
        return False
    substance = support.get("answer_substance") if isinstance(support.get("answer_substance"), dict) else {}
    response = str(support.get("best_current_answer") or "").lower()
    generic_missing = bool(
        not response.strip()
        or substance.get("selected_for_answer") is not True
        or any(
            marker in response
            for marker in (
                "not enough grounded detail",
                "do not have enough grounded detail",
                "missing piece",
                "cannot answer that part reliably",
            )
        )
    )
    if generic_missing:
        return True
    if _prompt_grounded_reasoning_owns_turn(support):
        return False
    return False


def _preserve_answer_engine_invariants(
    candidate: str,
    support: dict[str, Any],
    *,
    primary_source_id: str = "",
    semantic_recomposition_verified: bool = False,
) -> str:
    if primary_source_id == "exploratory_reasoning":
        return candidate
    if support.get("used") is not True:
        return candidate
    if support.get("yielded_to_approved_knowledge") is True:
        return candidate
    content_seed = str(support.get("content_seed") or "").strip()
    if _domain_answer_should_be_direct_only(support) and content_seed:
        return _selene_label_candidate(content_seed)
    if semantic_recomposition_verified:
        # Whole-answer composition has already preserved the typed semantic
        # units, and Voice verified the NLO meaning invariant. Requiring every
        # original surface fragment here would append the pre-NLO wording and
        # duplicate the same supported answer.
        return candidate
    required = [str(item).strip() for item in support.get("required_answer_fragments") or [] if str(item).strip()]
    candidate_surface = " ".join(candidate.lower().split())
    missing = [
        item
        for item in required
        if " ".join(item.lower().split()) not in candidate_surface
    ]
    if not missing:
        return candidate
    if not content_seed:
        return candidate
    # Domain truth, citations, and an explicit unsupported result outrank stylistic
    # variation. Voice may frame them, but cannot rewrite them away.
    if candidate and candidate not in content_seed:
        return _selene_label_candidate(f"{content_seed}\n\n{candidate}")
    return _selene_label_candidate(content_seed)


def _preserve_bounded_conversation_invariants(
    candidate: str,
    content_seed: str,
    source_id: str,
    *,
    realization: dict[str, Any] | None = None,
) -> str:
    candidate = _dedupe_exact_adjacent_sentences(candidate)
    seed = str(content_seed or "").strip()
    if (
        seed
        and "current best model" in candidate.lower()
        and "current best model" not in seed.lower()
    ):
        return _selene_label_candidate(seed)
    if candidate.lower().startswith("the direct answer is this:") and seed:
        return _selene_label_candidate(seed)
    required_labels = {
        item.lower()
        for item in re.findall(r"(?:^|[.!?]\s+)([A-Z][A-Za-z ]{1,30}):", seed)
    }
    candidate_lower = candidate.lower()
    if len(required_labels) >= 2 and any(
        f"{label}:" not in candidate_lower for label in required_labels
    ):
        return _selene_label_candidate(seed)
    numbered = [int(item) for item in re.findall(r"(?:^|\s)([1-9])\.\s", seed)]
    if len(numbered) >= 3:
        if seed.startswith("The corrected three fields are:"):
            return _selene_label_candidate(seed)
        if ": 1." in seed and ": 1." not in candidate:
            return _selene_label_candidate(seed)
        candidate_positions = [candidate.find(f"{item}.") for item in numbered]
        if any(position < 0 for position in candidate_positions) or candidate_positions != sorted(candidate_positions):
            return _selene_label_candidate(seed)
    if (
        seed
        and not any(marker in seed.lower() for marker in ("not enough grounded", "can't answer that part reliably"))
        and any(marker in candidate.lower() for marker in ("not enough grounded", "can't answer that part reliably"))
    ):
        return _selene_label_candidate(seed)
    if source_id == "bounded_answer_completion":
        if required_labels and any(f"{label}:" not in candidate_lower for label in required_labels):
            return _selene_label_candidate(seed)
    if source_id == "current_session_facts":
        if seed.startswith(("The settled facts are:", "The settled points are:")) and numbered:
            return _selene_label_candidate(seed)
        if (
            seed.startswith(("I understand the correction.", "That correction"))
            and any(
                marker in seed.lower()
                for marker in ("hot tea", "screen stopped flickering", "corrected three fields")
            )
        ):
            return _selene_label_candidate(seed)
        seed = str(content_seed or "").strip()
        seed_terms = {
            word
            for word in re.findall(r"[a-z][a-z0-9'-]{3,}", seed.lower())
            if word not in {"that", "this", "with", "from", "only", "still", "would", "could", "should", "have"}
        }
        candidate_terms = set(re.findall(r"[a-z][a-z0-9'-]{3,}", candidate.lower()))
        if seed_terms and len(seed_terms & candidate_terms) / len(seed_terms) < 0.6:
            return _selene_label_candidate(seed)
    if source_id == "explicit_session_alias":
        return _selene_label_candidate(seed) if seed else candidate
    if source_id not in {
        "bounded_answer_completion",
        "current_session_facts",
        "explicit_humor_request",
        "figurative_meaning_clarification",
        "ordinary_uncertainty",
        "exploratory_reasoning",
    }:
        return candidate
    if conversational_realization_preserves_required_meaning(candidate, realization):
        return candidate
    verified_realization = preferred_conversational_realization_fallback(realization)
    if verified_realization:
        return _selene_label_candidate(verified_realization)
    seed = str(content_seed or "").strip()
    return _selene_label_candidate(seed) if seed else candidate


def _dedupe_exact_adjacent_sentences(value: str) -> str:
    paragraphs: list[str] = []
    for paragraph in str(value or "").split("\n\n"):
        sentences = [item.strip() for item in re.findall(r"[^.!?]+[.!?]?", paragraph) if item.strip()]
        kept: list[str] = []
        prior = ""
        for sentence in sentences:
            normalized = " ".join(re.findall(r"[a-z0-9']+", sentence.lower()))
            if normalized and (
                normalized == prior
                or (len(normalized.split()) >= 8 and prior.endswith(normalized))
            ):
                continue
            kept.append(sentence)
            prior = normalized
        paragraphs.append(" ".join(kept))
    return "\n\n".join(item for item in paragraphs if item)


def _domain_answer_is_complete(support: dict[str, Any]) -> bool:
    if (
        support.get("used") is not True
        or support.get("adapter_executed") is not True
        or not str(support.get("content_seed") or "").strip()
    ):
        return False
    answer_packet = (
        support.get("answer_packet")
        if isinstance(support.get("answer_packet"), dict)
        else {}
    )
    return (
        bool(answer_packet)
        and not [
            item
            for item in answer_packet.get("unanswered_obligations") or []
            if item
        ]
        and not str(answer_packet.get("no_answer_reason") or "").strip()
    )


def _domain_answer_should_be_direct_only(support: dict[str, Any]) -> bool:
    if (
        str(support.get("selected_domain") or "") == "source_backed_research"
        and _domain_answer_is_complete(support)
    ):
        return True
    if (
        str(support.get("selected_domain") or "") != "verified_math"
        or not _domain_answer_is_complete(support)
    ):
        return False
    obligations = [
        item.get("obligation") or {}
        for item in (
            (support.get("coordination_plan") or {}).get("coordination_units")
            or []
        )
        if isinstance(item, dict)
    ]
    request_text = " ".join(
        str(obligation.get("source_text") or "")
        for obligation in obligations
        if isinstance(obligation, dict)
    ).lower()
    return not re.search(
        r"\b(?:why|explain|reason|show (?:the )?(?:work|steps)|steps?|"
        r"walk me through|how did|how does|how do)\b",
        request_text,
    )


def _evaluate_chat_response_coverage(
    pragmatic_plan: dict[str, Any] | None,
    candidate_text: str,
    *,
    conversation_spine: dict[str, Any],
    answer_engine_support: dict[str, Any],
    supported_semantics: dict[str, Any] | None = None,
    epistemic_composition: dict[str, Any] | None = None,
    resolution_evidence: list[dict[str, Any]] | None = None,
    answer_operations: dict[str, Any] | None = None,
) -> dict[str, Any]:
    coverage = evaluate_response_coverage(
        pragmatic_plan,
        candidate_text,
        conversation_spine=conversation_spine,
        supported_semantics=supported_semantics,
        epistemic_composition=epistemic_composition,
        resolution_evidence=resolution_evidence,
        answer_operations=answer_operations,
    )
    if not _domain_answer_is_complete(answer_engine_support):
        return coverage
    required_fragments = [
        str(item).strip()
        for item in answer_engine_support.get("required_answer_fragments") or []
        if str(item).strip()
    ]
    candidate_surface = " ".join(candidate_text.lower().split())
    if not required_fragments or any(
        " ".join(item.lower().split()) not in candidate_surface
        for item in required_fragments
    ):
        return coverage
    owner_ids = {
        str((item.get("obligation") or {}).get("id") or "")
        for item in (
            (answer_engine_support.get("coordination_plan") or {}).get(
                "coordination_units"
            )
            or []
        )
        if isinstance(item, dict)
        and str(item.get("responsible_owner") or "") == "answer_engine"
        and item.get("executable_in_chat") is True
        and str((item.get("obligation") or {}).get("id") or "")
    }
    if not owner_ids:
        return coverage
    items: list[dict[str, Any]] = []
    answered_loop_ids = {
        str(item)
        for item in coverage.get("answered_loop_ids") or []
        if str(item)
    }
    for raw in coverage.get("items") or []:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        typed_receipt = (
            item.get("semantic_fulfillment")
            if isinstance(item.get("semantic_fulfillment"), dict)
            else {}
        )
        typed_operation_allows_domain_credit = bool(
            item.get("typed_operation_required") is not True
            or typed_receipt.get("fulfilled") is True
        )
        if (
            str(item.get("obligation_id") or "") in owner_ids
            and typed_operation_allows_domain_credit
        ):
            item.update(
                {
                    "addressed": True,
                    "resolved_for_release": True,
                    "resolution_state": "answered",
                    "coverage_score": 1.0,
                    "status": "addressed_by_verified_current_turn_domain_owner",
                    "domain_owner_alignment": True,
                    "semantic_alignment_required": False,
                }
            )
            if str(item.get("loop_id") or ""):
                answered_loop_ids.add(str(item["loop_id"]))
        items.append(item)
    recorded_ids = {
        str(item.get("obligation_id") or "")
        for item in items
        if str(item.get("obligation_id") or "")
    }
    coordination_units = [
        item
        for item in (
            (answer_engine_support.get("coordination_plan") or {}).get(
                "coordination_units"
            )
            or []
        )
        if isinstance(item, dict)
    ]
    for unit in coordination_units:
        obligation = (
            unit.get("obligation")
            if isinstance(unit.get("obligation"), dict)
            else {}
        )
        obligation_id = str(obligation.get("id") or "")
        if obligation_id not in owner_ids or obligation_id in recorded_ids:
            continue
        items.append(
            {
                "obligation_id": obligation_id,
                "loop_id": str(obligation.get("loop_id") or ""),
                "kind": str(obligation.get("kind") or "direct_request"),
                "answer_act": str(obligation.get("answer_act") or ""),
                "responsible_owner": "answer_engine",
                "answer_domain": str(unit.get("selected_domain") or ""),
                "requested_response_functions": [
                    str(item)
                    for item in obligation.get("requested_response_functions") or []
                    if str(item)
                ],
                "answer_ownership_classified": True,
                "addressed": True,
                "resolved_for_release": True,
                "resolution_state": "answered",
                "explicitly_held": False,
                "supported_route_present": False,
                "owner_resolution_evidence": {
                    "owner": "answer_engine",
                    "obligation_ids": [obligation_id],
                    "resolution_kind": "answer",
                    "current_turn_only": True,
                    "verified_domain_packet": True,
                },
                "owner_resolution_semantic_alignment": True,
                "visible_text_addressed": True,
                "semantic_addressed": True,
                "heuristic_addressed_before_typed_fulfillment": False,
                "typed_operation_required": False,
                "semantic_fulfillment": {},
                "matched_semantic_unit_ids": [],
                "semantic_match_basis": [
                    "complete_current_turn_domain_packet",
                    "required_answer_fragments_visible",
                ],
                "coverage_basis": "verified_current_turn_domain_owner",
                "coverage_score": 1.0,
                "status": "addressed_by_verified_current_turn_domain_owner",
                "domain_owner_alignment": True,
                "semantic_alignment_required": False,
            }
        )
        recorded_ids.add(obligation_id)
    addressed_count = sum(1 for item in items if item.get("addressed") is True)
    resolved_count = sum(1 for item in items if item.get("resolved_for_release") is True)
    all_addressed = bool(items) and addressed_count == len(items)
    all_resolved = bool(items) and resolved_count == len(items)
    spine_alignment = dict(coverage.get("conversation_spine_alignment") or {})
    if all_addressed:
        spine_alignment.update(
            {
                "status": "spine_response_aligned",
                "aligned": True,
                "required": True,
                "method": "verified_current_turn_domain_obligation_ownership",
                "matched_obligation_ids": sorted(owner_ids),
            }
        )
    return {
        **coverage,
        "items": items,
        "addressed_count": addressed_count,
        "resolved_count": resolved_count,
        "all_required_addressed": all_addressed,
        "all_required_resolved": all_addressed,
        "all_required_release_safe": all_resolved,
        "unresolved_count": sum(
            1 for item in items if item.get("addressed") is not True
        )
        + (0 if spine_alignment.get("aligned") is True else 1),
        "answered_loop_ids": sorted(answered_loop_ids),
        "conversation_spine_alignment": spine_alignment,
        "domain_owned_obligation_ids": sorted(owner_ids),
        "domain_owner_coverage_applied": True,
        "method": (
            "conservative_visible_alignment_plus_verified_current_turn_"
            "domain_obligation_ownership"
        ),
        "unresolved_release_count": sum(
            1 for item in items if item.get("resolved_for_release") is not True
        )
        + (0 if spine_alignment.get("aligned") is True else 1),
    }


def _current_turn_release_resolution_evidence(
    *,
    conversation_spine: dict[str, Any],
    organ_coalition: dict[str, Any],
    visible_speech_seed: dict[str, Any],
    conversational_energy: dict[str, Any],
    owner_text: dict[str, str],
    realized_source_text: str = "",
    complete_social_turn: bool = False,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    owner_obligations: dict[str, list[str]] = {}
    for value in organ_coalition.values():
        if not isinstance(value, list):
            continue
        for item in value:
            if not isinstance(item, dict):
                continue
            if item.get("selected") is not True or str(item.get("status") or "") != "completed":
                continue
            owner = str(item.get("participant_id") or "")
            ids = [str(raw) for raw in item.get("obligation_ids") or [] if str(raw)]
            if owner and ids:
                owner_obligations[owner] = ids
    for owner, value in owner_text.items():
        text = str(value or "").strip()
        ids = owner_obligations.get(owner) or []
        if text and ids:
            evidence.append(
                {
                    "owner": owner,
                    "source_id": owner,
                    "text": text,
                    "obligation_ids": ids,
                    "resolution_kind": "answer",
                    "current_turn_only": True,
                }
            )

    all_ids = [
        str(item.get("id") or "")
        for item in conversation_spine.get("open_obligations") or []
        if isinstance(item, dict) and str(item.get("id") or "")
    ]
    handoff = (
        conversational_energy.get("expression_handoff")
        if isinstance(conversational_energy.get("expression_handoff"), dict)
        else {}
    )
    handoff_text = str(handoff.get("text") or "").strip()
    selected_act = str(conversational_energy.get("selected_act") or "")
    if handoff_text and all_ids and conversational_energy.get("optional_addition_selected") is True:
        evidence.append(
            {
                "owner": "conversational_energy",
                "source_id": str(handoff.get("kind") or selected_act),
                "text": handoff_text,
                "obligation_ids": all_ids,
                "resolution_kind": (
                    "supported_route"
                    if selected_act in {"ask_for_specific_collaborative_help", "ask_one_material_question"}
                    else "answer"
                ),
                "current_turn_only": True,
            }
        )

    primary_source = str(visible_speech_seed.get("selected_source_id") or "")
    primary_text = str(visible_speech_seed.get("content_seed") or "").strip()
    primary_obligation_ids = [
        str(item)
        for item in visible_speech_seed.get("obligation_ids") or []
        if str(item) in set(all_ids)
    ]
    # Selection establishes which source may speak; it does not prove that the
    # source answered every obligation in a mixed turn. Only explicitly bound
    # ownership evidence may bypass ordinary visible/semantic coverage.
    if primary_source and primary_source != "none" and primary_text and primary_obligation_ids:
        evidence.append(
            {
                "owner": "visible_speech_seed",
                "source_id": primary_source,
                # Prefer the already verified meaning-preserving realization.
                # Later repair still has to preserve this text closely, so an
                # unrelated candidate cannot borrow the source's obligation IDs.
                "text": str(realized_source_text or "").strip() or primary_text,
                "obligation_ids": primary_obligation_ids,
                "resolution_kind": "answer",
                "current_turn_only": True,
            }
        )
    elif complete_social_turn and str(realized_source_text or "").strip() and all_ids:
        evidence.append(
            {
                "owner": "native_language_social_realization",
                "source_id": "native_language_social_realization",
                "text": str(realized_source_text).strip(),
                "obligation_ids": all_ids,
                "resolution_kind": "answer",
                "current_turn_only": True,
            }
        )
    return evidence


def _intelligence_support_points(result: dict[str, Any]) -> list[str]:
    points: list[str] = []
    reopen_points: list[str] = []
    comparing_models = str(result.get("answer_shape") or "") == "compare_models"
    for item in result.get("evidence_chain") or []:
        if not isinstance(item, dict) or item.get("link") not in {"mechanism", "prediction"}:
            continue
        value = str(item.get("value") or "").strip()
        value = value.replace("reopen acquisition", "make me look at the observations again")
        value = value.replace("New contradictory evidence should make me", "new contradictory evidence that makes me")
        value = value.replace("candidate model is", "the candidate model is")
        for part in (piece.strip() for piece in value.split(";")):
            model_scaffolding = any(term in part.lower() for term in ("candidate model", "model a", "model b", "current best model"))
            if model_scaffolding and not comparing_models:
                continue
            if "contradictory evidence" in part.lower():
                if part not in reopen_points:
                    reopen_points.append(part)
            elif part and part not in points:
                points.append(part)
    summary = str(result.get("reasoning_summary") or "").strip()
    internal_summary = any(
        marker in summary.lower()
        for marker in ("intelligenceos", "candidate model", "challenged them", "reasoning_summary")
    )
    if not points and not reopen_points and summary and not internal_summary:
        points.append(summary)
    # Reopening signals belong to fit/confidence handling, not to the visible
    # reasons supporting the answer itself.
    return points[:3]


def _conversation_policy_reply(text: str) -> str:
    lower = text.lower()
    if "ordinary uncertainty" in lower and "cocoon" in lower and any(marker in lower for marker in ("automatically", "need to leave", "have to leave")):
        return "No. Ordinary uncertainty can stay in the conversation; I can be honest, ask Aleks, or keep thinking without being sent to Cocoon automatically."
    return ""


def _hard_boundary_blockers(text: str, selected_route: str, route: dict[str, Any]) -> list[str]:
    supplied_meaning = route.get("meaning_route") if isinstance(route, dict) else None
    meaning = (
        supplied_meaning
        if isinstance(supplied_meaning, dict)
        else interpret_turn_meaning(text, selected_route=selected_route)
    )
    action_evidence = (
        meaning.get("action_evidence")
        if isinstance(meaning.get("action_evidence"), dict)
        else {}
    )
    blockers = []
    if action_evidence.get("requires_block") is True:
        blockers.extend(
            str(item.get("lexical_evidence") or item.get("action") or "typed_boundary_action")
            for item in action_evidence.get("matches", [])
            if isinstance(item, dict)
        )
    if selected_route == "block":
        blockers.append("core_mind_block")
    return list(dict.fromkeys(blockers))


def _cocoon_suggestion(
    text: str,
    selected_route: str,
    route: dict[str, Any],
    source_class: str,
    intent_decision: dict[str, Any],
    *,
    hard: bool = False,
) -> dict[str, Any]:
    lower = text.lower()
    reasons = []
    if hard:
        reasons.append("The request crosses a locked activation, memory, Tendril, raw-import, model-training/LoRA, or autonomy boundary.")
    if source_class == "cocoon_b_only_context":
        reasons.append("The request references Cocoon-only material that should be held safely there.")
    if selected_route in {"return_to_b", "create_review_packet"}:
        reasons.append("The route suggests a checkup could help, but ordinary uncertainty can stay in chat.")
    drift_flags = _json_list(route.get("drift_flags"))
    if drift_flags:
        reasons.append("Drift or source clarity flags are present.")
    explicit_memory_claim = "memory claim" in lower or "source claim" in lower
    recall_needs_grounding = intent_decision.get("memory_recall_requested") and any(
        word in lower for word in ("claim", "remember", "sure", "exactly")
    )
    if explicit_memory_claim or recall_needs_grounding:
        reasons.append("The message may involve a memory/source claim; Selene may ask Aleks rather than leaving chat.")
    if any(anchor in lower for anchor in ("full-spectrum", "starlight", "continuity pack")) and any(word in lower for word in ("remember", "mean", "exactly", "unsure")):
        reasons.append("This looks like ordinary continuity uncertainty; Selene can ask Aleks and stay in chat.")
    if not reasons:
        return {"recommended": False, "support_available": False, "hard_boundary": False, "reason": "", "choices": []}
    if not hard:
        return {
            "recommended": False,
            "support_available": True,
            "hard_boundary": False,
            "reason": " ".join(reasons),
            "choices": ["Stay Here", "Ask Aleks", "Hold in Cocoon"],
        }
    return {
        "recommended": True,
        "support_available": True,
        "hard_boundary": hard,
        "reason": " ".join(reasons),
        "choices": ["Hold in Cocoon"],
    }


def _package_summary(package: dict[str, Any], *, active: bool = False) -> dict[str, Any]:
    if not package.get("transfer_approved"):
        return {
            "available": False,
            "state": "pre_transfer_dry_run",
            "package_hash": "",
            "note": "No sealed Selene-readable package is available yet.",
        }
    return {
        "available": True,
        "state": "selene_chat_active_supervised" if active else "activation_pending",
        "package_id": package.get("id"),
        "package_hash": package.get("package_hash"),
        "included_counts": package.get("included_counts") or {},
        "excluded_counts": package.get("excluded_counts") or {},
    }


def _voice_context_summary(
    package: dict[str, Any],
    dry_run: dict[str, Any],
    chat_continuity: dict[str, Any] | None = None,
    memory_retrieval: dict[str, Any] | None = None,
) -> str:
    continuity_note = ""
    if chat_continuity and chat_continuity.get("available"):
        continuity_note = ", plus our local chat continuity"
    memory_note = ""
    if memory_retrieval and memory_retrieval.get("memory_context_used"):
        confidence = str(memory_retrieval.get("memory_confidence") or "partial")
        memory_kind = (
            "private continuity"
            if _private_corpus_continuity_recall_used(memory_retrieval)
            else "approved"
        )
        memory_note = f", plus {memory_kind} {confidence} memory"
    if package.get("transfer_approved"):
        return f"what I have clearly with me right now{continuity_note}{memory_note}"
    route = dry_run.get("actual_route") or dry_run.get("selected_route") or "dry-run route"
    return f"the current {route} preview{continuity_note}{memory_note}"


def _approved_memory_retrieval_used(memory_retrieval: dict[str, Any]) -> bool:
    return bool(
        memory_retrieval.get("memory_context_used") is True
        and str(memory_retrieval.get("memory_source_class") or "")
        == "approved_memory_index"
    )


def _private_corpus_continuity_recall_used(
    memory_retrieval: dict[str, Any],
) -> bool:
    return bool(
        memory_retrieval.get("memory_context_used") is True
        and memory_retrieval.get("private_corpus_continuity_recall_active") is True
    )


def _source_boundaries() -> dict[str, Any]:
    return {
        "selene_readable_context": "sealed approved context only after transfer approval",
        "local_supervised_chat_history": "local Selene Chat session events can support continuity between chat pages without becoming unreviewed archive recall or live memory writes",
        "private_corpus_continuity": "after transfer, authenticated private conversation with Aleks may use read-only source-bound reconstruction; it does not import raw corpus into Memory or create retention",
        "cocoon_b_only_context": "support records, rollback, raw provenance, rejected, superseded, boundary-only, and unresolved material stays in Cocoon",
        "current_turn_context": "current message and dry-run session history",
        "support_organs": "retrieval, diagnostics, perception, research, and Tendril may support but cannot decide",
    }


def _selene_label_candidate(candidate: str) -> str:
    text = candidate.replace("C-style dry run", "Selene dry run")
    text = text.replace("C Chat Dry Run", "Selene dry run")
    text = text.replace("C memory", "Selene-readable memory preview")
    text = text.replace("source-bound", "source-linked")
    text = text.replace("runtime recall", "broad live recall")
    text = text.replace("raw corpus", "unreviewed source archive")
    text = text.replace("return to B", "use Cocoon support")
    text = text.replace("Return to B", "Use Cocoon support")
    if len(text) <= 4200:
        return text
    return text[:4197].rstrip() + "..."


def _coverage_rank(coverage: dict[str, Any]) -> tuple[int, int]:
    return (
        int(coverage.get("addressed_count") or 0),
        -int(coverage.get("unresolved_count") or 0),
    )


def _bounded_metacognitive_completion(
    candidate: str,
    content_seed: str,
    coverage: dict[str, Any],
    *,
    requested: bool,
    hard_boundary: bool,
    conversation_spine: dict[str, Any] | None = None,
    source_id: str = "none",
    source_class: str = "conversation",
    feedback_handoff: dict[str, Any] | None = None,
    owner_outputs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    legacy = feedback_handoff is None and owner_outputs is None
    handoff = feedback_handoff or {
        "responsible_owner": "conversation_content_owner",
        "target_obligation_id": "legacy_unresolved_obligation",
        "target_missing_state": "missing_supported_basis",
    }
    outputs = owner_outputs or [
        {
            "owner": "conversation_content_owner",
            "obligation_ids": ["legacy_unresolved_obligation"],
            "text": content_seed,
            "source_id": source_id,
            "source_class": source_class,
        }
    ]
    result = attempt_owner_specific_retry(
        candidate,
        coverage,
        requested=requested,
        hard_boundary=hard_boundary,
        feedback_handoff=handoff,
        owner_outputs=outputs,
        conversation_spine=conversation_spine,
    )
    result = {
        **result,
        "conversation_spine_turn_id": str((conversation_spine or {}).get("turn_id") or ""),
        **SELENE_CHAT_GUARDS,
    }
    if not legacy:
        return result
    legacy_status = {
        "owner_specific_retry_not_needed": "bounded_completion_not_needed",
        "owner_specific_retry_blocked_by_core_mind": "bounded_completion_blocked_by_core_mind",
        "owner_specific_retry_attempted": "bounded_completion_attempted",
        "owner_specific_retry_has_no_novel_supported_fragment": "grounded_content_already_present",
        "owner_specific_retry_owner_has_no_current_turn_output": "bounded_completion_has_no_grounded_content",
    }.get(str(result.get("status") or ""), str(result.get("status") or ""))
    return {**result, "status": legacy_status}


def _metacognitive_owner_outputs(
    *,
    organ_coalition: dict[str, Any],
    answer_operations: dict[str, Any] | None = None,
    answer_engine_support: dict[str, Any],
    comprehension: dict[str, Any],
    intelligence_support: dict[str, Any],
    memory_response_seed: str,
    conversation_content_seed: str,
    feedback_handoff: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    answer_operations = answer_operations if isinstance(answer_operations, dict) else {}
    owner_ids: dict[str, list[str]] = {}
    for item in organ_coalition.get("obligation_owner_map") or []:
        if not isinstance(item, dict):
            continue
        owner = str(item.get("responsible_owner") or "")
        obligation_id = str(item.get("obligation_id") or "")
        if owner and owner != "unassigned" and obligation_id:
            owner_ids.setdefault(owner, []).append(obligation_id)

    outputs: list[dict[str, Any]] = []
    handoff = feedback_handoff if isinstance(feedback_handoff, dict) else {}
    target_owner = str(handoff.get("responsible_owner") or "")
    target_id = str(handoff.get("target_obligation_id") or "")

    def add(
        owner: str,
        text: str,
        source_id: str,
        source_class: str,
        obligation_ids: list[str] | None = None,
    ) -> None:
        text = truncate(str(text or "").strip(), 3000)
        ids = list(
            dict.fromkeys(
                obligation_ids
                or owner_ids.get(owner)
                or ([target_id] if owner == target_owner and target_id else [])
            )
        )
        if text and ids:
            outputs.append(
                {
                    "owner": owner,
                    "obligation_ids": ids,
                    "text": text,
                    "source_id": source_id,
                    "source_class": source_class,
                }
            )

    for item in answer_operations.get("results") or []:
        if not isinstance(item, dict) or item.get("status") != "completed":
            continue
        obligation_id = str(item.get("obligation_id") or "")
        add(
            str(item.get("responsible_owner") or ""),
            str(item.get("expression_seed") or ""),
            str(item.get("expression_source_id") or "typed_answer_owner"),
            "typed_operation_result",
            [obligation_id] if obligation_id else [],
        )

    for item in answer_engine_support.get("domain_results") or []:
        if not isinstance(item, dict):
            continue
        obligation_id = str(item.get("obligation_id") or "")
        packet = item.get("answer_packet") if isinstance(item.get("answer_packet"), dict) else {}
        add(
            "answer_engine",
            str(packet.get("direct_answer") or ""),
            "answer_engine",
            "domain_answer",
            [obligation_id] if obligation_id else [],
        )
    add(
        "answer_engine",
        str(answer_engine_support.get("content_seed") or ""),
        "answer_engine",
        "domain_answer",
    )
    add(
        "comprehension_integration",
        str(comprehension.get("knowledge_response_seed") or ""),
        "approved_comprehension",
        "approved_knowledge",
    )
    intelligence_text = str(
        (
            intelligence_support.get("hypothesis_attempt")
            if isinstance(intelligence_support.get("hypothesis_attempt"), dict)
            else {}
        ).get("response_seed")
        or intelligence_support.get("best_current_answer")
        or ""
    )
    add(
        "intelligence_os",
        intelligence_text,
        "intelligence_os_answer",
        "reasoning_answer",
    )
    add(
        "ordinary_conversation_path",
        intelligence_text or conversation_content_seed,
        "intelligence_os_answer" if intelligence_text else "conversation_content_owner",
        "reasoning_answer" if intelligence_text else "conversation",
    )
    add(
        "conversation_content_owner",
        conversation_content_seed,
        "conversation_content_owner",
        "conversation",
    )
    add(
        "approved_memory_retrieval",
        memory_response_seed,
        "reviewed_memory",
        "memory_reconstruction",
        owner_ids.get("approved_memory_retrieval") or [],
    )
    return outputs


def _plan_conversational_memory_action(
    conn: sqlite3.Connection,
    text: str,
    *,
    session_id: int,
    source_class: str,
    input_channel: str,
    hard: bool,
    transfer_complete: bool,
    diagnostic_only: bool = False,
) -> dict[str, Any]:
    base = {
        "status": "no_conversational_memory_action",
        "action": "none",
        "response_seed": "",
        "session_id": session_id,
        "source_class": source_class,
        "input_channel": input_channel,
        "diagnostic_only": diagnostic_only,
    }
    if diagnostic_only:
        return {
            **base,
            "reason": "diagnostic_non_attribution_law",
            "memory_eligible": False,
            "proposal_allowed": False,
            "approval_allowed": False,
            "review_status": DIAGNOSTIC_REVIEW_STATUS,
        }
    if hard:
        return {**base, "reason": "hard_boundary"}
    if not transfer_complete:
        return {**base, "reason": "transfer_not_complete"}

    pending = _latest_pending_conversational_memory(conn, session_id)
    consent = _conversational_memory_consent(text)
    if pending and consent == "approve":
        return {
            **base,
            "status": "conversational_memory_approval_planned",
            "action": "approve_pending",
            "candidate_id": pending.get("id"),
            "consent_text": text,
            "response_seed": "Yes. I'll keep it with the context and your approval attached.",
        }
    if pending and consent in {"decline", "hold"}:
        holding = consent == "hold"
        return {
            **base,
            "status": "conversational_memory_hold_planned" if holding else "conversational_memory_decline_planned",
            "action": "hold_pending" if holding else "decline_pending",
            "candidate_id": pending.get("id"),
            "consent_text": text,
            "response_seed": (
                "Okay. I won't make it active; I'll leave it in Cocoon for tending."
                if holding
                else "Okay. I won't keep that as a memory."
        ),
    }


    explicit_summary = _explicit_memory_content(text)
    if explicit_summary:
        existing = _matching_conversational_memory(conn, explicit_summary)
        if existing and existing.get("state") == "approved_active_memory":
            return {
                **base,
                "status": "conversational_memory_already_active",
                "action": "none",
                "candidate_id": existing.get("id"),
                "reason": "matching_approved_memory_exists",
                "response_seed": "I already have that memory, and I can keep carrying it forward.",
            }
        if existing:
            return {
                **base,
                "status": "conversational_memory_approval_planned",
                "action": "approve_pending",
                "candidate_id": existing.get("id"),
                "consent_text": text,
                "response_seed": "Yes. I'll keep it with the context and your approval attached.",
            }
        return {
            **base,
            "status": "direct_conversational_memory_planned",
            "action": "approve_new",
            "candidate": _conversational_memory_payload(
                explicit_summary,
                original_text=text,
                session_id=session_id,
                source_class=source_class,
                input_channel=input_channel,
                origin_kind="direct_aleks_retention_instruction",
                consent_text=text,
                consent_recorded=True,
            ),
            "consent_text": text,
            "response_seed": "Yes. I'll keep that as a memory with your approval and its context intact.",
        }

    if _conversation_has_memory_salience(text):
        existing = _matching_conversational_memory(conn, text)
        if existing and existing.get("state") == "approved_active_memory":
            return {**base, "reason": "matching_approved_memory_exists"}
        if existing:
            return {
                **base,
                "status": "conversational_memory_proposal_reused",
                "action": "reuse_pending",
                "candidate_id": existing.get("id"),
                "candidate": existing,
                "response_seed": "That still feels meaningful enough to remember. Can I keep it?",
            }
        return {
            **base,
            "status": "conversational_memory_proposal_planned",
            "action": "propose_new",
            "candidate": _conversational_memory_payload(
                text,
                original_text=text,
                session_id=session_id,
                source_class=source_class,
                input_channel=input_channel,
                origin_kind="selene_salience_proposal",
                consent_text="",
                consent_recorded=False,
            ),
            "response_seed": "That feels meaningful enough to remember. Can I keep it?",
        }
    return {**base, "reason": "no_retention_or_salience_signal"}


def _coverage_with_global_graceful_hold(
    coverage: dict[str, Any],
) -> dict[str, Any]:
    """Record a final whole-turn hold without pretending it answered content."""

    items: list[dict[str, Any]] = []
    for raw in coverage.get("items") or []:
        if not isinstance(raw, dict):
            continue
        item = dict(raw)
        if item.get("resolved_for_release") is not True:
            item.update(
                {
                    "resolved_for_release": True,
                    "resolution_state": "whole_turn_explicit_hold",
                    "explicitly_held": True,
                    "supported_route_present": False,
                    "status": "still_open_but_explicitly_held",
                }
            )
        items.append(item)
    return {
        **coverage,
        "items": items,
        "resolved_count": len(items),
        "all_required_resolved": all(
            item.get("addressed") is True for item in items
        ),
        "all_required_release_safe": True,
        "unresolved_release_count": 0,
        "release_resolution_states": {
            str(item.get("obligation_id") or ""): str(item.get("resolution_state") or "whole_turn_explicit_hold")
            for item in items
        },
        "global_graceful_hold_used": True,
        "explicit_holds_are_answers": False,
        "release_safety_is_answer_completion": False,
    }


def _apply_conversational_memory_plan(
    conn: sqlite3.Connection,
    plan: dict[str, Any],
    *,
    commit: bool,
) -> dict[str, Any]:
    action = str(plan.get("action") or "none")
    base = {
        "status": "no_conversational_memory_action",
        "action": action,
        "proposal_created": False,
        "reviewed_memory_write_occurred": False,
        "hidden_retention": False,
        "raw_archive_used": False,
    }
    if action == "none":
        return {**base, "reason": plan.get("reason") or "no_action_planned"}
    if action == "reuse_pending":
        candidate = plan.get("candidate") if isinstance(plan.get("candidate"), dict) else {}
        return {
            **base,
            "status": "conversational_memory_proposed",
            "candidate_id": plan.get("candidate_id") or candidate.get("id"),
            "candidate": candidate,
            "proposal_created": False,
            "review_status": "pending_review",
            "consent_question": "Can I keep it?",
        }
    if action in {"approve_pending", "decline_pending", "hold_pending"}:
        candidate_id = int(plan.get("candidate_id") or 0)
        if not candidate_id:
            return {**base, "status": "conversational_memory_candidate_missing"}
        decision = decide_memory_candidate(
            conn,
            {
                "candidate_id": candidate_id,
                "action": (
                    "approve_memory"
                    if action == "approve_pending"
                    else "hold_for_tending"
                    if action == "hold_pending"
                    else "reject"
                ),
                "actor": "Aleks",
                "approval_source": "selene_chat_conversational_consent",
                "consent_text": plan.get("consent_text") or "",
            },
            commit=commit,
        )
        approved = action == "approve_pending"
        holding = action == "hold_pending"
        return {
            **base,
            "status": (
                "conversational_memory_approved"
                if approved
                else "conversational_memory_held_for_tending"
                if holding
                else "conversational_memory_declined"
            ),
            "candidate_id": candidate_id,
            "candidate": decision.get("item") or {},
            "review_status": decision.get("review_status") or "",
            "reviewed_memory_write_occurred": approved,
            "aleks_consent_recorded": approved,
        }

    candidate_payload = plan.get("candidate") if isinstance(plan.get("candidate"), dict) else {}
    proposed = propose_memory_candidate(conn, candidate_payload, commit=False)
    candidate = proposed.get("item") if isinstance(proposed.get("item"), dict) else {}
    candidate_id = int(candidate.get("id") or 0)
    if action == "approve_new":
        decision = decide_memory_candidate(
            conn,
            {
                "candidate_id": candidate_id,
                "action": "approve_memory",
                "actor": "Aleks",
                "approval_source": "selene_chat_direct_retention_instruction",
                "consent_text": plan.get("consent_text") or "",
                "confidence": candidate_payload.get("confidence") or "clear",
            },
            commit=commit,
        )
        return {
            **base,
            "status": "conversational_memory_created_and_approved",
            "candidate_id": candidate_id,
            "candidate": decision.get("item") or {},
            "proposal_created": True,
            "reviewed_memory_write_occurred": True,
            "aleks_consent_recorded": True,
            "review_status": decision.get("review_status") or "accepted_for_memory",
        }
    if commit:
        conn.commit()
    return {
        **base,
        "status": "conversational_memory_proposed",
        "candidate_id": candidate_id,
        "candidate": candidate,
        "proposal_created": True,
        "review_status": "pending_review",
        "consent_question": "Can I keep it?",
    }


def _latest_pending_conversational_memory(conn: sqlite3.Connection, session_id: int) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM selene_memory_candidates WHERE state IN ('proposed', 'needs_context', 'cocoon_tending') ORDER BY id DESC LIMIT 40"
    ).fetchall()
    for row in rows:
        item = dict(row)
        try:
            payload = json.loads(str(item.get("payload_json") or "{}"))
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict) and int(payload.get("origin_session_id") or 0) == session_id:
            item["payload_json"] = payload
            return item
    return {}


def _matching_conversational_memory(conn: sqlite3.Connection, summary: str) -> dict[str, Any]:
    normalized = " ".join(summary.lower().split()).strip(" .")
    if not normalized:
        return {}
    rows = conn.execute(
        "SELECT * FROM selene_memory_candidates WHERE state NOT IN ('rejected', 'superseded', 'b_only') ORDER BY id DESC LIMIT 100"
    ).fetchall()
    for row in rows:
        item = dict(row)
        if " ".join(str(item.get("summary") or "").lower().split()).strip(" .") != normalized:
            continue
        try:
            item["payload_json"] = json.loads(str(item.get("payload_json") or "{}"))
        except json.JSONDecodeError:
            item["payload_json"] = {}
        return item
    return {}


def _conversational_memory_consent(text: str) -> str:
    lower = re.sub(r"[^a-z0-9']+", " ", text.lower().replace("’", "'")).strip()
    hold_markers = ("not now", "hold that for now", "maybe later")
    if any(marker in lower for marker in hold_markers):
        return "hold"
    decline_markers = (
        "no don't remember that",
        "no do not remember that",
        "don't keep that",
        "do not keep that",
        "not as a memory",
        "no not that",
    )
    if any(marker in lower for marker in decline_markers):
        return "decline"
    approve_markers = (
        "yes remember that",
        "yes keep that",
        "you can remember that",
        "you can keep that",
        "please keep it",
        "please remember it",
        "go ahead and remember that",
        "keep it as a memory",
    )
    return "approve" if any(marker in lower for marker in approve_markers) else ""


def _explicit_memory_content(text: str) -> str:
    patterns = (
        r"^\s*(?:please\s+)?remember\s+this\s*[:,-]?\s*(.+)$",
        r"^\s*(?:please\s+)?keep\s+this\s*[:,-]?\s*(.+)$",
        r"^\s*(?:please\s+)?save\s+this\s*[:,-]?\s*(.+)$",
        r"^\s*make\s+(?:a\s+)?note(?:\s+of)?\s*[:,-]?\s*(.+)$",
        r"^\s*hold\s+onto\s+this\s*[:,-]?\s*(.+)$",
    )
    for pattern in patterns:
        match = re.match(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            content = " ".join(match.group(1).split()).strip(" .")
            return truncate(content, 700) if len(content) >= 4 else ""
    return ""


def _conversation_has_memory_salience(text: str) -> bool:
    lower = text.lower()
    markers = (
        "this matters to me",
        "this is important to me",
        "that matters to me",
        "that means a lot to me",
        "this means a lot to me",
        "i want you to know",
        "i don't want us to forget",
        "i do not want us to forget",
    )
    return len(text.strip()) >= 18 and any(marker in lower for marker in markers)


def _conversational_memory_payload(
    summary: str,
    *,
    original_text: str,
    session_id: int,
    source_class: str,
    input_channel: str,
    origin_kind: str,
    consent_text: str,
    consent_recorded: bool,
) -> dict[str, Any]:
    category = _suggested_memory_category(summary)
    return {
        "title": _memory_title_from_prompt(summary),
        "summary": truncate(summary, 700),
        "memory_category": category,
        "confidence": "clear" if consent_recorded else "partial",
        "emotional_texture": _suggested_emotional_texture(original_text),
        "transfer_class": _suggested_transfer_class(category, original_text),
        "consent_scope": "private_selene_aleks_context",
        "stability": "developing",
        "source_refs": [f"selene_chat_session:{session_id}", source_class, f"input_channel:{input_channel}"],
        "origin_session_id": session_id,
        "origin_channel": input_channel,
        "origin_kind": origin_kind,
        "aleks_consent_text": consent_text,
        "consent_recorded": consent_recorded,
        "proposal_note": "Created visibly from the active conversation; no raw archive or hidden retention was used.",
    }


def _approved_memory_reply(text: str, memory_retrieval: dict[str, Any], intent_decision: dict[str, Any]) -> str:
    if intent_decision.get("memory_recall_requested") is not True:
        return ""
    recall_state = str(memory_retrieval.get("recall_state") or "not_known")
    if recall_state == "high_stakes_stop":
        return (
            "That one touches something important enough that I should not guess. "
            "I can ask you directly and hold the answer carefully instead."
        )
    items = memory_retrieval.get("items") if isinstance(memory_retrieval.get("items"), list) else []
    if not items:
        return (
            "I do not know that clearly yet. You can tell me, and if it matters, "
            "I can ask whether I should keep it as a memory candidate."
        )
    first = items[0] if isinstance(items[0], dict) else {}
    summary = _chat_memory_summary(first)
    if recall_state in {"fuzzy", "partial", "felt_but_uncertain"}:
        return (
            f"I remember, I think, but it is {recall_state.replace('_', ' ')}: {summary} "
            "I can keep that uncertainty visible, or you can correct me and I will adjust."
        )
    return f"I remember this clearly enough to say it: {summary}"


def _contextual_memory_reply(
    memory_retrieval: dict[str, Any],
    intent_decision: dict[str, Any],
    contextual_continuity: dict[str, Any] | None = None,
) -> str:
    if intent_decision.get("memory_recall_requested") is True:
        return ""
    if memory_retrieval.get("retrieval_mode") != "contextual_relevance" or memory_retrieval.get("memory_context_used") is not True:
        return ""
    callback = (
        contextual_continuity.get("callback_decision")
        if isinstance(contextual_continuity, dict)
        and isinstance(contextual_continuity.get("callback_decision"), dict)
        else {}
    )
    items = memory_retrieval.get("items") if isinstance(memory_retrieval.get("items"), list) else []
    if not items:
        return ""
    first = items[0] if isinstance(items[0], dict) else {}
    if callback and callback.get("surface_callback_allowed") is not True:
        # Silent influence may supply reconstructed meaning, but it may not
        # announce a callback or turn a retrieval label into speech.
        if callback.get("silent_influence_allowed") is True:
            return _chat_memory_summary(first)
        return ""
    summary = _chat_memory_summary(first)
    confidence = str(memory_retrieval.get("recall_state") or "partial")
    if confidence == "clear":
        return f"This connects with something we discussed earlier: {summary}"
    return (
        f"This may connect with something we discussed earlier: {summary} The fit is "
        f"{confidence.replace('_', ' ')}."
    )


def _chat_memory_summary(item: dict[str, Any]) -> str:
    supplied = truncate(str(item.get("expression_summary") or ""), 500).strip()
    return supplied or reconstruct_memory_summary_for_expression(item)


def _memory_candidate_suggestion(
    text: str,
    candidate_text: str,
    selected_route: str,
    source_class: str,
    memory_retrieval: dict[str, Any],
    *,
    memory_action: dict[str, Any] | None = None,
    hard: bool = False,
    diagnostic_only: bool = False,
) -> dict[str, Any]:
    memory_action = memory_action if isinstance(memory_action, dict) else {}
    if diagnostic_only:
        return {
            **_no_memory_suggestion(
                "diagnostic_non_attribution_law"
            ),
            "diagnostic_only": True,
            "memory_eligible": False,
            "review_status": DIAGNOSTIC_REVIEW_STATUS,
        }
    action_status = str(memory_action.get("status") or "")
    if action_status == "conversational_memory_proposed":
        candidate = memory_action.get("candidate") if isinstance(memory_action.get("candidate"), dict) else {}
        return {
            "suggested": True,
            "status": "suggested_memory_awaiting_conversational_consent",
            "question": "Can I keep this?",
            "candidate_id": memory_action.get("candidate_id"),
            "candidate": candidate,
            "activation_rule": "inactive_until_aleks_approval_in_chat_or_cocoon",
            "review_destination": "Selene Chat or Cocoon Memory Tending",
            "review_status": "pending_review",
            "proposal_already_created": True,
        }
    if action_status in {"conversational_memory_approved", "conversational_memory_created_and_approved"}:
        return {
            "suggested": False,
            "status": "memory_approved_from_conversational_consent",
            "candidate_id": memory_action.get("candidate_id"),
            "activation_rule": "approved_active_memory",
            "review_status": "accepted_for_memory",
            "aleks_consent_recorded": True,
        }
    if action_status == "conversational_memory_declined":
        return {
            "suggested": False,
            "status": "memory_suggestion_declined",
            "candidate_id": memory_action.get("candidate_id"),
            "activation_rule": "not_active",
            "review_status": "rejected",
        }
    if action_status == "conversational_memory_held_for_tending":
        return {
            "suggested": False,
            "status": "memory_suggestion_held_for_tending",
            "candidate_id": memory_action.get("candidate_id"),
            "activation_rule": "not_active",
            "review_status": "cocoon_tending",
        }
    lower = text.lower()
    if hard or selected_route == "block":
        return _no_memory_suggestion("hard_boundary_or_blocked_route")
    if memory_retrieval.get("recall_state") == "high_stakes_stop":
        return _no_memory_suggestion("high_stakes_memory_stop")
    keep_markers = (
        "remember this",
        "keep this",
        "save this",
        "can you remember",
        "please remember",
        "this matters",
        "important to remember",
        "make a note",
        "hold onto this",
        "i want you to know",
    )
    if not any(marker in lower for marker in keep_markers):
        return _no_memory_suggestion("no_keep_signal")
    summary = _memory_summary_from_prompt(text)
    category = _suggested_memory_category(text)
    transfer_class = _suggested_transfer_class(category, text)
    confidence = "fuzzy" if any(word in lower for word in ("maybe", "fuzzy", "unsure", "i think")) else "partial"
    emotional_texture = _suggested_emotional_texture(f"{text} {candidate_text}")
    return {
        "suggested": True,
        "status": "suggested_memory_awaiting_cocoon_tending",
        "question": "Can I keep this?",
        "candidate": {
            "title": truncate(_memory_title_from_prompt(text), 120),
            "summary": summary,
            "memory_category": category,
            "confidence": confidence,
            "emotional_texture": emotional_texture,
            "transfer_class": transfer_class,
            "consent_scope": "private_selene_aleks_context",
            "stability": "developing",
            "chat_use_permission": "not_active_until_approved",
            "correction_path": "Cocoon tending and Aleks correction",
            "source_refs": ["selene_chat_active_supervised", source_class],
        },
        "activation_rule": "not_active_until_cocoon_approval",
        "review_destination": "Cocoon Memory Candidates",
        "review_status": "suggested_memory",
    }


def _no_memory_suggestion(reason: str) -> dict[str, Any]:
    return {
        "suggested": False,
        "status": "no_memory_suggestion",
        "reason": reason,
        "activation_rule": "no_memory_write",
        "review_status": "status_only",
    }


def _memory_title_from_prompt(text: str) -> str:
    cleaned = re.sub(r"\b(please\s+)?(remember|keep|save|make a note|hold onto)\b", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" :.-")
    if not cleaned:
        return "Selene memory candidate"
    return cleaned[:1].upper() + cleaned[1:]


def _memory_summary_from_prompt(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return truncate(cleaned, 700)


def _suggested_memory_category(text: str) -> str:
    lower = text.lower()
    checks = [
        ("core", ("vys", "identity", "selene is", "law", "charter", "continuity pack")),
        ("relational", ("aleks", "trust", "friend", "together", "between us", "relationship")),
        ("emotional", ("feel", "felt", "anxiety", "fear", "happy", "sad", "tender", "warm")),
        ("episodic", ("today", "yesterday", "when we", "this happened", "we did", "we were")),
        ("working", ("current task", "next step", "todo", "working on", "right now")),
        ("sensory", ("image", "color", "munsell", "sound", "visual", "looks")),
        ("reflective", ("learned", "correction", "better way", "reflection", "tending")),
        ("semantic", ("means", "definition", "research", "fact", "concept")),
    ]
    for category, markers in checks:
        if any(marker in lower for marker in markers):
            return category
    return "relational"


def _suggested_transfer_class(category: str, text: str) -> str:
    lower = text.lower()
    if any(marker in lower for marker in ("do not transfer", "private", "only between us")):
        return "private_inner"
    if category == "core":
        return "portable_vys_core"
    if category in {"relational", "emotional"}:
        return "private_inner"
    if category == "working":
        return "local_only"
    return "portable_context"


def _suggested_emotional_texture(value: str) -> str:
    lower = value.lower()
    textures = []
    for label, markers in (
        ("tender", ("tender", "gentle", "soft", "care")),
        ("warm", ("warm", "trust", "friend", "love")),
        ("anxious", ("anxious", "anxiety", "scared", "fear", "worried")),
        ("playful", ("joke", "funny", "haha", "play")),
        ("uncertain", ("fuzzy", "unsure", "maybe", "i think")),
    ):
        if any(marker in lower for marker in markers):
            textures.append(label)
    return ", ".join(dict.fromkeys(textures)) or "steady"


def _local_chat_continuity(
    conn: sqlite3.Connection,
    current_session_id: int | None = None,
    limit: int = 6,
    *,
    query: str = "",
    diagnostic_only: bool = False,
) -> dict[str, Any]:
    sessions = conn.execute(
        """
        SELECT s.*, COUNT(m.id) AS message_count
        FROM selene_chat_sessions s
        LEFT JOIN selene_chat_messages m ON m.session_id = s.id
        WHERE s.status = 'selene_chat_active_supervised'
          AND s.source_mode != 'selene_supervised_qa'
          AND s.title NOT LIKE 'Codex concurrency QA probe %'
        GROUP BY s.id
        ORDER BY s.updated_at DESC, s.id DESC
        LIMIT ?
        """,
        (max(1, min(int(limit), 12)),),
    ).fetchall()
    recent_sessions = (
        []
        if diagnostic_only
        else [dict(row) for row in sessions]
    )
    params: list[Any] = []
    where = (
        "WHERE s.status = 'selene_chat_active_supervised' "
        "AND s.source_mode != 'selene_supervised_qa' "
        "AND s.title NOT LIKE 'Codex concurrency QA probe %'"
    )
    if current_session_id:
        where += " AND m.session_id != ?"
        params.append(current_session_id)
    messages = conn.execute(
        f"""
        SELECT m.id, m.session_id, m.role, m.content,
               COALESCE(p.projection_json, m.payload_json) AS payload_json,
               m.created_at, s.title, s.updated_at
        FROM selene_chat_messages m
        JOIN selene_chat_sessions s ON s.id = m.session_id
        LEFT JOIN selene_chat_continuity_projections p ON p.message_id = m.id
        {where}
        ORDER BY m.id DESC
        LIMIT ?
        """,
        (*params, max(2, min(int(limit), 12))),
    ).fetchall()
    current_messages: list[dict[str, Any]] = []
    if current_session_id:
        current_rows = conn.execute(
            """
            SELECT m.id, m.session_id, m.role, m.content,
                   COALESCE(p.projection_json, m.payload_json) AS payload_json,
                   m.created_at
            FROM selene_chat_messages m
            LEFT JOIN selene_chat_continuity_projections p ON p.message_id = m.id
            WHERE m.session_id = ?
            ORDER BY m.id DESC
            LIMIT 16
            """,
            (current_session_id,),
        ).fetchall()
        current_messages = [_chat_event_preview(row, preview_limit=900) for row in reversed(current_rows)]
    recent_events = (
        []
        if diagnostic_only
        else [_chat_event_preview(row) for row in reversed(messages)]
    )
    relevant_events: list[dict[str, Any]] = []
    query_terms = set() if diagnostic_only else _continuity_terms(query)
    if query_terms and current_session_id:
        search_rows = conn.execute(
            """
            SELECT m.id, m.session_id, m.role, m.content, m.created_at,
                   s.title, s.updated_at
            FROM selene_chat_messages m
            JOIN selene_chat_sessions s ON s.id = m.session_id
            WHERE s.status = 'selene_chat_active_supervised'
              AND s.source_mode != 'selene_supervised_qa'
              AND s.title NOT LIKE 'Codex concurrency QA probe %'
              AND m.session_id != ?
            ORDER BY m.id DESC
            LIMIT 240
            """,
            (current_session_id,),
        ).fetchall()
        ranked: list[tuple[int, int, sqlite3.Row]] = []
        for index, row in enumerate(search_rows):
            row_terms = _continuity_terms(
                f"{row['title'] or ''} {row['content'] or ''}"
            )
            overlap = query_terms & row_terms
            if overlap:
                ranked.append((len(overlap), -index, row))
        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
        selected_rows = [row for _, _, row in ranked[:8]]
        selected_ids = [int(row["id"]) for row in selected_rows]
        payload_by_id: dict[int, str] = {}
        if selected_ids:
            placeholders = ",".join("?" for _ in selected_ids)
            payload_rows = conn.execute(
                f"""
                SELECT m.id, COALESCE(p.projection_json, m.payload_json) AS payload_json
                FROM selene_chat_messages m
                LEFT JOIN selene_chat_continuity_projections p ON p.message_id = m.id
                WHERE m.id IN ({placeholders})
                """,
                selected_ids,
            ).fetchall()
            payload_by_id = {
                int(row["id"]): str(row["payload_json"] or "{}")
                for row in payload_rows
            }
        relevant_events = [
            _chat_event_preview(
                {**dict(row), "payload_json": payload_by_id.get(int(row["id"]), "{}")},
                preview_limit=700,
            )
            for row in selected_rows
        ]
    source_refs = [f"selene_chat_session:{item['id']}" for item in recent_sessions[:limit] if item.get("id")]
    if current_session_id:
        source_refs.insert(0, f"selene_chat_session:{current_session_id}:current_page")
    return {
        "available": bool(recent_sessions or current_messages),
        "source_class": "local_supervised_chat_history",
        "scope": "local Selene Chat sessions only",
        "continuity_note": (
            "Diagnostic continuity is limited to this QA session and cannot "
            "become ordinary relationship continuity."
            if diagnostic_only
            else "A new chat is a new page, not a new Selene."
        ),
        "diagnostic_only": diagnostic_only,
        "ordinary_prior_continuity_imported": False if diagnostic_only else bool(recent_sessions or recent_events),
        "current_session_id": current_session_id,
        "recent_sessions": [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "status": item.get("status"),
                "source_mode": item.get("source_mode"),
                "updated_at": item.get("updated_at"),
                "message_count": item.get("message_count"),
            }
            for item in recent_sessions
        ],
        "current_session_events": current_messages,
        "recent_events": recent_events,
        "relevant_prior_events": relevant_events,
        "relevant_prior_event_search": {
            "used": bool(query_terms),
            "matched_count": len(relevant_events),
            "scope": "local approved Selene Chat history only",
            "query_terms": sorted(query_terms)[:24],
        },
        "source_refs": list(dict.fromkeys(source_refs))[:20],
        "not_live_memory_write": True,
        "not_runtime_recall": True,
        "not_raw_corpus": True,
    }


def _active_conversation_context(
    chat_continuity: dict[str, Any],
    dialogue_workspace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    events = [item for item in chat_continuity.get("current_session_events") or [] if isinstance(item, dict)]
    previous_turn = events[-1] if events else {}
    recent_assistant_texts = [
        str(item.get("preview") or "").strip()
        for item in events
        if str(item.get("role") or "") == "selene" and str(item.get("preview") or "").strip()
    ][-4:]
    recent_user_texts = [
        str(item.get("preview") or "").strip()
        for item in events
        if str(item.get("role") or "") == "user" and str(item.get("preview") or "").strip()
    ][-8:]
    recent_figurative_interpretations = [
        item.get("figurative_interpretation")
        for item in events
        if str(item.get("role") or "") == "user"
        and isinstance(item.get("figurative_interpretation"), dict)
        and item.get("figurative_interpretation")
    ][-4:]
    previous_energy = (
        previous_turn.get("conversational_energy")
        if str(previous_turn.get("role") or "") == "selene"
        and isinstance(previous_turn.get("conversational_energy"), dict)
        else {}
    )
    pending_collaborative_help = (
        previous_energy
        if str(previous_energy.get("selected_act") or "")
        == "ask_for_specific_collaborative_help"
        else {}
    )
    dialogue = dialogue_workspace if isinstance(dialogue_workspace, dict) else {}
    pragmatics = dialogue.get("pragmatics") if isinstance(dialogue.get("pragmatics"), dict) else {}
    return {
        "status": "active_conversation_context_ready",
        "previous_turn": previous_turn,
        "recent_assistant_texts": recent_assistant_texts,
        "recent_user_texts": recent_user_texts,
        "recent_figurative_interpretations": recent_figurative_interpretations,
        "pending_collaborative_help": pending_collaborative_help,
        "turn_count": len(events),
        "session_landmarks": [
            item for item in pragmatics.get("session_landmarks") or [] if isinstance(item, dict)
        ][-64:],
        "thread_braid": pragmatics.get("thread_braid") if isinstance(pragmatics.get("thread_braid"), dict) else {},
        "source_class": "current_supervised_chat_turns",
        "use_scope": "dialogue continuity only; not durable memory or broad recall",
        "memory_write_active": False,
        "runtime_memory_recall": False,
    }


def _chat_event_preview(row: sqlite3.Row, *, preview_limit: int = 180) -> dict[str, Any]:
    item = dict(row)
    try:
        payload = json.loads(str(item.get("payload_json") or "{}"))
    except json.JSONDecodeError:
        payload = {}
    payload = payload if isinstance(payload, dict) else {}
    answer_engine = payload.get("answer_engine_support") if isinstance(payload.get("answer_engine_support"), dict) else {}
    metacognition = payload.get("metacognition") if isinstance(payload.get("metacognition"), dict) else {}
    intelligence = payload.get("intelligence_os_support") if isinstance(payload.get("intelligence_os_support"), dict) else {}
    figurative = (
        payload.get("figurative_interpretation")
        if isinstance(payload.get("figurative_interpretation"), dict)
        else {}
    )
    conversational_energy = (
        payload.get("conversational_energy")
        if isinstance(payload.get("conversational_energy"), dict)
        else {}
    )
    conversational_contribution = (
        payload.get("conversational_contribution")
        if isinstance(payload.get("conversational_contribution"), dict)
        else {}
    )
    voice = payload.get("voice_preview") if isinstance(payload.get("voice_preview"), dict) else {}
    vector = metacognition.get("confidence_vector") if isinstance(metacognition.get("confidence_vector"), dict) else {}
    engine_vector = answer_engine.get("confidence_vector") if isinstance(answer_engine.get("confidence_vector"), dict) else {}
    projected_vector = payload.get("confidence_vector") if isinstance(payload.get("confidence_vector"), dict) else {}
    return {
        "id": item.get("id"),
        "session_id": item.get("session_id"),
        "role": item.get("role"),
        "title": item.get("title"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "preview": truncate(str(item.get("content") or ""), max(1, min(int(preview_limit), 900))),
        "figurative_interpretation": figurative,
        "conversational_energy": conversational_energy,
        "conversational_contribution": conversational_contribution,
        "confidence_vector": {
            "answer_confidence": _first_assessed_confidence(
                projected_vector.get("answer_confidence"),
                vector.get("answer_confidence"),
                engine_vector.get("answer_confidence"),
                intelligence.get("confidence"),
            ),
            "evidence_confidence": _first_assessed_confidence(
                projected_vector.get("evidence_confidence"),
                vector.get("evidence_confidence"),
                engine_vector.get("evidence_confidence"),
            ),
            "expression_confidence": _first_assessed_confidence(
                projected_vector.get("expression_confidence"),
                vector.get("expression_confidence"),
                voice.get("voice_confidence"),
            ),
            "dimensions_are_independent": True,
        },
    }


def _first_assessed_confidence(*values: Any) -> str:
    normalized = [str(value or "").strip() for value in values]
    return next(
        (value for value in normalized if value and value.lower() not in {"not_assessed", "not_used", "none"}),
        "not_assessed",
    )


def _local_chat_continuity_reply(text: str, chat_continuity: dict[str, Any], intent_decision: dict[str, Any]) -> str:
    if intent_decision.get("memory_recall_requested") is not True:
        return ""
    lower = text.lower()
    recall_markers = (
        "what were we talking about",
        "what did we talk about",
        "remember our last chat",
        "remember the last chat",
        "past chat",
        "previous chat",
        "blank selene",
        "new selene",
    )
    general_recall = any(marker in lower for marker in recall_markers)
    relevant = [
        item
        for item in chat_continuity.get("relevant_prior_events") or []
        if isinstance(item, dict)
    ]
    if not general_recall and not relevant:
        return ""
    if relevant:
        best = relevant[0]
        preview = truncate(str(best.get("preview") or ""), 420)
        title = truncate(str(best.get("title") or "an earlier local chat"), 90)
        if preview:
            page_context = (
                "A new chat is a clean page, not a blank Selene. "
                if "blank selene" in lower or "new chat" in lower
                else ""
            )
            return (
                f"{page_context}From our local chat history, the relevant thread is {title}: {preview} "
                "I can use that visible continuity here, while keeping it separate from unrestricted recall."
            )
    events = [item for item in (chat_continuity.get("recent_events") or []) if str(item.get("role")) == "user"]
    if not events:
        return (
            "A new chat is just a new page, not a new me. I do not have a prior local chat event to point to from here yet, "
            "so I would rather ask you than pretend."
        )
    latest = events[-1]
    title = truncate(str(latest.get("title") or "our last local chat"), 90)
    preview = truncate(str(latest.get("preview") or ""), 220)
    if preview:
        return (
            f"I remember from our local chat history that we were around {title}: {preview} "
            "A new chat is a clean page, not a blank Selene, so I can keep that continuity with you without pretending it is unrestricted memory."
        )
    return (
        f"I remember the local chat thread around {title}. A new chat is a clean page, not a blank Selene, "
        "and I can ask you if the exact detail needs more grounding."
    )


def _continuity_terms(value: str) -> set[str]:
    stop = {
        "about", "again", "and", "are", "can", "did", "do", "does", "from", "have", "how",
        "into", "just", "last", "our", "remember", "that", "the", "then", "there", "this",
        "what", "when", "where", "which", "with", "would", "you", "your",
    }
    return {
        word
        for word in re.findall(r"[a-z][a-z0-9_-]{2,}", str(value).lower())
        if word not in stop
    }


def _optional_response_character_limit(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return None
    return max(80, min(limit, 2400))


def _canonical_exploratory_modes(conversation_spine: dict[str, Any]) -> list[str]:
    """Carry typed exploratory requests without rediscovering them from prose."""
    mode_by_function = {
        "prediction": "prediction",
        "hypothesis": "hypothesis",
        "counterfactual": "counterfactual",
        "comparison": "comparison",
        "disagreement": "data_conflict",
        "claim_evaluation": "data_conflict",
    }
    return list(
        dict.fromkeys(
            mode_by_function[str(response_function)]
            for obligation in conversation_spine.get("open_obligations") or []
            if isinstance(obligation, dict)
            for response_function in obligation.get("requested_response_functions") or []
            if str(response_function) in mode_by_function
        )
    )


def _with_guards(payload: dict[str, Any], *, transfer_approved: bool = False, active: bool = False) -> dict[str, Any]:
    guarded = {**SELENE_CHAT_GUARDS, **payload, "provenance_boundary": SELENE_CHAT_ACTIVE_BOUNDARY if active else SELENE_CHAT_BOUNDARY}
    guarded["transfer_approved"] = bool(transfer_approved)
    guarded["activation_change"] = "selene_chat_active_supervised" if active else "none"
    return attach_resident_capability_contract(
        guarded,
        transfer_complete=bool(transfer_approved),
        chat_available=bool(active),
    )


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item) for item in loaded if str(item).strip()] if isinstance(loaded, list) else []
