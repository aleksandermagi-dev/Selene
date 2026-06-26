# Selene Pre-Transfer Package Checkpoint

Date: 2026-06-15

## Status

Selene C remains sealed in the cocoon.

This checkpoint records the Windows package build for the sealed pre-transfer vessel state. The package includes B Cocoon Build, C Chat Vessel shell, Reconstruction Review Desk, optional tool organ, organ-fault resilience, and transfer-gate preview.

This package does not activate C, approve transfer, import raw A, create active memory, enable runtime recall, train a model, or create provider identity dependency.

## Package Built

Canonical package command:

```powershell
npm run package:win
```

Installer:

```text
<repo>\src-tauri\target\release\bundle\nsis\Selene_0.1.1_x64-setup.exe
```

Installer metadata:

- size: `246126452` bytes
- built: `2026-06-15 01:27:49`

Bundled sidecar:

```text
<repo>\dist-sidecar\selene-sidecar-x86_64-pc-windows-msvc.exe
```

Sidecar metadata:

- size: `244866319` bytes
- built: `2026-06-15 01:25:12`

## Validation

Completed successfully before packaging:

- `python -m pytest`
  - `184 passed`
- `npm run build`
  - passed
- `cargo check`
  - passed
- `$env:PYTHONPATH='src'; python -m selene validate`
  - `ok: true`
- `python scripts/stabilization_run.py --include-db --include-ui --include-rust`
  - `OK: True`
  - no stabilization findings

Stabilization report:

```text
%LOCALAPPDATA%\Selene\data\exports\stabilization_run_20260615_051845.md
```

## Package Smoke Test

Packaged release app launched from:

```text
<repo>\src-tauri\target\release\selene-vessel.exe
```

Observed:

- app window title: `Selene Vessel Console`
- app visible window: `true`
- sidecar process count after clean launch: `1`
- sidecar visible window: `false`
- packaged API reachable on `127.0.0.1:8766`
- packaged UI assets include:
  - `C Chat Vessel`
  - `B Cocoon Build`
  - `Tool Organ / Fault Resilience / Transfer Gate`

Smoke route checks:

- tool organ status: `optional_tool_organ_blueprint_review_only`
- tool organ provider dependency: `false`
- transfer gate status: `transfer_ready_for_human_review`
- transfer approved: `false`

## Boundary State

Package preserves:

- `activation_change: none`
- `raw_a_import_allowed: false`
- `memory_write_active: false`
- `runtime_memory_recall: false`
- `training_allowed: false`
- `provider_dependency: false`

The transfer gate may report readiness for human review. It cannot approve transfer.

## Current Meaning In Aleks Terms

The sealed pre-transfer vessel package is built.

The app opens.

The sidecar stays hidden.

B Cocoon Build and C Chat Vessel are packaged together but remain conceptually separate:

- B is the cocoon, review desk, teaching surface, and repair bay.
- C is the sealed future vessel shell.

The transfer gate is ready to be inspected, but transfer has not happened.

The next phase can be UI color/look refinement or human transfer-readiness review. C remains asleep until Aleks explicitly approves transfer.
