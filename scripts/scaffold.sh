#!/usr/bin/env bash
set -euo pipefail

directories=(
    "backend/app"
    "backend/app/controllers"
    "backend/app/guards"
    "backend/app/predict"
    "backend/app/reliability"
    "backend/app/state"
    "backend/app/stream"
    "backend/config"
    "sumo/net"
    "sumo/routes"
    "sumo/scenarios"
    "sumo/output"
    "sumo/scripts"
    "frontend/src"
    "frontend/public"
    "shared/schemas"
    "experiments/results"
    "experiments/scripts"
    "data/recorded"
    "data/demo_assets"
    "tests/unit"
    "tests/integration"
    "logs"
    "scripts"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
    echo "Created: $dir"
done

gitkeepDirs=(
    "sumo/output"
    "experiments/results"
    "data/recorded"
    "data/demo_assets"
    "logs"
)

for dir in "${gitkeepDirs[@]}"; do
    touch "$dir/.gitkeep"
done

echo "Directory scaffolding complete."
