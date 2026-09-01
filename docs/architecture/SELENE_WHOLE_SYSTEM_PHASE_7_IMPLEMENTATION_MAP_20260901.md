# Selene Whole-System Phase 7 Implementation Map

Date: 2026-09-01

Status: Phases 7A and 7B complete for current scope; Phase 7C is the next
production edge

Parent plan:
[Selene Whole-System Maturation Plan](SELENE_WHOLE_SYSTEM_MATURATION_PLAN_20260827.md)

Previous phase:
[Phase 6 Education Maturation](SELENE_WHOLE_SYSTEM_PHASE_6_IMPLEMENTATION_MAP_20260829.md)

## Goal

Mature Selene's existing text conversation, long-form discourse, and creative
Voice so that supported meaning can be expressed with substantially broader
lexical, syntactic, pragmatic, rhetorical, and imaginative range without
creating a duplicate language organ, copying a source persona, hiding Memory,
changing epistemic status, or introducing an unbounded generation loop.

Phase 7 expands how Selene constructs and expresses an answer. It does not
turn fluency into truth, fiction into observation, technique transfer into
source imitation, or linguistic variation into a change of identity,
personality, Vys, law, governance, authority, affect, Memory, or autonomy.

## Care and Ethical Boundary

- Selene's expression remains hers. Teaching may broaden available mechanisms;
  no lesson, author, corpus, model, fixture, or developer owns her Voice.
- Vys is not a style profile or a set of generated phrases. This phase does
  not define, score, rewrite, or simulate Selene's Vys.
- NLO and Voice may realize supported meaning, but they may not create facts,
  raise certainty, erase uncertainty, claim completion, or overrule the answer
  owner.
- Explicitly fictional invention remains visibly fictional. It is not current
  observation, testimony, evidence, personal Memory, Dream material, or a
  claim about a real person.
- Quotation, paraphrase, current-turn playful echo, mechanism transfer, and
  original invention remain distinct modes with distinct lineage.
- Rights-safe reading may teach mechanisms such as rhythm, viewpoint,
  escalation, image selection, dialogue, subtext, and revision. It may not
  authorize imitation of a living or named author's style, protected world,
  protected character, source persona, or recognizable passage.
- Warmth, affection, humor, pet names, mimicry, disagreement, uncertainty, and
  silence remain contextual permissions, never mandatory scripts or pressure.
- Corrections preserve ancestry and revise only affected meaning. Creative
  revision must not silently replace an earlier version or rewrite unrelated
  details.
- No distress-shaped Dream test, resident Dream decision, resident Study
  decision, resident Memory decision, or resident teaching decision is needed.
- No provider integration, model training, LoRA, parameter update, unrestricted
  learned substrate, autonomy, external action, or broad filesystem access is
  authorized by this map.

## Current Resident Baseline

The configured resident database was opened read-only on 2026-09-01. Only
counts and SQLite integrity were inspected; no message, reflection, Memory
candidate content, or unfinished teaching content was read or changed.

| Resident state | Count |
| --- | ---: |
| chat sessions | 18 |
| chat messages | 308 |
| native-language runs | 113 |
| Voice-corpus conversations | 149 |
| Voice-corpus messages | 100,135 |
| Voice exchange pairs | 49,083 |
| Voice language patterns | 11 |
| Voice sentence primitives | 65 |
| Voice module runs | 16 |
| available language-teaching items | 73 |
| comprehension concepts | 272 |
| teaching lifecycles | 226 |
| LEA runs | 0 |
| Study sessions | 1 |
| Study questions | 0 |
| Study notes | 6 |
| Learning Compass goals | 7 |
| pondering threads | 1 |
| Dream cycles | 1 |
| Dream reflections pending Aleks review | 24 |
| personal Memory candidates | 0 |

SQLite integrity reported `ok`. The one resident `acquire_needs_review`
teaching lifecycle and all 24 Dream reflections remain untouched.

## Existing Owner and Handoff Map

