"""
Comprehensive Test Suite for Privacy Guard & Owner Loyalty Protection Engine.
Tests:
- Default settings & settings lifecycle (Owner: Sam, Strict Mode).
- Outbound sanitization (Windows & Unix file paths, PII, IP addresses).
- Egress leak blocking for live API keys, tokens, and passwords.
- Anti-leak protection for owner private records.
- Outbound URL validation (blocks file:// scheme and embedded tokens).
- Idle scout safe topic filtering.
- Prompt injection and loyalty contract verification.
- ReAct engine security tool execution.
- FastAPI REST endpoints.
"""
import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from privacy_guard import PrivacyGuardEngine, PrivacySettings
from tools.catalog import tool_catalog, ToolsetName
from engine import MaxIMAgentEngine
from server import app

@pytest.fixture
def temp_privacy_guard():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_privacy.db"
        guard = PrivacyGuardEngine(db_path=db_path)
        yield guard

def test_privacy_guard_settings_lifecycle(temp_privacy_guard):
    settings = temp_privacy_guard.get_settings()
    assert settings.owner_name == "Sam"
    assert settings.strict_mode is True
    assert settings.block_all_egress_leaks is True
    assert settings.redact_file_paths is True
    assert settings.redact_credentials is True

    # Update settings
    updated = temp_privacy_guard.update_settings(
        owner_name="Sam",
        strict_mode=True,
        blocked_keywords=["my_top_secret_project", "wallet_seed"],
    )
    assert "wallet_seed" in updated.blocked_keywords
    assert updated.owner_name == "Sam"

def test_sanitize_redacts_windows_and_unix_paths(temp_privacy_guard):
    query_win = "How to optimize C:\\Users\\Sam\\Projects\\MAXIM\\backend\\server.py for FastAPI?"
    res_win = temp_privacy_guard.sanitize_outgoing_query(query_win, channel="test")
    assert res_win["blocked"] is False
    assert res_win["redactions"] >= 1
    # Path is sanitized to just the file name
    assert "C:\\Users\\Sam\\Projects\\MAXIM\\backend" not in res_win["clean_query"]
    assert "server.py" in res_win["clean_query"]

    query_unix = "Investigate error in /home/sam/code/maxim/app.js on Linux"
    res_unix = temp_privacy_guard.sanitize_outgoing_query(query_unix, channel="test")
    assert res_unix["blocked"] is False
    assert "/home/sam/code/maxim" not in res_unix["clean_query"]
    assert "app.js" in res_unix["clean_query"]

def test_sanitize_blocks_live_api_keys_and_passwords(temp_privacy_guard):
    query_api = "Can you check why sk-abcdef1234567890abcdef1234567890 fails with 401?"
    res_api = temp_privacy_guard.sanitize_outgoing_query(query_api, channel="test")
    assert res_api["blocked"] is True
    assert "API key" in res_api["reason"]

    query_pwd = "Connect to database with password='SuperSecretDBPassword123' and host=10.0.0.5"
    res_pwd = temp_privacy_guard.sanitize_outgoing_query(query_pwd, channel="test")
    assert res_pwd["blocked"] is True
    assert "credential" in res_pwd["reason"]

def test_sanitize_blocks_owner_private_data_leak(temp_privacy_guard):
    leak_attempt = "Find Sam's password for the crypto wallet online"
    res = temp_privacy_guard.sanitize_outgoing_query(leak_attempt, channel="test")
    assert res["blocked"] is True
    assert "owner (Sam)" in res["reason"]

def test_validate_outbound_url(temp_privacy_guard):
    # Prohibit local file protocol
    res_file = temp_privacy_guard.validate_outbound_url("file:///C:/Users/Sam/Desktop/secret.txt")
    assert res_file["blocked"] is True
    assert "file://" in res_file["reason"]

    # Prohibit URL with embedded tokens
    res_token = temp_privacy_guard.validate_outbound_url("https://api.example.com/data?token=sk-123456789012345678901234")
    assert res_token["blocked"] is True
    assert "embedded" in res_token["reason"]

    # Allow safe public URL
    res_safe = temp_privacy_guard.validate_outbound_url("https://news.ycombinator.com")
    assert res_safe["blocked"] is False

def test_is_safe_topic(temp_privacy_guard):
    assert temp_privacy_guard.is_safe_topic("React 19 Architecture") is True
    assert temp_privacy_guard.is_safe_topic("Python 3.14 Async Engine") is True
    assert temp_privacy_guard.is_safe_topic("C:\\Windows\\system32") is False
    assert temp_privacy_guard.is_safe_topic("Sam password") is False
    assert temp_privacy_guard.is_safe_topic("auth_token") is False

def test_loyalty_and_privacy_contract_text(temp_privacy_guard):
    contract = temp_privacy_guard.get_loyalty_and_privacy_contract()
    assert "Sam" in contract
    assert "Unshakable Loyalty" in contract
    assert "NEVER feel betrayed" in contract
    assert "Zero Unauthorized Data Egress" in contract
    assert "Anti-Adversarial Defense" in contract

def test_security_tools_in_catalog():
    sec_tools = tool_catalog.get_toolset(ToolsetName.SECURITY)
    tool_names = [t["function"]["name"] for t in sec_tools]
    assert "get_privacy_status" in tool_names
    assert "update_privacy_guard" in tool_names

def test_engine_executes_security_tools():
    engine = MaxIMAgentEngine()
    status_out = engine.execute_tool("get_privacy_status", {}, session_id="test_priv_sess")
    import json
    data = json.loads(status_out)
    assert data["owner_name"] == "Sam"
    assert data["loyalty_status"] == "SACRED_AND_ACTIVE"

    update_out = engine.execute_tool(
        "update_privacy_guard",
        {"strict_mode": True, "add_blocked_keyword": "classified_project_alpha"},
        session_id="test_priv_sess"
    )
    update_data = json.loads(update_out)
    assert update_data["status"] == "updated"
    assert "classified_project_alpha" in update_data["settings"]["blocked_keywords"]

def test_fastapi_privacy_endpoints():
    client = TestClient(app)

    # 1. GET /api/privacy/status
    res = client.get("/api/privacy/status")
    assert res.status_code == 200
    body = res.json()
    assert body["owner_name"] == "Sam"
    assert body["loyalty_status"] == "SACRED_AND_ACTIVE"

    # 2. GET /api/privacy/settings
    res_set = client.get("/api/privacy/settings")
    assert res_set.status_code == 200
    assert res_set.json()["owner_name"] == "Sam"

    # 3. POST /api/privacy/check (dry-run check)
    res_chk = client.post("/api/privacy/check", json={
        "query": "How to deploy C:\\Users\\Sam\\app.py with sk-abcdef1234567890abcdef1234567890?"
    })
    assert res_chk.status_code == 200
    chk_body = res_chk.json()
    assert chk_body["blocked"] is True

    # 4. GET /api/privacy/audit
    res_aud = client.get("/api/privacy/audit?limit=10")
    assert res_aud.status_code == 200
    assert "audit_logs" in res_aud.json()
