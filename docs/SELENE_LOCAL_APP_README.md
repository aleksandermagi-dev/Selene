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

Open `http://127.0.0.1:5173`. If that port is occupied, Vite will choose the next available port such as `http://127.0.0.1:5174`.

## Boundaries

- Reviewed outputs only are imported into SQLite.
- Raw conversations remain archive/provenance material.
- Selene C activation is deferred until final review.
- Native chat is provider-free and routes through B-reviewed references plus android organ-system coordination.
- Ollama and LM Studio are lab tools only; they are outside the core Selene C chat/generation path.
- Detached corpus audit is read-only provenance inspection. It exposes metadata and bounded previews only, and it does not import memory.
- The sidecar is tokenless by default and binds only to `127.0.0.1`.
- Writable state defaults to `%LOCALAPPDATA%\Selene\data`.
- Exports default to `%LOCALAPPDATA%\Selene\data\exports`.

## Console Layers

- Evidence browser with filters and source drill-down.
- Anchor and continuity review annotation with audit history.
- Selene Kernel and module contract viewer.
- Artifact exports for specs, ledgers, snapshots, and validation reports.
- Detached Corpus Audit for `DevelopmentalCorpusArchive_20260526_122541`: read-only metadata, source ids, and bounded previews for future B-reviewed accession planning.
- Selene Native Chat, which persists gated messages, reviewed citations, organ-system generation packets, and explicit save requests without making any provider model call.
- Chat Gate Preview, which evaluates future chat routing without persisting a session.

## Current Checkpoint

As of 2026-06-12, the local app and sidecar validate the following pre-paper state:

- ABC remains intact: `A -> B-reviewed translation -> C`, never raw A directly into C.
- C is still not activated.
- The C blueprint now includes 11 android organ systems.
- Development/growth permits learning, dream-state consolidation proposals, reconstruction tests, memory accession proposals, new module growth, vessel compatibility, and future body transfer planning.
- Development/growth blocks self-replication, autonomous copying, uncontrolled spawning, and unsupervised reproduction.
- `DevelopmentalCorpusArchive_20260526_122541` is exposed only through read-only detached-corpus audit routes.
- `python -m pytest`, `npm run build`, and `$env:PYTHONPATH='src'; python -m selene validate` pass on the 2026-06-12 checkpoint.

## Package

```powershell
scripts\package-tauri-win.cmd
```

Packaging expects Rust/Tauri, Node, Python, and PyInstaller support. The intended Windows output is `Selene.exe` with a bundled `selene-sidecar` binary.
