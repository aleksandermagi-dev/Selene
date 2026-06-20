$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$statusPath = Join-Path $repo "dist-sidecar\package-status.json"
$installer = Join-Path $repo "src-tauri\target\release\bundle\nsis\Selene_0.1.1_x64-setup.exe"
$releaseExe = Join-Path $repo "src-tauri\target\release\selene-vessel.exe"
$installedExe = "C:\Users\aleks\AppData\Local\Selene\selene-vessel.exe"

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
$status["release_exe_path"] = $releaseExe
$status["release_exe_size_bytes"] = if (Test-Path -LiteralPath $releaseExe) { [int64](Get-Item -LiteralPath $releaseExe).Length } else { 0 }
$status["installed_exe_path"] = $installedExe
$status["installed_exe_last_write_time"] = if (Test-Path -LiteralPath $installedExe) { (Get-Item -LiteralPath $installedExe).LastWriteTimeUtc.ToString("o") } else { $null }
$status["finalized_at"] = (Get-Date).ToUniversalTime().ToString("o")

New-Item -ItemType Directory -Path (Split-Path -Parent $statusPath) -Force | Out-Null
$status | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $statusPath -Encoding UTF8
$status | ConvertTo-Json -Depth 6
