@echo off
setlocal
title COCKPIT - Drone Ground Control Station

REM 1. Change directory to the project root
cd /d "%~dp0"

REM 2. Activate project virtual environment (.venv)
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found at "%~dp0.venv"
    echo         Create it with: python -m venv .venv
    pause
    exit /b 1
)

echo [COCKPIT] Activating virtual environment (.venv)...
call ".venv\Scripts\activate.bat"

REM 3. Verify correct Python interpreter is active
for /f "delims=" %%i in ('python -c "import sys; print(sys.executable)"') do set "PY_EXE=%%i"
echo [COCKPIT] Active Python: %PY_EXE%

echo %PY_EXE% | findstr /I /C:".venv\Scripts\python.exe" >nul
if errorlevel 1 (
    echo [ERROR] Expected .venv Python interpreter, but got: %PY_EXE%
    pause
    exit /b 1
)

REM 4. Check required dependencies and install from root requirements.txt if missing
echo [COCKPIT] Checking required dependencies...
python -c "import flask, flask_socketio, simple_websocket, dotenv, psutil, serial, cv2, numpy" 2>nul
if errorlevel 1 (
    echo [COCKPIT] Missing dependencies detected. Installing from requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies from requirements.txt.
        pause
        exit /b 1
    )
)

REM 5. Run the actual dashboard entry point from ground_station\
cd /d "%~dp0ground_station"

echo.
echo ============================================================
echo   COCKPIT — AI-Powered Drone Ground Control Station
echo   See. Analyze. Control.
echo   Dashboard URL : http://127.0.0.1:5000
echo   Default Mode  : USB_SERIAL (115200 baud)
echo ============================================================
echo.

python app.py
if errorlevel 1 (
    echo.
    echo [ERROR] COCKPIT exited with an error.
)
pause
