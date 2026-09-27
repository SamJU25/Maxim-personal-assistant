"""
Unit & Integration Tests for Phase 10:
- Agent Reach Native Internet Gateway.
- Jina Reader URL to Markdown fetcher & fallback.
- Multi-Engine Web Search (DuckDuckGo / Instant Answers).
- GitHub Reach (Repository metadata, stars, activity, README).
- Community Reach (V2EX hot topics, Hacker News top developer discussions).
- Reach Channel Doctor Diagnostics.
- MaxIM ReAct Engine tool integration.
- Sub-Agent delegation with reach toolset.
- FastAPI Phase 10 REST endpoints.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from server import app
from tools.reach_tool import agent_reach, AgentReachGateway
from engine import agent_engine
from subagent import subagent_pool

client = TestClient(app)

@pytest.mark.asyncio
async def test_read_web_page_jina_success():
    """Verifies clean Markdown extraction via Jina Reader."""
    mock_markdown = "# Agent Reach\n\nUniversal Internet Access for AI Agents."
    
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.text = mock_markdown

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_res
        result = await agent_reach.read_web_page("https://github.com/Panniantong/Agent-Reach")

        assert result["status"] == "success"
        assert result["engine"] == "jina_reader"
        assert "Agent Reach" in result["content"]
        assert result["url"] == "https://github.com/Panniantong/Agent-Reach"

@pytest.mark.asyncio
async def test_read_web_page_direct_fallback():
    """Verifies direct HTML fetch fallback if Jina fails."""
    mock_html = "<html><head><title>Fallback Page</title></head><body><h1>Hello World</h1><p>Test content</p></body></html>"
    
    # First call (Jina) fails, second call (direct) succeeds
    fail_res = MagicMock(status_code=500, text="")
    success_res = MagicMock(status_code=200, text=mock_html)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = [Exception("Jina 503"), success_res]
        result = await agent_reach.read_web_page("https://example.com/fallback")

        assert result["status"] == "success"
        assert result["engine"] == "direct_fallback"
        assert "Hello World" in result["content"]

@pytest.mark.asyncio
async def test_read_web_page_empty():
    """Verifies validation on empty URL."""
    result = await agent_reach.read_web_page("")
    assert "error" in result

@pytest.mark.asyncio
async def test_web_search_instant_answers():
    """Verifies DuckDuckGo Instant Answers API integration."""
    mock_ddg = {
        "Heading": "Python Programming",
        "AbstractText": "Python is a high-level programming language.",
        "AbstractURL": "https://en.wikipedia.org/wiki/Python",
        "RelatedTopics": [
            {
                "Text": "Python Software Foundation - Official site",
                "FirstURL": "https://www.python.org",
            }
        ],
    }

    mock_res = MagicMock(status_code=200)
    mock_res.json.return_value = mock_ddg

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_post.side_effect = Exception("HTML parsing bypass")
        mock_get.return_value = mock_res
        result = await agent_reach.web_search("Python language", max_results=3)

        assert result["status"] == "success"
        assert result["query"] == "Python language"
        assert len(result["results"]) > 0
        assert "Python" in result["results"][0]["title"]

@pytest.mark.asyncio
async def test_web_search_fallback():
    """Verifies defensive search fallback when network fails."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_post.side_effect = Exception("Network offline")
        mock_get.side_effect = Exception("Network offline")
        result = await agent_reach.web_search("Offline query")

        assert result["status"] == "fallback"
        assert len(result["results"]) == 1

@pytest.mark.asyncio
async def test_github_reach_info():
    """Verifies GitHub repository information extraction."""
    mock_repo_data = {
        "full_name": "Panniantong/Agent-Reach",
        "description": "Universal agent internet access gateway",
        "stargazers_count": 342,
        "forks_count": 48,
        "open_issues_count": 3,
        "pushed_at": "2026-03-20T10:00:00Z",
        "language": "Python",
        "html_url": "https://github.com/Panniantong/Agent-Reach",
        "license": {"name": "MIT License"},
    }

    mock_res = MagicMock(status_code=200)
    mock_res.json.return_value = mock_repo_data

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_res
        result = await agent_reach.github_reach("Panniantong/Agent-Reach", action="info")

        assert result["status"] == "success"
        assert result["stars"] == 342
        assert result["language"] == "Python"
        assert result["license"] == "MIT License"

@pytest.mark.asyncio
async def test_github_reach_readme():
    """Verifies GitHub raw README fetching."""
    mock_readme = "# Agent Reach\n\nGive any AI agent internet access in 1 line."
    mock_res = MagicMock(status_code=200, text=mock_readme)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_res
        result = await agent_reach.github_reach("Panniantong/Agent-Reach", action="readme")

        assert result["status"] == "success"
        assert "Give any AI agent internet access" in result["readme"]

