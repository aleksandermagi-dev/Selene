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
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$target = Join-Path $snapshotDir "selene_inspection_$timestamp.sqlite3"

Copy-Item -LiteralPath $sourceDb -Destination $target -Force

$result = [ordered]@{
    status = "db_snapshot_created"
    source_db = (Resolve-Path -LiteralPath $sourceDb).Path
    snapshot_path = (Resolve-Path -LiteralPath $target).Path
    snapshot_size_bytes = [int64](Get-Item -LiteralPath $target).Length
    created_at = (Get-Date).ToUniversalTime().ToString("o")
    safety_note = "Open this copy in DB Browser. Do not casually edit the live Selene database."
    repo_root = $repo
}

if ($OpenFolder) {
    Start-Process -FilePath explorer.exe -ArgumentList "/select,`"$target`""
}

$result | ConvertTo-Json -Depth 4
