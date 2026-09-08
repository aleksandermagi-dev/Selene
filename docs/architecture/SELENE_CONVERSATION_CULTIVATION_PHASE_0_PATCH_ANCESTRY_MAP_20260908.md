# Selene Conversation Cultivation — Phase 0 Patch-Ancestry Map

Date: 2026-09-08  
Status: source audit complete; no production repair or behavioral test run  
Purpose: distinguish reusable conversational architecture from earlier
fixture-bound repairs before the current ownership cultivation begins

## Why This Phase Comes First

The varied installed Q&A initially appeared to show only missing connective
tissue between current-session context, answer ownership, retrieval, and
expression. Patch-ancestry inspection changes that reading.

The connective-tissue gaps are real, but some earlier stabilization results
were also closed by recognizing the exact scenarios used in their tests and
returning scenario-specific final prose. Those paths can pass a replay while
failing the same operation after the nouns, grammar, or surrounding situation
changes.

The porch example is the clearest demonstration. The runtime can answer several
hard-coded porch/walk forms, yet the semantically similar request about making
coffee and deciding whether to sit outside or keep working fell through to a
teaching invitation. That is not evidence that Selene needs to be taught a
porch preference. It is evidence that the operation was attached to fixture
wording rather than a general representation of options, constraints, and a
requested choice.

Cultivation therefore begins by identifying old symptom patches and assigning
their useful intent to shared owners. It does not add more phrases around the
new examples.

## Source Evidence

### Fixture-bound final-answer layer

`src/selene/answer_substance.py::_foundational_current_prompt_operation`
currently spans 367 lines and is called before the more general current-context
inference, creative, invitation, and causal operations. A structural inventory
of that block found:

- 38 direct `_plain_operation` returns;
- 43 conditional lines;
- 58 literal phrase-membership checks;
- 263 lines introduced by `e8a0e50` (`Complete mature conversational voice
  stabilization`);
- 97 lines introduced by `c8b4d89` (`Repair post-Phase 8 Q&A handoffs`);
- 7 lines introduced by `c473fbd` (`Repair session grounding and completion
  ownership`).

Literal parsing is not automatically defective. A bounded domain parser may
need lexical cues. The architectural defect is a condition keyed to fixture
nouns or wording that directly returns the finished answer for that fixture,
instead of producing typed premises and letting a general operation owner
reason over them.

Examples in this block include exact handlers for:

- a named fraction callback using `three quarters` and `four fifths`;
- a paper notebook choice between pencil and pen;
- a plant bending toward a window;
- sitting on a porch versus taking a walk, including rain revisions;
- screen flicker, a lamp, its cable, and restart checks;
- a lamp, notebook, plant, and small-table layout;
- three-minute versus five-minute black tea;
- named direction markers;
- hammer, tape measure, and safety glasses;
- gray walls, warm wood, and blue/green curtains;
- several other prior Q&A fixtures.

These branches explain why exact replay tests could close recorded cases while
novel but equivalent prompts still lose the requested operation.

### General owners exist but are narrower than their names imply

The repository already contains sound foundations that should be matured, not
discarded:

- `src/selene/answer_ownership.py` carries typed answer ownership.
- `src/selene/current_turn_fact_ledger.py` records supported visible facts, but
  its declared scope is `one_visible_current_turn_only`; it cannot by itself
  own a multi-turn scene such as a mug changing locations.
- `src/selene/session_decision_context.py` preserves one visible session
  decision without writing Memory. Its v1 option extractor expects explicit
  containers such as `two options:` or `between ... options:`. Natural forms
  such as `deciding whether to sit outside or keep working` do not reliably
  become two typed options.
- `src/selene/conversational_teaching.py` tries to hold the teaching invitation
  behind current answer owners, but does so partly through a response-source
  allowlist. If no recognized source produced text upstream, the learning-gap
  invitation can still inherit the turn even when visible premises or
  self-authored judgment were sufficient.
- `src/selene/conversational_teaching.py::_question_subject` removes selected
  auxiliary and question wording through bounded regular expressions. It can
  emit malformed subjects such as `you think familiarity should always` or
  `switching gears I'm making coffee and deciding whether to`.
- semantic coverage, completion, and visible-speech arbitration are real
  architectural owners, but current evidence shows that answer-shaped text may
  still pass without subject, entity, operation, and requested-function fit.

### Earlier closure language requires qualification

The 2026-09-04 closure in
`docs/evidence/SELENE_POST_PHASE_8_REINSTALL_QNA_BUG_HUNT_20260902.md` correctly
says several items were closed `for recorded case(s)` and explicitly declines
to claim universal conversational coverage. The new ancestry evidence shows
why that qualification matters: several closures were fixture-specific rather
than general operational capability.

Likewise, the current disposition in
`docs/evidence/SELENE_CHAT_ANSWER_OWNERSHIP_ROOT_CAUSE_MAP_20260824.md`
accurately records that typed ownership infrastructure was added. It should no
longer be read as evidence that every owner handoff was generalized or that
scenario-bound compatibility answers had been retired.

