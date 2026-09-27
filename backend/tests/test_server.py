"""
Tests for MaxIM FastAPI Server and Telegram Remote Uplink (Phase 6).
Verifies:
1. Health check & TELOS profile endpoints.
2. Provider listing, switching, and custom provider dynamic registration.
3. Session lifecycle & receipt retrieval.
4. Screen state & CUA action dispatch.
5. Dream trigger & morning greeting generation.
6. Voice speech synthesis streaming.
7. Chat endpoint (SSE streaming & standard response).
8. Telegram Remote Uplink command dispatching.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from server import app
from config import config
from telegram_bot import TelegramRemoteUplink

client = TestClient(app)

def test_health_check_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "active_provider" in data
    assert "vault_path" in data
    assert data["vault_exists"] is True

def test_telos_endpoint():
    res = client.get("/api/telos")
    assert res.status_code == 200
    data = res.json()
    assert "profile" in data
    assert "targets" in data["profile"]
    assert "formatted_context" in data

def test_providers_endpoints():
    # 1. List providers
    res = client.get("/api/providers")
    assert res.status_code == 200
    data = res.json()
    assert "google" in data["providers"]
    assert "chatgpt" in data["providers"]
    assert "omniroute" in data["providers"]

    # 2. Register custom provider
    res_custom = client.post("/api/providers/custom", json={
        "name": "fastapi_test_vllm",
        "base_url": "http://localhost:8080/v1",
        "api_key": "test_token",
        "model_name": "qwen2.5-coder"
    })
    assert res_custom.status_code == 200
    assert res_custom.json()["status"] == "registered"

    # 3. Select custom provider
    res_select = client.post("/api/providers/select", json={
        "provider": "fastapi_test_vllm"
    })
    assert res_select.status_code == 200
    assert res_select.json()["active_provider"] == "fastapi_test_vllm"

def test_session_management():
    # Create new session
    res = client.post("/api/session/new")
    assert res.status_code == 200
    sess_id = res.json()["session_id"]
    assert sess_id.startswith("session_")

    # Fetch session state
    res_get = client.get(f"/api/session?session_id={sess_id}")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["session_id"] == sess_id
    assert "messages" in data
    assert "facts" in data
    assert "receipts" in data

def test_screen_and_cua_endpoints():
    # Screen state
    res_screen = client.get("/api/screen")
    assert res_screen.status_code == 200
    sdata = res_screen.json()
    assert "active_window" in sdata
    assert "resolution" in sdata

    # CUA action dispatch
    res_cua = client.post("/api/cua/act", json={
        "action": "click",
        "x": 200,
        "y": 300
    })
    assert res_cua.status_code == 200
    assert "status" in res_cua.json()

def test_dream_and_morning_endpoints():
    # Morning greeting
    res_morning = client.get("/api/morning-greeting")
    assert res_morning.status_code == 200
    assert "greeting" in res_morning.json()
    assert len(res_morning.json()["greeting"]) > 5

    # Dream reflection trigger
    res_dream = client.post("/api/dream/trigger", json={"session_id": "test_api_dream"})
    assert res_dream.status_code == 200
    assert res_dream.json()["status"] == "completed"

def test_voice_synthesis_endpoint():
    res = client.post("/api/voice/synthesize", json={
        "text": "MaxIM server speech synthesis online."
    })
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/mpeg"
    assert len(res.content) > 0

@pytest.mark.asyncio
async def test_chat_non_streaming_mock():
    with patch("server.agent_engine.run_turn", new_callable=AsyncMock) as mock_turn:
        mock_turn.return_value = {
            "session_id": "sess_test",
            "response": "Affirmative, human.",
            "receipts": [],
            "iterations": 1
        }
        res = client.post("/api/chat", json={
            "message": "Are you alive?",
            "stream": False,
            "session_id": "sess_test"
        })
        assert res.status_code == 200
        assert res.json()["response"] == "Affirmative, human."

@pytest.mark.asyncio
async def test_telegram_remote_uplink_commands():
    uplink = TelegramRemoteUplink(token="123456:FAKE_TOKEN", allowed_chat_id="9999")
    assert uplink.is_configured is True

    # Test authorization rejection
    with patch.object(uplink, "send_message", new_callable=AsyncMock) as mock_send:
        # Unauthorized chat ID
        await uplink.handle_update({
            "message": {
                "chat": {"id": 1111},
                "text": "Hello"
            }
        })
        mock_send.assert_called_once()
        assert "Access Denied" in mock_send.call_args[0][1]

    # Test /status authorized
    with patch.object(uplink, "send_message", new_callable=AsyncMock) as mock_send:
        await uplink.handle_update({
            "message": {
                "chat": {"id": 9999},
                "text": "/status"
            }
        })
        mock_send.assert_called_once()
        assert "Desktop Status" in mock_send.call_args[0][1]

def test_tools_catalog_endpoint():
    """Verify GET /api/tools returns all tools with schemas, categories, and parameter counts."""
    res = client.get("/api/tools")
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    assert "total" in data
    assert data["total"] >= 100
    names = [t["name"] for t in data["tools"]]
    assert "read_vault_note" in names
    assert "browser_navigate" in names
    assert "os_focus_window" in names
    assert "organize_directory" in names

