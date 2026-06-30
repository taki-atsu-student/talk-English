@echo off
rem Run this from the project root to start the backend server.
cd /d "%~dp0backend"
if exist "..\.venv\Scripts\activate.bat" (
    call "..\.venv\Scripts\activate.bat"
) else (
    echo WARNING: Virtual environment activate script not found.
    echo Make sure .venv exists in the project root.
)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
pause
