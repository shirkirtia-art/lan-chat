@echo off
setlocal
title LAN Web Chat - Cloudflare Tunnel

echo =======================================================
echo     LAN Web Chat + Cloudflare Tunnel Launcher
echo =======================================================
echo.

:: Detect Python executable (python or py launcher)
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

:: Get directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

:: Check if the chat server is already running on port 8000
%PY_CMD% -c "import socket; s = socket.socket(); exit(0 if s.connect_ex(('127.0.0.1', 8000)) == 0 else 1)" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [*] Starting Web Chat server in background...
    start "" /b %PY_CMD% "%SCRIPT_DIR%web_chat.py"
    timeout /t 2 /nobreak >nul
) else (
    echo [*] Web Chat server is already running on port 8000.
)

:: Check if cloudflared is installed
where cloudflared >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo [WARNING] 'cloudflared' was not found in your system PATH!
    echo To install Cloudflare Tunnel on Windows:
    echo   Run in terminal:  winget install Cloudflare.cloudflared
    echo   Or download from: https://github.com/cloudflare/cloudflared/releases/latest
    echo.
    echo Note: Your local LAN Web Chat is running at:
    echo   http://localhost:8000
    echo.
    pause
    exit /b 1
)

echo [*] Starting Cloudflare Tunnel to http://localhost:8000 ...
echo [i] Look for the "https://*.trycloudflare.com" URL below:
echo.
cloudflared tunnel --url http://localhost:8000

pause
