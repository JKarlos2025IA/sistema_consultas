@echo off
chcp 65001 > nul
echo ========================================================
echo      ACTUALIZADOR AUTOMATICO DE GITHUB (PUSH)
echo      Proyecto: SISTEMA CONSULTAS NORMATIVAS
echo ========================================================
echo.
cd /d "%~dp0"

echo 1. Verificando estado actual...
git status
echo.

set /p commit_msg="Introduce mensaje del commit (Enter para usar fecha/hora): "

if "%commit_msg%"=="" (
    set commit_msg=Actualizacion automatica %date% %time%
)

echo.
echo 2. Sincronizando con GitHub (git pull --rebase)...
git pull --rebase origin main
if %errorlevel% neq 0 (
    echo.
    echo      [ERROR] Conflicto al sincronizar. Resuelve manualmente.
    echo ========================================================
    pause
    exit /b 1
)

echo.
echo 3. Agregando cambios (git add)...
git add .

echo.
echo 4. Guardando cambios (git commit)...
git commit -m "%commit_msg%"

echo.
echo 5. Subiendo a la nube (git push)...
git push origin main

echo.
echo ========================================================
if %errorlevel% equ 0 (
    echo      [EXITO] Cambios subidos correctamente.
    echo      La web deberia actualizarse en unos minutos.
) else (
    echo      [ERROR] Hubo un problema al subir los cambios.
)
echo ========================================================
pause
