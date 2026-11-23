@echo off
title CraveBites System Launcher
cd /d "%~dp0"

echo ========================================================
echo   🍱 STARTING CRAVEBITES SYSTEM (BACKEND + TUNNEL + WEB)
echo ========================================================
echo.

REM 1. Start Backend on Port 5000
echo [*] Launching CraveBites Backend on Port 5000...
start "CraveBites Backend (Port 5000)" cmd /k "cd /d %~dp0food-ordering-system\backend && python app.py"

REM 2. Start Cloudflare Tunnel
echo [*] Launching Cloudflare Wireless Tunnel...
start "CraveBites Cloudflare Tunnel" cmd /k "cd /d %~dp0 && cloudflared.exe tunnel --url http://127.0.0.1:5000"

REM 3. Start Restaurant Web Dashboard on Port 5002
echo [*] Launching Restaurant Web on Port 5002...
start "CraveBites Restaurant Web (Port 5002)" cmd /k "cd /d %~dp0food-ordering-system\restaurant-web && python -m http.server 5002 --bind 127.0.0.1"

echo.
echo ========================================================
echo   ✅ ALL SERVERS ARE NOW RUNNING!
echo ========================================================
echo   * Keep the pop-up terminal windows open.
echo   * Restaurant Web:   http://127.0.0.1:5002
echo   * Backend Health:   http://127.0.0.1:5000/api/health
echo.
echo   📱 HOW TO USE WIRELESSLY ON YOUR PHONES:
echo   1. Look at the "CraveBites Cloudflare Tunnel" window for the URL:
echo      (e.g., https://xxxx-xxxx.trycloudflare.com)
echo.
echo   2. Option A (Open in phone browser - ZERO setup):
echo      - Customer App: https://[your-tunnel].trycloudflare.com/app
echo      - Rider App:    https://[your-tunnel].trycloudflare.com/rider
echo      (Tap "Add to Home screen" to use it as a fullscreen app!)
echo.
echo   3. Option B (In the installed phone APK):
echo      - In the APK, paste the URL in the "Server URL" box
echo      - Tap "Save & Connect" (works immediately, no wires needed!)
echo ========================================================
echo.
pause
