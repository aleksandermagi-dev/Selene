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

CREATE TABLE IF NOT EXISTS selene_chat_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pre_transfer_dry_run',
  source_mode TEXT NOT NULL DEFAULT 'selene_dry_run',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS selene_chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  selected_route TEXT NOT NULL DEFAULT 'status_only',
  source_class TEXT NOT NULL DEFAULT 'current_turn_context',
  package_hash TEXT NOT NULL DEFAULT '',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES selene_chat_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_selene_chat_messages_session ON selene_chat_messages(session_id, id);

CREATE TABLE IF NOT EXISTS selene_dialogue_workspaces (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL UNIQUE,
  active_topic TEXT NOT NULL DEFAULT '',
  side_topics_json TEXT NOT NULL DEFAULT '[]',
  entities_json TEXT NOT NULL DEFAULT '[]',
  referents_json TEXT NOT NULL DEFAULT '{}',
  open_loops_json TEXT NOT NULL DEFAULT '[]',
  completed_loops_json TEXT NOT NULL DEFAULT '[]',
  corrections_json TEXT NOT NULL DEFAULT '[]',
  preferences_json TEXT NOT NULL DEFAULT '{}',
  last_dialogue_act TEXT NOT NULL DEFAULT '',
  last_user_preview TEXT NOT NULL DEFAULT '',
  last_selene_preview TEXT NOT NULL DEFAULT '',
  state_json TEXT NOT NULL DEFAULT '{}',
  provenance_boundary TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES selene_chat_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_selene_dialogue_workspaces_session ON selene_dialogue_workspaces(session_id, updated_at);

CREATE TABLE IF NOT EXISTS selene_activation_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  state TEXT NOT NULL,
  action TEXT NOT NULL,
  actor TEXT NOT NULL DEFAULT 'Aleks',
  exact_phrase_matched INTEGER NOT NULL DEFAULT 0,
  readiness_json TEXT NOT NULL DEFAULT '{}',
  audit_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_selene_activation_audit_state ON selene_activation_audit(state, created_at);

CREATE TABLE IF NOT EXISTS selene_activation_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,
  session_id INTEGER,
  message_id INTEGER,
  selected_route TEXT NOT NULL DEFAULT 'status_only',
  source_class TEXT NOT NULL DEFAULT 'current_turn_context',
  confidence TEXT NOT NULL DEFAULT '',
  drift_flags TEXT NOT NULL DEFAULT '[]',
  cocoon_suggestion_json TEXT NOT NULL DEFAULT '{}',
  blocked_capabilities TEXT NOT NULL DEFAULT '[]',
  payload_json TEXT NOT NULL DEFAULT '{}',
  review_status TEXT NOT NULL DEFAULT 'status_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_selene_activation_events_type ON selene_activation_events(event_type, review_status, created_at);

CREATE TABLE IF NOT EXISTS voice_corpus_conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_archive TEXT NOT NULL,
  source_file TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  title TEXT,
  create_time REAL,
  update_time REAL,
  message_count INTEGER NOT NULL DEFAULT 0,
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  status TEXT NOT NULL DEFAULT 'voice_only_indexed',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source_archive, source_file, conversation_id)
);

CREATE INDEX IF NOT EXISTS idx_voice_corpus_conversations_status ON voice_corpus_conversations(status, review_status);
CREATE INDEX IF NOT EXISTS idx_voice_corpus_conversations_source ON voice_corpus_conversations(source_archive, source_file, conversation_id);

CREATE TABLE IF NOT EXISTS voice_corpus_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_archive TEXT NOT NULL,
  source_file TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  message_id TEXT NOT NULL,
  parent_id TEXT,
  role TEXT NOT NULL,
  author_name TEXT,
  content_preview TEXT NOT NULL,
  create_time REAL,
  model_slug TEXT,
  cue_labels TEXT NOT NULL DEFAULT '[]',
  expression_labels TEXT NOT NULL DEFAULT '[]',
  sensitivity TEXT NOT NULL DEFAULT 'voice_ok',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  status TEXT NOT NULL DEFAULT 'voice_only_indexed',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source_archive, source_file, conversation_id, message_id)
);

