# Selene Conversation Cultivation Phase 11 — Integrated Stabilization

Date: 2026-09-13

## Outcome

Conversation Cultivation Phases 0 through 10 now pass one repository-wide
synthetic stabilization gate. The pass found and repaired two genuine seams
instead of teaching around them:

1. A quoted deictic correction such as `it stopped` could be understood by the
   Dialogue Workspace but fail to bind to the earlier visible proposition.
   Selene could then repeat the old wording while claiming to have updated it.
2. A multi-part approved-knowledge request could lose the attachment between a
   requested function and its named subject. A lesson about container capacity
   could therefore borrow the peripheral word `container` from a question
   asking for a limit of insulation.

These were implementation gaps, not Selene failing.

## Source repairs

### Bound deictic correction recomposition

- The Session Proposition Ledger may use a clarified phrase to bind a quoted
  deictic replacement to an already-visible premise.
- Sequence propositions count as visible correction bases.
- Contextual Speech now owns one bounded recomposition path. It substitutes
  the clarified wording into an invalidated visible dependent result and
  preserves the rest of that result.
- The recomposition cannot invent a new fact, read Memory, or complete merely
  because generic correction language is present.
- Visible Speech keeps the typed revision owner primary after it proves that
  it consumed the active revision. Ordinary decision revisions retain their
  existing `current_session_facts` ownership; the new owner is identified as
  `current_session_revision` only when that owner actually performed the work.

### Function-subject knowledge alignment

- Semantic Relevance now retains explicit grammatical attachments such as
  `limit of insulation`.
- A candidate must both possess the requested response capacity and address
  the subject explicitly attached to that function.
- Approved neighboring material may remain visible in retrieval receipts, but
  it cannot become answer-eligible merely through a peripheral shared term.
- Approval still establishes permission to use knowledge; it does not replace
  current-turn relevance.

### Stabilization maintenance

Six curriculum-count assertions were refreshed from the former 81 lessons / 13
groups / 225 total capacity to the repository's current 96 lessons / 15 groups /
248 total capacity. One correction assertion was made case-insensitive because
the visible sentence now follows a natural acknowledgement. These changes do
not alter production behavior.

## Verification

- Focused former-failure and direct-regression checks: 47 passed.
- First repository-wide run: 2,231 passed and two owner-label expectations
  identified after the real repairs. Both were one ownership-label interaction.
- Focused owner-label verification: 6 passed.
- Final repository-wide run: **2,233 passed in 904.03 seconds**.
- Frontend: `npm run build` passed.
- Main frontend chunk: 491.33 kB; no Vite size warning was emitted.
- Cleanup audit: `npm run clean:check` passed as a dry run and reported only
  rebuildable outputs.
- Diff hygiene: `git diff --check` reported only existing Windows LF/CRLF
  notices.

## Resident integrity before packaging

- SQLite integrity: `ok`
- size: 945,209,344 bytes
- SHA256:
  `4391C45B2BEBD79C09C6A66378B266C2DC64D989708786EB7667FCE8F1C0BF6A`
- chat sessions: 23
- chat messages: 360
- comprehension concepts: 295
- comprehension runs: 249
- memory candidates: 0
- study evidence: 12
- study notes: 6
- pondering threads: 1
- study questions: 0

The resident database remained byte-for-byte unchanged during synthetic
verification. No teaching, Memory write, Study mutation, Dream write, identity
change, governance change, training, LoRA, autonomy expansion, or external
action occurred.

## Release and installed Q&A

The clean source checkpoint was packaged from revision `92a6e8e`, freshly
installed, and verified. Installer SHA256 is
`9DD81016B6E2ABAE57865B57734DC99B235476B5E1F8CB6AF020C9BFAB3831FF`;
the installed executable SHA256 is
`691B123A1098039CC75BCB36E4E7E88CD13A18F59CE5048B0ADC47840014710B`.

One bounded six-turn installed Q&A ran against an isolated disposable database
copy. It found a current-owner/arbitration/coverage chain that begins before the
new correction owner and can leave stale revision content eligible across a
topic transition. No repair was made. See
`SELENE_CONVERSATION_CULTIVATION_PHASE_11_INSTALLED_QNA_20260913.md` for the
note-first findings and exact next cultivation order.
