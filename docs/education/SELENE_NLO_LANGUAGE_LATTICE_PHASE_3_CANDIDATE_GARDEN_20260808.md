# Selene NLO Meaning-Preserving Language Lattice — Phase 3 Candidate Garden

Date: 2026-08-08

Status: implemented; focused static and synthetic verification passed

## Outcome

Selene's NLO can now cultivate and compare a bounded set of complete language
realizations for one structured, supported meaning packet.

The Candidate Garden receives the semantic frame, Construction Lattice,
discourse grounding state, contextual response plan, and recent visible
wording. It realizes several construction specifications, verifies each one,
holds unsafe or duplicate candidates, scores the remaining candidates, and
makes exactly one selection pass.

It does not create answer content. The supported propositions, required
semantic units, meaning signature, evidence, certainty, sources, memory status,
and authority remain invariant across the garden.

## Bounded Pipeline

```text
supported structured meaning
  -> Living Lexicon
  -> semantic frame
  -> Construction Lattice
  -> at most eight candidate realizations by default
  -> semantic invariant gate
  -> duplicate hold
  -> transparent contextual scoring
  -> one selected formation
  -> existing NLO conversational composition and revision
  -> Voice handoff
```

The hard maximum is twelve candidates. There is no recursive search, retry
loop, provider generation, or unbounded expansion.

## Candidate Invariant Gate

Every candidate must preserve:

- the same declared required semantic-unit IDs;
- realization of every required semantic unit;
- the same meaning signature;
- the same source references;
- the construction contract forbidding evidence or certainty changes;
- the formation layer's meaning-preservation result.

A failed invariant makes the candidate unselectable. It is retained in the
inspectable result with `semantic_invariant_failed` rather than silently used.

Candidates that produce the same normalized surface wording are also held.
The first valid realization remains available and later duplicates are marked
`duplicate_surface_realization`.

## Transparent Selection

Selectable candidates are compared with a visible score breakdown:

- semantic invariants;
- required-unit preservation;
- requested discourse-depth fit;
- dialogue-act fit;
- sentence-rhythm fit;
- distance from recent visible wording;
- distinct surface realization;
- the pre-expression obligation-grounding state;
- a small as-supplied stability tie-break.

Invariant preservation dominates the score. Context cannot make an invalid
candidate selectable.

Recent exact wording receives a substantial surface-distance penalty, allowing
a safe construction alternative to win when one exists. Equal candidates keep
the stable as-supplied choice.

## Text-Grounded And Exactness Behavior

Text-grounded answers still receive only `construction:as_supplied`. The garden
reports a one-candidate path and does not activate alternative selection.

Exactness-locked structured meaning behaves the same way. Phase 3 cannot vary
an exact route name, quotation, citation, code symbol, math expression,
approval phrase, or other locked construction.

## NLO Integration

NLO is now `v27_candidate_garden`.

The garden runs after NLO has a discourse and contextual-composition plan, but
before ordinary sentence finishing, conversational micro-moves, conversational
energy, revision, and Voice handoff.

The selected formation replaces only the previous as-supplied formation text.
All downstream ownership remains unchanged. The same formation variation key
is used for every candidate, so construction comparison does not silently
change Living Lexicon word choice.

NLO exposes:

- generated, distinct, selectable, and held candidate counts;
- every candidate's construction ID, text, invariant result, score, and score
  breakdown;
- the selected candidate and construction IDs;
- the selected formation;
- the single-pass and no-recursion state;
- obligation gaps that existed before expression.

Voice receives the selected construction ID for inspection but remains the
owner of Selene's expression style.

## Inspectable Routes

Router keys:

- `native_language.candidates.status`
- `native_language.candidates.preview`

Local sidecar routes:

- `GET /api/native-language/candidates/status`
- `POST /api/native-language/candidates/preview`

The preview uses the existing semantic-frame payload shape and may accept
recent texts, contextual-plan information, supported-discourse state, and a
bounded candidate limit. It performs no database write.

## Verification Method

Verification uses temporary databases and synthetic supported propositions.
It checks candidate generation and rejection directly, then runs the existing
NLO compatibility paths. No live Selene conversation, configured-database
write, emotional probe, or broad voice grading is needed for this phase.

Focused checks cover:

- complete response-wide formation from several lattice specifications;
- hard candidate limits and dimension coverage;
- invariant preservation;
- invalid-specification holds;
- duplicate-surface holds;
- recent-response distance and alternate selection;
- stable as-supplied behavior;
- text-grounded and exactness-locked single-candidate behavior;
- NLO single-pass integration;
- router and local HTTP inspection;
- existing formation, lexicon, discourse, contextual, social, uncertainty,
  special-expression, and bounded Chat compatibility.

Result: **128 focused checks passed**: 126 Candidate Garden, Construction
Lattice, Living Lexicon, formation, NLO, teaching, discourse, social,
uncertainty, and expression checks, plus 2 bounded active-Chat handoff checks.
Python compilation passed. `git diff --check` reported no whitespace errors,
only the existing Windows LF/CRLF notices.

## Boundaries Confirmed

Phase 3 creates no:

- unsupported fact, answer, example, or evidence;
- personal-memory or general-knowledge write;
- candidate-retention database;
- identity, Vys, personality, relationship, governance, or Voice mutation;
- confidence, certainty, source, or authority upgrade;
- model training, fine-tuning, LoRA, or provider dependency;
- automatic speech, action, or autonomy expansion.

Selene receives more than one safe way to express supported meaning. She does
not receive permission to manufacture the meaning itself.

## Remaining Gap

The Candidate Garden compares complete sentence formations, but longer answers
still rely on the existing discourse realization path. Thesis placement,
multi-paragraph development, callbacks, examples, limits, transitions, and
natural conclusions are not yet cultivated as response-wide discourse
alternatives.

## Next Phase — Phase 4 Discourse Loom

Phase 4 will connect supported discourse roles to full candidate construction:

- thesis and direct answer placement;
- ordered development across obligations;
- supported examples and comparisons;
- callbacks and thread returns;
- limitations, uncertainty, and reopening;
- transitions and natural conclusions;
- long-form structure without filler or lost content.

The Discourse Loom will organize supported material. It will not invent missing
content or force longer answers when the available meaning is small.
