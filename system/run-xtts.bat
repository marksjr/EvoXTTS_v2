@echo off
setlocal EnableExtensions
cd /d "%~dp0"
cd ..
title Evo XTTS V2 - Starting

set "LOG_DIR=logs"
set "LOG_FILE=%LOG_DIR%\start.log"
set "PYTHON_EXE="

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
break > "%LOG_FILE%"

echo ============================================
echo  Evo XTTS V2 - Starting
echo ============================================
echo.
echo The interface will open in the browser automatically.
echo To stop the API, close this window.
echo Log: %CD%\%LOG_FILE%
echo.
>> "%LOG_FILE%" echo Starting Evo XTTS V2 from %CD%

if exist "runtime\python.exe" (
    set "PYTHON_EXE=runtime\python.exe"
) else if exist "runtime\Scripts\python.exe" (
    set "PYTHON_EXE=runtime\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Using Python: %PYTHON_EXE%
>> "%LOG_FILE%" echo Using Python: %PYTHON_EXE%

"%PYTHON_EXE%" system\start.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
    echo.
    echo Failed to start the application.
    echo.
    echo What to check:
    echo - run install.bat again and watch which install step fails
    echo - open %CD%\logs\install.log
    echo - open %CD%\%LOG_FILE%
    echo - if using the portable release, confirm the runtime folder exists
    echo.
    >> "%LOG_FILE%" echo Start failed.
)

pause
