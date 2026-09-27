"""
Unit and integration tests for OpenHuman Innovations:
1. TokenJuice In-Memory Tool Compression Engine (token_juice.py).
2. Durable Session Goals & Todo Ledger Engine (session_todos.py).
3. FastAPI REST Endpoints in server.py.
"""
import pytest
from token_juice import TokenJuiceCompressor
from session_todos import SessionTodoManager


def test_token_juice_json_compression():
    compressor = TokenJuiceCompressor(max_output_chars=5000)
    
    # Raw JSON with empty collections, nulls, and indentation
    raw_payload = {
        "status": "success",
        "empty_list": [],
        "null_val": None,
        "nested": {
            "key1": "value1",
            "redundant": None
        },
        "processes": [{"pid": i, "name": f"proc_{i}"} for i in range(35)]
    }

    compressed = compressor.compress(raw_payload, tool_name="os_list_processes")
    assert "null_val" not in compressed
    assert "empty_list" not in compressed
    assert "value1" in compressed
    # Long list should be compacted
    assert "items compacted" in compressed

    stats = compressor.get_stats()
    assert stats["total_raw_characters"] > stats["total_compressed_characters"]
    assert stats["tokens_saved"] > 0
    assert stats["compression_ratio_percent"] > 0


def test_token_juice_text_distillation():
    compressor = TokenJuiceCompressor(max_output_chars=5000)
    raw_markdown = """
    # Header Line
    
    
    
    Paragraph with     extra    spaces.
    ---------------------------------------------
    
    
    Another paragraph.
    """
    compressed = compressor.compress(raw_markdown)
    assert "\n\n\n" not in compressed
    assert "Paragraph with extra spaces." in compressed
    assert "---" in compressed


def test_session_todos_lifecycle(tmp_path):
    test_db = tmp_path / "test_todos.db"
    manager = SessionTodoManager(db_path=test_db)
    session_id = "test_openhuman_session"

    # 1. Add Todos
    t1 = manager.add_todo(session_id, "Scaffold database tables")
    t2 = manager.add_todo(session_id, "Wire Hermes tools")
    t3 = manager.add_todo(session_id, "Run end-to-end verification")

    assert t1.step_order == 1
    assert t2.step_order == 2
    assert t3.step_order == 3
    assert t1.status == "pending"

    # 2. Update status
    updated = manager.update_todo(t1.id, "completed", result_summary="Schema migrated in WAL mode")
    assert updated.status == "completed"
    assert updated.result_summary == "Schema migrated in WAL mode"

    # 3. Context formatting for system prompt
    context = manager.format_todos_context(session_id)
    assert "Active Session Goals" in context
    assert "[x] 1. Scaffold database tables (completed)" in context
    assert "[ ] 2. Wire Hermes tools (pending)" in context

    # 4. List and filter
    pending = manager.list_todos(session_id, status="pending")
    assert len(pending) == 2

    # 5. Delete and clear
    deleted = manager.delete_todo(t3.id)
    assert deleted is True
    assert len(manager.list_todos(session_id)) == 2

    cleared = manager.clear_session_todos(session_id)
    assert cleared == 2
    assert len(manager.list_todos(session_id)) == 0


def test_openhuman_server_endpoints():
    from fastapi.testclient import TestClient
    from server import app
    client = TestClient(app)

    # Create todo
    res_create = client.post("/api/todos", json={
        "session_id": "test_api_sess",
        "task_description": "Validate OpenHuman integration",
        "step_order": 1
    })
    assert res_create.status_code == 200
    todo_id = res_create.json()["id"]

    # List todos
    res_list = client.get("/api/todos?session_id=test_api_sess")
    assert res_list.status_code == 200
    assert res_list.json()["count"] >= 1

    # Update todo
    res_patch = client.patch(f"/api/todos/{todo_id}", json={
        "status": "completed",
        "result_summary": "Passed API validation"
    })
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "completed"

    # TokenJuice stats endpoint
    res_tj = client.get("/api/tokenjuice/stats")
    assert res_tj.status_code == 200
    assert "estimated_raw_tokens" in res_tj.json()
    assert "compression_ratio_percent" in res_tj.json()

    # Clean up
    res_del = client.delete(f"/api/todos/{todo_id}")
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True
