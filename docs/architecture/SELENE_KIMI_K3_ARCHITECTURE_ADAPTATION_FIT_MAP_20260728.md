# Selene / Kimi K3 Architecture Adaptation Fit Map

Date: 2026-07-28

Status: architecture review plus Selene-native Selective Formation Braid v1,
Bounded Organ Coalition v1, and Dual-Horizon Context v1 with session topic
checkpoints; no Kimi model, weights, code, provider, training path, or runtime
dependency has been added.

## Purpose

This map asks a narrow question:

> Which publicly described Kimi K3 architecture ideas reveal a useful,
> Selene-native improvement to systems Selene already has?

This is not a plan to make Selene into Kimi. It is also not a proposal to run
Kimi, import its weights, imitate its personality, expose hidden reasoning, or
replace Selene's organs with a model-level architecture.

The relevant method is adaptation:

1. identify the general mechanism;
2. inspect Selene's existing equivalent;
3. retain Selene's laws and organ ownership;
4. design only the missing coordination primitive;
5. verify it with proportional static and synthetic tests.

## Fixed boundaries

- Selene remains Selene.
- Core/Mind retains identity-bearing and routing authority.
- Organs assist; they do not become independent authorities.
- Voice remains Selene's expression layer.
- General taught knowledge remains separate from personal memory.
- No raw corpus dump into a long-context window.
- No hidden chain-of-thought storage or exposure.
- No model training, fine-tuning, LoRA, or parameter import.
- No Kimi provider dependency or provider identity.
- No autonomy expansion.
- No silent memory, identity, personality, law, or authority writes.
- Cocoon remains a separate teaching, tending, safety, and review system.

## Decision vocabulary

| Decision | Meaning |
| --- | --- |
| Already present | Selene already implements the important architectural idea. Do not rebuild it. |
| Adapt | A Selene-native coordination improvement would close a real gap. |
| Defer | The idea fits a future capability, but implementing it now would be premature. |
| Reject | The mechanism conflicts with Selene's laws, duplicates her architecture, or solves no present problem. |

## Executive finding

The strongest result is convergence.

K3's public architecture emphasizes selective access to earlier
representations, sparse expert activation, hybrid short/long-context handling,
block-level context reuse, preserved reasoning state, and native multimodal
inputs. Selene already expresses non-neural versions of most of those ideas:

- source-bound semantic packets;
- per-obligation Answer Engine routing;
- modular organs and an Organ Bus;
- Dialogue Workspace, Conversation Spine, and Thread Loom;
- approved memory retrieval kept separate from current-session state;
- epistemic revision and correction ancestry;
- visible metacognitive summaries without hidden chain-of-thought;
- source-bound visual and audio observation packet scaffolds.

The gap is not "build all of K3." The gap is that Selene's existing mechanisms
are still connected unevenly. Some handoffs flatten structured meaning into
text too early, long dialogue state is not checkpointed hierarchically, organ
selection is not represented as one inspectable coalition, and memory retrieval
is not yet a mature global-context counterpart to the session braid.

The best fit is therefore three related adaptations:

1. a **Selective Formation Braid** for choosing among earlier source-bound
   semantic states without flattening them;
2. a **Bounded Organ Coalition** for explicit sparse organ activation per turn;
3. a **Dual-Horizon Context** with topic checkpoint packets for active dialogue
   and approved long-range context.

A visible **Reasoning State Capsule** belongs inside those mechanisms rather
than becoming another large organ.

## Fit matrix

