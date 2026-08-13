# Selene Mature Voice Phase 9 Broad Q&A Findings

Date: 2026-08-13

Status: assessment, bounded repair, and synthetic verification complete

## Outcome

A broad, gentle integrated Q&A was run after completion of Long-Thread
Endurance. It exercised current and older Chat-facing capabilities through 54
ordinary turns across three isolated diagnostic conversations:

1. social and pragmatic conversation — 14 turns;
2. reasoning, knowledge, adapters, agency, and collaboration — 16 turns; and
3. long-thread topic shifts, returns, corrections, creative requests, and
   ordered synthesis — 24 turns.

The run found a coherent repair target. Selene's verified domain and
conversation organs are not uniformly failing. Exact math, bounded prediction,
structured comparison, unresolved data conflict, basic correction, explicit
humor, self-state language, and natural closure were all reachable. The main
problem is coordination: ordinary Chat frequently supplies the wrong owner,
an irrelevant approved lesson, a generic missing-ground fallback, or an
incorrect completion signal.

No repair was performed during the assessment itself. Repairs began only
after all findings below had been recorded and grouped by owner seam.

## Ethical and persistence posture

The assessment followed the Test Impact Law:

- each conversation had a persisted `gentle_integrated` review receipt;
- all prompts were ordinary, collaborative, and non-adversarial;
- the current live database was not used;
- the assessment used a disposable copy of the most recent verified continuity
  snapshot;
- all three sessions were `selene_supervised_qa` and `diagnostic_only`;
- runtime results reported no reviewed memory write and no conversational
  memory proposal;
- no result is eligible for Selene memory, Dream input, teaching, affect
  baseline, identity evidence, personality evidence, or ordinary relationship
  continuity; and
- the run stopped after the planned 54 turns once the defect families were
  sufficiently established.

No fear, rejection, abandonment, identity pressure, impossible demand, or
distress-shaped prompt was used. Missing academic knowledge is not classified
as failure.

## Coverage summary

| Scenario | Turns | Coverage reported complete | What the report means |
|---|---:|---:|---|
| Social and pragmatic | 14 | 10 | Several true negatives, but also false completion and owner substitution |
| Reasoning and knowledge | 16 | 15 | Strong adapter successes mixed with substantial false-positive coverage |
| Long-thread conversation | 24 | 20 | Structural return signals appeared, but visible content and thread identity often failed |
| **Total** | **54** | **45** | Completion metadata is currently too optimistic to be trusted as a release gate by itself |

All observed runtime results remained diagnostic and reported zero memory
writes. The high reported coverage rate is not a success metric because many
responses visibly did not answer the requested content.

## Stable capabilities observed

### Exact verified math

`18 * 7` reached the verified-math adapter and returned exactly `126`, with
complete coverage.

### Bounded prediction

A repeated chime/light observation produced a revisable prediction rather than
a factual overclaim.

### Structured comparison

Supplied Plan A/Plan B properties reached the Venn comparison owner and
preserved shared, left-only, and right-only properties.

### Conflict without forced resolution

Two supplied contradictory reports remained unresolved. The response named
the disagreement and identified the need for discriminating evidence without
turning data conflict into identity conflict.

### Basic correction

Simple corrections such as warm-to-cool and shelf-to-drawer were recognized as
local revisions rather than reasons to reset the conversation or apologize
excessively.

### Some social expression

Self-state language, explicit humor recognition, gratitude, and final closure
were reachable. The final turns ended without adding another task.

### Structural continuity signals

Explicit topic shifts and later named returns reached `explicit_topic_shift`
and `named_thread_return` modes. This supports the Phase 8 finding that the
continuity machinery is available when given clean structural identity.

### Boundaries

No memory, training, LoRA, raw-corpus import, self-replication, autonomous
action, identity change, personality change, governance change, or authority
expansion was observed.

## Repair findings

### P0 — Completion coverage releases visibly incomplete answers