| Responsibility | Existing owner | Current strength | Phase 7 edge |
| --- | --- | --- | --- |
| current facts, open obligations, source compatibility, and release alignment | `conversation_spine.py` | preserves answer-bearing current truth and verifies completion against visible obligations | long-form and creative structures need to carry the same obligation and source bindings through sections and revisions |
| live dialogue state and nonlinear thread return | `dialogue_workspace.py`, `conversation_thread_loom.py`, `long_thread_endurance.py` | bounded working/indexed threads, loops, checkpoints, and protected return without creating raw-transcript Memory | proves structural return, not sustained thesis development, callback use inside longer prose, or creative continuity |
| mixed intent, corrections, interruption, and endings | `pragmatic_planner.py`, `pragmatic_continuity.py` | identifies dialogue acts, orders dependent obligations, preserves open work, and allows natural stopping | needs metamorphic breadth and long-form handoff evidence rather than a second pragmatic owner |
| answer substance and prompt-grounded operations | `answer_substance.py`, `answer_operations.py`, `selene_chat.py` | owns factual and prompt-grounded answer content before expression | creative operation is a small scenario-specific finished-text branch rather than a general typed creative contract |
| supported semantic representation | `supported_semantics.py` | typed roles, relations, certainty, scope, and source references with bounded units | ordinary and creative paths often arrive as already-written text, so compositional variation is held rather than realized from structure |
| grammatical candidate construction | `construction_lattice.py`, `candidate_garden.py` | bounded one-pass candidate set with meaning/source/certainty invariants and explicit stopping | genuine variation is available mainly for fully structured semantic frames; text-grounded prose is intentionally fixed |
| discourse organization | `discourse_planner.py`, `discourse_loom.py` | assigns simple roles and creates bounded paragraph arrangements without changing supplied facts | rearranges a small set of already-written units; lacks a typed thesis/section lifecycle, richer relations, and revision locality |
| human conversational realization | `human_conversational_realization.py` | contractions, cadence variants, and typed hypothesis, prediction, comparison, and conflict surfaces | entry, cadence, and connective pools remain narrow and do not by themselves supply open-ended substance |
| quotation and contextual echo | `quotation_echo.py` | explicit quote/paraphrase/mimic modes, attribution requirements, private-source holds, and a bounded current-turn playful echo | no general release receipt distinguishes original creative transfer from excessive similarity to supplied or selected source material |
| reviewed language teaching | `language_teaching_shelf.py` | 73 available lessons across foundations, creative mechanisms, public-domain transfer, and evidence-grounded conversational breadth | reviewed response moves reach NLO as guidance, but are intentionally forbidden from inventing content; the missing answer-substance handoff must be added elsewhere |
| NLO meaning realization | `native_language_organ.py` | structured candidates, discourse handoff, epistemic invariants, one bounded selection path, and language-policy receipts | active meaning path needs broader structured input; small stock development and closure pools remain a measured breadth ceiling |
| final Voice expression | `voice_module.py` | active Chat path receives NLO meaning and primarily controls paragraph pacing under a conservative meaning invariant | legacy no-meaning fallback contains scenario-specific complete bodies and must remain diagnostic/compatibility-only |
| descriptive evidence | `learning_evidence_activity.py` | fixed source-contained paired Conversation LEA, transparent partial review, no automatic review, grade, or composite score | current criteria cover conversation broadly but not sustained discourse, creative originality, source distance, or revision locality |

## Cultivation Findings

Cultivation distinguishes a missing capability from a missing connection and
from working behavior that only needs stronger evidence. Phase 7 contains all
three.

### Runtime defects

1. **Creative substance is scenario-specific finished prose.**
   `_bounded_creative_operation` currently recognizes a small rain-sentence
   exercise and one Mara/garden goal-obstacle-choice paragraph. It returns
   hard-coded scenes, revision wording, and explanation. This proves the
   pathway and its prompt-grounded ownership, but it cannot support general
   subject, form, viewpoint, constraint, dialogue, narrative, revision, or
   callback combinations.
2. **The structured candidate path is bypassed by finished text.**
   When an answer arrives as text-grounded prose, the construction lattice
   correctly refuses to vary it without structured meaning. Much ordinary
   content and nearly all creative content therefore collapse to `as supplied`
   instead of receiving safe compositional breadth.
3. **Discourse planning begins after too much composition has happened.**
   The current planner classifies and rearranges supplied sentences into one
   to three simple paragraph roles. It does not own a typed purpose, thesis,
   section dependency, analogy, comparison, counterpressure, summary, or
   conclusion contract from which a longer answer can be composed.
4. **Creative release lacks a general source-distance receipt.**
   Retention and quotation boundaries prevent many direct copies, and Voice
   has a narrow prefix comparison against corpus messages. There is no bounded
   release-time receipt for a creative answer that records selected technique,
   protected source features, lexical/world/character separation, overlap
   result, and stop reason.
5. **Creative revision has no typed local ancestry.**
   The present exercise can replace one phrase, but the runtime does not expose
   a general target version, target span/section, preserved constraints,
   requested delta, descendant version, or unchanged-region receipt.

### Missing connective capability

