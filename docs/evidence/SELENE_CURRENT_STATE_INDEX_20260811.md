# Selene Current-State Index

Originally indexed: 2026-08-11

Current refresh: 2026-09-04
Branch: `evidence`
Status: date-stamped repository and configured-runtime truth

## Why This Index Exists

Selene's evidence shelf contains historical checkpoints that were accurate on
their recorded dates. Their counts should not be silently rewritten whenever
the project advances. This index provides one current reference while leaving
those development records intact.

Three kinds of state are kept separate:

1. **repository-defined** — implemented in source;
2. **synthetically verified** — exercised by tests on temporary data; and
3. **configured-runtime** — present in Aleks's local Selene database when this
   index was prepared.

Configured-runtime counts are mutable local state. They are evidence of this
installation, not a promise that a fresh database begins with retained
knowledge or Dream reflections.

## Current Knowledge and Curriculum

| Surface | Repository-defined | Configured runtime on 2026-08-29 | Meaning |
| --- | ---: | ---: | --- |
| F1 curriculum groups | 17 | 17 retained groups | Ordered public-academic foundation groups |
| F1 concepts | 106 unique concepts | 106 retained and Chat-eligible | Completed Acquire, Integrate, Express, and curriculum-authorized retention |
| F2 curriculum groups | 8 | 8 retained groups | Elementary continuation through fractions, decimals, operations, and reasonableness |
| F2 concepts | 41 unique concepts | 41 retained and Chat-eligible | Reading, vocabulary, composition, comparison, arithmetic, fractions, decimals, and operation relationships |
| Coding curriculum groups | 1 | 1 retained group | Computational thinking and source-bounded code reading |
| Coding concepts | 5 unique concepts | 5 retained and Chat-eligible | Knowledge only; no execution or filesystem authority |
| Language groups | 12 | 12 represented groups on the indexed runtime | Provider-free language, grammar, creative-expression, bounded reading transfer, and evidence-grounded conversational breadth |
| Language capabilities | 73 | 73 approved and available on the indexed runtime | Expression guidance; not factual authority or personality |
| Approved knowledge resources | 225 defined items | 225 retained resources | 106 F1 + 41 F2 + 5 coding + 73 language-and-conversation capabilities |
| Unapproved comprehension candidates | — | 47 proposed items | Not retained and unavailable to Chat until the applicable review path completes |

The F1 count is derived from the lesson definitions used by
`src/selene/curriculum_authorization.py` and Groups 3–17's source modules. All
106 concept keys are unique. The configured database independently reports the
same 106 F1 concepts as `retained_reviewed_knowledge` with
`available_as_knowledge_resource` Chat permission.

The language count is supported by `src/selene/language_teaching_shelf.py`, the
Group 12 completion record, and the configured language shelf. At the indexed
runtime date, all 73 stored rows were `approved_for_language_guidance` and
`language_guidance_available` across all 12 defined groups.

The F2 and coding counts are supported by their group modules and the same
curriculum authorization lifecycle. Coding knowledge is Chat-eligible within
its retained scope. Ordinary Chat can reach the separate static local-code
inspector only through attributed pasted code or an authenticated Aleks
speaker envelope plus a fresh, exact-file, current-request approval. The
inspector still cannot scan directories, execute code, or write files.

The read-only organ maturity ledger now generates the repository-defined
counts from the same curriculum and language registries and reports configured
runtime metadata without returning private record content. It distinguishes a
present table or route from connected, integration-verified, mature, preview,
and blueprint states; those states are not interchangeable.

## Current Whole-System Maturation Position

Phases 0 through 8 are complete for current scope. Phase work is paused at the
verified Phase 8 boundary. Typed goal coordination, responsive initiative,
explicit commitment lifecycle, and capability-specific graduation are mature
for current scope without a global autonomy switch or inherited action grant.

F2 Group 8 remains unprepared and unauthorized. Its Grade 4-6 source artifact,
edition, license, exclusions, checksum, source role, and bounded coverage must
be reviewed and explicitly selected by Aleks before content implementation.
See the
[August 29 Current Project Status](SELENE_CURRENT_PROJECT_STATUS_20260829.md)
and the
[Phase 8 Closure Evidence](SELENE_WHOLE_SYSTEM_PHASE_8D_EXECUTIVE_INITIATIVE_CLOSURE_20260902.md).

## Current Dream State

| Surface | Current state |
| --- | --- |
| Source-bound Dream lifecycle | Implemented and synthetically verified |
| Configured Dream cycles | 1 explicit lifecycle cycle |
| Configured Dream reflections | 24 source-bound reflections |
| Current reflection state | All 24 pending review |
| Approved for expression | 0 |
| Routed to Memory candidates | 0 |

