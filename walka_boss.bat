@echo off
chcp 65001 >nul 2>&1
title PokeWars Bot - Walka z bossem (reczne logowanie)
if not exist config.py (
    echo Brak pliku config.py! Skopiuj: copy config.example.py config.py
    pause
    exit /b 1
)
python walka_boss.py
pause
