# Requires: PowerShell 7+, Python 3.13 venv at .\.venvEnvisionPerdido
# Purpose: Activate venv, load env vars, run health_check.py, and log output
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

try {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    $repoRoot = Resolve-Path (Join-Path $scriptRoot "..\..")
    Set-Location $repoRoot

    # Load env vars if present
    $envScript = Join-Path $scriptRoot "env.ps1"
    if (Test-Path $envScript) { . $envScript } else { Write-Host "env.ps1 not found; proceeding with current environment" }

    # Activate venv
    $activate = Join-Path $repoRoot ".venvEnvisionPerdido\Scripts\Activate.ps1"
    if (Test-Path $activate) { . $activate } else { Write-Warning "Virtual environment not found at $activate" }

    # Ensure logs dir exists
    $logDir = Join-Path $repoRoot "output\logs"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $logPath = Join-Path $logDir "healthcheck_$timestamp.log"

    "[$(Get-Date -Format o)] Starting health_check.py" | Tee-Object -FilePath $logPath -Append

    $python = "python"
    & $python "scripts\health_check.py" 2>&1 | Tee-Object -FilePath $logPath -Append

    "[$(Get-Date -Format o)] Finished health_check.py" | Tee-Object -FilePath $logPath -Append
}
catch {
    try {
        if (-not $logPath) {
            $fallbackDir = Join-Path $repoRoot "output\logs"
            New-Item -ItemType Directory -Force -Path $fallbackDir | Out-Null
            $logPath = Join-Path $fallbackDir ("healthcheck_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")
        }
        "[$(Get-Date -Format o)] ERROR: $($_.Exception.Message)" | Tee-Object -FilePath $logPath -Append
        "[$(Get-Date -Format o)] STACK: $($_.ScriptStackTrace)" | Tee-Object -FilePath $logPath -Append
    } catch {}
    throw
}