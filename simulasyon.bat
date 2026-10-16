@echo off
chcp 65001 >nul
title Haydar - Simülasyon Modu
cd /d "%~dp0"
echo Haydar Simülasyon (Klavye Girişi) başlatılıyor...
call .venv\Scripts\activate.bat
python main.py --cli
pause
