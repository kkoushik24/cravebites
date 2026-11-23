@echo off
title CraveBites Live System Launcher
cd /d "%~dp0"

python start_system.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [!] Server exited.
    pause
)
