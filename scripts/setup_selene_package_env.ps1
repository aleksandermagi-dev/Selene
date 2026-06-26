param(
    [switch]$Semantic,
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$venvDir = Join-Path $repo ".venv-selene-package"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

Push-Location $repo
try {
    if (-not (Test-Path -LiteralPath $venvPython)) {
        $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
        $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
        $knownLocalPython = Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"
        $bootstrapPython = if ($Python) {
            $Python
        } elseif ($pyLauncher) {
            $pyLauncher.Source
        } elseif ($pythonCommand) {
            $pythonCommand.Source
        } elseif (Test-Path -LiteralPath $knownLocalPython) {
            $knownLocalPython
        } else {
            throw "No Python launcher found. Install Python 3.11+ or pass -Python to this script."
        }

        if ((Split-Path -Leaf $bootstrapPython) -ieq "py.exe") {
            & $bootstrapPython -3 -m venv $venvDir
        } else {
            & $bootstrapPython -m venv $venvDir
        }
    }

    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -e ".[packaging]"

    if ($Semantic) {
        & $venvPython -m pip install -e ".[semantic]"
    }

    $status = [ordered]@{
        status = "selene_package_env_ready"
        semantic_enabled = [bool]$Semantic
        python_executable = (Resolve-Path -LiteralPath $venvPython).Path
        env_path = (Resolve-Path -LiteralPath $venvDir).Path
        azari_reference_only = $true
        created_at = (Get-Date).ToUniversalTime().ToString("o")
    }
    $status | ConvertTo-Json -Depth 4
} finally {
    Pop-Location
}