@pytest.mark.asyncio
async def test_community_reach_v2ex():
    """Verifies V2EX community discussion feed extraction."""
    mock_v2ex_topics = [
        {
            "id": 101,
            "title": "Discussion on LLM Native Gateways",
            "url": "https://v2ex.com/t/101",
            "replies": 42,
            "member": {"username": "developer_alpha"},
            "node": {"title": "AI"},
        }
    ]

    mock_res = MagicMock(status_code=200)
    mock_res.json.return_value = mock_v2ex_topics

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_res
        result = await agent_reach.community_reach("v2ex", limit=5)

        assert result["status"] == "success"
        assert result["source"] == "v2ex"
        assert len(result["discussions"]) == 1
        assert result["discussions"][0]["author"] == "developer_alpha"

@pytest.mark.asyncio
async def test_reach_doctor_diagnostics():
    """Verifies Channel Doctor diagnostic reporting."""
    diag_res = MagicMock(status_code=200, text="# MaxIM Doctor")
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = diag_res
        doc = await agent_reach.reach_doctor()

        assert "overall_health" in doc
        assert "channels" in doc
        assert "jina_reader" in doc["channels"]
        assert "duckduckgo_search" in doc["channels"]
        assert "github_api" in doc["channels"]
        assert "community_v2ex" in doc["channels"]

def test_engine_tool_execution():
    """Verifies ReAct Agent Engine tool dispatch for Reach tools."""
    mock_res = {"status": "success", "content": "Sample parsed text"}
    with patch.object(agent_reach, "read_web_page", new_callable=AsyncMock) as mock_read:
        mock_read.return_value = mock_res
        out = agent_engine.execute_tool(
            "read_web_page",
            {"url": "https://example.com/test"},
            session_id="test_reach_engine"
        )
        parsed = json.loads(out)
        assert parsed["status"] == "success"
        assert parsed["content"] == "Sample parsed text"

    mock_search = {"status": "success", "query": "AI Agents", "results": []}
    with patch.object(agent_reach, "web_search", new_callable=AsyncMock) as mock_s:
        mock_s.return_value = mock_search
        out = agent_engine.execute_tool(
            "web_search",
            {"query": "AI Agents"},
            session_id="test_reach_engine"
        )
        parsed = json.loads(out)
        assert parsed["status"] == "success"

def test_subagent_reach_delegation():
    """Verifies subagents can be initialized with the reach toolset."""
    sub = subagent_pool.create_subagent(
        task="Investigate Agent-Reach architecture",
        role="Web Researcher",
        toolset_whitelist=["read_web_page", "web_search", "github_reach"],
        max_iterations=2,
    )
    assert sub.cfg.role == "Web Researcher"
    assert "read_web_page" in sub.cfg.toolset_whitelist
    assert "write_vault_note" not in sub.cfg.toolset_whitelist

def test_fastapi_reach_endpoints():
    """Verifies all FastAPI Phase 10 REST endpoints respond correctly."""
    # 1. Doctor
    with patch.object(agent_reach, "reach_doctor", new_callable=AsyncMock) as mock_doc:
        mock_doc.return_value = {
            "status": "healthy",
            "overall_health": "optimal",
            "channels": {
                "jina_reader": {"status": "healthy", "latency_ms": 120}
            }
        }
        res = client.get("/api/reach/doctor")
        assert res.status_code == 200
        assert res.json()["overall_health"] == "optimal"

    # 2. Read
    with patch.object(agent_reach, "read_web_page", new_callable=AsyncMock) as mock_read:
        mock_read.return_value = {"status": "success", "engine": "jina_reader", "content": "# Readme"}
        res = client.post("/api/reach/read", json={"url": "https://example.com", "max_chars": 5000})
        assert res.status_code == 200
        assert res.json()["engine"] == "jina_reader"

    # 3. Search
    with patch.object(agent_reach, "web_search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = {"status": "success", "query": "MaxIM", "results": [{"title": "MaxIM"}]}
        res = client.post("/api/reach/search", json={"query": "MaxIM", "max_results": 5})
        assert res.status_code == 200
        assert res.json()["query"] == "MaxIM"

    # 4. GitHub
    with patch.object(agent_reach, "github_reach", new_callable=AsyncMock) as mock_gh:
        mock_gh.return_value = {"status": "success", "repo": "Panniantong/Agent-Reach", "stars": 350}
        res = client.post("/api/reach/github", json={"repo": "Panniantong/Agent-Reach", "action": "info"})
        assert res.status_code == 200
        assert res.json()["stars"] == 350

    # 5. Community
    with patch.object(agent_reach, "community_reach", new_callable=AsyncMock) as mock_comm:
        mock_comm.return_value = {"status": "success", "source": "v2ex", "discussions": []}
        res = client.get("/api/reach/community?source=v2ex&limit=5")
        assert res.status_code == 200
        assert res.json()["source"] == "v2ex"
