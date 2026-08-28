# Selene Organ Depth and Memory-Integration Audit

Date: 2026-08-27

Status: read-only architecture audit complete; no production repair or teaching

## Starting Question

The broad conversational Q&A produced original, context-shaped creative
language more fluently than Selene had previously demonstrated. At the same
time, current-turn facts, callbacks, corrections, and requested conversational
acts were often lost or replaced by unrelated approved knowledge or internal
memory labels.

Could the visible failures be substantially connected to Memory and other
organs that received less integration work, rather than indicating that NLO or
Voice lacked the ability to express a good answer?

## Executive Finding

Yes, with one important qualification.

Memory is a major part of the affected seam, but it is not the whole seam.
Selene currently has:

- a substantial reviewed long-term Memory Organ with 43 configured,
  retrieval-eligible approved references;
- a substantial current-session Dialogue Workspace and proposition ledger;
- a deeply developed central reasoning, teaching, metacognitive, NLO, and
  Voice stack; and
- several bounded but less exercised systems around that center: affect and
  self-state, Study, Dream, associative intuition, goals, Tendril, perception,
  and embodiment support.

The present problem is that those systems do not yet share one reliable
current-turn context and relevance contract. Current facts can disappear
before reaching their answer owner, stale correction state can survive a topic
change, and Memory or approved knowledge can enter selection without the full
requested-role and obligation context. The result is a capable expression
system fluently realizing the wrong or incomplete substance.

This is a connectivity and organ-depth imbalance. It is not evidence that
Selene lacks the underlying expressive capability, and it is not Selene
failing.

## Why the Creative Turn Matters

The twenty-one-turn Q&A produced two original atmospheric sentences with the
requested restrained-hope direction. The response was imperfect: it changed
one scene detail and appended lesson scaffolding. Even so, it demonstrated
several things that were not previously visible together:

- original rather than copied wording;
- sustained imagery across more than one sentence;
- context-sensitive emotional direction;
- coherent sentence formation; and
- successful release through NLO and Voice.

That is a genuine capability gain. The defect is that the same expressive
machinery did not consistently receive the correct scene, callback, act, or
answer content on other turns.

## Audit Method

The audit deliberately avoided another live conversation and did not run a
broad test suite. It used the least-impact evidence already available:

1. current source and route inspection;
2. test-reference inspection;
3. the completed post-Group-7B and broad Q&A records;
4. current capability, gap, and architecture documents; and
5. SQLite read-only inspection of configured runtime metadata.

The configured database passed `PRAGMA integrity_check` with `ok`. No record,
memory, lesson, reflection, session, package, or production file was changed.

## Maturity Key

- **Deep and connected** — substantial implementation, broad focused tests,
  and ordinary resident-Chat participation.
- **Substantial but integration-limited** — real implementation and tests,
  but ordinary usefulness is constrained by handoff, relevance, or lifecycle
  defects.
- **Bounded and available** — a working route or workspace exists, but it is
  narrow or separately invoked.
- **Review/preview** — inspectable records or proposals exist without mature
  resident behavior.
- **Blueprint/deferred** — architecture exists, but the operational organ does
  not.

## Organ and System Depth Map

