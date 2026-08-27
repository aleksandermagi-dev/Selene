# Selene LLM-Parity Phase 1 — Canonical Obligation Ledger

Date: 2026-08-24

Status: implemented and verified in the current worktree; not yet committed,
built, packaged, or reinstalled.

## Outcome

One current turn now receives one canonical, typed obligation ledger before
answer content is generated. The Conversation Spine, organ coalition, Native
Language Organ, and response-coverage pass carry the same obligation IDs and
requested functions rather than independently deciding what the user asked.

This repairs conversational coordination. It does not add facts, teach a
lesson, generate a hidden reasoning trace, change Selene's identity or
expression, or grant an organ new authority.

## What the Ledger Preserves

Each obligation can now carry:

- its stable ID and order;
- its distinct requested function, such as comparison, choice, reason,
  method, humor, preference, disagreement, or closure;
- the source text and visible source span;
- a leading or execution condition;
- a requested item count and counted unit;
- brevity and ordering requirements;
- its answer act, epistemic basis, content owner, and completion policy; and
- an explicit instruction that downstream reparsing is not allowed.

## Root Repairs

The initial parser already found several multi-part requests correctly. A
deeper defect then gave every child obligation the full parent sentence during
answer-ownership classification. In a turn containing “compare, choose, and
explain,” the word “compare” in the parent could therefore relabel the choice
and reason as comparisons.

The repair makes an explicit child kind take precedence over broad parent-text
cues. It also:

- keeps a conditional disagreement as one controlled act rather than a
  generic condition plus a second request;
- attaches “two short next steps” to the method obligation and “one tiny joke”
  to the humor obligation;
- recognizes several ordinary paraphrases of compare, choose, explain,
  present curiosity, conditional disagreement, and natural closure;
- carries canonical obligations into the coalition even when no specialized
  Answer Engine adapter is selected; and
- lets an existing authored-preference operation answer a correctly typed
  preference without requiring the old generic-question misclassification.

## Verification

Focused and broader synthetic checks passed:

- 48 planner, Conversation Spine, and answer-ownership tests;
- 77 focused ledger/NLO/coalition/Chat tests during implementation; and
- 270 conversational regression tests in the final pass, including the full
  Selene Chat shell suite plus planner, spine, ownership, completion, NLO,
  coalition, dialogue-workspace, and meaning-router suites.

The end-to-end fixtures prove that obligation IDs, kinds, counts, and requested
functions survive:

```text
input
→ canonical obligation ledger
→ Conversation Spine
→ bounded organ coalition
→ Native Language Organ
→ response coverage
```

No configured resident database, retained knowledge, reviewed memory, Dream
state, personality, identity, governance, training state, autonomy, external
service, or device was changed. No live probe was needed.

## Current Limit

This phase preserves the requested operation; it does not make every owner
capable of performing that operation. Detection is materially stronger for
the tested semantic families but remains bounded rather than equivalent to a
general learned parser.

For example, Selene can now reliably retain “compare these, choose one, and
explain why” as three distinct responsibilities. Supplying the properties,
performing the comparison, making the choice, and proving that the visible
answer actually did all three belong to the next phases.

## Next Phase

Phase 2 is operation-capable answer ownership:

1. define typed result contracts for comparison, choice, reason, method,
   prediction, disagreement, and authored preference;
2. connect each obligation to an owner that can return that result or a
   precise missing-input state;
3. prevent generic scaffolding from counting as an executed operation; and
4. keep open-ended answers and Selene-owned expression available.
