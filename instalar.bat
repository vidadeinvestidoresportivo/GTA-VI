@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Instalando o Canal GTA
echo ============================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set PY=py -3
) else (
    where python >nul 2>nul
    if errorlevel 1 (
        echo [!] Python nao encontrado.
        echo     Instalando com o winget...
        winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
        echo.
        echo Feche esta janela e rode o instalar.bat de novo.
        pause
        exit /b 1
    )
    set PY=python
)

if not exist .venv (
    echo Criando ambiente Python...
    %PY% -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [!] Falha ao instalar as bibliotecas. Veja a mensagem acima.
    pause
    exit /b 1
)

where ffmpeg >nul 2>nul
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
