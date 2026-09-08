# Selene Conversation Cultivation Phase 1 — Shared Proposition Normalization

Date: 2026-09-08  
Status: implemented and focused-verification complete  
Scope: visible current-turn structure and ephemeral current-session proposition continuity

## Purpose

Phase 0 established that several historical conversation checks were being
answered by scenario-specific compatibility branches. Phase 1 supplies the
general representation those branches had been masking. It does not attempt
to solve every answer-selection problem in the same layer.

The completion question for this phase was:

> Can the existing conversation owners preserve unfamiliar visible entities,
> relations, alternatives, state changes, and requested operations without
> turning them into durable Memory or confusing a request with an accomplished
> fact?

The focused answer is yes.

## Implementation

### Shared normalization connective tissue

`src/selene/proposition_normalization.py` now provides one shared structural
grammar for the existing Current-Turn Fact Ledger and Current-Session Decision
Context. It recognizes:

- explicit option containers;
- `whether X or Y`, `would you rather X or Y`, `between X and Y`, and ordinary
  comparison alternatives;
- multiple subject/predicate/object relations in one visible sentence;
- reported location changes; and
- requested placement operations.

This module is not an organ, answer generator, truth owner, or persistence
store. It normalizes only what is visible.

### Fact and operation distinction

The Current-Turn Fact Ledger now carries `operation` as a typed fact kind.
`Move the green cup to the cabinet` is therefore represented as a requested,
not-executed operation. `I moved the green cup to the cabinet` is represented
as a user-reported location update that remains independently unverified.

This prevents a command from silently becoming an observation.

### Active session propositions

The existing Session Proposition Ledger now receives the structured current-
turn ledger when Dialogue Workspace records the visible reply. It retains the
visible user-supplied structure in current-session scope, preserves source and
turn references, and links visible answer results to their current-turn bases.

An explicit reported state update supersedes only an earlier active proposition
with the same structural replacement key. Unrelated attributes remain active,
and dependent results become invalidated rather than silently surviving a
changed premise. Requested operations do not claim execution.

### Relevant proposition grounding

Conversation Spine now exposes a bounded `relevant_session_propositions` view.
It selects active attributable propositions by current subject terms, resolved
reference terms, summary intent, or a bounded recent fallback for deictic
follow-ups. Only the selected visible premises are added to the grounded prompt.

This does not make the ledger an answer owner. Phase 2 must still ensure that a
capable current-turn or current-session owner outranks unrelated retrieval.

### Generalized decision grammar

The existing Current-Session Decision Context consumes the shared option
normalizer. Natural alternatives no longer receive awkward synthetic labels
such as `sketch indoors option`, and `Which sounds better?` or `Would you rather
...?` can reach the existing revisable choice operation without a scenario noun.

## Changed-Entity Evidence

The new checks deliberately avoid the historical porch, notebook, pen, and
plant fixtures. They use:

- sketching indoors versus walking by a river;
- assembling a shelf versus reading by a window;
- green and silver cups with distinct attributes;
- a reported cup location change from a shelf to a cabinet; and
- a requested cup move that must remain unexecuted.

The checks establish that:

- paraphrased alternatives reach the same decision owner;
- coordinated attributes remain separate propositions;
- an instruction is not recorded as accomplished state;
- a later reported location selectively supersedes the earlier location;
- an unrelated object attribute survives that change;
- the Conversation Spine can retrieve the relevant active proposition; and
- every new path retains the no-Memory, no-training, no-authority, and no-action
  guards.

## Verification

- 64 direct fact-ledger, decision-context, proposition-ledger, Conversation
  Spine, and Dialogue Workspace checks passed during implementation.
- 149 affected-owner checks passed in the final focused run across Answer
  Operations, Conversation Continuity, Conversation Spine, Current-Turn Fact
  Ledger, Dialogue Workspace, Memory, Semantic Relevance, Current-Session
  Decision Context, and Session Proposition Ledger.
- Python compilation passed for all changed production modules.
- `git diff --check` reported only the existing Windows LF/CRLF notices.

All verification used synthetic or disposable state. No broad Q&A was run.

## Boundaries Preserved

- no resident database mutation;
- no durable Memory or retained-knowledge write;
- no identity, personality, Vys, governance, or authority change;
- no training, fine-tuning, LoRA, provider, or model change;
- no autonomous or external action;
- no Dream, Study, teaching, perception, embodiment, Tendril, package, or
  installation change; and
- no inference that a user-supplied proposition is independently true.

## Remaining Work

Phase 1 gives later owners a general visible structure; it does not by itself
guarantee that structure wins answer arbitration. The next dependency is
Phase 2, the current-owner gate:

1. prove which current-turn or current-session owner can satisfy each requested
   response function;
2. rank that owner ahead of optional learned retrieval;
3. retain a typed hold when no current owner is capable; and
4. verify with new nouns and reordered wording before removing any historical
   compatibility branch.

Learning-gap eligibility, retrieval relevance, revision completion, typed
participation acts, semantic coverage, and shared realization cleanup remain
later phases.
