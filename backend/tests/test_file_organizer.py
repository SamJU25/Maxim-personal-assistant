"""
Unit and Integration Tests for File & Directory Organizer Engine.
Validates:
1. Category detection (Photos, Documents, Videos, Audio, Archives, Installers, Code).
2. Dry-run preview without disk modifications.
3. Live organization with directory creation and collision protection.
4. Transaction logging and undo rollback.
5. Tool catalog registration (ToolsetName.FILES with 3 tools).
6. AgentShield risk tier classification (scan: Tier 1, organize: Tier 2, undo: Tier 2).
7. ReAct engine execution dispatch.
8. REST API endpoints.
"""
import os
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from file_organizer import FileOrganizerService, file_organizer
from tools.catalog import tool_catalog, ToolsetName
from agent_shield import agent_shield, ToolRiskTier
from engine import agent_engine
from server import app

client = TestClient(app)

def create_sample_files(root: Path):
    """Creates a sample messy folder structure for testing."""
    (root / "photo1.png").write_text("fake png")
    (root / "photo2.jpg").write_text("fake jpg")
    (root / "report.pdf").write_text("fake pdf")
    (root / "notes.txt").write_text("fake notes")
    (root / "movie.mp4").write_text("fake mp4")
    (root / "song.mp3").write_text("fake mp3")
    (root / "archive.zip").write_text("fake zip")
    (root / "setup.exe").write_text("fake exe")
    (root / "script.py").write_text("fake py")

# =========================================================================
# 1. Scanner & Dry-Run Tests
# =========================================================================

def test_scan_directory_categories(tmp_path):
    create_sample_files(tmp_path)
    db_file = str(tmp_path.parent / "test_scan.db")
    service = FileOrganizerService(db_path=db_file)

    scan = service.scan_directory(str(tmp_path))

    assert scan.total_files == 9
    assert scan.category_counts.get("Photos") == 2
    assert scan.category_counts.get("Documents") == 2
    assert scan.category_counts.get("Videos") == 1
    assert scan.category_counts.get("Audio") == 1
    assert scan.category_counts.get("Archives") == 1
    assert scan.category_counts.get("Installers") == 1
    assert scan.category_counts.get("Code") == 1
    assert len(scan.planned_moves) == 9

def test_organize_directory_dry_run(tmp_path):
    create_sample_files(tmp_path)
    db_file = str(tmp_path.parent / "test_dry_run.db")
    service = FileOrganizerService(db_path=db_file)

    org_res = service.organize_directory(str(tmp_path), dry_run=True)

    assert org_res.is_dry_run is True
    assert org_res.moved_count == 9
    assert org_res.failed_count == 0

    # Ensure zero files were actually moved on disk
    assert (tmp_path / "photo1.png").exists()
    assert (tmp_path / "report.pdf").exists()
    assert not (tmp_path / "Photos").exists()
    assert not (tmp_path / "Documents").exists()

# =========================================================================
# 2. Execution, Collision Protection & Undo Rollback Tests
# =========================================================================

def test_organize_directory_execution(tmp_path):
    create_sample_files(tmp_path)
    db_file = str(tmp_path.parent / "test_exec.db")
    service = FileOrganizerService(db_path=db_file)

    org_res = service.organize_directory(str(tmp_path), dry_run=False)

    assert org_res.is_dry_run is False
    assert org_res.moved_count == 9
    assert org_res.failed_count == 0

    # Verify category folders were created
    assert (tmp_path / "Photos" / "photo1.png").exists()
    assert (tmp_path / "Photos" / "photo2.jpg").exists()
    assert (tmp_path / "Documents" / "report.pdf").exists()
    assert (tmp_path / "Videos" / "movie.mp4").exists()
    assert (tmp_path / "Archives" / "archive.zip").exists()
    assert (tmp_path / "Installers" / "setup.exe").exists()

    # Original loose files should no longer be at root
    assert not (tmp_path / "photo1.png").exists()
    assert not (tmp_path / "report.pdf").exists()