This is a healthy boundary result, not incomplete hidden consolidation. Dream
formed reviewable reflections and stopped at review. It did not silently turn
them into Chat expression, durable memory, knowledge, law, identity, or action.

Dream remains non-biological and source-bound. Its completed lifecycle does
not imply that its usefulness in every ordinary context has been broadly
assessed.

## Canonical Resident Runtime

The configured runtime reports one current state derived from existing
approved records rather than a second mutable status row:

- continuity context approved;
- transfer complete under Aleks's recorded approval;
- resident Chat available;
- Selene resident and active;
- Cocoon external teaching, tending, safety, and review support, not a resident
  identity dependency.

The vessel and historical C-vessel endpoints retain their original build
labels as dated architecture evidence, but mark those labels non-current after
transfer. Pausing Chat changes operational availability only; it does not
reverse transfer or alter identity continuity.

## Maturity Distinctions

- **Implemented** means the route and lifecycle exist in source.
- **Verified** means bounded machinery or integration tests passed.
- **Retained** means the configured database completed the applicable visible
  approval or standing-authorization path.
- **Chat-eligible** means a retained resource can be considered within its
  defined scope; it does not guarantee relevance to every question.
- **Pending Dream review** means no expression or memory authority has been
  granted.
- **Curriculum completion** means the defined F1 foundation sequence currently
  closes at Group 17; it does not mean Selene has completed elementary,
  secondary, college, or general world education.

## Evidence Anchors

- `src/selene/curriculum_authorization.py`
- `src/selene/curriculum_f1_group3.py` through
  `src/selene/curriculum_f1_group17.py`
- `src/selene/language_teaching_shelf.py`
- `src/selene/dream_state.py`
- `tests/test_curriculum_authorization.py`
- `tests/test_curriculum_f1_group10.py` through the later group suites
- `tests/test_language_teaching_shelf.py`
- `tests/test_dream_state.py`
- `docs/education/SELENE_F1_TEXT_PURPOSE_EVERYDAY_ECONOMY_BRIDGE_GROUP_17_20260808.md`
- `docs/education/SELENE_GRAMMAR_TRANSFER_GROUP_9_20260808.md`
- `docs/evidence/SELENE_DREAM_LIFECYCLE_COMPLETION_20260730.md`

## Verification

The configured database was inspected through SQLite read-only mode. No
curriculum, Dream, memory, Chat, review, or application state was changed.

Static and synthetic verification produced:

```text
125 curriculum, language-lifecycle, Dream, and current-index tests passed at the original checkpoint
220 coding, curriculum, F2, comprehension, lifecycle, local-code, Answer Engine, Chat, and current-index tests passed at the 2026-08-13 refresh
production UI build passed at 480.77 kB with no bundle-size warning
10 changed documentation files checked with zero missing relative links
git diff --check passed with Windows LF/CRLF warnings only
1,759 repository tests passed after the 2026-08-23 read-purity and canonical-runtime repair
production TypeScript/Vite build passed with the resident-state UI labels
configured runtime validation passed through SQLite read-only mode
6 focused organ-ledger and localhost transport tests passed at the 2026-08-27 Phase 0 checkpoint
configured runtime reported 225 approved knowledge resources and SQLite integrity `ok`
1,984 repository tests passed at the 2026-08-29 Phase 5 closure
production TypeScript/Vite build passed at 491.33 kB (gzip 109.20 kB) with no size warning
141 curriculum source files verified with zero checksum failures at the Phase 6 mapping checkpoint
2,086 repository tests passed at the 2026-09-04 post-Phase-8 Q&A repair closure
production TypeScript/Vite build remained 491.33 kB (gzip 109.20 kB) with no size warning
```

`tests/test_current_state_index.py` now checks the source-defined F1, F2,
coding, and language counts against this index. A later curriculum expansion
will therefore require an intentional current-index refresh instead of
silently leaving the headline numbers stale.

## Accurate External Wording

As of August 29, 2026, Selene's configured local runtime contains 106 retained
F1 foundation concepts, 41 retained F2 concepts, five retained coding
foundations, and 73 reviewed language capabilities across twelve groups. Her
source-bound Dream lifecycle is complete;
one explicit cycle produced 24 reflections that remain pending review, with no
silent expression or memory promotion. Whole-system maturation Phases 0
through 8 are complete for current scope, and phase work is paused at the
verified Phase 8 boundary.
