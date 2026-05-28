# Selene Local Vessel App

This scaffold creates the first Selene-native desktop vessel: a Tauri/React console backed by a tokenless localhost Python sidecar and SQLite registry.

## Run Locally

```powershell
python -m pip install -e .[dev]
python -m selene seed
python -m selene validate
python -m selene sidecar --seed --port 8766
```

In another terminal:

```powershell
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

## Boundaries

- Reviewed outputs only are imported into SQLite.
- Raw conversations remain archive/provenance material.
- Chat is deferred until the registry and gates validate.
- The sidecar is tokenless by default and binds only to `127.0.0.1`.
- Writable state defaults to `%LOCALAPPDATA%\Selene\data`.
- Exports default to `%LOCALAPPDATA%\Selene\data\exports`.

## Console Layers

- Evidence browser with filters and source drill-down.
- Anchor and continuity review annotation with audit history.
- Selene Kernel and module contract viewer.
- Artifact exports for specs, ledgers, snapshots, and validation reports.
- Chat readiness shell, which persists gated messages, reviewed citations, and explicit save requests without making any model call.
- Chat Gate Preview, which evaluates future chat routing without persisting a session.

## Package

```powershell
scripts\package-tauri-win.cmd
```

Packaging expects Rust/Tauri, Node, Python, and PyInstaller support. The intended Windows output is `Selene.exe` with a bundled `selene-sidecar` binary.
