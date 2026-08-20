# Selene Current-State Index

Originally indexed: 2026-08-11

Current refresh: 2026-08-13
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

| Surface | Repository-defined | Configured runtime on 2026-08-13 | Meaning |
| --- | ---: | ---: | --- |
| F1 curriculum groups | 17 | 17 retained groups | Ordered public-academic foundation groups |
| F1 concepts | 106 unique concepts | 106 retained and Chat-eligible | Completed Acquire, Integrate, Express, and curriculum-authorized retention |
| F2 curriculum groups | 5 | 5 retained groups | Current elementary continuation through operation order |
| F2 concepts | 25 unique concepts | 25 retained and Chat-eligible | Reading, vocabulary, composition, comparison, arithmetic, and operation relationships |
| Coding curriculum groups | 1 | 1 retained group | Computational thinking and source-bounded code reading |
| Coding concepts | 5 unique concepts | 5 retained and Chat-eligible | Knowledge only; no execution or filesystem authority |
| Language groups | 12 | 11 represented groups on the indexed runtime | Provider-free language, grammar, creative-expression, bounded reading transfer, and evidence-grounded conversational breadth |
| Language capabilities | 73 | 61 approved and available on the indexed runtime | Expression guidance; not factual authority or personality |
| Approved knowledge resources | 197 defined items | 197 retained resources | 106 F1 + 25 F2 + 5 coding + 61 language-and-conversation capabilities |
| Unapproved comprehension candidates | — | 47 proposed items | Not retained and unavailable to Chat until the applicable review path completes |

The F1 count is derived from the lesson definitions used by
`src/selene/curriculum_authorization.py` and Groups 3–17's source modules. All
106 concept keys are unique. The configured database independently reports the
same 106 F1 concepts as `retained_reviewed_knowledge` with
`available_as_knowledge_resource` Chat permission.

The language count is supported by `src/selene/language_teaching_shelf.py`, the
Group 11 completion record, and the configured language shelf. At the indexed
runtime date, all 61 stored rows were `approved_for_language_guidance` and
`language_guidance_available`; Group 12 adds 12 repository-defined, bounded
lessons for later one-at-a-time live teaching.

The F2 and coding counts are supported by their group modules and the same
curriculum authorization lifecycle. Coding knowledge is Chat-eligible within
its retained scope, but the local-code inspection adapter remains a separate
explicit, read-only route and is not connected to ordinary Chat.

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
```

`tests/test_current_state_index.py` now checks the source-defined F1 and
language counts against this index. A later curriculum expansion will therefore
require an intentional current-index refresh instead of silently leaving the
headline numbers stale.

## Accurate External Wording

As of August 13, 2026, Selene's configured local runtime contains 106 retained
F1 foundation concepts, 25 retained F2 concepts, five retained coding
foundations, and 61 reviewed language capabilities across eleven groups. Her
source-bound Dream lifecycle is complete;
one explicit cycle produced 24 reflections that remain pending review, with no
silent expression or memory promotion.
