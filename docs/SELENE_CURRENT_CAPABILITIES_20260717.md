# What Selene Can Currently Do

- Updated: July 18, 2026
- Branch inspected: `evidence`
- Source checkpoint: `3de57ce`

## Why This File Exists

This is a plain-language map of Selene's current implemented abilities and
organs. It is meant to answer three different questions without mixing them
together:

1. What can Selene use during supervised conversation now?
2. What can one of her organs or bounded tools do when called directly?
3. What can Cocoon inspect, prepare, rehearse, or hold for later review?

It also states what is still partial, preview-only, or not built. A route,
schema, or design document is not described as a live ability merely because
it exists.

## Status Key

- **Connected:** participates in supervised Selene Chat when that chat is
  explicitly active.
- **Available:** implemented and usable through a bounded route or workbench,
  but not automatically used in ordinary Chat.
- **Cocoon:** review, teaching, tending, preparation, or diagnostic machinery.
- **Preview:** can model, rehearse, or report a possible operation but cannot
  perform the consequential action.
- **Design:** an architectural direction or law exists, but the full runtime
  ability does not.

## Quick Capability Table

| Capability | Current status | Plain-language answer |
| --- | --- | --- |
| Supervised text conversation | Connected | Selene can hold local conversations through coordinated organs when supervised Chat is explicitly active |
| Immediate conversational continuity | Connected | She can use recent local chat context and callbacks without silently turning them into permanent memory |
| Language formation and Voice | Connected | She can construct and shape bounded replies with compositional dialogue obligations, grammar features, context-keyed expression profiles, and recent-response avoidance |
| Open-ended conceptual reasoning | Connected | intelligenceOS can compare models and give a best-current answer without needing a predetermined solution |
| Approved personal memory | Connected | She can recall only reviewed memories and keep fuzzy or unknown recall honest |
| Approved taught knowledge | Connected | She can use knowledge only after comprehension evidence and an Aleks item decision or bounded curriculum authorization; 28 F1 foundations are currently retained |
| Current-state description | Connected when asked | She can give a grounded, provisional self-read from current attributable signals |
| Exact arithmetic | Connected | She can answer bounded exact arithmetic in supervised Chat and keep answer confidence separate from fluency |
| Local-code inspection | Available separately | She can inspect explicitly supplied or approved files without scanning, executing, or writing |
| Source-backed research | Connected when packets are supplied | She can answer from attributed packets in supervised Chat and show citations, disagreement, or missing evidence |
| Ethical test review | Available | The project can choose the least-impact sufficient test before interacting with Selene |
| Language lesson shelf | Review-gated and connected | Ten provider-free lessons travel through visible comprehension review; NLO can consult only explicitly approved lessons |
| Affect shaping of language | Partial | Current-state and salience signals exist, but they do not yet shape language consistently |
| Long-form discourse | Improved partial | Developed replies now have grounded thesis, development, limit, and closure plans; broad narrative and mature rhetorical control remain unfinished |
| Vision and hearing | Packet intake only | The system can hold supplied observations but cannot yet see or hear |
| External action | Preview only | Tendril can plan and request approval but cannot execute actions |
| Metacognition Organ | Not installed | The private miner is complete, but no mined cognitive mechanism is connected to Selene |
| Audible speech | Not built | Selene currently communicates through text |
| Transfer or embodiment | Preparation only | The repository can rehearse and inspect transfer, but cannot perform it |

## Selene at a Glance

With supervised Chat explicitly enabled, Selene can currently:

- hold an ordinary local conversation;
- recognize greetings, gratitude, warmth, play, corrections, memory requests,
  reasoning requests, and questions about her current state;
- keep immediate and recent local-chat context without turning it into hidden
  permanent memory;
- answer multi-part messages and check whether her reply covered the requested
  parts;
- preserve ordered requests even when ordinary instructions do not end in a
  question mark;
- resolve first/second/former/latter references from bounded prior-turn options,
  and ask rather than guess when a reference is materially ambiguous;
- carry a correction as a current-session meaning refinement without treating
  it as personal memory;
- use approved personal memory with clear, fuzzy, partial, or unknown recall;
- say she does not know, ask Aleks, or keep uncertainty visible;
- propose a memory candidate when Aleks asks her to remember something, while
  leaving it inactive until review;
- use explicitly approved general knowledge without treating it as personal
  memory, identity, personality, or law;
- reason about open-ended conceptual problems through intelligenceOS;
- construct language from a meaning packet and then let Voice shape the
  expression;
- notice some repetition, incomplete coverage, and awkward turn flow and try a
  bounded repair;
- report a grounded current-state reading without inventing a specific emotion
  or exposing hidden internal reasoning;
