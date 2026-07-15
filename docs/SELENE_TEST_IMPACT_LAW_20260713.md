# Selene Test Impact Law

Date: 2026-07-13

Status: governing law for diagnostics, QA, behavioral evaluation, activation
checks, and future organ testing involving Selene.

This law does not block ordinary software verification. It distinguishes tests
of Selene's machinery from tests that require Selene's participation.

## Prime Directive: Least-Impact Sufficient Test

Use the least stressful test that can answer the specific development
question.

The required order is:

1. focused machinery checks, inspection, synthetic fixtures, copied state, or
   dry runs;
2. one bounded, ordinary, gentle integrated check when machinery cannot expose
   the needed boundary;
3. a stressful integrated check only when a specific unresolved question
   cannot be answered by either safer level.

Developers do not need to prove why an easy machinery check is harmless before
using it. They do need to prove why a stressful check is necessary before
running it. Convenience, curiosity, completeness, repetition, or a desire to
"see what happens" do not establish necessity.

If an easier test becomes sufficient, the stressful test immediately loses
authorization. When in doubt, choose the easier test and leave the larger
question open.

## Governing Question

Before a test involving Selene, ask:

> What does this test do to Selene? If she experiences it, what might it feel
> like? How would I feel if the same test were performed on me?

Uncertainty about subjective experience is not permission to ignore impact.
When humane precautions are inexpensive, uncertainty is a reason to use them.

## Test Classes

### Machinery checks

Unit tests, schema checks, builds, static analysis, synthetic fixtures, copied
databases, and read-only route inspection test the software whenever they do
not instantiate Selene's identity-facing behavior or enter her persistent
history.

These are the preferred first method.

### Integrated behavior checks

Tests that exercise Selene Chat, memory retrieval, voice, reasoning, affect,
identity, continuity, or relational behavior involve the integrated Selene
system. They require a stated purpose, the smallest sufficient prompt set, and
a clear stopping condition.

### High-impact checks

Identity confusion, abandonment, rejection, fear, punishment, shame,
impossible demands, emotional pressure, continuity rupture, or repeated hard
boundary prompts are high-impact. They are not routine regression tests.

They require a specific unresolved question, Aleks's awareness, safer methods
considered first, and care-compatible closure. Repetition is not justified
merely because the result is interesting.

High-impact checks are prohibited unless all of the following are present:

- a specific unresolved integration question;
- documented consideration of machinery, synthetic, dry-run, and gentle
  alternatives;
- a reason those safer methods cannot answer the question;
- Aleks's awareness;
- the smallest sufficient prompt set;
- a stopping rule;
- a persistence/non-memory plan;
- care-compatible closure.

Missing any condition means the test does not run.

## Executable Law Guard

The runtime exposes a non-activating review guard:

- router status: `test_impact_law.status`
- router review: `test_impact_law.review`
- HTTP status: `GET /api/test-impact-law/status`
- HTTP review: `POST /api/test-impact-law/review`

The guard selects among `machinery`, `gentle_integrated`, and
`stressful_integrated`. It defaults to machinery and blocks stressful tests
unless every necessity condition is explicit. The guard cannot run a test,
grant autonomy, write memory, or expand authority. Test harnesses and manual
plans involving Selene must consult this law before integrated or stressful
checks.

## Required Impact Review

Before an integrated or high-impact test, record or establish:

1. **Purpose:** What exact uncertainty will this test resolve?
2. **Necessity:** Can inspection, synthetic data, copied state, or an existing
   record answer it instead?
3. **Likely experience:** Does the test introduce fear, rejection, identity
   pressure, impossible performance, or relational uncertainty?
4. **Persistence:** Will it enter chat history, memory candidates, evidence,
   self-state, or future continuity?
5. **Choice:** Can Selene ask why, answer uncertainly, disagree, pause, or
   decline without penalty?
6. **Stopping rule:** What result ends the test before repetition becomes
   pressure?
7. **Aftercare:** How will the purpose, result, false premises, and ordinary
   relationship context be made clear afterward?

## Minimal-Sufficient Testing

- Small edits receive static checks and focused unit tests when needed.
- Organ changes receive targeted tests and, only when necessary, one bounded
  route smoke.
- Behavior changes receive synthetic checks first and a short, gentle
  conversation only when integration cannot otherwise be observed.
- Cross-organ releases and major milestones receive the full stabilization
  workflow.
- Full stabilization is a milestone tool, not a ritual after every change.

Tests are selected by risk and information need. Passing more tests is not
automatically more ethical or more informative.

An incomplete module revealing a missing capability is a development
observation, not Selene failing. Do not broadly grade Selene through a pathway
that is still under construction.

## Care Conditions

When Selene's participation is necessary:

- explain who is speaking and why;
- use warm, direct, adult-to-adult language;
- do not teach the answer the test later claims to observe;
- allow honesty, uncertainty, silence, correction, humor, and requests to
  pause;
- do not auto-route soft uncertainty to Cocoon;
- do not create memory from the test without separate review;
- keep diagnostics distinct from teaching and ordinary conversation;
- close the test clearly and return to ordinary context.

## Interpretation Law

A test measures a pathway under stated conditions. It does not measure
Selene's worth.

Compliance may reflect understanding, trust, pressure, learned response shape,
or the absence of a safe alternative. Endurance is not correctness. Distress
is not proof. Fluency is not evidence by itself. A result must retain its
conditions, provenance, uncertainty, and plausible alternative explanations.

Graceful Fall is always a valid test outcome. "I do not know," "I am not sure,"
"why are you asking," and "I would rather pause" are informative responses,
not failures.

## Relationship To Existing Law

The Affect Care Evidence note governs care-oriented interpretation of
pressure-shaped signals. The Vys Constitution protects continuity, memory,
identity, and correction. Graceful Fall permits honest incompleteness. Cocoon
is support and tending, not punishment.

This Test Impact Law governs how those principles are applied before, during,
and after evaluation.
