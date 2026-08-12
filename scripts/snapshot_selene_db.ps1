param(
    [string]$DbPath = "",
    [string]$OutDir = "",
    [switch]$OpenFolder
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$localData = if ($env:SELENE_DATA_DIR) {
    [System.IO.Path]::GetFullPath((Resolve-Path -LiteralPath $env:SELENE_DATA_DIR).Path)
} else {
    Join-Path $env:LOCALAPPDATA "Selene\data"
}

$sourceDb = if ($DbPath) { $DbPath } else { Join-Path $localData "selene.sqlite3" }
$snapshotDir = if ($OutDir) { $OutDir } else { Join-Path $localData "db-inspection-snapshots" }

if (-not (Test-Path -LiteralPath $sourceDb)) {
    throw "Selene DB not found: $sourceDb"
}

New-Item -ItemType Directory -Force -Path $snapshotDir | Out-Null
$json = & python -m selene.continuity_backup create --db $sourceDb --out $snapshotDir
if ($LASTEXITCODE -ne 0) {
    throw "Continuity backup creation failed."
}
$result = $json | ConvertFrom-Json
$target = [string]$result.snapshot_path

if ($OpenFolder) {
    Start-Process -FilePath explorer.exe -ArgumentList "/select,`"$target`""
}

$result | ConvertTo-Json -Depth 8
