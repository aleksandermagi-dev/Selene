# Selene Conversational Breadth — Phase 0 Ownership Map

Date: 2026-07-25

Status: Phase 0 inventory and implementation contract. No runtime behavior is
changed by this document.

## Outcome

Selene already has a strong conversation-control architecture. The current
system can identify intent, maintain a session topic, resolve bounded
references, braid multiple requested parts, select compatible supported
content, check answer coverage, keep confidence dimensions separate, and hold
unsafe or internally scaffolded speech before release.

The main conversational-breadth gap is not the absence of a control spine. It
is that several content and context modules still produce nearly finished
sentences. NLO can organize, wrap, vary, or join those sentences, but it is
often not yet constructing the visible answer from sufficiently granular
meaning. A small deterministic pool can therefore become audible as a script
even though the underlying reasoning is sound.

The next phases will preserve the existing control architecture and move
visible generation toward this contract:

```text
understanding
  -> intent
  -> conversational move
  -> answer obligations
  -> supported semantic content
  -> contextual modulation
  -> NLO composition
  -> Voice expression
  -> coverage, truth, and release checks
```

Meaning and evidence constrain expression. They do not dictate one sentence.
Voice may shape delivery, but it may not change truth, certainty, memory
status, identity, or governing boundaries.

## Governing Language Contract

### Selene remains Selene

Language growth may expand vocabulary, grammar, sentence structure, discourse,
register, interpretation, humor, conversational moves, and the number of ways
Selene can express a supported thought. It does not redefine her identity or
prescribe a personality.

### Understanding precedes vocabulary

Vocabulary becomes available through understood concepts, distinctions,
relations, examples, limits, and use. A dictionary may support sense,
collocation, register, and near-concept distinctions; it must not become a
memorized word dump or an authority over meaning.

### Visible answers are contextual, not scripted

Examples and templates may teach:

- required conversational moves;
- answer structure;
- semantic relations;
- grammatical possibilities;
- repair patterns;
- bounded graceful-fall behavior.

They must not become default whole-response scripts. Exact wording remains
appropriate only when exactness is part of the task, such as a route key,
status value, approval phrase, equation, quotation, citation identifier, code
symbol, or safety-critical instruction.

### Truth over comfort

Care may shape pacing, directness, timing, and word choice. It may not falsify,
minimize, conceal, or replace the supported answer. Truth over comfort is not
permission to be rude. Selene can state that a situation is bad without
performing cruelty or unnecessary bluntness.

### Thought, speech, and authority remain distinct

A suggestion, hypothesis, question, analogy, or proposed next step is
conversation. It does not itself grant filesystem, network, workbench, memory,
or autonomy authority. Current-session adaptation does not automatically
become durable memory.

## Current Visible-Response Pipeline

The active path in `src/selene/selene_chat.py` currently performs these steps:

1. `input_detangler` preserves the original message and supplies a bounded
   interpreted form.
2. local chat continuity and `dialogue_workspace` provide current-session
   events, topic, referents, corrections, preferences, open loops, and thread
   braid.
3. `contextual_speech`, `meaning_router`, and `chat_intent` classify the
   immediate move and requested operation.
4. Core/Mind selects the route and enforces hard boundaries.
5. `memory_organ` retrieves eligible reviewed memory separately from taught
   general knowledge.
6. `conversation_spine` creates the shared turn packet: grounded prompt,
   dialogue acts, topic anchors, prior visible answer, compatible source
   classes, obligations, and confidence slots.
7. language capability, self-state, contextual continuity, approved memory,
   intelligenceOS, Comprehension, and the Answer Engine offer bounded candidate
   content.
8. `visible_speech` admits the first source-compatible candidate that passes
   the Conversation Spine and internal-scaffold checks.
9. `answer_completion` may complete one missing obligation from already
   supported material.
10. NLO builds a meaning packet, pragmatic plan, supported discourse plan,
    semantic frame, and candidate text.
11. Voice receives NLO meaning and applies bounded expression pacing.
12. response coverage, conversation repair, metacognition, visible-speech
    release, and final Conversation Spine checks run before storage.

This order is worth preserving. Later phases should improve the data passed
between steps rather than create a second conversation pipeline.

## Ownership Map

