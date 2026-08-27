# Selene LLM-Parity Phase 5.5 — Problem Resolution and Informed Retry

Date: 2026-08-27
Status: implemented in the current worktree; bounded focused gate passed

## Purpose

This is an architectural augmentation between completed Phase 5 whole-answer
composition and Phase 6 knowledge expansion. It does not replace either phase.
It gives existing reasoning machinery one shared way to determine whether a
bad or unresolved result came from missing context, a false premise, a
constraint conflict, an inference, a source, retrieval, or verification.

The coordinator is connective tissue, not a new organ or solver authority.
It creates no facts, takes no action, and writes no memory or retained
knowledge.

## Existing Ancestry Preserved

The implementation reuses rather than duplicates:

- F1 Group 17 question-role teaching for who, what, when, where, why, and how;
- Conversation Spine and Dialogue Workspace current-session context;
- intelligenceOS ABCD(E) observations, candidate models, challenges, evidence,
  and stopping;
- claim/evidence validity and candidate status;
- exploratory-reasoning prediction, hypothesis, and data-conflict contracts;
- session proposition ancestry, selective invalidation, and recomputation;
- metacognitive correction, bounded reopening, and graceful stopping; and
- exact answer-operation ownership and completion truth.

## Added Connective Tissue

`problem_resolution.py` now provides:

1. one inspectable seven-point reconstruction containing who, what, why, when,
   where, how, and context;
2. explicit missing-dimension states without inventing the absent context;
3. a typed satisfiability gate for premises, objectives, policies, and
   constraints;
4. explicit conflicts for incompatible required values, required-and-forbidden
   states, impossible numeric bounds, and declared conflicts;
5. a canonical problem-solving state map:
   `KNOWN_SUPPORTED`, `CANDIDATE_UNVERIFIED`,
   `UNKNOWN_INSUFFICIENT_EVIDENCE`, `CONFLICT_UNSATISFIABLE`,
   `WRONG_FALSIFIED`, and `RETRY_UPDATED_APPROACH`;
6. bounded failure classes for knowledge, retrieval, inference, source,
   ambiguity, evidence, constraints, premises, underspecification, and
   verification;
7. visible attempt ancestry, preserved useful mechanics, and failed causal
   paths; and
8. an informed-retry contract that rejects blind regeneration and refuses to
   repeat either the failed approach or its named causal path.

intelligenceOS now includes this packet in each reasoning result. An
unsatisfiable typed problem stops for constraint revision rather than blaming
the solver. Metacognition observes the packet, holds constraint conflicts, or
permits one materially changed attempt when the failed attempt supplied useful
diagnostic information.

The existing Answer Engine completion retry now builds the same diagnosis
before its one allowed second pass. It carries the first attempt, unresolved
obligations, preserved useful parts, failed path, and selected changed approach
into intelligenceOS. The retry is therefore an informed continuation rather
than another sample of the original request.

Status and preview routes are available as:

- `problem_resolution.status`
- `problem_resolution.preview`

Selene Chat can carry an explicitly supplied `problem_context` into this
coordination path. Ordinary turns without a typed problem context retain their
existing behavior.

## Verification

Eleven dedicated checks cover:

- the seven-point and epistemic-state contract;
- status and preview routing;
- contradictory hard constraints;
- missing information where unknown is the only justified result;
- false premises;
- materially ambiguous context despite a plausible why statement;
- correction after a confident falsified answer;
- rejection of a repeated failed causal path;
- supported verification; and
- intelligenceOS-to-metacognition conflict and informed-retry handoff.

The first focused run exposed a real defect: a candidate retry could repeat the
failed approach when the attempt also supplied a differently worded causal-path
label. The source contract was corrected to exclude both surfaces. The final
dedicated gate passed 11 checks. A separate Answer Engine regression verifies
that the executed completion retry receives prior-failure information and a
different strategy. The adjacent intelligenceOS, metacognition, and selected
Chat integration checks also passed after correcting one local payload-name
integration error discovered by the focused Chat gate.

No live Q&A, resident database, teaching, build, package, reinstall, or broad
stress test was used.

## Boundaries Preserved

- no fact invention or hidden reasoning exposure;
- no memory, retained-knowledge, identity, personality, Vys, governance, or
  authority change;
- no model training, LoRA, provider call, self-replication, or autonomous
  action;
- no expression scripting or transfer of NLO/Voice authority;
- unknown and wrongness remain epistemic/process states, not identity failure;
  and
- a constraint conflict cannot be bypassed by retrying harder.

## Deliberate Deferrals

The following remain in their existing roadmap positions:

- broader domain verification and fact-checking: Phase 7;
- learned open-language reconstruction: Phase 8 substrate decision;
- sensed environmental context: Phase 9 perception and embodiment;
- external experiments/actions: later scoped workbench authority; and
- durable cross-session failure learning: reviewed memory or teaching paths,
  never silent retention.

## Next

Return to Phase 6 knowledge and teaching expansion. Lesson-specific gaps can
now be distinguished from premise, context, constraint, source, inference,
retrieval, and verification failures before additional teaching is proposed.
