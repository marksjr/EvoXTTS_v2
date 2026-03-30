@echo off
setlocal
cd /d "%~dp0"
cd ..
title Evo XTTS V2 - Starting

echo ============================================
echo  Evo XTTS V2 - Starting
echo ============================================
echo.
echo The interface will open in the browser automatically.
echo To stop the API, close this window.
echo.

if exist "runtime\Scripts\python.exe" (
    set "PYTHON_EXE=runtime\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

%PYTHON_EXE% system\start.py
if errorlevel 1 (
    echo.
    echo Failed to start the application.
    echo.
    echo If using the normal version, run install.bat first.
    echo If using the portable version, check that the runtime folder exists.
    echo.
)

pause
