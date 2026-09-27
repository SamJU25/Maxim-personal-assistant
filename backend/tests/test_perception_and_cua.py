"""
Unit tests for Phase 4: Screen Perception & Cua Computer Use Integration.
Tests active window detection, screenshot capture, Cua background actions, and ReAct dispatch.
"""
import pytest
import json
from pathlib import Path
from tools.screen_tool import screen_tool, get_active_window_info
from tools.cua_tool import cua_driver
from engine import MaxIMAgentEngine, MAXIM_TOOLS
from memory import SQLiteMemoryStore

def test_active_window_detection():
    """Verify active foreground window detection on Windows."""
    info = get_active_window_info()
    assert isinstance(info, dict)
    assert "title" in info
    assert len(info["title"]) > 0

def test_screen_capture_and_downscaling():
    """Verify screenshot capture, proportional downscaling, and base64 generation."""
    shot = screen_tool.capture_screenshot(as_base64=True)
    assert shot["success"] is True
    assert "original_dimensions" in shot
    assert "scaled_dimensions" in shot
    assert len(shot["image_base64"]) > 0
    assert shot["bytes_size"] > 0
    # Scaled dimensions must not exceed max_dimension
    assert max(shot["scaled_dimensions"]) <= screen_tool.max_dimension

def test_inspect_screen_summary():
    """Verify inspect_screen returns active window title and screenshot status."""
    res = screen_tool.inspect_screen()
    assert "active_window" in res
    assert "screenshot_available" in res
    assert res["screenshot_available"] is True

def test_cua_driver_actions():
    """Verify Cua background computer-use driver actions."""
    # 1. Test background click
    click_res = cua_driver.click(element_name_or_selector="Submit Button", x=100, y=200)
    assert click_res["action"] == "click"
    assert click_res["success"] is True
    assert "mode" in click_res

    # 2. Test background typing
    type_res = cua_driver.type_text("Hello Cua", element_name="Search Input")
    assert type_res["action"] == "type"
    assert type_res["success"] is True

    # 3. Test background browser navigation
    nav_res = cua_driver.navigate_browser("https://github.com/trycua/cua")
    assert nav_res["action"] == "navigate"
    assert nav_res["target"] == "https://github.com/trycua/cua"
    assert nav_res["success"] is True

def test_engine_perception_and_cua_dispatch(tmp_path: Path):
    """Verify engine dispatches inspect_screen and Cua actions and records receipts."""
    test_db = SQLiteMemoryStore(db_path=tmp_path / "test.db")
    engine = MaxIMAgentEngine(memory_store=test_db)

    # 1. Dispatch inspect_screen
    screen_out = engine.execute_tool("inspect_screen", {}, session_id="test_turn")
    screen_data = json.loads(screen_out)
    assert "active_window" in screen_data
    assert screen_data["screenshot_captured"] is True

    # 2. Dispatch cua_click
    click_out = engine.execute_tool("cua_click", {"element_name_or_selector": "Download ZIP"}, session_id="test_turn")
    click_data = json.loads(click_out)
    assert click_data["action"] == "click"

    # 3. Dispatch cua_type
    type_out = engine.execute_tool("cua_type", {"text": "pytest testing"}, session_id="test_turn")
    type_data = json.loads(type_out)
    assert type_data["action"] == "type"

    # 4. Dispatch cua_navigate_browser
    nav_out = engine.execute_tool("cua_navigate_browser", {"url": "https://ourlifeos.ai"}, session_id="test_turn")
    nav_data = json.loads(nav_out)
    assert nav_data["action"] == "navigate"

    # Verify receipts recorded in SQLite
    with test_db._get_connection() as conn:
        receipts = conn.execute("SELECT * FROM execution_receipts WHERE session_id = 'test_turn'").fetchall()
        assert len(receipts) == 4
        tool_names = [r["tool_name"] for r in receipts]
        assert "inspect_screen" in tool_names
        assert "cua_click" in tool_names
        assert "cua_type" in tool_names
        assert "cua_navigate_browser" in tool_names