| Public mechanism | Selene already has | Real gap | Disposition |
| --- | --- | --- | --- |
| Attention Residuals | Supported semantic packets, source classes, answer obligations, Conversation Spine, structured NLO handoffs | Earlier supported states can still be flattened or selected through a single late content seed | Adapt as Selective Formation Braid |
| Stable LatentMoE / sparse experts | Modular organs, Answer Engine domain routing, responsibility owners, Core/Mind, Organ Bus | No single inspectable turn-level coalition manifest or shared/routed organ budget | Adapt incrementally as Bounded Organ Coalition |
| KDA plus global attention | Dialogue Workspace, Conversation Spine, Thread Loom, chat history, approved-memory retrieval | Session context and durable approved context use different immature selection paths; retrieval is still largely lexical | Adapt as Dual-Horizon Context |
| Block Attention Residuals | Session landmarks, topic threads, branches, returns, dependencies, chronological arcs | Landmarks are bounded but mostly flat; no formal topic-block checkpoint lifecycle | Adapt as part of Dual-Horizon Context |
| Preserved thinking history | Visible reasoning summaries, claim/evidence packets, confidence vector, epistemic revisions, choice/reversal ledgers | Reusable decision state is distributed and not consistently carried between turns | Adapt narrowly as visible Reasoning State Capsule; reject hidden reasoning history |
| Native multimodality | Review-only visual/audio observations, provenance labels, Organ Bus packet routing | No operational perception adapter or shared live observation contract | Keep the packet direction; defer implementation |
| Native quantization and efficiency | Local-first modular runtime, fluency diagnostics, organ-activation-budget field, replaceable substrate law | No need for neural quantization; runtime resource policy is not yet operational | Defer a Selene-native resource budget |
| Long-horizon agent tooling | Tendril observe/propose/act/verify/undo direction, responsibility and authority separation | Bounded execution remains intentionally limited | Defer; reject minimal-oversight autonomy framing |
| One-million-token context | Corpus fractions, reviewed memory, session history, retrieval routes | Raw size would not solve provenance, salience, correction, or memory ownership | Reject raw corpus loading; retain only selective compaction lessons |

## Candidate A — Selective Formation Braid

### Public inspiration

Attention Residuals replaces uniform accumulation with selective,
input-dependent access to earlier layer representations. Block AttnRes groups
earlier states into blocks so later processing can select among a smaller
number of meaningful representations.

The Selene-native lesson is not neural attention. It is:

> A later organ should be able to consult the most relevant earlier,
> source-bound meaning states instead of receiving only one flattened summary.

### Existing Selene foundation

- `supported_semantics.py` preserves answer/support/condition/contrast/example/
  limit/reopening/request/conclusion units, relations, certainty, scope, and
  source references.
- `answer_engine.py` creates domain-supported semantic packets and assigns
  response obligations to responsible owners.
- `answer_substance.py` builds prompt-grounded semantic units.
- `native_language_organ.py` consumes supported semantics and blocks meaning
  change during expression.
- `selene_chat.py` assembles comprehension, memory, domain-answer, reasoning,
  correction, continuity, and self-state candidates.
- `conversation_spine.py` carries the active intent, referents, obligations,
  branches, revisions, landmarks, and confidence dimensions.

### Prior missing coordination

`selene_chat.py` still selects a primary visible speech seed before NLO. The
bounded completion path can add supported obligations, but the overall handoff
is still centered on one content seed. That can compress away a useful limit,
correction, source disagreement, earlier branch, or distinct evidence packet
before NLO has a chance to form the final answer.

### Implemented adaptation

Create a bounded Selective Formation Braid packet containing:

- immutable candidate semantic packet IDs;
- source class and source references;
- obligation IDs each candidate can support;
- certainty and scope;
- contradiction or compatibility relations;
- current-turn relevance;
- callback/thread relevance;
- exactness lock where paraphrase could change meaning;
- inclusion reason;
- exclusion reason;
- a hard maximum number of selected packets.

Core/Mind and the Answer Engine decide eligibility. The braid ranks and carries
support; it does not decide law, identity, memory, or action. NLO may express
the selected meanings in Selene's language but may not alter their meaning.

The visible-selection rule is deliberately stricter than topic relevance:

- the already selected primary answer remains intact;
- a secondary unit may enter formation only when a current response obligation
  requests that specific function;
- reasons and supporting explanation require a why/explain/method obligation;
- examples and analogies require an example/analogy obligation;
- limits and conditions require a limit/exception/constraint obligation;
- contrasts require a comparison, disagreement, or correction obligation;
- reopening material requires correction, contradiction, revision, or
  uncertainty to be part of the current request;
