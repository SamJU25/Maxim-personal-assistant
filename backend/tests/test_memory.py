"""
Unit tests for SQLite Memory Tree (memory.py).
Tests session management, message turn persistence, facts, and execution receipts.
"""
import pytest
from pathlib import Path
from memory import SQLiteMemoryStore, MessageRecord

@pytest.fixture
def temp_db(tmp_path: Path):
    db_file = tmp_path / "test_maxim.db"
    return SQLiteMemoryStore(db_path=db_file)

def test_session_lifecycle(temp_db: SQLiteMemoryStore):
    temp_db.create_session("sess_01", title="Test Session")
    sessions = temp_db.list_sessions()
    
    assert len(sessions) == 1
    assert sessions[0]["id"] == "sess_01"
    assert sessions[0]["title"] == "Test Session"

def test_message_turn_persistence(temp_db: SQLiteMemoryStore):
    msg1 = MessageRecord(session_id="sess_01", role="user", content="Hello MaxIM")
    msg2 = MessageRecord(session_id="sess_01", role="assistant", content="I'm awake. What now?")
    
    temp_db.add_message(msg1)
    temp_db.add_message(msg2)
    
    messages = temp_db.get_messages("sess_01")
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "Hello MaxIM"
    assert messages[1].role == "assistant"
    assert messages[1].content == "I'm awake. What now?"

def test_continuous_fact_storage_and_upsert(temp_db: SQLiteMemoryStore):
    temp_db.remember_fact("preference", "ui_style", "dark_minimalist")
    facts = temp_db.get_facts("preference")
    assert len(facts) == 1
    assert facts[0].value == "dark_minimalist"
    
    # Test update (upsert)
    temp_db.remember_fact("preference", "ui_style", "luxury_obsidian")
    updated_facts = temp_db.get_facts("preference")
    assert len(updated_facts) == 1
    assert updated_facts[0].value == "luxury_obsidian"

def test_execution_receipts(temp_db: SQLiteMemoryStore):
    receipt_id = temp_db.log_receipt(
        tool_name="vault.write_note",
        arguments={"title": "TestNote", "folder": "01 - Memory"},
        result="Success: 120 bytes written",
        session_id="sess_01"
    )
    assert receipt_id > 0

def test_frequent_user_directives(temp_db: SQLiteMemoryStore):
    temp_db.add_message(MessageRecord(session_id="s1", role="user", content="Inspect telemetry note"))
    temp_db.add_message(MessageRecord(session_id="s1", role="assistant", content="Done"))
    temp_db.add_message(MessageRecord(session_id="s1", role="user", content="Inspect telemetry note"))
    temp_db.add_message(MessageRecord(session_id="s2", role="user", content="Deploy autonomous agents"))
    temp_db.add_message(MessageRecord(session_id="s2", role="user", content="hi"))

    directives = temp_db.get_frequent_user_directives(limit=4)
    assert len(directives) == 2
    assert directives[0]["content"] == "Inspect telemetry note"
    assert directives[0]["usage_count"] == 2
    assert directives[1]["content"] == "Deploy autonomous agents"
    assert directives[1]["usage_count"] == 1
