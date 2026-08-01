[CmdletBinding()]
param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 8080,
    [switch]$NoBrowser
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$catalogPath = Join-Path $projectRoot 'catalog\catalog.html'

if (-not (Test-Path -LiteralPath $catalogPath)) {
    throw "Catalog not found: $catalogPath"
}

$python = Get-Command py -ErrorAction SilentlyContinue
$pythonArgs = @('-m', 'http.server', $Port, '--bind', '127.0.0.1', '--directory', $projectRoot)
if ($null -eq $python) {
    $python = Get-Command python -ErrorAction SilentlyContinue
}
if ($null -eq $python) {
    throw 'Python was not found (py or python). Run tools/windows/setup.ps1.'
}

$url = "http://127.0.0.1:$Port/catalog/catalog.html"
Write-Host "Catalog: $url"
Write-Host 'Stop server: Ctrl+C'

if (-not $NoBrowser) {
    Start-Process $url
}

& $python.Source @pythonArgs
