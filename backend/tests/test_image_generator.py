"""
backend/tests/test_image_generator.py
=====================================
Unit tests for the Neural Image Generator and Vault Integration.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from image_generator import ImageGenerationEngine, image_generator
from server import app

client = TestClient(app)


def test_enhance_prompt():
    engine = ImageGenerationEngine()
    enhanced = engine._enhance_prompt("A neon cyber mascot", style="cyberpunk")
    assert "A neon cyber mascot" in enhanced
    assert "cyberpunk" in enhanced


def test_directory_traversal_protection(tmp_path):
    engine = ImageGenerationEngine(output_dir=tmp_path)
    test_file = tmp_path / "valid.jpg"
    test_file.write_bytes(b"image data")

    # Valid name
    assert engine.get_image_path("valid.jpg") == test_file

    # Directory traversal attempts should be resolved safely or return None
    assert engine.get_image_path("../../../windows/system32/cmd.exe") is None


def test_image_endpoints(tmp_path):
    test_img = tmp_path / "test_mascot.jpg"
    test_img.write_bytes(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00")

    with patch.object(image_generator, "get_image_path", return_value=test_img):
        res = client.get("/api/images/test_mascot.jpg")
        assert res.status_code == 200
        assert res.content == test_img.read_bytes()

    # Non-existent image
    with patch.object(image_generator, "get_image_path", return_value=None):
        res_404 = client.get("/api/images/nonexistent.jpg")
        assert res_404.status_code == 404


def test_engine_tool_execution():
    from engine import agent_engine

    mock_res = {
        "status": "success",
        "prompt": "neon cat",
        "filename": "gen_test.jpg",
        "image_url": "/api/images/gen_test.jpg",
        "markdown": "![neon cat](/api/images/gen_test.jpg)"
    }

    with patch("image_generator.image_generator.generate", return_value=mock_res):
        out_str = agent_engine.execute_tool("generate_image", {"prompt": "neon cat"}, session_id="test_session")
        assert "gen_test.jpg" in out_str
        assert "/api/images/gen_test.jpg" in out_str
