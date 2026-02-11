@echo off
TITLE Sistema de Consulta Normativa
echo ====================================================
echo      INICIANDO SISTEMA DE CONSULTA NORMATIVA
echo ====================================================
echo.
echo Directorio de trabajo: %~dp0

REM Usar el entorno virtual CORRECTO detectado en 'TRABAJO 2025\venv'
"C:\Users\juan.montenegro\TRABAJO 2025\venv\Scripts\python.exe" -m streamlit run "%~dp001_APP_CORE\app_interfaz.py"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo iniciar el sistema.
    pause
)