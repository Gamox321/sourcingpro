@echo off
title SourcingPro - Presentacion
cls

echo =============================================
echo   SourcingPro - Sistema de Gestion
echo =============================================
echo.

REM --- Use bundled Python (no system Python needed) ---
set PYTHON=python\python.exe

if not exist "%PYTHON%" (
    echo ERROR: No se encuentra python\python.exe
    echo La carpeta python/ debe estar junto a este archivo.
    echo.
    pause
    exit /b 1
)

echo Python listo: versión incluida en el proyecto.
echo.

REM --- Setup database + seed ---
echo [1/2] Configurando base de datos y datos demo...
if exist "presentacion.sqlite3" del /q presentacion.sqlite3
%PYTHON% manage.py migrate --noinput --settings=config.presentation_settings
%PYTHON% manage.py setup_presentacion --settings=config.presentation_settings

REM --- Start ---
echo.
echo =============================================
echo   Listo - http://127.0.0.1:8000/
echo =============================================
echo.
echo   admin@sourcingpro.cl        Admin2024!
echo   rrhh@sourcingpro.cl         Demo2024!
echo   ti@sourcingpro.cl           Demo2024!
echo   prevencion@sourcingpro.cl   Demo2024!
echo   finanzas@sourcingpro.cl     Demo2024!
echo   logistica@sourcingpro.cl    Demo2024!
echo   jefatura@sourcingpro.cl     Demo2024!
echo.
echo   Ctrl+C para detener.
echo =============================================
echo.
%PYTHON% manage.py runserver --settings=config.presentation_settings
pause
