@echo off
title TrafficTwin AI - Launcher
echo ==========================================================
echo               TrafficTwin AI - Quick Start
echo ==========================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking environment...
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found in .venv.
    echo Please create it using: python -m venv .venv
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend dependencies...
    cd frontend && npm install && cd ..
)

echo [2/3] Launching FastAPI Backend (Port 8000)...
start "TrafficTwin AI - Backend [Port 8000]" cmd /k "cd /d ""%~dp0"" && .venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

echo [3/3] Launching Vite Frontend (Port 5173)...
start "TrafficTwin AI - Frontend [Port 5173]" cmd /k "cd /d ""%~dp0\frontend"" && npm run dev -- --host 127.0.0.1 --port 5173"

echo.
echo Waiting for servers to initialize...
timeout /t 3 /nobreak >nul

echo.
echo ==========================================================
echo TrafficTwin AI is now running!
echo.
echo   - Operator Dashboard:           http://localhost:5173/
echo   - Public Simulation Dashboard:  http://localhost:5173/public
echo   - Backend REST & OpenAPI Docs:  http://127.0.0.1:8000/docs
echo ==========================================================
echo.
echo Opening Operator Dashboard in default browser...
start http://localhost:5173/

echo.
echo To stop the servers later, run stop.bat or close the opened terminal windows.
echo Press any key to exit this launcher window.
pause >nul
