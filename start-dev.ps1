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

function Test-CommandExists {
    param([Parameter(Mandatory = $true)][string]$Name)

    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-PythonLauncher {
    param([Parameter(Mandatory = $true)][string]$ProjectDir)

    $venvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    if (Test-CommandExists -Name "py") {
        return "py"
    }

    if (Test-CommandExists -Name "python") {
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
    Write-Host "[Skip] Frontend folder open was skipped by parameter."
}
elseif ($DryRun) {
    Write-Host "[DryRun] Frontend folder to open: $frontendDir" -ForegroundColor Yellow
}
else {
    Start-Process -FilePath "explorer.exe" -ArgumentList $frontendDir | Out-Null
    Write-Host "Frontend folder opened." -ForegroundColor Green
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Open this folder in WeChat DevTools: $frontendDir"
Write-Host "2. Confirm utils/config.js points apiBaseUrl to http://127.0.0.1:8000"
Write-Host '3. For local debugging, open the health URL and expect {"status":"ok"}'
Write-Host ""
