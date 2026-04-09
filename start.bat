@echo off
title Darija Marocain - App d'apprentissage
cd /d "%~dp0"
echo.
echo  ========================================
echo    Darija Marocain - Apprentissage Audio
echo  ========================================
echo.
echo Demarrage de l'application...
echo.
start http://localhost:8503
.venv\Scripts\python.exe -m streamlit run app.py --server.port 8503 --server.headless true
pause