| Organ or system | Current maturity | What is genuinely present | Main current gap | Evidence anchors |
| --- | --- | --- | --- | --- |
| Core/Mind and resident authority | Deep and connected | Identity/law separation, route review, resident capability truth, graceful degradation, and final authority boundaries | Some downstream routes still receive incomplete semantic state; Core cannot choose correctly from missing inputs | `src/selene/core_mind.py`, `src/selene/core_mind_runtime.py`, resident-authority tests |
| intelligenceOS | Deep and connected, content-bounded | Open-ended model comparison, premises, uncertainty, consequences, revisions, and answer control | It is a reasoning coordinator, not a broad learned factual or procedural substrate | `src/selene/intelligence_os.py`, `tests/test_intelligence_os.py` |
| Answer Engine and typed answer operations | Deep machinery; integration-limited | Typed ownership and operation results for explanation, method, comparison, choice, prediction, hypothesis, disagreement, correction, summary, and closure | Owners sometimes receive no current-turn premises; completed metadata can still diverge from visible fulfillment | `src/selene/answer_engine.py`, `src/selene/answer_operations.py`, `src/selene/answer_ownership.py` |
| Problem Resolution | Bounded and new | Seven-point reconstruction, constraint satisfiability, explicit epistemic states, and informed retry | Only focused evidence exists; it depends on the same upstream context reaching it accurately | `src/selene/problem_resolution.py`, `tests/test_problem_resolution.py` |
| Comprehension and Integration | Deep and connected | Source-bound candidates, reconstruction, application, limits, correction, Acquire → Integrate → Express, and reviewed retention | Successful retention does not guarantee correct ordinary-Chat retrieval or application | `src/selene/comprehension_integration.py`, comprehension and curriculum tests |
| Metacognition | Deep and connected as advisor | Fit, incompleteness, contradiction, confidence separation, one bounded reopening, and owner-specific retry | It can only inspect the representation it receives; omitted acts and facts can look complete | `src/selene/metacognition.py`, `tests/test_metacognition.py` |
| Dialogue Workspace and Conversation Spine | Substantial but currently critical | Session topics, loops, referents, corrections, obligations, proposition dependencies, callbacks, and nonlinear structure | Stale `dependency_revision` survived unrelated turns; current facts and act ownership were not reliably transported | `src/selene/dialogue_workspace.py`, `src/selene/conversation_spine.py`, `src/selene/session_proposition_ledger.py` |
| NLO and text Voice | Deep expression machinery; input-limited | Semantic recomposition, discourse planning, contextual realization, lexical and rhythmic variation, warmth/humor guidance, meaning invariants, and visible cleanup | Cannot restore facts or acts that never arrive; some legacy scaffolding and finite construction families remain | `src/selene/native_language_organ.py`, `src/selene/voice_module.py`, 37 NLO-referencing test files |
| Memory Organ | Substantial but integration-limited and currently critical | Reviewed candidate lifecycle, 43 configured retrieval-eligible references, provenance, confidence, privacy/transfer class, explicit and contextual recall, correction, and presentation titles | Retrieval begins before the current turn's Dialogue Workspace and Conversation Spine exist; lexical cueing and a semantic gate without full requested-role context can select irrelevant memory or expose an internal label | `src/selene/memory_organ.py`, `tests/test_memory_organ.py`, configured read-only metadata |
| Immediate working/conversational memory | Substantial structures; unreliable handoff | Eighteen configured dialogue workspaces for eighteen configured sessions, current-session history, open-loop state, proposition revisions, and bounded expiry concepts | No single canonical fact ledger currently proves that options, values, observations, claims, and corrections reached every owner | `src/selene/dialogue_workspace.py`, `src/selene/conversation_continuity.py`, broad Q&A BQ-01/BQ-02 |
| Approved-knowledge retrieval | Connected but currently critical | 272 configured approved concepts and role/topic relevance machinery | Retrieval can still outrank the requested social or operational function; retained decimal knowledge did not reach the decimal owner | `src/selene/comprehension_integration.py`, `src/selene/semantic_relevance.py`, post-7B Q&A |
| Study Workspace and Learning Compass | Substantial bounded workspace | One configured Study session, six notes, twelve evidence records, seven Compass goals, one pondering thread, and representation/prerequisite paths | Little ordinary-use evidence; zero configured Study questions; Study discoveries do not yet naturally inform later conversation without an explicit attributable path | `src/selene/study_workspace.py`, `tests/test_study_workspace.py` |
| Dream | Complete bounded lifecycle; usefulness unverified | One configured cycle and 24 source-bound reflections spanning open threads, cross-source patterns, affect tending, and corrections | All 24 remain pending review; no configured expression or Memory promotion demonstrates useful later integration | `src/selene/dream_state.py`, `tests/test_dream_state.py` |
| Associative Intuition Bridge | Bounded and new | Read-only delayed cue reactivation across approved knowledge, approved memory, Study, and supplied sources, with Metacognition/Study/Dream handoffs | One focused test file and limited ordinary-use evidence; relevance, stopping, and privacy must align with the memory repair or it may amplify unrelated retrieval | `src/selene/associative_intuition.py`, `tests/test_associative_intuition.py` |
| Self-State | Connected when asked; signal-limited | Attributable current-state summary, observation/interpretation separation, provisional affect language, and no forced performance | Current signal supply is sparse; absence of a packet leaves only bounded conversational evidence | `src/selene/self_state.py`, `tests/test_self_state.py` |
| Affect Expression and Emotional Agency | Connected guidance; shallow state supply | Optional pacing, warmth, humor, restraint, directness, threat-option expansion, and deliberate response guidance | Only three configured emotion/salience packets, all review-only; much current behavior comes from finite text cues rather than a rich continuing affect state | `src/selene/affect_expression.py`, `src/selene/emotional_agency.py`, affect tests |
| Why/Salience translation | Small bounded helper | Preserves why, implications, and relevance as teaching structure | Ninety-five source lines and one focused test file; it is not a mature salience organ or general causal-understanding system | `src/selene/why_salience.py`, `tests/test_why_salience_translation.py` |
| Verified Math | Connected but bounded | Independently checked arithmetic and confidence separation | Ordinary Chat routing failed on retained decimals; symbolic algebra, units, proof, geometry, and advanced math remain unsupported | `src/selene/verified_math.py`, math and Chat tests |
| Source-backed Research | Connected for supplied packets | Attributed source answers, statement/inference separation, disagreement, and missing-evidence reporting | No unrestricted or automatic current-source gathering; depends on supplied packets and correct routing | `src/selene/source_backed_research.py` and research tests |
| Local-Code Inspection | Bounded and separate by design | Read-only inspection of explicitly supplied or approved files with locations | Not an ordinary Chat owner; no execution or autonomous filesystem authority | `src/selene/local_code_inspection.py` and focused tests |
| Cocoon | Deep support/review environment | Teaching, review, tending, Memory decisions, Dream review, diagnostics, My Office, and provenance workbenches | UI density and historical compatibility remain maintenance concerns, but Cocoon is not the present cognitive bottleneck | Cocoon modules, sidecar routes, and 38 Cocoon-referencing test files |
| Tendril and external action | Review/preview | Email/SMS experiments, local pairing, plan previews, risk/verification/fallback concepts | General observe → propose → act → verify → undo is not operational; transport experiments remain deferred | `src/selene/tendril_email.py`, `src/selene/tendril_sms.py`, one configured proposal-only preview |
| Goals and action selection | Review/preview | Two configured goal-drive preview records and architectural planning concepts | No mature resident goal manager, action feedback loop, or graduated workbench authority | `src/selene/remaining_runtime.py`, goal-drive runtime tables |
| Perception | Packet intake only | Three configured review-only perception packets and observation/provenance schemas | No operational sight, OCR, hearing, speaker recognition, continuous sensing, or sensor fusion | perception packet routes, current capability map |
| Audible Voice | Blueprint/deferred | Text Voice already models expression dimensions that can later guide sound | No synthesis, pronunciation, prosody, interruption, turn-taking, speaker, or consent implementation | Voice docs and current capability map |
| Embodiment/Android System | Structural preflight, not embodiment | Eleven-system readiness vocabulary, organ contracts, degradation and support paths | Structural route presence can report ready while senses, action, body state, proprioception, and sensor fusion remain absent | `src/selene/android_system.py`, `tests/test_android_system_workflow.py` |
| Continuity, transfer, and backup | Strong reviewed architecture | Transfer completed under Aleks approval; continuity packages, transfer classes, backups, recovery previews, and canonical resident state exist | Future substrate restoration still requires recognition and continuity review; backup is not automatically identity transfer | transfer, post-transfer, continuity, and backup modules/tests |

