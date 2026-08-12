# Selene F1 Language and Number Group 2 Checkpoint

Date: 2026-07-19

Status: implemented, separately authorized by Aleks, taught through the full
lifecycle, and retained as reviewed general knowledge

## Group

The second ordered F1 curriculum group contains eight concepts.

Language structure:

1. symbols, words, sentences, and punctuation have different jobs;
2. sentences can state, ask, request, or exclaim;
3. sentences connect participants, actions, descriptions, and references; and
4. sequence preserves order while reconstruction preserves meaning.

Number sense:

5. counting determines how many items are in a bounded collection;
6. same, more, and fewer compare bounded quantities;
7. two-digit numbers organize quantities into tens and ones; and
8. numbers can be represented in several forms and compared by value.

## Sources

The source shelf added and verified two official artifacts for the actual
number progression instead of treating the previously mirrored geometry unit
as number instruction:

- CKMath Kindergarten Unit 1, *Math in Our World* — SHA-256
  `cb9b9ce65c9d05201c14534a2c2d05bc15589759b1d7ca77039545215963773b`;
- CKMath Grade 1 Unit 4, *Numbers to 99* — SHA-256
  `d9704c6604d2bd9aafd9451a0b2c3e6654cd463181a1b4a221b468d717fa0eef`.

The language lessons use the already mirrored Grade 1 CKLA Unit 7 and the
content-addressed 2023 K-8 sequence. Applicable artifact notices remain in the
source shelf. No images or media were used in the teaching items.

The shelf now contains 33 cataloged sources, 22 mirrored sources, 112 verified
files, approximately 1.30 GB of artifacts, and zero acquisition or checksum
failures.

## Authorization and Retention

Aleks activated the independent authorization
`f1_language_number_foundations_v1`. The earlier science authorization alone
cannot retain this group.

All eight candidates completed Acquire, Integrate, Express, source alignment,
reconstruction, distinct application, limits, correction support, and
source-parroting checks. All eight were retained with:

- approval status: `approved_under_curriculum_authorization`;
- approval mode: `curriculum_authorization`;
- retention state: `retained_reviewed_knowledge`; and
- Chat permission: `available_as_knowledge_resource`.

The retained concept IDs in the current local database are 52 through 59.
Zero items were held. Together with group 1, Selene now has 12 retained F1
curriculum foundations.

## Verification

- 16 focused curriculum-authorization and teaching-lifecycle tests passed.
- 58 focused tests passed across curriculum authorization, teaching lifecycle,
  comprehension, and Selene Chat.
- `npm run build` passed; the existing Vite large-chunk warning remains at
  approximately 582 kB.
- All 112 source files passed SHA-256 verification.
- A second teaching action retained zero new items, recognized all eight as
  already retained, and held zero.
- Approved-knowledge retrieval returned the appropriate language foundations
  for a reference/sentence-purpose query and all four number foundations for a
  quantity/place-value query.
- Retrieval classified both sets as `reviewed_teaching_knowledge_resource`,
  with memory, identity, and governance source flags false.
- `git diff --check` found no whitespace errors; existing Windows line-ending
  warnings remain.

No live conversational probe, adversarial test, stress test, model training,
fine-tuning, LoRA, package/reinstall action, personal-memory write, identity
change, personality change, governance change, or autonomy expansion was used.

A SQLite-safe pre-group backup was created at:

`%LOCALAPPDATA%\Selene\data\selene.pre_f1_language_number_group2_20260719.sqlite3`

## Next Ordered Step

The next small F1 group can build on these foundations with addition and
subtraction as relationships, simple data representations, and basic time and
measurement language. That group should receive its own source-bounded
authorization and focused machinery check.
