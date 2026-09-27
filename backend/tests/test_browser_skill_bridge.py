"""
Unit and integration tests for BrowserSkill Bridge (Tencent adaptation).
"""
import pytest
import tempfile
import shutil
import json
from pathlib import Path
from browser_skill_bridge import BrowserSkillBridge

@pytest.fixture
def temp_bridge():
    tmp_dir = Path(tempfile.mkdtemp())
    db_path = tmp_dir / "test_browser_skill.db"
    bridge = BrowserSkillBridge(db_path=db_path, cdp_port=9999)
    yield bridge, tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_get_active_browser_tab_simulated(temp_bridge):
    bridge, _ = temp_bridge
    tab = bridge.get_active_browser_tab(test_mode=True)
    assert tab["connected"] is True
    assert tab["session_type"] == "real_user_session"
    assert "GitHub" in tab["title"]
    assert tab["cookies_active"] is True

def test_get_active_browser_tab_fallback(temp_bridge):
    bridge, _ = temp_bridge
    # Since port 9999 has no running browser, fallback should activate safely
    tab = bridge.get_active_browser_tab(test_mode=False)
    assert tab["connected"] is False
    assert tab["session_type"] == "standby"
    assert tab["url"] == "about:blank"

def test_evaluate_script(temp_bridge):
    bridge, _ = temp_bridge
    res = bridge.evaluate_script("document.title", test_mode=True)
    assert res["status"] == "success"
    assert res["script"] == "document.title"
    assert "result" in res

    # Verify action logged
    actions = bridge.list_recent_actions()
    assert len(actions) == 1
    assert actions[0]["action_type"] == "eval_js"

def test_execute_browser_command(temp_bridge):
    bridge, _ = temp_bridge
    res_click = bridge.execute_browser_command(action="click", target="#submit-btn")
    assert res_click["status"] == "success"
    assert "Clicked target" in res_click["result"]

    res_type = bridge.execute_browser_command(action="type", target="#search-input", value="deepseek")
    assert res_type["status"] == "success"
    assert "deepseek" in res_type["result"]

    actions = bridge.list_recent_actions()
    assert len(actions) == 2

def test_engine_tool_dispatch(temp_bridge):
    from engine import agent_engine
    import asyncio

    # Test browserskill_get_active_tab
    res_raw = agent_engine.execute_tool(
        name="browserskill_get_active_tab",
        args={"test_mode": True},
        session_id="test_session"
    )
    res = json.loads(res_raw)
    assert res["status"] == "success"
    assert res["tab"]["connected"] is True

    # Test browserskill_evaluate_script
    res_raw2 = agent_engine.execute_tool(
        name="browserskill_evaluate_script",
        args={"script": "window.location.href", "test_mode": True},
        session_id="test_session"
    )
    res2 = json.loads(res_raw2)
    assert res2["status"] == "success"

    # Test browserskill_execute_command
    res_raw3 = agent_engine.execute_tool(
        name="browserskill_execute_command",
        args={"action": "click", "target": ".nav-item", "test_mode": True},
        session_id="test_session"
    )
    res3 = json.loads(res_raw3)
    assert res3["status"] == "success"
