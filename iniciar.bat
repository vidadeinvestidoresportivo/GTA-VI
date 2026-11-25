@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv (
    echo Rode primeiro o instalar.bat
    pause
    exit /b 1
)
call .venv\Scripts\activate.bat
python canal.py %*
pause
