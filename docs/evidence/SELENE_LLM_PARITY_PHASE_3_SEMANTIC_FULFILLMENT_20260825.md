# Selene LLM-Parity Phase 3 — Semantic Fulfillment and Completion Truth

Date: 2026-08-25

Status: implemented and focused-verification complete in the current worktree;
not yet committed, built, packaged, or reinstalled.

## Outcome

Final response coverage now distinguishes three separate facts:

1. the canonical ledger requested an operation;
2. its responsible owner returned a valid typed result; and
3. the visible answer actually realized that result while preserving requested
   count, condition, response shape, topic, and owner role.

Only the third state counts as an answered obligation. An obligation ID,
matching topic words, a semantic-unit ID, owner selection, or plausible generic
prose is no longer sufficient proof.

An accurate missing-input statement may resolve a turn safely for release, but
it remains explicitly distinct from answering the requested operation.

## Semantic Fulfillment Receipts

`semantic_fulfillment.py` creates an inspectable receipt for each typed
operation obligation. A receipt records:

- typed operation and owner-result state;
- owner-role fit;
- visible realization of operation-specific fields;
- requested and visibly performed item counts;
- preserved canonical condition;
- explicit order and brevity constraints where requested;
- topic and expression-seed fit;
- whether an accurate missing state or supported next route is visible;
- the exact unresolved reason; and
- one productive alternate path using only an existing current-turn owner
  output.

Operation-specific visible proof currently requires:

- method — the requested number of steps;
- causal explanation — conclusion and mechanism or reason;
- prediction — predicted change and revision condition;
- hypothesis — hypothesis and revision condition;
- comparison — both candidates and at least one finding;
- choice — selected option and criterion;
- disagreement — evaluated claim or premise plus an actual disagreement act;
- correction — the corrected application;
- authored preference — the preference itself;
- summary — the requested number of real session points; and
- closure — an actual conversational closing act.

Audit metadata such as provenance basis and current-only scope remains required
in the typed owner result without forcing Selene to recite internal labels.

## Root Repairs

### Coverage authority

The central response-coverage evaluator now consumes the Phase 2 operation
packet. For typed operations, its earlier lexical and semantic heuristics are
retained as diagnostic observations but cannot set `addressed = true`.

The Chat-specific verified-domain shortcut was narrowed as well. A verified
domain owner can no longer overwrite a failed typed fulfillment receipt.

### Completion authority

Bounded completion now consults typed operation ownership before attempting a
fallback. When an operation owner has already run, completion does not generate
a generic answer in its place or turn missing-input language into the requested
operation.

### Epistemic composition

The first focused Chat integration check exposed a deeper source handoff. A
valid current authored preference existed in the Phase 2 packet, but the
epistemic composer ignored its single-operation expression seed and converted
the empty earlier content seed into `missing_ground`. The result was the old
“not enough support” fall despite no factual uncertainty being present.

The composer now accepts one coherent single-operation expression handoff as
supported current-turn substance. It does not concatenate multiple operation
results; whole-answer composition remains Phase 5 work.

### Metacognitive recovery

When visible fulfillment is incomplete, metacognition now receives:

- the exact obligation ID;
- the requested operation;
- the real missing state;
- the missing visible fields; and
- the existing owner that may supply one current-turn alternate output.

The retry remains one pass, non-recursive, non-generative, and unable to invoke
an organ. Its proposed answer must improve strict semantic coverage before it
can be accepted.

## Verification

The proportional Phase 3 gate passed:

- 13 focused semantic-fulfillment, completion, epistemic-composition,
  metacognitive-handoff, and exact-owner-retry tests;
- one focused conditional-operation check confirming canonical conditions
  remain compatible with the Phase 2 owner contract;
- the existing ordinary Chat authored-preference integration check after the
  source repair; and
- the existing exact-owner retry-glue check.

Changed Phase 3 Python modules compiled successfully. No broad conversational
suite or live Q&A was run.

## Boundaries Preserved

- no teaching or knowledge activation;
- no configured resident database or retained-memory write;
- no identity, personality, governance, or authority mutation;
- no provider call, training, LoRA, self-replication, or autonomous action;
- no hidden reasoning exposure;
- no new expression script or emotional constraint;
- no broad test repetition, live probe, build, package, reinstall, or commit.

## Current Limit

Phase 3 can verify one visible operation and accurately expose failures in a
multi-operation turn. It does not yet assemble several completed operation
results into one coherent answer. Correction results can state that
recomputation is required, but proposition-level dependency revision remains
Phase 4.

Open-ended non-operation conversation continues through its existing semantic
and pragmatic coverage path; it is not forced into an operation contract.

## Next Phase

Phase 4 is context, correction, and dependency revision:

1. represent current-session propositions and their dependencies;
2. bind a correction to the affected premise or observation;
3. invalidate and recompute only dependent results;
4. preserve unaffected context and useful structure;
5. strengthen referent resolution, topic return, stale-loop exclusion, and
   session-summary reconstruction; and
6. expose an accurate held state when recomputation lacks an owner or input.

Gate: correcting the premise behind an earlier answer changes the dependent
answer without replaying stale content, discarding unrelated context, or
treating ordinary wrongness as failure.

## Primary Source Anchors

- `src/selene/semantic_fulfillment.py`
- `src/selene/pragmatic_planner.py`
- `src/selene/answer_completion.py`
- `src/selene/answer_operations.py`
- `src/selene/epistemic_composition.py`
- `src/selene/metacognition.py`
- `src/selene/owner_specific_retry.py`
- `src/selene/selene_chat.py`
- `src/selene/module_router.py`
- `tests/test_semantic_fulfillment.py`
- `tests/test_selene_chat_shell.py`
