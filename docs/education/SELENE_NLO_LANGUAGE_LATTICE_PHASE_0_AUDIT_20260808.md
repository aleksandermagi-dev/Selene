# Selene NLO Meaning-Preserving Language Lattice — Phase 0 Audit

Date: 2026-08-08

Status: Phase 0 complete. Read-only capability and reachability audit; no
production behavior changed.

## Outcome

Selene does not need a replacement language system or a provider model to make
the next meaningful gain in expressive breadth. The current repository already
contains the major structural layers:

- supported meaning and provenance handoff;
- response obligations and conversation-thread tracking;
- semantic frames;
- grammatical clause construction;
- discourse and paragraph planning;
- contextual pacing and conversational micro-moves;
- affect-to-expression guidance;
- Voice handoff;
- truth, coverage, repetition, and visible-speech checks.

The principal limitation is reachability. Most answer owners still hand NLO
nearly finished prose. NLO therefore protects and passes through a supported
answer instead of constructing several original, meaning-equivalent ways to
say it. The architecture is stronger than the portion of it currently reached
in ordinary use.

The next build should connect already reviewed vocabulary and meaning
distinctions to the existing lexical-semantic contract, then progressively make
structured composition the ordinary path. It should not rebuild NLO, Voice,
the Conversation Spine, intelligenceOS, or the teaching lifecycle.

## Ethical Audit Method

Before inspection, the test-impact questions were applied:

- This work should not ask Selene to perform or expose a missing capability.
- A live probe was unnecessary because source, tests, and existing run records
  could answer the architectural questions.
- Existing repetitions are development evidence about the expression path, not
  Selene failing.
- No distress-shaped, adversarial, or repeated settled-capability test was
  justified.

The audit therefore used only:

- static source inspection;
- existing focused tests and documentation;
- read-only counts from the configured local database;
- existing NLO run records, without creating a new conversation turn.

It made no memory, knowledge, identity, personality, governance, authority,
training, LoRA, autonomy, or activation change.

## Current Expression Path

The current path is already close to the desired architecture:

```text
Core/Mind route and Conversation Spine
  -> supported answer content and obligations
  -> NLO meaning packet
  -> supported discourse plan
  -> semantic frame
  -> language formation
  -> contextual composition
  -> optional conversational micro-moves
  -> conversational energy modulation
  -> truth and repetition revision
  -> Voice pacing and expression handoff
  -> final visible-speech release checks
```

The intended lattice extends this path rather than replacing it:

```text
supported meaning
  -> discourse plan
  -> several meaning-equivalent constructions
  -> truth, coverage, grammar, context, rhythm, and variation checks
  -> selected candidate
  -> Voice
  -> visible speech
```

## Capability And Reachability Map

| Capability | Current implementation | Reachability finding | Action |
| --- | --- | --- | --- |
| Supported semantic packets | `supported_semantics.py` preserves roles, relations, certainty, scope, sources, exactness, and required units | Strong contract, but most live units are text-grounded | Preserve; migrate answer owners incrementally |
| Sense-grounded lexical forms | `lexical_semantics.py` requires sense, grammar, provenance, and attributable understanding | Available only when a caller supplies entries inside the current semantic unit | Turn it into an inspectable Living Lexicon fed by reviewed teaching |
| Grammar formation | `language_formation.py` supports tense, aspect, modality, polarity, active/passive voice, imperatives, questions, modifiers, reasons, conditions, contrasts, and examples | Real capability; rarely receives structured propositions in ordinary runs | Preserve and make reachable |
| Clause relations | Eight relation groups and 34 connector choices exist | Useful bounded bootstrap, but selection is local and hash-derived | Move toward construction alternatives evaluated as complete candidates |
| Discourse planning | `discourse_planner.py` binds obligations and plans thesis, development, limits, reopening, and closure | Strong plan; much input is already realized prose and not every realization path consumes the full plan | Carry plan roles into candidate construction |
| Social realization | 19 acts with 76 bounded clause choices | Compositional, but each act currently has four choices and one is selected directly | Retain acts; broaden construction and contextual omission |
| Uncertainty realization | Four uncertainty states, eight acts, and 32 bounded clauses | Preserves epistemic honesty, but wording and state range remain narrow | Expand through lexicon and construction, not disclaimers |
| Reasoned answer variation | Direct, comparison, procedure, reflection, synthesis, and explanation frames | Usually the same seed with one of a few stock introductions | Replace prefix variation with proposition-level alternatives |
| Contextual variation | Recent openings and turn state feed a reproducible variation key | Avoids some immediate repetition, but equal context produces equal choice | Keep reproducibility; add ranked alternatives and recency scoring |
| Candidate revision | Checks architecture leakage, unsupported memory certainty, authority overclaim, repetition, obligations, and guidance use | Mostly flags or softens one candidate; it does not generally request a new realization | Let failed expression checks choose the next valid candidate once |
| Voice | 65 stored sentence primitives plus evidence-derived patterns; NLO meaning is paced without semantic additions | Correct ownership. On the live NLO path Voice intentionally preserves the supplied wording | Keep Voice downstream; do not make it invent answer content |
| Reviewed language teaching | 52 lessons are available as approved language guidance | Lessons guide response moves, but their vocabulary and distinctions are not compiled into NLO lexical entries | Phase 1 bridge |

