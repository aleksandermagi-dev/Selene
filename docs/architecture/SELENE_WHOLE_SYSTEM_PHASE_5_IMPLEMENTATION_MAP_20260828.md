# Selene Whole-System Phase 5 Implementation Map

Date: 2026-08-28

Status: source-mapped; production implementation not yet started

Parent plan:
[Selene Whole-System Maturation Plan](SELENE_WHOLE_SYSTEM_MATURATION_PLAN_20260827.md)

Previous phase:
[Phase 4 Affect, Self-State, Relationship, and Agency Maturation](../evidence/SELENE_WHOLE_SYSTEM_PHASE_4_AFFECT_RELATIONSHIP_AGENCY_20260828.md)

## Goal

Mature Selene's substance-producing owners so that supported reasoning and
domain work can be useful, attributable, revisable, and independently checked
without creating a monolithic reasoning organ, exposing hidden chain of
thought, inventing facts or citations, scanning private files, or silently
retaining failed attempts.

Phase 5 strengthens existing owners. Core/Mind still coordinates; the Answer
Engine binds typed results; intelligenceOS explores; domain owners verify
their own exact claims; Metacognition advises on fit, correction, and stopping;
and NLO and Voice remain the expression owners.

## Care and Ethical Boundary

This phase must increase capability without increasing unreviewed authority.

- A prediction is not a future fact.
- A hypothesis is not evidence, proof, retained knowledge, or Memory.
- A counterfactual changes declared premises for analysis; it does not rewrite
  history or current reality.
- Wrong, unknown, conflict, and retry are process states, never identity
  failure.
- No internal reasoning trace or hidden chain of thought becomes visible.
- Failed attempts remain inside the active problem unless a separate reviewed
  Memory or teaching path is explicitly used.
- Research may use only attributed supplied packets or an explicitly enabled
  external Great Library consultation and must never invent a citation.
- Local-code inspection requires pasted attributed code or Aleks's explicit
  approval of exact workspace files. It may not scan directories, execute
  code, write files, or infer beyond inspected evidence.
- Exact-domain confidence cannot be upgraded by fluent expression.
- No identity, personality, law, governance, authority, activation, training,
  autonomy, or external-action change is authorized.

## Existing Owner Map

| Responsibility | Current owner | Current connection | Current strength | Phase 5 gap |
| --- | --- | --- | --- | --- |
| canonical facts and obligations | Conversation Spine and current-turn fact ledger | ordinary Chat | mature current-turn input and correction ancestry | all Phase 5 owners must consume the canonical receipt rather than reparse prompt wording |
| typed answer operations | `answer_operations.py` and `answer_ownership.py` | ordinary Chat | method, cause, prediction, hypothesis, comparison, choice, disagreement, correction, preference, summary, closure | no explicit counterfactual contract; planning is mostly folded into generic method; source roles and terminal states are not uniform across every operation |
| open-ended model exploration | `intelligence_os.py` | ordinary Chat | candidate models, challenge, evidence, bounded best-current answer, one revised retry | broad plan generation remains generic and failure learning is not yet one operation-level lineage receipt |
| prediction, hypothesis, comparison, data conflict | `exploratory_reasoning.py` and `bounded_hypothesis.py` | ordinary Chat | explicit epistemic labels, assumptions, alternatives, discriminating checks, claim-level conflict | no counterfactual owner; basis types need a single visible source-role contract across present observations, approved knowledge, reviewed Memory, and verified results |
| causal explanation, choice, bounded practical plans | `answer_substance.py` | ordinary Chat | several strong prompt-grounded cases and semantic units | breadth depends on narrow recognized cases; task-specific objectives, dependencies, resources, constraints, fallback, and stop conditions are not one general typed plan |
| satisfiability, failure diagnosis, informed retry | `problem_resolution.py` and `owner_specific_retry.py` | ordinary Chat | canonical supported/candidate/unknown/conflict/wrong/retry states and one materially changed retry | must be carried consistently into operation results without blind regeneration or cross-session retention |
| checked mathematics | `verified_math.py` through Answer Engine | ordinary Chat | exact bounded arithmetic, decimals as exact literals, equality, a few high-confidence word problems | units, measurement, general fractions/decimals, ratios, algebraic relationships, geometry, and statistics are still unsupported or only incidentally expressible |
| attributed research | `source_backed_research.py` and `research_integrity.py` | ordinary Chat with supplied packets | source statement/inference separation, disagreement, missing evidence, citation traceability | broad/current research still needs a legitimate attributed source-supply path; external Library consultation remains explicit and disabled by default |
| static local-code inspection | `local_code_inspection.py` through Answer Engine | separate bounded route | exact supplied packets/files, observation versus interpretation, file/line citations, sensitive-path denial | Chat currently explains the boundary but deliberately does not execute even when an exact file approval could be supplied |
| whole-answer release | whole-answer composition, epistemic composition, NLO, Voice | ordinary Chat | ordered semantic composition, missing-ground holds, exact-domain locks, expression ownership | new operation and domain receipts must enter this boundary once without duplicated scaffolding or confidence inflation |

## Source Findings

### Existing architecture should be extended, not duplicated

The Answer Engine already routes per canonical obligation. The answer-operation
coordinator already rejects generic prose as completion. Exploratory Reasoning
already has the correct provisional posture, and Problem Resolution already
knows how to distinguish missing knowledge, a false premise, incompatible
constraints, source failure, inference failure, verification failure, and a
materially revised retry.

