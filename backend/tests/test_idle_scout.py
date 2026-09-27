"""
Comprehensive Test Suite for Autonomous Overnight & Idle Intelligence Scout.
Verifies interest profiling, idle/sleep detection, live search scout cycles,
vault notes persistence, catalog tools, and REST API endpoints.
"""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from idle_scout import IdleIntelligenceScout, UserInterestTopic, ScoutReport
from server import app
from tools.catalog import tool_catalog, ToolsetName
from engine import agent_engine

@pytest.fixture
def scout_instance(tmp_path):
    db_file = tmp_path / "test_scout.db"
    return IdleIntelligenceScout(db_path=db_file)

def test_scout_settings_lifecycle_and_defaults(scout_instance):
    settings = scout_instance.get_settings()
    assert settings.enabled is True
    assert settings.idle_threshold_minutes == 45
    assert settings.night_start_hour == 23
    assert settings.night_end_hour == 7

    updated = scout_instance.update_settings(
        enabled=True,
        idle_threshold_minutes=30,
        night_start_hour=22,
        night_end_hour=6,
    )
    assert updated.idle_threshold_minutes == 30
    assert updated.night_start_hour == 22
    assert updated.night_end_hour == 6

def test_user_activity_and_interest_profiling(scout_instance):
    # Record user message with distinct technology keywords
    scout_instance.record_user_activity("I am building an agent workflow in React and Python with FastAPI and SQLite.")
    
    topics = scout_instance.get_interest_topics(limit=10)
    topic_names = [t.topic for t in topics]
    assert any("React" in name for name in topic_names)
    assert any("Python" in name or "FastAPI" in name for name in topic_names)

    # Calling again should increase weight
    react_topic_before = next(t for t in topics if "React" in t.topic)
    scout_instance.record_user_activity("More React improvements today")
    topics_after = scout_instance.get_interest_topics(limit=10)
    react_topic_after = next(t for t in topics_after if "React" in t.topic)
    assert react_topic_after.weight >= react_topic_before.weight

def test_manual_interest_topic_management(scout_instance):
    new_t = scout_instance.add_interest_topic("Quantum Neural Networks", category="science")
    assert new_t.topic == "Quantum Neural Networks"
    assert new_t.category == "science"
    assert new_t.source == "manual"

    topics = scout_instance.get_interest_topics()
    assert any(t.topic == "Quantum Neural Networks" for t in topics)

    target_t = next(t for t in topics if t.topic == "Quantum Neural Networks")
    assert target_t.id is not None
    deleted = scout_instance.delete_interest_topic(target_t.id)
    assert deleted is True

    topics_after = scout_instance.get_interest_topics()
    assert not any(t.topic == "Quantum Neural Networks" for t in topics_after)

def test_idle_and_night_detection(scout_instance):
    status = scout_instance.check_idle_or_sleep_status()
    assert "is_idle" in status
    assert "is_night" in status
    assert "minutes_idle" in status
    assert "should_auto_scout" in status

