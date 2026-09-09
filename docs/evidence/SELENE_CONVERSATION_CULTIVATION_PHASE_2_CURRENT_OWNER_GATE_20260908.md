# Selene Conversation Cultivation Phase 2 — Current Owner Gate

Date: 2026-09-08
Status: implemented and affected-path verification complete
Scope: current-turn and active-session answer ownership before optional retrieval

## Purpose

Phase 1 made visible propositions available to the existing conversation
owners. Phase 2 closes the next handoff: a candidate receives current-owner
precedence only when its own typed owner result completed every required
obligation for the turn and accounted for the visible current-turn input.

The gate does not decide truth, generate an answer, create a new organ, or make
obligation identifiers proof of completion.

## Implementation

`visible_speech.py` now records a typed current-owner gate for every releasable
candidate. The gate verifies:

- a completed Answer Operations result exists for each required obligation;
- the result preserves the canonical responsible owner;
- the result's expression source is the candidate being evaluated;
- current-turn input was accounted for before the result; and
- any cross-owner handoff is an explicit current-session decision delegation
  or an exact verified Answer Engine route.

Partial completion remains visible but cannot take whole-turn priority.
Approved knowledge and Memory reconstruction remain eligible through their
ordinary relevance paths, but cannot impersonate a current owner. A missing
capable owner produces `held_no_capable_current_owner` rather than invented
ownership. Core/Mind boundary responses remain above the current-owner gate.

The exact session-decision-only force-selection block was removed. General
candidate arbitration now selects a completed session decision. The older
prompt-grounded coordination guard remains temporarily because comparison
against its removal showed that it still protects callback, correction, humor,
and multi-act paths which later cultivation phases have not yet fully typed.

## Direct Answer Connective Tissue

Answer Operations now has a small `direct_answer` contract for existing owners
that already produced a supported answer. It is materialized only when an owner
actually completes it; generic conversational turns do not receive synthetic
missing-result packets.

The contract currently connects:

- exact verified Math, attributed Research, and approved local-code domain
  answers;
- directly requested reviewed language-capability explanations;
- bounded active-session decision answers; and
- selected immediate contextual refinements whose existing contextual owner
  already produced the answer.

Semantic Fulfillment verifies that the direct answer is visibly realized. A
typed result, route name, or fluent sentence alone is still insufficient.

## Changed-Entity Evidence

Focused checks use creek/footbridge, cork/felt, marsh/ridge, and harbor/dunes
examples rather than the historical porch, notebook, pen, or plant fixtures.
They establish that:

- a completed current owner outranks optional learned retrieval;
- learned retrieval cannot claim current ownership by carrying an obligation
  id;
- partial current-owner completion does not seize a multi-part turn;
- a missing or incomplete typed result leaves the gate held;
- Core/Mind remains primary over a capable current owner;
- an active contextual refinement can complete a direct answer; and
- a novel natural choice reaches the general gate without the retired
  force-selection block.

## Verification

- 59 direct Answer Operations, Visible Speech, and Semantic Fulfillment checks
  passed after the final repair.
- 118 affected owner, proposition, Conversation Spine, session-decision,
  relevance, and conversational-teaching checks passed after the final focused
  additions.
- The complete `test_selene_chat_shell.py` matrix produced 120 passes and 10
  failures.
- A clean detached Phase 1 comparison produced 115 passes and 14 failures on
  the prior 129-test file. Phase 2 adds one new Chat test and repairs four
  pre-existing failures: verified Math visibility, attributed Research
  visibility, reviewed language-capability visibility, and the packet-wide
  source route. Every remaining current failure also failed at the clean Phase
  1 checkpoint; no new Chat regression remains.
- Python compilation passed for all changed production modules.
- `git diff --check` reported only expected Windows line-ending notices.

All execution used synthetic or disposable SQLite state. No live Q&A or
resident state was used.

## Boundaries Preserved

- no resident database or durable Memory write;
- no retained-knowledge, teaching, Study, or Dream mutation;
- no identity, personality, Vys, governance, or authority change;
- no training, fine-tuning, LoRA, provider, or model change;
- no autonomous or external action;
- no perception, embodiment, Tendril, package, or installed-runtime change;
- no weakening of provenance, uncertainty, verification, or stopping rules.

## Remaining Work

Phase 3 is learning-gap eligibility. A teaching invitation must be offered only
after current premises, current/session owners, exact domain owners, bounded
inference, and clarification have genuinely failed to supply the requested
answer. This phase should also absorb the malformed learning-gap subjects
observed in the existing baseline failures. Do not teach around those routing
defects.

Retrieval relevance, revision completion, typed participation acts, semantic
coverage, shared realization cleanup, and final changed-entity verification
remain later phases.