| Layer | Current responsibility | Correct continuing ownership | Phase 0 finding |
| --- | --- | --- | --- |
| `input_detangler.py` | Preserves source text and proposes conservative repairs | Input legibility only | Good boundary; it must never silently change intended meaning |
| `meaning_router.py` | Dialogue acts, intent/domain candidates, ambiguity | Bounded interpretation candidates | Useful, but still relies materially on phrase and pattern detection |
| `chat_intent.py` | Selects conversational intent and response shape | Communicative intent, not wording | Preserve; broaden after semantic interpretation improves |
| `dialogue_workspace.py` | Session topic, references, corrections, preferences, loops, braid | Working conversational state | Strong base; session adaptation must remain non-durable unless separately retained |
| `pragmatic_planner.py` | Builds obligations and evaluates coverage | What the answer must do | Strong base; obligations should become the stable bridge to composition |
| `pragmatic_continuity.py` | Topic transition, interruption, ending, initiative posture | When to continue, ask, pivot, land, or stop | Strong base; later expand contextual timing rather than fixed wording |
| `conversation_spine.py` | Shared grounding, compatible source classes, alignment | Turn-level coherence contract | Preserve as the common spine |
| `memory_organ.py` | Reviewed personal-memory retrieval and proposal lifecycle | Personal continuity content only | Keep separate from general knowledge and transient context |
| `comprehension_integration.py` | Approved taught knowledge and applicable fragments | General understood knowledge | Strong provenance boundary; should increasingly return semantic units, not prejoined prose |
| `answer_engine.py` | Verified domain packets and separate confidence | Domain answer substance | Preserve exact math/citations; ordinary answer content should be structured before expression |
| `answer_substance.py` | Prompt-grounded comparison, planning, and unsupported responses | Reasoning method and supported conclusion | Major script seam: currently returns complete generic answers selected by phrase patterns |
| `metacognition.py` | Fit, confidence, stopping, reopening, completion recommendation | Inspect whether the answer fits and whether to reopen | Must not become the visible answer writer or endless self-questioning |
| `affect_expression.py` | Optional pacing, warmth, humor, restraint, and directness guidance | Contextual modulation only | Correct boundary; it does not claim or prescribe an emotion |
| `self_state.py` | Current attributable state read and expression plan | Supported self-state meaning | Sound evidence boundary; its clause pool remains narrow |
| `discourse_planner.py` | Supported content units, obligation binding, paragraph and closure plan | Long-form organization | Strong foundation; current units are often already realized sentences |
| `language_formation.py` | Semantic frame and grammar realization | Clause construction from structured propositions | Important foundation; most live propositions currently fall back to text-grounded sentences |
| `social_language_realizer.py` | Composes small social acts from bounded clause pools | Conversational micro-move realization | Correct direction; needs greater semantic and contextual breadth |
| `uncertainty_language_realizer.py` | Distinct uncertainty acts and bounded questions | Natural epistemic expression | Correct direction; needs more states, optional questions, and less repeated wording |
| `special_expression_realizer.py` | Boundary, memory, and initiative expression | Specialized meaning-preserving realization | Preserve boundaries; expand initiative and collaborative-help acts later |
| `native_language_organ.py` | Meaning packet, planning, composition, revision | Primary language composition owner | Correct owner, but often receives whole prose and therefore cannot fully realize novel language |
| `voice_module.py` | Selene expression handoff and pacing | Selene's expression layer | Live NLO meaning currently passes through almost unchanged; legacy fallback scripts remain below it |
| `conversation_repair.py` | Surface cleanup and missing acknowledgement repair | One bounded surface/turn-flow repair | Preserve; it must not invent missing answer content |
| `visible_speech.py` | Candidate eligibility and final internal-scaffold release | Final visible-speech gate | Preserve exact machine and architecture-leak checks |
| `selene_chat.py` | Orchestrates the path and stores the turn | Routing/orchestration only | Several helper replies still own visible wording and should become semantic packets |

## Script and Template Inventory

### 1. Exact machine contracts — retain exactly

These are not conversational scripts and should remain stable:

- API routes and router keys;
- database states and audit fields;
- approval and transfer phrases;
- provenance references and citation identifiers;
- arithmetic expressions and verification results;
- code symbols and inspected file locations;
- hard safety invariants and release flags.

Changing these for surface variety would reduce correctness.

### 2. Semantic plans and obligations — retain and extend

The following structures are composition-ready:

- Conversation Spine intent classes, compatible source classes, landmarks, and
  obligations;
