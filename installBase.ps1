# Script version | Based on original weget installer (see: https://github.com/KRWCLASSIC/weget/blob/2407bb9dca90645af8df5dbe99ac1ca621a68d61/install/install_weget.ps1)
# Below variables are handled by external script that scrapes versions and edits these variables.
$scriptVersion = "v2.1"
$APP_NAME = " "
$APP_OWNER = ""
$APP_VERSION = ""
$APP_BINARY = ""
$APP_DISPLAYNAME = ""
$APP_FOLDER = ""
$APP_AUTORUN = $false
$APP_AUTORUN_PREFIX = ""
$APP_AUTORUN_ARGS = ""
Write-Host "$APP_DISPLAYNAME ($APP_VERSION) | IronShell installer $scriptVersion" -ForegroundColor Cyan

# Define installation path (user only)
$installPath = Join-Path $env:APPDATA "$APP_OWNER\$APP_FOLDER"
$binaryPath = Join-Path $installPath "$APP_BINARY"

# ISver file path
$isverPath = Join-Path $installPath "ISver.txt"

# Check if already installed in user path
$existingPaths = @($installPath) | Where-Object { Test-Path (Join-Path $_ "$APP_BINARY") }
if ($existingPaths) {
    Write-Host "$APP_DISPLAYNAME is already installed at: $($existingPaths -join ', ')" -ForegroundColor Yellow
    $installPath = $existingPaths
}

# Ensure install directory exists before download and ISver.txt write
if (!(Test-Path $installPath)) {
    Write-Host "Creating installation directory: $installPath" -ForegroundColor Green
    New-Item -ItemType Directory -Path $installPath -Force | Out-Null
}

# ISver version check
$skipInstall = $false
if (Test-Path $isverPath) {
    $installedVersion = (Get-Content $isverPath -Raw).Trim()
    $targetVersion = $APP_VERSION.Trim()
    if ($installedVersion -eq $targetVersion) {
        Write-Host "Existing installation is up to date ($installedVersion)." -ForegroundColor Green
        $skipInstall = $true
    } else {
        Write-Host "Installed version ($installedVersion) differs from requested ($targetVersion). Updating..." -ForegroundColor Yellow
    }
} else {
    Write-Host "No ISver.txt found. Will perform fresh installation of $APP_DISPLAYNAME ($APP_VERSION)." -ForegroundColor Yellow
}

if ($skipInstall) {
    if ($APP_AUTORUN -eq $true) {
        Write-Host "Press any key to continue... (autorun enabled)"
    } else {
        Write-Host "Press any key to continue..."
    }
    
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    
    if ($APP_AUTORUN -eq $true) {
        Write-Host "Autorun enabled. Running: "$APP_AUTORUN_PREFIX `"$binaryPath`" $APP_AUTORUN_ARGS"" -ForegroundColor Cyan
        if ($APP_AUTORUN_PREFIX -ne "") {
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "$APP_AUTORUN_PREFIX `"$binaryPath`" $APP_AUTORUN_ARGS"
        } else {
            if ($APP_AUTORUN_ARGS -ne "") {
                & $binaryPath $APP_AUTORUN_ARGS.Split(" ")
            } else {
                & $binaryPath
            }
        }
    }
    return
}

# Always download and install the binary if not skipping
$binaryUrl = "https://github.com/$APP_OWNER/$APP_NAME/releases/download/$APP_VERSION/$APP_BINARY"
Write-Host "Downloading $APP_DISPLAYNAME ($APP_VERSION) to: $binaryPath" -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $binaryUrl -OutFile $binaryPath -ErrorAction Stop
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 500) {
        Write-Host "GitHub returned 500. GitHub seems to be down." -ForegroundColor Red
    } else {
        Write-Host ("Failed to download " + $APP_DISPLAYNAME + ": " + $_) -ForegroundColor Red
    }
    Write-Host "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    return
}

# After download, check if binary exists
if (!(Test-Path $binaryPath)) {
    Write-Host "Download failed: $binaryPath does not exist." -ForegroundColor Red
    Write-Host "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    return
}

# Add to user PATH
$userEnvPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($userEnvPath -notlike "*$installPath*") {
    Write-Host "Adding to user PATH" -ForegroundColor Green
    [System.Environment]::SetEnvironmentVariable("Path", "$userEnvPath;$installPath", "User")
} else {
    Write-Host "Already in user PATH" -ForegroundColor Yellow
}

# Refresh PATH in current session
$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User")

# After successful install, write ISver.txt
Set-Content -Path $isverPath -Value $APP_VERSION.Trim()

# Only autorun and print success if binary exists
if (Test-Path $binaryPath) {
    Write-Host "Installation complete! $APP_DISPLAYNAME ($APP_VERSION) is ready to use." -ForegroundColor Green
} else {
    Write-Host "Binary not found for autorun or completion message. Something went wrong." -ForegroundColor Red
}

if ($APP_AUTORUN -eq $true) {
    Write-Host "Press any key to continue... (autorun enabled)"
} else {
    Write-Host "Press any key to continue..."
}

$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

if ($APP_AUTORUN -eq $true) {
    Write-Host "Autorun enabled. Running: "$APP_AUTORUN_PREFIX `"$binaryPath`" $APP_AUTORUN_ARGS"" -ForegroundColor Cyan
    if ($APP_AUTORUN_PREFIX -ne "") {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "$APP_AUTORUN_PREFIX `"$binaryPath`" $APP_AUTORUN_ARGS"
    } else {
        if ($APP_AUTORUN_ARGS -ne "") {
            & $binaryPath $APP_AUTORUN_ARGS.Split(" ")
        } else {
            & $binaryPath
        }
    }
}