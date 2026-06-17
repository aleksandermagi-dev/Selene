# Selene Repo Cleanup Map - 2026-06-12

## Purpose

This map separates source material from rebuildable output so the local workspace stays understandable before the next packaged app build.

## Keep

- `src/`, `src-ui/`, `src-tauri/src/`, `tests/`, `scripts/`, `docs/`, `README.md`, `package.json`, `package-lock.json`, `pyproject.toml`, `tsconfig.json`, and `vite.config.ts`.
- `DevelopmentalCorpusArchive_20260526_122541/`: preserved detached developmental corpus source material.
- `Ref material for codex/`: paper and reference intake material.
- `Project ABC/`: project boundary/reference material.
- `analysis/`: generated review and blueprint artifacts. These are large, but they are provenance-bearing project records unless explicitly regenerated or archived.

## Rebuildable Output

These can be deleted and recreated:

- `src-tauri/target/`: Rust/Tauri build output, app binaries, and old NSIS installers.
- `dist-sidecar/`: packaged sidecar executable output.
- `build-sidecar/` and `build/`: PyInstaller/package build intermediates.
- `dist-ui/` and `dist/`: frontend build output.
- `.pytest_cache/`, `scripts/__pycache__/`, and log files such as `selene_sidecar_dev.log` and `vite_dev.log`.

## What The Executables Mean

- `Selene_0.1.1_x64-setup.exe`: Windows installer produced by Tauri under `src-tauri/target/release/bundle/nsis/`.
- `selene-vessel.exe`: built Tauri app binary, useful for smoke tests but not the normal reinstall path.
- `selene-sidecar.exe` and `selene-sidecar-x86_64-pc-windows-msvc.exe`: local helper process binaries. The app launches and shuts these down; Aleks does not open them directly.

## Cleanup Commands

Dry run:

```powershell
npm run clean:check
```

Apply cleanup:

```powershell
npm run clean
```

Include `node_modules` only when a deeper dependency reset is desired:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/clean_workspace.ps1 -Apply -IncludeNodeModules
```

## Rebuild After Cleanup

For a fresh installer:

```powershell
npm run package:win
```

The current installer will appear under:

```text
src-tauri/target/release/bundle/nsis/
```