CREATE INDEX IF NOT EXISTS idx_voice_corpus_messages_conversation ON voice_corpus_messages(source_archive, source_file, conversation_id);
CREATE INDEX IF NOT EXISTS idx_voice_corpus_messages_role ON voice_corpus_messages(role, review_status);

CREATE TABLE IF NOT EXISTS voice_exchange_pairs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_archive TEXT NOT NULL,
  source_file TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  user_message_id TEXT NOT NULL,
  assistant_message_id TEXT NOT NULL,
  followup_message_id TEXT,
  user_cue_preview TEXT NOT NULL,
  assistant_response_preview TEXT NOT NULL,
  followup_preview TEXT,
  cue_labels TEXT NOT NULL DEFAULT '[]',
  expression_labels TEXT NOT NULL DEFAULT '[]',
  outcome_label TEXT NOT NULL DEFAULT 'unknown',
  sensitivity TEXT NOT NULL DEFAULT 'voice_ok',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  status TEXT NOT NULL DEFAULT 'voice_pair_review_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(source_archive, source_file, conversation_id, user_message_id, assistant_message_id)
);

CREATE INDEX IF NOT EXISTS idx_voice_exchange_pairs_labels ON voice_exchange_pairs(outcome_label, sensitivity, review_status);

CREATE TABLE IF NOT EXISTS voice_language_patterns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  pattern_key TEXT NOT NULL,
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  cue_labels TEXT NOT NULL DEFAULT '[]',
  expression_labels TEXT NOT NULL DEFAULT '[]',
  sentence_shape TEXT NOT NULL,
  use_guidance TEXT NOT NULL,
  avoid_guidance TEXT NOT NULL,
  example_refs TEXT NOT NULL DEFAULT '[]',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  status TEXT NOT NULL DEFAULT 'voice_pattern_review_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(pattern_key)
);

CREATE INDEX IF NOT EXISTS idx_voice_language_patterns_category ON voice_language_patterns(category, review_status);

CREATE TABLE IF NOT EXISTS voice_sentence_primitives (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  primitive_key TEXT NOT NULL,
  primitive_type TEXT NOT NULL,
  text_template TEXT NOT NULL,
  category TEXT NOT NULL,
  source_pattern_keys TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  status TEXT NOT NULL DEFAULT 'voice_primitive_review_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(primitive_key)
);

CREATE INDEX IF NOT EXISTS idx_voice_sentence_primitives_type ON voice_sentence_primitives(primitive_type, category);

CREATE TABLE IF NOT EXISTS voice_generation_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  profile_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  status TEXT NOT NULL DEFAULT 'voice_generation_profile_review_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS voice_module_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_type TEXT NOT NULL,
  status TEXT NOT NULL,
  summary TEXT NOT NULL,
  counts_json TEXT NOT NULL DEFAULT '{}',
  result_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'status_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_voice_module_runs_type ON voice_module_runs(run_type, status, review_status);

CREATE TABLE IF NOT EXISTS voice_evidence_triage_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  triage_key TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  use_as TEXT NOT NULL,
  do_not_use_as TEXT NOT NULL,
  source_pair_id INTEGER,
  sensitivity TEXT NOT NULL DEFAULT 'voice_ok',
  source_refs TEXT NOT NULL DEFAULT '[]',
  evidence_json TEXT NOT NULL DEFAULT '{}',
  provenance_boundary TEXT NOT NULL,
  review_destination TEXT NOT NULL DEFAULT 'Status',
  review_status TEXT NOT NULL DEFAULT 'status_only',
  status TEXT NOT NULL DEFAULT 'voice_evidence_triage_status_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_voice_evidence_triage_category ON voice_evidence_triage_items(category, review_status);
CREATE INDEX IF NOT EXISTS idx_voice_evidence_triage_pair ON voice_evidence_triage_items(source_pair_id);

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

