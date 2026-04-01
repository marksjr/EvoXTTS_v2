@echo off
setlocal EnableExtensions
cd /d "%~dp0"
cd ..
title Evo XTTS V2 - Installer

set "LOG_DIR=logs"
set "LOG_FILE=%LOG_DIR%\install.log"
set "PYTHON_EXE="
set "SYSTEM_PYTHON_EXE="
set "SITE_PACKAGES_DIR="
set "CURRENT_STEP=0"
set "CURRENT_STEP_NAME=Starting installer"

if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
break > "%LOG_FILE%"

call :header
call :log "Installer log: %CD%\%LOG_FILE%"
call :log "This installer runs in clear steps so you can see exactly where it fails."
call :log ""

call :set_step 1 "Prepare Python environment"
if exist "runtime\python.exe" (
    set "PYTHON_EXE=runtime\python.exe"
    set "SITE_PACKAGES_DIR=%CD%\runtime\Lib\site-packages"
    call :log "Using existing portable Python runtime."
) else if exist "runtime\Scripts\python.exe" (
    set "PYTHON_EXE=runtime\Scripts\python.exe"
    set "SITE_PACKAGES_DIR=%CD%\runtime\Lib\site-packages"
    call :log "Using existing portable Python runtime."
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
    set "SITE_PACKAGES_DIR=%CD%\venv\Lib\site-packages"
    call :log "Using existing virtual environment."
) else (
    call :log "No local Python found. Looking for a compatible system Python..."
    call :detect_system_python
    if defined SYSTEM_PYTHON_EXE (
        call :log "System Python detected: %SYSTEM_PYTHON_EXE%"
        call :log "Creating local virtual environment in venv\ ..."
        call %SYSTEM_PYTHON_EXE% -m venv venv >> "%LOG_FILE%" 2>&1
        if errorlevel 1 goto :python_error

        if exist "venv\Scripts\python.exe" (
            set "PYTHON_EXE=venv\Scripts\python.exe"
            set "SITE_PACKAGES_DIR=%CD%\venv\Lib\site-packages"
            call :log "Virtual environment created successfully."
        ) else (
            goto :python_error
        )
    ) else (
        call :log "System Python not found."
        call :log "Downloading and preparing a local portable Python runtime..."
        powershell -ExecutionPolicy Bypass -File "system\bootstrap-runtime.ps1" >> "%LOG_FILE%" 2>&1
        if errorlevel 1 goto :python_error

        if exist "runtime\python.exe" (
            set "PYTHON_EXE=runtime\python.exe"
            set "SITE_PACKAGES_DIR=%CD%\runtime\Lib\site-packages"
        ) else if exist "runtime\Scripts\python.exe" (
            set "PYTHON_EXE=runtime\Scripts\python.exe"
            set "SITE_PACKAGES_DIR=%CD%\runtime\Lib\site-packages"
        ) else (
            goto :python_error
        )

        call :log "Portable Python runtime prepared successfully."
    )
)

if not defined SITE_PACKAGES_DIR goto :python_error
call :log "Python site-packages: %SITE_PACKAGES_DIR%"

call :set_step 2 "Upgrade pip tools"
call :log "Updating pip, setuptools and wheel..."
"%PYTHON_EXE%" -m pip install --upgrade pip setuptools wheel >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :install_error
call :log "pip tools updated."

call :set_step 3 "Install PyTorch"
call :log "Checking hardware to decide between GPU and CPU packages..."
where nvidia-smi >nul 2>nul
if %errorlevel%==0 (
    call :log "NVIDIA GPU detected. Installing PyTorch with CUDA support..."
    "%PYTHON_EXE%" -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128 >> "%LOG_FILE%" 2>&1
) else (
    call :log "No NVIDIA GPU detected. Installing PyTorch for CPU..."
    "%PYTHON_EXE%" -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu >> "%LOG_FILE%" 2>&1
)
if errorlevel 1 goto :install_error
call :log "PyTorch installed."

call :set_step 4 "Install Evo XTTS dependencies"
call :log "Removing legacy coqpit package if it exists..."
"%PYTHON_EXE%" -m pip uninstall -y coqpit >> "%LOG_FILE%" 2>&1
if exist "%SITE_PACKAGES_DIR%\coqpit" (
    call :log "Removing leftover coqpit folder from site-packages..."
    rmdir /s /q "%SITE_PACKAGES_DIR%\coqpit" >> "%LOG_FILE%" 2>&1
)
call :log "Installing project dependencies from system\requirements.txt ..."
"%PYTHON_EXE%" -m pip install -r system\requirements.txt >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :install_error
call :log "Reinstalling coqpit-config 0.1.2 to restore the coqpit module..."
"%PYTHON_EXE%" -m pip install --force-reinstall --no-deps coqpit-config==0.1.2 >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :install_error
call :log "Project dependencies installed."

