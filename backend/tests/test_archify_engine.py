"""
Unit and integration tests for Archify Architecture & Diagram Verification Engine (Archify adaptation).
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from archify_engine import ArchifyEngine

@pytest.fixture
def temp_arch():
    tmp_dir = Path(tempfile.mkdtemp())
    db_path = tmp_dir / "test_arch.db"
    vault_dir = tmp_dir / "vault"
    vault_dir.mkdir(parents=True)
    engine = ArchifyEngine(db_path=db_path, vault_dir=vault_dir)
    yield engine, tmp_dir, vault_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_mermaid_syntax_validation(temp_arch):
    engine, _, _ = temp_arch
    
    # Valid flowchart
    code = """flowchart TD
    A[Client] --> B[Server]
    B --> C[(Database)]
"""
    val = engine.validate_mermaid(code)
    assert val["valid"] is True
    assert val["node_count"] >= 3
    assert val["edge_count"] == 2

    # Invalid: missing header
    bad_code = "A --> B"
    val_bad = engine.validate_mermaid(bad_code)
    assert val_bad["valid"] is False
    assert "Invalid or missing diagram header" in val_bad["error"]

    # Invalid: unbalanced brackets
    unbalanced = "graph TD\nA[Client --> B"
    val_unb = engine.validate_mermaid(unbalanced)
    assert val_unb["valid"] is False
    assert "Unbalanced brackets" in val_unb["error"]

def test_generate_default_and_custom_diagrams(temp_arch):
    engine, _, vault_dir = temp_arch
    
    # 1. Generate sequence diagram default template
    seq_diag = engine.generate_diagram(
        title="Authentication_Flow",
        diagram_type="sequence",
        description="End-to-end authentication and token generation sequence."
    )
    assert seq_diag["id"] is not None
    assert seq_diag["diagram_type"] == "sequence"
    assert Path(seq_diag["vault_path"]).exists()
    
    content = Path(seq_diag["vault_path"]).read_text(encoding="utf-8")
    assert "sequenceDiagram" in content
    assert "# 📐 Authentication_Flow" in content

    # 2. Generate custom diagram
    custom_mermaid = """graph LR
    API[FastAPI Gateway] ==> Core[ReAct Engine]
    Core --> Memory[(SQLite WAL)]
"""
    cust_diag = engine.generate_diagram(
        title="Custom_Pipeline",
        diagram_type="system",
        description="Custom pipeline visualization",
        raw_mermaid=custom_mermaid
    )
    assert cust_diag["edge_count"] >= 2
    assert Path(cust_diag["vault_path"]).exists()

def test_inspect_codebase_architecture(temp_arch):
    engine, tmp_dir, _ = temp_arch
    
    # Create fake modules in a sample dir
    mock_dir = tmp_dir / "mock_backend"
    mock_dir.mkdir()
    (mock_dir / "server.py").write_text("import engine\nfrom config import config", encoding="utf-8")
    (mock_dir / "engine.py").write_text("import memory\nfrom router import router", encoding="utf-8")
    (mock_dir / "memory.py").write_text("import sqlite3", encoding="utf-8")
    (mock_dir / "router.py").write_text("from config import config", encoding="utf-8")
    (mock_dir / "config.py").write_text("class Config: pass", encoding="utf-8")

    diag = engine.inspect_codebase_architecture(target_dir=str(mock_dir))
    assert diag["title"] == "MaxIM_Backend_Module_Architecture"
    assert diag["node_count"] >= 3
    assert Path(diag["vault_path"]).exists()
    
    file_text = Path(diag["vault_path"]).read_text(encoding="utf-8")
    assert "flowchart TD" in file_text

def test_list_diagrams(temp_arch):
    engine, _, _ = temp_arch
    engine.generate_diagram(title="Diagram_One", diagram_type="state_machine")
    engine.generate_diagram(title="Diagram_Two", diagram_type="data_flow")
    
    diags = engine.list_diagrams()
    assert len(diags) == 2
    titles = [d["title"] for d in diags]
    assert "Diagram_One" in titles
    assert "Diagram_Two" in titles
