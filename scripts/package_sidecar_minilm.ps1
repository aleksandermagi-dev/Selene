param(
    [ValidateSet("core", "semantic")]
    [string]$Mode = "core"
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$packageEnv = Join-Path $repo ".venv-selene-package\Scripts\python.exe"
$setupScript = Join-Path $repo "scripts\setup_selene_package_env.ps1"
$azariPython = "C:\Users\aleks\Desktop\Azari\.venv\Scripts\python.exe"
$startedAt = Get-Date
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

$python = if ($env:SELENE_PACKAGE_PYTHON) {
    $env:SELENE_PACKAGE_PYTHON
} else {
    $packageEnv
}

Push-Location $repo
try {
    if ((-not (Test-Path -LiteralPath $python)) -or $Mode -eq "semantic") {
        $setupArgs = @()
        if ($Mode -eq "semantic") {
            $setupArgs += "-Semantic"
        }
        & $setupScript @setupArgs
    }

    if (-not (Test-Path -LiteralPath $python)) {
        throw "Selene packaging Python was not found at $python. Run npm run package:env first."
    }

    $resolvedPython = (Resolve-Path -LiteralPath $python).Path
    $azariDetected = Test-Path -LiteralPath $azariPython
    $azariAvoided = $resolvedPython -ne $azariPython

    if (-not $azariAvoided) {
        throw "Refusing to package Selene with Azari's Python environment: $azariPython"
    }

    $env:SELENE_SIDECAR_MODE = $Mode
    & $resolvedPython -m PyInstaller selene_sidecar.spec --noconfirm --distpath dist-sidecar --workpath build-sidecar

    New-Item -ItemType Directory -Path "src-tauri\target\release" -Force | Out-Null
    Copy-Item -LiteralPath "dist-sidecar\selene-sidecar\selene-sidecar.exe" -Destination "src-tauri\target\release\selene-sidecar.exe" -Force -ErrorAction SilentlyContinue

    $sidecarDir = Join-Path $repo "dist-sidecar\selene-sidecar"
    $sidecarExe = Join-Path $sidecarDir "selene-sidecar.exe"
    $installer = Join-Path $repo "src-tauri\target\release\bundle\nsis\Selene_0.1.1_x64-setup.exe"
    $statusPath = Join-Path $repo "dist-sidecar\package-status.json"
    $sidecarSize = if (Test-Path -LiteralPath $sidecarDir) {
        (Get-ChildItem -LiteralPath $sidecarDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
    } else {
        0
    }
    $installerSize = if (Test-Path -LiteralPath $installer) {
        (Get-Item -LiteralPath $installer).Length
    } else {
        0
    }

    $stopwatch.Stop()
    $status = [ordered]@{
        status = "sidecar_package_complete"
        packaging_mode = $Mode
        python_executable = $resolvedPython
        selene_package_env = $packageEnv
        azari_env_detected = $azariDetected
        azari_env_avoided = $azariAvoided
        sidecar_dist_path = $sidecarDir
        sidecar_exe_path = $sidecarExe
        sidecar_size_bytes = [int64]$sidecarSize
        installer_path = $installer
        installer_size_bytes = [int64]$installerSize
        build_started_at = $startedAt.ToUniversalTime().ToString("o")
        build_finished_at = (Get-Date).ToUniversalTime().ToString("o")
        build_duration_seconds = [math]::Round($stopwatch.Elapsed.TotalSeconds, 2)
    }
    $status | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statusPath -Encoding UTF8
    $status | ConvertTo-Json -Depth 5
} finally {
    Remove-Item Env:\SELENE_SIDECAR_MODE -ErrorAction SilentlyContinue
    Pop-Location
}
