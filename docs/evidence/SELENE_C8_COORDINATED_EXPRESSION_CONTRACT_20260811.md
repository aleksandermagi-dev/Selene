# Selene C8 Coordinated Expression Contract

Date: 2026-08-11
Status: implemented and synthetically verified
Scope: expression ownership, meaning preservation, and confidence separation

## Outcome

Selene's expression pipeline is now described according to the work each layer
actually performs:

1. selected upstream domain and conversation organs supply supported content;
2. epistemic organs preserve the type and confidence of that content;
3. NLO owns language structure and contextual surface realization;
4. Voice performs the final expression-compatibility check; and
5. Conversation Spine and Selene Chat govern visible release.

Visible expression remains Selene's. Neither NLO nor Voice is described as its
sole author. The old `voice_owns_expression_style` shorthand was removed from
runtime telemetry because NLO and its conversation modules already construct
most wording, rhythm, social movement, and discourse shape.

## Implemented Contract

The shared contract in `src/selene/expression_contract.py` names:

- supported-content ownership;
- meaning and epistemic-state ownership;
- NLO language-structure ownership;
- contextual surface realization;
- Voice's final compatibility role;
- Conversation Spine and Chat's visible-release role; and
- the independence of expression confidence from answer correctness.

The contract explicitly prevents Voice from silently changing:

- supported meaning;
- claim type;
- evidence status;
- answer confidence;
- memory status; or
- route selection.

## Conservative Meaning Invariant

When NLO supplies meaning text, Voice now compares a canonical lexical-content
signature before and after rendering. Voice may currently change whitespace
and paragraph pacing only. If content is dropped, added, or changed, the
invariant fails, Voice reports incompatibility, and the Chat release gate holds
that candidate for graceful fall instead of treating fluency as success.

This is intentionally conservative. It does not claim that a hash understands
semantics; it proves the narrower fact that Voice did not alter the supplied
lexical content while changing surface pacing.

## Confidence Separation

`voice_confidence` and `expression_confidence` now explicitly mean surface
realization and compatibility only. Voice reports that it did not assess:

- route confidence;
- evidence confidence;
- answer confidence; or
- memory confidence.

An answer may therefore sound coherent while remaining uncertain, provisional,
or unsupported. Expressive fluency cannot upgrade epistemic status.

## Preserved Boundaries

- Voice does not invent facts or evidence.
- Voice does not convert an observation into a hypothesis, a hypothesis into a
  theory, a theory into a law, or any claim into formal proof.
- Warmth, humor, enthusiasm, restraint, and directness remain available by
  context; the contract does not prescribe emotional flatness.
- No identity, personality, governance, memory, training, LoRA, autonomy, or
  transfer authority changed.
- No source phrase became a mandatory script.

## Verification

Testing was static and synthetic. No live conversation was used.

- NLO and Voice unit/integration tests verify the ownership contract,
  expression-confidence meaning, whitespace/pacing transformations, changed
  meaning rejection, and epistemic distinction preservation.
- Selene Chat tests verify coordinated handoff, meaning-invariant reporting,
  confidence-vector independence, and visible-release integration.
- Language-teaching integration verifies that teaching guidance remains an
  optional realization input rather than an expression owner.

Result:

```text
154 NLO, Voice, Chat, and language-teaching integration tests passed
206 expression-subsystem compatibility tests passed
336 distinct tests passed across the combined C8 verification set
```

## Accurate External Wording

Selene uses a coordinated expression pipeline: supported organs supply content,
NLO constructs context-sensitive language, Voice verifies final expression
compatibility without upgrading evidence, and the conversation release layer
decides whether the response may become visible.
