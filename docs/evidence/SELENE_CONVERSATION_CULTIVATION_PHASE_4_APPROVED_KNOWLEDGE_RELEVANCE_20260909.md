# Selene Conversation Cultivation Phase 4 — Approved-Knowledge Relevance

Date: 2026-09-09  
Status: implemented and proportionally verified

## Question

Does approval alone let a reviewed teaching item enter an ordinary Chat
answer, or must the item also fit the subject, current entity, requested
operation, and response function of the present turn?

## Root finding

Approval and relevance had become conflated at two different gates. The
shared semantic gate checked broad topic overlap, then Comprehension applied a
second local word-count filter. Both could admit a nearby lesson because it
shared general words with the request.

On a read-only resident-state reproduction, this question:

> Both trial groups improved equally. What does that suggest about the treatment?

selected the elementary lesson `Equal groups connect repeated addition to
multiplication`. The overlap was lexical, not conceptual. Approval correctly
meant that the lesson was available for use; it did not prove that the lesson
answered this question.

The same root could displace a current entity, let a lesson describe an
operation it did not perform, or select a neighboring concept for a precise
definition.

## Source repair

`semantic_relevance.py` now owns one inspectable approved-knowledge alignment
receipt. It records:

- the required obligation and requested subject;
- direct-subject or bounded distinct-application alignment;
- preservation of typed current entities;
- whether the requested operation belongs to the knowledge candidate;
- whether the candidate performs the requested response function; and
- the explicit invariant that approval cannot substitute for relevance.

`comprehension_integration.py` no longer performs an independent word-count
relevance judgment. It consumes the shared receipt after the existing
Conversation Spine compatibility gate and exposes the receipt on eligible
items. Existing compatibility fields remain available as projections of that
single decision.

During full Chat verification, the first implementation held a relevant
approved Memory item when the user asked which telescope setup was the better
fit. Cultivation traced this to a shared `choice` ownership classification.
The boundary is now typed correctly: relevant Memory may inform a choice, but
approved teaching cannot impersonate the choice-maker merely because it is
approved. The exact Memory regression then passed.

## Transfer evidence

Synthetic changed-entity and neighboring-concept checks prove that:

- equal-group multiplication does not answer an experimental-treatment
  comparison;
- a seedling/fertilizer request cannot be displaced by a nearby lesson;
- a turbine/controller request cannot be displaced by a nearby lesson;
- an exact unit-fraction definition outranks a lesson about dividing with unit
  fractions;
- a current requested action remains with its responsible owner even when a
  lesson shares the word `place`; and
- the approved sound mechanism remains available for the distinct application
  “How does a bell produce sound?”

Read-only resident controls also retained the exact Earth-rotation explanation
for day and night and the exact unit-fraction definition.

## Verification

- 37 semantic-relevance and comprehension checks passed after the Memory
  boundary repair.
- 122 supporting semantic, comprehension, Answer Completion, Answer Engine,
  Conversation Spine, and Visible Speech checks passed.
- The full Chat shell returned to 124 passing checks with exactly the same
  seven previously recorded stabilization failures. The temporary Memory
  regression was removed; Phase 4 introduced no remaining Chat regression.
- Resident SQLite integrity was `ok`.
- Resident counts remained 295 comprehension concepts, 249 teaching
  lifecycles, 23 Chat sessions, 360 Chat messages, zero Memory candidates, 24
  Dream reflections, one Study session, and 248 approved knowledge resources.
- Resident SQLite remained byte-for-byte unchanged at SHA-256
  `4391C45B2BEBD79C09C6A66378B266C2DC64D989708786EB7667FCE8F1C0BF6A`.
- `git diff --check` reported only existing Windows line-ending notices.

## Boundaries

This phase changes ephemeral answer eligibility only. It does not write
Memory, approve or retain knowledge, mutate identity, personality, Vys, or
governance, train a model, expand authority, act externally, or alter
perception or embodiment. No live Q&A, teaching, package, or installation ran.

## Remaining stabilization debt

Seven pre-existing Chat failures remain a separate bounded batch: mixed-turn
repair source ownership, a long-request Answer Engine precedence case, bare
why specificity, synthetic multi-operation coverage, one Venn comparison,
one older-thread return, and correction acknowledgement wording.

## Next

Conversation Cultivation Phase 5 is correction/revision completion: when a
correction changes current-session state, recompute the still-open answer from
the updated active state rather than merely acknowledging the correction or
replaying the prior answer.