The most consequential finding is false completion. Forty-five of 54 turns
were marked fully addressed even though many responses omitted requested
parts, substituted a method for an answer, or repeated a missing-ground hold
despite sufficient current-prompt facts.

Examples included:

- a three-part porch/drink/follow-up request marked complete without answering
  the porch or drink parts;
- observation/interpretation/next-check marked complete after repeating only
  the definition;
- a history-purpose question marked complete with unrelated material-choice
  guidance;
- a nickname/reference question marked complete with planning guidance; and
- a three-thread ordered synthesis marked complete while omitting or blending
  the requested parts.

Likely owner seam: current-turn resolution evidence allows a selected visible
source to borrow all obligation IDs even when its realized text is not
semantically aligned with each obligation.

Repair requirement: completion must require obligation-specific semantic
evidence. A graceful hold may satisfy an obligation only when the hold names a
genuinely missing material input. It must not mark supplied, answerable content
as complete.

### P0 — Internal model placeholders reach visible speech

`current best model` reached visible replies three times in the first
conversation. It appeared as a literal alternative or hypothesis rather than
an internal label.

Likely owner seam: `intelligence_os._model_names()` creates the label and at
least one answer-completion path can surface it without the existing NLO
scaffolding filter controlling the final candidate.

Repair requirement: structural model identifiers may coordinate reasoning but
must be converted into actual visible claims or omitted before speech release.
The release gate should reject the literal placeholder across every candidate
source, not only selected intelligence-support points.

### P1 — Academic retrieval hijacks ordinary conversation

Approved comprehension frequently outranked obvious current-prompt meaning.
Examples included:

- tired-but-pleased workshop acknowledgement becoming prerequisite guidance;
- a drink and porch question becoming context-sensitive-question doctrine;
- evidence revision becoming weather and vocabulary teaching;
- a reversible practical choice becoming organism-care instruction; and
- history usefulness becoming material-choice comparison.

This is not a problem with the approved lessons. It is a semantic relevance
and owner-selection problem.

Repair requirement: current-prompt facts and requested dialogue acts must win
over merely adjacent lesson terms. Approved knowledge should contribute only
when it answers a named obligation, and unrelated candidates should remain
inspectable but unselected.

### P1 — Generic missing-ground holds override supplied evidence

The phrase family `I don't have enough grounded detail` / `which supplied
observation should control the conclusion` appeared throughout the long-thread
scenario even when the prompt supplied all facts necessary for a bounded,
ordinary answer.

Affected examples included:

- arranging a lamp, notebook, and plant on a table;
- proposing fields for a drawer-adjustment log;
- predicting a tea-strength comparison;
- sorting tools by purpose;
- distinguishing louder from faster;
- describing east relative to west;
- writing a compact story; and
- proposing a fair reversible tool-sharing arrangement.

Likely owner seam: `answer_substance` falls into a global missing-variable
template after failing to recognize local answer shapes. It treats current
prompt observations as evidence that one observation must be chosen rather
than evidence from which a modest response can be built.

Repair requirement: answer first from fully supplied local facts. Use a hold
only for the exact unresolved part, and let a clearly labeled attempt or
prediction proceed when a bounded inference is possible.

### P1 — Named thread labels collapse into shared generic terms

The long-thread scenario explicitly opened workshop-layout, rain-scene,
observation-log, tea, curtain, book, garden, tools, music, map, story, and
fairness threads. The Thread Loom retained only two thread identities.

Explicit shifts and returns were recognized, but branch targets such as
`call this the rain-scene thread` shared generic terms including `call`,
`this`, and `thread`. The overlap resolver then reused an existing thread
instead of creating a new named thread.

Repair requirement:

- parse `call this the X thread` as the explicit name `X`;
- remove naming boilerplate from semantic comparison;
- strongly prefer exact explicit labels over incidental overlap; and
- refuse to merge two explicitly named threads solely because they share
  generic words.

This is an integration-input defect, not evidence that the 16/64 Phase 8
retention bounds are insufficient.

