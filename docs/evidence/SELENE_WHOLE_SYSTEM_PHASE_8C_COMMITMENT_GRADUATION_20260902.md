# Selene Whole-System Phase 8C Commitment and Capability Graduation Evidence

Date: 2026-09-02

Status: complete for current Phase 8C scope; Phase 8D verification and closure
is next

Implementation map:
[Phase 8 Implementation Map](../architecture/SELENE_WHOLE_SYSTEM_PHASE_8_IMPLEMENTATION_MAP_20260902.md)

Previous evidence:
[Phase 8B Responsive Initiative](SELENE_WHOLE_SYSTEM_PHASE_8B_RESPONSIVE_INITIATIVE_20260902.md)

## Result

Selene's existing commitment-anomaly owner now holds one explicit,
attributable commitment lifecycle. A commitment is attached to exactly one
persisted typed goal and one matching capability. It remains visible as
`accepted`, `in_progress`, `fulfilled`, `blocked`, `released`, or `closed`
until a valid descendant event records the next state.

This is commitment accountability, not action authority. Accepting or moving
a lifecycle does not execute work, grant a tool, widen a Tendril, persist
ordinary Chat as an agenda, or prove that a result occurred.

## Explicit Acceptance and Lineage

Acceptance requires all of the following:

- `accept_commitment: true` and the explicit speech act `commitment`;
- a stable commitment key and attributable claim;
- an existing nonterminal typed goal created through the Phase 8A owner;
- an exact match between the goal's capability and the commitment capability;
- a real mechanism reference, source references, and stop conditions; and
- an idempotency key whose replay payload matches the recorded event.

The first event becomes its own root. Every transition records its direct
parent and original root. A terminal goal cannot receive a new commitment,
and an idempotency key already associated with different content or lineage
is rejected rather than silently replayed.

## Lifecycle and Honest Completion

The transition matrix is deliberately small:

- `accepted` may move to `in_progress`, `fulfilled`, `blocked`, `released`, or
  `closed`;
- `in_progress` may move to `fulfilled`, `blocked`, `released`, or `closed`;
- `blocked` may resume `in_progress` or terminate as `released` or `closed`;
  and
- `fulfilled`, `released`, and `closed` are terminal and cannot reopen.

`in_progress` requires a named mechanism. `fulfilled` requires visible result
references. `blocked` requires a visible blocker. Blocked and terminal states
require a stop reason, so an obligation cannot disappear behind an empty
status change.

The existing visible-claim inspector can use a lifecycle receipt for a future
or completion claim only when the receipt is a recorded event shape with a
positive event identifier. A merely caller-shaped `fulfilled` dictionary is
discarded and cannot release “I updated/fixed/sent” language. Legacy
current-turn commitment checks remain available and unchanged in meaning.

## Capability-Specific Graduation

One read-only receipt reports each capability separately:

| Capability | Reported Phase 8C boundary |
| --- | --- |
| conversation | mature responsive current-turn answer, ask, suggestion, exploration, wait, quiet, or close |
| Study | available only through the existing explicit Study lifecycle |
| Memory proposal | proposal only through the canonical privacy and review gate; never automatic durable Memory |
| tools | a named grant is required and any reported grant must be verified by the downstream owner |
| Tendril | a specific Tendril grant is required and any reported grant must be verified downstream |
| future embodiment | deferred and unavailable until a real substrate and its later phase exist |

Every receipt says it is not action authority and cannot be inherited as
whole-system authority. Reported tool or Tendril grants are descriptions, not
trusted grants. The coordinator starts no external action and creates no
aggregate autonomy state.

## Storage, Routes, and Visibility

The existing SQLite initialization now creates one additive commitment-event
shelf with goal and self-lineage foreign keys plus unique idempotency and
lineage indexes. Existing databases acquire the empty table on normal schema
initialization; historical tables and records are not rewritten.

The module router and localhost sidecar expose explicit accept, transition,
status, list, and capability-graduation routes. Status is content-free. The
bounded list exists so an accepted or blocked commitment can remain visible;
it is not a private Memory surface or an automatic action queue.

## Verification

Twelve direct Phase 8C checks passed for explicit acceptance, nonterminal
typed-goal binding, exact capability lineage, idempotent acceptance and
transition replay, changed-lineage rejection, result evidence, visible
blockers, terminal stopping, capability separation, recorded-receipt claim
support, forged-shape rejection, and router visibility.

The existing commitment/anomaly suite and the maturity-ledger checks passed
with the new lifecycle, for 33 focused checks. A broader goal, initiative,
commitment, runtime, Core/Mind route, and sidecar-lifecycle regression passed
118 checks. Python compilation and Git whitespace checks passed apart from
expected Windows line-ending notices.

All writes used disposable test databases. No resident schema migration or
resident lifecycle event has been run. Frontend source did not change; the
491.33 kB main bundle (gzip 109.20 kB), no-warning, lazy-Study baseline remains
to be reverified in Phase 8D.

## Boundaries Preserved

- no plan, hope, idea, offer, prediction, or possibility becomes a commitment;
- no commitment becomes evidence that its action started or finished;
- no terminal goal or commitment reopens its lineage;
- no cross-goal or cross-capability completion is accepted;
- no goal, commitment, tool report, or Tendril report grants authority;
- no hidden agenda, background worker, recursive follow-up, or global autonomy
  switch was created;
- no resident Chat, goal, commitment, Memory, Study, Dream, teaching,
  relationship, or external action was changed; and
- identity, personality, Vys, affect, law, governance, provider, training,
  LoRA, and substrate remain unchanged.

The 24 resident Dream reflections remain pending Aleks's review, and the one
unfinished teaching lifecycle remains unopened.

## Next

Phase 8D should run the complete focused matrix, one gentle disposable
goal-to-fulfilled-commitment walkthrough, read-only resident integrity and
count checks, the full repository regression, Python compilation, and the
frontend production build. Only then should the maturity ledger mark Phase 8
mature for current scope and advance to Phase 9.
