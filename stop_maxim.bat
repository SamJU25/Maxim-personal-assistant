@echo off
title Stopping MaxIM Services
echo ====================================================================
echo                   Stopping MaxIM V2 Services                        
echo ====================================================================
echo.

powershell -NoProfile -Command ^
    "$ports = @(8000, 5173); foreach ($p in $ports) { try { $conns = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue; foreach ($c in $conns) { $pidToKill = $c.OwningProcess; if ($pidToKill -gt 0) { Write-Host \"[*] Stopping process on port $p (PID: $pidToKill)...\"; Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue } } } catch {} }; Write-Host '[v] Ports 8000 and 5173 released.'"

taskkill /f /im llama-server.exe >nul 2>&1

echo.
echo [v] MaxIM backend and frontend processes have stopped.
echo ====================================================================
