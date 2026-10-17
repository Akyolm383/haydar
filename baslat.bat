@echo off
title Haydar
cd /d "%~dp0"
taskkill /f /im pythonw.exe >nul 2>&1
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0main.py"
