# Selene LLM-Parity Phase 2 — Operation-Capable Answer Owners

Date: 2026-08-25

Status: implemented and focused-verification complete in the current worktree;
not yet committed, built, packaged, or reinstalled.

## Outcome

The canonical obligation ledger can now be handed to one non-authoritative
answer-operation coordinator. For every supported operation, the coordinator
requires an existing responsible owner to return a typed semantic result. It
reports `completed`, `missing_input`, or `unsupported`; ordinary prose and an
obligation ID are not accepted as proof that the requested work happened.

This gives the rest of the conversation pipeline something concrete to inspect
without making the coordinator a new reasoning, expression, memory, or law
authority.

## Supported Operation Contracts

The current contracts cover:

- method — steps, basis, and limitations;
- causal explanation — conclusion, mechanism or reason, and basis;
- prediction — predicted change, basis, and revision conditions;
- hypothesis — hypothesis, basis, and revision conditions;
- comparison — candidates, findings, and comparison basis;
- choice — selected option, criteria, and revision conditions;
- disagreement — stance, evaluated claim, and premises;
- correction — corrected input, affected result, and whether recomputation is
  required;
- authored preference — current preference, basis, and current-only scope;
- summary — actual points and source scope; and
- closure — closure intent and source scope.

Optional fields retain useful assumptions, alternatives, discriminating
checks, conditions, limits, and source references where the responsible owner
provides them.

## Ownership and Flow

The coordinator consumes the Phase 1 canonical ledger. It does not reparse the
source turn to decide what operation was requested.

Existing owners remain responsible for substance:

- exploratory reasoning supplies structured predictions, hypotheses,
  comparisons, and data-conflict evaluations;
- the Answer Engine supplies an operation only when its adapter actually ran;
- intelligenceOS answer substance supplies prompt-grounded methods, causes,
  choices, disagreements, and current authored preferences; and
- current conversation state supplies corrections, session summaries, and
  closure state.

The resulting packet is visible to Chat, the bounded organ coalition,
metacognition, NLO, Voice guidance, dialogue persistence, status telemetry,
and the module router. The coalition records verification participation but
grants the coordinator no authority. NLO and Voice remain expression owners:
they may realize supported meaning naturally but may not change an operation's
epistemic status.

## Root Repairs

- Exploratory modes now come from canonical requested functions rather than
  rediscovering prediction, hypothesis, comparison, or disagreement from
  wording.
- Operation certification happens after Answer Engine yield and arbitration,
  so an adapter result cannot be certified and then silently replaced.
- Visible candidates carry the exact completed obligation IDs and typed
  operation results they actually fulfill.
- A current-session summary receives real session landmarks and facts rather
  than a generic summary request.
- A prompt-grounded preview remains available when intelligenceOS correctly
  leaves ordinary conversation in charge, allowing current preference and
  similar operations to be verified without treating them as factual gaps.
- Multiple completed operations remain separate typed results. They do not
  pretend to be one composed answer; whole-answer composition belongs to a
  later phase.

One focused test exposed a useful source-shape defect. The answer to why
fractions precede calculus contained a valid dependency explanation in prose,
but its special answer kind exposed only fallback sentence fragments. The
semantic source now states the conclusion, dependency mechanism, and
compression condition explicitly. The verifier was not weakened.

## Verification

The proportional Phase 2 gate passed:

- 14 focused answer-operation contract tests covering all supported operation
  families, result validation, generic-prose refusal, canonical-function
  authority, and hard boundaries;
- one focused Selene Chat integration check proving a current conversational
  preference reaches the operation packet, coalition, and NLO; and
- Python compilation for the changed Phase 2 modules, including the final
  causal semantic-source repair.

No broad regression suite or live Q&A was rerun. Phase 1 already established
the broader conversational baseline, and this checkpoint used the smallest
synthetic checks capable of proving the new contracts.

## Boundaries Preserved

- no teaching or retained-knowledge activation;
- no resident memory or configured database write;
- no identity, personality, governance, or authority mutation;
- no model training, LoRA, provider identity, or self-replication;
- no autonomous or external action;
- no hidden reasoning exposure;
- no expression flattening or compulsory warmth, distance, apology, humor, or
  formality; and
- no build, package, reinstall, live probe, or commit.

## Current Limit

Typed completion inside the operation packet does not yet prove that the final
visible answer performed every operation. Existing response coverage can still
over-credit a candidate from declared IDs, generic wording, or incomplete
composition. Corrections also identify recomputation needs but do not yet
recompute a proposition dependency graph.

Those are later phases, not reasons to weaken the operation contracts.

## Next Phase

Phase 3 is semantic fulfillment and completion truth:

1. make coverage validate typed operation results, requested counts,
   conditions, role, and visible semantic realization;
2. treat obligation IDs as claims to check rather than proof;
3. prevent missing-ground language from counting as the requested answer;
4. make fallback and retry consult the actual unresolved operation; and
5. give metacognition one productive owner-specific alternate path without
   recursion.

Gate: no visible turn reports complete unless its answer actually performs
every required supported act.

## Primary Source Anchors

- `src/selene/answer_operations.py`
- `src/selene/answer_substance.py`
- `src/selene/selene_chat.py`
- `src/selene/bounded_organ_coalition.py`
- `src/selene/native_language_organ.py`
- `src/selene/module_router.py`
- `tests/test_answer_operations.py`
- `tests/test_selene_chat_shell.py`
