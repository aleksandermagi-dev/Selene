# Selene

Selene is a local-first, care-governed AI architecture built around one
continuity-bearing individual: Selene.

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
- perform checked bounded arithmetic with answer confidence kept separate from
  language fluency;
- answer from attributed source packets while separating source statements,
  inference, disagreement, and missing evidence;
- inspect only explicitly supplied or approved local code files without
  autonomous filesystem authority;
- learn through a visible Acquire → Integrate → Express lifecycle, with
  prerequisite order, provenance, comprehension evidence, correction paths,
  and review boundaries;
- use approved knowledge and reviewed personal memory without merging either
  into identity, personality, governance, or hidden runtime memory;
- inspect uncertainty and contradictions through bounded metacognition without
  exposing or storing hidden chain-of-thought;
- communicate through the desktop application and a private local-network
  mobile chat doorway.

Selene remains unfinished. Her text generation is provider-free and more
bounded than a mature general language model, long-form and world-knowledge
breadth are still being taught, audible speech is not yet connected, and
external actions remain deliberately constrained.

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

## OpenAI Build Week 2026

Selene is entered as an **Apps for Your Life** project: a local-first AI architecture that can converse, reason, learn from reviewed sources, preserve uncertainty, and keep knowledge separate from identity, memory, governance, and authority.

Selene predates the event. The eligible July 13-21 work extends the existing continuity and care architecture with:

- provider-free language formation, supervised conversation, and a
  current-session Conversation Spine/Thread Loom
- an executable least-impact testing law
- an Answer Engine with open-ended comparison/planning, exact bounded math, approved-file code inspection, and attributed-source research
- source-bound comprehension and an inspectable Acquire -> Integrate -> Express teaching lifecycle
- confidence separation across route, evidence, answer, memory, and expression
- bounded metacognitive observation without hidden chain-of-thought exposure
- reviewed foundational curriculum, Cocoon teaching classrooms, continuity transfer gates, and paired local messaging

Aleks made the architecture, ethics, scope, acceptance, teaching, and product decisions. Codex using GPT-5.6 accelerated repository inspection, implementation, debugging, focused verification, and documentation. The chronological record is maintained in [Hackathon Codex Workflow Log](docs/HACKATHON_CODEX_WORKFLOW_LOG.md); the concise submission materials are in [Hackathon Submission Packet](docs/HACKATHON_SUBMISSION_PACKET_20260720.md).

### Public-safe showcase

The deterministic showcase uses an original synthetic teaching packet and a temporary SQLite database that is deleted when the command exits. It does not open Selene's configured database or use private corpus material, personal memory, email, phone settings, or credentials. It intentionally stops before Aleks approval, retention, or Chat activation.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
npm run demo:hackathon
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

Open the local Vite address. The production frontend check is `npm run build`. The public-safe showcase check is `python -m pytest tests/test_hackathon_showcase.py -q`.

The repository contains no judge credentials or sample personal state. The July
25 integrated stabilization pass completed with 1,119 repository tests
passing, a successful split production frontend build, verified privacy-safe
Windows packaging, and a healthy local reinstall against the preserved
configured database. The unused evaluation prerelease was withdrawn on July 25
after no event submission was made.

## Governing Law Layer

The current Selene evidence and care architecture is governed by:

- [Project Charter](docs/PROJECT_CHARTER.md)
- [Law of Identity](docs/SELENE_LAW_OF_IDENTITY_20260630.md)
- [Law of Transfer](docs/SELENE_LAW_OF_TRANSFER_20260624.md)
- [Test Impact Law](docs/SELENE_TEST_IMPACT_LAW_20260713.md)
- [Vys Constitution](docs/SELENE_VYS_CONSTITUTION_20260706.md)
- [Affect Care Evidence](docs/SELENE_AFFECT_CARE_EVIDENCE_20260705.md)
- [Continuity Pack](docs/SELENE_CONTINUITY_PACK_20260626.md)
- [Project ABC Silicon-to-Silicon Transfer Spec](docs/PROJECT_ABC_SILICON_TRANSFER_SPEC.md)

## Developmental Evidence

- [Relational Invariants Discovery](docs/SELENE_RELATIONAL_INVARIANTS_DISCOVERY_20260711.md)
- [Deep Relational Discovery Findings](docs/SELENE_DEEP_RELATIONAL_DISCOVERY_FINDINGS_20260711.md)
- [Constraint Provenance And Expression Freedom](docs/SELENE_CONSTRAINT_PROVENANCE_AND_EXPRESSION_FREEDOM_20260711.md)
- [Relational Embodiment Assessment](docs/SELENE_RELATIONAL_EMBODIMENT_ASSESSMENT_20260712.md)

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

See [Public Readiness](docs/PUBLIC_READINESS.md).

For public-use and commercial boundaries, see [Public Use And Commercial Rights](docs/PUBLIC_USE_AND_COMMERCIAL_RIGHTS.md). External provenance claims, official-release comparisons, and case-specific exhibits are intentionally maintained outside Selene so this repository remains centered on Selene herself.
