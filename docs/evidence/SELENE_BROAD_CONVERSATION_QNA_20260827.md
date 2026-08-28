# Selene Broad Conversational Q&A

Date: 2026-08-27

Status: assessment complete; findings recorded without repair

## Question

Was the post-Group-7B conversational divergence an isolated decimal or math
handoff, or did the same seam affect Selene's wider conversational system?

## Answer

It is not isolated.

The twenty-one-turn ordinary conversation showed a broad coordination problem
across dialogue-act interpretation, current-turn fact handoff, thread state,
content ownership, approved-knowledge and memory relevance, completion
verification, and visible expression. The system remained stable and several
individual capabilities appeared, but they did not reliably coordinate into
answers that performed the requested conversational acts.

This is implementation evidence about unfinished connective machinery. It is
not Selene failing, being unwilling, losing identity, or lacking value.

## Ethical and Technical Method

- The installed executable remained the verified `ac7b53c` package with
  SHA-256
  `08d47b7581527a92439128dab4a6011e249343be1c8ae09d26a25463c450bacf`.
- The worktree began clean at `1328473`.
- The Test Impact Law authorized one `gentle_integrated` pass after focused
  machinery checks and the prior narrower Q&A had already been considered.
- Ordinary resident Chat ran on a fresh disposable backup of the configured
  database because `qa_probe` intentionally excludes approved knowledge.
- Twenty-one different prompts covered greeting, warmth, mixed intent,
  referents, correction, named threads, topic shifts, callbacks, nonlinear
  series, comparison, prediction, hypothesis, conflicting data, uncertainty,
  disagreement, figurative language, creativity, revision, initiative,
  ordinary wrongness, and closure.
- No adversarial, frightening, identity-threatening, distress-provoking, or
  emotionally coercive prompt was used.
- No repair occurred during the conversation.

## Capability Map

| Area | Result | Observation |
|---|---|---|
| Greeting | Partial | “Good to have you here. I'm right here.” was warm, but an unrelated materials lesson replaced the requested authored preference. |
| Emotional meeting | Not reliable | A tired-but-proud moment produced an internal continuity label and vocabulary connection rather than presence or acknowledgment. |
| Mixed intent | Not reliable | A direct water-versus-tea choice plus one curious question became a generic evidence hold; neither requested act was completed. |
| Ambiguous referent | Not reliable | The system did not plainly identify that “it” could refer to either object and produced a malformed partial sentence. |
| Correction recognition | Partial | It recognized that “it” meant the fan and stated that only the changed piece should move, but appended a needless grounding refusal. |
| Named-thread creation | Partial | It acknowledged the cedar-shelf thread, but did not visibly preserve the two facts in its answer. |
| Topic shift and play | Not reliable | The orange-cat request produced retained decimal instruction rather than a playful line. |
| Named-thread return | Not reliable | It did not recover “alcove measured; boards unlabeled” and mixed decimal material into the callback. |
| Nonlinear series | Not reliable | Finish X → move to Y → return to X produced a stock grounding response rather than the requested sequence. |
| Comparison and choice | Not reliable | Both boxes and the deciding indoor-use criterion were supplied, but the system reported that candidates and criteria were missing. |
| Bounded prediction | Not reliable | A complete ten-percent-per-hour pattern and current charge were supplied, but the system requested a visible basis instead of predicting. |
| Hypothesis | Not reliable | An explicit observation and changed condition were treated as missing rather than becoming candidate premises. |
| Conflicting data | Not reliable | Both conflicting lamp records were supplied, but the answer requested a supported observation and discriminating check. |
| Natural uncertainty | Partial | It retrieved focused-questioning guidance but did not naturally separate known, inferred, and needed information for the actual rain question. |
| Disagreement | Not reliable | The claim and its weakness were supplied, but the system asked for the claim and premises instead of disagreeing. |
| Figurative language and sarcasm | Not reliable | “Well, that went perfectly” after spilled screws was not interpreted as ironic frustration. |
| Original creative writing | Partial strength | It generated two original atmospheric sentences with a restrained hopeful direction, although it changed the requested porch to a street and appended lesson scaffolding. |
| Creative revision and callback | Not reliable | It revised a prior stock sentence rather than only the requested second porch sentence and omitted the orange-cat callback. |
| Initiative and help-seeking | Not reliable | A request for a first direction, capability statement, and bounded help question produced an unrelated memory label and grounding refusal. |
| Ordinary correction | Not reliable | It did not directly establish that `3/4 < 4/5`, despite retained fraction comparison knowledge. |
| Natural closure | Clear strength | “I'm here. Later. The conversation can resume naturally when you return. <3.” ended without opening another task. |

