"""
Unit tests for LocalModelManager and Standalone Local Model Endpoints.
Verifies auto-discovery of F:\\huggingface\\hub GGUF models and API endpoints.
"""
import pytest
from pathlib import Path
from local_model_manager import LocalModelManager, local_model_manager
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_local_model_manager_binary_discovery():
    mgr = LocalModelManager()
    bin_path = mgr.find_llama_binary()
    assert bin_path is not None
    assert bin_path.exists()
    assert "llama-server" in bin_path.name.lower()

def test_local_model_manager_scan():
    mgr = LocalModelManager()
    models = mgr.scan_models()
    assert isinstance(models, list)
    assert len(models) > 0
    
    # Verify Qwen 9B is detected in models/llm/
    qwen = next((m for m in models if "Qwen3.5-9B-abliterated" in m["file_name"]), None)
    assert qwen is not None
    assert qwen["quant"] == "Q4_K_M"
    assert qwen["category"] == "llm"
    assert qwen["is_project_local"] is True
    assert qwen["location"] == "models/llm"

    # Verify Vision, ASR, and TTS capability folders
    vision = next((m for m in models if m["category"] == "vision"), None)
    assert vision is not None
    assert vision["location"] == "models/vision"

    asr = next((m for m in models if m["category"] == "asr"), None)
    assert asr is not None
    assert asr["location"] == "models/asr"

    tts = next((m for m in models if m["category"] == "tts"), None)
    assert tts is not None
    assert tts["location"] == "models/tts"

def test_local_model_manager_select_best():
    mgr = LocalModelManager()
    
    # All-Rounder LLM
    best_llm = mgr.select_best_model(task_type="llm")
    assert best_llm is not None
    assert best_llm["category"] == "llm"
    assert ("9B" in best_llm["file_name"] or "4B" in best_llm["file_name"])

    # Vision model
    best_vision = mgr.select_best_model(task_type="vision")
    assert best_vision is not None
    assert best_vision["category"] == "vision"

    # Audio ASR model
    best_asr = mgr.select_best_model(has_audio=True)
    assert best_asr is not None
    assert best_asr["category"] == "asr"

    # Speech TTS model
    best_tts = mgr.select_best_model(task_type="tts")
    assert best_tts is not None
    assert best_tts["category"] == "tts"

def test_select_best_endpoint():
    resp = client.post("/api/local/select-best", json={"task_type": "vision"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["selected_model"]["category"] == "vision"
    assert data["routed_category"] == "vision"

def test_local_models_endpoint():
    resp = client.get("/api/local/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "models" in data
    assert len(data["models"]) > 0
    assert "telemetry" in data

def test_local_status_endpoint():
    resp = client.get("/api/local/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "llama_binary_available" in data
    assert data["llama_binary_available"] is True

def test_method_b_drag_and_drop_discovery(tmp_path):
    """Verifies that any .gguf dragged into models/ is detected and prioritized."""
    from local_model_manager import PROJECT_MODELS_DIR
    test_gguf = PROJECT_MODELS_DIR / "custom-assistant-Q4_K_M.gguf"
    try:
        # Create a dummy 1KB GGUF file to simulate user drag-and-drop
        test_gguf.write_bytes(b"GGUF" + b"\x00" * 1024)
        
        mgr = LocalModelManager()
        models = mgr.scan_models()
        
        # Check that the dragged model is detected
        match = next((m for m in models if m["file_name"] == "custom-assistant-Q4_K_M.gguf"), None)
        # Verify it is identified as project-local in models/
        assert match["is_project_local"] is True
        assert match["location"] == "models/"
    finally:
        if test_gguf.exists():
            test_gguf.unlink()

def test_open_models_folder_endpoint():
    resp = client.post("/api/local/open-folder")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("opened", "error")
    assert "models" in data["path"]

def test_vision_autonomous_routing_on_image_query_and_attachment():
    """Verifies that vision model is automatically selected when giving, creating, or seeing images."""
    mgr = LocalModelManager()
    
    # 1. When image attachment is present
    routed_attach = mgr.select_best_model(has_image=True)
    assert routed_attach is not None
    assert routed_attach["category"] == "vision"
    
    # 2. When creating/generating image
    routed_gen = mgr.select_best_model(task_type="auto", query="Please generate an image of a futuristic neon city")
    assert routed_gen is not None
    assert routed_gen["category"] == "vision"
    
    # 3. When finding and seeing an image
    routed_see = mgr.select_best_model(task_type="auto", query="Can you find and see this image for me?")
    assert routed_see is not None
    assert routed_see["category"] == "vision"

    # 4. Standard reasoning prompt should route to LLM
    routed_llm = mgr.select_best_model(task_type="auto", query="Write a python async generator for SSE streaming")
    assert routed_llm is not None
    assert routed_llm["category"] == "llm"

def test_cloud_model_connection_and_auto_routing():
    """Verifies that connected cloud providers are discovered and can participate in auto-routing."""
    from router import model_router
    # Temporarily simulate a connected Anthropic or OpenAI API key
    orig_key = model_router.providers["anthropic"].api_key
    try:
        model_router.providers["anthropic"].api_key = "sk-ant-test-live-key"
        connected = model_router.get_connected_cloud_providers()
        assert any(c["provider"] == "anthropic" for c in connected)

        mgr = LocalModelManager()
        # Explicit cloud / frontier query should route to cloud
        routed_cloud = mgr.select_best_model(
            task_type="auto",
            query="Use Claude to design a formal security audit of our smart contract",
        )
        assert routed_cloud is not None
        assert routed_cloud.get("is_cloud") is True
        assert routed_cloud.get("provider") == "anthropic"

        # Standard local coding prompt should still prefer local model for privacy and speed
        routed_local = mgr.select_best_model(
            task_type="auto",
            query="Write a python helper function to format timestamps",
        )
        assert routed_local is not None
        assert routed_local.get("is_cloud") is not True
    finally:
        model_router.providers["anthropic"].api_key = orig_key