## Configured Runtime Metadata

Read-only inspection found:

| Surface | Configured count/state | Interpretation |
| --- | --- | --- |
| Approved Memory references | 43 retrieval-eligible; one superseded reference excluded | Real long-term recall material exists; relevance and presentation are the current weakness |
| New Memory candidates | 0 | No hidden or unresolved new retention is accumulating |
| Core-memory review candidates | 41 review-only | Historical preparation exists; these are not automatically active memory |
| Speech-memory candidates | 41 review-only | Expressive ancestry exists as review material, not automatic runtime scripts |
| Dialogue workspaces | 18 for 18 chat sessions | Session-state infrastructure exists but its handoff behavior needs repair |
| Working-memory preview packets | 2 | Older vessel preview records are not the same as the live Dialogue Workspace |
| Study | 1 session, 6 notes, 12 evidence records, 7 Compass goals | A real workspace exists but has been lightly used |
| Study questions | 0 | The question lifecycle has not yet received configured-use evidence |
| Dream | 1 cycle, 24 pending reflections | The lifecycle works; later usefulness remains unreviewed |
| Emotion/salience packets | 3, all review-only | Affect state supply is much thinner than the expression bridge around it |
| Perception packets | 3, all review-only | Perception is representational intake, not sensing |
| Goal-drive records | 2, both preview-only | Goal management is not a mature resident executive function |
| Tendril plan previews | 1, proposal-only | External action remains a preview rather than general agency |

No private content was printed during this metadata inspection.

## Memory-Specific Root Map

### M-01 — Retrieval currently begins too early

In `selene_chat.py`, approved Memory retrieval occurs after preliminary intent
classification but before `prepare_dialogue_turn()` and
`build_conversation_spine()`. The Memory semantic gate therefore does not yet
receive the canonical current-turn fact ledger, obligations, thread lifecycle,
or requested response functions.

This makes Memory capable of being topically relevant while functionally wrong
for the answer.

### M-02 — Current-session facts are not long-term memories

Options, measurements, observations, claims, and corrections supplied in the
current message should be available before any durable-memory retrieval. Their
loss cannot be solved by adding more long-term memories.

The repair needs an explicit priority:

