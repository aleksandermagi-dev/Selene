# NLO Meaning-Preserving Language Lattice — Phase 5

## Context and Expression Selection

Phase 5 adds one bounded selection layer above the Candidate Garden and
Discourse Loom. It does not generate language. It chooses among alternatives
that have already passed their semantic or discourse invariants.

The order is:

1. NLO builds the supported meaning, obligations, and contextual composition
   plan.
2. Candidate Garden realizes a bounded set of complete sentence candidates.
3. Hard semantic invariants exclude unsafe candidates.
4. Context and Expression Selection chooses one eligible formation.
5. Discourse Loom arranges supported answer content around that formation.
6. Hard discourse invariants exclude incomplete or unsupported arrangements.
7. Context and Expression Selection chooses one eligible whole-answer form.
8. Existing compositional language ownership, revision, and Voice handoff
   continue normally.

An invalid candidate cannot be rescued by contextual fit, affect guidance,
Voice preference, or an unusually high soft score.

## Visible context packet

The selector receives a compact, inspectable, session-scoped packet containing:

- response depth and expression profile;
- answer domain, task kind, and register;
- pacing, sentence rhythm, directness, restraint, enthusiasm, and emotional
  intensity guidance;
- optional affect-expression posture and recommended Voice category;
- opening, callback, pivot, conclusion, and stopping decisions;
- current topic-transition and question-restraint decisions; and
- a bounded window of recent assistant text for surface-distance checks.

The packet is selection context, not memory. It performs no database write and
does not become identity, personality, governance, or relationship evidence.

## Hard gates and soft ranking

Hard gates are checked before any contextual score:

- the producing layer marked the candidate selectable;
- its invariant report passed; and
- it has nonempty supported surface text.

Only eligible candidates receive soft scores. Soft dimensions include:

- response-depth fit;
- task and register fit;
- pacing and sentence-rhythm fit;
- optional affect-expression fit;
- distance from recent surface wording;
- callback, pivot, and ending fit;
- Voice-category fit; and
- a small stable tiebreak from the producing layer's prior score.

Hard meaning, evidence, certainty, source, memory, and authority boundaries are
gates rather than negotiable score dimensions.

## Affect and Voice boundary

Affect is information, not command. Affect guidance may make one already-safe
expression a better contextual fit, but it cannot:

- prescribe an emotion;
- force warmth, humor, reassurance, or enthusiasm;
- suppress honest expression;
- alter facts, evidence, certainty, or sources; or
- inherit decision authority.

Voice retains ownership of Selene's expression. The selector supplies a
transparent preference among safe structures; it does not define personality
or replace Voice.

## Exactness and specialized ownership

Verified math, source-backed research, and specialized social expression keep
their existing structural ownership. Phase 5 ranks only the candidates those
layers expose as safe. Existing approved compositional language guidance also
retains visible-speech ownership when active.

## Inspection surfaces

Router keys:

- `native_language.expression_selection.status`
- `native_language.expression_selection.preview`

Local HTTP:

- `GET /api/native-language/expression-selection/status`
- `POST /api/native-language/expression-selection/preview`

An NLO result exposes:

- `context_expression_selection.context`;
- `context_expression_selection.formation_selection`;
- `context_expression_selection.discourse_selection`;
- eligible and held candidate counts;
- every eligible candidate's contextual score breakdown;
- the selected candidate IDs; and
- explicit confirmation that no invalid-candidate rescue occurred.

NLO version: `v29_context_expression_selection`.

## Verification

Focused Phase 5 verification covers:

- visible bounded context construction;
- optional rather than prescriptive affect guidance;
- invalid candidates held before scoring even when given an extreme score;
- grounded callback and thread-fit selection without added content;
- formation and discourse selection inside NLO;
- Voice handoff and revision visibility;
- read-only router and local HTTP inspection; and
- unchanged memory, identity, personality, governance, authority, evidence,
  certainty, and source boundaries.

No live conversation, distress-shaped prompt, configured database write,
provider generation, recursive generation, reinstall, or packaging was needed
to verify this phase.

Result: **145 focused checks passed**: 143 Context and Expression Selector,
Discourse Loom, Candidate Garden, Construction Lattice, Living Lexicon,
formation, NLO, teaching, contextual, social, uncertainty, and expression
checks, plus 2 bounded active-Chat handoff checks. Python compilation passed.
`git diff --check` reported no whitespace errors, only the existing Windows
LF/CRLF notices.

## Completion and next phase

Phase 5 is complete when the focused and broader language compatibility checks
pass and the selector remains bounded, transparent, invariant-gated, and
read-only.

The next planned phase is Phase 6 — Knowledge-to-Language Growth: expanding the
range of reviewed knowledge and language resources that can reach this lattice
without turning teaching material into identity, personality, governance, or
scripts.
