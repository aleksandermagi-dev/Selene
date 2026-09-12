# Selene Conversation Cultivation Phase 7 — Semantic Coverage and Arbitration

Date: 2026-09-12  
Status: implemented and proportionally verified

## Question

Can final speech arbitration prefer the candidate that actually answers the
whole current request, while rejecting a fluent current-owner candidate that
changes the subject, loses requested entities, or merely claims completion?

## Root finding

The architecture already had the right owners: Conversation Spine declared
the current obligations, Answer Operations produced typed results, Semantic
Fulfillment could inspect visible performance, and Response Coverage could
measure the whole answer. Visible Speech arbitration was not yet using the
last two receipts as part of candidate ranking.

That gap produced three connected failure paths:

1. a current-session candidate could receive priority from a completed status
   and obligation id without visibly performing the operation;
2. candidates were ranked by claimed ids and source priority rather than the
   number of current required obligations actually addressed and resolved;
3. Session Decision could turn two bare option labels into tautological
   comparison prose, then suppress a richer comparison owner.

The bounded stabilization cases also exposed two smaller semantic seams. The
coverage normalizer did not recognize `reversibility` and `reversible` (or
`reliability` and `reliable`) as the same meaning, and a structured three-part
recap could receive a redundant fourth generic summary obligation.

## Source repair

Visible Speech now evaluates every candidate through the existing Response
Coverage owner before ranking it. Whole-request completion, visibly addressed
obligation count, and visibly resolved obligation count participate in
arbitration ahead of claimed obligation ids.

The current-owner gate now also asks Semantic Fulfillment whether each
completed typed operation is present in that candidate's visible text. A
completed status, owner name, and current-turn receipt remain necessary, but
they are no longer sufficient. Failed visible fulfillment is recorded as
`typed_owner_result_not_visibly_fulfilled`.

Typed expression delegation remains modular: an expression surface may carry
the responsible owner's result when the exact result source is the candidate
source and the result owner still matches the canonical obligation owner. It
does not transfer truth or decision authority to NLO or Voice.

Session Decision continues to preserve bare option labels for reference and
continuity, but no longer emits comparison findings unless every compared
option has at least one visible distinction beyond its own name. This leaves
the richer domain or exploratory owner free to answer.

Semantic Fulfillment now normalizes the paired forms
`reversibility/reversible` and `reliability/reliable`. Pragmatic Planning no
longer adds a generic session-summary obligation when explicit named summary
sections already represent that same language act.

## Evidence

Focused tests prove that:

- bare labels remain available for reference but cannot become comparison
  findings;
- a completed typed owner result without visible operation meaning is held;
- a valid current-owner result with visible fields still receives priority;
- partial current-owner completion cannot take whole-turn priority;
- whole-request response coverage participates in candidate arbitration;
- grammatical noun/adjective forms preserve the intended comparison meaning;
- named recap sections are not counted twice;
- Answer Engine content wins over a partial current-session candidate;
- Venn content retains shared and distinct properties;
- older-thread return retains the requested landmark meaning;
- bare-why specificity and multi-operation composition remain intact; and
- the long multi-turn festival flow reaches its structured recap without a
  false unresolved obligation.

The bounded Session Decision, Semantic Fulfillment, Visible Speech, Pragmatic
Planner, and exact Chat-path matrix passed 85 checks. Python compilation
passed. `git diff --check` reported only expected Windows line-ending notices.

The broader Chat suite, repository-wide suite, resident-state pass, frontend
build, package, installation, and live Q&A were deliberately deferred to the
Phase 11 stabilization gate under the proportional-testing agreement. No
resident database or external state was touched.

Of the six previously recorded stabilization cases, the five belonging to
semantic coverage and arbitration now pass in the bounded reproductions. The
remaining current-session correction phrase (`corrected meaning`) is a shared
realization/scaffolding defect and remains explicitly assigned to Phase 8.

## Boundaries

This phase changes selection evidence, not Selene's facts, values, identity,
personality, Vys, governance, permissions, Memory, Study, Dream, teaching, or
external authority. It does not require parroting exact wording: visible
semantic equivalence is sufficient. Unknown or unsupported content remains a
valid hold, and a fluent sentence is not treated as proof that an operation
was performed.

No live Q&A, teaching, resident write, package, installation, or external
action ran.

## Next

Conversation Cultivation Phase 8 is shared realization cleanup: remove
internal correction/recovery scaffolding from released speech, preserve
punctuation and symbols, repair malformed subjects, and prevent stale fallback
contamination without changing supported meaning.
