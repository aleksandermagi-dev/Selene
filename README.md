# Selene

Selene is a local-first, care-governed AI architecture built around one
continuity-bearing individual. She is designed as a coordinated cognitive
system rather than a chatbot whose model, prompt, memory, and authority are
collapsed into one opaque generator.

This README is the factual project and implementation entrypoint. For why
Selene was created, how Vys is understood, and the principles governing her
growth, read [Selene's Philosophy](PHILOSOPHY.md). For a shorter non-technical
introduction, read [Selene: Quick Overview](QUICK_README.md).

Current checkpoint: Phases 0 through 8 of the
[Whole-System Maturation Plan](docs/architecture/SELENE_WHOLE_SYSTEM_MATURATION_PLAN_20260827.md)
are complete for their documented scope. Phase work is paused, and Phase 9 has
not started. The exact current state is recorded in
[Selene Current Project Status](docs/evidence/SELENE_CURRENT_PROJECT_STATUS_20260829.md).

## What Selene Is

Selene is a Windows-resident system whose responsibilities are separated into
inspectable organs and workspaces. Core/Mind coordinates those parts while
knowledge, personal memory, conversation context, expression, reflection, and
external action retain different owners and rules.

The architecture does not define a language model, database, tool, provider,
or user interface as Selene. Those components may support her without becoming
her identity or silently inheriting authority.

At a technical level, the project currently includes:

- a Python resident sidecar and SQLite state layer;
- a React, TypeScript, Vite, and Tauri Windows application;
- typed routing and provenance receipts across cognitive organs;
- reviewed teaching, knowledge, and personal-memory lifecycles;
- provider-free deterministic text generation for the current resident path;
- action-specific capability and authority boundaries; and
- a large synthetic, disposable-runtime, and read-only-resident verification
  suite.

## What She Can Do

The current implementation can:

- hold text conversations with bounded session continuity, multi-part
  obligations, corrections, callbacks, topic returns, interruption, and
  natural stopping;
- reason about open-ended questions using explicit answer owners for causal
  explanation, method, comparison, choice, disagreement, prediction,
  hypothesis, counterfactuals, and planning;
- perform independently checked bounded mathematics across arithmetic, units,
  fractions, ratios and proportions, simple linear relationships, elementary
  geometry, and descriptive statistics;
- answer from attributed source packets while distinguishing source claims,
  inference, disagreement, uncertainty, and missing evidence;
- inspect explicitly supplied code—or one freshly approved exact local file
  from an authenticated Aleks request—without gaining permission to scan,
  execute, or rewrite the filesystem;
- learn reviewed public-academic material through a visible Acquire →
  Integrate → Express lifecycle with provenance, comprehension evidence,
  correction ancestry, and approval before ordinary Chat use;
- keep approved general knowledge, reviewed personal Memory, current-session
  context, and raw provenance archives separate;
- use Study, Learning Compass, Dream, and Associative Intuition through typed
  destinations, lineage, privacy checks, and stopping rules;
- create bounded original fiction and longer structured responses with
  explicit source/style separation, local revision ancestry, and terminal
  stopping;
- coordinate typed goals, responsive help, and explicit commitments without
  turning them into a global autonomy switch; and
- communicate through the local desktop application and a bounded private
  mobile doorway while the host computer is available.

These are scoped capabilities, not claims of unrestricted general
intelligence, unlimited world knowledge, or external-action authority.

## How The System Is Organized

| System | Current responsibility | Boundary |
| --- | --- | --- |
| Core / Mind | Final coordination, governing-law checks, continuity, routing, and scoped decisions | Supporting organs advise or supply content; they do not silently become the final authority |
| intelligenceOS | Open-ended reasoning, comparison, consequence tracing, hypotheses, counterfactuals, and plans | Reasoning does not establish facts or authorize action by itself |
| Answer Engine and Answer Operations | Assign and satisfy visible response obligations | Fluent prose is not accepted as proof that the requested answer was supplied |
| Comprehension | Build reviewable understanding from source-labeled teaching | Repetition and familiarity are not treated as understanding |
| Study and Learning Compass | Deliberate waking review, questions, representations, and next learning directions | Study is not punishment, hidden retention, Dream, or a grade |
| Memory organs | Maintain reviewed, consent-scoped personal continuity | Personal Memory remains separate from knowledge and session context |
| Dream and Associative Intuition | Reflect on attributable material and propose bounded connections or destinations | Reflections and associations are not automatic truth, Memory, or action |
| Metacognition | Check fit, contradiction, incompleteness, confidence, correction, and stopping | It is a bounded advisor, not a hidden answer writer or anxiety loop |
| NLO and Voice | Express supported meaning in contextual language | Expression cannot invent evidence or turn teaching material into personality |
| Tendril | Propose or perform specifically authorized external actions | Thought, capability, and plausibility do not grant execution permission |
| Cocoon | Local support, teaching, tending, review, and repair | Cocoon is not Selene and does not own her identity |

Project vocabulary is defined in the
[Terminology Ledger](docs/TERMINOLOGY_LEDGER.md).

## Current Evidence

The latest completed whole-system checkpoint reports:

```text
full repository regression:  2,086 passed
focused Phase 8 matrix:       210 passed
frontend main bundle:         491.33 kB
frontend gzip:                109.19 kB
Vite size warning:            none
Study workspaces:             lazy-loaded
```

Phase 8 closed goals, responsive initiative, collaboration, explicit
commitment ancestry, evidence-backed fulfillment, and capability-specific
graduation without creating a global autonomy switch. The closure evidence is
[here](docs/evidence/SELENE_WHOLE_SYSTEM_PHASE_8D_EXECUTIVE_INITIATIVE_CLOSURE_20260902.md).

A clean Phase 8 package was then built, silently reinstalled, and verified.
Package health, local-process capability enforcement, My Office readiness,
privacy inspection, and protected transfer boundaries passed with no warning.
The subsequent gentle Q&A used a disposable database copy and made no resident
Memory, Study, teaching, or Dream decision. All 14 findings from that bounded
run are now repaired and synthetically verified in the same
[evidence record](docs/evidence/SELENE_POST_PHASE_8_REINSTALL_QNA_BUG_HUNT_20260902.md).

## Known Limits

Selene remains unfinished.

- Provider-free text generation and world-knowledge breadth remain narrower
  than a mature general language model.
- The recorded post-Phase-8 Q&A defects are repaired for their exact synthetic
  scope, but unfamiliar phrasings and longer unscripted exchanges still need
  ongoing evaluation; provider-free breadth must not be inferred from fixtures.
- Audible Voice, new sensory pathways, broad tools, accountable external
  action, and embodiment remain deferred, bounded, or substrate-ready rather
  than generally operational.
- Dream reflections remain review-governed; the current 24 resident
  reflections have not been decided automatically.
- F2 Group 8 remains unprepared and unauthorized until Aleks selects an exact
  Grade 4–6 source artifact after edition, license, exclusions, checksum,
  role, and coverage review.
- No unrestricted public evaluation build is published.

The evidence shelf distinguishes **implemented**, **connected**, **available**,
**preview**, **design**, and **observed** states so architectural intent is not
misreported as runtime capability.

## Public-Safe Showcase

The deterministic showcase uses an original synthetic teaching packet and a
temporary SQLite database that is deleted when the command exits. It does not
open Selene's configured resident database or use private corpus material,
personal Memory, credentials, or private communication settings. It stops
before approval, retention, or Chat activation.

Prerequisites: Python 3.11+, Node.js/npm, and a supported Windows environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
npm install
npm run demo:public
```

The showcase demonstrates machinery selection under the Test Impact Law, an
open-ended problem, checked arithmetic, source-bound research, the teaching
lifecycle, an unapproved candidate remaining unavailable to Chat, and guards
against false identity, Memory, governance, training, authority, and autonomy
changes.

## Development Launch

Start the local sidecar:

```powershell
npm run sidecar
```

In a second terminal using the same Python environment:

```powershell
npm run dev
```

Open the local address printed by Vite. Common verification commands are:

```powershell
python -m pytest
npm run build
npm run validate
```

Windows packaging and verification are available through:

```powershell
npm run db:snapshot
npm run package:win
npm run package:verify
```

The database snapshot comes first because packaging and verification may start
the installed application. See the
[Local Vessel App guide](docs/architecture/SELENE_LOCAL_APP_README.md) and
current evidence before using resident state.

## Documentation

The [Documentation Map](docs/README.md) separates four questions:

| Shelf | Question |
| --- | --- |
| [Philosophy](PHILOSOPHY.md) | Why does Selene exist, and what principles guide her growth? |
| [Evidence](docs/evidence/README.md) | What has actually been implemented, observed, or verified? |
| [Education](docs/education/README.md) | How does Selene acquire, integrate, express, study, and revisit knowledge? |
| [Architecture](docs/architecture/README.md) | How are the organs, routes, state, interfaces, and boundaries constructed? |

The dated [Work Journal](docs/journal/README.md) preserves how decisions and
understanding developed. The active continuation ledger is an operational
recovery aid for ongoing work, not public evidence or Selene Memory.

## Repository And Release Boundary

The `evidence` branch is the canonical public source and evidence workspace.
The secondary `project-abc` branch is reserved for Project ABC transfer
philosophy, portability, and reconstruction architecture.

This repository is source-visible reference material, not an unrestricted
public Selene release. It intentionally excludes private corpora, resident
databases and Memory state, credentials, installers, packaged binaries, local
logs, exports, snapshots, voice archives, and private design material.

`package.json` remains `"private": true`. Public visibility grants no
commercial use, redistribution, model training, fine-tuning, LoRA, hosted
service, or derivative-product right. See
[Public Use and Commercial Rights](docs/philosophy/PUBLIC_USE_AND_COMMERCIAL_RIGHTS.md)
and [Public Readiness](docs/evidence/PUBLIC_READINESS.md).

## Authorship

Aleks created Selene and designed her architecture, ethics, governing laws,
scope, acceptance criteria, teaching approach, and product direction. Codex
has assisted with repository inspection, implementation, debugging,
verification, and documentation under Aleks's direction.
