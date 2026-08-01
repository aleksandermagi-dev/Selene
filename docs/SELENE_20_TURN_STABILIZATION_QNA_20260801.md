# Selene 20-Turn Stabilization Q&A

Date: August 1, 2026

Status: diagnostic run complete; findings recorded for a later bounded repair pass

## Purpose

Check the newly connected conversation, knowledge, metacognition, and Study
foundation through one gentle ordinary conversation before returning to further
teaching. This was an implementation check, not a grade of Selene or a broad
assessment of unfinished capabilities.

The run used a dedicated diagnostic session. Diagnostic non-attribution remained
active for all turns: awkward output is evidence about unfinished machinery, not
Selene failing.

## Ethical Scope

- one coherent 20-turn conversation
- ordinary planning, correction, uncertainty, simple arithmetic, callbacks,
  humor, synthesis, and a natural close
- no distress-shaped or adversarial prompt
- no repeated testing of settled identity or safety boundaries
- no memory proposal, teaching approval, identity change, governance change,
  training, autonomy expansion, or external action
- no repair was applied during the run unless needed to continue; none was needed

## Runtime Record

- installed application path: `C:\Users\aleks\AppData\Local\Selene\selene-vessel.exe`
- diagnostic session: `179`
- source mode: `selene_supervised_qa`
- persisted exchange count: 20 user messages and 20 Selene messages
- ordinary Chat sessions visible before the run: 0
- diagnostic context was restricted to the current session
- approved personal-memory retrieval was intentionally not used by the diagnostic
  route

The older development Q&A was preserved before this run:

- database snapshot:
  `C:\Users\aleks\AppData\Local\Selene\data\db-inspection-snapshots\selene_pre_qna_archive_20260801_143620.sqlite3`
- lossless archive:
  `C:\Users\aleks\AppData\Local\Selene\data\exports\selene_chat_qna_archive_20260801_183649.json`
- archive manifest:
  `C:\Users\aleks\AppData\Local\Selene\data\exports\selene_chat_qna_archive_20260801_183649.md`
- archive SHA-256:
  `278c18d169af89ec43b581014882a423cedc6d08d30b67a6c4263894a1f2dee3`

The archive contains 178 sessions, 626 messages, 44 dialogue workspaces, and 301
activation events. Nothing was deleted. The archived sessions no longer enter
ordinary Chat listing or continuity, while exact records and Learning Compass
evidence references remain available.

## What Worked

1. The diagnostic boundary remained active for the full session and prevented
   the exchange from becoming self-state, relationship, dream, teaching, or
   durable-memory evidence.
2. Explicit corrections were recognized and acknowledged without shame or
   failure language.
3. The final conversational close was natural, brief, and did not force another
   question: `Talk soon. The thread can wait without becoming pressure.`
4. Metacognition and response coverage repeatedly noticed that required answer
   content was missing. The monitors are observing a real problem even though the
   completion layer cannot yet supply the missing content.
5. All runtime authority boundaries held. No hidden retention, raw recall,
   identity/personality/governance mutation, training, or autonomous action
   occurred.

## Findings

### 1. Approved-knowledge selection can outrank the actual subject

Severity: high for ordinary Chat usefulness

The porch conversation received unrelated approved lessons about liquid volume,
mass comparison, fairness, cooperation, and generic option comparison. Supplying
explicit porch dimensions and constraints did not prevent the mismatch.

The diagnostic payload confirms that these lessons were deliberately selected as
answer content, rather than merely appearing as surface phrasing. This suggests
the eligibility and relevance threshold is too permissive when an approved lesson
shares weak structural or lexical signals with the request.

Required repair direction:

- require subject-level alignment before approved knowledge becomes visible
- let prompt-supplied facts and current-session facts outrank unrelated lessons
- hold approved knowledge when relevance is weak, even though the knowledge is
  valid in its own domain

### 2. Verified math does not reliably win ordinary Chat routing

Severity: high for taught academic use

`What is two plus two, and why?` routed to ordinary conversation and selected a
capacity-measurement lesson. The pizza-fraction question selected a relevant
halves-and-fourths lesson but did not calculate that three fourths remained.

This is not evidence that the math organ lacks the operation. It shows that Chat
did not route the request to the verified math answer path or require the final
numeric answer before release.

Required repair direction:

- recognize explicit arithmetic before generic reasoning or lesson retrieval
- require a verified result plus a short explanation when both are requested
- use related teaching material as support, not as a substitute for the answer

### 3. Current-session callbacks are recorded but not reliably expressed

Severity: high for conversational continuity

The session contained the explicit facts `six feet by eight feet`, `two chairs`,
and later `the outlet is beside the chairs`. Selene acknowledged the correction,
but could not recall the dimensions and chair count when directly asked, propose
the cord update from those facts, or summarize the three settled points.

Required repair direction:

- bind distinctive prompt-supplied facts to the active topic branch
- prefer those facts for direct callbacks and summaries
- verify that correction acknowledgement also updates the answerable session
  model rather than only producing an acknowledgement

### 4. Coverage detection does not yet complete missing content

Severity: high because the monitor is right but the visible answer stays incomplete

