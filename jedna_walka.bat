@echo off
chcp 65001 >nul 2>&1
title PokeWars Bot - Jedna walka
if not exist config.py (
    echo Brak pliku config.py! Skopiuj: copy config.example.py config.py
    pause
    exit /b 1
)
python jedna_walka.py
pause
