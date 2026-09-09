# Selene Conversation Cultivation Phase 5 — Revision Completion

Date: 2026-09-09  
Status: implemented and proportionally verified

## Question

When a visible correction changes current-session state, can Selene bind the
changed premise to the right proposition and accept a recomputed answer only
from an owner that demonstrably used that exact revision?

## Root finding

The existing architecture already preserved correction ancestry, selectively
invalidated dependent propositions, and could recompute a current-session
decision. Two missing handoffs prevented that machinery from proving the full
lifecycle:

- common correction shapes such as `X, not Y` and quoted referent replacement
  did not always produce separate corrected and replaced meanings; and
- Chat could treat a generic statement such as “the latest condition changed”
  as recomputation even when the owner had not consumed the actual changed
  premise.

Three historical correction fixtures also returned scenario-specific prose.
They preserved useful old behavior but could not serve as evidence of a
general correction capability.

## Source repair

Dialogue Workspace now extracts explicit replacement pairs from:

- `X, not Y` correction clauses;
- `X instead of Y`; and
- quoted forms such as `by 'Y' I meant X`.

When a replacement pair is available, the Session Proposition Ledger prefers
the visible premise, observation, source statement, claim, relation,
condition, constraint, or correction over an equally similar downstream
result. The corrected premise supersedes only its matched basis and
invalidates its dependents; unrelated active context remains available.

The ledger now exposes a bounded revision-completion coordinator. A general
owner result is accepted only when it:

- is explicitly typed as an owner result;
- is the responsible owner and has accounted for the current-turn inputs;
- supports correction;
- names the active revision exactly;
- is not a legacy fixture; and
- visibly consumes significant content from the revised premise.

The coordinator generates no answer. It permits one owner recomputation pass
and records that replaying the previous answer is not recomputation.

Chat carries this receipt through Answer Operations and Dialogue Workspace.
The ledger reaches `completed` only after the accepted owner result is visibly
realized with complete current-turn coverage.

## Compatibility boundary

The three earlier warm/cool drink, screen-flicker, and drawer/shelf correction
fixtures remain available because their general replacements are not all
proved yet. They are now explicitly labeled compatibility-only:

- they cannot outrank an accepted general owner result;
- `general_capability_evidence_eligible` is false; and
- exact replay remains insufficient evidence of transfer.

This preserves working behavior without mistaking it for completion of the
general mechanism.

## Transfer evidence

A changed-noun two-turn example used a swift/delicate route and a
steady/robust route. After the deadline moved closer while robustness remained
the governing priority:

- the typed current-session owner consumed the changed deadline premise;
- the coordinator matched the exact revision id;
- the prior dependent result was invalidated;
- the recommendation was recomputed once from the updated state;
- the visible answer retained the revised premise and current priority; and
- the final ledger recorded general-capability-eligible completion.

Negative controls rejected:

- a prior-answer replay carrying a different revision id;
- a scenario-specific legacy fixture as general evidence; and
- a same-revision generic change notice that did not consume the corrected
  premise.

An equal-groups/fertilizer ledger control also proved premise-first targeting:
the premise was superseded and its downstream conclusion invalidated rather
than rewriting the conclusion as though it were the corrected observation.

## Verification

- Python compilation passed for all four changed production modules.
- 22 direct and selected end-to-end revision checks passed.
- 117 affected Answer Operations, Epistemic Revision, Dialogue Workspace,
  Conversation Spine, Session Proposition Ledger, and Session Decision checks
  passed.
- Full Chat passed 126 checks with six previously recorded later-phase gaps:
  mixed-turn recovery-source ownership, long-request Answer Engine precedence,
  bare-why specificity, synthetic multi-operation coverage, Venn semantics,
  and older-thread return.
- The former correction-revision failure is no longer in the remaining set.
- Resident SQLite integrity was `ok`.
- Resident counts remained 295 comprehension concepts, 249 teaching
  lifecycles, 23 Chat sessions, 360 Chat messages, zero Memory candidates, 24
  Dream reflections, one Study session, and 248 approved knowledge resources.
- Resident SQLite remained byte-for-byte unchanged at SHA-256
  `4391C45B2BEBD79C09C6A66378B266C2DC64D989708786EB7667FCE8F1C0BF6A`.
- `git diff --check` reported only expected Windows line-ending notices.

## Boundaries

This phase changes visible current-session correction coordination only. It
does not write Memory, approve or retain knowledge, mutate identity,
personality, Vys, or governance, train a model, expand authority, act
externally, or alter perception or embodiment. No live Q&A, teaching, package,
or installation ran.

## Next

Conversation Cultivation Phase 6 is typed participation ownership for humor,
acknowledgement, recap, and closure. These ordinary conversational acts should
be proved by their existing responsible owners rather than relying on the
remaining broad prompt-grounded compatibility guard.
