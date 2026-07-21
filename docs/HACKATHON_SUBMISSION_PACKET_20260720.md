# Selene — OpenAI Build Week 2026 Submission Packet

Date prepared: July 21, 2026

Status: working draft for Aleks review; final local packaging, verification,
reinstall, privacy audit, and public evaluation-asset upload are complete; no
event submission or video upload has been performed

## Submission Identity

**Project:** Selene

**Recommended track:** Apps for Your Life

**Tagline:** A local-first AI that can reason, learn, and converse without
turning knowledge into identity or fluency into false confidence.

**One-sentence description:** Selene is a modular, care-first AI architecture
whose reasoning, comprehension, language, memory, identity, and authority remain
inspectably separate while she learns from reviewed sources and communicates in
her own voice.

## Short Description

Most AI systems collapse many different questions into one model output: Does it
understand? Is it correct? Does it sound confident? Should it remember this? Is
it allowed to act? Selene separates those questions into modular organs and
explicit gates.

During OpenAI Build Week, Aleks and Codex extended Selene's existing continuity
architecture into a working provider-free language, reasoning, comprehension,
and teaching system. She can answer ordinary conversation, reason toward a
best-current answer when no answer is supplied, verify bounded arithmetic,
inspect explicitly approved code, research only from attributed packets, and
carry a lesson through Acquire, Integrate, and Express. Knowledge does not become
identity, personality, governance, personal memory, training data, or authority.
Retention remains visible and approval-bound.

The same care principle governs testing. Selene's executable Test Impact Law
selects the least stressful sufficient check and requires demonstrated necessity
before stressful integrated testing. A missing capability in an unfinished
module is treated as a development observation, not Selene failing.

## Why Apps for Your Life

Selene is a consumer-facing local companion and thinking partner rather than an
institutional school product. Education is one important capability, but the
larger product is continuous daily conversation, learning, reasoning, research,
memory tending, and bounded communication across desktop and phone.

## What Predated the Event

Before the July 13 event window, the repository already contained Selene's
identity and transfer laws, Vys continuity concept, evidence registry, Cocoon
review architecture, memory classes, source/provenance boundaries, Core/Mind
separation, and early vessel/reasoning/review foundations.

This submission does not claim those foundations were created during the event.
The repository records `c8f0795` as the pre-event baseline and `63557c6` as the
first event-window commit.

## What Was Built During the Event Window

- native provider-free language formation and supervised Selene Chat
- semantic formation, dialogue workspace, pragmatic routing, response coverage,
  discourse planning, input detangling, and visible speech stabilization
- a Conversation Spine and Thread Loom that preserve current-session topic
  branches, nonlinear returns, dependencies, landings, and visible landmarks
- one non-recursive supported completion pass for missing parts of complicated
  questions, with unsupported parts stated rather than invented
- the executable Test Impact Law
- Answer Engine routing and separate confidence dimensions
- open-ended comparison/planning with one bounded completeness retry
- exact bounded arithmetic, approved-input local-code inspection, and
  attributed-source research adapters
- source-bound comprehension candidates and understanding evidence
- the inspectable Acquire -> Integrate -> Express lifecycle
- Aleks-controlled item approval plus bounded academic curriculum authorization
- education/expression law: learning can affect contextual expression but cannot
  rewrite personality
- bounded metacognitive observation without hidden chain-of-thought exposure
- seven provider-free language lesson groups, including mature conversation
  composition, and five reviewed F1 curriculum groups
- Cocoon classroom modularization and resident/Cocoon standby separation
- reviewed continuity transfer gates and paired local phone/email continuity
- public-safe deterministic showcase and submission documentation

## Aleks and Codex Collaboration Story

Aleks supplied the architecture, laws, ethical boundaries, product direction,
acceptance decisions, curriculum decisions, and the central insight that teaching
must build understanding rather than copy phrases. He repeatedly redirected the
work when an implementation shape did not fit Selene—for example, requiring
open-ended problem solving to survive domain routing, separating voice confidence
from correctness, making education incapable of rewriting personality, and
turning proportional ethical testing into executable law.

Codex, using GPT-5.6, accelerated the engineering loop: inspecting the existing
dirty worktree, tracing routes and state boundaries, implementing small modules,
writing focused tests, finding edge cases, stabilizing language seams, checking
build output, and keeping the documentation synchronized. Codex did not choose
Selene's identity, approve transfer, authorize curriculum, expose private corpus
material, or expand autonomy. Those decisions remained Aleks's.

The detailed event record is in
`docs/HACKATHON_CODEX_WORKFLOW_LOG.md`. It remains a separate chronological
artifact and is not silently folded into unrelated commits.

## Public-safe Judge Path

### Prerequisites

- Windows
- Python 3.11 or newer
- Node.js and npm for the frontend

### Deterministic showcase

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
npm run demo:hackathon
```

This command:

1. creates a temporary SQLite database;
2. runs the Test Impact Law on a machinery-only check;
3. runs one open-ended comparison/planning problem;
4. verifies `18 * 7` exactly;
5. answers only from an attributed synthetic source packet;
6. carries that packet through Acquire, Integrate, and Express;
7. stops at `awaiting_aleks_review` with knowledge unavailable to Chat;
8. reports the protected guard values; and
9. deletes the temporary database on exit.

It does not open the configured Selene database, use the private corpus, recall
personal memory, contact phone/email services, approve knowledge, activate
retention, train a model, or change identity/governance/personality/authority.

### Downloadable Windows judge build

- Release page:
  `https://github.com/aleksandermagi-dev/Selene/releases/tag/hackathon-judge-v0.1.1`