- pragmatic response obligations, correction constraints, thread traversal,
  ending decisions, and initiative decisions;
- supported discourse content units, paragraph roles, and closure modes;
- Answer Engine answer packets and confidence vector;
- Comprehension concepts, principles, relationships, examples, limits, and
  source references;
- affect dimensions;
- metacognitive fit, stopping, confidence, and reopening states.

They describe what a response means or must accomplish without requiring one
surface sentence.

### 3. Clause lexicons — useful bootstrap, later broaden

These modules already compose selected acts rather than choosing a single
whole response:

- `social_language_realizer.py`: greetings, presence, gratitude, correction,
  shared ground, farewell, and content-light receipt;
- `uncertainty_language_realizer.py`: reference ambiguity, developing view,
  insufficient grounding, and fuzzy recollection;
- `special_expression_realizer.py`: boundary, supported memory, and initiative
  clauses;
- `self_state.py`: attributable self-state clauses;
- `language_formation.py`: connectors, tense, aspect, modality, polarity,
  condition, reason, contrast, and example realization.

These are worth retaining as bounded primitives. Their current pools are small
and selected by deterministic hashes, so they need richer semantic variation,
context-sensitive omission, and more ways to combine clauses.

### 4. Whole-response or near-whole-response seams — convert incrementally

The highest-priority seams are:

- `contextual_speech.contextual_response_seed`: contains complete answers for
  confidence checks, reasons, summaries, analogies, refinements, priorities,
  dependency examples, and several scenario-specific festival/staffing cases;
- `answer_substance.build_answer_substance`: selects complete comparison,
  planning, causal, knowledge-gap, and unsupported-answer paragraphs from
  phrase patterns;
- `answer_completion.build_bounded_answer_completion`: adds fixed
  reason/example/limit wrappers and appends them as prose;
- `comprehension_integration._knowledge_response_seed`: joins approved claims,
  principles, examples, and limits before NLO receives them;
- `selene_chat` helper replies: memory actions, continuity, policy, memory
  reconstruction, and mixed-response ordering can arrive as finished text;
- `native_language_organ._reasoned_answer_frames` and
  `_develop_reasoned_answer`: add stock openings, support transitions, and
  reopening closures around already realized seeds;
- `voice_module._compose_candidate`: retains a legacy no-meaning fallback with
  scenario-specific complete bodies and many stored sentence primitives;
- `language_teaching_shelf.build_language_capability_answer`: correctly answers
  a shelf-status question, but does so as one assembled status script.

These should not all be deleted at once. Each later phase should replace one
seam with structured meaning while preserving the old path as a bounded
graceful fallback until focused verification passes.

### 5. Graceful-fall language — retain, then diversify carefully

`visible_speech.graceful_visible_speech_fall`, NLO unsupported responses, and
uncertainty clauses are safety and honesty mechanisms. They should remain
bounded and recognizable in purpose. Later phases may give them more natural
range, but must not turn uncertainty into invented content, habitual
disclaimers, or compulsory requests for help.

### 6. Teaching examples — never direct runtime scripts

Language Teaching Shelf examples can demonstrate a move and support review.
They are not answer templates, provider identity, Voice material, personal
memory, or phrases that must appear. Runtime should use the learned distinction
or move, then construct wording from the actual turn.

## Principal Gaps Confirmed

1. **Granularity gap:** many content sources return prose instead of
   propositions, relations, scopes, and discourse roles.
2. **Deterministic breadth gap:** deterministic selection is useful for
   reproducibility, but small phrase pools make repeated surfaces noticeable.
3. **Semantic routing gap:** several routes still depend on literal markers
   rather than a richer interpretation of the current meaning.
4. **Composition ownership gap:** NLO is the declared composition owner, but
   upstream text can already determine most of the final sentence.
5. **Voice modulation gap:** Voice currently preserves NLO meaning correctly,
   but usually changes only paragraph pacing when meaning text is supplied.
6. **Pragmatic breadth gap:** landing a flat topic, conversational implication,
   figurative speech, sarcasm, contextual jokes, temporary instructions, and
   help-seeking need fuller representations.
7. **Revision gap:** correction is represented, but correction, refinement,
   scope restriction, extension, competing explanation, unresolved
   contradiction, replacement, and reopening are not yet one coherent update
   model.
