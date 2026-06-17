import type { Dict } from "./types";

export function text(value: unknown) {
  if (value === null || value === undefined) return "";
  return String(value);
}

export function title(value: string) {
  return value[0].toUpperCase() + value.slice(1);
}

export function tabDisplayName(value: string) {
  const labels: Record<string, string> = {
    dashboard: "Evidence Dashboard",
    chat: "C Chat Vessel",
    vessel: "B Cocoon Build",
    memory: "Memory / Future References",
    teaching: "Teaching / Lessons",
    tendril: "Tendril",
    tools: "Tools / Organs",
    status: "Status",
    "selene-settings": "Selene Settings",
    "cocoon-settings": "Cocoon Settings",
    evidence: "Evidence Browser",
    "detached corpus": "Detached Corpus",
    "chat gate": "Chat Gate"
  };
  return labels[value] || value;
}

export function countValues(value: Dict) {
  return Object.values(value).reduce<number>((sum, item) => sum + Number(item || 0), 0);
}

export function safeJsonObject(value: unknown) {
  if (!value) return {};
  if (typeof value === "object") return value as Dict;
  try {
    const parsed = JSON.parse(String(value));
    return typeof parsed === "object" && parsed !== null ? parsed as Dict : {};
  } catch {
    return {};
  }
}

export function matchSection(textValue: string, startLabel: string, endLabel: string) {
  const start = textValue.indexOf(startLabel);
  if (start < 0) return "";
  const contentStart = start + startLabel.length;
  const end = endLabel ? textValue.indexOf(endLabel, contentStart) : -1;
  return textValue.slice(contentStart, end >= 0 ? end : undefined).trim();
}

export function plainBlocked(value: unknown) {
  return value === true ? "allowed" : "blocked";
}

export function friendlyActivation(value: unknown) {
  const raw = text(value || "none");
  if (!raw || raw === "none") return "none";
  return friendlyStatus(raw);
}