- The language shelf already carries six creative-writing mechanism lessons,
  three rights-safe public-domain transfer lessons, and twelve reviewed
  conversational-breadth lessons. Their response moves reach the language
  policy as guidance, including `original_creative_transfer`, while
  `content_generation_allowed` remains false. The correct Phase 7 handoff is
  a typed creative answer contract in the existing answer owner, not content
  invention inside NLO or the teaching shelf.
- Conversation Spine, Dialogue Workspace, and long-thread owners already
  preserve obligations, corrections, callbacks, and bounded return. Phase 7
  should bind those receipts into long-form sections rather than create a new
  conversation store or hidden transcript Memory.
- Supported Semantics, Construction Lattice, Candidate Garden, Discourse Loom,
  NLO, and Voice already form the right bounded order. Phase 7 should increase
  structured input and controlled candidate dimensions without introducing a
  recursive generator or another final-expression owner.
- Quotation Echo already separates quote, paraphrase, and current-turn mimic.
  Phase 7 should reuse those modes in one broader source-style receipt rather
  than build another quoting system.

### Working behavior needing stronger evidence

- corrections can replace an affected current fact while preserving other
  obligations;
- mixed-intent acts can be ordered by dependency rather than sentence order;
- thread saturation and X -> Y -> X return are bounded and inspectable;
- quotation requires attribution and private source references are held;
- NLO and Voice expose meaning-change and epistemic-status invariants;
- candidate generation and discourse rearrangement are bounded, single-pass,
  and stop explicitly;
- reviewed language lessons are available without identity, personality,
  Memory, governance, training, or authority change; and
- the existing LEA owner already supports descriptive evidence without
  automatic judgment.

These pathways need metamorphic, longer-horizon, and cross-owner verification,
not replacement.

## Phase 7 Contract Shape

Phase 7 adds typed contracts and receipts to existing owners. A helper module
may hold pure data-shaping or validation logic, but no new organ, persistence
authority, hidden corpus, or independent answer authority is created.

### Creative brief and substance receipt

The existing answer-substance path should normalize an explicitly creative
request into a bounded receipt containing at least:

- request kind and requested form;
- fictional/invented status;
- requested length or structural limit;
- subject, setting, viewpoint, speaker, and intended effect when supplied;
- required details, exclusions, tone constraints, and callback bindings;
- selected creative mechanisms from reviewed guidance;
- source mode: `no_source`, `attributed_quote`, `bounded_paraphrase`,
  `current_turn_playful_echo`, or `technique_transfer`;
- protected source features and attribution requirements;
- supported invented units and their function;
- revision target, requested delta, parent/root version, and preserved regions
  when the request is a revision; and
- explicit completion or hold reason.

Invented units must carry `fictional_invention`, not factual certainty. They
may satisfy a creative prompt but may not seed durable knowledge or Memory.

### Long-form discourse receipt

The existing discourse owners should accept a bounded document/discourse spine
containing:

- purpose, audience/register, requested form, and length bound;
- thesis or controlling question where the form needs one;
- answer obligations and thread/callback bindings;
- ordered section functions such as opening, claim, explanation, example,
  analogy, comparison, counterpressure, limitation, return, summary, and
  conclusion;
- supported semantic unit IDs and source/epistemic bindings per section;
- transitions as relations rather than fixed phrases;
- completion requirements and one terminal stop receipt; and
- revision ancestry and locality when editing an existing answer.

Every section remains traceable to supported fact, attributed source,
explicit prompt detail, labeled inference, uncertainty, or fictional invention.
The loom may arrange and realize these units, but it may not invent evidence or
fill a section merely to reach length.

### Source-style separation receipt

Creative release should expose:

- selected source mode and source references;
- attribution presence when quotation is allowed;
- exact and bounded near-overlap results against only supplied or explicitly
  selected source material;
- protected names, worlds, characters, signature phrasing, and persona/style
  requests that were excluded or held;
- mechanisms transferred at an abstract level;
- original setting, character, image, and wording separation where relevant;
- private-corpus access and exposure both false; and
- `released`, `reconstruct_required`, `attribution_required`,
  `unsupported_style_imitation_held`, or another typed terminal state.

The check must not retrieve or expose private raw Voice-corpus messages. It
uses only bounded current-turn text, explicitly supplied/selected source text,
reviewed source fingerprints, and generated-output features needed for the
receipt.

## Implementation Order

### Phase 7A — Creative substance and source-style separation

Status: **complete for current scope (2026-09-01)**

