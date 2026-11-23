@echo off
title Push CraveBites to GitHub
cd /d "%~dp0"

echo ========================================================
echo   🚀 PUSH CRAVEBITES TO GITHUB
echo ========================================================
echo.
set /p REPO_URL="Enter your GitHub Repository URL (e.g. https://github.com/username/cravebites.git): "

if "%REPO_URL%"=="" (
    echo [!] No URL entered. Exiting.
    pause
    exit /b
)

echo [*] Setting up git remote...
git remote remove origin 2>nul
git remote add origin %REPO_URL%
git branch -M main

echo [*] Pushing code to GitHub...
git push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================================
    echo   ✅ CODE SUCCESSFULLY PUSHED TO GITHUB!
    echo ========================================================
    echo   Now you can connect this repo directly to Render.com!
) else (
    echo.
    echo [!] Push failed. Please ensure you are logged into GitHub in your browser/terminal.
)
echo.
pause
