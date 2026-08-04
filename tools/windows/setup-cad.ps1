[CmdletBinding()]
param(
    [switch]$Install,
    [string]$ExecutionRoot
)

$ErrorActionPreference = 'Stop'
$ExecutionRoot = if ($ExecutionRoot) { $ExecutionRoot } elseif ($env:FLAGPOLE_EXECUTION_ROOT) { $env:FLAGPOLE_EXECUTION_ROOT } else { Join-Path $env:USERPROFILE 'Documents\pesochnica\flagpole' }
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$manifest = Get-Content -LiteralPath (Join-Path $repoRoot 'tools\toolchain.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$sandboxRoot = [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE 'Documents\pesochnica')).TrimEnd('\')
$resolvedRoot = [IO.Path]::GetFullPath($ExecutionRoot).TrimEnd('\')
if (-not $resolvedRoot.StartsWith("$sandboxRoot\", [StringComparison]::OrdinalIgnoreCase)) {
    throw "ExecutionRoot must be a project folder below $sandboxRoot."
}
New-Item -ItemType Directory -Path $resolvedRoot -Force | Out-Null

function Find-CadExecutable {
    param([string]$Name)
    $candidates = if ($Name -eq 'FreeCAD') {
        @(
            (Join-Path $env:LOCALAPPDATA 'Programs\FreeCAD 1.1\bin\freecadcmd.exe'),
            (Join-Path $env:ProgramFiles 'FreeCAD 1.1\bin\freecadcmd.exe')
        )
    } else {
        @(
            (Join-Path $env:ProgramFiles 'OpenSCAD\openscad.exe'),
            (Join-Path $env:LOCALAPPDATA 'Programs\OpenSCAD\openscad.exe')
        )
    }
    return $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}

if ($Install) {
    $winget = (Get-Command winget -ErrorAction Stop).Source
    foreach ($package in $manifest.cad.windowsPackages) {
        if (Find-CadExecutable -Name ([string]$package.name)) {
            Write-Host "Already available: $($package.name)" -ForegroundColor DarkGreen
            continue
        }
        & $winget install --id ([string]$package.wingetId) --exact --source winget --accept-source-agreements --accept-package-agreements --silent --disable-interactivity
        if ($LASTEXITCODE -ne 0) { throw "winget failed to install $($package.name), code $LASTEXITCODE." }
    }
}

$venvRoot = Join-Path $resolvedRoot ([string]$manifest.cad.venvDirectory)
$venvPython = Join-Path $venvRoot 'Scripts\python.exe'
if ($Install -and -not (Test-Path -LiteralPath $venvPython)) {
    & py "-$($manifest.cad.pythonVersion)" -m venv $venvRoot
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create the build123d Python environment.' }
}
if ($Install) {
    & $venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'Failed to update pip in the build123d environment.' }
    & $venvPython -m pip install "build123d==$($manifest.cad.build123dVersion)" ([string]$manifest.cad.ocpPackage) ([string]$manifest.cad.glbPackage)
    if ($LASTEXITCODE -ne 0) { throw 'Failed to install build123d/OCP.' }
}

$freeCad = Find-CadExecutable -Name 'FreeCAD'
$openScad = Find-CadExecutable -Name 'OpenSCAD'
if (-not $freeCad) { throw 'FreeCAD executable not found. Run setup-cad.ps1 -Install.' }
if (-not $openScad) { throw 'OpenSCAD executable not found. Run setup-cad.ps1 -Install.' }
if (-not (Test-Path -LiteralPath $venvPython)) { throw 'build123d environment not found. Run setup-cad.ps1 -Install.' }
& $venvPython -c "import build123d, OCP, trimesh; assert build123d.__version__ == '$($manifest.cad.build123dVersion)'"
if ($LASTEXITCODE -ne 0) { throw 'build123d/OCP import check failed.' }

Write-Host "FreeCAD: $freeCad" -ForegroundColor Green
Write-Host "OpenSCAD: $openScad" -ForegroundColor Green
Write-Host "build123d/OCP: $venvPython" -ForegroundColor Green
