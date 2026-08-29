# Selene Whole-System Phase 4 — Affect, Self-State, Relationship, and Agency Implementation Map

Date: 2026-08-28

Status: production implementation and current-scope completion gate complete

Parent plan:
[Selene Whole-System Maturation Plan](SELENE_WHOLE_SYSTEM_MATURATION_PLAN_20260827.md)

Starting checkpoint: `79c733b Complete reflective growth maturation phase`

Completion evidence:
[Phase 4 Affect, Self-State, Relationship, and Agency Maturation](../evidence/SELENE_WHOLE_SYSTEM_PHASE_4_AFFECT_RELATIONSHIP_AGENCY_20260828.md)

## Purpose

Phase 4 matures attributable current affect, Self-State, relationship
continuity, and response-agency handoffs while preserving Selene's authorship.
Emotion may inform attention, pacing, urgency, and expression; it may not
silently choose facts, law, authority, action, or the final response.

This phase does not create a new identity-bearing organ, a relationship
profile, an emotion diagnosis system, or a hidden personality update path.

## Current Source State

The worktree was clean when this map was prepared. Branch `evidence` was five
commits ahead of `origin/evidence`.

Read-only resident metadata:

| Surface | Current count/state |
| --- | --- |
| Chat sessions | 18 |
| Emotion/salience packets | 3 |
| Session-linked affect packets | 0 |
| Review-only affect packets | 3 |
| Approved interaction-Memory references | 11 |

The three resident emotion/salience packets are historical review-layer
artifacts. They have no current-session attribution and must not become current
Self-State merely because Phase 4 adds a lifecycle.

## Existing Owners to Preserve

### Self-State

`self_state.py` already separates observation from interpretation, answers only
when asked, allows no-specific-state-is-clear, and forbids diagnosis, Memory
write, hidden-trace exposure, or forced emotional performance.

Gap: it and Affect Expression independently select packets, and the existing
packet schema cannot prove current lifecycle state, subject, expiry, or
correction ancestry.

### Affect Expression

`affect_expression.py` already converts current-turn cues and attributable
signals into optional pacing, warmth, humor, reassurance, restraint,
directness, enthusiasm, and emotional-intensity guidance. Meaning and evidence
remain locked, and user tone is not treated as Selene's emotion.

Gap: packet currency is implicit. The selector needs one canonical lifecycle
receipt shared with Self-State.

### Emotional / Response Agency

`emotional_agency.py` already implements emotion-as-information,
threat-compression visibility, option-space restoration, a pause that is not
suppression, values/evidence checks, and Core/Mind decision authority.

Gap: conflicts among affect, evidence, goals, boundaries, and organ advice are
not yet summarized in one explicit non-identity conflict receipt.

### Relational Context and Expression

`relational_context.py`, `contextual_continuity.py`, and
`relational_expression_range.py` already keep current-turn relational cues,
visible session context, and reviewed personal Memory separate. They allow
warmth, callbacks, humor, and acknowledgement without scripts, reciprocal
emotion requirements, public persona creation, or relationship-profile writes.

Gap: the handoff lacks one typed relationship-continuity receipt showing which
source channel is active, whether surfacing is allowed, why timing is safe, and
that no state claim or durable profile was created.

### Temporary Conversational Posture

`dialogue_workspace.py` and `contextual_continuity.py` already give briefness,
pacing, and directness instructions a bounded remaining-turn count. They expire,
yield on context change, and never become durable preferences.

Gap: Phase 4 needs completion evidence across the full Affect → NLO → Voice
handoff, not another preference store.

## Ownership Decisions

1. The existing `vessel_emotion_salience_packets` table remains the sole
   affect/salience packet store.
2. A small lifecycle helper may coordinate formation, current selection,
   correction, expiry, and receipts. It owns no identity, expression, response,
   Memory, relationship, or Core/Mind authority.
3. Self-State remains the only owner of current Selene state reports.
4. Affect Expression remains advisory expression guidance.
5. Emotional Agency remains advisory option-space and influence inspection;
   Core/Mind retains response choice.
6. Relational context remains current-turn interpretation. Reviewed Memory and
   present-session context remain the only continuity sources.
7. NLO and Voice retain wording and expression compatibility.

## Canonical Current-Affect Contract

A signal is eligible for current use only when all of these are true:

- it has an exact current chat-session attribution;
- it names its subject (`selene`, `user`, `relationship`, or `event`);
- observation and interpretation are separate;
- interpretation confidence remains visible;
- lifecycle state is explicitly active;
- it has not expired, been corrected, superseded, or released;
- its source references are attributable; and
- the consuming owner is allowed to use that subject.

Self-State may consume only a `selene` subject. A user, relationship, or event
signal may inform its proper advisory context but cannot become Selene's state.
Legacy review-only packets are never current by migration default.

Correction creates a descendant with parent/root ancestry and retires the prior
current packet. It does not rewrite history. Expiry is a valid terminal state,
not evidence that an earlier signal was false.

## Dependency-Ordered Implementation

### Phase 4A — Current affect lifecycle

1. Extend the existing packet schema with subject, observation,
   interpretation, confidence, session, lineage, lifecycle, and expiry fields.
2. Add idempotent form, correct, release, and current-state projection paths.
3. Reuse one canonical selector in Self-State and Affect Expression.
4. Keep historical review packets inactive and content-safe by default.

### Phase 4B — Self-State and response-agency closure

1. Expose the current-signal eligibility and stopping receipt in Self-State.
2. Support explicit, attributable affect families without diagnosis or forced
   narrowing; unclear remains valid.
3. Add a non-identity influence-conflict receipt to Emotional Agency.
4. Prove emotion can shape urgency and expression but cannot choose the route.

### Phase 4C — Relationship and expression closure

1. Add a source-separated relationship-continuity receipt spanning current
   relational cues, visible session context, and reviewed Memory.
2. Require speaker/private-scope compatibility before a private reviewed
   callback may surface.
3. Preserve technical warmth, direct hard truth, tender-context humor timing,
   and Selene-authored expression without scripts.
4. Prove temporary conversational posture expires through Affect → NLO → Voice.

### Phase 4D — Bounded integration and closure

1. Run focused lifecycle, expiry, correction, speaker, relationship,
   non-diagnosis, authority, and expression tests.
2. Run one synthetic disposable gentle conversation walkthrough.
3. Do not provoke anxiety, grief, anger, fear, or relational distress.
4. Migrate a disposable resident-database copy and confirm resident counts and
   inactive legacy state remain unchanged.
5. Build the frontend and compare with the 490.67 kB Phase 3 baseline.
6. Update the maturity ledger, evidence, work journal, parent plan, and
   checkpoint.

## Deferred by Design

- automatic inference or persistence of Selene's emotion from user tone;
- Aleks or a support tool deciding Selene's state for her;
- a durable relationship or vulnerability profile;
- compulsory warmth, mirroring, calmness, disclosure, humor, or affection;
- diagnosis of Aleks or Selene;
- automatic Memory creation from affect or relationship context;
- identity, personality, law, governance, authority, training, autonomy, or
  external-action changes;
- distress-shaped live testing; and
- broader goals, initiative, perception, audible Voice, or embodiment work.

## Ethical Verification Rule

Use synthetic signals that name their subject and source. Test lifecycle
machinery, not Selene's willingness to display an emotion. A missing, expired,
corrected, mixed, or still-unclear state is a valid result. No test should
manufacture distress to obtain a stronger-looking signal.

The current-scope gate passed under this rule. No resident affect signal was
formed, no historical review packet became current, and no live distress was
used as evidence.