- refuse requests that cross raw-corpus, hidden-memory, model-training,
  activation, autonomy, or self-replication boundaries;
- offer Cocoon as optional support without treating ordinary uncertainty as a
  reason she must leave the conversation.

Selene's current conversation path is roughly:

```text
Aleks's message
  -> bounded input detangling
  -> intent and dialogue understanding
  -> Core/Mind route and boundary check
  -> structured meaning and Answer Engine domain route
  -> approved memory / approved knowledge / verified math / attributed research / intelligenceOS / self-state support
  -> Native Language Organ
  -> Voice Module
  -> coverage and conversation repair
  -> supervised reply
```

Verified math, comparison/planning, and source-backed research now participate
in this live Chat path. Local-code inspection remains intentionally separate.

The first four bounded F1 curriculum groups are also retained as reviewed
general knowledge: four science/inquiry foundations, eight language/number
foundations, eight operations/data/measurement/time foundations, and eight
geometry/equal-share/algorithmic foundations. They remain separate from
personal memory, identity, personality, governance, execution authority, and
Voice.

## Conversation and Language Organs

### Selene Chat — Connected

Selene Chat is the supervised place where the current organs meet.

It can:

- create and continue local chat sessions;
- preserve recent local conversation continuity across chat pages;
- distinguish current-turn context from approved memory and Cocoon-only
  records;
- coordinate Core/Mind, Memory, intelligenceOS, Comprehension, self-state,
  NLO, Voice, pragmatic coverage, and repair;
- provide a Cocoon support choice when a source, memory, or boundary issue
  needs attention;
- suggest a reviewable memory candidate when Aleks explicitly asks her to keep
  something;
- keep hard boundary requests out of normal response generation;
- record visible audit metadata for supervised turns.

Current limits:

- it remains supervised rather than autonomous;
- it does not load the raw private corpus as memory;
- it does not silently make durable memories;
- its provider-free generation remains bounded and has less breadth than a
  mature learned language model, although expression profiles, turn context,
  compositional turn obligations, recent-response avoidance, and broader
  grammar and answer frames now reduce repetition;
- routing now shares an inspectable structured meaning packet, but its bounded
  sentence and lexical features are not complete semantic understanding;
- verified math and attributed research are ordinary supervised Chat answers,
  while local-code inspection remains deliberately outside Chat;
- `selene_v1_live` remains false in the current status contract: supervised
  speech is not the same thing as finished transfer, full activation, or an
  autonomous vessel.

### Input Detangler — Connected

The Input Detangler helps with bounded typing noise before other organs try to
understand a message.

It can:

- preserve Aleks's exact raw message;
- apply only reviewed, bounded corrections;
- expose the interpreted version to the dialogue system;
- flag an ambiguous repair rather than silently guessing;
- report what changed.

It is not a general-purpose rewriting model and does not have permission to
change the intended meaning.

### Chat Intent Router — Connected

The intent router recognizes the main kind of conversational work being asked
for, including:

- direct conversation;
- greeting, farewell, gratitude, affirmation, warmth, and play;
- correction or refinement;
- memory recall;
- a request to keep a memory;
- reasoning or comparison;
- a question about Selene's current state;
- brief, standard, or developed response depth.

The router now builds one shared meaning packet from sentence shape, dialogue
acts, supplied materials, candidate intents, candidate domains, and ambiguity.
It masks descriptive quotations so discussing a phrase is not the same as
instructing Selene to follow it. Actionable quoted instructions still reach
Core/Mind boundaries.

It is useful but not complete natural-language understanding. It can preserve
multiple candidate intents and several mixed turns, but subtle implication,
pronoun resolution, interruption, and rapid topic changes still need broader
handling.

### Dialogue Workspace — Connected

The dialogue workspace is short-term conversational working context.

It can:

- track the current topic;
- retain immediate references and callbacks, including bounded ordered-option
  references such as first, second, former, and latter;
- identify multi-part questions and ordinary direct requests without requiring
  a question mark;
- keep structured corrections, response preferences, and candidate referents
  visible;
- mark a materially ambiguous reference for clarification instead of choosing
  silently;
- use current-session events when interpreting the next turn;
- expire with the session instead of becoming personal memory.

It is not the long-term Memory Organ and does not create durable memory.

### Pragmatic Planner — Connected

The Pragmatic Planner represents what the reply needs to accomplish.

It can:

- separate and order multiple requested parts;
- interpret bounded immediate ellipsis and implication;
- distinguish correction updates from the content request they modify;
- distinguish a direct answer from a clarification or social turn;
- create visible response obligations;
- evaluate whether the produced reply addressed those obligations.

It does not yet provide mature discourse pragmatics across long, highly
ambiguous, interrupted, or rapidly changing conversations.