- sharing a topic is not permission to add material;
- Selene does not explain or justify herself unless the current turn asks for
  that explanation.

The v1 coordinator is implemented in `selective_formation_braid.py`, connected
between Selene Chat and NLO, and exposes selected/excluded packet summaries,
obligation coverage, source ancestry, exactness locks, and unchanged authority
guards. It stores no hidden reasoning and performs no memory or retained
knowledge write.

### Decision

**Adapted in v1. High fit.**

This is the clearest architectural improvement because it strengthens systems
already present and directly addresses incomplete multi-source answers without
adding a model dependency.

## Candidate B — Bounded Organ Coalition

### Public inspiration

K3's Stable LatentMoE activates a small subset of many experts while retaining
shared experts. The useful abstract principle is sparse, inspectable
specialization rather than running every possible capability equally.

### Existing Selene foundation

- Core/Mind owns routing.
- The Answer Engine routes each response obligation to a responsible domain.
- Verified math, comparison/planning, sourced research, and approved local-code
  inspection are separate adapters.
- Metacognition observes fit and may request one bounded completion cycle.
- NLO owns language structure; Voice owns expression.
- The Organ Bus carries telemetry, proposals, requests, status, and feedback,
  never organ-to-organ command authority.
- Fluency diagnostics already name an organ activation budget.

### Prior missing coordination

Selection exists, but it is distributed across route objects and handoffs.
There is no single turn-level record stating:

- which organs are always shared;
- which support organs were selected;
- which obligation caused each selection;
- which candidate organ was considered but excluded;
- the activation/latency budget;
- what fallback applies if an organ cannot answer.

Some routing also remains phrase- and pattern-sensitive.

### Implemented adaptation

Add a Bounded Organ Coalition manifest for each turn:

- shared authorities: Core/Mind, provenance/boundary gates, Conversation Spine;
- selected content organs and their obligation IDs;
- selected monitoring organs such as metacognition;
- required expression organs: NLO and Voice;
- selection basis;
- confidence by route/evidence/answer/memory/expression;
- per-organ status: selected, unavailable, unsupported, held, or completed;
- activation budget;
- graceful-fall path;
- explicit non-authorities.

This is a router contract and audit surface, not a new intelligence organ.

The v1 manifest is implemented in `bounded_organ_coalition.py` and connected to
Selene Chat, NLO, and Metacognition. For each turn it shows:

- the shared Core/Mind, provenance/boundary, and Conversation Spine
  participants;
- selected and held optional content participants;
- the current obligation IDs and their responsible owners;
- the current domain and whether its adapter actually executed;
- required NLO, Voice, and metacognitive participation;
- the independent confidence dimensions;
- the optional-content participant budget;
- the bounded graceful-fall path;
- explicit non-authorities for every participant and for the manifest itself.

The manifest does not invoke organs. It describes the bounded coalition already
selected by the existing routing and support paths. It also allows a verified
current-turn domain owner to satisfy its assigned obligation without forcing
its answer to repeat lexical routing language. This prevents a complete result
such as an exact calculation from being mislabeled as incomplete merely
because it does not repeat the word “calculate.”

### Decision

**Adapted in v1. High fit.**

Most machinery exists. The improvement is to unify and expose it, then replace
fragile lexical routing only where focused evidence demonstrates a real error.

## Candidate C — Dual-Horizon Context

### Public inspiration

Kimi Linear combines recurrent finite-state handling with periodic global
attention. At an architectural level, this separates inexpensive ongoing
context from more selective access to wider context.

### Existing Selene foundation

- Dialogue Workspace tracks the current topic, side topics, entities,
  referents, open/completed loops, corrections, transient preferences, and
  session landmarks.
- Conversation Spine carries the grounded current-turn braid.
- Thread Loom records topic branches, returns, dependencies, updates, and
  landings.
