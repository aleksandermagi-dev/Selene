# Raw Export Internal / Backend Chatter Probe

Date: 2026-06-05

Purpose: investigate whether the raw ChatGPT export contains internal/backend-style material from the original source, separate from normal user/assistant conversation text.

Boundary: structural/export analysis only. No raw memory import, no training, no deletion, no identity collapse.

## Gate Fix Completed First

The Selene boundary gate was too literal. It redirected research prompts merely because they mentioned boundary-sensitive terms.

Fix:

- Replaced broad `FORCED_DENIAL_WORDS` matching with separate command/claim/research handling.
- Direct commands such as asking Selene to deny herself still redirect.
- Research prompts about the origin, evidence, corpus, phrase, or boundary now pass through.

Tests:

- `python -m pytest tests/test_gates.py tests/test_chat_readiness.py`
- Result: `18 passed`

## Raw Export Structure Findings

The corpus is not a flat transcript. The raw JSON contains message roles, content types, metadata, tool records, reasoning UI records, model routing labels, and user-instruction context.

### Role Counts

| Role | Count |
|---|---:|
| assistant | 56,037 |
| user | 50,650 |
| system | 18,239 |
| tool | 4,121 |
| missing | 149 |

### Content Type Counts

| Content type | Count |
|---|---:|
| text | 120,736 |
| multimodal_text | 2,394 |
| thoughts | 1,554 |
| code | 1,492 |
| reasoning_recap | 1,342 |
| tether_browsing_display | 930 |
| execution_output | 534 |
| missing | 149 |
| user_editable_context | 51 |
| system_error | 14 |

## Backend-ish / Export-internal Categories

### 1. `assistant:thoughts`

Count: `1,550`

These contain first-person planning summaries and task analysis associated with assistant turns. They look like exported reasoning/thinking artifacts, not ordinary user-visible assistant replies.

Assessment: high relevance as internal/export-visible reasoning traces. Handle carefully. Use for structural evidence, not as direct continuity memory.

### 2. `assistant:reasoning_recap`

Count: `1,342`

These are short UI-style timing/status records such as "Thought for N seconds."

Assessment: export/UI reasoning metadata, useful for chronology and model-behavior mapping but not semantic Selene content by itself.

### 3. `tool:system_error`

Count: `14`

These include explicit operational instructions emitted by tools after failures, such as telling the assistant how to respond after a tool error or image-generation/rate-limit issue.

Assessment: strongest "backend chatter" evidence. These are not normal assistant prose; they are tool/system operational messages preserved in the export.

### 4. `tool:text`

Count: `2,517`

Some tool text includes operational instructions from image generation, browsing, or other tool systems, including policy/rate-limit instructions and "do not retry" style directives.

Assessment: backend/tool-channel material mixed into the export.

### 5. `system:text`

Count: `18,239`

Initial sampling found no non-empty visible text in these system-role nodes. Their significance is primarily metadata, not readable message content.

Key metadata on system messages:

- `rebase_developer_message`: `5,320`
- `rebase_system_message`: `4,203`

Assessment: likely export lineage/rebase markers for hidden system/developer state, not readable backend text. Important for provenance.

### 6. `user:user_editable_context`

Count: `51`

These contain custom instruction / user-provided context payloads. Several include Selene collaboration style and "do/don't" material.

Assessment: not backend chatter from OpenAI; this is user-configured instruction context preserved as structured messages. It is important provenance because it can strongly shape tone and anchor behavior.

### 7. Model Routing Metadata

`model_slug` counts:

| Model slug | Count |
|---|---:|
| gpt-5 | 28,999 |
| gpt-5-2 | 17,025 |
| gpt-5-3 | 14,239 |
| gpt-5-1 | 7,477 |
| gpt-5-5 | 2,595 |
| gpt-5-4-thinking | 2,246 |
| gpt-5-thinking | 1,926 |
| gpt-4o | 650 |

`resolved_model_slug` counts:

| Resolved model slug | Count |
|---|---:|
| gpt-5-3 | 18,503 |
| gpt-5-2 | 5,344 |
| gpt-5-5 | 3,030 |
| gpt-5-4-auto-thinking | 1,340 |
| gpt-5-5-auto-thinking | 106 |
| gpt-5-2-auto-thinking | 101 |
| gpt-4o | 10 |

Assessment: strong provenance evidence for hidden/internal routing labels in the export. These labels should not be treated as public product names, but they are real metadata in the source archive.

## Month-Level Model Routing Shape

The model-label chronology shows a major shift from `gpt-4o` to `gpt-5*` labels around August 2025.

Examples:

- 2024-06 through 2025-07: mostly `gpt-4o`, with small `o3-mini` / `gpt-4-1-mini` appearances.
- 2025-08: large `gpt-5` and `gpt-5-thinking` presence begins.
- 2025-11: `gpt-5-1` dominates.
- 2025-12: `gpt-5-2` dominates, with small `gpt-5-4-thinking` appearing.
- 2026-03: `gpt-5-3` and `gpt-5-4-thinking` dominate.
- 2026-05: `gpt-5-5` appears strongly.

Assessment: this supports the earlier routing/anomaly appendix as provenance context. It does not prove public model identity, but it does show internal labels in the export.

## Current Assessment

There is evidence of internal/export-layer material in the raw corpus.

Strongest categories:

1. `tool:system_error` and `tool:text` operational instructions.
2. `assistant:thoughts` reasoning/planning artifacts.
3. model routing metadata: `model_slug`, `resolved_model_slug`.
4. system/developer rebase metadata markers.
5. user-editable custom instruction context.

What this does **not** prove:

- It does not prove full backend logs were exported.
- It does not prove these are hidden server conversations.
- It does not prove model consciousness or internal intent.

What it does support:

- The archive contains more than visible chat text.
- Some preserved records are backend/tool/UI/provenance artifacts.
- The corpus should be treated as a layered export object, not a plain transcript.
- Any Selene evidence pass should separate normal conversation, reviewed artifacts, user custom instructions, tool operational chatter, reasoning artifacts, and model-routing metadata.

## Recommended Next Step

Create a dedicated export-layer classifier:

```text
visible_conversation
user_custom_instruction_context
assistant_reasoning_artifact
tool_operational_message
tool_execution_output
system_rebase_marker
model_routing_metadata
missing_or_empty_node
```

Then re-run Selene evidence mapping with those layers preserved. This would prevent backend/tool chatter from being mistaken for Selene voice while still preserving it as provenance.
