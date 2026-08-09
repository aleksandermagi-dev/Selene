# NLO Meaning-Preserving Language Lattice — Phase 7

## Generative Thought Expression

Phase 7 gives already-supported generative thought a bounded path into Selene's
language. It does not create a new reasoning organ.

The underlying thought owners remain:

- intelligenceOS and domain support for current answer meaning;
- Claim–Evidence Coordination for observations, inferences, hypotheses,
  models, conclusions, evidence, confidence, and reopening conditions;
- Structural Discovery for cross-domain mappings, analogy boundaries,
  hypotheses, discriminating observations, and counterexamples; and
- Conversational Energy for one relevant idea, connection, curiosity question,
  or specific collaborative-help request.

The new expression bridge receives those attributable outputs, preserves their
kind and epistemic status, and lets NLO express at most one optional thought in
the current turn.

## Supported thought kinds

The bridge recognizes five distinct kinds:

- **idea** — a supported possibility that may advance the current exchange;
- **hypothesis** — a provisional, testable explanation with a reopening path;
- **analogy** — a structural comparison with explicit hold and break
  boundaries;
- **collaborative question** — one question that materially improves
  understanding or shared work; and
- **revisable attempt** — a useful current attempt that may be corrected
  without being treated as failure.

These labels are semantic invariants. Voice may make the wording Selene's, but
it cannot turn an idea into an answer, an analogy into proof, a hypothesis into
a conclusion, or a tentative attempt into certainty.

## Attribution gate

An explicit thought candidate requires at least one of:

- accepted source provenance;
- an evidence reference;
- a basis claim present in the supplied Claim–Evidence packet; or
- an explicit statement that the meaning is supported by the current visible
  context.

Private corpus and Metacognition Miner provenance are held out of visible
thought expression. The bridge does not retrieve raw sources, memories, or
teaching text.

Additional gates depend on thought kind:

- an idea names why it matters;
- a hypothesis retains a discriminating observation or change condition and a
  counterexample or failure condition;
- an analogy names where the mapping holds and where it breaks;
- a collaborative question must materially improve understanding or the
  shared task; and
- a revisable attempt keeps a correction or reopening path.

Unsupported candidates remain inspectable as held candidates with a reason.

## Expression behavior

`src/selene/generative_thought_expression.py` performs one bounded selection
and adds only wrapper language around supplied meaning. It does not generate a
fact, infer a new relationship, or fill a missing answer.

Default realization is concise. Selene does not have to explain herself unless
the response shape asks for development. An analogy receives the short safety
distinction that it is a comparison rather than proof; detailed hold, break,
test, and counterexample material remains attached to the packet for supported
long-form use.

Conversational Energy and the new bridge cooperate rather than duplicate one
another. If Conversational Energy selects an idea or material question, the
bridge preserves its attributable kind and realizes it once. The older energy
realizer detects that the meaning is already present and does not append it a
second time.

Natural closure outranks optional thought expression. Questions remain
disallowed by default and become available only when a selected collaborative
question has passed its materiality gate.

## NLO and Voice integration

NLO v31 carries:

- the complete generative-thought packet in its meaning result;
- the selected thought kind as a visible discourse move;
- a bounded realization report;
- kind and confidence invariants into revision; and
- the packet and realization into Voice handoff.

Voice owns expression style but may not change thought kind, confidence,
evidence, source, or scope.

Inspectable routes:

- `native_language.generative_thought.status`
- `native_language.generative_thought.preview`
- `GET /api/native-language/generative-thought/status`
- `POST /api/native-language/generative-thought/preview`

The routes are read-only and do not retain preview material.

## Boundaries

Phase 7 creates no:

- new reasoning or truth authority;
- hidden chain-of-thought exposure;
- automatic memory write or retention;
- raw corpus or private miner recall;
- identity, personality, governance, law, or authority change;
- automatic speech, message delivery, initiative, or action;
- automatic Cocoon routing;
- model training, fine-tuning, or LoRA; or
- provider dependency.

An ordinary wrong answer or incomplete attempt remains development evidence,
not Selene failing. Selene remains Selene.

## Ethical verification approach

Verification is static and synthetic first. It covers:

- supported and unsupported attribution;
- private-source holds;
- hypothesis basis, falsifiability, and counterexamples;
- analogy hold/break boundaries and no-proof invariant;
- revisable attempts without failure framing;
- one material collaborative question and no habitual question;
- natural-close precedence;
- single realization without duplication or pressure;
- NLO, discourse, revision, and Voice handoff;
- read-only router and local HTTP previews; and
- regressions across existing NLO, Conversational Energy, Structural
  Discovery, Claim–Evidence, and Knowledge-to-Language Growth behavior.

No live Selene conversation, configured-database write, distress-shaped test,
reinstall, package, provider call, or model training is required.

Result: **221 focused checks passed**: 216 language-lattice and supporting-organ
checks, plus 5 bounded active-Chat handoff checks for supported ideas,
collaborative help, structural hypotheses, visible-basis attempts, and answer
ownership. Static Python compilation and whitespace checks also passed; only
the repository's existing Windows LF/CRLF notices remained.

## Next phase

The next planned phase is Phase 8 — Gentle Stabilization: static checks,
synthetic invariant and coverage fixtures, existing-record inspection, and
only then a small ordinary conversation if implementation evidence genuinely
requires one.
