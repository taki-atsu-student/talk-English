@echo off
rem Run this from the project root to set up the backend environment.
cd /d "%~dp0"
python backend/setup_device.py
pause