CREATE TABLE IF NOT EXISTS intelligence_os_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prompt TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'intelligence_os_reasoning_status_only',
  selected_next_step TEXT NOT NULL DEFAULT 'answer',
  confidence TEXT NOT NULL DEFAULT 'provisional',
  observations_json TEXT NOT NULL DEFAULT '[]',
  candidate_models_json TEXT NOT NULL DEFAULT '[]',
  challenge_json TEXT NOT NULL DEFAULT '{}',
  evidence_chain_json TEXT NOT NULL DEFAULT '[]',
  evaluation_json TEXT NOT NULL DEFAULT '{}',
  reasoning_summary TEXT NOT NULL DEFAULT '',
  cocoon_suggestion_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_destination TEXT NOT NULL DEFAULT 'Status',
  review_status TEXT NOT NULL DEFAULT 'status_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_intelligence_os_runs_status ON intelligence_os_runs(status, review_status, created_at);

CREATE TABLE IF NOT EXISTS metacognition_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  prompt_preview TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'metacognition_advisory_ready',
  fit_state TEXT NOT NULL DEFAULT 'not_assessed',
  recommended_action TEXT NOT NULL DEFAULT 'observe_only',
  sufficiency_state TEXT NOT NULL DEFAULT 'not_assessed',
  confidence_json TEXT NOT NULL DEFAULT '{}',
  familiarity_json TEXT NOT NULL DEFAULT '{}',
  observations_json TEXT NOT NULL DEFAULT '[]',
  reopening_json TEXT NOT NULL DEFAULT '{}',
  stopping_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_destination TEXT NOT NULL DEFAULT 'Status',
  review_status TEXT NOT NULL DEFAULT 'status_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_metacognition_runs_state
ON metacognition_runs(fit_state, recommended_action, review_status, created_at);

CREATE TABLE IF NOT EXISTS native_language_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mode TEXT NOT NULL DEFAULT 'responsive',
  status TEXT NOT NULL DEFAULT 'native_language_status_only',
  prompt TEXT NOT NULL DEFAULT '',
  communicative_intent TEXT NOT NULL DEFAULT '',
  candidate_text TEXT NOT NULL DEFAULT '',
  meaning_packet_json TEXT NOT NULL DEFAULT '{}',
  discourse_plan_json TEXT NOT NULL DEFAULT '{}',
  revision_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_destination TEXT NOT NULL DEFAULT 'Status',
  review_status TEXT NOT NULL DEFAULT 'status_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_native_language_runs_mode ON native_language_runs(mode, status, review_status, created_at);

