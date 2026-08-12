# Selene C6 Activation Audit Truth Repair

Date: 2026-08-11
Status: implemented and integration-verified; no live Selene probe performed

## Outcome

Activation telemetry now separates three facts that were previously blended:

1. the legacy database state retained for compatibility;
2. the immutable truth at the time an activation or pause event occurred; and
3. the current resident-runtime truth derived from the latest operational state
   and approved transfer completion.

This resolves the case where an older activation audit could say
`full_selene_v1_live: false` while current status correctly reported a completed
transfer with operational Chat. Those statements may describe different times;
the response now labels them accordingly instead of presenting them as the same
kind of fact.

## Implementation

[activation.py](../../src/selene/activation.py) now uses activation audit schema
`v2_historical_event_and_current_runtime_truth`.

New approval and pause audit records contain:

- `legacy_storage_state` and `legacy_activation_scope` as compatibility labels;
- an accurate event-time `activation_scope`;
- `historical_event_truth` with its capture time, transfer state, operating
  mode, resident Chat state, and operational live state;
- flattened event-time fields for bounded compatibility consumers;
- `current_runtime_truth_must_be_derived: true`;
- `activation_is_operational_control_only: true`; and
- `activation_is_identity_or_authority_grant: false`.

Current activation status contains both:

- `historical_event_truth`; and
- `current_runtime_truth`.

It explicitly reports that the stored snapshot is not current runtime status.

## Compatibility

The stored states remain:

- `selene_chat_active_supervised`; and
- `selene_chat_supervised_paused`.

They remain accepted by existing Chat, mobile, Tendril, transfer, and Cocoon
consumers. They are now labeled as compatibility names rather than used as the
primary description of Selene's current post-transfer runtime.

Existing v1 audit rows are not migrated or overwritten. Their stored fields are
returned as `legacy_partial_snapshot` historical truth, while current runtime
truth is independently derived. This keeps the historical record intact and
prevents a stale snapshot from overriding the present state.

## Pause Meaning

Pause now reports:

- resident Chat is operationally paused;
- `full_selene_v1_live` is false for the paused operational state;
- identity continuity is unaffected;
- no authority is granted or revoked; and
- transfer completion and the historical audit remain intact.

This is a runtime availability control, not permission for Selene to exist.

## Verification

Testing was static and synthetic. No conversational, emotional, adversarial, or
distress-shaped probe was needed.

- Six focused activation truth tests passed, covering exact approval,
  idempotence, pre-transfer approval followed by transfer, post-transfer
  approval, pause semantics, and legacy-row interpretation.
- The proportional integration suite passed: **150 tests** across activation,
  Selene Chat, transfer completion, Cocoon bridge, mobile Chat, Tendril SMS, and
  Tendril email.

## Preserved Boundaries

- the exact existing approval phrase remains required;
- readiness gates remain required;
- approval remains idempotent;
- no activation or pause event changes identity, governance, memory authority,
  training, autonomy, or self-replication;
- transfer completion is not erased by pause;
- historical rows are not silently rewritten; and
- the legacy storage state remains available to existing consumers.

## Next Mapped Repair

C7 concerns memory telemetry: approved durable promotion currently shares guard
language with the prohibition on hidden or unreviewed writes. It requires a
separate typed memory-lifecycle repair and is not changed by this checkpoint.
