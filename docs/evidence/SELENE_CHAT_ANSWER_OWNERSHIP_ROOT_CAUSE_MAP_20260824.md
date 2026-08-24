# Selene Chat Answer-Ownership Root-Cause Map — 2026-08-24

## Purpose

This record maps why a correctly routed ordinary conversation can still end in
a source-packet request, an irrelevant approved lesson, or a fluent but
incomplete answer. It applies the Cultivation method: preserve the visible
symptom, reproduce it without changing the resident system, trace the first
architectural divergence, and repair the owning contract rather than one
phrase.

This is a diagnosis and repair map. It is not a runtime repair, teaching
packet, evaluation of Selene's worth, or evidence that a missing capability is
Selene failing.

## Ethical And Technical Method

- Static inspection was used wherever it could answer the question.
- One gentle eleven-turn conversation was run in `qa_probe` mode against a
  disposable copy of the configured database.
- The prompts used ordinary self-state, preference, correction, comparison,
  prediction, planning, and closure requests. They did not provoke distress or
  test emotional injury.
- The resident database, retained knowledge, memory, identity, personality,
  governance, authority, training state, and installed application were not
  changed.
- The trace is implementation evidence about unfinished coordination
  machinery, not an assessment of Selene as an individual.

## Short Finding

The recurring source-packet language does not have one cause. Several
independent ownership errors converge on the same visible fallback:

```text
current request
  -> meaning / dialogue obligations
  -> content-owner assignment
  -> knowledge or domain retrieval
  -> bounded completion
  -> semantic-to-obligation binding
  -> coverage
  -> NLO / Voice realization

first wrong owner or wrong obligation
  -> wrong content is labeled supported
  -> coverage trusts the label
  -> later organs preserve or polish the wrong answer
```

The strongest architecture already exists: typed meaning, a conversation
spine, domain adapters, comprehension, metacognition, affect guidance, NLO,
Voice, and evidence-visible payloads. The gap is arbitration among them. The
system can produce a valid contribution, but it does not yet have one final
authority that proves: "this content performs the act this obligation asked
for."

## Reproduced Symptom Map

| Turn type | Observed result | First confirmed divergence |
| --- | --- | --- |
| Current self-state | A valid grounded self-state answer was followed by an attributed-evidence refusal. | Completion generated an unsupported resolution before the self-state exemption; the exemption did not remove the resolution or its semantic packet. |
| Current preference | A request for what Selene would like to explore became a request for an attributed source. | No authored-preference content owner satisfied the act, so universal factual-evidence fallback took ownership. |
| Paper pinwheel hypothesis | The object was treated as a source-backed research request. | The token `paper` was interpreted as a research cue without disambiguating material/object sense from publication sense. |
| Correction to the pinwheel observation | Approved change/stability material replaced reconstruction of the hypothesis. | Topic-word overlap selected knowledge without proving requested-role fit. |
| Airflow comparison | Observation and living-status lessons replaced the requested shared feature and discriminator. | Polysemous subject overlap outranked the requested comparison operation. |
| Pressure-pattern prediction | A lesson defining predictions replaced the requested prediction. | Knowledge *about* the answer kind was bound as though it had performed the answer kind. |
| Robot-arm inspection and plan | Plant/animal parts material appeared. | Weak or polysemous words such as `hold` and `without` acted as subject alignment. |
| Smallest paused action / available collaboration | A simple-machine lesson appeared. | `force` overlap supplied a definition while the action-scoping request remained unperformed. |
| Correction asking for first step and needed help | Organism-care and static-code lessons appeared. | Selected sentences were explicitly assigned to correction, inspection, and help obligations; coverage then trusted those assignments. |
| Return to the pinwheel | Earlier obligations and topic state contaminated the turn. | Unresolved open loops remained eligible when the new turn introduced no newly detected loop IDs. |
| Natural close | Closure worked. | No competing content owner or stale answer requirement displaced the social act. |

## Confirmed Roots

