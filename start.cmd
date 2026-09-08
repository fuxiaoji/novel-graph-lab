@echo off
cd /d "%~dp0"
python server.py --open
if errorlevel 1 pause