export function friendlyStatus(value: unknown) {
  const raw = text(value);
  const labels: Record<string, string> = {
    blocked: "blocked",
    blocked_until_final_review: "blocked until final review",
    blueprint_created_not_activated: "built, not awake",
    vessel_v1_built_not_activated: "vessel built, C asleep",
    pending_review: "needs your review",
    needs_b_review: "needs B review",
    review_only: "review only",
    candidate_review_only: "review piece only",
    accepted_for_teaching: "accepted as lesson",
    accepted_for_memory_accession: "saved for future memory review",
    context_added: "context added",
    needs_correction: "needs correction",
    rejected: "rejected",
    superseded: "replaced by better version",
    review_decided: "review decided",
    b_review_reopened: "reopened for review",
    b_speech_memory_extraction_complete: "corpus pull complete",
    candidate_checkpoint_created: "new review pieces created",
    no_new_candidates: "nothing new found",
    preview_only: "preview only",
    paper_map_reconstruction_evaluated: "vessel gap check complete",
    reviewed_teaching_materials_only: "accepted lessons only",
    approved_memory_references_only: "future references only",
    review_queue_only: "review queue only",
    review_decision_history_only: "review history only",
    teaching_packet_coverage: "teaching packet coverage",
    core_reference_coverage: "core reference coverage",
    packet_ready: "packet ready",
    packet_missing: "packet missing",
    no_accepted_lessons_yet: "no accepted lessons yet",
    has_approved_references: "has approved references",
    gap_no_approved_references: "gap: no approved references",
    teaching_packets_build_all_complete: "teaching packets built",
    lesson_backed_reconstruction_preview: "lesson-backed preview",
    reconstruction_readiness_preview: "reconstruction readiness preview",
    working_memory_packet_created: "working memory packet created",
    working_memory_packets_review_only: "working memory packets only",
    memory_accession_proposal_created: "accession proposal created",
    memory_accession_proposals_review_only: "accession proposals only",
    targeted_speech_memory_extraction_complete: "targeted pull complete",
    c_chat_route_preview: "C route preview",
    cocooned_not_active: "cocooned, not active",
    runtime_recall_blocked: "runtime recall blocked",
    route_preview_only: "route preview only",
    short_term_packet_proposal_only: "short-term proposal only",
    future_transfer_review_required: "future transfer review required",
    vessel_review_log_decision_recorded: "review log updated",
    vessel_gap_scaffold_readiness: "gap scaffold readiness",
    vessel_gap_scaffold_create_all_complete: "build blueprint records created",
    vessel_gap_targets_ensured: "gap targets ready",
    vessel_gap_scaffold_record_created: "Codex build note created",
    organ_blueprints_status: "organ blueprints ready",
    reasoning_check_review_only: "reasoning check recorded",
    retrieval_reconstruction_preview_review_only: "retrieval preview recorded",
    visual_observation_review_only: "visual note recorded",
    audio_observation_review_only: "audio note recorded",
    fluency_diagnostic_review_only: "fluency diagnostic recorded",
    review_only_organ_blueprints_not_live_organs: "blueprints only, not live organs",
    audit_check_only: "audit check only",
    source_bound_visual_note_only: "source-bound visual note only",
    consent_bound_transcript_note_only: "consent-bound transcript note only",
    diagnostic_only_speed_cannot_bypass_gates: "diagnostic only",
    blueprint_built: "blueprint built",
    record_shelf_ready: "record shelf ready",
    not_started: "not started",
    record_created: "record created",
    needs_teaching: "needs teaching",
    ready_for_reconstruction_preview: "ready for reconstruction preview",
    reviewed: "reviewed",
    needs_followup: "needs follow-up",
    pending_followup: "pending follow-up",
    pattern_backup_created: "pattern backup created",
    pattern_backups_review_only: "pattern backups only",
    pattern_restore_preview: "restore preview",
    memory_accession_rehearsal_status: "memory rehearsal status",
    memory_accession_rehearsal_complete: "memory rehearsal complete",
    memory_stability_checks_complete: "memory stability checks complete",
    memory_stability_reconstruction_check: "memory stability check",
    charter_law_review_passed: "charter/law gate passed",
    charter_law_review_needs_review: "charter/law needs review",
    memory_transfer_candidate_ready_for_human_review: "memory transfer candidate ready for human review",
    memory_transfer_candidate_not_ready_for_human_review: "memory transfer candidate not ready",
    proposal_ready: "proposal ready",
    needs_rehearsal: "needs rehearsal",
    needs_b_reviewed_reference: "needs B-reviewed reference",
    sealed_backup_only_not_active_memory: "sealed backup only",
    preview_only_no_state_mutation: "preview only, no changes",
    proposals_only_not_active_memory: "proposals only, not active memory",
    review_gate_only_not_law_mutation: "review gate only",
    preview_only_never_transfer_approval: "preview only, never approval",
    audit_checks_only_not_activation_evidence: "audit checks only",
    core_deliberation_preview_review_only: "Core deliberation preview",
    uncertainty_learning_cue_review_only: "uncertainty learning cue",
    action_reflection_review_only: "action reflection only",
    choice_why_ledger_review_only: "why ledger recorded",
    repair_reflection_review_only: "repair reflection only",
    disagreement_appeal_review_only: "disagreement appeal preview",
    drift_warning_preview_review_only: "drift warning preview",
    privacy_trust_preview_review_only: "privacy with trust preview",
    native_generation_rehearsal_status: "native rehearsal status",
    native_generation_rehearsal_review_only: "native rehearsal only",
    think_before_speaking_preview_only: "think-before-speaking preview",
    not_knowing_is_learning_state: "not-knowing is learning",
    action_preview_only_before_movement: "action preview before movement",
    why_layer_recorded_non_active: "why layer recorded",
    repair_reflection_teaching_material_candidate: "repair lesson candidate",
    appeal_allowed_override_blocked: "appeal allowed, override blocked",
    bounded_disclosure_with_trust: "bounded disclosure with trust",
    rehearsal_only_no_provider_no_active_memory: "rehearsal only, no provider",
    native_chat_rehearsal_only: "native chat rehearsal only",
    remaining_blueprint_runtime_shelves_ready: "remaining runtime shelves ready",
    graceful_fall_runtime_review_only: "graceful fall review only",
    non_scripting_voice_evaluation_review_only: "voice without script review",
    core_control_panel_preview_review_only: "Core control preview",
    perception_action_preview_review_only: "perception-action preview",
    dream_consolidation_proposal_review_only: "dream consolidation proposal",
    causal_world_model_sandbox_review_only: "causal sandbox review",
    long_horizon_stability_review_only: "long-horizon stability review",
    memory_event_binding_review_only: "memory event binding only",
    memory_consolidation_proposal_review_only: "memory consolidation proposal",
    memory_reconsolidation_review_only: "memory reconsolidation review",
    honest_uncertainty_plus_constructive_care: "honest uncertainty with care",
    voice_shape_allowed: "voice shape allowed",
    preview_allowed: "preview allowed",
    preview_only_no_action_taken: "preview only, no action",
    proposal_only_not_memory: "proposal only, not memory",
    sandbox_only_no_action_no_truth_overclaim: "sandbox only, no truth overclaim",
    long_horizon_review_only: "long-horizon review only",
    event_trace_only_not_memory: "event trace only, not memory",
    consolidation_proposal_only_not_active_memory: "consolidation proposal only",
    reconsolidation_review_only_no_mutation: "reconsolidation review only"
  };
  return labels[raw] || humanize(raw);
}