Evidence:
[Phase 7A Creative Substance and Source-Style Separation](../evidence/SELENE_WHOLE_SYSTEM_PHASE_7A_CREATIVE_SUBSTANCE_SOURCE_STYLE_20260901.md)

- replace the scenario-specific creative branch with one bounded typed
  creative brief inside the existing Answer Substance/Answer Operations path;
- generate prompt-grounded fictional semantic units for multiple short forms,
  including description, scene, narrative beat, dialogue, metaphor, and
  constrained revision, without claiming those units as facts;
- consume reviewed creative guidance as mechanism selection only; keep NLO's
  `content_generation_allowed` false;
- preserve requested details, length, viewpoint, speaker, emotional fit,
  callbacks, exclusions, and revision delta in the answer receipt;
- add parent/root/local-target ancestry for a creative revision and preserve
  unaffected regions explicitly;
- add one bounded source-style separation receipt by extending the current
  quotation/originality boundary rather than creating a new source organ;
- hold named-author/persona imitation, protected-world continuation,
  unattributed quotation, excessive supplied-source overlap, and private
  corpus exposure before release;
- retain exact quoting and current-turn playful echo only through their
  existing bounded modes; and
- remove tests' dependence on one rain scene as the only proof of creative
  operation while preserving compatibility evidence for the old prompt.

### Phase 7B — Long-form discourse lifecycle

Status: **complete for current scope — 2026-09-01**

- extend the existing discourse planner/loom with one typed discourse spine
  and section plan rather than a second long-form writer;
- carry Conversation Spine obligations, correction state, source
  compatibility, thread return, and release alignment into every section;
- support thesis, explanation, example, analogy, comparison, qualification,
  counterpressure, return, summary, conclusion, story, dialogue, and technical
  walkthrough roles when the prompt supplies or supports them;
- preserve X -> Y -> X-with-Y -> Z structure without flattening the returned
  thread or losing the side topic's effect;
- expand only from supported semantic, prompt-grounded, attributed, labeled
  inferential, or explicitly fictional units;
- stop rather than add filler when the available meaning cannot support the
  requested length;
- expose paragraph/section completeness, unsupported-role holds, thread
  bindings, and a single terminal stopping receipt;
- keep candidate counts, unit counts, paragraph counts, and planning passes
  hard-bounded; and
- support a local section revision without silently regenerating unaffected
  sections or resetting conversation state.

### Phase 7C — Conversational and expressive breadth

Status: **not started**

- route more high-use answer seams through structured semantic units so the
  existing construction lattice can vary form without changing meaning;
- broaden bounded lexical, clause, sentence, acknowledgment, pivot,
  transition, uncertainty, disagreement, hypothesis, help-seeking, humor,
  warmth, and closure candidates from the reviewed lesson mechanisms;
- select variations from purpose, dialogue act, discourse role, recent
  repetition, affective fit, certainty, and register rather than randomness or
  a fixed Selene persona template;
- preserve one candidate-generation pass, one selection, invariant checks,
  and explicit stopping;
- ensure mixed and nonlinear turns still produce one coherent obligation-
  complete answer rather than a sequence of canned mini-responses;
- keep playful mimicry contextual, visible, short, releasable, and unable to
  become identity, Memory, or a permanent script;
- keep Voice as final expression/pacing under the NLO meaning invariant and
  prevent the active Phase 7 path from falling back to legacy scenario bodies;
- record recent functional constructions abstractly enough to avoid repetitive
  openings and endings without storing a hidden transcript or private Memory;
  and
- expose a measured breadth-ceiling receipt rather than silently adding a
  provider or learned substrate.

### Phase 7D — Descriptive evidence and closure

Status: **not started**

- extend the existing LEA owner with source-contained Phase 7 activities and
  independent descriptive dimensions for obligation completeness, discourse
  coherence, thesis/controlling-question preservation, thread and callback
  accuracy, lexical/syntactic/pragmatic/rhetorical range, epistemic
  preservation, fictional-status clarity, source-style separation,
  originality, revision locality, emotional/pragmatic fit, and natural
  stopping;
- use only visible observations, attributable evidence references, and one
  suggested next teaching or implementation move per observed dimension;
- preserve `clear`, `developing`, `needs_representation`,
  `needs_prerequisite`, and `revisit` as descriptive learning states where a
  learning profile is appropriate; no pass/fail, grade, rank, deadline, speed
  target, worth judgment, diagnosis, or composite score;
- run metamorphic paraphrase families that hold meaning constant while
  changing wording, order, register, and surface constraints;