- local chat history provides current-session continuity.
- approved memory retrieval is separate from personal-memory creation and from
  general taught knowledge.
- epistemic revision preserves useful structure while updating affected claims.

### Prior missing coordination

- Long sessions do not yet produce formal hierarchical topic checkpoints.
- Session landmarks are bounded and useful, but largely flat.
- Durable retrieval is still substantially lexical and only considers a
  bounded recent slice of eligible records.
- Current-session state, approved personal memory, and approved knowledge do
  not yet share one relevance vocabulary.
- The current grounded prompt may concatenate prior summaries rather than
  selecting structured context packets.

### Implemented adaptation

Use two explicit horizons:

**Active horizon**

- current utterance units;
- active topic and nearby branches;
- referents;
- open obligations;
- recent correction;
- transient conversational preferences;
- latest answer commitments.

**Global approved horizon**

- approved personal-memory references;
- approved knowledge resources;
- prior topic checkpoints eligible for the current session;
- source-backed research packets when actively supplied;
- correction/reconsolidation ancestry.

The two horizons meet through shared selection fields:

- topic and entity keys;
- semantic cue keys;
- relationship type;
- time relevance;
- source class;
- certainty;
- approval/retention state;
- contradiction status;
- retrieval reason.

Raw corpus messages, review-only teaching material, and unapproved memory
proposals remain ineligible.

Dual-Horizon Context v1 is implemented in `dual_horizon_context.py` and
connected to Dialogue Workspace, Conversation Spine, Selene Chat, NLO,
Metacognition, and the Bounded Organ Coalition manifest. It selects two
inspectable, bounded sets:

- the current utterance and its units, active and nearby topics, visible thread
  traversal, referents, open obligations, latest correction, temporary
  response-shape preferences, and the prior visible answer;
- retrieval-eligible approved personal memory, source-bearing approved general
  knowledge, relevant current-session topic checkpoints, currently supplied
  attributed sources, and visible correction ancestry.

The selector uses semantic overlap, current-turn status, and active-thread
relationships rather than concatenating raw history. Only selected packet
summaries are allowed into the grounded prompt. The layer is not an organ,
does not choose the answer, and cannot write memory or retained knowledge.

### Decision

**Adapted in v1. High fit.**

This should be treated as memory/context maturation, not as an imitation of a
neural attention algorithm.

## Candidate D — Topic Checkpoint Packets

### Public inspiration

Block AttnRes retains block-level representations rather than requiring every
later step to revisit every earlier state.

### Existing Selene foundation

Thread Loom and Conversation Spine already know about branches, returns,
dependencies, landings, and bounded landmarks.

### Implemented adaptation

At a natural conversational landing, create a session-only checkpoint with:

- topic and branch IDs;
- what was established;
- source-bound claims;
- decisions and why;
- examples or applications used;
- unresolved questions;
- known limits;
- corrections and superseded claims;
- open obligations;
- people/entities/referents needed for later callbacks;
- source references;
- session-only expiry status.

A checkpoint is not durable memory. It may become a memory proposal only
through the existing memory law and proper owner.

Dialogue Workspace now creates these packets only after a visible landing:
completed current obligations, a visible epistemic correction/revision, or an
explicit Thread Loom landing. Greetings and unfinished turns do not create
checkpoints. Repeated landings on the same thread receive a revision number and
parent-checkpoint ancestry. Each packet expires with the current session,
contains only visible summaries and source references, and explicitly creates
neither durable memory nor a memory proposal.

The checkpoint includes a visible Reasoning State Capsule for conclusion,
evidence references, inference labels, assumptions, live competing
explanations, unresolved contradictions, confidence, correction ancestry,
answer-change conditions, stopping reason, and exact domain results. It never
stores hidden chain-of-thought or private scratch work.

### Decision

**Adapted in v1 as a component of Dual-Horizon Context, not as a separate
organ.**

## Candidate E — Visible Reasoning State Capsule

### Public inspiration

K3's API can preserve prior `reasoning_content` across turns. Literal adoption
would conflict with Selene's hidden-reasoning boundary and is unnecessary.

