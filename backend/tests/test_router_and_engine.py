"""
Unit tests for Multi-Model Router (router.py) and Agent Engine (engine.py).
Tests Google, OpenAI, DeepSeek, OmniRoute, and Custom providers, plus tool loop execution.
"""
import pytest
import json
from pathlib import Path
from router import model_router, ProviderType, ProviderConfig
from engine import MaxIMAgentEngine, MAXIM_TOOLS
from memory import SQLiteMemoryStore

def test_all_providers_configured():
    """Verify all required providers (Google, OpenAI, DeepSeek, OmniRoute, Ollama, Custom) exist."""
    providers = [
        ProviderType.OLLAMA,
        ProviderType.OPENAI,
        ProviderType.GOOGLE,
        ProviderType.DEEPSEEK,
        ProviderType.OMNIROUTE,
        ProviderType.CUSTOM,
    ]
    for p in providers:
        cfg = model_router.get_provider_config(p)
        assert isinstance(cfg, ProviderConfig)
        assert cfg.name == p.value
        assert len(cfg.base_url) > 0
        assert len(cfg.default_model) > 0

def test_google_gemini_spec():
    """Verify Google Gemini uses the OpenAI-compatible endpoint."""
    google_cfg = model_router.get_provider_config(ProviderType.GOOGLE)
    assert "generativelanguage.googleapis.com" in google_cfg.base_url
    assert "openai" in google_cfg.base_url
    assert "gemini" in google_cfg.default_model

def test_chatgpt_openai_spec():
    """Verify OpenAI ChatGPT provider configuration."""
    openai_cfg = model_router.get_provider_config(ProviderType.OPENAI)
    assert "api.openai.com" in openai_cfg.base_url
    assert "gpt" in openai_cfg.default_model

def test_omniroute_spec():
    """Verify OmniRoute provider configuration."""
    omni_cfg = model_router.get_provider_config(ProviderType.OMNIROUTE)
    assert "omniroute" in omni_cfg.base_url

def test_custom_provider_dynamic_registration():
    """Verify registering a custom arbitrary provider (e.g. Groq, Together, Localhost vLLM)."""
    model_router.register_custom_provider(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key="gsk_test123",
        default_model="llama-3.3-70b-versatile"
    )
    
    cfg = model_router.get_provider_config("groq")
    assert cfg.name == "groq"
    assert cfg.base_url == "https://api.groq.com/openai/v1"
    assert cfg.default_model == "llama-3.3-70b-versatile"
    assert cfg.api_key == "gsk_test123"

def test_client_instantiation():
    """Verify AsyncOpenAI and OpenAI clients are instantiated cleanly for providers."""
    client, model = model_router.get_async_client(ProviderType.GOOGLE)
    assert client is not None
    assert "gemini" in model

    sync_client, sync_model = model_router.get_sync_client(ProviderType.OPENAI)
    assert sync_client is not None
    assert "gpt" in sync_model

def test_engine_tool_execution(tmp_path: Path):
    """Verify engine tool dispatcher executes tools and logs receipts."""
    test_db = SQLiteMemoryStore(db_path=tmp_path / "test.db")
    engine = MaxIMAgentEngine(memory_store=test_db)
    
    # 1. Test read vault note
    read_out = engine.execute_tool("read_vault_note", {"title": "Master MOC"}, session_id="test_sess")
    read_data = json.loads(read_out)
    assert read_data["found"] is True
    assert read_data["title"] == "Master MOC"
    
    # 2. Test search vault
    search_out = engine.execute_tool("search_vault", {"query": "galaxy"}, session_id="test_sess")
    search_data = json.loads(search_out)
    assert len(search_data) > 0
    
    # 3. Test remember fact
    fact_out = engine.execute_tool(
        "remember_user_fact",
        {"category": "preference", "key": "agent_style", "value": "sarcastic"},
        session_id="test_sess"
    )
    assert "remembered" in fact_out
    
    # Verify receipts in DB
    facts = test_db.get_facts("preference")
    assert len(facts) == 1
    assert facts[0].key == "agent_style"

def test_engine_system_prompt_builder(tmp_path: Path):
    """Verify system prompt fuses soul, TELOS, and remembered facts."""
    test_db = SQLiteMemoryStore(db_path=tmp_path / "test.db")
    test_db.remember_fact("rule", "code_style", "defensive")
    
    engine = MaxIMAgentEngine(memory_store=test_db)
    prompt = engine.build_system_prompt()
    
    assert "MaxIM" in prompt
    assert "sarcastic" in prompt.lower()
    assert "Active Targets:" in prompt or "TELOS" in prompt
    assert "code_style: defensive" in prompt

