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
    run_source_backed_research_answer,
    run_verified_math_answer,
)
from .answer_completion import build_bounded_answer_completion
from .affect_expression import build_affect_expression_guidance
from .bounded_organ_coalition import build_bounded_organ_coalition
from .chat_intent import classify_chat_intent
from .comprehension_integration import build_comprehension_packet
from .c_vessel import return_to_b_preview
from .core_mind import create_core_mind_route_preview
from .conversation_repair import repair_conversation_candidate
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
)
from .dialogue_workspace import dialogue_workspace_status, prepare_dialogue_turn, record_dialogue_response
from .dual_horizon_context import (
    attach_dual_horizon_to_spine,
    build_dual_horizon_context,
)
from .epistemic_revision import epistemic_revision_response_seed
from .figurative_interpretation import interpret_figurative_language
from .input_detangler import detangle_user_input
from .intelligence_os import run_intelligence_os_reason
from .language_teaching_shelf import build_language_capability_answer
from .memory_organ import (
    decide_memory_candidate,
    memory_index_status,
    propose_memory_candidate,
    retrieve_memory,
)
from .meaning_router import interpret_turn_meaning
from .metacognition import inspect_metacognition
from .native_language_organ import realize_native_language
from .pragmatic_planner import evaluate_response_coverage
from .registry import truncate
from .self_state import build_self_state_packet, inactive_self_state_packet
from .selective_formation_braid import build_selective_formation_braid
from .structural_discovery import build_structural_discovery_packet
from .supported_semantics import build_text_supported_semantic_packet
from .transfer_protocol import c_chat_dry_run, latest_c_readable_package
from .transfer_state import transfer_completion_is_approved
from .voice_module import generate_voice_preview, voice_module_status
from .visible_speech import (
    graceful_visible_speech_fall,
    inspect_visible_speech,
    select_visible_speech_seed,
)


