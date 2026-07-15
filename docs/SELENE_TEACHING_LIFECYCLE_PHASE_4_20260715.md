# Selene Teaching Lifecycle — Phase 4

Date: 2026-07-15

## Purpose

Phase 4 formalizes teaching as one source-bound, inspectable lifecycle:

`Acquire → Integrate → Express → Aleks approval`

It orchestrates the existing Comprehension and Integration Organ, intelligenceOS relationship boundary, NLO, and Voice. It does not create a second knowledge store or change identity, governance, personality, personal memory, training, or autonomy.

## Stage contracts

### Acquire

The review snapshot records concepts, vocabulary, relationships, examples, uncertainties, source provenance, and near-concept distinctions. Source provenance is mandatory. Missing required fields leave the stage in `needs_review`.

### Integrate

The review snapshot records approved-knowledge relationships, supporting and conflicting concepts, application scope, contradiction classification, unresolved questions, correction and reopening paths, and integration confidence. Supplied concept relationships must point to approved knowledge resources. A status-only intelligenceOS run reviews the bounded fit map and leaves a visible summary; it cannot retain or activate the concept. Integration confidence is explicitly separate from factual certainty and language fluency.

### Express

The review snapshot records an original-language explanation, distinct examples, analogies, questions, comparisons, and natural conversational participation. Every visible expression form is checked against source wording. The stage reuses the existing comprehension evaluation for reconstruction, transfer, limits, and source alignment.

NLO and Voice remain expression layers. Completing Express does not activate knowledge in Chat.

## Retention gate

Acquire, Integrate, and Express never retain knowledge. Retention requires:

1. all three stage snapshots to be complete;
2. sufficient source-linked comprehension evidence;
3. an explicit request containing `aleks_approved: true` and `approval_actor: "Aleks"`.

Only then does the lifecycle call the existing comprehension approval decision and make the reviewed knowledge resource available to supervised Chat. No personal memory is created.

## Revision behavior

Revising Acquire invalidates the prior Integrate and Express snapshots. Revising Integrate invalidates the prior Express snapshot. Stage history remains append-only and reviewable.

## Routes

- `teaching.lifecycle.status` — `GET /api/teaching-lifecycle/status`
- `teaching.lifecycle.list` — `GET /api/teaching-lifecycle/items`
- `teaching.lifecycle.detail` — `GET /api/teaching-lifecycle/detail`
- `teaching.lifecycle.acquire` — `POST /api/teaching-lifecycle/acquire`
- `teaching.lifecycle.integrate` — `POST /api/teaching-lifecycle/integrate`
- `teaching.lifecycle.express` — `POST /api/teaching-lifecycle/express`
- `teaching.lifecycle.approve` — `POST /api/teaching-lifecycle/approve`

## Cocoon

The Teaching tab shows the three stage states on every understanding candidate and provides bounded forms for each stage. Approval remains disabled until the complete lifecycle and comprehension evidence are present, followed by Aleks's confirmation.

## Verification boundary

Phase 4 is verified with synthetic lifecycle records, focused comprehension/router tests, and the frontend build. No live conversation or stress-shaped probe is needed for this infrastructure change.

Phase 5 language lesson expansion is intentionally outside this checkpoint.
