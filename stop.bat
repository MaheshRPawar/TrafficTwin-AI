@echo off
title TrafficTwin AI - Stop Servers
echo ==========================================================
echo               TrafficTwin AI - Stopping Services
echo ==========================================================
echo.

echo Stopping services running on port 8000 and 5173...

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo All TrafficTwin AI background servers have been stopped.
echo.
pause
