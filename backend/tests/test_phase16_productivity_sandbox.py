"""
Unit and integration tests for Phase 16: 10xProductivity Workstation & QwenPaw Sandboxed Guard.
"""
import pytest
import shutil
from pathlib import Path
from workstation_sandbox import WorkstationSandboxEngine, CommandAuditResult, SandboxedExecutionResult

@pytest.fixture
def sandbox_fixture(tmp_path):
    test_db = tmp_path / "test_sandbox.db"
    test_ws = tmp_path / "workspace"
    test_ws.mkdir()
    engine = WorkstationSandboxEngine(db_path=test_db, workspace_root=test_ws)
    return engine, test_ws


def test_qwenpaw_audit_safe_commands(sandbox_fixture):
    engine, _ = sandbox_fixture
    audit = engine.audit_command("echo 'Hello World'")
    assert audit.verdict == "ALLOW"
    assert audit.is_safe is True
    assert audit.risk_level == "LOW"

    audit_git = engine.audit_command("git status")
    assert audit_git.verdict == "ALLOW"
    assert audit_git.is_safe is True


def test_qwenpaw_audit_destructive_blocks(sandbox_fixture):
    engine, _ = sandbox_fixture
    
    # Root deletion
    audit1 = engine.audit_command("rm -rf /")
    assert audit1.verdict == "BLOCK"
    assert audit1.is_safe is False
    assert audit1.risk_level == "CRITICAL"
    
    # Windows disk format
    audit2 = engine.audit_command("Format-Volume -DriveLetter C")
    assert audit2.verdict == "BLOCK"
    assert audit2.is_safe is False

    # Windows root deletion
    audit3 = engine.audit_command("del /s /q C:\\Windows")
    assert audit3.verdict == "BLOCK"
    assert audit3.is_safe is False

    # Database drop
    audit4 = engine.audit_command("DROP DATABASE production_db;")
    assert audit4.verdict == "BLOCK"
    assert audit4.is_safe is False
    assert audit4.risk_level == "HIGH"


def test_qwenpaw_audit_suspicious_warnings(sandbox_fixture):
    engine, _ = sandbox_fixture
    audit = engine.audit_command("git reset --hard HEAD~1")
    assert audit.verdict == "WARN"
    assert audit.is_safe is True
    assert audit.risk_level == "MEDIUM"


def test_sandboxed_command_execution(sandbox_fixture):
    engine, ws = sandbox_fixture
    # Execute safe echo
    res = engine.execute_sandboxed_command("echo test_sandbox_ok", cwd=str(ws))
    assert res.executed is True
    assert res.exit_code == 0
    assert "test_sandbox_ok" in res.stdout
    assert res.duration_ms >= 0

    # Execute blocked command
    res_blocked = engine.execute_sandboxed_command("rm -rf /", cwd=str(ws))
    assert res_blocked.executed is False
    assert res_blocked.audit.verdict == "BLOCK"
    assert "blocked" in res_blocked.error.lower()

    # Check SQLite audit ledger
    logs = engine.list_audit_logs(limit=10)
    assert len(logs) >= 2
    verdicts = [log["verdict"] for log in logs]
    assert "ALLOW" in verdicts
    assert "BLOCK" in verdicts


def test_workstation_scaffolding(sandbox_fixture):
    engine, ws = sandbox_fixture
    res = engine.scaffold_project(
        project_type="python_service",
        target_dir=str(ws),
        project_name="telemetry_worker",
        description="Telemetry background service"
    )
    assert res["success"] is True
    assert res["project_name"] == "telemetry_worker"

    proj_dir = Path(res["directory"])
    assert (proj_dir / "main.py").exists()
    assert (proj_dir / "requirements.txt").exists()
    assert (proj_dir / "tests" / "test_main.py").exists()
    assert (proj_dir / "README.md").exists()

    content = (proj_dir / "main.py").read_text(encoding="utf-8")
    assert "telemetry_worker" in content


def test_workstation_git_hygiene(sandbox_fixture):
    engine, ws = sandbox_fixture
    status = engine.get_git_hygiene(repo_dir=str(ws))
    # Temp directory is not a git repo
    assert status.is_git_repo is False
    assert status.hygiene_score == 0
    assert len(status.recommendations) > 0


def test_workstation_atomic_commit_validation(sandbox_fixture):
    engine, ws = sandbox_fixture
    # Non-conventional commit message must fail
    res_bad = engine.create_atomic_commit("fixed some stuff", repo_dir=str(ws))
    assert res_bad["success"] is False
    assert "Conventional Commits" in res_bad["error"]


def test_workstation_snippet_registry(sandbox_fixture):
    engine, _ = sandbox_fixture
    snippet = engine.save_snippet(
        title="SQLite WAL Checkpoint",
        language="python",
        code="conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')",
        tags=["sqlite", "wal", "database"],
        description="Truncates WAL journal to reclaim disk space"
    )
    assert snippet.id is not None
    assert snippet.title == "SQLite WAL Checkpoint"

    # Query snippet
    results = engine.list_snippets(language="python")
    assert len(results) >= 1
    assert results[0].language == "python"

    results_tagged = engine.list_snippets(tag="wal")
    assert len(results_tagged) >= 1

    # Delete snippet
    deleted = engine.delete_snippet(snippet.id)
    assert deleted is True
    assert len(engine.list_snippets(language="python")) == 0


def test_sandbox_server_endpoints():
    from fastapi.testclient import TestClient
    from server import app
    client = TestClient(app)

    # 1. Audit endpoint
    res_audit = client.post("/api/sandbox/audit", json={"command": "echo test_api"})
    assert res_audit.status_code == 200
    assert res_audit.json()["verdict"] == "ALLOW"

    # 2. Audit logs endpoint
    res_logs = client.get("/api/sandbox/audit-logs")
    assert res_logs.status_code == 200
    assert "logs" in res_logs.json()

    # 3. Git status endpoint
    res_git = client.get("/api/workstation/git-status")
    assert res_git.status_code == 200
    assert "is_git_repo" in res_git.json()

    # 4. Snippets endpoint
    res_snip = client.post("/api/workstation/snippets", json={
        "title": "FastAPI Health Endpoint",
        "language": "python",
        "code": "@app.get('/health')\ndef h(): return {'ok': True}",
        "tags": ["fastapi", "health"]
    })
    assert res_snip.status_code == 200
    assert res_snip.json()["id"] is not None

    res_list = client.get("/api/workstation/snippets")
    assert res_list.status_code == 200
    assert res_list.json()["count"] >= 1
