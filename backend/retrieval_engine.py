"""
Local Semantic Retrieval & Reranker Engine for MaxIM.
Orchestrates Qwen3-Embedding (0.6B) and Qwen3-Reranker (0.6B) via native llama-server
with hardware-safe VRAM budgeting on NVIDIA RTX 4050.
Provides sub-second dense vector embeddings and neural reranking for Obsidian vault notes
and 5-layer memory recall.
"""
import os
import sys
import time
import math
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

import httpx

logger = logging.getLogger("maxim.retrieval_engine")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_MODELS_DIR = PROJECT_ROOT / "models"
EMBEDDING_PORT = int(os.getenv("MAXIM_EMBEDDING_PORT", "8085"))
RERANKER_PORT = int(os.getenv("MAXIM_RERANKER_PORT", "8086"))


class RetrievalEngine:
    def __init__(self):
        self._embed_process: Optional[subprocess.Popen] = None
        self._rerank_process: Optional[subprocess.Popen] = None
        self._embed_port = EMBEDDING_PORT
        self._rerank_port = RERANKER_PORT
        # In-memory embedding cache keyed by sha256(text)
        self._cached_embeddings: Dict[str, List[float]] = {}

    def find_embedding_model(self) -> Optional[Path]:
        """Discovers Qwen3-Embedding GGUF in models/embedding/ or models/."""
        embed_dir = PROJECT_MODELS_DIR / "embedding"
        if embed_dir.exists():
            for p in embed_dir.glob("*.gguf"):
                if "embed" in p.name.lower():
                    return p
        for p in PROJECT_MODELS_DIR.rglob("*.gguf"):
            if "embed" in p.name.lower():
                return p
        return None

    def find_reranker_model(self) -> Optional[Path]:
        """Discovers Qwen3-Reranker GGUF in models/embedding/ or models/."""
        embed_dir = PROJECT_MODELS_DIR / "embedding"
        if embed_dir.exists():
            for p in embed_dir.glob("*.gguf"):
                if "rerank" in p.name.lower():
                    return p
        for p in PROJECT_MODELS_DIR.rglob("*.gguf"):
            if "rerank" in p.name.lower():
                return p
        return None

    def find_llama_binary(self) -> Optional[Path]:
        """Locates llama-server executable via local_model_manager."""
        from local_model_manager import local_model_manager
        return local_model_manager.find_llama_binary()

    def is_server_ready(self, port: int) -> bool:
        """Pings the target port /health endpoint and checks status code."""
        try:
            with httpx.Client(timeout=1.0) as client:
                res = client.get(f"http://127.0.0.1:{port}/health")
                return res.status_code == 200
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Returns readiness and presence of embedding and reranking models."""
        embed_model = self.find_embedding_model()
        rerank_model = self.find_reranker_model()
        bin_path = self.find_llama_binary()

        return {
            "embedding": {
                "available": embed_model is not None,
                "model_name": embed_model.name if embed_model else None,
                "model_path": str(embed_model.resolve()) if embed_model else None,
                "port": self._embed_port,
                "running": self.is_server_ready(self._embed_port),
            },
            "reranker": {
                "available": rerank_model is not None,
                "model_name": rerank_model.name if rerank_model else None,
                "model_path": str(rerank_model.resolve()) if rerank_model else None,
                "port": self._rerank_port,
                "running": self.is_server_ready(self._rerank_port),
            },
            "binary_available": bin_path is not None and bin_path.exists(),
            "binary_path": str(bin_path.resolve()) if bin_path else None,
            "cached_vectors_count": len(self._cached_embeddings),
        }

    def stop_server(self, service: str = "all") -> bool:
        """Terminates embedding and/or reranker server subprocesses."""
        stopped = False
        if service in ("all", "embed") and self._embed_process:
            try:
                self._embed_process.terminate()
                self._embed_process.wait(timeout=2)
            except Exception:
                try:
                    self._embed_process.kill()
                except Exception:
                    pass
            self._embed_process = None
            stopped = True

        if service in ("all", "rerank") and self._rerank_process:
            try:
                self._rerank_process.terminate()
                self._rerank_process.wait(timeout=2)
            except Exception:
                try:
                    self._rerank_process.kill()
                except Exception:
                    pass
            self._rerank_process = None
            stopped = True

        return stopped

    def ensure_embedding_server(self, timeout_sec: float = 12.0) -> bool:
        """Ensures Qwen3-Embedding llama-server is online on port 8085 with CUDA acceleration."""
        if self.is_server_ready(self._embed_port):
            return True

        model_path = self.find_embedding_model()
        if not model_path:
            logger.warning("No embedding model (.gguf) found in models/embedding/")
            return False

        bin_path = self.find_llama_binary()
        if not bin_path or not bin_path.exists():
            logger.warning("llama-server binary not found")
            return False

        self.stop_server(service="embed")

        cmd = [
            str(bin_path),
            "-m", str(model_path.resolve()),
            "--embedding",
            "--port", str(self._embed_port),
            "-ngl", "99",
            "-c", "2048",
            "-fa", "on",
            "--host", "127.0.0.1",
        ]

        env = os.environ.copy()
        cuda_bin = Path(os.path.expanduser("~")) / ".unsloth" / "audio.cpp" / "bin"
        if cuda_bin.exists():
            env["PATH"] = f"{cuda_bin};{bin_path.parent};{env.get('PATH', '')}"
        else:
            env["PATH"] = f"{bin_path.parent};{env.get('PATH', '')}"

        logger.info(f"Starting Qwen3-Embedding server on port {self._embed_port}: {model_path.name}")
        self._embed_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            cwd=str(bin_path.parent),
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            time.sleep(0.3)
            if self.is_server_ready(self._embed_port):
                logger.info(f"Qwen3-Embedding server ready on port {self._embed_port}")
                return True
        return False

    def ensure_reranker_server(self, timeout_sec: float = 12.0) -> bool:
        """Ensures Qwen3-Reranker llama-server is online on port 8086 with CUDA acceleration."""
        if self.is_server_ready(self._rerank_port):
            return True

        model_path = self.find_reranker_model()
        if not model_path:
            logger.warning("No reranker model (.gguf) found in models/embedding/")
            return False

        bin_path = self.find_llama_binary()
        if not bin_path or not bin_path.exists():
            logger.warning("llama-server binary not found")
            return False

        self.stop_server(service="rerank")

        cmd = [
            str(bin_path),
            "-m", str(model_path.resolve()),
            "--rerank",
            "--port", str(self._rerank_port),
            "-ngl", "99",
            "-c", "2048",
            "-fa", "on",
            "--host", "127.0.0.1",
        ]

        env = os.environ.copy()
        cuda_bin = Path(os.path.expanduser("~")) / ".unsloth" / "audio.cpp" / "bin"
        if cuda_bin.exists():
            env["PATH"] = f"{cuda_bin};{bin_path.parent};{env.get('PATH', '')}"
        else:
            env["PATH"] = f"{bin_path.parent};{env.get('PATH', '')}"

        logger.info(f"Starting Qwen3-Reranker server on port {self._rerank_port}: {model_path.name}")
        self._rerank_process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
            cwd=str(bin_path.parent),
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        t0 = time.time()
        while time.time() - t0 < timeout_sec:
            time.sleep(0.3)
            if self.is_server_ready(self._rerank_port):
                logger.info(f"Qwen3-Reranker server ready on port {self._rerank_port}")
                return True
        return False

    def get_embedding(self, text: str, auto_boot: bool = False) -> Optional[List[float]]:
        """Returns 1024-dim dense embedding vector from Qwen3-Embedding."""
        if not text or not text.strip():
            return None

        # Check in-memory cache first
        cache_key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if cache_key in self._cached_embeddings:
            return self._cached_embeddings[cache_key]

        if not self.is_server_ready(self._embed_port):
            if auto_boot:
                if not self.ensure_embedding_server():
                    return None
            else:
                return None

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    f"http://127.0.0.1:{self._embed_port}/v1/embeddings",
                    json={"input": text[:2048], "model": "qwen3-embed"},
                )
                if res.status_code == 200:
                    data = res.json()
                    vec = data["data"][0]["embedding"]
                    self._cached_embeddings[cache_key] = vec
                    return vec
        except Exception as e:
            logger.debug(f"Failed to get embedding: {e}")
        return None

    def get_embeddings_batch(self, texts: List[str], auto_boot: bool = False) -> List[Optional[List[float]]]:
        """Returns embeddings for a batch of strings."""
        return [self.get_embedding(t, auto_boot=auto_boot) for t in texts]

    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """Calculates cosine similarity between two float vectors."""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None,
        auto_boot: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Reranks documents against query using Qwen3-Reranker.
        Returns list of {'index': int, 'document': str, 'relevance_score': float} sorted descending.
        """
        if not documents:
            return []
        if not query or not query.strip():
            return [{"index": i, "document": doc, "relevance_score": 1.0} for i, doc in enumerate(documents)]

        limit = top_k or len(documents)

        if not self.is_server_ready(self._rerank_port):
            if auto_boot:
                if not self.ensure_reranker_server():
                    return self._lexical_rank_fallback(query, documents, limit)
            else:
                return self._lexical_rank_fallback(query, documents, limit)

        try:
            safe_docs = [doc[:2048] for doc in documents]
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    f"http://127.0.0.1:{self._rerank_port}/v1/rerank",
                    json={
                        "query": query[:512],
                        "documents": safe_docs,
                        "model": "qwen3-rerank",
                        "top_n": limit,
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    results = []
                    for item in data.get("results", []):
                        idx = item.get("index", 0)
                        score = float(item.get("relevance_score", 0.0))
                        results.append({
                            "index": idx,
                            "document": documents[idx],
                            "relevance_score": round(score, 4),
                        })
                    return results
        except Exception as e:
            logger.debug(f"Neural rerank call failed: {e}")

        return self._lexical_rank_fallback(query, documents, limit)

    def _lexical_rank_fallback(self, query: str, documents: List[str], top_k: int) -> List[Dict[str, Any]]:
        """Fast fallback lexical overlap ranking when neural reranker is offline."""
        q_words = set(query.lower().split())
        scored = []
        for i, doc in enumerate(documents):
            d_lower = doc.lower()
            overlap = sum(1 for w in q_words if w in d_lower)
            score = round(overlap / max(1, len(q_words)), 4)
            scored.append({"index": i, "document": doc, "relevance_score": score})
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:top_k]

    def hybrid_search_vault(
        self,
        query: str,
        vault_dir: Path,
        max_results: int = 10,
        auto_boot: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid dense vector + neural reranker search across markdown notes in vault_dir.
        """
        if not query or not query.strip() or not vault_dir.exists():
            return []

        all_notes = list(vault_dir.rglob("*.md"))
        if not all_notes:
            return []

        # 1. Gather note contents
        candidates = []
        doc_texts = []
        q_lower = query.lower()

        for path in all_notes:
            try:
                text = path.read_text(encoding="utf-8")
                rel_path = path.relative_to(vault_dir).as_posix()
                snippet = ""
                for line in text.splitlines():
                    if q_lower in line.lower():
                        snippet = line.strip()
                        break
                if not snippet:
                    snippet = text[:200].strip()

                candidates.append({
                    "title": path.stem,
                    "path": rel_path,
                    "folder": path.parent.name,
                    "snippet": snippet,
                    "full_text": text,
                })
                # Provide representation for reranker
                doc_repr = f"Title: {path.stem}\nContent: {text[:800]}"
                doc_texts.append(doc_repr)
            except Exception:
                continue

        if not candidates:
            return []

        # 2. Dense Semantic Pre-filtering via Qwen3-Embedding if available
        q_vec = self.get_embedding(query, auto_boot=auto_boot)
        if q_vec:
            for cand in candidates:
                cand_vec = self.get_embedding(cand["full_text"][:1000], auto_boot=auto_boot)
                cand["similarity"] = self.cosine_similarity(q_vec, cand_vec) if cand_vec else 0.0
            candidates.sort(key=lambda c: c.get("similarity", 0.0), reverse=True)
            # Take top 20 candidates for reranking
            candidates = candidates[:20]
            doc_texts = [f"Title: {c['title']}\nContent: {c['full_text'][:800]}" for c in candidates]

        # 3. Neural Reranking via Qwen3-Reranker
        reranked = self.rerank(query, doc_texts, top_k=max_results, auto_boot=auto_boot)
        results = []
        for item in reranked:
            idx = item["index"]
            if idx < len(candidates):
                cand = candidates[idx]
                results.append({
                    "title": cand["title"],
                    "path": cand["path"],
                    "folder": cand["folder"],
                    "snippet": cand["snippet"],
                    "relevance_score": item["relevance_score"],
                })

        return results


retrieval_engine = RetrievalEngine()