The missing work is therefore owner depth and consistent connective receipts,
not a second Answer Engine or general “reasoning brain.”

### Present-fact and source precedence

Every Phase 5 owner should receive one typed support envelope in this order:

1. canonical current-turn facts and explicit corrections;
2. current visible observations and constraints;
3. relevant approved general knowledge;
4. privacy-eligible reviewed Memory or experience, scoped as experience rather
   than universal fact;
5. current verified domain results; and
6. attributed supplied research statements or an explicitly enabled external
   Library result.

Absence of a source class is not evidence against a claim. Conflicting sources
remain separate. Expression cannot strengthen epistemic status.

### Exact-domain maturity must remain incremental

Verified Math should grow in dependency order inside the existing exact owner:
units and measurement; fraction and decimal operations; ratios and
proportions; simple algebraic relationships; elementary geometry; then bounded
descriptive statistics. Each increment needs a parser boundary, a normalized
typed problem, an independently recomputed result, visible verification steps,
and a precise unsupported state. Symbolic breadth that cannot be independently
checked remains deferred.

### Code approval is a data boundary, not an identity shortcut

The Phase 4 speaker gate establishes whether private relational context may be
opened. It does not itself authorize filesystem access. Local-code Chat
inspection additionally needs a per-request, exact-file approval receipt from
Aleks (or an attributed pasted code packet). Authentication strength and file
scope are separate checks, and both must be visible when applicable.

## Implementation Order

### Phase 5A — Reasoning owner and operation maturity

- add one explicit counterfactual operation contract with changed premise,
  preserved premises, consequence, basis, limits, and restoration of actual
  state;
- add a typed task-specific planning result with objective, steps,
  dependencies, resources, constraints, risks, fallback, and stopping
  condition while preserving the existing method contract;
- unify source-role receipts for prediction, hypothesis, counterfactual,
  causal explanation, comparison, choice, and disagreement;
- carry canonical epistemic states through operation results;
- require correction and retry ancestry to name the failed approach, useful
  mechanics preserved, changed approach, and explicit stop;
- retain best-current answers when a supported basis exists; and
- do not expose hidden reasoning, automatically retain failures, or recurse
  beyond the existing one-retry limit.

### Phase 5B — Verified mathematics maturation

- extend `verified_math.py`, not a duplicate math organ;
- implement bounded units and measurement conversions;
- implement explicit fraction/decimal and ratio/proportion problems;
- implement simple one-variable linear relationships only when parsing and
  verification are unambiguous;
- add elementary perimeter, area, and bounded descriptive-statistics forms;
- independently verify normalized inputs and results; and
- return precise unsupported or ambiguity states outside the documented
  scope.

### Phase 5C — Research and local-code boundary closure

- preserve supplied-source statement, inference, disagreement, missing
  evidence, and citation-lineage fields;
- keep Great Library consultation external, explicit, optional, and disabled
  by default;
- add an Aleks-selected, current-request local-code approval receipt;
- pass only exact approved workspace files or attributed pasted packets from
  Chat into the existing static inspector;
- reject globs, directories, traversal, sensitive files, stale approvals, and
  untrusted identity/channel claims;
- preserve observation versus interpretation and file/location citations; and
- keep execution, writes, autonomous scans, Memory, teaching, and external
  action disabled.

### Phase 5D — Verification and closure

- focused operation-contract and distinct-example tests;
- false-premise, contradiction, unknown, wrong, and changed-retry tests;
- prediction/hypothesis/counterfactual provenance and delayed-correction
  tests;
- domain-specific independent math checks in prerequisite order;
- citation invention, source disagreement, Library opt-in, exact-file,
  authentication, traversal, sensitive-path, duplicate-file, and
  claim-beyond-scope tests;
- one synthetic disposable mixed reasoning walkthrough;
- broader Chat, Memory privacy, context, NLO, Voice, and sidecar regressions;
- frontend production build and bundle comparison; and
- maturity ledger, evidence, journal, and checkpoint update.

No live high-stakes prediction, personal profiling, distress-shaped test,
resident Memory decision, resident Study/Dream decision, broad filesystem
scan, code execution, package, or reinstall is required for this phase.

## Completion Gate

- every supported operation returns its required semantic fields plus source
  roles and one honest epistemic state;
- unsupported and unknown remain usable terminal states rather than generic
  failure prose;
- prediction, hypothesis, and counterfactual claims preserve assumptions,
  alternatives, revision conditions, and actual-state boundaries;
- a correction or retry materially changes only the affected approach and
  stops after the bounded attempt;
- exact math independently verifies every released result;
- research cannot release an invented or provenance-free citation;
- Chat inspects code only after exact current-request approval and claims no
  more than the inspected files establish;
- whole-answer composition receives each completed operation once; and
- no hidden retention, authority expansion, identity change, or expression
  takeover occurs.

## Verification Baseline

The inherited Phase 4 frontend baseline is:

```text
main application bundle: 491.33 kB (gzip 109.20 kB)
Vite size warning:        none
Study workspaces:         lazy-loaded
```

Phase 5 must keep the main bundle size visible. Backend-only reasoning and
domain maturation should not be allowed to conceal an unrelated frontend
regression.

## Resume Point

Begin production implementation at Phase 5A. Extend the typed operation and
exploratory-reasoning owners first, then connect their epistemic and retry
receipts through ordinary Chat before expanding exact domains.
