@echo off
chcp 65001 >nul 2>&1
title PokeWars Bot
echo ============================================================
echo   PokeWars Bot - Automatyczne walki z bossem
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Python nie jest zainstalowany!
    echo Pobierz Python ze strony: https://www.python.org/downloads/
    echo Podczas instalacji zaznacz opcje Add Python to PATH
    echo.
    pause
    exit /b 1
)

python -c "import playwright; import win32com.client" >nul 2>&1
if errorlevel 1 (
    echo Instaluje wymagane pakiety, prosze czekac...
    pip install -r requirements.txt
    echo Instaluje przegladarke Chromium...
    python -m playwright install chromium
    echo.
)

if not exist config.py (
    echo Brak pliku config.py!
    echo Skopiuj config.example.py jako config.py i uzupelnij EMAIL oraz HASLO.
    echo Przyklad: copy config.example.py config.py
    echo.
    pause
    exit /b 1
)

echo Uruchamiam skrypt...
echo.
python pokewars_bot.py

echo.
pause
