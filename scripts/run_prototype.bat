@echo off
REM ==============================================================================
REM TrafficTwin AI - Hackathon Prototype Runner (Batch script)
REM Attribution: RoadwayVR/SUMO-Traffic-Simulator-Tutorial (MIT License)
REM ==============================================================================
title TrafficTwin AI - SUMO Prototype Runner
echo ==========================================================
echo   TrafficTwin AI - SUMO & Python/TraCI Prototype Runner
echo ==========================================================

cd /d "%~dp0\.."

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

python Traci4.py
pause
