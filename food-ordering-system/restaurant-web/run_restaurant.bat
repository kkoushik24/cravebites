@echo off
title CraveBites Restaurant Web (Port 5002)
cd /d "%~dp0"
python -m http.server 5002 --bind 127.0.0.1
pause

