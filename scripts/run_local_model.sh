#!/usr/bin/env bash
# MaxIM Native llama.cpp Runner for Linux & macOS
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PORT=8080
CTX=16384
NGL=99

# 1. Binary auto-detection
if [ -f "$PROJECT_ROOT/bin/llama-server" ]; then
    LLAMA_BIN="$PROJECT_ROOT/bin/llama-server"
elif [ -n "$LLAMA_SERVER_BIN" ] && [ -f "$LLAMA_SERVER_BIN" ]; then
    LLAMA_BIN="$LLAMA_SERVER_BIN"
elif command -v llama-server >/dev/null 2>&1; then
    LLAMA_BIN="$(command -v llama-server)"
elif [ -f "$HOME/.local/bin/llama-server" ]; then
    LLAMA_BIN="$HOME/.local/bin/llama-server"
elif [ -f "/usr/local/bin/llama-server" ]; then
    LLAMA_BIN="/usr/local/bin/llama-server"
else
    echo "[!] llama-server binary not found."
    echo "Please place prebuilt binary in $PROJECT_ROOT/bin/ or install via: brew install llama.cpp"
    exit 1
fi

# 2. Model auto-detection
if [ -n "$1" ]; then
    MODEL_PATH="$1"
else
    MODEL_PATH="$(find "$PROJECT_ROOT/models" "$HOME/.cache/huggingface/hub" -name "*.gguf" 2>/dev/null | head -n 1 || true)"
fi

if [ -z "$MODEL_PATH" ] || [ ! -f "$MODEL_PATH" ]; then
    echo "[!] No GGUF model found in $PROJECT_ROOT/models or ~/.cache/huggingface/hub"
    echo "Run: python scripts/download_model.py to download a recommended model."
    exit 1
fi

echo "========================================================"
echo "       Starting MaxIM Native llama.cpp Server           "
echo "========================================================"
echo "Binary:      $LLAMA_BIN"
echo "Model:       $MODEL_PATH"
echo "Context:     $CTX tokens"
echo "GPU Offload: $NGL layers"
echo "API URL:     http://127.0.0.1:$PORT/v1"
echo "========================================================"

exec "$LLAMA_BIN" -m "$MODEL_PATH" -ngl "$NGL" -c "$CTX" --port "$PORT" --host 127.0.0.1