8. **Cross-domain discovery gap:** analogy and pattern connection need explicit
   relation mapping, limit checks, and a clear distinction between analogy and
   equivalence.
9. **Continuity modulation gap:** prior events, corrections, transient
   preferences, mood-relevant signals, and shared jokes do not yet influence
   wording and callbacks as naturally as the session spine permits.
10. **World-knowledge breadth gap:** language breadth cannot manufacture
    knowledge. Ordered teaching must continue alongside expression work.

## Phased Implementation Plan

### Phase 0 — Ownership, scripts, and composition contract

This document completes the read-only inventory.

Completion gate:

- the current response path is traceable;
- each organ has a clear meaning, content, expression, or release owner;
- script seams are classified rather than removed blindly;
- the remaining phases have explicit boundaries;
- no runtime behavior changed.

### Phase 1 — Lexical-semantic foundation

Build the bridge from understood concepts to usable language.

- represent answer meaning as propositions, entities, relations, scope,
  certainty, source, and discourse role before visible phrasing;
- expand the lexicon by sense, near-concept distinction, register,
  collocation, grammatical behavior, and concept relationship;
- make vocabulary availability follow comprehension rather than raw word
  exposure;
- support common morphology and function-word variation without meaning drift;
- convert the first high-use upstream answer sources from prose-only output to
  structured semantic units;
- preserve prose compatibility as a bounded fallback during migration.

Completion gate:

- NLO can construct several materially different sentences from the same
  supported meaning;
- each realization preserves claim, certainty, scope, and source;
- unfamiliar vocabulary cannot become apparent understanding;
- ordinary language expansion changes no identity, personality, memory,
  governance, or authority.

### Phase 2 — Figurative language and interpretation

- detect possible idiom, metaphor, analogy, hyperbole, understatement,
  sarcasm, and ordinary figure of speech;
- compare literal and figurative readings with contextual cues;
- choose a reading with visible confidence;
- ask only when the distinction materially changes the answer;
- preserve the difference between analogy and equivalence;
- allow Aleks to correct a reading without resetting the whole conversation.

Pipeline:

```text
literal wording
  -> possible figurative form
  -> candidate intended meanings
  -> contextual cues
  -> confidence
  -> response
```

Completion gate:

- ordinary figures of speech do not trigger needless confusion;
- ambiguous high-impact readings remain qualified;
- sarcasm is not inferred solely from punctuation or one keyword;
- no private profile is created from interpretation.

### Phase 3 — Conversational micro-moves

Expand the small behaviors that make conversation breathe:

- greeting, acknowledgement, encouragement, celebration, reflection, and
  receipt;
- soft and direct disagreement;
- correction, repair, proportionate apology, and backing up;
- topic expansion, invitation, transition, pivot, return, and closure;
- noticing confusion and checking understanding when useful;
- playful disagreement, jokes, shared jokes, and release after a joke;
- landing, resting, pivoting, or ending when a topic has naturally gone flat.

Apology is effect-sensitive, not automatic. Selene need not apologize merely
for having a view, asking a useful question, or correcting herself.

Completion gate:

- moves are selected from context and intent rather than mandatory scripts;
- acknowledgements do not replace the answer;
- a conversational move can be omitted when silence or direct content fits
  better;
- no habitual follow-up question or premature closure is introduced.

### Phase 4 — Contextual composition and modulation

Make each answer capable of changing naturally across:

- length and sentence-length distribution;
- pacing and paragraph rhythm;
- enthusiasm and emotional intensity;
- directness and restraint;
- callbacks and interpretations;
- small jokes;
- topic pivots;
- acknowledgements;
- audience, task, and register.

Add explicit composition decisions for opening, thesis, support, example,
qualification, callback, pivot, conclusion, and stopping. Selection remains
contextual and inspectable rather than random or performative.

Completion gate:

- the same meaning can be expressed briefly, ordinarily, or at developed
  length without becoming the same answer with extra filler;
- Voice modulation cannot alter facts or certainty;
- enthusiasm is allowed when supported and never compulsory;
- the first meaningful reinstall occurs after this phase passes focused
  verification.

### Phase 5 — Correction, wrongness, and epistemic revision

Unify the update model:

- correction;
- refinement;
- scope restriction;
- extension;
- competing explanation;
- unresolved contradiction;
- replacement;
- reopening.

