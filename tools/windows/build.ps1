[CmdletBinding()]
param(
    [ValidateSet('all', 'generate', 'validate', 'catalog', 'ci', 'legacy-references')]
    [string]$Mode = 'all'
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$executionRoot = if ($env:FLAGPOLE_EXECUTION_ROOT) {
    $env:FLAGPOLE_EXECUTION_ROOT
} else {
    Join-Path $env:USERPROFILE 'Documents\pesochnica\flagpole'
}
$mechanicalPython = Join-Path $executionRoot '.mechanical-venv\Scripts\python.exe'
$cadPython = Join-Path $executionRoot '.venv-build123d\Scripts\python.exe'

if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'package.json'))) {
    throw "Project root was not found: $projectRoot"
}
if (-not (Test-Path -LiteralPath $mechanicalPython)) {
    throw "Mechanical Python was not found: $mechanicalPython. Run tools/windows/setup.ps1 -Install."
}
if (-not (Test-Path -LiteralPath $cadPython)) {
    throw "CAD Python was not found: $cadPython. Run tools/windows/setup-cad.ps1 -Install."
}
if ($projectRoot -notlike "$executionRoot\*") {
    throw "For antivirus-safe execution run this script from a synchronized worktree below $executionRoot."
}

$env:FLAGPOLE_PYTHON = $mechanicalPython
$env:FLAGPOLE_CAD_PYTHON = $cadPython
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

Push-Location $projectRoot
try {
    & node scripts/build.mjs $Mode
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}
