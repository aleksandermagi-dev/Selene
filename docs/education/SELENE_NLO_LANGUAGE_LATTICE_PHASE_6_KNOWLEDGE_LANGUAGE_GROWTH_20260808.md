# NLO Meaning-Preserving Language Lattice — Phase 6

## Knowledge-to-Language Growth

Phase 6 connects approved teaching to the completed language lattice through a
read-only, provenance-gated growth handoff.

It addresses a specific missing bridge: approved knowledge could already seed
an answer, and explicit lexical metadata could already reach the Living
Lexicon, but NLO could not inspect the complete teaching lifecycle as one
language-capability resource or preserve the semantic role of each selected
knowledge sentence through whole-answer composition.

The new flow is:

1. Comprehension selects strongly relevant approved knowledge for the current
   question.
2. Knowledge-to-Language Growth checks its complete Acquire → Integrate →
   Express lifecycle, approval, source provenance, understanding evidence,
   source-parroting check, and Education–Expression–Personality Law result.
3. The bridge inspects only the answer text already selected by Comprehension.
4. Existing selected sentences are labeled as thesis, support, example,
   counterexample, or limitation when their approved knowledge field supports
   that role.
5. Discourse Planner and Discourse Loom may organize those units through their
   existing hard meaning and obligation gates.
6. Context and Expression Selection ranks only invariant-safe arrangements.
7. Voice remains the owner of Selene's expression.

The bridge does not add a sentence, retrieve raw teaching material, or turn a
lesson response into a reusable answer template.

## Availability gate

A teaching resource becomes available to this bridge only when all of the
following are true:

- its comprehension concept is an `approved_knowledge_resource`;
- review status is `approved_for_knowledge_use`;
- Chat use is `available_as_knowledge_resource`;
- source provenance is present;
- a teaching lifecycle exists;
- Acquire, Integrate, and Express are complete;
- the lifecycle is at `approved_knowledge_resource`;
- Aleks approved the item directly or through a recorded bounded curriculum or
  language-capability authorization;
- the Express source-parroting check passed;
- understanding evidence was sufficient; and
- the Education–Expression–Personality Law review permitted the lifecycle.

Failure of any gate holds the resource and reports the reason. A held resource
cannot reach NLO through this bridge.

## Vocabulary growth

Acquire-stage vocabulary becomes an inspectable reviewed term catalog for the
approved concept. A vocabulary mention is not automatically treated as a
synonym or interchangeable surface form.

Surface alternatives require explicit lexical metadata with:

- grammatical field;
- lemma and forms;
- sense;
- part of speech and grammatical behavior;
- compatible registers and collocations;
- near-concept distinctions; and
- source provenance.

That explicit metadata continues through the Living Lexicon's existing
validation and exactness locks.

## Construction growth

Phase 6 compiles evidence-backed construction affordances from completed
Express work:

- explanation;
- distinct example;
- analogy;
- question;
- comparison;
- limitation;
- counterexample;
- correction; and
- natural conversational participation.

These affordances record demonstrated expressive reach. They are not stored
phrases. They apply only to current, already-supported content and cannot grant
permission to invent an example, analogy, question, claim, or correction.

For the current answer, semantic role labeling allows the Discourse Loom to
retain a selected example as an example, a selected counterexample as a
counterexample, and a selected limitation as a limitation rather than flattening
all approved knowledge into generic prose.

## No-script boundary

Teach-back, application, analogy, question, comparison, conversational
participation, and correction responses are evidence that a concept was
understood and expressible. Their wording is not copied into an answer template.

Phase 6 therefore reports:

- `teaching_answers_used_as_templates: false`;
- `source_wording_imitation_allowed: false`;
- `content_added: false`; and
- `text_generated_by_growth_bridge: false` for every handed-off content unit.

Teaching expands what Selene can understand and express. It does not dictate
what she says, how she must feel, or who she is.

## Inspection surfaces

Router keys:

- `native_language.knowledge_growth.status`
- `native_language.knowledge_growth.items`
- `native_language.knowledge_growth.preview`

Local HTTP:

- `GET /api/native-language/knowledge-growth/status`
- `GET /api/native-language/knowledge-growth/items`
- `POST /api/native-language/knowledge-growth/preview`

NLO exposes `knowledge_language_growth` in its result, meaning packet, Voice
handoff, and revision evidence.

NLO version: `v30_knowledge_language_growth`.

## Boundaries preserved

Phase 6 creates no:

- hidden retention or memory write;
- identity, personality, Vys, governance, relationship, or authority change;
- model training, fine-tuning, or LoRA;
- provider dependency;
- raw corpus recall;
- autonomous teaching approval;
- factual content generation;
- source imitation; or
- teaching-answer script library.

The Great Library remains external. Personal memory remains separate from
general taught knowledge.

## Verification approach

Verification uses temporary databases and synthetic approved-teaching records.
It checks:

- complete approved lifecycle compilation;
- reviewed vocabulary and explicit lexical metadata visibility;
- construction-affordance compilation without template extraction;
- holds for unapproved, provenance-free, incomplete, or source-parroting
  material;
- role labeling of only already-selected answer text;
- no accidental inclusion of an unselected counterexample;
- NLO, Discourse Planner, Discourse Loom, revision, and Voice handoff;
- read-only router and local HTTP access; and
- unchanged memory, identity, personality, governance, authority, evidence,
  certainty, and source boundaries.

No live conversation, configured-database write, distress-shaped test,
reinstall, packaging, or provider generation is required.

Result: **180 focused checks passed**: 148 Knowledge-to-Language Growth,
Context and Expression Selector, Discourse Loom, Candidate Garden,
Construction Lattice, Living Lexicon, formation, NLO, teaching, contextual,
social, uncertainty, and expression checks; 3 bounded active-Chat handoff
checks; and 29 Comprehension and Teaching Lifecycle checks. Python compilation
passed. `git diff --check` reported no whitespace errors, only the existing
Windows LF/CRLF notices.

## Next phase

The next planned phase is Phase 7 — Generative Thought Expression: expressing
attributable ideas, hypotheses, analogies, collaborative questions, and
revisable attempts through this lattice without confusing a logical leap with
evidence or treating ordinary wrongness as failure.
