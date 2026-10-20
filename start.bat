@echo off
title Islamic Note-taking & Collaboration App Launcher
echo =====================================================
echo  Starting Islamic Note-taking ^& Collaboration App... 
echo =====================================================

:: 1. Start backend server
echo Starting Backend API (FastAPI) on port 8000...
start /B cmd /c "cd backend && call venv\Scripts\activate && python -m uvicorn app.main:app --port 8000 > backend.log 2>&1"

:: 2. Start frontend server
echo Starting Frontend UI (SvelteKit) on port 5173...
start /B cmd /c "cd frontend && npm run dev -- --port 5173 > frontend.log 2>&1"

:: Wait for servers to spin up
timeout /t 4 /nobreak > nul

:: 3. Open browser
echo Launching default web browser...
start http://localhost:5173

echo.
echo Application is running.
echo To close, close this command prompt window.
echo =====================================================
pause > nul