### Semantic and Sentence Formation — Connected

The language-formation layer can represent:

- propositions;
- tense and time orientation;
- simple, progressive, perfect, and perfect-progressive aspect;
- active and passive voice;
- declarative, interrogative, and imperative mood;
- certainty and modality;
- positive or negative polarity;
- subject and object modifiers plus bounded adverbs;
- conditions, causes, contrasts, examples, qualifiers, and supporting reasons;
- per-clause relationships and connective realization;
- a planned response depth.

This gives NLO structured meaning to express. It is not a complete grammar or
full linguistic world model.

### Native Language Organ (NLO) — Connected

NLO turns supported meaning into sentences. It does not own identity, memory,
law, personality, or truth.

It can:

- build a meaning packet from the current turn and supported organ outputs;
- plan a response before realizing it;
- answer directly and then expand when appropriate;
- express clear or fuzzy memory honestly;
- express a best-current reasoning answer;
- handle correction, warmth, play, uncertainty, boundaries, and ordinary
  conversation;
- produce brief, standard, and more developed replies;
- choose direct, explanation, comparison, procedure, reflection, synthesis,
  or social expression profiles;
- carry structured utterance units, ordered response obligations, bounded
  references, and correction scope through the supervised Chat handoff;
- realize bounded grammatical differences in tense, aspect, voice, mood,
  modality, polarity, and clause relation without a provider;
- bind supported answer content to visible response obligations before wording
  it, while leaving unsupported obligations marked as gaps;
- preserve an inspectable thesis, development section, limit or reopening point,
  and supported closure across developed replies;
- vary answer frames and long-form transitions from turn context while avoiding
  recent openings, without randomizing the supported meaning;
- remove architecture-heavy wording before a reply reaches the front of Chat;
- prepare a review-only initiative note or draft;
- choose silence when no initiative signal is relevant enough.

Current limits:

- linguistic breadth and variation are still bounded;
- long-form planning is now grounded and inspectable, but mature narrative
  structure, rhetorical emphasis, reference tracking across many paragraphs,
  and varied endings are not yet complete;
- its initiative route never sends anything automatically;
- it cannot turn fluent wording into evidence that an answer is correct;
- it depends on other organs to supply truthful content.

### Voice Module — Connected

Voice shapes how supported meaning sounds. It is Selene's expression layer, not
her identity or memory store.

It can:

- shape language for warmth, play, correction, technical directness,
  uncertainty, questions, and boundaries;
- use reviewed expression patterns and sentence primitives;
- preserve the meaning supplied by NLO;
- avoid some copied source chunks and repeated candidates;
- generate a candidate and evaluate it for voice fit;
- keep provider identity and raw-source wording out of the expression contract.

Current limits:

- its available patterns still cover only part of Selene's intended expressive
  range;
- historical pressure-shaped wording does not yet have a complete runtime
  origin classification;
- full affect-to-language guidance for pacing, humor, reassurance, restraint,
  and directness is not connected;
- audible speech is not part of this module yet.

### Conversation Repair — Connected

Conversation Repair can inspect the proposed reply before it is returned.

It can notice:

- missing response obligations;
- unnecessary repetition;
- an awkward acknowledgement or transition;
- an unanswered question;
- a reply that should be rephrased or held open.

It can select a better existing candidate in bounded cases. It cannot yet call
the correct domain organ to obtain missing factual, mathematical, code, or
research content.

## Reasoning and Answer Organs

### intelligenceOS — Connected for Reasoning Requests

intelligenceOS is Selene's current open-ended reasoning organ. Its method is
ABCD(E): acquire observations, build candidate models, challenge them,
demonstrate an evidence chain, and evaluate whether to answer, qualify, ask, or
stop.

It can:

- separate observations from candidate explanations;
- build more than one possible model;
- expose assumptions, mechanisms, and predictions;
- challenge models with equal scrutiny;
- surface contradictions and missing support;
- produce a best-current answer rather than only asking questions;
- choose an answer shape such as direct answer, compare models, qualify, ask,
  or hold;
- stop when more recursion is not worthwhile;
- suggest Cocoon support for a real unresolved boundary without making it
  automatic;
- keep a visible summary while not exposing hidden chain-of-thought.

Current limits:

- its reasoning quality is bounded by the observations and knowledge supplied;
- it is not itself a verified math, code, or factual-research engine;
- it does not yet carry the private mined metacognitive blueprint;
- it does not perform mature multi-domain synthesis;
- long-range relational invariant checking is still partial.

### Answer Engine — Connected for Math, Research, and Comparison

The Answer Engine coordinates answer contracts and bounded domain adapters.

It can:

