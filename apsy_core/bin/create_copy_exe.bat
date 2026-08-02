@echo off
setlocal

REM =====================================
REM CONFIGURACION
REM =====================================

set RELEASES_DIR=C:\apsy_data\releases
set TOOL_NAME=apsy_db

REM =====================================
REM COMPILAR
REM =====================================

echo.
echo Compilando %TOOL_NAME%...

pyinstaller --onefile --name %TOOL_NAME% apsydb.py

if errorlevel 1 (
    echo.
    echo Error compilando.
    pause
    exit /b 1
)

REM =====================================
REM CREAR DESTINO
REM =====================================

set DESTINO=%RELEASES_DIR%\TOOLS\

if not exist "%DESTINO%" (
    mkdir "%DESTINO%"
)

REM =====================================
REM COPIAR EJECUTABLE
REM =====================================

copy /Y "dist\%TOOL_NAME%.exe" "%DESTINO%\"

REM =====================================
REM COPIAR JSON
REM =====================================

copy /Y "apsydb.json" "%DESTINO%\"

echo.
echo Release creada:
echo %DESTINO%

pause