"""
Unit and integration tests for Socratic Mastery & Topic Curriculum Engine (OpenMAIC adaptation).
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from socratic_curriculum import SocraticCurriculumEngine

@pytest.fixture
def temp_curriculum():
    tmp_dir = Path(tempfile.mkdtemp())
    db_path = tmp_dir / "test_curr.db"
    vault_dir = tmp_dir / "vault"
    vault_dir.mkdir(parents=True)
    engine = SocraticCurriculumEngine(db_path=db_path, vault_dir=vault_dir)
    yield engine, tmp_dir, vault_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_generate_curriculum_and_vault_sync(temp_curriculum):
    engine, _, vault_dir = temp_curriculum
    res = engine.generate_curriculum(
        topic="SQLite_WAL_Concurrency",
        category="engineering",
        description="Understanding Write-Ahead Logging and database crash resilience."
    )
    assert res["curriculum_id"] is not None
    assert res["modules_count"] == 3
    assert res["drills_count"] == 3
    assert Path(res["vault_path"]).exists()

    content = Path(res["vault_path"]).read_text(encoding="utf-8")
    assert "# 🎓 Socratic Curriculum: SQLite_WAL_Concurrency" in content
    assert "Foundations & Mental Models" in content
    assert "Socratic Exploration & Tradeoffs" in content
    assert "Socratic Exploration Drills" in content

def test_get_drill_and_submit_answer(temp_curriculum):
    engine, _, _ = temp_curriculum
    curr = engine.generate_curriculum(topic="Rust_Memory_Safety")
    c_id = curr["curriculum_id"]

    # 1. Fetch first drill
    drill = engine.get_next_drill(c_id)
    assert drill is not None
    assert "Rust_Memory_Safety" in drill["question"]
    assert len(drill["socratic_hint"]) > 0

    # 2. Submit thoughtful answer
    ans_res = engine.submit_drill_answer(
        drill_id=drill["id"],
        user_answer="The ownership system and borrow checker guarantee single-writer or multiple-readers at compile time, preventing data races."
    )
    assert ans_res["score"] >= 60
    assert ans_res["updated_mastery_level"] > 0
    assert "feedback" in ans_res

    # 3. Fetch next drill (should be drill 2, not drill 1)
    next_drill = engine.get_next_drill(c_id)
    assert next_drill is not None
    assert next_drill["id"] != drill["id"]

def test_list_curricula_tracking(temp_curriculum):
    engine, _, _ = temp_curriculum
    c1 = engine.generate_curriculum(topic="Distributed_Consensus")
    c2 = engine.generate_curriculum(topic="Vector_Embeddings")

    # Answer one drill in c1
    d1 = engine.get_next_drill(c1["curriculum_id"])
    engine.submit_drill_answer(d1["id"], "Raft ensures leader election and log replication consistency.")

    all_topics = engine.list_curricula()
    assert len(all_topics) == 2
    
    t1 = next(t for t in all_topics if t["id"] == c1["curriculum_id"])
    assert t1["answered_drills"] == 1
    assert t1["mastery_level"] > 0