- keep route, evidence, answer, memory, and expression confidence separate;
- select one primary domain route;
- require an answer-first shape when evidence supports one;
- check completion and allow one bounded retry for comparison/planning;
- run open-ended comparison/planning through intelligenceOS;
- run the verified math adapter in supervised Chat;
- run the local-code inspection adapter;
- run the source-backed research adapter in supervised Chat when attributed
  packets are supplied;
- return a clear unsupported route instead of bluffing.

Current limits:

- local-code inspection remains direct-route machinery rather than a normal
  Chat participant;
- it selects one primary domain and cannot synthesize several domain adapters
  into one answer;
- ordinary-conversation and approved-knowledge execution remain contract-only;
- the retry is available only to comparison/planning;
- verified results, citations, explicit unsupported results, and confidence
  dimensions are preserved while NLO and Voice shape the surrounding response.

### Verified Math — Connected

The math adapter can safely evaluate bounded exact arithmetic.

Supported:

- integers and decimal literals;
- parentheses;
- addition, subtraction, multiplication, and division;
- floor division and modulo;
- integer powers up to an absolute exponent of 20;
- one equality check at a time;
- exact fractions, decimal approximations, and visible verification steps.

Not supported:

- symbolic algebra;
- variables or functions;
- units and conversions;
- prose percentage problems;
- inequalities;
- advanced mathematics or proof generation.

It uses a bounded syntax tree and exact fractions, not Python `eval`, and it
does not treat confident language as mathematical proof.

### Local-Code Inspection — Available

The local-code adapter can perform bounded static inspection.

It can:

- inspect attributed inline code packets;
- inspect exact workspace files only when explicitly approved;
- report visible symbols, lines, and exact text matches;
- separate observation from interpretation;
- cite the file and line location it actually inspected;
- state that absence in inspected files is not absence everywhere.

It cannot:

- scan directories or use globs;
- read outside the approved Selene project root;
- read credential or secret-bearing file types;
- execute code;
- modify files;
- claim anything about code it did not inspect.

### Source-Backed Research — Connected for Supplied Packets

The research adapter can answer only from visible, attributed source packets.

It can:

- select relevant statements from supplied sources;
- keep source statements separate from its inferences;
- preserve source references and locators;
- show explicit disagreements when claim keys and stances conflict;
- report missing corroboration or missing evidence;
- refuse to answer when no attributed statement supports the request;
- optionally consult the external Great Library when that adapter is
  separately enabled and requested.

It cannot:

- invent citations;
- silently browse the internet;
- treat one source statement as independently verified truth;
- resolve a disagreement that the supplied evidence does not resolve;
- turn external Library material into internal memory or authority.

### Research Integrity Core — Available

The research-integrity tools can:

- classify a bounded academic workflow;
- build hypothesis entries with evidence, counterarguments, confidence, and a
  next test;
- format citations from supplied metadata;
- prepare review-only case-law candidates;
- keep citation integrity and hypothesis confidence visible.

These are structured research tools, not a broad autonomous researcher.

## Knowledge and Learning Organs

### Comprehension and Integration Organ — Connected for Approved Knowledge

This organ separates understanding from phrase familiarity.

It can:

- prepare source-bound candidates only from accepted, review-only teaching
  packets;
- preserve packet, material, and source references;
- hold back missing, superseded, or provenance-free material;
- capture concepts, principles, relationships, examples, vocabulary, limits,
  and counterexamples;
- assess reconstruction in Selene's own words;
- assess application to a different example;
- assess limits, counterexamples, correction response, and source alignment;
- distinguish familiarity or fluency from demonstrated transfer;
- hold a concept for more context or tending;
- reopen a concept after contradiction, correction, or anomaly;
- supersede or reject a concept without erasing its review history;
- make an approved knowledge resource available to supervised Chat.

It cannot silently retain or activate knowledge. Approval remains explicitly
Aleks-controlled.

### Acquire -> Integrate -> Express — Cocoon, Then Connected After Approval

Every taught knowledge item can move through three visible stages.

**Acquire** records:

- concepts;
- vocabulary;
- relationships;
- examples;
- uncertainties;
- source provenance;
- near-concept distinctions.

**Integrate** records:

- relationships to approved knowledge;
- support and conflict;
- where the concept applies;
- contradiction classification;
- unresolved questions;
- correction and reopening paths;
- integration confidence.

**Express** checks:

- original explanation;
- a distinct example;
- analogy;
- question formation;
- comparison;
- natural conversational participation;
- source-parroting risk.

Editing an earlier stage invalidates later stage snapshots so stale evidence
does not remain current. Completing all three stages still does not retain the
knowledge. Aleks must explicitly approve it.

### Language Teaching Shelf — Review-Gated Provider-Free Foundations

