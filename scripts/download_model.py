"""
MaxIM Open-Source Local Model Downloader.
Downloads recommended GGUF models directly into your local 'models/' directory.
Fully cross-platform (Windows, macOS, Linux) with automatic resume support.

Usage:
    python scripts/download_model.py
    python scripts/download_model.py --model qwen-7b
    python scripts/download_model.py --repo Qwen/Qwen2.5-Coder-7B-Instruct-GGUF --file qwen2.5-coder-7b-instruct-q4_k_m.gguf
"""
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"

CATALOG = {
    "1": {
        "alias": "qwen-7b",
        "name": "Qwen 2.5 Coder 7B (Q4_K_M)",
        "repo_id": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
        "filename": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "size": "4.68 GB",
        "vram": "6 GB - 8 GB VRAM",
        "desc": "Recommended workhorse for coding, agentic tool execution, and daily tasks.",
    },
    "2": {
        "alias": "qwen-3b",
        "name": "Qwen 2.5 3B (Q4_K_M)",
        "repo_id": "Qwen/Qwen2.5-3B-Instruct-GGUF",
        "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "size": "2.10 GB",
        "vram": "3 GB - 4 GB VRAM (Runs on CPU)",
        "desc": "Ultra-fast lightweight model for entry laptops, MacBooks, and CPU inference.",
    },
    "3": {
        "alias": "qwen-9b",
        "name": "Qwen 3.5 9B Abliterated (Q4_K_M)",
        "repo_id": "lukey03/Qwen3.5-9B-abliterated-GGUF",
        "filename": "Qwen3.5-9B-abliterated-Q4_K_M.gguf",
        "size": "5.24 GB",
        "vram": "6 GB VRAM (RTX 4050/3060)",
        "desc": "Uncensored abliterated 9B reasoning model.",
    },
    "4": {
        "alias": "llama-3b",
        "name": "Llama 3.2 3B Instruct (Q4_K_M)",
        "repo_id": "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "size": "2.02 GB",
        "vram": "3 GB VRAM",
        "desc": "Meta Llama 3.2 compact dialogue model.",
    },
}

def main():
    parser = argparse.ArgumentParser(description="MaxIM GGUF Model Downloader")
    parser.add_argument("--model", type=str, help="Model alias (qwen-7b, qwen-3b, qwen-9b, llama-3b)")
    parser.add_argument("--repo", type=str, help="Custom HuggingFace repo ID")
    parser.add_argument("--file", type=str, help="Custom GGUF filename")
    parser.add_argument("--dir", type=str, default=str(MODELS_DIR), help="Target download directory")
    args = parser.parse_args()

    dest_dir = Path(args.dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("\n[!] huggingface_hub is required. Install via: pip install huggingface_hub\n")
        sys.exit(1)

    repo_id = None
    filename = None

    if args.repo and args.file:
        repo_id = args.repo
        filename = args.file
    elif args.model:
        for entry in CATALOG.values():
            if entry["alias"] == args.model.lower():
                repo_id = entry["repo_id"]
                filename = entry["filename"]
                break
        if not repo_id:
            print(f"[!] Unknown model alias: {args.model}")
            sys.exit(1)
    else:
        # Interactive prompt
        print("\n=======================================================")
        print("          MaxIM Open-Source Local Model Setup          ")
        print("=======================================================")
        print(f"Target Directory: {dest_dir.resolve()}\n")
        print("Available Recommended Models:")
        for key, entry in CATALOG.items():
            print(f"  [{key}] {entry['name']} ({entry['size']})")
            print(f"      Hardware: {entry['vram']}")
            print(f"      Usage:    {entry['desc']}\n")

        choice = input("Select a model to download [1-4] or 'q' to quit: ").strip()
        if choice.lower() == 'q':
            print("Aborted.")
            sys.exit(0)

        selected = CATALOG.get(choice)
        if not selected:
            print("[!] Invalid selection.")
            sys.exit(1)

        repo_id = selected["repo_id"]
        filename = selected["filename"]

    print("\n-------------------------------------------------------")
    print(f"Downloading: {repo_id}/{filename}")
    print(f"Destination: {dest_dir.resolve()}")
    print("Supports auto-resume if interrupted.")
    print("-------------------------------------------------------\n")

    try:
        downloaded = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=str(dest_dir),
            resume_download=True,
        )
        print("\n[SUCCESS] Model downloaded successfully!")
        print(f"File: {downloaded}")
        print("\nMaxIM has automatically detected this model.")
        print("You can now select it in the model dropdown or launch it via llama-server.\n")
    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
