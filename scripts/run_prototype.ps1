# ==============================================================================
# TrafficTwin AI - Hackathon Prototype Runner
# Scenario: SUMO Simulation with Python/TraCI Traffic Signal Control
#
# Original Tutorial Source & Attribution:
#   Repository: RoadwayVR/SUMO-Traffic-Simulator-Tutorial
#   License: MIT License
#   Tutorial Focus: TraCI Traffic Light Preemption / Priority Controller
# ==============================================================================

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  TrafficTwin AI - SUMO & Python/TraCI Prototype Runner    " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Ensure SUMO_HOME is configured
if (-not $env:SUMO_HOME) {
    try {
        $detectedHome = python -c "import sumo; print(sumo.SUMO_HOME)" 2>$null
        if ($detectedHome) {
            $env:SUMO_HOME = $detectedHome.Trim()
            Write-Host "[+] Auto-detected SUMO_HOME: $env:SUMO_HOME" -ForegroundColor Green
        }
    } catch {
        Write-Warning "Could not auto-detect SUMO_HOME from python package."
    }
}

if ($env:SUMO_HOME) {
    $sumoBin = Join-Path $env:SUMO_HOME "bin"
    if ($env:PATH -notlike "*$sumoBin*") {
        $env:PATH = "$sumoBin;$env:PATH"
    }
}

# 2. Activate virtual environment if present
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$venvActivate = Join-Path $projectRoot "venv\Scripts\Activate.ps1"

if (Test-Path $venvActivate) {
    Write-Host "[+] Activating local virtual environment..." -ForegroundColor Green
    & $venvActivate
}

# 3. Set Working Directory to Project Root
Set-Location $projectRoot

Write-Host "[+] Starting TraCI Traffic Light Controller (Traci4.py)..." -ForegroundColor Yellow
Write-Host "    - Network: SUMOSample/Sample.net.xml (Junction J6 with 4-phase TLS)"
Write-Host "    - Controller: TraCI live state monitoring & preemption"
Write-Host "    - SUMO GUI will open automatically."
Write-Host "==========================================================" -ForegroundColor Cyan

python Traci4.py