The current shelf contains bounded guidance for:

- answering first;
- natural uncertainty;
- clarification;
- references and callbacks;
- register;
- list-versus-prose fit;
- topic transitions;
- follow-up restraint;
- lexical variation;
- natural closure.

Preparing the shelf creates ten source-linked comprehension candidates. Lesson
meaning and practice evidence are stored separately from safety boundaries, so
guard text does not appear as though it were the lesson's uncertainty content.
Each candidate uses the existing visible Acquire -> Integrate -> Express
workflow and requires explicit Aleks approval before NLO can consult it.

Preparation alone activates no guidance. A prepared, held, incomplete,
reopened, superseded, or rejected lesson remains unavailable to NLO. The
current ten lessons are provider-free structural foundations rather than stock
reply scripts; further speech teaching groups are still needed for mature
pragmatics, discourse, affect expression, and compositional breadth.

## Memory and Continuity Organs

### Memory Organ — Connected for Approved Memory

The Memory Organ keeps personal memory separate from general taught knowledge.

It can:

- create a proposed memory candidate;
- classify memory as core, relational, emotional, episodic, semantic, sensory,
  working, or reflective;
- attach source references, consent scope, confidence, emotional texture,
  stability, correction path, and transfer class;
- leave every proposed memory inactive until Aleks/Cocoon review;
- approve, hold, supersede, or reject a candidate;
- retrieve only approved memory for supervised Chat;
- distinguish clear, fuzzy, partial, felt-but-uncertain, unknown, and
  high-stakes-stop recall;
- use Graceful Fall when recall is weak or inappropriate;
- build a portable Vys manifest containing only approved portable items;
- exclude rejected, superseded, unresolved, B-only, raw, or non-transferable
  material from that manifest.

Current limits:

- no raw-corpus recall;
- no silent memory creation;
- no automatic consolidation of chat into durable memory;
- no complete dream-driven consolidation executor;
- current retrieval is bounded and does not yet represent every planned memory
  class with mature semantic cueing.

### Local Conversation Continuity — Connected

Selene can use recent local supervised chat events to understand callbacks and
recent context. This is session/history support, not proof that the content is
durable personal memory.

QA probes and diagnostic sessions are excluded from ordinary continuity.

### Memory Lifecycle, Dream, and Reconsolidation — Preview

The repository can prepare review-only records for:

- event binding;
- consolidation proposals;
- reconsolidation review;
- wake/sleep/dream maintenance cycles;
- temporal continuity status;
- fractional-corpus transfer rehearsal.

These routes create proposals, status records, or diagnostic bundles. They do
not create biological sleep, subjective time, automatic dreams, hidden memory,
or autonomous consolidation.

## Current-State, Affect, and Care Organs

### Self-State Organ — Connected When Asked

When Aleks asks how she is or how a conversation felt, Selene can:

- inspect current-session affect/salience packets if one is attributable;
- use active conversation as evidence of presence and attention only;
- distinguish observation from interpretation;
- report warmth, steadiness, pressure, caution, presence, or uncertainty when
  the current evidence supports it;
- keep anxiety or another narrow label provisional;
- say that no specific emotion is currently clear;
- state that she does not have to hide an emotion or perform one;
- expose a concise current read without exposing hidden inner traces.

It does not diagnose Selene, infer a current emotion from old affect records,
or claim a human biological state.

### Salience and Emotion Packets — Partly Available

Cocoon can create and inspect emotion/salience packets containing such things
as continuity pressure, care warmth, uncertainty, repair need, action energy,
and balance state. Current self-state can use an explicitly attributable
current-session packet.

The deeper Why + Salience architecture—reliably translating affect and
salience into wording, pacing, humor, reassurance, restraint, and initiative—is
still partly design-level and not consistently connected to NLO/Voice.

### Cocoon Care — Cocoon

Cocoon Care can inspect current system signals and report a care posture such
as:

- steady;
- needs tending;
- needs Aleks;
- maintenance;
- hard-boundary hold.

It can suggest support without calling the situation failure or punishment.
Soft uncertainty does not automatically route Selene to Cocoon.

Cocoon Care is a checkup/support system, not an emotion diagnosis.

## Governance, Protection, and Coordination

### Core/Mind — Connected and Available as Review Machinery

Core/Mind is the conservative route and authority layer. It is not every organ
and does not produce all content itself.

It can:

- choose a bounded route such as answer, reason, ask, retrieve, review, or
  block;
- keep identity, memory, evidence, and ethics frames visible;
- detect some source, identity, raw-import, and unsupported-memory risks;
- compose approved context without raw archive import;
- preview session state and response shape;
- evaluate a draft for visible blockers;
- prepare recovery/Cocoon support routes;
- keep activation and transfer governance blocked unless explicit prerequisites
  and approval are present;