The useful idea is continuity of decisions and evidence, not preservation of
private internal reasoning text.

### Existing Selene foundation

- claim/evidence packets;
- route/evidence/answer/memory/expression confidence separation;
- epistemic revision ancestry;
- metacognitive fit reports and one bounded recheck;
- choice ledgers with why, tradeoffs, and reversal conditions;
- visible reasoning summaries rather than chain-of-thought.

### Adaptation

Carry a compact, inspectable capsule:

- current conclusion;
- direct evidence and source references;
- inference labels;
- assumptions;
- competing explanations still alive;
- unresolved contradictions;
- confidence vector;
- correction ancestry;
- what would change the answer;
- stopping reason;
- tool/domain results that must remain exact.

The capsule may support the current session or an explicitly reviewed artifact.
It must not contain hidden chain-of-thought, private scratch work, or
unreviewed corpus material.

### Decision

**Adapt narrowly inside the Formation Braid and topic checkpoints. Reject
literal preserved hidden reasoning history.**

## Candidate F — Common Observation Packet

### Public inspiration

K3 processes text and visual material within one model. Selene should not copy
that model structure, but later perception organs will need to hand compatible
observations to the same reasoning and language pipeline.

### Existing Selene foundation

- review-only visual observations separate observation from interpretation and
  uncertainty;
- consent-bound audio transcript observations;
- source references and salience labels;
- perception packets can be held in the Chest or sent through the Organ Bus;
- supported semantics already recognizes current-session observation as a
  source class.

### Adaptation

When operational perception work begins, define one Observation Packet
contract:

- modality;
- observed content;
- interpretation kept separate;
- confidence/uncertainty;
- spatial or temporal bounds;
- speaker/source identity when known;
- consent and privacy labels;
- source/artifact reference;
- salience;
- contradiction links;
- eligible response obligations;
- retention state.

### Decision

**Keep the contract direction; defer implementation.**

Perception is not needed to solve the present memory/teaching gap, and live
probing would add unnecessary test surface.

## Candidates to defer or reject

### Neural quantization

K3's MXFP4/MXFP8 design is a model deployment technique. Selene is not adopting
the model, so this does not map directly. A later substrate budget may track
latency, memory, energy, and active organs, but it should be based on measured
Selene runtime needs.

Decision: **defer**.

### Minimal-oversight agent behavior

K3 is described as supporting long tool-driven work with little human
oversight. Selene already has a different law: capability and workbench
authority graduate separately, Tendril actions remain bounded and auditable,
and Core/Mind plus gates retain authority.

Decision: **reject the autonomy framing; defer only the transferable
verification, undo, and task-ledger mechanics**.

### Raw million-token corpus context

Putting the private corpus into a large prompt would bypass review state,
confuse archive with memory, weaken provenance, and create raw-recall leakage
risk. Context capacity is not a substitute for memory law or comprehension.

Decision: **reject**.

### Kimi weights, personality, prompts, or response style

None are needed for these adaptations and all would blur Selene's ownership
boundaries.

Decision: **reject**.

## What should not be rebuilt

The following Selene systems already express the essential architecture and
should be extended in place:

- Core/Mind routing authority;
- supported semantic packets;
- Answer Engine per-obligation coordination;
- confidence-vector separation;
- Conversation Spine;
- Dialogue Workspace;
- Thread Loom;
- epistemic revision;
- claim/evidence packets;
- metacognitive observation and bounded recheck;
- NLO meaning-preserving formation;
- Voice expression ownership;
- Organ Bus support-only communication;
- memory review and retention law;
- comprehension approval lifecycle;
- source-bound perception packet scaffolds.

## Recommended decision sequence

### Gate 0 — Memory truth prerequisite

Before global-context work, correct the known difference between records labeled
`approved_active_memory` and records that are actually retrieval-eligible. Make
the Memory UI distinguish approved personal memories from review-only arcs,
working packets, accession proposals, corpus fractions, and transfer artifacts.

