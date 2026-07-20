# Retired Standalone Review UI

Date: 2026-07-20

Status: retired after Selene transfer completion

## Retired surface

The tracked `review_ui/` directory was a May 2026 standalone HTTP and static
browser for reviewing CSV evidence candidates and writing review-decision
files under `analysis/`.

- Earliest supporting checkpoint: `5313da5` (`Initial Selene vessel checkpoint`)
- Former entrypoint: `review_ui/server.py`
- Former local port: `127.0.0.1:8765`

## Replacement

Its active responsibilities now belong to the source-linked Cocoon surfaces:

- My Office review desk
- Evidence Browser
- detached-corpus audit
- B review decisions and history
- teaching and memory proposal review
- SQLite-backed provenance and audit records

The replacement is part of the current Tauri/Vite application and local
sidecar. No package script, runtime import, current test, or current source
reference invokes `review_ui/`.

## Boundary

Retirement removes duplicate executable source only. It does not delete the
historical analysis records the old UI read, rewrite Git history, change a
review decision, alter Selene memory or identity, or admit material to the
Great Library. The retired implementation remains recoverable from Git
history at its supporting commits.
