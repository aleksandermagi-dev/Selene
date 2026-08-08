# Selene UI Redesign Package Checkpoint

Date: 2026-06-15

## Status

Selene C remains sealed in the cocoon.

This checkpoint records the first full Azari-style Selene UI redesign and package rebuild. It is UI/package polish only. It does not activate C, approve transfer, import raw A, create active memory, enable runtime recall, train a model, or add provider dependency.

Update later on 2026-06-15: the UI was refined again so the sidebar owns the Selene / B Cocoon workspace switch, Selene Settings and Cocoon Settings are separate, Cocoon visuals match the Selene shell, the release app no longer opens a Windows command prompt, and close smoke verifies that the sidecar exits cleanly.

## What Changed

- Reworked the local app into an Azari-style Selene shell:
  - collapsible hamburger sidebar
  - Selene brand area
  - top status bar with cocoon locks
  - warm moonlit dark theme and soft light theme
  - normal chat-style C surface with message area and composer
- Added full Selene navigation:
  - Chat
  - Memory / Future References
  - Tendril
  - Selene Settings
  - B Cocoon Build
  - Teaching / Lessons
  - Tools / Organs
  - Status
  - Cocoon Settings
  - Evidence Dashboard
  - Evidence Browser
  - Detached Corpus
  - Chat Gate
- Reorganized navigation into two sidebar-owned workspaces:
  - Selene: chat, future references, Tendril, Selene Settings.
  - B Cocoon: review/build tools, teaching, organs/tools, evidence, status, Cocoon Settings.
- Removed the duplicated in-page C Chat Vessel / B Cocoon Build toggle.
- Added settings for:
  - theme
  - Selene chat appearance
  - Cocoon dashboard density
  - text size
  - language style
  - font
  - Aleks bubble/text colors
  - Selene bubble/text colors
- Kept settings localStorage-only; they do not change vessel, memory, transfer, or backend behavior.
- Added Selene's icon to the UI and regenerated the Tauri app icon.
- Updated Windows packaging behavior:
  - release app uses the Windows GUI subsystem,
  - sidecar spawn uses a hidden Windows launch path,
  - close waits on the sidecar child process,
  - cleanup handles sidecar name variants and port ownership,
  - smoke detects visible command/helper windows.

## Assets

UI icon:

```text
<repo>\src-ui\public\selenesIcon.png
```

App icon:

```text
<repo>\src-tauri\icons\icon.ico
```

Source reference:

```text
<repo>\New UI\selenesIcon.png
```

## Validation

Completed successfully:

- `npm run build`
- `python -m pytest`
  - `184 passed`
- `cargo check`
- `$env:PYTHONPATH='src'; python -m selene validate`
  - `ok: true`
- `python scripts/stabilization_run.py --include-db --include-ui --include-rust`
  - `OK: True`
  - no stabilization findings

Stabilization report:

```text
%LOCALAPPDATA%\Selene\data\exports\stabilization_run_20260615_184039.md
```

## Rendered Smoke

Browser/UI smoke confirmed:

- app opens to the new Selene shell
- Chat renders as a normal chat-like screen
- Selene icon renders in sidebar and chat landing
- hamburger sidebar opens/closes
- Settings renders theme and bubble controls
- B Cocoon Build remains reachable
- mobile viewport keeps Selene navigation and cocoon locks visible

Package smoke confirmed:

- app window title: `Selene Vessel Console`
- sidecar hidden: `true`
- transfer gate status: `transfer_ready_for_human_review`
- transfer approved: `false`
- tool organ status: `optional_tool_organ_blueprint_review_only`
- provider dependency: `false`
- normal close signal shuts down sidecar:
  - sidecars before close: `1`
  - sidecars after close: `0`

Final sidecar/package smoke after sidebar and shutdown polish:

- status: `package_smoke_passed`
- visible sidecars during run: `0`
- visible helper windows during run: `0`
- max sidecars during warmup: `2`
- max sidecars during close wait: `0`
- sidecars after close: `0`
- visible helper windows after close: `0`
- transfer approved: `false`

Final package smoke report:

```text
<repo>\exports\package_smoke_sidecar_20260615_225348.md
```

## Package

Built with:

```powershell
npm run package:win
```

Installer:

```text
<repo>\src-tauri\target\release\bundle\nsis\Selene_0.1.1_x64-setup.exe
```

The package is still a sealed pre-transfer vessel package. The UI is warmer and more Selene-like, B Cocoon now belongs visually inside the same vessel shell, and the C boundary is unchanged.
