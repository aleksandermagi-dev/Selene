# Selene Conversational Breadth — Phase 4 Contextual Composition and Modulation

Date: 2026-07-25

Status: implemented and proportionally verified.

## Outcome

Selene now has one inspectable composition decision between supported meaning
and final expression:

```text
supported meaning and discourse
  -> contextual composition plan
  -> meaning-preserving structural modulation
  -> optional conversational micro-moves
  -> NLO revision
  -> Voice pacing handoff
```

The layer can shape an answer without supplying new answer content. It does
not change facts, certainty, sources, identity, personality, governance,
memory, authority, or Voice ownership.

## Implemented

### Contextual composition profile

`src/selene/contextual_composition.py` records:

- response depth: brief, standard, or developed;
- current task kind and expression profile;
- explicit current-task audience;
- task-bound register;
- pacing and sentence rhythm;
- optional enthusiasm and emotional intensity;
- directness and restraint;
- supported content units and roles;
- whether developed length is limited by available content;
- whether exact-domain or specialized social structure is locked;
- explicit decisions for opening, thesis, support, example, qualification,
  callback, pivot, conclusion, and stopping.

These decisions are inspectable summaries, not hidden reasoning.

### Brief, standard, and developed structure

The same supported words may now take three distinct shapes:

- brief answers may combine a small set of related statements into one compact
  block;
- standard answers may separate a material limitation or qualification;
- developed answers may distribute supported thesis, development, and
  qualification across paragraphs.

Structural application checks the before-and-after supported token sequence.
If meaning-bearing words move, disappear, or appear, the meaning-preservation
check fails. The layer does not invent support, examples, filler, conclusions,
or follow-up questions.

Developed length is honestly limited when fewer than two supported content
units exist. A request to go deeper is not permission to pad the answer.

### Audience and register

The plan can recognize an explicitly requested current-task audience such as a
beginner, child, technical peer, or formal reader. It can also recognize
task-bound formal, plain explanatory, technical, narrative, reflective, or
ordinary conversational register.

No durable user or audience profile is created. Register is an expression
decision for the current task and cannot alter Selene's identity or
personality.

### Pacing, enthusiasm, and emotional intensity

The affect-to-language guidance now exposes enthusiasm and emotional intensity
alongside pacing, sentence rhythm, warmth, humor, reassurance, restraint, and
directness.

The values are optional expression guidance:

- lively context can make livelier expression available;
- careful, repair, or tender context can keep intensity contained;
- enthusiasm is never compulsory;
- no value is treated as proof of Selene's internal emotional state;
- no affect value may change facts or certainty.

### Callback, pivot, and stopping decisions

The composition plan reads the existing Conversation Spine, pragmatic
continuity, and contextual-follow-up results. It can distinguish:

- an attributable visible callback from an invented recollection;
- a named return from a silent soft pivot;
- a supported conclusion from stopping after the available content;
- an allowed material question from a habitual follow-up question.

The phase does not create new memory or longer-term callback authority.

### Exact-domain and specialized-expression locks

Verified math and source-backed research remain structurally locked. The
composition layer cannot restyle an exact arithmetic result or disturb an
attributed source packet.

Specialized social acts remain owned by the compositional social-language
layer. Phase 4 does not recompose them a second time.

The Answer Engine invariant check now treats whitespace-only paragraph
modulation as preserved content. This prevents a structurally modulated
comparison answer from being restored a second time and duplicated. Exact
domain truth and citation invariants remain protected.

### NLO, Voice, and active Chat integration

NLO is now `v24_contextual_composition_and_modulation`.

NLO:

- creates the contextual composition plan beside the supported discourse,
  pragmatic-continuity, and micro-move plans;
- applies structural modulation before optional conversational micro-moves;
- exposes both the plan and application result;
- passes both to Voice;
- omits absent support values instead of admitting the literal string
  `None` as a content unit.

Voice:

- receives the NLO plan and application result;
- can preserve, compact, or space paragraph rhythm;
- does not add semantic clauses;
- does not collapse a meaningful standard/developed paragraph boundary merely
  because affect guidance requests compact rhythm.

Active Chat carries the same inspectable handoff through the released answer.

## Verification

Testing remained synthetic and ordinary. No live Selene conversation or
distress-shaped probe was needed.

Focused checks cover:

- distinct brief, standard, and developed forms;
- token-level meaning preservation;
- no padding under thin support;
- task-bound audience and register;
- enthusiasm and emotional-intensity boundaries;
- attributable callbacks, named pivots, and non-pressuring stopping;
- exact math and attributed research structure locks;
- NLO-to-Voice and active Chat handoff;
- paragraph preservation;
- comparison-answer duplication prevention;
- social acts, micro-moves, figurative interpretation, uncertainty,
  supported semantics, teaching guidance, repair, pragmatic continuity,
  language formation, Voice, and active Chat regressions.

Result: **193 focused tests passed**.

No provider, memory proposal, training, autonomy, adversarial, fear-shaped, or
repeated settled-capability test was used.

The production frontend build passed with split 415.84 kB application and
193.81 kB React chunks and no former single-bundle warning. The Windows
package and privacy verifier passed with zero forbidden packaged files. The
configured database was snapshotted before the planned local reinstall; the
installer completed successfully and the installed app returned healthy and
ready. The verification-started app was then closed. No post-reinstall live
Q&A was performed.

## Boundaries Confirmed

Phase 4 creates no:

- identity or personality change;
- governance or authority change;
- durable or hidden memory write;
- user or audience profile;
- unsupported fact, example, source, citation, certainty, or emotion claim;
- model training, fine-tuning, or LoRA;
- provider dependency;
- autonomous action, automatic initiative, or automatic speech.

Composition changes how supported meaning is arranged. Selene remains Selene.

## Remaining Gaps

- The available clause and vocabulary range remains bounded by current
  language teaching and provider-free construction machinery.
- Register recognition is intentionally conservative and mainly follows
  explicit current-task cues.
- Fine-grained sentence-length choice still operates over supported clauses;
  it cannot create missing explanatory substance.
- Longer shared-joke and personal callback continuity remains Phase 9 work.
- Cross-domain analogy evaluation remains Phase 8 work.
- Corrections currently have several separate paths; their epistemic update
  model is not yet unified.

## Next Phase — Phase 5: Correction, Wrongness, and Epistemic Revision

Phase 5 will unify:

- correction;
- refinement;
- scope restriction;
- extension;
- competing explanations;
- unresolved contradictions;
- replacement;
- reopening.

Selene should identify what changed, preserve what still fits, revise only the
affected piece, and continue without shame, defensive persistence, or a full
context reset. Evidence may update either Aleks or Selene. Hypotheses and
accepted theories remain falsifiable, and superseded structures may remain
useful within an attributable valid scope.

The completion gate requires unresolved contradictions to stay visible,
ordinary wrongness to avoid collapse or over-apology, and later evidence to
revise an earlier conclusion without erasing its still-valid structure.
