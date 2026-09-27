"""
Unit tests for Local Semantic Retrieval & Reranker Engine (Qwen3-Embedding & Qwen3-Reranker).
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from retrieval_engine import retrieval_engine, RetrievalEngine
from tools.vault_tool import ObsidianVaultSynapse
from five_layer_memory import five_layer_memory
from server import app

client = TestClient(app)

def test_model_discovery():
    """Verifies Qwen3-Embedding and Qwen3-Reranker models are discovered in models/embedding/."""
    embed_model = retrieval_engine.find_embedding_model()
    assert embed_model is not None
    assert embed_model.exists()
    assert "embed" in embed_model.name.lower()

    rerank_model = retrieval_engine.find_reranker_model()
    assert rerank_model is not None
    assert rerank_model.exists()
    assert "rerank" in rerank_model.name.lower()

def test_llama_binary_discovery():
    """Verifies that native llama-server binary is found."""
    bin_path = retrieval_engine.find_llama_binary()
    assert bin_path is not None
    assert bin_path.exists()

def test_retrieval_status():
    """Verifies status payload structure."""
    status = retrieval_engine.get_status()
    assert "embedding" in status
    assert "reranker" in status
    assert status["embedding"]["available"] is True
    assert status["reranker"]["available"] is True
    assert "Qwen3-Embedding" in status["embedding"]["model_name"]
    assert "Qwen3-Reranker" in status["reranker"]["model_name"]

def test_cosine_similarity():
    """Verifies cosine similarity computation."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert round(RetrievalEngine.cosine_similarity(v1, v2), 4) == 1.0

    v3 = [0.0, 1.0, 0.0]
    assert round(RetrievalEngine.cosine_similarity(v1, v3), 4) == 0.0

    v4 = [-1.0, 0.0, 0.0]
    assert round(RetrievalEngine.cosine_similarity(v1, v4), 4) == -1.0

def test_lexical_rerank_fallback():
    """Verifies fallback lexical ranker properly scores document relevance."""
    docs = [
        "NVIDIA RTX 4050 GPU VRAM governor architecture.",
        "A recipe for chocolate chip cookies with sugar.",
        "Deep learning and transformer neural networks.",
    ]
    ranked = retrieval_engine.rerank("RTX 4050 GPU VRAM", docs, top_k=2)
    assert len(ranked) == 2
    assert ranked[0]["index"] == 0
    assert "RTX 4050" in ranked[0]["document"]
    assert ranked[0]["relevance_score"] > 0

def test_hybrid_vault_search(tmp_path: Path):
    """Verifies hybrid search over isolated vault notes."""
    synapse = ObsidianVaultSynapse(vault_dir=tmp_path)
    synapse.write_note(
        title="Hardware Profile",
        content="NVIDIA RTX 4050 with 6GB VRAM and PCIe paging mitigation.",
        folder="02 - Knowledge",
    )
    synapse.write_note(
        title="Baking Guide",
        content="Flour, yeast, and sourdough bread fermentation guide.",
        folder="02 - Knowledge",
    )

    results = synapse.semantic_search_vault("RTX 4050 VRAM", max_results=5)
    assert len(results) > 0
    titles = [r["title"] for r in results]
    assert "Hardware Profile" in titles

def test_five_layer_recall_with_rerank():
    """Verifies 5-layer recall primitive supports rerank flag."""
    res = five_layer_memory.recall("TELOS LifeOS objectives", top_k=3, rerank=True)
    assert res["status"] == "success"
    assert "observations" in res["results"]
    assert "vault_notes" in res["results"]

def test_retrieval_api_endpoints():
    """Verifies FastAPI endpoints for retrieval status, rerank, and semantic search."""
    # 1. Status
    res_status = client.get("/api/retrieval/status")
    assert res_status.status_code == 200
    data = res_status.json()
    assert data["embedding"]["available"] is True
    assert data["reranker"]["available"] is True

    # 2. Rerank
    res_rerank = client.post(
        "/api/retrieval/rerank",
        json={
            "query": "Quantum computing superposition",
            "documents": [
                "Quantum computing uses qubits and quantum superposition.",
                "The cat sat lazily on the warm windowsill.",
            ],
            "top_k": 2,
        },
    )
    assert res_rerank.status_code == 200
    r_data = res_rerank.json()
    assert r_data["status"] == "success"
    assert len(r_data["results"]) == 2
    assert r_data["results"][0]["index"] == 0

    # 3. Vault Semantic Search
    res_search = client.post(
        "/api/vault/semantic-search",
        json={"query": "LifeOS TELOS", "max_results": 5},
    )
    assert res_search.status_code == 200
    s_data = res_search.json()
    assert s_data["status"] == "success"
    assert "results" in s_data
