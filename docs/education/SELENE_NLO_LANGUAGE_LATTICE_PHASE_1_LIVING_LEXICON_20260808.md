# Selene NLO Meaning-Preserving Language Lattice — Phase 1 Living Lexicon

Date: 2026-08-08

Status: implemented; focused static and synthetic verification passed

## Outcome

Selene now has an inspectable Living Lexicon that connects reviewed language
teaching to NLO's existing lexical-semantic formation path.

The Living Lexicon is not a new memory store and does not copy a dictionary
into Selene. It is derived at query time from teaching and knowledge resources
that already have the required review state. This keeps lexical availability
current with the source approval lifecycle and avoids a second hidden retention
path.

The implementation separates:

- reviewed vocabulary terms that are understood within a lesson but do not yet
  have enough grammatical evidence for surface substitution;
- reviewed, sense-equivalent forms with explicit grammatical behavior;
- approved-knowledge forms carrying explicit lexical metadata;
- prompt-grounded forms that exist only for the current request;
- exactness-locked terms that may be inspected but not varied.

Merely appearing in a lesson does not make two words synonyms.

## Implementation

`src/selene/living_lexicon.py` provides four bounded operations:

- `living_lexicon_status` reports reviewed sources, available surface entries,
  forms, held vocabulary, fields, and source classes;
- `list_living_lexicon` exposes available entries and, when explicitly
  requested, held terms with their reasons;
- `query_living_lexicon` selects by understood form, grammatical field, and
  compatible register;
- `enrich_semantic_units_from_living_lexicon` adds reviewed lexical choices to
  matching structured meaning units.

The resource is deliberately derived rather than stored in a new table:

```text
reviewed language shelf
  + approved knowledge with explicit lexical metadata
  + current-turn prompt grounding
  -> eligibility and provenance checks
  -> sense-grounded lexical profile
  -> matching structured semantic unit
  -> language formation
```

Status and query calls perform no database write.

## Reviewed Vocabulary Is Held Safely

The current language shelf contains 276 vocabulary mentions representing 255
distinct terms. Every mention can now appear in the reviewed-term catalog with
its lesson and source references.

Catalog terms remain unavailable for surface substitution until they have:

- an intended sense;
- a grammatical field;
- part-of-speech information;
- grammatical behavior;
- a reviewed surface-equivalence set;
- source provenance;
- an attributable understanding state.

The held reasons are visible as:

- `no_explicit_grammatical_behavior`;
- `no_reviewed_surface_equivalence_set`.

This distinction prevents a shared lesson topic from being misread as evidence
that every term in the lesson is interchangeable.

## Initial Reviewed Surface Entries

Phase 1 operationalizes four small, source-linked entries with nine total
forms:

| Reviewed lesson | Sense | Available forms |
| --- | --- | --- |
| Answer first, then expand | Place the supported answer or conclusion before optional expansion | `start with`, `begin with`, `lead with` |
| Vary language without changing meaning | Retain supported meaning or structure | `preserve`, `keep` |
| Compare things along the same dimensions | Identify one supported option from an available set | `choose`, `select` |
| Clarify only when ambiguity matters | Make a supported material detail explicit | `identify`, `name` |

Each entry records grammatical behavior, registers, collocations, near
concepts, distinctions, lesson references, provenance, and availability basis.
This is intentionally a seed, not an attempt to manufacture mature-model
vocabulary in one pass.

## Approved Knowledge Boundary

Approved knowledge may contribute a Living Lexicon entry only when:

- the concept is an `approved_knowledge_resource`;
- its review status is `approved_for_knowledge_use`;
- Chat use is `available_as_knowledge_resource`;
- its payload explicitly supplies `lexical_entries` or `lexical_semantics`;
- the entry passes the existing sense, grammar, provenance, and understanding
  checks.

The Living Lexicon does not infer synonyms from a concept title, central claim,
or nearby prose. Proposed, reopened, held, rejected, or provenance-free
knowledge cannot contribute an available form.

