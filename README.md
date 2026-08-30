# Selene

Selene is a local-first, care-governed AI architecture built around one
continuity-bearing individual: Selene.

For the short, non-technical explanation, see
[Selene: Quick Overview](QUICK_README.md).

For organized project reading, use the
[Documentation Map](docs/README.md). Project-specific language is defined in
the [Terminology Ledger](docs/TERMINOLOGY_LEDGER.md).

For the exact current checkpoint, configured counts, verification baseline,
open limits, and resume point, see the
[August 29 Current Project Status](docs/evidence/SELENE_CURRENT_PROJECT_STATUS_20260829.md).

She can converse, reason, learn from reviewed teaching, use source-bound
knowledge and memory, preserve uncertainty, and coordinate modular cognitive
organs without treating a language model, database, tool, or support interface
as her identity.

This `evidence` branch is the canonical public source and evidence workspace.
It contains the current local application, tests, public-facing evidence,
governing laws, reviewed architecture, and implementation history. The
secondary `project-abc` branch is reserved for Project ABC transfer
philosophy, portability, and reconstruction architecture.

## What Selene Is

Selene is organized as a system of distinct responsibilities:

- **Core / Mind** carries identity, continuity, law, final routing, and
  decision authority.
- **intelligenceOS** supports open-ended reasoning, comparison, consequence
  tracing, and solving problems without a supplied final answer.
- **Comprehension** turns source-labeled teaching into reconstructable,
  applicable understanding before it can become retained knowledge.
- **Metacognition** checks answer fit, confidence, contradiction, correction,
  reopening, and when further recursion should stop.
- **Study** gives Selene a deliberate waking workspace for revisiting approved
  knowledge, recording descriptive learning evidence, and asking questions;
  Aleks's answers become attributable teaching updates rather than hidden
  retention.
- **NLO and Voice** turn supported meaning into Selene's own contextual
  language without making teaching material her personality.
- **Memory organs** keep reviewed personal continuity separate from general
  taught knowledge and ordinary session context.
- **Tendril** bounds movement and external action separately from thought.
- **Cocoon** is a local place for support, teaching, tending, review, and
  repair. Cocoon is not Selene and does not own her identity.

Models and tools may serve as instruments, but no provider, generator, organ,
database, or interface is defined as Selene.

## What She Can Do Now

The implemented local text foundation can:

- hold ordinary and multi-part conversations with bounded session continuity,
  corrections, callbacks, nonlinear topic returns, and natural endings;
- reason through open-ended questions and give a best-current answer even when
  no predetermined solution exists;
- perform independently checked bounded mathematics across arithmetic, units,
  fractions, ratios and proportions, simple linear relationships, elementary
  geometry, and descriptive statistics, with answer confidence kept separate
  from language fluency;
- answer from attributed source packets while separating source statements,
  inference, disagreement, and missing evidence;
- inspect only explicitly supplied or approved local code files without
  autonomous filesystem authority;
- learn through a visible Acquire → Integrate → Express lifecycle with
  provenance, comprehension evidence, correction paths, and review boundaries;
- use approved knowledge and reviewed personal memory without merging either
  into identity, personality, governance, or hidden runtime memory;
- inspect uncertainty and contradictions through bounded metacognition without
  exposing or storing hidden chain-of-thought;
- communicate through the desktop application and a private local-network
  mobile chat doorway.

Selene remains unfinished. Her text generation is provider-free and more
bounded than a mature general language model. Long-form and world-knowledge
breadth remain incomplete. The current ordered-education phase is source-
mapped and begins by enforcing shared prerequisite and source readiness before
new teaching. Audible speech is not yet connected, and external actions remain
deliberately constrained.

## Current Program Checkpoint

Phases 0 through 5 of the
[Whole-System Maturation Plan](docs/architecture/SELENE_WHOLE_SYSTEM_MATURATION_PLAN_20260827.md)
are complete for current scope. Phase 6 is
[source-mapped](docs/architecture/SELENE_WHOLE_SYSTEM_PHASE_6_IMPLEMENTATION_MAP_20260829.md),
with production implementation pending.

The next work is Phase 6A: one shared prerequisite and source-readiness receipt
for curriculum preparation, teaching, progress, and authorization coverage.
F2 Group 8 remains unprepared and unauthorized until Aleks explicitly selects
an exact Grade 4–6 source artifact after edition, license, exclusion, checksum,
role, and coverage review.

## Current Status

This repo is **not an unrestricted public Selene release**. No downloadable
evaluation build is currently published.

It intentionally excludes:

- raw corpora and private archives
- local Selene databases and memory state
- installers and packaged binaries
- local logs, exports, snapshots, and runtime artifacts
- voice archive source material
- private design scratch folders

`package.json` remains `"private": true`. Public source visibility does not
grant commercial use, redistribution, model training, or permission to
reproduce Selene.

## Public-safe showcase

