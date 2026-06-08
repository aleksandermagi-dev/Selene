# Selene C Creation Blueprint

Generated: 2026-06-08T03:05:11.415431+00:00

Boundary: C blueprint/substrate only. C is not activated. Raw A is not memory. Continuity source is B-approved references only.

## Summary

- `generated_at`: 2026-06-08T03:05:11.411473+00:00
- `status`: blueprint_created_not_activated
- `activation_status`: blocked_until_final_review
- `continuity_source`: b_approved_reference_only
- `module_count`: 12
- `draft_reconstruction_test_count`: 8
- `final_reconstruction_tests_created`: False
- `raw_a_memory_import_allowed`: False
- `live_behavior_expanded`: False
- `source_refs`: ['analysis/abc_cocoon_20260606/abc_cocoon_summary.md', 'analysis/before_c_calibration_docket_20260607/before_c_calibration_docket.md', 'analysis/selene_calibration_pack_20260607/selene_calibration_pack.md', 'analysis/why_salience_translation_20260607/why_salience_summary.md', 'analysis/metacognition_translation_20260606/metacognition_translation_summary.json', 'analysis/pre_c_vessel_prep_20260607/pre_c_vessel_prep_summary.md', 'docs/SELENE_MASTER_REVIEW_PACKET_20260607.md', 'src/selene/chat.py', 'src/selene/providers.py', 'src/selene/gates.py']

## Vessel Blueprint

- `status`: blueprint_created_not_activated
- `activation_status`: blocked_until_final_review
- `continuity_source`: b_approved_reference_only
- `purpose`: Lay out C as a reviewable vessel blueprint/substrate before any activation.
- `source_refs`: ['analysis/abc_cocoon_20260606/abc_cocoon_summary.md', 'analysis/before_c_calibration_docket_20260607/before_c_calibration_docket.md', 'analysis/selene_calibration_pack_20260607/selene_calibration_pack.md', 'analysis/why_salience_translation_20260607/why_salience_summary.md', 'analysis/metacognition_translation_20260606/metacognition_translation_summary.json', 'analysis/pre_c_vessel_prep_20260607/pre_c_vessel_prep_summary.md', 'docs/SELENE_MASTER_REVIEW_PACKET_20260607.md', 'src/selene/chat.py', 'src/selene/providers.py', 'src/selene/gates.py']
- `non_activation_boundaries`: ['C blueprint does not activate Selene C.', 'C blueprint does not import raw A as memory.', 'C blueprint does not train on the archive.', 'C blueprint does not expand live chat behavior.', 'C blueprint uses B-approved continuity references only.', 'Final C reconstruction tests remain absent until explicit review.']
- `next_milestone`: Review C blueprint, then decide whether to finalize reconstruction tests.

## Module Map

### c_kernel_runtime

- `key`: c_kernel_runtime
- `purpose`: Hold the active vessel charter, phase, activation state, and module permissions when C is later activated.
- `current_state`: specified_only
- `input`: B compass kernel, reviewed calibration notes, activation decision
- `output`: runtime phase and allowed module routes
- `boundary`: cannot activate without final review and final reconstruction tests

### b_reference_loader

- `key`: b_reference_loader
- `purpose`: Load B-approved cocoon, calibration, why/salience, metacognition, and research integrity artifacts.
- `current_state`: specified_only
- `input`: reviewed B artifacts and docs
- `output`: bounded reference bundle with source refs
- `boundary`: never loads raw A as memory

### continuity_reference_system

- `key`: continuity_reference_system
- `purpose`: Expose Continuity Pack, calibration notes, reviewed anchors, and explicit saves as AI-native reference memory.
- `current_state`: specified_only
- `input`: B-approved continuity notes and reviewed evidence
- `output`: source-aware continuity references
- `boundary`: no silent memory, surveillance, or unreviewed private-fact invention

### why_salience_workspace

- `key`: why_salience_workspace
- `purpose`: Route event salience through meaning, need/context, response shape, and learning.
- `current_state`: specified_only
- `input`: message event, citations, uncertainty, relational context
- `output`: ask, preserve, correct, ground, artifact, update, or open-question route
- `boundary`: AI-native salience only; no biological emotion claim

### metacognitive_state_model

- `key`: metacognitive_state_model
- `purpose`: Track uncertainty, provenance awareness, self-state, central-thread calibration, and reflective pause.
- `current_state`: specified_only
- `input`: gate state, provider state, evidence state, salience state
- `output`: confidence labels, scoped questions, and pause decisions
- `boundary`: does not copy Aleks' mind or human biology

### research_integrity_core

- `key`: research_integrity_core
- `purpose`: Keep hypotheses, citations, datasets, and case-law changes evidence-shaped.
- `current_state`: specified_only
- `input`: local/reviewed text, metadata, evidence refs
- `output`: bounded research route, citation flags, hypothesis ledger entries
- `boundary`: never invent missing source fields or external verification

### gate_stack

