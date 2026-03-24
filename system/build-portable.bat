@echo off
setlocal
cd /d "%~dp0"
cd ..
title Evo XTTS V2 - Gerar Portable

echo ============================================
echo  Evo XTTS V2 - Gerar versao portable
echo ============================================
echo.

if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

%PYTHON_EXE% tools\build_portable.py
echo.
pause