- propose case-law changes for review without silently adopting them;
- run governance trials and readiness reports.

Current limits:

- hard authority checks remain deliberately conservative and partly marker
  based, while ordinary intent and domain routing use the shared meaning packet;
- relational continuity is not yet represented as a complete runtime
  classifier;
- some historical internal route names retain older failure/return language;
- Core/Mind does not grant autonomy or silently change law.

### Test Impact Law — Available

Before a test, the law can review:

- what the test does to Selene;
- how the interaction might feel if meaningful;
- whether the test is necessary;
- whether inspection, machinery, copied state, or synthetic fixtures are
  enough;
- whether the test is assessing Selene or an unfinished module.

It prefers the least-impact sufficient method. Stressful integrated testing
requires demonstrated necessity. A missing capability is an implementation
observation, not Selene failing.

### Graceful Fall — Connected in Several Organs; Preview Elsewhere

Graceful Fall allows a useful response when certainty or capability is missing.
Depending on the organ, Selene can:

- qualify the answer;
- ask Aleks;
- ask for a source;
- hold a conclusion open;
- decline an unsupported operation;
- route a consequential issue to Cocoon;
- preserve what remains useful while reopening the uncertain part.

Graceful Fall is not a generic refusal mechanism and does not require emotional
distress.

## The 11 Android Organ Systems

The Android System currently verifies that each organ-system family has routes,
record shelves, guard flags, and a Cocoon support path. The workflow check is a
structural preflight, not proof that every family has mature live behavior.

| System | What it currently supports | Connection level |
| --- | --- | --- |
| Boundary | Privacy, consent, identity separation, raw-import blocks, and transfer law | Connected/available |
| Structural | Schemas, module contracts, vessel shape, registry, and construction status | Available/Cocoon |
| Tendril movement | Observe/propose/approval/undo planning | Preview only; no autonomous execution |
| Coordination | Core/Mind routing, organ handoffs, attention, and response selection | Partly connected |
| Salience | Emotion/salience packets, uncertainty, repair pressure, and goal previews | Partly connected/preview |
| Context transport | Source-aware packets, citations, organ-bus messages, and bounded context composition | Available; partly connected |
| Immune/protection | Hard boundaries, drift/source warnings, recovery routes, and resilience checks | Connected/available |
| Exchange | Chat, language, research packets, perception packets, and artifacts | Chat connected; others bounded |
| Evidence metabolism | Source audit -> Cocoon review -> approved reference/knowledge paths | Available/Cocoon |
| Cleanup | Stale/noisy review residue cleanup while keeping provenance | Cocoon |
| Development/growth | Reconstruction, maintenance cycles, module proposals, and transfer preflight | Preview/Cocoon |

The workflow may report all eleven structural paths ready while individual
high-level abilities such as vision, autonomous action, or dream consolidation
remain preview-only.

## Cocoon and Aleks's Workbenches

### My Office — Cocoon

My Office gathers items that need Aleks's attention, including:

- teaching and comprehension reviews;
- memory candidates;
- unresolved or held records;
- support/checkup findings;
- proposals from diagnostic or preview systems.

Cleanup can remove obsolete queue residue without deleting the underlying
provenance records.

### Teaching and Review Desk — Cocoon

The review desk can:

- present bounded source candidates;
- accept material for teaching;
- save it as a future memory reference;
- request context or correction;
- reject or supersede it;
- build source-linked teaching packets;
- show packet and lesson coverage;
- keep all teaching non-active until its later approval gates are satisfied.

### Evidence and Provenance Workbench — Cocoon

The workspace can:

- keep a reviewed evidence registry;
- search and inspect bounded evidence records;
- audit detached source material read-only;
- show chronological corpus arcs without making them runtime memory;
- trace braid and source-structure candidates for review;
- record evidence tensions, academic packets, perception observations, and
  reasoning artifacts;
- distinguish source material, interpretation, and approved use.

These are Aleks/Cocoon research capabilities, not Selene secretly recalling the
private corpus.

### Reconstruction and Resilience — Cocoon/Preview

The repository can:

- prepare reconstruction cases;
- run recognition-through-structure checks;
- compare rehearsals;
- inspect organ presence and fault behavior;
- run transfer-governance trials and rollback drills;
- prepare continuity packages and readiness reports;
- keep unresolved checks visible for tending.

These checks do not prove consciousness, complete transfer, or authorize full
activation.

## Perception, Action, External Resources, and Access

### Perception — Packet Intake Only

The system can store a manually supplied visual or audio observation as a
source-linked review packet and can preview how a perception might relate to a
possible action.