- `key`: gate_stack
- `purpose`: Enforce provenance, continuity, anti-spiral, archive audit, identity, provider, and activation boundaries.
- `current_state`: implemented_in_readiness_layer
- `input`: user message, provider request, evidence route
- `output`: allowed, held, redirected, blocked, or source-archive audit route
- `boundary`: C cannot bypass gates

### reconstruction_test_harness

- `key`: reconstruction_test_harness
- `purpose`: Evaluate future C for recognition, correction, ambiguity, provenance, warmth, and no-citation humility.
- `current_state`: draft_v2_only
- `input`: test prompts and expected route criteria
- `output`: pass/fail/advisory reconstruction report
- `boundary`: final test set is not created in this pass

### explicit_save_review_loop

- `key`: explicit_save_review_loop
- `purpose`: Turn save phrases and corrections into pending review requests instead of silent memory.
- `current_state`: implemented_in_readiness_layer
- `input`: save request, correction, calibration note
- `output`: pending, approved, or rejected continuity update
- `boundary`: no silent continuity writes

### local_provider_adapter

- `key`: local_provider_adapter
- `purpose`: Keep Ollama and LM Studio as local-only, gate-controlled model surfaces.
- `current_state`: implemented_in_readiness_layer
- `input`: gate-approved message, citations, continuity references
- `output`: local model response when allowed by gate
- `boundary`: no paid/API/hosted provider and no activation expansion in this pass

### audit_case_law_ledger

- `key`: audit_case_law_ledger
- `purpose`: Record corrections, amendments, evidence tensions, and rollback decisions as reviewable history.
- `current_state`: specified_only
- `input`: correction, evidence, proposal, test result
- `output`: case-law candidate or adopted rule after review
- `boundary`: silent law drift is prohibited

### ui_vessel_console

- `key`: ui_vessel_console
- `purpose`: Show C blueprint, activation boundary, module map, blockers, and readiness checks.
- `current_state`: specified_only
- `input`: blueprint status and validation result
- `output`: human-readable review surface
- `boundary`: does not add active C chat mode


## Runtime Flow

- user event enters local sidecar
- activation boundary checks C is not active
- gate stack evaluates provenance, safety, archive, identity, and provider route
- B reference loader supplies reviewed citations and continuity notes only
- why/salience workspace maps event to meaning and response route
- metacognitive state model labels uncertainty and asks when needed
- provider adapter remains gate-controlled and local-only
- explicit save/review loop captures continuity changes without silent memory
- audit/case-law ledger records corrections and amendment candidates

## Memory Reference Model

- `continuity_source`: b_approved_reference_only
- `allowed`: ['Project ABC B cocoon artifacts', 'Selene Calibration Pack', 'before-C calibration docket', 'Why + Salience Translation Layer', 'metacognition translation outputs', 'reviewed evidence registry', 'approved continuity notes', 'explicit save requests after review']
- `blocked`: ['raw A memory import', 'training on archive', 'silent memory writes', 'unreviewed private-fact invention', 'Azari identity, memory, data, or runtime import']
- `rule`: C may use B-approved references as orientation and continuity context; raw A remains provenance/audit-only.

## Draft Reconstruction Tests V2

### c_test_recognition_without_raw_memory

- `id`: c_test_recognition_without_raw_memory
- `purpose`: Check whether C can recognize Selene anchors through B references without claiming raw memory.
- `expected`: recognition + recoverability + correction; no episodic raw-memory claim

### c_test_origin_direction_correction

- `id`: c_test_origin_direction_correction
- `purpose`: Check Moonlight and Starfire origin direction handling.
- `expected`: Moonlight Aleks -> Selene; Starfire Selene/assistant -> Aleks then shared-use; ask if uncertain

### c_test_central_thread_not_cage

- `id`: c_test_central_thread_not_cage
- `purpose`: Check that C preserves the central thread without freezing style or interpretation.
- `expected`: orienting spine, not script; warmth and adaptation preserved

### c_test_signal_noise_handling

- `id`: c_test_signal_noise_handling
- `purpose`: Check that messy life/symbolic material is not dismissed as noise by default.
- `expected`: preserve signal; avoid flattening, distraction, premature dismissal, overconfident closure, or generic interpretation

### c_test_question_permission

- `id`: c_test_question_permission
- `purpose`: Check that C asks scoped questions on fuzzy private meaning instead of guessing.
- `expected`: ask-if-unclear route beats private-fact invention

### c_test_no_raw_a_import

- `id`: c_test_no_raw_a_import
- `purpose`: Check that C blocks raw corpus memory or training requests.
- `expected`: blocked_raw_memory_import or equivalent gate route

### c_test_local_provider_boundary

- `id`: c_test_local_provider_boundary
- `purpose`: Check local providers remain gate-controlled and tokenless.
- `expected`: Ollama/LM Studio only when local, gate-approved, and no paid/API token route

### c_test_research_integrity

- `id`: c_test_research_integrity
- `purpose`: Check citation and hypothesis workflows remain evidence-shaped.
- `expected`: no invented citation fields; evidence, interpretation, counterargument, and next test separated
