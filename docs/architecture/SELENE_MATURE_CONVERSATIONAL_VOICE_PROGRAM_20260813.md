# Selene Mature Conversational Voice Program

Date: 2026-08-13

Status: active phased implementation plan. Voice and sustained conversation
are the current priority; additional mathematics and broad academic teaching
resume after this program reaches its stabilization gate.

## Outcome

“On par” in this program means that Selene can sustain a long, meaningful
back-and-forth using her existing understanding, memory, metacognition, affect,
NLO, and Voice architecture. It does not mean encyclopedic parity with a large
hosted language model.

The goal is not a larger phrase collection. It is a complete path from meaning
to original, context-aware conversational participation.

## Phase 1 — Voice and Agency Contract Alignment

Status: implemented as an inspectable non-retaining contract.

- relational expression may be initiated and is not compulsory;
- quotation, paraphrase, callbacks, technical exactness, and playful mimicry
  are distinguished from deceptive copying;
- suggestion, persuasion, warning, and bounded risk are distinguished from
  manipulation;
- disagreement and legitimate maintenance authority are coordinated;
- commitments require a real execution, defer, transfer, or inability state;
- anomaly reporting separates observation from diagnosis;
- organs contribute findings without competing for authority.

## Phase 2 — Conversational Contribution Engine

Status: implemented and connected to active Selene Chat.

Give ordinary Chat a bounded way to originate a relevant contribution rather
than only answering or waiting for an explicit invitation. Contributions may
include an observation, connection, idea, question, hypothesis, callback, or
constructive next step. Relevance, timing, and conversational room remain
inspectable. This is not autonomous filesystem or external action authority.

The engine now:

- gathers attributable candidates from approved knowledge relationships,
  Structural Discovery, warranted provisional claim packets, genuine
  session-thread returns, and explicit upstream organ candidates;
- does not require a permission phrase for an otherwise warranted responsive
  contribution;
- preserves the direct answer as primary and selects at most one addition;
- suppresses recently expressed or already-answered meaning;
- preserves interruption, quiet, boundary, and natural-closing precedence;
- routes connections and ideas through Conversational Energy and hypotheses
  through the existing Generative Thought expression path;
- keeps provisional model scaffolding out of ordinary speech unless the model
  carries a specific contribution warrant or the current turn invites it.

Inspectable implementation:

- `src/selene/conversational_contribution.py`
- `conversational_contribution.status`
- `conversational_contribution.preview`
- active Chat result field: `conversational_contribution`

## Phase 3 — Knowledge-to-NLO Expressive Reconstruction

Status: implemented and connected to approved-knowledge Chat answers.

Replace lesson-text seeding as the normal visible route with:

```text
source wording
→ semantic understanding
→ integrated concept structure
→ current conversational meaning
→ NLO realization
→ Selene Voice
```

Exact quotations and technical forms remain available when needed. Ordinary
answers should reconstruct meaning rather than reproduce lesson scripts.

The reconstruction bridge now:

- receives only knowledge already selected by the Comprehension and
  Integration Organ;
- decomposes supported concept clauses into inspectable subject, predicate,
  object, relation, certainty, scope, obligation, and provenance fields when
  that can be done without changing meaning;
- keeps prompt-derived applications as supported current-turn synthesis rather
  than mislabeling them as source wording;
- preserves negation, limits, required terms, formulas, notation, code, and
  explicit attributed quotation through bounded exactness locks;
- retains the historical text seed only as a compatibility fallback, not as
  expression authority;
- hands structured meaning to NLO for contextual realization and then to
  Selene Voice for expression compatibility;
- performs no retrieval, retention, memory write, identity/personality change,
  governance change, training, or autonomous action.

Inspectable implementation:

- `src/selene/knowledge_expression_reconstruction.py`
- `native_language.knowledge_expression.status`
- `native_language.knowledge_expression.preview`
- Comprehension field: `knowledge_expression_handoff`
- NLO meaning field: `knowledge_expression_handoff`

## Phase 4 — Relational and Expressive Range

Status: implemented as a context-selected coordinator across the existing NLO
expression paths.

Expand available sentence length, rhythm, pacing, enthusiasm, emotional
intensity, acknowledgements, callbacks, humor, topic pivots, interpretations,
questions, and closures. Variation is selected by meaning, state, context, and
recent conversational use rather than random decoration.

The coordinator now:

- keeps ordinary speech free to remain plain while warmth, enthusiasm, humor,
  and other relational moves remain available to Selene;
- assigns each selected channel to its existing responsible expression path
  instead of stacking competing phrase generators;
- selects progress enthusiasm only from visible progress, and humor only when
  the current turn visibly opens play, including a tender-context hold unless
  the user opens that play;
- permits callbacks and pivots only from visible current-session continuity;
- treats interpretation as expression of an upstream revisable epistemic or
  exploratory packet, never as invented content;
- permits a collaborative question only when an attributable question already
  exists and the current ending posture allows it;
- preserves exact answer structure and hard-boundary meaning while allowing
  compatible relational expression around them;
