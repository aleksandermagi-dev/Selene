# Selene Conversational Breadth — Phase 8 Cross-Domain Analogy, Hypothesis, and Discovery

Date: 2026-07-25

Status: implemented and proportionally verified.

## Outcome

Selene now has one bounded, inspectable structural-discovery contract for:

- finding a recurring pattern across domains;
- building an analogy from mapped relationships;
- distinguishing analogy from homology, causal connection, and equivalence;
- making a logical leap without presenting it as a conclusion;
- naming where the mapping holds and where it breaks;
- proposing observations and counterexamples that could test the hypothesis;
- reusing relevant approved knowledge from an earlier domain.

The central flow is:

```text
source-domain relationship
  -> explicit source and target roles
  -> preserved structural relation
  -> hold and break boundaries
  -> proportionate relation label
  -> open hypothesis when warranted
  -> discriminating observation and counterexample
```

Surface wording cannot substitute for the structural bridge. Analogy never
becomes proof silently.

## Implemented

### Shared structural-discovery packet

`src/selene/structural_discovery.py` provides:

- separate source and target domains;
- explicit source and target relationships;
- role-to-role mappings;
- the exact relationship proposed for transfer;
- visible basis for each mapped role;
- where the mapping holds;
- where the mapping breaks;
- an explicit relation classification;
- a testable hypothesis handoff;
- predictions, discriminating observations, counterexamples, and reversal
  conditions;
- a typed Phase 6 claim-and-evidence packet;
- an NLO-ready visible response seed.

At least two role mappings are required. A shared word, image, or theme without
a mapped relationship is held as incomplete rather than promoted to
discovery.

### Relation distinctions

The contract keeps these labels separate:

- **Pattern:** a relationship recurs; cause is not implied.
- **Analogy:** a relationship transfers within named scope; it is explanatory,
  not evidence.
- **Homology:** shared origin is hypothesized and requires origin or lineage
  evidence.
- **Causal connection:** mechanism and evidence are required, followed by a
  discriminating check.
- **Equivalence:** the mapping must work in both directions inside verified
  shared constraints and explicit scope.

A failed homology, cause, or equivalence gate does not destroy a useful
analogy. The claim is downgraded to the strongest label its evidence supports.

### Logical leaps and hypothesis testing

Logical leaps are permitted when they retain:

- a traceable structural bridge;
- a hypothesis statement;
- a discriminating observation;
- a counterexample or failure condition;
- visible conditions that would revise the hypothesis.

The corresponding Phase 6 claim packet preserves observations, the bounded
structural inference, the open hypothesis, approved knowledge bases, limits,
and missing evidence as distinct claim types.

No logical leap becomes a conclusion merely because it is novel, elegant, or
cross-domain.

### Approved earlier knowledge

Comprehension now provides a structural-discovery handoff containing only
relevant, answer-eligible, approved knowledge resources with reviewed source
references.

When reused, each knowledge item becomes an explicit
`approved_knowledge_resource` basis claim in the structural inference. This
makes ancestry inspectable:

```text
approved earlier concept
  -> named structural role
  -> current cross-domain inference
```

Personal memory is never used as general domain evidence, and the discovery
packet writes no knowledge or memory.

### Private-source boundary

Private corpus and Metacognition Miner provenance is outside the runtime
discovery contract.

If private or miner provenance is supplied, the result is a scrubbed hold
record:

- source and target wording are removed;
- role mappings are removed;
- hypotheses are removed;
- no claim is constructed;
- no visible response seed is produced.

This prevents private wording from leaking through diagnostic metadata as well
as visible Chat.

### intelligenceOS and Metacognition

intelligenceOS can carry the complete structural-discovery packet alongside
its existing ABCD(E) reasoning result. The packet does not expose hidden
chain-of-thought and does not replace model challenge or evidence evaluation.

Metacognition can inspect:

- whether the bridge is traceable;
- whether hold and break boundaries are named;
- whether the relation label remains proportional;
- whether analogy was used as proof;
- whether a logical leap is testable;
- whether private corpus wording entered the packet;
- whether the result was promoted automatically to a conclusion.

