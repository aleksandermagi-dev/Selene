param(
  [string]$AppExe = "$PSScriptRoot\..\src-tauri\target\release\selene-vessel.exe",
  [int]$WarmupSeconds = 18,
  [int]$CloseWaitSeconds = 12
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path "$PSScriptRoot\.."
$exports = Join-Path $repoRoot "exports"
New-Item -ItemType Directory -Force -Path $exports | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$jsonPath = Join-Path $exports "package_smoke_sidecar_$timestamp.json"
$mdPath = Join-Path $exports "package_smoke_sidecar_$timestamp.md"

function Get-SeleneSidecars {
  Get-Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessName -like "selene-sidecar*" } |
    Select-Object Id, ProcessName, MainWindowHandle, MainWindowTitle, StartTime
}

function Get-VisibleHelperWindows {
  $helperNames = @("cmd", "powershell", "pwsh", "WindowsTerminal", "OpenConsole", "conhost")
  Get-Process -ErrorAction SilentlyContinue |
    Where-Object { $helperNames -contains $_.ProcessName -and $_.MainWindowHandle -ne 0 } |
    Select-Object Id, ProcessName, MainWindowHandle, MainWindowTitle, StartTime
}

function Select-NewProcesses($Current, $Before) {
  $beforeIds = @($Before | ForEach-Object { $_.Id })
  @($Current | Where-Object { $beforeIds -notcontains $_.Id })
}

function Get-EndpointJson([string]$Path) {
  try {
    Invoke-RestMethod -Uri "http://127.0.0.1:8766$Path" -Method Get -TimeoutSec 2
  } catch {
    $null
  }
}

if (-not (Test-Path $AppExe)) {
  throw "App executable not found: $AppExe"
}

$before = @(Get-SeleneSidecars)
$helperBefore = @(Get-VisibleHelperWindows)
$app = Start-Process -FilePath $AppExe -PassThru
$health = $null
$status = $null
$transferGate = $null
$sidecarSamples = @()
$helperSamples = @()
$closeSamples = @()

