@echo off
chcp 65001 >nul
title Haydar Kapat
echo Haydar sonlandırılıyor...
taskkill /f /im pythonw.exe >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq Haydar*" >nul 2>&1
echo Haydar başarıyla kapatıldı.
timeout /t 2 >nul
exit
