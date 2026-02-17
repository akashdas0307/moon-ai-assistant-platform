@echo off
setlocal enabledelayedexpansion

:: ═══════════════════════════════════════════
::   Moon-AI Dev Launcher (Windows)
::   Usage: moon.bat [install|run|reload|stop]
:: ═══════════════════════════════════════════

set SCRIPT_DIR=%~dp0
set VENV_ACTIVATE=%SCRIPT_DIR%backend\venv\Scripts\activate.bat

if \"%1\"==\"install\"  goto :install
if \"%1\"==\"run\"      goto :run
if \"%1\"==\"reload\"   goto :reload
if \"%1\"==\"stop\"     goto :stop
goto :usage

:: ─── INSTALL ────────────────────────────────
:install
echo.
echo  [Moon-AI] Installing dependencies...
echo  --------------------------------------
echo.
echo  [1/2] Installing Python dependencies...
if not exist \"%VENV_ACTIVATE%\" (
  echo  WARNING: venv not found at backend\venv
  echo  Run: cd backend ^&^& python -m venv venv
  exit /b 1
)
call \"%VENV_ACTIVATE%\"
pip install -r \"%SCRIPT_DIR%backend\requirements.txt\"
echo.
echo  [2/2] Installing Node.js dependencies...
cd \"%SCRIPT_DIR%frontend\" && npm install
echo.
echo  Done! Run: moon.bat run
echo.
goto :end

:: ─── RUN ────────────────────────────────────
:run
echo.
echo  [Moon-AI] Starting services...
echo  --------------------------------------
echo  Backend  -- http://localhost:8000
echo  Frontend -- http://localhost:5173
echo  Close the opened windows to stop.
echo  --------------------------------------
echo.
if exist \"%VENV_ACTIVATE%\" call \"%VENV_ACTIVATE%\"
cd \"%SCRIPT_DIR%\"
start \"Moon-AI Backend\" cmd /k \"call %VENV_ACTIVATE% && uvicorn backend.main:app --reload --port 8000\"
cd \"%SCRIPT_DIR%frontend\"
start \"Moon-AI Frontend\" cmd /k \"npm run dev\"
goto :end

:: ─── STOP ────────────────────────────────────
:stop
echo.
echo  [Moon-AI] Stopping services...
for /f \"tokens=5\" %%a in ('netstat -aon ^| findstr \":8000 \"') do (
  taskkill /F /PID %%a >nul 2>&1
)
for /f \"tokens=5\" %%a in ('netstat -aon ^| findstr \":5173 \"') do (
  taskkill /F /PID %%a >nul 2>&1
)
echo  Backend and Frontend stopped.
echo.
goto :end

:: ─── RELOAD ──────────────────────────────────
:reload
echo.
echo  [Moon-AI] Reloading services...
echo  Stopping running services...
for /f \"tokens=5\" %%a in ('netstat -aon ^| findstr \":8000 \"') do (
  taskkill /F /PID %%a >nul 2>&1
)
for /f \"tokens=5\" %%a in ('netstat -aon ^| findstr \":5173 \"') do (
  taskkill /F /PID %%a >nul 2>&1
)
echo  Stopped. Restarting in 2 seconds...
timeout /t 2 /nobreak > nul
if exist \"%VENV_ACTIVATE%\" call \"%VENV_ACTIVATE%\"
cd \"%SCRIPT_DIR%\"
start \"Moon-AI Backend\" cmd /k \"call %VENV_ACTIVATE% && uvicorn backend.main:app --reload --port 8000\"
cd \"%SCRIPT_DIR%frontend\"
start \"Moon-AI Frontend\" cmd /k \"npm run dev\"
echo  Services restarted!
echo.
goto :end

:: ─── USAGE ───────────────────────────────────
:usage
echo.
echo  Moon-AI Dev Launcher
echo.
echo  Usage: moon.bat [command]
echo.
echo  Commands:
echo    install   Install all Python + Node.js dependencies
echo    run       Start backend + frontend services
echo    reload    Stop and restart all services
echo    stop      Stop all running services
echo.

:end
endlocal