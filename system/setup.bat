@echo off
setlocal
cd /d "%~dp0"
cd ..
title Evo XTTS V2 - Instalador

echo ============================================
echo  Evo XTTS V2 - Instalador para Windows
echo ============================================
echo.

if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 goto :python_error
)

echo Ativando ambiente virtual...
call venv\Scripts\activate.bat
if errorlevel 1 goto :venv_error

echo Atualizando pip...
python -m pip install --upgrade pip

echo.
echo Detectando hardware...
where nvidia-smi >nul 2>nul
if %errorlevel%==0 (
    echo GPU NVIDIA detectada. Instalando PyTorch com CUDA...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
) else (
    echo GPU NVIDIA nao detectada. Instalando PyTorch para CPU...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)
if errorlevel 1 goto :install_error

echo.
echo Instalando dependencias do projeto...
pip install -r system\requirements.txt
if errorlevel 1 goto :install_error

if not exist "voices" (
    echo Criando pasta voices...
    mkdir voices
)

echo.
echo Verificando ambiente...
python -c "import torch; print('Torch:', torch.__version__); print('Device:', 'cuda' if torch.cuda.is_available() else 'cpu')"

echo.
echo ============================================
echo  Pronto
echo ============================================
echo.
echo  1. Coloque um ou mais arquivos .wav na pasta voices
echo  2. Clique em Abrir XTTS.bat
echo  3. O navegador vai abrir sozinho em http://localhost:8881
echo.
echo  Se quiser MP3, tenha ffmpeg instalado:
echo  winget install ffmpeg
echo.
pause
exit /b 0

:python_error
echo.
echo Python nao foi encontrado.
echo Instale Python 3.10+ e marque a opcao "Add Python to PATH".
pause
exit /b 1

:venv_error
echo.
echo Falha ao ativar o ambiente virtual.
pause
exit /b 1

:install_error
echo.
echo Falha na instalacao de dependencias.
pause
exit /b 1


