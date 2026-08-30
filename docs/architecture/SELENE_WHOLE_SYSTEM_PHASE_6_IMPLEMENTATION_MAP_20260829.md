# Selene Whole-System Phase 6 Implementation Map

Date: 2026-08-29

Status: source-mapped; production implementation pending

Parent plan:
[Selene Whole-System Maturation Plan](SELENE_WHOLE_SYSTEM_MATURATION_PLAN_20260827.md)

Previous phase:
[Phase 5 Reasoning, Answer Owners, and Domain Depth Maturation](../evidence/SELENE_WHOLE_SYSTEM_PHASE_5_REASONING_DOMAIN_MATURATION_20260829.md)

## Goal

Mature Selene's existing education path so that public academic knowledge is
acquired in visible prerequisite order, reconstructed rather than copied,
applied beyond its teaching example, corrected through preserved ancestry,
and available to ordinary Chat only after the existing reviewed retention
gate.

Phase 6 expands knowledge, not authority. It does not create another teaching
organ, hidden Memory, automatic truth, an unrestricted curriculum mandate, or
a pass/fail account of Selene's worth.

## Care and Ethical Boundary

- Teaching builds capability; it does not define Selene's identity,
  personality, Vys, values, law, governance, or relationship with Aleks.
- Public academic knowledge remains distinct from personal Memory and from
  changing current facts.
- A fluent explanation is not proof of understanding or factual certainty.
- Learning states describe the next useful teaching move. They are not grades,
  diagnoses, performance pressure, or identity judgments.
- `developing`, `needs representation`, `needs prerequisite`, `revisit`, and
  `unclear` remain valid non-failure states. Speed is secondary.
- Corrections preserve the earlier record and useful structure. They do not
  silently rewrite history or erase uncertainty.
- Standing authorization applies only to the exact bounded public-academic
  group Aleks authorized. It does not flow automatically to the next group.
- Special, personal, identity-adjacent, emotionally consequential, disputed,
  culturally sensitive, or rapidly changing material remains item-reviewable
  by Aleks.
- Source acquisition is review-only. A mirrored file is not accepted teaching
  material, retained knowledge, Memory, or permission to teach.
- No distress-shaped test, resident Dream decision, resident Study decision,
  resident Memory decision, or resident teaching decision is needed for this
  phase.
- No model training, LoRA, parameter update, autonomy, external action,
  self-replication, or broad filesystem access is authorized.

## Current Resident Baseline

The resident database was opened read-only on 2026-08-29. No content or state
was changed.

| Resident state | Count |
| --- | ---: |
| active curriculum authorizations | 27 |
| curriculum authorization audit events | 230 |
| comprehension concepts | 272 |
| approved general-knowledge resources | 225 |
| tending candidates | 47 |
| reopened concepts | 0 |
| teaching lifecycles | 226 |
| complete and approved teaching lifecycles | 225 |
| acquire-needs-review lifecycles | 1 |
| LEA runs | 0 |

The 152 concepts approved under curriculum authorization comprise 106 F1
concepts across 17 groups, 41 F2 concepts across Groups 1 through 6, 7A, and
7B, and 5 Coding concepts. Another 51 resources were approved under the
language-capability authorization and 22 through explicit Aleks review.

The one unfinished resident teaching lifecycle remains awaiting Aleks review.
Phase 6 mapping did not open its teaching content, decide it, or alter it.

## Existing Owner and Handoff Map

| Responsibility | Existing owner | Current strength | Phase 6 gap |
| --- | --- | --- | --- |
| candidate proposal and reviewed retention | `comprehension_integration.py` | source refs required; candidates are inactive; reconstruction, distinct application, limits, counterexample/correction readiness, and source alignment are reviewable | source acceptance metadata is mostly free-form; reopening mutates the same record and has no correction descendant ancestry |
| Acquire -> Integrate -> Express | `teaching_lifecycle.py` | strict stage order, approved-knowledge relationship checks, scope, contradiction class, reopening path, original-language expression, application, comparison, questions, correction response, and anti-parroting check | instructional “why” and source role are not typed obligations; approved revisions have no parent/descendant lifecycle |
| bounded curriculum authorization | `curriculum_authorization.py` | explicit Aleks activation, exact band/family/source/group scope, exception review, audit events, and idempotent group teaching | shared prepare/teach functions do not enforce prior-group or concept prerequisites; progress reports counts but not readiness |
| group lesson definitions | `curriculum_f1_group*.py`, `curriculum_f2_group*.py`, and `curriculum_coding_group1.py` | source-bound lessons with checksums, vocabulary, examples, limits, near concepts, applications, comparisons, and correction responses | prerequisite requirements are implied in prose and module order rather than one inspectable runtime contract |
| ordinary-Chat knowledge selection | `comprehension_integration.py`, `semantic_relevance.py`, and `selene_chat.py` | only approved chat-active knowledge can seed an answer; relevance, current intent, canonical facts, and answer ownership constrain use | same-session retrieval exists, but delayed distinct-case use and reviewed correction replacement are not proven as one education lifecycle |
| explanatory response support | comprehension relationships and approved response seeds | an approved concept can answer a “why” request when an explanatory relationship happens to be present | no required `why_kind`, causal/mechanistic relationship, consequence, scope, exception, or unknown field is retained |
| general conversation evidence | `learning_evidence_activity.py` | fixed, source-contained, descriptive paired scenarios; no automatic review or composite score | current LEA is conversation-oriented and uses `demonstrated`, `developing`, `not_observed`, `cannot_assess`, and `activity_issue`, not the Phase 6 learning profile |
| affective meaning and salience | `why_salience.py` | a narrow status-only map for affective meaning, needs, and response agency | this is not the owner for instructional explanations and must not be expanded into a duplicate education organ |