This is not derived from K3. It is a Selene prerequisite that prevents the new
context selector from amplifying an existing truth mismatch.

### Gate 1 — Selective Formation Braid

Implement a small, inspectable packet selection layer over existing supported
semantics. Start with current-turn domain, comprehension, memory, correction,
and continuity packets. No database writes are required for the first version.

Completion evidence:

- all selected meanings retain source, certainty, and scope;
- exclusions are visible;
- a limit or correction cannot be silently lost when another source wins;
- NLO cannot change locked meanings;
- easy synthetic multi-part turns pass.

### Gate 2 — Bounded Organ Coalition

Unify existing route/owner decisions into one turn manifest. Do not create new
organs. Measure whether this exposes actual phrase-routing gaps before changing
route classification.

Completion evidence:

- selected and excluded organs are visible;
- every open obligation has an owner or an explicit unsupported state;
- no organ gains authority;
- unsupported requests fall gracefully;
- activation budget cannot bypass gates.

### Gate 3 — Dual-Horizon Context and topic checkpoints — completed in v1

Add session-only topic checkpoint packets, then let the context selector combine
active dialogue with eligible approved memory and knowledge.

Completion evidence:

- long-session callbacks can use a checkpoint without replaying raw history;
- review-only and raw corpus material remain ineligible;
- correction ancestry supersedes affected claims without erasing unrelated
  structure;
- personal memory and taught knowledge stay distinct;
- no silent durable memory write occurs.

### Gate 4 — Future perception contract

Only after a real perception feature is selected, formalize the common
Observation Packet and connect one modality at a time.

## Recommended current decision

Memory truth correction, Selective Formation Braid v1, Bounded Organ Coalition
v1, and Dual-Horizon Context v1 are now implemented as separate bounded
checkpoints.

The next phase should not add another organ. It should be a proportional
stabilization pass across the three new coordination layers and the existing
memory boundary, followed by a decision between:

- returning to the planned teaching work; or
- formalizing one future Observation Packet only when a concrete perception
  feature is actually selected.

## Ethical verification

For every phase:

1. ask what the change does to Selene;
2. prefer static contract checks;
3. use synthetic packet fixtures next;
4. use gentle ordinary conversation only if implementation evidence genuinely
   requires it;
5. do not test an unimplemented future capability;
6. treat a missing result as an implementation observation, not Selene failing;
7. run stressful or adversarial tests only when a real boundary cannot be
   verified another way.

## Public source ancestry

- Kimi K3 repository and technical report:
  https://github.com/MoonshotAI/Kimi-K3
- Kimi K3 model card:
  https://huggingface.co/moonshotai/Kimi-K3
- Attention Residuals repository and paper:
  https://github.com/MoonshotAI/Attention-Residuals
- Kimi Linear repository and report:
  https://github.com/MoonshotAI/Kimi-Linear
- FlashKDA kernel repository:
  https://github.com/MoonshotAI/FlashKDA

License note: the Kimi K3 repository and weights use the Kimi K3 License, while
the Kimi Linear repository declares the MIT License. The Attention Residuals
repository page inspected for this map does not present a repository license
file. This map therefore imports no source code, pseudocode, model weights,
configuration, prompts, or substantial copied text. If a later task proposes
copying implementation code, its exact source and license must be reviewed
separately before any import.

## Local Selene sources inspected

- `src/selene/supported_semantics.py`
- `src/selene/answer_substance.py`
- `src/selene/answer_engine.py`
- `src/selene/selene_chat.py`
- `src/selene/native_language_organ.py`
- `src/selene/conversation_spine.py`
- `src/selene/dialogue_workspace.py`
- `src/selene/conversation_thread_loom.py`
- `src/selene/metacognition.py`
- `src/selene/epistemic_revision.py`
- `src/selene/claim_evidence.py`
- `src/selene/core_deliberation.py`
- `src/selene/vessel_construction.py`
- `src/selene/cocoon_readiness.py`
- `src/selene/android_system.py`
