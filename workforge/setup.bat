@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %ERRORLEVEL%==0 (
  set "PY=py -3"
) else (
  where python >nul 2>&1
  if %ERRORLEVEL%==0 (
    set "PY=python"
  ) else (
    echo Python not found. Install Python 3.10+ and retry.
    exit /b 1
  )
)

echo Creating venv...
%PY% -m venv venv
if errorlevel 1 exit /b 1

echo Installing runtime dependencies...
call "%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip
call "%~dp0venv\Scripts\python.exe" -m pip install -r "%~dp0requirements-runtime.txt"
if errorlevel 1 exit /b 1

echo Done. Copy .env.example to src\.env if needed, then run run.bat