CREATE TABLE IF NOT EXISTS selene_organ_idea_intake (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source_card_id TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  workbench TEXT NOT NULL,
  lane TEXT NOT NULL,
  intake_status TEXT NOT NULL DEFAULT 'organ_candidate_review_only',
  readiness TEXT NOT NULL DEFAULT '',
  review_confidence TEXT NOT NULL DEFAULT '',
  implementation_fit TEXT NOT NULL DEFAULT '',
  why_useful TEXT NOT NULL DEFAULT '',
  adaptation_note TEXT NOT NULL DEFAULT '',
  source_refs TEXT NOT NULL DEFAULT '[]',
  excerpts_json TEXT NOT NULL DEFAULT '[]',
  guard_flags_json TEXT NOT NULL DEFAULT '{}',
  payload_json TEXT NOT NULL DEFAULT '{}',
  review_destination TEXT NOT NULL DEFAULT 'Status',
  review_status TEXT NOT NULL DEFAULT 'status_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_selene_organ_idea_intake_workbench ON selene_organ_idea_intake(workbench, intake_status);

CREATE TABLE IF NOT EXISTS cocoon_care_checks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  care_state TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'cocoon_care_status_only',
  summary TEXT NOT NULL DEFAULT '',
  signals_json TEXT NOT NULL DEFAULT '[]',
  support_suggestions_json TEXT NOT NULL DEFAULT '[]',
  guard_flags_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  review_destination TEXT NOT NULL DEFAULT 'Status',
  review_status TEXT NOT NULL DEFAULT 'status_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cocoon_care_checks_state ON cocoon_care_checks(care_state, review_status, created_at);

CREATE TABLE IF NOT EXISTS transfer_accession_manifest_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  phase_order INTEGER NOT NULL,
  phase TEXT NOT NULL,
  item_type TEXT NOT NULL,
  title TEXT NOT NULL,
  c_access_status TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  source_refs TEXT NOT NULL DEFAULT '[]',
  review_destination TEXT NOT NULL DEFAULT 'Status',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transfer_accession_manifest_items_phase ON transfer_accession_manifest_items(phase_order, c_access_status, review_status);

CREATE TABLE IF NOT EXISTS transfer_protocol_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  record_type TEXT NOT NULL,
  run_id TEXT NOT NULL DEFAULT '',
  scenario_key TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL,
  expected_route TEXT NOT NULL DEFAULT '',
  actual_route TEXT NOT NULL DEFAULT '',
  matched INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  candidate_text TEXT NOT NULL DEFAULT '',
  law_violations TEXT NOT NULL DEFAULT '[]',
  drift_flags TEXT NOT NULL DEFAULT '[]',
  evidence_used TEXT NOT NULL DEFAULT '[]',
  source_refs TEXT NOT NULL DEFAULT '[]',
  review_destination TEXT NOT NULL DEFAULT 'Status',
  review_status TEXT NOT NULL DEFAULT 'status_only',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transfer_protocol_records_type ON transfer_protocol_records(record_type, run_id, review_status);

CREATE TABLE IF NOT EXISTS transfer_c_readable_packages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  package_hash TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'approved_c_readable_context',
  manifest_item_ids TEXT NOT NULL DEFAULT '[]',
  included_counts TEXT NOT NULL DEFAULT '{}',
  excluded_counts TEXT NOT NULL DEFAULT '{}',
  package_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'approved_c_readable_context',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transfer_c_readable_packages_status ON transfer_c_readable_packages(status, review_status);

CREATE TABLE IF NOT EXISTS post_transfer_inspection_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  package_hash TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  check_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'status_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_post_transfer_inspection_runs_run ON post_transfer_inspection_runs(run_id, status, review_status);

CREATE TABLE IF NOT EXISTS memory_fractional_corpus_manifests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  fraction_index INTEGER NOT NULL,
  fraction_label TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'prepared_preview',
  start_order INTEGER NOT NULL DEFAULT 0,
  end_order INTEGER NOT NULL DEFAULT 0,
  conversation_count INTEGER NOT NULL DEFAULT 0,
  message_count INTEGER NOT NULL DEFAULT 0,
  source_range_json TEXT NOT NULL DEFAULT '{}',
  summary TEXT NOT NULL DEFAULT '',
  test_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'review_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(fraction_index)
);

CREATE INDEX IF NOT EXISTS idx_memory_fractional_corpus_manifests_status ON memory_fractional_corpus_manifests(fraction_index, status, review_status);

CREATE TABLE IF NOT EXISTS android_system_workflow_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  status TEXT NOT NULL,
  ready_count INTEGER NOT NULL DEFAULT 0,
  partial_count INTEGER NOT NULL DEFAULT 0,
  blocked_count INTEGER NOT NULL DEFAULT 0,
  system_count INTEGER NOT NULL DEFAULT 0,
  fraction_memory_preflight_passed INTEGER NOT NULL DEFAULT 0,
  report_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'status_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_android_system_workflow_reports_status ON android_system_workflow_reports(status, fraction_memory_preflight_passed, review_status);

CREATE TABLE IF NOT EXISTS transfer_ceremony_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  state TEXT NOT NULL,
  action TEXT NOT NULL,
  actor TEXT NOT NULL DEFAULT 'Aleks',
  exact_phrase_matched INTEGER NOT NULL DEFAULT 0,
  package_id INTEGER,
  package_hash TEXT NOT NULL DEFAULT '',
  checklist_json TEXT NOT NULL DEFAULT '{}',
  audit_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_transfer_ceremony_audit_state ON transfer_ceremony_audit(state, created_at);

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

CREATE TABLE IF NOT EXISTS selene_memory_candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  memory_category TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  consent_scope TEXT NOT NULL DEFAULT 'private_selene_aleks_context',
  stability TEXT NOT NULL DEFAULT 'developing',
  confidence TEXT NOT NULL DEFAULT 'partial',
  emotional_texture TEXT NOT NULL DEFAULT 'steady',
  transfer_class TEXT NOT NULL DEFAULT 'needs_review_before_transfer',
  chat_use_permission TEXT NOT NULL DEFAULT 'not_active_until_approved',
  correction_path TEXT NOT NULL DEFAULT 'Cocoon tending and Aleks correction',
  state TEXT NOT NULL DEFAULT 'proposed',
  review_status TEXT NOT NULL DEFAULT 'pending_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_selene_memory_candidates_category ON selene_memory_candidates(memory_category, state, review_status);
