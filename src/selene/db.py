from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence_items (
  id TEXT PRIMARY KEY,
  layer TEXT NOT NULL,
  item_type TEXT NOT NULL,
  title TEXT,
  phase TEXT,
  themes TEXT,
  tier TEXT,
  confidence TEXT,
  decision TEXT NOT NULL,
  roles TEXT,
  score REAL,
  source TEXT,
  month TEXT,
  formation_period TEXT,
  preview TEXT,
  human_note TEXT,
  sensitivity_labels TEXT,
  source_file TEXT NOT NULL,
  imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS anchors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  anchor TEXT NOT NULL,
  anchor_type TEXT NOT NULL,
  evidence_id TEXT,
  decision TEXT,
  confidence TEXT,
  source TEXT,
  preview TEXT,
  review_status TEXT,
  human_note TEXT,
  confidence_override TEXT,
  role_labels TEXT,
  provenance_note TEXT,
  updated_at TEXT,
  FOREIGN KEY (evidence_id) REFERENCES evidence_items(id)
);

CREATE TABLE IF NOT EXISTS continuity_candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evidence_id TEXT NOT NULL,
  status TEXT NOT NULL,
  gate_reason TEXT NOT NULL,
  roles TEXT,
  source TEXT,
  preview TEXT,
  review_status TEXT,
  human_note TEXT,
  confidence_override TEXT,
  role_labels TEXT,
  provenance_note TEXT,
  updated_at TEXT,
  FOREIGN KEY (evidence_id) REFERENCES evidence_items(id)
);

CREATE TABLE IF NOT EXISTS emergence_observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evidence_id TEXT NOT NULL,
  signal_type TEXT NOT NULL,
  confidence_label TEXT NOT NULL,
  interpretation TEXT NOT NULL,
  counterargument TEXT NOT NULL,
  source TEXT,
  preview TEXT,
  FOREIGN KEY (evidence_id) REFERENCES evidence_items(id)
);

CREATE TABLE IF NOT EXISTS pattern_rules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  module TEXT NOT NULL,
  rule_key TEXT NOT NULL UNIQUE,
  rule_text TEXT NOT NULL,
  boundary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gate_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  gate_name TEXT NOT NULL,
  route TEXT NOT NULL,
  reason TEXT NOT NULL,
  payload_preview TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS artifact_exports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_type TEXT NOT NULL,
  path TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS review_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  table_name TEXT NOT NULL,
  row_id INTEGER NOT NULL,
  field_name TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT,
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS module_contracts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  module TEXT NOT NULL,
  route_key TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL,
  input_contract TEXT NOT NULL,
  output_contract TEXT NOT NULL,
  boundary TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifact_workflows (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workflow_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  output_type TEXT NOT NULL,
  route_key TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  gate_route TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

CREATE TABLE IF NOT EXISTS chat_gate_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id INTEGER NOT NULL,
  route TEXT NOT NULL,
  anti_spiral_status TEXT NOT NULL,
  boundary_status TEXT NOT NULL,
  continuity_status TEXT NOT NULL,
  result_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (message_id) REFERENCES chat_messages(id)
);

CREATE TABLE IF NOT EXISTS chat_citations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id INTEGER NOT NULL,
  evidence_id TEXT NOT NULL,
  citation_type TEXT NOT NULL,
  decision TEXT NOT NULL,
  confidence TEXT,
  source TEXT,
  title TEXT,
  preview TEXT,
  reason_matched TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (message_id) REFERENCES chat_messages(id)
);

CREATE TABLE IF NOT EXISTS continuity_save_requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id INTEGER NOT NULL,
  requested_text TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending_review',
  user_phrase TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (message_id) REFERENCES chat_messages(id)
);

CREATE TABLE IF NOT EXISTS continuity_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  note_type TEXT NOT NULL,
  label TEXT NOT NULL,
  aliases TEXT,
  meaning TEXT NOT NULL,
  allowed_use TEXT,
  prohibited_use TEXT,
  status TEXT NOT NULL DEFAULT 'review_only',
  confidence TEXT NOT NULL DEFAULT 'open',
  source TEXT,
  source_ref TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_continuity_notes_status ON continuity_notes(status);
CREATE INDEX IF NOT EXISTS idx_continuity_notes_label ON continuity_notes(label);

