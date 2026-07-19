# Selene Hackathon Repository Retention Audit

Date: 2026-07-19

Status: read-only classification checkpoint; no file has been deleted, moved,
archived, committed, packaged, reinstalled, published, or admitted to the
Great Library by this audit

## Purpose

Prepare Selene's repository for a clear hackathon presentation without
discarding provenance, weakening safety evidence, confusing the Great Library
with a backup drive, or moving protected material during the Library Vault
freeze.

This audit separates four different questions:

1. What consumes local disk space?
2. What affects repository clone and review size?
3. What enters the Cocoon frontend bundle?
4. What may become a source-bound Great Library proposal?

Those questions must not be collapsed into one deletion decision.

## Inspected State

- Branch: `evidence`.
- Relationship to `origin/evidence`: 34 commits ahead and zero behind at the
  time of inspection.
- The worktree contains substantial related uncommitted implementation and
  documentation work. It must be checkpointed intentionally before any
  structural cleanup.
- `docs/HACKATHON_CODEX_WORKFLOW_LOG.md` was not modified.
- The external Library exists at
  `C:\Users\aleks\Desktop\TheGreatLibraryofAleksander`.
- Its Charter, admission interface, source rules, agent rules, and Vault freeze
  policy were read before making archival recommendations.

## Finding 1: Local Build Output Is the Main Safe Disk-Reclamation Target

The existing guarded cleanup script identifies these rebuildable outputs:

| Path | Approximate size | Classification |
| --- | ---: | --- |
| `src-tauri/target/` | 7.88 GB | Rebuildable Rust/Tauri output |
| `dist-sidecar/` | 489 MB | Rebuildable packaged sidecar output |
| `build-sidecar/` | 9.76 MB | Rebuildable packaging intermediate |
| `dist-ui/` | 2.12 MB | Rebuildable frontend output |
| `scripts/__pycache__/` | 0.67 MB | Rebuildable Python cache |
| `src-tauri/gen/` | 0.32 MB | Rebuildable generated output |
| `.pytest_cache/` | 0.08 MB | Rebuildable test cache |

Together these currently occupy approximately 8.38 GB. They are ignored by
Git and are already covered by `npm run clean:check` and the explicitly
destructive `npm run clean` command.

No cleanup command was applied. Deletion still requires an explicit Aleks
decision because rebuildable does not mean presently authorized for removal.

Other ignored directories such as `tmp/`, `exports/`, and `output/` contain
about 61 MB collectively but may include useful inspection or handoff
artifacts. They require a file-class review rather than blanket deletion.
`node_modules/` and the packaging virtual environment are reproducible but
should normally remain until dependency or packaging work is finished.

## Finding 2: Repository Source Is Not the Disk Problem

Tracked worktree size by major area is approximately:

| Area | Tracked size | Decision |
| --- | ---: | --- |
| `analysis/` | 67.03 MB | Review public/privacy classification; do not bulk delete |
| `src-ui/` | 2.13 MB | Live frontend source; keep |
| `src/` | 1.84 MB | Live backend source; keep |
| `docs/` | 1.45 MB | Small; organize for readability, not disk savings |
| `scripts/` | 1.07 MB | Reproducibility and evidence tooling; keep pending script-level review |
| `tests/` | 0.80 MB | Active regression and safety evidence; keep |
| `public_release/` | 0.72 MB | Existing public artifacts; review against hackathon story |

Git currently reports approximately 36.69 MiB of packed objects and 27.51
MiB of loose objects. Removing a tracked file in a new commit does not erase it
from Git history or materially shrink an existing clone. History rewriting
would be a separate, high-risk operation and is not recommended during the
hackathon stabilization window.

The largest tracked file is
`analysis/metadata_audit_20260605/metadata_traces.csv` at approximately
61.49 MB. It accounts for most of the tracked analysis size. Its privacy,
public-demonstration value, and reproducibility role must be reviewed without
exposing its contents before any branch or release decision. If it derives
from protected material, the shared Great Library is not an authorized
destination.

## Finding 3: No Backend Module Is Currently Proven Unused

A static Python import graph was built from the runtime entrypoints
`selene.__main__` and `selene.sidecar`.

- 78 package modules were inspected.
- 77 were reachable from the runtime roots.
- The only non-reached file was the empty `selene.__init__` package marker.
- Every substantive backend module has a source-level inbound dependency.

Therefore this audit identifies **zero backend modules safe to archive or
remove**. A file seeming old from its name is not enough evidence when it
remains connected to routing, transfer preparation, evidence review, Cocoon,
or other runtime paths.

A later removal requires all of:

1. no runtime reachability;
2. no database-schema or migration dependency;
3. no router, sidecar, packaging, or CLI dependency;
4. no current law or safety contract dependency;
5. replacement or retirement of its tests; and
6. a deprecation record naming the last supporting commit and replacement.

## Finding 4: Tests Are Active Safety Evidence, Not Immediate Archive Material

The current suite collects 760 tests without collection errors. Test files
cover live runtime code, boundary law, teaching and comprehension, memory,
transfer preparation, source research, exact math, Cocoon, language, Voice,
miners, packaging-related behavior, and historical reconstruction machinery.

This audit identifies **zero test files safe for bulk archival**. Tests should
move only with a deliberately retired feature. In particular, tests that
prove no identity, memory, governance, training, autonomy, transfer, or source
boundary mutation are part of the current safety case even if the feature
they guard is not shown in the hackathon demo.

The correct code-retention mechanism is Git history and a deliberate release
tag or source snapshot. The Great Library may later store a human-readable,
source-bound deprecation or release record that points to the commit. It should
not become an unstructured mirror of executable test trees.