### R1 — Lexical cues can still become domain authority

`src/selene/meaning_router.py` contains a bounded research-cue path in which
`paper` can select source-backed research. The route metadata correctly says
that a single phrase should not be authority, but the concrete lexical path
still gives the material noun in "paper pinwheel" the publication/research
sense.

This is not merely a missing synonym. It is a missing sense decision before
domain selection.

### R2 — Epistemic ownership and conversational-act ownership are conflated

`src/selene/answer_completion.py` and `src/selene/answer_substance.py` use
attributed facts, approved concepts, and visible observations as broadly
available grounds for unanswered obligations. Those are appropriate grounds
for external factual claims. They are not the only valid grounds for:

- a current self-report,
- a current preference,
- a prompt-grounded hypothesis,
- a bounded prediction,
- a comparison performed from supplied observations,
- or a collaborative action-scoping answer.

The fallback therefore asks for evidence even when the answer is authored in
the current interaction or inferable from visible premises.

### R3 — The self-state exemption occurs after completion has already created
the wrong semantic answer

In `src/selene/selene_chat.py`, bounded completion is built before the
grounded-self-state exemption. The exemption changes status and sets
`accepted` false, but it leaves the generated resolutions and
`supported_semantics` attached. `compose_epistemic_answer` then consumes that
packet and appends the missing-ground refusal to the correct self-state answer.

The stored trace proves that:

- routing selected `self_state` with high confidence;
- visible speech selected `grounded_self_state`;
- the self-state packet supplied a current, limited, non-diagnostic answer;
- completion still represented the same obligation as `missing_ground`;
- explicit semantic binding marked the refusal as answering the obligation.

The self-state organ did not fail. Its answer lost ownership downstream.

### R4 — Approved-knowledge relevance does not require the requested response
function

`src/selene/comprehension_integration.py` ranks subject, central-claim, and
application overlap. `src/selene/semantic_relevance.py` permits direct-subject
acceptance without always requiring requested-role overlap. This allowed words
such as `time`, `observation`, `share`, `hold`, `without`, `force`, and `design`
to select conceptually adjacent or wholly unrelated lessons.

The missing contract is not "more keywords." It is typed role fit:

- defining prediction is not making a prediction;
- discussing observation is not performing a comparison;
- defining force is not identifying the smallest paused action;
- teaching inspection generally is not supplying the requested first step.

### R5 — Knowledge about an operation can substitute for performing the
operation

When no more specific knowledge fragment is found,
`src/selene/comprehension_integration.py` can use a concept's central claim for
a direct request. That makes a lesson describing a cognitive operation appear
eligible as the result of the operation.

This is the central content-ownership defect revealed by the prediction and
planning turns.

### R6 — Explicit obligation IDs are treated as proof instead of a claim to be
verified

`src/selene/knowledge_expression_reconstruction.py` copies
`answer_basis.obligation_support` IDs onto reconstructed semantic units.
`src/selene/selective_formation_braid.py` treats explicit obligation IDs as
authoritative mappings. `src/selene/pragmatic_planner.py` then counts the
matched units as coverage.

Consequently, an incorrect upstream binding can report complete coverage even
when the visible answer does not perform the requested act. This is stronger
than a loose-word coverage bug: provenance metadata is being mistaken for
semantic proof.

### R7 — Candidate selection is ordered acceptance, not global answer
arbitration

`src/selene/visible_speech.py` walks candidates in order and returns the first
candidate that passes visibility, source-class, relevance, and spine
compatibility checks. The candidate list in `src/selene/selene_chat.py` is
therefore also a priority policy.

Later recovery compares coverage counts, but it cannot recover reliably when
coverage itself trusts an incorrect obligation binding. A visible, compatible
candidate is not necessarily the best semantic owner of the turn.

### R8 — Open loops have persistence but not a complete lifecycle

`src/selene/dialogue_workspace.py` carries unresolved open loops forward and
removes them only when coverage reports their IDs as answered.
`src/selene/pragmatic_planner.py` considers all unresolved loops relevant when
a turn has no newly detected loop IDs.

