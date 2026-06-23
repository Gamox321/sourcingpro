@echo off
title SourcingPro - Dev Mode
cls

echo =============================================
echo   SourcingPro - Modo Desarrollo
echo =============================================
echo.

REM Find system Python
set PYTHON=
for %%p in (py -3 python python3) do (
    where %%p >nul 2>nul
    if not errorlevel 1 (
        %%p --version >nul 2>nul
        if not errorlevel 1 (
            set PYTHON=%%p
            goto :found
        )
    )
)

echo ERROR: Python no encontrado en el sistema.
echo Instala Python desde https://python.org
pause
exit /b 1

:found
echo Python: %PYTHON%

REM Rebuild venv with full requirements
echo [1/3] Reconstruyendo entorno virtual...
if exist "venv" rmdir /s /q venv
%PYTHON% -m venv venv
echo [2/3] Instalando dependencias...
venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
echo [3/3] Migrando base de datos...
venv\Scripts\python.exe manage.py migrate
echo.
echo Listo - http://127.0.0.1:8000/
echo.
venv\Scripts\python.exe manage.py runserver
pause
