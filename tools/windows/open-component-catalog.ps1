[CmdletBinding()]
param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 8080,
    [ValidateSet('Default', 'Firefox')]
    [string]$Browser = 'Default',
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
    if ($Browser -eq 'Firefox') {
        $firefox = Get-Command firefox.exe -ErrorAction SilentlyContinue
        if ($null -eq $firefox) {
            $firefoxCandidates = @()
            if (-not [string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
                $firefoxCandidates += Join-Path $env:ProgramFiles 'Mozilla Firefox\firefox.exe'
            }
            $programFilesX86 = [Environment]::GetEnvironmentVariable('ProgramFiles(x86)')
            if (-not [string]::IsNullOrWhiteSpace($programFilesX86)) {
                $firefoxCandidates += Join-Path $programFilesX86 'Mozilla Firefox\firefox.exe'
            }
            $firefoxCandidates = @($firefoxCandidates | Where-Object { Test-Path -LiteralPath $_ })

            if ($firefoxCandidates.Count -eq 0) {
                throw 'Firefox was not found. Install Firefox or run without -Browser Firefox.'
            }

            $firefoxPath = $firefoxCandidates[0]
        } else {
            $firefoxPath = $firefox.Source
        }

        Start-Process -FilePath $firefoxPath -ArgumentList $url
    } else {
        Start-Process $url
    }
}

& $python.Source @pythonArgs
