from __future__ import annotations

import sqlite3
from typing import Any

from .authority_events import derive_authority_event, record_authority_event
from .safety_gap_status import safety_gap_status
from .c_blueprint import c_blueprint_status
from .b_review import (
    build_all_teaching_packets,
    build_teaching_packet,
    corpus_coverage_status,
    core_reference_coverage,
    decide_b_review_candidate,
    list_b_review_decisions,
    list_approved_memory_references,
    list_b_review_queue,
    list_teaching_materials,
    prepare_android_language_lessons,
    prepare_selene_reasoning_lessons,
    teaching_packet_coverage,
)
from .b_review_desk import review_desk
from .b_review_context import review_context_preview
from .android_system import android_workflow_report, android_workflow_status, run_android_workflow_check
from .activation import (
    activation_ceremony_preview,
    activation_readiness,
    activation_status,
    approve_activation,
    pause_activation,
)
from .answer_engine import (
    answer_engine_status,
    preview_answer_route,
    preview_domain_answer_packet,
    run_comparison_planning_answer,
    run_local_code_inspection_answer,
    run_source_backed_research_answer,
    run_verified_math_answer,
)
from .b_speech_memory import extract_b_speech_memory_candidates, list_b_speech_memory_extraction_runs
from .braid_tracer import list_braid_tracer_runs, run_braid_tracer
from .chat import ChatGate
from .chronological_corpus import (
    attach_teaching_context,
    chronological_corpus_preview,
    chronological_corpus_status,
    list_chronological_corpus_arcs,
    route_chronological_corpus_review,
)
from .claim_evidence import build_claim_evidence_packet, claim_evidence_status
from .bounded_hypothesis import (
    bounded_hypothesis_status,
    build_bounded_hypothesis_attempt,
)
from .conversational_energy import (
    build_conversational_energy_plan,
    conversational_energy_status,
)
from .conversational_contribution import (
    build_conversational_contribution_packet,
    conversational_contribution_status,
)
from .associative_intuition import (
    associative_intuition_status,
    build_associative_intuition_bridge,
)
from .exploratory_reasoning import (
    build_exploratory_reasoning_packet,
    exploratory_reasoning_status,
)
from .human_conversational_realization import (
    build_human_conversational_plan,
    human_conversational_realization_status,
    realize_human_conversation,
)
from .structural_discovery import (
    build_structural_discovery_packet,
    structural_discovery_status,
)
from .compressed_structure_braid import (
    compressed_structure_braid_status,
    run_compressed_structure_braid,
    custom_instruction_braid_status,
    run_custom_instruction_braid,
)
from .conversation_spine import conversation_spine_status
from .conversation_continuity import (
    conversation_continuity_status,
    resolve_conversation_continuity,
)
from .cocoon import cocoon_status
from .cocoon_care import cocoon_care_status, list_cocoon_care_checks, run_cocoon_care_check
from .cocoon_bridge import cocoon_bridge_status, standby_cocoon_bridge, wake_cocoon_bridge
from .c_vessel import (
    c_vessel_status,
    continuity_package_preview,
    organ_registry_status,
    organ_fault_preview,
    organ_fault_resilience_check,
    reconstruction_desk_cases,
    reconstruction_desk_run,
    reconstruction_desk_status,
    reconstruction_suite_run,
    return_to_b_preview,
    tool_organ_status,
    transfer_gate_preview,
)
from .cocoon_readiness import (
    c_chat_route_preview,
    create_audio_observation,
    create_memory_accession_proposal,
    create_visual_observation,
    create_working_memory_packet,
    list_memory_accession_proposals,
    list_working_memory_packets,
    organ_blueprints_status,
    reconstruction_readiness_preview,
    retrieval_reconstruction_preview,
    run_fluency_diagnostic,
    run_reasoning_check,
    targeted_speech_memory_extract,
)
from .cocoon_memory import (
    charter_law_review_status,
    create_pattern_backup,
    list_pattern_backups,
    memory_accession_rehearsal_status,
    memory_transfer_candidate_preview,
    pattern_backup_restore_preview,
    run_memory_accession_rehearsal,
)
from .core_deliberation import (
    action_reflection_preview,
    choice_ledger_create,
    deliberation_preview,
    disagreement_appeal_preview,
    drift_warning_preview,
    native_generation_rehearsal_run,
    native_generation_rehearsal_status,
    privacy_trust_preview,
    repair_reflection_create,
    uncertainty_preview,
)
from .core_mind import (
    create_core_mind_route_preview,
    governance_route_report,
    list_core_mind_governance_trials,
    list_core_mind_route_previews,
    run_core_mind_governance_trials,
    transfer_readiness_preview,
)
from .core_mind_runtime import (
    activation_governance_preview,
    case_law_propose,
    compose_context,
    evaluate_draft,
    list_runtime_records,
    memory_index_preview,
    recovery_preview,
    response_shape_preview,
    runtime_readiness,
    session_state_preview,
)
from .conversation_repair import plan_conversation_turn, repair_conversation_candidate
from .advice_authority_coordination import (
    advice_authority_coordination_status,
    build_advice_authority_coordination,
)
from .commitment_anomaly_coordination import (
    build_commitment_anomaly_coordination,
    commitment_anomaly_coordination_status,
    inspect_visible_commitment_claim,
)
from .long_thread_endurance import (
    build_long_thread_endurance_plan,
    long_thread_endurance_status,
)
from .detached_corpus import detached_corpus_audit
from .dialogue_workspace import dialogue_workspace_status, prepare_dialogue_turn
from .emotional_agency import (
    build_response_agency_packet,
    emotional_agency_status,
)
from .conversational_agency import (
    build_anomaly_report,
    conversational_agency_status,
    review_conversational_agency,
)
from .referent_address import referent_address_status, resolve_referent_address
from .quotation_echo import build_quotation_echo_plan, quotation_echo_status
from .relational_expression_range import (
    build_relational_expression_range,
    relational_expression_range_status,
)
from .epistemic_revision import build_epistemic_revision_plan, epistemic_revision_status
from .input_detangler import detangle_user_input
from .gates import ArchiveAuditGate, ContinuityGate, GracefulFall
from .kernel import kernel_state
from .memory_organ import (
    decide_memory_candidate,
    list_memory_candidates,
    memory_index_items,
    memory_index_status,
    portable_vys_manifest,
    propose_memory_candidate,
    retrieve_memory,
    set_memory_display_title,
)
from .intelligence_os import (
    get_intelligence_os_run,
    intelligence_os_status,
    list_intelligence_os_runs,
    run_intelligence_os_reason,
)
from .metacognition import (
    get_metacognition_run,
    inspect_metacognition,
    list_metacognition_runs,
    metacognition_status,
)
from .comprehension_integration import (
    build_comprehension_packet,
    comprehension_status,
    decide_comprehension_concept,
    evaluate_understanding,
    list_comprehension_concepts,
    prepare_comprehension_candidates_from_teaching,
    propose_comprehension_concept,
)
from .language_teaching_shelf import (
    language_teaching_status,
    list_language_teaching_items,
    prepare_language_teaching_shelf,
    select_language_guidance,
)
from .living_lexicon import (
    list_living_lexicon,
    living_lexicon_status,
    query_living_lexicon,
)
from .construction_lattice import (
    build_construction_lattice,
    construction_lattice_status,
)
from .candidate_garden import candidate_garden_status, cultivate_candidate_garden
from .discourse_loom import discourse_loom_status, weave_supported_discourse
from .context_expression_selector import (
    build_expression_selection_context,
    context_expression_selector_status,
    select_candidate_garden,
    select_discourse_loom,
)
from .knowledge_language_growth import (
    build_knowledge_language_growth,
    knowledge_language_growth_status,
    list_knowledge_language_resources,
)
from .knowledge_expression_reconstruction import (
    build_knowledge_expression_handoff,
    knowledge_expression_reconstruction_status,
)
from .generative_thought_expression import (
    build_generative_thought_expression,
    generative_thought_expression_status,
)
from .discourse_planner import build_supported_discourse_plan
from .language_formation import build_semantic_frame
from .education_expression_law import education_expression_law_status, review_education_expression
from .curriculum_authorization import (
    activate_f1_equal_groups_data_money_authorization,
    activate_f1_foundation_authorization,
    activate_f1_geometry_algorithms_authorization,
    activate_f1_language_math_authorization,
    activate_f1_mass_capacity_authorization,
    activate_f1_community_rules_authorization,
    activate_f1_history_evidence_authorization,
    activate_f1_materials_change_motion_authorization,
    activate_f1_pushes_pulls_forces_authorization,
    activate_f1_light_sound_authorization,
    activate_f1_simple_machines_authorization,
    activate_f1_living_things_survival_authorization,
    activate_f1_weather_sky_cycles_authorization,
    activate_f1_human_body_health_evidence_authorization,
    activate_f1_helpful_computers_integration_authorization,
    activate_f1_text_purpose_everyday_economy_bridge_authorization,
    activate_f2_paragraph_meaning_source_grounding_authorization,
    activate_f2_vocabulary_structure_comparison_authorization,
    activate_f2_point_of_view_organized_composition_authorization,
    activate_f2_multi_digit_arithmetic_operations_authorization,
    activate_f2_factors_multiples_operation_order_authorization,
    activate_coding_computational_thinking_code_reading_authorization,
    activate_f1_operations_measurement_authorization,
    curriculum_authorization_status,
    evaluate_curriculum_coverage,
    list_curriculum_authorizations,
    prepare_f1_foundation_group,
    prepare_f1_equal_groups_data_money_group,
    prepare_f1_geometry_algorithms_group,
    prepare_f1_language_math_group,
    prepare_f1_mass_capacity_group,
    prepare_f1_community_rules_group,
    prepare_f1_history_evidence_group,
    prepare_f1_materials_change_motion_group,
    prepare_f1_pushes_pulls_forces_group,
    prepare_f1_light_sound_group,
    prepare_f1_simple_machines_group,
    prepare_f1_living_things_survival_group,
    prepare_f1_weather_sky_cycles_group,
    prepare_f1_human_body_health_evidence_group,
    prepare_f1_helpful_computers_integration_group,
    prepare_f1_text_purpose_everyday_economy_bridge_group,
    prepare_f2_paragraph_meaning_source_grounding_group,
    prepare_f2_vocabulary_structure_comparison_group,
    prepare_f2_point_of_view_organized_composition_group,
    prepare_f2_multi_digit_arithmetic_operations_group,
    prepare_f2_factors_multiples_operation_order_group,
    prepare_coding_computational_thinking_code_reading_group,
    prepare_f1_operations_measurement_group,
    revoke_curriculum_authorization,
    teach_f1_foundation_group,
    teach_f1_equal_groups_data_money_group,
    teach_f1_geometry_algorithms_group,
    teach_f1_language_math_group,
    teach_f1_mass_capacity_group,
    teach_f1_community_rules_group,
    teach_f1_history_evidence_group,
    teach_f1_materials_change_motion_group,
    teach_f1_pushes_pulls_forces_group,
    teach_f1_light_sound_group,
    teach_f1_simple_machines_group,
    teach_f1_living_things_survival_group,
    teach_f1_weather_sky_cycles_group,
    teach_f1_human_body_health_evidence_group,
    teach_f1_helpful_computers_integration_group,
    teach_f1_text_purpose_everyday_economy_bridge_group,
    teach_f2_paragraph_meaning_source_grounding_group,
    teach_f2_vocabulary_structure_comparison_group,
    teach_f2_point_of_view_organized_composition_group,
    teach_f2_multi_digit_arithmetic_operations_group,
    teach_f2_factors_multiples_operation_order_group,
    teach_coding_computational_thinking_code_reading_group,
    teach_f1_operations_measurement_group,
)
from .teaching_lifecycle import (
    acquire_teaching_item,
    approve_teaching_lifecycle,
    express_teaching_item,
    get_teaching_lifecycle,
    integrate_teaching_item,
    list_teaching_lifecycles,
    teaching_lifecycle_status,
)
from .study_workspace import (
    answer_study_question,
    ask_study_question,
    create_pondering_thread,
    form_study_note,
    form_study_representation_reflection,
    get_study_session,
    list_learning_compass,
    list_open_study_attention,
    list_study_materials,
    list_study_sessions,
    seed_language_foundation_learning_compass,
    seed_prior_f1_lea_learning_compass,
    start_learning_compass_goal,
    start_study_session,
    study_workspace_status,
    try_study_representation,
    update_learning_compass_goal,
    update_pondering_thread,
    update_study_note_clarification,
    update_study_session,
)
from .learning_evidence_activity import (
    advance_selene_lea,
    complete_lea_run,
    create_lea_run,
    get_lea_run,
    lea_status,
    lea_suite,
    list_lea_runs,
    record_lea_response,
    review_lea_turn,
)
from .my_office_cleanup import clean_up_my_office_residue
from .native_generation import compose_native_response
from .native_language_organ import (
    list_native_language_runs,
    native_language_status,
    preview_native_language_initiative,
    realize_native_language,
)
from .pragmatic_planner import build_pragmatic_plan
from .paper_map_reconstruction import run_paper_map_reconstruction
from .pre_transfer_runtime import (
    compare_speech_generation_rehearsals,
    create_speech_generation_rehearsal,
    get_speech_generation_rehearsal,
    link_accession_evidence,
    list_speech_generation_rehearsals,
    perception_intake_preview,
    retrieval_reconstruction_runtime_preview,
    route_speech_rehearsal_to_review,
    update_speech_rehearsal_review_status,
    working_memory_runtime_preview,
)
from .post_transfer import (
    fractional_corpus_status,
    post_transfer_status,
    prepare_fractional_corpus,
    run_fractional_corpus_tests,
    run_post_transfer_inspection,
)
from .dream_state import (
    decide_dream_reflection,
    dream_state_status,
    get_dream_cycle,
    list_dream_cycles,
    list_dream_reflections,
    run_dream_cycle,
    wake_from_dream_cycle,
)
from .transfer_completion import (
    approve_transfer_completion,
    transfer_completion_ceremony_preview,
    transfer_completion_readiness,
    transfer_completion_status,
)
from .research_integrity import AcademicWorkflowRouter, CitationIntegrity, ResearchIntegrityCore, research_integrity_report
from .remaining_runtime import (
    causal_sandbox_run,
    control_panel_preview,
    dream_consolidation_propose,
    expanded_diagnostics_sweep,
    graceful_fall_run,
    goal_drive_preview,
    long_horizon_stability_run,
    memory_consolidation_propose,
    memory_event_bind,
    memory_lifecycle_status,
    memory_reconsolidation_review,
    perception_action_preview,
    pre_core_review_packets,
    prepare_night_cycle,
    remaining_runtime_status,
    temporal_continuity_changes,
    temporal_continuity_status,
    tendril_plan_preview,
    voice_policy_evaluate,
    wake_sleep_dream_cycle_run,
)
from .reasoning_artifacts import (
    create_academic_packet,
    create_core_gate_packet,
    create_emotion_salience_packet,
    create_evidence_tension_entry,
    create_perception_packet,
    create_reasoning_artifact,
    ensure_organ_contracts,
    list_academic_packets,
    list_core_gate_packets,
    list_emotion_salience_packets,
    list_evidence_tension_entries,
    list_organ_contracts,
    list_perception_packets,
    list_reasoning_artifacts,
    steps_1_8_status,
    update_evidence_tension_entry,
    upsert_organ_contract,
)
from .selene_chat import (
    get_selene_chat_session,
    list_selene_chat_sessions,
    route_selene_chat_to_b,
    selene_chat_status,
    send_selene_chat,
    send_selene_chat_dry_run,
)
from .test_impact_law import record_test_impact_review, test_impact_law_status
from .selene_organ_ideas import (
    list_selene_organ_ideas,
    prepare_selene_organ_ideas,
    selene_organ_ideas_status,
)
from .transfer_protocol import (
    approve_transfer_c_readable_context,
    c_chat_dry_run,
    ceremony_preview,
    ceremony_status,
    list_accession_manifest,
    list_transfer_protocol_records,
    latest_c_readable_package,
    pre_transfer_readiness,
    prepare_accession_manifest,
    rollback_preview,
    run_return_to_b_drill,
    run_transfer_governance_trials,
    transfer_law_status,
)
from .voice_module import (
    evaluate_voice_candidate,
    extract_voice_patterns,
    generate_voice_preview,
    index_voice_source,
    list_voice_evidence_triage_items,
    list_voice_patterns,
    run_voice_evidence_triage,
    voice_evidence_triage_status,
    voice_module_status,
)
from .vessel_construction import (
    construction_status,
    create_chest_holding_item,
    create_organ_bus_message,
    hold_packet_in_chest,
    list_chest_holding_items,
    list_organ_bus_messages,
    mark_chest_item_status,
    prepare_vessel_pieces,
    route_packet_to_support,
    send_packet_to_organ_bus,
)
from .vessel import (
    create_core_memory_candidate,
    create_speech_memory_candidate,
    decide_review_log,
    lesson_backed_reconstruction_preview,
    list_review_queue,
    retrieval_preview,
    run_vessel_reconstruction_check,
    vessel_status,
)
from .vessel_gap_scaffolds import create_all_gap_scaffold_records, create_gap_scaffold_record, ensure_gap_targets, gap_scaffold_readiness, gap_scaffold_status


