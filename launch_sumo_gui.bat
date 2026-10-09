@echo off
title TrafficTwin AI - Launch SUMO Simulation GUI
echo ==========================================================
echo         TrafficTwin AI - SUMO Simulation GUI Launcher
echo ==========================================================
echo.
echo Select scenario to view in SUMO GUI:
echo   [1] Normal Daytime Traffic (corridor_normal.sumocfg)
echo   [2] Rush Hour Congestion (corridor_rush.sumocfg)
echo   [3] Blocked Downstream and Spillback (corridor_blocked_downstream.sumocfg)
echo   [4] Emergency Ambulance Preemption (corridor_ambulance.sumocfg)
echo   [5] Interactive Digital Twin Evaluator with TraCI (run_planner.py --gui)
echo.
set /p choice="Enter choice (1-5, default 1): "

if "%choice%"=="2" (
    echo Launching Rush Hour Congestion in SUMO GUI...
    start "" sumo-gui -c sumo/scenarios/corridor_rush.sumocfg --start
) else if "%choice%"=="3" (
    echo Launching Blocked Downstream in SUMO GUI...
    start "" sumo-gui -c sumo/scenarios/corridor_blocked_downstream.sumocfg --start
) else if "%choice%"=="4" (
    echo Launching Ambulance Preemption in SUMO GUI...
    start "" sumo-gui -c sumo/scenarios/corridor_ambulance.sumocfg --start
) else if "%choice%"=="5" (
    echo Launching Interactive Digital Twin Planner with TraCI in SUMO GUI...
    .venv\Scripts\python.exe experiments/run_planner.py --scenario rush --gui
) else (
    echo Launching Normal Arterial Traffic in SUMO GUI...
    start "" sumo-gui -c sumo/scenarios/corridor_normal.sumocfg --start
)

echo.
echo Simulation launched.
pause
