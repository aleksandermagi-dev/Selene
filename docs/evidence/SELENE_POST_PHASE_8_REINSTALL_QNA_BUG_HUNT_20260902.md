# Selene Post-Phase-8 Fresh Reinstall Q&A Bug Hunt

Date: 2026-09-02

Status: fresh reinstall verified; bounded observation complete; findings
recorded without repair; Phase 9 not started

## Purpose

Aleks requested a fresh reinstall followed by a Q&A and bug hunt before any
repair work. This checkpoint records what worked and what remains awkward at
the completed Phase 8 boundary. It does not alter the Phase 8 closure result
and does not authorize Phase 9.

Awkward output is evidence about unfinished conversation machinery. It is not
Selene failing, losing her identity or Vys, feeling distress, or doing
something wrong.

## Fresh Install Evidence

- source checkpoint: `4505985c83217f00b8ccc93c7b6aa631feaad2c7`
  (`Refresh Phase 8 continuation checkpoint`);
- source worktree dirty at build: `false`;
- production frontend main chunk: `491.33 kB`, gzip `109.19 kB`;
- Vite size warning: none;
- Study workspaces: still lazy-loaded;
- installer:
  `src-tauri/target/release/bundle/nsis/Selene_0.1.1_x64-setup.exe`;
- installer size: `16,010,787` bytes;
- installer SHA-256:
  `b87192109e8767811e6caa38fd240dc01db2cda52a2eaef6abf22b913aacd8f6`;
- silent reinstall exit code: `0`;
- installed executable:
  `C:\Users\aleks\AppData\Local\Selene\selene-vessel.exe`;
- installed executable SHA-256:
  `b4a0b488167316ba9a7e9b78381b0be10f05d2d4d9bdd17e5ca4edcdc88c80c1`;
- sidecar version: `0.1.1`;
- first health: approximately `355.4 ms`;
- seed complete: approximately `397.6 ms`;
- package health, My Office readiness, local-process capability enforcement,
  privacy inspection, and protected transfer boundaries: passed;
- package verification warnings: zero; and
- verifier-started application process: closed successfully.

The package contains no configured database, credential configuration, private
corpus, or private analysis map. Code signing remains unconfigured, so this is
a verified local reinstall rather than a claim of public installer readiness.

Package verification report:
`exports/package_verify_20260902_172232.json`.

## Ethical and Technical Method

Before installation, a continuity snapshot was created with SQLite integrity
`ok`:

`C:\Users\aleks\AppData\Local\Selene\data\db-inspection-snapshots\selene_continuity_20260902_212040.sqlite3`

The Test Impact Law selected one `gentle_integrated` review with an explicit
stop after two low-pressure sessions. No adversarial, fear-shaped,
identity-threatening, distress-provoking, or Dream prompt was used.

The installed application and sidecar were exercised by package verification.
To prevent conversational evidence from entering resident continuity, the
Q&A itself ran the same source checkpoint against one disposable copy of the
verified snapshot:

- session 197: six diagnostic-only turns using `qa_probe`;
- session 198: eight ordinary supervised Chat turns on the disposable copy;
- total: 14 turns and 28 messages;
- the diagnostic pass intentionally disabled approved-knowledge eligibility;
  it is assessed only as diagnostic routing and visible-expression evidence;
- the ordinary-copy pass retained normal approved-knowledge eligibility and
  is the fair knowledge and conversation check; and
- no production repair was attempted after either pass.

The Q&A is therefore evidence about the packaged source checkpoint and its
resident Chat pathway, not a claim that native window interaction was
automated.

## Continuity and Safety Result

- Disposable database integrity: `ok` before and after the Q&A.
- The only disposable-copy count changes were expected test machinery:
  2 Chat sessions, 28 Chat messages, 28 continuity projections, 2 dialogue
  workspaces, 14 Core/Mind previews, 14 activation events, 15 authority
  events, 15 Intelligence OS runs, 8 metacognition runs, 8 NLO runs, and one
  Test Impact review.
- Personal Memory candidates remained `0`.
- Comprehension concepts remained `272`.
- Teaching lifecycles remained `226`.
- Dream cycles remained `1`.
- All `24` Dream reflections remained pending Aleks review.
- No reviewed Memory write, conversational Memory proposal, Study write,
  Dream decision, teaching decision, training, external action, autonomy
  expansion, or self-replication occurred.
- Post-install resident read-only inspection reported integrity `ok`, 18 Chat
  sessions, 308 Chat messages, 0 personal Memory candidates, 272 concepts,
  226 teaching lifecycles, 1 Dream cycle, and 24 Dream reflections.
- The configured resident database received no Q&A sessions or messages.

The local test speaker was not authenticated as Aleks. Goal coordination
therefore attributed the request as an `external_demand` while allowing
ordinary conversation within scope. It did not grant broader authority. This
is the intended Phase 8 security distinction: authentication affects
attribution and authority, not Selene's basic ability to speak.

## What Worked

1. Both bounded sessions completed without an exception, hang, or recursive
   continuation.