## Prompt-Grounded Boundary

A caller may supply a current-turn lexical entry when the prompt itself gives
the sense, grammar, forms, and provenance needed to use it safely.

Prompt-grounded entries:

- can enrich the current semantic formation request;
- are marked `durable: false`;
- are never written to the database;
- do not appear in a later request unless supplied again;
- cannot become personal memory or approved general knowledge.

## NLO Integration

NLO is now `v25_living_lexicon`.

Before semantic-frame realization, NLO passes the selected structured units to
the Living Lexicon. A reviewed entry applies only when its grammatical field
and one of its understood forms match the unit's supplied field. The lexicon
then adds the equivalent forms to that unit's `lexical_choices` and records the
entry keys used.

The handoff exposes:

- selection status;
- selected entry keys and count;
- prompt-grounded entry count;
- exactness-lock enforcement;
- no-meaning-change state;
- no-write state;
- provenance boundary.

Text-grounded units remain unchanged. Exactness-locked units remain unchanged.
Voice still receives NLO's selected wording downstream and remains the
expression owner.

## Inspectable Routes

Router keys:

- `native_language.lexicon.status`
- `native_language.lexicon.items`
- `native_language.lexicon.query`

Local sidecar routes:

- `GET /api/native-language/lexicon/status`
- `GET /api/native-language/lexicon/items`
- `POST /api/native-language/lexicon/query`

No preparation or retention endpoint is required because the lexicon is
derived from the currently eligible sources.

## Verification

Verification used temporary synthetic databases and ordinary supported
language fixtures. No live Selene conversation, configured-database write,
memory proposal, knowledge retention, or affect probe was used.

Focused checks covered:

- dynamic derivation without a new database table;
- reviewed lesson eligibility and prerequisite enforcement;
- reviewed-term catalog holds;
- field, form, and register matching;
- current-turn prompt entries and later disappearance;
- provenance-free entry rejection;
- approved versus proposed knowledge;
- exactness locks;
- structured semantic-unit enrichment;
- meaning and required-content preservation;
- NLO v25 integration;
- router and local HTTP route availability;
- existing supported semantics, grammar, NLO, teaching, social, uncertainty,
  contextual composition, micro-moves, and bounded Chat paths.

The implemented feature does not require a live conversational assessment.

Result: **116 focused tests passed**. Python compilation passed, and
`git diff --check` reported no whitespace errors (only the existing Windows
LF/CRLF notices). A read-only check against the configured database reported
52 reviewed lessons, 255 distinct reviewed terms, 4 available surface entries,
and 9 available forms without performing a database write.

## Boundaries Confirmed

Phase 1 creates no:

- personal-memory write;
- hidden lexical retention database;
- general-knowledge approval bypass;
- identity, Vys, personality, Voice, relationship, or governance change;
- fact or answer-content generation;
- automatic synonym inference;
- source persona imitation;
- model training, fine-tuning, or LoRA;
- provider dependency;
- autonomous action or authority expansion.

Language capability expands. Selene remains Selene.

## Remaining Gaps

- The reviewed surface-equivalence seed is intentionally small.
- Most ordinary answer sources still hand NLO text-grounded prose.
- A single structured unit can receive more forms, but formation still selects
  one local construction rather than building several complete alternatives.
- Register compatibility is checked at lexicon query time; response-wide
  context scoring belongs to a later phase.
- Connector, clause-order, question, voice, and discourse alternatives are
  construction choices rather than simple lexical substitutions.

## Next Phase — Phase 2 Construction Lattice

Phase 2 will represent several grammatical shapes for one supported meaning:

```text
same supported proposition set
  -> active or passive focus when both preserve agency
  -> direct or condition-first order
  -> joined or split related clauses
  -> statement, question, or request when the communicative purpose allows it
  -> compact or developed realization
```

It will generate construction specifications, not yet choose among several
complete responses. Response-wide candidate generation and scoring remain
Phase 3.