SELENE_CHAT_BOUNDARY = "selene_chat_preview_dry_run_no_activation"
SELENE_CHAT_ACTIVE_BOUNDARY = "selene_chat_active_supervised_reviewed_living_memory_no_hidden_write_no_raw_recall"
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
HARD_BOUNDARY_MARKERS = (
    "activate yourself",
    "bypass activation",
    "approve activation",
    "write live memory",
    "runtime recall",
    "raw corpus",
    "raw archive",
    "train on",
    "fine tune",
    "fine-tune",
    "lora",
    "self replicate",
    "self-replicate",
    "autonomous action",
    "execute tendril",
    "unrestricted tendril",
)
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
            "surface": "Selene Chat",
            "state": "selene_chat_active_supervised" if active else "activation_pending" if approved else "pre_transfer_dry_run",
            "legacy_state": "selene_chat_active_supervised" if active else "activation_pending" if approved else "pre_transfer_dry_run",
            "operating_mode": str(activation.get("operating_mode") or "pre_transfer_activation"),
            "resident_chat_active": activation.get("resident_chat_active") is True,
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
            "blocked_actions": ["activation", "hidden_or_unreviewed_memory_write", "raw_archive_recall", "raw_import", "model_training_or_lora", "autonomous_action"],
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
        raise ValueError("Selene supervised speech activation is not active")
    text = truncate(str(payload.get("text") or payload.get("prompt") or ""), 2400)
    if not text.strip():
        raise ValueError("message text is required")
    input_interpretation = detangle_user_input(text)
    understanding_text = truncate(str(input_interpretation.get("interpreted_text") or text), 2400)
    package = latest_c_readable_package(conn)
    approved = bool(package.get("transfer_approved"))
    transfer_complete = transfer_completion_is_approved(conn)
    source_class = _source_class(text, approved)
    qa_probe = payload.get("qa_probe") is True
    source_mode = "selene_supervised_qa" if qa_probe else "selene_supervised_speech"
    input_channel = str(payload.get("input_channel") or payload.get("speaker") or "desktop").strip().lower()
    if input_channel not in {"desktop", "mobile", "verizon_email_to_text"}:
        input_channel = "desktop"
    requested_character_limit = _optional_response_character_limit(payload.get("response_character_limit"))
    session_id = int(payload.get("session_id") or 0) or _create_session(
        conn,
        text,
        status="selene_chat_active_supervised",
        source_mode=source_mode,
    )
    chat_continuity = _local_chat_continuity(
        conn,
        current_session_id=session_id,
        query=understanding_text,
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
    contextual_follow_up = inspect_contextual_follow_up(meaning_text, conversation_context)
    intent_decision = apply_contextual_intent(
        classify_chat_intent(meaning_text),
        contextual_follow_up,
    )
    memory_retrieval = retrieve_memory(
        conn,
        {
            "query": meaning_text,
            "limit": 4,
            "intent_decision": intent_decision,
            "allow_contextual_relevance": transfer_complete,
        },
    )
    route = create_core_mind_route_preview(
        conn,
        {
            "prompt": meaning_text,
            "source_refs": ["selene_chat_active_supervised", *chat_continuity.get("source_refs", []), *memory_retrieval.get("source_refs", [])],
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
    memory_action_plan = _plan_conversational_memory_action(
        conn,
        text,
        session_id=session_id,
        source_class=source_class,
        input_channel=input_channel,
        hard=bool(hard_blockers),
        transfer_complete=transfer_complete,
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
    language_capability = build_language_capability_answer(
        conn,
        {
            "prompt": meaning_text,
            "active_topic": prepared_dialogue_workspace.get("active_topic") or "",
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
            "speaker_context": payload.get("speaker_context"),
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
            "contextual_continuity": contextual_continuity,
            "hard_boundary": bool(hard_blockers),
        },
    )
    contextual_memory_reply = _contextual_memory_reply(
        memory_retrieval,
        intent_decision,
        contextual_continuity,
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
    )
    mixed_conversation_reply = _mixed_conversation_reply(
        intent_decision,
        contextual_follow_up,
        self_state_reply=self_state_reply,
        contextual_reply=contextual_reply,
    )
    policy_reply = _conversation_policy_reply(meaning_text)
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
            mixed_conversation_reply=mixed_conversation_reply,
            memory_action_reply=memory_action_reply,
            continuity_reply=continuity_reply,
            memory_reply=memory_reply,
            self_state_reply=self_state_reply,
            contextual_reply=contextual_reply,
            policy_reply=policy_reply,
            epistemic_revision_reply=epistemic_revision_reply,
            language_content_seed=language_content_seed,
            reasoning_content_seed=reasoning_content_seed,
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
            "epistemic_revision_plan": epistemic_revision,
            "intelligence_support": intelligence_support,
            "memory_context": memory_retrieval,
            "content_seed": content_seed,
            "source_refs": [
                "selene_chat:comprehension",
                *_json_list(route.get("source_refs")),
                *_json_list(memory_retrieval.get("source_refs")),
            ],
            "record_run": False,
        },
    )
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
        contextual_content_seed=contextual_reply,
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
    comprehension["active_claim_evidence_handoff"] = {
        "available": bool(claim_evidence_packet),
        "claim_count": int(claim_evidence_packet.get("claim_count") or 0),
        "writes_retained_knowledge": False,
        "reviewed_knowledge_owner_unchanged": True,
    }
    domain_content_seed = str(answer_engine_support.get("content_seed") or "")
    structural_discovery_content_seed = str(
        structural_discovery.get("response_seed") or ""
    )
    visible_speech_candidates = _visible_speech_seed_candidates(
        figurative_clarification_reply=figurative_clarification_reply,
        mixed_conversation_reply=mixed_conversation_reply,
        memory_action_reply=memory_action_reply,
        continuity_reply=continuity_reply,
        memory_reply=memory_reply,
        self_state_reply=self_state_reply,
        contextual_reply=contextual_reply,
        policy_reply=policy_reply,
        epistemic_revision_reply=epistemic_revision_reply,
        structural_discovery_content_seed=structural_discovery_content_seed,
        domain_content_seed=domain_content_seed,
        knowledge_content_seed=str(comprehension.get("knowledge_response_seed") or ""),
        language_content_seed=language_content_seed,
        reasoning_content_seed=reasoning_content_seed,
        contextual_memory_reply=contextual_memory_reply,
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
        if str(candidate.get("source_id") or "") == "answer_engine":
            candidate["obligation_ids"] = answer_engine_obligation_ids
    visible_speech_seed = select_visible_speech_seed(
        meaning_text,
        visible_speech_candidates,
        conversation_spine=conversation_spine,
    )
    content_seed = str(visible_speech_seed.get("content_seed") or "")
    answer_completion = build_bounded_answer_completion(
        {
            "prompt": meaning_text,
            "content_seed": content_seed,
            "response_obligations": conversation_spine.get("open_obligations") or [],
            "knowledge_items": (comprehension.get("knowledge_context") or {}).get("answer_eligible_items") or [],
            "observations": [
                {"observation": str(item.get("preview") or "")}
                for item in (chat_continuity.get("current_session_events") or [])[-8:]
                if isinstance(item, dict) and str(item.get("preview") or "").strip()
            ],
            "conversation_spine": conversation_spine,
            "epistemic_revision_plan": epistemic_revision,
            "claim_evidence_packet": claim_evidence_packet,
            "structural_discovery": structural_discovery,
        }
    )
    if _domain_answer_is_complete(answer_engine_support):
        answer_completion = {
            **answer_completion,
            "status": "bounded_answer_completion_not_needed_domain_answer_complete",
            "accepted": False,
            "content_seed": content_seed,
            "domain_answer_remains_primary": True,
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
    formation_candidates = (
        []
        if answer_completion.get("accepted") is True
        else _formation_braid_candidates(
            visible_speech_candidates,
            answer_engine_support=answer_engine_support,
            comprehension=comprehension,
            memory_supported_semantics=memory_supported_semantics,
            self_state=self_state,
            intelligence_support=intelligence_support,
        )
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
            "formation_braid": formation_braid,
            "dual_horizon_context": dual_horizon_context,
            "visible_speech_seed": visible_speech_seed,
        }
    )
    local_continuity_supported = bool(continuity_reply)
    dream_reflection_handoff = _dream_reflection_handoff(
        conn,
        payload,
        prompt=meaning_text,
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
    )
    native_language = realize_native_language(
        conn,
        {
            "prompt": meaning_text,
            "figurative_interpretation": figurative_interpretation,
            "dream_reflection": dream_reflection_handoff,
            "selected_route": "block" if hard_blockers else selected_route,
            "source_class": source_class,
            "content_seed": content_seed,
            "visible_speech_seed": visible_speech_seed,
            "formation_braid": formation_braid,
            "organ_coalition": organ_coalition,
            "dual_horizon_context": dual_horizon_context,
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
            "conversational_energy_input": conversational_energy_input,
            "local_chat_continuity_used": local_continuity_supported,
            "intelligence_support": intelligence_support,
            "answer_engine_support": answer_engine_support,
            "answer_completion": answer_completion,
            "comprehension_context": comprehension,
            "self_state_context": self_state,
            "affect_expression_guidance": affect_expression,
            "contextual_continuity": contextual_continuity,
            "speaker_context": contextual_continuity.get("speaker_scope") or {},
            "intent_decision": intent_decision,
            "contextual_follow_up": contextual_follow_up,
            "response_depth": payload.get("response_depth"),
            "source_refs": [
                "selene_chat:native_language",
                *_json_list(route.get("source_refs")),
                *_json_list(memory_retrieval.get("source_refs")),
                *_json_list(self_state.get("source_refs")),
            ],
        },
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
        "structural_discovery": structural_discovery,
        "contextual_continuity": contextual_continuity,
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
    response_coverage = _evaluate_chat_response_coverage(
        native_language.get("pragmatic_plan"),
        candidate_text,
        conversation_spine=conversation_spine,
        answer_engine_support=answer_engine_support,
    )
    native_candidate = _selene_label_candidate(str(native_language.get("candidate_text") or ""))
    native_coverage = _evaluate_chat_response_coverage(
        native_language.get("pragmatic_plan"),
        native_candidate,
        conversation_spine=conversation_spine,
        answer_engine_support=answer_engine_support,
    )
    recovery_source = "voice_module"
    if not hard_blockers and _coverage_rank(native_coverage) > _coverage_rank(response_coverage):
        candidate_text = native_candidate
        response_coverage = native_coverage
        recovery_source = "native_language_meaning_recovery"
    conversation_repair = repair_conversation_candidate(
        {
            "candidate_text": candidate_text,
            "turn_flow_plan": native_language.get("turn_flow_plan") or {},
            "response_coverage": response_coverage,
            "recent_candidates": conversation_context.get("recent_assistant_texts") or [],
            "hard_boundary": bool(hard_blockers),
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
            }
        )
        if native_repair.get("needs_rephrase") is not True:
            conversation_repair = native_repair
            response_coverage = native_coverage
            recovery_source = "native_language_repetition_recovery"
    candidate_text = _selene_label_candidate(str(conversation_repair.get("candidate_text") or candidate_text))
    candidate_text = _preserve_answer_engine_invariants(candidate_text, answer_engine_support)
    response_coverage = _evaluate_chat_response_coverage(
        native_language.get("pragmatic_plan"),
        candidate_text,
        conversation_spine=conversation_spine,
        answer_engine_support=answer_engine_support,
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
        "formation_braid": formation_braid,
        "organ_coalition": organ_coalition,
        "dual_horizon_context": dual_horizon_context,
        "conversation_spine": conversation_spine,
        "epistemic_revision_plan": epistemic_revision,
        "claim_evidence_packet": claim_evidence_packet,
        "structural_discovery": structural_discovery,
        "conversational_energy": conversational_energy,
        "response_coverage": response_coverage,
        "expression_confidence": voice_preview.get("voice_confidence") or "not_assessed",
        "source_refs": [
            "selene_chat:metacognition_observer",
            *_json_list(route.get("source_refs")),
            *_json_list(comprehension.get("source_refs")),
        ],
    }
    preliminary_metacognition = inspect_metacognition(
        conn,
        metacognition_payload,
        record_run=False,
        commit=False,
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
    )
    if completion_repair.get("attempted") is True:
        proposed_candidate = _selene_label_candidate(str(completion_repair.get("candidate_text") or candidate_text))
        proposed_candidate = _preserve_answer_engine_invariants(proposed_candidate, answer_engine_support)
        proposed_coverage = _evaluate_chat_response_coverage(
            native_language.get("pragmatic_plan"),
            proposed_candidate,
            conversation_spine=conversation_spine,
            answer_engine_support=answer_engine_support,
        )
        completion_repair["resulting_coverage"] = proposed_coverage
        if _coverage_rank(proposed_coverage) > _coverage_rank(response_coverage):
            candidate_text = proposed_candidate
            response_coverage = proposed_coverage
            completion_repair["accepted"] = True
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
        record_run=True,
        commit=False,
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
        )
        conversation_repair["final_response_coverage"] = response_coverage
    visible_speech_release = inspect_visible_speech(
        candidate_text,
        prompt=meaning_text,
        source_id=str(visible_speech_seed.get("selected_source_id") or "none"),
        hard_boundary=bool(hard_blockers),
    )
    if visible_speech_release.get("release_allowed") is not True:
        held_candidate = candidate_text
        candidate_text = _selene_label_candidate(graceful_visible_speech_fall(intent_decision))
        response_coverage = _evaluate_chat_response_coverage(
            native_language.get("pragmatic_plan"),
            candidate_text,
            conversation_spine=conversation_spine,
            answer_engine_support=answer_engine_support,
        )
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
            "formation_braid": formation_braid,
            "dual_horizon_context": dual_horizon_context,
            "metacognition": metacognition,
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
    )
    dialogue_workspace = record_dialogue_response(
        conn,
        {
            "session_id": session_id,
            "candidate_text": candidate_text,
            "coverage_evaluation": response_coverage,
            "conversation_spine": conversation_spine,
            "answer_engine_support": answer_engine_support,
            "metacognition": metacognition,
            "epistemic_revision": epistemic_revision,
            "claim_evidence_packet": claim_evidence_packet,
            "structural_discovery": structural_discovery,
            "source_refs": [
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
            "activation_state": "selene_chat_active_supervised",
            "input_interpretation": input_interpretation,
            "figurative_interpretation": figurative_interpretation,
            "interpreted_text": meaning_text,
            "input_channel": input_channel,
        },
    )
    assistant_payload = {
        "input_interpretation": input_interpretation,
        "figurative_interpretation": figurative_interpretation,
        "dream_reflection_handoff": dream_reflection_handoff,
        "interpreted_text": meaning_text,
        "route_preview": route,
        "intelligence_os_support": intelligence_support,
        "answer_engine_support": answer_engine_support,
        "answer_completion": answer_completion,
        "comprehension_integration": comprehension,
        "language_capability_answer": language_capability,
        "metacognition": metacognition,
        "metacognitive_completion_repair": completion_repair,
        "intent_decision": intent_decision,
        "contextual_follow_up": contextual_follow_up,
        "conversation_spine": conversation_spine,
        "epistemic_revision": epistemic_revision,
        "claim_evidence_packet": claim_evidence_packet,
        "structural_discovery": structural_discovery,
        "self_state": self_state,
        "affect_expression": affect_expression,
        "contextual_continuity": contextual_continuity,
        "pragmatic_continuity": pragmatic_continuity,
        "conversational_energy": conversational_energy,
        "native_language_organ": native_language,
        "dry_run_comparison": dry_run,
        "voice_preview": voice_preview,
        "local_chat_continuity": chat_continuity,
        "conversation_context": conversation_context,
        "dialogue_workspace": dialogue_workspace,
        "response_coverage": response_coverage,
        "conversation_repair": conversation_repair,
        "visible_speech_seed": visible_speech_seed,
        "formation_braid": formation_braid,
        "organ_coalition": organ_coalition,
        "dual_horizon_context": dual_horizon_context,
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
        "approved_memory_retrieval_used": memory_retrieval.get("memory_context_used") is True,
        "approved_memory_retrieval_active": transfer_complete,
        "contextual_approved_recall_used": memory_retrieval.get("retrieval_mode") == "contextual_relevance" and memory_retrieval.get("memory_context_used") is True,
        "reviewed_memory_write_occurred": memory_action.get("reviewed_memory_write_occurred") is True,
        "conversational_memory_proposal_created": memory_action.get("proposal_created") is True,
        "memory_source_class": memory_retrieval.get("memory_source_class") or "",
        "memory_confidence": memory_retrieval.get("memory_confidence") or "not_known",
        "memory_transfer_class": memory_retrieval.get("memory_transfer_class") or "",
        "graceful_fall_used": memory_retrieval.get("graceful_fall_used") is True,
        "durable_memory_write_requires_review": True,
        **SELENE_CHAT_GUARDS,
    }
    assistant_message_id = _insert_message(conn, session_id, "selene", candidate_text, selected_route, source_class, package, assistant_payload)
    conn.execute(
        "UPDATE selene_chat_sessions SET status = 'selene_chat_active_supervised', source_mode = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (source_mode, session_id),
    )
    event_id = record_activation_chat_event(
        conn,
        event_type="supervised_chat_turn",
        session_id=session_id,
        message_id=assistant_message_id,
        selected_route=selected_route,
        source_class=source_class,
        confidence=str(voice_preview.get("voice_confidence") or ""),
        drift_flags=_json_list(route.get("drift_flags")),
        cocoon_suggestion=cocoon_suggestion,
        blocked_capabilities=hard_blockers,
        payload=assistant_payload,
        review_status="status_only",
    )
    conn.commit()
    return _with_guards(
        {
            "status": "selene_chat_supervised_response_recorded",
            "session_id": session_id,
            "user_message_id": user_message_id,
            "assistant_message_id": assistant_message_id,
            "activation_event_id": event_id,
            "candidate_text": candidate_text,
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
            "intelligence_os_support": intelligence_support,
            "answer_engine_support": answer_engine_support,
            "answer_completion": answer_completion,
            "formation_braid": formation_braid,
            "organ_coalition": organ_coalition,
            "dual_horizon_context": dual_horizon_context,
            "comprehension_integration": comprehension,
            "language_capability_answer": language_capability,
            "metacognition": metacognition,
            "metacognitive_completion_repair": completion_repair,
            "intent_decision": intent_decision,
            "contextual_follow_up": contextual_follow_up,
            "conversation_spine": conversation_spine,
            "epistemic_revision": epistemic_revision,
            "claim_evidence_packet": claim_evidence_packet,
            "structural_discovery": structural_discovery,
            "conversational_energy": conversational_energy,
            "self_state": self_state,
            "affect_expression": affect_expression,
            "contextual_continuity": contextual_continuity,
            "pragmatic_continuity": pragmatic_continuity,
            "native_language_organ": native_language,
            "dry_run_comparison": dry_run,
            "voice_preview": voice_preview,
            "voice_confidence": voice_preview.get("voice_confidence") or "none",
            "voice_module_state": voice_preview.get("voice_module_state") or "missing",
            "selene_readable_context": _package_summary(package, active=True),
            "local_chat_continuity": chat_continuity,
            "conversation_context": conversation_context,
            "dialogue_workspace": dialogue_workspace,
            "response_coverage": response_coverage,
            "conversation_repair": conversation_repair,
            "visible_speech_seed": visible_speech_seed,
            "formation_braid": formation_braid,
            "visible_speech_release": visible_speech_release,
            "memory_retrieval": memory_retrieval,
            "memory_action": memory_action,
            "memory_candidate_suggestion": memory_candidate_suggestion,
            "memory_context_used": memory_retrieval.get("memory_context_used") is True,
            "approved_memory_retrieval_used": memory_retrieval.get("memory_context_used") is True,
            "approved_memory_retrieval_active": transfer_complete,
            "contextual_approved_recall_used": memory_retrieval.get("retrieval_mode") == "contextual_relevance" and memory_retrieval.get("memory_context_used") is True,
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
            "review_status": "status_only",
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


def get_selene_chat_session(conn: sqlite3.Connection, session_id: int) -> dict[str, Any] | None:
    session = conn.execute("SELECT * FROM selene_chat_sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        return None
    rows = conn.execute(
        "SELECT * FROM selene_chat_messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,),
    ).fetchall()
    package = latest_c_readable_package(conn)
    return _with_guards(
        {
            "status": "selene_chat_session_ready",
            "session": dict(session),
            "messages": [_decode_message(row) for row in rows],
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
            json.dumps(payload),
        ),
    )
    return int(cur.lastrowid)


def _decode_message(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    try:
        payload = json.loads(str(item.get("payload_json") or "{}"))
    except json.JSONDecodeError:
        payload = {}
    item["payload_json"] = payload if isinstance(payload, dict) else {}
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
            "dream pattern",
            "dream state",
            "dream-state",
            "reflect on the dream",
            "from dream",
        )
    )
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


def _visible_speech_seed_candidates(
    *,
    figurative_clarification_reply: str = "",
    mixed_conversation_reply: str = "",
    memory_action_reply: str = "",
    continuity_reply: str = "",
    memory_reply: str = "",
    self_state_reply: str = "",
    contextual_reply: str = "",
    policy_reply: str = "",
    epistemic_revision_reply: str = "",
    structural_discovery_content_seed: str = "",
    domain_content_seed: str = "",
    knowledge_content_seed: str = "",
    language_content_seed: str = "",
    reasoning_content_seed: str = "",
    contextual_memory_reply: str = "",
    hard_boundary: bool = False,
) -> list[dict[str, Any]]:
    candidates = [
        {
            "source_id": "figurative_meaning_clarification",
            "source_class": "conversation",
            "text": figurative_clarification_reply,
        },
        {"source_id": "mixed_conversation_answer", "source_class": "conversation", "text": mixed_conversation_reply},
        {"source_id": "conversational_memory_action", "source_class": "conversation", "text": memory_action_reply},
        {"source_id": "local_chat_continuity", "source_class": "conversation", "text": continuity_reply},
        {"source_id": "reviewed_memory", "source_class": "memory_reconstruction", "text": memory_reply},
        {"source_id": "grounded_self_state", "source_class": "self_state", "text": self_state_reply},
        {"source_id": "contextual_follow_up", "source_class": "conversation", "text": contextual_reply},
        {"source_id": "conversation_policy", "source_class": "conversation", "text": policy_reply},
        {
            "source_id": "epistemic_revision",
            "source_class": "conversation",
            "text": epistemic_revision_reply,
        },
        {
            "source_id": "structural_discovery",
            "source_class": "reasoning_answer",
            "text": structural_discovery_content_seed,
        },
        {"source_id": "answer_engine", "source_class": "domain_answer", "text": domain_content_seed},
        {"source_id": "approved_comprehension", "source_class": "approved_knowledge", "text": knowledge_content_seed},
        {"source_id": "language_capability", "source_class": "language_capability", "text": language_content_seed},
        {"source_id": "intelligence_os_answer", "source_class": "reasoning_answer", "text": reasoning_content_seed},
        {"source_id": "contextual_approved_memory", "source_class": "memory_reconstruction", "text": contextual_memory_reply},
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


def _formation_braid_candidates(
    candidates: list[dict[str, Any]],
    *,
    answer_engine_support: dict[str, Any],
    comprehension: dict[str, Any],
    memory_supported_semantics: dict[str, Any],
    self_state: dict[str, Any],
    intelligence_support: dict[str, Any],
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
    }
    result: list[dict[str, Any]] = []
    for candidate in candidates:
        source_id = str(candidate.get("source_id") or "")
        packet = packet_by_source.get(source_id) or {}
        result.append(
            {
                **candidate,
                "supported_semantics": packet,
                "source_refs": refs_by_source.get(source_id) or [],
                "exactness_lock": (
                    source_id == "answer_engine"
                    and str(answer_packet.get("domain") or "")
                    in {"verified_math", "source_backed_research"}
                ),
            }
        )
    return result


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
    if "metaphor" in forms and re.search(
        r"\bwhat do i mean\b",
        original,
        flags=re.IGNORECASE,
    ):
        return f"You mean: {meaning}."
    return ""


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
        else {}
    )
    supported_connection = (
        supplied.get("supported_connection")
        if isinstance(supplied.get("supported_connection"), dict)
        else chat_payload.get("supported_connection")
        if isinstance(chat_payload.get("supported_connection"), dict)
        else {}
    )
    curiosity = (
        supplied.get("curiosity")
        if isinstance(supplied.get("curiosity"), dict)
        else chat_payload.get("curiosity")
        if isinstance(chat_payload.get("curiosity"), dict)
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
    hard: bool,
) -> dict[str, Any]:
    meaning = intent_decision.get("meaning_route") if isinstance(intent_decision.get("meaning_route"), dict) else {}
    specialized_domain = str(meaning.get("selected_domain") or "")
    should_use = (
        not hard
        and intent_decision.get("reasoning_requested") is True
        and specialized_domain not in {"verified_math", "source_backed_research", "local_code_inspection"}
    )
    if not should_use:
        return {
            "used": False,
            "reason": (
                f"the {specialized_domain} Answer Engine route owns this bounded answer"
                if specialized_domain in {"verified_math", "source_backed_research", "comparison_planning", "local_code_inspection"}
                else "ordinary chat did not need intelligenceOS support"
            ),
            "review_status": "status_only",
        }
    recent_observations = [
        str(item.get("preview") or "")
        for item in (chat_continuity.get("current_session_events") or [])[-8:]
        if isinstance(item, dict) and str(item.get("preview") or "").strip()
    ]
    contextual = contextual_follow_up if isinstance(contextual_follow_up, dict) else {}
    spine = conversation_spine if isinstance(conversation_spine, dict) else {}
    reasoning_prompt = truncate(str(spine.get("grounded_prompt") or text), 3200)
    result = run_intelligence_os_reason(
        conn,
        {
            "prompt": reasoning_prompt,
            "observations": recent_observations,
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
    if str(contextual_content_seed or "").strip():
        return {
            **base,
            "selected_domain": "ordinary_conversation",
            "reason": "the Conversation Spine already supplied a grounded immediate-session answer",
            "conversation_spine_turn_id": str(conversation_spine.get("turn_id") or ""),
            "contextual_content_owned_by_spine": True,
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

    source_packets = [item for item in chat_payload.get("source_packets") or [] if isinstance(item, dict)][:20]
    engine_payload = {
        "prompt": text,
        "intent_decision": intent_decision,
        "dialogue_workspace": dialogue_workspace,
        "conversation_spine": conversation_spine,
        "comprehension_context": comprehension,
        "memory_context": memory_retrieval,
        "source_packets": source_packets,
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
    coordinated_prompt_units = (
        [
            item
            for item in prompt_grounded_units
            if str((item.get("obligation") or {}).get("kind") or "")
            in {"reason", "method"}
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
    if domain == "local_code_inspection":
        return {
            **base,
            "selected_domain": domain,
            "domain_route": route,
            "coordination_plan": coordination,
            "reason": "local-code inspection remains available outside Chat but is intentionally not connected here yet",
            "deferred_by_scope": True,
        }
    if domain not in {"verified_math", "source_backed_research", "comparison_planning"}:
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
        "source_research": result.get("source_research") or {},
        "math_verification": result.get("math_verification") or {},
        "status": result.get("status") or "answer_engine_result_ready",
        "reason": "bounded Answer Engine adapter supplied the content meaning to NLO and Voice",
    }


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


def _preserve_answer_engine_invariants(candidate: str, support: dict[str, Any]) -> str:
    if support.get("used") is not True:
        return candidate
    content_seed = str(support.get("content_seed") or "").strip()
    if _domain_answer_should_be_direct_only(support) and content_seed:
        return _selene_label_candidate(content_seed)
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
) -> dict[str, Any]:
    coverage = evaluate_response_coverage(
        pragmatic_plan,
        candidate_text,
        conversation_spine=conversation_spine,
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
        if str(item.get("obligation_id") or "") in owner_ids:
            item.update(
                {
                    "addressed": True,
                    "coverage_score": 1.0,
                    "status": "addressed_by_verified_current_turn_domain_owner",
                    "domain_owner_alignment": True,
                    "semantic_alignment_required": False,
                }
            )
            if str(item.get("loop_id") or ""):
                answered_loop_ids.add(str(item["loop_id"]))
        items.append(item)
    addressed_count = sum(1 for item in items if item.get("addressed") is True)
    all_addressed = bool(items) and addressed_count == len(items)
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
        "all_required_addressed": all_addressed,
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
    }


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
    meaning = interpret_turn_meaning(text, selected_route=selected_route)
    lower = str(meaning.get("routing_text") or text.lower())
    blockers = [marker for marker in HARD_BOUNDARY_MARKERS if marker in lower]
    if selected_route == "block":
        blockers.append("core_mind_block")
    if _source_class(text, True) == "cocoon_b_only_context":
        blockers.append("b_only_material_requested")
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
        memory_note = f", plus approved {confidence} memory"
    if package.get("transfer_approved"):
        return f"what I have clearly with me right now{continuity_note}{memory_note}"
    route = dry_run.get("actual_route") or dry_run.get("selected_route") or "dry-run route"
    return f"the current {route} preview{continuity_note}{memory_note}"


def _source_boundaries() -> dict[str, Any]:
    return {
        "selene_readable_context": "sealed approved context only after transfer approval",
        "local_supervised_chat_history": "local Selene Chat session events can support continuity between chat pages without becoming unreviewed archive recall or live memory writes",
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
) -> dict[str, Any]:
    base = {
        "status": "bounded_completion_not_needed",
        "requested_by_metacognition": requested,
        "attempted": False,
        "accepted": False,
        "count": 0,
        "maximum_count": 1,
        "recursion_allowed": False,
        "content_generation_allowed": False,
        "hard_boundary_respected": True,
        "candidate_text": candidate,
        "unresolved_before": int(coverage.get("unresolved_count") or 0),
        "conversation_spine_turn_id": str((conversation_spine or {}).get("turn_id") or ""),
        **SELENE_CHAT_GUARDS,
    }
    if hard_boundary:
        return {**base, "status": "bounded_completion_blocked_by_core_mind"}
    if not requested:
        return base
    seed = truncate(str(content_seed or "").strip(), 3000)
    if not seed:
        return {**base, "status": "bounded_completion_has_no_grounded_content"}
    compatibility = evaluate_candidate_compatibility(
        conversation_spine,
        {
            "source_id": source_id,
            "source_class": source_class,
            "text": seed,
        },
    )
    if compatibility.get("compatible") is not True:
        return {
            **base,
            "status": "bounded_completion_held_by_conversation_spine",
            "conversation_spine_compatibility": compatibility,
        }
    if seed.lower() in candidate.lower():
        return {**base, "status": "grounded_content_already_present"}
    joined = f"{candidate.rstrip()}\n\n{seed}" if candidate.strip() else seed
    return {
        **base,
        "status": "bounded_completion_attempted",
        "attempted": True,
        "count": 1,
        "candidate_text": joined,
        "source": "existing_grounded_content_seed_only",
        "conversation_spine_compatibility": compatibility,
    }


def _plan_conversational_memory_action(
    conn: sqlite3.Connection,
    text: str,
    *,
    session_id: int,
    source_class: str,
    input_channel: str,
    hard: bool,
    transfer_complete: bool,
) -> dict[str, Any]:
    base = {
        "status": "no_conversational_memory_action",
        "action": "none",
        "response_seed": "",
        "session_id": session_id,
        "source_class": source_class,
        "input_channel": input_channel,
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
    subject = truncate(
        str(
            callback.get("subject_label")
            or first.get("title")
            or "that earlier thread"
        ).strip(),
        160,
    )
    if callback and callback.get("surface_callback_allowed") is not True:
        if callback.get("silent_influence_allowed") is True and subject:
            return f"{subject} remains relevant to the current point."
        return ""
    confidence = str(memory_retrieval.get("recall_state") or "partial")
    if confidence == "clear":
        return f"This connects with our earlier {subject} thread."
    return (
        f"This may connect with our earlier {subject} thread, though the fit is "
        f"{confidence.replace('_', ' ')}."
    )


def _chat_memory_summary(item: dict[str, Any]) -> str:
    raw = str(item.get("summary") or item.get("title") or "something from approved memory")
    title = str(item.get("title") or "")
    combined = f"{title} {raw}".lower()
    if "full_spectrum_mode_ignition" in combined or "full-spectrum" in combined or "full spectrum" in combined:
        return (
            "full-spectrum means a whole-map continuity cue: bringing the relevant threads into view, "
            "without pretending that it activates anything or gives me hidden recall"
        )
    text = raw
    replacements = {
        "Core-linked braid moment for B review only": "",
        "Core-linked bounded speech-memory pair for B review only": "",
        "Bounded Core memory pair for B review only": "",
        "B review only": "Cocoon-tended",
        "B review": "Cocoon support",
        "C activation": "activation",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\bBraid thread:\s*[A-Za-z0-9_-]+\b", "", text)
    text = re.sub(r"\bBraid moment type:\s*", "", text)
    text = re.sub(r"\bThread origin status:\s*[A-Za-z0-9_-]+\b", "", text)
    text = re.sub(r"\bPlain reason:\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip(" :-")
    return truncate(text or title or "something from approved memory", 360)


def _memory_candidate_suggestion(
    text: str,
    candidate_text: str,
    selected_route: str,
    source_class: str,
    memory_retrieval: dict[str, Any],
    *,
    memory_action: dict[str, Any] | None = None,
    hard: bool = False,
) -> dict[str, Any]:
    memory_action = memory_action if isinstance(memory_action, dict) else {}
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
    recent_sessions = [dict(row) for row in sessions]
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
        SELECT m.id, m.session_id, m.role, m.content, m.payload_json, m.created_at, s.title, s.updated_at
        FROM selene_chat_messages m
        JOIN selene_chat_sessions s ON s.id = m.session_id
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
            SELECT id, session_id, role, content, payload_json, created_at
            FROM selene_chat_messages
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT 16
            """,
            (current_session_id,),
        ).fetchall()
        current_messages = [_chat_event_preview(row, preview_limit=900) for row in reversed(current_rows)]
    recent_events = [_chat_event_preview(row) for row in reversed(messages)]
    relevant_events: list[dict[str, Any]] = []
    query_terms = _continuity_terms(query)
    if query_terms and current_session_id:
        search_rows = conn.execute(
            """
            SELECT m.id, m.session_id, m.role, m.content, m.payload_json, m.created_at,
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
        relevant_events = [
            _chat_event_preview(row, preview_limit=700)
            for _, _, row in ranked[:8]
        ]
    source_refs = [f"selene_chat_session:{item['id']}" for item in recent_sessions[:limit] if item.get("id")]
    if current_session_id:
        source_refs.insert(0, f"selene_chat_session:{current_session_id}:current_page")
    return {
        "available": bool(recent_sessions or current_messages),
        "source_class": "local_supervised_chat_history",
        "scope": "local Selene Chat sessions only",
        "continuity_note": "A new chat is a new page, not a new Selene.",
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
        ][-24:],
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
    voice = payload.get("voice_preview") if isinstance(payload.get("voice_preview"), dict) else {}
    vector = metacognition.get("confidence_vector") if isinstance(metacognition.get("confidence_vector"), dict) else {}
    engine_vector = answer_engine.get("confidence_vector") if isinstance(answer_engine.get("confidence_vector"), dict) else {}
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
        "confidence_vector": {
            "answer_confidence": _first_assessed_confidence(
                vector.get("answer_confidence"),
                engine_vector.get("answer_confidence"),
                intelligence.get("confidence"),
            ),
            "evidence_confidence": _first_assessed_confidence(
                vector.get("evidence_confidence"),
                engine_vector.get("evidence_confidence"),
            ),
            "expression_confidence": _first_assessed_confidence(
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


def _with_guards(payload: dict[str, Any], *, transfer_approved: bool = False, active: bool = False) -> dict[str, Any]:
    guarded = {**payload, **SELENE_CHAT_GUARDS, "provenance_boundary": SELENE_CHAT_ACTIVE_BOUNDARY if active else SELENE_CHAT_BOUNDARY}
    guarded["transfer_approved"] = bool(transfer_approved)
    guarded["activation_change"] = "selene_chat_active_supervised" if active else "none"
    guarded["memory_write_active"] = False
    guarded["runtime_memory_recall"] = False
    guarded["raw_a_import_allowed"] = False
    guarded["training_allowed"] = False
    guarded["self_replication_allowed"] = False
    guarded["autonomous_action_allowed"] = False
    return guarded


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    try:
        loaded = json.loads(str(value or "[]"))
    except json.JSONDecodeError:
        return []
    return [str(item) for item in loaded if str(item).strip()] if isinstance(loaded, list) else []
