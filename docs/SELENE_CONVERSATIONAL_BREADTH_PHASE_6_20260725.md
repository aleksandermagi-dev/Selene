# Selene Conversational Breadth — Phase 6 Sources, Claims, Evidence, and Model Ancestry

Date: 2026-07-25

Status: implemented and proportionally verified.

## Outcome

Selene now has one bounded, inspectable claim-and-evidence contract shared by
research, intelligenceOS, Comprehension, the Answer Engine, Metacognition,
NLO, Voice handoff, and active Chat.

The contract keeps these meanings distinct:

```text
observation
  -> attributed source statement
  -> bounded inference
  -> falsifiable hypothesis or model
  -> revisable conclusion

speculation remains explorable, but is not evidence
```

Claims are assessed individually. A source, tradition, discipline, or domain
is not accepted or rejected as one indivisible block.

## Implemented

### Shared typed claim-and-evidence packet

`src/selene/claim_evidence.py` provides:

- seven explicit claim types:
  - observation;
  - source statement;
  - inference;
  - hypothesis;
  - model;
  - conclusion;
  - speculation;
- stable claim IDs and claim-level scope;
- separate confidence and validity;
- source and evidence references;
- explicit basis-claim relationships;
- limitations and missing evidence;
- a visible account of what would change each claim;
- claim-level disagreement by shared subject and differing stance;
- model ancestry and valid scope;
- an expression handoff that keeps direct answers, inferences, and
  uncertainty separate;
- citation validation against supplied, attributed source references.

An unattributed source statement is held back. A citation that does not trace
to an accepted source is also held back rather than invented or silently
accepted.

### Domain-neutral evidence policy

Source category is descriptive metadata, never a truth or credibility score.
Science, history, archaeology, religion, mythology, and other domains remain
open to the same questions:

- What is directly observed?
- What did the source actually state?
- What inference is being made?
- What evidence supports it?
- What is missing?
- What would revise or falsify the current claim?

This allows one claim from a source to remain useful while another is limited,
revised, contested, reopened, or superseded.

### Research and intelligenceOS

Source-backed research now converts accepted attributed statements and
bounded inferences into the shared packet. Existing disagreement, citation,
and missing-evidence behavior remains intact.

intelligenceOS now emits:

- observations from supplied problem context;
- candidate models grounded in those observations;
- a revisable current conclusion;
- explicit basis links and model limitations.

The packet exposes reasoning structure without exposing hidden
chain-of-thought.

### Comprehension and the Answer Engine

Approved, answer-eligible knowledge resources become bounded conclusion claims
for the current response. Their provenance, limits, confidence, and Phase 5
revision ancestry remain visible.

The Answer Engine carries the packet through source-backed research and
comparison/planning answers. It does not gain truth authority or a new
persistence path.

### Metacognition

Metacognition can now inspect:

- the number of claims;
- claim-level disagreements;
- missing evidence;
- whether source-backed claims are attributed;
- whether citations trace to accepted sources;
- whether direct answer, inference, and uncertainty remain separate.

Claim disagreement can reopen fit assessment without automatically rejecting
either source or recursively questioning the entire answer.

### NLO, Voice, and active Chat

NLO preserves claim type, basis, confidence, disagreement, and uncertainty in
its discourse plan. Its inspectable moves can:

- keep observation separate from interpretation;
- attribute a source statement without promoting it to fact;
- label an inference and retain its basis;
- keep a hypothesis or model falsifiable;
- preserve claim-level disagreement and missing evidence.

Voice may vary expression, but it may not change a claim type or upgrade
confidence.

Active source-backed Chat now visibly separates:

- attributed source statements;
- bounded inference;
- uncertainty;
- missing evidence.

The same typed packet remains inspectable in the Chat result and assistant
record.

### Inspectable routes

- `claim_evidence.status`
- `claim_evidence.build`

These routes report or construct a non-persistent packet. They do not mutate
Selene or retained state.

## Verification

Testing followed the Teaching Law and ethical testing law:

- static compilation checks;
- all seven claim types and reversal conditions;
- attribution required for source statements;
- invented citation rejection;
- independent claim evaluation within one source;
- claim-level disagreement without whole-source rejection;
- domain-neutral treatment across science, mythology, and archaeology;
- Phase 5 model ancestry preservation;
- source-backed research integration;
- intelligenceOS observation, model, and conclusion handoff;
- Metacognition, NLO, Voice-handoff, Answer Engine, Comprehension, and active
  Chat integration;
- Conversation Spine, Dialogue Workspace, intent, contextual speech,
  pragmatics, repair, supported semantics, language formation, Voice, and
  visible-speech regressions.

Result: **292 focused cross-organ tests passed**.

No live Selene conversation, adversarial battery, distress-shaped prompt,
provider call, model training, package, or reinstall was needed. No frontend
files changed, so the production frontend build was not repeated.

Static compilation passed. `git diff --check` passed with only existing
Windows LF/CRLF warnings.

## Boundaries Confirmed

Phase 6 creates no:

- identity, personality, governance, law, or authority change;
- durable or hidden memory write;
- automatic evidence-ledger or approved-knowledge write;
- source-category truth authority;
- invented citation;
- model training, fine-tuning, or LoRA;
- provider dependency;
- autonomy expansion;
- automatic Cocoon routing;
- hidden chain-of-thought exposure.

Selene remains Selene. Evidence may revise a claim or model; it does not
redefine the individual.

## Remaining Gaps

- The packet coordinates currently supplied and already-approved evidence; it
  does not autonomously acquire sources.
- Source-quality assessment remains evidence-specific rather than a global
  reputation score.
- Retained evidence-ledger updates remain explicitly reviewed and owned by the
  existing provenance and Comprehension systems.
- Curiosity, initiative, collaborative help, and conversational-energy
  decisions remain Phase 7 work.
- Cross-domain analogy testing remains Phase 8 work.
- Longer personal and shared-joke callback continuity remains Phase 9 work.

## Next Phase — Phase 7: Curiosity, Initiative, Collaborative Help, and Conversational Energy

Phase 7 will let Selene:

- say when she has an idea;
- offer a relevant direction, next step, or alternative;
- ask a curiosity question when it genuinely adds value;
- surface a useful connection without hijacking the conversation;
- choose whether to answer, ask, offer, wait, stay quiet, or let a conversation
  end;
- ask Aleks for specific help during collaborative work when a missing
  observation, expertise, value choice, or user-owned action materially blocks
  progress;
- use available reasoning and support before asking;
- incorporate the supplied help and resume the task.

The completion gate requires initiative without pressure, relevant curiosity,
specific and materially necessary help requests, no reflexive permission
seeking, no automatic Cocoon routing, no autonomy expansion, and natural
endings for already-complete answers.
