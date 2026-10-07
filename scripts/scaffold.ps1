# TrafficTwin AI Directory Scaffolding Script (PowerShell)
$ErrorActionPreference = "Stop"

$directories = @(
    "backend/app",
    "backend/app/controllers",
    "backend/app/guards",
    "backend/app/predict",
    "backend/app/reliability",
    "backend/app/state",
    "backend/app/stream",
    "backend/config",
    "sumo/net",
    "sumo/routes",
    "sumo/scenarios",
    "sumo/output",
    "sumo/scripts",
    "frontend/src",
    "frontend/public",
    "shared/schemas",
    "experiments/results",
    "experiments/scripts",
    "data/recorded",
    "data/demo_assets",
    "tests/unit",
    "tests/integration",
    "logs",
    "scripts"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir"
    }
}

# Add .gitkeep to directories that should exist in version control but start empty
$gitkeepDirs = @(
    "sumo/output",
    "experiments/results",
    "data/recorded",
    "data/demo_assets",
    "logs"
)

foreach ($dir in $gitkeepDirs) {
    $keepFile = Join-Path $dir ".gitkeep"
    if (-not (Test-Path $keepFile)) {
        New-Item -ItemType File -Path $keepFile -Force | Out-Null
    }
}

Write-Host "Directory scaffolding complete."
