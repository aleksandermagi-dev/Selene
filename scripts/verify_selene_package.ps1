param(
    [string]$InstalledExe = "",
    [string]$Installer = "",
    [int]$WarmupSeconds = 35,
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $Installer) {
    $Installer = Join-Path $repo "src-tauri\target\release\bundle\nsis\Selene_0.1.1_x64-setup.exe"
}

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

function Resolve-InstalledSeleneExe([string]$ExplicitPath) {
    $candidates = New-Object System.Collections.Generic.List[string]
    if ($ExplicitPath) {
        $candidates.Add($ExplicitPath)
    }
    $installDir = Join-Path $env:LOCALAPPDATA "Selene"
    $candidates.Add((Join-Path $installDir "selene-vessel.exe"))
    $candidates.Add((Join-Path $installDir "Selene.exe"))
    $productName = Get-TauriProductName
    if ($productName) {
        $candidates.Add((Join-Path $installDir "$productName.exe"))
    }
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }
    if ($ExplicitPath) {
        return $ExplicitPath
    }
    return (Join-Path $installDir "selene-vessel.exe")
}

function Get-EndpointJson([string]$Path) {
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:8766$Path" -Method Get -TimeoutSec 3
    } catch {
        $null
    }
}

function Get-Sidecars {
    @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like "selene-sidecar*" })
}

$startedProcess = $null
$launched = $false
$closedStartedApp = $false
$resolvedInstalledExe = Resolve-InstalledSeleneExe $InstalledExe
$health = Get-EndpointJson "/health"

if (-not $health -and -not $NoLaunch) {
    if (-not (Test-Path -LiteralPath $resolvedInstalledExe)) {
        throw "Installed Selene executable not found. Checked explicit path and LocalAppData Selene candidates; selected fallback: $resolvedInstalledExe"
    }
    $startedProcess = Start-Process -FilePath $resolvedInstalledExe -PassThru
    $launched = $true
    $deadline = (Get-Date).AddSeconds($WarmupSeconds)
    while ((Get-Date) -lt $deadline -and -not $health) {
        Start-Sleep -Milliseconds 750
        $health = Get-EndpointJson "/health"
    }
}

$construction = if ($health) { Get-EndpointJson "/api/vessel/construction/status" } else { $null }
$steps = if ($health) { Get-EndpointJson "/api/vessel/steps-1-8/status" } else { $null }
$reviewQueue = if ($health) { Get-EndpointJson "/api/vessel/review-queue?limit=5" } else { $null }
$mobileHealth = if ($health) { Get-EndpointJson "/api/mobile/health" } else { $null }
$transferGate = if ($health) { Get-EndpointJson "/api/c-vessel/transfer-gate/preview" } else { $null }

$transferApproved = $false
if ($transferGate -and $null -ne $transferGate.transfer_approved) {
    $transferApproved = [bool]$transferGate.transfer_approved
}

$ok = [bool](
    $health -and
    $construction -and
    $steps -and
    $reviewQueue -and
    $mobileHealth -and
    $transferGate -and
    -not $transferApproved
)

$warnings = @()
if (-not $health) { $warnings += "Health endpoint did not respond." }
if ($transferApproved) { $warnings += "Transfer gate reports transfer_approved=true; this violates the no-transfer checkpoint." }
if (-not $construction) { $warnings += "Construction status endpoint did not respond." }
if (-not $steps) { $warnings += "Steps 1-8 status endpoint did not respond." }
if (-not $reviewQueue) { $warnings += "Review queue endpoint did not respond." }
if (-not $mobileHealth) { $warnings += "Mobile chat health endpoint did not respond." }

$result = [ordered]@{
    status = if ($ok) { "selene_package_verify_passed" } else { "selene_package_verify_needs_review" }
    ok = $ok
    launched_installed_app = $launched
    closed_started_app = $false
    installed_exe_path = $resolvedInstalledExe
    installed_exe_last_write_time = if (Test-Path -LiteralPath $resolvedInstalledExe) { (Get-Item -LiteralPath $resolvedInstalledExe).LastWriteTimeUtc.ToString("o") } else { $null }
    installer_path = $Installer
    installer_size_bytes = if (Test-Path -LiteralPath $Installer) { [int64](Get-Item -LiteralPath $Installer).Length } else { 0 }
    sidecar_process_count = (Get-Sidecars).Count
    health_ok = [bool]$health
    sidecar_version = if ($health) { $health.sidecar_version } else { $null }
    startup = if ($health) { $health.startup } else { $null }
    my_office_readiness = [ordered]@{
        construction_status_ok = [bool]$construction
        steps_1_8_status_ok = [bool]$steps
        review_queue_ok = [bool]$reviewQueue
        mobile_chat_ok = [bool]$mobileHealth
    }
    mobile_health = $mobileHealth
    transfer_approved = $transferApproved
    transfer_gate = $transferGate
    warnings = $warnings
    boundary_flags = [ordered]@{
        activation_change = "none"
        transfer_approved = $false
        raw_a_import_allowed = $false
        memory_write_active = $false
        runtime_memory_recall = $false
        autonomous_action_allowed = $false
        self_replication_allowed = $false
    }
    verified_at = (Get-Date).ToUniversalTime().ToString("o")
}

if ($startedProcess) {
    try {
        $null = $startedProcess.CloseMainWindow()
        $startedProcess.WaitForExit(8000) | Out-Null
        if (-not $startedProcess.HasExited) {
            Stop-Process -Id $startedProcess.Id -Force -ErrorAction SilentlyContinue
            Start-Sleep -Milliseconds 500
            $startedProcess.Refresh()
        }
        $closedStartedApp = [bool]$startedProcess.HasExited
        $result["closed_started_app"] = $closedStartedApp
        if (-not $closedStartedApp) {
            $result["warnings"] += "Installed app process started for verification may still be running."
        }
    } catch {
        $result["warnings"] += "Could not close the installed app process started for verification: $($_.Exception.Message)"
    }
}

$exports = Join-Path $repo "exports"
New-Item -ItemType Directory -Force -Path $exports | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$jsonPath = Join-Path $exports "package_verify_$timestamp.json"
$result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $jsonPath -Encoding UTF8
$result["report_path"] = $jsonPath

$result | ConvertTo-Json -Depth 10
if (-not $ok) {
    exit 1
}