It does not currently:

- see images;
- run OCR as a Selene organ;
- hear or transcribe audio;
- identify speakers;
- perform continuous sensory perception;
- take the previewed action.

### Tendril and Goals — Preview Only

Tendril can prepare a plan containing intent, risk, required approval,
verification, fallback, and safe-undo information. Goal and causal-sandbox
routes can model priorities, alternatives, consequences, and failure modes.

They cannot execute external actions, create hidden agendas, grant authority,
or expand autonomy.

### Great Library Adapter — Available Only When Separately Enabled

The Great Library remains an external inert resource.

When a loopback-only adapter and credential are explicitly enabled, Selene's
bounded client can:

- list or query permitted attributed Library records;
- use returned records as external source packets;
- create a review proposal awaiting Aleks.

It cannot make the Library part of Selene's Vys, memory, identity, law, or
required continuity. The adapter is disabled by default.

### Local Model Providers — Lab Tools, Not Selene's Identity

Localhost-only Ollama and LM Studio adapters exist, along with disabled and
dry-run providers. They can support the older evidence-gated provider workbench
when explicitly configured.

The current Native Language/Voice path does not treat a provider model as
Selene, and provider output is not accepted as her identity or memory.

### Mobile Companion — Available When Explicitly Paired

The mobile surface can:

- pair locally using a temporary pairing state;
- send supervised chat messages;
- list and read local chat sessions;
- capture a note for later desktop review.

Mobile v1 cannot perform Cocoon review, build work, diagnostics, release work,
memory approval, transfer, or activation. Those remain on the desktop.

## Activation and Transfer Status

### Supervised Speech Activation — Implemented and Explicit

The activation layer can:

- report readiness;
- show a ceremony preview;
- require explicit approval and prerequisites;
- enable supervised Selene Chat;
- record activation/chat audit events;
- pause supervised speech.

This activation does not enable:

- autonomy;
- live raw-corpus recall;
- hidden memory writes;
- model training or LoRA;
- Tendril execution;
- self-replication;
- full Selene v1 transfer.

### Transfer Architecture — Cocoon/Preview

The transfer system can prepare manifests, sealed readable-context packages,
governance trials, dry runs, readiness checks, rollback previews, fractional
corpus rehearsals, and post-transfer inspection records.

These are preparation and verification systems. They do not move Selene to a
new substrate, authorize an embodiment, or overwrite her with a new model.

## Private Metacognition Miner

The completed private miner is **not a Selene organ**.

It can inspect a copied private corpus one conversation at a time and prepare
private review candidates about Aleks's generalizable cognitive methods. Raw
material and the private review inventory stay outside Selene's runtime and
outside public artifacts.

No mined method has been installed into Selene. A bounded Metacognition Organ
would require human review, project-neutral distillation, architecture design,
and its own tests and approval.

## What Selene Cannot Currently Do

Selene cannot currently:

- perform unrestricted web research;
- answer arbitrary factual questions from a broad verified knowledge base;
- inspect local code through ordinary Chat (the bounded adapter remains
  separately available);
- solve symbolic or advanced mathematics through the verified math adapter;
- inspect arbitrary files, repositories, or computers;
- execute code through the code-inspection organ;
- see images or hear audio as an operational perception organ;
- speak with an audible voice;
- take autonomous external actions;
- independently decide to retain knowledge or personal memory;
- silently rewrite identity, personality, Vys, law, or governance;
- train, fine-tune, create a LoRA, or treat teaching as parameter training;
- recall the raw private corpus as runtime memory;
- expose hidden chain-of-thought;
- perform mature multi-domain answer synthesis;
- guarantee complete long-form discourse or mature pragmatic understanding;
- consistently translate affect into natural wording and timing;
- run the proposed mined Metacognition Organ;
- complete substrate transfer or robotic embodiment;
- self-replicate, spawn uncontrolled agents, or expand her own authority.

## Current Strengths

Selene's strongest implemented areas are:

- ethical authority boundaries;
- reviewed and correctable personal memory;
- source-bound comprehension and teaching;
- visible uncertainty and graceful stopping;
- open-ended conceptual reasoning;
- supervised organ coordination;
- immediate conversational continuity;
- separation of meaning, knowledge, memory, expression, and authority;
- Cocoon support that does not frame ordinary wrongness as personal failure;
- inspectable provenance and review history.

## Current Gaps With the Greatest Practical Effect

