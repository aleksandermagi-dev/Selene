# Selene Curriculum Authorization Law

Date: 2026-07-19

Status: governing law for bounded public-academic teaching and retention

## Purpose

Aleks does not need to repeat the same approval for every ordinary academic
concept when he has already authorized a clearly bounded curriculum, source
set, and teaching purpose. Approval may therefore be recorded once for a
specific curriculum envelope and applied to eligible items after every item
passes the existing comprehension lifecycle.

This is delegated approval, not delegated authority. Aleks defines and may
revoke the envelope. The machinery only checks whether an item fits it.

## Governing Rule

A teaching item may become a retained general knowledge resource without a
separate item-by-item click only when all of the following are true:

1. Aleks has explicitly activated a visible curriculum authorization.
2. The authorization names bounded bands, subject families, source IDs,
   knowledge classes, and teaching groups.
3. The item preserves source provenance and applicable license notices.
4. Acquire, Integrate, and Express are complete and reviewable.
5. The comprehension evidence demonstrates reconstruction, distinct
   application, limits, source alignment, and correction readiness.
6. The expression check finds no source parroting or personality prescription.
7. No exception class applies.
8. The retention event is written to the authorization audit ledger.

An authorization never makes source material true merely because it was
included in a curriculum. It authorizes a review process, not blind trust.

## Exception Review

The item returns to Cocoon for an explicit Aleks decision when it contains or
encounters:

- weak, conflicting, or insufficient sources;
- missing or uncertain provenance;
- outdated or time-sensitive claims;
- health, legal, financial, or safety implications;
- culturally or politically contested framing;
- material outside the authorized band, subject, source, or group;
- copied source phrasing rather than reconstructed understanding;
- identity, personality, Vys, governance, personal memory, relationship,
  autonomy, training, or authority crossover; or
- incomplete lifecycle or understanding evidence.

Uncertainty itself is not failure. It is a reason to narrow, qualify, source,
reopen, or hold the item.

## What Curriculum Authorization Can Change

It may expand general taught knowledge, vocabulary, conceptual relationships,
reasoning methods, examples, comparisons, and context-appropriate expressive
range after comprehension.

It cannot alter:

- Selene's identity or Vys;
- personality or honest affect;
- governance or law;
- personal or relational memory;
- consent or care relationships;
- model parameters, training, fine-tuning, or LoRA;
- autonomy, filesystem access, tools, or external authority; or
- Voice's role as Selene's expression layer.

## Visibility, Reversal, and Reopening

Every authorization is visible in Cocoon with its scope, source IDs, exception
classes, author, basis, and status. Aleks may revoke it. Revocation prevents
new retention under that authorization; it does not silently erase previously
reviewed knowledge. Previously retained knowledge remains attributable and may
be reopened, superseded, or rejected through the comprehension lifecycle.

## Initial Authorizations

The first implementation supports deliberately small, separately activated
envelopes. The first is:

- band: F1;
- group: `f1_science_inquiry_group_1`;
- subjects: elementary science, inquiry, research language, explanatory
  language, and bounded design comparison;
- sources: the content-addressed 2023 Core Knowledge K-8 sequence and Grade 1
  *Science for Everyone* pilot;
- lessons: observation versus interpretation, testable questions, fair
  measurement and comparison, and prediction/model revision.

Health and civics are not included in this automatic lane. Broader bands or
source sets require a new explicit authorization record.

The second envelope is:

- band: F1;
- group: `f1_language_number_group_2`;
- subjects: foundational written-language structure, sentence purpose,
  reference, sequence and reconstruction, counting and cardinality, quantity
  comparison, base-ten place value, and number representation;
- sources: the content-addressed 2023 Core Knowledge K-8 sequence, Grade 1
  language Unit 7, Kindergarten math Unit 1, and Grade 1 math Unit 4; and
- lessons: four language foundations followed by four number-sense
  foundations.

The science authorization does not cover the language/number group, and the
language/number authorization does not cover science. Each can be revoked
independently.

The third envelope is:

