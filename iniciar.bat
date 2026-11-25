@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    echo Rode primeiro o instalar.bat
    pause
    exit /b 1
)

rem --- Confere se as bibliotecas estao instaladas; se faltar alguma, instala.
.venv\Scripts\python.exe -c "import requests, PIL, pytrends, faster_whisper, imageio_ffmpeg" >nul 2>nul
if errorlevel 1 (
    echo Instalando as bibliotecas que faltam - pode levar alguns minutos...
    echo.
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [!] Falha ao instalar as bibliotecas.
        echo     Tire um print desta janela inteira e mande para o Claude.
        pause
        exit /b 1
    )
)

.venv\Scripts\python.exe canal.py %*
pause
