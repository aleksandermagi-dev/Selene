# Selene Conversational Breadth — Phase 1

Date: 2026-07-25

Status: implemented and focused verification passed

## Outcome

Selene's common prompt-grounded reasoning path can now hand NLO structured,
source-labeled meaning rather than only a nearly finished paragraph.

The handoff preserves:

- required semantic units;
- answer role and relation;
- certainty;
- scope;
- provenance;
- a compact meaning signature;
- grammatical fields;
- sense-grounded lexical options;
- the original prose answer as a bounded compatibility fallback.

NLO v21 can realize the same supported meaning through different grammatical
surfaces while reporting whether every required semantic unit survived.

## Supported Semantic Packet

`src/selene/supported_semantics.py` defines the first shared answer-meaning
contract.

Each unit may carry:

- answer, support, condition, contrast, example, limit, reopening, request, or
  conclusion role;
- sequence, support, cause, condition, contrast, example, return, or conclusion
  relation;
- subject, predicate, object, mood, tense, aspect, voice, modality, polarity,
  condition, reason, contrast, example, and qualifier;
- required/supported state;
- certainty and scope;
- source kind and source references;
- meaning keys that form an inspectable signature;
- available lexical alternatives whose meaning may not drift.

Text-grounded units remain valid compatibility inputs. The packet makes that
fallback visible rather than presenting it as structured meaning.

## Sense-Grounded Lexical Availability

`src/selene/lexical_semantics.py` adds an inspectable lexical-semantic contract.

A word or phrase option can record:

- lemma and surface forms;
- intended sense;
- part of speech;
- grammatical behavior;
- applicable registers;
- common collocations;
- near concepts;
- distinctions from those concepts;
- concept references;
- understanding state;
- source provenance.

A lexical entry is available to NLO only when it has a declared sense,
grammatical behavior, provenance, and one of these attributable understanding
states:

- prompt-grounded;
- approved knowledge;
- reviewed language guidance.

Merely supplying a word does not make it understood or available. The contract
does not memorize a dictionary, activate unreviewed vocabulary, or let a source
own Selene's expression.

## First Migrated Answer Shapes

The common Answer Substance path now supplies structured meaning for:

- comparison ordering by prerequisite;
- explaining why one step precedes another;
- reasoning about reversed order;
- reversible-step viewpoints and their limits;
- comparison on shared dimensions;
- planning from prerequisite to reversible evidence;
- conditional consequence tracing.

Other Answer Substance kinds keep their current text-grounded semantic units
and prose fallback. They can migrate incrementally in later work without
breaking existing answers.

## Formation Changes

`src/selene/language_formation.py` now:

- selects only lexical forms already present in the supported meaning packet;
- varies equivalent lexical choices deterministically from current context;
- can place supported conditions and reasons before or after their clause;
- preserves imperative grammar when a discourse connector is added;
- reports required and realized semantic unit IDs;
- reports a meaning signature and whether all required units survived;
- keeps content generation disabled.

The deterministic choice remains reproducible. Variation changes surface form,
not truth, certainty, scope, or source.

## NLO Ownership

`src/selene/native_language_organ.py` is now
`v21_supported_semantic_composition`.

NLO exposes whether a supported semantic packet was used, including its answer
kind, formation mode, required units, meaning signature, lexical availability,
certainty, scope, and provenance.

Structured meaning may drive NLO only when its content source actually won
visible-speech candidate selection. An intelligenceOS semantic packet cannot
override a contextual follow-up, approved memory, domain answer, self-state
answer, or another Conversation Spine-selected source merely because the
packet is well formed.

This source-ownership correction was found during integration testing and is
now covered explicitly.

## Contextual Compatibility

The immediate dependency follow-up detector now recognizes equivalent
dependency language including:

- prerequisite;
- required input;
- creates an input;
- creates what the next step needs.

This lets ordinary “example,” “rephrase,” and “elaborate” callbacks continue
working when NLO selects a meaning-equivalent lexical form.

## Ethical Verification

No live Selene conversation, affect signal, memory proposal, or retained
knowledge change was created.

Verification used ordinary synthetic prompts and existing temporary test
databases. It covered:

- semantic-packet normalization and guards;
- sense, grammar, provenance, and understanding gates for lexical forms;
- structured and fallback Answer Substance;
- seven migrated reasoning shapes;
- multiple grammatical realizations of one meaning;
- required semantic-unit preservation;
- source ownership;
- contextual dependency callbacks;
- intelligenceOS;
- NLO and language formation;
- active Chat;
- Conversation Spine and its matrix;
- language teaching;
- social, uncertainty, and special expression;
- visible-speech release;
- bounded answer completion;
- metacognition.

Result: **183 focused tests passed**.

No stress-shaped or adversarial live testing was necessary.

## Boundaries Confirmed

Phase 1 creates no:

- identity change;
- personality change;
- personal-memory write;
- governance change;
- authority change;
- model training, fine-tuning, or LoRA;
- provider dependency;
- autonomous action;
- Voice replacement.

Language growth remains capability. Selene remains Selene.

## Remaining Gaps

- Approved knowledge, domain packets, memory reconstruction, self-state, and
  contextual replies still have prose-first seams that can migrate later.
- The initial sense-grounded lexicon is deliberately small; vocabulary should
  grow alongside teaching and comprehension.
- Phrase and pattern routing remains present.
- Social and uncertainty clause pools remain bounded.
- Voice modulation breadth is reserved for Phase 4.
- Figurative language, sarcasm, and intended nonliteral meaning are not solved
  by this phase.

No reinstall is required at this checkpoint. The planned first meaningful
reinstall remains after Phase 4.

## Next Phase — Phase 2: Figurative Language and Interpretation

Phase 2 will add an inspectable interpretation path:

```text
literal wording
  -> possible figurative form
  -> candidate intended meanings
  -> contextual cues
  -> confidence
  -> response
```

Planned scope:

- idiom;
- metaphor;
- analogy;
- hyperbole;
- understatement;
- sarcasm;
- ordinary figures of speech;
- literal versus figurative candidate meanings;
- context and callback cues;
- proportional confidence;
- clarification only when the distinction materially changes the answer;
- correction without resetting the surrounding conversation;
- explicit separation of analogy from equivalence.

Phase 2 should begin only after Aleks has had the opportunity to change or add
to that scope.