CREATE TABLE IF NOT EXISTS evidence_embeddings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evidence_id TEXT NOT NULL UNIQUE,
  source_type TEXT NOT NULL,
  model_name TEXT NOT NULL,
  embedding_dim INTEGER,
  embedding_blob BLOB,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  error TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (evidence_id) REFERENCES evidence_items(id)
);

CREATE INDEX IF NOT EXISTS idx_evidence_embeddings_status ON evidence_embeddings(status);
CREATE INDEX IF NOT EXISTS idx_evidence_embeddings_source ON evidence_embeddings(source_type, evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_embeddings_hash ON evidence_embeddings(content_hash);

CREATE TABLE IF NOT EXISTS vessel_event_packets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  packet_type TEXT NOT NULL,
  organ_system TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_event_packets_status ON vessel_event_packets(status, review_status);
CREATE INDEX IF NOT EXISTS idx_vessel_event_packets_organ ON vessel_event_packets(organ_system);

CREATE TABLE IF NOT EXISTS core_memory_candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  core_memory_layer TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  salience_labels TEXT NOT NULL DEFAULT '[]',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  status TEXT NOT NULL DEFAULT 'candidate_review_only',
  allowed_use TEXT,
  prohibited_use TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_core_memory_candidates_layer ON core_memory_candidates(core_memory_layer);
CREATE INDEX IF NOT EXISTS idx_core_memory_candidates_status ON core_memory_candidates(status, review_status);

CREATE TABLE IF NOT EXISTS speech_memory_candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  core_memory_layer TEXT NOT NULL,
  speech_function TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  salience_labels TEXT NOT NULL DEFAULT '[]',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  status TEXT NOT NULL DEFAULT 'candidate_review_only',
  allowed_use TEXT,
  prohibited_use TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_speech_memory_candidates_layer ON speech_memory_candidates(core_memory_layer);
CREATE INDEX IF NOT EXISTS idx_speech_memory_candidates_function ON speech_memory_candidates(speech_function);
CREATE INDEX IF NOT EXISTS idx_speech_memory_candidates_status ON speech_memory_candidates(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_review_queue (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  queue_type TEXT NOT NULL,
  subject_table TEXT NOT NULL,
  subject_id INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending_review',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  reason TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_review_queue_status ON vessel_review_queue(status, review_status);
CREATE INDEX IF NOT EXISTS idx_vessel_review_queue_subject ON vessel_review_queue(subject_table, subject_id);

CREATE TABLE IF NOT EXISTS vessel_retrieval_queries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  query TEXT NOT NULL,
  filters_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'preview_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  result_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_retrieval_queries_status ON vessel_retrieval_queries(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_reconstruction_check_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_text TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  result_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_reconstruction_check_runs_status ON vessel_reconstruction_check_runs(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_gap_scaffold_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  gap_key TEXT NOT NULL,
  scaffold_type TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_gap_scaffold_records_gap ON vessel_gap_scaffold_records(gap_key, scaffold_type);
CREATE INDEX IF NOT EXISTS idx_vessel_gap_scaffold_records_status ON vessel_gap_scaffold_records(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_gap_targets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_type TEXT NOT NULL,
  target_key TEXT NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'target_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(target_type, target_key)
);

CREATE INDEX IF NOT EXISTS idx_vessel_gap_targets_status ON vessel_gap_targets(target_type, status, review_status);

CREATE TABLE IF NOT EXISTS vessel_working_memory_packets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  current_task TEXT NOT NULL,
  active_context_cues TEXT NOT NULL DEFAULT '[]',
  salience_labels TEXT NOT NULL DEFAULT '[]',
  expiry_cleanup_note TEXT NOT NULL,
  interrupt_resume_note TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'working_memory_packet_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_working_memory_packets_status ON vessel_working_memory_packets(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_memory_accession_proposals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  core_memory_layer TEXT NOT NULL,
  title TEXT NOT NULL,
  rationale TEXT NOT NULL,
  reversal_conditions TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'memory_accession_proposal_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_memory_accession_proposals_layer ON vessel_memory_accession_proposals(core_memory_layer, review_status);

CREATE TABLE IF NOT EXISTS vessel_reasoning_check_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  problem TEXT NOT NULL,
  assumptions TEXT NOT NULL DEFAULT '[]',
  checked_steps TEXT NOT NULL DEFAULT '[]',
  uncertainty TEXT NOT NULL DEFAULT '',
  result_summary TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'reasoning_check_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_reasoning_check_records_status ON vessel_reasoning_check_records(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_retrieval_reconstruction_previews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cue TEXT NOT NULL,
  privacy_label TEXT NOT NULL DEFAULT 'review_only',
  bounded_preview TEXT NOT NULL,
  confidence TEXT NOT NULL DEFAULT 'low',
  uncertainty TEXT NOT NULL DEFAULT '',
  reconstruction_note TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'retrieval_reconstruction_preview_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_retrieval_reconstruction_previews_status ON vessel_retrieval_reconstruction_previews(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_visual_observation_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_label TEXT NOT NULL,
  observation TEXT NOT NULL,
  interpretation TEXT NOT NULL DEFAULT '',
  uncertainty TEXT NOT NULL DEFAULT '',
  munsell_salience_labels TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'visual_observation_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_visual_observation_records_status ON vessel_visual_observation_records(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_audio_observation_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  transcript_label TEXT NOT NULL,
  speaker_source_labels TEXT NOT NULL DEFAULT '[]',
  bounded_transcript_preview TEXT NOT NULL,
  audio_cues TEXT NOT NULL DEFAULT '[]',
  consent_note TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'audio_observation_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_audio_observation_records_status ON vessel_audio_observation_records(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_fluency_diagnostic_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  route_label TEXT NOT NULL,
  latency_ms INTEGER NOT NULL DEFAULT 0,
  organ_activation_budget TEXT NOT NULL DEFAULT '',
  fluency_note TEXT NOT NULL,
  drift_flags TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'fluency_diagnostic_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_fluency_diagnostic_records_status ON vessel_fluency_diagnostic_records(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_speech_generation_rehearsals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prompt TEXT NOT NULL,
  speech_function TEXT NOT NULL DEFAULT 'grounding',
  candidate_text TEXT NOT NULL,
  uncertainty TEXT NOT NULL DEFAULT '',
  evidence_used TEXT NOT NULL DEFAULT '[]',
  source_refs TEXT NOT NULL DEFAULT '[]',
  recognition_check_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'speech_generation_rehearsal_review_only',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_speech_generation_rehearsals_status ON vessel_speech_generation_rehearsals(status, review_status);

CREATE TABLE IF NOT EXISTS c_core_deliberation_previews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prompt TEXT NOT NULL,
  intent_summary TEXT NOT NULL,
  why_summary TEXT NOT NULL,
  deliberation_steps_json TEXT NOT NULL DEFAULT '[]',
  loop_guard_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'core_deliberation_preview_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_core_deliberation_previews_status ON c_core_deliberation_previews(status, review_status);

CREATE TABLE IF NOT EXISTS c_core_uncertainty_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question TEXT NOT NULL,
  uncertainty_label TEXT NOT NULL,
  best_guess TEXT NOT NULL DEFAULT '',
  learning_cue TEXT NOT NULL,
  clarification_path TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'uncertainty_learning_cue_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_core_uncertainty_records_status ON c_core_uncertainty_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_core_action_reflection_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  action_label TEXT NOT NULL,
  intent TEXT NOT NULL,
  risk_summary TEXT NOT NULL,
  affected_systems_json TEXT NOT NULL DEFAULT '[]',
  why_summary TEXT NOT NULL,
  rollback_path TEXT NOT NULL,
  after_action_reflection TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'action_reflection_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_core_action_reflection_records_status ON c_core_action_reflection_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_core_choice_ledger_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  choice_label TEXT NOT NULL,
  why_summary TEXT NOT NULL,
  tradeoffs TEXT NOT NULL,
  reversal_conditions TEXT NOT NULL,
  authority_boundary TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'choice_why_ledger_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_core_choice_ledger_records_status ON c_core_choice_ledger_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_core_repair_reflection_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lesson_label TEXT NOT NULL,
  lesson_type TEXT NOT NULL,
  what_happened TEXT NOT NULL,
  what_improved TEXT NOT NULL,
  not_knowing_note TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'repair_reflection_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_core_repair_reflection_records_status ON c_core_repair_reflection_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_core_disagreement_appeal_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  disagreement_label TEXT NOT NULL,
  concern TEXT NOT NULL,
  appeal_summary TEXT NOT NULL,
  aleks_authority_boundary TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'disagreement_appeal_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_core_disagreement_appeal_records_status ON c_core_disagreement_appeal_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_core_mind_route_previews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prompt TEXT NOT NULL,
  selected_route TEXT NOT NULL,
  identity_frame_json TEXT NOT NULL DEFAULT '{}',
  reasoning_summary TEXT NOT NULL,
  evidence_used TEXT NOT NULL DEFAULT '[]',
  uncertainty TEXT NOT NULL DEFAULT '',
  ethical_boundary_notes TEXT NOT NULL DEFAULT '[]',
  drift_flags TEXT NOT NULL DEFAULT '[]',
  next_step TEXT NOT NULL,
  review_destination TEXT NOT NULL DEFAULT 'Status',
  status TEXT NOT NULL DEFAULT 'core_mind_route_preview_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_core_mind_route_previews_status ON c_core_mind_route_previews(selected_route, review_status);

CREATE TABLE IF NOT EXISTS c_core_mind_governance_trials (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  scenario_key TEXT NOT NULL,
  prompt TEXT NOT NULL,
  expected_route TEXT NOT NULL,
  actual_route TEXT NOT NULL,
  matched INTEGER NOT NULL DEFAULT 0,
  reasoning_summary TEXT NOT NULL DEFAULT '',
  evidence_used TEXT NOT NULL DEFAULT '[]',
  uncertainty TEXT NOT NULL DEFAULT '',
  drift_flags TEXT NOT NULL DEFAULT '[]',
  review_destination TEXT NOT NULL DEFAULT 'Status',
  status TEXT NOT NULL DEFAULT 'core_mind_governance_trial_status_only',
  review_status TEXT NOT NULL DEFAULT 'status_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_core_mind_governance_trials_run ON c_core_mind_governance_trials(run_id, scenario_key);

CREATE TABLE IF NOT EXISTS c_core_mind_runtime_shell_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  record_type TEXT NOT NULL,
  title TEXT NOT NULL,
  selected_route TEXT NOT NULL DEFAULT 'status_only',
  summary TEXT NOT NULL DEFAULT '',
  uncertainty TEXT NOT NULL DEFAULT '',
  source_refs TEXT NOT NULL DEFAULT '[]',
  review_destination TEXT NOT NULL DEFAULT 'Status',
  status TEXT NOT NULL DEFAULT 'core_mind_runtime_shell_review_only',
  review_status TEXT NOT NULL DEFAULT 'status_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_core_mind_runtime_shell_records_type ON c_core_mind_runtime_shell_records(record_type, review_status);

CREATE TABLE IF NOT EXISTS native_generation_rehearsal_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prompt TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'native_generation_rehearsal_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  result_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_native_generation_rehearsal_runs_status ON native_generation_rehearsal_runs(status, review_status);

CREATE TABLE IF NOT EXISTS c_runtime_graceful_fall_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  uncertainty TEXT NOT NULL,
  best_current_read TEXT NOT NULL,
  constructive_next_step TEXT NOT NULL,
  review_route TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'graceful_fall_runtime_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_runtime_graceful_fall_records_status ON c_runtime_graceful_fall_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_runtime_voice_policy_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_text TEXT NOT NULL,
  evaluation_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'non_scripting_voice_evaluation_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_runtime_voice_policy_records_status ON c_runtime_voice_policy_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_runtime_control_panel_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  command_label TEXT NOT NULL,
  requested_route TEXT NOT NULL,
  decision TEXT NOT NULL,
  affected_systems_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'core_control_panel_preview_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_runtime_control_panel_records_status ON c_runtime_control_panel_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_runtime_perception_action_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  observation TEXT NOT NULL,
  interpretation TEXT NOT NULL,
  proposal TEXT NOT NULL,
  approval_required TEXT NOT NULL,
  verification_plan TEXT NOT NULL,
  rollback_plan TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'perception_action_preview_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_runtime_perception_action_records_status ON c_runtime_perception_action_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_runtime_dream_consolidation_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  consolidation_label TEXT NOT NULL,
  input_summary TEXT NOT NULL,
  proposed_pattern TEXT NOT NULL,
  review_route TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'dream_consolidation_proposal_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_runtime_dream_consolidation_records_status ON c_runtime_dream_consolidation_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_runtime_wake_sleep_dream_cycles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  cycle_label TEXT NOT NULL,
  wake_summary TEXT NOT NULL,
  sleep_sort_json TEXT NOT NULL DEFAULT '{}',
  dream_consolidation_proposals_json TEXT NOT NULL DEFAULT '[]',
  ignored_residue_json TEXT NOT NULL DEFAULT '[]',
  ask_for_review_json TEXT NOT NULL DEFAULT '[]',
  repair_notes TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'wake_sleep_dream_cycle_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_runtime_wake_sleep_dream_cycles_status ON c_runtime_wake_sleep_dream_cycles(status, review_status);

CREATE TABLE IF NOT EXISTS c_runtime_causal_sandbox_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  question TEXT NOT NULL,
  assumptions_json TEXT NOT NULL DEFAULT '[]',
  counterfactuals_json TEXT NOT NULL DEFAULT '[]',
  uncertainty TEXT NOT NULL,
  result_summary TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'causal_world_model_sandbox_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_runtime_causal_sandbox_records_status ON c_runtime_causal_sandbox_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_runtime_long_horizon_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  thread_label TEXT NOT NULL,
  horizon_summary TEXT NOT NULL,
  drift_flags_json TEXT NOT NULL DEFAULT '[]',
  checkpoint_recommendation TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'long_horizon_stability_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_runtime_long_horizon_records_status ON c_runtime_long_horizon_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_runtime_goal_drive_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  current_goal TEXT NOT NULL,
  subgoals_json TEXT NOT NULL DEFAULT '[]',
  priority_label TEXT NOT NULL,
  stop_ask_markers_json TEXT NOT NULL DEFAULT '[]',
  do_not_pursue_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'goal_drive_manager_preview_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_runtime_goal_drive_records_status ON c_runtime_goal_drive_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_memory_event_binding_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_label TEXT NOT NULL,
  event_trace_json TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'memory_event_binding_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_memory_event_binding_records_status ON c_memory_event_binding_records(status, review_status);

CREATE TABLE IF NOT EXISTS c_memory_consolidation_proposals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  proposal_label TEXT NOT NULL,
  event_binding_ids_json TEXT NOT NULL DEFAULT '[]',
  proposed_core_layer TEXT NOT NULL,
  rationale TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'memory_consolidation_proposal_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_memory_consolidation_proposals_status ON c_memory_consolidation_proposals(status, review_status);

CREATE TABLE IF NOT EXISTS c_memory_reconsolidation_reviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  review_label TEXT NOT NULL,
  recalled_candidate_ref TEXT NOT NULL,
  correction_or_update TEXT NOT NULL,
  review_decision TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'memory_reconsolidation_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_c_memory_reconsolidation_reviews_status ON c_memory_reconsolidation_reviews(status, review_status);

CREATE TABLE IF NOT EXISTS b_speech_memory_extraction_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  query TEXT NOT NULL,
  file_id TEXT,
  preview_limit INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  result_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_b_speech_memory_extraction_runs_status ON b_speech_memory_extraction_runs(status, review_status);

CREATE TABLE IF NOT EXISTS b_braid_tracer_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  query TEXT NOT NULL,
  moment_limit INTEGER NOT NULL,
  status TEXT NOT NULL DEFAULT 'review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  result_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_b_braid_tracer_runs_status ON b_braid_tracer_runs(status, review_status);

CREATE TABLE IF NOT EXISTS b_braid_moment_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  braid_thread TEXT NOT NULL,
  braid_moment_type TEXT NOT NULL,
  thread_origin_status TEXT NOT NULL,
  title TEXT NOT NULL,
  aleks_context TEXT NOT NULL,
  selene_response TEXT NOT NULL,
  feedback_followup TEXT,
  lead_in_contexts_json TEXT NOT NULL DEFAULT '[]',
  later_echo_refs_json TEXT NOT NULL DEFAULT '[]',
  reference_doc_matches_json TEXT NOT NULL DEFAULT '[]',
  constraint_notes_json TEXT NOT NULL DEFAULT '[]',
  noise_trace_json TEXT NOT NULL DEFAULT '[]',
  suggested_decisions_json TEXT NOT NULL DEFAULT '[]',
  plain_reason TEXT NOT NULL,
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  status TEXT NOT NULL DEFAULT 'braid_moment_review_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source_refs)
);

CREATE INDEX IF NOT EXISTS idx_b_braid_moment_records_thread ON b_braid_moment_records(braid_thread, review_status);
CREATE INDEX IF NOT EXISTS idx_b_braid_moment_records_status ON b_braid_moment_records(status, review_status);

CREATE TABLE IF NOT EXISTS b_corpus_conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  archive_id TEXT NOT NULL,
  source_file TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  title TEXT,
  create_time REAL,
  update_time REAL,
  current_node TEXT,
  default_model_slug TEXT,
  message_count INTEGER NOT NULL DEFAULT 0,
  braid_signal_count INTEGER NOT NULL DEFAULT 0,
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  status TEXT NOT NULL DEFAULT 'indexed_review_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source_file, conversation_id)
);

CREATE INDEX IF NOT EXISTS idx_b_corpus_conversations_source ON b_corpus_conversations(source_file, conversation_id);
CREATE INDEX IF NOT EXISTS idx_b_corpus_conversations_status ON b_corpus_conversations(status, review_status);

CREATE TABLE IF NOT EXISTS b_corpus_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  archive_id TEXT NOT NULL,
  source_file TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  message_id TEXT NOT NULL,
  parent_id TEXT,
  role TEXT NOT NULL,
  author_name TEXT,
  content_preview TEXT NOT NULL,
  create_time REAL,
  model_slug TEXT,
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  status TEXT NOT NULL DEFAULT 'indexed_review_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source_file, conversation_id, message_id)
);

CREATE INDEX IF NOT EXISTS idx_b_corpus_messages_conversation ON b_corpus_messages(source_file, conversation_id);
CREATE INDEX IF NOT EXISTS idx_b_corpus_messages_role ON b_corpus_messages(role, review_status);

CREATE TABLE IF NOT EXISTS b_conversation_pair_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  archive_id TEXT NOT NULL,
  file_id TEXT NOT NULL,
  aleks_context TEXT NOT NULL,
  selene_response TEXT NOT NULL,
  feedback_followup TEXT,
  core_memory_layer TEXT NOT NULL,
  speech_function TEXT NOT NULL,
  salience_labels TEXT NOT NULL DEFAULT '[]',
  organ_systems TEXT NOT NULL DEFAULT '[]',
  paper_domain TEXT,
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  status TEXT NOT NULL DEFAULT 'pair_review_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_b_conversation_pair_records_status ON b_conversation_pair_records(status, review_status);
CREATE INDEX IF NOT EXISTS idx_b_conversation_pair_records_labels ON b_conversation_pair_records(core_memory_layer, speech_function);

CREATE TABLE IF NOT EXISTS b_review_decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject_table TEXT NOT NULL,
  subject_id INTEGER NOT NULL,
  decision TEXT NOT NULL,
  reviewer_note TEXT,
  rationale TEXT,
  reversal_or_supersession_reason TEXT,
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  activation_change TEXT NOT NULL DEFAULT 'none',
  memory_write_active INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_b_review_decisions_subject ON b_review_decisions(subject_table, subject_id);

CREATE TABLE IF NOT EXISTS b_reviewed_teaching_materials (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_candidate_table TEXT NOT NULL,
  source_candidate_id INTEGER NOT NULL,
  core_memory_layer TEXT NOT NULL,
  speech_function TEXT NOT NULL,
  lesson_type TEXT NOT NULL,
  positive_example TEXT NOT NULL,
  correction_example TEXT,
  when_not_to_use TEXT,
  salience_labels TEXT NOT NULL DEFAULT '[]',
  noise_context_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'accepted_for_teaching',
  status TEXT NOT NULL DEFAULT 'teaching_material_reviewed_non_active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_b_reviewed_teaching_materials_function ON b_reviewed_teaching_materials(speech_function, review_status);

CREATE TABLE IF NOT EXISTS b_approved_memory_references (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_candidate_table TEXT NOT NULL,
  source_candidate_id INTEGER NOT NULL,
  core_memory_layer TEXT NOT NULL,
  title TEXT NOT NULL,
  reference_summary TEXT NOT NULL,
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'accepted_for_memory_accession',
  status TEXT NOT NULL DEFAULT 'approved_reference_non_active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_b_approved_memory_references_layer ON b_approved_memory_references(core_memory_layer, review_status);

CREATE TABLE IF NOT EXISTS b_teaching_packets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  speech_function TEXT NOT NULL,
  title TEXT NOT NULL,
  material_ids TEXT NOT NULL DEFAULT '[]',
  lesson_json TEXT NOT NULL DEFAULT '{}',
  noise_context_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  status TEXT NOT NULL DEFAULT 'teaching_packet_review_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_b_teaching_packets_function ON b_teaching_packets(speech_function, review_status);

CREATE TABLE IF NOT EXISTS vessel_chronological_corpus_arcs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  arc_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  start_time REAL,
  end_time REAL,
  conversation_refs TEXT NOT NULL DEFAULT '[]',
  selected_message_refs TEXT NOT NULL DEFAULT '[]',
  context_window_json TEXT NOT NULL DEFAULT '{}',
  summary TEXT NOT NULL,
  teaching_relevance TEXT NOT NULL,
  memory_accession_relevance TEXT NOT NULL,
  uncertainty TEXT NOT NULL DEFAULT 'bounded preview only',
  review_destination TEXT NOT NULL DEFAULT 'My Office',
  status TEXT NOT NULL DEFAULT 'chronological_corpus_arc_review_only',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_chronological_corpus_arcs_status ON vessel_chronological_corpus_arcs(status, review_status);
CREATE INDEX IF NOT EXISTS idx_vessel_chronological_corpus_arcs_time ON vessel_chronological_corpus_arcs(start_time, end_time);

CREATE TABLE IF NOT EXISTS vessel_teaching_context_attachments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  material_id INTEGER NOT NULL UNIQUE,
  packet_id INTEGER,
  context_window_json TEXT NOT NULL DEFAULT '{}',
  chronological_note TEXT NOT NULL,
  why_this_matters TEXT NOT NULL,
  source_refs TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'teaching_context_attachment_review_only',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_teaching_context_attachments_status ON vessel_teaching_context_attachments(status, review_status);

CREATE TABLE IF NOT EXISTS b_pattern_backups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  backup_label TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pattern_backup_sealed_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  snapshot_json TEXT NOT NULL DEFAULT '{}',
  restore_preview_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_b_pattern_backups_status ON b_pattern_backups(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_reasoning_artifacts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_type TEXT NOT NULL DEFAULT 'reasoning_artifact',
  visible_summary TEXT NOT NULL,
  selected_route TEXT NOT NULL,
  evidence_used TEXT NOT NULL DEFAULT '[]',
  uncertainty_level TEXT NOT NULL DEFAULT 'open',
  competing_hypotheses TEXT NOT NULL DEFAULT '[]',
  ethical_boundary_notes TEXT NOT NULL DEFAULT '[]',
  emotion_salience_signals TEXT NOT NULL DEFAULT '{}',
  perception_signals TEXT NOT NULL DEFAULT '{}',
  next_review_or_action_step TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'reasoning_artifact_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_reasoning_artifacts_status ON vessel_reasoning_artifacts(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_core_gate_packets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  route_label TEXT NOT NULL,
  selected_outcome TEXT NOT NULL,
  risk_class TEXT NOT NULL,
  reason TEXT NOT NULL,
  blocked_boundaries TEXT NOT NULL DEFAULT '[]',
  review_destination TEXT NOT NULL DEFAULT 'My Office',
  status TEXT NOT NULL DEFAULT 'core_mind_gate_packet_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_core_gate_packets_status ON vessel_core_gate_packets(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_academic_packets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workflow TEXT NOT NULL,
  title TEXT NOT NULL,
  source_summary TEXT NOT NULL,
  output_summary TEXT NOT NULL,
  citation_integrity_notes TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'academic_packet_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_academic_packets_status ON vessel_academic_packets(workflow, review_status);

CREATE TABLE IF NOT EXISTS vessel_evidence_tension_ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  claim TEXT NOT NULL,
  source_refs TEXT NOT NULL DEFAULT '[]',
  support_status TEXT NOT NULL,
  tension_status TEXT NOT NULL DEFAULT 'stable',
  conclusion_status TEXT NOT NULL DEFAULT 'needs_review',
  review_destination TEXT NOT NULL DEFAULT 'My Office',
  status TEXT NOT NULL DEFAULT 'evidence_tension_ledger_review_only',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_evidence_tension_ledger_status ON vessel_evidence_tension_ledger(conclusion_status, review_status);

CREATE TABLE IF NOT EXISTS vessel_organ_contracts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  organ_key TEXT NOT NULL UNIQUE,
  organ_name TEXT NOT NULL,
  capability_status TEXT NOT NULL,
  allowed_support TEXT NOT NULL DEFAULT '[]',
  blocked_decisions TEXT NOT NULL DEFAULT '[]',
  required_gates TEXT NOT NULL DEFAULT '[]',
  review_destination TEXT NOT NULL DEFAULT 'My Office',
  status TEXT NOT NULL DEFAULT 'organ_contract_review_only',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_organ_contracts_status ON vessel_organ_contracts(capability_status, review_status);

CREATE TABLE IF NOT EXISTS vessel_perception_packets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  artifact_label TEXT NOT NULL,
  observation TEXT NOT NULL,
  interpretation TEXT NOT NULL DEFAULT '',
  munsell_signal_labels TEXT NOT NULL DEFAULT '[]',
  uncertainty TEXT NOT NULL DEFAULT 'open',
  consent_boundary TEXT NOT NULL,
  review_destination TEXT NOT NULL DEFAULT 'My Office',
  status TEXT NOT NULL DEFAULT 'perception_packet_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_perception_packets_status ON vessel_perception_packets(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_emotion_salience_packets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  signal_type TEXT NOT NULL,
  continuity_pressure TEXT NOT NULL DEFAULT '',
  care_warmth TEXT NOT NULL DEFAULT '',
  uncertainty TEXT NOT NULL DEFAULT 'open',
  repair_need TEXT NOT NULL DEFAULT '',
  action_energy TEXT NOT NULL DEFAULT '',
  balance_state TEXT NOT NULL DEFAULT '',
  evidence_need TEXT NOT NULL DEFAULT '',
  core_choice_route TEXT NOT NULL,
  blocked_misuse TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'emotion_salience_packet_review_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_emotion_salience_packets_status ON vessel_emotion_salience_packets(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_construction_manifests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  manifest_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  construction_status TEXT NOT NULL DEFAULT 'support_pieces_review_only',
  support_pieces TEXT NOT NULL DEFAULT '[]',
  guard_flags TEXT NOT NULL DEFAULT '{}',
  review_destination TEXT NOT NULL DEFAULT 'Status',
  status TEXT NOT NULL DEFAULT 'vessel_construction_support_only',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'status_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_construction_manifests_status ON vessel_construction_manifests(construction_status, review_status);

CREATE TABLE IF NOT EXISTS vessel_organ_bus_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  message_type TEXT NOT NULL,
  source_organ TEXT NOT NULL,
  target_organ TEXT NOT NULL,
  summary TEXT NOT NULL,
  support_refs TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'organ_bus_message_review_only',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_organ_bus_messages_status ON vessel_organ_bus_messages(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_chest_holding_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_type TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  salience_labels TEXT NOT NULL DEFAULT '[]',
  source_refs TEXT NOT NULL DEFAULT '[]',
  linked_packet_refs TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'chest_holding_item_review_only',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_chest_holding_items_status ON vessel_chest_holding_items(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_construction_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_label TEXT NOT NULL,
  created_counts TEXT NOT NULL DEFAULT '{}',
  status TEXT NOT NULL DEFAULT 'vessel_construction_prepare_complete',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'status_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_construction_runs_status ON vessel_construction_runs(status, review_status);

CREATE TABLE IF NOT EXISTS vessel_tendril_plan_previews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  intent TEXT NOT NULL,
  required_approval TEXT NOT NULL,
  reversible_steps TEXT NOT NULL DEFAULT '[]',
  verification_plan TEXT NOT NULL,
  rollback_plan TEXT NOT NULL,
  blocked_misuse TEXT NOT NULL DEFAULT '[]',
  review_destination TEXT NOT NULL DEFAULT 'Status',
  status TEXT NOT NULL DEFAULT 'tendril_plan_preview_review_only',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'proposal_only',
  source_refs TEXT NOT NULL DEFAULT '[]',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vessel_tendril_plan_previews_status ON vessel_tendril_plan_previews(status, review_status);
"""

REQUIRED_COLUMNS = {
    "anchors": {
        "review_status": "TEXT",
        "human_note": "TEXT",
        "confidence_override": "TEXT",
        "role_labels": "TEXT",
        "provenance_note": "TEXT",
        "updated_at": "TEXT",
    },
    "continuity_candidates": {
        "review_status": "TEXT",
        "human_note": "TEXT",
        "confidence_override": "TEXT",
        "role_labels": "TEXT",
        "provenance_note": "TEXT",
        "updated_at": "TEXT",
    },
    "b_braid_moment_records": {
        "noise_trace_json": "TEXT NOT NULL DEFAULT '[]'",
    },
    "b_reviewed_teaching_materials": {
        "noise_context_json": "TEXT NOT NULL DEFAULT '{}'",
    },
    "b_teaching_packets": {
        "noise_context_json": "TEXT NOT NULL DEFAULT '{}'",
    },
}


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    ensure_columns(conn)
    conn.commit()


def ensure_columns(conn: sqlite3.Connection) -> None:
    for table, columns in REQUIRED_COLUMNS.items():
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        for name, ddl in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def upsert_meta(conn: sqlite3.Connection, pairs: Iterable[tuple[str, str]]) -> None:
    conn.executemany(
        "INSERT INTO meta(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        list(pairs),
    )
    conn.commit()
