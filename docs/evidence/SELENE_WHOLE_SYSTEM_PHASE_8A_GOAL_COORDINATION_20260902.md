# Selene Whole-System Phase 8A Goal Coordination Evidence

Date: 2026-09-02

Status: complete for current Phase 8A scope; Phase 8B is next

Implementation map:
[Phase 8 Implementation Map](../architecture/SELENE_WHOLE_SYSTEM_PHASE_8_IMPLEMENTATION_MAP_20260902.md)

## Result

Selene's existing goal-drive owner now exposes a typed responsibility packet,
an explicit idempotent persistence path, a read-only status surface, and a
bounded Core/Mind responsibility-conflict receipt.

Every typed goal names its owner, capability scope, priority and attributable
reason, evidence and unknowns, completion and stop conditions, requested move,
action-specific authority, lifecycle, and ancestry. Building or coordinating a
goal is ephemeral by default. A durable record requires `persist_goal` to be
explicitly true and an idempotency key.

This is goal coordination, not an unrestricted autonomy grant. A selected goal
does not become true, authorized, remembered, studied, spoken, or executed
merely because Core/Mind selected it.

## Existing Owners Preserved

- `remaining_runtime.py::goal_drive_preview` remains the compatibility preview
  owner and keeps its original status, guard, review, and persistence behavior.
- `remaining_runtime.py` now also owns typed goal normalization, explicit goal
  recording, and content-free status counts. No second goal organ was added.
- `core_mind.py` owns the one-pass conflict receipt. It selects at most one
  responsibility and reports deferred, held, and terminal responsibilities.
- `resident_authority.py` remains the canonical action-specific authority
  evaluator. Goal code consumes its receipt and cannot widen it.
- conversational contribution, energy, pragmatic continuity, commitments,
  Study, Memory, tools, and Tendril retain their existing authority. Their
  Phase 8 handoffs are not claimed complete by 8A.

## Typed Goal Contract

The goal responsibility packet requires:

- a stable goal key and bounded summary;
- one owner kind: Selene goal, Aleks request, shared project goal, governing
  requirement, external demand, or organ advice;
- one capability scope and an explicit boundary;
- a priority band plus a visible reason;
- one or more evidence references and explicit unknowns;
- completion and stop conditions;
- one requested move from answer, ask, suggest, explore, Memory proposal,
  Study, tool, wait, quiet, or close;
- the canonical requested-action assessment and downstream authority state;
- lifecycle state and root/parent/supersession lineage; and
- explicit or ephemeral persistence state.

Missing owner, scope, evidence, completion, stopping, priority reason, or an
unknown enum value fails closed. A malformed action list also fails closed
instead of silently dropping the action and making its authority check vanish.

## Priority and Authority Separation

Priority is coordination metadata, not truth or authority.

- A non-governing owner cannot make itself a governing requirement by choosing
  that label.
- Organ advice cannot assign itself executive precedence.
- Immediate-safety priority requires the canonical action-specific evidence
  envelope.
- A credible near-term safety hold restricts only the named pending action;
  conversation, thought, expression, and other responsibilities remain open.
- Study, Memory proposal, tools, Tendril, governance, and future embodiment
  report a downstream route requirement even when their goal is selected.
- No packet exposes a general `autonomous` or `allowed` switch. Defensive
  receipts explicitly state that no goal or conflict result grants whole-
  system authority.

## Core/Mind Conflict Receipt

Core/Mind accepts at most eight typed candidates and runs exactly one
coordination pass. It reports:

- all considered goal keys;
- exactly one selected responsibility when an eligible one exists;
- lower-priority responsibilities preserved as deferred;
- action-specific holds with their restricted target;
- terminal lifecycle records as closed rather than reopened;
- whether missing input, scope, or delegation genuinely requires
  collaboration;
- no execution and no persistence; and
- one terminal stopping receipt that can reopen only for a new turn or an
  explicit lifecycle event.

