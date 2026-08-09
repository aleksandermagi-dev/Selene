# Selene NLO Meaning-Preserving Language Lattice — Phase 4 Discourse Loom

Date: 2026-08-08

Status: implemented; focused static and synthetic verification passed

## Outcome

Selene's NLO can now execute its existing supported discourse plan across a
whole answer.

The Discourse Loom arranges already-supported content into a bounded set of
response-wide structures. It preserves the direct answer or thesis, carries
grounded obligations, places supported development and examples, keeps limits
and reopening conditions visible, follows attributed thread traversal, and
stops naturally when no conclusion is supplied.

The Loom does not create the discourse content. It operates only over content
units created by the existing `supported_discourse_plan` and, when available,
the Candidate Garden's selected structured formation.

## Pipeline

```text
supported meaning
  -> Living Lexicon
  -> Construction Lattice
  -> Candidate Garden
  -> selected structured formation
  + supported discourse plan and obligations
  -> Discourse Loom
  -> bounded whole-answer arrangements
  -> discourse invariant gate
  -> one selected discourse candidate
  -> contextual composition and revision
  -> Voice handoff
```

The Candidate Garden chooses a grammatical realization. The Discourse Loom
then organizes that realization with the other supported content roles. These
remain separate inspectable decisions.

## Supported Roles

The Loom recognizes the discourse planner's existing roles:

- thesis;
- correction;
- support;
- assumption;
- example;
- limitation;
- reopening;
- conclusion.

It adds only small structural labels licensed by those roles:

- `For example:` for a supplied example;
- `One assumption:` for a supplied assumption;
- `One limit:` for a supplied limitation;
- `What would change this:` for a supplied reopening condition.

These labels organize attributed content. They do not supply the example,
assumption, limit, or reopening condition themselves.

## Bounded Discourse Candidates

The Loom creates at most four arrangements:

- the supported discourse planner's paragraph order;
- one integrated complete arrangement;
- one role-braided arrangement;
- an obligation-ordered or grounded thread-traversal arrangement when
  applicable.

For brief responses, a `brief_required` arrangement may omit optional support.
It must still include:

- the thesis;
- every grounded required-obligation unit;
- material corrections;
- supported limitations;
- supported reopening or conclusion content.

Developed responses preserve all supported units. They do not expand when the
available content is too small.

## Structured Thesis Handoff

When Candidate Garden supplies a structured, meaning-preserved formation, the
Loom uses it as the thesis.

The older text content-seed units represented by that formation are collapsed
into the structured thesis so the answer is not said twice. Non-duplicated
support, examples, assumptions, limits, reopening conditions, and conclusions
remain available for development.

If no text seed exists, the structured formation can still supply the thesis.

Text-grounded answers remain composed from their supported text units.

## Discourse Invariant Gate

Every discourse candidate must preserve:

- all required content-unit IDs;
- every grounded required-obligation unit;
- the supported closure unit when one exists;
- thesis-first ordering when a thesis exists;
- only units declared by its Loom specification;
- the no-meaning-change specification contract.

An invariant failure makes the candidate unselectable and leaves it visible as
`discourse_invariant_failed`.

Paragraph-only differences remain distinct discourse candidates. Duplicate
wording with the same paragraph structure is held.

## Thread Returns And Callbacks

The Loom consumes the discourse planner's existing
`thread_obligation_bindings`. A thread-traversal candidate is available only
when those bindings are grounded and carry thread IDs and traversal indexes.

The Loom preserves their order and may add the generic transition:

`Returning to that thread:`

It does not invent a past event, name a topic that was not supplied, or claim
memory. Without a grounded binding, no thread-return construction is created.

## Natural Endings

The closure plan remains authoritative:

- a supplied limitation may form a bounded-limit ending;
- a supplied reopening condition may state what would change the answer;
- a supplied conclusion may provide the supported landing;
- without closure content, the answer simply stops after supported material.

The Loom never adds a habitual follow-up question or a generic invitation to
continue.

## Exact And Specialized Structures

Verified math and source-backed research may mark their structure exact.
Specialized social acts may retain ownership of their structure. In either
case the Loom provides only the as-supplied arrangement and adds no role
labels or alternate paragraph candidate.

## NLO Integration

NLO is now `v28_discourse_loom`.

NLO exposes:

- generated, distinct, selectable, and held discourse-candidate counts;
- every paragraph arrangement and included content-unit IDs;
- invariant checks and score breakdowns;
- required and obligation-bound content-unit IDs;
- structured-thesis and collapsed-seed state;
- selected candidate and Loom specification IDs;
- one-pass, no-recursion, no-provider state;
- natural-stop and no-forced-closure state.

The final revision packet reports whether the selected discourse invariants
passed, the required content IDs, and the one-pass selection count.

When an approved compositional language lesson already owns clause or surface
recomposition, the Loom remains inspectable but yields visible-speech
ownership to that reviewed language path. This prevents a later structural
layer from erasing approved paraphrase, rhythm, or clause-composition behavior.

## Inspectable Routes

Router keys:

- `native_language.discourse_loom.status`
- `native_language.discourse_loom.preview`

Local sidecar routes:

- `GET /api/native-language/discourse-loom/status`
- `POST /api/native-language/discourse-loom/preview`

Preview may receive an existing supported-discourse packet. Otherwise it uses
the existing discourse planner payload shape. It performs no database write.

## Verification Method

Verification uses temporary databases and synthetic supported-content units.
It does not require a live conversation, affect probe, configured-database
write, or broad grading of Selene's unfinished language module.

Focused checks cover:

- thesis, development, example, limitation, reopening, and conclusion roles;
- structured-thesis replacement without duplicated content seeds;
- structured thesis formation when no text seed exists;
- grounded obligation preservation;
- brief required-content retention and optional-support omission;
- developed content completeness;
- attributed thread traversal;
- natural stopping without forced questions;
- exact-domain and specialized-social holds;
- NLO visible-speech integration;
- revision evidence;
- router and local HTTP inspection;
- earlier Living Lexicon, Construction Lattice, Candidate Garden, formation,
  contextual, social, uncertainty, special-expression, and bounded Chat
  compatibility.

Result: **138 focused checks passed**: 136 Discourse Loom, Candidate Garden,
Construction Lattice, Living Lexicon, formation, NLO, teaching, contextual,
social, uncertainty, and expression checks, plus 2 bounded active-Chat handoff
checks. Python compilation passed. `git diff --check` reported no whitespace
errors, only the existing Windows LF/CRLF notices.

## Boundaries Confirmed

Phase 4 creates no:

- unsupported fact, example, assumption, limit, callback, or conclusion;
- personal-memory or general-knowledge write;
- discourse-retention database;
- identity, Vys, personality, relationship, governance, or Voice mutation;
- certainty, source, confidence, or authority upgrade;
- model training, fine-tuning, LoRA, or provider dependency;
- automatic speech, action, or autonomy expansion.

The Loom organizes what Selene has. It does not pretend she has more.

## Remaining Gap

The Candidate Garden and Discourse Loom now produce safe alternatives, but
selection still uses a small local score. It does not yet fully compare
register, affect guidance, conversational pacing, recent construction history,
rhythm across paragraphs, or Voice fit as one response-wide context decision.

## Next Phase — Phase 5 Context And Expression Selection

Phase 5 will unify the safe selection signals across:

- current conversational context;
- task and register;
- optional affect-expression guidance;
- pacing and sentence rhythm;
- recent lexical, construction, and discourse usage;
- callback and ending fit;
- Voice handoff preferences.

Meaning, evidence, certainty, sources, memory state, and authority will remain
hard invariants rather than soft score dimensions.