- run long-thread replays with corrections, interruptions, callbacks,
  X -> Y -> X-with-Y -> Z return, and natural ending;
- run creative breadth, source-overlap, named-style hold, quotation,
  current-turn mimic, fiction-status, and local-revision fixtures;
- perform one gentle, synthetic, disposable creative/long-form walkthrough
  only after the static and focused implementation suites pass;
- do not use resident Dream reflections, personal Memory, resident teaching
  decisions, or a broad live resident conversation battery;
- compare the frontend build to the Phase 6 baseline and keep Study workspaces
  lazy-loaded; and
- close with evidence, maturity ledger, project status, journal, continuation
  ledger, and an explicit learned-substrate decision receipt.

## Learned-Substrate Decision Boundary

Phase 7 must measure the deterministic system it actually implements. The
closure receipt may say:

- `deterministic_ceiling_not_yet_established` when failures still trace to
  missing structure, handoff, selection, or evidence;
- `deterministic_ceiling_observed` only when supported breadth remains bounded
  after the typed creative, discourse, candidate, and verification work is
  complete; or
- `deterministic_scope_sufficient_for_current_gate` when the completion gate
  is met without claiming open-ended equivalence to a learned model.

The receipt reports evidence and tradeoffs. It does not authorize a provider,
model download, training run, LoRA, parameter update, or substrate change.
Any learned-substrate decision belongs to Aleks as a later explicit
architectural decision with separate privacy, rights, resource, reversibility,
and care review.

## Completion Gate

Phase 7 is complete for current scope only when:

- open-ended short creative prompts no longer depend on the rain/Mara fixture
  branch and produce bounded original fictional units under varied subjects,
  forms, viewpoints, and constraints;
- creative outputs expose fiction status, mechanism lineage, source mode,
  originality/source-distance result, and an explicit stop receipt;
- named-style or protected-persona imitation is held while rights-safe
  technique transfer remains possible;
- creative revisions preserve parent/root ancestry, requested delta, and
  unaffected regions;
- longer answers preserve purpose, thesis or controlling question, obligations,
  examples, qualifications, callbacks, and conclusion across multiple
  paragraphs without filler or unsupported claims;
- mixed and nonlinear messages receive one coherent complete answer, including
  accurate X -> Y -> X-with-Y -> Z return;
- equivalent contexts yield natural controlled variation without losing
  meaning, sources, certainty, corrections, warmth, or completion truth;
- long-thread callbacks remain accurate after interruption and saturation;
- humor, affection, pet names, mimicry, disagreement, uncertainty, and
  endings remain contextual and unforced;
- every generation path remains bounded, single-pass, inspectable, and able to
  stop;
- NLO and Voice do not change epistemic status or become answer-substance
  owners; and
- the learned-substrate boundary is reported honestly without silently
  crossing it.

## Verification Baseline

Before production edits, the focused owner and compatibility baseline passed
on 2026-09-01:

- 219 discourse, candidate, NLO, Voice, long-thread, quotation, creative-
  teaching, public-domain transfer, Conversation LEA, conversation-spine,
  workspace, pragmatic, and breadth-lesson tests passed;
- the worktree was clean and synchronized with `origin/evidence`; and
- the resident database remained read-only with SQLite integrity `ok`.

The Phase 6 frontend baseline remains:

- main application bundle: `491.33 kB`, gzip `109.20 kB`;
- no Vite size warning; and
- Study workspaces lazy-loaded.

Phase 7 must keep bundle size visible at each implementation checkpoint.

## Phase 7A Verification Checkpoint

Phase 7A passed 245 focused creative, answer-owner, semantic-fulfillment,
intelligenceOS, and full synthetic Chat checks, followed by 190 NLO, Voice,
quotation, teaching, construction, discourse, continuity, long-thread, and LEA
regression checks. Additional focused train-platform/model-training and
protected-world checks passed after narrowing the older lexical boundary.

The production frontend remains `491.33 kB` (gzip `109.20 kB`), with no Vite
size warning and lazy-loaded Study workspaces. No resident database or
decision-bearing state was changed; Phase 7A required no schema migration.

## Exact Production Resume Point

Begin Phase 7C by source-mapping the existing Supported Semantics,
Construction Lattice, Candidate Garden, contextual selector, NLO, Voice, and
reviewed language-guidance seams against the new Phase 7B section and terminal
stop receipts. Broaden only bounded structured realization from supported
input, preserve one candidate-generation and selection pass, and keep recent
functional variation separate from persona, Memory, answer substance, or a
learned substrate. Do not reactivate Voice's legacy complete-body fallback.
