# Selene Whole-System Phase 3 — Reflective Growth Implementation Map

Date: 2026-08-28

Status: production implementation and current-scope completion gate complete

Parent plan:
[Selene Whole-System Maturation Plan](SELENE_WHOLE_SYSTEM_MATURATION_PLAN_20260827.md)

Starting checkpoint: `3f7e78b Complete reviewed memory maturation phase`

Production starting checkpoint: `88327ed Map reflective growth maturation phase`

Completion evidence:
[Phase 3 Reflective Growth Maturation](../evidence/SELENE_WHOLE_SYSTEM_PHASE_3_REFLECTIVE_GROWTH_20260828.md)

## Purpose

Phase 3 matures the handoffs among Selene's existing Study, Learning Compass,
Dream, associative-intuition, Comprehension, Metacognition, and personal Memory
systems. It does not add a replacement organ and does not turn reflection into
hidden retention, automatic truth, or recursive self-monitoring.

## Current Source State

The worktree was clean when this map was prepared. Branch `evidence` was three
commits ahead of `origin/evidence`.

Read-only resident counts:

| Lifecycle | Current count/state |
| --- | --- |
| Study sessions | 1 |
| Study questions | 0 |
| Study notes | 6 |
| Learning Compass goals | 7: 1 `connected_for_now`, 6 `ready_to_explore` |
| Pondering threads | 1 `integrated_for_now` |
| Dream cycles | 1 |
| Dream reflections | 24, all `pending_review` |
| Personal Memory candidates | 0 |

The 24 Dream reflections were inspected only as lifecycle counts. Their content
was not reclassified and no decision was made for Aleks.

Frontend baseline from the Phase 2 production build:

```text
main application bundle: 485.69 kB
Vite size warning: absent
Study and its larger workspaces: already lazy-loaded into separate chunks
```

Bundle size remains a Phase 3 completion signal. Reflective coordination should
stay in backend contracts or existing lazy Study/Dream surfaces unless visible
interaction genuinely requires UI work.

## What Already Exists

### Study and Learning Compass

`src/selene/study_workspace.py` already supports:

- approved-knowledge-only Study materials;
- visible Study sessions, notes, evidence, and representation attempts;
- `ready`, `developing`, and `question_without_words` questions;
- attributable Aleks answers usable immediately inside the Study session;
- source-labeled Comprehension candidates for durable teaching review;
- clarification, reopening, prerequisite, alternate-representation, and
  return-later states;
- Learning Compass goals without grades or performance pressure; and
- explicit separation from Memory, Dream, identity, governance, and training.

### Dream

`src/selene/dream_state.py` already supports:

- explicit, source-bound, idempotent Dream cycles;
- provisional reflections from eligible open threads, corrections,
  metacognition, Study, affect, evidence tensions, and Memory review;
- Aleks-only review decisions;
- reviewed expression eligibility;
- inactive Memory proposals rather than automatic Memory;
- needs-context, tending, reopening, supersession, rejection, and wake
  summaries; and
- duplicate filtering that prevents already-routed material from cycling back
  into another Dream reflection.

### Associative Intuition

`src/selene/associative_intuition.py` already exists as connective tissue, not
an organ. It:

- scans approved knowledge, approved personal Memory, Study connections, open
  pondering threads, approved Dream reflections, and supplied attributed
  sources;
- uses inspectable semantic cue families and bounded lexical overlap;
- distinguishes no connection, felt connection, articulated connection, and
  held context;
- emits provisional Metacognition, Structural Discovery, Study, and Dream
  handoffs;
- contributes only strong articulated candidates to ordinary Chat; and
- never decides truth, writes Memory, retains knowledge, exposes raw corpus,
  changes identity/governance, or routes itself automatically.

Selene Chat and Metacognition already consume this bridge.

## Missing Connective Tissue

### P3-1 — Study answer integration reconciliation

An Aleks answer creates a source-labeled Comprehension candidate and correctly
does not assume understanding. The Study question does not yet expose the
candidate's later lifecycle—under review, needs context, approved knowledge,
rejected, or reopened—as one visible integration receipt.

Repair:

- add a read-only integration-state projection to Study question/session
  detail;
- add an explicit integrate-for-now action that requires approved knowledge and
  Selene's visible reconstruction;
