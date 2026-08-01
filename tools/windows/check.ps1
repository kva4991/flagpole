[CmdletBinding()]
param(
    [string]$AndroidSdkRoot = (Join-Path $env:LOCALAPPDATA 'Android\Sdk'),
    [string]$ExecutionRoot
)

$ErrorActionPreference = 'Stop'
$ExecutionRoot = if ($ExecutionRoot) { $ExecutionRoot } elseif ($env:FLAGPOLE_EXECUTION_ROOT) { $env:FLAGPOLE_EXECUTION_ROOT } else { Join-Path $env:USERPROFILE 'Documents\pesochnica\flagpole' }
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$manifest = Get-Content -LiteralPath (Join-Path $repoRoot 'tools\toolchain.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$rows = [System.Collections.Generic.List[object]]::new()
$missingRequired = 0

function Add-Result {
    param([string]$Status, [string]$Tool, [string]$Details, [bool]$Required = $true)
    $script:rows.Add([pscustomobject]@{ Status = $Status; Tool = $Tool; Details = $Details })
    if ($Required -and $Status -ne 'OK') { $script:missingRequired++ }
}

function Get-CommandLine {
    param([string]$Command, [string[]]$Arguments = @('--version'))
    $resolved = Get-Command $Command -ErrorAction SilentlyContinue
    if (-not $resolved) { return $null }
    try {
        $previousErrorAction = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $output = & $resolved.Source @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = $previousErrorAction
        if ($exitCode -ne 0) { return $null }
        $line = ($output | ForEach-Object { $_ -as [string] } | Where-Object { $_.Trim() } | Select-Object -First 1)
        return [pscustomobject]@{ Source = $resolved.Source; Text = $line.Trim() }
    }
    catch {
        $ErrorActionPreference = $previousErrorAction
        return $null
    }
}

function Test-VersionRequirement {
    param([object]$Package, [string]$Text)
    if (-not ($Package.minimumVersion -or $Package.requiredMajorVersion)) { return $true }
    $match = [regex]::Match($Text, '(\d+)(?:\.(\d+))?(?:\.(\d+))?')
    if (-not $match.Success) { return $false }
    $actual = [version]::new([int]$match.Groups[1].Value, $(if ($match.Groups[2].Success) { [int]$match.Groups[2].Value } else { 0 }), $(if ($match.Groups[3].Success) { [int]$match.Groups[3].Value } else { 0 }))
    if ($Package.requiredMajorVersion -and $actual.Major -ne [int]$Package.requiredMajorVersion) { return $false }
    if ($Package.minimumVersion -and $actual -lt [version]$Package.minimumVersion) { return $false }
    return $true
}

foreach ($package in $manifest.windowsPackages) {
    $arguments = if ($package.command -eq 'java') { @('-version') } elseif ($package.command -eq '7z') { @('i') } else { @('--version') }
    $result = Get-CommandLine -Command $package.command -Arguments $arguments
    $temporary = $false
    if ($result -and $package.disallowedPathFragments) {
        foreach ($fragment in $package.disallowedPathFragments) {
            if ($result.Source.IndexOf([string]$fragment, [StringComparison]::OrdinalIgnoreCase) -ge 0) { $temporary = $true }
        }
    }
    if (-not $result) {
        Add-Result 'MISSING' $package.name 'Command not found in PATH' ([bool]$package.required)
    }
    elseif ($temporary) {
        Add-Result 'MISSING' $package.name 'Only the temporary Codex copy was found' ([bool]$package.required)
    }
    elseif (-not (Test-VersionRequirement -Package $package -Text $result.Text)) {
        Add-Result 'WRONG' $package.name $result.Text ([bool]$package.required)
    }
    else { Add-Result 'OK' $package.name $result.Text ([bool]$package.required) }
}

$bash = Get-CommandLine -Command 'bash' -Arguments @('--version')
if ($bash) { Add-Result 'OK' 'Git Bash' $bash.Text } else { Add-Result 'MISSING' 'Git Bash' 'bash not found in PATH' }

$platformIoCandidates = @(
    (Join-Path $ExecutionRoot '.platformio\penv\Scripts\pio.exe'),
    (Join-Path $ExecutionRoot '.platformio\penv\Scripts\platformio.exe')
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -Unique
if ($platformIoCandidates) {
    $pio = $platformIoCandidates | Select-Object -First 1
    $version = (& $pio --version 2>&1 | Select-Object -First 1) -as [string]
    Add-Result 'OK' 'PlatformIO Core' "$version ($pio)"
}
else { Add-Result 'MISSING' 'PlatformIO Core' 'pio not found' }

$mechanicalPython = Join-Path $ExecutionRoot '.mechanical-venv\Scripts\python.exe'
if (Test-Path -LiteralPath $mechanicalPython) {
    & $mechanicalPython -c 'import matplotlib, networkx, numpy, resvg_py, skimage, trimesh' 2>$null
    if ($LASTEXITCODE -eq 0) { Add-Result 'OK' 'Mechanical Python environment' $mechanicalPython }
    else { Add-Result 'MISSING' 'Mechanical Python environment' 'Environment exists, but required imports fail' }
}
else { Add-Result 'MISSING' 'Mechanical Python environment' $mechanicalPython }

if (Test-Path -LiteralPath $ExecutionRoot) { Add-Result 'OK' 'Execution root' $ExecutionRoot }
else { Add-Result 'MISSING' 'Execution root' $ExecutionRoot }

$androidChecks = @(
    @('Android sdkmanager', (Join-Path $AndroidSdkRoot 'cmdline-tools\latest\bin\sdkmanager.bat')),
    @('Android Platform Tools', (Join-Path $AndroidSdkRoot 'platform-tools\adb.exe')),
    @('Android Platform 35', (Join-Path $AndroidSdkRoot 'platforms\android-35\android.jar')),
    @('Android Build Tools 35.0.0', (Join-Path $AndroidSdkRoot 'build-tools\35.0.0\aapt2.exe'))
)
foreach ($check in $androidChecks) {
    if (Test-Path -LiteralPath $check[1]) { Add-Result 'OK' $check[0] $check[1] }
    else { Add-Result 'MISSING' $check[0] $check[1] }
}

$androidRoot = Join-Path $repoRoot ([string]$manifest.androidProject)
$wrapper = Join-Path $androidRoot 'gradlew.bat'
$wrapperJar = Join-Path $androidRoot 'gradle\wrapper\gradle-wrapper.jar'
if ((Test-Path -LiteralPath $wrapper) -and (Test-Path -LiteralPath $wrapperJar)) {
    Add-Result 'OK' 'Gradle Wrapper' $wrapper
}
else { Add-Result 'MISSING' 'Gradle Wrapper' 'gradlew.bat or gradle-wrapper.jar is missing' }

Write-Host ''
Write-Host 'Crucian Windows toolchain'
$rows | Format-Table -AutoSize -Wrap
Write-Host ''
if ($missingRequired -gt 0) {
    Write-Host "Missing required components: $missingRequired." -ForegroundColor Yellow
    Write-Host 'Run tools\windows\setup.ps1 -Install -AcceptAndroidLicenses.'
    exit 1
}
Write-Host 'All required components are ready.' -ForegroundColor Green
exit 0