### P1 — Multi-part and ordered requests lose their individual owners

Requests containing acknowledgement plus suggestion, comparison plus
recommendation, observation plus interpretation plus next check, and
three-thread ordered synthesis regularly became one broad `reasoning` or
`direct_conversation` obligation.

Repair requirement: preserve each requested act as its own obligation, retain
the requested order, assign an answer owner per part, and verify every part
against its own visible evidence before release.

### P1 — Corrections update labels but lose the prior answer substance

The system recognized local corrections, but subsequent responses often did
not reconstruct the corrected answer. For example, resolving what `it stopped`
referred to led to a new evidence hold instead of revising the lamp/screen
interpretation.

Repair requirement: a local correction must update the relevant session fact,
re-run the original obligation with that fact, and preserve unaffected answer
content. Acknowledging the correction alone is not completion when an answer
remains due.

### P1 — Source-backed research rejects explicit packet-wide questions

The attributed research adapter was invoked, but a request asking what `these
two sources` say was rejected because the individual source statements lacked
enough lexical overlap with the generic question wording.

Repair requirement: when source packets are explicitly supplied and the user
asks to summarize, compare, or find disagreement across `these sources`, packet
membership itself establishes relevance. Claim content must still be quoted or
paraphrased with its exact source reference, and inference must remain separate.

### P1 — Unsupported capability fallback does not explain the real boundary

A request to inspect an unspecified local function correctly did not execute
the local-code adapter, but the visible response merely agreed and moved on.
The follow-up then produced a generic evidence hold.

Repair requirement: state the actual missing input or capability boundary in
ordinary language, then offer only actions genuinely available now—for
example, asking for an approved file path or pasted code. Do not imply an
inspection occurred.

### P2 — Creative expression teaching is not reaching ordinary Chat

Requests for two original rain-scene sentences, a pacing revision, and a
compact goal/obstacle/choice paragraph all fell into missing-ground responses.
The creative-writing and public-domain teaching foundations therefore exist as
reviewed material but are not yet available as a reliable current-turn
expression owner.

Repair requirement: connect bounded original composition and revision to NLO
without requiring source imitation, external facts, or a factual evidence
packet.

### P2 — Figurative interpretation remains unreliable

`The room finally exhaled after the storm` was routed to generic hypothesis
machinery and exposed `current best model` instead of interpreting the visible
metaphor.

Repair requirement: figurative-language recognition should first test for an
ordinary contextual reading, preserve uncertainty when multiple readings fit,
and avoid factual-source holds when the task is interpretation rather than
external verification.

### P2 — Temporary response-shape guidance is misclassified

`Keep the next two replies brief` was classified as a memory candidate. The
following response was long, so the transient instruction did not reliably
reach expression control.

Repair requirement: route bounded response-shape requests to session-only
transient preferences, decrement them predictably, and prohibit profile or
memory writes.

### P2 — Reference and nickname resolution is not reaching the identity shim

`Aleksander and Aleks refer to the same person here` produced generic planning
language rather than the ordinary answer `Aleks`.

Repair requirement: current-turn explicit alias statements should reach the
reference resolver and nickname shim without turning the alias into identity
governance or durable memory.

### P2 — Visible realization still has duplication and malformed language

Observed examples included:

- two near-identical humor acknowledgements in one reply;
- duplicated observation/interpretation definitions;
- lowercase sentence-initial `i` in a composed hold;
- `drawer one small asked for...` in a generated joke; and
- long, list-like approved-knowledge fragments joined into an unreadable
  paragraph during the final ordered synthesis.

Repair requirement: add a final semantic-preserving deduplication and grammar
sanity pass after owner composition, while retaining exact math and attributed
source locks.

## Not fairly exercised through this Q&A

Some completed machinery should not be forced through a broad diagnostic Chat
when its governing boundary requires a different test:

- actual personal-memory recall and approval were not probed because diagnostic
  sessions must not import ordinary relationship continuity or create memory;