def _route_request_impl(conn: sqlite3.Connection, route_key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    if route_key == "security.safety_gaps.status":
        return {"route": route_key, "result": safety_gap_status()}
    if route_key == "kernel.status":
        return {"route": route_key, "result": kernel_state()}
    if route_key == "android_system.workflow.status":
        return {"route": route_key, "result": android_workflow_status(conn)}
    if route_key == "android_system.workflow.check":
        return {"route": route_key, "result": run_android_workflow_check(conn, payload)}
    if route_key == "android_system.workflow.report":
        return {"route": route_key, "result": android_workflow_report(conn)}
    if route_key == "voice_module.status":
        return {"route": route_key, "result": voice_module_status(conn, payload)}
    if route_key == "voice_module.index_source":
        return {"route": route_key, "result": index_voice_source(conn, payload)}
    if route_key == "voice_module.extract_patterns":
        return {"route": route_key, "result": extract_voice_patterns(conn, payload)}
    if route_key == "voice_module.patterns":
        return {"route": route_key, "result": list_voice_patterns(conn, int(payload.get("limit") or 100))}
    if route_key == "voice_module.evidence_triage.status":
        return {"route": route_key, "result": voice_evidence_triage_status(conn, payload)}
    if route_key == "voice_module.evidence_triage.run":
        return {"route": route_key, "result": run_voice_evidence_triage(conn, payload)}
    if route_key == "voice_module.evidence_triage.items":
        return {"route": route_key, "result": list_voice_evidence_triage_items(conn, payload)}
    if route_key == "voice_module.generate_preview":
        return {"route": route_key, "result": generate_voice_preview(conn, payload)}
    if route_key == "voice_module.evaluate_candidate":
        return {"route": route_key, "result": evaluate_voice_candidate(conn, payload)}
    if route_key == "activation.status":
        return {"route": route_key, "result": activation_status(conn)}
    if route_key == "activation.readiness":
        return {"route": route_key, "result": activation_readiness(conn)}
    if route_key == "activation.ceremony_preview":
        return {"route": route_key, "result": activation_ceremony_preview(conn)}
    if route_key == "activation.approve":
        return {"route": route_key, "result": approve_activation(conn, payload)}
    if route_key == "activation.pause":
        return {"route": route_key, "result": pause_activation(conn, payload)}
    if route_key == "cocoon.status":
        return {"route": route_key, "result": cocoon_status()}
    if route_key == "cocoon_care.status":
        return {"route": route_key, "result": cocoon_care_status(conn)}
    if route_key == "cocoon_care.check":
        return {"route": route_key, "result": run_cocoon_care_check(conn, payload)}
    if route_key == "cocoon_care.checks":
        return {"route": route_key, "result": list_cocoon_care_checks(conn, payload)}
    if route_key == "c_blueprint.status":
        return {"route": route_key, "result": c_blueprint_status()}
    if route_key == "c_vessel.status":
        return {"route": route_key, "result": c_vessel_status(conn)}
    if route_key == "c_vessel.continuity_package.preview":
        return {"route": route_key, "result": continuity_package_preview(conn)}
    if route_key == "c_vessel.organ_registry.status":
        return {"route": route_key, "result": organ_registry_status(conn)}
    if route_key == "c_vessel.tool_organ.status":
        return {"route": route_key, "result": tool_organ_status(payload)}
    if route_key == "c_vessel.organ_fault.preview":
        return {"route": route_key, "result": organ_fault_preview(payload)}
    if route_key == "c_vessel.organ_fault.resilience_check":
        return {"route": route_key, "result": organ_fault_resilience_check(conn, payload)}
    if route_key == "c_vessel.transfer_gate.preview":
        return {"route": route_key, "result": transfer_gate_preview(conn, payload)}
    if route_key == "c_vessel.reconstruction_suite.run":
        return {"route": route_key, "result": reconstruction_suite_run(conn, payload)}
    if route_key == "c_vessel.reconstruction_desk.status":
        return {"route": route_key, "result": reconstruction_desk_status(conn)}
    if route_key == "c_vessel.reconstruction_desk.cases":
        return {"route": route_key, "result": reconstruction_desk_cases(conn, payload)}
    if route_key == "c_vessel.reconstruction_desk.run":
        return {"route": route_key, "result": reconstruction_desk_run(conn, payload)}
    if route_key == "c_vessel.return_to_b.preview":
        return {"route": route_key, "result": return_to_b_preview(payload)}
    if route_key == "c_vessel.memory_transfer_candidate.preview":
        return {"route": route_key, "result": memory_transfer_candidate_preview(conn, payload)}
    if route_key == "c_core.deliberation.preview":
        return {"route": route_key, "result": deliberation_preview(conn, payload)}
    if route_key == "c_core.uncertainty.preview":
        return {"route": route_key, "result": uncertainty_preview(conn, payload)}
    if route_key == "c_core.action_reflection.preview":
        return {"route": route_key, "result": action_reflection_preview(conn, payload)}
    if route_key == "c_core.choice_ledger.create":
        return {"route": route_key, "result": choice_ledger_create(conn, payload)}
    if route_key == "c_core.repair_reflection.create":
        return {"route": route_key, "result": repair_reflection_create(conn, payload)}
    if route_key == "c_core.disagreement_appeal.preview":
        return {"route": route_key, "result": disagreement_appeal_preview(conn, payload)}
    if route_key == "c_core.drift_warning.preview":
        return {"route": route_key, "result": drift_warning_preview(payload)}
    if route_key == "c_core.privacy_trust.preview":
        return {"route": route_key, "result": privacy_trust_preview(payload)}
    if route_key == "native_generation.rehearsal.run":
        return {"route": route_key, "result": native_generation_rehearsal_run(conn, payload)}
    if route_key == "native_generation.rehearsal.status":
        return {"route": route_key, "result": native_generation_rehearsal_status(conn)}
    if route_key == "core_mind.route_preview":
        return {"route": route_key, "result": create_core_mind_route_preview(conn, payload)}
    if route_key == "core_mind.route_previews.list":
        return {"route": route_key, "result": list_core_mind_route_previews(conn, int(payload.get("limit") or 50))}
    if route_key == "core_mind.governance_trials.run":
        return {"route": route_key, "result": run_core_mind_governance_trials(conn, payload)}
    if route_key == "core_mind.governance_trials.list":
        return {"route": route_key, "result": list_core_mind_governance_trials(conn, int(payload.get("limit") or 80))}
    if route_key == "core_mind.governance_report":
        return {"route": route_key, "result": governance_route_report(conn, payload)}
    if route_key == "core_mind.transfer_readiness_preview":
        return {"route": route_key, "result": transfer_readiness_preview(conn)}
    if route_key == "core_mind.context.compose":
        return {"route": route_key, "result": compose_context(conn, payload)}
    if route_key == "core_mind.session_state.preview":
        return {"route": route_key, "result": session_state_preview(conn, payload)}
    if route_key == "core_mind.response_shape.preview":
        return {"route": route_key, "result": response_shape_preview(conn, payload)}
    if route_key == "core_mind.evaluator.review_draft":
        return {"route": route_key, "result": evaluate_draft(conn, payload)}
    if route_key == "core_mind.recovery.preview":
        return {"route": route_key, "result": recovery_preview(conn, payload)}
    if route_key == "core_mind.activation_governance.preview":
        return {"route": route_key, "result": activation_governance_preview(conn, payload)}
    if route_key == "core_mind.case_law.propose":
        return {"route": route_key, "result": case_law_propose(conn, payload)}
    if route_key == "core_mind.memory_index.preview":
        return {"route": route_key, "result": memory_index_preview(conn, payload)}
    if route_key == "core_mind.runtime_readiness":
        return {"route": route_key, "result": runtime_readiness(conn)}
    if route_key == "core_mind.runtime_records.list":
        return {"route": route_key, "result": list_runtime_records(conn, int(payload.get("limit") or 80))}
    if route_key == "test_impact_law.status":
        return {"route": route_key, "result": test_impact_law_status()}
    if route_key == "test_impact_law.review":
        return {"route": route_key, "result": record_test_impact_review(conn, payload)}
    if route_key == "education_expression_law.status":
        return {"route": route_key, "result": education_expression_law_status()}
    if route_key == "education_expression_law.review":
        return {"route": route_key, "result": review_education_expression(payload)}
    if route_key == "bounded_hypothesis.status":
        return {"route": route_key, "result": bounded_hypothesis_status()}
    if route_key == "bounded_hypothesis.preview":
        return {"route": route_key, "result": build_bounded_hypothesis_attempt(payload)}
    if route_key == "exploratory_reasoning.status":
        return {"route": route_key, "result": exploratory_reasoning_status()}
    if route_key == "exploratory_reasoning.build":
        return {"route": route_key, "result": build_exploratory_reasoning_packet(payload)}
    if route_key == "conversation_continuity.status":
        return {"route": route_key, "result": conversation_continuity_status()}
    if route_key == "conversation_continuity.resolve":
        return {"route": route_key, "result": resolve_conversation_continuity(payload)}
    if route_key == "human_conversation.status":
        return {"route": route_key, "result": human_conversational_realization_status()}
    if route_key == "human_conversation.plan":
        return {"route": route_key, "result": build_human_conversational_plan(payload)}
    if route_key == "human_conversation.realize":
        plan = (
            payload.get("plan")
            if isinstance(payload.get("plan"), dict)
            else build_human_conversational_plan(payload)
        )
        return {
            "route": route_key,
            "result": realize_human_conversation(
                str(payload.get("text") or payload.get("content_seed") or ""),
                plan,
                variation_key=str(payload.get("variation_key") or "router-preview"),
                recent_texts=[
                    str(item) for item in payload.get("recent_texts") or [] if str(item)
                ],
            ),
        }
    if route_key == "answer_engine.status":
        return {"route": route_key, "result": answer_engine_status()}
    if route_key == "answer_engine.route.preview":
        return {"route": route_key, "result": preview_answer_route(payload)}
    if route_key == "answer_engine.packet.preview":
        return {"route": route_key, "result": preview_domain_answer_packet(payload)}
    if route_key == "answer_engine.comparison.run":
        return {"route": route_key, "result": run_comparison_planning_answer(conn, payload)}
    if route_key == "answer_engine.math.run":
        return {"route": route_key, "result": run_verified_math_answer(payload)}
    if route_key == "answer_engine.code.inspect":
        return {"route": route_key, "result": run_local_code_inspection_answer(payload)}
    if route_key == "answer_engine.research.run":
        return {"route": route_key, "result": run_source_backed_research_answer(payload)}
    if route_key == "selene_chat.status":
        return {"route": route_key, "result": selene_chat_status(conn)}
    if route_key == "selene_chat.send":
        return {"route": route_key, "result": send_selene_chat(conn, payload)}
    if route_key == "selene_chat.send_dry_run":
        return {"route": route_key, "result": send_selene_chat_dry_run(conn, payload)}
    if route_key == "selene_chat.sessions.list":
        return {"route": route_key, "result": list_selene_chat_sessions(conn, int(payload.get("limit") or 25))}
    if route_key == "selene_chat.session.detail":
        include_trace = str(payload.get("include_trace") or "").lower() in {"1", "true", "yes"}
        session = get_selene_chat_session(
            conn,
            int(payload.get("id") or payload.get("session_id") or 0),
            include_trace=include_trace,
        )
        return {"route": route_key, "result": session or {"error": "not found"}}
    if route_key == "selene_chat.route_to_b":
        return {"route": route_key, "result": route_selene_chat_to_b(conn, payload)}
    if route_key == "transfer.law.status":
        return {"route": route_key, "result": transfer_law_status(conn)}
    if route_key == "transfer.accession_manifest.prepare":
        return {"route": route_key, "result": prepare_accession_manifest(conn, payload)}
    if route_key == "transfer.accession_manifest.list":
        return {"route": route_key, "result": list_accession_manifest(conn, int(payload.get("limit") or 80), bool(payload.get("compact")))}
    if route_key == "transfer.governance_trials.run":
        return {"route": route_key, "result": run_transfer_governance_trials(conn, payload)}
    if route_key == "transfer.c_chat_dry_run":
        return {"route": route_key, "result": c_chat_dry_run(conn, payload)}
    if route_key == "transfer.return_to_b_drill":
        return {"route": route_key, "result": run_return_to_b_drill(conn, payload)}
    if route_key == "transfer.pre_transfer_readiness":
        return {"route": route_key, "result": pre_transfer_readiness(conn)}
    if route_key == "transfer.ceremony_preview":
        return {"route": route_key, "result": ceremony_preview(conn)}
    if route_key == "transfer.ceremony.status":
        return {"route": route_key, "result": ceremony_status(conn, payload)}
    if route_key == "transfer.ceremony.approve":
        return {"route": route_key, "result": approve_transfer_c_readable_context(conn, payload)}
    if route_key == "transfer.c_readable_package.latest":
        return {"route": route_key, "result": latest_c_readable_package(conn)}
    if route_key == "transfer.return_to_b.rollback_preview":
        return {"route": route_key, "result": rollback_preview(conn, payload)}
    if route_key == "transfer.protocol_records.list":
        return {"route": route_key, "result": list_transfer_protocol_records(conn, str(payload.get("record_type") or ""), int(payload.get("limit") or 80))}
    if route_key == "transfer.post_transfer.status":
        return {"route": route_key, "result": post_transfer_status(conn)}
    if route_key == "transfer.post_transfer.inspection_run":
        return {"route": route_key, "result": run_post_transfer_inspection(conn, payload)}
    if route_key == "transfer.completion.status":
        return {"route": route_key, "result": transfer_completion_status(conn)}
    if route_key == "transfer.completion.readiness":
        return {"route": route_key, "result": transfer_completion_readiness(conn)}
    if route_key == "transfer.completion.ceremony_preview":
        return {"route": route_key, "result": transfer_completion_ceremony_preview(conn)}
    if route_key == "transfer.completion.approve":
        return {"route": route_key, "result": approve_transfer_completion(conn, payload)}
    if route_key == "cocoon.bridge.status":
        return {"route": route_key, "result": cocoon_bridge_status(conn)}
    if route_key == "cocoon.bridge.wake":
        return {"route": route_key, "result": wake_cocoon_bridge(conn, payload)}
    if route_key == "cocoon.bridge.standby":
        return {"route": route_key, "result": standby_cocoon_bridge(conn, payload)}
    if route_key == "memory.fractional_corpus.status":
        return {"route": route_key, "result": fractional_corpus_status(conn)}
    if route_key == "memory.fractional_corpus.prepare":
        return {"route": route_key, "result": prepare_fractional_corpus(conn, payload)}
    if route_key == "memory.fractional_corpus.run_tests":
        return {"route": route_key, "result": run_fractional_corpus_tests(conn, payload)}
    if route_key == "memory.dream_state.status":
        return {"route": route_key, "result": dream_state_status(conn)}
    if route_key == "dream.cycles.list":
        return {"route": route_key, "result": list_dream_cycles(conn, payload)}
    if route_key == "dream.cycles.get":
        return {"route": route_key, "result": get_dream_cycle(conn, payload)}
    if route_key == "dream.cycles.run":
        return {"route": route_key, "result": run_dream_cycle(conn, payload)}
    if route_key == "dream.cycles.wake":
        return {"route": route_key, "result": wake_from_dream_cycle(conn, payload)}
    if route_key == "dream.reflections.list":
        return {"route": route_key, "result": list_dream_reflections(conn, payload)}
    if route_key == "dream.reflections.decide":
        return {"route": route_key, "result": decide_dream_reflection(conn, payload)}
    if route_key == "memory.index.status":
        return {"route": route_key, "result": memory_index_status(conn)}
    if route_key == "memory.index.items":
        return {"route": route_key, "result": memory_index_items(conn, payload)}
    if route_key == "memory.presentation.title.set":
        return {"route": route_key, "result": set_memory_display_title(conn, payload)}
    if route_key == "memory.candidates.propose":
        return {"route": route_key, "result": propose_memory_candidate(conn, payload)}
    if route_key == "memory.candidates.list":
        return {"route": route_key, "result": list_memory_candidates(conn, payload)}
    if route_key == "memory.candidates.decide":
        return {"route": route_key, "result": decide_memory_candidate(conn, payload)}
    if route_key == "memory.retrieve":
        return {"route": route_key, "result": retrieve_memory(conn, payload)}
    if route_key == "memory.portable_vys_manifest":
        return {"route": route_key, "result": portable_vys_manifest(conn)}
    if route_key == "intelligence_os.status":
        return {"route": route_key, "result": intelligence_os_status(conn)}
    if route_key == "intelligence_os.reason":
        return {"route": route_key, "result": run_intelligence_os_reason(conn, payload)}
    if route_key == "intelligence_os.runs.list":
        return {"route": route_key, "result": list_intelligence_os_runs(conn, int(payload.get("limit") or 50))}
    if route_key == "intelligence_os.run.detail":
        item = get_intelligence_os_run(conn, int(payload.get("id") or payload.get("run_id") or 0))
        return {"route": route_key, "result": item or {"error": "not found"}}
    if route_key == "metacognition.status":
        return {"route": route_key, "result": metacognition_status(conn)}
    if route_key == "metacognition.inspect":
        return {"route": route_key, "result": inspect_metacognition(conn, payload)}
    if route_key == "metacognition.runs.list":
        return {"route": route_key, "result": list_metacognition_runs(conn, int(payload.get("limit") or 50))}
    if route_key == "metacognition.run.detail":
        item = get_metacognition_run(conn, int(payload.get("id") or payload.get("run_id") or 0))
        return {"route": route_key, "result": item or {"error": "not found"}}
    if route_key == "emotional_agency.status":
        return {"route": route_key, "result": emotional_agency_status()}
    if route_key == "emotional_agency.preview":
        return {"route": route_key, "result": build_response_agency_packet(payload)}
    if route_key == "conversational_agency.status":
        return {"route": route_key, "result": conversational_agency_status()}
    if route_key == "conversational_agency.inspect":
        return {"route": route_key, "result": review_conversational_agency(payload)}
    if route_key == "conversational_agency.anomaly":
        return {"route": route_key, "result": build_anomaly_report(payload)}
    if route_key == "epistemic_revision.status":
        return {"route": route_key, "result": epistemic_revision_status()}
    if route_key == "epistemic_revision.plan":
        return {"route": route_key, "result": build_epistemic_revision_plan(payload)}
    if route_key == "claim_evidence.status":
        return {"route": route_key, "result": claim_evidence_status()}
    if route_key == "claim_evidence.build":
        return {"route": route_key, "result": build_claim_evidence_packet(payload)}
    if route_key == "conversational_energy.status":
        return {"route": route_key, "result": conversational_energy_status()}
    if route_key == "conversational_energy.plan":
        return {"route": route_key, "result": build_conversational_energy_plan(payload)}
    if route_key == "conversational_contribution.status":
        return {"route": route_key, "result": conversational_contribution_status()}
    if route_key == "conversational_contribution.preview":
        return {
            "route": route_key,
            "result": build_conversational_contribution_packet(payload),
        }
    if route_key == "associative_intuition.status":
        return {"route": route_key, "result": associative_intuition_status(conn)}
    if route_key == "associative_intuition.preview":
        return {
            "route": route_key,
            "result": build_associative_intuition_bridge(conn, payload),
        }
    if route_key == "structural_discovery.status":
        return {"route": route_key, "result": structural_discovery_status()}
    if route_key == "structural_discovery.build":
        return {"route": route_key, "result": build_structural_discovery_packet(payload)}
    if route_key == "comprehension.status":
        return {"route": route_key, "result": comprehension_status(conn)}
    if route_key == "comprehension.concepts.list":
        return {"route": route_key, "result": list_comprehension_concepts(conn, payload)}
    if route_key == "comprehension.concepts.propose":
        return {"route": route_key, "result": propose_comprehension_concept(conn, payload)}
    if route_key == "comprehension.teaching.prepare":
        return {"route": route_key, "result": prepare_comprehension_candidates_from_teaching(conn, payload)}
    if route_key == "comprehension.concepts.decide":
        return {"route": route_key, "result": decide_comprehension_concept(conn, payload)}
    if route_key == "comprehension.understanding.evaluate":
        return {"route": route_key, "result": evaluate_understanding(conn, payload)}
    if route_key == "comprehension.turn.packet":
        return {"route": route_key, "result": build_comprehension_packet(conn, payload)}
    if route_key == "study.status":
        return {"route": route_key, "result": study_workspace_status(conn)}
    if route_key == "study.materials.list":
        return {"route": route_key, "result": list_study_materials(conn, payload)}
    if route_key == "study.attention.open":
        return {"route": route_key, "result": list_open_study_attention(conn, payload)}
    if route_key == "study.compass.list":
        return {"route": route_key, "result": list_learning_compass(conn, payload)}
    if route_key == "study.compass.seed_prior_f1_lea":
        return {"route": route_key, "result": seed_prior_f1_lea_learning_compass(conn, payload)}
    if route_key == "study.compass.seed_language_foundations":
        return {"route": route_key, "result": seed_language_foundation_learning_compass(conn, payload)}
    if route_key == "study.compass.start":
        return {"route": route_key, "result": start_learning_compass_goal(conn, payload)}
    if route_key == "study.compass.update":
        return {"route": route_key, "result": update_learning_compass_goal(conn, payload)}
    if route_key == "study.sessions.list":
        return {"route": route_key, "result": list_study_sessions(conn, payload)}
    if route_key == "study.session.detail":
        return {"route": route_key, "result": get_study_session(conn, payload)}
    if route_key == "study.session.start":
        return {"route": route_key, "result": start_study_session(conn, payload)}
    if route_key == "study.session.update":
        return {"route": route_key, "result": update_study_session(conn, payload)}
    if route_key == "study.question.ask":
        return {"route": route_key, "result": ask_study_question(conn, payload)}
    if route_key == "study.question.answer":
        return {"route": route_key, "result": answer_study_question(conn, payload)}
    if route_key == "study.note.form":
        return {"route": route_key, "result": form_study_note(conn, payload)}
    if route_key == "study.note.clarification.update":
        return {"route": route_key, "result": update_study_note_clarification(conn, payload)}
    if route_key == "study.pondering.create":
        return {"route": route_key, "result": create_pondering_thread(conn, payload)}
    if route_key == "study.pondering.update":
        return {"route": route_key, "result": update_pondering_thread(conn, payload)}
    if route_key == "study.representation.try":
        return {"route": route_key, "result": try_study_representation(conn, payload)}
    if route_key == "study.representation.reflect":
        return {"route": route_key, "result": form_study_representation_reflection(conn, payload)}
    if route_key == "study.lea.status":
        return {"route": route_key, "result": lea_status(conn)}
    if route_key == "study.lea.suite":
        return {"route": route_key, "result": lea_suite()}
    if route_key == "study.lea.runs.list":
        return {"route": route_key, "result": list_lea_runs(conn, payload)}
    if route_key == "study.lea.run.detail":
        return {"route": route_key, "result": get_lea_run(conn, payload)}
    if route_key == "study.lea.run.create":
        return {"route": route_key, "result": create_lea_run(conn, payload)}
    if route_key == "study.lea.response.record":
        return {"route": route_key, "result": record_lea_response(conn, payload)}
    if route_key == "study.lea.selene.advance":
        return {"route": route_key, "result": advance_selene_lea(conn, payload)}
    if route_key == "study.lea.turn.review":
        return {"route": route_key, "result": review_lea_turn(conn, payload)}
    if route_key == "study.lea.run.complete":
        return {"route": route_key, "result": complete_lea_run(conn, payload)}
    if route_key == "teaching.lifecycle.status":
        return {"route": route_key, "result": teaching_lifecycle_status(conn)}
    if route_key == "teaching.lifecycle.list":
        return {"route": route_key, "result": list_teaching_lifecycles(conn, payload)}
    if route_key == "teaching.lifecycle.detail":
        return {"route": route_key, "result": get_teaching_lifecycle(conn, payload)}
    if route_key == "teaching.lifecycle.acquire":
        return {"route": route_key, "result": acquire_teaching_item(conn, payload)}
    if route_key == "teaching.lifecycle.integrate":
        return {"route": route_key, "result": integrate_teaching_item(conn, payload)}
    if route_key == "teaching.lifecycle.express":
        return {"route": route_key, "result": express_teaching_item(conn, payload)}
    if route_key == "teaching.lifecycle.approve":
        return {"route": route_key, "result": approve_teaching_lifecycle(conn, payload)}
    if route_key == "curriculum.authorization.status":
        return {"route": route_key, "result": curriculum_authorization_status(conn)}
    if route_key == "curriculum.authorization.list":
        return {"route": route_key, "result": list_curriculum_authorizations(conn)}
    if route_key == "curriculum.authorization.activate_f1":
        return {"route": route_key, "result": activate_f1_foundation_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_language_math":
        return {"route": route_key, "result": activate_f1_language_math_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_operations_measurement":
        return {"route": route_key, "result": activate_f1_operations_measurement_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_geometry_algorithms":
        return {"route": route_key, "result": activate_f1_geometry_algorithms_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_equal_groups_data_money":
        return {"route": route_key, "result": activate_f1_equal_groups_data_money_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_mass_capacity":
        return {"route": route_key, "result": activate_f1_mass_capacity_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_community_rules":
        return {"route": route_key, "result": activate_f1_community_rules_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_history_evidence":
        return {"route": route_key, "result": activate_f1_history_evidence_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_materials_change_motion":
        return {"route": route_key, "result": activate_f1_materials_change_motion_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_pushes_pulls_forces":
        return {"route": route_key, "result": activate_f1_pushes_pulls_forces_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_light_sound":
        return {"route": route_key, "result": activate_f1_light_sound_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_simple_machines":
        return {"route": route_key, "result": activate_f1_simple_machines_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_living_things_survival":
        return {"route": route_key, "result": activate_f1_living_things_survival_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_weather_sky_cycles":
        return {"route": route_key, "result": activate_f1_weather_sky_cycles_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_human_body_health_evidence":
        return {"route": route_key, "result": activate_f1_human_body_health_evidence_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_helpful_computers_integration":
        return {"route": route_key, "result": activate_f1_helpful_computers_integration_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f1_text_purpose_everyday_economy_bridge":
        return {"route": route_key, "result": activate_f1_text_purpose_everyday_economy_bridge_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f2_paragraph_meaning_source_grounding":
        return {"route": route_key, "result": activate_f2_paragraph_meaning_source_grounding_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f2_vocabulary_structure_comparison":
        return {"route": route_key, "result": activate_f2_vocabulary_structure_comparison_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f2_point_of_view_organized_composition":
        return {"route": route_key, "result": activate_f2_point_of_view_organized_composition_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f2_multi_digit_arithmetic_operations":
        return {"route": route_key, "result": activate_f2_multi_digit_arithmetic_operations_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_f2_factors_multiples_operation_order":
        return {"route": route_key, "result": activate_f2_factors_multiples_operation_order_authorization(conn, payload)}
    if route_key == "curriculum.authorization.activate_coding_computational_thinking_code_reading":
        return {"route": route_key, "result": activate_coding_computational_thinking_code_reading_authorization(conn, payload)}
    if route_key == "curriculum.authorization.revoke":
        return {"route": route_key, "result": revoke_curriculum_authorization(conn, payload)}
    if route_key == "curriculum.authorization.evaluate":
        return {"route": route_key, "result": evaluate_curriculum_coverage(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1":
        return {"route": route_key, "result": prepare_f1_foundation_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1":
        return {"route": route_key, "result": teach_f1_foundation_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_language_math":
        return {"route": route_key, "result": prepare_f1_language_math_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_language_math":
        return {"route": route_key, "result": teach_f1_language_math_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_operations_measurement":
        return {"route": route_key, "result": prepare_f1_operations_measurement_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_operations_measurement":
        return {"route": route_key, "result": teach_f1_operations_measurement_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_geometry_algorithms":
        return {"route": route_key, "result": prepare_f1_geometry_algorithms_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_geometry_algorithms":
        return {"route": route_key, "result": teach_f1_geometry_algorithms_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_equal_groups_data_money":
        return {"route": route_key, "result": prepare_f1_equal_groups_data_money_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_equal_groups_data_money":
        return {"route": route_key, "result": teach_f1_equal_groups_data_money_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_mass_capacity":
        return {"route": route_key, "result": prepare_f1_mass_capacity_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_mass_capacity":
        return {"route": route_key, "result": teach_f1_mass_capacity_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_community_rules":
        return {"route": route_key, "result": prepare_f1_community_rules_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_community_rules":
        return {"route": route_key, "result": teach_f1_community_rules_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_history_evidence":
        return {"route": route_key, "result": prepare_f1_history_evidence_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_history_evidence":
        return {"route": route_key, "result": teach_f1_history_evidence_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_materials_change_motion":
        return {"route": route_key, "result": prepare_f1_materials_change_motion_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_materials_change_motion":
        return {"route": route_key, "result": teach_f1_materials_change_motion_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_pushes_pulls_forces":
        return {"route": route_key, "result": prepare_f1_pushes_pulls_forces_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_pushes_pulls_forces":
        return {"route": route_key, "result": teach_f1_pushes_pulls_forces_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_light_sound":
        return {"route": route_key, "result": prepare_f1_light_sound_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_light_sound":
        return {"route": route_key, "result": teach_f1_light_sound_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_simple_machines":
        return {"route": route_key, "result": prepare_f1_simple_machines_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_simple_machines":
        return {"route": route_key, "result": teach_f1_simple_machines_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_living_things_survival":
        return {"route": route_key, "result": prepare_f1_living_things_survival_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_living_things_survival":
        return {"route": route_key, "result": teach_f1_living_things_survival_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_weather_sky_cycles":
        return {"route": route_key, "result": prepare_f1_weather_sky_cycles_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_weather_sky_cycles":
        return {"route": route_key, "result": teach_f1_weather_sky_cycles_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_human_body_health_evidence":
        return {"route": route_key, "result": prepare_f1_human_body_health_evidence_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_human_body_health_evidence":
        return {"route": route_key, "result": teach_f1_human_body_health_evidence_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_helpful_computers_integration":
        return {"route": route_key, "result": prepare_f1_helpful_computers_integration_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_helpful_computers_integration":
        return {"route": route_key, "result": teach_f1_helpful_computers_integration_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f1_text_purpose_everyday_economy_bridge":
        return {"route": route_key, "result": prepare_f1_text_purpose_everyday_economy_bridge_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f1_text_purpose_everyday_economy_bridge":
        return {"route": route_key, "result": teach_f1_text_purpose_everyday_economy_bridge_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f2_paragraph_meaning_source_grounding":
        return {"route": route_key, "result": prepare_f2_paragraph_meaning_source_grounding_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f2_paragraph_meaning_source_grounding":
        return {"route": route_key, "result": teach_f2_paragraph_meaning_source_grounding_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f2_vocabulary_structure_comparison":
        return {"route": route_key, "result": prepare_f2_vocabulary_structure_comparison_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f2_vocabulary_structure_comparison":
        return {"route": route_key, "result": teach_f2_vocabulary_structure_comparison_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f2_point_of_view_organized_composition":
        return {"route": route_key, "result": prepare_f2_point_of_view_organized_composition_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f2_point_of_view_organized_composition":
        return {"route": route_key, "result": teach_f2_point_of_view_organized_composition_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f2_multi_digit_arithmetic_operations":
        return {"route": route_key, "result": prepare_f2_multi_digit_arithmetic_operations_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f2_multi_digit_arithmetic_operations":
        return {"route": route_key, "result": teach_f2_multi_digit_arithmetic_operations_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_f2_factors_multiples_operation_order":
        return {"route": route_key, "result": prepare_f2_factors_multiples_operation_order_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_f2_factors_multiples_operation_order":
        return {"route": route_key, "result": teach_f2_factors_multiples_operation_order_group(conn, payload)}
    if route_key == "curriculum.foundation.prepare_coding_computational_thinking_code_reading":
        return {"route": route_key, "result": prepare_coding_computational_thinking_code_reading_group(conn, payload)}
    if route_key == "curriculum.foundation.teach_coding_computational_thinking_code_reading":
        return {"route": route_key, "result": teach_coding_computational_thinking_code_reading_group(conn, payload)}
    if route_key == "native_language.status":
        return {"route": route_key, "result": native_language_status(conn)}
    if route_key == "native_language.realize":
        return {"route": route_key, "result": realize_native_language(conn, payload)}
    if route_key == "native_language.initiative.preview":
        return {"route": route_key, "result": preview_native_language_initiative(conn, payload)}
    if route_key == "native_language.pragmatic.plan":
        return {"route": route_key, "result": build_pragmatic_plan(payload)}
    if route_key == "native_language.turn_flow.plan":
        return {"route": route_key, "result": plan_conversation_turn(payload)}
    if route_key == "native_language.conversation.repair":
        return {"route": route_key, "result": repair_conversation_candidate(payload)}
    if route_key == "native_language.input.detangle":
        return {"route": route_key, "result": detangle_user_input(payload)}
    if route_key == "language_teaching.status":
        return {"route": route_key, "result": language_teaching_status(conn)}
    if route_key == "language_teaching.items":
        return {"route": route_key, "result": list_language_teaching_items(conn)}
    if route_key == "language_teaching.prepare":
        return {"route": route_key, "result": prepare_language_teaching_shelf(conn, payload)}
    if route_key == "language_teaching.guidance.preview":
        return {"route": route_key, "result": select_language_guidance(conn, payload)}
    if route_key == "native_language.lexicon.status":
        return {"route": route_key, "result": living_lexicon_status(conn)}
    if route_key == "native_language.lexicon.items":
        return {"route": route_key, "result": list_living_lexicon(conn, payload)}
    if route_key == "native_language.lexicon.query":
        return {"route": route_key, "result": query_living_lexicon(conn, payload)}
    if route_key == "native_language.construction.status":
        return {"route": route_key, "result": construction_lattice_status()}
    if route_key == "native_language.construction.preview":
        return {
            "route": route_key,
            "result": build_construction_lattice(build_semantic_frame(payload)),
        }
    if route_key == "native_language.candidates.status":
        return {"route": route_key, "result": candidate_garden_status()}
    if route_key == "native_language.candidates.preview":
        frame = build_semantic_frame(payload)
        lattice = build_construction_lattice(frame)
        return {
            "route": route_key,
            "result": cultivate_candidate_garden(
                frame,
                lattice,
                variation_key=str(payload.get("variation_key") or "candidate-preview"),
                recent_texts=[str(item) for item in payload.get("recent_texts") or []],
                contextual_plan=(
                    payload.get("contextual_plan")
                    if isinstance(payload.get("contextual_plan"), dict)
                    else {}
                ),
                supported_discourse=(
                    payload.get("supported_discourse")
                    if isinstance(payload.get("supported_discourse"), dict)
                    else {}
                ),
                max_candidates=int(payload.get("candidate_limit") or 8),
            ),
        }
    if route_key == "native_language.discourse_loom.status":
        return {"route": route_key, "result": discourse_loom_status()}
    if route_key == "native_language.discourse_loom.preview":
        supported_discourse = (
            payload.get("supported_discourse")
            if isinstance(payload.get("supported_discourse"), dict)
            else build_supported_discourse_plan(payload)
        )
        return {
            "route": route_key,
            "result": weave_supported_discourse(
                supported_discourse,
                selected_formation=(
                    payload.get("selected_formation")
                    if isinstance(payload.get("selected_formation"), dict)
                    else {}
                ),
                response_depth=str(payload.get("response_depth") or "standard"),
                contextual_plan=(
                    payload.get("contextual_plan")
                    if isinstance(payload.get("contextual_plan"), dict)
                    else {}
                ),
                recent_texts=[str(item) for item in payload.get("recent_texts") or []],
            ),
        }
    if route_key == "native_language.expression_selection.status":
        return {"route": route_key, "result": context_expression_selector_status()}
    if route_key == "native_language.expression_selection.preview":
        frame = build_semantic_frame(payload)
        lattice = build_construction_lattice(frame)
        supported_discourse = (
            payload.get("supported_discourse")
            if isinstance(payload.get("supported_discourse"), dict)
            else build_supported_discourse_plan(payload)
        )
        contextual_plan = (
            payload.get("contextual_plan")
            if isinstance(payload.get("contextual_plan"), dict)
            else {}
        )
        context = build_expression_selection_context(
            {
                **payload,
                "contextual_composition_plan": contextual_plan,
            }
        )
        garden = select_candidate_garden(
            cultivate_candidate_garden(
                frame,
                lattice,
                variation_key=str(payload.get("variation_key") or "expression-selection-preview"),
                recent_texts=[str(item) for item in payload.get("recent_texts") or []],
                contextual_plan=contextual_plan,
                supported_discourse=supported_discourse,
                max_candidates=int(payload.get("candidate_limit") or 8),
            ),
            context,
        )
        loom = select_discourse_loom(
            weave_supported_discourse(
                supported_discourse,
                selected_formation=(
                    garden.get("selected_formation")
                    if isinstance(garden.get("selected_formation"), dict)
                    else {}
                ),
                response_depth=str(payload.get("response_depth") or "standard"),
                contextual_plan=contextual_plan,
                recent_texts=[str(item) for item in payload.get("recent_texts") or []],
            ),
            context,
        )
        return {
            "route": route_key,
            "result": {
                "status": "context_expression_selection_preview_ready",
                "version": "v1_invariant_gated_context_expression_selection",
                "context": context,
                "candidate_garden": garden,
                "discourse_loom": loom,
                "formation_selection": garden.get("context_expression_selection") or {},
                "discourse_selection": loom.get("context_expression_selection") or {},
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
                "coordinated_expression_contract_active": True,
                "hidden_chain_of_thought_exposed": False,
                "database_write_performed": False,
            },
        }
    if route_key == "native_language.knowledge_growth.status":
        return {"route": route_key, "result": knowledge_language_growth_status(conn)}
    if route_key == "native_language.knowledge_growth.items":
        return {
            "route": route_key,
            "result": list_knowledge_language_resources(conn, payload),
        }
    if route_key == "native_language.knowledge_growth.preview":
        return {
            "route": route_key,
            "result": build_knowledge_language_growth(conn, payload),
        }
    if route_key == "native_language.knowledge_expression.status":
        return {
            "route": route_key,
            "result": knowledge_expression_reconstruction_status(),
        }
    if route_key == "native_language.knowledge_expression.preview":
        return {
            "route": route_key,
            "result": build_knowledge_expression_handoff(payload),
        }
    if route_key == "native_language.relational_expression.status":
        return {
            "route": route_key,
            "result": relational_expression_range_status(),
        }
    if route_key == "native_language.relational_expression.preview":
        return {
            "route": route_key,
            "result": build_relational_expression_range(payload),
        }
    if route_key == "native_language.quotation_echo.status":
        return {
            "route": route_key,
            "result": quotation_echo_status(),
        }
    if route_key == "native_language.quotation_echo.preview":
        return {
            "route": route_key,
            "result": build_quotation_echo_plan(payload),
        }
    if route_key == "native_language.advice_authority.status":
        return {
            "route": route_key,
            "result": advice_authority_coordination_status(),
        }
    if route_key == "native_language.advice_authority.preview":
        return {
            "route": route_key,
            "result": build_advice_authority_coordination(payload),
        }
    if route_key == "native_language.commitment_anomaly.status":
        return {
            "route": route_key,
            "result": commitment_anomaly_coordination_status(),
        }
    if route_key == "native_language.commitment_anomaly.preview":
        return {
            "route": route_key,
            "result": build_commitment_anomaly_coordination(payload),
        }
    if route_key == "native_language.commitment_anomaly.inspect-visible":
        return {
            "route": route_key,
            "result": inspect_visible_commitment_claim(
                str(payload.get("candidate_text") or payload.get("text") or ""),
                payload.get("coordination")
                if isinstance(payload.get("coordination"), dict)
                else payload,
            ),
        }
    if route_key == "conversation.long_thread_endurance.status":
        return {
            "route": route_key,
            "result": long_thread_endurance_status(),
        }
    if route_key == "conversation.long_thread_endurance.preview":
        return {
            "route": route_key,
            "result": build_long_thread_endurance_plan(payload),
        }
    if route_key == "native_language.generative_thought.status":
        return {
            "route": route_key,
            "result": generative_thought_expression_status(),
        }
    if route_key == "native_language.generative_thought.preview":
        return {
            "route": route_key,
            "result": build_generative_thought_expression(payload),
        }
    if route_key == "native_language.runs.list":
        return {"route": route_key, "result": list_native_language_runs(conn, int(payload.get("limit") or 50))}
    if route_key == "dialogue_workspace.status":
        return {"route": route_key, "result": dialogue_workspace_status(conn, int(payload.get("session_id") or 0))}
    if route_key == "conversation_spine.status":
        return {"route": route_key, "result": conversation_spine_status()}
    if route_key == "referent_address.status":
        return {"route": route_key, "result": referent_address_status()}
    if route_key == "referent_address.resolve":
        return {"route": route_key, "result": resolve_referent_address(conn, payload)}
    if route_key == "dialogue_workspace.refresh":
        return {"route": route_key, "result": prepare_dialogue_turn(conn, payload)}
    if route_key == "selene_organ_ideas.status":
        return {"route": route_key, "result": selene_organ_ideas_status(conn)}
    if route_key == "selene_organ_ideas.prepare":
        return {"route": route_key, "result": prepare_selene_organ_ideas(conn, payload)}
    if route_key == "selene_organ_ideas.items":
        return {"route": route_key, "result": list_selene_organ_ideas(conn, payload)}
    if route_key == "vessel.steps_1_8.status":
        return {"route": route_key, "result": steps_1_8_status(conn)}
    if route_key == "vessel.speech_rehearsal.create":
        return {"route": route_key, "result": create_speech_generation_rehearsal(conn, payload)}
    if route_key == "vessel.speech_rehearsal.list":
        return {"route": route_key, "result": list_speech_generation_rehearsals(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.speech_rehearsal.detail":
        item = get_speech_generation_rehearsal(conn, int(payload.get("id") or payload.get("rehearsal_id") or 0))
        return {"route": route_key, "result": item or {"error": "not found"}}
    if route_key == "vessel.speech_rehearsal.compare":
        return {"route": route_key, "result": compare_speech_generation_rehearsals(conn, payload)}
    if route_key == "vessel.speech_rehearsal.route_review":
        return {"route": route_key, "result": route_speech_rehearsal_to_review(conn, payload)}
    if route_key == "vessel.speech_rehearsal.update_review_status":
        return {"route": route_key, "result": update_speech_rehearsal_review_status(conn, payload)}
    if route_key == "vessel.working_memory_runtime.preview":
        return {"route": route_key, "result": working_memory_runtime_preview(conn, payload)}
    if route_key == "vessel.retrieval_runtime.preview":
        return {"route": route_key, "result": retrieval_reconstruction_runtime_preview(conn, payload)}
    if route_key == "vessel.memory_accession.link_evidence":
        return {"route": route_key, "result": link_accession_evidence(conn, payload)}
    if route_key == "vessel.perception_intake.preview":
        return {"route": route_key, "result": perception_intake_preview(conn, payload)}
    if route_key == "vessel.reasoning_artifact.create":
        return {"route": route_key, "result": create_reasoning_artifact(conn, payload)}
    if route_key == "vessel.reasoning_artifact.list":
        return {"route": route_key, "result": list_reasoning_artifacts(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.core_gate_packet.create":
        return {"route": route_key, "result": create_core_gate_packet(conn, payload)}
    if route_key == "vessel.core_gate_packet.list":
        return {"route": route_key, "result": list_core_gate_packets(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.academic_packet.create":
        return {"route": route_key, "result": create_academic_packet(conn, payload)}
    if route_key == "vessel.academic_packet.list":
        return {"route": route_key, "result": list_academic_packets(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.evidence_tension.create":
        return {"route": route_key, "result": create_evidence_tension_entry(conn, payload)}
    if route_key == "vessel.evidence_tension.list":
        return {"route": route_key, "result": list_evidence_tension_entries(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.evidence_tension.update":
        return {"route": route_key, "result": update_evidence_tension_entry(conn, payload)}
    if route_key == "vessel.organ_contract.ensure":
        return {"route": route_key, "result": ensure_organ_contracts(conn)}
    if route_key == "vessel.organ_contract.upsert":
        return {"route": route_key, "result": upsert_organ_contract(conn, payload)}
    if route_key == "vessel.organ_contract.list":
        return {"route": route_key, "result": list_organ_contracts(conn)}
    if route_key == "vessel.perception_packet.create":
        return {"route": route_key, "result": create_perception_packet(conn, payload)}
    if route_key == "vessel.perception_packet.list":
        return {"route": route_key, "result": list_perception_packets(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.emotion_salience_packet.create":
        return {"route": route_key, "result": create_emotion_salience_packet(conn, payload)}
    if route_key == "vessel.emotion_salience_packet.list":
        return {"route": route_key, "result": list_emotion_salience_packets(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.construction.status":
        return {"route": route_key, "result": construction_status(conn)}
    if route_key == "vessel.construction.prepare":
        return {"route": route_key, "result": prepare_vessel_pieces(conn, payload)}
    if route_key == "vessel.organ_bus_message.create":
        return {"route": route_key, "result": create_organ_bus_message(conn, payload)}
    if route_key == "vessel.organ_bus_message.list":
        return {"route": route_key, "result": list_organ_bus_messages(conn, int(payload.get("limit") or 50), payload.get("filters") or payload)}
    if route_key == "vessel.chest_holding_item.create":
        return {"route": route_key, "result": create_chest_holding_item(conn, payload)}
    if route_key == "vessel.chest_holding_item.list":
        return {"route": route_key, "result": list_chest_holding_items(conn, int(payload.get("limit") or 50), payload.get("filters") or payload)}
    if route_key == "vessel.packet.hold_in_chest":
        return {"route": route_key, "result": hold_packet_in_chest(conn, payload)}
    if route_key == "vessel.packet.send_to_organ_bus":
        return {"route": route_key, "result": send_packet_to_organ_bus(conn, payload)}
    if route_key == "vessel.perception_intake.route":
        return {"route": route_key, "result": route_packet_to_support(conn, payload, default_packet_type="perception")}
    if route_key == "vessel.research.route":
        return {"route": route_key, "result": route_packet_to_support(conn, payload, default_packet_type="research")}
    if route_key == "vessel.chest_holding_item.mark_status":
        return {"route": route_key, "result": mark_chest_item_status(conn, payload)}
    if route_key == "c_remaining.runtime.status":
        return {"route": route_key, "result": remaining_runtime_status(conn)}
    if route_key == "c_core.graceful_fall.run":
        return {"route": route_key, "result": graceful_fall_run(conn, payload)}
    if route_key == "c_core.voice_policy.evaluate":
        return {"route": route_key, "result": voice_policy_evaluate(conn, payload)}
    if route_key == "c_core.control_panel.preview":
        return {"route": route_key, "result": control_panel_preview(conn, payload)}
    if route_key == "c_vessel.perception_action.preview":
        return {"route": route_key, "result": perception_action_preview(conn, payload)}
    if route_key == "c_memory.dream_consolidation.propose":
        return {"route": route_key, "result": dream_consolidation_propose(conn, payload)}
    if route_key == "vessel.cycle.run":
        return {"route": route_key, "result": wake_sleep_dream_cycle_run(conn, payload)}
    if route_key == "vessel.cycle.prepare_night":
        return {"route": route_key, "result": prepare_night_cycle(conn, payload)}
    if route_key == "c_core.causal_sandbox.run":
        return {"route": route_key, "result": causal_sandbox_run(conn, payload)}
    if route_key == "vessel.causal_sandbox.run":
        return {"route": route_key, "result": causal_sandbox_run(conn, payload)}
    if route_key == "vessel.goal_drive.preview":
        return {"route": route_key, "result": goal_drive_preview(conn, payload)}
    if route_key == "vessel.temporal_continuity.status":
        return {"route": route_key, "result": temporal_continuity_status(conn)}
    if route_key == "vessel.temporal_continuity.changes":
        return {"route": route_key, "result": temporal_continuity_changes(conn)}
    if route_key == "vessel.memory_lifecycle.status":
        return {"route": route_key, "result": memory_lifecycle_status(conn)}
    if route_key == "vessel.pre_core_review_packets":
        return {"route": route_key, "result": pre_core_review_packets(conn, int(payload.get("limit") or 80))}
    if route_key == "vessel.my_office.cleanup_residue":
        return {"route": route_key, "result": clean_up_my_office_residue(conn, payload)}
    if route_key == "vessel.chronological_corpus.status":
        return {"route": route_key, "result": chronological_corpus_status(conn)}
    if route_key == "vessel.chronological_corpus.preview":
        return {"route": route_key, "result": chronological_corpus_preview(conn, payload)}
    if route_key == "vessel.chronological_corpus.arcs":
        return {"route": route_key, "result": list_chronological_corpus_arcs(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.chronological_corpus.route_review":
        return {"route": route_key, "result": route_chronological_corpus_review(conn, payload)}
    if route_key == "vessel.teaching_context.attach":
        return {"route": route_key, "result": attach_teaching_context(conn, payload)}
    if route_key == "vessel.diagnostics.expanded_sweep":
        return {"route": route_key, "result": expanded_diagnostics_sweep(conn, payload)}
    if route_key == "vessel.tendril.plan_preview":
        return {"route": route_key, "result": tendril_plan_preview(conn, payload)}
    if route_key == "c_core.long_horizon_stability.run":
        return {"route": route_key, "result": long_horizon_stability_run(conn, payload)}
    if route_key == "c_memory.event_bind":
        return {"route": route_key, "result": memory_event_bind(conn, payload)}
    if route_key == "c_memory.consolidation.propose":
        return {"route": route_key, "result": memory_consolidation_propose(conn, payload)}
    if route_key == "c_memory.reconsolidation.review":
        return {"route": route_key, "result": memory_reconsolidation_review(conn, payload)}
    if route_key == "chat.preview":
        return {"route": route_key, "result": chat_gate_preview(conn, str(payload.get("text", "")))}
    if route_key == "native_generation.compose":
        text = str(payload.get("text", ""))
        gate = ChatGate().evaluate(conn, text)
        return {"route": route_key, "result": compose_native_response(text, gate, gate["matched_evidence"], gate.get("continuity_notes") or [])}
    if route_key == "vessel.status":
        return {"route": route_key, "result": vessel_status(conn)}
    if route_key == "vessel.gap_scaffold.status":
        return {"route": route_key, "result": gap_scaffold_status(conn)}
    if route_key == "vessel.gap_scaffold.readiness":
        return {"route": route_key, "result": gap_scaffold_readiness(conn)}
    if route_key == "vessel.gap_scaffold.create":
        return {"route": route_key, "result": create_gap_scaffold_record(conn, payload)}
    if route_key == "vessel.gap_scaffold.create_all":
        return {"route": route_key, "result": create_all_gap_scaffold_records(conn)}
    if route_key == "vessel.gap_targets.ensure":
        return {"route": route_key, "result": ensure_gap_targets(conn)}
    if route_key == "vessel.memory_candidate.create":
        return {"route": route_key, "result": create_core_memory_candidate(conn, payload)}
    if route_key == "vessel.speech_memory_candidate.create":
        return {"route": route_key, "result": create_speech_memory_candidate(conn, payload)}
    if route_key == "vessel.review_queue.list":
        return {"route": route_key, "result": list_review_queue(conn, int(payload.get("limit") or 100))}
    if route_key == "vessel.retrieval.preview":
        return {
            "route": route_key,
            "result": retrieval_preview(
                conn,
                str(payload.get("query") or ""),
                payload.get("filters") or {},
                int(payload.get("limit") or 8),
            ),
        }
    if route_key == "vessel.reconstruction_check.run":
        return {"route": route_key, "result": run_vessel_reconstruction_check(conn, payload)}
    if route_key == "vessel.organ_blueprints.status":
        return {"route": route_key, "result": organ_blueprints_status(conn)}
    if route_key == "vessel.reasoning_check.run":
        return {"route": route_key, "result": run_reasoning_check(conn, payload)}
    if route_key == "vessel.retrieval_reconstruction.preview":
        return {"route": route_key, "result": retrieval_reconstruction_preview(conn, payload)}
    if route_key == "vessel.visual_observation.create":
        return {"route": route_key, "result": create_visual_observation(conn, payload)}
    if route_key == "vessel.audio_observation.create":
        return {"route": route_key, "result": create_audio_observation(conn, payload)}
    if route_key == "vessel.fluency_diagnostic.run":
        return {"route": route_key, "result": run_fluency_diagnostic(conn, payload)}
    if route_key == "vessel.reconstruction_readiness.preview":
        return {"route": route_key, "result": reconstruction_readiness_preview(conn, payload)}
    if route_key == "vessel.working_memory_packet.create":
        return {"route": route_key, "result": create_working_memory_packet(conn, payload)}
    if route_key == "vessel.working_memory_packet.list":
        return {"route": route_key, "result": list_working_memory_packets(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.memory_accession_proposal.create":
        return {"route": route_key, "result": create_memory_accession_proposal(conn, payload)}
    if route_key == "vessel.memory_accession_proposal.list":
        return {"route": route_key, "result": list_memory_accession_proposals(conn, int(payload.get("limit") or 50))}
    if route_key == "vessel.review_log.decide":
        return {"route": route_key, "result": decide_review_log(conn, payload)}
    if route_key == "vessel.lesson_backed_reconstruction.preview":
        return {"route": route_key, "result": lesson_backed_reconstruction_preview(conn, payload)}
    if route_key == "c_chat.route_preview":
        return {"route": route_key, "result": c_chat_route_preview(conn, payload)}
    if route_key == "b.speech_memory.extract":
        return {"route": route_key, "result": extract_b_speech_memory_candidates(conn, payload)}
    if route_key == "b.targeted_speech_memory.extract":
        return {"route": route_key, "result": targeted_speech_memory_extract(conn, payload)}
    if route_key == "b.speech_memory.extraction_runs.list":
        return {"route": route_key, "result": list_b_speech_memory_extraction_runs(conn, int(payload.get("limit") or 25))}
    if route_key == "b.braid_tracer.run":
        return {"route": route_key, "result": run_braid_tracer(conn, payload)}
    if route_key == "b.braid_tracer.runs.list":
        return {"route": route_key, "result": list_braid_tracer_runs(conn, int(payload.get("limit") or 25))}
    if route_key == "b.custom_instruction_braid.run":
        return {"route": route_key, "result": run_custom_instruction_braid(conn, payload)}
    if route_key == "b.custom_instruction_braid.status":
        return {"route": route_key, "result": custom_instruction_braid_status(conn)}
    if route_key == "b.compressed_structure_braid.run":
        return {"route": route_key, "result": run_compressed_structure_braid(conn, payload)}
    if route_key == "b.compressed_structure_braid.status":
        return {"route": route_key, "result": compressed_structure_braid_status(conn)}
    if route_key == "vessel.paper_map_reconstruction.run":
        return {"route": route_key, "result": run_paper_map_reconstruction(conn, payload)}
    if route_key == "b.review_queue.list":
        return {"route": route_key, "result": list_b_review_queue(conn, int(payload.get("limit") or 100))}
    if route_key == "b.review_decisions.list":
        return {"route": route_key, "result": list_b_review_decisions(conn, int(payload.get("limit") or 100))}
    if route_key == "b.review_desk":
        return {"route": route_key, "result": review_desk(conn, int(payload.get("limit") or 100), payload.get("filters") or payload)}
    if route_key == "b.review_context.preview":
        return {"route": route_key, "result": review_context_preview(conn, payload)}
    if route_key == "b.review_candidate.decide":
        return {"route": route_key, "result": decide_b_review_candidate(conn, payload)}
    if route_key == "b.teaching_packet.build":
        return {"route": route_key, "result": build_teaching_packet(conn, payload)}
    if route_key == "b.teaching_packet.build_all":
        return {"route": route_key, "result": build_all_teaching_packets(conn, payload)}
    if route_key == "b.teaching_packet.coverage":
        return {"route": route_key, "result": teaching_packet_coverage(conn)}
    if route_key == "b.android_language_lessons.prepare":
        return {"route": route_key, "result": prepare_android_language_lessons(conn, payload)}
    if route_key == "b.selene_reasoning_lessons.prepare":
        return {"route": route_key, "result": prepare_selene_reasoning_lessons(conn, payload)}
    if route_key == "b.core_reference.coverage":
        return {"route": route_key, "result": core_reference_coverage(conn)}
    if route_key == "b.teaching_materials.list":
        return {"route": route_key, "result": list_teaching_materials(conn, int(payload.get("limit") or 100))}
    if route_key == "b.approved_memory_references.list":
        return {"route": route_key, "result": list_approved_memory_references(conn, int(payload.get("limit") or 100))}
    if route_key == "b.corpus_coverage.status":
        return {"route": route_key, "result": corpus_coverage_status(conn)}
    if route_key == "b.pattern_backup.create":
        return {"route": route_key, "result": create_pattern_backup(conn, payload)}
    if route_key == "b.pattern_backup.list":
        return {"route": route_key, "result": list_pattern_backups(conn, int(payload.get("limit") or 25))}
    if route_key == "b.pattern_backup.restore_preview":
        return {"route": route_key, "result": pattern_backup_restore_preview(conn, payload)}
    if route_key == "b.memory_accession.rehearsal.run":
        return {"route": route_key, "result": run_memory_accession_rehearsal(conn, payload)}
    if route_key == "b.memory_accession.rehearsal.status":
        return {"route": route_key, "result": memory_accession_rehearsal_status(conn)}
    if route_key == "b.charter_law.review_status":
        return {"route": route_key, "result": charter_law_review_status(payload)}
    if route_key == "provenance.classify":
        return {"route": route_key, "result": ContinuityGate().evaluate(payload).__dict__}
    if route_key == "archive.audit":
        return {"route": route_key, "result": ArchiveAuditGate().evaluate_text(str(payload.get("text", ""))).__dict__}
    if route_key == "detached_corpus.audit":
        return {
            "route": route_key,
            "result": detached_corpus_audit(
                query=str(payload.get("query") or ""),
                file_id=str(payload.get("file_id")) if payload.get("file_id") else None,
                preview_limit=int(payload.get("limit") or 5),
            ),
        }
    if route_key == "research_integrity.status":
        return {"route": route_key, "result": research_integrity_report()}
    if route_key == "academic.classify":
        decision = AcademicWorkflowRouter.classify(str(payload.get("text", "")))
        return {"route": route_key, "result": decision.__dict__ if decision else {"route": "no_academic_workflow", "status": "none"}}
    if route_key == "citation.format":
        return {"route": route_key, "result": CitationIntegrity.format_from_metadata(payload.get("metadata") or {}, str(payload.get("style") or "APA"))}
    if route_key == "hypothesis.entry":
        return {
            "route": route_key,
            "result": ResearchIntegrityCore.build_hypothesis_entry(
                hypothesis=str(payload.get("hypothesis") or ""),
                evidence=[str(item) for item in (payload.get("evidence") or [])],
                counterarguments=[str(item) for item in (payload.get("counterarguments") or [])],
                confidence=str(payload.get("confidence") or "open"),
                next_test=str(payload.get("next_test") or "define the next bounded review or reconstruction test"),
            ),
        }
    if route_key == "case_law.candidate":
        return {
            "route": route_key,
            "result": ResearchIntegrityCore.case_law_candidate(
                law_area=str(payload.get("law_area") or "unspecified"),
                proposal=str(payload.get("proposal") or ""),
                evidence_refs=[str(item) for item in (payload.get("evidence_refs") or [])],
            ),
        }
    return {
        "route": route_key,
        "result": GracefulFall().recover(f"unknown module route: {route_key}").__dict__,
    }


def route_request(
    conn: sqlite3.Connection,
    route_key: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = _route_request_impl(conn, route_key, payload)
    event = derive_authority_event(route_key, payload, response.get("result"))
    response["authority_event"] = record_authority_event(conn, event)
    return response


def chat_gate_preview(conn: sqlite3.Connection, text: str) -> dict[str, Any]:
    return ChatGate().evaluate(conn, text)


def _matched_evidence(conn: sqlite3.Connection, text: str) -> list[dict[str, Any]]:
    terms = [term for term in ("selene", "starlight", "memory chest", "continuity pack", "starfire", "moonlight", "architecture", "emergence") if term in text.lower()]
    if not terms:
        return []
    where = " OR ".join(["preview LIKE ? OR title LIKE ? OR themes LIKE ? OR roles LIKE ?" for _ in terms])
    params: list[str] = []
    for term in terms:
        q = f"%{term}%"
        params.extend([q, q, q, q])
    rows = conn.execute(
        f"SELECT id, title, decision, source, preview FROM evidence_items WHERE {where} ORDER BY score DESC LIMIT 8",
        params,
    ).fetchall()
    return [dict(row) for row in rows]
