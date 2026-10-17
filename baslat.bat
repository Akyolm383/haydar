@echo off
chcp 65001 >nul
title Haydar
cd /d "%~dp0"
echo Eski çalışan kopyalar kapatılıyor...
taskkill /f /im pythonw.exe >nul 2>&1
echo Haydar başlatılıyor (Dinamik Ada modu)...
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0main.py"
exit