call :set_step 5 "Validate environment"
if not exist "voices" (
    call :log "Creating voices folder..."
    mkdir voices >> "%LOG_FILE%" 2>&1
)
call :log "Checking installed versions and runtime health..."
"%PYTHON_EXE%" -c "import torch, TTS; print('Torch:', torch.__version__); print('Device:', 'cuda' if torch.cuda.is_available() else 'cpu'); print('TTS:', TTS.__version__)" >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :install_error
call :log "Environment check passed."

call :set_step 6 "Prepare ffmpeg for MP3"
if exist "ffmpeg\bin\ffmpeg.exe" (
    set "PATH=%CD%\ffmpeg\bin;%PATH%"
)

where ffmpeg >nul 2>nul
if %errorlevel%==0 (
    call :log "ffmpeg detected. MP3 export is available."
) else (
    call :log "ffmpeg not found."
    call :log "Trying to download a portable ffmpeg package..."
    powershell -ExecutionPolicy Bypass -File "system\bootstrap-ffmpeg.ps1" >> "%LOG_FILE%" 2>&1

    if exist "ffmpeg\bin\ffmpeg.exe" (
        set "PATH=%CD%\ffmpeg\bin;%PATH%"
        call :log "Portable ffmpeg installed locally in ffmpeg\bin."
    ) else (
        call :log "Automatic ffmpeg setup failed."
        call :log "WAV output will still work, but MP3 export may be unavailable."
    )
)

call :success
pause
exit /b 0

:header
echo ============================================
echo  Evo XTTS V2 - Windows Installer
echo ============================================
echo.
exit /b 0

:set_step
set "CURRENT_STEP=%~1"
set "CURRENT_STEP_NAME=%~2"
call :log "PASSO %CURRENT_STEP%/6 - %CURRENT_STEP_NAME%"
exit /b 0

:log
if "%~1"=="" (
    echo.
    >> "%LOG_FILE%" echo.
    exit /b 0
)
echo %~1
>> "%LOG_FILE%" echo %~1
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
echo ============================================
echo  Installation Failed
echo ============================================
echo.
echo Failed during PASSO %CURRENT_STEP%/6 - %CURRENT_STEP_NAME%
echo.
echo Reason: the Python environment could not be prepared.
echo The installer tried runtime\, venv\, system Python, and portable bootstrap.
echo Check your internet connection and then run install.bat again.
echo.
echo Full log: %CD%\%LOG_FILE%
echo.
>> "%LOG_FILE%" echo.
>> "%LOG_FILE%" echo Installation failed during PASSO %CURRENT_STEP%/6 - %CURRENT_STEP_NAME%
pause
exit /b 1

:install_error
echo.
echo ============================================
echo  Installation Failed
echo ============================================
echo.
echo Failed during PASSO %CURRENT_STEP%/6 - %CURRENT_STEP_NAME%
echo.
echo Open the log file below to see the exact error details:
echo %CD%\%LOG_FILE%
echo.
echo Common causes:
echo - internet connection blocked during download
echo - antivirus blocking Python or ffmpeg files
echo - Python package download temporarily unavailable
echo.
>> "%LOG_FILE%" echo.
>> "%LOG_FILE%" echo Installation failed during PASSO %CURRENT_STEP%/6 - %CURRENT_STEP_NAME%
pause
exit /b 1

:success
echo.
echo ============================================
echo  Installation Complete
echo ============================================
echo.
echo The system is ready for normal users:
echo 1. Put one or more .wav voice files in the voices folder
echo 2. Run start.bat
echo 3. Wait for the browser to open at http://localhost:8881
echo.
echo If something fails later, check this log:
echo %CD%\%LOG_FILE%
echo.
echo Notes:
echo - the installer reuses runtime\, venv\, or a valid system Python before downloading anything
echo - the app can work without ffmpeg, but then only WAV export is guaranteed
echo - the XTTS model may still download on first application start
echo.
>> "%LOG_FILE%" echo.
>> "%LOG_FILE%" echo Installation completed successfully.
exit /b 0
