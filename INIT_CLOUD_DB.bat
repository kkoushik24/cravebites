@echo off
title Initialize Cloud Database
cd /d "%~dp0food-ordering-system\backend"

echo ========================================================
echo   🗄️ INITIALIZE CLOUD MYSQL DATABASE (TiDB / Aiven / etc.)
echo ========================================================
echo.
echo Please enter the connection details from your cloud database:
echo.

set /p DB_HOST="1. Enter DB Host (e.g. gateway01.ap-southeast-1.prod.aws.tidbcloud.com): "
set /p DB_PORT="2. Enter DB Port [Press Enter for 4000]: "
if "%DB_PORT%"=="" set DB_PORT=4000
set /p DB_USER="3. Enter DB User (e.g. xxxxxx.root): "
set /p DB_PASS="4. Enter DB Password: "
set /p DB_NAME="5. Enter DB Name [Press Enter for test]: "
if "%DB_NAME%"=="" set DB_NAME=test

echo.
echo ========================================================
echo [*] Connecting to %DB_HOST%:%DB_PORT%...
echo [*] Deploying 14 tables, procedures, triggers, views & dishes...
echo ========================================================
echo.

set DB_HOST=%DB_HOST%
set DB_PORT=%DB_PORT%
set DB_USER=%DB_USER%
set DB_PASSWORD=%DB_PASS%
set DB_NAME=%DB_NAME%

python init_db.py

echo.
pause