def test_dynamic_intent_tool_scoping(tmp_path: Path):
    """Verify that local models dynamically receive intent-specific tool bundles on demand."""
    test_db = SQLiteMemoryStore(db_path=tmp_path / "test.db")
    engine = MaxIMAgentEngine(memory_store=test_db)

    # 1. Base tools for local model without specific query
    base_tools = engine.get_scoped_tools(provider="local", model="qwen3.5:4b", query=None)
    base_names = {t["function"]["name"] for t in base_tools}
    assert "read_vault_note" in base_names
    assert "generate_image" in base_names
    assert "browser_navigate" not in base_names
    assert "os_focus_window" not in base_names
    assert "organize_directory" not in base_names

    # 2. Browser intent query mounts browser tools
    browser_tools = engine.get_scoped_tools(
        provider="local",
        model="qwen3.5:4b",
        query="Open the browser and navigate to https://github.com"
    )
    browser_names = {t["function"]["name"] for t in browser_tools}
    assert "browser_navigate" in browser_names
    assert "browser_click_element" in browser_names
    assert "browser_get_dom" in browser_names

    # 3. OS & Window intent query mounts OS tools
    os_tools = engine.get_scoped_tools(
        provider="local",
        model="qwen3.5:4b",
        query="Please focus the active window and launch my code editor"
    )
    os_names = {t["function"]["name"] for t in os_tools}
    assert "os_focus_window" in os_names
    assert "os_list_windows" in os_names
    assert "os_launch_app" in os_names

    # 4. File organizer intent query mounts file tools
    file_tools = engine.get_scoped_tools(
        provider="local",
        model="qwen3.5:4b",
        query="Organize the files in my downloads directory"
    )
    file_names = {t["function"]["name"] for t in file_tools}
    assert "organize_directory" in file_names
    assert "scan_directory" in file_names

    # 5. Spreadsheet intent query mounts office tools
    office_tools = engine.get_scoped_tools(
        provider="local",
        model="qwen3.5:4b",
        query="Create a new spreadsheet workbook with revenue calculations"
    )
    office_names = {t["function"]["name"] for t in office_tools}
    assert "office_create_workbook" in office_names
    assert "office_read_sheet" in office_names

    # 6. Cloud model receives full un-pruned catalog regardless of query (including extensions)
    cloud_tools = engine.get_scoped_tools(provider="google", model="gemini-2.5-flash")
    assert len(cloud_tools) >= len(MAXIM_TOOLS)

@pytest.mark.asyncio
async def test_engine_run_turn_stream_tool_chunk_assembly(tmp_path: Path):
    """Verify tool call streaming chunk assembly and fallback id generation via time.time()."""
    test_db = SQLiteMemoryStore(db_path=tmp_path / "test.db")
    engine = MaxIMAgentEngine(memory_store=test_db)

    class MockDelta:
        def __init__(self, content=None, tool_calls=None):
            self.content = content
            self.tool_calls = tool_calls

    class MockChoice:
        def __init__(self, delta):
            self.delta = delta

    class MockChunk:
        def __init__(self, delta):
            self.choices = [MockChoice(delta)]

    class MockTCFunction:
        def __init__(self, name="", arguments=""):
            self.name = name
            self.arguments = arguments

    class MockToolCallDelta:
        def __init__(self, index, id=None, function=None):
            self.index = index
            self.id = id
            self.function = function

    chunks = [
        MockChunk(MockDelta(content="Looking up note")),
        MockChunk(MockDelta(tool_calls=[
            MockToolCallDelta(index=0, id=None, function=MockTCFunction(name="read_vault_note", arguments='{"title": '))
        ])),
        MockChunk(MockDelta(tool_calls=[
            MockToolCallDelta(index=0, id=None, function=MockTCFunction(arguments='"Master MOC"}'))
        ])),
    ]

    async def mock_stream(*args, **kwargs):
        for c in chunks:
            yield c

    orig_stream = model_router.stream_chat_completion
    model_router.stream_chat_completion = mock_stream
    try:
        events = []
        async for event in engine.run_turn_stream("check notes", session_id="test_stream"):
            events.append(event)
            if event.get("type") == "tool_result":
                break
        assert any(e.get("type") == "content" for e in events)
        assert any(e.get("type") == "tool_call" for e in events)
        tool_call = next(e for e in events if e.get("type") == "tool_call")
        assert tool_call.get("tool") == "read_vault_note"
        assert any(e.get("type") == "tool_result" for e in events)
    finally:
        model_router.stream_chat_completion = orig_stream


