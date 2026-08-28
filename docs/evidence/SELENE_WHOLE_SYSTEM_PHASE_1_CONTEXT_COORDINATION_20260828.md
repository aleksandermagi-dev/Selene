# Selene Whole-System Phase 1 — Canonical Context and Coordination

Date: 2026-08-28

Status: complete for current scope

Parent plan:
[Selene Whole-System Maturation Plan](../architecture/SELENE_WHOLE_SYSTEM_MATURATION_PLAN_20260827.md)

## Outcome

Selene now constructs one canonical representation of the visible current turn
before optional personal Memory retrieval. The representation preserves typed
facts, dialogue obligations, owners, current-session continuity, and correction
ancestry without becoming durable Memory or answer authority.

The repaired order is:

```text
visible turn
  -> meaning and pragmatic acts
  -> Dialogue Workspace and correction lifecycle
  -> Conversation Spine
  -> typed current-turn fact ledger and owner inputs
  -> subject / role / thread / privacy / function / competition gates
  -> approved Memory and knowledge contributions
  -> responsible answer owners
  -> typed operation results and visible fulfillment
  -> NLO and Voice expression
```

## Implemented Work

### Canonical current-turn facts

`src/selene/current_turn_fact_ledger.py` now records bounded, attributable
entities, quantities, options, criteria, observations, claims, relations,
conditions, constraints, corrections, and sequence. Facts remain reported
speaker input rather than independently verified truth. They write no state.

Each canonical response obligation receives an owner-input packet containing
the relevant fact IDs and supplied fields. Equivalent comparison wording is
tested for stable candidates and criteria. Two quantities in the same clause
receive distinct IDs.

Router keys:

- `current_turn_facts.status`
- `current_turn_facts.build`

### Owner consumption and completion truth

`src/selene/answer_operations.py` attaches a current-turn input receipt to
every supported operation result. A missing-input report must account for what
the speaker already supplied. If two candidates and a criterion are present,
the answer path may report an incomplete owner result, but it may not ask for
those candidates or that criterion again.

Existing typed operation contracts and semantic-fulfillment receipts remain
the completion authority. Generic prose, an obligation ID, or fluent wording
does not prove that the requested operation was performed.

### Retrieval order and relevance competition

Approved personal Memory retrieval now occurs after Conversation Spine and the
current-turn ledger exist. Memory receives the typed speaker envelope and the
same Spine used by other owners. `src/selene/semantic_relevance.py` checks:

- subject alignment;
- requested response role;
- current-session thread and correction posture;
- speaker and consent scope;
- whether the candidate actually performs an owner-only operation; and
- whether current-turn facts or a responsible owner take precedence.

Knowledge retrieval already followed Spine construction; its existing
performed-function and topic gates now share the same current-turn contract.

### Correction lifecycle

Completed correction work no longer persists as `dependency_revision` on an
unrelated turn. A real topic transition expires unresolved correction posture
to inspectable ancestry rather than deleting history. Only affected
propositions remain eligible for recomputation; unrelated session context is
preserved.

### Expression boundary

Approved memories now carry a read-only expression reconstruction separate
from their index title and review metadata. Internal titles, Braid fields,
source IDs, table names, record classes, and old review-lane labels do not
become Selene's visible wording. Silent contextual influence may provide
reconstructed meaning without announcing retrieval or using remembered
wording as a script. NLO and Voice remain the expression owners.

## Completion Gate

| Requirement | Result |
| --- | --- |
| Equivalent paraphrases preserve relevant facts and owner inputs | Met |
| Supplied facts cannot be requested again as missing | Met |
| Stale correction state does not cross unrelated topics | Met |
| Current-turn facts and responsible owners outrank optional retrieval | Met |
| Private Memory is held for an ineligible claimed speaker | Met |
| Selected Memory contributes reconstructed meaning, not an internal title | Met |
| Corrections preserve selective recomputation and ancestry | Met |
| Typed completion and visible fulfillment remain required | Met |
| NLO and Voice retain expression ownership | Met |

## Verification

Machinery and bounded integration checks:

```text
130 focused context, operation, completion, correction, relevance, Memory, and maturity-ledger tests passed
9 focused Selene Chat shell integration tests passed
139 total selected checks passed
```

The tests covered paraphrase-equivalent fact extraction, mixed comparison and
choice inputs, direct correction values, unique quantity IDs, owner receipts,
stale correction expiry, selective proposition ancestry, privacy scope,
retrieval competition, contextual Memory reconstruction, internal-label
holding, and the real Chat ordering path.

No broad Q&A, stressful prompt, teaching action, Memory write, retention
decision, Dream decision, package, reinstall, external action, or autonomy
change was needed.

## Remaining Limits

- Fact extraction is intentionally bounded and still uses some lexical and
  structural detection; it is coordination machinery, not a truth oracle or
  general semantic solver.
- Personal Memory has correct Phase 1 ordering and privacy competition, but
  broad paraphrase recall, working-context expiry, reconsolidation, revocation,
  and natural relationship continuity remain Phase 2 work.
- Knowledge breadth and delayed application remain ordered-education work.
- Language breadth and visible warmth remain later expression work; this phase
  repaired substance delivery without scripting Selene's voice.

## Boundaries Preserved

This phase created no durable Memory, retained knowledge, identity,
personality, governing-law, authority, training, LoRA, autonomy,
self-replication, external action, or hidden reasoning access. Selene remains
Selene. Current-session context remains distinct from personal Memory and
general taught knowledge.

## Next Phase

Phase 2 — Working, Personal, and Knowledge Memory Maturation.

The next work should mature attention and expiry, explicit/contextual recall
across varied wording, reconstruction versus inference, duplicate prevention,
correction and reconsolidation, privacy and speaker scope, and natural use of
approved history without turning Memory into a script.
