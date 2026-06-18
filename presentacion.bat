@echo off
chcp 65001 >nul
title SourcingPro — Presentacion
cls

echo =============================================
echo   SourcingPro — Sistema de Gestion
echo   Configurando presentacion...
echo =============================================
echo.

REM --- Crear venv si no existe ---
if not exist "venv\Scripts\python.exe" (
    echo [1/4] Creando entorno virtual...
    python -m venv venv
    echo [1/4] Instalando dependencias...
    venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
) else (
    echo [1/4] Entorno virtual listo.
)

REM --- Migrar + configurar ---
echo [2/4] Configurando base de datos SQLite...
set DJANGO_SETTINGS_MODULE=config.presentation_settings
venv\Scripts\python.exe manage.py migrate --noinput

echo [3/4] Creando datos de demostracion...
venv\Scripts\python.exe manage.py setup_presentacion

REM --- Listo ---
echo.
echo =============================================
echo   PRESENTACION LISTA — Iniciando servidor
echo =============================================
echo.
echo   Abre en el navegador: http://127.0.0.1:8000/
echo.
echo   Usuarios:
echo     admin@sourcingpro.cl      / Admin2024!
echo     rrhh@sourcingpro.cl       / Demo2024!
echo     ti@sourcingpro.cl         / Demo2024!
echo     prevencion@sourcingpro.cl / Demo2024!
echo     finanzas@sourcingpro.cl   / Demo2024!
echo     logistica@sourcingpro.cl  / Demo2024!
echo     jefatura@sourcingpro.cl   / Demo2024!
echo.
echo   Presiona Ctrl+C para detener el servidor.
echo =============================================
echo.

venv\Scripts\python.exe manage.py runserver
pause
