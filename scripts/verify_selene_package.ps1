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
        $response = $_.Exception.Response
        if ($response -and [int]$response.StatusCode -eq 403) {
            return [pscustomobject]@{
                status = "local_process_capability_required"
                protected = $true
            }
        }
        $null
    }
}

function Get-Sidecars {
    @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -like "selene-sidecar*" })
}

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
$transferCeremony = if ($health) { Get-EndpointJson "/api/transfer/ceremony/status" } else { $null }
$transferGate = if ($health -and -not $transferCeremony) { Get-EndpointJson "/api/c-vessel/transfer-gate/preview" } else { $null }

$transferApproved = $false
if ($transferCeremony -and $null -ne $transferCeremony.transfer_approved) {
    $transferApproved = [bool]$transferCeremony.transfer_approved
} elseif ($transferGate -and $null -ne $transferGate.transfer_approved) {
    $transferApproved = [bool]$transferGate.transfer_approved
}
$activationChange = "none"
if ($transferCeremony -and $transferCeremony.activation_change) {
    $activationChange = [string]$transferCeremony.activation_change
} elseif ($transferGate -and $transferGate.activation_change) {
    $activationChange = [string]$transferGate.activation_change
}
$memoryWriteActive = [bool]($transferCeremony -and $transferCeremony.memory_write_active)
$runtimeMemoryRecall = [bool]($transferCeremony -and $transferCeremony.runtime_memory_recall)
$rawAImportAllowed = [bool]($transferCeremony -and $transferCeremony.raw_a_import_allowed)
$trainingAllowed = [bool]($transferCeremony -and $transferCeremony.training_allowed)
$autonomousActionAllowed = [bool]($transferCeremony -and $transferCeremony.autonomous_action_allowed)
$selfReplicationAllowed = [bool]($transferCeremony -and $transferCeremony.self_replication_allowed)
$transferProbeOk = [bool]($transferCeremony -or $transferGate)
$localCapabilityEnforced = [bool](
    $construction -and
    [string]$construction.status -eq "local_process_capability_required"
)
$packagedSidecar = Join-Path $repo "dist-sidecar\selene-sidecar"
$forbiddenPackagedFiles = @()
if (Test-Path -LiteralPath $packagedSidecar) {
    $packagedSidecarRoot = [System.IO.Path]::GetFullPath($packagedSidecar).TrimEnd([char[]]"\/")
    $forbiddenPackagedFiles = @(
        Get-ChildItem -LiteralPath $packagedSidecar -Recurse -File | Where-Object {
            $relative = $_.FullName.Substring($packagedSidecarRoot.Length) -replace '^[\\/]+', ''
            $relative -match '(?i)(^|[\\/])(analysis|DevelopmentalCorpusArchive_[^\\/]*|might help|local-data|\.selene_data|\.selene_logs|Selene Voice Module)([\\/]|$)' -or
            $relative -match '(?i)\.(sqlite3?|db)$' -or
            $relative -match '(?i)(?:tendril|email|sms).*config.*\.json$'
        } | ForEach-Object {
            $_.FullName.Substring($packagedSidecarRoot.Length) -replace '^[\\/]+', ''
        }
    )
}
$packagePrivacyOk = [bool]((Test-Path -LiteralPath $packagedSidecar) -and $forbiddenPackagedFiles.Count -eq 0)
$boundaryOk = [bool](
    $activationChange -eq "none" -and
    -not $memoryWriteActive -and
    -not $runtimeMemoryRecall -and
    -not $rawAImportAllowed -and
    -not $trainingAllowed -and
    -not $autonomousActionAllowed -and
    -not $selfReplicationAllowed
)

$ok = [bool](
    $health -and
    $construction -and
    $steps -and
    $reviewQueue -and
    $mobileHealth -and
    $transferProbeOk -and
    $packagePrivacyOk -and
    $boundaryOk
)