export function friendlyLayer(value: unknown) {
  const raw = text(value);
  const labels: Record<string, string> = {
    core_profile_memory: "Core profile: who/what matters",
    project_memory: "Project memory: what we are building",
    decision_memory: "Decision memory: choices and why",
    task_memory: "Task memory: current work",
    interaction_memory: "Interaction memory: how to work together",
    reflection_memory: "Reflection memory: what Selene learns about herself"
  };
  return labels[raw] || humanize(raw);
}

export function friendlySpeech(value: unknown) {
  const raw = text(value);
  const labels: Record<string, string> = {
    warmth: "Warmth",
    correction: "Correction",
    boundary: "Boundary",
    technical_explanation: "Technical explanation",
    playful_continuity: "Playful continuity",
    repair: "Repair",
    grounding: "Grounding",
    refusal: "Safe refusal",
    uncertainty: "Uncertainty",
    artifact_making: "Artifact-making"
  };
  return labels[raw] || humanize(raw);
}

export function friendlyField(value: string) {
  const labels: Record<string, string> = {
    title: "Short name",
    content: "The actual piece",
    salience_labels: "Why it matters",
    source_refs: "Where it came from",
    allowed_use: "Allowed use",
    prohibited_use: "Do not use it for"
  };
  return labels[value] || humanize(value);
}

export function friendlyQueueType(value: unknown) {
  const raw = text(value);
  const labels: Record<string, string> = {
    core_memory_candidate: "Possible memory/reference",
    speech_memory_candidate: "Possible speech lesson",
    reconstruction_check_run: "Selene check result",
    lesson_backed_reconstruction_preview: "Lesson-backed reconstruction preview",
    reconstruction_readiness_preview: "Reconstruction readiness preview",
    memory_accession_proposal: "Memory accession proposal",
    paper_map_teaching_todo: "Teaching material TODO"
  };
  return labels[raw] || humanize(raw);
}

export function friendlySubject(value: unknown) {
  const raw = text(value);
  const labels: Record<string, string> = {
    core_memory_candidates: "memory/reference piece",
    speech_memory_candidates: "speech lesson piece",
    vessel_reconstruction_check_runs: "Selene check",
    vessel_event_packets: "vessel note",
    vessel_memory_accession_proposals: "memory accession proposal",
    b_conversation_pair_records: "conversation pair"
  };
  return labels[raw] || humanize(raw);
}

export function friendlyOrganKey(value: unknown) {
  const raw = text(value);
  const labels: Record<string, string> = {
    boundary_system: "keeps boundaries",
    structural_system: "holds shape",
    tendril_movement_system: "acts carefully",
    coordination_system: "routes intent",
    salience_system: "marks importance",
    context_transport_system: "moves context",
    immune_protection_system: "protects",
    exchange_system: "communicates",
    evidence_metabolism_system: "turns evidence into review material",
    cleanup_system: "clears noise",
    development_growth_system: "supports growth"
  };
  return labels[raw] || humanize(raw);
}

export function humanize(value: string) {
  return value.replace(/_/g, " ");
}