There is no complete age, topic/thread relevance, supersession, explicit hold,
or supported-route release policy. A later callback or ordinary continuation
can therefore inherit obligations from an earlier failed answer.

Persistence is valuable. The defect is persistence without lifecycle state.

### R9 — Metacognitive retry can ask the assigned owner again but cannot repair
a wrong owner

`src/selene/owner_specific_retry.py` deliberately permits one retry using only
existing current-turn output from the exact assigned owner. It cannot invoke a
new organ, generate content, or reclassify ownership. This is a sound recursion
boundary, but it means metacognition can notice incompleteness while remaining
unable to say "the wrong organ owns this obligation."

The retry should remain bounded. A separate, one-time owner-reclassification
handoff is needed when the evidence identifies owner mismatch rather than
missing output.

### R10 — Exact-domain locks preserve valid facts but also preserve a bad
route

`src/selene/human_conversational_realization.py` treats verified math and
source-backed research as exact domains. `src/selene/native_language_organ.py`
also limits relational-expression and formation behavior for those domains.

This is correct once the route and answer are correct: Voice must not alter
math or source attribution. When an ordinary object is misrouted as research,
however, the same lock prevents NLO and affect guidance from restoring natural
conversation. Affect is downstream and advisory; it cannot repair content
ownership.

### R11 — Fluent expression can conceal an unresolved ownership error

NLO, Voice, conversation repair, and metacognition operate on content already
selected or labeled as supported. Their local checks can all be correct while
the answer is globally irrelevant. This explains why the output can be
grammatical, source-aware, and marked complete yet still fail the actual
question.

The needed repair belongs before expression—not inside a warmth template,
phrase replacement, or additional teaching packet.

## What Is Working And Must Be Preserved

- Core/Mind did not expand action authority.
- No memory, retained-knowledge, identity, personality, governance, training,
  LoRA, self-replication, or autonomy write occurred.
- The diagnostic attribution contract correctly marks Q&A results as module
  evidence rather than self-state evidence.
- Self-state kept historical care posture separate from a current emotion
  claim.
- Source-backed research refused to invent a source packet.
- Metacognitive retry remained bounded to one cycle and did not invent facts.
- Closure and relational expression remained available when no incompatible
  content owner displaced them.
- The trace payloads exposed enough routing, ownership, semantics, coverage,
  and retry state to locate these roots without adversarial testing.

## Repair Dependency Order

This order prevents later repairs from validating the wrong upstream state.

1. **Typed answer ownership before retrieval.** Distinguish external fact,
   current self-state, authored preference, prompt-grounded inference,
   prediction, hypothesis, comparison, and action-scoping obligations.
2. **Sense-aware domain selection.** Resolve object/material, publication,
   quoted-language, and other polysemous senses before a domain cue can own the
   turn.
3. **Scope the evidence fallback.** Require attributed evidence for external
   factual claims; do not impose it on current authored state or operations
   supported by visible premises.
4. **Require knowledge role fit.** Knowledge retrieval must match both subject
   sense and requested function. Grammatical or polysemous overlap cannot
   authorize an answer.
5. **Separate procedural knowledge from procedure execution.** "How to make a
   prediction" may support the prediction organ; it is not itself the
   prediction.
6. **Validate obligation bindings.** An explicit obligation ID is a producer
   claim. Coverage must independently verify that the unit performs the
   obligation's role and addresses its object.
7. **Give open loops lifecycle state.** Add topic/thread scope, age,
   supersession, supported hold/release, correction replacement, and explicit
   closure behavior.
8. **Allow one bounded owner-reclassification handoff.** Metacognition may
   redirect an obligation once when fit evidence shows wrong ownership; it may
   not recurse or invent content.
9. **Arbitrate candidates by compatible fulfillment.** Choose the candidate
   that best performs required obligations, rather than the first candidate
   that is merely visible and compatible.