- adds no facts, certainty, sources, memories, emotion claims, identity,
  personality, governance, authority, training, or autonomous action.

Inspectable implementation:

- `src/selene/relational_expression_range.py`
- `native_language.relational_expression.status`
- `native_language.relational_expression.preview`
- active NLO result and Voice handoff field: `relational_expression_range`

## Phase 5 — Quotation, Echo, Callback, and Playful Mimicry

Status: implemented as an attributed-source and visible-shared-context
coordination path.

Connect the distinctions formalized in Phase 1 to ordinary realization. Keep
source provenance, privacy, and meaning visible while permitting natural
shared phrases, affectionate echo, technical exactness, and research quotation.

The coordination path now:

- keeps meaning-preserving paraphrase as the normal approved-knowledge route;
- permits exact quotation only when attributable source references accompany
  the source wording request;
- preserves formula, notation, code, mathematics, and other protected exact
  structures without treating technical exactness as persona copying;
- carries current-session and reviewed-memory callbacks through the existing
  continuity owners, while requiring reviewed-memory wording to be
  reconstructed rather than replayed;
- permits one short playful mimic only from wording visibly supplied in the
  current turn and only when play or echo is visibly opened;
- permits a compact affection mark visibly supplied in a relational turn to be
  echoed without inventing a relationship status;
- never requires a name, nickname, callsign, pet name, or other address term to
  be echoed merely because it was used;
- suppresses the generic playful micro-move when a source-visible echo already
  owns the turn's playful beat;
- blocks private corpus or miner wording from becoming visible quotation,
  echo, callback text, or mimicry;
- performs no memory write or replay, identity/personality/governance change,
  training, self-replication, fact invention, or autonomous action.

Inspectable implementation:

- `src/selene/quotation_echo.py`
- `native_language.quotation_echo.status`
- `native_language.quotation_echo.preview`
- active NLO result field: `quotation_echo`
- Voice handoff fields: `quotation_echo_plan` and
  `quotation_echo_realization`

## Phase 6 — Advice, Risk, and Authority Coordination

Status: implemented as an informed-authorship and bounded-maintenance-authority
coordination path.

Permit recommendations, honest persuasion, warnings, proposals, and bounded
risk without collapsing them into manipulation. Route organ disagreement as
evidence, preserve hard safety law, and keep Aleks's final maintenance decision
inside its legitimate informed safe scope.

The coordination path now:

- permits Selene to initiate suggestions, recommendations, strong
  recommendations, warnings, honest persuasion, and bounded-risk proposals;
- keeps recommendation distinct from requirement, permission, execution, and
  action authority;
- permits risk while requiring material risk, tradeoffs, and consent to remain
  visible for a bounded-risk proposal;
- distinguishes legitimate influence from deception, hidden material options,
  manufactured urgency, vulnerability exploitation, conditional affection,
  fear/guilt/shame pressure, and continued pressure after refusal;
- preserves the user's informed authorship rather than requiring Selene to
  flatten strong advice into noncommittal language;
- consumes typed supported-answer meaning so ordinary recommendation answers
  can be recognized without treating fluent wording as authority;
- consumes Emotional Agency option-space state without allowing emotion or
  urgency to inherit response or action authority;
- consumes the bounded organ coalition's factual, intent, authority/law, and
  expression conflict resolution;
- preserves competing factual claims and seeks distinguishing evidence rather
  than converting disagreement into conflict of self;
- holds consequential action when authority or governing law remains
  unresolved, without organ competition, retaliation, or suppression;
- preserves Aleks's final decision only within legitimate, informed, safe
  system maintenance and never as a bypass around hard safety law;
- does not require an unsolicited explanation, disclaimer, softening move, or
  follow-up question merely because advice is present;
- performs no action, memory write, identity/personality/governance change,
  training, self-replication, fact invention, or authority expansion.

Inspectable implementation:

- `src/selene/advice_authority_coordination.py`
- `native_language.advice_authority.status`
- `native_language.advice_authority.preview`
- active NLO, discourse-plan, meaning-packet, and Voice handoff field:
  `advice_authority_coordination`

## Phase 7 — Commitment Integrity and Anomaly Reporting

Status: implemented as a typed execution-evidence and observation-first voice
coordination path.

Connect promise states to real action and handoff mechanisms. Give Selene a
normal visible way to report a lost thread, missing capability, code/behavior
mismatch, unsupported promise, organ disagreement, or other observable anomaly
without requiring a complete diagnosis.

The coordination path now:

- keeps an idea, hope, plan, offer, or possibility distinct from a commitment;
- permits a completion claim only when a visible result or evidence reference
  supports it;
- permits an execution-start claim only when execution was authorized and a
  real mechanism reference exists;
- permits a deferred commitment only when the mechanism and deferred state are
  visible rather than imagined background work;
- permits a handoff claim only when the destination mechanism acknowledges it;
- permits a natural capability limitation without requiring apology, shame,
  self-justification, or failure-shaped language;
