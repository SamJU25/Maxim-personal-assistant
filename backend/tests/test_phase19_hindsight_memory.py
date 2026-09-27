"""
Unit tests for Phase 19: Hindsight Epistemic Mental Models & Unified Retain-Recall-Reflect Memory Engine.
Paper: 'Hindsight is 20/20: Building Agent Memory that Retains, Recalls, and Reflects' (arXiv:2512.12818)
Repository reference: https://github.com/vectorize-io/hindsight

Verifies:
1. MentalModelEngine: SQLite WAL table, upsert, Bayesian reinforcement, contradiction decay, and disproven state.
2. Obsidian Synapse integration: Markdown note generation with YAML frontmatter, wikilinks, and _Mental Models MOC.md.
3. Epistemic reflection: Pattern matching across observations into synthesized behavioral dispositions.
4. FiveLayerMemorySystem Hindsight primitives: retain(), recall(), and reflect().
5. Tool catalog registration: 4 Hindsight tools in ToolsetName.MEMORY.
6. MaxIMAgentEngine: ReAct system prompt context injection and tool dispatch.
7. FastAPI REST API endpoints: /api/memory/retain, /api/memory/recall, /api/memory/reflect, /api/memory/mental-models CRUD.
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from mental_models import MentalModelEngine, MentalModelRecord, mental_models
from five_layer_memory import five_layer_memory, FiveLayerMemorySystem
from tools.catalog import tool_catalog, ToolsetName
from engine import MaxIMAgentEngine
from server import app


# =============================================================================
# 1. MENTAL MODEL ENGINE CRUD & BAYESIAN REINFORCEMENT
# =============================================================================

def test_mental_model_upsert_and_retrieve(tmp_path: Path):
    """Verifies creating and retrieving a mental model record."""
    test_db = tmp_path / "test_maxim.db"
    test_vault = tmp_path / "vault"
    engine = MentalModelEngine(db_path=test_db, vault_dir=test_vault)

    # 1. Upsert new preference
    rec = engine.upsert_mental_model(
        name="prefers_concise_diffs",
        disposition="Prefers minimal, surgical unified diffs without rewriting entire files.",
        category="preference",
        confidence=0.7,
        observation="User said: Keep diffs short.",
        sync_vault=True,
    )

    assert rec.name == "prefers_concise_diffs"
    assert rec.confidence == 0.7
    assert rec.evidence_count == 1
    assert "User said: Keep diffs short." in rec.source_observations
    assert rec.status == "active"

    # 2. Retrieve by name
    retrieved = engine.get_model("prefers_concise_diffs")
    assert retrieved is not None
    assert retrieved.id == rec.id
    assert retrieved.name == "prefers_concise_diffs"

    # 3. Retrieve by ID
    retrieved_by_id = engine.get_model(rec.id)
    assert retrieved_by_id is not None
    assert retrieved_by_id.name == "prefers_concise_diffs"


def test_mental_model_reinforcement(tmp_path: Path):
    """Verifies incremental Bayesian confidence reinforcement upon corroborating evidence."""
    test_db = tmp_path / "test_maxim.db"
    test_vault = tmp_path / "vault"
    engine = MentalModelEngine(db_path=test_db, vault_dir=test_vault)

    engine.upsert_mental_model(
        name="powershell_preference",
        disposition="Prefers running native PowerShell commands over bash on Windows.",
        category="heuristic",
        confidence=0.6,
        sync_vault=False,
    )

    # Reinforce with supporting observation (+0.1)
    reinforced = engine.reinforce(
        "powershell_preference",
        delta=0.1,
        observation="User executed: powershell.exe Get-Process",
        sync_vault=False,
    )

    assert reinforced is not None
    assert pytest.approx(reinforced.confidence, 0.01) == 0.7
    assert reinforced.evidence_count == 2
    assert len(reinforced.source_observations) == 1


def test_mental_model_contradiction_and_disproven(tmp_path: Path):
    """Verifies confidence decay and status transition to 'disproven' when contradicted."""
    test_db = tmp_path / "test_maxim.db"
    test_vault = tmp_path / "vault"
    engine = MentalModelEngine(db_path=test_db, vault_dir=test_vault)

    # Start with low confidence
    engine.upsert_mental_model(
        name="likes_dark_mode",
        disposition="Believes user prefers dark mode.",
        category="preference",
        confidence=0.25,
        sync_vault=False,
    )

    # Contradict with -0.15 delta
    contradicted = engine.contradict(
        "likes_dark_mode",
        delta=0.15,
        reason="User explicitly requested light mode theme.",
        sync_vault=False,
    )

    assert contradicted is not None
    assert pytest.approx(contradicted.confidence, 0.01) == 0.10
    # Confidence <= 0.15 should transition status to disproven
    assert contradicted.status == "disproven"


def test_mental_model_update(tmp_path: Path):
    """Verifies explicit updates to disposition, confidence, and status."""
    test_db = tmp_path / "test_maxim.db"
    test_vault = tmp_path / "vault"
    engine = MentalModelEngine(db_path=test_db, vault_dir=test_vault)

    rec = engine.upsert_mental_model(
        name="code_style",
        disposition="Avoid excessive docstrings.",
        category="heuristic",
        confidence=0.5,
        sync_vault=False,
    )

    updated = engine.update_model(
        name_or_id=rec.id,
        disposition="Use concise typing and direct docstrings.",
        confidence=0.85,
        status="active",
        sync_vault=False,
    )

    assert updated is not None
    assert updated.disposition == "Use concise typing and direct docstrings."
    assert pytest.approx(updated.confidence, 0.01) == 0.85


# =============================================================================
# 2. OBSIDIAN VAULT SYNCHRONIZATION & MOC GENERATION
# =============================================================================

def test_obsidian_vault_sync_and_moc(tmp_path: Path):
    """Verifies markdown note writing in 01 - Memory/Mental Models and _Mental Models MOC.md."""
    test_db = tmp_path / "test_maxim.db"
    test_vault = tmp_path / "vault"
    engine = MentalModelEngine(db_path=test_db, vault_dir=test_vault)

    rec = engine.upsert_mental_model(
        name="subagent_delegation",
        disposition="Delegate high-volume token tasks to isolated child subagents.",
        category="heuristic",
        confidence=0.8,
        observation="Observed prompt exhaustion on monolithic turn.",
        sync_vault=True,
    )

    model_file = test_vault / "01 - Memory" / "Mental Models" / "subagent_delegation.md"
    assert model_file.exists()

    content = model_file.read_text(encoding="utf-8")
    assert 'name: "subagent_delegation"' in content
    assert "confidence: 0.80" in content
    assert "[[00 - LifeOS/TELOS]]" in content
    assert "Delegate high-volume token tasks" in content

    # Check MOC
    moc_file = test_vault / "01 - Memory" / "Mental Models" / "_Mental Models MOC.md"
    assert moc_file.exists()
    moc_content = moc_file.read_text(encoding="utf-8")
    assert "[[subagent_delegation]]" in moc_content
    assert "80% confidence" in moc_content


# =============================================================================
# 3. REFLECTIVE SYNTHESIS OVER RAW OBSERVATIONS
# =============================================================================

def test_epistemic_reflection_clustering(tmp_path: Path):
    """Verifies that reflect() detects heuristic patterns and crystallizes mental models."""
    test_db = tmp_path / "test_maxim.db"
    test_vault = tmp_path / "vault"
    engine = MentalModelEngine(db_path=test_db, vault_dir=test_vault)

    observations = [
        "Please use minimal diffs and replace_file_content for edits.",
        "Remember to save tokens: compress and distill output with token budget.",
        "When executing powershell scripts, double check quoting conventions.",
    ]

    res = engine.reflect(topic="coding_discipline", observations=observations, sync_vault=True)
    assert res["status"] == "reflected"
    assert res["observations_processed"] == 3
    assert len(res["models_touched"]) >= 2

    # Check crystallized models
    surgical = engine.get_model("surgical_code_editing")
    assert surgical is not None
    assert surgical.category == "heuristic"

    token_budget = engine.get_model("token_budget_conservation")
    assert token_budget is not None


# =============================================================================
# 4. FIVE-LAYER MEMORY HINDSIGHT PRIMITIVES: RETAIN, RECALL, REFLECT
# =============================================================================

def test_five_layer_retain_observation_and_preference():
    """Verifies retain() primitive routing: observation to SQLite facts vs opinion to Mental Models."""
    # Retain fact/observation
    obs_res = five_layer_memory.retain(
        content="Active Python virtualenv is Python 3.14.7 located at backend/.venv",
        category="observation",
        source="system_check",
    )
    assert obs_res["status"] == "retained"
    assert obs_res["primitive"] == "retain"
    assert obs_res["network"] == "observation"

    # Retain opinion/preference (routes to MentalModelEngine)
    pref_res = five_layer_memory.retain(
        content="Prefer functional composition over deep inheritance hierarchies.",
        category="preference",
        metadata={"name": "prefer_composition", "confidence": 0.85},
    )
    assert pref_res["status"] == "retained"
    assert pref_res["primitive"] == "retain"
    assert pref_res["network"] == "opinion"
    assert pref_res["name"] == "prefer_composition"


def test_five_layer_recall_hybrid_search():
    """Verifies recall() primitive hybrid querying across mental models, observations, and vault."""
    # Ensure item exists
    five_layer_memory.retain(
        content="Always verify 100% green tests before marking phase complete.",
        category="rule",
        metadata={"key": "test_verification_rule"},
    )

    recall_res = five_layer_memory.recall(
        query="tests green verify",
        top_k=5,
        include_mental_models=True,
    )
    assert recall_res["status"] == "success"
    assert recall_res["primitive"] == "recall"
    assert "results" in recall_res
    assert "mental_models" in recall_res["results"]
    assert "observations" in recall_res["results"]
    assert "vault_notes" in recall_res["results"]


def test_five_layer_reflect():
    """Verifies reflect() primitive executes pass over session turns."""
    ref_res = five_layer_memory.reflect(
        topic="workspace_hygiene",
        session_id="default_session",
    )
    assert ref_res["status"] == "reflected"
    assert ref_res["primitive"] == "reflect"
    assert "active_models_count" in ref_res


# =============================================================================
# 5. TOOL CATALOG & AGENT ENGINE INTEGRATION
# =============================================================================

def test_tool_catalog_memory_registration():
    """Verifies that all 4 Hindsight tools are present in MEMORY_TOOLS catalog."""
    tools = tool_catalog.get_toolset(ToolsetName.MEMORY)
    tool_names = [t["function"]["name"] for t in tools]

    assert "retain_memory" in tool_names
    assert "recall_memory" in tool_names
    assert "reflect_mental_models" in tool_names
    assert "get_mental_models" in tool_names


def test_agent_engine_system_prompt_mental_models_injection():
    """Verifies that active high-confidence mental models are injected into system prompt."""
    engine = MaxIMAgentEngine()
    prompt = engine.build_system_prompt(session_id="prompt_test_session")

    # If active mental models exist, header should appear
    active = mental_models.get_active_models(min_confidence=0.4, limit=5)
    if active:
        assert "### HINDSIGHT MENTAL MODELS & LEARNED DISPOSITIONS" in prompt


def test_agent_engine_hindsight_tool_execution():
    """Verifies MaxIMAgentEngine.execute_tool dispatches retain_memory and get_mental_models."""
    engine = MaxIMAgentEngine()

    # 1. Execute retain_memory
    retain_out = engine.execute_tool(
        name="retain_memory",
        args={
            "content": "Database migrations must use idempotent SQLite pragmas.",
            "category": "observation",
            "source": "architectural_rule",
        },
        session_id="tool_test_session",
    )
    retain_data = json.loads(retain_out)
    assert retain_data.get("status") == "retained"

    # 2. Execute get_mental_models
    models_out = engine.execute_tool(
        name="get_mental_models",
        args={"min_confidence": 0.0, "limit": 10},
        session_id="tool_test_session",
    )
    models_data = json.loads(models_out)
    assert models_data.get("status") == "success"
    assert "mental_models" in models_data


# =============================================================================
# 6. FASTAPI REST API ENDPOINTS
# =============================================================================

client = TestClient(app)

def test_api_memory_retain_endpoint():
    """POST /api/memory/retain stores observation/fact with provenance."""
    payload = {
        "content": "Hardware volume changes must be clamped between 0 and 100.",
        "category": "observation",
        "source": "test_suite",
        "session_id": "api_test_session",
    }
    response = client.post("/api/memory/retain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "retained"
    assert data["primitive"] == "retain"


def test_api_memory_recall_endpoint():
    """POST /api/memory/recall performs hybrid search."""
    payload = {
        "query": "volume hardware",
        "top_k": 3,
        "include_mental_models": True,
    }
    response = client.post("/api/memory/recall", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "results" in data


def test_api_memory_reflect_endpoint():
    """POST /api/memory/reflect runs epistemic reflection pass."""
    payload = {
        "topic": "api_verification",
        "session_id": "default_session",
    }
    response = client.post("/api/memory/reflect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "reflected"


def test_api_memory_mental_models_get_and_patch():
    """GET /api/memory/mental-models and PATCH /api/memory/mental-models/{id}."""
    # 1. Upsert a model to ensure at least one exists
    created = mental_models.upsert_mental_model(
        name="api_test_model",
        disposition="Test disposition for API validation.",
        category="heuristic",
        confidence=0.6,
        sync_vault=False,
    )

    # 2. GET mental models
    get_res = client.get("/api/memory/mental-models?min_confidence=0.0&limit=20")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["status"] == "success"
    assert get_data["count"] >= 1

    # 3. PATCH the model
    patch_payload = {
        "confidence": 0.95,
        "disposition": "Updated disposition via PATCH endpoint.",
    }
    patch_res = client.patch(f"/api/memory/mental-models/{created.id}", json=patch_payload)
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["status"] == "updated"
    assert pytest.approx(patch_data["mental_model"]["confidence"], 0.01) == 0.95
    assert patch_data["mental_model"]["disposition"] == "Updated disposition via PATCH endpoint."

    # 4. PATCH invalid model ID returns 404
    invalid_res = client.patch("/api/memory/mental-models/99999999", json=patch_payload)
    assert invalid_res.status_code == 404