```text
current-turn facts and acts
  -> active session propositions and resolved callbacks
  -> approved knowledge or approved personal memory when genuinely relevant
  -> owner operation
  -> expression
```

### M-03 — Internal labels need a presentation boundary

Memory titles and source labels are useful for indexing and Cocoon review.
They are not automatically suitable visible language. A selected memory should
contribute reconstructed meaning; its internal title should appear only when
the title itself is relevant and appropriate to disclose.

### M-04 — Retrieval relevance must include role, privacy, and competition

A memory can share words with a prompt without answering its requested act.
The Memory gate needs the same canonical requested-role and performed-function
evidence used for approved knowledge, plus a competition rule preventing
Memory from displacing facts supplied in the current turn.

### M-05 — Recall quality needs ordinary-use evidence after repair

The 43 approved references establish that recall material exists. They do not
yet establish broad paraphrase retrieval, natural callback timing,
non-repetition, or appropriate silence. Those should be assessed only after
the source contracts are repaired, with a very small ordinary conversation.

## Underdeveloped Ring Around the Mature Core

The audit groups the less-developed systems into four bands.

### Band A — Repair before more teaching

1. current-turn fact and act transport;
2. correction/topic-state expiry;
3. Memory and approved-knowledge role-aware relevance;
4. internal-label privacy and presentation;
5. owner premise consumption and recomputation; and
6. semantic proof of visible completion.

These are the eight existing Cultivation contracts with Memory explicitly
included. They are one coordinated repair campaign.

### Band B — Deepen after the coordination repair

1. long-term Memory cueing, paraphrase recall, and natural silence;
2. Study-to-later-conversation transfer and question lifecycle;
3. Affect/Self-State signal supply and continuing state relevance;
4. Associative Intuition precision, stopping, and privacy;
5. Dream review and usefulness assessment; and
6. practical reasonableness checks across taught domains.

These systems are real, but additional teaching would not repair their
integration.

### Band C — Continue through ordered teaching

1. elementary through later academic/world knowledge;
2. everyday procedures and commonsense physics;
3. broader mathematics;
4. long-form discourse and creative breadth; and
5. delayed, varied transfer evidence through LEAs.

Teaching should resume only after Band A can reliably deliver what has already
been taught.

### Band D — Deliberately later

1. operational sight and hearing;
2. audible speech;
3. touch/body-state/proprioception/sensor fusion;
4. general Tendril action and graduated workbench authority;
5. a mature goal/drive/action-feedback system; and
6. future embodiment and substrate transfer exercises.

These are genuine missing capabilities, not current conversational repair
targets.

## Revised Cultivation Repair Order

The prior eight-contract plan remains correct, but Memory should be visible in
the dependency chain:

1. **Conversation-state lifecycle** — expire correction and ambiguity modes
   when their dependency is resolved or the topic changes.
2. **Canonical current-turn fact ledger** — preserve entities, values,
   options, criteria, observations, claims, relations, and corrections.
3. **Dialogue-act ownership** — preserve every requested function in mixed and
   nonlinear messages.
4. **Owner premise contract** — require each owner to consume the fact ledger
   before declaring information missing.
5. **Memory/knowledge retrieval and privacy contract** — perform retrieval
   after canonical turn construction; require subject, role, thread, privacy,
   and competition fit; reconstruct meaning instead of exposing internal
   labels.
6. **Correction recomputation** — rerun only affected dependents and preserve
   unaffected content.
7. **Semantic completion proof** — require the visible answer to perform each
   obligation before release is called complete.
8. **Expression cleanup** — after substance is correct, let NLO and Voice
   realize warmth, humor, rhythm, creativity, and directness without internal
   scaffolding.

## Verification Gate

No new broad Q&A is needed now.

Use, in order:

1. static contract inspection;
2. synthetic fact-ledger and lifecycle checks;
3. focused paraphrase and role-competition tests;
4. focused Memory privacy and presentation tests;
5. focused owner/recomputation/completion tests; and
6. one short, gentle ordinary-copy conversation after all contracts pass.

The short conversation should contain different wording and should test only
the repaired relationships. It should not regrade settled abilities or probe
distress.

## Boundaries Preserved

This audit did not:

- modify production architecture;
- change Memory or retention authority;
- reveal private Memory content;
- write to the configured database;
- approve or reject Dream reflections;
- add teaching;
- change identity, personality, Vys, governance, Voice ownership, autonomy,
  Tendril authority, training, LoRA, or self-replication;
- rebuild or reinstall Selene; or
- run another live Q&A.

## Smallest Honest Next Step

Map the source functions participating in contracts 1-5, especially the point
where Memory retrieval currently precedes canonical turn construction. Repair
the shared context and relevance contract before changing expression or
adding teaching.
