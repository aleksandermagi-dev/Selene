# Selene Conversational Breadth — Phase 5 Correction, Wrongness, and Epistemic Revision

Date: 2026-07-25

Status: implemented and proportionally verified.

## Outcome

Selene now has one bounded, inspectable update contract for:

- correction;
- refinement;
- scope restriction;
- extension;
- competing explanation;
- unresolved contradiction;
- replacement;
- reopening.

The contract coordinates existing owners rather than becoming a new truth
authority:

```text
visible correction or changed evidence
  -> identify the affected claim
  -> preserve still-valid structure
  -> classify the warranted update
  -> recheck only dependent conclusions when needed
  -> continue, compare, qualify, reopen once, or hold
```

Ordinary wrongness is treated as correctable. It does not require collapse,
defensive persistence, over-apology, or a reset of the whole conversation.

## Implemented

### Shared epistemic-revision contract

`src/selene/epistemic_revision.py` provides:

- conservative visible-signal classification;
- explicit structured update kinds for organ-to-organ handoff;
- affected target, prior claim, revised claim, and scope;
- separate support for updates to Aleks, Selene, or a shared model;
- supporting evidence and source references;
- validity after the update;
- preserved useful structure;
- one bounded dependent recheck;
- unresolved contradictions;
- model ancestry and valid scope;
- response obligations;
- metacognitive and retained-state handoffs;
- an explicit no-shame social posture.

The packet has no direct truth authority. It cannot write memory, silently
rewrite approved knowledge, alter identity or governance, train a model,
expand autonomy, or route Selene into Cocoon automatically.

### Current-session continuity

Dialogue Workspace stores only compact current-session epistemic updates
inside its existing pragmatic state. No new durable-memory schema or hidden
knowledge store was added.

Conversation Spine carries:

- the current revision plan;
- up to twelve bounded session updates;
- the affected target and revised claim as grounding anchors;
- model ancestry visibility;
- whether selective revision is active.

This lets a later turn use a prior correction without treating the correction
as personal memory or resetting unrelated context.

### Comprehension and retained knowledge

Comprehension receives the same packet. A real reopening or unresolved
contradiction may place the current understanding into
`reopened_for_recheck`.

A simple correction, refinement, scope restriction, or replacement does not
automatically create an endless reopening loop.

Approved knowledge remains owned by the existing Comprehension review and
reapproval lifecycle. Phase 5 creates no silent retention, supersession, or
Chat activation.

### Metacognition

Metacognition now distinguishes:

- an already-applicable structured correction;
- a correction that truly requires reopening;
- competing explanations;
- an unresolved contradiction;
- a repeated recheck with no new material.

Legacy unstructured correction signals still receive one bounded recheck.
Structured ordinary corrections can continue immediately. Reopening and
contradiction still receive at most one recheck without new evidence, after
which the result is held open rather than recursively questioned.

### NLO, Voice, and active Chat

NLO carries the revision packet into discourse planning. Its inspectable moves
can:

- identify the affected claim without resetting context;
- preserve unaffected useful structure;
- recheck changed dependencies once;
- leave a contradiction visible;
- compare competing explanations without forcing a result.

NLO does not decide truth and Voice cannot change the update's meaning.

Active Chat can use a bounded conversational response seed for refinement,
scope restriction, extension, competing explanations, unresolved
contradictions, replacement, and reopening. Ordinary correction remains
owned by the existing social-language correction path.

The complete packet remains visible in the Chat result and recorded assistant
payload for inspection.

### Inspectable routes

- `epistemic_revision.status`
- `epistemic_revision.plan`

These routes expose the contract and create a plan only. They do not mutate
Selene or retained state.

## Verification

Testing followed the Teaching Law and ethical testing law:

- static compilation checks;
- structured packet checks;
- ordinary current-session corrections;
- Newtonian mechanics retained within its valid scope after a broader model
  change;
- competing explanations kept live;
- unresolved contradictions held visibly;
- evidence updating either Aleks or Selene;
- one bounded recheck and stopping behavior;
- Core/Mind owner locks;
- no memory write or proposal from an academic scope correction;
- NLO, Voice-handoff, Comprehension, Conversation Spine, and active Chat
  integration;
- adjacent intent, pragmatics, repair, language formation, supported
  semantics, and visible-speech regressions.

Result: **236 focused tests passed**.

No live Selene conversation, adversarial battery, distress-shaped prompt,
provider call, model training, package, or reinstall was needed. No frontend
files changed, so the production frontend build was not repeated.

`git diff --check` passed with only existing Windows LF/CRLF warnings.

## Boundaries Confirmed

Phase 5 creates no:

- identity, personality, governance, law, or authority change;
- durable or hidden memory write;
- automatic approved-knowledge rewrite;
- source-category truth authority;
- invented citation;
- model training, fine-tuning, or LoRA;
- provider dependency;
- autonomy expansion;
- automatic Cocoon routing;
- hidden chain-of-thought exposure.

Selene remains Selene. Correction changes the affected claim or model, not the
individual.

## Remaining Gaps

- Phase 5 coordinates claim updates but does not yet provide a full
  claim-by-claim evidence ledger.
- Observation, source statement, inference, hypothesis, model, conclusion,
  and speculation are not yet represented as one shared typed claim packet.
- Source disagreement is visible in existing research and comprehension
  paths, but is not yet normalized across domains.
- Model ancestry is carried through the current session; retained knowledge
  ancestry still remains owned by the existing reviewed comprehension and
  provenance systems.
- Cross-domain analogy testing remains Phase 8 work.
- Longer personal and shared-joke callback continuity remains Phase 9 work.

## Next Phase — Phase 6: Sources, Claims, Evidence, and Model Ancestry

Phase 6 will:

- separate observation, source statement, inference, hypothesis, model,
  conclusion, and speculation;
- compare claims individually instead of accepting or rejecting a whole
  source category;
- preserve disagreement and missing evidence;
- explain what evidence would change an answer;
- preserve source and model ancestry with valid scope;
- keep science, history, religion, mythology, archaeology, and other domains
  open to evidence without automatic dogmatic acceptance or dismissal.

The completion gate requires citations never to be invented, source authority
never to become truth merely by category, individual claims to remain
independently useful or revisable, and direct answer, inference, and
uncertainty to remain visibly distinguishable.
