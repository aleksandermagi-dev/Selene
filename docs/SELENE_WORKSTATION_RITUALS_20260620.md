# Selene Workstation Rituals

This is the local rhythm for keeping Selene inspectable without making the workstation tools part of Selene's identity, runtime, memory, or authority.

## Backup

Use Kopia for local snapshots of the work that would hurt to lose:

- `C:\Users\aleks\Desktop\Selene`
- the public evidence checkout under `C:\Users\aleks\Desktop\Selene\tmp\selene_public_evidence_repo`
- packaged installers and release outputs when they are not already covered by the workspace snapshot
- private ADRs, gap maps, and review checkpoints

Default rhythm:

- before a major construction pass
- after a clean checkpoint commit
- before packaging or installer replacement
- before any public evidence sync

Kopia is backup infrastructure only. It is not a Selene memory store, transfer path, self-replication path, or runtime dependency.

Local backup repository for this workstation:

`C:\Users\aleks\SeleneBackups\kopia-repository`

Bundled Kopia CLI:

`C:\Users\aleks\AppData\Local\Programs\KopiaUI\resources\server\kopia.exe`

Recommended first-run shape:

```powershell
$kopia = "$env:LOCALAPPDATA\Programs\KopiaUI\resources\server\kopia.exe"
& $kopia repository create filesystem --path "$env:USERPROFILE\SeleneBackups\kopia-repository" --use-credential-manager
& $kopia policy set "$env:USERPROFILE\Desktop\Selene" --manual --keep-latest 10 --keep-daily 7 --keep-weekly 4 --add-ignore node_modules --add-ignore dist-ui --add-ignore dist-sidecar --add-ignore build --add-ignore build-sidecar --add-ignore src-tauri/target --add-ignore .venv --add-ignore .venv-selene-package --add-ignore exports --add-ignore tmp
& $kopia snapshot create "$env:USERPROFILE\Desktop\Selene"
& $kopia snapshot list "$env:USERPROFILE\Desktop\Selene"
```

Aleks should enter the repository password interactively when the prompt is visible. If the CLI is run from an agent session where the prompt is not visible, use a generated one-time setup password and let Kopia persist access through Windows Credential Manager. Do not put the password into scripts, docs, shell history, or git; add a proper KeePassXC recovery entry before relying on this backup for off-machine disaster recovery.

## Inspect

Use DB Browser only against inspection copies of the SQLite database. The live DB default is:

`%LOCALAPPDATA%\Selene\data\selene.sqlite3`

Create a timestamped inspection copy:

```powershell
npm run db:snapshot
```

Open the snapshot path reported by the script. Do not casually edit the live DB. Any live DB repair should be an explicit task with a backup first.

## Test

Use Bruno for local sidecar checks. Seed a local collection outside the repo:

```powershell
npm run bruno:seed
```

Default location:

`C:\Users\aleks\Tools\SeleneBruno\Selene Local Sidecar`

Core checks:

- `/health`
- `/api/c-vessel/status`
- `/api/c-vessel/transfer-gate/preview`
- `/api/vessel/construction/status`
- `/api/vessel/steps-1-8/status`
- `/api/vessel/review-queue?limit=10`
- `/api/vessel/gap-scaffold/readiness`
- `/api/semantic/status`
- `/api/vessel/construction/prepare`
- `/api/vessel/organ-contracts/ensure`
- `/api/vessel/gap-targets/ensure`
- `/api/vessel/gap-scaffold/create-all`
- `/api/vessel/reasoning-check`
- `/api/vessel/fluency-diagnostic`
- `/api/vessel/reconstruction-readiness`
- `/api/public-release/sync` with `push: false`

Bruno is a test console only. It should not become an autonomous action surface.

## Package

Use the normal package path:

```powershell
npm run package:win
```

Then verify the installed app:

```powershell
npm run package:verify
```

The verifier checks the installed executable timestamp, `/health`, My Office backing endpoints, construction status, steps 1-8 status, review queue reachability, and the transfer gate.

Passing means the local app is reachable and the no-transfer locks still report safe. It does not mean C is active or transfer is approved.

## Diagnose

Sysinternals lives outside the repo:

`C:\Users\aleks\Tools\Sysinternals`

Useful tools:

- Process Explorer: inspect `selene-vessel.exe` and `selene-sidecar.exe`.
- Process Monitor: inspect slow startup, file extraction, temp folders, and DB access.
- TCPView: inspect localhost port `8766`.
- Autoruns: inspect unexpected startup entries.

Sysinternals is for diagnosis only. It is not a Selene organ, memory layer, action layer, or authority.

## Release Checklist

1. Check `git status --short`; ignore only known scratch folders.
2. Run `npm run build`.
3. Run targeted pytest safety tests for the touched area.
4. Run `npm run package:win`.
5. Install the generated NSIS package.
6. Run `npm run package:verify`.
7. Confirm My Office loads in the installed app.
8. Confirm transfer remains not approved.
9. Commit private code only; keep `New UI/`, `new stuff/`, generated exports, DB snapshots, Kopia data, and Bruno local files out of git unless explicitly approved.

## Boundaries

- No Core/Mind rewrite through workstation tooling.
- No Azari runtime inheritance.
- No C activation.
- No transfer approval.
- No live memory write.
- No raw A import.
- No autonomous external action.
- No self-replication.