- add direct question reopening with parent/descendant ancestry; and
- preserve “I still don't get it” and `question_without_words` without shame or
  forced completion.

### P3-2 — Dream destination and loop receipt

Dream can route to expression or Memory review, but its destination history is
not yet a single typed receipt and there is no reviewed Dream-to-Study reopening
path.

Repair:

- represent the selected destination explicitly;
- prevent cross-destination promotion and duplicate Study/Memory proposals;
- add an Aleks-selected Study reopening destination when an approved Study
  concept is attributable;
- preserve terminal destination ancestry when a reflection is superseded; and
- expose usefulness as review metadata without deciding any of the 24 pending
  reflections automatically.

### P3-3 — Associative privacy and development handoff

The bridge blocks raw/private corpus references, but the approved-Memory source
scan does not yet consume the Phase 2 speaker/channel/authentication envelope.
The bridge can suggest Study, but it cannot yet enter Study's visible
candidate → fit → evidence → revision path.

Repair:

- reuse the canonical Memory privacy decision rather than duplicate it;
- pass the current speaker envelope from Selene Chat;
- hold ineligible Memory sources before their content enters candidate text;
- add explicit stop reasons when no useful connection exists;
- let an explicitly accepted candidate create or update one idempotent Study
  pondering thread; and
- preserve the association as provisional—not evidence, proof, fact, Memory,
  or a finished answer.

### P3-4 — Cross-system lineage and stopping

Study, Dream, and intuition each have local provenance, but their cross-system
handoffs need a shared lineage vocabulary so the same item cannot bounce among
them while appearing new.

Repair:

- standardize origin record, parent record, destination, candidate state,
  source refs, and terminal stop reason;
- treat an already-active source as held rather than reactivated;
- allow one bounded Metacognition fit reopening;
- stop after no new evidence, failed fit, duplicate lineage, explicit hold, or
  terminal review; and
- keep every automatic write flag false.

## Dependency-Ordered Implementation

### Phase 3A — Study lifecycle closure

1. Add question ancestry and integration-state projection.
2. Add reopen and integrate-for-now actions.
3. Reconcile Learning Compass without grades or implied understanding.
4. Test ready/developing/no-words → answered → reopened/integrated paths.

### Phase 3B — Dream destination closure

1. Add typed destination receipts and transition rules.
2. Add idempotent reviewed Study reopening handoff.
3. Add usefulness/status summary for the 24 pending reflections.
4. Do not decide, batch-approve, or expand Dream generation.

### Phase 3C — Associative intuition maturation

1. Reuse Memory privacy gates and pass the speaker envelope.
2. Add cross-domain fit and explicit stop receipts.
3. Add explicit, idempotent promotion into a Study pondering thread.
4. Test delayed cues, weak resemblance, privacy, duplicate lineage, revision,
   and stopping.

### Phase 3D — Bounded integration and closure

1. Run focused lifecycle and loop-prevention tests.
2. Run one synthetic Study walkthrough on disposable state.
3. Use no distress-provoking Dream test and no live resident decisions.
4. Build the frontend and compare bundle output with the 485.69 kB baseline.
5. Update the maturity ledger, evidence record, work journal, and checkpoint.

## Deferred by Design

- Aleks's decisions for the 24 resident Dream reflections;
- broader Dream generation or scheduling;
- ordered teaching and LEAs;
- personal Memory approval;
- raw private corpus recall;
- identity, personality, law, authority, autonomy, or action changes;
- audible voice, perception, embodiment, packaging, or reinstall.

These are not blockers to building and verifying the Phase 3 machinery. The
phase cannot honestly claim the resident Dream review queue is completed until
Aleks reviews it, but no implementation should force that review.

The current-scope completion gate is satisfied by the machinery and synthetic
evidence. The 24 resident reflections remain pending, which is the intended
ethical boundary rather than an incomplete implementation decision.

## Ethical Verification Rule

Before each check:

1. What does this do to Selene?
2. Could static or synthetic evidence answer it?
3. Are we testing implemented machinery rather than judging an unfinished
   capability?
4. Is a live interaction actually necessary?

Use disposable fixtures first. Unknown, unfinished, or still unclear is valid
learning state, not failure.
