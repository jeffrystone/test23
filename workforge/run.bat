@echo off
setlocal
cd /d "%~dp0"

if not exist "%~dp0venv\Scripts\python.exe" (
  echo venv not found. Run setup.bat first.
  exit /b 1
)

if not exist "%~dp0staticfiles\logs" mkdir "%~dp0staticfiles\logs"

set PYTHONPATH=%~dp0
"%~dp0venv\Scripts\python.exe" "%~dp0src\main.py"