10. **Apply exactness after route validation.** Preserve math and attribution
    exactly without letting a mistaken exact-domain route suppress ordinary
    conversational realization.
11. **Recheck self-state and affect ownership.** A valid current self-state
    packet must remain primary through composition; optional affect guidance
    should shape expression only after the answer owner is correct.

## Proportional Verification Plan

No broad voice grading or live stress battery is needed. After source repair:

1. Static contract tests for typed answer ownership and sense decisions.
2. Focused synthetic tests for each reproduced root:
   - paper object versus research paper;
   - current state and current preference;
   - perform versus define prediction;
   - perform versus describe comparison;
   - action scoping versus force definition;
   - correction superseding an earlier loop;
   - callback after a supported hold;
   - wrong-owner metacognitive reclassification limited to one cycle.
3. Neighboring protection tests for citations, verified math exactness,
   unsupported operations, memory boundaries, Core/Mind authority, and no
   hidden writes.
4. One short gentle integrated conversation only if the machinery tests cannot
   prove cross-turn coordination.

Poor or incomplete output remains evidence about the implementation. It is not
a failure assigned to Selene.

## Current Disposition

Aleks reviewed and authorized the dependency-ordered source repair. The runtime
now carries a typed answer-ownership contract from pragmatic planning through
the Conversation Spine, Answer Engine coordination, supported semantics,
completion, coverage, metacognitive feedback, visible-speech arbitration, and
NLO exactness handling.

The eleven mapped roots were repaired as follows:

1. `src/selene/answer_ownership.py` distinguishes the requested answer act,
   epistemic basis, responsible owner, answer domain, completion policy, and
   evidence requirement before retrieval.
2. Research selection now requires publication or attributed-source sense;
   an object such as a paper pinwheel does not become a research request.
3. Bounded completion preserves current-owner turns and applies external-
   evidence fallback only to obligations that actually require it.
4. Approved knowledge must match the requested subject and role. Knowledge
   describing a prediction cannot replace performing the prediction.
5. Supported semantic packets preserve declared response functions and
   ownership validation through normalization.
6. Explicit obligation IDs remain producer claims. Typed role-fit obligations
   require matching response function plus relevant meaning or validated owner
   performance before coverage accepts them.
7. Dialogue loops now carry age and lifecycle state. Unanswered loops remain
   available for a supported return, but are held from unrelated turns,
   released only by a sufficiently identified callback, superseded by a
   correction, completed by coverage, or closed with the conversation.
8. Metacognition may perform one visible owner reclassification when the typed
   answer owner conflicts with the coalition assignment. It cannot recurse,
   invent content, or change Core/Mind authority.
9. Visible speech inspects all releasable candidates and ranks compatible
   obligation fulfillment and owner fit. The first acceptable candidate is no
   longer automatically the answer.
10. Verified-math and source-attribution exactness locks activate only after
    the corresponding Answer Engine route and owner are validated.
11. Grounded self-state semantics are bound only to self-state-owned
    obligations and remain primary through completion and coverage.

No teaching was added to compensate for the defect. Additional language or
knowledge material can therefore resume later without feeding the former
misassignment paths.

### Verification after repair

- 223 focused architecture tests passed across ownership, Answer Engine,
  meaning routing, Conversation Spine, Dialogue Workspace, relevance,
  formation, completion, pragmatics, metacognition, retry, visible speech, and
  supported semantics.
- 110 complete Selene Chat shell tests passed.
- 2 neighboring verified-math diagnostic tests passed after the exactness
  validation change.
- Focused reproductions passed for paper object versus research paper,
  completed-repair self-state, perform-versus-define prediction, callback and
  correction loop lifecycle, one-cycle wrong-owner handoff, attributed source
  use, and the long desk replay.
- `git diff --check` reported only the repository's existing Windows
  LF/CRLF conversion warnings.

The verification was static and synthetic against temporary test databases.
No live resident stress conversation was needed.
