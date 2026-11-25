@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Instalando o Canal GTA
echo ============================================
echo.

rem --- Procura um Python que funcione de verdade.
rem --- O "python" da Microsoft Store e so um atalho falso, por isso testamos rodando.
set "PY="
py -3 --version >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    python --version >nul 2>nul
    if not errorlevel 1 set "PY=python"
)
if not defined PY (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
)

if not defined PY (
    echo O Python nao esta instalado. Instalando agora...
    echo Se aparecer uma janela pedindo permissao, clique em SIM.
    echo.
    winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) else (
        echo.
        echo [!] Nao consegui instalar o Python automaticamente.
        echo     Baixe em https://www.python.org/downloads/
        echo     Na instalacao, MARQUE a opcao "Add python.exe to PATH".
        echo     Depois rode este instalar.bat de novo.
        pause
        exit /b 1
    )
)

echo Usando Python:
"%PY%" --version 2>nul || %PY% --version
echo.

rem --- Apaga um ambiente quebrado de uma tentativa anterior
if exist .venv if not exist .venv\Scripts\python.exe rmdir /s /q .venv

if not exist .venv\Scripts\python.exe (
    echo Criando ambiente Python...
    if exist "%PY%" (
        "%PY%" -m venv .venv
    ) else (
        %PY% -m venv .venv
    )
)
if not exist .venv\Scripts\python.exe (
    echo [!] Nao consegui criar o ambiente Python. Veja a mensagem acima.
    pause
    exit /b 1
)

echo Instalando bibliotecas - pode levar alguns minutos...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo [!] Falha ao instalar as bibliotecas. Veja a mensagem acima.
    pause
    exit /b 1
)

ffmpeg -version >nul 2>nul
if errorlevel 1 (
    echo.
    echo Instalando o ffmpeg - editor de video...
    winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
)

echo.
echo ============================================
echo   Pronto! Para usar, de dois cliques em iniciar.bat
echo ============================================
pause
