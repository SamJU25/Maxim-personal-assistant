@echo off
setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set PORT=8080
set CTX=16384
set NGL=99

:: 1. Auto-detect llama-server binary
if exist "%PROJECT_ROOT%\bin\llama-server.exe" (
    set "LLAMA_BIN=%PROJECT_ROOT%\bin\llama-server.exe"
) else if defined LLAMA_SERVER_BIN (
    set "LLAMA_BIN=%LLAMA_SERVER_BIN%"
) else if exist "C:\Users\Sam\.unsloth\llama.cpp\build\bin\Release\llama-server.exe" (
    set "LLAMA_BIN=C:\Users\Sam\.unsloth\llama.cpp\build\bin\Release\llama-server.exe"
) else (
    where llama-server.exe >nul 2>&1
    if !errorlevel! equ 0 (
        set "LLAMA_BIN=llama-server.exe"
    ) else (
        echo [!] llama-server.exe was not found.
        echo Please drop prebuilt binaries into %PROJECT_ROOT%\bin\ from https://github.com/ggml-org/llama.cpp/releases
        pause
        exit /b 1
    )
)

:: 2. Auto-detect model if not provided
if not "%~1"=="" (
    set "MODEL_PATH=%~1"
) else (
    :: Check project models/ folder first
    for /r "%PROJECT_ROOT%\models" %%f in (*.gguf) do (
        if not defined MODEL_PATH set "MODEL_PATH=%%f"
    )
    :: Fallback to F:\huggingface if not found
    if not defined MODEL_PATH (
        if exist "F:\huggingface\hub\models--lukey03--Qwen3.5-9B-abliterated-GGUF\snapshots\dac35c6385d79a6a9fe113d7a3b730348791d37f\Qwen3.5-9B-abliterated-Q4_K_M.gguf" (
            set "MODEL_PATH=F:\huggingface\hub\models--lukey03--Qwen3.5-9B-abliterated-GGUF\snapshots\dac35c6385d79a6a9fe113d7a3b730348791d37f\Qwen3.5-9B-abliterated-Q4_K_M.gguf"
        )
    )
)

if not defined MODEL_PATH (
    echo [!] No GGUF model found in %PROJECT_ROOT%\models or HuggingFace cache.
    echo Run: python scripts\download_model.py to download a recommended model.
    pause
    exit /b 1
)

echo ========================================================
echo        Starting MaxIM Native llama.cpp CUDA Server       
echo ========================================================
echo Binary:      %LLAMA_BIN%
echo Model:       %MODEL_PATH%
echo Context:     %CTX% tokens
echo GPU Offload: %NGL% layers
echo API URL:     http://127.0.0.1:%PORT%/v1
echo ========================================================

"%LLAMA_BIN%" -m "%MODEL_PATH%" -ngl %NGL% -c %CTX% --port %PORT% --host 127.0.0.1
pause
