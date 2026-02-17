@echo off
setlocal enabledelayedexpansion

:: ═══════════════════════════════════════════
::   Moon-AI Dev Launcher (Windows)
::   Usage: moon.bat [install|run|reload|stop]
:: ═══════════════════════════════════════════

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%backend\venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_UVICORN=%VENV_DIR%\Scripts\uvicorn.exe"

if "%1"=="install" goto :install
if "%1"=="run"     goto :run
if "%1"=="reload"  goto :reload
if "%1"=="stop"    goto :stop
goto :usage

:: ── INSTALL ─────────────────────────────────────────────────
:install
echo.
echo   [Moon-AI] Setting up dependencies...
echo   ----------------------------------------

:: 1. Verify Python is available
python --version >nul 2>&1
if errorlevel 1 (
  echo   ERROR: Python is not installed or not in PATH.
  echo   Download from https://python.org
  exit /b 1
)

:: 2. Create venv automatically if missing
if not exist "%VENV_PYTHON%" (
  echo   Creating Python virtual environment...
  python -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo   ERROR: Failed to create venv. Check your Python installation.
    exit /b 1
  )
  echo   Virtual environment created.
) else (
  echo   Virtual environment found.
)

:: 3. Upgrade pip so it can handle new packages
echo   Upgrading pip...
"%VENV_PYTHON%" -m pip install --upgrade pip --quiet

:: 4. Install Python dependencies via the venv python directly (no activation needed)
echo   Installing Python packages...
"%VENV_PYTHON%" -m pip install -r "%SCRIPT_DIR%backend\requirements.txt"
if errorlevel 1 (
  echo.
  echo   ERROR: pip install failed. See errors above.
  exit /b 1
)

:: 5. Confirm uvicorn was installed
if not exist "%VENV_UVICORN%" (
  echo.
  echo   ERROR: uvicorn not found after install.
  echo   Try: "%VENV_PYTHON%" -m pip install uvicorn
  exit /b 1
)
echo   Python packages installed OK.

:: 6. Install Node.js dependencies
echo.
echo   Installing Node.js packages...
cd /d "%SCRIPT_DIR%frontend"
npm install
if errorlevel 1 (
  echo.
  echo   ERROR: npm install failed. Is Node.js installed?
  echo   Download from https://nodejs.org
  exit /b 1
)
echo   Node.js packages installed OK.

echo.
echo   ----------------------------------------
echo   All dependencies installed successfully.
echo   Run:  moon.bat run
echo   ----------------------------------------
echo.
goto :end

:: ── RUN ─────────────────────────────────────────────────────
:run
:: Auto-install if uvicorn is missing -- no manual step needed
if not exist "%VENV_UVICORN%" (
  echo.
  echo   [Auto] Dependencies not found. Running install first...
  echo.
  call "%~f0" install
  if errorlevel 1 (
    echo   ERROR: Auto-install failed. Fix errors above then retry.
    exit /b 1
  )
  echo.
)

echo.
echo   [Moon-AI] Starting services...
echo   ----------------------------------------
echo   Backend  -^> http://localhost:8000
echo   Frontend -^> http://localhost:5173
echo   Close the windows below to stop.
echo   ----------------------------------------
echo.

:: Start backend using the venv python.exe directly -- no PATH / activation issues
cd /d "%SCRIPT_DIR%"
start "Moon-AI Backend" cmd /k ""%VENV_PYTHON%" -m uvicorn backend.main:app --reload --port 8000"

:: Start frontend
cd /d "%SCRIPT_DIR%frontend"
start "Moon-AI Frontend" cmd /k "npm run dev"
goto :end

:: ── STOP ────────────────────────────────────────────────────
:stop
echo.
echo   [Moon-AI] Stopping services...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 " 2^>nul') do (
  taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173 " 2^>nul') do (
  taskkill /F /PID %%a >nul 2>&1
)
echo   Backend and Frontend stopped.
echo.
goto :end

:: ── RELOAD ──────────────────────────────────────────────────
:reload
echo.
echo   [Moon-AI] Reloading services...
call "%~f0" stop
timeout /t 2 /nobreak >nul
call "%~f0" run
goto :end

:: ── USAGE ───────────────────────────────────────────────────
:usage
echo.
echo   Moon-AI Dev Launcher
echo.
echo   Usage:  moon.bat [command]
echo.
echo   Commands:
echo     install   Install all Python + Node.js dependencies
echo     run       Start backend + frontend  (auto-installs if needed)
echo     reload    Stop and restart all services
echo     stop      Stop all running services
echo.

:end
endlocal
