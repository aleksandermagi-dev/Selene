# Chat Auto-Follow and Dream Review Workflow

Date: 2026-09-20  
Scope: resident Chat viewport behavior, explicit bulk Dream review, and future-cycle reflection quality

## Outcome

Resident Chat now follows the newest turn after Aleks sends a message and after
Selene's reply enters the current session. If Aleks deliberately scrolls up to
read earlier turns, background updates do not pull the view away; a visible
`Latest` control returns to the newest message.

Dream now offers one explicit `Approve All Pending` action. The action:

- requires the actor to be exactly Aleks;
- requires a confirmation in the UI;
- approves only untouched `pending_review` reflections;
- records the entire selection atomically;
- is idempotent when no untouched pending reflections remain;
- approves provisional expression only;
- does not create Memory candidates or Study threads;
- does not include held, needs-context, routed, rejected, or superseded items.

No resident Dream reflection was approved or otherwise changed during this
implementation.

## Smarter future Dream harvests

Future cycles now preserve a stronger signal boundary:

- correction reflections require an active correction with both a corrected
  premise and an attributable replaced premise or prior turn;
- correction titles state the corrected premise instead of using a generic
  heading;
- open-thread titles retain the actual open question;
- cross-source comparison uses source-specific content rather than Dream's own
  template wording;
- records from the same primary source family cannot manufacture a
  cross-source recurrence;
- low-specificity process words cannot by themselves establish a pattern.

Existing reflections remain historical, source-linked review records and were
not silently rewritten, deleted, or reclassified.

## Verification

- `python -m pytest tests/test_dream_state.py -q`: 17 passed.
- `python -m pytest tests/test_associative_intuition.py tests/test_dream_state.py -q`: 33 passed.
- `python -m py_compile` passed for Dream, router, and sidecar modules.
- `npm run build` passed; main frontend bundle is 493.45 kB (gzip 109.82 kB)
  with no Vite size warning.
- `git diff --check` passed with only existing Windows line-ending notices.

Verification used temporary synthetic databases and static/frontend build
checks. There was no live conversation, resident-state write, Dream decision,
Memory write, Study route, teaching action, package, install, or external
action.

## Remaining UI observation

The Dream page still presents the full reflection history as one long list.
A later convenience pass could default to pending items and place reviewed or
terminal items behind a state filter or collapsed history section. That is a
presentation improvement, not a lifecycle or safety blocker.