@pytest.mark.asyncio
async def test_execute_scout_cycle_success(scout_instance, tmp_path):
    mock_search_results = {
        "status": "success",
        "results": [
            {
                "title": "React 19 Official Production Release Announced",
                "url": "https://react.dev/blog/2026/react-19",
                "snippet": "React 19 brings concurrent asset loading and server actions to stable.",
            }
        ]
    }
    mock_community_results = {
        "status": "success",
        "discussions": [
            {
                "title": "Show HN: Fast local inference engine for small models",
                "url": "https://news.ycombinator.com/item?id=99999",
                "score": 340,
                "comments": 85,
            }
        ]
    }

    mock_llm_json = json.dumps({
        "title": "Overnight Intelligence Briefing: React 19 & Fast Local AI",
        "summary": "React 19 hits stable with server actions, while community launches lightweight local inference engine.",
        "news_items": [
            {
                "headline": "React 19 Stable Release",
                "detail": "Brings concurrent asset loading and native server actions.",
                "source_url": "https://react.dev/blog/2026/react-19"
            }
        ],
        "project_ideas": [
            {
                "idea": "Upgrade MaxIM frontend to leverage React 19 streaming hooks",
                "relevance": "Direct alignment with UI/UX modernization target"
            }
        ],
        "audio_brief": "Good morning! While you were asleep, React 19 was officially released with major performance enhancements."
    })

    mock_chat_response = MagicMock()
    mock_chat_response.choices = [
        MagicMock(message=MagicMock(content=mock_llm_json))
    ]

    with patch("tools.reach_tool.agent_reach.web_search", new_callable=AsyncMock) as mock_search, \
         patch("tools.reach_tool.agent_reach.community_reach", new_callable=AsyncMock) as mock_comm, \
         patch("router.model_router.chat_completion", new_callable=AsyncMock) as mock_chat:
        
        mock_search.return_value = mock_search_results
        mock_comm.return_value = mock_community_results
        mock_chat.return_value = mock_chat_response

        report = await scout_instance.execute_scout_cycle(trigger_type="sleep", force=True)
        assert report["title"] == "Overnight Intelligence Briefing: React 19 & Fast Local AI"
        assert "React 19 Stable Release" in report["briefing_markdown"]
        assert "Good morning!" in report["audio_brief"]
        assert len(report["topics"]) > 0

        # Verify saved in SQLite
        latest = scout_instance.get_latest_report()
        assert latest is not None
        assert latest["id"] == report["id"]
        assert latest["title"] == report["title"]
        assert latest["is_reviewed"] is False

        # Mark reviewed
        reviewed = scout_instance.mark_report_reviewed(report["id"])
        assert reviewed is True
        latest_reviewed = scout_instance.get_latest_report()
        assert latest_reviewed["is_reviewed"] is True

def test_scout_tools_registered_in_catalog():
    scout_tools = tool_catalog.get_toolset(ToolsetName.SCOUT)
    assert len(scout_tools) >= 3
    tool_names = [t["function"]["name"] for t in scout_tools]
    assert "trigger_idle_scout" in tool_names
    assert "get_overnight_intel" in tool_names
    assert "manage_interest_topics" in tool_names

def test_engine_executes_scout_tools():
    # Test manage_interest_topics list
    res_list = agent_engine.execute_tool("manage_interest_topics", {"action": "list"}, session_id="test_session")
    data_list = json.loads(res_list)
    assert data_list["status"] == "success"
    assert "topics" in data_list

    # Test get_overnight_intel
    res_intel = agent_engine.execute_tool("get_overnight_intel", {}, session_id="test_session")
    data_intel = json.loads(res_intel)
    assert "status" in data_intel

def test_cron_watchdog_idle_scout_job():
    from cron_engine import watchdog_scheduler
    assert "idle_intelligence_scout" in watchdog_scheduler.jobs
    job = watchdog_scheduler.jobs["idle_intelligence_scout"]
    assert job.enabled is True
    assert job.interval_seconds == 1800

def test_api_scout_endpoints():
    client = TestClient(app)

    # 1. Status
    res_status = client.get("/api/scout/status")
    assert res_status.status_code == 200
    assert "is_idle" in res_status.json()

    # 2. Settings
    res_settings = client.get("/api/scout/settings")
    assert res_settings.status_code == 200
    assert "idle_threshold_minutes" in res_settings.json()

    res_up_settings = client.post("/api/scout/settings", json={"idle_threshold_minutes": 50})
    assert res_up_settings.status_code == 200
    assert res_up_settings.json()["idle_threshold_minutes"] == 50

    # 3. Interests
    res_interests = client.get("/api/scout/interests")
    assert res_interests.status_code == 200
    assert "topics" in res_interests.json()

    res_add = client.post("/api/scout/interests", json={"topic": "Agentic Workflows", "category": "ai"})
    assert res_add.status_code == 200
    assert res_add.json()["status"] == "success"

    # 4. Reports
    res_reports = client.get("/api/scout/reports")
    assert res_reports.status_code == 200
    assert "reports" in res_reports.json()

    # 5. Latest
    res_latest = client.get("/api/scout/latest")
    assert res_latest.status_code == 200
    assert "status" in res_latest.json()