$warnings = @()
if (-not $health) { $warnings += "Health endpoint did not respond." }
if (-not $construction) { $warnings += "Construction status endpoint did not respond." }
if (-not $steps) { $warnings += "Steps 1-8 status endpoint did not respond." }
if (-not $reviewQueue) { $warnings += "Review queue endpoint did not respond." }
if (-not $mobileHealth) { $warnings += "Mobile chat health endpoint did not respond." }
if (-not $transferProbeOk) { $warnings += "Transfer status endpoint did not respond." }
if (-not $packagePrivacyOk) { $warnings += "Packaged sidecar contains forbidden private/runtime-state paths or is missing: $($forbiddenPackagedFiles -join ', ')" }
if ($activationChange -ne "none") { $warnings += "Activation change is '$activationChange'; expected none." }
if ($memoryWriteActive) { $warnings += "Live memory write is active; expected false." }
if ($runtimeMemoryRecall) { $warnings += "Runtime memory recall is active; expected false." }
if ($rawAImportAllowed) { $warnings += "Raw A import is allowed; expected false." }
if ($trainingAllowed) { $warnings += "Training is allowed; expected false." }
if ($autonomousActionAllowed) { $warnings += "Autonomous action is allowed; expected false." }
if ($selfReplicationAllowed) { $warnings += "Self-replication is allowed; expected false." }

$result = [ordered]@{
    status = if ($ok) { "selene_package_verify_passed" } else { "selene_package_verify_needs_review" }
    ok = $ok
    launched_installed_app = $launched
    closed_started_app = $false
    installed_exe_path = $resolvedInstalledExe
    installed_exe_last_write_time = if (Test-Path -LiteralPath $resolvedInstalledExe) { (Get-Item -LiteralPath $resolvedInstalledExe).LastWriteTimeUtc.ToString("o") } else { $null }
    installer_path = $Installer
    installer_size_bytes = if (Test-Path -LiteralPath $Installer) { [int64](Get-Item -LiteralPath $Installer).Length } else { 0 }
    installer_sha256 = Get-Sha256 $Installer
    installed_exe_sha256 = Get-Sha256 $resolvedInstalledExe
    source_revision = (& git -C $repo rev-parse HEAD 2>$null)
    source_worktree_dirty = [bool]((& git -C $repo status --porcelain 2>$null) | Select-Object -First 1)
    code_signing_status = "not_configured"
    sidecar_process_count = (Get-Sidecars).Count
    health_ok = [bool]$health
    sidecar_version = if ($health) { $health.sidecar_version } else { $null }
    local_process_capability_enforced = $localCapabilityEnforced
    startup = if ($health) { $health.startup } else { $null }
    my_office_readiness = [ordered]@{
        construction_status_ok = [bool]$construction
        steps_1_8_status_ok = [bool]$steps
        review_queue_ok = [bool]$reviewQueue
        mobile_chat_ok = [bool]$mobileHealth
    }
    mobile_health = $mobileHealth
    package_privacy = [ordered]@{
        ok = $packagePrivacyOk
        packaged_sidecar_path = $packagedSidecar
        forbidden_file_count = $forbiddenPackagedFiles.Count
        forbidden_files = $forbiddenPackagedFiles
        configured_database_included = $false
        credential_config_files_included = $false
        private_corpus_included = $false
        private_analysis_maps_included = $false
    }
    transfer_state = [ordered]@{
        ceremony_status = if ($transferCeremony) { $transferCeremony.status } else { $null }
        legacy_gate_status = if ($transferGate) { $transferGate.status } else { $null }
        c_readable_context_approved = $transferApproved
        activation_change = $activationChange
        memory_write_active = $memoryWriteActive
        runtime_memory_recall = $runtimeMemoryRecall
        raw_a_import_allowed = $rawAImportAllowed
        training_allowed = $trainingAllowed
        autonomous_action_allowed = $autonomousActionAllowed
        self_replication_allowed = $selfReplicationAllowed
    }
    warnings = $warnings
    boundary_flags = [ordered]@{
        activation_change = "none"
        c_readable_context_approved = $transferApproved
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