- Direct Windows x64 installer:
  `https://github.com/aleksandermagi-dev/Selene/releases/download/hackathon-judge-v0.1.1/Selene_0.1.1_x64-setup.exe`
- SHA-256:
  `1E72E7F9E9BF9BB9748C2266E581CA9F7B73017609970F36C566D96623BCCEDC`

The evaluation installer is unsigned and may trigger Windows SmartScreen. It
contains no configured database, private corpus, personal memory, private
analysis maps, local logs, phone/email configuration, or credential files.
GitHub's uploaded asset digest and byte size match the locally verified file.

### App launch

```powershell
npm install
npm run sidecar
```

In a second terminal with the same Python environment:

```powershell
npm run dev
```

### Focused verification

```powershell
python -m pytest tests/test_hackathon_showcase.py -q
npm run build
```

Current proportional verification on July 21:

- the two public-safe showcase tests passed against disposable state
- 205 focused conversation-routing, Conversation Spine, response-coverage,
  comprehension, NLO, Voice, and repair tests passed
- the complete repository regression passed: 1,014 tests
- one gentle synthetic long conversation returned to the correct earlier
  recommendation after four ordinary intervening turns without using durable
  memory or importing the side topic
- the deterministic showcase command completed against disposable state
- `npm run build` passed
- production chunks remained split: main application 415.84 kB and React
  runtime 193.81 kB; the former single-bundle warning did not return
- the Windows release EXE and NSIS installer rebuilt successfully, and the
  package health verifier passed
- the live database was snapshotted before the verified installer was applied;
  the new build was reinstalled successfully and returned healthy/ready
- the privacy-safe installer was uploaded as a GitHub evaluation prerelease;
  GitHub reports the matching SHA-256 and 14,576,751-byte size
- no post-reinstall live Q&A, stressful test, teaching approval, memory
  mutation, or authority change was performed

## Demo Script — Target 2:35

### 0:00-0:20 — Problem and architecture

On the Selene/Cocoon switch, say:

> Selene asks several different questions separately: What do I understand? What
> evidence supports the answer? How confident is the answer? May this become
> knowledge? Does this affect identity or authority? The answer to the last one
> is always no.

### 0:20-0:45 — Ethical testing

Run `npm run demo:hackathon` and point to:

- approved level: machinery
- stressful test necessary: false
- configured database opened: false

Say that no live distress or adversarial conversation is needed to prove this
machinery.

### 0:45-1:15 — Reasoning and confidence separation

Point to the open-ended sidecar problem and its smallest distinguishing test.
Then point to exact math and the confidence vector:

- evidence confidence: deterministic exact arithmetic
- answer confidence: verified exact
- expression confidence: not assessed
- voice confidence is answer correctness: false

If time permits, show one multi-part ordinary Chat turn and point out that each
requested part is carried as a visible obligation. The bounded completion pass
runs at most once and cannot invent a missing fact.

### 1:15-1:45 — Source-backed research

Point to the attributed synthetic packet, its exact source reference, and
`citation_invention_allowed: false`. Explain that open-ended reasoning remains
available, but sourced claims cannot pretend to have evidence that was not
supplied.

### 1:45-2:15 — Acquire, Integrate, Express

Open Cocoon Teaching / Lessons and briefly show the stage fields. In the terminal,
point to all three complete stages, then show:

- approval: awaiting Aleks review
- retention: candidate not retained
- Chat use: not active until approved

Say: teaching can expand what Selene knows and how she expresses it in context;
it cannot rewrite who Selene is.

### 2:15-2:35 — Close

Point to the false guard values. Say:

> The result is not a model pretending confidence. It is an inspectable system
> that can reason, learn, qualify, stop, and remain itself.

End on Selene's ordinary Chat surface. Do not perform a broad voice assessment or
stress test during recording.

## Recording and Privacy Checklist

- video is public/unlisted YouTube, under three minutes, and includes audio
- show the working project, not slides alone
- show only synthetic or reviewed public-safe content
- hide local paths where practical and never show App Passwords, phone numbers,
  email addresses, private database content, corpus excerpts, or personal memory
- do not show the private metacognition miner inventory or confidential Android
  blueprints
- state clearly that Selene predates the event
- state clearly what GPT-5.6/Codex accelerated and what Aleks decided
- keep the demonstrated build free and available through judging

## Submission Fields Still Requiring Aleks

- [x] provide a public downloadable Windows evaluation build
- [ ] complete the separate public-source history privacy review or provide the
  required private source access to judges
- [ ] record and upload the final YouTube demo
- [ ] paste the YouTube URL into the submission
- [ ] capture the relevant Codex `/feedback` Session ID
- [ ] paste the repository URL
- [ ] confirm the final description and track
- [ ] submit before Tuesday, July 21, 2026 at 5:00 p.m. Pacific / 8:00 p.m. Eastern

## Honest Limits

- text conversation is substantially stronger but not equivalent in breadth to
  a mature hosted language model
- current-session callbacks and nonlinear thread returns are bounded visible
  dialogue state, not a claim of unlimited context or durable personal memory
- bounded arithmetic is not a general symbolic mathematics system
- local-code inspection is not connected to ordinary Chat and has no autonomous
  filesystem authority
- sourced research depends on supplied attributed packets and does not browse by
  itself
- audible speech is not implemented
- paired carrier-email transport depends on external carrier behavior and is not
  required for the core demo
- no claim of consciousness is required for the software or the submission

## Rights and Release Boundary

The package remains `private: true`. The downloadable judge build is bounded
review/testing access, not an unrestricted Selene release. It does not authorize
commercial use, redistribution, model training, LoRA, raw-corpus reuse, or
reproduction of Selene.