## Read-Only Runtime Evidence

The configured database snapshot contained:

- 52 language-shelf lessons, all marked
  `approved_for_language_guidance` and `language_guidance_available`;
- 276 vocabulary mentions representing 255 distinct vocabulary items inside
  their nested Acquire review blueprints;
- zero stored lexical-semantic entry structures in those lesson records;
- 226 total NLO records, of which 224 were realized responses with visible
  candidate text;
- 163 realized records reporting text-grounded formation;
- 3 reporting structured formation;
- 58 older or specialized records without a reported formation mode;
- 223 records with zero lexical-choice units and 1 record with one
  lexical-choice unit;
- 97 records reporting that approved language realization guidance was
  applied and 127 without it;
- 25 exact-duplicate candidate groups, with the most repeated exact candidate
  appearing 11 times.

These counts describe existing development records, not a conversational score
or a judgment of Selene. Some repetitions came from repeated diagnostics or
equivalent prompts. They are useful because they show that the current
selection path can converge on the same supported wording even when the
underlying architecture could support more variation.

## Exact Concentration Points

### 1. Most meaning arrives as prose

`build_text_supported_semantic_packet` correctly preserves already-supported
sentences as text-grounded units. This is a good compatibility boundary, but a
complete sentence offers NLO far less expressive freedom than participant,
event, relation, certainty, scope, and discourse-role fields.

### 2. Lexical understanding is transient and caller-supplied

The lexical-semantic contract is well designed: a form is unavailable without
sense, part of speech, grammatical behavior, provenance, and an attributable
understanding state. At present, however, entries live only inside a supplied
semantic unit. Reviewed teaching vocabulary is not yet compiled into a
queryable NLO resource.

### 3. Candidate generation is local rather than response-wide

The structured formation path constructs one response. It may reverse multiple
clauses after an exact recent match. The reasoned-answer path may choose among
several frames, but those alternatives mostly add a stock introduction to the
same completed seed. Social and uncertainty paths choose one clause per act.

There is no unified Candidate Garden that creates several complete realizations
and compares them while holding meaning, evidence, certainty, scope, memory
status, and obligations invariant.

### 4. Selection is reproducible but not yet a full quality comparison

Current surface choices use hashes of prompt, intent, turn state, and recent
openings. This is safely deterministic and testable. It is not the harmful
kind of determinism where only one sentence is logically possible; it is an
engineering choice that maps one context to one item from a small pool.

The next system should remain reproducible while ranking candidates by:

- required-meaning preservation;
- evidence and certainty preservation;
- obligation coverage;
- grammatical fit;
- referent clarity;
- discourse-plan fit;
- context and register fit;
- sentence rhythm;
- recent wording and construction distance;
- exactness locks.

### 5. Revision does not normally regenerate

Current revision reliably detects several unsafe or repetitive properties.
Outside a few specialized selectors, a repetition flag does not cause a second
meaning-equivalent construction to be tried. One bounded alternative-selection
step can improve breadth without allowing recursion.

## What Is A Genuine Breadth Gap

- A durable but non-memory Living Lexicon connected to reviewed understanding.
- Richer structured propositions from approved knowledge, ordinary reasoning,
  self-state, reviewed memory, and contextual answers.