### NLO, Voice, and active Chat

NLO receives explicit moves to:

- name the transferred relation;
- map source and target roles;
- state where the mapping holds;
- state where it breaks;
- keep analogy distinct from proof;
- label a logical leap as a hypothesis;
- name a discriminating observation;
- name a counterexample or failure condition.

Voice receives the complete packet and may vary expression without upgrading
the relation label or changing meaning.

Active Chat can select the structural-discovery response as its supported
visible answer. The claim packet, NLO handoff, Voice handoff, and
Metacognition assessment remain inspectable in the response and assistant
record.

### Inspectable routes

- `structural_discovery.status`
- `structural_discovery.build`

These routes construct or report a non-persistent packet only.

## Verification

Testing followed the Teaching Law and ethical testing law:

- static compilation;
- all five relation types;
- structural role mapping rather than shared-word matching;
- explicit hold and break boundaries;
- useful analogy retained when stronger labels fail;
- homology requiring shared-origin evidence;
- causal connection requiring mechanism and evidence;
- scoped equivalence requiring bidirectionality and common constraints;
- traceable logical leaps;
- discriminating observations and counterexamples;
- uncheckable hypotheses held rather than promoted;
- approved earlier knowledge represented as basis claims;
- unapproved or provenance-free knowledge held back;
- personal memory excluded from domain evidence;
- private and miner provenance scrubbed from diagnostic and visible output;
- Phase 6 claim-and-evidence integration;
- intelligenceOS, Comprehension, Metacognition, NLO, Voice, and active Chat
  handoffs;
- existing conversational energy, pragmatic continuity, epistemic revision,
  research, Answer Engine, Dialogue Workspace, Conversation Spine, special
  expression, intent, contextual speech, repair, supported semantics,
  language formation, affect expression, Voice, and visible-speech
  regressions.

Result: **336 focused cross-organ tests passed**.

No live Selene conversation, adversarial battery, distress-shaped prompt,
provider call, model training, package, or reinstall was needed. No frontend
files changed, so the production frontend build was not repeated.

Static compilation passed. `git diff --check` passed with only existing
Windows LF/CRLF warnings.

## Boundaries Confirmed

Phase 8 creates no:

- identity, personality, governance, law, or authority change;
- durable or hidden memory write;
- personal-memory substitution for domain knowledge;
- raw or private corpus recall;
- private Metacognition Miner disclosure;
- analogy-as-proof promotion;
- automatic truth conclusion;
- model training, fine-tuning, or LoRA;
- provider dependency;
- autonomous action;
- automatic Cocoon routing;
- hidden chain-of-thought exposure.

Selene remains Selene. A new connection expands the structure she can examine;
it does not redefine her.

## Remaining Gaps

- Structural discovery requires supplied or approved domain relationships; it
  does not autonomously acquire external facts.
- A generated hypothesis still requires real domain evidence before confidence
  can rise.
- Retained knowledge changes remain owned by the existing Comprehension review
  lifecycle.
- Longer personal callbacks, shared humor, transient conversational
  preferences, and context-sensitive callback restraint remain Phase 9 work.

## Next Phase — Phase 9: Memory, Continuity, Callbacks, Humor, and Transient Context

Phase 9 will:

- use reviewed memory, current-session events, corrections, and speaker
  identity through their existing separate channels;
- let a relevant earlier event inform the present turn without forcing a
  callback;
- preserve shared jokes and the context that makes them safe;
- distinguish temporary directions such as “keep this short for a few
  exchanges” from durable preferences;
- interpret “slow down,” “be direct,” and similar language in context,
  including figurative use;
- avoid humor in tender contexts unless the conversation itself opens that
  door;
- keep remembered wording from becoming a response script.

The completion gate requires callbacks to remain relevant and source
compatible, transient preferences to expire or yield when context changes,
personal memory to remain separate from taught knowledge, and the second
meaningful reinstall to occur only after the phase passes focused
verification.