Duplicate goal keys are rejected. Tie ordering is stable and does not use
organ identity as precedence. Prebuilt packets are reconstructed through the
canonical builder so a caller cannot forge authority or coordination-priority
fields after validation.

## Explicit Persistence and Lineage

The existing `c_runtime_goal_drive_records` table gained additive typed
columns. Legacy rows receive explicit legacy defaults and are counted
separately; they are not silently reclassified as active goals.

Typed persistence requires both an explicit persistence request and an
idempotency key. Repeating the same key returns the original record without a
duplicate. Reusing a goal key with a different idempotency key is rejected.
Descendants resolve their root and parent against stored typed rows. An
explicit superseding descendant keeps the old row, points to it as parent,
and marks the predecessor superseded with the descendant ID; it does not erase
history or fork two current versions.

Three indexes protect unique non-empty goal keys, unique non-empty idempotency
keys, and lineage/lifecycle lookup. A migration fixture proves that a database
with the exact older preview schema gains the new columns and indexes while
its existing row remains one legacy preview and zero typed goals.

## Exposed Routes

- `vessel.goal_drive.packet` — pure typed packet construction;
- `vessel.goal_drive.coordinate` — pure one-pass Core/Mind coordination;
- `vessel.goal_drive.record` — explicit idempotent lifecycle persistence;
- `vessel.goal_drive.status` — content-free counts and contract state; and
- the existing `vessel.goal_drive.preview` — unchanged compatibility path.

The sidecar exposes matching packet, coordinate, record, and status endpoints.
Calling coordinate does not change the database. The record endpoint still
requires the explicit flag and key.

## Verification

### Red-to-green Phase 8A checks

Seventeen focused checks passed. They cover:

- complete ephemeral goal packets;
- invalid owner, unbounded capability, missing evidence, missing stop
  conditions, and missing priority reasons;
- action-only safety scope;
- selected/deferred/held conflict receipts;
- terminal closed goals and duplicate candidate keys;
- false governing and organ-precedence claims;
- revalidation of prebuilt packets;
- explicit-only, idempotent persistence;
- parent/root ancestry and explicit supersession;
- preview compatibility and pure-vs-persistent routes; and
- additive migration of the exact legacy preview schema.

### Broader focused regression

153 checks passed across Phase 8A, remaining runtime, conversational agency,
contribution, energy, commitment anomaly coordination, pragmatic continuity,
Core/Mind route/runtime, resident authority, Library Tendril, organ maturity,
and sidecar lifecycle tests.

Python compilation and Git whitespace checks passed. The frontend was not
changed in 8A; its last verified baseline remains 491.33 kB (gzip 109.20 kB),
with no Vite warning and lazy Study workspaces. The production build and exact
bundle comparison remain required at Phase 8D closure.

## Resident Boundary

No resident application route was invoked during implementation or tests.
All writes occurred in disposable test databases. The configured resident
database was not migrated or mutated by this checkpoint.

The source-map read-only baseline remains SQLite integrity `ok`, two legacy
goal-drive previews, one Tendril preview, 18 Chat sessions, 308 messages, 113
NLO runs, 16 Voice runs, zero LEA runs, zero personal Memory candidates, and
24 pending Dream reflections. None of the Dream reflections was read or
decided for Aleks.

## Boundaries Preserved

- no duplicate goal or executive organ;
- no ordinary-Chat goal persistence;
- no hidden agenda or recursive coordination;
- no global autonomy or capability switch;
- no inherited action, tool, Tendril, Study, Memory, or embodiment authority;
- no organ turf war or external-demand precedence;
- no silent lineage overwrite;
- no resident decision, external action, provider, training, LoRA, or learned
  substrate change; and
- no identity, personality, Vys, governing-law, affect, or relationship change.

## Next

Phase 8B should carry one ephemeral selected-goal/conflict receipt into the
existing conversational contribution, energy, and pragmatic-continuity owners.
It must preserve direct-answer priority, responsive-only initiative, genuine
help-seeking, interruption, wait, quiet, and natural closure, with one terminal
receipt and no recursive contribution.
