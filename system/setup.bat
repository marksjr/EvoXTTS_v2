@echo off
setlocal
cd /d "%~dp0"
cd ..
title Evo XTTS V2 - Installer

echo ============================================
echo  Evo XTTS V2 - Windows Installer
echo ============================================
echo.

set "PYTHON_EXE="
set "SYSTEM_PYTHON_EXE="

if exist "runtime\python.exe" (
    set "PYTHON_EXE=runtime\python.exe"
    echo Using existing portable Python runtime.
) else if exist "runtime\Scripts\python.exe" (
    set "PYTHON_EXE=runtime\Scripts\python.exe"
    echo Using existing portable Python runtime.
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
    echo Using existing virtual environment.
) else (
    call :detect_system_python
    if defined SYSTEM_PYTHON_EXE (
        echo System Python detected: %SYSTEM_PYTHON_EXE%
        echo Creating local virtual environment...
        "%SYSTEM_PYTHON_EXE%" -m venv venv
        if errorlevel 1 goto :python_error

        if exist "venv\Scripts\python.exe" (
            set "PYTHON_EXE=venv\Scripts\python.exe"
        ) else (
            goto :python_error
        )
    ) else (
        echo System Python not found.
        echo Downloading and preparing local portable runtime...
        powershell -ExecutionPolicy Bypass -File "system\bootstrap-runtime.ps1"
        if errorlevel 1 goto :python_error

        if exist "runtime\python.exe" (
            set "PYTHON_EXE=runtime\python.exe"
        ) else if exist "runtime\Scripts\python.exe" (
            set "PYTHON_EXE=runtime\Scripts\python.exe"
        ) else (
            goto :python_error
        )
    )
)

echo Upgrading pip...
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto :install_error

echo.
echo Detecting hardware...
where nvidia-smi >nul 2>nul
if %errorlevel%==0 (
    echo NVIDIA GPU detected. Installing PyTorch with CUDA...
    "%PYTHON_EXE%" -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
) else (
    echo NVIDIA GPU not detected. Installing PyTorch for CPU...
    "%PYTHON_EXE%" -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)
if errorlevel 1 goto :install_error

echo.
echo Installing project dependencies...
"%PYTHON_EXE%" -m pip install -r system\requirements.txt
if errorlevel 1 goto :install_error

if not exist "voices" (
    echo Creating voices folder...
    mkdir voices
)

echo.
echo Checking environment...
"%PYTHON_EXE%" -c "import torch; print('Torch:', torch.__version__); print('Device:', 'cuda' if torch.cuda.is_available() else 'cpu')"
if errorlevel 1 goto :install_error

echo.
if exist "ffmpeg\bin\ffmpeg.exe" (
    set "PATH=%CD%\ffmpeg\bin;%PATH%"
)

where ffmpeg >nul 2>nul
if %errorlevel%==0 (
    echo ffmpeg detected. MP3 export is available.
) else (
    echo ffmpeg not found.
    echo Downloading portable ffmpeg with curl...
    powershell -ExecutionPolicy Bypass -File "system\bootstrap-ffmpeg.ps1"

    if exist "ffmpeg\bin\ffmpeg.exe" (
        set "PATH=%CD%\ffmpeg\bin;%PATH%"
        echo Portable ffmpeg installed locally in ffmpeg\bin.
    ) else (
        echo Failed to prepare ffmpeg automatically.
        echo WAV will still work, but MP3 export may be unavailable until ffmpeg is installed.
    )
)

echo.
echo ============================================
echo  Done
echo ============================================
echo.
echo  1. Place one or more .wav files in the voices folder
echo  2. Run start.bat
echo  3. The browser will open automatically at http://localhost:8881
echo.
echo  The installer reuses runtime\, venv\, or a valid system Python before downloading anything.
echo  ffmpeg is available globally or in ffmpeg\bin for MP3 support.
echo.
pause
exit /b 0

:detect_system_python
set "SYSTEM_PYTHON_EXE="
call :check_python_candidate py -3.11
if defined SYSTEM_PYTHON_EXE exit /b 0
call :check_python_candidate py -3
if defined SYSTEM_PYTHON_EXE exit /b 0
call :check_python_candidate python
if defined SYSTEM_PYTHON_EXE exit /b 0
call :check_python_candidate python3
exit /b 0

:check_python_candidate
set "_PY_CMD=%~1"
set "_PY_ARG=%~2"
if "%_PY_CMD%"=="" exit /b 0
if not "%_PY_ARG%"=="" (
    %_PY_CMD% %_PY_ARG% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 set "SYSTEM_PYTHON_EXE=%_PY_CMD% %_PY_ARG%"
) else (
    %_PY_CMD% -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
    if not errorlevel 1 set "SYSTEM_PYTHON_EXE=%_PY_CMD%"
)
exit /b 0

:python_error
echo.
echo Failed to prepare the Python environment.
echo The installer tried runtime\, venv\, system Python, and portable bootstrap.
echo Check your internet connection and try install.bat again.
pause
exit /b 1

:install_error
echo.
echo Failed to install dependencies.
pause
exit /b 1