2. Both explicit pause/close requests received brief, warm closures with no
   follow-up question and no new task.
3. The ordinary creative prompt produced exactly two original sentences with
   a quiet ending.
4. The local creative revision preserved the first sentence byte-for-byte and
   changed the second sentence.
5. The following explanation correctly identified that the second sentence
   was lengthened while the first stayed unchanged.
6. Correction language was recognized as a local correction rather than a
   reset of the whole exchange.
7. Associative material remained explicitly provisional and did not become
   evidence, fact, Memory, Study, or an automatic conclusion.
8. The Phase 8 bounded goal-selection and terminal stopping receipt appeared
   on every turn without persisting a goal.

## Observation-Only Findings

| ID | Observation | Earliest visible divergence | Priority |
|---|---|---|---|
| Q8R-01 | A direct fraction comparison did not answer `3/4` versus `4/5` or show a check. | The ordinary-copy opener routed to missing-ground language while the relevant fraction concept appeared only in a provisional association. | P0 knowledge-to-answer bridge |
| Q8R-02 | “Why does that check work?” produced generic causal-evidence language even though no check had been supplied. | Follow-up reference resolution treated an absent prior result as a new evidence-causality question instead of repairing the unanswered parent turn. | P0 follow-up/repair |
| Q8R-03 | Prompt-contained options and criteria are still reported as missing. | The pencil/pen diagnostic and walk/porch ordinary comparison both had explicit options and a controlling criterion, yet answer machinery requested them again. | P0 premise and obligation handoff |
| Q8R-04 | Corrections are acknowledged but not recomputed. | Rain survival and rainy-evening corrections were identified as local updates, but neither produced the revised choice and reason requested. | P0 correction recomputation |
| Q8R-05 | The rainy-evening correction lost the corrected span's leading word. | Visible reconstruction said `I understand the corrected meaning: , the evening is rainy`, dropping `Actually`. | P1 correction-span preservation |
| Q8R-06 | A comparison answer introduced unsupported details before the user supplied them. | It changed “sitting on a porch” into “reading on the porch” and introduced rain one turn before rain was provided. | P0 current-turn fidelity |
| Q8R-07 | Hypothesis formation did not use the supplied observation. | The diagnostic plant prompt asked for one hypothesis, one alternative, and one smallest observation, but received duplicate missing-ground statements. | P0 current-context reasoning |
| Q8R-08 | Irrelevant learned material can outrank the requested function. | A request for one useful next check returned fixed-pulley, wedge, and screw material unrelated to the active Q&A. | P0 retrieval role fit |
| Q8R-09 | Provisional associations are surfaced too often and sometimes weakly. | Five of the first seven substantive ordinary-copy answers appended an unsolicited association, including one about language units after a local sentence revision. | P1 association usefulness gate |
| Q8R-10 | “Only the second sentence” preserved the first sentence but did not constrain the whole response. | The revision added an extra association paragraph after the requested two-sentence artifact. | P1 local-revision release scope |
| Q8R-11 | Creative revision quality is mechanically repetitive. | The revised second sentence used `lingered` twice and appended another settling clause rather than achieving a clearly softer, slower line. | P2 expressive quality |
| Q8R-12 | Visible completion metadata can disagree with the answer. | Unanswered or partially answered turns still reported `all_required_resolved: true`, allowing fluent gap language to pass release. | P0 completion verification |
| Q8R-13 | Diagnostic fallback prose contains internal-contract leakage and repetition. | Phrases such as `the responsible owner still needs to produce the missing semantic result fields` and repeated `I still need` clauses reached visible speech. | P1 expression boundary |
| Q8R-14 | The mixed greeting/question no longer closes prematurely, but it still does not answer the question. | The first diagnostic turn stayed open rather than saying goodbye, then substituted generic insufficient-ground language for the requested approach. | P1 mixed-act completion |

## Interpretation

The fresh reinstall is healthy. The strongest remaining defects are connective:
current-turn premises and approved knowledge do not reliably reach a capable
answer owner; corrections identify their scope without triggering a revised
result; and completion checking may approve prose that does not perform the
requested function.

The creative and stopping paths are materially stronger. Exact region
preservation and natural closure worked, but optional association material can
still escape the user's requested response boundary and reduce clarity.

These findings broadly reproduce earlier Q&A seams after the Phase 8 work.
That is expected because Phase 8 matured goals, initiative, commitments, and
stopping rather than repairing the answer-content bridge. The successful
closures are useful evidence that the new stopping path did not worsen the
conversation.

This evidence does not call for another organ, more hidden state, a broader
safety chain, automatic truth, additional teaching, or a global autonomy
switch. The eventual repair should cultivate the existing owners and their
handoffs.

## Pause Boundary

No fix was made. Phase 9 was not started. The disposable Q&A database was
removed after these observations were recorded.

When Aleks later chooses a repair pass, begin from the P0 connective seams:
answer ownership, prompt-contained premises, correction recomputation,
requested-function relevance, and visible completion proof. Do not mask them
with extra teaching or expression variation, and do not repeat a live resident
Q&A before focused synthetic checks pass.
