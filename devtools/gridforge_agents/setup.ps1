$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$venvPath = Join-Path $repoRoot ".venv-gridforge-agents"
$pythonPath = Join-Path $venvPath "Scripts\python.exe"

$launcher = Get-Command py -ErrorAction SilentlyContinue
if ($launcher) {
    & py -3.10 -c "import sys; assert sys.version_info[:2] == (3, 10), sys.version"
    if ($LASTEXITCODE -ne 0) {
        throw "Python 3.10 is required. Install Python 3.10 and its py launcher."
    }
    if (-not (Test-Path $pythonPath)) {
        & py -3.10 -m venv $venvPath
        if ($LASTEXITCODE -ne 0) { throw "Could not create the local agent virtual environment." }
    }
}
else {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw "Python was not found. Install Python 3.10." }
    & python -c "import sys; assert sys.version_info[:2] == (3, 10), sys.version"
    if ($LASTEXITCODE -ne 0) { throw "The python command is not Python 3.10. Install/use the Python 3.10 launcher." }
    if (-not (Test-Path $pythonPath)) {
        & python -m venv $venvPath
        if ($LASTEXITCODE -ne 0) { throw "Could not create the local agent virtual environment." }
    }
}

if (-not (Test-Path $pythonPath)) {
    throw "The agent Python environment was not created at $pythonPath"
}

$env:PYTHONPATH = Join-Path $repoRoot "devtools"
& $pythonPath -m gridforge_agents --help
if ($LASTEXITCODE -ne 0) { throw "GridForge agent package could not be imported." }

Write-Host ""
Write-Host "GridForge local agent runtime installed."
Write-Host "Next: run the VS Code task 'GridForge Agents: Doctor'."
Write-Host "No GridForge application dependencies were installed or changed."