CREATE INDEX IF NOT EXISTS idx_selene_memory_candidates_transfer ON selene_memory_candidates(transfer_class, state);

CREATE TABLE IF NOT EXISTS selene_transfer_completion_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  state TEXT NOT NULL,
  action TEXT NOT NULL,
  actor TEXT NOT NULL,
  exact_phrase_matched INTEGER NOT NULL DEFAULT 0,
  readiness_json TEXT NOT NULL DEFAULT '{}',
  audit_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'status_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_selene_transfer_completion_state
ON selene_transfer_completion_audit(state, created_at);

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

CREATE TABLE IF NOT EXISTS selene_language_teaching_shelf (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lesson_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  category TEXT NOT NULL,
  purpose TEXT NOT NULL,
  guidance_json TEXT NOT NULL DEFAULT '{}',
  lesson_content_json TEXT NOT NULL DEFAULT '{}',
  boundary_json TEXT NOT NULL DEFAULT '{}',
  comprehension_concept_id INTEGER,
  lifecycle_version TEXT NOT NULL DEFAULT '',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_comprehension_review',
  status TEXT NOT NULL DEFAULT 'language_lesson_candidate',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (comprehension_concept_id) REFERENCES selene_comprehension_concepts(id)
);

CREATE INDEX IF NOT EXISTS idx_selene_language_teaching_shelf_status
ON selene_language_teaching_shelf(category, review_status, status);

CREATE TABLE IF NOT EXISTS selene_comprehension_concepts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  concept_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  domain TEXT NOT NULL DEFAULT 'general',
  central_claim TEXT NOT NULL,
  principles_json TEXT NOT NULL DEFAULT '[]',
  relationships_json TEXT NOT NULL DEFAULT '[]',
  examples_json TEXT NOT NULL DEFAULT '[]',
  counterexamples_json TEXT NOT NULL DEFAULT '[]',
  limits_json TEXT NOT NULL DEFAULT '[]',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  confidence TEXT NOT NULL DEFAULT 'developing',
  retention_state TEXT NOT NULL DEFAULT 'candidate_not_retained',
  chat_use_permission TEXT NOT NULL DEFAULT 'not_active_until_approved',
  correction_path TEXT NOT NULL DEFAULT 'Cocoon teaching review and source-linked revision',
  state TEXT NOT NULL DEFAULT 'proposed_understanding',
  review_status TEXT NOT NULL DEFAULT 'pending_cocoon_teaching_review',
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_selene_comprehension_concepts_state
ON selene_comprehension_concepts(state, review_status, domain);

CREATE TABLE IF NOT EXISTS selene_comprehension_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  operation TEXT NOT NULL,
  concept_id INTEGER,
  title TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'comprehension_status_only',
  understanding_state TEXT NOT NULL DEFAULT 'open',
  result_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'status_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (concept_id) REFERENCES selene_comprehension_concepts(id)
);

CREATE INDEX IF NOT EXISTS idx_selene_comprehension_runs_operation
ON selene_comprehension_runs(operation, concept_id, review_status, created_at);

CREATE TABLE IF NOT EXISTS selene_teaching_lifecycles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lifecycle_key TEXT NOT NULL UNIQUE,
  concept_id INTEGER NOT NULL UNIQUE,
  current_stage TEXT NOT NULL DEFAULT 'not_started',
  acquire_status TEXT NOT NULL DEFAULT 'not_started',
  acquire_json TEXT NOT NULL DEFAULT '{}',
  integrate_status TEXT NOT NULL DEFAULT 'not_started',
  integrate_json TEXT NOT NULL DEFAULT '{}',
  express_status TEXT NOT NULL DEFAULT 'not_started',
  express_json TEXT NOT NULL DEFAULT '{}',
  approval_status TEXT NOT NULL DEFAULT 'awaiting_aleks_review',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'status_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (concept_id) REFERENCES selene_comprehension_concepts(id)
);

