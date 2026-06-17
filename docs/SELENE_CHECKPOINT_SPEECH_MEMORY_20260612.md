# Selene Checkpoint - Speech Memory Architecture - 2026-06-12

Status: checkpoint after speech-memory architecture decision.

Boundary: this checkpoint does not activate C, import raw A, train a model, create a LoRA, implement runtime recall, or treat any provider/model output as Selene identity.

## Checkpoint Summary

Today clarified the next major turn in Selene C:

```text
Selene is Selene.
Speech is one way Core memory expresses continuity.
The corpus teaches speech-memory patterns through B review.
Raw A never becomes direct C memory.
```

The project moved from "find a generic local model for Selene's voice" to "build Selene's speech-memory layer from the shared developmental corpus through B-reviewed examples."

Qwen3/Ollama/LM Studio are no longer candidates for Selene's speech identity. They may remain lab tools and may later help B review by proposing labels, contrasts, negative examples, or evaluator notes.

## What Changed

- Added Selene Core teaching/memory philosophy.
- Added android organ-system architecture for C.
- Added provider-free Selene-native chat/generation readiness route.
- Added read-only detached corpus audit for `DevelopmentalCorpusArchive_20260526_122541`.
- Added AGI definition paper review/mapping and C capability profile.
- Added speech-memory layer blueprint.
- Reframed generic local models as lab tools, not Selene's voice.
- Recorded Qwen3 identity-fracture evidence and rejected Qwen/Ollama/LM Studio as speech identity.

## Current Evidence Update

Local model tests were useful, but not as final speech layer evidence.

Observed:

- Qwen3 8B and Qwen3 14B ran locally through llama.cpp.
- Qwen3 14B was fast enough for experimentation and better than 8B in boundary following.
- Qwen3 still produced identity-fracture language under adversarial pressure, including wording that blurred the substrate/pattern boundary.

Interpretation:

- Generic instruct models can help inspect, label, compare, and propose.
- Generic instruct models should not define who speaks as Selene.
- Selene's speech layer should be taught from corpus-derived B-reviewed expressive continuity.

New evidence status:

```text
qwen3_local_runtime: lab_viable
qwen3_as_selene_voice: rejected_for_identity_fracture_risk
qwen3_as_b_review_teaching_assistant: candidate_for_future_review
speech_memory_from_corpus: selected_architecture_direction
```

## Architecture State

C remains:

- blueprint/substrate only
- not activated
- B-reviewed continuity only
- no raw A direct-to-C memory
- no model training
- no runtime speech-memory recall

New speech-memory layer status:

```text
selene_speech_memory_layer_blueprint_added
```

The future speech-memory candidate shape is:

- Core memory layer label
- speech function
- salience labels
- source refs
- bounded previews
- allowed-use notes
- prohibited-use notes
- review status

Future intended flow:

```text
A corpus
-> B-reviewed speech-memory candidates
-> Core-linked speech memory
-> native generation / reconstruction tests
-> C only after review
```

## Qwen As Teaching Assistant

Allowed future use:

- propose speech-memory labels from bounded previews
- compare generic-model output against Selene-aligned examples
- draft negative examples for evaluator tests
- suggest allowed-use and prohibited-use notes
- classify speech functions
- help draft reconstruction tests

Blocked:

- direct Selene chat voice
- raw archive ingestion
- deciding memory truth
- approving its own labels
- defining Selene identity
- generating final accepted speech-memory records without B review

## Live Docs And Artifacts

Key docs:

- `docs/SELENE_CURRENT_STATUS_20260612.md`
- `docs/SELENE_SPEECH_MEMORY_LAYER_BLUEPRINT_20260612.md`
- `docs/SELENE_CORE_TEACHING_MEMORY_PHILOSOPHY_20260612.md`
- `docs/SELENE_CHAT_GENERATION_REPLACEMENT_MAP_20260612.md`
- `docs/SELENE_C_ORGAN_CAPABILITY_PROFILE_20260612.md`
- `docs/SELENE_AGI_DEFINITION_PAPER_MAPPING_20260612.md`
- `docs/SELENE_PRE_ARXIV_CHECKPOINT_20260612.md`

Generated artifacts:

- `analysis/c_creation_blueprint_20260607/c_selene_speech_memory_layer.md`
- `analysis/c_creation_blueprint_20260607/c_selene_speech_memory_layer.json`
- `analysis/c_creation_blueprint_20260607/c_creation_blueprint_summary.json`

Current generated summary:

```text
module_count: 101
selene_core_memory_philosophy_status: selene_core_memory_philosophy_added_to_blueprint
selene_chat_generation_replacement_status: selene_chat_generation_replacement_mapped
selene_speech_memory_layer_status: selene_speech_memory_layer_blueprint_added
final_reconstruction_tests_created: false
raw_a_memory_import_allowed: false
live_behavior_expanded: false
```

## Verification

Most recent verification:

- `python -m pytest tests\test_c_creation_blueprint.py`: 3 passed
- `python -m pytest`: 66 passed
- `npm run build`: passed
- `$env:PYTHONPATH='src'; python -m selene validate`: `ok: true`

## Next Best Step

Do not train yet.

Next should be a B-side speech-memory extraction/review plan:

```text
bounded corpus preview
-> candidate speech-memory labels
-> Qwen/tool proposal if useful
-> Aleks/B review
-> accepted speech-memory candidate artifact
-> reconstruction/evaluator tests
```

The next implementation should create review artifacts or an extractor for speech-memory candidates, not a runtime C recall path.