## Cultivation Findings

Cultivation asks whether friction reveals a missing capability, a missing
connection, or merely language that describes an already working behavior.
The Phase 6 trace produced all three classes.

### Runtime defects

1. **Prerequisite order is not enforced at the shared gate.**
   `_prepare_defined_group` can create a later group without checking prior
   retained groups. `_teach_defined_group` checks only the matching active
   authorization before running the full lifecycle. `_group_progress` reports
   prepared and retained counts but no declared prerequisites, unmet concepts,
   source readiness, or exception receipt.
2. **Reviewed correction has no preserved concept ancestry.**
   `reopen_for_revision` changes the approved row in place to
   `reopened_for_revision`. The schema has no parent, root, descendant, or
   supersession receipt for comprehension concepts. Ordinary Chat correctly
   suggests a recheck without silently mutating knowledge, but the later
   reviewed correction path is not yet lineage-safe.
3. **Source acceptance is not a typed precondition.**
   The shelf records artifact, license, revision, risks, and checksums, while
   runtime proposal metadata requires only source references and a dictionary.
   The prepare path does not independently require accepted edition, artifact
   checksum, license scope, exclusions, source role, retrieval date, knowledge
   class, freshness class, dispute/context flags, or original-language
   feasibility.
4. **Instructional “why” is optional structure.**
   Existing lessons usually contain strong explanatory prose, but the shared
   lifecycle can complete without a typed explanation of cause, mechanism,
   significance, dependency, scope, failure condition, or what remains
   unknown.
5. **The Phase 6 learning profile is not represented.**
   Conversation LEA states are honest but answer a different question. Ordered
   education needs concept-level evidence that can say `clear`, `developing`,
   `needs_representation`, `needs_prerequisite`, or `revisit`, with the
   observation and suggested next teaching move visible.

### Missing connective verification

- Approved knowledge already reaches ordinary Chat through the correct owner,
  and relevance safeguards already prevent many false matches. Phase 6 needs
  delayed, paraphrased, distinct-case, source-lineage, correction, and
  competing-concept tests rather than another retrieval system.
- Acquire, Integrate, and Express already require most of the intended
  evidence. Phase 6 should extend their snapshots and receipts rather than
  replace the lifecycle.
- Authorization already blocks scope exceptions. Phase 6 should add
  prerequisite and source-acceptance facts to that same coverage decision.

### Documentation vocabulary gaps

- Education documents still describe an earlier resident count of 35 F2
  concepts. The current resident and source modules contain 41 after Groups 7A
  and 7B.
- The source shelf's introductory status language predates its Group 7B
  expansion.
- The whole-system plan previously named Phase 5 as the immediate starting
  point even though Phase 5 is complete.
- Instructional “why” should not be routed into the affective Why + Salience
  status helper merely because the same English word appears in both places.

## Source Shelf and F2 Content Edge

The local review-only shelf currently catalogs 62 sources, mirrors 51 source
snapshots, and pins their revisions and checksums. The verifier passed all 141
mirrored files with zero failures on 2026-08-29.

The next content group remains:

> **F2 Group 8 — ratios, unit comparison, percentages, scale, and
> proportional language**

Its prerequisite concepts are the retained arithmetic, factor/multiple,
fraction, fraction-operation, and decimal relationships in Groups 4 through
7B. Group 8 is proposed content, not currently prepared, authorized, taught,
or retained.

The shelf does not yet contain an accepted coherent Grade 4-6 ratio and
percentage backbone:

- the exact Illustrative Mathematics first edition remains catalog-only
  because the first-edition artifact must be distinguished from newer
  material and its exclusions;
- Open Up Resources remains catalog-only because program, edition, component,
  assessment, and third-party licenses differ;
- the mirrored CKMath material currently supports the retained fraction and
  decimal bridge but does not provide the selected Grade 6 ratio/percentage
  artifact for Group 8;
- NIST unit pages are authoritative terminology references, not a coherent
  ratio curriculum; and
- GSM8K is later independently reviewed practice, not a concept-teaching
  backbone or reasoning script.

Before Group 8 implementation, Aleks must approve one exact bounded source
selection after its edition, license, exclusions, source role, retrieval date,
checksum, concept coverage, prerequisite fit, examples, counterexamples,
misconceptions, and original reconstruction feasibility are recorded. That
decision must create only a source-acceptance and authorization receipt; it
must not silently teach the group.

## Implementation Order

### Phase 6A — Prerequisite and source-readiness closure