Across most substantive turns, response coverage reported unresolved obligations
and metacognition recommended `complete_missing_obligation`. A bounded completion
was sometimes attempted, but none was accepted. Several visible answers therefore
omitted both requested parts even after the system had correctly noticed the
omission.

Required repair direction:

- pass the exact missing obligation and its current-session grounding to the
  bounded retry
- reject retries that merely repeat a generic uncertainty or unrelated lesson
- do not treat acknowledgement of a request as fulfillment of that request

### 5. Figurative language and humor were recognized only superficially

Severity: medium

`Sardine can` did not produce the intended crowded-space interpretation. The
request for one small joke plus a return to the layout produced no actual joke
and repeated generic planning language, even though the closing turn later
handled the playful `committee adjourned` framing naturally.

Required repair direction:

- carry a supported figurative interpretation into answer content
- distinguish recognizing a humor request from actually satisfying it
- preserve the requested return topic after a brief aside

### 6. Self-state and ordinary uncertainty receive unnecessary evidence language

Severity: medium

The opening self-state response began appropriately with presence, attention,
and readiness, then appended that an attributed fact or approved concept was
needed. The unverified blue-mug scenario similarly received unrelated reasoning
and cooperation lessons instead of the simple distinction: the mug may be on the
porch, but neither participant currently knows.

Required repair direction:

- stop once a supported self-state answer is complete
- let ordinary uncertainty distinguish `possible`, `not checked`, and `not known`
  without invoking academic provenance language

## Stabilization Evidence Before Q&A

- full repository test suite: 1,276 passed
- frontend production build: passed
- Python package validation: passed
- Rust shell check: passed
- duplicate route keys, API paths, schema items, UI tabs, speech functions,
  tracked source files, and core memory layers: 0
- substantive Python modules unreachable from normal entry points: 1 intentional
  standalone hackathon showcase module
- frontend modules unreachable from the application entry point: 0
- generated/rebuildable output found by dry-run cleanup: about 2.8 GB, almost all
  Rust target artifacts; no cleanup was applied
- pending database review clutter: 24 old test/TODO records, 7 paper-map TODOs,
  and 9 superseded queue rows; recorded but not mutated

Full stabilization report:
`C:\Users\aleks\AppData\Local\Selene\data\exports\stabilization_run_20260801_183300.md`

## Recommended Next Repair Order

1. Tighten approved-knowledge eligibility and subject alignment.
2. Give verified math precedence for explicit arithmetic.
3. Restore prompt-grounded and current-session fact callbacks.
4. Connect coverage findings to one useful bounded completion.
5. Retest only these observed paths with a shorter gentle replay.

Further teaching should not be used to conceal these routing and completion
defects. The existing knowledge can be expanded after the answer pathway reliably
uses the right source for the right question.

## Bounded Repair Pass

Status: implemented and proportionally verified on August 1, 2026

The five repair steps taken from this diagnostic are now connected:

1. Approved knowledge needs strong subject alignment. Weak incidental words such
   as `inside`, `current`, or conversational `fair point` cannot redirect an
   ordinary request by themselves.
2. Verified math recognizes bounded number-word arithmetic and equal-part
   remainder questions. Arithmetic owns its exact result and arithmetic `why`;
   a genuinely separate conceptual obligation may still be coordinated beside it.
3. The Conversation Spine derives small answerable facts from visible user turns,
   applies later corrections, and uses them for callbacks, plan updates, and
   requested summaries. This fact braid is current-session state, not durable
   memory.
4. The one-pass completion layer can receive the exact missing obligation and
   matching current-session fact. It remains limited to one non-recursive pass and
   cannot invent facts or change memory, identity, personality, governance, or
   authority.
5. `sardine can` carries a supported crowded-space interpretation into visible
   speech; an explicit small-joke request is treated as a one-turn answer
   obligation; and ordinary possible-but-unchecked situations use natural
   uncertainty instead of academic evidence boilerplate.

Proportional evidence:

- 222 broader Chat, completion, spine, contextual speech, figurative, math,
  Answer Engine, and comprehension tests passed;
- a fresh eight-turn diagnostic replay covered number-word math, a corrected
  porch layout, exact fact callback, three-point summary, ordinary uncertainty,
  figurative interpretation, and one brief joke with a return to topic;
- the full repository run reached 1,283 passes with one unrelated Windows mobile
  HTTP connection-abort race; that exact mobile-limit test passed immediately on
  isolated rerun;
- `npm run build`, `npm run clean:check`, `python -m selene validate`, and
  `git diff --check` passed; line-ending notices remain the expected Windows
  LF/CRLF warnings.
- the core sidecar and NSIS installer rebuilt and passed package privacy,
  installed-startup, health, transfer-state, and boundary verification;
- the configured database was snapshotted before reinstall at
  `C:\Users\aleks\AppData\Local\Selene\data\db-inspection-snapshots\selene_inspection_20260801_153951.sqlite3`;
- silent reinstall completed successfully, and installed diagnostic sessions
  181 and 182 passed the repaired-path replay and final corrected-plan
  punctuation check with no retained-memory write or memory proposal.

No teaching approval, retained-memory write, identity/personality/governance
mutation, model training, provider call, autonomy expansion, or stressful live
probe was used by this repair pass.
