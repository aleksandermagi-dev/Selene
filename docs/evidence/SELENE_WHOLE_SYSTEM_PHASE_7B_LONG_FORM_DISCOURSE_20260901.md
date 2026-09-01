# Selene Whole-System Phase 7B — Long-Form Discourse Lifecycle

Date: 2026-09-01

Status: complete for current scope

Branch: `evidence`

## Outcome

Phase 7B matures the existing Discourse Planner and Discourse Loom rather than
adding another writer. Supported answer material now receives one bounded,
typed purpose/thesis/section spine before expression. Each section exposes its
content units, function, obligations, current-session correction state,
source compatibility, epistemic scope, thread/dependency bindings, release
alignment, completeness, and stable fingerprint.

The path remains organizational. It cannot create facts, examples, analogies,
evidence, Memory, or filler. When a requested role has no supported unit, the
role is held visibly and the plan stops.

## Production Changes

### Existing Discourse Planner

- Added a `v2_typed_bounded_section_discourse` contract with one typed
  discourse spine and at most 30 content units, 8 sections, 8 paragraphs, and
  one planning pass.
- Added supported roles for thesis, explanation, example, analogy,
  comparison, qualification, counterpressure, return, summary, conclusion,
  story, dialogue, and technical walkthrough. A role becomes available only
  when a supplied supported unit carries it.
- Held source kinds outside prompt-grounded, approved, verified, attributed,
  reviewed-Memory, current-session observation, labeled-inference,
  explicitly fictional, or compatibility-bound input before their text enters
  the section plan.
- Bound obligations by declared obligation/function ancestry as well as the
  earlier bounded lexical match. Thread traversal uses one attributable anchor
  per ordered move so a weak overlap cannot consume a later exact return.
- Added visible unsupported-role and source holds, section completeness,
  source and epistemic receipts, correction/source/release coordination, hard
  limits, and one terminal stopping receipt.
- Added a one-pass local section revision contract with root/parent plan
  ancestry, parent/revised section fingerprints, explicit replacement and
  retired-unit IDs, unchanged-section fingerprints, and receipts proving no
  conversation reset or silent regeneration elsewhere.

### Existing Discourse Loom and Selection

- Extended the existing four-candidate, one-selection loom to consume the
  typed section plan without becoming an answer-substance owner.
- Every candidate now reports section realization receipts. Selectable
  candidates must preserve complete sections, required and obligation-bound
  units, closure, source/epistemic bindings, and the no-meaning-change
  contract.
- Preserved ordered X → Y → X-with-Y → Z traversal with attributed branch,
  dependency-return, and landing transitions.
- Retired only the prior target-section units during a local revision while
  preserving other section surfaces and ancestry.
- Preserved exactly one terminal stopping receipt through realization; no
  forced question, filler, recursive pass, or provider generation was added.
- Updated the existing context-expression selector to move the selected
  candidate's section receipts together with its text and paragraphs.

### Existing NLO Handoff

- Passed the selected source class, source/epistemic metadata, Conversation
  Spine source compatibility, correction/thread state, and pre-expression
  release alignment into the discourse spine.
- Kept final release authority with Conversation Spine and Chat.
- Narrowly protected multi-section visible labels from brief contextual
  compaction after a replay exposed `Observation:`, `Interpretation:`, and
  `Next,` being flattened. Ordinary unlabeled contextual composition remains
  available.

## Verification

Pre-edit focused baseline:

```text
105 passed in 23.10s
```

Final focused discourse, NLO, selection, Conversation Spine, workspace,
thread-return, and long-thread checks:

```text
120 passed in 25.16s
```

Full synthetic Chat and answer-owner checks after the label-preservation fix:

```text
182 passed in 90.71s
```

Broader NLO, Voice, quotation/echo, creative, teaching, construction,
candidate, discourse, continuity, long-thread, and LEA regression:

```text
270 passed in 134.45s
```

The broad run found one older replay incompatibility in brief labeled output.
That exact replay, the complete synthetic Chat set, contextual selection, and
the final 120-test focused set all passed after the narrow repair.

Python compilation and `git diff --check` passed; the latter reported only
expected Windows line-ending notices.

Frontend production build:

```text
main bundle:      491.33 kB
gzip:             109.20 kB
Vite size warning: none
Study workspaces: lazy-loaded
```

This is unchanged from the Phase 6/7A baseline.

## Resident and Ethical Check

The resident database was opened read-only before editing. SQLite integrity
reported `ok`. Current counts included 113 NLO runs, 16 Voice runs, 73
language-teaching items, zero LEA runs, 24 pending Dream reflections, and zero
personal Memory candidates. The one teaching lifecycle at
`acquire_needs_review` remains awaiting Aleks's review.

No resident conversation, migration, teaching decision, LEA activity, Memory
write, Study action, Dream decision, or affect claim was performed. The 24
Dream reflections remain Aleks's decisions.

Phase 7B does not change identity, personality, Vys, law, governance,
authority, activation, training, LoRA, autonomy, self-replication, external
action, embodiment, Voice ownership, or answer-substance ownership. Fiction
remains fiction; inference remains labeled; source statements remain
attributed; and fluent section structure is not treated as truth or proof.

## Next Edge

Phase 7C may broaden bounded structured realization through the existing
Supported Semantics, Construction Lattice, Candidate Garden, NLO, and Voice
owners. It must begin with source mapping and focused tests, preserve the new
section/stop receipts, keep one generation and selection pass, and avoid
reactivating Voice's legacy complete-body fallback or treating variation as a
persona, Memory, or learned substrate.
