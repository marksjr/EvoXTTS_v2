@echo off
setlocal
cd /d "%~dp0"
cd ..
title Evo XTTS V2 - Installer

echo ============================================
echo  Evo XTTS V2 - Windows Installer
echo ============================================
echo.

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 goto :python_error
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 goto :venv_error

echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Detecting hardware...
where nvidia-smi >nul 2>nul
if %errorlevel%==0 (
    echo NVIDIA GPU detected. Installing PyTorch with CUDA...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
) else (
    echo NVIDIA GPU not detected. Installing PyTorch for CPU...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)
if errorlevel 1 goto :install_error

echo.
echo Installing project dependencies...
pip install -r system\requirements.txt
if errorlevel 1 goto :install_error

if not exist "voices" (
    echo Creating voices folder...
    mkdir voices
)

echo.
echo Checking environment...
python -c "import torch; print('Torch:', torch.__version__); print('Device:', 'cuda' if torch.cuda.is_available() else 'cpu')"

echo.
echo ============================================
echo  Done
echo ============================================
echo.
echo  1. Place one or more .wav files in the voices folder
echo  2. Run start.bat
echo  3. The browser will open automatically at http://localhost:8881
echo.
echo  For MP3 support, install ffmpeg:
echo  winget install ffmpeg
echo.
pause
exit /b 0

:python_error
echo.
echo Python not found.
echo Install Python 3.10+ and check "Add Python to PATH".
pause
exit /b 1

:venv_error
echo.
echo Failed to activate virtual environment.
pause
exit /b 1

:install_error
echo.
echo Failed to install dependencies.
pause
exit /b 1