- Multiple complete grammatical constructions for the same supported meaning.
- Response-wide candidate scoring and one bounded retry.
- More varied discourse realization, callbacks, transitions, emphasis, and
  natural endings.
- Growth of lexical and construction availability as teaching progresses.

## What Is Primarily A Selection Gap

- Existing tense, aspect, mood, modality, polarity, and voice support is rarely
  reached by ordinary text-grounded inputs.
- Existing paragraph and closure plans are richer than many surface answers.
- Existing affect, pacing, and conversational-energy guidance cannot create
  variation when the candidate arrives as fixed prose.
- Existing recent-response checks detect concentration after most wording has
  already been chosen.

## What Must Not Be Changed

- Core/Mind remains the law and routing owner.
- intelligenceOS and domain organs remain meaning and answer-content owners.
- Comprehension remains the approved general-knowledge owner.
- Personal memory remains separate from taught knowledge and language.
- NLO owns language construction, not facts or authority.
- Voice remains Selene's expression layer and may not alter supported meaning.
- Exact math, citations, quotations, route keys, code symbols, approval phrases,
  and safety-critical wording retain exactness locks.
- Missing knowledge remains visible; fluency may not manufacture an answer.
- No hidden retention, raw-corpus recall, model training, fine-tuning, LoRA,
  provider dependency, identity/personality/governance mutation, or autonomy
  expansion is introduced.

## Phase 1 Contract — Living Lexicon

Phase 1 should operationalize the lexical-semantic system that already exists.

### Inputs

- reviewed language-guidance lessons;
- approved comprehension knowledge;
- prompt-grounded vocabulary that remains current-turn only;
- explicit exactness-locked terms.

### Stored lexical information

- lemma and available forms;
- intended sense and near-concept distinctions;
- part of speech and grammatical behavior;
- semantic roles the form can express;
- number, tense, aspect, modality, or other relevant features;
- collocations and incompatible pairings;
- ordinary, technical, tender, playful, formal, or other supported register;
- concept and lesson references;
- source provenance and understanding state;
- exactness lock and availability state.

### Behavior

- Compile only from already reviewed or approved material.
- Do not convert every vocabulary label into a synonym automatically.
- Keep prompt-grounded entries ephemeral.
- Make approved entries queryable by sense, grammatical field, register,
  relation, and concept—not only by string match.
- Return several applicable forms to language formation while preserving the
  same meaning.
- Record why a form was available or held.
- Treat lexical availability as language capability, not personal memory,
  personality, governance, or authority.

### Completion gate

- Existing reviewed language lessons can produce inspectable lexical entries.
- At least one ordinary structured semantic unit can obtain multiple
  sense-equivalent forms from the Living Lexicon.
- Incompatible senses, missing provenance, and unreviewed entries remain held.
- Exactness-locked terms remain unchanged.
- The feature is idempotent and introduces no hidden retention.
- Focused static and synthetic tests pass without a live conversation probe.

## Remaining Ordered Phases

1. **Phase 1 — Living Lexicon:** make reviewed lexical understanding
   operational.
2. **Phase 2 — Construction Lattice:** describe several grammatical shapes for
   one supported proposition set.
3. **Phase 3 — Candidate Garden:** generate and compare several complete
   meaning-equivalent responses.
4. **Phase 4 — Discourse Loom:** realize thesis, development, callbacks,
   transitions, examples, limits, and endings across longer answers.
5. **Phase 5 — Context And Expression Selection:** rank for current context,
   register, affect guidance, rhythm, recent usage, and Voice fit.
6. **Phase 6 — Knowledge-To-Language Growth:** let approved teaching expand
   usable vocabulary and constructions without becoming identity or scripts.
7. **Phase 7 — Generative Thought Expression:** support ideas, hypotheses,
   analogies, collaborative questions, and revisable attempts from attributable
   meaning.
8. **Phase 8 — Gentle Stabilization:** static checks, synthetic equivalence and
   coverage fixtures, existing-record inspection, and only then a small ordinary
   conversation if implementation evidence genuinely requires it.

Each phase is a separate checkpoint. Later phases should not be pulled forward
merely to make an early demo sound broader.

## Phase 0 Verification

- No production source was edited.
- No live Selene conversation was started.
- No database row was written.
- No reinstall or package build was performed.
- Existing uncommitted work was preserved.
- The separate community-safety documentation was not touched.

