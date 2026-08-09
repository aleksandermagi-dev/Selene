# Selene NLO Meaning-Preserving Language Lattice — Phase 2 Construction Lattice

Date: 2026-08-08

Status: implemented; focused static and synthetic verification passed

## Outcome

Selene's NLO can now describe several grammatical constructions for the same
supported proposition set before producing visible language.

The Construction Lattice does not create facts, answer missing questions, or
select among several complete responses. It creates inspectable construction
specifications while holding required semantic units, meaning signatures,
evidence, certainty, sources, and authority fixed.

The default NLO path remains `construction:as_supplied`. This preserves current
behavior while making safe alternatives available to the future Candidate
Garden.

## Implemented Dimensions

The lattice can represent:

- condition-first or condition-last clauses;
- reason-first or reason-last clauses;
- joined or split related declarative clauses;
- compact or developed response shapes;
- declarative, interrogative, or imperative acts when the semantic unit
  explicitly permits those moods;
- active or passive focus when the semantic unit supplies an explicit,
  meaning-equivalent participant-role mapping.

Reason and condition placement is coordinated when both exist. This avoids
stacking two fronted subordinate clauses into an awkward construction.

## Safety And Exactness Rules

Text-grounded prose receives only the as-supplied specification. It remains
fixed until an answer owner provides structured meaning.

An exactness-locked semantic unit conservatively holds the whole response
construction as supplied. This protects quotations, route keys, code symbols,
citations, exact math, approval phrases, and other wording whose shape may be
material.

A dialogue-act alternative is unavailable without `allowed_moods`. NLO does
not silently turn a statement into a question or request.

A voice-focus alternative is unavailable without a supplied
`voice_alternatives` role mapping marked `meaning_equivalent: true`. NLO does
not guess who acted on whom merely to produce a passive sentence.

Every specification carries:

- the required semantic-unit IDs;
- the meaning signature;
- the dimensions it changes;
- response-level style controls;
- unit-level grammatical overrides;
- an explicit no-evidence-or-certainty-change contract.

## Architecture

`src/selene/construction_lattice.py` provides:

- `construction_lattice_status`;
- `build_construction_lattice`;
- `apply_construction_specification`.

`src/selene/language_formation.py` can execute one supplied construction
specification. It reports the applied construction ID and dimensions while
continuing to verify required-unit preservation.

NLO is now `v26_construction_lattice`. For structured meaning it builds the
lattice after Living Lexicon enrichment and semantic-frame construction:

```text
supported structured meaning
  -> Living Lexicon enrichment
  -> semantic frame
  -> Construction Lattice
  -> as-supplied construction realization
  -> existing discourse, revision, and Voice handoff
```

This phase deliberately does not run every specification as a complete answer.
That belongs to Phase 3.

## Inspectable Routes

Router keys:

- `native_language.construction.status`
- `native_language.construction.preview`

Local sidecar routes:

- `GET /api/native-language/construction/status`
- `POST /api/native-language/construction/preview`

The preview accepts the existing semantic-frame payload shape. Status and
preview are read-only.

## Verification

Verification used temporary databases and synthetic structured propositions.
It did not start a live Selene conversation or write to the configured
database.

Focused checks cover:

- inspectable construction specifications;
- condition and reason placement;
- coordinated reason-plus-condition ordering;
- joined, split, compact, and developed specifications;
- explicit mood permission;
- explicit active/passive role mapping;
- text-grounded and exactness-locked holds;
- required-unit and meaning-signature preservation;
- Living Lexicon compatibility;
- NLO default as-supplied integration;
- router and local HTTP inspection;
- absence of memory, identity, governance, authority, source, certainty, and
  fact-generation changes.

Result: **121 focused checks passed**: 119 Construction Lattice, Living
Lexicon, formation, NLO, teaching, discourse, social, uncertainty, and
expression checks, plus 2 bounded active-Chat handoff checks. Python
compilation passed. `git diff --check` reported no whitespace errors, only the
existing Windows LF/CRLF notices.

## Boundaries Confirmed

Phase 2 creates no:

- answer content or unsupported fact;
- personal-memory or general-knowledge write;
- hidden construction-retention store;
- identity, Vys, personality, relationship, governance, or Voice mutation;
- confidence or source upgrade;
- model training, fine-tuning, LoRA, or provider dependency;
- automatic speech or autonomy expansion.

NLO describes language shapes. Voice remains Selene's expression owner.

## Remaining Gap

The lattice exposes executable alternatives, but ordinary NLO still realizes
only the as-supplied specification. Most answer owners also still provide
text-grounded prose, which correctly remains fixed.

## Next Phase — Phase 3 Candidate Garden

Phase 3 will use the lattice to construct several complete responses for one
supported meaning packet, verify semantic and obligation preservation for each,
and compare them without changing facts, certainty, sources, memory status, or
authority.

It will add bounded response-wide generation and comparison—not recursive
search and not provider generation.