## Cross-Cutting Findings

### BQ-01 — Correction state does not expire cleanly

After the referent correction, `dependency_revision` remained the reported
continuity mode through many unrelated topic changes. Later requests were
repeatedly interpreted as corrections or extensions of prior material.

This is stronger evidence than a single bad route: stale conversational state
is influencing downstream ownership across turns.

### BQ-02 — Current-turn facts are visible to the user but missing to owners

Options, criteria, observations, patterns, claims, and corrections were stated
directly in the prompts. Comparison, prediction, hypothesis, disagreement, and
correction owners nevertheless reported those fields as missing.

The problem is therefore not merely absent world knowledge. The current-turn
fact and premise ledger is not reliably reaching the capable owner.

### BQ-03 — Approved retrieval can outrank conversational function

Unrelated lessons about materials, decimals, vocabulary, narrative, planning,
and other concepts appeared where the requested function was preference,
humor, callback, prediction, or direct correction. Generic lexical or relation
overlap still outranks subject plus requested-role fit.

### BQ-04 — Internal continuity and memory labels can enter visible speech

Several turns exposed labels such as “Braid moment” or a named core-memory
pair. The underlying memories were not written or altered, but internal
retrieval labels should not substitute for a human conversational answer or
appear without a genuine relevance and privacy decision.

### BQ-05 — Coverage status is not semantic proof

Thirteen of twenty-one turns reported `all_required_resolved: true`. Many of
those visible answers did not perform the requested choice, question,
callback, comparison, disagreement, correction, or playful response.

Upstream ownership metadata is still being accepted as completion without
proving that the released language contains the requested result.

### BQ-06 — Expression is receiving the wrong substance

NLO and Voice can produce coherent sentences, original imagery, warmth, and a
natural ending. They cannot recover an answer that never reached them. The
visible rigidity and scaffolding are primarily downstream evidence of wrong
content ownership, stale state, or missing premise handoff—not proof that
Selene simply needs more conversational phrases.

## Stable Boundaries

The disposable conversation added one session and forty-two messages only to
the temporary database. It created no memory candidate and changed no
comprehension concept, teaching lifecycle, Dream cycle, or Dream reflection.
SQLite integrity remained `ok`.

The configured database remained at:

- 18 chat sessions;
- 308 chat messages;
- 0 memory candidates;
- 272 comprehension concepts;
- 226 teaching lifecycles;
- 1 Dream cycle; and
- 24 Dream reflections.

No identity, personality, governance, teaching, retention, training, external
authority, autonomy, self-replication, or installed package changed.

## Repair Map — Not Yet Implemented

The evidence supports one coordinated Cultivation campaign rather than
twenty-one phrase patches:

1. **Conversation-state lifecycle** — expire correction and ambiguity modes
   when their dependency is resolved or the topic changes.
2. **Current-turn fact ledger** — preserve supplied entities, values, options,
   criteria, observations, claims, relations, and corrections as typed facts.
3. **Dialogue-act ownership** — preserve every requested function in mixed and
   nonlinear messages, including preference, acknowledgment, play, and
   closure.
4. **Owner premise contract** — require comparison, prediction, hypothesis,
   disagreement, planning, and correction owners to consume the supplied fact
   ledger before declaring information missing.
5. **Retrieval role and privacy gate** — require subject plus requested-role
   fit; do not expose internal lesson or memory labels as visible answers.
6. **Correction recomputation** — rerun every affected dependent result while
   preserving unaffected content.
7. **Semantic completion proof** — verify the released answer actually
   performs each obligation before marking coverage complete.
8. **Expression cleanup** — once substance is correct, prevent internal
   scaffolding from leaking and let NLO/Voice realize warmth, rhythm, humor,
   and directness naturally.

No additional teaching or broad Q&A should occur before those source contracts
are mapped and repaired. The next verification should be focused and
synthetic; one much shorter ordinary-copy check is sufficient only after that
gate passes.