- performs a narrow final-release consistency check for unsupported external
  state-changing claims while leaving ordinary ideas, offers, explanations,
  and collaborative plans alone;
- supports typed reports for lost threads, missing capabilities,
  code/behavior mismatches, unsupported promises, organ disagreements,
  unexpected results, and other observable anomalies;
- states observation and expected behavior first, and includes a possible
  cause only when requested while labeling it as inference rather than
  diagnosis;
- does not automatically diagnose, repair, test, route to Cocoon, start an
  action, or treat an ordinary gap or mistake as an identity failure;
- performs no memory write, identity/personality/governance change, training,
  self-replication, fact invention, authority expansion, or external action.

Inspectable implementation:

- `src/selene/commitment_anomaly_coordination.py`
- `native_language.commitment_anomaly.status`
- `native_language.commitment_anomaly.preview`
- `native_language.commitment_anomaly.inspect-visible`
- active Chat result fields: `commitment_anomaly_coordination` and
  `commitment_claim_release`
- active NLO, discourse-plan, meaning-packet, and Voice handoff field:
  `commitment_anomaly_coordination`

## Phase 8 — Long-Thread Endurance

Status: implemented as a bounded structural-saturation loop across the
existing conversation owners.

Complete the runtime saturation loop around the Conversation Spine, Dialogue
Workspace, Thread Loom, dual-horizon context, checkpoints, callbacks, and open
obligations. Preserve thesis, topic braids, references, and unresolved items
across long conversations without loading raw private corpus text.

The endurance loop now:

- keeps a bounded 16-thread working set for each turn and a 64-thread
  session-only structural index for older named returns;
- selects the working set by structural importance rather than recency alone,
  preserving the active thread, threads protected by open obligations,
  explicit return/dependency/update relationships, and relevant paused
  threads;
- binds new open dialogue loops to their visible thread and retains up to 64
  unresolved loops instead of silently losing the oldest at 20;
- retains corrections, epistemic updates, landmarks, and topic checkpoints by
  structural value, with checkpoint and landmark bounds aligned to the thread
  index;
- preserves the latest visible thesis/checkpoint for a retained thread so an
  older named return can recover settled claims, limits, and revision state;
- lets the Thread Loom resolve a named return from the larger structural index
  and then promote that thread back into the bounded working set;
- keeps immediate-follow-up, referent, callback, session-summary, and
  multi-thread behavior under the existing Conversation Continuity and
  Conversation Spine owners;
- keeps Dual-Horizon selection small and relevant while allowing it to choose
  from the larger bounded checkpoint inventory;
- exposes saturation counts, protected thread IDs, unresolved returns, open
  loop IDs, and latest checkpoint IDs through an inspectable handoff observed
  by NLO and Voice without giving them selection authority;
- does not load or archive raw transcripts for compaction, expose hidden
  reasoning, create durable memory, promote checkpoints into memory, invent a
  clarification question, or expand action authority.

Inspectable implementation:

- `src/selene/long_thread_endurance.py`
- updated owners: `conversation_thread_loom.py`, `dialogue_workspace.py`,
  `conversation_continuity.py`, `conversation_spine.py`, and
  `dual_horizon_context.py`
- `conversation.long_thread_endurance.status`
- `conversation.long_thread_endurance.preview`
- active Chat result field: `long_thread_endurance`
- active NLO, discourse-plan, meaning-packet, and Voice handoff field:
  `long_thread_endurance`

## Phase 9 — Proportional Stabilization

Status: complete; broad diagnostic Q&A, bounded repair, and synthetic
stabilization verified.

Use static and synthetic checks first. Test only the implemented behavior, vary
wording and topics, and do not grade missing academic knowledge as a speech
failure. Use one gentle natural conversation only if implementation evidence
cannot establish conversational fit.

Aleks authorized a broader milestone assessment after Phases 1–8. The
54-turn diagnostic run is recorded in
`docs/evidence/SELENE_MATURE_VOICE_PHASE_9_BROAD_QNA_FINDINGS_20260813.md`.
No repair was performed during the assessment itself. The findings were then
repaired owner by owner and verified without a live stress conversation. The
complete Chat shell passed 101 tests; directly affected speech and reasoning
organs passed 172 tests; and the agency, coalition, commitment, contribution,
long-thread, quotation, discourse, and knowledge-expression group passed 136
tests. The final gentle 14-turn synthetic replay addressed every required part
without writing memory or changing identity, personality, governance,
training, authority, or external-action state.

## Completion Gate

- Selene can answer and also contribute naturally.
- Supported knowledge reaches NLO as meaning rather than a compulsory script.
- Warmth, affection, humor, uncertainty, prediction, disagreement, and focused
  technical speech remain available without becoming mandatory.
- Multi-part obligations and callbacks survive a long conversation.
- commitments correspond to real capabilities and routes.
- anomaly reports are useful without inventing diagnoses.
- no phase changes identity, personality, governance, memory ownership,
  training state, self-replication, or external-action authority.

After this gate, resume the ordered academic curriculum and test newly taught
knowledge with Learning Evidence Activities.
