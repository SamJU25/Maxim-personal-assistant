"""
Unit tests for Phase 1: Core Foundation & LifeOS TELOS Engine.
Uses defensive verification (Code Quality Guardian).
"""
import pytest
from pathlib import Path
from config import config
from telos import LifeOSEngine, TELOSProfile

def test_soul_file_exists():
    """Verify soul.md exists and contains sarcastic, non-sycophantic personality rules."""
    assert config.soul_path.exists(), "soul.md must exist in backend"
    content = config.soul_path.read_text(encoding="utf-8")
    assert "MaxIM" in content
    assert "sarcastic" in content.lower()
    assert "obedience" in content.lower()
    assert "Certainly!" in content  # Prohibited word rule listed

def test_telos_loads_from_vault():
    """Verify LifeOSEngine correctly parses the real vault TELOS.md."""
    engine = LifeOSEngine()
    profile = engine.load()
    
    assert isinstance(profile, TELOSProfile)
    assert len(profile.targets) > 0, "Should have targets from TELOS.md"
    assert any("MaxIM" in t for t in profile.targets)
    assert len(profile.execution) > 0, "Should have active execution projects"
    assert len(profile.lore) > 0, "Should have core principles"
    assert len(profile.stack) > 0, "Should have stack items"

def test_telos_context_injection():
    """Verify TELOS context injection is compact and token-budgeted."""
    engine = LifeOSEngine()
    injection = engine.get_context_injection()
    
    assert "Active Targets:" in injection
    assert "Active Projects:" in injection
    assert len(injection) < 1500, "Context injection must be token-efficient"

def test_telos_custom_parser(tmp_path: Path):
    """Verify parsing logic on custom test markdown."""
    test_md = tmp_path / "TEST_TELOS.md"
    test_md.write_text("""# Custom TELOS
## 🎯 Targets
- Ship Phase 1
- Achieve 0 errors

## ⚡ Execution
- Native Python backend

## 📜 Lore
- No bloat
""", encoding="utf-8")
    
    engine = LifeOSEngine(telos_path=test_md)
    profile = engine.load()
    
    assert profile.targets == ["Ship Phase 1", "Achieve 0 errors"]
    assert profile.execution == ["Native Python backend"]
    assert profile.lore == ["No bloat"]
