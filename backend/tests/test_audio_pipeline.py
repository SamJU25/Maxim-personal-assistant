"""
Unit tests for the Local Audio Pipeline (ASR & TTS).
Tests Qwen3-ASR discovery, Qwen3-TTS voice cloning reference resolution,
transcript normalization, audio status inspection, and API endpoints.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport

from local_asr import local_asr, normalize_asr_transcript, _get_audiocpp_asr_model
from voice import voice_engine, _get_tts_model, _get_voice_ref_file
from server import app


def test_normalize_asr_transcript():
    """Verify phonetic corrections for MaxIM system terminology."""
    raw = "Hello magazine, please run tell us and check life os for hermes updates."
    normalized = normalize_asr_transcript(raw)
    assert "MaxIM" in normalized
    assert "TELOS" in normalized
    assert "LifeOS" in normalized
    assert "Hermes" in normalized
    assert normalize_asr_transcript("") == ""


def test_asr_model_discovery():
    """Verify Qwen3-ASR GGUF models are discovered in models/asr/."""
    status = local_asr.get_status()
    assert isinstance(status, dict)
    assert "audiocpp_available" in status
    assert "models" in status
    assert "active_model" in status
    assert status["audiocpp_available"] is True
    # Verify discovered models include Qwen3-ASR
    model_names = [m["name"] for m in status["models"]]
    assert "qwen3-asr-0.6b-q8_0.gguf" in model_names

    # Test preference lookup
    preferred = _get_audiocpp_asr_model("1.7b")
    if preferred:
        assert "1.7b" in preferred.name.lower()


def test_tts_model_and_voice_ref_discovery():
    """Verify Qwen3-TTS model and voice clone reference audio are located."""
    status = voice_engine.get_status()
    assert isinstance(status, dict)
    assert "audiocpp_available" in status
    assert "models" in status
    assert "voice_ref_available" in status
    assert status["audiocpp_available"] is True
    assert status["voice_ref_available"] is True

    model_names = [m["name"] for m in status["models"]]
    assert "qwen3-tts-12hz-0.6b-base-q8_0.gguf" in model_names

    ref = _get_voice_ref_file()
    assert ref is not None
    assert ref.exists()
    assert ref.stat().st_size > 100


def test_transcribe_bytes_empty():
    """Verify empty byte payload returns empty string gracefully."""
    result = local_asr.transcribe_bytes(b"")
    assert result == ""


@pytest.mark.asyncio
async def test_audio_status_endpoint():
    """Verify GET /api/audio/status returns operational metrics for both pipelines."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/audio/status")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ready"
        assert "asr" in data
        assert "tts" in data
        assert data["asr"]["audiocpp_available"] is True
        assert data["tts"]["voice_ref_available"] is True


@pytest.mark.asyncio
async def test_synthesize_voice_endpoint():
    """Verify POST /api/voice/synthesize with mock or fast engine returns streaming audio."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "text": "MaxIM audio pipeline operational verification.",
            "engine": "fast",
        }
        res = await client.post("/api/voice/synthesize", json=payload)
        assert res.status_code == 200
        assert res.headers["content-type"] == "audio/mpeg"
        assert len(res.content) > 0


@pytest.mark.asyncio
async def test_transcribe_voice_endpoint_mock():
    """Verify POST /api/voice/transcribe handles audio uploads."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch.object(local_asr, "transcribe_bytes", return_value="MaxIM, start session."):
            files = {"file": ("test.webm", b"RIFFmockwavdata", "audio/webm")}
            res = await client.post("/api/voice/transcribe", files=files)
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "success"
            assert data["text"] == "MaxIM, start session."
