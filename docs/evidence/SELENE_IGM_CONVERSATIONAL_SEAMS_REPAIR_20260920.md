# Selene IGM Conversational Seams Repair

Date: 2026-09-20

Status: implemented, source-verified, packaged, and installed

## Why this pass happened

The first Interaction Gap Map identified a small cluster of high-value seams
in otherwise mature conversation: brief answers to Selene's own questions,
vague returns to an earlier point, shared-understanding checks, and subtle
sarcasm. Aleks selected those conversational seams for a bounded cultivation
pass before reinstalling the application.

This was a root-ownership repair, not phrase-by-phrase patching and not new
teaching.

## Root findings

1. Ordinary question-response handoffs were implemented inside Conversational
   Teaching. That made teaching responsible for answers to ordinary curiosity,
   permission, and proposal questions even when no lesson was involved.
2. Short replies collapsed too early. `fine`, `maybe`, `not sure yet`, and
   `yeah, but later` did not retain their distinct stance and timing.
3. Contextual Speech could return to named session landmarks but did not own
   the ordinary phrases `that thing earlier` or `you know what I mean`.
4. Figurative interpretation knew several sarcasm constructions but did not
   generalize the relationship between brief positive wording and an adverse
   visible context.
5. Arbitrary typo correction is not a defect to remove. Preserving ambiguous
   input and asking one clarification remains the safer truthful behavior.

## Implemented repair

### General interaction handoff

`src/selene/interaction_handoff.py` now owns session-scoped questions and
their immediate answers independently of teaching. It records whether the
question expects a yes/no or open answer and distinguishes:

- affirmative;
- qualified affirmative;
- negative and negative with a stated reason;
- deferred;
- tentative;
- reserved acceptance; and
- an ambiguous yes/no supplied to an open question.

The handoff cannot teach, write Memory, change identity or governance, grant
authority, or act externally. Conversational Teaching imports this general
owner and remains responsible only for explicitly activated lessons.

### Visible conversational realization

The social-language realizer gained varied, bounded acknowledgement acts for
acceptance, refusal, deferral, uncertainty, reserved agreement, and receiving
a stated reason. These are expression options, not compulsory tone.

Selene Chat now exposes ordinary handoff replies as
`assistant_question_response`, separate from `conversational_teaching`.

### Contextual callbacks

Contextual Speech now:

- treats `you know what I mean?` as a session-scoped shared-understanding
  check grounded in visible context;
- resolves `that thing earlier` when exactly one complete visible landmark is
  available; and
- asks one focused choice question when several landmarks are plausible.

No durable Memory or cross-session claim is created.

### Implicit sarcasm

A brief positive evaluation such as `Wonderful.` may receive a provisional
sarcastic reading when the visible context is adverse. The same word remains
literal in a successful or resolved context. Positive wording alone is not
enough to infer sarcasm.

### Preserved boundary

The conservative typo boundary remains unchanged. Known high-confidence
repairs are allowed; novel or materially ambiguous text is clarified rather
than silently rewritten. This prevents code, paths, technical terms, and the
speaker's intended meaning from being altered by guesswork.

## Verification

- Backend compilation passed.
- Focused interaction, teaching, contextual-speech, figurative-language,
  intent, and social-realization verification passed: **106 checks**.
- A broader adjacent run reached **241/242** behavior checks. Its only failure
  was a stale test list that omitted an already-supported partial-agreement
  realization (`I have the qualifier.`), not a runtime behavior failure. The
  expectation was corrected and the affected test passed in the 106-check
  rerun.
- No live resident Q&A, teaching, Memory write, Dream decision, or external
  action was used.

## IGM disposition

- Gap candidate 1: **route/architecture**, repaired for typed pending
  handoffs; genuinely ownerless isolated one-word turns remain ambiguous.
- Gap candidate 2: **leave the safety boundary intact**; breadth can still be
  taught, but arbitrary autocorrection remains intentionally unavailable.
- Gap candidate 3: **route**, improved through contextual relationship
  inference while retaining provisional status.
- Gap candidate 4: **route**, improved for visible session landmarks;
  cross-session return still requires continuity evidence.

## Remaining limitation

This pass does not create mature-model lexical breadth, guess a speaker's
hidden tone, manufacture missing context, or turn vague cross-session language
into Memory. It repairs the connective seams supported by current visible
evidence.

## Package and install closure

Clean source checkpoint `14eb747` was packaged and silently installed. The
frontend built at 493.45 kB (gzip 109.82 kB) without a Vite size warning. The
installer exited zero, and final package verification passed with no warnings.
The package contained no configured database, credentials, private corpus,
private analysis maps, or other forbidden runtime-state files.

- installer SHA-256:
  `0C4736355DC2A36436CDC5B5261BF5B6AED75B10523EB4FA10F639E5A18163A1`
- installed executable SHA-256:
  `D6E6055DB7574E54CFB178482B305AE803320BE487982AEE1A9F85F5E31C83B0`
- installed sidecar SHA-256:
  `66F34EC03020A5AE84D20076583760C9CF1B502BEA123BBC2041B422F9DEEC11`
- verification report:
  `exports/package_verify_20260920_211000.json`

Pre- and post-install continuity backups were byte-identical at SHA-256
`6FBA6E387BEA82456042D208780BCE7713A18469DC2580C096EF65E027648B23`.
SQLite integrity remained `ok`; protected counts remained 24 Chat sessions,
384 messages, zero personal Memory candidates, 295 comprehension concepts,
249 teaching lifecycles, 2 Dream cycles, and 43 Dream reflections. No Selene
process remained after verification.