## Finding 5: Documentation Needs Navigation More Than Deletion

The tracked documentation is only about 1.45 MB. Removing it provides almost
no disk or bundle benefit. The real issue is that current law, active
architecture, dated implementation checkpoints, research history, and draft
papers are presented at the same directory level.

### Keep prominent in Selene

- current project, identity, transfer, Vys, care, testing, teaching, and
  curriculum law;
- `README.md`, `PUBLIC_ARCHITECTURE_INDEX.md`, public-readiness and rights
  documents;
- `HACKATHON_COMPLETION_MAP_20260717.md` and the separate chronological
  hackathon workflow log;
- `SELENE_CURRENT_CAPABILITIES_20260717.md`;
- current comprehension, teaching-lifecycle, Answer Engine, and F1 curriculum
  checkpoints needed to explain implemented behavior;
- architecture records that source current code or public claims.

### Archive candidates after the demo path is frozen

These are categories, not authorization to move files:

- superseded `CURRENT_STATUS` or architecture-index snapshots;
- older May and June checkpoint documents whose conclusions are incorporated
  into current law or capability maps;
- intermediate paper outline, draft, and readable-draft stages after the final
  public artifact and its provenance chain are confirmed;
- phase-by-phase Answer Engine notes after a current consolidated architecture
  record links their commit ancestry;
- completed preparation dockets whose active decisions now live in code,
  current law, or an inspectable audit ledger.

The existing `docs/archive/` convention is still useful for repository-local
history. Moving a referenced document requires updating inbound links in the
same change. Deleting the source document after copying it elsewhere would
break repository-local provenance unless an index or source pointer remains.

## Finding 6: The Great Library Is Not a General Backup Destination

The Library Charter permits reusable, attributable project history and
implementation knowledge, but admission requires a stable record ID, admitted
sources, origin, consent basis, classification, allowed consumers, prohibited
uses, reviewer, authority basis, uncertainty, and correction status.

The current Vault freeze prohibits moving real private or sensitive payloads,
including private corpora, miner output, Cocoon records, personal memory, or a
catalog that exposes protected holdings. Such material must remain at its
existing separately governed location. The Library's `private-vault/` path is
only a boundary marker and cannot be used for safekeeping.

### Appropriate future Library proposals

- a Selene hackathon implementation ledger referencing exact Git commits;
- a generalized Test Impact Law implementation record;
- an Acquire -> Integrate -> Express architecture record;
- an Answer Engine confidence-separation and domain-adapter record;
- a repository-cleanup and reproducible-build lesson;
- reviewed architectural decisions and correction histories that are safe as
  shared knowledge.

### Inappropriate automatic accessions

- raw or derived private corpus payloads;
- miner outputs or inventories;
- personal or relational memory;
- live databases, Cocoon records, credentials, or local runtime state;
- whole code, test, or build trees merely because they are old;
- Selene identity or Vys material treated as Library authority;
- ambiguous files whose sensitivity or consent basis is unresolved.

Publication authority remains with Aleks. This audit creates no Library
proposal or record and does not interpret filesystem access as consent.

## Finding 7: The Vite Warning Requires Modularization, Not Repository Deletion

The frontend source is concentrated in:

- `src-ui/src/main.tsx`: approximately 506 kB;
- `src-ui/src/components.tsx`: approximately 67 kB; and
- the remaining frontend TypeScript: approximately 19 kB.

Most Cocoon panels are eagerly imported into one application entrypoint. This
produces the approximately 586 kB minified Vite bundle warning even when a tab
is not visible at startup.

Deleting old backend files, tests, documentation, build output, or ignored
corpora will not solve this warning. The proportional fix is to extract
tab-level components and lazy-load major areas such as Corpus, Evidence,
Vessel, Teaching, and diagnostics. That should be a separate behavior-
preserving frontend checkpoint with focused navigation and build checks.

## Recommended Hackathon Order

1. Checkpoint the current dirty implementation intentionally without including
   unrelated contextual work.
2. Freeze the judge-visible demo path and public/private boundary.
3. Review the 61.49 MB tracked metadata artifact for release necessity and
   privacy without exposing its contents.
4. Keep all backend modules and tests for the hackathon stabilization pass.
5. Add a concise documentation index rather than moving dozens of files before
   recording.
6. Apply only the existing guarded rebuildable-output cleanup if Aleks
   explicitly requests it and no immediate package test needs the outputs.
7. Split the Cocoon frontend only if startup or the bundle warning materially
   affects the hackathon path; otherwise defer it until the demo is frozen.
8. After submission, prepare itemized Great Library proposals for reusable
   implementation lessons and project history.
9. Archive superseded repository documents and any genuinely retired feature
   code only after link, import, schema, test, and provenance checks pass.

## Decision Table

| Material | Current decision |
| --- | --- |
| Rebuildable ignored build outputs | Safe cleanup candidates; deletion not yet authorized |
| Live backend modules | Keep; no unused module proven |
| Current 760-test suite | Keep; active regression and safety evidence |
| Current law and capability documents | Keep prominent |
| Historical checkpoints and draft chains | Organize/archive after demo freeze |
| Tracked 61.49 MB metadata trace | High-priority release/privacy review; do not auto-move |
| Private corpora, miner material, memory, Cocoon state | Excluded; Vault freeze prevents Library movement |
| Shared reusable architectural lessons | Eligible only as itemized Library proposals reviewed by Aleks |
| Vite bundle | Solve through frontend modularization, not file deletion |

## Verification Boundary

This was a static and metadata-only audit. It did not run Selene, probe her
conversation, alter her database, teach new material, or exercise stressful
behavior. No runtime verification was necessary because the audit changed no
runtime code.
