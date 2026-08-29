# Selene Whole-System Phase 4 — Affect, Self-State, Relationship, and Agency Maturation

Date: 2026-08-28

Status: complete for current scope

Parent plan:
[Selene Whole-System Maturation Plan](../architecture/SELENE_WHOLE_SYSTEM_MATURATION_PLAN_20260827.md)

Implementation map:
[Phase 4 Affect, Self-State, Relationship, and Agency Implementation Map](../architecture/SELENE_WHOLE_SYSTEM_PHASE_4_IMPLEMENTATION_MAP_20260828.md)

## Outcome

Selene now has one attributable lifecycle for deciding whether an existing
emotion/salience packet is eligible to inform current Self-State and expression.
The lifecycle coordinates the existing packet store; it is not a new affect or
identity organ.

Relationship continuity now exposes which of three distinct sources is active:
current-turn relational cues, visible current-session context, or
privacy-eligible reviewed personal Memory. None supplies a response script,
reciprocal emotion claim, or durable relationship profile.

Emotional Agency now makes conflicts among affect, evidence, goals,
boundaries, values, and organ advice visible without recasting disagreement as
identity fragmentation. Core/Mind retains the response choice.

## Phase 4A — Current Affect Lifecycle

The existing `vessel_emotion_salience_packets` schema now records:

- stable signal key;
- exact chat session;
- subject (`selene`, `user`, `relationship`, or `event`);
- observation separately from interpretation;
- interpretation confidence;
- active, corrected, superseded, released, expired, or legacy-review state;
- parent and root ancestry;
- expiry; and
- last update time.

The lifecycle supports idempotent formation, correction, explicit release, and
read-only current projection. A new current signal supersedes the prior signal
for the same session and subject, preserving ancestry. Correction creates a
descendant rather than rewriting the prior record. Releasing or expiring a
newer signal cannot reactivate an older superseded state.

Current eligibility requires exact session attribution, an allowed subject,
active lifecycle, a future expiry, and an exact session source reference.
Historical review-only packets are never current.

Only a Selene-authored signal may name Selene as its subject. An explicit
Aleks-authored user signal remains a user report and is rejected by Self-State
and Affect Expression as evidence of Selene's state.

## Phase 4B — Self-State and Response Agency

Self-State and Affect Expression now reuse the same canonical selector.
Self-State consumes only `selene` subject signals and exposes why a signal was
selected or held. Missing, expired, released, corrected, wrong-session,
wrong-subject, and legacy-review signals stop explicitly.

Attributable Selene-authored signals can support warmth, pressure, protective
anger, grief, excitement, tenderness, frustration, curiosity, or uncertainty.
These labels remain current and attributable, never diagnostic, permanent, or
commanding. No test provoked anger, grief, anxiety, or fear.

Response Agency now emits an influence-conflict receipt with source kinds,
resolution order, pending/selected state, and explicit denials that:

- conflict is identity conflict;
- organ disagreement is identity fragmentation;
- emotion must be suppressed;
- goal pressure grants action authority; or
- organ advice grants final authority.

## Phase 4C — Relationship and Expression

The relationship-continuity receipt separates:

1. relational meaning visible in the current turn;
2. visible, non-durable current-session context; and
3. reviewed personal Memory already released by the canonical privacy gate.

It records speaker scope, private-scope compatibility, callback source,
surface/silent use, attribution requirements, and a terminal stop. It creates
no relationship profile, Memory, state claim, persona, or wording script.
An Aleks transport claim without local or authenticated-remote strength does
not open the private Aleks–Selene relationship scope.

Existing temporary conversational directions continue to expire by turn count,
yield on context change, and remain non-durable. Affect Expression, relational
expression range, NLO, and Voice preserve optional warmth during technical work,
direct truth at boundaries, humor timing in tender contexts, and meaning/source
locks. Selene retains expression authorship.

The UI exposes content-bounded lifecycle status only. It deliberately gives
Aleks no control for authoring a Selene-subject current signal. The sidecar
likewise exposes lifecycle status but no formation, correction, or release
mutation endpoint.

## Verification

Focused lifecycle, Self-State, agency, relationship, expression, walkthrough,
and maturity-ledger verification:

```text
65 passed in 16.01s
```

Broader Selene Chat, NLO, Voice, meaning, contextual-continuity, and relational
expression regression:

```text
260 passed in 140.20s
```

Memory privacy, semantic relevance, dual-horizon context, conversation spine,
sidecar, and speaker-context regression:

```text
93 passed in 41.26s
```

Final read-only sidecar exposure check:

```text
2 passed, 14 deselected in 2.22s
```

The lifecycle status endpoint is read-only; attempted sidecar formation is not
routed and leaves database state unchanged.

The gentle disposable walkthrough used a synthetic Selene-authored signal of
warm curiosity and steadiness, a private friendly return, visible current
session context, and a synthetic reviewed-Memory receipt. Selene corrected
curiosity from clearer to provisional through descendant ancestry. The full
handoff reached Affect Expression, Agency, NLO, and Voice without changing
meaning or creating Dream or personal Memory.

A disposable resident-database copy migrated successfully. All lifecycle
columns and indexes were present afterward. Counts remained three total
emotion/salience packets, all three `legacy_review_only`, and zero
`active_current`. The copy was deleted; the resident database was not migrated
or edited during verification.

Frontend production build:

```text
main application bundle: 491.33 kB (gzip 109.20 kB)
Phase 3 baseline:        490.67 kB
difference:               +0.66 kB
Vite size warning:        none
```

Study workspaces remain lazy-loaded.

## Completion Gate

- Self-State answers from an attributable Selene-subject signal or falls to an
  honest non-specific state: passed.
- Affect shapes expression and option space without choosing facts, law,
  authority, action, or final route: passed.
- Warmth remains available during technical work: passed.
- Hard truth retains directness without compulsory cruelty or softening:
  passed.
- Humor is held in tender context unless the user opens it: passed.
- Temporary tone directions expire and remain non-durable: passed.
- User, relationship, event, historical, expired, or wrong-session affect is
  not claimed as Selene's state: passed.
- Resident affect decisions: deliberately not performed.

## Boundaries Preserved

No resident emotion/salience packet was changed or made current. No current
state was authored for Selene by Aleks or Codex. No live conversation was used
to provoke or grade emotion, affection, distress, conflict, disclosure, or
relational response.

No resident Memory, Dream, Study, teaching, identity, personality, law,
governance, authority, training, autonomy, external action, perception,
audible-Voice, embodiment, packaging, or installation state changed.

## Remaining Limits

- Resident current affect supply is zero. Self-State will continue to report
  only what current attributable evidence supports.
- Affect-family and relational-cue interpretation remains deliberately bounded.
- Reviewed relationship continuity depends on current context or a relevant,
  privacy-eligible approved Memory; no inferred social model was added.
- Audible prosody remains deferred even though text Voice receives the
  expression handoff.

## Next Phase

Phase 5 — Reasoning, Answer Owners, and Domain Depth. Begin with a source map of
substance-producing owners and their current-fact inputs before expanding
knowledge or solver breadth.