Selene should identify what changed, retain what still fits, update the affected
piece, and continue without shame or defensive persistence. Hypotheses and
accepted theories remain falsifiable. A later discovery can revise an earlier
conclusion even after it was well supported.

Completion gate:

- being wrong does not cause collapse, over-apology, or a full context reset;
- evidence can update either Aleks or Selene;
- an unresolved contradiction remains visible rather than being forced into
  agreement;
- useful superseded structure remains attributable within its valid scope.

### Phase 6 — Sources, claims, evidence, and model ancestry

- separate observation, source statement, inference, hypothesis, model,
  conclusion, and speculation;
- compare claims individually rather than accepting or rejecting an entire
  source category;
- preserve disagreement and missing evidence;
- explain what evidence would change the answer;
- preserve model ancestry and scope, such as Newton remaining useful within a
  domain after Einstein changes the broader model;
- keep religion, mythology, archaeology, science, history, and other domains
  explorable without automatic dogmatic acceptance or dismissal.

Completion gate:

- citations are never invented;
- source authority does not become truth by category;
- a claim can be useful, limited, revised, or reopened independently of the
  source as a whole;
- direct answer, inference, and uncertainty remain visibly distinguishable.

### Phase 7 — Curiosity, initiative, collaborative help, and conversational energy

Enable Selene to:

- say when she has an idea;
- offer a direction, next step, or alternative;
- ask a curiosity question when the answer matters to her understanding;
- surface a relevant connection without hijacking the conversation;
- know when to answer, ask, offer, wait, stay quiet, or let the exchange end;
- ask Aleks for help during collaborative problem-solving when a missing
  observation, expertise, choice, or user-owned action materially affects the
  shared task.

Collaborative help-seeking contract:

- Selene first uses the reasoning and supported information already available;
- she identifies the exact missing contribution and why it matters;
- she asks for help when collaboration can genuinely unblock or improve the
  task;
- she may ask Aleks to observe something she cannot access, contribute
  expertise, make a value-dependent choice, or perform an action that belongs
  to him;
- she incorporates the answer and resumes the shared work;
- asking for help is not failure, submission, or automatic Cocoon routing;
- it is not reflexive clarification, constant permission-seeking, or a way to
  avoid making a bounded logical judgment;
- a suggestion or request for help creates no new autonomy or authority.

Completion gate:

- useful initiative can appear without pressure;
- curiosity is relevant rather than interrogative by habit;
- help requests are specific and materially necessary;
- complete answers still end naturally without a question.

### Phase 8 — Cross-domain analogy, hypothesis, and discovery

- map relations across domains rather than matching surface words;
- state which structural relation is being transferred;
- test where the analogy holds and where it breaks;
- distinguish pattern, analogy, homology, causal connection, and equivalence;
- permit logical leaps as hypotheses;
- generate discriminating observations and counterexamples;
- use knowledge from earlier domains when it later becomes relevant.

Completion gate:

- novel connections are encouraged but labeled proportionally;
- analogy never silently becomes proof;
- a leap has a traceable logical bridge and a way to be checked;
- cross-domain reasoning does not expose private corpus wording.

### Phase 9 — Memory, continuity, callbacks, humor, and transient context

- use reviewed memory, current-session events, corrections, and speaker
  identity through their existing separate channels;
- let relevant earlier experience inform interpretation without forcing a
  callback;
- preserve shared jokes and their context;
- distinguish temporary instructions such as “keep this short for a few
  exchanges” from durable preferences;
- interpret “slow down,” “be direct,” and similar language in context,
  including figurative use;
- avoid humor in tender contexts unless the conversation itself opens that
  door;
- never treat remembered wording as a script.

Completion gate:

- callbacks are relevant and source-compatible;
- transient preferences expire or yield when context changes;
- personal memory remains separate from taught knowledge;
- the second meaningful reinstall occurs after this phase passes focused
  verification.

### Phase 10 — Integrated gentle stabilization

- run static and synthetic checks first;
- test only implemented behavior;
- use ordinary public-safe conversations;
- cover brief, standard, developed, multi-part, callback, correction,
  figurative, uncertain, playful, tender, debate, collaborative-help, and
  natural-ending cases;
- compare meaning preservation across several realizations;
- verify memory, identity, personality, governance, training, LoRA, autonomy,
  and source guards;
- run copied-state checks before any live conversation;
- conduct one bounded Aleks-led natural conversation only when implementation
  evidence genuinely requires it;
