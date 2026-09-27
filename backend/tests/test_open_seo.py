"""
Unit and integration tests for OpenSEO Website Visibility & Technical Auditor.
"""
import pytest
import tempfile
import shutil
import json
from pathlib import Path
from open_seo import OpenSEOEngine

@pytest.fixture
def temp_seo():
    tmp_dir = Path(tempfile.mkdtemp())
    db_path = tmp_dir / "test_open_seo.db"
    vault_dir = tmp_dir / "vault"
    vault_dir.mkdir(parents=True)
    engine = OpenSEOEngine(db_path=db_path, vault_dir=vault_dir)
    yield engine, tmp_dir, vault_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_audit_html_complete_score(temp_seo):
    engine, _, vault_dir = temp_seo

    sample_html = """<!DOCTYPE html>
<html>
<head>
    <title>MaxIM AI — Executive Personal Assistant Platform</title>
    <meta name="description" content="MaxIM is a high-performance native personal executive assistant with local intelligence, voice, and memory." />
    <meta property="og:title" content="MaxIM AI" />
    <meta property="og:description" content="Executive personal assistant." />
    <meta property="og:image" content="https://example.com/og.png" />
    <link rel="canonical" href="https://example.com" />
    <script type="application/ld+json">{"@context": "https://schema.org", "@type": "SoftwareApplication"}</script>
</head>
<body>
    <h1>MaxIM Intelligent Executive Co-Pilot</h1>
    <h2>System Architecture and Capabilities</h2>
    <img src="logo.png" alt="MaxIM Logo" />
</body>
</html>"""

    res = engine.audit_html(sample_html, url="https://maxim.local")
    assert res["seo_score"] == 100
    assert res["passed_checks"] == 8
    assert res["issues_count"] == 0
    assert len(res["passed"]) == 8
    assert len(res["issues"]) == 0

    # Verify Markdown scorecard was generated in vault
    report_file = Path(res["vault_path"])
    assert report_file.exists()
    content = report_file.read_text(encoding="utf-8")
    assert "# 🔍 Technical SEO Audit: maxim.local" in content
    assert "100/100" in content
    assert "#seo #audit" in content

def test_audit_html_with_issues(temp_seo):
    engine, _, _ = temp_seo

    # Poor HTML missing tags
    poor_html = """<!DOCTYPE html>
<html>
<head>
    <title>Hi</title>
</head>
<body>
    <h1>First Header</h1>
    <h1>Second Header Duplicate</h1>
    <img src="missing_alt.png" />
</body>
</html>"""

    res = engine.audit_html(poor_html, url="https://poor-site.com")
    assert res["seo_score"] < 50
    assert res["issues_count"] > 0
    assert any("Title tag is too short" in issue for issue in res["issues"])
    assert any("Missing <meta name='description'>" in issue for issue in res["issues"])
    assert any("Multiple <h1>" in issue for issue in res["issues"])
    assert any("missing alt" in issue for issue in res["issues"])

def test_audit_url_test_mode(temp_seo):
    engine, _, _ = temp_seo
    res = engine.audit_url("https://maxim-assistant.dev", test_mode=True)
    assert res["seo_score"] == 100
    assert res["passed_checks"] >= 5

    audits = engine.list_audits()
    assert len(audits) >= 1

def test_analyze_keyword_density(temp_seo):
    engine, _, _ = temp_seo
    text = """
    Artificial intelligence models and autonomous agent workflows are transforming computing.
    An autonomous agent can analyze data, plan operations, and execute agent tasks with precision.
    The agent architecture relies on continuous learning and memory.
    """
    res = engine.analyze_keyword_density(text, target_keywords=["agent", "autonomous", "quantum"])
    assert res["total_words"] > 10
    assert any(k["keyword"] == "agent" for k in res["top_keywords"])

    targets = {t["keyword"]: t for t in res["target_keywords"]}
    assert targets["agent"]["count"] >= 3
    assert targets["quantum"]["count"] == 0

def test_engine_tool_dispatch():
    from engine import agent_engine

    # Test seo_audit_url test mode
    res_raw = agent_engine.execute_tool(
        name="seo_audit_url",
        args={"url": "https://test-maxim.com", "test_mode": True},
        session_id="test_session"
    )
    res = json.loads(res_raw)
    assert res["seo_score"] == 100

    # Test seo_analyze_keyword_density
    res_raw2 = agent_engine.execute_tool(
        name="seo_analyze_keyword_density",
        args={"text": "Software architecture principles and automated testing pipelines are essential.", "target_keywords": ["testing"]},
        session_id="test_session"
    )
    res2 = json.loads(res_raw2)
    assert res2["total_words"] > 0

    # Test seo_list_audits
    res_raw3 = agent_engine.execute_tool(
        name="seo_list_audits",
        args={},
        session_id="test_session"
    )
    res3 = json.loads(res_raw3)
    assert res3["status"] == "success"
    assert len(res3["audits"]) >= 1
