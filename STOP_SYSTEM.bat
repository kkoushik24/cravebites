@echo off
title Stop CraveBites System
cd /d "%~dp0"

echo ========================================================
echo   🛑 STOPPING ALL CRAVEBITES SERVERS & TUNNELS
echo ========================================================
powershell -Command "Get-Process python, cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force"
echo.
echo All CraveBites servers and tunnels have been stopped.
echo ========================================================
pause