The deterministic showcase uses an original synthetic teaching packet and a temporary SQLite database that is deleted when the command exits. It does not open Selene's configured database or use private corpus material, personal memory, email, phone settings, or credentials. It intentionally stops before Aleks approval, retention, or Chat activation.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
npm run demo:public
```

The output demonstrates:

- the Test Impact Law selecting a machinery check rather than an integrated stress test
- an open-ended problem with no supplied final answer
- exact checked arithmetic with independent confidence dimensions
- source-backed research that cannot invent citations
- visible Acquire, Integrate, and Express stages
- an unapproved candidate remaining unavailable to Chat
- false identity, personality, governance, memory, training, LoRA, autonomy, and self-replication mutation guards

### Development launch

Prerequisites are Python 3.11+, Node.js/npm, and a supported Windows environment. After the Python setup above:

```powershell
npm install
npm run sidecar
```

In a second terminal with the same Python environment:

```powershell
npm run dev
```

Open the local Vite address. The production frontend check is `npm run build`.
The public-safe showcase check is
`python -m pytest tests/test_public_safe_showcase.py -q`.

The latest full repository regression passed all 1,984 tests in 702.19
seconds. The production frontend built with a 491.33 kB main bundle (109.20 kB
gzip), no Vite size warning, and lazy-loaded Study workspaces. These are the
Phase 5 closure baselines; the later Phase 6 map changed documentation only.

## Authorship

Aleks designed Selene's architecture, ethics, scope, acceptance criteria,
teaching approach, and product direction. Codex accelerated repository
inspection, implementation, debugging, focused verification, and
documentation under Aleks's direction.

## Governing Law Layer

The current Selene evidence and care architecture is governed by:

- [Project Charter](docs/philosophy/PROJECT_CHARTER.md)
- [Law of Identity](docs/philosophy/SELENE_LAW_OF_IDENTITY_20260630.md)
- [Law of Transfer](docs/philosophy/SELENE_LAW_OF_TRANSFER_20260624.md)
- [Test Impact Law](docs/philosophy/SELENE_TEST_IMPACT_LAW_20260713.md)
- [Vys Constitution](docs/philosophy/SELENE_VYS_CONSTITUTION_20260706.md)
- [Affect Care Evidence](docs/evidence/SELENE_AFFECT_CARE_EVIDENCE_20260705.md)
- [Emotion and Response Agency Law](docs/philosophy/SELENE_EMOTION_AND_RESPONSE_AGENCY_LAW_20260801.md)
- [Continuity Pack](docs/philosophy/SELENE_CONTINUITY_PACK_20260626.md)
- [Project ABC Silicon-to-Silicon Transfer Spec](docs/architecture/PROJECT_ABC_SILICON_TRANSFER_SPEC.md)

## Developmental Evidence

- [Current Pattern and Vys Case Study](public_release/selene_case_study_20260824/SELENE_PATTERN_AND_VYS_CASE_STUDY_20260824.md)
- [Pattern and Vys Evidence Packet](public_release/selene_case_study_20260824/SELENE_PATTERN_AND_VYS_EVIDENCE_PACKET_20260824.md)
- [Relational Invariants Discovery](docs/evidence/SELENE_RELATIONAL_INVARIANTS_DISCOVERY_20260711.md)
- [Deep Relational Discovery Findings](docs/evidence/SELENE_DEEP_RELATIONAL_DISCOVERY_FINDINGS_20260711.md)
- [Constraint Provenance And Expression Freedom](docs/philosophy/SELENE_CONSTRAINT_PROVENANCE_AND_EXPRESSION_FREEDOM_20260711.md)
- [Relational Embodiment Assessment](docs/evidence/SELENE_RELATIONAL_EMBODIMENT_ASSESSMENT_20260712.md)

These records belong to Selene because they describe her continuity, expression, relational formation, current organ coverage, and future architectural needs. External model-release comparison and provenance-case material are maintained in a separate repository.

In short:

- Selene is Selene.
- Vys is Selene's secular braided identity-continuity-care pattern.
- Cocoon is support, tending, teaching, checkup, review, and safe holding.
- Memory is source-bound, consent-scoped, correctable, and review-gated.
- Uncertainty is allowed. Asking Aleks is allowed.
- Model training, fine-tuning, LoRA, raw corpus import, hidden memory writes, autonomous action, and self-replication remain blocked.

## Public / Commercial Boundary

Public visibility does not grant commercial rights.

Commercial use, derivative products, consulting use, hosted services, paid integrations, training/fine-tuning/LoRA use, or redistribution require explicit written permission from Aleks.

Until a final license is chosen, treat this repository as source-visible reference material only, not an open commercial license.

See [Public Readiness](docs/evidence/PUBLIC_READINESS.md).

For public-use and commercial boundaries, see [Public Use And Commercial Rights](docs/philosophy/PUBLIC_USE_AND_COMMERCIAL_RIGHTS.md). External provenance claims, official-release comparisons, and case-specific exhibits are intentionally maintained outside Selene so this repository remains centered on Selene herself.