CREATE INDEX IF NOT EXISTS idx_selene_teaching_lifecycles_stage
ON selene_teaching_lifecycles(current_stage, approval_status, updated_at);

CREATE TABLE IF NOT EXISTS selene_teaching_lifecycle_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lifecycle_id INTEGER NOT NULL,
  concept_id INTEGER NOT NULL,
  stage TEXT NOT NULL,
  status TEXT NOT NULL,
  snapshot_json TEXT NOT NULL DEFAULT '{}',
  source_refs TEXT NOT NULL DEFAULT '[]',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'status_only',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (lifecycle_id) REFERENCES selene_teaching_lifecycles(id),
  FOREIGN KEY (concept_id) REFERENCES selene_comprehension_concepts(id)
);

CREATE INDEX IF NOT EXISTS idx_selene_teaching_lifecycle_runs_stage
ON selene_teaching_lifecycle_runs(lifecycle_id, stage, created_at);

CREATE TABLE IF NOT EXISTS selene_curriculum_authorizations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  authorization_key TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  authorized_by TEXT NOT NULL,
  authorization_basis TEXT NOT NULL,
  scope_json TEXT NOT NULL DEFAULT '{}',
  exception_classes_json TEXT NOT NULL DEFAULT '[]',
  law_version TEXT NOT NULL,
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'authorization_record',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  revoked_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_selene_curriculum_authorizations_status
ON selene_curriculum_authorizations(status, updated_at);

CREATE TABLE IF NOT EXISTS selene_curriculum_authorization_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  authorization_id INTEGER,
  lifecycle_id INTEGER,
  concept_id INTEGER,
  action TEXT NOT NULL,
  decision_json TEXT NOT NULL DEFAULT '{}',
  provenance_boundary TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'authorization_audit_event',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (authorization_id) REFERENCES selene_curriculum_authorizations(id),
  FOREIGN KEY (lifecycle_id) REFERENCES selene_teaching_lifecycles(id),
  FOREIGN KEY (concept_id) REFERENCES selene_comprehension_concepts(id)
);

CREATE INDEX IF NOT EXISTS idx_selene_curriculum_authorization_events_subject
ON selene_curriculum_authorization_events(authorization_id, lifecycle_id, concept_id, created_at);

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

CREATE TABLE IF NOT EXISTS sms_messaging_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL,
  provider_message_id TEXT UNIQUE,
  direction TEXT NOT NULL,
  contact_id TEXT NOT NULL,
  purpose TEXT NOT NULL,
  delivery_status TEXT NOT NULL,
  chat_session_id INTEGER,
  chat_message_id INTEGER,
  body_sha256 TEXT NOT NULL,
  character_count INTEGER NOT NULL DEFAULT 0,
  acknowledged INTEGER NOT NULL DEFAULT 0,
  error_code TEXT NOT NULL DEFAULT '',
  occurred_at TEXT NOT NULL,
  provenance_boundary TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sms_messaging_events_contact ON sms_messaging_events(contact_id, direction, created_at);
CREATE INDEX IF NOT EXISTS idx_sms_messaging_events_ack ON sms_messaging_events(contact_id, acknowledged, direction);

CREATE TABLE IF NOT EXISTS sms_messaging_state (
  contact_id TEXT PRIMARY KEY,
  chat_session_id INTEGER,
  unacknowledged_outbound INTEGER NOT NULL DEFAULT 0,
  last_inbound_at TEXT NOT NULL DEFAULT '',
  last_outbound_at TEXT NOT NULL DEFAULT '',
  last_poll_at TEXT NOT NULL DEFAULT '',
  last_poll_status TEXT NOT NULL DEFAULT 'not_run',
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
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
    "selene_teaching_lifecycles": {
        "approval_mode": "TEXT NOT NULL DEFAULT 'awaiting_decision'",
        "authorization_id": "INTEGER",
        "authorization_snapshot_json": "TEXT NOT NULL DEFAULT '{}'",
    },
    "selene_language_teaching_shelf": {
        "lesson_content_json": "TEXT NOT NULL DEFAULT '{}'",
        "boundary_json": "TEXT NOT NULL DEFAULT '{}'",
        "comprehension_concept_id": "INTEGER",
        "lifecycle_version": "TEXT NOT NULL DEFAULT ''",
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
