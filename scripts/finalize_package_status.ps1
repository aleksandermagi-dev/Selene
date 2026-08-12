$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$statusPath = Join-Path $repo "dist-sidecar\package-status.json"
$installer = Join-Path $repo "src-tauri\target\release\bundle\nsis\Selene_0.1.1_x64-setup.exe"
$releaseExe = Join-Path $repo "src-tauri\target\release\selene-vessel.exe"

function Get-TauriProductName {
    $configPath = Join-Path $repo "src-tauri\tauri.conf.json"
    if (-not (Test-Path -LiteralPath $configPath)) {
        return $null
    }
    try {
        return (Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json).productName
    } catch {
        return $null
    }
}

function Resolve-InstalledSeleneExe {
    $installDir = Join-Path $env:LOCALAPPDATA "Selene"
    $candidates = @(
        (Join-Path $installDir "selene-vessel.exe"),
        (Join-Path $installDir "Selene.exe")
    )
    $productName = Get-TauriProductName
    if ($productName) {
        $candidates += (Join-Path $installDir "$productName.exe")
    }
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    return (Join-Path $installDir "selene-vessel.exe")
}

$installedExe = Resolve-InstalledSeleneExe
$gitRevision = (& git -C $repo rev-parse HEAD 2>$null)
$gitDirty = [bool]((& git -C $repo status --porcelain 2>$null) | Select-Object -First 1)

function Get-Sha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }
    $stream = [System.IO.File]::OpenRead($Path)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try {
        return (($sha.ComputeHash($stream) | ForEach-Object { $_.ToString("x2") }) -join "")
    } finally {
        $sha.Dispose()
        $stream.Dispose()
    }
}

$status = [ordered]@{}
if (Test-Path -LiteralPath $statusPath) {
    $existing = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
    foreach ($property in $existing.PSObject.Properties) {
        $status[$property.Name] = $property.Value
    }
}

$status["status"] = "windows_package_complete"
$status["installer_path"] = $installer
$status["installer_size_bytes"] = if (Test-Path -LiteralPath $installer) { [int64](Get-Item -LiteralPath $installer).Length } else { 0 }
$status["installer_sha256"] = Get-Sha256 $installer
$status["release_exe_path"] = $releaseExe
$status["release_exe_size_bytes"] = if (Test-Path -LiteralPath $releaseExe) { [int64](Get-Item -LiteralPath $releaseExe).Length } else { 0 }
$status["release_exe_sha256"] = Get-Sha256 $releaseExe
$status["installed_exe_path"] = $installedExe
$status["installed_exe_last_write_time"] = if (Test-Path -LiteralPath $installedExe) { (Get-Item -LiteralPath $installedExe).LastWriteTimeUtc.ToString("o") } else { $null }
$status["installed_exe_found"] = [bool](Test-Path -LiteralPath $installedExe)
$status["installed_exe_sha256"] = Get-Sha256 $installedExe
$status["source_revision"] = if ($gitRevision) { [string]$gitRevision } else { $null }
$status["source_worktree_dirty_at_build"] = $gitDirty
$status["code_signing_status"] = "not_configured"
$status["unsigned_artifact_warning"] = "Verify the published SHA-256 hash against this manifest. Code signing remains a separate release requirement."
$status["finalized_at"] = (Get-Date).ToUniversalTime().ToString("o")

New-Item -ItemType Directory -Path (Split-Path -Parent $statusPath) -Force | Out-Null
$status | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $statusPath -Encoding UTF8
$manifestPath = Join-Path $repo "dist-sidecar\release-provenance.json"
$status | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
$status["release_provenance_manifest"] = $manifestPath
$status | ConvertTo-Json -Depth 6
