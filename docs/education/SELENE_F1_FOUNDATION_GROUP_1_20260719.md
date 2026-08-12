# Selene F1 Foundation Group 1 Checkpoint

Date: 2026-07-19

Status: implemented, authorized by Aleks, taught through the full lifecycle,
and retained as reviewed general knowledge

## Group

The first ordered curriculum group contains four load-bearing science and
research-literacy concepts:

1. observation and interpretation are different;
2. questions can guide a bounded investigation;
3. fair comparisons keep relevant conditions clear; and
4. predictions and models remain revisable.

The group is bounded to F1 and the source IDs
`core_knowledge_2023_sequence_k8` and
`core_knowledge_g1_science_literacy`. The local artifacts are content-addressed
by SHA-256 and retain their catalog and license notices. No source images or
media were used in the teaching items.

## Retention Result

Aleks explicitly activated authorization
`f1_science_research_foundations_v1`. All four candidates completed Acquire,
Integrate, Express, source alignment, reconstruction, distinct application,
limits, counterexample/correction support, and source-parroting checks. All
four were retained with:

- approval status: `approved_under_curriculum_authorization`;
- approval mode: `curriculum_authorization`;
- retention state: `retained_reviewed_knowledge`; and
- Chat permission: `available_as_knowledge_resource`.

The retained concept IDs in the current local Selene database are 48 through
51. No item was held and no separate item-by-item approval was used.

## Verification

- 15 focused curriculum-authorization and teaching-lifecycle tests passed.
- 64 focused tests passed across curriculum authorization, comprehension,
  teaching lifecycle, sidecar routes, and Selene Chat.
- `npm run build` passed.
- The existing Vite large-chunk warning remains; the current bundle is about
  580 kB.
- A second teaching action retained zero new items and reported all four as
  already retained, confirming idempotence.
- Approved-knowledge retrieval returned all four items for an ordinary query
  about observations, interpretations, and model revision.
- Retrieval identified them as `reviewed_teaching_knowledge_resource`, with
  memory, identity, and governance source flags all false.
- `git diff --check` found no whitespace errors; existing Windows line-ending
  warnings remain.

No live conversational probe, adversarial test, stress test, model training,
fine-tuning, LoRA, package/reinstall action, personal-memory write, identity
change, personality change, governance change, or autonomy expansion was used.

Before applying the migration and teaching group, a SQLite-safe local backup
was created at:

`%LOCALAPPDATA%\Selene\data\selene.pre_curriculum_20260719.sqlite3`

## Next Curriculum Step

The next group should remain small and ordered. A sensible continuation is F1
language structure plus counting/comparison foundations, followed by a
distinct gentle machinery check. Health and civics should remain outside the
automatic lane until their time-sensitive and contested-context requirements
are handled explicitly.