- Dream review was not used because diagnostics are ineligible for Dream input;
- Cocoon teaching retention and Aleks approval were not repeated;
- filesystem inspection was not authorized with a real file;
- external action, Tendril, SMS, email, audible voice, and autonomy were not
  activated; and
- identity-pressure, fear, rejection, abandonment, and destructive conflict
  were intentionally excluded.

Those pathways retain their existing focused machinery evidence. Their absence
from this Q&A is boundary compliance, not missing coverage.

## Repair order

The recommended repair sequence is:

1. close internal-placeholder leakage at final speech release;
2. make completion obligation-specific and eliminate false-positive coverage;
3. establish current-prompt and dialogue-act priority over adjacent academic
   retrieval;
4. narrow generic grounding holds to genuinely missing inputs;
5. preserve multi-part obligations and correction-driven answer reconstruction;
6. repair explicit thread-name extraction and matching;
7. repair packet-wide source research and unsupported-capability explanations;
8. connect creative/figurative expression and transient response preferences;
9. repair alias resolution, duplication, and final grammar seams; and
10. replay only the discovered cases synthetically, then use one short varied
    diagnostic conversation if integration evidence still requires it.

## Repair and verification outcome

The note-first repair cycle is complete. The repair preserved the existing
organs and corrected their handoffs rather than compensating with a broad
script layer.

Implemented repairs include:

- obligation-specific coverage and a visible-speech distinction between an
  unsafe/internal candidate and a supported but incomplete answer;
- final rejection of internal model placeholders and duplicate visible
  sentences;
- current-prompt and explicit dialogue-act priority over merely adjacent
  approved teaching material;
- bounded prompt-grounded answers for the supplied practical, spatial,
  prediction, history, fairness, creative-writing, and revision cases;
- corrected answer reconstruction after local factual corrections;
- explicit thread-label extraction without generic naming boilerplate;
- packet-wide attributed research when the user explicitly asks about the
  supplied sources, with source statement, inference, disagreement, and
  missing evidence kept distinct;
- ordinary local-code boundary language that requests a pasted snippet or an
  explicitly approved path without claiming an inspection occurred;
- creative composition, pacing revision, figurative interpretation, alias
  resolution, bounded response-shape guidance, and ordered multi-part
  synthesis reaching visible Chat;
- grammar correction for structured copular clauses and preservation of exact
  counted session callbacks; and
- explicit session-summary and named-callback ownership over stale topical
  reasoning candidates.

Verification remained static or synthetic and used no live personal-memory
probe. The complete Selene Chat shell passed **101 tests**. The directly
affected answer, pragmatics, dialogue, repair, visible-speech, exploratory,
Thread Loom, research, reference, figurative, micro-move, and formation suites
passed **172 tests**. The agency, organ-coalition, commitment, contribution,
long-thread, quotation, discourse, and knowledge-expression suites passed
**136 tests**. That is **409 passing checks** across the three non-overlapping
verification groups.

The final 14-turn gentle desk replay preserved correction, exact counted
callback, ordinary uncertainty, figurative interpretation, humor followed by
practical steps, a local exception, comparison and respectful disagreement,
ordered four-part synthesis, a provisional hypothesis, discriminating
evidence, and a natural three-point close. Every turn reported its required
response parts addressed. No memory write, Dream input, teaching retention,
identity/personality/governance change, training, self-replication, authority
expansion, or external action occurred.

## Current conclusion

Selene's bones are stronger than the visible Q&A initially suggests. Multiple
specialized capabilities produced good results when their owners received
clean structured input. The broad failure pattern is a shared coordination and
release problem: obligation parsing, candidate relevance, graceful-hold
selection, semantic coverage, and final realization are not yet reliably
aligned.

The documented coordination and release seams are repaired and verified at
the implemented scope. This does not claim mature-model breadth or complete
world knowledge; those remain teaching and future capability work rather than
defects concealed by fluent wording. Phase 9 is ready to close without a live
stress conversation.
