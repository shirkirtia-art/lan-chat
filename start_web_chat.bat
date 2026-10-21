@echo off
setlocal
title LAN Web Chat Server

echo =======================================================
echo              LAN Web Chat Server
echo =======================================================
echo.

:: Detect Python executable
set "PY_CMD="
python -V >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=python"
) else (
    py -V >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PY_CMD=py"
    )
)

if not defined PY_CMD (
    echo [ERROR] Python was not found in your system PATH.
    echo Please install Python 3 from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Run the Web Chat server
%PY_CMD% "%~dp0web_chat.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo Server stopped with error code %ERRORLEVEL%.
    pause
)