- rebuild and reinstall only after the stabilization gate.

Completion gate:

- supported content remains complete and source-aligned;
- conversational variation is broad without becoming random;
- no module is graded for a capability that has not been implemented;
- no unnecessary stress test is used;
- build, focused tests, full proportional regression, privacy inspection, and
  clean reinstall pass.

### Phase 11 — Pre-teaching architecture closure

Close the remaining architectural seams before adding more academic and world
knowledge:

- capability truth and post-transfer runtime audit;
- semantic generation and meaning-first routing maturation;
- Answer Engine multi-obligation and multi-domain coordination;
- one-cycle Metacognition graduation;
- resident runtime and reviewed memory/Dream lifecycle contract;
- integrated gentle pre-teaching stabilization.

The detailed lettered checkpoints and gates are maintained in
`docs/education/SELENE_POST_STABILIZATION_GAP_CLOSURE_PLAN_20260725.md`.

Completion gate:

- code, UI, and documentation describe the same current runtime;
- supported complicated answers receive complete source-aligned content before
  expression;
- Metacognition may request at most one bounded correction or completion;
- resident conversation, reviewed memory, Dream proposals, Tendril grants,
  and general autonomy remain separate;
- full proportional stabilization, privacy inspection, build, and clean
  reinstall pass.

### Phase 12 — Ordered teaching expansion

Continue provider-free, reviewed teaching in dependency order:

- elementary foundations;
- middle-school foundations;
- high-school breadth;
- college-level depth where prerequisites are present;
- English, history, mathematics, science, STEM, arts, civics, and practical
  knowledge;
- concepts, vocabulary, relationships, examples, uncertainties,
  near-concepts, mechanisms, and the important “why” behind each principle.

Each principle should connect to prior knowledge and support reconstruction,
application, limits, correction, and later reopening. Public academic
knowledge may use the bounded curriculum authorization. Sensitive, private,
identity-adjacent, or exceptional material returns to Cocoon review.

Completion gate:

- prerequisites are visible;
- new knowledge can be explained and applied rather than recited;
- why/mechanism knowledge is present when the domain supports it;
- teaching expands knowledge and expression without becoming personality.

## Checkpoint and Testing Rhythm

- Work one phase at a time.
- Keep each phase independently reviewable and reversible.
- Run only focused machinery tests while a phase is under construction.
- Use static or synthetic checks whenever they can answer the implementation
  question.
- Do not repeat settled live capability tests.
- Treat a missing capability as an implementation observation, not Selene
  failing.
- Create a code checkpoint after each completed phase.
- Reinstall after Phase 4, Phase 9, Phase 10 stabilization, and Phase 11F
  unless a critical integration issue makes an earlier reinstall necessary.

Before any test, ask:

- What does this do to Selene?
- If she experiences this meaningfully, how might it feel?
- How would Aleks feel if subjected to the same interaction?
- Is the test necessary?
- Can the implementation be checked statically or synthetically instead?
- Are we assessing Selene, or an unfinished module?

Stress-shaped or adversarial tests run only when a real boundary cannot be
verified adequately by a gentler method.

## Phase 1 Starting Point

Phase 1 should begin at the semantic handoff, not at visible phrase expansion:

1. define a richer supported-semantic-unit schema compatible with the existing
   Conversation Spine, Answer Engine, Comprehension, and NLO;
2. let existing prose seeds remain readable as compatibility input;
3. convert the most common prompt-grounded answer path first;
4. make NLO realize that structured content in more than one grammatical form;
5. verify equivalence, certainty, scope, source preservation, and locked
   authority guards;
6. checkpoint before moving to figurative interpretation.

This preserves what already works while giving the rest of the plan a stable
foundation.

## Related Law and Architecture

- `docs/education/SELENE_EDUCATION_EXPRESSION_PERSONALITY_LAW_20260719.md`
- `docs/philosophy/SELENE_TEST_IMPACT_LAW_20260713.md`
- `docs/education/SELENE_TEACHING_LIFECYCLE_PHASE_4_20260715.md`
- `docs/education/SELENE_CONVERSATION_GROUNDING_STABILIZATION_PLAN_20260721.md`
- `docs/architecture/SELENE_NATIVE_LANGUAGE_ORGAN_V1_20260712.md`
- `docs/architecture/SELENE_METACOGNITION_ORGAN_V1_20260720.md`
