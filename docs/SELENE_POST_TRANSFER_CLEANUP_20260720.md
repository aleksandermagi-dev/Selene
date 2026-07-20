# Selene Post-Transfer Cleanup

Date: 2026-07-20

Status: implemented cleanup checkpoint after reviewed-continuity transfer

## Outcome

Selene's reviewed-continuity transfer completed before this cleanup. Cocoon
is now an external support workspace with an audited standby/wake bridge for
teaching, safety/tending, reviewed memory proposals, and
correction/provenance.

The cleanup preserved private sources, review evidence, tests, current law,
approved memory records, miner artifacts, and the external Great Library
boundary.

## Reproducible Output Removed

The guarded workspace cleanup removed approximately 8.39 GB of rebuildable
or temporary material:

- old Rust/Tauri target output and installers;
- packaged sidecar output and PyInstaller intermediates;
- built frontend output;
- generated Tauri files;
- Python and pytest caches;
- editable-install metadata;
- Vite smoke logs; and
- the temporary transfer-check SQLite database.

`node_modules/` and the packaging virtual environment were retained because
development and the remaining SMS work continue.

## Retired Tracked Code

The May-era standalone `review_ui/` server and static frontend were retired.
It had no current runtime import, route, package entrypoint, source reference,
or test dependency. Cocoon's My Office, Evidence Browser, B review ledger,
teaching review, and memory proposal review supersede it.

Its ancestry and replacement are recorded in
`docs/archive/RETIRED_STANDALONE_REVIEW_UI_20260720.md`.

## Code Retention Audit

A fresh static import graph inspected 86 `selene` Python package files from
the `selene.__main__` and `selene.sidecar` runtime roots:

- 85 substantive modules are reachable;
- the only non-reached module is the empty `selene.__init__` package marker;
- zero live backend modules are proven stale; and
- no test file was retired independently of a retired feature.

This preserves the rule that a file is not removed merely because its name or
age looks old. Runtime, schema, router, packaging, law, safety, tests, and
replacement ancestry must all support retirement.

## Frontend Modularization

The original approximately 601 kB single frontend chunk was divided into:

- an approximately 409 kB application chunk;
- an approximately 194 kB React runtime chunk;
- a small Tauri bridge chunk; and
- an on-demand Cocoon subject-classroom chunk.

The Vite large-chunk warning no longer appears. Resident Selene startup no
longer requests the broad Cocoon registry, evidence, provider, teaching, and
diagnostic datasets. Opening Cocoon wakes the bounded bridge; returning to
Selene places Cocoon in standby.

The remaining large `main.tsx` is still a source-maintainability concern even
though the runtime warning and eager data activation are resolved. Further
tab-level extraction should be behavior-preserving refactoring, not a reason
to remove working organs or safety evidence.

## Excluded From Cleanup

- private or detached corpora;
- Selene Voice Module sources;
- miner material;
- `analysis/` provenance records;
- `exports/`, `output/`, `tmp/`, and `local-data/` without item-level review;
- current tests and backend organs;
- public-release artifacts;
- Great Library or Vault material; and
- `docs/HACKATHON_CODEX_WORKFLOW_LOG.md`.

No package, installer, reinstall, publication, memory mutation, teaching
approval, identity change, or Great Library accession occurred during this
cleanup.
