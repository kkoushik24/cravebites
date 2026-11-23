@echo off
title CraveBites - Install Apps to Connected Phones
cd /d "%~dp0"

echo ========================================================
echo   📱 CRAVEBITES PHONE INSTALLER
echo ========================================================
echo Please ensure your phone(s) are plugged in via USB
echo and your phone screens are UNLOCKED!
echo.

echo [*] Checking connected devices...
adb devices -l
echo.

REM Phone 1 (Customer App)
echo [*] Installing CraveBites Customer App on Phone 1...
adb -s 1412931553013415 install -r "%~dp0builds\CraveBites-Customer.apk"
adb -s 1412931553013415 shell am start -n com.dabba.customer/com.dabba.customer.MainActivity >nul 2>&1

REM Phone 2 (Rider App)
echo [*] Installing Crave Rider App on Phone 2...
adb -s 6296bfb8 install -r "%~dp0builds\dabba-rider.apk"
adb -s 6296bfb8 shell am start -n com.dabba.delivery/com.dabba.delivery.MainActivity >nul 2>&1

echo.
echo ========================================================
echo   ✅ APPS INSTALLED & LAUNCHED!
echo ========================================================
echo   You can now UNPLUG both USB cables!
echo   Both phones will work wirelessly over Cloudflare.
echo ========================================================
pause
