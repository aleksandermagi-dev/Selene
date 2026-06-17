param(
    [switch]$Apply,
    [switch]$IncludeNodeModules
)

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$relativeTargets = @(
    ".pytest_cache",
    "build",
    "build-sidecar",
    "dist",
    "dist-sidecar",
    "dist-ui",
    "src-tauri\gen",
    "src-tauri\target",
    "scripts\__pycache__",
    "selene_sidecar.log",
    "selene_sidecar_dev.log",
    "vite_dev.log"
)

if ($IncludeNodeModules) {
    $relativeTargets += "node_modules"
}

function Assert-UnderRoot {
    param([string]$Path)

    $full = [System.IO.Path]::GetFullPath($Path)
    $rootWithSep = $root.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar

    if ($full -ne $root -and -not $full.StartsWith($rootWithSep, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clean outside workspace: $full"
    }

    return $full
}

$found = @()
foreach ($relative in $relativeTargets) {
    $candidate = Assert-UnderRoot (Join-Path $root $relative)
    if (Test-Path -LiteralPath $candidate) {
        $item = Get-Item -LiteralPath $candidate -Force
        $size = 0
        if ($item.PSIsContainer) {
            $size = (Get-ChildItem -LiteralPath $candidate -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
        } else {
            $size = $item.Length
        }
        $found += [PSCustomObject]@{
            Path = $candidate
            Type = if ($item.PSIsContainer) { "directory" } else { "file" }
            SizeMB = [math]::Round(($size / 1MB), 2)
        }
    }
}

if ($found.Count -eq 0) {
    Write-Host "Workspace is already clean."
    exit 0
}

$found | Sort-Object SizeMB -Descending | Format-Table -AutoSize

if (-not $Apply) {
    Write-Host ""
    Write-Host "Dry run only. Re-run with -Apply or npm run clean to remove these rebuildable outputs."
    exit 0
}

foreach ($target in $found) {
    Remove-Item -LiteralPath $target.Path -Recurse -Force
    Write-Host "Removed $($target.Path)"
}

Write-Host "Clean complete."