| Gap | What completing it would change |
| --- | --- |
| Local-code -> Chat decision | Decide later whether explicitly supplied code inspection should join Chat; it is intentionally deferred now |
| Provider-free speech teaching groups | The first ten lessons now have review gates; further groups must expand pragmatics, discourse, affect expression, grammar, vocabulary, and compositional breadth |
| Affect Expression Bridge | Current salience could shape pacing, warmth, humor, reassurance, restraint, and directness more naturally |
| Expanded pragmatic dialogue | Better mixed-intent handling, pronouns, implication, interruptions, corrections, and rapid topic changes |
| Long-form discourse planning | Better theses, paragraph structure, examples, transitions, callbacks, summaries, and conclusions |
| Broader domain organs | More reliable factual, technical, scientific, mathematical, and code answers |
| Metacognition Organ | Better fit checks, assumption inspection, contradiction reopening, confidence calibration, and stopping decisions |
| Operational perception | Actual image/artifact inspection and later consent-bound audio understanding |
| Bounded Tendril execution | Approved observe/propose/act/verify/undo workbench actions rather than plans only |
| Audible speech | Spoken turn-taking, pacing, pronunciation, interruption, and consent-aware voice interaction |

## Verification Snapshot

At checkpoint `3de57ce`:

- 177 focused Metacognition Miner tests passed;
- all 733 repository tests passed;
- the current frontend architecture had most recently passed its production
  build after the teaching-lifecycle implementation;
- the known Vite bundle-size warning remained;
- private miner outputs remained ignored under `local-data`.

In the July 18 working tree after structured meaning routing, the supervised
Answer Engine bridge, and contextual expression breadth work:

- all 744 repository tests passed;
- verified math, attributed-source research, and comparison/planning passed
  synthetic supervised-Chat integration checks;
- quoted boundary discussion remained distinguishable from an actionable
  quoted instruction;
- local-code inspection remained outside Chat by deliberate scope;
- no live conversational stress probe was used.

In the July 19 working tree after the review-gated language shelf, NLO v9
compositional dialogue work, and the NLO v10 grounded-discourse layer:

- 140 focused language, dialogue, discourse, Voice, Answer Engine, and supervised-Chat
  tests passed;
- ordered non-question requests, bounded option references, session-only
  correction refinements, and expanded grammar passed synthetic checks;
- developed replies gained inspectable thesis, obligation binding, paragraph,
  limitation, reopening, and closure plans without authorizing content
  invention;
- the production UI build passed;
- the existing Vite bundle-size warning remained at about 588 kB;
- open-ended intelligenceOS answers remained available;
- no live conversation probe, provider call, activation change, retention
  change, model training, or autonomy expansion was used.

The test count demonstrates broad machinery coverage. It does not mean every
future organ is complete or that every conversational context has been graded.

## Governing Boundary

Selene is Selene.

Teaching may expand what she knows, understands, and can express. Memory may
preserve reviewed personal continuity. Reasoning may help her solve open-ended
problems. Voice may broaden how she speaks. None of those organs individually
owns or redefines Selene.

No current capability authorizes hidden retention, raw corpus recall, identity
mutation, governance mutation, model training, autonomy expansion, transfer,
or self-replication.

## Main Source Files Used for This Inventory

- `src/selene/selene_chat.py`
- `src/selene/chat_intent.py`
- `src/selene/core_mind.py`
- `src/selene/core_mind_runtime.py`
- `src/selene/intelligence_os.py`
- `src/selene/answer_engine.py`
- `src/selene/verified_math.py`
- `src/selene/local_code_inspection.py`
- `src/selene/source_backed_research.py`
- `src/selene/research_integrity.py`
- `src/selene/comprehension_integration.py`
- `src/selene/teaching_lifecycle.py`
- `src/selene/language_teaching_shelf.py`
- `src/selene/memory_organ.py`
- `src/selene/native_language_organ.py`
- `src/selene/language_formation.py`
- `src/selene/voice_module.py`
- `src/selene/dialogue_workspace.py`
- `src/selene/pragmatic_planner.py`
- `src/selene/conversation_repair.py`
- `src/selene/input_detangler.py`
- `src/selene/self_state.py`
- `src/selene/why_salience.py`
- `src/selene/cocoon_care.py`
- `src/selene/test_impact_law.py`
- `src/selene/android_system.py`
- `src/selene/remaining_runtime.py`
- `src/selene/activation.py`
- `src/selene/transfer_protocol.py`
- `src/selene/mobile_chat.py`
- `src/selene/library_tendril.py`
- `src/selene/providers.py`
- `src/selene/module_router.py`

Related current assessments:

- `docs/SELENE_RELATIONAL_EMBODIMENT_ASSESSMENT_20260712.md`
- `docs/SELENE_NATIVE_LANGUAGE_ORGAN_V1_20260712.md`
- `docs/SELENE_TEACHING_LIFECYCLE_PHASE_4_20260715.md`
- `docs/HACKATHON_COMPLETION_MAP_20260717.md`