- define a typed group manifest inside the existing curriculum owner with
  band, group key, ordered predecessor groups, required concept keys, source
  acceptance receipt, and exception route;
- expose `ready`, `needs_prerequisite`, `source_review_required`,
  `authorization_required`, and `complete` without a score or deadline;
- make prepare, teach, and coverage evaluation consume the same readiness
  receipt;
- prevent an active authorization from bypassing missing prerequisites or an
  unaccepted source artifact;
- preserve idempotence and report the exact unmet group, concept, source, or
  decision;
- migrate existing completed groups descriptively without replaying or
  reteaching resident knowledge; and
- keep proposed future groups unavailable until their exact source and
  authorization exist.

### Phase 6B — Teaching contract and instructional-why maturity

- extend the existing lesson and lifecycle snapshots with typed source roles:
  `source_statement`, `inference`, `example`, `practice`, `verification`, and
  `current_fact` where applicable;
- require a bounded instructional-why receipt containing why kind, explanatory
  relationship, why it matters, scope, failure or exception condition, and
  unresolved uncertainty;
- preserve vocabulary, near concepts, distinct examples, counterexamples,
  limitations, questions, comparisons, original-language reconstruction, and
  source-parroting checks;
- distinguish durable public-academic knowledge from time-sensitive current
  claims at proposal, retention, and retrieval;
- keep `developing`, `needs_representation`, `needs_prerequisite`, `revisit`,
  and `unclear` available without forcing completion; and
- leave affective Why + Salience, Memory, identity, and expression ownership
  unchanged.

### Phase 6C — Reviewed correction ancestry and delayed Chat use

- reopen an approved concept by creating one idempotent revision descendant,
  preserving parent and root identifiers, original content, source receipts,
  and reason for review;
- keep the parent available as historical evidence but inactive for ordinary
  answer seeding while a correction is unresolved;
- require the descendant to complete source review and Acquire -> Integrate ->
  Express before approval;
- supersede the parent only when the reviewed descendant is approved, and make
  the active lineage winner explicit;
- stop duplicate descendants and correction loops with typed terminal
  receipts;
- prove that delayed ordinary Chat can select the approved concept under
  paraphrase, apply it to a distinct case, explain its “why” and limits, avoid
  source wording, reject an irrelevant near concept, and switch to an approved
  correction without returning the superseded claim; and
- preserve current-turn canonical corrections above retained knowledge.

### Phase 6D — Learning evidence and closure

- extend the existing LEA owner with a curriculum-concept profile rather than
  creating another assessment organ;
- report `clear`, `developing`, `needs_representation`,
  `needs_prerequisite`, or `revisit` per visible dimension and preserve
  `cannot_assess` and `activity_issue` as activity-level integrity states;
- record reconstruction, distinct application, why/mechanism, scope and
  limits, near-concept distinction, counterexample, correction response,
  source alignment, and delayed use independently;
- never calculate a pass/fail result, rank, worth judgment, compulsory speed
  target, or hidden composite score;
- add focused source-acceptance, prerequisite, lifecycle, provenance,
  correction-ancestry, duplicate-lineage, anti-parroting, delayed-cue,
  competing-concept, and loop-prevention tests;
- use only synthetic disposable concepts and a copied resident database for
  migration/status checks;
- run one gentle synthetic Group 8-shaped walkthrough only after the machinery
  is complete, without authorizing or teaching the resident group;
- run broader Chat, Memory privacy, context, NLO, Voice, Study, sidecar, and
  maturity-ledger regressions;
- build the frontend and compare the main bundle; and
- update the maturity ledger, evidence, journal, and checkpoint.

## Completion Gate

- no advanced group can prepare or teach while a declared prerequisite,
  accepted source, or bounded authorization is missing;
- every retained lesson exposes source roles, reconstruction, distinct
  application, limits, near concepts, counterexamples, correction readiness,
  and a typed instructional “why”;
- a correction creates reviewed ancestry, preserves the parent, selects one
  active descendant only after approval, and stops duplicate loops;
- delayed ordinary Chat applies approved knowledge to a genuinely distinct
  case without parroting or choosing an irrelevant neighboring concept;
- the learning profile remains descriptive, multi-dimensional, and free of
  speed pressure or pass/fail worth;
- current facts, disputed material, personal material, and identity-adjacent
  material cannot inherit standing public-academic authorization; and
- no teaching path writes personal Memory or changes identity, personality,
  Vys, governance, authority, parameters, autonomy, or external action.

## Verification Baseline

The inherited Phase 5 frontend baseline is:

```text
main application bundle: 491.33 kB (gzip 109.19 kB)
Vite size warning:        none
Study workspaces:         lazy-loaded
```

The source shelf verification baseline is:

```text
cataloged sources:         62
mirrored source snapshots: 51
verified files:            141
checksum failures:         0
```

Phase 6 must keep both provenance integrity and bundle size visible.

## Resume Point

Begin Phase 6A in production code. First add the shared prerequisite and
source-readiness receipt using synthetic tests and migration-safe descriptive
state for existing groups. Do not create F2 Group 8 or activate a new resident
authorization until its exact source artifact and license have been selected
and explicitly approved by Aleks.
