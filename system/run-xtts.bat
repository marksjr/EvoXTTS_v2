@echo off
setlocal
cd /d "%~dp0"
cd ..
title Evo XTTS V2 - Inicializando

echo ============================================
echo  Evo XTTS V2 - Iniciando
echo ============================================
echo.
echo A interface vai abrir no navegador automaticamente.
echo Para encerrar a API, feche esta janela.
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
    echo Falha ao iniciar a aplicacao.
    echo.
    echo Se estiver usando a versao normal, execute system\setup.bat primeiro.
    echo Se estiver usando a versao portable, verifique se a pasta runtime existe.
    echo.
)

pause


