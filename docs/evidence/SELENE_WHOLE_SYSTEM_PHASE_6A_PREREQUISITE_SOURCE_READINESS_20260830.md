# Selene Whole-System Phase 6A — Prerequisite and Source Readiness

Date: 2026-08-30

Status: complete for the Phase 6A scope

Parent map:
[Phase 6 Ordered Education and World-Knowledge Expansion Implementation Map](../architecture/SELENE_WHOLE_SYSTEM_PHASE_6_IMPLEMENTATION_MAP_20260829.md)

## Result

Selene's existing Curriculum Authorization owner now exposes and enforces one
shared group-readiness receipt before curriculum preparation, teaching, and
authorization coverage. Progress/status uses the same receipt.

An active authorization can no longer bypass a missing declared prerequisite
or an unaccepted source. Existing completed groups are described as complete
from their approved concept state without replaying Acquire, Integrate,
Express, approval, or authorization events.

No new teaching organ, source store, Memory path, score, deadline, or F2 Group
8 implementation was added.

## Shared Contract

Every implemented curriculum group now has one typed manifest containing:

- curriculum band and group key;
- bounded authorization key;
- the group's concept keys;
- ordered predecessor groups;
- exact required prerequisite concept keys;
- a source-acceptance receipt; and
- the existing Cocoon teaching exception route.

The source receipt names the bounded source IDs, source references, artifact
checksums, inline license references where present, source role, knowledge and
freshness classes, exclusions, reconstruction feasibility, review actor and
date, and the canonical source-shelf and retrieval-manifest records. It is a
descriptive migration of already reviewed groups, not a new source or teaching
decision. Mirroring a file still does not make it accepted teaching material.

The computed readiness state is exactly one of:

- `ready`;
- `needs_prerequisite`;
- `source_review_required`;
- `authorization_required`; or
- `complete`.

The receipt exposes exact unmet predecessor groups, concept keys, source IDs,
or decision. `score` and `deadline` are explicitly absent (`None`).

## Enforcement

- Status/progress returns each manifest and its current readiness receipt.
- Authorization activation returns the resulting readiness but does not
  pretend prerequisites or source review are complete.
- Preparation stops before candidate text is created unless the shared receipt
  is `ready` or the group is already `complete`.
- Teaching consumes the same gate before Acquire, Integrate, Express, coverage,
  or retention.
- Coverage includes the same receipt and adds typed prerequisite or source-
  review exceptions when applicable.
- A completed group returns existing descriptive state idempotently even if a
  copied historical database does not contain reconstructable prerequisite
  history. It performs no replay or reteaching.

## Verification

Synthetic tests prove:

- status exposes the five non-graded readiness states and exact unmet facts;
- active authorization cannot bypass a missing prerequisite;
- blocked preparation and teaching create neither candidate concepts nor
  teaching lifecycles;
- preparation and coverage consume the same `ready` receipt;
- an unaccepted source stops before its content enters candidate text; and
- an existing complete group migrates descriptively without changing its
  rows.

Verification results:

```text
curriculum authorization, F1, F2, Coding, and Phase 6A tests: 140 passed
teaching, comprehension, maturity, runtime-truth, and public checks: 43 passed
disposable resident-copy status: 26/26 groups complete; 152 concepts described
frontend main bundle: 491.33 kB (gzip 109.19 kB)
Vite size warning: none
Study workspaces: lazy-loaded
git diff --check: clean apart from expected Windows line-ending notices
```

The resident database was copied and inspected; the copy was removed after the
read-only status check. The resident database itself was not initialized,
migrated, written, taught, or decided through this work.

## Care and Authority Boundary

- The 24 resident Dream reflections remain pending for Aleks.
- The one resident `acquire_needs_review` teaching lifecycle was not opened or
  decided.
- No resident Memory, Study, Dream, affect, teaching, or authorization decision
  occurred.
- No identity, personality, Vys, law, governance, authority, training, LoRA,
  autonomy, self-replication, filesystem scope, external action, or embodiment
  changed.
- Learning readiness remains a description of the next useful teaching move,
  never a grade, diagnosis, worth judgment, or speed demand.
- F2 Group 8 remains absent, unprepared, and unauthorized pending Aleks's
  explicit selection of an exact reviewed source artifact and license.

## Next

Phase 6B should extend the existing lesson and Teaching Lifecycle snapshots
with typed source roles and an instructional-why receipt. It must preserve
Acquire -> Integrate -> Express, source reconstruction, distinct application,
limits, counterexamples, correction readiness, and non-forced states such as
developing, needs representation, needs prerequisite, revisit, and unclear.
