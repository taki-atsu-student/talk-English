@echo off
REM run_backend.bat - Create venv, install deps, ensure .env, and start backend
REM Usage: Run from project root (double-click or from terminal)

SETLOCAL EnableDelayedExpansion
REM Root directory of this script
SET ROOT_DIR=%~dp0
REM Remove trailing backslash
IF "%ROOT_DIR:~-1%"=="\" SET ROOT_DIR=%ROOT_DIR:~0,-1%

REM Create virtualenv if missing
IF NOT EXIST "%ROOT_DIR%\.venv" (
    echo Creating virtual environment in %ROOT_DIR%\.venv ...
    python -m venv "%ROOT_DIR%\.venv"
)

REM Activate virtualenv
IF EXIST "%ROOT_DIR%\.venv\Scripts\activate.bat" (
    call "%ROOT_DIR%\.venv\Scripts\activate.bat"
) ELSE (
    echo WARNING: Could not find virtualenv activate script.
)

REM Install backend requirements if not already installed (quick check)
python -c "import pkgutil,sys; exit(0 if pkgutil.find_loader('fastapi') else 1)" 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Installing backend requirements...
    python -m pip install --upgrade pip
    python -m pip install -r "%ROOT_DIR%\backend\requirements.txt"
)

REM Ensure .env exists (copy from .env.example if present)
IF NOT EXIST "%ROOT_DIR%\.env" (
    IF EXIST "%ROOT_DIR%\.env.example" (
        echo Creating .env from .env.example
        copy "%ROOT_DIR%\.env.example" "%ROOT_DIR%\.env" >nul
    ) ELSE (
        echo NOTE: .env not found. Create .env with GROQ_API_KEY if needed.
    )
)

REM Change into backend and start server in a separate window
cd /d "%ROOT_DIR%\backend"
echo Starting backend on http://0.0.0.0:8000 ...
start "Talk English Backend" /min cmd /c "cd /d "%ROOT_DIR%\backend" && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM Give the server a moment to start and open the static UI in the default browser
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8000/static/index.html"

ENDLOCAL
