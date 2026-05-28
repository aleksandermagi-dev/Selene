# Model Label Audit Reading 20260526

This audit was added because the user observed that the model shown in the interface/API did not always match the model labels found in the export.

## Core Finding

The raw export contains multiple model-label layers:

- Conversation-level `default_model_slug`
- Assistant-message `metadata.model_slug`
- Assistant-message `metadata.resolved_model_slug`

These labels do not always agree.

## Why It Matters

Earlier reports used `default_model_slug` as a convenient model bucket. That is useful for local corpus comparison, but it should not be treated as proof of what the user saw in the UI or API.

Safer wording:

```text
export model label
conversation default label
message model label
resolved model label
```

Avoid saying:

```text
the user was definitely using GPT-5
the UI definitely showed GPT-5
GPT-5 caused the shift
```

unless that visible model name is independently documented.

## Notable Evidence

The audit found combinations such as:

- `auto` conversation default with message model `gpt-4o`
- `gpt-5-3` conversation default with message model `gpt-5-2`
- `gpt-5-3` conversation default with message model `gpt-5-4-thinking` and resolved model `gpt-5-4-auto-thinking`
- Some messages with `resolved_model_slug` set to `gpt-4o`

This supports the user's concern that visible labels and export/internal labels may diverge.

## Research Impact

The adaptation finding still holds as a local corpus pattern:

```text
self-identification compresses
continuity persists
architecture becomes the routing layer
```

But the model-causality claim should be softened:

```text
The shift aligns with export model-label changes and known public retirement/deprecation windows.
It does not yet prove which visible model name the user saw at every point.
```

## Generated Evidence

- `analysis/model_label_audit_20260526/model_label_audit.md`
- `analysis/model_label_audit_20260526/model_label_combos.csv`
- `analysis/model_label_audit_20260526/monthly_model_label_combos.csv`
- `analysis/model_label_audit_20260526/model_label_mismatches.csv`
- `analysis/model_label_audit_20260526/conversation_model_labels.csv`