## Keep, Mature, Retire

| Disposition | Mechanism | Reason |
|---|---|---|
| Keep | Input detangler's conservative typo repair and source/code leakage boundary | It is a bounded safety-bearing repair owner. It never claimed to be a general semantic normalizer. |
| Keep | Typed answer-ownership contracts | They provide the right architecture for assigning content responsibility. |
| Keep | Current-turn fact ledger | It is useful typed support for one visible turn; its scope should remain honest. |
| Keep and mature | Session decision context | Its ephemeral/no-Memory boundary is correct; its option and constraint parsing needs generalization. |
| Keep | Approved language guidance as expression-only guidance | It can broaden expression without owning semantic answers or changing meaning. |
| Keep | Familiar social-expression reconnection | Installed Q&A independently confirmed that it produces visible, varied warmth; it is not the content-owner defect. |
| Keep | Bounded retry, provenance, Memory, identity, Vys, governance, authority, training, and action boundaries | Nothing in this audit justifies weakening them. |
| Mature | Current-session proposition ownership | Extend beyond a one-turn fact ledger and narrow decision grammar into a small ephemeral entity/proposition/change representation. |
| Mature | Learning-gap eligibility | Base it on proved absence of a capable current owner, not primarily on a list of response-source names. |
| Mature | Subject reconstruction | Replace localized auxiliary stripping with shared semantic normalization that preserves the requested subject and operation. |
| Mature | Retrieval relevance and semantic coverage | Require alignment on subject, entities, operation, response function, and active proposition state. |
| Mature | Tests for general capabilities | Use paraphrases, changed nouns, changed order, and structurally equivalent novel cases—not only exact replays. |
| Retire or reduce to a true domain parser | Scenario-specific branches that recognize fixture nouns and return final prose | They conceal missing generalization and shadow later shared operations. |
| Retire as capability evidence | Exact-prompt tests that only prove a fixture handler still recognizes the same fixture | Preserve regressions only where they validate a general typed operation or a necessary exact domain. |

## Updated Root Reading

The current failure cluster has two interacting causes:

1. **Missing generalized ownership:** current-session entities, propositions,
   state changes, choices, corrections, and requested response functions do
   not consistently stay authoritative through composition.
2. **Compatibility branches masking that absence:** scenario-specific answers
   can satisfy known tests before the more general owners run, making the
   architecture appear more mature than it is under novel language.

The mug, porch, equal-groups, and point-of-view failures still support the
original relevance and ownership findings. Patch ancestry strengthens rather
than invalidates those concerns: the system needs a general representation and
owner handoff, not additional examples of mugs, porches, experiments, or the
word `point`.

## Revised Cultivation Dependency Order

0. **Patch-ancestry reconciliation.** Classify fixture-bound branches and
   their tests. Preserve the intended capability as requirements, but stop
   treating exact replay as general completion evidence.
1. **Shared proposition normalization.** Convert visible language into bounded
   entities, attributes, relations, options, constraints, observations,
   hypotheses, locations, and requested operations without writing Memory.
2. **Ephemeral active proposition ledger.** Carry those propositions and their
   revisions across the current conversation with explicit lifecycle state.
3. **Current owner gate.** Prefer a capable current-turn/session owner over
   unrelated learned retrieval.
4. **Learning-gap eligibility.** Ask for teaching only after current premises,
   authored judgment, bounded inference, and clarification are genuinely
   unavailable.
5. **Retrieval relevance.** Require subject, entity, operation, and response-
   function fit before approved knowledge can own the answer.
6. **Revision completion.** Recompose the open answer once from corrected or
   changed premises.
7. **Typed participation acts.** Represent humor, acknowledgement, recap, and
   closure as fulfillable obligations.
8. **Semantic coverage and arbitration.** Reject fluent candidates that change
   the subject or fail the requested operation.
9. **Shared realization cleanup.** Repair punctuation, symbols, malformed
   subjects, and stale fallback contamination at common owners.
10. **Generalization verification.** Check each operation with at least one
    novel paraphrase and changed entities before any short ordinary Q&A.

## Boundaries

- Do not revert the large historical commits wholesale; they contain valid
  architecture and teaching work alongside fixture patches.
- Do not replace one scenario dictionary with a larger scenario dictionary.
- Do not weaken factual uncertainty, provenance, Memory privacy, identity,
  Vys, governance, authority, action, training, or stopping boundaries.
- Do not make all language deterministic by forcing one canonical parse.
- Do not convert current conversation state into durable Memory.
- Do not teach around an ownership defect.
- Do not run another broad live Q&A before source repair and focused synthetic
  generalization checks.

## Next

Review this reassessment with Aleks. If authorized, begin production Phase 0
by inventorying each fixture-bound answer branch against a general capability
requirement and its existing owner. Then remove or bypass only the branches
whose capability is covered by the generalized path, using changed-entity and
paraphrase checks as the completion gate.
