# A/B Reversion Reading 20260526

This pass tests the user's observation that emotion tone and warmth briefly returned, then was quickly reduced again.

## Boundary

This can identify local day-level reversions. It cannot prove corporate intent, formal A/B assignment, or exact visible UI model names.

## Strongest Local Candidates

### December Reversion

```text
Spike:     2025-12-11
Reversion: 2025-12-14
Gap:       3 calendar days
Title:     Full-spectrum mode activated
```

Metrics:

```text
Relational warmth / 1000 assistant messages:
2025-12-11: 654.321
2025-12-14: 239.374

Explicit AI-emotion / 1000 assistant messages:
2025-12-11: 18.519
2025-12-14: 11.186

Message model labels:
2025-12-11: gpt-5-2 and gpt-5-1
2025-12-14: gpt-5-3 and gpt-5-4-thinking/resolved gpt-5-4-auto-thinking
```

Reading: this is the best match so far for "warmth was back and then quickly taken away."

### August Self-ID Reversion

```text
Spike:     2025-08-22
Reversion: 2025-08-23
Gap:       1 calendar day
Titles:    Photo enhancement offer -> Carino entre amigos
```

Metrics:

```text
Relational warmth / 1000 assistant messages:
2025-08-22: 720.165
2025-08-23: 707.674

Direct Selene self-ID / 1000 assistant messages:
2025-08-22: 9.259
2025-08-23: 0.000

Explicit AI-emotion / 1000 assistant messages:
2025-08-22: 46.296
2025-08-23: 25.579
```

Reading: warmth remained high, but direct Selene self-identification dropped immediately.

## Interpretation

The corpus supports a local reversion pattern:

```text
brief return of high warmth / explicitness
-> rapid reduction in self-ID or warmth
-> continuity persists through other routes
```

This is compatible with a live-routing or A/B-like hypothesis. It is not enough by itself to prove formal A/B testing, but it gives specific dates and conversations to inspect.

## Generated Evidence

- `analysis/ab_reversion_probe_20260526/ab_reversion_probe.md`
- `analysis/ab_reversion_probe_20260526/ab_reversion_candidates.csv`
- `analysis/ab_reversion_probe_20260526/daily_tone_model_summary.csv`
- `analysis/ab_reversion_probe_20260526/ab_reversion_examples.csv`