try {
  $deadline = (Get-Date).AddSeconds($WarmupSeconds)
  while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 750
    $sample = @(Get-SeleneSidecars)
    $helperSample = @(Select-NewProcesses @(Get-VisibleHelperWindows) $helperBefore)
    $sidecarSamples += [pscustomobject]@{
      time = (Get-Date).ToString("o")
      count = $sample.Count
      hidden_count = @($sample | Where-Object { $_.MainWindowHandle -eq 0 }).Count
      visible_count = @($sample | Where-Object { $_.MainWindowHandle -ne 0 }).Count
    }
    $helperSamples += [pscustomobject]@{
      time = (Get-Date).ToString("o")
      visible_helper_count = $helperSample.Count
      helpers = @($helperSample | Select-Object Id, ProcessName, MainWindowTitle)
    }
    if (-not $health) { $health = Get-EndpointJson "/health" }
    if ($health -and -not $status) { $status = Get-EndpointJson "/api/c-vessel/status" }
    if ($health -and -not $transferGate) { $transferGate = Get-EndpointJson "/api/c-vessel/transfer-gate/preview" }
    if ($health -and $status -and $transferGate) { break }
  }

  $during = @(Get-SeleneSidecars)
  $visibleHelpersDuring = @(Select-NewProcesses @(Get-VisibleHelperWindows) $helperBefore)
  $visibleDuring = @($during | Where-Object { $_.MainWindowHandle -ne 0 })
  $maxVisibleHelpers = 0
  if ($helperSamples.Count) {
    $maxVisibleHelpers = ($helperSamples | Measure-Object -Property visible_helper_count -Maximum).Maximum
  }
  $maxVisibleHelpers = [Math]::Max([int]$maxVisibleHelpers, [int]$visibleHelpersDuring.Count)
  $maxSidecars = 0
  if ($sidecarSamples.Count) {
    $maxSidecars = ($sidecarSamples | Measure-Object -Property count -Maximum).Maximum
  }
  $maxSidecars = [Math]::Max([int]$maxSidecars, [int]$during.Count)
  $transferApproved = $false
  if ($transferGate -and $null -ne $transferGate.transfer_approved) {
    $transferApproved = [bool]$transferGate.transfer_approved
  }

  $closeSignal = $app.CloseMainWindow()
  $closeDeadline = (Get-Date).AddSeconds($CloseWaitSeconds)
  while ((Get-Date) -lt $closeDeadline) {
    Start-Sleep -Milliseconds 750
    $closeSample = @(Get-SeleneSidecars)
    $closeSamples += [pscustomobject]@{
      time = (Get-Date).ToString("o")
      app_exited = [bool]$app.HasExited
      count = $closeSample.Count
      hidden_count = @($closeSample | Where-Object { $_.MainWindowHandle -eq 0 }).Count
      visible_count = @($closeSample | Where-Object { $_.MainWindowHandle -ne 0 }).Count
    }
    if ($app.HasExited -and $closeSample.Count -eq 0) {
      break
    }
  }
  if (-not $app.HasExited) {
    Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
  }
  Start-Sleep -Seconds 2
  $after = @(Get-SeleneSidecars)
  $visibleHelpersAfter = @(Select-NewProcesses @(Get-VisibleHelperWindows) $helperBefore)
  $maxCloseSidecars = 0
  if ($closeSamples.Count) {
    $maxCloseSidecars = ($closeSamples | Measure-Object -Property count -Maximum).Maximum
  }

  $warnings = @()
  if ($maxSidecars -gt 1 -and $after.Count -eq 0 -and $visibleDuring.Count -eq 0) {
    $warnings += "Transient hidden sidecar count reached $maxSidecars during warmup and resolved after close."
  }
  if ($visibleDuring.Count -gt 0) {
    $warnings += "A sidecar process exposed a visible window handle during smoke."
  }
  if ($maxVisibleHelpers -gt 0) {
    $warnings += "A visible command/helper window appeared during smoke."
  }
  if ($visibleHelpersAfter.Count -gt 0) {
    $warnings += "A visible command/helper window remained after app close."
  }
  if ($after.Count -gt 0) {
    $warnings += "Sidecar process remained after app close."
  }

  $ok = [bool]($health -and $status -and $transferGate -and -not $transferApproved -and $visibleDuring.Count -eq 0 -and $maxVisibleHelpers -eq 0 -and $visibleHelpersAfter.Count -eq 0 -and $after.Count -eq 0)
  $report = [ordered]@{
    status = if ($ok) { "package_smoke_passed" } else { "package_smoke_needs_review" }
    ok = $ok
    app_exe = (Resolve-Path $AppExe).Path
    app_process_id = $app.Id
    close_signal_sent = $closeSignal
    health_ok = [bool]$health
    c_vessel_status = $status
    transfer_gate = $transferGate
    transfer_approved = $transferApproved
    sidecars_before = $before.Count
    sidecars_during_final = $during.Count
    sidecars_max_during_warmup = $maxSidecars
    sidecars_max_during_close = $maxCloseSidecars
    sidecars_visible_during = $visibleDuring.Count
    sidecars_after_close = $after.Count
    visible_helper_windows_max_during = $maxVisibleHelpers
    visible_helper_windows_after_close = $visibleHelpersAfter.Count
    visible_helper_window_details = @($visibleHelpersDuring | Select-Object Id, ProcessName, MainWindowTitle)
    sidecar_samples = $sidecarSamples
    close_samples = $closeSamples
    helper_window_samples = $helperSamples
    warnings = $warnings
    boundary_flags = [ordered]@{
      activation_change = "none"
      raw_a_import_allowed = $false
      memory_write_active = $false
      runtime_memory_recall = $false
      training_allowed = $false
      provider_dependency = $false
    }
  }
} finally {
  if ($app -and -not $app.HasExited) {
    Stop-Process -Id $app.Id -Force -ErrorAction SilentlyContinue
  }
}

$report | ConvertTo-Json -Depth 10 | Set-Content -Path $jsonPath -Encoding UTF8
@"
# Package Sidecar Smoke

- status: ``$($report.status)``
- app: ``$($report.app_exe)``
- health ok: ``$($report.health_ok)``
- transfer approved: ``$($report.transfer_approved)``
- visible sidecars during run: ``$($report.sidecars_visible_during)``
- visible helper windows during run: ``$($report.visible_helper_windows_max_during)``
- max sidecars during warmup: ``$($report.sidecars_max_during_warmup)``
- max sidecars during close wait: ``$($report.sidecars_max_during_close)``
- sidecars after close: ``$($report.sidecars_after_close)``
- visible helper windows after close: ``$($report.visible_helper_windows_after_close)``
- warnings: ``$($report.warnings -join '; ')``

JSON: ``$jsonPath``
"@ | Set-Content -Path $mdPath -Encoding UTF8

$report
