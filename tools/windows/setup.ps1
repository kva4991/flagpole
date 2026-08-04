[CmdletBinding()]
param(
    [switch]$Install,
    [switch]$AcceptAndroidLicenses,
    [string]$AndroidSdkRoot = (Join-Path $env:LOCALAPPDATA 'Android\Sdk'),
    [string]$ExecutionRoot
)

$ErrorActionPreference = 'Stop'
$ExecutionRoot = if ($ExecutionRoot) { $ExecutionRoot } elseif ($env:FLAGPOLE_EXECUTION_ROOT) { $env:FLAGPOLE_EXECUTION_ROOT } else { Join-Path $env:USERPROFILE 'Documents\pesochnica\flagpole' }
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$manifest = Get-Content -LiteralPath (Join-Path $repoRoot 'tools\toolchain.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$checkScript = Join-Path $PSScriptRoot 'check.ps1'

function Refresh-ProcessPath {
    $env:Path = (@(
        [Environment]::GetEnvironmentVariable('Path', 'Machine'),
        [Environment]::GetEnvironmentVariable('Path', 'User')
    ) | Where-Object { $_ }) -join ';'
}

function Add-UserPathEntry {
    param([string]$Path)
    if (-not $Path -or -not (Test-Path -LiteralPath $Path)) { return }
    $current = [Environment]::GetEnvironmentVariable('Path', 'User')
    $entries = @($current -split ';' | Where-Object { $_ })
    $normalized = $Path.TrimEnd('\')
    if (-not ($entries | Where-Object { $_.TrimEnd('\') -ieq $normalized })) {
        [Environment]::SetEnvironmentVariable('Path', (($entries + $Path) -join ';'), 'User')
    }
    if (-not (($env:Path -split ';') | Where-Object { $_.TrimEnd('\') -ieq $normalized })) {
        $env:Path = "$env:Path;$Path"
    }
}

function Set-UserVariable {
    param([string]$Name, [string]$Value)
    [Environment]::SetEnvironmentVariable($Name, $Value, 'User')
    Set-Item -Path "Env:$Name" -Value $Value
}

function Add-KnownPaths {
    foreach ($path in @(
        'C:\Program Files\Git\cmd',
        'C:\Program Files\Git\bin',
        'C:\Program Files\Git\usr\bin',
        'C:\Program Files\nodejs',
        (Join-Path $ExecutionRoot '.platformio\penv\Scripts'),
        (Join-Path $AndroidSdkRoot 'platform-tools'),
        (Join-Path $AndroidSdkRoot 'cmdline-tools\latest\bin')
    )) { Add-UserPathEntry $path }
    foreach ($root in @((Join-Path $env:ProgramFiles 'Eclipse Adoptium'), (Join-Path $env:ProgramFiles 'Java'))) {
        Get-ChildItem -LiteralPath $root -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -like 'jdk-17*' } |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1 |
            ForEach-Object { Add-UserPathEntry (Join-Path $_.FullName 'bin') }
    }
}

function Initialize-ExecutionRoot {
    $sandboxRoot = [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE 'Documents\pesochnica')).TrimEnd('\')
    $resolved = [IO.Path]::GetFullPath($ExecutionRoot).TrimEnd('\')
    if (-not $resolved.StartsWith("$sandboxRoot\", [StringComparison]::OrdinalIgnoreCase)) {
        throw "ExecutionRoot must be a project folder below $sandboxRoot."
    }
    foreach ($path in @(
        $resolved,
        (Join-Path $resolved 'artifacts'),
        (Join-Path $resolved 'logs'),
        (Join-Path $resolved '.platformio'),
        (Join-Path $resolved '.gradle')
    )) { New-Item -ItemType Directory -Path $path -Force | Out-Null }
    $script:ExecutionRoot = $resolved
    Set-UserVariable 'FLAGPOLE_EXECUTION_ROOT' $resolved
    Set-UserVariable 'PLATFORMIO_CORE_DIR' (Join-Path $resolved '.platformio')
    Set-UserVariable 'GRADLE_USER_HOME' (Join-Path $resolved '.gradle')
}

function Find-Winget {
    $command = Get-Command winget -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    $package = Get-AppxPackage -Name Microsoft.DesktopAppInstaller -ErrorAction SilentlyContinue |
        Sort-Object Version -Descending | Select-Object -First 1
    if ($package) {
        $candidate = Join-Path $package.InstallLocation 'winget.exe'
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    throw 'winget not found. Install Microsoft App Installer and retry.'
}

function Test-UsableCommand {
    param([object]$Package)
    $command = Get-Command ([string]$Package.command) -ErrorAction SilentlyContinue
    if (-not $command) { return $false }
    if ($Package.disallowedPathFragments) {
        foreach ($fragment in $Package.disallowedPathFragments) {
            if ($command.Source.IndexOf([string]$fragment, [StringComparison]::OrdinalIgnoreCase) -ge 0) { return $false }
        }
    }
    return $true
}

function Install-WindowsPackages {
    $winget = Find-Winget
    foreach ($package in $manifest.windowsPackages) {
        if (Test-UsableCommand $package) {
            Write-Host "Already available: $($package.name)" -ForegroundColor DarkGreen
            continue
        }
        Write-Host "Installing: $($package.name)" -ForegroundColor Cyan
        & $winget install --id $package.wingetId --exact --source winget --accept-source-agreements --accept-package-agreements --silent --disable-interactivity
        if ($LASTEXITCODE -ne 0) { throw "winget failed to install $($package.name), code $LASTEXITCODE." }
        Refresh-ProcessPath
        Add-KnownPaths
    }
}

function Configure-Java {
    $java = Get-Command java -ErrorAction SilentlyContinue
    if (-not $java) { throw 'java not found after JDK installation.' }
    $javaHome = Split-Path (Split-Path $java.Source -Parent) -Parent
    Set-UserVariable 'JAVA_HOME' $javaHome
    Add-UserPathEntry (Join-Path $javaHome 'bin')
}

function Configure-GitLfs {
    & git lfs install --skip-repo
    if ($LASTEXITCODE -ne 0) { throw 'Git LFS initialization failed.' }
}

function Install-AndroidCommandLineTools {
    $sdkManager = Join-Path $AndroidSdkRoot 'cmdline-tools\latest\bin\sdkmanager.bat'
    if (Test-Path -LiteralPath $sdkManager) { return $sdkManager }

    Write-Host 'Downloading Android command-line tools from the official repository...' -ForegroundColor Cyan
    [xml]$repository = (Invoke-WebRequest -UseBasicParsing -Uri ([string]$manifest.androidSdk.repositoryUrl)).Content
    $package = $repository.SelectSingleNode("//*[local-name()='remotePackage' and @path='cmdline-tools;latest']")
    $selected = $null
    foreach ($archive in $package.SelectNodes(".//*[local-name()='archive']")) {
        $hostNode = $archive.SelectSingleNode(".//*[local-name()='host-os']")
        if ($hostNode -and $hostNode.InnerText -eq 'windows') { $selected = $archive; break }
    }
    if (-not $selected) { throw 'Android command-line tools Windows archive not found.' }
    $urlNode = $selected.SelectSingleNode("./*[local-name()='complete']/*[local-name()='url']")
    $checksumNode = $selected.SelectSingleNode("./*[local-name()='complete']/*[local-name()='checksum']")
    $url = ([string]$manifest.androidSdk.archiveBaseUrl) + $urlNode.InnerText
    $cacheRoot = Join-Path $repoRoot 'tools\.cache\android-sdk'
    New-Item -ItemType Directory -Path $cacheRoot -Force | Out-Null
    $archivePath = Join-Path $cacheRoot ([IO.Path]::GetFileName($urlNode.InnerText))
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $archivePath
    $algorithm = if ($checksumNode.InnerText.Trim().Length -eq 64) { 'SHA256' } else { 'SHA1' }
    $actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm $algorithm).Hash.ToLowerInvariant()
    if ($actualHash -ne $checksumNode.InnerText.Trim().ToLowerInvariant()) { throw 'Android command-line tools checksum mismatch.' }
    $extractRoot = Join-Path $cacheRoot 'extract'
    if (Test-Path -LiteralPath $extractRoot) { Remove-Item -LiteralPath $extractRoot -Recurse -Force }
    Expand-Archive -LiteralPath $archivePath -DestinationPath $extractRoot -Force
    $target = Join-Path $AndroidSdkRoot 'cmdline-tools\latest'
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Copy-Item -Path (Join-Path $extractRoot 'cmdline-tools\*') -Destination $target -Recurse -Force
    if (-not (Test-Path -LiteralPath $sdkManager)) { throw 'sdkmanager missing after extraction.' }
    return $sdkManager
}

function Install-AndroidSdk {
    $resolved = [IO.Path]::GetFullPath($AndroidSdkRoot).TrimEnd('\')
    if ($resolved -ieq [IO.Path]::GetPathRoot($resolved).TrimEnd('\')) { throw 'AndroidSdkRoot cannot be a drive root.' }
    New-Item -ItemType Directory -Path $resolved -Force | Out-Null
    $sdkManager = Install-AndroidCommandLineTools
    Set-UserVariable 'ANDROID_HOME' $resolved
    Set-UserVariable 'ANDROID_SDK_ROOT' $resolved
    Add-UserPathEntry (Join-Path $resolved 'platform-tools')
    Add-UserPathEntry (Join-Path $resolved 'cmdline-tools\latest\bin')
    if (-not $AcceptAndroidLicenses) { throw 'Run again with -AcceptAndroidLicenses to install Android SDK.' }
    1..100 | ForEach-Object { 'y' } | & $sdkManager "--sdk_root=$resolved" --licenses | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'Android SDK license acceptance failed.' }
    & $sdkManager "--sdk_root=$resolved" @($manifest.androidSdk.packages | ForEach-Object { [string]$_ })
    if ($LASTEXITCODE -ne 0) { throw 'Android SDK component installation failed.' }
}

function Install-PlatformIO {
    $candidate = Join-Path $ExecutionRoot '.platformio\penv\Scripts\pio.exe'
    if (-not (Test-Path -LiteralPath $candidate)) {
        Write-Host 'Installing PlatformIO Core into an isolated environment...' -ForegroundColor Cyan
        $cacheRoot = Join-Path $repoRoot 'tools\.cache\platformio'
        New-Item -ItemType Directory -Path $cacheRoot -Force | Out-Null
        $installer = Join-Path $cacheRoot 'get-platformio.py'
        Invoke-WebRequest -UseBasicParsing -Uri ([string]$manifest.platformio.installerUrl) -OutFile $installer
        & python $installer
        if ($LASTEXITCODE -ne 0) { throw 'PlatformIO installer failed.' }
    }
    Add-UserPathEntry (Split-Path $candidate -Parent)
    if (-not (Test-Path -LiteralPath $candidate)) { throw 'PlatformIO was installed but pio.exe was not found.' }
}

function Install-MechanicalPythonEnvironment {
    $venvRoot = Join-Path $ExecutionRoot '.mechanical-venv'
    $venvPython = Join-Path $venvRoot 'Scripts\python.exe'
    $requirements = Join-Path $repoRoot 'mechanical\requirements.txt'
    if (-not (Test-Path -LiteralPath $venvPython)) {
        Write-Host 'Creating isolated mechanical Python environment...' -ForegroundColor Cyan
        & python -m venv $venvRoot
        if ($LASTEXITCODE -ne 0) { throw 'Failed to create the mechanical Python environment.' }
    }
    & $venvPython -m pip install --disable-pip-version-check --requirement $requirements
    if ($LASTEXITCODE -ne 0) { throw 'Failed to install mechanical Python dependencies.' }
    & $venvPython -c 'import matplotlib, networkx, numpy, resvg_py, skimage, trimesh'
    if ($LASTEXITCODE -ne 0) { throw 'Mechanical Python dependency import check failed.' }
}

function Sync-ExecutionWorktree {
    $target = Join-Path $ExecutionRoot 'worktree'
    $resolvedTarget = [IO.Path]::GetFullPath($target).TrimEnd('\')
    $resolvedRoot = [IO.Path]::GetFullPath($ExecutionRoot).TrimEnd('\')
    if (-not $resolvedTarget.StartsWith("$resolvedRoot\", [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Refusing to synchronize outside ExecutionRoot.'
    }
    New-Item -ItemType Directory -Path $resolvedTarget -Force | Out-Null
    Write-Host "Synchronizing disposable build copy: $resolvedTarget" -ForegroundColor Cyan
    & robocopy $repoRoot $resolvedTarget /E /PURGE /R:2 /W:2 /XD .git .gradle .kotlin .pio build node_modules .cache /XF .git *.log *.tmp | Out-Host
    if ($LASTEXITCODE -gt 7) { throw "robocopy failed with code $LASTEXITCODE." }
    return $resolvedTarget
}

function Warm-Toolchains {
    param([string]$BuildRoot)
    $wrapper = Join-Path (Join-Path $BuildRoot ([string]$manifest.androidProject)) 'gradlew.bat'
    & $wrapper --version
    if ($LASTEXITCODE -ne 0) { throw 'Gradle Wrapper failed.' }
    & $wrapper -p (Join-Path $BuildRoot ([string]$manifest.androidProject)) :app:assembleDebug --stacktrace
    if ($LASTEXITCODE -ne 0) { throw 'Android debug build failed.' }
    $apk = Join-Path (Join-Path $BuildRoot ([string]$manifest.androidProject)) 'app\build\outputs\apk\debug\app-debug.apk'
    if (-not (Test-Path -LiteralPath $apk)) { throw 'Android debug APK was not produced.' }
    Copy-Item -LiteralPath $apk -Destination (Join-Path $ExecutionRoot 'artifacts\crucian-control-debug.apk') -Force

    $pio = Join-Path $ExecutionRoot '.platformio\penv\Scripts\pio.exe'
    foreach ($project in $manifest.platformio.projects) {
        $projectRoot = Join-Path $BuildRoot ([string]$project)
        & $pio run --project-dir $projectRoot
        if ($LASTEXITCODE -ne 0) { throw "PlatformIO build failed: $project" }
        $environment = if ([string]$project -like '*esp32_c3_crucian_v06') { 'esp32-c3-devkitm-1' } else { 'esp32-c3-supermini-plus' }
        $firmware = Join-Path $projectRoot ".pio\build\$environment\firmware.bin"
        if (-not (Test-Path -LiteralPath $firmware)) { throw "Firmware artifact missing: $firmware" }
        $artifactName = if ([string]$project -like '*esp32_c3_crucian_v06') { 'crucian-v06-firmware.bin' } else { 'flag-light-legacy-firmware.bin' }
        Copy-Item -LiteralPath $firmware -Destination (Join-Path $ExecutionRoot "artifacts\$artifactName") -Force
    }
}

if (-not $Install) {
    & $checkScript -AndroidSdkRoot $AndroidSdkRoot -ExecutionRoot $ExecutionRoot
    exit $LASTEXITCODE
}

Refresh-ProcessPath
Initialize-ExecutionRoot
Add-KnownPaths
Install-WindowsPackages
Configure-GitLfs
Configure-Java
Install-AndroidSdk
Install-PlatformIO
Install-MechanicalPythonEnvironment
& (Join-Path $PSScriptRoot 'setup-cad.ps1') -Install -ExecutionRoot $ExecutionRoot
$buildRoot = Sync-ExecutionWorktree
Warm-Toolchains -BuildRoot $buildRoot
Write-Host ''
Write-Host 'Setup complete. Open a new PowerShell/Codex process to refresh PATH.' -ForegroundColor Green
& $checkScript -AndroidSdkRoot $AndroidSdkRoot -ExecutionRoot $ExecutionRoot
exit $LASTEXITCODE
