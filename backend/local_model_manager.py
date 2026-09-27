"""
MaxIM Standalone Local Model Discovery & Native Llama-Server Manager.
Enables MaxIM to run completely independently without requiring Unsloth Studio.
Supports:
1. Multi-path auto-discovery across project-local 'models/', standard HuggingFace caches, and custom env paths.
2. Built-in 1-click model downloader via huggingface_hub with automatic resume.
3. Native CUDA-accelerated llama-server process lifecycle management.
"""
import os
import re
import sys
import time
import json
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import httpx

logger = logging.getLogger("maxim.local_models")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_MODELS_DIR = PROJECT_ROOT / "models"
PROJECT_BIN_DIR = PROJECT_ROOT / "bin"
STANDALONE_PORT = 8080

# Curated catalog for zero-configuration 1-click open source onboarding
RECOMMENDED_MODELS: Dict[str, Dict[str, Any]] = {
    "qwen2.5-coder-7b": {
        "repo_id": "Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
        "filename": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "name": "Qwen 2.5 Coder 7B",
        "size_gb": 4.68,
        "vram_required": "6 GB",
        "description": "State-of-the-art coding, tool use, and general task automation",
    },
    "qwen2.5-3b": {
        "repo_id": "Qwen/Qwen2.5-3B-Instruct-GGUF",
        "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "name": "Qwen 2.5 3B",
        "size_gb": 2.1,
        "vram_required": "3 GB (Runs on CPU/Low-end GPUs)",
        "description": "Ultra-lightweight and fast local assistant",
    },
    "qwen3.5-9b-abliterated": {
        "repo_id": "lukey03/Qwen3.5-9B-abliterated-GGUF",
        "filename": "Qwen3.5-9B-abliterated-Q4_K_M.gguf",
        "name": "Qwen 3.5 9B Abliterated",
        "size_gb": 5.24,
        "vram_required": "6 GB",
        "description": "Uncensored abliterated 9B model running full GPU on RTX 4050",
    },
    "llama-3.2-3b": {
        "repo_id": "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "filename": "Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        "name": "Llama 3.2 3B Instruct",
        "size_gb": 2.02,
        "vram_required": "3 GB",
        "description": "Meta Llama 3.2 fast conversational companion",
    },
}

