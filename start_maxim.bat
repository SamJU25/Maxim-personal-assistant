@echo off
title MaxIM V2 — Sovereign AI Executive Assistant Launcher
setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

cls
echo ====================================================================
echo           MaxIM V2 — Sovereign Personal AI Assistant                
echo ====================================================================
echo.
echo [*] Root Directory: %PROJECT_ROOT%
echo.

:: 1. Verify Python & Virtual Environment
set "PYTHON_EXE=%PROJECT_ROOT%\backend\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    echo [!] Backend virtual environment not found. Setting it up now...
    where python >nul 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] Python 3 was not found on your system PATH.
        echo Please install Python 3.11+ and restart this launcher.
        pause
        exit /b 1
    )
    python -m venv "%PROJECT_ROOT%\backend\.venv"
    "%PROJECT_ROOT%\backend\.venv\Scripts\pip.exe" install -r "%PROJECT_ROOT%\backend\requirements.txt"
)

:: 2. Verify Frontend Dependencies
if not exist "%PROJECT_ROOT%\frontend\node_modules" (
    echo [!] Frontend dependencies not found. Running npm install...
    where npm >nul 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] Node.js / npm was not found on your system PATH.
        echo Please install Node.js 20+ and restart this launcher.
        pause
        exit /b 1
    )
    cd /d "%PROJECT_ROOT%\frontend"
    call npm install
    cd /d "%PROJECT_ROOT%"
)

:: 3. Launch Backend Server (Port 8000)
echo [*] Launching MaxIM Native Backend on http://127.0.0.1:8000 ...
start "MaxIM Backend API (Port 8000)" /min cmd /c "cd /d "%PROJECT_ROOT%\backend" && .venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000"

:: 4. Launch Frontend Dev Server (Port 5173)
echo [*] Launching MaxIM React 19 Frontend on http://localhost:5173 ...
start "MaxIM Frontend UI (Port 5173)" /min cmd /c "cd /d "%PROJECT_ROOT%\frontend" && npm run dev"

:: 5. Wait for Backend Health Check
echo [*] Waiting for services to initialize...
powershell -NoProfile -Command ^
    "$ready = $false; for ($i = 0; $i -lt 30; $i++) { try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 1; if ($r.status -eq 'healthy') { $ready = $true; break; } } catch {} Start-Sleep -Milliseconds 500 }; if ($ready) { exit 0 } else { exit 1 }"

if %errorlevel% neq 0 (
    echo [!] Backend took longer than expected to report healthy. Proceeding anyway...
) else (
    echo [v] Backend is healthy and ready.
)

:: 6. Launch Web Browser
echo [*] Opening MaxIM in your default browser...
timeout /t 2 /nobreak >nul
start http://localhost:5173

cls
echo ====================================================================
echo           MaxIM V2 — Sovereign Personal AI Assistant                
echo ====================================================================
echo.
echo   [+] Frontend UI:     http://localhost:5173
echo   [+] Backend API:     http://127.0.0.1:8000
echo   [+] API Swagger:     http://127.0.0.1:8000/docs
echo   [+] Vault Synapse:   %PROJECT_ROOT%\vault
echo.
echo ====================================================================
echo   MaxIM is running in the background.
echo   To STOP all MaxIM services, press any key or run stop_maxim.bat
echo ====================================================================
echo.
pause

echo.
echo [*] Shutting down MaxIM services...
call "%PROJECT_ROOT%\stop_maxim.bat"
echo [v] Shutdown complete.
timeout /t 2 >nul
exit /b 0
