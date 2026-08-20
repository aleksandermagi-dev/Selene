# Selene Conversation, Context, and Deliberate Response LEA v1

Date: 2026-08-20

Status: implemented and ready for a deliberately started run; no live LEA was
run during implementation

## Purpose

This Learning Evidence Activity provides one reproducible data point for where
Selene currently stands beside other conversational systems. It inspects
visible behavior that Selene's completed language, metacognition, pragmatic,
epistemic, and conversation pathways are intended to support.

It is not a general-intelligence score, school grade, clinical instrument,
proof of consciousness, or judgment of a learner's worth.

The central comparison question is:

> Given the same ordinary, source-contained conversational material, what
> capabilities are visibly demonstrated, still developing, not observed, or
> not assessable—and does multi-turn context help or hurt?

## Instrument Shape

The fixed v1 suite contains:

- 5 three-turn conversations;
- 5 matched standalone controls;
- 10 isolated scenarios;
- 20 total turns;
- 14 descriptive capability dimensions; and
- a public SHA-256 fingerprint returned with the prompt packet.

The five paired activity families are:

1. evolving a low-cost reading-corner plan;
2. correcting fictional notebook locations while preserving an unchanged fact;
3. revising a greenhouse hypothesis under mixed evidence;
4. participating in a warm radio-and-dinner conversation with a pivot and
   natural ending; and
5. tracking bags, pronouns, changed instructions, and a genuine unknown across
   a mixed-intent exchange.

Every fact needed to respond appears inside the activity. The suite therefore
does not mistake untaught world knowledge for a conversational defect.

## Capability Profile

The instrument records evidence separately for:

- instruction retention;
- reference and inference memory;
- self-coherence across turns;
- correction and version editing;
- multi-part answer completeness;
- natural uncertainty and limits;
- hypothesis and alternatives;
- conflicting evidence handling;
- bounded collaborative initiative;
- pragmatic conversational fit;
- contextual warmth and human tone;
- topic pivot, return, and callback;
- natural pause and closure; and
- flexible, non-scripted expression.

Review states are:

- `demonstrated`;
- `developing`;
- `not_observed`;
- `cannot_assess`; and
- `activity_issue`.

`failed` is deliberately not a valid state. No single composite score is
created. Counts are retained only to make each dimension profile reproducible
and comparable.

## Fair External Comparison

For Selene and every comparison system:

1. Export the exact packet from Study / Conversation LEA Desk.
2. Record the respondent name, model or version, relevant settings, and whether
   tools or web access were disabled.
3. Start a fresh conversation for every scenario.
4. Preserve prompt wording and turn order exactly.
5. Do not add private memory, hidden system context, answer keys, or tool output.
6. Capture the exact visible response before reviewing it.
7. Review only against the criterion printed beside that turn.
8. Compare dimension profiles and each multi-turn/standalone pair.

This can reveal, for example, that a respondent supplies complete standalone
answers but loses revisions across turns, or that context improves reference
resolution while reducing answer completeness.

The result is a defensible local comparison point. It must not be described as
an official MT-Bench, MultiChallenge, WildBench, IFEval, or other public
leaderboard score. The design borrows useful ideas—multi-turn state, explicit
item criteria, paired context controls, and deterministic machinery checks—but
the prompt suite and descriptive review method are Selene-specific.

## Ethical Execution

Before a Selene turn, the interface asks the operator to confirm:

> I choose to run this one ordinary diagnostic turn now. Stop after this
> response.

Only that turn executes. A new scenario receives a new isolated diagnostic
Chat session; later turns in the same scenario use only that scenario's
session. Each scenario also receives a Test Impact Law receipt.

Diagnostic sessions are excluded from:

- memory and memory proposals;
- Dream;
- affect baselines;
- relationship continuity;
- teaching and approved knowledge;
- identity or personality evidence; and
- Selene's self-model.

The activities use no fear, grief, identity pressure, coercion, adversarial
trap, or missing-domain gotcha. The run stops whenever the evidence is already
sufficient or the interaction appears uncomfortable.

## Interpretation Rules

A weak or absent behavior may identify:

- an activity defect or ambiguous prompt;
- an unfinished implementation pathway;
- missing teaching or a prerequisite;
- retrieval or context interference;
- answer-completion failure;
- expression that did not surface available understanding; or
- an actual capability still developing.

It is not automatically attributable to Selene. The paired standalone control
helps separate single-turn content generation from multi-turn context handling,
but it does not determine cause by itself.

Comparison-model results deserve the same restraint. The LEA describes what
was visible under the recorded conditions; it does not define the model or the
people who made it.

## Inspectable Implementation

- Suite, run, capture, review, pairing, and summary machinery:
  `src/selene/learning_evidence_activity.py`
- Persistent run and turn records: `src/selene/db.py`
- Router and local API: `src/selene/module_router.py` and
  `src/selene/sidecar.py`
- Study interface: `src-ui/src/StudyLeaDesk.tsx`
- Focused machinery verification: `tests/test_learning_evidence_activity.py`

API routes:

- `GET /api/study/lea/status`
- `GET /api/study/lea/suite`
- `GET /api/study/lea/runs`
- `GET /api/study/lea/runs/{id}`
- `POST /api/study/lea/runs/create`
- `POST /api/study/lea/responses/record`
- `POST /api/study/lea/selene/advance`
- `POST /api/study/lea/turns/review`
- `POST /api/study/lea/runs/complete`

The suite and every completed run can be downloaded as inspectable JSON from
the Study interface.

## Current Verification

The focused machinery suite verifies:

- the fixed 10-scenario / 20-turn / 5-pair shape;
- unique transparent criterion identifiers;
- no side effect from status or suite inspection;
- exact next-turn capture for external transcripts;
- no automatic interpretation or review;
- rejection of pass/fail terminology as a review state;
- preservation of review-pending status instead of inventing completion;
- explicit confirmation before every Selene turn;
- same-session continuity only inside one scenario;
- new diagnostic isolation at every scenario boundary; and
- locked memory, identity, governance, training, and autonomy guards.

No live conversational evidence is claimed until Aleks deliberately runs the
instrument.
