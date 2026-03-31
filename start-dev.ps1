[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$NoOpenFrontend
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$backendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceDir = Split-Path -Parent $backendDir
$frontendDir = Join-Path $workspaceDir "wechat-miniprogram-game-front"
$healthUrl = "http://127.0.0.1:8000/api/health"
$adminUrl = "http://127.0.0.1:8000/admin"

function Test-CommandExists {
    param([Parameter(Mandatory = $true)][string]$Name)

    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Test-PythonLauncher {
    param([Parameter(Mandatory = $true)][string]$Launcher)

    try {
        & $Launcher --version *> $null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

function Get-PythonLauncher {
    param([Parameter(Mandatory = $true)][string]$ProjectDir)

    $venvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
    if ((Test-Path $venvPython) -and (Test-PythonLauncher -Launcher $venvPython)) {
        return $venvPython
    }

    $localPython = Join-Path $env:LOCALAPPDATA "Python\pythoncore-3.14-64\python.exe"
    if ((Test-Path $localPython) -and (Test-PythonLauncher -Launcher $localPython)) {
        return $localPython
    }

    if ((Test-CommandExists -Name "py") -and (Test-PythonLauncher -Launcher "py")) {
        return "py"
    }

    if ((Test-CommandExists -Name "python") -and (Test-PythonLauncher -Launcher "python")) {
        return "python"
    }

    throw "No Python launcher was found. Install Python or create .venv\\Scripts\\python.exe in the backend project."
}

function Wait-BackendHealth {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$RetryCount = 10,
        [int]$DelaySeconds = 1
    )

    for ($attempt = 1; $attempt -le $RetryCount; $attempt++) {
        try {
            $response = Invoke-RestMethod -Uri $Url -Method Get -TimeoutSec 2
            if ($response.status -eq "ok") {
                return $true
            }
        }
        catch {
            Start-Sleep -Seconds $DelaySeconds
        }
    }

    return $false
}

if (-not (Test-Path $backendDir)) {
    throw "Backend directory not found: $backendDir"
}

if (-not (Test-Path $frontendDir)) {
    throw "Frontend directory not found: $frontendDir"
}

$pythonLauncher = Get-PythonLauncher -ProjectDir $backendDir
$backendCommand = "& '$pythonLauncher' -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
$backendShellCommand = @(
    '$Host.UI.RawUI.WindowTitle = ''Wendao Backend'''
    "Set-Location '$backendDir'"
    '$env:PYTHONPATH = ''.vendor;.'''
    $backendCommand
) -join "; "

Write-Host ""
Write-Host "=== Wendao Local Dev Startup ===" -ForegroundColor Cyan
Write-Host "Backend: $backendDir"
Write-Host "Frontend: $frontendDir"
Write-Host "Health check: $healthUrl"
Write-Host "Admin console: $adminUrl"
Write-Host ""

if ($DryRun) {
    Write-Host "[DryRun] Backend command:" -ForegroundColor Yellow
    Write-Host $backendCommand
}
else {
    Start-Process -FilePath "powershell.exe" `
        -WorkingDirectory $backendDir `
        -ArgumentList @(
            "-NoExit",
            "-ExecutionPolicy", "Bypass",
            "-Command", $backendShellCommand
        ) | Out-Null

    $backendHealthy = Wait-BackendHealth -Url $healthUrl
    if ($backendHealthy) {
        Write-Host "Backend window started and health check passed." -ForegroundColor Green
    }
    else {
        Write-Host "Backend window started, but health check is not ready yet. Check the backend window logs." -ForegroundColor Yellow
    }
}

if ($NoOpenFrontend) {
    Write-Host "[Skip] Admin console open was skipped by parameter."
}
elseif ($DryRun) {
    Write-Host "[DryRun] Admin console page to open: $adminUrl" -ForegroundColor Yellow
}
else {
    Start-Process -FilePath $adminUrl | Out-Null
    Write-Host "Admin console page opened." -ForegroundColor Green
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Open this folder in WeChat DevTools: $frontendDir"
Write-Host "2. The admin console should open at $adminUrl"
Write-Host "3. Confirm utils/config.js points apiBaseUrl to http://127.0.0.1:8000"
Write-Host '4. For local debugging, open the health URL and expect {"status":"ok"}'
Write-Host ""
