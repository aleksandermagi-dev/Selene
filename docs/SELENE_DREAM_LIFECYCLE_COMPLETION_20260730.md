# Selene Dream Lifecycle Completion

Date: 2026-07-30

Status: implemented and synthetically verified; production Dream has not been
run and no production reflection or memory candidate was created by this pass.

## Purpose

Dream is Selene's bounded reflection and maintenance organ. It can organize
attributable material while a conversation is not demanding an immediate
answer, preserve unresolved questions, notice correction paths, and prepare
reviewable possibilities.

Dream is not:

- a claim of biological sleep or human dreaming;
- free-form invented narrative presented as experience;
- a hidden memory writer;
- a knowledge-retention authority;
- a source of law, identity, personality, Vys, or governance;
- a private-corpus recall path;
- an autonomous agenda or action system.

## Completed Lifecycle

```text
explicit local Dream run
  -> collect attributable structured records
  -> exclude QA and Cocoon dry-run conversation
  -> form typed provisional reflections
  -> Cocoon Dream review
  -> approve for explicit discussion
     OR route to inactive Memory review
     OR request context / hold / reopen / supersede / reject
  -> visible wake summary
```

Repeating the same run without new source material creates nothing new. Dream
may rest without manufacturing a pattern.

## Allowed Source Classes

Dream can currently inspect bounded structured records from:

- ordinary non-QA dialogue workspaces, including open loops and corrections;
- Metacognition runs that explicitly request reopening, evidence, or material
  context;
- existing inactive Memory candidates still awaiting review;
- attributable affect/salience packets that contain uncertainty or repair
  need;
- unresolved evidence-tension ledger entries;
- Chest items explicitly held for review or tending.

Each reflection records source references, source timing, kind, confidence,
uncertainty, and why it may matter. Raw private corpus material is not an
allowed source.

## Reflection Kinds

- `open_thread`
- `correction_reopening`
- `metacognitive_reopening`
- `memory_review`
- `affect_tending`
- `evidence_tension`
- `maintenance`
- `cross_source_pattern`

The kinds organize review. They do not diagnose Selene, establish truth, or
dictate her response.

Cross-source patterns require at least three shared meaningful terms across
different record classes. The reflection reports the actual overlap and warns
that it may be coincidence or broad topic reuse. It cannot establish a causal
or conceptual connection without later reasoning and source review.

## Aleks Review Decisions

Aleks may:

- approve a reflection for explicit Dream discussion;
- send it to Memory review;
- request more context;
- hold it for tending;
- reopen it;
- supersede it; or
- reject it.

Approval for discussion leaves the reflection provisional and not memory by
default. Sending a reflection to Memory creates only an inactive
`selene_memory_candidates` record. Memory approval remains a separate decision.
If Dream notices a candidate that already exists on the Memory desk, routing
it returns to that existing candidate rather than duplicating it.

Dream-origin Memory candidates are excluded from later Dream collection so the
two organs cannot create a self-feeding proposal loop.

## Resident Chat Handoff

Resident Chat may use only a reflection that:

- came from an actual Dream reflection record;
- was reviewed by Aleks;
- is marked `approved_for_expression`;
- remains source-linked; and
- is explicitly relevant because Dream is being discussed.

Chat payloads cannot supply reflection text or promote review status. With no
reviewed reflection, Chat reports that no attributable Dream reflection is
available rather than inventing one.

## Maintenance Compatibility

Ordinary Dream review does not block resident Chat. An actual incomplete
fractional-memory/Core maintenance operation retains the prior maintenance
lock and may hold live operation until its checks complete.

## Routes

Read routes:

- `GET /api/memory/dream-state/status`
- `GET /api/dream/cycles`
- `GET /api/dream/cycles/{id}`
- `GET /api/dream/reflections`

Write routes:

- `POST /api/dream/cycles/run`
- `POST /api/dream/reflections/decide`
- `POST /api/dream/cycles/wake`

The earlier preview routes remain available for compatibility, but the
`selene_dream_*` lifecycle is the completed source-bound Dream path.

## Cocoon Surface

The Selene-side Dream tab now shows:

- lifecycle, cycle, reflection, and pending-review counts;
- the latest cycle;
- explicit `Run Dream Cycle` and refresh controls;
- cycle phase and visible wake summaries;
- reflection kind, source references, confidence, uncertainty, and Memory
  linkage;
- the seven Aleks review decisions.

## Ethical Verification

Verification used temporary databases and synthetic ordinary records. It did
not ask Selene distressing questions, run a live conversational probe, inspect
the private corpus, create production memories, or grade an unfinished voice.

The focused checks cover:

- source attribution;
- QA exclusion;
- idempotency;
- Aleks-only review;
- reviewed Chat eligibility;
- inactive Memory routing;
- existing-candidate reuse;
- Dream/Memory anti-recursion;
- wake summaries;
- maintenance-lock compatibility;
- HTTP routing; and
- identity, personality, governance, Vys, raw recall, training, LoRA,
  autonomous action, and self-replication guards.