class LocalModelManager:
    def __init__(self, hub_dir: Optional[Path] = None, llama_bin: Optional[Path] = None):
        self.custom_hub_dir = hub_dir
        self.custom_llama_bin = llama_bin
        self._server_process: Optional[subprocess.Popen] = None
        self._active_model_path: Optional[str] = None
        self._active_port: int = STANDALONE_PORT
        # Ensure project models directory exists
        PROJECT_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    def get_search_directories(self) -> List[Path]:
        """
        Gathers all candidate model directories in priority order:
        1. Custom hub_dir (if provided in constructor)
        2. Project-local 'models/' folder
        3. Explicit MAXIM_MODELS_DIR environment variable
        4. Standard HF_HOME / HUGGINGFACE_HUB_CACHE
        5. Standard platform home cache (~/.cache/huggingface/hub)
        6. Dedicated drives (e.g. F:\\huggingface\\hub) if existing
        """
        dirs: List[Path] = []
        if self.custom_hub_dir:
            dirs.append(self.custom_hub_dir)
        dirs.append(PROJECT_MODELS_DIR)

        # Environment overrides
        env_custom = os.getenv("MAXIM_MODELS_DIR")
        if env_custom:
            dirs.append(Path(env_custom))

        env_hf = os.getenv("HF_HOME")
        if env_hf:
            dirs.append(Path(env_hf) / "hub")

        env_cache = os.getenv("HUGGINGFACE_HUB_CACHE")
        if env_cache:
            dirs.append(Path(env_cache))

        # Standard OS default (~/.cache/huggingface/hub)
        std_hf = Path.home() / ".cache" / "huggingface" / "hub"
        dirs.append(std_hf)

        # Deduplicate while preserving order and verifying existence
        seen = set()
        existing_dirs = []
        for d in dirs:
            resolved = str(d.resolve()) if d.exists() else str(d)
            if resolved not in seen and d.exists() and d.is_dir():
                seen.add(resolved)
                existing_dirs.append(d)

        return existing_dirs

    def find_llama_binary(self) -> Optional[Path]:
        """
        Locates the native llama-server executable:
        1. LLAMA_SERVER_BIN environment variable
        2. Project bin/ directory (<project_root>/bin/llama-server[.exe])
        3. System PATH (llama-server)
        4. Local Unsloth / llama.cpp build artifacts if present
        5. Standard Linux/macOS paths (/usr/local/bin, ~/.local/bin)
        """
        if self.custom_llama_bin and self.custom_llama_bin.exists():
            return self.custom_llama_bin

        env_bin = os.getenv("LLAMA_SERVER_BIN")
        if env_bin and Path(env_bin).exists():
            return Path(env_bin)

        # Check project bin directory
        proj_exe = PROJECT_BIN_DIR / ("llama-server.exe" if sys.platform == "win32" else "llama-server")
        if proj_exe.exists():
            return proj_exe

        # Check system PATH
        path_found = shutil.which("llama-server") or shutil.which("llama-server.exe")
        if path_found:
            return Path(path_found)

        # Check local development build locations
        dev_candidates = [
            Path(r"C:\Users\Sam\.unsloth\llama.cpp\build\bin\Release\llama-server.exe"),
            Path.home() / ".local" / "bin" / ("llama-server.exe" if sys.platform == "win32" else "llama-server"),
            Path("/usr/local/bin/llama-server"),
        ]
        for c in dev_candidates:
            if c.exists():
                # Ensure CUDA runtime DLLs are present alongside llama-server.exe on Windows
                if sys.platform == "win32":
                    cuda_source = Path(os.path.expanduser("~")) / ".unsloth" / "audio.cpp" / "bin"
                    if cuda_source.exists():
                        for dll_name in ("cublas64_13.dll", "cublasLt64_13.dll", "cudart64_13.dll", "cufft64_12.dll"):
                            dest = c.parent / dll_name
                            src = cuda_source / dll_name
                            if src.exists() and not dest.exists():
                                try:
                                    shutil.copy2(src, dest)
                                except Exception:
                                    pass
                return c

        return None

    def scan_models(self) -> List[Dict[str, Any]]:
        """
        Scans all candidate directories for GGUF models.
        Handles:
        1. Project-local 'models/' directory (Method B) recursively.
        2. HuggingFace Hub directory layouts (models--org--repo/snapshots/...).
        3. Flat directory style (direct .gguf files or custom subfolders).
        """
        models: List[Dict[str, Any]] = []
        seen_paths = set()

        search_dirs = self.get_search_directories()

        for base_dir in search_dirs:
            try:
                is_proj_dir = (base_dir.resolve() == PROJECT_MODELS_DIR.resolve())

                # If this is the project-local models/ folder (Method B), scan recursively for all .gguf/.GGUF files
                if is_proj_dir:
                    for ext in ("*.gguf", "*.GGUF", "**/*.gguf", "**/*.GGUF"):
                        for gguf_file in base_dir.glob(ext):
                            rel_parent = gguf_file.relative_to(base_dir).parent
                            repo_tag = str(rel_parent).replace("\\", "/") if str(rel_parent) != "." else "local"
                            self._process_gguf_file(
                                gguf_file=gguf_file,
                                repo_id=repo_tag,
                                display_hint=gguf_file.stem,
                                models=models,
                                seen_paths=seen_paths,
                                is_project_local=True,
                            )
                    continue

                # 1. HuggingFace Hub style (models--*)
                for model_dir in base_dir.glob("models--*"):
                    if not model_dir.is_dir():
                        continue
                    dir_name = model_dir.name
                    parts = dir_name.replace("models--", "").split("--", 1)
                    repo_id = f"{parts[0]}/{parts[1]}" if len(parts) == 2 else dir_name

                    for gguf_file in model_dir.glob("**/*.gguf"):
                        self._process_gguf_file(gguf_file, repo_id, parts[1] if len(parts) == 2 else dir_name, models, seen_paths)
                    for gguf_file in model_dir.glob("**/*.GGUF"):
                        self._process_gguf_file(gguf_file, repo_id, parts[1] if len(parts) == 2 else dir_name, models, seen_paths)

                # 2. Flat directory style (direct .gguf files or non-hub subfolders)
                for gguf_file in list(base_dir.glob("*.gguf")) + list(base_dir.glob("*.GGUF")):
                    self._process_gguf_file(gguf_file, "local", gguf_file.stem, models, seen_paths)

                for sub_dir in base_dir.iterdir():
                    if sub_dir.is_dir() and not sub_dir.name.startswith("models--") and not sub_dir.name.startswith("."):
                        for gguf_file in list(sub_dir.glob("*.gguf")) + list(sub_dir.glob("*.GGUF")):
                            self._process_gguf_file(gguf_file, sub_dir.name, gguf_file.stem, models, seen_paths)
            except Exception as e:
                logger.debug(f"Error scanning directory {base_dir}: {e}")

        # Sort: Project-local models first (Method B), then LLMs, then descending by file size
        models.sort(key=lambda m: (
            0 if m.get("is_project_local") else 1,
            0 if m["category"] == "llm" else 1,
            -m["size_bytes"]
        ))
        return models

    def _process_gguf_file(
        self,
        gguf_file: Path,
        repo_id: str,
        display_hint: str,
        models: List[Dict[str, Any]],
        seen_paths: set,
        is_project_local: bool = False,
    ):
        file_path_str = str(gguf_file.resolve())
        if file_path_str in seen_paths:
            return
        file_name = gguf_file.name

        # Skip incomplete downloads
        if ".incomplete" in file_name or file_name.endswith(".tmp"):
            return

        seen_paths.add(file_path_str)

        lower_name = file_name.lower()
        parent_name = gguf_file.parent.name.lower()

        # Check if file contains diffusion weights (diffusion models cannot run in llama-server)
        is_diffusion = False
        try:
            with open(gguf_file, "rb") as f:
                header_bytes = f.read(1024)
                if b"diffusion_model" in header_bytes or b"diffusion" in header_bytes:
                    is_diffusion = True
        except Exception:
            pass

        # Semantic Capability Classification based on filename and folder
        if "mmproj" in lower_name or "mtp" in lower_name:
            category = "projector"
            category_name = "Multimodal Projector"
            category_icon = "🔌"
            role_desc = "Multimodal visual projection adapter weights"
        elif "rerank" in lower_name or parent_name in ("rerank", "reranker", "rerankers"):
            category = "reranker"
            category_name = "Semantic Reranker"
            category_icon = "🎯"
            role_desc = "High-precision cross-encoder search reranking"
        elif "embed" in lower_name or parent_name in ("embed", "embedding", "embeddings"):
            category = "embedding"
            category_name = "Vector Embedding"
            category_icon = "📐"
            role_desc = "Semantic text embedding for vector retrieval"
        elif is_diffusion or "diffusion" in lower_name:
            category = "diffusion"
            category_name = "Image Generation (Diffusion)"
            category_icon = "🎨"
            role_desc = "Text-to-image neural image synthesis"
        elif parent_name in ("vision", "image") or any(k in lower_name for k in ("image", "vision", "vl-", "-vl", "llava", "minicpm-v")):
            category = "vision"
            category_name = "Vision & Multimodal"
            category_icon = "👁️"
            role_desc = "Visual inspection, screen analysis, and multimodal document analysis"
        elif parent_name in ("asr", "stt") or any(k in lower_name for k in ("asr", "whisper", "speech-to-text", "transcribe")):
            category = "asr"
            category_name = "Voice-to-Text (ASR)"
            category_icon = "🎙️"
            role_desc = "Microphone speech recognition and audio transcription"
        elif parent_name in ("tts", "voice") or any(k in lower_name for k in ("tts", "voice", "text-to-speech", "bark")):
            category = "tts"
            category_name = "Text-to-Voice (TTS)"
            category_icon = "🔊"
            role_desc = "Neural speech synthesis and realistic vocal audio generation"
        else:
            category = "llm"
            category_name = "All-Rounder Reasoning"
            category_icon = "🧠"
            role_desc = "General reasoning, coding, autonomous tool use, and TELOS task execution"

        # Extract quantization
        quant_match = re.search(r"(Q\d_[A-Z0-9_]+|F16|F32|BF16|UD-Q\d_[A-Z0-9_]+)", file_name, re.I)
        quant = quant_match.group(1) if quant_match else "GGUF"

        try:
            size_bytes = gguf_file.stat().st_size
            size_gb = round(size_bytes / (1024 ** 3), 2)
        except Exception:
            size_bytes = 0
            size_gb = 0.0

        clean_name = display_hint.replace("-GGUF", "").replace("-gguf", "").replace("-", " ")
        is_active = (file_path_str == self._active_model_path)

        # Check if located in project models/ folder
        try:
            in_proj = is_project_local or (PROJECT_MODELS_DIR.resolve() in gguf_file.resolve().parents)
        except Exception:
            in_proj = is_project_local

        subfolder_tag = f"models/{parent_name}" if in_proj and parent_name in ("llm", "vision", "asr", "tts", "embedding") else "models/"

        models.append({
            "id": f"{repo_id}:{file_name}",
            "repo_id": repo_id,
            "name": clean_name,
            "file_name": file_name,
            "path": file_path_str,
            "size_gb": size_gb,
            "size_bytes": size_bytes,
            "quant": quant,
            "category": category,
            "category_name": category_name,
            "category_icon": category_icon,
            "role_description": role_desc,
            "subfolder": subfolder_tag,
            "is_active": is_active,
            "is_project_local": in_proj,
            "location": subfolder_tag if in_proj else "hub_cache",
            "source": f"MaxIM {subfolder_tag}" if in_proj else "External Hub",
            "is_diffusion": is_diffusion,
        })

    def download_model(
        self,
        repo_id: str,
        filename: str,
        target_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Downloads a GGUF model directly from HuggingFace with automatic resume.
        Saves into project-local models/ by default.
        """
        from huggingface_hub import hf_hub_download

        dest_dir = target_dir or PROJECT_MODELS_DIR
        dest_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting download of {repo_id}/{filename} into {dest_dir}...")
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=str(dest_dir),
            resume_download=True,
        )

        return {
            "status": "success",
            "repo_id": repo_id,
            "filename": filename,
            "path": downloaded_path,
        }

    def is_server_ready(self, port: Optional[int] = None) -> bool:
        """Pings the target llama-server /health endpoint and verifies status is 200 OK (model fully loaded into VRAM)."""
        p = port or self._active_port
        try:
            with httpx.Client(timeout=1.5) as client:
                res = client.get(f"http://127.0.0.1:{p}/health")
                return res.status_code == 200
        except Exception:
            return False

    def is_server_alive(self, port: Optional[int] = None) -> bool:
        """Pings the target llama-server /health endpoint (accepts 200 OK or 503 loading)."""
        p = port or self._active_port
        try:
            with httpx.Client(timeout=1.5) as client:
                res = client.get(f"http://127.0.0.1:{p}/health")
                return res.status_code in (200, 503)
        except Exception:
            return False

    def stop_server(self) -> bool:
        """Terminates any active llama-server managed by this process."""
        if self._server_process:
            try:
                self._server_process.terminate()
                self._server_process.wait(timeout=3)
            except Exception:
                try:
                    self._server_process.kill()
                except Exception:
                    pass
            self._server_process = None
            self._active_model_path = None
            return True
        return False

    def find_matching_projector(self, model_path: str) -> Optional[Path]:
        """
        Finds a matching mmproj file for a vision GGUF model in the same directory
        or the project models/vision folder.
        """
        p = Path(model_path)
        candidates: List[Path] = []
        if p.parent.exists():
            candidates.extend(list(p.parent.glob("*mmproj*.gguf")) + list(p.parent.glob("*mmproj*.GGUF")))
        vision_dir = PROJECT_MODELS_DIR / "vision"
        if vision_dir.exists():
            candidates.extend(list(vision_dir.glob("*mmproj*.gguf")) + list(vision_dir.glob("*mmproj*.GGUF")))

        if not candidates:
            return None

        # Prioritize matching model family/name
        model_stem_clean = p.stem.lower().replace("-gguf", "").replace("-q4_k_m", "").replace("-instruct", "")
        for c in candidates:
            c_stem = c.stem.lower()
            if any(part in c_stem for part in model_stem_clean.split("-") if len(part) >= 3):
                return c
        return candidates[0]

    def calculate_hardware_safe_params(
        self,
        model_path: str,
        is_vision: bool = False,
    ) -> Tuple[int, int]:
        """
        Calculates optimal n_gpu_layers and context_length to maximize token generation
        speed on the host GPU (e.g. RTX 4050 6GB VRAM) while preventing Windows CUDA
        driver PCIe RAM paging thrashing.
        """
        try:
            from hardware_governor import hardware_governor
            telemetry = hardware_governor.get_telemetry()
            vram_total_mb = telemetry.vram_total_mb or 0.0
        except Exception:
            vram_total_mb = 6144.0

        p = Path(model_path)
        size_gb = (p.stat().st_size / (1024 ** 3)) if p.exists() else 3.5

        # For systems with <= 6GB VRAM (e.g. RTX 4050 Laptop GPU with ~5100MB usable budget):
        if vram_total_mb > 0 and vram_total_mb <= 6400:
            if size_gb >= 5.0:
                # 9B class model (e.g. Qwen 3.5 9B at 5.63 GB)
                # Keep total memory strictly under 5000 MB: budget context to 4k and offload 28 layers
                # so the top 4 layers sit in system RAM cleanly without CUDA thrashing
                logger.info(f"VRAM Governor (RTX 4050 6GB): Budgeting 9B model ({size_gb:.2f}GB) with -ngl 28, -c 4096 to prevent PCIe thrashing")
                return 28, 4096
            elif is_vision or "vl" in p.name.lower():
                # Vision model (e.g. Qwen 3-VL 4B at 2.5 GB + mmproj 0.8 GB = 3.3 GB)
                # Full GPU offload with 8192 context (leaves 1.8 GB headroom for Windows DWM)
                logger.info(f"VRAM Governor (RTX 4050 6GB): Allocating Vision model ({size_gb:.2f}GB) with -ngl 99, -c 8192")
                return 99, 8192
            elif size_gb >= 3.4:
                # High-quant 4B model (e.g. Qwen 3.5 4B Q6_K at 3.64 GB)
                logger.info(f"VRAM Governor (RTX 4050 6GB): Allocating 4B Q6 model ({size_gb:.2f}GB) with -ngl 99, -c 8192")
                return 99, 8192
            else:
                # Lightweight 3B/4B model (e.g. Qwen 3.5 4B UD at 2.9 GB, Gemma 4)
                logger.info(f"VRAM Governor (RTX 4050 6GB): Allocating lightweight model ({size_gb:.2f}GB) with -ngl 99, -c 16384")
                return 99, 16384

        # For GPUs with > 8GB VRAM or default:
        return 99, 16384

    def start_server(
        self,
        model_path_or_id: str,
        port: int = STANDALONE_PORT,
        context_length: int = 16384,
        n_gpu_layers: int = 99,
    ) -> Dict[str, Any]:
        """
        Launches native llama-server with CUDA/Metal/CPU acceleration on the specified port.
        """
        bin_path = self.find_llama_binary()
        if not bin_path or not bin_path.exists():
            raise FileNotFoundError(
                "Native llama-server binary not found. Please install llama.cpp or drop the prebuilt "
                "binary into the 'bin/' folder: https://github.com/ggml-org/llama.cpp/releases"
            )

        # Resolve model path
        resolved_path = model_path_or_id
        if not Path(model_path_or_id).exists():
            models = self.scan_models()
            for m in models:
                if m["id"] == model_path_or_id or m["repo_id"] == model_path_or_id or m["file_name"] == model_path_or_id:
                    resolved_path = m["path"]
                    break

        if not Path(resolved_path).exists():
            raise FileNotFoundError(f"Target GGUF model file not found at '{resolved_path}'")

        self.stop_server()

        # Clean up any orphaned llama-server processes on Windows
        if sys.platform == "win32":
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", "llama-server.exe"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                time.sleep(0.3)
            except Exception:
                pass

        # Check if target model is a vision model requiring mmproj projector pairing
        model_file_lower = Path(resolved_path).name.lower()
        parent_dir_lower = Path(resolved_path).parent.name.lower()
        is_vision = parent_dir_lower in ("vision", "image") or any(k in model_file_lower for k in ("vl", "vision", "image"))
        projector_path = self.find_matching_projector(resolved_path) if is_vision else None

        # Calculate hardware-safe parameters for RTX 4050 (prevents PCIe memory paging)
        safe_ngl, safe_ctx = self.calculate_hardware_safe_params(resolved_path, is_vision=bool(projector_path))
        eff_ngl = safe_ngl if n_gpu_layers == 99 else n_gpu_layers
        eff_ctx = safe_ctx if context_length == 16384 else context_length

        cmd = [
            str(bin_path),
            "-m", resolved_path,
            "-ngl", str(eff_ngl),
            "-c", str(eff_ctx),
            "-fa", "on",
            "--parallel", "1",
            "--reasoning-budget", "0",
            "--port", str(port),
            "--host", "127.0.0.1",
        ]

        if projector_path and projector_path.exists():
            cmd.extend(["--mmproj", str(projector_path.resolve())])
            logger.info(f"Vision Projector paired: {projector_path.name}")

        logger.info(f"Launching standalone llama-server on port {port}: {' '.join(cmd)}")
        
        env = os.environ.copy()
        cuda_bin = Path(os.path.expanduser("~")) / ".unsloth" / "audio.cpp" / "bin"
        if cuda_bin.exists():
            env["PATH"] = f"{cuda_bin};{bin_path.parent};{env.get('PATH', '')}"
        else:
            env["PATH"] = f"{bin_path.parent};{env.get('PATH', '')}"

        self._server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            cwd=str(bin_path.parent),
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        self._active_model_path = resolved_path
        self._active_port = port

        t0 = time.time()
        ready = False
        while time.time() - t0 < 30:
            time.sleep(0.5)
            if self.is_server_ready(port):
                ready = True
                break

        return {
            "status": "started" if ready else "initializing",
            "model_path": resolved_path,
            "port": port,
            "base_url": f"http://127.0.0.1:{port}/v1",
            "context_length": context_length,
            "gpu_layers": n_gpu_layers,
            "pid": self._server_process.pid if self._server_process else None,
        }

    def open_models_directory(self) -> Dict[str, Any]:
        """Opens the project models/ directory in the native OS file explorer."""
        PROJECT_MODELS_DIR.mkdir(parents=True, exist_ok=True)
        dir_str = str(PROJECT_MODELS_DIR.resolve())
        try:
            if sys.platform == "win32":
                os.startfile(dir_str)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", dir_str])
            else:
                subprocess.Popen(["xdg-open", dir_str])
            return {"status": "opened", "path": dir_str}
        except Exception as e:
            logger.error(f"Failed to open models folder: {e}")
            return {"status": "error", "error": str(e), "path": dir_str}

    def select_best_model(
        self,
        task_type: str = "auto",
        has_image: bool = False,
        has_audio: bool = False,
        query: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        Autonomously selects the optimal local GGUF model based on task demands:
        - Image analysis / Image-to-image / OCR -> 'vision' category (models/vision/)
        - Audio transcription / Speech recognition -> 'asr' category (models/asr/)
        - Speech synthesis / Neural voice -> 'tts' category (models/tts/)
        - General reasoning / coding / autonomous ReAct agent -> 'llm' category (models/llm/)

        Within the category, ranks models by:
        1. Project-local folder storage (models/<category>/ prioritized over external cache)
        2. Parameter size and architecture capability
        3. Quantization quality
        """
        all_models = self.scan_models()
        if not all_models:
            return None

        task_lower = (task_type or "auto").strip().lower()
        target_category = "llm"

        if has_image or task_lower in ("vision", "image", "image_to_image", "multimodal", "ocr", "visual"):
            target_category = "vision"
        elif has_audio or task_lower in ("asr", "stt", "speech_to_text", "voice_to_text", "audio", "transcribe"):
            target_category = "asr"
        elif task_lower in ("tts", "voice", "text_to_speech", "text_to_voice", "synthesize", "speech"):
            target_category = "tts"
        elif task_lower in ("llm", "chat", "code", "coding", "reasoning", "general", "agent"):
            target_category = "llm"
        elif task_lower == "auto":
            # 1. Autonomous Model Capability Evaluation via Laya
            try:
                try:
                    from backend.decision_engine import decision_engine
                except ImportError:
                    from decision_engine import decision_engine

                connected_cloud = []
                try:
                    from router import model_router
                    connected_cloud = model_router.get_connected_cloud_providers()
                except Exception:
                    pass

                running_path = None
                if self.is_server_ready(self._active_port):
                    r_info = self.get_running_model_info(self._active_port)
                    if r_info and r_info.get("id"):
                        running_path = r_info["id"]

                runnable = [m for m in all_models if m.get("category") not in ("diffusion", "projector", "embedding", "reranker")]
                laya_decision = decision_engine.select_suitable_model(
                    query=query,
                    task_type=task_type,
                    has_image=has_image,
                    has_audio=has_audio,
                    candidates=runnable,
                    cloud_providers=connected_cloud,
                    running_model_path=running_path,
                )
                if laya_decision and laya_decision.full_candidate_info:
                    selected = dict(laya_decision.full_candidate_info)
                    cat_map = {
                        "vision": "vision",
                        "asr": "asr",
                        "tts": "tts",
                        "coding": "llm",
                        "deep_reasoning": "llm",
                        "browsing": "llm",
                        "creative": "llm",
                        "chat": "llm",
                    }
                    selected["routed_category"] = cat_map.get(laya_decision.task_domain, "llm")
                    selected["selection_reason"] = laya_decision.reason
                    selected["laya_decision"] = {
                        "task_domain": laya_decision.task_domain,
                        "complexity": laya_decision.complexity,
                        "capability_score": laya_decision.capability_score,
                        "capabilities": laya_decision.model_capabilities,
                        "is_neural": laya_decision.is_neural,
                    }
                    logger.info(f"Laya Model Selector: {laya_decision.reason}")
                    return selected
            except Exception as laya_err:
                logger.warning(f"Laya model selection fallback: {laya_err}")

            # 2. Resilient Heuristic Fallback
            q_clean = (query or "").lower()
            if any(k in q_clean for k in (
                "image", "picture", "photo", "screenshot", "chart", "diagram", "ocr",
                "visual inspection", "look at this", "look at the image", "image to image",
                "image-to-image", "create image", "creating image", "generate image",
                "generating image", "find image", "finding image", "see image", "seeing image",
                "see an image", "view image", "draw", "render image", "visualize"
            )):
                target_category = "vision"
            elif any(k in q_clean for k in ("speech to text", "voice to text", "transcribe", "listen to audio", "audio to text", "transcription")):
                target_category = "asr"
            elif any(k in q_clean for k in ("text to voice", "text to speech", "speak this", "read aloud", "say aloud", "voice output", "tts", "synthesize voice")):
                target_category = "tts"
            else:
                target_category = "llm"

        # Only consider runnable models (diffusion, embedding, and projector weights cannot run as llama-server text endpoints)
        runnable_models = [m for m in all_models if m.get("category") not in ("diffusion", "projector", "embedding", "reranker")]
        candidates = [m for m in runnable_models if m.get("category") == target_category]
        # Graceful fallback: if no model exists for auxiliary category, fallback to all-rounder LLM
        if not candidates and target_category != "llm":
            candidates = [m for m in runnable_models if m.get("category") == "llm"]
        if not candidates:
            candidates = runnable_models or all_models

        # Incorporate connected cloud providers if configured with valid API keys
        if target_category in ("llm", "vision"):
            try:
                from router import model_router
                connected_cloud = model_router.get_connected_cloud_providers()
                for cp in connected_cloud:
                    candidates.append({
                        "id": f"cloud:{cp['provider']}:{cp['model_name']}",
                        "repo_id": cp["provider"],
                        "name": f"{cp['name']} ({cp['model_name']})",
                        "file_name": cp["model_name"],
                        "path": f"cloud:{cp['provider']}",
                        "size_gb": 0.0,
                        "size_bytes": 0,
                        "quant": "Cloud API",
                        "category": target_category,
                        "category_name": f"Cloud {target_category.upper()}",
                        "category_icon": "☁️",
                        "role_description": f"Frontier cloud intelligence via {cp['name']}",
                        "subfolder": "cloud",
                        "is_project_local": False,
                        "is_cloud": True,
                        "provider": cp["provider"],
                        "location": "cloud",
                        "source": f"Cloud API ({cp['name']})",
                    })
            except Exception:
                pass
                pass

        running_path = None
        if self.is_server_ready(self._active_port):
            r_info = self.get_running_model_info(self._active_port)
            if r_info and r_info.get("id"):
                running_path = r_info["id"]

        def score_candidate(m: Dict[str, Any]) -> float:
            score = 0.0
            if m.get("is_project_local"):
                score += 100.0

            if m.get("is_cloud"):
                q_text = (query or "").lower()
                prov_str = f"{m.get('provider', '')} {m.get('name', '')} {m.get('file_name', '')}".lower()
                is_cloud_request = any(k in q_text for k in ("cloud", "frontier", "claude", "gpt-4", "gpt4", "gemini 2", "deepseek", "sonnet", "o1", "o3", "r1"))
                prov_name = m.get('provider', '').lower()
                is_named_prov = (
                    (prov_name and prov_name in q_text)
                    or ("claude" in q_text and "anthropic" in prov_str)
                    or ("gpt" in q_text and "openai" in prov_str)
                    or ("gemini" in q_text and "google" in prov_str)
                    or ("deepseek" in q_text and "deepseek" in prov_str)
                )
                is_deep_architecture = any(k in q_text for k in ("comprehensive architecture", "formal proof", "enterprise security audit", "large scale migration"))
                
                if is_cloud_request or is_named_prov:
                    score += 450.0
                    if is_named_prov:
                        score += 50.0
                elif is_deep_architecture or len(q_text.split()) > 60:
                    score += 190.0
                elif not any(cand.get("is_project_local") for cand in candidates if not cand.get("is_cloud")):
                    score += 150.0
                else:
                    # Keep local models prioritized for normal prompts
                    score += 10.0
                return score

            name_lower = f"{m.get('name', '')} {m.get('file_name', '')}".lower()

            if target_category == "vision":
                if "image" in name_lower or "vl" in name_lower:
                    score += 50.0
            elif target_category == "asr":
                if "whisper" in name_lower or "asr" in name_lower:
                    score += 50.0
            elif target_category == "tts":
                if "tts" in name_lower or "voice" in name_lower:
                    score += 50.0
            elif target_category == "llm":
                q_text = (query or "").lower()
                is_coding = any(k in q_text for k in (
                    "code", "coding", "python", "typescript", "javascript", "function",
                    "bug", "debug", "refactor", "error", "traceback", "sql", "git",
                    "api", "endpoint", "class", "async", "def ", "const ", "impl", "regex"
                ))
                is_deep_reasoning = any(k in q_text for k in (
                    "analyze", "analysis", "architecture", "plan", "complex", "strategy",
                    "design", "math", "proof", "evaluate", "compare", "tradeoff", "system",
                    "security", "audit", "philosophical", "deep", "uncensored"
                )) or len(q_text.split()) > 40
                is_quick_chat = any(k in q_text for k in (
                    "hi", "hello", "hey", "who are you", "what can you do", "help",
                    "quick", "brief", "short", "fast", "thanks", "ok"
                )) and len(q_text.split()) < 15

                if is_coding:
                    # Coding / development tasks: prioritize specialized coder models or high-quant precision models
                    if "coder" in name_lower:
                        score += 60.0
                    elif "q6_k" in name_lower or "q8" in name_lower:
                        score += 45.0
                    elif "9b" in name_lower:
                        score += 40.0
                    else:
                        score += 25.0
                elif is_deep_reasoning:
                    # Deep reasoning / multi-step planning / complex architecture: prioritize maximum parameter capacity (9B)
                    if "9b" in name_lower:
                        score += 60.0
                    elif "7b" in name_lower or "8b" in name_lower:
                        score += 40.0
                    elif "4b" in name_lower:
                        score += 30.0
                    else:
                        score += 20.0
                elif is_quick_chat:
                    # Quick conversational queries: prioritize ultra-lightweight, low-latency models (gemma 4 E4B, fast 4B)
                    if "gemma" in name_lower or "e4b" in name_lower:
                        score += 55.0
                    elif "4b-ud" in name_lower or "4b" in name_lower:
                        score += 45.0
                    elif "9b" in name_lower:
                        score += 25.0
                else:
                    # General balanced reasoning: prioritize top parameter model
                    if "9b" in name_lower:
                        score += 40.0
                    elif "4b-q6_k" in name_lower:
                        score += 35.0
                    elif "4b" in name_lower:
                        score += 30.0
                    else:
                        score += 20.0

            quant = str(m.get("quant", "")).upper()
            if "Q4_K_M" in quant or "Q5" in quant or "Q6" in quant or "Q8" in quant:
                score += 15.0
            elif "F16" in quant or "BF16" in quant:
                score += 10.0

            score += min(float(m.get("size_gb", 0)), 15.0)

            # Warm Model Affinity: If this model is ALREADY running on llama-server,
            # grant it a massive bonus (+200.0) so we never dump VRAM and reload between turns
            if running_path and (m.get("path") == running_path or Path(m.get("path", "")).name == Path(running_path).name):
                score += 200.0

            return score

        candidates.sort(key=score_candidate, reverse=True)
        selected = dict(candidates[0])
        selected["routed_category"] = target_category
        selected["selection_reason"] = (
            f"Autonomous routing: Selected {selected.get('category_name', target_category)} "
            f"model '{selected.get('file_name')}' for {target_category.upper()} intent"
        )
        return selected

    def get_running_model_info(self, port: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Queries /v1/models on the running llama-server to determine what model is currently loaded."""
        p = port or self._active_port
        try:
            with httpx.Client(timeout=1.5) as client:
                res = client.get(f"http://127.0.0.1:{p}/v1/models")
                if res.status_code == 200:
                    data = res.json()
                    if data.get("data") and len(data["data"]) > 0:
                        return data["data"][0]
        except Exception:
            pass
        return None

    def ensure_model_running(self, model_identifier: Optional[str] = None) -> Dict[str, Any]:
        """
        Ensures a native llama-server is online with the requested model.
        If already running with the target model, returns status without restarting.
        If stopped or running a different model, restarts with the requested model.
        """
        all_models = self.scan_models()
        if not all_models:
            raise FileNotFoundError("No local GGUF models detected in models/ or cache directories.")

        is_ready = self.is_server_ready(self._active_port)
        if is_ready:
            running_info = self.get_running_model_info(self._active_port)
            running_path = running_info.get("id", "") if running_info else ""
            if running_path:
                self._active_model_path = running_path

            # If user selected auto / local:auto (or no explicit model given)
            # and a reasoning model is already hot in VRAM, PRESERVE IT!
            # Never restart the server and incur a 10-second weight reload!
            if not model_identifier or model_identifier in ("auto", "local:auto"):
                if running_path:
                    running_name = Path(running_path).name
                    logger.debug(f"llama-server already running on port {self._active_port} with '{running_name}'. Preserving warm model.")
                    return {
                        "status": "already_running",
                        "model": {"path": running_path, "name": running_name, "file_name": running_name},
                        "port": self._active_port,
                        "base_url": f"http://127.0.0.1:{self._active_port}/v1",
                    }

        target_model = None
        if model_identifier and model_identifier not in ("auto", "local:auto"):
            clean_id = model_identifier.replace("local:", "")
            for m in all_models:
                if (
                    m["id"] == clean_id
                    or m["repo_id"] == clean_id
                    or m["file_name"] == clean_id
                    or m["name"].lower() == clean_id.lower()
                    or m["path"] == clean_id
                    or clean_id.endswith(m["file_name"])
                ):
                    target_model = m
                    break

        if not target_model:
            target_model = self.select_best_model(task_type="auto")
            if not target_model:
                target_model = all_models[0]

        if is_ready and (
            self._active_model_path == target_model["path"]
            or (self._active_model_path and Path(self._active_model_path).name == Path(target_model["path"]).name)
        ):
            return {
                "status": "already_running",
                "model": target_model,
                "port": self._active_port,
                "base_url": f"http://127.0.0.1:{self._active_port}/v1",
            }

        # If target model is a vision/diffusion asset that cannot run as a llama-server text endpoint,
        # ensure the text reasoning model is online on port 8080 so tool execution and turns succeed.
        if target_model.get("category") == "vision" and target_model.get("is_diffusion"):
            if is_ready:
                return {
                    "status": "already_running",
                    "model": target_model,
                    "port": self._active_port,
                    "base_url": f"http://127.0.0.1:{self._active_port}/v1",
                }
            llm_target = self.select_best_model(task_type="llm")
            if llm_target:
                return self.start_server(llm_target["path"], port=self._active_port)

        res = self.start_server(target_model["path"], port=self._active_port)
        if not self.is_server_ready(self._active_port):
            logger.warning(
                f"Failed to start target model '{target_model.get('name')}' on port {self._active_port}. "
                "Attempting automatic fallback to verified reasoning LLM..."
            )
            fallback_models = [
                m for m in all_models
                if m.get("category") == "llm" and m.get("path") != target_model.get("path")
            ]
            if fallback_models:
                res = self.start_server(fallback_models[0]["path"], port=self._active_port)
        return res

    def get_status(self) -> Dict[str, Any]:
        """Returns the current execution telemetry of the standalone model manager."""
        running = self.is_server_alive(self._active_port)
        search_dirs = [str(p) for p in self.get_search_directories()]
        return {
            "server_running": running,
            "active_port": self._active_port,
            "base_url": f"http://127.0.0.1:{self._active_port}/v1" if running else None,
            "active_model_path": self._active_model_path,
            "llama_binary_path": str(self.find_llama_binary()) if self.find_llama_binary() else None,
            "llama_binary_available": bool(self.find_llama_binary()),
            "search_directories": search_dirs,
            "recommended_catalog": RECOMMENDED_MODELS,
        }

local_model_manager = LocalModelManager()
