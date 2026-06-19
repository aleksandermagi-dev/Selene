$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$defaultAzariPython = "C:\Users\aleks\Desktop\Azari\.venv\Scripts\python.exe"
$python = if ($env:SELENE_MINILM_PYTHON) {
    $env:SELENE_MINILM_PYTHON
} elseif (Test-Path -LiteralPath $defaultAzariPython) {
    $defaultAzariPython
} else {
    "python"
}

Push-Location $repo
try {
    & $python -m PyInstaller selene_sidecar.spec --noconfirm --distpath dist-sidecar --workpath build-sidecar
    New-Item -ItemType Directory -Path "src-tauri\target\release" -Force | Out-Null
    Copy-Item -LiteralPath "dist-sidecar\selene-sidecar\selene-sidecar.exe" -Destination "src-tauri\target\release\selene-sidecar.exe" -Force -ErrorAction SilentlyContinue
} finally {
    Pop-Location
}