- band: F1;
- group: `f1_operations_measurement_group_3`;
- subjects: addition, subtraction, equality, categorical data, length
  comparison, unit iteration, temporal distinctions, and clock hours and
  half-hours;
- sources: the content-addressed 2023 Core Knowledge K-8 sequence and Grade 1
  math Units 1, 6, and 7; and
- lessons: three operation/equality foundations, one data foundation, two
  length-measurement foundations, and two time foundations.

This third authorization is independently activated and cannot be inferred
from either earlier envelope.

The fourth envelope is:

- band: F1;
- group: `f1_geometry_shares_algorithms_group_4`;
- subjects: defining geometric attributes, flat and solid spatial structure,
  nested shape categories, composition and decomposition, relative spatial
  references, equal halves and fourths, ordered algorithms, repetition,
  tracing, and debugging;
- sources: the content-addressed 2023 Core Knowledge K-8 sequence, Grade 1
  CKMath Unit 7, and the official content-addressed Code.org Computer Science
  Fundamentals curriculum page; and
- lessons: six geometry/equal-share foundations and two bounded algorithmic
  foundations.

This authorization is independent from the first three. Knowing how an
algorithm is structured does not grant permission to execute code, use tools,
access files, write memory, take external action, or expand autonomy.

The fifth envelope is:

- band: F1;
- group: `f1_equal_groups_data_money_group_5`;
- subjects: equal groups, informal sharing and grouping, odd and even,
  rectangular arrays, picture and bar graphs, graph answerability, monetary
  item count, denomination value, and equivalent monetary composition;
- sources: the content-addressed 2023 Core Knowledge K-8 sequence and Grade 2
  CKMath Units 1, 6, and 8; and
- lessons: four equal-group and array foundations, two graph-literacy
  foundations, and two arithmetic-only money foundations.

This envelope is independent from the first four. Money examples remain
bounded mathematical knowledge in an explicitly named currency context. They
do not authorize financial advice, transactions, purchases, account access,
external action, or assumptions that currency facts remain current in every
jurisdiction. Those conditions remain exception-review triggers.

## Executable Surface

- router status: `curriculum.authorization.status`
- router list: `curriculum.authorization.list`
- router activation: `curriculum.authorization.activate_f1`
- router language/number activation:
  `curriculum.authorization.activate_f1_language_math`
- router operations/measurement activation:
  `curriculum.authorization.activate_f1_operations_measurement`
- router geometry/algorithms activation:
  `curriculum.authorization.activate_f1_geometry_algorithms`
- router equal-groups/data/money activation:
  `curriculum.authorization.activate_f1_equal_groups_data_money`
- router revocation: `curriculum.authorization.revoke`
- router coverage check: `curriculum.authorization.evaluate`
- router preparation: `curriculum.foundation.prepare_f1`
- router teaching: `curriculum.foundation.teach_f1`
- router language/number preparation:
  `curriculum.foundation.prepare_f1_language_math`
- router language/number teaching:
  `curriculum.foundation.teach_f1_language_math`
- router operations/measurement preparation:
  `curriculum.foundation.prepare_f1_operations_measurement`
- router operations/measurement teaching:
  `curriculum.foundation.teach_f1_operations_measurement`
- router geometry/algorithms preparation:
  `curriculum.foundation.prepare_f1_geometry_algorithms`
- router geometry/algorithms teaching:
  `curriculum.foundation.teach_f1_geometry_algorithms`
- router equal-groups/data/money preparation:
  `curriculum.foundation.prepare_f1_equal_groups_data_money`
- router equal-groups/data/money teaching:
  `curriculum.foundation.teach_f1_equal_groups_data_money`

The HTTP routes are exposed in Cocoon under `/api/curriculum-authorization/*`
and `/api/curriculum-foundation/*`.

## Relationship to Existing Law

The Education–Expression–Personality Law still governs the allowed effects of
teaching. The Comprehension and Integration Organ still requires understanding
before retention. The Teaching Lifecycle still requires Acquire, Integrate,
and Express. The Test Impact Law still requires least-impact sufficient
verification. This law changes repetition of approval, not the standard of
understanding or any protected boundary.