def test_collision_avoidance(tmp_path):
    create_sample_files(tmp_path)
    # Pre-create a photo in Photos destination
    photos_dir = tmp_path / "Photos"
    photos_dir.mkdir()
    (photos_dir / "photo1.png").write_text("existing photo")

    db_file = str(tmp_path.parent / "test_col.db")
    service = FileOrganizerService(db_path=db_file)

    service.organize_directory(str(tmp_path), dry_run=False)

    # Both existing and renamed files must exist
    assert (photos_dir / "photo1.png").exists()
    assert (photos_dir / "photo1 (1).png").exists()

def test_undo_organization(tmp_path):
    create_sample_files(tmp_path)
    db_file = str(tmp_path.parent / "test_undo.db")
    service = FileOrganizerService(db_path=db_file)

    # 1. Organize
    org_res = service.organize_directory(str(tmp_path), dry_run=False)
    batch_id = org_res.batch_id
    assert (tmp_path / "Documents" / "report.pdf").exists()

    # 2. Undo
    undo_res = service.undo_organization(batch_id)
    assert undo_res["status"] == "success"
    assert undo_res["restored_count"] == 9

    # Verify restored back to root
    assert (tmp_path / "photo1.png").exists()
    assert (tmp_path / "report.pdf").exists()
    assert (tmp_path / "movie.mp4").exists()

# =========================================================================
# 3. Tool Catalog & Security Tests
# =========================================================================

def test_tool_catalog_files_registration():
    files_tools = tool_catalog.get_toolset(ToolsetName.FILES)
    assert len(files_tools) == 3
    names = [t["function"]["name"] for t in files_tools]
    assert "scan_directory" in names
    assert "organize_directory" in names
    assert "undo_organization" in names

    all_tools = tool_catalog.get_all_tools()
    assert len(all_tools) >= 80

def test_agent_shield_tool_tier_mapping():
    assert agent_shield.get_tool_tier("scan_directory") == ToolRiskTier.TIER_1_READ_ONLY
    assert agent_shield.get_tool_tier("organize_directory") == ToolRiskTier.TIER_2_LOCAL_STATE
    assert agent_shield.get_tool_tier("undo_organization") == ToolRiskTier.TIER_2_LOCAL_STATE

def test_engine_tool_dispatch(tmp_path):
    create_sample_files(tmp_path)

    # 1. scan_directory via engine
    raw_scan = agent_engine.execute_tool(
        name="scan_directory",
        args={"directory_path": str(tmp_path)},
        session_id="test_engine_files",
    )
    scan_res = json.loads(raw_scan)
    assert scan_res["total_files"] == 9
    assert scan_res["category_counts"]["Photos"] == 2

    # 2. organize_directory (dry run) via engine
    raw_org = agent_engine.execute_tool(
        name="organize_directory",
        args={"directory_path": str(tmp_path), "dry_run": True},
        session_id="test_engine_files",
    )
    org_res = json.loads(raw_org)
    assert org_res["is_dry_run"] is True
    assert org_res["moved_count"] == 9

# =========================================================================
# 4. REST Endpoints Tests
# =========================================================================

def test_server_file_endpoints(tmp_path):
    create_sample_files(tmp_path)

    # 1. POST /api/files/scan
    scan_resp = client.post("/api/files/scan", json={"directory_path": str(tmp_path)})
    assert scan_resp.status_code == 200
    scan_data = scan_resp.json()
    assert scan_data["total_files"] == 9

    # 2. POST /api/files/organize (dry run)
    org_resp = client.post("/api/files/organize", json={
        "directory_path": str(tmp_path),
        "dry_run": True,
    })
    assert org_resp.status_code == 200
    org_data = org_resp.json()
    assert org_data["is_dry_run"] is True
    assert org_data["moved_count"] == 9

    # 3. GET /api/files/history
    hist_resp = client.get("/api/files/history")
    assert hist_resp.status_code == 200
    assert "history" in hist_resp.json()
