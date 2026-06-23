@echo off
title SourcingPro - Presentacion
cls

echo =============================================
echo   SourcingPro - Sistema de Gestion
echo =============================================
echo.

REM ============================================================
REM  1. FIND PYTHON - 5 fallback strategies
REM ============================================================
set PYTHON=

REM Strategy 1: Windows Python Launcher (C:\Windows\py.exe)
py -3 --version >nul 2>nul
if not errorlevel 1 (
    set PYTHON=py -3
    goto :found
)

REM Strategy 2: python3 in PATH
python3 --version >nul 2>nul
if not errorlevel 1 (
    set PYTHON=python3
    goto :found
)

REM Strategy 3: python in PATH
python --version >nul 2>nul
if not errorlevel 1 (
    set PYTHON=python
    goto :found
)

REM Strategy 4: Microsoft Store
if exist "%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe" (
    set PYTHON="%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe"
    goto :found
)

REM Strategy 5: Scan common locations
for %%d in (
    "%LOCALAPPDATA%\Programs\Python"
    "C:\Python314" "C:\Python313" "C:\Python312"
    "C:\Program Files\Python314" "C:\Program Files\Python313" "C:\Program Files\Python312"
) do (
    if exist "%%d\python.exe" (
        set PYTHON="%%d\python.exe"
        goto :found
    )
)

echo ERROR: Python no encontrado.
echo.
echo Instala Python desde https://python.org
echo Marca "Add Python to PATH" durante la instalacion.
echo.
pause
exit /b 1

:found
echo Python encontrado: %PYTHON%

REM ============================================================
REM  2. REBUILD VENV (delete stale paths from other PC)
REM ============================================================
echo [1/3] Creando entorno virtual...
if exist "venv" (
    rmdir /s /q venv
)
%PYTHON% -m venv venv
echo [2/3] Instalando dependencias...
venv\Scripts\python.exe -m pip install django django-widget-tweaks python-decouple --quiet

REM ============================================================
REM  3. SETUP DATABASE + SEED
REM ============================================================
echo [3/3] Configurando base de datos y datos demo...
if exist "presentacion.sqlite3" del /q presentacion.sqlite3
venv\Scripts\python.exe manage.py migrate --noinput --settings=config.presentation_settings
venv\Scripts\python.exe manage.py setup_presentacion --settings=config.presentation_settings

REM ============================================================
REM  4. START
REM ============================================================
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
venv\Scripts\python.exe manage.py runserver --settings=config.presentation_settings
pause
